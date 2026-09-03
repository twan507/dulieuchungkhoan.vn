# Spec — `etl price`: lát 3 của [7] ETL REST hằng ngày

**Ngày:** 2026-09-03 · **Trạng thái:** thực thi theo chỉ thị chủ dự án *"làm liên tục, chỉ dừng khi có quyết định khó"* — các điểm cần duyệt tường minh gom ở §9 để rà lại · **Lát trước:** [`etl events`](../2026-09-03-events-daily-etl/spec.md) ✅ xong cùng ngày

---

## 1. Vì sao lát này, và lát này là gì

Giá theo ngày là **chuỗi dữ liệu nền** của mọi thứ phía sau: chỉ báo kỹ thuật, hệ số điều chỉnh cho nến intraday (`market.price_factor`), và re-crawl theo sự kiện quyền mà lát 2 đã đặt tín hiệu (`corporate_event.exright_date`, 30 dòng đang ở phía trước). Đây là họ lớn nhất trong lịch ngày: **1.523 lời gọi/ngày** *(không phải 1.974 — số cũ đếm trước lượt dọn 442 mã huỷ niêm yết, [measurements §8](measurements.md))*.

**Lát này là:** job `python -m etl price` có hai chế độ dùng chung một đường code:

| Chế độ | Làm gì | Giao dịch |
|---|---|---|
| hằng ngày *(mặc định)* | trang 1 (60 phiên) của **mọi cổ phiếu `listed`** → `market.price_daily` | **một** giao dịch, guard TRƯỚC commit |
| `--backfill` | mọi trang tới hết lịch sử (~12,5 năm), **tiếp tục được** qua nhiều lượt bằng con trỏ, có ngân sách `--max-minutes` | mỗi mã một giao dịch |

Cộng `--codes T1,T2` để giới hạn tập mã ở cả hai chế độ — vừa là cách chạy thử dưới quyền production với vài mã (§3.5), vừa là đường mà cơ chế re-crawl theo `exright_date` của lát 4 sẽ gọi.

**Lát này KHÔNG phải:** không dựng trigger re-crawl (lát 4), không ghi giá thô từ BVSC EOD (`/datafeed/instruments`), không lấy ETF/chỉ số/phái sinh (§3.2).

## 2. Dữ kiện đã đo vs giả định *(§4.8 bước 0 — bắt buộc)*

### 2.1 Đã đo — 18 lời gọi thật + 2 nguồn đối chứng, 2026-09-03

Hồ sơ đầy đủ: [`measurements.md`](measurements.md) · bằng chứng: [`samples/`](samples/). Bảy điều quyết định thiết kế:

1. 🔴 **`closePrice` là giá THÔ lịch sử, `closeValue` là giá đã điều chỉnh** — kiểm bằng cổ tức của lát 2 (DMX: hệ số 0,9548 = (88.500 − 4.000)/88.500, đúng 4 chữ số) và tick BVSC trong ClickHouse (10/10 khớp). Tài liệu và thiết kế cũ nói *"quá khứ không có giá thô ở nguồn nào"* — **sai**.
2. 🔴 **`status` trả lẫn `0` và `"Success"`** trên cùng endpoint (2/16 lời gọi) — kiểm `== "Success"` như lát 1–2 sẽ thử lại vô ích ~1/8 lời gọi.
3. **Mã sai trả `Failed / "Code not valid: X"`**, không phải `items` rỗng — lỗi có tên, phân biệt được với lỗi tạm thời.
4. **`FromDate`/`ToDate` bị bỏ qua** — trang 1 là đơn vị nhỏ nhất.
5. **`totalCount` chính xác** (3.142 = 52 × 60 + 22), trang cuối ngắn, trang sau rỗng với `status: Success`, các trang **liền nhau không chồng**.
6. **Ngày nghỉ không có dòng** — không cần vế guard "có phiên không" như Screener.
7. **Dòng tiền theo nhà đầu tư điền trễ T+1** (HOSE); HNX/UPCOM luôn null. Trang 1 = 60 phiên nên hôm sau tự ghi đè bản hôm qua đã điền đủ.

