# API công khai Binance — có gì hợp với Finext · đo 2026-08-15

**46/60 lời gọi** (43×`200`, 1×WebSocket, 1×`404`, 1×`202` chặn bot) · chỉ dữ liệu thị trường công khai, chỉ đọc · không đăng ký tài khoản, không tạo khoá, không chạm endpoint giao dịch.

*(Agent không ghi được `.md`; controller ghi lại. Raw: `scratchpad/binance-raw/` — 46 file + `_calllog.jsonl`.)*

## 0. Trả lời thẳng đề bài

Câu hỏi **không phải** "API Binance có tốt không" (có, và đó không phải phát hiện). Câu hỏi là **Binance cho dự án này dữ liệu gì mà ta chưa có**.

| # | Thứ Binance cho | Đo được | Kết luận |
|---|---|---|---|
| 1 | **Vàng thế giới realtime 24/7** (PAXG) | Lệch WiChart **0,369%** TB tuyệt đối / **712 ngày**; premium so LBMA **−0,049%** | ✅ **Lấy** |
| 2 | Dầu WTI/Brent, bạc, đồng, khí qua "TradFi perpetual" | Có thật, thanh khoản lớn — nhưng dầu lệch FRED **3,42%**, **tệ hơn WiChart (2,77%)** | ❌ **Không lấy** |
| 3 | 6 cặp tiền dựng DXY | **CAD/SEK/CHF chưa từng tồn tại**; GBP đã ngừng | ❌ **Không lấy** |
| 4 | BTC/ETH làm thước khẩu vị rủi ro | Tương quan VN30↔BTC = **−0,04** (n=237) | ❌ **Không lấy** |
| 5 | *(ngoài Binance)* chuẩn vàng **LBMA** | 14.662 điểm từ **1968**, không khoá | ✅ **Lấy** |

## 1. Hạ tầng — ghi cho đủ, không phải lý do để lấy

| Mục | Đo được |
|---|---|
| Chặn theo vùng từ Việt Nam | **Không.** `api`/`fapi`/`data-api`/`data`/`stream` đều `200` |
| Xác thực | **Không cần khoá** cho toàn bộ endpoint dữ liệu thị trường |
| Độ trễ (36 mẫu) | min 71 ms · **trung vị 151 ms** · max 406 ms |
| Header hạn mức thật | `x-mbx-used-weight`, `x-mbx-used-weight-1m` trên **mọi** response |
| Hạn mức API tự công bố | `REQUEST_WEIGHT` **6.000/phút** · `RAW_REQUESTS` 300.000/5 phút |
| Mã lỗi | `429` vượt nhịp · `418` cấm IP nếu tiếp tục sau 429 |
| Lệch đồng hồ | máy trạm **chậm hơn server 646 ms** — phải hiệu chỉnh trước khi tính độ trễ |

Tổng weight dùng cả phiên ≈ **100/6.000** mỗi phút. **Chủ đích không dò ngưỡng chặn.**

### Lược đồ `/api/v3/klines` — mảng vị trí, số dạng chuỗi

12 phần tử theo vị trí: `0` mở nến (epoch **ms**) · `1-4` OHLC (**chuỗi**) · `5` KL base (chuỗi) · `6` đóng nến · `7` giá trị quote · `8` số lệnh · `9-10` taker buy · `11` bỏ trống.

⚠️ Nến định danh bằng **thời điểm mở**. `limit` mặc định 500, **tối đa 1000**. Có tham số `timeZone` (mặc định UTC) — **phải đặt rõ**, đừng để mặc định rồi lệch nhãn ngày.
⚠️ **Toàn bộ giá là chuỗi.** Ép `Decimal` ở tầng ETL.

### Realtime & kho lịch sử

WebSocket `wss://stream.binance.com:9443` nối được sau **373 ms**, không khoá, ghép nhiều luồng một kết nối, độ trễ event→nhận **≈23 ms** sau hiệu chỉnh.

⚠️ **Nhịp tin PAXG mỏng:** 20 giây quan sát chỉ nhận **2 bản tin**; 21.941 lệnh/24h ≈ **0,25 lệnh/giây**. Là *tick thưa*, không phải dòng chảy dày như BTC. REST: giao dịch mới nhất cách **4,2 giây**, nến 1 phút trễ **15,5 giây**.

