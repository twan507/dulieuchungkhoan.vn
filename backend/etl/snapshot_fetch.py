"""Tải bốn endpoint họ Snapshot theo mã, tuần tự, có giãn cách (spec §5.2). I/O thuần.

Ba điều đo 2026-09-04 quyết định hình dạng module (measurements.md):
- `status` trả **0** ở `GetSnapshot` (ngân hàng) và **"Success"** ở `GetSnapshotNoneBank` —
  cùng một họ, cùng một lượt gọi ⇒ hợp lệ là status ∈ {0, "Success"} (quy ước §6.1).
- `status: "Failed"` của `GetValuation` là timeout Redis PHÍA NGUỒN (quy ước §10.5) ⇒ THỬ LẠI.
  Đọc `items: null` thành "mã này rỗng" là ghi kết luận sai rồi đánh dấu đã kiểm.
- Lượt hỏng tốn 12,3 s ⇒ timeout của `valuation` phải rộng hơn hẳn ba kind còn lại.
"""
from __future__ import annotations

import contextlib
import json
import time
from dataclasses import dataclass

import httpx

FUND = "https://wlgw-fundamental.fiintrade.vn"
TOOLS = "https://wlgw-tools.fiintrade.vn"
FIIN_ORIGIN = "https://fiinapp.bvsc.com.vn"       # bắt buộc cho *.fiintrade.vn (00-conventions §2)

KINDS = ("snapshot", "valuation", "ownership", "dividend")
ROOT_KEY = {"snapshot": "summary", "ownership": "overviewChartData",
            "dividend": "organCode", "valuation": "valuationStock"}
TIMEOUT = {"snapshot": 15.0, "ownership": 15.0, "dividend": 15.0, "valuation": 30.0}
RETRIES = 3
BACKOFF = (2, 4, 8)
MIN_INTERVAL = 0.5                                 # trần 2 request/giây (market-data-store §4.2)


def url(kind: str, organ_code: str, ticker: str, com_type: str | None) -> str:
    if kind == "snapshot":
        ep = "GetSnapshot" if com_type == "NH" else "GetSnapshotNoneBank"
        return f"{FUND}/Snapshot/{ep}?OrganCode={organ_code}&language=vi"
    if kind == "ownership":
        return f"{FUND}/Ownership/GetOwnership?OrganCode={organ_code}&language=vi"
    if kind == "dividend":
        # Endpoint DUY NHẤT của cả nguồn nhận cả organCode lẫn ticker (00-conventions §5)
        return f"{FUND}/CashDividendAnalysis/GetAnalysis?OrganCode={organ_code}&Code={ticker}&language=vi"
    if kind == "valuation":
        return f"{TOOLS}/Valuation/GetValuation?OrganCode={organ_code}&language=vi"
    raise ValueError(f"kind lạ: {kind!r}")


def classify(kind: str, http: int, text: str) -> tuple[str, dict | None]:
    """('ok', bản ghi) | ('retry', None) | ('bad_shape', None)."""
    if http != 200:
        return "retry", None
    try:
        d = json.loads(text)
    except ValueError:
        return "retry", None
    if d.get("status") not in (0, "Success"):     # gồm "Failed" — lỗi tạm thời của nguồn
        return "retry", None
    items = d.get("items")
    if not isinstance(items, list) or not items or not isinstance(items[0], dict):
        return "bad_shape", None
    if ROOT_KEY[kind] not in items[0]:
        return "bad_shape", None
    return "ok", items[0]


@dataclass(frozen=True)
class Target:
    kind: str
    issuer_id: int
    organ_code: str
    ticker: str
    com_type: str | None
    found_by: str                                  # 'event' | 'floor'


class FetchError(Exception):
    """Một mã/kind hỏng sau mọi lần thử — để nó CHƯA KIỂM, không ghi gì."""


class BadShape(Exception):
    """Response hợp lệ nhưng thiếu khoá gốc — nguồn đổi hình dạng, thử lại vô ích."""


class Fetcher:
    def __init__(self, get, sleep=time.sleep, clock=time.monotonic):
        self._get, self._sleep, self._clock = get, sleep, clock
        self.calls = 0
        self.retries = 0
        self._last: float | None = None

    def _request(self, kind: str, u: str) -> tuple[int, str]:
        if self._last is not None:
            wait = MIN_INTERVAL - (self._clock() - self._last)
            if wait > 0:
                self._sleep(wait)
        self._last = self._clock()
        self.calls += 1
        return self._get(u, TIMEOUT[kind])

    def fetch_one(self, t: Target) -> tuple[dict, str]:
        u = url(t.kind, t.organ_code, t.ticker, t.com_type)
        http, text = 0, ""
        for attempt in range(RETRIES + 1):
            try:
                http, text = self._request(t.kind, u)
            except httpx.HTTPError as e:
                # Timeout/đứt kết nối đi CÙNG đường với response xấu (bài học lát 3, e7f80f6)
                http, text = 0, f"{type(e).__name__}: {e}"
            verdict, item = classify(t.kind, http, text)
            if verdict == "ok":
                return item, text
            if verdict == "bad_shape":
                raise BadShape(f"{t.organ_code}/{t.kind}: thiếu khoá gốc {ROOT_KEY[t.kind]!r}")
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
    # MỘT client cho trọn lượt — mở lại mỗi lời gọi là ~234 lần bắt tay TLS
    with httpx.Client(headers={"Origin": FIIN_ORIGIN}) as client:
        def get_one(u: str, timeout: float) -> tuple[int, str]:
            r = client.get(u, timeout=timeout)
            return r.status_code, r.text
        yield Fetcher(get_one, sleep, clock)
