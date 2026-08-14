# -*- coding: utf-8 -*-
"""gen_field_selection.py — sinh docs/20-design/market-field-selection.{md,json}
tu MOT nguon du lieu duy nhat (bien ROWS ben duoi).

Chay:  PYTHONIOENCODING=utf-8 python gen_field_selection.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

DICT = HERE.parent / "10-sources" / "market" / "field-dictionary.json"
OUT_MD = HERE / "market-field-selection.md"
OUT_JSON = HERE / "market-field-selection.json"

with open(DICT, encoding="utf-8") as f:
    d = json.load(f)
RATIO = d["chi_tieu_ty_so_va_thi_truong"]
BCTC = d["chi_tieu_bao_cao_tai_chinh"]


def dict_name(code):
    c = code.lower()
    v = RATIO.get(c) or BCTC.get(c) or {}
    return v.get("ten_vi")


ROWS = []   # moi phan tu: dict(code, name_vi, name_src, source, nguon_chuan, keep, reason, status, block)

# nguon cua TEN — bat buoc ghi, khong duoc de mac dinh nham lan:
#   "từ điển"          ten_vi lay tu field-dictionary.json (729 ma)
#   "tài liệu endpoint" chep tu bang mo ta truong cua tai lieu endpoint (01, 04, 09)
#   "suy theo luật kỳ"  ma TTM/Y suy tu ma goc theo luat hau to cua phu luc A
#   "tự đặt"            toi tu dat theo mo ta NHOM trong tai lieu nguon — khong phai ten chinh thuc
#   "—"                 khong co ten


def add(codes, source, nguon_chuan, keep, reason, status="chốt", names=None, block="",
        nsrc="tài liệu endpoint"):
    """names: dict override ten_vi (cho ma khong co ten trong tu dien 729).
    nsrc: nguon cua cac ten override trong `names`."""
    names = names or {}
    for c in codes:
        name = names.get(c, dict_name(c))
        if name is None:
            src = "—"
        elif c in names:
            src = nsrc
        else:
            src = "từ điển"
        ROWS.append({
            "code": c,
            "name_vi": name,
            "name_src": src,
            "source": source,
            "nguon_chuan": nguon_chuan,
            "keep": keep,
            "reason": reason,
            "status": status,
            "block": block,
        })


# ───────────────────────── BVSC — nhom gia, realtime ─────────────────────────
BV = "BVSC `datafeed/instruments` + realtime"
add(["closePrice", "ceiling", "floor", "reference", "open", "high", "low", "averagePrice", "PRIOR_PRICE"],
    "BVSC", "BVSC", True,
    "giá — nguồn realtime khớp trực tiếp với sàn, ưu tiên tuyệt đối cho giá và mọi thứ dẫn xuất từ giá",
    names={"closePrice": "Giá khớp gần nhất", "ceiling": "Trần", "floor": "Sàn", "reference": "Tham chiếu",
           "open": "Mở cửa", "high": "Cao nhất", "low": "Thấp nhất", "averagePrice": "Giá bình quân phiên",
           "PRIOR_PRICE": None}, block="Giá")
add(["totalTrading", "totalTradingValue", "closeVol"], "BVSC", "BVSC", True,
    "khối lượng và giá trị khớp lệnh — lấy cùng nguồn với giá để không lệch chuỗi",
    names={"totalTrading": "Tổng khối lượng khớp lệnh", "totalTradingValue": "Tổng giá trị khớp lệnh",
           "closeVol": "Khối lượng của lệnh khớp gần nhất"}, block="Khối lượng, giá trị")
add(["bidPrice1", "bidPrice2", "bidPrice3", "bidVol1", "bidVol2", "bidVol3",
     "offerPrice1", "offerPrice2", "offerPrice3", "offerVol1", "offerVol2", "offerVol3",
     "TOTAL_BID_QTTY", "TOTAL_OFFER_QTTY"], "BVSC", "BVSC", True,
    "sổ lệnh 3 bậc — chỉ có nghĩa ở nguồn realtime; BVSC cấp 3 bậc cho mọi sàn",
    names={**{f"bidPrice{i}": f"Giá dư mua bậc {i}" for i in (1, 2, 3)},
           **{f"bidVol{i}": f"Khối lượng dư mua bậc {i}" for i in (1, 2, 3)},
           **{f"offerPrice{i}": f"Giá dư bán bậc {i}" for i in (1, 2, 3)},
           **{f"offerVol{i}": f"Khối lượng dư bán bậc {i}" for i in (1, 2, 3)},
           "TOTAL_BID_QTTY": "Tổng dư mua", "TOTAL_OFFER_QTTY": "Tổng dư bán"}, block="Sổ lệnh 3 bậc")
add(["foreignBuy", "foreignSell", "foreignRemain", "foreignRoom"], "BVSC", "BVSC", True,
    "khối ngoại trong phiên — nguồn realtime, khớp sàn",
    names={"foreignBuy": "Khối ngoại mua trong phiên", "foreignSell": "Khối ngoại bán trong phiên",
           "foreignRemain": "Room còn lại", "foreignRoom": "Tổng room"}, block="Khối ngoại")
add(["PT_MATCH_QTTY", "PT_MATCH_PRICE", "PT_TOTAL_TRADED_QTTY", "PT_TOTAL_TRADED_VALUE"], "BVSC", "BVSC", True,
    "thoả thuận — nguồn realtime, khớp sàn",
    names={"PT_MATCH_QTTY": "Khối lượng lệnh thoả thuận gần nhất",
           "PT_MATCH_PRICE": "Giá lệnh thoả thuận gần nhất",
           "PT_TOTAL_TRADED_QTTY": "Luỹ kế khối lượng thoả thuận trong phiên",
           "PT_TOTAL_TRADED_VALUE": "Luỹ kế giá trị thoả thuận trong phiên"}, block="Thoả thuận")

# ───────────────────────── Screener — GIU ─────────────────────────
R_NAMED = ("tỷ số tài chính — nằm trong cụm 55 tỷ số được nêu đích danh khi chốt nguồn; "
           "không nguồn nào khác có")
R_CLASS = ("tỷ số tài chính/định giá — không rơi vào bất kỳ nhóm bỏ nào trong 113 trường bị loại, "
           "nên thuộc 80 trường giữ")
add(["rtd26", "rtd27", "rtd28", "rtd40"], "Screener", "Screener", True, R_NAMED, block="Định giá")
add(["rtd36", "rtd43", "rtd51", "rtd20Avg"], "Screener", "Screener", True,
    R_NAMED + " · nhóm cổ tức", block="Cổ tức")
add(["rtq4", "rtq6", "rtq7", "rtq77"], "Screener", "Screener", True,
    R_NAMED + " · nhóm đòn bẩy", block="Đòn bẩy, thanh toán")
add(["rtq78", "rtq79", "rtq83", "rtd52", "ryq160", "ryq166", "ryq176"], "Screener", "Screener", True,
    R_NAMED + " · nhóm tăng trưởng", block="Tăng trưởng")
add(["rqq23", "rqq25", "rqq27", "rqq29"], "Screener", "Screener", True,
    R_NAMED + " · nhóm chỉ tiêu theo quý", block="Sinh lời")
add(["rtd11", "rtd21", "rtd25", "rtd14", "rtd7"], "Screener", "Screener", True,
    R_CLASS + "; vốn hoá và EPS là mẫu số của chính các tỷ số FiinTrade nên phải lấy cùng bộ",
    block="Định giá")
add(["rtq12", "rtq14", "rtq25", "ryq25", "rtq29", "ryq29", "rtq27"], "Screener", "Screener", True,
    R_CLASS, block="Sinh lời")
add(["rqq6", "rtq3", "rtq2", "rtq1"], "Screener", "Screener", True, R_CLASS, block="Đòn bẩy, thanh toán")
add(["revGrowth", "prfGrowth"], "Screener", "Screener", True, R_CLASS, block="Tăng trưởng")
add(["rtd19"], "Screener", "Screener", True,
    "Beta — giữ theo quyết định của chủ dự án: tự tính được nhưng phải chọn chuẩn thị trường và số phiên, "
    "kết quả sẽ lệch số FiinTrade", block="Beta")
add(["corpOwnership", "organizationOwnership"], "Screener", "Screener", True,
    "hai chỉ tiêu sở hữu tổ chức KHÁC NHAU, không phải trùng tên — FPT 0,0567 vs 0,1555, ACB có cái này "
    "thiếu cái kia; `GetOwnership` không có tỷ lệ tổng hợp mà chỉ có danh sách cổ đông lớn",
    names={"organizationOwnership": "Sở hữu tổ chức (chỉ tiêu thứ hai, khác `corpOwnership`)"},
    nsrc="tự đặt", block="Sở hữu")
add(["revTTM", "revY", "isa1TTM", "isa1Y", "isa20TTM", "isa20Y", "isa3TTM",
     "isb25TTM", "isb25Y", "isi103TTM", "isi103Y", "rev", "prf"], "Screener", "Screener", True,
    "khối TTM/Y lấy trọn cụm — `isa20TTM` chính là mẫu số P/E của FiinTrade (vốn hoá ÷ `isa20TTM` khớp "
    "9/10 mã VN30) và KHÔNG bằng tổng 4 quý `isa20` (lệch tới 9,4%); tự tính lại sẽ ra P/E khác cột P/E "
    "ngay bên cạnh",
    names={"isa1TTM": "Doanh số (TTM) — suy từ `isa1`", "isa1Y": "Doanh số (năm trước) — suy từ `isa1`",
           "isa3TTM": "Doanh số thuần (TTM) — suy từ `isa3`",
           "isb25TTM": "Thu nhập lãi và các khoản thu nhập tương tự (TTM) — suy từ `isb25`",
           "isb25Y": "Thu nhập lãi và các khoản thu nhập tương tự (năm trước) — suy từ `isb25`",
           "isi103TTM": "Doanh thu phí bảo hiểm (TTM) — suy từ `isi103`",
           "isi103Y": "Doanh thu phí bảo hiểm (năm trước) — suy từ `isi103`"},
    nsrc="suy theo luật kỳ", block="TTM/Y")

# ───────────────────────── Screener — BO ─────────────────────────
add(["closePrice"], "Screener", "BVSC", False,
    "trùng BVSC — `closePrice`/`reference`; giá lấy nguồn realtime khớp sàn", block="Trùng BVSC")
add(["totalMatchVolume"], "Screener", "BVSC", False, "trùng BVSC — `totalTrading`", block="Trùng BVSC")
add(["totalMatchValue"], "Screener", "BVSC", False, "trùng BVSC — `totalTradingValue`", block="Trùng BVSC")
add(["foreignerRoom"], "Screener", "BVSC", False,
    "trùng BVSC — `foreignRemain` (room CÒN LẠI), **không phải** `foreignRoom` (tổng room). "
    "Đo 2026-08-15: `foreignerRoom` của Screener khớp cỡ `foreignRemain` của BVSC chứ không khớp "
    "`foreignRoom` — BID 906.709.318 vs `foreignRemain` 906.101.718 vs `foreignRoom` 2.184.019.563; "
    "FPT 371.145.103 vs 368.745.271 vs 840.019.946. Tên hai bên đặt ngược nhau",
    block="Trùng BVSC")
add(["percentPriceChange1Day", "percentPriceChange1Week", "percentPriceChange1Month",
     "percentPriceChange3Month", "percentPriceChange6Month", "percentPriceChange52Week",
     "percentPriceChangeYTD"], "Screener", "BVSC (tự tính)", False,
    "biến động giá — tính lại được từ chuỗi giá BVSC", block="Biến động giá")
add(["averageVolume1Week", "averageVolume2Week", "averageVolume1Month", "averageVolume3Month"],
    "Screener", "BVSC (tự tính)", False,
    "khối lượng bình quân 5/10/20 phiên và 3 tháng — tính lại được từ chuỗi khối lượng BVSC",
    block="KL bình quân")
add(["icbRank", "value", "growth", "momentum", "vgm", "fScore", "canslim"], "Screener", "— (không lưu)", False,
    "nhóm chấm điểm riêng của FiinTrade — quyết định của chủ dự án: không dùng điểm do bên thứ ba chấm",
    block="Chấm điểm")
add(["capitalStructure", "financialStrength", "financialPlan", "cfo", "debt", "equityInssurance"],
    "Screener", "— (không lưu)", False,
    "thành phần chấm điểm VGM — bỏ cùng nhóm chấm điểm, không dùng điểm bên thứ ba chấm",
    names={c: "Thành phần chấm điểm VGM" for c in
           ["capitalStructure", "financialStrength", "financialPlan", "cfo", "debt", "equityInssurance"]},
    nsrc="tự đặt", block="Chấm điểm")
TECH = ["rsi", "adx", "cci", "roc", "stochastic", "williams", "mfi",
        "ma9", "ma20", "ma50", "ma75", "ma100", "ma200", "sma20", "sma50", "sma100", "overSma50"]
add(TECH, "Screener", "BVSC (tự tính)", False,
    "chỉ báo kỹ thuật — tự tính từ giá BVSC; lấy của FiinTrade thì chỉ báo và giá đến từ hai chuỗi khác nhau",
    names={**{c: f"Trung bình động {c[2:]} phiên" for c in ["ma9", "ma20", "ma50", "ma75", "ma100", "ma200"]},
           **{c: f"Trung bình động giản đơn {c[3:]} phiên" for c in ["sma20", "sma50", "sma100"]},
           "overSma50": "Giá so với trung bình động 50 phiên (đo 2026-08-15: kiểu bool)"},
    nsrc="tự đặt", block="Chỉ báo kỹ thuật")
add(["c1", "c2", "h1", "h2", "l1", "l2", "o1", "o2"], "Screener", "BVSC", False,
    "OHLC hai phiên gần nhất — đã có trong chuỗi giá BVSC",
    names={c: "OHLC hai phiên gần nhất" for c in ["c1", "c2", "h1", "h2", "l1", "l2", "o1", "o2"]},
    nsrc="tự đặt", block="OHLC 2 phiên")
add(["isa20", "isa22", "cfa18"], "Screener", "BCTC đầy đủ", False,
    "trùng bộ báo cáo tài chính đầy đủ — nguồn chuẩn cho mọi mã `bs*` `is*` `cf*` `no*` là bộ 556 mã",
    block="Trùng BCTC")
add(["rs52w", "rs6m"], "Screener", "BVSC (tự tính)", False,
    "sức mạnh tương đối — tính lại được từ chuỗi giá BVSC",
    names={"rs52w": "Sức mạnh tương đối 52 tuần", "rs6m": "Sức mạnh tương đối 6 tháng"},
    nsrc="tự đặt", block="Sức mạnh tương đối")
add(["totalBuyTradeVolume", "totalSellTradeVolume"], "Screener", "MoneyFlow", False,
    "trùng MoneyFlow — chuỗi mua/bán chủ động lấy trọn bộ ở MoneyFlow",
    names={"totalBuyTradeVolume": "Khối lượng theo chiều mua",
           "totalSellTradeVolume": "Khối lượng theo chiều bán"},
    nsrc="tự đặt", block="Trùng MoneyFlow")

# ───────────────────────── Screener — DA CHOT BANG SO DO 2026-08-15 ─────────────────────────
# Bon nhom duoi day truoc mang trang thai `can kiem API`; loi goi that ngay 2026-08-15
# (`GetScreenerItems`, 1 tieu chi ClosePrice, comGroupCode ALL va VN30) da tra loi.
DO_0815 = {("Screener", "foreignerPercentage"), ("Screener", "freeFloatRate"),
           ("Screener", "averageValue1Week"), ("Screener", "averageValue2Week"),
           ("Screener", "averageValue1Month"), ("Screener", "averageValue3Month"),
           ("Snapshot", "outstandingShare"), ("Snapshot", "freeFloat")}

add(["foreignerPercentage"], "Screener", "Screener", True,
    "**đo 2026-08-15** — có thật trong khối `stockScreenerItem`, key camelCase `foreignerPercentage`. "
    "BVSC `datafeed/instruments` đo cùng lúc chỉ có room theo số cổ phiếu, không có trường tỷ lệ nào. "
    "Giá trị trùng khít Snapshot ở BID và FPT (0,17545313 · 0,27350383), lệch nhẹ ở VNM "
    "(0,496079 vs 0,49580332). Đây là nguồn duy nhất còn lại → **lấy**, và Snapshot bỏ theo",
    block="Sở hữu")
add(["freeFloatRate"], "Screener", "Screener", True,
    "**đo 2026-08-15** — có thật trong khối `stockScreenerItem`, key camelCase `freeFloatRate`, "
    "giá trị trùng khít Snapshot cả 3/3 mã đo (BID 0,06 · FPT 0,85 · VNM 0,4). "
    "→ **lấy** ở Screener, Snapshot bỏ theo",
    block="Sở hữu")
add(["averageValue1Week", "averageValue2Week", "averageValue1Month", "averageValue3Month"],
    "Screener", "BVSC (tự tính)", False,
    "**đo 2026-08-15** — có thật, key camelCase `averageValue1Week`…, nằm ngay cạnh `averageVolume*` "
    "trong cùng khối `stockScreenerItem` và cùng dạng chuỗi bình quân 5/10/20 phiên + 3 tháng. "
    "BVSC `datafeed/instruments` đo cùng lúc có `totalTradingValue` theo phiên, nên chuỗi GTGD bình quân "
    "tính lại được y như chuỗi KL bình quân → cùng nhóm lý do với `averageVolume*`, **bỏ**",
    block="GTGD bình quân")

# ───────────────────────── Screener — CAN KIEM API ─────────────────────────
add(["rtd53", "rtq81"], "Screener", None, None,
    "có trong từ điển 729 mã nhưng mang trạng thái CHƯA GIẢI MÃ — không nguồn nào có tên, chưa biết là "
    "chỉ tiêu gì nên chưa xếp được vào nhóm nào. **Đo 2026-08-15**: cả hai CÓ THẬT trong khối `financial` "
    "và có giá trị (FPT `rtd53`=5426,73780245 `rtq81`=−0,03335415 · VNM 4702,49259309 và 0,22632399 · "
    "BID cả hai `null`) — nhưng số đo chỉ chứng minh trường tồn tại, KHÔNG cho ra tên, nên vẫn chưa xếp được",
    status="cần kiểm API", block="Chưa giải mã")
add(["rtd39", "rtd54"], "Screener", None, None,
    "có mặt trong khối `financial` của response nhưng KHÔNG có trong từ điển 729 mã — chưa biết là chỉ tiêu gì. "
    "**Đo 2026-08-15**: đã dump khoá khối `financial` — cả hai CÓ THẬT và có giá trị "
    "(`rtd39` BID 3,42582495 · FPT 15,93348656 · VNM 15,38168732; `rtd54` FPT 12,5858301 · VNM 13,09943584 · "
    "BID `null`). Vế *có thật không* đã xong; vế *là chỉ tiêu gì* thì số đo không trả lời được nên vẫn giữ",
    status="cần kiểm API", block="Chưa giải mã")

# ───────────────────────── Snapshot — GIU 16 ─────────────────────────
add(["ceo", "competitors", "majorHoldings", "comTypeCode"], "Snapshot", "Snapshot", True,
    "hồ sơ doanh nghiệp — chỉ Snapshot có; `competitors` là danh sách mã cùng ngành, dùng ngay cho so sánh "
    "ngang ngành; `comTypeCode` quyết định gọi `GetSnapshot` hay `GetSnapshotNoneBank`",
    names={"ceo": "Tên tổng giám đốc", "competitors": "Danh sách mã cùng ngành để so sánh",
           "majorHoldings": "Các khoản đầu tư lớn", "comTypeCode": "Loại hình doanh nghiệp"},
    block="Hồ sơ doanh nghiệp")
add(["statePercentage", "stateVolumn", "foreignerVolumn", "totalForeignRoom", "maximumForeignPercentage"],
    "Snapshot", "Snapshot", True,
    "sở hữu chi tiết — nằm trong 16 trường độc quyền của Snapshot, không nguồn nào khác có",
    names={"statePercentage": "Tỷ lệ sở hữu nhà nước", "stateVolumn": "Khối lượng nhà nước nắm",
           "foreignerVolumn": "Khối lượng nước ngoài nắm", "totalForeignRoom": "Tổng room",
           "maximumForeignPercentage": "Trần sở hữu nước ngoài"}, block="Sở hữu chi tiết")
add(["rtq10", "rtq44", "rtq137", "rqq41", "valuePerShare"], "Snapshot", "Snapshot", True,
    "chỉ tiêu riêng của Snapshot — không có trong 83 tiêu chí Screener",
    names={"valuePerShare": "Mệnh giá"}, block="Chỉ tiêu riêng")
add(["year", "quarter"], "Snapshot", "Snapshot", True,
    "metadata kỳ báo cáo — bắt buộc để gắn chuỗi `quarterly`/`yearly` vào đúng kỳ",
    names={"year": "Năm báo cáo", "quarter": "Quý báo cáo"}, nsrc="tự đặt", block="Metadata")

# ───────────────────────── Snapshot — BO ─────────────────────────
add(["rtd11", "rtd14", "rtd21", "rtd25", "rtq12", "rtq14", "rtq29"], "Snapshot", "Screener", False,
    "trùng Screener — cùng mã, lấy ở Screener cho trọn bộ tỷ số", block="Trùng Screener")
add(["freeFloatRate", "foreignerPercentage"], "Snapshot", "Screener", False,
    "trùng Screener — **đo 2026-08-15 đã gỡ điều kiện**: cả hai có thật ở khối `stockScreenerItem` của "
    "`getScreenerItems` và đã chốt **lấy** bên Screener (xem §4.1), nên bỏ ở đây là bỏ đúng, không còn là "
    "*chờ chốt*. Giá trị hai bên trùng khít trên `freeFloatRate` 3/3 mã và trên `foreignerPercentage` 2/3 "
    "(VNM lệch 0,000276 — cùng chỉ tiêu, khác thời điểm chốt số)",
    names={"freeFloatRate": "Tỷ lệ free float", "foreignerPercentage": "Tỷ lệ sở hữu nước ngoài"},
    block="Trùng Screener")
add(["rtq25", "rtq1", "rtq2", "rtq3"], "Snapshot", "Screener", False,
    "trùng Screener — cùng mã trong 83 tiêu chí, lấy ở Screener", block="Trùng Screener")
add(["foreignerRoom"], "Snapshot", "BVSC", False, "trùng BVSC — `foreignRemain` (room còn lại)",
    names={"foreignerRoom": "Room còn lại"}, block="Trùng BVSC")
add(["lowestPrice1Year", "highestPrice1Year"], "Snapshot", "BVSC (tự tính)", False,
    "giá thấp nhất/cao nhất 52 tuần — dẫn xuất từ chuỗi giá, nguồn chuẩn là giá BVSC",
    names={"lowestPrice1Year": "Thấp nhất 52 tuần", "highestPrice1Year": "Cao nhất 52 tuần"},
    block="Trùng BVSC")
add(["averageMatchVolume1Month"], "Snapshot", "BVSC (tự tính)", False,
    "KLGD bình quân 1 tháng — tính lại từ chuỗi khối lượng BVSC; Screener cũng có trường tương đương "
    "`averageVolume1Month` và cũng bỏ",
    names={"averageMatchVolume1Month": "KLGD bình quân 1 tháng"}, block="Trùng BVSC")
add(["isa1", "isa22", "isb27", "isi103", "bsa53", "bsb104", "bsa1", "bsa23", "bsa54", "bsa78",
     "bsa80", "bsb98", "bsb113", "nob44", "cfa18"], "Snapshot", "BCTC đầy đủ", False,
    "trùng bộ báo cáo tài chính đầy đủ — nguồn chuẩn cho mọi mã `bs*` `is*` `cf*` `no*` là bộ 556 mã",
    block="Trùng BCTC")

# ───────────────────────── Snapshot — CAN KIEM API ─────────────────────────
add(["outstandingShare"], "Snapshot", "Snapshot", True,
    "**đo 2026-08-15** — phép kiểm đã định sẵn là *bằng `ListedShare` của BVSC thì bỏ, khác thì lấy*. "
    "Kết quả: BID 7.280.065.210 và VNM 2.089.955.445 bằng đúng `ListedShare`, nhưng **FPT 1.714.326.422 "
    "vs `ListedShare` 1.703.507.121 — lệch 10.819.301 CP (0,64%)**. Hai bên KHÔNG bằng nhau ⇒ **lấy**",
    names={"outstandingShare": "Số CP đang lưu hành"}, block="Sở hữu chi tiết")
add(["freeFloat"], "Snapshot", "Snapshot", True,
    "**đo 2026-08-15** — đã dump đủ 193 khoá `getScreenerItems`: Screener chỉ có tỷ lệ `freeFloatRate`, "
    "KHÔNG có trường khối lượng free float nào; BVSC `datafeed/instruments` (62 khoá) cũng không có. "
    "Snapshot là nguồn duy nhất (BID 436.803.912 · FPT 1.457.177.458 · VNM 835.982.178) ⇒ **lấy**",
    names={"freeFloat": "Khối lượng tự do chuyển nhượng"}, block="Sở hữu chi tiết")

# ───────────────────────── Snapshot — CAN KIEM API ─────────────────────────
add(["organCode"], "Snapshot", None, None,
    "khoá định danh, không phải chỉ tiêu — không nằm trong 16 trường độc quyền được liệt kê; "
    "khoá nối hiện lấy từ bảng `organization`. **Đo 2026-08-15**: có mặt trong `summary` của Snapshot và "
    "trong CẢ NĂM khối của `getScreenerItems`, nên không thiếu nguồn — nhưng đây là quyết định lúc cài ETL "
    "(lưu lại khoá hay nối sang bảng `organization`), không phải câu hỏi số đo trả lời được",
    names={"organCode": "Mã doanh nghiệp"}, status="cần kiểm API", block="Định danh")
add(["rtd53"], "Snapshot", None, None,
    "mã mang trạng thái chưa giải mã; cũng có mặt trong khối `financial` của Screener nên nếu quyết định "
    "lưu thì nguồn chuẩn là Screener. **Đo 2026-08-15**: hai bên trả cùng một số ở FPT và VNM "
    "(5426,73780245 · 4702,49259309) nên xác nhận là cùng chỉ tiêu; riêng BID thì Snapshot trả `0.0` còn "
    "Screener trả `null`. Vẫn chưa có tên nên chưa xếp được lấy hay bỏ",
    status="cần kiểm API", block="Chưa giải mã")

# ───────────────────────── xuat file ─────────────────────────
KEEP_TXT = {True: "lấy", False: "bỏ", None: "chưa rõ"}


def esc(s):
    return "—" if s is None else str(s).replace("|", "\\|")


def table(rows, show_block=True):
    head = ("| Mã | Tên | Nguồn tên | Lấy/Bỏ | Nguồn chuẩn | Lý do | Trạng thái |"
            "\n|---|---|---|---|---|---|---|")
    out = [head]
    for r in rows:
        out.append("| `{}` | {} | {} | {} | {} | {} | {} |".format(
            r["code"], esc(r["name_vi"]), r["name_src"], KEEP_TXT[r["keep"]], esc(r["nguon_chuan"]),
            esc(r["reason"]), r["status"]))
    return "\n".join(out)


def sel(source, keep=..., status=...):
    return [r for r in ROWS if r["source"] == source
            and (keep is ... or r["keep"] is keep)
            and (status is ... or r["status"] == status)]


def n(source, keep=..., status=...):
    return len(sel(source, keep, status))


scr_keep, scr_drop, scr_chk = n("Screener", True), n("Screener", False), n("Screener", None)
sn_keep, sn_drop, sn_chk = n("Snapshot", True), n("Snapshot", False), n("Snapshot", None)
bv_keep = n("BVSC", True)

# Dong "bo CO DIEU KIEN" cua Snapshot: da xep `bo` nhung van mang trang thai `can kiem API`.
# Truoc 2026-08-15 co 2 dong nhu vay (`freeFloatRate`, `foreignerPercentage`); so do da go
# dieu kien nen nay bang 0. Suy tu ROWS chu khong viet so cung — them dong moi thi phai
# viet lai van ban §5 va §8, assert nay bat truong hop do.
sn_cond_drop = n("Snapshot", False, "cần kiểm API")
assert sn_cond_drop == 0, (
    "Co %d dong Snapshot 'bo co dieu kien' — van ban §5.2/§5.3/§8 dang viet nhu the khong con dong nao. "
    "Cap nhat van ban truoc khi chay lai." % sn_cond_drop)

# doi soat theo nhom BO cua Screener (so cua quyet dinh 2026-08-14 vs so liet ke duoc)
SCR_DROP_GROUPS = [
    ("Trùng BVSC (giá, KL, sổ lệnh, khối ngoại, thoả thuận)", 31, "Trùng BVSC"),
    ("Chỉ báo kỹ thuật — tính từ giá BVSC", 20, "Chỉ báo kỹ thuật"),
    ("Nhóm chấm điểm riêng của FiinTrade", 20, "Chấm điểm:FT"),
    ("Biến động giá 1d–52w, YTD", 11, "Biến động giá"),
    ("OHLC hai phiên gần nhất", 8, "OHLC 2 phiên"),
    ("Thành phần chấm điểm VGM", 6, "Chấm điểm:VGM"),
    ("Trùng BCTC đầy đủ", 5, "Trùng BCTC"),
    ("ATO/ATC", 4, "ATO/ATC"),
    ("Khối lượng bình quân 5/10/20 phiên, 3 tháng", 4, "KL bình quân"),
    ("Sức mạnh tương đối", 2, "Sức mạnh tương đối"),
    ("Trùng MoneyFlow", 2, "Trùng MoneyFlow"),
    # Nhom nay khong co trong quyet dinh 2026-08-14 — chot bang so do 2026-08-15, nen cot
    # "Da chot" de trong thay vi bia mot con so.
    ("Giá trị GD bình quân 5/10/20 phiên, 3 tháng — *chốt bằng số đo 2026-08-15*", None, "GTGD bình quân"),
]


def count_scr_drop(tag):
    if tag == "Chấm điểm:FT":
        return len([r for r in ROWS if r["source"] == "Screener" and r["block"] == "Chấm điểm"
                    and r["name_vi"] != "Thành phần chấm điểm VGM"])
    if tag == "Chấm điểm:VGM":
        return len([r for r in ROWS if r["source"] == "Screener" and r["name_vi"] == "Thành phần chấm điểm VGM"])
    if tag == "ATO/ATC":
        return 0
    return len([r for r in ROWS if r["source"] == "Screener" and r["keep"] is False and r["block"] == tag])


SCR_KEEP_GROUPS = [
    ("55 mã tỷ số tài chính", 55,
     len([r for r in ROWS if r["source"] == "Screener" and r["keep"] and
          r["block"] in ("Định giá", "Cổ tức", "Đòn bẩy, thanh toán", "Tăng trưởng", "Sinh lời")])),
    ("`rtd19` Beta", 1, n("Screener", True) and len([r for r in ROWS if r["code"] == "rtd19"])),
    ("`corpOwnership` + `organizationOwnership`", 2,
     len([r for r in ROWS if r["source"] == "Screener" and r["keep"]
          and r["code"] in ("corpOwnership", "organizationOwnership")])),
    ("Khối TTM/Y trọn cụm", 13,
     len([r for r in ROWS if r["source"] == "Screener" and r["block"] == "TTM/Y"])),
    ("Phần còn lại của 80 trường — không nguồn nào nêu đích danh", 9, 0),
    ("`freeFloatRate` + `foreignerPercentage` — *chốt bằng số đo 2026-08-15*", None,
     len([r for r in ROWS if r["source"] == "Screener" and r["keep"]
          and r["code"] in ("freeFloatRate", "foreignerPercentage")])),
]

SN_GROUPS = [
    ("Giữ — 16 trường độc quyền", 16, sn_keep - 2),
    ("Giữ thêm — `outstandingShare` + `freeFloat`, *chốt bằng số đo 2026-08-15*", None, 2),
    ("Bỏ — trùng Screener", 18,
     len([r for r in ROWS if r["source"] == "Snapshot" and r["block"] == "Trùng Screener"])),
    ("Bỏ — trùng BCTC đầy đủ", 15,
     len([r for r in ROWS if r["source"] == "Snapshot" and r["block"] == "Trùng BCTC"])),
    ("Bỏ — trùng BVSC", 5,
     len([r for r in ROWS if r["source"] == "Snapshot" and r["block"] == "Trùng BVSC"])),
]


def lech(a, b):
    if a is None:
        return "mới đo 2026-08-15"
    return "khớp" if a == b else ("thiếu %d" % (a - b) if a > b else "dư %d" % (b - a))


def cnt_txt(a):
    return "—" if a is None else str(a)


def group_tables(source, keep=..., status=...):
    rows = sel(source, keep, status)
    blocks, order = {}, []
    for r in rows:
        if r["block"] not in blocks:
            blocks[r["block"]] = []
            order.append(r["block"])
        blocks[r["block"]].append(r)
    parts = []
    for b in order:
        parts.append("**%s** — %d trường\n\n%s" % (b, len(blocks[b]), table(blocks[b])))
    return "\n\n".join(parts)


md = """# Chọn trường cho ETL thị trường — bảng tường minh theo từng mã

