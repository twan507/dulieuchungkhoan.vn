# Deploy scaffold — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: dùng `superpowers:subagent-driven-development` (khuyến nghị) hoặc `superpowers:executing-plans` để thực thi từng task. Steps dùng checkbox (`- [ ]`).

**Goal:** Dựng khung đóng gói một-nút (`pnpm dev-start` / `docker-up` / `docker-down` / `docker-clean`) cho monorepo, với walking-skeleton `api`+`etl` để nghiệm thu được đầu-cuối.

**Architecture:** Compose tách **infra** (postgres+redis, `-p dlck-infra`) và **app** (api+etl, `-p dlck-app`), nối bằng external network `dlck-net`. Orchestrator Node `scripts/stack.mjs` chạy hai chế độ: dev = infra docker + app native (uvicorn `--reload`); deploy = tất cả docker. An toàn dữ liệu: named volume, kiểm bất biến volume, guard prune theo phiên bản Docker.

**Tech Stack:** Python 3.12 + uv + FastAPI (backend) · Node ≥18 (orchestrator, dùng `node:test`) · pnpm (nút lệnh) · Docker Compose v2 · Postgres (pgvector) · Redis.

**Spec:** [spec.md](spec.md) — đọc kèm; plan này lập luận từ spec.

## Global Constraints

- **Nhánh:** thực thi trên `feat/deploy-scaffold`, **không commit thẳng `main`** *(CLAUDE.md §4.7)*. Conventional Commits, commit theo mốc.
- **Slug:** `dlck` cho network/project/volume → `dlck-net`, project `dlck-infra`/`dlck-app`, volume `dlck-infra_pgdata`/`dlck-infra_redisdata`.
- **An toàn dữ liệu:** không bind-mount data DB (chỉ named volume) · cổng DB bind `127.0.0.1` · biến bắt buộc fail-fast · không cờ `-v`/`--volumes` trong lệnh docker.
- **Test:** đỏ trước xanh; expected từ nguồn độc lập (không tautological); assert giá trị cụ thể + case biên. Không gọi nguồn ngoài trong test *(test-strategy §1)*. Seam đã chốt ở [spec §8](spec.md); plan này không thêm seam ngoài đó.
- **Đúng-Windows:** `shell:true` khi spawn trên win32 · native dev dùng `POSTGRES_HOST=127.0.0.1` (không "postgres", không "localhost") · parse `netstat -ano` chỉ dòng `LISTENING`.

**Cây file tạo ra:**

```
.gitignore                          (tạo/commit — che .env, .venv, node_modules)
.env.example
package.json                        (gốc — 5 script pnpm)
scripts/stack.mjs                   (orchestrator: helper thuần export + command)
scripts/stack.test.mjs              (node:test cho 3 seam)
deploy/infra/docker-compose.yml     postgres + redis
deploy/app/docker-compose.yml       api + etl
deploy/backend.Dockerfile           một image
backend/pyproject.toml
backend/.dockerignore
backend/core/__init__.py            (rỗng — điền ở plan sau)
backend/app/__init__.py
backend/app/main.py                 FastAPI /api/healthz
backend/etl/__init__.py
backend/etl/heartbeat.py            hàm thuần
backend/etl/__main__.py             vòng lặp scheduler
backend/tests/test_healthz.py
backend/tests/test_heartbeat.py
```

---

## Task 1: Secrets boundary — `.gitignore` + `.env.example`

Chốt ranh giới bí mật **trước** khi tạo bất kỳ file `.env` nào. *(Cũng đóng luôn việc roadmap §5.2: ".gitignore chưa bao giờ được commit".)*

**Files:**
- Create/commit: `.gitignore`
- Create: `.env.example`

- [ ] **Step 1: Viết `.gitignore`**

```
# Secrets
.env
.env.*
!.env.example

# Python
.venv/
__pycache__/
*.pyc

# Node
node_modules/
.pnpm-store/
```

- [ ] **Step 2: Viết `.env.example`** (toàn `change-me`, biến bắt buộc không default)

```
# Postgres
POSTGRES_DB=dulieu
POSTGRES_USER=dulieu
POSTGRES_PASSWORD=change-me-in-production
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432

# Redis
REDIS_HOST=127.0.0.1
REDIS_PORT=6379

# App
APP_ENV=dev
LOG_LEVEL=info
```

