"""Kho thu nhỏ, tất định, dùng chung cho mọi test của tầng ngữ nghĩa.

Vì sao cần: `migrated_engine` dựng DB test **rỗng** — chỉ `market.industry` có sẵn 30 dòng do
migration seed. Test tool mà đọc kho dev thật thì tiêu chí trôi theo dữ liệu (ETL chạy là số
đổi), vi phạm "tiêu chí phải bất biến, không phải số thời điểm" (CLAUDE.md §4.4.4).

Vì sao con số trong đây giống kho thật: chúng chép từ số đo ngày 2026-09-07 để test đi qua
đúng những hình dạng dữ liệu có thật (giá trị âm của chi phí, hai mã cùng tên hiển thị,
`price_type` của hàng hoá, tin có cụm từ nằm rời rạc). Đây là **fixture**, không phải bản sao
kho — không ai được suy ngược ra kết luận về thị trường từ những số này.

Fixture chạy trong transaction của `db` nên tự tan sau mỗi test.
"""
from __future__ import annotations

import json

import pytest
import sqlalchemy as sa

METRICS = [
    ("isa3", "Doanh số thuần", "VND"), ("isa9", "Chi phí bán hàng", "VND"),
    ("isa10", "Chi phí quản lý doanh  nghiệp", "VND"), ("isa16", "Lãi/(lỗ) ròng trước thuế", "VND"),
    ("isa20", "LỢI NHUẬN THUẦN", "VND"), ("isa22", "LỢI NHUẬN THUẦN", "VND"),
    ("isa23", "Lãi cơ bản trên cổ phiếu (VND)", "VND/CP"),
    ("bsa1", "TÀI SẢN NGẮN HẠN", "VND"), ("bsa2", "Tiền và tương đương tiền", "VND"),
    ("bsa53", "TỔNG TÀI SẢN", "VND"), ("bsa54", "NỢ PHẢI TRẢ", "VND"),
    ("bsa78", "VỐN CHỦ SỞ HỮU", "VND"), ("bsa96", "TỔNG CỘNG NGUỒN VỐN", "VND"),
    ("cfa18", "Lưu chuyển tiền thuần từ hoạt động kinh doanh", "VND"),
    ("rtd11", "Vốn hóa", "VND"), ("rtd14", "EPS (TTM)", "VND/CP"),
    ("rtd21", "P/E (TTM)", "lan"), ("rtd25", "P/B (TTM)", "lan"),
    ("rtd7", "Giá trị sổ sách trên mỗi cổ phiếu (BVPS)", "VND/CP"),
    ("rtq12", "ROE (TTM)", "ty_le_thap_phan"), ("rtq14", "ROA (TTM)", "ty_le_thap_phan"),
    ("prf", "Lợi nhuận ròng (tỉ đồng) (quý gần nhất)", "VND"),
]

# ticker, tên doanh nghiệp, mã ngành level 2, loại chứng khoán, trạng thái
DOANH_NGHIEP = [
    ("HPG", "Tập đoàn Hòa Phát", "KIMLOAI", "stock", "listed"),
    ("VCB", "Ngân hàng Thương mại Cổ phần Ngoại thương Việt Nam", "NGANHANG", "stock", "listed"),
    ("FPT", "Công ty Cổ phần FPT", "CONGNGHE", "stock", "listed"),
    ("TIN", "Ngân hàng Thử Nghiệm", "NGANHANG", "stock", "listed"),
    ("HDB", "Ngân hàng Phát Triển Nhà", "NGANHANG", "stock", "listed"),
    ("LPB", "Ngân hàng Bưu Điện", "NGANHANG", "stock", "listed"),
    ("CUOI", "Doanh nghiệp đã rời sàn", "KIMLOAI", "stock", "delisted"),
    ("VNINDEX", None, None, "index", "listed"),
    # F2 (review CHUẨN lát 10, vòng 2): ETF CÓ issuer_id trong kho thật (đo 2026-09-07: 21/31
    # etf có issuer_id) và CÓ sự kiện doanh nghiệp thật (etf 18 mã/104 sự kiện) — bắt hồi quy
    # "mọi loại khác stock đều không có sự kiện" đã từng chặn nhầm cả ETF.
    ("QUYTN", "Quỹ ETF Thử Nghiệm", None, "etf", "listed"),
]

GIA_HPG = [("2026-09-01", 21200), ("2026-09-02", 21400), ("2026-09-03", 21600)]

