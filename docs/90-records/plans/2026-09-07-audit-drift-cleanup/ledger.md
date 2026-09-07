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

---

## Task 5 — `20-design/` và `architecture.md` ✅

**Nhịp K** — đọc cả hai vế của 10 mục, tất cả còn đúng:

```
A3  news-pipeline "20 sub" ×4 + "(5 sub)"     | code SUBS {'1':6,'2':6,'3':9,'x':1}
A4  architecture:140 "chưa vá"                | system_prompt.py:23 SCOPE_GUARD tồn tại
A5  architecture:144 "maintenance.md §5"      | maintenance.md §5 = "Lỗi của nguồn đã sửa"; §7 = "Lỗ hổng phạm vi"
A6  market-data-store:577 "code text PRIMARY KEY" | 0004:101-110 PRIMARY KEY (dictionary, code)
A7  market-data-store:615 5 view              | grep CREATE VIEW = 3 view KHÁC hẳn
A8  news-pipeline:256 "200–300 ký tự"         | news_classify.py:42 "3–5 câu ngắn"
A9  chatbot-semantic-layer:5 "chưa ai viết"   | dòng 3 nói "đã dựng 2026-09-07"
A10 test-strategy:9 pytest-asyncio + respx    | uv.lock grep = 0
A11 service-topology:123 "agent/skills/"      | backend/agent có 8 module + tools/ 10 file
A12 10-sources/README:49 api.frankfurter.app  | fx_fetch.py:11 api.frankfurter.dev/v1
```

**Nhịp S — thêm hai chỗ ngoài danh sách, phát sinh từ chính A4:** `docs/README.md:18` và `:32` quảng cáo `architecture.md` bằng cụm *"một lỗ hổng đã biết chưa vá"*. Sửa A4 mà bỏ hai dòng này là để tài liệu tự đá nhau ngay trong cùng lượt — đúng thứ §1.7 cấm. Đã sửa cả hai.

**Ba mục viết lại chứ không vá chữ**, vì vá chữ sẽ để lại một tài liệu vô nghĩa:

- **A4** — không chỉ đổi tiêu đề. Giữ nguyên phần mô tả lỗ hổng (nó giải thích *vì sao* phải vá ở tầng sản phẩm, còn giá trị cho skill 3, 4 sau này), thêm khối ✅ nói `SCOPE_GUARD` là **block đầu tiên** của `build_system_blocks()` nên tới trước mọi câu hỏi, kèm bằng chứng đối chiếu nguyên văn 587 ký tự.
- **A6** — không chỉ thêm cột. Câu *"Nạp từ Screener — 83 tiêu chí"* cũng sai từ lát 5: bảng nay nạp **hai** bộ (83 tiêu chí Screener + 729 mã BCTC), và **đó chính là lý do khoá chính phải có cột `dictionary`** — không tách thì mã trùng tên giữa hai bộ đè nhau im lặng. Viết cả lý do vào.
- **A7** — không xoá dòng 5 view. Ghi rõ **chưa bao giờ dựng và nay hết cần**, kèm lý do đọc được: function calling (§6.3 ngay dưới) thay đúng vai trò đó, 9 công cụ tự đặt nhãn người-đọc-được trong payload (`agent/labels.py`) nên đổi nhãn không phải chạy migration. Liệt 3 view thật đang có. Xoá trơn thì ba tháng nữa có người đề xuất lại đúng 5 view đó.

**A8 — một chỗ CỐ Ý không sửa:** `news-pipeline.md:128` vẫn còn cụm *"200–300 ký tự"*. Đó là §7.1 ghi lại **chính lần đổi luật** (*"đổi từ 2–3 câu, 200–300 ký tự ngày 2026-09-06"*) — bản ghi at-the-time, xoá là mất lý do. Chỉ sửa §9.3 (dòng 256) vốn đang **mô tả luật hiện hành sai**.

**Nhịp X:**

```
"20 sub"/"(5 sub)" còn 0    "Bộ view tối thiểu" còn 0     "chưa ai viết" còn 0
respx/pytest-asyncio còn 0  api.frankfurter.app còn 0     PRIMARY KEY (dictionary, code) ✓
"200–300 ký tự" còn 1  <- đúng, là ghi chú lịch sử §7.1
pytest tests/docs -q  ->  2 failed, 5 passed   (từ 3 failed, 4 passed)
    còn lại: dead_links + orphan  ← Task 6
```

