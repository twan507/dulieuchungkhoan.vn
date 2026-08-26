"""Tải 4 payload thô nguồn refdata (spec §2/§6).

I/O thuần — không parse, không phân loại; `refdata_normalize` xử lý tiếp.
"""
from __future__ import annotations

import httpx

ENDPOINTS = {
    "quotes": "https://online.bvsc.com.vn/quotes?symbols=ALL",
    "indexsnaps": "https://online.bvsc.com.vn/datafeed/indexsnaps",
    "organization": "https://wlgw-core.fiintrade.vn/Master/GetListOrganization?language=vi",
    "icb": "https://wlgw-core.fiintrade.vn/Master/GetAllIcbIndustry?language=vi",
}

FIIN_ORIGIN = "https://fiinapp.bvsc.com.vn"   # bắt buộc cho *.fiintrade.vn (00-conventions §2)


def fetch() -> dict[str, str]:
    result: dict[str, str] = {}
    with httpx.Client(timeout=60.0) as client:
        for key, url in ENDPOINTS.items():
            headers = {"Origin": FIIN_ORIGIN} if "fiintrade.vn" in url else {}
            resp = client.get(url, headers=headers)
            resp.raise_for_status()
            result[key] = resp.text
    return result
