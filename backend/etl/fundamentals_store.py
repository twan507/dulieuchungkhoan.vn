"""Danh sách tới hạn, từ điển và ghi kết quả BCTC (spec §5.4). SQL thuần.

Không có con trỏ: `ops.fundamentals_check.checked_at` CHÍNH LÀ con trỏ — kể cả ở chế độ
--backfill (lấy mọi dòng chưa kiểm, ORDER BY issuer_id), nên lượt bị giết giữa chừng không mất chỗ.

Khi nội dung đổi: XOÁ trọn (issuer, statement_type) rồi CHÈN lại trong cùng giao dịch — một luật,
điều chỉnh hồi tố / ô biến mất / ô đổi giá trị đều tự đúng (spec §4.4). Lịch sử đổi nằm ở
staging.raw_payload, một dòng mỗi lần đổi.
"""
from __future__ import annotations

import datetime as dt
import json
import logging
from dataclasses import dataclass
from pathlib import Path

import sqlalchemy as sa

from etl.fundamentals_fetch import KINDS, Target
from etl.fundamentals_guard import Tally, Verdict
from etl.fundamentals_normalize import EMPTY_HASH, STATEMENT, ReportRow, StatementRow, payload_hash

log = logging.getLogger("etl.fundamentals")

JOB = "market.fundamentals"
DOMAIN = "market.fundamentals"
SOURCE = "fiintrade"

MAX_EVIDENCE = 20
MAX_TRIGGER = 300                                  # trần nhánh trigger/lượt — xem due_list()
COLD_START = dt.date(1900, 1, 1)
CADENCE_DAYS = 90
QUOTA = 20                                         # mã/kind/ngày ⇒ 80 lời gọi/ngày, phủ 1.523 mã sau 77 ngày
INSERT_CHUNK = 5000

DICTIONARY_JSON = Path(__file__).resolve().parents[2] / "docs" / "10-sources" / "market" / "field-dictionary.json"
DICTIONARY_GROUPS = ("chi_tieu_bao_cao_tai_chinh", "chi_tieu_ty_so_va_thi_truong")

# Vũ trụ: issuer có ÍT NHẤT một cổ phiếu đang niêm yết — nguyên văn snapshot_store._UNIVERSE.
_UNIVERSE = """
WITH uni AS (
  SELECT i.issuer_id, x.external_code AS organ_code, i.com_type_code,
         (SELECT s.ticker FROM market.security s
           WHERE s.issuer_id = i.issuer_id AND s.status = 'listed' AND s.security_type = 'stock'
           ORDER BY s.security_id LIMIT 1) AS ticker
  FROM market.issuer i
  JOIN market.issuer_external_id x ON x.issuer_id = i.issuer_id AND x.source = 'fiintrade'
  WHERE EXISTS (SELECT 1 FROM market.security s
                 WHERE s.issuer_id = i.issuer_id AND s.status = 'listed'
                   AND s.security_type = 'stock')
)
"""


def load_watermark(conn) -> dt.date:
    got = conn.execute(sa.text(
        "SELECT watermark FROM ops.data_domain_state WHERE domain = :d AND source = :s"),
        {"d": DOMAIN, "s": SOURCE}).scalar()
    return dt.date.fromisoformat(got) if got else COLD_START


def new_watermark(conn) -> dt.date:
    """Mốc 'sự kiện MỚI CÔNG BỐ' — CHỈ `public_date` của `Earning`. Không trộn `exright_date`
    (bài học mốc nước tương lai của lát 4)."""
    got = conn.execute(sa.text(
        "SELECT max(public_date) FROM market.corporate_event WHERE event_type = 'Earning'")).scalar()
    return got or COLD_START


def _target(row, kind: str, found_by: str) -> Target:
    return Target(kind=kind, issuer_id=row.issuer_id, organ_code=row.organ_code,
                  ticker=row.ticker, found_by=found_by)


