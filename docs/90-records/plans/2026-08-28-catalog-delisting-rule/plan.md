# Kế hoạch thực thi — Luật huỷ niêm yết cho mã vắng danh bạ

> **Cho người thực thi:** làm từng task, mỗi task một vòng đỏ → xanh → commit. Mỗi bước là một checkbox `- [ ]`.

**Mục tiêu:** job `etl refdata` tự lật `delisted` cho cổ phiếu **có trong bảng giá BVSC mà vắng khỏi danh bạ doanh nghiệp FiinTrade**, sau khi mã đó vắng liên tục đủ lâu — để tập "mã đang niêm yết" thôi chứa mã chết.

**Kiến trúc:** thêm một cột dấu thời gian `market.security.directory_absent_since`. `apply()` **đóng dấu** khi thấy mã vắng danh bạ và **gỡ dấu** khi mã quay lại; `plan_delist()` (chạy TRƯỚC `apply`, cấp số liệu cho chốt chặn) chỉ chọn lật những mã đã mang dấu đủ ngưỡng. Nhờ tách hai vai này, mã mới lên sàn — xuất hiện ở bảng giá trước khi vào danh bạ — chỉ mang dấu tạm rồi tự được gỡ, không bao giờ bị lật.

**Tech stack:** Python 3.12 · SQLAlchemy 2 Core (text SQL) · Alembic · pytest trên Postgres thật.

**Chủ sở hữu thiết kế:** [`market-data-store.md §4.4`](../../../20-design/market-data-store.md) — luật, ba ràng buộc, và lý do. Plan này chỉ nói *cài thế nào*.

**Nhánh:** nhánh mới từ `main` — `feat/catalog-delisting-rule`. *(Bản đầu của plan này ghi "làm tiếp trên `feat/industry-two-layer-mapping`"; nhánh đó đã merge vào `main` sáng 2026-08-28 theo quyết định của chủ dự án, nên chỉ dẫn cũ không còn đúng.)*

---

## Global Constraints

- 🔴 **Không sửa file khi sắp tới giờ job chạy.** Task `dlck-refdata` chạy `cd /d "<backend>" && uv run python -m etl refdata` lúc **08:00**, `dlck-ingester` **08:30** — chúng đọc file trên đĩa tại thời điểm đó. Sửa dở giữa chừng là đẩy code nửa vời vào đường chạy production.
- **Không sửa migration `0001`–`0013`** — đã chạy trên DB thật. File mới là `0014`.
- `PYTHONIOENCODING=utf-8` cho mọi lệnh Python.
- Test chạy dưới đúng quyền production: `SET LOCAL ROLE dlck_etl`.
- Chạy `uv run pytest tests` một lệnh là được cả bộ — lỗi collection do hai `conftest.py` trùng tên module **đã sửa ở `ff4d0ca`** (2026-08-28). Trước đó phải chạy riêng từng thư mục; chỉ dẫn cũ nào còn nói thế là đã lỗi thời.
- Conventional Commits, message tiếng Anh. Không `--no-verify`, không push.

```bash
cd /d/twan_projects/dulieuchungkhoan.vn
set -a; . ./.env; set +a          # KHÔNG in giá trị biến ra output
export PYTHONIOENCODING=utf-8
cd backend && uv run pytest tests/etl -v
```

---

## Ba ràng buộc của luật *(chép từ §4.4, là yêu cầu bắt buộc)*

1. **Chỉ `security_type = 'stock'`.** ETF (10 mã) và chỉ số (18 mã) không có doanh nghiệp phát hành — "không issuer" là trạng thái bình thường vĩnh viễn của chúng. Chứng chỉ quỹ **có** issuer `com_type_code='QU'` nên không rơi vào diện này.
2. **Chốt chặn sụt sẽ từ chối lượt dọn đầu tiên.** `DELIST_RATIO = 0.01`; 438/1.962 = 22,3%. Lượt dọn đầu **phải chạy tay** với `--accept-drop`, có người nhìn.
3. **Vắng một lượt chưa chắc là chết** — mã mới niêm yết vào bảng giá trước danh bạ. Ngưỡng: **vắng liên tục ≥ 3 ngày**.

## Số đo nền *(đo trên DB thật 2026-08-28)*

