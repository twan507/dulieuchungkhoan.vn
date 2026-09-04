"""Một lượt chạy fundamentals: từ điển → due_list → fetch+normalize → guard → apply (spec §5.1).

Y khuôn `snapshot_job.run`: MỘT giao dịch cho dữ liệu, guard đánh giá TRƯỚC commit — từ chối thì
raise bên trong `engine.begin()` để tự rollback; bằng chứng ghi ở giao dịch riêng. Không re-crawl.
Hạn theo đồng hồ TƯỜNG như `price_job._backfill`: máy ngủ 02:00 rồi thức dậy là hết ngân sách.
"""
from __future__ import annotations

import logging
import os
import sys
import time
from datetime import datetime

import sqlalchemy as sa

from core.env import load_dotenv
from etl import fundamentals_fetch, fundamentals_guard, fundamentals_normalize, fundamentals_store, omo_store
from etl.fundamentals_fetch import BadShape, FetchError
from etl.fundamentals_normalize import BadRecord
from etl.price_job import VN, _next_open

log = logging.getLogger("etl.fundamentals")
JOB = fundamentals_store.JOB
_wall_clock = time.time                  # seam cho test


class GuardRefused(Exception):
    def __init__(self, verdict):
        self.verdict = verdict
        super().__init__("; ".join(verdict.reasons))


def _engine():
    url = os.environ.get("ETL_DATABASE_URL")
    if not url:
        raise RuntimeError("thiếu ETL_DATABASE_URL")
    return sa.create_engine(url, pool_pre_ping=True)


def _fetch_all(targets, get, sleep, deadline):
    fetched, failed, bad_shape, stopped = [], 0, 0, False
    with fundamentals_fetch.open_fetcher(get=get, sleep=sleep) as f:
        for i, t in enumerate(targets, 1):
            if deadline is not None and _wall_clock() > deadline:
                stopped = True
                log.info("hết ngân sách thời gian sau %d/%d target", i - 1, len(targets))
                break
            try:
                item, text = f.fetch_one(t)
                rows = fundamentals_normalize.rows(t.kind, item)
                fetched.append(fundamentals_store.Fetched(target=t, text=text, rows=rows))
            except (BadShape, BadRecord) as e:
                bad_shape += 1
                log.warning("%s/%s sai hợp đồng: %s", t.organ_code, t.kind, e)
            except FetchError as e:
                failed += 1
                log.warning("%s", e)
            if i % 50 == 0:
                log.info("đã gọi %d/%d target (%d lời gọi, %d retry)", i, len(targets), f.calls, f.retries)
        return fetched, failed, bad_shape, stopped, f.calls, f.retries


def run(codes=None, kinds=None, max_minutes=None, backfill=False, stop_before_open=False,
        get=None, sleep=time.sleep) -> int:
    logging.basicConfig(level=logging.INFO, stream=sys.stderr,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    load_dotenv()
    subset = codes is not None or kinds is not None      # lượt con: không đẩy mốc nước toàn bảng
    try:
        engine = _engine()
    except RuntimeError as e:
        log.error("%s", e)
        return 2
    run_id = omo_store.open_run(engine, JOB)
    try:
        with engine.begin() as conn:
            n_dict = fundamentals_store.load_dictionary(conn)       # hợp đồng khởi động: hỏng thì chết trước fetch
            watermark = fundamentals_store.load_watermark(conn)
            targets = fundamentals_store.due_list(conn, watermark, kinds=kinds, codes=codes, backfill=backfill)
            new_wm = fundamentals_store.new_watermark(conn)          # cùng giao dịch với due_list — không đọc lại sau fetch
        log.info("từ điển %d mã; tới hạn: %d target (%d theo sự kiện)", n_dict, len(targets),
                 sum(1 for t in targets if t.found_by == "event"))

        deadlines = []
        if max_minutes is not None:
            deadlines.append(_wall_clock() + max_minutes * 60)
        if stop_before_open:
            deadlines.append(_next_open(datetime.now(VN)).timestamp())
        deadline = min(deadlines) if deadlines else None
        stop_at = datetime.fromtimestamp(deadline, VN).isoformat(timespec="minutes") if deadline else None

        fetched, failed, bad_shape, stopped, calls, retries = _fetch_all(targets, get, sleep, deadline)
        run_date = datetime.now(VN).date()
        try:
            with engine.begin() as conn:
                tally, written = fundamentals_store.apply(conn, fetched, run_id)
                tally.attempted = len(targets)
                tally.failed, tally.bad_shape = failed, bad_shape
                verdict = fundamentals_guard.check(tally)
                if not verdict.ok:
                    raise GuardRefused(verdict)
                left = fundamentals_store.remaining(conn, kinds)
        except GuardRefused as e:
            fundamentals_store.store_refusal_evidence(engine, fetched, run_id, e.verdict)
            omo_store.close_run(engine, run_id, "failed", error="guard refused: " + "; ".join(e.verdict.reasons))
            log.error("fundamentals từ chối: %s", e.verdict.reasons)
            return 1

        stats = {"tally": vars(tally), "rows_written": written, "calls": calls, "retries": retries,
                 "stopped_early": stopped, "run_date": run_date.isoformat(),
                 "dictionary_rows": n_dict, "remaining": left, "stop_at": stop_at}
        if subset:
            stats["subset"] = True
        if backfill:
            stats["backfill"] = True

        # Mốc nước chỉ tiến khi lượt ĐẦY ĐỦ và KHÔNG target nào hỏng/sai hình dạng/rỗng/bị cắt —
        # đẩy mốc khi còn target chưa phục vụ là mất trigger vĩnh viễn (bài học lát 4).
        push = not subset and failed == 0 and bad_shape == 0 and tally.empty == 0 and not stopped
        if push:
            stats["watermark"] = new_wm.isoformat()
        elif not subset:
            stats["watermark_held"] = True
        omo_store.close_run(engine, run_id, "success", stats)       # close_run TRƯỚC, domain state SAU
        if push:
            fundamentals_store.upsert_domain_state(engine, new_wm.isoformat())
        log.info("fundamentals xong: %s", stats)
        return 0
    except Exception as e:                    # noqa: BLE001 — job biên ngoài: mọi lỗi vào etl_run
        omo_store.close_run(engine, run_id, "failed", error=f"{type(e).__name__}: {e}")
        log.exception("fundamentals thất bại")
        return 2
    finally:
        engine.dispose()
