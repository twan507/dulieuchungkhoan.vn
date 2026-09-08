# Ledger — lát 12: chạy được trong container

**Nhánh:** `feat/container-runtime` · **Spec:** [`spec.md`](spec.md) · **Plan:** [`plan.md`](plan.md)

Mỗi task ghi output THẬT của bước kiểm (đỏ trước · xanh sau · lệnh nghiệm thu). Không dán giá trị secret.

## Task 0 — xuất phát 2026-09-08

- `git log --oneline -1`: `e1c9c27 docs(plan): slice 12 implementation plan, 12 TDD tasks, with a spec erratum on the seed step`
- `docker ps … | grep infra`: `infra-clickhouse-1 Up 2 days (healthy)` · `infra-postgres-1 Up 2 days (healthy)` · `infra-redis-1 Up 2 days (healthy)` — kho cũ còn chạy, giữ tới Task 9
- `docker volume ls … | grep -E 'infra|dlck'`: `dlck-infra_chdata` `dlck-infra_pgdata` `dlck-infra_redisdata` `infra_chdata` `infra_pgdata` `infra_redisdata` (sáu volume sẽ xoá ở Task 12) · `tutor-infra_pgdata` (**dự án khác, không đụng**)
- `cd backend && uv run pytest tests -q` (kho cũ, `.env` cũ): **`1072 passed, 2 skipped in 92.23s`** — khớp số `database/README.md` sở hữu

Sổ SDD (brief · report · gói diff review) nằm ở scratchpad ngoài repo, đúng luật cấm `.superpowers/` trong repo (CLAUDE.md §4.1).
