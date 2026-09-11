"""Backfill sitemap TinnhanhCK: tháng lùi, bỏ trang chủ, bỏ URL đã có, mỗi bài một giao dịch, con trỏ tháng, hạn giờ, cầu chì 10 bài."""
import os
from datetime import datetime, timedelta, timezone

import pytest
import sqlalchemy as sa
from tests.etl.test_e56_news_job import NAMES, _cleanup, _page  # noqa: F401 — cùng khuôn dọn/dựng trang

from etl import news_job as nj

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
        return c.execute(sa.text("SELECT status, stats, error FROM ops.etl_run WHERE job='news.backfill_sitemap:tinnhanhck' ORDER BY run_id DESC LIMIT 1")).one()


def _n(engine, sql):
    with engine.connect() as c:
        return c.execute(sa.text(sql)).scalar()


def test_periods_desc_month_and_day():
    from datetime import date
    assert nj.periods_desc("tinnhanhck", "2026-07", "2026-09") == ["2026-09", "2026-08", "2026-07"]
    assert nj.periods_desc("bnews", "2025-11", "2026-01") == ["2026-01", "2025-12", "2025-11"]
    d = nj.periods_desc("nguoiquansat", "2026-08", "2026-08", today=date(2026, 9, 6))
    assert len(d) == 31 and d[0] == "2026-08-31" and d[-1] == "2026-08-01" and d == sorted(d, reverse=True)
    assert len(nj.periods_desc("nguoiquansat", "2026-02", "2026-03", today=date(2026, 9, 6))) == 59      # 2026 không nhuận
    assert len(nj.periods_desc("nguoiquansat", "2024-02", "2024-02", today=date(2026, 9, 6))) == 29      # 2024 nhuận
    # tháng hiện tại: không sinh ngày tương lai
    assert nj.periods_desc("nguoiquansat", "2026-09", "2026-09", today=date(2026, 9, 6))[0] == "2026-09-06"
    assert nj.periods_desc("nguoiquansat", "2026-10", "2026-10", today=date(2026, 9, 6)) == []
    # nguồn THÁNG cũng không sinh kỳ tương lai (trước đây chỉ nguồn ngày mới cắt today)
    assert nj.periods_desc("bnews", "2026-08", "2026-12", today=date(2026, 9, 6)) == ["2026-09", "2026-08"]
    assert nj.periods_desc("tinnhanhck", "2026-10", "2026-11", today=date(2026, 9, 6)) == []
    with pytest.raises(ValueError):
        nj.periods_desc("bnews", "2026-9", "2026-09")


def test_backfill_one_month_skips_homepage_and_seen_urls_and_sets_cursor(clean):
    with clean.begin() as c:
        c.execute(sa.text("INSERT INTO news.article (canonical_url, primary_source, fetched_at) VALUES ('https://www.tinnhanhchungkhoan.vn/b-post2.html','tinnhanhck',now()) RETURNING article_id"))
        aid = c.execute(sa.text("SELECT article_id FROM news.article")).scalar()
        c.execute(sa.text("INSERT INTO news.article_revision (article_id, version, title, content, content_fetched_at) VALUES (:a,1,'b','x',now())"), {"a": aid})
        c.execute(sa.text("INSERT INTO news.article_source (article_id, source_name, url) VALUES (:a,'tinnhanhck','https://www.tinnhanhchungkhoan.vn/b-post2.html')"), {"a": aid})
    months = []
    assert nj.run_backfill("2026-08", "2026-08", get=_get(months), sleep=lambda s: None, now=NOW) == 0
    status, stats, _ = _last(clean)
    assert status == "success" and months == ["2026-8"] and stats["periods_done"] == ["2026-08"] and stats["cursor"] == "2026-08"
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
    # stats/cursor của tháng sau — ghi nhận vào periods_failed rồi ĐI TIẾP, không đếm vào streak cầu chì bài.
    # §4.2-V: kỳ hỏng là kỳ ĐẦU ⇒ con trỏ đóng băng ở None (chưa có kỳ trọn nào trước đó) dù 2026-08 xong sau đó.
    def get(u, timeout):
        if "/sitemaps/news-2026-9.xml" in u:
            return 503, "", {}
        if "/sitemaps/news-" in u:
            return 200, SM, {}
        return 200, _page("tinnhanhck", "Bài " + u.rsplit("/", 1)[1]) * 9, {}
    assert nj.run_backfill("2026-08", get=get, sleep=lambda s: None, now=NOW) == 0
    status, stats, _ = _last(clean)
    assert status == "success" and stats["periods_failed"] == ["2026-09"]
    assert stats["periods_done"] == ["2026-08"] and stats["cursor"] is None
    assert stats["articles_ok"] == 3                              # SM (tháng 08) có 3 URL bài thật, kho trống ⇒ cả 3 mới
    assert _n(clean, "SELECT count(*) FROM news.article") == stats["articles_ok"]


