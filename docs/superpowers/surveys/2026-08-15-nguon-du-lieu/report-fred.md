# FRED API (St. Louis Fed) — khảo sát nguồn vĩ mô quốc tế

**Phiên bản:** 0.1 (khảo sát bước đầu) · **Ngày đo:** 2026-08-15 · **Trạng thái:** 53/60 lời gọi thật, tuần tự · **Chưa phải tài liệu chốt**

> Khảo sát khả năng lấp **chỗ trống vĩ mô quốc tế** — khối mà `10-sources/README.md §2` đang liệt vào *Ngoài phạm vi*. Nguồn trong nước đã có WiChart (87 endpoint); FRED bổ sung **mắt xích Mỹ**, không thay thế WiChart. Mọi số đến từ 53 lời gọi thật tới `https://api.stlouisfed.org/fred/`. Cái chưa gọi gắn nhãn **chưa kiểm** (§12).
>
> *(Ghi chú controller: agent khảo sát không ghi được file `.md`; controller ghi lại nguyên văn báo cáo. Đã kiểm chứng độc lập hai khẳng định an toàn — xem §14.)*

## 1. Vì sao là FRED, và lấy đúng cái gì

### 1.1 Nhu cầu rút từ skill `vn-stock-advisor` — không chọn theo cảm tính

Đọc `SKILL.md` + 4 file `references/`. Skill **không liệt kê chỉ báo quốc tế nào theo tên**. Nó nêu **đúng một chuỗi nhân quả**, và chuỗi đó là tiêu chí chọn series:

> `analysis-framework.md` dòng 38 — *"Thế giới tác động tới Việt Nam **gián tiếp qua tỷ giá** (kỳ vọng lãi suất Mỹ → đồng đô → tỷ giá → dư địa chính sách), cộng kênh giá dầu → lạm phát. Nói rõ mắt xích, không nhảy cóc từ 'Fed' sang 'VN-Index'."*

Cộng bốn ràng buộc khác:

| Nguồn trong skill | Ràng buộc suy ra |
|---|---|
| `SKILL.md` §Hai chế độ — chế độ A mở bằng heading **`## Bối cảnh thế giới`** | Phải có số cho mục này, không thì mục rỗng |
| `SKILL.md` §Dữ liệu — *"Tuyệt đối không bịa số"*, *"có công cụ lấy dữ liệu thì gọi và dùng ngay"* | Series phải **truy được realtime**, không phải bảng tra tay |
| `analysis-framework.md` — *"Lãi suất chính sách là ý chí, lãi suất thị trường là cái tạm thời"* | Tách **lãi suất điều hành** khỏi **lãi suất thị trường** thành hai series |
| `reasoning.md` dòng 67 — *"hành động theo mắt xích hiện tại, không theo mắt xích thứ ba"* | Ưu tiên độ trễ thấp; series trễ 45–75 ngày chỉ là bối cảnh |

**Kết luận Bước 1:** skill cần đúng 4 khối — (a) mặt bằng lãi suất Mỹ và kỳ vọng, (b) sức mạnh đồng đô, (c) lạm phát Mỹ, (d) giá dầu + khẩu vị rủi ro. Danh sách ví dụ trong brief (`DFF`, `DGS10`, `DGS2`, `CPIAUCSL`, `DTWEXBGS`, `T10Y2Y`, `UNRATE`, `VIXCLS`, `DCOILWTICO`) **đã xác minh có thật và sống** (§5).

### 1.2 Ranh giới với WiChart — không chồng lấn

| Khối | WiChart có | FRED có | Kết luận |
|---|---|---|---|
| Vĩ mô Việt Nam | 18 key, m/q, trễ 42–72d | Chỉ dữ liệu **năm** của WB/IMF/PWT (§7) | **WiChart thắng tuyệt đối** |
| Tỷ giá VND/USD | `dhtg`, ngày, trễ 0d, 5 series | **Không có series ngày nào** (`count=0`) | WiChart |
| Lãi suất VN | `lsdh` `lslnh` `lshd`, ngày | không có | WiChart |
| Hàng hoá | 61 key (SunSirs, TOCOM, CFR) | WTI/Brent (EIA) | Chồng một phần (§8) |
| **Lãi suất Mỹ, đô Mỹ, CPI Mỹ, VIX** | **không có** | **có, chất lượng cao** | **Chỗ FRED lấp** |

## 2. Đặc tả API — đo được

### 2.1 Endpoint và xác thực

```
GET https://api.stlouisfed.org/fred/{path}?api_key=***&file_type=json&...
```

Khoá truyền bằng **query param `api_key`**, không có header auth. → **Bẫy vận hành:** khoá lọt vào mọi access log, mọi chuỗi URL đem đi cache/debug.

Nhóm endpoint đã **gọi thật**: `series` (16), `series/observations` (27), `series/search` (3), `series/tags` (4), `series/release` (1), `series/vintagedates` (1), `release/dates` (1), `tags` (2). Các nhóm `category/*`, `releases`, `sources/*`, `maps/*`: **chưa gọi**.

### 2.2 Tham số chung

