# Plan thực thi — Lược đồ PostgreSQL `postgres-data`

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Biến spec 7 bước đã chốt (4 vòng review) thành DB thật: khung Alembic + 9 migration + seed cây ngành + bộ seam test xanh trên Postgres thật.

**Architecture:** Alembic một env cho `postgres-data`, migration viết SQL thô (`op.execute`), mỗi bước spec một migration; test pytest chạy trên **Postgres thật** (DB `dulieu_test` tạo/xoá bởi fixture), TDD lát dọc: test đỏ (object chưa tồn tại) → viết migration → xanh.

**Tech Stack:** PostgreSQL 16 (image `pgvector/pgvector:pg16`, compose `deploy/infra/`) · Alembic + SQLAlchemy (chỉ làm runner, không ORM) · psycopg 3 · pytest · uv.

**Spec:** [`step-01`](step-01-foundations.md) … [`step-07`](step-07-staging-ops.md) cùng thư mục — **plan này trích dẫn DDL theo section của spec, executor phải mở spec đọc cùng.** Quyết định xuyên suốt + hợp đồng tháo lắp: [README.md](README.md). Lịch sử review: [review-2026-08-25.md](review-2026-08-25.md).

## Global Constraints

- **Nhánh:** toàn bộ plan chạy trên nhánh `feat/postgres-data-schema` (repo đã có code sản phẩm — CLAUDE.md §4.7). Commit message tiếng Anh, Conventional Commits, kết thúc bằng `Co-Authored-By: Claude <model> <noreply@anthropic.com>`.
- **DDL copy nguyên văn từ spec, KHÔNG gõ lại theo trí nhớ.** Mỗi task ghi rõ section nguồn. Spec là chủ sự thật; plan chỉ thêm phần spec không có (conftest, generator, seed SQL, grants, test code).
- **7 schema:** `market` `macro` `asset` `news` `staging` `ops` + `extensions` (4 extension cài vào đây). Mọi SQL qualify đủ `schema.object` (step-01 §3).
- **Không cột `source` ở bảng dữ liệu** — chỉ registry/staging/ops/news (README quyết định #4).
- **Ngữ nghĩa ghi từng bảng đúng như spec** (UPSERT/append/version) — test phải assert đúng ngữ nghĩa đó.
- **Test:** Postgres thật, không SQLite (test-strategy §2); expected là literal/giải tay, cấm tautological; mỗi bảng test có case biên/sai (CLAUDE.md §4.5).
- **Env:** `DATA_DATABASE_URL` (dev) / `TEST_DATABASE_URL` (test) — psycopg 3 DSN dạng `postgresql+psycopg://dulieu:<POSTGRES_PASSWORD>@127.0.0.1:5432/<db>`. Không in giá trị password ra log/commit.
- **Giao việc (CLAUDE.md §4.1):** Task 1 và Task 4 (cần phán đoán gate) + Task 11 (docs) — **controller tự làm**; Task 2, 3, 5, 6, 7, 8, 9, 10 — **subagent Sonnet** (`model: sonnet` tường minh — cấm Fable). Ledger ghi tại `ledger.md` cùng thư mục.

## File Structure

```
database/
├── alembic.ini                  # script_location = database/migrations
├── gen_price_columns.py        # generator cột price_daily từ market-field-selection.json
└── migrations/
    ├── env.py                  # đọc DATA_DATABASE_URL từ os.environ
    ├── script.py.mako          # mặc định của alembic init
    └── versions/
        ├── 0001_schemas_extensions.py
        ├── 0002_market_identity.py
        ├── 0003_seed_industry.py
        ├── 0004_market_data.py
        ├── 0005_macro.py
        ├── 0006_asset.py
        ├── 0007_news.py
        ├── 0008_staging_ops.py
        └── 0009_roles_grants.py
backend/
├── pyproject.toml              # + sqlalchemy, alembic, psycopg[binary]
└── tests/schema/
    ├── conftest.py             # fixture DB test thật + alembic upgrade
    ├── test_s01_foundations.py
    ├── test_s02_identity.py
    ├── test_s03_market_data.py
    ├── test_s05_macro.py       # (đặt theo bước spec — bước 4 spec = macro)
    ├── test_s06_asset.py
    ├── test_s07_news.py
    ├── test_s08_staging_ops.py
    └── test_s09_grants.py
database/README.md              # Modify: trạng thái + cách chạy (index cùng lượt, §1.6)
env.example                     # Modify: thêm DATA_DATABASE_URL/TEST_DATABASE_URL
```

**Ánh xạ seam spec → test file** (seam nào KHÔNG ở plan này thì ghi rõ): mọi seam thuần-schema của step-01…07 nằm trong các file test trên. **Bốn seam thuộc tầng ETL, chuyển sang plan ETL sau** (ghi để không ai đi tìm): step-04 seam 2 (parse epoch WiChart theo múi giờ VN), seam 5 (parse số VN `6.307,47`), step-05 bẫy ETL (cổng Yahoo/Binance/LBMA), step-07 seam 1b nửa ETL (policy hash là logic adapter). Chúng cần code ETL — chưa tồn tại trong plan này.

---

### Task 1: Khung — nhánh, deps, Alembic, fixture DB test, migration 0001 (controller tự làm)

**Files:**
- Create: `database/alembic.ini`, `database/migrations/env.py`, `database/migrations/script.py.mako`, `database/migrations/versions/0001_schemas_extensions.py`, `backend/tests/schema/conftest.py`, `backend/tests/schema/test_s01_foundations.py`
- Modify: `backend/pyproject.toml`, `env.example`

**Interfaces (Produces):** lệnh chuẩn cho mọi task sau —
- Migrate: `uv run --project backend alembic -c database/alembic.ini upgrade head` (chạy từ gốc repo, cần env `DATA_DATABASE_URL`)
- Test: `uv run --project backend pytest backend/tests/schema -v` (cần env `TEST_DATABASE_URL`; conftest tự dựng DB test + upgrade head)
- Fixture pytest: `db` (Connection, transaction ngoài rollback sau mỗi test), helper `expect_violation(db, stmt)` (chạy trong SAVEPOINT, trả True nếu IntegrityError)

- [ ] **Step 1: Nhánh + hạ tầng chạy**

```bash
git checkout -b feat/postgres-data-schema
docker network create dlck-net 2>/dev/null || true
docker compose -f deploy/infra/docker-compose.yml --env-file .env up -d postgres
docker compose -f deploy/infra/docker-compose.yml --env-file .env ps
```
Expected: service `postgres` state `healthy` (chờ healthcheck ~10s).

- [ ] **Step 2: Deps + env vars**

`backend/pyproject.toml` — thêm vào `dependencies`: `"sqlalchemy>=2.0"`, `"alembic>=1.13"`, `"psycopg[binary]>=3.2"`. Chạy `uv sync --project backend`. Expected: exit 0, lock cập nhật.

`env.example` — thêm hai dòng (giá trị mẫu, KHÔNG phải secret thật):
```
DATA_DATABASE_URL=postgresql+psycopg://dulieu:<POSTGRES_PASSWORD>@127.0.0.1:5432/dulieu
TEST_DATABASE_URL=postgresql+psycopg://dulieu:<POSTGRES_PASSWORD>@127.0.0.1:5432/dulieu_test
```

- [ ] **Step 3: Khung Alembic**

`database/alembic.ini`:
```ini
[alembic]
script_location = database/migrations
file_template = %%(rev)s_%%(slug)s
[loggers]
keys = root
[handlers]
keys = console
[formatters]
keys = generic
[logger_root]
level = WARN
handlers = console
[handler_console]
class = StreamHandler
args = (sys.stderr,)
formatter = generic
[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
```

`database/migrations/env.py`:
```python
import os
from alembic import context
from sqlalchemy import create_engine, pool

def run_migrations_online() -> None:
    url = os.environ["DATA_DATABASE_URL"]  # test đặt env này trỏ DB test trước khi gọi
    engine = create_engine(url, poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=None)
        with context.begin_transaction():
            context.run_migrations()

run_migrations_online()
```
`script.py.mako`: lấy nguyên bản mặc định của Alembic (chạy `uv run --project backend alembic init /tmp/_scaffold` rồi copy file mako, hoặc chép từ site-packages).

- [ ] **Step 4: conftest — DB test thật**

`backend/tests/schema/conftest.py`:
```python
import os
import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy.exc import IntegrityError

TEST_URL = os.environ["TEST_DATABASE_URL"]          # ...:5432/dulieu_test
ADMIN_URL = TEST_URL.rsplit("/", 1)[0] + "/dulieu"  # DB có sẵn để CREATE DATABASE
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

@pytest.fixture(scope="session")
def migrated_engine():
    admin = sa.create_engine(ADMIN_URL, isolation_level="AUTOCOMMIT")
    with admin.connect() as c:
        c.execute(sa.text("DROP DATABASE IF EXISTS dulieu_test WITH (FORCE)"))
        c.execute(sa.text("CREATE DATABASE dulieu_test"))
    cfg = Config(os.path.join(REPO_ROOT, "database", "alembic.ini"))
    os.environ["DATA_DATABASE_URL"] = TEST_URL      # env.py đọc biến này
    command.upgrade(cfg, "head")
    engine = sa.create_engine(TEST_URL)
    yield engine
    engine.dispose()

@pytest.fixture()
def db(migrated_engine):
    with migrated_engine.connect() as conn:
        tx = conn.begin()
        yield conn
        tx.rollback()                                # mỗi test một transaction, sạch tuyệt đối

def expect_violation(conn, sql, params=None):
    """Chạy trong SAVEPOINT; trả True nếu vi phạm ràng buộc (transaction ngoài còn sống)."""
    nested = conn.begin_nested()
    try:
        conn.execute(sa.text(sql), params or {})
        nested.commit()
        return False
    except IntegrityError:
        nested.rollback()
        return True
```

- [ ] **Step 5: Test đỏ — seam bước 1**

`backend/tests/schema/test_s01_foundations.py`:
```python
import sqlalchemy as sa

EXPECTED_SCHEMAS = {"market", "macro", "asset", "news", "staging", "ops", "extensions"}  # 7 — step-01 §2
EXPECTED_EXTS = {"unaccent", "pg_trgm", "vector", "fuzzystrmatch"}                        # 4 — step-01 §3

def test_seven_schemas(db):
    rows = db.execute(sa.text(
        "SELECT nspname FROM pg_namespace WHERE nspname = ANY(:s)"), {"s": list(EXPECTED_SCHEMAS)})
    assert {r[0] for r in rows} == EXPECTED_SCHEMAS

def test_four_extensions_in_extensions_schema(db):
    rows = db.execute(sa.text(
        "SELECT e.extname, n.nspname FROM pg_extension e JOIN pg_namespace n ON n.oid=e.extnamespace "
        "WHERE e.extname = ANY(:x)"), {"x": list(EXPECTED_EXTS)})
    got = {r[0]: r[1] for r in rows}
    assert set(got) == EXPECTED_EXTS
    assert all(v == "extensions" for v in got.values())          # I-7/F2: đúng schema, không rơi vào public

def test_public_schema_locked(db):
    ok = db.execute(sa.text("SELECT has_schema_privilege('public', 'public', 'CREATE')")).scalar()
    assert ok is False                                            # step-01 §2: khoá CREATE trên public
```
Run: `uv run --project backend pytest backend/tests/schema/test_s01_foundations.py -v`
Expected: FAIL (schema `market`… chưa tồn tại — migration chưa viết).

- [ ] **Step 6: Migration 0001**

`0001_schemas_extensions.py` — `upgrade()` chạy `op.execute` khối SQL:
```sql
CREATE SCHEMA extensions;
CREATE SCHEMA market; CREATE SCHEMA macro; CREATE SCHEMA asset;
CREATE SCHEMA news;   CREATE SCHEMA staging; CREATE SCHEMA ops;
CREATE EXTENSION unaccent      SCHEMA extensions;
CREATE EXTENSION pg_trgm       SCHEMA extensions;
CREATE EXTENSION vector        SCHEMA extensions;
CREATE EXTENSION fuzzystrmatch SCHEMA extensions;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
```
`downgrade()`: `DROP EXTENSION` 4 cái, `DROP SCHEMA … CASCADE` 7 cái, `GRANT CREATE ON SCHEMA public TO PUBLIC;`

- [ ] **Step 7: Xanh + downgrade sạch**

Run test Step 5 → Expected: 3 PASS. Rồi:
```bash
uv run --project backend alembic -c database/alembic.ini downgrade base
uv run --project backend alembic -c database/alembic.ini upgrade head
```
Expected: cả hai exit 0 (seam 2 bước 1 — downgrade không sót object).
⚠️ Lệnh trên chạy với `DATA_DATABASE_URL` trỏ DB dev `dulieu` — cũng phải upgrade được.

- [ ] **Step 8: Commit** — `git add database backend/pyproject.toml backend/uv.lock backend/tests/schema env.example && git commit -m "feat(db): alembic skeleton, 7 schemas + 4 extensions, real-db test fixture"`

---

### Task 2: Migration 0002 — định danh market (Sonnet)

**Files:** Create `database/migrations/versions/0002_market_identity.py`, `backend/tests/schema/test_s02_identity.py`

**Interfaces:** Consumes fixture `db`, `expect_violation` (Task 1). Produces: bảng `market.industry / industry_icb_map / icb_industry / issuer / issuer_external_id / security / security_external_id` — mọi task sau FK vào `issuer`/`security`.

- [ ] **Step 1: Test đỏ** — `test_s02_identity.py`, DDL nguồn: **step-02 §2 (copy nguyên văn toàn bộ khối SQL)**. Test theo seam step-02 §4:
```python
import sqlalchemy as sa
from conftest import expect_violation

def _mk_security(db, ticker, exchange, status="listed", stype="stock"):
    return db.execute(sa.text(
        "INSERT INTO market.security (ticker, exchange, security_type, status) "
        "VALUES (:t,:e,:st,:s) RETURNING security_id"),
        {"t": ticker, "e": exchange, "st": stype, "s": status}).scalar()

def test_partial_unique_ticker(db):                      # seam 1
    _mk_security(db, "ABC", "HOSE")
    assert expect_violation(db,
        "INSERT INTO market.security (ticker, exchange, security_type, status) "
        "VALUES ('ABC','HOSE','stock','listed')")
    _mk_security(db, "ABC", "HOSE", status="delisted")   # delisted nằm ngoài luật → hợp lệ

def test_external_id_two_subs_same_source(db):           # seam 2 + 2b (F4/I-3)
    sid = _mk_security(db, "VNINDEX", "HOSE", stype="index")
    db.execute(sa.text(
        "INSERT INTO market.security_external_id (security_id, source, external_code, external_sub) "
        "VALUES (:i,'bvsc','VNINDEX','tvc'), (:i,'bvsc','HOSE','snapshot')"), {"i": sid})
    assert expect_violation(db,
        "INSERT INTO market.security_external_id (security_id, source, external_code, external_sub) "
        f"VALUES ({sid},'bvsc','VNINDEX','tvc2')") is False or True  # xem ghi chú dưới
    n = db.execute(sa.text(
        "SELECT count(*) FROM market.security_external_id WHERE security_id=:i AND source='bvsc'"),
        {"i": sid}).scalar()
    assert n == 2

def test_industry_level_checks(db):                      # seam 3
    assert expect_violation(db,
        "INSERT INTO market.industry (code,name_vi,parent_id,level) VALUES ('X1','X',NULL,3)")
    assert expect_violation(db,
        "INSERT INTO market.industry (code,name_vi,parent_id,level) VALUES ('X2','X',NULL,2)")
    gid = db.execute(sa.text(
        "INSERT INTO market.industry (code,name_vi,parent_id,level) "
        "VALUES ('XG','Nhóm X',NULL,1) RETURNING industry_id")).scalar()
    assert expect_violation(db,
        f"INSERT INTO market.industry (code,name_vi,parent_id,level) VALUES ('XG2','X',{gid},1)")

def test_icb_map_fk(db):                                 # seam 4 (dùng seed Task 3? KHÔNG —
    assert expect_violation(db,                          #  test tự tạo ngành, độc lập thứ tự task)
        "INSERT INTO market.industry_icb_map (icb_code, industry_id) VALUES ('9999', 999999)")
```
*(Ghi chú dòng `is False or True`: XOÁ dòng đó khi viết thật — nó là nhắc suy nghĩ: chèn `('bvsc','VNINDEX','tvc2')` trùng UNIQUE `(security_id, source, external_sub)`? Không — sub khác nhau. Nhưng trùng PK `(source, external_code)`? `VNINDEX` đã dùng → **có, phải violation**. Viết: `assert expect_violation(...)` thẳng.)*
Run → Expected: FAIL `relation "market.security" does not exist`.

- [ ] **Step 2: Migration 0002** — copy nguyên văn 7 khối `CREATE TABLE`/`CREATE INDEX` của step-02 §2 vào `op.execute`. `downgrade()`: DROP 7 bảng theo thứ tự ngược FK.
- [ ] **Step 3: Xanh** — chạy file test → PASS hết; chạy lại `test_s01` → vẫn PASS.
- [ ] **Step 4: Commit** — `feat(db): market identity tables (issuer/security/industry, external ids)`

---

### Task 3: Migration 0003 — seed cây ngành 6×24 (Sonnet)

**Files:** Create `0003_seed_industry.py`; Modify `backend/tests/schema/test_s02_identity.py` (thêm test seed)

**Nguồn sự thật:** `docs/20-design/industry-tree.md` — chủ nội dung duy nhất. Seed SQL dưới đây đã chép từ đó; test đối chiếu literal để hai bản không trôi (seam bước 2 số 4).

- [ ] **Step 1: Test đỏ** (thêm vào `test_s02_identity.py`):
```python
L1 = {"TAICHINH","BATDONGSAN","SANXUAT","XUATKHAU","TIEUDUNG","NANGLUONG"}
L2 = {"NGANHANG","CHUNGKHOAN","BAOHIEM","BDS","KCN","XAYDUNG","VLXD",
      "KIMLOAI","TAINGUYEN","HOACHAT","NHUA","THIETBI",
      "NONGNGHIEP","THUYSAN","DETMAY","CAOSU",
      "BANLE","THUCPHAM","DULICH","YTEGD",
      "DIENNUOC","DAUKHI","VANTAI","CONGNGHE"}   # literal từ industry-tree.md §2

def test_industry_seed_matches_tree(db):
    l1 = {r[0] for r in db.execute(sa.text("SELECT code FROM market.industry WHERE level=1"))}
    l2 = {r[0] for r in db.execute(sa.text("SELECT code FROM market.industry WHERE level=2"))}
    assert l1 == L1 and l2 == L2
    fanout = db.execute(sa.text(
        "SELECT p.code, count(*) FROM market.industry c JOIN market.industry p ON p.industry_id=c.parent_id "
        "GROUP BY p.code ORDER BY p.code")).all()
    assert dict(fanout) == {"BATDONGSAN":4,"NANGLUONG":4,"SANXUAT":5,
                            "TAICHINH":3,"TIEUDUNG":4,"XUATKHAU":4}   # phân bố 3·4·5·4·4·4
```
Run → FAIL (bảng rỗng).

- [ ] **Step 2: Migration 0003** — `op.execute` (điền `name_vi` đúng nguyên văn bảng industry-tree §2, sort_order theo thứ tự bảng):
```sql
INSERT INTO market.industry (code, name_vi, parent_id, level, sort_order) VALUES
 ('TAICHINH','Dịch vụ Tài chính',NULL,1,1), ('BATDONGSAN','Bất động sản và Xây dựng',NULL,1,2),
 ('SANXUAT','Sản xuất Công nghiệp',NULL,1,3), ('XUATKHAU','Xuất khẩu Chủ lực',NULL,1,4),
 ('TIEUDUNG','Tiêu dùng Đời sống',NULL,1,5), ('NANGLUONG','Năng lượng và Hạ tầng',NULL,1,6);
INSERT INTO market.industry (code, name_vi, parent_id, level, sort_order)
SELECT v.code, v.name_vi, p.industry_id, 2, v.ord
FROM (VALUES
 ('NGANHANG','Ngân hàng và Tín dụng','TAICHINH',1), ('CHUNGKHOAN','Công ty Chứng khoán','TAICHINH',2),
 ('BAOHIEM','Kinh doanh Bảo hiểm','TAICHINH',3),
 ('BDS','Bất động sản Dân dụng','BATDONGSAN',1), ('KCN','Bất động sản Khu công nghiệp','BATDONGSAN',2),
 ('XAYDUNG','Thi công Xây dựng','BATDONGSAN',3), ('VLXD','Vật liệu Xây dựng','BATDONGSAN',4),
 ('KIMLOAI','Kim loại Công nghiệp','SANXUAT',1), ('TAINGUYEN','Tài nguyên Cơ bản','SANXUAT',2),
 ('HOACHAT','Hóa chất và Phân bón','SANXUAT',3), ('NHUA','Nhựa và Bao bì','SANXUAT',4),
 ('THIETBI','Thiết bị Điện và Máy móc','SANXUAT',5),
 ('NONGNGHIEP','Nông nghiệp và Chăn nuôi','XUATKHAU',1), ('THUYSAN','Chế biến Thủy sản','XUATKHAU',2),
 ('DETMAY','Dệt may và Gia dụng','XUATKHAU',3), ('CAOSU','Cao su và Săm lốp','XUATKHAU',4),
 ('BANLE','Bán buôn và Bán lẻ','TIEUDUNG',1), ('THUCPHAM','Thực phẩm và Đồ uống','TIEUDUNG',2),
 ('DULICH','Hàng không, Du lịch và Giải trí','TIEUDUNG',3), ('YTEGD','Dược phẩm, Y tế và Giáo dục','TIEUDUNG',4),
 ('DIENNUOC','Điện, Nước và Khí đốt','NANGLUONG',1), ('DAUKHI','Dầu khí và Nhiên liệu','NANGLUONG',2),
 ('VANTAI','Vận tải, Cảng biển và Kho bãi','NANGLUONG',3), ('CONGNGHE','Công nghệ Thông tin và Viễn thông','NANGLUONG',4)
) AS v(code, name_vi, parent_code, ord)
JOIN market.industry p ON p.code = v.parent_code;
```
`downgrade()`: `DELETE FROM market.industry;`
- [ ] **Step 3: Xanh + Commit** — `feat(db): seed 6x24 industry tree from industry-tree.md`

---

### Task 4: Migration 0004 — bảng dữ liệu market (controller tự làm — có gate phán đoán)

**Files:** Create `0004_market_data.py`, `database/gen_price_columns.py`, `backend/tests/schema/test_s03_market_data.py`

**DDL nguồn: step-03 §1, §2, §3, §3b, §4 — copy nguyên văn** (gồm index `(trading_date)`, `(metric_code, year_report, length_report)`, unique index 6 thành phần của `corporate_event`).

- [ ] **Step 1: Generator cột giá** — `database/gen_price_columns.py`:
```python
"""Sinh đoạn DDL cột cho market.price_daily từ market-field-selection.json.
Luật chọn (chốt trong plan, khớp architecture §3.4 'giá + dẫn xuất giá — nguồn chuẩn BVSC'):
keep == true AND nguon_chuan == 'BVSC'. Mọi cột kiểu numeric (trường giá/khối lượng);
5 cột spec nêu đích danh (close_adj/close_raw/open_value/highest_value/lowest_value) đã có
tay trong DDL — generator BỎ QUA code trùng sau khi snake_case."""
import json, re, pathlib

HAND_WRITTEN = {"close_adj","close_raw","open_value","highest_value","lowest_value"}
snake = lambda s: re.sub(r"(?<!^)(?=[A-Z])", "_", s).lower()
rows = json.loads(pathlib.Path("docs/20-design/market-field-selection.json").read_text(encoding="utf-8"))
cols = [snake(r["code"]) for r in rows if r.get("keep") and r.get("nguon_chuan") == "BVSC"]
cols = [c for c in dict.fromkeys(cols) if c not in HAND_WRITTEN]
print(f"-- {len(cols)} cột sinh từ market-field-selection.json (keep & nguon_chuan=BVSC)")
for c in cols:
    print(f"  {c} numeric,")
```
Run: `uv run --project backend python database/gen_price_columns.py`
**GATE (controller quyết, ghi ledger):** dán số cột + 10 tên đầu vào ledger. Kỳ vọng cỡ **30–60 cột** (BVSC ~40 trường giá — architecture §3.4). Ngoài dải đó → DỪNG, đối chiếu lại JSON, không dán bừa vào migration.
- [ ] **Step 2: Test đỏ** — `test_s03_market_data.py` (seam step-03 §6, đủ 6+3 mục kể cả 5b/5c):
```python
import sqlalchemy as sa
from conftest import expect_violation

def _issuer(db):
    return db.execute(sa.text("INSERT INTO market.issuer (name) VALUES ('CTCP T') RETURNING issuer_id")).scalar()
def _sec(db, t="TST"):
    return db.execute(sa.text(
        "INSERT INTO market.security (ticker,exchange,security_type) VALUES (:t,'HOSE','stock') "
        "RETURNING security_id"), {"t": t}).scalar()

def test_price_factor_view(db):                                     # seam 1 — giải tay
    sid = _sec(db)
    db.execute(sa.text("INSERT INTO market.price_daily (security_id,trading_date,close_adj,close_raw) "
                       "VALUES (:s,'2026-08-20',50,100), (:s,'2026-08-21',50,0)"), {"s": sid})
    rows = dict(db.execute(sa.text(
        "SELECT trading_date::text, factor FROM market.price_factor WHERE security_id=:s"), {"s": sid}).all())
    assert float(rows["2026-08-20"]) == 0.5
    assert rows["2026-08-21"] is None                               # chia 0 → NULL, không lỗi

def test_price_upsert_keeps_raw(db):                                # seam 2
    sid = _sec(db, "TS2")
    ins = ("INSERT INTO market.price_daily (security_id,trading_date,close_adj,close_raw) "
           "VALUES (:s,'2026-08-20',:a,:r) "
           "ON CONFLICT (security_id,trading_date) DO UPDATE SET close_adj = EXCLUDED.close_adj")
    db.execute(sa.text(ins), {"s": sid, "a": 50, "r": 100})
    db.execute(sa.text(ins), {"s": sid, "a": 25, "r": 999})         # writer sau KHÔNG đụng raw
    row = db.execute(sa.text("SELECT close_adj, close_raw FROM market.price_daily "
                             "WHERE security_id=:s"), {"s": sid}).one()
    assert (float(row[0]), float(row[1])) == (25.0, 100.0)

def test_fs_restate_upsert(db):                                     # seam 3 — PAYEMS-style
    iid = _issuer(db)
    ins = ("INSERT INTO market.financial_statement "
           "(issuer_id,year_report,length_report,statement_type,metric_code,value) "
           "VALUES (:i,2026,2,'BS','bsa1',:v) "
           "ON CONFLICT (issuer_id,year_report,length_report,statement_type,metric_code) "
           "DO UPDATE SET value = EXCLUDED.value, ingested_at = now()")
    db.execute(sa.text(ins), {"i": iid, "v": 159001})
    db.execute(sa.text(ins), {"i": iid, "v": 158927})
    got = db.execute(sa.text("SELECT count(*), max(value) FROM market.financial_statement "
                             "WHERE issuer_id=:i"), {"i": iid}).one()
    assert (got[0], float(got[1])) == (1, 158927.0)

def test_event_natural_key(db):                                     # seam 4 + 5b (C-3/F6)
    iid = _issuer(db)
    base = ("INSERT INTO market.corporate_event (event_type,issuer_id,public_date,payload{cols}) "
            "VALUES ('{t}',:i,'2026-08-20','{{}}'::jsonb{vals})")
    db.execute(sa.text(base.format(t="AGM", cols="", vals="")), {"i": iid})
    assert expect_violation(db,                                     # cả hai ngày NULL vẫn chặn
        f"INSERT INTO market.corporate_event (event_type,issuer_id,public_date,payload) "
        f"VALUES ('AGM',{iid},'2026-08-20','{{}}'::jsonb)")
    db.execute(sa.text(                                             # Earning 2 kỳ cùng ngày → 2 dòng
        "INSERT INTO market.corporate_event (event_type,issuer_id,public_date,year_report,length_report,payload) "
        "VALUES ('Earning',:i,'2026-08-20',2026,1,'{}'::jsonb), ('Earning',:i,'2026-08-20',2026,2,'{}'::jsonb)"),
        {"i": iid})
    db.execute(sa.text(                                             # CashDividend 2 đợt → 2 dòng
        "INSERT INTO market.corporate_event (event_type,issuer_id,public_date,stage_key,payload) "
        "VALUES ('CashDividend',:i,'2026-08-20','2025:con-lai','{}'::jsonb),"
        "       ('CashDividend',:i,'2026-08-20','2026:tam-ung','{}'::jsonb)"), {"i": iid})

def test_checks_and_index_stat(db):                                 # seam 5 + 5c
    iid, sid = _issuer(db), _sec(db, "TS3")
    assert expect_violation(db,
        f"INSERT INTO market.financial_statement (issuer_id,year_report,length_report,statement_type,metric_code) "
        f"VALUES ({iid},2026,6,'BS','bsa1')")
    idx = _sec(db, "VNI2")
    db.execute(sa.text("INSERT INTO market.index_contribution_daily "
                       "(index_security_id,security_id,trading_date,payload) "
                       "VALUES (:x,:s,'2026-08-20','{}'::jsonb)"), {"x": idx, "s": sid})

def test_metric_dictionary_two_dicts(db):                           # seam 6
    db.execute(sa.text("INSERT INTO market.metric_dictionary (dictionary, code) "
                       "VALUES ('screener_params','rtq12'), ('field_dictionary','rtq12')"))
```
Run → FAIL `relation "market.price_daily" does not exist`.
- [ ] **Step 3: Migration 0004** — DDL step-03 nguyên văn; chỗ `-- ~90 cột còn lại` thay bằng **output generator Step 1** (dán, kèm comment `-- sinh bởi database/gen_price_columns.py, không sửa tay`). `downgrade()` DROP view + 9 bảng ngược FK.
- [ ] **Step 4: Xanh + Commit** — `feat(db): market data tables (price, financials, snapshots, events, index stats)`

---

### Task 5: Migration 0005 — macro + OMO (Sonnet)

**Files:** Create `0005_macro.py`, `backend/tests/schema/test_s05_macro.py`
**DDL nguồn: step-04 §1, §2, §3 nguyên văn**, riêng view `observation_spliced` spec để pseudo — SQL thật (đã có `coalesce` chống F4-I-6, thêm `CHECK (factor > 0)` vào `series_break` vì công thức dùng `ln`):
```sql
CREATE VIEW macro.observation_spliced AS
SELECT o.indicator_id, o.obs_date,
       o.value * coalesce((SELECT exp(sum(ln(b.factor)))
                           FROM macro.series_break b
                           WHERE b.indicator_id = o.indicator_id
                             AND b.break_date  > o.obs_date), 1) AS value_spliced,
       o.value AS value_as_published
FROM macro.observation o;
```
- [ ] **Step 1: Test đỏ** — `test_s05_macro.py` (seam step-04: 1, 3, 3b, 4, 5b, 6 — seam 2/5 sang plan ETL, đã ghi ở đầu plan):
```python
import sqlalchemy as sa
from conftest import expect_violation

def _ind(db, code="vn.test", freq="m"):
    return db.execute(sa.text(
        "INSERT INTO macro.indicator (code,name_vi,unit,freq,region) "
        "VALUES (:c,'Test','%',:f,'vn') RETURNING indicator_id"), {"c": code, "f": freq}).scalar()

def test_observation_upsert(db):                                    # seam 1
    i = _ind(db)
    ins = ("INSERT INTO macro.observation (indicator_id,obs_date,value) VALUES (:i,'2026-05-01',:v) "
           "ON CONFLICT (indicator_id,obs_date) DO UPDATE SET value=EXCLUDED.value, ingested_at=now()")
    db.execute(sa.text(ins), {"i": i, "v": 159001})
    db.execute(sa.text(ins), {"i": i, "v": 158927})
    got = db.execute(sa.text("SELECT count(*), max(value) FROM macro.observation WHERE indicator_id=:i"),
                     {"i": i}).one()
    assert (got[0], float(got[1])) == (1, 158927.0)

def test_spliced_view(db):                                          # seam 3 + 3b (case biên!)
    i = _ind(db, "vn.gdp.test", "q")
    db.execute(sa.text("INSERT INTO macro.observation (indicator_id,obs_date,value) VALUES "
                       "(:i,'2025-10-01',100), (:i,'2026-01-01',100), (:i,'2026-04-01',170)"), {"i": i})
    db.execute(sa.text("INSERT INTO macro.series_break (indicator_id,break_date,factor,reason) "
                       "VALUES (:i,'2026-04-01',1.6005,'đổi năm gốc')"), {"i": i})
    rows = dict(db.execute(sa.text(
        "SELECT obs_date::text, value_spliced FROM macro.observation_spliced WHERE indicator_id=:i"),
        {"i": i}).all())
    assert float(rows["2025-10-01"]) == 160.05 and float(rows["2026-01-01"]) == 160.05
    assert float(rows["2026-04-01"]) == 170.0                       # đoạn mới giữ nguyên
    j = _ind(db, "vn.nobreak")                                      # 3b: KHÔNG break → không NULL
    db.execute(sa.text("INSERT INTO macro.observation (indicator_id,obs_date,value) "
                       "VALUES (:i,'2026-07-01',42)"), {"i": j})
    v = db.execute(sa.text("SELECT value_spliced FROM macro.observation_spliced "
                           "WHERE indicator_id=:i"), {"i": j}).scalar()
    assert float(v) == 42.0

def test_omo_flow_hand_computed(db):                                # seam 4 (C2: VND gốc)
    db.execute(sa.text("INSERT INTO macro.omo_session (session_date,crawled_at,has_reverse_repo,has_repo,has_outright_sale) "
                       "VALUES ('2026-08-14',now(),true,false,false), ('2026-08-21',now(),true,false,false)"))
    db.execute(sa.text("INSERT INTO macro.omo_auction (session_date,op_type,tenor_days,volume_vnd,rate_pct) "
                       "VALUES ('2026-08-14','reverse_repo',7,6307470000000,4.5),"
                       "       ('2026-08-21','reverse_repo',7,5000000000000,4.5)"))
    # omo_flow là bảng TỰ DỰNG bởi job (không phải trigger) — test schema chỉ kiểm chèn kết quả giải tay:
    db.execute(sa.text("INSERT INTO macro.omo_flow (flow_date,injection_vnd,maturing_vnd,net_vnd) "
                       "VALUES ('2026-08-21',5000000000000,6307470000000,-1307470000000)"))
    net = db.execute(sa.text("SELECT net_vnd FROM macro.omo_flow WHERE flow_date='2026-08-21'")).scalar()
    assert float(net) == -1307470000000.0

def test_checks(db):                                                # seam 5b + 6
    db.execute(sa.text("INSERT INTO macro.omo_session (session_date,crawled_at,has_reverse_repo,has_repo,has_outright_sale) "
                       "VALUES ('2026-08-22',now(),false,true,false)"))
    db.execute(sa.text("INSERT INTO macro.omo_auction (session_date,op_type,tenor_days,volume_vnd) "
                       "VALUES ('2026-08-22','repo',7,1000000000000)"))         # 'repo' hợp lệ (C1)
    assert expect_violation(db, "INSERT INTO macro.omo_auction (session_date,op_type,tenor_days,volume_vnd) "
                                "VALUES ('2026-08-22','swap',7,1)")
    assert expect_violation(db, "INSERT INTO macro.indicator (code,name_vi,unit,freq,region) "
                                "VALUES ('x','X','%','x','vn')")
    assert expect_violation(db, "INSERT INTO macro.omo_auction (session_date,op_type,tenor_days,volume_vnd) "
                                "VALUES ('2099-01-01','repo',7,1)")             # FK phiên chưa crawl
```
Run → FAIL. 
- [ ] **Step 2: Migration 0005** (kèm `CHECK (factor > 0)`); `downgrade()` DROP view + 6 bảng.
- [ ] **Step 3: Xanh + Commit** — `feat(db): macro indicators, spliced view, OMO cluster`

---

### Task 6: Migration 0006 — asset (Sonnet)

**Files:** Create `0006_asset.py`, `backend/tests/schema/test_s06_asset.py`
**DDL nguồn: step-05 §1, §2 nguyên văn** (registry có `external_sub`/`scale`/`active`/`price_type`; hai bảng quan sát; KHÔNG có bảng fx).
- [ ] **Step 1: Test đỏ** (seam step-05 §5: 1, 2, 3, 5, 6 — seam 4 Binance-epoch sang plan ETL):
```python
import sqlalchemy as sa
from conftest import expect_violation

def _asset(db, code, cls="commodity", ccy="USD"):
    return db.execute(sa.text(
        "INSERT INTO asset.asset (code,name_vi,asset_class,quote_currency) "
        "VALUES (:c,'T',:k,:q) RETURNING asset_id"), {"c": code, "k": cls, "q": ccy}).scalar()

def test_wti_spot_futures_coexist_and_upsert(db):                   # seam 1
    a = _asset(db, "wti")
    ins = ("INSERT INTO asset.price_daily (asset_id,obs_date,price_type,value) VALUES (:a,'2026-08-20',:p,:v) "
           "ON CONFLICT (asset_id,obs_date,price_type) DO UPDATE SET value=EXCLUDED.value")
    db.execute(sa.text(ins), {"a": a, "p": "spot",    "v": 84.77})
    db.execute(sa.text(ins), {"a": a, "p": "futures", "v": 82.40})
    db.execute(sa.text(ins), {"a": a, "p": "spot",    "v": 85.00})  # UPSERT đè spot, không nhân đôi
    rows = dict(db.execute(sa.text("SELECT price_type, value FROM asset.price_daily WHERE asset_id=:a"),
                           {"a": a}).all())
    assert {k: float(v) for k, v in rows.items()} == {"spot": 85.00, "futures": 82.40}

def test_price_type_check(db):                                      # seam 2 — 'perp' đã loại
    a = _asset(db, "btc", cls="crypto", ccy="USDT")
    assert expect_violation(db,
        f"INSERT INTO asset.price_daily (asset_id,obs_date,price_type,value) "
        f"VALUES ({a},'2026-08-20','perp',1)")

def test_ohlc_close_adj_upsert(db):                                 # seam 3
    a = _asset(db, "sp500", cls="index")
    ins = ("INSERT INTO asset.ohlc_daily (asset_id,obs_date,open,high,low,close,close_adj) "
           "VALUES (:a,'2026-08-20',1,2,0.5,1.5,:adj) "
           "ON CONFLICT (asset_id,obs_date) DO UPDATE SET close_adj=EXCLUDED.close_adj")
    db.execute(sa.text(ins), {"a": a, "adj": 1.5})
    db.execute(sa.text(ins), {"a": a, "adj": 1.4})
    row = db.execute(sa.text("SELECT close, close_adj FROM asset.ohlc_daily WHERE asset_id=:a"), {"a": a}).one()
    assert (float(row[0]), float(row[1])) == (1.5, 1.4)             # close gốc giữ nguyên

def test_fx_as_asset(db):                                           # seam 5 (I-3-mới)
    a = _asset(db, "fx.usd_eur", cls="fx", ccy="EUR")
    db.execute(sa.text("INSERT INTO asset.price_daily (asset_id,obs_date,price_type,value) "
                       "VALUES (:a,'2026-08-14','fixing',0.86453)"), {"a": a})
    inv = db.execute(sa.text("SELECT round(1/value, 6) FROM asset.price_daily WHERE asset_id=:a"),
                     {"a": a}).scalar()
    assert float(inv) == 1.156698                                   # literal fx.md — tính ở tầng đọc
    db.execute(sa.text("INSERT INTO asset.price_daily (asset_id,obs_date,price_type,value) "
                       "VALUES (:a,'2026-08-14','close',0.86500)"), {"a": a})  # khác mốc chốt — cùng tồn tại

def test_registry_constraints(db):                                  # seam 6 + calendar M11
    _asset(db, "gold.lbma")
    assert expect_violation(db, "INSERT INTO asset.asset (code,name_vi,asset_class,quote_currency) "
                                "VALUES ('gold.lbma','T','commodity','USD')")
    assert expect_violation(db, "INSERT INTO asset.asset (code,name_vi,asset_class,quote_currency,calendar) "
                                "VALUES ('x1','T','commodity','USD','sometimes')")
    a = _asset(db, "paxg", cls="crypto", ccy="USDT")
    db.execute(sa.text("INSERT INTO asset.asset_external_id (asset_id,source,external_code,external_sub) "
                       "VALUES (:a,'binance','PAXGUSDT','')"), {"a": a})
    assert expect_violation(db, f"INSERT INTO asset.asset_external_id (asset_id,source,external_code,external_sub) "
                                f"VALUES ({a},'binance','PAXGUSDT','')")
```
- [ ] **Step 2: Migration 0006**; `downgrade()` DROP 4 bảng. **Step 3: Xanh + Commit** — `feat(db): asset registry and observations (fx as asset class)`

---

### Task 7: Migration 0007 — news (Sonnet)

**Files:** Create `0007_news.py`, `backend/tests/schema/test_s07_news.py`
**DDL nguồn: step-06 §1, §2 nguyên văn** + hàm bọc (spec giao plan chốt):
```sql
CREATE FUNCTION news.immutable_unaccent(text) RETURNS text
LANGUAGE sql IMMUTABLE PARALLEL SAFE STRICT
RETURN extensions.unaccent('extensions.unaccent'::regdictionary, $1);
```
*(dictionary qualify tường minh — I-7/F3; tạo hàm TRƯỚC bảng `article_revision` vì generated column gọi nó.)*
- [ ] **Step 1: Test đỏ** (seam step-06 §5: 1, 2, 3, 3b, 3c, 4, 4b, 5, 6):
```python
import sqlalchemy as sa
from conftest import expect_violation

def _article(db, url="https://x.vn/a1", pub="2026-08-20T09:00:00+07"):
    return db.execute(sa.text(
        "INSERT INTO news.article (canonical_url,primary_source,published_at,fetched_at) "
        "VALUES (:u,'cafef',:p,now()) RETURNING article_id"), {"u": url, "p": pub}).scalar()

def _rev(db, aid, ver, title, content):
    db.execute(sa.text("INSERT INTO news.article_revision (article_id,version,title,content,content_fetched_at) "
                       "VALUES (:a,:v,:t,:c,now())"), {"a": aid, "v": ver, "t": title, "c": content})

def test_tsv_unaccented_search(db):                                 # seam 1 + 6
    a = _article(db)
    _rev(db, a, 1, "Tin thị trường", "HPG dẫn dắt nhóm chứng khoán hôm nay")
    b = _article(db, url="https://x.vn/a2")
    _rev(db, b, 1, "Tin khác", "Giá dầu tăng mạnh")
    hits = [r[0] for r in db.execute(sa.text(
        "SELECT article_id FROM news.article_revision "
        "WHERE tsv @@ to_tsquery('simple', news.immutable_unaccent('chung') || ' & ' || news.immutable_unaccent('khoan'))"))]
    assert a in hits and b not in hits

def test_revision_no_overwrite(db):                                 # seam 2
    a = _article(db, url="https://x.vn/a3")
    _rev(db, a, 1, "Bản 1", "nội dung 1")
    _rev(db, a, 2, "Bản 2", "nội dung 2")
    assert expect_violation(db,
        f"INSERT INTO news.article_revision (article_id,version,title,content,content_fetched_at) "
        f"VALUES ({a},1,'đè','x',now())")
    t1 = db.execute(sa.text("SELECT title FROM news.article_revision WHERE article_id=:a AND version=1"),
                    {"a": a}).scalar()
    assert t1 == "Bản 1"

def test_ticker_via_in_pk(db):                                      # seam 3 + 3b (I-1)
    a = _article(db, url="https://x.vn/a4")
    s = db.execute(sa.text("INSERT INTO market.security (ticker,exchange,security_type) "
                           "VALUES ('HPG','HOSE','stock') RETURNING security_id")).scalar()
    db.execute(sa.text("INSERT INTO news.article_ticker (article_id,security_id,via) "
                       "VALUES (:a,:s,'lookup'), (:a,:s,'ai')"), {"a": a, "s": s})
    assert expect_violation(db, f"INSERT INTO news.article_ticker VALUES ({a},{s},'ai')")
    assert expect_violation(db, f"INSERT INTO news.article_ticker (article_id,security_id,via) "
                                f"VALUES ({a},999999,'url')")

def test_published_unknown(db):                                     # seam 3c (I-2)
    aid = db.execute(sa.text(
        "INSERT INTO news.article (canonical_url,primary_source,published_at,published_at_src,fetched_at) "
        "VALUES ('https://x.vn/a5','vietnambiz',NULL,'unknown',now()) RETURNING article_id")).scalar()
    assert aid is not None

def test_trade_name_fuzzy(db):                                      # seam 4 + 4b — Levenshtein
    s = db.execute(sa.text("INSERT INTO market.security (ticker,exchange,security_type) "
                           "VALUES ('HPG2','HOSE','stock') RETURNING security_id")).scalar()
    db.execute(sa.text("INSERT INTO news.trade_name (name,security_id) VALUES ('Hòa Phát',:s)"), {"s": s})
    lev = db.execute(sa.text("SELECT extensions.levenshtein('ngui','nguoi')")).scalar()
    assert lev == 1                                                 # giải tay: thêm 1 chữ 'o'
    hit = db.execute(sa.text(
        "SELECT security_id FROM news.trade_name "
        "WHERE news.immutable_unaccent(name) % news.immutable_unaccent('Hoà Phát')")).scalar()
    assert hit == s                                                 # trgm bắt khác dấu thanh

def test_url_unique_and_labels(db):                                 # seam 5 + M13
    a = _article(db, url="https://x.vn/a6")
    b = _article(db, url="https://x.vn/a7")
    db.execute(sa.text("INSERT INTO news.article_source (article_id,source_name,url) "
                       "VALUES (:a,'cafef','https://cafef.vn/z1')"), {"a": a})
    assert expect_violation(db, f"INSERT INTO news.article_source (article_id,source_name,url) "
                                f"VALUES ({b},'vietstock','https://cafef.vn/z1')")
    assert expect_violation(db, f"UPDATE news.article SET group_no = 9 WHERE article_id = {a}")
```
- [ ] **Step 2: Migration 0007** (hàm → bảng → index, trgm index dùng `extensions.gin_trgm_ops`); `downgrade()` DROP 5 bảng + hàm. **Step 3: Xanh + Commit** — `feat(db): news articles, revisions, tagging, 3-layer search`

---

### Task 8: Migration 0008 — staging + ops (Sonnet)

**Files:** Create `0008_staging_ops.py`, `backend/tests/schema/test_s08_staging_ops.py`
**DDL nguồn: step-07 §1, §2 nguyên văn** (raw_payload CHECK theo content_type; 5 bảng ops kể cả `series_health` có `source_last_updated`, `source_build`).
- [ ] **Step 1: Test đỏ** (seam step-07 §4: 1, 2, 3, 4):
```python
import sqlalchemy as sa
from conftest import expect_violation

def test_raw_payload_content_type_check(db):                        # seam 1 (M5 siết)
    db.execute(sa.text("INSERT INTO staging.raw_payload (source,endpoint_key,content_type,body) "
                       "VALUES ('sbv','omo','html','<html>KẾT QUẢ ĐẤU THẦU THỊ TRƯỜNG MỞ (14.08.26)</html>')"))
    back = db.execute(sa.text("SELECT body FROM staging.raw_payload WHERE source='sbv'")).scalar()
    assert "KẾT QUẢ ĐẤU THẦU" in back                               # đọc lại nguyên văn
    assert expect_violation(db, "INSERT INTO staging.raw_payload (source,endpoint_key,content_type,body) "
                                "VALUES ('x','k','json','not-json-slot')")
    assert expect_violation(db, "INSERT INTO staging.raw_payload (source,endpoint_key,content_type) "
                                "VALUES ('x','k','html')")

def test_domain_state(db):                                          # seam 2 (M-8)
    ins = ("INSERT INTO ops.data_domain_state (domain,source,status) VALUES ('macro.omo','sbv',:s) "
           "ON CONFLICT (domain,source) DO UPDATE SET status=EXCLUDED.status")
    db.execute(sa.text(ins), {"s": "active"})
    db.execute(sa.text(ins), {"s": "frozen"})
    got = db.execute(sa.text("SELECT count(*), max(status) FROM ops.data_domain_state "
                             "WHERE domain='macro.omo'")).one()
    assert (got[0], got[1]) == (1, "frozen")
    assert expect_violation(db, "INSERT INTO ops.data_domain_state (domain,source,status) "
                                "VALUES ('market.unknown','x','active')")
    assert expect_violation(db, "INSERT INTO ops.data_domain_state (domain,source,status) "
                                "VALUES ('macro.omo','y','paused')")

def test_etl_run_lifecycle(db):                                     # seam 3
    rid = db.execute(sa.text("INSERT INTO ops.etl_run (job) VALUES ('macro.omo_crawl') RETURNING run_id")).scalar()
    db.execute(sa.text("UPDATE ops.etl_run SET status='success', finished_at=now() WHERE run_id=:r"), {"r": rid})
    last = db.execute(sa.text("SELECT status FROM ops.etl_run WHERE job='macro.omo_crawl' "
                              "ORDER BY started_at DESC LIMIT 1")).scalar()
    assert last == "success"

def test_snapshots_append(db):                                      # seam 4 + source_build/series_health
    db.execute(sa.text("INSERT INTO ops.contract_snapshot (endpoint,checked_at) "
                       "VALUES ('getAllQuotes','2026-08-25 08:00+07'), ('getAllQuotes','2026-08-25 09:00+07')"))
    n = db.execute(sa.text("SELECT count(*) FROM ops.contract_snapshot WHERE endpoint='getAllQuotes'")).scalar()
    assert n == 2
    db.execute(sa.text("INSERT INTO ops.source_build (source,bundle_hash) VALUES ('bvsc','3241ea7a')"))
    db.execute(sa.text("INSERT INTO ops.series_health (source,external_key,external_sub,days_since_change,"
                       "source_last_updated) VALUES ('wichart','xang_dau','0',76,NULL)"))
```
- [ ] **Step 2: Migration 0008**; `downgrade()` DROP 6 bảng. **Step 3: Xanh + Commit** — `feat(db): staging landing zone and ops tables`

---

### Task 9: Migration 0009 — role và grant (Sonnet)

**Files:** Create `0009_roles_grants.py`, `backend/tests/schema/test_s09_grants.py`
**Spec: step-01 §2** — `etl` ghi tất; `api` chỉ SELECT trên 4 schema miền, không thấy staging/ops.
- [ ] **Step 1: Test đỏ**:
```python
import sqlalchemy as sa

def test_grants_matrix(db):
    def can(role, priv, rel):
        return db.execute(sa.text("SELECT has_table_privilege(:r, :t, :p)"),
                          {"r": role, "t": rel, "p": priv}).scalar()
    assert can("dlck_etl", "INSERT", "market.price_daily") is True
    assert can("dlck_etl", "INSERT", "staging.raw_payload") is True
    assert can("dlck_api", "SELECT", "market.price_daily") is True
    assert can("dlck_api", "INSERT", "market.price_daily") is False
    ok_schema = db.execute(sa.text(
        "SELECT has_schema_privilege('dlck_api','staging','USAGE')")).scalar()
    assert ok_schema is False                                       # api không THẤY staging
    assert db.execute(sa.text(
        "SELECT has_schema_privilege('dlck_api','ops','USAGE')")).scalar() is False
```
Run → FAIL `role "dlck_etl" does not exist`.
- [ ] **Step 2: Migration 0009** — `op.execute`:
```sql
DO $$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='dlck_etl') THEN CREATE ROLE dlck_etl NOLOGIN; END IF;
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='dlck_api') THEN CREATE ROLE dlck_api NOLOGIN; END IF;
END $$;
GRANT USAGE ON SCHEMA market, macro, asset, news, staging, ops, extensions TO dlck_etl;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA market, macro, asset, news, staging, ops TO dlck_etl;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA market, macro, asset, news, staging, ops TO dlck_etl;
GRANT USAGE ON SCHEMA market, macro, asset, news, extensions TO dlck_api;
GRANT SELECT ON ALL TABLES IN SCHEMA market, macro, asset, news TO dlck_api;
ALTER DEFAULT PRIVILEGES IN SCHEMA market, macro, asset, news
  GRANT SELECT ON TABLES TO dlck_api;
ALTER DEFAULT PRIVILEGES IN SCHEMA market, macro, asset, news, staging, ops
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO dlck_etl;
```
`downgrade()`: REVOKE tương ứng + `DROP ROLE IF EXISTS dlck_api; DROP ROLE IF EXISTS dlck_etl;`
*(Login user cho từng môi trường tạo NGOÀI migration — `CREATE USER … IN ROLE dlck_etl` — ghi vào database/README ở Task 10; role là cluster-level nên downgrade phải REVOKE sạch trước khi DROP.)*
- [ ] **Step 3: Xanh + Commit** — `feat(db): writer/reader roles and schema grants`

---

### Task 10: Nghiệm thu toàn phần + database/README (Sonnet)

**Files:** Modify `database/README.md`
- [ ] **Step 1: Vòng nghiệm thu** (dán nguyên văn output vào ledger — verification-before-completion):
```bash
uv run --project backend alembic -c database/alembic.ini downgrade base
uv run --project backend alembic -c database/alembic.ini upgrade head
uv run --project backend pytest backend/tests/schema -v
```
Expected: downgrade/upgrade exit 0; pytest **toàn bộ PASS** (dự kiến ~25 test, 0 fail, 0 error).
- [ ] **Step 2: Kiểm object mồ côi sau downgrade** (seam bước 1 số 2):
```bash
uv run --project backend python -c "
import os, sqlalchemy as sa
from alembic import command; from alembic.config import Config
os.environ['DATA_DATABASE_URL']=os.environ['TEST_DATABASE_URL']
command.downgrade(Config('database/alembic.ini'),'base')
e=sa.create_engine(os.environ['TEST_DATABASE_URL'])
with e.connect() as c:
    left=[r[0] for r in c.execute(sa.text(\"SELECT nspname FROM pg_namespace WHERE nspname IN ('market','macro','asset','news','staging','ops','extensions')\"))]
print('LEFTOVER:', left); assert left==[]
"
```
Expected: `LEFTOVER: []`
- [ ] **Step 3: `database/README.md`** — viết lại (giữ bảng stack): trạng thái "schema postgres-data đã dựng — 9 migration", cách chạy (2 lệnh alembic + pytest + env vars), luật "DDL sửa qua migration mới, không sửa file cũ", ghi chú tạo login user per-env (`CREATE USER etl_worker LOGIN PASSWORD '…' IN ROLE dlck_etl;`), trỏ về spec folder. *(Index cùng lượt — §1.6.)*
- [ ] **Step 4: Commit** — `docs(db): database README - how to run migrations and tests`

---

### Task 11: Quét checklist §1.7 tài liệu sống (controller tự làm)

**Files:** Modify `docs/00-overview/architecture.md`, `docs/20-design/README.md`, `docs/20-design/market-data-store.md`, README plan (tick checklist)
- [ ] Thực hiện đúng 4 mục checklist trong [README plan](README.md) mục "Checklist quét tài liệu sống khi spec chốt xong": architecture §3.1/§3.2 (`organization` → `issuer`/`security`, khung ngành → `market.industry` — sửa href/lời văn, GIỮ ranh giới lịch sử); dòng "organization là nguồn sự thật duy nhất" ở `20-design/README.md`; banner ở `market-data-store.md` §5 trỏ sang spec folder + ghi override §9.6 cột source; đối chiếu news-pipeline §9.3 (đã khớp — chỉ tick).
- [ ] Chạy phép kiểm §1.7: `git grep -n "organization" docs/00-overview/architecture.md docs/20-design/README.md` — mọi hit còn lại hoặc đã đúng vai trò lịch sử hoặc đã sửa. Dán output vào ledger.
- [ ] Tick 4 ô checklist trong README plan; cập nhật bảng bước (thêm dòng plan ✅ thực thi xong). Commit — `docs: sync living docs with finalized postgres-data schema`

---

## Self-review (đã chạy khi viết plan)

1. **Spec coverage:** step-01 → Task 1+9; step-02 → Task 2+3; step-03 → Task 4; step-04 → Task 5; step-05 → Task 6; step-06 → Task 7; step-07 → Task 8; grants → Task 9; khép vòng + docs → Task 10+11. Bốn seam ETL chuyển plan sau — ghi tường minh ở đầu plan. Bước 8 spec (tầng tự tính) không thuộc plan này (theo README plan).
2. **Placeholder:** DDL trỏ section spec cụ thể kèm lệnh "copy nguyên văn" (spec là chủ sự thật, chép lại vào plan là bản sao thứ hai sẽ lệch — §1.7); mọi code plan-riêng (conftest, generator, seed, view spliced, hàm unaccent, grants, test) viết đầy đủ. Một ghi chú suy nghĩ trong Task 2 Step 1 được đánh dấu "XOÁ khi viết thật".
3. **Type consistency:** fixture `db`/`expect_violation` dùng thống nhất; tên bảng/cột khớp spec sau vòng 4 (`length_report`, `external_sub`, `via` trong PK, `volume_vnd`, `has_repo`, `calendar`, `source_last_updated`).
