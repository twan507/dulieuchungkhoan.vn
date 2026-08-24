# Khảo sát nguồn PHÁI SINH — BVSC · đo 2026-08-15

Người đo: controller (dò trực tiếp bằng trình duyệt + gọi server-side).
Điểm xuất phát: `https://online.bvsc.com.vn/priceboard/chung-khoan/DERIVATIVE/DERIVATIVEALL`

---

## 0. Kết luận một dòng

**BVSC CÓ dữ liệu phái sinh, đầy đủ và miễn phí.** Tài liệu hiện tại khẳng định ngược lại ở hai chỗ và **cả hai đều sai** — nguyên nhân là khảo sát trước dò nhầm đường dẫn.

---

## 1. 🔴 Hai khẳng định SAI trong tài liệu hiện có

| Chỗ | Câu đang ghi | Sự thật đo được 2026-08-15 |
|---|---|---|
| `01-bvsc-rest.md:72` | "Không chứa phái sinh. BVSC **không cung cấp dữ liệu phái sinh qua bất kỳ endpoint public nào**." | Sai. `/datafeed/instruments` trả đủ 14 hợp đồng với 62 trường, gồm cả `openInterest` |
| `01-bvsc-rest.md:422` + `market-data-store.md:465` | `/priceservice/derivative/snapshot` · `/transactions` → `404`, xếp vào "endpoint đã loại khỏi phạm vi" | 404 là **đúng nhưng vô nghĩa** — đường dẫn thật trong mã nguồn là `/priceservice/derivative/snapshot/q=…`, và ngay cả dạng đúng cũng 404. Dữ liệu phái sinh **không đi qua nhóm `/priceservice/`** mà qua `/datafeed/instruments` |

**Vì sao khảo sát trước kết luận nhầm:** nó suy ra "không có phái sinh" từ `/quotes?symbols=ALL` (2.534 mã, không mã phái sinh nào) — kiểm chứng lại hôm nay: `/quotes?symbols=41I1G8000` trả `{"s":"ok","d":[]}`, tức endpoint `quotes` **thật sự không phục vụ phái sinh**. Quan sát đúng, suy luận sai: sai lầm là mở rộng từ "một endpoint không có" thành "toàn hệ thống không có".

**Bài học phương pháp:** kết luận phủ định về toàn nguồn không được suy từ một endpoint. Phải dò từ ứng dụng thật (trang bảng giá của chính nguồn) mới thấy đường đi.

---

## 2. Cách dò ra (tái lập được)

1. Mở trang bảng giá phái sinh → **không có lời gọi mạng nào của phái sinh trên main thread** (trang dùng web worker + socket).
2. `performance.getEntriesByType('resource')` chỉ thấy `/quotes`, `/mapping`, `/datafeed/chartinday`, `/userdata/time`.
3. Tải bundle `priceboard/static/js/index.3241ea7a.js` (895 KB) và grep chuỗi `derivative` → lộ ra bảng hằng số `PriceService` và các hàm client.
4. Từ đó ra `SECINFO_URL: "/datafeed/instruments"` và bảng `FloorCodes` với `DERIVATIVE_INDEX: "03"`, `DERIVATIVE: "XHNF"`.

Phiên bản ứng dụng quan sát được: `ProtradeVersion 1.19.6`.

### Hằng số rút từ mã nguồn (dùng để tra cứu, không phải endpoint)

```
PriceService.DERIVATIVE_URL              = "/priceservice/derivative/snapshot/q="      → 404 (chết)
PriceService.DERIVATIVE_TRANSACTIONS_URL = "/priceservice/derivative/transactions/q="  → 404 (chết)
PriceService.SECINFO_URL                 = "/datafeed/instruments"                     → 200 ✅ đường thật
FloorCodes.DERIVATIVE_INDEX = "03"   FloorCodes.DERIVATIVE = "XHNF"   derivativeExchanges = ["XHNF"]
```

Host price service = `BASE_URL` = `https://online.bvsc.com.vn` (không phải host riêng; `wss.bvsc.com.vn` là kênh realtime).

---

## 3. Endpoint dùng được — đã gọi thật

Không cần header nào (gọi từ PowerShell server-side, không `Origin`, không cookie → 200).

### 3.1 `GET BVSC/datafeed/instruments` — toàn bộ danh mục *(đường chính)*

| Chỉ số | Đo được 2026-08-15 |
|---|---|
| Bản ghi | **2.001** · HOSE 768 · UPCOM 823 · HNX 396 · **phái sinh (`FloorCode=03`) 14** |
| Kích thước | 3,29 MB (3.447.763 byte) |
| Độ trễ | ~309 ms (trình duyệt) · ~509 ms (server-side, 1 lần chạy) |

