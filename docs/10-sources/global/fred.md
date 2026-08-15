# FRED — Vĩ mô Mỹ: lãi suất, lạm phát, đồng đô, dầu

**Phiên bản:** 1.0 · **Ngày đo:** 2026-08-15 · **Trạng thái:** 53 lời gọi thật, 15 series đã đo từng cái

> FRED lấp **mắt xích Mỹ** — lãi suất chính sách, kỳ vọng lãi suất, lạm phát Mỹ, sức mạnh đồng đô, dầu giao ngay. Nó **không thay** [`macro/wichart.md`](../macro/wichart.md): mảng Việt Nam của FRED thua WiChart ở mọi chiều đo được (§7). Mọi số dưới đây đến từ lời gọi thật ngày 2026-08-15; cái chưa gọi ghi **chưa kiểm** (§9).

---

## 1. Nguồn gốc và tình trạng pháp lý

| | |
|---|---|
| Host API | `https://api.stlouisfed.org/fred/` |
| Host web/tài liệu | `https://fred.stlouisfed.org` — ⚠️ **chập chờn từ mạng Việt Nam**, xem Bẫy 8 |
| Chủ dữ liệu | **Federal Reserve Bank of St. Louis** (tổng hợp lại từ Fed Board, BLS, BEA, EIA, CBOE) |
| Xác thực | Khoá API, truyền bằng **query param** |
| Tình trạng pháp lý | ✅ **Chủ dự án đã làm việc với FRED và được đồng ý (2026-08-15).** |

Chuỗi phụ thuộc: **cơ quan gốc (Fed Board / BLS / BEA / EIA) → FRED → Finext**. FRED là tầng tổng hợp, không phải nơi sinh số — nên lịch công bố và bản vá đều theo nhịp của cơ quan gốc (§4, §5).

---

## 2. Đặc tả API

### 2.1 Endpoint và xác thực

```
GET https://api.stlouisfed.org/fred/{path}?api_key=***&file_type=json&...
```

Không có header auth. Khoá đi trong URL → xem Bẫy 7.

Nhóm endpoint **đã gọi thật** *(2026-08-15)*: `series` (16 lời gọi) · `series/observations` (27) · `series/search` (3) · `series/tags` (4) · `series/release` (1) · `series/vintagedates` (1) · `release/dates` (1) · `tags` (2).
**Chưa kiểm:** `category/*`, `releases`, `sources/*`, `maps/*`.

### 2.2 Tham số chung

| Tham số | Đo được *(2026-08-15)* |
|---|---|
| `api_key` | Bắt buộc, query param |
| `file_type` | 🔴 **Mặc định là `xml`, KHÔNG phải `json`.** Bỏ tham số → `Content-Type: text/xml` kèm `HTTP 200`. Phải truyền `file_type=json` ở **mọi** lời gọi |
| `limit` | Mặc định của `series/observations` = **100000**. Chuỗi dài nhất đo được (`DGS10`, 16.858 điểm) vẫn lọt một lời gọi — **không cần phân trang** |
| `offset` | Có, mặc định `0` |
| `sort_order` | `asc` \| `desc`. `desc` + `limit=n` = cách rẻ nhất lấy n điểm mới nhất |
| `observation_start` / `_end` | Mặc định `1600-01-01` / `9999-12-31` |
| `realtime_start` / `_end` | Trục vintage — xem §4. ⚠️ Mặc định **không phải hôm nay**, xem Bẫy 5 |
| `frequency` + `aggregation_method` | Gộp phía server. ⚠️ Đổi ý nghĩa của `count` và sinh `"."` — xem Bẫy 4 |
| `units` | §3 |
| `output_type` | `1` mặc định; `4` = bản công bố lần đầu (§4.2). `2`, `3`: **chưa kiểm** |

### 2.3 Cấu trúc response — `series/observations`

