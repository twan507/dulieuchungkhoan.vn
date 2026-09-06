"""Seam S4 — chuỗi giá.

Expected lấy từ fixture `kho` (backend/tests/agent/conftest.py, seed 2026-09-07), không phải
đo kho dev thật (§4.4.4 — tiêu chí phải bất biến). Đường lấy expected KHÁC đường của hàm: hàm
join qua security_id, đây đọc trực tiếp hằng số `GIA_HPG` trong conftest — tương đương câu SQL:
  SELECT p.close_raw FROM market.price_daily p JOIN market.security s USING(security_id)
  WHERE s.ticker='HPG' AND p.trading_date='2026-09-03'  ->  21600  (close_raw = close_adj)
Kho không có total_trading/total_trading_value (NULL 100% trên 1.115.219 dòng, đo 2026-09-07)
nên hàm KHÔNG trả khối lượng — test canh đúng điều đó để không ai lặng lẽ thêm cột rỗng.
"""
import json

import sqlalchemy as sa

from agent.tools.get_price_series import gia_theo_ngay


def test_gia_dong_cua_hpg_phien_2026_09_03(db, kho):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(gia_theo_ngay(db, "HPG", "2026-09-03", "2026-09-03"))
    assert out["co_du_lieu"] is True
    assert out["so_dong"] == 1
    phien = out["du_lieu"][0]
    assert phien["dong_cua"] == "21.600 đ"
    assert phien["ngay"] == "2026-09-03"
    assert phien["ngay_hien_thi"] == "03/09/2026"
    assert "khoi_luong" not in phien


def test_chi_so_co_ma_nhung_khong_co_gia(db, kho):
    """VNINDEX: có danh tính (security_type='index'), 0 điểm giá trong kho.

    Phải ra hình dạng #2 ("có mã, không có dữ liệu"), không phải mảng rỗng — trộn hai ca này
    làm model bịa số.
    """
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(gia_theo_ngay(db, "VNINDEX"))
    assert out["tim_thay"] is True
    assert out["co_du_lieu"] is False
    assert out["loai"] == "index"
    assert "chưa có" in out["ly_do"] or "khong co" in out["ly_do"]


def test_ma_khong_ton_tai(db, kho):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(gia_theo_ngay(db, "ZZZZ"))
    assert out["tim_thay"] is False


def test_khoang_ngay_rong_van_bao_khoang_co_du_lieu(db, kho):
    """Kho chỉ có giá HPG ba phiên 09-01..09-03/2026 (GIA_HPG trong conftest.py)."""
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(gia_theo_ngay(db, "HPG", "1999-01-01", "1999-12-31"))
    assert out["co_du_lieu"] is True and out["so_dong"] == 0
    assert out["khoang_co_du_lieu"] == {"tu": "2026-09-01", "den": "2026-09-03"}