⚠️ **`floorCode` không lọc được.** Mã nguồn dựng URL `?floorCode:XHNF` (dấu hai chấm, không phải `=`). Cả `?floorCode:XHNF` lẫn `?floorCode=XHNF` đều trả **nguyên 3,29 MB toàn bộ danh mục** — tham số bị bỏ qua im lặng, không báo lỗi. Muốn lọc phái sinh phải tự lọc `FloorCode === "03"` phía client.

⚠️ **`symbols=ALL` KHÔNG dùng được ở endpoint này** — trả `d: []` rỗng (khác `/quotes?symbols=ALL`). Muốn toàn bộ thì gọi **không tham số**.

### 3.2 `GET BVSC/datafeed/instruments?symbols={mã HĐ}` — snapshot theo mã

3 mã: 5.215 byte · ~104 ms. Nhận nhiều mã cách nhau dấu phẩy.

### 3.3 `GET BVSC/datafeed/translogsnaps/{mã HĐ}` — sổ lệnh khớp trong ngày

Hoạt động với phái sinh: 47.723 byte cho `41I1G8000`, ~105 ms, có `nextIndex: 100` để phân trang. Endpoint này **đã có trong tài liệu** (`01-bvsc-rest.md:241`) nhưng chưa ai ghi là nó phục vụ cả phái sinh.

### 3.4 `GET TVC/symbols?symbol={mã HĐ}` + `GET TVC/history`

Biểu đồ TradingView nhận mã phái sinh. Metadata `41I1G8000`:
`pricescale: 10` · `session: "0845-1500"` · `has_intraday: true` · `exchange-traded: "HNX"`

⚠️ **Phiên phái sinh mở lúc 08:45**, sớm hơn cổ phiếu 15 phút. Lịch ETL phải tính riêng.

---

## 4. Danh mục 14 hợp đồng *(đo 2026-08-15, dữ liệu phiên 14/08/2026)*

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

**Nhận định:**
- Thanh khoản tập trung gần như tuyệt đối vào **VN30F tháng gần nhất** — 276.881 hợp đồng, tức **99,3%** tổng KL phái sinh phiên đó.
- **VN100 Index Futures là sản phẩm mới chưa có trong bất kỳ tài liệu nào của dự án.** Có niêm yết, gần như không có thanh khoản.
- **Phái sinh TPCP: niêm yết nhưng chưa từng giao dịch** — OI = 0, KL = 0, `firstTradingDate` rỗng cả 6 mã. Suy ra: có mặt để đủ bộ sản phẩm, không có giá trị phân tích. *(Suy luận từ 1 phiên; chưa kiểm nhiều phiên.)*

### Giải mã cấu trúc mã hợp đồng *(suy ra từ 14 mẫu, chưa xác nhận với tài liệu HNX)*
`41` + `I1`/`I2`/`B5`/`BA` (VN30 · VN100 · TPCP5 · TPCP10) + `G`/`H` (năm 2026 · 2027) + `8`/`9`/`C`/`3` (tháng, hex: C=12) + `000`.

---

## 5. Lược đồ 62 trường *(BVSC `/datafeed/instruments`)*

Bằng đúng lược đồ cổ phiếu — phái sinh dùng chung cấu trúc, chỉ khác **trường nào có giá trị**.

**Trường CHỈ phái sinh mới có giá trị:** `openInterest` · `firstTradingDate` · `lastTradingDate` · `underlyingSymbol` · `MaturityDate` · `exchange: "XHNF"`

**Trường luôn rỗng/0 với cả 14 hợp đồng** *(đừng chờ dữ liệu)*: `openInterestChange` · `foreignRemain` · `foreignRoom` · `PRIOR_PRICE` · `IssuerName` · `CoveredWarrantType` · `ExerciseRatio` · `ListedShare` · `FundType` · `TotalListingQtty`

### 🔴 Bốn bẫy kiểu dữ liệu đã xác nhận trên dữ liệu thật

1. **`bidPrice1` và `offerPrice1` là CHUỖI, còn `bidPrice2/3`, `offerPrice2/3` là SỐ.**
   `"bidPrice1": "1878.0"` · `"bidPrice2": 1877.3` — cùng một thang giá, hai kiểu. Parser cứng kiểu sẽ vỡ đúng ở mức giá tốt nhất.
2. **`openInterest` là chuỗi** (`"33220"`), không phải số.
3. **`ExercisePrice` là chuỗi `"0.0"`** với cả 14 hợp đồng — có giá trị nhưng vô nghĩa, đừng đọc thành giá thực hiện.
4. **`totalTradingValue` đã nhân hệ số hợp đồng.** `276.881 × 1.892,9 × 100.000 = 5,24×10¹³` khớp đúng `52.411.872.640.000`. Tức **hệ số nhân VN30F = 100.000 VND/điểm** đã nằm sẵn trong giá trị — không nhân lại lần nữa.

