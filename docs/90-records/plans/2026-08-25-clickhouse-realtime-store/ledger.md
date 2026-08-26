# SDD ledger — plan: docs/90-records/plans/2026-08-25-clickhouse-realtime-store/plan.md

Nhánh: `feat/clickhouse-realtime-store` (từ `main` @ 3fc9de7). Spec: `spec.md` cùng thư mục (thẩm quyền cao nhất khi plan mâu thuẫn). Artifact tạm (brief/report/review package): scratchpad phiên làm việc, ngoài repo.

## Pre-flight scan (trước Task 1)

| Cặp / Task | Đối chiếu | Kết quả |
|---|---|---|
| T1 ↔ T3 (conftest) | T1 tạo `ch`/`ch_backup_dir`; T3 thêm `migrated` + helper ngày động `dt_ago`/`part_of`/`TODAY`; T4–T6 import helper từ conftest | Khớp thứ tự — helper có mặt trước khi T4 dùng |
| T1 ↔ T7 (backups.xml) | T1 tạo `deploy/infra/clickhouse/backups.xml` (fixture cần); T7 chỉ tạo 2 xml còn lại + compose | Không giẫm nhau — T7 có ghi chú tường minh |
| T2 → T3/T5/T6 (interface) | `upgrade(client, versions_dir=None)` — T3 `migrated` gọi `upgrade(ch)`; T5/T6 dùng qua `migrated` | Chữ ký khớp |
| T3 → T5 (roles) | T5 tạo user gắn `dlck_ingester` từ 0001 | Khớp |
| T6 (chữ ký) | `run_backup(client, backup_dir, today)` — test gọi đúng dạng | Khớp |
| Từng task tự nhất quán | Test/DDL/file tạo-ra vs dùng-lại soi từng task | Không thấy mâu thuẫn |

**Ruling (pre-flight):** T4/T5 là task thuần test bổ sung cho DDL đã giao ở T3 (T3 đã đi đỏ-trước-xanh ở Step 4→5) — luật "test đỏ trước implementation" không áp cho task không có implementation; plan đã ghi tường minh "FAIL là dừng-và-báo, không sửa expected". Giá nếu sai: reviewer task có thể phàn nàn thiếu bước đỏ — xử bằng ruling này.

**Ruling (pre-flight):** import `from tests.clickhouse.conftest import dt_ago` dựa namespace package + `pythonpath=["."]`; nếu môi trường không import được thì implementer chuyển helper sang module `tests/clickhouse/_dates.py` và conftest re-export — thay đổi cơ học, không đổi hành vi. Giá nếu sai: một vòng fix nhỏ.

