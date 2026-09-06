"""Tìm tin trong kho.

Hai đường lọc khác nhau, đừng trộn:
  query      -> tìm toàn văn trên TOÀN BỘ article_revision, kể cả bài chưa có nhãn AI
  nhãn       -> group_no/sub/industry_code/ticker, CHỈ khớp bài đã phân loại
Bài chưa nhãn là trạng thái TẠM (sẽ backfill khi lên prod) nên không có nhánh code riêng —
chỉ có cờ da_phan_loai và ghi_chu; backfill xong thì cờ luôn true, không phải sửa gì.

tsv của article_revision sinh bằng to_tsvector('simple', news.immutable_unaccent(title || ' '
|| content)) (migration 0007) — câu hỏi PHẢI bọc cùng news.immutable_unaccent, quên là khớp 0
bài. Ưu tiên phraseto_tsquery (khớp ĐÚNG CỤM); ra 0 bài mới lùi về plainto_tsquery (khớp theo
TỪ, không cần liền nhau), và luôn trả kèm kieu_tim để model biết đã lùi hay chưa.

SUBS: 21 mã hiện hành sau migration 0019 (thêm '2f' 2026-09-06) — nhóm 3 chạy tới 'i' (9 mã),
không phải 'e' như bản nháp đầu của plan; chốt bằng CHECK constraint article_sub_check thật.
"""
from __future__ import annotations

import sqlalchemy as sa

from agent.format import format_date_vi
from agent.tools._shared import cap_limit, co_du_lieu, to_json

SUBS = [f"{g}{c}" for g, cs in ((1, "abcdef"), (2, "abcdef"), (3, "abcdefghi")) for c in cs]

# CAST(:x AS type) — KHÔNG viết :x::type, SQLAlchemy lặng lẽ bỏ tham số (CLAUDE.md §3 lát 10).
_DIEU_KIEN_NHAN = [
    "(CAST(:tu AS date) IS NULL OR a.published_at >= CAST(:tu AS date))",
    "(CAST(:den AS date) IS NULL OR a.published_at < (CAST(:den AS date) + 1))",
    "(CAST(:g AS int) IS NULL OR a.group_no = :g)",
    "(CAST(:sub AS text) IS NULL OR a.sub = :sub)",
]
_DIEU_KIEN_TICKER = (
    "EXISTS (SELECT 1 FROM news.article_ticker t JOIN market.security s USING (security_id)"
    " WHERE t.article_id = a.article_id AND upper(s.ticker) = :tk)"
)
_DIEU_KIEN_NGANH = (
    "EXISTS (SELECT 1 FROM news.article_industry ai JOIN market.industry i USING (industry_id)"
    " WHERE ai.article_id = a.article_id AND i.code = :nganh)"
)


def tim_tin(conn: sa.Connection, query: str | None = None, ticker: str | None = None,
            group_no: int | None = None, sub: str | None = None, industry_code: str | None = None,
            from_date: str | None = None, to_date: str | None = None, limit: int | None = None) -> str:
    if sub and sub not in SUBS:
        return to_json({"loi": True, "ly_do": f"khong co sub '{sub}'", "sub_hop_le": SUBS})
    lim, da_cat = cap_limit(limit, 10, 30)
    p = {"q": query, "tk": ticker.upper() if ticker else None, "g": group_no, "sub": sub,
         "nganh": industry_code, "tu": from_date, "den": to_date, "lim": lim}

    dk = list(_DIEU_KIEN_NHAN)
    if ticker:
        dk.append(_DIEU_KIEN_TICKER)
    if industry_code:
        dk.append(_DIEU_KIEN_NGANH)
    where = " AND ".join(dk)

    kieu = None
    if query:
        for kieu_thu, ham in (("cum", "phraseto_tsquery"), ("tu_khoa", "plainto_tsquery")):
            sql_dem = f"""
                SELECT count(*) FROM news.article a JOIN news.article_revision r USING (article_id)
                WHERE r.tsv @@ {ham}('simple', news.immutable_unaccent(:q)) AND {where}"""
            tong = conn.execute(sa.text(sql_dem), p).scalar()
            if tong:
                kieu = kieu_thu
                break
        else:
            return to_json({"tim_thay": True, "co_du_lieu": True, "so_dong": 0, "tong_khop": 0,
                            "kieu_tim": "cum", "du_lieu": []})
        sql = f"""
            SELECT a.article_id, a.published_at, a.primary_source, a.group_no, a.sub,
                   a.classified_from IS NOT NULL AS da_phan_loai, r.title, r.sapo, r.summary_ai,
                   ts_rank(r.tsv, {ham}('simple', news.immutable_unaccent(:q))) AS diem
            FROM news.article a JOIN news.article_revision r USING (article_id)
            WHERE r.tsv @@ {ham}('simple', news.immutable_unaccent(:q)) AND {where}
            ORDER BY diem DESC, a.published_at DESC LIMIT :lim"""
    else:
        tong = conn.execute(sa.text(
            f"SELECT count(*) FROM news.article a WHERE {where}"), p).scalar()
        sql = f"""
            SELECT a.article_id, a.published_at, a.primary_source, a.group_no, a.sub,
                   a.classified_from IS NOT NULL AS da_phan_loai, r.title, r.sapo, r.summary_ai
            FROM news.article a JOIN news.article_revision r USING (article_id)
            WHERE {where}
            ORDER BY a.published_at DESC LIMIT :lim"""

    rows = conn.execute(sa.text(sql), p).all()
    du_lieu = [{"tieu_de": r.title, "ngay": str(r.published_at.date()),
                "ngay_hien_thi": format_date_vi(r.published_at), "bao": r.primary_source,
                "nhom": r.group_no, "sub": r.sub, "da_phan_loai": bool(r.da_phan_loai),
                "tom_tat": r.summary_ai or r.sapo} for r in rows]
    out = co_du_lieu(du_lieu, tong_khop=tong, da_cat=da_cat)
    if kieu:
        out["kieu_tim"] = kieu
    if not du_lieu and (group_no or sub or industry_code or ticker):
        chua = conn.execute(sa.text(
            "SELECT count(*) FROM news.article a WHERE a.classified_from IS NULL"
            " AND (CAST(:tu AS date) IS NULL OR a.published_at >= CAST(:tu AS date))"
            " AND (CAST(:den AS date) IS NULL OR a.published_at < (CAST(:den AS date) + 1))"), p).scalar()
        out["ghi_chu"] = (f"không có bài nào khớp nhãn; trong khoảng này còn {chua} bài "
                          f"chưa phân loại nên chưa thể lọc theo nhãn")
    return to_json(out)
