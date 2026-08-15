# Vàng và dầu — đối chiếu với chuẩn Investing.com · đo 2026-08-15

Chủ dự án yêu cầu: *"vàng dầu bạn check lại với giá vninvesting hoặc tradingview làm chuẩn ấy."*

**Đây là báo cáo thay thế cho `report-wichart-oil-deviation.md`, vốn sai vì lỗi parse múi giờ.**

## 0. Kết luận — đảo ngược hoàn toàn kết luận trước

| Khẳng định cũ (sai) | Sự thật đo được |
|---|---|
| *"WiChart lệch giá dầu 3,35%, nên bỏ"* | **WiChart bám giá tương lai WTI ở 0,50%. Giữ nguyên, không cần thay.** |
| *"Tài liệu ghi lệch 1,3% là sai gấp 3 lần"* | Chưa kết luận được — phụ thuộc tài liệu so với chuẩn nào |
| *"FRED chuẩn, WiChart nhiễu"* | **Cả hai đều đúng — đo hai thứ khác nhau.** FRED = giao ngay Cushing; WiChart = giá tương lai |

## 1. Cách lấy chuẩn

`vn.investing.com` chặn client HTTP thường (`403` Cloudflare); `scanner.tradingview.com` trả `404`. **Lấy được bằng trình duyệt thật.**

| Chuẩn | Trang | Bản chất |
|---|---|---|
| **Dầu** | `vn.investing.com/commodities/crude-oil-historical-data` | *"Hợp Đồng Tương Lai Dầu Thô WTI - 9/26 (OIL)"* — **hợp đồng tương lai tháng gần**, không phải giao ngay |
| **Vàng** | `vn.investing.com/currencies/xau-usd-historical-data` | *"XAU/USD - Giá Vàng Giao Ngay Đô la Mỹ"* — **giao ngay** |

## 2. 🔴 Lỗi múi giờ đã làm hỏng phép đo trước

Mốc thời gian WiChart là epoch mili giây của **nửa đêm giờ Việt Nam**:

```
epoch=1786726800000 → UTC 2026-08-14 17:00 → giờ VN 2026-08-15 00:00
```

Parse theo **UTC** → cả chuỗi **lệch lùi một ngày** → so nhầm phiên với FRED.

| Cách parse | n | TB có dấu | \|lệch\| TB | sd | max |
|---|---:|---:|---:|---:|---:|
| **UTC** *(sai — dùng ở báo cáo trước)* | 115 | −2,26% | **3,35%** | 3,97% | 16,40% |
| **Giờ VN (+7h)** *(đúng)* | 125 | −1,97% | **2,85%** | 3,34% | 21,50% |

**Dấu hiệu phát hiện:** khi đối chiếu **vàng** với Investing, giá WiChart của ngày `d` **trùng khít** giá Investing của ngày `d+1` — một chuỗi số trùng khít lệch pha là bằng chứng lệch nhãn ngày, không phải sai giá.

## 3. VÀNG — kết quả

Chuẩn: Investing XAU/USD giao ngay.

| Ngày | Investing | PAXG | % | LBMA | % | **WiChart** | **%** |
|---|---:|---:|---:|---:|---:|---:|---:|
| 14/08 | 4.376,60 | 4.380,40 | +0,09 | 4.390,70 | +0,32 | **4.376,60** | **0,00** |
| 13/08 | 4.351,34 | 4.356,83 | +0,13 | 4.373,00 | +0,50 | **4.351,34** | **0,00** |
| 12/08 | 4.408,70 | 4.409,58 | +0,02 | 4.426,65 | +0,41 | **4.408,70** | **0,00** |
| 11/08 | 4.368,46 | 4.369,65 | +0,03 | 4.383,35 | +0,34 | **4.368,46** | **0,00** |
| 10/08 | 4.388,96 | 4.397,13 | +0,19 | 4.324,45 | −1,47 | **4.388,96** | **0,00** |
| 07/08 | 4.343,74 | 4.344,47 | +0,02 | 4.335,55 | −0,19 | **4.343,74** | **0,00** |
| 06/08 | 4.240,42 | 4.248,73 | +0,20 | 4.267,85 | +0,65 | **4.240,42** | **0,00** |
| 05/08 | 4.247,02 | 4.272,06 | +0,59 | 4.206,60 | −0,95 | **4.247,02** | **0,00** |
| 04/08 | 4.077,65 | 4.068,67 | −0,22 | 4.084,20 | +0,16 | **4.077,65** | **0,00** |
| 03/08 | 4.053,45 | 4.052,20 | −0,03 | 4.028,15 | −0,62 | **4.053,45** | **0,00** |
| **\|Lệch\| TB** | | | **0,15%** | | **0,56%** | | **0,00%** |

🔵 **WiChart khớp Investing tới từng chữ số thập phân, 10/10 ngày.** Không phải "gần giống" — **bằng nhau tuyệt đối**. Suy ra WiChart `vang_the_gioi` dùng **cùng một nguồn giá** với XAU/USD của Investing. *(Suy luận từ 10 ngày; chưa kiểm nguồn gốc.)*

**PAXG 0,15%** — bám giao ngay rất sát, và có thêm ưu thế **chạy 24/7** (WiChart đứng yên 36,8% ngày cuối tuần — số của khảo sát Binance).
**LBMA 0,56%** — lệch lớn hơn vì là **fixing 15:00 London**, không phải giá đóng cửa. Đây là **đặc tính**, không phải sai số.

