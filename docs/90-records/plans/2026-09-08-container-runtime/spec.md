# Spec — lát 12: chạy được trong container (một `.env` nguyên tố · một compose gốc · một lệnh lên)

**Ngày:** 2026-09-08 · **Trạng thái:** ✅ **DUYỆT 2026-09-08** — chủ dự án: *"tất cả cứ như bạn đề xuất"* (cả năm điểm §9) · **Nhánh:** `feat/container-runtime`
**Điểm vào:** [roadmap §3 "Điểm vào cho lát 12"](../../../00-overview/roadmap.md) (đọc §0 ở đó trước — bảy quyết định 2026-09-08 và dữ kiện code) · **Hồ sơ tiền nhiệm:** [`2026-09-07-audit-drift-cleanup/`](../2026-09-07-audit-drift-cleanup/) (đợt chuẩn hoá 15 họ job, quyết định không gộp `Fetcher`)

---

## 1. Vì sao lát này, và lát này là gì

Chủ dự án nêu nguyên văn: *"chuẩn hoá tất cả tác vụ, thiết kế cho chạy trong Docker để sau này dùng được trên VPS luôn không phải làm lại"* — và bổ sung 2026-09-08: *"tất cả đều chạy bằng docker, đóng gói hoàn chỉnh lên VPS chỉ chạy 1 lệnh docker lên là ok luôn không phải cài đặt gì hết."*

Hôm nay: vỏ Docker có (Dockerfile, hai compose), nhưng **chưa job sản phẩm nào từng chạy bên trong**. Chín biến `.env` trỏ `127.0.0.1`; gốc repo trong image là `/`; `database/` không nằm trong image; ingester thoát ngay khi quá 15:05 nên `restart: unless-stopped` sẽ khởi động lại nó suốt đêm; user login hai kho tạo tay.

**Lát này là gì, một câu:** sau lát này, trên máy mới chỉ cần `git clone` + điền `.env` + `docker compose up -d --build` là kho dựng xong, user cấp xong, và cả 15 họ job lẫn ingester chạy được trong container; trên máy dev, native (`uv run …`) vẫn chạy với **cùng một `.env`**. Chưa có scheduler (lát 13).

## 2. Dữ kiện đã kiểm vs giả định *(§4.8 bước 0)*

### 2.1 Đã kiểm — 2026-09-08, đọc code + grep + lệnh

| Dữ kiện | Nguồn |
|---|---|
| Mọi consumer đọc **URL đầy đủ** qua `os.environ`: `ETL_DATABASE_URL` (10 file `etl/*_job.py` + `agent/db.py`), `AGENT_DATABASE_URL`, `CLICKHOUSE_INGESTER_URL` + `REDIS_URL` (ingester), `CLICKHOUSE_URL` (`ch_migrate`/`ch_backup`), `DATA_DATABASE_URL` (chỉ alembic), `TEST_DATABASE_URL` (chỉ `tests/conftest.py`) | grep `environ` toàn `backend/` ngoài test |
| **Mọi consumer đều gọi `load_dotenv()`** trước khi đọc: 11 job (`*_job.py`, `news_classify.py`), `ingester/config.py`, `agent/__main__.py` | grep `load_dotenv(` |
| `POSTGRES_HOST`/`REDIS_HOST`/`POSTGRES_PORT`/`REDIS_PORT`/`LOG_LEVEL` **không code nào đọc**; `APP_ENV` chỉ `scripts/stack.mjs` | nt · audit D2 |
| `.env` thật có **đúng 9 dòng** `127.0.0.1`/`localhost` (2 host rời + 7 URL) | `grep -c`, không in giá trị |
| `core/env.py`: `REPO_ROOT = parents[2]`; build context `backend/`, `WORKDIR /app` ⇒ trong image `REPO_ROOT = /` ⇒ ingester mặc định `mkdir /dlck-runtime` dưới `appuser` ⇒ exit 2 | `core/env.py` · `deploy/backend.Dockerfile` |
| `database/` và `backend/tests/` **không có trong image** (`backend/.dockerignore` loại `tests/`) | `.dockerignore` · compose `context` |
| Ingester run mode không `--minutes`: `_run_deadline` trả `now` khi đã quá 15:05 ⇒ phiên kết thúc tức thì | `ingester/main.py:302-307` |
| Mỗi lần khởi động run mode: `assert_migrated` → Redis ping → **REST danh mục BVSC** → socket | `ingester/main.py:536-560` |
| `console.py` có 3 chỗ dùng (`etl/__main__`, `ingester/__main__`, `price_job.banner`) + 1 file test `tests/core/test_console.py` | grep |
| Ba chỗ `date.today()` trần: `etl/refdata_job.py:60`, `core/ch_backup.py:39`, `agent/system_prompt.py:53`; còn lại đều `ZoneInfo("Asia/Ho_Chi_Minh")` | grep |
| Role NOLOGIN có sẵn: Postgres `dlck_etl`/`dlck_api` (migration `0009`), ClickHouse `dlck_ingester`/`dlck_api` (`0001_roles.sql`). User login tạo **tay** (`database/README.md` mục Luật, `create_users.sql.example`) | đọc file |
| Bootstrap kho mới có **bước 3 bắt buộc**: `0013` seed lớp 2 phân giải ticker qua `market.security`, rỗng lúc migrate ⇒ 0 dòng không báo; phải `downgrade 0012` → `upgrade head` **sau** `etl refdata`, kiểm đủ **161** | `database/README.md` mục Bootstrap |
| Máy dev: Docker Engine 29.1.3, Compose v2.40.3, uv 0.9.18. Stack đang chạy là project `infra` (volume `infra_*`); còn bộ `dlck-infra_*` rỗng của `stack.mjs`; **`tutor-infra_pgdata` là dự án khác, không đụng** | `docker volume ls` 2026-09-08 |
| Hợp đồng mã thoát 0/1/2 nay có test cho cả 15 họ (`test_e63`), một `GuardRefused` (`test_e65`), `pool_pre_ping` (`test_e64`) | hồ sơ audit 2026-09-08 |

### 2.2 Giả định — CHƯA kiểm, kiểm trong plan trước khi tin