Kèm: latency trung vị 1,76 s · 200 KB/trang · `organCode` số (`5702162138`) chạy bình thường · 41% mã có `organCode ≠ ticker`, 100% tra được qua `issuer_external_id('fiintrade')`.

### 2.2 Giả định — CHƯA kiểm, ghi để người sau biết mình đứng trên gì

| Giả định | Hỏng thì sao | Vì sao chấp nhận |
|---|---|---|
| Nhịp tuần tự **kéo dài 45 phút** (1.523 lời gọi) không bị chặn | Lượt hằng ngày dừng giữa chừng, không ghi gì | Nhịp thấp hơn burst Screener đã đo (~17 so với ~29 request/phút); lượt chạy thật đầu tiên là phép đo đúng tải kế hoạch (§4.3) |
| Trang 1 lúc **15:40** đã có OHLCV của phiên vừa đóng | Bản ghi hôm nay thiếu tới lượt hôm sau | Chỉ trễ 1 ngày, không mất; đo lúc 22:00 đã đủ; Screener 15:20 đã thấy giá 100% |
| Nguồn không **sửa hồi tố `closePrice`** | `close_raw` điền một lần giữ giá sai | Bộ đếm `raw_close_mismatch` mỗi lượt (§5.5) lộ ngay ca này; sửa bằng một câu UPDATE có người nhìn |
| Một `organCode` → đúng một cổ phiếu `listed` | Hai security cùng nhận một chuỗi | Đo 2026-09-03: 0 issuer có > 1 security listed; `list_codes` đếm `dup_issuer` và từ chối nếu > 0 |

## 3. Phạm vi

### 3.1 Trong phạm vi

Job hai chế độ + `--codes`; điền **5 cột** (`close_adj` · `close_raw` · `open_value` · `highest_value` · `lowest_value`) + `raw.fiintrade`; guard; con trỏ backfill; task `dlck-price`; cập nhật tài liệu sống (§8).

### 3.2 Ngoài phạm vi — phân ba loại *(§1.4)*

| Mục | Loại | Lý do |
|---|---|---|
| **ETF** (31 mã, chỉ 6 có dữ liệu, gọi theo ticker) | **Đã có đường khác** | Giá ETF đã có realtime BVSC; giá trị riêng của endpoint là `iNav` cho **2 quỹ** thanh khoản — thêm khi thiết kế chỉ báo dòng tiền ETF, chỉ cần nhánh `security_type='etf'` dùng ticker làm `Code` |
| **Chỉ số** (18) | **Đã có đường khác** | Không có `organCode`; nguồn EOD chỉ số là TVC/`getIndexSnapshots`, tự tích luỹ từ ngày vận hành (step-03 §1) |
| **Phái sinh `VN30F*`** (nguồn chuẩn `openInterest`) | **Đã có đường khác** | Danh mục mã chưa có phái sinh — quyết định phạm vi riêng của lát mở rộng danh mục ([roadmap §2](../../../00-overview/roadmap.md)) |
| **Writer `close_raw` từ BVSC EOD** `/datafeed/instruments` | **Đã có đường khác** | Số đo §2.1.1: `closePrice` đã cho giá thô **toàn bộ lịch sử**; writer EOD nay chỉ còn vai trò đối chứng, không còn là nguồn duy nhất |
| Mở cột cho 90+ trường còn lại (dòng tiền theo NĐT, thoả thuận…) | **Loại có chủ đích** *(tạm)* | Xem quyết định 3 ở §4.3 — `raw` giữ nguyên 99 trường nên mở cột sau **không phải crawl lại** |
| Cơ chế trigger re-crawl theo `exright_date` | **Đã có đường khác** | Lát 4; lát này chỉ để sẵn `--backfill --codes` |
| `core/http` + token bucket dùng chung ETL/chatbot | **Loại có chủ đích** *(tạm)* | Xem quyết định 1 ở §4.1 — chưa có người dùng thứ hai |

