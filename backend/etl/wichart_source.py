"""Bảng đo về nguồn WiChart — 87 key: series, đơn vị gốc, hệ số `scale`, role, cờ, tier, `SRCNOTE`.

Từng là khối Python §9 của `docs/10-sources/macro/wichart.md` (audit 2026-08-12, đo lại 2026-08-15 · 2026-09-05 · 2026-09-07).
Dời nguyên văn vào code 2026-09-08 (lát 12, Task 10a): code không đọc `docs/`, image không mang `docs/`.
Chủ sở hữu duy nhất của bảng này là module này; `wichart.md` giữ phần người đọc (bẫy, quy ước, cách đo).
Sửa số ở đây CHỈ khi đo lại (CLAUDE.md §1.2). `etl.wichart_registry.build()` ghép bảng này với MACRO/ASSET;
`docs/10-sources/macro/verify_wichart.py` đọc module này để đối chiếu với API sống.
"""

# wichart_registry.py — sinh từ audit 2026-08-12
# scale: nhân raw để về đơn vị gốc (đơn vị 1)
# role:  "data" = nguồn chính | "growth_ref" = bảng _raw_reference, không hiển thị

BASE = "https://api.wichart.vn/vietnambiz/vi-mo"
def url(key, group):
    return f"{BASE}?key=hang_hoa&name={key}" if group == "hang_hoa" else f"{BASE}?name={key}"

# (tên series, đơn vị gốc, scale, role, [cờ])
G = "growth_ref"; D = "data"

