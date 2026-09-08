# P2 — `.env` nguyên tố + một hàm ráp duy nhất

Trục: **một sự thật một chủ**. `.env` chỉ khai NGUYÊN TỐ (host, port, tên DB, user, password) — không khai URL ghép sẵn. Một hàm duy nhất trong `core/env.py` ráp nguyên tố thành 7 chuỗi kết nối mà code đang đọc; mọi consumer giữ nguyên tên biến, không đổi dòng đọc-env nào.

## 1. Hình dạng

### Nguyên tố trong `.env` (thay 7 URL ghép sẵn hôm nay)

| Biến | Nghĩa | Ai đọc |
|---|---|---|
| `POSTGRES_HOST/_PORT` | host/cổng Postgres | hàm ráp (đã có, hôm nay chưa ai đọc) |
| `POSTGRES_DB` | DB owner | hàm ráp, compose infra, bootstrap |
| `POSTGRES_TEST_DB` *(mới, mặc định `dulieu_test`)* | DB test | hàm ráp (thay literal viết tay) |
| `POSTGRES_USER/_PASSWORD` | owner/admin | hàm ráp, compose infra, bootstrap |
| `ETL_USER/_PASSWORD` *(mới)* | login `etl_worker`, role `dlck_etl` | hàm ráp, bootstrap |
| `AGENT_USER/_PASSWORD` *(mới)* | login `agent_reader`, role `dlck_api` | hàm ráp, bootstrap |
| `REDIS_HOST/_PORT` | host/cổng Redis | hàm ráp |
| `REDIS_DB` *(mới, mặc định `0`)* | index Redis | hàm ráp (thay hậu tố `/0` viết tay) |
| `CLICKHOUSE_HOST/_PORT` *(mới)* | host/cổng ClickHouse | hàm ráp |
| `CLICKHOUSE_PASSWORD` | mật khẩu owner `default` (user cố định, không tham số hoá — §4) | hàm ráp, compose infra, bootstrap |
| `CLICKHOUSE_INGESTER_USER/_PASSWORD` *(mới)* | login `ingester_worker`, role `dlck_ingester` | hàm ráp, bootstrap |
| `CLICKHOUSE_API_USER/_PASSWORD` *(mới)* | login `api_reader`, role `dlck_api` — chưa ai tiêu thụ URL | bootstrap |
| `CLICKHOUSE_BACKUP_DIR`, `INGESTER_*_DIR`, `APP_ENV`, `LOG_LEVEL`, `LLM_API`, `FRED_API`… | ngoài trục, không đổi | như hiện tại |

**Xoá khỏi `.env`** (thành giá trị tính ra): `DATA_DATABASE_URL`, `TEST_DATABASE_URL`, `ETL_DATABASE_URL`, `AGENT_DATABASE_URL`, `CLICKHOUSE_URL`, `CLICKHOUSE_INGESTER_URL`, `REDIS_URL`.

### Cơ chế ráp — không rẽ nhánh theo container

`core/env.py` thêm `_compose_urls()`, gọi ở **cuối** `load_dotenv()`, chạy vô điều kiện kể cả khi không có file `.env` (container). Hàm đọc nguyên tố sẵn trong `os.environ` và `setdefault` từng URL — biến đã set trước (test monkeypatch, export tay) không bị đè.

```
ETL_DATABASE_URL  = f"postgresql+psycopg://{ETL_USER}:{ETL_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
TEST_DATABASE_URL = tương tự, user=owner, db=POSTGRES_TEST_DB
CLICKHOUSE_URL    = f"http://default:{CLICKHOUSE_PASSWORD}@{CLICKHOUSE_HOST}:{CLICKHOUSE_PORT}"
REDIS_URL         = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
```

Native vs container **không phải if/else trong code** — cùng một hàm, khác giá trị. `.env` ghi `127.0.0.1` (native); compose tầng `app` ghi đè bằng `environment:` (`POSTGRES_HOST: postgres`, `REDIS_HOST: redis`, `CLICKHOUSE_HOST: clickhouse`) — cơ chế đã có sẵn cho hai biến đầu hôm nay (nay mới có tác dụng, vì trước không ai đọc `POSTGRES_HOST`). `environment:` compose luôn thắng `env_file:` cùng khoá — quy tắc của Docker Compose, không phải tôi đặt ra. Đã đọc cả 4 tiến trình: không có biến `IN_DOCKER`, không có nhánh nào hỏi "đang trong container?".

