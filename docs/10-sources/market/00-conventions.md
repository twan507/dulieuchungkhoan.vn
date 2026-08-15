# 00 — Quy ước chung

> **Đọc hết file này trước khi triển khai bất kỳ endpoint nào.** Phần lớn lỗi khi tích hợp hệ thống này không đến từ endpoint riêng lẻ mà từ các quy ước chung và các hành vi bất thường mô tả ở đây.

---

## 1. Máy chủ (Base URL)

| Ký hiệu | Base URL | Chủ sở hữu | Dùng cho |
|---|---|---|---|
| `BVSC` | `https://online.bvsc.com.vn` | BVSC | Danh mục mã, snapshot, chỉ số, sổ lệnh khớp |
| `TVC` | `https://apis.bvsc.com.vn/tvcharts-1.0` | BVSC | Biểu đồ lịch sử (TradingView UDF) |
| `FIIN_CORE` | `https://wlgw-core.fiintrade.vn` | FiinGroup | Danh bạ doanh nghiệp, cây ngành |
| `FIIN_FUND` | `https://wlgw-fundamental.fiintrade.vn` | FiinGroup | Hồ sơ, BCTC, chỉ số tài chính |
| `FIIN_MARKET` | `https://wlgw-market.fiintrade.vn` | FiinGroup | Dòng tiền, lịch sự kiện, thị trường |
| `FIIN_TECH` | `https://wlgw-technical.fiintrade.vn` | FiinGroup | Giá lịch sử |
| `FIIN_STRAT` | `https://wlgw-strategy.fiintrade.vn` | FiinGroup | Chấm điểm, xếp hạng |
| `FIIN_TOOLS` | `https://wlgw-tools.fiintrade.vn` | FiinGroup | Định giá, bộ lọc |

---

## 2. Xác thực và Header

Không có token, không có API key, không có cookie. Cơ chế kiểm soát truy cập duy nhất là header `Origin`.

| Nhóm host | Header bắt buộc |
|---|---|
| `*.fiintrade.vn` | `Origin: https://fiinapp.bvsc.com.vn` |
| `online.bvsc.com.vn` | Không bắt buộc *(gửi `Origin: https://online.bvsc.com.vn` để nhất quán)* |
| `apis.bvsc.com.vn` | Không bắt buộc |

Thiếu `Origin` khi gọi FiinTrade → `HTTP 403`, body rỗng.

```bash
curl -H "Origin: https://fiinapp.bvsc.com.vn" \
  "https://wlgw-fundamental.fiintrade.vn/Snapshot/GetSnapshot?OrganCode=BID&language=vi"
```

**Hệ quả khi triển khai:** vì gate nằm ở `Origin`, mọi lời gọi phải xuất phát từ **backend BVSC** (proxy) chứ không phải từ trình duyệt người dùng — trình duyệt sẽ tự đặt `Origin` theo domain thật của trang và bị chặn.

---

## 3. Tham số chung

| Tham số | Kiểu | Giá trị | Ghi chú |
|---|---|---|---|
| `language` | string | `vi` \| `en` | Áp dụng cho **toàn bộ** endpoint FiinTrade. Ảnh hưởng tới các trường tên tiếng Việt (`icbName`, `rateIndicatorName`, `issueMethodName`…). Không ảnh hưởng tới dữ liệu số |
| `Page` | integer | ≥ 1 | Trang, bắt đầu từ 1 |
| `PageSize` | integer | tuỳ endpoint | ⚠️ Một số endpoint có whitelist cứng — xem Bẫy 4 |

---

## 4. Cấu trúc response

### 4.1 FiinTrade — envelope thống nhất

Mọi endpoint FiinTrade trả về cùng một vỏ bọc:

```json
{
  "page": 1,
  "pageSize": 0,
  "totalCount": 1,
  "items": [ ... ],
  "packageId": null,
  "status": 0,
  "errors": null
}
```

| Trường | Kiểu | Mô tả |
|---|---|---|
| `page` | integer | Trang hiện tại |
| `pageSize` | integer | Kích thước trang. Nhiều endpoint trả `0` dù có dữ liệu — **không dùng trường này để phân trang** |
| `totalCount` | integer | Tổng số bản ghi. ⚠️ Một số endpoint luôn trả `0` dù có dữ liệu (xem Bẫy 6) |
| `items` | array | Dữ liệu thật. Có thể là mảng rỗng `[]` hoặc `null` |
| `packageId` | string \| null | Định danh gói dịch vụ. Luôn `null` trên bản white-label BVSC |
| `status` | integer \| string | Trạng thái xử lý — **xem Bẫy 2** |
| `errors` | array \| null | Danh sách lỗi khi `status` báo thất bại |

### 4.2 BVSC — envelope `{s, d}`

```json
{ "s": "ok", "d": [ ... ] }
```

