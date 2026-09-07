# Plan — dọn lệch tài liệu ↔ code sau đợt audit 2026-09-07

**Ngày:** 2026-09-07 · **Nhánh:** `fix/audit-drift-cleanup` · **Trạng thái:** chủ dự án gọi tên *("viết plan đi, sửa từng bước, mỗi bước trước khi sửa đều phải kiểm lại rồi mới sửa")*

**Nguồn:** đợt audit độc lập 2026-09-07 — 47 phát hiện, **mọi phát hiện đã xác thực bằng lệnh chạy thật** trước khi vào plan này. Bằng chứng từng mục nằm ở [`audit.md`](audit.md) cùng thư mục.

**Đây không phải lát tính năng.** Không thêm hành vi mới, không đổi thiết kế. Chỉ làm ba việc: *(1)* kéo tài liệu về khớp code, *(2)* vá hai lỗ hổng test lộ ra trong lúc audit, *(3)* dựng bộ kiểm tự động để §1.7 không còn phụ thuộc trí nhớ người viết.

---

## 1. Vì sao lát này tồn tại

Audit kết luận một câu: **code khoẻ, tài liệu là chỗ bị trôi.**

| Trục | Tình trạng đo được |
|---|---|
| Dead code | ~không có — 0/117 module mồ côi, 0 TODO/FIXME, 0 lỗi ruff trong code sản phẩm |
| Test | 1.029 passed / 2 skipped / exit 0 (chạy thật 2026-09-07, 86,25 s) |
| **Tài liệu ↔ code** | **13 chỗ nói sai** |
| **Tài liệu ↔ tài liệu** | **13 chỗ lệch số/trạng thái** — `README.md` gốc chứa *ba* giá trị số test khác nhau |
| Dead doc | 3 file `.md` không index nào biết · 1 mục index trỏ file chưa từng commit · 3 link chết |

Nguyên nhân gốc: **một sự thật có nhiều chủ.** Số test nằm ở 4 nơi, số migration 3 nơi, số sub taxonomy 5 nơi. CLAUDE.md §1.7 đã cấm đúng bệnh này nhưng **không có phép kiểm nào thi hành nó** — ba lần đồng bộ gần nhất (thêm `2f`, hạ ngưỡng screener, thêm migration `0019`/`0020`) đều quên. Vì vậy Task 1 dựng bộ kiểm **trước**, các task sửa đứng sau.

## 2. Luật thực thi — chủ dự án chốt

> **"Mỗi bước trước khi sửa đều phải kiểm lại rồi mới sửa."**

Mỗi task đi đúng ba nhịp, không nhịp nào được bỏ:

| Nhịp | Việc | Ghi vào ledger |
|---|---|---|
| **K** — Kiểm | Chạy lệnh đọc **lại** cả hai vế (tài liệu và code/số thật) ngay trước khi sửa. Audit viết cách đây vài giờ; nếu vế nào đã đổi thì phát hiện đó **không còn đúng** và phải bỏ khỏi task | output thật của lệnh |
| **S** — Sửa | Chỉ sửa đúng chỗ đã kiểm ở nhịp K. Không "tiện tay" sửa dòng lân cận *(CLAUDE.md §4.4.3)* | diff tóm tắt |
| **X** — Xác nhận | Chạy lại chính lệnh của nhịp K, phải cho kết quả khớp | output thật |

Thêm ba luật cứng:

1. **Vùng lịch sử không viết lại.** `docs/90-records/` và `00-overview/decisions/` chỉ được sửa **href** của link chết, giữ nguyên nhãn hiển thị *(§1.7)*. Task 6 áp luật này.
2. **Tầng `10-sources/` chỉ sửa khi đo lại** *(§1.2)*. Lát này **không gọi API nào**, nên chỉ được sửa ở đó những thứ **không phải số đo**: đường dẫn host đã có bản đo mới ghi ở file khác, và mục lục. Cấm chạm mọi con số đo.
3. **Commit theo mốc** *(§4.7)* — mỗi task xong là một commit riêng, message tiếng Anh, Conventional Commits.

## 3. Tiêu chí nghiệm thu

