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
- Task 1: minor (deferred): (a) chưa có test cho nhánh WARN-log BẮN (chỉ test nhánh im — plan-mandated); (b) `insert_percentiles()` nhánh deque rỗng chưa test; (c) ledger.md bị cuốn vào commit 272c70a (vệ sinh commit). Hai ⚠️ reviewer đã được controller xác nhận không phải gap (`_run_measure` không có ChWriter; ledger do controller viết).
- Task 1: complete (commits ceeb5dd..272c70a, review clean — Approved, 0 Critical/Important)
- Task 2: implementer DONE sau 2 lần resume (agent tự treo vì background probe rồi ngồi chờ — lần 3 ép foreground + chẻ `-k` mới xong). Commits 7d65d44 + 5219dcb. Số đo: 1a: count=100 trên block 100 dòng insert 2 lần (dedup GIỮ qua pickle roundtrip) · 1b: count=100 trên block 50 dòng (NHÂN ĐÔI sau 105 block chen — đúng dự đoán spec, cửa sổ đẩy theo block) · 1c: count=10 trên block 10 dòng sau 130 s chờ (cửa sổ KHÔNG co theo giây — thuần block) · pickle 5.000 dòng = 323.657 B (~65 B/dòng trên đĩa) · p95 insert: block 5.000 dòng ~88 ms, block 50 dòng ~72 ms, DEV ≈ VPS. **Phát hiện ngoài dự kiến: `memory-vps.xml` như đã commit làm CH crash-loop lúc boot (BAD_ARGUMENTS — 3 setting merge_tree mặc định > pool size 8); đã sửa (pin = 4) + kiểm bằng boot container thật.** Đang review.
- Task 2 review: Needs fixes với đúng 1 Important — số đo chưa vào spec §9/ledger (Bước 3 brief). **Ruling T2-2:** Bước 3 vốn trùng với việc gate Task 3 giao cho controller ("ghi số vào spec §2.5", "KHÔNG giao subagent") — chuyển Bước 3 về gate, controller ghi ngay trong cùng lượt thay vì mở fix round. Chi phí nếu sai: không — cùng nội dung, người ghi khác.
- Task 2: minor (deferred): (a) `import time` lặp cục bộ trong probe; (b) cleanup timing probe không try/finally; (c) `n_1c` không có assert guard (kế thừa từ brief).
- Task 2: complete (commits 272c70a..5219dcb, review: probe logic sạch toàn bộ, Important duy nhất xử bằng Ruling T2-2)
- **GATE Task 3 — ĐÓNG 2026-08-27 tối:** hằng số tạm ĐỨNG VỮNG trước số đo, không đổi giá trị: `N_CAP_ROWS=100_000` (49,7 MB; ~15 s ATO đỉnh) · `K_REPLAY_ROWS=20_000` (>19.488=đỉnh×3; 4 insert gộp×88 ms≈0,35 s<1 nhịp) · `SPILL_CAP_BYTES=10 GiB` (2 h đỉnh ×3 ≈ 9,1 GB @ 65 B/dòng đo). **Điều kiện khả thi §2.4 ĐẠT dư ~8,7×** (6.496×17,6 µs≈0,114<1). p95 VPS hẹp ≈ dev ⇒ K không cần hiệu chỉnh. Số + nguồn đã ghi spec §2.5 + §9. Mục kiểm chứng sau phiên 28/08 giữ nguyên trong plan Task 3.
- **Ruling T2-1:** brief Task 2 bước 2 viết "bật lại compose với overlay VPS" — nhưng probe chạy trên container test ephemeral, overlay compose dev không chạm tới nó, còn trỏ probe vào CH dev thì ghi rác vào kho thật. Quyết: probe tự dựng container CH thứ hai mount `deploy/infra/clickhouse/memory-vps.xml` + `--memory` theo trần vps để đo hồ sơ hẹp, không đụng compose dev. Chi phí nếu sai: probe đo trên môi trường lệch cấu hình VPS thật một phần (mount config là chính, chấp nhận).
