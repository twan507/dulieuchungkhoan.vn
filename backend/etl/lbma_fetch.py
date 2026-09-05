"""Hai file JSON trọn lịch sử LBMA (~900 KB mỗi file, không lọc được ở nguồn — commodities.md Bẫy 2)."""
from __future__ import annotations

import json
import logging

from etl.http_fetch import BadShape, FetchError, open_fetcher

log = logging.getLogger("etl.lbma")
BASE = "https://prices.lbma.org.uk/json"
MIN_INTERVAL = 1.0


def url(name: str) -> str:
    return f"{BASE}/{name}.json"


def classify(http: int, text: str):
    if http != 200:
        return "retry", None
    try:
        d = json.loads(text)
    except ValueError:
        return "retry", None
    if not isinstance(d, list) or not d or not all(isinstance(r, dict) and "d" in r and "v" in r for r in d[:3] + d[-3:]):
        return "bad_shape", None
    return "ok", d


def fetch_all(series, get, sleep, backfill):
    docs, texts, failed = {}, {}, []
    with open_fetcher(classify, get=get, sleep=sleep, min_interval=MIN_INTERVAL, timeout=60.0) as f:
        for s in series:
            try:
                docs[s.external_key], texts[s.external_key] = f.fetch_one(url(s.external_key), s.external_key)
            except (BadShape, FetchError) as e:
                failed.append(s.external_key)
                log.warning("%s", e)
        return docs, texts, failed, f.calls, f.retries_done
