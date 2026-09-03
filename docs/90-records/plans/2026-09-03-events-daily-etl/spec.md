# Spec — `etl events`: lát 2 của [7] ETL REST hằng ngày

**Ngày:** 2026-09-03 · **Trạng thái:** chờ chủ dự án duyệt · **Lát trước:** [`etl screener`](../2026-09-03-screener-daily-etl/spec.md) ✅ xong cùng ngày

---

## 1. Vì sao lát này, và lát này là gì

Lịch sự kiện là lát **rẻ nhất mà mở khoá nhiều nhất** trong nhóm [7]. Nó tốn 9 lời gọi/ngày, nhưng ba thứ phía sau đều chờ nó:

- **họ Snapshot** kích hoạt theo `Earning` + `ShareIssuance` *([market-data-store §4.1b](../../../20-design/market-data-store.md))*
- **BCTC** kích hoạt theo `getCorporateEarning`
- **re-crawl giá** kích hoạt theo `exright_date` *(step-03 §4: "tín hiệu vận hành quan trọng nhất bảng này")*

Vì vậy thứ tự lát đã đảo 2026-09-03: lịch sự kiện đứng **trước** lát giá và lát snapshot.

**Lát này là:** job `python -m etl events` nạp sáu họ `Calendar/GetCorporate*` vào `market.corporate_event`, cộng chính sách tạo issuer tối thiểu cho mã vắng danh bạ.

**Lát này KHÔNG phải:** không dựng cơ chế trigger, không gọi snapshot/BCTC/giá. Lát này chỉ **đặt dữ liệu vào kho để lát sau đọc**. Cơ chế trigger là việc của lát 4.

## 2. Dữ kiện đã đo vs giả định *(§4.8 bước 0 — bắt buộc)*

### 2.1 Đã đo — 46 lời gọi thật, 2026-09-03

Hồ sơ đầy đủ: [`measurements.md`](measurements.md) · bằng chứng: [`samples/`](samples/). Sáu điều quan trọng nhất:

1. **`PageSize` không có trần** — nguồn trả `min(PageSize, số còn lại)`. Tải trọn sáu họ = **9 lời gọi, ~140 giây, 36 MB**. Phân trang ổn định (57.026 bản ghi qua 3 trang, 0 trùng giữa trang).
2. **`FromDate`/`ToDate` lọc theo trục ngày khác nhau ở mỗi họ** — `payoutDate` (Cash/StockDividend) · `issueDate` (ShareIssuance) · `publicDate` (AGM). Trục **sắp xếp** lại là trục thứ ba (`exrightDate`).
3. 🔴 **Earning lọc theo trường không có trong response** — cửa sổ `2026-03-10..14` trả **24** bản ghi trong khi có **217** bản ghi mang `publicDate` trong đúng cửa sổ đó. Hai tập cắt nhau.
4. **Khoá tự nhiên với `stage_key` đúng như thiết kế F6** để lại: AGM 16 · CashDividend 4 · StockDividend 3 · ShareIssuance 127 · IPO 0 · Earning 0 khoá đụng.
5. **517/2.065 `organCode` của lịch không có trong danh bạ** = 5.964/110.737 bản ghi (5,4%); phần `publicDate ≥ 2023` là 620/34.418 (1,8%).
6. **`totalCount` trôi cả hai chiều** — Earning **−150** trong 24 ngày; bốn họ kia tăng.

### 2.2 Giả định — CHƯA kiểm, ghi để người sau biết mình đứng trên gì

| Giả định | Hỏng thì sao | Vì sao chấp nhận |
|---|---|---|
| Tải trọn 9 lời gọi/ngày không gặp tín hiệu chặn | ETL đứng | Tải thấp hơn burst Screener 52 trang đã đo an toàn 2026-08-15; và **thấp hơn ngân sách ~10 lời gọi** mà [market-data-store §4.1](../../../20-design/market-data-store.md) cấp cho họ này |
| `organCode` là định danh **ổn định** của nguồn | Nguồn đổi hệ mã ⇒ đẻ hàng loạt issuer tối thiểu trùng nghĩa | Vế guard (iii) chặn đúng ca này — đẻ quá 20 issuer/lượt thì dừng |
| Bản ghi cũ không bị nguồn **sửa im lặng** ngoài phần ta thấy | Kho giữ bản cũ | Tải trọn mỗi ngày + UPSERT làm giả định này gần như vô hại |
| Trục lọc của `IPO` là `publicDate` | — | Không ảnh hưởng: tải trọn thì không dùng trục lọc nào |

