"""Cây ngành riêng 6 nhóm × 24 ngành, và ngành đã phân giải của một mã.

KHÔNG có tham số icb_level và KHÔNG trả cây ICB: bộ ngành riêng là chuẩn duy nhất khi hiển
thị và phân tích, ICB chỉ là đường nạp nhanh ở tầng ETL (industry-tree.md §1).
Đọc ngành của doanh nghiệp PHẢI qua view market.v_issuer_industry — đọc thẳng
issuer.industry_id là bỏ qua lớp gán tay (market.issuer_industry_override).
"""
from __future__ import annotations

import sqlalchemy as sa

from agent.tools._shared import khong_tim_thay, resolve_ticker, to_json

_SQL_NGANH_CUA_MA = sa.text("""
    SELECT ind.code, ind.name_vi, par.code AS nhom_ma, par.name_vi AS nhom_ten, v.source
    FROM market.v_issuer_industry v
    JOIN market.industry ind ON ind.industry_id = v.industry_id
    LEFT JOIN market.industry par ON par.industry_id = ind.parent_id
    WHERE v.issuer_id = :iid
""")

# CAST(:x AS text) — KHÔNG viết :x::text, SQLAlchemy lặng lẽ bỏ tham số (CLAUDE.md §3 lát 10).
_SQL_CAY = sa.text("""
    SELECT par.code AS nhom_ma, par.name_vi AS nhom_ten, ind.code, ind.name_vi
    FROM market.industry ind
    JOIN market.industry par ON par.industry_id = ind.parent_id
    WHERE ind.level = 2 AND (CAST(:ma AS text) IS NULL OR ind.code = :ma OR par.code = :ma)
    ORDER BY par.sort_order, ind.sort_order
""")

# Gợi ý khi industry_code không khớp mã nhóm/mã ngành nào — cùng khuôn _shared._SQL_GOI_Y,
# nhưng trên market.industry (cả hai cấp, vì _SQL_CAY ở trên chấp nhận mã của CẢ nhóm lẫn
# ngành). F5 (review CHUẨN lát 10, vòng 3).
_SQL_GOI_Y_NGANH = sa.text("""
    SELECT code
    FROM market.industry
    WHERE extensions.similarity(upper(code), upper(:ma)) > 0.3
       OR extensions.similarity(name_vi, :ma) > 0.3
    ORDER BY extensions.similarity(upper(code), upper(:ma)) DESC
    LIMIT 5
""")


def cay_nganh(conn: sa.Connection, industry_code: str | None = None, ticker: str | None = None) -> str:
    if ticker:
        ma = resolve_ticker(conn, ticker)
        if not ma["tim_thay"]:
            return to_json(ma)
        row = conn.execute(_SQL_NGANH_CUA_MA, {"iid": ma["issuer_id"]}).first()
        if row is None or row.code is None:
            return to_json({"tim_thay": True, "co_du_lieu": False, "ma": ma["ticker"],
                            "ly_do": "mã này chưa được gán ngành (quỹ/ETF theo thiết kế không có ngành)"})
        return to_json({"tim_thay": True, "co_du_lieu": True, "ma": ma["ticker"],
                        "nganh": {"ma": row.code, "ten": row.name_vi},
                        "nhom": {"ma": row.nhom_ma, "ten": row.nhom_ten},
                        "nguon_gan": row.source})

    rows = conn.execute(_SQL_CAY, {"ma": industry_code}).all()
    # F5 (review CHUẨN lát 10, vòng 3): industry_code KHÔNG khớp mã nhóm/mã ngành nào ra 0
    # dòng — đây là một MÃ KHÔNG TỒN TẠI, cùng bản chất với ticker bịa (hình dạng #1), KHÔNG
    # phải "mã ngành có thật nhưng chưa có ngành con nào". Bản sửa trước (F7, vòng 2) gộp
    # nhầm ca này vào tim_thay=True cứng, kèm một bình luận nói hình dạng đó "đúng khuôn
    # khong_co_du_lieu/rong ở _shared.py" — SAI, không khuôn nào như vậy tồn tại:
    # khong_co_du_lieu() luôn kèm loai+ly_do, rong() luôn co_du_lieu=True. industry_code=None
    # (lấy toàn bộ cây) không rơi vào nhánh này trên kho thật vì 24 ngành cấp 2 luôn được
    # migration 0002/0011/0013 seed sẵn.
    if not rows and industry_code:
        goi_y = [r[0] for r in conn.execute(_SQL_GOI_Y_NGANH, {"ma": industry_code})]
        return to_json(khong_tim_thay(industry_code, goi_y))
    nhom: dict[str, dict] = {}
    for r in rows:
        nhom.setdefault(r.nhom_ma, {"ma": r.nhom_ma, "ten": r.nhom_ten, "nganh": []})
        nhom[r.nhom_ma]["nganh"].append({"ma": r.code, "ten": r.name_vi})
    return to_json({"tim_thay": True, "co_du_lieu": len(rows) > 0, "so_dong": len(rows),
                    "nhom": list(nhom.values())})
