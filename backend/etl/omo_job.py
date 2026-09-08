"""Một lần chạy crawl OMO: fetch → parse → store → flow. Chạy-rồi-thoát (Task Scheduler)."""
from __future__ import annotations

import logging
import os
import sys

import sqlalchemy as sa

from core.env import load_dotenv
from etl import omo_fetch, omo_flow, omo_parse, omo_store

log = logging.getLogger("etl.omo")
JOB = "macro.omo_crawl"


def run() -> int:
    logging.basicConfig(level=logging.INFO, stream=sys.stderr,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    load_dotenv()
    url = os.environ.get("ETL_DATABASE_URL")
    if not url:
        log.error("thiếu ETL_DATABASE_URL")
        return 2
    engine = sa.create_engine(url, pool_pre_ping=True)  # pool_pre_ping: kết nối trong pool chết sau khi máy ngủ giữa lượt (bài học price_job 2026-09-04)
    run_id = omo_store.open_run(engine, JOB)
    try:
        html = omo_fetch.fetch()
        result = omo_parse.parse(html)
        with engine.begin() as conn:
            stats = omo_store.store(result, html, conn)
            if not stats.get("skipped"):
                stats["flow_rows"] = omo_flow.rebuild(conn)
        omo_store.close_run(engine, run_id, "success", stats)
        omo_store.upsert_domain_state(engine, watermark=result.session_date.isoformat())
        log.info("omo xong: %s", stats)
        return 0
    except KeyboardInterrupt:
        # Ctrl+C là cách dừng chính thức của cửa sổ task — sổ phải ghi lý do, không treo 'running' (khuôn price_job)
        omo_store.close_run(engine, run_id, "failed", error="dừng tay (Ctrl+C)")
        log.warning("omo dừng tay (Ctrl+C)")
        return 130
    except Exception as e:  # noqa: BLE001 — job biên ngoài: mọi lỗi đều phải vào etl_run
        omo_store.close_run(engine, run_id, "failed", error=f"{type(e).__name__}: {e}")
        log.exception("omo thất bại")
        # 2 = lỗi thật (README §"Mã thoát"). `omo` KHÔNG có guard nên 1 ở đây không bao giờ
        # mang nghĩa "chốt chặn từ chối" — trả 1 là nói dối với bảng lịch của lát 13.
        return 2
    finally:
        engine.dispose()
