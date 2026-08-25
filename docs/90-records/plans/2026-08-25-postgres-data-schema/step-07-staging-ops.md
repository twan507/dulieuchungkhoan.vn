# Bước 7 — Hậu trường: landing zone và vận hành

**Trạng thái:** ✅ chốt 2026-08-25 (chủ dự án chốt sau khi bước này qua mục soi riêng của review vòng 3; kèm điều kiện: chạy vòng review 4 toàn cục trước khi sang plan) · **Phụ thuộc:** bước 1–6 (✅) · **Phạm vi:** hai schema không phục vụ người dùng cuối — `staging` (kho đồ thô) và `ops` (trạng thái hệ thống). Role của `api` **không thấy** hai schema này (phân quyền bước 1).

---

## 1. `staging` — kho payload thô

```sql
CREATE TABLE staging.raw_payload (
  payload_id   bigint generated always as identity PRIMARY KEY,
  source       text NOT NULL,            -- 'wichart' | 'sbv' | 'fred' | 'lbma' | 'binance' | 'yahoo'…
  endpoint_key text NOT NULL,            -- định danh lời gọi: key/series/URL
  fetched_at   timestamptz NOT NULL DEFAULT now(),
  content_type text NOT NULL CHECK (content_type IN ('json','html','text')),
  payload      jsonb,                    -- json → payload; html/text → body
  body         text,
  meta         jsonb,                    -- HTTP status, độ dài…; khoá 'hash' giữ hash nội dung
                                         -- cho chính sách "lưu khi đổi" (khoá đặt tên cố định)
  CHECK ( (content_type = 'json' AND payload IS NOT NULL AND body IS NULL)
       OR (content_type IN ('html','text') AND body IS NOT NULL AND payload IS NULL) )
  -- Review vòng 2, M5: CHECK cũ (payload OR body) cho phép content_type='json' mà chỉ có body.
);
CREATE INDEX ON staging.raw_payload (source, endpoint_key, fetched_at);
```

Vai trò — "Bronze layer" theo chuẩn kho dữ liệu, ba việc:

1. **Bảo hiểm đổi-schema:** nguồn đổi tên trường → sửa adapter rồi **dựng lại bảng chuẩn từ đồ thô đã lưu**, không crawl lại. (Bảng `market` có `raw jsonb` inline riêng vì payload 1-ứng-1 dòng; các nguồn còn lại payload là *một tài liệu chứa nhiều dòng* nên để staging.)
2. **Cứu dữ liệu không tải lại được:** OMO chỉ hiện phiên mới nhất (HTML ~414 KB/phiên — markup viết tay, đổi là mất); WiChart cửa sổ trượt 2 năm. Với hai nguồn này, lưu thô là **bắt buộc**, không phải tuỳ chọn.
3. **Trọng tài khi nghi ngờ:** số trong bảng chuẩn lệch → mở đồ thô cùng ngày xem lỗi ở nguồn hay ở adapter.

Ngữ nghĩa ghi: **append-only tuyệt đối** — mỗi lần crawl một dòng mới, không sửa không xoá. Không retention drop (kho là tài sản).

**Chính sách lưu — MỘT luật** *(vòng 2 đặt hai lớp; vòng 3 + tự duyệt lại của kiến trúc sư gộp thành một, đồng thời vá hai lỗ hổng B7-4/B7-7)*:

> **Lưu khi hash nội dung đổi so lần lưu gần nhất của cùng `(source, endpoint_key)`** — hash giữ ở `meta` khoá `'hash'`. Và **chỉ nhận payload đã qua kiểm hình thức** của adapter (độ dài, chuỗi mốc) — body WAF 246 byte của SBV là đồ giả, vào staging sẽ phá vai trò trọng tài; đồ lỗi đi vào `etl_run.error`.

Một luật phủ đúng mọi ca: OMO/WiChart payload đổi mỗi lần crawl → tự nhiên **lưu mọi lần** (đúng yêu cầu nguồn không tải lại được); LBMA cuối tuần trả y hệt → bỏ, hết rác full-history 0,9 MB/lời gọi; và **BCTC FiinTrade** (191–374 KB một tài liệu sinh hàng trăm dòng — đúng ca "một tài liệu nhiều dòng" phải để staging, bản trước bỏ sót cả nguồn lớn nhất kho — vòng 3, B7-4): lần re-crawl mùa báo cáo có **restate** → hash đổi → **giữ được cả bản trước lẫn sau restate** — vá đúng lỗ hổng G1 (FiinTrade không có API vintage, bản trước restate vốn mất vĩnh viễn). Bằng chứng "đã crawl ngày đó" không cần dòng staging trùng — nó nằm ở `ops.etl_run`.