| AC | Nội dung | Cách kiểm |
|---|---|---|
| **AC1** | Bộ kiểm tài liệu mới **đỏ trước khi sửa, xanh sau khi sửa** | `uv run --env-file ../.env pytest tests/docs -q` — chạy ở Task 1 phải FAIL, chạy ở Task 9 phải PASS |
| **AC2** | Toàn bộ test cũ **không hồi quy** | `pytest tests -q` ≥ 1.029 passed, 2 skipped, exit 0 |
| **AC3** | 47 phát hiện đều có kết cục ghi tên: **đã sửa** · **cố ý không sửa (kèm lý do)** · **hết đúng khi kiểm lại** | bảng §5 của [`ledger.md`](ledger.md), không mục nào trống |
| **AC4** | 0 link nội bộ chết ngoài khối code | test `test_no_dead_internal_links` |
| **AC5** | 0 file `.md` mồ côi trong `90-records/plans/` | test `test_no_orphan_plan_docs` |
| **AC6** | `ruff check backend --select F` = 0 lỗi | chạy thật |
| **AC7** | `git grep "\[DEBUG-"` trong `backend/` = 0 *(luật CLAUDE.md §4.6 lần đầu thật sự dùng được)* | chạy thật |
| **AC8** | `python -m etl fred --dry-run --keys us.cpi` vẫn chạy được sau khi đụng `.env.example` | chạy thật, exit 0 |

## 4. Ánh xạ 47 phát hiện → task

| Task | Lô | Mục | Vì sao gom chung |
|---|---|---|---|
| **T1** | bộ kiểm | — | Dựng lưới trước, để chính nó chứng minh 5 nhóm sau đã sửa xong |
| **T2** | chặn người dùng | **D1 · A1 · A2** | Ba thứ mà làm theo là hỏng việc thật — sửa trước tiên |
| **T3** | README gốc | **B1–B7** | Một file, một lượt |
| **T4** | roadmap + database/README | **B8–B13 · A13** | Số cơ học |
| **T5** | 20-design + architecture | **A3–A12** | Cần đọc hiểu, không dán số |
| **T6** | index & dead doc | **C1–C9** | Cơ học; C3 chỉ sửa href |
| **T7** | code & config | **D2 · D3 · D9 · D10 · D11 · D12** | Đụng file ngoài `docs/` |
| **T8** | lỗ hổng test | **D6 · D7 · D8** + quyết **D4 · D5** | Viết test thật, TDD |
| **T9** | nghiệm thu | — | Chạy trọn, viết ledger, báo cáo |

---

## 5. Chi tiết từng task

### Task 1 — Bộ kiểm tài liệu, đỏ trước

**File mới:** `backend/tests/docs/test_d01_docs_consistency.py` (+ `__init__.py` nếu cần cho `pythonpath`).

**Seam đã chốt:** file markdown trong repo + số thật lấy từ filesystem/code. Test **không** gọi DB, **không** gọi mạng — chạy được cả khi không có `.env`.

🔴 **Luật chọn phép kiểm** *(CLAUDE.md §4.4.4 — tiêu chí phải bất biến, không phải số thời điểm)*: chỉ kiểm **"hai biểu diễn của cùng một sự thật phải khớp nhau"**. **Cấm** hardcode một con số của hôm nay vào test — vì thế **không kiểm số test** (thêm một test là đỏ oan, đúng loại tiêu chí tự vi phạm mà §4.4.4 cảnh báo).

Bảy phép kiểm:

