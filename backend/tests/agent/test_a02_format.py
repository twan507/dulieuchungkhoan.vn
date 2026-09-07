# backend/tests/agent/test_a02_format.py
"""Seam S2 — quy đổi đơn vị.

Hai họ đơn vị KHÁC NHAU dùng chung ký hiệu '%': metric_dictionary có 'ty_le_thap_phan'
(giá trị thập phân, PHẢI nhân 100) còn macro/asset có '%' (đã là phần trăm, KHÔNG nhân).
Hai ca dưới đây cố tình đặt cạnh nhau — đó là chốt chống lỗi sai 100 lần.

Giá trị lấy từ kho ngày 2026-09-07:
  0.17377625  = ROE (TTM) của HPG, screener_daily 2026-09-04
  4.45        = macro.observation vn.cpi obs_date 2026-08-01
  62848794351367 = financial_statement FPT isa3 2024 (length_report=5)
  -6115961971783 = financial_statement FPT isa9 2024 — chi phí bán hàng, ÂM trong kho
"""
import datetime as dt

from agent.format import display_metric, display_series_value, format_date_vi
from agent.labels import label_for


def test_ty_le_thap_phan_nhan_100():
    assert display_metric(0.17377625, "ty_le_thap_phan") == "17,38%"


def test_phan_tram_cua_macro_khong_nhan_100():
    assert display_series_value(4.45, "%") == "4,45%"


def test_vnd_quy_ty():
    assert display_metric(62848794351367, "VND") == "62.848,8 tỷ VND"


def test_vnd_am_van_quy_ty_va_giu_dau():
    assert display_metric(-6115961971783, "VND") == "-6.116,0 tỷ VND"


def test_vnd_nho_hon_mot_ty_thi_de_dong():
    assert display_metric(21600, "VND") == "21.600 đ"


def test_lan_va_vnd_tren_cp():
    assert display_metric(7.89115654, "lan") == "7,89 lần"
    assert display_metric(2749.91376474, "VND/CP") == "2.750 đ/cp"


def test_unit_null_thi_loai():
    assert display_metric(123, None) is None


def test_gia_tri_none_thi_none():
    assert display_metric(None, "VND") is None


def test_don_vi_la_thi_giu_nguyen_van():
    assert display_series_value(91.22, "USD/thùng") == "91,22 USD/thùng"
    assert display_series_value(1234567, "người") == "1.234.567 người"


def test_ngay_kieu_viet():
    assert format_date_vi(dt.date(2026, 9, 3)) == "03/09/2026"


def test_ngay_none_thi_none():
    """Mục 1 (review vòng 4): published_at NULLABLE có chủ đích (migration 0007) — cột NULL đưa
    thẳng vào đây (vd ngày suy từ published_at khi cột đó rỗng) không được ném AttributeError."""
    assert format_date_vi(None) is None


def test_bang_nhan_tach_duoc_hai_ma_trung_ten():
    """isa20 và isa22 trong nguồn CÙNG tên 'LỢI NHUẬN THUẦN' — bảng nhãn phải tách được."""
    assert label_for("isa22") == "Lợi nhuận sau thuế của cổ đông công ty mẹ"
    assert label_for("isa20") == "Lợi nhuận sau thuế (toàn bộ)"
    assert label_for("isa22") != label_for("isa20")


def test_ma_ngoai_bang_thi_none():
    assert label_for("prf") is None      # tên nói "tỉ đồng" nhưng unit='VND' — cố ý loại
    assert label_for("khong_ton_tai") is None
