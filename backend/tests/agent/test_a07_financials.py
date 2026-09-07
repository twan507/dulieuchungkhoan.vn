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


def test_statement_type_la_bi_tu_choi_khong_ra_0_dong_cam(db, kho):
    """statement_type ngoài {IS,BS,CF} (đo kho thật 2026-09-07: 'NO' được DB CHECK cho phép
    nhưng 0 dòng thật, không có nhãn hiển thị trong labels.py) trước sửa lọt qua
    DEFAULT_BY_STATEMENT.get(..., []) thành codes=[] rồi câu SQL luôn ra 0 dòng — model nhận
    hình dạng #3 ("mã đúng, khoảng năm rỗng") dù statement_type mình gõ không hề tồn tại."""
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(bao_cao_tai_chinh(db, "FPT", statement_type="XX"))
    assert out["loi"] is True
    assert out["statement_type_hop_le"] == ["IS", "BS", "CF"]


def test_period_la_bi_tu_choi_khong_am_tham_doi_thanh_quy(db, kho):
    """period chỉ so sánh == 'nam' rồi mặc định coi MỌI giá trị khác là quý (length_report
    1..4) — gõ nhầm 'Nam' (hoa đầu) trước sửa bị âm thầm đọc thành 'quý', ra 0 dòng vì kho
    fixture chỉ có báo cáo NĂM cho FPT, không báo statement_type/period đã gõ sai."""
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(bao_cao_tai_chinh(db, "FPT", period="Nam"))
    assert out["loi"] is True
    assert out["period_hop_le"] == ["nam", "quy"]


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
    đủ để lộ hành vi cắt trần thật. Chèn thêm nhiều năm `isa3` NGAY TRONG TEST này (không đụng
    conftest.py — đúng luật "không sửa file dùng chung") để vượt TRAN_KY, rồi kiểm hàm cắt
    đúng TRAN_KY và báo da_cat=True.

    Dùng chính hằng số TRAN_KY của module (không mã hoá cứng số kỳ) — trần đã nới 8 -> 20
    (chủ dự án chốt 2026-09-07), khoá cứng "15 năm > 8" như bản cũ sẽ không còn vượt trần mới
    và làm test hoá xanh giả (§4.4.4: tiêu chí phải bất biến, không phải số thời điểm).
    """
    from agent.tools.get_financials import TRAN_KY
    nam_them = TRAN_KY + 6  # đủ dư để chắc chắn vượt trần dù trần đổi tiếp sau này
    for i in range(nam_them):
        nam = 2024 - 1 - i  # 2023, 2022, ... — không đụng năm 2024 sẵn có trong kho
        db.execute(sa.text(
            "INSERT INTO market.financial_statement"
            " (issuer_id, year_report, length_report, statement_type, metric_code, value)"
            " VALUES (:i, :y, 5, 'IS', 'isa3', :v)"),
            {"i": kho["issuer:FPT"], "y": nam, "v": nam * 1_000_000_000})
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(bao_cao_tai_chinh(db, "FPT", "IS", 2000, 2024))
    assert nam_them + 1 > TRAN_KY  # +1 vì năm 2024 sẵn có trong kho cũng thuộc IS/isa3
    assert len(out["du_lieu"]) <= TRAN_KY
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


def test_khoang_rong_loc_dung_period_khong_muon_khoang_cua_ky_khac(db, kho):
    """F4 (review CHUẨN lát 10, vòng 3): câu khoang_co_du_lieu cũ chỉ lọc issuer_id +
    statement_type, BỎ QUÊN length_report và metric_code — trong khi câu chính (_SQL_BCTC) lọc
    cả bốn. Fixture chỉ seed FPT báo cáo NĂM (length_report=5, BCTC_FPT_2024 trong conftest),
    không có báo cáo QUÝ nào. Hỏi period='quy' (length_report in [1,2,3,4]) ra 0 dòng — câu
    khoảng cũ (không lọc length_report) sẽ tìm thấy khoảng của báo cáo NĂM (2024..2024) rồi trả
    nhầm cho câu hỏi QUÝ, khiến model tưởng "kho có kỳ quý ở khoảng 2024, chỉ là hỏi sai năm".
    Đúng ra kho không có kỳ quý nào cho FPT/IS ⇒ không được có khoang_co_du_lieu."""
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(bao_cao_tai_chinh(db, "FPT", "IS", 2010, 2030, period="quy"))
    assert out["co_du_lieu"] is True and out["so_dong"] == 0
    assert "khoang_co_du_lieu" not in out
