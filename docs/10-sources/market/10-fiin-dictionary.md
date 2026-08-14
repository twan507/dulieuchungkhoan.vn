# 10 — Từ điển mã trường & Bộ sàng lọc

Base URL: `https://wlgw-tools.fiintrade.vn` — ký hiệu `FIIN_TOOLS`
Header bắt buộc: `Origin: https://fiinapp.bvsc.com.vn`

2 endpoint.

---

## `getScreenerParameters`

**Tóm tắt:** Danh mục 83 tiêu chí tài chính kèm mã, tên tiếng Việt, đơn vị và dải giá trị toàn thị trường.

**Mô tả:** Endpoint này thiết kế cho tính năng bộ lọc cổ phiếu, nhưng giá trị thực tế lớn hơn thế: **nó là bảng giải mã mã trường FiinGroup**. Dữ liệu FiinTrade trả về khắp nơi dùng mã viết tắt (`rtq12`, `rtd21`, `rqq25`…) mà không kèm giải thích. Endpoint này ánh xạ chúng sang tên có nghĩa và đơn vị.

Nên gọi và cache dù không xây tính năng screener.

```
GET FIIN_TOOLS/Screener/GetScreenerParameters?language=vi
```

### Tham số

| Tên | Vị trí | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|---|
| `language` | query | string | *tuỳ chọn* | `vi` \| `en`. Ảnh hưởng trường `name` |

### Response 200

```json
{
  "items": [
    {
      "name": "Chỉ số khả năng sinh lời",
      "code": "ProfitabilityRatio",
      "parameters": [
        {
          "name": "ROE (TTM)",
          "code": "Rtq12",
          "type": "Range",
          "selectedValue": null,
          "valueRange": [-127.56331573, 7.85938948],
          "unit": "Percentage"
        }
      ]
    }
  ],
  "status": "Success"
}
```

#### Cấp nhóm

| Trường | Kiểu | Mô tả |
|---|---|---|
| `name` | string | Tên nhóm tiêu chí, đã dịch |
| `code` | string | Mã nhóm, ví dụ `ProfitabilityRatio` |
| `parameters` | array | Danh sách tiêu chí thuộc nhóm |

#### Cấp tiêu chí

| Trường | Kiểu | Mô tả |
|---|---|---|
| `name` | string | **Tên tiêu chí bằng tiếng Việt** |
| `code` | string | **Mã trường** — chữ đầu viết hoa (`Rtq12`), tương ứng `rtq12` trong dữ liệu trả về |
| `type` | string | Kiểu bộ lọc, quan sát thấy `Range` |
| `selectedValue` | null | Giá trị đang chọn — luôn `null` khi chưa lọc |
| `valueRange` | number[2] | **[min, max] toàn thị trường** của tiêu chí đó |
| `unit` | string | Đơn vị: `VND` \| `Percentage` \| `ThousandUnit` \| `Times`… |

### 13 nhóm / 83 tiêu chí

| Nhóm | Mã nhóm | Số tiêu chí |
|---|---|---|
| Giá | `Price` | 8 |
| Khối lượng & Biến động | `VolumeNVolatility` | 7 |
| Giá trị GD | `TradingValue` | 5 |
| Chỉ tiêu FiinTrade | `FiinTradeIndicators` | 7 |
| Chỉ số định giá thị trường | `MarketRatio` | 8 |
| Doanh thu & lợi nhuận | `RevenueProfit` | 6 |
| Chỉ số tăng trưởng | `GrowthRatio` | 9 |
| Chỉ số khả năng sinh lời | `ProfitabilityRatio` | 11 |
| Cơ cấu tài chính | `EquityStructure` | 4 |
| Chỉ số thanh toán | `LiquidityRatio` | 4 |
| Sở hữu | `Ownership` | 3 |
| Cổ Tức | `Dividends` | 4 |
| Chỉ Số Kĩ Thuật | `TechnicalIndicators` | 7 |