| | |
|---|---|
| Cổ phiếu không issuer, vẫn `listed` | **438** (UPCOM 378 · HNX 39 · HOSE 21) |
| Cổ phiếu `listed` tổng | 1.962 ⇒ tỷ lệ lật 22,3% |
| ETF không issuer | 10 · chỉ số 18 — **phải nằm ngoài** |
| Chứng chỉ quỹ có issuer `QU` | 3 |
| Toàn kho `delisted` | 4 dòng |

**Không backdate cột dấu cho 438 mã hiện có.** Đồng hồ tính từ lượt chạy đầu tiên sau khi cài. Backdate là ghi con số không đo được — trong đó có đúng một mã vừa gia nhập nhóm ngày 27/08 mà không biết là mã nào (`stocks_no_issuer` đi từ 437 lên 438).

---

## Cấu trúc file

| File | Trách nhiệm |
|---|---|
| `database/migrations/versions/0014_directory_absent_since.py` | **Tạo** — thêm cột `market.security.directory_absent_since` |
| `backend/etl/refdata_store.py` | **Sửa** — `apply()` đóng/gỡ dấu; `plan_delist()` chọn thêm ứng viên đủ ngưỡng |
| `backend/tests/etl/test_e09_refdata_store.py` | **Sửa** — seam test cho đóng dấu, gỡ dấu, ngưỡng, loại trừ theo loại |
| `backend/tests/schema/test_s12_directory_absent.py` | **Tạo** — seam schema: cột tồn tại, mặc định NULL, quyền của `dlck_etl` |
| `docs/20-design/market-data-store.md` §4.4 | **Sửa** — đổi từ "chưa có luật nào" sang mô tả cơ chế đã cài |
| `docs/00-overview/roadmap.md` §5 | **Sửa** — hạ mục khỏi "để ngỏ", ghi việc còn lại là lượt dọn tay |
| `docs/90-records/plans/2026-08-28-catalog-delisting-rule/ledger.md` | **Tạo** — sổ ghi thực thi |

---

### Task 1: Migration 0014 — cột dấu vắng danh bạ

**Files:** Create `database/migrations/versions/0014_directory_absent_since.py` · Create `backend/tests/schema/test_s12_directory_absent.py`

**Interfaces:** Produces cột `market.security.directory_absent_since timestamptz NULL`. Task 2 đọc/ghi cột này.

- [ ] **Bước 1: Viết test đỏ** — `backend/tests/schema/test_s12_directory_absent.py`

```python
import sqlalchemy as sa


def _stock(db, ticker, stype="stock"):
    return db.execute(sa.text(
        "INSERT INTO market.security (ticker, exchange, security_type, status) "
        "VALUES (:t,'HOSE',:ty,'listed') RETURNING security_id"),
        {"t": ticker, "ty": stype}).scalar_one()


def test_directory_absent_since_defaults_to_null(db):        # seam 1
    sid = _stock(db, "ZZZ1")
    assert db.execute(sa.text(
        "SELECT directory_absent_since FROM market.security WHERE security_id=:i"),
        {"i": sid}).scalar_one() is None


def test_etl_role_can_write_directory_absent_since(db):      # seam 2: đường ghi production
    sid = _stock(db, "ZZZ2")
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    db.execute(sa.text(
        "UPDATE market.security SET directory_absent_since = now() WHERE security_id=:i"),
        {"i": sid})
    assert db.execute(sa.text(
        "SELECT directory_absent_since IS NOT NULL FROM market.security WHERE security_id=:i"),
        {"i": sid}).scalar_one() is True
```

- [ ] **Bước 2: Chạy để thấy đỏ** — `cd backend && uv run pytest tests/schema/test_s12_directory_absent.py -v`
  Expected: FAIL — `UndefinedColumn: column "directory_absent_since" does not exist`.

- [ ] **Bước 3: Viết migration**

```python
"""directory_absent_since on market.security (market-data-store §4.4)

Revision ID: 0014
Revises: 0013
Create Date: 2026-08-28

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0014"
down_revision: Union[str, None] = "0013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        -- Dấu thời điểm LẦN ĐẦU thấy mã vắng khỏi danh bạ doanh nghiệp FiinTrade
        -- (mã còn trong bảng giá BVSC nhưng không có issuer). NULL = đang có mặt.
        -- Job đóng dấu một lần rồi thôi, gỡ dấu khi mã quay lại; chỉ mã mang dấu đủ
        -- ngưỡng mới bị lật 'delisted' (market-data-store §4.4). Nhờ đó mã MỚI niêm
        -- yết — vào bảng giá trước khi vào danh bạ — chỉ mang dấu tạm rồi được gỡ.
        ALTER TABLE market.security ADD COLUMN directory_absent_since timestamptz;
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE market.security DROP COLUMN directory_absent_since;")
```

