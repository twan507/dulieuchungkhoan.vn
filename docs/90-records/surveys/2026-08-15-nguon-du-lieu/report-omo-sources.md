# Nguồn OMO / tín phiếu NHNN có thể ETL — khảo sát 2026-08-15

**Trạng thái:** xong · **Lời gọi mạng:** 40/50 (agent) + 5 (controller kiểm chứng) · Mọi con số từ lời gọi thật ngày **2026-08-15**, trừ chỗ ghi rõ "chưa kiểm" / "suy đoán".

*(Agent khảo sát không ghi được file `.md` — controller ghi lại, kèm phần kiểm chứng độc lập ở §6.)*

## 0. Kết luận một dòng

**Không có nguồn nào vừa miễn phí, vừa ẩn danh, vừa cho chuỗi bơm/hút ròng theo ngày.** Ba đường đi được: (1) **xin WiFeed mở gói "Tiền tệ – Thị trường mở"** — đã đo được đúng schema cần, dự án đã là khách WiFeed; (2) **Vietstock Macro API với một tài khoản Free** — endpoint JSON đã đo chính xác, gói Free cho 60 ngày; (3) **crawl sbv.gov.vn hằng ngày** — miễn phí, gốc, parse được, nhưng **chỉ có phiên mới nhất, không backfill được**.

## 1. Cần lấy đúng trường nào

| Trường | Bắt buộc? | Ghi chú |
|---|---|---|
| `ngay` (ngày đấu thầu) | ✅ | khoá thời gian |
| `cong_cu` — `OMO_reverse_repo` \| `SBV_bills` | ✅ | bơm bằng mua kỳ hạn, hút bằng bán hẳn (tín phiếu) |
| `ky_han_ngay` | ✅ | 7/14/21/28/35/56/63/91/140 — cần để **suy ra lịch đáo hạn** |
| `kl_trung_thau` (tỷ VND) | ✅ | lượng bơm/hút gộp trong phiên |
| `ls_trung_thau` (%/năm) | ✅ | giá của thanh khoản |
| `kl_dao_han` (tỷ VND) | ✅ | **thiếu cái này là không tính được ròng** |
| `bom_hut_rong` = phát hành − đáo hạn | ✅ | thứ skill cần cộng dồn |
| `dang_luu_hanh` (OMO / Bills outstanding) | ⭕ nên có | mức tồn, đọc xu hướng nhanh hơn cộng dồn tay |
| `so_tv_tham_gia` / `so_tv_trung_thau` | ⭕ | tín hiệu độ căng hệ thống |

⚠️ Theo cảnh báo `macro-money-creation.md:178`, thứ cần lưu là **chuỗi ròng theo ngày để cộng dồn**, không phải con số từng phiên. Nghĩa là **`kl_dao_han` là trường phân định**: nguồn nào chỉ có "khối lượng trúng thầu" thì chưa đủ, phải tự dựng lịch đáo hạn từ `ky_han_ngay`.

## 2. Xếp hạng ứng viên

| # | Nguồn | ETL được? | Độ trễ | Lịch sử | Rủi ro vỡ | Chặn/khoá |
|---|---|---|---|---|---|---|
| **1** | **WiFeed / WiGroup — gói "Tiền tệ"** | ✅ (khi có key) — đủ trường kể cả đáo hạn & lưu hành | ngày *(chưa kiểm)* | *(chưa kiểm)* | thấp — API thương mại | cần mở gói; **chưa có key** |
| **2** | **Vietstock Macro API** (`/Macro/GetReportDataByIDs`) | ✅ JSON, endpoint + payload đã đo | ngày (T+0) | Free = **60 ngày**; sâu hơn = trả tiền | trung bình — API nội bộ web, anti-forgery token | **cần đăng nhập** |
| **3** | **SBV `sbv.gov.vn`** | ⚠️ được, nhưng **chỉ phiên mới nhất** | T+0 | **0 ngày** — không có kho lưu | cao — HTML viết tay | xem §6 — nhẹ hơn agent mô tả |
| 4 | FiinPro X | ✅ *(theo tài liệu)* | *(chưa kiểm)* | *(chưa kiểm)* | — | sản phẩm trả tiền **khác** FiinTrade dự án đang dùng |
| — | FiinTrade (BVSC white-label) | ❌ không có OMO | — | — | — | — |
| — | VBMA | ❌ trang daily-highlight không có chữ OMO nào | — | — | — | — |
| — | HNX | ❌ chỉ TPCP/Kho bạc | — | — | — | — |
| — | CEIC | ❌ bảng `VN.Z004` **năm**, dừng 2017 | — | 2012–2017 | — | trả tiền |
| — | DBnomics / IMF / BIS | ❌ 0 kết quả OMO Việt Nam | — | — | — | — |
| — | Báo điện tử | ❌ văn bản, không phải chuỗi số | — | — | — | — |