Danh sách `source` vì vậy gồm **cả `fiintrade`/`bvsc`** (payload đa-dòng: BCTC, danh bạ, sự kiện…), không chỉ nhóm macro/global. **Loại trừ tường minh: tin tức không đi qua staging** — nội dung đã bóc trong `news.article_revision.content` chính là bản lưu bền (không tải lại được vì link rot — news-pipeline §9.1), còn HTML thô 97–446 KB/trang đã quyết không lưu (§9.2, gấp 18–146 lần text sạch) *(vòng 3, B7-5)*.

Dung lượng WiChart mỗi payload **chưa đo** — ghi nhận khi chạy thật qua `ops`, xét nén hay gộp khi có số thật, không đoán trước.

## 2. `ops` — năm bảng trạng thái *(ba bảng gốc + hai bổ sung ở vòng 3)*

```sql
CREATE TABLE ops.data_domain_state (      -- CÔNG TẮC miền × nguồn: "phần thiếu kệ nó, phần đủ cứ chạy"
  domain          text NOT NULL CHECK (domain IN
                    ('market.reference','market.price','market.fundamentals',
                     'market.events','market.scores','market.index_stat',
                     'macro.indicator','macro.omo','asset','news')),
                  -- danh sách ĐÓNG do mình định nghĩa → CHECK theo quy ước bước 1 §3
                  -- (vòng 3, M-8; 'market.scores' = snapshot/screener — tầng C "mất là mất")
  source          text NOT NULL,
  status          text NOT NULL CHECK (status IN ('active','frozen','migrating')),
  last_success_at timestamptz,
  watermark       text,                   -- điểm đã nạp tới (ngày/trang/id — tuỳ miền)
  note            text,
  PRIMARY KEY (domain, source)
);

CREATE TABLE ops.contract_snapshot (      -- giám sát hợp đồng dữ liệu — nguồn không có versioning
  endpoint       text NOT NULL,
  checked_at     timestamptz NOT NULL DEFAULT now(),
  field_set_hash text,                    -- hash danh sách trường đã sắp — trường biến mất/mới là biết
  field_types    jsonb,                   -- tên trường → kiểu (số thành chuỗi là biết)
  record_count   int,
  coverage_pct   numeric,                 -- độ phủ trên bộ mã mẫu cố định 51 mã
  p95_latency_ms int,
  sample_payload jsonb,
  PRIMARY KEY (endpoint, checked_at)
);

CREATE TABLE ops.series_health (          -- độ tươi Ở CẤP SERIES — vòng 3, B7-2: contract_snapshot
  source       text NOT NULL,             -- theo endpoint KHÔNG bắt được kiểu chết-từng-series
  external_key text NOT NULL,             -- (xang_dau sống mà RON 95 chết 76 ngày; be_tong_mac_300
  external_sub text NOT NULL DEFAULT '',  --  có điểm mới hằng tháng nhưng giá đứng 407 ngày)
  checked_at   timestamptz NOT NULL DEFAULT now(),
  last_obs_date     date,
  days_since_change smallint,             -- giá đứng bao nhiêu ngày (bắt carry-forward/đóng băng)
  gap_median_days   numeric,              -- so với freq khai để bắt FREQMIS
  note         text,
  PRIMARY KEY (source, external_key, external_sub, checked_at)
);

CREATE TABLE ops.source_build (           -- hash bundle JS của nguồn — cảnh báo sớm "họ vừa deploy"
  source      text NOT NULL,              -- (P3, §7.1 kho dữ liệu). Bảng riêng vì nhét vào
  checked_at  timestamptz NOT NULL DEFAULT now(),  -- contract_snapshot.field_set_hash là phá nghĩa
  bundle_hash text NOT NULL,              -- cột đó (vòng 3, B7-1). Baseline: BVSC '3241ea7a',
  urls        jsonb,                      -- FiinTrade '2.d5375412'/'main.876ed868' (đo 2026-08-15)
  PRIMARY KEY (source, checked_at)
);

CREATE TABLE ops.etl_run (                -- nhật ký từng lần chạy job
  run_id      bigint generated always as identity PRIMARY KEY,
  job         text NOT NULL,              -- 'market.price_daily' | 'macro.omo_crawl'…
  started_at  timestamptz NOT NULL DEFAULT now(),
  finished_at timestamptz,
  status      text NOT NULL DEFAULT 'running' CHECK (status IN ('running','success','failed')),
  stats       jsonb,                      -- số dòng ghi, số lời gọi, dải ngày…
  error       text
);
CREATE INDEX ON ops.etl_run (job, started_at DESC);
```

