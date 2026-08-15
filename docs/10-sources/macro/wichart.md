# 13 — API WiChart: Vĩ mô, Tiền tệ, Hàng hoá

**Phiên bản:** 1.1 · **Ngày audit:** 2026-08-12 *(rà lại vàng và dầu 2026-08-15)* · **Trạng thái:** 87 endpoint đã kiểm chứng sống, hiệu chuẩn đơn vị từng series

> Tài liệu này bổ sung mảng **vĩ mô — tiền tệ — giá hàng hoá** mà bộ nguồn BVSC/FiinTrade (file `00`–`12`) không có. Mọi số liệu trong đây đến từ lời gọi thật ngày 2026-08-12, không suy đoán từ tên endpoint.

---

## 1. Nguồn gốc và tình trạng pháp lý

| | |
|---|---|
| Host | `https://api.wichart.vn` |
| Chủ dữ liệu | **CTCP WiGroup** |
| Sản phẩm thương mại tương ứng | **WiFeed.vn** (bán API này kèm lịch sử đầy đủ) |
| Nơi phát hiện | Trang `data.vietnambiz.vn` — bản white-label hiển thị dữ liệu WiGroup theo giấy phép |
| Tình trạng pháp lý | ✅ **Giấy phép WiFeed đã chốt 2026-08-15** — chủ dự án xác nhận, phủ đúng endpoint `api.wichart.vn` đang dùng |

Nguồn gốc cấp trên của dữ liệu (xác định qua đối chiếu):

| Nhóm | Nguồn gốc thật |
|---|---|
| Vĩ mô | Tổng cục Thống kê (GSO) |
| Tiền tệ, lãi suất, tỷ giá | Ngân hàng Nhà nước (NHNN) |
| PMI | S&P Global (dữ liệu độc quyền, WiGroup cũng phải mua) |
| Kim loại, hoá chất, năng lượng CNY | **SunSirs** — khớp 0,00% tới từng chữ số thập phân |
| Thép phế/thanh | Benchmark **CFR Thổ Nhĩ Kỳ** (không phải Anh, xem `SRCNOTE`) |
| Cao su Nhật | TOCOM RSS3 |

Chuỗi phụ thuộc của Finext sẽ là 3 tầng: **nguồn gốc → WiGroup → Finext**.

---

## 2. Đặc tả API

### 2.1 Endpoint

```
GET https://api.wichart.vn/vietnambiz/vi-mo?name={key}                 # vĩ mô + tiền tệ
GET https://api.wichart.vn/vietnambiz/vi-mo?key=hang_hoa&name={key}    # hàng hoá
```

Không token, không API key, không cookie. `Access-Control-Allow-Origin: *` — không cần header `Origin`, không cần `User-Agent`.

⚠️ Giá trị `key` khác ngoài `hang_hoa` đều bị **bỏ qua âm thầm**: `key=tien_te` trả `200` với kết quả **giống hệt byte-for-byte** khi không truyền `key`. Các giá trị `chung_khoan`, `nganh`, `doanh_nghiep`, `vi_mo` trả `500`. Chỉ có đúng hai namespace.

### 2.2 Tham số `type`

Nhận các giá trị trong `timeArray` của chính endpoint đó. Giá trị ngoài danh sách trả `500 {"message":"Có lỗi xảy ra"}`. Với endpoint một tần suất, truyền `type` không đổi kết quả.

### 2.3 Cấu trúc response

```json
{
  "title": "Cán cân thương mại (Balance of Trade)",
  "titleIndex": ["53,095.5", "56,668.3"],
  "timeArray": ["m"],
  "unitArray": ["triệu USD", "triệu USD"],
  "stacked_column": false,
  "timeUpdate": "Tháng 07/2026",
  "is_growth": false,
  "chart": {
    "name": "Cán cân thương mại Việt Nam",
    "series": [
      { "name": "Xuất khẩu", "unit": "triệu USD", "type": "bar",
        "data": [[1782838800000, 53095.48], [1780246800000, 50809.07]] }
    ]
  }
}
```

| Trường | Ghi chú |
|---|---|
| `title` | Tên chỉ tiêu, đáng tin |
| `titleIndex` | Giá trị kỳ mới nhất, **đầy đủ độ chính xác**. ⚠️ **KHÔNG ánh xạ 1:1 với `series`** — xem Bẫy 3 |
| `timeArray` | Tần suất khai báo. ⚠️ **Sai ở 16 key** — xem Bẫy 4 |
| `unitArray` / `series[].unit` | ⚠️ **Sai ở 14 series** — xem Bẫy 2 |
| `timeUpdate` | Nhãn kỳ mới nhất, đáng tin, dùng làm khoá đối chiếu |
| `is_growth` | Không đáng tin, đừng dùng |
| `chart.series[].data` | `[epoch_ms, value]`, **mới nhất trước** |

### 2.4 🔴 Quy ước thời gian — đọc kỹ

**Mọi timestamp là 17:00 UTC = 00:00 giờ Việt Nam.** Bắt buộc parse bằng `Asia/Ho_Chi_Minh` (UTC+7). Parse bằng UTC sẽ làm mọi mốc lùi 1 ngày, và với chuỗi tháng sẽ tạo ảo giác lệch nhãn 1 tháng.

Ví dụ cụ thể, một mốc thật của chuỗi hàng hoá:

```
epoch = 1786726800000
  parse UTC  → 2026-08-14 17:00   ❌ chuỗi bị gán nhãn ngày 14/08
  parse ICT  → 2026-08-15 00:00   ✅ đúng nhãn ngày 15/08
```

```python
from datetime import datetime, timedelta, timezone
ICT = timezone(timedelta(hours=7))
dt = datetime.fromtimestamp(epoch_ms / 1000, tz=ICT)
```

> 🔴 **Lỗi này đã thật sự xảy ra, ngày 2026-08-15.** Một phép đối chiếu `dau_wti` với FRED parse bằng UTC làm **cả chuỗi WiChart lùi một ngày**, ghép nhầm phiên, và đẻ ra kết luận *"WiChart lệch giá dầu 3,35%, nên bỏ"*. Parse lại bằng ICT còn 2,85%; so với đúng chuẩn (giá tương lai) chỉ **0,50%** — kết luận **đảo ngược hoàn toàn**. Chi tiết ở §5.3, ghi chú dưới bảng **Năng lượng**.
>
> ⚠️ **Dấu hiệu nhận biết lệch nhãn ngày:** giá WiChart của ngày `d` **trùng khít** giá nguồn chuẩn của ngày `d±1`. Một chuỗi trùng khít nhưng lệch pha là bằng chứng **sai nhãn ngày**, không phải sai giá. Luôn chạy phép thử này trước khi kết luận một nguồn "lệch".

Bẫy múi giờ này không riêng WiChart — bản chung ghi ở [`../market/00-conventions.md`](../market/00-conventions.md).

Neo trong kỳ:

