# Phương án P1 — dịch host ở lớp compose, không đụng code

**Trục tối ưu:** bán kính hỏng nhỏ nhất — ít file production đụng nhất, rollback bằng một `git revert`, không migration, không đổi hợp đồng đang có. Một phương án, không hybrid.

## 1. Hình dạng

**Nguyên lý:** `.env` giữ nguyên hình dạng native (URL đầy đủ, host `127.0.0.1`). Container không tự suy host khác từ `.env` — `deploy/app/docker-compose.yml` dịch host bằng `environment:` của Compose: override giá trị mà `env_file: ../../.env` đã bơm, CHỈ cho service container, dựng lại URL bằng `${VAR}` compose lấy từ CHÍNH `.env` gốc (`stack.mjs` đã truyền `--env-file .env` cho tầng app sẵn). Mở rộng cơ chế `${POSTGRES_PASSWORD:?...}` **đã dùng sẵn** ở `deploy/infra/docker-compose.yml` — không phải kỹ thuật mới.

**Biến `.env`** (9 dòng hiện có + 4 dòng mới):

| Biến | Nghĩa | Ai đọc |
|---|---|---|
| `ETL_DATABASE_URL` | Postgres, `etl_worker` (ghi 6 schema) | 11 job etl, `agent/db.py::ops_engine` |
| `AGENT_DATABASE_URL` | Postgres, `agent_reader` (đọc 4 schema) | `agent/db.py::read_engine` |
| `DATA_DATABASE_URL` | Postgres, owner | `database/migrations/env.py` |
| `TEST_DATABASE_URL` | Postgres, owner, DB `dulieu_test` | `tests/conftest.py` — chỉ native |
| `REDIS_URL` | Redis, không mật khẩu | `ingester` |
| `CLICKHOUSE_INGESTER_URL` | ClickHouse, `ingester_worker` | `ingester` (runtime + `assert_migrated`) |
| `CLICKHOUSE_URL` | ClickHouse, owner `default` | `core.ch_migrate`, `core.ch_backup` |
| `POSTGRES_USER/PASSWORD/DB`, `CLICKHOUSE_PASSWORD` | mảnh owner rời (đã có) | compose interpolation |
| **`ETL_WORKER_PASSWORD`** *(mới)* | mật khẩu `etl_worker`, trùng giá trị đã nhúng trong `ETL_DATABASE_URL` | compose + bootstrap |
| **`AGENT_READER_PASSWORD`** *(mới)* | nt cho `agent_reader` | nt |
| **`INGESTER_WORKER_PASSWORD`** *(mới)* | nt cho `ingester_worker` | nt |
| **`API_READER_PASSWORD`** *(mới)* | mật khẩu `api_reader` (CH) — chưa URL nào dùng, chỉ bootstrap cần | bootstrap |

Compose chỉ thay `${VAR}` nguyên khối, không bóc được password khỏi URL, nên 4 mảnh rời này bắt buộc để dựng URL container mà không sửa code. 3/4 **trùng lặp có chủ đích** với password đã nhúng trong URL native (chi phí §4.1).

**Ví dụ cơ chế** (service `etl`, đã có sẵn):

```yaml
etl:
  environment:
    ETL_DATABASE_URL: postgresql+psycopg://etl_worker:${ETL_WORKER_PASSWORD}@postgres:5432/${POSTGRES_DB:-dulieu}
```

`environment:` đè giá trị `env_file` đã bơm cho đúng service này; `${...}` compose giải ngay lúc parse, lấy từ `.env` gốc. Native (`uv run ...`) không qua lớp này — thấy nguyên `.env`.

**Rẽ nhánh "đang trong container" trong code:** không có, ở bất kỳ đâu — đã đọc `core/env.py`, `ingester/config.py`, `agent/db.py`, `core/ch_migrate.py`, `core/ch_backup.py`, `database/migrations/env.py`, `tests/conftest.py`, một job etl mẫu (`omo_job.py`): tất cả chỉ `os.environ.get/[...]`. Dịch host nằm ở YAML, đúng vai trò compose đã làm hôm nay.

## 2. Thay đổi từng file

