# Cấu hình theo trục bảo mật / least privilege — file-based secrets

## 1. Hình dạng

Nguyên tắc: `.env` chỉ chứa cấu hình KHÔNG bí mật + con trỏ tới file bí mật. Bí mật thật nằm trong file riêng (một file một bí mật) ở thư mục **ngoài repo** `../dlck-secrets/` (anh em với repo, cùng quy ước `INGESTER_LOG_DIR` mặc định `REPO_ROOT.parent/"dlck-runtime"` — `backend/ingester/config.py:30`). Ngoài repo = không cần `.gitignore` bảo vệ, loại hẳn nguy cơ `git add -A`/nén thư mục cuốn theo bí mật.

8 file bí mật (chủ dự án tự sinh, ghi tay một lần khi dựng máy — như điền `.env` hôm nay, chỉ tách nhiều file):

| Biến trỏ (`.env` native) | File bí mật | Ý nghĩa | Ai đọc |
|---|---|---|---|
| `DATA_DATABASE_URL_PASSWORD_FILE` / `POSTGRES_PASSWORD_FILE` | `pg_owner_password.txt` | Postgres superuser | `postgres` (init), `pg-migrate`, `pg-bootstrap-users` |
| `ETL_DATABASE_URL_PASSWORD_FILE` | `pg_etl_password.txt` | mật khẩu `etl_worker` | `etl`, `agent` (ghi sổ `ops.llm_call`), `pg-bootstrap-users` |
| `AGENT_DATABASE_URL_PASSWORD_FILE` | `pg_agent_password.txt` | mật khẩu `agent_reader` | `agent`, `pg-bootstrap-users` |
| `CLICKHOUSE_URL_PASSWORD_FILE` / `CLICKHOUSE_PASSWORD_FILE` | `ch_owner_password.txt` | ClickHouse `default` | `clickhouse` (init), `ch-migrate`, `ch-bootstrap-users`, `ch_backup` |
| `CLICKHOUSE_INGESTER_URL_PASSWORD_FILE` | `ch_ingester_password.txt` | mật khẩu `ingester_worker` | `ingester`, `ch-bootstrap-users` |
| *(chỉ bootstrap dùng)* | `ch_api_password.txt` | mật khẩu `api_reader` | `ch-bootstrap-users` — cấp sẵn, chưa ai dùng |
| `LLM_API_FILE` | `llm_api_key.txt` | khoá MiniMax | `etl` (news_classify), `agent` |
| `FRED_API_FILE` | `fred_api_key.txt` | khoá FRED | `etl` (fred_fetch) |

`REDIS_URL` không có mật khẩu hôm nay nên giữ nguyên plain var. `api` không đọc bí mật nào (walking skeleton, `backend/api/main.py` chỉ có `/healthz`) — không cấp file nào cho `api`.

**Một `.env` cho hai host:** mỗi DSN là một CHUỖI MẪU chứa placeholder `{PASSWORD}`, không chứa mật khẩu thật:
```
ETL_DATABASE_URL=postgresql+psycopg://etl_worker:{PASSWORD}@127.0.0.1:5432/dulieu
ETL_DATABASE_URL_PASSWORD_FILE=D:\...\dlck-secrets\pg_etl_password.txt
```
Native đọc file thẳng từ đĩa. Container KHÔNG sửa `.env` — compose override cả hai biến trong `environment:` của service, đúng cơ chế có sẵn cho `POSTGRES_HOST`/`REDIS_HOST` (`deploy/app/docker-compose.yml:8-10`, dù nay chưa code nào đọc hai biến đó):
```
environment:
  ETL_DATABASE_URL: postgresql+psycopg://etl_worker:{PASSWORD}@postgres:5432/dulieu
  ETL_DATABASE_URL_PASSWORD_FILE: /run/secrets/pg_etl_password
secrets: [pg_etl_password]
```
Compose mount `/run/secrets/pg_etl_password` từ CÙNG file — một nội dung, hai đường đọc, không hand-edit giữa hai lần chạy.

Hai hàm mới trong `backend/core/env.py`:
```python
def resolve_secret(name: str) -> str | None:   # <name>_FILE ưu tiên, fallback <name>
def resolve_dsn(name: str) -> str | None:      # thay {PASSWORD} bằng resolve_secret(f"{name}_PASSWORD"), url-encode
```
Không hàm nào ghi lại vào `os.environ` — chuỗi ráp xong chỉ sống trong biến cục bộ của lời gọi `create_engine`/`get_client`. **Không dòng code nào rẽ nhánh theo "đang trong container"** — cả hai môi trường gọi CHUNG `resolve_dsn`/`resolve_secret`; khác biệt chỉ ở giá trị env var do compose override, giống hệt `POSTGRES_HOST`.