## 3. Bằng chứng từng hướng

### 3.1 ⭐ WiFeed / WiGroup — gói "Tiền tệ" (hạng 1)

`https://www.wigroup.vn/danh-muc/kinh-te-vi-mo/tien-te` mô tả nguyên văn: *"SBV Bills: … khối lượng phát hành, lãi suất phát hành, khối lượng đáo hạn, Bills đang lưu hành"*, *"OMO - Reverse Repo: … khối lượng phát hành, lãi suất phát hành, khối lượng đáo hạn, OMO đang lưu hành"*, *"Bơm hút ròng: … tổng khối lượng tiền được bơm vào hoặc hút ra khỏi hệ thống…"*.

Trang nhúng **biểu đồ Datawrapper công khai**; tải thẳng dataset:

```
GET https://datawrapper.dwcdn.net/TWL5q/4/dataset.csv → 200, 4.600 byte, 74 dòng × 13 cột
```

Đây là **mẫu marketing tĩnh** (10 ngày, 02–15/08/2024), không phải feed sống — nhưng là **đặc tả schema chính xác**:

```
SBV BILLS        → Khối lượng phát hành / Lãi suất phát hành / Khối lượng đáo hạn / Bills đang lưu hành
OMO-REVERSE REPO → Khối lượng phát hành / Lãi suất phát hành / Khối lượng đáo hạn / Omo đang lưu hành
   (mỗi nhóm tách theo kỳ hạn 7 / 14 / 21 / 28 / 56 / 91 / 140 ngày)
BƠM HÚT RÒNG     → SBV-Bills · OMO · Bơm/hút ròng của NHNN · Tổng lưu hành
Đơn vị: Tỷ VND (khối lượng), % (lãi suất). Cột = ngày.
```

**Đúng bằng** danh sách §1, kể cả `kl_dao_han` và `dang_luu_hanh` — thứ SBV không cho. Dự án **đã là khách WiFeed** (`wichart.md §1`), nên đây là mở thêm gói trong quan hệ đã có, không dựng phụ thuộc mới.

**Chưa kiểm:** endpoint thật, tên key, độ sâu lịch sử, độ trễ, giá (không có key nên không gọi được).

**Đo phụ có ích:** namespace đang dùng không có *khối lượng* OMO (khớp kết quả 11 key → 500 trước đây), **nhưng** trang white-label `data.vietnambiz.vn/currency-interest-rate` (SSR, nguồn ghi rõ WiFeed.vn) có hai chuỗi ngày:

```json
{"title":"Lãi suất OMO","time_type":1,"ngay":"Ngày 14/08/2026","value":4.5,"time_update":"Hàng ngày"}
{"title":"Lãi suất tín phiếu","time_type":1,"ngay":"Ngày 16/07/2025","value":3.4,"time_update":"Hàng ngày"}
```

→ **lãi suất** OMO/tín phiếu đã nằm trong vùng có giấy phép, chỉ thiếu **khối lượng**. Đáng hỏi WiFeed tên key hai chuỗi này. (`GET api.wichart.vn/vietnambiz/currency-interest-rate` → **404**.)

### 3.2 ⭐ Vietstock Macro API (hạng 2)

