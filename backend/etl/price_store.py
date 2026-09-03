"""Ghi kho cho job price (spec §5.5).

Một câu UPSERT mang ba luật: `coalesce` = điền `close_raw` MỘT LẦN (lược đồ: "không bao giờ
sửa"); `raw || EXCLUDED.raw` = writer chỉ đụng khoá adapter của mình (review vòng 2, C5);
`WHERE … IS DISTINCT FROM` = bỏ qua dòng payload không đổi — lượt hằng ngày ghi lại 60 phiên/mã
(91.000 dòng) mà thường chỉ 1–2 phiên/mã đổi. `rowcount` vì thế là số dòng THẬT SỰ đổi.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date

import sqlalchemy as sa

from etl.price_normalize import PriceRow

JOB_DAILY = "market.price_daily"
JOB_BACKFILL = "market.price_backfill"
DOMAIN = "market.price"
BATCH = 2000
SAMPLE = 20            # bộ đếm phải nêu tên (bài học 3 lát 1) — nhưng không phình etl_run.stats

SQL_UPSERT = (
    "INSERT INTO market.price_daily (security_id, trading_date, close_adj, close_raw,"
    "   open_value, highest_value, lowest_value, raw)"
    " VALUES (:sid, :d, :ca, :cr, :o, :h, :l,"
    "   jsonb_build_object('fiintrade', jsonb_build_object('fetched_at', cast(:fa AS text),"
    "                                                      'payload', cast(:p AS jsonb))))"
    # cast(:fa AS text) bắt buộc: jsonb_build_object là hàm variadic "any", tham số trần trong đó
    # làm Postgres ném IndeterminateDatatype "could not determine data type of parameter $8".
    " ON CONFLICT (security_id, trading_date) DO UPDATE SET"
    "   close_adj = EXCLUDED.close_adj,"
    "   close_raw = coalesce(market.price_daily.close_raw, EXCLUDED.close_raw),"
    "   open_value = EXCLUDED.open_value, highest_value = EXCLUDED.highest_value,"
    "   lowest_value = EXCLUDED.lowest_value,"
    "   raw = market.price_daily.raw || EXCLUDED.raw,"
    "   ingested_at = clock_timestamp()"
    " WHERE market.price_daily.raw->'fiintrade'->'payload'"
    "   IS DISTINCT FROM EXCLUDED.raw->'fiintrade'->'payload'"
)


@dataclass(frozen=True)
class Code:
    security_id: int
    ticker: str
    organ_code: str


@dataclass(frozen=True)
class CodeList:
    codes: list[Code]
    no_organ_code: list[str]


def list_codes(conn, tickers: list[str] | None = None) -> CodeList:
    rows = conn.execute(sa.text(
        "SELECT s.security_id, s.ticker, x.external_code"
        " FROM market.security s"
        " LEFT JOIN market.issuer_external_id x"
        "   ON x.issuer_id = s.issuer_id AND x.source = 'fiintrade'"
        " WHERE s.security_type = 'stock' AND s.status = 'listed'"
        " ORDER BY s.ticker")).all()
    if tickers is not None:
        want = set(tickers)
        unknown = sorted(want - {r.ticker for r in rows})
        if unknown:
            raise ValueError(f"--codes có mã không phải cổ phiếu đang niêm yết: {unknown}")
        rows = [r for r in rows if r.ticker in want]
    codes = [Code(r.security_id, r.ticker, r.external_code) for r in rows if r.external_code]
    by_organ: dict[str, list[str]] = {}
    for c in codes:
        by_organ.setdefault(c.organ_code, []).append(c.ticker)
    dup = {k: v for k, v in by_organ.items() if len(v) > 1}
    if dup:
        raise ValueError(f"một organCode trỏ tới nhiều cổ phiếu niêm yết: {dup}")
    return CodeList(codes, [r.ticker for r in rows if not r.external_code])


def apply(conn, batch: list[tuple[int, list[PriceRow]]], fetched_at: str) -> dict:
    params = [{"sid": sid, "d": r.trading_date, "ca": r.close_adj, "cr": r.close_raw,
               "o": r.open_value, "h": r.highest_value, "l": r.lowest_value,
               "fa": fetched_at, "p": json.dumps(r.payload, ensure_ascii=False)}
              for sid, rows in batch for r in rows]
    stmt = sa.text(SQL_UPSERT)
    changed = 0
    for i in range(0, len(params), BATCH):
        changed += conn.execute(stmt, params[i:i + BATCH]).rowcount
    return {"rows_sent": len(params), "rows_changed": changed}


def raw_close_mismatches(conn, security_ids: list[int], since: date) -> tuple[int, list[str]]:
    """Mắt của quyết định spec §4.2: `close_raw` đã điền có còn khớp `closePrice` mới nhất không."""
    rows = conn.execute(sa.text(
        "SELECT s.ticker, p.trading_date, p.close_raw,"
        "       (p.raw->'fiintrade'->'payload'->>'closePrice')::numeric AS src"
        " FROM market.price_daily p JOIN market.security s USING (security_id)"
        " WHERE p.security_id = ANY(:ids) AND p.trading_date >= :since"
        "   AND p.close_raw IS DISTINCT FROM (p.raw->'fiintrade'->'payload'->>'closePrice')::numeric"
        " ORDER BY s.ticker, p.trading_date"), {"ids": security_ids, "since": since}).all()
    return len(rows), [f"{t} {d} close_raw={cr} closePrice={src}" for t, d, cr, src in rows[:SAMPLE]]


def load_baseline(engine) -> dict | None:
    """Mốc cho vế (ii)/(iv) — lượt success TOÀN TẬP gần nhất; lượt `--codes` (subset) không làm mốc."""
    with engine.connect() as c:
        row = c.execute(sa.text(
            "SELECT stats FROM ops.etl_run WHERE job = :j AND status = 'success'"
            "   AND coalesce((stats->>'subset')::boolean, false) = false"
            " ORDER BY finished_at DESC LIMIT 1"), {"j": JOB_DAILY}).first()
    if row is None or not row[0]:
        return None
    return {"with_data": row[0].get("with_data"), "latest_trading_date": row[0].get("latest_trading_date")}


def load_cursor(engine) -> str | None:
    with engine.connect() as c:
        row = c.execute(sa.text(
            "SELECT stats->>'cursor' FROM ops.etl_run WHERE job = :j AND stats->>'cursor' IS NOT NULL"
            " ORDER BY run_id DESC LIMIT 1"), {"j": JOB_BACKFILL}).first()
    return row[0] if row else None


def save_progress(engine, run_id: int, stats: dict) -> None:
    """Ghi tiến độ vào chính dòng etl_run của lượt — chết giữa chừng vẫn giữ con trỏ."""
    with engine.begin() as c:
        c.execute(sa.text("UPDATE ops.etl_run SET stats = cast(:s AS jsonb) WHERE run_id = :r"),
                  {"s": json.dumps(stats, ensure_ascii=False), "r": run_id})


def store_refusal_evidence(engine, run_id: int, reasons, stats: dict,
                           pages: dict[str, list[str]]) -> None:
    """Bằng chứng vào staging.raw_payload — bộ đếm + 3 bản ghi đầu của ≤ 5 mã, KHÔNG lưu 300 MB trang thô."""
    sample = {}
    for code, texts in list(pages.items())[:5]:
        sample[code] = json.loads(texts[0])["items"][:3] if texts else []
    with engine.begin() as conn:
        conn.execute(sa.text(
            "INSERT INTO staging.raw_payload (source, endpoint_key, content_type, payload, meta)"
            " VALUES ('fiintrade', 'price:refusal', 'json', cast(:p AS jsonb), cast(:m AS jsonb))"),
            {"p": json.dumps({"stats": stats, "sample": sample}, ensure_ascii=False),
             "m": json.dumps({"run_id": run_id, "reasons": list(reasons)}, ensure_ascii=False)})


def upsert_domain_state(engine, watermark: str) -> None:
    with engine.begin() as conn:
        conn.execute(sa.text(
            "INSERT INTO ops.data_domain_state (domain, source, status, last_success_at, watermark)"
            " VALUES (:dom, 'fiintrade', 'active', now(), :w)"
            " ON CONFLICT (domain, source) DO UPDATE"
            " SET last_success_at = now(), watermark = :w, status = 'active'"),
            {"dom": DOMAIN, "w": watermark})
