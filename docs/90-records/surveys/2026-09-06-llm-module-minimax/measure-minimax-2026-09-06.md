# Nhật ký đo MiniMax M3 — 2026-09-06 12:00–12:40 VN

Khoá `LLM_API` của dự án (Token Plan, không in giá trị). Công cụ: `curl`, `urllib` thuần, SDK `anthropic` 1.4.0 chạy tạm bằng `uv run --with anthropic` (không sửa `pyproject`). Số đã chép vào [minimax.md](../../../10-sources/llm/minimax.md); file này giữ output thô rút gọn theo thứ tự chạy.

## 1. Nhận diện khoá
- `.env` có `LLM_API` (125 ký tự, chỉ `[A-Za-z0-9_-]`, hình dạng 12 ký tự đầu `aa-aa-aaaaaa`); không tiền tố `sk-ant-`.
- `anthropic.Anthropic().messages.count_tokens` với khoá này ⇒ `AuthenticationError 401`.
- Chủ dự án xác nhận: MiniMax M3, Token Plan.

## 2. Endpoint và model
```
GET https://api.minimax.io/v1/models            HTTP 200  ['MiniMax-M3','MiniMax-M2.7','MiniMax-M2.7-highspeed','MiniMax-M2.5','MiniMax-M2.5-highspeed','MiniMax-M2.1','MiniMax-M2.1-highspeed','MiniMax-M2']
GET https://api.minimaxi.com/v1/models          HTTP 401  {"type":"error","error":{"type":"authorized_error","message":"invalid api key (2049)"}}
GET https://api.minimax.io/anthropic/v1/models  HTTP 200  (cùng danh sách)
```

## 3. Giao diện OpenAI `/v1/chat/completions`, M3
- `max_tokens 60`, câu hỏi VN-Index: 200, 1,3 s; `content` bắt đầu `<think>…</think>` rồi bị cắt (`finish_reason length`); usage `prompt 193 · completion 60 (reasoning 32) · cached 128`.
- `response_format json_object`, `max_tokens 120`: cắt giữa `<think>` (reasoning 119/120) — không có JSON.
- `response_format json_schema`, `max_tokens 120`: như trên.
- `tools` + câu hỏi giá HPG: 200, 7,1 s, `finish_reason tool_calls`, `tool_calls[0].function.arguments = {"ticker":"HPG","from_date":"2026-08-01"}`; content vẫn có `<think>`.
- `json_schema` + `max_tokens 1500`: 200, 7,9 s, `finish stop`, completion 675 — JSON nằm sau `</think>` (không in hết).
- `reasoning_split: true`: `content` sạch, `reasoning_content` riêng (5 câu), 4,8 s.
- Ép công cụ `tool_choice.function=classify` (thinking mặc định bật): 200, 3,4 s, `tool_calls` đúng `{"group":"1","sub":"1c","confidence":0.97,"summary_ai":…}`.
- `json_schema` + `reasoning_split` + `thinking disabled`, `max_completion_tokens 2000`: JSON hợp lệ **nhưng** `{"group":"3","sub":"3d","note":…}` — thiếu `confidence/summary_ai/tickers` dù `required` (+`strict: true`).
- `json_schema` + `thinking adaptive`: `content` = ```json {"phan_loai": {...}} ``` — không parse được, khoá tự đặt.
- Ép công cụ + `thinking disabled` ×3: `finish stop`, **không** `tool_calls` cả 3 lần (2,8 · 2,2 · 5,5 s).

## 4. Giao diện Anthropic `/anthropic/v1/messages`, M3
- Không tham số thinking: chỉ block `text`; usage `input 52 · output 60 · cache_read 128 · cache_creation 0 · service_tier standard`; 1,2 s.
- `tools` + hỏi giá HPG: `[text "Tôi sẽ lấy giá…", tool_use{get_price_series, {"ticker":"HPG"}}]`, `stop_reason tool_use`, 0,6 s.
- Ép công cụ `tool_choice {type: tool}`: `[text "<tool_call>\n", tool_use{classify, {"confidence":0.95,"group":"1","sub":"1c","summary_ai":…}}]`, 2,2 s.
- `thinking {"type":"enabled","budget_tokens":1024}`: block `thinking` (kèm `signature`) + `text`, `end_turn`, 2,2 s.
- `thinking {"type":"disabled"}`: chỉ `text`, 3,7 s.
- `output_config.format json_schema`: 200 nhưng trả **markdown** "# Phân loại tin…" — tham số bị bỏ qua.

