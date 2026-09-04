# Spec — lát 6 `etl wichart`: vĩ mô, tiền tệ và giá hàng hoá WiChart

**Ngày:** 2026-09-05 · **Nhánh:** `feat/wichart-etl` · **Trạng thái:** chờ chủ dự án duyệt spec
**Tiền đề:** [roadmap — Điểm vào cho lát 6](../../../00-overview/roadmap.md) · [tài liệu nguồn WiChart](../../../10-sources/macro/wichart.md) · [bước 4 (macro)](../2026-08-25-postgres-data-schema/step-04-macro.md) và [bước 5 (asset)](../2026-08-25-postgres-data-schema/step-05-asset.md) của spec schema · [spec lát 5](../2026-09-04-fundamentals-etl/spec.md) (khuôn job, khuôn nạp registry từ file)
**Brainstorm:** 12 câu hỏi, chủ dự án chốt 2026-09-05 sáng — ghi tại §4 và §9. Số đo trong ngày: [`verify-wichart-2026-09-05.txt`](verify-wichart-2026-09-05.txt) · [`dead-series-check.txt`](dead-series-check.txt) · [`weekend-points-check.txt`](weekend-points-check.txt).

Tiêu chí xuyên suốt: **kho là sự thật nguồn sau khi chuẩn hoá đơn vị và neo kỳ, không có gì tự tính**; mọi luật đều phải truy được về một số đo.

---

## 1. Vì sao lát này, và lát này là gì

Lát 6 theo [thứ tự chuẩn](../../../00-overview/roadmap.md): job `python -m etl wichart` gọi **68 key** của `api.wichart.vn` (67 key thu thập theo khối §9 của tài liệu nguồn + `ca_tra` sống lại — §9.1; 20 key Tier X đứng ngoài), chuẩn hoá đơn vị bằng bảng hệ số hardcode, neo kỳ về ngày đầu kỳ, và ghi:

- **53 series** của 24 key vĩ mô/tiền tệ → `macro.observation` (40 `data` + 13 `growth_ref`);
- **52 series** của 43 key giá → `asset.price_daily` (47 hàng hoá + 5 tỷ giá USD/VND của `dhtg`),

kèm nạp hai registry (`macro.indicator`/`indicator_source`, `asset.asset`/`asset_external_id`) ở đầu mỗi lượt và một dòng `macro.series_break` cho GDP giá so sánh. Đây là job đầu tiên ghi vào hai miền này (ngoài cụm OMO); lược đồ đã có từ migration `0005`/`0006`, **không migration mới**.

Đứng trước lát 7 (quốc tế) vì cùng ổ cắm registry: lát 7 chỉ thêm `source='fred'|'yahoo'|…` vào hai bảng ánh xạ mà lát này dựng cách nạp.

## 2. Dữ kiện đã đo vs giả định *(§4.8 bước 0)*

### 2.1 Đã đo — 2026-09-05 sáng, ~230 lời gọi thật + truy vấn kho

| Dữ kiện | Số | Nguồn |
|---|---|---|
| Hợp đồng nguồn còn nguyên sau 3 tuần: số series, tên, `scale`, tần suất **0 FAIL** trên 72 key; 22 FAIL "độ trễ" là lỗi của phép kiểm (so số ngày tuyệt đối chụp lúc audit), 2 FAIL `CONST` ở key Tier X | 485/509 | [verify](verify-wichart-2026-09-05.txt) |
| **~90 lời gọi liên tiếp không giãn cách, rồi ~140 lời gọi nữa trong 10 phút: 0 lỗi HTTP, 0 tín hiệu chặn** ⇒ mức tải 68 lời gọi/lượt an toàn (§4.3 — kết luận chỉ ở mức này) | | ba script đo |
| Series chết, đúng cờ: `thiec` 547 ngày · `cao_su` 572 · `gdpbinhquan` và `ncp[1]` 1.343 · RON 95 (`xang_dau[0]`) 99 · `gao_tpxk` đứng giá 93 ngày | | [dead-series-check](dead-series-check.txt) |
| `gdpbinhquan` kiểm lại theo chủ dự án ("có thể chưa tới kỳ"): chuỗi **năm** (`timeArray ['y']`, `timeUpdate` "Năm 2023"), trong khi `ds` cùng nguồn GSO đã "Năm 2025", `ncp` "Năm 2024" ⇒ bỏ hai kỳ liên tiếp, **chết thật** | | nt |
| **`ca_tra` hết đóng băng**: điểm mới nhất 28/08, giá đổi 22/08 | | nt |
| `lshd` 3 series giá đứng 81–137 ngày nhưng có điểm mới mỗi ngày — lãi suất quầy đổi thưa, **không phải chết** | | nt |
| **`vai_cotton_my` là US cent/lb**, nhãn `USD/tấn` sai: 82,33–93,14 khớp bậc ICE cotton #2 `CT=F` 83,36–91,70 cùng tuần, lệch ≈ 1 %, nhãn ngày trễ 1 ngày so với phiên Mỹ | 5 ngày | nt + Yahoo `v8/finance/chart/CT=F` |
| Điểm cuối tuần **không đồng nhất**: `vang_the_gioi` 193 điểm T7/CN chỉ 70 chép lại (phiên Mỹ đóng rạng sáng T7 giờ VN); `lua`/`gao_nguyen_lieu` 174 điểm cuối tuần thì 172–173 chép lại; 8 key **không có** điểm cuối tuần; `kem`/`niken` 208 điểm cuối tuần, 205–207 chép lại | 58 series ngày | [weekend-points-check](weekend-points-check.txt) |
| Chép lại **trong tuần** cũng phổ biến và là dữ kiện thật (giá khảo sát không đổi): `lua` 82 %, `ca_tra` 93 %, `lsdh` 100 % | | nt |
| Kho: `macro.indicator`/`indicator_source`/`observation`/`series_break` và `asset.asset`/`asset_external_id`/`price_daily`/`ohlc_daily` **đều 0 dòng**; `data_domain_state` đã có `'macro.indicator'` và `'asset'` trong CHECK; role `dlck_etl` có `SELECT/INSERT/UPDATE/DELETE` cả hai schema (`0009`) — **vẫn phải kiểm bằng test dưới role** (§3.5) | | truy vấn `ETL_DATABASE_URL` · `0008` · `0009` |
| Epoch = 17:00 UTC = 00:00 giờ VN (B1 của verify PASS); neo tháng ngày 1, quý ngày 1 tháng **cuối** quý, năm bất nhất | | verify B1/B2 |

