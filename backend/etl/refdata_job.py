"""Một lần chạy refdata: fetch → normalize → merge → guard → store → close_run.

Y khuôn `omo_job.py` (`open_run`/`close_run` của `omo_store`). Một giao dịch
duy nhất cho việc ghi dữ liệu; chốt chặn hai tầng (`refdata_guard`) đánh giá
TRƯỚC commit — từ chối thì raise `GuardRefused` bên trong `with engine.begin()`
để giao dịch tự rollback, bằng chứng ghi ở giao dịch riêng (spec §4.3).
"""
from __future__ import annotations

import logging
import os
import sys
from datetime import date

import sqlalchemy as sa

from core.env import load_dotenv
from etl import omo_store, refdata_fetch, refdata_guard, refdata_merge, refdata_normalize, refdata_store
from etl.refdata_indices import SNAP_CODES

log = logging.getLogger("etl.refdata")
JOB = refdata_store.JOB


class GuardRefused(Exception):
    """Chốt chặn hai tầng từ chối lượt chạy — giao dịch dữ liệu phải rollback."""

    def __init__(self, reasons):
        self.reasons = list(reasons)
        super().__init__("; ".join(self.reasons))


def run(accept_drop: bool = False) -> int:
    logging.basicConfig(level=logging.INFO, stream=sys.stderr,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    load_dotenv()
    url = os.environ.get("ETL_DATABASE_URL")
    if not url:
        log.error("thiếu ETL_DATABASE_URL")
        return 2
    engine = sa.create_engine(url)
    run_id = omo_store.open_run(engine, JOB)
    try:
        raw = refdata_fetch.fetch()
        n = refdata_normalize.normalize(raw)
        t = refdata_merge.merge(n)
        counts = {"quotes": len(n.quotes), "organization": len(n.orgs), "icb": len(n.icb)}
        baseline = refdata_store.load_baseline(engine)
        try:
            with engine.begin() as conn:
                delist, planned_flips, listed = refdata_store.plan_delist(conn, t)
                verdict = refdata_guard.check(
                    counts, baseline, n.index_codes, SNAP_CODES, planned_flips, listed
                )
                if not verdict.ok and not accept_drop:
                    raise GuardRefused(verdict.reasons)
                apply_stats = refdata_store.apply(conn, t, delist)
        except GuardRefused as e:
            refdata_store.store_refusal_evidence(engine, raw, run_id, e.reasons)
            omo_store.close_run(engine, run_id, "failed", error=f"guard refused: {'; '.join(e.reasons)}")
            log.error("refdata từ chối: %s", e.reasons)
            return 1
        stats = {**apply_stats, "counts": counts, **t.counters}
        if accept_drop:
            stats["accept_drop"] = True
        omo_store.close_run(engine, run_id, "success", stats)
        refdata_store.upsert_domain_state(engine, date.today().isoformat())
        log.info("refdata xong: %s", stats)
        return 0
    except KeyboardInterrupt:
        # Ctrl+C là cách dừng chính thức của cửa sổ task — sổ phải ghi lý do, không treo 'running' (khuôn price_job)
        omo_store.close_run(engine, run_id, "failed", error="dừng tay (Ctrl+C)")
        log.warning("refdata dừng tay (Ctrl+C)")
        return 130
    except Exception as e:  # noqa: BLE001 — job biên ngoài: mọi lỗi đều phải vào etl_run
        omo_store.close_run(engine, run_id, "failed", error=f"{type(e).__name__}: {e}")
        log.exception("refdata thất bại")
        return 1
    finally:
        engine.dispose()
