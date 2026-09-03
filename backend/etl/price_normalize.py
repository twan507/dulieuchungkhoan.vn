"""Chuẩn hoá bản ghi getPriceData → PriceRow (spec §5.3). Thuần, không I/O.

Đo 2026-09-03: `closePrice` là giá THÔ khớp sàn, `closeValue` là giá đã điều chỉnh hồi tố
(measurements.md §1) — hai cột khác nhau của lược đồ, không phải hai tên của một giá.
Số đi qua Decimal(str(v)) để giữ đúng chữ số nguồn (5747.8202873773), không qua float8.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class PriceRow:
    organ_code: str
    trading_date: date
    close_adj: Decimal | None
    close_raw: Decimal | None
    open_value: Decimal | None
    highest_value: Decimal | None
    lowest_value: Decimal | None
    payload: dict


@dataclass(frozen=True)
class CodeSummary:
    n_rows: int
    latest: date | None


def _dec(v):
    return None if v is None else Decimal(str(v))


def _date(s: str) -> date:
    return date.fromisoformat(s[:10])


def _items(texts: list[str]):
    for text in texts:
        yield from json.loads(text)["items"]


def normalize_code(organ_code: str, texts: list[str]) -> tuple[list[PriceRow], int]:
    rows: list[PriceRow] = []
    seen: set[date] = set()
    dups = 0
    for it in _items(texts):
        d = _date(it["tradingDate"])
        if d in seen:
            dups += 1          # trang chồng ngày (phiên mới chen vào giữa hai lời gọi) — giữ bản thấy trước
            continue
        seen.add(d)
        rows.append(PriceRow(organ_code, d, _dec(it.get("closeValue")), _dec(it.get("closePrice")),
                             _dec(it.get("openValue")), _dec(it.get("highestValue")),
                             _dec(it.get("lowestValue")), it))
    return rows, dups


def summarize(texts: list[str]) -> CodeSummary:
    """Số phiên và ngày mới nhất — KHÔNG giữ bản ghi (guard trước khi parse 91.000 dict)."""
    dates = {_date(it["tradingDate"]) for it in _items(texts)}
    return CodeSummary(len(dates), max(dates) if dates else None)
