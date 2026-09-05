"""/api/v3/klines — mảng theo vị trí, giá chuỗi (crypto.md Bẫy 2). Header weight thật: tự phanh trước 6.000/phút.

Ruling controller (task 6): 418 → `Banned` được bọc MỘT LẦN qua `_guard_418`, áp cho cả `get` do test tiêm lẫn
`get` thật — không bao giờ gán đè thuộc tính riêng (`f._get`) của `Fetcher`."""
from __future__ import annotations

import json
import logging

import httpx

from etl.http_fetch import BadShape, DEFAULT_HEADERS, FetchError, open_fetcher

log = logging.getLogger("etl.binance")
BASE = "https://api.binance.com/api/v3/klines"
DAILY_LIMIT = 40
PAGE = 1000
MIN_INTERVAL = 0.3
WEIGHT_PAUSE = 3000


class Banned(Exception):
    """418: IP bị cấm sau khi tiếp tục gọi qua 429 — dừng cả lượt, không thử lại."""


def url(symbol: str, limit: int, start_time: int | None = None) -> str:
    u = f"{BASE}?symbol={symbol}&interval=1d&limit={limit}&timeZone=0"
    return u + (f"&startTime={start_time}" if start_time is not None else "")


def classify(http: int, text: str):
    if http != 200:
        return "retry", None                       # 429 đi đường backoff 2/4/8
    try:
        d = json.loads(text)
    except ValueError:
        return "retry", None
    if not isinstance(d, list) or (d and not (isinstance(d[0], list) and len(d[0]) == 12)):
        return "bad_shape", None
    return "ok", d


def _guard_418(get):
    """Bọc một `get(url, timeout) -> (status, text, headers)` để 418 nổ thành `Banned` — dùng cho cả get giả
    (test tiêm) lẫn get thật (client httpx), cùng một hành vi."""
    def guarded(u: str, timeout: float):
        st, tx, h = get(u, timeout)
        if st == 418:
            raise Banned(f"418 từ Binance: {tx[:100]}")
        return st, tx, h
    return guarded


def _pause(f, sleep):
    w = f.last_headers.get("x-mbx-used-weight-1m") or f.last_headers.get("X-MBX-USED-WEIGHT-1M")
    if w and int(w) >= WEIGHT_PAUSE:
        log.warning("weight-1m %s ≥ %s — nghỉ 60 s", w, WEIGHT_PAUSE)
        sleep(60)


def _fetch_with(series, get, sleep, backfill):
    docs, texts, failed = {}, {}, []
    with open_fetcher(classify, get=get, sleep=sleep, min_interval=MIN_INTERVAL) as f:
        for s in series:
            sym = s.external_key
            try:
                if backfill:
                    rows, start = [], 0
                    while True:
                        doc, text = f.fetch_one(url(sym, PAGE, start), sym)
                        rows.extend(doc)
                        _pause(f, sleep)
                        if len(doc) < PAGE:
                            break
                        start = doc[-1][0] + 1
                    docs[sym], texts[sym] = rows, text
                else:
                    docs[sym], texts[sym] = f.fetch_one(url(sym, DAILY_LIMIT), sym)
                    _pause(f, sleep)
            except (BadShape, FetchError) as e:
                failed.append(sym)
                log.warning("%s", e)
        return docs, texts, failed, f.calls, f.retries_done


def fetch_all(series, get, sleep, backfill):
    if get is not None:                            # test tiêm get giả
        return _fetch_with(series, _guard_418(get), sleep, backfill)
    with httpx.Client(headers=DEFAULT_HEADERS, follow_redirects=True) as client:   # MỘT client cho trọn lượt
        def real_get(u: str, timeout: float):
            r = client.get(u, timeout=timeout)
            return r.status_code, r.text, dict(r.headers)
        return _fetch_with(series, _guard_418(real_get), sleep, backfill)