def test_cursor_resumes_from_month_before_last_done(clean):
    months = []
    assert nj.run_backfill("2026-07", "2026-09", get=_get(months), sleep=lambda s: None, now=NOW, max_minutes=None) == 0
    assert months == ["2026-9", "2026-8", "2026-7"] and _last(clean)[1]["cursor"] == "2026-07"
    assert nj.load_cursor(clean, "tinnhanhck") == "2026-07"
    months.clear()
    assert nj.run_backfill("2026-05", "2026-09", get=_get(months), sleep=lambda s: None, now=NOW) == 0
    assert months == ["2026-6", "2026-5"]                                                  # nối sau con trỏ, không lặp 09/08/07


def test_budget_stops_after_current_article_and_keeps_it(clean):
    ticks = iter([0.0] + [10 * 60.0] * 50)                                                 # sau bài đầu tiên đã hết 5 phút
    assert nj.run_backfill("2026-08", "2026-08", max_minutes=5, get=_get(), sleep=lambda s: None, now=NOW, clock=lambda: next(ticks)) == 0
    status, stats, _ = _last(clean)
    assert status == "success" and stats["budget_hit"] is True and stats["articles_ok"] == 1 and stats["periods_done"] == [] and stats["cursor"] is None
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
    assert stats["cursor"] is None and stats["periods_done"] == []


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


BN = ('<?xml version="1.0" encoding="utf-8" ?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
      '<url><loc>https://bnews.vn</loc><lastmod>2026-09-05T22:57:40Z</lastmod></url>'
      '<url><loc>https://bnews.vn/photo/trang-1.html</loc><lastmod>2026-09-05T22:57:40Z</lastmod></url>'
      '<url><loc>https://bnews.vn/video/trang-1.html</loc><lastmod>2026-09-05T22:57:40Z</lastmod></url>'
      '<url><loc>https://bnews.vn/a/435003.html</loc><lastmod>2026-08-31T21:00:00+07:00</lastmod></url>'
      '<url><loc>https://bnews.vn/b/435002.html</loc><lastmod>2026-08-15T09:00:00+07:00</lastmod></url>'
      '<url><loc>https://bnews.vn/c/435001.html</loc><lastmod>2026-08-01T05:30:00+07:00</lastmod></url></urlset>')
NQ = ('<?xml version="1.0" encoding="utf-8"?><urlset xmlns:image="http://www.google.com/schemas/sitemap-image/1.1" xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
      '<url><loc>https://nguoiquansat.vn/x-{d}01.html</loc><image:image><image:loc>https://nqs.1cdn.vn/a.jpg</image:loc></image:image><lastmod>2026-08-{d}T23:00:01+07:00</lastmod></url>'
      '<url><loc>https://nguoiquansat.vn/y-{d}02.html</loc><lastmod>2026-08-{d}T08:00:01+07:00</lastmod></url></urlset>')


