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


def test_from_date_hinh_dang_sai_bao_loi_co_cau_truc_khong_nem(db, kho):
    """Đo thật 2026-09-07: from_date='2025-13-45' (đúng hình dạng chuỗi, tháng không có thật)
    trước đây lọt xuống CAST(:tu AS date) và làm Postgres ném DataError."""
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(su_kien_doanh_nghiep(db, "FPT", from_date="2025-13-45"))
    assert out["loi"] is True
    assert out["dinh_dang_hop_le"] == "YYYY-MM-DD"


def test_ma_khong_ton_tai(db, kho):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    assert json.loads(su_kien_doanh_nghiep(db, "ZZZZ"))["tim_thay"] is False


def test_chi_so_khong_co_su_kien_la_hinh_dang_2_khong_phai_rong(db, kho):
    """spec §4.6 hình dạng #2: VNINDEX (index) không thể có sự kiện doanh nghiệp — kho không lưu
    sự kiện cho chỉ số, đó là bản chất loại chứng khoán chứ không phải khoảng ngày rỗng (#3)."""
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(su_kien_doanh_nghiep(db, "VNINDEX"))
    assert out["tim_thay"] is True
    assert out["co_du_lieu"] is False
    assert out["loai"] == "index"
    assert "so_dong" not in out


def test_khoang_ngay_rong_thi_bao_kho_co_tu_ngay_nao(db, kho):
    """Hình dạng #3 phải kèm khoảng có dữ liệu (spec §4.6). Fixture: FPT có sự kiện 2025."""
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(su_kien_doanh_nghiep(db, "FPT", None, "2019-01-01", "2019-12-31"))
    assert out["co_du_lieu"] is True and out["so_dong"] == 0
    assert out["khoang_co_du_lieu"] == {"tu": "2025-03-10", "den": "2025-11-19"}


def test_etf_co_issuer_van_tra_su_kien_that_khong_phai_hinh_dang_2(db, kho):
    """F2 (review CHUẨN lát 10, vòng 2): bản sửa vòng 1 chặn nhầm MỌI loại khác 'stock' bằng
    khong_co_du_lieu — sai với ETF/fund_cert đo trên kho thật (etf 18 mã/104 sự kiện,
    2026-09-07). Sự kiện gắn theo issuer_id: QUYTN (etf) có issuer_id thật trong fixture nên
    phải nhận đúng sự kiện của nó, không được khẳng định 'kho không có sự kiện cho ETF'."""
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(su_kien_doanh_nghiep(db, "QUYTN", "CashDividend"))
    assert out["tim_thay"] is True
    assert out["co_du_lieu"] is True
    assert out["so_dong"] == 1
    assert out["du_lieu"][0]["ngay_gdkhq"] == "2026-03-05"
