# 08 — Lịch sự kiện

Base URL: `https://wlgw-market.fiintrade.vn/Calendar` — ký hiệu `FIIN_MARKET`
Header bắt buộc: `Origin: https://fiinapp.bvsc.com.vn`

8 endpoint. Nguồn gốc dữ liệu là **VSD và các Sở giao dịch** — đây là dữ kiện thô, không phải phân tích của FiinTrade. Trường `sourceUrl` trỏ thẳng về bản công bố gốc — nhưng **chỉ `getCorporateAGM` trả trường này** *(đo 2026-09-03)*; năm họ `GetCorporate*` còn lại (`CashDividend`, `StockDividend`, `Earning`, `IPO`, `ShareIssuance`) không có `sourceUrl`.

BVSC không có nguồn tương đương cho bất kỳ endpoint nào trong nhóm này.

---

## Tham số dùng chung cho nhóm `GetCorporate*`

| Tên | Vị trí | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|---|
| `Page` | query | integer | *tuỳ chọn* | Mặc định 1 |
| `PageSize` | query | integer | *tuỳ chọn* | Không có whitelist — nhận giá trị tự do |
| `OrganCode` | query | string | *tuỳ chọn* | **Lọc theo doanh nghiệp.** Hoạt động đúng |
| `FromDate` / `ToDate` | query | string | *tuỳ chọn* | `yyyy-MM-dd`. Hoạt động đúng |
| `language` | query | string | *tuỳ chọn* | `vi` \| `en` |

### 🔴 Bẫy — tham số `Ticker` bị bỏ qua

```
GET /Calendar/GetCorporateAGM?Ticker=BID&...      →  trả toàn bộ 23.434 bản ghi  ❌
GET /Calendar/GetCorporateAGM?OrganCode=BID&...   →  chỉ bản ghi của BID          ✅
```

Truyền `Ticker` không gây lỗi, `totalCount` cũng không đổi — API đơn giản là bỏ qua. **Luôn dùng `OrganCode`**, lấy từ [`getListOrganization`](03-fiin-reference.md).

`totalCount` ở nhóm này **chính xác** và cần thiết để phân trang.

---

## `getCorporateAGM`

**Tóm tắt:** Đại hội đồng cổ đông.

```
GET FIIN_MARKET/Calendar/GetCorporateAGM?Page=1&PageSize=20&language=vi
```

### Response 200 — 10 trường

```json
{
  "totalCount": 23434,
  "items": [{
    "organCode": "NHANCO",
    "ticker": "VCE",
    "organShortName": "Xây lắp Môi trường",
    "publicDate": "2026-08-06T00:00:00",
    "issueDate": null,
    "exrightDate": "2026-08-27T00:00:00",
    "address": "Tầng 12, tòa nhà Intracom 2, số 33 Cầu Diễn, Hà Nội",
    "locationName": "Thành phố Hà Nội",
    "eventTitle": null,
    "sourceUrl": "https://vsd.vn/vi/ad/198980"
  }],
  "status": "Success"
}
```

| Trường | Kiểu | Mô tả |
|---|---|---|
| `organCode` / `ticker` / `organShortName` | string | Định danh doanh nghiệp |
| `publicDate` | string | Ngày công bố thông tin |
| `issueDate` | string \| null | Ngày phát hành |
| `exrightDate` | string | **Ngày giao dịch không hưởng quyền** |
| `address` | string | Địa điểm tổ chức đầy đủ |
| `locationName` | string | Tỉnh/thành |
| `eventTitle` | string \| null | Tiêu đề sự kiện |
| `sourceUrl` | string | Link công bố gốc trên VSD |

**Tổng bản ghi lịch sử: 23.434**

---

## `getCorporateCashDividend`

**Tóm tắt:** Cổ tức bằng tiền mặt.

```
GET FIIN_MARKET/Calendar/GetCorporateCashDividend?Page=1&PageSize=20&language=vi
```

### Response 200 — 10 trường

