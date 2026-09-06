"""Seam S4 — sự kiện doanh nghiệp.

Expected lấy từ fixture `kho` (backend/tests/agent/conftest.py) — chốt hồi quy, không phải đo
kho dev thật (§4.4.4 — tiêu chí phải bất biến):
  FPT, event_type='CashDividend', public_date trong 2025 -> 2 dòng,
  exright_date = 2025-06-12 và 2025-12-01. payload không có tỷ lệ chi trả (NULL).
Sáu event_type có thật trong kho: Earning, AGM, CashDividend, ShareIssuance, StockDividend, IPO.
"""
import json

import sqlalchemy as sa

from agent.tools.get_corporate_events import su_kien_doanh_nghiep


def test_co_tuc_tien_mat_fpt_2025(db, kho):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(su_kien_doanh_nghiep(db, "FPT", "CashDividend", "2025-01-01", "2025-12-31"))
    assert out["so_dong"] == 2
    ngay = sorted(e["ngay_gdkhq"] for e in out["du_lieu"])
    assert ngay == ["2025-06-12", "2025-12-01"]


def test_loai_su_kien_la_bi_tu_choi_kem_danh_sach(db, kho):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(su_kien_doanh_nghiep(db, "FPT", "KhongCoLoaiNay"))
    assert out["loi"] is True
    assert "CashDividend" in out["loai_hop_le"]


def test_ma_khong_ton_tai(db, kho):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    assert json.loads(su_kien_doanh_nghiep(db, "ZZZZ"))["tim_thay"] is False
