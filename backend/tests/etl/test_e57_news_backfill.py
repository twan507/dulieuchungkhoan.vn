"""Backfill sitemap TinnhanhCK: tháng lùi, bỏ trang chủ, bỏ URL đã có, mỗi bài một giao dịch, con trỏ tháng, hạn giờ, cầu chì 10 bài."""
import os
from datetime import datetime, timedelta, timezone

import pytest
import sqlalchemy as sa

from etl import news_job as nj
from tests.etl.test_e56_news_job import _cleanup, _page, NAMES  # noqa: F401 — cùng khuôn dọn/dựng trang

VN = timezone(timedelta(hours=7))
NOW = datetime(2026, 9, 6, 0, 0, tzinfo=VN)
SM = ('<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
      '<url><loc>https://www.tinnhanhchungkhoan.vn</loc><lastmod>2026-09-06T00:00:00+07:00</lastmod></url>'
      '<url><loc>https://www.tinnhanhchungkhoan.vn/a-post1.html</loc><lastmod>2026-08-01T08:00:00+07:00</lastmod></url>'
      '<url><loc>https://www.tinnhanhchungkhoan.vn/b-post2.html</loc><lastmod>2026-08-02T08:00:00+07:00</lastmod></url>'
      '<url><loc>https://www.tinnhanhchungkhoan.vn/c-post3.html</loc><lastmod>2026-08-03T08:00:00+07:00</lastmod></url></urlset>')


def _get(months_seen=None, fail=()):
    def get(u, timeout):
        if "/sitemaps/news-" in u:
            if months_seen is not None:
                months_seen.append(u.rsplit("news-", 1)[1].replace(".xml", ""))
            return 200, SM, {}
        if any(f in u for f in fail):
            return 503, "", {}
        return 200, _page("tinnhanhck", "Bài " + u.rsplit("/", 1)[1]) * 9, {}   # ×6 không đủ 5 KB (đo e56) — ×9 an toàn
    return get


@pytest.fixture()
def clean(migrated_engine, monkeypatch):
    monkeypatch.setenv("ETL_DATABASE_URL", os.environ["TEST_DATABASE_URL"])
    monkeypatch.setattr("etl.news_job.load_dotenv", lambda *a, **k: None)
    _cleanup(migrated_engine)
    yield migrated_engine
    _cleanup(migrated_engine)


def _last(engine):
    with engine.connect() as c:
        return c.execute(sa.text("SELECT status, stats, error FROM ops.etl_run WHERE job='news.backfill_sitemap' ORDER BY run_id DESC LIMIT 1")).one()


def _n(engine, sql):
    with engine.connect() as c:
        return c.execute(sa.text(sql)).scalar()


def test_months_desc_and_cursor_resume():
    assert nj.months_desc("2026-07", "2026-09") == ["2026-09", "2026-08", "2026-07"]
    assert nj.months_desc("2025-11", "2026-01") == ["2026-01", "2025-12", "2025-11"]
    with pytest.raises(ValueError):
        nj.months_desc("2026-9", "2026-09")


def test_backfill_one_month_skips_homepage_and_seen_urls_and_sets_cursor(clean):
    with clean.begin() as c:
        c.execute(sa.text("INSERT INTO news.article (canonical_url, primary_source, fetched_at) VALUES ('https://www.tinnhanhchungkhoan.vn/b-post2.html','tinnhanhck',now()) RETURNING article_id"))
        aid = c.execute(sa.text("SELECT article_id FROM news.article")).scalar()
        c.execute(sa.text("INSERT INTO news.article_revision (article_id, version, title, content, content_fetched_at) VALUES (:a,1,'b','x',now())"), {"a": aid})
        c.execute(sa.text("INSERT INTO news.article_source (article_id, source_name, url) VALUES (:a,'tinnhanhck','https://www.tinnhanhchungkhoan.vn/b-post2.html')"), {"a": aid})
    months = []
    assert nj.run_backfill("2026-08", "2026-08", get=_get(months), sleep=lambda s: None, now=NOW) == 0
    status, stats, _ = _last(clean)
    assert status == "success" and months == ["2026-8"] and stats["months_done"] == ["2026-08"] and stats["cursor"] == "2026-08"
    assert stats["urls_in_sitemap"] == 3 and stats["skipped_seen"] == 1 and stats["articles_ok"] == 2 and stats["budget_hit"] is False
    with clean.connect() as c:
        rows = c.execute(sa.text("SELECT canonical_url, feed, published_at, published_at_src, group_from_feed FROM news.article ORDER BY canonical_url")).all()
    assert [r[0][-13:] for r in rows] == ["/a-post1.html", "/b-post2.html", "/c-post3.html"]
    a = rows[0]
    assert a[1] == "sitemap" and a[2] == datetime(2026, 8, 1, 8, 0, tzinfo=VN) and a[3] == "feed" and a[4] is None   # trang tổng hợp không có cms-date ⇒ lastmod
    assert nj.run_backfill("2026-08", "2026-08", get=_get(), sleep=lambda s: None, now=NOW) == 0
    assert _last(clean)[1]["articles_ok"] == 0 and _last(clean)[1]["skipped_seen"] == 3


