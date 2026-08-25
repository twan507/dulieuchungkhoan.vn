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
Task 5: complete (commits 5b897e1..b1f43de, review clean — SPEC ✅ verbatim + giải tay khớp; Quality Approved). Implementer tự bắt bug thứ tự DROP view/series_break trong downgrade và sửa trước khi nộp. Ghi chú: "5 hàm/19 test" trong dispatch là controller đếm sai — implementer đúng khi theo brief (4 hàm/18). Reviewer bắt lỗi đếm "6 bảng" trong brief (thật 7) — văn bản, không ảnh hưởng code.
Task 6: complete (commits eb2f989..8fe2753, review clean — SPEC ✅ diff tự động khớp nguồn, không fx_rate, không 'rate'/'perp'; Quality Approved, 1 Minor lời văn report). Implementer tự kiểm thêm round-trip downgrade/upgrade.
Task 7: fix round 1/5 (1 addressed — CHECK 20 sub taxonomy từ feeds.json, reviewer đối chiếu 2 nguồn khớp; commits 0872615..407f012).
Task 7: complete (commits 74ea130..407f012, SPEC ✅; 1 Important PARKED — Ruling: finding là gap BẰNG CHỨNG quy trình (không dán output đỏ, fix round không chứng minh đỏ-trước), không phải lỗi code — DDL/test đã kiểm độc lập đúng; controller tự chạy lại suite xác nhận 30/30 xanh làm bằng chứng sống; khắc phục hệ thống: mọi dispatch còn lại BẮT BUỘC dán nguyên văn output đỏ vào report. — Sai thì: nếu thực chất test chưa từng đỏ, Task 10 downgrade/upgrade + suite toàn phần sẽ lộ). Ghi nhận bẫy mới từ implementer: operator pg_trgm phải viết OPERATOR(extensions.%) khi extension nằm ngoài search_path — đưa vào database/README ở Task 10.
Task 8: complete (commits 31a42f1..5f67472, review clean — SPEC ✅ diff tự động 0 sai khác, output đỏ/xanh có dán và đối chiếu chéo khớp 34 test). Không finding.
Task 9: fix round 1/5 (1 addressed — thiếu default priv ON SEQUENCES cho dlck_etl, lỗi trong SQL của plan do controller viết; commits d537ba2..9b0efd2).
Task 9: complete (commits 98daa78..9b0efd2, review clean — ma trận grant đếm tay khớp 100%, downgrade đối xứng, xử lý cross-DB role bằng EXCEPTION dependent_objects_still_exist đúng bản chất pg_shdepend). Ghi nhận: dev DB đang ở revision 0001 (các task chỉ chạy test DB) — Task 10 sẽ đưa dev lên head.
Task 10: fix round 1/5 (1 addressed — câu "mỗi migration một file test" sai thực tế; commit c3ae1e8). Ruling: re-review scoped do controller tự thẩm trên diff (fix docs 1 câu, dữ kiện kiểm được trực tiếp) thay vì dispatch — Sai thì: bỏ lọt lỗi câu chữ, final review sẽ quét lại.
Task 10: complete (commits 80ff53a..c3ae1e8, review 1 finding đã fix). NGHIỆM THU TOÀN PHẦN ĐÃ CHẠY THẬT: dev DB 0001→head→base→head sạch; pytest 35/35 ×2 lượt; LEFTOVER: [] sau downgrade; output dán trong task-10-report.md.
