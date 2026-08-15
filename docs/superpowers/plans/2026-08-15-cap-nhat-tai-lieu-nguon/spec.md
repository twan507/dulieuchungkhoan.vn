# Spec — Cập nhật tài liệu nguồn theo khảo sát 2026-08-15

## 1. Bối cảnh

Ngày 2026-08-15 dự án chạy một đợt khảo sát nguồn dữ liệu: **9 nguồn, ~400 lời gọi thật**. Toàn bộ báo cáo đã lưu ở [`docs/superpowers/surveys/2026-08-15-nguon-du-lieu/`](../../surveys/2026-08-15-nguon-du-lieu/README.md) *(commit `d74bbc9`)*.

Tài liệu sống trong `docs/10-sources/` **chưa phản ánh gì** từ đợt này, và đang chứa **hai khẳng định sai** đã được chứng minh bằng đo đạc.

## 2. Mục tiêu

Đưa `docs/` về đúng trạng thái đã đo, gồm bốn việc:

1. **Sửa khẳng định sai** trong tài liệu hiện có
2. **Bổ sung dữ liệu mới của nguồn cũ** — phái sinh, ETF/quỹ
3. **Lập tài liệu cho 6 nguồn mới** — SBV · FRED · Frankfurter · Yahoo · LBMA · Binance
4. **Đồng bộ tầng tổng quan** — README các cấp, kiến trúc, lộ trình, sổ quyết định

## 3. Ngoài phạm vi

- **Không viết code ETL.** Giai đoạn này chỉ tài liệu.
- **Không sửa `20-design/market-field-selection.md`** — sinh tự động từ `gen_field_selection.py`, phải chạy generator chứ không sửa tay.
- **Không đo lại gì.** Mọi con số lấy từ báo cáo khảo sát. Cần số chưa có thì ghi "chưa kiểm", **không tự đo**.
- **Không đụng `30-skills/`** và `docs/superpowers/surveys/`.

## 4. Ràng buộc cứng

### 4.1 Luật vàng của repo — tài liệu sống phải tường minh

> **Không trỏ về ADR.** `00-overview/decisions/` chỉ để tra cứu lịch sử. Mọi tài liệu sống phải ghi tường minh. Phép thử: **xoá cả thư mục `decisions/` thì chỉ được phép mất lịch sử, không được mất tri thức vận hành.**

### 4.2 Tầng reference chỉ sửa khi đo lại

`10-sources/` là tầng **reference** — chép sự thật đo được, không diễn giải. Mọi con số **phải kèm ngày đo**. Chưa đo thì ghi **"chưa kiểm"**, không đoán.

### 4.3 Đặt tên tiếng Anh

Theo ADR 0005: tên file và thư mục dùng tiếng Anh, nội dung tiếng Việt.

### 4.4 Giữ nguyên giọng tài liệu hiện có

Bảng nhiều, câu ngắn, số liệu kèm ngày đo, bẫy đánh dấu 🔴 (nghiêm trọng) và ⚠️ (cần biết). Đọc một file `market/` bất kỳ trước khi viết file mới.

## 5. Cấu trúc thư mục — quyết định

`10-sources/` hiện có ba nhóm: `market/` (thị trường VN) · `macro/` (vĩ mô VN) · `news/` (tin).

**Thêm nhóm thứ tư: `global/` cho nguồn quốc tế.**

| Thư mục | Chứa | Nguồn |
|---|---|---|
| `market/` | Thị trường Việt Nam | BVSC · FiinTrade |
| `macro/` | Vĩ mô Việt Nam | WiChart · **SBV (mới)** |
| **`global/`** | **Nguồn quốc tế (mới)** | **FRED · Frankfurter · Yahoo · LBMA · Binance** |
| `news/` | Tin tức | 8 báo điện tử |

**Lý do:** Yahoo cho chỉ số cổ phiếu và Binance cho crypto **không phải vĩ mô**, nên nhét vào `macro/` là sai nghĩa. Tách theo *phạm vi địa lý và loại thị trường* rõ hơn tách theo *loại chỉ tiêu*.

## 6. Yêu cầu chi tiết

### 6.1 🔴 Sửa hai khẳng định sai

