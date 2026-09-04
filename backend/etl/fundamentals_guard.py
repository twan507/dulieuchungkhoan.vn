"""Năm chốt chặn của một lượt `etl fundamentals` (spec §5.5). Thuần, đánh giá TRƯỚC commit.

Khác lát 4 ở chốt (iv): payload RỖNG trên mã từng có dữ liệu. Rỗng không bao giờ được xoá dữ liệu
cũ (apply bỏ qua và không tiến sổ kiểm), nhưng rỗng hàng loạt là nguồn hỏng — dừng lượt.
"""
from __future__ import annotations

from dataclasses import dataclass, field

MIN_SAMPLE = 20
MAX_FLOOR_CHANGED = 0.20
MAX_FAILED = 0.20
MAX_BAD_SHAPE = 0.05
MAX_EMPTY = 0.05


@dataclass
class Tally:
    attempted: int = 0          # số (mã × kind) định gọi trong lượt
    failed: int = 0             # hỏng sau mọi lần thử ⇒ CHƯA KIỂM
    bad_shape: int = 0          # sai hình dạng (fetch) hoặc sai hợp đồng bản ghi (normalize)
    empty: int = 0              # rỗng trên mã từng có dữ liệu ⇒ CHƯA KIỂM, không xoá gì
    checked: int = 0            # số bản ghi apply() đã ghi sổ kiểm
    first: int = 0              # lần kiểm đầu của (mã, kind)
    floor_compared: int = 0     # mã quét sàn CÓ hash cũ để so
    changed_floor: int = 0      # trong số đó, nội dung đổi — LỖ của lịch sự kiện
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
                           f" ({t.changed_floor}/{t.floor_compared}) — nguồn đổi cách tính,"
                           f" hoặc mùa báo cáo mà lịch sự kiện sót (đọc README trước khi nới)")
    if t.attempted >= MIN_SAMPLE:
        for n, cap, label in ((t.failed, MAX_FAILED, "lời gọi hỏng"),
                              (t.bad_shape, MAX_BAD_SHAPE, "sai hình dạng"),
                              (t.empty, MAX_EMPTY, "rỗng trên mã từng có dữ liệu")):
            rate = n / t.attempted
            if rate > cap:
                reasons.append(f"tỷ lệ {label} {rate:.1%} > {cap:.0%} ({n}/{t.attempted}) — nguồn đang sự cố")
    return Verdict(ok=not reasons, reasons=reasons)
