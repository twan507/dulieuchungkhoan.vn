"""Chốt chặn sụt hai tầng cho job refdata (spec §4).

Module thuần: không I/O, không import module refdata khác. Đầu vào là
mapping/set trần để test không cần database.
"""

from dataclasses import dataclass
from typing import AbstractSet, Mapping

DROP_RATIO = 0.02        # tầng 1 (spec §4)
DELIST_RATIO = 0.01      # tầng 2


@dataclass(frozen=True)
class GuardVerdict:
    ok: bool
    reasons: tuple[str, ...]     # rỗng khi ok


def check(
    counts: Mapping[str, int],
    baseline: Mapping[str, int] | None,
    index_codes_seen: AbstractSet[str],
    expected_index_codes: AbstractSet[str],
    planned_delist: int,
    listed_now: int,
) -> GuardVerdict:
    reasons: list[str] = []

    # Tầng 1 — tỷ lệ sụt từng endpoint so mốc (lần chạy đầu không mốc thì bỏ trọn).
    if baseline is not None:
        for key, base_count in baseline.items():
            if key not in counts:
                continue
            count = counts[key]
            if count < base_count * (1 - DROP_RATIO):
                reasons.append(
                    f"{key}: count {count} < baseline {base_count} minus {DROP_RATIO:.0%}"
                )

    # Tầng 1 — khớp-tập cho indexsnaps, chạy CẢ KHI không có mốc.
    missing = expected_index_codes - index_codes_seen
    if missing:
        reasons.append(f"indexsnaps missing expected codes: {sorted(missing)}")

    # Tầng 2 — tỷ lệ tác động của phép lật delisted.
    if listed_now > 0 and planned_delist > listed_now * DELIST_RATIO:
        reasons.append(
            f"planned_delist {planned_delist} > listed_now {listed_now} times {DELIST_RATIO:.0%}"
        )

    return GuardVerdict(ok=not reasons, reasons=tuple(reasons))
