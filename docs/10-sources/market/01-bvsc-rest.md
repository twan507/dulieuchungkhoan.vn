# 01 — REST BVSC (`online.bvsc.com.vn`)

Base URL: `https://online.bvsc.com.vn` — ký hiệu `BVSC`
Header: không bắt buộc. Khuyến nghị gửi `Origin: https://online.bvsc.com.vn`.

7 endpoint. Không endpoint nào cần `organCode` — **tất cả dùng mã chứng khoán (ticker)**.

---

## `getAllQuotes`

**Tóm tắt:** Danh mục toàn bộ mã đang niêm yết kèm giá tham chiếu/trần/sàn.

**Mô tả:** Endpoint nền tảng để dựng danh sách mã. Trả về mọi loại chứng khoán trên cả ba sàn, phân biệt bằng `StockType`. Đây là nguồn duy nhất cho `tradelot` (đơn vị giao dịch).

```
GET BVSC/quotes?symbols=ALL
```

### Tham số

| Tên | Vị trí | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|---|
| `symbols` | query | string | **bắt buộc** | `ALL` để lấy toàn bộ, hoặc danh sách mã cách nhau bởi dấu phẩy: `BID,FPT,VNM` |

### Response 200

```json
{
  "s": "ok",
  "d": [
    {
      "symbol": "ACB",
      "ceiling": 23950,
      "floor": 20850,
      "reference": 22400,
      "FullName": "Ngân hàng Thương mại Cổ phần Á Châu",
      "StockType": "2",
      "exchange": "HOSE",
      "tradelot": 100
    }
  ]
}
```

| Trường | Kiểu | Đơn vị | Mô tả |
|---|---|---|---|
| `symbol` | string | — | Mã chứng khoán |
| `ceiling` | integer | VND | Giá trần phiên hiện tại |
| `floor` | integer | VND | Giá sàn |
| `reference` | integer | VND | Giá tham chiếu |
| `FullName` | string | — | Tên đầy đủ tổ chức phát hành |
| `StockType` | string | — | Phân loại — xem bảng dưới |
| `exchange` | string | — | `HOSE` \| `HNX` \| `UPCOM` |
| `tradelot` | integer | cổ phiếu | Đơn vị giao dịch tối thiểu |

**Bảng `StockType`** *(đếm trên toàn bộ 2.530 mã)*

| Giá trị | Nghĩa | Số lượng |
|---|---|---|
| `2` | Cổ phiếu | 1.972 |
| `4` | Chứng quyền có bảo đảm (CW) | 342 |
| `12` | Trái phiếu | 185 |
| `3` | ETF / Chứng chỉ quỹ | 31 |

**Phân bố theo sàn** *(toàn bộ)*: HOSE 804 · HNX 530 · UPCOM 1.196.
**Riêng cổ phiếu (`StockType=2`)**: HOSE 432 · HNX 344 · UPCOM 1.196.

### Ghi chú
- Không chứa phái sinh. BVSC không cung cấp dữ liệu phái sinh qua bất kỳ endpoint public nào.
- Giá trần/sàn/tham chiếu là của **phiên hiện tại**, cập nhật đầu ngày giao dịch.

### Độ phủ & hiệu năng
2.530 bản ghi · 51/51 mã mẫu có mặt · 589 KB · ~580 ms.
Nên cache trong ngày, làm mới đầu phiên.

---

## `getSymbolMapping`

**Tóm tắt:** Bảng ánh xạ mã ↔ tên ↔ sàn ↔ loại chứng khoán.

**Mô tả:** Tập con của `getAllQuotes`, không có dữ liệu giá. Dùng khi chỉ cần tra cứu định danh, nhẹ hơn về mặt xử lý dù kích thước không nhỏ hơn nhiều.

```
GET BVSC/mapping
```

### Tham số
Không có.

### Response 200

⚠️ Trả về **mảng trần**, không có vỏ bọc `{s, d}`.

```json
[
  { "FullName": "VBA122001-AUTO", "symbol": "VBA122001", "exchange": "HNX", "StockType": "12" }
]
```

