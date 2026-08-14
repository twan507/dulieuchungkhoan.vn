# 06 — Chấm điểm, chỉ số tài chính và định giá

Ba host:
- `https://wlgw-fundamental.fiintrade.vn` — `FIIN_FUND`
- `https://wlgw-strategy.fiintrade.vn` — `FIIN_STRAT`
- `https://wlgw-tools.fiintrade.vn` — `FIIN_TOOLS`

Header bắt buộc: `Origin: https://fiinapp.bvsc.com.vn`. Tất cả nhận **`organCode`**.

6 endpoint.

---

## `getCheckup`

**Tóm tắt:** Bộ chỉ tiêu "khám sức khoẻ" tài chính, kèm so sánh với nhóm tham chiếu.

```
GET FIIN_FUND/FinancialAnalysis/GetCheckup?OrganCode={organCode}&language=vi
```

### Tham số

| Tên | Vị trí | Kiểu | Bắt buộc |
|---|---|---|---|
| `OrganCode` | query | string | **bắt buộc** |
| `language` | query | string | *tuỳ chọn* |

### Response 200

```json
{
  "items": [{
    "organCode": "BID",
    "checkupItem": { ... },
    "comparingCheckupItems": [ ... ]
  }],
  "status": "Success"
}
```

| Trường | Kiểu | Mô tả |
|---|---|---|
| `checkupItem` | object | Bộ chỉ tiêu của chính doanh nghiệp |
| `comparingCheckupItems` | array | Cùng bộ chỉ tiêu cho các doanh nghiệp so sánh (thường là cùng ngành) |

### Độ phủ & hiệu năng
51/51 mã mẫu · 173 byte – 5,95 KB · TB 5,3 KB · ~131 ms.

---

## `getFinancialRatioV2`

**Tóm tắt:** Chỉ số tài chính theo từng kỳ cụ thể do người gọi chỉ định.

**Mô tả:** Khác với các endpoint trả toàn bộ lịch sử, endpoint này để **lấy đúng những kỳ cần**. Tham số `Timeline` lặp nhiều lần trong cùng một query string.

```
GET FIIN_FUND/FinancialAnalysis/GetFinancialRatioV2
      ?Type=Company&OrganCode={organCode}
      &Timeline=2025_4&Timeline=2026_1&Timeline=2026_2
      &language=vi
```

### Tham số

| Tên | Vị trí | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|---|
| `Type` | query | string | **bắt buộc** | `Company` |
| `OrganCode` | query | string | **bắt buộc** | |
| `Timeline` | query | string | **bắt buộc** | ⚠️ **Lặp nhiều lần.** Định dạng `{năm}_{quý}`, quý `1`..`4`. Ví dụ `2026_2` |
| `language` | query | string | *tuỳ chọn* | |

### Response 200

```json
{
  "items": [
    { "key": "2025_4", "value": { "organCode": "BID", ... } },
    { "key": "2026_1", "value": { "organCode": "BID", ... } }
  ],
  "status": "Success"
}
```

| Trường | Kiểu | Mô tả |
|---|---|---|
| `key` | string | Kỳ, đúng chuỗi đã truyền vào `Timeline` |
| `value` | object | Bộ chỉ tiêu của kỳ đó |

### Bẫy — kỳ không tồn tại KHÔNG báo lỗi

`Timeline=2025_9` (quý 9 không tồn tại) trả `status: "Success"` kèm marker đặc biệt:

```json
{ "key": "2025_9", "value": { "organCode": "EndOfData" } }
```

Phải kiểm `value.organCode != "EndOfData"` trước khi dùng.

### Bảng thông báo lỗi

Toàn bộ đều trả `HTTP 200`:

| Input `Timeline` | `status` | `errors` |
|---|---|---|
| `2025_4` *(đúng)* | `"Success"` | `null` |
| `2025-4` *(gạch ngang)* | `"Failed"` | `["Input string was not in a correct format."]` |
| `20254` *(thiếu gạch dưới)* | `"Failed"` | `["Index was outside the bounds of the array."]` |
| `abcd_1` *(năm không phải số)* | `"Failed"` | `["Input string was not in a correct format."]` |
| *(không truyền)* | `"Failed"` | `["Object reference not set to an instance of an object."]` |
| `2025_9` *(quý ảo)* | `"Success"` | marker `EndOfData` |

