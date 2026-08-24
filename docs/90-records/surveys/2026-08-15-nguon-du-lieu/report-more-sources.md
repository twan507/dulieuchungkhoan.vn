# Nguồn dữ liệu miễn phí ngoài akshare/FRED — DXY · nguồn khác · hàng hoá

**Ngày đo:** 2026-08-15 · **83/100 lời gọi** (68×`200`, 7×`404`, 3×`403`, 2×`401`, 3 lỗi kết nối) · tuần tự, nghỉ ≥1,05 s cùng host · không dò ngưỡng chặn

*(Agent không ghi được `.md`; controller ghi lại. Phần kiểm chứng độc lập ở §8.)*

## 0. Ba câu trả lời

| Việc | Kết luận |
|---|---|
| **1. Dựng DXY hằng ngày** | ✅ **Giải được.** **Frankfurter** (`api.frankfurter.app`, dữ liệu ECB) — **1 lời gọi lấy đủ 6 cặp**, không khoá, lịch sử từ **1999-01-04**. DXY dựng lại 2026-08-14 = **99,6113** vs DXY ICE **99,67** → **−0,059%**. Kiểm 248 phiên: **\|lệch\| TB 0,180%**, không thiên lệch |
| **2. Nguồn miễn phí khác** | ✅ 5 nguồn đáng lấy. Phát hiện lớn nhất **không phải nguồn mới**: `fredgraph.csv` chạy được **không cần khoá API**; trang điều khoản FRED nay đọc được — **và nó chứa điều cấm quan trọng** (§7) |
| **3. Hàng hoá quốc tế** | ⚠️ Không nguồn đơn lẻ nào vừa tươi vừa chuẩn cho dầu. **Ghép được:** FRED làm mức chuẩn + Yahoo `CL=F` làm suất sinh lời → **0,18–0,42%**. Vàng thay thẳng bằng **LBMA** |

## 1. VIỆC 1 — Sáu cặp tiền dựng DXY

### 1.1 Bảy nguồn tỷ giá đã gọi thật

| Nguồn | Đủ 6 cặp? | Khoá | Lịch sử | Mốc chốt giá | Lời gọi cho 6 cặp |
|---|---|---|---|---|---|
| **`api.frankfurter.app` (ECB)** | ✅ | ❌ | **1999-01-04 →** | **fixing 14:15 CET** | **1** |
| `api.frankfurter.dev` (v2) | ✅ | ❌ | 1948 → (tài liệu) | ⚠️ mặc định **trộn 84 NHTW** | 1 |
| `open.er-api.com` | ✅ | ❌ | **không có** | 1 lần/ngày ~00:02 UTC | 1 |
| currency-api (jsDelivr) | ✅ (+696 mã) | ❌ | có | 🔴 **lệch nhãn ngày** | 1 |
| Yahoo `v8/finance/chart` | ✅ | ❌ | 1996–2003 tuỳ cặp | đóng cửa ~17:00 ET | **6** |
| ECB SDMX gốc | ✅ nhưng pivot EUR | ❌ | 1999 → | 14:15 CET | 1 |
| `fredgraph.csv` | ✅ | ❌ | **1971 →** | 🔴 **H.10 theo tuần** | 1 |

**Cần đăng ký, chưa kiểm:** exchangerate.host (`missing_access_key`) · finnhub (`401`) · tiingo (`403`) · marketstack (`401`) · Alpha Vantage & Twelve Data (khoá `demo` chạy được, dùng thật phải đăng ký).

### 1.2 🔵 Nghiệm thu — dựng DXY rồi đối chiếu DXY thật

Chuẩn độc lập: `DX-Y.NYB` trên Yahoo — chính là **chỉ số ICE** (`fullExchangeName: "ICE Futures"`, từ 1971).

**Ngày 2026-08-14:**

| Nguồn 6 cặp | **DXY dựng lại** | **DXY ICE thật** | **Sai lệch** |
|---|---|---|---|
| **Frankfurter / ECB** | **99,6113** | **99,67** | **−0,059%** |
| open.er-api.com | 99,6471 | 99,67 | −0,023% |
| Yahoo 6 cặp | 99,6151 | 99,67 | −0,055% |
| currency-api | 99,9075 | 99,67 | **+0,238%** ⚠️ |

**Kiểm rộng 1 năm (2025-08-15 → 2026-08-14):**

