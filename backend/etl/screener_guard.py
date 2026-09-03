"""Chốt chặn cho job screener — bốn vế, vế nào hỏng cũng từ chối (spec §5.4).

Module thuần: không I/O, đầu vào là số trần để test không cần database.
Vế (i) là lý do tồn tại: nguồn đóng dấu tradingDate = hôm nay ngay từ trước mở cửa
với giá 0 (đo 2026-09-03) — không có vế này, mỗi ngày lễ đẻ ~1.545 dòng ma.
"""
from dataclasses import dataclass

DROP_RATIO = 0.02
UNMAPPED_RATIO = 0.02
MIN_PRICED_RATIO = 0.5


@dataclass(frozen=True)
class GuardVerdict:
    ok: bool
    reasons: tuple[str, ...]


def check(total_count: int, collected: int, priced: int, unmapped: int,
          baseline_items: int | None, *, unknown: int = 0) -> GuardVerdict:
    reasons: list[str] = []
    # (i) TỶ LỆ, không phải "> 0": một mã lẻ có giá trong ngày lễ không được phép mở cửa
    # cho 1.545 dòng ma đi vào kho. Phiên thật đo được 30/30, trước mở cửa 0/30.
    if collected == 0 or priced < collected * MIN_PRICED_RATIO:            # (i)
        reasons.append(f"chỉ {priced}/{collected} mã có closePrice > 0 — không phải ngày giao dịch")
    if collected != total_count:                                           # (ii) đủ trang
        reasons.append(f"gom được {collected} mã, totalCount báo {total_count} — thiếu trang")
    if baseline_items is not None and total_count < baseline_items * (1 - DROP_RATIO):
        reasons.append(f"totalCount {total_count} sụt quá {DROP_RATIO:.0%} so mốc {baseline_items}")
    if collected > 0 and unmapped > collected * UNMAPPED_RATIO:            # (iii)
        reasons.append(f"{unmapped}/{collected} mã không ghép được security_id — quá {UNMAPPED_RATIO:.0%}")
    if collected > 0 and unknown > collected * UNMAPPED_RATIO:             # (iv) sàn lạ
        reasons.append(f"{unknown}/{collected} mã có comGroupCode lạ — quá {UNMAPPED_RATIO:.0%}")
    return GuardVerdict(ok=not reasons, reasons=tuple(reasons))
