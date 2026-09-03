"""Chốt chặn lượt hằng ngày — năm vế (spec §5.4). Module thuần.

KHÁC lát 1 và 2: không có vế "ngày giao dịch" (nguồn không đóng dấu ngày nghỉ — đo 2026-09-03)
và không có vế "thiếu trang" (trang 1 luôn trọn). Chế độ --backfill không qua guard này.
"""
from dataclasses import dataclass
from datetime import date

MISSING_RATIO = 0.02   # mã sai + mã hỏng. Dự kiến ~0; mã mới lên sàn chưa có ở FiinTrade là ca hợp lệ, vài mã
DROP_RATIO = 0.02      # số mã có dữ liệu sụt so mốc lượt success gần nhất


@dataclass(frozen=True)
class GuardVerdict:
    ok: bool
    reasons: tuple[str, ...]


def check(codes: int, with_data: int, invalid: int, failed: int, latest: date | None,
          today: date, baseline: dict | None) -> GuardVerdict:
    reasons: list[str] = []
    if with_data == 0:                                                              # (0)
        reasons.append("không mã nào có dữ liệu — nguồn hỏng")
    missing = invalid + failed
    if codes and missing > codes * MISSING_RATIO:                                   # (i)
        reasons.append(f"{missing}/{codes} mã không có dữ liệu ({invalid} mã sai, {failed} mã hỏng)"
                       f" — quá {MISSING_RATIO:.0%}")
    base_n = (baseline or {}).get("with_data")
    if base_n and with_data < base_n * (1 - DROP_RATIO):                            # (ii)
        reasons.append(f"chỉ {with_data} mã có dữ liệu — sụt quá {DROP_RATIO:.0%} so mốc {base_n}")
    if latest is not None and latest > today:                                       # (iii)
        reasons.append(f"ngày mới nhất {latest} ở tương lai (hôm nay {today})")
    base_latest = (baseline or {}).get("latest_trading_date")
    if latest is not None and base_latest and latest < date.fromisoformat(base_latest):   # (iv)
        reasons.append(f"ngày mới nhất {latest} lùi so mốc {base_latest}")
    return GuardVerdict(ok=not reasons, reasons=tuple(reasons))
