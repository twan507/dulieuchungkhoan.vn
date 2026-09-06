"""Quy đổi số sang chuỗi người đọc được. Hàm thuần, không chạm DB.

HAI HỌ ĐƠN VỊ, đừng trộn:
  metric_dictionary.unit ∈ {VND, ty_le_thap_phan, lan, VND/CP, co_phieu, so_luong, NULL}
  macro.indicator.unit / asset.asset.unit là VĂN BẢN TỰ DO: %, USD/thùng, điểm, người…
'ty_le_thap_phan' phải NHÂN 100; '%' thì KHÔNG. Đây là chỗ dễ sai 100 lần nhất của lát.
"""
from __future__ import annotations

import datetime as dt
from decimal import Decimal

TY = Decimal(10) ** 9


def _num(value) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def _group(n: Decimal, places: int = 0) -> str:
    """1234567.8 -> '1.234.567,8' (dấu chấm phân nhóm, phẩy thập phân — kiểu Việt)."""
    q = f"{n:,.{places}f}"
    return q.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def _tien(n: Decimal, ky_hieu: str) -> str:
    if abs(n) >= TY:                       # so sánh theo TRỊ TUYỆT ĐỐI, giữ dấu ở kết quả
        return f"{_group(n / TY, 1)} tỷ {ky_hieu}"
    return f"{_group(n, 0)} đ" if ky_hieu == "VND" else f"{_group(n, 0)} {ky_hieu}"


def display_metric(value, unit: str | None) -> str | None:
    n = _num(value)
    if n is None or unit is None:
        return None
    if unit == "VND":
        return _tien(n, "VND")
    if unit == "ty_le_thap_phan":
        return f"{_group(n * 100, 2)}%"
    if unit == "lan":
        return f"{_group(n, 2)} lần"
    if unit == "VND/CP":
        return f"{_group(n, 0)} đ/cp"
    if unit == "co_phieu":
        return f"{_group(n, 0)} cp"
    if unit == "so_luong":
        return f"{_group(n, 0)}"
    return f"{_group(n, 2)} {unit}"


def display_series_value(value, unit: str | None) -> str | None:
    """Đơn vị của macro/asset — văn bản tự do, KHÔNG nhân 100 cho '%'."""
    n = _num(value)
    if n is None:
        return None
    if unit is None:
        return _group(n, 2)
    if unit == "%":
        return f"{_group(n, 2)}%"
    if unit in ("VND", "USD"):
        return _tien(n, unit)
    if n == n.to_integral_value():
        return f"{_group(n, 0)} {unit}"
    return f"{_group(n, 2)} {unit}"


def format_date_vi(d: dt.date | dt.datetime) -> str:
    return d.strftime("%d/%m/%Y")
