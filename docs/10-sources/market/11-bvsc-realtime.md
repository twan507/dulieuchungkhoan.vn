# 11 — Realtime BVSC (Socket.IO)

Endpoint: `wss://wss.bvsc.com.vn/market/socket.io/`
Giao thức: **Socket.IO v2 trên nền Sails.js** — không phải Socket.IO thuần
Xác thực: không có

Một kết nối duy nhất phục vụ toàn bộ nhu cầu realtime: giá, sổ lệnh, khớp lệnh, chỉ số, thoả thuận.

**Số liệu trong tài liệu này** đo trong phiên chiều 10/08/2026, 13:08–13:12, **3.266 frame** trên 53 topic đăng ký, 12 mã cả ba sàn — **bổ sung bằng phiên đo 2026-08-26** (2.316.573 frame, 6.322 topic, 2.007 mã, trọn phiên chiều 12:56–15:10): xem [hồ sơ phiên đo](../../90-records/surveys/2026-08-26-bvsc-realtime-session/README.md). Mọi mục đã đo lại đều gắn nhãn *(đo 2026-08-26)*.

> 🔴 **BẮT BUỘC ĐỌC TRƯỚC KHI VIẾT CLIENT — frame thật có VỎ BỌC** *(đo 2026-08-26)*. Các mẫu JSON ở §4–§8 dưới đây là **bản ghi bên trong**, không phải nguyên văn frame. Frame thật:
>
> ```
> 42["t",{"a":"i","d":[ {"TD":"26/08/2026","FV":"1","SB":"41I1G9000", ...} ]}]
> ```
>
> Bản ghi nằm trong **mảng `d`**; `a` là cờ lớp vận chuyển (`u` cập nhật · `i` chèn), không phải trường dữ liệu. Đo trên 2.316.573 frame: `d` luôn đúng **1 phần tử**, nhưng client vẫn nên duyệt mảng. Không bóc vỏ thì **mọi frame thật đều hỏng ở cổng ép kiểu** mà không có lỗi socket nào — đúng loại bẫy "gọi thật vẫn chưa đủ".

---

## 1. Thiết lập kết nối

### 1.1 URL

```
wss://wss.bvsc.com.vn/market/socket.io/
    ?EIO=3
    &transport=websocket
    &__sails_io_sdk_version=1.2.1
    &__sails_io_sdk_platform=browser
    &__sails_io_sdk_language=javascript
```

| Tham số | Giá trị | Bắt buộc |
|---|---|---|
| `EIO` | `3` | **bắt buộc** — Engine.IO v3 |
| `transport` | `websocket` | **bắt buộc** — server **chỉ** nhận WebSocket, không hỗ trợ HTTP long-polling |
| `__sails_io_sdk_*` | như trên | Của Sails.js SDK. Kết nối vẫn thành công nếu thiếu, nhưng nên gửi để đồng nhất với client gốc |

⚠️ Thử handshake qua HTTP polling (`transport=polling`) sẽ nhận `400 {"code":0,"message":"Transport unknown"}`.

### 1.2 Trình tự bắt tay

```
1. Mở WebSocket
2. Server gửi:  0{"sid":"...","upgrades":[],"pingInterval":25000,"pingTimeout":60000,...}
3. Server gửi:  40                       ← sẵn sàng nhận lệnh
4. Client gửi:  42<ackId>["get", {...}]  ← đăng ký topic
5. Server gửi:  43<ackId>[{...}]         ← xác nhận
6. Server gửi:  42["<event>", {...}]     ← luồng dữ liệu
```

| Tham số kết nối | Giá trị |
|---|---|
| `pingInterval` | 25.000 ms |
| `pingTimeout` | 60.000 ms |
| `upgrades` | `[]` — đã là WebSocket, không nâng cấp thêm |

### 1.3 Đăng ký topic

```javascript
ws.send('421["get",{"url":"/client/subscribe","method":"get","headers":{},'
      + '"data":{"op":"subscribe","args":["i:BID","o10:BID","t:BID","idx:HOSE"]}}]');
```

