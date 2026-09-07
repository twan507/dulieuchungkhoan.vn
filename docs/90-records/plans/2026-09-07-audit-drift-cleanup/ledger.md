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
