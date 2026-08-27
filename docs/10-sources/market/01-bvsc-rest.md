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

**Bảng `StockType`** *(đếm lại 2026-08-15 trên toàn bộ **2.534** mã; cột 2026-08-10 giữ lại để thấy nhịp thay đổi)*

| Giá trị | Nghĩa | Số lượng — 2026-08-15 | 2026-08-10 |
|---|---|---:|---:|
| `2` | Cổ phiếu | **1.974** | 1.972 |
| `4` | Chứng quyền có bảo đảm (CW) | **342** | 342 |
| `12` | Trái phiếu | **187** | 185 |
| `3` | ETF / Chứng chỉ quỹ | **31** | 31 |

**Phân bố theo sàn** *(toàn bộ, 2026-08-15)*: HOSE 805 · HNX 532 · UPCOM 1.197.
**Riêng cổ phiếu (`StockType=2`)**: HOSE 433 · HNX 344 · UPCOM 1.197.

Tổng tăng 4 mã trong 5 ngày (2 cổ phiếu + 2 trái phiếu) — bảng này **không tĩnh**, đừng hardcode con số.

### Ghi chú
- **`/quotes` không chứa phái sinh** — kiểm 2026-08-15: `/quotes?symbols=41I1G8000` trả `{"s":"ok","d":[]}`.
  ⚠️ **Đừng suy từ đây ra "BVSC không có phái sinh"** — bản trước của tài liệu này đã mắc đúng lỗi đó: quan sát đúng *(một endpoint không có)*, suy luận sai *(toàn nguồn không có)*. Kết luận phủ định về cả một nguồn phải dò từ ứng dụng thật của nguồn, không được suy từ một endpoint.
  Phái sinh đi đường [`/datafeed/instruments`](#phái-sinh--14-hợp-đồng) — **14 hợp đồng, 62 trường, có `openInterest`** *(đo 2026-08-15)*.
- ⚠️ **`/quotes` và `/datafeed/instruments` lệch độ phủ**: 2.534 vs **2.001** bản ghi *(đo 2026-08-15)*. `VFMVF1` có ở `/quotes` nhưng **không có** ở `/datafeed/instruments`; ngược lại 14 hợp đồng phái sinh chỉ có ở `/datafeed/instruments`. **Không endpoint nào là danh mục chuẩn duy nhất** — ETL phải hợp nhất cả hai.
- Giá trần/sàn/tham chiếu là của **phiên hiện tại**, cập nhật đầu ngày giao dịch.

### Độ phủ & hiệu năng
**2.534 bản ghi** *(đo 2026-08-15; 2026-08-10 là 2.530)* · 51/51 mã mẫu có mặt · 590 KB · **~280 ms** *(đo 2026-08-15, **1 lần chạy**; 2026-08-10 là ~580 ms — một lần chạy là một điểm dữ liệu, đừng đọc thành "đã nhanh gấp đôi")*.
Mỗi bản ghi đúng **8 trường**, không hơn: `symbol` `FullName` `exchange` `StockType` `ceiling` `floor` `reference` `tradelot`.
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

*Số này là đo 2026-08-10 và **chưa đo lại** ngày 2026-08-15 — endpoint `getAllQuotes` đo lại được 2.534, nên `/mapping` nhiều khả năng cũng đã là 2.534. Chưa gọi thì chưa sửa.*

---

## `getInstrumentSnapshot`

**Tóm tắt:** Snapshot đầy đủ của một hoặc nhiều mã tại thời điểm gọi.

**Mô tả:** Nguồn khởi tạo trạng thái trước khi chuyển sang nhận cập nhật realtime. Chứa các trường mà kênh realtime **không đẩy** (`open`, `high`, `low`, `ceiling`, `floor`, `reference`), nên bắt buộc gọi một lần lúc mở màn hình.

```
GET BVSC/datafeed/instruments?symbols={tickers}
GET BVSC/datafeed/instruments                     # không tham số → TOÀN BỘ danh mục
```

### Tham số

| Tên | Vị trí | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|---|
| `symbols` | query | string | không | Một hoặc nhiều **ticker**, cách nhau bởi dấu phẩy. **Bỏ hẳn tham số** thì trả toàn bộ danh mục |

⚠️ **`symbols=ALL` KHÔNG dùng được ở endpoint này** — trả `{"s":"ok","d":[]}` *(đo 2026-08-15)*, khác hẳn `/quotes?symbols=ALL`. Muốn toàn bộ thì gọi **không tham số**.

⚠️ **`floorCode` bị bỏ qua im lặng.** Mã nguồn app BVSC dựng URL `?floorCode:XHNF` *(dấu hai chấm)*. Cả `?floorCode:XHNF` lẫn `?floorCode=XHNF` đều trả **nguyên toàn bộ danh mục 3,29 MB**, không báo lỗi *(đo 2026-08-15)*. Muốn lọc phái sinh phải **tự lọc `FloorCode === "03"` phía client**.

### Response 200 — 62 trường

> **Đính chính 2026-08-15.** Tiêu đề này trước ghi *50 trường* — đó là lỗi đếm, không phải mô tả một bản response khác. Đếm thật trên BID · FPT · VNM ngày 2026-08-15 ra **62/62/62 trường**, và ví dụ ngay dưới đây cũng đúng 62 khoá: không thừa khoá nào so với số đo, cũng không thiếu khoá nào. Con số 62 mà [quyết định chọn nguồn](../../20-design/market-field-selection.md) dùng là con số đúng.

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
| `FloorCode` | string | Mã sàn dạng số — `10` HOSE · `02` HNX · `04` UPCOM · **`03` phái sinh** *(đo 2026-08-15)* |
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

---

### Phái sinh — 14 hợp đồng

**Đây là đường duy nhất lấy được phái sinh của BVSC** *(đo 2026-08-15, dữ liệu phiên 14/08/2026)*. Lược đồ **bằng đúng lược đồ cổ phiếu — 62 trường**; khác biệt chỉ nằm ở **trường nào có giá trị**.

Cách lấy: gọi `/datafeed/instruments` **không tham số**, rồi lọc `FloorCode === "03"` *(tương đương `exchange === "XHNF"`)*. Gọi theo mã cũng được: `?symbols=41I1G8000`.

🔴 **Lọc `FloorCode` KHÔNG đủ — endpoint trả cả hợp đồng đã đáo hạn** *(đo 2026-08-27)*: **61 bản ghi** `FloorCode='03'`, trong đó **chỉ 14 còn hiệu lực**. 47 bản ghi kia là hợp đồng cũ vẫn nằm nguyên trong response, **mất `tradingdate` · `Status` · `MaturityDate` · `lastTradingDate` · `ts`**, chỉ còn `ceiling`/`floor`/`reference` cũ — ví dụ `VN30F2509` = *"HDTL VN30 9/2025"*, và `StockId` của chúng là số ngắn (`1219`) thay vì trùng `symbol` như hợp đồng sống.

**Phân biệt:** hợp đồng còn sống có `tradingdate` **và** `Status` khác rỗng. Nhận bừa cả 61 là đăng ký thừa 47 × 20 topic và nạp danh mục rác.

⚠️ Con số **14** ở tiêu đề mục này *(đo 2026-08-15)* vẫn **đúng** — nó đếm hợp đồng sống. Chỗ tài liệu bản cũ chưa nói là **response chứa nhiều hơn thế**.

Hai họ mã cùng tồn tại: mã máy `41I1G9000` *(= "VN30 Index Futures 092026", `StockId` trùng symbol, đây là mã đi trong luồng realtime)* và mã người đọc `VN30F2509` *(chỉ thấy ở nhóm đã hết hạn)*. `underlyingSymbol` phân bố `VN30` 22 · `VN100` 19 · `VGB10` 10 · `VGB05` 9 *(đo 2026-08-27, tính cả hợp đồng chết)*. `openInterest` chỉ có ở **8/14** hợp đồng sống — không phổ quát.

#### Danh mục 14 hợp đồng *(đo 2026-08-15, phiên 14/08/2026)*

| Mã HĐ | Sản phẩm | Cơ sở | GD đầu | GD cuối | Đáo hạn | OI | KL phiên |
|---|---|---|---|---|---|---:|---:|
| `41I1G8000` | VN30 Index Futures 08/2026 | VN30 | 19/06/2026 | 20/08/2026 | 21/08/2026 | 33.220 | **276.881** |
| `41I1G9000` | VN30 09/2026 | VN30 | 16/01/2026 | 17/09/2026 | 18/09/2026 | 3.343 | 1.794 |
| `41I1GC000` | VN30 12/2026 | VN30 | 17/04/2026 | 17/12/2026 | 18/12/2026 | 836 | 103 |
| `41I1H3000` | VN30 03/2027 | VN30 | 17/07/2026 | 18/03/2027 | 19/03/2027 | 219 | 40 |
| `41I2G8000` | **VN100** Index Futures 08/2026 | VN100 | 23/06/2026 | 20/08/2026 | 21/08/2026 | 48 | 40 |
| `41I2G9000` | VN100 09/2026 | VN100 | 20/01/2026 | 17/09/2026 | 18/09/2026 | 12 | 0 |
| `41I2GC000` | VN100 12/2026 | VN100 | 23/04/2026 | 17/12/2026 | 18/12/2026 | 25 | 12 |
| `41I2H3000` | VN100 03/2027 | VN100 | 17/07/2026 | 18/03/2027 | 19/03/2027 | 14 | 3 |
| `41B5G9000` `41B5GC000` `41B5H3000` | TPCP **5 năm** 09/26 · 12/26 · 03/27 | VGB05 | *(rỗng)* | 15/09/26 · 15/12/26 · 15/03/27 | +3 ngày | 0 | 0 |
| `41BAG9000` `41BAGC000` `41BAH3000` | TPCP **10 năm** 09/26 · 12/26 · 03/27 | VGB10 | *(rỗng)* | 25/09/26 · 25/12/26 · 25/03/27 | +5 ngày | 0 | 0 |

- Thanh khoản tập trung gần như tuyệt đối vào **VN30F tháng gần nhất** — 276.881 hợp đồng, **99,3%** tổng KL phái sinh phiên đó.
- **VN100 Index Futures** có niêm yết, gần như không có thanh khoản.
- **Phái sinh TPCP: niêm yết nhưng chưa từng giao dịch** — OI 0, KL 0, `firstTradingDate` rỗng cả 6 mã. *(Suy luận từ **1 phiên**; chuỗi nhiều phiên **chưa kiểm**.)*

**Cấu trúc mã hợp đồng** *(suy ra từ 14 mẫu, **chưa đối chiếu tài liệu HNX**)*:
`41` + `I1`/`I2`/`B5`/`BA` *(VN30 · VN100 · TPCP5 · TPCP10)* + `G`/`H` *(2026 · 2027)* + `8`/`9`/`C`/`3` *(tháng, hex: `C`=12)* + `000`.

#### Trường riêng của phái sinh

| Nhóm | Trường |
|---|---|
| **Chỉ phái sinh mới có giá trị** | `openInterest` · `firstTradingDate` · `lastTradingDate` · `underlyingSymbol` · `MaturityDate` · `exchange: "XHNF"` |
| **Luôn rỗng/0 với cả 14 hợp đồng** *(đừng chờ dữ liệu)* | `openInterestChange` · `foreignRemain` · `foreignRoom` · `PRIOR_PRICE` · `IssuerName` · `CoveredWarrantType` · `ExerciseRatio` · `ListedShare` · `FundType` · `TotalListingQtty` |

#### 🔴 Bẫy nghiêm trọng nhất — `openInterest` của BVSC trễ MỘT PHIÊN

Cùng ngày 14/08/2026, BVSC báo OI của `41I1G8000` = **33.220**, FiinTrade báo `VN30F1M` = **30.427** — lệch 9,2%. Đối chiếu chuỗi OI nhiều phiên của FiinTrade thì ra: **33.220 chính là OI của phiên 13/08**.

Bản ghi BVSC ngày 14/08 chứa `closePrice` 1.878,8 ✅ *(14/08)* · `totalTrading` 276.881 ✅ *(14/08)* · `reference` 1.901,1 ✅ *(đóng cửa 13/08, đúng định nghĩa)* · nhưng `openInterest` **33.220 = OI của 13/08**.

**Kiểm chứng trên cả 4 hợp đồng VN30 — khớp 4/4** *(đo 2026-08-15)*:

| Chuỗi | Hợp đồng | BVSC báo | Fiin 14/08 | Fiin 13/08 | Kết luận |
|---|---|---:|---:|---:|---|
| VN30F1M | `41I1G8000` | 33.220 | 30.427 | **33.220** | trễ 1 phiên |
| VN30F2M | `41I1G9000` | 3.343 | 3.972 | **3.343** | trễ 1 phiên |
| VN30F1Q | `41I1GC000` | 836 | 843 | **836** | trễ 1 phiên |
| VN30F2Q | `41I1H3000` | 219 | 223 | **219** | trễ 1 phiên |

Không phải hai định nghĩa OI khác nhau, cũng không phải sai số — **BVSC trộn hai phiên trong cùng một bản ghi**. Sai lệch bằng 0 khi so với phiên trước, đúng 4/4.

**Hệ quả vận hành:**
- OI lấy từ BVSC phải **dịch nhãn ngày lùi 1 phiên**. Đây là loại lỗi **không có gì báo** — số vẫn hợp lý, chỉ gán sai ngày.
- Giải thích luôn vì sao `openInterestChange` **luôn rỗng**: nguồn không tự tính được biến động khi chính nó chưa có OI phiên hiện tại.
- **Nguồn chuẩn cho OI là FiinTrade `getPriceData`** — xem [`09-fiin-market-price.md`](09-fiin-market-price.md). BVSC chỉ dùng OI khi cần realtime trong phiên, và phải hiểu đó là OI phiên trước.

⚠️ **Phạm vi phép kiểm:** 2 phiên liền kề × 4 hợp đồng, đo lúc thị trường đã đóng. **Chuỗi dài chưa kiểm. OI trong phiên chưa kiểm** — trong phiên hành vi có thể khác.

#### 🔴 Bốn bẫy kiểu dữ liệu *(xác nhận trên dữ liệu thật 2026-08-15)*

1. **`bidPrice1` / `offerPrice1` là CHUỖI, `bidPrice2/3` · `offerPrice2/3` là SỐ.** `"bidPrice1": "1878.0"` vs `"bidPrice2": 1877.3` — cùng thang giá, hai kiểu. Parser cứng kiểu **vỡ đúng ở mức giá tốt nhất**.
2. **`openInterest` là chuỗi** (`"33220"`), không phải số.
3. **`ExercisePrice` là chuỗi `"0.0"`** với cả 14 hợp đồng — có giá trị nhưng vô nghĩa, **đừng đọc thành giá thực hiện**.
4. **`totalTradingValue` ĐÃ nhân hệ số hợp đồng.** `276.881 × 1.892,9 × 100.000 = 5,24×10¹³` khớp đúng `52.411.872.640.000`. Tức **hệ số nhân VN30F = 100.000 VND/điểm** đã nằm sẵn trong giá trị — **không nhân lại lần nữa**.

#### Lịch phiên và các đường phụ

⚠️ **Phiên phái sinh mở lúc 08:45**, sớm hơn cổ phiếu 15 phút — `TVC /symbols` khai `session: "0845-1500"` *(đo 2026-08-15)*. **Lịch ETL phải tính riêng cho phái sinh.**

| Đường | Dùng được với phái sinh | Ghi chú |
|---|---|---|
| [`/datafeed/translogsnaps/{mã HĐ}`](#gettransactionlogsnapshot) | ✅ | 47.723 byte cho `41I1G8000` · ~105 ms · `nextIndex: 100` *(đo 2026-08-15)* |
| [`TVC /symbols` + `/history`](02-bvsc-tvcharts.md) | ✅ nhưng **nông** | Trọn đời hợp đồng, trần ~239 nến; hợp đồng đã đáo hạn vẫn tra được |
| [FiinTrade `getPriceData`](09-fiin-market-price.md) | ✅ và **sâu** | `VN30F1M`/`2M`/`1Q`/`2Q` → **2.233 phiên từ 31/08/2017**, 99 trường |
| Realtime BVSC *(socket)* | **chưa kiểm** | Đo lúc thị trường đóng nên không kiểm được — phải đo trong phiên, khung 08:45–15:00 |
| `/priceservice/derivative/*` | ❌ `404` | Xem [Endpoint đã loại khỏi phạm vi](#endpoint-đã-loại-khỏi-phạm-vi) |

---

### ETF và chứng chỉ quỹ — 31 mã

**31 mã `StockType=3`** *(đo 2026-08-15)*.

✅ **Tách ETF với chứng chỉ quỹ: dùng `FundType` của `/datafeed/instruments`** *(đo 2026-08-27)* — `E` = ETF (20 mã) · `M` = quỹ mở (3 mã) · rỗng (7 mã). `/quotes` **không có** trường này, `StockType=3` của nó gộp chung cả hai loại. *(30 bản ghi `StockType=3` ở instruments vs 31 ở `/quotes` — chênh đúng `VFMVF1`, xem bẫy 11.)* Ngoài giá, endpoint này là nơi duy nhất của BVSC có **số chứng chỉ lưu hành** và **room ngoại** cho quỹ.

| Trường | Kiểu | Mô tả |
|---|---|---|
| `FundType` | string | `E` = ETF · `M` = loại khác. ⚠️ Nghĩa chính xác của `M` **chưa kiểm** — mã `FUCVREIT` là quỹ bất động sản |
| `ListedShare` | string | Số chứng chỉ quỹ đã niêm yết |
| `TotalListingQtty` | string | Tổng số chứng chỉ đang lưu hành |
| `foreignRemain` / `foreignRoom` | integer | Room ngoại còn lại / tổng room |

🔴 **BVSC KHÔNG có NAV.** Không endpoint BVSC nào trả giá trị tài sản ròng của quỹ. Muốn **chênh lệch giá–NAV** *(tín hiệu dòng tiền vào/ra chứng chỉ quỹ)* phải dùng `iNav` và `iIndex` của FiinTrade `getPriceData` — xem [`09-fiin-market-price.md`](09-fiin-market-price.md). Độ phủ `iNav` **chỉ là tập con của 31 mã**, ghi rõ ở đó.

⚠️ **`VFMVF1` có trong `/quotes` nhưng không có trong `/datafeed/instruments`** *(đo 2026-08-15)* — danh sách 31 mã của hai endpoint **không trùng nhau hoàn toàn**.

⚠️ **NAV quỹ mở** *(VESAF, DCDS, VCBF, SSISCA…)*: đã kiểm 2026-08-15, **không nguồn nào trong các nguồn dự án đang dùng có** — ngoài phạm vi, không phải thiếu sót.

---

### Độ phủ & hiệu năng

| Cách gọi | Bản ghi | Kích thước | Độ trễ |
|---|---:|---|---|
| `?symbols={mã}` | 51/51 mã mẫu | ~1,8 KB/mã | ~140 ms |
| Không tham số *(toàn bộ)* | **2.001** — HOSE 768 · UPCOM 823 · HNX 396 · **phái sinh 14** | 3,29 MB *(3.447.763 byte)* | ~309 ms trình duyệt · ~509 ms server-side |

*Số hàng thứ hai đo 2026-08-15, **1 lần chạy mỗi con số** — là một điểm dữ liệu, không phải phân phối. Độ ổn định **chưa kiểm**.*

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

### Response 200 — 33 trường, 20 bản ghi = 18 chỉ số thật + 2 bản ghi rác *(đo lại 2026-08-25)*

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

**18 chỉ số** *(đo 2026-08-25 — khớp đúng danh sách này)*: `HOSE` (VN-Index) · `30` (VN30) · `100` (VN100) · `MID` (VNMID) · `SML` (VNSML) · `XALL` (VNXALL) · `X50` (VNX50) · `SI` (VNSI) · `ALL` · `DIAMOND` · `FINLEAD` · `FINSELECT` · `HNX` · `HNX30` · `HNXFin` · `HNXMSCap` · `HNXMan` · `UPCOM`.

⚠️ **Hai bản ghi rác lẫn trong response, ETL phải lọc** *(đo 2026-08-25 — giải thích mâu thuẫn "20 chỉ số" vs danh sách 18 của bản tài liệu trước)*:
- `marketCode='indexCode'`, `marketId='indexId'` — dòng **header-echo** (tên trường đổ vào giá trị), mọi trường còn lại rỗng;
- `marketCode='0'` — dòng **placeholder toàn số 0** nhưng vẫn mang `tradingdate` của ngày hiện tại.

Luật lọc: bỏ bản ghi có `marketCode` không nằm trong danh mục chỉ số đã biết (hoặc `marketIndex='0'` kèm `marketStatus` rỗng). Đây là cùng họ bẫy "HTTP 200 kèm dữ liệu sai" của bộ giám sát hợp đồng.

### Độ phủ & hiệu năng
20 bản ghi (18 chỉ số thật) · 20 KB *(đo lại 2026-08-25: 20.614 byte)* · ~123 ms *(đo 2026-08-10)*.

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

| Đường dẫn | Kết quả | Ghi chú |
|---|---|---|
| `/datafeed/indexs/getTime` | `200` nhưng luôn rỗng: `{"nextIndex":-1,"marketInfor":[]}` — kể cả trong phiên | — |
| `/datafeed/prevTradingDate` | `404` | — |
| `/datafeed/alltranslogs` | `404` | — |
| `/datafeed/m-instruments` | `500` | — |
| `/priceservice/derivative/snapshot` · `/transactions` | `404` | 🔴 **404 đúng nhưng vô nghĩa — đừng đọc thành "BVSC không có phái sinh".** Đường dẫn thật trong mã nguồn app *(`ProtradeVersion 1.19.6`)* là `/priceservice/derivative/snapshot/q=` và `/priceservice/derivative/transactions/q=`, **cũng 404** *(kiểm 2026-08-15)*. Cả nhóm `/priceservice/` đã chết; dữ liệu phái sinh đi đường [`/datafeed/instruments`](#phái-sinh--14-hợp-đồng) |
| `/priceservice/ptorder/history` · `/adorder/history` | `404` | Cùng nhóm `/priceservice/` đã chết |
| `/priceservice/ceilingfloorcount/snapshot` | `404` | Cùng nhóm `/priceservice/` đã chết |
| `/datafeed/oddlotInstruments` · `/oltranslogsnaps` | Hoạt động nhưng lô lẻ ngoài phạm vi | Loại **có chủ đích**, không phải không có dữ liệu |
