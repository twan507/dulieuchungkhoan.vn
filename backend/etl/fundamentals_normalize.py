"""Payload BCTC → dòng dạng dài + hash (spec §5.3). Thuần, không I/O.

Không có danh sách trắng: ba endpoint không có trường nào tính từ giá (đã kiểm 557 khoá, khảo sát
§6.2), nên hash trên TOÀN BỘ dòng đã chuẩn hoá — bớt đúng cái luật hay hỏng nhất của lát 4.
Hash tính trên dòng ĐÃ SẮP XẾP, nên nguồn đổi thứ tự khoá/kỳ hay thêm ô null không gây báo đổi giả.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
from dataclasses import dataclass

# 8 khoá không phải mã chỉ tiêu, có mặt trong response (đối chiếu từ điển 2026-09-04, khảo sát §6.2).
NON_METRIC = frozenset({"organCode", "ebit", "ebitDa", "operating",
                        "otherAssetBank", "otherAssetNonBank", "otherLiabilties", "rtq29"})
STATEMENT = {"bs": "BS", "is": "IS", "cf": "CF"}
STATEMENT_LENGTHS = frozenset({1, 2, 3, 4, 5})            # 1-4 quý, 5 năm — 0 dòng khác trên 5 mã
REPORT_LENGTHS = frozenset({1, 2, 3, 4, 5, 6, 9})         # PDF có thêm 6 bán niên, 9 chín tháng


class BadRecord(ValueError):
    """Bản ghi sai hợp đồng — cùng nhóm với BadShape của fetch, job đếm vào bad_shape."""


@dataclass(frozen=True)
class StatementRow:
    year: int
    length: int
    statement_type: str
    metric_code: str
    value: float


@dataclass(frozen=True)
class ReportRow:
    source_id: int
    year: int | None
    length: int | None
    title: str | None
    url: str


def statement_rows(kind: str, item: dict) -> list[StatementRow]:
    st = STATEMENT[kind]
    out: list[StatementRow] = []
    seen: set[tuple[int, int]] = set()
    for rec in (item.get("quarterly") or []) + (item.get("yearly") or []):
        year, length = rec.get("yearReport"), rec.get("quarterReport")
        if not isinstance(year, int) or length not in STATEMENT_LENGTHS:
            raise BadRecord(f"{kind}: quarterReport/yearReport lạ: {year!r}/{length!r}")
        if (year, length) in seen:
            raise BadRecord(f"{kind}: kỳ trùng {year}/{length}")
        seen.add((year, length))
        for k, v in rec.items():
            if k in ("yearReport", "quarterReport") or k in NON_METRIC or v is None:
                continue
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                raise BadRecord(f"{kind}: {k} không phải số: {v!r}")
            out.append(StatementRow(year, length, st, k.lower(), float(v)))
    return out


def report_rows(item: dict) -> list[ReportRow]:
    out: list[ReportRow] = []
    for it in item.get("items") or []:
        sid, u, length = it.get("id"), it.get("sourceUrl"), it.get("lengthReport")
        if not isinstance(sid, int) or not u:
            raise BadRecord(f"reports: thiếu id hoặc sourceUrl: {it!r}"[:200])
        if length is not None and length not in REPORT_LENGTHS:
            raise BadRecord(f"reports: lengthReport lạ {length!r} (id {sid})")
        out.append(ReportRow(sid, it.get("yearReport"), length, it.get("title"), u))
    return out


def rows(kind: str, item: dict) -> list:
    return report_rows(item) if kind == "reports" else statement_rows(kind, item)


def payload_hash(rows_: list) -> str:
    parts = sorted(json.dumps(dataclasses.astuple(r), separators=(",", ":"), ensure_ascii=False)
                   for r in rows_)
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


EMPTY_HASH = payload_hash([])
