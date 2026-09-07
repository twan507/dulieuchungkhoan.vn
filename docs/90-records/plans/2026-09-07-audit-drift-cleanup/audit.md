# Audit độc lập 2026-09-07 — hồ sơ 47 phát hiện

**Ngày:** 2026-09-07 · **Người chạy:** trợ lý, vai reviewer độc lập, theo yêu cầu chủ dự án *("đọc tài liệu dự án, tìm dead code / dead doc / sai lệch, tự kiểm từng bước")*

**Luật của hồ sơ này:** mỗi phát hiện phải kèm **lệnh đã chạy thật** và kết quả. Không suy đoán. Mục nào chưa kiểm được thì ghi *"chưa kiểm"*.

---

## 1. Cách kiểm

| Trục | Cách |
|---|---|
| Test | `uv run --env-file ../.env pytest tests -q` — **1029 passed, 2 skipped, exit 0, 86,25 s** |
| Link markdown | script Python, **lọc bỏ dòng trong khối ` ``` `** — 1.481 link nội bộ |
| File sinh tự động | sinh lại cả 4 trong scratchpad rồi `diff` với bản commit |
| Registry | `import etl.<src>_registry; build()` đếm series thật |
| Biến môi trường | quét `getenv`/`environ`/`env.get`/`process.env` toàn `backend|scripts|deploy|database`, đối chiếu hai chiều với `.env.example` |
| Trạng thái máy | `Get-ScheduledTask -TaskName "dlck-*"` |
| Lint | `uvx ruff check . --select F --exclude .venv` (repo chưa có `ruff` — tải tạm, không cài vào venv) |
| Bảng DB | trích `CREATE TABLE` từ 20 migration Postgres + 2 migration ClickHouse = **44 bảng**, rồi quét ngược tài liệu sống |

**Ngoài phạm vi, ghi rõ để người sau không tưởng đã kiểm:** không gọi API ngoài nào ⇒ **mọi con số đo của `10-sources/` chỉ được kiểm nhất quán nội bộ, không kiểm đúng** (§1.2 cấm khẳng định nếu chưa đo lại).

---

## 2. Ba đính chính của chính đợt audit

Ghi lại vì đây là bài học về chính phương pháp — cùng họ với CLAUDE.md §3.2.

| # | Bản nháp đầu nói | Sự thật sau khi kiểm kỹ | Bài học |
|---|---|---|---|
| 1 | *"19–20 link nội bộ chết"* | **3.** Bộ dò không lọc khối ` ``` `; 17 "link chết" ở `monorepo-restructure/plan.md` nằm trong fence hoặc trong backtick — markdown không render chúng thành link | Công cụ đo cũng phải bị nghi ngờ như dữ liệu |
| 2 | *"6 crawler là drift"* | **Không phải lỗi.** `chi_backfill=True` ở đúng 2 mục ⇒ 8 − 2 = 6 nguồn lượt thường, khớp `news/README.md:7` | Đọc chủ sở hữu trước khi kết luận bản sao sai |
| 3 | *"`SCOPE_GUARD` khớp nguyên văn 587 ký tự"* | Đúng, **nhưng chỉ sau khi bỏ tiền tố blockquote `> `** | Nói "khớp nguyên văn" thì phải nói cả phép chuẩn hoá |

---

## 3. Nhóm A — tài liệu sống nói sai so với code (13)

