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

Schema `postgres-data` đã dựng: **21 migration** Alembic (`0001` schemas/extensions … `0010` registry ingested_at · `0011` đổi 6 code + 7 tên ngành · `0012` bảng `market.issuer_industry_override` + view `market.v_issuer_industry` · `0013` seed ngành hai lớp · `0014` cột dấu `security.directory_absent_since` cho luật huỷ niêm yết · `0015` bỏ hai kind chấm điểm khỏi `snapshot_daily` · `0016` bảng sổ kiểm `ops.snapshot_check` + domain `market.snapshot` · `0017` `financial_report_file.source_id` UNIQUE thay UNIQUE `source_url`, `length_report IN (1,2,3,4,5,6,9)` cho `financial_report_file`/`corporate_event` (giữ 1–5 ở `financial_statement`), bảng sổ kiểm `ops.fundamentals_check` · `0018` (lát 9a, 2026-09-06) `news.article_industry` bài ↔ ngành hai đường `via IN ('ticker','ai')` trong PK + `ops.llm_call` sổ mỗi lời gọi model · `0019` thêm sub `2f` vào CHECK taxonomy tin · `0020` chỉ mục GIN trigram trên `immutable_unaccent(lower(title))` cho gộp tin gần giống · `0021` (lát 13, 2026-09-09) cột `news.article.classify_attempts smallint NOT NULL DEFAULT 0` — đếm số lần phân loại hỏng, job `etl classify` bỏ qua bài đã thử đủ 3 lần), **66 test** seam chạy trên Postgres thật (`backend/tests/schema/test_sNN_*.py` — 16 file, không 1-1 với 21 migration: test seed `0003` gộp vào `test_s02_identity.py`, `test_s03_market_data.py` test migration `0004`; từ `test_s05_macro.py` trở đi NN khớp đúng số migration, kể cả `test_s10_registry_ts.py` cho `0010`; `test_s11_industry_override.py` phủ cả `0012` lẫn nội dung seed `0013`; `test_s12_directory_absent.py` cho `0014`; `test_s13_snapshot_check.py` cho `0016`, gồm một test chạy dưới role `dlck_etl` thật; `test_s14_fundamentals.py` cho `0017`, test role đi qua cả **DELETE** `financial_statement` — đường mà `etl fundamentals` dùng mỗi lần nội dung đổi; `test_s15_news_industry_llm_call.py` cho `0018`, test role `dlck_etl` đi qua **mọi đường** của job `etl classify` — INSERT hai bảng mới, UPDATE `article` + `article_revision.summary_ai`, SELECT `industry`/`v_issuer_industry` — và `dlck_api` đọc `article_industry`; `test_s16_sub_2f.py` cho `0019`. **`0020` cố ý không có test schema riêng** — nó chỉ thêm một chỉ mục GIN trigram, không đổi ràng buộc nào; đường dùng nó được phủ ở test dedupe của `etl news`; `test_s17_classify_attempts.py` cho `0021`).

**Đọc ngành của tin qua `news.article_industry`** (không suy lại lúc đọc): `via='ticker'` = suy từ mã lúc phân loại, `via='ai'` = model đọc hiểu; cùng (bài, ngành) có thể có hai dòng — [news-pipeline §8b](../docs/20-design/news-pipeline.md). ⚠️ `ops.llm_call.run_id` tham chiếu `ops.etl_run` và `article_id` tham chiếu `news.article`: **`TRUNCATE ops.etl_run` / `news.article` phải truncate `ops.llm_call` cùng lúc** (test e05 đã sửa theo).

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
> ⚠️ Khi dựng: nghiệm thu bằng **khôi phục thật** (restore vào database tạm rồi đối chiếu số dòng), không phải bằng "đã upload xong" — luật [CLAUDE.md §3.5](../CLAUDE.md). `CLICKHOUSE_BACKUP_DIR` tương đối được giải theo **gốc repo** (cùng gốc với `docker-compose.yml` từ lát 12, cùng chuẩn compose dùng); để TRỐNG = coi như chưa đặt ⇒ mặc định `deploy/infra/clickhouse-backups` — nên đặt đường dẫn tuyệt đối khi deploy thật.

> **Idempotency dựa trên tên file, không kiểm nội dung:** script coi một partition/ngày là "đã backup" nếu file `.zip` cùng tên đã tồn tại. File `.zip` hỏng do crash giữa chừng (ví dụ mất điện khi đang ghi) vẫn bị coi là đã backup và sẽ không được ghi lại — kiểm toàn vẹn định kỳ là việc vận hành, chưa tự động hoá.