| Tần suất | Neo | Ví dụ |
|---|---|---|
| Ngày | chính ngày đó | `2026-08-12` |
| Tháng | **ngày 1 của tháng đó** | `2026-07-01` = tháng 7/2026 |
| Quý | **ngày 1 của tháng CUỐI quý** | `2026-06-01` = Q2/2026 |
| Năm | ⚠️ **không nhất quán** — `ds`/`ncp` dùng 31/12, `gdpbinhquan` dùng 01/01 | |

→ **Đừng suy kỳ báo cáo bằng số học ngày.** Khoá theo `timeUpdate`, hoặc dùng bảng neo đã hardcode ở §5.

### 2.5 Hiệu năng và cache

| | |
|---|---|
| Độ trễ | 110–300 ms |
| gzip | Giảm ~64% (6.255 → 2.255 byte). Luôn gửi `Accept-Encoding: gzip` |
| **ETag** | Có. `If-None-Match` trả `304`, 0 byte — **dùng cho ETL hàng ngày** |
| Tầng cache | Header `hit-cached: false/true`. Lần đầu miss, sau đó hit |
| Rate limit | **Chưa đo.** Không có header `X-RateLimit-*` hay `Retry-After` |
| Stack | nginx + Express (helmet.js). HTTP/1.1, quảng cáo h3 |

```bash
curl -H 'Accept-Encoding: gzip' -H 'If-None-Match: W/"186f-CySOaOuPFA8zslRCf1wtHyhEjRg"' \
  "https://api.wichart.vn/vietnambiz/vi-mo?name=cpi"
```

---

## 3. Sáu bẫy triển khai

### Bẫy 1 — Chuỗi ngày bị cắt cửa sổ trượt đúng 2 năm

Mọi series tần suất ngày (toàn bộ 61 key hàng hoá + `dhtg` `lsdh` `lslnh` `lshd`) bắt đầu tại **T-2 năm**, không có tham số `from`, không phân trang. Ngày không chạy ETL là ngày mất vĩnh viễn ở đuôi.

Chuỗi tháng/quý/năm thì sâu thật: `dtnh` từ 2000, `cpi` và `ctt` và `td` từ 2003–2004.

### Bẫy 2 — 🔴 Đơn vị sai 1000× rải rác ngẫu nhiên theo từng series

`unit` mô tả `titleIndex` (số hiển thị trên web), **không mô tả `series[].data`**. Khi hai cái lệch nhau, `data` lớn gấp 1000 lần đơn vị khai báo.

Không có quy luật phân loại nào bắt được. Bằng chứng — hai series cùng họ, cùng nhãn, ngược nhau:

```
da_0_4    unit="nghìn đồng/m3"  raw = 109.2      → nhãn ĐÚNG
da_1x2    unit="nghìn đồng/m3"  raw = 169200     → nhãn SAI (thực là đồng)

ton_lanh_hoa_sen_045mm      unit="nghìn đồng/m2"  raw = 119.9     → ĐÚNG
ton_lanh_mau_hoa_sen_045mm  unit="nghìn đồng/m2"  raw = 126500    → SAI

son_lot_khang_kiem_cao_cap  unit="nghìn đồng/lít" raw = 117.09    → ĐÚNG
son_noi_that_tieu_chuan     unit="nghìn đồng/lít" raw = 50000     → SAI
```

**Lỗi còn xảy ra theo chiều ngược lại**, và trúng một chỉ tiêu quan trọng:

```
vang  unit="VNĐ/lượng"  raw = 141300   → SAI, thực tế là NGHÌN đồng/lượng
```

Kiểm chứng bằng quy đổi độc lập: vàng thế giới 4.412,1 USD/oz × (37,5/31,1035) g × tỷ giá 26.270 = **139.742.152 VND/lượng**. Giá vàng miếng trong nước phải nhỉnh hơn con số đó — tức `141300 × 1000 = 141.300.000`, không phải `141.300`. Bảng hiển thị trên `data.vietnambiz.vn` cũng ghi sai theo (`Đồng/lượng | 144300`), nên **không thể lấy trang web làm chuẩn đối chiếu đơn vị**.

→ **Bắt buộc hardcode hệ số từng series.** Bảng đầy đủ ở §5.

### Bẫy 3 — `titleIndex` không ánh xạ 1:1 với `series`

Ghép theo chỉ số sẽ so nhầm series:

| key | `titleIndex` | Số series | Ánh xạ thật |
|---|---|---|---|
| `gdp` | 2 phần tử | 3 | `[1]` ứng với series **[2]** (Tăng trưởng), bỏ qua [1] |
| `ncp` | 2 phần tử | 3 | cùng kiểu nhảy cóc |
| `xang_dau` | 2 phần tử | 4 | ứng với RON 95 và Diezen, **bỏ qua E5 và Dầu hoả** |
| `dhtg` | 2 phần tử | 5 | 3 series không có đối chiếu |

→ Nếu cần ghép, ghép **theo giá trị** (thử các hệ số 1 / 1000 / 100 / 0.01), không theo chỉ số.

### Bẫy 4 — `timeArray` khai sai tần suất ở 16 key

`vdtnsnn` khai `"q"` nhưng thực tế là **tháng** (199 điểm, gap trung vị 31 ngày). 15 key nhóm VLXD khai `"d"` nhưng thực tế là **tháng** (18–22 điểm).

→ Suy tần suất từ **trung vị khoảng cách giữa các điểm**, không tin `timeArray`.

### Bẫy 5 — 🔴 Series "Tăng trưởng" lưu dạng phân số làm tròn 2 chữ số

Độ phân giải còn **1 điểm phần trăm**. Sai số trung bình 0,25 điểm %, tối đa 0,50 — đo trên **15 series**, cơ chế đồng nhất ở tất cả. Phân bổ: 13 series đi vào `growth_ref`, 1 series (`iip`) buộc phải giữ làm dữ liệu chính, 1 series (`ncp` tỷ lệ nợ/GDP) bị loại vì đã chết.

```
GDP tăng trưởng thật:  7,05% · 8,16% · 8,25% · 8,46% · 8,39%
API trả về:            0.07  · 0.08  · 0.08  · 0.08  · 0.08
```

`ds` (dân số) tệ nhất: 26 điểm dữ liệu chỉ còn **đúng 1 giá trị duy nhất**.

Cùng cơ chế: `iip` (chỉ có 1 series và nó là tăng trưởng) và `ncp` "Tỷ lệ nợ chính phủ/GDP".

→ **Không dùng làm dữ liệu.** Xem chính sách xử lý ở §6.2.

⚠️ Phân biệt: các series `%` sau là **phép đo gốc, đủ độ chính xác, phải giữ** — `cpi` · `tn` · `pmi` · toàn bộ `lsdh` `lslnh` `lshd` · toàn bộ `dhtg`.

### Bẫy 6 — Đứt gãy cấu trúc

`gdp` series "GPD theo giá so sánh" nhảy **+34,8%** tại 2026-03 do đổi năm gốc so sánh (trung vị biến động của chuỗi này chỉ 4,9%). Tự tính YoY xuyên mốc ra +74%, vô nghĩa.

Series "GPD theo giá hiện hành" thì **liên tục**, không đứt.

