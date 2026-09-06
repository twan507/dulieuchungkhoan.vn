# Spec — lát 9a: lưới AI phân loại tin + `summary_ai` + gắn mã tầng 3 + gắn ngành, trên MiniMax M3

**Ngày:** 2026-09-06 chiều · **Nhánh:** `feat/news-classify-llm` · **Trạng thái:** chủ dự án chốt hướng trong chat 2026-09-06 chiều ("như bạn đề xuất đi… thiết kế xong test khoảng 100 bài gần nhất mỗi loại thôi đừng full 7000 bài, chủ yếu đo kết quả token và thời gian… chỉnh sửa spec, check cẩn thận rồi viết plan, sau đó thực thi luôn") — spec này là bản để rà, các điểm tự chốt ghi §9.
**Tiền đề:** [roadmap — Điểm vào cho lát 9](../../../00-overview/roadmap.md) · [brainstorm module LLM](../../surveys/2026-09-06-llm-module-minimax/brainstorm.md) (phương án A đã chọn theo §4.8) · [minimax.md](../../../10-sources/llm/minimax.md) (tầng reference, mọi số kèm ngày đo) · [news-pipeline §3, §7, §8](../../../20-design/news-pipeline.md) · [industry-tree.md](../../../20-design/industry-tree.md) · [spec lát 8](../2026-09-05-news-collect/spec.md) (§3.1 tầng 1–2, §4.6) · migration [`0007_news.py`](../../../../database/migrations/versions/0007_news.py).

Tiêu chí xuyên suốt: **lát này dựng công cụ và đo, không bật lưới chạy tự động.** Mọi lời gọi model đều có trần (`--limit`/`--per-group`), mọi lời gọi đều ghi sổ (`ops.llm_call`), và không sửa thiết kế taxonomy/quy tắc đã duyệt.

---

## 1. Vì sao lát này, và lát này là gì

Kho `news.*` sau lát 8/8b có 7.998 bài *(đếm 2026-09-06 15:00)* mà **mọi trường AI đều NULL**; roadmap lát 9 = "chốt ngân sách token → bật lưới phân loại 20 sub + gắn mã". Khảo sát 2026-09-06 đã đo xong hình dạng đầu ra (0 lỗi schema / 232 lời gọi), tokenizer (1,62 ký tự/token), cache, quota — chưa có dòng code nào gọi model.

Chủ dự án bổ sung 2026-09-06 chiều một yêu cầu thiết kế còn thiếu: ngoài mã cổ phiếu phải **gắn ngành** (24 ngành level 2 của [industry-tree.md](../../../20-design/industry-tree.md)); ngành áp cho **cả ba nhóm** (tin vĩ mô trong nước và quốc tế cũng thuộc ngành: giá điện, thuế phân bón, thuế quan lên dệt may/thuỷ sản), còn mã cổ phiếu chỉ ở nhóm 3.

| Thành phần | Nội dung |
|---|---|
| `backend/core/llm/` | module gọi model dùng chung (lát 9 lô, lát 10 chatbot): `LLMSettings` · `LLMClient.structured()` · `Usage` · `LLMError` · `token_plan_remains()` — SDK `anthropic` 1.4.0 trỏ `https://api.minimax.io/anthropic` |
| migration `0018` | `news.article_industry` (bài ↔ ngành, hai đường `ticker`/`ai`) · `ops.llm_call` (sổ mỗi lời gọi model: token, độ trễ, trạng thái) |
| `backend/etl/news_classify.py` + `etl classify` | job `news.classify`: chọn bài chưa phân loại (có trần), gọi model, ghi `group_no/sub/confidence/classified_from/content_chars/group_overridden/labels`, `summary_ai`, mã tầng 3 (`via='ai'`, lọc `market.security`), mã tầng 2 bù cho bài backfill, ngành `ai` + ngành suy từ mã `ticker`; guard quota; `--dry-run` để đo không ghi |
| Nghiệm thu = đo | ≈ 100 bài gần nhất **mỗi nhóm gợi ý** (1 · 2 · 3 · không nhóm) ⇒ ≈ 400 bài với thinking `adaptive`; 100 bài `--dry-run` thinking `disabled` để so token/thời gian; báo cáo ở ledger |

**Không** trong lát này: embedding (lát 9b), bộ đánh giá gán tay (lùi — §3.2), gắn vào `--loop` hay Scheduler (lát 13), chatbot (lát 10).

## 2. Dữ kiện đã kiểm vs giả định *(§4.8 bước 0)*

### 2.1 Đã kiểm

