# Frankfurter (ECB) — Tỷ giá quốc tế và chỉ số đô Mỹ dựng lại

**Phiên bản:** 1.0 · **Ngày đo:** 2026-08-15 · **Trạng thái:** đã nghiệm thu bằng đối chiếu DXY thật, 248 phiên

> File này giải đúng một bài toán: **có chỉ số đô Mỹ hằng ngày**. FRED có `DTWEXBGS` nhưng công bố theo tuần, trễ 3–9 ngày *(xem [`fred.md`](fred.md) §5.1)* — không dùng được cho phân tích trong ngày. Cách giải: lấy **6 cặp tiền từ Frankfurter** rồi **dựng lại DXY**, sai số trung bình **0,180%** trên 248 phiên. Mọi số dưới đây từ lời gọi thật 2026-08-15.

---

## 1. Nguồn gốc và tình trạng pháp lý

| | |
|---|---|
| Host | `https://api.frankfurter.app` (v1) · `https://api.frankfurter.dev` (v2) |
| Chủ dữ liệu gốc | **Ngân hàng Trung ương châu Âu (ECB)** — tỷ giá tham chiếu hằng ngày |
| Frankfurter là gì | Lớp API mở bọc dữ liệu ECB. **Mã nguồn mở, tự dựng lại được bằng Docker** |
| Xác thực | ❌ Không khoá, không token, không cookie |
| Điều khoản quan sát trực tiếp trên `frankfurter.dev` *(2026-08-15)* | Không hạn mức tháng/ngày; chỉ rate-limit chống lạm dụng |
| Mốc chốt giá | 🔴 **Fixing 14:15 CET** — **không phải giá đóng cửa**. Đây là nguồn gốc của toàn bộ sai lệch, xem §5 Bẫy 2 |

Chuỗi phụ thuộc: **ECB → Frankfurter → dulieuchungkhoan.vn**. Vì Frankfurter mã nguồn mở và tự dựng lại được, rủi ro phụ thuộc tầng giữa thấp hơn hẳn các nguồn khác trong dự án.

---

## 2. Đặc tả API

### 2.1 Endpoint

```
GET https://api.frankfurter.app/latest?from=USD&to=EUR,JPY,GBP,CAD,SEK,CHF
GET https://api.frankfurter.app/{YYYY-MM-DD}?from=USD&to=...
GET https://api.frankfurter.app/{start}..{end}?from=USD&to=...
```

**1 lời gọi lấy đủ 6 cặp.** Một lời gọi nữa lấy trọn chuỗi lịch sử → **backfill 27 năm tốn một lời gọi**.

| | Đo được *(2026-08-15)* |
|---|---|
| Lịch sử | **1999-01-04 →** |
| Khoá API | ❌ không cần |
| Độ trễ | trung vị ~720 ms · chậm nhất 1.366 ms (n=8) |
| Header hạn mức | 🔴 **Không có** `X-RateLimit-*`, không `Retry-After`. ETL tự giữ nhịp |

### 2.2 Cấu trúc response

Dạng khoảng ngày trả về `base`, `start_date`, `end_date` và một bản đồ `rates` khoá theo ngày; dạng một ngày trả `date` thay cho cặp `start_date`/`end_date`. Giá trị là **số đơn vị ngoại tệ trên 1 đơn vị `base`**.

```json
{
  "base": "USD",
  "start_date": "2026-08-01",
  "rates": {
    "2026-08-14": { "CAD": 1.3875, "CHF": 0.81179, "EUR": 0.86453,
                    "GBP": 0.73874, "JPY": 159.01, "SEK": 9.5089 }
  }
}
```

*(Sáu con số trên là số thật ngày 2026-08-14, đã được kiểm chứng độc lập. Danh sách trường ngoài `base` / `date` / `start_date` / `end_date` / `rates`: **chưa kiểm**.)*

