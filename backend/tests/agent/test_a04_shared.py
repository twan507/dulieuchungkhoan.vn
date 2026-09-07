"""Seam — bốn khuôn trạng thái dữ liệu, phép tra mã, và cửa đọc tri thức L2.

Phân biệt "không tìm thấy mã" với "có mã nhưng kho không có loại dữ liệu này" là bắt buộc:
VN-Index có danh tính trong market.security nhưng KHÔNG có một điểm giá nào (đo 2026-09-07,
kiểm cả price_daily, index_stat_daily, asset.*, macro.*). Trộn hai ca này lại là mời model bịa.
"""
import json

import sqlalchemy as sa

from agent.tools._shared import cap_limit, resolve_ticker, to_json
from agent.tools.load_knowledge_reference import doc_tri_thuc


def test_to_json_giu_dau_tieng_viet():
    assert to_json({"ten": "Ngân hàng"}) == '{"ten": "Ngân hàng"}'


def test_cap_limit_tra_gioi_han_thuc_dung():
    """N2: cap_limit không còn trả cờ da_cat — chạy TRƯỚC truy vấn nên không biết kết quả thật
    có bị cắt hay không (xin 500 dòng trên bảng có 3 dòng thì hạ về trần chứ không cắt gì cả).
    Cờ da_cat nay do bên gọi tự tính từ SỐ DÒNG THẬT trả về, xem test_a08/a09/a10."""
    assert cap_limit(None, 20, 50) == 20
    assert cap_limit(10, 20, 50) == 10
    assert cap_limit(500, 20, 50) == 50


def test_resolve_ticker_ma_that(db, kho):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    r = resolve_ticker(db, "hpg")                 # chữ thường — phải chuẩn hoá
    assert r["tim_thay"] is True
    assert r["ticker"] == "HPG"
    assert r["loai"] == "stock"
    assert r["trang_thai"] == "listed"
    assert isinstance(r["issuer_id"], int)


def test_resolve_ticker_chi_so_van_tim_thay(db, kho):
    """Chỉ số có danh tính nhưng không có giá — resolve phải nói tìm thấy, loại 'index'."""
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    ma = db.execute(sa.text(
        "SELECT ticker FROM market.security WHERE security_type='index' ORDER BY ticker LIMIT 1")).scalar()
    r = resolve_ticker(db, ma)
    assert r["tim_thay"] is True
    assert r["loai"] == "index"


def test_resolve_ticker_ma_bia_thi_co_goi_y(db, kho):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    r = resolve_ticker(db, "HPGX")
    assert r["tim_thay"] is False
    assert "HPG" in r["goi_y"]                    # trigram trên ticker


def test_doc_tri_thuc_tra_chuoi_json_co_noi_dung():
    out = json.loads(doc_tri_thuc("valuation"))
    assert out["chu_de"] == "valuation"
    assert "FCFF" in out["noi_dung"]


def test_doc_tri_thuc_chu_de_la_thi_bao_loi_kem_danh_sach():
    """Chủ đề lạ trả LỖI CÓ CẤU TRÚC, không ném — model tự sửa mà không phá vòng chat."""
    out = json.loads(doc_tri_thuc("../../../etc/passwd"))
    assert out["loi"] is True
    assert "valuation" in out["chu_de_hop_le"]
