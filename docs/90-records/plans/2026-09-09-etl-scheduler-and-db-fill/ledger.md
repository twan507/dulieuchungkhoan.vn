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
