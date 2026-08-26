"""Đối chứng cuối phiên §5.7 spec ClickHouse — hai chiều lệch hai nghĩa, hai ngưỡng."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

THRESHOLD = 0.001  # 0,1% — hiệu chỉnh sau tuần đầu (spec CH §10)

_SQL = """
SELECT coalesce(b.symbol, t.symbol) AS symbol,
       coalesce(b.sv, 0)  AS bar_vol,  coalesce(t.mv, 0)  AS avo
FROM (SELECT symbol, sum(v) AS sv FROM rt.bar_1m_v WHERE toDate(ts) = {d:Date} GROUP BY symbol) b
FULL OUTER JOIN
     (SELECT symbol, max(cum_volume) AS mv FROM rt.trade WHERE toDate(ts) = {d:Date} GROUP BY symbol) t
ON b.symbol = t.symbol
"""


@dataclass
class ReconcileResult:
    p1: list
    p2: list
    ok: int


def _classify(bar_vol: int, avo: int) -> str:
    if bar_vol > avo:
        return "p1"                       # đếm đôi — luôn là lỗi
    if avo == 0:
        return "ok"
    miss = (avo - bar_vol) / avo
    if miss > THRESHOLD:
        return "p2"                       # mất quá ngưỡng chấp nhận
    return "minor" if miss > 0 else "ok"


def reconcile(client, d: date) -> ReconcileResult:
    rows = client.query(_SQL, parameters={"d": d}).result_rows
    p1, p2, ok = [], [], 0
    for symbol, bar_vol, avo in rows:
        kind = _classify(int(bar_vol), int(avo))
        if kind == "p1":
            p1.append((symbol, int(bar_vol), int(avo)))
        elif kind == "p2":
            p2.append((symbol, int(bar_vol), int(avo)))
        else:
            ok += 1
    return ReconcileResult(p1, p2, ok)