### 2.2 Giả định — CHƯA kiểm

1. WiChart cập nhật chuỗi ngày **trước 08:00 giờ VN** của ngày kế. Chưa đo giờ nạp; lát 13 xếp lịch sẽ cần số này. Spec này chạy tay nên không phụ thuộc.
2. Nguồn **không** vá số quá khứ ở chuỗi tháng/quý (GSO có điều chỉnh sơ bộ → chính thức). Thiết kế UPSERT trọn (§4.4) đúng dù giả định này sai; `stats.changed` sẽ đo tần suất thật.
3. Chuẩn của `vai_cotton_my` là hợp đồng tháng gần ICE (lệch ≈ 1 % có thể là Cotlook A). Không ảnh hưởng đơn vị; đã ghi ở [wichart.md §10](../../../10-sources/macro/wichart.md) để hỏi WiGroup.

## 3. Phạm vi

### 3.1 Trong phạm vi

- Job `python -m etl wichart` với `--keys a,b` và `--dry-run` (§5.1).
- Module registry `backend/etl/wichart_registry.py` (§4.2) + nạp hai registry mỗi lượt (§4.1).
- Seed một dòng `macro.series_break` (§9.4).
- Bằng chứng thô vào `staging.raw_payload` khi hash response đổi.
- Sửa tài liệu sống theo checklist §8.

### 3.2 Ngoài phạm vi — ba loại *(§1.4)*

| Mục | Loại | Lý do |
|---|---|---|
| 20 key Tier X (`TIER_X` trong wichart.md §9, trừ `ca_tra`): 16 key VLXD (kể cả `xi_mang_pcb` trả 500) + `gdpbinhquan`, `gao_tpxk`, `thiec`, `cao_su` | **Loại có chủ đích** | Chết/đóng băng/không liên quan cổ phiếu; đo lại 2026-09-05 vẫn đúng cờ. Không tạo dòng registry (chủ dự án chốt câu 9) |
| RON 95 `xang_dau[0]`, tỷ lệ nợ/GDP `ncp[1]` | **Loại có chủ đích** | Chết 99 / 1.343 ngày. Không tạo dòng |
| OMO của SBV | **Đã có đường khác** | job `etl omo`, tắt theo [4d] |
| FRED · Frankfurter · Yahoo · LBMA · Binance | **Đã có đường khác** | lát 7, cắm vào cùng registry |
| `ops.series_health` (giám sát từng series: `days_since_change`, `gap_median`) | **Đã có đường khác** | lát 12; lát này chỉ ghi `stats` đủ để lát 12 đọc |
| Tăng trưởng tự tính, DXY dựng lại, chuỗi đã nối trong bảng | **Loại có chủ đích** | Tầng tự tính; `observation_spliced` là view đã có |
| Đăng ký task Scheduler | **Loại có chủ đích** | Lịch thuộc lát 13 |
| `asset.calendar='24x7'` cho bất kỳ chuỗi WiChart nào | **Loại có chủ đích** | Không chuỗi nào giao dịch 24/7; điểm cuối tuần là nhãn múi giờ hoặc chép lại (§2.1). Tất cả `trading_days` |

## 4. Quyết định *(§4.8 — phương án, lý do loại, điều kiện đảo ngược; chủ dự án chốt 2026-09-05)*

### 4.1 Registry nạp trong job mỗi lượt, không migration seed *(câu 1 → a)*

| Phương án | Lý do loại |
|---|---|
| **A · upsert `macro.indicator` + `indicator_source` + `asset.asset` + `asset_external_id` ở đầu mỗi lượt từ registry trong repo** ✅ | — chọn: cùng khuôn `load_dictionary` lát 5; sửa hệ số/thêm series = sửa file; idempotent |
| B · migration seed như ngành `0013` | mỗi lần hiệu chỉnh `scale` hay thêm series là một migration; ngành là quyết định của người, còn registry này là số đo nguồn + mapping kỹ thuật |

