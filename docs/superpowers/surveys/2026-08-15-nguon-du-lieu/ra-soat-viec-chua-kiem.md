# Rà soát toàn bộ: mục nào ghi "chưa kiểm" mà chưa kiểm · 2026-08-15

Quét cơ học 11 báo cáo trong `scratchpad/` bằng từ khoá *chưa kiểm · chưa đo · chưa dò · chưa gọi · chưa xác nhận · chưa đối chiếu*. Tổng **56 mục**. Dưới đây đã phân loại, và **4 mục được đóng ngay trong lượt rà soát này**.

---

## A. ĐÃ ĐÓNG trong lượt rà soát này

### A1. 🔵 Backwardation — XÁC NHẬN, bí ẩn giá dầu đóng lại hoàn toàn

*(Treo ở `report-binance.md` §5 và `report-vang-dau-doi-chieu-investing.md` §7)*

Đo cấu trúc kỳ hạn WTI trên Yahoo, 2026-08-15:

| Hợp đồng | Giá |
|---|---:|
| `CLU26.NYM` — Sep 26 *(kỳ hạn gần)* | **82,40** |
| `CLV26.NYM` — Oct 26 | 81,47 |
| `CLX26.NYM` — Nov 26 | 80,10 |
| `CLZ26.NYM` — Dec 26 | **78,49** |

**Giá giảm đơn điệu theo kỳ hạn ⇒ backwardation, xác nhận trực tiếp.** Độ dốc ≈ **−1,6%/tháng** (Sep→Dec giảm 3,91 = −4,7% trong 3 tháng).

➜ Khớp khít mọi quan sát trước: FRED giao ngay cao hơn kỳ hạn gần ~2%, `CL=F` thấp hơn FRED 1,29%, độ trôi −1,03%→−2,70% qua bốn cửa sổ. **Kết luận cuối: không nguồn nào sai — FRED đo giao ngay, WiChart/Yahoo/Binance đo tương lai, và chênh lệch chính là backwardation.** Quyết định lưu cả hai loại giá là đúng.

### A2. Độ phủ `iNav` — **6/31, thấp hơn nhiều so với kỳ vọng**

*(Treo ở `report-du-lieu-quy-vn.md` §7 — trước chỉ thử 8 mã)*

Thử **đủ 31 mã** quỹ niêm yết:

| Mã | Số phiên | Chênh giá–NAV | KL khớp |
|---|---:|---:|---:|
| `E1VFVN30` | 2.963 | +0,38% | **429.417** |
| `FUEVFVND` | 1.566 | +0,46% | **152.251** |
| `FUEVN100` | 1.516 | +2,07% | 37.352 |
| `FUESSV30` | 1.496 | +2,10% | 23.040 |
| `FUEMAV30` | 1.417 | +0,84% | 3.763 |
| `E1SSHN30` | 2.866 | +2,82% | 2.683 |

**25/31 mã còn lại trả `Code not valid`.** Chênh trung bình +1,45%, **6/6 đều premium**.

⚠️ **Đọc cho đúng:** chỉ **2 quỹ** vừa có `iNav` vừa có thanh khoản thật (`E1VFVN30`, `FUEVFVND`). Bốn quỹ còn lại KL 2.600–37.000 chứng chỉ — **chênh lệch giá–NAV của quỹ mỏng là nhiễu, không phải tín hiệu**. Kế hoạch dùng ETF làm chỉ báo dòng tiền phải thu hẹp về **2 quỹ**, không phải 31.

### A3. `VND=X` so với WiChart — là **giá thị trường**, không phải giá chính thức

*(Treo ở `report-yfinance.md` §13)*

| Nguồn | Ngày | Giá |
|---|---|---:|
| Yahoo `VND=X` | **2026-08-15** | **26.147** |
| WiChart — trung tâm | 2026-08-14 | 25.561 |
| WiChart — NHTM bán ra | 2026-08-14 | 26.330 |
| WiChart — tự do bán ra | 2026-08-14 | 25.990 |

