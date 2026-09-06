"""Lọc và xếp hạng cổ phiếu theo chỉ tiêu screener của phiên gần nhất.

Nguồn market.screener_daily: payload->'stockScreenerItem' chứa ~70 khoá mã chỉ tiêu. Chỉ
chấp nhận mã nằm trong BẢNG NHÃN ĐÓNG — mã ngoài bảng bị từ chối kèm danh sách hợp lệ, vì
tên hiển thị không suy được và đơn vị có thể sai (prf/rev: tên nói "tỉ đồng", unit nói VND).

Join market.metric_dictionary PHẢI khoá dictionary='field_dictionary': PK là (dictionary,
code), cùng một code có thể tồn tại song song ở 'screener_params' — không khoá sẽ nhân đôi
dòng trên kho thật (CLAUDE.md §3 lát 10).
"""
from __future__ import annotations

import sqlalchemy as sa

from agent.format import display_metric
from agent.labels import DEFAULT_RATIOS, LABELS
from agent.tools._shared import cap_limit, co_du_lieu, rong, to_json

TOAN_TU = {">": ">", "<": "<", ">=": ">=", "<=": "<=", "=": "="}
_KEY = "payload->'stockScreenerItem'->>"


def _don_vi(conn: sa.Connection) -> dict[str, str | None]:
    return {r.code: r.unit for r in conn.execute(sa.text(
        "SELECT code, unit FROM market.metric_dictionary"
        " WHERE dictionary = 'field_dictionary' AND code = ANY(:c)"),
        {"c": list(LABELS)})}


def loc_co_phieu(conn: sa.Connection, criteria: list[dict] | None = None,
                 industry_code: str | None = None, exchange: str | None = None,
                 sort_by: str | None = None, limit: int | None = None) -> str:
    criteria = list(criteria or [])
    xin = [c.get("metric_code") for c in criteria] + ([sort_by] if sort_by else [])
    la = [c for c in xin if c and c not in LABELS]
    if la:
        return to_json({"loi": True, "ly_do": f"ma chi tieu ngoai bang nhan: {la}", "ma_hop_le": sorted(LABELS)})
    for c in criteria:
        if c.get("operator") not in TOAN_TU:
            return to_json({"loi": True, "ly_do": f"toan tu la: {c.get('operator')}",
                            "toan_tu_hop_le": sorted(TOAN_TU)})

    ngay = conn.execute(sa.text("SELECT max(trading_date) FROM market.screener_daily")).scalar()
    if ngay is None:
        return to_json(rong())
    lim, da_cat = cap_limit(limit, 20, 50)
    sort = sort_by or "rtd11"
    dieu_kien, params = [], {"ngay": ngay, "nganh": industry_code, "san": exchange, "lim": lim}
    for i, c in enumerate(criteria):
        params[f"v{i}"] = c["value"]
        dieu_kien.append(f"({_KEY}'{c['metric_code']}')::numeric {TOAN_TU[c['operator']]} :v{i}")
    where = (" AND " + " AND ".join(dieu_kien)) if dieu_kien else ""

    rows = conn.execute(sa.text(f"""
        SELECT s.ticker, s.exchange, ind.name_vi AS nganh, sd.payload->'stockScreenerItem' AS item
        FROM market.screener_daily sd
        JOIN market.security s USING (security_id)
        LEFT JOIN market.v_issuer_industry v ON v.issuer_id = s.issuer_id
        LEFT JOIN market.industry ind ON ind.industry_id = v.industry_id
        WHERE sd.trading_date = :ngay AND s.status = 'listed'
          AND (CAST(:nganh AS text) IS NULL OR ind.code = :nganh)
          AND (CAST(:san AS text) IS NULL OR s.exchange = :san)
          AND ({_KEY}'{sort}') IS NOT NULL
          {where}
        ORDER BY ({_KEY}'{sort}')::numeric DESC
        LIMIT :lim
    """), params).all()
    if not rows:
        return to_json({**rong(), "ngay_du_lieu": str(ngay)})

    units = _don_vi(conn)
    hien = [sort] + [c["metric_code"] for c in criteria] + DEFAULT_RATIOS
    thu_tu = list(dict.fromkeys(hien))
    du_lieu = []
    for r in rows:
        ct = {}
        for code in thu_tu:
            v = (r.item or {}).get(code)
            s = display_metric(v, units.get(code)) if v is not None else None
            if s is not None:
                ct[LABELS[code]] = s
        du_lieu.append({"ma": r.ticker, "san": r.exchange, "nganh": r.nganh, "chi_tieu": ct})
    return to_json(co_du_lieu(du_lieu, ngay_du_lieu=str(ngay), da_cat=da_cat))