Upsert theo khoá tự nhiên: `indicator.code` / `asset.code` (UNIQUE) và `(source, external_key, external_sub)`. **Không xoá** dòng vắng mặt trong file (bảo toàn `indicator_id`/`asset_id` đã có observation trỏ tới); dòng biến mất khỏi registry ⇒ `active=false`. **Đảo ngược khi:** registry cần người duyệt từng dòng như ngành ⇒ chuyển B.

### 4.2 Mã của mình ở module backend; `scale`/cờ vẫn ở tài liệu nguồn *(câu 2 → a)*

- `docs/10-sources/macro/wichart.md` §9 (khối `WICHART`/`TIER_X`/`SRCNOTE`) giữ **sự thật đo về nguồn**: tên series, đơn vị gốc, `scale`, role, cờ, nhóm, tần suất. Chủ sở hữu duy nhất, sửa khi đo lại (§1.2).
- `backend/etl/wichart_registry.py` giữ **lựa chọn của mình**: `(key, idx) → domain, code, name_vi, freq/region/role` (macro) hoặc `asset_class, quote_currency, unit, price_type, calendar` (asset). Bảng đầy đủ ở Phụ lục A/B.
- Job đọc khối §9 bằng `exec` trên khối Python cuối cùng của file (đúng cách `verify_wichart.py` làm), ghép với module theo `(key, idx)`.
- **Test ràng buộc hai chủ:** mọi `(key, idx)` trong module phải có trong §9 với role ≠ None và tier ≠ X; mọi series §9 thu thập được phải có trong module. Lệch một dòng là test đỏ — đây là cách "hai chủ sở hữu" không trôi lệch nhau.

| Phương án bị loại | Lý do |
|---|---|
| JSON máy đọc trong `20-design/` sinh từ script | thêm một file sinh và một script sinh cho ~105 dòng; module Python đã là máy đọc và test được |
| Chép cả `scale` vào module | hai chủ cho một số đo, đúng bẫy §1.7 |

**Đảo ngược khi:** lát 7 cần cùng cấu trúc cho FRED/Yahoo và registry phình quá một module đọc được ⇒ tách theo nguồn, giữ nguyên hợp đồng `(source, external_key, external_sub)`.

### 4.3 Một job ghi hai miền *(câu 3 → a)*

Một nguồn, một vòng fetch, một `etl_run` (`job = 'macro.wichart'`), một giao dịch; `data_domain_state` hai dòng `('macro.indicator','wichart')` và `('asset','wichart')`, cùng mốc nước. Loại B (hai job): gọi nguồn hai lần, hai ngân sách cho cùng một API, và `dhtg` nằm giữa hai miền không có chỗ tự nhiên. **Đảo ngược khi:** hai miền cần lịch khác nhau (ví dụ hàng hoá 2 lần/ngày) — khi đó `--domain` là đủ, không cần job mới.

### 4.4 UPSERT trọn mỗi lượt; `raw_payload` khi hash đổi *(câu 7 → a)*

Mỗi lượt gọi đủ 68 key, chuẩn hoá, UPSERT mọi điểm theo PK (`(indicator_id, obs_date)` / `(asset_id, obs_date, price_type)`), đếm **số dòng có giá trị thật sự đổi** vào `stats.changed` (so `value` cũ trước khi ghi — đây là thước đo vá hồi tố cho giả định §2.2.2). ≤ 105 series × ≤ 730 điểm ≈ 45.000 dòng, vài giây. `staging.raw_payload` (`source='wichart'`, `endpoint_key='wichart:<key>'`, `content_type='json'`) chỉ ghi khi sha256 của body khác dòng gần nhất cùng `endpoint_key`. Loại B (ETag/`304` bỏ qua key): tiết kiệm không đáng kể, thêm trạng thái phải quản, và mất phép đếm `changed`. **Đảo ngược khi:** nguồn nâng số điểm lên hàng chục nghìn/key.

### 4.5 Điểm cuối tuần: bỏ khi chỉ là chép lại *(câu 5 → a)*

Với mọi asset `calendar='trading_days'` (tất cả — §3.2): **bỏ điểm rơi vào thứ 7/CN (ngày VN) có giá trị bằng đúng điểm liền trước; giữ điểm cuối tuần có giá khác.** Số đo §2.1 loại cả hai cực: bỏ hết cuối tuần mất 123 điểm thật của `vang_the_gioi` và ~52 của `ca_phe`; giữ hết thì `lua`/`gao`/`kem`/`niken` nhận ~170–207 dòng chép lại mỗi chuỗi. Điểm chép lại **trong tuần** giữ nguyên (là giá khảo sát thật không đổi). Áp cho `dhtg` (`fixing`/`spot`) như nhau. Không áp cho `macro` (chuỗi ngày `lsdh`/`lslnh`/`lshd` là lãi suất công bố, 1–3 điểm cuối tuần, giữ như nguồn).

