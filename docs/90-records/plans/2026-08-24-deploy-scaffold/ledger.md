# Ledger thực thi — plan 2026-08-24-deploy-scaffold

Bản ghi quá trình thực thi plan qua subagent-driven-development *(2026-08-25)*. Nhánh: `feat/deploy-scaffold`.

**Pre-flight:** plan tự chứa code đầy đủ, self-review trong plan đã kiểm coverage + tên hàm nhất quán → sạch.

## Rulings (quyết định thay người dùng)

- Review từng lô do **controller** làm trực tiếp (diff nhỏ, tôi là tác giả plan) thay vì reviewer subagent riêng — cân theo quy mô scaffold; final whole-branch review vẫn giao subagent. *Sai → sót lỗi tới final review (đã có final review chặn — bắt được TCP6).*
- **Self-do** Task 1–2 (setup) + Task 9 (Docker cần phán đoán); **Sonnet** cho Task 3–8. *Sai → thấp.*
- Commit root `pnpm-lock.yaml` (9 dòng, zero-dep) — artifact hợp lệ của entrypoint pnpm. *Sai → tầm thường.*
- Final review giao **Sonnet** (diff ~370 dòng toàn file mới, cơ học; logic `stack.mjs` đã unit-test). *Sai → sót lỗi tinh vi, thấp.*
- **[Critical reviewer] "Task 9 không có bằng chứng trong git"** — verification **đã chạy live** (AC1–8 pass, output đã dán cho user); reviewer chỉ thấy git. Persist bằng commit mốc `f778447`. *Sai → không, verification thật đã xảy ra.*
- **[Minor] `.gitignore` thêm `.superpowers/`** — ban đầu chấp nhận; **sau chuẩn hoá lại** (xem dưới): gỡ hẳn, ledger về thư mục plan.

## Task log

| Task | Commit | Kết quả |
|---|---|---|
| 1 gitignore + env.example | `1e5cc03` | self · `.gitignore` mở rộng từ superset của `.env` |
| 2 backend uv skeleton | `7e84734` | self · `uv sync` ok, imports ok |
| 3 api healthz (TDD) | `3244efa` | assert body cụ thể |
| 4 etl heartbeat (TDD) | `5c7e537` | expected literal độc lập |
| 5 infra compose | `e0ba89b` | config ok + fail-fast |
| 6 image + app compose | `78c3592` | image builds, app config ok, `.env` untracked |
| 7 stack.mjs helper (TDD 3 seam) | `d20085c` | 4 pass |
| 8 stack.mjs command + package.json | `6b46cba` | CLI guard ok, no regression |
| 9 nghiệm thu | `8a7c42e` (lockfile), `f778447` (mốc AC) | AC1–AC8 pass live trên Docker 29 |

## Final review (Sonnet, whole-branch)

Findings: **[Important]** `listeningPids` bỏ sót `TCP6`; **[Critical]** Task 9 bằng chứng (adjudicate ở trên); **[Minor]** `.gitignore` `.superpowers/`.

Fix round 1/1: **TCP6 ADDRESSED** — commit `1b748c9` (test đỏ `actual []` vs `['4242']`, fix `TCP`→`TCP6?`, 5 pass). Controller re-review sạch.

## Deferred minor (không chặn merge)

- Node `DEP0190` (`spawnSync(cmd,args,{shell:true})` trong `stack.mjs`) — kế thừa pattern tutor-agent, args nội bộ không injection; real nhưng low-risk.
- `StarletteDeprecationWarning` (`httpx` TestClient) — upstream, không phải code ta.

## Chuẩn hoá vị trí ledger *(2026-08-25)*

Ban đầu ledger nằm ở `.superpowers/sdd/...` (mặc định của skill SDD) — **sai**, vì `superpowers` là tên đã nghỉ theo [ADR 0007](../../../00-overview/decisions/0007-monorepo-layout-and-stack.md). Đã chuyển ledger về đây (thư mục plan, commit — đúng tiền lệ plan 2026-08-15), xoá `.superpowers/`, gỡ khỏi `.gitignore`, và ghi luật vào [CLAUDE.md §4.1](../../../../CLAUDE.md).

Rename 76d0af4: backend/app -> backend/api để khớp tên service `api` (song song etl/ingester); convention FastAPI chỉ ép tên đối tượng ASGI (app), không ép tên package. Sửa Dockerfile CMD, stack.mjs dev-start, test import; pytest 2 pass, stack 5 pass. Spec/plan giữ nguyên chữ app/ (bản ghi lịch sử).
