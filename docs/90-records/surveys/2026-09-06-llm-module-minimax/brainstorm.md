# Brainstorm — module LLM dùng chung (lát 9 lưới phân loại · lát 10 chatbot web), trên MiniMax M3

**Ngày:** 2026-09-06 trưa · **Người viết:** trợ lý, theo yêu cầu chủ dự án ("thu thập thêm thông tin để dựng sẵn một điểm vào đầy đủ cho lát 9… module này sau này còn cần được dùng lại ở chế độ chạy agent của web") · **Trạng thái:** 🟡 **đề xuất — chủ dự án rà ở phiên sau rồi mới thành spec lát 9**. Áp CLAUDE.md §4.8 vì đây là **ranh giới module + thư viện ngoài** (khó đảo ngược).

Dữ kiện nguồn: [minimax.md](../../../10-sources/llm/minimax.md) (tầng reference, mọi số kèm ngày đo) · nhật ký đo: [measure-minimax-2026-09-06.md](measure-minimax-2026-09-06.md).

---

## 0. Dữ kiện đã kiểm vs giả định *(§4.8 bước 0)*

### Đã kiểm (đọc file / chạy lệnh / có nguồn)

| # | Dữ kiện | Nguồn |
|---|---|---|
| F1 | Chủ dự án: chỉ dùng **MiniMax M3**, khoá Token Plan ở `LLM_API`; không OpenAI, không Claude | lời chủ dự án 2026-09-06 |
| F2 | Khoá chạy trên `api.minimax.io` cả hai giao diện (OpenAI `/v1`, Anthropic `/anthropic`); MiniMax khuyến nghị giao diện Anthropic cho M3 | đo + tài liệu |
| F3 | Đầu ra có cấu trúc: **ép công cụ + schema có enum ⇒ 0 lỗi schema / 232 lời gọi** (29 bài × 8 lượt) ở cả thinking bật lẫn tắt trên giao diện Anthropic, và cả giao diện OpenAI khi thinking bật; `json_schema`/`output_config` không cưỡng chế; ép function khi tắt thinking ở giao diện OpenAI hỏng 3/3 | đo ([minimax.md §5](../../../10-sources/llm/minimax.md)) |
| F4 | Tiếng Việt **1,62 ký tự/token** (20 bài); một bài phân loại ≈ 2,9k vào; thinking tắt: ≈ 250 token ra, **3 s**; thinking bật: ≈ 500 token ra, 4,7–5,5 s (đuôi 22 s) | đo |
| F4b | Nhất quán nhãn giữa hai lượt bất kỳ 86–100% nhóm, 72–97% nhóm+sub; **thinking và `temperature 0` không đổi con số này**; bất đồng dồn vào 6/29 bài mơ hồ thật; model bỏ qua độ dài `summary_ai` (p50 331–360 ký tự); bịa mã `VFM` 2/19 lần | đo ([minimax.md §7.1](../../../10-sources/llm/minimax.md)) |
| F5 | Cache tự động chạy (system + tools ≈ 2,8k token đọc lại từ lượt 2); `cache_control` vô hiệu trên M3 | đo |
| F6 | SDK `anthropic` 1.4.0 chạy đủ `messages.create` / vòng tool nhiều lượt / `beta.messages.tool_runner` với MiniMax | đo |
| F7 | Token Plan: cửa sổ 5 giờ + tuần, chỉ lộ % còn lại qua `GET /v1/token_plan/remains`; tài liệu nói gói cho "cá nhân, tương tác", production nên pay-go; song song ≈ 3–4 agent | đo + tài liệu |
| F8 | Embedding `embo-01`: body riêng, **bị chặn (1002) dưới khoá này**, 1536 chiều theo bên thứ ba; dự án đã chốt `halfvec(768)` | đo + news-pipeline §9.5 |
| F9 | Ranh giới tiến trình đã chốt: `core/` là thư viện lõi dùng chung, `etl` chạy job theo lịch, `api` phục vụ người dùng (chatbot function calling nằm trong `api`, có thể tách sau) | service-topology §2, §3, §8 |
| F10 | Skill chatbot là hai thư mục prompt `backend/agent/skills/` (3.046 dòng), đã test 6 vòng **không** có công cụ dữ liệu; tầng ngữ nghĩa đề xuất 8 function | chatbot-semantic-layer.md |
| F11 | Test: cấm gọi nguồn ngoài trong CI, mock HTTP; DB test thật; mỗi seam một test đỏ trước | test-strategy.md |
| F12 | Repo có khuôn `http_fetch.Fetcher` (get bơm được, retry/backoff, exception chỉ giữ tên lớp) và `fred_fetch.redact` che khoá | code |
| F13 | Kho tin hiện 7.974 bài, trường AI NULL, 6.312 bài backfill không nhóm gợi ý; dedupe theo tiêu đề y hệt ≈ 0,5% | ledger lát 8b, roadmap |