⚠️ Đây là **thông báo lỗi runtime .NET thô**, không phải lỗi validate thân thiện. Không hiển thị cho người dùng cuối; nên validate định dạng `^\d{4}_[1-4]$` ở phía BVSC trước khi gọi.

### Độ phủ & hiệu năng
51/51 mã mẫu · 158 byte – 3,48 KB · TB 2,7 KB · ~165 ms.

---

## `getZMFScore`

**Tóm tắt:** Bộ điểm ZMF của doanh nghiệp.

```
GET FIIN_FUND/FinancialAnalysis/GetZMFScore?OrganCode={organCode}&language=vi
```

### Tham số

| Tên | Vị trí | Kiểu | Bắt buộc |
|---|---|---|---|
| `OrganCode` | query | string | **bắt buộc** |
| `language` | query | string | *tuỳ chọn* |

### Response 200

```json
{ "items": [{ "organCode": "BID", "scorings": [ ... ] }], "status": "Success" }
```

| Trường | Kiểu | Mô tả |
|---|---|---|
| `organCode` | string | Mã doanh nghiệp |
| `scorings` | array | Danh sách điểm thành phần |

### Độ phủ & hiệu năng
51/51 mã mẫu · 139–563 byte · TB 505 byte · ~156 ms.

---

## `getRateIndicator`

**Tóm tắt:** Bung 32 chỉ tiêu thành phần đứng sau điểm VGM.

**Mô tả:** [`getCompanyScore`](04-fiin-company-profile.md) chỉ trả bốn chữ cái `A`–`F`. Endpoint này giải thích **vì sao** — liệt kê từng chỉ tiêu và điểm của nó.

```
GET FIIN_STRAT/Rankings/GetRateIndicator?OrganCode={organCode}&language=vi
```

### Tham số

| Tên | Vị trí | Kiểu | Bắt buộc |
|---|---|---|---|
| `OrganCode` | query | string | **bắt buộc** |
| `language` | query | string | *tuỳ chọn* — ảnh hưởng `rateIndicatorName` |

### Response 200

```json
{
  "items": [
    { "organCode": "BID", "scoreType": "Momentum", "rateIndicatorName": "RSI 14", "rateValue": 0.0 },
    { "organCode": "BID", "scoreType": "Value",    "rateIndicatorName": "Vốn hóa thị trường", "rateValue": 1.0 },
    { "organCode": "BID", "scoreType": "Growth",   "rateIndicatorName": "Tăng trưởng Doanh thu (năm)", "rateValue": 1.0 }
  ],
  "status": "Success"
}
```

| Trường | Kiểu | Mô tả |
|---|---|---|
| `organCode` | string | Mã doanh nghiệp |
| `scoreType` | string | `Value` \| `Growth` \| `Momentum` |
| `rateIndicatorName` | string | Tên chỉ tiêu, đã dịch sẵn theo `language` |
| `rateValue` | number | Điểm thành phần. Quan sát thấy `0.0`, `1.0`, `3.0` |

### Danh sách 32 chỉ tiêu

**Momentum (13):** SMA 5 · SMA 20 · SMA 100 · RSI 14 · Xu hướng ngắn hạn · Xu hướng trung hạn · Giá đóng cửa tuần · Giá đóng cửa tháng · KLGD tb 1 tháng · Tỷ suất cổ phiếu · Giá trị NĐTNN 1 tuần · Giá trị NĐTNN 1 tháng · Giá trị NĐTNN 3 tháng

**Value (10):** Vốn hóa thị trường · Tỷ suất lợi nhuận E/P · Chỉ số EV/EBITDA · Tỷ số Giá/TS hữu hình · Tỷ lệ cổ tức · Chỉ số thanh khoản · Dòng tiền · Đầu tư tiền · Lợi nhuận gộp · Gánh nặng nợ

