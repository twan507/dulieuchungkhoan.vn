# Sổ thực thi — lát 10, tầng ngữ nghĩa

Nhánh `feat/semantic-layer`. Ghi theo mốc, dán output thật.

---

## Task 0 — spike `tool_runner` × MiniMax ✅ ĐẠT (2026-09-07)

Đóng hai giả định rủi ro nhất của spec (§2.4 A1, A2) **trước khi xây gì**.

Chạy: `PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1 uv run --project backend python <scratchpad>/spike_tool_runner.py` (tiền cảnh).

Output nguyên văn:

```
SCHEMA: {"additionalProperties": false, "properties": {"ma": {"title": "Ma", "type": "string"}, "ngay": {"anyOf": [{"type": "string"}, {"type": "null"}], "default": null, "title": "Ngay"}}, "required": ["ma"], "type": "object"}
STOP: tool_use | usage: BetaUsage(cache_creation=None, cache_creation_input_tokens=0, cache_read_input_tokens=128, fallback_credit=None, inference_geo=None, input_tokens=420, iterations=None, output_tokens=68, output_tokens_details=BetaOutputTokensDetails(thinking_tokens=21), server_tool_use=None, service_tier='standard', speed=None)
TOOL RESULT: {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "call_1f79ebbab1d4437a9ba3373b", "content": "{\"ma\": \"HPG\", \"ngay\": \"2026-09-03\", \"gia\": \"21.600 đ\"}"}]}
STOP: end_turn | usage: BetaUsage(cache_creation=None, cache_creation_input_tokens=0, cache_read_input_tokens=512, fallback_credit=None, inference_geo=None, input_tokens=149, iterations=None, output_tokens=48, output_tokens_details=BetaOutputTokensDetails(thinking_tokens=22), server_tool_use=None, service_tier='standard', speed=None)
TEXT: Giá đóng cửa HPG phiên 03/09/2026: **21.600 đ**.
SO LAN TOOL CHAY THAT: 1
```

**Bốn điều đóng lại từ output này:**

| # | Trước spike | Sau spike |
|---|---|---|
| A1 | `beta.messages.parse` luôn gắn header `anthropic-beta: structured-outputs-2025-12-15`, không tắt được — MiniMax có thể trả 400 | **Không sao.** Vòng công cụ chạy trọn, không lỗi header. Giữ nguyên thiết kế dùng `tool_runner` |
| A2 | Schema `@beta_tool` cho tham số tuỳ chọn sinh `anyOf: [string, null]`; MiniMax chưa từng đo với hình dạng này | **Nuốt được.** Model gọi công cụ đúng schema, điền `ngay` đúng ngày hỏi |
| G8 | Lo tham số tuỳ chọn rơi vào `required` | `required: ["ma"]` — **chỉ tham số không có mặc định**. Luật "mọi tham số tuỳ chọn phải có default" là đủ |
| G6 | Gọi `generate_tool_call_response()` rồi `append_messages()` làm mọi function chạy **hai lần** | **`SO LAN TOOL CHAY THAT: 1`** — không gọi `append_messages`, để `__run__` tự lấy từ cache là đúng cách |

**Số đo phụ:** cache tự động trúng ngay lượt đầu (`cache_read_input_tokens: 128` rồi `512`); một vòng hỏi–gọi–trả với prompt nhỏ tốn 420 + 149 token vào, 68 + 48 token ra. Prompt thật của lát nặng hơn nhiều vì mang trọn L1 (~37,8k token/request) — số thật đo ở Task 14.
