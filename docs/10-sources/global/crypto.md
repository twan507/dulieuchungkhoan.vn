# Binance — Vàng token hoá 24/7 và crypto

**Ngày đo:** 2026-08-15 · **Trạng thái:** 46/60 lời gọi thật (43×`200`, 1×WebSocket, 1×`404`, 1×`202` chặn bot) · chỉ dữ liệu thị trường công khai, chỉ đọc

> Không đăng ký tài khoản, không tạo khoá, không chạm endpoint giao dịch. Mọi con số đến từ lời gọi thật ngày **2026-08-15**; cái gì chưa gọi thì ghi **"chưa kiểm"**.

---

## 1. Vai trò trong dự án — đọc trước khi dùng

Lấy Binance vì **đúng hai thứ**, không phải vì "API tốt":

| Vai | Lý do đo được |
|---|---|
| **PAXG — vàng thế giới chạy 24/7** | 🔴 **Lý do là ĐỘ PHỦ THỜI GIAN, không phải độ chính xác.** WiChart **đứng yên 36,8% ngày cuối tuần** (70/190 điểm cuối tuần trùng khít điểm liền trước — đo 2026-08-15). PAXG chạy thật cuối tuần |
| **10 đồng crypto lớn** | Hiển thị và vẽ biểu đồ. Không dùng làm tín hiệu phân tích |

⚠️ **Đừng ghi lý do lấy PAXG là "WiChart lệch".** WiChart **không lệch** — nó khớp chuẩn Investing XAU/USD **0,00%** trên 10/10 ngày *(đo 2026-08-15, xem [`../macro/wichart.md`](../macro/wichart.md))*, và PAXG lệch WiChart chỉ **0,369%** trên 712 ngày. Hai nguồn đồng ý với nhau; cái PAXG thêm vào là **những ngày WiChart không có số mới**.

**Loại có chủ đích** *(đo 2026-08-15, chi tiết ở §7)*: dầu/bạc/đồng qua nhóm TradFi perpetual · dựng DXY · BTC làm thước khẩu vị rủi ro. **Cả ba đã đo và loại — đừng mở lại mà không đọc §7 trước.**

---

## 2. Đặc tả API

### 2.1 Host và xác thực

| | |
|---|---|
| Host dữ liệu spot | `https://api.binance.com` |
| Host phái sinh | `https://fapi.binance.com` |
| WebSocket | `wss://stream.binance.com:9443` |
| Kho file lịch sử | `https://data.binance.vision` |
| Chặn theo vùng từ Việt Nam | **Không.** `api` · `fapi` · `data-api` · `data` · `stream` đều `200` *(đo 2026-08-15)* |
| Xác thực | **Không cần khoá** cho toàn bộ endpoint dữ liệu thị trường |

### 2.2 Hiệu năng và hạn mức *(đo 2026-08-15)*

| | |
|---|---|
| Độ trễ (36 mẫu) | min **71 ms** · trung vị **151 ms** · max **406 ms** |
| Header hạn mức **thật** | `x-mbx-used-weight`, `x-mbx-used-weight-1m` trên **mọi** response |
| Hạn mức tự công bố | `REQUEST_WEIGHT` **6.000/phút** · `RAW_REQUESTS` **300.000/5 phút** |
| Mã lỗi vượt nhịp | `429` vượt nhịp · `418` **cấm IP** nếu tiếp tục gọi sau `429` |
| Tổng weight cả phiên khảo sát | ≈ **100/6.000** mỗi phút |

🔵 **Đây là nguồn duy nhất trong bộ quốc tế có header hạn mức thật** — ETL đọc `x-mbx-used-weight-1m` để tự điều tiết thay vì đoán. FRED, Yahoo, Frankfurter, LBMA đều không có.

⚠️ **Ngưỡng chặn thật: chưa kiểm** — chủ đích không dò.

⚠️ **Lệch đồng hồ:** máy trạm **chậm hơn server 646 ms** *(đo 2026-08-15)*, **991 ms** *(đo 2026-09-05)*. Phải hiệu chỉnh trước khi tính độ trễ, nếu không mọi phép đo độ tươi đều sai theo một chiều.

### 2.3 `/api/v3/klines` — lược đồ

```
GET https://api.binance.com/api/v3/klines
      ?symbol=PAXGUSDT&interval=1d&limit=1000&timeZone=0
```

