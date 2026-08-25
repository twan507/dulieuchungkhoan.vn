# SDD ledger — plan: docs/90-records/plans/2026-08-25-postgres-data-schema/plan.md

Nhánh: `feat/postgres-data-schema` · Artifact tạm (brief/report/review package): scratchpad ngoài repo (luật §4.1 — cấm `.superpowers/`). Spec: 7 file step cùng thư mục (authority khi plan mâu thuẫn).

## Pre-flight scan (trước Task 1)

| Cặp/Task | Kiểm gì | Kết quả |
|---|---|---|
| T1→T2..T9 | Interface lệnh alembic/pytest + fixture `db`/`expect_violation` | Khớp — T1 produces, các task sau consume đúng tên |
| T2↔T3 | T3 modify file test của T2 | Tuần tự, không xung đột; test seed độc lập bảng tự tạo (không phụ thuộc seed khi test identity) |
| T1..T9 chuỗi revision | 0001→0009 down_revision phải nối đúng | Ghi vào brief từng task: `down_revision` = id trước đó |
| T4 gate | Generator 30–60 cột, ngoài dải → dừng | Controller tự làm T4 nên gate thực thi được |
| T2 Step 1 | Ghi chú "XOÁ khi viết thật" trong plan | Đã dặn trong brief — dòng nhắc không được vào code |
| T9 sau T2–T8 | Grants `ON ALL TABLES` phải chạy sau khi bảng tồn tại | Thứ tự migration bảo đảm |
| T10↔T1 | Downgrade base sạch — T1 đã kiểm ở mức 0001, T10 kiểm cả chuỗi | Nhất quán |
| Từng task tự khớp | Test ↔ DDL section được trỏ | Khớp theo self-review của plan (đã chạy khi viết) |

Ruling: Task 1/4/11 controller tự làm theo phân vai ghi trong plan (CLAUDE.md §4.1 — task cần nhìn output quyết ngay); override mặc định "controller không tự code" của skill SDD. — Sai thì: thiếu một lớp review độc lập cho 3 task đó, bù bằng final whole-branch review.
Ruling: Ledger + brief/report đặt ngoài `.superpowers/` theo luật repo (tiền lệ deploy-scaffold). — Sai thì: không.

## Task log
Task 1: complete (commit 1f0a70f, controller tự làm theo plan; 3 test pass; downgrade/upgrade dev DB OK). Ghi chú: PG16 mặc định đã khoá CREATE public — REVOKE trong 0001 giữ làm tường minh/idempotent.
Task 2: complete (commits 1f0a70f..3b0c77e, review clean — SPEC ✅, Quality Approved). Minor (deferred): thứ tự DROP trong downgrade 0002 không phải đảo ngược chính xác thứ tự tạo (an toàn FK, icb_industry không có FK vào/ra).
Task 3: complete (commits 27b3339..d4ff21e, review clean — seed 6+24 khớp literal từng ký tự với industry-tree.md, kiểm bằng script độc lập của reviewer). Minor (deferred): downgrade 0003 thêm `DELETE industry_icb_map` ngoài brief. Ruling: GIỮ — phòng FK khi map có dữ liệu rồi downgrade; lệch literal brief nhưng đúng kỹ thuật. — Sai thì: không (bảng đang rỗng).
Task 4: complete (controller tự làm theo plan; commit sau ledger-3..HEAD; 14 test pass). GATE generator: 34 cột (dải 30-60 OK) — dán 10 tên đầu ở price-cols.sql scratchpad; bắt + sửa 2 lỗi trong lượt: (a) generator snake_case bẻ vụn 'PRIOR_PRICE' → sửa regex chỉ chèn _ giữa chữ-thường→HOA; (b) thiếu PYTHONIOENCODING=utf-8 crash cp1252 (bẫy CLAUDE.md §5 — cắn thật). Bẫy mới ghi nhận: dấu ':' trong literal JSON bị sa.text() hiểu là bind param → mọi test sau truyền payload jsonb qua bind.
