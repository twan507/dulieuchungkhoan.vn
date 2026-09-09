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
