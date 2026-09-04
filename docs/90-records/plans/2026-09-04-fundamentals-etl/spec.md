# Spec — lát 5 `etl fundamentals`: báo cáo tài chính và danh sách PDF

**Ngày:** 2026-09-04 · **Nhánh:** `feat/fundamentals-etl` · **Trạng thái:** chờ chủ dự án duyệt
**Tiền đề:** [roadmap — Điểm vào cho lát 5](../../../00-overview/roadmap.md) · [khảo sát BCTC 2026-09-04](../../surveys/2026-09-04-bctc-endpoints/README.md) · [tài liệu nguồn 05](../../../10-sources/market/05-fiin-financial-statements.md) · [spec lát 4](../2026-09-04-snapshot-family-etl/spec.md) (khuôn được nhân bản)

Tiêu chí xuyên suốt của lát này, chốt trong brainstorm: **ít luật nhất, không đọc sai**. Mỗi quyết định dưới đây được chấm theo hai trục *bảo trì* và *sử dụng* trước, rồi mới tới dung lượng.

---

## 1. Vì sao lát này, và lát này là gì

Lát 5 của [7] theo [thứ tự đã chốt](../../../00-overview/roadmap.md): nạp ba báo cáo tài chính (cân đối kế toán · kết quả kinh doanh · lưu chuyển tiền tệ) của **1.523 doanh nghiệp niêm yết** vào `market.financial_statement` dạng dài, cộng danh sách file PDF gốc vào `market.financial_report_file`, cộng nạp từ điển 729 mã vào `market.metric_dictionary` để mã chỉ tiêu tra được ngay trong kho. Kích hoạt theo sự kiện `Earning` của lát 2, lưới quét sàn cuốn chiếu như lát 4, lượt điền đầu chạy như backfill giá của lát 3.

Đứng sau lát 4 vì lát 4 đã chốt xong khuôn *fetch → normalize → guard → store → job* và mẫu *ghi khi đổi + sổ kiểm*; lát này nhân bản từ `snapshot_*`, **đơn giản hơn lát 4 ở một chỗ**: không cần danh sách trắng để hash (§4.3).

## 2. Dữ kiện đã đo vs giả định *(§4.8 bước 0 — bắt buộc)*

### 2.1 Đã đo — 25 lời gọi thật 2026-09-04 và truy vấn kho production

| Dữ kiện | Số | Nguồn |
|---|---|---|
| Ba endpoint số liệu trả **trọn lịch sử**, không tham số lọc kỳ, không phân trang | tới 87 kỳ quý (VNM), 24 kỳ năm | [05](../../../10-sources/market/05-fiin-financial-statements.md) · [khảo sát §6](../../surveys/2026-09-04-bctc-endpoints/README.md) |
| `quarterReport` **chỉ** 1–4 (quý) và 5 (năm) — 0 dòng khác trên 5 mã có/không có kỳ quý | BAB · AAS · VNM · HPG · A32 | khảo sát §6.1 |
| `lengthReport` của `getFinancialReports` có **bảy** giá trị: 1–5, **6** (bán niên), **9** (9 tháng) | 28/307 dòng trên 4 mã | khảo sát §5.1 |
| Số khoá mỗi endpoint **cố định** bất kể loại hình: 235 / 180 / 150 | 4/4 mã | khảo sát §6.4 |
| Trong đó **8 khoá không phải mã chỉ tiêu**: `organCode` `ebit` `ebitDa` `operating` `otherAssetBank` `otherAssetNonBank` `otherLiabilties` `rtq29`; 549 mã từ điển xuất hiện, 7 mã từ điển (`cfa71` `cfa72` `isi173` `nob44` `nob65` `nob66` `nob151`) chưa gặp | 557 khoá phân biệt | khảo sát §6.2 |
| `GetBalanceSheet` trả **`bsI141` và `bsS134` viết hoa lẫn**; từ điển chữ thường | 4/4 mã + A32 | khảo sát §6.3 |
| `status` = `"Success"` 21/21; tài liệu 2026-08-10 ghi `0` | | khảo sát câu 2, §5.4 |
| `quarterly[]` và `yearly[]` xếp **mới → cũ**; số kỳ ba báo cáo **không bằng nhau** trên cùng mã (VNM 84 / 87 / 67) | | khảo sát §6.1, §6.4 |
| Mật độ ô có số 50–71 % vì response gộp bộ mã của **cả bốn loại hình** (`a` `b` `s` `i`); ước **≈ 21 triệu** dòng không null cho 1.523 mã | BAB 16.785 · AAS 21.194 · A32 3.710 ô non-null *(kể cả 8 khoá phi chỉ tiêu; A32 sau khi bỏ = 3.645)* | khảo sát câu 4 · [`count_rows.py`](count_rows.py) |
| Độ trễ 27–1.069 ms, payload 80–408 KB; chi phí trọn sàn do **giãn cách 0,5 s** quyết định: 4.569 + 1.523 lời gọi ≥ **51 phút** | | khảo sát câu 3, §6.4 |
| `sourceUrl` **trùng trong cùng response** (BID, BAB: hai `id`, một URL); `len(items) == totalCount` 4/4 | | khảo sát §5.2, §5.3 |
| Kho: 57.026 sự kiện `Earning`, `length_report` 1–5 đủ cả, `public_date` mới nhất 03/09; 1.140 issuer công bố trong 90 ngày; **1.137/1.523** issuer niêm yết có sự kiện trong 120 ngày ⇒ ~390 mã không có tín hiệu | | truy vấn 2026-09-04 17:20 |
| Vũ trụ: 1.438 `CT` · 42 `CK` · 30 `NH` · 13 `BH`; `financial_statement`, `financial_report_file`, `metric_dictionary` đều **0 dòng**; domain `market.fundamentals` đã có trong CHECK, chưa dùng | | nt |
| Role `dlck_etl` có `SELECT, INSERT, UPDATE, DELETE` trên mọi bảng `market`/`ops` kể cả bảng tạo sau (`ALTER DEFAULT PRIVILEGES`) | migration `0009` | đọc code — **vẫn phải kiểm bằng test dưới role**, §3.5 |