| Chỗ | Đang ghi | Sự thật |
|---|---|---|
| `market/01-bvsc-rest.md:72` | *"Không chứa phái sinh. BVSC **không cung cấp dữ liệu phái sinh qua bất kỳ endpoint public nào**."* | `/datafeed/instruments` trả **14 hợp đồng, 62 trường, có `openInterest`** |
| `macro/wichart.md:357` | `dau_wti` — cờ *"lệch 1,3%"* | Đo 115 ngày: lệch **2,85%** so với FRED. **Nhưng** so với chuẩn đúng (giá tương lai WTI của Investing) thì chỉ **0,50%** — vì `dau_wti` là **giá tương lai**, không phải giao ngay |

Cả hai chỗ phải ghi **cả lý do sai cũ**, vì đó là tri thức phương pháp:
- Khẳng định phái sinh sai vì **suy từ một endpoint (`/quotes`) ra toàn nguồn**.
- Cờ dầu sai vì **chấm một điểm thay vì so chuỗi**, và vì **so nhầm chuẩn** (giao ngay vs tương lai).

### 6.2 Bổ sung phái sinh

Vào `market/01-bvsc-rest.md` (endpoint `/datafeed/instruments`), `market/02-bvsc-tvcharts.md` (UDF), `market/09-fiin-market-price.md` (`getPriceData` nhận `VN30F1M/2M/1Q/2Q`), `market/00-conventions.md` (bẫy).

Phải có: 14 hợp đồng (VN30F 4 · VN100F 4 · TPCP 5/10 năm 6) · lược đồ trường riêng phái sinh · **bẫy OI trễ một phiên** (kiểm 4/4) · 4 bẫy kiểu dữ liệu · phiên mở **08:45** · backfill 2.233 phiên từ 31/08/2017 · giới hạn UDF (chỉ 2 khung, `/search` 404, body rỗng 0 byte).

### 6.3 Bổ sung ETF/quỹ

31 mã `StockType=3` · trường `FundType`/`ListedShare`/`TotalListingQtty`/room ngoại · **`iNav` + `iIndex` của FiinTrade, phủ 6/31 mã**, và **chỉ 2 mã có thanh khoản thật** — phải ghi rõ giới hạn này, không được để người đọc tưởng dùng được cả 31.

### 6.4 Sáu nguồn mới

Mỗi nguồn một file trong `global/` (trừ SBV vào `macro/`), theo đúng khuôn `market/`: base URL · xác thực · tham số · lược đồ response · bẫy · độ phủ và hiệu năng · giới hạn.

| File | Nguồn | Điểm bắt buộc phải có |
|---|---|---|
| `macro/sbv-omo.md` | SBV | **Không backfill được** — mỗi ngày không crawl là mất vĩnh viễn · thiếu cột đáo hạn và ròng · HTML viết tay · WAF chặn theo vân tay client *(PowerShell qua được, `python-requests` không)* |
| `global/fred.md` | FRED | 15 series · **vá hồi tố** (PAYEMS 3 giá trị cho một tháng) · `"."` là giá trị thiếu · `file_type` mặc định XML · **chỉ số đô trễ 3–9 ngày vì bản H.10 ra theo tuần** · giấy phép chủ dự án đã xử lý xong |
| `global/fx.md` | Frankfurter (ECB) | 6 cặp dựng DXY + công thức + sai số **0,18%** · fixing **14:15 CET ≠ giá đóng cửa** · lịch nghỉ hai bên không trùng · v2 mặc định trộn 84 NHTW, **bắt buộc `providers=ECB`** |
| `global/yahoo.md` | Yahoo | **36 chỉ số/21 nước** · `^TNX` lệch FRED **0,009 điểm %** · 3 bẫy: `period1=0` cắt ở 1970, `range=max` trả nến tháng, `404` không nghĩa là mã chết · **chết im lặng** nhận biết bằng `quoteType=ALTSYMBOL` · **gọi thẳng REST, không dùng thư viện** |
| `global/commodities.md` | LBMA | Vàng/bạc fixing từ **1968**, 14.662 điểm một lời gọi · fixing 15:00 London |
| `global/crypto.md` | Binance | PAXG (vàng 24/7, premium **−0,05%**) + 10 đồng lớn · giá theo **USDT không phải USD** (chênh neo <0,15%) · `/klines` mảng vị trí, số dạng chuỗi |

