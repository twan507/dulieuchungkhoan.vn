"""Một cột tiền tệ (theo `external_sub`) từ mảng {d, v:[USD, GBP, EUR]} — đo 2026-09-05. `null` = tiền tệ chưa có."""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from etl.registry import Point, SeriesError


def series_points(s, doc, now) -> list[Point]:
    idx = int(s.external_sub)
    pts: list[Point] = []
    prev: date | None = None
    for row in doc:
        v = row.get("v")
        if not isinstance(v, list) or len(v) != 3:
            raise SeriesError("shape", f"{s.external_key}: v không phải mảng 3 phần tử tại {row.get('d')}")
        d = date.fromisoformat(row["d"])
        if prev is not None and d <= prev:
            raise SeriesError("shape", f"{s.external_key}: ngày không tăng tại {d}")
        prev = d
        if v[idx] is None:
            continue
        pts.append(Point("asset", s.code, d, Decimal(str(v[idx])), s.price_type))
    if not pts:
        raise SeriesError("shape", f"{s.external_key}: không có điểm")
    if pts[-1].obs_date < now.date() - timedelta(days=s.max_lag_days):
        raise SeriesError("stale", f"{s.external_key}: điểm cuối {pts[-1].obs_date} quá {s.max_lag_days} ngày")
    lo, hi = s.band
    if not (lo <= pts[-1].value <= hi):
        raise SeriesError("band", f"{s.external_key}: {pts[-1].value} ngoài dải ({lo}, {hi})")
    return pts