**Growth (9):** Tăng trưởng Doanh thu (quý) · Tăng trưởng Doanh thu (năm) · Tăng trưởng LNG (quý) · Tăng trưởng LNG (năm) · Tăng trưởng Lợi nhuận · Chỉ số PEG · Chỉ số hoàn vốn · Kế hoạch Doanh thu · Cổ phiếu dẫn đầu

Số chỉ tiêu dao động **32–33** tuỳ mã.

### Độ phủ — CÓ HẠN CHẾ

⚠️ **42/51 mã mẫu (82%).** Thiếu 9 mã, lệch rõ theo sàn:

| Sàn | Có dữ liệu | Thiếu |
|---|---|---|
| HOSE | 21/22 | `VMD` |
| HNX | 10/10 | — |
| **UPCOM** | **11/19** | `THU` `VCT` `RAT` `NAC` `HD8` `TAH` `BVL` `TAB` |

**42% mã UPCOM không có dữ liệu.** Giao diện phải xử lý trường hợp hiện được điểm tổng (`getCompanyScore` phủ 98%) nhưng không bung được chi tiết.

### Hiệu năng
~3,45 KB · ~477 ms.

---

## `getAllScore`

**Tóm tắt:** Điểm tổng hợp kèm các chỉ số thị trường cơ bản, gói trong một lời gọi.

```
GET FIIN_STRAT/Rankings/GetAllScore?OrganCode={organCode}&language=vi
```

### Response 200

```json
{
  "items": [{
    "organCode": "BID", "ticker": "BID",
    "icbRank": 4, "icbTotalRanked": 28,
    "icbCode": "8350", "icbName": "Ngân hàng", "comGroupCode": "VNINDEX",
    "growth": "C", "value": "F", "momentum": "C", "vgm": "C",
    "rtd11": 284286546450500.0,
    "rtd21": 8.58520944,
    "rtd25": 1.47260709,
    "rtq12": 0.18208852,
    "rtq14": 0.009751
  }],
  "status": "Success"
}
```

| Trường | Kiểu | Đơn vị | Mô tả |
|---|---|---|---|
| `organCode` / `ticker` | string | — | Định danh |
| `icbRank` / `icbTotalRanked` | integer | — | Thứ hạng trong ngành |
| `icbCode` / `icbName` | string | — | Ngành |
| `comGroupCode` | string | — | Sàn |
| `value` `growth` `momentum` `vgm` | string | — | Điểm `A`..`F` |
| `rtd11` | number | VND | Vốn hoá |
| `rtd21` | number | lần | P/E |
| `rtd25` | number | lần | P/B |
| `rtq12` | number | thập phân | ROE (TTM) |
| `rtq14` | number | thập phân | ROA (TTM) |

### Ghi chú
So với `getCompanyScore`, endpoint này có thêm `ticker`, `icbName`, và **5 chỉ số thị trường**. Nếu màn hình cần cả điểm lẫn P/E, P/B, ROE, ROA thì dùng endpoint này để tiết kiệm một lời gọi.

Năm trường `rtd*`/`rtq*` ở đây **đều có giá trị thật** (kiểm chứng 100% trên 50 mã có dữ liệu).

### Độ phủ & hiệu năng
50/51 mã mẫu (98%) · ~392 byte · ~400 ms.

---

## `getValuation`

**Tóm tắt:** Mô hình định giá của FiinTrade và bảng so sánh toàn ngành.

**Mô tả:** Trả về hai khối: các tham số định giá của chính doanh nghiệp (EPS/BVPS ước tính và dự phóng, lãi suất phi rủi ro, phương pháp khuyến nghị), và bảng P/E–P/B của toàn bộ doanh nghiệp cùng ngành để đối chiếu.

```
GET FIIN_TOOLS/Valuation/GetValuation?OrganCode={organCode}&language=vi
```

### Tham số

| Tên | Vị trí | Kiểu | Bắt buộc |
|---|---|---|---|
| `OrganCode` | query | string | **bắt buộc** |
| `language` | query | string | *tuỳ chọn* |