Hệ số nối tính được từ hai quý độc lập, thống nhất trong 0,34%:

```
Q2/2026:  2,854,515 / 1.0839 = 2,633,560  ÷ 1,642,683 (nền cũ)  →  1.6032
Q1/2026:  2,592,640 / 1.0794 = 2,401,927  ÷ 1,503,311 (nền cũ)  →  1.5978
```

⚠️ Hệ số nối **chỉ tính được nhờ series tăng trưởng** — đoạn cũ và đoạn mới không có kỳ nào chồng lấn. Đây là lý do giữ nhóm `GROWTH_REF` (§6.2).

Bộ dò đứt gãy tự động (biến động > 6× trung vị và > 25%) đã quét toàn bộ series tuyệt đối: **chỉ 1 đứt gãy thật, còn lại toàn báo động giả** — COVID (`kqt` 2020-04 −94%), mùa vụ Tết (`cctm` tháng 3 hàng năm +45~55%), dồn chi cuối năm (`tcns` tháng 12 +170~222%), và chuỗi cắt qua số 0 (`cán cân thương mại` +13.781%).

→ **Bảng đăng ký đứt gãy phải do người duyệt**, job đêm chỉ sinh ứng viên. Chuỗi cắt qua số 0 phải dùng test chênh lệch tuyệt đối chuẩn hoá, không dùng phần trăm.

---

## 4. Bộ ký hiệu

```python
FLAGS = {
  # --- đơn vị & thang đo ---
  "U1000":     "data thô = 1000× đơn vị nhãn; scale đã hiệu chỉnh trong bảng §5",
  "UK1000":    "data thô ở đơn vị 'nghìn'; scale đã hiệu chỉnh trong bảng §5",
  "PCTFRAC":   "% lưu dạng phân số, scale=100",
  "LOWRES":    "làm tròn 2 chữ số ⇒ phân giải 1 điểm %; KHÔNG hiển thị, KHÔNG định lượng",

  # --- thời gian ---
  "WIN2Y":     "cửa sổ trượt 2 năm, không có lịch sử sâu hơn",
  "FREQMIS":   "timeArray khai sai tần suất thật",
  "LAGM":      "trễ theo kỳ công bố cơ quan nhà nước (kèm số ngày điển hình)",
  "BREAK":     "có đứt gãy cấu trúc, xem BREAKS ở §5.3",

  # --- tình trạng ---
  "DEAD":      "nguồn đã ngừng cập nhật",
  "FROZEN":    "còn điểm dữ liệu mới nhưng giá trị không đổi quá lâu (carry-forward)",
  "SUBDEAD":   "một series con đã chết trong endpoint còn sống",
  "CONST":     "giá trị không đổi suốt toàn bộ lịch sử; xem ghi chú để biết là thật hay lỗi",

  # --- ngữ nghĩa ---
  "NAMEWRONG": "nhãn series đặt sai",
  "UNITCHK":   "nhãn đơn vị nghi sai, chưa xác minh được",
  "LVLOFF":    "mức giá lệch hệ thống so với benchmark; chỉ dùng xu hướng",
  "SRCNOTE":   "nguồn gốc/định nghĩa thật khác tên gọi",
}

TIERS = {
  "A": "Lõi — đưa vào sản phẩm và chatbot",
  "B": "Phụ — dữ liệu sạch nhưng ít liên quan cổ phiếu VN; dashboard, không vào chatbot",
  "R": "Chỉ tham chiếu — bảng _raw_reference, không bao giờ hiển thị",
  "X": "Loại — không thu thập",
}
```

---

## 5. Bảng tra 87 key

Quy ước cột: **scale** = hệ số nhân `raw` để về **đơn vị gốc (đơn vị 1)**. Không lưu "nghìn", "triệu", "tỷ" ở tầng dữ liệu.

### 5.1 Vĩ mô — 18 key

| key | Chỉ tiêu | Tần suất | Lịch sử | Trễ | Series | Đơn vị gốc | scale | Tier | Cờ |
|---|---|---|---|---|---|---|---|---|---|
| `gdp` | Tổng sản phẩm quốc nội | q | 2010-03 → | 72d | GDP giá hiện hành | VND | 1e9 | A | `LAGM` |
| | | | | | GDP giá so sánh | VND | 1e9 | A | `BREAK` 2026-03 |
| | | | | | Tăng trưởng GDP | % | 100 | R | `PCTFRAC` `LOWRES` |
| `cpi` | Lạm phát | m | 2003-01 → | 42d | CPI | % | 1 | A | `LAGM` |
| `iip` | Sản xuất công nghiệp | m | 2014-01 → | 42d | IIP (YoY) | % | 100 | A | `PCTFRAC` `LOWRES` ⚠️ |
| `pmi` | PMI | m | 2015-07 → | 42d | PMI | điểm | 1 | A | `LAGM` `SRCNOTE` |
| `hhdv` | Bán lẻ HH & DV | m | 2004-01 → | 42d | Tổng mức bán lẻ | VND | 1e9 | A | `LAGM` |
| | | | | | Tăng trưởng | % | 100 | R | `PCTFRAC` `LOWRES` |
| `fdi` | Đầu tư nước ngoài | m | 2014-01 → | 42d | FDI đăng ký | USD | 1e6 | A | |
| | | | | | FDI thực hiện | USD | 1e6 | A | |
| | | | | | Tăng trưởng ×2 | % | 100 | R | `PCTFRAC` `LOWRES` |
| `cctm` | Cán cân thương mại | m | 2009-01 → | 42d | Xuất khẩu | USD | 1e6 | A | |
| | | | | | Nhập khẩu | USD | 1e6 | A | |
| | | | | | Cán cân | USD | 1e6 | A | cắt qua 0 |
| `cctt` | Cán cân thanh toán | q | 2012-03 → | 164d | 4 series | USD | 1e6 | A | `LAGM` cắt qua 0 |
| `vdtptxh` | Vốn ĐT phát triển XH | q | 2013-12 → | 72d | Vốn đầu tư | VND | 1e12 | A | `LAGM` |
| | | | | | Tăng trưởng | % | 100 | R | `PCTFRAC` `LOWRES` |
| `vdtnsnn` | Vốn ĐT từ NSNN | **m** | 2010-01 → | 42d | Vốn đầu tư | VND | **1e9** | A | `FREQMIS` `UNITCHK` |
| | | | | | Tăng trưởng | % | 100 | R | `PCTFRAC` `LOWRES` |
| `vt` | Vận tải | m | 2015-01 → | 42d | Hành khách | **lượt người** | 1e3 | A | không phải số người, là lượt vận chuyển |
| | | | | | Hàng hoá | tấn | 1e3 | A | |
| `kqt` | Khách quốc tế | m | 2014-06 → | 42d | Khách quốc tế | người | 1e3 | A | |
| | | | | | Tăng trưởng | % | 100 | R | `PCTFRAC` `LOWRES` |
| `ds` | Dân số | y | 2000 → 2025 | 224d | Tổng dân số | người | 1e3 | A | `LAGM` |
| | | | | | Tăng trưởng | % | 100 | R | `PCTFRAC` `LOWRES` `CONST` |
| `tn` | Thất nghiệp | q | 2015-03 → | 72d | Tỷ lệ thất nghiệp | % | 1 | A | `LAGM` |
| `ld` | Lực lượng lao động | q | 2012-03 → | 72d | Tổng lao động | người | 1e3 | A | `LAGM` |
| | | | | | Tăng trưởng | % | 100 | R | `PCTFRAC` `LOWRES` |
| `tcns` | Ngân sách nhà nước | q | 2009-03 → | 72d | Thu / Chi / Bội chi | VND | 1e9 | A | `LAGM` bội chi cắt qua 0 |
| `ncp` | Nợ chính phủ | y | 2013 → 2024 | 589d | Nợ chính phủ | VND | 1e9 | A | `LAGM` |
| | | | | | Tỷ lệ nợ/GDP | % | 100 | X | `LOWRES` `DEAD` (dừng 2023) |
| | | | | | Tăng trưởng | % | 100 | R | `PCTFRAC` `LOWRES` |
| `gdpbinhquan` | GDP bình quân đầu người | y | 2000 → **2023** | **1319d** | Thu nhập bình quân | VND/người | 1e6 | **X** | `DEAD` |

