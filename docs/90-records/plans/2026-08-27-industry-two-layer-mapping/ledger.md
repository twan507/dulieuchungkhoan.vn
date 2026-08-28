# SDD ledger — Task 6: nghiệm thu trên DB thật dưới role production

Plan: `docs/90-records/plans/2026-08-27-industry-two-layer-mapping/plan.md`. Nhánh: `feat/industry-two-layer-mapping`, HEAD `3ed8d0a` khi bắt đầu. DB thật: container `infra-postgres-1`, database `dulieu` (trước migrate ở `alembic_version=0010`). Không sửa code/migration nào ở task này — chỉ chạy lệnh và ghi sổ.

Ghi chú lệnh alembic: brief gốc ghi `cd database && uv run alembic ...` — sai (thư mục `database/` không có `pyproject.toml`). Dạng đúng dùng ở task này, chạy tại gốc repo: `uv run --project backend alembic -c database/alembic.ini <lệnh>`.

## Bước 1 — Sao lưu trước khi migrate

```bash
export MSYS_NO_PATHCONV=1
docker exec infra-postgres-1 pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc -f /tmp/pre-0013.dump
docker cp infra-postgres-1:/tmp/pre-0013.dump <scratchpad>/pre-0013.dump
```

Kết quả: file lưu ngoài repo tại `.../scratchpad/sdd-industry/pre-0013.dump`, kích thước **332.600 byte** (> 0) — đạt điều kiện tiếp tục.

## Bước 2 — Migration lên DB thật

```bash
uv run --project backend alembic -c database/alembic.ini upgrade head
uv run --project backend alembic -c database/alembic.ini current
```

`current` in ra: `0013 (head)`. Migration chạy thành công nhưng SQLAlchemy/psycopg3 không tự in NOTICE của server ra console (không có notice handler đăng ký trong `env.py`), nên dòng `RAISE NOTICE` không xuất hiện trực tiếp ở log lệnh trên.

Để lấy nguyên văn dòng NOTICE làm bằng chứng mà không đụng dữ liệu thật, đã mô phỏng lại đúng khối SQL của `upgrade()` (trích bằng `ast` từ chính file migration, không gõ tay lại) trong một transaction riêng: `DELETE` hai bảng seed-only rồi chạy lại SQL gốc, đăng ký notice handler của psycopg3 để bắt message, sau đó `ROLLBACK` — không `COMMIT`. Script tạm: `<scratchpad>/capture_notice.py`.

Output:
```
NOTICES CAPTURED:
seed lop 2: 161/161 ticker khop issuer, 161 dong override
override count after rollback: 161
icb_map count after rollback: 55
```

Con số `override count after rollback: 161` / `icb_map count after rollback: 55` xác nhận ROLLBACK không làm lệch dữ liệu thật đã migrate (đúng bằng số đo trực tiếp trước và sau khi chạy script). Dòng NOTICE khớp kỳ vọng đã sửa trong đề bài task: `161/161 ticker khop issuer, 161 dong override` — **đúng 161, không dừng**.

**Nói thẳng về loại bằng chứng:** dòng NOTICE trên là bằng chứng **gián tiếp** — nó đến từ SQL mô phỏng lại (chạy trong transaction rồi ROLLBACK), không phải in ra trực tiếp từ chính lệnh `alembic upgrade head` chạy trên production (lệnh đó không in NOTICE, như đã nêu ở trên). **Bằng chứng trực tiếp cho kết quả seed thật của lệnh production** là hai số đo thẳng trên DB *sau* khi migration đã chạy và commit: `C_so_dong_override=161` và `D_so_dong_icb_map=55` ở Bước 4 (và lặp lại giống hệt ở Bước 6) — đây mới là số đến từ chính dữ liệu mà `alembic upgrade head` production đã ghi, không qua mô phỏng.

## Bước 3 — Chạy job thật dưới role `dlck_etl`, hai lượt

```bash
cd backend
set -a; . ../.env; set +a
export PYTHONIOENCODING=utf-8
uv run python -m etl refdata
```

**Lượt 1** (exit 0):
```
2026-08-28 00:07:57,496 WARNING etl.refdata_store 24 doanh nghiệp không tra được ngành từ industry_icb_map — để NULL, không chặn job
2026-08-28 00:07:57,505 INFO etl.refdata refdata xong: {'sec_inserted': 0, 'sec_updated': 1, 'sec_unchanged': 2014, 'delisted': 0, 'exchange_moves': 0, 'issuers_inserted': 0, 'icb_rows': 176, 'icb_orphaned': 0, 'issuers_without_industry': 24, 'counts': {'quotes': 1993, 'organization': 1549, 'icb': 176}, 'skipped_cw': 296, 'skipped_bond': 188, 'junk_stocktype2': 14, 'unknown_stocktype': 0, 'index_junk': 2, 'stocks_no_issuer': 438, 'fiin_only_delisted': 4, 'unknown_com_group': 0, 'dup_org_ticker': 0}
```