### 2.2 Giả định — CHƯA kiểm

1. Số liệu quá khứ **có** bị điều chỉnh hồi tố với tần suất đáng kể. Chỉ đo được sau hai mùa báo cáo; thiết kế §4.4 đúng dù giả định này đúng hay sai.
2. `getCorporateEarning` **sẽ** có ngày phát `length_report` 6/9 như `getFinancialReports`. Chưa từng thấy, nhưng nới CHECK trên `corporate_event` rẻ hơn một lượt `etl events` chết.
3. Mùa báo cáo, số issuer công bố trong **một ngày** không vượt ~300. Trần `MAX_TRIGGER = 300` cắt phần dư sang ngày sau, cũ nhất trước, nên sai giả định chỉ làm trễ, không mất.

## 3. Phạm vi

### 3.1 Trong phạm vi

- Job `python -m etl fundamentals` với bốn kind `bs` · `is` · `cf` · `reports`, cờ `--codes` · `--kinds` · `--max-minutes` · `--backfill` · `--stop-before-open`.
- Migration `0017` (§4.5).
- Nạp `metric_dictionary` từ [`field-dictionary.json`](../../../10-sources/market/field-dictionary.json) mỗi lượt (§4.6).
- Bảng sổ kiểm `ops.fundamentals_check`; bằng chứng đổi vào `staging.raw_payload`.

### 3.2 Ngoài phạm vi — phân ba loại *(§1.4)*

| Mục | Loại | Lý do |
|---|---|---|
| Tải file PDF về đĩa | **Loại có chủ đích** | Chỉ lưu metadata + URL; proxy tải là việc của `api` |
| `canonical_code` trong `financial_statement` | **Đã có đường khác** | Cột NULL không chặn, điền dần theo taxonomy riêng ([market-data-store §9](../../../20-design/market-data-store.md)) |
| Mã ngoài bảng `nob*` | **Đã kiểm — không có** | 0/7 mã `nob*` xuất hiện ở ba endpoint (khảo sát §6.2); `statement_type = 'NO'` trong CHECK giữ nguyên, không dùng |
| Khối `quarterly[]`/`yearly[]` trong `snapshot_daily` | **Đã có đường khác** | 25 mã / 9 kỳ, là lát vẽ biểu đồ; nguồn chuẩn là ba endpoint này |
| Tách ngưỡng guard theo kind | **Hoãn có lý do** | Cùng lý do lát 4: cần vài tháng số `changed_floor` thật |
| Đăng ký task Scheduler | **Loại có chủ đích** | Lịch thuộc lát 7; lát này chạy tay hoặc do lát 7 gọi |
| Phân biệt "chỉ tiêu không áp dụng cho loại hình" với "nguồn chưa có số" **trong bảng** | **Đã có đường khác** | Suy lúc đọc từ hậu tố mã (`metric_dictionary.code`) và `issuer.com_type_code` — §4.1 |