**Đảo ngược khi:** một chuỗi có giá cuối tuần thật mà trùng giá thứ 6 với tần suất cao (khó phân biệt) — dấu hiệu là `days_since_change` của lát 12 nhảy đúng vào thứ 2.

### 4.6 Tên `asset.code` tiếng Anh, `indicator.code` tiền tố `vn.` *(câu 4 → b)*

Slug tiếng Anh, chữ thường, `_` trong từ, `.` cho biến thể; nguồn gốc nước ghi hậu tố `_cn`/`_tr`/`_my`/`_jp` khi tài liệu ghi rõ chuẩn là giá nước đó; tên bước 5 giữ nguyên (`wti`, `gold.intl`, `gold.sjc_buy/sell`, `fx.usd_vnd.*`). Tăng trưởng = `<code>.growth`, role `growth_ref`. Bảng đầy đủ Phụ lục A/B — chốt cùng spec vì mã là mặt API về sau.

### 4.7 Không tạo dòng cho series chết *(câu 9)*

Chủ dự án chốt: bỏ luôn, không `active=false`. Đã kiểm lại từng series (§2.1). Cột `active` giữ cho lát 12 (khi một series đang nạp chết đi thì lật `false`, không xoá).

## 5. Job `python -m etl wichart`

### 5.1 Khuôn — y `omo_job`/`fundamentals_job`

`open_run` → `load_registry` (§4.1, hợp đồng khởi động: file/khối §9 sai hình dạng ⇒ raise trước khi fetch) → fetch 68 key → normalize → **guard trước commit** → `apply` một giao dịch → `close_run` → `upsert_domain_state` hai dòng. Guard từ chối ⇒ raise trong `engine.begin()` để rollback, bằng chứng ở giao dịch riêng, `failed`, exit 1.

| Cờ | Nghĩa |
|---|---|
| `--keys a,b` | tập ép; **không** đụng mốc nước/domain_state, **không** guard tỷ lệ (lượt con nhỏ hơn `MIN_SAMPLE`), đọc `stats` bằng mắt (bài học 1c lát 4) |
| `--dry-run` | fetch + normalize + guard, **không ghi** (kể cả registry, raw_payload), in `stats` |

Không `--backfill`, không `--max-minutes`: lượt đầu đã nạp trọn cửa sổ 2 năm (chuỗi ngày) và toàn lịch sử (tháng/quý/năm); 68 lời gọi ≈ 1 phút.

### 5.2 `wichart_fetch` — I/O thuần

- URL theo `g`: `?name={key}` (vi_mo) / `?key=hang_hoa&name={key}`. Header `Accept-Encoding: gzip`, `User-Agent` mặc định của httpx; không cần `Origin`.
- Timeout 30 s, retry 3, backoff 2/4/8, exception vận chuyển đi cùng đường với response xấu (bài học `e7f80f6`). Không giãn cách bắt buộc (đo 90 lời gọi liên tiếp sạch) nhưng giữ `MIN_INTERVAL = 0.2` s cho lịch sự.
- `classify(key, http, text) → ('ok', doc) | ('retry', None) | ('bad_shape', None)`: `ok` khi HTTP 200, JSON hợp lệ, có `chart.series` là list; `retry` khi HTTP ≠ 200 / JSON hỏng / exception; `bad_shape` khi thiếu `chart.series`.
- Hết lượt thử ⇒ key đó `failed`, không ghi gì cho key đó, đếm.

### 5.3 `wichart_normalize` — thuần

```
Point(domain, code, obs_date, value, price_type)

series_points(key, idx, spec_doc, spec_ours, api_series) -> list[Point], reason | None
  1. api_series[idx] phải tồn tại và tên khớp tiền tố 18 ký tự (trừ cờ NAMEWRONG)  -> else 'shape'
  2. value = raw * scale (Decimal), bỏ điểm raw None / không phải số
  3. obs_date = fromtimestamp(epoch/1000, tz=Asia/Ho_Chi_Minh).date(), rồi neo kỳ:
        freq m -> replace(day=1)             (WiChart đã là ngày 1)
        freq q -> tháng PHẢI ∈ {3,6,9,12} (neo tháng cuối quý, đo B2b) -> tháng đầu quý, ngày 1
                  (03 -> 01, 06 -> 04, 09 -> 07, 12 -> 10); tháng khác -> lỗi 'shape' (nguồn đổi cách neo)
        freq y -> 01-01 cùng năm             (ds/ncp neo 12-31 -> 01-01 của NĂM ĐÓ)
        freq d -> giữ nguyên
     freq lấy từ trung vị khoảng cách điểm (không tin timeArray) và phải KHỚP freq khai ở §9 -> else 'freq'
  4. dải đơn vị: |value| nằm trong BANDS[unit] (Phụ lục C) với điểm MỚI NHẤT -> else 'band'
  5. asset trading_days: bỏ điểm T7/CN có value == điểm liền trước (§4.5)
```

`shape`/`freq`/`band` làm series đó bị **bỏ khỏi lượt ghi** (không ghi một phần), đếm vào `tally`; các series khác của cùng key vẫn ghi.

