# Tiêu chí chấm — hình dạng scheduler trong service `etl` (lát 13), viết TRƯỚC khi sinh phương án

Ngày 2026-09-09. Quyết định khó đảo (chọn thư viện / ranh giới module) ⇒ §4.8 CLAUDE.md.

## Dữ kiện đã kiểm (đọc code + tài liệu 2026-09-09 sáng)

- `backend/etl/__main__.py`: CLI `python -m etl <job> [cờ]` cho 15 họ; không tham số = vòng heartbeat 15 s (`etl/heartbeat.py`, test `tests/test_heartbeat.py`). Lát 13 thay nhánh không tham số bằng scheduler; compose service `etl` chỉ đổi `command` (`docker-compose.yml`, hợp đồng `tests/docs/test_d03_compose_contract.py` ghim tập biến `environment` của `etl`).
- Mã thoát hợp đồng (test `tests/etl/test_e63_exit_code_contract.py`): 0 ghi xong · 1 guard từ chối (dữ liệu lành) · 2 lỗi thật · 130 dừng tay. `core/shutdown.py` nâng SIGTERM thành KeyboardInterrupt ⇒ job đóng sổ `ops.etl_run` "failed: dừng tay (Ctrl+C)", exit 130; compose `stop_grace_period` của `etl` = 60 s.
- Sổ `ops.etl_run` (migration 0008): `run_id, job, started_at, finished_at, status ∈ {running,success,failed}, stats jsonb, error`. Tên job: `market.refdata` `market.screener` `market.price_daily` `market.price_backfill` `market.events` `market.snapshot` `market.fundamentals` `macro.omo_crawl` `macro.wichart` `global.fred` `global.ecb` `global.lbma` `global.yahoo` `global.binance` `news.collect` `news.classify` `news.backfill_sitemap:<src>`. Lượt `--intraday` và lượt trọn CÙNG tên job, khác `stats.intraday=true`; lượt `--keys/--codes` có `stats.subset=true`; `--dry-run` có `stats.dry_run=true`.
- Múi giờ: mọi "hôm nay" qua `core.clock.now_vn()/today_vn()`; `tests/core/test_tz_contract.py` quét AST cấm `datetime.now()`/`date.today()` trần trong `backend/` ngoài test. Compose đặt `TZ=Asia/Ho_Chi_Minh`; Postgres giữ UTC.
- Khuôn vòng lặp sẵn có: `ingester/main.py::daemon()` (clock/sleep tiêm được, ngủ lát ≤ 60 s, `asyncio.Event` stop, mã ≥ 2 thoát để Docker restart có giãn cách) và `next_window()` thuần, test bằng literal ở `tests/ingester/test_i16_daemon.py`.
- Ingester là service riêng, KHÔNG đi qua scheduler.
- `pyproject.toml` KHÔNG có thư viện scheduler nào (fastapi, uvicorn, sqlalchemy, alembic, psycopg, clickhouse-connect, websockets, redis, httpx, beautifulsoup4, anthropic; dev: psutil, pytest, pyyaml).
- Job dài: `price --backfill --stop-before-open` ~20 giờ, `fundamentals --backfill` ~1 h 45, quét sàn snapshot trọn 40–75 phút; job ngắn: fred/fx/lbma ~2 phút, wichart 15 s, screener 1 phút, price ngày 38 phút, events 2,5 phút.
- `news --loop` là tiến trình sống dai (vòng 300 s, sitemap mỗi 3 vòng, `--classify N` tuỳ chọn, Ctrl+C dừng sạch).
- Dockerfile đã tạo `/var/lib/dlck/logs` thuộc `appuser`; ingester ghi `ingester-YYYYMMDD.log` vào volume `ingester_logs`.
- RAM VPS (overlay `docker-compose.vps.yml`): API + ETL + tin có ~1,1 GB; mỗi tiến trình con Python chưa đo (~60–120 MB ước).
- Native trên dev: Windows 11, `uv run python -m etl`; SIGTERM không giao cho handler Python trên Windows (Ctrl+C là đường dừng).

## Quyết định chủ dự án đã chốt (brainstorm 2026-09-09 sáng) — KHÔNG mở lại