1. `docker compose up -d` **khởi động lại** container one-shot đã thoát 0 ở lần `up` sau (để bootstrap tự chạy lại mỗi lượt). Kiểm: Task đầu của plan, `up` hai lần, đọc `docker compose ps -a`.
2. Volume có tên trên Docker Desktop (WSL2) giữ được **OS file lock** của `spill.py` (`fcntl.flock` trên ext4 trong VM — không phải bind mount NTFS). Kiểm: chạy ingester `--minutes 2` trong container, đọc log `SpillStore`.
3. `ALTER USER … IDENTIFIED WITH sha256_password BY` trên tag ClickHouse `26.3.22.7` đang ghim. Kiểm: test seam trên container CH ephemeral (§6).
4. `prepend_sys_path` của alembic giải theo thư mục làm việc, nên `env.py` import được `core.env` khi chạy từ gốc repo. Kiểm: chạy `alembic … upgrade head` native sau khi sửa `alembic.ini`.

## 3. Phạm vi

### 3.1 Trong phạm vi

1. **Hình dạng cấu hình P2** — `.env` nguyên tố, một hàm ráp trong `core/env.py` (§4.1, §5.1).
2. **Một compose gốc** `docker-compose.yml` + overlay `docker-compose.vps.yml`, thay ba file compose hiện có (§5.2).
3. **Image tự đủ**: context gốc repo, chứa `backend/` + `database/`; `.dockerignore` gốc (§5.3).
4. **`core.bootstrap`**: migrate hai kho + cấp 4 user login từ env + tự seed lớp 2 khi phát hiện thiếu; là lệnh của service one-shot `migrate` (§5.4).
5. **Ingester thành daemon thật**: vòng cửa sổ phiên, ngủ ngoài giờ; service `ingester` + profile `measure`; ba volume runtime (§5.5).
6. **Múi giờ ba lớp** (§5.6).
7. **Về hưu đồ Windows và wrapper Node**: `core/console.py`, `scripts/register-tasks.ps1`, `scripts/stack.mjs` + `package.json` (§5.7).
8. **Dựng lại kho dev từ đầu** trên project `dlck`; xoá volume cũ sau khi nghiệm thu (§5.9).
9. Test hợp đồng canh lệch `.env.example` ↔ compose ↔ code, và múi giờ (§6).
10. Tài liệu sống (§8) + khép roadmap bằng "Điểm vào cho lát 13".

### 3.2 Ngoài phạm vi — ba loại *(§1.4)*

| Mục | Loại | Lý do |
|---|---|---|
| Scheduler / bảng lịch / chạy bù / chặn chạy chồng | **Đã có đường khác** | Lát 13. Lát này chỉ để service `etl` giữ heartbeat như hiện tại; lát 13 thay `command` |
| Trần RAM/CPU cho `api`/`etl`/`ingester` trong overlay VPS | **Đã có đường khác** | Lát 15 — chưa đo dưới hồ sơ hẹp; overlay hiện tại (postgres/redis/clickhouse) được **chuyển nguyên** lên gốc, không thêm số chưa đo |
| Reverse proxy / TLS / firewall cổng 8000 trên VPS | **Đã có đường khác** | Lát 15 |
| `api` ngoài `/api/healthz` | **Loại có chủ đích** | `api` chưa bắt đầu; lát này chỉ cần nó chạy trong image chung |
| Docker secrets / `*_FILE` (phương án P3) | **Loại có chủ đích** | §4.1: chi phí gấp ba cho mô hình đe doạ dự án không có |
| Gộp `Fetcher` / cấu hình tập trung kiểu settings object | **Loại có chủ đích** | Quyết định §4.8 2026-09-08 (P2 của hồ sơ audit) — chỉ xét lại nếu lát này lộ nhu cầu; **không lộ** (hàm ráp một chỗ là đủ) |
| Registry image (GHCR) / CI build | **Loại có chủ đích** | Chủ dự án chốt 2026-09-08: build ngay trên VPS từ git clone |
| Chạy `pytest` trong container | **Loại có chủ đích** | Chủ dự án chốt: native giữ cho dev/test; bộ test tự spawn container ClickHouse bằng docker CLI |
| Bật lại ingester ghi thật hằng ngày | **Đã có đường khác** | [4d]: sau lát 12–14, chạy thử vài ngày trên dev, rồi VPS |
| Cổng health 8100 của ingester (topology §6) | **Loại có chủ đích** | Chưa ai đọc; `restart` + log đủ cho lát này; lát 14 giám sát xét |
| Thư mục `../dlck-runtime` (log/measure/spill thời Windows) và `deploy/infra/clickhouse-backups/` cũ trên máy dev | **Loại có chủ đích** | Ngoài repo, không hại; chủ dự án tự xoá nếu muốn |
| `ruff` | **Đã có đường khác** | Chủ dự án: sau lát 12 |

## 4. Quyết định

### 4.1 Hình dạng cấu hình — P2 "`.env` nguyên tố + một hàm ráp" *(§4.8, ba phương án độc lập do ba subagent Sonnet sinh song song 2026-09-08, chấm theo tiêu chí viết trước)*

**Tiêu chí viết trước khi sinh phương án:** (a) một `.env` cho một máy, cùng file phục vụ native lẫn container không sửa tay · (b) cùng code, cùng image, không rẽ nhánh "đang trong container" · (c) secret một chỗ, đổi một mật khẩu = sửa một chỗ · (d) bán kính hỏng, rollback một `git revert` · (e) lát 13/15 chỉ đổi biến/overlay · (f) có test canh lệch · (g) giữ hợp đồng khởi động (thiếu env ⇒ exit 2 · `assert_migrated` · `assert_read_only`) · (h) cấp 4 user login tự động từ env.

| | a | b | c | d | e | f | g | h |
|---|---|---|---|---|---|---|---|---|
| **P1** — compose dịch host bằng `environment:`, 0 dòng code | ✗ mật khẩu ×2 trong `.env`, URL lặp ở mỗi service | ✓ | ✗ | ✓✓ 3 file | ✓ | yếu | ✓ nhưng bind-mount `database/` từ host | có, trùng lặp |
| **P2** — `.env` nguyên tố + `_compose_urls()` | ✓✓ mỗi thứ một lần | ✓ | ✓ | ~12 file | ✓✓ | ✓✓ | ✓ | ✓✓ |
| **P3** — secret theo file, least privilege | ✗ 8 file secret tạo tay | ✓ | ✓✓ | ✗ ~25 file | ~ | ~ | ~ | không xoay vòng |