| Dữ kiện | Bằng chứng |
|---|---|
| Ép công cụ + schema có enum ⇒ **0 lỗi schema / 232 lời gọi**, thinking bật hay tắt như nhau; nhãn tự lệch ~10% giữa hai lượt kể cả `temperature 0`; model bỏ qua độ dài `summary_ai` (p50 331–360); bịa mã `VFM` 2/19 | [minimax.md §5, §7.1](../../../10-sources/llm/minimax.md) *(đo 2026-09-06)* |
| Một bài ≈ 2,9k token vào (≈ 1,3k system/tools được cache tự động), thinking adaptive ≈ 0,7–1,3k ra · 8–12 s; disabled ≈ 250 ra · 3 s; tiếng Việt 1,62 ký tự/token ⇒ trần 3.000 ký tự ≈ 1.850 token | minimax.md §4, §7 |
| SDK `anthropic` 1.4.0 dùng **`httpx2`** (không phải `httpx`); `Anthropic(api_key, base_url, http_client=httpx2.Client(transport=httpx2.MockTransport(...)), max_retries=0)` chạy offline: parse `content[text, tool_use]`, `usage.input_tokens/cache_read_input_tokens/output_tokens/output_tokens_details.thinking_tokens`; 429 ⇒ `anthropic.RateLimitError` (`status_code 429`), `str(e)` không chứa khoá | đo 2026-09-06 15:10 trên nhánh này (`uv add anthropic` đã chạy: +`httpx2`, `httpcore2`, `jiter`) |
| `GET https://api.minimax.io/v1/token_plan/remains` (Bearer khoá) ⇒ `{"model_remains":[{"model_name":"general","current_interval_remaining_percent":97,"current_weekly_remaining_percent":86,"current_interval_status":1,…},{"model_name":"video",…}],"base_resp":{"status_code":0,"status_msg":"success"}}` | gọi thật 2026-09-06 15:12 (fixture test `tests/core/fixtures/token_plan_remains.json`) |
| Kho 2026-09-06 15:00: **7.998 bài**, `classified_from IS NULL` toàn bộ; theo `group_from_feed`: 1 → 544 · 2 → 509 · 3 → 627 · NULL → 6.318; 22 bài thân < 200 ký tự; `article_ticker` 470 dòng (`url`/`lookup`); `market.industry` level 2 = **24 mã** đúng industry-tree; `ETL_DATABASE_URL` đăng nhập `etl_worker` (role `dlck_etl`) | truy vấn kho thật |
| Lược đồ `0007`: `article.confidence numeric`, `sub CHECK` 20 mã (NULL được), `classified_from CHECK ('content','title_only')`, `group_overridden boolean NOT NULL DEFAULT false`, `labels text[] NOT NULL DEFAULT '{}'` (nhãn `x` = `group_no NULL` + `labels`); `article_revision.summary_ai text` cột thường, `tsv` GENERATED chỉ từ `title || content` — **không có trigger cấm UPDATE**; `article_ticker(article_id, security_id, via CHECK ('url','lookup','ai'))` PK có `via`; `trade_name` 0 dòng | đọc migration |
| Quyền: `0009` cấp `dlck_etl` mọi bảng hiện có **và default privileges** trên 6 schema (kể cả `news`, `ops`) — bảng mới tạo bởi owner migration tự có quyền; `dlck_api` SELECT mặc định trên `news`; `market.v_issuer_industry` đã GRANT cho `dlck_etl` (`0012`) | đọc `0009`, `0012` |
| Ngành của mã: `market.security.issuer_id → market.v_issuer_industry.industry_id` (level 2); 24 quỹ/ETF không có ngành theo thiết kế | database/README |
| `news_store.load_listed`, `news_tag.tickers_lookup/tickers_from_url`, `omo_store.open_run/close_run`, `core.env.load_dotenv`, khuôn `redact` (`fred_fetch`) và "exception chỉ giữ tên lớp" (`http_fetch`) có sẵn | code |

### 2.2 Giả định — CHƯA kiểm

| # | Giả định | Kiểm ở đâu | Nếu sai |
|---|---|---|---|
| A1 | Thêm trường `industries` (enum 24) vào schema công cụ không làm tăng lỗi hình dạng (đo 232 lời gọi chưa có trường này) | AC4: `failed_schema` + `repaired` trên ≈ 400 bài | vòng sửa một lần đã có; nếu > 2% ⇒ tách ngành thành lời gọi riêng |
| A2 | Quota Token Plan đủ cho ≈ 500 lời gọi trong một buổi (≈ 1,5M token vào, 0,5M ra); đo 45 lời gọi làm cửa sổ 5 giờ tụt ≤ 1% | AC4: `% còn lại` trước/sau, ghi ledger | chia nhiều cửa sổ 5 giờ bằng `--per-group` nhỏ hơn |
| A3 | SDK map 429/5xx của giao diện tương thích thành `RateLimitError`/`APIStatusError` (đã đo 429 offline; hình dạng thật khi throttle *chưa kiểm*) | quan sát AC4; `ops.llm_call.error` | bọc thêm `base_resp` nếu lỗi về dạng HTTP 200 |
| A4 | Ước lượng 1,62 ký tự/token đủ để cắt trần; không cần `count_tokens` | AC4: `input_tokens` p50 so ước 2,9k | đổi hằng, không đổi kiến trúc |
| A5 | Model gán ngành hợp lý ở nhóm 1/2 (chưa từng đo) | AC4: soi tay 10 bài nhóm 1/2 có ngành + phân bố ngành | chỉnh câu lệnh prompt; không đổi lược đồ |

Phần giả định không nặng hơn dữ kiện; đều kiểm được ngay trong nghiệm thu.

## 3. Phạm vi

### 3.1 Trong phạm vi