```json
{
  "realtime_start": "2026-08-14", "realtime_end": "2026-08-14",
  "observation_start": "1600-01-01", "observation_end": "9999-12-31",
  "units": "lin", "output_type": 1, "file_type": "json",
  "order_by": "observation_date", "sort_order": "desc",
  "count": 26342, "offset": 0, "limit": 5,
  "observations": [
    { "realtime_start": "2026-08-14", "realtime_end": "2026-08-14",
      "date": "2026-08-13", "value": "3.6300000000" }
  ]
}
```

| Trường | Kiểu | Ý nghĩa đo được |
|---|---|---|
| `count` | int | **Tổng số quan sát của toàn chuỗi**, không phải số dòng trả về. `DGS10` báo `count=16858` ngay cả khi `limit=4` |
| `date` | `YYYY-MM-DD` | Chuỗi tháng neo **ngày 1**; chuỗi tuần (`WALCL`) neo **thứ Tư** |
| `value` | **string** | ⚠️ Luôn là chuỗi. Giá trị thiếu = `"."` — Bẫy 1. Độ chính xác không đồng nhất — Bẫy 2 |
| `realtime_start`/`_end` **mức dòng** | date | Khoảng thời gian **bản số này còn hiệu lực** — §4 |
| `realtime_start`/`_end` **mức gốc** | date | ⚠️ Là **vintage hiện hành của chính series đó**, không phải hôm nay — Bẫy 5 |

Response `series` (metadata) có: `observation_start` · `observation_end` · `frequency` + `frequency_short` · `units` + `units_short` · `seasonal_adjustment_short` · `last_updated` *(kèm offset giờ St. Louis, đổi theo DST — Bẫy 6)* · `popularity` · `notes`.

### 2.4 Lỗi

`HTTP 400` + thân JSON. Hai mẫu bắt được thật *(2026-08-15)*:

```json
{"error_code":400,"error_message":"Bad Request.  Invalid value for variable series_id.  Series IDs should be 25 or less alphanumeric characters."}
{"error_code":400,"error_message":"Bad Request.  No vintage dates exist for the specified real-time period: 2026-08-15 to 2026-08-15."}
```

🔵 **Khác hẳn BVSC / FiinTrade / WiChart:** FRED **không** trả `200` kèm dữ liệu rỗng khi tham số sai. Mã lỗi dùng trực tiếp được, không cần đoán từ body.

### 2.5 Hiệu năng và kích thước

| | Đo 2026-08-15 (51 lời gọi `200`) |
|---|---|
| Độ trễ | **trung vị 426 ms** · min 370 · p90 809 · max 4.723 |
| Hai lời gọi chậm nhất | `tags?search_text=copyright` 4.723 ms · `tags?tag_group_id=cc` 2.835 ms — nhóm `tags` chậm hơn hẳn nhóm `series` |
| `series/observations` điển hình (`limit=4`) | 390–460 ms · **650–710 byte** |
| Kéo toàn bộ `DGS10` (16.858 điểm, 1962 → nay) | **733 ms · 1.601.211 byte thô · 85.110 byte trên dây** (gzip −94,7%) |
| gzip | Có, 51/53 lời gọi (2 lời gọi `400` không nén) |
| **Header hạn mức** | 🔴 **Không có.** Hợp nhất header 53 response: không `X-RateLimit-*`, không `Retry-After` |
| ETag / `If-None-Match` | **Chưa kiểm** |

**Hệ quả:** cả lịch sử 64 năm của một chuỗi ngày tốn 85 KB nén và **một** lời gọi. Backfill không phải bài toán ở nguồn này.

### 2.6 Rate limit

- **Đo được:** 53 lời gọi tuần tự trong ~1 phút → `200` toàn bộ. Không `429`, không `Retry-After`.
- **Con số công bố chính thức: chưa kiểm.** Trang tài liệu không đọc được ổn định từ mạng đo (Bẫy 8). Một nguồn thứ ba nêu 120 request/phút — **không dùng làm cam kết**.
- **Chủ đích không dò ngưỡng chặn.** ETL tự giữ nhịp, giống WiChart/FiinTrade.

---

## 3. Biến thể `units`