**Chọn P2 nguyên vẹn.** Lý do loại:

- **P1** tái tạo đúng bẫy hai nguồn sự thật (§1.7): mỗi mật khẩu sống hai dạng trong cùng `.env` (nhúng URL cho native, biến rời cho compose), mỗi URL lặp ở từng service trong YAML; image không tự đủ vì phải bind-mount `database/` từ host — trái mục tiêu "đóng gói hoàn chỉnh".
- **P3** tốn ~25 file cho một mô hình đe doạ dự án không có (một người, một máy; secret của compose cũng chỉ là bind mount, chỉ tránh được kênh `inspect`/`ps`); hai giả định chưa kiểm (`CLICKHOUSE_PASSWORD_FILE` trên tag đang ghim, bind-mount file đơn trên Windows); không xoay vòng mật khẩu.

**Một chi tiết P2 bỏ sót, thêm vì là điều kiện đúng của chính P2:** mật khẩu phải **URL-encode** (`urllib.parse.quote`, `safe=""`) khi ráp — không phải mượn từ phương án khác.

**Điều kiện đảo ngược:** (1) một tiến trình cần host Postgres/ClickHouse *khác* các tiến trình còn lại trong cùng môi trường ⇒ tách `*_HOST` theo consumer; (2) kết nối cần SSL/replica/tham số mà `user:pass@host:port/db` không biểu diễn nổi ⇒ cần cấu trúc khác hàm ráp; (3) `.env` nguyên tố vượt ~30 dòng và bắt đầu khó đọc ⇒ xét nhóm theo tiền tố hoặc file cấu hình không-bí-mật riêng.

Ba bản phương án nguyên văn (tài sản, ngăn mở lại ngõ cụt): [`options/`](options/) — `option-P1.md` · `option-P2.md` · `option-P3.md` · `criteria.md`.

### 4.2 Bảy quyết định chủ dự án 2026-09-08 (chép từ roadmap §0 điểm vào lát 12, không diễn giải lại)

Bật lại ingester sau 12–14 · kho dev **xoá và dựng lại** (2026-09-08: *"cứ clear hết toàn bộ infra db cũ để dựng lại cho chuẩn chỉ, không cần lưu trữ gì"*) · migration **trong** container · ingester **trong** phạm vi · tiêu chí nghiệm thu chi tiết chốt ở spec này (§7) · múi giờ ba lớp · `ruff` sau lát.

Hai câu hỏi brainstorm, chủ dự án chốt cùng ngày: **native giữ cho dev/test** (Docker là hình dạng production) · **image build ngay trên VPS từ git clone** (không registry).

### 4.3 Điểm trợ lý tự chốt — ghi §9 để chủ dự án rà

1. ClickHouse **luôn bật**, bỏ profile `realtime` và biến `COMPOSE_PROFILES`.
2. `scripts/stack.mjs` + `stack.test.mjs` + `package.json` **về hưu** (trỏ vào compose không còn; thay bằng lệnh `docker compose` thẳng).
3. Bootstrap `ALTER … PASSWORD` **mỗi lần chạy** để `.env` luôn là nguồn thật (idempotent, rẻ).
4. Postgres **giữ UTC** (không đặt `TZ`/`timezone` cho container postgres) — code đã học tránh `now()` phía DB; đổi nay là đổi nghĩa đang chạy.
5. Ingester **tự ngủ ngoài phiên** trong lát này (không đợi lát 13) vì `restart: unless-stopped` + thoát-ngay là vòng khởi động lại vô nghĩa gọi REST BVSC suốt đêm.
6. `.env.example` chỉ còn biến **có người đọc** (code hoặc compose); bỏ `APP_ENV`, `LOG_LEVEL`, `COMPOSE_PROFILES`; có test canh.
7. `core.ch_backup` giải đường dẫn tương đối theo **gốc repo** (khớp compose gốc) thay vì `deploy/infra`.
8. Dev **xoá sáu volume cũ** sau khi nghiệm thu xong (§5.9), không xoá `tutor-infra_pgdata`.

## 5. Thiết kế

### 5.1 `.env` nguyên tố và hàm ráp

**`.env` sau lát này** (giá trị mẫu ở `.env.example`; máy dev host `127.0.0.1`):

| Biến | Nghĩa | Ai đọc |
|---|---|---|
| `POSTGRES_HOST` `POSTGRES_PORT` `POSTGRES_DB` `POSTGRES_USER` `POSTGRES_PASSWORD` | Postgres, user owner | hàm ráp · compose service `postgres` (initdb) · bootstrap |
| `POSTGRES_TEST_DB` *(mặc định `dulieu_test`, có thể bỏ trống)* | DB test | hàm ráp |
| `ETL_DB_USER` `ETL_DB_PASSWORD` | login `etl_worker` ∈ `dlck_etl` | hàm ráp · bootstrap |
| `AGENT_DB_USER` `AGENT_DB_PASSWORD` | login `agent_reader` ∈ `dlck_api` | hàm ráp · bootstrap |
| `REDIS_HOST` `REDIS_PORT` `REDIS_DB` *(mặc định `0`)* | Redis | hàm ráp |
| `CLICKHOUSE_HOST` `CLICKHOUSE_PORT` `CLICKHOUSE_PASSWORD` | ClickHouse, owner `default` | hàm ráp · compose service `clickhouse` · bootstrap |
| `CLICKHOUSE_INGESTER_USER` `CLICKHOUSE_INGESTER_PASSWORD` | login `ingester_worker` ∈ `dlck_ingester` | hàm ráp · bootstrap |
| `CLICKHOUSE_API_USER` `CLICKHOUSE_API_PASSWORD` | login `api_reader` ∈ `dlck_api` (chưa consumer nào dùng URL) | bootstrap |
| `CLICKHOUSE_BACKUP_DIR` | thư mục backup (host, bind-mount) | compose · `ch_backup` (native) |
| `INGESTER_LOG_DIR` `INGESTER_MEASURE_DIR` `INGESTER_SPILL_DIR` | để trống khi native (mặc định `<repo>/../dlck-runtime/…`) | ingester |
| `LLM_API` (+ `LLM_BASE_URL` `LLM_MODEL` `LLM_TIMEOUT_S` tuỳ chọn) · `FRED_API` | khoá dịch vụ ngoài | `core/llm/settings.py` · `fred_fetch` |
| `COMPOSE_FILE` *(chỉ VPS)* · `COMPOSE_PROJECT_NAME` *(tuỳ chọn)* | chọn overlay / tên project | Docker Compose |