| Trường | Kiểu | Mô tả |
|---|---|---|
| `s` | string | `ok` khi thành công |
| `d` | array \| object | Dữ liệu |

Một số endpoint BVSC trả **mảng trần** hoặc **object trần**, không có vỏ bọc:
- `/mapping` → mảng trần
- `/datafeed/chartinday/{codes}` → object trần, khoá là mã chỉ số

### 4.3 tvcharts — chuẩn TradingView UDF

```json
{ "s": "ok", "t": [...], "o": [...], "h": [...], "l": [...], "c": [...], "v": [...] }
```

Khi không có dữ liệu: `{"s": "no_data"}`.

---

## 5. Kiểu dữ liệu và đơn vị

| Loại | Quy ước | Ví dụ |
|---|---|---|
| Giá cổ phiếu | **VND, số nguyên** | `39050` = 39.050 đ = 39,05 nghìn |
| Giá trị giao dịch | **VND**, có thể rất lớn | `8164990000` = 8,16 tỷ |
| Khối lượng | **Số cổ phiếu** | `206600` |
| Tỷ lệ / phần trăm | **Số thập phân**, không phải % | `0.0154` = 1,54% |
| Chỉ số | **Điểm, số thập phân** | `1769.8` |
| Thời gian FiinTrade | ISO 8601 có offset | `2026-08-10T09:18:12.2500000+07:00` |
| Thời gian BVSC (realtime) | Epoch milliseconds | `1786330492737` |
| Ngày BVSC (REST) | `dd/MM/yyyy` | `10/08/2026` |
| Giờ BVSC (REST) | `HH:mm:ss` | `10:40:35` |

**Múi giờ:** toàn hệ thống dùng `Asia/Ho_Chi_Minh` (UTC+7). Trường `timezone` trong `TVC /symbols` khai báo `Asia/Bangkok` — cùng offset, không ảnh hưởng tính toán.

**Kỳ báo cáo:** cặp `yearReport` + `lengthReport`, trong đó `lengthReport` = `1`..`4` là quý I–IV, `5` là cả năm. Định dạng chuỗi tương ứng là `{năm}_{quý}`, ví dụ `2026_2`.

---

## 6. Xử lý lỗi

### 6.1 FiinTrade — HTTP status KHÔNG phản ánh kết quả

> ### 🔴 Quy tắc số một
> **FiinTrade luôn trả `HTTP 200`, kể cả khi xử lý thất bại.** Mọi cơ chế bắt lỗi dựa trên HTTP status code sẽ không phát hiện được bất kỳ lỗi nào.

Cách kiểm tra đúng:

```
Thành công  ⟺  status ∈ {0, "Success"}
Thất bại    ⟺  status == "Failed"  →  đọc mảng errors
```

⚠️ Trường `status` có **hai kiểu dữ liệu** tuỳ endpoint:

| Nhóm endpoint | Giá trị khi thành công |
|---|---|
| `Snapshot/*`, `MoneyFlow/*` | `0` *(số nguyên)* |
| `Calendar/*`, `FinancialAnalysis/*` | `"Success"` *(chuỗi)* |

Chỉ kiểm `status == "Success"` sẽ báo lỗi giả cho toàn bộ nhóm Snapshot. Chỉ kiểm `status == 0` sẽ báo lỗi giả cho nhóm Calendar.

### 6.2 Các dạng lỗi quan sát được

| Tình huống | HTTP | Body |
|---|---|---|
| Thiếu header `Origin` | `403` | rỗng |
| Tham số sai kiểu (validate được) | `400` | `{"error":{"code":"InvalidOperationException","message":"PageSize is not allowed: 10"}}` |
| Enum không hợp lệ | `400` | `{"investorType":["The value 'Foreign' is not valid for InvestorType."]}` |
| Lỗi runtime .NET | `200` | `{"status":"Failed","errors":["Object reference not set to an instance of an object."]}` |
| Sai định dạng tham số | `200` | `{"status":"Failed","errors":["Input string was not in a correct format."]}` |
| Mã không tồn tại / sai `organCode` | `200` | `{"items":[]}` hoặc `{"items":null}` — **không có lỗi nào** |

FiinTrade **rò thông báo lỗi runtime .NET thô** ra ngoài (`Object reference not set to an instance of an object`, `Index was outside the bounds of the array`). Đây là dấu hiệu thiếu validate ở tầng controller. Không nên hiển thị các chuỗi này cho người dùng cuối; nên validate tham số ở phía BVSC trước khi gọi.

### 6.3 BVSC

BVSC trả HTTP status đúng nghĩa: `404` cho endpoint không tồn tại, `200` cho thành công. Endpoint không hỗ trợ tham số có thể trả `200` với **body rỗng hoàn toàn** (0 byte) — xem Bẫy 7.