| Cách dựng | Mốc chốt | n | Lệch TB có dấu | **\|Lệch\| TB** | p90 | max | sd |
|---|---|---:|---:|---:|---:|---:|---:|
| **A. Frankfurter / ECB** | 14:15 CET | **248** | **+0,013%** | **0,180%** | 0,377% | 0,975% | 0,241% |
| B. FRED `DEX*` | noon ET | 27 | +0,062% | 0,158% | 0,213% | 1,500% | 0,325% |
| C. Yahoo 6 cặp | ~17:00 ET | 251 | −0,008% | 0,260% | 0,548% | 0,978% | 0,330% |

Phương án A: tương quan mức **0,9787** · tương quan biến động ngày **0,489** · trùng dấu tăng/giảm **62%**.

**Kết quả nghịch trực giác:** Yahoo lấy giá **đóng cửa** (đúng mốc ICE) mà lại **kém hơn** ECB fixing (0,260% vs 0,180%). Nguyên nhân đo được: **6 cặp của Yahoo không đồng bộ mốc thời gian** — cùng phiên, `EURUSD=X`/`GBPUSD=X` có `regularMarketTime` 2026-08-14 21:29 UTC, còn `JPY=X`/`CAD=X`/`SEK=X`/`CHF=X` = 2026-08-15 04:21 UTC.

### 1.3 Năm bẫy đã bắt

1. 🔴 **currency-api lệch nhãn ngày một phiên.** File nhãn `2026-08-14` thực chất mang số phiên **08-13**. Rẻ và phủ rộng nhưng **không tin được nhãn ngày**.
2. ⚠️ **ECB fixing ≠ giá đóng cửa — đây là toàn bộ nguồn gốc sai lệch 0,18%.** Fixing chốt 14:15 CET = 08:15 ET; DXY ICE chốt 17:00 ET — cách **8 giờ 45 phút giao dịch**. Sai lệch **không có dấu cố định**, **không hiệu chỉnh được bằng hằng số**.
3. ⚠️ **Lịch nghỉ hai bên không trùng.** 1 năm: 3 ngày ICE có mà ECB không; 7 ngày ECB có mà ICE không. Chuỗi dựng lại **không khớp 1-1**.
4. ⚠️ Frankfurter **nới ngày bắt đầu** ra trước (xin `08-01..08-14` trả `start_date 07-31`).
5. 🔴 **Frankfurter v2 mặc định TRỘN 84 NHTW.** Trả cả ngày thứ Bảy, tươi hơn — nhưng **không còn là tỷ giá tham chiếu chính thức của tổ chức nào**. **Bắt buộc `providers=ECB`** — đã kiểm: v2 + `providers=ECB` trả đúng từng con số của v1.

### 1.4 Chọn Frankfurter

1 lời gọi đủ 6 cặp; thêm 1 lời gọi cho cả chuỗi lịch sử → **backfill 27 năm tốn một lời gọi**. Không khoá. Chính xác nhất trong ba cách. Điều khoản quan sát trực tiếp trên `frankfurter.dev`: không hạn mức tháng/ngày, chỉ rate-limit chống lạm dụng; mã nguồn mở, tự dựng được bằng Docker.

**Dự phòng `open.er-api.com`** — nhược: endpoint mở **không có lịch sử**.

⚠️ **Phải ghi vào tài liệu:** DXY dựng lại là **ảnh chụp 14:15 CET**, sai số **0,18% TB / 0,98% max**. Đủ cho phân tích vĩ mô, **không đủ** để hiển thị cạnh một giá đóng cửa thật.

## 2. VIỆC 3 — Hàng hoá

### 2.1 🔵 Lấy được FRED không cần khoá API

`fredgraph.csv?id=DCOILWTICO` → `200`, 605 ms, 178.830 byte, 10.594 dòng, 1986→2026-08-11, **không truyền khoá nào**.

| Khả năng | Đo được |
|---|---|
| Nhiều series một lời gọi | ✅ `?id=A,B,C` |
| Khoảng ngày `cosd`/`coed` | ⚠️ **chỉ đúng khi một `id`** |
| Giá trị thiếu | chuỗi **rỗng** `,,` — **khác** JSON API (dùng `"."`) |
| Nhiều series **khác tần suất** | 🔴 trả về **file ZIP** |