| Trường | Kiểu | Mô tả |
|---|---|---|
| `FullName` | string | Tên tổ chức phát hành |
| `symbol` | string | Mã chứng khoán |
| `exchange` | string | `HOSE` \| `HNX` \| `UPCOM` |
| `StockType` | string | Xem bảng `StockType` ở trên |

### Độ phủ & hiệu năng
2.530 bản ghi · 51/51 mã mẫu có mặt · 324 KB · ~465 ms. Cache dài hạn.

---

## `getInstrumentSnapshot`

**Tóm tắt:** Snapshot đầy đủ của một hoặc nhiều mã tại thời điểm gọi.

**Mô tả:** Nguồn khởi tạo trạng thái trước khi chuyển sang nhận cập nhật realtime. Chứa các trường mà kênh realtime **không đẩy** (`open`, `high`, `low`, `ceiling`, `floor`, `reference`), nên bắt buộc gọi một lần lúc mở màn hình.

```
GET BVSC/datafeed/instruments?symbols={tickers}
```

### Tham số

| Tên | Vị trí | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|---|
| `symbols` | query | string | **bắt buộc** | Một hoặc nhiều **ticker**, cách nhau bởi dấu phẩy |

### Response 200 — 50 trường

```json
{"s":"ok","d":[{
  "symbol":"BID","StockId":"217","FullName":"Ngân hàng TMCP Đầu tư và Phát triển Việt Nam",
  "tradingdate":"10/08/2026","FloorCode":"10","StockType":"2",
  "ceiling":41750,"floor":36350,"reference":39050,
  "bidPrice1":"39450.0","bidVol1":105100,"bidPrice2":39400,"bidVol2":35900,"bidPrice3":39350,"bidVol3":50000,
  "offerPrice1":"39500.0","offerVol1":27700,"offerPrice2":39550,"offerVol2":54500,"offerPrice3":39600,"offerVol3":66400,
  "closePrice":39500,"closeVol":1100,"change":450,"changePercent":1.1523687580025608,
  "open":39550,"high":39750,"low":39300,"averagePrice":39524,
  "totalTrading":999200,"totalTradingValue":39492260000,
  "foreignBuy":78600,"foreignSell":44435,"foreignRemain":908366228,"foreignRoom":2184019563,
  "TOTAL_BID_QTTY":0,"TOTAL_OFFER_QTTY":0,"PRIOR_PRICE":0,
  "PT_MATCH_QTTY":0,"PT_MATCH_PRICE":0,"PT_TOTAL_TRADED_QTTY":0,"PT_TOTAL_TRADED_VALUE":0,
  "Status":"00","symbolStatusCode":"NRM|NRM|NRM","exchange":"HOSE",
  "priceOne":"1100","priceTwo":"39500.0","tradingSessionID":"",
  "ListedShare":"7280065210","TotalListingQtty":"7280065210",
  "openInterest":"","openInterestChange":"","firstTradingDate":"","lastTradingDate":"",
  "underlyingSymbol":"","IssuerName":"BID","CoveredWarrantType":"","MaturityDate":"",
  "ExercisePrice":"0.0","ExerciseRatio":"","FundType":"","ts":1786331263964
}]}
```

#### Nhóm định danh

| Trường | Kiểu | Mô tả |
|---|---|---|
| `symbol` | string | Mã chứng khoán |
| `StockId` | string | ID nội bộ BVSC |
| `FullName` | string | Tên tổ chức phát hành |
| `exchange` | string | Sàn |
| `FloorCode` | string | Mã sàn dạng số — `10` HOSE · `02` HNX · `04` UPCOM |
| `StockType` | string | Xem bảng `StockType` |
| `tradingdate` | string | Ngày giao dịch, `dd/MM/yyyy` |
| `ts` | integer | Epoch ms tại thời điểm sinh snapshot |

#### Nhóm giá và biên độ