## 3. Phạm vi

### 3.1 Trong phạm vi

Sáu họ `GetCorporate*`: `AGM` · `CashDividend` · `StockDividend` · `Earning` · `IPO` · `ShareIssuance` → `market.corporate_event`. Job, guard, chính sách issuer tối thiểu, đăng ký task, cập nhật tài liệu sống.

### 3.2 Ngoài phạm vi — phân ba loại *(§1.4)*

| Mục | Loại | Lý do |
|---|---|---|
| `getCalendarWatchList` (190.143 bản ghi) | **Đã có đường khác** | Bộ `eventListCode` rộng hơn CHECK 6 giá trị ⇒ dùng nó sẽ bị CHECK chặn ~79k dòng *(step-03 §4, review vòng 3 M-5)*. Sáu endpoint chuyên biệt đã phủ đủ |
| `getEconomy` (lịch vĩ mô, ~2 sự kiện/tuần) | **Loại có chủ đích** | Lịch vĩ mô Việt Nam, không phải sự kiện doanh nghiệp; `corporate_event` không có chỗ cho nó và nó không kích hoạt gì |
| Cơ chế trigger snapshot/BCTC/re-crawl giá | **Đã có đường khác** | Là nội dung lát 3–4; lát này chỉ đặt dữ liệu |
| Quét sàn làm lưới bắt phần lịch bỏ sót | **Đã có đường khác** | [market-data-store §4.1b](../../../20-design/market-data-store.md) giao cho lát snapshot |
| Backfill riêng phần `publicDate < 2023` | **Đã có đường khác** | Tải trọn làm cả lịch sử trong cùng một lượt, không cần việc riêng |

## 4. Ba chỗ lệch khỏi lược đồ đã duyệt — kèm lý do

Lược đồ `market.corporate_event` do [`step-03-market-data.md` §4](../2026-08-25-postgres-data-schema/step-03-market-data.md) sở hữu, đã qua 4 vòng review. Spec này **giữ nguyên lược đồ, không migration**. Ba chỗ lệch, tất cả nằm ở tầng ETL:

### 4.1 `stage_key` của ShareIssuance thêm `planVolumn`

Thiết kế ghi `issueMethodName`+`issueYear`. Đo trên 10.097 bản ghi thật: `issueYear` gỡ được đúng **2/129** khoá đụng — gần như vô dụng, vì hai đợt phát hành cùng năm là chuyện thường. `planVolumn` gỡ **103/129**, còn **26**.

### 4.2 `stage_key` của AGM = ngày tổ chức đại hội

Thiết kế không nói gì về AGM — cột `stage_key` để trống. Kết quả: **16 khoá đụng, cả 16 khác nội dung**. Nguyên nhân là doanh nghiệp triệu tập đại hội nhiều lần (lần 1 không đủ tỷ lệ, dời sang lần 2) với cùng `publicDate` và `exrightDate`, chỉ khác ngày họp. Lấy `issueDate` (ngày tổ chức) làm `stage_key` còn **8**.

⚠️ `eventTitle` **không dùng được** — null ở cả 23.467/23.467 bản ghi.

### 4.3 Tải trọn thay vì `FromDate`

Thiết kế ghi *"ETL lấy phần mới bằng `FromDate`"*. Số đo bác bỏ: xem §2.1 điểm 2–3. Ba lý do đổi:

1. **Đúng hơn** — không trục ngày nào bỏ sót; Earning không có trục dùng được.
2. **Rẻ hơn thiết kế** — 9 lời gọi so với ngân sách ~10.
3. **Ít code hơn** — backfill và job hằng ngày là **một đường code**, không watermark, không cửa sổ, không nhánh "lượt đầu".

Đổi lại: 110.695 lượt UPSERT/ngày và ~140 giây mỗi lượt.

## 5. Job `python -m etl events`