**Xoá khỏi `.env`** (thành giá trị ráp): `DATA_DATABASE_URL` `TEST_DATABASE_URL` `ETL_DATABASE_URL` `AGENT_DATABASE_URL` `CLICKHOUSE_URL` `CLICKHOUSE_INGESTER_URL` `REDIS_URL`; xoá hẳn `APP_ENV` `LOG_LEVEL` `COMPOSE_PROFILES`.

**Hàm ráp** `core.env._compose_urls()` — gọi ở **cuối** `load_dotenv()`, chạy kể cả khi không có file `.env` (container). Với mỗi URL: nếu **đủ** nguyên tố bắt buộc thì `os.environ.setdefault(tên, chuỗi)`; thiếu bất kỳ nguyên tố nào thì **bỏ qua URL đó, không ném** — consumer tự thi hành hợp đồng "thiếu env ⇒ exit 2" như hôm nay. Biến đã có sẵn trong môi trường **thắng** (setdefault), nên `TEST_DATABASE_URL` export ở CI hay `CLICKHOUSE_URL` do fixture test gán vẫn đè được.

```
DATA_DATABASE_URL       = postgresql+psycopg://{POSTGRES_USER}:{q(POSTGRES_PASSWORD)}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}
TEST_DATABASE_URL       = … như trên …/{POSTGRES_TEST_DB | dulieu_test}
ETL_DATABASE_URL        = postgresql+psycopg://{ETL_DB_USER}:{q(ETL_DB_PASSWORD)}@…/{POSTGRES_DB}
AGENT_DATABASE_URL      = postgresql+psycopg://{AGENT_DB_USER}:{q(AGENT_DB_PASSWORD)}@…/{POSTGRES_DB}
CLICKHOUSE_URL          = http://default:{q(CLICKHOUSE_PASSWORD)}@{CLICKHOUSE_HOST}:{CLICKHOUSE_PORT}
CLICKHOUSE_INGESTER_URL = http://{CLICKHOUSE_INGESTER_USER}:{q(CLICKHOUSE_INGESTER_PASSWORD)}@{CLICKHOUSE_HOST}:{CLICKHOUSE_PORT}
REDIS_URL               = redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB | 0}
```

`q` = `urllib.parse.quote(x, safe="")`. Không dòng nào hỏi "đang trong container" — khác biệt native/container chỉ ở giá trị ba biến `*_HOST` mà compose đè.

**CLI nhỏ** `python -m core.env check`: in **tên** biến bắt buộc còn thiếu và biến lạ (không bao giờ in giá trị), thoát 1 nếu thiếu — dùng khi điền `.env` trên máy mới.

**Consumer không đổi dòng đọc.** Thay đổi kèm theo: `tests/conftest.py` suy URL admin từ `POSTGRES_DB` thay literal `"dulieu"`; `database/migrations/env.py` gọi `load_dotenv()` (bỏ hai dòng `export` tay trong README); `database/alembic.ini` thêm `prepend_sys_path = backend`; `core/ch_migrate.py` và `core/ch_backup.py` gọi `load_dotenv()` đầu `main()`.

### 5.2 Một compose gốc, một lệnh

`docker-compose.yml` ở **gốc repo**, `name: dlck`. Ba file `deploy/infra/docker-compose.yml`, `deploy/infra/docker-compose.vps.yml`, `deploy/app/docker-compose.yml` **xoá**; nội dung chuyển lên gốc (overlay giữ nguyên số đo, chỉ đổi đường dẫn xml). `deploy/infra/clickhouse/*.xml` **giữ nguyên chỗ** (test conftest trỏ vào đó).

| Service | Vai | Ghi chú |
|---|---|---|
| `postgres` `redis` `clickhouse` | kho | như hiện tại; cổng bind `127.0.0.1` cho native; healthcheck giữ; ClickHouse **không còn profile** |
| `migrate` | one-shot | `python -m core.bootstrap` (§5.4); `restart: "no"`; `depends_on` ba kho `service_healthy` |
| `api` | web | CMD uvicorn của image; `depends_on: migrate: service_completed_successfully`; cổng `8000:8000` |
| `etl` | vỏ job | `command: ["python","-m","etl"]` (heartbeat, giữ tới lát 13); mount backup dir; **job chạy bằng `docker compose run --rm etl python -m etl <job> …`** |
| `ingester` | daemon | `python -m ingester` (§5.5); ba volume runtime; `depends_on` migrate + clickhouse + redis |
| `ingester-measure` | daemon, `profiles: [measure]` | `python -m ingester --measure`; volume measure/logs; tắt mặc định |
| `agent` | `profiles: [tools]` | `docker compose run --rm agent` mở REPL; không `restart` |

Mọi service app (`api` `etl` `ingester` `ingester-measure` `agent`) `depends_on: migrate: condition: service_completed_successfully`, và dùng chung một neo YAML `x-app` (build, `env_file: .env`, `restart`, và `environment:` đè): `POSTGRES_HOST: postgres` · `REDIS_HOST: redis` · `CLICKHOUSE_HOST: clickhouse` · `TZ: Asia/Ho_Chi_Minh` · `INGESTER_LOG_DIR: /var/lib/dlck/logs` · `INGESTER_MEASURE_DIR: /var/lib/dlck/measure` · `INGESTER_SPILL_DIR: /var/lib/dlck/spill` · `CLICKHOUSE_BACKUP_DIR: /backups`. Đây là **toàn bộ** danh sách biến compose được đè — test §6 canh đúng tập này.

