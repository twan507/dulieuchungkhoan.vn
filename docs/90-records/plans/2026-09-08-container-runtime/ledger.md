# Ledger — lát 12: chạy được trong container

**Nhánh:** `feat/container-runtime` · **Spec:** [`spec.md`](spec.md) · **Plan:** [`plan.md`](plan.md)

Mỗi task ghi output THẬT của bước kiểm (đỏ trước · xanh sau · lệnh nghiệm thu). Không dán giá trị secret.

## Task 0 — xuất phát 2026-09-08

- `git log --oneline -1`: `e1c9c27 docs(plan): slice 12 implementation plan, 12 TDD tasks, with a spec erratum on the seed step`
- `docker ps … | grep infra`: `infra-clickhouse-1 Up 2 days (healthy)` · `infra-postgres-1 Up 2 days (healthy)` · `infra-redis-1 Up 2 days (healthy)` — kho cũ còn chạy, giữ tới Task 9
- `docker volume ls … | grep -E 'infra|dlck'`: `dlck-infra_chdata` `dlck-infra_pgdata` `dlck-infra_redisdata` `infra_chdata` `infra_pgdata` `infra_redisdata` (sáu volume sẽ xoá ở Task 12) · `tutor-infra_pgdata` (**dự án khác, không đụng**)
- `cd backend && uv run pytest tests -q` (kho cũ, `.env` cũ): **`1072 passed, 2 skipped in 92.23s`** — khớp số `database/README.md` sở hữu

Sổ SDD (brief · report · gói diff review) nằm ở scratchpad ngoài repo, đúng luật cấm `.superpowers/` trong repo (CLAUDE.md §4.1).

## Task 1–3 — hình dạng cấu hình P2 (2026-09-08)

- **Task 1** `1182b99` — `core/env.py`: `compose_urls` · `check`; 9 test `test_env.py` (RED `ImportError` → GREEN `11 passed` cùng hai test hợp đồng cũ). Review sạch, 2 Minor để dành.
- **Task 2** `68aa1d5` + `21ef1cc` — `.env.example` nguyên tố + `test_env_contract.py` (4 test; RED 3/4 trên file cũ → GREEN `13 passed`). **Ruling khi thực thi:** bỏ vế cấm mọi khoá đuôi `_URL` (`LLM_BASE_URL` là khoá tuỳ chọn hợp lệ), giữ vế `ASSEMBLED_KEYS` — plan `15f6e71`, `5cf5c52`. Review: 1 Important (docstring lệch phán quyết) → sửa `21ef1cc`, re-review đóng.
- **Task 3** `00a7fde` — conftest đọc `POSTGRES_DB`, tên DB test lấy từ URL và kiểm identifier; `alembic.ini` `prepend_sys_path = backend`; `migrations/env.py`, `ch_migrate.main`, `ch_backup.main` gọi `load_dotenv()`; `resolve_backup_dir` theo gốc repo (2 test literal). Kiểm: `test_t06_backup` + `tests/schema` + hợp đồng env **76 passed**.
- **Giả định spec 2.2.4 ĐÓNG:** từ gốc repo, shell không export biến DB nào, `uv run --project backend alembic -c database/alembic.ini current` in `0020 (head)` — `env.py` tự ráp `DATA_DATABASE_URL`.

## Task 4–5 — múi giờ, tín hiệu dừng, về hưu đồ Windows (2026-09-08)