- [ ] **Step 3: Verify `.env` bị ignore**

Run: `printf 'X=1\n' > .env && git check-ignore .env && rm .env`
Expected: in ra `.env` (tức đã ignore).

- [ ] **Step 4: Commit**

```bash
git add .gitignore .env.example
git commit -m "chore: add gitignore secrets boundary and env example"
```

---

## Task 2: Backend Python project skeleton

**Files:**
- Create: `backend/pyproject.toml`, `backend/.dockerignore`, `backend/core/__init__.py`, `backend/app/__init__.py`, `backend/etl/__init__.py`

**Interfaces:**
- Produces: chạy được `uv run pytest` và `uv run uvicorn app.main:app` từ thư mục `backend/`.

- [ ] **Step 1: Viết `backend/pyproject.toml`**

```toml
[project]
name = "dulieuchungkhoan-backend"
version = "0.0.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.30",
]

[dependency-groups]
dev = [
    "pytest>=8",
    "httpx>=0.27",
]

[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
```

- [ ] **Step 2: Viết `backend/.dockerignore`**

```
.venv/
__pycache__/
*.pyc
tests/
.pytest_cache/
```

- [ ] **Step 3: Tạo package rỗng**

```bash
mkdir -p backend/core backend/app backend/etl backend/tests
: > backend/core/__init__.py
: > backend/app/__init__.py
: > backend/etl/__init__.py
```

- [ ] **Step 4: Sinh lockfile + verify**

Run: `cd backend && uv sync`
Expected: tạo `backend/.venv` + `backend/uv.lock`, exit 0.
Run: `cd backend && uv run python -c "import fastapi, uvicorn; print('ok')"`
Expected: in `ok`.

- [ ] **Step 5: Commit**

```bash
git add backend/pyproject.toml backend/uv.lock backend/.dockerignore backend/core backend/app backend/etl
git commit -m "chore: scaffold backend python project with uv"
```

---

## Task 3: api walking skeleton (TDD — seam §8c)

**Files:**
- Create: `backend/app/main.py`
- Test: `backend/tests/test_healthz.py`

**Interfaces:**
- Produces: FastAPI `app` với `GET /api/healthz` → `{"status": "ok", "service": "api"}`.

- [ ] **Step 1: Viết test đỏ** — `backend/tests/test_healthz.py`

```python
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_healthz_returns_ok_payload():
    resp = client.get("/api/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "service": "api"}
```

- [ ] **Step 2: Chạy test — kỳ vọng đỏ**

Run: `cd backend && uv run pytest tests/test_healthz.py -v`
Expected: FAIL — `ModuleNotFoundError: app.main` (chưa có `main.py`).

- [ ] **Step 3: Viết implementation tối thiểu** — `backend/app/main.py`

```python
from fastapi import FastAPI

app = FastAPI(title="dulieuchungkhoan.vn api")


@app.get("/api/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok", "service": "api"}
```

- [ ] **Step 4: Chạy test — kỳ vọng xanh**

Run: `cd backend && uv run pytest tests/test_healthz.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/main.py backend/tests/test_healthz.py
git commit -m "feat: add api healthz endpoint"
```

---

## Task 4: etl walking skeleton (TDD tick)

Tách phần **thuần** (`heartbeat`) ra khỏi vòng lặp để test được; `__main__` chỉ là vòng lặp gọi nó.

**Files:**
- Create: `backend/etl/heartbeat.py`, `backend/etl/__main__.py`
- Test: `backend/tests/test_heartbeat.py`

**Interfaces:**
- Produces: `heartbeat(now: datetime) -> str`; `python -m etl` in một dòng heartbeat mỗi 15 s.

- [ ] **Step 1: Viết test đỏ** — `backend/tests/test_heartbeat.py`

```python
from datetime import datetime, timezone

from etl.heartbeat import heartbeat


def test_heartbeat_formats_utc_iso():
    now = datetime(2026, 8, 24, 3, 0, 0, tzinfo=timezone.utc)
    assert heartbeat(now) == "[etl] alive at 2026-08-24T03:00:00+00:00"
```