| ID | Vị trí tài liệu | Nói | Sự thật | Lệnh xác thực |
|---|---|---|---|---|
| A1 | `backend/README.md:102` | guard screener ≥ **50 %** | `MIN_PRICED_RATIO = 0.2` | `grep -n MIN_PRICED_RATIO backend/etl/screener_guard.py` → dòng 11, kèm comment *"Hạ 0.5 → 0.2 sau lượt chạy thật 2026-09-03 13:38"* |
| A2 | `backend/README.md:314` | FRED/ECB/LBMA *"nhận cờ `--intraday` rồi bỏ qua"* | argparse không có cờ → `exit 2` | `uv run python -m etl fred --intraday` → `unrecognized arguments`, `EXIT CODE = 2`; `__main__.py:150-152` chỉ thêm cờ cho `yahoo`/`binance` |
| A3 | `news-pipeline.md:5,21,55,418` + heading `:70` | *"20 sub"*, *"Nhóm 2 (5 sub)"* | **21 sub** (6+6+9), nhóm 2 có **6** | `news_classify.py:29-30` `SUBS`; migration `0019_sub_2f.py`; bảng dưới heading 70 đã có `2f` |
| A4 | `architecture.md:140` §4 | *"lỗ hổng gác cổng phạm vi — **chưa vá**"* | Đã vá lát 10 | `grep -n SCOPE_GUARD backend/agent/system_prompt.py` → dòng 23; là block đầu của `build_system_blocks` |
| A5 | `architecture.md:144` | đoạn dán ở *"`maintenance.md` §5"* | ở **§7** | `grep -n "^## " docs/30-skills/maintenance.md`; §5 = "Lỗi của nguồn đã sửa" |
| A6 | `market-data-store.md:577-584` | `metric_dictionary (code text PRIMARY KEY)` | thêm cột `dictionary`, `PRIMARY KEY (dictionary, code)` | `0004_market_data.py:101-110`. §6 **không** nằm dưới banner lịch sử — 3 banner đầu file chỉ phủ §3.2/§5/§5.3 |
| A7 | `market-data-store.md:615` | *"Bộ view tối thiểu"* 5 view | **0/5 tồn tại** | `grep -rn "CREATE VIEW" database/` = 3 view khác: `market.price_factor`, `macro.observation_spliced`, `market.v_issuer_industry`. 9 công cụ đọc thẳng bảng gốc |
| A8 | `news-pipeline.md:256` | `summary_ai` *"200–300 ký tự"* | *"3–5 câu ngắn"* | §7.1 cùng file (dòng 128) đã đổi 2026-09-06; `news_classify.py:42` dùng bản mới |
| A9 | `chatbot-semantic-layer.md:7` | *"Phần ở giữa thì chưa ai viết"* | đã dựng | dòng 3 cùng file: *"đã dựng và kiểm chứng 2026-09-07"* |
| A10 | `test-strategy.md:8` | *"pytest + **pytest-asyncio** · `httpx.MockTransport`/**`respx`**"* | cả hai **không tồn tại** | `pyproject.toml` dev = `psutil`, `pytest`; `git grep respx` = 0; `git grep pytest_asyncio` = 0; `grep respx backend/uv.lock` = 0. Test async chạy `asyncio.run(...)`; mock chỉ `httpx.MockTransport` (4 file) |
| A11 | `service-topology.md:117-123` §6 | cây `backend/` chỉ có `└── agent/skills/` | `backend/agent/` có 8 module + `tools/` 10 file + `skills/` | `ls backend/agent backend/agent/tools`. §6 đã cập nhật cho `core/llm/` (lát 9a) nhưng bỏ sót `agent/` (lát 10) |
| A12 | `10-sources/README.md:49` | `REST — Frankfurter (api.frankfurter.app)` | `api.frankfurter.dev/v1` | `fx_fetch.py:11`; `global/fx.md:13` đo 2026-09-05, host cũ trả `301`. Dòng 21 của chính file này đã biết |
| A13 | `roadmap.md:124` | lát 7 = *"15 + 6 + 2 + 37 + 11 series"* | fred **14**, fx **7** | `fred.build()`=14 · `fx.build()`=7 · `lbma`=2 · `binance`=11. FRED bỏ `DEXCHUS` ở lát 7b (`fred.md:188`). Hai cách cùng cộng ra 71 nên lỗi bị che |

## 4. Nhóm B — số / trạng thái lệch (13)