| Đường dẫn | Sửa gì | Vì sao |
|---|---|---|
| `.env.example` | +4 dòng password rời (bảng trên) | Nguồn cho compose dựng URL container + cho bootstrap đọc |
| `deploy/app/docker-compose.yml` | (a) thêm `environment:` dựng URL cho `etl` + service **mới** `ingester`, `agent`, `migrate-postgres`, `migrate-clickhouse`, `bootstrap-users` — 3 service sau gắn `profiles: ["migrate"]`, one-shot, không tự chạy khi `up -d` (như `clickhouse` dùng `profiles: ["realtime"]`); (b) `migrate-postgres` mount `../../database:/app/database:ro`, `migrate-clickhouse` mount `../../database:/database:ro` — khác đích vì alembic giải đường dẫn tương đối theo CWD (`/app`), còn `ch_migrate.REPO_ROOT` = `parents[2]` của `__file__` = `/` trong image này | Compose là lớp duy nhất biết đang dựng container gì; `database/` ngoài build context (`backend/`) nên phải mount, không sửa Dockerfile chung |
| `backend/core/bootstrap_users.py` *(MỚI)* | 2 hàm: tạo `etl_worker`/`agent_reader` (Postgres, khuôn `DO $$ IF NOT EXISTS` y hệt migration `0009_roles_grants.py`) và `ingester_worker`/`api_reader` (ClickHouse, y hệt `create_users.sql.example`), password tham số hoá từ 4 biến mới; đọc owner qua `DATA_DATABASE_URL`/`CLICKHOUSE_URL` (tên biến có sẵn) | Quyết định #4: bootstrap tự động, tái dùng nguyên SQL đã có, chỉ đổi `'CHANGE-ME'` thành biến môi trường. Đặt ở `backend/core/` để khỏi cần mount thêm — image đã `COPY . .` nguyên `backend/` |
| `database/README.md` | +3 lệnh `docker compose run --rm` (bootstrap-users, migrate-postgres, migrate-clickhouse) vào mục "Cách chạy", nêu thứ tự bắt buộc | §1.6 CLAUDE.md: nơi sở hữu "Cách chạy" phải cập nhật cùng lượt *(chỉ ghi nhận trong bảng — nhiệm vụ này không cho sửa file thật)* |

**Không đụng:** `deploy/backend.Dockerfile`, `deploy/infra/docker-compose.yml`, `scripts/stack.mjs`, **0 dòng code Python production** — đã xác nhận `alembic`/`psycopg[binary]`/`clickhouse-connect`/`sqlalchemy` đều ở `dependencies` chính (không `dev`) của `backend/pyproject.toml`, nên image hiện có đủ cho cả 3 service mới.

## 3. Đường đi từng consumer

