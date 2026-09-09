"""Vòng lặp scheduler — nối planner thuần và runner với sổ `ops.etl_run` thật (spec lát 13 §5.6, §5.8, §5.10).

Ba việc, không hơn: đọc sổ (SQL ở đây, `read_today`/`once_done`/`summary_lines`), chạy một nhịp
(`run_once`), và vòng 20 giây có cờ dừng (`main`). Mọi quyết định "job nào tới lượt" nằm ở
`planner.due` (thuần, kiểm được bằng literal), mọi việc với tiến trình con nằm ở `runner`.

Trạng thái sống ở SỔ, không ở RAM: tiến trình chết giữa ngày rồi bật lại vẫn ra đúng quyết định,
vì mỗi nhịp đều đọc lại `ops.etl_run` của ngày VN hôm nay.
"""
from __future__ import annotations

import logging
import os
import signal
import sys
import threading
from collections.abc import Mapping
from datetime import datetime, timedelta
from pathlib import Path

import sqlalchemy as sa

from core.clock import now_vn, today_vn
from core.env import REPO_ROOT, load_dotenv
from etl.scheduler.planner import LedgerRow, day_bounds_utc, due
from etl.scheduler.runner import Runner
from etl.scheduler.schedule import SCHEDULE, SUMMARY_AT, TICK_SECONDS, JobSpec, job_names

log = logging.getLogger("etl.scheduler")

# Native (dev): log ra NGOÀI repo, cạnh `dlck-runtime/logs` của ingester — không rác trong cây git.
# Container: `ETL_LOG_DIR` trỏ vào volume (Task 10).
DEFAULT_LOG_DIR = REPO_ROOT.parent / "dlck-runtime" / "etl-logs"

# Sổ hôm nay (spec §5.8). Ba cờ `intraday`/`subset`/`dry_run` bị loại vì đó là những lượt KHÔNG
# thay mặt cho mốc trong ngày: coi chúng là "đã chạy" thì mốc trọn ngày bị nuốt.
_TODAY_SQL = sa.text("""
SELECT job, started_at, finished_at, status, stats, error
FROM ops.etl_run
WHERE started_at >= :day_start_utc AND started_at < :day_end_utc
  AND job = ANY(:job_names)
  AND coalesce(stats->>'intraday','false') <> 'true'
  AND coalesce(stats->>'subset','false')   <> 'true'
  AND coalesce(stats->>'dry_run','false')  <> 'true'
ORDER BY job, started_at
""")

_ONCE_DONE_SQL = sa.text(
    "SELECT DISTINCT job FROM ops.etl_run"
    " WHERE status = 'success' AND stats->>'pass_complete' = 'true'")

# Đếm 24 giờ qua theo job. Bốn kết cục của hợp đồng mã thoát (README §"Mã thoát") đọc từ sổ:
# success · exit 1 (`guard_refused`, trong đó khoá bận là một loại) · exit 2 (hỏng thật) · 130
# (Ctrl+C/SIGTERM — sổ chỉ có ba `status`, dấu vết duy nhất của 130 là câu `error` chung của 11 họ).
_SUMMARY_SQL = sa.text("""
SELECT job,
       count(*) FILTER (WHERE status = 'success')                                   AS success,
       count(*) FILTER (WHERE status = 'failed' AND stats->>'guard_refused' = 'true') AS refused,
       count(*) FILTER (WHERE status = 'failed' AND stats->>'lock_busy' = 'true')     AS lock_busy,
       count(*) FILTER (WHERE status = 'failed'
                          AND coalesce(stats->>'guard_refused','false') <> 'true'
                          AND strpos(coalesce(error,''), 'Ctrl+C') = 0)             AS failed,
       count(*) FILTER (WHERE status = 'failed' AND strpos(coalesce(error,''), 'Ctrl+C') > 0) AS interrupted
FROM ops.etl_run
WHERE started_at >= :since
GROUP BY job
ORDER BY job
""")


def resolve_log_dir(env: Mapping[str, str]) -> Path:
    """Thư mục log của tiến trình con, tạo sẵn nếu chưa có. Thuần theo `env` truyền vào."""
    raw = env.get("ETL_LOG_DIR")
    path = Path(raw) if raw else DEFAULT_LOG_DIR
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_today(engine, now_vn: datetime, job_names: list[str]) -> list[LedgerRow]:
    """Sổ `ops.etl_run` của NGÀY VN chứa `now_vn`, chỉ các job trong bảng lịch (spec §5.8)."""
    day_start_utc, day_end_utc = day_bounds_utc(now_vn)
    with engine.connect() as conn:
        rows = conn.execute(_TODAY_SQL, {"day_start_utc": day_start_utc, "day_end_utc": day_end_utc,
                                         "job_names": list(job_names)}).all()
    return [LedgerRow(r.job, r.started_at, r.finished_at, r.status, r.stats or {}, r.error) for r in rows]


def once_done(engine) -> frozenset[str]:
    """Job `weekly_once` đã trọn một lượt (luật 6) — hỏi MỌI thời điểm, không chỉ hôm nay: cờ
    `pass_complete` là "xong hẳn", đọc theo ngày thì thứ 7 sau lại chạy lại từ đầu."""
    with engine.connect() as conn:
        return frozenset(conn.execute(_ONCE_DONE_SQL).scalars().all())