Trang: `finance.vietstock.vn/vi-mo/du-lieu/ket-qua-dau-thau-thi-truong-mo-70` (`CategoryID=70`). Đọc bundle `/bundles/macro-v2/jsx` ra endpoint + payload:

```
POST https://finance.vietstock.vn/Macro/GetReportDataByIDs
X-Requested-With: XMLHttpRequest
Referer: https://finance.vietstock.vn/vi-mo/du-lieu/ket-qua-dau-thau-thi-truong-mo-70

termTypeID=0&subTermTypeID=&fromDate=2026-06-01&toDate=2026-08-15
&type=CATEGORY&listID[]=70&__RequestVerificationToken=<token>
```

Token lấy từ `<form id=__CHART_AjaxAntiForgeryForm>` trong HTML (thuộc tính **không có dấu nháy** — regex phải chịu được `value=xxx`), gắn với cookie phiên.

Gọi ẩn danh (đo 3 lần, cat 70 / 54 / 66) đều trả:
```json
{"errorModel":{"ErrorCode":"RequestUpgradeAccount_Permission","ErrorMessage":"Yêu cầu nâng cấp tài khoản","IsLimitData":true}}
```

Trang tự khai bảng quyền cho gói **Free**: `Category-70_TermType-0_Feature-ViewData = true`, `Feature-DataTimeLimit = {"days":"60"}` → **tài khoản Free = 60 ngày gần nhất**.

Trường có (từ từ điển i18n nhúng): `AuctionDay` · `Type` (`TreasureBillType1` Mua kỳ hạn / `2` Bán kỳ hạn / `3` Bán hẳn) · `TypeOfTerm` · `NumParticipant`/`NumWinBid` · `VolumeWinbid` · `WinBid` · **`TotalVolPumpWithdrawOMO` "Giá trị bơm ròng (tỷ đồng)"** · `PumpOMO`/`WithdrawOMO` · `OMOChartTitle` "Diễn biến bơm hút ròng nghiệp vụ OMO theo ngày". → **Vietstock có sẵn chuỗi bơm ròng, không phải tự tính.** Category liên quan: **70** (chi tiết phiên) và **54** (tổng hợp).

Rủi ro: API nội bộ web, phải giữ phiên đăng nhập trong ETL. Trang cũ `/du-lieu-vi-mo/69-70/thi-truong-mo.htm` **đã chết** (→ `/Error/Index`) — bằng chứng họ có đổi cấu trúc.

*Quan sát pháp lý (chỉ ghi):* trang khai gói `Free`/`PackageId:3`, cơ chế `RequestUpgradeAccount_Permission`; liên hệ `data@vietstock.vn`. Agent **không lập tài khoản** — chủ dự án tự xử lý.

### 3.3 SBV — khó ở chỗ nào, vượt được tới đâu (hạng 3)

URL thật: `https://sbv.gov.vn/vi/nghiệp-vụ-thị-trường-mở` *(dạng mã hoá: `/vi/nghi%E1%BB%87p-v%E1%BB%A5-th%E1%BB%8B-tr%C6%B0%E1%BB%9Dng-m%E1%BB%9F`)*

**Bốn vấn đề cụ thể**, không phải "khó chung chung":

1. **WAF chặn theo dấu vân tay client.** Python `requests` với UA mặc định → `200` nhưng body **246 byte**: `<title>Request Rejected</title> … Your support ID is: …`. Gửi đủ header trình duyệt → `200`, ~414 KB. ⚠️ **Controller kiểm lại thấy nhẹ hơn** — xem §6.
2. 🔴 **Chỉ phiên mới nhất, không kho lưu.** Portlet Liferay Asset Publisher hiển thị **đúng một bài**. Không tham số ngày, không phân trang, không link category. Tìm kiếm nội bộ bị WAF chặn; kho tín phiếu `/-/categories/94000` chỉ có một thông báo đứng yên; bản EN không có bảng nào. → **Backfill từ SBV là không làm được.** *(Controller kiểm độc lập, xác nhận — §6.)*
3. **Thiếu trường then chốt.** Bảng chỉ 4 cột: `Loại hình giao dịch` · `Số thành viên tham gia/trúng thầu` · `Khối lượng trúng thầu (Tỷ đồng)` · `Lãi suất trúng thầu (%/năm)`. **Không có đáo hạn, không có ròng, không có lưu hành.** Vượt được một phần: kỳ hạn nằm trong nhãn dòng nên tự dựng được lịch đáo hạn — nhưng chỉ đúng **sau khi tích luỹ đủ ~140 ngày tự crawl**, và sai nếu bỏ lỡ một phiên.
4. **HTML viết tay.** Class tự chế `ls01-table`/`ls01-group`/`ls01-total` kèm `<style>` nội tuyến ngay trong nội dung bài — biên tập viên dán vào, đổi lúc nào cũng được. Số định dạng Việt (`6.307,47`). Ngày nằm trong **tiêu đề bài** `(14.08.26)`.

