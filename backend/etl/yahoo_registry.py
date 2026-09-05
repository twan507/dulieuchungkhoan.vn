"""Registry Yahoo (spec lát 7 Phụ lục D): 36 chỉ số + DXY ICE → asset.ohlc_daily. quote_currency chép từ meta.currency đo 2026-09-05."""
from __future__ import annotations

from decimal import Decimal

from etl.registry import Series

SOURCE = "yahoo"
# (symbol, code, name_vi, ccy, region, band_lo, band_hi)
_ROWS = [
    ("^GSPC", "idx.sp500", "S&P 500", "USD", "us", 700, 80000),
    ("^IXIC", "idx.nasdaq", "NASDAQ Composite", "USD", "us", 2500, 270000),
    ("^DJI", "idx.dow", "Dow Jones Industrial", "USD", "us", 5000, 540000),
    ("^RUT", "idx.russell2000", "Russell 2000", "USD", "us", 290, 30000),
    ("^GSPTSE", "idx.tsx", "S&P/TSX Composite", "CAD", "ca", 3600, 370000),
    ("^MXX", "idx.ipc", "IPC Mexico", "MXN", "mx", 6400, 650000),
    ("^BVSP", "idx.bovespa", "Bovespa", "BRL", "br", 18000, 1900000),
    ("^MERV", "idx.merval", "MERVAL", "ARS", "ar", 300000, 31000000),
    ("^FTSE", "idx.ftse100", "FTSE 100", "GBP", "gb", 1000, 110000),
    ("^GDAXI", "idx.dax", "DAX", "EUR", "de", 2600, 270000),
    ("^FCHI", "idx.cac40", "CAC 40", "EUR", "fr", 800, 83000),
    ("^SSMI", "idx.smi", "SMI", "CHF", "ch", 1400, 150000),
    ("^BFX", "idx.bel20", "BEL 20", "EUR", "be", 580, 59000),
    ("^AEX", "idx.aex", "AEX", "EUR", "nl", 110, 12000),
    ("^IBEX", "idx.ibex35", "IBEX 35", "EUR", "es", 2000, 210000),
    ("FTSEMIB.MI", "idx.ftsemib", "FTSE MIB", "EUR", "it", 5200, 530000),
    ("^N100", "idx.euronext100", "Euronext 100", "EUR", "eu", 190, 20000),
    ("^STOXX50E", "idx.stoxx50", "EURO STOXX 50", "EUR", "eu", 640, 64000),
    ("^OMX", "idx.omx30", "OMX Stockholm 30", "SEK", "se", 330, 33000),
    ("^TA125.TA", "idx.ta125", "TA-125", "ILS", "il", 420, 42000),
    ("^N225", "idx.nikkei225", "Nikkei 225", "JPY", "jp", 6500, 660000),
    ("^HSI", "idx.hsi", "Hang Seng", "HKD", "hk", 2500, 260000),
    ("^HSCE", "idx.hscei", "Hang Seng China Enterprises", "HKD", "hk", 850, 86000),
    ("000001.SS", "idx.shcomp", "Thượng Hải Composite", "CNY", "cn", 390, 40000),
    ("399001.SZ", "idx.szcomp", "Thâm Quyến Component", "CNY", "cn", 1350, 140000),
    ("^TWII", "idx.taiex", "TAIEX", "TWD", "tw", 4600, 470000),
    ("^KS11", "idx.kospi", "KOSPI", "KRW", "kr", 660, 67000),
    ("^STI", "idx.sti", "Straits Times", "SGD", "sg", 580, 59000),
    ("^KLSE", "idx.klci", "FTSE Bursa Malaysia KLCI", "MYR", "my", 170, 18000),
    ("^JKSE", "idx.jkse", "Jakarta Composite", "IDR", "id", 660, 67000),
    ("^SET.BK", "idx.set", "SET", "THB", "th", 160, 16000),
    ("PSEI.PS", "idx.psei", "PSEi", "PHP", "ph", 600, 61000),
    ("^BSESN", "idx.sensex", "BSE SENSEX", "INR", "in", 7600, 770000),
    ("^NSEI", "idx.nifty50", "NIFTY 50", "INR", "in", 2300, 240000),
    ("^AXJO", "idx.asx200", "S&P/ASX 200", "AUD", "au", 900, 91000),
    ("^NZ50", "idx.nzx50", "S&P/NZX 50", "NZD", "nz", 1400, 140000),
    ("DX-Y.NYB", "dxy.ice", "Chỉ số đô Mỹ DXY (ICE)", "USD", "us", 10, 1000),
]


def build() -> list[Series]:
    return [Series(source=SOURCE, external_key=sym, domain="asset", code=code, name_vi=name, unit="điểm", freq="d",
                   region=region, asset_class="index", quote_currency=ccy, price_type=None, calendar="trading_days",
                   band=(Decimal(lo), Decimal(hi)), max_lag_days=14, shape="ohlc")
            for sym, code, name, ccy, region, lo, hi in _ROWS]