def summary_lines(engine, now_vn: datetime) -> list[str]:
    """Bảng đếm 24 giờ qua, mỗi job một dòng (spec §5.10 "Tóm tắt sáng")."""
    with engine.connect() as conn:
        rows = conn.execute(_SUMMARY_SQL, {"since": now_vn - timedelta(hours=24)}).all()
    return [f"{r.job} success={r.success} refused={r.refused} lock_busy={r.lock_busy}"
            f" failed={r.failed} interrupted={r.interrupted}" for r in rows]


def run_once(engine, runner: Runner, now_vn: datetime, *, schedule: list[JobSpec] = SCHEDULE) -> dict:
    """Một nhịp: daemon → intraday → mốc tới hạn → thu hoạch con đã thoát → dọn log cũ.

    Thứ tự có ý: daemon được đảm bảo trước (không tính trần), rồi intraday theo đồng hồ runner, rồi
    mới tới các mốc — task nào bị trần chặn thì nhịp sau `due()` tính lại từ sổ, không cần nhớ gì.
    `poll` chạy MỌI nhịp: con đã thoát chỉ rời khỏi "đang sống" khi được thu hoạch.
    """
    spawned: list[str] = []
    for spec in schedule:
        if spec.kind == "daemon" and runner.ensure_daemon(spec, now_vn):
            spawned.append(spec.name)
    spawned += runner.tick_intraday([s for s in schedule if s.kind == "intraday"], now_vn)
    ledger = read_today(engine, now_vn, job_names(schedule))
    spawned += runner.reconcile(due(schedule, now_vn, ledger, once_done(engine)), now_vn)
    finished = runner.poll(now_vn)
    runner.prune_old_logs(now_vn)
    return {"spawned": spawned, "finished": finished}


def _daemon_alive_line(runner: Runner, schedule: list[JobSpec]) -> list[str]:
    """Dòng "news --loop đang sống từ HH:MM" của bản tóm tắt sáng (spec §5.10)."""
    lines = []
    for spec in schedule:
        if spec.kind != "daemon":
            continue
        # `Runner` chưa có accessor công khai cho giờ khởi động của con; đọc bản ghi qua `_children`
        # sau khi `alive()` xác nhận còn sống (một dòng, không đáng mở thêm API ở runner).
        if runner.alive(spec.name):
            lines.append(f"{' '.join(spec.cmd)} đang sống từ {runner._children[spec.name].started_at:%H:%M}")
        else:
            lines.append(f"{' '.join(spec.cmd)} KHÔNG sống")
    return lines


def main(argv: list[str] | None = None) -> int:      # noqa: ARG001 — không nhận tham số, giữ chữ ký cho `__main__`
    """Vòng 20 giây tới khi có cờ dừng. Thiếu `ETL_DATABASE_URL` ⇒ 2; dừng sạch ⇒ 0."""
    logging.basicConfig(level=logging.INFO, stream=sys.stderr,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    load_dotenv()
    url = os.environ.get("ETL_DATABASE_URL")
    if not url:
        log.error("thiếu ETL_DATABASE_URL")
        return 2
    # Đọc tường minh (ruling R3): `tests/core/test_env_contract.py` quét literal trong code sản phẩm
    # để biết biến `.env` nào còn người đọc.
    log_dir = resolve_log_dir({"ETL_LOG_DIR": os.environ.get("ETL_LOG_DIR", "")})
    engine = sa.create_engine(url, pool_pre_ping=True)   # pool_pre_ping: kết nối trong pool chết sau khi máy ngủ
    runner = Runner(log_dir)

    stop = threading.Event()

    def _flag_stop(signum, frame):  # noqa: ARG001 — chữ ký handler của `signal`
        stop.set()

    # Đăng ký SAU `core.shutdown.install_signal_handlers()` của `etl.__main__` nên thắng nó: scheduler
    # KHÔNG được chết ngay khi có SIGTERM, phải đóng từng con có trật tự rồi mới thoát (§5.10).
    signal.signal(signal.SIGINT, _flag_stop)
    if hasattr(signal, "SIGTERM"):          # Windows có hằng số nhưng không bao giờ gửi tín hiệu này
        signal.signal(signal.SIGTERM, _flag_stop)

    print(f"scheduler: {len(job_names())} job, log_dir={log_dir}, tick {TICK_SECONDS}s", flush=True)
    summary_printed_on = None
    try:
        while not stop.is_set():
            now = now_vn()
            try:
                run_once(engine, runner, now)
            except Exception:
                # Một sự cố thoáng qua (vd Postgres rớt giữa nhịp) không được kéo chết cả vòng
                # supervisor: log rồi thử lại ở nhịp sau, không backoff, không đếm.
                log.exception("scheduler: nhịp lỗi, thử lại sau %ss", TICK_SECONDS)
            if (now.hour, now.minute) >= SUMMARY_AT and today_vn(now) != summary_printed_on:
                for line in summary_lines(engine, now) + _daemon_alive_line(runner, SCHEDULE):
                    print(line, flush=True)
                summary_printed_on = today_vn(now)
            stop.wait(TICK_SECONDS)
    finally:
        try:
            runner.shutdown()
        finally:
            engine.dispose()
    return 0