## 4. Quyết định theo §4.8 — phương án, lý do loại, điều kiện đảo ngược

### 4.1 Bỏ mọi null, kèm payload thô khi đổi *(chủ dự án chọn 2026-09-04)*

| Phương án | Tối ưu trục | Lý do loại |
|---|---|---|
| **A · bỏ mọi ô null** ✅ | bảo trì (không luật) · sử dụng (không lọc) | — chọn |
| B · lưu cả null | không mất thông tin | ~15–20 triệu dòng null vô nghĩa (bộ mã ngân hàng của công ty sản xuất); **mọi truy vấn** phải thêm `value IS NOT NULL` mãi mãi |
| C · bỏ null theo loại hình, giữ null trong bộ của mình | tách hai nghĩa của "không có" | cần luật ánh xạ `com_type_code → hậu tố`; **luật sai lúc ghi là mất dữ liệu vĩnh viễn** (holding có ngân hàng con, đổi loại hình). Điều C muốn lưu suy được lúc đọc bằng một JOIN |

Bổ sung rẻ: mỗi lần hash đổi, ghi thêm một bản `staging.raw_payload` (§5.4). Khi cần "nguồn thực sự trả gì cho kỳ này", mở payload; đó cũng là bằng chứng cho lát 6.

**Đảo ngược khi:** có tiêu thụ thật cần phân biệt hai nghĩa của "không có dòng" **mà** phép suy từ hậu tố + `com_type_code` cho kết quả sai trên dữ liệu thật ⇒ xét lại C với luật đã được số liệu chứng minh.

### 4.2 Trọn lịch sử, không cửa sổ *(tự chốt — đảo ngược rẻ)*

Nguồn luôn trả trọn; cửa sổ N kỳ là thêm một luật mà không tiết kiệm lời gọi. Đổi ý chỉ mất một lượt điền lại (~1 giờ). Không thuộc diện §4.8.

### 4.3 Trigger `Earning` + quét sàn cuốn chiếu, ghi khi đổi, **hash trọn payload** *(chủ dự án chọn 2026-09-04)*

| Phương án | Tối ưu trục | Lý do loại |
|---|---|---|
| **A · trigger + quét sàn nhịp 90 ngày, ghi khi đổi** ✅ | độ tươi, không đỉnh tải | — chọn |
| B · chạy trọn sàn mỗi mùa báo cáo | ít code nhất | dữ liệu cũ tới một quý; báo cáo rải nhiều tuần nên vẫn phải lặp; không biết mã nào đã tươi |
| C · chỉ trigger | ít lời gọi nhất | ~390 mã không có sự kiện trong 120 ngày **không bao giờ** được nạp |

Khác lát 4: hash tính trên **toàn bộ dòng đã chuẩn hoá** (§5.3), không danh sách trắng — ba endpoint không có trường nào tính từ giá (đã kiểm 557 khoá; `rtq29` là tỷ số của kỳ, đổi cùng kỳ). Bớt đúng cái luật hay hỏng nhất của lát 4.

**Đảo ngược khi:** `changed_floor / floor_compared` của một kind vượt 20 % ngoài mùa báo cáo hai lượt liên tiếp ⇒ có trường jitter, phải soi payload thô hai phiên bản để tìm, rồi mới nghĩ tới danh sách trắng.

### 4.4 Khi đổi: xoá trọn `(issuer, statement_type)` rồi chèn lại *(điểm duyệt §9.2)*

| Phương án | Lý do loại |
|---|---|
| **A · DELETE theo `(issuer_id, statement_type)` + INSERT, một giao dịch** ✅ | — chọn: một luật; điều chỉnh hồi tố, ô biến mất, ô đổi giá trị đều tự đúng |
| B · upsert từng ô + xoá ô vắng bằng anti-join | giữ `ingested_at` từng ô; đổi lại thêm hai câu SQL và một tập tạm; lợi ích ("ô này đổi khi nào") đã có ở `staging.raw_payload` |
| C · chỉ upsert, không xoá | ô nguồn rút lại vẫn nằm trong kho ⇒ **đọc sai** |