- **`backend/core/llm/`** (mới): `settings.py` (`LLMSettings.from_env()`: `LLM_API` bắt buộc, `LLM_BASE_URL` mặc định `https://api.minimax.io/anthropic`, `LLM_MODEL` mặc định `MiniMax-M3`, `LLM_TIMEOUT_S` mặc định 120; `__repr__` che khoá) · `client.py` (`LLMClient(settings, *, http_client=None, max_retries=3)`: `structured(schema, *, system, user, thinking, max_tokens=4000, temperature=None) -> Structured[T]`, `token_plan_remains() -> QuotaRemains`, thuộc tính `raw`) · `usage.py` (`Usage` cộng dồn + `estimate_usd()` theo giá pay-go minimax.md) · `errors.py` (`LLMError(retryable, reason)`) · `__init__.py`. Không `messages()`/`stream()` — lát 10 thêm khi cần (§4.2-XIII).
- **`uv add anthropic`** (đã chạy, `pyproject` + `uv.lock`); `.env.example` thêm `LLM_API=` (rỗng) và hai biến tuỳ chọn.
- **Migration `0018_news_industry_llm_call.py`**: `news.article_industry` + `ops.llm_call` (§5.3); test schema `test_s15_news_industry_llm_call.py` gồm ca chạy dưới role `dlck_etl` thật đi qua **mọi đường ghi/đọc của job** (INSERT hai bảng mới, UPDATE `news.article`, UPDATE `news.article_revision.summary_ai`, INSERT `article_ticker`, SELECT `market.industry`/`v_issuer_industry`/`security`).
- **`backend/etl/news_classify.py`**: `build_schema(industry_codes) -> type[BaseModel]` (Pydantic động, enum `group`/`sub`/`industries`), `system_prompt(industries: list[tuple[code, name_vi]])`, `user_prompt(row, cap) -> (text, content_chars, classified_from)`, `select_articles(conn, *, limit, per_group)`, `apply(conn, row, result, listed, industry_ids, hint) -> ApplyStats` (thuần SQL, một giao dịch/bài), `classify_run(engine, client, ...) -> stats`, `run(...)` CLI: `--limit N | --per-group N` (bắt buộc một), `--thinking adaptive|disabled` (mặc định `adaptive`), `--dry-run [--out FILE.jsonl]`, `--max-minutes`, `--cap-chars` (mặc định 3000).
- **`__main__.py`**: subcommand `classify`.
- Tài liệu §8; ledger với bảng đo token/thời gian/chi phí.

### 3.2 Ngoài phạm vi — ba loại *(§1.4)*

| Mục | Loại | Lý do |
|---|---|---|
| Embedding, dedupe ngữ nghĩa, migration cột `halfvec(768)` | **Đã có đường khác** | lát 9b (roadmap); `embo-01` bị chặn dưới gói và 1536 chiều ≠ 768 |
| Bộ đánh giá gán tay 100–150 bài, ngưỡng `confidence`, chốt thinking cuối cùng, chốt trần 3.000/4.000 | **Loại có chủ đích** | chủ dự án 2026-09-06 chiều: lát này đo **token và thời gian**; số đúng/sai là điều kiện trước khi bật lưới tự động (lát sau), không phải trước khi dựng công cụ |
| Chạy toàn kho 7.998 bài | **Loại có chủ đích** | chủ dự án: ≈ 100 bài/nhóm; chạy tiếp sau này chỉ là gọi lại lệnh với trần khác |
| Gắn phân loại vào vòng `--loop` / task Scheduler | **Đã có đường khác** | lát 13 chuẩn hoá cách chạy; job lô chạy tay đủ cho đo |
| Seed `news.trade_name` (tên thương mại → mã) và khớp mờ `pg_trgm` | **Loại có chủ đích** | chưa có nguồn tên thương mại; model đọc toàn văn đã đổi tên → mã (17/19 đúng, minimax.md §7.1) — tầng 3 lát này = mã AI **lọc qua `market.security`**; mở lại khi đo thấy AI sót tên doanh nghiệp |
| `messages()`/`stream()`/`tool_runner` trong `core/llm` | **Đã có đường khác** | lát 10 (chatbot) — YAGNI §4.4.2; `raw` đủ để lát 10 bắt đầu |
| Song song nhiều luồng | **Loại có chủ đích** | 400 bài × ~10 s ≈ 70 phút chấp nhận được; Token Plan "3–4 agent" |
| Tải lại bài để bắt bản sửa | **Đã có đường khác** | lát 12 (nợ lát 8) |
| Khoá pay-go, `service_tier` | **Đã có đường khác** | chỉ đổi `.env` khi mở web công khai (roadmap câu 8) |

## 4. Quyết định

### 4.1 Chủ dự án chốt (chat 2026-09-06 chiều)

1. **Gắn ngành** bằng bảng riêng `news.article_industry`, hai đường `via='ticker'` (suy từ mã qua `v_issuer_industry`, xác định) và `via='ai'` (model đọc hiểu, có `confidence`); ngành áp **mọi nhóm**, mã chỉ nhóm 3. Không dùng cột mảng trên `article` (mất FK, mất `via`, mất `confidence`).
2. **Phạm vi chạy thử: ≈ 100 bài gần nhất mỗi loại**, không chạy toàn kho; mục tiêu chính **đo token và thời gian**. *(Trợ lý hiểu "mỗi loại" = mỗi giá trị `group_from_feed` 1 · 2 · 3 · NULL — bốn nhóm ⇒ ≈ 400 bài; ghi §9 để rà.)*
3. **"Như bạn đề xuất"** cho tám điểm của roadmap: phương án A + `backend/core/llm/`; thinking `adaptive` mặc định (tắt được bằng cờ để đo); tách 9a/9b; bộ gold lùi; trần 3.000; không chạy toàn kho; nhịp = job lô có trần, không gắn `--loop`; Token Plan cho dev/test.

### 4.2 Điểm trợ lý tự chốt khi viết spec (ghi §9 để rà)