## 4. Ba quyết định theo §4.8 — phương án, lý do loại, điều kiện đảo ngược

### 4.1 Nhịp gọi — tuần tự, không 8 luồng

| Phương án | Trục tối ưu | Rủi ro tự khai |
|---|---|---|
| **A · Tuần tự + giãn cách tối thiểu 0,5 s trong `price_fetch`** *(chọn)* | scope-YAGNI, bán kính hỏng nhỏ | Backfill chậm: 25–40 giờ tuần tự |
| B · `core/http` token bucket theo host + 8 luồng | tốc độ | Nhịp 8 luồng **chưa ai đo** ([§10.6](../../../10-sources/market/00-conventions.md)); phải đo trước, và dựng hạ tầng cho người dùng thứ hai (chatbot) chưa tồn tại |
| C · `httpx.AsyncClient` + semaphore | tốc độ, ít thread | Cùng rủi ro nhịp như B; đổi mô hình đồng bộ của cả 4 job hiện có |

**Loại B, C** vì cùng đòi phép đo chưa có, trong khi **nhu cầu đã biến mất**: ngân sách ngày là 45 phút tuần tự (không phải 20–30 phút cho 6.000 lời gọi như bản 2026-08-14), và backfill rải vài đêm là đúng ý *"rải 1–2 tuần"* của [market-data-store §4.2](../../../20-design/market-data-store.md). Nhịp tuần tự là **mức đã kiểm** — dùng được ngay.

**Đảo ngược khi:** (a) `api` bắt đầu gọi FiinTrade — lúc đó mới cần ngân sách dùng chung, tách `core/http`; hoặc (b) backfill thật đo được > 60 giờ.

### 4.2 `close_raw` — điền một lần từ `closePrice`, không đè

| Phương án | Trục | Rủi ro |
|---|---|---|
| **A · `close_raw = coalesce(cũ, closePrice)`** *(chọn)* | đúng luật lược đồ *"không bao giờ sửa"* | Nguồn sửa hồi tố thì kho giữ giá cũ — có bộ đếm lộ |
| B · Giữ NULL như thiết kế, chờ writer BVSC EOD | tôn trọng thiết kế cũ | Bỏ phí dữ liệu **đã kiểm 3 cách**; `price_factor` NULL suốt 12 năm; phải dựng thêm một writer |
| C · Đè mỗi lượt | theo nguồn | Vi phạm chú thích lược đồ; writer EOD tương lai và writer này giành nhau một cột |

**Đảo ngược khi:** `raw_close_mismatch > 0` liên tiếp nhiều lượt trên cùng mã ⇒ nguồn có sửa hồi tố thật, xét lại luật điền-một-lần.

### 4.3 Cột — 5 cột + `raw`, không migration

| Phương án | Trục | Rủi ro |
|---|---|---|
| **A · 5 cột đích danh + `raw.fiintrade` giữ nguyên 99 trường** *(chọn)* | scope-YAGNI, dễ rollback | Truy vấn dòng tiền theo NĐT phải đọc jsonb |
| B · Migration `0016` thêm ~40 cột dòng tiền/thoả thuận/khối ngoại | tiện truy vấn | [`market-field-selection.md`](../../../20-design/market-field-selection.md) **chưa có mục cho endpoint này** — chọn cột lúc này là chọn không có bảng tường minh; và 34 cột BVSC hiện có đã là nền giá thô, dễ trộn nền |
| C · Chỉ `raw`, không điền cột nào | tối giản nhất | Lược đồ đã dành đích danh 5 cột cho endpoint này; `price_factor` không có gì để tính |

**Đảo ngược khi:** có tiêu thụ thật cần cột (chatbot/api) ⇒ mở mục getPriceData trong bảng chọn trường, migration thêm cột, **điền từ `raw` bằng một UPDATE** — không crawl lại.

