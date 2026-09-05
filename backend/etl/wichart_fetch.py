"""Tải một key WiChart (spec §5.2). I/O thuần; `get` bơm được để test không mở kết nối.

Đo 2026-09-05: 90 lời gọi liên tiếp không giãn cách sạch — MIN_INTERVAL chỉ để lịch sự.
"""
from __future__ import annotations

import contextlib
import json
import time

import httpx

BASE = "https://api.wichart.vn/vietnambiz/vi-mo"
TIMEOUT = 30.0
RETRIES = 3
BACKOFF = (2, 4, 8)
MIN_INTERVAL = 0.2
HEADERS = {"Accept-Encoding": "gzip",
           "User-Agent": "dulieuchungkhoan.vn/etl (dulieuchungkhoan.official@gmail.com)"}


def url(key: str, group: str) -> str:
    return f"{BASE}?key=hang_hoa&name={key}" if group == "hang_hoa" else f"{BASE}?name={key}"


def classify(http: int, text: str) -> tuple[str, dict | None]:
    """('ok', doc) | ('retry', None) | ('bad_shape', None)."""
    if http != 200:
        return "retry", None
    try:
        d = json.loads(text)
    except ValueError:
        return "retry", None
    chart = d.get("chart") if isinstance(d, dict) else None
    series = chart.get("series") if isinstance(chart, dict) else None
    if not isinstance(series, list):
        return "bad_shape", None
    return "ok", d


class FetchError(Exception):
    """Một key hỏng sau mọi lần thử — key đó CHƯA nạp, không ghi gì."""


class BadShape(Exception):
    """Response hợp lệ nhưng không có chart.series — nguồn đổi hình dạng, thử lại vô ích."""


class Fetcher:
    def __init__(self, get, sleep=time.sleep, clock=time.monotonic):
        self._get, self._sleep, self._clock = get, sleep, clock
        self.calls = 0
        self.retries = 0
        self._last: float | None = None

    def _throttle(self) -> None:
        # Chỉ giãn cách MỘT lần mỗi fetch_one (không phải mỗi lần thử lại) —
        # retry đã có BACKOFF lo giãn cách rồi, giãn thêm ở đây là thừa.
        now = self._clock()
        if self._last is not None:
            wait = MIN_INTERVAL - (now - self._last)
            if wait > 0:
                self._sleep(wait)
        self._last = self._clock()

    def fetch_one(self, key: str, group: str) -> tuple[dict, str]:
        u = url(key, group)
        self._throttle()
        http, text = 0, ""
        for attempt in range(RETRIES + 1):
            try:
                self.calls += 1
                http, text = self._get(u, TIMEOUT)
            except httpx.HTTPError as e:
                # Timeout/đứt kết nối đi CÙNG đường với response xấu (bài học lát 3, e7f80f6)
                http, text = 0, f"{type(e).__name__}: {e}"
            verdict, doc = classify(http, text)
            if verdict == "ok":
                return doc, text
            if verdict == "bad_shape":
                raise BadShape(f"{key}: response không có chart.series")
            if attempt == RETRIES:
                break
            self._sleep(BACKOFF[attempt])
            self.retries += 1
        raise FetchError(f"{key} hỏng sau {RETRIES + 1} lần (HTTP {http}): {text[:200]}")


@contextlib.contextmanager
def open_fetcher(get=None, sleep=time.sleep, clock=time.monotonic):
    if get is not None:                            # test tiêm get giả, không mở kết nối
        yield Fetcher(get, sleep, clock)
        return
    with httpx.Client(headers=HEADERS) as client:  # MỘT client cho trọn lượt
        def get_one(u: str, timeout: float) -> tuple[int, str]:
            r = client.get(u, timeout=timeout)
            return r.status_code, r.text
        yield Fetcher(get_one, sleep, clock)
