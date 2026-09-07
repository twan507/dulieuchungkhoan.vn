"""Seam S4 — cây ngành RIÊNG của dự án, tuyệt đối không phơi ICB ra model.

Expected lấy từ fixture `kho` (backend/tests/agent/conftest.py): VCB được gán ngành
NGANHANG qua issuer.industry_id (không qua issuer_industry_override) ⇒ view
market.v_issuer_industry trả source='icb'. Cây ngành ('market.industry') do migration
0003/0011/0013 seed sẵn, KHÔNG do fixture `kho` tạo — đo 2026-09-07 bằng đường khác đường
của hàm (đếm thẳng trên bảng, không qua view):
  SELECT count(*) FROM market.industry WHERE level=1  -> 6
  SELECT count(*) FROM market.industry WHERE level=2  -> 24
  SELECT ind.code, ind.name_vi, par.code, par.name_vi FROM market.industry ind
    JOIN market.industry par ON par.industry_id=ind.parent_id
    WHERE ind.code='NGANHANG'
  -> NGANHANG, 'Ngân hàng và Tín dụng', TAICHINH, 'Dịch vụ Tài chính'
"""
import json

import sqlalchemy as sa

from agent.tools.get_industry_tree import cay_nganh


def test_cay_du_sau_nhom_hai_bon_nganh(db, kho):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(cay_nganh(db))
    assert len(out["nhom"]) == 6
    assert sum(len(n["nganh"]) for n in out["nhom"]) == 24
    # F7 (review CHUẨN lát 10, vòng 2): nhánh trả cây phải cùng khuôn tim_thay/co_du_lieu/
    # so_dong với 7 hàm anh em (_shared.py: phân biệt bằng TRƯỜNG TƯỜNG MINH, không bằng độ
    # dài mảng) — trước sửa, nhánh này trả trần {"nhom": [...]}, không có ba khoá đó.
    assert out["tim_thay"] is True
    assert out["co_du_lieu"] is True
    assert out["so_dong"] == 24


def test_nganh_cua_vcb(db, kho):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(cay_nganh(db, ticker="VCB"))
    assert out["nganh"]["ma"] == "NGANHANG"
    assert out["nganh"]["ten"] == "Ngân hàng và Tín dụng"
    assert out["nhom"]["ten"] == "Dịch vụ Tài chính"
    assert out["nguon_gan"] == "icb"


def test_khong_bao_gio_lo_icb(db, kho):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    assert "icb_code" not in cay_nganh(db, ticker="VCB")
    assert "icb" not in json.loads(cay_nganh(db))["nhom"][0]


def test_ma_khong_ton_tai(db, kho):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    assert json.loads(cay_nganh(db, ticker="ZZZZ"))["tim_thay"] is False


def test_chi_so_chua_gan_nganh_bao_dung_loai_khong_phai_luon_la_etf(db, kho):
    """B1 (review lát 10): nhánh 'chưa gán ngành' từng nói cứng ly_do "quỹ/ETF theo thiết kế
    không có ngành" — sai với VNINDEX (loại 'index', không phải quỹ/ETF; issuer_id=None trong
    fixture nên _SQL_NGANH_CUA_MA không ra dòng nào). CLAUDE.md §3.6 cấm suy loại thật từ một
    quan sát hẹp — ly_do phải lấy đúng `loai` từ resolve_ticker, và response phải kèm trường
    `loai` như các hàm anh em (get_price_series, get_financials)."""
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(cay_nganh(db, ticker="VNINDEX"))
    assert out["tim_thay"] is True
    assert out["co_du_lieu"] is False
    assert out["loai"] == "index"
    assert "etf" not in out["ly_do"].lower() and "quỹ" not in out["ly_do"]


def test_industry_code_khong_ton_tai_thi_khong_khang_dinh_co_that(db, kho):
    """F5 (review CHUẨN lát 10, vòng 3): bản sửa F7 (vòng 2) từng khoá industry_code lạ vào
    {"tim_thay": True, "co_du_lieu": False, "so_dong": 0, "nhom": []} — khẳng định một mã
    ngành BỊA là có thật (tim_thay: true nghĩa là "mã có tồn tại"), và không có ly_do/goi_y
    nào để model tự sửa. Đây là test cũ đã khoá chết hình dạng sai đó thành hợp đồng — sửa lại
    để canh đúng hình dạng #1 (không tìm thấy), cùng khuôn với ticker bịa."""
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(cay_nganh(db, industry_code="KHONGCO"))
    assert out["tim_thay"] is False
    assert out["ma_da_tra"] == "KHONGCO"
    assert out["goi_y"] == []