```json
{
  "totalCount": 17884,
  "items": [{
    "organCode": "SAS", "ticker": "SAS",
    "publicDate": "2026-07-29T00:00:00",
    "recordDate": "2026-08-04T00:00:00",
    "exrightDate": "2026-08-03T00:00:00",
    "payoutDate": "2026-08-10T00:00:00",
    "exerciseRate": 0.4024,
    "valuePerShare": 4024.0,
    "dividendYear": 2025,
    "stageName": "Đợt 2"
  }],
  "status": "Success"
}
```

| Trường | Kiểu | Đơn vị | Mô tả |
|---|---|---|---|
| `publicDate` | string | — | Ngày công bố |
| `recordDate` | string | — | Ngày chốt danh sách |
| `exrightDate` | string | — | **Ngày GDKHQ** |
| `payoutDate` | string | — | Ngày chi trả |
| `exerciseRate` | number | thập phân | Tỷ lệ thực hiện. `0.4024` = 40,24% |
| `valuePerShare` | number | VND | Số tiền mỗi cổ phiếu. `4024.0` = 4.024 đ |
| `dividendYear` | integer | — | Năm tài chính của cổ tức |
| `stageName` | string | — | Đợt chi trả: `Đợt 1`, `Đợt 2`, `Cả năm`… |

**Tổng bản ghi: 17.884**

Bốn mốc ngày đầy đủ (`publicDate` → `exrightDate` → `recordDate` → `payoutDate`) cho phép làm cảnh báo đúng thời điểm.

---

## `getCorporateStockDividend`

**Tóm tắt:** Cổ tức bằng cổ phiếu và cổ phiếu thưởng.

```
GET FIIN_MARKET/Calendar/GetCorporateStockDividend?Page=1&PageSize=20&language=vi
```

### Response 200

Cấu trúc **giống hệt** `getCorporateCashDividend` (10 trường như trên).

Khác biệt: `exerciseRate` là tỷ lệ chia cổ phiếu (`0.1` = 10%, tức 10 cổ phiếu cũ nhận 1 cổ phiếu mới), và `valuePerShare` thường bằng `0.0`.

**Tổng bản ghi: 2.086**

---

## `getCorporateEarning`

**Tóm tắt:** Công bố kết quả kinh doanh theo kỳ.

```
GET FIIN_MARKET/Calendar/GetCorporateEarning?Page=1&PageSize=20&language=vi
```

### Response 200 — 12 trường

```json
{
  "totalCount": 57176,
  "items": [{
    "ticker": "PTM", "organCode": "PTM", "organShortName": "Ô tô PTM",
    "publicDate": "2026-08-03T00:00:00",
    "yearReport": 2026, "lengthReport": 2,
    "revenue": 146297369890.0,
    "revenueGrowth": -0.6259779696801286,
    "profit": 3763661387.0,
    "profitGrowth": -0.8009643526712689,
    "rtd21": 54.09339502,
    "rtd25": 0.93522941
  }],
  "status": "Success"
}
```

| Trường | Kiểu | Đơn vị | Mô tả |
|---|---|---|---|
| `publicDate` | string | — | Ngày công bố BCTC |
| `yearReport` | integer | — | Năm báo cáo |
| `lengthReport` | integer | — | `1`..`4` = quý · `5` = cả năm |
| `revenue` | number | VND | Doanh thu kỳ báo cáo |
| `revenueGrowth` | number | thập phân | Tăng trưởng doanh thu so với cùng kỳ |
| `profit` | number | VND | Lợi nhuận |
| `profitGrowth` | number | thập phân | Tăng trưởng lợi nhuận |
| `rtd21` | number | lần | P/E tại thời điểm công bố |
| `rtd25` | number | lần | P/B tại thời điểm công bố |

**Tổng bản ghi: 57.176** — endpoint nhiều dữ liệu nhất nhóm.

⚠️ Thời gian phản hồi **~7,4 s** — chậm nhất trong toàn bộ 43 endpoint. Cần cache và không gọi đồng bộ khi render trang.

