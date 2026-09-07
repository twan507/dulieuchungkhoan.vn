# Ledger — dọn lệch tài liệu ↔ code

**Nhánh:** `fix/audit-drift-cleanup` · **Plan:** [`plan.md`](plan.md) · **Bằng chứng audit:** [`audit.md`](audit.md)

Mỗi task đi ba nhịp **K**iểm → **S**ửa → **X**ác nhận *(luật chủ dự án 2026-09-07)*. Sổ này ghi output thật của nhịp K và X.

---

## Task 1 — bộ kiểm tài liệu, đỏ trước ✅

**Làm gì:** `backend/tests/docs/test_d01_docs_consistency.py` — 7 phép kiểm thi hành CLAUDE.md §1.7.

**Nhịp K:** không có gì để kiểm (file mới). Chỉ kiểm một tiền đề: `backend/tests/conftest.py` đọc `TEST_DATABASE_URL` **trong fixture**, không lúc import ⇒ `tests/docs` chạy được khi shell chưa có `.env`. Xác nhận bằng cách chạy `uv run pytest tests/docs` **không** `--env-file` — không lỗi `KeyError`.

**Nhịp X — bộ kiểm ĐỎ 6/7, đúng các phát hiện của audit:**

```
6 failed, 1 passed in 0.51s

test_no_dead_internal_links       link nội bộ chết:
    …/2026-09-05-intraday-refresh/brief.md:3 -> ../../../CLAUDE.md
    …/2026-09-05-intraday-refresh/spec.md:50 -> ../../10-sources/global/yahoo.md
    …/2026-09-05-news-collect/spec.md:5 -> measure-news-2026-09-05.txt
test_no_orphan_plan_docs          file .md không index/ledger nào nhắc tên:
    …/2026-09-07-semantic-layer-closeout/reminder-ab-2026-09-07.md
    …/2026-09-07-semantic-layer-closeout/reminder-ab-transcript-2026-09-07.md
    …/2026-09-07-semantic-layer-closeout/round10-nhom-a-2026-09-07.md
test_migration_count_matches_docs số migration thật = 20, tài liệu nói khác:
    {'database/README.md (câu ánh xạ test)': '18', 'roadmap.md §0': '18',
     'README.md (bảng trạng thái)': '17', 'README.md (cây repo)': '17'}
test_sub_count_matches_code       heading nhóm nói {'1':6,'2':5,'3':9}, code nói {'1':6,'2':6,'3':9}
test_schema_test_count_matches_docs  database/README.md nói 14 file / 64 test; thật 15 file / 65 test
test_guard_constants_match_docs   backend/README.md thiếu '≥ 20 %' (MIN_PRICED_RATIO = 0.2)
```

Danh sách link chết và orphan **khớp đúng từng dòng** với audit §5 (C1, C3) — không thừa, không thiếu.

### Hai điều chỉnh trong lúc viết, ghi lại vì cả hai là bài học về chính công cụ đo

**1 · `test_no_orphan_plan_docs` xanh oan ở lượt chạy đầu.** Nguyên nhân: `audit.md` mà tôi vừa viết có **nhắc tên** cả ba file mồ côi trong bảng phát hiện ⇒ phép kiểm "có file `.md` nào nhắc tên không" thoả. Nhưng bị **trích dẫn trong một hồ sơ ở thư mục khác** không phải là **được index sở hữu** — §1.6 nói *index*, không nói *nhắc tới*. Siết lại: chủ sở hữu hợp lệ chỉ là **`README.md` bất kỳ** hoặc **`.md` cùng thư mục**. Sau khi siết: đỏ đúng 3 file.

> Đây đúng họ lỗi §1.3 của repo: *một phép đo thành công vẫn có thể trả lời sai câu hỏi.*

**2 · `test_crawl_source_count` bắt nhầm.** Regex `(\d+) crawl` khớp `"87 REST + 1 crawl"` ở `architecture.md:14` — dòng đó nói **trang OMO của SBV**, không phải nguồn tin. Siết thành `(\d+) crawler` hoặc `(\d+) nguồn crawl`.

### Phép kiểm này XANH ngay từ đầu — ghi rõ, không tô hồng

`test_crawl_source_count_matches_feeds_json` **xanh trước khi sửa gì**. Đúng như vậy: phát hiện **C9** không phải lỗi số — mọi tài liệu đang nói `6`, mà `6` là số nguồn crawl lượt thường thật (8 − 2 mục `chi_backfill`). C9 là chuyện **thiếu vế diễn đạt** (*"+2 sitemap backfill"*), máy không bắt được ⇒ **sửa tay ở Task 6**. Phép kiểm này giữ lại làm lưới cho tương lai: thêm nguồn crawl thứ 9 mà quên đồng bộ là nó đỏ.