| Tham số | Đo được |
|---|---|
| `api_key` | Bắt buộc, query param |
| `file_type` | ⚠️ **Mặc định là `xml`, KHÔNG phải json.** Đo trực tiếp: bỏ `file_type` → `Content-Type: text/xml`. Phải truyền `file_type=json` ở **mọi** lời gọi |
| `limit` | Mặc định `series/observations` = **100000**. Không cần phân trang cho chuỗi dài nhất đo được (DGS10, 16.858 điểm) |
| `offset` | Có, mặc định 0 |
| `sort_order` | `asc`\|`desc`. `desc`+`limit=n` = cách rẻ nhất lấy n điểm mới nhất |
| `observation_start`/`_end` | Mặc định `1600-01-01` / `9999-12-31` |
| `realtime_start`/`_end` | Mặc định = hôm nay. Trục vintage — §4 |

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
| `count` | int | **Tổng số quan sát của toàn chuỗi**, không phải số dòng trả về. DGS10 `count=16858` kể cả khi `limit=4`. ⚠️ Với `frequency=m` thì `count` **vẫn là số điểm ngày** — Bẫy 4 |
| `date` | `YYYY-MM-DD` | Chuỗi tháng neo **ngày 1**; chuỗi tuần WALCL neo **thứ Tư** |
| `value` | **string** | ⚠️ Luôn là chuỗi. Giá trị thiếu = `"."` — Bẫy 1 |
| `realtime_start/end` (mức dòng) | date | Khoảng thời gian **bản số này còn hiệu lực** — §4 |
| `realtime_start/end` (mức gốc) | date | ⚠️ Khi không truyền, echo về **không phải hôm nay** mà là **vintage hiện hành của chính series đó**. Cùng phiên 2026-08-15: DGS10→`2026-08-15`, DFF→`2026-08-14`, CPIAUCSL→`2026-08-12`, PCEPILFE→`2026-07-30` |

Response `series` (metadata): `observation_start`, `observation_end`, `frequency`+`frequency_short`, `units`+`units_short`, `seasonal_adjustment_short`, `last_updated` (kèm offset `-05`/`-06` = **giờ St. Louis, đổi theo DST**), `popularity`, `notes`.

### 2.4 Lỗi

`HTTP 400` + thân JSON. Hai mẫu bắt được thật:

```json
{"error_code":400,"error_message":"Bad Request.  Invalid value for variable series_id.  Series IDs should be 25 or less alphanumeric characters."}
{"error_code": 400, "error_message": "Bad Request.  No vintage dates exist for the specified real-time period: 2026-08-15 to 2026-08-15."}
```

→ **Khác hẳn FiinTrade/WiChart**: FRED **không** trả `200` kèm dữ liệu rỗng khi tham số sai. Mã lỗi dùng được trực tiếp.

### 2.5 Hiệu năng, kích thước, nén

| | Giá trị |
|---|---|
| Độ trễ (51 lời gọi `200`) | **trung vị 426 ms** · min 370 · p90 809 · max 4.723 |
| Hai lời gọi chậm nhất | `tags?search_text=copyright` 4.723 ms · `tags?tag_group_id=cc` 2.835 ms — nhóm `tags` chậm hơn hẳn nhóm `series` |
| `series/observations` điển hình (limit 4) | ~390–460 ms, **650–710 byte** |
| Kéo toàn bộ DGS10 (16.858 điểm, 1962→nay) | **733 ms · 1.601.211 byte thô · 85.110 byte trên dây (gzip −94,7%)** |
| gzip | Có, 51/53 lời gọi (2 lời gọi `400` không nén) |
| **Header hạn mức** | 🔴 **Không có.** Hợp nhất header 53 response: không `X-RateLimit-*`, không `Retry-After` |
| Tổng lưu lượng cả phiên | 114.199 byte trên dây / 1.699.587 byte thô |

**Hệ quả:** cả lịch sử một chuỗi ngày 64 năm chỉ tốn 85 KB nén và **một** lời gọi. Backfill không phải bài toán.

### 2.6 Rate limit

- **Đo được:** 53 lời gọi tuần tự trong ~1 phút → `200` toàn bộ. Không `429`, không `Retry-After`.
- **Con số tài liệu công bố:** 🔴 **KHÔNG ĐỌC ĐƯỢC.** Host web `fred.stlouisfed.org` **không truy cập được từ máy đo** — WebFetch `403`; `curl` và `urllib` **timeout sau 40 s** trên cả 5 trang (`/docs/api/fred/`, `series_observations.html`, `terms_of_use.html`, `realtime_period.html`, `series_search.html`). Chỉ `api.stlouisfed.org` thông.
- Nguồn thứ ba (tìm kiếm web, **không phải tài liệu gốc, chưa kiểm**) nêu **120 request/phút cho khoá đã đăng ký**, vượt trả `429`. **Không dùng làm cam kết.**
- **Chủ đích không dò ngưỡng chặn.**

## 3. Biến thể `units` — đã thử thật

| `units` | Đo được |
|---|---|
| `lin` (mặc định) | CPIAUCSL 2026-07 = **332.813** (chỉ số 1982–84=100) |
| `pc1` | CPIAUCSL 2026-07 = **3.30386** → **phần trăm YoY, dạng phần trăm đầy đủ (3,30%), KHÔNG phải phân số 0,033** |

