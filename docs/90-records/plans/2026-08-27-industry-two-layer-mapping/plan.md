# Kế hoạch thực thi — Lát ngành hai lớp

> **Cho người thực thi:** dùng skill `superpowers:subagent-driven-development` (khuyến nghị) hoặc `superpowers:executing-plans`, làm từng task một. Mỗi bước là một checkbox `- [ ]`.

**Mục tiêu:** nạp bảng map ngành hai lớp vào Postgres và bật lớp 1 trong `etl refdata`, để mã mới niêm yết tự có ngành theo ICB còn phần gán tay đè lên không bị ETL ghi đè.

**Kiến trúc:** ba migration (đổi tên/mã ngành · bảng override + view đọc · seed nội dung) rồi một thay đổi trong `refdata_store.apply` gán `issuer.industry_id` theo luật *khớp chính xác trước, không có thì leo `icb_code_path` lấy tổ tiên gần nhất*. Lớp tay nằm ở bảng riêng `market.issuer_industry_override`, ETL không đọc không ghi; đường đọc là view `market.v_issuer_industry` = `COALESCE(tay, máy)`.

**Tech stack:** Python 3.12 · SQLAlchemy 2 Core (text SQL, không ORM) · Alembic · pytest trên Postgres thật (`dulieu_test`, dựng lại từ migration mỗi phiên).

**Spec:** [`spec.md`](spec.md) — đọc cùng plan này. Sổ rà nội dung lớp 2: [`layer2-review.md`](layer2-review.md).

---

## Global Constraints

- **Nhánh git:** `feat/industry-two-layer-mapping`. Repo đã có code sản phẩm ⇒ không commit thẳng `main` *(CLAUDE.md §4.7)*. Commit nhỏ, Conventional Commits, message tiếng Anh.
- **`PYTHONIOENCODING=utf-8`** cho mọi lệnh Python — không đặt sẽ crash cp1252 khi in tiếng Việt *(CLAUDE.md §5)*.
- **Nguồn nội dung map là [`docs/20-design/industry-mapping.json`](../../../20-design/industry-mapping.json)**, sinh từ `gen_industry_mapping.py`. **Cấm sửa tay** file `.md`/`.json`; sửa nội dung thì sửa trong script rồi chạy lại. File Excel ở `worksheets/` chỉ là ảnh chụp, **không phải nguồn nạp**.
- **Không sửa migration đã chạy trên DB thật** (`0001`–`0010`). Mọi thay đổi đi bằng revision mới.
- **Test chạy dưới đúng quyền production** — `SET LOCAL ROLE dlck_etl` cho mọi test chạm đường ETL, cả đường đọc lẫn đường ghi *(CLAUDE.md §3.5)*.
- **Tiêu chí nghiệm thu phải bất biến, không phải số thời điểm** *(CLAUDE.md §4.4.4)*. Số doanh nghiệp mỗi ngành đổi mỗi lần có mã mới niêm yết ⇒ **cấm** assert `VATLIEU == 90` trong test. Assert cái không đổi: *"0 doanh nghiệp có cổ phiếu niêm yết mà thiếu ngành"*, *"0 vi phạm luật BCTC"*, *"số dòng seed khớp file JSON"*.
- **Lệnh chạy test** *(từ [`database/README.md`](../../../../database/README.md))*:
  ```bash
  export TEST_DATABASE_URL="postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@127.0.0.1:5432/dulieu_test"
  cd backend && uv run pytest tests/schema tests/etl -v
  ```
  Fixture `migrated_engine` **xoá và dựng lại** `dulieu_test` từ `alembic upgrade head` mỗi phiên — migration mới tự động được kiểm.

---

## Trạng thái đo lại trước khi bắt đầu *(đo 2026-08-27, DB thật `dulieu`)*

Spec đo lúc 15:20 cùng ngày; đây là lần đo lại để plan không đứng trên số cũ.

| Đo | Kết quả |
|---|---|
| `alembic_version` | `0010` |
| `market.industry_icb_map` | **0 dòng** |
| `market.issuer` có `industry_id` | **0** / 1.550 issuer |
| `market.issuer_industry_override` | **chưa tồn tại** |
| `market.v_issuer_industry` | **chưa tồn tại** |
| Mã ngành level 2 trong DB | vẫn bộ CŨ: `BDS` `KCN` `VLXD` `TAINGUYEN` `YTEGD` `DIENNUOC` |
| `market.icb_industry` | 176 dòng |
| Lượt `market.refdata` gần nhất | success 08-27 01:00 |

**Mô phỏng luật phân giải trên dữ liệu thật** (chạy trong transaction rồi ROLLBACK, không ghi gì):

- 161/161 ticker lớp 2 **đều tìm được issuer** — 0 dòng rơi.
- 56/56 `icb_code` lớp 1 **đều có trong cây ICB** của nguồn.
- Lớp 1 phủ **1.550/1.550 issuer**, **0 issuer NULL** — kể cả trước khi áp lớp 2.
- Luật BCTC hai chiều: **0 vi phạm** sau khi áp cả hai lớp.
- Phân bố sau hai lớp, cổ phiếu `listed`, tổng **1.525**: `XAYDUNG 198 · TIENICH 143 · DANDUNG 117 · VANTAI 109 · VATLIEU 91 · YTE 89 · THUCPHAM 89 · DETMAY 72 · THIETBI 69 · NHUA 54 · DAUKHI 52 · DULICH 51 · KIMLOAI 44 · CHUNGKHOAN 42 · KHOANGSAN 40 · CONGNGHE 39 · HOACHAT 37 · BANLE 37 · KHUCONGNGHIEP 34 · THUYSAN 32 · NGANHANG 30 · NONGNGHIEP 29 · CAOSU 14 · BAOHIEM 13`.

🔴 **Ba điểm lệch với spec, phải biết trước khi code:**

1. **Seed lớp 1 là 55 dòng, không phải 56.** Dòng `8980` "Quỹ đầu tư" có `industry_code = null` (KHÔNG NẠP — ETF/quỹ không có ngành). Seed phải lọc `industry_code IS NOT NULL`.
2. **Phân bố lệch spec §7 đúng 1 dòng:** spec ghi `VATLIEU 90 · TIENICH 144`, đo lại được `VATLIEU 91 · TIENICH 143`. Nguyên nhân: `PTB` (ICB `1733`) có dòng lớp 2 đè sang `VATLIEU`, còn `TIENICH 144` của spec đếm cả `EGL` — cổ phiếu duy nhất `delisted` mà vẫn có issuer. Không phải lỗi map; là lệch cách đếm. **Lấy số đo lại làm chuẩn**, và vì lý do ở Global Constraints, **không đóng số này vào test**.
3. **Luật phân giải phải sắp theo VỊ TRÍ trong `icb_code_path`, không theo độ dài mã.** Mọi mã ICB đều 4 ký tự nên `ORDER BY length(icb_code) DESC` là tie-break rỗng nghĩa — tổ tiên cấp 2 và cấp 3 sẽ tranh nhau không xác định. Dùng `array_position(string_to_array(path,'/'), icb_code) DESC` (phần tử càng cuối path càng gần lá).

