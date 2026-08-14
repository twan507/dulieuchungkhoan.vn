# 08 — Lịch sự kiện

Base URL: `https://wlgw-market.fiintrade.vn/Calendar` — ký hiệu `FIIN_MARKET`
Header bắt buộc: `Origin: https://fiinapp.bvsc.com.vn`

8 endpoint. Nguồn gốc dữ liệu là **VSD và các Sở giao dịch** — đây là dữ kiện thô, không phải phân tích của FiinTrade. Trường `sourceUrl` trỏ thẳng về bản công bố gốc.

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

## Tổng hợp độ phủ nhóm Calendar

| Endpoint | Bản ghi lịch sử | Thời gian | Ổn định |
|---|---|---|---|
| `getCorporateEarning` | 57.176 | ~7,4 s | ✅ |
| `getCorporateAGM` | 23.434 | ~740 ms | ✅ |
| `getCorporateCashDividend` | 17.884 | ~800 ms | ✅ |
| `getCorporateShareIssuance` | 10.052 | ~750 ms | ✅ |
| `getCorporateStockDividend` | 2.086 | ~1,0 s | ✅ |
| `getCorporateIPO` | 77 | ~1,4 s | ✅ |
| `getCalendarWatchList` | 190.143 | ~3,65 s | ✅ |
| `getEconomy` | 2 / tuần | ~520 ms | ✅ |

Gọi lặp hai lần cho kết quả **byte-identical** — dữ liệu ổn định, cache được.

## Endpoint đã loại

`Calendar/GetCorporateListing` — trả `200` với `items: []` trên mọi tham số thử nghiệm.