- [ ] **Bước 4: Chạy để thấy xanh** — `uv run pytest tests/schema -q`. Expected: toàn bộ PASS.
- [ ] **Bước 5: Commit** — `feat(db): track when a ticker first went missing from the issuer directory`

---

### Task 2: Đóng dấu, gỡ dấu, và chọn ứng viên lật

**Files:** Modify `backend/etl/refdata_store.py` · Modify `backend/tests/etl/test_e09_refdata_store.py`

**Interfaces:**
- `plan_delist(conn, target)` giữ nguyên chữ ký `-> (list[str], int, int)`, nhưng danh sách trả về nay gồm **cả** ứng viên "vắng danh bạ đủ ngưỡng"; `flips` cộng luôn số đó nên chốt chặn tầng 2 nhìn thấy.
- `apply()` trả thêm `stats["directory_absent_marked"]` và `stats["directory_absent_cleared"]`.

**Thứ tự chạy phải đúng, đây là điểm dễ sai nhất:** `refdata_job` gọi `plan_delist` → `guard.check` → `apply`. Nên `plan_delist` đọc **dấu của các lượt TRƯỚC**, còn `apply` cập nhật dấu **cho lượt SAU**. Không được đóng dấu rồi lật ngay trong cùng một lượt — làm thế thì ngưỡng 3 ngày vô nghĩa.

- [ ] **Bước 1: Viết test đỏ** — thêm vào `backend/tests/etl/test_e09_refdata_store.py`

```python
def _mark_age(db, ticker, days):
    """Lùi dấu vắng danh bạ về quá khứ — mô phỏng mã đã vắng nhiều ngày."""
    db.execute(sa.text("RESET ROLE"))
    db.execute(sa.text(
        "UPDATE market.security SET directory_absent_since = now() - make_interval(days => :d)"
        " WHERE ticker = :t"), {"d": days, "t": ticker})
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))


def _absent_since(db, ticker):
    return db.execute(sa.text(
        "SELECT directory_absent_since FROM market.security WHERE ticker=:t"),
        {"t": ticker}).scalar_one()


def _no_issuer_stock(target):
    """Ticker cổ phiếu trong đích mà không khớp doanh nghiệp nào — diện của luật này."""
    return next(s.ticker for s in target.securities
                if s.security_type == "stock" and s.organ_code is None
                and s.status == "listed")


def test_absent_from_directory_gets_marked_once(db):          # seam: đóng dấu
    _as_etl(db)
    t = _target()
    refdata_store.apply(db, t, [])
    tk = _no_issuer_stock(t)
    first = _absent_since(db, tk)
    assert first is not None
    refdata_store.apply(db, t, [])                            # lượt hai không được dời dấu
    assert _absent_since(db, tk) == first


def test_mark_is_cleared_when_ticker_returns_to_directory(db):   # seam: gỡ dấu
    _as_etl(db)
    t = _target()
    refdata_store.apply(db, t, [])
    tk = _no_issuer_stock(t)
    assert _absent_since(db, tk) is not None
    # doanh nghiệp xuất hiện trong danh bạ ở lượt sau
    from dataclasses import replace
    org = t.issuers[0]
    t2 = type(t)(
        securities=[replace(s, organ_code=org.organ_code) if s.ticker == tk else s
                    for s in t.securities],
        issuers=t.issuers, icb=t.icb, counters=t.counters)
    stats = refdata_store.apply(db, t2, [])
    assert _absent_since(db, tk) is None
    assert stats["directory_absent_cleared"] >= 1


def test_not_delisted_before_threshold(db):                   # ca biên: dưới ngưỡng
    _as_etl(db)
    t = _target()
    refdata_store.apply(db, t, [])
    tk = _no_issuer_stock(t)
    _mark_age(db, tk, 2)                                      # mới vắng 2 ngày
    delist, flips, _ = refdata_store.plan_delist(db, t)
    assert tk not in delist


def test_delisted_after_threshold(db):                        # ca chính
    _as_etl(db)
    t = _target()
    refdata_store.apply(db, t, [])
    tk = _no_issuer_stock(t)
    _mark_age(db, tk, 4)                                      # vắng 4 ngày > ngưỡng 3
    delist, flips, _ = refdata_store.plan_delist(db, t)
    assert tk in delist and flips >= 1
    refdata_store.apply(db, t, delist)
    assert db.execute(sa.text("SELECT status FROM market.security WHERE ticker=:t"),
                      {"t": tk}).scalar_one() == "delisted"


def test_etf_and_index_are_never_marked_or_delisted(db):      # ràng buộc 1
    _as_etl(db)
    t = _target()
    refdata_store.apply(db, t, [])
    rows = db.execute(sa.text(
        "SELECT count(*) FROM market.security"
        " WHERE security_type <> 'stock' AND directory_absent_since IS NOT NULL")).scalar_one()
    assert rows == 0
```

