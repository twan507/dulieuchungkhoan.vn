"""Một lần chạy events: fetch → normalize → ensure_issuers → guard → apply → close_run.

Y khuôn `screener_job.py`: một giao dịch cho dữ liệu; guard đánh giá TRƯỚC commit —
từ chối thì raise bên trong `with engine.begin()` để tự rollback (kể cả issuer vừa tạo);
bằng chứng ghi ở giao dịch riêng.
"""
from __future__ import annotations

import logging
import os
import sys

import sqlalchemy as sa

from core.env import load_dotenv
from etl import events_fetch, events_guard, events_normalize, events_store, omo_store

log = logging.getLogger("etl.events")
JOB = events_store.JOB


class GuardRefused(Exception):
    def __init__(self, verdict):
        self.verdict = verdict
        super().__init__("; ".join(verdict.reasons))


def run(accept_new: bool = False) -> int:
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
        pages, retries = events_fetch.fetch()
        n = events_normalize.normalize(pages)
        baseline = events_store.load_baseline(engine)
        try:
            with engine.begin() as conn:
                issuer_by_organ, issuers_new = events_store.ensure_issuers(conn, n.rows)
                verdict = events_guard.check(n.counts, n.collected, baseline, issuers_new,
                                             n.dup_conflicts, len(n.rows), accept_new=accept_new)
                if not verdict.ok:
                    raise GuardRefused(verdict)
                apply_stats = events_store.apply(conn, n.rows, issuer_by_organ)
        except GuardRefused as e:
            events_store.store_refusal_evidence(engine, pages, run_id, e.verdict,
                                                n.counts, n.collected)
            omo_store.close_run(engine, run_id, "failed",
                                error="guard refused: " + "; ".join(e.verdict.reasons))
            log.error("events từ chối: %s", e.verdict.reasons)
            return 1
        watermark = max(r.public_date for r in n.rows if r.public_date).isoformat()
        stats = {"counts": n.counts, "collected": n.collected, **apply_stats,
                 "issuers_created": issuers_new, "dup_conflicts": n.dup_conflicts,
                 "dup_keys": n.dup_keys, "retries": retries, "watermark": watermark}
        if accept_new:
            # Khuôn `refdata_job` ghi `accept_drop`: phải để lại dấu vết rằng CÓ NGƯỜI bấm
            # qua chốt chặn (iii). Không có dấu này thì về sau nhìn `issuers_created: 517`
            # không phân biệt được "người duyệt" với "guard hỏng".
            stats["accept_new"] = True
        omo_store.close_run(engine, run_id, "success", stats)
        events_store.upsert_domain_state(engine, watermark)
        log.info("events xong: %s", {k: v for k, v in stats.items() if k != "dup_keys"})
        return 0
    except Exception as e:  # noqa: BLE001 — job biên ngoài: mọi lỗi đều phải vào etl_run
        omo_store.close_run(engine, run_id, "failed", error=f"{type(e).__name__}: {e}")
        log.exception("events thất bại")
        return 2
    finally:
        engine.dispose()
