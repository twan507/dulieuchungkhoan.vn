"""Đường ghi DUY NHẤT vào news.* (spec lát 8 §5.1): dedupe (URL đã thấy · canonical · tiêu đề chuẩn hoá trong 48 giờ),
ghi bài mới (article + revision v1 + source + ticker), thêm nguồn cho tin đã có, thêm phiên bản khi nội dung đổi (không đè),
bằng chứng danh sách khi hash đổi và HTML bài khi bóc từ chối, domain state theo báo."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta

import sqlalchemy as sa

from etl import series_store
from etl.news_parse import norm_title

WINDOW = timedelta(hours=48)
DOMAIN = "news"


def load_listed(conn) -> dict[str, int]:
    return dict(conn.execute(sa.text("SELECT ticker, security_id FROM market.security WHERE status = 'listed'")).all())


def published_for(item, ext) -> tuple[datetime | None, str]:
    """TinnhanhCK: giờ trên trang (cms-date) trước, sitemap lastmod là giờ SỬA (đo 2026-09-05: 09:18 vs 20:39);
    báo khác: giờ feed trước, giờ trang bù. `src` giữ 'url' khi giá trị đến từ URL (VietnamBiz/BaoChinhPhu)."""
    if item.rule == "tinnhanhck":
        if ext.published_at:
            return ext.published_at, "feed"
        return item.published_at, item.published_at_src if item.published_at else "unknown"
    if item.published_at:
        return item.published_at, item.published_at_src
    if ext.published_at:
        return ext.published_at, "feed"
    return None, "unknown"


@dataclass
class Seen:
    urls: set[str] = field(default_factory=set)
    canon: dict[str, int] = field(default_factory=dict)
    titles: list[tuple[str, datetime, int]] = field(default_factory=list)

    @classmethod
    def load(cls, conn, now: datetime) -> "Seen":
        urls = {r[0] for r in conn.execute(sa.text("SELECT url FROM news.article_source")).all()}
        canon = dict(conn.execute(sa.text("SELECT canonical_url, article_id FROM news.article")).all())
        rows = conn.execute(sa.text(
            "SELECT r.title, coalesce(a.published_at, a.fetched_at), a.article_id FROM news.article a"
            " JOIN news.article_revision r ON r.article_id = a.article_id AND r.version = 1"
            " WHERE coalesce(a.published_at, a.fetched_at) >= :since"), {"since": now - WINDOW}).all()
        return cls(urls, canon, [(norm_title(t), ts, aid) for t, ts, aid in rows])

    def decide(self, item, now: datetime) -> tuple[str, int | None]:
        if item.url in self.urls:                    # khớp URL THÔ đã ghi (article_source.url) — canonical không kiểm ở đây,
            return "seen", self.canon.get(item.canonical_url)   # trùng canonical với url thô của CHÍNH bài gốc gây false positive
        if item.canonical_url in self.canon:
            return "merge_url", self.canon[item.canonical_url]
        key = norm_title(item.title)
        if key:
            when = item.published_at or now
            for k, ts, aid in self.titles:
                if k == key and abs(when - ts) < WINDOW:
                    return "merge_title", aid
        return "new", None

    def remember(self, item, article_id: int, when: datetime) -> None:
        self.urls.add(item.url)
        self.canon[item.canonical_url] = article_id
        self.titles.append((norm_title(item.title), item.published_at or when, article_id))


def insert_article(conn, item, ext, *, fetched_at: datetime, tickers: list[tuple[str, str, int]]) -> int:
    pub, src = published_for(item, ext)
    aid = conn.execute(sa.text(
        "INSERT INTO news.article (canonical_url, primary_source, feed, published_at, published_at_src, fetched_at,"
        " group_from_feed, ticker_step_ran)"
        " VALUES (:cu, :src, :feed, :pub, :psrc, :fa, :grp, :ran) RETURNING article_id"),
        {"cu": item.canonical_url, "src": item.source, "feed": item.feed_slug, "pub": pub, "psrc": src, "fa": fetched_at,
         "grp": item.group_from_feed, "ran": item.group_from_feed == 3}).scalar_one()
    conn.execute(sa.text(
        "INSERT INTO news.article_revision (article_id, version, title, sapo, content, content_fetched_at)"
        " VALUES (:a, 1, :t, :s, :c, :fa)"),
        {"a": aid, "t": item.title or ext.title, "s": ext.sapo, "c": ext.content, "fa": fetched_at})
    add_source(conn, aid, item.source, item.url)
    for ticker, via, sid in tickers:
        conn.execute(sa.text(
            "INSERT INTO news.article_ticker (article_id, security_id, via) VALUES (:a, :s, :v) ON CONFLICT DO NOTHING"),
            {"a": aid, "s": sid, "v": via})
    return aid


def add_source(conn, article_id: int, source_name: str, url: str) -> bool:
    return conn.execute(sa.text(
        "INSERT INTO news.article_source (article_id, source_name, url) VALUES (:a, :s, :u) ON CONFLICT (url) DO NOTHING"),
        {"a": article_id, "s": source_name, "u": url}).rowcount == 1


def add_revision(conn, article_id: int, ext, fetched_at: datetime) -> bool:
    ver, content = conn.execute(sa.text(
        "SELECT version, content FROM news.article_revision WHERE article_id = :a ORDER BY version DESC LIMIT 1"),
        {"a": article_id}).one()
    if series_store.hash_text(content) == series_store.hash_text(ext.content):
        return False
    conn.execute(sa.text(
        "INSERT INTO news.article_revision (article_id, version, title, sapo, content, content_fetched_at)"
        " VALUES (:a, :v, :t, :s, :c, :fa)"),
        {"a": article_id, "v": ver + 1, "t": ext.title, "s": ext.sapo, "c": ext.content, "fa": fetched_at})
    return True


def store_list_if_changed(conn, source: str, url: str, text: str, run_id: int, content_type: str) -> bool:
    h = series_store.hash_text(text)
    last = conn.execute(sa.text(
        "SELECT meta->>'hash' FROM staging.raw_payload WHERE source = :s AND endpoint_key = :k ORDER BY payload_id DESC LIMIT 1"),
        {"s": source, "k": url}).scalar()
    if last == h:
        return False
    conn.execute(sa.text(
        "INSERT INTO staging.raw_payload (source, endpoint_key, content_type, body, meta)"
        " VALUES (:s, :k, :ct, :b, cast(:m AS jsonb))"),
        {"s": source, "k": url, "ct": content_type, "b": text, "m": json.dumps({"hash": h, "run_id": run_id, "bytes": len(text.encode("utf-8"))})})
    return True


def store_refused(conn, source: str, url: str, html_text: str, reason: str, run_id: int) -> None:
    conn.execute(sa.text(
        "INSERT INTO staging.raw_payload (source, endpoint_key, content_type, body, meta)"
        " VALUES (:s, :k, 'html', :b, cast(:m AS jsonb))"),
        {"s": source, "k": url, "b": html_text,
         "m": json.dumps({"refused": True, "reason": reason, "run_id": run_id, "bytes": len(html_text.encode("utf-8"))})})


def upsert_domain_state(engine, sources: set[str], watermark: str) -> None:
    for s in sorted(sources):
        series_store.upsert_domain_state(engine, s, (DOMAIN,), watermark)
