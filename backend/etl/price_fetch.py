"""Tải PriceData/GetPriceData theo mã, tuần tự, có giãn cách (spec §5.2). I/O thuần.

Ba điều đo 2026-09-03 quyết định hình dạng module (measurements.md):
- `status` trả lẫn 0 và "Success" trên CÙNG endpoint ⇒ hợp lệ là status ∈ {0, "Success"};
  kiểm `== "Success"` như lát 1–2 sẽ thử lại vô ích ~1/8 lời gọi.
- Mã sai trả {"status":"Failed","errors":["Code not valid: X"]} ⇒ CodeInvalid, không thử lại.
- Trang trả < 60 bản ghi là trang cuối; totalCount chính xác ⇒ ceil(totalCount/60) làm trần.
"""
from __future__ import annotations

import contextlib
import json
import logging
import math
import time
from dataclasses import dataclass, field

import httpx

log = logging.getLogger("etl.price")

URL = "https://wlgw-technical.fiintrade.vn/PriceData/GetPriceData"
FIIN_ORIGIN = "https://fiinapp.bvsc.com.vn"      # bắt buộc cho *.fiintrade.vn (00-conventions §2)
PAGE_SIZE = 60                                    # whitelist cứng: chỉ 30 | 60 (09-fiin-market-price)
TIMEOUT = 60.0                                    # ~200 KB/trang, ~1,8 s
RETRIES = 3
BACKOFF = (2, 4, 8)
MIN_INTERVAL = 0.5                                # trần 2 request/giây (market-data-store §4.2)
MAX_CONSECUTIVE_FAILURES = 10                     # 10 mã liên tiếp hỏng = nguồn/mạng chết


class FetchError(Exception):
    """Một mã hỏng sau mọi lần thử."""


class SourceDown(FetchError):
    """Nhiều mã liên tiếp hỏng — dừng cả lượt thay vì đi hết 1.523 mã mà không ghi gì."""


class CodeInvalid(Exception):
    """Nguồn không biết mã này (`Code not valid`) — lỗi có tên, không thử lại."""


@dataclass
class FetchResult:
    pages: dict[str, list[str]] = field(default_factory=dict)
    invalid: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)


def url(code: str, page: int) -> str:
    return f"{URL}?Code={code}&Frequently=Daily&Page={page}&PageSize={PAGE_SIZE}&language=vi"


def _parse(status: int, text: str) -> dict | None:
    if status != 200:
        return None
    try:
        d = json.loads(text)
    except ValueError:
        return None
    return d if isinstance(d, dict) else None


def _valid(d: dict | None) -> bool:
    return d is not None and d.get("status") in (0, "Success") and isinstance(d.get("items"), list)


def _code_invalid(d: dict | None) -> bool:
    return (d is not None and d.get("status") == "Failed"
            and any("Code not valid" in str(e) for e in (d.get("errors") or [])))


class Fetcher:
    """Giữ trạng thái giãn cách và bộ đếm cho trọn lượt. `get`/`sleep`/`clock` tiêm được để test."""

    def __init__(self, get, sleep=time.sleep, clock=time.monotonic):
        self._get, self._sleep, self._clock = get, sleep, clock
        self._last_start: float | None = None
        self._streak = 0
        self.retries = 0
        self.calls = 0

    def _request(self, code: str, page: int) -> tuple[int, str]:
        now = self._clock()
        if self._last_start is not None:
            wait = self._last_start + MIN_INTERVAL - now
            if wait > 0:
                self._sleep(wait)
                now = self._clock()
        self._last_start = now
        self.calls += 1
        return self._get(url(code, page))

    def _page(self, code: str, page: int) -> tuple[dict, str]:
        status, text = 0, ""
        for attempt in range(RETRIES + 1):
            status, text = self._request(code, page)
            d = _parse(status, text)
            if _valid(d):
                return d, text
            if _code_invalid(d):
                raise CodeInvalid(f"{code}: {d['errors']}")
            if attempt == RETRIES:
                break
            self._sleep(BACKOFF[attempt])
            self.retries += 1
        raise FetchError(f"{code} trang {page} hỏng sau {RETRIES + 1} lần (HTTP {status}): {text[:200]}")

    def _pages(self, code: str, max_pages: int | None) -> list[str]:
        d, text = self._page(code, 1)
        texts = [text]
        total = d.get("totalCount")
        cap = math.ceil(total / PAGE_SIZE) if isinstance(total, int) and total > 0 else None
        n = 1
        while (len(d["items"]) == PAGE_SIZE
               and (max_pages is None or n < max_pages)
               and (cap is None or n < cap)):
            n += 1
            d, text = self._page(code, n)
            texts.append(text)
        return texts

    def pages(self, code: str, max_pages: int | None = 1) -> list[str]:
        """Text các trang 1..n của một mã. Dừng ở trang < 60 bản ghi, ở max_pages, hoặc ở trần totalCount."""
        try:
            texts = self._pages(code, max_pages)
        except CodeInvalid:
            self._streak = 0                          # nguồn CÓ trả lời — không phải mạng chết
            raise
        except FetchError:
            self._streak += 1
            if self._streak >= MAX_CONSECUTIVE_FAILURES:
                raise SourceDown(f"{self._streak} mã liên tiếp hỏng — nguồn hoặc mạng chết, dừng lượt")
            raise
        self._streak = 0
        return texts

    def many(self, codes: list[str], max_pages: int | None = 1) -> FetchResult:
        res = FetchResult()
        for i, code in enumerate(codes, 1):
            try:
                res.pages[code] = self.pages(code, max_pages)
            except CodeInvalid:
                res.invalid.append(code)
            except SourceDown:
                raise
            except FetchError as e:
                res.failed.append(code)
                log.warning("%s", e)
            if i % 100 == 0:
                log.info("đã gọi %d/%d mã (%d lời gọi, %d retry)", i, len(codes), self.calls, self.retries)
        return res


@contextlib.contextmanager
def open_fetcher(get=None, sleep=time.sleep, clock=time.monotonic):
    if get is not None:                                   # test tiêm get giả, không mở kết nối
        yield Fetcher(get, sleep, clock)
        return
    # MỘT client cho trọn lượt (khuôn events_fetch) — mở lại mỗi mã là 1.523 lần bắt tay TLS
    with httpx.Client(timeout=TIMEOUT, headers={"Origin": FIIN_ORIGIN}) as client:
        def get_one(u: str) -> tuple[int, str]:
            r = client.get(u)
            return r.status_code, r.text
        yield Fetcher(get_one, sleep, clock)
