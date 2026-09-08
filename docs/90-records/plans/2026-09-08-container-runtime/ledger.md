# Ledger — lát 12: chạy được trong container

**Nhánh:** `feat/container-runtime` · **Spec:** [`spec.md`](spec.md) · **Plan:** [`plan.md`](plan.md)

Mỗi task ghi output THẬT của bước kiểm (đỏ trước · xanh sau · lệnh nghiệm thu). Không dán giá trị secret.

## Task 0 — xuất phát 2026-09-08

*(điền khi thực thi Task 0)*

- `git log --oneline -1`:
- `docker ps --format '{{.Names}} {{.Status}}' | grep infra`:
- `docker volume ls --format '{{.Name}}' | grep -E 'infra|dlck'`:
- `cd backend && uv run pytest tests -q` (kho cũ, `.env` cũ):
