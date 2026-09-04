"""Tải ba báo cáo tài chính và danh sách PDF theo organCode, tuần tự, có giãn cách (spec §5.2). I/O thuần.

Đo 2026-09-04 (khảo sát BCTC §6): `status` = "Success" 21/21, tài liệu 2026-08-10 đo 0 — cùng
endpoint ⇒ hợp lệ là status ∈ {0, "Success"} (quy ước §6.1). Payload tới 408 KB (VNM) ⇒ timeout
30 s cho mọi kind. `items: []` ở báo cáo số liệu KHÔNG phải sai hình dạng: coi là báo cáo rỗng,
normalize/apply xử lý (spec §5.4 bước 2).
"""
from __future__ import annotations

import contextlib
import json
import time
from dataclasses import dataclass

import httpx

FUND = "https://wlgw-fundamental.fiintrade.vn"
FIIN_ORIGIN = "https://fiinapp.bvsc.com.vn"       # bắt buộc cho *.fiintrade.vn (00-conventions §2)

KINDS = ("bs", "is", "cf", "reports")
ENDPOINT = {"bs": "GetBalanceSheet", "is": "GetIncomeStatement",
            "cf": "GetCashFlow", "reports": "GetFinancialReports"}
TIMEOUT = 30.0
RETRIES = 3
BACKOFF = (2, 4, 8)
MIN_INTERVAL = 0.5                                 # trần 2 request/giây (market-data-store §4.2)


def url(kind: str, organ_code: str) -> str:
    if kind not in ENDPOINT:
        raise ValueError(f"kind lạ: {kind!r}")
    return f"{FUND}/FinancialStatement/{ENDPOINT[kind]}?OrganCode={organ_code}&language=vi"


def classify(kind: str, http: int, text: str) -> tuple[str, dict | None]:
    """('ok', item) | ('retry', None) | ('bad_shape', None)."""
    if http != 200:
        return "retry", None
    try:
        d = json.loads(text)
    except ValueError:
        return "retry", None
    if not isinstance(d, dict) or d.get("status") not in (0, "Success"):
        return "retry", None                       # gồm "Failed" — lỗi tạm thời của nguồn (quy ước §10.5)
    items = d.get("items")
    if not isinstance(items, list):
        return "bad_shape", None
    if kind == "reports":
        if not all(isinstance(i, dict) for i in items):
            return "bad_shape", None
        return "ok", {"items": items}
    if not items:
        return "ok", {"quarterly": [], "yearly": []}
    item = items[0]
    if not isinstance(item, dict) or not isinstance(item.get("quarterly"), list) \
            or not isinstance(item.get("yearly"), list):
        return "bad_shape", None
    return "ok", item


@dataclass(frozen=True)
class Target:
    kind: str
    issuer_id: int
    organ_code: str
    ticker: str
    found_by: str                                  # 'event' | 'floor'


class FetchError(Exception):
    """Một mã/kind hỏng sau mọi lần thử — để nó CHƯA KIỂM, không ghi gì."""


class BadShape(Exception):
    """Response hợp lệ nhưng sai hình dạng — nguồn đổi, thử lại vô ích."""


class Fetcher:
    def __init__(self, get, sleep=time.sleep, clock=time.monotonic):
        self._get, self._sleep, self._clock = get, sleep, clock
        self.calls = 0
        self.retries = 0
        self._last: float | None = None

    def _request(self, u: str) -> tuple[int, str]:
        if self._last is not None:
            wait = MIN_INTERVAL - (self._clock() - self._last)
            if wait > 0:
                self._sleep(wait)
        self._last = self._clock()
        self.calls += 1
        return self._get(u, TIMEOUT)

    def fetch_one(self, t: Target) -> tuple[dict, str]:
        u = url(t.kind, t.organ_code)
        http, text = 0, ""
        for attempt in range(RETRIES + 1):
            try:
                http, text = self._request(u)
            except httpx.HTTPError as e:
                # Timeout/đứt kết nối đi CÙNG đường với response xấu (bài học lát 3, e7f80f6)
                http, text = 0, f"{type(e).__name__}: {e}"
            verdict, item = classify(t.kind, http, text)
            if verdict == "ok":
                return item, text
            if verdict == "bad_shape":
                raise BadShape(f"{t.organ_code}/{t.kind}: sai hình dạng response")
            if attempt == RETRIES:
                break
            self._sleep(BACKOFF[attempt])
            self.retries += 1
        raise FetchError(f"{t.organ_code}/{t.kind} hỏng sau {RETRIES + 1} lần"
                         f" (HTTP {http}): {text[:200]}")


@contextlib.contextmanager
def open_fetcher(get=None, sleep=time.sleep, clock=time.monotonic):
    if get is not None:                            # test tiêm get giả, không mở kết nối
        yield Fetcher(get, sleep, clock)
        return
    with httpx.Client(headers={"Origin": FIIN_ORIGIN}) as client:
        def get_one(u: str, timeout: float) -> tuple[int, str]:
            r = client.get(u, timeout=timeout)
            return r.status_code, r.text
        yield Fetcher(get_one, sleep, clock)
