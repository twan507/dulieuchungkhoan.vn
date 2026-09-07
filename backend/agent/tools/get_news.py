"""Tìm tin trong kho.

Hai đường lọc khác nhau, đừng trộn:
  query      -> tìm toàn văn trên TOÀN BỘ article_revision, kể cả bài chưa có nhãn AI
  nhãn       -> group_no/sub/industry_code/ticker, CHỈ khớp bài đã phân loại
Bài chưa nhãn là trạng thái TẠM (sẽ backfill khi lên prod) nên không có nhánh code riêng —
chỉ có cờ da_phan_loai và ghi_chu; backfill xong thì cờ luôn true, không phải sửa gì.

`ticker` phải qua resolve_ticker TRƯỚC khi lọc (spec §4.6 hình dạng #1): mã không tồn tại phải
báo tim_thay=False, không được rơi vào nhánh "lọc theo nhãn ra 0 dòng" rồi bị gán nhầm lý do
"chưa phân loại" — đó là giải thích SAI NGUYÊN NHÂN (review SPEC lát 10 §2.1).

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
from agent.tools._shared import cap_limit, co_du_lieu, kiem_industry_code, kiem_ngay, resolve_ticker, to_json

SUBS = [f"{g}{c}" for g, cs in ((1, "abcdef"), (2, "abcdef"), (3, "abcdefghi")) for c in cs]

# CHECK constraint thật (migration 0007): group_no smallint CHECK (group_no BETWEEN 1 AND 3).
# Nhóm 'x' (tin bị loại) KHÔNG có mặt ở đây — nó biểu diễn bằng group_no NULL (xem migration),
# nên không phải một giá trị group_no có thể hỏi được qua tham số int này.
GROUP_NO_HOP_LE = [1, 2, 3]

# CLAUDE.md §3.1: published_at là timestamptz, phiên Postgres chạy Etc/UTC — so/hiển thị "ngày"
# PHẢI ép sang Asia/Ho_Chi_Minh trước khi lấy ::date, không được để mặc định so theo ngày UTC
# (khuôn đã có ở fundamentals_store.py:121, snapshot_store.py:125).
_NGAY_VN = "(a.published_at AT TIME ZONE 'Asia/Ho_Chi_Minh')::date"

# CAST(:x AS type) — KHÔNG viết :x::type, SQLAlchemy lặng lẽ bỏ tham số (CLAUDE.md §3 lát 10).
_DIEU_KIEN_NHAN = [
    f"(CAST(:tu AS date) IS NULL OR {_NGAY_VN} >= CAST(:tu AS date))",
    f"(CAST(:den AS date) IS NULL OR {_NGAY_VN} <= CAST(:den AS date))",
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
# N1: khoá bản mới nhất — khuôn giống news_classify.py:110,119. Không khoá version thì một bài
# có 2 revision (news_store.add_revision chèn version+1 khi nội dung đổi) sẽ nhân đôi trong kết quả.
#
# F4 (review CHUẨN lát 10, vòng 2): bản N1 ban đầu viết bằng JOIN LATERAL (...ORDER BY version
# DESC LIMIT 1) — cách này đẩy vị từ `r.tsv @@ ...` ra NGOÀI subquery nên Postgres không còn
# đường nào dùng GIN article_revision_tsv_idx, ép quét backward-index TỪNG bài một (nested
# loop, N vòng lặp = N bài). Viết lại bằng JOIN thẳng + NOT EXISTS (anti-join) để vị từ tsv nằm
# ngay trên bảng article_revision — đo lại trên kho thật 2026-09-07, câu đếm cho query 'lãi
# suất điều hành' (8.179 revision, trung bình 3 lần chạy mỗi bản):
#   JOIN LATERAL (bản cũ) : cost=68.307  buffers=51.489  ~28-35 ms
#   JOIN + NOT EXISTS      : cost=2.062   buffers=28.994  ~22-23 ms  (mặc định planner)
# Ép SET LOCAL enable_seqscan=off cho bản LATERAL KHÔNG đổi được kế hoạch (vẫn nested loop —
# chặn cấu trúc, không phải chuyện thống kê); cùng lệnh đó cho bản JOIN+NOT EXISTS chuyển hẳn
# sang Bitmap Index Scan trên article_revision_tsv_idx, còn ~6 ms — planner mặc định vẫn chọn
# Seq Scan cho bảng 8k dòng này vì content bị TOAST hoá nặng khiến ước lượng chi phí seq scan
# thấp hơn ước lượng bitmap dù thực đo chậm hơn; không ép enable_seqscan trong code (rủi ro
# cho câu lệnh khác cùng phiên), chỉ sửa cấu trúc để planner CÓ ĐƯỜNG dùng GIN khi kho lớn lên.
_REV_MOI_NHAT = "JOIN news.article_revision r ON r.article_id = a.article_id"
_REV_LA_MOI_NHAT = (
    "NOT EXISTS (SELECT 1 FROM news.article_revision r2"
    " WHERE r2.article_id = r.article_id AND r2.version > r.version)"
)


def tim_tin(conn: sa.Connection, query: str | None = None, ticker: str | None = None,
            group_no: int | None = None, sub: str | None = None, industry_code: str | None = None,
            from_date: str | None = None, to_date: str | None = None, limit: int | None = None) -> str:
    if sub and sub not in SUBS:
        return to_json({"loi": True, "ly_do": f"khong co sub '{sub}'", "sub_hop_le": SUBS})
    if group_no is not None and group_no not in GROUP_NO_HOP_LE:
        return to_json({"loi": True, "ly_do": f"khong co nhom '{group_no}'", "group_no_hop_le": GROUP_NO_HOP_LE})
    for loi in (kiem_ngay(from_date, "from_date"), kiem_ngay(to_date, "to_date")):
        if loi:
            return to_json(loi)
    if industry_code:
        loi = kiem_industry_code(conn, industry_code)
        if loi:
            return to_json(loi)
    # spec §4.6 hình dạng #1: ticker phải tra được TRƯỚC khi lọc, không thì mã không tồn tại
    # rơi vào nhánh "lọc theo nhãn ra 0 dòng" và bị gán nhầm lý do "chưa phân loại" (§2.1).
    ma = resolve_ticker(conn, ticker) if ticker else None
    if ma is not None and not ma["tim_thay"]:
        return to_json(ma)
    # Trần 15/100 (cũ 10/30) — chủ dự án chốt 2026-09-07: nới trần thoải mái, ngữ cảnh model
    # 1 triệu token không thiếu chỗ chứa; trần chỉ còn để bắt ca bệnh, không chặn ca thường.
    lim = cap_limit(limit, 15, 100)
    p = {"q": query, "tk": ma["ticker"] if ma else None, "g": group_no, "sub": sub,
         "nganh": industry_code, "tu": from_date, "den": to_date, "lim": lim}

    dk = list(_DIEU_KIEN_NHAN)
    if ticker:
        dk.append(_DIEU_KIEN_TICKER)
    if industry_code:
        dk.append(_DIEU_KIEN_NGANH)
    where = " AND ".join(dk)

    # N2 (review SPEC lát 10, vòng 3): khi khoảng hỏi (from_date/to_date) làm 0 dòng khớp,
    # phải nói kho THẬT SỰ có bài khớp các bộ lọc còn lại (nhãn/từ khoá) ở khoảng nào — cùng
    # nguyên tắc khoang_co_du_lieu đã vá ở get_price_series/get_financials/get_corporate_events.
    # Bỏ vị từ ngày (tu/den ép về None, _DIEU_KIEN_NHAN tự IS NULL) nhưng GIỮ NGUYÊN mọi bộ
    # lọc khác (nhãn, và vị từ tsv nếu có) để không lẫn "hỏi sai ngày" với "chủ đề kho không có".
    def _khoang_khop(dieu_kien_tsv: str | None) -> dict | None:
        dk_tsv = f"{dieu_kien_tsv} AND " if dieu_kien_tsv else ""
        tu, den = conn.execute(sa.text(
            f"SELECT min({_NGAY_VN}), max({_NGAY_VN}) FROM news.article a {_REV_MOI_NHAT}"
            f" WHERE {dk_tsv}{where} AND {_REV_LA_MOI_NHAT}"), {**p, "tu": None, "den": None}).one()
        return {"tu": str(tu), "den": str(den)} if tu is not None else None

    kieu = None
    if query:
        for kieu_thu, ham in (("cum", "phraseto_tsquery"), ("tu_khoa", "plainto_tsquery")):
            sql_dem = f"""
                SELECT count(*) FROM news.article a {_REV_MOI_NHAT}
                WHERE r.tsv @@ {ham}('simple', news.immutable_unaccent(:q))
                  AND {where} AND {_REV_LA_MOI_NHAT}"""
            tong = conn.execute(sa.text(sql_dem), p).scalar()
            if tong:
                kieu = kieu_thu
                break
        else:
            out_rong = {"tim_thay": True, "co_du_lieu": True, "so_dong": 0, "tong_khop": 0,
                        "kieu_tim": "cum", "du_lieu": []}
            if from_date or to_date:
                khoang = _khoang_khop(
                    "r.tsv @@ plainto_tsquery('simple', news.immutable_unaccent(:q))")
                if khoang:
                    out_rong["khoang_co_du_lieu"] = khoang
            return to_json(out_rong)
        sql = f"""
            SELECT a.article_id, {_NGAY_VN} AS ngay_vn, a.primary_source, a.group_no, a.sub,
                   a.classified_from IS NOT NULL AS da_phan_loai, r.title, r.sapo, r.summary_ai,
                   ts_rank(r.tsv, {ham}('simple', news.immutable_unaccent(:q))) AS diem
            FROM news.article a {_REV_MOI_NHAT}
            WHERE r.tsv @@ {ham}('simple', news.immutable_unaccent(:q))
              AND {where} AND {_REV_LA_MOI_NHAT}
            ORDER BY diem DESC, a.published_at DESC LIMIT :lim"""
    else:
        tong = conn.execute(sa.text(
            f"SELECT count(*) FROM news.article a WHERE {where}"), p).scalar()
        sql = f"""
            SELECT a.article_id, {_NGAY_VN} AS ngay_vn, a.primary_source, a.group_no, a.sub,
                   a.classified_from IS NOT NULL AS da_phan_loai, r.title, r.sapo, r.summary_ai
            FROM news.article a {_REV_MOI_NHAT}
            WHERE {where} AND {_REV_LA_MOI_NHAT}
            ORDER BY a.published_at DESC LIMIT :lim"""

    rows = conn.execute(sa.text(sql), p).all()
    du_lieu = [{"tieu_de": r.title, "ngay": str(r.ngay_vn),
                "ngay_hien_thi": format_date_vi(r.ngay_vn), "bao": r.primary_source,
                "nhom": r.group_no, "sub": r.sub, "da_phan_loai": bool(r.da_phan_loai),
                "tom_tat": r.summary_ai or r.sapo} for r in rows]
    # N2: da_cat từ SỐ DÒNG THẬT (tong đã đếm ở trên), không suy từ việc limit đầu vào có vượt
    # trần input hay không — cap_limit không còn biết chuyện đó (xem _shared.cap_limit).
    out = co_du_lieu(du_lieu, tong_khop=tong, da_cat=tong > len(du_lieu))
    if kieu:
        out["kieu_tim"] = kieu
    if not du_lieu and not query and (from_date or to_date):
        # N2: nhánh lọc THEO NHÃN (không kèm query) — khoảng hỏi rỗng cũng phải nói khoảng
        # kho thật sự có bài khớp CÙNG các bộ lọc nhãn, không chỉ nói "còn N bài chưa phân
        # loại" (lý do đó không liên quan khi sub/ticker/... đã khớp nhãn nhưng sai khoảng ngày).
        khoang = _khoang_khop(None)
        if khoang:
            out["khoang_co_du_lieu"] = khoang
    if not du_lieu and (group_no or sub or industry_code or ticker):
        chua = conn.execute(sa.text(
            "SELECT count(*) FROM news.article a WHERE a.classified_from IS NULL"
            f" AND (CAST(:tu AS date) IS NULL OR {_NGAY_VN} >= CAST(:tu AS date))"
            f" AND (CAST(:den AS date) IS NULL OR {_NGAY_VN} <= CAST(:den AS date))"), p).scalar()
        out["ghi_chu"] = (f"không có bài nào khớp nhãn; trong khoảng này còn {chua} bài "
                          f"chưa phân loại nên chưa thể lọc theo nhãn")
    return to_json(out)