## Tiến trình
- Task 1: complete (commits 3fc9de7..5635e38, review clean — Spec ✅, Quality Approved)
- Task 1: minor (deferred): lệnh chạy chưa set PYTHONIOENCODING=utf-8 tường minh; race nhẹ ở _free_port (thiết kế nguyên văn brief, chấp nhận cho single-session)
- Task 2: complete (commits 5635e38..475ab7a, review clean — Spec ✅, Quality Approved, 0 finding)
- Task 3: Ruling: (a) brief 0002 có dấu `;` trong comment vi phạm chính quy ước Global Constraints — implementer sửa đúng (đổi thành `.`); (b) LỖI PLAN liên-task: test cuối t02 ghi version giả trùng tên thật `0002_rt_schema` vào sổ container session → đầu độc fixture `migrated` khi chạy cả suite. Ruling: đổi tên fake trong t02 thành `0002_zz_fake` + gọi assert_migrated với required tường minh; xác nhận cả suite chạy chung xanh. Giá nếu sai: một vòng fix nữa.
- Task 3: fix round 1/5 — đổi tên fake version t02 (fc3193f), lộ tiếp: stub rt.a của t02 sống qua session. Ruling: t02 tự dọn sau mình bằng module-scoped autouse teardown DROP DATABASE rt (kẻ gây ô nhiễm tự dọn — không đụng t03/conftest). Giá nếu sai: một vòng fix nữa.
- Task 3: complete (commits 475ab7a..376dd73, fix round 1-2 xong theo ruling, review clean — Spec ✅, Quality Approved, 0 finding; suite 13/13)
- Task 4: complete (commits 376dd73..cb8f5a8, review clean — Spec ✅, Quality Approved, 0 finding; suite 19/19)
- Task 5: complete (commits cb8f5a8..1e57cd3, review clean — Spec ✅, Quality Approved; suite 23/23)
- Task 6: fix round 1/5 (1 addressed — thêm 2 test phủ nhánh prune, code test do controller cấp theo ruling "thiếu sót plan"; commit 1e349ec)
- Task 6: complete (commits 1e57cd3..1e349ec, re-review ADDRESSED — Spec ✅, Quality Approved; suite 29/29)
- Task 6: minor (deferred): idempotency backup dựa tồn-tại-tên-file, file .zip hỏng do crash giữa chừng sẽ bị coi là đã backup (không tự phục hồi)
- Task 7: review Critical — fail-fast realtimeMisconfigured nằm sau early-return của ensureEnv (dead code ở đường chạy phổ biến). Ruling: LỖI PLAN (snippet của controller); sửa = tái cấu trúc ensureEnv chạy check vô điều kiện; verify bằng .env tạm có realtime thiếu password → dev-stop phải die trước mọi hành động docker.
- Task 7: fix round 1/5 (1 addressed — ensureEnv chạy guard vô điều kiện, verify die thật không đụng docker; commit 7486b9b)
- Task 7: complete (commits 1e349ec..7486b9b, re-review ADDRESSED — Spec ✅, Quality Approved sau fix)
- Task 8: fix round 1/5 (2 addressed — roadmap "spec 8 bước"→mô tả đúng; chạy lại đúng lệnh grep spec; commit 5c56fb8)
- Task 8: fix round 2/5 (report-only — khối fence grep thay bằng output thật 174 dòng nguyên vẹn, diễn giải tách ra ngoài fence; không commit)
- Task 8: complete (commits 7486b9b..5c56fb8, review clean sau 2 vòng — Spec ✅, Quality Approved)
- Task 8: minor — roadmap.md dòng 131 thiếu 1 dấu | (final review xác minh bằng git blame: DO commit 5c56fb8 của nhánh này gây ra; dòng ledger cũ quy kết "có sẵn" là khẳng định chưa kiểm — đính chính tại đây). Sửa trong fix wave cuối
- Final review (opus, toàn nhánh): APPROVE có điều kiện — 4 Important: I1 CLICKHOUSE_BACKUP_DIR hai CWD; I2 ledger chưa commit; I3 bảng roadmap hỏng; I4 thiếu 5 case biên seam spec §9. Ruling: I1 chốt quy ước đường dẫn tương đối giải theo deploy/infra (một chuẩn cho cả compose lẫn script); I4 làm 4/5 case, PARK case dedup-qua-restart — Ruling: đã đo thật (spec §12/T8), harness restart container session dùng chung quá đắt so với giá trị lưới hồi quy, chuyển sang plan ingester (nơi có harness riêng); T5-minor cũ xoá khỏi ledger vì MergeTree thuần merge nền không bao giờ bỏ dòng — lập luận reviewer task không đứng; T6 thêm caveat zip-hỏng vào README. Giá nếu ruling sai: I1 sai chuẩn thì backup ghi nhầm chỗ (bắt được ngay đêm đầu); park T8-restart sai thì hồi quy dedup-restart chỉ được phát hiện ở plan ingester.
- Fix wave cuối: complete (commit 9a85fdd — I1/I3/I4/F4/F5; re-review scoped: ALL ADDRESSED, không hỏng mới). Verify tay của controller: pytest tests/clickhouse → 32 passed; node --test → 7/7.
- Nhánh sẵn sàng trình chủ dự án quyết merge. Ledger commit ở đây đóng finding I2.
