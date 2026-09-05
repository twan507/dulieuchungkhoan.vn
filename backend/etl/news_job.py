"""`python -m etl news` — thu 47 feed + 6 crawl → news.* (spec lát 8 §5.2). Khuôn `series_job`: open_run ngay trước try,
Ctrl+C ⇒ failed 'dừng tay (Ctrl+C)' exit 130; KHÔNG từ chối cả lượt (tin bỏ lỡ là mất thật) — tally + warnings.
--loop: mỗi vòng một etl_run, nhịp 300 s, sitemap mỗi 3 vòng; --sources: lượt con không đụng domain state."""
from __future__ import annotations

import logging
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import sqlalchemy as sa

from core.env import load_dotenv
from etl import news_extract, news_fetch, news_registry, news_store, news_tag, omo_store
from etl.news_parse import PARSERS, ParseError

log = logging.getLogger("etl.news")
VN = ZoneInfo("Asia/Ho_Chi_Minh")
JOB = "news.collect"
CYCLE_SECONDS = 300
SITEMAP_EVERY = 3
MAX_FAILED_RATE = 0.20
MAX_REFUSED_RATE = 0.05
STALE_DAYS = 7


def _engine():
    url = os.environ.get("ETL_DATABASE_URL")
    if not url:
        raise RuntimeError("thiếu ETL_DATABASE_URL")
    return sa.create_engine(url, pool_pre_ping=True)


def _empty_stats(now_vn, cycle):
    return {"sources_total": 0, "lists_ok": 0, "lists_failed": 0, "lists_stored": 0, "items": 0, "seen": 0, "merged_url": 0,
            "merged_title": 0, "new": 0, "stale_feeds": [], "warnings": [], "calls": 0, "retries": 0,
            "run_date": now_vn.date().isoformat(), "cycle": cycle}


def _newest(items):
    ts = [it.published_at for it in items if it.published_at]
    return max(ts) if ts else None


def collect(engine, registry, *, run_id, now, dry_run, subset, cycle, get, sleep, rng) -> dict:
    now_vn = now.astimezone(VN)
    st = _empty_stats(now_vn, cycle)
    st["sources_total"] = len(registry)
    items: dict[str, object] = {}
    ok_sources: set[str] = set()
    with news_fetch.open_news_fetcher(get=get, sleep=sleep, rng=rng) as f:
        for s in registry:
            if s.kind == "tnck_sitemap" and cycle % SITEMAP_EVERY != 0:
                continue
            url = news_registry.sitemap_url(now_vn) if s.kind == "tnck_sitemap" else s.url
            try:
                text = f.fetch_one(url, f"{s.name}/{s.feed_slug}")[1]
                parsed = PARSERS[s.kind](text, s)
            except (news_fetch.BadShape, news_fetch.FetchError, ParseError) as e:
                st["lists_failed"] += 1
                log.warning("%s", e)
                continue
            st["lists_ok"] += 1
            ok_sources.add(s.name)
            if not dry_run:
                with engine.begin() as c:
                    if news_store.store_list_if_changed(c, s.name, url, text, run_id, "text" if s.kind in ("rss", "tnck_sitemap") else "html"):
                        st["lists_stored"] += 1
            newest = _newest(parsed)
            if s.kind == "rss" and newest and now - newest > timedelta(days=STALE_DAYS):
                st["stale_feeds"].append(f"{s.name}/{s.feed_slug}")
            for it in parsed:
                items.setdefault(it.canonical_url, it)               # cùng kênh qua nhiều slug: bản đầu thắng
        st["items"] = len(items)
        with engine.connect() as c:
            seen = news_store.Seen.load(c, now)
            listed = news_store.load_listed(c)
        if not dry_run:
            st.update({"articles_ok": 0, "articles_failed": 0, "refused": 0, "tickers_url": 0, "tickers_lookup": 0})
        for it in items.values():
            decision, aid = seen.decide(it, now)
            if decision == "seen":
                st["seen"] += 1
                continue
            if decision in ("merge_url", "merge_title"):
                st[decision.replace("merge_", "merged_")] += 1
                if not dry_run:
                    with engine.begin() as c:
                        news_store.add_source(c, aid, it.source, it.url)
                    seen.urls.add(it.url)
                continue
            st["new"] += 1
            if dry_run:
                seen.remember(it, -1, now)
                continue
            try:
                html_text = f.fetch_one(it.url, it.source)[1]
            except (news_fetch.BadShape, news_fetch.FetchError) as e:
                st["articles_failed"] += 1
                log.warning("%s", e)
                continue
            if len(html_text.encode("utf-8")) < news_fetch.ARTICLE_MIN_BYTES:
                st["refused"] += 1
                with engine.begin() as c:
                    news_store.store_refused(c, it.source, it.url, html_text, "soft404", run_id)
                continue
            try:
                ext = news_extract.extract(html_text, it.rule)
            except news_extract.ExtractError as e:
                st["refused"] += 1
                with engine.begin() as c:
                    news_store.store_refused(c, it.source, it.url, html_text, e.reason, run_id)
                continue
            tickers: list[tuple[str, str, int]] = []
            if it.group_from_feed == 3:
                for t in news_tag.tickers_from_url(it.url):
                    if t in listed:
                        tickers.append((t, "url", listed[t]))
                        st["tickers_url"] += 1
                for t in news_tag.tickers_lookup(ext.title, ext.sapo, listed):
                    tickers.append((t, "lookup", listed[t]))
                    st["tickers_lookup"] += 1
            with engine.begin() as c:
                aid = news_store.insert_article(c, it, ext, fetched_at=now, tickers=tickers)
            seen.remember(it, aid, now)
            st["articles_ok"] += 1
        st["calls"], st["retries"] = f.calls, f.retries_done
    lists_total = st["lists_ok"] + st["lists_failed"]
    if lists_total and st["lists_failed"] / lists_total > MAX_FAILED_RATE:
        st["warnings"].append(f"feed/danh sách hỏng {st['lists_failed']}/{lists_total} > {MAX_FAILED_RATE:.0%}")
    if not dry_run and st["new"] and st["refused"] / st["new"] > MAX_REFUSED_RATE:
        st["warnings"].append(f"bóc từ chối {st['refused']}/{st['new']} > {MAX_REFUSED_RATE:.0%}")
    if st["stale_feeds"]:
        st["warnings"].append(f"feed im > {STALE_DAYS} ngày: {st['stale_feeds']}")
    st["_ok_sources"] = sorted(ok_sources)
    if subset:
        st["subset"] = True
    if dry_run:
        st["dry_run"] = True
    return st