---

## `getCorporateIPO`

**Tóm tắt:** Các đợt IPO và niêm yết mới.

```
GET FIIN_MARKET/Calendar/GetCorporateIPO?Page=1&PageSize=20&language=vi
```

### Response 200 — 11 trường

```json
{
  "totalCount": 77,
  "items": [{
    "organCode": "0304941312", "ticker": "XDC",
    "organName": "Xây dựng Công trình Tân Cảng",
    "publicDate": "2022-09-08T00:00:00",
    "listingDate": "2022-10-21T09:00:00",
    "exchange": null,
    "offeringShare": 3279800.0,
    "ipoRatio": 0.0,
    "prices": 15322.0,
    "revenue": 314796320540.0,
    "profit": 9916445679.0
  }],
  "status": "Success"
}
```

| Trường | Kiểu | Đơn vị | Mô tả |
|---|---|---|---|
| `organName` | string | — | Tên đầy đủ |
| `publicDate` / `listingDate` | string | — | Ngày công bố / ngày niêm yết |
| `exchange` | string \| null | — | Sàn niêm yết. Thường `null` |
| `offeringShare` | number | cổ phiếu | Số lượng chào bán |
| `ipoRatio` | number | thập phân | Tỷ lệ IPO |
| `prices` | number | VND | Giá chào bán |
| `revenue` / `profit` | number | VND | Doanh thu / lợi nhuận tại thời điểm IPO |

**Tổng bản ghi: 77** — dữ liệu lịch sử ít nhất nhóm.

---

## `getCorporateShareIssuance`

**Tóm tắt:** Phát hành thêm cổ phiếu.

```
GET FIIN_MARKET/Calendar/GetCorporateShareIssuance?Page=1&PageSize=20&language=vi
```

### Response 200 — 11 trường

```json
{
  "totalCount": 10052,
  "items": [{
    "organCode": "GEN3", "ticker": "PGV",
    "publicDate": "2026-08-04T00:00:00",
    "exrightDate": "2026-08-10T00:00:00",
    "issueDate": "2026-08-10T00:00:00",
    "listingDate": null,
    "issueMethodName": "Cổ phiếu thưởng",
    "exerciseRatio": 0.08,
    "planVolumn": 89877443.0,
    "issueYear": 2026,
    "issueStatusName": "Đã thực hiện xong"
  }],
  "status": "Success"
}
```

| Trường | Kiểu | Đơn vị | Mô tả |
|---|---|---|---|
| `publicDate` / `exrightDate` / `issueDate` / `listingDate` | string \| null | — | Bốn mốc trong quy trình phát hành |
| `issueMethodName` | string | — | Hình thức: `Cổ phiếu thưởng`, `Phát hành riêng lẻ`, `Chào bán cho cổ đông hiện hữu`, `ESOP`… |
| `exerciseRatio` | number | thập phân | Tỷ lệ thực hiện. `0.08` = 8% |
| `planVolumn` | number | cổ phiếu | Khối lượng theo kế hoạch. ⚠️ Tên trường viết là `Volumn` |
| `issueYear` | integer | — | Năm phát hành |
| `issueStatusName` | string | — | Trạng thái: `Đã thực hiện xong`, `Đang thực hiện`… |

**Tổng bản ghi: 10.052**

Dùng để theo dõi pha loãng cổ phiếu.

---

## `getEconomy`

**Tóm tắt:** Lịch sự kiện kinh tế vĩ mô theo tuần.

```
GET FIIN_MARKET/Calendar/GetEconomy?WeekOfYear=33&Year=2026&Page=1&PageSize=50&language=vi
```

### Tham số

| Tên | Vị trí | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|---|
| `WeekOfYear` | query | integer | **bắt buộc** | Tuần trong năm, `1`..`53` |
| `Year` | query | integer | **bắt buộc** | Năm |
| `Page` / `PageSize` | query | integer | *tuỳ chọn* | |
| `KeyWord` | query | string | *tuỳ chọn* | Tìm theo từ khoá |
| `language` | query | string | *tuỳ chọn* | |

