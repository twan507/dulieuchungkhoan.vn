"""Ghi kho cho job screener (spec etl screener §5.5).

`merge` đọc `market.security` theo (ticker, exchange) đang niêm yết — đúng unique
index sẵn có; không ghép qua organ_code → issuer vì một issuer có thể có nhiều security.
`apply` UPSERT theo PK (security_id, trading_date): chạy lại trong ngày đè bản của
chính ngày đó (step-03 §3). Bằng chứng từ chối vào staging.raw_payload ở giao dịch riêng.
"""
from __future__ import annotations

import json

import sqlalchemy as sa

from etl.screener_normalize import ScreenerRow

JOB = "market.screener"


UNMAPPED_SAMPLE = 20        # đủ để chẩn đoán, không phình `ops.etl_run.stats`


def merge(conn, rows: list[ScreenerRow]) -> tuple[list[tuple[int, ScreenerRow]], int]:
    listed = conn.execute(sa.text(
        "SELECT ticker, exchange, security_id FROM market.security WHERE status = 'listed'")).all()
    by_key = {(t, e): sid for t, e, sid in listed}
    mapped: list[tuple[int, ScreenerRow]] = []
    missing: list[str] = []
    for r in rows:
        sid = by_key.get((r.ticker, r.exchange))
        if sid is None:
            missing.append(f"{r.ticker}/{r.exchange}")
        else:
            mapped.append((sid, r))
    return mapped, sorted(missing)


def load_baseline(engine) -> int | None:
    """Mốc cho vế (ii) — counts.items của lượt success gần nhất (khuôn refdata_store)."""
    with engine.connect() as c:
        row = c.execute(sa.text(
            "SELECT stats FROM ops.etl_run WHERE job = :j AND status = 'success'"
            " ORDER BY finished_at DESC LIMIT 1"), {"j": JOB}).first()
    if row is None or not row[0]:
        return None
    return (row[0].get("counts") or {}).get("items")


def apply(conn, mapped: list[tuple[int, ScreenerRow]]) -> dict:
    stmt = sa.text(
        "INSERT INTO market.screener_daily (security_id, trading_date, payload)"
        " VALUES (:sid, :d, cast(:p AS jsonb))"
        " ON CONFLICT (security_id, trading_date) DO UPDATE"
        " SET payload = EXCLUDED.payload, ingested_at = clock_timestamp()")
    for sid, r in mapped:
        conn.execute(stmt, {"sid": sid, "d": r.trading_date, "p": json.dumps(r.payload)})
    return {"rows_written": len(mapped)}


def store_refusal_evidence(engine, pages: list[str], run_id: int, reasons: list[str]) -> None:
    """Bằng chứng vào `staging.raw_payload` — **trang 1 là đủ** cho vế (i)/(iii)/(iv).

    Chỉ lý do *thiếu trang* mới cần trọn bộ, vì cái đang bị nghi chính là bộ trang.
    Lưu 52 trang mỗi ngày nghỉ là ~9,6 MB jsonb vào một staging không có retention.
    """
    keep_all = any("thiếu trang" in r for r in reasons)
    meta = json.dumps({"run_id": run_id, "reasons": reasons})
    with engine.begin() as conn:
        for i, text in enumerate(pages if keep_all else pages[:1], start=1):
            conn.execute(sa.text(
                "INSERT INTO staging.raw_payload (source, endpoint_key, content_type, payload, meta)"
                " VALUES ('screener', :ek, 'json', cast(:p AS jsonb), cast(:m AS jsonb))"),
                {"ek": f"screener:page{i}", "p": text, "m": meta})


def upsert_domain_state(engine, watermark: str) -> None:
    with engine.begin() as conn:
        conn.execute(sa.text(
            "INSERT INTO ops.data_domain_state (domain, source, status, last_success_at, watermark)"
            " VALUES ('market.scores', 'fiintrade', 'active', now(), :w)"
            " ON CONFLICT (domain, source) DO UPDATE"
            " SET last_success_at = now(), watermark = :w, status = 'active'"), {"w": watermark})