## 5. Job `python -m etl price`

### 5.1 Khuôn — y `events_job.run`, không sáng tạo

```
list_codes → fetch → normalize → guard (TRƯỚC commit) → apply → close_run
```

Năm module: `price_fetch` · `price_normalize` · `price_guard` · `price_store` · `price_job`. CLI thêm nhánh `price` vào `etl/__main__.py` với `--backfill`, `--codes`, `--max-minutes`.

Sổ chạy: hai tên job trong `ops.etl_run` — **`market.price_daily`** và **`market.price_backfill`** — để mốc (baseline) của lượt hằng ngày không lẫn lượt backfill. Công tắc miền: `ops.data_domain_state('market.price', 'fiintrade')`, chỉ lượt hằng ngày cập nhật, `watermark = latest_trading_date`.

### 5.2 `price_fetch` — I/O thuần

| Mục | Giá trị | Nguồn |
|---|---|---|
| URL | `FIIN_TECH/PriceData/GetPriceData?Code={organCode}&Frequently=Daily&Page={n}&PageSize=60&language=vi` | [09](../../../10-sources/market/09-fiin-market-price.md) |
| Header | `Origin: https://fiinapp.bvsc.com.vn` | 00-conventions §2 |
| Hợp lệ | HTTP 200 · JSON · **`status ∈ {0, "Success"}`** · `items` là list | §2.1.2 |
| Mã sai | `status == "Failed"` và `errors` chứa `"Code not valid"` ⇒ **`CodeInvalid`, không thử lại** | §2.1.3 |
| Retry | 3 lần, backoff 2·4·8 s cho mọi lỗi khác; hết ⇒ `FetchError` cho mã đó | khuôn lát 2 |
| Dừng trang | trang trả **< 60** bản ghi là trang cuối; trần `ceil(totalCount/60)` phòng hờ | §2.1.5 |
| Giãn cách | **≥ 0,5 s giữa hai lời gọi** (trần 2 request/giây của thiết kế) — với latency ~1,8 s hầu như không phải ngủ | market-data-store §4.2 |
| Timeout | 60 s | 200 KB/trang, 3 s |
| Ngắt khẩn | **10 mã liên tiếp `FetchError`** ⇒ ngắt cả lượt (nguồn/mạng chết, không phải mã lẻ hỏng) | mới |

Một `httpx.Client` cho trọn lượt. Đối tượng `Fetcher(get, sleep, clock)` giữ trạng thái giãn cách + bộ đếm `retries`; test tiêm cả ba.

### 5.3 `price_normalize` — thuần, không I/O

`PriceRow(organ_code, trading_date, close_adj, close_raw, open_value, highest_value, lowest_value, payload)`:

| Cột | Trường nguồn | Ghi chú |
|---|---|---|
| `trading_date` | `tradingDate[:10]` | `"2026-09-03T00:00:00"` → `date(2026, 9, 3)` |
| `close_adj` | `closeValue` | đã điều chỉnh |
| `close_raw` | **`closePrice`** | thô — §2.1.1 |
| `open_value` · `highest_value` · `lowest_value` | `openValue` · `highestValue` · `lowestValue` | nền đã điều chỉnh |
| `payload` | **nguyên bản ghi 99 trường** | vào `raw.fiintrade.payload` |

Số → `Decimal(str(v))` (giữ đúng chữ số nguồn, không qua float8), `null` → `None`. **Gộp trong một mã:** hai trang chồng ngày (mã mới lên sàn giữa hai lời gọi) thì giữ bản **thấy trước** (trang mới hơn), đếm `dup_dates`. `summarize(texts)` trả `(n_rows, latest_date)` mà không giữ bản ghi — lượt hằng ngày dùng nó để guard **trước** khi parse đầy đủ (giữ 1.523 trang thô ~300 MB thay vì 91.000 dict).