Trong đó `421` = mã frame `42` + `ackId` là `1`. Server trả về:

```
431[{"body":{"result":[],"request":{"op":"subscribe","args":[...]}},"headers":{},"statusCode":200}]
```

**Huỷ đăng ký:** đổi `"op": "subscribe"` thành `"op": "unsubscribe"`.

### 1.4 🔴 Ack `statusCode: 200` KHÔNG có nghĩa là topic hợp lệ

Server chấp nhận **mọi** chuỗi topic và luôn trả `statusCode: 200`, kể cả topic không tồn tại hoặc không được phục vụ. Không có cách nào biết topic sai ngoài việc **không nhận được frame nào**.

Đây là nguyên nhân của bẫy `o:` mô tả ở mục 3.

### 1.5 Kết nối rớt và tự nối lại

Quan sát **2 lần rớt trong 4 phút** đo liên tục. Client phải tự nối lại và **đăng ký lại toàn bộ topic** — server không nhớ trạng thái đăng ký cũ.

Ứng dụng BVSC gốc nối lại sau `5000 ms`.

---

## 2. Danh sách topic

| Topic | Định dạng | Nội dung | Tên sự kiện nhận về |
|---|---|---|---|
| `i:<mã>` | ticker | Snapshot delta: giá, 3 bậc, khối ngoại | `i` |
| **`o10:<mã>`** | ticker | Sổ lệnh 3 bậc | **`o`** |
| `t:<mã>` | ticker | Từng lệnh khớp | `t` |
| `idx:<mã chỉ số>` | mã chỉ số | Chỉ số thị trường | `idx` |
| `ptm:<sàn>` | `HOSE`\|`HNX`\|`UPCOM` | Thoả thuận đã khớp | `ptm` |

⚠️ Topic dùng **ticker**, không phải `organCode`. Đây là điểm khác biệt so với API FiinTrade.

⚠️ **Tên topic đăng ký khác tên sự kiện nhận về** ở trường hợp sổ lệnh: đăng ký `o10:`, nhận sự kiện `o`.

### Mã chỉ số hỗ trợ — đã xác minh 15 mã

`HOSE` (VN-Index) · `30` (VN30) · `100` (VN100) · `MID` · `SML` · `XALL` · `X50` · `SI` · `ALL` · `DIAMOND` · `FINLEAD` · `FINSELECT` · `HNX` · `HNX30` · `UPCOM`

Tất cả 15 mã đều đẩy dữ liệu. Mã chỉ số ở đây trùng quy ước của [`getIndexSnapshots`](01-bvsc-rest.md), **khác** quy ước của tvcharts (`VNINDEX`, `HNXIndex`).

---

## 3. 🔴 Bẫy nghiêm trọng — topic `o:` không hoạt động

Topic sổ lệnh **phải đăng ký bằng `o10:`**. Topic `o:` được server chấp nhận, trả ack `statusCode: 200`, rồi **không bao giờ đẩy dữ liệu**.

### Bằng chứng — phép thử đối chứng

Trong cùng một kết nối, cùng khoảng thời gian, 8 mã thanh khoản cao:

| Đăng ký bằng | Mã | Frame sổ lệnh nhận được |
|---|---|---|
| `o10:` | BID · VNM · SHS · VGI | **138 · 180 · 195 · 57** |
| `o:` | HPG · SSI · PVS · ACV | **0 · 0 · 0 · 0** |

HPG và SSI là hai mã hoạt động mạnh nhất trong nhóm — cùng lúc đó chúng đẩy 39 và 40 frame `i:`, 10 và 13 frame `t:`. Việc không có frame sổ lệnh nào không thể do thị trường trầm lắng.

Phép thử đảo ngược (đổi nhóm mã giữa `o:` và `o10:`) cho kết quả nhất quán.

**Hệ quả:** dùng `o:` sẽ khiến sổ lệnh trống hoàn toàn mà không có lỗi nào để truy vết.

### Số bậc giá — luôn là 3, mọi sàn

Dù tên topic là `o10`, dữ liệu chỉ có **`TOP` = 1, 2, 3**:

| Mã | Sàn | Bậc nhận được |
|---|---|---|
| BID, VNM | HOSE | 1, 2, 3 |
| SHS | HNX | 1, 2, 3 |
| VGI | UPCOM | 1, 2, 3 |

Đã kiểm chứng thêm trên HPG, SSI, CEO, PVS ở các phiên đo trước — kết quả giống nhau.

---

## 4. Sự kiện `i` — Snapshot delta (34 trường)

**Cơ chế delta:** mỗi frame **chỉ chứa những trường vừa thay đổi**, cộng ba trường định danh luôn có mặt. Client phải giữ trạng thái và ghép chồng.

```json
{"EX":"HOSE","t":1786330492737,"U2":43500,"SB":"BID"}
```

### Bảng trường

| Trường | Ý nghĩa | Đơn vị | Tần suất* |
|---|---|---|---|
| `SB` | Mã chứng khoán | — | 100% |
| `EX` | Sàn | — | 100% |
| `t` | Thời điểm, epoch ms | — | 100% |
| `B1` `B2` `B3` | Giá mua bậc 1–3 | VND | thấp |
| `V1` `V2` `V3` | Khối lượng mua bậc 1–3 | cổ phiếu | **cao nhất** |
| `S1` `S2` `S3` | Giá bán bậc 1–3 | VND | thấp |
| `U1` `U2` `U3` | Khối lượng bán bậc 1–3 | cổ phiếu | **cao** |
| `TB` | Tổng dư mua | cổ phiếu | trung bình |
| `TO` | Tổng dư bán | cổ phiếu | trung bình |
| `CP` | Giá khớp gần nhất | VND | trung bình |
| `CH` | Thay đổi so với tham chiếu | VND | trung bình |
| `CHP` | Thay đổi phần trăm | % | trung bình |
| `AP` | Giá bình quân | VND | thấp |
| `HI` | Giá cao nhất phiên | VND | rất thấp |
| `CV` | Khối lượng lệnh khớp gần nhất | cổ phiếu | cao |
| `P1` | Khối lượng lệnh khớp gần nhất | cổ phiếu | cao |
| `P2` | Giá lệnh khớp gần nhất | VND | trung bình |
| `TT` | Tổng khối lượng khớp | cổ phiếu | cao |
| `TV` | Tổng giá trị khớp | VND | cao |
| `FB` | Khối ngoại mua | cổ phiếu | rất thấp |
| `FS` | Khối ngoại bán | cổ phiếu | rất thấp |
| `FR` | Room ngoại còn lại | cổ phiếu | thấp |
| `PMP` | Giá lệnh thoả thuận gần nhất | VND | rất thấp |
| `PMQ` | Khối lượng lệnh thoả thuận gần nhất | cổ phiếu | rất thấp |
| `PTQ` | Luỹ kế khối lượng thoả thuận | cổ phiếu | rất thấp |
| `PTV` | Luỹ kế giá trị thoả thuận | VND | rất thấp |

\* Tần suất xuất hiện trong 843 frame `i` đo được: `V1` 292 lần · `U1` 272 · `TT`/`TV` 221 · `P1`/`CV` 190 · `TO` 141 · `TB` 123 · `CH`/`CHP`/`CP` 72 · `FR` 53 · `AP` 25 · `FS` 22 · `FB` 16 · `PMP`/`PMQ`/`PTQ`/`PTV` 2 · `HI` 1.

### Cách xác minh bảng trường

Sáu trường được xác minh **khớp giá trị tuyệt đối** với [`getInstrumentSnapshot`](01-bvsc-rest.md) tại cùng thời điểm:

| Realtime | REST | Giá trị (BID) |
|---|---|---|
| `U1` | `offerVol1` | 27.700 |
| `U2` | `offerVol2` | 54.500 |
| `TT` | `totalTrading` | 999.200 |
| `TV` | `totalTradingValue` | 39.492.260.000 |
| `CV` | `closeVol` | 1.100 |
| `P1` | `priceOne` | 1.100 |
| `FR` | `foreignRemain` | 908.366.228 |