- [ ] **Step 2: Chạy test — kỳ vọng đỏ**

Run: `cd backend && uv run pytest tests/test_heartbeat.py -v`
Expected: FAIL — `ModuleNotFoundError: etl.heartbeat`.

- [ ] **Step 3: Viết `backend/etl/heartbeat.py`**

```python
from datetime import datetime, timezone


def heartbeat(now: datetime) -> str:
    return f"[etl] alive at {now.astimezone(timezone.utc).isoformat()}"
```

- [ ] **Step 4: Chạy test — kỳ vọng xanh**

Run: `cd backend && uv run pytest tests/test_heartbeat.py -v`
Expected: PASS.

- [ ] **Step 5: Viết `backend/etl/__main__.py`** (không unit-test — vòng lặp, smoke ở Task 9)

```python
import time
from datetime import datetime, timezone

from etl.heartbeat import heartbeat


def main() -> None:
    while True:
        print(heartbeat(datetime.now(timezone.utc)), flush=True)
        time.sleep(15)


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Verify chạy một nhịp**

Run: `cd backend && timeout 2 uv run python -m etl || true`
Expected: in ít nhất một dòng `[etl] alive at ...`.

- [ ] **Step 7: Commit**

```bash
git add backend/etl/heartbeat.py backend/etl/__main__.py backend/tests/test_heartbeat.py
git commit -m "feat: add etl heartbeat walking skeleton"
```

---

## Task 5: Infra compose (postgres + redis)

**Files:**
- Create: `deploy/infra/docker-compose.yml`

- [ ] **Step 1: Viết `deploy/infra/docker-compose.yml`**

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg16
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-dulieu}
      POSTGRES_USER: ${POSTGRES_USER:-dulieu}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?POSTGRES_PASSWORD phải đặt trong .env}
    ports:
      - "127.0.0.1:5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-dulieu} -d ${POSTGRES_DB:-dulieu}"]
      interval: 5s
      timeout: 3s
      retries: 10
    networks:
      - dlck-net

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: ["redis-server", "--appendonly", "yes"]
    ports:
      - "127.0.0.1:6379:6379"
    volumes:
      - redisdata:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 10
    networks:
      - dlck-net

volumes:
  pgdata:
  redisdata:

networks:
  dlck-net:
    external: true
```

- [ ] **Step 2: Verify cú pháp + fail-fast**

Run: `docker network create dlck-net 2>/dev/null; POSTGRES_PASSWORD=x docker compose -p dlck-infra -f deploy/infra/docker-compose.yml config -q`
Expected: exit 0 (cú pháp hợp lệ).
Run: `docker compose -p dlck-infra -f deploy/infra/docker-compose.yml config -q` *(không có POSTGRES_PASSWORD)*
Expected: lỗi có chuỗi "POSTGRES_PASSWORD phải đặt trong .env".

- [ ] **Step 3: Commit**

```bash
git add deploy/infra/docker-compose.yml
git commit -m "feat: add infra compose (postgres, redis)"
```

---

## Task 6: Backend image + app compose

**Files:**
- Create: `deploy/backend.Dockerfile`, `deploy/app/docker-compose.yml`

**Interfaces:**
- Consumes: `backend/` (pyproject, app, etl từ Task 2–4).
- Produces: image chạy `uvicorn app.main:app` (api) và `python -m etl` (etl).

- [ ] **Step 1: Viết `deploy/backend.Dockerfile`**

```dockerfile
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.9.18 /uv /uvx /bin/
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PYTHONUNBUFFERED=1
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY . .
ENV PATH="/app/.venv/bin:$PATH"
RUN useradd -m appuser && chown -R appuser /app
USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: Viết `deploy/app/docker-compose.yml`**

```yaml
services:
  api:
    build:
      context: ../../backend
      dockerfile: ../deploy/backend.Dockerfile
    restart: unless-stopped
    env_file: ../../.env
    environment:
      POSTGRES_HOST: postgres
      REDIS_HOST: redis
    ports:
      - "8000:8000"
    networks:
      - dlck-net

  etl:
    build:
      context: ../../backend
      dockerfile: ../deploy/backend.Dockerfile
    restart: unless-stopped
    command: ["python", "-m", "etl"]
    env_file: ../../.env
    environment:
      POSTGRES_HOST: postgres
      REDIS_HOST: redis
    networks:
      - dlck-net

