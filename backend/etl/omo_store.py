"""Ghi kết quả OMO — append-only, ngày trùng bỏ qua (sbv-omo.md §9.2, step-04 §3)."""
from __future__ import annotations

import hashlib
import json

import sqlalchemy as sa

from etl.omo_parse import OmoResult


def store(result: OmoResult, html: str, conn) -> dict:
    exists = conn.execute(
        sa.text("SELECT 1 FROM macro.omo_session WHERE session_date = :d"),
        {"d": result.session_date},
    ).first()
    if exists:
        return {"skipped": True}
    conn.execute(
        sa.text(
            "INSERT INTO macro.omo_session"
            " (session_date, crawled_at, has_reverse_repo, has_repo, has_outright_sale)"
            " VALUES (:d, now(), :r, :p, :o)"
        ),
        {"d": result.session_date,
         "r": "reverse_repo" in result.groups_present,
         "p": "repo" in result.groups_present,
         "o": "outright_sale" in result.groups_present},
    )
    for row in result.rows:
        conn.execute(
            sa.text(
                "INSERT INTO macro.omo_auction (session_date, op_type, tenor_days,"
                " participants, winners, volume_vnd, rate_pct)"
                " VALUES (:d, :op, :t, :p, :w, :v, :r)"
            ),
            {"d": result.session_date, "op": row.op_type, "t": row.tenor_days,
             "p": row.participants, "w": row.winners,
             "v": row.volume_vnd, "r": row.rate_pct},
        )
    body_bytes = html.encode("utf-8")
    conn.execute(
        sa.text(
            "INSERT INTO staging.raw_payload (source, endpoint_key, content_type, body, meta)"
            " VALUES ('sbv', 'omo', 'html', :b, cast(:m AS jsonb))"
        ),
        {"b": html, "m": json.dumps({"bytes": len(body_bytes),
                                     "hash": hashlib.sha256(body_bytes).hexdigest()})},
    )
    return {"sessions": 1, "auctions": len(result.rows)}


def open_run(engine, job: str) -> int:
    with engine.connect() as c:
        rid = c.execute(
            sa.text("INSERT INTO ops.etl_run (job) VALUES (:j) RETURNING run_id"), {"j": job}
        ).scalar_one()
        c.commit()
        return rid


def close_run(engine, run_id: int, status: str, stats: dict | None = None,
              error: str | None = None) -> None:
    with engine.connect() as c:
        c.execute(
            sa.text("UPDATE ops.etl_run SET finished_at = now(), status = :s,"
                    " stats = cast(:st AS jsonb), error = :e WHERE run_id = :r"),
            {"s": status, "st": json.dumps(stats) if stats is not None else None,
             "e": error, "r": run_id},
        )
        c.commit()


def upsert_domain_state(engine, watermark: str) -> None:
    with engine.connect() as c:
        c.execute(
            sa.text(
                "INSERT INTO ops.data_domain_state (domain, source, status, last_success_at, watermark)"
                " VALUES ('macro.omo', 'sbv', 'active', now(), :w)"
                " ON CONFLICT (domain, source) DO UPDATE"
                " SET last_success_at = now(), watermark = :w, status = 'active'"
            ),
            {"w": watermark},
        )
        c.commit()
