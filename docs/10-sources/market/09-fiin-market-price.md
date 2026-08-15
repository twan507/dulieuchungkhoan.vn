# 09 — Giá lịch sử và chỉ báo thị trường

Hai host:
- `https://wlgw-technical.fiintrade.vn` — `FIIN_TECH`
- `https://wlgw-market.fiintrade.vn` — `FIIN_MARKET`

Header bắt buộc: `Origin: https://fiinapp.bvsc.com.vn`

3 endpoint.

---

## `getPriceData`

**Tóm tắt:** Lịch sử giá theo ngày với **97 trường** — bao gồm dòng tiền tách theo nhóm nhà đầu tư và cờ sự kiện doanh nghiệp.

**Mô tả:** Endpoint giàu dữ liệu nhất toàn hệ thống. Không chỉ là OHLCV — mỗi phiên còn kèm phân rã giao dịch theo bốn nhóm nhà đầu tư (cá nhân trong nước, tổ chức trong nước, nước ngoài, tự doanh), tách riêng khớp lệnh và thoả thuận, cùng các cờ trạng thái doanh nghiệp.

```
GET FIIN_TECH/PriceData/GetPriceData
      ?Code={organCode}&Frequently=Daily&Page=1&PageSize=60&language=vi
```

### Tham số

| Tên | Vị trí | Kiểu | Bắt buộc | Giá trị | Mô tả |
|---|---|---|---|---|---|
| `Code` | query | string | **bắt buộc** | | ⚠️ **`organCode`**, không phải ticker |
| `Frequently` | query | string | **bắt buộc** | `enum`: `Daily` | Xem bẫy dưới |
| `Page` | query | integer | **bắt buộc** | ≥ 1 | |
| `PageSize` | query | integer | **bắt buộc** | `enum`: **`30` \| `60`** | Xem bẫy dưới |
| `language` | query | string | *tuỳ chọn* | `vi` \| `en` | |

### 🔴 Hai bẫy tham số

**`PageSize` có whitelist cứng — chỉ `30` và `60`.**

```
PageSize=10, 20, 25, 40, 50, 100, 120
→ 400 {"error":{"code":"InvalidOperationException","message":"PageSize is not allowed: 10"}}
```

**`Frequently` chỉ `Daily` hoạt động đúng.**

| Giá trị | HTTP | Kết quả thật |
|---|---|---|
| `Daily` | 200 | ✅ Nến ngày |
| `Weekly` | 200 | ⚠️ **Vẫn trả nến ngày** — chưa implement, không báo lỗi |
| `Monthly` | 200 | ⚠️ **Vẫn trả nến ngày** |
| `Quarterly` | 200 | `status: "Failed"` |
| `Yearly` | 200 | Không xác định |

Dùng `Weekly`/`Monthly` sẽ ra biểu đồ sai mà không có dấu hiệu nào. **Chỉ dùng `Daily`.**

### Response 200 — 97 trường mỗi phiên

Nhóm theo chức năng:

#### Định danh và thời gian
`code` · `tradingDate` · `referenceDate`

#### Giá và biên độ

| Trường | Đơn vị | Mô tả |
|---|---|---|
| `referenceValue` / `referencePrice` | VND | Giá tham chiếu |
| `ceilingValue` / `floorValue` | VND | Trần / sàn |
| `openValue` | VND | Mở cửa |
| `closeValue` / `closePrice` | VND | Đóng cửa |
| `highestValue` / `lowestValue` | VND | Cao nhất / thấp nhất |
| `averageValue` | VND | Giá bình quân |
| `matchValue` | VND | Giá khớp |
| `valueChange` | VND | Thay đổi |
| `percentValueChange` | thập phân | Thay đổi phần trăm |
| `parValue` | VND | Mệnh giá |

#### Khối lượng và giá trị

| Trường | Đơn vị | Mô tả |
|---|---|---|
| `totalMatchVolume` / `totalMatchValue` | cổ phiếu / VND | Khớp lệnh |
| `totalDealVolume` / `totalDealValue` | cổ phiếu / VND | **Thoả thuận** |
| `totalVolume` / `totalValue` | cổ phiếu / VND | Tổng cộng |
| `totalTrade` / `totalBuyTrade` / `totalSellTrade` | lệnh | Số lệnh |
| `totalBuyTradeVolume` / `totalSellTradeVolume` | cổ phiếu | KL theo chiều |
| `totalMatchBuyTradeVolume` / `totalMatchBuyTradeValue` | | Khớp lệnh chiều mua |
| `totalMatchSellTradeVolume` / `totalMatchSellTradeValue` | | Khớp lệnh chiều bán |

