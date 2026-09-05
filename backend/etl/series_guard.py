"""Chốt chặn chung (spec lát 7 §4.5, §5.4). Thuần; đánh giá TRƯỚC khi mở giao dịch ghi.

Hai chế độ: `all_or_nothing` cho nguồn ≤ 20 series (FRED · ECB · LBMA · Binance) — một series hỏng là từ chối cả lượt;
`ratio` cho nguồn ≥ MIN_SAMPLE (Yahoo) — khuôn tỷ lệ của lát 6, thêm trục `stale`."""
from __future__ import annotations

from dataclasses import dataclass, field

MIN_SAMPLE = 20
MAX_FAILED = 0.20
MAX_SHAPE = 0.05
MAX_BAND = 0.05
MAX_STALE = 0.20


@dataclass
class Tally:
    total: int = 0
    failed: int = 0        # fetch hỏng sau mọi lần thử
    shape: int = 0         # response sai hình dạng / cổng lược đồ
    band: int = 0          # điểm mới nhất ngoài dải
    stale: int = 0         # cổng độ tươi
    ok: int = 0
    details: list[str] = field(default_factory=list)


@dataclass
class Verdict:
    ok: bool
    reasons: list[str] = field(default_factory=list)


def check(t: Tally, mode: str) -> Verdict:
    bad = t.failed + t.shape + t.band + t.stale
    if mode == "all_or_nothing":
        if bad:
            return Verdict(False, [f"{bad}/{t.total} series hỏng — nguồn ≤ 20 series: tất cả hoặc không gì; "
                                   + "; ".join(t.details[:10])])
        return Verdict(True)
    if mode != "ratio":
        raise ValueError(f"mode lạ: {mode!r}")
    reasons: list[str] = []
    if t.total >= MIN_SAMPLE:
        for n, cap, label in ((t.failed, MAX_FAILED, "series fetch hỏng"), (t.shape, MAX_SHAPE, "series sai hình dạng"),
                              (t.band, MAX_BAND, "series ngoài dải"), (t.stale, MAX_STALE, "series không tươi")):
            rate = n / t.total
            if rate > cap:
                reasons.append(f"tỷ lệ {label} {rate:.1%} > {cap:.0%} ({n}/{t.total})")
    return Verdict(ok=not reasons, reasons=reasons)