| # | Chốt | Vì sao | Đảo ngược khi |
|---|---|---|---|
| I | Subcommand riêng `etl classify`, job `news.classify` | `etl news` đã có 9 cờ loại trừ chéo; phân loại là bước khác thu thập (chạy sau, có trần, tốn tiền) | — |
| II | **Bắt buộc** `--limit N` hoặc `--per-group N`; không có chế độ "chạy hết" | mọi lời gọi tốn quota; quên trần = 22 giờ + hết cửa sổ tuần | — |
| III | `--dry-run` gọi model **thật**, không ghi `news.*`, không ghi `ops.llm_call`, không mở `etl_run`; xuất JSONL từng bài qua `--out` | so hai chế độ thinking trên cùng tập bài mà không đụng kho; đo là mục tiêu chính | — |
| IV | Bảng `ops.llm_call` ghi **mỗi lời gọi** (token 4 loại, độ trễ, trạng thái, `article_id`, `run_id`) | "đo token và thời gian" cần số từng lời gọi, không chỉ tổng; lát 10 dùng lại để tính quota chatbot | — |
| V | Nhãn `x` ⇒ `group_no NULL`, `sub NULL`, `labels = '{x}'`, `confidence` vẫn ghi; `group_overridden = (hint IS NOT NULL AND group ≠ hint)`, `x` tính là khác | đúng chú thích `0007`; §7.3 cần cờ để đo feed đặt sai nhóm | — |
| VI | Tầng 2 (`lookup` + `url`) chạy **bù** cho bài `group_no = 3` mà `ticker_step_ran = false` (6.318 bài backfill); tầng 3 = `tickers` của model lọc `status='listed'`, ghi `via='ai'`; mã bị lọc đếm `tickers_ai_dropped`; `ticker_step_ran = true` khi `group_no = 3` | đóng lỗ roadmap (tầng 2 chỉ chạy khi `group_from_feed == 3`); `VFM` bịa | — |
| VII | `classified_from = 'title_only'` khi thân bài < 200 ký tự (CafeF CBTT); còn lại `'content'`; `content_chars` = số ký tự **thân bài** thực nạp (≤ `cap`), không tính tiêu đề/sapo | §7.1b; `content_chars` để đối chiếu chọn trần sau | — |
| VIII | Guard quota: gọi `token_plan_remains()` **trước lượt** và **mỗi 25 bài**; dừng (`quota_stop`) khi `general` cửa sổ 5 giờ < **20%** hoặc tuần < **10%**; guard hỏng (HTTP ≠ 200) ⇒ cảnh báo, không chặn. Cầu chì `ModelDown` sau **5** lỗi liên tiếp (khuôn `SourceDown`) | brainstorm §4.4; không đốt hết quota của chatbot | ngưỡng chỉnh ở hằng |
| IX | `summary_ai` ghi bằng `UPDATE news.article_revision SET summary_ai` trên **phiên bản mới nhất** (chỉ khi đang NULL) | cột sinh ra để đó; bất biến §9.4 áp cho `title/sapo/content` — `0007` không có trigger; không tạo revision mới vì nội dung không đổi | — |
| X | Ngành `via='ticker'` **lưu vật lý** lúc phân loại, từ **mọi** `article_ticker` của bài (url/lookup/ai) qua `v_issuer_industry`; không dùng view thay bảng | giữ ngành tại thời điểm gắn (mã đổi ngành sau không xoá lịch sử), nhất quán với `article_ticker`; phép đo "AI trùng suy-từ-mã bao nhiêu" chạy bằng SQL | — |
| XI | Chọn bài: `classified_from IS NULL`, thứ tự `published_at DESC NULLS LAST, article_id DESC`; `--per-group N` = N bài đầu của **mỗi** giá trị `group_from_feed` (1, 2, 3, NULL); bài `classified_from IS NOT NULL` không bao giờ chọn lại (không có `--force`) | "gần nhất mỗi loại"; chạy lại nối tiếp tự nhiên | cần phân loại lại (đổi prompt) ⇒ thêm `--force` sau, kèm xoá dòng `ai` cũ |
| XII | Tuần tự một luồng; **không** giãn cách giữa lời gọi | đo 232 lời gọi cách 0,5 s không bị chặn; SDK tự retry 429 (`max_retries=3`, backoff mũ) | throttle thật ⇒ thêm giãn cách |
| XIII | `core/llm` lát này chỉ có `structured`, `token_plan_remains`, `raw` | YAGNI; lát 10 thêm `messages/stream` khi đo streaming | — |
| XIV | System prompt = taxonomy §3 (khối đo 232 lời gọi) + **danh sách 24 ngành nạp từ `market.industry` lúc chạy** (code — tên), câu lệnh ngành: "ngành liên quan trực tiếp, tối đa 3, rỗng nếu không thuộc ngành nào, áp cho mọi nhóm"; khối tĩnh đặt đầu để cache tự động; `max_tokens 4000`; không đặt `temperature` | industry-tree là chủ nội dung, không chép cứng (chatbot-semantic-layer §3.2); cache ≥ 512 token | — |
| XV | Lược đồ Pydantic: `Classification(group: Literal['1','2','3','x'], sub: Literal[20 mã + 'x'], confidence: float [0,1], summary_ai: str, tickers: list[str], industries: list[Literal[24]])`, `extra='forbid'`; validator: `sub` phải thuộc `group`; `summary_ai` không ràng buộc độ dài (đo: model không tuân) | minimax.md §5, §7.1 | — |
| XVI | Bảng ngành dùng `industry_id` (FK `market.industry`) không dùng `code` | nhất quán `issuer.industry_id`, `industry_icb_map` | — |

## 5. Thiết kế

### 5.1 File và thay đổi

| File | Thay đổi |
|---|---|
| `backend/core/llm/{__init__,settings,client,usage,errors}.py` | mới (§3.1) |
| `backend/tests/core/{test_llm_settings,test_llm_client,test_llm_usage}.py` + `fixtures/token_plan_remains.json` | mới |
| `database/migrations/versions/0018_news_industry_llm_call.py` · `backend/tests/schema/test_s15_news_industry_llm_call.py` | mới |
| `backend/etl/news_classify.py` · `backend/tests/etl/{test_e59_news_classify,test_e60_classify_job,test_e61_classify_cli}.py` | mới |
| `backend/etl/__main__.py` | thêm `classify` |
| `backend/pyproject.toml`, `uv.lock`, `.env.example` | `anthropic>=1.4.0`; `LLM_API=`, `LLM_BASE_URL`, `LLM_MODEL` |
| Tài liệu §8 | |