**Ngày:** 2026-08-14 · **Đo lại và chốt thêm:** 2026-08-15 · **Trạng thái:** ✅ đã chốt ·
**Trải từ quyết định chọn nguồn ngày 2026-08-14**

**File sinh tự động** từ [`gen_field_selection.py`](gen_field_selection.py) — sửa qua script rồi chạy lại, không sửa tay. Bản [`market-field-selection.json`](market-field-selection.json) sinh cùng nguồn.

Tài liệu này trả lời đúng một câu hỏi của người viết ETL: **trường này lấy hay bỏ, nguồn chuẩn là ai, vì sao.**
Lý do ghi thẳng tại từng dòng — không phải tra chỗ khác, không phải diễn giải lại quyết định của ai.

Số đo nền — **đo lại toàn bộ ngày 2026-08-15**, khớp con số cũ và giải luôn hai chỗ vênh:

| Nguồn | Số trường | Ghi chú số đo 2026-08-15 |
|---|---:|---|
| Screener `getScreenerItems` | **193** | 193 là số khoá **phân biệt**. Con số 223 của tài liệu endpoint là **tổng kích thước 5 khối** (43+129+12+21+18) — 27 khoá nằm ở từ hai khối trở lên, dư đúng 30 lần. Cả hai đều đúng, không mâu thuẫn. Đo trên `comGroupCode=ALL` và `VN30` đều ra 193 |
| `GetSnapshot` (BID, ngân hàng) | **54** | `summary` 28 + `quarterly[0]`/`yearly[0]` 27, hợp lại 54 khoá phân biệt |
| BVSC `datafeed/instruments` | **62** | Đếm thật trên BID/FPT/VNM: 62/62/62 |