### 5.4 `price_guard` — thuần, đánh giá trước commit *(chỉ chế độ hằng ngày)*

| # | Vế | Ngưỡng | Vùng dữ liệu thật |
|---|---|---|---|
| (0) | không mã nào có dữ liệu | — | nguồn chết |
| (i) | `invalid + failed` / tổng mã | > **2%** (~30 mã) | dự kiến 0 — mã mới lên sàn chưa có ở FiinTrade là ca hợp lệ, vài mã |
| (ii) | số mã có dữ liệu sụt so mốc lượt `success` gần nhất | > **2%** | — |
| (iii) | `latest_trading_date` > hôm nay (giờ VN) | tuyệt đối | lỗi đồng hồ/múi giờ nguồn |
| (iv) | `latest_trading_date` < mốc lượt trước | tuyệt đối | nguồn lùi thời gian |

**Không có vế "ngày giao dịch"** (§2.1.6) và **không có vế thiếu trang** (trang 1 luôn trọn). `--backfill` không qua guard tổng vì cố ý chạy từng phần — chỉ có ngắt khẩn §5.2 và bộ đếm trong `stats`.

### 5.5 `price_store`

**a. `list_codes(conn, tickers=None)`** — cổ phiếu `listed` ⋈ `issuer_external_id('fiintrade')`, sắp theo ticker. Trả thêm `no_organ_code` (mã không tra được — 0 hôm nay, đếm và nêu tên) và **từ chối** nếu một `organCode` trỏ tới hơn một security listed (giả định §2.2.4). `--codes` nêu ticker không có trong tập ⇒ lỗi rõ tên, không chạy.

**b. `apply` — UPSERT theo PK, merge `raw` theo khoá adapter, bỏ qua dòng không đổi**

```sql
INSERT INTO market.price_daily (security_id, trading_date, close_adj, close_raw,
                                open_value, highest_value, lowest_value, raw)
VALUES (:sid, :d, :ca, :cr, :o, :h, :l,
        jsonb_build_object('fiintrade', jsonb_build_object('fetched_at', :fa,
                                                           'payload', cast(:p AS jsonb))))
ON CONFLICT (security_id, trading_date) DO UPDATE SET
  close_adj     = EXCLUDED.close_adj,
  close_raw     = coalesce(market.price_daily.close_raw, EXCLUDED.close_raw),   -- §4.2
  open_value    = EXCLUDED.open_value,
  highest_value = EXCLUDED.highest_value,
  lowest_value  = EXCLUDED.lowest_value,
  raw           = market.price_daily.raw || EXCLUDED.raw,                       -- giữ khoá adapter khác
  ingested_at   = clock_timestamp()
WHERE market.price_daily.raw->'fiintrade'->'payload'
      IS DISTINCT FROM EXCLUDED.raw->'fiintrade'->'payload'
```

Ba luật trong một câu: `coalesce` = *điền một lần*; `||` ở tầng ngoài = *writer chỉ đụng khoá của mình* (review vòng 2, C5 — khoá `bvsc` tương lai nguyên vẹn); `WHERE … IS DISTINCT FROM` = **bỏ qua dòng payload không đổi** — lượt hằng ngày ghi lại 60 phiên/mã (91.000 dòng) mà thường chỉ 1–2 phiên/mã đổi (phiên mới + phiên T+1 điền dòng tiền); không có vế này là ~300 MB churn/ngày cho autovacuum. `rowcount` của executemany = **`rows_changed`** — đây là số idempotency: lượt hai phải bằng **0**.

**c. `raw_close_mismatches(conn, security_ids, since)`** — sau `apply`, trong cùng giao dịch: đếm dòng có `close_raw IS DISTINCT FROM (raw->'fiintrade'->'payload'->>'closePrice')::numeric`, nêu tên ≤ 20. Đây là mắt của quyết định §4.2 — `0` là bình thường.

