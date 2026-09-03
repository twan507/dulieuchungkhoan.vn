"""Tải 52 trang GetScreenerItems, tuần tự (spec etl screener §5.2).

I/O thuần — không parse ngoài việc đọc totalCount/status để phân trang và retry.
Trang hỏng thử lại tối đa 3 lần (2·4·8 s); hết thì raise — KHÔNG trả trang rỗng
(00-conventions §10.5: trang trắng vào kho mà không ai biết).
"""
from __future__ import annotations

import json
import math
import time

import httpx

URL = "https://wlgw-tools.fiintrade.vn/Screener/GetScreenerItems?language=vi"
FIIN_ORIGIN = "https://fiinapp.bvsc.com.vn"          # bắt buộc cho *.fiintrade.vn (00-conventions §2)
PAGE_SIZE = 30                                        # enum: chỉ nhận 30 (10-fiin-dictionary)
CRITERION = {"code": "ClosePrice", "type": "Range", "unit": "VND",
             "valueRange": [100.0, 614345.0], "selectedValue": [100.0, 614345.0]}
RETRIES = 3
BACKOFF = (2, 4, 8)


class FetchError(Exception):
    """Một trang hỏng sau mọi lần thử — lượt chạy phải thất bại, không ghi gì."""


def _body(page: int) -> dict:
    return {"comGroupCode": "ALL", "icbCode": "ALL", "page": page, "pageSize": PAGE_SIZE,
            "parameters": [CRITERION]}


def _valid(status: int, text: str) -> bool:
    if status != 200:
        return False
    try:
        d = json.loads(text)
    except ValueError:
        return False
    return d.get("status") == "Success" and isinstance(d.get("items"), list)


def _page(post, sleep, page: int) -> tuple[str, int]:
    retries = 0
    for attempt in range(RETRIES + 1):
        try:
            status, text = post(_body(page))
        except httpx.HTTPError as e:
            # Timeout/đứt kết nối đi CÙNG đường với response xấu — thử lại rồi mới FetchError.
            # Cùng lỗi lát 3 vá (e7f80f6): máy ngủ giữa lời gọi, ReadTimeout lọt ra ngoài vòng retry.
            status, text = 0, f"{type(e).__name__}: {e}"
        if _valid(status, text):
            return text, retries
        if attempt == RETRIES:
            break
        sleep(BACKOFF[attempt])
        retries += 1
    raise FetchError(f"trang {page} hỏng sau {RETRIES + 1} lần (HTTP {status}): {text[:200]}")


def _pages(post, sleep) -> tuple[list[str], int]:
    first, retries = _page(post, sleep, 1)
    total = int(json.loads(first)["totalCount"])
    pages = [first]
    for p in range(2, math.ceil(total / PAGE_SIZE) + 1):
        text, r = _page(post, sleep, p)
        pages.append(text)
        retries += r
    return pages, retries


def fetch(post=None, sleep=time.sleep) -> tuple[list[str], int]:
    if post is not None:                                  # test tiêm post giả, không mở kết nối
        return _pages(post, sleep)
    # MỘT client cho trọn 52 trang (khuôn `refdata_fetch`) — mở lại mỗi trang là 52 lần
    # bắt tay TLS trên cùng một host, không được gì.
    with httpx.Client(timeout=60.0) as client:
        def post_one(body: dict) -> tuple[int, str]:
            r = client.post(URL, json=body, headers={"Origin": FIIN_ORIGIN})
            return r.status_code, r.text
        return _pages(post_one, sleep)