---

## Cấu trúc file

| File | Trách nhiệm |
|---|---|
| `database/migrations/versions/0011_industry_rename.py` | **Tạo** — đổi 6 code + 7 tên ở `market.industry` |
| `database/migrations/versions/0012_industry_override.py` | **Tạo** — bảng `issuer_industry_override`, view `v_issuer_industry`, thu hồi quyền ghi của `dlck_etl` trên bảng override |
| `database/migrations/versions/0013_seed_industry_map.py` | **Tạo** — seed 55 dòng `industry_icb_map` + 161 dòng override |
| `backend/etl/refdata_store.py` | **Sửa** — thêm bước gán lớp 1 sau khi upsert issuer |
| `backend/tests/schema/test_s02_identity.py:5-10` | **Sửa** — literal 24 mã ngành theo bộ mới |
| `backend/tests/schema/test_s11_industry_override.py` | **Tạo** — seam bảng override, view, quyền, đối chiếu seed ↔ JSON |
| `backend/tests/etl/test_e09_refdata_store.py:82-105` | **Sửa** — viết lại test *tay thắng máy*; thêm test luật phân giải và luật BCTC |
| `docs/20-design/industry-tree.md` · `docs/20-design/README.md` · `docs/00-overview/roadmap.md` · `database/README.md` | **Sửa** — đồng bộ tài liệu sống |
| `docs/90-records/plans/2026-08-27-industry-two-layer-mapping/ledger.md` | **Tạo** — sổ ghi thực thi |

---

### Task 0: Nhánh làm việc

- [ ] **Bước 1: Tạo nhánh**

```bash
git checkout -b feat/industry-two-layer-mapping
git status --short   # phải sạch
```

---

### Task 1: Migration 0011 — đổi 6 mã và 7 tên ngành

**Files:**
- Create: `database/migrations/versions/0011_industry_rename.py`
- Modify: `backend/tests/schema/test_s02_identity.py:5-10`

**Interfaces:**
- Produces: bộ 24 mã ngành level 2 mới — `DANDUNG` `KHUCONGNGHIEP` `VATLIEU` `KHOANGSAN` `YTE` `TIENICH` thay cho `BDS` `KCN` `VLXD` `TAINGUYEN` `YTEGD` `DIENNUOC`. Task 3 seed theo mã mới; không đổi trước thì seed chết vì không tìm thấy `industry.code`.

- [ ] **Bước 1: Viết test đỏ** — sửa literal trong `backend/tests/schema/test_s02_identity.py`

```python
L2 = {"NGANHANG","CHUNGKHOAN","BAOHIEM","DANDUNG","KHUCONGNGHIEP","XAYDUNG","VATLIEU",
      "KIMLOAI","KHOANGSAN","HOACHAT","NHUA","THIETBI",
      "NONGNGHIEP","THUYSAN","DETMAY","CAOSU",
      "BANLE","THUCPHAM","DULICH","YTE",
      "TIENICH","DAUKHI","VANTAI","CONGNGHE"}   # literal từ industry-tree.md §2
```

Thêm ngay dưới, cùng file, một test khoá **tên** (bản cũ chỉ khoá mã nên 7 tên đổi sẽ trôi không ai biết):

```python
NAMES = {                                        # literal từ industry-tree.md §2
    "DANDUNG": "Bất động sản Dân dụng",
    "KHUCONGNGHIEP": "Bất động sản Khu công nghiệp",
    "VATLIEU": "Vật liệu Xây dựng",
    "KHOANGSAN": "Than và Khoáng sản",
    "NHUA": "Nhựa, Bao bì và Giấy",
    "DETMAY": "Dệt may, Gỗ và Gia dụng",
    "DULICH": "Hàng không, Du lịch và Truyền thông",
    "YTE": "Y tế, Giáo dục và Xuất bản",
    "TIENICH": "Điện, Nước và Môi trường",
    "DAUKHI": "Dầu mỏ và Khí đốt",
}


def test_industry_names_match_tree(db):
    rows = dict(db.execute(sa.text(
        "SELECT code, name_vi FROM market.industry WHERE level=2")).all())
    assert {c: rows[c] for c in NAMES} == NAMES
```

- [ ] **Bước 2: Chạy để thấy đỏ**

Run: `cd backend && uv run pytest tests/schema/test_s02_identity.py -v`
Expected: FAIL — `test_industry_seed_matches_tree` báo set lệch (`BDS`/`KCN`/… còn trong DB), `test_industry_names_match_tree` báo `KeyError: 'DANDUNG'`.

- [ ] **Bước 3: Viết migration**

```python
"""rename industry codes and names (industry-tree.md §2, rà 2026-08-27)

Revision ID: 0011
Revises: 0010
Create Date: 2026-08-27

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0011"
down_revision: Union[str, None] = "0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (code cũ, code mới, tên mới) — nội dung do docs/20-design/industry-tree.md §2 sở hữu.
RENAMES = [
    ("BDS", "DANDUNG", "Bất động sản Dân dụng"),
    ("KCN", "KHUCONGNGHIEP", "Bất động sản Khu công nghiệp"),
    ("VLXD", "VATLIEU", "Vật liệu Xây dựng"),
    ("TAINGUYEN", "KHOANGSAN", "Than và Khoáng sản"),
    ("YTEGD", "YTE", "Y tế, Giáo dục và Xuất bản"),
    ("DIENNUOC", "TIENICH", "Điện, Nước và Môi trường"),
]
# Đổi tên mà giữ nguyên code.
RETITLES = [
    ("NHUA", "Nhựa, Bao bì và Giấy"),
    ("DETMAY", "Dệt may, Gỗ và Gia dụng"),
    ("DULICH", "Hàng không, Du lịch và Truyền thông"),
    ("DAUKHI", "Dầu mỏ và Khí đốt"),
]
OLD = {
    "DANDUNG": ("BDS", "Bất động sản Dân dụng"),
    "KHUCONGNGHIEP": ("KCN", "Bất động sản Khu công nghiệp"),
    "VATLIEU": ("VLXD", "Vật liệu Xây dựng"),
    "KHOANGSAN": ("TAINGUYEN", "Tài nguyên Cơ bản"),
    "YTE": ("YTEGD", "Dược phẩm, Y tế và Giáo dục"),
    "TIENICH": ("DIENNUOC", "Điện, Nước và Khí đốt"),
    "NHUA": ("NHUA", "Nhựa và Bao bì"),
    "DETMAY": ("DETMAY", "Dệt may và Gia dụng"),
    "DULICH": ("DULICH", "Hàng không, Du lịch và Giải trí"),
    "DAUKHI": ("DAUKHI", "Dầu khí và Nhiên liệu"),
}


def upgrade() -> None:
    conn = op.get_bind()
    for old, new, name in RENAMES:
        conn.exec_driver_sql(
            "UPDATE market.industry SET code = %s, name_vi = %s WHERE code = %s",
            (new, name, old),
        )
    for code, name in RETITLES:
        conn.exec_driver_sql(
            "UPDATE market.industry SET name_vi = %s WHERE code = %s", (name, code)
        )


def downgrade() -> None:
    conn = op.get_bind()
    for new, (old, name) in OLD.items():
        conn.exec_driver_sql(
            "UPDATE market.industry SET code = %s, name_vi = %s WHERE code = %s",
            (old, name, new),
        )
```