> ⚠️ **Ngược quy ước với WiChart.** WiChart Bẫy 5: series "Tăng trưởng" lưu **dạng phân số làm tròn 2 chữ số**. FRED `pc1` trả **5 chữ số thập phân, đơn vị phần trăm**. Tầng chuẩn hoá phải xử lý riêng từng nguồn, không dùng chung hàm.

`chg`, `ch1`, `pch`, `pca`, `cch`, `cca`, `log`: **chưa kiểm**.

**Khuyến nghị:** ETL **lưu `lin`**, tự tính tăng trưởng ở tầng phân tích — vì `pc1` là phái sinh, lưu nó thì mất khả năng tính lại khi số gốc bị vá hồi tố (§4).

## 4. 🔴 Bản vá hồi tố (revision / ALFRED)

FRED **không phải kho append-only**.

### 4.1 Bằng chứng — PAYEMS tháng 5/2026

`series/observations?series_id=PAYEMS&realtime_start=1990-01-01&realtime_end=9999-12-31&observation_start=2026-05-01&observation_end=2026-05-01`:

| Bản (vintage) hiệu lực từ | đến | Giá trị (nghìn người) |
|---|---|---|
| 2026-06-05 | 2026-07-01 | **159.001** |
| 2026-07-02 | 2026-08-06 | **158.927** (−74) |
| 2026-08-07 | 9999-12-31 | **158.861** (−66) |

→ **Một điểm dữ liệu có 3 giá trị.** Lệch tích luỹ 140 nghìn việc làm. Kho lưu bản đầu và không cập nhật → biểu đồ Finext **vĩnh viễn khác** biểu đồ FRED.

### 4.2 Ba chế độ đọc, đều đã gọi thật

| Cách gọi | Trả về | Dùng khi |
|---|---|---|
| Mặc định (không `realtime_*`) | **Bản hiện hành** — 1 giá trị/ngày | ETL thường nhật. **Cái nên lưu** |
| `realtime_start=1990-01-01&realtime_end=9999-12-31` | **Toàn bộ vintage**, mỗi bản một dòng | Bảng lịch sử sửa đổi |
| `output_type=4` + `realtime_*` mở rộng | **Chỉ bản công bố lần đầu** | Backtest không nhìn trộm tương lai |

`output_type=4` cho PAYEMS 2026-01→07 (bản đầu): 158.627 · 158.466 · 158.637 · 158.736 · **159.001** · 158.984 · 158.858. So bản hiện hành: tháng 5 = 158.861 (đầu 159.001), tháng 6 = 158.881 (đầu 158.984) → **bản đầu luôn cao hơn** trong loạt này.

> ⚠️ `output_type=4` mà **không** truyền `realtime_start`/`realtime_end` mở rộng → `400 "No vintage dates exist for the specified real-time period"`. Phải truyền cả hai.

### 4.3 Lịch vintage lấy được

`series/vintagedates?series_id=PAYEMS` → **858 ngày vintage**, 8 bản gần nhất: 2026-08-07, 07-02, 06-05, 05-08, 04-03, 03-06, 02-11, 01-09.
`series/release?series_id=PAYEMS` → release **id 50 "Employment Situation"** (`press_release: true`).
`release/dates?release_id=50` → **862 ngày công bố**, 6 gần nhất **trùng khớp 100%** với danh sách vintage.

→ **Lịch công bố lấy được bằng API.** Thứ WiChart không có: ETL có thể **đặt lịch gọi đúng ngày ra số** thay vì poll mù.

### 4.4 Quy tắc đề xuất cho kho dữ liệu

1. **Lưu bản hiện hành**, khoá `(series_id, date)`, **UPSERT** — không INSERT-only.
2. **Không tin `date` là bất biến về giá trị.** Mỗi lần chạy làm mới **cửa sổ 24 tháng gần nhất** cho series tháng/quý.
3. Ghi `last_updated` của metadata làm cột kiểm soát — đổi thì mới kéo lại.
4. Cần backtest nghiêm túc → bảng phụ chứa vintage, dùng `output_type=4`. **Chưa cần giai đoạn này.**

## 5. Bảng 15 series đã đo — đề xuất lấy

Đo 2026-08-15. **Trễ** = số ngày từ `observation_end` tới 2026-08-15 (cùng quy ước `wichart.md §5`).

