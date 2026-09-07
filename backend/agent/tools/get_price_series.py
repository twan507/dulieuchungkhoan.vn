"""Chuỗi giá theo ngày của một mã cổ phiếu.

Kho CHỈ có giá cổ phiếu đang niêm yết — đo trên kho dev 2026-09-07: 1.523 mã `stock listed`,
**0 dòng** cho `security_type='index'` (18 chỉ số có danh tính nhưng không một điểm giá nào),
0 dòng cho `etf`, và **0/442** mã `delisted`. Vì vậy mọi loại khác 'stock' và mọi mã đã huỷ
niêm yết ra hình dạng "có mã, không có dữ liệu" — nói thẳng còn hơn để model đoán.

N5/G1 (review CHUẨN lát 10, vòng 2): TRAN_PHIEN cắt câm nếu không báo cờ — đo kho thật
2026-09-07, mã BT6 có 5.764 phiên (2002-04-18..2026-09-04); 356 mã đang niêm yết có >400 phiên
(trần cũ). `ORDER BY trading_date DESC LIMIT :lim` giữ các phiên GẦN NHẤT trong khoảng hỏi
(không phải phiên đầu khoảng) — hành vi này giữ nguyên vì hợp lý hơn cho câu hỏi thường gặp
("giá gần đây"), nhưng báo tường minh qua `da_cat`/`tong_khop` (cùng khuôn get_news.tim_tin)
và `ghi_chu` nói rõ đây là phiên gần nhất, không phải phiên đầu.

TRAN_PHIEN nới 400 -> 2000 (~8 năm phiên): chủ dự án chốt 2026-09-07 "nới các giới hạn thoải
mái ra, không phải sợ quá tốn kém token" — ngữ cảnh model 1 triệu token không thiếu chỗ chứa.
BT6 (5.764 phiên) vẫn vượt 2000 nên vẫn cần cờ da_cat cho các mã niêm yết lâu năm, nhưng 2000
đủ phủ phần lớn nhu cầu phân tích gần đây mà trần 400 cũ cắt mất.
"""
from __future__ import annotations

import sqlalchemy as sa

from agent.format import display_metric, format_date_vi
from agent.tools._shared import co_du_lieu, khong_co_du_lieu, kiem_ngay, resolve_ticker, rong, to_json

_LY_DO = {"index": "kho chưa có dữ liệu giá cho chỉ số",
          "etf": "kho chưa có dữ liệu giá cho chứng chỉ quỹ ETF",
          "fund_cert": "kho chưa có dữ liệu giá cho chứng chỉ quỹ"}
TRAN_PHIEN = 2000

_SQL_KHOANG = sa.text(
    "SELECT min(trading_date), max(trading_date) FROM market.price_daily WHERE security_id = :sid")


def gia_theo_ngay(conn: sa.Connection, ticker: str, from_date: str | None = None,
                  to_date: str | None = None, adjusted: bool = True) -> str:
    for loi in (kiem_ngay(from_date, "from_date"), kiem_ngay(to_date, "to_date")):
        if loi:
            return to_json(loi)
    ma = resolve_ticker(conn, ticker)
    if not ma["tim_thay"]:
        return to_json(ma)
    if ma["loai"] != "stock":
        return to_json({**khong_co_du_lieu(ma["loai"], _LY_DO.get(ma["loai"], "kho chưa có dữ liệu giá cho loại này")),
                        "ma": ma["ticker"]})
    if ma["trang_thai"] == "delisted":
        return to_json({**khong_co_du_lieu("stock", "mã đã huỷ niêm yết, kho chưa có giá lịch sử của mã huỷ"),
                        "ma": ma["ticker"], "trang_thai": "delisted"})

    cot = "close_adj" if adjusted else "close_raw"
    params = {"sid": ma["security_id"], "tu": from_date, "den": to_date}
    # N5/G1: đếm tổng số phiên KHỚP khoảng hỏi (trước LIMIT) để tính da_cat từ kết quả thật,
    # cùng khuôn get_news.tim_tin — không suy từ TRAN_PHIEN có bị vượt hay không (_shared.cap_limit).
    tong = conn.execute(sa.text(
        "SELECT count(*) FROM market.price_daily WHERE security_id = :sid"
        " AND (CAST(:tu AS date) IS NULL OR trading_date >= CAST(:tu AS date))"
        " AND (CAST(:den AS date) IS NULL OR trading_date <= CAST(:den AS date))"), params).scalar()
    # CAST(:x AS date) — KHÔNG viết :x::date, SQLAlchemy lặng lẽ bỏ tham số (CLAUDE.md §3 lát 10).
    rows = conn.execute(sa.text(f"""
        SELECT trading_date, {cot} AS dong_cua, open_value, highest_value, lowest_value
        FROM market.price_daily
        WHERE security_id = :sid
          AND (CAST(:tu AS date) IS NULL OR trading_date >= CAST(:tu AS date))
          AND (CAST(:den AS date) IS NULL OR trading_date <= CAST(:den AS date))
        ORDER BY trading_date DESC
        LIMIT :lim
    """), {**params, "lim": TRAN_PHIEN}).all()

    if not rows:
        tu, den = conn.execute(_SQL_KHOANG, {"sid": ma["security_id"]}).one()
        return to_json({**rong({"tu": str(tu), "den": str(den)} if tu else None), "ma": ma["ticker"]})

    du_lieu = [{"ngay": str(r.trading_date), "ngay_hien_thi": format_date_vi(r.trading_date),
                "dong_cua": display_metric(r.dong_cua, "VND"),
                "mo_cua": display_metric(r.open_value, "VND"),
                "cao_nhat": display_metric(r.highest_value, "VND"),
                "thap_nhat": display_metric(r.lowest_value, "VND")} for r in reversed(rows)]
    da_cat = tong > len(rows)
    ghi_chu = "kho chưa có khối lượng giao dịch theo ngày"
    if da_cat:
        ghi_chu += (f"; đã cắt còn {len(rows)}/{tong} phiên GẦN NHẤT trong khoảng hỏi"
                    " (không phải phiên đầu khoảng)")
    return to_json(co_du_lieu(du_lieu, ma=ma["ticker"], gia_dieu_chinh=adjusted,
                              da_cat=da_cat, tong_khop=tong, ghi_chu=ghi_chu))