Chốt luôn ba điểm vênh cũ: **223 vs 193** không phải do loại hình doanh nghiệp mà do khoá lặp giữa các khối ·
BVSC **62 vs 50** thì 62 đúng *(chính ví dụ response trong tài liệu endpoint cũng có đủ 62 khoá — con số 50 ở
tiêu đề là đếm sai của tài liệu, đã sửa)* · mã trường Screener **không viết thường toàn bộ** mà chỉ hạ chữ cái
đầu: `ForeignerRoom` → `foreignerRoom`, `Rtq12` → `rtq12`.

Nguồn dẫn của từng bảng: [10 — Từ điển mã trường & Bộ sàng lọc](../10-sources/market/10-fiin-dictionary.md) ·
[Phụ lục A — mã trường](../10-sources/market/appendix-A-field-codes.md) ·
[field-dictionary.json](../10-sources/market/field-dictionary.json) ·
[04 — Hồ sơ doanh nghiệp](../10-sources/market/04-fiin-company-profile.md) ·
[01 — BVSC REST](../10-sources/market/01-bvsc-rest.md) ·
[Phụ lục B — độ phủ](../10-sources/market/appendix-B-coverage.md).

---

## 1 · Luật chọn nguồn

Chép nguyên từ [kiến trúc tổng thể §3.4](../00-overview/architecture.md):