Với `reports`: upsert theo `source_id`, **không xoá** dòng vắng — danh sách PDF chỉ nên lớn lên, một entry biến mất không phải bằng chứng file không tồn tại.

**Đảo ngược khi:** có tiêu thụ thật cần `ingested_at` theo ô ⇒ chuyển B, dữ liệu cũ dùng được nguyên.

### 4.5 `financial_report_file` khoá theo `source_id` *(chủ dự án chọn 2026-09-04)* — migration `0017`

| Phương án | Lý do loại |
|---|---|
| **A · thêm `source_id` UNIQUE, `source_url` thành cột thường** ✅ | — chọn: `id` là định danh chính chủ của nguồn, upsert idempotent không cần nghĩ |
| B · giữ `source_url UNIQUE`, khử trùng khi chuẩn hoá | phải chọn dòng giữ; nguồn coi là hai mà ta coi là một, im lặng |
| C · khoá ghép (issuer, năm, kỳ, tiêu đề) | `_HN`/`_RL` cùng kỳ chỉ khác tiêu đề, đụng khi nguồn đổi cách đặt tên |

```sql
-- 0017_fundamentals.py
ALTER TABLE market.financial_report_file
  ADD COLUMN source_id bigint;                       -- id của nguồn
UPDATE market.financial_report_file SET source_id = file_id WHERE source_id IS NULL;  -- bảng đang 0 dòng; giữ migration chạy được trên kho có dữ liệu
ALTER TABLE market.financial_report_file
  ALTER COLUMN source_id SET NOT NULL,
  ADD CONSTRAINT financial_report_file_source_id_key UNIQUE (source_id),
  DROP CONSTRAINT financial_report_file_source_url_key,
  DROP CONSTRAINT financial_report_file_length_report_check,
  ADD CONSTRAINT financial_report_file_length_report_check
      CHECK (length_report IN (1,2,3,4,5,6,9));       -- 1–4 quý · 5 năm · 6 bán niên · 9 chín tháng (đo 2026-09-04)
ALTER TABLE market.corporate_event
  DROP CONSTRAINT corporate_event_length_report_check,
  ADD CONSTRAINT corporate_event_length_report_check
      CHECK (length_report IN (1,2,3,4,5,6,9));       -- gỡ mìn cho `etl events`; nguồn chưa từng phát 6/9 ở đây

-- financial_statement GIỮ CHECK (length_report BETWEEN 1 AND 5): ba endpoint số liệu chỉ phát 1–5
-- (đo 2026-09-04, 5 mã). Nếu một ngày phát 6/9, normalize xếp bad_shape và guard báo — không lặng lẽ nạp
-- dòng bán niên làm sai mọi phép cộng quý.

CREATE TABLE ops.fundamentals_check (
  issuer_id    bigint NOT NULL REFERENCES market.issuer,
  kind         text   NOT NULL CHECK (kind IN ('bs','is','cf','reports')),
  checked_at   timestamptz NOT NULL,
  payload_hash text   NOT NULL,
  changed_at   timestamptz,
  found_by     text   NOT NULL CHECK (found_by IN ('event','floor')),
  PRIMARY KEY (issuer_id, kind)
);
CREATE INDEX ON ops.fundamentals_check (kind, checked_at);   -- ORDER BY của due_list
```

Tên ràng buộc lấy theo tên Postgres tự đặt cho CHECK/UNIQUE không tên trong `0004`; plan phải **đọc tên thật** bằng `\d` trước khi viết `DROP CONSTRAINT`, không đoán. `downgrade()` làm ngược, riêng CHECK về `BETWEEN 1 AND 5` chỉ khi không còn dòng 6/9.

### 4.6 Từ điển nạp trong job, không migration seed *(điểm duyệt §9.4)*

| Phương án | Lý do loại |
|---|---|
| **A · upsert 729 dòng ở đầu mỗi lượt** ✅ | — chọn: file trong repo là nguồn sự thật; trích lại bundle (lát 6) chỉ cần đổi file, không cần migration mới; 729 dòng là ~50 ms |
| B · migration seed như `0013` ngành | tiền lệ có, nhưng mỗi lần trích lại bundle là một migration; ngành là quyết định *của người*, còn từ điển là *số đo của nguồn* — hai bản chất khác nhau |

