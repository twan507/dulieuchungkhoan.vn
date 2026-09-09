"""Planner thuần — quyết định job nào tới lượt chạy (spec lát 13 §5.8, sáu luật chạy bù).

Không I/O, không đồng hồ: `now_vn` và sổ `ops.etl_run` của hôm nay đều do `loop.py` truyền vào.
Nhờ thế cả sáu luật kiểm được bằng literal ngày giờ, và bật lại máy giữa ngày cũng ra đúng
quyết định như thể tiến trình chưa từng chết — trạng thái nằm ở sổ, không nằm trong bộ nhớ.
"""
from __future__ import annotations

from collections import namedtuple
from dataclasses import dataclass
from datetime import datetime, time as dtime, timedelta, timezone

from core.clock import VN, today_vn
from etl.scheduler.schedule import RETRY_AFTER_MIN, JobSpec

# started_at/finished_at tz-aware (Postgres trả UTC), stats là dict, error là str | None
LedgerRow = namedtuple("LedgerRow", "job started_at finished_at status stats error")


@dataclass(frozen=True)
class Task:
    spec: JobSpec
    reason: str        # nhánh luật đã sinh ra lượt này, ghi thẳng vào log


def day_bounds_utc(now_vn: datetime) -> tuple[datetime, datetime]:
    """Nửa khoảng [đầu ngày, đầu ngày sau) của NGÀY VN chứa `now_vn`, đổi sang UTC cho câu SQL.

    Biên ngày tính ở Python rồi truyền UTC: để Postgres tự cắt theo `current_date` là rơi lại
    đúng bẫy UTC đã trả giá 2026-09-05 (xem `core.clock`).
    """
    d = today_vn(now_vn)
    start = datetime.combine(d, dtime(0, 0), tzinfo=VN)
    end = datetime.combine(d + timedelta(days=1), dtime(0, 0), tzinfo=VN)
    return start.astimezone(timezone.utc), end.astimezone(timezone.utc)


def last_mark(spec: JobSpec, now_vn: datetime) -> datetime | None:
    """Mốc giờ gần nhất ĐÃ QUA trong hôm nay. None nếu sai thứ, không có mốc nào, hoặc chưa tới
    mốc đầu tiên — bốn mốc OMO dùng chung một tên job nên chỉ mốc gần nhất mới đáng hỏi."""
    if now_vn.weekday() not in spec.weekdays or not spec.times:
        return None
    passed = [datetime.combine(now_vn.date(), dtime(h, m), tzinfo=now_vn.tzinfo)
              for h, m in spec.times if (h, m) <= (now_vn.hour, now_vn.minute)]
    return max(passed) if passed else None


def _parent_mark(spec: JobSpec, ledger: list[LedgerRow]) -> datetime | None:
    """Mốc của job mắt xích: `started_at` của lượt `success` MỚI NHẤT hôm nay của cha.
    Cha chưa xong ⇒ None ⇒ con nằm im (thứ tự events → snapshot → fundamentals)."""
    ok = [r.started_at for r in ledger if r.job == spec.depends_on and r.status == "success"]
    return max(ok) if ok else None


def _verdict(spec: JobSpec, mark: datetime, now_vn: datetime, rows: list[LedgerRow]) -> str | None:
    """Luật 5 trên các dòng của chính job này có `started_at >= mark`: trả None nếu KHÔNG due,
    `"mốc"` nếu due lần đầu, hoặc nguyên câu lý do nếu là lượt thử lại sau exit 2.

    Dòng `running` không tính vào đâu cả: runner mới là chỗ chặn chạy chồng (§5.9), planner mà
    coi `running` là "đã xong" thì một lượt treo sẽ nuốt luôn mốc của ngày hôm đó.
    """
    since = [r for r in rows if r.job == spec.name and r.started_at >= mark]
    if any(r.status == "success" for r in since):
        return None
    if any(r.status == "failed" and (r.stats or {}).get("guard_refused") is True for r in since):
        return None       # exit 1: dữ liệu lành, chưa tới lượt — chạy lại cũng chỉ từ chối tiếp
    real = sorted((r for r in since if r.status == "failed"), key=lambda r: r.started_at)
    if not real:
        return "mốc"
    if len(real) == 1 and now_vn >= real[0].started_at + timedelta(minutes=RETRY_AFTER_MIN):
        return f"thử lại sau exit 2 lúc {real[0].started_at.astimezone(now_vn.tzinfo):%H:%M}"
    return None           # chưa đủ 10 phút, hoặc đã hỏng hai lần: thôi, để người xem


def due(schedule: list[JobSpec], now_vn: datetime, ledger: list[LedgerRow],
        once_done: frozenset[str] = frozenset()) -> list[Task]:
    """Các job tới lượt tại `now_vn`, theo đúng thứ tự bảng lịch.

    `ledger` là sổ `ops.etl_run` của NGÀY VN hôm nay (luật 2 — biên ngày do `day_bounds_utc` cắt);
    `once_done` là tên các `weekly_once` đã có lượt `success` mang `stats.pass_complete = true`,
    tắt vĩnh viễn (luật 6). `intraday`/`daemon` không bao giờ ra ở đây (luật 3).
    """
    tasks: list[Task] = []
    for spec in schedule:
        if spec.kind in ("intraday", "daemon"):
            continue
        if spec.kind == "weekly_once" and spec.name in once_done:
            continue
        if spec.depends_on:
            mark, chain = _parent_mark(spec, ledger), True
        else:
            mark, chain = last_mark(spec, now_vn), False
        if mark is None:
            continue
        verdict = _verdict(spec, mark, now_vn, ledger)
        if verdict is None:
            continue
        if verdict == "mốc":
            verdict = f"chuỗi: cha {spec.depends_on} success" if chain else f"mốc {mark:%H:%M}"
        tasks.append(Task(spec, verdict))
    return tasks
