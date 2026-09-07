"""Chuỗi vĩ mô (macro) và giá tài sản (asset) — một cửa cho model.

macro đọc qua view observation_spliced (chuỗi ĐÃ NỐI): lấy value_spliced; kèm
value_as_published khi hai giá trị khác nhau để model nói được là chuỗi đã nối.

asset nằm ở HAI bảng: price_daily (giá trị đơn, CÓ cột price_type) và ohlc_daily (nến,
KHÔNG có price_type) — phải thử cả hai. Một asset_id có thể mang NHIỀU price_type trong
cùng khoảng ngày (vàng: spot + fixing; dầu: futures) — ADR §2.3 cấm trộn hai loại giá vào
một cột/chuỗi (tạo bậc nhảy ~2% tại điểm đổi nguồn). Vì vậy nhánh price_daily luôn CHỌN
ĐÚNG MỘT loại — loại có nhiều dòng nhất trong khoảng hỏi — rồi trả kèm `loai_gia` và
`cac_loai_gia_co_san` để model biết còn loại nào khác chưa lấy.

Không có code ⇒ trả DANH MỤC theo keyword, không trả số: đó là cách model tìm mã mà không
phải nhồi hàng trăm mã vào system prompt.
"""
from __future__ import annotations

import sqlalchemy as sa

from agent.format import display_series_value, format_date_vi
from agent.tools._shared import cap_limit, co_du_lieu, khong_tim_thay, rong, to_json

TRAN_DANH_MUC = 40

# CAST(:x AS type) — KHÔNG viết :x::type, SQLAlchemy lặng lẽ bỏ tham số (CLAUDE.md §3 lát 10).
_SQL_DANH_MUC = sa.text("""
    SELECT i.code AS ma, i.name_vi AS ten, i.unit AS don_vi, 'macro' AS nguon
    FROM macro.indicator i
    WHERE CAST(:kw AS text) IS NULL OR i.code ILIKE '%' || :kw || '%' OR i.name_vi ILIKE '%' || :kw || '%'
    UNION ALL
    SELECT a.code, a.name_vi, a.unit, 'asset'
    FROM asset.asset a
    WHERE CAST(:kw AS text) IS NULL OR a.code ILIKE '%' || :kw || '%' OR a.name_vi ILIKE '%' || :kw || '%'
    ORDER BY 1 LIMIT :tran
""")

# N3: danh mục là cửa DUY NHẤT để model tìm mã (kho có 192 chuỗi, đo 2026-09-07) — đếm riêng
# tổng số khớp thật để model biết còn bao nhiêu ngoài 40 mục đã trả, thay vì cắt câm.
_SQL_DANH_MUC_DEM = sa.text("""
    SELECT (SELECT count(*) FROM macro.indicator i
            WHERE CAST(:kw AS text) IS NULL OR i.code ILIKE '%' || :kw || '%' OR i.name_vi ILIKE '%' || :kw || '%')
         + (SELECT count(*) FROM asset.asset a
            WHERE CAST(:kw AS text) IS NULL OR a.code ILIKE '%' || :kw || '%' OR a.name_vi ILIKE '%' || :kw || '%')
""")

_SQL_MACRO_INDICATOR = sa.text(
    "SELECT indicator_id, name_vi, unit FROM macro.indicator WHERE code = :c")

_SQL_MACRO_OBS = sa.text("""
    SELECT obs_date, value_spliced, value_as_published
    FROM macro.observation_spliced
    WHERE indicator_id = :id
      AND (CAST(:tu AS date) IS NULL OR obs_date >= CAST(:tu AS date))
      AND (CAST(:den AS date) IS NULL OR obs_date <= CAST(:den AS date))
    ORDER BY obs_date DESC LIMIT :lim
""")

_SQL_ASSET = sa.text("SELECT asset_id, name_vi, unit FROM asset.asset WHERE code = :c")

# Loại giá nào tồn tại trong khoảng hỏi, xếp theo số dòng giảm dần — dòng đầu là loại được chọn.
_SQL_LOAI_GIA = sa.text("""
    SELECT price_type, count(*) AS so_dong
    FROM asset.price_daily
    WHERE asset_id = :id
      AND (CAST(:tu AS date) IS NULL OR obs_date >= CAST(:tu AS date))
      AND (CAST(:den AS date) IS NULL OR obs_date <= CAST(:den AS date))
    GROUP BY price_type
    ORDER BY so_dong DESC, price_type
""")

_SQL_PRICE_DAILY = sa.text("""
    SELECT obs_date, value AS gia
    FROM asset.price_daily
    WHERE asset_id = :id AND price_type = :pt
      AND (CAST(:tu AS date) IS NULL OR obs_date >= CAST(:tu AS date))
      AND (CAST(:den AS date) IS NULL OR obs_date <= CAST(:den AS date))
    ORDER BY obs_date DESC LIMIT :lim
""")

_SQL_OHLC = sa.text("""
    SELECT obs_date, close AS gia
    FROM asset.ohlc_daily
    WHERE asset_id = :id
      AND (CAST(:tu AS date) IS NULL OR obs_date >= CAST(:tu AS date))
      AND (CAST(:den AS date) IS NULL OR obs_date <= CAST(:den AS date))
    ORDER BY obs_date DESC LIMIT :lim
""")

