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

- 🔴 **Chênh lệch hoa/thường — chỉ hạ CHỮ CÁI ĐẦU, không viết thường toàn bộ** *(đo lại 2026-08-15)*. Endpoint này trả hoa chữ đầu (`Rtq12`, `ForeignerRoom`, `AverageValue1Week`); `getScreenerItems` trả `rtq12`, `foreignerRoom`, `averageValue1Week` — tức **chỉ chữ cái đầu bị hạ, phần sau giữ nguyên**. Với mã dạng `Rtq12` thì hai cách chuẩn hoá cho kết quả giống nhau nên lỗi này ẩn rất lâu; với 31 tiêu chí có tên tiếng Anh thì viết thường toàn bộ sẽ **trượt khoá**. Đã đối chiếu thật ngày 2026-08-15: hạ chữ cái đầu → **83/83 tiêu chí khớp** khoá response; viết thường toàn bộ → **trượt 31/83**.
- `valueRange` phản ánh dải giá trị thực của toàn thị trường tại thời điểm gọi. Có thể dùng để đặt giới hạn slider hoặc phát hiện giá trị bất thường.
- Bảng này **không phủ** các mã chỉ tiêu báo cáo tài chính chi tiết (`bsa*`, `isa*`, `isb*`, `cfa*`, `nob*`). Chúng được giải mã bằng nguồn khác — xem [Phụ lục A §A.5](appendix-A-field-codes.md), 729 mã lấy từ bundle JS của ứng dụng FiinTrade, độ phủ 100%.

### Độ phủ & hiệu năng
13 nhóm · 83 tiêu chí · 13,6 KB. Cache dài hạn.

*Đo lại 2026-08-15: đúng 13 nhóm / 83 tiêu chí, 13.597 byte, `status: "Success"` — phân bố theo nhóm không đổi một tiêu chí nào so với bản 2026-08-10.*

**Thời gian — hai lần đo cùng ngày 2026-08-15 lệch nhau hơn hai lần:**

| Lần đo | Thời gian |
|---|---|
| Lần đo sớm hơn trong ngày | **6,33 s** |
| Trong [phép đo rate limit](00-conventions.md), cùng ngày | **2,77 s** |
| Bản 2026-08-10 | ~1,45 s |

