# 02 — Biểu đồ lịch sử BVSC (`apis.bvsc.com.vn/tvcharts-1.0`)

Base URL: `https://apis.bvsc.com.vn/tvcharts-1.0` — ký hiệu `TVC`
Header: không bắt buộc.

Đây là **UDF datafeed chuẩn TradingView** (Universal Data Feed). Nếu dùng thư viện Charting Library của TradingView thì có thể trỏ thẳng `datafeedUrl` vào base URL này mà không cần adapter.

4 endpoint. Định danh bằng **ticker**, không phải `organCode`.

---

## `getChartConfig`

**Tóm tắt:** Khai báo năng lực của datafeed. Thư viện TradingView gọi đầu tiên.

```
GET TVC/config
```

### Tham số
Không có.

### Response 200

```json
{
  "supports_search": true,
  "supports_group_request": false,
  "supports_marks": true,
  "supports_timescale_marks": true,
  "supports_time": true,
  "supportedResolutions": ["1", "D"],
  "exchanges": [
    { "value": "",      "name": "Tất cả", "desc": "" },
    { "value": "HNX",   "name": "HNX",    "desc": "HNX" },
    { "value": "UPCOM", "name": "UPCOM",  "desc": "UPCOM" },
    { "value": "HOSE",  "name": "HSX",    "desc": "HOSE" }
  ]
}
```

| Trường | Kiểu | Mô tả |
|---|---|---|
| `supports_search` | boolean | Khai báo hỗ trợ tìm kiếm — ⚠️ nhưng `/search` trả `404`, xem Ghi chú |
| `supports_marks` | boolean | Khai báo hỗ trợ marker — ⚠️ `/marks` trả `404` |
| `supports_timescale_marks` | boolean | Khai báo hỗ trợ marker trục thời gian |
| `supports_time` | boolean | Hỗ trợ `/time` — đúng |
| `supportedResolutions` | string[] | **Chỉ `1` và `D`** |
| `exchanges[]` | object[] | Danh sách sàn cho bộ lọc tìm kiếm |

### Ghi chú
⚠️ `/config` khai báo `supports_search: true` và `supports_marks: true` nhưng hai endpoint `/search` và `/marks` đều trả `404`. Nếu dùng thư viện TradingView, phải override hai capability này về `false` để thư viện không gọi rồi báo lỗi.

### Hiệu năng
830 byte.

---

## `getSymbolInfo`

**Tóm tắt:** Metadata một mã cho thư viện biểu đồ.

```
GET TVC/symbols?symbol={ticker}
```

### Tham số

| Tên | Vị trí | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|---|
| `symbol` | query | string | **bắt buộc** | Ticker cổ phiếu hoặc mã chỉ số |

### Response 200

⚠️ Trả về **object trần**, không có vỏ bọc.

```json
{
  "name": "BID",
  "symbol": "BID",
  "exchange-traded": "HOSE",
  "exchange-listed": "HOSE",
  "timezone": "Asia/Bangkok",
  "minmov": 1,
  "minmov2": 1,
  "pricescale": 10,
  "pointvalue": 1,
  "session": "0900-1500",
  "has_intraday": true,
  "has_no_volume": false,
  "ticker": null,
  "description": "Joint Stock Commercial Bank for Investment and Development of Vietnam",
  "type": "Stock",
  "supported_resolutions": null,
  "intraday_multipliers": ["1"]
}
```

| Trường | Kiểu | Mô tả |
|---|---|---|
| `name` / `symbol` | string | Mã chứng khoán |
| `exchange-traded` / `exchange-listed` | string | Sàn giao dịch / niêm yết |
| `timezone` | string | `Asia/Bangkok` — cùng UTC+7 với Việt Nam |
| `minmov` / `minmov2` | integer | Bước giá tối thiểu |
| `pricescale` | integer | Hệ số chia hiển thị giá |
| `pointvalue` | integer | Giá trị một điểm |
| `session` | string | Khung giờ giao dịch `0900-1500` |
| `has_intraday` | boolean | Có dữ liệu trong phiên |
| `has_no_volume` | boolean | `false` = có khối lượng |
| `description` | string | Tên tổ chức — **bằng tiếng Anh** |
| `type` | string | `Stock` \| `index` |
| `intraday_multipliers` | string[] | `["1"]` — chỉ nến 1 phút |
| `supported_resolutions` | null | Luôn `null`, lấy từ `/config` |

### Ghi chú
`description` trả tên tiếng Anh. Muốn tên tiếng Việt phải lấy từ `getAllQuotes.FullName` hoặc `Master/GetListOrganization.organName`.

### Độ phủ & hiệu năng
51/51 mã mẫu · ~371 byte · ~115 ms.

---

## `getHistoryBars`

**Tóm tắt:** Nến lịch sử OHLCV.

**Mô tả:** Nguồn biểu đồ chính. Hỗ trợ cả cổ phiếu và chỉ số. Giá **đã điều chỉnh hồi tố** (back-adjusted) cho cổ tức và chia tách — xem mục Độ sâu & điều chỉnh giá.

```
GET TVC/history?symbol={ticker}&resolution={res}&from={epoch}&to={epoch}
```

### Tham số

| Tên | Vị trí | Kiểu | Bắt buộc | Giá trị | Mô tả |
|---|---|---|---|---|---|
| `symbol` | query | string | **bắt buộc** | ticker hoặc mã chỉ số | Xem bảng mã chỉ số dưới |
| `resolution` | query | string | **bắt buộc** | `enum`: `D` \| `1` | `D` = nến ngày · `1` = nến 1 phút |
| `from` | query | integer | **bắt buộc** | epoch **giây** | Mốc bắt đầu |
| `to` | query | integer | **bắt buộc** | epoch **giây** | Mốc kết thúc |