Ánh xạ: `dictionary = 'field_dictionary'` · `code` = khoá JSON (đã chữ thường) · `name_vi` = `ten_vi` · `name_en` = `ten_en` · `unit` = `don_vi_du_lieu` · `value_min/max` = `dai_gia_tri[0]/[1]` (chỉ nhóm tỷ số có). Cả hai nhóm `chi_tieu_bao_cao_tai_chinh` (556) và `chi_tieu_ty_so_va_thi_truong` (173) đều nạp, vì `rtq29` nằm trong response BCTC.

## 5. Job `python -m etl fundamentals`

### 5.1 Khuôn — y `snapshot_job.run`

`open_run` → `load_dictionary` → `due_list` → fetch → normalize → **guard trước commit** → `apply` trong một giao dịch → `close_run` → `upsert_domain_state('market.fundamentals')`. Guard từ chối ⇒ `raise` trong `engine.begin()` để rollback, bằng chứng ở giao dịch riêng, `etl_run.status = 'failed'`, exit 1. Không re-crawl giá. `pool_pre_ping` như lát 3/4 vì lượt backfill sống qua giấc ngủ 02:00.

Ba chế độ, một đường code, khác nhau ở `due_list`:

| Chế độ | `due_list` | Dùng khi |
|---|---|---|
| thường | trigger + quét sàn theo quota | hằng ngày (lát 7 gọi), sau `events` 18:10 và sau `snapshot` |
| `--backfill` | **bỏ quota**: mọi `(issuer, kind)` chưa có dòng `fundamentals_check`, `ORDER BY issuer_id`, cộng trigger như thường | lượt điền đầu, chạy nhiều đêm với `--max-minutes` / `--stop-before-open` (08:45 ngày giao dịch kế, y lát 3); con trỏ là `checked_at`, giết giữa chừng không mất chỗ |
| `--codes` | tập ép, mọi kind, bỏ nhịp và quota; **không** đụng mốc nước, **không** tác dụng phụ toàn cục (bài học 1c lát 4) | chạy thử dưới quyền production, kéo lại tay |

### 5.2 `fundamentals_fetch` — I/O thuần

- URL: `FIIN_FUND/FinancialStatement/Get{BalanceSheet|IncomeStatement|CashFlow|FinancialReports}?OrganCode={organ_code}&language=vi`; header `Origin: https://fiinapp.bvsc.com.vn`.
- Giãn cách ≥ 0,5 s giữa hai lần bắt đầu lời gọi; timeout **30 s** mọi kind (payload tới 408 KB); retry 3, backoff 2/4/8 s; **exception vận chuyển đi cùng đường với response xấu** (bài học `e7f80f6`).
- `classify(kind, http, text)` thuần, ba nhánh: `ok` khi HTTP 200, JSON hợp lệ, `status ∈ {0, "Success"}`, và `items[0]` có khoá gốc (`quarterly` **và** `yearly` với ba báo cáo; `items` là list với `reports`) · `retry` khi HTTP ≠ 200, JSON hỏng, `status == "Failed"`, exception · `bad_shape` còn lại.
- Hết lượt thử ⇒ mã đó **chưa kiểm**: không ghi, không đụng sổ kiểm, đếm `failed`.

### 5.3 `fundamentals_normalize` — thuần, không I/O

```
NON_METRIC = {"organCode", "ebit", "ebitDa", "operating",
              "otherAssetBank", "otherAssetNonBank", "otherLiabilties", "rtq29"}
STATEMENT  = {"bs": "BS", "is": "IS", "cf": "CF"}

rows(kind, item) -> list[Row]
  với bs/is/cf: duyệt item["quarterly"] + item["yearly"]; mỗi bản ghi:
    year = yearReport, length = quarterReport  (phải ∈ 1..5, không thì raise BadShape)
    với mỗi (k, v) ngoài {yearReport, quarterReport} ∪ NON_METRIC:
      v is None  -> bỏ
      còn lại    -> Row(year, length, STATEMENT[kind], k.lower(), Decimal(v))
  với reports: mỗi item: Row(source_id=id, year=yearReport, length=lengthReport ∈ {1..6, 9},
                             title, url=sourceUrl); thiếu id/URL -> BadShape

payload_hash(rows) = sha256(json.dumps(sorted(rows as tuples), separators=(",",":")))
```