**Lượt 2** (exit 0):
```
2026-08-28 00:08:25,585 WARNING etl.refdata_store 24 doanh nghiệp không tra được ngành từ industry_icb_map — để NULL, không chặn job
2026-08-28 00:08:25,595 INFO etl.refdata refdata xong: {'sec_inserted': 0, 'sec_updated': 0, 'sec_unchanged': 2015, 'delisted': 0, 'exchange_moves': 0, 'issuers_inserted': 0, 'icb_rows': 176, 'icb_orphaned': 0, 'issuers_without_industry': 24, 'counts': {'quotes': 1993, 'organization': 1549, 'icb': 176}, 'skipped_cw': 296, 'skipped_bond': 188, 'junk_stocktype2': 14, 'unknown_stocktype': 0, 'index_junk': 2, 'stocks_no_issuer': 438, 'fiin_only_delisted': 4, 'unknown_com_group': 0, 'dup_org_ticker': 0}
```

Cả hai thoát 0. Lượt hai `sec_inserted=0, sec_updated=0` đúng kỳ vọng (idempotent). `issuers_without_industry=24` cả hai lượt — khác 0 so với số đo tham chiếu bằng mô phỏng (0), nhưng chỉ số này đếm **toàn bộ issuer**, còn điều kiện đỗ chính thức A ở Bước 4 chỉ tính issuer có cổ phiếu `listed` — xem nguyên nhân đo được và đối chiếu ở Bước 4.

*(Vòng sửa 1 — đính chính)* Bản đầu của mục này từng suy đoán 24 issuer là "trái phiếu/lô lẻ/chứng quyền hoặc chứng khoán delisted" — **sai, chưa đo mà đã viết**. Đo lại bằng truy vấn chỉ đọc trên DB thật (điều phối viên đo, reviewer đo độc lập lần nữa, và tự kiểm tra lại lần ba khi sửa vòng này, cả ba cùng kết quả):
```
QU_thieu_nganh=24
icb_8985_thieu_nganh=24
thieu_nganh_tong=24
thieu_nganh_co_listed=0
```
Cả 24 đều là **chứng chỉ quỹ/ETF** (`com_type_code='QU'`, `icb_code='8985'`) — đúng luật "ETF và quỹ không có ngành" (dòng ICB `8980` "Quỹ đầu tư" cố ý KHÔNG NẠP trong seed migration 0013, xem docstring `upgrade()`). Ba khối trái phiếu/lô lẻ/chứng quyền ở CLAUDE.md §2.2 không liên quan tới 24 issuer này. **`issuers_without_industry=24` là trạng thái ổn định bình thường** — cảnh báo này lặp lại mỗi lượt job không phải dấu hiệu hỏng; con số vượt 24 đáng kể mới đáng nghi.

## Bước 4 — Năm câu kiểm bất biến

**Nguồn uỷ quyền câu kiểm B:** câu B dưới đây dùng `LEFT JOIN` + `coalesce(...) IS DISTINCT FROM`, khác bản `INNER JOIN` + `<>` trong `plan.md`. Đây không phải tự ý đổi khi thực thi task — bản `INNER JOIN` có lỗ hổng: issuer `NH` mà không tra được ngành (industry NULL) bị `INNER JOIN` loại khỏi kết quả nên **tàng hình**, không bị đếm là vi phạm dù đúng ra là vi phạm; và `com_type_code` NULL bị logic ba trị SQL (`NULL <> 'NH'` → `NULL`, không phải `TRUE`/`FALSE`) nuốt mất, cũng tàng hình theo cách tương tự. Vì vậy người điều phối đã siết câu dò này ở Task 5 và dùng bản siết ở Task 6 (đúng như phần "đã lỗi thời" ghi trong đề bài task 6). Reviewer đã chạy cả hai bản trên DB thật: cả hai đều ra `B=0`, nhưng bản siết mới là bản chặt — không bỏ sót ca NULL.

```sql
select 'A_issuer_khong_nganh_ma_co_cp_niem_yet=' || count(distinct v.issuer_id)
  from market.v_issuer_industry v join market.security s on s.issuer_id = v.issuer_id
 where v.industry_id is null and s.security_type='stock' and s.status='listed';
select 'B_vi_pham_BCTC=' || count(*)
  from market.issuer iss
  left join market.v_issuer_industry v on v.issuer_id = iss.issuer_id
  left join market.industry i on i.industry_id = v.industry_id
 where (coalesce(iss.com_type_code,'') = 'NH') is distinct from (coalesce(i.code,'') = 'NGANHANG')
    or (coalesce(iss.com_type_code,'') = 'CK') is distinct from (coalesce(i.code,'') = 'CHUNGKHOAN')
    or (coalesce(iss.com_type_code,'') = 'BH') is distinct from (coalesce(i.code,'') = 'BAOHIEM');
select 'C_so_dong_override=' || count(*) from market.issuer_industry_override;
select 'D_so_dong_icb_map=' || count(*) from market.industry_icb_map;
select 'E_nganh_khong_co_ma=' || coalesce(string_agg(code, ','), 'none') from market.industry i
 where i.level=2 and not exists (select 1 from market.v_issuer_industry v where v.industry_id=i.industry_id);
select i.code || ' ' || count(*) from market.security s
  join market.v_issuer_industry v on v.issuer_id = s.issuer_id
  join market.industry i on i.industry_id = v.industry_id
 where s.security_type='stock' and s.status='listed' group by i.code order by count(*) desc;
```