Bảng đầy đủ `code → name → unit`: [Phụ lục A](appendix-A-field-codes.md#a3-bảng-tra-83-tiêu-chí-từ-getscreenerparameters).

### Ghi chú

- ⚠️ **Chênh lệch hoa/thường:** endpoint này trả `Rtq12`, `Rqq25`, `Ryq29`; các endpoint dữ liệu trả `rtq12`, `rqq25`, `ryq29`. Phải chuẩn hoá về chữ thường khi tra.
- `valueRange` phản ánh dải giá trị thực của toàn thị trường tại thời điểm gọi. Có thể dùng để đặt giới hạn slider hoặc phát hiện giá trị bất thường.
- Bảng này **không phủ** các mã chỉ tiêu báo cáo tài chính chi tiết (`bsa*`, `isa*`, `isb*`, `cfa*`, `nob*`). Chúng được giải mã bằng nguồn khác — xem [Phụ lục A §A.5](appendix-A-field-codes.md), 729 mã lấy từ bundle JS của ứng dụng FiinTrade, độ phủ 100%.

### Độ phủ & hiệu năng
13 nhóm · 83 tiêu chí · 13,6 KB · ~1,45 s. Cache dài hạn.

---

## `getScreenerItems`

**Tóm tắt:** Sàng lọc toàn thị trường theo 83 tiêu chí — **chạy phía server**, trả 223 trường mỗi mã.

**Mô tả:** Endpoint duy nhất trong toàn hệ thống có khả năng **truy vấn cắt ngang thị trường**. Mọi endpoint khác chỉ trả dữ liệu của một mã hoặc một nhóm cố định; endpoint này nhận điều kiện lọc và quét toàn bộ 1.517 mã ở phía FiinTrade.

Đây là công cụ thay thế cho việc tự dựng kho dữ liệu khi cần trả lời câu hỏi kiểu *"những mã nào có ROE trên 20% và P/E dưới 10"*.

```
POST FIIN_TOOLS/Screener/GetScreenerItems?language=vi
Content-Type: application/json
```

### Body

```json
{
  "comGroupCode": "ALL",
  "icbCode": "ALL",
  "parameters": [ { ...đối tượng tiêu chí, có selectedValue... } ],
  "page": 1,
  "pageSize": 30
}
```

| Trường | Kiểu | Bắt buộc | Giá trị |
|---|---|---|---|
| `comGroupCode` | string | **bắt buộc** | `ALL` \| `HOHAUP` \| `VNINDEX` \| `HNXIndex` \| `UpcomIndex` \| `VN30` |
| `icbCode` | string | **bắt buộc** | `ALL` \| `0` \| mã ngành ICB bất kỳ cấp (`8000` L1, `8300` L3, `8350` L4) |
| `parameters` | array | **bắt buộc** | Danh sách tiêu chí — xem dưới. Mảng rỗng trả 0 kết quả |
| `page` | integer | **bắt buộc** | ≥ 1 |
| `pageSize` | integer | **bắt buộc** | `enum`: **chỉ `30`** |

⚠️ **Cả `comGroupCode` và `icbCode` đều bắt buộc.** Thông báo lỗi `"ComGroupCode or IcbCode is not supplied."` dùng chữ *or* nhưng thực tế cần cả hai.

⚠️ `pageSize` chỉ nhận **`30`**. Đã thử 10, 15, 20, 25, 50, 60, 100 — đều `status: "Failed"` với `"PageSize or Page is invalid"`.

🔴 **Gửi nhiều tiêu chí một lúc sẽ timeout phía server.** 79 tiêu chí → `status: "Failed"` kèm lỗi Redis timeout của chính FiinTrade *(`Timeout performing GET (5000ms) … serverEndpoint: 192.168.1.232:6379`)*. 1 tiêu chí → chạy ngay.

Response trả **đủ 223 trường mỗi mã bất kể gửi bao nhiêu tiêu chí**, nên cách dùng đúng là **gửi một tiêu chí duy nhất** với `selectedValue = valueRange` của chính nó:

```json
{ "comGroupCode": "VN30", "icbCode": "ALL", "page": 1, "pageSize": 30,
  "parameters": [ { "code": "ClosePrice", "type": "Range", "unit": "VND",
                    "valueRange": [100.0, 614345.0], "selectedValue": [100.0, 614345.0] } ] }
```

### Cấu trúc phần tử `parameters`

Lấy nguyên đối tượng tiêu chí từ [`getScreenerParameters`](#getscreenerparameters), gán thêm `selectedValue` là mảng `[min, max]`:

```json
{
  "name": "ROE (TTM)",
  "code": "Rtq12",
  "type": "Range",
  "selectedValue": [0.20, 7.85938948],
  "valueRange": [-127.56331573, 7.85938948],
  "unit": "Percentage"
}
```

⚠️ **`selectedValue` phải là mảng `[min, max]`**, không phải object `{from, to}` (dạng này trả `HTTP 400`).

⚠️ **Thang đơn vị theo dữ liệu thô, không theo `unit`.** Trường `unit` ghi `Percentage` nhưng `valueRange` của ROE là `[-127,56 · 7,86]` — tức thang **thập phân** (`0.20` = 20%), không phải `[0, 100]`. Luôn tham chiếu `valueRange` để biết thang thật.

Không lọc theo một tiêu chí thì đặt `selectedValue` bằng đúng `valueRange` của nó.

### Response 200

```json
{
  "totalCount": 1517,
  "items": [{
    "priceInfo":         { ...43 trường... },
    "stockScreenerItem": { ...129 trường... },
    "performance":       { ...12 trường... },
    "financial":         { ...21 trường... },
    "technical":         { ...18 trường... }
  }],
  "status": "Success"
}
```

**223 trường mỗi mã**, chia 5 khối:

| Khối | Số trường | Nội dung |
|---|---|---|
| `priceInfo` | 43 | Giá đầy đủ: OHLC, trần/sàn/tham chiếu, khớp lệnh, thoả thuận, khối ngoại |
| `stockScreenerItem` | **129** | Chỉ báo tổng hợp: `ma9` `ma20` `ma50` `ma75` `ma100` `ma200` `sma50` `overSma50`, KLGD, GTGD… |
| `performance` | 12 | Hiệu suất 11 mốc: 1 ngày · 1 tuần · 2 tuần · 1/2/3/6/9 tháng · 1 năm · YTD · 52 tuần |
| `financial` | 21 | `rtd7` `rtd11` `rtd14` `rtd19` `rtd21` `rtd25` `rtd39` `rtd51` `rtd53` `rtd54` `rtq12` `rtq81` `rtq27`… |
| `technical` | 18 | `sma20` `sma50` `sma100` `rsi`, OHLC 2 phiên gần nhất |

### Độ rộng đã kiểm chứng

| `comGroupCode` | `icbCode` | Số mã |
|---|---|---|
| `ALL` | `ALL` | **1.517** — toàn thị trường |
| `HOHAUP` | `ALL` | 1.517 |
| `VNINDEX` | `ALL` | 404 |
| `VNINDEX` | `8000` (L1 Tài chính) | 85 |
| `VNINDEX` | `8350` (L4 Ngân hàng) | 22 |
| `HNXIndex` | `8000` | 34 |
| `UpcomIndex` | `8000` | 66 |
| `VN30` | `8000` | 5 |

### Ví dụ hoàn chỉnh

Lọc ROE ≥ 20% và P/E ≤ 10 trên toàn thị trường:

```json
{
  "comGroupCode": "ALL", "icbCode": "ALL", "page": 1, "pageSize": 30,
  "parameters": [
    { "code": "Rtq12", "type": "Range", "unit": "Percentage",
      "valueRange": [-127.56331573, 7.85938948], "selectedValue": [0.20, 7.85938948] },
    { "code": "Rtd21", "type": "Range", "unit": "Unit",
      "valueRange": [-4972.336, 5058595.397], "selectedValue": [-4972.336, 10] }
  ]
}
```

Kết quả: **237 mã**, 2,4 giây. Ví dụ `ABT` (HOSE) ROE 24,66% P/E 4,02 P/B 0,87 · `TOS` (UPCOM) ROE 52,59% P/E 6,96.

### Hiệu năng

| Truy vấn | Thời gian |
|---|---|
| Toàn thị trường, 1 tiêu chí không lọc | ~682 ms |
| Toàn thị trường, 2 tiêu chí lọc thật | ~2,4 s |
| Một ngành | < 500 ms |

Với `pageSize=30` cố định, lấy hết 1.517 mã cần **51 lời gọi**.

### Ghi chú
`Screener/DownloadScreenerItems` dùng cùng body, trả file xuất — chưa kiểm thử.

### Dùng bao nhiêu trong 223 trường

⚠️ Đo lại ngày 2026-08-14 trên VN30 chỉ thấy **193 trường** — chênh 30 so với con số 223 đo hồi 2026-08-10. Nhiều khả năng 30 trường kia chỉ xuất hiện ở một số loại hình doanh nghiệp không có trong VN30. Con số dưới đây tính trên 193 trường quan sát được.

Finext chỉ lưu **80/193 trường**. 113 trường bị bỏ vì trùng BVSC, trùng BCTC, hoặc tính lại được từ giá; 20 trường nhóm chấm điểm bỏ theo quyết định của chủ dự án; số còn lại là metadata không dùng.

Phần giữ lại là **55 mã tỷ số tài chính không nguồn nào khác có** (P/S, Giá/Dòng tiền, nhóm cổ tức, nhóm đòn bẩy, nhóm tăng trưởng), Beta, hai chỉ tiêu sở hữu tổ chức, và trọn cụm TTM/Y.

Danh sách lấy/bỏ và lý do tới từng mã: [chọn trường cho ETL thị trường](../../20-design/market-field-selection.md).

⚠️ **`isa20ttm` không bằng tổng 4 quý `isa20`** — lệch tới 9,4%. Screener dùng *lợi nhuận sau thuế của cổ đông công ty mẹ*, còn `isa20` trong BCTC là *lợi nhuận thuần* gồm cả lợi ích cổ đông thiểu số. Và `P/E = vốn hoá ÷ isa20ttm` khớp 9/10 mã VN30, nên đây chính là mẫu số FiinTrade dùng. Đừng tự tính lại.