#### Khối ngoại

| Trường | Mô tả |
|---|---|
| `foreignBuyVolume` / `foreignBuyValue` | Tổng mua |
| `foreignSellVolume` / `foreignSellValue` | Tổng bán |
| `foreignBuyVolumeMatched` / `foreignBuyValueMatched` | Mua qua khớp lệnh |
| `foreignSellVolumeMatched` / `foreignSellValueMatched` | Bán qua khớp lệnh |
| `foreignBuyVolumeDeal` / `foreignBuyValueDeal` | Mua qua thoả thuận |
| `foreignSellVolumeDeal` / `foreignSellValueDeal` | Bán qua thoả thuận |
| `foreignTotalRoom` / `foreignCurrentRoom` | Tổng room / room còn lại |
| `foreignerPercentage` | Tỷ lệ sở hữu nước ngoài |
| `foreignIndividualBuyTradingMatchValue` / `...Volume` | **Ngoại cá nhân** mua |
| `foreignIndividualSellTradingMatchValue` / `...Volume` | Ngoại cá nhân bán |
| `foreignInstitutionalBuyTradingMatchValue` / `...Volume` | **Ngoại tổ chức** mua |
| `foreignInstitutionalSellTradingMatchValue` / `...Volume` | Ngoại tổ chức bán |

#### Nhà đầu tư trong nước

| Trường | Mô tả |
|---|---|
| `localIndividualBuyValue` / `localIndividualBuyVolume` | **Cá nhân trong nước** mua |
| `localIndividualSellValue` / `localIndividualSellVolume` | Cá nhân trong nước bán |
| `localIndividualBuyMatchValue` / `...MatchVolume` | Cá nhân, riêng khớp lệnh |
| `localIndividualSellMatchValue` / `...MatchVolume` | |
| `localInstitutionalBuyValue` / `localInstitutionalBuyVolume` | **Tổ chức trong nước** mua |
| `localInstitutionalSellValue` / `localInstitutionalSellVolume` | Tổ chức trong nước bán |
| `localInstitutionalBuyMatchValue` / `...MatchVolume` | Tổ chức, riêng khớp lệnh |
| `localInstitutionalSellMatchValue` / `...MatchVolume` | |
| `netInstitutionMatchVolume` / `netInstitutionMatchValue` | Tổ chức ròng |

#### Tự doanh

| Trường | Mô tả |
|---|---|
| `proprietaryTotalBuyTradeVolume` / `...Value` | Tổng mua |
| `proprietaryTotalSellTradeVolume` / `...Value` | Tổng bán |
| `proprietaryTotalMatchBuyTradeVolume` / `...Value` | Mua qua khớp lệnh |
| `proprietaryTotalMatchSellTradeVolume` / `...Value` | Bán qua khớp lệnh |
| `proprietaryTotalDealBuyTradeVolume` / `...Value` | Mua qua thoả thuận |
| `proprietaryTotalDealSellTradeVolume` / `...Value` | Bán qua thoả thuận |
| `netProprietaryMatchVolume` / `netProprietaryMatchValue` | Tự doanh ròng |

#### Cờ sự kiện và trạng thái

| Trường | Kiểu | Mô tả |
|---|---|---|
| `split` | flag | Chia tách cổ phiếu |
| `benefit` | flag | Quyền lợi cổ đông |
| `meeting` | flag | Đại hội cổ đông |
| `notice` | flag | Thông báo |
| `issueDate` | date | Ngày phát hành |
| `shareIssue` | number | Phát hành thêm |
| `suspension` | flag | Tạm ngừng giao dịch |
| `delist` | flag | Huỷ niêm yết |
| `haltResumeFlag` | flag | Ngừng / mở lại |

#### Chuyên biệt theo loại chứng khoán
`iNav` · `iIndex` *(ETF)* · `openInterest` *(phái sinh)*

### Ví dụ dữ liệu thật

BID phiên 07/08/2026:
- Cá nhân trong nước: mua 194,83 tỷ · bán 194,84 tỷ
- Tổ chức trong nước: mua 87,06 tỷ · bán 129,47 tỷ
- Tự doanh: mua 8,81 tỷ · bán 16,61 tỷ
- Ngoại tổ chức mua khớp lệnh: 56,38 tỷ · ngoại cá nhân: 1,05 tỷ

### 🔴 Giới hạn quan trọng — dòng tiền theo nhóm NĐT chỉ có ở HOSE