Kết quả:
```
A_issuer_khong_nganh_ma_co_cp_niem_yet=0
B_vi_pham_BCTC=0
C_so_dong_override=161
D_so_dong_icb_map=55
E_nganh_khong_co_ma=none
XAYDUNG 198
TIENICH 143
DANDUNG 117
VANTAI 109
VATLIEU 91
THUCPHAM 89
YTE 88
DETMAY 72
THIETBI 69
NHUA 54
DAUKHI 52
DULICH 51
KIMLOAI 44
CHUNGKHOAN 42
KHOANGSAN 40
CONGNGHE 39
HOACHAT 37
BANLE 37
KHUCONGNGHIEP 34
THUYSAN 32
NGANHANG 30
NONGNGHIEP 29
CAOSU 14
BAOHIEM 13
```

**A=0 · B=0 · C=161 · D=55 · E=none — cả năm điều kiện đỗ.** Tổng phân bố = 1.524 (tham chiếu đo 2026-08-27: 1.525) — lệch 1, cụ thể `YTE` 88 thay vì 89 tham chiếu, các ngành khác khớp nguyên. Đây là chênh lệch mã mới niêm yết bình thường theo brief, không phải hỏng.

Con số `issuers_without_industry=24` ở Bước 3 không mâu thuẫn với `A=0`: 24 issuer đó là chứng chỉ quỹ/ETF (xem đính chính ở Bước 3 — `com_type_code='QU'`, `icb_code='8985'`, không issuer nào trong 24 có cổ phiếu `listed`), nên không rơi vào phạm vi điều kiện A. Đây là thiết kế cố ý (ICB `8980` không nạp ngành), không phải lỗ hổng dữ liệu.

## Bước 5 — Phép thử động (spec §9)

```sql
update market.industry_icb_map set industry_id = (select industry_id from market.industry where code='CONGNGHE')
 where icb_code = '2353';
```
`UPDATE 1`.

```bash
uv run python -m etl refdata
```
Exit 0, `issuers_without_industry=24` (không đổi so với Bước 3).

```sql
select 'CONGNGHE_sau_khi_doi=' || count(*) ... where i.code='CONGNGHE' ...;
select 'VATLIEU_sau_khi_doi=' || count(*) ... where i.code='VATLIEU' ...;
select 'PTB_van_la=' || i.code || ' source=' || v.source ... where s.ticker='PTB';
```
Kết quả:
```
CONGNGHE_sau_khi_doi=129
VATLIEU_sau_khi_doi=1
PTB_van_la=VATLIEU source=manual
```

`CONGNGHE` tăng từ 39 lên 129 (**+90**, đúng số mã nhánh `2353` đo 2026-08-27). `VATLIEU` còn lại 1 (chỉ `PTB`). `PTB_van_la=VATLIEU source=manual` — override lớp 2 không nhúc nhích dù map ICB lớp 1 đổi, đúng luật phân giải "override thắng map".

`PTB` chứng minh "đè tay thắng" nói chung, nhưng bản thân `PTB` mang `icb_code` khác `2353` nên vốn dĩ không nằm trong nhánh bị đổi ở phép thử này — bằng chứng không mạnh bằng việc chỉ ra chính những issuer **trong** nhánh `2353` mà vẫn đứng yên. Đo bằng truy vấn chỉ đọc (sau khi đã trả map về, không ảnh hưởng gì phép thử):
```
issuer_icb_2353_total=110
issuer_icb_2353_voi_override=20
issuer_icb_2353_listed_stock=110
issuer_icb_2353_listed_voi_override=20
```
Khớp đúng số học suy ra từ phép thử động: 110 issuer mang `icb_code='2353'`, trong đó 20 issuer có dòng ở `issuer_industry_override` — chính 20 issuer này không di chuyển sang `CONGNGHE` khi map lớp 1 đổi (110 − 20 = 90, đúng bằng số mã thực sự chuyển sang `CONGNGHE` đo được ở trên). Đây là bằng chứng mạnh hơn `PTB` một mình: 20 issuer *nằm ngay trong* nhánh ICB bị đổi vẫn đứng yên nhờ override, không phải nhờ đứng ngoài nhánh.

## Bước 6 — Trả map về, chạy lại, đối chiếu

```sql
update market.industry_icb_map set industry_id = (select industry_id from market.industry where code='VATLIEU')
 where icb_code = '2353';
```
`UPDATE 1`.

```bash
uv run python -m etl refdata
```
Exit 0, `issuers_without_industry=24` (không đổi).

Chạy lại nguyên văn 5 câu kiểm + bảng phân bố ở Bước 4:
```
A_issuer_khong_nganh_ma_co_cp_niem_yet=0
B_vi_pham_BCTC=0
C_so_dong_override=161
D_so_dong_icb_map=55
E_nganh_khong_co_ma=none
XAYDUNG 198
TIENICH 143
DANDUNG 117
VANTAI 109
VATLIEU 91
THUCPHAM 89
YTE 88
DETMAY 72
THIETBI 69
NHUA 54
DAUKHI 52
DULICH 51
KIMLOAI 44
CHUNGKHOAN 42
KHOANGSAN 40
CONGNGHE 39
HOACHAT 37
BANLE 37
KHUCONGNGHIEP 34
THUYSAN 32
NGANHANG 30
NONGNGHIEP 29
CAOSU 14
BAOHIEM 13
```

