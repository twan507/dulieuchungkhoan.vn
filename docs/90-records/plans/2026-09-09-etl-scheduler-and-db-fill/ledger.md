# Ledger — lát 13: scheduler trong `etl` + hoàn thiện toàn bộ kho

**Nhánh:** `feat/etl-scheduler` · **Spec:** [spec.md](spec.md) (duyệt 2026-09-09 ~08:45) · **Plan:** [plan.md](plan.md) (`78faa8d`) · **Thực thi:** subagent-driven, sổ SDD ở scratchpad phiên (không `.superpowers/` trong repo).

## Quyết định vận hành ngày 09/09

- 07:59 `docker compose stop ingester` theo yêu cầu chủ dự án: hôm nay không ghi tick, chỉ nạp đầu. `docker compose up -d` sẽ dựng lại ingester ⇒ cả ngày dùng `docker compose run --name dlck-fill-<x> etl …`.
- Kho dev là kho thật, không xoá dựng lại nữa (chủ dự án 2026-09-09 sáng); lên VPS mang nguyên dữ liệu.

## Nạp đầu 09/09 (Task 0)

| Giờ | Lệnh | `run_id` | Mã thoát | Số đo |
|---|---|---|---|---|
| 08:24–08:27 | `yahoo --backfill` | 24 | 0 | 54 lời gọi, success |
| 08:27–08:29 | `binance --backfill` | 27 | 0 | 39 lời gọi |
| 08:29–08:33 | `wichart` | 28 | 0 | 68 lời gọi |
| 08:33–08:34 | `fred` | 29 | 0 | 14 lời gọi |
| 08:34 | `fx` | 30 | 0 | 1 lời gọi |
| 08:34 | `lbma` | 31 | 0 | 2 lời gọi |
| 08:23 | `price --backfill --stop-before-open` (lần 1, run 22) | 22 | 130 | ⚠️ lỗi thao tác: cờ tính hạn 08:45 hôm nay vì chạy trước mở cửa ⇒ `docker stop` sau 40 s; đóng sổ "dừng tay" đúng đường SIGTERM trong container |
| 08:23 | `fundamentals --backfill --stop-before-open` (lần 1, run 23) | 23 | 130 | cùng lý do |
| 08:24 → | `price --backfill` (container `dlck-fill-price-backfill`) | 25 | đang chạy | con trỏ nối sau A32; **FiinTrade "Timeout expired" (HTTP 200, `status: Failed`) ở trang sâu**: 08:27 AAA trang 1 · 08:33 AAH trang 8 · 08:36 AAM trang 4, tới 09:00 là 5 lỗi/14 mã; tốc độ ~2,5 phút/mã ⇒ cả vòng ước **> 2 ngày**, không phải 20 giờ (giãn cách + ~50 trang/mã) |
| 08:24 → | `fundamentals --backfill` (container `dlck-fill-fundamentals`) | 26 | đang chạy | 3.900/6.091 lời gọi lúc 09:00, **0 retry** — luồng BCTC không bị ảnh hưởng |

Kho lúc 08:23 (trước nạp đầu): `price_daily` 2.084 dòng · `financial_statement` 15.904 · `ohlc_daily` 308 · `asset.price_daily` 79.876 · `observation` 16.154 · `article` 174 · `snapshot_daily` 1 · `etl_run` 21.

Dữ kiện danh mục: `market.security` có 1.962 mã `listed` nhưng 439 mã mang dấu `directory_absent_since = 2026-09-08 16:09 VN` ⇒ luật huỷ niêm yết (ngưỡng 3 ngày, guard 1 %) sẽ làm `refdata` từ chối từ lượt đầu tiên sau 2026-09-11 16:09; xử lý bằng một lượt tay `--accept-drop` có người nhìn (plan Task 0 Step 10). Tập mã có mã FiinTrade và chưa dấu vắng = **1.523** — đây là tập cho `snapshot --codes` trọn sàn.

## Task 1 → 13

*(ghi tiếp theo tiến độ)*

## ⏸️ Tạm dừng 2026-09-09 09:06 — chủ dự án: sắp hết hạn mức phiên, dừng ở điểm an toàn, đợi reset

**Trạng thái code:** nhánh `feat/etl-scheduler` HEAD `8941bab` (spec + plan + ledger, chưa có code). Task 1 vừa giao subagent Sonnet lúc 09:06 và đã bị dừng; cây làm việc còn **một file sửa chưa commit**: `backend/tests/etl/test_e03_parse.py` (hai test đỏ theo brief Task 1) — phiên sau: implementer mới đối chiếu với brief, dùng lại hoặc ghi đè, không cần stash.