### 5.4 `wichart_guard` — thuần, trước commit

| Chốt | Ngưỡng | Bắt |
|---|---|---|
| (i) key hỏng (`failed`) | > 20 % số key, `MIN_SAMPLE 20` | nguồn sự cố |
| (ii) key sai hình dạng (`bad_shape` + series `shape`) | > 5 % số series | nguồn đổi cấu trúc / đổi thứ tự series |
| (iii) series ngoài dải đơn vị (`band`) | > 5 % số series | nguồn đổi thang (lỗi 1000× mới) |
| (iv) series lệch tần suất (`freq`) | chỉ ghi `stats`, không từ chối | 16 key vốn khai sai; ta so với freq **thật** đã đo nên lệch là hiếm |
| (v) 0 key hỏng, 0 series lỗi, `changed = 0` | **không phải lỗi** — `success` | ngày nguồn chưa nạp |

Một series `band` lẻ (ví dụ vàng đột biến) không từ chối cả lượt nhưng **không ghi series đó** và xuất hiện trong `stats.tally.band` — người trực đọc rồi chạy `--keys` sau khi soi.

### 5.5 `wichart_store`

- `load_registry(conn)`: đọc khối §9 + module, upsert 4 bảng, trả `dict[(key, idx)] -> (domain, id, price_type, calendar)`; `active=false` cho dòng có trong DB mà vắng registry.
- `apply(conn, points)`: `INSERT … ON CONFLICT (pk) DO UPDATE SET value = EXCLUDED.value, ingested_at = clock_timestamp() WHERE t.value IS DISTINCT FROM EXCLUDED.value` — dòng không đổi **không được chạm** (`ingested_at` = lúc giá trị hiện tại về, đúng nghĩa bước 4); `changed` = rowcount của câu lệnh trừ số dòng chèn mới (`inserted` đếm qua `RETURNING (xmax = 0)`). Test pin: chạy lại ⇒ rowcount 0.
- `series_break` seed: upsert một dòng `(vn.gdp.real, 2026-03-01, 1.6005, 'Đổi năm gốc giá so sánh; trung bình hai ước lượng độc lập 1.6032 / 1.5978 (wichart.md Bẫy 6)', verified_by NULL, verified_at 2026-09-05)` — §9.4.
- Bằng chứng: `raw_payload` khi hash đổi (§4.4); khi guard từ chối: mọi body của lượt vào `raw_payload` với `meta.refused = reasons` trong giao dịch riêng (y lát 1–5).
- Mốc nước `data_domain_state.watermark` = ngày VN của lượt (`max(obs_date)` không có nghĩa khi tần suất trộn).

### 5.6 Lịch và vận hành

Không đăng ký task. Chạy tay: `uv run python -m etl wichart`. Vị trí gợi ý cho bảng lịch lát 13: **08:15 giờ VN**, sau khi đo giờ nạp thật (giả định §2.2.1); tần suất hằng ngày kể cả cuối tuần (chuỗi ngày có điểm T7/CN thật).

## 6. Seam test *(chốt cùng plan — §4.5.2)*

Expected từ mẫu thật lưu trong `samples/` (chụp 2026-09-05: `cpi`, `gdp`, `vang`, `xang_dau`, `vai_cotton_my`, `lua`, `dhtg`, `ds`) hoặc giải tay, không tính lại theo cách code tính.

| Seam | Ca phải có |
|---|---|
| `classify` | 200 + series → ok · 500 → retry · JSON hỏng → retry · thiếu `chart.series` → bad_shape · exception → retry |
| `series_points` neo kỳ | epoch `1782838800000` (mẫu `cpi` tháng 07/2026) ⇒ `2026-07-01`; parse UTC ⇒ `06-30` phải đỏ · `gdp` quý neo `2026-06-01` ⇒ `2026-04-01` · `ds` năm neo `2025-12-01`/`12-31` ⇒ `2025-01-01` |
| `series_points` đơn vị | `vang[0]` raw `141300` × 1e3 ⇒ `141300000` VND/lượng · `gdp[0]` raw × 1e9 · `vai_cotton_my` raw `82.33` × 0.01 ⇒ `0.8233` USD/lb · `gdp[2]` (growth_ref) raw `0.08` × 100 ⇒ `8` |
| `series_points` cuối tuần | mẫu `lua`: T7 giá bằng T6 ⇒ bỏ; mẫu `vang_the_gioi`: T7 giá khác ⇒ giữ; điểm chép lại **trong tuần** giữ |
| `series_points` lỗi | tên series lệch ⇒ `shape` · `xang_dau` chỉ 3 series được map (idx 1–3), idx 0 không có trong module ⇒ không ghi · freq thật `m` mà §9 khai `d` ⇒ `freq` · giá sau scale ngoài dải ⇒ `band` |
| `td` map theo key | mẫu `td` (nhãn "Tổng tiền gửi") ⇒ `vn.credit`, không phải `vn.deposits` |
| registry ↔ §9 | mọi `(key, idx)` module ⊂ §9 thu thập; mọi series §9 thu thập ⊂ module; 105 series đúng số; `xang_dau[0]`, `ncp[1]`, 20 key Tier X **không** có trong module |
| `guard.check` | qua · (i)–(iii) đỏ · `changed = 0` vẫn ok · `MIN_SAMPLE` biên 19/20 |
| `load_registry` | 53 indicator + 53 indicator_source; 52 asset + 52 external_id; chạy hai lần ⇒ số không đổi, `indicator_id` không đổi; xoá một dòng khỏi module ⇒ `active=false`, không mất dòng |
| `apply` | first ⇒ `inserted = n`; chạy lại ⇒ `inserted = changed = 0`, `ingested_at` không đổi; đổi một giá trị ⇒ `changed = 1`, số dòng không đổi, `ingested_at` của đúng dòng đó tiến; `raw_payload` chỉ tăng khi hash đổi |
| `series_break` | view `observation_spliced` cho `vn.gdp.real` trước `2026-03-01` = gốc × 1,6005 (literal), sau giữ nguyên |
| quyền | `test_wichart_works_under_etl_role`: `SET LOCAL ROLE dlck_etl` đi qua upsert 4 bảng registry + observation + price_daily + series_break + raw_payload |