1. Bảng lịch giờ VN, trong code:
   - Ngày làm việc: `refdata` 08:00 · `screener` 15:20 · `price` 15:40 · `events` 18:10 → `snapshot` (ngay sau, cùng chuỗi) → `fundamentals` (sau snapshot).
   - `omo` 11:30 · 15:30 · 18:00 · 21:30 (mọi ngày).
   - `wichart` trọn 08:15 mọi ngày · `yahoo` trọn 11:00 · `binance` trọn 07:15 · `fred` 05:00 + 20:00 · `fx` + `lbma` 22:30.
   - Nhịp 24/7: `yahoo --intraday` 10 phút · `binance --intraday` 5 phút · `wichart --intraday` 5 phút.
   - `classify --limit 1000` 8 mốc: 07:00 09:00 11:00 13:00 15:00 17:00 19:00 21:00.
   - `news --loop` = tiến trình con sống dai, scheduler giữ sống + khởi động lại nếu chết; KHÔNG gọi từng vòng.
   - `price --backfill --stop-before-open` thứ 7 00:05, chỉ tới khi `pass_complete` lần đầu rồi tắt (cờ/hằng trong bảng lịch).
   - Lát 14 sẽ thêm một dòng job giám sát.
2. Chạy bù (6 luật): chỉ mốc CỦA HÔM NAY (giờ VN) đã qua mà `ops.etl_run` chưa có `success` cùng ngày cho job đó (bỏ qua lượt `stats.intraday/subset/dry_run`), theo đúng thứ tự phụ thuộc; job nhịp ngắn và `news --loop` không bù; OMO nhiều mốc chung tên: bù khi mốc gần nhất đã qua mà chưa có success sau mốc đó; exit 1 không bù lại trong ngày; exit 2 thử lại đúng 1 lần sau 10 phút rồi thôi; backfill giá thứ 7 lỡ mốc thì bù.
3. Chặn chạy chồng: **advisory lock Postgres theo tên job, lấy trong job lúc mở sổ** (`pg_try_advisory_lock`), lượt trùng thoát ngay có ghi sổ; scheduler thêm lớp ngoài: không spawn khi tiến trình con cùng job còn sống.
4. Log: mỗi job một file theo ngày trong volume mới `etl_logs` (`<job>-YYYYMMDD.log`), giữ 30 ngày; scheduler stdout một dòng mỗi lượt (job, giờ, mã thoát, thời lượng) + bảng tóm tắt mỗi sáng (đếm exit 2).
5. Cùng code chạy native (`uv run python -m etl`, một cửa sổ) và container; SIGTERM → chuyển cho con, chờ ≤ 60 s.
6. Ngày lễ: không có lịch nghỉ trong scheduler.

## Tiêu chí (chấm ✓✓ / ✓ / ~ / ✗ cho từng phương án)

| # | Tiêu chí |
|---|---|
| a | Cùng code chạy native (Windows, `uv run`) và container; chỉ đổi `command` của service `etl`; giờ VN qua `core.clock`, không `datetime.now()` trần |
| b | Bảng lịch đọc được trong một màn hình: mốc ngày, nhịp, daemon con, thứ tự phụ thuộc — thêm một dòng cho lát 14 là đủ |
| c | Spawn tiến trình con `python -m etl <job>`; log mỗi job một file theo ngày; mã thoát 0/1/2/130 được đọc và ghi |
| d | Chạy bù đúng 6 luật, suy từ `ops.etl_run`, không cần bảng trạng thái mới (hoặc nếu cần, nói rõ và biện minh) |
| e | Chặn chạy chồng hai lớp (advisory lock trong job + scheduler không spawn trùng), phủ cả lượt tay `docker compose run` |
| f | Dừng sạch: SIGTERM → con nhận tín hiệu → đóng sổ ≤ 60 s; scheduler chết → Docker dựng lại → bù đúng; sống qua reboot |
| g | Test bằng literal, seam rõ (đồng hồ/sleep/spawn tiêm được), không test tautological; liệt kê seam |
| h | Bán kính hỏng: một job lỗi không đổ scheduler; rollback = một `git revert` |
| i | Phụ thuộc mới: 0 hoặc biện minh rõ (maintain, tz, cron, kích thước) |
| j | Kích thước: ước dòng code + số test + thời gian làm (giờ) |
| k | Trần tiến trình con đồng thời (news loop + 3 intraday + 1 ngày + backfill ≈ 6) và cách giới hạn |

Mỗi phương án PHẢI tự khai rủi ro của chính nó và điều kiện đảo ngược.