| Trường | Kiểu | Đơn vị | Mô tả |
|---|---|---|---|
| `ceiling` / `floor` / `reference` | integer | VND | Trần / sàn / tham chiếu |
| `open` / `high` / `low` | integer | VND | Mở cửa / cao nhất / thấp nhất |
| `closePrice` | integer | VND | Giá khớp gần nhất *(không phải giá đóng cửa cuối phiên)* |
| `closeVol` | integer | cổ phiếu | Khối lượng của lệnh khớp gần nhất |
| `change` | integer | VND | Thay đổi so với tham chiếu |
| `changePercent` | float | % | Thay đổi phần trăm — **là số phần trăm thật** (`1.152` = 1,152%), khác quy ước thập phân của FiinTrade |
| `averagePrice` | integer | VND | Giá bình quân phiên |
| `priceOne` / `priceTwo` | string | — | Khối lượng và giá của lệnh khớp gần nhất *(trùng `closeVol`/`closePrice`)* |

#### Nhóm sổ lệnh — 3 bậc

| Trường | Kiểu | Mô tả |
|---|---|---|
| `bidPrice1..3` / `bidVol1..3` | number | Giá và khối lượng dư mua bậc 1–3 |
| `offerPrice1..3` / `offerVol1..3` | number | Giá và khối lượng dư bán bậc 1–3 |
| `TOTAL_BID_QTTY` / `TOTAL_OFFER_QTTY` | integer | Tổng dư mua / dư bán |

⚠️ `bidPrice1` và `offerPrice1` trả về dạng **chuỗi** (`"39450.0"`), các bậc 2–3 trả về **số**. Phải ép kiểu khi xử lý.

⚠️ BVSC chỉ cung cấp **3 bậc giá** cho mọi sàn.

#### Nhóm khối lượng và khối ngoại

| Trường | Kiểu | Đơn vị | Mô tả |
|---|---|---|---|
| `totalTrading` | integer | cổ phiếu | Tổng khối lượng khớp lệnh |
| `totalTradingValue` | integer | VND | Tổng giá trị khớp lệnh |
| `foreignBuy` / `foreignSell` | integer | cổ phiếu | Khối ngoại mua / bán trong phiên |
| `foreignRemain` | integer | cổ phiếu | Room còn lại |
| `foreignRoom` | integer | cổ phiếu | Tổng room |

#### Nhóm thoả thuận

| Trường | Kiểu | Mô tả |
|---|---|---|
| `PT_MATCH_QTTY` / `PT_MATCH_PRICE` | number | Khối lượng / giá lệnh thoả thuận gần nhất |
| `PT_TOTAL_TRADED_QTTY` / `PT_TOTAL_TRADED_VALUE` | number | Luỹ kế thoả thuận trong phiên |

#### Nhóm trạng thái

| Trường | Kiểu | Mô tả |
|---|---|---|
| `Status` | string | Mã trạng thái mã, `00` = bình thường |
| `symbolStatusCode` | string | Ba trạng thái ngăn bởi `\|`, ví dụ `NRM\|NRM\|NRM` |
| `tradingSessionID` | string | Phiên giao dịch hiện tại, rỗng ngoài giờ |

#### Nhóm cổ phiếu quỹ / chứng quyền / phái sinh

Các trường sau chỉ có giá trị với loại chứng khoán tương ứng, còn lại là chuỗi rỗng:
`ListedShare`, `TotalListingQtty`, `IssuerName`, `CoveredWarrantType`, `MaturityDate`, `ExercisePrice`, `ExerciseRatio`, `underlyingSymbol`, `FundType`, `openInterest`, `openInterestChange`, `firstTradingDate`, `lastTradingDate`.

### Độ phủ & hiệu năng
51/51 mã mẫu · ~1,8 KB/mã · ~140 ms.

---

## `getTransactionLogSnapshot`

**Tóm tắt:** Lịch sử lệnh khớp trong phiên của một mã.

**Mô tả:** Danh sách từng lệnh khớp, có chiều mua/bán chủ động. Dùng để dựng bảng "Lệnh khớp" khi mở màn hình, trước khi chuyển sang nhận realtime qua topic `t:`.

```
GET BVSC/datafeed/translogsnaps/{ticker}
```

### Tham số

| Tên | Vị trí | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|---|
| `ticker` | path | string | **bắt buộc** | Mã chứng khoán |

### Response 200