**Trùng khớp từng dòng với kết quả Bước 4** (kể cả `VATLIEU=91`, `CONGNGHE=39`) — hệ thống quay đúng về trạng thái ban đầu sau khi trả map.

## Kiểm hồi quy sau task

```bash
cd backend
uv run pytest tests/schema -q   # 49 passed in 0.82s
uv run pytest tests/etl -q      # 57 passed in 5.06s
```

Cả hai bộ xanh, chạy riêng theo đúng chỉ dẫn (lệnh gộp hỏng vì nợ có sẵn của repo, ngoài phạm vi task này).

## Đính chính số đo của plan

`plan.md:51` ghi: *"Lớp 1 phủ **1.550/1.550 issuer**, **0 issuer NULL** — kể cả trước khi áp lớp 2."* — **con số này sai.** Nguyên nhân: mô phỏng lúc lập plan đã chèn chuỗi `'None'` làm mã ngành cho dòng ICB `8980` ("Quỹ đầu tư") thay vì lọc dòng đó ra, nên 24 quỹ/ETF bị gán một ngành ma thay vì để NULL.

Số đúng, đo trên DB thật sau khi migration 0013 + job `etl refdata` đã chạy (Bước 3–4 ở trên): **1.526/1.550 issuer có ngành, 24 quỹ/ETF không có ngành theo đúng thiết kế** (xem đính chính ở Bước 3 — `com_type_code='QU'`, `icb_code='8985'`). Theo luật §1.7/§4.4.3 của repo, `plan.md` là bản ghi tại-thời-điểm và không sửa lại; mục này chỉ ghi đính chính tại đây, không đụng vào `plan.md`.

## Kết luận

Migration 0013 lên DB thật thành công, seed lớp 2 đúng 161/161. Job `etl refdata` chạy dưới role `dlck_etl` idempotent qua nhiều lượt. Năm bất biến A/B/C/D/E đều đạt trên DB thật. Phép thử động spec §9 xác nhận luật phân giải hai lớp (override thắng ICB map) hoạt động đúng trên dữ liệu thật, và hệ thống phục hồi chính xác sau khi trả cấu hình về. Không phát hiện sai lệch cần dừng. Không sửa file code/migration nào trong task này.

## Task 7 — Đồng bộ tài liệu sống

Nguồn số liệu: mục "Kết luận" và Bước 3–4 ở trên (đo trên DB thật 2026-08-28). Không lấy số từ `plan.md` — xem đính chính ở mục trên (`plan.md:51` sai, số đúng 1.526/1.550).

### File đã sửa

| File | Sửa gì |
|---|---|
| `docs/20-design/industry-tree.md` §4 | Thêm gạch đầu dòng "Ai ghi cột nào" — lớp 1/lớp 2/view `v_issuer_industry` |
| `docs/20-design/README.md` | Dòng `industry-mapping.md`: bỏ "chưa nạp vào DB", ghi "đã nạp DB (migration `0013`: 55 dòng lớp 1 + 161 dòng lớp 2)" |
| `docs/00-overview/roadmap.md` mục [6] | Thay đoạn "⚠️ CHƯA NẠP" bằng trạng thái thật 2026-08-28, số đo từ ledger (1.526/1.550, A=0·B=0·C=161·D=55·E=none), nêu rõ [10] và khung ngành skill hết bị chặn |
| `database/README.md` | Thêm migration `0011`/`0012`/`0013` vào danh sách (10→13 migration, 37→49 test, 9→10 file); thêm mô tả `issuer_industry_override` + `v_issuer_industry`; thêm luật "đọc qua view, không đọc thẳng cột"; cập nhật dòng "Dữ liệu thật" với số ngành đã nạp |
| `docs/90-records/plans/2026-08-27-industry-two-layer-mapping/spec.md` | Chỉ dòng trạng thái đầu file: 🟡 chờ thực thi → ✅ thực thi xong, nghiệm thu 2026-08-28. Không đụng nội dung spec |
| `backend/README.md` | (a) Bỏ câu sai "Không bao giờ ghi `issuer.industry_id`" — thay bằng đoạn "Ngành hai lớp — luật đã đảo" giải thích ETL sở hữu lớp 1, đọc qua view `v_issuer_industry`. (b) Thêm đoạn giải thích cảnh báo `issuers_without_industry = 24` là trạng thái ổn định bình thường (24 quỹ/ETF `com_type_code='QU'`) |
| `docs/00-overview/architecture.md:95` *(ngoài brief, phát hiện qua quét chéo)* | Câu "ngành … CHƯA NẠP … tầng lọc ngành của tin vẫn chặn" — thay bằng "đã nạp DB 2026-08-28 … hết bị chặn" |
| `docs/90-records/README.md:28` *(ngoài brief, phát hiện qua quét chéo)* | Dòng trạng thái của hàng `2026-08-27-industry-two-layer-mapping/` trong index sống — 🟡 "code chờ thực thi" → ✅ "thực thi xong, nghiệm thu trên DB thật 2026-08-28", số đo cập nhật theo. Đây là index sống (§1.6), không phải nội dung bản ghi tại-thời-điểm, nên được cập nhật (khác với `spec.md`/`plan.md`/`layer2-review.md` bên trong cùng thư mục — giữ nguyên) |

