# Bước 7 — Hậu trường: landing zone và vận hành

**Trạng thái:** 🟡 chờ duyệt · **Phụ thuộc:** bước 1–6 (✅) · **Phạm vi:** hai schema không phục vụ người dùng cuối — `staging` (kho đồ thô) và `ops` (trạng thái hệ thống). Role của `api` **không thấy** hai schema này (phân quyền bước 1).

---

## 1. `staging` — kho payload thô

```sql
CREATE TABLE staging.raw_payload (
  payload_id   bigint generated always as identity PRIMARY KEY,
  source       text NOT NULL,            -- 'wichart' | 'sbv' | 'fred' | 'lbma' | 'binance' | 'yahoo'…
  endpoint_key text NOT NULL,            -- định danh lời gọi: key/series/URL
  fetched_at   timestamptz NOT NULL DEFAULT now(),
  content_type text NOT NULL CHECK (content_type IN ('json','html','text')),
  payload      jsonb,                    -- một trong hai cột, tuỳ content_type
  body         text,
  meta         jsonb,                    -- HTTP status, độ dài, hash… tuỳ adapter
  CHECK (payload IS NOT NULL OR body IS NOT NULL)
);
CREATE INDEX ON staging.raw_payload (source, endpoint_key, fetched_at);
```

Vai trò — "Bronze layer" theo chuẩn kho dữ liệu, ba việc:

1. **Bảo hiểm đổi-schema:** nguồn đổi tên trường → sửa adapter rồi **dựng lại bảng chuẩn từ đồ thô đã lưu**, không crawl lại. (Bảng `market` có `raw jsonb` inline riêng vì payload 1-ứng-1 dòng; các nguồn còn lại payload là *một tài liệu chứa nhiều dòng* nên để staging.)
2. **Cứu dữ liệu không tải lại được:** OMO chỉ hiện phiên mới nhất (HTML ~414 KB/phiên — markup viết tay, đổi là mất); WiChart cửa sổ trượt 2 năm. Với hai nguồn này, lưu thô là **bắt buộc**, không phải tuỳ chọn.
3. **Trọng tài khi nghi ngờ:** số trong bảng chuẩn lệch → mở đồ thô cùng ngày xem lỗi ở nguồn hay ở adapter.

Ngữ nghĩa ghi: **append-only tuyệt đối** — mỗi lần crawl một dòng mới, không sửa không xoá. Không retention drop (kho là tài sản).

**Chính sách lưu — hai lớp theo khả năng tải lại** *(review 2026-08-25 — bản trước ước lượng "lớn nhất OMO ~150 MB/năm" là sai: bỏ sót nguồn trả full-history mỗi lời gọi, riêng LBMA đã 0,9 MB/lời gọi — đo 2026-08-15)*:

| Lớp | Nguồn | Luật lưu |
|---|---|---|
| **Không tải lại được** | OMO (chỉ hiện phiên mới nhất) · WiChart (cửa sổ trượt 2 năm) | Lưu **mọi lần crawl**, vô điều kiện |
| **Tải lại được** | FRED · LBMA · Yahoo · Binance · Frankfurter | Lưu khi **hash nội dung đổi** so lần trước (nguồn trả full-history mỗi lời gọi thì đa số ngày giống hệt hôm qua — lưu lặp là rác); cột `meta` giữ hash để so |

Dung lượng WiChart mỗi payload **chưa đo** — ghi nhận khi chạy thật qua `ops`, xét nén (`pg_column_compression` mặc định đã nén jsonb) hay gộp khi có số thật, không đoán trước.

## 2. `ops` — ba bảng trạng thái

```sql
CREATE TABLE ops.data_domain_state (      -- CÔNG TẮC miền × nguồn: "phần thiếu kệ nó, phần đủ cứ chạy"
  domain          text NOT NULL,          -- 'market.reference' | 'market.price' | 'market.fundamentals'
                                          -- | 'macro.indicator' | 'macro.omo' | 'asset' | 'news'
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

## 3. Điểm cần duyệt ở bước này

- [ ] **Kho đồ thô một bảng chung** append-only, không xoá — bảo hiểm đổi-schema + cứu nguồn không tải lại được — đồng ý?
- [ ] **Công tắc miền × nguồn** (`data_domain_state`) với ba trạng thái active/frozen/migrating — đồng ý?
- [ ] **Giám sát hợp đồng** lưu snapshot hằng ngày trong DB (`contract_snapshot`) để so baseline — đồng ý?
- [ ] **Nhật ký job** (`etl_run`) làm nguồn cho cảnh báo — đồng ý?

## 4. Kiểm chứng của bước này (seam)

1. `raw_payload`: chèn dòng không có cả `payload` lẫn `body` → lỗi CHECK; chèn HTML OMO (literal rút gọn) rồi đọc lại nguyên văn.
2. `data_domain_state`: `status='paused'` → lỗi CHECK; UPSERT `(domain, source)` đổi `frozen` → 1 dòng, trạng thái mới.
3. `etl_run`: vòng đời `running` → `success` cập nhật được `finished_at`; truy vấn "lần chạy gần nhất của job X" ra đúng dòng (literal 2 lần chạy).
4. `contract_snapshot`: hai lần check cùng endpoint khác `checked_at` → 2 dòng (lịch sử baseline giữ nguyên).

## 5. Khép vòng spec

Chốt bước này là **đủ DDL cho toàn bộ `postgres-data` phần sự thật** (bước 1–7). Còn lại:

- **Bước 8** — tầng tự tính (chỉ số ngành, chỉ báo kỹ thuật, DXY dựng lại): nguyên tắc đã chốt ở README, danh sách bảng + công thức chốt khi có dữ liệu thật.
- Sau đó: **`plan.md`** bẻ task thực thi (khung Alembic → migration theo bước → seed → test seam), theo quy trình §4.1.