WICHART = {
# ---------- VĨ MÔ ----------
"gdp":        dict(g="vi_mo", tier="A", freq="q", frm="2010-03", lag=72, s=[
                  ("GPD theo giá hiện hành","VND",1e9,D,[]),
                  ("GPD theo giá so sánh","VND",1e9,D,["BREAK"]),
                  ("Tăng trưởng GDP","%",100,G,["PCTFRAC","LOWRES"])]),
"cpi":        dict(g="vi_mo", tier="A", freq="m", frm="2003-01", lag=42, s=[
                  ("CPI","%",1,D,[])]),
"iip":        dict(g="vi_mo", tier="A", freq="m", frm="2014-01", lag=42, s=[
                  ("Sản xuất công nghiệp","%",100,D,["PCTFRAC","LOWRES"])]),  # ngoại lệ đã chấp nhận
"pmi":        dict(g="vi_mo", tier="A", freq="m", frm="2015-07", lag=42, s=[
                  ("PMI","điểm",1,D,["SRCNOTE"])]),
"hhdv":       dict(g="vi_mo", tier="A", freq="m", frm="2004-01", lag=42, s=[
                  ("Tổng mức bán lẻ HH và DV","VND",1e9,D,[]),
                  ("Tăng trưởng","%",100,G,["PCTFRAC","LOWRES"])]),
"fdi":        dict(g="vi_mo", tier="A", freq="m", frm="2014-01", lag=42, s=[
                  ("FDI đăng ký","USD",1e6,D,[]),
                  ("FDI thực hiện","USD",1e6,D,[]),
                  ("Tăng trưởng FDI thực hiện","%",100,G,["PCTFRAC","LOWRES"]),
                  ("Tăng trưởng FDI đăng ký","%",100,G,["PCTFRAC","LOWRES"])]),
"cctm":       dict(g="vi_mo", tier="A", freq="m", frm="2009-01", lag=42, s=[
                  ("Xuất khẩu","USD",1e6,D,[]),
                  ("Nhập khẩu","USD",1e6,D,[]),
                  ("Cán cân thương mại","USD",1e6,D,["ZEROCROSS"])]),
"cctt":       dict(g="vi_mo", tier="A", freq="q", frm="2012-03", lag=164, s=[
                  ("Cán cân tổng thể","USD",1e6,D,["ZEROCROSS"]),
                  ("Cán cân vãng lai","USD",1e6,D,["ZEROCROSS"]),
                  ("Cán cân tài chính","USD",1e6,D,["ZEROCROSS"]),
                  ("Lỗi và sai sót","USD",1e6,D,["ZEROCROSS"])]),
"vdtptxh":    dict(g="vi_mo", tier="A", freq="q", frm="2013-12", lag=72, s=[
                  ("Vốn đầu tư phát triển xã hội","VND",1e12,D,[]),
                  ("Tăng trưởng","%",100,G,["PCTFRAC","LOWRES"])]),
"vdtnsnn":    dict(g="vi_mo", tier="A", freq="m", frm="2010-01", lag=42, s=[
                  ("Vốn đầu tư từ NSNN","VND",1e9,D,["UNITCHK"]),   # nhãn ghi "nghìn tỷ", thực là tỷ
                  ("Tăng trưởng","%",100,G,["PCTFRAC","LOWRES"])], flags=["FREQMIS"]),
"vt":         dict(g="vi_mo", tier="A", freq="m", frm="2015-01", lag=42, s=[
                  ("Vận chuyển Hành khách","lượt người",1e3,D,[]),   # lượt vận chuyển, không phải số người
                  ("Vận chuyển Hàng hoá","tấn",1e3,D,[])]),
"kqt":        dict(g="vi_mo", tier="A", freq="m", frm="2014-06", lag=42, s=[
                  ("Khách quốc tế","người",1e3,D,[]),
                  ("Tăng trưởng","%",100,G,["PCTFRAC","LOWRES"])]),
"ds":         dict(g="vi_mo", tier="A", freq="y", frm="2000-12", lag=224, s=[
                  ("Tổng dân số","người",1e3,D,[]),
                  ("Tăng trưởng","%",100,G,["PCTFRAC","LOWRES","CONST"])]),
"tn":         dict(g="vi_mo", tier="A", freq="q", frm="2015-03", lag=72, s=[
                  ("Tỷ lệ thất nghiệp","%",1,D,[])]),
"ld":         dict(g="vi_mo", tier="A", freq="q", frm="2012-03", lag=72, s=[
                  ("Tổng lao động","người",1e3,D,[]),
                  ("Tăng trưởng","%",100,G,["PCTFRAC","LOWRES"])]),
"tcns":       dict(g="vi_mo", tier="A", freq="q", frm="2009-03", lag=72, s=[
                  ("Thu ngân sách","VND",1e9,D,[]),
                  ("Chi ngân sách","VND",1e9,D,[]),
                  ("Bội chi ngân sách","VND",1e9,D,["ZEROCROSS"])]),
"ncp":        dict(g="vi_mo", tier="A", freq="y", frm="2013-12", lag=589, s=[
                  ("Nợ chính phủ","VND",1e9,D,[]),
                  ("Tỷ lệ nợ chính phủ/GDP","%",100,None,["PCTFRAC","LOWRES","DEAD"]),  # dừng 2023, bỏ
                  ("Tăng trưởng","%",100,G,["PCTFRAC","LOWRES"])]),
"gdpbinhquan":dict(g="vi_mo", tier="X", freq="y", frm="2000-01", lag=1319, s=[
                  ("Thu nhập bình quân","VND/người",1e6,None,["DEAD"])]),

# ---------- TIỀN TỆ ----------
"ctt":        dict(g="vi_mo", tier="A", freq="m", frm="2004-01", lag=72, s=[
                  ("Cung tiền tệ","VND",1e9,D,[]),
                  ("Tăng trưởng","%",100,G,["PCTFRAC","LOWRES"])]),
"hd":         dict(g="vi_mo", tier="A", freq="m", frm="2012-04", lag=72, s=[
                  ("Tổng tiền gửi","VND",1e9,D,[]),
                  ("Tăng trưởng","%",100,G,["PCTFRAC","LOWRES"])]),
"td":         dict(g="vi_mo", tier="A", freq="m", frm="2004-01", lag=72, s=[
                  ("Tổng tín dụng","VND",1e9,D,["NAMEWRONG"]),   # API ghi nhầm "Tổng tiền gửi"
                  ("Tăng trưởng","%",100,G,["PCTFRAC","LOWRES"])]),
"dtnh":       dict(g="vi_mo", tier="A", freq="m", frm="2000-04", lag=103, s=[
                  ("Dự trữ ngoại hối","USD",1e6,D,[])]),
"dhtg":       dict(g="vi_mo", tier="A", freq="d", frm="T-2y", lag=0, s=[
                  ("Tỷ giá USD trung tâm","VND/USD",1,D,[]),
                  ("Tỷ giá trần","VND/USD",1,D,[]),
                  ("Tỷ giá sàn","VND/USD",1,D,[]),          # unit API ghi "Đông" - lỗi chính tả
                  ("Tỷ giá USD NHTM bán ra","VND/USD",1,D,[]),
                  ("Tỷ USD tự do bán ra","VND/USD",1,D,[])], flags=["WIN2Y"]),
"lsdh":       dict(g="vi_mo", tier="A", freq="d", frm="T-2y", lag=0, s=[
                  ("Lãi suất chiết khấu","%",1,D,["CONST"]),
                  ("Lãi suất tái cấp vốn","%",1,D,["CONST"]),
                  ("LS qua đêm cho vay bù đắp thiếu hụt vốn","%",1,D,["CONST"])], flags=["WIN2Y"]),
"lslnh":      dict(g="vi_mo", tier="A", freq="d", frm="T-2y", lag=1, s=[
                  ("LS qua đêm liên ngân hàng","%",1,D,[]),
                  ("LS liên ngân hàng kỳ hạn 1 tuần","%",1,D,[]),
                  ("LS liên ngân hàng kỳ hạn 2 tuần","%",1,D,[])], flags=["WIN2Y"]),
"lshd":       dict(g="vi_mo", tier="A", freq="d", frm="T-2y", lag=0, s=[
                  ("1-3 tháng - NHTM Lớn","%",1,D,["SRCNOTE"]),
                  ("6-9 tháng - NHTM Lớn","%",1,D,["SRCNOTE"]),
                  ("13 tháng - NHTM Lớn","%",1,D,["SRCNOTE"])], flags=["WIN2Y"]),

# ---------- HÀNG HOÁ (tất cả freq="d", flags=["WIN2Y"]) ----------
# Nông thuỷ sản
"heo_hoi":         dict(g="hang_hoa", tier="A", s=[("Giá heo bình quân","VND/kg",1,D,[])]),
"ca_phe":          dict(g="hang_hoa", tier="A", s=[("Giá cà phê","VND/kg",1,D,[])]),
"tieu":            dict(g="hang_hoa", tier="A", s=[("Giá tiêu","VND/kg",1,D,[])]),
"duong":           dict(g="hang_hoa", tier="A", s=[("Giá đường","USD/tấn",1,D,[])]),
"dau_co_malaysia": dict(g="hang_hoa", tier="A", s=[("Giá dầu cọ","MYR/tấn",1,D,[])]),
"soi_coton":       dict(g="hang_hoa", tier="A", s=[("Giá sợi coton","CNY/tấn",1,D,[])]),
"lua":             dict(g="hang_hoa", tier="A", s=[("Giá lúa","VND/kg",1,D,["U1000"])]),
"gao_nguyen_lieu": dict(g="hang_hoa", tier="A", s=[("Giá gạo nguyên liệu","VND/kg",1,D,["U1000"])]),
"phu_pham_lua_gao":dict(g="hang_hoa", tier="A", s=[("Giá phụ phẩm lúa gạo","VND/kg",1,D,["U1000"])]),
"tom_the":         dict(g="hang_hoa", tier="A", s=[("Giá tôm thẻ","VND/kg",1,D,["U1000"])]),
"vai_cotton_my":   dict(g="hang_hoa", tier="A", s=[("Giá vải cotton","USD/lb",0.01,D,["SRCNOTE"])]),  # raw = US cent/lb (đo 2026-09-05 vs ICE CT=F)
"gao_tpxk":        dict(g="hang_hoa", tier="X", s=[("Giá gạo TPXK","VND/kg",1,None,["U1000","FROZEN"])]),
"ca_tra":          dict(g="hang_hoa", tier="A", s=[("Giá cá tra","VND/kg",1,D,[])]),  # FROZEN tại audit 12/08, sống lại 22/08 (đo 2026-09-05) — nâng Tier A ở lát 6 (VHC · ANV · IDI)
# Kim loại
"quang_sat":       dict(g="hang_hoa", tier="A", s=[("Giá quặng sát","CNY/tấn",1,D,[])]),
"vang":            dict(g="hang_hoa", tier="A", s=[("Giá vàng mua vào","VND/lượng",1e3,D,["UK1000"]),
                                                    ("Giá vàng bán ra","VND/lượng",1e3,D,["UK1000"])]),
"vang_the_gioi":   dict(g="hang_hoa", tier="A", s=[("Giá vàng","USD/ounce",1,D,[])]),
"chi":             dict(g="hang_hoa", tier="B", s=[("Giá chì","CNY/tấn",1,D,[])]),
"kem":             dict(g="hang_hoa", tier="B", s=[("Giá kẽm","CNY/tấn",1,D,[])]),
"nhom":            dict(g="hang_hoa", tier="B", s=[("Giá nhôm","CNY/tấn",1,D,[])]),
"niken":           dict(g="hang_hoa", tier="B", s=[("Giá Niken","CNY/tấn",1,D,[])]),
"dong":            dict(g="hang_hoa", tier="B", s=[("Giá đồng","USD/pound",1,D,[])]),
"bac":             dict(g="hang_hoa", tier="B", s=[("Giá bạc","USD/ounce",1,D,[])]),
"thiec":           dict(g="hang_hoa", tier="X", s=[("Giá thiếc","CNY/tấn",1,None,["DEAD"])]),
# Năng lượng
"dau_wti":         dict(g="hang_hoa", tier="A", s=[("Giá dầu WTI","USD/thùng",1,D,["SRCNOTE"])]),  # giá TƯƠNG LAI, không phải giao ngay
"khi_thien_nhien": dict(g="hang_hoa", tier="A", s=[("Giá khí thiên nhiên","USD/MMBtu",1,D,[])]),
"than_newcastle":  dict(g="hang_hoa", tier="A", s=[("Giá than","USD/tấn",1,D,[])]),
"than_coc":        dict(g="hang_hoa", tier="A", s=[("Giá than cốc","CNY/tấn",1,D,[])]),
"khi_lpg_trung_quoc":dict(g="hang_hoa", tier="A", s=[("Giá khí LPG","CNY/tấn",1,D,["LVLOFF"])]),
"xang_dau":        dict(g="hang_hoa", tier="A", s=[
                       ("Giá xăng RON 95","VND/lít",1e3,None,["SUBDEAD"]),   # chết 28/05/2026 - BỎ
                       ("Giá xăng E5","VND/lít",1e3,D,[]),
                       ("Dầu Diezen","VND/lít",1e3,D,[]),
                       ("Dầu hoả","VND/lít",1e3,D,[])]),
# Hoá chất & phân bón
"ure_trung_dong":      dict(g="hang_hoa", tier="A", s=[("Giá Ure","USD/tấn",1,D,[])]),
"phan_ure":            dict(g="hang_hoa", tier="A", s=[("Giá phân Ure Phú Mỹ","VND/kg",1,D,[]),
                                                        ("Giá phân Ure Cà Mau","VND/kg",1,D,[])]),
"phan_urea_trung_quoc":dict(g="hang_hoa", tier="A", s=[("Giá phân Urea","CNY/tấn",1,D,[])]),
"luu_huynh":           dict(g="hang_hoa", tier="A", s=[("Giá lưu huỳnh","CNY/tấn",1,D,[])]),
"phot_pho":            dict(g="hang_hoa", tier="A", s=[("Giá phốt pho","CNY/tấn",1,D,[])]),
# Nhựa & cao su
"nhua_pvc_trung_quoc": dict(g="hang_hoa", tier="A", s=[("Giá nhựa PVC","CNY/tấn",1,D,[])]),
"nhua_pp_trung_quoc":  dict(g="hang_hoa", tier="A", s=[("Giá nhựa PP","CNY/tấn",1,D,[])]),
"pet_trung_quoc":      dict(g="hang_hoa", tier="A", s=[("Giá PET","CNY/tấn",1,D,[])]),
"cao_su_nhat_ban":     dict(g="hang_hoa", tier="A", s=[("Giá cao su","JPY/kg",1,D,["SRCNOTE"])]),
"cao_su":              dict(g="hang_hoa", tier="X", s=[("Giá cao su","VND/TSC",1,None,["DEAD"])]),
# Thép & tôn
"hrc_trung_quoc":  dict(g="hang_hoa", tier="A", s=[("Giá HRC","CNY/tấn",1,D,[])]),
"thep_phe_anh":    dict(g="hang_hoa", tier="A", s=[("Giá thép phế","USD/tấn",1,D,["SRCNOTE"])]),
"thep_thanh_anh":  dict(g="hang_hoa", tier="A", s=[("Giá thép thanh","USD/tấn",1,D,["SRCNOTE"])]),
"ton_lanh_hoa_sen_045mm":     dict(g="hang_hoa", tier="A", s=[("Giá tôn lạnh Hoa Sen 0,45mm","VND/m2",1e3,D,[])]),
"ton_lanh_mau_hoa_sen_045mm": dict(g="hang_hoa", tier="A", s=[("Giá tôn lạnh màu Hoa Sen 0,45mm","VND/m2",1,D,["U1000"])]),
# Giấy & vải TQ
"giay_gon_song_trung_quoc": dict(g="hang_hoa", tier="A", s=[("Giá giấy gợn sóng","CNY/tấn",1,D,[])]),
"vai_coton":                dict(g="hang_hoa", tier="A", s=[("Giá vải coton","CNY/tấn",1,D,[])]),
}