## 2. Thay đổi từng file

| Đường dẫn | Sửa gì | Vì sao |
|---|---|---|
| `backend/core/env.py` | + `resolve_secret`, `resolve_dsn`, CLI nhỏ `python -m core.env resolve_dsn NAME` | dùng chung cho mọi consumer |
| `backend/core/llm/settings.py` | `from_env`: nhánh `env is None` gọi `resolve_secret("LLM_API")` | giữ khả năng test bằng Mapping giả |
| `backend/etl/fred_fetch.py` | `os.environ.get("FRED_API")` → `resolve_secret("FRED_API")` | key qua file |
| 10 file `backend/etl/{events,fundamentals,news,omo,price,refdata,screener,series,snapshot,wichart}_job.py` | `os.environ.get("ETL_DATABASE_URL")` → `resolve_dsn(...)` | 5 job mỏng (binance/fred/fx/lbma/yahoo) uỷ quyền `series_job`, không đụng |
| `backend/agent/db.py` | `_engine()`: `os.environ.get(var)` → `resolve_dsn(var)` | dùng chung cho `AGENT_DATABASE_URL` lẫn `ETL_DATABASE_URL` (`agent/db.py:1-11`) |
| `backend/ingester/config.py`, `backend/ingester/main.py:288` | `CLICKHOUSE_INGESTER_URL` qua `resolve_dsn`; `REDIS_URL` giữ nguyên | Redis không có mật khẩu để bảo vệ |
| `backend/core/ch_migrate.py` | `get_client()`: `os.environ["CLICKHOUSE_URL"]` → `resolve_dsn(...)` | owner cred, dùng lại bởi `ch_backup` |
| `backend/core/bootstrap_users.py` *(mới)* | script idempotent CREATE/ALTER USER, Postgres+ClickHouse | thay bước tay `database/README.md:108-112` |
| `deploy/resolve-and-exec.sh` *(mới)* | export DSN đã ráp rồi `exec "$@"`; tiền tố `command:` cho `pg-migrate` | `env.py` không import được `core.env` (`alembic.ini:2` không đặt `prepend_sys_path`, CWD=repo root ≠ `backend/`) |
| `deploy/infra/docker-compose.yml` | `postgres`/`clickhouse` dùng `*_PASSWORD_FILE`; + `secrets:` (8 mục); + 4 service one-shot `pg-migrate→pg-bootstrap-users`, `ch-migrate→ch-bootstrap-users` | role đã có (`0009`, `0001_roles.sql`), thiếu bước tạo login user tự động |
| `deploy/app/docker-compose.yml` | bỏ `env_file` chung; `api` không nhận secret; `etl` chỉ nhận 3 secret qua `environment:`+`secrets:` | `env_file: ../../.env` hôm nay cấp TOÀN BỘ file cho service không dùng tới |
| `.env.example` | 5 dòng DSN → mẫu `{PASSWORD}`; thêm 8 dòng `*_FILE` | tài liệu hình dạng mới |
| `database/README.md:65-71,108-112` | recipe native dùng CLI `core.env`; đánh dấu `CREATE USER` tay là đã tự động | tránh tài liệu nói ngược code (§1.7) |
| `database/clickhouse/create_users.sql.example` | ghi chú "nay do `bootstrap_users.py` sinh, giữ tham chiếu" | tránh hai nguồn sự thật |
| `scripts/stack.mjs` | `realtimeMisconfigured` nhận thêm `CLICKHOUSE_PASSWORD_FILE`; `dockerUp()` chèn bước chạy one-shot | guard cũ báo lỗi giả khi owner pass chuyển sang file |

## 3. Đường đi từng consumer