**d. Bằng chứng khi từ chối** — `staging.raw_payload('fiintrade', 'price:refusal')`: `reasons` + bộ đếm + 3 bản ghi đầu của ≤ 5 mã. Không lưu 300 MB trang thô.

**e. Con trỏ backfill** — `stats.cursor` = ticker vừa xong, ghi vào chính dòng `ops.etl_run` của lượt **sau mỗi mã** (`save_progress`), nên chết giữa chừng vẫn giữ tiến độ (`close_run` coalesce stats). Lượt sau đọc con trỏ của lượt backfill gần nhất *(bất kể status)* và đi tiếp từ mã kế; con trỏ đã ở mã cuối ⇒ **bắt đầu vòng mới**, ghi log rõ. `--codes` không đụng con trỏ.

### 5.6 Lịch và vận hành

| Mục | Giá trị |
|---|---|
| Task | **`dlck-price`, 15:40 ngày làm việc** |
| Vì sao 15:40 | Soi lịch sẵn có (bài học 5 lát 2): 15:20 screener (~1 phút) · 15:30 OMO · 18:00 OMO · 18:10 events. 15:40 + 45 phút (xấu nhất 81) kết thúc trước 18:00; ingester đã đóng 15:05 |
| Trạng thái | đăng ký nhưng **để `Disabled`** cùng cả đội cho tới khi [4d] bật lại |
| Log | `dlck-runtime/logs/price.log` |
| `Assert-TaskCommand` | `-MustContain "python -m etl price"` **`-MustNotContain "--backfill"`** — task tự động không bao giờ chạy backfill |
| Backfill | chạy tay ngoài giờ giao dịch: `python -m etl price --backfill --max-minutes 600` mỗi đêm cho tới khi `stats.pass_complete = true` |

## 6. Seam test *(chốt cùng plan — §4.5.2; expected lấy từ mẫu thật ở `samples/`, không tính lại theo code)*

| # | Seam | Case | Expected — nguồn độc lập |
|---|---|---|---|
| 1 | `fetch` — URL | mã `NHN` trang 2 | đúng chuỗi `?Code=NHN&Frequently=Daily&Page=2&PageSize=60&language=vi` |
| 2 | `fetch` — `status` hai kiểu | body `status: 0` và `status: "Success"` | **cả hai hợp lệ**, 0 retry |
| 3 | `fetch` — mã sai | `{"status":"Failed","errors":["Code not valid: VHM"]}` | `CodeInvalid`, **0 lần ngủ** |
| 4 | `fetch` — lỗi tạm rồi hồi | 2 lần HTTP 500 rồi 200 | `retries = 2`, ngủ `[2, 4]` |
| 5 | `fetch` — hết retry | 500 mãi | `FetchError` nêu mã và trang |
| 6 | `fetch` — dừng trang | 60 · 60 · 22 bản ghi | đúng **3** lời gọi, không gọi trang 4 |
| 7 | `fetch` — giãn cách | clock giả: lời gọi 2 đến sau 0,1 s | ngủ **0,4 s** |
| 8 | `fetch` — ngắt khẩn | 10 mã liên tiếp 500 | `FetchError` sau đúng 10 mã, mã 11 không gọi |
| 9 | `normalize` — ánh xạ | BID trang 1 bản ghi đầu (`shape` sample) | `date(2026,9,3)` · `close_adj 36450` · `close_raw 36450` · `open 36750` · `high 36750` · `low 36400` |
| 10 | `normalize` — thô ≠ điều chỉnh | BID trang 52 bản ghi đầu | `close_adj = Decimal("5747.8202873773")` · `close_raw = Decimal("14500")` |
| 11 | `normalize` — gộp chồng trang | cùng ngày ở hai trang, payload khác | 1 dòng, bản trang trước; `dup_dates = 1` |
| 12 | `guard` (i) | 31 mã hỏng / 1.523 | từ chối (2,04%); 30/1.523 cho qua |
| 13 | `guard` (ii) | `with_data 1.480` vs mốc 1.523 | từ chối (−2,8%); 1.500 cho qua |
| 14 | `guard` (iii)/(iv) | `latest = today + 1` · `latest < mốc` | từ chối cả hai, lý do nêu ngày |
| 15 | `store.list_codes` | 3 security cắm tay: 1 mã có organCode, 1 thiếu, 1 ETF | trả đúng 1; `no_organ_code = ['X']`; ETF không có mặt |
| 16 | `store.apply` — điền/đè/bỏ qua | ghi 1 dòng; ghi lại **cùng** payload; ghi lại payload **khác** | `rows_changed` = **1 · 0 · 1**; `close_adj` theo bản mới |
| 17 | `store.apply` — `close_raw` một lần | cắm sẵn `close_raw = 999`, apply `closePrice = 36450` | vẫn **999**; `raw_close_mismatches` trả **1** kèm tên |
| 18 | `store.apply` — merge khoá adapter | cắm sẵn `raw = {"bvsc": {...}}` rồi apply | `raw` có **cả hai** khoá, `bvsc` nguyên văn |
| 19 | `job` hằng ngày | fetch giả 2 mã từ fixture, DB thật, role `dlck_etl` | `count(*)` = số phiên; `stats.rows_changed` lượt 1 > 0, lượt 2 = **0**; `data_domain_state` watermark = ngày mới nhất |
| 20 | `job` từ chối | fetch giả: 1/2 mã `CodeInvalid` (50% > 2%) | exit 1, `count(*) = 0`, 1 bằng chứng, `status='failed'` |
| 21 | `job --backfill` | `max_minutes` hết sau mã 1 của 3; chạy lại | lượt 1 `cursor = mã 1`, lượt 2 làm mã 2–3 rồi `pass_complete = true` |
| 22 | CLI | `etl price --backfill --codes A,B --max-minutes 5` | gọi `run(backfill=True, codes=['A','B'], max_minutes=5)` |