| `units` | Đo được *(2026-08-15)* |
|---|---|
| `lin` (mặc định) | `CPIAUCSL` 2026-07 = **332,813** (chỉ số 1982–84 = 100) |
| `pc1` | `CPIAUCSL` 2026-07 = **3,30386** → **phần trăm YoY dạng phần trăm đầy đủ**, 5 chữ số thập phân |

> 🔴 **Ngược quy ước với WiChart.** WiChart lưu series tăng trưởng **dạng phân số làm tròn 2 chữ số** *(xem [`macro/wichart.md`](../macro/wichart.md) Bẫy 5)*; FRED `pc1` trả **phần trăm đầy đủ**. **Không dùng chung một hàm chuẩn hoá cho hai nguồn.**

`chg` · `ch1` · `pch` · `pca` · `cch` · `cca` · `log`: **chưa kiểm**.

**Quy tắc:** ETL **lưu `lin`**, tự tính tăng trưởng ở tầng phân tích. `pc1` là số phái sinh — lưu nó thì mất khả năng tính lại khi số gốc bị vá hồi tố (§4).

---

## 4. 🔴 Vá hồi tố — FRED không phải kho append-only

### 4.1 Bằng chứng: `PAYEMS` tháng 5/2026

`series/observations?series_id=PAYEMS&realtime_start=1990-01-01&realtime_end=9999-12-31&observation_start=2026-05-01&observation_end=2026-05-01` *(đo 2026-08-15)*:

| Bản (vintage) hiệu lực từ | đến | Giá trị (nghìn người) |
|---|---|---|
| 2026-06-05 | 2026-07-01 | **159.001** |
| 2026-07-02 | 2026-08-06 | **158.927** (−74) |
| 2026-08-07 | 9999-12-31 | **158.861** (−66) |

→ **Một điểm dữ liệu có 3 giá trị.** Lệch tích luỹ 140 nghìn việc làm. Kho lưu bản đầu rồi không cập nhật → biểu đồ Finext **vĩnh viễn khác** biểu đồ FRED, và không có cách nào phát hiện bằng timestamp.

### 4.2 Ba chế độ đọc — đều đã gọi thật

| Cách gọi | Trả về | Dùng khi |
|---|---|---|
| Mặc định (không `realtime_*`) | **Bản hiện hành**, 1 giá trị / ngày | ETL thường nhật — **cái nên lưu** |
| `realtime_start=1990-01-01&realtime_end=9999-12-31` | **Toàn bộ vintage**, mỗi bản một dòng | Bảng lịch sử sửa đổi |
| `output_type=4` + `realtime_*` mở rộng | **Chỉ bản công bố lần đầu** | Backtest không nhìn trộm tương lai |

`output_type=4` cho `PAYEMS` 2026-01→07, bản đầu: 158.627 · 158.466 · 158.637 · 158.736 · **159.001** · 158.984 · 158.858. So bản hiện hành, **bản đầu luôn cao hơn** trong loạt này.

> ⚠️ `output_type=4` mà **không** truyền `realtime_start` / `realtime_end` mở rộng → `400 "No vintage dates exist for the specified real-time period"`. Phải truyền cả hai.

### 4.3 Lịch công bố lấy được bằng API

| Lời gọi | Kết quả *(2026-08-15)* |
|---|---|
| `series/vintagedates?series_id=PAYEMS` | **858 ngày vintage**; 8 bản gần nhất: 2026-08-07 · 07-02 · 06-05 · 05-08 · 04-03 · 03-06 · 02-11 · 01-09 |
| `series/release?series_id=PAYEMS` | release **id 50 "Employment Situation"** (`press_release: true`) |
| `release/dates?release_id=50` | **862 ngày công bố**; 6 ngày gần nhất **trùng khớp 100%** với danh sách vintage |

🔵 **Thứ WiChart không có:** ETL **đặt lịch gọi đúng ngày ra số** thay vì poll mù.

### 4.4 Bốn quy tắc bắt buộc cho kho dữ liệu