**Commit:** `docs: the design layer said things the code stopped doing`

### 🔴 Sự cố trong Task 5 — tôi tự gây đúng lỗi D3 đang đi sửa

Script sửa hàng loạt của tôi dùng `pathlib.write_text(...)` **không truyền `newline="\n"`** ⇒ trên Windows ghi ra CRLF. Đúng bằng lỗi **D3** của `gen_industry_mapping.py` mà Task 7 sắp sửa.

Chuỗi việc:

1. Commit Task 5 đi qua bình thường — `git add` chuẩn hoá về LF nhờ `.gitattributes` `* text=auto eol=lf`, nên **nội dung trong repo đúng**. Nhưng working copy 5 file thành CRLF, và `git status` vẫn sạch nên **không có gì báo**.
2. Tôi viết script quét toàn repo đổi CRLF → LF. Nó báo **211 file** — phần lớn không phải do tôi, mà là **bản trên đĩa** của những file được checkout ra CRLF ở đâu đó trước phiên này. *(Lúc đó tôi kết luận nhầm là chúng "được lưu CRLF trong git" — xem đính chính cuối mục.)*
3. `git status` sau đó: **211 file `M`**. Đây là thay đổi nội dung **thật**, hoàn toàn **ngoài phạm vi** lát này (§4.4.3: *"không tiện tay cải thiện code lân cận"*).
4. 🔴 Script đó còn đọc-ghi **cả file nhị phân** (`.xlsx`) — nếu một file Excel chứa chuỗi byte `0D 0A` thì đã hỏng. May là `git status` không liệt file `.xlsx` nào.
5. `git checkout -- .` hoàn nguyên sạch. Kiểm lại: 5 sửa đổi Task 5 **còn nguyên** (5 phép grep đều ra 0), file nay là LF, `pytest tests/docs` vẫn 2 failed / 5 passed.

**Ba bài học ghi lại:**

- **Công cụ sửa hàng loạt phải khai `newline="\n"`** — chính xác là bản sửa mà D3 sắp làm cho generator. Từ đây dùng heredoc bash hoặc ghi có `newline="\n"`.
- **Đừng bao giờ đọc-ghi byte hàng loạt trên `git ls-files`** — danh sách đó có cả nhị phân. Lọc theo phần mở rộng, hoặc dùng `git add --renormalize` để git tự lo.
- **"211 file thay đổi" là tín hiệu dừng, không phải tín hiệu tiến.** Một lát dọn 47 mục mà chạm 211 file thì đã đi lạc. Việc chuẩn hoá CRLF toàn repo là một quyết định riêng, cần chủ dự án chốt — **không gộp vào đây**.

### 🔴 Đính chính chính mục này — đo lại 2026-09-07 sau khi chủ dự án hỏi "211 file CRLF là gì"

Câu *"211 file lưu CRLF trong git"* ở trên **SAI**, và tôi đã suýt để lại một việc treo không tồn tại. Đo lại bằng đúng công cụ:

```
git ls-files --eol | awk '{print $1,$2}' | sort | uniq -c
    738 i/lf w/lf          <- KHONG file nao luu CRLF, KHONG file nao tren dia con CRLF
     50 i/none w/none      <- nhi phan
      6 i/-text w/-text
git cat-file blob <blob cua mot trong 211 file> | dem byte 0x0d   ->  0
```

**Sự thật là gì.** Dựng lại đúng trình tự trên một file thật (`frontend/README.md`), mỗi bước một phép đo:

| Bước | Trạng thái | `git status` | `git diff` |
|---|---|---|---|
| Đĩa CRLF, blob LF | `i/lf w/crlf` | ` M` | — |
| `git add` | blob vẫn **0 byte CR** | *sạch* | — |
| Đĩa đổi về LF | `i/lf w/lf` | ` M` | **rỗng** |

