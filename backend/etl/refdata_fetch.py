"""Tải 4 payload thô nguồn refdata (spec §2/§6).

I/O thuần — không parse, không phân loại; `refdata_normalize` xử lý tiếp.

🔴 Retry thêm 2026-09-07 (rà chuẩn hoá). Bản trước là `httpx.Client` trần + `raise_for_status()`
— đường tải DUY NHẤT trong 15 họ job không có lớp phục hồi nào, nên một `ConnectError` thoáng
qua giết trọn lượt `refdata` 08:00, mà `refdata` lại là job chặn cả ETL giá lẫn pipeline tin.

Dùng `http_fetch.Fetcher` chung thay vì viết lớp retry thứ tư (`price`/`snapshot`/`fundamentals`
mỗi họ đang có một bản gần giống hệt — nợ chuẩn hoá đã ghi, không mở rộng thêm ở đây).
Giữ `gap=(0.5, 0.5)` để đúng nhịp 0,5 s của họ FiinTrade (market-data-store §4.2), không lấy
nhịp ngẫu nhiên 1–5 s vốn dành cho nguồn quốc tế.
"""
from __future__ import annotations

import httpx

from etl import http_fetch

ENDPOINTS = {
    "quotes": "https://online.bvsc.com.vn/quotes?symbols=ALL",
    "indexsnaps": "https://online.bvsc.com.vn/datafeed/indexsnaps",
    "organization": "https://wlgw-core.fiintrade.vn/Master/GetListOrganization?language=vi",
    "icb": "https://wlgw-core.fiintrade.vn/Master/GetAllIcbIndustry?language=vi",
}

FIIN_ORIGIN = "https://fiinapp.bvsc.com.vn"   # bắt buộc cho *.fiintrade.vn (00-conventions §2)
GAP = (0.5, 0.5)                             # cố định, khuôn FiinTrade — không phải 1–5 s của global
TIMEOUT = 60.0


def headers_for(url: str) -> dict[str, str]:
    """Header riêng theo host. Tách thành hàm để kiểm được — `Fetcher.fetch_one` chỉ truyền
    `(url, timeout)` nên không có chỗ nào quan sát header nếu nó nằm ẩn trong closure."""
    return {"Origin": FIIN_ORIGIN} if "fiintrade.vn" in url else {}


def _classify(http: int, text: str):
    """Chỉ `200` kèm thân khác rỗng mới là xong; còn lại đều đáng thử lại.

    Không có nhánh `bad_shape`: bốn endpoint này trả JSON tự do, việc soi hình dạng thuộc
    `refdata_normalize`/`refdata_guard`, không thuộc lớp tải.
    """
    return ("ok", None) if http == 200 and text else ("retry", None)


def fetch(get=None, sleep=None) -> tuple[dict[str, str], int]:
    """(payload thô theo khoá, số lần đã thử lại). `get`/`sleep` bơm được để test."""
    result: dict[str, str] = {}
    if get is None:
        with httpx.Client(headers=http_fetch.DEFAULT_HEADERS, follow_redirects=True) as client:
            def get_one(u: str, timeout: float):
                r = client.get(u, timeout=timeout, headers=headers_for(u))
                return r.status_code, r.text, dict(r.headers)
            return _run(get_one, sleep, result)
    return _run(get, sleep, result)


def _run(get, sleep, result: dict[str, str]) -> tuple[dict[str, str], int]:
    import time
    with http_fetch.open_fetcher(_classify, get=get, sleep=sleep or time.sleep,
                                 gap=GAP, timeout=TIMEOUT) as f:
        for key, url in ENDPOINTS.items():
            _, text = f.fetch_one(url, key)
            result[key] = text
        return result, f.retries_done
