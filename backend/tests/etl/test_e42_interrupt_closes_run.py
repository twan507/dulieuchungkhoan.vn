"""Ctrl+C giữa lượt phải ĐÓNG SỔ `ops.etl_run` cho CẢ HỌ JOB — không riêng `price_job`.

Nợ ghi ở ledger lát 4 §3 ("open_run ngoài try/except… dọn cả họ job trong một lượt riêng") và roadmap
"Nợ để lại" của lát 6. Hợp đồng (khuôn `price_job` 2026-09-04): `KeyboardInterrupt` ⇒ dòng `etl_run`
`failed`, `error = 'dừng tay (Ctrl+C)'`, hàm trả **130**; không dòng nào treo `running`.

Bước đầu tiên bên trong `try` của mỗi job bị thay bằng hàm ném `KeyboardInterrupt` — đúng thời điểm
người trực bấm Ctrl+C sớm nhất. Trước fix, 7/9 đường để traceback bò ra ngoài và dòng `running` treo.
"""
import os

import pytest
import sqlalchemy as sa

from etl import (events_job, fundamentals_job, omo_job, price_job, refdata_job, screener_job,
                 snapshot_job, wichart_job)

INTERRUPT_ERROR = "dừng tay (Ctrl+C)"
EXIT_INTERRUPTED = 130

# (job trong ops.etl_run, module job, bước đầu tiên trong try, hàm run, kwargs)
CASES = [
    ("macro.omo_crawl", "omo_job", "etl.omo_fetch.fetch", omo_job.run, {}),
    ("market.screener", "screener_job", "etl.screener_fetch.fetch", screener_job.run, {}),
    ("market.events", "events_job", "etl.events_fetch.fetch", events_job.run, {}),
    ("market.refdata", "refdata_job", "etl.refdata_fetch.fetch", refdata_job.run, {}),
    ("market.snapshot", "snapshot_job", "etl.snapshot_store.load_watermark", snapshot_job.run, {}),
    ("market.fundamentals", "fundamentals_job", "etl.fundamentals_store.load_dictionary",
     fundamentals_job.run, {}),
    ("macro.wichart", "wichart_job", "etl.wichart_registry.build", wichart_job.run, {}),
    ("market.price_daily", "price_job", "etl.price_store.list_codes", price_job.run, {}),
    ("market.price_backfill", "price_job", "etl.price_store.list_codes", price_job.run, {"backfill": True}),
]


def _boom(*_a, **_k):
    raise KeyboardInterrupt


def _last_run(engine, job):
    with engine.connect() as c:
        return c.execute(sa.text(
            "SELECT run_id, status, error FROM ops.etl_run WHERE job = :j ORDER BY run_id DESC LIMIT 1"),
            {"j": job}).one_or_none()


@pytest.mark.parametrize("job,module,first_step,run,kwargs", CASES, ids=[c[0] for c in CASES])
def test_ctrl_c_closes_the_run_as_failed_and_returns_130(migrated_engine, monkeypatch, job, module,
                                                          first_step, run, kwargs):
    monkeypatch.setenv("ETL_DATABASE_URL", os.environ["TEST_DATABASE_URL"])   # KHÔNG str(engine.url) — mật khẩu bị che
    monkeypatch.setattr(f"etl.{module}.load_dotenv", lambda *a, **k: None)
    monkeypatch.setattr(first_step, _boom)
    before = _last_run(migrated_engine, job)
    try:
        rc = run(**kwargs)
    except KeyboardInterrupt:
        pytest.fail(f"{job}: KeyboardInterrupt thoát khỏi run() — sổ etl_run không được đóng")
    row = _last_run(migrated_engine, job)
    try:
        assert rc == EXIT_INTERRUPTED
        assert row is not None and (before is None or row.run_id != before.run_id), "lượt chưa được mở sổ"
        assert (row.status, row.error) == ("failed", INTERRUPT_ERROR)
    finally:
        if row is not None and (before is None or row.run_id != before.run_id):
            with migrated_engine.begin() as c:
                c.execute(sa.text("DELETE FROM ops.etl_run WHERE run_id = :r"), {"r": row.run_id})


def test_backfill_failing_before_its_try_block_leaves_no_run_open(migrated_engine, monkeypatch):
    """`_backfill` tính hạn giờ (`_next_open`) SAU `open_run` nhưng TRƯỚC `try` — hỏng ở đó là dòng `running`
    treo mà không except nào đóng. Mở sổ phải là việc cuối cùng trước `try`."""
    monkeypatch.setenv("ETL_DATABASE_URL", os.environ["TEST_DATABASE_URL"])
    monkeypatch.setattr("etl.price_job.load_dotenv", lambda *a, **k: None)
    monkeypatch.setattr("etl.price_job._next_open", _boom_runtime)
    before = _last_run(migrated_engine, "market.price_backfill")
    with pytest.raises(RuntimeError):
        price_job.run(backfill=True, stop_before_open=True)
    after = _last_run(migrated_engine, "market.price_backfill")
    try:
        opened = after is not None and (before is None or after.run_id != before.run_id)
        assert not opened, f"sổ mở rồi bỏ treo: {after}"
    finally:
        if after is not None and (before is None or after.run_id != before.run_id):
            with migrated_engine.begin() as c:
                c.execute(sa.text("DELETE FROM ops.etl_run WHERE run_id = :r"), {"r": after.run_id})


def _boom_runtime(*_a, **_k):
    raise RuntimeError("hạn giờ tính hỏng")