1. 🔴 **UPSERT theo khoá `(series_id, date)` — không INSERT-only.**
2. 🔴 **Mỗi lần chạy làm mới cửa sổ 24 tháng gần nhất** cho series tháng/quý. `date` bất biến, **giá trị thì không**.
3. Ghi `last_updated` của metadata làm cột kiểm soát — chỉ kéo lại khi nó đổi.
4. Cần backtest nghiêm túc → bảng phụ chứa vintage, dùng `output_type=4`. **Chưa cần ở giai đoạn này.**

---

## 5. Bảng 15 series đã đo

Đo 2026-08-15. **Trễ** = số ngày lịch từ `observation_end` tới ngày đo — cùng quy ước [`macro/wichart.md`](../macro/wichart.md) §5. ⚠️ Đọc cột này kèm §5.1, vì nó trộn ba thứ khác nhau.

| series_id | Chỉ tiêu | Tần suất | Lịch sử | Trễ | Đơn vị | Số điểm | Giá trị mới nhất | Mắt xích trong phân tích |
|---|---|---|---|---|---|---|---|---|
| `DFF` | Fed funds hiệu lực | d (7 ngày/tuần) | 1954-07-01 → | 2d | % | 26.342 | 3,63 (08-13) | **Ý chí chính sách Mỹ** — đầu chuỗi nhân quả |
| `FEDFUNDS` | Fed funds bình quân tháng | m | 1954-07-01 → | 45d | % | 865 | 3,63 (07/2026) | Bản tháng, dùng so chuỗi dài |
| `SOFR` | Repo có bảo đảm qua đêm | d | 2018-04-03 → | 2d | % | 2.183 | 3,62 (08-13) | Căng thẳng thanh khoản đô |
| `DGS2` | Lợi suất TPCP Mỹ 2 năm | d | 1976-06-01 → | 2d | % | 13.098 | 4,15 (08-13) | **Kỳ vọng lãi suất** |
| `DGS10` | Lợi suất TPCP Mỹ 10 năm | d | 1962-01-02 → | 2d | % | 16.858 | 4,63 (08-13) | Mặt bằng chi phí vốn toàn cầu |
| `T10Y2Y` | Chênh 10y − 2y | d | 1976-06-01 → | **1d** | % | 13.099 | 0,51 (08-14) | Vị trí chu kỳ |
| `T10YIE` | Breakeven lạm phát 10 năm | d | 2003-01-02 → | **1d** | % | 6.162 | 2,27 (08-14) | **Kỳ vọng lạm phát realtime** |
| `DTWEXBGS` | Chỉ số đô Mỹ (broad, danh nghĩa) | d | 2006-01-02 → | 🔴 **8d** | Index 2006-01=100 | 5.375 | 119,065 (08-07) | **Đồng đô** — mắt xích 2 của chuỗi Fed → tỷ giá |
| `DEXCHUS` | CNY/USD | d | 1981-01-02 → | 🔴 **8d** | CNY / 1 USD | 11.896 | 6,7474 (08-07) | Neo khu vực cho VND |
| `CPIAUCSL` | CPI Mỹ (đã hiệu chỉnh mùa vụ) | m | 1947-01-01 → | 45d | Index 1982-84=100 | 955 | 332,813 · YoY **3,30%** | Lạm phát Mỹ |
| `PCEPILFE` | Core PCE | m | 1959-01-01 → | 🔴 **75d** | Index 2017=100 | 810 | 130,266 (06/2026) | Thước Fed thật sự nhìn |
| `UNRATE` | Thất nghiệp Mỹ | m | 1948-01-01 → | 45d | % | 943 | 4,1 (07/2026) | Sức ép hạ lãi suất |
| `PAYEMS` | Bảng lương phi nông nghiệp | m | 1939-01-01 → | 45d | nghìn người | 1.051 | 158.858 (07/2026) | Số làm thị trường biến động mạnh nhất. 🔴 **Bị vá hồi tố** — §4 |
| `VIXCLS` | VIX | d | 1990-01-02 → | 2d | Index | 9.553 | 14,63 (08-13) | Khẩu vị rủi ro toàn cầu |
| `DCOILWTICO` | Dầu WTI **giao ngay** | d | 1986-01-02 → | 4d | USD/thùng | 10.594 | 84,77 (08-11) | **Kênh dầu → lạm phát** |