### 6.5 🔴 Bẫy chung phải ghi vào `00-conventions.md`

| Bẫy | Nội dung |
|---|---|
| **Múi giờ WiChart** | Epoch là **nửa đêm giờ Việt Nam**. Parse UTC làm lệch cả chuỗi một ngày — đã tạo ra một kết luận sai hoàn toàn trong đợt này |
| **`StockType` không nhất quán** | Cùng mã trái phiếu: `/quotes` báo `12`, `/datafeed/instruments` báo `1`. Không dùng làm khoá phân loại chung |
| **Hai endpoint BVSC lệch độ phủ** | `/quotes` 2.534 vs `/datafeed/instruments` 2.001. **Không endpoint nào là danh mục chuẩn duy nhất** |
| **Giao ngay vs tương lai** | Chênh ~2% giữa FRED và WiChart/Yahoo là **backwardation**, không phải sai số. Xác nhận bằng cấu trúc kỳ hạn: Sep 82,40 · Oct 81,47 · Nov 80,10 · Dec 78,49 |

### 6.6 Danh sách "Ngoài phạm vi" — viết lại thành ba loại có lý do

Hiện chỉ liệt tên mục không kèm lý do, và chính vì thế mà đợt khảo sát đã **tốn công mở lại ba mục vốn bị loại có chủ đích**.

| Loại | Mục |
|---|---|
| **Loại có chủ đích** — có dữ liệu nhưng không phục vụ phân tích | Chứng quyền (342 mã) · Lô lẻ (1.890 mã) · Trái phiếu (187 mã) |
| **Đã có đường khác** | Realtime FiinTrade *(dùng của BVSC)* · Luồng cần đăng nhập |
| **Đã kiểm — không nguồn nào có** | NAV quỹ mở |

### 6.7 Đồng bộ tầng tổng quan

`docs/README.md` · `docs/10-sources/README.md` *(mục 2, 3, changelog bản 5.0)* · `00-overview/architecture.md` *(L0)* · `00-overview/roadmap.md` · `README.md` gốc.

### 6.8 ADR mới

`00-overview/decisions/0006-source-selection-2026-08-15.md` — ghi **quyết định và lý do**: chốt SBV thay Vietstock · giữ WiChart cho dầu · lưu **cả hai** loại giá dầu · Frankfurter chính/Yahoo dự phòng · Yahoo chính cho chỉ số quốc tế thay FiinTrade · bỏ thư viện yfinance · loại 4 khối có chủ đích.

⚠️ ADR **chỉ ghi lịch sử**. Mọi tri thức vận hành phải nằm ở tầng sống — xem §4.1.

### 6.9 Việc còn treo

`viec-con-treo.md` trong thư mục khảo sát đã liệt đầy đủ. Đưa các mục **ảnh hưởng thiết kế** vào `roadmap.md §5`, nổi bật nhất: **realtime phái sinh chưa đo được, phải đo trong phiên, thứ Hai 17/08 khung 08:45–15:00**.

## 7. Nghiệm thu

1. `grep -rn "không cung cấp dữ liệu phái sinh" docs/` → **rỗng**
2. Mọi liên kết nội bộ trong `docs/` trỏ tới file có thật → **0 liên kết chết**
3. Mọi mục lục khớp tiêu đề thật trong file → **0 lệch**
4. Không file nào trong `10-sources/` chứa số không kèm ngày đo hoặc nhãn "chưa kiểm"
5. **Phép thử luật vàng:** xoá thử `00-overview/decisions/` → không tài liệu sống nào mất tri thức vận hành
6. Sáu file nguồn mới tồn tại và được liên kết từ `10-sources/README.md`

## 8. Rủi ro đã biết

| Rủi ro | Cách chặn |
|---|---|
| Chép nhầm số từ báo cáo | Mỗi task chỉ đọc **báo cáo của đúng nguồn mình viết**, không đọc chéo |
| Ghi số mà không kèm ngày đo | Nghiệm thu 4 |
| Tạo liên kết chết khi thêm thư mục `global/` | Nghiệm thu 2 |
| Vi phạm luật vàng — nhét tri thức vào ADR | Nghiệm thu 5 |
| Nhiều task cùng sửa `10-sources/README.md` | Gom mọi thay đổi README vào **một task cuối** |