**Volume:** `pgdata` `redisdata` `chdata` (như cũ) + `ingester_logs` `ingester_measure` `ingester_spill` (có tên, mount vào `/var/lib/dlck/…`; trần spill 10 GiB giữ nguyên) + bind `${CLICKHOUSE_BACKUP_DIR}` → `clickhouse:/backups` và `etl:/backups`.

**VPS:** `.env` VPS đặt `COMPOSE_FILE=docker-compose.yml:docker-compose.vps.yml`, nên lệnh vẫn là `docker compose up -d --build`. Overlay chỉ chứa trần tài nguyên ba kho như hôm nay (chuyển nguyên, đổi đường dẫn `memory-vps.xml`).

### 5.3 Image tự đủ

`deploy/backend.Dockerfile`, build context **gốc repo**:

```
/app/backend/   ← COPY backend/ (uv sync --frozen --no-dev tại đây; .venv trong này)
/app/database/  ← COPY database/ (alembic.ini, migrations/, clickhouse/versions/)
WORKDIR /app/backend · PATH=/app/backend/.venv/bin · USER appuser
```

⇒ `REPO_ROOT` trong container = `/app` (đúng cấp với native), `ch_migrate.DEFAULT_VERSIONS_DIR` = `/app/database/clickhouse/versions` tự đúng. `.dockerignore` **gốc** (thay `backend/.dockerignore`): `.git` `.env*` `**/.venv` `**/__pycache__` `backend/tests` `docs` `node_modules` `deploy/infra/clickhouse-backups`. `.env` **không bao giờ** vào image.

### 5.4 `core.bootstrap` — lệnh của service `migrate`

Chạy bằng **owner** cả hai kho (`DATA_DATABASE_URL`, `CLICKHOUSE_URL` ráp từ nguyên tố), thứ tự cứng, idempotent, thoát 2 ở bước đầu tiên hỏng, in tóm tắt **không giá trị secret**:

1. **Alembic `upgrade head`** qua API (cùng cách `tests/conftest.py`, cwd = `REPO_ROOT`).
2. **`ch_migrate.upgrade()`**.
3. **Cấp user login**: Postgres `CREATE ROLE IF NOT EXISTS`-tương-đương (`DO $$ … $$`, khuôn `0009`) rồi **luôn** `ALTER ROLE … LOGIN PASSWORD` và `GRANT dlck_etl`/`dlck_api`; ClickHouse `CREATE USER IF NOT EXISTS … DEFAULT ROLE …` rồi **luôn** `ALTER USER … IDENTIFIED WITH sha256_password BY …`. Bốn user: `etl_worker` `agent_reader` `ingester_worker` `api_reader`, tên và mật khẩu từ §5.1.
4. **Tự seed lớp 2 ngành khi phát hiện thiếu**: nếu `count(market.security) > 0` **và** `count(market.issuer_industry_override) = 0` ⇒ chạy đúng nhịp `downgrade 0012` → `upgrade head` rồi kiểm `= 161`, thiếu ⇒ thoát 2. Kho mới lúc `up` lần đầu: `security` rỗng ⇒ bỏ qua có log; sau lượt `etl refdata` đầu tiên, lần `up` (hoặc `docker compose run --rm migrate`) kế tiếp tự seed. Kho đã có 161 ⇒ bỏ qua.

`database/clickhouse/create_users.sql.example` xoá; README hai kho trỏ về bootstrap.

### 5.5 Ingester — daemon thật

`python -m ingester` (không `--minutes`) nay là **vòng cửa sổ phiên**, giờ VN:

- Cửa sổ ghi thật `[08:30, 15:05)` ngày thứ 2–6 (`SESSION_START = (8, 30)` mới; `SESSION_END_RUN` giữ). Mode measure: `[08:30, 15:10)`.
- Ngoài cửa sổ: ghi **một** dòng log "ngoài phiên, chờ tới `<mốc>`", ngủ tới mốc (ngủ theo lát 60 s để Ctrl+C/`SIGTERM` dừng nhanh). Ngày lễ không biết ⇒ vẫn nối như hôm nay (vô hại, giống task Windows).
- Trong cửa sổ: chạy `_run_run`/`_run_measure` **y như hiện tại** (kể cả hợp đồng khởi động mỗi phiên), ghi phán quyết đối chứng ra log, rồi quay lại chờ.
- Lỗi hợp đồng khởi động vẫn thoát **3** ⇒ Docker khởi động lại có giãn cách — đúng ý "chờ kho có giới hạn" ([service-topology §5](../../../20-design/service-topology.md)). Lỗi giữa phiên: giữ hành vi hiện tại của `_run_run`.
- `--minutes N` **giữ nguyên nghĩa** (chạy N phút rồi thoát 0/1) — đường nghiệm thu và chạy tay.
- Không đụng `--reconcile`, `--count`.
- **Tín hiệu dừng.** `docker compose down`/`stop` gửi `SIGTERM`; Python mặc định chết ngay, không đi qua đường đóng phiên mà Ctrl+C (`KeyboardInterrupt`) đang có ⇒ hàng đợi RAM chưa xả là mất. Lát này đăng ký `SIGTERM` → nâng thành `KeyboardInterrupt` ở cả `ingester/__main__.py` lẫn `etl/__main__.py` (job đang chạy qua `docker compose run` cũng đóng sổ `failed: dừng tay`, exit 130 như hợp đồng `test_e42`), và compose đặt `stop_grace_period: 90s` cho `ingester` (xả hàng đợi + đối chứng) và `60s` cho `etl`. Trên Windows native handler đăng ký được nhưng không có tác dụng thực tế — chấp nhận, Ctrl+C vẫn là đường dừng ở đó.

Hàm thuần `next_window(now, start_hm, end_hm) -> (start, end)` tách riêng để test bằng literal; vòng lặp nhận `clock`/`sleep`/`run_session` tiêm được.

### 5.6 Múi giờ — ba lớp