def _get_src(seen=None):
    """Fake get cho ba nguồn: sitemap theo URL mẫu, trang bài dựng theo RULES của nguồn (×9 để qua sàn 5 KB)."""
    def get(u, timeout):
        if "bnews.vn/sitemap/news-" in u:
            if seen is not None:
                seen.append(u.rsplit("news-", 1)[1].replace(".xml", ""))
            return 200, BN, {}
        if "nguoiquansat.vn/sitemap-article-" in u:
            full = u.rsplit("sitemap-article-", 1)[1].replace(".xml", "")   # 'YYYY-MM-DD' — dùng cho seen, không phải cho mẫu NQ
            if seen is not None:
                seen.append(full)
            return 200, NQ.replace("{d}", full[-2:]), {}
        if "/sitemaps/news-" in u:
            if seen is not None:
                seen.append(u.rsplit("news-", 1)[1].replace(".xml", ""))
            return 200, SM, {}
        rule = "bnews" if "bnews.vn" in u else "nguoiquansat" if "nguoiquansat.vn" in u else "tinnhanhck"
        return 200, _page(rule, "Bài " + u.rsplit("/", 1)[1]) * 9, {}
    return get


def _last_of(engine, source):
    with engine.connect() as c:
        return c.execute(sa.text("SELECT status, stats FROM ops.etl_run WHERE job=:j ORDER BY run_id DESC LIMIT 1"),
                         {"j": f"news.backfill_sitemap:{source}"}).one()


def test_backfill_bnews_month_skips_non_articles_and_seen_and_sets_own_cursor(clean):
    with clean.begin() as c:
        aid = c.execute(sa.text("INSERT INTO news.article (canonical_url, primary_source, feed, fetched_at) VALUES ('https://bnews.vn/b/435002.html','bnews','sitemap',now()) RETURNING article_id")).scalar()
        c.execute(sa.text("INSERT INTO news.article_source (article_id, source_name, url) VALUES (:a,'bnews','https://bnews.vn/b/435002.html')"), {"a": aid})
    months = []
    assert nj.run_backfill("2026-08", "2026-08", source="bnews", get=_get_src(months), sleep=lambda s: None, now=NOW) == 0
    assert months == ["2026-8"]
    status, stats = _last_of(clean, "bnews")
    assert status == "success" and stats["source"] == "bnews" and stats["period_unit"] == "month"
    assert stats["urls_in_sitemap"] == 3 and stats["skipped_seen"] == 1 and stats["articles_ok"] == 2 and stats["articles_failed"] == 0
    assert stats["periods_done"] == ["2026-08"] and stats["cursor"] == "2026-08" and stats["periods_failed"] == []
    assert _n(clean, "SELECT count(*) FROM news.article WHERE primary_source='bnews' AND feed='sitemap' AND group_from_feed IS NULL") == 3
    assert _n(clean, "SELECT published_at FROM news.article WHERE canonical_url='https://bnews.vn/c/435001.html'") == datetime(2026, 8, 1, 5, 30, tzinfo=VN)
    assert _n(clean, "SELECT published_at_src FROM news.article WHERE canonical_url='https://bnews.vn/c/435001.html'") == "feed"
    assert _n(clean, "SELECT count(*) FROM news.article_source WHERE source_name='bnews'") == 3
    assert nj.load_cursor(clean, "bnews") == "2026-08" and nj.load_cursor(clean, "tinnhanhck") is None and nj.load_cursor(clean, "nguoiquansat") is None


def test_backfill_nguoiquansat_walks_days_desc_and_cursor_is_a_day(clean):
    days = []
    assert nj.run_backfill("2026-08", "2026-08", source="nguoiquansat", get=_get_src(days), sleep=lambda s: None, now=NOW) == 0
    assert days[0] == "2026-08-31" and days[-1] == "2026-08-01" and len(days) == 31
    status, stats = _last_of(clean, "nguoiquansat")
    assert status == "success" and stats["period_unit"] == "day" and stats["cursor"] == "2026-08-01" and len(stats["periods_done"]) == 31
    assert stats["articles_ok"] == 62 and stats["urls_in_sitemap"] == 62
    assert _n(clean, "SELECT count(*) FROM news.article WHERE primary_source='nguoiquansat'") == 62
    # lượt hai cùng tham số: con trỏ đã ở ngày 1 ⇒ không còn kỳ nào — không mở etl_run mới, exit 0
    n_runs = _n(clean, "SELECT count(*) FROM ops.etl_run WHERE job='news.backfill_sitemap:nguoiquansat'")
    assert nj.run_backfill("2026-08", "2026-08", source="nguoiquansat", get=_get_src(), sleep=lambda s: None, now=NOW) == 0
    assert _n(clean, "SELECT count(*) FROM ops.etl_run WHERE job='news.backfill_sitemap:nguoiquansat'") == n_runs