⚠️ `industry_id` **không đổi** — chỉ `code`/`name_vi`. Mọi FK trỏ vào `industry_id` nên không có gì gãy. `market.issuer.industry_id` đang toàn NULL nên lượt đổi này không chạm dữ liệu doanh nghiệp nào.

- [ ] **Bước 4: Chạy để thấy xanh**

Run: `cd backend && uv run pytest tests/schema/test_s02_identity.py -v`
Expected: PASS toàn bộ (fixture dựng lại `dulieu_test` tới `head` = `0011`).

- [ ] **Bước 5: Kiểm migration ngược**

```bash
cd database && uv run alembic downgrade 0010 && uv run alembic upgrade head
```
Expected: cả hai lệnh thoát 0, không traceback.

- [ ] **Bước 6: Commit**

```bash
git add database/migrations/versions/0011_industry_rename.py backend/tests/schema/test_s02_identity.py
git commit -m "feat(db): rename 6 industry codes and 7 names per industry-tree review"
```

---

### Task 2: Migration 0012 — bảng override, view đọc, thu hồi quyền ghi của ETL

**Files:**
- Create: `database/migrations/versions/0012_industry_override.py`
- Create: `backend/tests/schema/test_s11_industry_override.py`

**Interfaces:**
- Consumes: bộ mã ngành mới của Task 1.
- Produces: `market.issuer_industry_override(issuer_id PK, industry_id, note, updated_at)` và view `market.v_issuer_industry(issuer_id, industry_id, source)` với `source ∈ {'manual','icb',NULL}`. Task 3 seed vào bảng này; Task 5–6 nghiệm thu trên view.

**Quyết định đi kèm, ghi rõ để người sau không tưởng là thừa:** migration `0009` cấp `INSERT/UPDATE/DELETE` trên **mọi bảng** schema `market` cho `dlck_etl`, và `ALTER DEFAULT PRIVILEGES` khiến bảng mới cũng tự có. Spec nói *"ETL không đọc, không ghi"* bảng override — nếu chỉ ghi luật đó trong comment thì nó là luật giấy. `0012` **REVOKE** quyền ghi để DB tự chặn, đúng nguyên tắc *một bảng một người ghi*.

- [ ] **Bước 1: Viết test đỏ** — tạo `backend/tests/schema/test_s11_industry_override.py`

```python
import sqlalchemy as sa

from conftest import expect_violation


def _issuer(db, name="DN thử", icb="8355", com="NH"):
    return db.execute(sa.text(
        "INSERT INTO market.issuer (name, com_type_code, icb_code) "
        "VALUES (:n,:c,:i) RETURNING issuer_id"),
        {"n": name, "c": com, "i": icb}).scalar_one()


def _ind(db, code):
    return db.execute(sa.text(
        "SELECT industry_id FROM market.industry WHERE code=:c"), {"c": code}).scalar_one()


def test_override_note_is_mandatory(db):                 # seam 1: không cho đè vô danh
    iid, ind = _issuer(db), _ind(db, "DANDUNG")
    assert expect_violation(
        db,
        "INSERT INTO market.issuer_industry_override (issuer_id, industry_id, note) "
        "VALUES (:i, :d, NULL)", {"i": iid, "d": ind})


def test_override_one_row_per_issuer(db):                # seam 2: PK issuer_id
    iid, ind = _issuer(db), _ind(db, "DANDUNG")
    db.execute(sa.text(
        "INSERT INTO market.issuer_industry_override (issuer_id, industry_id, note) "
        "VALUES (:i,:d,'lần 1')"), {"i": iid, "d": ind})
    assert expect_violation(
        db,
        "INSERT INTO market.issuer_industry_override (issuer_id, industry_id, note) "
        "VALUES (:i,:d,'lần 2')", {"i": iid, "d": ind})


def test_view_prefers_manual_over_icb(db):               # seam 3: COALESCE + cột source
    iid = _issuer(db)
    icb_ind, man_ind = _ind(db, "XAYDUNG"), _ind(db, "DANDUNG")
    db.execute(sa.text("UPDATE market.issuer SET industry_id=:d WHERE issuer_id=:i"),
               {"d": icb_ind, "i": iid})
    assert db.execute(sa.text(
        "SELECT industry_id, source FROM market.v_issuer_industry WHERE issuer_id=:i"),
        {"i": iid}).one() == (icb_ind, "icb")
    db.execute(sa.text(
        "INSERT INTO market.issuer_industry_override (issuer_id, industry_id, note) "
        "VALUES (:i,:d,'đè tay')"), {"i": iid, "d": man_ind})
    assert db.execute(sa.text(
        "SELECT industry_id, source FROM market.v_issuer_industry WHERE issuer_id=:i"),
        {"i": iid}).one() == (man_ind, "manual")


def test_view_source_is_null_when_no_industry(db):       # seam 3, ca biên
    iid = _issuer(db)
    assert db.execute(sa.text(
        "SELECT industry_id, source FROM market.v_issuer_industry WHERE issuer_id=:i"),
        {"i": iid}).one() == (None, None)


def test_etl_role_cannot_write_override(db):             # seam 4: luật một bảng một người ghi
    iid, ind = _issuer(db), _ind(db, "DANDUNG")
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    nested = db.begin_nested()
    try:
        db.execute(sa.text(
            "INSERT INTO market.issuer_industry_override (issuer_id, industry_id, note) "
            "VALUES (:i,:d,'etl không được ghi')"), {"i": iid, "d": ind})
        nested.commit()
        denied = False
    except sa.exc.ProgrammingError as e:
        nested.rollback()
        denied = "permission denied" in str(e).lower()
    assert denied


def test_etl_role_can_read_view(db):                     # seam 4b: đường ĐỌC của production
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    db.execute(sa.text("SELECT count(*) FROM market.v_issuer_industry")).scalar_one()


def test_api_role_can_read_view(db):                     # seam 4c: đường đọc của API
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    db.execute(sa.text("SELECT count(*) FROM market.v_issuer_industry")).scalar_one()
```

- [ ] **Bước 2: Chạy để thấy đỏ**

Run: `cd backend && uv run pytest tests/schema/test_s11_industry_override.py -v`
Expected: FAIL — `UndefinedTable: relation "market.issuer_industry_override" does not exist`.

