"""Ghi kho cho `etl wichart` (spec §5.5). SQL thuần; hai miền trong cùng giao dịch của caller."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

import sqlalchemy as sa

from etl.wichart_guard import Verdict
from etl.wichart_normalize import Point
from etl.wichart_registry import SOURCE, Series

JOB = "macro.wichart"
DOMAINS = ("macro.indicator", "asset")
CHUNK = 5000
# Đứt gãy GDP giá so sánh: nguồn nhảy tại kỳ nguồn neo "2026-03" = Q1/2026; kho neo đầu kỳ ⇒ 2026-01-01
# là điểm ĐẦU TIÊN thuộc nền mới. Hệ số = TB hai ước lượng độc lập (wichart.md Bẫy 6). Chủ dự án chốt
# 2026-09-05: không cần verified_by, ghi ngày.
GDP_BREAK = dict(code="vn.gdp.real", break_date=date(2026, 1, 1), factor=Decimal("1.6005"),
                 reason="Đổi năm gốc giá so sánh; trung bình hai ước lượng độc lập 1.6032 / 1.5978 (wichart.md Bẫy 6)",
                 verified_at=date(2026, 9, 5))


@dataclass(frozen=True)
class Resolved:
    domain: str
    row_id: int
    price_type: str | None


@dataclass
class Written:
    inserted: int = 0
    changed: int = 0


def load_registry(conn, series: list[Series]) -> tuple[dict[str, Resolved], dict]:
    # Dòng ánh xạ vắng mặt trong registry hiện tại bị XOÁ trước vòng INSERT (ruling I1): nếu chỉ lật
    # active=false, một mã đổi external_sub giữa hai lượt sẽ để lại dòng cũ trỏ cùng indicator_id và vỡ
    # UNIQUE (indicator_id, source) khi INSERT dòng mới. indicator_id/asset_id không bao giờ bị xoá ở đây
    # nên observation không mất chủ. Cột active giữ lại cho lát 12 (series chết ở nguồn mà vẫn trong registry).
    present_m = [f"{s.key}/{s.external_sub}" for s in series if s.domain == "macro"]
    present_a = [f"{s.key}/{s.external_sub}" for s in series if s.domain == "asset"]
    removed = conn.execute(sa.text(
        "DELETE FROM macro.indicator_source WHERE source = :src"
        " AND NOT (external_key || '/' || external_sub = ANY(:present))"), {"src": SOURCE, "present": present_m}).rowcount
    removed += conn.execute(sa.text(
        "DELETE FROM asset.asset_external_id WHERE source = :src"
        " AND NOT (external_code || '/' || external_sub = ANY(:present))"), {"src": SOURCE, "present": present_a}).rowcount
    resolved: dict[str, Resolved] = {}
    for s in series:
        meta = json.dumps({"tier_flags": list(s.flags), "freq": s.freq, "group": s.group}, ensure_ascii=False)
        if s.domain == "macro":
            iid = conn.execute(sa.text(
                "INSERT INTO macro.indicator (code, name_vi, unit, freq, region, role)"
                " VALUES (:code, :name, :unit, :freq, :region, :role)"
                " ON CONFLICT (code) DO UPDATE SET name_vi = excluded.name_vi, unit = excluded.unit,"
                " freq = excluded.freq, role = excluded.role RETURNING indicator_id"),
                {"code": s.code, "name": s.name_vi, "unit": s.unit, "freq": s.freq, "region": s.region, "role": s.role}).scalar_one()
            conn.execute(sa.text(
                "INSERT INTO macro.indicator_source (indicator_id, source, external_key, external_sub, scale, active, meta)"
                " VALUES (:iid, :src, :key, :sub, :scale, true, cast(:meta AS jsonb))"
                " ON CONFLICT (source, external_key, external_sub) DO UPDATE SET indicator_id = excluded.indicator_id,"
                " scale = excluded.scale, active = true, meta = excluded.meta"),
                {"iid": iid, "src": SOURCE, "key": s.key, "sub": s.external_sub, "scale": s.scale, "meta": meta})
            resolved[s.code] = Resolved("macro", iid, None)
        else:
            aid = conn.execute(sa.text(
                "INSERT INTO asset.asset (code, name_vi, asset_class, quote_currency, unit, calendar, region)"
                " VALUES (:code, :name, :cls, :ccy, :unit, :cal, :region)"
                " ON CONFLICT (code) DO UPDATE SET name_vi = excluded.name_vi, asset_class = excluded.asset_class,"
                " quote_currency = excluded.quote_currency, unit = excluded.unit, calendar = excluded.calendar,"
                " region = excluded.region RETURNING asset_id"),
                {"code": s.code, "name": s.name_vi, "cls": s.asset_class, "ccy": s.quote_currency, "unit": s.unit,
                 "cal": s.calendar, "region": s.region}).scalar_one()
            conn.execute(sa.text(
                "INSERT INTO asset.asset_external_id (asset_id, source, external_code, external_sub, scale, active, price_type, meta)"
                " VALUES (:aid, :src, :key, :sub, :scale, true, :pt, cast(:meta AS jsonb))"
                " ON CONFLICT (source, external_code, external_sub) DO UPDATE SET asset_id = excluded.asset_id,"
                " scale = excluded.scale, active = true, price_type = excluded.price_type, meta = excluded.meta"),
                {"aid": aid, "src": SOURCE, "key": s.key, "sub": s.external_sub, "scale": s.scale, "pt": s.price_type, "meta": meta})
            resolved[s.code] = Resolved("asset", aid, s.price_type)
    return resolved, {"macro": len(present_m), "asset": len(present_a), "removed": removed}


_UPSERT_MACRO = sa.text(
    "INSERT INTO macro.observation (indicator_id, obs_date, value)"
    " SELECT * FROM unnest(cast(:ids AS bigint[]), cast(:dates AS date[]), cast(:vals AS numeric[]))"
    " ON CONFLICT (indicator_id, obs_date) DO UPDATE SET value = excluded.value, ingested_at = clock_timestamp()"
    " WHERE macro.observation.value IS DISTINCT FROM excluded.value"
    " RETURNING (xmax = 0) AS inserted")
_UPSERT_ASSET = sa.text(
    "INSERT INTO asset.price_daily (asset_id, obs_date, price_type, value)"
    " SELECT * FROM unnest(cast(:ids AS bigint[]), cast(:dates AS date[]), cast(:types AS text[]), cast(:vals AS numeric[]))"
    " ON CONFLICT (asset_id, obs_date, price_type) DO UPDATE SET value = excluded.value, ingested_at = clock_timestamp()"
    " WHERE asset.price_daily.value IS DISTINCT FROM excluded.value"
    " RETURNING (xmax = 0) AS inserted")


def apply(conn, points: list[Point], resolved: dict[str, Resolved]) -> Written:
    w = Written()
    macro = [p for p in points if p.domain == "macro"]
    asset = [p for p in points if p.domain == "asset"]
    for start in range(0, len(macro), CHUNK):
        chunk = macro[start:start + CHUNK]
        flags = conn.execute(_UPSERT_MACRO, {"ids": [resolved[p.code].row_id for p in chunk],
                                             "dates": [p.obs_date for p in chunk],
                                             "vals": [p.value for p in chunk]}).scalars().all()
        w.inserted += sum(1 for f in flags if f)
        w.changed += sum(1 for f in flags if not f)
    for start in range(0, len(asset), CHUNK):
        chunk = asset[start:start + CHUNK]
        flags = conn.execute(_UPSERT_ASSET, {"ids": [resolved[p.code].row_id for p in chunk],
                                             "dates": [p.obs_date for p in chunk],
                                             "types": [p.price_type for p in chunk],
                                             "vals": [p.value for p in chunk]}).scalars().all()
        w.inserted += sum(1 for f in flags if f)
        w.changed += sum(1 for f in flags if not f)
    return w


def seed_series_break(conn) -> None:
    conn.execute(sa.text(
        "INSERT INTO macro.series_break (indicator_id, break_date, factor, reason, verified_at)"
        " SELECT indicator_id, :d, :f, :r, :v FROM macro.indicator WHERE code = :code"
        " ON CONFLICT (indicator_id, break_date) DO UPDATE SET factor = excluded.factor, reason = excluded.reason,"
        " verified_at = excluded.verified_at"),
        {"code": GDP_BREAK["code"], "d": GDP_BREAK["break_date"], "f": GDP_BREAK["factor"],
         "r": GDP_BREAK["reason"], "v": GDP_BREAK["verified_at"]})


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def store_payload_if_changed(conn, key: str, text: str, run_id: int) -> bool:
    ek = f"wichart:{key}"
    h = _hash(text)
    last = conn.execute(sa.text(
        "SELECT meta->>'hash' FROM staging.raw_payload WHERE source = :src AND endpoint_key = :ek"
        " ORDER BY payload_id DESC LIMIT 1"), {"src": SOURCE, "ek": ek}).scalar()
    if last == h:
        return False
    conn.execute(sa.text(
        "INSERT INTO staging.raw_payload (source, endpoint_key, content_type, payload, meta)"
        " VALUES (:src, :ek, 'json', cast(:p AS jsonb), cast(:m AS jsonb))"),
        {"src": SOURCE, "ek": ek, "p": text, "m": json.dumps({"hash": h, "run_id": run_id, "bytes": len(text)})})
    return True


def store_refusal_evidence(engine, texts: dict[str, str], run_id: int, verdict: Verdict) -> None:
    """Bằng chứng ở giao dịch RIÊNG — lượt chính không ghi gì."""
    meta = json.dumps({"run_id": run_id, "reasons": verdict.reasons, "refused": True}, ensure_ascii=False)
    with engine.begin() as conn:
        for key, text in texts.items():
            conn.execute(sa.text(
                "INSERT INTO staging.raw_payload (source, endpoint_key, content_type, payload, meta)"
                " VALUES (:src, :ek, 'json', cast(:p AS jsonb), cast(:m AS jsonb))"),
                {"src": SOURCE, "ek": f"wichart:{key}", "p": text, "m": meta})


def upsert_domain_state(engine, watermark: str) -> None:
    with engine.begin() as conn:
        for domain in DOMAINS:
            conn.execute(sa.text(
                "INSERT INTO ops.data_domain_state (domain, source, status, last_success_at, watermark)"
                " VALUES (:d, :s, 'active', now(), :w)"
                " ON CONFLICT (domain, source) DO UPDATE SET last_success_at = now(), watermark = :w, status = 'active'"),
                {"d": domain, "s": SOURCE, "w": watermark})
