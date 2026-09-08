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