---

## 7. Mười ba bẫy triển khai

### Bẫy 1 — `organCode` khác `ticker` ở 41% doanh nghiệp

**Mức độ: nghiêm trọng.** Đây là nguyên nhân lỗi phổ biến nhất khi tích hợp FiinTrade.

Toàn bộ API FiinTrade định danh doanh nghiệp bằng `organCode` — mã nội bộ của FiinGroup — **không phải mã chứng khoán**. Trong 1.553 doanh nghiệp, **647 mã (41,7%)** có `organCode ≠ ticker`:

| Sàn | Số mã lệch | Tỷ lệ |
|---|---|---|
| UPCOM | 449 | 37,5% mã UPCOM |
| HOSE | 135 | 31,3% mã HOSE |
| HNX | 63 | 18,3% mã HNX |

Ví dụ: `VHM → NHN` · `ACV → ACVN` · `VGI → VTGI` · `MCH → MSCC` · `BSR → BSRC` · `STK → CENTURY`. Có **72 mã dùng mã số thuế** làm `organCode`: `TAH → 3801140300`, `TAB → 0107005554`, `BVL → 10708`.

**Hành vi khi gọi sai:** không có lỗi. API trả `HTTP 200` với `items` rỗng.

```
GET /PriceData/GetPriceData?Code=VHM&...  →  200 ·    119 byte · items rỗng
GET /PriceData/GetPriceData?Code=NHN&...  →  200 · 204.195 byte · 60 phiên
```

Đã kiểm chứng trên **22/22 mã lệch**, không có ngoại lệ.

**Bắt buộc:** nạp `Master/GetListOrganization` lúc khởi động, cache bảng `ticker → organCode`, và dùng `organCode` cho mọi lời gọi FiinTrade. Các endpoint bị ảnh hưởng nhận tham số tên `OrganCode` **hoặc** `Code` — cả hai đều cần `organCode`.

Ngoại lệ: `CashDividendAnalysis/GetAnalysis` nhận **cả hai** — `OrganCode` và `Code` (ticker).

### Bẫy 2 — `status` hai kiểu dữ liệu

Xem mục 6.1.

### Bẫy 3 — Chọn sai endpoint Snapshot làm rỗng gần nửa dữ liệu

`Snapshot/GetSnapshot` và `Snapshot/GetSnapshotNoneBank` có **cấu trúc giống hệt nhau** và **đều trả `HTTP 200` cho mọi mã**. Khác biệt nằm ở tỷ lệ trường `null` bên trong:

| `comTypeCode` | Số mã kiểm thử | `GetSnapshot` tỷ lệ null | `GetSnapshotNoneBank` tỷ lệ null | Dùng |
|---|---|---|---|---|
| `NH` — Ngân hàng | 3 | **25,9%** | 46,4% | `GetSnapshot` |
| `CT` — Doanh nghiệp thường | 41 | 36,3% | **12,1%** | `GetSnapshotNoneBank` |
| `CK` — Chứng khoán | 5 | 29,6% | **24,3%** | `GetSnapshotNoneBank` |
| `BH` — Bảo hiểm | 2 | 29,6% | **14,3%** | `GetSnapshotNoneBank` |

**Quy tắc:** `comTypeCode == "NH"` → `GetSnapshot`. Mọi trường hợp khác → `GetSnapshotNoneBank`.

`comTypeCode` lấy từ `Master/GetListOrganization`.

### Bẫy 4 — Whitelist tham số cứng

| Endpoint | Tham số | Giá trị hợp lệ | Giá trị khác |
|---|---|---|---|
| `PriceData/GetPriceData` | `PageSize` | **chỉ `30` và `60`** | `400 InvalidOperationException` |
| `PriceData/GetPriceData` | `Frequently` | **chỉ `Daily`** | `Weekly`/`Monthly` → `200` nhưng **vẫn trả nến ngày**; `Quarterly` → `status: "Failed"` |
| `Screener/GetScreenerItems` | `pageSize` | **chỉ `30`** | `status: "Failed"` — đã thử 10, 15, 20, 25, 50, 60, 100 |
| `Screener/GetScreenerItems` | `comGroupCode` + `icbCode` | **cả hai bắt buộc** | Thiếu một → `"ComGroupCode or IcbCode is not supplied."` *(chữ `or` gây hiểu nhầm)* |
| `MoneyFlow/GetContribution` | `Type` | **chỉ `Total`** | `Up`/`Down` → `400` |
| `MarketInDepth/GetLiquiditySeries` | `TimeRange` | **bắt buộc có** | Thiếu → `items: []` |
| `TVC /history` | `resolution` | **chỉ `D` và `1`** | `5`/`15`/`30`/`60`/`W`/`M` → body rỗng 0 byte |