### 5.2 Hợp đồng `core/llm`

```python
@dataclass(frozen=True)
class LLMSettings:
    api_key: str; base_url: str; model: str; timeout_s: float
    @classmethod
    def from_env(cls) -> "LLMSettings"   # thiếu LLM_API ⇒ LLMConfigError("thiếu LLM_API")
    def __repr__(self)                    # 'LLMSettings(model=MiniMax-M3, base_url=…, api_key=<đặt, 40 ký tự>)'

@dataclass
class Usage:
    input_tokens: int = 0; cache_read_tokens: int = 0; output_tokens: int = 0; thinking_tokens: int = 0
    calls: int = 0; latency_s: float = 0.0
    def __add__(self, other) -> "Usage"
    def estimate_usd(self) -> float       # input*0.30 + cache_read*0.06 + output*1.20, đơn vị $/1M — giá minimax.md §3 (2026-09-06); input = phần không cache

class LLMError(Exception):
    retryable: bool; reason: str          # 'rate_limit' | 'server' | 'auth' | 'schema' | 'transport' | 'bad_request'

@dataclass
class Structured(Generic[T]):
    value: T; usage: Usage; repaired: bool; stop_reason: str

@dataclass
class QuotaRemains:
    interval_pct: int; weekly_pct: int; raw: dict     # model_name == 'general'

class LLMClient:
    def __init__(self, settings, *, http_client=None, max_retries=3)
    raw: anthropic.Anthropic
    def structured(self, schema: type[T], *, system: str, user: str, thinking: str = "adaptive",
                   max_tokens: int = 4000, temperature: float | None = None) -> Structured[T]
    def token_plan_remains(self) -> QuotaRemains      # GET {host}/v1/token_plan/remains qua http_client (httpx2), Bearer
```

Luật `structured()`: tool duy nhất `{"name": schema.__name__, "input_schema": schema.model_json_schema()}` (Pydantic `extra='forbid'` ⇒ `additionalProperties: false`), `tool_choice={"type":"tool","name":…}`, `thinking={"type": thinking}`. Đọc `content`: bỏ mọi block `text` (kể cả `"<tool_call>\n"`); block `tool_use` đầu ⇒ `schema.model_validate(input)`; không có `tool_use` mà `text` có JSON ⇒ parse (`repaired=True`); `ValidationError` ⇒ gọi lại **một** lần, thêm lượt `assistant` (nguyên `content`) + `user` "Kết quả không hợp lệ: {lỗi}. Gọi lại công cụ {tên} cho đúng." ⇒ vẫn lỗi ⇒ `LLMError(retryable=False, reason='schema')`. `Usage` cộng cả hai lời gọi. `anthropic.RateLimitError`/`InternalServerError`/`APIConnectionError`/`APITimeoutError` ⇒ `LLMError(retryable=True)`; `AuthenticationError`/`PermissionDeniedError` ⇒ `'auth'` không retry; `BadRequestError` ⇒ `'bad_request'` không retry. Thông điệp lỗi chỉ giữ **tên lớp + status** (không `str(e)` — khuôn `http_fetch`).

`token_plan_remains()`: `base_url` bỏ đuôi `/anthropic` ⇒ `https://api.minimax.io/v1/token_plan/remains`; HTTP ≠ 200 hoặc `base_resp.status_code ≠ 0` ⇒ `LLMError('transport', retryable=True)`; không có `general` ⇒ `LLMError('bad_request')`.

### 5.3 Migration `0018`

```sql
CREATE TABLE news.article_industry (
  article_id  bigint NOT NULL REFERENCES news.article,
  industry_id bigint NOT NULL REFERENCES market.industry,   -- luôn level 2 (kỷ luật code; view v_issuer_industry chỉ có level 2)
  via         text   NOT NULL CHECK (via IN ('ticker','ai')),  -- 'ticker' = suy từ article_ticker qua v_issuer_industry · 'ai' = model đọc hiểu
  confidence  numeric CHECK (confidence BETWEEN 0 AND 1),     -- NULL với 'ticker'
  PRIMARY KEY (article_id, industry_id, via)                  -- via TRONG PK: cùng (bài, ngành) do hai đường tìm ra là HAI dòng — đo 'ai' vs 'ticker'
);
CREATE INDEX ON news.article_industry (industry_id);          -- "mọi tin ngành thép" — truy vấn chủ lực

CREATE TABLE ops.llm_call (
  call_id           bigint generated always as identity PRIMARY KEY,
  called_at         timestamptz NOT NULL DEFAULT now(),
  purpose           text NOT NULL,                             -- 'news.classify' · lát 10: 'chat'
  model             text NOT NULL,
  thinking          text NOT NULL CHECK (thinking IN ('adaptive','disabled')),
  run_id            bigint REFERENCES ops.etl_run,
  article_id        bigint REFERENCES news.article,
  status            text NOT NULL CHECK (status IN ('ok','repaired','failed')),
  http_calls        smallint NOT NULL DEFAULT 1,               -- 2 khi phải gọi lại sửa schema
  input_tokens      int, cache_read_tokens int, output_tokens int, thinking_tokens int,
  latency_ms        int NOT NULL,
  error             text                                       -- 'RateLimitError 429' — KHÔNG BAO GIỜ chứa khoá
);
CREATE INDEX ON ops.llm_call (purpose, called_at);
```

