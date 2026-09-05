"""Tải một series FRED (spec lát 7 §5.2). Khoá đi trong URL ⇒ MỌI chuỗi ra log/stats đi qua `redact`."""
from __future__ import annotations

import json
import logging
import os

from etl.http_fetch import BadShape, FetchError, open_fetcher

log = logging.getLogger("etl.fred")
BASE = "https://api.stlouisfed.org/fred/series/observations"


def url(series_id: str, key: str) -> str:
    return f"{BASE}?series_id={series_id}&api_key={key}&file_type=json"


def redact(text: str, key: str) -> str:
    return text.replace(key, "<REDACTED>") if key else text


def classify(http: int, text: str):
    """('ok', doc) | ('retry', None) | ('bad_shape', None). 400 = tham số/khoá sai — FRED trả lỗi rõ, thử lại vô ích."""
    if http == 400:
        return "bad_shape", None
    if http != 200:
        return "retry", None
    if text.lstrip().startswith("<"):                       # Bẫy 3: quên file_type=json ⇒ XML kèm 200
        return "bad_shape", None
    try:
        d = json.loads(text)
    except ValueError:
        return "retry", None
    if not isinstance(d, dict) or not isinstance(d.get("observations"), list):
        return "bad_shape", None
    return "ok", d


def fetch_all(series, get, sleep, backfill, intraday=False):
    key = os.environ.get("FRED_API")
    if not key:
        raise RuntimeError("thiếu FRED_API")
    docs, texts, failed = {}, {}, []
    with open_fetcher(classify, get=get, sleep=sleep) as f:
        for s in series:
            try:
                docs[s.external_key], texts[s.external_key] = f.fetch_one(url(s.external_key, key), s.external_key)
            except (BadShape, FetchError) as e:
                failed.append(s.external_key)
                log.warning("%s", redact(str(e), key))
        return docs, texts, failed, f.calls, f.retries_done
