"""So sánh vài mã trên cùng bộ chỉ tiêu, cùng phiên screener gần nhất.

Cùng nguồn và cùng luật với screen_stocks.py: bảng nhãn đóng cho mã chỉ tiêu, và join
market.metric_dictionary phải khoá dictionary='field_dictionary' — (dictionary, code) là khoá
chính, schema cho phép cùng code tồn tại song song ở 'screener_params' nên phải khoá để
phòng thủ; đo kho thật 2026-09-07 chỉ có 'field_dictionary' (729 dòng), chưa từng nhân đôi.

TRAN_MA mã đầu tiên và bị hạ trần nếu xin nhiều hơn — báo qua da_cat. Mã xin mà không có mặt
trong kết quả không được âm thầm biến mất (N4, review CHUẨN lát 10) — VÀ phải phân biệt LÝ DO
(spec §4.6, review SPEC lát 10 §2.1): mã hoàn toàn không tồn tại trong market.security
(khong_tim_thay, hình dạng #1) khác hẳn mã CÓ danh tính nhưng phiên screener gần nhất không có
dòng cho nó — không phải cổ phiếu, hoặc chưa 'listed' (khong_co_du_lieu_phien). Trộn hai lý do
vào một trường mời model kết luận sai (ví dụ tưởng một mã có thật là gõ nhầm).

Hình dạng khi KHÔNG mã nào trong `tickers` tồn tại (F1/F2/mục 6, review lát 10 vòng 3):
`{"tim_thay": False, "khong_tim_thay": [...], "goi_y": {ma: [...]}, "ly_do": "..."}` — cùng
họ hình dạng #1 của tám hàm anh em (tim_thay/goi_y), khác ở chỗ nhận DANH SÁCH nên khong_tim_thay
là một mảng và goi_y là một DICT (mã hỏi -> gợi ý của riêng mã đó, vì resolve_ticker tính gợi ý
theo TỪNG mã, không gộp chung). KHÔNG mang so_dong/du_lieu — hai khoá đó chỉ có ở hình dạng #4
(có kết quả). Chốt xét trên TOÀN BỘ danh sách người hỏi (`mas_xin`), không phải phần đã cắt còn
TRAN_MA mã đầu — 10 mã đầu bịa mà mã 11 có thật vẫn phải nhận đúng mã 11 (F2).
"""
from __future__ import annotations

import sqlalchemy as sa

from agent.format import display_metric
from agent.labels import DEFAULT_RATIOS, LABELS
from agent.tools._shared import co_du_lieu, kiem_industry_code, resolve_ticker, rong, to_json

# Nới 10/8 -> 25/15 (mã / chỉ tiêu) — chủ dự án chốt 2026-09-07 "nới các giới hạn thoải mái
# ra, không phải sợ quá tốn kém token": ngữ cảnh model 1 triệu token không thiếu chỗ chứa;
# trần chỉ còn để bắt ca bệnh (model xin so sánh hàng trăm mã), không chặn so sánh nhóm ngành
# cỡ thường gặp.
TRAN_MA, TRAN_CHI_TIEU = 25, 15