Các trường còn lại suy ra theo đối xứng (`B`↔`S`, `V`↔`U`) và xác nhận chéo bằng mẫu chứng quyền `CACB2602` (`B1:50.0, B2:40, B3:30` — giá mua giảm dần đúng quy luật sổ lệnh).

Nhóm `PMP`/`PMQ`/`PTQ`/`PTV` khớp tên với `PT_MATCH_PRICE` / `PT_MATCH_QTTY` / `PT_TOTAL_TRADED_QTTY` / `PT_TOTAL_TRADED_VALUE` bên REST.

### ⚠️ Trường KHÔNG được đẩy — **đính chính 2026-08-26**

`ceiling` · `floor` · `reference` — vẫn đúng, phải lấy từ [`getInstrumentSnapshot`](01-bvsc-rest.md) khi khởi tạo.

🔴 **`open` và `low` THÌ CÓ được đẩy** *(đo 2026-08-26)* — dưới tên `OP` và `LO`, hai trong ba khoá không có trong bảng 34 trường (khoá thứ ba: `TSI`, giá trị quan sát `"OPEN"`, chỉ thấy ở mã phái sinh). Mẫu thật: `{"SB":"WCS","EX":"HNX","t":1787724001934,"OP":290600,"LO":290600,"HI":290600,"CP":290600,...}`. Ghi chú cũ ("không được đẩy") dựa trên mẫu 843 frame/4 phút của đợt 2026-08-15 — quá ngắn để thấy trường hiếm. `HI` (cao nhất) có xuất hiện nhưng cực hiếm (1/843 frame) — không nên phụ thuộc, nên tự tính từ luồng `t`.

### ⚠️ Danh sách trường có thể chưa đầy đủ — **xác nhận 2026-08-26: KHÔNG đóng**

Phiên đo 2026-08-26 (519.133 frame `i`) thấy **37 khoá phân biệt** — 34 khoá cũ **cộng** `OP`, `LO`, `TSI`. Không khoá cũ nào biến mất. ⇒ Client **phải** có chỗ chứa trường lạ (dự án đưa vào cột `extra` JSON), đừng giả định danh sách đóng.

Số trường quan sát được tăng dần theo thời gian đo *(đợt 2026-08-15)*: 22 → 27 → 29 → 33 → **34**, ổn định từ giây thứ 142. Các trường hiếm (`HI`, `PMP`, `PMQ`, `PTQ`, `PTV`) chỉ lộ ra khi có sự kiện tương ứng. **Không loại trừ còn trường khác chưa xuất hiện** — ví dụ trường giá thấp nhất phiên, hoặc trạng thái phiên. Client nên xử lý trường lạ một cách an toàn thay vì giả định danh sách đóng.

---

## 5. Sự kiện `o` — Sổ lệnh (11 trường)

Đăng ký bằng **`o10:<mã>`**. Mỗi frame mô tả **một bậc giá**, không phải cả sổ lệnh.

```json
{"ACT":"U","TOP":"1","t":1786342135726,"id":"SHS:1",
 "BP":"15800.0","BQ":"544200","SP":"15900.0","SQ":"557400",
 "CBV":"544200","CSV":"557400","SB":"SHS"}
```

| Trường | Kiểu | Đơn vị | Mô tả |
|---|---|---|---|
| `SB` | string | — | Mã chứng khoán |
| `TOP` | string | — | **Bậc giá: `1`, `2`, `3`** |
| `id` | string | — | Khoá tổng hợp `{mã}:{bậc}`, ví dụ `SHS:1` |
| `ACT` | string | — | Hành động. Quan sát thấy `U` = cập nhật |
| `BP` | string | VND | Giá mua bậc này |
| `BQ` | string | cổ phiếu | Khối lượng mua bậc này |
| `SP` | string | VND | Giá bán bậc này |
| `SQ` | string | cổ phiếu | Khối lượng bán bậc này |
| `CBV` | string | cổ phiếu | Khối lượng mua luỹ kế tới bậc này |
| `CSV` | string | cổ phiếu | Khối lượng bán luỹ kế tới bậc này |
| `t` | integer | epoch ms | Thời điểm |