⚠️ **`iip` là ngoại lệ đã chấp nhận.** Endpoint chỉ có 1 series và nó là tăng trưởng dạng phân số làm tròn — không có giá trị tuyệt đối để khôi phục. Vẫn đưa vào Tier A vì không có lựa chọn khác, **chấp nhận sai số ±0,5 điểm %**. Nguồn thay thế khi cần chính xác: Tổng cục Thống kê công bố IIP hàng tháng, miễn phí.

### 5.2 Tiền tệ & lãi suất — 8 key

| key | Chỉ tiêu | Tần suất | Lịch sử | Trễ | Series | Đơn vị gốc | scale | Tier | Cờ |
|---|---|---|---|---|---|---|---|---|---|
| `ctt` | Cung tiền M2 | m | 2004-01 → | 72d | Cung tiền tệ | VND | 1e9 | A | `LAGM` |
| | | | | | Tăng trưởng | % | 100 | R | `PCTFRAC` `LOWRES` |
| `hd` | Tổng tiền gửi | m | 2012-04 → | 72d | Tổng tiền gửi | VND | 1e9 | A | `LAGM` |
| | | | | | Tăng trưởng | % | 100 | R | `PCTFRAC` `LOWRES` |
| `td` | **Tổng tín dụng** | m | 2004-01 → | 72d | (nhãn ghi "Tổng tiền gửi") | VND | 1e9 | A | `NAMEWRONG` `LAGM` |
| | | | | | Tăng trưởng | % | 100 | R | `PCTFRAC` `LOWRES` |
| `dtnh` | Dự trữ ngoại hối | m | 2000-04 → | 103d | Dự trữ ngoại hối | USD | 1e6 | A | `LAGM` |
| `dhtg` | Tỷ giá | d | T-2y → | 0d | Trung tâm / Trần / Sàn / NHTM bán / Tự do bán | VND/USD | 1 | A | `WIN2Y` — series "Sàn" ghi đơn vị "Đông" (lỗi chính tả) |
| `lsdh` | Lãi suất điều hành | d | T-2y → | 0d | Chiết khấu 3,0% / Tái cấp vốn 4,5% / Qua đêm 5,0% | % | 1 | A | `WIN2Y` `CONST` — **đứng yên là ĐÚNG**, NHNN không đổi từ 19/06/2023 |
| `lslnh` | LS liên ngân hàng | d | T-2y → | 1d | Qua đêm / 1 tuần / 2 tuần | % | 1 | A | `WIN2Y` |
| `lshd` | LS huy động | d | T-2y → | 0d | 1-3T / 6-9T / 13T | % | 1 | A | `WIN2Y` `SRCNOTE` |

> 🔴 **`td` — bug nhãn.** `series[0].name` ghi "Tổng tiền gửi", trùng nhãn với `hd`. Giá trị số **đúng và khác nhau thật** (`td` 20,15 triệu tỷ vs `hd` 17,44 triệu tỷ). **Map theo key endpoint, tuyệt đối không map theo `series.name`** — nếu không sẽ tính nhầm tăng trưởng tín dụng thành tăng trưởng huy động.

> 🔴 **`lshd` — `SRCNOTE` bắt buộc.** Đây là **bình quân lãi suất niêm yết TẠI QUẦY** của MBB/ACB/TCB/VPB, không phải lãi suất online. Đối chiếu 8/2026: API 5,91% vs trung bình quầy 4 NH 5,94% (lệch 0,03 điểm %), trong khi trung bình mức online cao nhất là 6,78%. Bảng "lãi suất ngân hàng hôm nay" trên báo luôn đăng mức online — nếu hiển thị không ghi rõ kênh, người dùng sẽ kết luận số của bạn sai.

### 5.3 Hàng hoá — 61 key

Tất cả tần suất **ngày**, cửa sổ trượt 2 năm (`WIN2Y`), gọi qua `?key=hang_hoa&name=`.

#### ⚠️ Cách đọc cờ «lệch x%» ở các bảng dưới

Cờ này nói **khoảng cách với một benchmark** — nên nó chỉ có nghĩa khi biết **so với chuẩn nào** và **so trên bao nhiêu điểm**.

| | Trạng thái |
|---|---|
| Phần lớn cờ | Sinh trong audit 2026-08-12 bằng cách **chấm một điểm**, không phải so chuỗi |
| Đã rà lại bằng cách so chuỗi | **Đúng 2 key:** `dau_wti` và `vang_the_gioi` *(đo 2026-08-15)* |
| 59 key còn lại | **Chưa rà** — không rõ sinh theo cách nào và so với chuẩn nào. Ghi **"chưa kiểm"**, đừng suy diễn |

🔴 **Hai lỗi làm hỏng một cờ lệch:** (1) **chấm một điểm** — không đo được độ lệch của cả chuỗi; (2) **so nhầm chuẩn** — giao ngay đem so với tương lai. Cờ cũ của `dau_wti` mắc cả hai.

⚠️ **Nhưng đừng suy đoán đồng loạt là cả bộ cờ sai.** Rà lại hai key thì **một sai (`dau_wti`), một đúng (`vang_the_gioi`, kiểm trên 712 ngày)**. Hai mẫu không đủ cơ sở kết luận cho 59 key kia — theo cả hai chiều.

#### Nông thuỷ sản & sợi dệt (13)