- [ ] **Bước 3: Viết migration**

```python
"""issuer_industry_override + v_issuer_industry (spec §2)

Revision ID: 0012
Revises: 0011
Create Date: 2026-08-27

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0012"
down_revision: Union[str, None] = "0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        -- LỚP 2 — gán tay, người ghi, ETL KHÔNG đọc KHÔNG ghi (spec §2).
        CREATE TABLE market.issuer_industry_override (
          issuer_id   bigint PRIMARY KEY REFERENCES market.issuer,
          industry_id bigint NOT NULL REFERENCES market.industry,  -- luôn level 2
          note        text NOT NULL,                               -- vì sao đè — bắt buộc
          updated_at  timestamptz NOT NULL DEFAULT now(),
          CONSTRAINT note_not_blank CHECK (btrim(note) <> '')
        );

        -- ĐƯỜNG ĐỌC DUY NHẤT của ngành doanh nghiệp. Đọc thẳng issuer.industry_id là
        -- bỏ qua lớp tay — mọi truy vấn hiển thị/phân tích phải qua view này.
        CREATE VIEW market.v_issuer_industry AS
        SELECT i.issuer_id,
               COALESCE(o.industry_id, i.industry_id) AS industry_id,
               CASE WHEN o.industry_id IS NOT NULL THEN 'manual'
                    WHEN i.industry_id IS NOT NULL THEN 'icb'
               END AS source
        FROM market.issuer i
        LEFT JOIN market.issuer_industry_override o USING (issuer_id);

        -- 0009 cấp quyền ghi cho dlck_etl trên MỌI bảng market (kèm default privileges).
        -- Bảng này là của NGƯỜI: thu hồi để luật "ETL không ghi" do DB gác, không do comment gác.
        REVOKE INSERT, UPDATE, DELETE ON market.issuer_industry_override FROM dlck_etl;
        GRANT SELECT ON market.v_issuer_industry TO dlck_etl, dlck_api;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP VIEW IF EXISTS market.v_issuer_industry;
        DROP TABLE IF EXISTS market.issuer_industry_override;
        """
    )
```

- [ ] **Bước 4: Chạy để thấy xanh**

Run: `cd backend && uv run pytest tests/schema/test_s11_industry_override.py -v`
Expected: PASS 7/7.

- [ ] **Bước 5: Chạy cả bộ schema để chắc không vỡ chỗ khác**

Run: `cd backend && uv run pytest tests/schema -v`
Expected: PASS toàn bộ (`test_s09_grants.py` và `test_s10_registry_ts.py` không được đỏ).

- [ ] **Bước 6: Commit**

```bash
git add database/migrations/versions/0012_industry_override.py backend/tests/schema/test_s11_industry_override.py
git commit -m "feat(db): manual industry override table and read view"
```

---

### Task 3: Migration 0013 — seed 55 dòng ICB map + 161 dòng override

**Files:**
- Create: `database/migrations/versions/0013_seed_industry_map.py`
- Modify: `backend/tests/schema/test_s11_industry_override.py` (thêm test đối chiếu seed ↔ JSON)

**Interfaces:**
- Consumes: bảng của Task 2, mã ngành của Task 1.
- Produces: nội dung `market.industry_icb_map`; Task 4 tra bảng này.

**Hai điều phải hiểu trước khi viết:**

1. **Seed ICB map = 55 dòng.** JSON có 56 dòng lớp 1; dòng `8980` mang `industry_code: null` (KHÔNG NẠP — ETF/quỹ không có ngành). Lọc `industry_code IS NOT NULL`.
2. **Seed override phụ thuộc dữ liệu.** Bảng khoá theo `issuer_id`, còn worksheet khoá theo **ticker** ⇒ phải join `market.security` → `issuer_id`. Trên DB thật khớp đủ 161/161 *(đo 2026-08-27)*; trên `dulieu_test` vừa dựng, `market.issuer` **rỗng** nên seed nạp **0 dòng** — đó là hành vi đúng, không phải lỗi. Vì vậy migration **không được** `RAISE EXCEPTION` khi thiếu ticker; chỉ `RAISE NOTICE` số dòng nạp được. Kiểm 161/161 là việc của nghiệm thu trên DB thật (Task 6).
   ⚠️ **Giới hạn đã biết, ghi vào tài liệu:** seed chạy một lần. Ticker lớp 2 mà issuer xuất hiện *sau* lượt migration sẽ không có override. Hiện không mã nào rơi vào ca này; câu kiểm ở Task 6 phát hiện được nếu về sau có.

- [ ] **Bước 1: Viết test đỏ** — thêm vào `backend/tests/schema/test_s11_industry_override.py`

```python
import json
import pathlib

MAP_JSON = pathlib.Path(__file__).resolve().parents[3] / "docs" / "20-design" / "industry-mapping.json"


def test_icb_map_seed_matches_json(db):                  # seam 5: seed không trôi khỏi tài liệu
    doc = json.loads(MAP_JSON.read_text(encoding="utf-8"))
    want = {r["icb_code"]: r["industry_code"]
            for r in doc["layer1"] if r["industry_code"] is not None}
    got = dict(db.execute(sa.text(
        "SELECT m.icb_code, i.code FROM market.industry_icb_map m "
        "JOIN market.industry i USING (industry_id)")).all())
    assert got == want
    assert len(want) == 55                               # 56 dòng lớp 1 trừ 8980 không nạp


def test_icb_map_targets_level_2_only(db):               # seam 5, ca biên
    assert db.execute(sa.text(
        "SELECT count(*) FROM market.industry_icb_map m JOIN market.industry i "
        "USING (industry_id) WHERE i.level <> 2")).scalar_one() == 0
```

- [ ] **Bước 2: Chạy để thấy đỏ**

Run: `cd backend && uv run pytest tests/schema/test_s11_industry_override.py -k seed_matches -v`
Expected: FAIL — `assert {} == {...}` (bảng rỗng).

- [ ] **Bước 3: Sinh phần thân migration từ JSON**

Không gõ tay 216 dòng. Chạy lệnh sau, dán kết quả vào chỗ đánh dấu ở Bước 4:

```bash
PYTHONIOENCODING=utf-8 python - <<'PY'
import json
d = json.load(open('docs/20-design/industry-mapping.json', encoding='utf-8'))
l1 = [r for r in d['layer1'] if r['industry_code']]
print('-- L1 VALUES (%d dòng):' % len(l1))
print(',\n'.join("         ('%s','%s')" % (r['icb_code'], r['industry_code']) for r in l1))
print('-- L2 VALUES (%d dòng):' % len(d['layer2']))
print(',\n'.join("         ('%s','%s','%s')" % (r['ticker'], r['industry_code'],
      r['reason'].replace("'", "''")) for r in d['layer2']))
PY
```

- [ ] **Bước 4: Viết migration**