### Phép kiểm chéo toàn repo (CLAUDE.md §1.7)

Lệnh chạy đúng nguyên văn brief:
```bash
git grep -n "chưa nạp\|CHƯA NẠP\|industry_icb_map\|YTEGD\|DIENNUOC\|TAINGUYEN\|VLXD" -- docs backend database
git grep -nw "BDS\|KCN" -- docs backend database
```
Tổng **94 dòng hit** (69 + thêm ở query BDS/KCN, nhiều dòng trùng giữa hai truy vấn). Phán quyết từng nhóm:

| Nhóm hit | Số dòng | Phán quyết | Vì sao |
|---|---|---|---|
| `backend/etl/refdata_store.py`, `backend/tests/etl/test_e09_refdata_store.py`, `backend/tests/schema/test_s02_identity.py`, `backend/tests/schema/test_s11_industry_override.py` | 9 | **Đã đúng** | Code/test thật, phản ánh đúng hành vi hiện tại (ETL sở hữu lớp 1 qua `industry_icb_map`). Task 7 không sửa code |
| `database/README.md:90` (cảnh báo downgrade 0003) | 1 | **Đã đúng** | Vẫn đúng kỹ thuật — downgrade qua `0003` vẫn xoá bảng `industry_icb_map` |
| `database/migrations/versions/0002_*.py`, `0003_seed_industry.py`, `0010_*.py`, `0011_industry_rename.py`, `0013_seed_industry_map.py` | 21 | **Đã đúng** | Migration đã chạy, không sửa lại (luật `database/README.md` §Luật: không sửa migration cũ). `0003`/`0011` cố ý giữ code cũ `BDS`/`KCN`/`VLXD`/`YTEGD`/`DIENNUOC`/`TAINGUYEN` để downgrade khôi phục đúng |
| `docs/10-sources/macro/verify_wichart.py:253`, `docs/10-sources/macro/wichart.md:185` | 2 | **Đã đúng — trùng chữ ngẫu nhiên** | `VLXD` ở đây là nhóm dữ liệu WiChart (vật liệu xây dựng vĩ mô), không liên quan mã ngành `industry.code` cũ |
| `docs/10-sources/market/field-dictionary.json:5990` | 1 | **Đã đúng — trùng chữ ngẫu nhiên** | `BDS` là viết tắt "bất động sản" trong công thức kế toán, không phải mã ngành |
| `docs/30-skills/corpus/.../Tra Chieu 2026-03-26.md:93` | 1 | **Đã đúng — trùng chữ ngẫu nhiên** | `BDS` = "bất động sản" trong hội thoại chat corpus, không phải mã ngành; corpus là bản ghi hội thoại tại-thời-điểm |
| `docs/20-design/gen_industry_mapping.py`, `docs/20-design/industry-mapping.json`, `docs/20-design/industry-mapping.md` | 21 | **Đã đúng — cấm sửa tay** | File sinh tự động, chủ là `gen_industry_mapping.py` (CLAUDE.md luật cứng). Nội dung `KCN`/`VLXD` ở đây là chuỗi lý do (`reason`) mô tả nghiệp vụ ("cả hai cùng KCN"), không phải mã ngành cũ — đúng như thiết kế |
| `docs/20-design/industry-tree.md:7,63-65,79,94,105` | 7 | **Đã đúng** | Đoạn "Rà lại 2026-08-27" và "Đổi so với bộ 24 tên gốc" **cố ý** ghi mã cũ để truy vết lịch sử đổi tên, đã tự gắn nhãn "để truy vết, không phải để dùng". Dòng 94 (`industry_icb_map`) là mô tả thiết kế đúng hiện trạng |
| `docs/20-design/README.md:16` (industry-mapping.md) | 1 | **Đã sửa** | Task 7 bước 2 |
| `docs/00-overview/roadmap.md:102` | 1 | **Đã sửa** | Task 7 bước 3 |
| `docs/00-overview/architecture.md:95,101` | 2 | **1 đã sửa (dòng 95), 1 đã đúng (dòng 101)** | Dòng 95 nêu "CHƯA NẠP" — sai, đã sửa. Dòng 101 mô tả vai trò ICB "tham khảo" — vẫn đúng, không sửa |
| `docs/90-records/plans/2026-08-25-postgres-data-schema/*` (ledger, plan, review, step-02, step-05) | 10 | **Thuộc vùng lịch sử** | `90-records/` là bản ghi tại-thời-điểm (CLAUDE.md §1.7) — không sửa nội dung. Không có href chết |
| `docs/90-records/plans/2026-08-26-reference-data-etl/ledger.md:54`, `spec.md:14,228` | 3 | **Thuộc vùng lịch sử** | nt — mô tả đúng quyết định "hoãn có chủ đích" tại thời điểm viết |
| `docs/90-records/plans/2026-08-27-industry-two-layer-mapping/layer2-review.md`, `plan.md` (toàn bộ, trừ mục tiêu sửa) | 27 | **Thuộc vùng lịch sử** | Nội dung `plan.md`/`layer2-review.md` không sửa (bản ghi tại-thời-điểm); chỉ `spec.md` được sửa đúng **dòng trạng thái** theo brief |
| `docs/90-records/plans/2026-08-27-industry-two-layer-mapping/spec.md` (thân bài, không phải dòng trạng thái) | 7 | **Thuộc vùng lịch sử** | Giữ nguyên — chỉ dòng trạng thái đầu file được sửa |
| `docs/90-records/plans/2026-08-27-industry-two-layer-mapping/ledger.md` | 5 | **Đã đúng** | Chính sổ ghi này — số liệu mô tả đúng lệnh/kết quả đã chạy |
| `docs/90-records/worksheets/README.md:31,78` | 2 | **Đã đúng** | Mô tả cách nạp (qua migration seed) — vẫn đúng nguyên xi sau khi migration `0013` đã chạy |
| `docs/90-records/README.md:28` | 1 | **Đã sửa** | Ngoài brief — phát hiện qua quét chéo, xem bảng "File đã sửa" ở trên |
| `backend/README.md` | 0 (không khớp pattern grep) | **Đã sửa** | **Không nằm trong Files-list của `task-7-brief.md` hay mục Task 7 của `plan.md`.** Sửa theo phán quyết của người điều phối, giao thẳng trong lời dispatch — phán quyết sinh từ review Task 4, khi phát hiện câu "Không bao giờ ghi `issuer.industry_id`" đã nói ngược luật mới sau khi ETL nhận quyền sở hữu cột đó. (a)+(b) thực hiện theo chỉ dẫn đó, không qua grep |

