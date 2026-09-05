"""Đường ghi chung cho mọi job series (spec lát 7 §5.5): UPSERT chỉ-khi-đổi, đếm inserted/changed qua xmax,
mẫu dòng đổi (§4.6) thay cho lưu body mỗi lần hash đổi. Trích từ `wichart_store` lát 6 khi lát 7 cần lần thứ hai."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

import sqlalchemy as sa

CHUNK = 5000
SAMPLE_CAP = 50


@dataclass(frozen=True)
class Resolved:
    domain: str
    row_id: int
    price_type: str | None


@dataclass
class Written:
    inserted: int = 0
    changed: int = 0
    changes_sample: list = field(default_factory=list)   # [(code, iso_date, old, new)] ≤ SAMPLE_CAP


_UPSERT_MACRO = sa.text(
    "INSERT INTO macro.observation (indicator_id, obs_date, value)"
    " SELECT * FROM unnest(cast(:ids AS bigint[]), cast(:dates AS date[]), cast(:vals AS numeric[]))"
    " ON CONFLICT (indicator_id, obs_date) DO UPDATE SET value = excluded.value, ingested_at = clock_timestamp()"
    " WHERE macro.observation.value IS DISTINCT FROM excluded.value"
    " RETURNING (xmax = 0) AS inserted, indicator_id AS rid, obs_date")
_UPSERT_ASSET = sa.text(
    "INSERT INTO asset.price_daily (asset_id, obs_date, price_type, value)"
    " SELECT * FROM unnest(cast(:ids AS bigint[]), cast(:dates AS date[]), cast(:types AS text[]), cast(:vals AS numeric[]))"
    " ON CONFLICT (asset_id, obs_date, price_type) DO UPDATE SET value = excluded.value, ingested_at = clock_timestamp()"
    " WHERE asset.price_daily.value IS DISTINCT FROM excluded.value"
    " RETURNING (xmax = 0) AS inserted, asset_id AS rid, obs_date")
_OLD_MACRO = sa.text(
    "SELECT o.indicator_id, o.obs_date, o.value FROM macro.observation o"
    " JOIN unnest(cast(:ids AS bigint[]), cast(:dates AS date[])) AS u(id, d) ON u.id = o.indicator_id AND u.d = o.obs_date")
_OLD_ASSET = sa.text(
    "SELECT p.asset_id, p.obs_date, p.value FROM asset.price_daily p"
    " JOIN unnest(cast(:ids AS bigint[]), cast(:dates AS date[]), cast(:types AS text[])) AS u(id, d, t)"
    " ON u.id = p.asset_id AND u.d = p.obs_date AND u.t = p.price_type")
_UPSERT_OHLC = sa.text(
    "INSERT INTO asset.ohlc_daily (asset_id, obs_date, open, high, low, close, close_adj, volume)"
    " SELECT * FROM unnest(cast(:ids AS bigint[]), cast(:dates AS date[]), cast(:o AS numeric[]), cast(:h AS numeric[]),"
    " cast(:l AS numeric[]), cast(:c AS numeric[]), cast(:ca AS numeric[]), cast(:v AS numeric[]))"
    " ON CONFLICT (asset_id, obs_date) DO UPDATE SET open = excluded.open, high = excluded.high, low = excluded.low,"
    " close = excluded.close, close_adj = excluded.close_adj, volume = excluded.volume, ingested_at = clock_timestamp()"
    " WHERE (asset.ohlc_daily.open, asset.ohlc_daily.high, asset.ohlc_daily.low, asset.ohlc_daily.close,"
    " asset.ohlc_daily.close_adj, asset.ohlc_daily.volume) IS DISTINCT FROM"
    " (excluded.open, excluded.high, excluded.low, excluded.close, excluded.close_adj, excluded.volume)"
    " RETURNING (xmax = 0) AS inserted")


def _run_points(conn, w: Written, chunk, resolved, code_of, upsert, old_sql, params):
    old = {(r[0], r[1]): r[2] for r in conn.execute(old_sql, params).all()}
    new = {(resolved[p.code].row_id, p.obs_date): p.value for p in chunk}
    for inserted, rid, d in conn.execute(upsert, params).all():
        if inserted:
            w.inserted += 1
        else:
            w.changed += 1
            if len(w.changes_sample) < SAMPLE_CAP:
                w.changes_sample.append((code_of[rid], d.isoformat(), old.get((rid, d)), new[(rid, d)]))


def apply(conn, points, resolved) -> Written:
    w = Written()
    code_of_m = {r.row_id: c for c, r in resolved.items() if r.domain == "macro"}
    code_of_a = {r.row_id: c for c, r in resolved.items() if r.domain == "asset"}
    macro = [p for p in points if p.domain == "macro"]
    asset = [p for p in points if p.domain == "asset"]
    for start in range(0, len(macro), CHUNK):
        chunk = macro[start:start + CHUNK]
        params = {"ids": [resolved[p.code].row_id for p in chunk], "dates": [p.obs_date for p in chunk],
                  "vals": [p.value for p in chunk]}
        _run_points(conn, w, chunk, resolved, code_of_m, _UPSERT_MACRO, _OLD_MACRO, params)
    for start in range(0, len(asset), CHUNK):
        chunk = asset[start:start + CHUNK]
        params = {"ids": [resolved[p.code].row_id for p in chunk], "dates": [p.obs_date for p in chunk],
                  "types": [p.price_type for p in chunk], "vals": [p.value for p in chunk]}
        _run_points(conn, w, chunk, resolved, code_of_a, _UPSERT_ASSET, _OLD_ASSET, params)
    return w


def apply_ohlc(conn, bars, resolved) -> Written:
    w = Written()
    for start in range(0, len(bars), CHUNK):
        chunk = bars[start:start + CHUNK]
        flags = conn.execute(_UPSERT_OHLC, {
            "ids": [resolved[b.code].row_id for b in chunk], "dates": [b.obs_date for b in chunk],
            "o": [b.open for b in chunk], "h": [b.high for b in chunk], "l": [b.low for b in chunk],
            "c": [b.close for b in chunk], "ca": [b.close_adj for b in chunk], "v": [b.volume for b in chunk]}).scalars().all()
        w.inserted += sum(1 for f in flags if f)
        w.changed += sum(1 for f in flags if not f)
    return w


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def store_refusal_evidence(engine, source: str, texts: dict[str, str], run_id: int, reasons: list[str]) -> None:
    """Bằng chứng ở giao dịch RIÊNG — lượt chính không ghi gì. JSON hợp lệ vào payload; body khác vào text."""
    with engine.begin() as conn:
        for key, text in texts.items():
            meta = json.dumps({"run_id": run_id, "reasons": reasons, "refused": True, "hash": _hash(text)}, ensure_ascii=False)
            try:
                json.loads(text)
                conn.execute(sa.text(
                    "INSERT INTO staging.raw_payload (source, endpoint_key, content_type, payload, meta)"
                    " VALUES (:src, :ek, 'json', cast(:p AS jsonb), cast(:m AS jsonb))"),
                    {"src": source, "ek": f"{source}:{key}", "p": text, "m": meta})
            except ValueError:
                conn.execute(sa.text(
                    "INSERT INTO staging.raw_payload (source, endpoint_key, content_type, body, meta)"
                    " VALUES (:src, :ek, 'text', :b, cast(:m AS jsonb))"),
                    {"src": source, "ek": f"{source}:{key}", "b": text[:100000], "m": meta})


def upsert_domain_state(engine, source: str, domains: tuple[str, ...], watermark: str) -> None:
    with engine.begin() as conn:
        for domain in domains:
            conn.execute(sa.text(
                "INSERT INTO ops.data_domain_state (domain, source, status, last_success_at, watermark)"
                " VALUES (:d, :s, 'active', now(), :w)"
                " ON CONFLICT (domain, source) DO UPDATE SET last_success_at = now(), watermark = :w, status = 'active'"),
                {"d": domain, "s": source, "w": watermark})