### Response 200 — 10 trường

```json
{
  "items": [{
    "eventTitle": "...",
    "levelName": "Cao",
    "recentValue": "...",
    "forecastValue": "...",
    "previousValue": "...",
    "unitCode": "...",
    "sourceUrl": "...",
    "newsSourceLink": "...",
    "newsId": 12345,
    "issueDateFrom": "2026-08-12T00:00:00"
  }],
  "status": "Success"
}
```

| Trường | Kiểu | Mô tả |
|---|---|---|
| `eventTitle` | string | Tên sự kiện vĩ mô |
| `levelName` | string | Mức ảnh hưởng: `Thấp` \| `Trung bình` \| `Cao` |
| `recentValue` | string | Giá trị công bố gần nhất |
| `forecastValue` | string | Giá trị dự báo |
| `previousValue` | string | Giá trị kỳ trước |
| `unitCode` | string | Đơn vị đo |
| `issueDateFrom` | string | Ngày diễn ra |
| `sourceUrl` / `newsSourceLink` / `newsId` | string / integer | Liên kết tới nguồn |

### Ghi chú
Số sự kiện mỗi tuần rất ít — tuần 33/2026 chỉ có **2 sự kiện**. Đây là lịch vĩ mô Việt Nam, không phải lịch kinh tế toàn cầu.

---

## `getCalendarWatchList`

**Tóm tắt:** Sự kiện doanh nghiệp gộp chung mọi loại, dạng dòng thời gian.

```
GET FIIN_MARKET/Calendar/GetCalendarWatchList?Page=1&PageSize=50&language=vi
```

### Tham số

| Tên | Vị trí | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|---|
| `Page` / `PageSize` | query | integer | *tuỳ chọn* | |
| `WatchlistType` | query | string | *tuỳ chọn* | Ví dụ `CompanyGroup` |
| `WatchListId` | query | integer | *tuỳ chọn* | ID danh mục |
| `language` | query | string | *tuỳ chọn* | |

### Response 200 — 10 trường

```json
{
  "totalCount": 190143,
  "items": [{
    "eventId": 123456,
    "organCode": "BID", "ticker": "BID",
    "eventTitle": "...",
    "publicDate": "...",
    "recordDate": "...",
    "exrightDate": "...",
    "exerciseDate": "...",
    "sourceUrl": "...",
    "eventListCode": "..."
  }],
  "status": "Success"
}
```

| Trường | Kiểu | Mô tả |
|---|---|---|
| `eventId` | integer | Định danh sự kiện |
| `organCode` / `ticker` | string | Doanh nghiệp |
| `eventTitle` | string | Mô tả sự kiện |
| `publicDate` / `recordDate` / `exrightDate` / `exerciseDate` | string | Các mốc thời gian |
| `eventListCode` | string | **Mã loại sự kiện** — dùng để lọc/nhóm |
| `sourceUrl` | string | Link công bố gốc |

### Ghi chú
**190.143 bản ghi** — lớn nhất toàn hệ thống. Đây là bảng gộp của mọi loại sự kiện, thay thế cho việc gọi lần lượt 6 endpoint `GetCorporate*` khi chỉ cần dòng thời gian tổng hợp. Ngược lại, nếu cần trường chuyên biệt (tỷ lệ cổ tức, khối lượng phát hành…) thì phải dùng endpoint chuyên biệt.

⚠️ Thời gian phản hồi ~3,65 s với `PageSize=50`.

---

## `PageSize` không có trần — đo 2026-09-03

Bảng tham số dùng chung ở trên đã ghi "không có whitelist" cho `PageSize` của nhóm `GetCorporate*` — đo lại 2026-09-03 xác nhận bằng số: nguồn trả `min(PageSize, số bản ghi còn lại)`, không cắt, không báo lỗi, đã thử tới `PageSize=20.000`.