Trả về **mảng của mảng 12 phần tử, định danh theo VỊ TRÍ** (không có tên trường):

| Vị trí | Nội dung |
|---:|---|
| `0` | Thời điểm **mở** nến — epoch **mili giây** |
| `1`–`4` | OHLC — **dạng chuỗi** |
| `5` | Khối lượng base — **dạng chuỗi** |
| `6` | Thời điểm đóng nến |
| `7` | Giá trị quote |
| `8` | Số lệnh |
| `9`–`10` | Taker buy |
| `11` | Bỏ trống |

| Tham số | Ghi chú |
|---|---|
| `limit` | Mặc định **500**, tối đa **1000** |
| `timeZone` | Mặc định UTC — ⚠️ **phải đặt rõ**, đừng để mặc định rồi lệch nhãn ngày |

### 2.4 WebSocket và kho lịch sử *(đo 2026-08-15)*

| | |
|---|---|
| Nối WebSocket | **373 ms**, không khoá, ghép nhiều luồng trên một kết nối |
| Độ trễ event → nhận | **≈23 ms** sau khi hiệu chỉnh lệch đồng hồ |
| `data.binance.vision` | Có bản **ngày và tháng**, mỗi file kèm `.CHECKSUM` |
| File T−1 publish lúc | **02:12 UTC** |
| `PAXGUSDT` 1d sớm nhất trong kho file | **2020-08-28** — khớp đúng REST |
| Cấu trúc cột trong file zip | ⚠️ **Chưa kiểm** — chưa mở nội dung zip. Phải mở trước khi dựng backfill |

---

## 3. PAXG — nguồn vàng 24/7

### 3.1 Ba mã vàng token hoá *(đo 2026-08-15)*

| Mã | Lịch sử sớm nhất | Kết luận |
|---|---|---|
| **`PAXGUSDT`** | **2020-08-28** (~6 năm) | ✅ **Lấy.** Paxos Gold, 1 token ≈ 1 ounce vàng vật chất |
| `XAUTUSDT` | 2026-03-26 | ❌ Tether Gold — **quá ngắn để backfill** |
| `XAUUSDT` (perp) | 2025-12-11 | ❌ Nhóm TradFi perpetual, xem §7 |

Thanh khoản `PAXGUSDT`: trung vị **12,7 triệu USDT/ngày**, chênh mua–bán **0,0002%**.

### 3.2 Đối chiếu PAXG ↔ WiChart `vang_the_gioi` — 712 ngày *(đo 2026-08-15)*

Thử cả ba kiểu ghép để loại giả thuyết trễ pha:

| Kiểu ghép | n | Lệch TB có dấu | **\|Lệch\| TB** | sd | Biên độ | Ngày >2% |
|---|---:|---:|---:|---:|---|---:|
| PAXG(d) ↔ WiChart(d−1) | 711 | +0,284% | 0,941% | 1,323% | −8,74 … +6,78 | 10,7% |
| **PAXG(d) ↔ WiChart(d)** | **712** | **+0,197%** | **0,369%** | **0,467%** | **−1,49 … +2,75** | **0,6%** |
| PAXG(d) ↔ WiChart(d+1) | 712 | +0,124% | 0,855% | 1,268% | −5,26 … +12,62 | 8,8% |

**Ghép đúng ngày là ghép đúng** — hai kiểu lệch pha đều xấu đi ~2,4 lần. **Không có độ trễ hệ thống giữa hai nguồn.**

Chi tiết thêm: trung vị lệch tuyệt đối **0,281%** · ngày >1%: **4,8%** · **ngày >5%: 0/712**. Bốn ngày lệch >2% đều rơi vào ngày vàng biến động mạnh ⇒ lệch do **chênh giờ chốt**, không phải sai nguồn.

🔵 **Hệ quả cho `wichart.md`:** cờ *"lệch 0,3%"* mà `wichart.md` gắn cho `vang_the_gioi` — đo trên 712 ngày thì **ĐÚNG** (0,369%). Khác hẳn cờ `dau_wti`. **Bộ cờ của WiChart không sai đồng loạt — phải kiểm từng cái.**

### 3.3 Premium của PAXG — đo, không giả định

Chuẩn: **LBMA Gold PM** (chốt 15:00 London = 14:00 UTC mùa hè — xem [`commodities.md`](commodities.md)). So với **nến 1 giờ mở lúc 14:00 UTC** cùng ngày để triệt tiêu chênh giờ.