1. **Code**: ba chỗ `date.today()` trần → `datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).date()` (`refdata_job`, `ch_backup.run_backup` mặc định, `agent/system_prompt`).
2. **Compose**: `TZ: Asia/Ho_Chi_Minh` ở mọi service app (neo `x-app`); ClickHouse đã có; Postgres **không** (§4.3.4).
3. **Test hợp đồng** `tests/core/test_tz_contract.py`: quét `backend/` ngoài `tests/` và `.venv`, đỏ nếu còn `date.today()`, `datetime.now()` không đối số, `datetime.utcnow()`, `datetime.today()`; cộng phép tự kiểm "quét được ≥ 60 file" để phép kiểm không tự rỗng.

### 5.7 Về hưu

| Xoá | Kèm |
|---|---|
| `backend/core/console.py` | `tests/core/test_console.py`; gỡ `lock_if_scheduled` ở `etl/__main__.py`, `ingester/__main__.py`; gỡ `banner` ở `price_job` (hai dòng "bắt đầu …" chuyển thành `log.info`) |
| `scripts/register-tasks.ps1` | 11 task trên máy dev: **chủ dự án gỡ tay** `Get-ScheduledTask dlck-* \| Unregister-ScheduledTask -Confirm:$false` (không cần admin, task Interactive) — plan ghi thành bước có kiểm `Get-ScheduledTask dlck-*` rỗng |
| `scripts/stack.mjs` `scripts/stack.test.mjs` `package.json` | README bỏ `npm run …`, thay bằng lệnh compose (§5.8) |
| `deploy/infra/docker-compose*.yml` `deploy/app/docker-compose.yml` `backend/.dockerignore` `database/clickhouse/create_users.sql.example` | thay bởi file gốc (§5.2–5.4) |

### 5.8 Lệnh vận hành sau lát này *(chép vào README, chủ ở đó)*

```bash
# máy mới (dev hoặc VPS): clone → cp .env.example .env → điền → kiểm tên biến
(cd backend && uv run python -m core.env check)          # hoặc: docker compose run --rm migrate python -m core.env check
docker compose up -d --build                             # kho + migrate + api + etl(heartbeat) + ingester(daemon)
docker compose run --rm etl python -m etl refdata        # danh bạ — lượt đầu của kho mới
docker compose run --rm migrate                          # lần hai: tự seed 161 dòng ngành lớp 2
docker compose run --rm etl python -m etl <job> [cờ]     # bất kỳ họ job nào
docker compose run --rm agent                            # REPL tầng ngữ nghĩa
docker compose --profile measure up -d ingester-measure  # lưới an toàn frame thô (tuỳ chọn)
docker compose run --rm etl python -m core.ch_backup     # backup ClickHouse
docker compose down && docker compose up -d              # không mất gì (AC5)
```

Native trên dev **không đổi cách gọi**: `cd backend && uv run pytest tests -q`, `uv run python -m etl <job>` — cùng `.env`.

### 5.9 Dựng lại kho dev — thứ tự và xoá

1. Đầu lượt thực thi, **trước khi xoá file compose cũ**: `docker compose -p infra -f deploy/infra/docker-compose.yml --profile realtime down` để trả cổng; **không** xoá volume.
2. Dựng project `dlck` mới theo §5.8; nghiệm thu §7 trên kho mới này (vừa là AC "kho mới" cho VPS).
3. **Sau khi §7 xanh**, xoá đúng sáu volume: `infra_pgdata` `infra_chdata` `infra_redisdata` `dlck-infra_pgdata` `dlck-infra_chdata` `dlck-infra_redisdata` (chủ dự án uỷ quyền 2026-09-08). **Không** đụng `tutor-infra_pgdata`. Ghi lệnh và output vào ledger.

## 6. Seam test *(chốt cùng spec — §4.5.2; expected là literal, không tính lại theo code)*

| Seam | Test đỏ trước | Case biên/sai |
|---|---|---|
| `core.env._compose_urls` | với dict nguyên tố cho trước, `ETL_DATABASE_URL` == chuỗi literal; mật khẩu `p@ss:w/rd` ⇒ `p%40ss%3Aw%2Frd` | thiếu `ETL_DB_PASSWORD` ⇒ không có biến; biến có sẵn không bị đè |
| `core.env` CLI `check` | thiếu `POSTGRES_PASSWORD` ⇒ exit 1, stdout chứa tên biến, **không** chứa giá trị nào của env | đủ ⇒ exit 0 |
| Hợp đồng `.env.example` ↔ code ↔ compose | mọi khoá trong `.env.example` được đọc ở đâu đó (code ngoài test, hoặc compose, hoặc Compose nội tại `COMPOSE_*`); mọi tên `os.environ` đọc trong code ngoài test có trong `.env.example` hoặc thuộc tập ráp/đè; compose không chứa khoá nào đuôi `_URL`; tập `environment:` đè == đúng danh sách §5.2 | thêm một khoá thừa vào `.env.example` ⇒ đỏ |
| `core.bootstrap.provision_postgres` (DB test, owner) | sau khi chạy: `pg_has_role('etl_worker','dlck_etl','member')` true; nối bằng mật khẩu mới được; chạy lần hai với mật khẩu khác ⇒ mật khẩu cũ **bị từ chối** | role đích không tồn tại ⇒ ném lỗi rõ |
| `core.bootstrap.provision_clickhouse` (CH ephemeral) | `ingester_worker` SELECT được `rt.*`, `CREATE TABLE` bị `ACCESS_DENIED`; `ALTER` đổi mật khẩu có hiệu lực | nt |
| `core.bootstrap.reseed_if_needed` (DB test) | `security` rỗng ⇒ trả `skipped`, không đụng override; chèn `issuer`+`security` cho **một** ticker lấy từ `industry-mapping.json` ⇒ sau reseed override có **1** dòng đúng ticker đó; chạy lần hai ⇒ `skipped` | override đã có dòng ⇒ không chạy |
| `ingester.main.next_window` | thứ 6 16:00 ⇒ thứ 2 08:30; thứ 7 10:00 ⇒ thứ 2 08:30; thứ 3 07:00 ⇒ thứ 3 08:30; thứ 3 09:00 ⇒ đang trong cửa sổ, `end` = 15:05 cùng ngày (literal `datetime` có tz) | 15:05:00 đúng mốc ⇒ đã ngoài |
| Vòng daemon (`clock`/`sleep`/`run_session` giả) | ngoài phiên: `run_session` **không** gọi, `sleep` gọi với mốc đúng; trong phiên: gọi đúng một lần rồi ngủ tới mốc kế | `run_session` trả 3 ⇒ vòng thoát 3 |
| Tín hiệu dừng | tiến trình con `python -m etl omo` (hoặc job giả cùng khuôn) nhận `SIGTERM` ⇒ sổ `ops.etl_run` đóng `failed: dừng tay`, exit 130 — mở rộng `test_e42` sang `SIGTERM`; chỉ chạy trên POSIX (`pytest.mark.skipif(win32)`) vì Windows không giao `SIGTERM` | handler không đăng ký ⇒ tiến trình chết không đóng sổ ⇒ đỏ |
| Múi giờ (hợp đồng tĩnh) | không còn `date.today()`/`datetime.now()` trần trong `backend/` ngoài test; phép kiểm quét ≥ 60 file | chèn một `date.today()` vào file tạm trong phạm vi ⇒ đỏ |
| Ba chỗ sửa §5.6 | `refdata_store.upsert_domain_state` nhận ngày VN: mock `now` 2026-09-08 00:30 VN (= 07/09 17:30 UTC) ⇒ mốc `2026-09-08` | nt cho `ch_backup`/`system_prompt` |
| `tests/conftest.py` | fixture chạy được khi `.env` chỉ có nguyên tố (không có `TEST_DATABASE_URL`) — `test_conftest_env_contract` cập nhật theo | — |
| Dockerfile/compose (tĩnh) | Dockerfile không `COPY` `.env`; `.dockerignore` gốc chứa `.env*` và `backend/tests` | — |