| ID | Vị trí | Nói | Đúng | Lệnh |
|---|---|---|---|---|
| B1 | `README.md:5` `596` · `:69` `640` · `:92` `456 passed` | ba giá trị trong một file | **1029 passed, 2 skipped** | `pytest tests -q`, exit 0, 86,25 s |
| B2 | `README.md:20` · `:70` | Postgres **17 migration** | **20** | `ls database/migrations/versions/*.py \| wc -l` |
| B3 | `README.md:16` | *"pipeline tin chưa"* | đã cài lát 8 · 8b · 9a | `backend/etl/news_*.py`, `news_classify.py`, migration `0018`–`0020` |
| B4 | `README.md:17` | tầng ngữ nghĩa *"🟡 đề xuất, chưa duyệt"* | xong lát 10–11, merge `main` | `ls backend/agent`; `roadmap.md:21` |
| B5 | `README.md:5` | *"lát 1–6 xong… tiếp theo lát 6 giám sát hợp đồng"* | lát 1–11 xong; tiếp **lát 12 container**; giám sát nay **lát 14** | `roadmap.md:167-181, 207` |
| B6 | `README.md:67` | danh sách `etl` 7 job | thiếu **8**: `wichart fred fx lbma yahoo binance news classify` | `__main__.py:161-162` liệt đủ 15 |
| B7 | `README.md:22` | 11 task *"đều `Disabled`"* | **10 Disabled + `dlck-price-backfill` Ready** | `Get-ScheduledTask -TaskName "dlck-*"` (2026-09-07) |
| B8 | `roadmap.md:29` | *"18 migration"* | **20** | cùng file dòng 581 ghi `head 0020` |
| B9 | `roadmap.md:19` | *"chưa viết dòng code nào"* | đã cài | như B3 |
| B10 | `roadmap.md:30` | chuỗi trạng thái dừng ở lát 9a | còn 9b · 10 · 11 | cùng file dòng 149–166 |
| B11 | `roadmap.md:586` | *"11 task vẫn `Disabled`"* | 10/11 | như B7. Dòng 581, 606 và 8 chỗ *"10/11"* khác đều đúng |
| B12 | `database/README.md:18` | *"20 migration"* rồi *"14 file, không 1-1 với **18 migration**"*; *"**64 test**"* | 20 · **15 file** · **65 test** | `pytest tests/schema --collect-only -q` = 65; `ls tests/schema/test_s*.py` = 15. Câu ánh xạ dừng ở `test_s15`, thiếu `test_s16←0019`; `0020` không có test schema |
| B13 | `database/README.md:86` | *"877 test"* | 1029 | dòng 92 cùng file đã ghi 1.029 |

## 5. Nhóm C — dead doc · index · từ vựng (9)

| ID | Vị trí | Vấn đề | Lệnh |
|---|---|---|---|
| C1 | `plans/2026-09-07-semantic-layer-closeout/` | **3 file mồ côi**: `reminder-ab-2026-09-07.md`, `reminder-ab-transcript-2026-09-07.md`, `round10-nhom-a-2026-09-07.md` | `git grep` toàn `docs/` = 0 hit cả ba. `ledger.md:96` chỉ nhắc khái niệm. Dòng lát 11 ở `90-records/README.md` không liệt file nào — dòng lát 10 liền trên liệt đủ 17 |
| C2 | `90-records/README.md:40` | liệt `measure-news-2026-09-05.txt` — chưa từng commit | `find docs -name "measure-news-2026-09-05.txt"` = rỗng; `news/README.md:370` đã tự đính chính |
| C3 | 3 link chết | `intraday-refresh/brief.md:3` thiếu 1 cấp · `intraday-refresh/spec.md:50` thiếu 1 cấp (dòng 3 cùng file dùng đúng) · `news-collect/spec.md:5` → file của C2 | bộ dò có lọc fence, 1.481 link |
| C4 | `docs/README.md:63-67` | chép lại bảng của `30-skills/README.md:5-9` | chính `docs/README.md:35, 55` từ chối chép `decisions/` và `20-design/` với lý do *"hai bản sẽ trôi lệch"* |
| C5 | `90-records/README.md:53-54` | chép lại bảng của `worksheets/README.md` dù dòng 48 đã có câu dẫn | |
| C6 | `10-sources/README.md` §2(b) | `DEXCHUS` loại *"đã có đường khác"* nhưng không vào bảng | `fred.md:188` ghi lý do; bảng §2(b) chỉ có SignalR — §1.4 |
| C7 | `00-conventions.md:169` | tiêu đề *"Mười ba bẫy"* | `grep -c "^### Bẫy"` = **14** (có `Bẫy 4b`) |
| C8 | `terminology.md:3` | *"bảng tra bắt buộc cho **Giai đoạn 3**"* — từ vựng thời dự án skill | `git grep "Giai đoạn 3"` ngoài corpus = chỉ chỗ này |
| C9 | 8 tài liệu | *"47 RSS + 6 crawler"* thiếu vế *"+2 sitemap backfill"* ⇒ đọc ra tổng 6 | chủ sở hữu `news/README.md:7` ghi **8**; `feeds.json.crawl_html` = 8, `chi_backfill=True` ở 2 |