| Consumer | Native | Container |
|---|---|---|
| 11 job etl | `.env` trực tiếp (`etl_worker`, `127.0.0.1`) | service `etl`: override → `etl_worker:${ETL_WORKER_PASSWORD}@postgres` |
| `ingester` | `.env` trực tiếp | service **mới** `ingester`: override `CLICKHOUSE_INGESTER_URL`→`@clickhouse`, `REDIS_URL`→`@redis` — vá đúng lỗ ACCESS_DENIED của `assert_migrated` (§3.5 ca 3): nay thấy đúng host thay vì `127.0.0.1` không tồn tại trong container |
| `agent` | `.env` trực tiếp | service **mới** `agent` (REPL — không `restart:`, chạy qua `docker compose run --rm -it agent`): override `AGENT_DATABASE_URL`, `ETL_DATABASE_URL` |
| alembic (`migrations/env.py`) | operator tự `export DATA_DATABASE_URL` theo `database/README.md`, không đổi | service **mới** `migrate-postgres` (profile `migrate`, one-shot): set thẳng `DATA_DATABASE_URL=...${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres...`, mount `database/` vào `/app/database` |
| `tests/conftest.py` | `.env` trực tiếp qua `load_dotenv()` trong conftest | không chạy trong container (quyết định #1, `tests/` không nằm trong image) |
| `core.ch_migrate` | `.env` trực tiếp (`CLICKHOUSE_URL`, owner) | service **mới** `migrate-clickhouse` override `CLICKHOUSE_URL`→`@clickhouse`, mount `database/` vào `/database` |
| `core.ch_backup` | `.env` trực tiếp, chạy tay/cron | ngoài phạm vi quyết định #2 (chỉ nêu ingester + migration hai kho) — để nguyên native |
| bootstrap 4 user login | không có đường native trong quy trình thường (script tự chạy được native nếu trỏ owner URL vào `127.0.0.1`) | service **mới** `bootstrap-users` (profile `migrate`, one-shot): `DATA_DATABASE_URL` + `CLICKHOUSE_URL` (owner, host container) qua compose, cộng 4 biến password mới |

## 4. Rủi ro tự khai

1. **Password sống hai dạng trong `.env`** — nhúng trong URL (native) và rời (`_PASSWORD`, container). Đổi một chỗ quên chỗ kia ⇒ hai chế độ chạy lặng lẽ lệch nhau, chỉ lộ khi auth fail đúng lúc dùng chế độ bị bỏ quên.
2. **Giả định đường dẫn tương đối của alembic chưa chạy thật** — dựa trên `script_location` giải theo CWD (bằng chứng gián tiếp: `conftest.py` tự `os.chdir(REPO_ROOT)` trước khi gọi alembic), nhưng chưa tự chạy `migrate-postgres` để kiểm mount `/app/database` khớp. Đúng CLAUDE.md §3.5: phải chạy tay dưới điều kiện thật trước khi tin — nhiệm vụ này chỉ cho đọc, cần kiểm trước khi triển khai.
3. **`environment:` lặp lại ở nhiều service** (`etl` và `agent` cùng cần `ETL_DATABASE_URL`) — không dùng YAML anchor, giữ style phẳng đã có (đã lặp `POSTGRES_HOST`/`REDIS_HOST` ở `api`/`etl`), nên đổi một biến sau này phải sửa N chỗ trong CÙNG một file.
4. **`bootstrap_users.py` dựng SQL bằng f-string nhúng password** — an toàn vì `.env` do dự án tự kiểm soát, cùng kiểu f-string sẵn có ở `ch_backup.py`, nhưng vẫn là điểm reviewer bảo mật sẽ gắn cờ nếu đọc rời ngữ cảnh.
5. **Cái giá dài hạn bị hy sinh có chủ đích:** không "settings" tập trung kiểm kiểu một chỗ — mỗi consumer tự `os.environ.get`/`[...]` riêng. Gọn/nhất quán hơn cần tập trung hoá — sửa cả 11 job + ingester + agent, đối lập trực tiếp trục "ít file nhất" đang yêu cầu.

## 5. Điều kiện đảo ngược

- Thêm ≥2 consumer mới cần override tương tự (vd `api` bắt đầu đọc ClickHouse) khiến lặp `environment:` gây lỗi thật ít nhất một lần ⇒ nên gộp bằng YAML anchor hoặc file cấu hình container tập trung.
- Alembic thực ra giải `script_location` theo thư mục chứa ini (`%(here)s`) chứ không theo CWD ⇒ mount cho `migrate-postgres` sai đích, phải đổi cách.
- Chính sách bảo mật cấm lưu cùng một mật khẩu ở hai dạng biến trong cùng file ⇒ phải bỏ 4 biến rời, tìm cách khác tách password khỏi URL (cần sửa code — không còn "0 dòng production").
- VPS thật dùng tên service khác `postgres`/`redis`/`clickhouse` ⇒ giá trị hardcode trong `environment:` sai theo, phải tham số hoá thêm tên host.

## 6. Ước lượng

- **File production đụng:** 2 sửa (`.env.example`, `deploy/app/docker-compose.yml`) + 1 file mới (`backend/core/bootstrap_users.py`) + 1 doc (`database/README.md`). **0 file code Python đang chạy bị sửa.**
- **Số dòng ước lượng:** `.env.example` +~10; `docker-compose.yml` (app) từ 31 dòng lên ~100–120; `bootstrap_users.py` ~70–90 dòng mới. Tổng **~180–220 dòng**, không dòng nào nằm trên đường chạy hiện có của `api`/`etl`.
- **Migration:** không — `CREATE USER` cố tình đứng ngoài alembic/`ch_migrate`, đúng quy ước "per-môi-trường, ngoài migration" đã ghi ở `database/README.md`.
- **Rollback:** một `git revert` của commit thêm 3 file trên — xoá sạch service/override/script mới; `api`/`etl` không đổi dòng nào ngoài 2 dòng `environment:` mới ở `etl`. `.env` thật (không tracked, không bị revert) còn sót 4 dòng password thừa — vô hại vì không còn gì đọc, dọn tay sau nếu muốn.