- **`data_domain_state`** thi hành mô hình đã chốt ở kiến trúc: mất WiChart → gạt `frozen` đúng các dòng `(*, 'wichart')`, mọi miền khác chạy tiếp; đổi nguồn một miền → `migrating` trong lúc chạy song song. View đọc phải chịu `NULL`/khoảng trống, không lỗi. Đây cũng là công tắc của cơ chế tháo lắp nguồn (README).
- **`contract_snapshot`** là phòng vệ duy nhất trước nguồn không cam kết (không versioning, không changelog, kiểu hỏng nguy hiểm nhất là *HTTP 200 + dữ liệu sai*): chạy trước phiên mỗi ngày trên bộ mã mẫu, so với baseline — trường đổi, kiểu đổi, độ phủ tụt, giá trị bất thường. Kèm theo dõi hash bundle JS của nguồn (cảnh báo sớm "họ vừa deploy") — chi tiết bộ kiểm ở [kho dữ liệu §7.1](../../../20-design/market-data-store.md), gồm cả 7 phép kiểm đơn vị từ điển chỉ tiêu (bước 3).
- **`etl_run`** trả lời hai câu hỏi vận hành hằng ngày: *job nào chưa chạy hôm nay* và *job nào đang đỏ* — nguyên liệu cho cảnh báo mức P1/P2/P3 đã thiết kế.
- **Ngữ nghĩa ghi** *(M8 + vòng 3)*: `data_domain_state` UPSERT theo `(domain, source)`; `contract_snapshot` · `series_health` · `source_build` append-only (mỗi lần check một dòng — lịch sử baseline); `etl_run` chèn lúc bắt đầu, UPDATE đúng dòng đó lúc kết thúc.
- **Cảnh báo P1/P2/P3: TÍNH LÚC ĐỌC, không có bảng alert** *(vòng 3, B7-3 — chốt để người sau không đi tìm bảng không tồn tại)*: điều kiện từng mức đã định nghĩa ở [kho dữ liệu §7.1](../../../20-design/market-data-store.md), nguyên liệu là bốn bảng trên; kênh phát báo là việc của vận hành (roadmap `40-operations/` sau này), không phải của schema.

## 3. Điểm cần duyệt ở bước này

- [ ] **Kho đồ thô một bảng chung** append-only, không xoá — bảo hiểm đổi-schema + cứu nguồn không tải lại được — đồng ý?
- [ ] **Công tắc miền × nguồn** (`data_domain_state`) với ba trạng thái active/frozen/migrating — đồng ý?
- [ ] **Giám sát hợp đồng** lưu snapshot hằng ngày trong DB (`contract_snapshot`) để so baseline — đồng ý?
- [ ] **Nhật ký job** (`etl_run`) làm nguồn cho cảnh báo — đồng ý?

## 4. Kiểm chứng của bước này (seam)

1. `raw_payload`: chèn `content_type='json'` kèm `body` (hoặc thiếu `payload`) → lỗi CHECK; `'html'` thiếu `body` → lỗi CHECK *(CHECK đã siết ở M5 — test đuổi theo)*; chèn HTML OMO (literal rút gọn) rồi đọc lại nguyên văn.
1b. Policy hash là logic ETL (test ở plan ETL, không phải constraint): hai dòng cùng `(source, endpoint_key)` khác hash → 2 dòng hợp lệ trong bảng.
2. `data_domain_state`: `status='paused'` → lỗi CHECK; UPSERT `(domain, source)` đổi `frozen` → 1 dòng, trạng thái mới.
3. `etl_run`: vòng đời `running` → `success` cập nhật được `finished_at`; truy vấn "lần chạy gần nhất của job X" ra đúng dòng (literal 2 lần chạy).
4. `contract_snapshot`: hai lần check cùng endpoint khác `checked_at` → 2 dòng (lịch sử baseline giữ nguyên).

## 5. Khép vòng spec

Chốt bước này là **đủ DDL cho toàn bộ `postgres-data` phần sự thật** (bước 1–7). Còn lại:

- **Bước 8** — tầng tự tính (chỉ số ngành, chỉ báo kỹ thuật, DXY dựng lại): nguyên tắc đã chốt ở README, danh sách bảng + công thức chốt khi có dữ liệu thật.
- **Bộ view ngữ nghĩa cho chatbot** (`v_financial_ratios` · `v_price_adjusted` · `v_company_profile` · `v_corporate_calendar` · `v_money_flow` — kho dữ liệu §6.2): thuộc tầng L3, làm ở roadmap [13] sau khi có dữ liệu — nền đã đủ (từ điển chỉ tiêu, canonical id, index cắt ngang) *(ghi để khép vòng không bỏ sót — vòng 3, M-6)*.
- Sau đó: **`plan.md`** bẻ task thực thi (khung Alembic → migration theo bước → seed → test seam), theo quy trình §4.1.