> 🔴 **`DCOILWTICO` là giá GIAO NGAY.** WiChart `dau_wti` là giá **tương lai**. Chênh ~2% giữa hai nguồn là **chênh lệch cơ sở, không phải sai số** — xem [`market/00-conventions.md`](../market/00-conventions.md) và [`macro/wichart.md`](../macro/wichart.md). Đừng lấy cái này để "sửa" cái kia.

### 5.1 🔴 Đọc cột "Trễ" cho đúng — ba nhóm khác hẳn nhau

Ngày đo 2026-08-15 là **thứ Bảy**, nên con số trễ trộn hiệu ứng cuối tuần với độ trễ thật. Đo đuôi từng chuỗi để tách bạch:

| Nhóm | Bằng chứng (đuôi chuỗi thật, đo 2026-08-15) | Nghĩa thật |
|---|---|---|
| **Chuỗi ngày, T+1, đã có số thứ Sáu** | `T10Y2Y`: 08-14 · 08-13 · 08-12 · 08-11 · 08-10 | ✅ **Không trễ.** "Trễ 1 ngày" chỉ là hiệu ứng cuối tuần |
| **Chuỗi ngày, T+1, số thứ Sáu lên muộn** | `DGS10`: 08-13 · 08-12 · 08-11 · 08-10 · 08-07 | ✅ Bản chất vẫn T+1 |
| 🔴 **Chuỗi ngày nhưng CÔNG BỐ THEO TUẦN** | `DTWEXBGS`: 08-07 · 08-06 · 08-05 · 08-04 · 08-03 · 07-31 — **trống trọn tuần 08-10 → 08-14** | 🔴 **Hạn chế thật duy nhất** |

🔴 **Chỉ số đô Mỹ trễ 3–9 ngày, không phải 8 ngày cố định.** `DTWEXBGS` và `DEXCHUS` thuộc bản công bố **H.10 của Fed, ra mỗi thứ Hai**, mang dữ liệu tới hết thứ Sáu tuần trước (`last_updated` 2026-08-10 15:16 → `observation_end` 2026-08-07). Nên độ trễ **dao động từ 3 ngày (sáng thứ Ba) tới 9 ngày (Chủ nhật)**; con số 8 chỉ là lát cắt tại thời điểm đo.

➜ **Nói gọn:** lãi suất, VIX, dầu, chỉ số — tươi T+1, dùng được cho phân tích hằng ngày. **Chỉ số đô Mỹ là chỗ hụt**, vì Fed chỉ ra số mỗi tuần một lần. Cần "đô mạnh hay yếu hôm nay" thì phải dựng DXY từ tỷ giá — xem [`fx.md`](fx.md).

Ghi chú thêm:
- `T10Y2Y`, `T10YIE` cập nhật ~16:03 giờ St. Louis.
- 🔴 `PCEPILFE` trễ 75 ngày — chậm nhất danh sách, chỉ dùng làm **bối cảnh**, không để hành động.
- Nhóm tháng (`CPIAUCSL`, `UNRATE`, `PAYEMS`) trễ 45 ngày theo quy ước neo đầu tháng — thực chất **12–15 ngày sau khi kỳ tham chiếu kết thúc**, tương đương WiChart (42d).
- ⚠️ Quan sát chưa giải thích: `T10Y2Y` = `DGS10` − `DGS2` nhưng **có** điểm 08-14 trong khi `DGS10` chưa có. Chuỗi phái sinh đi trước chuỗi thành phần. **Chưa kiểm** nguyên nhân.

---

## 6. Tám bẫy triển khai

**Bẫy 1 — 🔴 Giá trị thiếu là chuỗi `"."`, không phải `null`.** Đo `DGS10` cửa sổ 2026-06-29 → 07-10:

```json
{"date": "2026-07-02", "value": "4.49"},
{"date": "2026-07-03", "value": "."},     ← nghỉ lễ Quốc khánh Mỹ
{"date": "2026-07-06", "value": "4.48"}
```

Toàn chuỗi `DGS10` (16.858 điểm): **719 điểm `"."` = 4,3%**. Cuối tuần **không** sinh dòng; chỉ ngày nghỉ lễ giữa tuần sinh `"."`. → `float(value)` ném `ValueError` ở 4,3% số dòng.

```python
v = None if value == "." else float(value)
```

**Bẫy 2 — ⚠️ `value` luôn là string, độ chính xác không đồng nhất trong cùng một lời gọi.** `FEDFUNDS` trả `"3.6300000000"` cho tháng 7 nhưng `"3.63"` cho tháng 6 — **cùng một response**. Đừng suy đơn vị hay độ chính xác từ số chữ số thập phân.

**Bẫy 3 — 🔴 `file_type` mặc định là `xml`.** Quên `file_type=json` → nhận XML mà vẫn `HTTP 200`. Parser JSON hỏng ở nơi không ai ngờ.

**Bẫy 4 — ⚠️ `frequency=m` gộp phía server: `count` sai và kỳ dở dang trả `"."`.** Gọi `DGS10&frequency=m&aggregation_method=avg&limit=4&sort_order=desc`:

```json
"count": 16858,                          ← vẫn là số điểm NGÀY, không phải số tháng
"observations": [
  {"date": "2026-08-01", "value": "."},  ← tháng 8 chưa xong → "."
  {"date": "2026-07-01", "value": "4.60"}
]
```

→ (a) **không dùng `count` để phân trang khi có `frequency`**; (b) **kỳ hiện tại luôn `"."`** khi gộp — đừng đọc thành "dữ liệu thiếu".

**Bẫy 5 — ⚠️ `realtime_start` ở mức gốc không phải hôm nay.** Khi không truyền, API echo về **vintage hiện hành của chính series đó**. Cùng phiên 2026-08-15: `DGS10` → `2026-08-15` · `DFF` → `2026-08-14` · `CPIAUCSL` → `2026-08-12` · `PCEPILFE` → `2026-07-30`. Đừng dùng trường này làm dấu thời gian của lần chạy ETL.

**Bẫy 6 — ⚠️ `last_updated` có offset múi giờ đổi theo DST.** Đo được `"2026-08-14 15:17:23-05"` (hè) và `"2026-02-04 11:43:37-06"` (đông) — giờ St. Louis. **Không hardcode offset.**

**Bẫy 7 — 🔴 Khoá API nằm trong URL.** Không có header auth. Mọi access log, cache key, chuỗi trace, ảnh chụp màn hình debug đều dính khoá nếu không che. **Che `api_key` ở mọi chỗ ghi log** — quy tắc bắt buộc, không phải khuyến nghị.

**Bẫy 8 — ⚠️ Host web `fred.stlouisfed.org` chập chờn từ mạng Việt Nam, host API thì thông.** Đo 2026-08-15: `api.stlouisfed.org` trả `200` trong 440 ms; cùng lúc `fred.stlouisfed.org` thất bại **3/3 lần** (`HttpRequestException` sau 19,4 s, rồi timeout 45 s × 2). Đường tắt `fredgraph.csv?id=...` (lấy CSV **không cần khoá**) nằm trên host web này ⇒ **chỉ là tiện ích bổ sung, không phải đường thay thế.** ETL giữ đường API có khoá làm chính.

> Ghi chú về `fredgraph.csv` khi dùng làm đường phụ *(đo 2026-08-15)*: nhiều series một lời gọi bằng `?id=A,B,C`; khoảng ngày `cosd`/`coed` **chỉ đúng khi truyền một `id`**; giá trị thiếu là chuỗi **rỗng** `,,` chứ không phải `"."`; ghép nhiều series **khác tần suất** thì trả về **file ZIP**. Và ⚠️ `DTWEXBGS` qua CSV **vẫn dừng 2026-08-07** — bỏ khoá API **không** làm chỉ số đô tươi lên.

