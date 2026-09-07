"""Báo cáo tài chính dạng dài.

Bảng 27,3 triệu dòng (đo 2026-09-07) ⇒ MỌI truy vấn lọc issuer_id trước, rồi mới lọc năm và
mã chỉ tiêu; trần 8 kỳ. length_report: 1..4 = quý, 5 = CẢ NĂM (không phải quý 5).
canonical_code NULL toàn bộ nên đừng dùng nó. Tên hiển thị lấy từ bảng nhãn đóng, KHÔNG tra
name_vi (tên không duy nhất — isa20/isa22 cùng name_vi "LỢI NHUẬN THUẦN" trong nguồn).

Join metric_dictionary CHỈ trên dictionary='field_dictionary': PK là (dictionary, code) —
schema CHO PHÉP cùng một code tồn tại song song ở 'screener_params' (xem
test_metric_dictionary_two_dicts, backend/tests/schema/test_s03_market_data.py), khoá
dictionary là phòng thủ cho khả năng đó. Đo kho thật 2026-09-07: chỉ có 'field_dictionary'
(729 dòng), 0 dòng 'screener_params' — chưa từng nhân đôi trên kho thật, chỉ là phòng khi có.
"""
from __future__ import annotations

import sqlalchemy as sa

from agent.format import display_metric
from agent.labels import DEFAULT_BY_STATEMENT, LABELS
from agent.tools._shared import khong_co_du_lieu, resolve_ticker, rong, to_json

TRAN_KY = 8

# hình dạng #2 (spec §4.6): kho chỉ có báo cáo tài chính của DOANH NGHIỆP (issuer), nên chỉ số
# và ETF/chứng chỉ quỹ không bao giờ có — khác hẳn "mã cổ phiếu đúng nhưng khoảng năm rỗng".
_LY_DO = {"index": "kho không có báo cáo tài chính cho chỉ số",
          "etf": "kho không có báo cáo tài chính cho chứng chỉ quỹ ETF",
          "fund_cert": "kho không có báo cáo tài chính cho chứng chỉ quỹ"}

# CAST(:x AS type) — KHÔNG viết :x::type, SQLAlchemy lặng lẽ bỏ tham số (CLAUDE.md §3 lát 10).
_SQL_BCTC = sa.text("""
    SELECT fs.year_report, fs.length_report, fs.metric_code, fs.value, md.unit
    FROM market.financial_statement fs
    LEFT JOIN market.metric_dictionary md
           ON md.dictionary = 'field_dictionary' AND md.code = fs.metric_code
    WHERE fs.issuer_id = :iid
      AND fs.statement_type = :st
      AND fs.length_report = ANY(:lens)
      AND fs.metric_code = ANY(:codes)
      AND (CAST(:tu AS int) IS NULL OR fs.year_report >= CAST(:tu AS int))
      AND (CAST(:den AS int) IS NULL OR fs.year_report <= CAST(:den AS int))
    ORDER BY fs.year_report DESC, fs.length_report
""")


def bao_cao_tai_chinh(conn: sa.Connection, ticker: str, statement_type: str = "IS",
                      from_year: int | None = None, to_year: int | None = None,
                      period: str = "nam", metric_codes: list[str] | None = None) -> str:
    codes = list(metric_codes or []) or DEFAULT_BY_STATEMENT.get(statement_type, [])
    ma_la = [c for c in codes if c not in LABELS]
    if ma_la:
        return to_json({"loi": True, "ly_do": f"ma chi tieu ngoai bang nhan: {ma_la}",
                        "ma_hop_le": sorted(LABELS)})
    ma = resolve_ticker(conn, ticker)
    if not ma["tim_thay"]:
        return to_json(ma)
    if ma["loai"] != "stock":
        return to_json({**khong_co_du_lieu(ma["loai"], _LY_DO.get(ma["loai"], "kho không có báo cáo tài chính cho loại này")),
                        "ma": ma["ticker"]})

    lengths = [5] if period == "nam" else [1, 2, 3, 4]
    rows = conn.execute(_SQL_BCTC, {"iid": ma["issuer_id"], "st": statement_type, "lens": lengths,
                                    "codes": codes, "tu": from_year, "den": to_year}).all()
    if not rows:
        return to_json({**rong(), "ma": ma["ticker"]})

    ky: dict[tuple[int, int], list[dict]] = {}
    for r in rows:
        gia_tri = display_metric(r.value, r.unit)
        if gia_tri is None:
            continue
        ky.setdefault((r.year_report, r.length_report), []).append(
            {"ten": LABELS[r.metric_code], "gia_tri": gia_tri})
    khoa = sorted(ky, reverse=True)
    da_cat = len(khoa) > TRAN_KY
    du_lieu = [{"nam": k[0], **({"quy": k[1]} if k[1] != 5 else {}), "chi_tieu": ky[k]}
               for k in khoa[:TRAN_KY]]
    return to_json({"tim_thay": True, "co_du_lieu": True, "so_dong": len(du_lieu),
                    "ma": ma["ticker"], "loai_bao_cao": statement_type,
                    "du_lieu": du_lieu, "da_cat": da_cat})
