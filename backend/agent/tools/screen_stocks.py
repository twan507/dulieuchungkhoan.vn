"""Lọc và xếp hạng cổ phiếu theo chỉ tiêu screener của phiên gần nhất.

Nguồn market.screener_daily: payload->'stockScreenerItem' chứa ~70 khoá mã chỉ tiêu. Chỉ
chấp nhận mã nằm trong BẢNG NHÃN ĐÓNG — mã ngoài bảng bị từ chối kèm danh sách hợp lệ, vì
tên hiển thị không suy được và đơn vị có thể sai (prf/rev: tên nói "tỉ đồng", unit nói VND).

Join market.metric_dictionary PHẢI khoá dictionary='field_dictionary': PK là (dictionary,
code), schema CHO PHÉP cùng một code tồn tại song song ở 'screener_params' — khoá dictionary
là phòng thủ cho khả năng đó, không phải vì đã xảy ra: đo kho thật 2026-09-07 chỉ có
'field_dictionary' (729 dòng), 0 dòng 'screener_params' (CLAUDE.md §3 lát 10).

`criteria` do MODEL sinh (không qua schema kiểm sâu từng phần tử) nên có thể thiếu khoá hay
sai kiểu — mọi hình dạng lạ phải ra {"loi": True, ...} có cấu trúc, không được ném exception
làm hỏng vòng chat (N6, review CHUẨN lát 10).
"""
from __future__ import annotations

import sqlalchemy as sa

from agent.format import display_metric
from agent.labels import DEFAULT_RATIOS, LABELS
from agent.tools._shared import cap_limit, co_du_lieu, rong, to_json

TOAN_TU = {">": ">", "<": "<", ">=": ">=", "<=": "<=", "=": "="}
_KEY = "payload->'stockScreenerItem'->>"
_KHOA_CAN = {"metric_code", "operator", "value"}


def _don_vi(conn: sa.Connection) -> dict[str, str | None]:
    return {r.code: r.unit for r in conn.execute(sa.text(
        "SELECT code, unit FROM market.metric_dictionary"
        " WHERE dictionary = 'field_dictionary' AND code = ANY(:c)"),
        {"c": list(LABELS)})}


def loc_co_phieu(conn: sa.Connection, criteria: list[dict] | None = None,
                 industry_code: str | None = None, exchange: str | None = None,
                 sort_by: str | None = None, limit: int | None = None) -> str:
    criteria = list(criteria or [])
    # N6: criteria do model sinh, có thể thiếu khoá hoặc không phải object — kiểm HÌNH DẠNG
    # trước khi đụng vào bất kỳ khoá nào, để không ném KeyError/AttributeError giữa vòng chat.
    sai_dang = [c for c in criteria if not isinstance(c, dict) or not _KHOA_CAN <= c.keys()]
    if sai_dang:
        return to_json({"loi": True, "tieu_chi_loi": [repr(c) for c in sai_dang],
                        "ly_do": "moi tieu chi phai la object co du ba khoa metric_code/operator/value"})
    xin = [c["metric_code"] for c in criteria] + ([sort_by] if sort_by else [])
    # Whitelist theo isinstance, KHÔNG theo truthiness — `if c and ...` từng bỏ lọt None/''/0
    # (giá trị falsy) qua vòng kiểm, dù chúng vẫn được nội suy vào f-string SQL bên dưới.
    la = [c for c in xin if not isinstance(c, str) or c not in LABELS]
    if la:
        return to_json({"loi": True, "ly_do": f"ma chi tieu ngoai bang nhan: {la}", "ma_hop_le": sorted(LABELS)})
    for c in criteria:
        if c["operator"] not in TOAN_TU:
            return to_json({"loi": True, "ly_do": f"toan tu la: {c['operator']}",
                            "toan_tu_hop_le": sorted(TOAN_TU)})
        # F6 (review CHUẨN lát 10, vòng 2): Python coi bool LÀ con của int nên
        # isinstance(True, (int, float)) == True — phải chặn bool tường minh trước, không thì
        # value: true lọt qua vòng kiểm rồi chết ở tầng SQL (ProgrammingError, không phải lỗi
        # có cấu trúc mà file này trả cho mọi ca khác).
        if isinstance(c["value"], bool) or not isinstance(c["value"], (int, float)):
            return to_json({"loi": True, "ly_do": f"value phai la so, nhan duoc: {c['value']!r}"})

    ngay = conn.execute(sa.text("SELECT max(trading_date) FROM market.screener_daily")).scalar()
    if ngay is None:
        return to_json(rong())
    # Trần 30/200 (cũ 20/50) — chủ dự án chốt 2026-09-07: "nới các giới hạn thoải mái ra,
    # không phải sợ quá tốn kém token". Ngữ cảnh model là 1 triệu token nên chỗ chứa không
    # phải vấn đề; trần chỉ còn tác dụng bắt ca bệnh (model xin số dòng phi lý), không chặn
    # ca dùng bình thường (CLAUDE.md không ghi số này — quyết định nằm ở phiên làm việc).
    lim = cap_limit(limit, 30, 200)
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
    return to_json(co_du_lieu(du_lieu, ngay_du_lieu=str(ngay), da_cat=len(rows) >= lim))