| series_id | Chỉ tiêu | Tần suất | Lịch sử | Trễ | Đơn vị | Số điểm | Giá trị mới nhất | Mắt xích trong skill |
|---|---|---|---|---|---|---|---|---|
| `DFF` | Fed funds hiệu lực | d, 7-day | 1954-07-01 → | **2d** | % | 26.342 | 3,63 (08-13) | **Ý chí chính sách Mỹ** — đầu chuỗi |
| `FEDFUNDS` | Fed funds bình quân tháng | m | 1954-07-01 → | 45d | % | 865 | 3,63 (07/2026) | Bản tháng, so chuỗi dài |
| `SOFR` | Repo có bảo đảm qua đêm | d | 2018-04-03 → | 2d | % | 2.183 | 3,62 (08-13) | Căng thẳng thanh khoản đô |
| `DGS2` | Lợi suất TPCP Mỹ 2 năm | d | 1976-06-01 → | 2d | % | 13.098 | 4,15 (08-13) | **Kỳ vọng lãi suất** |
| `DGS10` | Lợi suất TPCP Mỹ 10 năm | d | 1962-01-02 → | 2d | % | 16.858 | 4,63 (08-13) | Mặt bằng chi phí vốn toàn cầu |
| `T10Y2Y` | Chênh 10y−2y | d | 1976-06-01 → | **1d** | % | 13.099 | 0,51 (08-14) | Vị trí chu kỳ |
| `T10YIE` | Breakeven lạm phát 10 năm | d | 2003-01-02 → | **1d** | % | 6.162 | 2,27 (08-14) | **Kỳ vọng lạm phát realtime** |
| `DTWEXBGS` | Chỉ số đô Mỹ (broad, danh nghĩa) | d | 2006-01-02 → | **8d** | Index 2006-01=100 | 5.375 | 119,065 (08-07) | **"đồng đô"** — mắt xích 2 |
| `DEXCHUS` | CNY/USD | d | 1981-01-02 → | **8d** | CNY/1 USD | 11.896 | 6,7474 (08-07) | Neo khu vực cho VND |
| `CPIAUCSL` | CPI Mỹ (SA) | m | 1947-01-01 → | 45d | Index 1982-84=100 | 955 | 332,813 · YoY **3,30%** | Lạm phát Mỹ |
| `PCEPILFE` | Core PCE | m | 1959-01-01 → | **75d** | Index 2017=100 | 810 | 130,266 (06/2026) | Thước Fed thật sự nhìn |
| `UNRATE` | Thất nghiệp Mỹ | m | 1948-01-01 → | 45d | % | 943 | 4,1% (07/2026) | Sức ép hạ lãi suất |
| `PAYEMS` | Bảng lương phi nông nghiệp | m | 1939-01-01 → | 45d | nghìn người | 1.051 | 158.858 (07/2026) | Số làm thị trường biến động mạnh nhất |
| `VIXCLS` | VIX | d | 1990-01-02 → | 2d | Index | 9.553 | 14,63 (08-13) | Khẩu vị rủi ro toàn cầu |
| `DCOILWTICO` | Dầu WTI giao ngay | d | 1986-01-02 → | 4d | USD/thùng | 10.594 | 84,77 (08-11) | **Kênh dầu → lạm phát** |

> ### ⚠️ Đọc cột "Trễ" cho đúng — controller đính chính cách diễn đạt
>
> Cột trễ đếm **ngày lịch từ ngày đo (thứ Bảy 2026-08-15)**, nên nó trộn ba thứ rất khác nhau vào một con số. Đo lại đuôi chuỗi ngày 2026-08-15 để tách bạch:
>
> | Loại | Bằng chứng (đuôi chuỗi thật) | Nghĩa thật |
> |---|---|---|
> | **Chuỗi ngày, cập nhật T+1** | `T10Y2Y`: 08-14 · 08-13 · 08-12 · 08-11 · 08-10 — liên tục tới **thứ Sáu** | ✅ **Không trễ.** Ngày đo là thứ Bảy, phiên gần nhất là thứ Sáu. "Trễ 1 ngày" chỉ là hiệu ứng cuối tuần |
> | **Chuỗi ngày, T+1 nhưng chưa kịp trong ngày đo** | `DGS10`: 08-13 · 08-12 · 08-11 · 08-10 · 08-07 — thiếu thứ Sáu | ✅ Về bản chất vẫn T+1; số thứ Sáu lên muộn hơn thời điểm đo |
> | 🔴 **Chuỗi ngày nhưng CÔNG BỐ THEO TUẦN** | `DTWEXBGS`: 08-07 · 08-06 · 08-05 · 08-04 · 08-03 · 07-31 — **trống trọn tuần 08-10→08-14** | 🔴 **Đây mới là vấn đề thật** |
>
> **Chỉ có nhóm thứ ba là hạn chế thật.** `DTWEXBGS`/`DEXCHUS` thuộc bản công bố **H.10 của Fed, ra mỗi thứ Hai**, mang dữ liệu tới hết thứ Sáu tuần trước (`last_updated` 2026-08-10 15:16 → `observation_end` 2026-08-07). Nên độ trễ **dao động 3 ngày (sáng thứ Ba) đến 9 ngày (Chủ nhật)**, chứ không cố định 8. Con số 8 chỉ là lát cắt tại thời điểm đo.
>
> ➜ Nói gọn: **lãi suất, VIX, dầu, chỉ số — tươi T+1, dùng được cho phân tích hằng ngày. Chỉ số đô Mỹ mới là chỗ hụt, vì Fed chỉ ra số mỗi tuần một lần.**
>
> *(Quan sát phụ chưa giải thích: `T10Y2Y` = DGS10 − DGS2 nhưng lại **có** điểm 08-14 trong khi `DGS10` thì chưa. Chuỗi phái sinh đi trước chuỗi thành phần. Chưa kiểm nguyên nhân — có thể hai chuỗi cập nhật lệch giờ trong ngày.)*