### Giả định — chưa kiểm

| # | Giả định | Kiểm ở đâu | Nếu sai |
|---|---|---|---|
| A1 | ~~Ép công cụ đúng ≈ 100% ở quy mô trăm bài~~ ✅ **đã đo 232 lời gọi, 0 lỗi schema** (F3) — vòng sửa vẫn giữ làm lưới an toàn cho toàn kho | — | — |
| A2 | Quota Token Plan đủ cho ~350 bài/ngày + backlog 8k bài (ước ≈ 3M token vào/ngày lúc nạp backlog) | đọc `remains` trước/sau lô 100 bài | chạy backlog rải nhiều cửa sổ 5 giờ; hoặc khoá pay-go cho backlog |
| A3 | Streaming qua SDK (`messages.stream`) hoạt động trên MiniMax | đo ở lát 10 | chatbot trả lời không streaming trước |
| A4 | HTTP 429/5xx của giao diện tương thích được SDK map thành `RateLimitError`/`APIStatusError` (SDK tự retry 2 lần) | quan sát khi chạy thật | bọc retry riêng theo `base_resp` |
| A5 | Không có endpoint `count_tokens`; ước bằng 1,62 ký tự/token là đủ để cắt trần | đo `messages.count_tokens` ở lát 9 | dùng `max_tokens: 1` để đếm khi cần chính xác |
| A6 | Độ chính xác phân loại M3 đạt mức chấp nhận trên taxonomy 20 sub (chưa có số đúng/sai; mới có nhất quán 86–100% — F4b) | **bộ đánh giá gán tay** ≥ 100 bài, chạy **3 lượt** mỗi cấu hình vì nhãn tự lệch 10% | chỉnh prompt / few-shot / gộp sub mơ hồ; không có model dự phòng theo F1 |

Phần giả định **không nặng hơn** dữ kiện ⇒ đủ điều kiện sinh phương án.

## 1. Tiêu chí chấp nhận (viết trước khi chấm)

1. Một chỗ duy nhất biết khoá, base URL, tên model; consumer không import SDK trực tiếp.
2. Dùng được ngay cho lát 9 (phân loại theo lô, đầu ra có cấu trúc kiểm bằng schema) **và** lát 10 (chatbot nhiều lượt, tool loop, streaming) mà không viết lại.
3. Test offline: mock HTTP theo test-strategy; seam rõ để test đỏ→xanh.
4. Đếm token/chi phí mỗi lời gọi vào `stats` (etl) và log (api); che khoá tuyệt đối.
5. Đổi nhà cung cấp/khoá (Token Plan → pay-go, hay model khác) là **đổi cấu hình hoặc một file**, không lan ra consumer.
6. YAGNI: không xây abstraction cho nhà cung cấp thứ hai chưa tồn tại (F1).

## 2. Ba phương án độc lập

### A — `backend/core/llm/` mỏng trên SDK `anthropic`, trỏ giao diện Anthropic của MiniMax *(trục: tốc độ + đúng khuyến nghị nguồn)*