Nhóm trường `localIndividual*`, `localInstitutional*`, `foreignIndividual*`, `foreignInstitutional*`, `proprietary*` **chỉ có dữ liệu với cổ phiếu HOSE**:

| Mã | Sàn | Số trường dòng tiền có giá trị (trên 12 trường kiểm) |
|---|---|---|
| BID, FPT | HOSE | **9/12** |
| SHS | HNX | 1/12 — còn lại `null` |
| PVS | HNX | 3/12 |
| VGI, ACV | UPCOM | 1–2/12 |

Phần OHLCV, thoả thuận, khối ngoại tổng và cờ sự kiện thì **hoạt động đủ trên cả ba sàn**.

### 🔴 Độ sâu — phân trang lùi tới 2014

Tham số `Page` **hoạt động và lùi được về quá khứ**. Đây là nguồn lịch sử sâu nhất của toàn hệ thống.

| Page | Phiên | Lùi tới |
|---|---|---|
| 1 | 60 | 2026-05-18 |
| 10 | 60 | 2024-03-13 |
| 20 | 60 | 2021-10-15 |
| 30 | 60 | 2019-05-29 |
| 40 | 60 | 2016-12-27 |
| 50 | 60 | 2014-08-05 |
| **52** | 60 | **2014-02-12** |
| 54 trở đi | 0 | hết dữ liệu |

**~3.120 phiên ≈ 12,5 năm** (mã BID, độ sâu thay đổi theo tuổi niêm yết của từng mã).

Quan trọng: **dữ liệu ở trang sâu vẫn đủ 99 trường**, kể cả nhóm dòng tiền theo nhà đầu tư. Kiểm chứng Page 20 (07/01/2022): `localIndividualBuyValue` 147.041.725.000 · `localInstitutionalBuyValue` 1.318.440.000 · `proprietaryTotalBuyTradeValue` 944.055.000 · `foreignInstitutionalBuyTradingMatchValue` 17.766.105.000.

### Điều chỉnh giá

Chuỗi giá là **giá đã điều chỉnh hồi tố** cho cổ tức và chia tách. Nhận biết bằng giá trị thập phân ở dữ liệu cũ — ví dụ `closeValue = 28104,0406633688` ngày 07/01/2022, trong khi giá hiện tại là số nguyên.

Đối chiếu với [`getHistoryBars`](02-bvsc-tvcharts.md) của BVSC: cả hai đều điều chỉnh, nhưng **hệ số khác nhau**, lệch ~1,9 đ (0,005%):

| Ngày | tvcharts BVSC | GetPriceData |
|---|---|---|
| 2025-11-14 | 37910,8925 | 37908,975 |
| 2025-11-11 | 37564,90 | 37563,00 |

Phiên gần nhất thì trùng khớp tuyệt đối (07/08/2026: cả hai `open 37900 · close 39050`), vì tại đó điều chỉnh bằng thô.

⚠️ **Không trộn hai nguồn trong cùng một chuỗi.**

### Độ phủ & hiệu năng
51/51 mã mẫu · 60 phiên/trang · ~201 KB · ~3,5 s mỗi trang.
Quét đủ 12,5 năm một mã = 52 lời gọi ≈ 3 phút tuần tự.

---

## `getLiquiditySeries`

**Tóm tắt:** Chuỗi thanh khoản toàn thị trường theo thời gian trong phiên, có **giá trị bằng tiền**.

**Mô tả:** Bổ sung cho [`getIntradayIndexChart`](01-bvsc-rest.md) của BVSC — endpoint BVSC chỉ có khối lượng, không có giá trị VND.

```
GET FIIN_MARKET/MarketInDepth/GetLiquiditySeries
      ?ComGroupCode={group}&TimeRange={range}&language=vi
```

### Tham số

| Tên | Vị trí | Kiểu | Bắt buộc | Giá trị |
|---|---|---|---|---|
| `ComGroupCode` | query | string | **bắt buộc** | `VNINDEX` \| `HNXIndex` \| `UpcomIndex` \| `VN30` \| `HNX30` \| `VNMID` \| `VN100` |
| `TimeRange` | query | string | **bắt buộc** | `OneDay` \| `OneWeek` \| `OneMonth` \| `ThreeMonths` \| `SixMonths` \| `OneYear` \| `YearToDate` |
| `language` | query | string | *tuỳ chọn* | |

### 🔴 Bẫy — `TimeRange` bắt buộc nhưng giá trị không đổi kết quả

