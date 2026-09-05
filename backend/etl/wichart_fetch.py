"""Tải một key WiChart (spec lát 6 §5.2). Từ lát 7b ruột là `http_fetch.Fetcher` (giãn cách ngẫu nhiên 1–5 s,
retry 3, backoff 2/4/8 — đóng nợ "wichart_fetch chưa chuyển sang http_fetch" của lát 7); file này giữ MẶT NGOÀI
của lát 6 — `url`, `classify`, `Fetcher(get, sleep, clock)`, `fetch_one(key, group)`, `calls`/`retries`,
`FetchError`/`BadShape` — để `wichart_job` và test lát 6 không đổi.

`get` của WiChart trả 2-tuple `(status, text)` (test e37/e41 tiêm vậy) — bọc thành 3-tuple cho fetcher chung.
Đo 2026-09-05: 90 lời gọi liên tiếp không giãn cách sạch; 282 lời gọi/14 phút với giãn cách 1–5 s sạch (A4)."""
from __future__ import annotations

import contextlib
import json
import time

import httpx

from etl.http_fetch import DEFAULT_HEADERS, BadShape, FetchError  # noqa: F401 — re-export cho wichart_job/test lát 6
from etl.http_fetch import Fetcher as _SharedFetcher

BASE = "https://api.wichart.vn/vietnambiz/vi-mo"
TIMEOUT = 30.0


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


def _three(get):
    """(status, text) của WiChart → (status, text, headers) cho fetcher chung."""
    def get3(u: str, timeout: float):
        http, text = get(u, timeout)
        return http, text, {}
    return get3


class Fetcher:
    def __init__(self, get, sleep=time.sleep, clock=None, rng=None):
        # `clock` giữ cho chữ ký lát 6 (test e37 truyền vào), không còn dùng — giãn cách nay ngẫu nhiên, không theo đồng hồ
        self._inner = _SharedFetcher(_three(get), classify, sleep=sleep, rng=rng, timeout=TIMEOUT)

    @property
    def calls(self) -> int:
        return self._inner.calls

    @property
    def retries(self) -> int:
        return self._inner.retries_done

    @property
    def gaps(self) -> list[float]:
        return self._inner.gaps

    def fetch_one(self, key: str, group: str) -> tuple[dict, str]:
        try:
            return self._inner.fetch_one(url(key, group), key)
        except BadShape as e:
            raise BadShape(f"{key}: response không có chart.series") from e


@contextlib.contextmanager
def open_fetcher(get=None, sleep=time.sleep, clock=None, rng=None):
    if get is not None:                            # test tiêm get giả, không mở kết nối
        yield Fetcher(get, sleep, clock, rng)
        return
    with httpx.Client(headers=DEFAULT_HEADERS) as client:  # MỘT client cho trọn lượt
        def get_one(u: str, timeout: float) -> tuple[int, str]:
            r = client.get(u, timeout=timeout)
            return r.status_code, r.text
        yield Fetcher(get_one, sleep, clock, rng)