- `LLMSettings.from_env()` (khoá `LLM_API`, `LLM_BASE_URL` mặc định `https://api.minimax.io/anthropic`, `LLM_MODEL` mặc định `MiniMax-M3`, timeout, số luồng), `repr` che khoá.
- `LLMClient` bọc `anthropic.Anthropic(...)`: `structured(schema: type[BaseModel], system, user, *, thinking="adaptive", max_tokens, temperature) -> Structured[T]` (ép công cụ tên `schema.__name__`, kiểm Pydantic, đường sửa theo F3), `messages(...)`/`stream(...)` mỏng cho agent, `token_plan_remains()`, và `raw` (client SDK) cho `tool_runner`.
- `Usage` cộng dồn `input/cache_read/output/thinking/calls/retries`, quy tiền theo bảng giá pay-go trong `minimax.md` (để so sánh, không phải hoá đơn).
- **Rủi ro tự khai:** (i) SDK đổi phiên bản có thể thêm tham số MiniMax không hỗ trợ (bị bỏ qua lặng lẽ — F3) ⇒ cần kiểm hợp đồng sống định kỳ (lát 12), (ii) `httpx2` thêm một dependency HTTP thứ hai, (iii) beta `tool_runner` là beta của SDK.

### B — `backend/core/llm/` tự viết trên `httpx` sẵn có, gọi giao diện OpenAI `/v1` *(trục: ít phụ thuộc, kiểm soát toàn bộ)*

- Không thêm SDK; dùng `response_format` + `reasoning_split`; tự viết SSE cho streaming, tự viết vòng tool cho agent; mock bằng `httpx.MockTransport` đúng khuôn test-strategy.
- **Rủi ro tự khai:** F3 đo thấy `json_schema` không cưỡng chế và ép công cụ thất bại 3/3 khi tắt thinking; phải giữ thinking bật và tự parse `<think>`; phải tự viết và tự test toàn bộ vòng agent (streaming SSE, ghép tool call nhiều lượt) — chính phần mà lát 10 cần nhất.

### C — Cổng LLM trung lập nhà cung cấp: kiểu `Message/Tool/Result` riêng + adapter (MiniMax-Anthropic, MiniMax-OpenAI, …) *(trục: linh hoạt tương lai)*

- Consumer chỉ thấy kiểu riêng của dự án; thêm nhà cung cấp = thêm adapter.
- **Rủi ro tự khai:** xây abstraction cho nhà cung cấp thứ hai chưa tồn tại (vi phạm tiêu chí 6, §4.4.2); mỗi tính năng (thinking block, cache usage, tool loop, streaming) phải định nghĩa lại một lần nữa trong kiểu riêng; chậm nhất trong ba.

## 3. Chấm theo tiêu chí

| Tiêu chí | A | B | C |
|---|---|---|---|
| 1 một chỗ biết khoá/model | ✅ | ✅ | ✅ |
| 2 dùng được cả lát 9 lẫn lát 10 không viết lại | ✅ (F6: tool loop, tool_runner đã chạy) | ⚠️ phải tự viết SSE + tool loop | ✅ nhưng phải định nghĩa lại kiểu |
| 3 test offline | ✅ (`http_client` bơm transport giả của SDK) | ✅ (MockTransport) | ✅ |
| 4 đếm token, che khoá | ✅ | ✅ | ✅ |
| 5 đổi nhà cung cấp = cấu hình/một file | ✅ nếu giữ MiniMax-specific trong `client.py` | ✅ | ✅✅ |
| 6 YAGNI | ✅ | ✅ | ❌ |
| Độ tin cậy đầu ra có cấu trúc (F3) | ✅ ép công cụ + thinking | ⚠️ | phụ thuộc adapter |
| Khớp khuyến nghị nguồn | ✅ | ❌ | — |