```
Thiếu TimeRange       →  200, items: [], totalCount: 0     ❌
TimeRange=OneDay      →  200, 44.223 byte
TimeRange=OneMonth    →  200, 44.227 byte
TimeRange=OneYear     →  200, 44.427 byte
```

Tham số **bắt buộc phải có** để endpoint trả dữ liệu, nhưng mọi giá trị đều cho kết quả gần như đồng nhất — dữ liệu luôn là **chuỗi trong phiên hiện tại**, không phải chuỗi lịch sử theo khoảng đã chọn.

### Response 200

```json
{
  "items": [
    { "comGroupCode": null,
      "tradingDate": "2026-08-10T09:00:00",
      "totalMatchValue": 0.0,
      "totalMatchVolume": 0.0 }
  ],
  "status": 0
}
```

| Trường | Kiểu | Đơn vị | Mô tả |
|---|---|---|---|
| `comGroupCode` | string \| null | — | Thường `null` |
| `tradingDate` | string | ISO 8601 | Mốc thời gian trong phiên |
| `totalMatchValue` | number | VND | Giá trị khớp lệnh luỹ kế |
| `totalMatchVolume` | number | cổ phiếu | Khối lượng khớp lệnh luỹ kế |

**361 điểm** dữ liệu trong phiên.

### Độ phủ & hiệu năng
7/7 nhóm chỉ số · ~44 KB · nhanh.

---

## `getComGroupBuSdChart`

**Tóm tắt:** Áp lực mua/bán chủ động của toàn thị trường.

**Mô tả:** BVSC chỉ có chiều chủ động ở **cấp từng lệnh** (trường `LC` trong realtime `t:` và `lastColor` trong `translogsnaps`). Muốn có tổng hợp toàn thị trường bằng nguồn BVSC thì phải tự cộng dồn 1.974 mã *(đếm `StockType=2` từ `getAllQuotes`, đo 2026-08-15)*. Endpoint này trả sẵn.

```
GET FIIN_MARKET/MarketInDepth/GetComGroupBuSdChart?ComGroupCode={group}&language=vi
```

### Tham số

| Tên | Vị trí | Kiểu | Bắt buộc | Giá trị |
|---|---|---|---|---|
| `ComGroupCode` | query | string | **bắt buộc** | 7 nhóm như trên |
| `language` | query | string | *tuỳ chọn* | |

### Response 200

```json
{
  "items": [
    { "matchPrice": 1769.8,
      "volumeBu": 5250648.0,
      "volumeSd": 2448198.0,
      "tradingDate": "2026-08-10T10:30:00" }
  ],
  "status": 0
}
```

| Trường | Kiểu | Đơn vị | Mô tả |
|---|---|---|---|
| `matchPrice` | number | điểm | Giá trị chỉ số tại mốc đó |
| `volumeBu` | number | cổ phiếu | Khối lượng **mua chủ động** (Buy Up) |
| `volumeSd` | number | cổ phiếu | Khối lượng **bán chủ động** (Sell Down) |
| `tradingDate` | string | ISO 8601 | Mốc thời gian |

### Độ phủ & hiệu năng
7/7 nhóm chỉ số · ~1,1–37 KB tuỳ thời điểm trong phiên · ~383 ms.

---

## Endpoint cùng nhóm đã loại

| Endpoint | Lý do |
|---|---|
| `MarketInDepth/GetIndexSeries` | Trùng `TVC/history` với `symbol=VNINDEX\|VN30\|HNXIndex` |
| `MarketInDepth/GetLatestIndices` | Trùng `BVSC/datafeed/indexsnaps`. *(Lưu ý: FiinTrade có 29 chỉ số, BVSC có 18 — thiếu 14 chỉ số ngành HOSE như `VNFIN`, `VNREAL`, `VNIT`. Đã chấp nhận đánh đổi.)* |
| `MarketInDepth/GetProspect` | Trùng hai endpoint trên |
| `MarketInDepth/GetValuationSeries` · `V2` · `GetMarketAnomaly` | Trả rỗng |
| `PriceData/GetLatestPrice` | Trùng `BVSC/datafeed/instruments` + realtime |
| `PriceDepth/GetPriceDepth` | Đã quyết dùng sổ lệnh 3 bậc từ realtime BVSC |
| `TimeAndSales/GetTimeAndSales` · `GetTimeAndSalesBuSdChart` | Trùng `BVSC/datafeed/translogsnaps` + realtime `t:` |
| `TradingView/GetStockChartData` · `GetStockEvents` | Trùng `TVC/history` và `Calendar/GetCorporate*` |
