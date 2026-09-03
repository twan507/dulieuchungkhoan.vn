"""Chốt chặn cho job events — bốn vế, vế nào hỏng cũng từ chối (spec §5.4).

Module thuần: đầu vào là số trần để test không cần database.

KHÁC lát 1 ở một điểm lớn: KHÔNG có vế "ngày giao dịch". Lịch sự kiện không phụ
thuộc phiên — ngày lễ nguồn vẫn trả đủ kho, không có dòng ma nào để đẻ ra.
"""
from dataclasses import dataclass

DROP_RATIO = 0.02
DUP_RATIO = 0.005
MAX_NEW_ISSUERS = 20
# Vùng dữ liệu thật (đo 2026-09-03): lượt backfill đầu tạo 517 issuer tối thiểu, còn lượt
# hằng ngày phải gần 0. Ngưỡng 20 nằm giữa hai vùng đó. Đây là chốt chặn của chính sách F7:
# nó biến "âm thầm đẻ issuer" thành "đẻ quá tay thì dừng và gọi người".


@dataclass(frozen=True)
class GuardVerdict:
    ok: bool
    reasons: tuple[str, ...]
    families: tuple[str, ...]        # họ bị nghi — quyết định lưu mẫu nào làm bằng chứng


def check(counts: dict[str, int], collected: dict[str, int], baseline: dict[str, int] | None,
          issuers_new: int, dup_conflicts: int, rows_kept: int,
          *, accept_new: bool = False) -> GuardVerdict:
    reasons: list[str] = []
    families: list[str] = []
    for fam in sorted(counts):
        total, got = counts[fam], collected.get(fam, 0)
        if got != total:                                                        # (i)
            reasons.append(f"{fam}: gom được {got} bản ghi, totalCount báo {total} — thiếu trang")
            families.append(fam)
        base = (baseline or {}).get(fam)
        if base is not None and total < base * (1 - DROP_RATIO):                # (ii)
            reasons.append(f"{fam}: totalCount {total} sụt quá {DROP_RATIO:.0%} so mốc {base}")
            families.append(fam)
    if issuers_new > MAX_NEW_ISSUERS and not accept_new:                        # (iii)
        reasons.append(f"tạo mới {issuers_new} issuer tối thiểu — quá {MAX_NEW_ISSUERS};"
                       " chạy lại với --accept-new nếu con số này đúng")
    fetched = rows_kept + dup_conflicts
    if fetched > 0 and dup_conflicts > fetched * DUP_RATIO:                     # (iv)
        reasons.append(f"{dup_conflicts}/{fetched} bản ghi đụng khoá tự nhiên"
                       f" — quá {DUP_RATIO:.1%}")
    return GuardVerdict(ok=not reasons, reasons=tuple(reasons),
                        families=tuple(dict.fromkeys(families)))
