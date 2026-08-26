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
-- injection_vnd / maturing_vnd là HAI CHIỀU TIỀN, đều KHÔNG ÂM (không bù trừ dấu):
--   injection = tiền BƠM RA thị trường trong ngày, maturing = tiền HÚT VỀ trong ngày.
-- Mỗi phiên đấu thầu sinh HAI sự kiện tiền: phát hành tại session_date và đáo hạn tại
-- session_date + tenor_days. Hai nhóm nghiệp vụ ngược chiều nhau:
--   reverse_repo (SBV cho vay có kỳ hạn) : phát hành = bơm, đáo hạn = hút
--   repo / outright_sale (SBV phát hành tín phiếu) : phát hành = hút, đáo hạn = bơm
-- Ca thường gặp — phiên chỉ có reverse_repo — cho ra đúng nghĩa tên cột: injection là
-- tiền bơm của phiên hôm nay, maturing là tiền đáo hạn của các phiên trước. Hai số hạng
-- CHÉO (đáo hạn vào injection, phát hành vào maturing) chỉ xuất hiện khi SBV phát hành
-- tín phiếu. net_vnd = injection − maturing (dương = bơm ròng) giữ nguyên nghĩa và giá
-- trị như trước, và outstanding_vnd vẫn là cộng dồn net theo ngày.
-- (KHÔNG đặt dấu chấm phẩy trong chú thích — rebuild() cắt câu lệnh bằng dấu đó)
WITH ev AS (
  SELECT session_date AS d,
         CASE WHEN op_type = 'reverse_repo' THEN volume_vnd ELSE 0 END AS inj,
         CASE WHEN op_type = 'reverse_repo' THEN 0 ELSE volume_vnd END AS mat
  FROM macro.omo_auction
  UNION ALL
  SELECT (session_date + tenor_days) AS d,
         CASE WHEN op_type = 'reverse_repo' THEN 0 ELSE volume_vnd END AS inj,
         CASE WHEN op_type = 'reverse_repo' THEN volume_vnd ELSE 0 END AS mat
  FROM macro.omo_auction
),
agg AS (SELECT d, sum(inj) AS inj, sum(mat) AS mat FROM ev GROUP BY d)
INSERT INTO macro.omo_flow (flow_date, injection_vnd, maturing_vnd, net_vnd, outstanding_vnd, complete)
SELECT d, inj, mat, inj - mat, sum(inj - mat) OVER (ORDER BY d), false
FROM agg;

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