- [ ] **Bước 2: Chạy để thấy đỏ** — `uv run pytest tests/etl/test_e09_refdata_store.py -v`
  Expected: FAIL — `KeyError: 'directory_absent_cleared'` và `assert None is not None`.

- [ ] **Bước 3: Viết implementation**

Trong `backend/etl/refdata_store.py`, thêm hằng số cạnh `JOB`:

```python
# Vắng khỏi danh bạ doanh nghiệp bao lâu thì coi là đã rời sàn (market-data-store §4.4).
# Có ngưỡng vì mã MỚI niêm yết xuất hiện ở bảng giá BVSC trước khi vào danh bạ FiinTrade —
# lật ngay lượt đầu là bắn nhầm mã vừa lên sàn.
DIRECTORY_ABSENT_DAYS = 3
```

Trong `apply()`, **sau khối upsert `security` (bước 2, sau vòng lặp) và trước bước 4 `icb_industry`**:

```python
    # 3b. Dấu vắng danh bạ — bookkeeping cho luật huỷ niêm yết (§4.4). Cố ý KHÔNG
    # đụng `updated_at`: đây là quan sát của job về nguồn, không phải trường dữ liệu
    # của mã. Đóng dấu một lần rồi thôi (điều kiện IS NULL), gỡ khi mã quay lại.
    cleared = conn.execute(
        sa.text(
            "UPDATE market.security SET directory_absent_since = NULL"
            " WHERE directory_absent_since IS NOT NULL AND issuer_id IS NOT NULL"
        )
    ).rowcount
    marked = conn.execute(
        sa.text(
            "UPDATE market.security SET directory_absent_since = now()"
            " WHERE directory_absent_since IS NULL AND issuer_id IS NULL"
            "   AND security_type = 'stock' AND status = 'listed'"
        )
    ).rowcount
    stats["directory_absent_cleared"] = cleared
    stats["directory_absent_marked"] = marked
```

Trong `plan_delist()`, sau khi tính `absent`, thêm đường thứ ba và cộng vào `flips`:

```python
    # Đường (c) — cổ phiếu CÓ trong bảng giá nhưng vắng khỏi danh bạ doanh nghiệp đủ
    # lâu (§4.4). Đọc dấu do các lượt TRƯỚC đóng: `apply` của lượt này mới cập nhật
    # dấu cho lượt sau, nên ngưỡng đếm theo ngày thật, không phải theo một lượt chạy.
    stale = [
        r[0]
        for r in conn.execute(
            sa.text(
                "SELECT ticker FROM market.security"
                " WHERE status = 'listed' AND security_type = 'stock'"
                "   AND issuer_id IS NULL AND directory_absent_since IS NOT NULL"
                "   AND directory_absent_since <= now() - make_interval(days => :d)"
            ),
            {"d": DIRECTORY_ABSENT_DAYS},
        ).all()
    ]
    absent = sorted(set(absent) | set(stale))
    flips = len(absent) + len(listed & target_delisted)
```

⚠️ Giữ nguyên phần tính `flips` cũ ở trên rồi tính lại sau khi gộp `stale` — đừng để hai công thức song song trôi lệch.

- [ ] **Bước 4: Chạy để thấy xanh** — `uv run pytest tests/etl -v`. Expected: PASS toàn bộ, đặc biệt `test_apply_twice_is_idempotent_including_timestamps` **phải vẫn xanh** (dấu không đụng `updated_at`, và lượt hai không đóng dấu lại).
- [ ] **Bước 5: Thí nghiệm đột biến** — tạm đổi `DIRECTORY_ABSENT_DAYS` thành `0`: `test_not_delisted_before_threshold` phải ĐỎ. Trả lại `3` → xanh. Dán output cả hai lần vào ledger.
- [ ] **Bước 6: Commit** — `feat(etl): delist stocks missing from the issuer directory past the grace window`