Ghi chú độ trễ:
- **Nhóm ngày dùng được:** `T10Y2Y`, `T10YIE` trễ **1 ngày** (cập nhật 16:03 giờ St. Louis). `DGS2`/`DGS10`/`DFF`/`SOFR`/`VIXCLS` trễ **2 ngày** vào thứ Bảy 2026-08-15 — điểm cuối là thứ Năm.
- 🔴 **`DTWEXBGS` và `DEXCHUS` trễ 8 ngày.** Cả hai thuộc bản công bố H.10, `last_updated` 2026-08-10, điểm cuối 2026-08-07. **Chỉ số đô Mỹ trên FRED là số tuần trước.** Nếu skill cần "đô đang mạnh hay yếu hôm nay" thì FRED **không đáp ứng**.
- 🔴 **`PCEPILFE` trễ 75 ngày** — điểm cuối 06/2026. Chậm nhất danh sách.
- Nhóm tháng (`CPIAUCSL`, `UNRATE`, `PAYEMS`) trễ 45 ngày theo quy ước neo đầu tháng — thực chất **12–15 ngày sau khi kỳ tham chiếu kết thúc**, tương đương WiChart (42d).

## 6. Bẫy triển khai — xác nhận bằng dữ liệu thật

**Bẫy 1 — 🔴 Giá trị thiếu là chuỗi `"."`, không phải `null`.** Đo `DGS10` cửa sổ 2026-06-29 → 07-10:
```json
{"date": "2026-07-02", "value": "4.49"},
{"date": "2026-07-03", "value": "."},     ← nghỉ lễ Quốc khánh Mỹ
{"date": "2026-07-06", "value": "4.48"}
```
Toàn chuỗi DGS10 (16.858 điểm): **719 điểm `"."` = 4,3%**. Cuối tuần **không** có dòng; chỉ ngày nghỉ lễ giữa tuần sinh `"."`. → `float(value)` ném `ValueError` ở 4,3% số dòng.

**Bẫy 2 — `value` luôn là string, độ chính xác không đồng nhất trong cùng series.** `FEDFUNDS` trả `"3.6300000000"` cho tháng 7 nhưng `"3.63"` cho tháng 6 — **cùng một lời gọi**. Đừng suy đơn vị từ số chữ số thập phân.

**Bẫy 3 — Mặc định `file_type` là `xml`.** Quên `file_type=json` → nhận XML mà vẫn `HTTP 200`.

**Bẫy 4 — ⚠️ `frequency=m` gộp phía server: `count` sai và kỳ dở dang trả `"."`.** Gọi `DGS10&frequency=m&aggregation_method=avg&limit=4&sort_order=desc`:
```json
"count": 16858,                          ← vẫn là số điểm NGÀY, không phải số tháng
"observations": [
  {"date": "2026-08-01", "value": "."},  ← tháng 8 chưa xong → "."
  {"date": "2026-07-01", "value": "4.60"}
]
```
→ (a) không dùng `count` để phân trang khi có `frequency`; (b) **kỳ hiện tại luôn `"."`** khi gộp — đừng đọc thành "dữ liệu thiếu".

**Bẫy 5 — `realtime_start` mức gốc không phải ngày hôm nay** (§2.3).

**Bẫy 6 — `last_updated` có offset múi giờ đổi theo DST.** Đo được `"2026-08-14 15:17:23-05"` (hè) và `"2026-02-04 11:43:37-06"` (đông). Không hardcode offset.

**Bẫy 7 — Khoá API nằm trong URL.** Không có header auth. Mọi log/cache key/trace đều dính khoá nếu không che.

## 7. FRED có dữ liệu Việt Nam không — đo thẳng

| Phép đo | Kết quả |
|---|---|
| `series/search?search_text=Vietnam` | **378 series** |
| `...&filter_variable=frequency&filter_value=Daily` | 🔴 **`count = 0` — không một series ngày nào** |
| `...&filter_value=Monthly` | 50 series, **phần lớn là nhiễu**: `LNU*` là *"Veterans, Vietnam-Era"* — dữ liệu **cựu binh Mỹ** |

Series Việt Nam thật (top 30 theo `popularity`):

| series_id | Chỉ tiêu | Tần suất | Phủ | Cập nhật cuối |
|---|---|---|---|---|
| `IMP5520` | Mỹ nhập khẩu từ Việt Nam | **m** | 1992-01 → 2026-06 | 2026-08-04 |
| `EXP5520` | Mỹ xuất khẩu sang Việt Nam | **m** | 1992-01 → 2026-06 | 2026-08-04 |
| `FPCPITOTLZGVNM` | Lạm phát CPI (World Bank) | y | 1996 → 2025 | 2026-06-30 |
| `MKTGDPVNA646NWDB` | GDP (World Bank) | y | 1985 → 2025 | 2026-06-30 |
| `VNMPCPIPCPPPT` | CPI %Δ (IMF WEO, **dự báo tới 2031**) | y | 1990 → 2031 | 2026-04-22 |
| `VNMNGDPRPCPPPT` | GDP thực %Δ (IMF WEO, dự báo) | y | 1990 → 2031 | 2026-04-22 |
| `FXRATEVNA618NUPN` | Tỷ giá VND/USD | y | 1970 → **2010** | **2012-09-17 — chết 14 năm** |
| `DDOE02VNA086NWDB` | CPI Việt Nam (chỉ số) | y | 1994 → **2017** | **2022 — chết** |
| `DDDM01VNA156NWDB` | Vốn hoá TTCK/GDP | y | 2008 → **2020** | 2024 — chết |
| `WUIVNM` | World Uncertainty Index | q | 1956 → 2026-04 | 2026-07-31 |

