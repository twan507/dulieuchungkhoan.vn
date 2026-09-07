"""Seam S4 — lọc cổ phiếu và so sánh, đọc market.screener_daily (payload jsonb).

Expected lấy từ fixture `kho` (backend/tests/agent/conftest.py, seed 2026-09-07), không phải
đo kho dev thật (§4.4.4 — tiêu chí phải bất biến). Phiên 2026-09-04 (hằng số SCREENER):
  ngành NGANHANG, ROE (rtq12) cao nhất: TIN 0.73478649, HDB 0.24836986, LPB 0.2466187
  P/E (rtd21): HPG 7.89115654, VCB 11.81676534
Payload thật có hai nhánh: 'financial' và 'stockScreenerItem' — chỉ tiêu của tầng ngữ nghĩa
nằm ở nhánh sau, fixture `kho` ghi thẳng payload = {"stockScreenerItem": {...}}.
"""
import json

import sqlalchemy as sa

from agent.tools.compare_peers import so_sanh_cung_nganh
from agent.tools.screen_stocks import loc_co_phieu


def test_top_roe_nganh_ngan_hang(db, kho):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(loc_co_phieu(db, industry_code="NGANHANG", sort_by="rtq12", limit=3))
    assert [c["ma"] for c in out["du_lieu"]] == ["TIN", "HDB", "LPB"]
    assert out["du_lieu"][0]["chi_tieu"]["ROE (TTM)"] == "73,48%"
    assert out["du_lieu"][1]["chi_tieu"]["ROE (TTM)"] == "24,84%"
    assert out["du_lieu"][2]["chi_tieu"]["ROE (TTM)"] == "24,66%"


def test_loc_theo_tieu_chi(db, kho):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(loc_co_phieu(db, criteria=[{"metric_code": "rtd21", "operator": "<", "value": 8}],
                                  industry_code="KIMLOAI", limit=20))
    assert out["co_du_lieu"] is True
    assert [c["ma"] for c in out["du_lieu"]] == ["HPG"]
    assert all("P/E (TTM)" in c["chi_tieu"] for c in out["du_lieu"])


def test_so_sanh_pe_hpg_vcb(db, kho):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(so_sanh_cung_nganh(db, tickers=["HPG", "VCB"], metric_codes=["rtd21"]))
    bang = {c["ma"]: c["chi_tieu"]["P/E (TTM)"] for c in out["du_lieu"]}
    assert bang == {"HPG": "7,89 lần", "VCB": "11,82 lần"}


def test_ma_chi_tieu_ngoai_bang_nhan_bi_tu_choi(db, kho):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(so_sanh_cung_nganh(db, tickers=["HPG"], metric_codes=["rev"]))
    assert out["loi"] is True


def test_ma_khong_tra_duoc_bi_bao_ro_khong_am_tham_nuot(db, kho):
    """N4: ZZZZ không tồn tại trong market.security — trước đây biến mất khỏi kết quả mà
    không một trường nào nói vì sao chỉ còn 1/2 mã được so sánh."""
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(so_sanh_cung_nganh(db, tickers=["HPG", "ZZZZ"], metric_codes=["rtd21"]))
    assert [c["ma"] for c in out["du_lieu"]] == ["HPG"]
    assert out["khong_tim_thay"] == ["ZZZZ"]


def test_ma_ton_tai_nhung_khong_co_phien_khac_ma_khong_ton_tai(db, kho):
    """spec §4.6: 'mã bịa ra hoàn toàn' (hình dạng #1) không được gộp chung với 'mã có danh
    tính nhưng phiên screener gần nhất không có dòng cho mã này' (VNINDEX — không phải cổ
    phiếu nên không có mặt trong SCREENER của fixture, khác bản chất với ZZZZ vốn không tồn
    tại trong market.security). Trước sửa, compare_peers không gọi resolve_ticker nên cả hai
    rơi chung vào một khong_tim_thay, đúng câu spec §4.6 cấm ("#1 bị gộp vào #3")."""
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(so_sanh_cung_nganh(db, tickers=["HPG", "VNINDEX", "ZZZZ"], metric_codes=["rtd21"]))
    assert out["khong_tim_thay"] == ["ZZZZ"]
    assert out["khong_co_du_lieu_phien"] == ["VNINDEX"]
    assert [c["ma"] for c in out["du_lieu"]] == ["HPG"]