⚠️ Mỗi con số vẫn là **một lần chạy**. Nhưng đặt cạnh 52 mẫu của [`getScreenerItems`](#getscreeneritems) — cũng dao động rộng trong cùng ngày — thì cách đọc hợp lý là **tải máy chủ dao động theo thời điểm**, không phải endpoint đã chậm đi hẳn. Đây là endpoint cache dài hạn nên ngân sách thời gian của nó không quan trọng; đừng dùng bất kỳ con số nào ở đây làm SLA.

---

## `getScreenerItems`

**Tóm tắt:** Sàng lọc toàn thị trường theo 83 tiêu chí — **chạy phía server**, trả **193 trường phân biệt** mỗi mã, trải trên 5 khối cộng lại 223 lượt.

**Mô tả:** Endpoint duy nhất trong toàn hệ thống có khả năng **truy vấn cắt ngang thị trường**. Mọi endpoint khác chỉ trả dữ liệu của một mã hoặc một nhóm cố định; endpoint này nhận điều kiện lọc và quét toàn bộ thị trường ở phía FiinTrade — `totalCount` đo ngày 2026-08-15 với `comGroupCode=ALL` là **1.549 mã** *(2026-08-10 đo được 1.517)*.

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

Response trả **đủ bộ trường mỗi mã bất kể gửi bao nhiêu tiêu chí**, nên cách dùng đúng là **gửi một tiêu chí duy nhất** với `selectedValue = valueRange` của chính nó:

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
  "totalCount": 1549,
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

> 🔴 **Đo lại 2026-08-28 (sau phiên) và 2026-09-03 (08:38, trước mở cửa)** — response thật lưu ở [`samples/`](../../90-records/plans/2026-09-03-screener-daily-etl/samples/):
> - Tầng đỉnh còn **`page`, `pageSize`, `packageId`, `errors`** ngoài ba khoá trên; `totalCount` = **1.545** ở cả hai lần *(1.549 là số 2026-08-15)*.
> - `priceInfo.tradingDate` là **timestamp riêng từng mã** — sau phiên 28/08 có 29 giá trị khác nhau trên 30 mã, 14:45–15:00. Lấy ngày thì phải cắt `::date`.
> - **Trước mở cửa, `tradingDate` đã mang ngày hôm nay** (`2026-09-03T08:22:46`) với `closePrice = 0`, `matchVolume = 0`, `totalVolume = 0`, `referenceDate = 2026-08-28` *(⇒ HOSE nghỉ 31/08–02/09)*. Ngày không giao dịch nguồn vẫn đóng dấu ngày đó — **không được dùng `tradingDate` làm bằng chứng có phiên**; tín hiệu dùng được là `closePrice > 0` (30/30 sau phiên vs 0/30 trước mở cửa). `totalVolume` không dùng được: 10/30 mã = 0 ngay trong ngày có phiên.
> - `marketStatus` = `null` ở cả hai lần — vô dụng. Một khối có thể **`null` nguyên khối** (`V68.technical`). 20,1% giá trị trong khối là `null`.
> - Tỷ số tài chính **đổi giữa hai lần** (103 + 733 giá trị) dù không có phiên nào ở giữa — *"payload trùng lượt trước"* không phải tín hiệu ngày nghỉ.

**193 trường phân biệt mỗi mã**, chia 5 khối cộng lại 223 lượt:

| Khối | Số trường | Nội dung |
|---|---|---|
| `priceInfo` | 43 | Giá đầy đủ: OHLC, trần/sàn/tham chiếu, khớp lệnh, thoả thuận, khối ngoại. Có `atoPrice` / `atoVolume`, **không có khoá ATC nào** |
| `stockScreenerItem` | **129** | Chỉ báo tổng hợp: `ma9` `ma20` `ma50` `ma75` `ma100` `ma200` `sma50` `overSma50`, KLGD, GTGD… |
| `performance` | 12 | Hiệu suất 11 mốc: 1 ngày · 1 tuần · 2 tuần · 1/2/3/6/9 tháng · 1 năm · YTD · 52 tuần |
| `financial` | 21 | `organCode` `rtd7` `rtd11` `rtd14` `rtd19` `rtd21` `rtd25` `rtd39` `rtd51` `rtd53` `rtd54` `rtq12` `rtq81` `rtq27` `rtq83` `isa3` `isa5` `isa20` `isa22` `cfa18` `fryq30` — **danh sách đủ, đo 2026-08-15** |
| `technical` | 18 | `sma20Past4` `sma20` `sma50` `sma100` `rsi` `cmf` `roc` `rs6m` `rs52w`, OHLC 2 phiên gần nhất |

> ### 🔴 223 hay 193? — cả hai, và không mâu thuẫn *(đo 2026-08-15)*
> `43 + 129 + 12 + 21 + 18 = 223` là **tổng kích thước 5 khối**. Nhưng **27 khoá nằm ở từ hai khối trở lên**, dư đúng 30 lượt, nên số khoá **phân biệt** chỉ là **193**. Đo trên `comGroupCode=ALL` và `VN30` đều ra 193 — tức chênh lệch **không** phải do loại hình doanh nghiệp như phỏng đoán trước đây.
>
> `organCode` có mặt ở **cả 5 khối**. Lặp ở 2 khối: `closePrice` `ticker` `totalMatchVolume` `totalMatchValue` *(`priceInfo` ↔ `stockScreenerItem`)* · `percentPriceChange1Day/1Week/1Month/3Month/6Month/52Week/YTD` *(`stockScreenerItem` ↔ `performance`)* · `rsi` `roc` `rs6m` `rs52w` `sma50` *(`stockScreenerItem` ↔ `technical`)* · `rtd7` `rtd11` `rtd14` `rtd19` `rtd21` `rtd25` `rtd51` `rtq12` `rtq27` `rtq83` *(`stockScreenerItem` ↔ `financial`)*.
>
> **Hệ quả khi triển khai:** làm phẳng 5 khối vào một bản ghi thì 27 khoá này sẽ đè lên nhau. Phải giữ tiền tố khối, hoặc chọn khối ưu tiên một cách có chủ ý.

### Độ rộng đã kiểm chứng

| `comGroupCode` | `icbCode` | Số mã |
|---|---|---|
| `ALL` | `ALL` | **1.549** — toàn thị trường *(đo lại 2026-08-15; 2026-08-10 là 1.517)* |
| `HOHAUP` | `ALL` | 1.517 *(đo 2026-08-10, chưa đo lại)* |
| `VNINDEX` | `ALL` | 404 |
| `VNINDEX` | `8000` (L1 Tài chính) | 85 |
| `VNINDEX` | `8350` (L4 Ngân hàng) | 22 |
| `HNXIndex` | `8000` | 34 |
| `UpcomIndex` | `8000` | 66 |
| `VN30` | `8000` | 5 |

*Chỉ dòng `ALL`/`ALL` được đo lại ngày 2026-08-15. Các dòng còn lại là số đo 2026-08-10 và chưa đo lại — nếu toàn thị trường đã tăng 1.517 → 1.549 thì các lát cắt con nhiều khả năng cũng đổi.*

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

| Truy vấn | Thời gian | Nguồn số |
|---|---|---|
| Toàn thị trường (`ALL`), 1 tiêu chí không lọc | **trung vị 2,07 s** · min 1,08 · p90 2,68 · max 3,10 | **52 mẫu**, đo 2026-08-15 trong [phép đo rate limit](00-conventions.md) |
| — *cùng truy vấn, lần đo sớm hơn trong ngày* | 6,44 s | đo 2026-08-15, **1 lần chạy** *(2026-08-10: ~682 ms)* |
| `VN30`, 1 tiêu chí không lọc | **4,98 s** | đo 2026-08-15, **1 lần chạy** |
| Toàn thị trường, 2 tiêu chí lọc thật | ~2,4 s | đo 2026-08-10, chưa đo lại |
| Một ngành | < 500 ms | đo 2026-08-10, chưa đo lại |

✅ **Câu hỏi "endpoint chậm đi thật hay chỉ gặp một lần tải cao" nay đã có đáp án: là tải cao nhất thời.** Con số 6,44 s là **một điểm dữ liệu của lần đo sớm hơn trong ngày**; 52 mẫu đo sau đó cùng ngày cho **trung vị 2,07 s**, dải min 1,08 – max 3,10 s, **không có xu hướng chậm dần** giữa trang 1 và trang 52. Dùng trung vị 2,07 s làm ngân sách thời gian, không dùng 6,44 s.

⚠️ Vẫn **chậm hơn hẳn ~682 ms đo 2026-08-10** — khoảng gấp ba. Đừng dựng SLA trên con số cũ đó nữa.

Với `pageSize=30` cố định, lấy hết **1.549** mã cần **52 lời gọi** *(đo 2026-08-15)*. Ngân sách thời gian thật cho cả 52 lời gọi chạy tuần tự: **1 phút 49 giây**, đo trực tiếp chứ không suy ra từ latency đơn lẻ — chi tiết ở [`00-conventions.md` §10](00-conventions.md).

### Ghi chú
`Screener/DownloadScreenerItems` dùng cùng body, trả file xuất — chưa kiểm thử.

🔴 **Bẫy tên ngược: `foreignerRoom` là room CÒN LẠI, không phải tổng room** *(đo 2026-08-15 trên BID · FPT · VNM)*. Khoá `foreignerRoom` của khối `stockScreenerItem` trùng nghĩa với `foreignRemain` của BVSC, **không phải** `foreignRoom` — dù tên gần giống hệt `foreignRoom`. Tổng room nằm ở khoá khác, trong khối `priceInfo`: `foreignTotalRoom`.

| Mã | `stockScreenerItem.foreignerRoom` | `priceInfo.foreignTotalRoom` | BVSC `foreignRemain` | BVSC `foreignRoom` |
|---|---:|---:|---:|---:|
| BID | 906.709.318 | 2.184.019.563 | 906.101.718 | 2.184.019.563 |
| FPT | 371.145.103 | 840.019.946 | 368.745.271 | 840.019.946 |
| VNM | 1.053.172.430 | 2.089.955.445 | 1.052.456.494 | 2.089.955.445 |

`foreignTotalRoom` khớp **tuyệt đối** với `foreignRoom` của BVSC ở cả 3/3 mã. `foreignerRoom` chỉ khớp *cỡ* `foreignRemain` — lệch 0,07%–0,65% vì hai bên chốt số ở hai thời điểm khác nhau trong phiên. Ánh xạ `foreignerRoom → foreignRoom` là **sai 2–2,4 lần** mà không có gì báo lỗi *(tỷ lệ đo được: BID 2,409 · FPT 2,263 · VNM 1,984 — hệ số phụ thuộc room đã dùng của từng mã, không phải hằng số)*.

Số đo không phải bằng chứng duy nhất: [`04-fiin-company-profile.md`](04-fiin-company-profile.md) mô tả `foreignerRoom` của `Snapshot.summary` đúng là **"Room còn lại"**, trong khi `GetScreenerParameters` gắn nhãn cùng cái tên đó là *"Room nước ngoài"*. Hai tài liệu nguồn của FiinGroup **tự mâu thuẫn với nhau về nhãn**, và số đo đứng về phía "room còn lại". Vì vậy [Phụ lục A](appendix-A-field-codes.md) và `field-dictionary.json` vẫn **chép đúng nhãn API** *("Room nước ngoài")* và để ngữ nghĩa thật ở ghi chú — không viết lại nhãn nguồn.

### Dùng bao nhiêu trong 193 trường

✅ **Đã giải chỗ vênh 223-vs-193** *(đo 2026-08-15)*: 223 là tổng kích thước 5 khối, 193 là số khoá phân biệt — xem ô cảnh báo ở [Response 200](#response-200-1). Không phải do loại hình doanh nghiệp: `comGroupCode=ALL` và `VN30` đều ra đúng 193. Con số dưới đây tính trên 193 trường đó.

dulieuchungkhoan.vn chỉ lưu **80/193 trường**. 113 trường bị bỏ vì trùng BVSC, trùng BCTC, hoặc tính lại được từ giá; 20 trường nhóm chấm điểm bỏ theo quyết định của chủ dự án; số còn lại là metadata không dùng.

Phần giữ lại là **55 mã tỷ số tài chính không nguồn nào khác có** (P/S, Giá/Dòng tiền, nhóm cổ tức, nhóm đòn bẩy, nhóm tăng trưởng), Beta, hai chỉ tiêu sở hữu tổ chức, và trọn cụm TTM/Y.

Danh sách lấy/bỏ và lý do tới từng mã: [chọn trường cho ETL thị trường](../../20-design/market-field-selection.md).

⚠️ **`isa20TTM` không bằng tổng 4 quý `isa20`** — lệch tới 9,4%. Screener dùng *lợi nhuận sau thuế của cổ đông công ty mẹ*, còn `isa20` trong BCTC là *lợi nhuận thuần* gồm cả lợi ích cổ đông thiểu số. Và `P/E = vốn hoá ÷ isa20TTM` khớp 9/10 mã VN30, nên đây chính là mẫu số FiinTrade dùng. Đừng tự tính lại.

*(Khoá thật là `isa20TTM` — hoa `TTM`, đo 2026-08-15. [ADR 0002](../../00-overview/decisions/0002-data-source-selection.md) và [roadmap](../../00-overview/roadmap.md) viết `isa20ttm` theo cách chuẩn hoá cũ; nội dung không đổi, chỉ là cách viết hoa.)*