```python
"""seed industry_icb_map (55) + issuer_industry_override (161)

Revision ID: 0013
Revises: 0012
Create Date: 2026-08-27

Nội dung do docs/20-design/industry-mapping.json sở hữu (sinh từ
gen_industry_mapping.py). Hai bảng này KHÔNG có đường ghi runtime nên seed ở
migration là đúng chỗ — khác market.security, nơi ETL ghi hằng ngày.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0013"
down_revision: Union[str, None] = "0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        -- LỚP 1 — 55 dòng (56 dòng worksheet trừ 8980 'Quỹ đầu tư' KHÔNG NẠP).
        -- Trộn cấp 3 (nền cả nhánh) với cấp 4 (ngoại lệ) là CỐ Ý: luật phân giải
        -- khớp chính xác trước, không có thì leo icb_code_path lấy tổ tiên gần nhất.
        INSERT INTO market.industry_icb_map (icb_code, industry_id)
        SELECT v.icb_code, i.industry_id
        FROM (VALUES
<<< dán khối L1 VALUES từ Bước 3 >>>
        ) AS v(icb_code, industry_code)
        JOIN market.industry i ON i.code = v.industry_code AND i.level = 2;

        -- LỚP 2 — 161 dòng gán tay. Khoá theo ticker ở worksheet, đổi sang issuer_id
        -- qua market.security. Ticker chưa có issuer thì BỎ QUA (DB test rỗng issuer
        -- ⇒ nạp 0 dòng, đúng hành vi mong đợi).
        INSERT INTO market.issuer_industry_override (issuer_id, industry_id, note)
        SELECT DISTINCT ON (s.issuer_id) s.issuer_id, i.industry_id, v.reason
        FROM (VALUES
<<< dán khối L2 VALUES từ Bước 3 >>>
        ) AS v(ticker, industry_code, reason)
        JOIN market.security s ON s.ticker = v.ticker AND s.issuer_id IS NOT NULL
        JOIN market.industry i ON i.code = v.industry_code AND i.level = 2
        ORDER BY s.issuer_id, s.security_id
        ON CONFLICT (issuer_id) DO NOTHING;

        DO $$
        DECLARE n int;
        BEGIN
          SELECT count(*) INTO n FROM market.issuer_industry_override;
          RAISE NOTICE 'seed lop 2: % dong override (worksheet co 161 ticker)', n;
        END $$;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM market.issuer_industry_override;
        DELETE FROM market.industry_icb_map;
        """
    )
```

⚠️ `DISTINCT ON (s.issuer_id)` là chốt chặn thật: một doanh nghiệp có thể có nhiều mã (`security`), và hai ticker cùng issuer trong worksheet sẽ nổ PK nếu không gộp.

- [ ] **Bước 5: Chạy để thấy xanh**

Run: `cd backend && uv run pytest tests/schema/test_s11_industry_override.py -v`
Expected: PASS 9/9.

- [ ] **Bước 6: Commit**

```bash
git add database/migrations/versions/0013_seed_industry_map.py backend/tests/schema/test_s11_industry_override.py
git commit -m "feat(db): seed ICB industry map and manual overrides"
```

---

### Task 4: Lớp 1 trong `refdata_store` — ETL gán `issuer.industry_id`

**Files:**
- Modify: `backend/etl/refdata_store.py` (docstring đầu file + hàm `apply`)
- Modify: `backend/tests/etl/test_e09_refdata_store.py:82-105`

**Interfaces:**
- Consumes: `market.industry_icb_map` (Task 3), `market.icb_industry.icb_code_path` (đã có, job tự nạp ở bước 4 của `apply`).
- Produces: `apply()` trả thêm khoá `stats["industry_unmapped"]` — số issuer không tra được ngành sau lượt gán. `refdata_job` đã ghi nguyên `apply_stats` vào `ops.etl_run.stats` nên không phải sửa `refdata_job.py`.

**Ba luật phải cài đúng:**
- Gán chạy **sau** bước 4 (`icb_industry`) — luật phân giải cần `icb_code_path` của lượt hiện tại.
- Tổ tiên gần nhất = **phần tử cuối nhất trong `icb_code_path`**, sắp bằng `array_position(...) DESC`. Mọi mã ICB đều 4 ký tự nên sắp theo độ dài là tie-break rỗng nghĩa.
- Câu UPDATE có đuôi `IS DISTINCT FROM` để `updated_at` không nhảy khi ngành không đổi — cùng luật với các bước trên trong `apply`.

- [ ] **Bước 1: Viết test đỏ** — thay `test_manual_industry_assignment_survives_rerun` trong `backend/tests/etl/test_e09_refdata_store.py` bằng bốn test dưới

```python
def _seed_map(db, icb_code, industry_code):
    """Thêm một dòng map bằng quyền owner (bảng seed, ETL không ghi)."""
    db.execute(sa.text("RESET ROLE"))
    db.execute(sa.text(
        "INSERT INTO market.industry_icb_map (icb_code, industry_id) "
        "SELECT :c, industry_id FROM market.industry WHERE code = :i "
        "ON CONFLICT (icb_code) DO UPDATE SET industry_id = EXCLUDED.industry_id"),
        {"c": icb_code, "i": industry_code})
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))


def _industry_of(db, organ_code):
    return db.execute(sa.text(
        "SELECT i.code FROM market.issuer iss "
        " JOIN market.issuer_external_id e ON e.issuer_id = iss.issuer_id"
        " LEFT JOIN market.industry i ON i.industry_id = iss.industry_id"
        " WHERE e.source='fiintrade' AND e.external_code=:o"), {"o": organ_code}).scalar_one()


def _icb_of(db, organ_code):
    return db.execute(sa.text(
        "SELECT iss.icb_code FROM market.issuer iss JOIN market.issuer_external_id e"
        " USING (issuer_id) WHERE e.source='fiintrade' AND e.external_code=:o"),
        {"o": organ_code}).scalar_one()


def _path_of(db, icb_code):
    return db.execute(sa.text(
        "SELECT icb_code_path FROM market.icb_industry WHERE icb_code=:c"),
        {"c": icb_code}).scalar_one().split("/")


def test_layer1_exact_icb_match_wins_over_ancestor(db):          # seam: luật phân giải
    _as_etl(db)
    t = _target()
    refdata_store.apply(db, t, [])
    icb = _icb_of(db, "NHN")
    _seed_map(db, _path_of(db, icb)[-2], "XAYDUNG")               # cha trực tiếp
    _seed_map(db, icb, "DANDUNG")                                 # khớp chính xác
    refdata_store.apply(db, t, [])
    assert _industry_of(db, "NHN") == "DANDUNG"


def test_layer1_climbs_path_to_nearest_ancestor(db):             # seam: leo path
    _as_etl(db)
    t = _target()
    refdata_store.apply(db, t, [])
    parts = _path_of(db, _icb_of(db, "NHN"))
    _seed_map(db, parts[0], "XAYDUNG")                            # tổ tiên XA
    _seed_map(db, parts[-2], "TIENICH")                           # tổ tiên GẦN NHẤT
    refdata_store.apply(db, t, [])
    assert _industry_of(db, "NHN") == "TIENICH"


def test_layer1_unknown_icb_stays_null_and_counts(db):           # ca sai: không chặn job
    _as_etl(db)
    t = _target()
    stats = refdata_store.apply(db, t, [])                        # map rỗng ⇒ không ai tra được
    assert _industry_of(db, "NHN") is None
    assert stats["industry_unmapped"] > 0


def test_manual_override_survives_while_layer1_refreshes(db):    # spec §8.5 — tay thắng máy
    _as_etl(db)
    t = _target()
    refdata_store.apply(db, t, [])
    icb = _icb_of(db, "NHN")
    iid = db.execute(sa.text(
        "SELECT issuer_id FROM market.issuer_external_id"
        " WHERE source='fiintrade' AND external_code='NHN'")).scalar_one()
    _seed_map(db, icb, "XAYDUNG")
    refdata_store.apply(db, t, [])
    assert _industry_of(db, "NHN") == "XAYDUNG"

    db.execute(sa.text("RESET ROLE"))                             # người đè tay
    db.execute(sa.text(
        "INSERT INTO market.issuer_industry_override (issuer_id, industry_id, note)"
        " SELECT :i, industry_id, 'đè tay trong test' FROM market.industry WHERE code='DANDUNG'"),
        {"i": iid})
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))

    _seed_map(db, icb, "TIENICH")                                 # sửa map ICB
    refdata_store.apply(db, t, [])
    row = db.execute(sa.text(
        "SELECT i.code, v.source FROM market.v_issuer_industry v"
        " JOIN market.industry i ON i.industry_id = v.industry_id"
        " WHERE v.issuer_id = :i"), {"i": iid}).one()
    assert row == ("DANDUNG", "manual")                           # tay THẮNG máy
    assert _industry_of(db, "NHN") == "TIENICH"                   # mà lớp 1 VẪN refresh
```