## 4. DẦU — kết quả

Chuẩn: Investing WTI **tương lai 9/26**.

| Ngày | Investing | FRED *(giao ngay)* | % | **WiChart** | **%** |
|---|---:|---:|---:|---:|---:|
| 14/08 | 82,40 | — | — | 81,96 | −0,53 |
| 13/08 | 81,25 | — | — | 81,94 | +0,85 |
| 12/08 | 83,27 | — | — | 83,05 | −0,26 |
| 11/08 | 83,20 | 84,77 | **+1,89** | 83,09 | −0,13 |
| 10/08 | 82,13 | 83,76 | **+1,98** | 81,12 | −1,23 |
| 07/08 | 78,18 | 79,77 | **+2,03** | 78,39 | +0,27 |
| 06/08 | 77,29 | 78,88 | **+2,06** | 77,71 | +0,54 |
| 05/08 | 75,22 | 76,78 | **+2,07** | 75,61 | +0,52 |
| 04/08 | 75,77 | 77,33 | **+2,06** | 76,22 | +0,59 |
| 03/08 | 80,34 | 81,96 | **+2,02** | 80,26 | −0,10 |
| **\|Lệch\| TB** | | | **2,02%** | | **0,50%** |

### 🔵 Hai kết luận

**1. Chênh FRED–tương lai là chênh lệch cơ sở, không phải sai số.**
`+1,89 · +1,98 · +2,03 · +2,06 · +2,07 · +2,06 · +2,02` — **cực kỳ ổn định quanh +2%**. `DCOILWTICO` là **giao ngay Cushing** (EIA); Investing là **tương lai tháng gần**. Thị trường đang **backwardation** nên giao ngay cao hơn tương lai. Sai số ngẫu nhiên không ổn định như thế.

Khớp với `report-more-sources.md` §2.2: Yahoo `CL=F` cũng thấp hơn FRED trung bình **−1,29%**, và chênh này **trôi dần** theo bốn cửa sổ 60 phiên (−1,03% → −2,70%) — đúng dáng của backwardation dốc dần.

**2. WiChart theo phe tương lai, và bám rất sát: 0,50%.**
Nghĩa là `dau_wti` của WiChart **không phải giá giao ngay** dù nhãn ghi "Giá dầu WTI". Ai đọc nó như giá giao ngay sẽ lệch ~2% một cách hệ thống.

## 5. Điều chỉnh các khuyến nghị đã đưa

| Khuyến nghị cũ | Trạng thái mới |
|---|---|
| *"Bỏ WiChart `dau_wti`, ghép FRED + Yahoo `CL=F`"* (`report-more-sources.md` §7.3) | ❌ **Không cần.** Cách ghép đó dựng lại giá **giao ngay** — nhưng nếu dự án muốn giá tương lai thì WiChart đã cho sẵn ở 0,50% |
| *"Vàng: thay bằng LBMA"* (`report-more-sources.md` §7.4) | ⚠️ **Sửa lại.** WiChart vàng đã khớp tuyệt đối với chuẩn. LBMA có giá trị riêng: **lịch sử từ 1968** để backfill, và là fixing chính thức — không phải để thay |
| *"PAXG lấy làm nguồn vàng"* (`report-binance.md`) | ✅ **Vẫn đúng, nhưng lý do đổi.** Không phải vì WiChart lệch — mà vì PAXG **chạy 24/7** còn WiChart đứng yên cuối tuần |
| *"Cờ `lệch x%` trong `wichart.md` đáng nghi hàng loạt"* | ⚠️ **Rút lại.** Cơ sở của nghi ngờ đó là con số 3,35% sai của tôi. Cờ `vang_the_gioi` ("0,3%") thì khảo sát Binance đã xác nhận **đúng** trên 712 ngày |

## 6. Câu hỏi thật còn lại

Không phải *"nguồn nào đúng"* mà là **"dự án muốn giá giao ngay hay giá tương lai?"**

- **Giao ngay** (FRED `DCOILWTICO`): phản ánh giá giao hàng thực tại Cushing. Chậm 2–4 ngày.
- **Tương lai tháng gần** (WiChart, Investing, Yahoo `CL=F`): thứ thị trường tài chính báo giá hằng ngày, tin tức hay trích. Tươi T−1.

Với phân tích vĩ mô kiểu top-down của skill (dầu → lạm phát → chính sách), **giá tương lai tháng gần là cái thị trường và báo chí dùng** — nên WiChart đang phục vụ đúng nhu cầu. *(Nhận định, không phải phép đo.)*

## 7. Chưa kiểm

- Mới đối chiếu **10 ngày** với Investing (giới hạn bảng mặc định của trang). Các số 712 ngày / 115 ngày ở báo cáo khác dùng chuẩn khác.
- **Chưa dùng TradingView** — `scanner.tradingview.com` trả 404, chưa tìm endpoint đúng.
- Chưa kiểm nguồn gốc thật của WiChart `vang_the_gioi` (mới suy luận từ trùng khít 10/10).
- Chưa đo lại các mặt hàng khác của WiChart bằng chuẩn Investing.
- Giả thuyết backwardation **chưa xác nhận trực tiếp** bằng cấu trúc kỳ hạn (cách kiểm: so hai kỳ hạn liền nhau của `CL=F`).