Bốn tính chất phải có test: đổi thứ tự khoá hay thứ tự kỳ trong response ⇒ hash **không đổi**; đổi một giá trị ⇒ hash **đổi**; thêm một ô null ⇒ hash **không đổi**; `bsI141` ra `bsi141`. Trùng kỳ `(year, length)` trong cùng mảng ⇒ `BadShape` (đo: 0 trùng trên 4 mã, nhưng khoá chính sẽ nổ nếu có).

### 5.4 `fundamentals_store`

**`_UNIVERSE`** dùng lại nguyên văn của `snapshot_store` (issuer có security `listed` + `stock`, `organ_code` từ `issuer_external_id`).

**`due_list(conn, watermark, kinds, codes, backfill, quota, cadence, max_trigger)`**, khử trùng theo `(issuer_id, kind)`:

```
A · trigger   corporate_event.event_type = 'Earning' AND public_date > watermark
              -> cả bốn kind; trần MAX_TRIGGER = 300 issuer/lượt, public_date CŨ NHẤT trước;
              cold start (watermark = 1900-01-01) bỏ qua nhánh A — quét sàn/backfill tự phủ
B · quét sàn  mỗi kind: chưa có dòng fundamentals_check HOẶC checked_at < now() - 90 ngày
              ORDER BY checked_at NULLS FIRST, issuer_id   LIMIT quota[kind]
B' backfill   như B nhưng KHÔNG LIMIT, chỉ lấy dòng chưa có (checked_at IS NULL)
```

| Kind | Nhịp | Quota/ngày | Phủ trọn sàn sau |
|---|---|---|---|
| `bs` · `is` · `cf` · `reports` | 90 ngày | **20** mỗi kind | 77 ngày |

Ngân sách ngày thường ≈ **80** lời gọi + trigger; mùa báo cáo trần **1.200** lời gọi/ngày ≈ 10 phút. Lượt `--backfill` trọn sàn: 6.092 lời gọi ≈ **1–1,5 giờ** (giãn cách + độ trễ trung vị ~0,4 s), một buổi tối là đủ nếu máy không ngủ; ngủ giữa chừng thì tối sau chạy tiếp.

**`apply(conn, fetched, run_date)`** — với mỗi kết quả `ok`:

1. `rows = normalize.rows(...)`, `h = payload_hash(rows)`; đọc `payload_hash` cũ ở `fundamentals_check`.
2. **`rows` rỗng mà đã có dòng cũ** ⇒ đếm `empty`, **không** ghi, **không** đụng sổ kiểm (rỗng không bao giờ xoá dữ liệu). `rows` rỗng và chưa có dòng cũ (mã UPCOM chưa có báo cáo) ⇒ ghi sổ kiểm bình thường với hash của rỗng.
3. Hash trùng ⇒ `unchanged`, chỉ tiến `checked_at`.
4. Hash đổi (hoặc `first`):
   - `bs`/`is`/`cf`: `DELETE FROM market.financial_statement WHERE issuer_id = :i AND statement_type = :t` rồi `INSERT` mọi dòng (`executemany`, lô 5.000), cùng giao dịch.
   - `reports`: `INSERT … ON CONFLICT (source_id) DO UPDATE SET year_report, length_report, title, source_url, ingested_at = clock_timestamp()`.
   - `staging.raw_payload`: một dòng `source = 'fundamentals'`, `endpoint_key = 'fundamentals:<kind>:<organCode>'`, `content_type = 'json'`, `payload` = response thô, `meta = {"hash": h, "run_id": …, "rows": n}`. Đây là lịch sử điều chỉnh, không xoá.
5. Upsert `fundamentals_check` với `clock_timestamp()` (không `now()` — bài học sổ kiểm lát 4), `changed_at` chỉ đổi khi `changed`.

`first` không tính vào `changed` (cold start không được tự vi phạm chốt (i)).

**Mốc nước** `= max(public_date)` của các sự kiện `Earning` đã phục vụ, **chỉ tiến khi lượt không có target hỏng/sai hình dạng/rỗng**; lượt `--codes` không đụng mốc. Chỉ đo `public_date`, không `exright_date` — hai đồng hồ, đừng trộn (lát 4).

**`load_dictionary(conn)`**: đọc `field-dictionary.json` theo đường dẫn tương đối repo (`docs/10-sources/market/`), upsert 729 dòng theo §4.6; sai hình dạng file ⇒ raise trước khi fetch (hợp đồng khởi động, §3.5).