Đã thử `PageSize` = 10, 20, 25, 40, 50, 100, 120 — tất cả đều `400`.

### Bẫy 4b — `selectedValue` của Screener phải là mảng, và thang đơn vị không theo `unit`

`Screener/GetScreenerItems` nhận điều kiện lọc dưới dạng mảng `[min, max]`:

```json
"selectedValue": [0.20, 7.85938948]      ✅
"selectedValue": {"from": 0.20, "to": 100}   ❌ HTTP 400
```

Và **thang giá trị theo dữ liệu thô, không theo trường `unit`**. Ví dụ ROE khai `unit: "Percentage"` nhưng `valueRange` là `[-127,56 · 7,86]` — tức thang thập phân, `0.20` = 20%, không phải `[0, 100]`. **Luôn tham chiếu `valueRange` để biết thang thật.**

### Bẫy 5 — `Calendar/*` bỏ qua tham số `Ticker`

Nhóm `Calendar/GetCorporate*` lọc theo mã bằng **`OrganCode`**. Tham số `Ticker` được chấp nhận nhưng **bị bỏ qua hoàn toàn** — `totalCount` không thay đổi, API vẫn trả toàn thị trường.

```
GET /Calendar/GetCorporateAGM?Ticker=BID&...      →  toàn bộ 23.434 bản ghi  ❌
GET /Calendar/GetCorporateAGM?OrganCode=BID&...   →  chỉ bản ghi của BID     ✅
```

`FromDate` / `ToDate` hoạt động đúng.

### Bẫy 6 — `totalCount` không đáng tin ở một số endpoint

Nhóm `TopMover/*` và một số endpoint khác trả `totalCount: 0` dù `items` có 30 bản ghi. Luôn dùng `items.length`, không dùng `totalCount`, trừ nhóm `Calendar/*` (nơi `totalCount` chính xác và cần thiết để phân trang).

### Bẫy 7 — `TVC /history` bỏ qua `from`, chặn cứng ở 239 nến

Với `resolution=D`, tham số `from` **không có tác dụng**. Yêu cầu cửa sổ 1, 2, 5, 10, 20 năm đều trả đúng **239 nến, luôn bắt đầu từ cùng một ngày**. Không có tham số phân trang.

→ Muốn lịch sử sâu hơn 1 năm, dùng `PriceData/GetPriceData` — **phân trang lùi tới ~12,5 năm** (Page 1–52, mỗi trang 60 phiên, dữ liệu trang sâu vẫn đủ 99 trường).

Với `resolution=1` (nến 1 phút), cửa sổ `to - from` phải **≤ ~30 ngày**, rộng hơn trả `{"s":"no_data"}`. Dữ liệu trả về luôn là phiên gần nhất.

Muốn nến 5/15/30/60 phút phải **tự gộp từ nến 1 phút** — API không hỗ trợ.

### Bẫy 8 — Giá lịch sử là giá ĐÃ điều chỉnh, và hai nguồn lệch nhau

`TVC /history` và `PriceData/GetPriceData` đều trả **giá điều chỉnh hồi tố** cho cổ tức và chia tách, nhận biết bằng giá trị thập phân ở dữ liệu cũ (`37910,8925`). Giá thô chỉ có ở phiên hiện tại, qua `/datafeed/instruments` và luồng realtime.

Hai nguồn dùng **hệ số điều chỉnh khác nhau**, lệch ~0,005%:

| Ngày | `TVC /history` | `getPriceData` |
|---|---|---|
| 2025-11-14 | 37910,8925 | 37908,975 |
| 2025-11-11 | 37564,90 | 37563,00 |

⚠️ **Không trộn hai nguồn trong cùng một chuỗi giá.** Phiên gần nhất thì trùng khớp tuyệt đối vì tại đó điều chỉnh bằng thô.

### Bẫy 9 — Kỳ báo cáo không tồn tại trả marker đặc biệt

`FinancialAnalysis/GetFinancialRatioV2` với `Timeline=2025_9` (quý 9 không tồn tại) trả `status: "Success"` kèm:

```json
{"key": "2025_9", "value": {"organCode": "EndOfData"}}
```

Không phải lỗi, cũng không phải dữ liệu. Phải kiểm `value.organCode != "EndOfData"` trước khi dùng.

> **Bẫy 10–13 phát hiện trong đợt khảo sát nguồn 2026-08-15.** Hai bẫy cuối vượt ra ngoài BVSC/FiinTrade — giữ ở đây vì chúng ảnh hưởng tới **mọi chuỗi thời gian** và **mọi phép đối chiếu giá** của hệ thống, không riêng một nguồn.

### Bẫy 10 — `StockType` không nhất quán giữa hai endpoint BVSC

Cùng một mã trái phiếu (`HDC425001`), hai endpoint báo hai giá trị khác nhau *(đo 2026-08-15)*:

| Endpoint | `StockType` |
|---|---|
| `BVSC /quotes` | **12** |
| `BVSC /datafeed/instruments` | **1** |

**Không dùng `StockType` làm khoá phân loại chung.** Mọi bảng ánh xạ `StockType → loại chứng khoán` chỉ có nghĩa **trong phạm vi đúng một endpoint**, phải ghi rõ endpoint nào khi lưu vào kho.

Hành vi này không báo lỗi: cả hai bản ghi đều hợp lệ, chỉ khác nghĩa. Nếu ETL hợp nhất hai endpoint rồi phân loại theo `StockType`, một phần danh mục sẽ **xếp sai nhóm mà không có tín hiệu nào**.

Phân loại đáng tin hơn: `FloorCode` *(`03` = phái sinh)*, `FundType` cho quỹ, và trường `exchange` — nhưng cũng phải kiểm lại theo từng endpoint, chưa kiểm chéo toàn bộ.

### Bẫy 11 — Hai endpoint BVSC lệch độ phủ, không endpoint nào là danh mục chuẩn

| Endpoint | Số bản ghi *(đo 2026-08-15)* |
|---|---:|
| `BVSC /quotes?symbols=ALL` | **2.534** |
| `BVSC /datafeed/instruments` | **2.001** *(HOSE 768 · UPCOM 823 · HNX 396 · phái sinh 14)* |

Chênh lệch **không phải quan hệ bao hàm một chiều** — mỗi endpoint có mã mà endpoint kia không có:

| Bằng chứng | Có ở | Không có ở |
|---|---|---|
| `VFMVF1` *(chứng chỉ quỹ)* | `/quotes` | `/datafeed/instruments` |
| 14 hợp đồng phái sinh | `/datafeed/instruments` | `/quotes` — trả `{"s":"ok","d":[]}` |

🔴 **Hệ quả thiết kế ETL:** không có endpoint nào dùng làm **danh mục chuẩn duy nhất**. Bước dựng danh mục mã phải **hợp nhất cả hai** rồi khử trùng theo mã, và ghi lại mã đến từ nguồn nào.

⚠️ **Bài học phương pháp:** chính vì lấy `/quotes` làm danh mục chuẩn mà bản trước của tài liệu này kết luận sai rằng BVSC không có phái sinh — xem [`01-bvsc-rest.md`](01-bvsc-rest.md). **Vắng mặt ở một endpoint không phải bằng chứng vắng mặt ở nguồn.**

### Bẫy 12 — Epoch của WiChart là nửa đêm GIỜ VIỆT NAM, không phải UTC

**Mức độ: nghiêm trọng.** Đây là bẫy đã **thật sự làm hỏng một phép đo** trong đợt khảo sát 2026-08-15 và sinh ra một kết luận sai hoàn toàn về giá dầu.

Mốc thời gian của mọi chuỗi WiChart là epoch mili giây của **nửa đêm giờ Việt Nam** — `00:00` theo `Asia/Ho_Chi_Minh` (UTC+7):

```
epoch = 1786726800000
  → parse UTC     : 2026-08-14 17:00  ❌ gán nhãn ngày 14/08
  → parse giờ VN  : 2026-08-15 00:00  ✅ đúng nhãn ngày 15/08
```

Parse theo UTC làm **lệch nhãn ngày của cả chuỗi lùi một ngày**. Hậu quả đo được khi đối chiếu `dau_wti` với FRED `DCOILWTICO` *(đo 2026-08-15)*:

| Cách parse | n | Lệch TB có dấu | \|Lệch\| TB | sd | max |
|---|---:|---:|---:|---:|---:|
| **UTC** *(sai)* | 115 | −2,26% | **3,35%** | 3,97% | 16,40% |
| **Giờ VN (+7h)** *(đúng)* | 125 | −1,97% | **2,85%** | 3,34% | 21,50% |

**Cách nhận biết đã lệch nhãn ngày:** khi so hai nguồn, giá của ngày `d` ở nguồn này **trùng khít tới từng chữ số thập phân** với giá ngày `d+1` ở nguồn kia. Một chuỗi trùng khít lệch pha là bằng chứng **sai nhãn ngày**, không phải sai giá — sai giá thật thì lệch ngẫu nhiên, không trùng khít.

**Quy tắc:** mọi epoch của WiChart phải quy đổi bằng `Asia/Ho_Chi_Minh`, không dùng `utcfromtimestamp`. Chi tiết riêng cho nguồn này ở [`wichart.md`](../macro/wichart.md).

### Bẫy 13 — Giá giao ngay KHÔNG bằng giá tương lai: chênh ~2% là chênh lệch cơ sở, không phải sai số