## 6. Nhóm D — code · config · vệ sinh (12)

| ID | Vị trí | Vấn đề | Lệnh |
|---|---|---|---|
| D1 | `.env.example` | thiếu **`FRED_API`**, **`AGENT_DATABASE_URL`**; `LLM_TIMEOUT_S` không khai | `fred_fetch.py:40` `raise RuntimeError("thiếu FRED_API")`; `agent/db.py:45` `_engine("AGENT_DATABASE_URL")`. Hai biến cùng loại `ETL_DATABASE_URL`/`CLICKHOUSE_INGESTER_URL` **có** dòng mẫu |
| D2 | `.env.example` | 3 biến không ai đọc: `POSTGRES_PORT`, `REDIS_PORT`, `LOG_LEVEL` | quét env hai chiều = 0 hit |
| D3 | `gen_industry_mapping.py:627-628` | ghi file không `newline="\n"`, không đóng handle — khác `gen_field_selection.py:928-930` | sinh trên Windows ra CRLF ⇒ diff toàn file. `.gitattributes` chỉ ghim `market-field-selection.*`; comment trong chính file đó mô tả đúng bẫy này. ✅ nội dung sinh lại khớp 100 % cả 4 file |
| D4 | `chwriter.py:593` | `flush_once` — 30 lời gọi, toàn bộ trong test | production `main.py:419-420, 620-631` gọi `manage_once()`+`write_once()` rời |
| D5 | `labels.py:46` | `label_for` — chỉ `test_a02_format.py` gọi | 3 tool production index thẳng `LABELS[code]` |
| D6 | `test_e38_wichart_normalize.py` | **`phan_ure` không có test** dù 2 series sống | `wichart_registry.py:156-157` `urea_phumy` + `urea_camau`; 10 lệnh `_series(...)` không có `phan_ure`. Fixture thật 26 KB không ai dùng |
| D7 | `fixtures/wichart/tn.json` | mồ côi — key `tn` có test nhưng bằng literal gõ tay | `test_e38:97` |
| D8 | `test_e52_news_parse.py` | phủ 6 nguồn RSS, thiếu **nguoiquansat** dù nguồn này có **4 feed sống** | `feeds.json`: `/rss/vi-mo` `/the-gioi` `/chung-khoan` `/doanh-nghiep`; fixture đã bắt sẵn |
| D9 | 10 file test | **11 import/biến thừa**, 9 tự sửa được. **0 lỗi trong code sản phẩm** | `uvx ruff check . --select F` → `Found 11 errors`. Repo chưa có bước lint nào |
| D10 | `test_c99_dedup_probe.py:125-126` | `[DEBUG-VPS]` mượn tiền tố mà §4.6 dành cho log tạm ⇒ phép kiểm *"grep ra 0"* vĩnh viễn không về 0 | nội dung hợp lệ (diag của probe chạy tay) |
| D11 | `scripts/stack.test.mjs` | 7 test chạy được nhưng không `npm test`, không tài liệu sống nào nhắc | `node --test` = 7/7; `package.json` không có script `test` |
| D12 | git | 15 nhánh local đã merge + 2 nhánh remote cũ | `git branch --merged main` = 15; `--no-merged` = rỗng; `main == origin/main` |

