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
