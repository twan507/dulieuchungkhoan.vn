"""Seam S4 — báo cáo tài chính dạng dài, bảng 27.281.962 dòng.

Expected đo 2026-09-07, cùng đường (bảng này là nguồn duy nhất) ⇒ CHỐT HỒI QUY, không chứng
minh tính đúng. Giá trị lấy từ fixture `kho` (backend/tests/agent/conftest.py, hằng số
BCTC_FPT_2024), không phải đo kho dev thật (§4.4.4 — tiêu chí phải bất biến):
  FPT 2024 length_report=5: isa3 = 62848794351367 ; isa22 = 7856767812178 ; isa20 = 9427422530444
Ba mã trên có ý nghĩa khác nhau nhưng isa20 và isa22 mang CÙNG name_vi trong nguồn — bảng
nhãn đóng của dự án (agent/labels.py) là chỗ tách chúng ra.
"""
import json

import sqlalchemy as sa

from agent.tools.get_financials import bao_cao_tai_chinh


def test_doanh_thu_va_loi_nhuan_fpt_2024(db, kho):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(bao_cao_tai_chinh(db, "FPT", "IS", 2024, 2024))
    ky = out["du_lieu"][0]
    assert ky["nam"] == 2024
    chi_tieu = {c["ten"]: c["gia_tri"] for c in ky["chi_tieu"]}
    assert chi_tieu["Doanh thu thuần"] == "62.848,8 tỷ VND"
    assert chi_tieu["Lợi nhuận sau thuế của cổ đông công ty mẹ"] == "7.856,8 tỷ VND"
    assert chi_tieu["Lợi nhuận sau thuế (toàn bộ)"] == "9.427,4 tỷ VND"


def test_chi_phi_am_van_dung_dinh_dang(db, kho):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(bao_cao_tai_chinh(db, "FPT", "IS", 2024, 2024))
    chi_tieu = {c["ten"]: c["gia_tri"] for c in out["du_lieu"][0]["chi_tieu"]}
    assert chi_tieu["Chi phí bán hàng"].startswith("-")


def test_khong_bao_gio_lo_ma_tho(db, kho):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    raw = bao_cao_tai_chinh(db, "FPT", "BS", 2024, 2024)
    for ma in ("isa3", "bsa53", "isa22"):
        assert ma not in raw


def test_ma_ngoai_bang_nhan_bi_tu_choi(db, kho):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(bao_cao_tai_chinh(db, "FPT", "IS", 2024, 2024, metric_codes=["prf"]))
    assert out["loi"] is True
    assert "isa3" in out["ma_hop_le"]


def test_chi_so_khong_co_bctc_la_hinh_dang_2_khong_phai_rong(db, kho):
    """spec §4.6 hình dạng #2: VNINDEX (index, không có issuer) hỏi BCTC phải trả
    co_du_lieu=False + loai, KHÔNG được lẫn với hình dạng #3 (mã đúng, khoảng ngày rỗng) —
    trước sửa, resolve_ticker() trả tim_thay=True cho VNINDEX rồi query BCTC thẳng ra 0 dòng,
    tức 'rong()' (so_dong=0, co_du_lieu=True), y hệt một mã cổ phiếu chưa nộp báo cáo năm đó."""
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(bao_cao_tai_chinh(db, "VNINDEX", "IS"))
    assert out["tim_thay"] is True
    assert out["co_du_lieu"] is False
    assert out["loai"] == "index"
    assert "so_dong" not in out


def test_tran_tam_nam(db, kho):
    """Kho fixture chỉ seed ĐÚNG 1 năm (2024) cho FPT (BCTC_FPT_2024 trong conftest.py) — không
    đủ để lộ hành vi cắt trần thật (trần 8 kỳ, theo Ràng buộc toàn cục của plan). Chèn thêm 14
    năm `isa3` NGAY TRONG TEST này (không đụng conftest.py — đúng luật "không sửa file dùng
    chung") để có 15 năm > TRAN_KY=8, rồi kiểm hàm cắt đúng 8 và báo da_cat=True.
    """
    for nam in range(2010, 2024):  # 2010..2023 — 14 năm, cộng năm 2024 sẵn có trong kho = 15
        db.execute(sa.text(
            "INSERT INTO market.financial_statement"
            " (issuer_id, year_report, length_report, statement_type, metric_code, value)"
            " VALUES (:i, :y, 5, 'IS', 'isa3', :v)"),
            {"i": kho["issuer:FPT"], "y": nam, "v": nam * 1_000_000_000})
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(bao_cao_tai_chinh(db, "FPT", "IS", 2000, 2024))
    assert len(out["du_lieu"]) <= 8
    assert out["da_cat"] is True


def test_khoang_nam_rong_thi_bao_kho_co_nhung_nam_nao(db, kho):
    """Hình dạng #3 phải kèm khoảng có dữ liệu (spec §4.6), như get_price_series đã làm.

    Không có nó, model hỏi FPT năm 2020 thấy 0 dòng rất dễ kết luận "doanh nghiệp chưa tồn
    tại" thay vì "kho chưa có năm đó". Fixture chỉ seed năm 2024 cho FPT.
    """
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(bao_cao_tai_chinh(db, "FPT", "IS", 2010, 2012))
    assert out["co_du_lieu"] is True and out["so_dong"] == 0
    assert out["khoang_co_du_lieu"] == {"tu_nam": 2024, "den_nam": 2024}
