"""Chốt chặn một lượt `etl wichart` (spec §5.4). Thuần; đánh giá TRƯỚC khi mở giao dịch ghi."""
from __future__ import annotations

from dataclasses import dataclass, field

MIN_SAMPLE = 20
MAX_FAILED = 0.20
MAX_SHAPE = 0.05
MAX_BAND = 0.05


@dataclass
class Tally:
    keys_total: int = 0
    keys_failed: int = 0        # hỏng sau mọi lần thử
    keys_bad_shape: int = 0     # response không có chart.series — mọi series của key tính vào series_shape
    series_total: int = 0
    series_shape: int = 0       # thiếu series / tên lệch / quý neo sai / key bad_shape
    series_freq: int = 0        # tần suất thật ≠ khai — chỉ báo
    series_band: int = 0        # giá trị mới nhất ngoài dải đơn vị
    series_ok: int = 0


@dataclass
class Verdict:
    ok: bool
    reasons: list[str] = field(default_factory=list)


def check(t: Tally) -> Verdict:
    reasons: list[str] = []
    if t.keys_total >= MIN_SAMPLE:
        rate = t.keys_failed / t.keys_total
        if rate > MAX_FAILED:
            reasons.append(f"tỷ lệ key hỏng {rate:.1%} > {MAX_FAILED:.0%} ({t.keys_failed}/{t.keys_total}) — nguồn sự cố")
    if t.series_total >= MIN_SAMPLE:
        for n, cap, label in ((t.series_shape, MAX_SHAPE, "series sai hình dạng"),
                              (t.series_band, MAX_BAND, "series ngoài dải đơn vị")):
            rate = n / t.series_total
            if rate > cap:
                reasons.append(f"tỷ lệ {label} {rate:.1%} > {cap:.0%} ({n}/{t.series_total}) — nguồn đổi cấu trúc/thang")
    return Verdict(ok=not reasons, reasons=reasons)
