# database — DDL · migrations · compose

**Stack đã chốt** *(2026-08-24, [ADR 0007](../docs/00-overview/decisions/0007-monorepo-layout-and-stack.md))*:

| Engine | Chứa gì |
|---|---|
| **PostgreSQL** | Dữ liệu REST: giá EOD, BCTC, sự kiện, vĩ mô, tin (tsvector + pgvector) |
| **ClickHouse** | Realtime: tick thô + sổ lệnh từ 5 topic BVSC; nến sinh bằng materialized view |

Redis đi kèm cho pub/sub SSE và leader lock của Ingester — nó là kênh phân phối, không phải kho.

Thiết kế chi tiết phần Postgres/REST ở [`docs/20-design/market-data-store.md`](../docs/20-design/market-data-store.md). Phần realtime (tick thô, sổ lệnh, nến `bar_1m`) đã có bản CHÍNH THỨC riêng cho ClickHouse — xem mục **Schema ClickHouse (`rt`)** dưới đây, không còn theo thiết kế TimescaleDB cũ trong `market-data-store.md` (tài liệu đó đã được đánh banner tương ứng).

## Trạng thái

**Dữ liệu thật (2026-08-26 đêm, ngành cập nhật 2026-08-28):** 5 bảng tham chiếu đã nạp qua job `etl refdata` — `market.security` 2.015 · `market.issuer` 1.550 · `security_external_id` 2.014 · `issuer_external_id` 1.550 · `icb_industry` 176. Ngành đã nạp qua migration `0013`: `market.industry_icb_map` **55 dòng** (lớp 1, máy gán) · `market.issuer_industry_override` **161 dòng** (lớp 2, tay gán). Nghiệm thu trên DB thật dưới role `dlck_etl`: **1.526/1.550 issuer có ngành**, 24 quỹ/ETF không có ngành theo đúng thiết kế *(hồ sơ: [ledger](../docs/90-records/plans/2026-08-27-industry-two-layer-mapping/ledger.md))*.

Schema `postgres-data` đã dựng: **13 migration** Alembic (`0001` schemas/extensions … `0010` registry ingested_at · `0011` đổi 6 code + 7 tên ngành · `0012` bảng `market.issuer_industry_override` + view `market.v_issuer_industry` · `0013` seed ngành hai lớp), **49 test** seam chạy trên Postgres thật (`backend/tests/schema/test_sNN_*.py` — 10 file, không 1-1 với 13 migration: test seed `0003` gộp vào `test_s02_identity.py`, `test_s03_market_data.py` test migration `0004`; từ `test_s05_macro.py` trở đi NN khớp đúng số migration, kể cả `test_s10_registry_ts.py` cho `0010`; `test_s11_industry_override.py` phủ cả `0012` lẫn nội dung seed `0013`).

**Đọc ngành qua view, không đọc thẳng cột:** `market.issuer.industry_id` (lớp 1, máy — ETL ghi đè mỗi lượt) và `market.issuer_industry_override` (lớp 2, tay — `dlck_etl` đã bị `REVOKE` cả đọc lẫn ghi trên bảng này ở migration `0012`) không phải là nguồn đọc cuối. Đường đọc duy nhất là view `market.v_issuer_industry` = `COALESCE(override.industry_id, issuer.industry_id)` kèm cột `source` ∈ `manual` | `icb` | `NULL`.

Spec: [`docs/90-records/plans/2026-08-25-postgres-data-schema/`](../docs/90-records/plans/2026-08-25-postgres-data-schema/) — `README.md` (mục tiêu G1–G5, quyết định xuyên suốt), `step-01`…`step-07` (thiết kế từng miền), `plan.md` (11 task TDD), `ledger.md` (nhật ký thực thi).

## Schema ClickHouse (`rt`)