**Kết luận thẳng:** FRED **không thay thế được WiChart cho mảng Việt Nam**, cũng không bổ sung gì đáng kể. Tỷ giá VND/USD dừng 2010 (WiChart: ngày, trễ 0d). CPI Việt Nam là **số năm** (WiChart: tháng từ 2003). Không có lãi suất, cung tiền, tín dụng VN ở tần suất dùng được. **Hai thứ FRED có mà WiChart không:** (1) `IMP5520`/`EXP5520` — thương mại song phương Mỹ–Việt **theo tháng, phía Mỹ báo cáo**, hữu ích cho câu chuyện thuế quan/xuất khẩu; (2) dự báo IMF WEO tới 2031. Cả hai là "gia vị", không phải xương sống.

## 8. Chồng lấn với WiChart ở mảng dầu

WiChart có 6 key năng lượng (SunSirs, giá CNY) với cửa sổ trượt **2 năm** (`WIN2Y` — mất vĩnh viễn nếu không chạy ETL). FRED `DCOILWTICO` cho **1986 → nay, 10.594 điểm, một lời gọi**, nguồn EIA, `public domain`.

→ Với dầu WTI, **FRED tốt hơn hẳn**: lịch sử đầy đủ, không cửa sổ trượt, không rủi ro mất đuôi. Giữ WiChart cho hàng hoá Trung Quốc (SunSirs) mà FRED không có.

## 9. 🔴 Ranh giới phân phối lại — đo được bằng chính API

FRED gắn **nhãn giấy phép ngay trên từng series** qua `series/tags`, nhóm `tag_group_id=cc`. Gọi `tags?tag_group_id=cc` (2026-08-15) — **đúng 3 nhãn, phủ toàn kho**:

| Nhãn | Số series | Tỷ lệ |
|---|---|---|
| `public domain: citation requested` | **618.088** | 73,5% |
| `copyrighted: citation required` | **208.642** | 24,8% |
| `copyrighted: pre-approval required` | **14.282** | **1,7%** |
| **Tổng** | **841.012** | |

Kiểm nhãn 4 series đã chọn:

| series | Nhãn giấy phép | Chủ dữ liệu |
|---|---|---|
| `DGS10` | `public domain: citation requested` | Fed Board (`frb`, release `h15`) |
| `DTWEXBGS` | `public domain: citation requested` | Fed Board (`h10`) |
| `DCOILWTICO` | `public domain: citation requested` | EIA |
| **`VIXCLS`** | 🔴 **`copyrighted: citation required`** | **CBOE** |

`notes` của `VIXCLS`, nguyên văn từ API: *"Copyright, 2016, Chicago Board Options Exchange, Inc. Reprinted with permission."*

**Ranh giới quan sát được:**
1. Kho FRED **không đồng nhất một giấy phép**. 26,5% là dữ liệu bên thứ ba có bản quyền; 1,7% còn đòi **pre-approval**.
2. Nhãn **truy được bằng API** → ETL có thể **kiểm tự động** trước khi lưu và **chặn ở tầng phân phối** với series `copyrighted`.
3. Trong 15 series đề xuất, **14 series `public domain: citation requested`** (Fed Board, BLS, BEA, EIA). **Đúng một series `copyrighted`: `VIXCLS`.**
4. Trang điều khoản gốc `terms_of_use.html` **không đọc được từ máy đo** → **toàn văn điều khoản: chưa kiểm**. Cái đo được là **nhãn trên từng series**.

*(Chủ dự án tự xử lý pháp lý — mục này chỉ ghi cái quan sát được.)*

## 10. Ngân sách request nếu pull định kỳ

15 series ở §5, ETL hằng ngày:

| Kịch bản | Cách gọi | Request/ngày |
|---|---|---|
| **Tối thiểu — chỉ đuôi** | 15 × `observations?limit=10&sort_order=desc` | **15** |
| **Có kiểm vá hồi tố** (khuyến nghị) | 15 obs + 15 `series` (đọc `last_updated`) | **30** |
| Có theo lịch công bố | +6 `release/dates`, 1 lần/tuần | ≈ **+1/ngày** |
| **Backfill một lần** | 15 × 1 lời gọi toàn lịch sử | **15 lời gọi, ~500 KB gzip, ~15 giây** |

**Đối chiếu hạn mức:** 30 request/ngày so với **120 request/phút** (nguồn thứ ba, chưa kiểm) = **0,02% hạn mức phút nếu dồn vào một phút**. Kể cả mở rộng lên 100 series vẫn dưới một phút hạn mức. Lưu trữ: 15 series ~126.000 điểm — không đáng kể.

