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

Cả hai thoát 0. Lượt hai `sec_inserted=0, sec_updated=0` đúng kỳ vọng (idempotent). `issuers_without_industry=24` cả hai lượt — khác 0 so với số đo tham chiếu bằng mô phỏng (0), nhưng chỉ số này đếm **toàn bộ issuer** (kể cả issuer không có chứng khoán `listed`), còn điều kiện đỗ chính thức A ở Bước 4 chỉ tính issuer có cổ phiếu `listed` — xem đối chiếu ở Bước 4.

## Bước 4 — Năm câu kiểm bất biến

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

Con số `issuers_without_industry=24` ở Bước 3 không mâu thuẫn với `A=0`: 24 issuer đó không có cổ phiếu `listed` (issuer trái phiếu/lô lẻ/chứng quyền hoặc chứng khoán delisted — các khối đã loại có chủ đích theo CLAUDE.md §2.2), nên không rơi vào phạm vi điều kiện A.

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

## Kết luận

Migration 0013 lên DB thật thành công, seed lớp 2 đúng 161/161. Job `etl refdata` chạy dưới role `dlck_etl` idempotent qua nhiều lượt. Năm bất biến A/B/C/D/E đều đạt trên DB thật. Phép thử động spec §9 xác nhận luật phân giải hai lớp (override thắng ICB map) hoạt động đúng trên dữ liệu thật, và hệ thống phục hồi chính xác sau khi trả cấu hình về. Không phát hiện sai lệch cần dừng. Không sửa file code/migration nào trong task này.