---

## 7. Đã kiểm — KHÔNG hỏng

Ghi lại để người sau không kiểm lại vô ích, và để thấy phần lớn repo đang khoẻ.

- **Test:** 1029 passed / 2 skipped / exit 0 / 86,25 s.
- **`SCOPE_GUARD`:** 587 = 587 ký tự, `EQUAL True` sau khi bỏ `> ` (`maintenance.md:116-120`).
- **9 công cụ:** chữ ký khớp `chatbot-semantic-layer.md:51-61` từng chữ; `L2_TOPICS` = 9 khớp *"Literal đóng 9 giá trị"*.
- **Toàn bộ trần §2c khớp code:** `TRAN_PHIEN=2000` · `TRAN_KY=20` · `TRAN_MA/CHI_TIEU=25/15` · `TRAN_MA_VAO=100` · `cap_limit(30,200)`×2 · `(15,100)` · `(120,2000)` · `TRAN_DANH_MUC=250` · `MAX_TOKENS=32000` · `MAX_ITERATIONS=16` · `TRAN_GIAY_MOT_LUOT=300` · `QUOTA_TIMEOUT_S=15` · `CHAT_TIMEOUT_S=600`.
- **MiniMax:** `DEFAULT_BASE_URL` · `DEFAULT_MODEL` · `LLM_API` · `thinking adaptive` · `tool_choice` · `GET /v1/token_plan/remains` + `Bearer` — khớp `minimax.md` từng dòng.
- **Hằng số vận hành:** `DELIST_RATIO=0.01` · `DIRECTORY_ABSENT_DAYS=3` · snapshot `QUOTA{24,70,70,70}`=234 · `MAX_TRIGGER=300`/`CADENCE_DAYS=90`/`QUOTA=20` · `MAX_CONSECUTIVE_FAILURES=10`/`SOURCE_DOWN_PAUSE_S=600`/`MAX_PAUSES=3` · `RETRY_BUDGET_S=60`/`N_CAP_ROWS=100_000`/`SPILL_CAP_BYTES=10 GiB`/`DRAIN 75|600` · `SESSION_END 15:05|15:10` · ClickHouse **TTL 3 MONTH ở đúng 5 bảng thô**, `bar_1m`/`index_bar_1m` không TTL.
- **44 bảng** từ migration: **không tài liệu sống nào nhắc bảng không tồn tại**. 13 "nghi vấn" đều là tên job `ops.etl_run` hoặc tên file — ví dụ `market.scores` là domain ở `screener_store.py:79`.
- **4 file sinh tự động khớp 100 %** khi sinh lại ⇒ không ai sửa tay.
- **0/117 module Python mồ côi** · **0 TODO/FIXME/HACK** trong code sản phẩm · **0 lỗi ruff** trong code sản phẩm · quy ước tiền tố `ZZ` dùng thật ở 25 file test.
- `backend/README.md` ghi **đúng** *"chưa đăng ký task"* ở 6 chỗ (220 · 256 · 295 · 318 · 352 · 375); cả 11 task trên máy đúng `LogonType=Interactive`.
- `decisions/README.md` khớp 7 ADR, kế tiếp 0008 · `industry-tree` 3+4+5+4+4+4 = 24 · `industry-mapping.json` layer1 56 / layer2 161 khớp migration `0013` (55 = 56 − `8980`) · 3.046 = 774 + 2.272 · corpus 96 file · 47 feed RSS · `reference-repos.md` khớp 5 skill đang cài.
- Working tree sạch, `main == origin/main`, không có `.superpowers/` trong repo.

## 8. Kết luận một câu

**Code khoẻ; tài liệu là chỗ bị trôi, và trôi vì một sự thật có nhiều chủ mà không có phép kiểm nào thi hành §1.7.** Kế hoạch sửa: [`plan.md`](plan.md).