---

## 7. Ranh giới — cái FRED KHÔNG lấp

### 7.1 Mảng Việt Nam: WiChart thắng tuyệt đối

| Phép đo *(2026-08-15)* | Kết quả |
|---|---|
| `series/search?search_text=Vietnam` | 378 series |
| `...&filter_variable=frequency&filter_value=Daily` | 🔴 **`count = 0` — không một series ngày nào** |
| `...&filter_value=Monthly` | 50 series, **phần lớn là nhiễu**: `LNU*` thực chất là *"Veterans, Vietnam-Era"* — dữ liệu **cựu binh Mỹ** |

Series Việt Nam thật, top theo `popularity`:

| series_id | Chỉ tiêu | Tần suất | Phủ | Cập nhật cuối |
|---|---|---|---|---|
| `IMP5520` | Mỹ nhập khẩu từ Việt Nam | **m** | 1992-01 → 2026-06 | 2026-08-04 |
| `EXP5520` | Mỹ xuất khẩu sang Việt Nam | **m** | 1992-01 → 2026-06 | 2026-08-04 |
| `FPCPITOTLZGVNM` | Lạm phát CPI (World Bank) | y | 1996 → 2025 | 2026-06-30 |
| `MKTGDPVNA646NWDB` | GDP (World Bank) | y | 1985 → 2025 | 2026-06-30 |
| `VNMPCPIPCPPPT` | CPI %Δ (IMF WEO, **dự báo tới 2031**) | y | 1990 → 2031 | 2026-04-22 |
| `VNMNGDPRPCPPPT` | GDP thực %Δ (IMF WEO, dự báo) | y | 1990 → 2031 | 2026-04-22 |
| `FXRATEVNA618NUPN` | Tỷ giá VND/USD | y | 1970 → **2010** | 🔴 **2012-09-17 — chết 14 năm** |
| `DDOE02VNA086NWDB` | CPI Việt Nam (chỉ số) | y | 1994 → **2017** | 🔴 **2022 — chết** |
| `DDDM01VNA156NWDB` | Vốn hoá TTCK / GDP | y | 2008 → **2020** | 🔴 **2024 — chết** |
| `WUIVNM` | World Uncertainty Index | q | 1956 → 2026-04 | 2026-07-31 |

🔴 **Không lấy mảng Việt Nam từ FRED.** Tỷ giá dừng 2010 (WiChart: ngày, trễ 0d). CPI là **số năm** (WiChart: tháng từ 2003). Không có lãi suất, cung tiền, tín dụng VN ở tần suất dùng được.

Đúng **hai thứ** FRED có mà WiChart không: `IMP5520` / `EXP5520` — thương mại song phương Mỹ–Việt **theo tháng, phía Mỹ báo cáo** (dùng cho câu chuyện thuế quan / xuất khẩu); và dự báo IMF WEO tới 2031. Cả hai là gia vị, không phải xương sống.

### 7.2 Chỉ số chứng khoán quốc tế: không lấy từ FRED

Đo 2026-08-15, 7 lời gọi bổ sung:

| series | Lịch sử | Trễ |
|---|---|---|
| `SP500` | **2016-08-15** → 2026-08-14 | 1d |
| `DJIA` | **2016-08-15** → 2026-08-14 | 1d |
| `NASDAQCOM` | 1971-02-05 → 2026-08-14 | 1d |
| `NIKKEI225` | 1949-05-16 → 2026-08-14 | 1d |

🔴 **`SP500` và `DJIA` là cửa sổ trượt 10 năm** — bắt đầu **đúng ngày 2016-08-15**, tức chính xác 10 năm trước ngày đo (cùng cơ chế `WIN2Y` của WiChart). `NASDAQCOM` (55 năm) và `NIKKEI225` (77 năm) thì đầy đủ — **không được nói chung "các series này chỉ giữ 10 năm"**.