⚠️ **Toàn bộ giá trị số trả về dưới dạng chuỗi**, kể cả khối lượng. Phải ép kiểu.

Dùng `id` làm khoá để cập nhật đúng ô trong bảng sổ lệnh.

---

## 6. Sự kiện `t` — Lệnh khớp (10 trường)

```json
{"TD":"10/08/2026","FT":"13:08:56","SB":"ACV","FV":"100","LC":"S",
 "FMP":"42100.0","FCV":"1000.0","SM":"74027",
 "AVO":"590000","AVA":"24983210000.0"}
```

| Trường | Kiểu | Đơn vị | Mô tả |
|---|---|---|---|
| `SB` | string | — | Mã chứng khoán |
| `TD` | string | — | Ngày giao dịch `dd/MM/yyyy` |
| `FT` | string | — | **Giờ khớp `HH:mm:ss`** |
| `FMP` | string | VND | Giá khớp |
| `FV` | string | cổ phiếu | Khối lượng lệnh này |
| `FCV` | string | VND | Thay đổi so với tham chiếu |
| **`LC`** | string | — | **Chiều chủ động: `B` = mua chủ động (BU) · `S` = bán chủ động (SD)** |
| `SM` | string | — | Số thứ tự message từ sở |
| `AVO` | string | cổ phiếu | Tổng khối lượng khớp luỹ kế |
| `AVA` | string | VND | Tổng giá trị khớp luỹ kế |

Trường `LC` là nguồn duy nhất cho chỉ báo BU/SD ở cấp từng lệnh. Cùng thông tin này ở REST là `lastColor` trong [`getTransactionLogSnapshot`](01-bvsc-rest.md).

⚠️ Giá trị số cũng trả về dạng chuỗi.

---

## 7. Sự kiện `idx` — Chỉ số (18 trường)

```json
{"MC":"X50","MI":"3230.86","ICH":"22.75","IPC":"0.71","IT":"13:09:00",
 "TD":"10/08/2026","TV":"215271860.0","TVA":"5719734825450.0",
 "AV":"202854146","DV":"12417714","NCV":"0","DE":"6","NC":"0",
 "t":1786342140044}
```

| Trường | Đơn vị | Mô tả |
|---|---|---|
| `MC` | — | **Mã chỉ số** |
| `MI` | điểm | Giá trị chỉ số |
| `ICH` | điểm | Thay đổi tuyệt đối |
| `IPC` | % | Thay đổi phần trăm |
| `IT` | — | Giờ cập nhật chỉ số `HH:mm:ss` |
| `TD` | — | Ngày giao dịch |
| `TV` | cổ phiếu | Tổng khối lượng khớp |
| `TVA` | VND | Tổng giá trị khớp |
| `ADV` | mã | Số mã tăng giá |
| `DE` | mã | Số mã giảm giá |
| `NC` | mã | Số mã đứng giá |
| `AV` | cổ phiếu | Khối lượng nhóm tăng |
| `DV` | cổ phiếu | Khối lượng nhóm giảm |
| `NCV` | cổ phiếu | Khối lượng nhóm đứng giá |
| `NOC` | mã | Số mã trần *(rất hiếm — 1/621 frame)* |
| `PTT` | — | Luỹ kế thoả thuận — số lệnh hoặc khối lượng *(chưa xác định rõ)* |
| `PTV` | VND | Luỹ kế giá trị thoả thuận |
| `t` | epoch ms | Thời điểm |

Tên trường tương ứng với [`getIndexSnapshots`](01-bvsc-rest.md): `MI`↔`marketIndex`, `ICH`↔`indexChange`, `ADV`↔`advances`, `AV`↔`advancesVolumn`, `NOC`↔`numberOfCe`.

⚠️ Cũng theo cơ chế **delta** — mẫu trên thiếu `ADV`, `NOC`, `PTT` vì chúng không đổi tại thời điểm đó.