Test cuối là chỗ **đảo luật cũ**: bản cũ khẳng định ETL không bao giờ chạm `industry_id`; nay ETL sở hữu cột đó, còn tay nằm bảng khác. Test cũ đỏ là dấu hiệu đúng, không phải hồi quy.

- [ ] **Bước 2: Chạy để thấy đỏ**

Run: `cd backend && uv run pytest tests/etl/test_e09_refdata_store.py -v`
Expected: FAIL 4 test mới — `KeyError: 'industry_unmapped'` và `assert None == 'DANDUNG'` (chưa có code gán).

- [ ] **Bước 3: Viết implementation** — thêm vào `backend/etl/refdata_store.py`, ngay **sau** khối `# 4b.` và **trước** `# 5. delist`

```python
    # 4c. LỚP 1 — gán industry_id theo industry_icb_map (spec lát ngành hai lớp §2).
    # ETL SỞ HỮU cột này: sửa map ICB rồi chạy lại job là toàn bộ doanh nghiệp cập nhật
    # theo. Lớp tay nằm ở market.issuer_industry_override, ETL không đọc không ghi.
    # Luật phân giải: khớp icb_code chính xác trước; không có thì leo icb_code_path lấy
    # TỔ TIÊN GẦN NHẤT — gần nhất = ở VỊ TRÍ cuối nhất trong path (mọi mã ICB đều 4 ký
    # tự nên sắp theo độ dài là tie-break rỗng nghĩa).
    conn.execute(
        sa.text(
            "UPDATE market.issuer iss SET industry_id = r.industry_id, updated_at = now()"
            " FROM ("
            "   SELECT i.issuer_id, COALESCE("
            "     (SELECT m.industry_id FROM market.industry_icb_map m"
            "       WHERE m.icb_code = i.icb_code),"
            "     (SELECT m.industry_id FROM market.icb_industry t"
            "        JOIN market.industry_icb_map m"
            "          ON m.icb_code = ANY(string_to_array(t.icb_code_path, '/'))"
            "       WHERE t.icb_code = i.icb_code"
            "       ORDER BY array_position(string_to_array(t.icb_code_path, '/'), m.icb_code)"
            "         DESC LIMIT 1)"
            "   ) AS industry_id"
            "   FROM market.issuer i"
            " ) AS r"
            " WHERE iss.issuer_id = r.issuer_id"
            "   AND iss.industry_id IS DISTINCT FROM r.industry_id"
        )
    )
    stats["industry_unmapped"] = conn.execute(
        sa.text("SELECT count(*) FROM market.issuer WHERE industry_id IS NULL")
    ).scalar_one()
    if stats["industry_unmapped"]:
        log.warning(
            "%d doanh nghiệp không tra được ngành từ industry_icb_map — để NULL, không chặn job",
            stats["industry_unmapped"],
        )
```

Sửa docstring đầu file: dòng ``  `industry_id` KHÔNG BAO GIỜ nằm trong UPDATE — tay thắng máy.`` thành

```
- `issuer` nhận diện qua `issuer_external_id('fiintrade', organ_code)`, KHÔNG qua tên.
  `industry_id` do ETL SỞ HỮU (bước 4c, lớp 1 theo `industry_icb_map`); lớp tay nằm ở
  `market.issuer_industry_override`, ETL không đọc không ghi. Đường đọc:
  `market.v_issuer_industry` = COALESCE(tay, máy).
```

Sửa luôn comment `# industry_id KHÔNG có mặt ở đây — tay thắng máy (spec §5).` trong nhánh UPDATE issuer thành `# industry_id gán ở bước 4c (lớp 1) — không nhét vào câu này để updated_at không nhảy oan.`

- [ ] **Bước 4: Chạy để thấy xanh**

Run: `cd backend && uv run pytest tests/etl -v`
Expected: PASS toàn bộ. Chú ý `test_apply_twice_is_idempotent_including_timestamps` **phải vẫn xanh** — nếu đỏ nghĩa là đuôi `IS DISTINCT FROM` sai và `updated_at` nhảy ở lượt hai.

- [ ] **Bước 5: Commit**

```bash
git add backend/etl/refdata_store.py backend/tests/etl/test_e09_refdata_store.py
git commit -m "feat(etl): assign issuer industry from ICB map on every refdata run"
```

---

### Task 5: Test luật BCTC trên view — nghiệm thu bắt buộc của spec §2b

**Files:**
- Modify: `backend/tests/etl/test_e09_refdata_store.py` (thêm 1 test)

**Interfaces:**
- Consumes: view của Task 2, gán lớp 1 của Task 4, helper `_seed_map`/`_icb_of` của Task 4.

