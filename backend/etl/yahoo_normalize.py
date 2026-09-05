"""Nến ngày Yahoo → Bar (spec lát 7 §5.3). Ba cổng bắt buộc + bỏ nến chưa đóng + ngày theo múi giờ SÀN."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

from etl.registry import Bar, SeriesError

EPOCH0 = datetime(1970, 1, 1, tzinfo=timezone.utc)   # fromtimestamp không nhận epoch âm trên Windows


def _dec(x):
    return None if x is None else Decimal(str(x))


def _utc(ts: int) -> datetime:
    return EPOCH0 + timedelta(seconds=ts)


def bars(s, doc, now) -> list[Bar]:
    try:
        res = doc["chart"]["result"][0]
        meta = res["meta"]
    except (KeyError, IndexError, TypeError) as e:
        raise SeriesError("shape", f"{s.external_key}: không có chart.result[0].meta") from e
    if meta.get("dataGranularity") != "1d":
        raise SeriesError("shape", f"{s.external_key}: dataGranularity {meta.get('dataGranularity')!r} ≠ '1d'")
    if "ALTSYMBOL" in (meta.get("instrumentType"), meta.get("quoteType")):     # quoteType không còn từ 2026-09-05
        raise SeriesError("shape", f"{s.external_key}: ALTSYMBOL — mã đã ngừng")
    ccy = meta.get("currency")
    if ccy and ccy != s.quote_currency:
        raise SeriesError("shape", f"{s.external_key}: currency {ccy!r} ≠ registry {s.quote_currency!r}")
    ts = res.get("timestamp") or []
    rmt_raw = meta.get("regularMarketTime")
    if not isinstance(rmt_raw, (int, float)):
        raise SeriesError("shape", f"{s.external_key}: thiếu/sai kiểu meta.regularMarketTime")
    rmt = _utc(rmt_raw)
    if not ts or rmt < now - timedelta(days=s.max_lag_days):
        raise SeriesError("stale", f"{s.external_key}: regularMarketTime {rmt.date()} / {len(ts)} nến — quá {s.max_lag_days} ngày")
    tzname = meta.get("exchangeTimezoneName")
    if not isinstance(tzname, str):
        raise SeriesError("shape", f"{s.external_key}: thiếu/sai kiểu meta.exchangeTimezoneName")
    tz = ZoneInfo(tzname)
    ind = res.get("indicators")
    quote_list = ind.get("quote") if isinstance(ind, dict) else None
    if not isinstance(quote_list, list) or not quote_list or not isinstance(quote_list[0], dict) or "close" not in quote_list[0]:
        raise SeriesError("shape", f"{s.external_key}: thiếu indicators.quote[0].close")
    q = quote_list[0]
    adj = (ind.get("adjclose") or [{}])[0].get("adjclose") or [None] * len(ts)
    reg = (meta.get("currentTradingPeriod") or {}).get("regular") or {}
    cut = len(ts) - 1 if reg and now.timestamp() < reg["end"] and ts[-1] >= reg["start"] else None
    out: dict = {}
    for i, t in enumerate(ts):
        if i == cut or q["close"][i] is None:
            continue
        d = _utc(t).astimezone(tz).date()
        out[d] = Bar(s.code, d, _dec(q["open"][i]), _dec(q["high"][i]), _dec(q["low"][i]), _dec(q["close"][i]),
                     _dec(adj[i]), _dec(q["volume"][i]))
    if not out:
        return []
    last = out[max(out)]
    lo, hi = s.band
    if not (lo <= last.close <= hi):
        raise SeriesError("band", f"{s.external_key}: close {last.close} ngoài dải ({lo}, {hi})")
    return [out[k] for k in sorted(out)]