Quyền: default privileges `0009` phủ (`dlck_etl` ghi, `dlck_api` đọc `news`); test schema chạy **dưới `dlck_etl` thật** để chứng, không suy. `downgrade`: DROP hai bảng.

### 5.4 Một lượt `etl classify`

```
run(limit|per_group, thinking, dry_run, out, max_minutes, cap)
 ├─ load_dotenv · engine · LLMSettings.from_env · LLMClient
 ├─ industries = SELECT industry_id, code, name_vi FROM market.industry WHERE level = 2 ORDER BY sort_order   (24, khác ⇒ RuntimeError)
 ├─ listed = news_store.load_listed · Schema = build_schema(codes) · SYSTEM = system_prompt(industries)
 ├─ rows = select_articles(limit/per_group)  — article_id, primary_source, feed, group_from_feed, ticker_step_ran, url (CafeF CBTT),
 │        title, sapo, content của revision MỚI NHẤT
 ├─ quota = token_plan_remains()  ⇒ dưới ngưỡng ⇒ dừng trước khi gọi (stats.quota_stop, exit 0)
 ├─ [không dry-run] run_id = open_run('news.classify')
 └─ với mỗi bài (tuần tự):
      user, content_chars, classified_from = user_prompt(row, cap)
      r = client.structured(Schema, system=SYSTEM, user=user, thinking=thinking)
         LLMError retryable ⇒ failed + streak (5 ⇒ ModelDown) · reason 'schema' ⇒ failed_schema · 'auth' ⇒ dừng ngay (exit 2)
      [dry-run] ghi JSONL {article_id, hint, value, usage, latency, repaired} ⇒ tiếp
      với một giao dịch: apply():
         UPDATE news.article SET group_no, sub, confidence, classified_from, content_chars, group_overridden, labels,
                ticker_step_ran = ticker_step_ran OR (group_no = 3)
         UPDATE news.article_revision SET summary_ai WHERE article_id AND version = max AND summary_ai IS NULL
         nếu group = 3: tầng 2 bù (url + lookup trên title+sapo, chỉ khi ticker_step_ran cũ = false) · tầng 3: tickers ∩ listed ⇒ article_ticker via 'ai'
         INSERT article_industry via 'ai' (industries × industry_id, confidence) ON CONFLICT DO NOTHING
         INSERT article_industry via 'ticker' SELECT DISTINCT industry_id FROM article_ticker JOIN security JOIN v_issuer_industry WHERE article_id ON CONFLICT DO NOTHING
         INSERT ops.llm_call (status ok|repaired, token, latency, run_id, article_id)
      lỗi ⇒ INSERT ops.llm_call (status failed, error = 'Tên lớp status') trong giao dịch riêng; bài giữ nguyên NULL
      mỗi 25 bài: quota ⇒ dưới ngưỡng ⇒ quota_stop, dừng · max_minutes ⇒ budget_hit
 └─ close_run(stats) · log tổng kết
```

`stats`: `{"thinking", "cap_chars", "selected", "classified", "failed", "failed_schema", "repaired", "groups": {"1","2","3","x"}, "overridden", "title_only", "tickers_ai", "tickers_ai_dropped", "tickers_lookup", "industries_ai", "industries_ticker", "tokens": {"input","cache_read","output","thinking"}, "latency_s": {"p50","p90","max","total"}, "usd_estimate", "quota": {"before": {"interval_pct","weekly_pct"}, "after": {…}}, "quota_stop", "budget_hit", "model_down"}`.

### 5.5 Xử lý lỗi

Khuôn lát 8: `open_run` ngay trước `try`; `KeyboardInterrupt` ⇒ `failed 'dừng tay (Ctrl+C)'` exit 130; `ModelDown` ⇒ `failed` kèm `stats` exit 1; lỗi khác ⇒ `failed` exit 2; mọi exception thoát `classify_run` mang `stats`. Lỗi một bài **không** giết lượt (C2 lát 8). Lỗi `auth` dừng ngay — gọi tiếp vô ích. Thiếu `LLM_API` ⇒ log rõ, exit 2 **trước** khi mở `etl_run`.

## 6. Seam test *(chốt cùng plan; expected là literal đọc tay)*