`data.binance.vision`: có bản **ngày và tháng**, mỗi file kèm `.CHECKSUM`. PAXGUSDT 1d sớm nhất `2020-08-28` — khớp đúng REST. File T−1 publish lúc 02:12 UTC. ⚠️ **Chưa mở nội dung zip** — cấu trúc cột: chưa kiểm.

### Điều khoản
`binance.com/en/terms` → **HTTP 202, body rỗng** (tường chặn bot). Repo `binance-spot-api-docs` **không có `LICENSE`**. → **Không có điều khoản nào quan sát được.**

## 2. Giả thuyết 1 — Vàng token hoá ✅ ĐÚNG

### 2.1 Có gì

| Mã | Lịch sử sớm nhất | Ghi chú |
|---|---|---|
| `PAXGUSDT` | **2020-08-28** (~6 năm) | Paxos Gold, 1 token ≈ 1 oz vàng vật chất |
| `XAUTUSDT` | 2026-03-26 | Tether Gold — **quá ngắn để backfill** |
| `XAUUSDT` (perp) | 2025-12-11 | Xem §3 |

Thanh khoản `PAXGUSDT`: trung vị **12,7 tr USDT/ngày**. Chênh mua–bán **0,0002%**.

### 2.2 Đối chiếu PAXG ↔ WiChart `vang_the_gioi` — 712 ngày

Thử cả ba kiểu ghép để loại giả thuyết trễ pha:

| Kiểu ghép | n | Lệch TB có dấu | **\|Lệch\| TB** | sd | Biên độ | **Ngày >2%** |
|---|---|---|---|---|---|---|
| PAXG(d) ↔ WiChart(d−1) | 711 | +0,284% | 0,941% | 1,323% | −8,74 … +6,78 | 10,7% |
| **PAXG(d) ↔ WiChart(d)** | **712** | **+0,197%** | **0,369%** | **0,467%** | **−1,49 … +2,75** | **0,6%** |
| PAXG(d) ↔ WiChart(d+1) | 712 | +0,124% | 0,855% | 1,268% | −5,26 … +12,62 | 8,8% |

**Ghép đúng ngày là ghép đúng** — hai kiểu lệch pha đều xấu đi ~2,4 lần. Không có độ trễ hệ thống.

Chi tiết: trung vị lệch tuyệt đối 0,281% · ngày >1%: 4,8% · **ngày >5%: 0/712**.

**Đối chiếu chỗ đau giá dầu:** dầu lệch **3,35%**, 61% ngày >2%, cực đại 16,4%. Vàng lệch **0,369%**, 0,6% ngày >2%, cực đại 2,75% → **nhỏ hơn gần 10 lần**.

➜ **Cờ "lệch 0,3%" mà `wichart.md` gắn cho `vang_the_gioi` — đo trên 712 ngày thì ĐÚNG** (0,369%). Khác hẳn `dau_wti` (ghi 1,3%, thật 3,35%). Tức bộ cờ **không sai đồng loạt** — phải kiểm từng cái.

4 ngày lệch >2% đều là ngày vàng biến động mạnh → **lệch do lệch giờ chốt, không phải sai nguồn**.

⚠️ **Phát hiện đáng giá:** **36,8% điểm cuối tuần của WiChart trùng khít điểm liền trước** (70/190) — WiChart **giữ nguyên giá cuối tuần**. PAXG chạy thật 24/7. Đây là chỗ PAXG **hơn hẳn**.

### 2.3 Premium của PAXG — đo, không giả định

Chuẩn: **LBMA Gold PM** (chốt 15:00 London = 14:00 UTC mùa hè). So với **nến 1 giờ mở lúc 14:00 UTC** cùng ngày để triệt tiêu chênh giờ.

| Phép đo (88 ngày) | TB có dấu | \|Lệch\| TB | Biên độ |
|---|---|---|---|
| **PAXG tại 14:00 UTC vs LBMA PM** | **−0,049%** | **0,130%** | −0,365 … +0,361 |
| PAXG sau hiệu chỉnh neo USDT | −0,105% | 0,149% | −0,441 … +0,268 |
| XAUT tại 14:00 UTC vs LBMA PM | −0,174% | 0,221% | −0,621 … +0,300 |
| PAXG vs XAUT (2 tổ chức phát hành độc lập) | +0,125% | 0,144% | −0,223 … +0,431 |