### 5.1 Khuôn — y `screener_job.run`, không sáng tạo

```
fetch → normalize → merge → guard (TRƯỚC commit) → apply → close_run
```

Một giao dịch cho dữ liệu. Guard đánh giá **trong** `with engine.begin()`, từ chối thì `raise` để tự rollback; bằng chứng ghi ở giao dịch riêng. Năm module: `events_fetch` · `events_normalize` · `events_guard` · `events_store` · `events_job`.

CLI: `python -m etl events [--accept-new]` — thêm nhánh vào `etl/__main__.py` cạnh `omo`/`refdata`/`screener`.

### 5.2 `events_fetch` — I/O thuần

| Mục | Giá trị |
|---|---|
| Base | `https://wlgw-market.fiintrade.vn/Calendar` |
| Header | `Origin: https://fiinapp.bvsc.com.vn` *(bắt buộc — 00-conventions §2)* |
| `PageSize` | **20.000** *(đo: không có trần; 20.000 cho Earning ~36 s/trang, 3,1 MB/10.000 bản ghi)* |
| Timeout | 300 s *(Earning ~36 s/trang — timeout 60 s của lát 1 sẽ đứt)* |
| Phân trang | lặp `Page` tới khi `collected >= totalCount` |
| Retry | 3 lần, backoff 2·4·8 s; hết thì `raise` — **không trả trang rỗng** *(00-conventions §10.5)* |
| Số lời gọi | AGM 2 · Earning 3 · bốn họ kia 1 = **9** |

Một `httpx.Client` cho trọn lượt, khuôn `screener_fetch`.

🔴 **Không truyền `Ticker=`** — nguồn bỏ qua tham số này im lặng và trả toàn bộ kho *(`08-fiin-event-calendar.md`)*. Job này không lọc theo mã nên bẫy không chạm tới, nhưng ghi lại để người sau không thêm vào.

### 5.3 `events_normalize` — thuần, không I/O

**Ánh xạ trường → cột:**

| Họ | `event_type` | `public_date` | `exright_date` | `record_date` | `payout_date` | `year_report` | `length_report` | `source_url` |
|---|---|---|---|---|---|---|---|---|
| AGM | `AGM` | `publicDate` | `exrightDate` | — | — | — | — | `sourceUrl` |
| CashDividend | `CashDividend` | `publicDate` | `exrightDate` | `recordDate` | `payoutDate` | — | — | — |
| StockDividend | `StockDividend` | `publicDate` | `exrightDate` | `recordDate` | `payoutDate` | — | — | — |
| Earning | `Earning` | `publicDate` | — | — | — | `yearReport` | `lengthReport` | — |
| IPO | `IPO` | `publicDate` | — | — | — | — | — | — |
| ShareIssuance | `ShareIssuance` | `publicDate` | `exrightDate` | — | — | — | — | — |

⚠️ **`source_url` chỉ AGM có.** Năm họ kia không trả trường đó — trái với câu khái quát ở đầu `08-fiin-event-calendar.md`; §8 dưới sửa câu đó.

**`stage_key` — công thức từng họ:**

| Họ | `stage_key` | Nguồn của luật |
|---|---|---|
| CashDividend · StockDividend | `f"{dividendYear}\|{stageName}"` | thiết kế F6, nguyên văn |
| ShareIssuance | `f"{issueMethodName}\|{issueYear}\|{planVolumn}"` | F6 + §4.1 |
| AGM | ngày `issueDate` dạng `YYYY-MM-DD`, rỗng nếu null | §4.2 |
| Earning · IPO | `NULL` | không cần — 0 khoá đụng trên toàn kho |

**Hai bẫy phải xử trong parse:**

1. `publicDate` **đôi khi kèm giờ** (`2018-03-27T11:03:28.023` cạnh `2018-03-27T00:00:00`) — cắt lấy 10 ký tự đầu. Không cắt thì hai bản ghi cùng ngày thành hai khoá khác nhau.
2. `planVolumn` **viết sai chính tả ở nguồn** — đọc đúng tên nguồn, không "sửa" thành `planVolume`.

