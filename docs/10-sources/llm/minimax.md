# MiniMax M3 — API mô hình ngôn ngữ của dự án

**Loại tài liệu:** tra cứu (reference) · **Đo ngày 2026-09-06 12:00–12:40 VN** (≈45 lời gọi thật bằng khoá của dự án) · **Trạng thái:** đã kiểm chứng phần đánh dấu *(đo)*; phần ghi *(tài liệu)* chép từ [platform.minimax.io/docs](https://platform.minimax.io/docs/llms.txt) cùng ngày; phần *chưa kiểm* ghi rõ.

Chủ dự án chốt 2026-09-06: **dự án chỉ dùng duy nhất MiniMax M3** cho mọi việc gọi mô hình ngôn ngữ (lưới phân loại tin lát 9, chatbot web lát 10), qua **Token Plan** đã mua. Khoá đặt ở biến `LLM_API` trong `.env` — **không bao giờ in giá trị hay ghi vào log/file** (CLAUDE.md §5). Thiết kế module dùng chung: [khảo sát 2026-09-06](../../90-records/surveys/2026-09-06-llm-module-minimax/README.md).

---

## 1. Khoá và endpoint

| | Giá trị | Bằng chứng |
|---|---|---|
| Loại khoá | **Subscription Key của Token Plan** (khác Standard API Key trả theo lượng — hai loại không dùng lẫn) | *(tài liệu)* token-plan/faq; *(đo)* khoá không có tiền tố `sk-ant-`, trả 401 với API Anthropic thật |
| Vùng | **Global** — `api.minimax.io` nhận; `api.minimaxi.com` (CN) trả `401 invalid api key (2049)` | *(đo)* |
| Giao diện tương thích OpenAI | `https://api.minimax.io/v1` — `/chat/completions`, `/models`, `/embeddings` | *(đo)* 200 |
| Giao diện tương thích Anthropic | `https://api.minimax.io/anthropic` — SDK `anthropic` trỏ `base_url` này; đường thật `/anthropic/v1/messages`, `/anthropic/v1/models` | *(đo)* 200; MiniMax **khuyến nghị** giao diện này cho M3 (tool use + interleaved thinking) *(tài liệu)* |
| Model có trong `/models` | `MiniMax-M3`, `MiniMax-M2.7`, `M2.7-highspeed`, `M2.5`, `M2.5-highspeed`, `M2.1`, `M2.1-highspeed`, `M2` | *(đo)* |
| Quota còn lại | `GET https://api.minimax.io/v1/token_plan/remains` (hoặc `www.minimax.io`), header `Authorization: Bearer <khoá>` | *(đo)* 200, xem §3 |

## 2. Model M3 *(tài liệu, trừ chỗ ghi đo)*

- Ngữ cảnh **1M token, tối thiểu đảm bảo 512K**; đa phương thức (text, ảnh, video vào; text ra). Đầu ra tối đa 262.144 token theo nguồn thứ ba — *chưa kiểm*.
- **Thinking:** giao diện OpenAI **mặc định BẬT**, chèn `<think>…</think>` ngay trong `content` *(đo)*; `reasoning_split: true` tách sang `reasoning_content` *(đo)*. Giao diện Anthropic **mặc định TẮT** cho M3; `thinking: {"type": "adaptive"}` bật, `{"type": "disabled"}` tắt *(đo cả hai)*; block `thinking` có `signature`, phải **echo nguyên vẹn** vào lượt sau (đã đo vòng tool 2 lượt chạy đúng).
- Tham số Anthropic được hỗ trợ: `model, messages, system, max_tokens, stream, temperature [0,2], tools, tool_choice, top_p, metadata, service_tier`; **bị bỏ qua lặng lẽ**: `top_k, stop_sequences, mcp_servers, context_management, container` *(tài liệu)* và `output_config` *(đo: trả prose thay vì JSON)*.
- Tham số OpenAI: `max_completion_tokens` (mới) / `max_tokens` (cũ), `temperature` mặc định 1, `top_p` mặc định 0,95, `tools`, `response_format`, `reasoning_split`, `thinking`, `stream_options.include_usage`, `service_tier` *(tài liệu)*.

## 3. Token Plan — cửa sổ quota và giới hạn

| | Giá trị |
|---|---|
| Gói *(tài liệu)* | Plus $22 · Max $55 · Ultra $132 / tháng; phủ "toàn bộ dòng M3 / M2.7 / image / speech"; **không liệt kê embedding** |
| Cửa sổ *(đo 12:36)* | `model_name: general`: cửa sổ **5 giờ** đang chạy 12:00–17:00 VN, còn **99%**; cửa sổ **tuần** 2026-08-31 07:00 → 2026-09-07 07:00 VN, còn **86%**. Các trường `*_total_count`/`*_usage_count` = 0 (không lộ tổng), chỉ có `*_remaining_percent` và `*_status` |
| Hết quota *(tài liệu)* | chờ cửa sổ reset, hoặc Credits đã mua, hoặc nâng gói, hoặc chuyển khoá pay-as-you-go. Quota không dùng **không cộng dồn** sang chu kỳ sau |
| Throttle *(tài liệu)* | "có thể bị chặn khi vượt; thường reset trong ~1 phút, siết hơn giờ cao điểm"; song song "≈ 3–4 agent" (Plus) → "6–7" (Ultra) |
| 🔴 Phạm vi dùng *(tài liệu)* | Token Plan "**thiết kế cho cá nhân, dùng tương tác**; khuyến nghị pay-as-you-go cho môi trường production". Chủ dự án chấp nhận dùng cho giai đoạn dev/test; khi web chatbot mở công khai phải đổi sang Standard API Key — module chỉ đổi biến môi trường |
| Tiêu hao *(đo)* | ≈45 lời gọi hôm nay (≈120k token vào, ≈10k ra) làm cửa sổ 5 giờ tụt **≤ 1%** — tổng cửa sổ chưa suy ra được, *chưa kiểm* |

Giá **pay-as-you-go** để quy đổi chi phí *(tài liệu pricing-paygo, 2026-09-06)*: M3 tiêu chuẩn ≤ 512K prompt: **$0,30 / 1M vào · $1,20 / 1M ra · $0,06 / 1M đọc cache** (đã gồm "giảm 50% vĩnh viễn"); > 512K gấp đôi; `service_tier: priority` ×1,5. Rate limit pay-go M3: **200 RPM · 10M TPM** *(tài liệu rate-limits)*. Không có Batch API, không giảm giá theo lô *(tài liệu)*.

## 4. Tokenizer tiếng Việt *(đo)*

20 bài thật trong kho (`tiêu đề + 3.000 ký tự đầu thân bài`, gửi `max_tokens: 1` rồi đọc `usage.prompt_tokens`): **56.097 ký tự / 34.647 token = 1,62 ký tự/token**, dải 1,47–1,73 theo bài. ⇒ một bài cắt trần 3.000 ký tự ≈ **1.850 token**; trần 4.000 ≈ 2.450 token. Con số này **thay** ước lượng 2,5–3,5 ký tự/token ghi ở roadmap sáng 2026-09-06.

## 5. Đầu ra có cấu trúc — thứ gì tin được *(đo, mẫu nhỏ)*

| Cách | Giao diện | Thinking | Kết quả |
|---|---|---|---|
| `tool_choice: {"type":"tool","name":…}` (ép gọi công cụ) | Anthropic | adaptive | **5/5** trả `tool_use` với `input` đúng khoá (2 bài thật + 3 lời gọi qua SDK) |
| ép công cụ | Anthropic | disabled | **1/2** — một lần trả JSON dạng **text**, `stop_reason: end_turn` |
| ép công cụ (`tool_choice.function`) | OpenAI | disabled | **0/3** — trả văn xuôi/JSON text, không `tool_calls` |
| ép công cụ | OpenAI | mặc định (bật) | 1/1 `tool_calls` |
| `response_format: json_schema` | OpenAI | disabled | JSON hợp lệ nhưng **không đúng schema** (thiếu `confidence`/`summary_ai`, thêm `note`) |
| `response_format: json_schema` | OpenAI | adaptive | JSON **không hợp lệ** (bọc ```json, khoá tự đặt) |
| `output_config.format` | Anthropic | — | **bị bỏ qua**, trả markdown |

Kết luận vận hành: **giao diện Anthropic + ép công cụ + thinking adaptive**, rồi **kiểm bằng Pydantic** (enum cho `group`/`sub`), có đường sửa: `end_turn` kèm text JSON ⇒ parse text; không hợp lệ ⇒ gọi lại một lần. Quirk *(đo)*: khi ép công cụ, đôi lúc có block text thừa `"<tool_call>\n"` đứng trước `tool_use` — bỏ qua block text khi đọc kết quả.

## 6. Prompt caching *(đo + tài liệu)*

- **Tự động** cho M3: prefix ≥ 512 token, thứ tự `tools → system → messages`, ghi cache miễn phí, đọc giá $0,06/M *(tài liệu)*. Đo qua SDK với system ≈ 2,8k token: lượt 1 `input 3.030 / cache_read None`; lượt 2–3 **`input 214 / cache_read 2.816`** — cache ăn ngay lượt kế.
- `cache_control` tường minh trên M3: **được nhận nhưng vô hiệu** (`cache_read` đứng ở 128, `cache_creation 0`) — tài liệu: tường minh chỉ cho M2.x. Không cần đặt.
- Luôn thấy `cache_read_input_tokens: 128` / `cached_tokens: 128` ngay cả lời gọi đầu — khả năng là khuôn nội bộ của MiniMax; không tính là cache của mình.
- Trường usage: Anthropic `cache_read_input_tokens`, `cache_creation_input_tokens`, `output_tokens_details.thinking_tokens` (khi có); OpenAI `prompt_tokens_details.cached_tokens`, `completion_tokens_details.reasoning_tokens`.

## 7. Chi phí và độ trễ một bài phân loại *(đo trên 2 bài thật, prompt taxonomy 20 sub + bài 3.000 ký tự, ép công cụ, giao diện Anthropic)*

| Thinking | Token vào | Token ra | Độ trễ |
|---|---:|---:|---:|
| disabled | 2.803 · 2.974 | 218 · 363 | 2,9 · 3,5 s |
| adaptive | 2.816 · 2.987 | 691 · 1.267 (thinking 938) | 7,7 · 12,2 s |

Quy giá pay-go (adaptive, phần system ≈ 1,3k token đã cache): ≈ 1,85k vào mới × $0,30/M + 1,3k đọc cache × $0,06/M + ≈ 1,0k ra × $1,20/M ≈ **$0,0018 / bài (≈ 0,2 xu)** ⇒ ~350 bài/ngày ≈ **$0,65/ngày**, kho 7.956 bài ≈ **$14** một lần. Dưới Token Plan tính theo quota cửa sổ, không theo tiền. Tuần tự 350 bài × ~10 s ≈ **1 giờ/ngày**; song song 2–3 luồng nằm trong "3–4 agent" của gói.

⚠️ Cùng một bài, hai chế độ thinking cho **nhóm khác nhau** (3e vs 1c cho bài giá vàng SJC) — độ ổn định phải đo bằng bộ đánh giá gán tay trước khi bật lưới (lát 9).

## 8. Embedding — `embo-01` *(đo + tài liệu bên thứ ba)*

- `POST /v1/embeddings` body **không theo chuẩn OpenAI**: `{"model":"embo-01","texts":[…],"type":"db"|"query"}`; gửi `input` ⇒ `base_resp 2013 invalid params`.
- Với body đúng: HTTP 200 nhưng `base_resp.status_code 1002 "rate limit exceeded(RPM)"` **hai lần cách 65 giây** ⇒ nhiều khả năng **Token Plan không bao gồm embedding** (tài liệu gói không liệt kê) — *chưa kiểm* với khoá pay-go.
- Số chiều **1536** theo tài liệu thư viện bên thứ ba (LangChain, Spring AI) — *chưa kiểm*; **không khớp** quyết định `halfvec(768)` ở [news-pipeline §9.5](../../20-design/news-pipeline.md).

## 9. Lỗi *(tài liệu errorcode + đo)*

Endpoint gốc trả **HTTP 200 kèm `base_resp.status_code`**: `1000` lỗi lạ · `1001` timeout · `1002` rate limit (thử lại được) · `1004` không được phép · `1008` hết số dư · `1027` đầu ra nhạy cảm · `1039` vượt trần token · `2013` tham số sai · `2049` khoá sai. Giao diện tương thích trả HTTP thật (đo `401` với body `{"type":"error","error":{"type":"authorized_error",…}}`); hình dạng `429` khi throttle *chưa kiểm* — code phải xử lý cả hai kiểu.

## 10. SDK *(đo)*

`anthropic` **1.4.0** (PyPI 2026-09-06) với `Anthropic(api_key=<LLM_API>, base_url="https://api.minimax.io/anthropic")`: `messages.create` (thinking + tools + `tool_choice`) chạy đúng; vòng tool 2 lượt echo `response.content` (gồm `thinking`) chạy đúng; **`client.beta.messages.tool_runner` với `@beta_tool` chạy đúng** trên MiniMax. SDK 1.x dùng `httpx2`, sống chung với `httpx` của repo. Chưa đo: streaming qua SDK, `messages.count_tokens` (khả năng không có — dùng tỷ lệ §4 để ước).

## 11. Bẫy đã gặp trong 40 phút đo

1. `max_tokens` nhỏ (60–120) trên giao diện OpenAI ⇒ phần `<think>` ăn hết ngân sách, `finish_reason: length`, không có nội dung thật — đặt `max_completion_tokens` ≥ 1.500 cho phân loại.
2. `json_schema` không phải cưỡng chế schema (§5) — đừng tin.
3. Tắt thinking làm ép công cụ mất hiệu lực từng lúc (§5).
4. `output_config` và `cache_control` không báo lỗi khi vô hiệu — "gọi thành công" không có nghĩa là tính năng chạy (CLAUDE.md §1.3).
5. Embedding trả 200 nhưng lỗi nằm trong `base_resp` — kiểm `base_resp` trước khi đọc `vectors`.