**Trạng thái:** **2 migration** SQL thuần (`database/clickhouse/versions/0001_roles.sql` — role `dlck_ingester`/`dlck_api`, `0002_rt_schema.sql` — 5 bảng frame thô TTL 3 tháng + 2 bảng nến vĩnh viễn + materialized view), chạy bằng runner riêng `core.ch_migrate` (không dùng Alembic — ClickHouse không hỗ trợ transaction DDL kiểu Postgres). **35 test** seam trong `backend/tests/clickhouse/` (`test_t01_fixture.py` … `test_t06_backup.py`) *(đếm 2026-08-26 tối; +6 so với mốc dựng schema — lát cắt ingester và vòng review mở gate bổ sung, trong đó có bộ test chạy `assert_migrated` dưới đúng role `dlck_ingester`)* — **cần Docker** vì mỗi phiên test dựng container ClickHouse ephemeral riêng (không dùng CH dev đang chạy).

Spec: [`docs/90-records/plans/2026-08-25-clickhouse-realtime-store/`](../docs/90-records/plans/2026-08-25-clickhouse-realtime-store/) — `spec.md` (quyết định xuyên suốt, checklist §13), `plan.md`, `ledger.md`.

> **Dung lượng — số ĐO THẬT** *(2026-08-26, nạp 2.316.573 record của một phiên chiều qua đúng đường ghi production: [hồ sơ đo §10](../docs/90-records/surveys/2026-08-26-bvsc-realtime-session/README.md))*: 5 bảng frame thô **~91 MiB/ngày** ⇒ TTL 3 tháng ≈ **6–8 GiB**; hai bảng nến **~0,5 GiB/năm**. Byte nén/dòng: `quote` 14,8 · `trade` 29,3 · `snapshot_delta` 36,1 · `index_delta` 48,5 · `pt_match` 23,5 · `bar_1m` 53,7.
>
> ⚠️ **Đừng dùng con số byte/dòng trong spec §10** — chúng đo trên dữ liệu tổng hợp lặp lại nên nén giả tạo (`snapshot_delta` ghi 5 B/dòng, thật là 36 B — lệch 7×). Ngược lại spec ước lượng nến cao hơn thực tế 5–13× (thật ~37–41k nến/ngày, không phải 200–540k). Hai sai số ngược chiều nên tổng vẫn nằm trong dải cũ, nhưng từng con số thì không dùng lại được.

Cách chạy (từ `backend/`, `PYTHONIOENCODING=utf-8`):

```bash
export CLICKHOUSE_URL="http://default:${CLICKHOUSE_PASSWORD}@127.0.0.1:8123"   # mẫu ở .env.example
uv run python -m core.ch_migrate upgrade   # hoặc: status
```

Test (dựng/huỷ container ClickHouse ephemeral, cần Docker chạy sẵn):

```bash
uv run pytest tests/clickhouse -v
```

Backup (script `core.ch_backup`, env `CLICKHOUSE_BACKUP_DIR` trỏ thư mục host ngoài Docker volume): dev chạy tay `uv run python -m core.ch_backup`; khi deploy Linux, đặt cron sau 15:30 (sau khi phiên đóng, tránh tranh I/O giờ giao dịch).