def test_day_budget_resumes_from_day_before_cursor(clean):
    ticks = iter([0.0] * 10 + [10 * 60.0] * 500)            # ~4 bài rồi hết 5 phút (mỗi URL kiểm clock sau khi xong)
    assert nj.run_backfill("2026-08", "2026-08", source="nguoiquansat", max_minutes=5, get=_get_src(), sleep=lambda s: None, now=NOW, clock=lambda: next(ticks)) == 0
    status, stats = _last_of(clean, "nguoiquansat")
    assert status == "success" and stats["budget_hit"] is True and 1 <= len(stats["periods_done"]) <= 5
    cur = stats["cursor"]
    assert cur is not None and cur.startswith("2026-08-")
    days = []
    assert nj.run_backfill("2026-08", "2026-08", source="nguoiquansat", get=_get_src(days), sleep=lambda s: None, now=NOW) == 0
    assert days[0] < cur and days[-1] == "2026-08-01" and cur not in days    # nối sau con trỏ, không lặp ngày đã xong


def test_day_sitemap_403_after_retries_freezes_cursor_before_failed_period(clean):
    # §4.2-V: kỳ hỏng → periods_failed, con trỏ KHÔNG vượt qua kỳ đó — lượt sau tự đi lại từ kỳ hỏng, Seen lo bài đã có.
    calls = {"n": 0}

    def get(u, timeout):
        if "sitemap-article-2026-08-30" in u:
            calls["n"] += 1
            if calls["n"] <= 4:                                                 # lượt 1: 4 lần (1 + 3 retry) đều 403
                return 403, "<html>Access Denied..</html>", {}
        return _get_src()(u, timeout)
    assert nj.run_backfill("2026-08", "2026-08", source="nguoiquansat", get=get, sleep=lambda s: None, now=NOW) == 0
    status, stats = _last_of(clean, "nguoiquansat")
    assert status == "success" and stats["periods_failed"] == ["2026-08-30"] and "2026-08-30" not in stats["periods_done"]
    assert len(stats["periods_done"]) == 30 and stats["articles_ok"] == 60
    assert stats["cursor"] == "2026-08-31"                                        # đóng băng TRƯỚC kỳ hỏng, dù 29 kỳ sau đã xong
    # lượt hai: WAF hết chặn ⇒ đi lại từ 30/08, các ngày đã xong chỉ tốn một lời gọi sitemap + skipped_seen
    days = []

    def get2(u, timeout):
        if "sitemap-article-" in u:
            days.append(u.rsplit("-", 3)[1:4])
        return _get_src()(u, timeout)
    assert nj.run_backfill("2026-08", "2026-08", source="nguoiquansat", get=get2, sleep=lambda s: None, now=NOW) == 0
    status2, stats2 = _last_of(clean, "nguoiquansat")
    assert "-".join(days[0]).replace(".xml", "") == "2026-08-30" and len(days) == 30
    assert stats2["periods_failed"] == [] and stats2["articles_ok"] == 2 and stats2["skipped_seen"] == 58 and stats2["cursor"] == "2026-08-01"