- **Task 4** `4d0384f` — `core/clock.py` (`VN` · `now_vn` · `today_vn`, naive ⇒ `ValueError`); ba chỗ `date.today()` trần đổi sang `today_vn()` (`refdata_job`, `system_prompt`, `ch_backup.run_backup`); `test_tz_contract` quét 129 file, RED đúng 3 hit → GREEN. Kiểm: `tests/core` + `tests/agent` + `test_e10` + `test_t06` **217 passed**. Ruling: docstring `clock.py` không được viết nguyên `date.today()` vì phép kiểm quét cả docstring. Review sạch, 2 Minor để dành.
- **Task 5** `c9a4998` + `3e4e39d` — `core/shutdown.py` (SIGTERM → `KeyboardInterrupt`), gắn đầu `main()` của `etl`/`ingester`; xoá `core/console.py` + test, `scripts/register-tasks.ps1`, `scripts/stack.mjs`, `stack.test.mjs`, `package.json`; `price_job.banner` → `log.info`. Kiểm: 65 passed, 1 skipped (test SIGTERM tiến trình thật chỉ chạy POSIX). 🔴 **Review bắt được lỗ có sẵn:** `ingester/main.py` không có `except KeyboardInterrupt`, ngoại lệ từ handler thoát thẳng `asyncio.run()` — đuôi phiên (xả hàng đợi, đối chứng) không chạy, với cả Ctrl+C từ trước. **Ruling:** Task 5 chỉ thu hẹp docstring (`3e4e39d`); đường dừng tử tế `install_loop_stop` (tín hiệu → `stop.set()` trên loop) chuyển sang Task 6 — spec có đính chính, plan Task 6 Step 3b (`8c9b806`).

## Task 6 — ingester thành daemon (2026-09-08)

- `b604386` — `SESSION_START` · `next_window` · `daemon` · `install_loop_stop` (Step 3b); `run()` rẽ nhánh: không `--minutes` ⇒ daemon, có ⇒ một phiên có hạn như cũ. RED `ImportError: SESSION_START` → GREEN `tests/ingester` **181 passed, 1 skipped**.
- Implementer tự khai hai lỗi trong thiết kế Step 3b của tôi: (a) `session_timer` và tín hiệu dừng dùng chung một event ⇒ hết phiên là daemon thoát, nhánh "chờ phiên kế" không bao giờ chạy thật; (b) ba test cũ gọi `run("run")` không `minutes` sẽ ngủ tới 08:30 nếu chạy ngoài giờ. **Ruling Step 3c** `21dfdb1`: event `shutdown` (tín hiệu) tách khỏi `stop` của từng phiên, nối bằng `_relay`/`_session_with_relay`, mỗi phiên một `stop` mới; ba test cũ đổi sang `run("run", minutes=1)`.
- Review bắt thêm một Important từ plan: cài `install_loop_stop` trước nhánh chọn chế độ làm `count`/`reconcile` mất đường ngắt trên POSIX. **Ruling Step 3d** `371b427`: chỉ cài ở `run`/`measure`, test dispatcher bằng recorder. Re-review đóng. Kiểm cuối `test_i16` 13 test `-W error` sạch; 3 Minor để dành.
- ⚠️ Nhánh POSIX của `install_loop_stop` (SIGTERM thật → xả + đối chứng) chưa chạy được trên máy dev Windows — nghiệm thu ở Task 10 (AC-SIGTERM trong container).

## Task 7 — image tự đủ, compose gốc, overlay VPS (2026-09-08)

- `7943b72` — `deploy/backend.Dockerfile` context gốc repo (`/app/backend` + `/app/database`, `REPO_ROOT` trong image = `/app` — probe `docker run` in `backend database` rồi `/app`); `.dockerignore` gốc (`.env*`, `backend/tests`, `.venv`, `docs`); `docker-compose.yml` gốc `name: dlck` (9 service, neo `x-app`, 6 volume); `docker-compose.vps.yml` chuyển nguyên từ `deploy/infra`; ba file compose cũ + `backend/.dockerignore` xoá; `pyyaml` vào dev; `test_d03_compose_contract.py` 7 test (RED `FileNotFoundError` → GREEN). `docker compose config --quiet` OK, `docker compose build migrate` OK. Review sạch (reviewer tự chạy lại contract test và `config --quiet`); ghi nhận rác có sẵn: `test_c99_dedup_probe.py:20` import ba tên đã dời khỏi `tests/clickhouse/conftest.py` từ 2026-09-07, chỉ vỡ khi `RUN_PROBE=1` — báo, không sửa (§4.4.3).
