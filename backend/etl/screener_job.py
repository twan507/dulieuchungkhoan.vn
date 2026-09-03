"""Một lần chạy screener: fetch → normalize → merge → guard → apply → close_run (spec §5.1).

Y khuôn `refdata_job.py`: một giao dịch cho dữ liệu; guard đánh giá TRƯỚC commit —
từ chối thì raise bên trong `with engine.begin()` để tự rollback; bằng chứng ở giao dịch riêng.
"""
from __future__ import annotations

import logging
import os
import sys

import sqlalchemy as sa

from core.env import load_dotenv
from etl import omo_store, screener_fetch, screener_guard, screener_normalize, screener_store

log = logging.getLogger("etl.screener")
JOB = screener_store.JOB


class GuardRefused(Exception):
    def __init__(self, reasons):
        self.reasons = list(reasons)
        super().__init__("; ".join(self.reasons))


def run() -> int:
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
        pages, retries = screener_fetch.fetch()
        n = screener_normalize.normalize(pages)
        priced = sum(1 for r in n.rows if r.close_price > 0)
        baseline = screener_store.load_baseline(engine)
        try:
            with engine.begin() as conn:
                mapped, unmapped = screener_store.merge(conn, n.rows)
                verdict = screener_guard.check(n.total_count, len(n.rows) + n.unknown_com_group,
                                               priced, unmapped, baseline)
                if not verdict.ok:
                    raise GuardRefused(verdict.reasons)
                apply_stats = screener_store.apply(conn, mapped)
        except GuardRefused as e:
            screener_store.store_refusal_evidence(engine, pages, run_id, e.reasons)
            omo_store.close_run(engine, run_id, "failed", error=f"guard refused: {'; '.join(e.reasons)}")
            log.error("screener từ chối: %s", e.reasons)
            return 1
        trading_date = max(r.trading_date for r in n.rows).isoformat()
        stats = {"counts": {"items": n.total_count, "pages": len(pages), "priced": priced},
                 **apply_stats, "unmapped": unmapped, "unknown_com_group": n.unknown_com_group,
                 "null_blocks": n.null_blocks, "retries": retries, "trading_date": trading_date}
        omo_store.close_run(engine, run_id, "success", stats)
        screener_store.upsert_domain_state(engine, trading_date)
        log.info("screener xong: %s", stats)
        return 0
    except Exception as e:  # noqa: BLE001 — job biên ngoài: mọi lỗi đều phải vào etl_run
        omo_store.close_run(engine, run_id, "failed", error=f"{type(e).__name__}: {e}")
        log.exception("screener thất bại")
        return 2
    finally:
        engine.dispose()