def test_month_sitemap_403_on_first_period_freezes_cursor_at_none(clean):
    # kỳ hỏng ngay từ kỳ ĐẦU (2026-09) ⇒ chưa có kỳ trọn nào trước đó để đóng băng ⇒ cursor is None.
    calls = {"n": 0}

    def get(u, timeout):
        if "bnews.vn/sitemap/news-2026-9.xml" in u:
            calls["n"] += 1
            if calls["n"] <= 4:
                return 403, "<html>Access Denied..</html>", {}
        return _get_src()(u, timeout)
    assert nj.run_backfill("2026-08", "2026-09", source="bnews", get=get, sleep=lambda s: None, now=NOW) == 0
    status, stats = _last_of(clean, "bnews")
    assert status == "success" and stats["periods_failed"] == ["2026-09"] and stats["periods_done"] == ["2026-08"]
    assert stats["cursor"] is None
    # lượt hai: WAF hết chặn ⇒ đi lại cả hai tháng (cursor None ⇒ không cắt periods)
    seen = []
    assert nj.run_backfill("2026-08", "2026-09", source="bnews", get=_get_src(seen), sleep=lambda s: None, now=NOW) == 0
    status2, stats2 = _last_of(clean, "bnews")
    assert seen == ["2026-9", "2026-8"] and stats2["cursor"] == "2026-08"


def test_tinnhanhck_cursor_falls_back_to_legacy_job_name(clean):
    with clean.begin() as c:
        c.execute(sa.text("INSERT INTO ops.etl_run (job, started_at, finished_at, status, stats) VALUES ('news.backfill_sitemap', now(), now(), 'success', '{\"cursor\": \"2026-08\"}'::jsonb)"))
    assert nj.load_cursor(clean, "tinnhanhck") == "2026-08"
    assert nj.load_cursor(clean, "bnews") is None
    months = []
    assert nj.run_backfill("2026-07", "2026-09", get=_get_src(months), sleep=lambda s: None, now=NOW) == 0
    assert months == ["2026-7"]                                             # nối sau con trỏ cũ 2026-08 của lát 8
    with clean.begin() as c:
        c.execute(sa.text("INSERT INTO ops.etl_run (job, started_at, finished_at, status, stats) VALUES ('news.backfill_sitemap:tinnhanhck', now(), now(), 'success', '{\"cursor\": \"2026-05\"}'::jsonb)"))
    assert nj.load_cursor(clean, "tinnhanhck") == "2026-05"                  # run_id lớn hơn thắng, bất kể tên


def test_unknown_source_returns_2_without_a_run(clean):
    assert nj.run_backfill("2026-08", "2026-08", source="cafef", get=_get_src(), sleep=lambda s: None, now=NOW) == 2
    assert _n(clean, "SELECT count(*) FROM ops.etl_run WHERE job LIKE 'news.backfill_sitemap%'") == 0


def test_run_backfill_disposes_engine_on_early_returns(clean, monkeypatch):
    # Lỗ có sẵn từ lát 8: return 0 ("không còn gì để làm") và return 2 (nguồn lạ/tham số sai) nằm ngoài finally dispose.
    class Wrap:
        def __init__(self, real):
            self.real, self.disposed = real, False

        def connect(self):
            return self.real.connect()

        def begin(self):
            return self.real.begin()

        def dispose(self):
            self.disposed = True
    wraps = []

    def fake_engine():
        w = Wrap(clean)
        wraps.append(w)
        return w
    monkeypatch.setattr(nj, "_engine", fake_engine)
    with clean.begin() as c:
        c.execute(sa.text("INSERT INTO ops.etl_run (job, started_at, finished_at, status, stats) VALUES ('news.backfill_sitemap:nguoiquansat', now(), now(), 'success', '{\"cursor\": \"2026-08-01\"}'::jsonb)"))
    assert nj.run_backfill("2026-08", "2026-08", source="nguoiquansat", get=_get_src(), sleep=lambda s: None, now=NOW) == 0   # hết kỳ
    assert nj.run_backfill("2026-9", "2026-09", source="bnews", get=_get_src(), sleep=lambda s: None, now=NOW) == 2          # --from sai dạng
    assert len(wraps) == 2 and all(w.disposed for w in wraps)