| Phép đo *(88 ngày, đo 2026-08-15)* | TB có dấu | \|Lệch\| TB | Biên độ |
|---|---:|---:|---|
| **PAXG tại 14:00 UTC vs LBMA PM** | **−0,049%** | **0,130%** | −0,365 … +0,361 |
| PAXG sau hiệu chỉnh neo USDT | −0,105% | 0,149% | −0,441 … +0,268 |
| XAUT tại 14:00 UTC vs LBMA PM | −0,174% | 0,221% | −0,621 … +0,300 |
| PAXG vs XAUT *(hai tổ chức phát hành độc lập)* | +0,125% | 0,144% | −0,223 … +0,431 |

**Không ngày nào lệch quá 0,5%.** "Premium" thực chất là **discount −0,05%**, nhỏ hơn cả chênh mua–bán của nhiều nguồn. Hai token của hai tổ chức độc lập chỉ khác nhau **0,14%** ⇒ bằng chứng mạnh rằng cả hai bám thật vào vàng vật chất.

🔴 **Bẫy đo lường:** lấy giá **close 23:59 UTC** rồi so LBMA PM cho ra **0,618%** — con số đó sẽ bị hiểu nhầm là premium, trong khi thực chất là **10 tiếng biến động thật**. Muốn đo premium thì phải so **đúng giờ chốt**.

### 3.4 ⚠️ Nhịp tin PAXG mỏng — đừng thiết kế như luồng dày

| | *(đo 2026-08-15)* |
|---|---|
| 20 giây quan sát WebSocket | chỉ nhận **2 bản tin** |
| Số lệnh 24h | 21.941 ≈ **0,25 lệnh/giây** |
| REST — giao dịch mới nhất cách | **4,2 giây** |
| REST — nến 1 phút trễ | **15,5 giây** |

Là **tick thưa**, không phải dòng chảy dày như BTC. Bộ giám sát "không có tin trong N giây ⇒ mất kết nối" đặt ngưỡng theo nhịp BTC sẽ **báo động giả liên tục** với PAXG.

---

## 4. Mười đồng crypto

**Chọn theo ĐỘ NHẬN BIẾT, không theo khối lượng** *(quyết định 2026-08-15)*. Lý do đo được: **top khối lượng đầy stablecoin và token lạ** (ví dụ `ACEUSDT`) — xếp theo khối lượng sẽ cho ra một danh sách mà người dùng Việt Nam không nhận ra đồng nào.

| Đồng | Lịch sử *(đo 2026-08-15)* |
|---|---:|
| BTC | **9 năm** |
| ETH | **9 năm** |
| BNB | 8,8 năm |
| ADA | 8,4 năm |
| XRP | 8,3 năm |
| TRX | 8,2 năm |
| LINK | 7,6 năm |
| DOGE | 7,1 năm |
| SOL | 6,0 năm |
| AVAX | 6,0 năm |

**Đủ cho hiển thị và vẽ biểu đồ.** Không dùng làm tín hiệu phân tích — xem §7.

---

## 5. Bốn bẫy bắt buộc nhớ

### 🔴 Bẫy 1 — Giá là USDT, không phải USD

Mọi cặp `*USDT` báo giá theo **USDT**, một stablecoin, **không phải đô la Mỹ**.

Chênh neo đã đo *(2026-08-15)*:

| Phép đo | Kết quả |
|---|---|
| `USDCUSDT`, 3.000 nến 1 giờ | lệch neo TB **−0,050%**, **max chỉ 0,145%** |
| `USDTUSD` (cặp USD thật), 271 ngày | trung vị **0,99970** |

→ Chênh neo **dưới 0,15%** — nhỏ hơn nhiễu của chính các nguồn đang dùng, **không phải lý do loại Binance**. Nhưng **lược đồ phải ghi rõ đơn vị là USDT**, và tài liệu hiển thị không được viết "USD" cho gọn.

### 🔴 Bẫy 2 — `/klines` là mảng theo vị trí, số dạng chuỗi

Không có tên trường. Đọc nhầm vị trí thì không có lỗi nào bật lên — chỉ có số sai. Và **toàn bộ giá là chuỗi**: ép `Decimal` ở tầng ETL, đừng để float lẻn vào.

