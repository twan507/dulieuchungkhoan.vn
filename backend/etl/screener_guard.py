"""Chốt chặn cho job screener — ba vế, vế nào hỏng cũng từ chối (spec §5.4).

Module thuần: không I/O, đầu vào là số trần để test không cần database.
Vế (i) là lý do tồn tại: nguồn đóng dấu tradingDate = hôm nay ngay từ trước mở cửa
với giá 0 (đo 2026-09-03) — không có vế này, mỗi ngày lễ đẻ ~1.545 dòng ma.
"""
from dataclasses import dataclass

DROP_RATIO = 0.02
UNMAPPED_RATIO = 0.02


@dataclass(frozen=True)
class GuardVerdict:
    ok: bool
    reasons: tuple[str, ...]


def check(total_count: int, collected: int, priced: int, unmapped: int,
          baseline_items: int | None) -> GuardVerdict:
    reasons: list[str] = []
    if priced <= 0:                                                        # (i)
        reasons.append("không có mã nào có closePrice > 0 — không phải ngày giao dịch")
    if collected != total_count:                                           # (ii) đủ trang
        reasons.append(f"gom được {collected} mã, totalCount báo {total_count} — thiếu trang")
    if baseline_items is not None and total_count < baseline_items * (1 - DROP_RATIO):
        reasons.append(f"totalCount {total_count} sụt quá {DROP_RATIO:.0%} so mốc {baseline_items}")
    if collected > 0 and unmapped > collected * UNMAPPED_RATIO:            # (iii)
        reasons.append(f"{unmapped}/{collected} mã không ghép được security_id — quá {UNMAPPED_RATIO:.0%}")
    return GuardVerdict(ok=not reasons, reasons=tuple(reasons))