Đã parse thật → `omo-raw/sbv-omo-parsed-2026-08-14.csv`, nhóm "Mua kỳ hạn", tổng **10.894,10 tỷ**:

| ngày | loại hình | kỳ hạn | TV tham gia/trúng | KL trúng thầu (tỷ) | LS (%) |
|---|---|---|---|---|---|
| 14.08.26 | Mua kỳ hạn | 7 | 4/4 | 6.307,47 | 4,5 |
| 14.08.26 | Mua kỳ hạn | 35 | 4/4 | 3.466,54 | 4,5 |
| 14.08.26 | Mua kỳ hạn | 63 | 1/1 | 210,17 | 4,5 |
| 14.08.26 | Mua kỳ hạn | 91 | 3/3 | 909,92 | 4,5 |

*(Suy đoán, chưa kiểm: hôm nào NHNN phát hành tín phiếu thì cùng bảng sẽ có thêm nhóm "Bán hẳn" — vì Vietstock và WiGroup đều mô tả ba nhóm Mua kỳ hạn / Bán kỳ hạn / Bán hẳn trên cùng bộ số gốc. Ngày đo chỉ có "Mua kỳ hạn".)*

### 3.4 FiinTrade / FiinPro X

- **FiinTrade (bản BVSC dự án dùng): không có OMO — quét toàn bộ mã.** Bundle `main.876ed868.chunk.js` (3.054.309 byte): `ChartEconomy` 7, `Economy` 74, `OpenMarket` 13 — **nhưng cả 13 lần `OpenMarket` đều là `secondsToOpenMarket`/`setTimeToOpenMarket`** (đồng hồ đếm ngược giờ mở cửa sàn), và lần duy nhất khớp `OMO` là chuỗi con trong `AUTOMOBILE_L4`. `MoneyMarket`/`Interbank`: 0. → Chắc chắn hơn hẳn so với chỉ đọc `GetAllChartEconomy`.
- **FiinPro X (sản phẩm trả tiền khác) thì có.** `docs.fiinpro.com/kinh-te-vi-mo/chinh-sach-tien-te/thi-truong-mo` liệt "Tín phiếu Sell Outright (Bán hẳn), Reverse Repo (Mua kỳ hạn)", "Bơm hút ròng", "Khối lượng lưu hành", kỳ "Hàng ngày, hàng tuần, hàng tháng". Tài liệu giao diện — **không nói gì về API**.

### 3.5 Các hướng đã loại, kèm bằng chứng

| Hướng | Đo được gì |
|---|---|
| **VBMA** | `/vi/market-data/daily-highlight` (33.682 byte): `OMO`=0, `thị trường mở`=0, `tín phiếu`=0, `bơm`=0, `hút`=0 |
| **HNX** | Dữ liệu là đấu thầu **TPCP của Kho bạc**. Tín phiếu NHNN không đấu thầu qua HNX |
| **CEIC** | `ceicdata.com/en/vietnam/open-market-operation` có bảng `VN.Z004`, nhưng series đều **"Yearly", 2012–2017** |
| **DBnomics/IMF/BIS** | `api.db.nomics.world/v22/search?q=Vietnam+open+market+operations` → `num_found = 0`; `Vietnam monetary` → 37 kết quả toàn IMF WEO (năm) |
| **WiChart namespace đang có** | `api.wichart.vn/vietnambiz/currency-interest-rate` → **404**. Khớp 11 key → 500 |
| **Vietstock trang cũ** | `/du-lieu-vi-mo/69-70/thi-truong-mo.htm` → `/Error/Index` |
| **Báo điện tử** | Có số **tuần** nhưng là văn xuôi → chỉ dùng đối chiếu |