**Chọn A nguyên vẹn.** Mượn một ý của C mà không xây C: mọi thứ riêng MiniMax (base URL, tên model, quirk `<tool_call>`, `remains`) nằm **trong `client.py` + `settings.py`**; consumer chỉ dùng `LLMClient` và model Pydantic của mình. Đảo ngược khi: (i) MiniMax đổi giao diện Anthropic làm SDK vỡ ⇒ chuyển `client.py` sang B (httpx thô) sau cùng interface; (ii) có nhà cung cấp thứ hai thật ⇒ nâng lên C bằng cách tách adapter khỏi `client.py`.

Loại B vì F3 (đầu ra có cấu trúc kém tin cậy hơn ở giao diện OpenAI) và vì lát 10 cần streaming + tool loop mà SDK đã có, đã đo chạy. Loại C vì F1 (chỉ một nhà cung cấp) và tiêu chí 6.

## 4. Thiết kế đề xuất (chi tiết để spec lát 9 chép vào, không phải plan)

### 4.1 Vị trí và ranh giới

```
backend/core/llm/
├── __init__.py     # xuất LLMClient, LLMSettings, Usage, LLMError, Structured
├── settings.py     # LLMSettings.from_env(); che khoá trong repr/log; KHÔNG đọc .env trực tiếp — nhận từ core.env.load_dotenv của job
├── client.py       # LLMClient: structured() · messages() · stream() · token_plan_remains() · raw (anthropic.Anthropic)
├── usage.py        # Usage (cộng dồn) + estimate_usd() theo bảng giá pay-go ghi ở 10-sources/llm/minimax.md
└── errors.py       # LLMError(retryable) từ anthropic.* và base_resp
backend/etl/news_classify.py      # lát 9: xây prompt taxonomy, gọi client.structured(Classification), ghi news.*
backend/api/chat/…                # lát 10: system = skills L1/L2 + luật, tools = 8 function, vòng tool_runner/stream
backend/agent/skills/             # giữ nguyên — prompt corpus, không phải code
```

`core/llm` **không** biết taxonomy tin hay skill chứng khoán; nó chỉ biết gọi model an toàn và đếm tiền.

### 4.2 Hợp đồng `LLMClient` (chữ ký dự kiến)

```python
class Structured(Generic[T]):
    value: T                    # đã kiểm Pydantic
    usage: Usage
    repaired: bool              # True nếu phải parse text JSON hoặc gọi lại
    raw_stop_reason: str

class LLMClient:
    def __init__(self, settings: LLMSettings, *, http_client=None): ...   # http_client bơm transport giả khi test
    def structured(self, schema: type[T], *, system: str, user: str | list, thinking: str = "adaptive",
                   max_tokens: int = 2000, temperature: float | None = None) -> Structured[T]: ...
    def messages(self, *, system, messages, tools=(), tool_choice=None, thinking="adaptive", max_tokens=4000): ...  # trả Message của SDK
    def stream(self, **kw): ...                                             # bọc client.messages.stream
    def token_plan_remains(self) -> dict: ...                               # GET /v1/token_plan/remains qua httpx, không qua SDK
    raw: anthropic.Anthropic                                                 # cho beta.messages.tool_runner ở lát 10
```

Luật trong `structured()` (từ F3): ép `tool_choice={"type":"tool","name":schema.__name__}`; **schema phải có enum** cho mọi trường phân loại (đo: enum là thứ làm 0 lỗi); bỏ block text (kể cả `"<tool_call>\n"`); nếu không có `tool_use` mà có text JSON ⇒ parse (`repaired=True`); Pydantic lỗi ⇒ gọi lại **một** lần kèm thông báo lỗi; vẫn lỗi ⇒ `LLMError(retryable=False, reason="schema")` để job đếm `failed`, không tạo dòng rỗng (khuôn §4.6-VII lát 8). Hai luật rút từ F4b nằm ở **consumer**, không ở `core/llm`: (i) độ dài `summary_ai` là ràng buộc mềm — cắt/ghi cờ, không fail; (ii) `tickers` phải lọc qua `market.security` (`VFM` bịa) trước khi ghi `article_ticker via='ai'`.