def _one_cycle(engine, registry, *, subset, dry_run, cycle, get, sleep, now, rng) -> int:
    run_id = omo_store.open_run(engine, JOB)
    try:
        st = collect(engine, registry, run_id=run_id, now=now, dry_run=dry_run, subset=subset, cycle=cycle, get=get, sleep=sleep, rng=rng)
        ok_sources = set(st.pop("_ok_sources"))
        if not subset and not dry_run:
            st["watermark"] = st["run_date"]
        omo_store.close_run(engine, run_id, "success", st)
        if not subset and not dry_run:
            news_store.upsert_domain_state(engine, ok_sources, st["run_date"])
        log.info("news cycle %s: items %s · new %s · merged %s/%s · seen %s · refused %s · warnings %s",
                 cycle, st["items"], st["new"], st["merged_url"], st["merged_title"], st["seen"], st.get("refused", "-"), st["warnings"])
        return 0
    except KeyboardInterrupt:
        omo_store.close_run(engine, run_id, "failed", error="dừng tay (Ctrl+C)")
        log.warning("news dừng tay (Ctrl+C)")
        return 130
    except Exception as e:                    # noqa: BLE001 — job biên ngoài
        omo_store.close_run(engine, run_id, "failed", error=f"{type(e).__name__}: {e}")
        log.exception("news thất bại")
        return 2


def run(sources=None, dry_run=False, loop=False, minutes=None, get=None, sleep=time.sleep, now=None, rng=None, clock=time.monotonic) -> int:
    logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    load_dotenv()
    try:
        engine = _engine()
        registry = news_registry.build()
        if sources is not None:
            unknown = sorted(set(sources) - set(news_registry.SOURCES))
            if unknown:
                raise RuntimeError(f"báo không có trong registry: {unknown}")
            registry = [s for s in registry if s.name in set(sources)]
    except (RuntimeError, news_registry.RegistryError) as e:
        log.error("%s", e)
        return 2
    subset = sources is not None
    t0 = clock()
    cycle = 0
    try:
        while True:
            started = clock()
            rc = _one_cycle(engine, registry, subset=subset, dry_run=dry_run, cycle=cycle,
                            get=get, sleep=sleep, now=now or datetime.now(timezone.utc), rng=rng)
            if rc != 0 or not loop:
                return rc
            cycle += 1
            if minutes is not None and clock() - t0 >= minutes * 60:
                return 0
            try:
                sleep(max(0.0, CYCLE_SECONDS - (clock() - started)))
            except KeyboardInterrupt:
                log.warning("news dừng tay (Ctrl+C) giữa hai vòng")
                return 130
    finally:
        engine.dispose()