def due_list(conn, watermark: dt.date, kinds=None, codes=None, backfill: bool = False,
             quota: int = QUOTA, cadence: int = CADENCE_DAYS, max_trigger: int = MAX_TRIGGER) -> list[Target]:
    kinds = list(kinds or KINDS)
    if codes:                                       # lượt ép: mọi kind, bỏ nhịp và quota
        rows = conn.execute(sa.text(
            _UNIVERSE + "SELECT * FROM uni WHERE ticker = ANY(:codes) ORDER BY ticker"),
            {"codes": list(codes)}).all()
        return [_target(r, k, "floor") for r in rows for k in kinds]

    out: list[Target] = []
    seen: set[tuple[int, str]] = set()

    if watermark == COLD_START:
        log.info("bỏ qua nhánh trigger: mốc nước còn ở mốc khởi tạo (cold start) — quét sàn/backfill tự phủ")
    else:
        rows = conn.execute(sa.text(
            _UNIVERSE + """
            SELECT u.issuer_id, u.organ_code, u.com_type_code, u.ticker, min(e.public_date) AS public_date
            FROM uni u
            JOIN market.corporate_event e ON e.issuer_id = u.issuer_id
            WHERE e.event_type = 'Earning' AND e.public_date > :wm
            GROUP BY u.issuer_id, u.organ_code, u.com_type_code, u.ticker
            ORDER BY min(e.public_date) ASC, u.issuer_id
            LIMIT :limit
            """), {"wm": watermark, "limit": max_trigger + 1}).all()
        if len(rows) > max_trigger:
            log.info("nhánh trigger vượt trần %d: cắt %d issuer, giữ cũ nhất theo public_date",
                     max_trigger, len(rows) - max_trigger)
            rows = rows[:max_trigger]
        for r in rows:
            for kind in kinds:
                if (r.issuer_id, kind) not in seen:
                    seen.add((r.issuer_id, kind))
                    out.append(_target(r, kind, "event"))

    for kind in kinds:
        if backfill:
            sql = (_UNIVERSE + """
                SELECT u.* FROM uni u
                LEFT JOIN ops.fundamentals_check c ON c.issuer_id = u.issuer_id AND c.kind = :kind
                WHERE c.checked_at IS NULL
                ORDER BY u.issuer_id
                """)
            params = {"kind": kind}
        else:
            sql = (_UNIVERSE + """
                SELECT u.* FROM uni u
                LEFT JOIN ops.fundamentals_check c ON c.issuer_id = u.issuer_id AND c.kind = :kind
                WHERE c.checked_at IS NULL
                   OR c.checked_at < now() - make_interval(days => :cadence)
                ORDER BY c.checked_at NULLS FIRST, u.issuer_id
                LIMIT :quota
                """)
            params = {"kind": kind, "cadence": cadence, "quota": quota}
        for r in conn.execute(sa.text(sql), params).all():
            if (r.issuer_id, kind) not in seen:
                seen.add((r.issuer_id, kind))
                out.append(_target(r, kind, "floor"))
    return out


def remaining(conn, kinds=None) -> int:
    """Số (issuer, kind) chưa từng kiểm — tiến độ của lượt điền đầu."""
    kinds = list(kinds or KINDS)
    return conn.execute(sa.text(
        _UNIVERSE + """
        SELECT count(*) FROM uni u
        CROSS JOIN unnest(cast(:kinds AS text[])) AS k(kind)
        LEFT JOIN ops.fundamentals_check c ON c.issuer_id = u.issuer_id AND c.kind = k.kind
        WHERE c.checked_at IS NULL
        """), {"kinds": kinds}).scalar_one()


def load_dictionary(conn) -> int:
    """Upsert 729 mã từ file trong repo — hợp đồng khởi động: file hỏng thì raise TRƯỚC khi fetch."""
    data = json.loads(DICTIONARY_JSON.read_text(encoding="utf-8"))
    rows = []
    for group in DICTIONARY_GROUPS:
        entries = data.get(group)
        if not isinstance(entries, dict) or not entries:
            raise RuntimeError(f"từ điển thiếu nhóm {group!r}: {DICTIONARY_JSON}")
        for code, e in entries.items():
            rng = e.get("dai_gia_tri") or [None, None]
            # 4 mã (growth/momentum/value/vgm) mang thang xếp hạng chữ ['A','B','C','D','F'],
            # không phải khoảng số — cột value_min/value_max là numeric nên bỏ qua, không raise.
            lo = rng[0] if isinstance(rng[0], (int, float)) and not isinstance(rng[0], bool) else None
            hi = rng[1] if isinstance(rng[1], (int, float)) and not isinstance(rng[1], bool) else None
            rows.append({"code": code.lower(), "vi": e.get("ten_vi"), "en": e.get("ten_en"),
                         "unit": e.get("don_vi_du_lieu"), "lo": lo, "hi": hi})
    conn.execute(sa.text(
        "INSERT INTO market.metric_dictionary (dictionary, code, name_vi, name_en, unit, value_min, value_max)"
        " VALUES ('field_dictionary', :code, :vi, :en, :unit, :lo, :hi)"
        " ON CONFLICT (dictionary, code) DO UPDATE SET name_vi = excluded.name_vi, name_en = excluded.name_en,"
        " unit = excluded.unit, value_min = excluded.value_min, value_max = excluded.value_max"), rows)
    return len(rows)


@dataclass
class Fetched:
    target: Target
    text: str
    rows: list                                     # StatementRow | ReportRow, đã chuẩn hoá


def _write_statement(conn, iid: int, st: str, rows: list[StatementRow]) -> None:
    conn.execute(sa.text(
        "DELETE FROM market.financial_statement WHERE issuer_id = :i AND statement_type = :s"), {"i": iid, "s": st})
    params = [{"i": iid, "y": r.year, "l": r.length, "s": st, "m": r.metric_code, "v": r.value} for r in rows]
    for start in range(0, len(params), INSERT_CHUNK):
        conn.execute(sa.text(
            "INSERT INTO market.financial_statement (issuer_id, year_report, length_report, statement_type, metric_code, value)"
            " VALUES (:i, :y, :l, :s, :m, :v)"), params[start:start + INSERT_CHUNK])