| # | Tên test | Bất biến |
|---|---|---|
| 1 | `test_no_dead_internal_links` | Mọi link markdown nội bộ, **bỏ qua dòng trong khối ` ``` `**, phải trỏ tới file/thư mục có thật |
| 2 | `test_no_orphan_plan_docs` | Mọi `.md` trong `docs/90-records/plans/*/` phải được **một file `.md` khác nhắc đúng tên** |
| 3 | `test_migration_count_matches_docs` | Số nêu trong `database/README.md`, `roadmap.md`, `README.md` == số file `database/migrations/versions/*.py` |
| 4 | `test_sub_count_matches_code` | Số sub nêu trong `news-pipeline.md` == `len(etl.news_classify.ALL_SUBS)` **trừ nhãn `x`** |
| 5 | `test_schema_test_count_matches_docs` | Số file + số test seam nêu ở `database/README.md` == đếm thật trong `backend/tests/schema/` |
| 6 | `test_crawl_source_count_matches_feeds_json` | Số nguồn crawl nêu trong tài liệu == `len(feeds.json["crawl_html"])`, và số "lượt thường" == số mục **không** có `chi_backfill` |
| 7 | `test_guard_constants_match_backend_readme` | `MIN_PRICED_RATIO`, `DELIST_RATIO`, `DIRECTORY_ABSENT_DAYS` nêu trong `backend/README.md`/`market-data-store.md` == hằng số thật trong code |

**Nhịp K:** chưa có gì để kiểm — đây là file mới.
**Nhịp S:** viết file.
**Nhịp X:** `cd backend && uv run pytest tests/docs -q` → **phải ĐỎ**, và phải đỏ ở **7/7** test (nếu test nào xanh ngay thì hoặc phát hiện tương ứng đã sai, hoặc test viết hỏng — phải điều tra, không được đi tiếp).

**Commit:** `test(docs): a red net for the doc-code drift the audit found`

---

### Task 2 — Ba thứ làm theo là hỏng việc

#### D1 · `.env.example` thiếu hai biến của đường production

**K:**
```bash
grep -n "FRED_API\|AGENT_DATABASE_URL\|LLM_TIMEOUT_S" .env.example        # kỳ vọng: rỗng
grep -n "FRED_API" backend/etl/fred_fetch.py backend/etl/fred_job.py
grep -n "AGENT_DATABASE_URL" backend/agent/db.py
grep -n "LLM_TIMEOUT_S" backend/core/llm/settings.py
```
**S:** thêm vào `.env.example`, đặt cạnh nhóm cùng loại, **giá trị placeholder, không phải khoá thật**:
- `FRED_API=` dưới một nhóm mới `# FRED (docs/10-sources/global/fred.md) — khoá miễn phí, đăng ký bằng email dự án`
- `AGENT_DATABASE_URL=postgresql+psycopg://agent_reader:...@127.0.0.1:5432/dulieu` cạnh `ETL_DATABASE_URL`, kèm chú thích trỏ `database/README.md` mục tạo user
- `# LLM_TIMEOUT_S=120` cạnh hai biến LLM đang comment sẵn

🔴 **Không in, không chép giá trị thật từ `.env`** *(CLAUDE.md §5)*.

**X:** `grep -c "FRED_API\|AGENT_DATABASE_URL" .env.example` = 2; và `diff <(grep -o '^[A-Z_]*' .env.example | sort -u) …` xác nhận không xoá nhầm biến nào.

#### A1 · Ngưỡng guard screener

**K:**
```bash
grep -n "MIN_PRICED_RATIO" backend/etl/screener_guard.py
sed -n '100,104p' backend/README.md
```
**S:** `backend/README.md:102` — đổi `≥ 50 %` thành `≥ 20 %`, và **ghi thêm lý do hạ ngưỡng** (số đo 831/1545 = 53,8 % giữa phiên) vì đó chính là tri thức vận hành mà comment trong code đang giữ một mình.
**X:** chạy lại hai lệnh của nhịp K, số khớp.

#### A2 · Cờ `--intraday` của FRED/ECB/LBMA

**K:**
```bash
sed -n '144,157p' backend/etl/__main__.py
sed -n '314p' backend/README.md
cd backend && uv run python -m etl fred --intraday; echo "EXIT=$?"     # kỳ vọng EXIT=2
```
**S:** `backend/README.md:314` — thay *"FRED/ECB/LBMA nhận cờ rồi bỏ qua"* bằng *"FRED/ECB/LBMA **không có** cờ này — truyền vào là `exit 2` (`unrecognized arguments`)"*.
**X:** chạy lại lệnh, câu trong README khớp hành vi.

**Commit:** `fix(docs): the three statements that break work if you follow them`

---

### Task 3 — `README.md` gốc

Không viết lại toàn file *(scope creep)*. Sửa đúng 8 vị trí đã xác thực.

**K (một lệnh, đọc hết vùng phải sửa):**
```bash
sed -n '5p;16,17p;20p;22p;67p;69,70p;92p' README.md
cd backend && uv run --env-file ../.env pytest tests --collect-only -q | tail -1
ls database/migrations/versions/*.py | wc -l
```

**S:**

| Dòng | Sửa thành |
|---|---|
| `:5` | Trạng thái **2026-09-07**; số test **1.029**; *"lát 1–11 xong, tiếp theo **lát 12 chạy được trong container**"*; bỏ câu *"tiếp theo lát 6 giám sát hợp đồng"* |
| `:16` | *"pipeline tin **đã cài** — thu thập lát 8/8b, lưới AI lát 9a"* |
| `:17` | *"✅ **dựng lát 10, đóng hợp đồng lát 11 (2026-09-07)** — 9 function + vòng chat terminal"* |
| `:20` · `:70` | **20 migration** |
| `:22` | *"**10/11** `Disabled`, `dlck-price-backfill` `Ready`"* |
| `:67` | thêm 8 job còn thiếu vào danh sách `etl` |
| `:69` | **1.029 test** *(2026-09-07)* |
| `:92` | kỳ vọng **1.029 passed, 2 skipped**, và thêm `--env-file ../.env` vào lệnh mẫu *(database/README.md:92 đã đo: thiếu cờ này là 425 error)* |

🔴 **Chống tái phát ngay trong task này:** ba chỗ mang số test (`:5`, `:69`, `:92`) — giữ **một** chỗ nêu số (`:92`, chỗ hướng dẫn chạy), hai chỗ kia đổi sang trỏ `database/README.md`. Đây là áp §1.7 chứ không chỉ vá số.

**X:** chạy lại `sed` của nhịp K; và `uv run pytest tests/docs -q -k migration` phải xanh.

**Commit:** `docs: the root README was two days and eleven slices behind`

---

### Task 4 — `roadmap.md` §0 và `database/README.md`

**K:**
```bash
sed -n '19p;29,30p;124p;586p' docs/00-overview/roadmap.md | cut -c1-200
sed -n '18p;86p' database/README.md | cut -c1-200
ls backend/tests/schema/test_s*.py | wc -l
cd backend && uv run --env-file ../.env pytest tests/schema --collect-only -q | tail -1
uv run python -c "import sys;sys.path.insert(0,'.');import etl.fred_registry as f,etl.fx_registry as x;print(len(f.build()),len(x.build()))"
```

**S:**

| Mục | Vị trí | Sửa |
|---|---|---|
| B8 | `roadmap.md:29` | `18 migration` → `20 migration` |
| B9 | `roadmap.md:19` | `chưa viết dòng code nào` → `đã cài lát 8 · 8b · 9a` |
| B10 | `roadmap.md:30` | nối tiếp chuỗi trạng thái: thêm lát 9b · 10 · 11 |
| B11 | `roadmap.md:586` | thêm ngoại lệ `dlck-price-backfill Ready` |
| A13 | `roadmap.md:124` | `15 + 6 + 2 + 37 + 11` → `14 + 7 + 2 + 37 + 11`, kèm *(FRED bỏ `DEXCHUS` ở lát 7b)* |
| B12 | `database/README.md:18` | `không 1-1 với 18 migration` → `20`; `64 test` → **65**; `14 file` → **15**; bổ sung ánh xạ `test_s16 ← 0019` và ghi rõ **`0020` không có test schema riêng** |
| B13 | `database/README.md:86` | `877 test` → `1.029` *(hoặc bỏ số, trỏ dòng 92 — chọn bỏ số để §1.7 chỉ còn một chủ)* |

**X:** chạy lại nhịp K; `pytest tests/docs -q -k "migration or schema_test"` xanh.

**Commit:** `docs: bring the roadmap and database README back to the real counts`

---

### Task 5 — `20-design/` và `architecture.md`

**K (đọc cả hai vế từng mục):**
```bash
grep -n "20 sub\|(5 sub)" docs/20-design/news-pipeline.md
cd backend && uv run python -c "import sys;sys.path.insert(0,'.');import etl.news_classify as c;print(c.SUBS)"
sed -n '140,145p' docs/00-overview/architecture.md
grep -n "^## " docs/30-skills/maintenance.md
sed -n '577,584p;613,616p' docs/20-design/market-data-store.md
grep -rn "CREATE VIEW" database/migrations/versions/*.py
sed -n '98,112p' database/migrations/versions/0004_market_data.py
sed -n '254,258p' docs/20-design/news-pipeline.md
grep -n "summary_ai" backend/etl/news_classify.py
sed -n '7p' docs/20-design/chatbot-semantic-layer.md
sed -n '6,10p' docs/20-design/test-strategy.md
grep -n "respx\|pytest.asyncio" backend/pyproject.toml backend/uv.lock
sed -n '114,124p' docs/20-design/service-topology.md
ls backend/agent backend/agent/tools
sed -n '49p' docs/10-sources/README.md
grep -n "frankfurter" backend/etl/fx_fetch.py docs/10-sources/global/fx.md
```

**S:**

| Mục | Vị trí | Sửa |
|---|---|---|
| A3 | `news-pipeline.md:5,21,55,418` + heading `:70` | `20 sub` → **21 sub**; `Nhóm 2 (5 sub)` → `(6 sub)` |
| A4 | `architecture.md:140` §4 | Đổi tiêu đề và thân: lỗ hổng **đã vá lát 10** bằng `SCOPE_GUARD` ở `backend/agent/system_prompt.py`; giữ phần mô tả lỗ hổng làm bối cảnh vì sao phải vá ở tầng sản phẩm |
| A5 | `architecture.md:144` | `maintenance.md §5` → `§7` |
| A6 | `market-data-store.md:577-584` | Sửa DDL: thêm cột `dictionary text NOT NULL CHECK (…)`, `PRIMARY KEY (dictionary, code)`; sửa câu *"Nạp từ Screener… 83 tiêu chí"* thành **hai nguồn** (83 tiêu chí Screener + 729 mã BCTC) |
| A7 | `market-data-store.md:615` | Ghi rõ **5 view chưa dựng và đã hết cần thiết** — function calling (§6.3) thay vai trò; nêu 3 view thật có trong kho |
| A8 | `news-pipeline.md:256` | comment `summary_ai` → *"3–5 câu ngắn, súc tích — xem 7.1"* |
| A9 | `chatbot-semantic-layer.md:7` | *"Phần ở giữa thì chưa ai viết"* → *"Phần ở giữa nay đã dựng — lát 10"* |
| A10 | `test-strategy.md:8` | Bỏ `pytest-asyncio` và `respx`; ghi đúng: `pytest` + `httpx.MockTransport`, test async chạy bằng `asyncio.run(...)` |
| A11 | `service-topology.md:117-123` | Cây `backend/` — tách `agent/` thành mục riêng có `tools/` (9 công cụ) và `skills/`, ghi *(lát 10, 2026-09-07)* giống cách đã ghi cho `core/llm/` |
| A12 | `10-sources/README.md:49` | `api.frankfurter.app` → `api.frankfurter.dev/v1` *(đo 2026-09-05 — bản đo nằm ở `global/fx.md:13`, đây chỉ là đồng bộ mục lục, không phải sửa số đo)* |

**X:** chạy lại nhịp K; `pytest tests/docs -q -k "sub_count or crawl"` xanh.

**Commit:** `docs: the design layer said things the code stopped doing`

---

### Task 6 — Index và dead doc

**K:**
```bash
for f in reminder-ab-2026-09-07 reminder-ab-transcript-2026-09-07 round10-nhom-a-2026-09-07; do echo -n "$f: "; git grep -c "$f" -- docs | wc -l; done
sed -n '40p;45p;53,54p' docs/90-records/README.md | cut -c1-160
find docs -name "measure-news-2026-09-05.txt"
sed -n '3p' docs/90-records/plans/2026-09-05-intraday-refresh/brief.md
sed -n '50p' docs/90-records/plans/2026-09-05-intraday-refresh/spec.md
sed -n '5p' docs/90-records/plans/2026-09-05-news-collect/spec.md
sed -n '63,67p' docs/README.md
grep -c "^### Bẫy" docs/10-sources/market/00-conventions.md
```

**S:**

| Mục | Sửa | Ghi chú luật |
|---|---|---|
| C1 | `90-records/README.md` dòng lát 11 — liệt đủ tên file trong thư mục, theo đúng khuôn dòng lát 10 liền trên | thêm mục lục, không sửa nội dung file lịch sử |
| C2 | `90-records/README.md:40` — bỏ `measure-news-2026-09-05.txt` khỏi danh sách, ghi *(chưa từng commit)* giống cách `news/README.md:370` đã làm | |
| C3 | 3 link chết: `brief.md:3` `../../../` → `../../../../` · `intraday spec.md:50` `../../` → `../../../` · `news-collect spec.md:5` bỏ link, giữ nhãn | 🔴 **chỉ sửa href, giữ nguyên nhãn hiển thị** (§1.7) |
| C4 | `docs/README.md:63-67` — thay bảng chép lại bằng câu dẫn sang `30-skills/README.md`, đúng khuôn đã dùng cho `decisions/` và `20-design/` | |
| C5 | `90-records/README.md:53-54` — bỏ bảng, giữ câu dẫn sang `worksheets/README.md` | |
| C6 | `10-sources/README.md` §2(b) — thêm dòng `DEXCHUS (CNY/USD, FRED)` → *đã có đường khác: ECB* | §1.4 ba loại |
| C7 | `00-conventions.md:169` — `Mười ba bẫy` → `Mười bốn bẫy` **hoặc** đổi `Bẫy 4b` thành `Bẫy 14`. **Chọn: đổi tiêu đề**, vì đánh số lại làm chết mọi tham chiếu chéo `Bẫy 5..13` | không đụng nội dung bẫy = không đụng số đo |
| C8 | `terminology.md:3` — bỏ *"cho Giai đoạn 3"* | từ vựng thời dự án skill, nay vô nghĩa |
| C9 | 8 chỗ *"47 RSS + 6 crawler"* — đổi thành `47 RSS + 8 crawl (6 lượt thường + 2 sitemap backfill)` | khớp chủ sở hữu `news/README.md:7` |

**X:** `pytest tests/docs -q -k "dead_link or orphan or crawl"` xanh.

**Commit:** `docs: three orphan files, one index entry pointing at nothing, three broken hrefs`

---

### Task 7 — Code, config, vệ sinh

**K:**
```bash
grep -n "POSTGRES_PORT\|REDIS_PORT\|LOG_LEVEL" .env.example
git grep -n "POSTGRES_PORT\|REDIS_PORT\|LOG_LEVEL" -- backend scripts deploy database
sed -n '625,630p' docs/20-design/gen_industry_mapping.py
sed -n '928,932p' docs/20-design/gen_field_selection.py
cat .gitattributes
git grep -n "\[DEBUG-" -- backend
cd backend && uvx ruff check . --select F --exclude .venv
cat ../package.json
git branch --merged main | grep -v main
```

**S:**

| Mục | Sửa |
|---|---|
| D2 | `.env.example` — **giữ** `POSTGRES_PORT`/`REDIS_PORT` (compose đọc `POSTGRES_HOST`/`REDIS_HOST` cùng nhóm, và cả bộ này là hồ sơ hạ tầng cho lát 12) nhưng thêm một dòng chú thích *"chưa code nào đọc — giữ cho lát 12"*; **`LOG_LEVEL`** cũng vậy. 🔴 **Không xoá** — quyết định ở §6.2 |
| D3 | `gen_industry_mapping.py:627-628` — dùng `with open(..., newline="\n")` cho cả hai file, khớp `gen_field_selection.py`; thêm 2 dòng `eol=lf` cho `industry-mapping.*` vào `.gitattributes`. **Sau đó sinh lại và diff phải rỗng** |
| D9 | `ruff check --fix` cho 9 lỗi tự sửa được; 2 biến gán không dùng (`test_e34:69`, `test_i13:237`) sửa tay — đọc ngữ cảnh trước, có thể là assertion bị quên |
| D10 | `test_c99_dedup_probe.py:125-126` — đổi tiền tố `[DEBUG-VPS]` → `[probe]` *(diag hợp lệ của probe chạy tay, chỉ đang mượn tiền tố mà §4.6 dành cho log tạm)* |
| D11 | `package.json` — thêm `"test": "node --test scripts/stack.test.mjs"`; nhắc tới trong `database/README.md` mục chạy test |
| D12 | Xoá 15 nhánh local đã merge + 2 nhánh remote cũ. **Nhánh hiện tại không nằm trong danh sách** — kiểm trước khi xoá |

**X:** `uvx ruff check . --select F` = 0; `git grep "\[DEBUG-" backend` = 0; sinh lại 4 file generator → `diff` rỗng; `npm test` = 7/7.

**Commit:** tách hai — `chore: retire the leftovers the audit turned up` và `chore(git): delete the fifteen branches already merged`

---

### Task 8 — Hai lỗ hổng test, và quyết `flush_once`/`label_for`

#### D6 · `phan_ure` — 2 series sống, 0 test

**K:**
```bash
grep -n "phan_ure" backend/etl/wichart_registry.py
grep -n "_series(" backend/tests/etl/test_e38_wichart_normalize.py
PYTHONIOENCODING=utf-8 python -c "import json;d=json.load(open('backend/tests/etl/fixtures/wichart/phan_ure.json',encoding='utf-8'));print(type(d), list(d)[:5] if isinstance(d,dict) else len(d))"
```

**S:** thêm test vào `test_e38_wichart_normalize.py` cho cả `("phan_ure", 0)` (`urea_phumy`) và `("phan_ure", 1)` (`urea_camau`).

🔴 **Chống test tautological** *(§4.5.3)*: giá trị kỳ vọng **đọc thẳng từ JSON fixture bằng mắt** (một cặp `[epoch, value]` cụ thể), rồi tự tính ngày theo `Asia/Ho_Chi_Minh` **bằng tay** — **không** chạy `series_points()` rồi chép output. Đơn vị `VND/kg` và `scale` lấy từ registry, kiểm dải giá trị hợp lý.

**X:** test mới chạy xanh; và **chứng minh nó có tác dụng** bằng đột biến — tạm đổi `Asia/Ho_Chi_Minh` thành `UTC` trong `wichart_normalize`, test phải ĐỎ, rồi hoàn nguyên.

#### D8 · NguoiQuanSat — 4 feed RSS sống, 0 test parse

**K:**
```bash
PYTHONIOENCODING=utf-8 python -c "import json;d=json.load(open('docs/10-sources/news/feeds.json',encoding='utf-8'));print([f['url'] for k in ('1_vi_mo_trong_nuoc','2_tai_chinh_quoc_te','3_doanh_nghiep_niem_yet') for f in d[k] if 'nguoiquansat' in f['url']])"
grep -n "_feed(" backend/tests/etl/test_e52_news_parse.py
head -30 backend/tests/etl/fixtures/news/feed-nguoiquansat.xml
```
**S:** thêm `_feed("nguoiquansat")` vào `test_e52_news_parse.py`, assert `published_at` và tiêu đề của bài đầu — **literal đọc từ chính file XML**, giống khuôn 6 nguồn đang có.
**X:** test xanh; `feed-nguoiquansat.xml` hết mồ côi.

#### D7 · `wichart/tn.json`

**K:** `grep -n "tn" backend/tests/etl/test_e38_wichart_normalize.py`
**S:** `tn` **đã có test** nhưng bằng literal gõ tay. Đổi test đó sang dùng `_series("tn")` — bản thu thật — giữ nguyên assertion nếu khớp; nếu không khớp thì **dừng và báo**, vì nghĩa là literal cũ sai.
**X:** test xanh, fixture hết mồ côi.

#### D4 · `ChWriter.flush_once` — quyết sau khi đọc

**K:** đọc `chwriter.py:590-610`. **Nếu** thân hàm đúng bằng `manage_once(); write_once()` thì rủi ro "test đi đường khác production" **bằng không** ⇒ giữ nguyên, chỉ ghi một dòng vào ledger. **Nếu** nó làm thêm/khác ⇒ đó là phát hiện nặng hơn audit tưởng, dừng và báo trước khi sửa.

#### D5 · `label_for` — quyết sau khi đọc

**K:** đọc `labels.py:40-55`. Nếu chỉ là `LABELS.get(code)` thì đây là hàm một dòng có test riêng — **giữ**, ghi ledger. Không xoá code đang có test chỉ để giảm số đếm *(§4.4.3: rác có sẵn thì báo, không tự xoá)*.

**Commit:** `test(etl): the two live sources nobody was testing`

---

### Task 9 — Nghiệm thu và báo cáo

```bash
cd backend && uv run --env-file ../.env pytest tests -q              # AC2: ≥ 1029 passed, 2 skipped
cd backend && uv run pytest tests/docs -q                            # AC1: 7/7 xanh
cd backend && uvx ruff check . --select F --exclude .venv            # AC6: 0
git grep -n "\[DEBUG-" -- backend                                    # AC7: rỗng
npm test                                                             # 7/7
cd backend && uv run --env-file ../.env python -m etl fred --dry-run --keys us.cpi; echo "EXIT=$?"   # AC8
```
Rồi viết `ledger.md` §5 — bảng 47 mục, mỗi mục một kết cục.

**Commit:** `docs(ledger): close the drift cleanup — what changed, what deliberately did not`

---

## 6. Quyết định chốt trong plan (không mở lại khi thực thi)

### 6.1 Không xoá `flush_once` / `label_for`

Cả hai **có test, có docstring khai rõ vai trò**. Xoá `flush_once` kéo theo viết lại 30 điểm gọi trong 3 file test — rủi ro hồi quy lớn hơn giá trị thu được, và nó không phải rác lén mà là lớp tương thích được ghi nhận. CLAUDE.md §4.4.3: *"rác có sẵn thì báo, không tự xoá"*. Ghi thành nợ có tên trong ledger, chủ dự án quyết sau.

### 6.2 Không xoá `POSTGRES_PORT` / `REDIS_PORT` / `LOG_LEVEL` khỏi `.env.example`

Ba biến này chưa ai đọc, nhưng `.env.example` là **hồ sơ cấu hình cho người dựng máy**, không phải danh sách biến code đọc. Lát 12 (chạy trong container) sẽ động đúng vùng này — xoá bây giờ để lát 12 thêm lại là hai lần đụng. Chỉ thêm chú thích.

### 6.3 `00-conventions.md`: đổi tiêu đề, không đánh số lại bẫy

Đánh số lại `Bẫy 4b → 14` làm chết mọi tham chiếu chéo `Bẫy 5`…`Bẫy 13` rải trong repo và trong CLAUDE.md §3.3. Đổi tiêu đề `Mười ba` → `Mười bốn` là sửa một chữ.

### 6.4 Bộ kiểm **không** assert số test

Số test tăng mỗi lát ⇒ assert nó là tiêu chí *thời điểm*, tự vi phạm §4.4.4. Thay vào đó Task 3 giảm số chủ của con số này từ 3 xuống 1.

## 7. Rủi ro

| Rủi ro | Giảm bằng |
|---|---|
| Sửa nhầm vào **số đo** của `10-sources/` (§1.2 cấm) | Lát này chỉ chạm `10-sources/` ở 3 chỗ: mục lục host Frankfurter (A12), bảng ngoài-phạm-vi (C6), tiêu đề đếm bẫy (C7). **Không chạm bảng số đo nào.** Nhịp K của Task 5/6 in ra đúng dòng sẽ sửa để đối chiếu |
| Sửa nội dung vùng lịch sử `90-records/` | Task 6 chỉ sửa **href**; nhãn hiển thị giữ nguyên. Nhịp X `git diff` phải cho thấy chỉ phần trong `(...)` đổi |
| `ruff --fix` sửa quá tay | Chỉ `--select F`; xem `git diff` từng file trước khi commit |
| Xoá nhầm nhánh đang làm việc | `git branch --merged main` **không** liệt nhánh hiện tại; vẫn kiểm `git branch --show-current` trước |
| Bộ kiểm mới làm CI chậm | Toàn bộ là đọc file, không DB/mạng — đo ở Task 1, kỳ vọng < 2 s |