def test_qua_tran_ma_bi_cat_va_bao_da_cat(db, kho):
    """N4: xin so sánh nhiều hơn TRAN_MA mã, danh sách bị hạ về TRAN_MA mã đầu — phải báo
    da_cat=True, không được câm lặng cắt rồi trả lời như thể đã so đủ.

    Dùng chính hằng số TRAN_MA của module (không mã hoá cứng số mã) — trần đã nới 10 -> 25
    (chủ dự án chốt 2026-09-07), khoá cứng "11 mã" như bản cũ sẽ không còn vượt trần mới và
    làm test hoá xanh giả (§4.4.4: tiêu chí phải bất biến, không phải số thời điểm)."""
    from agent.tools.compare_peers import TRAN_MA
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    mas = ["HPG", "VCB", "TIN", "HDB", "LPB", "FPT"] + [f"ZZ{i}" for i in range(TRAN_MA - 5)]
    assert len(mas) > TRAN_MA
    out = json.loads(so_sanh_cung_nganh(db, tickers=mas, metric_codes=["rtd21"]))
    assert out["da_cat"] is True


def test_luon_kem_ngay_du_lieu(db, kho):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    assert json.loads(loc_co_phieu(db, limit=1))["ngay_du_lieu"] == "2026-09-04"


def test_da_cat_bao_dung_khi_gioi_han_thap_hon_so_dong_that(db, kho):
    """N2: da_cat phải phản ánh KẾT QUẢ THẬT — ngành KIMLOAI trong kho chỉ có HPG và CUOI
    (nhưng CUOI đã huỷ niêm yết nên bị lọc bởi status='listed', chỉ còn 1 dòng khớp); dùng
    NGANHANG (4 mã: TIN, HDB, LPB, VCB) với limit=2 để chắc chắn có cắt thật."""
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(loc_co_phieu(db, industry_code="NGANHANG", limit=2))
    assert out["so_dong"] == 2
    assert out["da_cat"] is True


def test_da_cat_khong_bao_sai_khi_it_du_lieu_hon_tran(db, kho):
    """N2 chiều ngược lại: xin limit=500 (bị hạ về trần 50) nhưng NGANHANG chỉ có 4 mã — không
    được báo da_cat=True vì thực tế không dòng nào bị cắt (bug cũ: cờ suy từ limit ĐẦU VÀO có
    vượt trần hay không, không suy từ kết quả thật)."""
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(loc_co_phieu(db, industry_code="NGANHANG", limit=500))
    assert out["so_dong"] == 4
    assert out["da_cat"] is False


def test_criteria_thieu_khoa_bi_tu_choi_co_cau_truc(db, kho):
    """N6: criteria do model sinh có thể thiếu khoá — phải trả lỗi có cấu trúc, không ném
    KeyError giữa vòng chat."""
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(loc_co_phieu(db, criteria=[{"metric_code": "rtd21", "operator": "<"}]))
    assert out["loi"] is True


def test_criteria_thieu_metric_code_bi_tu_choi_co_cau_truc(db, kho):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(loc_co_phieu(db, criteria=[{"operator": "<", "value": 5}]))
    assert out["loi"] is True


def test_criteria_khong_phai_object_bi_tu_choi_co_cau_truc(db, kho):
    """criteria=["rtd21 < 5"] (chuỗi thay vì object) từng ném AttributeError vì code gọi
    thẳng c.get(...) trên một str."""
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(loc_co_phieu(db, criteria=["rtd21 < 5"]))
    assert out["loi"] is True


def test_criteria_metric_code_falsy_van_bi_chan(db, kho):
    """Whitelist cũ dùng truthiness (`if c and ...`) nên bỏ lọt None/''/0 qua vòng kiểm — phải
    chặn bằng isinstance, không phụ thuộc giá trị có falsy hay không."""
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(loc_co_phieu(db, criteria=[{"metric_code": None, "operator": "<", "value": 5}]))
    assert out["loi"] is True


def test_criteria_value_khong_phai_so_bi_tu_choi_co_cau_truc(db, kho):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(loc_co_phieu(db, criteria=[{"metric_code": "rtd21", "operator": "<", "value": "nam"}]))
    assert out["loi"] is True


def test_criteria_value_bool_bi_tu_choi_khong_lot_qua_isinstance_int(db, kho):
    """F6 (review CHUẨN lát 10, vòng 2): Python coi bool là con của int nên
    isinstance(True, (int, float)) == True — value: true lọt qua vòng kiểm rồi chết ở tầng SQL
    (ProgrammingError: operator does not exist: numeric < boolean) thay vì trả lỗi có cấu trúc."""
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(loc_co_phieu(db, criteria=[{"metric_code": "rtd21", "operator": "<", "value": True}]))
    assert out["loi"] is True


