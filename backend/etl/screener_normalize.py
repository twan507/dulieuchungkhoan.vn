"""Chuẩn hoá response GetScreenerItems thành ScreenerRow (spec etl screener §5.3).

Thuần — không I/O ngoài việc nạp bảng chọn trường lúc import. Nhận text thô
từng trang (đã fetch sẵn), trả NormResult cho merge/guard/store dùng tiếp.

10 khoá keep nằm ở cả `stockScreenerItem` lẫn `financial`, và 3 trong đó (`rtq12` `rtq27`
`rtq83`) có giá trị KHÁC nhau — lệch 52/90 cặp trên mẫu 28/08, kể cả đổi dấu. **Chốt
2026-09-03: `stockScreenerItem` là khối chuẩn**, mỗi mã chỉ lưu MỘT bản, theo
`BLOCK_PRIORITY`. Hai bằng chứng độc lập (spec etl screener §9.4):

1. Bundle JS của chính FiinTrade khai bản đồ cột có chỉ định khối — ROE đọc từ
   `"stockScreenerItem.rtq12"`, và mọi mã keep khác cũng khai `stockScreenerItem`.
2. Đẳng thức kế toán ROE = LNST(TTM) x P/B / vốn hoá, tính độc lập từ `isa20TTM`
   `rtd25` `rtd11`: `stockScreenerItem` sai số trung vị 8,1% (4 mã khớp trong 2%),
   `financial` 23,0% (0 mã khớp trong 2%).

⚠️ Bằng chứng (2) chỉ chạy được cho `rtq12`; `rtq27`/`rtq83` theo cùng luật vì bundle
xếp chúng cùng nhóm — suy luận, chưa đo riêng. `dup_conflicts` vẫn ĐẾM số cặp lệch
trước khi khử, làm chỉ báo sức khoẻ nguồn: nguồn đổi cách tính thì con số này đổi.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

# Bảng chọn trường là nguồn sự thật "trường này lấy hay bỏ" — không hardcode danh sách ở đây.
SELECTION_JSON = Path(__file__).resolve().parents[2] / "docs" / "20-design" / "market-field-selection.json"
BLOCKS = ("priceInfo", "stockScreenerItem", "performance", "financial", "technical")
# Thứ tự giành mã khi một khoá có ở nhiều khối — xem docstring. `financial` chỉ nhận
# những mã mà `stockScreenerItem` KHÔNG có — 5 mã họ tỷ số/thị trường mà BCTC cũng không cấp:
# fryq30 · rtd39 · rtd53 (EPS Forward) · rtd54 (P/E Forward, suy) · rtq81 (T.trưởng LN YoY).
BLOCK_PRIORITY = ("stockScreenerItem", "financial", "priceInfo", "performance", "technical")
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
    nulls = sum(1 for b in BLOCKS if item.get(b) is None)
    seen: dict[str, list] = {}                # mã keep → giá trị của nó ở TỪNG khối (trước khi khử)
    for b in BLOCKS:
        blk = item.get(b)
        if blk is None:
            continue
        for k, v in blk.items():
            if k in KEEP[b]:
                seen.setdefault(k, []).append(v)
    conflicts = sum(1 for vs in seen.values() if len(vs) > 1 and any(v != vs[0] for v in vs[1:]))
    payload: dict = {}
    claimed: set[str] = set()
    for b in BLOCK_PRIORITY:                  # khối ưu tiên cao giành mã trước
        blk = item.get(b)
        if blk is None:
            continue
        kept = {k: v for k, v in blk.items() if k in KEEP[b] and k not in claimed}
        if kept:
            payload[b] = kept
            claimed.update(kept)
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
