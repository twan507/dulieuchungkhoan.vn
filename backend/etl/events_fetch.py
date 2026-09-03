"""Tải TRỌN sáu họ Calendar/GetCorporate* mỗi lượt (spec §5.2).

Không dùng FromDate: đo 2026-09-03 cho thấy mỗi họ lọc theo một trục ngày khác nhau,
và Earning lọc theo trường KHÔNG có trong response — cửa sổ 5 ngày trả 24 bản ghi
trong khi có 217 bản ghi mang publicDate trong đúng cửa sổ đó (measurements.md §2.1).
Tải trọn hết 9 lời gọi, dưới ngân sách ~10 mà market-data-store §4.1 cấp cho họ này.
"""
from __future__ import annotations

import json
import time

import httpx

BASE = "https://wlgw-market.fiintrade.vn/Calendar"
FIIN_ORIGIN = "https://fiinapp.bvsc.com.vn"      # bắt buộc cho *.fiintrade.vn (00-conventions §2)
PAGE_SIZE = 20000                                 # đo: nhóm này KHÔNG có whitelist PageSize
TIMEOUT = 300.0                                   # Earning ~36 s/trang ở 20.000 — 60 s của lát 1 sẽ đứt
RETRIES = 3
BACKOFF = (2, 4, 8)

FAMILIES = {
    "AGM": "GetCorporateAGM",
    "CashDividend": "GetCorporateCashDividend",
    "StockDividend": "GetCorporateStockDividend",
    "Earning": "GetCorporateEarning",
    "IPO": "GetCorporateIPO",
    "ShareIssuance": "GetCorporateShareIssuance",
}


class FetchError(Exception):
    """Một trang hỏng sau mọi lần thử — lượt chạy phải thất bại, không ghi gì."""


def _url(endpoint: str, page: int) -> str:
    return f"{BASE}/{endpoint}?Page={page}&PageSize={PAGE_SIZE}&language=vi"


def _valid(status: int, text: str) -> bool:
    if status != 200:
        return False
    try:
        d = json.loads(text)
    except ValueError:
        return False
    return d.get("status") == "Success" and isinstance(d.get("items"), list)


def _page(get, sleep, endpoint: str, page: int) -> tuple[str, int]:
    retries = 0
    status, text = 0, ""
    for attempt in range(RETRIES + 1):
        status, text = get(_url(endpoint, page))
        if _valid(status, text):
            return text, retries
        if attempt == RETRIES:
            break
        sleep(BACKOFF[attempt])
        retries += 1
    raise FetchError(f"{endpoint} trang {page} hỏng sau {RETRIES + 1} lần (HTTP {status}): {text[:200]}")


def _family(get, sleep, endpoint: str) -> tuple[list[str], int]:
    first, retries = _page(get, sleep, endpoint, 1)
    d = json.loads(first)
    total, got, texts, page = int(d["totalCount"]), len(d["items"]), [first], 1
    while got < total:
        page += 1
        text, r = _page(get, sleep, endpoint, page)
        retries += r
        items = json.loads(text)["items"]
        if not items:
            # 00-conventions §10.5: trang trắng vào kho mà không ai biết
            raise FetchError(f"{endpoint} trang {page} rỗng trong khi mới gom {got}/{total}")
        texts.append(text)
        got += len(items)
    return texts, retries


def _all(get, sleep) -> tuple[dict[str, list[str]], int]:
    pages: dict[str, list[str]] = {}
    retries = 0
    for event_type, endpoint in FAMILIES.items():
        texts, r = _family(get, sleep, endpoint)
        pages[event_type] = texts
        retries += r
    return pages, retries


def fetch(get=None, sleep=time.sleep) -> tuple[dict[str, list[str]], int]:
    if get is not None:                                   # test tiêm get giả, không mở kết nối
        return _all(get, sleep)
    # MỘT client cho trọn lượt (khuôn screener_fetch) — mở lại mỗi trang là bắt tay TLS thừa
    with httpx.Client(timeout=TIMEOUT, headers={"Origin": FIIN_ORIGIN}) as client:
        def get_one(url: str) -> tuple[int, str]:
            r = client.get(url)
            return r.status_code, r.text
        return _all(get_one, sleep)
