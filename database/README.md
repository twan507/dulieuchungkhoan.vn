# database — DDL · migrations · compose

**Stack đã chốt** *(2026-08-24, [ADR 0007](../docs/00-overview/decisions/0007-monorepo-layout-and-stack.md))*:

| Engine | Chứa gì |
|---|---|
| **PostgreSQL** | Dữ liệu REST: giá EOD, BCTC, sự kiện, vĩ mô, tin (tsvector + pgvector) |
| **ClickHouse** | Realtime: tick thô + sổ lệnh từ 5 topic BVSC; nến sinh bằng materialized view |

Redis đi kèm cho pub/sub SSE và leader lock của Ingester — nó là kênh phân phối, không phải kho.

Thiết kế chi tiết phần Postgres/REST ở [`docs/20-design/market-data-store.md`](../docs/20-design/market-data-store.md). Phần realtime (tick thô, sổ lệnh, nến `bar_1m`) đã có bản CHÍNH THỨC riêng cho ClickHouse — xem mục **Schema ClickHouse (`rt`)** dưới đây, không còn theo thiết kế TimescaleDB cũ trong `market-data-store.md` (tài liệu đó đã được đánh banner tương ứng).

## Trạng thái

Schema `postgres-data` đã dựng: **10 migration** Alembic (`0001` schemas/extensions … `0010` registry ingested_at), **37 test** seam chạy trên Postgres thật (`backend/tests/schema/test_sNN_*.py` — 9 file, không 1-1 với 10 migration: test seed `0003` gộp vào `test_s02_identity.py`, `test_s03_market_data.py` test migration `0004`; từ `test_s05_macro.py` trở đi NN khớp đúng số migration).

Spec: [`docs/90-records/plans/2026-08-25-postgres-data-schema/`](../docs/90-records/plans/2026-08-25-postgres-data-schema/) — `README.md` (mục tiêu G1–G5, quyết định xuyên suốt), `step-01`…`step-07` (thiết kế từng miền), `plan.md` (11 task TDD), `ledger.md` (nhật ký thực thi).

## Schema ClickHouse (`rt`)

**Trạng thái:** **2 migration** SQL thuần (`database/clickhouse/versions/0001_roles.sql` — role `dlck_ingester`/`dlck_api`, `0002_rt_schema.sql` — 5 bảng frame thô TTL 3 tháng + 2 bảng nến vĩnh viễn + materialized view), chạy bằng runner riêng `core.ch_migrate` (không dùng Alembic — ClickHouse không hỗ trợ transaction DDL kiểu Postgres). **29 test** seam trong `backend/tests/clickhouse/` (`test_t01_fixture.py` … `test_t06_backup.py`) — **cần Docker** vì mỗi phiên test dựng container ClickHouse ephemeral riêng (không dùng CH dev đang chạy).

Spec: [`docs/90-records/plans/2026-08-25-clickhouse-realtime-store/`](../docs/90-records/plans/2026-08-25-clickhouse-realtime-store/) — `spec.md` (quyết định xuyên suốt, checklist §13), `plan.md`, `ledger.md`.

Cách chạy (từ `backend/`, `PYTHONIOENCODING=utf-8`):

```bash
export CLICKHOUSE_URL="http://default:${CLICKHOUSE_PASSWORD}@127.0.0.1:8123"   # mẫu ở .env.example
uv run python -m core.ch_migrate upgrade   # hoặc: status
```

Test (dựng/huỷ container ClickHouse ephemeral, cần Docker chạy sẵn):

```bash
uv run pytest tests/clickhouse -v
```

Backup (script `core.ch_backup`, env `CLICKHOUSE_BACKUP_DIR` trỏ thư mục host ngoài Docker volume): dev chạy tay `uv run python -m core.ch_backup`; khi deploy Linux, đặt cron sau 15:30 (sau khi phiên đóng, tránh tranh I/O giờ giao dịch). `CLICKHOUSE_BACKUP_DIR` tương đối được giải theo `deploy/infra/` (cùng gốc với `docker-compose.yml`, cùng chuẩn compose dùng) — nên đặt đường dẫn tuyệt đối khi deploy thật.

> **Idempotency dựa trên tên file, không kiểm nội dung:** script coi một partition/ngày là "đã backup" nếu file `.zip` cùng tên đã tồn tại. File `.zip` hỏng do crash giữa chừng (ví dụ mất điện khi đang ghi) vẫn bị coi là đã backup và sẽ không được ghi lại — kiểm toàn vẹn định kỳ là việc vận hành, chưa tự động hoá.

> **Hai role trùng tên `dlck_api` — đừng nhầm hai kho:** Postgres có role `dlck_api` đọc 4 schema miền (`market`/`macro`/`asset`/`news`, xem mục Luật bên dưới); ClickHouse **cũng** có role `dlck_api` (migration `0001_roles.sql`) nhưng chỉ đọc schema `rt`. Hai role sống trên hai engine khác nhau, trùng tên có chủ đích (cùng vai trò "reader cho `api`"), không phải cấu hình chung.
>
> User login của ClickHouse tạo **per-môi-trường, ngoài migration**, theo mẫu [`database/clickhouse/create_users.sql.example`](clickhouse/create_users.sql.example) — cùng nguyên tắc với user login Postgres ở mục Luật.

## Cách chạy

Env (Git Bash, từ gốc repo; `.env` khai `POSTGRES_USER`/`POSTGRES_PASSWORD`/`POSTGRES_DB`):

```bash
set -a && . ./.env && set +a
export DATA_DATABASE_URL="postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@127.0.0.1:5432/${POSTGRES_DB}"
export TEST_DATABASE_URL="postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@127.0.0.1:5432/dulieu_test"
```

Migrate DB ở `DATA_DATABASE_URL`:

```bash
uv run --project backend alembic -c database/alembic.ini upgrade head
uv run --project backend alembic -c database/alembic.ini downgrade base   # rollback toàn phần
```

Test schema (tự tạo lại `dulieu_test` từ đầu qua `conftest.py`, không đụng DB ở `DATA_DATABASE_URL`):

```bash
cd backend && uv run pytest tests/schema -v
```

## Luật

- **Sửa DDL qua migration mới** — không sửa file trong `database/migrations/versions/` đã chạy, kể cả trên dev. Phát hiện sai thì viết migration kế tiếp để sửa, không quay lại sửa migration cũ.
- **Mọi SQL qualify đủ `schema.object`**, không dựa `search_path`. Bốn extension (`unaccent`, `pg_trgm`, `vector`, `fuzzystrmatch`) nằm trong schema `extensions`, không phải `public`: hàm bọc phải qualify (`extensions.unaccent(...)`), opclass viết `extensions.gin_trgm_ops`, operator so khớp mờ của `pg_trgm` viết `OPERATOR(extensions.%)` chứ không phải `%` trần — bẫy đã gặp thật khi viết migration `0007` (tìm kiếm tin theo tên mờ).
- **Role ứng dụng là `NOLOGIN`, tạo trong migration `0009`:** `dlck_etl` ghi 6 schema (`market`/`macro`/`asset`/`news`/`staging`/`ops`), `dlck_api` chỉ đọc 4 schema miền (`market`/`macro`/`asset`/`news`). User login thật tạo **per-môi-trường, ngoài migration**:
  ```sql
  CREATE USER etl_worker LOGIN PASSWORD '…' IN ROLE dlck_etl;
  ```
- ⚠️ downgrade 0003 xoá cả `market.industry_icb_map` (bản đồ ICB→ngành có thể gán tay) — trước khi downgrade qua 0003 trên DB có dữ liệu thật, backup bảng này.
