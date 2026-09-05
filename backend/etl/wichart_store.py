"""Ghi kho cho `etl wichart` (spec §5.5). Từ lát 7 (2026-09-05) đường ghi chung nằm ở `series_store`/`registry`;
file này giữ phần RIÊNG của WiChart: hằng job/miền, `series_break` GDP, bằng chứng thô khi hash đổi."""
from __future__ import annotations

import json
from datetime import date
from decimal import Decimal

import sqlalchemy as sa

from etl import series_store
from etl.registry import load_registry as _load
from etl.series_store import Resolved, Written, apply, hash_text  # noqa: F401 — test lát 6 import từ đây
from etl.wichart_guard import Verdict
from etl.wichart_registry import SOURCE

JOB = "macro.wichart"
DOMAINS = ("macro.indicator", "asset")
# Đứt gãy GDP giá so sánh: nguồn nhảy tại kỳ nguồn neo "2026-03" = Q1/2026; kho neo đầu kỳ ⇒ 2026-01-01
# là điểm ĐẦU TIÊN thuộc nền mới. Hệ số = TB hai ước lượng độc lập (wichart.md Bẫy 6). Chủ dự án chốt
# 2026-09-05: không cần verified_by, ghi ngày.
GDP_BREAK = dict(code="vn.gdp.real", break_date=date(2026, 1, 1), factor=Decimal("1.6005"),
                 reason="Đổi năm gốc giá so sánh; trung bình hai ước lượng độc lập 1.6032 / 1.5978 (wichart.md Bẫy 6)",
                 verified_at=date(2026, 9, 5))


def load_registry(conn, series) -> tuple[dict[str, Resolved], dict]:
    return _load(conn, series, SOURCE)


def seed_series_break(conn) -> None:
    conn.execute(sa.text(
        "INSERT INTO macro.series_break (indicator_id, break_date, factor, reason, verified_at)"
        " SELECT indicator_id, :d, :f, :r, :v FROM macro.indicator WHERE code = :code"
        " ON CONFLICT (indicator_id, break_date) DO UPDATE SET factor = excluded.factor, reason = excluded.reason,"
        " verified_at = excluded.verified_at"),
        {"code": GDP_BREAK["code"], "d": GDP_BREAK["break_date"], "f": GDP_BREAK["factor"],
         "r": GDP_BREAK["reason"], "v": GDP_BREAK["verified_at"]})


def store_payload_if_changed(conn, key: str, text: str, run_id: int) -> bool:
    ek = f"wichart:{key}"
    h = hash_text(text)
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
    series_store.store_refusal_evidence(engine, SOURCE, texts, run_id, verdict.reasons)


def upsert_domain_state(engine, watermark: str) -> None:
    series_store.upsert_domain_state(engine, SOURCE, DOMAINS, watermark)