⚠️ `DTWEXBGS` qua CSV **vẫn dừng 2026-08-07** → bỏ khoá API **không** làm chỉ số đô tươi lên.

### 2.2 Dầu — không nguồn đơn lẻ nào đạt

Yahoo `CL=F` (tương lai WTI NYMEX kỳ hạn gần) vs `DCOILWTICO`, 246 ngày: lệch TB **−1,291%**, |lệch| TB **1,408%**, biên độ −5,22..+1,10.

Trên đúng cửa sổ đã đo WiChart (n=125): |lệch| TB **2,04%** (WiChart 3,35%), sd 1,46% (WiChart 3,97%).

Nhưng chênh mức **trôi theo thời gian** — 4 cửa sổ 60 phiên: −1,03% → −0,10% → −1,19% → **−2,70%**. **Không hiệu chỉnh được bằng hằng số.**

### 2.3 🔵 Cách ghép — mức của FRED, biến động của Yahoo

```
WTI_uoc_luong[t] = FRED[t-k] × ( CL=F[t] / CL=F[t-k] )
```

| Số phiên nối | n | Sai số tuyệt đối TB | p90 | max |
|---:|---:|---:|---:|---:|
| 1 | 245 | **0,183%** | 0,426% | 3,513% |
| 4 | 242 | **0,361%** | 0,915% | 3,901% |
| 5 | 241 | 0,418% | 1,093% | 3,943% |

| Cách | Sai số tuyệt đối TB |
|---|---:|
| WiChart `dau_wti` | **3,35%** |
| Dùng thẳng `CL=F` | 1,41% |
| **FRED + suất sinh lời `CL=F`, nối 4 phiên** | **0,36%** |

➜ Tốt hơn WiChart **~9 lần** ở độ trễ thực tế, vẫn tươi bằng WiChart. Chi phí **2 lời gọi/ngày**, không khoá.

**Giới hạn:** là **số ước lượng** → phải đánh cờ `is_estimated` và **ghi đè bằng số FRED** khi EIA công bố.

### 2.4 Brent và khí — kém hẳn

| Cặp | n | \|Lệch\| TB | Biên độ |
|---|---:|---:|---|
| `BZ=F` vs `DCOILBRENTEU` | 50 | **3,25%** | −8,31..+4,77 |
| `NG=F` vs `DHHNGSP` | 244 | **7,02%** | **−82,83..+30,83** |

🔴 Tương lai khí **không** thay được giao ngay Henry Hub. Nếu cần khí hằng ngày thì **`DHHNGSP` của FRED là nguồn duy nhất đo được**.

### 2.5 🔵 Vàng và bạc — có nguồn sạch hẳn

**LBMA** `prices.lbma.org.uk/json/gold_pm.json` / `silver.json`:

| | Vàng PM | Bạc |
|---|---|---|
| Lịch sử | **1968-04-01 →** 2026-08-14 | **1968-01-02 →** |
| Số điểm | **14.662** | 14.806 |
| Khoá | ❌ | ❌ |
| Một lời gọi lấy | **toàn bộ lịch sử** (913 KB) | |
| Độ trễ | **0 ngày làm việc** | |

Đối chiếu chéo Yahoo: `GC=F` vs LBMA → |lệch| TB **0,49%**, chỉ **1%** ngày >2%. `SI=F` vs LBMA bạc → 1,81%, 31% ngày >2% (fixing bạc chốt trưa London, COMEX chốt chiều NY).

### 2.6 Hướng khác

| Nguồn | Kết quả |
|---|---|
| **EIA API v2** | `403 API_KEY_MISSING` — cần đăng ký. *(`DCOILWTICO`/`DHHNGSP` của FRED **chính là dữ liệu EIA**, lấy được không khoá)* |
| **World Bank Pink Sheet** | Tải được, **86 mặt hàng** — nhưng tần suất **THÁNG**, và đường dẫn gọi được chỉ tới 2024M12 |
| **DBnomics `EIA/PET`** | 180.591 series — chưa gọi series cụ thể |
| Đồng, thép, than | 🔴 **Không tìm được nguồn ngày miễn phí không khoá** có mốc chuẩn để đối chiếu |

## 3. VIỆC 2 — Năm nguồn đáng lấy