### 5.5 `fundamentals_guard` — thuần, đánh giá trước commit

| Chốt | Ngưỡng | Bắt cái gì |
|---|---|---|
| (i) tỷ lệ đổi của nhóm **quét sàn** (bỏ `first`) | > 20 %, `MIN_SAMPLE` 20 | nguồn đổi cách tính/thang, trường jitter lọt vào hash |
| (ii) tỷ lệ lời gọi hỏng | > 20 % tổng, `MIN_SAMPLE` 20 | nguồn sự cố |
| (iii) tỷ lệ `bad_shape` | > 5 % | nguồn đổi hình dạng, hoặc bắt đầu phát `quarterReport` 6/9 |
| (iv) tỷ lệ `empty` (rỗng trên mã từng có dữ liệu) | > 5 % | nguồn trả rỗng hàng loạt |
| (v) danh sách tới hạn rỗng | — | **không phải lỗi**: `success` với `checked = 0` |

⚠️ Chốt (i) **trong mùa báo cáo** sẽ chạm ngưỡng theo cách vận hành bình thường nếu quét sàn rơi vào đúng nhóm vừa có kỳ mới mà trigger chưa bắn (lịch sót 3,6 % `Earning`). Xử lý y lát 4: đọc `stats.tally`, chạy tay `--kinds` để đi tiếp, ghi số vào ledger; **không** nới ngưỡng ở lát này.

### 5.6 Lịch và vận hành

Không đăng ký task (§3.2). Chạy tay: `uv run python -m etl fundamentals`. Vị trí trong bảng lịch lát 7: **sau `events` 18:10 và sau `snapshot`**, vì trigger đọc bảng `events` vừa ghi. Lượt điền đầu: `--backfill --stop-before-open` các buổi tối cho tới khi `stats.remaining = 0`.

## 6. Seam test *(chốt cùng plan — §4.5.2)*

Expected từ mẫu thật trong `samples/` của khảo sát hoặc giải tay, **không tính lại theo cách code tính** (§4.5.3).

| Seam | Ca phải có |
|---|---|
| `classify` | `status=0` → ok · `"Success"` → ok *(mẫu A32)* · `"Failed"` → retry · exception → retry · thiếu `quarterly` → bad_shape · `reports` với `items` không phải list → bad_shape |
| `rows` | mẫu A32: **1.749 / 980 / 916 = 3.645** dòng ba báo cáo — đếm độc lập bằng [`count_rows.py`](count_rows.py) *(khảo sát câu 4 ghi 3.710 vì đếm cả 65 ô của 8 khoá phi chỉ tiêu)*; một literal cụ thể như `bsa1` 2025 của A32 đọc tay từ mẫu; `bsI141` → `bsi141`; `quarterReport = 6` → BadShape; `null` bị bỏ; `organCode` bị bỏ |
| `payload_hash` | bốn tính chất §5.3 |
| `due_list` | trigger-only · floor-only · trùng ⇒ một dòng · quota chặn · `NULLS FIRST` · cold start bỏ trigger · `--backfill` bỏ LIMIT nhưng chỉ lấy `checked_at IS NULL` · `--codes` không đụng trigger |
| `guard.check` | qua · (i)–(iv) đỏ · `first` không tính vào (i) · rỗng vẫn ok |
| `apply` | first ⇒ n dòng; không đổi ⇒ 0 dòng nhưng `checked_at` tiến; **đổi một giá trị ⇒ đúng một dòng khác giá trị, số dòng bằng cũ**; **một ô biến mất ⇒ số dòng giảm 1**; `empty` ⇒ dữ liệu cũ nguyên, `checked_at` **không** tiến; `reports` vắng entry ⇒ không xoá; chạy lại ⇒ idempotent |
| `load_dictionary` | 729 dòng; `bsa1` unit `VND`; `rtq29` có `value_min/max`; chạy hai lần ⇒ 729 |
| quyền | `test_fundamentals_works_under_etl_role`: `SET LOCAL ROLE dlck_etl` rồi **DELETE + INSERT** `financial_statement`, upsert `fundamentals_check`, upsert `metric_dictionary`, insert `raw_payload` |
| migration | `length_report = 6` chèn được vào `financial_report_file` và `corporate_event`; **không** chèn được vào `financial_statement`; `source_id` trùng bị từ chối, `source_url` trùng được nhận |

