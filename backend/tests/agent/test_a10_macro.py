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


def test_from_date_ngon_ngu_tu_nhien_bao_loi_co_cau_truc_khong_nem(db, kho):
    """Đo thật 2026-09-07: from_date='xyz' trước đây lọt xuống CAST(:tu AS date) của nhánh
    macro và làm Postgres ném DataError, thoát khỏi thân hàm."""
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(chuoi_vi_mo(db, code="vn.cpi", from_date="xyz"))
    assert out["loi"] is True
    assert out["dinh_dang_hop_le"] == "YYYY-MM-DD"


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


def test_danh_muc_bao_ro_tong_khop_va_khong_cat_bao_sai(db, kho):
    """N3: danh mục là cửa DUY NHẤT để model tìm mã — trước đây cắt câm ở 40 mục, không trường
    nào báo đã cắt hay còn bao nhiêu. Kho test chỉ có 3 mục (cpi, wti, btc) nên phải KHỚP HẾT,
    không được báo da_cat=True khi thực ra chưa cắt gì."""
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(chuoi_vi_mo(db))
    assert out["kieu"] == "danh_muc"
    assert out["tong_khop"] == len(out["danh_muc"]) == 3
    assert out["da_cat"] is False


def test_khoang_ngay_rong_macro_thi_bao_khoang_that_co(db, kho):
    """N2 (review SPEC lát 10, vòng 3): nhánh macro thiếu khoang_co_du_lieu khi khoảng hỏi
    rỗng — cùng bệnh đã vá ở get_price_series/get_financials/get_corporate_events (spec §4.6
    hình dạng #3). Fixture chỉ seed vn.cpi từ 2026-06-01 tới 2026-08-01."""
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(chuoi_vi_mo(db, code="vn.cpi", from_date="1990-01-01", to_date="1990-12-31"))
    assert out["co_du_lieu"] is True and out["so_dong"] == 0
    assert out["khoang_co_du_lieu"] == {"tu": "2026-06-01", "den": "2026-08-01"}


def test_khoang_ngay_rong_asset_thi_bao_khoang_that_co(db, kho):
    """Cùng nguyên tắc N2 cho nhánh asset — wti chỉ có giá futures ở price_daily (09-04,
    09-05 trong fixture), không có dòng nào ở ohlc_daily. Khoảng báo về phải GỘP CẢ HAI bảng,
    không chỉ bảng vừa tra ra 0 dòng (ohlc_daily), vì asset có dữ liệu ở bảng còn lại."""
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(chuoi_vi_mo(db, code="wti", from_date="1990-01-01", to_date="1990-12-31"))
    assert out["co_du_lieu"] is True and out["so_dong"] == 0
    assert out["khoang_co_du_lieu"] == {"tu": "2026-09-04", "den": "2026-09-05"}


def test_danh_muc_dem_dung_tong_khong_phu_thuoc_tran(db, kho):
    """N3: hàm đếm tổng phải ĐỘC LẬP với LIMIT hiển thị — mô phỏng cắt bằng cách tự hạ trần
    xuống 2 (nội bộ), tổng đếm được vẫn phải là 3, để lộ đúng phần bị cắt."""
    from agent.tools.get_macro_series import _danh_muc, _dem_danh_muc

    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    rows = _danh_muc(db, None, tran=2)
    tong = _dem_danh_muc(db, None)
    assert len(rows) == 2
    assert tong == 3
    assert tong > len(rows)