## 4. Khuyến nghị triển khai

1. **Hỏi WiFeed gói "Tiền tệ – Thị trường mở"** — kèm schema §3.1 và câu hỏi tên key cho "Lãi suất OMO"/"Lãi suất tín phiếu" đã thấy trong white-label. Rẻ nhất về kiến trúc: cùng nhà cung cấp, cùng cơ chế, cùng hợp đồng dữ liệu.
2. **Trong lúc chờ: bật crawler SBV hằng ngày ngay.** SBV **không backfill được**, mỗi ngày không crawl là một ngày mất vĩnh viễn. ~30 dòng code, 1 lời gọi/ngày. Ba điều bắt buộc: gửi đủ header trình duyệt; lấy ngày từ **tiêu đề bài** `(dd.mm.yy)` chứ không lấy ngày hệ thống; lưu **cả HTML gốc** để parse lại khi markup đổi.
3. **Backfill 60 ngày bằng tài khoản Vietstock Free** (chủ dự án tự lập), qua endpoint §3.2. Vietstock cho sẵn `Giá trị bơm ròng` → vừa lấp lịch sử vừa **kiểm chứng chéo** con số tự tính từ SBV.

**Thoái lui rẻ nhất nếu (1) và (3) đều hỏng:** SBV-only, tự dựng lịch đáo hạn từ `ky_han_ngay`; chấp nhận **không có ròng đáng tin trong ~140 ngày đầu**, giai đoạn đó chỉ dùng `kl_trung_thau` + `ls_trung_thau` thô.

**Không khuyến nghị:** parse PDF bản tin tiền tệ của công ty chứng khoán (SSI/VCBS/MBS) — không đo được trang dữ liệu dạng bảng nào của họ, chi phí parse cao hơn hẳn.

## 5. Mẫu thô — `scratchpad/omo-raw/` (28 file, 8,6 MB)

Đáng chú ý: `sbv-omo-parsed-2026-08-14.csv` (bảng SBV đã parse) · `dw-TWL5q-dataset.csv` (schema WiGroup) · `vietstock-macro-v2.jsx.js` (nguồn rút endpoint + bảng quyền) · `fiinapp-main.js` (bằng chứng FiinTrade không có OMO).

## 5b. 🔴 Đường Datawrapper — ĐÃ ĐO, KHÔNG DÙNG ĐƯỢC

**Bối cảnh:** chủ dự án gọi hỏi WiGroup, được trả lời — *"nếu lấy được thì có thể dùng, họ có thể thêm điều khoản, nhưng họ không sửa lại API cung cấp nữa."* Tức **rào pháp lý đã mở**, câu hỏi còn lại thuần kỹ thuật: biểu đồ Datawrapper nhúng trên trang WiGroup có phải **feed sống** không?

**Đo 2026-08-15 — không phải.**

Trang `wigroup.vn/danh-muc/kinh-te-vi-mo/tien-te` nhúng **hai** biểu đồ Datawrapper:

| Chart | Nội dung | Phủ dữ liệu | Số cột ngày |
|---|---|---|---|
| `TWL5q/4` | SBV Bills · OMO Reverse Repo · Bơm hút ròng | **02-08-2024 → 15-08-2024** | 10 ngày |
| `qutcZ/2` | Cung tiền M2 · Tín dụng · Huy động | **04-2023 → 01-2024** | 10 tháng |

**Ba bằng chứng cho thấy đây là ảnh chụp tĩnh, không phải feed:**