**Sổ SDD (ngoài repo, đường dẫn tuyệt đối để phiên sau đọc):** `C:\Users\tuanb\AppData\Local\Temp\claude\D--twan-projects-dulieuchungkhoan-vn\3394952d-87db-4d2f-b1b1-98a68f2e1aa6\scratchpad\sdd\2026-09-09-etl-scheduler-and-db-fill\` — `progress.md` (bảng rà xung đột tiền thực thi + 4 phán quyết R1–R4), `task-1..5-brief.md`. Phiên sau có scratchpad khác: tạo workspace mới, chép `progress.md` sang (hoặc đọc tại chỗ), cắt brief lại bằng `scripts/task-brief PLAN N OUTFILE` của skill `subagent-driven-development` (luôn truyền OUTFILE ngoài repo).

**Bốn phán quyết đã ghi ở sổ SDD (chép để không mất):**
- R1: artifact SDD ở scratchpad; ledger dự án là file này, commit.
- R2: Task 5 — implementer chạy cả bộ test; test nào `open_run` mà không `close_run` phải thêm `close_run` (khoá sống theo lượt).
- R3: Task 8 — `main()` đọc `os.environ.get("ETL_LOG_DIR")` tường minh để `test_env_contract` thấy người đọc.
- R4: hợp đồng exit 1 là quét tĩnh `test_e68` (đã ghi đính chính spec).

**Đang chạy trên máy (Docker, không phụ thuộc phiên chat):**
| Container | Lệnh | Bắt đầu | Ghi chú |
|---|---|---|---|
| `dlck-fill-price-backfill` | `price --backfill` (run 25) | 08:24 | ~2,5 phút/mã, > 2 ngày; lỗi "Timeout expired" 5/14 mã tới 09:00 |
| `dlck-fill-fundamentals` | `fundamentals --backfill` (run 26) | 08:24 | 3.900/6.091 lúc 09:00, 0 retry |
| `dlck-fill-news-tinnhanhck` / `-bnews` / `-nguoiquansat` | `news --backfill-sitemap --source <x> --from 2026-09` | 09:03 | Task 0 Step 5 |
| *(ingester)* | **đang dừng** từ 07:59 theo yêu cầu | | `docker compose up -d` sẽ dựng lại nó — hôm nay tránh |

**Hai script nền (Git Bash `nohup`, có thể chết theo phiên):** `scratchpad/price-load-test.sh 1000 dlck-fill-price-daily-1` và `… 1330 dlck-fill-price-daily-2` — chờ tới 10:00 / 13:30 rồi `docker compose run -d --name <tên> etl python -m etl price`, ghi log `scratchpad/price-load-test-1.log`, `-2.log` (cùng thư mục scratchpad ở trên). Nếu phiên sau không thấy container `dlck-fill-price-daily-1`/`-2` thì script đã chết — chạy tay lệnh đó cho AC3.

**Việc còn lại trong ngày 09/09 nếu phiên chưa quay lại kịp (chủ dự án chạy tay được):**
1. Sau 15:05: `docker compose run --rm etl python -m etl screener` → `… price` → `… events` → `… snapshot` → `… fundamentals` → `… omo` (mỗi lệnh chờ xong mới tới lệnh sau; `snapshot` và `fundamentals` chờ `dlck-fill-fundamentals` xong).
2. Trước 08:30 sáng 10/09: `docker compose start ingester` (bật lại ghi tick; `docker compose logs --tail 3 ingester` phải thấy "chờ tới 2026-09-10T08:30").
3. Seed OMO và `snapshot --codes` trọn sàn cần code Task 2 / xong BCTC — để phiên sau.

**Điểm nối lại:** đọc mục này → `git status` → tiếp Task 1 theo `plan.md` (giao subagent Sonnet, BASE = HEAD lúc đó) → review → Task 2… Nhịp mỗi task: brief → implementer → review-package → reviewer → ledger.

## Nối lại 2026-09-09 13:08 — máy đã reboot lúc 13:05, Docker tắt từ ~09:07

- Mọi lượt nạp đầu đóng sổ **`failed: dừng tay (Ctrl+C)` lúc 09:07** (SIGTERM khi Docker tắt — hợp đồng dừng sạch trong container đúng cả với `docker compose run`). Hai script hẹn giờ thử tải chết theo; lượt 10:00 không chạy (không kết nối được engine). Mở lại Docker Desktop 13:09, engine lên sau 20 s; ba kho + `api` + `etl` tự lên (`restart: unless-stopped`), **ingester vẫn dừng** như chủ đích.
- **Kết quả lượt backfill giá đầu (run 25, 08:24–09:07):** 16 mã, con trỏ `ACC`, `price_daily` 2.084 → 18.094 dòng. **7/16 mã hỏng**, đều `Timeout expired` (HTTP 200, `status: Failed`) sau 4 lần: AAA trang 1 · AAH trang 8 · AAM trang 4 · ABS trang 10 · ABT trang 1 · ACB trang 65 · ACC trang 3 — không chỉ trang sâu; `source_down_pauses = 0`. Cùng lúc luồng BCTC (run 26) đi 4.000+ lời gọi **0 retry** ⇒ endpoint `getPriceData` nghẽn phía nguồn khi có hai luồng, hoặc nghẽn giờ sáng — lượt thử tải chiều sẽ phân định.
- **Backfill BCTC (run 26)** bị giết giữa pha fetch (3.900/6.091) ⇒ **không ghi gì** (`fundamentals_check` vẫn 1 dòng): job fetch trọn rồi mới apply, không nối được giữa chừng — phải chạy liền ~1 giờ 45.
- Sitemap tin (run 32–34): `article` 174 → 382 trước khi bị giết; con trỏ nối lại được.
- 13:10 khởi động lại: `dlck-fill-price-backfill` (nối sau ACC, còn 1.506 mã) · `dlck-fill-fundamentals` · ba `dlck-fill-news-*` · **lượt thử tải 1 `dlck-fill-price-daily-1` chạy ngay** (13:10, phiên chiều, ba luồng FiinTrade) · lượt 2 hẹn 14:30 (script nền `price-load-test.sh`, log `scratchpad/price-load-test-2b.log`).
- 13:12 giao lại Task 1 (Sonnet).

## Task 1–5 (2026-09-09 13:12 →)

- **Task 1** parser gộp dòng cùng kỳ hạn — `048c514`, review sạch (2 Minor để review cuối: chưa test nhánh None của thành viên; quét O(n) tìm dòng cùng kỳ hạn).
- **Task 2** seed OMO từ CSV — `2ad2126`, 46 test seam + 612 test `tests/etl` xanh. CSV chuyển từ xlsx bằng script dùng một lần (openpyxl, Python hệ thống) → `C:\Users\tuanb\Downloads\omo-fiinprox-20250908-20260907.csv`, 826 dòng, ngoài repo.
- **AC1 nửa đầu — chạy khô trên kho thật ~13:20** (`uv run python -m etl omo --seed <csv> --dry-run`, native):

```
sessions_new=248 sessions_skipped=0 auctions=823 rows_merged=3 min_session_date=2025-09-08 max_session_date=2026-09-07 flow_rows=317 outstanding_2026-09-07=250778.26 outstanding_2026-09-08=249363.44
rc=0
```

  Khớp từng số với dự đoán trong spec §2.1 (250.778,26 và 249.363,44 tỷ). `auctions=823` = 826 dòng − 3 dòng gộp. Lượt ghi thật chạy sau khi review Task 2 xanh.
- **Task 2 review:** 3 Important (dry-run không bắt lỗi thành 2/130; `store()` ghi note khi gộp chưa test; nhánh None chưa test) → vòng sửa 1 `84295a8`, re-review sạch. Minor để review cuối: INSERT auction lặp ở `store`/`store_seed`; test dry-run chỉ kiểm một khoá outstanding; test thật bỏ qua `auctions`/`flow_rows`; CSV rỗng chưa test.
- **AC1 ĐẠT — seed thật ~13:31** (`uv run python -m etl omo --seed <csv>`, run 41 `success`): `sessions_new=248 auctions=823 rows_merged=3 flow_rows=317`; kho `macro.omo_session` **249 phiên** 2025-09-08 → 2026-09-08 (248 seed + 1 SBV); bốn dòng 14/08/2026 = 6.307,47 · 3.466,54 · 210,17 · 909,92 tỷ, thành viên 4/4 · 4/4 · 1/1 · 3/3, lãi suất 4,5; `omo_flow.outstanding_vnd` 07/09 = **250.778,26** · 08/09 = **249.363,44** tỷ, `complete = true` cả hai; `note` phiên 03/02/2026 = "seed FiinProX export 2026-09-08 · gộp 3 dòng cùng kỳ hạn" (03/02 có ba kỳ hạn gộp 7/28/56 nên đếm 3 ở phiên đó — tổng `rows_merged=3` cả file).
- **Thử tải giá lượt 1 (từ 13:10, ba luồng FiinTrade):** 100 mã/3,5 phút 5 retry · 200 mã/16 phút 24 retry, có mã hỏng trang 1 sau 4 lần (BMF, 0700823506) — chậm ~3× so với lượt đơn luồng 04/09 (0 retry). Kết quả cuối ghi khi lượt xong.
- **Task 3** bỏ quota quét sàn snapshot — `79dc046` + `9f6f557`: `QUOTA`/`LIMIT` gỡ, `plan_due`/`due_list` mất tham số; hai test e29 viết lại (trả đủ mọi cặp tới hạn), ba test e30 dùng `_quiet_floor` (implementer tìm thêm một test thứ ba ngoài brief; kỳ vọng `rows_written` 1 → 4 vì một issuer × bốn kind — reviewer lần ngược `plan_due`/`apply` xác nhận đúng). Review: một Important (docstring còn chữ "zero-QUOTA") — controller tự sửa hai dòng (§4.1 việc nhỏ), commit `9f6f557`.
- **Task 4** `classify_attempts` — `b0881c4`: migration `0021`, `MAX_ATTEMPTS = 3`, lọc `< 3` ở cả hai đường chọn bài, tăng đếm trong cùng giao dịch với `log_call` (dry-run không tăng), `stats.skipped_attempts`; review sạch. Minor để Task 12: `database/README.md` còn ghi head `0020`. Đường `--ids-file` (bộ gold) cố ý không lọc theo attempts.
- **Task 5** giao Opus ~13:45 (12 file + cả bộ test + hai phép kiểm production).
- **Task 5** advisory lock + `close_run_refused` — `91b5079` + vòng sửa `d115ff1` (Opus làm, Opus review, Sonnet sửa). Review xác nhận độc lập: 10 nhánh exit 1 đổi đúng, cả 14 chỗ gọi `open_run` không có đường rò khoá, pool an toàn, `SystemExit(1)` ra tới shell. Hai Important đều ở test quét tĩnh `test_e68` (plan ép nguyên văn) ⇒ phán quyết R6/R7 dưới. Phép kiểm dưới quyền production: `omo` trong container exit 0 (run 42, dùng bind-mount `backend/etl` chỉ đọc lên image cũ vì cấm rebuild); khoá bận mô phỏng bằng cách giữ `hashtext('market.price_backfill')` từ host dưới role `dlck_etl` rồi chạy `price --backfill` trong container ⇒ stderr `lock busy`, exit 1, **run 43 là dòng `failed` cố ý** (không phải sự cố), lượt backfill thật run 35 không bị đụng. ⚠️ **Khoá chỉ có hiệu lực sau khi rebuild image** (`docker compose up -d --build`, Task 11) — các container `dlck-fill-*` đang chạy code cũ, chưa giữ khoá.
- **Cả bộ test tại `d115ff1`: 1.161 passed, 3 failed, 3 skipped** — ba fail là `tests/docs/test_d01_docs_consistency.py` (`test_no_orphan_plan_docs`, `test_migration_count_matches_docs`, `test_schema_test_count_matches_docs`): hồ sơ mới, migration `0021`, test schema mới chưa được ghi vào tài liệu — **về xanh ở Task 12**, không phải lỗi code. `test_s05_macro::test_omo_flow_hand_computed` từng đỏ do test seed Task 2 để lại dòng `omo_flow` đã commit — sửa ở `d115ff1` (dọn xong thì `rebuild`).

### Phán quyết của controller trong phiên (chép từ sổ SDD, để không mất)

| # | Phán quyết | Vì sao | Chi phí nếu sai |
|---|---|---|---|
| R1 | Artifact SDD ở scratchpad phiên, ledger dự án là file này | CLAUDE.md cấm `.superpowers/` trong repo | không |
| R2 | Task 5 chạy cả bộ test; test nào `open_run` mà không `close_run` phải thêm `close_run` | khoá sống theo lượt trên connection riêng | một test exit 1 chập chờn, lộ ngay |
| R3 | Task 8: `main()` đọc `os.environ.get("ETL_LOG_DIR")` tường minh | `test_env_contract` quét code tìm người đọc | một test hợp đồng đỏ, sửa một dòng |
| R4 | Hợp đồng exit 1 là quét tĩnh `test_e68`, không tham số hoá 15 họ | ép 15 kịch bản fetch giả quá đắt cho một điều kiện cú pháp | job đặt cờ sai mà scanner không thấy — test DB của `close_run_refused` che phần cờ |
| R5 | Controller tự sửa hai docstring "zero-QUOTA" (Task 3) | §4.1 việc nhỏ 1–2 dòng | không |
| R6 | Scanner `test_e68` bỏ qua dòng chú thích, nhận dấu `# no-run:` cho nhánh không có sổ, đối chứng dương bằng snippet literal | bản gốc bị "qua" bằng một chú thích nhắc tên hàm — khẳng định sai | không |
| R7 | `close_run` nhả khoá trong `finally`, lỗi unlock chỉ log | khoá rò trong `news --loop` sống dai làm mọi vòng sau exit 1 | không |

