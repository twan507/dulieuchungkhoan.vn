"""Chuẩn hoá payload thô 4 endpoint refdata thành bản ghi có kiểu (spec §3 luật 2).

Thuần — không I/O, không gọi mạng. Nhận JSON text (đã fetch sẵn), trả về
`NormResult` cho `refdata_merge` dùng tiếp.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass

from etl.refdata_indices import SNAP_CODES

log = logging.getLogger(__name__)

_STOCK_SYMBOL = re.compile(r"[A-Z0-9]{3}")


class RefdataError(Exception):
    """Dữ liệu nguồn vi phạm bất biến cứng — không thể tiếp tục normalize."""


@dataclass(frozen=True)
class QuoteRec:
    symbol: str
    full_name: str | None
    exchange: str
    security_type: str        # 'stock' | 'etf' — ĐÃ phân loại theo spec luật 2
    tradelot: int | None


@dataclass(frozen=True)
class OrgRec:
    organ_code: str
    ticker: str
    com_group_code: str
    organ_name: str
    organ_short_name: str | None
    com_type_code: str | None
    organ_type_code: str | None   # 'DN' | 'OTHER' — luật 6: khử trùng ticker ưu tiên DN
    icb_code: str | None


@dataclass(frozen=True)
class IcbRec:
    icb_code: str
    icb_name: str | None
    parent_icb_code: str | None
    icb_level: int | None
    icb_code_path: str | None


@dataclass(frozen=True)
class NormResult:
    quotes: list[QuoteRec]        # chỉ stock/etf đã lọc
    index_codes: frozenset[str]   # mã indexsnaps THẬT xuất hiện, sau lọc rác
    orgs: list[OrgRec]
    icb: list[IcbRec]
    counters: dict[str, int]      # skipped_cw · skipped_bond · junk_stocktype2 · unknown_stocktype · index_junk


def _unwrap_list(text: str) -> list[dict]:
    """Bóc payload dạng `{"s","d"}` (BVSC) hoặc list trần — khuôn `catalog.py`."""
    body = json.loads(text)
    if isinstance(body, list):
        return body
    return body.get("d") or []


def _unwrap_items(text: str) -> list[dict]:
    """Bóc payload dạng `{"items": [...]}` (FiinTrade)."""
    body = json.loads(text)
    if isinstance(body, list):
        return body
    return body.get("items") or []


def normalize(raw: dict[str, str]) -> NormResult:
    """raw keys: 'quotes' | 'indexsnaps' | 'organization' | 'icb' — text JSON nguyên văn."""
    counters = {
        "skipped_cw": 0,
        "skipped_bond": 0,
        "junk_stocktype2": 0,
        "unknown_stocktype": 0,
        "index_junk": 0,
    }

    quotes: list[QuoteRec] = []
    for r in _unwrap_list(raw["quotes"]):
        stock_type = r.get("StockType")
        symbol = r["symbol"]
        if stock_type == "2":
            if _STOCK_SYMBOL.fullmatch(symbol):
                security_type = "stock"
            else:
                counters["junk_stocktype2"] += 1
                continue
        elif stock_type == "3":
            security_type = "etf"
        elif stock_type == "4":
            counters["skipped_cw"] += 1
            continue
        elif stock_type == "12":
            counters["skipped_bond"] += 1
            continue
        else:
            counters["unknown_stocktype"] += 1
            log.warning("refdata: StockType lạ %r cho symbol %s", stock_type, symbol)
            continue
        quotes.append(QuoteRec(
            symbol=symbol,
            full_name=r.get("FullName"),
            exchange=r["exchange"],
            security_type=security_type,
            tradelot=r.get("tradelot"),
        ))

    index_codes: set[str] = set()
    for r in _unwrap_list(raw["indexsnaps"]):
        code = r.get("marketCode")
        if code in SNAP_CODES:
            index_codes.add(code)
        else:
            counters["index_junk"] += 1

    symbols = {q.symbol for q in quotes}
    if SNAP_CODES & symbols:
        raise RefdataError(
            f"mã indexsnaps trùng symbol /quotes: {SNAP_CODES & symbols}"
        )

    orgs = [
        OrgRec(
            organ_code=r["organCode"],
            ticker=r["ticker"],
            com_group_code=r["comGroupCode"],
            organ_name=r["organName"],
            organ_short_name=r.get("organShortName"),
            com_type_code=r.get("comTypeCode"),
            organ_type_code=r.get("organTypeCode"),
            icb_code=r.get("icbCode"),
        )
        for r in _unwrap_items(raw["organization"])
    ]

    icb = [
        IcbRec(
            icb_code=r["icbCode"],
            icb_name=r.get("icbName"),
            parent_icb_code=r.get("parentIcbCode"),
            icb_level=r.get("icbLevel"),
            icb_code_path=r.get("icbCodePath"),
        )
        for r in _unwrap_items(raw["icb"])
    ]

    return NormResult(
        quotes=quotes,
        index_codes=frozenset(index_codes),
        orgs=orgs,
        icb=icb,
        counters=counters,
    )