```json
{"s":"ok","d":{
  "nextIndex": 100,
  "translog": [{
    "id":"1786333235848-8248556900494534266",
    "sequenceMsg":"824128",
    "tradingdate":"10/08/2026",
    "symbol":"BID",
    "formattedTime":"10:40:35",
    "lastColor":"B",
    "formattedMatchPrice":"39.50",
    "changeColor":"...",
    "formattedChangeValue":"...",
    "formattedVol":"...",
    "formattedAccVol":"...",
    "formattedAccVal":"...",
    "createAt":"..."
  }]
}}
```

| Trường | Kiểu | Mô tả |
|---|---|---|
| `nextIndex` | integer | Con trỏ phân trang. `-1` khi hết dữ liệu |
| `translog[]` | array | Danh sách lệnh khớp, mới nhất trước |
| `id` | string | Định danh duy nhất, dạng `{epoch_ms}-{hash}` |
| `sequenceMsg` | string | Số thứ tự message từ sở |
| `formattedTime` | string | Giờ khớp `HH:mm:ss` |
| `lastColor` | string | **Chiều chủ động**: `B` = mua chủ động (BU), `S` = bán chủ động (SD) |
| `formattedMatchPrice` | string | Giá khớp đã định dạng sẵn |
| `formattedChangeValue` | string | Thay đổi giá đã định dạng |
| `changeColor` | string | Gợi ý màu hiển thị |
| `formattedVol` | string | Khối lượng lệnh này |
| `formattedAccVol` / `formattedAccVal` | string | Luỹ kế khối lượng / giá trị |

### Ghi chú
- ⚠️ **Giới hạn cứng 100 bản ghi mỗi lần gọi.** Mã thanh khoản cao luôn dừng đúng ở 100. Dùng `nextIndex` để lấy tiếp.
- Các trường `formatted*` là **chuỗi đã định dạng sẵn** để hiển thị, không phải số thô. Muốn tính toán phải tự parse.

### Độ phủ
**34/51 mã mẫu (67%)**. 12/17 mã rỗng thuộc UPCOM. Nguyên nhân nhiều khả năng là mã không có lệnh khớp nào trong phiên, không phải giới hạn API — cần thiết kế trạng thái rỗng. ~47 KB khi đầy · ~130 ms.

---

## `getIndexSnapshots`

**Tóm tắt:** Snapshot toàn bộ chỉ số thị trường.

```
GET BVSC/datafeed/indexsnaps
```

### Tham số
Không có.

### Response 200 — 33 trường, 20 chỉ số

| Trường | Kiểu | Đơn vị | Mô tả |
|---|---|---|---|
| `marketCode` / `marketId` | string | — | Mã chỉ số — xem bảng dưới |
| `marketIndex` | string | điểm | Giá trị chỉ số hiện tại |
| `indexChange` | string | điểm | Thay đổi tuyệt đối |
| `indexPercentChange` | string | % | Thay đổi phần trăm |
| `indexTime` | string | — | Giờ cập nhật `HH:mm:ss` |
| `indexColor` | string | — | Gợi ý màu |
| `tradingdate` | string | — | Ngày giao dịch |
| `marketStatus` | string | — | Trạng thái phiên |
| `totalTrade` | string | lệnh | Tổng số lệnh |
| `totalVolume` / `totalValue` | string | cổ phiếu / VND | Tổng khối lượng / giá trị khớp lệnh |
| `advances` / `declines` / `noChange` | string | mã | Số mã tăng / giảm / đứng giá |
| `advancesVolumn` / `declinesVolumn` / `noChangeVolumn` | string | cổ phiếu | Khối lượng tương ứng |
| `numberOfCe` / `numberOfFl` | string | mã | Số mã trần / sàn |
| `PT_TOTAL_QTTY` / `PT_TOTAL_VALUE` / `PT_TOTAL_TRADE` | string | — | Luỹ kế thoả thuận |
| `oddLotTotalVolume` / `oddLotTotalValue` | string | — | Luỹ kế lô lẻ |
| `PRV_PRIOR_MARKET_INDEX` | string | điểm | Chỉ số phiên trước |
| `AVR_MARKET_INDEX` / `AVR_PRIOR_MARKET_INDEX` / `AVR_CHG_INDEX` / `AVR_PCT_INDEX` | string | — | Nhóm chỉ số bình quân |
| `id` / `sequenceMsg` / `createAt` | string | — | Metadata |