## 5. Tokenizer tiếng Việt (20 bài thật, `max_tokens 1`)
```
(cafef, 3078 ký tự, 1778 token, 1.73) (cafef, 2454, 1513, 1.62) (tinnhanhck, 3109, 1899, 1.64) (tinnhanhck, 2454, 1674, 1.47)
(nguoiquansat, 3082, 1831, 1.68) (tinnhanhck, 3077, 1873, 1.64) (tinnhanhck, 3091, 1916, 1.61) (tinnhanhck, 3091, 1825, 1.69)
(nguoiquansat, 2415, 1421, 1.70) (nguoiquansat, 3119, 2033, 1.53) (cafef, 3119, 1867, 1.67) (nguoiquansat, 3076, 1844, 1.67)
(nguoiquansat, 3110, 1912, 1.63) (nguoiquansat, 3074, 1866, 1.65) (nguoiquansat, 2722, 1751, 1.55) (cafef, 2536, 1619, 1.57)
(nguoiquansat, 1945, 1266, 1.54) (bnews, 2575, 1609, 1.60) (cafef, 1895, 1213, 1.56) (vneconomy, 3075, 1937, 1.59)
TỔNG 20 bài: 56.097 ký tự / 34.647 token ⇒ 1,62 ký tự/token
```

## 6. Phân loại đúng hình dạng thật (system taxonomy 20 sub + tool `classify` + bài 3.000 ký tự, giao diện Anthropic, `max_tokens 4000`)
| thinking | bài | HTTP/thời gian | usage | kết quả |
|---|---|---|---|---|
| disabled | cafef/tai-chinh-quoc-te (gợi ý 2) "cổ phiếu Unitree tăng 460%" | 200 · 2,9 s | in 2.803 · out 218 · cache_read 128 | `tool_use` group 2 / 2a / 0,72, tickers [] |
| disabled | cafef/thi-truong-chung-khoan (gợi ý 3) "vàng SJC rẻ hơn thế giới" | 200 · 3,5 s | in 2.974 · out 363 | **`end_turn`, JSON dạng text** `{"group":"3","sub":"3e",…}` — không `tool_use` |
| adaptive | Unitree | 200 · 7,7 s | in 2.816 · out 691 | thinking 1.920 ký tự; `tool_use` 2 / 2a / 0,88 |
| adaptive | vàng SJC | 200 · 12,2 s | in 2.987 · out 1.267 (thinking_tokens 938) | thinking 3.282 ký tự; `tool_use` **1 / 1c** / 0,82 |

## 7. Embedding `embo-01`, `/v1/embeddings`
- body `{"model":"embo-01","input":[…]}` ⇒ 200, `base_resp {2013, "invalid params, binding: expr_path=texts, cause=missing required parameter"}`.
- body `{"model":"embo-01","texts":[…],"type":"db"}` ⇒ 200, `base_resp {1002, "rate limit exceeded(RPM)"}`; lặp lại sau 65 s ⇒ như trên (`vectors` rỗng).

## 8. SDK `anthropic` 1.4.0 trỏ `base_url=https://api.minimax.io/anthropic`
- Ép công cụ + `thinking adaptive` ×3 (system ≈ 2,8k token giả lập): lần 1 `in 3.030 · out 329 · cache_read None`; lần 2 `in 214 · out 305 · cache_read 2.816 · cache_creation 0`; lần 3 `in 214 · out 447 · cache_read 2.816`. Cả 3 lần `stop tool_use`, blocks `[thinking, tool_use]`. (Prompt giả lập nên `sub` trả "a" — không dùng làm số chất lượng.)
- `cache_control` tường minh trên `system` (M3): không lỗi, `cache_read 128 · cache_creation 0` cả hai lần.
- Vòng tool 2 lượt (echo `r1.content` gồm `thinking`, thêm `tool_result`): lượt 2 `end_turn`, `[thinking, text]`, text dùng đúng số từ tool_result.
- `client.beta.messages.tool_runner` + `@beta_tool`: chạy xong, `end_turn`, `[text]`.

## 9. Quota Token Plan `GET /v1/token_plan/remains` (12:36 VN)
```
general: start 1788670800000 (2026-09-06 12:00 VN) · end 1788688800000 (17:00 VN) · current_interval_remaining_percent 99 · status 1
         weekly_start 1788134400000 (2026-08-31 07:00 VN) · weekly_end 1788739200000 (2026-09-07 07:00 VN) · current_weekly_remaining_percent 86 · status 1
         *_total_count = *_usage_count = 0
video:   remaining 100/100, status 3
```
Hai host `www.minimax.io` và `api.minimax.io` trả giống nhau.

## 10. Tài liệu chính thức đã đọc (2026-09-06)
`docs/guides/rate-limits` (M3 200 RPM · 10M TPM) · `docs/api-reference/text-anthropic-api` · `docs/api-reference/text-openai-api` · `docs/guides/pricing-paygo` · `docs/guides/pricing-token-plan` · `docs/token-plan/intro` · `docs/token-plan/faq` · `docs/api-reference/text-prompt-caching` · `docs/api-reference/anthropic-api-compatible-cache` · `docs/guides/text-m3-function-call` · `docs/guides/models-intro` · `docs/api-reference/errorcode` · `docs/llms.txt` (index). `docs/api-reference/embeddings-api` ⇒ 404 (URL đoán sai; số chiều 1536 lấy từ LangChain/Spring AI, chưa kiểm).
