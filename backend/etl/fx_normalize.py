"""Một cặp từ document `rates` (spec lát 7 §5.3). Giá trị = số quote trên 1 USD, đúng chiều Frankfurter."""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from etl.registry import Point, SeriesError


def series_points(s, doc, now) -> list[Point]:
    rates = doc.get("rates") if isinstance(doc, dict) else None
    if not isinstance(rates, dict) or not rates:
        raise SeriesError("shape", f"{s.external_key}: không có rates")
    days = sorted(rates)
    if s.external_key not in rates[days[-1]]:
        raise SeriesError("shape", f"{s.external_key}: thiếu ở ngày cuối {days[-1]}")
    pts = [Point("asset", s.code, date.fromisoformat(d), Decimal(str(rates[d][s.external_key])), s.price_type)
           for d in days if s.external_key in rates[d]]
    if date.fromisoformat(days[-1]) < now.date() - timedelta(days=s.max_lag_days):
        raise SeriesError("stale", f"{s.external_key}: ngày cuối {days[-1]} quá {s.max_lag_days} ngày")
    lo, hi = s.band
    if not (lo <= pts[-1].value <= hi):
        raise SeriesError("band", f"{s.external_key}: {pts[-1].value} ngoài dải ({lo}, {hi})")
    return pts
