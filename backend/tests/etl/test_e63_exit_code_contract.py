"""Lỗi THẬT giữa lượt phải trả mã thoát **2** cho CẢ HỌ JOB — không phải 1.

Hợp đồng do `backend/README.md` §"Mã thoát" công bố:
    0 = ghi xong · 1 = **chốt chặn từ chối** (dữ liệu vẫn lành, không cần gọi người) ·
    2 = **lỗi thật** (mạng hỏng sau retry, DB lỗi, bug) — cần người nhìn.

🔴 Vì sao file này ra đời (rà chuẩn hoá 2026-09-07): 13/15 họ tuân đúng, nhưng `omo_job` trả
**1** cho mọi lỗi thật (nó không hề có guard nên `1` ở đó không bao giờ mang nghĩa "chốt chặn"),
và `refdata_job` trả **1** cho CẢ `GuardRefused` LẪN `except Exception` — tức một mã cho hai
tình huống vận hành ngược nhau. Lát 13 sắp thay 11 task Windows bằng bảng lịch trong code, mà
bảng lịch đó đọc mã thoát để quyết có báo động hay không: giữ nguyên là **bỏ sót lỗi thật**.

Cùng khuôn với `test_e42_interrupt_closes_run.py` (hợp đồng Ctrl+C ⇒ 130), chỉ đổi thứ được
ném ở bước đầu tiên: `RuntimeError` thay `KeyboardInterrupt`.
"""
import os

import pytest
import sqlalchemy as sa

from etl import events_job, fundamentals_job, omo_job, price_job, refdata_job, screener_job, snapshot_job, wichart_job

EXIT_REAL_ERROR = 2

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
]


def _boom(*_a, **_k):
    raise RuntimeError("ZZ lỗi thật giả lập")


def _last_run(engine, job):
    with engine.connect() as c:
        return c.execute(sa.text(
            "SELECT run_id, status, error FROM ops.etl_run WHERE job = :j ORDER BY run_id DESC LIMIT 1"),
            {"j": job}).one_or_none()


@pytest.mark.parametrize("job,module,first_step,run,kwargs", CASES, ids=[c[0] for c in CASES])
def test_loi_that_tra_ma_2_va_dong_so_failed(migrated_engine, monkeypatch, job, module,
                                             first_step, run, kwargs):
    monkeypatch.setenv("ETL_DATABASE_URL", os.environ["TEST_DATABASE_URL"])
    monkeypatch.setattr(f"etl.{module}.load_dotenv", lambda *a, **k: None)
    monkeypatch.setattr(first_step, _boom)
    before = _last_run(migrated_engine, job)

    rc = run(**kwargs)
    row = _last_run(migrated_engine, job)
    try:
        assert rc == EXIT_REAL_ERROR, (
            f"{job}: lỗi thật phải trả {EXIT_REAL_ERROR}, nhận {rc} — "
            "mã 1 dành riêng cho chốt chặn từ chối (backend/README.md)")
        assert row is not None and (before is None or row.run_id != before.run_id)
        assert row.status == "failed"
        assert "RuntimeError" in (row.error or "")        # lý do thật vào sổ, không nuốt
    finally:                                              # dọn dòng của chính mình, dù đỏ hay xanh
        if row is not None and (before is None or row.run_id != before.run_id):
            with migrated_engine.begin() as c:
                c.execute(sa.text("DELETE FROM ops.etl_run WHERE run_id = :r"), {"r": row.run_id})
