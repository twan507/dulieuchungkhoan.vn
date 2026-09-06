"""Seam S4 — chuỗi vĩ mô và giá tài sản.

Expected lấy từ fixture `kho` (backend/tests/agent/conftest.py, seed 2026-09-07), không phải
đo kho dev thật (§4.4.4). BA nguồn, không phải một:
  macro.observation_spliced (cột value_spliced / value_as_published — KHÔNG có cột 'value')
  asset.price_daily  — một giá trị mỗi (asset_id, obs_date, price_type); MỘT asset có thể
                       mang NHIỀU price_type (vàng spot+fixing, dầu futures) — ADR §2.3 cấm
                       trộn hai loại giá vào một chuỗi (bậc nhảy 2%)
  asset.ohlc_daily   — nến, không có cột price_type
Expected: vn.cpi 2026-08-01 = 4.45 (đơn vị '%' — KHÔNG nhân 100, xem conftest CPI_...);
wti 2026-09-05 = 91.22 USD/thùng (fixture GIA_HPG không liên quan, dùng ids["wti"] riêng).
"""
import json

import sqlalchemy as sa

from agent.tools.get_macro_series import chuoi_vi_mo


def test_cpi_thang_8_2026(db, kho):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(chuoi_vi_mo(db, code="vn.cpi", from_date="2026-08-01", to_date="2026-08-31"))
    assert out["du_lieu"][-1]["gia_tri"] == "4,45%"
    assert out["ten"] == "CPI (YoY)"


def test_dau_wti_la_nhanh_asset(db, kho):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(chuoi_vi_mo(db, code="wti", from_date="2026-09-05", to_date="2026-09-05"))
    assert out["du_lieu"][-1]["gia_tri"] == "91,22 USD/thùng"
    assert out["loai_gia"] == "futures"
    assert out["cac_loai_gia_co_san"] == ["futures"]


def test_gia_hang_hoa_nhieu_loai_gia_chi_lay_loai_nhieu_dong_nhat(db, kho):
    """wti trong kho thật có cả futures lẫn (đôi khi) spot cho cùng mã — mô phỏng bằng cách
    chèn thêm MỘT dòng 'spot' cạnh HAI dòng 'futures' sẵn có của fixture (09-04, 09-05).
    Hàm phải chọn đúng loại NHIỀU DÒNG HƠN (futures) và không được gộp dòng spot vào chuỗi
    trả về — trộn giao ngay với tương lai tạo bậc nhảy ~2% (ADR §2.3, CLAUDE.md mục 2.3).
    """
    db.execute(sa.text(
        "INSERT INTO asset.price_daily (asset_id, obs_date, price_type, value)"
        " VALUES (:a, CAST('2026-09-03' AS date), 'spot', 999)"), {"a": kho["wti"]})
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(chuoi_vi_mo(db, code="wti", from_date="2026-09-01", to_date="2026-09-05"))
    assert out["loai_gia"] == "futures"
    assert set(out["cac_loai_gia_co_san"]) == {"futures", "spot"}
    assert out["so_dong"] == 2
    assert all(d["gia_tri"].endswith("USD/thùng") for d in out["du_lieu"])
    assert all("999" not in d["gia_tri"] for d in out["du_lieu"])


def test_btc_nam_o_bang_ohlc(db, kho):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(chuoi_vi_mo(db, code="btc", limit=5))
    assert out["co_du_lieu"] is True and out["so_dong"] > 0
    assert out["du_lieu"][-1]["gia_tri"] == "105 USDT"
    assert "loai_gia" not in out          # ohlc_daily không có cột price_type, đừng bịa ra


def test_keyword_tra_danh_muc_khong_tra_so(db, kho):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(chuoi_vi_mo(db, keyword="dầu"))
    assert out["kieu"] == "danh_muc"
    ma = [d["ma"] for d in out["danh_muc"]]
    assert "wti" in ma
    assert "du_lieu" not in out


def test_ma_khong_ton_tai_thi_goi_y(db, kho):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(chuoi_vi_mo(db, code="vn.cpixxx"))
    assert out["tim_thay"] is False
    assert out["goi_y"]
