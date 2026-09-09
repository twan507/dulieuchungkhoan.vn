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