⚠️ **`from=USD` cho quote nghịch với quy ước thị trường.** `EUR: 0.86453` nghĩa là **1 USD = 0,86453 EUR**, không phải EUR/USD = 0,86453. Cặp EUR/USD và GBP/USD phải **nghịch đảo** trước khi so với bảng giá thị trường: `EURUSD = 1 / 0,86453 = 1,156698` · `GBPUSD = 1 / 0,73874 = 1,353656` *(2026-08-14)*.

---

## 3. Công thức DXY và cách dựng

### 3.1 Công thức đầy đủ

DXY là **trung bình nhân có trọng số** của 6 cặp, chuẩn ICE:

| Đồng tiền | Trọng số | Cặp theo quy ước thị trường |
|---|---:|---|
| EUR | **57,6%** | EUR/USD |
| JPY | **13,6%** | USD/JPY |
| GBP | **11,9%** | GBP/USD |
| CAD | **9,1%** | USD/CAD |
| SEK | **4,2%** | USD/SEK |
| CHF | **3,6%** | USD/CHF |
| | **100,0%** | |

```
DXY = 50.14348112
      × EURUSD^(-0.576)
      × USDJPY^(+0.136)
      × GBPUSD^(-0.119)
      × USDCAD^(+0.091)
      × USDSEK^(+0.042)
      × USDCHF^(+0.036)
```

Hằng số `50.14348112` chuẩn hoá chỉ số về **100 tại mốc gốc tháng 3/1973**.

🔵 **Dạng rút gọn cho dữ liệu Frankfurter — mọi số mũ đều DƯƠNG.** Vì `from=USD` đã trả sẵn "ngoại tệ trên 1 USD", hai cặp phải nghịch đảo (EUR, GBP) tự triệt tiêu dấu âm của số mũ. Gọi `r[X]` là giá trị Frankfurter trả về:

```
DXY = 50.14348112 × r[EUR]^0.576 × r[JPY]^0.136 × r[GBP]^0.119
                  × r[CAD]^0.091 × r[SEK]^0.042 × r[CHF]^0.036
```

```python
W = {"EUR": 0.576, "JPY": 0.136, "GBP": 0.119,
     "CAD": 0.091, "SEK": 0.042, "CHF": 0.036}

def dxy(r):                      # r = dict rates của Frankfurter, from=USD
    x = 50.14348112
    for k, w in W.items():
        x *= r[k] ** w
    return x
```

⚠️ **Không tự nghịch đảo EUR/GBP rồi vẫn dùng số mũ âm cùng lúc** — đây là chỗ dễ nhân đôi phép nghịch đảo nhất. Chọn **một** trong hai dạng.

### 3.2 Ví dụ nghiệm — dựng lại ngày 2026-08-14

| Đồng | `r[X]` (Frankfurter, `from=USD`) | Trọng số |
|---|---|---:|
| EUR | 0,86453 | 0,576 |
| JPY | 159,01 | 0,136 |
| GBP | 0,73874 | 0,119 |
| CAD | 1,3875 | 0,091 |
| SEK | 9,5089 | 0,042 |
| CHF | 0,81179 | 0,036 |

→ **DXY dựng lại = 99,6113**

---

## 4. 🔵 Nghiệm thu — đối chiếu DXY thật

Chuẩn độc lập: `DX-Y.NYB` trên Yahoo, chính là **chỉ số ICE** (`fullExchangeName: "ICE Futures"`, lịch sử từ 1971) — xem [`yahoo.md`](yahoo.md).

**Một ngày (2026-08-14):**

| Nguồn 6 cặp | DXY dựng lại | DXY ICE thật | Sai lệch |
|---|---|---|---|
| **Frankfurter / ECB** | **99,6113** | **99,67** | **−0,059%** |
| open.er-api.com | 99,6471 | 99,67 | −0,023% |
| Yahoo 6 cặp | 99,6151 | 99,67 | −0,055% |
| currency-api (jsDelivr) | 99,9075 | 99,67 | **+0,238%** ⚠️ |

**Một năm (2025-08-15 → 2026-08-14):**

