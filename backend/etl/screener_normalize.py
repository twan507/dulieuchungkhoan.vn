"""Chuẩn hoá response GetScreenerItems thành ScreenerRow (spec etl screener §5.3).

Thuần — không I/O ngoài việc nạp bảng chọn trường lúc import. Nhận text thô
từng trang (đã fetch sẵn), trả NormResult cho merge/guard/store dùng tiếp.

Tập keep áp **cho từng khối**: khoá nào nằm ở nhiều khối thì GIỮ BẢN SAO Ở MỌI KHỐI —
không chọn khối ưu tiên, không vứt bản nào. Hai bản có thể KHÁC nhau (`rtq12` `rtq27`
`rtq83` lệch 52/90 cặp trên mẫu 28/08, kể cả đổi dấu), nên `dup_conflicts` **đếm** độ
lệch để nhìn thấy được — không giải quyết nó; khối nào là chuẩn là quyết định của chủ
dự án (spec etl screener §9.4).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

# Bảng chọn trường là nguồn sự thật "trường này lấy hay bỏ" — không hardcode danh sách ở đây.
SELECTION_JSON = Path(__file__).resolve().parents[2] / "docs" / "20-design" / "market-field-selection.json"
BLOCKS = ("priceInfo", "stockScreenerItem", "performance", "financial", "technical")
EXCHANGE = {"VNINDEX": "HOSE", "HNXIndex": "HNX", "UpcomIndex": "UPCOM"}


def _load_keep() -> dict[str, frozenset[str]]:
    rows = json.loads(SELECTION_JSON.read_text(encoding="utf-8"))
    keep = frozenset(r["code"] for r in rows if r["source"] == "Screener" and r["keep"] is True)
    # Cùng một tập keep cho mọi khối: 27 khoá trùng khối được giữ ở MỌI khối có nó — không chọn khối ưu tiên.
    return {b: keep for b in BLOCKS}


KEEP = _load_keep()


@dataclass(frozen=True)
class ScreenerRow:
    ticker: str
    exchange: str
    organ_code: str | None
    trading_date: date
    close_price: float
    payload: dict


@dataclass(frozen=True)
class NormResult:
    rows: list[ScreenerRow]
    total_count: int
    unknown_com_group: int
    null_blocks: int
    dup_conflicts: int


def _row(item: dict) -> tuple[ScreenerRow | None, int, bool, int]:
    """Trả (row | None nếu bỏ, số khối null, bỏ vì com_group lạ?, số mã lệch giữa các khối)."""
    pi = item.get("priceInfo") or {}
    exchange = EXCHANGE.get(pi.get("comGroupCode"))
    if exchange is None:
        return None, 0, True, 0
    nulls = 0
    payload: dict = {}
    seen: dict[str, list] = {}                # mã keep → các giá trị của nó ở từng khối
    for b in BLOCKS:
        blk = item.get(b)
        if blk is None:
            nulls += 1
            continue
        kept = {k: v for k, v in blk.items() if k in KEEP[b]}
        for k, v in kept.items():
            seen.setdefault(k, []).append(v)
        if kept:
            payload[b] = kept
    conflicts = sum(1 for vs in seen.values() if len(vs) > 1 and any(v != vs[0] for v in vs[1:]))
    ts = datetime.fromisoformat(pi["tradingDate"])
    return ScreenerRow(
        ticker=pi["ticker"], exchange=exchange, organ_code=pi.get("organCode"),
        trading_date=ts.date(), close_price=float(pi.get("closePrice") or 0.0), payload=payload,
    ), nulls, False, conflicts


def normalize(pages: list[str]) -> NormResult:
    rows: list[ScreenerRow] = []
    unknown = 0
    nulls = 0
    conflicts = 0
    total_count = 0
    for i, text in enumerate(pages):
        d = json.loads(text)
        if i == 0:
            total_count = int(d["totalCount"])
        for item in d["items"]:
            row, n, skipped, c = _row(item)
            nulls += n
            if skipped:
                unknown += 1
                continue
            conflicts += c
            rows.append(row)
    return NormResult(rows=rows, total_count=total_count, unknown_com_group=unknown,
                      null_blocks=nulls, dup_conflicts=conflicts)