networks:
  dlck-net:
    external: true
```

> Trong docker-up, `api`/`etl` nối tới service `postgres`/`redis` (env override tại đây); trong dev-start native, `stack.mjs` đặt `POSTGRES_HOST=127.0.0.1`.

- [ ] **Step 3: Verify build + cú pháp**

Run: `docker build -f deploy/backend.Dockerfile -t dlck-backend-test backend`
Expected: build thành công.
Run: `docker compose -p dlck-app -f deploy/app/docker-compose.yml config -q` *(cần `.env` — tạo tạm từ example nếu chưa có)*
Expected: exit 0.

- [ ] **Step 4: Commit**

```bash
git add deploy/backend.Dockerfile deploy/app/docker-compose.yml
git commit -m "feat: add backend image and app compose"
```

---

## Task 7: `stack.mjs` helper thuần (TDD — 3 seam §8b)

Chỉ viết **các hàm thuần export** + test. Phần command (spawn) ở Task 8. Đây là seam đã chốt ở spec §8b — expected là literal độc lập, không tính lại theo cách hàm parse.

**Files:**
- Create: `scripts/stack.mjs` (chỉ phần export helper ở task này)
- Test: `scripts/stack.test.mjs`

**Interfaces:**
- Produces: `listeningPids(netstatOutput, port)`, `dockerMajor(versionOutput)`, `shouldPruneAnonVolumes(major)`, `assertVolumeSurvived(before, after, name)`.

- [ ] **Step 1: Viết test đỏ** — `scripts/stack.test.mjs`

```javascript
import { test } from "node:test";
import assert from "node:assert/strict";

import {
  listeningPids,
  dockerMajor,
  shouldPruneAnonVolumes,
  assertVolumeSurvived,
} from "./stack.mjs";

test("listeningPids: chỉ PID của dòng LISTENING đúng cổng, bỏ TIME_WAIT", () => {
  const out = [
    "  TCP    127.0.0.1:8000    0.0.0.0:0      LISTENING    1234",
    "  TCP    127.0.0.1:8000    10.0.0.2:55    TIME_WAIT    9999",
    "  TCP    127.0.0.1:3000    0.0.0.0:0      LISTENING    5678",
  ].join("\r\n");
  assert.deepEqual(listeningPids(out, 8000), ["1234"]);
  assert.deepEqual(listeningPids(out, 3000), ["5678"]);
  assert.deepEqual(listeningPids(out, 9999), []);
});

test("dockerMajor: lấy major, null nếu không parse được", () => {
  assert.equal(dockerMajor("27.1.1"), 27);
  assert.equal(dockerMajor("20.10.9"), 20);
  assert.equal(dockerMajor("garbage"), null);
});

test("shouldPruneAnonVolumes: chỉ true khi >= 23", () => {
  assert.equal(shouldPruneAnonVolumes(20), false);
  assert.equal(shouldPruneAnonVolumes(23), true);
  assert.equal(shouldPruneAnonVolumes(24), true);
  assert.equal(shouldPruneAnonVolumes(null), false);
});

test("assertVolumeSurvived: die khi volume có trước mà mất sau", () => {
  assert.equal(assertVolumeSurvived(["dlck-infra_pgdata"], [], "dlck-infra_pgdata").ok, false);
  assert.equal(assertVolumeSurvived(["dlck-infra_pgdata"], ["dlck-infra_pgdata"], "dlck-infra_pgdata").ok, true);
  assert.equal(assertVolumeSurvived([], [], "dlck-infra_pgdata").ok, true);
});
```

- [ ] **Step 2: Chạy test — kỳ vọng đỏ**

Run: `node --test scripts/stack.test.mjs`
Expected: FAIL — không import được từ `./stack.mjs` (chưa có file/hàm).

- [ ] **Step 3: Viết helper thuần** — `scripts/stack.mjs` (mới, chỉ phần này)

```javascript
export function listeningPids(netstatOutput, port) {
  const pids = new Set();
  for (const line of netstatOutput.split(/\r?\n/)) {
    const m = line.match(/^\s*TCP\s+(\S+)\s+\S+\s+LISTENING\s+(\d+)\s*$/i);
    if (m && m[1].endsWith(`:${port}`)) pids.add(m[2]);
  }
  return [...pids];
}

