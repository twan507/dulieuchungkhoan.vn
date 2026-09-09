"""Planner thuần — spec lát 13 §5.8. Ngày thật: 2026-09-09 thứ 4 · 12/09 thứ 7 · 13/09 chủ nhật."""
from datetime import datetime, timedelta, timezone

from core.clock import VN
from etl.scheduler import planner
from etl.scheduler.planner import LedgerRow, day_bounds_utc, due
from etl.scheduler.schedule import ALL_DAYS, MON_FRI, SCHEDULE, JobSpec


def vn(d, h, mi):
    return datetime(2026, 9, d, h, mi, tzinfo=VN)


def row(job, h, mi, status="success", stats=None, d=9):
    return LedgerRow(job, vn(d, h, mi), vn(d, h, mi) + timedelta(minutes=1), status, stats or {}, None)


PRICE = JobSpec("market.price_daily", ("price",), "daily", times=((15, 40),))
EVENTS = JobSpec("market.events", ("events",), "daily", times=((18, 10),))
SNAP = JobSpec("market.snapshot", ("snapshot",), "daily", depends_on="market.events")
OMO = JobSpec("macro.omo_crawl", ("omo",), "daily", weekdays=ALL_DAYS, times=((11, 30), (15, 30), (18, 0), (21, 30)))
BF = JobSpec("market.price_backfill", ("price", "--backfill", "--stop-before-open"), "weekly_once", weekdays=(5,), times=((0, 5),), once_until_flag="pass_complete")
INTRA = JobSpec("global.yahoo", ("yahoo", "--intraday"), "intraday", weekdays=ALL_DAYS, interval_s=600)
DAEMON = JobSpec("news.collect", ("news", "--loop"), "daemon")


def names(tasks):
    return [t.spec.name for t in tasks]


def test_day_bounds_utc_for_a_vn_night():
    start, end = day_bounds_utc(datetime(2026, 9, 10, 0, 30, tzinfo=VN))
    assert start == datetime(2026, 9, 9, 17, 0, tzinfo=timezone.utc) and end == datetime(2026, 9, 10, 17, 0, tzinfo=timezone.utc)


def test_due_fires_once_the_mark_has_passed_with_no_success():
    assert names(due([PRICE], vn(9, 15, 41), [])) == ["market.price_daily"]
    assert due([PRICE], vn(9, 15, 40), [])[0].reason == "mốc 15:40"


def test_not_due_before_the_mark_or_on_a_weekend():
    assert due([PRICE], vn(9, 15, 39), []) == []
    assert due([PRICE], vn(12, 16, 0), []) == []              # thứ 7, MON_FRI


def test_silent_once_marked_success_after_the_mark():
    assert due([PRICE], vn(9, 16, 0), [row("market.price_daily", 15, 42)]) == []


def test_a_success_before_the_mark_does_not_count():
    assert names(due([PRICE], vn(9, 16, 0), [row("market.price_daily", 10, 0)])) == ["market.price_daily"]   # lượt thử tải buổi sáng


def test_omo_recatches_the_15_30_slot_but_is_quiet_after_a_fresh_success():
    assert names(due([OMO], vn(9, 15, 31), [row("macro.omo_crawl", 11, 35)])) == ["macro.omo_crawl"]
    assert due([OMO], vn(9, 15, 35), [row("macro.omo_crawl", 15, 31)]) == []


def test_snapshot_waits_for_events_then_fires():
    assert due([EVENTS, SNAP], vn(9, 20, 0), [row("market.events", 18, 12, "failed", {"guard_refused": True})]) == []
    tasks = due([EVENTS, SNAP], vn(9, 18, 13), [row("market.events", 18, 12)])
    assert names(tasks) == ["market.snapshot"] and tasks[0].reason == "chuỗi: cha market.events success"


def test_a_child_success_older_than_the_parents_latest_success_does_not_count():
    """Ghim luật mắt xích CHẶT HƠN câu chữ spec §5.8 ("cha xong thì con chạy"): mốc của con là
    `started_at` của lượt `success` MỚI NHẤT hôm nay của cha, và chỉ dòng con có `started_at >= mốc
    đó` mới tính. Một lượt `snapshot` thành công TRƯỚC lượt `events` mới nhất không được coi là đã
    phục vụ dữ liệu của lượt cha đó — nó chạy trên sự kiện cũ, nên con vẫn phải chạy lại.

    Đây là hành vi đang có (test này không đổi code), viết ra để lát sau đừng "đơn giản hoá" thành
    "cha có success ⇒ con thôi" mà không biết mình đang bỏ mất một lượt chạy bù."""
    parent = row("market.events", 18, 12)
    assert names(due([EVENTS, SNAP], vn(9, 18, 30), [parent, row("market.snapshot", 18, 5)])) == ["market.snapshot"]
    assert due([EVENTS, SNAP], vn(9, 18, 30), [parent, row("market.snapshot", 18, 20)]) == []


def test_exit2_retries_once_after_ten_minutes_then_stops():
    fail = row("market.price_daily", 15, 41, "failed")
    assert due([PRICE], vn(9, 15, 49), [fail]) == []
    tasks = due([PRICE], vn(9, 15, 52), [fail])
    assert names(tasks) == ["market.price_daily"] and tasks[0].reason == "thử lại sau exit 2 lúc 15:41"
    assert due([PRICE], vn(9, 16, 30), [fail, row("market.price_daily", 15, 53, "failed")]) == []


def test_guard_refused_never_retries_the_same_day():
    assert due([PRICE], vn(9, 20, 0), [row("market.price_daily", 15, 41, "failed", {"guard_refused": True})]) == []


def test_running_rows_are_ignored():
    assert names(due([PRICE], vn(9, 15, 45), [row("market.price_daily", 15, 41, "running")])) == ["market.price_daily"]


def test_saturday_backfill_due_at_00_05_and_off_forever_after_pass_complete():
    assert names(due([BF], vn(12, 0, 5), [])) == ["market.price_backfill"]
    assert due([BF], vn(13, 0, 5), []) == []                                        # chủ nhật
    assert due([BF], vn(12, 10, 0), [], once_done=frozenset({"market.price_backfill"})) == []


def test_intraday_and_daemon_never_appear():
    assert due([INTRA, DAEMON], vn(9, 12, 0), []) == []


def test_schedule_is_the_spec_table():
    assert len(SCHEDULE) == 19
    assert [s.name for s in SCHEDULE if s.kind == "daemon"] == ["news.collect", "market.price_backfill"]
    assert not [s for s in SCHEDULE if s.kind == "weekly_once"]
    assert next(s for s in SCHEDULE if s.name == "market.price_backfill").once_until_flag == "pass_complete"
    assert [s.interval_s for s in SCHEDULE if s.kind == "intraday"] == [600, 300, 300]
    classify = next(s for s in SCHEDULE if s.name == "news.classify")
    assert classify.times == ((7, 0), (9, 0), (11, 0), (13, 0), (15, 0), (17, 0), (19, 0), (21, 0)) and classify.weekdays == ALL_DAYS
    assert next(s for s in SCHEDULE if s.name == "market.fundamentals").depends_on == "market.snapshot"
    assert next(s for s in SCHEDULE if s.name == "macro.wichart" and s.kind == "daily").times == ((8, 15),)
    assert next(s for s in SCHEDULE if s.name == "market.refdata").weekdays == MON_FRI
