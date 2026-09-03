# Sổ ghi thực thi — `etl events` (lát 2)

**Nhánh:** `feat/events-daily-etl` *(tách từ `main` tại `194f5e1`)* · **Bắt đầu:** 2026-09-03

Sổ này ghi **cái đã chạy và output thật**, không ghi ý định. Quy tắc: chưa dán được output thì chưa được đánh ✅.

---

## Bước 0 — Trước khi viết dòng code nào

| Việc | Kết quả |
|---|---|
| Đo nguồn, 46 lời gọi thật | `02a8a8e` — [`measurements.md`](measurements.md) |
| Spec, chủ dự án duyệt | `5572937` |
| Plan 7 task | `194f5e1` |
| **Chạy thử toàn bộ code của plan ở scratchpad ngoài repo** | **34/34 xanh** (21 thuần + 13 trên Postgres thật) |
| Kiểm câu `ON CONFLICT` trên `postgres-data` thật, role `dlck_etl`, trong giao dịch rollback | Arbiter suy được · ghi lại cùng khoá ⇒ 1 dòng · khác `stage_key` ⇒ 2 dòng · cả 5 cột `coalesce` cùng NULL vẫn dedupe |
| Kiểm quyền `dlck_etl` trên mọi đường ghi | `issuer` · `issuer_external_id` · `staging.raw_payload` · `data_domain_state('market.events')` · `etl_run` — đủ cả năm |
| Kiểm dữ liệu có phá CHECK không | `lengthReport` ∈ {1..5} ✓ · `yearReport` 2015–2026 vừa `smallint` ✓ · `organCode`/`publicDate` không bao giờ rỗng ✓ |

**Một lỗi thật bắt được ở lượt chạy thử**, đã vá trong plan trước khi giao: ngưỡng vế (iv) `DUP_RATIO = 0.5%` đúng cho lượt thật (42/110.737 = 0,037%) nhưng **sai cho fixture dày ca biên** (4/28 = 14,3%) — job bị chính guard của nó từ chối, 3 test của Task 5 đỏ. Vá bằng cách ghim ngưỡng **trong test đấu nối** (`test_e20`), giữ nguyên ngưỡng production; `test_e18` vẫn là chủ sở hữu ngưỡng.

---

## Nhật ký từng task

*(điền khi chạy — mỗi task một mục, kèm output thật)*
