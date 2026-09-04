"""Danh sách tới hạn và ghi kết quả họ Snapshot (spec §5.4). SQL thuần.

KHÔNG có con trỏ, và không cần: `ops.snapshot_check.checked_at` CHÍNH LÀ con trỏ —
lượt sau tự lấy nhóm cũ nhất chưa tới lượt, nên lượt bị giết giữa chừng không mất chỗ.
"""
from __future__ import annotations

import datetime as dt

import sqlalchemy as sa

from etl.snapshot_fetch import KINDS, Target

JOB = "market.snapshot"
DOMAIN = "market.snapshot"
SOURCE = "fiintrade"

CADENCE_DAYS = {"snapshot": 90, "valuation": 30, "ownership": 30, "dividend": 30}
QUOTA = {"snapshot": 24, "valuation": 70, "ownership": 70, "dividend": 70}
TRIGGER_KINDS = {"Earning": "snapshot", "ShareIssuance": "snapshot",
                 "CashDividend": "dividend", "StockDividend": "dividend"}

# Vũ trụ: issuer có ÍT NHẤT một cổ phiếu đang niêm yết. Quỹ/ETF tự rơi ra vì không có
# security dạng stock (đo 2026-09-04) — không cần luật loại riêng.
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
        "SELECT watermark FROM ops.data_domain_state"
        " WHERE domain = :d AND source = :s"), {"d": DOMAIN, "s": SOURCE}).scalar()
    return dt.date.fromisoformat(got) if got else dt.date(1900, 1, 1)


def _target(row, kind: str, found_by: str) -> Target:
    return Target(kind=kind, issuer_id=row.issuer_id, organ_code=row.organ_code,
                  ticker=row.ticker, com_type=row.com_type_code, found_by=found_by)


def due_list(conn, watermark: dt.date, kinds=None, codes=None,
             quota=None, cadence=None) -> list[Target]:
    kinds = list(kinds or KINDS)
    quota = quota or QUOTA
    cadence = cadence or CADENCE_DAYS

    if codes:                                   # lượt ép: mọi kind, bỏ qua nhịp và quota
        rows = conn.execute(sa.text(
            _UNIVERSE + "SELECT * FROM uni WHERE ticker = ANY(:codes) ORDER BY ticker"),
            {"codes": list(codes)}).all()
        return [_target(r, k, "floor") for r in rows for k in kinds]

    out: list[Target] = []
    seen: set[tuple[int, str]] = set()

    event_types = [t for t, k in TRIGGER_KINDS.items() if k in kinds]
    if event_types:
        rows = conn.execute(sa.text(
            _UNIVERSE + """
            SELECT DISTINCT u.*, e.event_type
            FROM uni u
            JOIN market.corporate_event e ON e.issuer_id = u.issuer_id
            WHERE e.event_type = ANY(:types)
              AND greatest(coalesce(e.public_date, DATE '1900-01-01'),
                           coalesce(e.exright_date, DATE '1900-01-01')) > :wm
            ORDER BY u.issuer_id
            """), {"types": event_types, "wm": watermark}).all()
        for r in rows:
            kind = TRIGGER_KINDS[r.event_type]
            if (r.issuer_id, kind) not in seen:
                seen.add((r.issuer_id, kind))
                out.append(_target(r, kind, "event"))

    for kind in kinds:
        rows = conn.execute(sa.text(
            _UNIVERSE + """
            SELECT u.* FROM uni u
            LEFT JOIN ops.snapshot_check c ON c.issuer_id = u.issuer_id AND c.kind = :kind
            WHERE c.checked_at IS NULL
               OR c.checked_at < now() - make_interval(days => :cadence)
            ORDER BY c.checked_at NULLS FIRST, u.issuer_id
            LIMIT :quota
            """), {"kind": kind, "cadence": cadence[kind], "quota": quota[kind]}).all()
        for r in rows:
            if (r.issuer_id, kind) not in seen:      # trigger đã lấy rồi thì thôi
                seen.add((r.issuer_id, kind))
                out.append(_target(r, kind, "floor"))
    return out