| Cách dựng | Mốc chốt | n | Lệch TB có dấu | **\|Lệch\| TB** | p90 | max | sd |
|---|---|---:|---:|---:|---:|---:|---:|
| **A. Frankfurter / ECB** | 14:15 CET | **248** | **+0,013%** | **0,180%** | 0,377% | 0,975% | 0,241% |
| B. FRED `DEX*` | noon ET | 27 | +0,062% | 0,158% | 0,213% | 1,500% | 0,325% |
| C. Yahoo 6 cặp | ~17:00 ET | 251 | −0,008% | 0,260% | 0,548% | 0,978% | 0,330% |

Phương án A: tương quan mức **0,9787** · tương quan biến động ngày **0,489** · trùng dấu tăng/giảm **62%**. **Lệch TB có dấu +0,013% ⇒ không thiên lệch một chiều**, nên **không hiệu chỉnh được bằng hằng số cộng hay nhân**.

⚠️ **Kết quả nghịch trực giác — đọc kỹ trước khi định "sửa" bằng cách đổi sang Yahoo.** Yahoo lấy giá **đóng cửa**, đúng mốc của ICE, mà lại **kém hơn** ECB fixing (0,260% vs 0,180%). Nguyên nhân đo được: **6 cặp của Yahoo không đồng bộ mốc thời gian**. Cùng phiên 2026-08-14, `EURUSD=X` và `GBPUSD=X` có `regularMarketTime` = 2026-08-14 21:29 UTC, còn `JPY=X` / `CAD=X` / `SEK=X` / `CHF=X` = 2026-08-15 04:21 UTC. **Đúng mốc mà lệch giờ giữa các cặp thì tệ hơn sai mốc mà đồng bộ.**

Phương án B chỉ có **n=27** vì `DEX*` của FRED công bố theo tuần — không đủ mẫu để so, và bản thân nó là chỗ hụt mà file này đang lấp.

---

## 5. Năm bẫy

**Bẫy 1 — 🔴 `currency-api` (jsDelivr) lệch nhãn ngày một phiên.** File nhãn `2026-08-14` thực chất mang số phiên **08-13**. Rẻ và phủ rộng (696 mã) nhưng **không tin được nhãn ngày**. Đây là lý do nó lệch +0,238% ở bảng §4 — không phải vì số sai, mà vì **so nhầm ngày**.

**Bẫy 2 — 🔴 ECB fixing ≠ giá đóng cửa. Đây là toàn bộ nguồn gốc sai lệch 0,18%.** Fixing chốt **14:15 CET = 08:15 ET**; DXY ICE chốt **17:00 ET** — cách nhau **8 giờ 45 phút giao dịch**. Sai lệch **không có dấu cố định**, **không hiệu chỉnh được bằng hằng số**. → Số dựng lại là **ảnh chụp lúc 14:15 CET**, phải ghi đúng như vậy ở mọi chỗ hiển thị.

**Bẫy 3 — ⚠️ Lịch nghỉ hai bên không trùng.** Trong 1 năm *(đo 2026-08-15)*: **3 ngày ICE có mà ECB không** · **7 ngày ECB có mà ICE không**. Chuỗi dựng lại **không khớp 1-1** với chuỗi DXY thật. Join phải theo **ngày thật**, không theo vị trí dòng; và job giám sát sai lệch phải chịu được ngày khuyết ở một trong hai phía.

**Bẫy 4 — ⚠️ Frankfurter nới ngày bắt đầu ra trước.** Xin khoảng `2026-08-01..2026-08-14` thì response trả `start_date` = **2026-07-31**. Đừng giả định `start_date` bằng tham số đã gửi; luôn đọc lại từ response và cắt ở tầng ứng dụng nếu cần biên chính xác.

**Bẫy 5 — 🔴 Frankfurter v2 mặc định TRỘN 84 ngân hàng trung ương.** `api.frankfurter.dev` trả cả ngày **thứ Bảy** và tươi hơn v1 — nhưng khi đó nó **không còn là tỷ giá tham chiếu chính thức của tổ chức nào**, và số dựng lại mất tính tái lập. **Bắt buộc truyền `providers=ECB`.** Đã kiểm 2026-08-15: v2 + `providers=ECB` trả **đúng từng con số** của v1.

