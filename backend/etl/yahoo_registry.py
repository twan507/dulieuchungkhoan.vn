"""Registry Yahoo (spec lát 7 Phụ lục D): 36 chỉ số + DXY ICE → asset.ohlc_daily. quote_currency chép từ meta.currency đo 2026-09-05.
+ 17 cặp FX `.market` (lát 7b)."""
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


# FX (lát 7b, spec Phụ lục F): <CCY>=X = số <CCY> trên 1 USD (đo 2026-09-05: EUR=X 0,8605 vs ECB 0,86044). Asset RIÊNG
# so với fixing ECB `fx.usd_<ccy>` (khác mốc chốt = asset khác); ECB vẫn là mốc chuẩn (fx.md). VND=X là tỷ giá thị
# trường, KHÔNG thay dhtg (yahoo.md §6.1). band = (đo ÷ 10, × 10) trên regularMarketPrice 2026-09-05.
# (symbol, ccy, region, band_lo, band_hi)
_FX_ROWS = [
    ("EUR=X", "EUR", "eu", "0.08", "9"), ("GBP=X", "GBP", "gb", "0.07", "7.5"), ("JPY=X", "JPY", "jp", "15", "1600"),
    ("CAD=X", "CAD", "ca", "0.13", "14"), ("SEK=X", "SEK", "se", "0.9", "96"), ("CHF=X", "CHF", "ch", "0.08", "8.1"),
    ("CNY=X", "CNY", "cn", "0.67", "67"), ("KRW=X", "KRW", "kr", "135", "13500"), ("THB=X", "THB", "th", "3.2", "330"),
    ("SGD=X", "SGD", "sg", "0.12", "13"), ("TWD=X", "TWD", "tw", "3.1", "320"), ("INR=X", "INR", "in", "9.4", "950"),
    ("IDR=X", "IDR", "id", "1760", "176000"), ("MYR=X", "MYR", "my", "0.4", "41"), ("PHP=X", "PHP", "ph", "6.2", "630"),
    ("HKD=X", "HKD", "hk", "0.78", "79"), ("VND=X", "VND", "vn", "2600", "261000"),
]


def build() -> list[Series]:
    idx = [Series(source=SOURCE, external_key=sym, domain="asset", code=code, name_vi=name, unit="điểm", freq="d",
                  region=region, asset_class="index", quote_currency=ccy, price_type=None, calendar="trading_days",
                  band=(Decimal(lo), Decimal(hi)), max_lag_days=14, shape="ohlc")
           for sym, code, name, ccy, region, lo, hi in _ROWS]
    fx = [Series(source=SOURCE, external_key=sym, domain="asset", code=f"fx.usd_{ccy.lower()}.market",
                 name_vi=(f"Tỷ giá {ccy}/USD (thị trường, Yahoo)" if ccy != "VND"
                          else "Tỷ giá USD/VND thị trường (Yahoo, đối chứng — không thay dhtg)"),
                 unit=f"{ccy}/1 USD", freq="d", region=region, asset_class="fx", quote_currency=ccy, price_type=None,
                 calendar="trading_days", band=(Decimal(lo), Decimal(hi)), max_lag_days=6, shape="ohlc")
          for sym, ccy, region, lo, hi in _FX_ROWS]
    return idx + fx