**Luật gộp trong lượt** — 41 khoá còn đụng sau mọi công thức trên *(nguồn tự đẻ trùng và giữ hai phiên bản của cùng một sự kiện sau khi dời ngày)*:

- gom theo khoá tự nhiên; giữ bản ghi có **nhiều trường non-null nhất**;
- hoà thì lấy bản **xuất hiện sau** trong thứ tự nguồn *(deterministic — nguồn trả byte-identical giữa hai lượt gọi)*;
- đếm `dup_conflicts` = **số bản ghi bị gộp bỏ** (đo được **42** trên 41 khoá — một khoá có 3 bản ghi), **và nêu tên tối đa 20 khoá** — bài học 3 của lát 1: *bộ đếm không nêu tên thì để suốt buổi không biết mã nào*.

`payload` giữ **nguyên bản ghi thô** nên không trường nào mất, kể cả trường không lên cột.

### 5.4 `events_guard` — thuần, đánh giá trước commit

Module thuần, đầu vào là số trần để test không cần database. Bốn vế, vế nào hỏng cũng từ chối:

| # | Vế | Ngưỡng | Vùng dữ liệu thật đã đo |
|---|---|---|---|
| (i) | mỗi họ: `collected == totalCount` | bằng tuyệt đối | — |
| (ii) | mỗi họ: `totalCount` sụt so mốc lượt `success` gần nhất | > **2%** | Earning −0,26% trong 24 ngày là biến động thật lớn nhất thấy được |
| (iii) | **số issuer tối thiểu tạo mới trong lượt** | > **20** | lượt backfill đầu = **517** ⇒ buộc chạy tay với `--accept-new` |
| (iv) | tỷ lệ khoá đụng sau gộp | > **0,5%** | 42/110.737 = **0,037%** — ngưỡng cách xa 13 lần |

**Không có vế "ngày giao dịch"** — khác biệt lớn nhất so với lát 1. Lịch sự kiện không phụ thuộc phiên: ngày lễ nguồn vẫn trả đủ kho, và không có "dòng ma" nào để đẻ ra.

Vế (iii) là chốt chặn của chính sách F7: nó biến *"âm thầm đẻ issuer"* thành *"đẻ quá tay thì dừng và gọi người"*. Cờ `--accept-new` y khuôn `refdata --accept-drop` đã có tiền lệ và đã chạy thật.

### 5.5 `events_store`

**a. `ensure_issuers` — chính sách F7, `INSERT` một chiều**

Mã vắng danh bạ ⇒ tạo `issuer` tối thiểu + `issuer_external_id('fiintrade', organ_code)` rồi ghi sự kiện; **không bỏ dòng, không để FK chặn job** *(step-03 §4, vòng 4 F7)*.

🔴 **Luật mới, chặn hai-chủ-một-bảng** *(§1.7)*: `etl refdata` là chủ duy nhất của nội dung `market.issuer`. `etl events` **chỉ được `INSERT` khi `organ_code` chưa tồn tại, tuyệt đối không `UPDATE`**. Khi doanh nghiệp xuất hiện trong danh bạ, lượt `refdata` kế tiếp nhận diện đúng dòng đó qua `organ_code` và cập nhật — issuer tối thiểu **tự lành**, không đẻ dòng thứ hai.

`market.issuer.name` là `NOT NULL` mà **ba họ không trả tên** (CashDividend · StockDividend · ShareIssuance chỉ có `organCode` + `ticker`). Thứ tự lấy tên: `organShortName` → `organName` → `ticker` → `organCode`. Gom tên **qua cả sáu họ trước** rồi mới tạo, để một mã xuất hiện ở nhiều họ lấy được tên tốt nhất.

`com_type_code`, `icb_code`, `industry_id` để **NULL** — không đoán. Đã kiểm: điều này không phá bất biến nào của [lát ngành hai lớp](../2026-08-27-industry-two-layer-mapping/ledger.md), vì câu A chỉ đếm issuer *có cổ phiếu đang niêm yết*, mà issuer tối thiểu không có dòng `security` nào trỏ tới; câu B an toàn với NULL nhờ `is distinct from`.

**b. `apply` — UPSERT theo khoá tự nhiên**