def test_month_fetch_failure_is_recorded_and_backfill_continues_to_next_month(clean):
    # I2: tháng đầu (2026-09, to_month mặc định = tháng hiện tại theo NOW) hỏng (503) không được làm mất
    # stats/cursor của tháng sau — ghi nhận vào months_failed rồi ĐI TIẾP, không đếm vào streak cầu chì bài.
    def get(u, timeout):
        if "/sitemaps/news-2026-9.xml" in u:
            return 503, "", {}
        if "/sitemaps/news-" in u:
            return 200, SM, {}
        return 200, _page("tinnhanhck", "Bài " + u.rsplit("/", 1)[1]) * 9, {}
    assert nj.run_backfill("2026-08", get=get, sleep=lambda s: None, now=NOW) == 0
    status, stats, _ = _last(clean)
    assert status == "success" and stats["months_failed"] == ["2026-09"]
    assert stats["months_done"] == ["2026-08"] and stats["cursor"] == "2026-08"
    assert stats["articles_ok"] == 3                              # SM (tháng 08) có 3 URL bài thật, kho trống ⇒ cả 3 mới
    assert _n(clean, "SELECT count(*) FROM news.article") == stats["articles_ok"]


def test_cursor_resumes_from_month_before_last_done(clean):
    months = []
    assert nj.run_backfill("2026-07", "2026-09", get=_get(months), sleep=lambda s: None, now=NOW, max_minutes=None) == 0
    assert months == ["2026-9", "2026-8", "2026-7"] and _last(clean)[1]["cursor"] == "2026-07"
    assert nj.load_cursor(clean) == "2026-07"
    months.clear()
    assert nj.run_backfill("2026-05", "2026-09", get=_get(months), sleep=lambda s: None, now=NOW) == 0
    assert months == ["2026-6", "2026-5"]                                                  # nối sau con trỏ, không lặp 09/08/07


def test_budget_stops_after_current_article_and_keeps_it(clean):
    ticks = iter([0.0] + [10 * 60.0] * 50)                                                 # sau bài đầu tiên đã hết 5 phút
    assert nj.run_backfill("2026-08", "2026-08", max_minutes=5, get=_get(), sleep=lambda s: None, now=NOW, clock=lambda: next(ticks)) == 0
    status, stats, _ = _last(clean)
    assert status == "success" and stats["budget_hit"] is True and stats["articles_ok"] == 1 and stats["months_done"] == [] and stats["cursor"] is None
    assert _n(clean, "SELECT count(*) FROM news.article") == 1


def test_budget_is_checked_after_refused_and_skipped_articles_too(clean):
    def get(u, timeout):
        if "/sitemaps/" in u:
            return 200, SM, {}
        return 200, "<html><body>" + "x" * 6000 + "</body></html>", {}   # >=5 KB nhưng không có div.article__body ⇒ refused no_container
    ticks = iter([0.0] + [999.0] * 50)                                  # sau bài đầu tiên đã hết ngân sách
    assert nj.run_backfill("2026-08", "2026-08", max_minutes=5, get=get, sleep=lambda s: None, now=NOW, clock=lambda: next(ticks)) == 0
    status, stats, _ = _last(clean)
    assert status == "success" and stats["budget_hit"] is True
    assert stats["refused"] == 1 and stats["articles_ok"] == 0
    assert stats["cursor"] is None and stats["months_done"] == []


def test_stop_before_open_stops_after_current_article(clean, monkeypatch):
    monkeypatch.setattr("etl.news_job._next_open", lambda now: now - timedelta(seconds=1))   # đã hết giờ ngay từ đầu
    assert nj.run_backfill("2026-08", "2026-08", stop_before_open=True, get=_get(), sleep=lambda s: None, now=NOW) == 0
    status, stats, _ = _last(clean)
    assert status == "success" and stats["stop_at"] is not None
    assert stats["budget_hit"] is True and stats["articles_ok"] == 1
    assert stats["cursor"] is None
    assert _n(clean, "SELECT count(*) FROM news.article") == 1


def test_ten_consecutive_failures_trip_the_breaker(clean):
    sm = "".join(f'<url><loc>https://www.tinnhanhchungkhoan.vn/x{i}-post{i}.html</loc><lastmod>2026-08-01T08:00:00+07:00</lastmod></url>' for i in range(12))
    def get(u, timeout):
        return (200, f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>', {}) if "/sitemaps/" in u else (503, "", {})
    assert nj.run_backfill("2026-08", "2026-08", get=get, sleep=lambda s: None, now=NOW) == 1
    status, stats, err = _last(clean)
    assert status == "failed" and "10 bài liên tiếp" in err and stats["articles_failed"] == 10 and stats["cursor"] is None
