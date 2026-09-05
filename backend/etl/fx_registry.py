"""Registry ECB qua Frankfurter (spec lát 7 Phụ lục B). source='ecb' là danh tính dữ liệu, không phải tên API."""
from __future__ import annotations

from decimal import Decimal

from etl.registry import Series

SOURCE = "ecb"
_ROWS = [("EUR", "fx.usd_eur", "Tỷ giá EUR/USD (fixing ECB 14:15 CET)", "0.5", "2"),
         ("JPY", "fx.usd_jpy", "Tỷ giá JPY/USD (fixing ECB)", "50", "400"),
         ("GBP", "fx.usd_gbp", "Tỷ giá GBP/USD (fixing ECB)", "0.4", "1.5"),
         ("CAD", "fx.usd_cad", "Tỷ giá CAD/USD (fixing ECB)", "0.8", "2.5"),
         ("SEK", "fx.usd_sek", "Tỷ giá SEK/USD (fixing ECB)", "4", "20"),
         ("CHF", "fx.usd_chf", "Tỷ giá CHF/USD (fixing ECB)", "0.5", "2")]


def build() -> list[Series]:
    return [Series(source=SOURCE, external_key=ccy, domain="asset", code=code, name_vi=name, unit=f"{ccy}/1 USD", freq="d",
                   region="eu", asset_class="fx", quote_currency=ccy, price_type="fixing", calendar="trading_days",
                   band=(Decimal(lo), Decimal(hi)), max_lag_days=6) for ccy, code, name, lo, hi in _ROWS]