> **Mỗi chỉ tiêu có đúng một nguồn chuẩn.** Chọn theo hai tiêu chí, xét theo thứ tự: *(1)* nguồn nào realtime
> và khớp sàn — ưu tiên tuyệt đối cho giá và mọi thứ dẫn xuất từ giá; *(2)* nguồn nào cho trọn bộ ngữ cảnh —
> trùng lặp không đủ là lý do để bỏ.
>
> **Nhóm chỉ tiêu dẫn xuất lẫn nhau thì lấy trọn bộ từ một nguồn.** Biến TTM sinh ra tỷ số, giá sinh ra chỉ
> báo. Trộn nguồn giữa chừng tạo ra dữ liệu **tự mâu thuẫn trong cùng một bảng** — chatbot lấy vốn hoá chia
> lợi nhuận sẽ ra P/E khác cột P/E ngay bên cạnh, mà không có gì báo sai.

| Nhóm | Nguồn chuẩn | Quy mô |
|---|---|---|
| Giá, KL, sổ lệnh, khối ngoại, thoả thuận, chỉ báo kỹ thuật | **BVSC** | ~40 trường, realtime |
| Tỷ số tài chính, Beta, sở hữu tổ chức, TTM | **Screener** | 80/193 |
| Hồ sơ DN, sở hữu chi tiết | **Snapshot** | 16/54 |
| Mọi mã `bs*` `is*` `cf*` `no*` | **BCTC đầy đủ** | 556 |
| Tự doanh, đóng góp chỉ số, chuỗi khối ngoại | **MoneyFlow** | BVSC không có |

