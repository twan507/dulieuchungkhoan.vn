"""Seam S4 — tìm tin.

Expected lấy từ fixture `kho` (backend/tests/agent/conftest.py, seed 2026-09-07): CHỈ 3 bài
trong TIN_TUC + 2 bài phụ (múi giờ C1, hai revision N1) = 5 bài trong kho test, không phải
1.050/31/23 bài của kho dev thật (những con số đó đo trên warehouse đầy, không áp dụng cho
fixture rỗng — §4.4.4, tiêu chí phải bất biến với dữ liệu).

BẪY ĐÃ ĐO: tsv sinh bằng to_tsvector('simple', news.immutable_unaccent(title || ' ' ||
content)), nên câu hỏi PHẢI bọc cùng hàm — quên là khớp 0 bài.

Ba bài trong TIN_TUC (conftest.py):
  2026-08-10 "...giữ nguyên lãi suất điều hành" / "...quyết định giữ nguyên lãi suất điều
             hành." — chứa ĐÚNG CỤM "lãi suất điều hành", sub='1b' (đã phân loại)
  2026-08-20 "...câu chuyện điều hành chính sách" / "Mức lãi suất huy động...điều hành tỷ
             giá..." — chứa CÁC TỪ ĐÓ nhưng KHÔNG liền cụm, sub='1a' (đã phân loại)
  2026-09-02 "Cổ phiếu thép hồi phục" — không liên quan, sub=None (CHƯA phân loại)

⇒ phraseto_tsquery('lãi suất điều hành') khớp ĐÚNG 1 bài (2026-08-10).
  plainto_tsquery của cùng cụm ĐẢO NGƯỢC thứ tự ('điều hành lãi suất', để ép phraseto = 0 và
  buộc hàm lùi về plainto) khớp CẢ 2 bài — vì plainto không đòi hỏi thứ tự.

Hai bài phụ (sub riêng '2b'/'2a', không đụng từ khoá của ba bài trên):
  "qua_nua_dem" (sub='2b'): published_at='2026-08-19 23:30:00+00' = 2026-08-20 06:30 giờ VN —
             bắt lỗi lệch múi giờ (CLAUDE.md §3.1): ngày UTC (08-19) và ngày VN (08-20) của
             CÙNG một thời điểm phải khác nhau, để phép thử thật sự bắt được nếu ai đó bỏ ép
             AT TIME ZONE 'Asia/Ho_Chi_Minh'.
  "hai_ban" (sub='2a'): HAI revision (version 1 và 2, tiêu đề khác nhau) — bắt lỗi JOIN
             news.article_revision không khoá version (N1): không khoá thì bài này hiện ra
             2 LẦN trong kết quả lọc theo sub='2a'.
"""
import json

import sqlalchemy as sa

from agent.tools.get_news import tim_tin


def test_tim_dung_cum_uu_tien_phraseto(db, kho):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(tim_tin(db, query="lãi suất điều hành", limit=30))
    assert out["kieu_tim"] == "cum"
    assert out["tong_khop"] == 1
    assert out["du_lieu"][0]["ngay"] == "2026-08-10"


def test_cum_khong_khop_thi_lui_ve_tu_khoa(db, kho):
    """Đảo thứ tự cụm -> phraseto khớp 0 -> hàm phải tự lùi về plainto_tsquery và báo kieu_tim."""
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(tim_tin(db, query="điều hành lãi suất", limit=30))
    assert out["kieu_tim"] == "tu_khoa"
    assert out["tong_khop"] == 2
    assert {b["ngay"] for b in out["du_lieu"]} == {"2026-08-10", "2026-08-20"}


def test_moi_bai_deu_co_co_da_phan_loai(db, kho):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(tim_tin(db, query="ngân hàng", limit=5))
    assert out["so_dong"] == 1
    assert all("da_phan_loai" in b for b in out["du_lieu"])
    assert out["du_lieu"][0]["da_phan_loai"] is True


def test_loc_theo_nhan_chi_khop_bai_da_phan_loai(db, kho):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(tim_tin(db, sub="1b", limit=5))
    assert out["so_dong"] == 1
    assert out["du_lieu"][0]["ngay"] == "2026-08-10"
    assert all(b["da_phan_loai"] is True for b in out["du_lieu"])