Dòng cuối là chỗ tôi đọc nhầm: `git status` báo `M` nhưng `git diff` và `git diff HEAD` đều **rỗng** — **không có một dòng nội dung nào đổi**. Đó là sổ ghi `stat` của index lệch (git `add` lúc file còn CRLF nên nhớ kích thước bản CRLF), không phải khác nội dung. Tôi thấy "211 file M" rồi suy ra "211 file lưu CRLF trong git" — **suy từ một triệu chứng ra một nguyên nhân, không đo**, đúng họ lỗi §3.6 của repo.

**Hệ quả:** không còn việc gì để làm. `git add --renormalize .` mà tôi định đề xuất sẽ **không đổi một byte nào** vì không có gì để chuẩn hoá. Cả hai vế đều đã sạch: 0 file CRLF trong git, 0 file CRLF trên đĩa, `git status` rỗng.

**Phần vẫn đúng của mục này:** ba bài học về công cụ sửa hàng loạt (`newline="
"`, đừng đọc-ghi byte trên `git ls-files` vì có nhị phân, "211 file đổi" là tín hiệu dừng) — cả ba giữ nguyên.

---

## Task 6 — index và dead doc ✅ · **bộ kiểm chuyển XANH 7/7**

**Nhịp K** — cả 9 mục còn đúng: 3 file mồ côi vẫn ở đó · `measure-news-2026-09-05.txt` `find` ra 0 · 2 href sai độ sâu còn nguyên · bảng §2(b) chỉ có 1 dòng · `## 7. Mười ba bẫy` nhưng `grep -c "^### Bẫy"` = **14** · `terminology.md:3` còn "Giai đoạn 3".

**Nhịp S:**

| Mục | Làm gì |
|---|---|
| C1 | Dòng lát 11 ở `90-records/README.md` liệt **đủ 11 tên file**, theo khuôn dòng lát 10 liền trên |
| C2 | Bỏ `measure-news-2026-09-05.txt` khỏi danh sách file, thay bằng ghi chú *"chưa từng được commit"* |
| C3 | `brief.md:3` `../../../` → `../../../../` · `intraday spec.md:50` `../../` → `../../../` · `news-collect spec.md:5` gỡ link giữ nhãn |
| C4 | `docs/README.md` §30 — bỏ bảng chép lại, thay bằng câu dẫn sang `30-skills/README.md` |
| C5 | `90-records/README.md` — bỏ bảng chép lại, thay bằng câu dẫn sang `worksheets/README.md` |
| C6 | Thêm `DEXCHUS` vào bảng §2(b) *"đã có đường khác"* |
| C7 | `Mười ba bẫy` → `Mười bốn bẫy` |
| C8 | Bỏ *"cho Giai đoạn 3"* |
| C9 | 8 chỗ → `47 RSS + 8 nguồn crawl (6 lượt thường + 2 sitemap backfill)` |

**Ba chỗ cần cân nhắc, không máy móc:**

1. **C3 — vùng lịch sử, chỉ sửa href.** `git diff -U0` xác nhận **mỗi file đúng 1 dòng đổi và phần chữ hiển thị y nguyên**. Riêng `news-collect/spec.md:5` không có href nào để sửa (file **chưa từng tồn tại**) ⇒ gỡ link, giữ nhãn, thêm ghi chú — **theo đúng tiền lệ** `news/README.md:370` đã làm y hệt ngày 2026-09-07.
2. **C7 — đổi tiêu đề, KHÔNG đánh số lại.** Đổi `Bẫy 4b` → `Bẫy 14` sẽ giết mọi tham chiếu chéo `Bẫy 5`…`Bẫy 13` rải trong repo **và trong CLAUDE.md §3.3**. Sửa một chữ ở tiêu đề là đủ và an toàn.
3. **C9 — hai dòng ASCII phải giữ độ rộng cột.** `architecture.md:14` là khung `┌─┐`: `"6 crawler"` (9 ký tự) → `"8 crawl  "` (7 + 2 dấu cách) để `│` vẫn thẳng cột. `news-pipeline.md:38` tương tự: `"6 crawler ────┘"` → `"8 crawl ──────┘"`.

**Hai chỗ CỐ Ý không sửa:**

- `10-sources/README.md:201` vẫn còn *"6 crawler"* — nằm trong **changelog phiên bản 4.0 (2026-08-14)**, ghi lại việc bản 4.0 đã làm. Bản ghi at-the-time, sửa là viết lại quá khứ.
- `architecture.md:73` vẫn trỏ *"quy trình 6 vòng"* — `maintenance.md` §6 đã tự khai bộ vòng 6 mất và trỏ sang vòng 7, nên người đọc theo link **không** bị dẫn sai.