| key | Chỉ tiêu | Điểm | Trễ | Đơn vị gốc | scale | Tier | Cờ |
|---|---|---|---|---|---|---|---|
| `heo_hoi` | Giá heo hơi bình quân | 511 | 0d | VND/kg | 1 | A | |
| `ca_phe` | Giá cà phê nhân | 567 | 1d | VND/kg | 1 | A | |
| `tieu` | Giá hồ tiêu | 515 | 0d | VND/kg | 1 | A | |
| `duong` | Giá đường thế giới | 510 | 0d | USD/tấn | 1 | A | |
| `dau_co_malaysia` | Dầu cọ Malaysia | 454 | 0d | MYR/tấn | 1 | A | |
| `soi_coton` | Sợi cotton Trung Quốc | 487 | 1d | CNY/tấn | 1 | A | |
| `lua` | Giá lúa | 655 | 6d | VND/kg | **1** | A | `U1000` |
| `gao_nguyen_lieu` | Gạo nguyên liệu | 655 | 6d | VND/kg | **1** | A | `U1000` |
| `phu_pham_lua_gao` | Phụ phẩm lúa gạo | 655 | 6d | VND/kg | **1** | A | `U1000` |
| `tom_the` | Giá tôm thẻ | 643 | 7d | VND/kg | **1** | A | `U1000` |
| `vai_cotton_my` | Vải cotton Mỹ | 685 | 0d | **?** | 1 | A | `UNITCHK` — nhãn `USD/tấn` nhưng 84,55 khớp **US cents/lb** |
| `gao_tpxk` | Gạo thành phẩm XK | 655 | 6d | VND/kg | 1 | **X** | `U1000` `FROZEN` (69 ngày không đổi) |
| `ca_tra` | Giá cá tra | 545 | 5d | VND/kg | 1 | **X** | `FROZEN` (60 ngày không đổi) |

#### Kim loại (10)

| key | Chỉ tiêu | Điểm | Trễ | Đơn vị gốc | scale | Tier | Cờ |
|---|---|---|---|---|---|---|---|
| `quang_sat` | Quặng sắt TQ | 731 | 0d | CNY/tấn | 1 | A | khớp SunSirs 0,00% |
| `vang` | Vàng miếng trong nước (mua/bán) | 522 | 0d | VND/lượng | **1e3** | A | `UK1000` — nhãn `VNĐ/lượng` **sai**, dữ liệu ở nghìn đồng. Sau khi ×1000 khớp SJC 0,00% |
| `vang_the_gioi` | Vàng thế giới | 712 | 0d | USD/ounce | 1 | A | khớp Investing XAU/USD **0,00%** *(đo 2026-08-15)*; lệch PAXG 0,369% trên 712 ngày — xem ghi chú dưới bảng |
| `chi` | Chì TQ | 481 | 1d | CNY/tấn | 1 | **B** | |
| `kem` | Kẽm TQ | 731 | 0d | CNY/tấn | 1 | **B** | khớp 0,00% |
| `nhom` | Nhôm TQ | 731 | 0d | CNY/tấn | 1 | **B** | khớp 0,00% |
| `niken` | Niken TQ | 731 | 0d | CNY/tấn | 1 | **B** | khớp 0,00% |
| `dong` | Đồng COMEX | 712 | 0d | USD/pound | 1 | **B** | lệch 0,3% |
| `bac` | Bạc | 711 | 0d | USD/ounce | 1 | **B** | lệch <1% |
| `thiec` | Thiếc TQ | 136 | **523d** | CNY/tấn | 1 | **X** | `DEAD` từ 07/03/2025 — giá thực đã **+63,7%** kể từ đó |

> 🔵 **`vang_the_gioi` khớp chuẩn tuyệt đối** *(đo 2026-08-15)*. Đối chiếu **10 phiên** với Investing XAU/USD (*"Giá Vàng Giao Ngay Đô la Mỹ"*): trùng **tới từng chữ số thập phân, 10/10 ngày, 0,00%**. Không phải "gần giống" mà là bằng nhau — nhiều khả năng WiChart dùng **cùng một nguồn giá** với XAU/USD của Investing. *(Suy luận từ 10 ngày; **chưa xác nhận** nguồn gốc thật.)*
>
> Một phép đo độc lập trên **712 ngày** so với PAXG (Binance) cho lệch **0,369%** — xác nhận cờ cũ *"lệch 0,3%"* của key này là **đúng**. Đây là key duy nhất có cờ lệch đã được kiểm bằng chuỗi dài.
>
> ⚠️ **WiChart giữ nguyên giá cuối tuần.** **36,8%** số điểm cuối tuần trùng khít điểm liền trước *(đo 2026-08-15)* — thứ Bảy/Chủ nhật chuỗi đứng yên chứ không có giá mới. **Đừng tính biến động cuối tuần từ chuỗi này**; cần vàng chạy 24/7 thì phải lấy nguồn khác.
>
> ⚠️ Không nhầm với `vang` (vàng miếng SJC trong nước, đơn vị sai 1000× — xem dòng trên).

#### Năng lượng (6)

| key | Chỉ tiêu | Điểm | Trễ | Đơn vị gốc | scale | Tier | Cờ |
|---|---|---|---|---|---|---|---|
| `dau_wti` | Dầu WTI — **giá TƯƠNG LAI** | 637 | 0d | USD/thùng | 1 | A | `SRCNOTE` — lệch **0,50%** so với WTI tương lai, **2,85%** so với FRED giao ngay *(đo 2026-08-15)*; xem ghi chú dưới bảng |
| `khi_thien_nhien` | Khí thiên nhiên | 638 | 0d | USD/MMBtu | 1 | A | lệch 0,7% |
| `than_newcastle` | Than Newcastle | 653 | 1d | USD/tấn | 1 | A | khớp 0,00% |
| `than_coc` | Than cốc TQ | 562 | 0d | CNY/tấn | 1 | A | lệch 0,27%; sẹo lịch sử: gap 85 ngày ~07/2025 |
| `xang_dau` | Xăng dầu bán lẻ VN | 517 | 0d | VND/lít | **1e3** | A | `SUBDEAD` — **bỏ series [0] RON 95**, đóng băng từ 28/05/2026. E5/Diezen/Dầu hoả khớp 0,00% |
| `khi_lpg_trung_quoc` | LPG TQ | 482 | 0d | CNY/tấn | 1 | A | `LVLOFF` — lệch 15–20% so với SunSirs, chỉ dùng xu hướng |