def test_hoi_toan_ma_khong_ton_tai_thi_khong_tra_ma_bat_ky(db, kho):
    """Hồi quy — review vòng 2, mục CHẶN.

    Bản sửa trước đổi tham số SQL từ *mã người hỏi* sang *mã tra được*, nhưng giữ nguyên
    mệnh đề canh `cardinality(:mas) = 0 OR ...`. Danh sách rỗng vốn có nghĩa "không lọc theo
    mã, lọc theo ngành", nay lại có nghĩa "không mã nào tra được" ⇒ hỏi một mã bịa thì hàm mở
    toang truy vấn và trả 10 mã bất kỳ của thị trường kèm `co_du_lieu: true`. Trước khi sửa
    nó trả rỗng (sai im lặng); sau khi sửa nó trả **dữ liệu sai một cách tự tin** — nặng hơn.
    Đo trên kho thật 2026-09-07: `so_sanh_cung_nganh(["ABCDE"])` → A32, AAA, AAH, AAM, AAN…

    F1 (review CHUẨN lát 10, vòng 3): hình dạng "không mã nào tồn tại" trước đây tự dựng tay,
    mang `so_dong`/`du_lieu` (mượn của hình dạng #4) và VỨT ĐI `goi_y` mà resolve_ticker đã
    tính sẵn. Test này giờ canh đúng hình dạng #1 (tim_thay/goi_y), không có so_dong/du_lieu.
    """
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(so_sanh_cung_nganh(db, tickers=["ABCDE"], metric_codes=["rtd21"]))
    assert out["tim_thay"] is False
    assert "du_lieu" not in out
    assert "so_dong" not in out
    assert out["khong_tim_thay"] == ["ABCDE"]
    assert out["goi_y"] == {"ABCDE": []}, "ABCDE không gần giống mã nào trong kho fixture"


def test_hoi_qua_tran_ma_nhung_mot_vai_ma_sau_co_that_van_duoc_nhan_ra(db, kho):
    """F2 (review CHUẨN lát 10, vòng 3): chốt "không mã nào tồn tại" trước đây chỉ xét
    `mas_xin[:TRAN_MA]` — 10 mã đầu bịa còn mã thứ 11-12 có thật (HPG, VCB) thì bị khẳng định
    sai là "không mã nào trong danh sách tồn tại trong danh bạ" mà không hề tra tới chúng.
    Chốt phải soi TOÀN BỘ danh sách người hỏi, TRAN_MA chỉ giới hạn số mã đưa vào kết quả."""
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    mas = [f"ZZ{i:02d}" for i in range(10)] + ["HPG", "VCB"]          # 12 mã, 10 mã đầu bịa
    out = json.loads(so_sanh_cung_nganh(db, tickers=mas, metric_codes=["rtd21"]))
    assert out["tim_thay"] is True
    assert {c["ma"] for c in out["du_lieu"]} == {"HPG", "VCB"}
    assert set(out["khong_tim_thay"]) == {f"ZZ{i:02d}" for i in range(10)}


def test_da_cat_khong_bao_sai_khi_hoi_dung_bang_tran_ma(db, kho, monkeypatch):
    """B2 (review lát 10): điều kiện cũ `len(rows) >= TRAN_MA` báo da_cat=True dù không cắt gì
    khi hỏi ĐÚNG TRAN_MA mã hợp lệ và tất cả đều có phiên screener — kết quả bị chặn bởi chính
    danh sách mas_xin, không phải bởi LIMIT. Hạ TRAN_MA xuống 3 (monkeypatch, cùng khuôn
    test_vuot_tran_phien... ở test_a05_price) rồi hỏi đúng 3 mã có thật trong fixture."""
    import agent.tools.compare_peers as compare_peers_mod
    monkeypatch.setattr(compare_peers_mod, "TRAN_MA", 3)
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(so_sanh_cung_nganh(db, tickers=["HPG", "VCB", "TIN"], metric_codes=["rtd21"]))
    assert out["so_dong"] == 3
    assert out["da_cat"] is False


def test_mot_phan_ma_hop_le_van_kem_goi_y_cho_ma_truot(db, kho):
    """B3 (review lát 10): nhánh 'một phần mã hợp lệ' (ít nhất một mã tra được) chỉ liệt mã
    trượt vào khong_tim_thay mà không kèm goi_y, trong khi nhánh 'không mã nào hợp lệ' (F1,
    xem test_hoi_toan_ma_khong_ton_tai_thi_khong_tra_ma_bat_ky) đã trả goi_y dạng dict. Đồng
    bộ để nhánh nào có mã trượt cũng kèm gợi ý. HPGX gõ nhầm HPG — trigram đã xác nhận cho
    đúng gợi ý này ở test_resolve_ticker_ma_bia_thi_co_goi_y (test_a04_shared.py)."""
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(so_sanh_cung_nganh(db, tickers=["HPG", "HPGX"], metric_codes=["rtd21"]))
    assert out["khong_tim_thay"] == ["HPGX"]
    assert "HPG" in out["goi_y"]["HPGX"]


def test_hoi_nganh_khong_kem_ma_van_loc_theo_nganh(db, kho):
    """Chốt chặn cho bản sửa trên: nhánh 'chỉ lọc theo ngành' phải còn nguyên tác dụng."""
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(so_sanh_cung_nganh(db, industry_code="NGANHANG", metric_codes=["rtd21"]))
    assert out["so_dong"] > 0
    assert {d["ma"] for d in out["du_lieu"]} <= {"VCB", "TIN", "HDB", "LPB"}