Spec §2b bắt buộc có test này: *"Không có test này thì lần sửa `industry_icb_map` sau sẽ lại lọt — chính lớp 1 vừa lọt 6 mã mà không ai biết cho tới khi đo."* Test khẳng định **quan hệ hai chiều**, không khẳng định con số thời điểm.

- [ ] **Bước 1: Viết test**

```python
BCTC_PROBE = (
    "SELECT iss.com_type_code, i.code FROM market.issuer iss"
    " JOIN market.v_issuer_industry v ON v.issuer_id = iss.issuer_id"
    " JOIN market.industry i ON i.industry_id = v.industry_id"
    " WHERE (iss.com_type_code = 'NH') <> (i.code = 'NGANHANG')"
    "    OR (iss.com_type_code = 'CK') <> (i.code = 'CHUNGKHOAN')"
    "    OR (iss.com_type_code = 'BH') <> (i.code = 'BAOHIEM')"
)


def test_bctc_rule_is_bidirectional_on_view(db):
    """com_type_code NH|CK|BH ⟺ ngành NGANHANG|CHUNGKHOAN|BAOHIEM, không ngoại lệ."""
    _as_etl(db)
    t = _target()
    refdata_store.apply(db, t, [])
    icb = _icb_of(db, "NHN")                      # NHN là com_type_code 'CT'
    _seed_map(db, icb, "NGANHANG")                # cố tình đẩy một DN 'CT' vào ngành ngân hàng
    refdata_store.apply(db, t, [])
    assert db.execute(sa.text(BCTC_PROBE)).all(), \
        "câu dò vi phạm phải BẮT được ca dựng sẵn — nếu rỗng thì chính nó hỏng"

    _seed_map(db, icb, "DANDUNG")                 # trả về đúng
    refdata_store.apply(db, t, [])
    assert db.execute(sa.text(BCTC_PROBE)).all() == []
```

Hai nửa là cố ý: nửa đầu chứng minh câu dò **bắt được** vi phạm (chống test luôn xanh), nửa sau khẳng định trạng thái sạch. Trước khi chạy, kiểm `com_type_code` của `NHN` trong fixture — nếu không phải `CT` thì đổi sang một `organ_code` khác có `com_type_code = 'CT'`:

```bash
cd backend && PYTHONIOENCODING=utf-8 python -c "import json;d=json.load(open('tests/etl/fixtures/refdata/organization.json',encoding='utf-8'));print([(x.get('organCode'),x.get('comTypeCode')) for x in (d.get('items') or d.get('data') or d)][:20])"
```

- [ ] **Bước 2: Kiểm test có thật sự bắt lỗi — thí nghiệm đột biến**

Tạm comment khối `# 4c.` ở `refdata_store.py`, chạy lại:

Run: `cd backend && uv run pytest tests/etl/test_e09_refdata_store.py -v`
Expected: FAIL. Trả lại khối `4c`, chạy lại → PASS. Ghi cả hai kết quả vào ledger.

- [ ] **Bước 3: Chạy toàn bộ**

Run: `cd backend && uv run pytest tests/schema tests/etl -v`
Expected: PASS toàn bộ.

- [ ] **Bước 4: Commit**

```bash
git add backend/tests/etl/test_e09_refdata_store.py
git commit -m "test(etl): bidirectional financial-statement rule on industry view"
```

---

### Task 6: Nghiệm thu trên DB thật dưới role production

**Files:** không sửa code. Kết quả dán nguyên văn vào `ledger.md`.

🔴 Không được coi là xong nếu chỉ có test xanh — CLAUDE.md §3.5: chạy tay chính lệnh production, dưới đúng credential production, ít nhất một lần.

- [ ] **Bước 1: Sao lưu trước khi migrate DB thật**

```bash
docker exec infra-postgres-1 pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc -f /tmp/pre-0013.dump
docker cp infra-postgres-1:/tmp/pre-0013.dump ./pre-0013.dump
```
Expected: file `pre-0013.dump` tồn tại, kích thước > 0. **Không commit file này** (để ngoài repo hoặc xoá sau khi xong).

- [ ] **Bước 2: Chạy migration lên DB thật**

```bash
cd database && uv run alembic upgrade head && uv run alembic current
```
Expected: `alembic current` in ra `0013`. Log có dòng `NOTICE: seed lop 2: 161 dong override (worksheet co 161 ticker)`. **Nếu số khác 161 thì dừng** — có ticker không tìm được issuer; ghi danh sách vào ledger trước khi đi tiếp.

- [ ] **Bước 3: Chạy job thật dưới role `dlck_etl`, hai lượt**

```bash
PYTHONIOENCODING=utf-8 python -m etl refdata
PYTHONIOENCODING=utf-8 python -m etl refdata
```
Expected: cả hai thoát 0. Lượt hai `sec_inserted=0`, `sec_updated=0`. Dán nguyên văn dòng `refdata xong: {...}` của cả hai lượt vào ledger — trong đó có `industry_unmapped`.

- [ ] **Bước 4: Đo trạng thái đích — năm câu kiểm bất biến**

```bash
docker exec infra-postgres-1 psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At -c "
select 'A_issuer_khong_nganh_ma_co_cp_niem_yet=' || count(distinct v.issuer_id)
  from market.v_issuer_industry v join market.security s on s.issuer_id = v.issuer_id
 where v.industry_id is null and s.security_type='stock' and s.status='listed';
select 'B_vi_pham_BCTC=' || count(*)
  from market.issuer iss join market.v_issuer_industry v using (issuer_id)
  join market.industry i on i.industry_id = v.industry_id
 where (iss.com_type_code='NH') <> (i.code='NGANHANG')
    or (iss.com_type_code='CK') <> (i.code='CHUNGKHOAN')
    or (iss.com_type_code='BH') <> (i.code='BAOHIEM');
select 'C_so_dong_override=' || count(*) from market.issuer_industry_override;
select 'D_so_dong_icb_map=' || count(*) from market.industry_icb_map;
select 'E_nganh_khong_co_ma=' || coalesce(string_agg(code, ','), 'none') from market.industry i
 where i.level=2 and not exists (select 1 from market.v_issuer_industry v where v.industry_id=i.industry_id);
select i.code || ' ' || count(*) from market.security s
  join market.v_issuer_industry v on v.issuer_id = s.issuer_id
  join market.industry i on i.industry_id = v.industry_id
 where s.security_type='stock' and s.status='listed' group by i.code order by count(*) desc;"
```

Expected — **A=0 · B=0 · C=161 · D=55 · E=none**, và bảng phân bố cộng lại bằng số cổ phiếu `listed` có issuer *(đo 2026-08-27: 1.525)*. Con số từng ngành **để tham chiếu** (bảng ở mục "Trạng thái đo lại"), đổi theo mã mới niêm yết là bình thường; A, B, C, D, E mới là điều kiện đỗ.

- [ ] **Bước 5: Nghiệm thu spec §9 — phép thử động trên DB thật**