BCTC_FPT_2024 = [("isa3", 62848794351367), ("isa9", -6115961971783),
                 ("isa20", 9427422530444), ("isa22", 7856767812178)]

SCREENER = {                                   # phiên 2026-09-04
    "HPG": {"rtd21": 7.89115654, "rtq12": 0.17377625, "rtd11": 183212330084000, "rtd14": 2749.91376474},
    "VCB": {"rtd21": 11.81676534, "rtq12": 0.17922416, "rtd11": 492149263036600, "rtd14": 4984.44356698},
    "TIN": {"rtd21": 5.10, "rtq12": 0.73478649, "rtd11": 1200000000000, "rtd14": 900.0},
    "HDB": {"rtd21": 6.20, "rtq12": 0.24836986, "rtd11": 90000000000000, "rtd14": 3100.0},
    "LPB": {"rtd21": 7.10, "rtq12": 0.24661870, "rtd11": 80000000000000, "rtd14": 2600.0},
    "FPT": {"rtd21": 21.30, "rtq12": 0.26474720, "rtd11": 124802963521600, "rtd14": 5863.11130562},
}

TIN_TUC = [
    # (ngày đăng, báo, tiêu đề, thân bài, nhóm, sub)
    ("2026-08-10", "tinnhanhck", "Ngân hàng Nhà nước giữ nguyên lãi suất điều hành",
     "Trong phiên họp tháng 8, cơ quan quản lý quyết định giữ nguyên lãi suất điều hành.", 1, "1b"),
    ("2026-08-20", "vietstock", "Lạm phát và câu chuyện điều hành chính sách",
     "Mức lãi suất huy động nhích lên trong khi việc điều hành tỷ giá vẫn thận trọng.", 1, "1a"),
    ("2026-09-02", "cafef", "Cổ phiếu thép hồi phục",
     "Nhóm thép tăng trở lại sau chuỗi phiên điều chỉnh.", None, None),
]


