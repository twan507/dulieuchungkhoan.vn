"""Bảng lịch của scheduler — DỮ LIỆU thuần, không I/O, không logic (spec lát 13 §5.7).

Mọi giờ là **giờ Việt Nam** (`core.clock.VN`); `weekdays` theo `datetime.weekday()` (0 = thứ 2).
Cùng một `name` được phép xuất hiện nhiều dòng (bản trọn ngày và bản `--intraday`): tên là khoá
của `ops.etl_run`, còn chống chạy chồng do runner lo theo `spec.name` (§5.9 lớp ngoài).
"""
from __future__ import annotations

from dataclasses import dataclass

MON_FRI = (0, 1, 2, 3, 4)
ALL_DAYS = (0, 1, 2, 3, 4, 5, 6)
SAT = (5,)

MAX_CONCURRENT_CHILDREN = 6     # trần tiến trình con chạy song song
RETRY_AFTER_MIN = 10            # exit 2 chỉ được thử lại sau ngần này phút, đúng một lần
TICK_SECONDS = 20               # nhịp vòng lặp loop.py
SHUTDOWN_GRACE_S = 60           # SIGTERM: chờ con tự tắt trước khi giết
LOG_KEEP_DAYS = 30              # log theo ngày giữ bao lâu
SUMMARY_AT = (6, 0)             # giờ VN phát bản tổng kết ngày


@dataclass(frozen=True)
class JobSpec:
    name: str                       # tên trong ops.etl_run
    cmd: tuple[str, ...]            # sau `python -m etl`
    kind: str                       # daily | intraday | daemon | weekly_once
    times: tuple[tuple[int, int], ...] = ()
    weekdays: tuple[int, ...] = MON_FRI
    depends_on: str | None = None
    interval_s: int | None = None
    once_until_flag: str | None = None


SCHEDULE: list[JobSpec] = [
    JobSpec("market.refdata",      ("refdata",),      "daily", times=((8, 0),)),
    JobSpec("market.screener",     ("screener",),     "daily", times=((15, 20),)),
    JobSpec("market.price_daily",  ("price",),        "daily", times=((15, 40),)),
    JobSpec("market.events",       ("events",),       "daily", times=((18, 10),)),
    JobSpec("market.snapshot",     ("snapshot",),     "daily", depends_on="market.events"),
    JobSpec("market.fundamentals", ("fundamentals",), "daily", depends_on="market.snapshot"),
    JobSpec("macro.omo_crawl", ("omo",), "daily", weekdays=ALL_DAYS, times=((11, 30), (15, 30), (18, 0), (21, 30))),
    JobSpec("macro.wichart",  ("wichart",), "daily", weekdays=ALL_DAYS, times=((8, 15),)),
    JobSpec("global.yahoo",   ("yahoo",),   "daily", weekdays=ALL_DAYS, times=((11, 0),)),
    JobSpec("global.binance", ("binance",), "daily", weekdays=ALL_DAYS, times=((7, 15),)),
    JobSpec("global.fred",    ("fred",),    "daily", weekdays=ALL_DAYS, times=((5, 0), (20, 0))),
    JobSpec("global.ecb",     ("fx",),      "daily", weekdays=ALL_DAYS, times=((22, 30),)),
    JobSpec("global.lbma",    ("lbma",),    "daily", weekdays=ALL_DAYS, times=((22, 30),)),
    # Ba dòng --intraday chạy 24/7 theo đồng hồ của runner, planner bỏ qua: ALL_DAYS cho khỏi
    # đọc nhầm là chỉ chạy ngày thường (mặc định MON_FRI).
    JobSpec("global.yahoo",   ("yahoo", "--intraday"),   "intraday", weekdays=ALL_DAYS, interval_s=600),
    JobSpec("global.binance", ("binance", "--intraday"), "intraday", weekdays=ALL_DAYS, interval_s=300),
    JobSpec("macro.wichart",  ("wichart", "--intraday"), "intraday", weekdays=ALL_DAYS, interval_s=300),
    JobSpec("news.classify", ("classify", "--limit", "1000"), "daily", weekdays=ALL_DAYS,
            times=((7, 0), (9, 0), (11, 0), (13, 0), (15, 0), (17, 0), (19, 0), (21, 0))),
    JobSpec("news.collect", ("news", "--loop"), "daemon"),
    JobSpec("market.price_backfill", ("price", "--backfill", "--stop-before-open"), "weekly_once",
            weekdays=SAT, times=((0, 5),), once_until_flag="pass_complete"),
    # lát 14: một dòng JobSpec giám sát tại đây
]


def job_names(schedule: list[JobSpec] = SCHEDULE) -> list[str]:
    """Tên job duy nhất, giữ thứ tự bảng (một tên có nhiều dòng chỉ kể một lần) — dùng cho
    `job = ANY(:job_names)` khi loop đọc sổ hôm nay."""
    return list(dict.fromkeys(s.name for s in schedule))