```bash
docker exec infra-postgres-1 psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
update market.industry_icb_map set industry_id = (select industry_id from market.industry where code='CONGNGHE')
 where icb_code = '2353';"
PYTHONIOENCODING=utf-8 python -m etl refdata
docker exec infra-postgres-1 psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At -c "
select 'CONGNGHE_sau_khi_doi=' || count(*) from market.security s
  join market.v_issuer_industry v on v.issuer_id=s.issuer_id
  join market.industry i on i.industry_id=v.industry_id
 where i.code='CONGNGHE' and s.security_type='stock' and s.status='listed';
select 'PTB_van_la=' || i.code || ' source=' || v.source from market.security s
  join market.v_issuer_industry v on v.issuer_id=s.issuer_id
  join market.industry i on i.industry_id=v.industry_id where s.ticker='PTB';"
```

Expected: `CONGNGHE` tăng thêm đúng số mã của nhánh `2353` *(đo 2026-08-27: 90 mã)*; `PTB_van_la=VATLIEU source=manual` — override không nhúc nhích dù map ICB đổi.

- [ ] **Bước 6: Trả map về đúng, chạy lại, đối chiếu**

```bash
docker exec infra-postgres-1 psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
update market.industry_icb_map set industry_id = (select industry_id from market.industry where code='VATLIEU')
 where icb_code = '2353';"
PYTHONIOENCODING=utf-8 python -m etl refdata
```
Expected: chạy lại bộ câu kiểm ở Bước 4 cho **đúng cùng kết quả** như trước phép thử.

- [ ] **Bước 7: Ghi ledger và commit**

```bash
git add docs/90-records/plans/2026-08-27-industry-two-layer-mapping/ledger.md
git commit -m "docs(plan): execution ledger - real-DB acceptance for industry mapping"
```

---

### Task 7: Đồng bộ tài liệu sống

**Files:**
- Modify: `docs/20-design/industry-tree.md` (§4)
- Modify: `docs/20-design/README.md` (dòng `industry-mapping.md`)
- Modify: `docs/00-overview/roadmap.md:102` (mục [6], phần NGÀNH)
- Modify: `database/README.md`
- Modify: `docs/90-records/plans/2026-08-27-industry-two-layer-mapping/spec.md` (trạng thái đầu file)

- [ ] **Bước 1: Sửa `industry-tree.md` §4** — thêm một gạch đầu dòng ngay dưới dòng nói về `industry_icb_map`

```markdown
- **Ai ghi cột nào:** lớp 1 (máy) ở `market.issuer.industry_id` — job `etl refdata` ghi đè mỗi lượt theo `industry_icb_map`; lớp 2 (tay) ở `market.issuer_industry_override`, ETL không đọc không ghi (DB đã thu hồi quyền ghi của role `dlck_etl`). **Đường đọc duy nhất là view `market.v_issuer_industry`** = `COALESCE(tay, máy)` kèm cột `source` ∈ `manual` | `icb` | `NULL` — đọc thẳng `issuer.industry_id` là bỏ qua lớp tay.
```

- [ ] **Bước 2: Sửa `docs/20-design/README.md`** — cột trạng thái dòng `industry-mapping.md`

```
| ✅ chốt 2026-08-27 · **đã nạp DB** (migration `0013`: 55 dòng lớp 1 + 161 dòng lớp 2) |
```

- [ ] **Bước 3: Sửa `roadmap.md:102`** — thay cả đoạn "⚠️ **Phần NGÀNH … CHƯA NẠP vào DB** *(kiểm 2026-08-27 15:20 …)*" bằng trạng thái thật, kèm ngày và số đo lấy từ ledger. Nêu rõ hệ quả: tầng lọc tin theo ngành của [10] và khung ngành cho skill **hết bị chặn**.

- [ ] **Bước 4: Sửa `database/README.md`** — thêm `0011`/`0012`/`0013` vào danh sách migration, thêm `issuer_industry_override` và `v_issuer_industry` vào mô tả schema `market`, ghi luật *đọc qua view, không đọc thẳng cột*.

- [ ] **Bước 5: Quét chéo toàn repo — không để tài liệu đá nhau** *(CLAUDE.md §1.7)*

```bash
git grep -n "chưa nạp\|CHƯA NẠP\|industry_icb_map\|\bBDS\b\|\bKCN\b\|VLXD\|YTEGD\|DIENNUOC\|TAINGUYEN" -- docs backend database
```
Expected: mọi hit còn lại **hoặc đã đúng, hoặc nằm trong vùng lịch sử** (`00-overview/decisions/`, `90-records/`). Dán danh sách hit và phán quyết từng dòng vào ledger — không chạy phép kiểm này thì không được nói đã đồng bộ.

- [ ] **Bước 6: Commit**

```bash
git add docs database/README.md
git commit -m "docs: industry mapping loaded - sync living docs and roadmap"
```

---

## Nghiệm thu toàn slice

Đối chiếu spec §9. Mọi mục phải có **output thật dán vào ledger**, không nói suông:

- [ ] `etl refdata` chạy dưới role `dlck_etl` hai lượt, lượt hai `sec_inserted=0 sec_updated=0`, `updated_at` không đổi *(Task 6 bước 3)*
- [ ] `v_issuer_industry`: **0** doanh nghiệp có cổ phiếu niêm yết mà thiếu ngành · **0** vi phạm luật BCTC · **0** ngành trống mã *(Task 6 bước 4)*
- [ ] Đè tay một issuer → chạy job → giá trị đè không đổi, `source = manual` *(Task 4 test + Task 6 bước 5)*
- [ ] Đổi một dòng `industry_icb_map` → chạy job → nhánh đó đổi theo, DN có override đứng yên *(Task 6 bước 5)*
- [ ] Issuer mang `icb_code` lá chưa có trong map → leo path → nhận ngành tổ tiên gần nhất *(Task 4 test `climbs_path`)*
- [ ] `pytest tests/schema tests/etl` xanh toàn bộ
- [ ] `git grep` §1.7 sạch, ledger ghi phán quyết từng hit

## Ngoài phạm vi slice này

| Mục | Vì sao để ngoài |
|---|---|
| Sửa `security.status` cho 437 mã đã huỷ niêm yết | Spec §10 xếp là việc riêng của **ETL danh mục** — luật *"vắng mặt trong danh bạ ⇒ huỷ niêm yết"* chạm `plan_delist` và đổi hành vi chốt chặn, cần spec riêng |
| Ngưỡng thanh khoản cho trọng số chỉ số ngành | Spec §6: chữa ở tầng tính chỉ số, không ở cây ngành |
| Công cụ sửa override lúc chạy (không qua migration) | Chưa có nhu cầu — YAGNI. Hôm nay override sửa bằng migration mới, đúng kiểu `0003_seed_industry` |
| 8 mã độ tin cậy thấp và `PVT` | Spec §10 — xem lại khi chỉ số ngành chạy và thấy nhiễu, không phải bây giờ |