> 🔴 **`dau_wti` là giá TƯƠNG LAI, không phải giao ngay**
>
> Nhãn của WiChart ghi *"Giá dầu WTI · USD/thùng"*, nên ai đọc cũng mặc định đây là **giá giao ngay**. Đo đối chiếu 2026-08-15 cho thấy **không phải**:
>
> | So với | Bản chất chuẩn | Mẫu | \|Lệch\| TB |
> |---|---|---:|---:|
> | Investing *"Hợp Đồng Tương Lai Dầu Thô WTI 9/26"* | **tương lai tháng gần** | 10 ngày | **0,50%** ✅ bám sát |
> | FRED `DCOILWTICO` | **giao ngay Cushing (EIA)** | 125 ngày | 2,85% |
>
> **2,85% KHÔNG phải sai số — là chênh lệch cơ sở.** Chênh giữa FRED và giá tương lai cực kỳ ổn định quanh **+2%** (`+1,89 · +1,98 · +2,03 · +2,06 · +2,07 · +2,06 · +2,02` — đo 2026-08-15). Sai số ngẫu nhiên không ổn định như thế. Thị trường đang **backwardation**: giao ngay cao hơn tương lai. Hai nguồn **đo hai thứ khác nhau**, cả hai đều đúng.
>
> ⚠️ **Ai đọc `dau_wti` như giá giao ngay sẽ lệch ~2% một cách hệ thống.** WiChart **không có** giá giao ngay Cushing — cần giao ngay thì phải lấy nguồn khác; cần giá tương lai thì WiChart đã cho sẵn ở 0,50%.
>
> ✅ **Không cần thay `dau_wti`.** Với phân tích vĩ mô kiểu top-down (dầu → lạm phát → chính sách), giá tương lai tháng gần chính là con số thị trường và báo chí trích hằng ngày. *(Nhận định, không phải phép đo.)*
>
> **Vì sao cờ cũ của key này sai** — bài học phương pháp, không phải chuyện riêng của dầu:
>
> 1. **Chấm một điểm** thay vì so cả chuỗi.
> 2. **So nhầm chuẩn** — lấy giao ngay làm mốc cho một chuỗi giá tương lai.
> 3. Vòng đo lại đầu tiên còn **parse epoch bằng UTC** (§2.4) nên ra 3,35%, sai theo chiều ngược lại. Ba lỗi chồng nhau mới lộ ra được sự thật.
>
> **Backwardation đã xác nhận trực tiếp** *(đo 2026-08-15)* — cấu trúc kỳ hạn WTI giảm đơn điệu theo kỳ hạn: Sep 82,40 · Oct 81,47 · Nov 80,10 · Dec 78,49, dốc ≈ **−1,6%/tháng**. Đây là bằng chứng độc lập cho lời giải thích ở trên, không phải suy đoán.
>
> **Chưa kiểm:** mới đối chiếu Investing **10 ngày** (giới hạn bảng mặc định của trang) · chưa dùng TradingView · chưa xác nhận `dau_wti` bám kỳ hạn nào (tháng gần hay xa) — mới biết nó thuộc phe tương lai.

#### Hoá chất & phân bón (5)

| key | Chỉ tiêu | Điểm | Trễ | Đơn vị gốc | scale | Tier | Cờ |
|---|---|---|---|---|---|---|---|
| `ure_trung_dong` | Ure Trung Đông | 505 | 0d | USD/tấn | 1 | A | lệch 1,3% |
| `phan_ure` | Ure Phú Mỹ + Cà Mau | 595/591 | 8d | VND/kg | 1 | A | giá niêm yết, đổi thưa |
| `phan_urea_trung_quoc` | Urea TQ | 480 | 0d | CNY/tấn | 1 | A | |
| `luu_huynh` | Lưu huỳnh TQ | 731 | 0d | CNY/tấn | 1 | A | |
| `phot_pho` | Phốt pho vàng TQ | 731 | 2d | CNY/tấn | 1 | A | |

#### Nhựa & cao su (5)

| key | Chỉ tiêu | Điểm | Trễ | Đơn vị gốc | scale | Tier | Cờ |
|---|---|---|---|---|---|---|---|
| `nhua_pvc_trung_quoc` | Nhựa PVC TQ | 591 | 0d | CNY/tấn | 1 | A | lệch 0,5% |
| `nhua_pp_trung_quoc` | Nhựa PP TQ | 591 | 0d | CNY/tấn | 1 | A | |
| `pet_trung_quoc` | PET TQ | 731 | 0d | CNY/tấn | 1 | A | |
| `cao_su_nhat_ban` | Cao su TOCOM | 498 | 2d | **Yên/kg** | 1 | A | Đơn vị API **ĐÚNG** (bảng web ghi "Yên/tấn" mới sai). Khớp TOCOM <1% |
| `cao_su` | Cao su trong nước | 131 | **548d** | VND/TSC | 1 | **X** | `DEAD` từ 10/02/2025 |

#### Thép & tôn (5)

| key | Chỉ tiêu | Điểm | Trễ | Đơn vị gốc | scale | Tier | Cờ |
|---|---|---|---|---|---|---|---|
| `hrc_trung_quoc` | HRC TQ | 592 | 0d | CNY/tấn | 1 | A | |
| `thep_phe_anh` | Thép phế | 492 | 2d | USD/tấn | 1 | A | `SRCNOTE` — thực là **HMS 1&2 CFR Thổ Nhĩ Kỳ**, khớp 0,00% |
| `thep_thanh_anh` | Thép thanh | 492 | 2d | USD/tấn | 1 | A | `SRCNOTE` — benchmark **Thổ Nhĩ Kỳ**, không phải Anh |
| `ton_lanh_hoa_sen_045mm` | Tôn lạnh Hoa Sen | 522 | 0d | VND/m² | **1e3** | A | giá niêm yết |
| `ton_lanh_mau_hoa_sen_045mm` | Tôn lạnh màu Hoa Sen | 522 | 0d | VND/m² | **1** | A | `U1000` — ngược với dòng trên |

#### Giấy & vải TQ (2)

| key | Chỉ tiêu | Điểm | Trễ | Đơn vị gốc | scale | Tier |
|---|---|---|---|---|---|---|
| `giay_gon_song_trung_quoc` | Giấy gợn sóng TQ | 731 | 0d | CNY/tấn | 1 | A |
| `vai_coton` | Vải cotton TQ | 487 | 1d | CNY/tấn | 1 | A |

#### Vật liệu xây dựng nội địa (15) — **Tier X, không thu thập**

Thực tế là chuỗi **tháng** (khai sai `"d"`), chỉ 18–22 điểm trong 2 năm, trễ 72–192 ngày, hệ số đơn vị không đồng nhất. Không đủ cho backtest hay tương quan.

| key | Trễ | Giá trị đổi lần cuối | scale | Lý do loại |
|---|---|---|---|---|
| `xi_mang` | 554d | 650d | 1 | `DEAD` từ 04/02/2025 |
| `da_0_4` | 72d | 103d | 1e3 | dữ liệu tháng, quá thưa |
| `da_1x2` | 72d | 133d | **1** | `U1000`, quá thưa |
| `da_mi_sang` | 72d | 133d | 1e3 | quá thưa |
| `da_hoc` | 72d | 72d | 1e3 | quá thưa |
| `be_tong_nhua_min` | 72d | 72d | **1** | `U1000`, quá thưa |
| `be_tong_mac_300` | 72d | **407d** | **1** | `FROZEN` — có điểm mới nhưng giá không đổi 13 tháng |
| `gach_dat_set_nung` | **192d** | 223d | **1** | `DEAD` từ 01/02/2026 |
| `coc_be_tong_du_ung_luc` | 72d | **chưa từng** | **1** | `CONST` — giá định mức tĩnh, không phải giá thị trường |
| `ong_nhua_27x18mm` | 103d | **chưa từng** | **1** | `CONST` |
| `ong_nhua_60x2mm` | 103d | **chưa từng** | **1** | `CONST` |
| `ong_nhua_90x29mm` | 103d | **chưa từng** | **1** | `CONST` |
| `son_lot_khang_kiem_cao_cap` | 192d | **chưa từng** | 1e3 | `CONST` `DEAD` |
| `son_noi_that_tieu_chuan` | 192d | **chưa từng** | **1** | `CONST` `DEAD` `U1000` |
| `son_ngoai_that_tieu_chuan` | 192d | **chưa từng** | **1** | `CONST` `DEAD` `U1000` |

