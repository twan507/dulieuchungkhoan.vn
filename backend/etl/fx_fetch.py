"""Một lời gọi Frankfurter cho trọn chuỗi 7 cặp (spec lát 7 §5.2). Host mới đo 2026-09-05 (host cũ trả 301)."""
from __future__ import annotations

import json
import logging

from etl.http_fetch import BadShape, FetchError, open_fetcher

log = logging.getLogger("etl.fx")
PAIRS = "EUR,JPY,GBP,CAD,SEK,CHF,CNY"
URL = f"https://api.frankfurter.dev/v1/1999-01-04..?from=USD&to={PAIRS}"


def classify(http: int, text: str):
    if http != 200:
        return "retry", None
    try:
        d = json.loads(text)
    except ValueError:
        return "retry", None
    if not isinstance(d, dict) or d.get("base") != "USD" or not isinstance(d.get("rates"), dict):
        return "bad_shape", None
    return "ok", d


def fetch_all(series, get, sleep, backfill, intraday=False):
    keys = [s.external_key for s in series]
    with open_fetcher(classify, get=get, sleep=sleep, timeout=60.0) as f:
        try:
            doc, text = f.fetch_one(URL, "frankfurter")
        except (BadShape, FetchError) as e:
            log.warning("%s", e)
            return {}, {"all": ""}, keys, f.calls, f.retries_done
        return {k: doc for k in keys}, {"all": text}, [], f.calls, f.retries_done