**Không ngày nào lệch quá 0,5%.** Premium thực chất là **discount −0,05%**, nhỏ hơn cả chênh mua–bán của nhiều nguồn. Hai token của hai tổ chức độc lập chỉ khác nhau 0,14% → **bằng chứng mạnh cả hai bám thật vào vàng vật chất**.

⚠️ **Đừng lấy giá close 23:59 UTC rồi so LBMA PM** — cho 0,618% và sẽ bị hiểu nhầm là premium, trong khi thực chất là **10 tiếng biến động thật**.

### 2.4 Khác biệt so với giá dầu
Ở dầu: WiChart *tươi mà lệch*, FRED *chuẩn mà chậm*, không nguồn nào đạt cả hai. **Ở vàng, PAXG đạt cả hai.**

## 3. Giả thuyết 4 — nghi ngờ trong brief SAI, Binance CÓ hàng hoá

`fapi.binance.com` có loại hợp đồng `TRADIFI_PERPETUAL` — **163 mã**, `underlyingType = COMMODITY`:

| Mã | Hàng hoá | Thanh khoản 24h | Lịch sử sớm nhất |
|---|---|---|---|
| `XAUUSDT` | Vàng | **1.040 tr USDT** | 2025-12-11 |
| `XAGUSDT` | Bạc | 473 tr | 2026-01-07 |
| `CLUSDT` | **Dầu WTI** | **411 tr** | 2026-04-01 |
| `BZUSDT` | Dầu Brent | 189 tr | 2026-03-31 |
| `NATGASUSDT` · `COPPERUSDT` · `XPTUSDT` · `XPDUSDT` | Khí · Đồng · Bạch kim · Palladi | 3–15 tr | chưa kiểm |

Thêm **160 mã cổ phiếu/ETF quốc tế** dạng perp (`SPY`, `QQQ`, `AAPL`, `NVDA`, cổ phiếu Hàn/HK, ETF quốc gia).

### 3.1 Nhưng dầu KHÔNG dùng được

| Nguồn (cùng 91 ngày) | TB có dấu | **\|Lệch\| TB** | Biên độ | >5% |
|---|---|---|---|---|
| **Binance `CLUSDT`** vs FRED | −3,369% | **3,463%** | −15,81 … +1,37 | 24,2% |
| Binance `CL` index vs FRED | −3,327% | **3,421%** | −15,82 … +1,48 | 23,9% |
| **WiChart `dau_wti`** vs FRED | −2,512% | **2,771%** | −7,08 … +2,15 | 11,0% |

🔴 **Binance lệch NHIỀU HƠN WiChart** — tệ hơn nguồn đang có.

Tương quan lợi suất ngày: WiChart↔FRED **+0,834** · Binance↔FRED +0,745 · Binance↔WiChart +0,510.

### 3.2 🔴 Bằng chứng chéo làm lung lay kết luận cũ về giá dầu

**Cả hai** nguồn độc lập (WiChart từ SunSirs, Binance từ nhà cung cấp chỉ số riêng) đều thấp hơn FRED **2,5–3,4% một cách hệ thống**. Cộng thêm Yahoo `CL=F` thấp hơn **1,29%** (đo ở `report-more-sources.md` §2.2) → **ba nguồn không liên quan cùng lệch một chiều so với FRED**.

➜ Kết luận *"WiChart sai"* ở `report-wichart-oil-deviation.md` **cần xét lại**. Xem §5 để biết giả thuyết giải thích.

### 3.3 Bẫy nếu vẫn muốn dùng nhóm TradFi

🔴 **Giá cuối tuần là giá giả.** Thị trường cơ sở đóng cửa, perp vẫn chạy 24/7:

| Mã | Biên độ ngày thường | Cuối tuần | Ngày cuối tuần đứng yên hoàn toàn |
|---|---|---|---|
| `CL` | 2,687% | **1,708%** | 5/39 |
| `XAU` | 1,365% | 0,455% | 21/71 |
| `XAG` | 3,071% | 0,877% | 17/63 |

Dầu vẫn dao động ~1,7% cuối tuần trong khi NYMEX đóng cửa — đó là **kỳ vọng của người giao dịch crypto, không phải giá dầu**. ETL **bắt buộc lọc bỏ ngày không giao dịch** của thị trường cơ sở.