**Tải trọn cả sáu họ `GetCorporate*` = 9 lời gọi, ~140 giây.** Riêng `getCorporateEarning` — họ nặng nhất, 57.026 bản ghi — ở `PageSize=20.000` mất **~36 giây mỗi trang, ~3,1 MB mỗi 10.000 bản ghi**, cần 3 trang để lấy trọn.

---

## 🔴 Trục lọc `FromDate` — đo 2026-09-03

`FromDate`/`ToDate` được liệt trong bảng tham số dùng chung ở trên là "Hoạt động đúng" — đúng theo nghĩa API không báo lỗi và trả về ít bản ghi hơn. Nhưng **mỗi họ lọc theo một trục ngày khác nhau**, và với `Earning` thì trục đó **không phải trường nào có trong response**.

Phép kiểm: tải trọn một họ, so **tập bản ghi** API trả cho một cửa sổ `FromDate`/`ToDate` với tập suy ra từ từng trường ngày trong bản ghi. Trục đúng phải cho **tập bằng nhau**, không phải "nằm trong".

| Họ | Trục lọc thật | Bằng chứng |
|---|---|---|
| `CashDividend` | **`payoutDate`** | 3 cửa sổ, 25/25 bản ghi khớp; `publicDate` 0/25 |
| `StockDividend` | **`payoutDate`** | cửa sổ 2026-05-25..29: chỉ `payoutDate` cho tập bằng nhau (7/7) |
| `ShareIssuance` | **`issueDate`** | 2 cửa sổ, 10/10 khớp; `exrightDate` chỉ 6/10 |
| `AGM` | **`publicDate`** | 219/219 trong cửa sổ 2026-03-10..14 |
| `IPO` | `publicDate` | mẫu chỉ 1 bản ghi — **chưa đủ để khẳng định** |
| `Earning` | **không phải trường nào có trong response** | xem bảng dưới |

🔴 **Trục SẮP XẾP lại là trục khác nữa, không phải trục lọc.** 100 bản ghi đầu của `AGM` · `CashDividend` · `StockDividend` · `ShareIssuance` sắp giảm dần theo **`exrightDate`** — không theo trục lọc ở trên, cũng không theo `publicDate`. `IPO` sắp giảm dần theo `publicDate`. `Earning` không sắp theo trường nào quan sát được.

### Earning: cửa sổ `FromDate` bỏ sót phần lớn dữ liệu

| Cửa sổ | API trả | Bản ghi thật có `publicDate` trong cửa sổ | Giao | API trả mà ngoài cửa sổ | Trong cửa sổ mà API KHÔNG trả |
|---|---|---|---|---|---|
| 2026-03-10..14 | 24 | 217 | 22 | 2 | **195** |
| 2025-11-03..07 | 83 | 80 | 75 | 8 | 5 |
| 2026-08-01..05 | 135 | 116 | 100 | 35 | 16 |

Hai tập **cắt nhau**, không tập nào chứa tập nào ⇒ trục lọc của `Earning` là một trường không có trong response (nhiều khả năng là ngày dự kiến công bố hoặc dấu thời gian cập nhật bản ghi).

**Hệ quả thiết kế:** lấy phần mới bằng `FromDate` cho họ `Earning` sẽ **mất im lặng tới 90% bản ghi** của cửa sổ đó. Tải trọn `Earning` chỉ tốn 3 lời gọi ở `PageSize=20.000` — xem mục trên.

---

## 🔴 Độ ĐẦY ĐỦ của lịch — đo 2026-09-03 bằng nguồn độc lập

> Câu hỏi *"lịch có sót không"* **không trả lời được từ chính lịch**. Ba phép đo dưới đây đối chiếu lịch với một nguồn khác của cùng sự kiện.

