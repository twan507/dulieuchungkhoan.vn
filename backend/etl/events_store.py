"""Ghi kho cho job events (spec §5.5).

Chính sách F7 (step-03 §4, review vòng 4): mã vắng danh bạ ⇒ TẠO issuer tối thiểu rồi ghi
sự kiện, không bỏ dòng, không để FK chặn job.

🔴 LUẬT CHỐNG HAI-CHỦ-MỘT-BẢNG (§1.7): `etl refdata` là chủ duy nhất của NỘI DUNG
`market.issuer`. Job này chỉ được INSERT khi organ_code chưa tồn tại, TUYỆT ĐỐI KHÔNG
UPDATE. Khi doanh nghiệp vào danh bạ, refdata nhận diện đúng dòng đó qua organ_code và
cập nhật — issuer tối thiểu tự lành, không đẻ dòng thứ hai.
"""
from __future__ import annotations

import json

import sqlalchemy as sa

from etl.events_normalize import EventRow

JOB = "market.events"
EVIDENCE_ITEMS = 50
BATCH = 5000

# Biểu thức coalesce phải LẶP NGUYÊN VĂN toàn bộ index `corporate_event_natural_key`
# thì Postgres mới suy ra arbiter (step-03 §4, vòng 4 F9). Đã chạy thật 2026-09-03.
SQL_UPSERT = (
    "INSERT INTO market.corporate_event"
    " (event_type, issuer_id, public_date, exright_date, record_date, payout_date,"
    "  year_report, length_report, stage_key, payload, source_url)"
    " VALUES (:t, :i, :pd, :ed, :rd, :yd, :yr, :lr, :sk, cast(:p AS jsonb), :su)"
    " ON CONFLICT (event_type, issuer_id,"
    "   coalesce(public_date,   '1900-01-01'),"
    "   coalesce(exright_date,  '1900-01-01'),"
    "   coalesce(year_report,   0),"
    "   coalesce(length_report, 0),"
    "   coalesce(stage_key,     ''))"
    " DO UPDATE SET payload = EXCLUDED.payload, source_url = EXCLUDED.source_url,"
    "   ingested_at = clock_timestamp()"
)


def load_baseline(engine) -> dict[str, int] | None:
    """Mốc cho vế (ii) — counts của lượt success gần nhất (khuôn screener_store)."""
    with engine.connect() as c:
        row = c.execute(sa.text(
            "SELECT stats FROM ops.etl_run WHERE job = :j AND status = 'success'"
            " ORDER BY finished_at DESC LIMIT 1"), {"j": JOB}).first()
    if row is None or not row[0]:
        return None
    return row[0].get("counts")


def ensure_issuers(conn, rows: list[EventRow]) -> tuple[dict[str, int], int]:
    names: dict[str, str | None] = {}
    for r in rows:
        if names.get(r.organ_code) is None:          # tên đầu tiên khác None thắng
            names[r.organ_code] = r.name_hint
    by_organ = {code: iid for code, iid in conn.execute(sa.text(
        "SELECT external_code, issuer_id FROM market.issuer_external_id"
        " WHERE source = 'fiintrade'")).all()}
    created = 0
    for code in sorted(names):
        if code in by_organ:
            continue                                  # KHÔNG update — refdata sở hữu nội dung
        issuer_id = conn.execute(sa.text(
            "INSERT INTO market.issuer (name) VALUES (:n) RETURNING issuer_id"),
            {"n": names[code] or code}).scalar_one()
        conn.execute(sa.text(
            "INSERT INTO market.issuer_external_id (issuer_id, source, external_code)"
            " VALUES (:i, 'fiintrade', :c)"), {"i": issuer_id, "c": code})
        by_organ[code] = issuer_id
        created += 1
    return by_organ, created


def apply(conn, rows: list[EventRow], issuer_by_organ: dict[str, int]) -> dict:
    params = [{"t": r.event_type, "i": issuer_by_organ[r.organ_code],
               "pd": r.public_date, "ed": r.exright_date, "rd": r.record_date,
               "yd": r.payout_date, "yr": r.year_report, "lr": r.length_report,
               "sk": r.stage_key, "p": json.dumps(r.payload, ensure_ascii=False),
               "su": r.source_url} for r in rows]
    stmt = sa.text(SQL_UPSERT)
    for i in range(0, len(params), BATCH):            # executemany theo lô — 110k dòng một lượt
        conn.execute(stmt, params[i:i + BATCH])
    return {"rows_written": len(rows)}


def store_refusal_evidence(engine, pages: dict[str, list[str]], run_id: int,
                           verdict, counts: dict, collected: dict) -> None:
    """Bằng chứng vào `staging.raw_payload` — KHÔNG lưu trang thô.

    Một lượt là 36 MB, và review vòng 4 F1 đã chốt sự kiện không vào staging vì đã có
    thô inline per-row. Lưu counts + 50 bản ghi đầu của họ bị nghi là đủ chẩn đoán.
    """
    sample = {}
    for fam in (verdict.families or tuple(pages)):
        texts = pages.get(fam) or []
        sample[fam] = json.loads(texts[0])["items"][:EVIDENCE_ITEMS] if texts else []
    with engine.begin() as conn:
        conn.execute(sa.text(
            "INSERT INTO staging.raw_payload (source, endpoint_key, content_type, payload, meta)"
            " VALUES ('fiintrade', 'events:refusal', 'json', cast(:p AS jsonb), cast(:m AS jsonb))"),
            {"p": json.dumps({"counts": counts, "collected": collected, "sample": sample},
                             ensure_ascii=False),
             "m": json.dumps({"run_id": run_id, "reasons": list(verdict.reasons)},
                             ensure_ascii=False)})


def upsert_domain_state(engine, watermark: str) -> None:
    with engine.begin() as conn:
        conn.execute(sa.text(
            "INSERT INTO ops.data_domain_state (domain, source, status, last_success_at, watermark)"
            " VALUES ('market.events', 'fiintrade', 'active', now(), :w)"
            " ON CONFLICT (domain, source) DO UPDATE"
            " SET last_success_at = now(), watermark = :w, status = 'active'"), {"w": watermark})
