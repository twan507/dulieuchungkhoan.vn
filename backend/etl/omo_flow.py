"""Rebuild macro.omo_flow — tầng tự tính, xoá-dựng-lại toàn phần idempotent (step-04 §3).

complete(D) cần CẢ BA: (1) đủ ≥140 ngày lịch sử; (2) lịch ngày làm việc từ
market.price_daily PHỦ cửa sổ [D−140, D] (rỗng/không phủ ⇒ false — cấm vacuous-true);
(3) mọi ngày làm việc trong cửa sổ đều có dòng omo_session. Chiều dấu repo/outright_sale
CHƯA KIỂM trên phiên thật — gặp phiên đầu có nhóm đó phải đối chiếu tay (spec §4.4).
"""
from __future__ import annotations

import sqlalchemy as sa

_REBUILD = """
DELETE FROM macro.omo_flow;   -- KHÔNG dùng TRUNCATE: đòi quyền chủ bảng, role dlck_etl chỉ có DML (migration 0009)
WITH signed AS (
  SELECT session_date, tenor_days,
         CASE WHEN op_type = 'reverse_repo' THEN volume_vnd ELSE -volume_vnd END AS sv
  FROM macro.omo_auction
),
inj AS (SELECT session_date AS d, sum(sv) AS v FROM signed GROUP BY 1),
mat AS (SELECT (session_date + tenor_days) AS d, sum(sv) AS v FROM signed GROUP BY 1),
days AS (SELECT d FROM inj UNION SELECT d FROM mat)
INSERT INTO macro.omo_flow (flow_date, injection_vnd, maturing_vnd, net_vnd, outstanding_vnd, complete)
SELECT days.d,
       coalesce(inj.v, 0),
       coalesce(mat.v, 0),
       coalesce(inj.v, 0) - coalesce(mat.v, 0),
       sum(coalesce(inj.v, 0) - coalesce(mat.v, 0)) OVER (ORDER BY days.d),
       false
FROM days LEFT JOIN inj ON inj.d = days.d LEFT JOIN mat ON mat.d = days.d;

UPDATE macro.omo_flow f SET complete = true
WHERE (SELECT min(session_date) FROM macro.omo_session) <= f.flow_date - 140
  AND EXISTS (SELECT 1 FROM market.price_daily p WHERE p.trading_date <= f.flow_date - 140)
  AND EXISTS (SELECT 1 FROM market.price_daily p WHERE p.trading_date >= f.flow_date)
  AND NOT EXISTS (
    SELECT 1
    FROM (SELECT DISTINCT trading_date AS wd FROM market.price_daily
          WHERE trading_date BETWEEN f.flow_date - 140 AND f.flow_date) w
    LEFT JOIN macro.omo_session s ON s.session_date = w.wd
    WHERE s.session_date IS NULL
  );
"""


def rebuild(conn) -> int:
    for stmt in _REBUILD.split(";"):
        if stmt.strip():
            conn.execute(sa.text(stmt))
    return conn.execute(sa.text("SELECT count(*) FROM macro.omo_flow")).scalar_one()