## 2. Thay đổi từng file

| Đường dẫn | Sửa gì | Vì sao |
|---|---|---|
| `backend/core/env.py` | Thêm `_compose_urls()` (~45 dòng); `load_dotenv()` gọi thêm 1 dòng | Chủ duy nhất của việc ráp |
| `.env.example` | 7 URL ghép → ~21 nguyên tố | Khớp hình dạng mới |
| `.env` thật | Chủ dự án tự cập nhật | Tôi bị cấm đọc/sửa |
| `backend/tests/conftest.py` | `admin_url` bỏ literal `"dulieu"`, đọc `POSTGRES_DB` | "dulieu" đang là chủ thứ hai ẩn của tên DB |
| `database/migrations/env.py` | Thêm `from core.env import load_dotenv; load_dotenv()` | Alembic tự đủ, bỏ export tay trong README |
| `backend/core/ch_migrate.py` | Thêm `load_dotenv()` đầu `main()` | Đồng bộ với mọi consumer khác |
| `backend/core/ch_backup.py` | nt | nt |
| `backend/core/bootstrap_users.py` *(mới)* | Script tạo/đồng bộ 4 user login, idempotent | Quyết định #4 |
| `deploy/backend.Dockerfile` | Build context lên gốc repo; `COPY` giữ đúng độ sâu (`backend/…`, `database/…` dưới `/app`) | Alembic cần thấy `database/`; sửa luôn `REPO_ROOT` tính ra `/` trong container hôm nay |
| `deploy/app/docker-compose.yml` | `context: ../..`; thêm service `migrate-pg`, `migrate-ch`, `bootstrap-users` (`restart: "no"`, `depends_on: service_completed_successfully`), thêm service `ingester`; `api`/`etl`/`ingester` thêm `CLICKHOUSE_HOST` vào `environment:` | Route đủ tiến trình còn thiếu vào cùng hình dạng |
| `.dockerignore` gốc *(mới)* | Gộp nội dung bản cũ trong `backend/` | Docker đọc `.dockerignore` tại context, nay là gốc |
| `database/README.md` | Bỏ 2 dòng `CREATE USER` tay, trỏ `core.bootstrap_users`; bỏ export tay `CLICKHOUSE_URL` | Tránh hai chủ cho cùng việc |
| `database/clickhouse/create_users.sql.example` | Xoá | Bootstrap thay thế |

## 3. Đường đi từng consumer

| Consumer | Đọc gì | Không đổi |
|---|---|---|
| 10 job `etl/*_job.py` (grep: events/fundamentals/news/omo/price/refdata/screener/series/snapshot/wichart) | `ETL_DATABASE_URL` — nay tính từ `ETL_USER/_PASSWORD` + `POSTGRES_HOST/_PORT/_DB` | Dòng đọc, thông điệp lỗi, exit code |
| `ingester/config.py` | `CLICKHOUSE_INGESTER_URL` (từ `CLICKHOUSE_INGESTER_USER/_PASSWORD` + host/port), `REDIS_URL` | Logic thư mục runtime, exit 2 |
| `agent/db.py` | `AGENT_DATABASE_URL` (từ `AGENT_USER/_PASSWORD`) cho đọc; `ETL_DATABASE_URL` cho ghi sổ ops (dùng lại, cố ý) | `assert_read_only()` |
| `database/migrations/env.py` | `DATA_DATABASE_URL` (owner + `POSTGRES_DB`) | Logic migration |
| `tests/conftest.py` | `TEST_DATABASE_URL` (owner + `POSTGRES_TEST_DB`); `admin_url` suy từ `POSTGRES_DB` | Fixture chính, container CH ephemeral |
| `core.ch_migrate` | `CLICKHOUSE_URL` (owner `default` + `CLICKHOUSE_PASSWORD` + host/port) | `upgrade`/`status`/`assert_migrated` |
| `core.ch_backup` | `CLICKHOUSE_URL` + `CLICKHOUSE_BACKUP_DIR` | Logic prune/backup |
| `core.bootstrap_users` *(mới)* | Nối Postgres bằng `DATA_DATABASE_URL` (owner) → ghi `ETL_USER/_PASSWORD` (role `dlck_etl`), `AGENT_USER/_PASSWORD` (role `dlck_api`). Nối ClickHouse bằng `CLICKHOUSE_URL` (owner) → ghi `CLICKHOUSE_INGESTER_USER/_PASSWORD` (role `dlck_ingester`), `CLICKHOUSE_API_USER/_PASSWORD` (role `dlck_api`) | `CREATE USER IF NOT EXISTS` + `ALTER … PASSWORD` mỗi lần chạy; đòi role đã tồn tại (migration `0009`/`0001_roles.sql`), sai thì thoát lỗi |