**Thinking cho phân loại — đề xuất mặc định `disabled`** (đo F3/F4/F4b: hợp lệ 100% ở cả hai, nhất quán như nhau, tắt nhanh gấp 1,8× và ra ít token gấp 2×); `adaptive` giữ cho chatbot (F6, MiniMax khuyến nghị cho tool loop). Đảo ngược nếu bộ đánh giá gán tay cho thấy bật thinking **đúng** hơn có ý nghĩa — độ chính xác chưa đo, chỉ mới đo nhất quán.

### 4.3 Cấu hình và bí mật

- Biến: `LLM_API` (bắt buộc), `LLM_BASE_URL` (mặc định MiniMax Anthropic), `LLM_MODEL` (mặc định `MiniMax-M3`), `LLM_TIMEOUT_S` (mặc định 120), `LLM_MAX_CONCURRENCY` (mặc định 2 — F7).
- Che khoá: `LLMSettings.__repr__` in `LLM_API=<đặt/chưa đặt, dài N>`; exception của SDK chỉ giữ **tên lớp + status** (khuôn `http_fetch`), không `str(e)` vì URL/headers có thể lọt.
- Chuyển sang pay-go khi web công khai: đổi `LLM_API` (Standard API Key) — không đổi code.

### 4.4 Chi phí, quota, nhịp chạy (cho spec lát 9)

- Mỗi bài ≈ 2,9k vào (1,3k cache) / ≈ 1,0k ra / ≈ 10 s. Backlog 7.956 bài ≈ 23M token vào tổng, ≈ 8M ra, ≈ 22 giờ tuần tự — chạy rải qua nhiều cửa sổ 5 giờ, **kiểm `token_plan_remains()` trước mỗi lô** và dừng khi `current_interval_remaining_percent < 20` hoặc `current_weekly_remaining_percent < 10` (ngưỡng đề xuất, chốt ở spec).
- Nhịp thường: 350 bài/ngày ≈ 1 giờ/ngày tuần tự — gắn vào vòng `--loop` (phân loại bài `new` mỗi vòng) hay job riêng theo lô là câu brainstorm lát 9 (câu 6).
- Không có Batch API ⇒ không có giảm giá lô; cache tự động đã lo phần system+tools.

### 4.5 Bộ đánh giá trước khi bật lưới (bắt buộc — A6)

- Gán tay **100–150 bài** lấy ngẫu nhiên phân tầng theo nguồn và nhóm gợi ý (có cả bài backfill không nhóm), lưu `docs/90-records/plans/<lát 9>/eval/gold.jsonl` (id, group, sub, tickers).
- Đo: độ đúng group/sub so gold, tỷ lệ `repaired`/`failed`, **độ ổn định 3 lượt** (đã biết: nhãn tự lệch ~10% nhóm dù `temperature 0`), thinking adaptive vs disabled (đã biết: hình dạng và nhất quán ngang nhau — chỉ còn câu độ đúng), trần 3.000 vs 4.000, tỷ lệ `x` (mẫu backfill: 34%). Chi phí đo ≈ 150 × 3 × 2 cấu hình × 0,1–0,2 xu ≈ $1–2 (quy đổi). Khung chạy có sẵn: [reliability/mm_reliability.py](reliability/mm_reliability.py) — chốt danh sách `article_id` trước khi đo (tập trôi khi `--loop` chạy).
- Ngưỡng `confidence` chốt từ phân bố trên gold, không đoán.

### 4.6 Lát 10 (chatbot) dùng lại thế nào

- `system` = luật phân định + L1 `vn-stock-advisor` + (L2 `vn-stock-knowledge` khi cần) — khối tĩnh đặt đầu để cache tự động (≥ 512 token, F5); tools = 8 function của chatbot-semantic-layer §2 khai bằng `@beta_tool` hoặc schema; vòng chạy = `raw.beta.messages.tool_runner` (F6) hoặc `messages()` + tự lặp; **echo nguyên `response.content`** (kể cả `thinking`) vào lịch sử (yêu cầu MiniMax).
- Streaming (A3) đo ở lát 10; nếu SDK stream không chạy trên MiniMax ⇒ trả lời không streaming trước.
- Token Plan "3–4 agent" ⇒ chỉ đủ cho dev/test nội bộ; mở công khai phải đổi khoá pay-go (4.3).

