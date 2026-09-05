"""Chuẩn hoá một series WiChart thành điểm ghi kho (spec §5.3). Thuần, không I/O.

Luật đo được (spec §2.1): epoch = 00:00 giờ VN · tháng neo ngày 1 · quý neo THÁNG CUỐI quý · năm bất
nhất (12-01 hoặc 01-01) · kho neo ĐẦU kỳ · điểm cuối tuần chỉ bỏ khi là chép lại của điểm liền trước.
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from etl.wichart_registry import BANDS, LEVEL_FLOOR, Series

VN = ZoneInfo("Asia/Ho_Chi_Minh")
QUARTER_END_TO_START = {3: 1, 6: 4, 9: 7, 12: 10}
NAME_PREFIX = 18


@dataclass(frozen=True)
class Point:
    domain: str
    code: str
    obs_date: date
    value: Decimal
    price_type: str | None


class SeriesError(Exception):
    def __init__(self, reason: str, msg: str):
        self.reason = reason            # 'shape' | 'freq' | 'band'
        super().__init__(msg)


def real_freq(epochs: list[int]) -> str | None:
    ts = sorted(set(epochs))
    if len(ts) < 3:
        return None
    med = statistics.median((b - a) / 86_400_000 for a, b in zip(ts, ts[1:]))
    return "d" if med <= 4 else "m" if med <= 45 else "q" if med <= 120 else "y"


def anchor(day: date, freq: str) -> date:
    if freq == "d":
        return day
    if freq == "m":
        return day.replace(day=1)
    if freq == "q":
        if day.month not in QUARTER_END_TO_START:
            raise SeriesError("shape", f"quý neo tháng {day.month}, không phải tháng cuối quý")
        return date(day.year, QUARTER_END_TO_START[day.month], 1)
    if freq == "y":
        return date(day.year, 1, 1)
    raise ValueError(f"freq lạ: {freq!r}")


def drop_weekend_carry(points: list[Point]) -> list[Point]:
    """Bỏ điểm T7/CN có giá trị bằng đúng điểm liền trước (theo thứ tự nguồn). Chép lại trong tuần giữ."""
    out: list[Point] = []
    prev: Point | None = None
    for p in points:
        if prev is not None and p.obs_date.weekday() >= 5 and p.value == prev.value:
            prev = p
            continue
        out.append(p)
        prev = p
    return out


def series_points(s: Series, api_series: list[dict]) -> list[Point]:
    if s.idx >= len(api_series):
        raise SeriesError("shape", f"{s.key}[{s.idx}] thiếu series (API trả {len(api_series)})")
    api = api_series[s.idx]
    api_name = (api.get("name") or "").strip()
    if "NAMEWRONG" not in s.flags:
        want = s.doc_name[:NAME_PREFIX]
        if not (api_name.startswith(want) or s.doc_name.startswith(api_name[:NAME_PREFIX])):
            raise SeriesError("shape", f"{s.key}[{s.idx}] tên series {api_name!r} ≠ {s.doc_name!r}")
    raw = [p for p in api.get("data") or []
           if isinstance(p, list) and len(p) == 2 and isinstance(p[1], (int, float)) and not isinstance(p[1], bool)]
    if not raw:
        raise SeriesError("shape", f"{s.key}[{s.idx}] không có điểm số")
    rf = real_freq([p[0] for p in raw])
    if rf is not None and rf != s.freq:
        raise SeriesError("freq", f"{s.key}[{s.idx}] tần suất thật {rf} ≠ {s.freq} khai ở §9")
    pts: list[Point] = []
    for epoch, v in sorted(raw, key=lambda p: p[0]):
        day = datetime.fromtimestamp(epoch / 1000, tz=VN).date()
        pts.append(Point(s.domain, s.code, anchor(day, s.freq), Decimal(str(v)) * s.scale, s.price_type))
    band = BANDS.get(s.unit)
    latest = pts[-1]
    if band and latest.value != 0:
        lo, hi = Decimal(str(band[0])), Decimal(str(band[1]))
        # dải cắt qua 0 (lo < 0, vd "USD", "%") so CÓ DẤU; dải không âm so theo TRỊ TUYỆT ĐỐI như cũ
        magnitude = latest.value if lo < 0 else abs(latest.value)
        if not (lo <= magnitude <= hi):
            raise SeriesError("band", f"{s.key}[{s.idx}] giá trị mới nhất {latest.value} ngoài dải {band} ({s.unit})")
    floor = LEVEL_FLOOR.get(s.code)
    if floor is not None and abs(latest.value) < floor:
        raise SeriesError("band", f"{s.key}[{s.idx}] giá trị mới nhất {latest.value} dưới sàn độ lớn {floor} ({s.unit})")
    if s.domain == "asset" and s.calendar == "trading_days":
        pts = drop_weekend_carry(pts)
    dedup: dict[date, Point] = {}
    for p in pts:                                   # hai điểm cùng ngày sau neo → giữ điểm sau (PK không nổ)
        dedup[p.obs_date] = p
    return list(dedup.values())