---

## 6. Giới hạn phải ghi ở mọi nơi hiển thị

🔴 **DXY dựng lại KHÔNG hiển thị được cạnh một giá đóng cửa thật.** Nó là ảnh chụp 14:15 CET, sai số **0,18% trung bình / 0,98% tối đa** so với DXY ICE. Đủ cho phân tích vĩ mô và cho câu hỏi "đô đang mạnh hay yếu"; **không đủ** để đặt cạnh bảng giá đóng cửa, vì người đọc sẽ kết luận một trong hai số bị sai.

Ba hệ quả vận hành:

1. Cột giá trị phải mang cờ **là số dựng lại**, kèm mốc **14:15 CET**.
2. Muốn con số DXY **thật**, lấy `DX-Y.NYB` — xem [`yahoo.md`](yahoo.md). Chuỗi dựng lại vẫn giữ, vì nó không phụ thuộc một API nội bộ không cam kết.
3. Chạy **job giám sát sai lệch** hằng ngày: nếu \|lệch\| vượt **0,98%** (max đã đo trên 248 phiên) thì báo động — hoặc nguồn đổi hành vi, hoặc công thức bị áp sai chiều nghịch đảo (§3.1).

---

## 7. Nguồn dự phòng

| Nguồn | Vai | Nhược điểm đo được *(2026-08-15)* |
|---|---|---|
| **Yahoo `v8/finance/chart`** | Dự phòng chính. 6 cặp + `DX-Y.NYB` (DXY ICE thật). Chi tiết ở [`yahoo.md`](yahoo.md) | **6 lời gọi** cho 6 cặp; 6 cặp **không đồng bộ mốc thời gian** (§4); là API nội bộ không cam kết |
| `open.er-api.com` | Dự phòng phụ | 🔴 Endpoint mở **không có lịch sử**. Chỉ dùng được cho điểm hôm nay |
| ECB SDMX gốc | Đường vòng khi Frankfurter chết | Trả pivot theo EUR, phải tự đổi gốc sang USD |
| FRED `DEX*` | Đối chứng, không phải nguồn chính | Công bố theo tuần — chính là chỗ hụt cần lấp |

**Đã thử và loại:** `currency-api` (Bẫy 1) · exchangerate.host, marketstack, finnhub, tiingo (đều đòi đăng ký — `missing_access_key` / `401` / `403`) · Alpha Vantage và Twelve Data (khoá `demo` chạy được, dùng thật phải đăng ký).

---

## 8. Ngân sách request

| Mục | Lời gọi/ngày |
|---|---:|
| 6 cặp tiền dựng DXY (Frankfurter, 1 lời gọi) | 1 |
| Đối chứng tỷ giá (nguồn thứ hai) | 1 |
| DXY thật để giám sát sai lệch (`DX-Y.NYB`) | 1 |
| **Tổng thường nhật** | **3** |
| **Backfill 1999 → nay** | **1 lời gọi** |

Không mục nào cần khoá API.

---

## 9. Việc chưa kiểm

- **Ngưỡng rate limit thật** của Frankfurter — **chủ đích không dò**.
- Điều khoản đầy đủ của Frankfurter và ECB *(mới quan sát trang `frankfurter.dev`, chưa đọc toàn văn)*.
- Danh sách trường đầy đủ của response ngoài `base` / `date` / `start_date` / `end_date` / `rates`.
- ETag / `If-None-Match` / cache header.
- Hành vi khi gọi nhiều luồng song song.
- Trọng số DXY có bị ICE điều chỉnh trong lịch sử không — bộ trọng số dùng ở §3.1 đã **nghiệm đúng trên 248 phiên gần nhất**, chưa kiểm cho giai đoạn trước 2025.
- `open.er-api.com` có endpoint lịch sử trả phí hay không.