### Minor để dành cho review toàn nhánh (Task 13)

Task 1: chưa test nhánh None của thành viên khi gộp; quét O(n). Task 2: INSERT auction lặp ở `store`/`store_seed`; test dry-run chỉ kiểm một khoá outstanding; test thật bỏ qua `auctions`/`flow_rows`; CSV rỗng chưa test. Task 4: `database/README.md` còn ghi head `0020` (Task 12). Task 5: docstring `close_run` về `coalesce` khi `close_run_refused` luôn truyền dict; bảng mã thoát ở `backend/README.md` cần thêm nghĩa "khoá bận" cho mã 1 và cờ `stats.guard_refused` (Task 12).

## ⏸️ Tạm dừng lần 2 — 2026-09-09 14:15, hết Task 5 theo chủ dự án ("càng tiết kiệm session càng tốt")

**Code:** nhánh `feat/etl-scheduler` HEAD = `d115ff1` + commit ledger này; cây sạch. Task 0–5 xong; **Task 6 là việc kế** (Opus): `backend/etl/scheduler/schedule.py` + `planner.py` theo plan. Sau đó 7 → 8 → 9 → 10 → 11 → 12 → 13.

**Đang chạy trên máy lúc 14:15 (Docker, sống qua phiên chat, không sống qua reboot):**
| Container | Việc | Ghi chú |
|---|---|---|
| `dlck-ingester-1` | daemon ghi tick, bật 13:51 theo chủ dự án để đo tải đồng thời | ngủ sau 15:05, **tự dậy 08:30 ngày 10/09** — không cần bật tay nữa; `docker compose up -d --build` ở Task 11 sẽ dựng lại nó |
| `dlck-fill-price-backfill` | run 35, con trỏ ~AG1 | > 2 ngày, chạy xuyên phiên; code cũ, chưa giữ khoá |
| `dlck-fill-fundamentals` | run 36, đang apply sau 6.091 lời gọi fetch (0 retry) | `financial_statement` vẫn 15.904 lúc 14:11, sẽ nhảy lên ~27 triệu khi apply xong |
| `dlck-fill-price-daily-1` | run 40, **thử tải lượt 1** ba luồng + ingester từ 13:10 | chậm ~3× (200 mã/16 phút, 24 retry); kết quả cuối ở `ops.etl_run` run 40 và `…\scratchpad\price-load-test-1b.log` |
| `dlck-fill-news-nguoiquansat` | run 39 | TinnhanhCK (37) và BNews (38) đã `success`; `article` 174 → 2.789 |

