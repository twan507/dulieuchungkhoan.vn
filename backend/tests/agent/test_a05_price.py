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

import agent.tools.get_price_series as get_price_series_mod
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


def test_khong_du_400_phien_thi_khong_bao_da_cat(db, kho):
    """N5/G1 chiều ngược: HPG chỉ có 3 phiên trong fixture — không được báo da_cat=True khi
    thực tế không phiên nào bị cắt (cùng bẫy N2 đã sửa ở compare_peers/screen_stocks)."""
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(gia_theo_ngay(db, "HPG"))
    assert out["so_dong"] == 3
    assert out["da_cat"] is False
    assert out["tong_khop"] == 3


def test_vuot_tran_phien_bao_da_cat_va_giu_phien_gan_nhat(db, kho, monkeypatch):
    """N5/G1 (review CHUẨN lát 10, vòng 2): trước sửa, hàm cắt câm ở TRAN_PHIEN=400 (đo kho
    thật: BT6 có 5.764 phiên, tool trả 400 không cờ nào báo, 356 mã đang niêm yết >400 phiên).
    Hạ TRAN_PHIEN xuống 2 để mô phỏng đúng tình huống 'kho có nhiều hơn giới hạn' mà không phải
    seed 400+ dòng giá — HPG có 3 phiên (GIA_HPG: 09-01, 09-02, 09-03), giữ 2 phiên GẦN NHẤT
    (09-02, 09-03), báo da_cat=True kèm tong_khop=3 và ghi_chú nói rõ 'gần nhất', không phải
    2 phiên đầu khoảng."""
    monkeypatch.setattr(get_price_series_mod, "TRAN_PHIEN", 2)
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(gia_theo_ngay(db, "HPG"))
    assert out["so_dong"] == 2
    assert out["da_cat"] is True
    assert out["tong_khop"] == 3
    assert [p["ngay"] for p in out["du_lieu"]] == ["2026-09-02", "2026-09-03"]
    assert "GẦN NHẤT" in out["ghi_chu"]