@pytest.fixture()
def kho(db):
    """Seed kho thu nhỏ rồi trả bảng tra id. Ghi bằng quyền chủ, test tự đổi sang dlck_api."""
    ids: dict[str, int] = {}

    nganh = dict(db.execute(sa.text(
        "SELECT code, industry_id FROM market.industry WHERE level = 2")).all())

    db.execute(sa.text(
        "INSERT INTO market.metric_dictionary (dictionary, code, name_vi, unit)"
        " VALUES ('field_dictionary', :c, :n, :u)"),
        [{"c": c, "n": n, "u": u} for c, n, u in METRICS])

    for ticker, ten, ma_nganh, loai, trang_thai in DOANH_NGHIEP:
        issuer_id = None
        if ten is not None:
            issuer_id = db.execute(sa.text(
                "INSERT INTO market.issuer (name, industry_id) VALUES (:n, :i) RETURNING issuer_id"),
                {"n": ten, "i": nganh.get(ma_nganh)}).scalar_one()
            ids[f"issuer:{ticker}"] = issuer_id
        ids[ticker] = db.execute(sa.text(
            "INSERT INTO market.security (ticker, exchange, security_type, issuer_id, status)"
            " VALUES (:t, 'HOSE', :loai, :i, :tt) RETURNING security_id"),
            {"t": ticker, "loai": loai, "i": issuer_id, "tt": trang_thai}).scalar_one()

    db.execute(sa.text(
        "INSERT INTO market.price_daily (security_id, trading_date, close_raw, close_adj,"
        " open_value, highest_value, lowest_value, raw)"
        " VALUES (:s, :d, :g, :g, :g, :g, :g, '{}'::jsonb)"),
        [{"s": ids["HPG"], "d": d, "g": g} for d, g in GIA_HPG])

    db.execute(sa.text(
        "INSERT INTO market.financial_statement"
        " (issuer_id, year_report, length_report, statement_type, metric_code, value)"
        " VALUES (:i, 2024, 5, 'IS', :c, :v)"),
        [{"i": ids["issuer:FPT"], "c": c, "v": v} for c, v in BCTC_FPT_2024])

    db.execute(sa.text(
        "INSERT INTO market.screener_daily (security_id, trading_date, payload)"
        " VALUES (:s, '2026-09-04', CAST(:p AS jsonb))"),
        [{"s": ids[t], "p": json.dumps({"stockScreenerItem": v})} for t, v in SCREENER.items()])

    db.execute(sa.text(
        "INSERT INTO market.corporate_event (event_type, issuer_id, public_date, exright_date, payload)"
        " VALUES (:e, :i, CAST(:p AS date), CAST(:x AS date), '{}'::jsonb)"),
        [{"e": "CashDividend", "i": ids["issuer:FPT"], "p": "2025-06-06", "x": "2025-06-12"},
         {"e": "CashDividend", "i": ids["issuer:FPT"], "p": "2025-11-19", "x": "2025-12-01"},
         {"e": "AGM", "i": ids["issuer:FPT"], "p": "2025-03-10", "x": None},
         # F2: ETF QUYTN có issuer_id thật — phải nhận đúng sự kiện của nó, không rơi vào
         # nhánh "loại chứng khoán này không có sự kiện doanh nghiệp".
         {"e": "CashDividend", "i": ids["issuer:QUYTN"], "p": "2026-02-26", "x": "2026-03-05"}])

    ids["cpi"] = db.execute(sa.text(
        "INSERT INTO macro.indicator (code, name_vi, unit, freq, region, role)"
        " VALUES ('vn.cpi', 'CPI (YoY)', '%', 'm', 'vn', 'data') RETURNING indicator_id")).scalar_one()
    db.execute(sa.text(
        "INSERT INTO macro.observation (indicator_id, obs_date, value) VALUES (:i, CAST(:d AS date), :v)"),
        [{"i": ids["cpi"], "d": d, "v": v}
         for d, v in [("2026-06-01", 4.38), ("2026-07-01", 4.39), ("2026-08-01", 4.45)]])

    ids["wti"] = db.execute(sa.text(
        "INSERT INTO asset.asset (code, name_vi, asset_class, quote_currency, unit, calendar)"
        " VALUES ('wti', 'Giá dầu WTI', 'commodity', 'USD', 'USD/thùng', 'trading_days')"
        " RETURNING asset_id")).scalar_one()
    db.execute(sa.text(
        "INSERT INTO asset.price_daily (asset_id, obs_date, price_type, value)"
        " VALUES (:a, CAST(:d AS date), 'futures', :v)"),
        [{"a": ids["wti"], "d": d, "v": v} for d, v in [("2026-09-04", 90.57), ("2026-09-05", 91.22)]])

    ids["btc"] = db.execute(sa.text(
        "INSERT INTO asset.asset (code, name_vi, asset_class, quote_currency, unit, calendar)"
        " VALUES ('btc', 'Bitcoin', 'crypto', 'USDT', 'USDT', '24x7') RETURNING asset_id")).scalar_one()
    db.execute(sa.text(
        "INSERT INTO asset.ohlc_daily (asset_id, obs_date, open, high, low, close)"
        " VALUES (:a, '2026-09-05'::date, 100, 110, 95, 105)"), {"a": ids["btc"]})

    for ngay, bao, tieu_de, than_bai, nhom, sub in TIN_TUC:
        aid = db.execute(sa.text(
            "INSERT INTO news.article (canonical_url, primary_source, published_at, published_at_src,"
            " fetched_at, group_no, sub, classified_from, content_chars)"
            " VALUES (:u, :b, CAST(:d AS timestamptz), 'feed', now(), :g, :s, :cf, :n) RETURNING article_id"),
            {"u": f"https://vi.du/{bao}/{ngay}", "b": bao, "d": ngay + " 08:00+07",
             "g": nhom, "s": sub, "cf": "content" if sub else None, "n": len(than_bai)}).scalar_one()
        db.execute(sa.text(
            "INSERT INTO news.article_revision (article_id, version, title, content, content_fetched_at)"
            " VALUES (:a, 1, :t, :c, now())"), {"a": aid, "t": tieu_de, "c": than_bai})
        ids[f"tin:{ngay}"] = aid

    # C1 — bài đăng sát nửa đêm UTC: 2026-08-19 23:30+00 = 2026-08-20 06:30 giờ VN. Dùng để bắt
    # lỗi lệch múi giờ (CLAUDE.md §3.1): ngày UTC và ngày VN của đúng một thời điểm phải KHÁC
    # nhau, nếu không phép thử không bắt được gì. group_no/sub riêng ('2b') để không lẫn với
    # ba bài TIN_TUC ở trên khi lọc theo nhãn.
    aid_nua_dem = db.execute(sa.text(
        "INSERT INTO news.article (canonical_url, primary_source, published_at, published_at_src,"
        " fetched_at, group_no, sub, classified_from, content_chars)"
        " VALUES ('https://vi.du/tinnhanhck/qua-nua-dem', 'tinnhanhck',"
        " CAST('2026-08-19 23:30:00+00' AS timestamptz), 'feed', now(), 2, '2b', 'content', 70)"
        " RETURNING article_id")).scalar_one()
    db.execute(sa.text(
        "INSERT INTO news.article_revision (article_id, version, title, content, content_fetched_at)"
        " VALUES (:a, 1, 'Bản tin thử múi giờ đăng sát nửa đêm',"
        " 'Nội dung này chỉ để kiểm tra hiển thị ngày theo giờ Việt Nam, không liên quan thị trường.', now())"),
        {"a": aid_nua_dem})
    ids["tin:qua_nua_dem"] = aid_nua_dem

    # N1 — một bài có HAI revision: news_store.add_revision chèn version+1 khi nội dung đổi
    # trong phiên (lát 7b). group_no/sub riêng ('2a') để phép lọc theo nhãn chỉ trúng đúng bài
    # này — nếu JOIN không khoá version, bài sẽ hiện ra 2 LẦN (một lần mỗi revision).
    aid_hai_ban = db.execute(sa.text(
        "INSERT INTO news.article (canonical_url, primary_source, published_at, published_at_src,"
        " fetched_at, group_no, sub, classified_from, content_chars)"
        " VALUES ('https://vi.du/cafef/hai-ban', 'cafef',"
        " CAST('2026-08-15 08:00+07' AS timestamptz), 'feed', now(), 2, '2a', 'content', 90)"
        " RETURNING article_id")).scalar_one()
    db.execute(sa.text(
        "INSERT INTO news.article_revision (article_id, version, title, content, content_fetched_at)"
        " VALUES (:a, 1, 'Doanh nghiệp dệt may mở rộng nhà máy tại Thái Bình',"
        " 'Một doanh nghiệp dệt may vừa công bố kế hoạch xây thêm nhà máy mới tại Thái Bình.', now())"),
        {"a": aid_hai_ban})
    db.execute(sa.text(
        "INSERT INTO news.article_revision (article_id, version, title, content, content_fetched_at)"
        " VALUES (:a, 2, 'Doanh nghiệp dệt may khởi công nhà máy mới tại Thái Bình',"
        " 'Doanh nghiệp dệt may đã chính thức khởi công nhà máy mới tại Thái Bình, dự kiến hoàn thành cuối năm sau.', now())"),
        {"a": aid_hai_ban})
    ids["tin:hai_ban"] = aid_hai_ban

    # Mục 1 (review vòng 4) — bài THIẾU published_at. NULLABLE có chủ đích (migration 0007
    # dòng 32-39): nguồn như VietnamBiz để pubDate trống; quy ước đọc đã ghi ngay trong migration
    # là "sắp xếp tầng đọc dùng coalesce(published_at, fetched_at)" (khuôn đã dùng ở
    # etl/news_store.py). Đo kho thật 2026-09-07: 47/8.220 bài published_at NULL — ORDER BY
    # ... DESC mặc định NULLS FIRST đưa chúng lên đầu, format_date_vi(None) ném AttributeError
    # ngay ở get_news() không tham số. fetched_at cố định SAU mọi bài khác trong kho test để bài
    # này đứng ĐẦU kết quả mặc định (không lọc gì) một khi sửa dùng coalesce — bài không đứng đầu
    # thì phép thử không thật sự đụng nhánh vừa sửa.
    aid_khong_ngay = db.execute(sa.text(
        "INSERT INTO news.article (canonical_url, primary_source, published_at, published_at_src,"
        " fetched_at, group_no, sub, classified_from, content_chars)"
        " VALUES ('https://vi.du/vietnambiz/khong-ro-ngay-dang', 'vietnambiz',"
        " NULL, 'unknown', CAST('2026-10-01 09:00:00+07' AS timestamptz), NULL, NULL, NULL, 60)"
        " RETURNING article_id")).scalar_one()
    db.execute(sa.text(
        "INSERT INTO news.article_revision (article_id, version, title, content, content_fetched_at)"
        " VALUES (:a, 1, 'Bản tin không rõ ngày đăng gốc',"
        " 'Nội dung này không có published_at, dùng để kiểm hàm không nổ khi thiếu ngày.', now())"),
        {"a": aid_khong_ngay})
    ids["tin:khong_ngay"] = aid_khong_ngay

    return ids