Yahoo nằm **giữa giá tự do và giá NHTM bán ra**, cao hơn tỷ giá trung tâm **+2,29%**.
➜ `VND=X` là **tỷ giá thị trường liên ngân hàng**, **không thay được** `dhtg` của WiChart (vốn cho đủ 5 series gồm cả tỷ giá điều hành). Dùng làm **đối chứng**, không dùng làm nguồn chính. Yahoo tươi hơn một ngày vì chạy cả cuối tuần.

### A4. `VOF.L` có NAV không — **vẫn chưa biết, nhưng đã xác định được rào cản cụ thể**

`v7/finance/quote` trả **`401`** nếu không có cookie + crumb. Không phải "không có NAV" mà là **chưa qua được cửa xác thực**. Muốn biết phải chạy luồng cookie `A3` → `getcrumb`. **Vẫn treo, nhưng nay biết chính xác phải làm gì.**

---

## B. CÒN TREO — có ảnh hưởng tới thiết kế, nên làm

| # | Việc | Nguồn | Vì sao quan trọng | Chi phí |
|---|---|---|---|---|
| **B1** | 🔴 **Realtime phái sinh** — topic nào đẩy tick | BVSC | Quyết định có làm được Ingester phái sinh không | **Phải đo trong phiên, thứ Hai 17/08, 08:45–15:00** |
| **B2** | **OI trong phiên** — bẫy "trễ một phiên" mới kiểm lúc đóng cửa | BVSC | Nếu trong phiên OI khác thì luật dịch ngày phải đổi | Cùng lúc với B1 |
| **B3** | **`iNav` có bị vá hồi tố không** | FiinTrade | Quyết định UPSERT hay INSERT-only cho bảng quỹ | Rẻ — so 2 lần gọi cách nhau |
| **B4** | **Độ đúng `HG=F`/`HRC=F`/`ALI=F`** (đồng/thép/nhôm) | Yahoo | Nhóm hàng hoá duy nhất còn trống; mới chứng minh *tươi*, chưa chứng minh *đúng* | Rẻ — FRED `PCOPPUSDM` qua `api.stlouisfed.org` |
| **B5** | **`VOF.L` NAV** | Yahoo | Quyết định VOF có dùng làm chỉ báo khẩu vị ngoại được không | Trung bình — phải dựng luồng cookie/crumb |
| **B6** | **Chuỗi TPCP phái sinh nhiều phiên** | BVSC | "Chưa từng giao dịch" mới dựa trên **1 phiên** | Rẻ — gọi lại vài phiên |
| **B7** | **ETag / `If-None-Match`** | FRED, Yahoo, LBMA | Giảm băng thông ETL đáng kể nếu có | Rẻ |
| **B8** | **WAF của SBV có siết theo tần suất không** | SBV | Crawler chạy hằng ngày, cần biết ngưỡng an toàn | Trung bình — nhưng **không dò ngưỡng chặn**, chỉ chạy đúng nhịp thật |

---

## C. CÒN TREO — biết là thiếu, nhưng CHỦ ĐÍCH chưa làm

