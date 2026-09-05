"""Fetcher chung cho 5 nguồn quốc tế: `get` bơm được (trả (status, text, headers)), `classify` theo nguồn,
retry + backoff, exception vận chuyển đi cùng đường với response xấu (bài học lát 3, e7f80f6).

⚠️ Khi exception, `text` là TÊN LỚP exception, không có `str(e)` — `str(e)` của httpx chứa URL, mà URL FRED chứa
khoá (fred.md Bẫy 7). `label` do nguồn đặt, không được chứa khoá."""
from __future__ import annotations

import contextlib
import time

import httpx

DEFAULT_HEADERS = {"Accept-Encoding": "gzip",
                   "User-Agent": "dulieuchungkhoan.vn/etl (dulieuchungkhoan.official@gmail.com)"}


class FetchError(Exception):
    """Một lời gọi hỏng sau mọi lần thử — series đó CHƯA nạp."""


class BadShape(Exception):
    """Response hợp lệ nhưng không đúng hình dạng/tham số — thử lại vô ích."""


class Fetcher:
    def __init__(self, get, classify, sleep=time.sleep, clock=time.monotonic, min_interval=0.0,
                 retries=3, backoff=(2, 4, 8), timeout=30.0):
        self._get, self._classify, self._sleep, self._clock = get, classify, sleep, clock
        self.min_interval, self.retries, self.backoff, self.timeout = min_interval, retries, backoff, timeout
        self.calls = 0
        self.retries_done = 0
        self.last_headers: dict = {}
        self._last: float | None = None

    def _throttle(self) -> None:
        # Giãn cách MỘT lần mỗi fetch_one — retry đã có backoff lo giãn cách (khuôn wichart_fetch)
        now = self._clock()
        if self._last is not None:
            wait = self.min_interval - (now - self._last)
            if wait > 0:
                self._sleep(wait)
        self._last = self._clock()

    def fetch_one(self, url: str, label: str):
        self._throttle()
        http, text = 0, ""
        for attempt in range(self.retries + 1):
            try:
                self.calls += 1
                http, text, self.last_headers = self._get(url, self.timeout)
            except httpx.HTTPError as e:
                http, text, self.last_headers = 0, f"{type(e).__name__}", {}
            verdict, doc = self._classify(http, text)
            if verdict == "ok":
                return doc, text
            if verdict == "bad_shape":
                raise BadShape(f"{label}: {text[:200]}")
            if attempt == self.retries:
                break
            self._sleep(self.backoff[attempt])
            self.retries_done += 1
        raise FetchError(f"{label} hỏng sau {self.retries + 1} lần (HTTP {http}): {text[:200]}")


@contextlib.contextmanager
def open_fetcher(classify, get=None, sleep=time.sleep, clock=time.monotonic, headers=None, **kw):
    if get is not None:                            # test tiêm get giả, không mở kết nối
        yield Fetcher(get, classify, sleep, clock, **kw)
        return
    with httpx.Client(headers={**DEFAULT_HEADERS, **(headers or {})}, follow_redirects=True) as client:  # MỘT client cho trọn lượt
        def get_one(u: str, timeout: float):
            r = client.get(u, timeout=timeout)
            return r.status_code, r.text, dict(r.headers)
        yield Fetcher(get_one, classify, sleep, clock, **kw)