| Họ | Đối chiếu với | Mẫu | Độ phủ | Chỗ sót |
|---|---|---|---|---|
| `getCorporateCashDividend` | `CashDividendAnalysis/GetAnalysis` — lịch sử chi trả từng DN | 10 mã · 291 bản ghi | **98,6 %** | 2 sót thật: HPG 2016-03 · **SSI 2026-08 (THÁNG TRƯỚC)** |
| `getCorporateEarning` | kỳ báo cáo thật trong `GetIncomeStatement` | 6 mã · 336 kỳ | **96,4 %** | 12 sót thật — **tất cả ≤ 2022; từ 2023 tới nay 0 sót** |
| `getCorporateShareIssuance` | `getCorporateStockDividend` (mọi CP thưởng phải có ở cả hai) | 5 mã | **100 %** | không |

**Ba kết luận cho người thiết kế ETL:**

1. **Lịch KHÔNG đầy đủ tuyệt đối.** Tỷ lệ sót 0–3,6 % tuỳ họ. Kiến trúc chỉ dựa vào trigger từ lịch sẽ **mất im lặng** đúng bằng tỷ lệ đó.
2. **Sót của `Earning` là lỗ backfill lịch sử, không phải feed hỏng** — không kỳ nào từ 2023 tới nay bị sót trên 6 mã. Trigger theo `Earning` vì thế đáng tin *cho tương lai*, nhưng đừng dùng lịch để dựng lại quá khứ.
3. 🔴 **`CashDividend` có sót ở vùng GẦN ĐÂY** (SSI, đợt tháng 8/2026, kiểm 2026-09-03: lịch dừng ở 2025-09-25, không có bản ghi `exrightDate` rỗng nào). Không phân biệt được "trễ vài tuần" với "sót hẳn" nếu không đợi thêm — nhưng **trễ cũng đủ làm trigger bắn muộn**.

⚠️ **Nguồn đối chiếu cũng không sạch:** `GetAnalysis` trả `exrightYear = 1753` (giá trị mốc tối thiểu của SQL Server) cho GMD và PNJ — tức bản ghi không có ngày chốt quyền. Nên **không nguồn nào là chuẩn tuyệt đối**; đối chiếu chéo hai chiều mới ra sự thật. Đây là việc của bộ giám sát hợp đồng dữ liệu.

**Ranh giới phủ:** kỳ `(2015, 1)` vắng ở cả 6/6 mã ⇒ lịch bắt đầu từ giữa 2015, không phải sót.

---

## Tổng hợp độ phủ nhóm Calendar

| Endpoint | Bản ghi lịch sử *(đo ~2026-08-10)* | Đo 2026-09-03 | Chênh | Thời gian | Ổn định |
|---|---|---|---|---|---|
| `getCorporateEarning` | 57.176 | 57.026 | **−150** | ~7,4 s | ✅ |
| `getCorporateAGM` | 23.434 | 23.467 | +33 | ~740 ms | ✅ |
| `getCorporateCashDividend` | 17.884 | 17.970 | +86 | ~800 ms | ✅ |
| `getCorporateShareIssuance` | 10.052 | 10.097 | +45 | ~750 ms | ✅ |
| `getCorporateStockDividend` | 2.086 | 2.100 | +14 | ~1,0 s | ✅ |
| `getCorporateIPO` | 77 | 77 | 0 | ~1,4 s | ✅ |
| `getCalendarWatchList` | 190.143 | *(chưa đo lại)* | — | ~3,65 s | ✅ |
| `getEconomy` | 2 / tuần | *(chưa đo lại)* | — | ~520 ms | ✅ |

⚠️ **`totalCount` trôi cả hai chiều theo thời gian** — `Earning` **giảm** 150 bản ghi trong 24 ngày trong khi năm họ kia tăng. Không được giả định tổng số chỉ tăng; chốt chặn kiểu "sụt quá X% thì từ chối" vẫn dùng được, nhưng ngưỡng phải cho phép trôi cả hai hướng.

Gọi lặp hai lần cho kết quả **byte-identical** — dữ liệu ổn định, cache được.

## Endpoint đã loại

`Calendar/GetCorporateListing` — trả `200` với `items: []` trên mọi tham số thử nghiệm.
