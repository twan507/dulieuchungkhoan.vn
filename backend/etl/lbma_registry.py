"""Registry LBMA (spec lát 7 Phụ lục C): chỉ cột USD (v[0]); GBP/EUR loại có chủ đích."""
from __future__ import annotations

from decimal import Decimal

from etl.registry import Series

SOURCE = "lbma"


def build() -> list[Series]:
    rows = [("gold_pm", "gold.lbma", "Vàng LBMA fixing PM (15:00 London)", "100", "20000"),
            ("silver", "silver.lbma", "Bạc LBMA fixing (12:00 London)", "1", "500")]
    return [Series(source=SOURCE, external_key=k, external_sub="0", domain="asset", code=code, name_vi=name, unit="USD/oz",
                   freq="d", region="global", asset_class="commodity", quote_currency="USD", price_type="fixing",
                   calendar="trading_days", band=(Decimal(lo), Decimal(hi)), max_lag_days=6) for k, code, name, lo, hi in rows]