**Đo:** toàn bộ 7 phép kiểm chạy **0,51 s**, không DB, không mạng — đạt kỳ vọng "< 2 s" của plan §7.

**Commit:** `test(docs): a red net for the doc-code drift the audit found`

---

## Task 2 — ba thứ làm theo là hỏng việc ✅

**Nhịp K** — cả ba còn đúng nguyên:

```
D1  grep FRED_API|AGENT_DATABASE_URL|LLM_TIMEOUT_S .env.example  -> rỗng
    code đọc thật: fred_fetch.py:40 raise RuntimeError("thiếu FRED_API")
                   agent/db.py:45   _engine("AGENT_DATABASE_URL")
                   core/llm/settings.py:30 env.get("LLM_TIMEOUT_S")
A1  screener_guard.py:11  MIN_PRICED_RATIO = 0.2   |  backend/README.md:102  "≥ 50 %"
A2  __main__.py:150-152   cờ --intraday/--backfill chỉ thêm khi args[0] in ("yahoo","binance")
```

**Nhịp S:**

- `.env.example` — thêm `AGENT_DATABASE_URL` (cạnh `ETL_DATABASE_URL`, cùng nhóm "user tạo per-môi-trường"), `FRED_API` (nhóm mới), `# LLM_TIMEOUT_S=120`. Giá trị đều là placeholder `change-me-in-production`; **không đọc, không chép gì từ `.env` thật** (§5).
- `backend/README.md:102` — `≥ 50 %` → `≥ 20 %`, **kèm 6 dòng lý do**: ngưỡng 0,5 đặt từ số đo trang 1, nhưng toàn thị trường giữa phiên chỉ 53,8 % ⇒ chỉ hơn ngưỡng 3,8 điểm; từ chối nhầm một phiên thật là mất vĩnh viễn. Tri thức này trước đó **chỉ sống trong comment của code** — nay lên tài liệu, đúng §1.1.
- `backend/README.md:321` — thay *"nhận cờ rồi bỏ qua"* bằng *"**không có cờ này** … truyền vào là `exit 2`"*, kèm trỏ `__main__.py:150-152`.

**Nhịp X:**

```
grep ^FRED_API|^AGENT_DATABASE_URL|LLM_TIMEOUT_S .env.example  -> 3 dòng, đúng chỗ
so khoá .env.example trước/sau:  MẤT: (không có)   THÊM: AGENT_DATABASE_URL, FRED_API
backend/README.md:102  "≥ 20 %"            backend/README.md:321  "không có cờ này"
pytest tests/docs -k guard  ->  1 passed
```

**Làm sớm hơn plan:** **D2** (chú thích 3 biến không ai đọc) làm luôn ở đây thay vì Task 7, vì cùng một file — đụng `.env.example` hai lượt là thừa. Theo quyết định plan §6.2: **giữ** `POSTGRES_PORT` · `REDIS_PORT` · `LOG_LEVEL`, chỉ thêm một dòng chú thích mỗi nhóm nói rõ "chưa code nào đọc".

**Commit:** `fix(docs): the three statements that break work if you follow them`

---

## Task 3 — `README.md` gốc ✅

**Nhịp K** — đo lại số thật trước khi ghi, không dùng lại số của audit:

```
ls database/migrations/versions/[0-9]*.py | wc -l        -> 20
pytest tests --collect-only -q                            -> 1036 collected  (1029 cũ + 7 test docs mới)
pytest tests -q                                           -> 5 failed, 1031 passed, 2 skipped in 85,50s
```

🔴 **Một điều lệch lộ ra ngay ở nhịp K, không có trong audit:** `--collect-only` cho **1036** trong khi lượt chạy thật cho **1031 passed + 2 skipped = 1033**. Tức bộ test có **vài test sinh lúc chạy**, không phải lúc thu. Vì thế **không được suy số passed từ số collected** — audit trước đó đã suýt làm vậy. Số cuối cùng chỉ chốt ở Task 9 bằng một lượt chạy thật.

**Nhịp S — 8 vị trí:**

| Dòng | Sửa |
|---|---|
| `:5` | 2026-09-05 → **2026-09-07**; *"6 job ETL"* → **15 họ job**; *"14 lát, lát 1–6 xong"* → **15 lát, lát 1–11 xong**; bỏ *"tiếp theo lát 6 giám sát hợp đồng"* → **lát 12 container** |
| `:5` | *"**596 test** xanh"* → trỏ `database/README.md`; *"test 6 vòng"* → **bộ hồi quy vòng 7**, kèm ghi chú bộ vòng 6 đã mất khỏi repo |
| `:16` | *"pipeline tin chưa"* → **đã cài** (lát 8/8b thu thập + 9a/9b lưới AI) |
| `:17` | *"🟡 đề xuất, chưa duyệt"* → ✅ **dựng lát 10, đóng hợp đồng lát 11** |
| `:20` · `:72` | `17 migration` → **20** |
| `:22` | *"đều `Disabled`"* → **10 `Disabled`, `dlck-price-backfill` `Ready`**; và nói rõ **chỉ 6/15 họ job có task**, chín họ còn lại chưa từng có lịch |
| `:67-71` | cây repo — liệt đủ 15 job `etl`, thêm nhánh `agent/` (lát 10) vốn không có trong cây |
| `:94` | bỏ số test, trỏ `database/README.md`; **thêm `--env-file ../.env` vào lệnh mẫu** — thiếu cờ này là hàng trăm `error` ở bước fixture, không phải test hỏng |

