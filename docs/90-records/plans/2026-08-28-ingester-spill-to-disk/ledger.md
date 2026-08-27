# SDD ledger — plan: docs/90-records/plans/2026-08-28-ingester-spill-to-disk/plan.md

*(Ledger nằm trong thư mục plan theo CLAUDE.md §4.1 — artifact tạm của subagent ở scratchpad ngoài repo, không tạo `.superpowers/`.)*

## Quét tiền-thực-thi (2026-08-27 tối)

Cặp task chung file/interface:

| Cặp | Produce ↔ Consume | Kết quả |
|---|---|---|
| T1 ↔ T5 (`chwriter.py`) | T1 thêm timing/gauge trong `flush_once`; T5 viết lại thành `manage_once`/`write_once` nhưng Interfaces T5 tuyên giữ `insert_percentiles`, và test T5 assert gauge cập nhật trong `manage_once` | Khớp — gauge dời vào vòng quản, `flush_once` compat = manage+write nên hành vi T1 giữ |
| T4 ↔ T6/T7/T8 (`SpillStore`) | `write(table, block, kind)` / `next_batch(max_rows)` / `SpillItem` / `delete` / `empty` / `counters` | Chữ ký thống nhất ở cả 4 task |
| T4 ↔ T8 (`config.spill_dir`) | T4 thêm trường; T8 `_run_run` dùng `cfg.spill_dir` | Khớp |
| T5 ↔ T6 (`_Pending`, hằng số) | T5 produce `_Pending(table, block, first_try)`; T6 test import `_Pending`, `N_CAP_ROWS` | Khớp (T6 mới thêm N/K/SPILL hằng — T5 chưa cần) |
| T5 ↔ T8 (`main.py`) | T5 đổi loop + drain dùng `clean()`; T8 đổi budget mặc định + replay nợ | Sửa tuần tự cùng file, không đè nhau |
| T9 ↔ T1 (`make_on_packet`) | T9 rút `process_record` nhưng giữ frames-counter + `not_leader_dropped` của T1 | Test i12 là lưới hồi quy |
| T2 ↔ T3 (probe → hằng số) | Gate T3 (bản điều chỉnh tối 27/08) cần p95 insert từ probe | **Ruling PF-1** dưới |

Tự-nhất-quán từng task: T5 test dùng `WRITE_CALL_BUDGET_S`, `_Clock` — định nghĩa trong cùng file test ✓ · T6 `_writer_with_spill` cần `import time` — file test đã import ✓ · T8 `drain_writer` import từ `ingester.main` ✓ · T10 khung chaos có hai chỗ chủ đích giao executor (client factory sau docker start) — có nêu ranh giới assert ✓.

**Ruling PF-1:** mục "thêm phép đo p95 insert vào probe" nằm ở gate Task 3 nhưng là việc code — gộp vào dispatch Task 2 (probe một file, một lần chạy). Chi phí nếu sai: probe dài hơn vài phút, không ảnh hưởng gì khác.

**Ruling PF-2:** plan Task 5 bước 4 đòi sửa test cũ hai lần (T5 giữ drop, T6 đổi thành spill). Chấp nhận chi phí sửa-hai-lần để mỗi task tự xanh độc lập — đúng nguyên tắc task-tự-kiểm của plan. Chi phí nếu sai: vài phút công subagent.

## Tiến trình

*(cập nhật sau mỗi task)*

- Task 1: implementer DONE_WITH_CONCERNS (commit 3f2cc33, 105 pass/73s). Concern đúng: test gauge trong plan thiếu fake clock → tự đốt 60s thật mỗi lần chạy suite. **Ruling T1-1:** lỗi do plan viết test verbatim thiếu fake clock — sửa trước khi review (resume implementer, thay riêng test đó bằng bản fake clock, assert giữ nguyên). Chi phí nếu sai: không — assert không đổi.
