# Spec — Khung đóng gói & vận hành (deploy scaffold)

**Ngày:** 2026-08-24 · **Trạng thái:** đã duyệt thiết kế qua thảo luận với chủ dự án (phiên 2026-08-24) · **Loại:** kiến trúc (dựng tầng đóng gói mới cho cả monorepo)

## 1. Mục tiêu

Dựng **khung đóng gọi một-nút** cho toàn dự án, học lại nguyên bộ "tinh hoa deploy" đã chuẩn hoá ở repo tham chiếu [`twan507/tutor-agent`](https://github.com/twan507/tutor-agent) *(đọc 2026-08-24)* và áp vào stack của dulieuchungkhoan.vn (Next.js · FastAPI · Postgres · Redis · ClickHouse — [ADR 0007](../../../00-overview/decisions/0007-monorepo-layout-and-stack.md)).

Hai chế độ, mỗi chế độ một lệnh:
- **Dev** (`pnpm dev-start`): infra trong Docker, **app chạy native** trên host với hot-reload gốc.
- **Deploy** (`pnpm docker-up`): **toàn bộ** trong Docker trên một máy chủ đơn.

Khung này là **hình chiếu deploy** của ranh giới tiến trình đã chốt ở [service-topology.md](../../../20-design/service-topology.md).

> **Chốt thiết kế trong phiên (khác giả định ban đầu):** dev **không** bind-mount code vào container. Học theo tutor-agent: **app native + infra docker** — né sạch nỗi đau file-watch qua bind-mount trên Windows.

## 2. Tiêu chí nghiệm thu

Khung coi là xong khi mọi mục sau kiểm được bằng lệnh thật:

| # | Nghiệm thu |
|---|---|
| AC1 | `pnpm dev-start`: Postgres + Redis (docker) **healthy**; `api` chạy native `:8000` với `--reload`, `GET /api/healthz` → `200`; `etl` chạy native, in một nhịp scheduler. Ctrl+C tắt `api`+`etl`, **Postgres+Redis vẫn chạy** |
| AC2 | `pnpm dev-stop`: giải phóng cổng 8000 (và cổng etl nếu có), **stop** container infra; volume nguyên vẹn |
| AC3 | `pnpm docker-up`: tất cả trong container (infra + `api`+`etl` build từ image); `curl localhost:8000/api/healthz` → `200` |
| AC4 | `pnpm docker-down`: gỡ container; volume `dlck-infra_pgdata` **và** `dlck-infra_redisdata` còn nguyên — script **`die` nếu volume biến mất** |
| AC5 | `pnpm docker-clean`: prune build cache + image mồ côi; **từ chối prune volume vô danh khi Docker Engine < 23**; xác nhận volume dữ liệu sống sót |
| AC6 | Thiếu `.env` → tự copy từ `.env.example`; thiếu biến bắt buộc (`POSTGRES_PASSWORD`) → compose **fail-fast** với thông báo rõ |
| AC7 | Cổng Postgres/Redis bind **`127.0.0.1`** (không `0.0.0.0`) — không lộ ra ngoài |
| AC8 | Trên Windows: dev-start trỏ `POSTGRES_HOST=127.0.0.1` cho app native; dò cổng bận chỉ khớp dòng `LISTENING` |

## 3. Phạm vi

**Trong phạm vi (dựng lần này):**
- Cây `deploy/`: `infra/docker-compose.yml` (postgres + redis), `app/docker-compose.yml` (api + etl), `backend.Dockerfile`.
- Orchestrator `scripts/stack.mjs` + `package.json` gốc (5 lệnh pnpm) + `.env.example`.
- External network dùng chung; named volume; các chốt an toàn dữ liệu.
- **Walking skeleton** để khung chạy được đầu-cuối và nghiệm thu được:
  - `api`: app FastAPI tối thiểu, đúng một route `GET /api/healthz` (ping DB nếu rẻ).
  - `etl`: tiến trình scheduler tối thiểu, in một nhịp rồi ngủ — chứng minh tiến trình chạy.

**Ngoài phạm vi (plan sau, dựng *trên* khung này):**
- Logic ETL thật (bảng tham chiếu, giá EOD, screener…) — plan `first-rest-slice`.
- Crawl OMO — cùng nhóm REST-first.
- ClickHouse + `ingester` realtime — **chặn bởi phiên thiết kế lại `market-data-store.md` theo ClickHouse** ([roadmap §5.2](../../../00-overview/roadmap.md)); thêm vào `infra`/`app` compose dưới profile `realtime` khi tới.
- `frontend` (Next.js) + `nginx` (HTTP/2 cho SSE) — profile `web`, thêm khi dựng FE/SSE.

Nguyên tắc "khung đủ chỗ, thêm dần": hạ tầng chung (network, env, image nền, hai chế độ) thiết kế cho **cả** 8 service; service chưa dựng để **profile**, mặc định không chạy.

## 4. Cây file tạo ra

```
deploy/
├── infra/docker-compose.yml     postgres (pgvector) · redis
├── app/docker-compose.yml       api · etl   (một image, hai command)
└── backend.Dockerfile           python:3.12-slim + uv, non-root
scripts/stack.mjs                 orchestrator Node (cross-platform)
package.json                      gốc — 5 script pnpm trỏ stack.mjs
.env.example                      commit, toàn giá trị change-me
backend/
├── pyproject.toml · uv.lock      deps Python (uv)
├── .dockerignore
├── app/main.py                   FastAPI walking skeleton (/api/healthz)
├── etl/__main__.py               scheduler walking skeleton (một nhịp)
└── core/                         (khung thư viện lõi — điền dần ở plan sau)
```

`frontend.Dockerfile`, `deploy/nginx/default.conf`, các service `clickhouse`/`ingester`/`frontend`/`nginx` **chưa tạo** lần này.

## 5. Từng thành phần

### 5.1 `deploy/infra/docker-compose.yml`

Project `dlck-infra`, network `dlck-net` (external). Học đúng conventions tutor-agent:

- **postgres**: image `pgvector/pgvector:pg16` *(cần pgvector cho tin — news-pipeline)*; `restart: unless-stopped`; env `POSTGRES_DB/USER` có default, `POSTGRES_PASSWORD:?` **bắt buộc**; port `127.0.0.1:5432:5432`; volume có tên `pgdata`; healthcheck `pg_isready`.
- **redis**: image `redis:7-alpine`; port `127.0.0.1:6379:6379`; volume có tên `redisdata` *(AOF để không mất leader-lock/state khi restart — cân nhắc, mặc định bật `--appendonly yes`)*; healthcheck `redis-cli ping`.

> Redis ở đây **dùng thật** (pub/sub fan-out, leader lock cho ingester, token bucket rate limit — service-topology §5), khác tutor-agent để `memory://`.

### 5.2 `deploy/app/docker-compose.yml`

Project `dlck-app`, cùng network external `dlck-net`. **Một image backend, nhiều command** (đúng pattern `backend` + `celery-worker` của tutor-agent):

- **api**: build từ `backend.Dockerfile`; command uvicorn; `env_file: ../../.env`; (chế độ docker-up) publish `8000` — *tạm thời*, tới khi có nginx thì chuyển cổng công khai về nginx.
- **etl**: cùng image; command chạy scheduler; `env_file`; không cổng.
- `clickhouse`/`ingester`/`frontend`/`nginx`: **để dành**, khai dưới profile khi tới.

### 5.3 `deploy/backend.Dockerfile`

`python:3.12-slim` + **uv** (`COPY --from=ghcr.io/astral-sh/uv`), `uv sync --frozen --no-dev`, `UV_COMPILE_BYTECODE=1`, `PYTHONUNBUFFERED=1`, user non-root. Một image phục vụ cả `api`, `etl`, (sau này) `ingester` — khác nhau ở `command` trong compose. Không migrate ở đây (dùng migration riêng — quyết ở plan DB, chưa chốt Alembic vs SQL thuần).

### 5.4 `scripts/stack.mjs` (orchestrator)

Bê nguyên khung tutor-agent, chỉnh cho stack ta. Hằng số: `INFRA`/`APP` compose args, `NETWORK=dlck-net`.

| Lệnh | Hành vi |
|---|---|
| `dev-start` | `ensureEnv` → dò cổng 8000 bận thì báo → `infraUp` (docker `--wait` healthy) → **native**: `uv run uvicorn app.main:app --reload --port 8000` (env `POSTGRES_HOST=127.0.0.1`, `REDIS_HOST=127.0.0.1`, settings dev) + `uv run python -m etl`; in nhãn màu `[api]`/`[etl]`; Ctrl+C tắt hai tiến trình, **giữ infra** |
| `dev-stop` | `killPort(8000)` (+ cổng etl nếu có) → `compose infra stop` (giữ container + volume) |
| `docker-up` | `ensureEnv` → `infraUp` → `compose app up -d --build` → in URL |
| `docker-down` | Ghi volume trước → `compose app down` → `compose infra down` (**giữ volume**) → **kiểm `pgdata`+`redisdata` còn sống, mất là `die`** |
| `docker-clean` | `builder/image prune` → **kiểm phiên bản Docker: <23 thì bỏ qua `volume prune`** → xác nhận volume dữ liệu sống sót |

Đúng-Windows (đã trả giá ở tutor-agent, bê nguyên): `shell:true` trên win32; `POSTGRES_HOST=127.0.0.1` (không "postgres", không "localhost" vì ::1 làm chờ ~10s); parse `netstat -ano` chỉ `LISTENING` (tránh false-positive TIME_WAIT); `taskkill /T /F`.

### 5.5 `package.json` gốc + `.env.example`

- `package.json`: `private: true`, 5 script `dev-start`/`dev-stop`/`docker-up`/`docker-down`/`docker-clean` → `node scripts/stack.mjs <lệnh>`.
- `.env.example` (commit, toàn `change-me`): khối Postgres (`POSTGRES_DB/USER/PASSWORD/HOST/PORT`), khối Redis (`REDIS_HOST/PORT`), khối app (`APP_ENV`, `LOG_LEVEL`…). Biến bắt buộc không có default để compose fail-fast.

## 6. Luồng dev vs deploy

```
dev-start:   [docker] postgres+redis  +  [native] uvicorn --reload  +  [native] etl
             Ctrl+C → tắt native, giữ docker infra

docker-up:   [docker] postgres+redis+api+etl  (một máy, một lệnh)
```

Khác biệt hai chế độ nằm ở **stack.mjs**, không phải ở file compose override — infra compose dùng chung, app compose chỉ dùng ở docker-up. (Không theo pattern `docker-compose.override.yml` vì dev không chạy app trong docker.)

## 7. An toàn dữ liệu (chốt bắt buộc — viên ngọc của tutor-agent)

1. Named volume cho mọi kho; **không bao giờ bind-mount thư mục data DB** (lỗi quyền + chậm trên Windows).
2. `docker-down`/`docker-clean` **kiểm volume dữ liệu còn sống trước và sau**, biến mất là `die` ngay.
3. `docker-clean` **không prune volume vô danh** khi Docker Engine < 23 (bản đó có thể xoá nhầm volume có tên).
4. Cổng DB bind `127.0.0.1`; biến bí mật bắt buộc fail-fast.
5. Ghi vào runbook (`docs/40-operations/` khi lập): **cấm bấm "Reset to factory defaults"** của Docker Desktop — xoá volume dữ liệu.

## 8. Rủi ro / điều chưa chốt

- **Migration DB**: Alembic vs SQL DDL thuần trong `database/` — **chưa chốt**, quyết ở plan lát cắt REST (không chặn khung này; walking skeleton chưa cần bảng).
- **Slug tên** `dlck` (network/project/volume) — đề xuất, đổi được trước khi chạy lần đầu.
- **Redis AOF**: bật `--appendonly yes` để giữ state qua restart — xác nhận khi dựng ingester (state realtime); walking skeleton chưa phụ thuộc.
- **Node/pnpm ở gốc**: chấp nhận có chủ đích (FE là Next.js nên dù sao cũng cần) — đổi lấy orchestrator cross-platform.

## 9. Việc kế tiếp (decompose)

Khung này xong thì các plan sau dựng *bên trong* nó, theo trình tự REST-first đã chốt:
1. `first-rest-slice` — ETL bảng tham chiếu + OMO crawl → Postgres (thêm migration, điền `core/` + `etl/`).
2. ETL hằng ngày (giá EOD, snapshot, screener, sự kiện).
3. Phiên thiết kế lại ClickHouse → rồi `ingester` + profile `realtime`.
4. `frontend` + `nginx` + profile `web`.