**Phát sinh ngoài danh sách:** `README.md:18` còn *"test 6 vòng"* — cùng họ với chỗ đã sửa ở dòng 5 trong Task 3. Sửa luôn, nếu không thì một file lại tự đá nhau.

### Một lần đỏ giữa chừng, đáng ghi

Lượt sửa C1 đầu tiên **không làm test xanh**: tôi viết tên file rút gọn (`round10-nhom-a`) trong khi phép kiểm so **tên file đầy đủ** (`round10-nhom-a-2026-09-07.md`). Phép kiểm đúng, bản sửa hớ — và nó bắt được. Viết lại đủ tên.

**Nhịp X:**

```
"6 crawler" còn:  README 0 · docs/README 0 · architecture 0 · news-pipeline 0
                  10-sources/README 1  <- changelog v4.0, cố ý giữ
"Mười bốn bẫy" ✓   "Giai đoạn 3" còn 0   DEXCHUS ✓   trùng chủ C4/C5 còn 0

pytest tests/docs -q  ->  7 passed in 0,41 s        ← AC1 ĐẠT
```

**Từ 6 đỏ / 1 xanh (Task 1) → 7 xanh.** Bộ kiểm nay là lưới thật, không phải trang trí.

**Commit:** `docs: three orphan files, one index entry pointing at nothing, three broken hrefs`

---

## Task 7 — code, config, vệ sinh ✅

**Nhịp K:** `gen_industry_mapping.py:627-628` ghi bằng `open(...).write(...)` không `newline=` và **không đóng handle** · `.gitattributes` chỉ ghim `market-field-selection.*` · `[DEBUG-VPS]` còn 2 dòng · `package.json` không có script `test` · 15 nhánh đã merge, 0 nhánh chưa merge.

**Nhịp S:**

| Mục | Làm gì |
|---|---|
| D3 | Hai lệnh ghi → `with open(..., newline='\n')`, khớp khuôn `gen_field_selection.py:928-930`; thêm 2 dòng `eol=lf` cho `industry-mapping.*` vào `.gitattributes` |
| D9 | `ruff check --select F --fix` → **9 import thừa** tự sửa; 2 biến còn lại sửa TAY (xem dưới) |
| D10 | `[DEBUG-VPS]` → `[probe-vps]` |
| D11 | `package.json` thêm `"test": "node --test scripts/stack.test.mjs"` |
| D12 | Xoá **15 nhánh local** đã merge |

### 🔴 Một trong hai biến "thừa" KHÔNG được xoá — ruff sẽ xoá sai

`tests/ingester/test_i13_spill_store.py:237` — `s = _store(tmp_path)`, ruff báo *"Remove assignment to unused variable `s`"*. **Nghe theo là hỏng test.** Đọc code trước khi sửa cho thấy: `_store()` gọi `try_acquire()` giành **file lock**, và lock đó sống theo **vòng đời object** (handle `msvcrt`/`fcntl` giữ trên `SpillStore`). Bỏ tên `s` ⇒ GC có thể đóng handle ⇒ tiến trình con **giành được** lock ⇒ `assert r.returncode == 0` vẫn xanh **vì lý do sai hoàn toàn**. Một test **xanh giả**, đúng họ lỗi §4.5 của repo.

Sửa đúng: **giữ tên**, và thêm `assert s.owned` — vừa hết cảnh báo, vừa canh chính tiền đề mà test dựa vào (trước đó tiền đề đó không được kiểm ở đâu cả). Kèm 2 dòng comment nói vì sao không được xoá, để lượt `ruff --fix` sau không xoá lại.

> Đây là lý do ruff xếp F841 vào nhóm **unsafe fix**. Chạy `--unsafe-fixes` cho cả bộ là đã hỏng test này rồi.

Biến còn lại (`test_e34:69` `a = _issuer(...)`) thì an toàn — chỉ cần **side effect** tạo dòng DB, assertion đối chiếu bằng chuỗi `"ZZA"`. Bỏ phép gán, giữ lời gọi, thêm comment nói vì sao dòng đó tồn tại.

