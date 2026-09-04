"""Bóc tập trắng và tính hash cho bốn kind họ Snapshot (spec §4.3, §5.3). Thuần, không I/O.

Vì sao có tập trắng thay vì hash cả payload: đo 2026-09-04 cho thấy `rtd11` `rtd21` `rtd25`
(snapshot) và `priceEarningRatio` `dividendYield` (dividend) tính TỪ GIÁ, đổi mỗi ngày —
hash trọn payload thì 100% mã "đổi" mỗi lượt và kiến trúc trigger mất nghĩa.

Danh sách TRẮNG chứ không phải danh sách đen: nguồn thêm một trường theo giá về sau cũng
không tự sinh báo động giả.
"""
from __future__ import annotations

import hashlib
import json

# 13 trường lấy từ `summary`; 5 trường còn lại nằm ở khối kỳ báo cáo (KEEP_PERIOD).
# Tổng 18 ở ngân hàng, 15 ở phi ngân hàng — rtq44/rtq137/rqq41 CHỈ ngân hàng mới có (đo 9/9 mã).
KEEP_SUMMARY = ("ceo", "comTypeCode", "competitors", "majorHoldings", "statePercentage",
                "stateVolumn", "foreignerVolumn", "totalForeignRoom",
                "maximumForeignPercentage", "outstandingShare", "freeFloat",
                "valuePerShare", "rtq10")
KEEP_PERIOD = ("year", "quarter", "rtq44", "rtq137", "rqq41")

KEEP = {
    "dividend": ("cashDividendPayouts", "cashDividendPlans", "dps", "dividendPayoutRatio", "eps"),
    "valuation": ("estimatedEPS", "forecastEPS", "estimatedBookValue", "forcastBookValue",
                  "riskFreeRate", "recommendMethod", "rtd7", "rtq180", "outstandingShare"),
    "ownership": ("majorShareHolders", "boardOfDirectors", "overviewChartData",
                  "majorOwnershipsChartData"),
}


def _newest_period(item: dict) -> dict:
    """Kỳ báo cáo mới nhất. Hai mảng sắp xếp CŨ → MỚI (đo 2026-09-04) nên [0] là kỳ cũ nhất —
    chọn theo max(year, quarter) để không phụ thuộc thứ tự nguồn trả."""
    rows = item.get("quarterly") or item.get("yearly") or []
    if not rows:
        return {}
    return max(rows, key=lambda r: (r.get("year") or 0, r.get("quarter") or 0))


def keep(kind: str, item: dict) -> dict:
    """Tập trắng của một bản ghi. Khoá vắng thì BỎ QUA, không ném lỗi."""
    if kind == "snapshot":
        summary = item.get("summary") or {}
        out = {k: summary[k] for k in KEEP_SUMMARY if k in summary}
        period = _newest_period(item)
        out.update({k: period[k] for k in KEEP_PERIOD if k in period})
        return out
    if kind == "valuation":
        block = item.get("valuationStock") or {}
        return {k: block[k] for k in KEEP[kind] if k in block}
    if kind in KEEP:
        return {k: item[k] for k in KEEP[kind] if k in item}
    raise ValueError(f"kind lạ: {kind!r}")


def keep_hash(kind: str, item: dict) -> str:
    body = json.dumps(keep(kind, item), sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(body.encode("utf-8")).hexdigest()