➜ Chỉ số quốc tế đi đường khác, xem [`yahoo.md`](yahoo.md). FRED dành cho **lãi suất / lạm phát / đô Mỹ / dầu**.

### 7.3 Chồng lấn với WiChart ở mảng dầu

WiChart có 6 key năng lượng (SunSirs, giá CNY) với **cửa sổ trượt 2 năm** — ngày không chạy ETL là ngày mất vĩnh viễn. FRED `DCOILWTICO` cho **1986 → nay, 10.594 điểm, một lời gọi**, nguồn EIA.

→ Với **dầu WTI giao ngay**, FRED tốt hơn hẳn: lịch sử đầy đủ, không cửa sổ trượt, không rủi ro mất đuôi. Giữ WiChart cho **hàng hoá Trung Quốc** (SunSirs) mà FRED không có. Và giữ **cả hai loại giá dầu** — giao ngay (FRED) và tương lai (WiChart) đo hai thứ khác nhau.

⚠️ `DCOILBRENTEU` (Brent) và `DHHNGSP` (khí Henry Hub giao ngay): **chưa gọi trong đợt này**. Ghi nhận `DHHNGSP` là nguồn ngày duy nhất đo được cho khí — tương lai khí `NG=F` lệch tới **7,02%** (biên độ −82,83 … +30,83), **không thay được**.

---

## 8. Ngân sách request và quy tắc ETL

15 series ở §5, chạy hằng ngày:

| Kịch bản | Cách gọi | Request/ngày |
|---|---|---|
| Tối thiểu — chỉ lấy đuôi | 15 × `observations?limit=10&sort_order=desc` | **15** |
| **Có kiểm vá hồi tố (bắt buộc)** | 15 obs + 15 `series` (đọc `last_updated`) | **30** |
| Có theo lịch công bố | + 6 × `release/dates`, 1 lần/tuần | ≈ +1/ngày |
| **Backfill một lần** | 15 × 1 lời gọi toàn lịch sử | **15 lời gọi · ~500 KB gzip · ~15 giây** |

15 series ≈ 126.000 điểm — dung lượng không đáng kể.

**Năm quy tắc bắt buộc:**

1. 🔴 **`file_type=json` ở MỌI lời gọi** (Bẫy 3).
2. 🔴 **`None if value == "." else float(value)`** ở mọi chỗ parse (Bẫy 1) — 4,3% số dòng của `DGS10`.
3. 🔴 **UPSERT, làm mới cửa sổ 24 tháng mỗi lần chạy** (§4.4).
4. 🔴 **Che `api_key` trong mọi log** (Bẫy 7).
5. ⚠️ **Lưu `units=lin`**, tính tăng trưởng ở tầng phân tích (§3).

**Giám sát hợp đồng — bổ sung riêng cho FRED:**

| Kiểm tra | Bắt được |
|---|---|
| `last_updated` đổi mà giá trị cũ cũng đổi | Vá hồi tố im lặng (§4.1) |
| Khoảng trống > 5 ngày trong chuỗi ngày | `DTWEXBGS` lỡ nhịp H.10 |
| Tỷ lệ dòng `"."` tăng đột biến | Đổi hành vi phía nguồn hoặc gọi nhầm `frequency` |
| `Content-Type` khác `application/json` | Rơi `file_type=json` |

---

## 9. Việc chưa kiểm

- **Rate limit công bố chính thức** — trang tài liệu không đọc ổn định được từ mạng đo; con số 120/phút là nguồn thứ ba.
- **Hành vi khi vượt hạn mức** (`429`, `Retry-After`) — **chủ đích không dò**.
- `units` = `chg` · `ch1` · `pch` · `pca` · `cch` · `cca` · `log`.
- `output_type` = 2 và 3; `aggregation_method` = `sum`, `eop`.
- Nhóm endpoint `category/*` · `releases` · `sources/*` · `maps/*` (GeoFRED).
- **ETag / `If-None-Match` / cache header** — WiChart có, FRED chưa đo.
- Hành vi khi gọi nhiều luồng song song.
- `DCOILBRENTEU` (Brent) — chưa gọi.