⚠️ **Toàn bộ giá trị số trả về dưới dạng chuỗi.** Phải ép kiểu.

**20 chỉ số:** `HOSE` (VN-Index) · `30` (VN30) · `100` (VN100) · `MID` (VNMID) · `SML` (VNSML) · `XALL` (VNXALL) · `X50` (VNX50) · `SI` (VNSI) · `ALL` · `DIAMOND` · `FINLEAD` · `FINSELECT` · `HNX` · `HNX30` · `HNXFin` · `HNXMSCap` · `HNXMan` · `UPCOM`.

### Độ phủ & hiệu năng
20 bản ghi · 20 KB · ~123 ms.

---

## `getIntradayIndexChart`

**Tóm tắt:** Chuỗi chỉ số theo từng phút trong phiên.

```
GET BVSC/datafeed/chartinday/{codes}
```

### Tham số

| Tên | Vị trí | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|---|
| `codes` | path | string | **bắt buộc** | Danh sách mã chỉ số cách nhau bởi dấu phẩy |

Hai tổ hợp app BVSC dùng: `HOSE,30,MID,100,SML,XALL,X50,SI,X200` và `HNX,HNX30,UPCOM`.

### Response 200

⚠️ Trả về **object trần**, khoá là mã chỉ số, không có vỏ bọc `{s, d}`.

```json
{
  "HOSE": {
    "formattedtime": ["09:00:00", "09:01:00", "09:02:00"],
    "volume":        [4, 0, 0],
    "close":         [1760.87, 1762.34, 1764.43],
    "reference":     ["1768.06"]
  }
}
```

| Trường | Kiểu | Mô tả |
|---|---|---|
| `formattedtime[]` | string[] | Mốc thời gian từng phút, `HH:mm:ss` |
| `volume[]` | number[] | Khối lượng trong phút đó |
| `close[]` | number[] | Giá trị chỉ số cuối phút |
| `reference[]` | string[] | **Mảng 1 phần tử** — chỉ số tham chiếu |

Ba mảng `formattedtime`, `volume`, `close` luôn cùng độ dài và **khớp theo chỉ số vị trí**.

### Ghi chú
- ⚠️ Chỉ có **khối lượng**, không có **giá trị (VND)**. Muốn chuỗi thanh khoản theo tiền phải dùng [`getLiquiditySeries`](09-fiin-market-price.md) của FiinTrade.
- ⚠️ Khoá `X200` **luôn trả mảng rỗng** dù các khoá khác trong cùng lời gọi đều có dữ liệu.
- Số điểm tăng dần trong phiên (126 điểm lúc 11:05).

### Hiệu năng
19–26 KB · ~95 ms.

---

## `getServerTime`

**Tóm tắt:** Thời gian máy chủ, dùng để đồng bộ đồng hồ hiển thị.

```
GET BVSC/userdata/time
```

### Response 200

```json
{ "s": "ok", "d": { "currentTimeDb": 1786326074394 } }
```

| Trường | Kiểu | Mô tả |
|---|---|---|
| `currentTimeDb` | integer | Epoch **milliseconds**, múi giờ UTC+7 |

### Hiệu năng
64 byte · < 100 ms.

---

## Endpoint đã loại khỏi phạm vi

Các đường dẫn sau tồn tại trong mã nguồn ứng dụng BVSC nhưng **không dùng được** trên host public:

| Đường dẫn | Kết quả |
|---|---|
| `/datafeed/indexs/getTime` | `200` nhưng luôn rỗng: `{"nextIndex":-1,"marketInfor":[]}` — kể cả trong phiên |
| `/datafeed/prevTradingDate` | `404` |
| `/datafeed/alltranslogs` | `404` |
| `/datafeed/m-instruments` | `500` |
| `/priceservice/derivative/snapshot` · `/transactions` | `404` |
| `/priceservice/ptorder/history` · `/adorder/history` | `404` |
| `/priceservice/ceilingfloorcount/snapshot` | `404` |
| `/datafeed/oddlotInstruments` · `/oltranslogsnaps` | Hoạt động nhưng lô lẻ ngoài phạm vi |