| Seam | Ca phải có |
|---|---|
| `LLMSettings.from_env` | thiếu `LLM_API` ⇒ `LLMConfigError` có chữ `LLM_API`; đủ ⇒ mặc định `base_url`/`model`/`timeout 120`; `repr` **không chứa** chuỗi khoá giả `zz-secret-key-0123456789` nhưng chứa `24 ký tự` |
| `LLMClient.structured` (transport `httpx2.MockTransport`) | (a) `tool_use` đúng ⇒ `value.group == "3"`, `value.industries == ["KIMLOAI"]`, `repaired False`, `usage` literal `214/2816/250/120`, `calls 1`, body gửi có `tool_choice.name == "Classification"` và `thinking.type == "adaptive"`; (b) `content` chỉ `text` JSON + `end_turn` ⇒ `repaired True`; (c) block `"<tool_call>\n"` + `tool_use` ⇒ bỏ text; (d) lần 1 `sub "9z"` ⇒ lần 2 đúng ⇒ `calls 2`, `repaired True`, lượt 2 có 3 message; (e) sai hai lần ⇒ `LLMError` `retryable False`, `reason 'schema'`; (f) 429 ⇒ `LLMError` `retryable True` `reason 'rate_limit'`; (g) 401 ⇒ `'auth'` không retry; (h) `str(err)` không chứa khoá `zz-secret-key…` |
| `LLMClient.token_plan_remains` | fixture thật ⇒ `interval_pct 97`, `weekly_pct 86`; body `base_resp.status_code 1002` ⇒ `LLMError retryable`; URL gọi == `https://api.minimax.io/v1/token_plan/remains`, header `Authorization: Bearer …` |
| `Usage.estimate_usd` / `__add__` | `Usage(input_tokens=1850, cache_read_tokens=1300, output_tokens=1000)` ⇒ `0.00183` (làm tròn 5 chữ số; `input_tokens` của SDK là phần **không** cache — đo minimax.md §6: lượt 2 `input 214 / cache_read 2.816`); cộng hai `Usage` ⇒ từng trường cộng, `calls` cộng |
| migration `0018` (schema) | `via` ngoài `('ticker','ai')` ⇒ vi phạm; `confidence 1.5` ⇒ vi phạm; PK trùng `(a, i, via)` ⇒ vi phạm, cùng `(a, i)` khác `via` ⇒ 2 dòng; `ops.llm_call.status 'meh'` ⇒ vi phạm; **dưới `SET LOCAL ROLE dlck_etl`**: INSERT `article_industry`, INSERT `llm_call`, UPDATE `article.group_no`, UPDATE `article_revision.summary_ai`, SELECT `market.industry`/`v_issuer_industry` đều chạy; `dlck_api` SELECT `article_industry` được |
| `news_classify.build_schema` | JSON schema có `properties.industries.items.enum` = 24 mã đúng thứ tự đưa vào, `sub.enum` 21 giá trị, `additionalProperties False`, `required` 6 khoá; `model_validate({"group":"3","sub":"1a",…})` ⇒ `ValidationError` (sub lệch nhóm); `{"group":"x","sub":"x"}` hợp lệ |
| `news_classify.user_prompt` | thân 5.000 ký tự, `cap 3000` ⇒ `content_chars 3000`, `classified_from 'content'`, prompt chứa `Tiêu đề:` và `nhóm gợi ý: 3`; thân 150 ký tự ⇒ `title_only`, `content_chars 150`; thân rỗng ⇒ `title_only`, `0`; hint NULL ⇒ `nhóm gợi ý: không có` |
| `news_classify.system_prompt` | chứa 24 dòng `CODE — tên`; chứa `3i`; không chứa khoá |
| `news_classify.apply` (DB, mồi 4 bài `zz-classify-*`, 2 mã `ZZK`/`ZZQ` niêm yết, issuer `ZZK` có ngành `KIMLOAI` qua `issuer.industry_id`, `ZZQ` không ngành) | (a) bài hint 1, kết quả `3/3d`, tickers `["ZZK","VFM"]`, industries `["KIMLOAI","XAYDUNG"]` ⇒ `group_no 3`, `sub '3d'`, `group_overridden True`, `ticker_step_ran True`, `article_ticker` có `(ZZK,'ai')` không có `VFM`, `tickers_ai_dropped 1`, `article_industry`: `(KIMLOAI,'ai')`, `(XAYDUNG,'ai')`, `(KIMLOAI,'ticker')` = **3 dòng**; `summary_ai` ghi ở version max; (b) kết quả `x` ⇒ `group_no NULL`, `sub NULL`, `labels {x}`, `confidence` ghi, không ticker; (c) hint 3 kết quả 1 ⇒ `overridden True`, không chạm ticker; (d) hint NULL, `ticker_step_ran false`, kết quả 3, tiêu đề chứa `ZZQ` ⇒ tầng 2 bù ghi `(ZZQ,'lookup')`, `tickers_lookup 1`, không có dòng `ticker`-industry (ZZQ không ngành); chạy `apply` hai lần ⇒ số dòng không đổi |
| `news_classify.select_articles` (DB) | `per_group 1` trên 4 bài mồi (hint 1/2/3/NULL, `published_at` khác nhau) ⇒ 4 bài; bài đã `classified_from` không chọn; `limit 2` ⇒ 2 bài mới nhất |
| `news_classify.classify_run` (DB, `client` giả trả `Structured` theo kịch bản) | 3 bài ok + 1 `LLMError schema` ⇒ `classified 3`, `failed_schema 1`, `ops.llm_call` 4 dòng (3 `ok`, 1 `failed` với `error` không chứa khoá), `etl_run` `success` stats `tokens.input` = tổng literal, `latency_s.p50` literal; quota giả `(15, 50)` ⇒ `quota_stop True`, 0 lời gọi model; 5 lỗi retryable liên tiếp ⇒ `ModelDown`, `etl_run failed` mang stats; `dry_run` ⇒ 0 dòng `llm_call`, 0 `etl_run`, JSONL 4 dòng, bài vẫn NULL |
| CLI | `classify --per-group 100` ⇒ `run(per_group=100, thinking='adaptive')`; thiếu cả `--limit`/`--per-group` ⇒ exit 2; cả hai ⇒ exit 2; `--out` không có `--dry-run` ⇒ exit 2; `--thinking foo` ⇒ exit 2 |
| quyền production | test schema `s15` dưới `dlck_etl` (trên); AC3 chạy `--dry-run --per-group 3` bằng `ETL_DATABASE_URL` thật + khoá thật **trước** lượt ghi |

## 7. Tiêu chí nghiệm thu