Mọi ngày trong test lấy từ mẫu cố định hoặc `date.today()`/ngày VN, không hardcode cạnh `now()` (bài học lát 5).

## 7. Tiêu chí nghiệm thu

| | Nội dung | Bằng chứng phải dán |
|---|---|---|
| AC1 | Toàn bộ test xanh | số test trước (596 + 2 skipped) / sau |
| AC2 | `--dry-run` trên nguồn sống: 68/68 key ok, `tally` 0 `shape`/`band`, freq lệch = 0 | `stats` |
| AC3 | Lượt đầu vào kho production (`ETL_DATABASE_URL`, role `dlck_etl`): registry 53 + 52; `macro.observation` và `asset.price_daily` có dòng cho **mọi** series đang nạp; `cpi` mới nhất = `titleIndex` của API cùng ngày; `vang` mới nhất ≈ 1,4 × 10⁸ VND/lượng; `vai_cotton_my` ≈ 0,8 USD/lb; `gdp` quý gần nhất neo ngày 1 tháng đầu quý | truy vấn đếm theo series + 4 literal đối chiếu tay với API |
| AC4 | Lượt hai cùng ngày | `changed = 0`, `inserted = 0`, `raw_payload` không tăng, `max(ingested_at)` **không** đổi |
| AC5 | Điểm cuối tuần: `lua` không có dòng T7/CN trùng giá T6; `vang_the_gioi` có dòng T7 với giá khác T6 | hai truy vấn đếm |
| AC6 | Ép hỏng: `get` giả trả 500 cho 20 key ⇒ `failed`, 0 dòng ghi, bằng chứng `raw_payload.meta.refused` | `etl_run` + `raw_payload` |
| AC7 | `observation_spliced` của `vn.gdp.real` trước 03/2026 = published × 1,6005 | truy vấn 2 kỳ |
| AC8 | Mọi lượt trên chạy dưới credential production trước khi coi là xong | dòng lệnh + exit code |

## 8. Checklist tài liệu sống — cùng lượt với code *(§1.6, §1.7)*

- [ ] [roadmap.md](../../../00-overview/roadmap.md): lát 6 ✅ + **"Điểm vào cho lát 7"** (quốc tế: cắm FRED/Yahoo/LBMA/Binance/Frankfurter vào cùng registry; ghi giờ nạp WiChart nếu đo được); số test; §0 dòng vĩ mô.
- [ ] [wichart.md](../../../10-sources/macro/wichart.md): `ca_tra` tier X → A (nếu §9.1 duyệt), §10 mức tải đã kiểm (68 lời gọi liên tiếp, đo 2026-09-05).
- [ ] [00-conventions.md §10](../../../10-sources/market/00-conventions.md): không đụng (WiChart không phải FiinTrade) — chỉ kiểm không có gì đá nhau.
- [ ] [market-data-store.md](../../../20-design/market-data-store.md): một dòng ở §4/§8 ghi vĩ mô/hàng hoá đã có job.
- [ ] [backend/README.md](../../../../backend/README.md): mục "Chạy job wichart", hai cờ, luật cuối tuần, cách đọc `tally.band`.
- [ ] [database/README.md](../../../../database/README.md): số test schema nếu thêm test role.
- [ ] [90-records/README.md](../../README.md): dòng plan này.
- [ ] `ledger.md` cùng thư mục, commit theo mốc.

## 9. Điểm cần chủ dự án duyệt tường minh