### 🔴 Bẫy 3 — Nến định danh bằng thời điểm MỞ, epoch ms UTC

Phần tử `0` là **thời điểm mở nến**, không phải thời điểm đóng. Tham số `timeZone` mặc định UTC — **phải đặt rõ**. Không đặt rồi ghép với chuỗi giờ Việt Nam sẽ lệch nhãn ngày, đúng loại lỗi đã thật sự xảy ra với WiChart trong đợt đo 2026-08-15 *(xem [`../market/00-conventions.md`](../market/00-conventions.md))*.

⚠️ **Nến cuối là nến ĐANG CHẠY** *(đo 2026-09-05)*: `limit=40` trả cả nến hôm nay với `closeTime` (phần tử `6`) = 23:59:59 UTC hôm nay, tức chưa đóng. ETL bỏ mọi nến có `closeTime > now`; backfill từ `startTime=0`, `limit=1000`: BTC 4 trang, PAXG 3 trang (39 lời gọi cho 11 mã, 30.951 nến). `limit=3` = 2 nến đóng + nến hôm nay đang chạy *(đo 2026-09-05)*; từ lát 7b luật "bỏ `closeTime > now`" gỡ hẳn (cả lượt trọn `limit=40` lẫn `--intraday` `limit=3`) — nến đang chạy vào kho, ghi đè tới khi đóng.

### ⚠️ Bẫy 4 — Nhịp tin PAXG mỏng

Xem §3.4. Đây là bẫy **thiết kế giám sát**, không phải bẫy dữ liệu.

---

## 6. Điều khoản — không quan sát được

| *(đo 2026-08-15)* | |
|---|---|
| `binance.com/en/terms` | **HTTP 202, body rỗng** — tường chặn bot |
| Repo `binance-spot-api-docs` | **Không có file `LICENSE`** |

→ **Không có điều khoản nào quan sát được.** Tài liệu này chỉ ghi sự thật đo được; xử lý pháp lý là việc của chủ dự án.

---

## 7. Đã đo và LOẠI — ba khối, đừng mở lại mà không đọc mục này

### 7.1 ❌ Hàng hoá qua nhóm TradFi perpetual

`fapi.binance.com` **có** loại hợp đồng `TRADIFI_PERPETUAL` — **163 mã**, `underlyingType = COMMODITY` *(nghi ngờ ban đầu rằng Binance không có hàng hoá là **SAI**)*:

| Mã | Hàng hoá | Thanh khoản 24h | Lịch sử sớm nhất |
|---|---|---:|---|
| `XAUUSDT` | Vàng | **1.040 tr USDT** | 2025-12-11 |
| `XAGUSDT` | Bạc | 473 tr | 2026-01-07 |
| `CLUSDT` | **Dầu WTI** | 411 tr | 2026-04-01 |
| `BZUSDT` | Dầu Brent | 189 tr | 2026-03-31 |
| `NATGASUSDT` · `COPPERUSDT` · `XPTUSDT` · `XPDUSDT` | Khí · Đồng · Bạch kim · Palladi | 3–15 tr | chưa kiểm |

Thêm **160 mã cổ phiếu/ETF quốc tế** dạng perp.

**Nhưng dầu không dùng được** *(cùng 91 ngày, đo 2026-08-15)*:

| Nguồn vs FRED | TB có dấu | **\|Lệch\| TB** | Biên độ | >5% |
|---|---:|---:|---|---:|
| **Binance `CLUSDT`** | −3,369% | **3,463%** | −15,81 … +1,37 | 24,2% |
| Binance `CL` index | −3,327% | 3,421% | −15,82 … +1,48 | 23,9% |
| **WiChart `dau_wti`** | −2,512% | **2,771%** | −7,08 … +2,15 | 11,0% |

🔴 **Binance lệch NHIỀU HƠN nguồn đang có.** Tương quan lợi suất ngày: WiChart↔FRED **+0,834** · Binance↔FRED +0,745 · Binance↔WiChart +0,510.

🔴 **Và giá cuối tuần của perp là giá giả** — thị trường cơ sở đóng cửa, perp vẫn chạy 24/7:

| Mã | Biên độ ngày thường | Cuối tuần | Ngày cuối tuần đứng yên hoàn toàn |
|---|---:|---:|---:|
| `CL` | 2,687% | 1,708% | 5/39 |
| `XAU` | 1,365% | 0,455% | 21/71 |
| `XAG` | 3,071% | 0,877% | 17/63 |