### D3 — nghiệm thu bằng phép thử, không bằng đọc code

```
sinh lại cả 4 file trong scratchpad:
  industry-mapping.md/.json · market-field-selection.md/.json   -> đều LF
cmp byte-by-byte với bản trong repo                             -> KHỚP 100% cả 4
copy bản sinh lại đè vào repo rồi git status docs/20-design/    -> chỉ generator "M"
                                                                   (4 file sinh: KHÔNG diff)
```

Vế cuối mới là điều D3 nhắm tới: **chạy generator không còn làm bẩn working tree**.

### Không làm — có lý do

**Hai nhánh remote** `origin/feat/intraday-refresh` và `origin/feat/news-collect` vẫn còn. Xoá nhánh remote là **đẩy thay đổi ra ngoài** và khó lấy lại — không tự quyết. Lệnh khi chủ dự án đồng ý:

```bash
git push origin --delete feat/intraday-refresh feat/news-collect
```

**Nhịp X:**

```
ruff check . --select F --exclude .venv        -> All checks passed!
git grep "\[DEBUG-" backend                    -> 0            ← AC7 ĐẠT
npm test                                       -> 7/7 pass
pytest test_e34 + test_i13 + test_c99 -q       -> 33 passed, 1 skipped
git branch                                     -> chỉ còn main + nhánh đang làm
```

**Commit:** `chore: retire the leftovers the audit turned up`

---

## Task 8 — hai lỗ hổng test, và quyết `flush_once`/`label_for` ✅

**Nhịp K — suy giá trị kỳ vọng bằng tay, không chạy code rồi chép output (§4.5.3):**

```
phan_ure.json:  2 series, mỗi series 588 điểm thô
  idx0 'Giá phân Ure Phú Mỹ'  epoch 1787850000000 -> VN 2026-08-28  value 11700
  idx1 'Giá phân Ure Cà Mau'  epoch 1787850000000 -> VN 2026-08-28  value 12150
  điểm cũ nhất 2024-09-05: phumy 9850 · camau 10250
wichart.md §9 dòng 753-754:  scale = 1, đơn vị VND/kg  ⇒ giá trị kỳ vọng = số thô
2026-08-28 là THỨ SÁU (tính tay) ⇒ điểm chép lại không rơi vào luật bỏ cuối tuần

tn.json: 46 điểm, mới nhất neo 2026-06-01 (Q2) ⇒ chuẩn hoá về 2026-04-01, value 2.23
feed-nguoiquansat.xml: 40 <item>; bài đầu pubDate 'Sat, 05 Sep 2026 22:17:01 +0700'
```

**Nhịp S — ba test mới:**

| Mục | Test |
|---|---|
| D6 | `test_phan_ure_two_series_share_one_key_and_both_land_with_scale_one` — hai series sống chưa từng được test |
| D7 | `test_quarterly_percent_series_on_real_capture_anchors_to_quarter_start` |
| D8 | `_feed("nguoiquansat")` thêm vào `test_parse_rss_literals_per_source` |

### D7 — plan sai, sửa lại khi đọc code

Plan viết *"đổi test `tn` sang dùng `_series("tn")`"*. **Làm vậy là hỏng test.** Nhịp K cho thấy test `tn` đang có là một test **ÂM** (`pytest.raises(SeriesError)`, `reason == "shape"`) với đầu vào **bịa có chủ đích**: quý neo tháng 5, không phải tháng cuối quý. Nó **bắt buộc** phải bịa — bản thu thật toàn quý hợp lệ nên không thể dựng ca đó.

Lỗ hổng thật là **thiếu vế dương**: `tn.json` chưa từng được khẳng định. Nên **thêm** một test dương, **giữ nguyên** test âm.

### D6 — test đỏ ở lượt đầu, và **kỳ vọng của tôi mới là cái sai**

`assert len(phumy) == 588` → đỏ, thật ra 488. Không phải code sai: **588 là số điểm THÔ**, còn luật bỏ điểm cuối tuần chép lại cắt bớt 100 điểm. Tôi đã khẳng định một con số mà chính luật đang kiểm sẽ làm đổi.

Sửa thành phép kiểm **bất biến**, vẫn suy được từ fixture + luật:

