"""Bốn chốt chặn của một lượt `etl snapshot` (spec §5.5). Thuần, đánh giá TRƯỚC commit.

Chốt (i) là cái đắt nhất: nó bắt 'tập trắng sai' và 'nguồn đổi cách tính' — hai thứ trông
y hệt 'cả sàn cùng công bố'. Mọi chốt đều có ngưỡng mẫu tối thiểu, vì lượt --codes vài mã
hoặc lượt cold start sẽ tự vi phạm ngưỡng phần trăm nếu không có nó (§4.4.4).
"""
from __future__ import annotations

from dataclasses import dataclass, field

MIN_SAMPLE = 20
MAX_FLOOR_CHANGED = 0.20
MAX_FAILED = 0.20
MAX_BAD_SHAPE = 0.05


@dataclass
class Tally:
    attempted: int = 0          # số (mã × kind) định gọi trong lượt
    failed: int = 0             # hỏng sau mọi lần thử ⇒ để CHƯA KIỂM
    bad_shape: int = 0          # response hợp lệ nhưng thiếu khoá gốc
    first: int = 0              # lần kiểm đầu tiên của (mã, kind) — chưa có hash cũ để so
    floor_compared: int = 0     # mã quét sàn CÓ hash cũ để so
    changed_floor: int = 0      # trong số đó, nội dung đổi — đây là LỖ của lịch sự kiện
    changed_event: int = 0
    unchanged: int = 0


@dataclass
class Verdict:
    ok: bool
    reasons: list[str] = field(default_factory=list)


def check(t: Tally) -> Verdict:
    reasons: list[str] = []
    if t.floor_compared >= MIN_SAMPLE:
        rate = t.changed_floor / t.floor_compared
        if rate > MAX_FLOOR_CHANGED:
            reasons.append(f"tỷ lệ đổi của nhóm quét sàn {rate:.1%} > {MAX_FLOOR_CHANGED:.0%}"
                           f" ({t.changed_floor}/{t.floor_compared}) — nghi tập trắng sai"
                           f" hoặc nguồn đổi cách tính")
    if t.attempted >= MIN_SAMPLE:
        rate = t.failed / t.attempted
        if rate > MAX_FAILED:
            reasons.append(f"tỷ lệ lời gọi hỏng {rate:.1%} > {MAX_FAILED:.0%}"
                           f" ({t.failed}/{t.attempted}) — nguồn đang sự cố")
        rate = t.bad_shape / t.attempted
        if rate > MAX_BAD_SHAPE:
            reasons.append(f"tỷ lệ sai hình dạng {rate:.1%} > {MAX_BAD_SHAPE:.0%}"
                           f" ({t.bad_shape}/{t.attempted}) — nguồn đổi hình dạng response")
    return Verdict(ok=not reasons, reasons=reasons)