Hai đánh đổi đã chấp nhận, ghi ở đây để không ai hoảng khi thấy số lệch:

- Beta và các tỷ số định giá của Screener tính trên **giá FiinTrade**, nên lệch nhẹ so với giá BVSC ta lưu.
  Lệch ở chữ số thập phân thứ hai của P/E là bình thường.
- ATO/ATC không lấy từ Screener: ETL Screener chạy sau 15:00 nên số đó đã là chuyện đã rồi. Chỗ nó có nghĩa
  là realtime — BVSC topic `i:` đã có. Ingester không bắt được thì sửa ở Ingester, không vá bằng bản chết.

## 2 · Cách đọc bảng

| Cột | Nghĩa |
|---|---|
| **Mã** | Tên trường **đúng như endpoint trả về**, đã đối chiếu với 193 khoá thật ngày 2026-08-15. `GetScreenerParameters` trả hoa chữ đầu (`Rtq12`, `ForeignerRoom`) còn `getScreenerItems` **chỉ hạ chữ cái đầu**, giữ nguyên phần sau: `rtq12`, `foreignerRoom`, `freeFloatRate`, `averageValue1Week`, `overSma50`, `isa20TTM`. Chuẩn hoá bằng cách viết thường TOÀN BỘ là sai — tra khoá sẽ trượt |
| **Tên** | Tên tiếng Việt. `—` nghĩa là **không nguồn nào đặt tên cho mã này, và tôi cũng không tự đặt** — mã mang trạng thái chưa giải mã trong từ điển, hoặc không có trong từ điển, mà mô tả nhóm ở tài liệu nguồn cũng không đủ để đặt một nhãn. Phân biệt với `tự đặt` ở dòng dưới: đó cũng là mã không nguồn nào đặt tên, nhưng có nhãn do tôi đặt theo mô tả nhóm |
| **Nguồn tên** | Tên đó ở đâu ra. `từ điển` = `ten_vi` trong từ điển 729 mã · `tài liệu endpoint` = chép từ bảng mô tả trường của tài liệu endpoint · `suy theo luật kỳ` = mã TTM/Y, suy từ mã gốc theo luật *cùng chữ số + cùng chữ thứ ba = cùng chỉ tiêu, khác kỳ* · **`tự đặt` = tôi đặt theo mô tả NHÓM trong tài liệu nguồn, KHÔNG phải tên chính thức của FiinGroup** |
| **Lấy/Bỏ** | `lấy` = ETL ghi vào kho · `bỏ` = không ghi · `chưa rõ` = chưa phân loại được |
| **Nguồn chuẩn** | Nơi duy nhất chỉ tiêu này được lấy. `(tự tính)` = tính lại từ chuỗi của nguồn đó |
| **Trạng thái** | `chốt` = suy được thẳng từ tài liệu nguồn hoặc từ nhóm lý do đã chốt · `cần kiểm API` = tài liệu không đủ căn cứ, phải gọi API đo mới kết luận được |