| Consumer | Host | User/password |
|---|---|---|
| 10 job etl (`python -m etl <job>`) | native `.env` (`127.0.0.1`) / container override `postgres` | `etl_worker` + `pg_etl_password.txt` qua `resolve_dsn` |
| 5 job mỏng (binance/fred/fx/lbma/yahoo) | uỷ quyền `series_job` | như trên |
| ingester | như trên, đích ClickHouse | `ingester_worker` + `ch_ingester_password.txt` |
| agent (native only, chưa có service compose) | `.env`/file trên đĩa, không qua Docker | `agent_reader` (đọc) + `etl_worker` (ghi `ops.llm_call`) + `llm_api_key` |
| alembic (`database/migrations/env.py`) | container `pg-migrate`, host=`postgres` | owner, DSN ráp bởi `resolve-and-exec.sh` trước khi exec — `env.py` không đổi |
| `tests/conftest.py` | native, `TEST_DATABASE_URL` | **giữ nguyên** — DSN owner thật trong `.env`, ngoài phạm vi trục này (máy dev một người — quyết định #1) |
| `core.ch_migrate`/`core.ch_backup` | container `ch-migrate`; backup định kỳ riêng (rủi ro #4) | owner + `ch_owner_password.txt` qua `resolve_dsn` trực tiếp (cùng package, không cần shell trick) |
| bootstrap 4 user login | `pg-bootstrap-users`/`ch-bootstrap-users`, host=service | owner (kết nối) + 2 file mật khẩu đích mỗi engine |

## 4. Rủi ro tự khai

1. **Độ phức tạp thật, không miễn phí**: ~15 file backend đổi 1-2 dòng, 2 file mới, 2 compose file viết lại, 8 file bí mật tạo tay ngoài `.env`. Cho dự án một người, đây là gánh bảo trì thêm so với "một `.env` phẳng" — giá thật của trục đã chọn.
2. **File secret của Compose không mã hoá tại chỗ** — chỉ là bind-mount thường; ai đọc được ổ đĩa host hoặc là root trong container vẫn đọc được y hệt một env var. Cái đạt được là tránh đúng 4 kênh đã nêu (inspect/ps/log/traceback), không phải mã hoá.
3. **`CLICKHOUSE_PASSWORD_FILE` mới xác nhận trên nhánh `master`** (đọc `docker/server/entrypoint.sh`), **chưa xác nhận đúng tag `26.3.22.7` đang ghim** (`deploy/infra/docker-compose.yml:38`). Nếu tag đó thiếu, service `clickhouse` phải lùi về plain env (Postgres thì chắc chắn hỗ trợ `POSTGRES_PASSWORD_FILE`).
4. **`core.ch_backup` phá một phần "owner chỉ ở bootstrap"**: dùng lại `ch_migrate.get_client()` (owner) cho backup CHẠY ĐỊNH KỲ, không chỉ một lần (`ch_backup.py:78-80`) — kế thừa kiến trúc app hiện có, không phải lỗi của cấu hình này nhưng phải nêu thật.
5. **Xoay vòng mật khẩu không tự động**: `CREATE USER IF NOT EXISTS` không cập nhật mật khẩu nếu user đã tồn tại; sửa file không tự áp dụng lại — cần `ALTER USER` tay hoặc mở rộng `bootstrap_users.py`.
6. **Chưa kiểm thật trên Windows**: bind-mount file đơn qua Docker Desktop/WSL2 — chỉ suy từ tài liệu Compose, chưa chạy thử trên máy dev; đúng điều kiện "đứng vững trên Windows" mà trục này đòi hỏi.

## 5. Điều kiện đảo ngược

1. Tag ClickHouse `26.3.22.7` xác nhận KHÔNG hỗ trợ `CLICKHOUSE_PASSWORD_FILE` → `clickhouse` là ngoại lệ dùng plain env, thu hẹp phạm vi thiết kế.
2. Thêm người/máy dev tham gia → ma sát "8 file tạo tay, không copy-paste một `.env.example` là xong" có thể vượt lợi ích cho team nhỏ.
3. Kiến trúc gộp 4 tiến trình (api/etl/ingester/agent) thành một → per-service secret scoping mất tác dụng, quay lại một secret set chung.
4. Dự án coi "owner cred sống cả trong cron backup" là vi phạm không chấp nhận được → phải đổi ARCHITECTURE app (role `dlck_backup` hẹp hơn) trước, không phải đổi cấu hình.
5. Thử thật trên Windows mà bind-mount file đơn từ `../dlck-secrets/` lỗi quyền/path → đổi sang mount cả thư mục, hoặc kết luận file-based không đứng vững trên Windows.

## 6. Ước lượng

- File production đụng: **~24-26** (15 file backend sửa 1-2 dòng, 2 file mới, 2 compose file viết lại, `.env.example`, `database/README.md`, `create_users.sql.example`, `scripts/stack.mjs`).
- Dòng ước lượng: **~450-550** — phần lớn ở 2 compose file (~90-120 dòng) và `bootstrap_users.py` (~120-150 dòng); còn lại 1-2 dòng/file.
- Không cần migration mới — role đã có sẵn (`0009`, `0001_roles.sql`); bootstrap chỉ tạo LOGIN USER, không DDL.
- Rollback: `git revert` commit này. Không cần rollback dữ liệu vì giá trị mật khẩu không đổi, chỉ đổi cách đọc — miễn KHÔNG rotate mật khẩu cùng lượt (nếu có, giữ `.env` cũ để lùi ngay).