### 4.7 Embedding — tách khỏi lát 9a

F8: `embo-01` bị chặn dưới khoá này và 1536 chiều ≠ `halfvec(768)`. Đề xuất **lát 9 tách đôi**: **9a** lưới phân loại + `summary_ai` + gắn mã tầng 3 (không embedding); **9b** embedding sau khi đo nhu cầu thật (dedupe theo tiêu đề y hệt chỉ 0,5% — F13 — nên giá trị của gộp ngữ nghĩa chưa chứng minh). Ứng viên 768 chiều để đo ở 9b (*chưa kiểm* cái nào): tự host `intfloat/multilingual-e5-base` hoặc `bkai-foundation-models/vietnamese-bi-encoder` trên CPU (350 bài/ngày là nhẹ); hoặc đổi quyết định `halfvec(768)` nếu chọn `embo-01` pay-go (1536 `halfvec` ≈ 1,2 GB/năm, gấp đôi mức đã chốt).

### 4.8 Test (seam dự kiến, chốt ở plan lát 9)

| Seam | Ca |
|---|---|
| `LLMSettings.from_env` | thiếu `LLM_API` ⇒ lỗi rõ; `repr` không chứa khoá (assert chuỗi khoá giả không xuất hiện) |
| `LLMClient.structured` (transport giả trả JSON hình dạng Anthropic) | `tool_use` đúng ⇒ `value` đúng literal, `repaired False`; text JSON + `end_turn` ⇒ `repaired True`; block `"<tool_call>\n"` + `tool_use` ⇒ bỏ text; Pydantic lỗi lần 1, đúng lần 2 ⇒ 2 lời gọi; lỗi 2 lần ⇒ `LLMError` không retryable; `usage` cộng đúng `cache_read` |
| `Usage.estimate_usd` | literal: 1.850 vào + 1.300 cache + 1.000 ra ⇒ $0,00183 (giá minimax.md) |
| `errors` | 429/5xx ⇒ retryable, 4xx khác ⇒ không; `base_resp 1002` ⇒ retryable |
| `token_plan_remains` (httpx MockTransport) | JSON mẫu đã đo ⇒ % đúng literal 99/86 |
| quyền/khoá | log của một lời gọi lỗi không chứa khoá |

Kiểm hợp đồng **sống** (không CI): script `docs/10-sources/llm/verify_minimax.py` (khuôn `verify_wichart.py`) chạy tay/lát 12: models có `MiniMax-M3`, ép công cụ 3/3, cache đọc lại ≥ 2k, `remains` trả %.

## 5. Điều kiện đảo ngược và việc chủ dự án cần chốt ở phiên sau

1. **Duyệt vị trí `backend/core/llm/` và phương án A** (hay muốn tách tiến trình `llm` riêng — không đề xuất, vì F9 và YAGNI).
2. **Thinking cho phân loại: đề xuất TẮT** (đo 232 lời gọi: hợp lệ 100% cả hai chế độ, nhất quán ngang nhau, tắt = 3 s và ≈ 250 token ra) — chốt cuối cùng sau bộ đánh giá gán tay (độ đúng chưa đo).
3. **Tách lát 9 thành 9a/9b** (4.7) và hướng embedding.
4. **Bộ đánh giá gán tay 100–150 bài**: ai gán (chủ dự án / trợ lý gán rồi chủ dự án rà 20%), khi nào.
5. **Ngưỡng quota** dừng lô (4.4) và cách chạy nhịp thường (trong `--loop` hay job lô).
6. Ghi nhận rủi ro chính sách: Token Plan "cho cá nhân, tương tác" — dùng cho dev/test; production đổi khoá pay-go.
