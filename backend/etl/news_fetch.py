"""I/O của pipeline tin: một Fetcher chung cho trọn lượt (giãn cách ngẫu nhiên 1–5 s — lát 7b), `get` thật trả text đã
decode theo luật null byte (README §6.1 — không tin charset khai), classify chung: 404 là mã chết (không thử lại),
200 là có (hình dạng kiểm ở parse/extract), còn lại thử lại."""
from __future__ import annotations

import contextlib
import time

import httpx

from etl.http_fetch import BadShape, DEFAULT_HEADERS, FetchError, Fetcher  # noqa: F401 — re-export cho news_job
from etl.news_parse import decode

ARTICLE_MIN_BYTES = 5000          # dưới đó là trang lỗi/soft-404 (đo 2026-09-05: bài bị gỡ trả 200 với 3 KB)
HEADERS = {"User-Agent": "Mozilla/5.0 (dulieuchungkhoan.vn etl; dulieuchungkhoan.official@gmail.com)", "Accept-Encoding": "gzip"}


def classify(http: int, text: str):
    if http == 404:
        return "bad_shape", None
    if http == 200:
        return "ok", text
    return "retry", None


@contextlib.contextmanager
def open_news_fetcher(get=None, sleep=time.sleep, rng=None):
    if get is not None:
        yield Fetcher(get, classify, sleep=sleep, rng=rng)
        return
    with httpx.Client(headers={**DEFAULT_HEADERS, **HEADERS}, follow_redirects=True) as client:
        def get_one(u: str, timeout: float):
            r = client.get(u, timeout=timeout)
            return r.status_code, decode(r.content), dict(r.headers)
        yield Fetcher(get_one, classify, sleep=sleep, rng=rng)