**Endpoint hỏng:** `xi_mang_pcb` trả `HTTP 500` — loại khỏi mọi tích hợp.

---

## 6. Quy tắc ETL

### 6.1 Bảy quy tắc bắt buộc

1. **Parse epoch bằng `Asia/Ho_Chi_Minh`.** Mọi timestamp là 17:00 UTC.
2. **Dùng bảng `scale` đã hardcode ở §5.** Không suy hệ số tự động lúc chạy — `titleIndex` không ánh xạ 1:1 và lỗi 1000× rải rác ngẫu nhiên.
3. **Lưu giá trị ở đơn vị gốc (đơn vị 1).** VND, USD, CNY, MYR, JPY, %, điểm, người, tấn, kg, lít, m², m³.
4. **Không tin `timeArray`** — suy tần suất từ trung vị khoảng cách điểm.
5. **Map theo key endpoint, không theo `series.name`** (bug `td`/`hd`).
6. **Giám sát `stale_days` và `days_since_change` theo TỪNG SERIES**, không theo endpoint (ca mẫu `xang_dau`).
7. **Dùng `If-None-Match` + gzip** cho ETL hàng ngày.

### 6.2 Chính sách với series tăng trưởng

Series tăng trưởng đi vào bảng **`_raw_reference` tách biệt hoàn toàn**. Không bao giờ đi vào API đọc, không bao giờ vào chatbot. Chỉ job giám sát đêm đụng tới.

Lý do giữ, dù độ phân giải chỉ 1 điểm %:

| Công dụng | Chi tiết |
|---|---|
| **Tính hệ số nối đứt gãy** | Đoạn cũ/mới không chồng lấn, không có tăng trưởng thì không nối được. Xem Bẫy 6 |
| **Phát hiện đứt gãy** | Tín hiệu đặc hiệu nhất: COVID thì cả hai nguồn cùng báo −94%, đổi năm gốc thì tự tính ra +74% mà nguồn báo 8% |
| **Xác thực quy ước** | Đo được: sai số TB 0,25 điểm % ⇒ WiChart dùng **YoY từng kỳ**, không phải luỹ kế |

Mọi tăng trưởng hiển thị cho người dùng **tự tính từ series tuyệt đối**.

### 6.3 Cạm bẫy khi tự tính tăng trưởng

| Vấn đề | Xử lý |
|---|---|
| YoY của bạn ≠ số báo chí | GSO công bố nhiều chỉ tiêu theo **luỹ kế từ đầu năm so cùng kỳ**. WiChart dùng **YoY từng kỳ**. Tính cả hai, ghi nhãn rõ |
| Tết phá MoM | Tháng 1–2 lệch nặng, Tết còn di chuyển giữa hai tháng. Mặc định dùng YoY, cảnh báo riêng Q1 |
| Ghép theo vị trí dòng | Sai khi chuỗi thủng. Luôn join bằng **ngày thật** + quy ước neo §2.4 |
| Đứt gãy | Xem §6.4 |
| Không có deflator | Chỉ `gdp` có cả giá hiện hành và giá so sánh. Bán lẻ, vốn đầu tư, ngân sách chỉ có **danh nghĩa** — đừng để chatbot nói "tăng trưởng thực" |
| Hệ số đơn vị | Tỷ lệ triệt tiêu nên không ảnh hưởng tăng trưởng, nhưng ảnh hưởng hiển thị mức và phép chia liên endpoint (`ncp` ÷ `gdp`) |

### 6.4 Bảng đăng ký đứt gãy

```sql
CREATE TABLE series_break (
  key            text NOT NULL,
  series_idx     smallint NOT NULL,
  break_date     date NOT NULL,       -- điểm ĐẦU TIÊN thuộc nền mới
  factor         numeric NOT NULL,    -- nhân đoạn CŨ với hệ số này
  reason         text,
  verified_by    text,
  verified_at    timestamptz,
  PRIMARY KEY (key, series_idx, break_date)
);

INSERT INTO series_break VALUES
 ('gdp', 1, '2026-03-01', 1.6005, 'Đổi năm gốc giá so sánh. Hệ số = TB 2 ước lượng độc lập 1.6032 / 1.5978', ...);
```

Lưu **hai cột giá trị**:

- `value_raw` — nguyên gốc theo nền của kỳ đó. Dùng khi trả lời "GDP quý 3/2020 là bao nhiêu tỷ đồng"
- `value_spliced` — đã nối. Dùng cho tăng trưởng, tương quan, biểu đồ

> ⚠️ Mức sau khi nối **không khớp bất kỳ tài liệu chính thức nào của GSO**. Chatbot mặc định trả `value_raw`.
>
> ⚠️ Rebasing không phải nhân đều — GSO đổi cả quyền số ngành. Hệ số đơn là xấp xỉ (hai ước lượng lệch 0,34% cho thấy đủ tốt với GDP tổng, đừng kỳ vọng chính xác tuyệt đối).

---

## 7. Bộ giám sát hợp đồng

Bổ sung vào bộ giám sát đã mô tả ở [market-data-store.md §7.1](../../20-design/market-data-store.md):

| Kiểm tra | Bắt được |
|---|---|
| `days_since_change` theo từng series | `be_tong_mac_300` có điểm mới mỗi tháng nhưng giá đứng 407 ngày — mọi test dựa trên timestamp đều bỏ lọt |
| Hệ số `scale` đã hiệu chuẩn có đổi không | Lỗi 1000× rải rác ngẫu nhiên, không có quy tắc tự động |
| `gap_median` so với `timeArray` khai báo | 16 key khai sai tần suất |
| `stale_days` **per-series** trong endpoint nhiều series | `xang_dau` — endpoint sống, RON 95 chết 76 ngày |
| Ngưỡng trễ theo **bội số chu kỳ thật**, không theo ngày tuyệt đối | Tránh báo động giả hàng loạt cho chuỗi quý/năm |
| Tăng trưởng tự tính vs `_raw_reference` — lệch > 0,5 điểm % | Đứt gãy chưa khai báo, hệ số đơn vị đổi, hoặc quy ước YoY lệch |
| Tự tính vs `titleIndex` kỳ mới nhất | Kiểm tra rẻ nhất, bắt được nhiều lỗi nhất |
| Chuỗi cắt qua 0: dùng chênh lệch tuyệt đối chuẩn hoá | `cctm` cán cân, 4 series `cctt`, `tcns` bội chi — phần trăm vô nghĩa |

---

## 8. Bản đồ liên quan mã niêm yết

Dùng cho tầng ngữ nghĩa của chatbot: khi người dùng hỏi về một mã, đây là các chuỗi hàng hoá cần kéo vào ngữ cảnh.