| | Nội dung | Bằng chứng |
|---|---|---|
| AC1 | Toàn bộ test xanh | trước **809 passed, 2 skipped** / sau |
| AC2 | `alembic upgrade head` trên kho thật ⇒ head `0018`; `downgrade 0017` + `upgrade head` trên `dulieu_test` sạch | log alembic |
| AC3 | `etl classify --dry-run --per-group 3 --out …` dưới credential production + khoá thật: 12 lời gọi, JSONL 12 dòng hình dạng đúng, 0 `failed`; log không chứa khoá (`grep` chuỗi 8 ký tự đầu khoá ⇒ 0) | JSONL + grep |
| AC4 | **Lượt đo chính**: `etl classify --per-group 100` (adaptive) ⇒ ≈ 400 bài: `stats` đủ trường §5.4; bảng ledger: token vào/cache/ra/thinking (tổng, p50), độ trễ p50/p90/max/tổng, `usd_estimate`, quota trước/sau, phân bố `groups`/`x`/`overridden`/`title_only`, `tickers_ai`/`dropped`/`lookup`, `industries_ai`/`ticker`, `repaired`/`failed`; **soi tay 10 bài** (5 nhóm 1/2 có ngành, 5 nhóm 3) — ghi nhận định tính, **không** phải số đúng/sai | `ops.etl_run` + truy vấn + ledger |
| AC5 | **So thinking**: trước AC4, `--dry-run --thinking disabled --per-group 25 --out …` (100 bài, trùng tập AC4) ⇒ bảng token/độ trễ hai chế độ trên cùng 100 bài (JSONL AC5 đối chiếu `ops.llm_call` AC4 theo `article_id`); tỷ lệ cùng nhóm/sub giữa hai chế độ ghi làm số tham khảo | ledger |
| AC6 | Lượt hai `--per-group 100` chọn **bài khác** (0 `article_id` trùng AC4); tổng `classified_from IS NOT NULL` = AC4 + lượt hai; `article_industry`/`article_ticker` không có dòng trùng; **có thể dừng lượt hai bằng `--max-minutes 5`** để không vượt phạm vi | truy vấn |
| AC7 | `SELECT` đối chiếu: số bài có ngành `ai` ∩ `ticker`, số ngành `ai` ⊄ `ticker` ở nhóm 3; ghi ledger làm số nền cho lát sau | truy vấn |
| AC8 | Tài liệu §8 xong; `git grep "article_industry\|llm_call\|etl classify"` ngoài `90-records/` đều trỏ đúng; roadmap gạch "Điểm vào cho lát 9", viết "Điểm vào cho lát 9b" | grep |

## 8. Checklist tài liệu sống — cùng lượt

- [ ] [news-pipeline.md](../../../20-design/news-pipeline.md): §7.1 đầu ra thêm `industries[]`; **§8b mới "Gắn ngành — hai đường"** (bảng `article_industry`, `ticker` xác định, `ai` mọi nhóm, tối đa 3, ngành level 2, không nhúng danh sách vào prompt tĩnh); §12 cập nhật (dedupe đo 0,5%; `confidence`/trần: số nền từ AC4; embedding → 9b); §14 thêm mục lát 9a *(2026-09-06)*.
- [ ] [minimax.md](../../../10-sources/llm/minimax.md) *(đo 2026-09-06 chiều)*: §7 thêm dòng số thật ≈ 400 bài (token/độ trễ với `industries`), §3 quota trước/sau lượt, §10 `httpx2` + `MockTransport` đã kiểm; §9 hình dạng 429 nếu gặp.
- [ ] [database/README.md](../../../../database/README.md): 18 migration (`0018` hai bảng), số test, "đọc ngành của tin qua `news.article_industry`".
- [ ] [backend/README.md](../../../../backend/README.md): mục "Chạy job classify" (cờ, trần bắt buộc, quota, `ops.llm_call`, ước chi phí), dependency `anthropic`, trạng thái code; số test.
- [ ] [architecture.md](../../../00-overview/architecture.md) cây `core/`: thêm `llm/`.
- [ ] [roadmap.md](../../../00-overview/roadmap.md): bảng lát — lát 9 → **9a ✅** + **9b** (embedding); gạch "Điểm vào cho lát 9", viết **"Điểm vào cho lát 9b"** (trạng thái bàn giao, số đo AC4/AC5, việc còn: gold, ngưỡng, `--loop`, embedding); dòng "Code sản phẩm" thêm lát 9a; §2 nếu chạm.
- [ ] `.env.example`: `LLM_API=` + hai biến tuỳ chọn.
- [ ] `90-records/README.md`: dòng plan này; `ledger.md` cùng thư mục; khảo sát LLM README trỏ tới plan.

## 9. Điểm cần chủ dự án duyệt tường minh

1. "≈ 100 bài gần nhất mỗi loại" hiểu là **mỗi nhóm gợi ý feed (1 · 2 · 3 · không nhóm) ⇒ ≈ 400 bài** (§4.1-2). Nếu ý là mỗi **nguồn báo** (8 × 100 = 800) thì chỉ đổi tham số `--per-group` thành `--per-source` — báo lại một câu.
2. Subcommand riêng `etl classify` và bảng sổ `ops.llm_call` (§4.2-I, IV).
3. Bắt buộc trần `--limit`/`--per-group`, không có "chạy hết" (§4.2-II).
4. `summary_ai` ghi bằng UPDATE cột trên revision mới nhất (§4.2-IX).
5. Ngành `via='ticker'` lưu vật lý từ mọi tầng mã; `industry_id` thay `code` (§4.2-X, XVI).
6. Tầng 2 chạy bù cho bài backfill được model xếp nhóm 3; tầng 3 = mã AI lọc niêm yết, **không** seed `trade_name` (§4.2-VI, §3.2).
7. Bộ gold, ngưỡng `confidence`, chốt thinking/trần: **lùi** khỏi lát này theo ý "chủ yếu đo token và thời gian" (§3.2) — lưới **chưa** chạy tự động cho tới khi có số đúng/sai.