---

### Task 3: Nghiệm thu trên DB thật + đồng bộ tài liệu

**Files:** không sửa code. Sửa `docs/20-design/market-data-store.md` §4.4, `docs/00-overview/roadmap.md` §5; tạo ledger.

🔴 **Chỉ chạy ngoài khung 08:00 và 08:30** — hai task tự động đọc file trên đĩa.

- [ ] **Bước 1: Sao lưu** vào scratchpad ngoài repo, kiểm file > 0 byte. Thất bại thì DỪNG.
- [ ] **Bước 2: Migrate DB thật** — `uv run --project backend alembic -c database/alembic.ini upgrade head` tại gốc repo, rồi `... current` phải in `0014`.
- [ ] **Bước 3: Chạy job thật hai lượt** — `cd backend && uv run python -m etl refdata`, hai lần. Kỳ vọng: cả hai exit 0; lượt đầu `directory_absent_marked = 438`, lượt hai `= 0` (đóng dấu một lần rồi thôi); `delisted = 0` ở cả hai lượt vì chưa mã nào đủ 3 ngày.
- [ ] **Bước 4: Đối chiếu trên DB thật** — mọi câu kiểm dán nguyên văn vào ledger:

```sql
select 'A_co_dau=' || count(*) from market.security where directory_absent_since is not null;
select 'B_dau_sai_loai=' || count(*) from market.security
 where directory_absent_since is not null and security_type <> 'stock';
select 'C_khong_issuer_chua_dau=' || count(*) from market.security
 where issuer_id is null and security_type = 'stock' and status = 'listed'
   and directory_absent_since is null;
select 'D_da_bi_lat=' || count(*) from market.security where status = 'delisted';
```
Kỳ vọng: **A = 438 · B = 0 · C = 0 · D = 4** (chưa lật thêm mã nào — đúng, ngưỡng chưa tới).

- [ ] **Bước 5: Sửa `market-data-store.md` §4.4** — đổi bảng "Job hiện xử lý" từ *"🔴 Chưa có luật nào"* sang mô tả cơ chế đã cài: cột dấu, ngưỡng `DIRECTORY_ABSENT_DAYS = 3`, ai đóng ai gỡ, vì sao `plan_delist` đọc dấu của lượt trước. Ghi rõ **việc còn lại là lượt dọn tay**: khi 438 mã đủ ngưỡng, chốt chặn 1% sẽ **từ chối** lượt tự động (job báo `failed`, không ghi gì) cho tới khi có người chạy `python -m etl refdata --accept-drop`. Nói thẳng để người trực không hoảng khi thấy job đỏ.
- [ ] **Bước 6: Sửa `roadmap.md` §5** — mục này thôi "để ngỏ": cơ chế đã cài, còn lại đúng một việc có người nhìn là lượt dọn `--accept-drop`, dự kiến sau 3 ngày kể từ lượt đóng dấu đầu tiên.
- [ ] **Bước 7: `git grep`** các chuỗi vừa đổi (`chưa có luật nào`, `438`, `directory_absent`) toàn repo, phán quyết từng hit, dán vào ledger.
- [ ] **Bước 8: Commit** — `docs: catalog delisting rule is live; only the manual sweep remains`

---

## Nghiệm thu toàn slice

- [ ] `pytest tests/schema` và `pytest tests/etl` xanh (chạy riêng)
- [ ] Job thật hai lượt exit 0; `directory_absent_marked` 438 rồi 0
- [ ] A = 438 · B = 0 · C = 0 · D = 4 trên DB thật
- [ ] Thí nghiệm đột biến ngưỡng có output trong ledger
- [ ] `git grep` §1.7 sạch

## Ngoài phạm vi

| Mục | Vì sao |
|---|---|
| Lượt dọn `--accept-drop` cho 438 mã | Cần người nhìn, và ngưỡng chưa tới. Việc riêng, có lịch |
| Phái sinh + `/datafeed/instruments` | Lát riêng đã hẹn ở refdata spec §9; luật này không chặn nó |
| Hạ `DELIST_RATIO` hay làm ngưỡng động | Chốt chặn hiện tại đang làm đúng việc của nó — từ chối một cú sụt 22% là hành vi mong muốn |