### Response 200

```json
{
  "items": [{
    "valuationStock": {
      "organCode": "BID",
      "outstandingShare": 7280065210.0,
      "rtq180": 87626300000000.0,
      "rtd14": 4548.52036746,
      "rtd7": 26517.59612466,
      "rtd35": 0.95516334,
      "estimatedEPS": 3503.12796167934,
      "forecastEPS": 1318.99045173525,
      "estimatedBookValue": 30020.7240863393,
      "forcastBookValue": 31339.7145380746,
      "riskFreeRate": 0.04538,
      "vnIndexEquityRisk": 0.0083521,
      "recommendMethod": "PB"
    },
    "valuationSector": {
      "icbCode": "8350",
      "valuationStocks": [
        { "organCode":"ACB","ticker":"ACB","totalAsset":444530104000000.0,
          "revenue":31855748000000.0,"netProfit":7682823000000.0,
          "marketCap":130019051836800.0,"pe":8.29301511,"pb":1.30916461 }
      ]
    }
  }],
  "status": 0
}
```

#### `valuationStock`

| Trường | Kiểu | Đơn vị | Mô tả |
|---|---|---|---|
| `outstandingShare` | number | cổ phiếu | Số CP lưu hành |
| `rtd7` | number | VND | Giá trị sổ sách trên cổ phiếu (BVPS) |
| `rtd14` | number | VND | EPS |
| `rtd35` | number | — | *(chưa xác định — nghi là Beta)* |
| `rtq180` | number | VND | *(chưa xác định)* |
| `estimatedEPS` | number \| null | VND | EPS ước tính |
| `forecastEPS` | number \| null | VND | EPS dự phóng |
| `estimatedBookValue` | number \| null | VND | GTSS ước tính |
| `forcastBookValue` | number \| null | VND | GTSS dự phóng — ⚠️ **tên trường viết thiếu chữ `e`**, đúng như API trả về |
| `riskFreeRate` | number | thập phân | Lãi suất phi rủi ro. `0.04538` = 4,538% |
| `vnIndexEquityRisk` | number | thập phân | Phần bù rủi ro VN-Index |
| `recommendMethod` | string | — | Phương pháp khuyến nghị: `PE` \| `PB` \| `FCFE` |

#### `valuationSector.valuationStocks[]`

| Trường | Kiểu | Đơn vị |
|---|---|---|
| `organCode` / `ticker` | string | — |
| `totalAsset` | number | VND |
| `revenue` | number | VND |
| `netProfit` | number | VND |
| `marketCap` | number | VND |
| `pe` / `pb` | number | lần |

Số doanh nghiệp cùng ngành trung bình **78,4 mã**.

### Bẫy — trường dự phóng thường rỗng

⚠️ Endpoint trả `HTTP 200` cho **51/51 mã**, nhưng các trường quan trọng nhất lại thiếu ở nhiều mã:

| Trường | Có giá trị | Tỷ lệ |
|---|---|---|
| `riskFreeRate`, `recommendMethod` | 51/51 | 100% |
| `estimatedEPS`, `estimatedBookValue` | 41/51 | 80% |
| `forecastEPS` | 35/51 | 69% |
| **`forcastBookValue`** | **34/51** | **67%** |

**Một phần ba số mã không tính được giá mục tiêu.** Phải kiểm `null` từng trường, không thể dựa vào `status`.

Phân bố `recommendMethod`: `PE` 27 mã · `PB` 17 · `FCFE` 7.

### Ghi chú cần xác nhận với FiinGroup

`estimatedEPS` và `forecastEPS` chênh nhau rất lớn (BID: 3.503 vs 1.319 — gấp 2,7 lần). Tài liệu của FiinGroup không nêu rõ định nghĩa: "estimated" là TTM ước tính hay đồng thuận thị trường, "forecast" là dự phóng năm nào. **Dùng nhầm sẽ ra giá mục tiêu lệch rất xa.** Cần làm rõ trước khi đưa vào sản phẩm.

### Hiệu năng
2,8–53 KB tuỳ quy mô ngành · ~243 ms.