Test đụng CSDL dùng chung phải **tự dập nền** và lọc theo mã của chính test (bài học 3 lát 4).

## 7. Tiêu chí nghiệm thu

| | Nội dung | Bằng chứng phải dán |
|---|---|---|
| AC1 | Toàn bộ test xanh | số test trước (523 + 2 skipped) / sau |
| AC2 | `--codes A32,BAB,AAS` → `financial_statement` **A32 = 3.645** dòng; BAB và AAS bằng đúng số [`count_rows.py`](count_rows.py) đếm trên payload thô của chính lượt (lấy từ `staging.raw_payload`; khảo sát ghi 16.785 / 21.194 là **kể cả** 8 khoá phi chỉ tiêu nên sẽ lớn hơn); `financial_report_file` **8 / 106 / 48** (đếm theo `id` trong `samples/`, BAB có 105 URL phân biệt); `metric_dictionary` 729 | truy vấn đếm theo issuer và theo bảng, cạnh output của `count_rows.py` — hai phép đếm viết riêng, không chung code |
| AC3 | Lượt `--backfill --max-minutes 30` vào kho production | số lời gọi · thời gian · retry · 0 tín hiệu chặn · `stats.remaining` giảm đúng số target đã kiểm |
| AC4 | Chạy lại `--codes` cùng tập cùng ngày | `unchanged = 12`, `rows_written = 0`, 0 dòng `raw_payload` mới |
| AC5 | Điều chỉnh hồi tố mô phỏng: đổi một giá trị trong fixture rồi `apply` | đúng 1 dòng khác, 1 dòng `raw_payload` mới với hash mới |
| AC6 | Ép hỏng hàng loạt ⇒ `failed`, 0 dòng ghi, sổ kiểm không nhúc nhích | `etl_run` + `staging.raw_payload` bằng chứng |
| AC7 | Lượt thường trên kho đã có dữ liệu: trigger theo `public_date > watermark` bắn đúng mã vừa công bố | so danh sách target với `corporate_event` |
| AC8 | Mọi lượt trên chạy dưới **credential production** (`ETL_DATABASE_URL`, role `dlck_etl`) trước khi coi là xong | dòng lệnh + exit code |

AC3 mở rộng thành lượt điền trọn sàn (6.092 lời gọi) trong vài buổi tối; ledger ghi từng lượt: target, lời gọi, `remaining`.

## 8. Checklist tài liệu sống — cùng lượt với code *(§1.6, §1.7)*

- [ ] [roadmap.md](../../../00-overview/roadmap.md): lát 5 ✅ + viết **"Điểm vào cho lát 6"**; số test; §0.
- [ ] [market-data-store.md](../../../20-design/market-data-store.md) §4.1/§4.2 (ngân sách BCTC hằng ngày ~80 + trigger), §5.4 (bảng thật, `fundamentals_check`, luật bỏ null và suy lúc đọc).
- [ ] [00-conventions.md §10.1](../../../10-sources/market/00-conventions.md): dòng BCTC từ "theo quý, rải" thành nhịp thật.
- [ ] [database/README.md](../../../../database/README.md): migration head `0017`, test schema mới.
- [ ] [backend/README.md](../../../../backend/README.md): mục "Chạy job fundamentals", ba chế độ, cảnh báo chốt (i) mùa báo cáo.
- [ ] [90-records/README.md](../../README.md): dòng plan này.
- [ ] `ledger.md` cùng thư mục, commit theo mốc.

## 9. Điểm cần chủ dự án duyệt tường minh

1. **Quota 20/kind/ngày, nhịp 90 ngày** — phủ trọn sàn ở chế độ thường mất 77 ngày; lượt điền đầu dùng `--backfill` nên con số này chỉ là nhịp kiểm lại.
2. **Đổi là xoá rồi chèn lại** cả báo cáo của một issuer — mất `ingested_at` từng ô, đổi lại không có luật diff; lịch sử đổi nằm ở `staging.raw_payload`.
3. **`financial_statement` không nới CHECK** — 6/9 ở đây là `bad_shape`, job sẽ báo chứ không nạp.
4. **Từ điển nạp trong job mỗi lượt**, không migration seed.
5. **Rỗng không xoá**: mã từng có dữ liệu mà nguồn trả rỗng thì giữ nguyên kho và không đánh dấu đã kiểm, để lượt sau thử lại.