def test_loc_nhan_rong_thi_noi_ro_con_bao_nhieu_bai_chua_nhan(db, kho):
    """Không được để model kết luận 'không có tin nào' khi thật ra là chưa phân loại.

    Tháng 9/2026 trong kho chỉ có 1 bài (2026-09-02), CHƯA phân loại (sub=None) — lọc theo
    sub='3b' ra 0 dòng nhưng ghi_chu phải nói rõ còn 1 bài chưa phân loại trong khoảng này.
    """
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(tim_tin(db, sub="3b", from_date="2026-09-01", to_date="2026-09-30"))
    assert out["so_dong"] == 0
    assert "còn 1 bài chưa phân loại" in out["ghi_chu"]


def test_ticker_khong_ton_tai_bao_khong_tim_thay_khong_do_loi_cho_chua_phan_loai(db, kho):
    """spec §4.6 hình dạng #1: ticker='ZZZZ' không tồn tại trong market.security phải trả
    tim_thay=False — trước sửa, hàm không gọi resolve_ticker nên rơi vào nhánh 'lọc theo nhãn
    ra 0 dòng' và trả ghi_chu nói 'còn N bài chưa phân loại', một lời GIẢI THÍCH SAI NGUYÊN
    NHÂN (mời model kết luận 'chưa phân loại nên chưa thấy tin' thay vì 'mã không tồn tại')."""
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(tim_tin(db, ticker="ZZZZ"))
    assert out["tim_thay"] is False
    assert "ghi_chu" not in out


def test_sub_la_bi_tu_choi(db, kho):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(tim_tin(db, sub="9z"))
    assert out["loi"] is True
    assert "3i" in out["sub_hop_le"]          # 3i hợp lệ (migration 0019: nhóm 3 tới 'i', không phải 'e')


def test_ngay_hien_thi_theo_gio_vn_khong_theo_utc(db, kho):
    """C1 (CLAUDE.md §3.1): phiên Postgres chạy Etc/UTC. Bài 'qua_nua_dem' đăng lúc
    2026-08-19 23:30 UTC = 2026-08-20 06:30 giờ VN — ngày phải khai là ngày VN (08-20),
    không phải ngày UTC (08-19) mà published_at.date() (Python, không ép TZ) sẽ cho ra."""
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(tim_tin(db, sub="2b", limit=5))
    assert out["so_dong"] == 1
    assert out["du_lieu"][0]["ngay"] == "2026-08-20"
    assert out["du_lieu"][0]["ngay_hien_thi"] == "20/08/2026"


def test_bo_loc_ngay_theo_gio_vn_khong_lot_luoi(db, kho):
    """C1: bộ lọc from_date/to_date cũng phải so theo NGÀY VN, không theo ngày UTC — cùng bài
    'qua_nua_dem' (2026-08-19 23:30 UTC = 2026-08-20 06:30 VN):
      to_date='2026-08-19' theo UTC vẫn còn chứa thời điểm đó (23:30 < nửa đêm 08-20 UTC) nên
      bộ lọc cũ (so theo UTC) sẽ lẫn nhầm nó vào — phải LOẠI vì ngày VN thật là 08-20.
      from/to='2026-08-20' theo UTC lại KHÔNG chứa nó (23:30 ngày 19 chưa tới nửa đêm UTC) nên
      bộ lọc cũ sẽ BỎ SÓT — phải GIỮ vì ngày VN thật đúng là 08-20."""
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    ngoai = json.loads(tim_tin(db, sub="2b", to_date="2026-08-19"))
    assert ngoai["so_dong"] == 0
    trong = json.loads(tim_tin(db, sub="2b", from_date="2026-08-20", to_date="2026-08-20"))
    assert trong["so_dong"] == 1


def test_join_revision_khoa_ban_moi_nhat_khong_nhan_doi(db, kho):
    """N1: bài 'hai_ban' có 2 revision. JOIN news.article_revision không khoá version (bug cũ)
    sẽ nhân đôi — mỗi revision ra một dòng. Phải chỉ trả ĐÚNG 1 dòng, đúng bản MỚI NHẤT."""
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(tim_tin(db, sub="2a", limit=5))
    assert out["so_dong"] == 1
    assert out["du_lieu"][0]["tieu_de"] == "Doanh nghiệp dệt may khởi công nhà máy mới tại Thái Bình"