> **Hai role trùng tên `dlck_api` — đừng nhầm hai kho:** Postgres có role `dlck_api` đọc 4 schema miền (`market`/`macro`/`asset`/`news`, xem mục Luật bên dưới); ClickHouse **cũng** có role `dlck_api` (migration `0001_roles.sql`) nhưng chỉ đọc schema `rt`. Hai role sống trên hai engine khác nhau, trùng tên có chủ đích (cùng vai trò "reader cho `api`"), không phải cấu hình chung.
>
> User login của ClickHouse do `core.bootstrap` cấp — cùng nguyên tắc với user login Postgres ở mục Luật.

## Cách chạy

`.env` ở gốc repo khai nguyên tố (`POSTGRES_USER`/`POSTGRES_PASSWORD`/`POSTGRES_HOST`/`POSTGRES_PORT`/`POSTGRES_DB`) — `database/migrations/env.py` tự gọi `core.env.load_dotenv()` để ráp `DATA_DATABASE_URL`, không cần export tay. Trong container: `docker compose run --rm migrate` chạy alembic head + `ch_migrate` + cấp user + seed lớp 2 — xem [`backend/core/bootstrap.py`](../backend/core/bootstrap.py).

Migrate DB ở `DATA_DATABASE_URL` (native):

```bash
uv run --project backend alembic -c database/alembic.ini upgrade head
uv run --project backend alembic -c database/alembic.ini downgrade base   # rollback toàn phần
```

Test schema (tự tạo lại `dulieu_test` từ đầu qua `backend/tests/conftest.py` — một lần cho cả bộ, không đụng DB ở `DATA_DATABASE_URL`):

```bash
cd backend && uv run pytest tests/schema -v
```

Cả bộ trong một lệnh *(số hiện hành ở ngay dưới — mục này chỉ giữ **lịch sử tăng trưởng**, đừng đọc nó làm số hôm nay)* *(đo 2026-09-06 chiều sau lát 9a lưới AI phân loại: 877 test, +52 test — `tests/core/test_llm_*` 13, `test_s15` 4, `test_e59`–`e61` 34, và +1 test dispose; migration head `0018`; 809 trưa cùng ngày sau lát 8b + trả nợ nhỏ; 791 sáng sau lát 8 thu thập tin: +53 test `test_e52`–`e58`; 729 tối 2026-09-05 sau lát 7b cập nhật trong phiên: +20 test `test_e50`–`e51` và test mới ở e41/e43–e49; 709 sau lát 7 ETL quốc tế và đợt sửa review toàn nhánh; 650 chiều cùng ngày sau nợ Ctrl+C `test_e42`; 640 sáng sau lát 6 `etl wichart`; không migration mới, head vẫn `0017`)*, gồm cả `tests/clickhouse` và `tests/ingester` *(hai bộ này tự dựng container ClickHouse riêng ở cổng riêng, không đụng CH production)*:

```bash
cd backend && uv run pytest tests -q
```