def so_sanh_cung_nganh(conn: sa.Connection, tickers: list[str] | None = None,
                       metric_codes: list[str] | None = None,
                       industry_code: str | None = None) -> str:
    codes = list(metric_codes or []) or DEFAULT_RATIOS
    la = [c for c in codes if c not in LABELS]
    if la:
        return to_json({"loi": True, "ly_do": f"ma chi tieu ngoai bang nhan: {la}", "ma_hop_le": sorted(LABELS)})
    codes = codes[:TRAN_CHI_TIEU]
    mas_xin = [t.upper() for t in (tickers or [])]
    if not mas_xin and not industry_code:
        return to_json({"loi": True, "ly_do": "phai cho tickers hoac industry_code"})
    if industry_code:
        loi = kiem_industry_code(conn, industry_code)
        if loi:
            return to_json(loi)

    # resolve_ticker TỪNG mã trong TOÀN BỘ danh sách người hỏi (mas_xin, KHÔNG cắt về TRAN_MA
    # trước) để tách "hoàn toàn không tồn tại" (khong_tim_thay, hình dạng #1) khỏi "có danh
    # tính nhưng phiên này không có dòng screener" (khong_co_du_lieu_phien) — trộn chung là
    # đúng lỗi spec §4.6 cấm (#1 gộp vào #3). F2 (review CHUẨN lát 10, vòng 3): cắt trước rồi
    # mới xét khiến "10 mã đầu đều bịa, mã 11 có thật" bị khẳng định sai là "không mã nào tồn
    # tại" — TRAN_MA chỉ được giới hạn số mã ĐƯA VÀO truy vấn/kết quả, không giới hạn phạm vi
    # xét tồn tại.
    tra = {t: resolve_ticker(conn, t) for t in mas_xin}
    ma_hop_le_full = [t for t in mas_xin if tra[t]["tim_thay"]]
    khong_ton_tai = [t for t in mas_xin if not tra[t]["tim_thay"]]

    # 🔴 Người hỏi có cho mã mà KHÔNG mã nào tra được ⇒ dừng tại đây. Không được rơi xuống
    # truy vấn bên dưới: mệnh đề `cardinality(:mas) = 0` ở đó nghĩa là "không lọc theo mã",
    # nên danh sách rỗng sẽ mở toang cả thị trường và trả 10 mã bất kỳ kèm cờ "có dữ liệu" —
    # dữ liệu sai một cách tự tin, nặng hơn hẳn ca trả rỗng (review vòng 2, mục CHẶN).
    #
    # F1 (review CHUẨN lát 10, vòng 3): resolve_ticker ĐÃ tính goi_y bằng extensions.similarity
    # cho từng mã trượt — trả thẳng ra thay vì vứt đi, để ca thường gặp nhất (gõ nhầm MỘT mã)
    # có đường tự sửa, giống tám hàm anh em. goi_y là DICT mã->gợi ý (không gộp phẳng) vì mỗi
    # mã trượt có gợi ý riêng, gộp phẳng sẽ mất thông tin gợi ý nào ứng với mã nào (mục 6).
    if mas_xin and not ma_hop_le_full:
        goi_y = {t: tra[t]["goi_y"] for t in khong_ton_tai}
        return to_json({"tim_thay": False, "khong_tim_thay": khong_ton_tai, "goi_y": goi_y,
                        "ly_do": "không mã nào trong danh sách tồn tại trong danh bạ"})

    ma_hop_le = ma_hop_le_full[:TRAN_MA]

    ngay = conn.execute(sa.text("SELECT max(trading_date) FROM market.screener_daily")).scalar()
    if ngay is None:
        return to_json({**rong(), "ngay_du_lieu": None})
    rows = conn.execute(sa.text("""
        SELECT s.ticker, ind.name_vi AS nganh, sd.payload->'stockScreenerItem' AS item
        FROM market.screener_daily sd
        JOIN market.security s USING (security_id)
        LEFT JOIN market.v_issuer_industry v ON v.issuer_id = s.issuer_id
        LEFT JOIN market.industry ind ON ind.industry_id = v.industry_id
        WHERE sd.trading_date = :ngay AND s.status = 'listed'
          AND (cardinality(CAST(:mas AS text[])) = 0 OR upper(s.ticker) = ANY(:mas))
          AND (CAST(:nganh AS text) IS NULL OR ind.code = :nganh)
        ORDER BY s.ticker
        LIMIT :lim
    """), {"ngay": ngay, "mas": ma_hop_le, "nganh": industry_code, "lim": TRAN_MA}).all()
    if not rows:
        out_rong = {**rong(), "ngay_du_lieu": str(ngay)}
        if khong_ton_tai:
            # B3 (review lát 10): mọi nhánh có mã trượt phải kèm goi_y của ĐÚNG những mã đó —
            # cùng khuôn với nhánh "không mã nào hợp lệ" ở trên (F1), không chỉ liệt tên suông.
            out_rong["khong_tim_thay"] = khong_ton_tai
            out_rong["goi_y"] = {t: tra[t]["goi_y"] for t in khong_ton_tai}
        if ma_hop_le:
            out_rong["khong_co_du_lieu_phien"] = ma_hop_le
        return to_json(out_rong)

    units = {r.code: r.unit for r in conn.execute(sa.text(
        "SELECT code, unit FROM market.metric_dictionary"
        " WHERE dictionary = 'field_dictionary' AND code = ANY(:c)"), {"c": codes})}
    du_lieu = []
    for r in rows:
        ct = {}
        for code in codes:
            v = (r.item or {}).get(code)
            s = display_metric(v, units.get(code)) if v is not None else None
            if s is not None:
                ct[LABELS[code]] = s
        du_lieu.append({"ma": r.ticker, "nganh": r.nganh, "chi_tieu": ct})

    # N4: cắt câm ở TRAN_MA + nuốt mã không tra được — cả hai phải báo rõ, không im lặng.
    # len(mas_xin) > TRAN_MA: biết CHẮC ngay từ Python (đã cắt trước khi truy vấn) — đúng với
    # CẢ hai nhánh (có tickers hay chỉ industry_code), vì mas_xin rỗng thì > TRAN_MA luôn False.
    # len(rows) >= TRAN_MA: industry_code có thể còn nhiều mã hơn TRAN_MA, suy từ kết quả thật
    #   — CHỈ đáng tin khi KHÔNG có danh sách mã tường minh (mas_xin rỗng). B2 (review lát 10):
    #   điều kiện cũ áp luôn cả khi mas_xin có mã, gây dương tính giả — hỏi ĐÚNG TRAN_MA mã hợp
    #   lệ (không hơn) và tất cả đều có phiên screener thì rows == TRAN_MA dù KHÔNG có gì bị cắt
    #   (kết quả đã bị chặn bởi chính danh sách mas_xin, không phải bởi LIMIT). Khi mas_xin có
    #   mã, cỡ cắt thật duy nhất là len(mas_xin) > TRAN_MA — đã xét ở vế trái.
    da_cat = len(mas_xin) > TRAN_MA or (not mas_xin and len(rows) >= TRAN_MA)
    extra = {"ngay_du_lieu": str(ngay), "da_cat": da_cat}
    if khong_ton_tai:
        extra["khong_tim_thay"] = khong_ton_tai
        # B3: đồng bộ với nhánh "if not rows" ở trên — mã trượt luôn kèm gợi ý của chính nó.
        extra["goi_y"] = {t: tra[t]["goi_y"] for t in khong_ton_tai}
    if ma_hop_le:
        khong_co_phien = sorted(set(ma_hop_le) - {r.ticker for r in rows})
        if khong_co_phien:
            extra["khong_co_du_lieu_phien"] = khong_co_phien
    return to_json(co_du_lieu(du_lieu, **extra))