## 4. Rủi ro tự khai

1. **Đọc khó hơn, `.env` dài hơn.** Giá trực tiếp của trục: 7 dòng URL thấy ngay host/db → ~21 nguyên tố, phải ráp trong đầu mới ra URL thật. Đánh đổi có chủ đích.
2. **Một hàm ráp sai hỏng đồng loạt.** Bug trong `_compose_urls()` (đảo `user`/`password`, sai tên port) lan ra cả 7 URL, cả 4 tiến trình cùng lúc — trước đây một dòng `.env` sai chỉ hỏng một biến. Giảm nhẹ bằng test đơn vị cho riêng hàm ráp, nhưng rủi ro tập trung là thật.
3. **Bootstrap phải luôn `ALTER PASSWORD`, không chỉ tạo lần đầu.** Nếu chỉ `CREATE IF NOT EXISTS`, đổi mật khẩu trong `.env` sau này không phản ánh xuống DB — `.env` hết là nguồn thật. Chọn luôn chạy `ALTER` mỗi lần bootstrap chạy: an toàn, nhưng mỗi `docker compose up` là một lượt ghi thật lên DB; restart riêng lẻ `api` không tự chạy lại bootstrap (`restart: "no"`).
4. **Mở rộng build context Docker — bán kính hỏng rộng hơn một biến.** Để alembic chạy trong container, `database/` phải vào image, buộc đổi context/`COPY` dùng chung cho MỌI service kể cả `api` production. Tiện thể lộ lỗi có sẵn từ trước (không do phương án này): `REPO_ROOT` tính ra `/` trong container hôm nay, lệch 1 cấp so với native. Cần build + `docker run` thật để kiểm, không chỉ đọc trạng thái.

## 5. Điều kiện đảo ngược

- Một tiến trình cần host Postgres/ClickHouse khác các tiến trình còn lại trong cùng container (không chỉ khác native/container) → một biến `*_HOST` chung không đủ, phải tách theo consumer.
- Hạ tầng chuyển sang nhiều host/replica/SSL phức tạp → f-string `user:pass@host:port/db` không biểu diễn nổi, cần cấu trúc khác.
- Nhiều consumer không đọc `os.environ` chuẩn (binary ngoài chỉ nhận flag dòng lệnh) → cần lớp sinh file cấu hình tường minh thay vì chỉ set env.
- Mở rộng build context đụng ràng buộc hạ tầng chưa biết (CI ngoài giả định context là `backend/`) → tách Dockerfile/image riêng cho migrate.

## 6. Ước lượng

- **File đụng:** 9 sửa (`core/env.py`, `tests/conftest.py`, `database/migrations/env.py`, `core/ch_migrate.py`, `core/ch_backup.py`, `deploy/backend.Dockerfile`, `deploy/app/docker-compose.yml`, `database/README.md`, `.env.example`) + 2 mới (`core/bootstrap_users.py`, `.dockerignore` gốc) + 1 xoá (`create_users.sql.example`) ≈ **12 file**.
- **Dòng ước lượng:** ~45 (`core/env.py`) + ~80 (`bootstrap_users.py`) + ~70 (compose YAML) + ~10 (Dockerfile) + vài dòng mỗi file còn lại ⇒ **~230–260 dòng ròng**, chưa tính `.env` thật.
- **Không cần migration DB mới** — không đổi schema; tạo user login vốn đã "ngoài migration", chỉ đổi từ tay sang script.
- **Rollback:** `git revert` (thuần cấu hình/script, không đụng schema). Ngoại lệ: đã chạy `bootstrap_users` trên môi trường thật thì revert code không tự xoá/đổi lại user trên DB — cần `DROP USER`/đổi mật khẩu tay, ghi rõ trong runbook.