---

## 6. Lịch sử — hai đường, sâu khác nhau 9 lần

### 6.1 TVC (`apis.bvsc.com.vn/tvcharts-1.0`) — nông

| Mã | Nến ngày | Khoảng |
|---|---:|---|
| `41I1G8000` | 41 | 19/06/2026 → 14/08/2026 *(trọn đời hợp đồng)* |
| `41I1G7000` *(đã đáo hạn)* | 40 | 22/05/2026 → 16/07/2026 |
| `41I1G6000` *(đã đáo hạn)* | 165 | 17/10/2025 → 18/06/2026 |
| `41I1F8000` *(08/2025)* | 0 | `no_data` |

✅ **Hợp đồng đã đáo hạn VẪN tra được** — quan trọng, cho phép dựng lại chuỗi quá khứ.
⚠️ Chặn ở **trần ~239 nến** đã ghi trong `02-bvsc-tvcharts.md:183` — đo lại hôm nay khớp (VN30: 238 nến từ 03/09/2025). Không mâu thuẫn tài liệu.
⚠️ Nến 1 phút: xin 7 ngày chỉ trả **90 nến của một phiên** (14/08 10:11→13:10, trừ nghỉ trưa) — khớp luật "chỉ phiên gần nhất" ở `02-bvsc-tvcharts.md:179`.

### 6.2 🔵 FiinTrade `getPriceData` — SÂU, và chưa ai biết nó nhận mã phái sinh

`GET FIIN_TECH/PriceData/GetPriceData?Code=VN30F1M&Frequently=Daily&Page=1&PageSize=60`

| Mã | totalCount | Khoảng | Trường |
|---|---:|---|---:|
| `VN30F1M` | **2.233** | 31/08/2017 → 14/08/2026 | 99 |
| `VN30F2M` | 2.233 | *(nt)* | 99 |
| `VN30F1Q` | 2.233 | *(nt)* | 99 |
| `VN30F2Q` | 2.233 | *(nt)* | 99 |
| `VN100F1M` · `GB05F1M` · `GB10F1M` | — | `status:"Failed"`, `"Code not valid"` | — |

**Đây là phát hiện có giá trị nhất của đợt khảo sát:** ~9 năm lịch sử phái sinh, bắt đầu 31/08/2017 — đúng thời điểm HNX khai trương hợp đồng tương lai VN30. 38 trang × PageSize 60.

Dữ liệu giàu hơn hẳn BVSC: có `openInterest`, `totalBuyTrade`/`totalSellTrade` (số lệnh), tách `foreign*Matched` khỏi tổng, `totalDealVolume` (thoả thuận) riêng.

### 6.3 Họ mã chuỗi liên tục *(chỉ TVC mới có VN100)*

| Mã | TVC nến ngày | Khớp hợp đồng |
|---|---:|---|
| `VN30F1M` | 238 (từ 03/09/2025) | `41I1G8000` — close 1.878,8 ✅ trùng khít |
| `VN30F2M` | 238 | `41I1G9000` — 1.875,0 ✅ |
| `VN30F1Q` | 238 | `41I1GC000` — 1.873,4 ✅ |
| `VN30F2Q` | 238 | `41I1H3000` — 1.882,5 ✅ |
| `VN100F1M` | 211 (từ 10/10/2025) | VN100 tháng gần |
| `GB05F1M` · `VN30F` | `no_data` | không tồn tại |

Bốn mã VN30F* đối chiếu giá đóng cửa **trùng khít** với 4 hợp đồng tương ứng → xác nhận đây là chuỗi nối tự động theo vị thế (1M/2M/1Q/2Q), không phải series độc lập.

---

## 7. 🔴 Bẫy nghiêm trọng nhất — `openInterest` của BVSC trễ MỘT PHIÊN

Xuất phát từ một mâu thuẫn: cùng ngày 14/08/2026, BVSC báo OI của `41I1G8000` = **33.220**, FiinTrade báo `VN30F1M` = **30.427** — lệch 9,2%.

Truy ra nguyên nhân bằng chuỗi OI nhiều phiên của FiinTrade:

| Phiên | OI (FiinTrade) | KL khớp | Đóng cửa |
|---|---:|---:|---:|
| **14/08/2026** | **30.427** | 276.881 | 1.878,8 |
| **13/08/2026** | **33.220** | 220.290 | 1.901,1 |
| 12/08/2026 | 30.390 | 227.139 | 1.940,0 |

Bản ghi BVSC ngày 14/08 chứa: `closePrice` 1.878,8 ✅ *(14/08)* · `totalTrading` 276.881 ✅ *(14/08)* · `reference` 1.901,1 ✅ *(đóng cửa 13/08 — đúng theo định nghĩa giá tham chiếu)* · nhưng `openInterest` **33.220 = OI của 13/08**, không phải 14/08.