## 11. Rủi ro và giới hạn — nói thẳng

| # | Rủi ro | Mức |
|---|---|---|
| 1 | 🔴 **Chỉ số đô Mỹ trễ 8 ngày.** `DTWEXBGS` là mắt xích trung tâm của skill nhưng FRED chỉ có số tuần trước. Không có nguồn thay thế trong bộ nguồn hiện tại | Cao |
| 2 | 🔴 **Vá hồi tố im lặng.** PAYEMS 05/2026 đổi 2 lần, lệch 140 nghìn. Kho INSERT-only lệch vĩnh viễn | Cao |
| 3 | 🔴 **Khoá API trong URL** — lọt log nếu không che | Cao (dễ chặn) |
| 4 | ⚠️ `VIXCLS` có **bản quyền CBOE** trong khi 14 series còn lại public domain. Phân phối lại cho khách hàng cuối phải xử lý riêng | Trung bình |
| 5 | ⚠️ **Không đọc được tài liệu gốc và điều khoản** từ môi trường đo → rate limit và điều khoản **chưa kiểm** | Trung bình |
| 6 | ⚠️ Không có header hạn mức → ETL tự giữ nhịp, giống WiChart/FiinTrade | Thấp (tải rất nhỏ) |
| 7 | ⚠️ `PCEPILFE` trễ 75 ngày — dùng làm bối cảnh, **không** để hành động | Thấp |
| 8 | ℹ️ FRED **không lấp được** mảng "cổ phiếu và chỉ số quốc tế" (S&P 500, Nasdaq…) — **chưa kiểm** trong phiên này | Thấp |

**So với hai nguồn hiện có, FRED hơn ở ba điểm:** (a) là **public API có khoá, có tài liệu** — khác hẳn "API nội bộ không cam kết" của BVSC/FiinTrade/WiChart; (b) **lỗi trả đúng mã 400**, không giả `200` rỗng; (c) **có trục vintage** — không nguồn nào khác trong dự án có.

## 12. Việc chưa kiểm

- **Rate limit công bố chính thức** — trang tài liệu không truy cập được; 120/phút là nguồn thứ ba.
- **Hành vi khi vượt hạn mức** (`429`, `Retry-After`) — chủ đích không dò.
- **Toàn văn điều khoản** `terms_of_use.html` và `fred.stlouisfed.org/legal`.
- `units` = `chg`, `ch1`, `pch`, `pca`, `cch`, `cca`, `log`.
- `output_type` = 2 và 3; `aggregation_method` = `sum`, `eop`.
- Nhóm endpoint `category/*`, `releases`, `sources/*`, `maps/*` (GeoFRED).
- ~~**Chỉ số chứng khoán quốc tế**~~ → **đã kiểm, xem §15.**
- ETag / `If-None-Match` / cache header — **chưa kiểm** (WiChart có, FRED chưa đo).
- Hành vi nhiều luồng song song.
- `DCOILBRENTEU` (Brent) — chưa gọi.

## 13. Kết luận

**Lấy.** FRED lấp đúng chỗ trống vĩ mô quốc tế mà skill `vn-stock-advisor` cần, chi phí gần bằng không: **30 request/ngày, ~500 KB backfill một lần**, 14/15 series public domain, lỗi rõ ràng, lịch công bố lấy được bằng API.

**Ba điều kiện bắt buộc trước khi đưa vào kho:**
1. **UPSERT, không INSERT-only** — làm mới cửa sổ 24 tháng mỗi lần chạy (§4.4).
2. **`None if value == "." else float(value)`** ở mọi chỗ parse (Bẫy 1) — 4,3% dòng của DGS10.
3. **Che `api_key` trong mọi log** (Bẫy 7).

**Không lấy từ FRED:** toàn bộ mảng Việt Nam — WiChart hơn ở mọi chiều đo được (§7).

**Còn treo trước khi dựng pipeline:** đọc được trang điều khoản và rate limit gốc; tìm nguồn thay thế cho **chỉ số đô Mỹ trễ 8 ngày** — đây là lỗ hổng thật, không tô hồng được.

## 14. Kiểm chứng độc lập của controller *(2026-08-15)*

Hai khẳng định an toàn của agent đã được kiểm lại bằng lệnh riêng, không tin lời agent:

| Khẳng định | Cách kiểm | Kết quả |
|---|---|---|
| "0 file chứa giá trị khoá" | Đọc khoá thật từ `.env` (32 ký tự), quét đệ quy **toàn bộ** scratchpad bằng so khớp chuỗi nguyên văn | ✅ **0 file** trùng khớp |
| "54/55 file có `api_key=***`" | Đếm file trong `fred-raw/` chứa chuỗi che | ✅ **54 file** |
| "Không chạy git, không sửa repo" | `git status --porcelain` + `git log -1` | ✅ HEAD vẫn `9de1e3b`, không file nào của repo bị sửa |

### 🔴 Một rủi ro an toàn phát hiện ngoài lề — không phải do agent

