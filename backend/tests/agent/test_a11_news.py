"""Seam S4 — tìm tin.

Expected lấy từ fixture `kho` (backend/tests/agent/conftest.py, seed 2026-09-07): CHỈ 3 bài
trong kho test, không phải 1.050/31/23 bài của kho dev thật (những con số đó đo trên warehouse
đầy, không áp dụng cho fixture rỗng — §4.4.4, tiêu chí phải bất biến với dữ liệu).

BẪY ĐÃ ĐO: tsv sinh bằng to_tsvector('simple', news.immutable_unaccent(title || ' ' ||
content)), nên câu hỏi PHẢI bọc cùng hàm — quên là khớp 0 bài.

Ba bài trong `kho` (TIN_TUC trong conftest.py):
  2026-08-10 "...giữ nguyên lãi suất điều hành" / "...quyết định giữ nguyên lãi suất điều
             hành." — chứa ĐÚNG CỤM "lãi suất điều hành", sub='1b' (đã phân loại)
  2026-08-20 "...câu chuyện điều hành chính sách" / "Mức lãi suất huy động...điều hành tỷ
             giá..." — chứa CÁC TỪ ĐÓ nhưng KHÔNG liền cụm, sub='1a' (đã phân loại)
  2026-09-02 "Cổ phiếu thép hồi phục" — không liên quan, sub=None (CHƯA phân loại)

⇒ phraseto_tsquery('lãi suất điều hành') khớp ĐÚNG 1 bài (2026-08-10).
  plainto_tsquery của cùng cụm ĐẢO NGƯỢC thứ tự ('điều hành lãi suất', để ép phraseto = 0 và
  buộc hàm lùi về plainto) khớp CẢ 2 bài — vì plainto không đòi hỏi thứ tự.
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


def test_sub_la_bi_tu_choi(db, kho):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(tim_tin(db, sub="9z"))
    assert out["loi"] is True
    assert "3i" in out["sub_hop_le"]          # 3i hợp lệ (migration 0019: nhóm 3 tới 'i', không phải 'e')