Cần thêm `pyyaml` vào `dependency-groups.dev` để test đọc compose (không vào dependencies chính).

## 7. Tiêu chí nghiệm thu *(chạy thật, dán output vào ledger; hỏng thì báo hỏng nguyên trạng)*

| # | Tiêu chí | Cách kiểm |
|---|---|---|
| AC1 | Build sạch từ clone mới thành công; image **không** chứa `.env`, không chứa `backend/tests`; có `/app/database/alembic.ini` | `git clone` vào thư mục tạm → `docker compose build`; `docker run --rm <image> sh -c 'ls /app; test ! -e /app/.env'` |
| AC2 | `docker compose up -d --build` trên kho **mới**: `migrate` exit 0 (schema head `0020`, `rt` tới `0002`, 4 user); `api` `/api/healthz` 200; `etl` heartbeat; `ingester` log "ngoài phiên, chờ tới …" (chạy ngoài giờ) | `docker compose ps -a`; `curl`; `docker compose logs` |
| AC3 | **Cả 15 họ job chạy trong container, ghi kho thật, mỗi họ ≥ 1 dòng `ops.etl_run` với `status ∈ {success, failed-có-lý-do-guard}`, mã thoát 0 hoặc 1, KHÔNG BAO GIỜ 2.** Thứ tự và cờ hẹp: `refdata` → `migrate` lần hai (seed 161) → `events --accept-new` (kho mới ⇒ > 20 issuer mới là mong đợi) → `price --codes <2 mã>` → `snapshot --codes <1 mã> --kinds snapshot` → `fundamentals --codes <1 mã> --kinds <1 kind>` → `screener` (ngoài phiên ⇒ guard từ chối, exit 1, **đúng**) → `omo` → `wichart --keys <1>` → `fred --keys <1>` → `fx` → `lbma` → `yahoo --keys <1>` → `binance --keys <1>` → `news --sources <1>` → `classify --limit 1`. Mã/khoá cụ thể chọn ở plan | `docker compose run --rm etl …` từng lệnh; truy vấn `ops.etl_run` dưới owner; bảng 15 dòng vào ledger |
| AC4 | Ingester trong container ngoài giờ: `docker compose run --rm ingester python -m ingester --minutes 2` qua `assert_migrated` dưới `ingester_worker`, nối socket, thoát 0/1 kèm dòng `reconcile:`; file log xuất hiện trong volume `ingester_logs`; `SpillStore` giành được lock (giả định 2.2.2) | log + `docker compose run --rm ingester ls /var/lib/dlck/logs` |
| AC5 | `docker compose down` rồi `up -d`: số dòng `ops.etl_run`, `market.security`, `rt.schema_migrations` **không đổi**; danh sách volume `dlck_*` không đổi; `migrate` chạy lại exit 0 no-op | đếm trước/sau, `docker volume ls` |
| AC6 | Đổi `ETL_DB_PASSWORD` trong `.env` → `docker compose run --rm migrate` → job `etl omo` vẫn success với mật khẩu mới; mật khẩu cũ bị từ chối | chạy thật, không dán giá trị |
| AC7 | `core.ch_backup` trong container ghi zip vào `${CLICKHOUSE_BACKUP_DIR}` trên host | `ls` thư mục host |
| AC8 | Native không hỏng: `cd backend && uv run pytest tests -q` xanh với `.env` hình dạng mới (số hiện hành do `database/README.md` sở hữu); `uv run python -m etl omo` native success | output pytest |
| AC9 | Sau khi gỡ 11 task và xoá 6 volume cũ: `Get-ScheduledTask dlck-*` rỗng; `docker volume ls` không còn `infra_*`/`dlck-infra_*`; `tutor-infra_pgdata` còn nguyên | output lệnh |

## 8. Checklist tài liệu sống — cùng lượt với code *(§1.6, §1.7)*