⚠️ `from`/`to` tính bằng **giây**, không phải mili giây.

### Response 200

```json
{
  "s": "ok",
  "t": [1756080000, 1756166400],
  "o": [37900.0, 38100.0],
  "h": [39400.0, 38300.0],
  "l": [37900.0, 37900.0],
  "c": [39050.0, 37900.0],
  "v": [8649000.0, 2715100.0]
}
```

| Trường | Kiểu | Đơn vị | Mô tả |
|---|---|---|---|
| `s` | string | — | `ok` hoặc `no_data` |
| `t[]` | integer[] | epoch giây | Mốc thời gian mỗi nến |
| `o[]` `h[]` `l[]` `c[]` | float[] | VND | Mở / cao / thấp / đóng |
| `v[]` | float[] | cổ phiếu | Khối lượng |

Sáu mảng luôn cùng độ dài, khớp theo chỉ số vị trí.

### Mã chỉ số hỗ trợ

| Mã | Chỉ số | Kết quả |
|---|---|---|
| `VNINDEX` | VN-Index | ✅ 13,3 KB |
| `VN30` | VN30 | ✅ 13,2 KB |
| `HNXIndex` | HNX-Index | ✅ 12,1 KB |
| `HNX` / `UPCOM` | — | ❌ `no_data` |

Lưu ý mã chỉ số ở đây (`VNINDEX`, `HNXIndex`) **khác** mã dùng trong `getIndexSnapshots` của BVSC (`HOSE`, `HNX`).

### Ghi chú & bẫy
- ⚠️ **`resolution=1` giới hạn cửa sổ ~30 ngày.** Cửa sổ rộng hơn trả `{"s":"no_data"}`. Trong mọi cửa sổ hợp lệ, dữ liệu trả về là **phiên gần nhất** (~5,8 KB).
- ⚠️ **Không hỗ trợ `5`, `15`, `30`, `60`, `W`, `M`.** Các giá trị này trả `HTTP 200` với **body rỗng 0 byte** — không phải JSON, sẽ làm hỏng parser nếu không kiểm tra độ dài trước. Muốn nến 5/15/30/60 phút phải tự gộp từ nến 1 phút.
- Khối lượng lệch nhẹ so với FiinTrade (BID 07/08: BVSC `8.649.000` vs FiinTrade `8.659.316`) — nhiều khả năng BVSC làm tròn hoặc loại một phần giao dịch. OHLC phiên gần nhất thì khớp chính xác.

### 🔴 Độ sâu bị chặn cứng ở ~239 nến — `from` bị bỏ qua

Yêu cầu cửa sổ 1, 2, 3, 5, 10, 15, 20 năm đều trả **đúng 239 nến, luôn bắt đầu từ 25/08/2025**:

| Cửa sổ yêu cầu | Kết quả |
|---|---|
| 1 năm | 239 nến · 2025-08-25 → 2026-08-10 |
| 5 năm | 239 nến · 2025-08-25 → 2026-08-10 |
| 20 năm | 239 nến · 2025-08-25 → 2026-08-10 |

Tham số `from` **không có tác dụng** với `resolution=D`. Không có tham số phân trang.

→ Muốn lịch sử sâu hơn 1 năm, bắt buộc dùng [`getPriceData`](09-fiin-market-price.md) của FiinTrade (phân trang tới ~12,5 năm).

### Điều chỉnh giá

Giá lịch sử là **giá đã điều chỉnh hồi tố**, nhận biết bằng giá trị thập phân:

| Ngày | tvcharts | FiinTrade `GetPriceData` |
|---|---|---|
| 2025-11-14 | 37910,8925 | 37908,975 |
| 2025-11-13 | 37861,465 | 37859,55 |
| 2025-11-11 | 37564,90 | 37563,00 |

⚠️ Hai nguồn dùng **hệ số điều chỉnh khác nhau**, lệch khoảng 1,9 đ (0,005%). Không trộn hai nguồn trong cùng một chuỗi giá.

Phiên gần nhất thì hai nguồn trùng khớp tuyệt đối, vì tại đó giá điều chỉnh bằng giá thô.

### Độ phủ & hiệu năng
51/51 mã mẫu với `resolution=D`, đều 238–239 nến · ~12,3 KB · ~1,25 s.

---

## `getServerTimeUnix`

**Tóm tắt:** Thời gian máy chủ theo chuẩn UDF.

```
GET TVC/time
```

### Response 200

⚠️ Trả về **số nguyên trần**, không phải JSON.

```
1786333262
```

| Kiểu | Đơn vị |
|---|---|
| integer | epoch **giây** |

Khác với `BVSC/userdata/time` trả JSON và tính bằng **mili giây**.

### Hiệu năng
12 byte.

---

## Endpoint UDF không khả dụng

| Đường dẫn | Kết quả | Ảnh hưởng |
|---|---|---|
| `/search` | `404` | Không dùng được tìm kiếm của TradingView, dù `/config` khai báo có. Phải tự dựng tìm kiếm từ `getAllQuotes` |
| `/marks` | `404` | Không có marker sự kiện trên biểu đồ. Muốn có phải tự vẽ từ [`Calendar/GetCorporate*`](08-fiin-event-calendar.md) |