**Script nền (Git Bash `nohup`, chết nếu reboot; log ở scratchpad phiên này `C:\Users\tuanb\AppData\Local\Temp\claude\D--twan-projects-dulieuchungkhoan-vn\3394952d-87db-4d2f-b1b1-98a68f2e1aa6\scratchpad\`):**
- `price-load-test.sh 1430 dlck-fill-price-daily-2` → **thử tải lượt 2 lúc 14:30**, log `price-load-test-2b.log`.
- `eod-0909.sh` → **15:20** chạy tuần tự `screener` → `price` → `events`, đợi `dlck-fill-fundamentals` xong rồi `snapshot` → `fundamentals` → `omo`; `omo` lại lúc 18:05 và 21:35; cuối cùng in bảng `ops.etl_run` 8 giờ gần nhất; log `eod-0909.log`. Container tên `dlck-eod-<job>`, `--rm`.
- Nếu phiên sau không thấy log/container tương ứng ⇒ script đã chết, chạy tay theo mục "Việc còn lại trong ngày 09/09" ở lần dừng 1 (các lệnh không đổi).

**Việc còn lại của Task 0 (nạp đầu) sang phiên sau:** `snapshot --codes` trọn sàn (1.523 mã, sau khi BCTC xong — lệnh ở plan Task 0 Step 6) · `classify --limit 1000` lặp tới hết (Step 8) · ghi kết quả thử tải lượt 1–2 và kết luận AC3 · từ 12/09 `refdata --accept-drop` một lần (Step 10).

**Điểm nối lại phiên sau:** đọc mục này → `git status` (sạch, HEAD nhánh) → đọc `eod-0909.log`, `price-load-test-*b.log`, `ops.etl_run` từ run 40 → ghi số vào ledger → Task 6 theo `plan.md` (brief cắt bằng `scripts/task-brief PLAN 6 <OUTFILE ngoài repo>`; sổ SDD mới ở scratchpad mới, chép bảng phán quyết trên sang). Sáng 10/09 nhớ Task 11 Step 1 `docker compose up -d --build` **sau** khi Task 8 + 10 xong, không sớm hơn (image mới mới có scheduler và khoá).

## Kết phiên 09/09 — đọc lúc 16:30

- **Ingester (bật 13:51 giữa phiên theo chủ dự án, đo tải đồng thời):** ghi tới 15:05 rồi ngủ "chờ tới 2026-09-10T08:30". Frame: o 619.278 · i 196.383 · t 48.146 · idx 8.817 · ptm 98 · `dup_dropped` 415 · `orphan_tmp`/`replay_corrupt` 0; insert p99 ~70 ms suốt phiên, kể cả ATC và khi ETL ba luồng. ClickHouse hôm nay: `rt.trade` 48.146 · `rt.quote` 619.724 · `rt.bar_1m` 8.272. **Đối chứng `p1=0 p2=605 ok=57`**: `p1` (đếm đôi) = 0 là điều quan trọng; `p2` = mã có khối lượng nến thiếu quá ngưỡng so với khối lượng tích luỹ ngày — tất yếu vì nến chỉ có từ 13:51 còn tích luỹ tính từ 09:00, không phải lỗi. Phiên trọn 10/09 (AC10) mới là phép kiểm thật; kỳ vọng `p2 = 0` như 27–28/08.
- **AC3 thử tải giá lượt 1 (run 40):** bắt đầu 13:10 cùng lúc với backfill giá + backfill BCTC + sitemap, sau 13:51 thêm ingester, sau 14:30 thêm lượt 2. Kết quả: `success`, exit 0, **1.502/1.523 mã có dữ liệu, 21 mã hỏng (1,4 % < ngưỡng 2 %), 305 retry, 11.653 s = 3 giờ 14 phút** (so 38 phút, 0 retry hôm 04/09 đơn luồng), `rows_changed` 87.587, `latest_trading_date` 2026-09-09. Backfill giá cùng khoảng: 9 → 17 mã hỏng. **Kết luận §4.3:** mức ba luồng vào `getPriceData` *chạy được nhưng chậm 5 lần và sát ngưỡng guard*; mức một luồng đã đo an toàn. Không dò thêm. Ingester và BCTC không bị ảnh hưởng ⇒ nghẽn nằm ở truy vấn phía FiinTrade của endpoint giá, không phải rate limit (0 lần 429/418).
- **Lượt 2 (run 44, 14:30) và lượt khép ngày (run 46, 15:21) còn chạy** lúc 16:30 — ba lượt `market.price_daily` chồng nhau vì image cũ chưa có khoá; UPSERT idempotent nên vô hại, chỉ chậm. Script khép ngày: `screener` run 45 `success` 15:20 (guard "có phiên" qua); `price` đang chạy; `events` → `snapshot` → `fundamentals` → `omo` nối sau. Kết quả cuối ở `eod-0909.log` và `ops.etl_run` từ run 45.
- **Kho lúc 16:30:** `financial_statement` 27.282.128 (BCTC toàn sàn xong, run 36 `success`, 0 retry) · `article` 3.070 (sitemap 3/3 xong) · `price_daily` > 35.610 · `omo_session` 249.

## Nối lại lần 3 — 2026-09-09 16:35 → (Task 6–10 + chạy thử native)

Sổ SDD phiên này: `C:\Users\tuanb\AppData\Local\Temp\claude\D--twan-projects-dulieuchungkhoan-vn\4b3d1482-7b5a-4ef5-af27-afb5fa18da27\scratchpad\sdd\2026-09-09-etl-scheduler-and-db-fill\progress.md` (chép bảng phán quyết cũ sang, brief 6–13 cắt lại).

### Mốc code

| Task | Commit | Review | Ghi chú |
|---|---|---|---|
| 6 bảng lịch + planner thuần | `8d5897d` | Opus, sạch (6 Minor để cuối) | 13 test planner; **R8** ba dòng intraday mang `weekdays=ALL_DAYS`; **R9** không tạo `tests/etl/scheduler/__init__.py` (cây test không phải package) |
| 7 runner | `db55c17` + sửa `34648e1` | Opus: 1 Important (trần đếm cả daemon ⇒ thực tế 5) + 5 Minor; vòng sửa 1 re-review sạch | **R10** helper test `vn(h, mi, s)` (brief bỏ sót, literal chỉ khớp cách đọc này); **R11** daemon không chiếm slot; **R12/R13** gộp Minor ghim nhánh reset backoff + `spawn_fn` ném `OSError` được log thay vì nổ; **R14** prune theo ngày trong tên file đứng (spec §5.10 ghi "mtime" là bên lỗi thời) |
| 8 loop + CLI | `a48052d` + sửa `473d484` | Opus: 2 Important cần phán quyết + 8 Minor; vòng sửa 1 sạch | **R15** Step 5 chạy thử do controller làm; **R16** `FakePopen` của brief không thể thoả (`Runner.poll` bỏ qua con đã có `returncode`) ⇒ fake trung thực hơn, literal giữ nguyên; **R17** test `summary_lines` ghim đủ 5 bộ đếm + biên 24 h; **R18** lỗi trong một nhịp chỉ log, không giết scheduler; **R19** `engine.dispose()` chạy kể cả khi `shutdown()` ném; **R20** `SHUTDOWN_GRACE_S` 60 = `stop_grace_period` 60s giữ nguyên plan |
| 10 compose/env | `9636410` | Sonnet, sạch | **R22** test dùng `rsplit(":", 1)` vì `${CLICKHOUSE_BACKUP_DIR:-…}` có dấu hai chấm |
| vá SIGBREAK | `4d7f081` | Sonnet, sạch (1 Minor → sửa ở `019f97b`) | **R23** — xem "Lỗ hổng Windows" dưới |
| vá cooldown | `8be509d` | *(review chung dưới)* | **R24** — xem "Chạy thử" dưới |
| vá dòng trùng + test | `019f97b` | *(review chung 4d7f081..019f97b)* | **R26** dòng "đang chạy, bỏ qua lượt" in một lần mỗi con sống, không mỗi nhịp |

Task 9 (kiểm bù trên kho thật) làm bằng lượt chạy thử dưới; **R21**: bước "chạy chồng ⇒ exit 1" thử native vì image container còn cũ (chưa có khoá) — đường container kiểm lại ở Task 11 AC6.

### Lỗ hổng Windows tìm thấy trước khi chạy thử (R23)

Runner dừng con bằng `CTRL_BREAK_EVENT` (spec §5.10). Đo bằng script hai file ở scratchpad (`sig/parent.py`, `child.py`): con có `install_signal_handlers()` nhận CTRL_BREAK ⇒ **chết mã `0xC000013A`, không qua `except KeyboardInterrupt`** ⇒ dòng sổ sẽ treo `running`. Python ánh xạ CTRL_BREAK sang `SIGBREAK`, không phải `SIGINT`. Thêm handler `SIGBREAK` ⇒ con in từ nhánh KeyboardInterrupt, **rc 130** (giao sau khi lời gọi chặn hiện tại trả về — ca `sleep(30)` thoát sau ~30 s). Sửa: `core.shutdown` và `loop.main` cùng ánh xạ `SIGBREAK` khi nền tảng có; Linux không có thuộc tính này ⇒ không đổi gì. Kiểm thật ở lượt chạy thử: cả ba con đóng sổ `dừng tay (Ctrl+C)`.

### Chạy thử native 10 phút — 17:35:24 → 17:45:45 (`trial.py`, log `trial-1.log` ở scratchpad)

Dự đoán ghi trước ở sổ SDD lúc 17:25; sai một điểm: `omo` không tới hạn vì script khép ngày vừa chạy `omo` success 17:35:14 (≥ mốc 15:30). Còn lại đúng.

| Giờ | Sự kiện | Đối chiếu |
|---|---|---|
| 17:35:24 | `scheduler: 16 job, log_dir=D:\twan_projects\dlck-runtime\etl-logs, tick 20s`; in ngay bảng tóm tắt 24 h + "news --loop đang sống từ 17:35" (khởi động sau 06:00 ⇒ in một lần, Minor để cuối) | |
| 17:35:25 | nhịp 1 spawn: `news.collect` (daemon) · 3 intraday · `refdata` (bù mốc 08:00) · `price` (mốc 15:40 — hai lượt trước đều bắt đầu **trước** mốc) · `classify` (mốc 17:00) ⇒ **chạm trần 6**; `yahoo` daily bị con intraday cùng tên chặn ("đang chạy, bỏ qua lượt (mốc 11:00)") | AC5 bù đúng, trần đúng, lớp ngoài khoá đúng |
| 17:35:32 | `refdata` rc=0 7 s (run 57) | |
| 17:35:44 | **`classify` rc=2** — `column a.classify_attempts does not exist`: kho dev chưa áp migration `0021` (container `migrate` chỉ chạy khi `up`). Job chết **trước `open_run`** ⇒ sổ không có dòng ⇒ planner cấp lại mỗi nhịp ⇒ **spawn lặp mỗi 40 s** (17:36:04 · 17:36:44 · 17:37:24) | 🔴 lỗ hổng thiết kế: spec §5.8 giả định mọi lần thoát đều có dòng sổ |
| 17:36:00 | chạy chồng native `python -m etl price` ⇒ stderr `lock busy: lượt khác đang chạy — bỏ lượt này`, **rc=1**, run 58 `failed {"lock_busy": true, "guard_refused": true}` | **AC6 (native) đạt** |
| 17:38 | controller `alembic upgrade head` native: `0020 → 0021`; `classify` chạy thật từ 17:38:05 (run 59) | |
| 17:38:07 · 17:37:25 · 17:36:05 | intraday yahoo/wichart/binance success; nhịp hai binance 17:40:25 (đúng 300 s), wichart 17:40:25; `yahoo` daily chạy 17:38:45 ngay khi con intraday nhả tên, success 17:41:14 (run 60) | nhịp intraday và khoá tên đúng |
| 17:45:24 | CTRL_BREAK ⇒ scheduler **rc 0 lúc 17:45:45** (21 s: `stop.wait(20)` không bị SIGBREAK đánh thức, xử lý ở biên nhịp), stdout `dừng 3 tiến trình con, giết cứng 0`; sổ: `news.collect` 17:45:26 · `classify` 17:45:29 · `price` 17:45:45 đều `failed: dừng tay (Ctrl+C)`, **không dòng `running` mồ côi** | **AC7 (native) đạt**; R23 kiểm thật |

**Sửa sau chạy thử:** **R24** runner từ chối spawn lại cùng tên trong 10 phút sau khi con thoát mã ≠ 0 (RAM, cùng loại `_last_spawn`; daemon có backoff riêng; = đúng độ trễ thử lại exit 2 của planner) — bịt đường job chết trước `open_run` đập nguồn mỗi 40 s. **R26** dòng từ chối trùng in một lần mỗi con sống (đo: một dòng mỗi 20 s suốt lúc `price` chạy ⇒ ~360 dòng/ngày chỉ riêng price).

**Đính chính spec cần ghi ở Task 12:** §5.8 (mọi lần thoát có dòng sổ — sai khi chết trước `open_run`; nay có cooldown RAM), §5.10 (prune theo ngày trong tên file, không phải mtime; Windows cần `SIGBREAK`).

**Run 49 — đã giải thích ở review toàn nhánh (18:20):** run 49 `market.price_backfill` 17:30:16 success `subset: true`, 4 mã DIG/HUB/ITC/VPI, `stop_at` +20 phút **là lượt re-crawl lồng trong tiến trình của run 48 `market.snapshot`** (`snapshot_job._recrawl` → `price_job.run(backfill=True, codes=…, max_minutes=20)`, mã có ngày giao dịch không hưởng quyền trong cửa sổ; `stats.recrawl` của run 48 = `{"exit": 0, "codes": ["DIG","HUB","ITC","VPI"]}`; hai run đóng cùng giây 17:35:07). **Không phải test ghi vào kho dev** — mọi test chạm DB đều ghim `ETL_DATABASE_URL` sang DB test (30 chỗ), `load_dotenv` chỉ `setdefault`. Giả thuyết "nghi một test" ghi ở bản 17:50 của mục này là **sai**, sửa cùng lượt ở roadmap và README (M12). Hệ quả kỹ thuật: chính lồng ghép này là đường để `SystemExit(1)` khoá bận từ `open_run` giết cả tiến trình cha ⇒ I1 của review cuối (R28). Run 50 `fundamentals` (script khép ngày) success 0 lời gọi vì watermark đã là 2026-09-09 sau backfill — đúng.

## Khép phiên tối 09/09 — review toàn nhánh, đợt sửa, verify

**Task 12 (docs)** — `86c0cf7`, Opus một lượt, review Sonnet sạch; ba test `tests/docs` về xanh (21 migration · 16 file / 66 test seam · hàng index cho hồ sơ này). Roadmap **không** ghi ✅ cho lát 13.

**Task 13 bước 1 — review toàn nhánh `56a71ec..86c0cf7` (Opus, hai trục, báo riêng):**

| Trục | Kết luận |
|---|---|
| **Chuẩn** | 0 Critical · **2 Important** · 12 Minor. I1: `SystemExit(1)` khoá bận từ `open_run` là `BaseException`, lọt qua `except Exception` của `snapshot_job._recrawl` (gọi `price_job.run(backfill=True, codes=…, max_minutes=20)` trong tiến trình) và của vòng `news --loop --classify` ⇒ khoá `price_backfill` bận (thứ 7, hoặc lượt tay như cả ngày 09/09) giết cả tiến trình `snapshot`, dòng `market.snapshot` treo `running` không cờ. I2: `SHUTDOWN_GRACE_S` 60 = `stop_grace_period` 60s ⇒ không có biên độ trong container. |
| **Spec** | Đủ, kể cả bốn đính chính; không scope creep đáng kể; hai edge case §6 chưa có test (khoá nhả khi dispose; con treo `poll()`); luật phụ thuộc chặt hơn câu spec ("success con phải ≥ success mới nhất của cha") chưa được ghim ⇒ ghim bằng test. |
| **Run 49** | **Đã giải thích** — re-crawl lồng của run 48 `market.snapshot` (xem mục trên). Vệ sinh kho dev nguyên vẹn. |
| **Triage Minor để dành** | 8 mục DONE trong nhánh, còn lại CAN WAIT sang lát 14 (bảng đầy đủ ở sổ SDD phiên). |

**Đợt sửa duy nhất (Opus) `86c0cf7..bc66bfa`, re-review Opus sạch:**

| Commit | Nội dung | Phán quyết |
|---|---|---|
| `aac01f2` | `omo_store.LockBusy(SystemExit)`, raise `LockBusy(1)`; `_recrawl` bắt ⇒ `stats.recrawl = {"codes", "lock_busy": true}`, snapshot đóng `success`; `news --loop --classify` bắt và đi tiếp; test e30/e56/e67 | **R28** |
| `13a0ad7` | dòng cooldown in một lần mỗi cửa sổ `(name, failed_at)`; `open_run` đóng connection khoá nếu chính lệnh acquire ném | M1, M3 |
| `31f7077` | compose `etl.stop_grace_period: 90s` (như ingester), `test_d03` ghim 90s, runner giữ 60 | **R27** (thay R20) |
| `753a192` | README: định dạng dòng thoát thật `[<ts>] <job> rc=<rc> <s>s (<lý do>)`; đoạn "dòng `subset` lồng từ snapshot"; roadmap sửa run 49; spec thêm một dòng đính chính | M8, M12 |
| `bc66bfa` | test ghim luật phụ thuộc chặt (con success 18:05 < cha 18:12 ⇒ vẫn tới hạn; 18:20 ⇒ không) | Spec |

Re-review ghi thêm ngoài phạm vi (để lát 14): `engine.connect()`/`execution_options` còn ngoài `try` của M3; `stats.recrawl` có 4 hình chưa ghim; test e56 chỉ ghim một vòng. Controller tự thêm dòng đính chính I2 vào spec (§4.1 việc một dòng).

**Chạy đêm 09→10/09 (R25):** scheduler native từ 17:48:13 — tiến trình scheduler nạp cây tại `019f97b` (có SIGBREAK, cooldown, dedupe; **chưa** có `LockBusy`/R27 vì hai vá đó vào sau 18:26), còn mỗi job con là interpreter mới đọc cây hiện tại nên đã mang `LockBusy`, wrapper tự gửi CTRL_BREAK ~07:18; tới 18:36 chỉ có rc=0 (intraday đúng nhịp 300/600 s), chưa có mã ≠ 0. Sáng 10/09 đọc `trial-night.log` + `ops.etl_run` từ run 63 trước khi `docker compose up -d --build`.

**Task 13 bước 2 — verify tại `bc66bfa` (controller chạy, output thật):**

```
uv run pytest tests -q            → 1206 passed, 3 skipped in 98.69s (0:01:38)
git grep -c "\[DEBUG-" -- backend → 0 hit
docker compose config --quiet     → rc=0
```

**Task 13 bước 3 (merge) chờ AC9** — ba ngày chạy thử 10–12/09 + AC4–AC7/AC10 trong container (Task 11). Điểm nối lại: memory `slice-13-in-progress` và mục này.

## Sáng 10/09 06:40 — đọc lượt chạy đêm native (17:48:13 → còn chạy, tự dừng ~07:18)

| Mục | Số đo *(đo 2026-09-10 06:40)* |
|---|---|
| Con thoát | **398 lượt, tất cả rc=0**; 0 mã ≠ 0, 0 lỗi nhịp, 0 dòng cooldown, 0 giết cứng |
| Intraday | binance 155 · wichart 154 · yahoo 77 lượt, đúng nhịp 300/300/600 s suốt đêm |
| Mốc daily | omo 18:00 + 21:30 · events 18:10 · snapshot 18:15 (chuỗi sau events) · fundamentals 19:33 (chuỗi sau snapshot, 0 lời gọi vì watermark) · fred 20:00 + 05:00 · ecb + lbma 22:30 · classify 17:48/20:59/23:45 — **không sót mốc nào** |
| `news --loop` | 134 vòng, sống liên tục từ 17:48 |
| Tóm tắt 06:00 | in đúng lúc 06:00 (giữa 05:59:27 và 06:01:47), 20 dòng job + dòng daemon |
| Sổ | 3 dòng `running` = đúng 3 con đang sống lúc đo (collect, yahoo, wichart intraday); không dòng mồ côi |
| Log | 18 file `<job>-2026090{9,10}.log` ở `dlck-runtime/etl-logs` |

**Classify (3 lượt × `--limit 1000`):** 3.000 lời gọi MiniMax, 8,05 triệu token vào + 2,55 triệu ra, 5 bài hỏng ở lượt đầu; quota Token Plan tuần 87 % → 80 %. Tồn đọng `news.article` chưa phân loại 4.396 → **1.356**, hết trong ngày với 8 mốc.

**Hai việc ngoài scheduler:** (1) container backfill giá cũ (run 35) **`failed` lúc 02:02** — `SourceDown: 10 mã liên tiếp hỏng` sau 194 mã, con trỏ `CK8`, 68 mã hỏng, 1.099 retry, 4 lần tạm nghỉ vì nguồn: `getPriceData` FiinTrade nghẽn cả đêm, không phải lỗi scheduler; con trỏ còn, lượt thứ 7 (`weekly_once`) hoặc chạy tay nối tiếp. (2) run 111 `price_backfill` lồng của snapshot 18:15 (re-crawl DIG/HUB/ITC/VPI): `budget_hit` 20 phút, 41 retry, HUB hỏng — cùng nguyên nhân nghẽn nguồn.

Kết luận: đường scheduler chạy 13 giờ không lỗi; điểm yếu duy nhất đêm qua nằm ở nguồn FiinTrade giá. Tiếp: chờ native tự dừng 07:18 → Task 11 Step 1 `docker compose up -d --build` ~07:30.

**07:18 — lượt native khép:** wrapper gửi CTRL_BREAK 07:18:16 ⇒ scheduler **rc 0 lúc 07:18:36**, `dừng 2 tiến trình con, giết cứng 0`; `news.classify` mốc 07:00 (run 621) đóng `failed: dừng tay (Ctrl+C)`; `news --loop` đang ở khoảng nghỉ giữa hai vòng nên không có dòng mở; **0 dòng `running`**, không còn tiến trình python. Tổng 13 giờ 30 phút chạy không người, **AC7 native lần hai đạt**.

**R29 (chủ dự án chốt 07:00):** backfill giá chạy 24/7 tới `pass_complete` — xem sổ SDD phiên và mục tiếp theo; review Opus ra C1 (một mã hỏng mãi làm pass đứng yên vô hình) + I2/I3/I4 ⇒ phán quyết R30–R33, vòng sửa 1 đang chạy; rebuild container lùi tới khi vòng sửa xanh.

## Task 11 — nghiệm thu trong container (10/09)

**R29 khép:** vòng sửa 1 `e5fafff` + `2615f8e` + `7ae8d91` (cap 6 lần nghỉ mỗi mã rồi đi tiếp · ngủ lát 30 s · reset thang khi `CodeInvalid` · backoff daemon theo tên · dòng "đã xong vòng" một lần · docs), re-review Opus sạch; cả bộ **1214 passed, 3 skipped** tại `7ae8d91`. Phán quyết R29–R33 ở sổ SDD phiên, tóm tắt: R29 backfill là daemon 24/7 tới `pass_complete` (chủ dự án chốt 07:00) · R30 bỏ qua mã sau 6 lần nghỉ liên tiếp cùng con trỏ · R31 backoff theo tên · R32 ngủ lát 30 s (Windows không đánh thức `sleep` bằng CTRL_BREAK) · R33 chấp nhận re-crawl snapshot bị khoá suốt pass, sau `pass_complete` chạy tay một lần `price --backfill --codes <mã có ngày không hưởng quyền trong pass>` **và** các mã trong `stats.failed_tickers` của pass.

**Step 1 — 07:37 `docker compose up -d --build`** (lần `up` đầu sau khi dừng ingester 09/09 07:59): build xong, `migrate` `Exited (0)` (alembic head `0021`, ClickHouse không có gì mới), `etl`/`api`/`ingester` `Up`. Log `etl`: `scheduler: 16 job, log_dir=/var/lib/dlck/etl-logs, tick 20s`, bảng tóm tắt in ngay (khởi động sau 06:00), `news --loop đang sống từ 07:38`, **`price --backfill đang sống từ 07:38`** — log con: `tiếp tục sau con trỏ CK8: còn 1313 mã · hạn không đặt`. `classify` mốc 07:00 được thử lại (dòng 07:00 của lượt native đóng `dừng tay` lúc 07:18 = 1 failed không cờ, đã quá 10 phút). Ingester: `ngoài phiên, chờ tới 2026-09-10T08:30`. Volume `etl_logs` có 6 file log ngay nhịp đầu.

Lịch nghiệm thu còn lại hôm nay: AC5 stop 11:25 / start 11:35 (bắt mốc omo 11:30) · AC7 stop giữa `price` ~15:45 · AC6 chạy tay `events` trùng 18:10 · AC10 ingester sau 15:05 · AC4 sáng 11/09.