Test đụng database chạy **dưới role `dlck_etl`** (`SET LOCAL ROLE` / listener `SET ROLE`) — §3.5, mọi đường đọc lẫn ghi.

## 7. Tiêu chí nghiệm thu

Tiêu chí **bất biến, không phải số thời điểm** *(§4.4.4)* — cấm assert `1.523` hay một `count(*)` cụ thể.

| AC | Nội dung | Kiểm bằng |
|---|---|---|
| **AC1** | Toàn bộ test backend xanh, gồm 22 seam mới | `uv run pytest`, dán output thật |
| **AC2** | Chạy tay `--codes BID,VHM,TD6` dưới credential production exit 0 **trước** lượt toàn tập (§3.5) | log + `count(*)` 3 mã |
| **AC3** | Lượt hằng ngày toàn tập exit 0; `stats.with_data + invalid + failed + no_organ_code = codes`; `raw_close_mismatch = 0`; mỗi mã có dữ liệu ghi đúng số phiên trang 1 trả | `count(*) GROUP BY security_id` đối chiếu `stats` |
| **AC4** | **Idempotent** — chạy lại: `rows_changed = 0`, `count(*)` không đổi | hai lượt liên tiếp |
| **AC5** | Guard từ chối thật bằng **đột biến**: ép 3% mã thành `CodeInvalid` ⇒ (i) đỏ, `count(*)` không đổi, có bằng chứng | chạy có đột biến |
| **AC6** | `price_factor` có nghĩa trên lịch sử: một mã đã có sự kiện quyền cho `factor < 1` trước ngày ex và `= 1` từ ngày ex | `SELECT` trên DMX quanh 2026-08-18 sau `--backfill --codes DMX` |
| **AC7** | Backfill **tiếp tục được**: lượt `--max-minutes` ngắn dừng đúng ngân sách, lượt sau đi tiếp từ `cursor`, không làm lại mã đã xong | hai lượt, so `cursor` và `codes_done` |
| **AC8** | Task `dlck-price` đăng ký đúng lệnh, 15:40 (`StartBoundary` có `+07:00`), **`Disabled`**, không mang `--backfill` | `Assert-TaskCommand` + `Triggers[0].StartBoundary` |