**Kết luận phép kiểm:** không còn hit nào mang tuyên bố sai về trạng thái "chưa nạp/CHƯA NẠP" ngoài vùng lịch sử hoặc trùng chữ ngẫu nhiên (đã kiểm lại bằng `git grep -n "chưa nạp\|CHƯA NẠP" -- docs backend database` sau khi sửa — 2 hit còn lại đều thuộc chủ đề khác, `vai_cotton_my`/đơn vị dữ liệu, không liên quan ngành). Không có link chết cần sửa href trong vùng lịch sử.

### Vòng sửa 1 — theo review Task 7 (2 finding Important, 1 Minor)

1. **Quy nguồn sai cho `backend/README.md`** — dòng cuối bảng "Phép kiểm chéo" ở trên từng ghi "brief chỉ ra tay". Sai: `task-7-brief.md` và mục Task 7 của `plan.md` **không nhắc file này**. Việc sửa là **có thẩm quyền** — người điều phối giao thẳng trong lời dispatch, phán quyết sinh từ review Task 4 (câu "Không bao giờ ghi `issuer.industry_id`" đã nói ngược luật mới). Đã sửa lại dòng đó cho đúng nguồn thẩm quyền; rà toàn bảng, không còn dòng quy nguồn sai nào khác.
2. **`docs/90-records/worksheets/README.md:32` nói ngược code, lọt lưới hai lệnh grep §1.7** — dòng "`market.issuer_industry_override` *(bảng chưa tồn tại — xem spec)*" không chứa từ khoá nào của hai lệnh grep bắt buộc nên không bị bắt. `worksheets/` là **đầu vào công việc** theo phân loại của `docs/90-records/README.md` (không phải bản ghi lịch sử), nên được và phải cập nhật. Đã sửa: bảng ghi rõ đã nạp qua migration `0012` (tạo bảng) + `0013` (seed 161 dòng), đo trên DB thật 2026-08-28; đồng thời cập nhật câu `COALESCE(lớp 2, lớp 1)` thêm tên view `market.v_issuer_industry` và mục "Nạp thế nào" đổi từ mô tả kế hoạch sang xác nhận đã chạy, trỏ tới chính ledger này thay vì §8 của spec. Rà hết phần còn lại của file — không còn câu nào nói bảng/view chưa tồn tại.
3. **[Minor] Neo số đo thiết kế trong `industry-tree.md` §4** — câu "24 ngành phủ 1.526/1.526 cổ phiếu có doanh nghiệp (đo 2026-08-27)" giữ nguyên số và ngày (đúng luật §1.2 — sửa số mà không đo là nói dối), thêm câu ngay sau xác nhận đã tái đo trên DB thật 2026-08-28 với hai bất biến `A=0` và `E=none`, kèm link ledger này.

Phép kiểm chéo chạy lại sau vòng sửa 1 (hai lệnh grep §1.7 nguyên văn) — không sinh hit mới, không có tuyên bố nào mâu thuẫn với ba chỗ vừa sửa.

## Vòng sửa 2 — đợt sửa duy nhất sau review toàn nhánh (2026-08-28)

Review toàn nhánh (không phải review Task 7 đơn lẻ như vòng sửa 1) sinh 8 finding, giao xử lý
trong một loạt, mỗi việc một commit hoặc gộp theo nhóm hợp lý. Bốn commit:

| Hash | Message | Việc phủ |
|---|---|---|
| `bd8865b` | docs(database): document layer-2 bootstrap order and downgrade warning | 1, 2 |
| `b7acf12` | fix(etl): runtime BCTC gate, correct gauge source, close two test gaps | 3, 4, 5, 6 |
| `3358a07` | fix(etl): strip whitespace from source icbCodePath | 7 |
| `640af10` | docs(industry-tree): clarify design vs measured row counts | 8 |

### Tám việc

1. **[Critical] Thứ tự bootstrap DB mới** — `database/README.md` §Luật thêm mục "Bootstrap DB mới":
   `upgrade head` → `etl refdata` một lượt → `downgrade 0012` rồi `upgrade head` (seed lại lớp 2) →
   kiểm `count(*) from market.issuer_industry_override` = 161. Lý do: migration `0013` seed lớp 2
   bằng `JOIN market.security` — DB dựng mới có `market.security` rỗng khi `0013` chạy ở bước 1 ⇒
   nạp 0 dòng, không exception, không có gì báo động.
2. **[Minor] Cảnh báo downgrade lạc hậu** — bổ sung câu cảnh báo downgrade qua `0012` (`DROP TABLE
   market.issuer_industry_override`, xoá cả bảng) bên cạnh câu cũ về downgrade qua `0003`.
3. **[Important] Chốt chặn luật BCTC lúc chạy** — `backend/etl/refdata_store.py` `apply()` chạy
   đúng câu `BCTC_PROBE` đã chuẩn hoá ở test (`test_e09_refdata_store.py`), ghi
   `stats["bctc_violations"]`, `log.warning` khi khác 0, không chặn job. Sửa
   `test_bctc_rule_is_bidirectional_on_view` khoá luôn giá trị `stats["bctc_violations"]` (không
   chỉ dò lại độc lập bằng `BCTC_PROBE` như trước).
4. **[Minor] Gauge đếm nhầm tầng** — `stats["issuers_without_industry"]` đổi từ đếm
   `market.issuer.industry_id IS NULL` (chỉ lớp 1) sang đếm qua `market.v_issuer_industry` (tay +
   máy). Đo lại trên DB thật (chỉ đọc): vẫn ra **24**, đều `com_type_code='QU'`, `icb_code='8985'`
   — khớp kỳ vọng, không dừng.
5. **[Important] Test "khớp chính xác thắng tổ tiên" không khoá được điều nó tuyên bố** — path thử
   của `test_layer1_exact_icb_match_wins_over_ancestor` đổi từ `'9000/9900/9990/9991'` (chứa chính
   mã lá) sang `'9000/9900/9990'` (không chứa) để chỉ nhánh khớp-chính-xác mới ra `DANDUNG`.
6. **[Important] Phép kiểm idempotency của `updated_at` không thể đỏ** — thêm chụp `xmin` của
   `market.issuer` trước/sau lượt hai. **Phát hiện thêm khi mutation-test:** `xmin` một mình KHÔNG
   đủ phân biệt trong fixture `db` (một transaction top-level cho cả test, không savepoint) — kiểm
   tay bằng psql xác nhận Postgres gán CÙNG một `xmin` cho mọi lần ghi trong cùng transaction bất
   kể ghi mấy lần. Đã tự sửa bằng `db.begin_nested()` (khuôn `expect_violation` sẵn có ở
   `tests/schema/conftest.py`) bọc quanh lượt `apply()` thứ hai, cho nó một subxact riêng —
   `re-review` xác nhận lập luận này đúng ngữ nghĩa MVCC.
7. **[Minor] `icb_code_path` có rác nguồn** — đo trên DB thật: dòng `icb_code='0580'` có
   `icb_code_path = '0001/0500/0580\r\n'` (1/176 dòng). Thêm `.strip()` khi chuẩn hoá
   `icbCodePath` trong `backend/etl/refdata_normalize.py`; thêm test
   `test_icb_code_path_strips_source_whitespace`. Dữ liệu cũ tự lành ở lượt refdata kế tiếp nhờ
   đuôi `IS DISTINCT FROM` của câu upsert `icb_industry`.
8. **[Minor] "40 dòng cấp 3" trong `industry-tree.md`** — làm rõ đó là con số THIẾT KẾ ở worksheet
   `industry-mapping.md`; DB thật (đo 2026-08-28, `market.industry_icb_map JOIN
   market.icb_industry`) là 39 dòng cấp 3 + 16 dòng cấp 4 = 55 dòng, vì `8980` "Quỹ đầu tư" cố ý
   không nạp. Không sửa file sinh tự động `industry-mapping.md`/`.json` — chỉ trỏ tới.

### Hai thí nghiệm đột biến (bắt buộc, việc 5 và 6)

**Việc 5** — tạm bỏ đối số thứ nhất của `COALESCE` trong khối 4c (nhánh khớp-chính-xác luôn
`NULL`):
```
tests/etl/test_e09_refdata_store.py::test_layer1_exact_icb_match_wins_over_ancestor FAILED
E   AssertionError: assert 'XAYDUNG' == 'DANDUNG'
1 failed in 0.77s
```
Trả lại nguyên trạng: `1 passed in 0.67s`.