# Tier X — không thu thập. Giữ danh sách để bộ giám sát biết đây là quyết định có chủ ý,
# không phải bỏ sót.
TIER_X = [
  "gdpbinhquan","gao_tpxk","thiec","cao_su","xi_mang","xi_mang_pcb",
  "da_0_4","da_1x2","da_mi_sang","da_hoc","be_tong_mac_300","be_tong_nhua_min",
  "coc_be_tong_du_ung_luc","gach_dat_set_nung","ong_nhua_27x18mm","ong_nhua_60x2mm",
  "ong_nhua_90x29mm","son_lot_khang_kiem_cao_cap","son_noi_that_tieu_chuan",
  "son_ngoai_that_tieu_chuan",
]

SRCNOTE = {
  ("thep_phe_anh", 0):   "Không phải giá tại Anh — là benchmark HMS 1&2 CFR Thổ Nhĩ Kỳ",
  ("thep_thanh_anh", 0): "Không phải giá tại Anh — là benchmark billet/rebar Thổ Nhĩ Kỳ",
  ("lshd", "*"):         "Lãi suất niêm yết TẠI QUẦY, bình quân MBB/ACB/TCB/VPB. "
                         "KHÔNG phải lãi suất online — chênh 1–2 điểm %",
  ("cao_su_nhat_ban",0): "TOCOM RSS3. Đơn vị API (Yên/kg) ĐÚNG; bảng web ghi Yên/tấn là sai",
  ("pmi", 0):            "S&P Global — dữ liệu độc quyền bên thứ ba, WiGroup cũng mua lại",
  ("vai_cotton_my", 0):  "Nhãn 'USD/tấn' SAI — raw là US cent/lb (82–93 khớp bậc ICE CT=F, lệch ≈1%, "
                         "nhãn ngày trễ 1 ngày so với phiên Mỹ). Đo 2026-09-05. Kho lưu USD/lb, scale 0,01",
  ("dau_wti", 0):        "Giá TƯƠNG LAI WTI tháng gần, KHÔNG phải giao ngay Cushing dù nhãn ghi "
                         "'Giá dầu WTI'. Lệch 0,50% so với Investing WTI tương lai (10 ngày); "
                         "2,85% so với FRED DCOILWTICO giao ngay (125 ngày) — chênh đó là "
                         "backwardation, không phải sai số. Đo 2026-08-15",
}