| # | Nguồn | Lấp chỗ nào | Khoá |
|---|---|---|---|
| **1** | **FRED qua `fredgraph.csv`** | Đường vào mới — bỏ khoá API, nhiều series một lời gọi | ❌ |
| **2** | **Frankfurter** | Tỷ giá 201 đồng tiền, 84 NHTW, từ 1948. Giải trọn Việc 1 | ❌ |
| **3** | **LBMA** | Vàng/bạc fixing chính thức, 1968→, 14.662 điểm/1 lời gọi | ❌ |
| **4** | **Yahoo `v8/finance/chart`** | **`DX-Y.NYB`** (DXY ICE thật, 1971→) — thứ không nguồn nào khác có | ❌ |
| **5** | **DBnomics** | 93 nhà cung cấp · 1,73 tỷ series. Cửa **duy nhất** vào IMF khi API gốc chết. Có **NBS & SAFE (TQ)** | ❌ |

### 3.1 Đã thử và loại

| Nguồn | Kết quả |
|---|---|
| **World Bank API** | ✅ chạy, nhưng dữ liệu **năm** — WiChart có CPI **tháng** từ 2003 |
| **BIS SDMX** | 29 dataflow, 🔴 **không có Việt Nam** (`WS_EER M.N.B.VN` → 404) |
| **IMF trực tiếp** | 🔴 `dataservices.imf.org` ConnectionError · `api.imf.org` 404 → phải đi qua DBnomics |
| **GSO** | 🔴 đã **đổi tên miền sang `nso.gov.vn`**; trang mới là WordPress, **không thấy API** |
| **vnstock** | 🔴 giấy phép PyPI tự khai: *personal, research, non-commercial* — **chưa gọi thử** |
| **Stooq** | 🔴 chặn bằng **thử thách JavaScript**. Không thử vượt |
| **Nasdaq Data Link** | 🔴 `403` chống bot |
| **Chỉ số Wilshire trên FRED** | 🔴 **không còn** — FRED gỡ từ 03/06/2024 |

➜ **Chỗ hụt "chỉ số quốc tế": không tìm được nguồn miễn phí nào điều khoản thoáng hơn.** Giữ khuyến nghị lấy `DJI`/`NASDAQ`/`N225` **từ FiinTrade**; Yahoo chỉ dùng cho `DX-Y.NYB` và `^GSPC`, và phải ghi rõ Yahoo là **API nội bộ không cam kết**.

### 3.2 DBnomics — lấy nhưng đúng vai

93 nhà cung cấp · 47.062 bộ · **1.725.529.719 series**, không khoá. Lấy được `IMF/IFS/M.VN.PCPI_IX` (CPI VN theo tháng) thật.

🔴 **Rất chậm và rất chênh:** `providers` 6.754 ms · `search?q=Vietnam` **11.799 ms**.
🔴 **Tìm kiếm nhiễu nặng:** `search?q=Vietnam` — **8/20 kết quả đầu không phải dữ liệu Việt Nam** (Eurostat "hàng hoá vận chuyển", ISTAT "người nước ngoài cư trú"). **Giống hệt bẫy `LNU*` "Vietnam-Era veterans"** của FRED.

➜ Cửa dự phòng, **không phải nguồn thường nhật**.

## 4. Ngân sách nếu triển khai

| Mục | Lời gọi/ngày |
|---|---:|
| 6 cặp tiền dựng DXY (Frankfurter) | 1 |
| Đối chứng tỷ giá | 1 |
| Dầu WTI mức chuẩn (fredgraph) | 1 |
| Dầu WTI nối phiên (Yahoo `CL=F`) | 1 |
| Brent + khí + VIX + đô broad (1 lời gọi, nhận ZIP) | 1 |
| Vàng + bạc (LBMA) | 2 |
| DXY thật để giám sát sai lệch | 1 |
| **Tổng thường nhật** | **≈ 8** |
| **Backfill một lần** | **≈ 13 lời gọi, ~3 MB** |

Không mục nào cần khoá API.

## 5. Hiệu năng

| Host | n | Trung vị | Chậm nhất |
|---|---:|---:|---:|
| Yahoo | 24 | ~170 ms | 209 ms |
| FRED | 8 | ~500 ms | 4.706 ms |
| Frankfurter | 8 | ~720 ms | 1.366 ms |
| DBnomics | 8 | 1.690 ms | **11.799 ms** |
| LBMA | 2 | ~1.170 ms | 1.331 ms |