`INSERT … ON CONFLICT` phải lặp lại **nguyên văn TOÀN BỘ năm biểu thức `coalesce` của index** thì Postgres mới suy ra arbiter *(step-03 §4, vòng 4 F9)*. `DO UPDATE SET payload`, `source_url`, `ingested_at = clock_timestamp()`.

**c. Bằng chứng khi từ chối**

**Không** lưu trang thô vào `staging.raw_payload` — một lượt là 36 MB, và [F1 của review vòng 4](../2026-08-25-postgres-data-schema/review-2026-08-25.md) đã chốt sự kiện *không* vào staging vì đã có thô inline per-row. Thay bằng: ghi `meta` gồm `reasons`, `run_id`, đếm từng họ, và **50 bản ghi đầu của họ gây từ chối** — đủ chẩn đoán, không phình kho.

**d. Công tắc miền**

`ops.data_domain_state`: `('market.events', 'fiintrade')`, `status='active'`, `watermark = max(public_date)` toàn lượt.

### 5.6 Lịch và vận hành

| Mục | Giá trị |
|---|---|
| Task | `dlck-events`, **18:00 hằng ngày** |
| Vì sao 18:00 | Sau phiên và sau `dlck-screener` (15:20) ⇒ không giành tài nguyên với ingester (08:30–15:00); dùng danh bạ đã làm mới lúc 08:00 cùng ngày |
| Trạng thái | đăng ký nhưng **để `Disabled`** cùng cả đội cho tới khi [4d] bật lại |
| Log | `dlck-runtime/logs/events.log` |

`scripts/register-tasks.ps1` lên **9 task**; thêm `Assert-TaskCommand -MustContain "python -m etl events"`.

## 6. Seam test *(chốt cùng plan — §4.5.2; expected lấy từ mẫu thật ở `samples/`, không tính lại theo code)*

| # | Seam | Case | Expected — nguồn độc lập |
|---|---|---|---|
| 1 | `normalize` — ánh xạ trường | 3 bản ghi đầu mỗi họ trong `shape-20260903.json` | Cột đúng theo bảng §5.3, giải tay từ JSON |
| 2 | `normalize` — `publicDate` có giờ | `"2018-03-27T11:03:28.023"` | `date(2018,3,27)` — và **cùng khoá** với bản `T00:00:00` của SASTECO |
| 3 | `normalize` — `stage_key` | SD9 hai dòng `dividendYear` 2019 vs 2021, cùng mọi thứ khác | **2 khoá khác nhau** ⇒ 2 dòng |
| 4 | `normalize` — luật gộp | Nhóm ABI trong `key-collisions-20260903.json` (một bản `listingDate` null, một bản đã điền) | **1 dòng**, giữ bản có `listingDate`; `dup_conflicts = 1` kèm tên khoá |
| 5 | `guard` (i) | `collected=100, total_count=101` | từ chối, lý do nêu cả hai số |
| 6 | `guard` (ii) | `total_count=57.000` vs mốc `57.176` | **cho qua** (−0,31% < 2%) — case biên đúng vùng dữ liệu thật |
| 7 | `guard` (iii) | `issuers_new=21`, không cờ | từ chối; `issuers_new=21` **có** cờ ⇒ cho qua |
| 8 | `guard` (iv) | `dup=600, rows=110.000` | từ chối (0,55% > 0,5%) |
| 9 | `store` — UPSERT arbiter | Ghi cùng khoá tự nhiên hai lần, `payload` khác | **1 dòng**, payload mới, `event_id` không đổi |
| 10 | `store` — issuer tối thiểu | `organ_code` lạ, không có trường tên nào | 1 issuer `name = organ_code`; chạy lại ⇒ **0 issuer mới** |
| 11 | `store` — không `UPDATE` issuer | issuer có sẵn tên `'X'`, lịch trả `organShortName='Y'` | tên vẫn `'X'` |

Test chạy trên Postgres thật **dưới role `dlck_etl`** *(§3.5 — mọi đường production đi qua, đọc lẫn ghi)*.

## 7. Tiêu chí nghiệm thu

Tiêu chí **bất biến, không phải số thời điểm** *(§4.4.4)* — nguồn tăng mỗi ngày nên cấm assert `110.695`.

