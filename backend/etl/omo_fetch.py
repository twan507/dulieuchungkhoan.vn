"""Tải trang OMO của SBV qua cổng WAF — sbv-omo.md §3/§6.

Bẫy chính: WAF chặn bằng HTTP 200 + body 246 byte "Request Rejected".
Cổng: body ≥ MIN_BYTES VÀ chứa MARKER; hụt một trong hai → WafBlocked, không ghi gì.
"""
from __future__ import annotations

import time

import httpx

URL = "https://sbv.gov.vn/vi/nghi%E1%BB%87p-v%E1%BB%A5-th%E1%BB%8B-tr%C6%B0%E1%BB%9Dng-m%E1%BB%9F"
MARKER = "KẾT QUẢ ĐẤU THẦU THỊ TRƯỜNG MỞ"
MIN_BYTES = 100_000  # trang thật ~414 KB; <10 KB chắc chắn bị chặn — biên an toàn
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                  " (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "vi,en;q=0.9",
}


class WafBlocked(RuntimeError):
    """Nghi WAF chặn hoặc trang đổi cấu trúc — cấm ghi kho lẫn staging."""


def check_gate(body: str) -> None:
    n = len(body.encode("utf-8"))
    if n < MIN_BYTES:
        raise WafBlocked(f"body {n} byte < {MIN_BYTES} — nghi WAF chặn")
    if MARKER not in body:
        raise WafBlocked("body đủ dài nhưng thiếu chuỗi mốc — trang đổi cấu trúc?")


def fetch(client: httpx.Client | None = None, retry_delay_s: float = 60.0) -> str:
    own = client is None
    client = client or httpx.Client(headers=HEADERS, timeout=30.0, follow_redirects=True)
    try:
        for attempt in (1, 2):  # một lần retry cho lỗi mạng; WAF chặn thì KHÔNG retry
            try:
                resp = client.get(URL, headers=HEADERS)
                resp.raise_for_status()
                body = resp.text
                break
            except httpx.TransportError:
                if attempt == 2:
                    raise
                time.sleep(retry_delay_s)
        check_gate(body)
        return body
    finally:
        if own:
            client.close()