1. **`ca_tra` sống lại → thu thập, Tier A**, mã `pangasius` (VHC · ANV · IDI). Đo 2026-09-05: giá đổi 22/08 sau 60 ngày đóng băng lúc audit. Nếu không duyệt thì giữ Tier X.
2. **`vai_cotton_my` nạp với đơn vị USD/lb, `scale = 0.01`** (raw là US cent/lb, đã kiểm với ICE `CT=F`); `quote_currency='USD'`. Phương án khác: giữ cent, `quote_currency='USX'` — loại vì kho không lưu đơn vị con (luật "không nghìn/tỷ").
3. **Tất cả asset WiChart `calendar='trading_days'`** — không chuỗi nào 24/7; điểm cuối tuần xử lý theo §4.5.
4. **Seed `series_break` GDP giá so sánh**: `factor 1.6005`, `break_date 2026-03-01`, `verified_by NULL`, `verified_at = 2026-09-05` (chủ dự án chốt "không cần by, ghi ngày").
5. **Bảng mã Phụ lục A/B** — đây là mặt API về sau; đổi sau này tốn một migration đổi tên + sửa tầng ngữ nghĩa.
6. **`--keys` không guard, không đụng mốc nước** — như lát 4/5.

---

## Phụ lục A — `asset` (52 series)

Cột: WiChart `(key, idx)` → `asset.code` · `asset_class` · `quote_currency` · `unit` · `price_type`. `scale` lấy từ §9, không chép. `calendar='trading_days'` toàn bộ, `region` = `'vn'` cho giá trong nước, `'cn'`/`'global'`/… theo chuẩn.

| key[idx] | code | class | ccy | unit | price_type |
|---|---|---|---|---|---|
| dhtg[0] | fx.usd_vnd.central | fx | VND | VND/1 USD | fixing |
| dhtg[1] | fx.usd_vnd.ceiling | fx | VND | VND/1 USD | fixing |
| dhtg[2] | fx.usd_vnd.floor | fx | VND | VND/1 USD | fixing |
| dhtg[3] | fx.usd_vnd.bank_sell | fx | VND | VND/1 USD | spot |
| dhtg[4] | fx.usd_vnd.free_sell | fx | VND | VND/1 USD | spot |
| heo_hoi | hog_live | commodity | VND | VND/kg | spot |
| ca_phe | coffee_robusta_vn | commodity | VND | VND/kg | spot |
| tieu | pepper_vn | commodity | VND | VND/kg | spot |
| duong | sugar | commodity | USD | USD/tấn | spot |
| dau_co_malaysia | palm_oil_my | commodity | MYR | MYR/tấn | spot |
| soi_coton | cotton_yarn_cn | commodity | CNY | CNY/tấn | spot |
| lua | paddy_vn | commodity | VND | VND/kg | spot |
| gao_nguyen_lieu | rice_raw_vn | commodity | VND | VND/kg | spot |
| phu_pham_lua_gao | rice_byproduct_vn | commodity | VND | VND/kg | spot |
| tom_the | shrimp_whiteleg_vn | commodity | VND | VND/kg | spot |
| vai_cotton_my | cotton_us | commodity | USD | USD/lb | spot |
| ca_tra *(§9.1)* | pangasius_vn | commodity | VND | VND/kg | spot |
| quang_sat | iron_ore_cn | commodity | CNY | CNY/tấn | spot |
| vang[0] | gold.sjc_buy | commodity | VND | VND/lượng | spot |
| vang[1] | gold.sjc_sell | commodity | VND | VND/lượng | spot |
| vang_the_gioi | gold.intl | commodity | USD | USD/oz | spot |
| chi | lead_cn | commodity | CNY | CNY/tấn | spot |
| kem | zinc_cn | commodity | CNY | CNY/tấn | spot |
| nhom | aluminum_cn | commodity | CNY | CNY/tấn | spot |
| niken | nickel_cn | commodity | CNY | CNY/tấn | spot |
| dong | copper | commodity | USD | USD/lb | spot |
| bac | silver | commodity | USD | USD/oz | spot |
| dau_wti | wti | commodity | USD | USD/thùng | **futures** |
| khi_thien_nhien | natgas_hh | commodity | USD | USD/MMBtu | spot |
| than_newcastle | coal_newcastle | commodity | USD | USD/tấn | spot |
| than_coc | coke_cn | commodity | CNY | CNY/tấn | spot |
| khi_lpg_trung_quoc | lpg_cn | commodity | CNY | CNY/tấn | spot |
| xang_dau[1] | gasoline_e5_vn | commodity | VND | VND/lít | spot |
| xang_dau[2] | diesel_vn | commodity | VND | VND/lít | spot |
| xang_dau[3] | kerosene_vn | commodity | VND | VND/lít | spot |
| ure_trung_dong | urea_me | commodity | USD | USD/tấn | spot |
| phan_ure[0] | urea_phumy | commodity | VND | VND/kg | spot |
| phan_ure[1] | urea_camau | commodity | VND | VND/kg | spot |
| phan_urea_trung_quoc | urea_cn | commodity | CNY | CNY/tấn | spot |
| luu_huynh | sulfur_cn | commodity | CNY | CNY/tấn | spot |
| phot_pho | phosphorus_cn | commodity | CNY | CNY/tấn | spot |
| nhua_pvc_trung_quoc | pvc_cn | commodity | CNY | CNY/tấn | spot |
| nhua_pp_trung_quoc | pp_cn | commodity | CNY | CNY/tấn | spot |
| pet_trung_quoc | pet_cn | commodity | CNY | CNY/tấn | spot |
| cao_su_nhat_ban | rubber_rss3_jp | commodity | JPY | JPY/kg | spot |
| hrc_trung_quoc | hrc_cn | commodity | CNY | CNY/tấn | spot |
| thep_phe_anh | scrap_steel_tr | commodity | USD | USD/tấn | spot |
| thep_thanh_anh | rebar_tr | commodity | USD | USD/tấn | spot |
| ton_lanh_hoa_sen_045mm | galv_sheet_hoasen | commodity | VND | VND/m2 | spot |
| ton_lanh_mau_hoa_sen_045mm | galv_sheet_color_hoasen | commodity | VND | VND/m2 | spot |
| giay_gon_song_trung_quoc | corrugated_paper_cn | commodity | CNY | CNY/tấn | spot |
| vai_coton | cotton_fabric_cn | commodity | CNY | CNY/tấn | spot |

