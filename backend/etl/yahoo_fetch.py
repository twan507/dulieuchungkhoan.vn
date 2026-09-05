"""v8/finance/chart, gọi thẳng REST (không yfinance — yahoo.md §6.5). Đo 2026-09-05: host query1, cửa sổ 400 ngày."""
from __future__ import annotations

import json
import logging
import time

from etl.http_fetch import BadShape, FetchError, open_fetcher

log = logging.getLogger("etl.yahoo")
HOST = "https://query1.finance.yahoo.com/v8/finance/chart"
HEADERS = {"User-Agent": "Mozilla/5.0 (dulieuchungkhoan.vn etl; dulieuchungkhoan.official@gmail.com)"}
DAILY_WINDOW_DAYS = 400          # 40 ngày trả 1 nến ở ^SET.BK/PSEI.PS (measure-yahoo2)
BACKFILL_PERIOD1 = -2208988800   # 1900-01-01: period1=0 cắt câm lịch sử ở 1970 (yahoo.md Bẫy 1)
MIN_INTERVAL = 1.1


def url(symbol: str, period1: int, period2: int) -> str:
    return f"{HOST}/{symbol}?period1={period1}&period2={period2}&interval=1d"


def classify(http: int, text: str):
    if http != 200:
        return "retry", None                                   # kể cả 404 — thử lại rồi mới coi là hỏng (Luật 3)
    try:
        d = json.loads(text)
    except ValueError:
        return "retry", None
    chart = d.get("chart") if isinstance(d, dict) else None
    if not isinstance(chart, dict) or chart.get("error") or not isinstance(chart.get("result"), list) or not chart["result"]:
        return "bad_shape", None
    if not isinstance(chart["result"][0], dict) or "meta" not in chart["result"][0]:
        return "bad_shape", None
    return "ok", d


def fetch_all(series, get, sleep, backfill):
    period2 = int(time.time())
    period1 = BACKFILL_PERIOD1 if backfill else period2 - DAILY_WINDOW_DAYS * 86400
    docs, texts, failed = {}, {}, []
    with open_fetcher(classify, get=get, sleep=sleep, headers=HEADERS, min_interval=MIN_INTERVAL) as f:
        for s in series:
            try:
                docs[s.external_key], texts[s.external_key] = f.fetch_one(url(s.external_key, period1, period2), s.external_key)
            except (BadShape, FetchError) as e:
                failed.append(s.external_key)
                log.warning("%s", e)
        return docs, texts, failed, f.calls, f.retries_done