🔴 **Không chỉ vá số — giảm số chủ.** Con số test trước đây nằm ở **ba** chỗ trong chính `README.md` và **cả ba nói khác nhau** (596 · 640 · 456). Nay `README.md` **không còn nêu số test ở chỗ nào**; chủ duy nhất là `database/README.md`. Đây mới là bản sửa thật của §1.7; vá ba con số cho bằng nhau chỉ mua được vài tuần.

**Nhịp X:**

```
grep "596 test|640 test|456 passed" README.md              -> rỗng
grep "Postgres \*\*20 migration|migrations: Postgres 20"   -> 2 dòng
8 job từng thiếu (wichart fred fx lbma yahoo binance news classify) -> có đủ 8
pytest tests/docs -k migration -> lỗi còn lại chỉ là
    {'database/README.md (câu ánh xạ test)': '18', 'roadmap.md §0': '18'}   ← Task 4
pytest tests/docs -q -> 5 failed, 2 passed  (từ 6 failed, 1 passed)
```

**Commit:** `docs: the root README was two days and eleven slices behind`

---

## Task 4 — `roadmap.md` §0 và `database/README.md` ✅

**Nhịp K** — đo lại toàn bộ số sẽ ghi:

```
migration                 20
schema test: file 15 · func 65
registry build():  fred 14 | fx 7 | lbma 2 | yahoo 54 | binance 11
roadmap:19   "chưa viết dòng code nào"
roadmap:29   "18 migration"
roadmap:124  "15 + 6 + 2 + 37 + 11 series"
roadmap:586  "11 task Scheduler vẫn Disabled"
```

**Nhịp S:** B8 · B9 · B10 · B11 · B12 · B13 sửa theo plan.

### A13 — làm KHÁC plan, có lý do

Plan viết *"`15 + 6` → `14 + 7`"*. **Không làm vậy.** Nhịp K lộ ra hai điều plan chưa biết:

1. Dòng 124 là **bản ghi lúc đóng lát 7** (`✅ XONG 2026-09-05`), không phải trạng thái hôm nay. `DEXCHUS` bị bỏ ở **lát 7b**, tức lúc lát 7 đóng thì FRED **thật sự có 15** — sửa thành 14 là **viết lại quá khứ cho sai đi**, đúng thứ §1.7 cấm.
2. Yahoo nay là **54** chứ không phải 37 (lát 7b thêm 17 cặp FX) — plan cũng không biết.
3. `6` của fx là số **cặp tiền**, không phải số series; series có thêm DXY dựng lại ⇒ 7. Đây là lệch **đơn vị đếm**, không phải lệch số.

Nên: **giữ nguyên dòng số cũ**, thêm 4 dòng chú thích ngay dưới ghi registry hôm nay (`build()`, đo 2026-09-07) và nói rõ hai chỗ lát 7b làm đổi. Bản ghi at-the-time còn nguyên, người đọc không bị dẫn sai.

### B13 — cũng làm khác plan một chút

Plan định bỏ hẳn số ở `database/README.md:86`. Nhưng dòng đó mang **chuỗi lịch sử tăng trưởng** (877 → 809 → 791 → 729 → …) — dữ liệu có giá trị, không phải bản sao rác. Giữ chuỗi, chỉ đổi cách mở đầu để không ai đọc nhầm nó là số hôm nay: *"số hiện hành ở ngay dưới — mục này chỉ giữ lịch sử tăng trưởng"*.

**Nhịp X:**

```
grep -c "18 migration" roadmap.md              -> 0
grep "chưa viết dòng code nào" roadmap.md      -> không còn
roadmap:590  "**10/11** task Scheduler Disabled ... ngoại lệ dlck-price-backfill Ready"
grep "64 test|14 file|877 test, 2 skipped" database/README.md -> không còn
pytest tests/docs -q  ->  3 failed, 4 passed   (từ 5 failed, 2 passed)
    còn lại: dead_links + orphan (Task 6) · sub_count (Task 5)
```

**Commit:** `docs: bring the roadmap and database README back to the real counts`