1. **`/4` và `/2` là phiên bản mới nhất.** Dò `TWL5q` các bản 5, 6, 7, 8, 10, 15, 20 → **`404` toàn bộ**. Dò `qutcZ` bản 3, 4, 5, 8 → **`404` toàn bộ**. Datawrapper tăng số phiên bản mỗi lần xuất bản lại, nên không có bản cao hơn nghĩa là **chưa từng xuất bản lại**.
2. **Không có `externalData`.** Metadata của cả hai chart **không khai nguồn dữ liệu ngoài** → số liệu được **dán tay** vào Datawrapper, không nối vào hệ thống nào.
3. **Nội dung tự tố cáo.** Dữ liệu OMO dừng ở **15/08/2024** — đúng **hai năm** trước ngày đo. Dữ liệu cung tiền còn cũ hơn, dừng **01/2024**.

**Kết luận:** đây là **mẫu marketing** để khách nhìn thấy schema, không phải kênh dữ liệu. "Lấy được thì dùng" — nhưng **không có gì sống để lấy**. Giá trị duy nhất của nó vẫn đúng như §3.1: nó **đặc tả chính xác schema** mà WiFeed có, chứ không cung cấp dữ liệu.

**Hệ quả cho xếp hạng §2:** WiGroup nói **không sửa/không cung cấp API mới** → hạng 1 (WiFeed gói "Tiền tệ") **đóng lại về mặt kỹ thuật**, trừ khi họ mở đúng gói đã có sẵn qua kênh API hiện hành. Ba đường rút còn **hai**:

| # mới | Nguồn | Trạng thái |
|---|---|---|
| **1** | **Vietstock Macro API** | Còn nguyên. Free 60 ngày; có sẵn `TotalVolPumpWithdrawOMO`; cần đăng nhập |
| **2** | **Crawl SBV hằng ngày** | Còn nguyên. Không backfill; thiếu đáo hạn/ròng nên phải tự dựng lịch đáo hạn |

→ **Vietstock giờ là đường chính, không còn là phương án 2.** Và vì SBV không backfill được, việc bật crawler SBV **càng gấp hơn** so với đánh giá ở §4.

---

## 6. Kiểm chứng độc lập của controller *(5 lời gọi, 2026-08-15)*

| Khẳng định của agent | Kết quả kiểm |
|---|---|
| Trang SBV chứa bảng phiên 14/08/2026 | ✅ **Đúng.** Tải lại được 414.559 byte; tiêu đề mang ngày `14.08.26`; có `Mua kỳ hạn`, `Khối lượng trúng thầu`, `Lãi suất trúng thầu`, và đúng giá trị `6.307,47` |
| Bảng **thiếu** đáo hạn / bơm ròng | ✅ **Đúng.** Tìm chuỗi `đáo hạn` và `bơm ròng` trong toàn trang → **không có** |
| **Không backfill được** | ✅ **Đúng.** Toàn trang chỉ có **đúng một** tiêu đề `KẾT QUẢ ĐẤU THẦU THỊ TRƯỜNG MỞ (14.08.26)`; không tìm thấy dấu hiệu phân trang (`page=`, `cur=`, `delta=`, "Trang sau"…); 4 link trông giống liên quan đều dẫn sang chủ đề khác (đấu thầu đầu tư, kết quả điều tra…) |
| Tổng "Mua kỳ hạn" = 10.894,10 tỷ | ✅ 6.307,47 + 3.466,54 + 210,17 + 909,92 = **10.894,10** |

### ⚠️ Một chỗ agent nói quá — WAF nhẹ hơn mô tả

Agent viết *"WAF chặn client trần"*. Controller gọi bằng **PowerShell `Invoke-WebRequest` không thêm header nào** → **`200`, 414.534 byte, HTML hợp lệ đầy đủ**, không hề bị chặn.

→ WAF chặn theo **dấu vân tay client cụ thể** (nhiều khả năng nhắm `python-requests`), **không phải chặn mọi client không có header trình duyệt**. Rủi ro của hướng SBV vì thế **thấp hơn** bảng xếp hạng §2 ghi. Vẫn nên gửi đủ header trình duyệt cho chắc, nhưng đừng coi đây là rào cản lớn.

*(Chưa kiểm: WAF có siết theo tần suất không — mới gọi vài lần, chủ đích không dò.)*