*`dau_wti` là futures theo cờ `SRCNOTE` (không trộn với `wti` spot của FRED ở lát 7). `dong` đơn vị `USD/pound` của §9 ghi thành `USD/lb` ở kho — cùng đơn vị, một cách viết.*

## Phụ lục B — `macro` (53 series, `region='vn'`)

`role` và `scale` lấy từ §9. Tăng trưởng = `<code>.growth`, role `growth_ref`, unit `%`.

| key[idx] | code | name_vi | unit | freq |
|---|---|---|---|---|
| gdp[0] | vn.gdp.nominal | GDP giá hiện hành | VND | q |
| gdp[1] | vn.gdp.real | GDP giá so sánh | VND | q |
| gdp[2] | vn.gdp.growth | Tăng trưởng GDP | % | q |
| cpi | vn.cpi | CPI (YoY) | % | m |
| iip | vn.iip | Sản xuất công nghiệp (YoY) — LOWRES, ngoại lệ đã chấp nhận, role `data` | % | m |
| pmi | vn.pmi | PMI | điểm | m |
| hhdv[0] / [1] | vn.retail / vn.retail.growth | Tổng mức bán lẻ HH&DV | VND | m |
| fdi[0] / [1] / [2] / [3] | vn.fdi.registered / vn.fdi.realized / vn.fdi.realized.growth / vn.fdi.registered.growth | FDI | USD | m |
| cctm[0] / [1] / [2] | vn.export / vn.import / vn.trade_balance | Xuất · nhập · cán cân | USD | m |
| cctt[0..3] | vn.bop.overall / vn.bop.current / vn.bop.financial / vn.bop.errors | Cán cân thanh toán | USD | q |
| vdtptxh[0] / [1] | vn.investment.social / .growth | Vốn ĐT phát triển XH | VND | q |
| vdtnsnn[0] / [1] | vn.investment.budget / .growth | Vốn ĐT từ NSNN (freq thật `m`) | VND | m |
| vt[0] / [1] | vn.transport.passengers / vn.transport.freight | Vận tải | lượt người / tấn | m |
| kqt[0] / [1] | vn.tourists / vn.tourists.growth | Khách quốc tế | người | m |
| ds[0] / [1] | vn.population / vn.population.growth | Dân số | người | y |
| tn | vn.unemployment | Tỷ lệ thất nghiệp | % | q |
| ld[0] / [1] | vn.labor_force / .growth | Lực lượng lao động | người | q |
| tcns[0] / [1] / [2] | vn.budget.revenue / vn.budget.expenditure / vn.budget.deficit | Ngân sách | VND | q |
| ncp[0] / [2] | vn.gov_debt / vn.gov_debt.growth | Nợ chính phủ *(idx 1 chết, bỏ)* | VND | y |
| ctt[0] / [1] | vn.m2 / vn.m2.growth | Cung tiền | VND | m |
| hd[0] / [1] | vn.deposits / vn.deposits.growth | Tổng tiền gửi | VND | m |
| td[0] / [1] | vn.credit / vn.credit.growth | Tổng tín dụng *(nhãn nguồn sai)* | VND | m |
| dtnh | vn.fx_reserves | Dự trữ ngoại hối | USD | m |
| lsdh[0..2] | vn.rate.discount / vn.rate.refinancing / vn.rate.overnight_lending | Lãi suất điều hành | % | d |
| lslnh[0..2] | vn.rate.interbank.on / .1w / .2w | Lãi suất liên ngân hàng | % | d |
| lshd[0..2] | vn.rate.deposit.1_3m / .6_9m / .13m | Lãi suất huy động tại quầy (SRCNOTE) | % | d |

Đếm: 24 key, 40 `data` + 13 `growth_ref` = 53 ✓.

## Phụ lục C — dải đơn vị cho chốt (iii)

Chủ sở hữu: `backend/etl/wichart_registry.py` (`BANDS`), khởi tạo từ bảng cùng tên trong `verify_wichart.py` và thêm `USD/lb (0.1, 20)`, `VND/1 USD (1e4, 1e5)`, `USD/oz (1, 1e4)`, `USD/thùng (5, 500)`. Áp trên **điểm mới nhất sau scale**. Hai bản (script tài liệu và module) phục vụ hai tầng khác nhau, test không ràng buộc chéo; nếu về sau cần một chủ thì script đọc module.