## 4. Giả thuyết 2 & 3 — cả hai ❌

### DXY: không dựng được
Đếm trên toàn bộ **3.681 mã**: **EUR** ✅ · **JPY** ⚠️ chỉ gián tiếp (không có `JPYUSDT`) · **GBP** ❌ đã ngừng (23 mã đều `BREAK`) · **CAD/SEK/CHF** ❌ **0 mã, chưa từng có**. Thiếu 3/6 hoàn toàn → **không có cách vớt vát**.

**Chênh neo USDT (đo trước, để loại nghi ngờ):** `USDCUSDT` 3.000 nến 1 giờ → lệch neo TB **−0,050%**, **max chỉ 0,145%**. Cặp USD thật `USDTUSD` (271 ngày) trung vị 0,99970. → Chênh neo **dưới 0,15%**, **nhỏ hơn nhiễu của chính WiChart** — không phải lý do loại Binance.

### Khẩu vị rủi ro: không có tín hiệu
Ghép lợi suất ngày VN30 (238 phiên):

| Cặp | Tương quan | n |
|---|---|---|
| VN30 ↔ `BTCUSDT` | **−0,0395** | 237 |
| VN30 ↔ `ETHUSDT` | −0,0385 | 237 |
| VN30 ↔ `XAU` index | +0,0219 | 167 |
| VN30(d) ↔ BTC(d−1) | +0,0697 | 237 |

**Cả bốn xấp xỉ 0.** BTC **không** dẫn dắt và **không** đồng pha với VN30. Dùng làm thước khẩu vị rủi ro là **thêm nhiễu, không thêm tin**. Vấn đề bản quyền VIX vẫn còn nguyên.

## 5. Giả thuyết của controller về mâu thuẫn giá dầu *(CHƯA KIỂM)*

Ba nguồn độc lập cùng thấp hơn FRED có một lời giải thích kinh tế mạch lạc:

- `DCOILWTICO` là **giá giao ngay** WTI tại Cushing (EIA).
- `CL=F` là **hợp đồng tương lai kỳ hạn gần**; `CLUSDT` của Binance và `dau_wti` của WiChart nhiều khả năng cũng bám theo tương lai.
- Khi thị trường **backwardation** (nguồn cung căng, kỳ vọng giá tương lai thấp hơn hiện tại) thì **tương lai < giao ngay** — đúng chiều lệch quan sát được.
- Và độ trôi **−1,03% → −0,10% → −1,19% → −2,70%** qua bốn cửa sổ 60 phiên (đo ở `report-more-sources.md` §2.2) **khớp với backwardation dốc dần**, không khớp với "một nguồn sai".

→ Nếu đúng thì **FRED không sai, WiChart cũng không hẳn sai — chúng đo hai thứ khác nhau**, và câu hỏi thật là *"dự án muốn giá giao ngay hay giá tương lai?"*.

**Chưa kiểm.** Cách kiểm rẻ: lấy chênh lệch hai kỳ hạn liền nhau của `CL=F` để đo trực tiếp cấu trúc kỳ hạn, xem có backwardation không và có dốc dần không.

## 6. Việc nên làm tiếp

1. Đối chiếu `XAGUSDT` (bạc) và `COPPERUSDT` (đồng) với WiChart theo đúng phương pháp — chưa ai đo.
2. **Rà lại toàn bộ cờ "lệch x%" của `wichart.md`.** Cờ `vang_the_gioi` **đúng**, cờ `dau_wti` **sai gấp 3 lần** → phải kiểm từng cái, không suy đoán đồng loạt.
3. Kiểm giả thuyết backwardation ở §5.
4. Mở file zip `data.binance.vision` để chốt cấu trúc cột trước khi dựng backfill.

## 7. Giới hạn báo cáo

Cửa sổ đo premium PAXG chỉ **88 ngày** (giới hạn 1000 nến × 3 lát); bảng đối chiếu WiChart thì đủ 712 ngày · FRED WTI dùng file lưu từ 2026-08-12 · chỉ số cơ sở nhóm TradFi do Binance tự tổng hợp, **thành phần nhà cung cấp giá chưa kiểm** · nhóm TradFi mới xuất hiện (dầu từ 2026-04-01), **độ ổn định dài hạn chưa đánh giá được** · `stooq.com` chặn bằng proof-of-work JS, **đã dừng, không vượt**.