Phân bố cột **Nguồn tên** trên {total_rows} dòng: `từ điển` {n_dict} · `tài liệu endpoint` {n_doc} ·
`suy theo luật kỳ` {n_suy} · **`tự đặt` {n_tudat}** · `—` {n_noname}. Con số `tự đặt` đáng để ý: đó là những
mã mà **không nguồn nào cho tên**, tên trong bảng chỉ là nhãn mô tả để đọc cho tiện — đừng đem hiển thị cho
người dùng cuối như tên chính thức, và đừng dùng nó làm căn cứ suy nghĩa. Việc phân loại lấy/bỏ của các dòng
này **không dựa vào tên** mà dựa vào nhóm lý do, nên tên có là nhãn tự đặt cũng không ảnh hưởng.

**Trường không có trong bảng nghĩa là chưa liệt kê được**, không phải đã bỏ — xem [§7 đối soát](#7--đối-soát-số-đếm).

## 3 · BVSC — giá, sổ lệnh, khối ngoại, thoả thuận

{bvsc_n} trường được nêu đích danh, tất cả **lấy**. BVSC là nguồn realtime khớp trực tiếp với sàn; đây là
nhóm được ưu tiên tuyệt đối theo luật §1.

{bvsc}

⚠️ `bidPrice1` và `offerPrice1` trả về dạng **chuỗi**, bậc 2–3 trả về **số** — ép kiểu khi xử lý.
Chỉ báo kỹ thuật **tự tính từ chuỗi giá này**, không lấy của FiinTrade.
`PRIOR_PRICE` để trống tên là cố ý: nó chỉ xuất hiện trong ví dụ response, tài liệu endpoint không mô tả.

## 4 · Screener `getScreenerItems`

{scr_keep_n} lấy · {scr_drop_n} bỏ · {scr_chk_n} cần kiểm API — trên {scr_total} trường liệt kê được.

### 4.1 Lấy — {scr_keep_n} trường

{scr_keep}

### 4.2 Bỏ — {scr_drop_n} trường

{scr_drop}

### 4.3 Cần kiểm API — {scr_chk_n} trường

{scr_chk}

✅ **`freeFloatRate` và `foreignerPercentage` đã chốt bằng số đo 2026-08-15 — không còn treo.** Trước đây hai
mã này phải chốt cùng lúc với §5.2 (Snapshot bỏ chúng với nguồn chuẩn *dự kiến* là Screener), và rủi ro là
**không nguồn nào lưu**. Lời gọi thật đã trả lời: cả hai có mặt trong khối `stockScreenerItem`, giá trị trùng
khít Snapshot, nên **Screener giữ · Snapshot bỏ** — xem §4.1 và §5.2. Không còn thứ tự cài đặt nào phải chờ.

🔴 **Bẫy tên ngược ở `foreignerRoom`** *(đo 2026-08-15)*. Screener `foreignerRoom` là **room CÒN LẠI**, cùng
nghĩa với `foreignRemain` của BVSC — **không phải** `foreignRoom` (tổng room) dù tên gần giống hệt. Số đo:
BID `foreignerRoom` = 906.709.318 · BVSC `foreignRemain` = 906.101.718 · BVSC `foreignRoom` = 2.184.019.563.
Tổng room của Screener nằm ở khoá khác, trong khối `priceInfo`: `foreignTotalRoom` (BID 2.184.019.563, bằng
đúng `foreignRoom` của BVSC). Ánh xạ nhầm hai khoá này là sai gấp ~2,4 lần mà không có gì báo.

## 5 · Snapshot `GetSnapshot` / `GetSnapshotNoneBank`

{sn_keep_n} lấy · {sn_drop_n} bỏ · {sn_chk_n} chưa rõ — trên {sn_total} trường liệt kê được
(28 trường khối `summary` + các mã được nêu đích danh trong khối `quarterly`/`yearly`).

🔴 Chọn sai endpoint **không báo lỗi** mà làm gần một nửa số trường thành `null`: `comTypeCode = NH` dùng
`GetSnapshot`, còn `CT` `CK` `BH` dùng `GetSnapshotNoneBank`.

### 5.1 Lấy — {sn_keep_n} trường

{sn_keep}

⚠️ `rtq137` và `rqq41` **được giữ dù chưa có tên** — từ điển 729 mã ghi trạng thái chưa giải mã cho cả hai.
Giữ vì đây là chỉ tiêu chỉ Snapshot có, không phải vì đã hiểu nó là gì. Manh mối đã đo được: `rtq137` chỉ
ngân hàng mới có, dải 0,47%–2,23%, luôn nhỏ hơn NIM. Lưu thô, đừng gắn nhãn cho người dùng cuối cho tới khi
có tên chính thức.

### 5.2 Bỏ — {sn_drop_n} trường

{sn_drop}

✅ Hai dòng `freeFloatRate` và `foreignerPercentage` **đã hết "chờ chốt"** — số đo 2026-08-15 xác nhận
Screener có và giữ cả hai (§4.1), nên bỏ ở đây là bỏ đúng. Cài được ngay, không phải chờ gì nữa.

### 5.3 Cần kiểm API — {sn_chk_n} trường chưa phân loại

{sn_chk}

## 6 · Hai nhóm quyết định theo họ mã, không theo từng trường

**BCTC đầy đủ — giữ nguyên vẹn 556 mã.** Mọi mã tiền tố `bs*` `is*` `cf*` `no*` đều **lấy**, nguồn chuẩn là
bộ báo cáo tài chính đầy đủ. Không trải từng dòng ở đây vì quyết định là *theo họ mã*, không có trường hợp
ngoại lệ nào phải cân nhắc riêng; danh sách máy đọc đủ 556 mã kèm tên và đơn vị đã có sẵn ở
[field-dictionary.json](../10-sources/market/field-dictionary.json). Hệ quả trực tiếp: mọi mã `bs*` `is*`
`cf*` `no*` xuất hiện ở Screener hay Snapshot đều **bỏ** — đã ghi ở §4.2 và §5.2.

**MoneyFlow — giữ FiinTrade, BVSC không có.** Ba endpoint: `getForeign` (chuỗi khối ngoại intraday — BVSC
chỉ có theo từng mã, muốn tổng thị trường phải cộng 2.534 mã), `getProprietaryV2` (tự doanh — BVSC không
có), `getContribution` (đóng góp chỉ số — BVSC không có). Đã kiểm chứng chéo: `getContribution` trả
VN-INDEX 1.729,08 và −36,55, khớp chính xác bảng giá BVSC cùng thời điểm.

## 7 · Đối soát số đếm

Số bên trái là con số của quyết định chọn nguồn ngày 2026-08-14; số bên phải là số dòng tài liệu này thực sự
liệt kê được từ tài liệu nguồn. **Lệch không bị ép cho khớp** — lệch ở đâu ghi ở đó.

### 7.1 Screener — nhóm bỏ

| Nhóm lý do | Đã chốt | Liệt kê được | Lệch |
|---|---:|---:|---|
{scr_drop_rows}
| **Tổng bỏ** | **113** | **{scr_drop_n}** | **{scr_drop_lech}** |

### 7.2 Screener — nhóm giữ

| Nhóm | Đã chốt | Liệt kê được | Lệch |
|---|---:|---:|---|
{scr_keep_rows}
| **Tổng giữ** | **80** | **{scr_keep_n}** | **{scr_keep_lech}** |

### 7.3 Screener — tổng

| Hạng mục | Số |
|---|---:|
| Tổng trường quan sát được trên VN30 | 193 |
| Liệt kê được trong tài liệu này | {scr_total} |
| — trong đó `chốt` | {scr_chot} |
| — trong đó `cần kiểm API` | {scr_chk_n} |
| **Chưa liệt kê được** (không tài liệu nguồn nào nêu mã) | **{scr_missing}** |

Phép cộng khép kín: thiếu {scr_keep_lech_n} trường ở nhóm giữ + thiếu {scr_drop_lech_n} trường ở nhóm bỏ =
{scr_gap_total} trường chưa phân loại, bằng đúng {scr_missing} trường chưa liệt kê được + {scr_chk_n} trường
`cần kiểm API`. Không có trường nào bị đếm hai lần.

### 7.4 Snapshot

| Nhóm | Đã chốt | Liệt kê được | Lệch |
|---|---:|---:|---|
{sn_rows}
| **Tổng** | **54** | **{sn_total}** | **{sn_total_lech}** |

Phép cộng khép kín: thiếu {sn_gap_scr} trường ở nhóm trùng Screener + thiếu {sn_gap_bvsc} ở nhóm trùng BVSC
= {sn_gap_total} trường chưa phân loại theo các nhóm của quyết định 2026-08-14; trừ {sn_new_keep} trường đã
chốt **lấy** bằng số đo 2026-08-15 *(`outstandingShare`, `freeFloat` — trước đây nằm trong chính khoảng
trống này)* còn {sn_gap_left}, bằng đúng {sn_chk_n} dòng `cần kiểm API` + {sn_missing} trường chưa liệt kê
được.

**Khớp tuyệt đối ở hai nhóm quan trọng nhất:** 16/16 trường giữ và 15/15 trường trùng BCTC — đúng từng mã.
Đây là bằng chứng mạnh rằng phân rã 54 trường khi chốt nguồn dựa trên đúng hai khối `summary` và
`quarterly` mà tài liệu nguồn mô tả.

### 7.5 Ba chỗ lệch, nguyên nhân đã truy được

1. **Screener thiếu {scr_missing} mã.** Không tài liệu nguồn nào liệt kê đủ 193 trường của response. Chỉ có:
   83 tiêu chí của `GetScreenerParameters`, các mã được nêu đích danh khi chốt nguồn, và vài mã trong mô tả
   5 khối response (`priceInfo` 43 · `stockScreenerItem` 129 · `performance` 12 · `financial` 21 ·
   `technical` 18). Phần lớn 129 trường của `stockScreenerItem` không có mã nào được ghi ra.
2. **Nhóm ATO/ATC (4 trường) vẫn không liệt kê được dòng nào** — quyết định nêu nhóm nhưng không nêu mã.
   Số đo 2026-08-15 tìm được **hai** khoá ATO thật trong khối `priceInfo`: `atoPrice` và `atoVolume` (BID
   38.700 · 26.700), **không có khoá ATC nào** trong 193 khoá. Nghĩa là nhóm "ATO/ATC 4 trường" của quyết
   định 2026-08-14 không có đủ 4 mã tương ứng trong response. Chưa thêm dòng vào bảng vì chưa biết quyết
   định định đếm 4 trường nào; ghi lại đây để lần sau khỏi đo lại.
3. **Snapshot thiếu {sn_missing} trường trên 54.** Tài liệu endpoint mô tả `summary` 28 trường và một ví dụ
   khối `quarterly` **của bản ngân hàng**; bản phi ngân hàng có bộ chỉ tiêu khác. Số 54 là số đo, không phải
   danh sách được viết ra ở đâu. ✅ Đo 2026-08-15 xác nhận đúng như vậy: BID (`GetSnapshot`, ngân hàng) ra
   **54** khoá, còn FPT và VNM (`GetSnapshotNoneBank`) ra **56** — `summary` 28 giống nhau, khác nhau ở khối
   `quarterly`/`yearly` (27 của ngân hàng vs 28 của phi ngân hàng).

### 7.6 Giả định đã dùng — **đã kiểm bằng số đo 2026-08-15**

83 tiêu chí của `GetScreenerParameters` được coi là **đều có mặt trong response `getScreenerItems`**. Tài
liệu nguồn không khẳng định điều đó. Đã đối chiếu thật hai danh sách ngày 2026-08-15: **83/83 tiêu chí đều
có mặt** trong 193 khoá response, sau khi hạ chữ cái đầu. Giả định đúng, tổng đối soát §7.3 không phải đổi.

### 7.7 Hai điểm về tài liệu nguồn — **đã xử lý bằng số đo 2026-08-15**

- BVSC `datafeed/instruments`: quyết định chọn nguồn ghi **62 trường**, tài liệu endpoint ghi **50 trường**.
  ✅ **Đếm thật ngày 2026-08-15 trên BID/FPT/VNM: 62/62/62.** Số 62 đúng. Con số 50 là lỗi đếm của tài liệu
  endpoint — chính ví dụ response ngay dưới tiêu đề đó liệt kê đủ 62 khoá, không thiếu khoá nào so với số
  đo. Tài liệu endpoint đã sửa tiêu đề.
- `rtd39` và `rtd54` được tài liệu endpoint nêu là trường của khối `financial` của Screener, nhưng **không
  có trong từ điển 729 mã**. Đây **không** phải mâu thuẫn với tuyên bố phủ 100% của từ điển: các tuyên bố
  100% đều có phạm vi rõ ràng và **không phạm vi nào bao Screener** — 100% đo trên `GetBalanceSheet`,
  `GetIncomeStatement`, `GetCashFlow`, tức họ mã báo cáo tài chính. Với họ tỷ số thì từ điển tự ghi ngược
  lại: 173 mã nhưng chỉ **83 mã** truy được qua `GetScreenerParameters`, phần còn lại lấy từ bundle. Hai mã
  này rơi đúng vào vùng 90 mã không có nguồn API xác nhận. ✅ **Đã đo khối `financial` ngày 2026-08-15: cả
  hai có thật và có giá trị số** (`rtd39` BID 3,42582495 · FPT 15,93348656; `rtd54` FPT 12,5858301, BID
  `null`). Vế *có thật không* đã xong. Vế *là chỉ tiêu gì* thì số đo không trả lời được, nên hai mã vẫn nằm
  ở §8 — nhưng nay là chờ **tên**, không còn là chờ **bằng chứng tồn tại**.

Số đo 2026-08-15 còn dựng được đủ 21 khoá của khối `financial`, trước đây tài liệu chỉ nêu một phần:
`organCode` `rtd7` `rtd11` `rtd14` `rtd19` `rtd21` `rtd25` `rtd39` `rtd51` `rtd53` `rtd54` `rtq12` `rtq81`
`rtq27` `rtq83` `isa3` `isa5` `isa20` `isa22` `cfa18` `fryq30`.

## 8 · Danh sách cần kiểm API — {chk_total} trường

Danh sách này **đã rút từ 16 xuống {chk_total} sau đợt đo 2026-08-15**. Mười dòng được chốt bằng số đo thật;
{chk_total} dòng còn lại thì số đo đã dùng hết công dụng — chúng chờ một cái **tên chỉ tiêu** hoặc một
**quyết định lúc cài ETL**, không phải chờ một lời gọi API nào nữa.

| Mã | Nguồn | Vì sao chưa chốt được | Phép kiểm sẽ kết luận |
|---|---|---|---|
{chk_rows}

Hai phép kiểm dự kiến gỡ khoảng trống §7.5 **đã chạy ngày 2026-08-15**, kết quả:

1. **`getScreenerItems` một tiêu chí duy nhất, dump đủ khoá của 5 khối** *(`ClosePrice`, `comGroupCode` =
   `ALL` rồi `VN30`, `pageSize` 30)*. Ra đúng **193 khoá phân biệt / 223 lượt xuất hiện**, giống nhau ở cả
   hai `comGroupCode`. Chốt được giả định §7.6 (83/83 tiêu chí đều có trong response), giải được cách chuẩn
   hoá hoa/thường, và cho thấy nhóm ATO chỉ có 2 khoá (`atoPrice`, `atoVolume`) chứ không phải 4 (§7.5).
   Vẫn còn **{scr_missing} mã chưa liệt kê được** — phần lớn nằm trong 129 khoá của `stockScreenerItem` mà
   không tài liệu nguồn nào ghi mã ra; số đo cho biết chúng TÊN gì nhưng không cho biết chúng LÀ gì, nên
   chưa xếp lấy/bỏ được.
2. **`GetSnapshot` (BID) và `GetSnapshotNoneBank` (FPT, VNM), dump khoá cả ba khối.** Bản ngân hàng ra đúng
   **54** khoá (`summary` 28 + `quarterly`/`yearly` 27); bản phi ngân hàng ra **56** (`summary` 28 +
   `quarterly`/`yearly` 28) — tức hai bản thật sự khác bộ chỉ tiêu, đúng như §7.5 điểm 3 dự đoán. Con số 54
   dùng làm mẫu số trong tài liệu này là của **bản ngân hàng**; với phi ngân hàng mẫu số là 56.

## 9 · Nhật ký thay đổi

| Ngày | Thay đổi |
|---|---|
| 2026-08-14 | Bản đầu — trải quyết định chọn nguồn ngày 2026-08-14 ra từng mã trường. 213 dòng: 57+34+16 lấy · 92 bỏ · 14 chưa rõ. 16 dòng mang trạng thái `cần kiểm API` (gồm 2 dòng đã xếp *bỏ* nhưng bỏ có điều kiện) |
| 2026-08-15 | **Đo thật, chốt 10/16 dòng `cần kiểm API`.** Gọi `GetScreenerParameters` (83 tiêu chí), `GetScreenerItems` 1 tiêu chí trên `ALL` và `VN30` (193 khoá), BVSC `/quotes?symbols=ALL` (2.534 bản ghi) và `/datafeed/instruments` (62 khoá), `GetSnapshot`/`GetSnapshotNoneBank` (54 / 56 khoá). Kết quả: `foreignerPercentage` + `freeFloatRate` → **lấy** ở Screener nên Snapshot bỏ hết điều kiện · `averageValue*` 4 mã → **bỏ** · `outstandingShare` + `freeFloat` → **lấy** ở Snapshot *(FPT lệch `ListedShare` 10.819.301 CP)* · `rtd39`/`rtd54` xác nhận có thật. Sửa **mã trường về đúng hoa/thường thật** — `getScreenerItems` chỉ hạ chữ cái đầu, viết thường toàn bộ sẽ trượt 31/83 khoá. Giải ba chỗ vênh: 223 = tổng 5 khối vs 193 khoá phân biệt · BVSC 62 đúng, 50 sai · `foreignerRoom` của Screener = `foreignRemain` của BVSC chứ không phải `foreignRoom`. Còn {chk_total} dòng `cần kiểm API`: {total_rows} dòng · {keep_total} lấy · {drop_total} bỏ · {chk_unknown} chưa rõ |
"""

chk_rows = []
for r in [x for x in ROWS if x["status"] == "cần kiểm API"]:
    if r["code"] in ("rtd39", "rtd54"):
        test = ("**số đo đã dùng hết công dụng** — dump khối `financial` ngày 2026-08-15 xác nhận trường có "
                "thật, nên việc còn lại là bổ sung vào từ điển 729 mã một cái TÊN. Không lời gọi nào cho ra "
                "tên; chỉ giải được khi FiinGroup trả lời hoặc bundle JS mới có")
    elif r["code"] in ("rtd53", "rtq81"):
        test = ("chưa có phép kiểm nào kết luận được — 5 cách đã thử đều không ra tên, và số đo 2026-08-15 "
                "chỉ thêm được dải giá trị chứ không thêm tên; chỉ giải được khi FiinGroup trả lời hoặc "
                "bundle mới có tên")
    else:  # organCode
        test = "quyết định lúc cài ETL: khoá nối lấy ở bảng `organization` hay lưu lại ở bảng Snapshot"
    chk_rows.append("| `%s` | %s | %s | %s |" % (r["code"], r["source"], esc(r["reason"]), test))

scr_drop_rows = "\n".join(
    "| %s | %s | %d | %s |" % (name, cnt_txt(cnt), count_scr_drop(tag), lech(cnt, count_scr_drop(tag)))
    for name, cnt, tag in SCR_DROP_GROUPS)
scr_keep_rows = "\n".join(
    "| %s | %s | %d | %s |" % (name, cnt_txt(cnt), got, lech(cnt, got)) for name, cnt, got in SCR_KEEP_GROUPS)
sn_rows = "\n".join(
    ["| %s | %s | %d | %s |" % (name, cnt_txt(cnt), got, lech(cnt, got)) for name, cnt, got in SN_GROUPS]
    # 4 dong `can kiem API` nam ngoai bon nhom tren: quyet dinh chua xep chung vao
    # nhom nao. Ghi thanh mot dong rieng de cot "Liet ke duoc" cong dung bang Tong.
    + ["| Ngoài nhóm — `cần kiểm API`, chưa xếp được vào nhóm nào | — | %d | ngoài nhóm |" % sn_chk])

scr_total = scr_keep + scr_drop + scr_chk
sn_total = sn_keep + sn_drop + sn_chk

md = md.format(
    bvsc=group_tables("BVSC"), bvsc_n=bv_keep,
    scr_keep=group_tables("Screener", True), scr_drop=group_tables("Screener", False),
    scr_chk=group_tables("Screener", None),
    sn_keep=group_tables("Snapshot", True), sn_drop=group_tables("Snapshot", False),
    sn_chk=group_tables("Snapshot", None),
    scr_keep_n=scr_keep, scr_drop_n=scr_drop, scr_chk_n=scr_chk, scr_total=scr_total,
    sn_keep_n=sn_keep, sn_drop_n=sn_drop, sn_chk_n=sn_chk, sn_total=sn_total,
    scr_drop_rows=scr_drop_rows, scr_keep_rows=scr_keep_rows, sn_rows=sn_rows,
    scr_drop_lech=lech(113, scr_drop), scr_keep_lech=lech(80, scr_keep),
    scr_drop_lech_n=113 - scr_drop, scr_keep_lech_n=80 - scr_keep,
    scr_gap_total=(113 - scr_drop) + (80 - scr_keep),
    scr_chot=scr_keep + scr_drop, scr_missing=193 - scr_total,
    sn_total_lech=lech(54, sn_total),
    sn_gap_scr=18 - SN_GROUPS[2][2], sn_gap_bvsc=5 - SN_GROUPS[4][2],
    sn_gap_total=(18 - SN_GROUPS[2][2]) + (5 - SN_GROUPS[4][2]), sn_missing=54 - sn_total,
    sn_new_keep=SN_GROUPS[1][2],
    sn_gap_left=(18 - SN_GROUPS[2][2]) + (5 - SN_GROUPS[4][2]) - SN_GROUPS[1][2],
    chk_rows="\n".join(chk_rows), chk_total=len([r for r in ROWS if r["status"] == "cần kiểm API"]), chk_unknown=scr_chk + sn_chk,
    n_dict=len([r for r in ROWS if r["name_src"] == "từ điển"]),
    n_doc=len([r for r in ROWS if r["name_src"] == "tài liệu endpoint"]),
    n_suy=len([r for r in ROWS if r["name_src"] == "suy theo luật kỳ"]),
    n_tudat=len([r for r in ROWS if r["name_src"] == "tự đặt"]),
    n_noname=len([r for r in ROWS if r["name_src"] == "—"]),
    total_rows=len(ROWS), keep_total=len([r for r in ROWS if r["keep"] is True]),
    drop_total=len([r for r in ROWS if r["keep"] is False]),
)

# Kiem TRUOC khi ghi file: trung ma thi khong duoc de lai output hong tren dia.
dups = {r["source"] + ":" + r["code"] for r in ROWS}
assert len(dups) == len(ROWS), "TRUNG MA trong cung mot nguon"

json_rows = [{"code": r["code"], "name_vi": r["name_vi"], "name_src": r["name_src"],
              "source": r["source"],
              "nguon_chuan": r["nguon_chuan"], "keep": r["keep"], "reason": r["reason"],
              "status": r["status"]} for r in ROWS]

with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
    f.write(md)
with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
    f.write(json.dumps(json_rows, ensure_ascii=False, indent=2) + "\n")

print("rows=%d  BVSC=%d  Screener=%d (keep %d / drop %d / check %d)  Snapshot=%d (keep %d / drop %d / check %d)"
      % (len(ROWS), bv_keep, scr_total, scr_keep, scr_drop, scr_chk, sn_total, sn_keep, sn_drop, sn_chk))
print("md:", OUT_MD)
print("json:", OUT_JSON)
