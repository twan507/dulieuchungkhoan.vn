# backend/etl/events_normalize.py
"""Chuẩn hoá lịch sự kiện — thuần, không I/O (spec §5.3).

Hai bẫy của nguồn, cả hai đã đo:
  1. publicDate ĐÔI KHI kèm giờ ('2018-03-27T11:03:28.023' cạnh '2018-03-27T00:00:00').
     Không cắt ngày thì cùng một sự kiện thành hai khoá.
  2. planVolumn viết SAI CHÍNH TẢ ở nguồn — đọc đúng tên nguồn, đừng "sửa".
"""
from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import date

DUP_SAMPLE = 20            # nêu tên tối đa 20 khoá — đủ chẩn đoán, không phình ops.etl_run.stats


@dataclass(frozen=True)
class EventRow:
    event_type: str
    organ_code: str
    name_hint: str | None
    public_date: date | None
    exright_date: date | None
    record_date: date | None
    payout_date: date | None
    year_report: int | None
    length_report: int | None
    stage_key: str | None
    source_url: str | None
    payload: dict

    @property
    def natural_key(self) -> tuple:
        """Đúng 7 thành phần của `corporate_event_natural_key` (migration 0004),
        với issuer thay bằng organ_code vì lúc này chưa ghép issuer_id."""
        return (self.event_type, self.organ_code, self.public_date, self.exright_date,
                self.year_report, self.length_report, self.stage_key or "")


@dataclass(frozen=True)
class Normalized:
    rows: list[EventRow]
    counts: dict[str, int]
    collected: dict[str, int]
    dup_conflicts: int
    dup_keys: list[str]


def _date(v: str | None) -> date | None:
    return date.fromisoformat(v[:10]) if v else None


def _stage_key(event_type: str, it: dict) -> str | None:
    # CashDividend/StockDividend và ShareIssuance: công thức của thiết kế (step-03 §4, F6).
    if event_type in ("CashDividend", "StockDividend"):
        return f"{it.get('dividendYear')}|{it.get('stageName') or ''}"
    # 🔴 planVolumn thêm ngoài thiết kế: issueYear gỡ đúng 2/129 khoá đụng, planVolumn gỡ 103.
    if event_type == "ShareIssuance":
        return f"{it.get('issueMethodName') or ''}|{it.get('issueYear')}|{it.get('planVolumn')}"
    # 🔴 AGM thiết kế bỏ trống: 16 khoá đụng vì DN triệu tập đại hội nhiều lần cùng ngày
    # công bố. eventTitle KHÔNG dùng được — null 23.467/23.467.
    if event_type == "AGM":
        d = _date(it.get("issueDate"))
        return d.isoformat() if d else ""
    return None                                     # Earning, IPO: 0 khoá đụng trên toàn kho


def _row(event_type: str, it: dict) -> EventRow:
    return EventRow(
        event_type=event_type,
        organ_code=it["organCode"],
        name_hint=it.get("organShortName") or it.get("organName") or it.get("ticker"),
        public_date=_date(it.get("publicDate")),
        exright_date=_date(it.get("exrightDate")),
        record_date=_date(it.get("recordDate")),
        payout_date=_date(it.get("payoutDate")),
        year_report=it.get("yearReport"),
        length_report=it.get("lengthReport"),
        stage_key=_stage_key(event_type, it),
        source_url=it.get("sourceUrl"),             # chỉ AGM có
        payload=it,
    )


def _completeness(it: dict) -> int:
    return sum(1 for v in it.values() if v is not None)


def _dedupe(rows: list[EventRow]) -> tuple[list[EventRow], int, list[str]]:
    """Nguồn tự đẻ trùng, và giữ hai phiên bản của cùng sự kiện sau khi dời ngày.

    Giữ bản ĐẦY ĐỦ NHẤT; hoà thì lấy bản xuất hiện sau (nguồn trả byte-identical
    giữa hai lượt gọi nên thứ tự là deterministic).
    """
    groups: dict[tuple, list[tuple[int, EventRow]]] = defaultdict(list)
    for i, r in enumerate(rows):
        groups[r.natural_key].append((i, r))
    kept: list[tuple[int, EventRow]] = []
    dup, dup_keys = 0, []
    for key, members in groups.items():
        if len(members) > 1:
            dup += len(members) - 1
            dup_keys.append("|".join("" if p is None else str(p) for p in key))
        kept.append(max(members, key=lambda im: (_completeness(im[1].payload), im[0])))
    kept.sort(key=lambda im: im[0])
    return [r for _, r in kept], dup, sorted(dup_keys)[:DUP_SAMPLE]


def normalize(pages: dict[str, list[str]]) -> Normalized:
    rows: list[EventRow] = []
    counts: dict[str, int] = {}
    collected: dict[str, int] = {}
    for event_type, texts in pages.items():
        total, got = 0, 0
        for i, text in enumerate(texts):
            d = json.loads(text)
            if i == 0:
                total = int(d["totalCount"])
            for it in d["items"]:
                rows.append(_row(event_type, it))
                got += 1
        counts[event_type] = total
        collected[event_type] = got
    kept, dup, dup_keys = _dedupe(rows)
    return Normalized(rows=kept, counts=counts, collected=collected,
                      dup_conflicts=dup, dup_keys=dup_keys)