| AC | Nội dung | Kiểm bằng |
|---|---|---|
| **AC1** | Toàn bộ test backend xanh, gồm 11 seam mới | `uv run pytest`, dán output thật |
| **AC2** | Lượt backfill chạy tay `--accept-new` exit 0; **số dòng ghi = số khoá tự nhiên duy nhất của dữ liệu tải về**; `stats` nêu đủ 4 bộ đếm | Truy vấn `count(*)` đối chiếu `stats.rows_written` |
| **AC3** | **Idempotent** — chạy lại ngay sau đó: `rows_written` không đổi, `issuers_created = 0`, `count(*)` không đổi | Hai lượt liên tiếp |
| **AC4** | Guard từ chối thật khi **đột biến** dữ liệu: bỏ 1 trang ⇒ vế (i) đỏ; ép `issuers_new` vượt ngưỡng không cờ ⇒ vế (iii) đỏ. Cả hai lượt **không ghi dòng nào** | Chạy có đột biến, kiểm `count(*)` trước/sau bằng nhau |
| **AC5** | `corporate_event.exright_date` có dòng dùng được cho lát sau: `SELECT count(*) FROM market.corporate_event WHERE exright_date >= current_date` **> 0** | Truy vấn thật |
| **AC6** | Task `dlck-events` đăng ký đúng lệnh và **đang `Disabled`** | `Assert-TaskCommand` + soi `State` |

⚠️ AC6 cần cửa sổ Run as Administrator — cùng ràng buộc đã gặp ở lát 1.

## 8. Checklist tài liệu sống — cùng lượt với code *(§1.6, §1.7)*

| File | Sửa gì | Tầng |
|---|---|---|
| [`10-sources/market/08-fiin-event-calendar.md`](../../../10-sources/market/08-fiin-event-calendar.md) | Thêm mục **trục lọc `FromDate` từng họ** và **`PageSize` không có trần** *(đo 2026-09-03)*; sửa câu khái quát *"trường `sourceUrl` trỏ thẳng về bản công bố gốc"* → **chỉ AGM có**; cập nhật `totalCount` sáu họ kèm ngày đo | reference — được sửa vì **đã đo lại** *(§1.2)* |
| [`20-design/market-data-store.md`](../../../20-design/market-data-store.md) §4.1, §4.2 | Lịch sự kiện: bỏ chú *"dùng `FromDate` lấy phần mới"*, ghi **tải trọn 9 lời gọi**; §4.2 sửa *"~500 lời gọi"* → **9** | explanation |
| [`00-overview/roadmap.md`](../../../00-overview/roadmap.md) | Trạng thái lát 2; mục *"Điểm vào cho lát 2"* chuyển thành điểm vào lát 3 | |
| [`docs/90-records/README.md`](../../README.md) | Cập nhật dòng của plan này | index sở hữu |
| [`backend/README.md`](../../../../backend/README.md) | Thêm subcommand `etl events` | |
| `scripts/register-tasks.ps1` | Thêm task thứ 9 | |

Trước khi tuyên "đã đồng bộ": `git grep` các chuỗi `FromDate`, `~500`, `sourceUrl` và xác nhận mọi hit còn lại **hoặc đã đúng, hoặc thuộc vùng lịch sử** *(`decisions/`, `90-records/` — không viết lại quá khứ)*.

## 9. Điểm cần chủ dự án duyệt tường minh

1. **Ba chỗ lệch khỏi lược đồ đã duyệt** — §4.1 (`planVolumn` vào `stage_key`), §4.2 (AGM dùng ngày đại hội), §4.3 (tải trọn thay `FromDate`). Cả ba nằm ở tầng ETL, **không đụng lược đồ, không migration**.
2. **Giữ chính sách F7** — tạo issuer tối thiểu, chấp nhận bảng `issuer` tăng 1.552 → ~2.069 dòng, trong đó ~517 dòng không có ngành và không có `com_type_code`.
3. **Giờ chạy 18:00** và **ngưỡng vế (iii) = 20 issuer/lượt**.
4. **Lượt backfill đầu tiên phải chạy tay có người nhìn** với `--accept-new` — 517 issuer là con số phải được người xác nhận, không để job tự quyết.
