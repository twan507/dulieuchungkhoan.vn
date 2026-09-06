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

---

## Task 1–13 — dựng tầng ngữ nghĩa ✅ XONG (2026-09-07)

Giao subagent **Sonnet** theo nhóm; test chạm DB phải chạy **tuần tự** vì `conftest` drop/create `dulieu_test` mỗi phiên pytest, hai phiên song song giẫm nhau.

| Task | Ai làm | Kết quả |
|---|---|---|
| 1 — `db.py`, role `dlck_api` | tự làm | 5 test; tạo user `agent_reader`, biến `AGENT_DATABASE_URL` |
| 2 — `format.py`, `labels.py` | subagent | 12 test |
| 3 — `system_prompt.py`, `skills.py` | subagent | 7 test; L1 thật **61.377 ký tự** |
| 4 — `_shared.py`, `load_knowledge_reference` | tự làm | 7 test |
| 5–6 — `get_price_series`, `get_industry_tree` | subagent | 4 + 4 test |
| 7–8 — `get_financials`, `get_corporate_events` | subagent | 5 + 3 test |
| 9–11 — `screen_stocks`, `compare_peers`, `get_macro_series`, `get_news` | subagent | 5 + 6 + 6 test |
| 12 — đăng ký 9 tool, `llm_log` | subagent | 5 test |
| 13 — vòng chat | tự làm | 5 test |

**Bốn lỗi trong chính plan, do người thực thi bắt được:**

1. 🔴 **DB test dựng RỖNG** — plan giả định test tool đọc được dữ liệu thật. Chỉ `market.industry` có sẵn 30 dòng do migration seed. Đã thêm fixture `kho` (`backend/tests/agent/conftest.py`) seed kho thu nhỏ tất định; sửa plan trong cùng lượt.
2. **`:p::jsonb` không được SQLAlchemy nhận là bind param** — lặng lẽ bỏ tham số rồi ném lỗi khó đọc. Phải viết `CAST(:p AS jsonb)`.
3. **`metric_dictionary` có PK `(dictionary, code)`** — join thiếu `dictionary='field_dictionary'` sẽ nhân đôi dòng trên kho thật, vì cùng một `code` tồn tại được ở cả `screener_params`.
4. **Danh sách `sub` trong plan sai**: kho có **21 mã** (nhóm 3 chạy tới `3i`, và `2f` thêm ở migration `0019`), plan viết nhóm 3 chỉ tới `3e` ⇒ sẽ từ chối nhầm nhãn hợp lệ.

Cộng thêm hai ràng buộc lược đồ gặp thật: `asset.asset.calendar ∈ {trading_days, 24x7}`; `asset.price_daily.price_type ∈ {spot, futures, fixing, close}` — và ADR §2.3 cấm trộn loại giá, nên `get_macro_series` chọn đúng một loại rồi khai báo `loai_gia`.

**Test:** `main` **877 passed, 2 skipped** → nhánh **951 passed, 2 skipped** (+74, không skip mới).

## Task 14 — chạy thật và bộ hồi quy vòng 7 ✅ XONG (2026-09-07)

Hồ sơ đầy đủ: [`round7-results-2026-09-07.md`](round7-results-2026-09-07.md) · [transcript](round7-transcript-2026-09-07.md) · [bảng chấm](round7-grading-2026-09-07.md).

**Tóm tắt:** số **15/15 đúng**; hình dạng L1 **12/15** (ngưỡng AC7 là 14) ⇒ **AC7 không đạt, báo nguyên trạng**. Cả 9 function đều được model gọi đúng chỗ. Chi phí thật **≈ $0,016/câu**, độ trễ p50 6,9 s · p90 34,5 s. Quota cửa sổ 5 giờ tụt còn 69% sau 22 câu.

**Ba lỗi code do lượt chạy thật lộ ra, đã sửa (`d23913c`):** `max_tokens=4000` cắt câu trả lời thành rỗng im lặng (3/40 request, một request tiêu 3.999 token chỉ cho thinking); model từ chối tra dữ liệu vì tưởng tháng 8/2026 nằm ngoài tri thức của nó (đã thêm block system neo ngày + bắt tra trước khi phủ định); sổ `ops.llm_call` ghi mọi lượt gọi công cụ thành `failed`.

**Phát hiện về cache, thay cho ghi chép cũ:** cache MiniMax trúng **trong cùng cuộc hội thoại** (lượt 2: vào 409 token, đọc cache 36.886) nhưng **không trúng giữa hai câu hỏi khác nhau** dù tiền tố giống hệt — mọi request đầu câu đều ở mức nền `cache_read = 128`.