**Ba khoá ngoài bảng 18 trường** *(đo 2026-08-26, 17.770 frame `idx`)*: `IC` (giá trị `"up"` — khớp dấu của `ICH`), `MS` (giá trị `"5"`), `NOF` (giá trị `"1"`). **Ý nghĩa `MS`/`NOF` chưa xác định** — ghi lại để không rơi mất, không suy đoán.

---

## 8. Sự kiện `ptm` — Thoả thuận đã khớp (13 trường)

Đăng ký theo **sàn**, nhưng frame trả về theo **từng mã**.

```json
{"SB":"DBC","MC":"HOSE","TD":"10/08/2026","TI":"13:09:17",
 "PR":"16650.0","MVL":590000,"RE":16650,"CE":17800,"FL":15500,
 "CNO":"VN000000DBC2-mdds:0:682530462/GSTO000009:1211905",
 "LS":1786342157,"MKI":"10","IAC":true}
```

| Trường | Kiểu | Đơn vị | Mô tả |
|---|---|---|---|
| `SB` | string | — | Mã chứng khoán |
| `MC` | string | — | Sàn |
| `TD` | string | — | Ngày giao dịch |
| `TI` | string | — | Giờ khớp `HH:mm:ss` |
| `PR` | string | VND | Giá thoả thuận |
| `MVL` | integer | cổ phiếu | Khối lượng |
| `RE` | integer | VND | Giá tham chiếu |
| `CE` | integer | VND | Giá trần |
| `FL` | integer | VND | Giá sàn |
| `CNO` | string | — | Định danh lệnh, chứa mã ISIN và số hiệu |
| `LS` | integer | epoch **giây** | Dấu thời gian — ⚠️ đơn vị **giây**, khác `t` của các sự kiện khác |
| `MKI` | string | — | Mã sàn dạng số (`10` = HOSE) |
| `IAC` | boolean | — | Cờ trạng thái |

### Tần suất

**Rất thưa.** Trong 239 giây đo chỉ nhận **6 frame**, thuộc 5 mã khác nhau (`DBC`, `PVS`, `MWG`, `HUT`, `KSV`) trên cả HOSE và HNX. Giao diện cần thiết kế trạng thái rỗng — có thể nhiều phút không có lệnh thoả thuận nào.

---

## 9. Topic `pth` — không quan sát được dữ liệu

`pth:<sàn>` được cho là kênh **chào mua / chào bán thoả thuận** (lệnh quảng cáo chưa khớp). Trong mã nguồn ứng dụng BVSC, sự kiện `pth` được xử lý bởi `updateDataPutthrough`, tách biệt với `updateDataPTMatch` của `ptm`, và bản ghi có trường `MarketCode`.

**Kết quả kiểm thử: 0 frame.**

| Lần đo | Thời lượng | Sàn | Frame |
|---|---|---|---|
| 1–4 | ~124 s | HOSE, HNX, UPCOM + biến thể mã sàn số (`10`, `02`, `04`) | 0 |
| 5 | 239 s | HOSE, HNX, UPCOM | 0 |

Tổng cộng **~6 phút** trong giờ giao dịch, cùng lúc `ptm` vẫn nhận được frame. Hai khả năng: kênh đã ngừng phát, hoặc không có lệnh chào thoả thuận trong khoảng đo.

Hai endpoint REST đối ứng `/priceservice/ptorder/history/` và `/priceservice/adorder/history/` đều trả `404` trên host public.

**Đo lần hai 2026-08-26:** đăng ký `pth` cả 3 sàn suốt **2 giờ 13 phút** (12:56–15:10) — vẫn **0 frame**, trong khi `ptm` nhận 1.426 frame cùng lúc.

**Kết luận:** không đưa `pth` vào phạm vi. Hai lần đo độc lập đều trống, nhưng **vẫn chưa đủ để tuyên "không có"** — kênh có thể chỉ sống khi có lệnh chào thoả thuận. Cần BVSC xác nhận.

---

## 10. Tần suất frame đo được

Đo trong 239 giây phiên chiều, 12 mã, thị trường hoạt động bình thường.

### Theo loại sự kiện

