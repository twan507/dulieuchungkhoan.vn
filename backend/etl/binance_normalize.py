"""Nến ngày Binance → Bar: obs_date = ngày UTC của thời điểm MỞ (seam 4 bước 5), bỏ nến closeTime > now."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from etl.registry import Bar, SeriesError


def bars(s, doc, now) -> list[Bar]:
    out: dict = {}
    for k in doc:
        if not isinstance(k, list) or len(k) != 12:
            raise SeriesError("shape", f"{s.external_key}: nến không có 12 phần tử")
        if k[6] / 1000 > now.timestamp():
            continue                                                   # nến đang chạy — đo: limit=40 trả cả hôm nay
        d = datetime.fromtimestamp(k[0] / 1000, timezone.utc).date()
        out[d] = Bar(s.code, d, Decimal(k[1]), Decimal(k[2]), Decimal(k[3]), Decimal(k[4]), None, Decimal(k[5]))
    if not out:
        raise SeriesError("stale", f"{s.external_key}: không có nến đã đóng")
    last_day = max(out)
    if last_day < now.date() - timedelta(days=s.max_lag_days):
        raise SeriesError("stale", f"{s.external_key}: nến đóng cuối {last_day} quá {s.max_lag_days} ngày")
    lo, hi = s.band
    if not (lo <= out[last_day].close <= hi):
        raise SeriesError("band", f"{s.external_key}: close {out[last_day].close} ngoài dải ({lo}, {hi})")
    return [out[k] for k in sorted(out)]