**Việc 6** — tạm bỏ đuôi `AND iss.industry_id IS DISTINCT FROM r.industry_id` (UPDATE ghi lại mọi
dòng vô điều kiện):
```
tests/etl/test_e09_refdata_store.py::test_apply_twice_is_idempotent_including_timestamps FAILED
E   AssertionError: assert [(1, '5729'), ...] == [(1, '5728'), ...]
1 failed in 0.90s
```
Trả lại nguyên trạng: `1 passed in 0.82s`. `git diff` sau khi trả lại cả hai đột biến: không còn
dấu vết.

Test suite sau đợt sửa: `tests/etl` 58 passed, `tests/schema` 49 passed.

### Cố ý không sửa — ghi rõ để người sau khỏi tưởng bỏ sót

- **`database/migrations/versions/0013_seed_industry_map.py`** — không thêm
  `AND s.status = 'listed'` vào câu `JOIN market.security s ON s.ticker = l.ticker AND
  s.issuer_id IS NOT NULL` dù về lý thuyết một ticker delisted trùng tên với ticker listed có thể
  làm `DISTINCT ON (s.issuer_id) ... ORDER BY s.issuer_id, s.security_id` chọn nhầm dòng. Migration
  đã chạy trên DB thật — cấm sửa (`database/README.md` §Luật). Đo lại hôm nay (2026-08-28, chỉ
  đọc): 0 ticker trong danh sách seed 161 dòng bị trùng giữa security listed/delisted khác
  issuer_id, nên kết quả seed thực tế y hệt dù có thêm điều kiện hay không — không phải lỗi đang
  hoạt động sai, chỉ là rủi ro lý thuyết không đáng viết migration mới để vá.
- **Lưới `xmin` (việc 6) chỉ phủ `market.issuer`** — hai assert timestamp còn lại trong cùng test
  (`market.security.updated_at`, `market.security_external_id.ingested_at`) vẫn dùng
  `transaction_timestamp()` trần, không có `xmin` đi kèm, nên vẫn "không bao giờ đỏ vì lý do
  timestamp" y hệt lỗ hổng đã tả ở việc 6 — chỉ là nợ có sẵn của test này từ trước đợt sửa, không
  thuộc phạm vi tám việc được giao. Không mở rộng sửa quá phạm vi.

Re-review xác nhận: 8/8 finding ADDRESSED, không chặn merge.

---

## Phụ lục — việc thêm ngoài plan (chủ dự án yêu cầu 2026-08-28)

Không thuộc bảy task của plan này. Sau khi rà, chủ dự án hỏi luật *"cổ phiếu không có issuer thì đảo thành `delisted`, trừ ETF"* đã cài chưa. Câu trả lời: **chưa** — và chỗ nó đang nằm mới là vấn đề.

Chẩn đoán đầy đủ đã có từ [spec §7c](spec.md), nhưng **chỉ nằm trong `90-records/`** — vùng lịch sử. Roadmap không có mục nào, [market-data-store.md](../../../20-design/market-data-store.md) không có dòng nào. Đúng bẫy CLAUDE.md §1.1: xoá vùng lịch sử thì chỉ được mất lịch sử, mà ở đây sẽ mất luôn tri thức vận hành — bằng chứng là chủ dự án phải hỏi thay vì tra được.

**Đã kéo luật ra tài liệu sống** *(số đo lại trên DB thật 2026-08-28)*:

| File | Thêm gì |
|---|---|
| [market-data-store.md §4.4](../../../20-design/market-data-store.md) | Chủ sở hữu luật: bảng hai chiều vắng mặt · **438 cổ phiếu** không issuer vẫn `listed` (UPCOM 378 · HNX 39 · HOSE 21) · ba ràng buộc khi cài (chỉ `stock`; chốt chặn `DELIST_RATIO=0.01` sẽ từ chối lượt dọn đầu vì 438/1.962 = **22,3%**; cần lưới chống bắn nhầm mã mới niêm yết) · làm cùng lát phái sinh + `/datafeed/instruments`, xong trước ETL giá |
| [roadmap.md §5](../../../00-overview/roadmap.md) | Một dòng "việc còn thật sự để ngỏ", trỏ về §4.4 |
| [20-design/README.md](../../../20-design/README.md) | Bổ sung §4.4 vào mô tả `market-data-store.md` (§1.6 — đổi nội dung thì cập nhật index sở hữu cùng lượt) |

Số đối chiếu, đo trên DB thật 2026-08-28: tổng 2.015 security · **chỉ 4 dòng `delisted`** toàn kho · 1.962 cổ phiếu `listed` · 10 ETF + 18 chỉ số không có issuer (bình thường vĩnh viễn, phải loại trừ) · 3 chứng chỉ quỹ **có** issuer `com_type_code='QU'` nên không rơi vào diện này.

**Chưa chốt, cố ý để ngỏ:** vắng danh bạ bao nhiêu lượt liên tiếp thì mới lật `delisted`. Không có lưới này thì luật tự bắn vào mã vừa lên sàn — mã mới có thể vào bảng giá BVSC trước khi vào danh bạ FiinTrade.