```python
raw = len(_series("phan_ure")[0]["data"])
assert raw == 588            # đếm tay trong fixture
assert 0 < len(phumy) < raw  # luật bỏ điểm cuối tuần PHẢI cắt bớt
```

### Chứng minh test có tác dụng — đột biến, không chỉ "nó xanh"

```
đột biến 1  wichart_normalize: Asia/Ho_Chi_Minh -> UTC
            => phan_ure ĐỎ · quarterly_percent ĐỎ            (hoàn nguyên)
đột biến 2  registry: hoán vị urea_phumy <-> urea_camau
            => phan_ure ĐỎ                                    (hoàn nguyên)
```

D8 **không** đột biến riêng — nó đi đúng đường `parse_rss` mà 6 nguồn khác đã canh; giá trị của nó là **phủ thêm một nguồn sống**, không phải canh thêm một nhánh code. Ghi rõ để không ai đọc nhầm là đã chứng minh.

### D4 · D5 — đọc code rồi mới quyết, và **cả hai đều GIỮ**

**`ChWriter.flush_once`** — thân hàm đúng là `manage_once()` rồi `write_once(budget_s=RETRY_BUDGET_S + 30)`. Tức nó **không** đi đường khác production về mặt *thứ tự*, chỉ khác **ngân sách thời gian**: test muốn "xả cho hết", production muốn "mỗi nhịp một ít". Khác biệt này **có chủ đích và đã ghi trong docstring**. Audit nói *"30 test đi đường khác production"* — nói vậy là **nặng hơn sự thật**; câu đúng là *"khác đúng một tham số ngân sách, có lý do"*. **Giữ.**

**`label_for`** — đúng một dòng `LABELS.get(code)`. Khác `LABELS[code]` của 3 tool ở chỗ trả `None` thay vì `KeyError`. 5 assertion của nó đang **ghi lại ngữ nghĩa của `LABELS`** (ví dụ `label_for("prf") is None` — mã bị loại có chủ đích). Xoá là mất 5 assertion đó mà không được gì. **Giữ** — §4.4.3: *"rác có sẵn thì báo, không tự xoá"*.

**Nhịp X:** `pytest test_e38 + test_e52 -q` → **31 passed**; hai đột biến đều bắt được; registry và normalize đã hoàn nguyên (`grep` xác nhận).

**Commit:** `test(etl): the two live sources nobody was testing`

---

## Task 9 — nghiệm thu ✅

### Một sự cố phải giải trước khi nghiệm thu được

Lượt chạy cả bộ đầu tiên **đỏ 1 test** — chính test `phan_ure` vừa viết — trong khi chạy riêng file đó thì **xanh**. Trông y hệt nhiễm chéo giữa các test. Không phải.

```
grep phan_ure backend/etl/wichart_registry.py   -> ("phan_ure", 0): ("urea_phumy", …)   ĐÚNG
git diff backend/etl/wichart_registry.py        -> rỗng, khớp HEAD
build() ngay lúc đó                             -> idx0 = urea_camau   ← HOÁN VỊ
```

File đúng mà `build()` sai ⇒ **`__pycache__` cũ**. `.pyc` sinh lúc chạy **đột biến 2** (hoán vị registry) và source khôi phục **trong cùng một giây** (`20:03` cả hai) — phép kiểm hết hạn theo mtime của Python không nhận ra source đã đổi. Xoá `__pycache__` là đúng ngay lập tức.

> **Bài học:** sau mỗi lần đột biến file nguồn, phải **xoá `__pycache__`**, không chỉ khôi phục file. Đột biến + khôi phục trong cùng một giây là ca mtime không phân giải được. Và nó suýt bị chẩn đoán nhầm thành "test nhiễm chéo" — đúng thứ CLAUDE.md §4.6 dặn: có vòng phản hồi đỏ rồi mới đặt giả thuyết.

### Tám cổng nghiệm thu