# Hình dạng #3 (spec §4.6) phải nói khoảng kho THẬT SỰ có, cùng nguyên tắc đã vá ở
# get_price_series/get_financials/get_corporate_events (review SPEC lát 10, vòng 3, N2) — nhánh
# macro/asset của tool này trước đó thiếu hẳn khoang_co_du_lieu khi khoảng hỏi rỗng.
_SQL_KHOANG_MACRO = sa.text(
    "SELECT min(obs_date), max(obs_date) FROM macro.observation_spliced WHERE indicator_id = :id")

# asset nằm ở HAI bảng (xem docstring đầu file) — khoảng "kho có dữ liệu" phải gộp cả hai,
# KHÔNG chỉ bảng vừa tra ra 0 dòng, vì asset có thể có dữ liệu ở bảng còn lại.
_SQL_KHOANG_ASSET = sa.text("""
    SELECT min(d), max(d) FROM (
        SELECT obs_date AS d FROM asset.price_daily WHERE asset_id = :id
        UNION ALL
        SELECT obs_date FROM asset.ohlc_daily WHERE asset_id = :id
    ) t
""")


def _danh_muc(conn: sa.Connection, keyword: str | None, tran: int = TRAN_DANH_MUC) -> list[dict]:
    return [dict(r._mapping) for r in conn.execute(_SQL_DANH_MUC, {"kw": keyword, "tran": tran})]


def _dem_danh_muc(conn: sa.Connection, keyword: str | None) -> int:
    return conn.execute(_SQL_DANH_MUC_DEM, {"kw": keyword}).scalar()


def chuoi_vi_mo(conn: sa.Connection, code: str | None = None, keyword: str | None = None,
                from_date: str | None = None, to_date: str | None = None,
                limit: int | None = None) -> str:
    if not code:
        danh_muc = _danh_muc(conn, keyword)
        tong = _dem_danh_muc(conn, keyword)
        return to_json({"kieu": "danh_muc", "danh_muc": danh_muc, "tong_khop": tong,
                        "da_cat": tong > len(danh_muc)})
    lim = cap_limit(limit, 60, 200)

    ind = conn.execute(_SQL_MACRO_INDICATOR, {"c": code}).first()
    if ind:
        rows = conn.execute(_SQL_MACRO_OBS, {"id": ind.indicator_id, "tu": from_date,
                                             "den": to_date, "lim": lim}).all()
        if not rows:
            tu, den = conn.execute(_SQL_KHOANG_MACRO, {"id": ind.indicator_id}).one()
            khoang = {"tu": str(tu), "den": str(den)} if tu is not None else None
            return to_json({**rong(khoang), "ma": code})
        du_lieu = []
        for r in reversed(rows):
            d = {"ngay": str(r.obs_date), "ngay_hien_thi": format_date_vi(r.obs_date),
                 "gia_tri": display_series_value(r.value_spliced, ind.unit)}
            if r.value_as_published is not None and r.value_as_published != r.value_spliced:
                d["gia_tri_cong_bo"] = display_series_value(r.value_as_published, ind.unit)
                d["ghi_chu"] = "chuỗi đã nối, khác số công bố gốc"
            du_lieu.append(d)
        return to_json(co_du_lieu(du_lieu, ma=code, ten=ind.name_vi, don_vi=ind.unit,
                                  da_cat=len(rows) >= lim))

    tai_san = conn.execute(_SQL_ASSET, {"c": code}).first()
    if tai_san is None:
        return to_json(khong_tim_thay(code, [d["ma"] for d in _danh_muc(conn, code[:6])][:5]))

    loai_rows = conn.execute(_SQL_LOAI_GIA, {"id": tai_san.asset_id, "tu": from_date, "den": to_date}).all()
    if loai_rows:
        # CHỈ MỘT loại — loại nhiều dòng nhất trong khoảng hỏi. Tuyệt đối không gộp loại khác
        # vào cùng chuỗi (ADR §2.3: trộn giao ngay với tương lai tạo bậc nhảy ~2%).
        loai_gia = loai_rows[0].price_type
        cac_loai = [r.price_type for r in loai_rows]
        rows = conn.execute(_SQL_PRICE_DAILY, {"id": tai_san.asset_id, "pt": loai_gia,
                                               "tu": from_date, "den": to_date, "lim": lim}).all()
        du_lieu = [{"ngay": str(r.obs_date), "ngay_hien_thi": format_date_vi(r.obs_date),
                    "gia_tri": display_series_value(r.gia, tai_san.unit)} for r in reversed(rows)]
        return to_json(co_du_lieu(du_lieu, ma=code, ten=tai_san.name_vi, don_vi=tai_san.unit,
                                  loai_gia=loai_gia, cac_loai_gia_co_san=cac_loai,
                                  da_cat=len(rows) >= lim))

    rows = conn.execute(_SQL_OHLC, {"id": tai_san.asset_id, "tu": from_date, "den": to_date, "lim": lim}).all()
    if not rows:
        tu, den = conn.execute(_SQL_KHOANG_ASSET, {"id": tai_san.asset_id}).one()
        khoang = {"tu": str(tu), "den": str(den)} if tu is not None else None
        return to_json({**rong(khoang), "ma": code})
    du_lieu = [{"ngay": str(r.obs_date), "ngay_hien_thi": format_date_vi(r.obs_date),
                "gia_tri": display_series_value(r.gia, tai_san.unit)} for r in reversed(rows)]
    return to_json(co_du_lieu(du_lieu, ma=code, ten=tai_san.name_vi, don_vi=tai_san.unit,
                              da_cat=len(rows) >= lim))