def _write_reports(conn, iid: int, rows: list[ReportRow]) -> None:
    if not rows:
        return
    conn.execute(sa.text(
        "INSERT INTO market.financial_report_file (issuer_id, year_report, length_report, title, source_url, source_id)"
        " VALUES (:i, :y, :l, :t, :u, :sid)"
        " ON CONFLICT (source_id) DO UPDATE SET issuer_id = excluded.issuer_id, year_report = excluded.year_report,"
        " length_report = excluded.length_report, title = excluded.title, source_url = excluded.source_url,"
        " ingested_at = clock_timestamp()"),
        [{"i": iid, "y": r.year, "l": r.length, "t": r.title, "u": r.url, "sid": r.source_id} for r in rows])


def apply(conn, fetched: list[Fetched], run_id: int) -> tuple[Tally, int]:
    """Ghi KHI ĐỔI; mọi lượt kiểm (trừ rỗng-trên-mã-từng-có-dữ-liệu) đều cập nhật sổ kiểm."""
    tally, written = Tally(), 0
    for f in fetched:
        t = f.target
        h = payload_hash(f.rows)
        prev = conn.execute(sa.text(
            "SELECT payload_hash FROM ops.fundamentals_check WHERE issuer_id = :i AND kind = :k"),
            {"i": t.issuer_id, "k": t.kind}).scalar()

        if not f.rows and prev is not None and prev != EMPTY_HASH:
            # Rỗng trên mã từng có dữ liệu: KHÔNG xoá, KHÔNG tiến sổ kiểm — lượt sau thử lại (spec §5.4 bước 2)
            tally.empty += 1
            log.warning("%s/%s: nguồn trả rỗng trên mã từng có dữ liệu — giữ nguyên kho", t.organ_code, t.kind)
            continue

        tally.checked += 1
        if prev is None:
            tally.first += 1
            changed = True
        else:
            changed = prev != h
            if t.found_by == "floor":
                tally.floor_compared += 1
                tally.changed_floor += int(changed)
            elif changed:
                tally.changed_event += 1
            if not changed:
                tally.unchanged += 1

        if changed:
            if t.kind in STATEMENT:
                _write_statement(conn, t.issuer_id, STATEMENT[t.kind], f.rows)
            else:
                _write_reports(conn, t.issuer_id, f.rows)
            written += len(f.rows)
            conn.execute(sa.text(
                "INSERT INTO staging.raw_payload (source, endpoint_key, content_type, payload, meta)"
                " VALUES ('fundamentals', :ek, 'json', cast(:p AS jsonb), cast(:m AS jsonb))"),
                {"ek": f"fundamentals:{t.kind}:{t.organ_code}", "p": f.text,
                 "m": json.dumps({"hash": h, "run_id": run_id, "rows": len(f.rows)})})

        # clock_timestamp(), KHÔNG now(): now() đứng yên trong một giao dịch (bài học sổ kiểm lát 4)
        conn.execute(sa.text(
            "INSERT INTO ops.fundamentals_check (issuer_id, kind, checked_at, payload_hash, changed_at, found_by)"
            " VALUES (:i, :k, clock_timestamp(), :h, clock_timestamp(), :f)"
            " ON CONFLICT (issuer_id, kind) DO UPDATE"
            " SET checked_at = clock_timestamp(), payload_hash = :h, found_by = :f,"
            "     changed_at = CASE WHEN :c THEN clock_timestamp() ELSE ops.fundamentals_check.changed_at END"),
            {"i": t.issuer_id, "k": t.kind, "h": h, "f": t.found_by, "c": changed})
    return tally, written


def upsert_domain_state(engine, watermark: str) -> None:
    with engine.begin() as conn:
        conn.execute(sa.text(
            "INSERT INTO ops.data_domain_state (domain, source, status, last_success_at, watermark)"
            " VALUES (:d, :s, 'active', now(), :w)"
            " ON CONFLICT (domain, source) DO UPDATE"
            " SET last_success_at = now(), watermark = :w, status = 'active'"),
            {"d": DOMAIN, "s": SOURCE, "w": watermark})


def store_refusal_evidence(engine, fetched: list[Fetched], run_id: int, verdict: Verdict) -> None:
    """Bằng chứng ở giao dịch RIÊNG — lượt chính đã rollback. Ưu tiên nhóm quét sàn."""
    picked = [f for f in fetched if f.target.found_by == "floor"][:MAX_EVIDENCE] or fetched[:MAX_EVIDENCE]
    meta = json.dumps({"run_id": run_id, "reasons": verdict.reasons}, ensure_ascii=False)
    with engine.begin() as conn:
        for f in picked:
            conn.execute(sa.text(
                "INSERT INTO staging.raw_payload (source, endpoint_key, content_type, payload, meta)"
                " VALUES ('fundamentals', :ek, 'json', cast(:p AS jsonb), cast(:m AS jsonb))"),
                {"ek": f"fundamentals:{f.target.kind}:{f.target.organ_code}", "p": f.text, "m": meta})
