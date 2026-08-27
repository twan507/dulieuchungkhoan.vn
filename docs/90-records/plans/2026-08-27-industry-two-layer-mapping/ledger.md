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
