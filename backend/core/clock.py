"""Đồng hồ dự án: mọi phép "hôm nay" tính theo giờ Việt Nam, không dựa vào TZ của tiến trình (spec lát 12 §5.6).

Bài học 2026-09-05: `recrawl_codes` lấy `current_date` phía Postgres (UTC) ⇒ hai test đỏ mỗi ngày
00:00–07:00 giờ VN. Container mặc định UTC nên `date.today` gọi trần rơi đúng bẫy đó mỗi đêm.
"""
from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

VN = ZoneInfo("Asia/Ho_Chi_Minh")


def now_vn() -> datetime:
    return datetime.now(VN)


def today_vn(now: datetime | None = None) -> date:
    """Ngày VN của `now` (mặc định: bây giờ). Từ chối `now` naive — naive là chính cái bẫy đang tránh."""
    if now is None:
        return now_vn().date()
    if now.tzinfo is None:
        raise ValueError("today_vn cần datetime có múi giờ")
    return now.astimezone(VN).date()
