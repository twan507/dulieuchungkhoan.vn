"""Chuẩn hoá một series FRED (spec lát 7 §5.3). Thuần. `"."` = thiếu ⇒ không dòng (bước 4 schema)."""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from etl.registry import Point, SeriesError


def series_points(s, doc, now) -> list[Point]:
    obs = doc.get("observations") if isinstance(doc, dict) else None
    if not isinstance(obs, list) or not obs:
        raise SeriesError("shape", f"{s.external_key}: không có observations")
    pts: list[Point] = []
    for o in obs:
        v = o.get("value")
        if v is None or v == ".":
            continue
        try:
            pts.append(Point(s.domain, s.code, date.fromisoformat(o["date"]), Decimal(v) * s.scale, s.price_type))
        except (KeyError, ValueError, InvalidOperation) as e:
            raise SeriesError("shape", f"{s.external_key}: điểm hỏng {o!r}") from e
    if not pts:
        raise SeriesError("shape", f"{s.external_key}: mọi điểm đều '.'")
    latest = max(pts, key=lambda p: p.obs_date)
    if latest.obs_date < now.date() - timedelta(days=s.max_lag_days):
        raise SeriesError("stale", f"{s.external_key}: điểm cuối {latest.obs_date} quá {s.max_lag_days} ngày")
    lo, hi = s.band
    if not (lo <= latest.value <= hi):
        raise SeriesError("band", f"{s.external_key}: {latest.value} ngoài dải ({lo}, {hi})")
    return pts