| Chuỗi hàng hoá | Mã chịu ảnh hưởng |
|---|---|
| `hrc_trung_quoc` `quang_sat` `than_coc` `thep_phe_anh` `thep_thanh_anh` | HPG · HSG · NKG · GDA · VGS |
| `ton_lanh_hoa_sen_045mm` `ton_lanh_mau_hoa_sen_045mm` | **HSG** (trực tiếp) |
| `dau_wti` `khi_thien_nhien` `xang_dau` | GAS · PVS · PVD · PVT · BSR · PLX · OIL |
| `khi_lpg_trung_quoc` | PGS · CNG · ASP |
| `than_newcastle` | PPC · QTP · NT2 · TVD · NBC |
| `phot_pho` | **DGC** (sản phẩm chính) |
| `phan_ure` `ure_trung_dong` `phan_urea_trung_quoc` `luu_huynh` | DPM · DCM · LAS |
| `nhua_pvc_trung_quoc` `nhua_pp_trung_quoc` `pet_trung_quoc` | AAA · NTP · BMP |
| `cao_su_nhat_ban` | GVR · PHR · DPR · DRC · CSM |
| `heo_hoi` | DBC · BAF · MML · HAG |
| `tom_the` | MPC · FMC · CMX |
| `lua` `gao_nguyen_lieu` `phu_pham_lua_gao` | LTG · TAR · AGM · PAN |
| `duong` | SLS · LSS · QNS · SBT |
| `dau_co_malaysia` | KDC · TAC · VOC |
| `vai_cotton_my` `soi_coton` `vai_coton` | STK · TCM · MSH · TNG · VGT |
| `giay_gon_song_trung_quoc` | DHC · HHP |
| `vang` `vang_the_gioi` | PNJ |
| `td` `hd` `ctt` `lshd` `lslnh` | Toàn ngành ngân hàng — **tăng trưởng tín dụng là biến số vĩ mô được theo dõi sát nhất** |

Nhóm Tier B (`chi` `kem` `nhom` `niken` `dong` `bac`): không có mã niêm yết VN nào chịu ảnh hưởng đáng kể. Dữ liệu sạch, giữ cho dashboard hàng hoá, không đưa vào ngữ cảnh chatbot.

---

## 9. Bảng hardcode

```python
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
"vai_cotton_my":   dict(g="hang_hoa", tier="A", s=[("Giá vải cotton","UNVERIFIED",1,D,["UNITCHK"])]),
"gao_tpxk":        dict(g="hang_hoa", tier="X", s=[("Giá gạo TPXK","VND/kg",1,None,["U1000","FROZEN"])]),
"ca_tra":          dict(g="hang_hoa", tier="X", s=[("Giá cá tra","VND/kg",1,None,["FROZEN"])]),
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
  "gdpbinhquan","gao_tpxk","ca_tra","thiec","cao_su","xi_mang","xi_mang_pcb",
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
  ("dau_wti", 0):        "Giá TƯƠNG LAI WTI tháng gần, KHÔNG phải giao ngay Cushing dù nhãn ghi "
                         "'Giá dầu WTI'. Lệch 0,50% so với Investing WTI tương lai (10 ngày); "
                         "2,85% so với FRED DCOILWTICO giao ngay (125 ngày) — chênh đó là "
                         "backwardation, không phải sai số. Đo 2026-08-15",
}
```

---

## 10. Việc cần làm với WiGroup

> ✅ **Giấy phép WiFeed đã chốt — chủ dự án xác nhận 2026-08-15.** Danh sách dưới đây vì vậy không còn là điều kiện đàm phán mà là việc cần làm tiếp với WiGroup.

Audit cho thấy **WiGroup gần như không sai về số học** — mọi thứ đối chiếu được đều khớp nguồn gốc (nhiều series khớp 0,00%). Cái họ làm ẩu là **metadata**. Vì vậy thứ cần nhất ở WiFeed không phải "dữ liệu có đúng không" mà là **một từ điển định nghĩa**, nên đưa vào hợp đồng như phụ lục.

Yêu cầu cụ thể:

1. **Từ điển 87 chỉ tiêu**: nguồn gốc thật, kênh lấy giá, chuẩn sản phẩm, đơn vị thật của trường `data`, tần suất thật, độ trễ cam kết.
2. **Làm rõ đơn vị `vai_cotton_my`** — `USD/tấn` hay `US cents/lb`.
3. **Làm rõ `khi_lpg_trung_quoc`** — chuẩn sản phẩm nào, vì sao lệch 15–20% so với LPG SunSirs.
4. **Xác nhận phương pháp `lshd`** — quầy hay online, rổ mẫu, cách bình quân.
5. **Lịch sử đầy đủ cho chuỗi ngày** — gói trả phí phải bỏ giới hạn cửa sổ 2 năm.
6. **Độ chính xác đầy đủ cho series tăng trưởng** — hoặc cam kết luôn cung cấp series tuyệt đối kèm theo.
7. **Thông báo trước khi đổi năm gốc / rebasing** — kèm hệ số nối chính thức.
8. **Ngưỡng rate limit** — chưa đo, cần con số cam kết.
9. **Sửa hoặc xác nhận các lỗi metadata** đã liệt kê: nhãn `td`, đơn vị `vdtnsnn`, `timeArray` của 16 key, `xi_mang_pcb` trả 500.
10. **Xác nhận chuẩn của `dau_wti`** — hợp đồng tương lai tháng nào, sàn nào, lấy giá lúc nào. Đo 2026-08-15 cho thấy đây là **giá tương lai** chứ không phải giao ngay, trong khi nhãn chỉ ghi "Giá dầu WTI"; cần họ ghi rõ trong từ điển chỉ tiêu.

---

## Phụ lục — Nhật ký audit

| Vòng | Nội dung | Kết quả |
|---|---|---|
| 1 | 6 agent song song, 87 key, harness đo toàn vẹn + websearch đối chiếu | 49 dùng được / 25 có điều kiện / 13 loại |
| — | **Phát hiện lỗi harness**: parse UTC thay vì ICT; ngưỡng trễ tuyệt đối áp cho mọi tần suất | Nhiều key bị đánh giá oan |
| 2 | Thẩm định lại 25 key có điều kiện với parse ICT, ngưỡng theo bội số chu kỳ, thêm `days_since_change` | 52 / 20 / 15 |
| 3 | Hiệu chuẩn đơn vị toàn bộ 126 series, ghép `titleIndex` theo giá trị | Phát hiện lỗi 1000× rải rác + 15 series `LOWRES` |
| 4 | Đo sai số series tăng trưởng, thử nối chuỗi GDP, quét đứt gãy toàn bộ | Hệ số nối 1.6005; 1 đứt gãy thật / 18 báo động giả |
| 5 | **Tự kiểm chứng file này**: script đọc chính khối Python trong file rồi đối chiếu từng trường với API sống — 507 khẳng định | 3 lỗi phát hiện & đã sửa: `vang` sai thang 1000×, đếm `LOWRES` 13→15, `vt` đơn vị "người"→"lượt người" |

Số liệu gốc: `calibration.json`, `reaudit.json`, `final_facts.json` trong thư mục scratchpad của phiên audit.