Dầu vẫn dao động ~1,7% cuối tuần trong khi NYMEX đóng cửa — đó là **kỳ vọng của người giao dịch crypto, không phải giá dầu**. Nếu vì lý do nào đó vẫn dùng nhóm này, ETL **bắt buộc lọc bỏ ngày không giao dịch của thị trường cơ sở**.

⚠️ Nhóm TradFi **mới xuất hiện** (dầu từ 2026-04-01) và **thành phần nhà cung cấp giá của chỉ số cơ sở: chưa kiểm**. Độ ổn định dài hạn chưa đánh giá được.

### 7.2 ❌ Dựng DXY từ Binance

Đếm trên toàn bộ **3.681 mã** *(đo 2026-08-15)*: **EUR** ✅ · **JPY** ⚠️ chỉ gián tiếp (không có `JPYUSDT`) · **GBP** ❌ đã ngừng (23 mã đều `BREAK`) · **CAD/SEK/CHF** ❌ **0 mã, chưa từng có**.

**Thiếu 3/6 cặp hoàn toàn ⇒ không có cách vớt vát.** DXY dựng bằng Frankfurter — xem [`fx.md`](fx.md).

### 7.3 ❌ BTC làm thước khẩu vị rủi ro

Ghép lợi suất ngày với VN30, 238 phiên *(đo 2026-08-15)*:

| Cặp | Tương quan | n |
|---|---:|---:|
| VN30 ↔ `BTCUSDT` | **−0,0395** | 237 |
| VN30 ↔ `ETHUSDT` | −0,0385 | 237 |
| VN30 ↔ `XAU` index | +0,0219 | 167 |
| VN30(d) ↔ BTC(d−1) | +0,0697 | 237 |

**Cả bốn xấp xỉ 0.** BTC **không** dẫn dắt và **không** đồng pha với VN30. Dùng làm thước khẩu vị rủi ro là **thêm nhiễu, không thêm tin**.

---

## 8. Chưa kiểm — phải đo trước khi triển khai

| Mục | Vì sao cần |
|---|---|
| **Cấu trúc cột file zip `data.binance.vision`** | Không dựng được backfill nếu chưa biết cột |
| **Ngưỡng rate limit thật** | Chủ đích không dò; hiện chỉ có số Binance tự công bố |
| **Lịch sử `XAGUSDT` · `COPPERUSDT` đối chiếu WiChart** | Chưa ai đo — nếu sau này cần bạc/đồng 24/7 thì đây là việc đầu tiên |
| **Thành phần nhà cung cấp giá của chỉ số TradFi** | Ảnh hưởng độ tin của cả nhóm §7.1 |
| **Điều khoản sử dụng** | Không đọc được vì tường chặn bot |

**Giới hạn của phép đo premium:** cửa sổ chỉ **88 ngày** (trần 1000 nến × 3 lát). Bảng đối chiếu PAXG ↔ WiChart thì đủ **712 ngày**.

---

## 9. Quy tắc ETL

1. **Ép `Decimal` cho mọi giá** — API trả chuỗi.
2. **Đọc theo vị trí mảng, hardcode chỉ số cột** kèm chú thích tên; không có tên trường để tự kiểm.
3. **Đặt `timeZone` rõ ràng**, và ghi nhớ nến định danh bằng thời điểm **mở**.
4. **Lưu đơn vị là USDT**, không viết tắt thành USD ở bất kỳ tầng nào.
5. **Đọc `x-mbx-used-weight-1m` sau mỗi lời gọi** và tự phanh trước ngưỡng — `429` nối tiếp sẽ thành `418` cấm IP.
6. **Hiệu chỉnh lệch đồng hồ** (máy trạm chậm hơn server ~646 ms) trước khi tính bất kỳ chỉ số độ tươi nào.
7. **PAXG là chuỗi 24/7, WiChart là chuỗi phiên.** Khi ghép, join theo ngày thật và **ghi cờ ngày cuối tuần** — nếu không, chuỗi vàng sẽ có hai chế độ dữ liệu khác nhau mà không ai biết.
8. **Ngưỡng giám sát của PAXG phải đặt riêng**, không dùng chung với nhịp BTC (§3.4).
