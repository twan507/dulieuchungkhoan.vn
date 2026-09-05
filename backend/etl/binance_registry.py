"""Registry Binance (spec lát 7 Phụ lục E): PAXG + 10 coin, quote USDT (không viết USD ở bất kỳ tầng nào), 24x7."""
from __future__ import annotations

from decimal import Decimal

from etl.registry import Series

SOURCE = "binance"
_ROWS = [("PAXGUSDT", "paxg", "PAX Gold — vàng token hoá 24/7 (1 token ≈ 1 oz)", "440", "45000"),
         ("BTCUSDT", "btc", "Bitcoin", "7900", "800000"), ("ETHUSDT", "eth", "Ethereum", "240", "25000"),
         ("BNBUSDT", "bnb", "BNB", "72", "7300"), ("ADAUSDT", "ada", "Cardano", "0.02", "2.2"),
         ("XRPUSDT", "xrp", "XRP", "0.13", "14"), ("TRXUSDT", "trx", "TRON", "0.03", "3.4"),
         ("LINKUSDT", "link", "Chainlink", "1.1", "120"), ("DOGEUSDT", "doge", "Dogecoin", "0.008", "0.85"),
         ("SOLUSDT", "sol", "Solana", "10", "1020"), ("AVAXUSDT", "avax", "Avalanche", "0.7", "75")]


def build() -> list[Series]:
    return [Series(source=SOURCE, external_key=sym, domain="asset", code=code, name_vi=name, unit="USDT", freq="d",
                   region="global", asset_class="crypto", quote_currency="USDT", price_type=None, calendar="24x7",
                   band=(Decimal(lo), Decimal(hi)), max_lag_days=2, shape="ohlc") for sym, code, name, lo, hi in _ROWS]
