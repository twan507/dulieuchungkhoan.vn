"""Registry chung cho mọi nguồn ngoài WiChart (spec lát 7 §4.1): `Series` là 'mã của mình' + tham số cổng;
`load_registry` là ĐƯỜNG GHI DUY NHẤT vào 4 bảng registry, lọc theo `source` — lát 6 đã trả giá vì bộ lọc này
(điểm vào lát 7: gọi thiếu `source` là lượt FRED xoá ánh xạ WiChart)."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

import sqlalchemy as sa

from etl.series_store import Resolved


@dataclass(frozen=True)
class Series:
    source: str
    external_key: str
    domain: str                      # 'macro' | 'asset'
    code: str
    name_vi: str
    unit: str
    freq: str                        # 'd' | 'm'
    external_sub: str = ""
    scale: Decimal = Decimal(1)
    role: str = "data"
    region: str = "global"
    asset_class: str | None = None
    quote_currency: str | None = None
    price_type: str | None = None    # None cho OHLC
    calendar: str | None = None
    band: tuple[Decimal, Decimal] | None = None
    max_lag_days: int = 6
    shape: str = "point"             # 'point' | 'ohlc'
    extra: dict = field(default_factory=dict)

    @property
    def meta(self) -> dict:
        band = [str(self.band[0]), str(self.band[1])] if self.band else None
        return {"freq": self.freq, "max_lag_days": self.max_lag_days, "band": band, **self.extra}


@dataclass(frozen=True)
class Point:
    domain: str
    code: str
    obs_date: date
    value: Decimal
    price_type: str | None


@dataclass(frozen=True)
class Bar:
    code: str
    obs_date: date
    open: Decimal | None
    high: Decimal | None
    low: Decimal | None
    close: Decimal
    close_adj: Decimal | None
    volume: Decimal | None


class SeriesError(Exception):
    def __init__(self, reason: str, msg: str):
        self.reason = reason         # 'shape' | 'band' | 'stale'
        super().__init__(msg)


def load_registry(conn, series, source: str) -> tuple[dict[str, Resolved], dict]:
    """Upsert indicator/asset theo `code` (không bao giờ xoá), upsert dòng ánh xạ theo (source, key, sub);
    dòng ánh xạ của `source` vắng mặt trong `series` bị xoá TRƯỚC vòng INSERT (ruling I1 lát 6)."""
    present_m = [f"{s.external_key}/{s.external_sub}" for s in series if s.domain == "macro"]
    present_a = [f"{s.external_key}/{s.external_sub}" for s in series if s.domain == "asset"]
    removed = conn.execute(sa.text(
        "DELETE FROM macro.indicator_source WHERE source = :src"
        " AND NOT (external_key || '/' || external_sub = ANY(:present))"), {"src": source, "present": present_m}).rowcount
    removed += conn.execute(sa.text(
        "DELETE FROM asset.asset_external_id WHERE source = :src"
        " AND NOT (external_code || '/' || external_sub = ANY(:present))"), {"src": source, "present": present_a}).rowcount
    resolved: dict[str, Resolved] = {}
    for s in series:
        meta = json.dumps(s.meta, ensure_ascii=False)
        if s.domain == "macro":
            iid = conn.execute(sa.text(
                "INSERT INTO macro.indicator (code, name_vi, unit, freq, region, role)"
                " VALUES (:code, :name, :unit, :freq, :region, :role)"
                " ON CONFLICT (code) DO UPDATE SET name_vi = excluded.name_vi, unit = excluded.unit,"
                " freq = excluded.freq, role = excluded.role, region = excluded.region RETURNING indicator_id"),
                {"code": s.code, "name": s.name_vi, "unit": s.unit, "freq": s.freq, "region": s.region, "role": s.role}).scalar_one()
            conn.execute(sa.text(
                "INSERT INTO macro.indicator_source (indicator_id, source, external_key, external_sub, scale, active, meta)"
                " VALUES (:iid, :src, :key, :sub, :scale, true, cast(:meta AS jsonb))"
                " ON CONFLICT (source, external_key, external_sub) DO UPDATE SET indicator_id = excluded.indicator_id,"
                " scale = excluded.scale, active = true, meta = excluded.meta"),
                {"iid": iid, "src": source, "key": s.external_key, "sub": s.external_sub, "scale": s.scale, "meta": meta})
            resolved[s.code] = Resolved("macro", iid, None)
        else:
            aid = conn.execute(sa.text(
                "INSERT INTO asset.asset (code, name_vi, asset_class, quote_currency, unit, calendar, region)"
                " VALUES (:code, :name, :cls, :ccy, :unit, :cal, :region)"
                " ON CONFLICT (code) DO UPDATE SET name_vi = excluded.name_vi, asset_class = excluded.asset_class,"
                " quote_currency = excluded.quote_currency, unit = excluded.unit, calendar = excluded.calendar,"
                " region = excluded.region RETURNING asset_id"),
                {"code": s.code, "name": s.name_vi, "cls": s.asset_class, "ccy": s.quote_currency, "unit": s.unit,
                 "cal": s.calendar or "trading_days", "region": s.region}).scalar_one()
            conn.execute(sa.text(
                "INSERT INTO asset.asset_external_id (asset_id, source, external_code, external_sub, scale, active, price_type, meta)"
                " VALUES (:aid, :src, :key, :sub, :scale, true, :pt, cast(:meta AS jsonb))"
                " ON CONFLICT (source, external_code, external_sub) DO UPDATE SET asset_id = excluded.asset_id,"
                " scale = excluded.scale, active = true, price_type = excluded.price_type, meta = excluded.meta"),
                {"aid": aid, "src": source, "key": s.external_key, "sub": s.external_sub, "scale": s.scale,
                 "pt": s.price_type, "meta": meta})
            resolved[s.code] = Resolved("asset", aid, s.price_type)
    return resolved, {"macro": len(present_m), "asset": len(present_a), "removed": removed}
