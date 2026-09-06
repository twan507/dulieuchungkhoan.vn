"""So sánh vài mã trên cùng bộ chỉ tiêu, cùng phiên screener gần nhất.

Cùng nguồn và cùng luật với screen_stocks.py: bảng nhãn đóng cho mã chỉ tiêu, và join
market.metric_dictionary phải khoá dictionary='field_dictionary' — không khoá sẽ nhân đôi
dòng vì (dictionary, code) mới là khoá chính, cùng code có thể có mặt ở 'screener_params'.
"""
from __future__ import annotations

import sqlalchemy as sa

from agent.format import display_metric
from agent.labels import DEFAULT_RATIOS, LABELS
from agent.tools._shared import co_du_lieu, rong, to_json

TRAN_MA, TRAN_CHI_TIEU = 10, 8


def so_sanh_cung_nganh(conn: sa.Connection, tickers: list[str] | None = None,
                       metric_codes: list[str] | None = None,
                       industry_code: str | None = None) -> str:
    codes = list(metric_codes or []) or DEFAULT_RATIOS
    la = [c for c in codes if c not in LABELS]
    if la:
        return to_json({"loi": True, "ly_do": f"ma chi tieu ngoai bang nhan: {la}", "ma_hop_le": sorted(LABELS)})
    codes = codes[:TRAN_CHI_TIEU]
    mas = [t.upper() for t in (tickers or [])][:TRAN_MA]
    if not mas and not industry_code:
        return to_json({"loi": True, "ly_do": "phai cho tickers hoac industry_code"})

    ngay = conn.execute(sa.text("SELECT max(trading_date) FROM market.screener_daily")).scalar()
    if ngay is None:
        return to_json({**rong(), "ngay_du_lieu": None})
    rows = conn.execute(sa.text("""
        SELECT s.ticker, ind.name_vi AS nganh, sd.payload->'stockScreenerItem' AS item
        FROM market.screener_daily sd
        JOIN market.security s USING (security_id)
        LEFT JOIN market.v_issuer_industry v ON v.issuer_id = s.issuer_id
        LEFT JOIN market.industry ind ON ind.industry_id = v.industry_id
        WHERE sd.trading_date = :ngay AND s.status = 'listed'
          AND (cardinality(CAST(:mas AS text[])) = 0 OR upper(s.ticker) = ANY(:mas))
          AND (CAST(:nganh AS text) IS NULL OR ind.code = :nganh)
        ORDER BY s.ticker
        LIMIT :lim
    """), {"ngay": ngay, "mas": mas, "nganh": industry_code, "lim": TRAN_MA}).all()
    if not rows:
        return to_json({**rong(), "ngay_du_lieu": str(ngay)})

    units = {r.code: r.unit for r in conn.execute(sa.text(
        "SELECT code, unit FROM market.metric_dictionary"
        " WHERE dictionary = 'field_dictionary' AND code = ANY(:c)"), {"c": codes})}
    du_lieu = []
    for r in rows:
        ct = {}
        for code in codes:
            v = (r.item or {}).get(code)
            s = display_metric(v, units.get(code)) if v is not None else None
            if s is not None:
                ct[LABELS[code]] = s
        du_lieu.append({"ma": r.ticker, "nganh": r.nganh, "chi_tieu": ct})
    return to_json(co_du_lieu(du_lieu, ngay_du_lieu=str(ngay)))