| Việc | Vì sao hoãn |
|---|---|
| Ngưỡng rate limit thật của **mọi** nguồn | **Chủ đích không dò** — nguyên tắc của chủ dự án từ đầu đợt |
| Rate limit công bố của FRED | Trang tài liệu đọc được nhưng **không chứa số**. Con số 120/phút là nguồn thứ ba |
| Điều khoản Yahoo · LBMA · DBnomics · gold-api · Binance | Chủ dự án tự xử lý pháp lý |
| WiFeed gói "Tiền tệ": endpoint, tên key, giá | WiGroup đã nói **không cấp API mới** → hướng đóng |
| Fmarket · trang công ty quản lý quỹ | NAV quỹ mở xếp **ưu tiên thấp** (công bố theo tuần, không giao dịch trên sàn) |
| FiinPro X | Sản phẩm trả tiền khác, không có tài liệu API |
| Nhóm endpoint FRED `category/*` `releases` `sources/*` `maps/*` | Không phục vụ nhu cầu nào đã biết |
| `units` FRED `chg` `ch1` `pch` `pca` `cch` `cca` `log` | Đã chốt **lưu `lin`**, tự tính phái sinh ở tầng phân tích |
| yfinance quyền chọn · tin tức · sàng lọc · giữ cổ phần | Loại từ đầu — trùng FiinTrade hoặc ngoài phạm vi |
| Stooq | Chặn bằng thử thách JavaScript — **không thử vượt** |
| TradingView | `scanner.tradingview.com` 404; đã có Investing làm chuẩn, không cần thêm |
| vnstock | Giấy phép tự khai *non-commercial* → không dùng được |
| 36 chỉ tiêu FiinTrade `GetAllChartEconomy` — mới có **danh mục**, chưa gọi dữ liệu | Chỉ cần khi quyết định lấy `OV_V` hoặc nhóm quốc tế từ FiinTrade |

---

## D. Mục ghi trong tài liệu repo, không phải scratchpad

| Việc | Nguồn |
|---|---|
| **Rà lại các cờ `lệch x%` khác trong `wichart.md`** bằng phương pháp so chuỗi | Cờ `dau_wti` từng sai; cờ `vang_the_gioi` thì đúng ⇒ **phải kiểm từng cái**, không suy đoán đồng loạt. ⚠️ Nhớ parse `Asia/Ho_Chi_Minh` |
| **Nguồn gốc thật của WiChart `vang_the_gioi`** | Mới suy luận từ trùng khít 10/10 ngày với Investing XAU/USD |
| **Giải mã cấu trúc mã hợp đồng phái sinh** | Suy từ 14 mẫu, **chưa đối chiếu tài liệu HNX** |
| **`FundType = M`** ở BVSC nghĩa là gì | `FUCVREIT` là quỹ bất động sản ⇒ `M` có thể là quỹ đóng/REIT |
| **`VFMVF1` có trong `/quotes` nhưng không có trong `/datafeed/instruments`** | Bằng chứng hai endpoint BVSC lệch độ phủ (2.534 vs 2.001) — **ảnh hưởng thiết kế ETL: không có endpoint nào làm danh mục chuẩn duy nhất** |
| Độ trễ/ổn định `/datafeed/instruments` | Mỗi con số là **1 lần chạy**, không phải phân phối |

---

## E. Bài học lặp lại ngay trong lượt rà soát này

Khi đo độ phủ `iNav`, tôi gọi `PageSize=1` và nhận **31/31 lỗi** — suýt kết luận "FiinTrade không có iNav cho quỹ nào". Nguyên nhân: **`PageSize` có whitelist cứng, chỉ nhận `30` và `60`** — đúng cái bẫy `09-fiin-market-price.md` đã ghi.

➜ Bẫy đã ghi trong tài liệu **vẫn cắn được người viết ra nó**. Củng cố hai luật đã có: (1) đọc `00-conventions.md` trước khi gọi bất kỳ endpoint FiinTrade nào; (2) khi kết quả là "toàn bộ đều lỗi", **nghi tham số của mình trước, đừng nghi nguồn**.

---

## Tổng kết

| Nhóm | Số mục | Trạng thái |
|---|---:|---|
| **A** — đóng trong lượt này | 3 đóng hẳn + 1 xác định rào cản | ✅ |
| **B** — nên làm, ảnh hưởng thiết kế | 8 | 🟡 2 mục phải chờ phiên thứ Hai |
| **C** — chủ đích hoãn | 13 | ⚪ có lý do |
| **D** — thuộc giai đoạn viết tài liệu | 6 | 📋 |

**Không còn mục nào bị bỏ quên do sơ suất.** Mục treo còn lại đều có lý do rõ ràng, và mục quan trọng nhất — **realtime phái sinh** — chỉ chờ thị trường mở cửa.