`.gitignore` ở gốc repo **chưa bao giờ được commit** (`git log -- .gitignore` rỗng; file tạo 2026-08-15 13:00, ngay sau `.env` lúc 12:59). Nó đang bảo vệ `.env` đúng cách **ở máy này** (`git check-ignore -v .env` → `.gitignore:1`), nhưng vì chưa vào lịch sử git nên **sự bảo vệ đó không đi theo repo**. Cần commit `.gitignore` trước lần push tới.

## 15. Chỉ số chứng khoán quốc tế — controller đo bổ sung *(7 lời gọi, 2026-08-15)*

Mục này agent để "chưa kiểm". Controller gọi thật vì nó **chạm trực tiếp vào quyết định chọn nguồn**: FiinTrade đã có sẵn `DJI`, `NASDAQ`, `N225` (phát hiện trong `report-omo-gap.md`).

| series | Lịch sử | Trễ | Giấy phép | Chủ dữ liệu |
|---|---|---:|---|---|
| `SP500` | **2016-08-15** → 2026-08-14 | 1d | 🔴 **copyrighted: pre-approval required** | S&P Dow Jones Indices |
| `DJIA` | **2016-08-15** → 2026-08-14 | 1d | 🔴 **copyrighted: pre-approval required** | S&P Dow Jones Indices |
| `NASDAQCOM` | 1971-02-05 → 2026-08-14 | 1d | 🔴 **copyrighted: pre-approval required** | Nasdaq Inc. |
| `NIKKEI225` | 1949-05-16 → 2026-08-14 | 1d | ⚠️ copyrighted: citation required | Nikkei Inc. |

**Hai điều chỉnh so với phần agent viết:**

1. **Suy đoán "chỉ giữ 10 năm" đúng một nửa.** `SP500` và `DJIA` bắt đầu **đúng ngày 2016-08-15** — tức chính xác 10 năm trước ngày đo, xác nhận đây là **cửa sổ trượt 10 năm** (giống cơ chế `WIN2Y` của WiChart). Nhưng `NASDAQCOM` có **55 năm** và `NIKKEI225` có **77 năm** lịch sử đầy đủ. Không thể nói chung "các series này chỉ giữ 10 năm".

2. **Giấy phép nghiêm ngặt hơn dự đoán.** Cả 4 đều `copyrighted`, và **3/4 ở mức `pre-approval required`** — bậc chặt nhất, chỉ chiếm **1,7% toàn kho FRED** (§9). Đây không phải "citation required" như `VIXCLS`.

### 🔵 Hệ quả: lấy chỉ số quốc tế từ FiinTrade, không lấy từ FRED

| | FRED | FiinTrade |
|---|---|---|
| Chỉ số có | SP500 · DJIA · NASDAQCOM · NIKKEI225 | `DJI` · `NASDAQ` · `N225` (+ `GoldS`, `OilWTI`) |
| Giấy phép | 🔴 3/4 đòi **pre-approval** của S&P/Nasdaq | Nằm trong quyền đã có với BVSC/FiinTrade — *"được phép thu thập, lưu trữ và phái sinh"* (`market-data-store.md:5`) |
| Phụ thuộc | Thêm một nguồn ngoài | Nguồn **đã tích hợp**, cùng cơ chế xác thực |

→ **Đề xuất: không lấy chỉ số chứng khoán quốc tế từ FRED.** Dùng FiinTrade cho phần này, dành FRED cho lãi suất / lạm phát / đô Mỹ / dầu — nơi 14/15 series là public domain.

*(Chưa kiểm: độ sâu lịch sử và tần suất thật của `DJI`/`NASDAQ`/`N225` bên FiinTrade — mới chỉ thấy tên trong danh mục `GetAllChartEconomy`, chưa gọi endpoint dữ liệu. Phải đo trước khi chốt.)*

## Phụ lục — Nhật ký đo

| | |
|---|---|
| Ngày | 2026-08-15 |
| Số lời gọi | **53 / trần 60** (51×`200`, 2×`400` chủ đích) |
| Chế độ | Tuần tự, một luồng, máy trạm tại Việt Nam |
| Tổng thời gian | ~1 phút (tổng latency 53 lời gọi) |
| Log thô | `scratchpad/fred-raw/` — 55 file (`NN_<tag>.json`, `_ledger.jsonl`, `_summary_step3.json`) |
| Che khoá | Regex thay `api_key=***` trước khi ghi |
| Script | `scratchpad/fredcall.py` (harness, trần cứng 60), `step1.py`–`step4.py`, `getdocs.py` |
| Không truy cập được | `fred.stlouisfed.org` (host web/tài liệu) — timeout 40 s qua `curl`/`urllib`, `403` qua WebFetch. Chỉ `api.stlouisfed.org` thông |

Nguồn cho phần rate limit / điều khoản (nguồn thứ ba, **chưa kiểm** — không phải tài liệu gốc):
- Terms of Use — FRED: `https://fred.stlouisfed.org/docs/api/terms_of_use.html` (không truy cập được từ máy đo)
- Ethical Use of Data with FRED — St. Louis Fed
- `fredr` — CRAN NEWS