**Không host nào trả `X-RateLimit-*` hay `Retry-After`.** ETL phải tự giữ nhịp.

## 6. Chưa kiểm

Ngưỡng rate limit thật mọi nguồn (chủ đích không dò) · điều khoản Yahoo/LBMA/DBnomics/gold-api · con số rate limit công bố của FRED (trang tài liệu đọc được nhưng **không chứa số**) · Stooq · vnstock (chưa gọi) · `nso.gov.vn` · OECD SDMX cú pháp khoá · đồng/thép/than · ETag/`If-None-Match` · hành vi nhiều luồng.

## 7. 🔴 Điều khoản FRED — nay đọc được, và có điều cấm quan trọng

`fred.stlouisfed.org/legal` → `200`, 117.021 byte. Mục **"Prohibited Use"** áp cho **mọi** hình thức dùng. Các điểm ghi nhận *(diễn đạt lại, không chép nguyên văn)*:

1. Cấm **thu thập/trích xuất tự động** — nêu đích danh data mining, mirroring, robots, scraping — **trừ khi điều khoản áp dụng cho FRED API cho phép rõ ràng**.
2. Cấm **phân phối lại nội dung độc quyền của bên thứ ba** cho mục đích **thương mại** nếu chưa có văn bản đồng ý của chủ dữ liệu.
3. Cấm dùng dịch vụ/nội dung FRED **cho mục đích thương mại** nếu chưa có văn bản đồng ý của Ngân hàng.
4. Cấm dùng nội dung FRED để **phát triển hoặc huấn luyện phần mềm, hệ thống, hay mô hình học máy** — nêu đích danh mô hình ngôn ngữ lớn.
5. Cấm gỡ/che/sửa thông báo quyền sở hữu.
6. Cấm sửa hình ảnh trực quan do FRED tạo.
7. Xác nhận lại **ba mức bản quyền** mà `report-fred.md` §9 đã đo bằng API.

**Chưa đọc được:** con số rate limit chính thức.

> ⚠️ **Đây là việc của chủ dự án.** Báo cáo chỉ ghi cái quan sát được, không phân tích, không đề xuất việc pháp lý. Nhưng vì mục 3 và 4 chạm thẳng vào mô hình sản phẩm (phục vụ khách hàng cuối + chatbot AI), **khuyến nghị "lấy FRED" ở `report-fred.md` §13 phải được chủ dự án xem lại trước khi triển khai.**

## 8. Kiểm chứng độc lập của controller *(6 lời gọi, 2026-08-15)*

| Khẳng định | Kết quả |
|---|---|
| Frankfurter: 1 lời gọi đủ 6 cặp, ngày 2026-08-14 | ✅ **Đúng** — CAD 1,3875 · CHF 0,81179 · EUR 0,86453 · GBP 0,73874 · JPY 159,01 · SEK 9,5089 |
| DXY dựng lại = **99,6113** | ✅ **Trùng khít.** Controller tự tính lại từ số vừa lấy → **99,6113** |
| LBMA vàng: 14.662 điểm, 1968-04-01 → 2026-08-14 | ✅ **Đúng từng con số.** 913.134 byte, giá cuối 4.390,7 |

### 🔴 Một chỗ phải sửa — `fredgraph.csv` KHÔNG ổn định từ máy này

Agent đo 8/8 lời gọi `200`, trung vị ~500 ms, và kết luận host `fred.stlouisfed.org` "nay thông hoàn toàn".

Controller thử lại **3 lần liên tiếp**: **thất bại cả 3** — `HttpRequestException` sau 19,4 s, rồi `TaskCanceledException` sau 45 s × 2. Cùng lúc đó `api.stlouisfed.org` (host API, có khoá) trả `200` trong **440 ms**.

➜ Host `fred.stlouisfed.org` **chập chờn** từ mạng này, không phải "đã thông". Điều này khớp với `report-fred.md` §12 (agent trước gặp timeout 40 s / `403`).

**Hệ quả cho khuyến nghị 2 của agent** ("chuyển toàn bộ đường lấy FRED sang `fredgraph.csv` không khoá"): **không làm được nếu chỉ dựa vào nó**. Đường CSV là **tiện ích bổ sung**, không phải đường thay thế — ETL phải giữ đường API có khoá làm chính, hoặc chịu tỉ lệ hỏng cao.