> ✅ **Đích backup khi lên VPS — chốt 2026-08-26 (chủ dự án): Cloudflare R2**, không giữ nhiều bản trên đĩa máy chủ. Lý do: VPS đích ~50 GB, mà chính sách "7 bản nến + 1× cửa sổ frame" giữ tại chỗ sẽ chiếm ~10–12 GB năm 1 và **~17–19 GB năm 3 ⇒ vượt 50 GB** khi cộng với dữ liệu sống ([số đo](../docs/90-records/surveys/2026-08-26-bvsc-realtime-session/README.md) §10).
>
> Cách làm: R2 nói giao thức S3 và ClickHouse `BACKUP TO Disk(...)` cấu hình được disk kiểu S3 ⇒ **chỉ thêm một khối XML trong `config.d/`**, không sửa `core.ch_backup`. Gói miễn phí R2: **10 GB-tháng + 1 triệu ghi + 10 triệu đọc, băng thông tải ra miễn phí** *(tra 2026-08-26)*; vượt thì $0,015/GB-tháng — mức dùng dự kiến 12–14 GB năm 1 ⇒ **dưới 2.000 đ/tháng**. Giữ **1 bản nến gần nhất tại máy** để khôi phục nhanh, phần còn lại đẩy R2.
>
> ⚠️ Khi dựng: nghiệm thu bằng **khôi phục thật** (restore vào database tạm rồi đối chiếu số dòng), không phải bằng "đã upload xong" — luật [CLAUDE.md §3.5](../CLAUDE.md). `CLICKHOUSE_BACKUP_DIR` tương đối được giải theo `deploy/infra/` (cùng gốc với `docker-compose.yml`, cùng chuẩn compose dùng) — nên đặt đường dẫn tuyệt đối khi deploy thật.

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
- ⚠️ **`alembic downgrade <revision>` = revision ĐÍCH, chạy `downgrade()` của migration NGAY SAU revision đó** — nói tắt "downgrade qua X" dễ khiến người đọc lẫn giữa "tới X" và "của X". Hai ca phá dữ liệu ngành thật, nêu rõ từng vế:
  - `alembic downgrade 0002` (tới revision `0002`) chạy `downgrade()` của `0003` → **`DELETE`** sạch `market.industry_icb_map` (bản đồ ICB→ngành lớp 1). Backup bảng này trước khi chạy lệnh này trên DB có dữ liệu thật.
  - `alembic downgrade 0011` (tới revision `0011`) chạy `downgrade()` của `0012` → **`DROP TABLE`** hẳn `market.issuer_industry_override` (161 dòng gán tay lớp 2) — mất luôn cả bảng, không chỉ mất dữ liệu. Backup bảng này trước khi chạy lệnh này trên DB có dữ liệu thật.

  **Không phải cùng lệnh với bước 3 của mục Bootstrap DB mới ngay dưới đây** — bước 3 chạy `alembic downgrade 0012` (tới revision `0012`, chỉ lùi qua `0013`, không đụng `0012`): chạy `downgrade()` của `0013`, chỉ `DELETE` rows do `0013` seed, KHÔNG `DROP` bảng nào — an toàn hơn nhiều so với hai ca DROP/DELETE ở trên.
- **Bootstrap DB mới — thứ tự bắt buộc, không được đảo:**
  1. `uv run --project backend alembic -c database/alembic.ini upgrade head`
  2. Chạy `etl refdata` một lượt để nạp danh bạ doanh nghiệp (`market.security`, `market.issuer`).
  3. Seed lại lớp 2: `uv run --project backend alembic -c database/alembic.ini downgrade 0012` rồi `uv run --project backend alembic -c database/alembic.ini upgrade head`.
  4. Kiểm: `select count(*) from market.issuer_industry_override` phải ra **161**.

  Vì sao cần bước 3: migration `0013` seed lớp 2 (`market.issuer_industry_override`) bằng cách phân giải **ticker → `issuer_id` qua `market.security`**. Trên DB dựng mới, `market.security` còn rỗng khi `0013` chạy ở bước 1 ⇒ nạp **0 dòng override, không exception** (câu `RAISE NOTICE` báo số dòng khớp cũng không hiện ra vì `alembic` không in `NOTICE`). Job `etl refdata` sau đó vẫn báo `issuers_without_industry` y hệt trạng thái khoẻ mạnh — **không có gì báo động** — trong khi toàn bộ 161 doanh nghiệp lẽ ra được gán tay lại rơi về gán máy (lớp 1), có thể sai ngành hoặc vi phạm luật BCTC.

  Đường `downgrade 0012` → `upgrade head` ở bước 3 an toàn để lặp lại — nó **chỉ** chạm `0013` (đích `0012` giữ nguyên `0012` đã áp dụng, không đụng DDL `CREATE TABLE`/`CREATE VIEW` của `0012`): `downgrade()` của `0013` `DELETE` sạch hai bảng seed (`market.industry_icb_map`, `market.issuer_industry_override`) trước; `upgrade()` của `0013` nạp lại — câu seed lớp 2 dùng `ON CONFLICT (issuer_id) DO NOTHING`, còn câu seed lớp 1 KHÔNG có `ON CONFLICT` nhưng vẫn an toàn vì bảng vừa bị `DELETE` sạch ngay trước đó nên không có gì để trùng.
