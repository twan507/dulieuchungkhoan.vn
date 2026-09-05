"""Fetcher chung cho mọi nguồn HTTP: `get` bơm được (trả (status, text, headers)), `classify` theo nguồn,
retry + backoff, exception vận chuyển đi cùng đường với response xấu (bài học lát 3, e7f80f6).
Từ lát 7b: giãn cách NGẪU NHIÊN đều [1, 5] s trước mỗi lời gọi có lời gọi trước đó trong cùng Fetcher — kể cả
lần thử lại và trang backfill (D5, spec 7b §4.6-III); `rng` bơm được để test cố định.

⚠️ Khi exception, `text` là TÊN LỚP exception, không có `str(e)` — `str(e)` của httpx chứa URL, mà URL FRED chứa
khoá (fred.md Bẫy 7). `label` do nguồn đặt, không được chứa khoá."""
from __future__ import annotations

import contextlib
import random
import time

import httpx

DEFAULT_HEADERS = {"Accept-Encoding": "gzip",
                   "User-Agent": "dulieuchungkhoan.vn/etl (dulieuchungkhoan.official@gmail.com)"}
GAP = (1.0, 5.0)            # giây, phân bố đều — mô phỏng request thường, tránh dồn cục (brief D5)


class FetchError(Exception):
    """Một lời gọi hỏng sau mọi lần thử — series đó CHƯA nạp."""


class BadShape(Exception):
    """Response hợp lệ nhưng không đúng hình dạng/tham số — thử lại vô ích."""


class Fetcher:
    def __init__(self, get, classify, sleep=time.sleep, rng=None, gap=GAP, retries=3, backoff=(2, 4, 8), timeout=30.0):
        self._get, self._classify, self._sleep = get, classify, sleep
        self._rng = rng if rng is not None else random.Random()
        self.gap, self.retries, self.backoff, self.timeout = gap, retries, backoff, timeout
        self.calls = 0
        self.retries_done = 0
        self.last_headers: dict = {}
        self.gaps: list[float] = []

    def _throttle(self) -> None:
        # Không ngủ trước lời gọi ĐẦU TIÊN của lượt; mọi lời gọi sau (kể cả thử lại) cách lời gọi trước một khoảng ngẫu nhiên
        if self.calls:
            g = self._rng.uniform(*self.gap)
            self.gaps.append(g)
            self._sleep(g)

    def fetch_one(self, url: str, label: str):
        http, text = 0, ""
        for attempt in range(self.retries + 1):
            self._throttle()
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
def open_fetcher(classify, get=None, sleep=time.sleep, headers=None, rng=None, **kw):
    if get is not None:                            # test tiêm get giả, không mở kết nối
        yield Fetcher(get, classify, sleep, rng, **kw)
        return
    with httpx.Client(headers={**DEFAULT_HEADERS, **(headers or {})}, follow_redirects=True) as client:  # MỘT client cho trọn lượt
        def get_one(u: str, timeout: float):
            r = client.get(u, timeout=timeout)
            return r.status_code, r.text, dict(r.headers)
        yield Fetcher(get_one, classify, sleep, rng, **kw)