- `README.md` gốc: mục cách chạy (§5.8), bỏ `npm run`, bỏ "Hai bộ volume" (thay bằng một dòng "project `dlck`"), trạng thái lát 12.
- `backend/README.md`: bỏ mục "Lịch chạy (Windows Task Scheduler)" và mọi câu về cửa sổ `cmd`/nút X; thêm "Chạy trong container"; mục ingester ghi vòng cửa sổ phiên.
- `database/README.md`: mục "Cách chạy" và "Bootstrap DB mới" theo `core.bootstrap`; bỏ `CREATE USER` tay; bỏ export `DATA_DATABASE_URL` tay.
- `.env.example`: viết lại theo §5.1, mỗi biến một dòng chú thích "ai đọc".
- `docs/20-design/service-topology.md`: §5 (Task Scheduler về hưu, Docker Desktop vẫn trong session — giữ cảnh báo reboot), §6 (bố cục container + volume), §7b (spill là volume có tên).
- `docs/00-overview/roadmap.md`: đóng lát 12, viết **"Điểm vào cho lát 13"** (scheduler: `etl` service đã có vỏ; danh sách 15 họ + cờ; ingester tự lo cửa sổ; migrate re-run; nhịp đo lát 4/11).
- `docs/90-records/README.md`: dòng hồ sơ này (đã thêm cùng commit spec).
- `CLAUDE.md` §5 Môi trường: thêm một dòng "chạy production = Docker, `docker compose up -d --build`".
- `git grep` sau cùng: `register-tasks` · `stack.mjs` · `npm run` · `COMPOSE_PROFILES` · `DLCK_LOCK_CONSOLE` · `deploy/infra/docker-compose` · `ETL_DATABASE_URL=` — mọi hit còn lại phải thuộc `90-records/` hoặc `decisions/`.

## 9. Điểm cần chủ dự án duyệt tường minh

1. Tám điểm tự chốt ở **§4.3** — đặc biệt (1) bỏ profile `realtime`, (2) về hưu `stack.mjs`/`package.json`, (8) xoá sáu volume cũ sau nghiệm thu.
2. **Tên biến mới** ở §5.1 (`ETL_DB_USER`… `CLICKHOUSE_INGESTER_PASSWORD`): chủ dự án sẽ phải **tự viết lại `.env`** theo bảng này (tôi không đọc/sửa file đó); `python -m core.env check` báo tên biến còn thiếu.
3. AC3 chấp nhận `screener` **exit 1** ngoài phiên là đúng hành vi (guard "có phiên"), và `events` chạy với `--accept-new` trên kho mới.
4. Cửa sổ ingester `[08:30, 15:05)` thứ 2–6, không lịch nghỉ lễ (giữ như task Windows).
5. Xoá `dlck-price-backfill` cùng 10 task kia (backfill giá về hưu theo quyết định xoá kho; lát 13 xếp lại nếu cần).


---

## Đính chính khi viết plan — 2026-09-08 *(không sửa phần trên: đó là bản duyệt)*

**§5.4 bước 4 sai một nhịp lệnh.** Spec viết *"chạy đúng nhịp `downgrade 0012` → `upgrade head`"* theo `database/README.md` mục Bootstrap. Câu đó **đúng khi head là `0013`** (lúc README viết, 2026-08-28). Head nay là `0020`: `alembic downgrade 0012` lùi **tám** migration — `DROP` `news.article_industry`, `ops.llm_call`, `ops.snapshot_check`, cột `directory_absent_since`… **kèm dữ liệu**. Một bước "tự động khi phát hiện thiếu" mà phá dữ liệu thì không được tồn tại.

**Cách đúng (plan Task 8):** `core.bootstrap` chạy lại **riêng** revision `0013` — `ScriptDirectory.from_config(cfg).get_revision("0013").module`, rồi `downgrade()` + `upgrade()` của module đó trong một transaction dưới `Operations.context(MigrationContext.configure(conn))`. Không đụng `alembic_version`, không đụng migration khác. Alembic 1.19.1 đang cài có cả hai API (kiểm 2026-09-08). Nghiệm thu (161 dòng) không đổi.

**Hệ quả cho tài liệu sống (plan Task 11):** `database/README.md` và `README.md` gốc phải **thay** hướng dẫn `downgrade 0012` bằng cảnh báo — bẫy này nằm sẵn trong tài liệu từ khi head vượt `0013`, lát 12 chỉ tình cờ chạm vào.

**§5.5 "Tín hiệu dừng" chỉ đúng cho 11 họ job, chưa đủ cho ingester** *(phát hiện ở review Task 5, 2026-09-08)*. Nâng `SIGTERM` thành `KeyboardInterrupt` chạy đúng `except KeyboardInterrupt` mà mọi `*_job.py` đã có (đóng sổ, exit 130). Nhưng `ingester/main.py` là vòng asyncio **không có** `except KeyboardInterrupt`: ngoại lệ ném giữa `await stop.wait()` thoát thẳng khỏi `asyncio.run()`, đuôi phiên (xả hàng đợi, đối chứng) **không chạy** — và điều này vốn đã đúng với Ctrl+C từ trước lát 12. Cách đúng cho asyncio: tín hiệu → `stop.set()` trên loop (`loop.add_signal_handler`), để phiên đóng y như tới deadline; Windows không hỗ trợ nên giữ đường cũ ở đó. Thực thi ở plan Task 6 (`install_loop_stop`), docstring `core/shutdown.py` thu hẹp lời hứa cho đúng.

**Bốn module đọc file dưới `docs/` lúc chạy — spec không biết, image không mang** *(phát hiện ở Task 10, 2026-09-08 18:51; chỉ đạo chủ dự án ~19:05)*. §5.3 loại `docs` khỏi image là **đúng**, nhưng `fundamentals_store` (từ điển 729 mã) · `news_registry` (`feeds.json`) · `screener_normalize` (`market-field-selection.json`) · `wichart_registry` (khối Python §9 `wichart.md`, `exec`) đều ráp đường dẫn vào `docs/` ⇒ bốn họ `fundamentals` `news` `screener` `wichart` chết `exit 2` trong container. **Chỉ đạo chủ dự án:** code không đọc `docs/` — tri thức code cần phải nằm trong `backend/`/`database/`; **không** đưa `docs/` (thứ không kiểm soát được) vào image; phần tra cứu cần thì hardcode lại thành file JSON/md chuẩn hoá trong code. Thực thi ở plan **Task 10a**: ba JSON `git mv` sang `backend/etl/data/`, khối §9 thành `backend/etl/wichart_source.py`, test tĩnh cấm mọi đường dẫn `docs/` trong code ngoài test (`backend/` + `database/`), `.dockerignore` §5.3 giữ nguyên. Hệ quả cho §8 (tài liệu sống): mọi link tới ba file JSON và câu "registry hardcode trong wichart.md §9" đổi theo — cùng lượt với code (Task 10a), không đợi Task 11.
