"""Sự kiện doanh nghiệp: cổ tức, đại hội, phát hành, IPO, ngày công bố kết quả.

Kho có 110.804 dòng (đo 2026-09-07), 6 loại — đúng danh sách CHECK constraint của
market.corporate_event.event_type. payload jsonb nhiều trường rỗng — chỉ phơi những trường có
nghĩa và ĐỪNG suy ra tỷ lệ chi trả khi kho không có (payload không lưu tỷ lệ chi trả cổ tức).
"""
from __future__ import annotations

import sqlalchemy as sa

from agent.format import format_date_vi
from agent.tools._shared import cap_limit, co_du_lieu, resolve_ticker, rong, to_json

LOAI = ["Earning", "AGM", "CashDividend", "ShareIssuance", "StockDividend", "IPO"]

# CAST(:x AS type) — KHÔNG viết :x::type, SQLAlchemy lặng lẽ bỏ tham số (CLAUDE.md §3 lát 10).
_SQL_SU_KIEN = sa.text("""
    SELECT ce.event_type, ce.public_date, ce.exright_date, ce.record_date, ce.payout_date,
           ce.year_report, ce.length_report
    FROM market.corporate_event ce
    WHERE ce.issuer_id = :iid
      AND (CAST(:loai AS text) IS NULL OR ce.event_type = :loai)
      AND (CAST(:tu AS date) IS NULL OR ce.public_date >= CAST(:tu AS date))
      AND (CAST(:den AS date) IS NULL OR ce.public_date <= CAST(:den AS date))
    ORDER BY ce.public_date DESC NULLS LAST
    LIMIT :lim
""")


def su_kien_doanh_nghiep(conn: sa.Connection, ticker: str, event_type: str | None = None,
                         from_date: str | None = None, to_date: str | None = None,
                         limit: int | None = None) -> str:
    if event_type and event_type not in LOAI:
        return to_json({"loi": True, "ly_do": f"khong co loai su kien '{event_type}'", "loai_hop_le": LOAI})
    ma = resolve_ticker(conn, ticker)
    if not ma["tim_thay"]:
        return to_json(ma)
    lim = cap_limit(limit, 20, 50)
    rows = conn.execute(_SQL_SU_KIEN, {"iid": ma["issuer_id"], "loai": event_type,
                                       "tu": from_date, "den": to_date, "lim": lim}).all()
    if not rows:
        return to_json({**rong(), "ma": ma["ticker"]})
    du_lieu = []
    for r in rows:
        e = {"loai": r.event_type, "ngay_cong_bo": str(r.public_date) if r.public_date else None}
        if r.exright_date:
            e["ngay_gdkhq"] = str(r.exright_date)
            e["ngay_gdkhq_hien_thi"] = format_date_vi(r.exright_date)
        if r.payout_date:
            e["ngay_thanh_toan"] = str(r.payout_date)
        if r.year_report:
            e["ky"] = f"{r.year_report}" + (f" quý {r.length_report}" if r.length_report and r.length_report < 5 else "")
        du_lieu.append(e)
    return to_json(co_du_lieu(du_lieu, ma=ma["ticker"], da_cat=len(rows) >= lim,
                              ghi_chu="kho không lưu tỷ lệ chi trả của các đợt cổ tức"))