Khi đối chiếu giá hàng hoá giữa các nguồn, chênh lệch hệ thống **~2%** giữa FRED `DCOILWTICO` và WiChart/Yahoo/Binance **không phải lỗi của nguồn nào** — hai bên đo hai thứ khác nhau:

| Nguồn | Đo cái gì |
|---|---|
| FRED `DCOILWTICO` | **Giao ngay** WTI Cushing *(EIA)* |
| WiChart `dau_wti` · Yahoo `CL=F` · Binance | **Tương lai** kỳ hạn gần |

Bằng chứng trực tiếp — cấu trúc kỳ hạn WTI *(đo 2026-08-15)*:

| Hợp đồng | Kỳ hạn | Giá |
|---|---|---:|
| `CLU26.NYM` | Sep 26 *(gần nhất)* | **82,40** |
| `CLV26.NYM` | Oct 26 | 81,47 |
| `CLX26.NYM` | Nov 26 | 80,10 |
| `CLZ26.NYM` | Dec 26 | **78,49** |

**Giá giảm đơn điệu theo kỳ hạn ⇒ thị trường backwardation**, dốc ≈ **−1,6%/tháng**. Backwardation nghĩa là giao ngay **cao hơn** tương lai — đúng chiều và đúng độ lớn của chênh lệch quan sát được: FRED cao hơn tương lai **+2,02%** trung bình, và **cực kỳ ổn định** (`+1,89 … +2,07` trên 7 phiên). Sai số ngẫu nhiên không ổn định như vậy.

🔴 **Quy tắc khi lưu và khi đối chiếu:**
- Ghi rõ **loại giá** *(giao ngay / tương lai)* cho mọi chuỗi hàng hoá — nhãn "Giá dầu WTI" của nguồn **không đủ** để biết là loại nào.
- **Không lấy chênh lệch hai loại giá làm chỉ báo chất lượng nguồn.** Chỉ so cùng loại với cùng loại.
- Chênh lệch cơ sở **trôi theo thời gian** khi độ dốc kỳ hạn đổi — một ngưỡng cảnh báo cố định kiểu *"lệch quá 1% là hỏng"* sẽ báo động giả.

⚠️ Bẫy anh em, cùng bản chất: **fixing ≠ giá đóng cửa.** LBMA là fixing 15:00 London, lệch **0,56%** so với XAU/USD giao ngay; tỷ giá ECB là fixing 14:15 CET *(đo 2026-08-15)*. Cũng là đặc tính, không phải sai số.

---

## 8. Độ phủ dữ liệu — cảnh báo chung

Toàn bộ 43 endpoint đã kiểm chứng sống trên 51 mã mẫu. Tuy nhiên **chất lượng dữ liệu suy giảm rõ rệt với cổ phiếu nhỏ sàn UPCOM**:

| Endpoint | Độ phủ | Nhóm thiếu |
|---|---|---|
| `Rankings/GetRateIndicator` | 82% | 8/19 mã UPCOM |
| `Valuation/GetValuation` — trường dự phóng | 67% | rải rác mọi sàn |
| `BVSC /datafeed/translogsnaps` | 67% | 12/17 mã rỗng là UPCOM |
| `GetFinancialReports` | 98% | 1 mã |

Các mã như `TAH`, `THU`, `RAT`, `VCT` gần như không có dữ liệu quý. Giao diện cần thiết kế trạng thái rỗng cho nhóm này thay vì giả định luôn có dữ liệu.

Chi tiết đầy đủ: [appendix-B-coverage.md](appendix-B-coverage.md).

---

## 9. Hiệu năng đo được

| Nhóm | Thời gian phản hồi | Kích thước |
|---|---|---|
| Endpoint nhẹ (`GetCompanyScore`, `GetZMFScore`) | 130–450 ms | < 1 KB |
| Endpoint trung bình | 0,5–1 s | 5–50 KB |
| `GetBalanceSheet` / `GetIncomeStatement` / `GetCashFlow` | 1,9–2,5 s | 191–374 KB |
| `MoneyFlow/GetProprietaryV2` | ~3,1 s | 459 KB |
| `PriceData/GetPriceData` (PageSize=60) | ~3,5 s | ~201 KB |
| `Calendar/GetCorporateEarning` | **~7,4 s** | 6 KB |
| `Master/GetListOrganization` | ~4,4 s | 355 KB |

Các endpoint tham chiếu (`GetListOrganization`, `GetAllIcbIndustry`, `/quotes`, `/mapping`) nên được cache dài hạn — dữ liệu chỉ đổi khi có mã mới niêm yết.

---

## 10. Rate limit — đo bằng đúng tải ETL kế hoạch (2026-08-15)