| AC | Lệnh | Kết quả |
|---|---|---|
| **AC1** | `pytest tests/docs -q` | **7 passed** *(mở màn 6 failed / 1 passed)* |
| **AC2** | `pytest tests -q` | **1.038 passed, 2 skipped**, 88,44 s *(nền 1.029 + 7 docs + 3 lỗ hổng − 1 gộp)* |
| **AC3** | bảng §5 dưới | 47/47 mục có kết cục ghi tên |
| **AC4** | `test_no_dead_internal_links` | xanh |
| **AC5** | `test_no_orphan_plan_docs` | xanh |
| **AC6** | `ruff check . --select F` | **All checks passed!** |
| **AC7** | `git grep "\[DEBUG-" backend` | **0** — lần đầu phép kiểm §4.6 thật sự về 0 |
| **AC8** | `python -m etl fred --dry-run --keys CPIAUCSL` | `ok: 1 · points: 954 · exit 0` — chứng minh `FRED_API` trong `.env.example` nối đúng đường thật |

Cộng `npm test` → **7/7** *(bộ node lần đầu có script chạy)*.

---

## §5 — Kết cục của 47 phát hiện (AC3)

**42 đã sửa · 3 cố ý giữ nguyên · 1 làm khác cách · 1 làm một nửa.**

| Nhóm | Mục | Kết cục |
|---|---|---|
| A · tài liệu nói sai code | A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 | ✅ **đã sửa** (12) |
| | **A13** | ✅ sửa **khác plan** — annotate thay vì đổi số, vì dòng đó là bản ghi lúc đóng lát 7 và `DEXCHUS` bị bỏ ở lát **7b** ⇒ đổi thành 14 là viết lại quá khứ cho sai đi |
| B · lệch số/trạng thái | B1 … B13 | ✅ **đã sửa** (13). Riêng B1 sửa **triệt để**: bỏ hẳn số test khỏi `README.md`, chỉ còn một chủ ở `database/README.md` |
| C · dead doc/index | C1 … C9 | ✅ **đã sửa** (9) |
| D · code/config | D1 D3 D6 D7 D8 D9 D10 D11 | ✅ **đã sửa** (8) |
| | **D2** | ⚪ **cố ý giữ** — `POSTGRES_PORT`/`REDIS_PORT`/`LOG_LEVEL` chưa ai đọc, nhưng `.env.example` là hồ sơ cấu hình cho người dựng máy, không phải danh sách biến code đọc; lát 12 sẽ động đúng vùng này. Chỉ thêm chú thích *(plan §6.2)* |
| | **D4** | ⚪ **cố ý giữ** — `flush_once` = `manage_once()` + `write_once(budget rộng hơn)`, khác production đúng **một tham số ngân sách**, có docstring khai. Audit nói *"đi đường khác production"* là nặng hơn sự thật |
| | **D5** | ⚪ **cố ý giữ** — `label_for` là `LABELS.get()` một dòng; 5 assertion của nó ghi lại ngữ nghĩa `LABELS`. Xoá là mất 5 assertion mà không được gì *(§4.4.3)* |
| | **D12** | 🟡 **một nửa** — xoá **15 nhánh local**; **2 nhánh remote để lại**: xoá nhánh remote là đẩy ra ngoài và khó lấy lại, cần chủ dự án đồng ý |

### Ba việc mới phát sinh, để lại cho chủ dự án

| # | Việc | Vì sao không gộp vào đây |
|---|---|---|
| 1 | ~~211 file lưu CRLF trong git~~ — **rút lại 2026-09-07: chẩn đoán sai, không có việc gì để làm.** `git ls-files --eol` cho 738/738 file `i/lf w/lf`; `git diff` ở bước gây hiểu nhầm là **rỗng**. Chi tiết ở đính chính mục Task 5 | — |
| 2 | **2 nhánh remote** `origin/feat/intraday-refresh` · `origin/feat/news-collect` | `git push origin --delete …` — hành động ra ngoài |
| 3 | **`ruff` chưa vào `pyproject.toml`** | Lát này chạy `uvx ruff` tạm. Thêm vào `dependency-groups.dev` + một bước lint là **quyết định quy trình**, thuộc lát 12/13 |

### Điều kiện đảo ngược

Nếu bộ kiểm `tests/docs` bắt đầu đỏ vì **lý do cách diễn đạt** (ai đó sửa câu chữ hợp lệ mà regex không khớp) nhiều hơn vì **lệch thật**, thì nó đang tính phí nhiều hơn giá trị — lúc đó nới regex hoặc bỏ phép kiểm đó, đừng sửa tài liệu cho vừa regex.