| Sự kiện | Tổng frame | Tỷ lệ |
|---|---|---|
| `i` | 1.350 | 41% |
| `o` | 933 | 29% |
| `idx` | 621 | 19% |
| `t` | 356 | 11% |
| `ptm` | 6 | 0,2% |
| **Tổng** | **3.266** | |

### Theo mã — frame/giây

| Topic | Tần suất |
|---|---|
| `o:SHS` | 1,41 |
| `o:VNM` | 1,08 |
| `i:SSI` | 1,01 |
| `o:BID` | 0,99 |
| `i:HPG` | 0,83 |
| `i:FPT` | 0,72 |
| `i:PVS` | 0,63 |
| `i:CEO` | 0,61 |
| `o:VGI` | 0,48 |
| `t:SSI` | 0,29 |

Chỉ số ổn định ở khoảng **0,09 frame/giây** mỗi mã chỉ số (9 frame / 100 giây).

### Ước lượng tải

Với một mã thanh khoản cao, tổng cả `i` + `o` + `t` vào khoảng **2–2,5 frame/giây**. Bảng giá hiển thị 50 mã đồng thời sẽ nhận cỡ **100 frame/giây** trong giờ cao điểm.

### Tải TOÀN THỊ TRƯỜNG — đo thật *(2026-08-26, 2.007 mã + 15 chỉ số + 3 sàn, phiên chiều trọn vẹn)*

| Sự kiện | Frame | Tỷ lệ |
|---|---:|---:|
| `o` | 1.647.375 | 71,1% |
| `i` | 519.133 | 22,4% |
| `t` | 130.869 | 5,6% |
| `idx` | 17.770 | 0,8% |
| `ptm` | 1.426 | 0,1% |
| **Tổng** | **2.316.573** | |

**289,5 frame/giây trung bình**, **đỉnh 704,8 frame/giây** lúc 13:00 (mở lại sau nghỉ trưa). Nhân đôi thô cho cả ngày (**chưa đo phiên sáng**): **~4,6 triệu dòng/ngày**. Tỷ lệ giữa các sự kiện đảo hẳn so với mẫu 12 mã của đợt trước — `o` chiếm ưu thế tuyệt đối khi đăng ký toàn thị trường.

---

## 11. Tóm tắt điểm cần nhớ

1. **Đăng ký sổ lệnh bằng `o10:`, không phải `o:`.** Sai sẽ không có dữ liệu và không có lỗi.
2. **Ack `statusCode: 200` không xác nhận topic hợp lệ.**
3. **Topic dùng ticker**, khác API FiinTrade dùng `organCode`.
4. **`i` và `idx` là delta** — phải giữ trạng thái, không ghi đè toàn bộ.
5. **Mọi giá trị số ở `o`, `t`, `idx` đều là chuỗi.**
6. **`open`/`low`/`ceiling`/`floor`/`reference` không được đẩy** — lấy từ REST khi khởi tạo.
7. **Sổ lệnh chỉ 3 bậc** trên mọi sàn.
8. **Phải tự nối lại và đăng ký lại** khi rớt — quan sát 2 lần rớt trong 4 phút.
9. **Danh sách 34 trường của `i` KHÔNG đóng** — *(đo 2026-08-26)* thực tế 37 khoá, thêm `OP`/`LO`/`TSI`; `idx` thêm `IC`/`MS`/`NOF`. Phải có chỗ chứa trường lạ.
10. **`ptm` rất thưa, `pth` không có dữ liệu** (0 frame qua hai đợt đo, tổng ~2,4 giờ).
11. 🔴 **Frame thật có vỏ `{"a":…,"d":[…]}`** — mẫu ở §4–§8 là bản ghi bên trong. Không bóc vỏ = hỏng toàn bộ, im lặng.
12. **`open`/`low` CÓ được đẩy** dưới tên `OP`/`LO` — đính chính §4.
13. **Phái sinh không có kênh riêng**: đi chung `i`/`o`/`t`, phân biệt bằng `EX="XHNF"`, **không có `openInterest`** *(đo 2026-08-26)*.