export function dockerMajor(versionOutput) {
  const m = String(versionOutput).match(/^(\d+)\./);
  return m ? parseInt(m[1], 10) : null;
}

export function shouldPruneAnonVolumes(major) {
  return major !== null && major >= 23;
}

export function assertVolumeSurvived(before, after, name) {
  const had = before.includes(name);
  const has = after.includes(name);
  if (had && !has) return { ok: false, reason: `volume ${name} biến mất` };
  return { ok: true, existed: had };
}
```

- [ ] **Step 4: Chạy test — kỳ vọng xanh**

Run: `node --test scripts/stack.test.mjs`
Expected: PASS (4 test).

- [ ] **Step 5: Commit**

```bash
git add scripts/stack.mjs scripts/stack.test.mjs
git commit -m "feat: add stack.mjs pure helpers with tests"
```

---

## Task 8: `stack.mjs` command + `package.json` gốc

Nối helper Task 7 với spawn để thành 5 lệnh. Không unit-test (side-effect) — smoke ở Task 9.

**Files:**
- Modify: `scripts/stack.mjs` (thêm phần command, giữ nguyên helper)
- Create: `package.json` (gốc)

**Interfaces:**
- Consumes: `listeningPids`, `dockerMajor`, `shouldPruneAnonVolumes`, `assertVolumeSurvived` (Task 7).

- [ ] **Step 1: Thêm phần command vào `scripts/stack.mjs`** (append DƯỚI các export helper)

```javascript
import { spawn, spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const ENV_FILE = path.join(ROOT, ".env");
const INFRA = ["-p", "dlck-infra", "-f", "deploy/infra/docker-compose.yml", "--env-file", ".env"];
const APP = ["-p", "dlck-app", "-f", "deploy/app/docker-compose.yml", "--env-file", ".env"];
const NETWORK = "dlck-net";
const WIN = process.platform === "win32";

function log(m) { console.log(`[stack] ${m}`); }
function die(m) { console.error(`[stack] ${m}`); process.exit(1); }
function run(cmd, args, opts = {}) {
  const r = spawnSync(cmd, args, { cwd: ROOT, stdio: "inherit", shell: WIN, ...opts });
  if (r.status !== 0 && !opts.allowFail) die(`lệnh thất bại: ${cmd} ${args.join(" ")}`);
  return r.status;
}
function capture(cmd, args) {
  const r = spawnSync(cmd, args, { cwd: ROOT, encoding: "utf8", shell: WIN });
  return (r.stdout || "").trim();
}
function volumes() { return capture("docker", ["volume", "ls", "--format", "{{.Name}}"]).split(/\r?\n/); }

function ensureEnv() {
  if (fs.existsSync(ENV_FILE)) return;
  const ex = path.join(ROOT, ".env.example");
  if (!fs.existsSync(ex)) die(".env và .env.example đều không tồn tại");
  fs.copyFileSync(ex, ENV_FILE);
  log("đã tạo .env từ .env.example — nhớ điền giá trị thật");
}
function ensureNetwork() {
  if (!capture("docker", ["network", "ls", "--format", "{{.Name}}"]).split(/\r?\n/).includes(NETWORK))
    run("docker", ["network", "create", NETWORK]);
}
function infraUp() {
  ensureNetwork();
  log("bật Postgres + Redis, chờ healthy…");
  run("docker", ["compose", ...INFRA, "up", "-d", "--wait"]);
}
function pidsOnPort(port) {
  if (WIN) return listeningPids(capture("netstat", ["-ano"]), port);
  return capture("lsof", ["-ti", `tcp:${port}`, "-sTCP:LISTEN"]).split(/\r?\n/).map(s => s.trim()).filter(Boolean);
}
function killPort(port) {
  for (const pid of pidsOnPort(port)) {
    log(`giết PID ${pid} ở cổng ${port}`);
    if (WIN) run("taskkill", ["/PID", pid, "/T", "/F"], { allowFail: true });
    else run("kill", ["-9", pid], { allowFail: true });
  }
}

const children = [];
function spawnLabeled(label, cmd, args, cwd, env) {
  const p = spawn(cmd, args, { cwd, env, shell: WIN });
  const pipe = (s) => s.on("data", (d) => d.toString().split(/\r?\n/).filter(Boolean).forEach(l => console.log(`[${label}] ${l}`)));
  pipe(p.stdout); pipe(p.stderr);
  children.push(p);
}
function killChildren() {
  for (const p of children) {
    if (p.exitCode !== null) continue;
    if (WIN) spawnSync("taskkill", ["/pid", String(p.pid), "/T", "/F"], { stdio: "ignore" });
    else p.kill("SIGTERM");
  }
}

function devStart() {
  ensureEnv();
  if (pidsOnPort(8000).length) die("cổng 8000 đang bận — tắt tiến trình chiếm rồi chạy lại");
  infraUp();
  const env = { ...process.env, POSTGRES_HOST: "127.0.0.1", REDIS_HOST: "127.0.0.1", APP_ENV: "dev" };
  const be = path.join(ROOT, "backend");
  log("bật api :8000 (uvicorn --reload) và etl — Ctrl+C để tắt cả hai (Postgres+Redis vẫn chạy)");
  spawnLabeled("api", "uv", ["run", "uvicorn", "app.main:app", "--reload", "--port", "8000"], be, env);
  spawnLabeled("etl", "uv", ["run", "python", "-m", "etl"], be, env);
  let closing = false;
  process.on("SIGINT", () => {
    if (closing) return; closing = true;
    console.log(""); log("đang tắt api + etl… (dùng dev-stop để tắt hẳn infra)");
    killChildren(); setTimeout(() => process.exit(0), 800);
  });
}
function devStop() {
  ensureEnv();
  killPort(8000);
  log("dừng container infra (giữ container + volume)…");
  run("docker", ["compose", ...INFRA, "stop"], { allowFail: true });
}
function dockerUp() {
  ensureEnv(); infraUp();
  log("build + chạy tầng app…");
  run("docker", ["compose", ...APP, "up", "-d", "--build"]);
  log("xong — API: http://localhost:8000/api/healthz");
}
function dockerDown() {
  ensureEnv();
  const before = volumes();
  run("docker", ["compose", ...APP, "down"], { allowFail: true });
  run("docker", ["compose", ...INFRA, "down"], { allowFail: true });
  for (const name of ["dlck-infra_pgdata", "dlck-infra_redisdata"]) {
    const r = assertVolumeSurvived(before, volumes(), name);
    if (!r.ok) die(`CẢNH BÁO: ${r.reason} — kiểm tra ngay`);
  }
  log("đã gỡ container. Volume dữ liệu còn nguyên.");
}
function dockerClean() {
  const before = volumes();
  run("docker", ["system", "df"]);
  run("docker", ["builder", "prune", "-f"], { allowFail: true });
  run("docker", ["image", "prune", "-f"], { allowFail: true });
  const major = dockerMajor(capture("docker", ["version", "--format", "{{.Server.Version}}"]));
  if (shouldPruneAnonVolumes(major)) run("docker", ["volume", "prune", "-f"], { allowFail: true });
  else log(`Docker Engine ${major ?? "?"}: bỏ qua prune volume vô danh cho an toàn`);
  for (const name of ["dlck-infra_pgdata", "dlck-infra_redisdata"]) {
    const r = assertVolumeSurvived(before, volumes(), name);
    if (!r.ok) die(`CẢNH BÁO: ${r.reason} sau khi dọn — KHÔNG được phép`);
  }
  run("docker", ["system", "df"]);
  log("volume dữ liệu: còn nguyên ✓");
}

const COMMANDS = { "dev-start": devStart, "dev-stop": devStop, "docker-up": dockerUp, "docker-down": dockerDown, "docker-clean": dockerClean };
const cmd = process.argv[2];
if (COMMANDS[cmd]) COMMANDS[cmd]();
else if (cmd === undefined) { /* import cho test — không chạy command */ }
else { console.log(`Lệnh: ${Object.keys(COMMANDS).join(", ")}`); process.exit(1); }
```

> ⚠️ Dòng cuối phân biệt "chạy CLI" với "import để test": khi `stack.test.mjs` import, `process.argv[2]` là `undefined` nên **không** kích hoạt command nào.

- [ ] **Step 2: Chạy lại test helper — vẫn xanh (không hồi quy)**

Run: `node --test scripts/stack.test.mjs`
Expected: PASS (import không kích hoạt command).

- [ ] **Step 3: Viết `package.json` gốc**

```json
{
  "name": "dulieuchungkhoan-vn",
  "private": true,
  "scripts": {
    "dev-start": "node scripts/stack.mjs dev-start",
    "dev-stop": "node scripts/stack.mjs dev-stop",
    "docker-up": "node scripts/stack.mjs docker-up",
    "docker-down": "node scripts/stack.mjs docker-down",
    "docker-clean": "node scripts/stack.mjs docker-clean"
  }
}
```

- [ ] **Step 4: Commit**

```bash
git add scripts/stack.mjs package.json
git commit -m "feat: add stack.mjs commands and root pnpm scripts"
```

---

## Task 9: Nghiệm thu đầu-cuối (verify AC1–AC8)

Không code — chạy thật, **dán output** *(§4.1.6)*. Cần Docker Desktop chạy. Điền `POSTGRES_PASSWORD` thật vào `.env` trước.

- [ ] **AC6** `.env`/fail-fast: xoá `.env`, chạy `pnpm dev-start` → tự tạo `.env`; bỏ `POSTGRES_PASSWORD` → thấy lỗi "POSTGRES_PASSWORD phải đặt trong .env".
- [ ] **AC1** `pnpm dev-start`: infra healthy; `curl -s localhost:8000/api/healthz` → `{"status":"ok","service":"api"}`; log có `[etl] alive at`; Ctrl+C → api+etl tắt, `docker ps` còn postgres+redis.
- [ ] **AC2** `pnpm dev-stop`: `netstat`/`lsof` cổng 8000 trống; `docker ps` không còn infra chạy; `docker volume ls` còn `dlck-infra_pgdata`+`dlck-infra_redisdata`.
- [ ] **AC3** `pnpm docker-up`: `docker ps` có postgres+redis+api+etl; `curl -s localhost:8000/api/healthz` → 200.
- [ ] **AC4** `pnpm docker-down`: `docker ps` sạch; hai volume dữ liệu còn; (thử xoá tay một volume rồi chạy lại để xác nhận `die`).
- [ ] **AC5** `pnpm docker-clean`: in `system df` trước/sau; máy Docker ≥23 thì prune volume vô danh, <23 thì bỏ qua; hai volume dữ liệu còn.
- [ ] **AC7** `docker inspect` cổng: 5432/6379 bind `127.0.0.1`.
- [ ] **AC8** (Windows) dev-start dùng `POSTGRES_HOST=127.0.0.1`; dò cổng bận đúng (không dính TIME_WAIT — đã có unit test Task 7).
- [ ] **Commit mốc cuối** (nếu có chỉnh sửa nhỏ khi nghiệm thu):

```bash
git commit -am "test: verify deploy scaffold acceptance criteria" --allow-empty
```

---

## Self-review (đã chạy khi viết plan)

- **Spec coverage:** §2 AC1–8 → Task 9; §4 cây file → Task 1–8; §5.1 infra → Task 5; §5.2 app → Task 6; §5.3 Dockerfile → Task 6; §5.4 stack.mjs → Task 7+8; §5.5 package/.env → Task 8+1; §7 an toàn dữ liệu → Task 5 (127.0.0.1, named volume) + Task 8 (kiểm bất biến, guard prune); §8 seam → Task 3/4/7. Không thấy khoảng trống.
- **Placeholder:** không có TODO/"tương tự Task N"/"xử lý lỗi phù hợp" — mọi step có nội dung thật.
- **Type/tên nhất quán:** `listeningPids`/`dockerMajor`/`shouldPruneAnonVolumes`/`assertVolumeSurvived` khai ở Task 7, dùng đúng tên ở Task 8; `heartbeat`/`app` khớp giữa test và impl; volume `dlck-infra_pgdata`/`dlck-infra_redisdata` đồng nhất mọi nơi.