**Không cần `--env-file`** *(từ 2026-09-08)*: `tests/conftest.py` tự gọi `load_dotenv()`, nên `uv run pytest tests -q` **và mọi lượt chạy một phần** (`pytest tests/etl`, `pytest tests/schema`) đều chạy được trong shell sạch. `load_dotenv` dùng `setdefault` nên biến export sẵn ở shell/CI vẫn thắng. 🔴 *Lịch sử, đừng làm theo:* trước 2026-09-08 `--env-file ../.env` là bắt buộc — chạy trần cho **425 error** `KeyError: 'TEST_DATABASE_URL'`. Rồi test canh đường khởi động của lát 11 vô tình nạp `.env` hộ cả bộ, nên `pytest tests` xanh mà `pytest tests/etl` vẫn đỏ: một sợi dây phụ thuộc thứ tự thu thập, nay đã thay bằng lời gọi tường minh (hợp đồng: `backend/tests/test_conftest_env_contract.py`). Số hiện hành: **1.136 passed, 3 skipped** *(đo 2026-09-08 tối, sau đợt dọn nợ cuối lát 12: +8 test — `test_ch_backup_paths.py` **file mới** 4 ca (+2 ròng: hai ca `resolve_backup_dir` dời khỏi `test_t06_backup.py` để khỏi phải dựng container, thêm hai ca biên `""` và `"."`), `test_tz_contract.py` +2 (quét `ast` thay regex: ca `now(VN)` KHÔNG phải vi phạm, ca văn xuôi nhắc `date.today()`), `test_clock.py` +1 (nhánh `today_vn()` không đối số), `test_env_contract.py` +1 (nháy mở/đóng lệch loại), `test_d03_compose_contract.py` +1 (ba kho không được mang `profiles`), `test_bootstrap_postgres.py` +1 (`main()` thiếu env ⇒ trả 2, không chạm kho); 1.128 sau đợt sửa gộp hậu-review toàn nhánh lát 12: +19 test — `test_env.py` +3 (rỗng = thiếu, `change-me` = yếu, fallback `os.environ`), `test_conftest_env_contract.py` +3 (bán kính `DROP DATABASE`), `test_bootstrap_literals.py` +4 file mới (`_ch_literal`), `test_bootstrap_postgres.py` +1 (role đích không tồn tại), `test_e36_wichart_registry.py` +1 (`doc`/`tier_x` phải đi cùng nhau), `test_tz_contract.py` +2 (đối chứng dương + seam âm), `test_env_contract.py` +3 (đối chứng dương `_READ` + `unread_keys`), `test_d03_compose_contract.py` +2 (đối chứng dương `docs/` + tách override `etl`); 1.109 sau khi đóng lát 12 "chạy được trong container" — skip thứ ba là `test_shutdown.py`: Windows không giao SIGTERM cho handler Python, chỉ chạy trên POSIX; "2 skipped" của các mốc dưới đây nay lỗi thời)* *(2026-09-07 sau đợt dọn lệch tài liệu ↔ code: +7 test `tests/docs` thi hành §1.7, +2 test bịt lỗ hổng `phan_ure` và `tn` — phần NguoiQuanSat là assertion chèn vào hàm sẵn có, không thêm hàm mới; 1.029 sau lát 11)*. 🔴 **Đây là chủ sở hữu duy nhất của con số này** — `README.md` gốc và `roadmap.md` §0 cố ý KHÔNG nêu lại (trước 2026-09-07 nó nằm ở bốn chỗ và bốn chỗ nói khác nhau).

🔴 **Đừng chạy hai phiên `pytest` cùng lúc.** Cả bộ dùng **một** DB test `dulieu_test`; hai phiên song song giẫm dữ liệu của nhau và cho ra hàng chục fail/error rải rác ở `tests/etl` — mỗi file chạy riêng lại pass, nên rất dễ tưởng là nợ kỹ thuật có sẵn *(đã gặp thật 2026-09-07: một phiên review chạy song song ⇒ 11 failed + 7 error; chạy lại một mình ⇒ 1.029 passed hai lượt liên tiếp)*.

*(Lịch sử fixture: trước `ff4d0ca` — 2026-08-28 — lệnh gộp chết ở bước collection vì `tests/schema/conftest.py` và `tests/etl/conftest.py` cùng nạp dưới tên module `conftest`; sửa bằng import đủ đường dẫn. Cách đó lại tạo **hai fixturedef `migrated_engine`** session-scope ⇒ full suite dựng + migrate `dulieu_test` **hai lần**, và lần dựng lại thứ hai từng che va chạm dữ liệu giữa test job và test schema (review lát 6). **Từ 2026-09-05 chỉ còn một `backend/tests/conftest.py`** giữ `migrated_engine` · `db` · `expect_violation`; hai conftest con đã xoá; test schema dùng literal `ZZ*`/`zz_test` để không đụng dòng mà test job đã commit.)*

## Luật

- **Sửa DDL qua migration mới** — không sửa file trong `database/migrations/versions/` đã chạy, kể cả trên dev. Phát hiện sai thì viết migration kế tiếp để sửa, không quay lại sửa migration cũ.
- **Mọi SQL qualify đủ `schema.object`**, không dựa `search_path`. Bốn extension (`unaccent`, `pg_trgm`, `vector`, `fuzzystrmatch`) nằm trong schema `extensions`, không phải `public`: hàm bọc phải qualify (`extensions.unaccent(...)`), opclass viết `extensions.gin_trgm_ops`, operator so khớp mờ của `pg_trgm` viết `OPERATOR(extensions.%)` chứ không phải `%` trần — bẫy đã gặp thật khi viết migration `0007` (tìm kiếm tin theo tên mờ).
- **Role ứng dụng là `NOLOGIN`, tạo trong migration `0009`:** `dlck_etl` ghi 6 schema (`market`/`macro`/`asset`/`news`/`staging`/`ops`), `dlck_api` chỉ đọc 4 schema miền (`market`/`macro`/`asset`/`news`). User login do `core.bootstrap` tạo/đồng bộ từ `.env` (`ETL_DB_*`, `AGENT_DB_*`, `CLICKHOUSE_INGESTER_*`, `CLICKHOUSE_API_*`) mỗi lần `docker compose up`; không còn tạo tay — mặc định `etl_worker IN ROLE dlck_etl` (biến `ETL_DATABASE_URL`) và `agent_reader IN ROLE dlck_api` (biến `AGENT_DATABASE_URL`).

  `agent_reader` tạo lần đầu 2026-09-07, nay do bootstrap đồng bộ mật khẩu mỗi lượt `up`. Tiến trình `python -m agent` gọi `agent.db.assert_read_only()` ngay lúc khởi động: khẳng định `pg_has_role(current_user,'dlck_api','member')` **và** `has_table_privilege('market.security','INSERT') = false`, sai thì chết ngay. Kiểm thật dưới credential production 2026-09-07: `current_user=agent_reader`, thuộc `dlck_api`, `INSERT` bị chặn (`ProgrammingError`).