> 🔴 **Không dò ngưỡng trần — đây là chủ đích, không phải thiếu sót.** Phép đo này chạy đúng mức tải mà [lịch ETL đã thiết kế](../../20-design/market-data-store.md) sẽ tạo ra, rồi dừng. Nó trả lời câu *"tải kế hoạch có bị chặn không"*, **không** trả lời câu *"chặn ở mức nào"*. Mọi câu trả lời cho câu hỏi thứ hai đều đòi phải cố tình làm quá tải hạ tầng của FiinGroup, và dự án chọn không làm.

### 10.1 Ngân sách lời gọi định kỳ — ước lượng trước khi đo

Tính từ [lịch ETL §4.1–4.2](../../20-design/market-data-store.md), tách theo tần suất:

| Họ endpoint | Host | Nhịp | Lời gọi mỗi lần chạy |
|---|---|---|---|
| Danh bạ · cây ngành · `/quotes` · `/mapping` | `FIIN_CORE`, `BVSC` | Trước phiên, hằng ngày | 4 |
| `PriceData/GetPriceData` Page 1 | `FIIN_TECH` | Sau 15:00, hằng ngày | 1.974 |
| `Snapshot/*` — hồ sơ, sở hữu | `FIIN_FUND` | Sau 15:00, hằng ngày | ~4.000 |
| **`Screener/GetScreenerItems` — phân trang 52 trang** | `FIIN_TOOLS` | Sau 15:00, hằng ngày | **52** |
| `Calendar/*` — lịch sự kiện | `FIIN_MARKET` | Hằng ngày | ~10 |
| **Cộng thường nhật** | | **hằng ngày** | **≈ 6.040** |
| BCTC 3 loại × 1.974 mã | `FIIN_FUND` | Theo quý, rải | 5.922 |
| `getPriceData` 52 trang × 1.974 mã | `FIIN_TECH` | **Một lần**, rải 1–2 tuần | 102.648 |

**Vì sao chọn burst Screener để kiểm.** Ba nhóm hằng ngày kia lớn hơn về số lượng nhưng là **nhiều lời gọi độc lập trên nhiều mã**, rải được tuỳ ý. Riêng 52 trang Screener là **một chuỗi phân trang dính liền trên đúng một endpoint của đúng một host** — không rải được, phải đi liền mạch mới lấy đủ 1.549 mã — và là lời gọi **nặng nhất mỗi lượt** trong cả lịch. Nếu chỗ nào bị chặn trước thì là chỗ này.

**Quy ra nhịp:** 52 lời gọi tuần tự ở latency đo ngày 2026-08-15 ⇒ dự kiến ~5–6 phút, tức **9–10 request/phút**. Đây là con số cần kiểm.

### 10.2 Đã chạy những gì

| Bước | Lời gọi | Thời gian | Kết quả |
|---|---|---|---|
| `Screener/GetScreenerParameters` — lấy bộ tiêu chí | 1 | 2,8 s | `Success` |
| **Burst thường nhật:** `Screener/GetScreenerItems` **52 trang liên tiếp, tuần tự** — `comGroupCode=ALL`, `icbCode=ALL`, 1 tiêu chí, `pageSize=30` | 52 | **1 phút 49 giây** | **52/52 `Success`** · 1.549 mã · 7,7 MB |
| Mẫu họ khác: `Snapshot/GetSnapshotNoneBank` + `Snapshot/GetCompanyScore` trên 5 mã | 10 | 2,7 s | 10/10 `Success` |
| Một lời gọi hỏng — Redis timeout của chính FiinTrade, xem §10.5 | 1 | 7,7 s | `status: "Failed"` |
| **Tổng toàn phiên** | **64** | | trần tự đặt: 100 |

Burst chạy **nhanh gấp ba dự kiến** — 1,8 phút thay vì 5–6 phút, vì latency lúc đo *(trung vị 2,07 s trên 52 mẫu)* thấp hơn hẳn con số 6,44 s của **lần đo sớm hơn trong cùng ngày 2026-08-15**, ghi ở [`10-fiin-dictionary.md`](10-fiin-dictionary.md). Hệ quả: nhịp thật đạt **~29 request/phút**, cao hơn ước lượng ban đầu, và **vẫn không bị chặn**.

Toàn bộ chạy **tuần tự, một luồng, không chèn khoảng nghỉ nhân tạo** — độ trễ thật của máy chủ chính là nhịp.

### 10.3 Số đo

| Chỉ tiêu | Giá trị |
|---|---|
| Nhịp burst Screener | **28,7 request/phút** *(52 lời gọi / 1,81 phút)* |
| Latency `GetScreenerItems` | min 1.077 · **trung vị 2.074** · p90 2.684 · max 3.100 ms |
| Latency `GetSnapshotNoneBank` / `GetCompanyScore` | min 32 · trung vị 229 · max 1.174 ms |
| HTTP status | **200 trên cả 64 lời gọi** |
| `status` trong body | `Success` trên 63/64 |