### Kiểm chứng trên cả 4 hợp đồng VN30 — khớp 4/4

| Chuỗi | Hợp đồng | BVSC báo | Fiin 14/08 | Fiin 13/08 | Kết luận |
|---|---|---:|---:|---:|---|
| VN30F1M | `41I1G8000` | 33.220 | 30.427 | **33.220** | trễ 1 phiên |
| VN30F2M | `41I1G9000` | 3.343 | 3.972 | **3.343** | trễ 1 phiên |
| VN30F1Q | `41I1GC000` | 836 | 843 | **836** | trễ 1 phiên |
| VN30F2Q | `41I1H3000` | 219 | 223 | **219** | trễ 1 phiên |

**Kết luận:** không phải hai định nghĩa OI khác nhau, cũng không phải sai số — **BVSC trộn hai phiên trong cùng một bản ghi**. Giá và khối lượng là phiên hiện tại, `openInterest` là phiên trước. Đúng 4/4, sai lệch bằng 0 khi so với phiên trước.

**Hệ quả vận hành:**
- OI lấy từ BVSC phải **dịch nhãn ngày lùi 1 phiên**, nếu không toàn bộ phân tích OI sẽ lệch pha một ngày. Đây là loại lỗi không có gì báo — số vẫn hợp lý, chỉ gán sai ngày.
- Điều này giải thích luôn vì sao `openInterestChange` **luôn rỗng** ở BVSC: nguồn không tự tính được biến động khi chính nó chưa có OI của phiên hiện tại.
- **Chọn FiinTrade `getPriceData` làm nguồn chuẩn cho OI.** BVSC chỉ dùng OI khi cần realtime trong phiên, và phải hiểu đó là OI phiên trước.

Mức độ quan trọng: OI là tín hiệu cốt lõi của phân tích phái sinh trong corpus (HP4 và HP6 đều dùng OI làm chỉ báo chính), nên lệch một phiên là lỗi làm hỏng kết luận chứ không phải sai số nhỏ.

*(Cảnh báo phạm vi: kiểm trên 2 phiên liền kề × 4 hợp đồng. Chưa kiểm chuỗi dài, chưa kiểm trong phiên — trong phiên OI có thể lại là số khác.)*

Bẫy phụ đã thấy: FiinTrade `percentValueChange = -0.01` trong khi BVSC `changePercent = -1.1730051023091894`. FiinTrade trả **phân số làm tròn 2 chữ số** → mất gần hết độ chính xác. Dùng BVSC hoặc tự tính từ `valueChange/referenceValue`.

---

## 8. Còn để ngỏ — chưa kiểm

- **Realtime phái sinh.** `11-bvsc-realtime.md` ghi 53 topic đo trên cổ phiếu; chưa thử topic nào với mã phái sinh. Đo lúc thị trường đóng cửa (`tradingSessionID: "CLOSED"`) nên không kiểm được. Cần đo trong phiên.
- **Chuỗi TPCP nhiều phiên.** Kết luận "chưa từng giao dịch" dựa trên 1 phiên.
- **Độ trễ/ổn định `/datafeed/instruments`** — mỗi con số ở trên là **1 lần chạy**, không phải phân phối.
- **Nến 1 phút cho phái sinh nhiều phiên** — chỉ xác nhận được luật "phiên gần nhất".
- **OI trong `getPriceData` có bị vá hồi tố không.**
- **OI trong phiên** — bẫy "trễ một phiên" mới kiểm khi thị trường đã đóng; trong phiên hành vi có thể khác.

## 9. Đề xuất đưa vào tài liệu

1. **Sửa hai khẳng định sai** ở `01-bvsc-rest.md:72` và mục "endpoint đã loại khỏi phạm vi" — kèm ghi rõ vì sao kết luận cũ sai (giá trị phương pháp).
2. Bỏ "Phái sinh" khỏi *Ngoài phạm vi* ở `10-sources/README.md:49`.
3. Bổ sung `/datafeed/instruments` phần phái sinh + `getPriceData` nhận `VN30F*` vào `09-fiin-market-price.md`.
4. Ghi 4 bẫy kiểu dữ liệu vào `00-conventions.md`.
5. Ghi bẫy "OI trễ một phiên" vào `00-conventions.md` như bẫy cấp 🔴, kèm bảng kiểm chứng 4/4 — và chốt FiinTrade là nguồn chuẩn cho OI.

## Dữ liệu thô

`scratchpad/bvsc-deriv-2026-08-15/` — 13 file JSON (instruments toàn bộ 3,29 MB, snapshot 3 mã, translog, 8 file lịch sử, 6 file FiinTrade).
