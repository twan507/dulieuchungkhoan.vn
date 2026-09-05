"""Registry FRED (spec lát 7 Phụ lục A). Chủ duy nhất của ánh xạ; sự thật đo ở docs/10-sources/global/fred.md."""
from __future__ import annotations

from decimal import Decimal

from etl.registry import Series

SOURCE = "fred"


def _band(a, b):
    return (Decimal(str(a)), Decimal(str(b)))


def _m(key, code, name, unit, freq, band, lag, scale=1):
    return Series(source=SOURCE, external_key=key, domain="macro", code=code, name_vi=name, unit=unit, freq=freq,
                  scale=Decimal(scale), region="us", band=_band(*band), max_lag_days=lag)


def _a(key, code, name, cls, ccy, unit, ptype, region, band, lag):
    return Series(source=SOURCE, external_key=key, domain="asset", code=code, name_vi=name, unit=unit, freq="d",
                  region=region, asset_class=cls, quote_currency=ccy, price_type=ptype, calendar="trading_days",
                  band=_band(*band), max_lag_days=lag)


def build() -> list[Series]:
    return [
        _m("DFF", "us.rate.fedfunds.daily", "Fed funds hiệu lực (ngày)", "%", "d", (-1, 25), 6),
        _m("FEDFUNDS", "us.rate.fedfunds", "Fed funds bình quân tháng", "%", "m", (-1, 25), 75),
        _m("SOFR", "us.rate.sofr", "SOFR", "%", "d", (-1, 25), 6),
        _m("DGS2", "us.yield.2y", "Lợi suất TPCP Mỹ 2 năm", "%", "d", (-1, 25), 6),
        _m("DGS10", "us.yield.10y", "Lợi suất TPCP Mỹ 10 năm", "%", "d", (-1, 25), 6),
        _m("T10Y2Y", "us.yield.spread_10y2y", "Chênh lợi suất 10 năm − 2 năm", "%", "d", (-5, 5), 6),
        _m("T10YIE", "us.breakeven.10y", "Lạm phát hoà vốn 10 năm", "%", "d", (-5, 15), 6),
        _m("CPIAUCSL", "us.cpi", "CPI Mỹ (SA, 1982–84 = 100)", "chỉ số (1982-84=100)", "m", (100, 1000), 75),
        _m("PCEPILFE", "us.pce.core", "PCE lõi (2017 = 100)", "chỉ số (2017=100)", "m", (50, 500), 100),
        _m("UNRATE", "us.unemployment", "Tỷ lệ thất nghiệp Mỹ", "%", "m", (0, 30), 75),
        _m("PAYEMS", "us.payrolls", "Việc làm phi nông nghiệp", "người", "m", (1e8, 3e8), 75, scale=1000),
        _a("DCOILWTICO", "wti", "Giá dầu WTI", "commodity", "USD", "USD/thùng", "spot", "us", (5, 500), 10),
        _a("DTWEXBGS", "dxy.broad", "Chỉ số đô Mỹ broad (Fed, 01/2006 = 100)", "index", "USD", "điểm", "close", "us", (50, 200), 12),
        _a("VIXCLS", "vix", "VIX", "index", "USD", "điểm", "close", "us", (5, 150), 6),
        # DEXCHUS (CNY noon NY) bỏ ở lát 7b — CNY về ECB, một mốc fixing (spec 7b §4.2)
    ]