**Không gặp bất kỳ tín hiệu chặn nào:** không `429`, không `403`, không `5xx`, không `Retry-After`, không đợt tăng latency đột biến. Latency ở trang 52 không cao hơn trang 1.

### 10.4 Header — xác nhận lại là không có

Hợp nhất header của cả 64 response:

```
access-control-allow-credentials · access-control-allow-origin · access-control-expose-headers
content-encoding · content-type · date · server · transfer-encoding · vary
x-miniprofiler-ids · x-powered-by
```

**Không có `X-RateLimit-*`, không có `Retry-After`, không có bất kỳ header họ hạn mức nào.** Điều tài liệu này nói trước đây được xác nhận bằng đo thật. Hệ quả: ETL **không thể** dựa vào header để biết mình còn bao nhiêu hạn mức — phải tự giữ nhịp bằng token bucket phía Finext.

*(`server` trả về hai giá trị xen kẽ — `Microsoft-IIS/8.5` và `Microsoft-IIS/10.0`, **mỗi loại đúng 32 lần trên 64 response**. Dấu hiệu có cân bằng tải trước ít nhất hai máy chủ khác đời.)*

### 10.5 Một lời gọi hỏng — và vì sao nó không phải tín hiệu chặn

**Lời gọi thứ hai của toàn phiên** *(`GetScreenerItems` trang 1)* trả `HTTP 200` kèm:

```json
{"status":"Failed","errors":["Timeout performing GET (5000ms) … serverEndpoint: 192.168.1.232:6379 …"]}
```

Đây là **Redis timeout nội bộ của chính FiinTrade** — cùng lỗi đã ghi ở [`10-fiin-dictionary.md`](10-fiin-dictionary.md) cho trường hợp gửi nhiều tiêu chí. Nó **không phải** rate limit, vì ba lý do đo được: xảy ra khi phiên mới có đúng 2 lời gọi *(không có tải nào để mà chặn)*, `HTTP 200` chứ không phải `429`, và không kèm header hạn mức nào.

🔵 **Quyết định dừng-và-chạy-lại — ghi lại để người sau audit được.** Phép đo **đã dừng ngay tại đây theo luật dừng ở tín hiệu đầu tiên** *(08:04:47)*. Sau khi đánh giá đây **không phải tín hiệu chặn** — `HTTP 200` kèm lỗi Redis nội bộ đã có hồ sơ sẵn trong tài liệu, và mới ở request thứ 2 của phiên — phép đo được **chạy lại đúng một lần** *(08:06:44)*, không đổi tham số, không giảm nhịp. Lần chạy lại đi trọn 52 trang thông suốt. Cả 64 lời gọi của **cả hai lần** đều tính vào trần 100 ở §10.2.

**Chính đánh giá này là chỗ cần soi lại nhất trong cả phép đo.** Nếu coi mọi `status: "Failed"` là tín hiệu chặn thì kết luận ở §10.6 không đứng được, và mục rate limit phải quay lại danh sách việc chặn.

**Hệ quả cho ETL:** `status: "Failed"` kèm chuỗi `Timeout performing` là **lỗi tạm thời của nguồn**, phải xử lý bằng thử lại có kiểm soát (backoff, giới hạn số lần) chứ không được coi là dữ liệu rỗng — coi là rỗng sẽ ghi một trang trắng vào kho mà không ai biết.

### 10.6 Kết luận và giới hạn của kết luận

✅ **Mức tải đã kiểm là an toàn:** burst Screener thường nhật — 52 lời gọi phân trang tuần tự, ~29 request/phút, ~1,8 phút — chạy trọn vẹn không gặp tín hiệu chặn nào, kèm mẫu 10 lời gọi họ `Snapshot/*`.

⚠️ **Những gì phép đo này KHÔNG nói:**

| Chưa kiểm | Vì sao quan trọng |
|---|---|
| Nhịp **8 luồng** của ETL hằng ngày | Lịch thiết kế là ~6.000 lời gọi trong 20–30 phút ≈ **200–300 request/phút** — gấp 7–10 lần nhịp đã đo |
| Trần **2 request/giây** đặt cho backfill 102.648 lời gọi | = 120 request/phút, vẫn gấp hơn 4 lần nhịp đã đo |
| Hai nhóm lớn nhất của lịch ngày — `getPriceData` 1.974 và Snapshot ~4.000 lời gọi | Chỉ burst Screener được tái hiện |

**Khuyến nghị vận hành:** nhịp tuần tự như thiết kế ETL mô tả là **mức đã kiểm** — dùng được ngay. Muốn nâng lên 8 luồng thì phải đo lại ở đúng nhịp đó trước khi bật chạy thật, và vẫn theo cùng nguyên tắc: chạy đúng tải kế hoạch rồi dừng, không dò trần.