⚠️ AC8 cần cửa sổ Run as Administrator — ràng buộc đã gặp ở lát 1 và 2; script sẵn sàng, chủ dự án chạy.

## 8. Checklist tài liệu sống — cùng lượt với code *(§1.6, §1.7)*

| File | Sửa gì | Tầng |
|---|---|---|
| [`10-sources/market/09-fiin-market-price.md`](../../../10-sources/market/09-fiin-market-price.md) | **`closePrice`/`referencePrice` là giá thô**; `status` hai kiểu; `Code not valid`; `FromDate` bị bỏ qua; `totalCount` chính xác, trang 53 ngắn; dòng tiền T+1; latency đo lại | reference — **đã đo lại** |
| [`10-sources/market/00-conventions.md`](../../../10-sources/market/00-conventions.md) | §6.1 bảng kiểu `status`: thêm dòng `PriceData/*` **lẫn cả hai**; bẫy 1: `PriceData` trả `Failed` có tên; bẫy 6: ngoại lệ `PriceData`; **bẫy 8: đính chính** giá thô lịch sử có ở `closePrice`; §10: thêm số đo nhịp tuần tự 1.523 lời gọi sau lượt thật | reference |
| [`20-design/market-data-store.md`](../../../20-design/market-data-store.md) | §4.1 dòng giá: **1.523**, ~45 phút tuần tự; §4.2 backfill: số lời gọi thật, con trỏ, vài đêm; §4.3: nhịp tuần tự đã đo, 8 luồng không cần; **§5.2 `close_raw` điền từ `closePrice`**, writer EOD thành đối chứng; §4.4 ghi lượt dọn đã chạy | explanation |
| [`00-overview/roadmap.md`](../../../00-overview/roadmap.md) | Trạng thái lát 3; "Điểm vào cho lát 3" → **điểm vào lát 4** (trigger snapshot + re-crawl giá) | |
| [`docs/90-records/README.md`](../../README.md) | Dòng của plan này | index sở hữu |
| [`backend/README.md`](../../../../backend/README.md) | Mục `etl price` (hai chế độ, `--codes`, backfill ngoài giờ), 10 task | |
| [`README.md`](../../../../README.md) gốc · [`service-topology.md`](../../../20-design/service-topology.md) §5 | 10 task, `dlck-price` 15:40 | |
| `scripts/register-tasks.ps1` | Task thứ 10 | |

Trước khi tuyên "đã đồng bộ": `git grep` các chuỗi `1.974`, `close_raw`, `Cả 9 task`, `9 task`, `chỉ có ở phiên hiện tại` và xác nhận mọi hit còn lại **hoặc đã đúng, hoặc thuộc vùng lịch sử**.

## 9. Điểm cần chủ dự án duyệt tường minh *(đã thực thi theo chỉ thị; rà lại ở đây)*

1. **`close_raw` điền từ `closePrice`** (§4.2) — đảo ngược thiết kế step-03 *"backfill để NULL"* trên cơ sở ba phép kiểm độc lập. Rollback = một `UPDATE … SET close_raw = NULL`.
2. **Tuần tự, không `core/http`** (§4.1) — trái với kỳ vọng ở roadmap *"lát đầu tiên cần lớp core/http"*, vì nhu cầu đã đổi khi ngân sách ngày còn 1.523 lời gọi.
3. **Không mở cột mới** (§4.3) — `raw` giữ đủ 99 trường.
4. **Giờ chạy 15:40**, ngưỡng (i)/(ii) = **2%**, ngắt khẩn **10 mã liên tiếp**.
5. Backfill là **vòng lặp tiếp diễn** (hết vòng thì vòng mới) — chạy tay đến khi `pass_complete`, sau đó dùng làm cơ chế làm mới định kỳ nếu lát 4 muốn.