- ⚠️ **`alembic downgrade <revision>` = revision ĐÍCH, chạy `downgrade()` của migration NGAY SAU revision đó** — nói tắt "downgrade qua X" dễ khiến người đọc lẫn giữa "tới X" và "của X". Hai ca phá dữ liệu ngành thật, nêu rõ từng vế:
  - `alembic downgrade 0002` (tới revision `0002`) chạy `downgrade()` của `0003` → **`DELETE`** sạch `market.industry_icb_map` (bản đồ ICB→ngành lớp 1). Backup bảng này trước khi chạy lệnh này trên DB có dữ liệu thật.
  - `alembic downgrade 0011` (tới revision `0011`) chạy `downgrade()` của `0012` → **`DROP TABLE`** hẳn `market.issuer_industry_override` (161 dòng gán tay lớp 2) — mất luôn cả bảng, không chỉ mất dữ liệu. Backup bảng này trước khi chạy lệnh này trên DB có dữ liệu thật.

  **Không phải cùng lệnh với bước 3 của mục Bootstrap DB mới ngay dưới đây** — bước 3 chạy `docker compose run --rm migrate`, tức `core.bootstrap` tự chạy lại **riêng revision `0013`** qua `Operations.context` (chỉ `DELETE` rồi nạp lại rows do `0013` seed, KHÔNG `DROP` bảng nào) — an toàn hơn nhiều so với hai ca DROP/DELETE ở trên.
- **Bootstrap DB mới — thứ tự bắt buộc, không được đảo:**
  1. `docker compose up -d` — kho + `migrate` chạy alembic head + `ch_migrate` + cấp 4 user login (`0013` seed lớp 2 ra **0 dòng** ở bước này vì `market.security` còn rỗng, đúng thiết kế).
  2. `docker compose run --rm etl python -m etl refdata` để nạp danh bạ doanh nghiệp (`market.security`, `market.issuer`).
  3. `docker compose run --rm migrate` — chạy lại: `core.bootstrap` tự phát hiện `market.security` đã có dòng mà `issuer_industry_override` rỗng, và chạy lại riêng revision `0013` để seed lớp 2 (xem cảnh báo dưới).
  4. Kiểm: `select count(*) from market.issuer_industry_override` phải ra **161**.

  Vì sao cần bước 3: migration `0013` seed lớp 2 (`market.issuer_industry_override`) bằng cách phân giải **ticker → `issuer_id` qua `market.security`**. Trên DB dựng mới, `market.security` còn rỗng khi `0013` chạy ở bước 1 ⇒ nạp **0 dòng override, không exception** (câu `RAISE NOTICE` báo số dòng khớp cũng không hiện ra vì `alembic` không in `NOTICE`). Job `etl refdata` sau đó vẫn báo `issuers_without_industry` y hệt trạng thái khoẻ mạnh — **không có gì báo động** — trong khi toàn bộ 161 doanh nghiệp lẽ ra được gán tay lại rơi về gán máy (lớp 1), có thể sai ngành hoặc vi phạm luật BCTC.

  🔴 **KHÔNG dùng `downgrade 0012` nữa** — đúng khi head là `0013`, nay head `0021` nên lệnh đó lùi chín migration và DROP `news.article_industry`, `ops.llm_call`, `ops.snapshot_check`… kèm dữ liệu (phát hiện 2026-09-08 khi viết plan lát 12). Cách đúng là `core.bootstrap` chạy riêng revision `0013` qua `Operations.context`.
