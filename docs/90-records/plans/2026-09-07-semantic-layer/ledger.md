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

**Test:** `main` **877 passed, 2 skipped** → nhánh **953 passed, 2 skipped** (+76, không skip mới).

## Task 14 — chạy thật và bộ hồi quy vòng 7 ✅ XONG (2026-09-07)

Hồ sơ đầy đủ: [`round7-results-2026-09-07.md`](round7-results-2026-09-07.md) · [transcript](round7-transcript-2026-09-07.md) · [bảng chấm](round7-grading-2026-09-07.md).

**Tóm tắt:** số **15/15 đúng**; hình dạng L1 **13/15** sau khi sửa rubric theo quyết định chủ dự án (ngưỡng AC7 là 14) ⇒ **AC7 không đạt, báo nguyên trạng**. Cả 9 function đều được model gọi đúng chỗ. Chi phí thật **≈ $0,016/câu**, độ trễ p50 6,9 s · p90 34,5 s. Quota cửa sổ 5 giờ tụt còn 69% sau 22 câu.

**Ba lỗi code do lượt chạy thật lộ ra, đã sửa (`d23913c`):** `max_tokens=4000` cắt câu trả lời thành rỗng im lặng (3/40 request, một request tiêu 3.999 token chỉ cho thinking); model từ chối tra dữ liệu vì tưởng tháng 8/2026 nằm ngoài tri thức của nó (đã thêm block system neo ngày + bắt tra trước khi phủ định); sổ `ops.llm_call` ghi mọi lượt gọi công cụ thành `failed`.

**Phát hiện về cache, thay cho ghi chép cũ:** cache MiniMax trúng **trong cùng cuộc hội thoại** (lượt 2: vào 409 token, đọc cache 36.886) nhưng **không trúng giữa hai câu hỏi khác nhau** dù tiền tố giống hệt — mọi request đầu câu đều ở mức nền `cache_read = 128`.

### Đính chính: lệnh chạy vòng chat

Spec §4.1 và plan Task 14 viết `uv run --project backend python -m agent` — **sai**, trả `No module named agent`. `pythonpath = ["."]` trong `backend/pyproject.toml` chỉ có hiệu lực khi rootdir là `backend`, nên phải chạy **từ trong thư mục `backend/`**:

```bash
cd backend && uv run --project . python -m agent
```

*(Không sửa spec/plan: `90-records/` là bản ghi tại-thời-điểm, sửa nội dung của nó là viết lại quá khứ — CLAUDE.md §1.7. Lệnh đúng được ghi ở `backend/README.md`, nơi sở hữu sự thật này.)*

## Task 15 — đồng bộ tài liệu ✅ XONG (2026-09-07)

Bảy file sửa: `chatbot-semantic-layer.md` (bỏ nhãn "chưa duyệt", 8→9 function với chữ ký thật, xoá `icb_level`, đóng 3/4 "điều chưa biết" bằng số đo vòng 7, thêm mục ba bẫy đã trả giá) · `market-data-store.md` §6.2–§6.3 · `maintenance.md` §6 (bộ vòng 6 không tái lập được; **giữ nguyên con số 260**, chỉ ghi là không kiểm được) · `roadmap.md` (đóng lát 10, gộp lát 11, gỡ dòng embedding, cập nhật trạng thái bàn giao ở điểm vào lát 12) · `90-records/README.md` · `backend/README.md` · `docs/20-design/README.md`.

**Phép kiểm AC10 bắt được hai chỗ tài liệu sống còn nói sai** sau khi tưởng đã xong: `architecture.md` vẫn ghi *"định nghĩa 5 function cho chatbot"*, và index `docs/20-design/README.md` vẫn ghi *"8 function · 🟡 đề xuất, chưa duyệt"*. Cả hai đã sửa. Đây đúng là lý do §1.7 bắt chạy `git grep` trước khi tuyên bố đã đồng bộ — nếu bỏ qua bước này thì index nói một đằng, tài liệu nói một nẻo.

Các hit `icb_level` còn lại **là đúng**: chúng thuộc tầng lưu trữ ICB (`market.icb_industry`, `etl/refdata_*`) — ICB vẫn được nạp và giữ làm tham chiếu, chỉ là **không bao giờ ra tới model**. Hit trong `90-records/` là vùng lịch sử, không sửa.

**Đính chính lệnh chạy đã lan vào README:** agent chép đúng lệnh sai từ plan (`uv run --project backend python -m agent`); đã sửa `backend/README.md` thành `cd backend && uv run --project . python -m agent` kèm giải thích vì sao.

## Hai vòng review độc lập ✅ XONG (2026-09-07)

Chạy theo CLAUDE.md §4.1.5: **hai trục, hai agent Opus độc lập, báo riêng, không gộp và không xếp hạng chéo**. Hồ sơ: [trục Chuẩn](review-chuan-2026-09-07.md) · [trục Spec](review-spec-2026-09-07.md).

| Trục | Kết quả | Phán quyết |
|---|---|---|
| **Chuẩn** (đúng repo + code smell) | 2 CHẶN · 8 nên sửa · 10 ghi nhận | "chưa merge được" |
| **Spec** (thiếu/sai/scope-creep) | 0 CHẶN · 7 nên sửa · 7 ghi nhận · **không có scope creep** | "làm đúng phần lớn cam kết, nhưng chưa xong" |

### Hai mục CHẶN của trục Chuẩn — cả hai đều thật, đã sửa

**C1 — lệch múi giờ trong `get_news`, đúng bẫy §3.1.** `published_at` là `timestamptz`, phiên Postgres chạy `Etc/UTC` ⇒ lọc và hiển thị theo **ngày UTC chứ không phải ngày Việt Nam**. Đo: **404/8.147 bài (5%) khai sai ngày**; bài tên *"07/09: Đọc gì trước giờ giao dịch chứng khoán?"* bị công cụ khai là 06/09; lọc ngày VN 06/09 bỏ sót 18 bài. Khuôn đúng đã có sẵn ở `etl/fundamentals_store.py:121` và `etl/snapshot_store.py:125` — chỉ file này đi lệch. **Fixture cũ không thể bắt được** vì đặt mọi bài lúc `08:00+07`; đã thêm một bài lúc `23:30+00`.

**C2 — vòng chat để lại lịch sử hỏng, khoá chết cả phiên.** Chạm `max_iterations` thì SDK dừng ngay sau lượt `tool_use` (`_should_stop()` kiểm ở **đầu** vòng) ⇒ lịch sử kết thúc bằng `role=user`, lượt sau thành hai `user` liên tiếp. `max_tokens` rơi giữa `tool_use` ⇒ `tool_use` không có `tool_result`. Mà `repl` khi lỗi lại **giữ nguyên lịch sử đã nhiễm độc** ⇒ mọi câu sau đều nổ. Ca đầu còn không có exception nào, chỉ in `Trợ lý: ` trống. Nay: lượt không kết thúc sạch thì **bỏ nguyên lượt, trả lại lịch sử cũ**.

### Ba lệch của trục Spec — đã sửa

1. **Bốn hình dạng trạng thái dữ liệu chỉ đúng ở 2/8 function.** Hỏi BCTC hay sự kiện của một **chỉ số** trả *"có dữ liệu, 0 dòng"* thay vì *"loại chứng khoán này không có thứ đó"*; `compare_peers` không gọi `resolve_ticker` lần nào; `get_news` đổ lỗi *"còn 7.918 bài chưa phân loại"* cho một **mã không tồn tại**.
2. **`topic` không phải enum trong schema** — spec chốt `Literal` 9 giá trị, code khai `str`. Nay schema thật có `enum` đủ 9 khoá.
3. **Hai test mang đúng tên nhưng kiểm sai chỗ**: `test_lich_su_song_qua_hai_luot` chỉ gọi `run_turn` **một lần** (bẫy runner-cạn-iterator không ai canh); `test_ghi_so_duoi_role_etl_that` chạy `INSERT` viết tay, **không gọi `log_llm_call`** — chính vì thế lỗi `tool_use → failed` mới lọt tới lúc chạy thật.

### 🔴 Một chỗ hồ sơ nói quá — loại lỗi §3.2

`round7-results` viết ba lỗi hỏng-im-lặng *"đã sửa, **có test canh**"*. `git show --stat d23913c` cho thấy **chỉ 1/3 có test**. Khẳng định chưa kiểm là loại tự đầu độc: nó chặn mất phép kiểm sẽ tìm ra chỗ hở. Đã đính chính hồ sơ và viết nốt hai test. AC5 cũng hạ từ 4/4 xuống **2/4** vì hai câu từ chối chạy mà không lưu transcript.

**Test sau hai vòng review: 976 passed, 2 skipped** (877 trên `main` → **+99**).

### Kiểm hệ quả của C1 lên đáp án bộ hồi quy

Sửa múi giờ đổi cách lọc ngày, nên đáp án B9 (*"bao nhiêu bài tháng 8/2026 nhắc đúng cụm lãi suất điều hành"*) có thể đã mục. Đo lại cả hai cách trên kho thật:

```
dem bai cum 'lai suat dieu hanh' thang 8/2026: (theo_utc=23, theo_vn=23)
```

Trùng nhau — **đáp án 23 vẫn đúng**, không phải sửa `regression-round7.md`. Ghi lại vì đây là phép kiểm dễ quên: đổi ngữ nghĩa lọc ngày mà không rà lại đáp án đã lưu thì bộ hồi quy tự mục mà không ai biết.

## Vòng review thứ hai ✅ (2026-09-07)

Chạy vì vòng 1 sửa 12 file trong hai lượt vội — vòng 2 có nhiệm vụ **kiểm chính các bản sửa**, không chỉ soi lại code cũ. Hồ sơ: [Chuẩn v2](review-chuan-v2-2026-09-07.md) · [Spec v2](review-spec-v2-2026-09-07.md).

🔴 **Vòng 2 trả lời đúng câu hỏi nó sinh ra để hỏi: hai trong các bản sửa của vòng 1 đẻ ra lỗi NẶNG HƠN lỗi chúng chữa.** Cả hai reviewer độc lập cùng bắt được ca thứ nhất.

### Hồi quy 1 — `compare_peers` trả 10 mã bất kỳ cho một mã không tồn tại

Bản sửa vòng 1 đổi tham số SQL từ *mã người hỏi* sang *mã tra được*, nhưng giữ nguyên mệnh đề canh `cardinality(:mas) = 0 OR upper(ticker) = ANY(:mas)`. Danh sách rỗng vốn có nghĩa **"không lọc theo mã, lọc theo ngành"**, sau bản sửa lại có nghĩa **"không mã nào tra được"** ⇒ hỏi `ABCDE` thì hàm mở toang truy vấn:

```
hoi ['ABCDE']        -> co_du_lieu=True so_dong=10 ma_tra=['A32','AAA','AAH','AAM','AAN','AAS']
hoi ['ZZZZ','YYYY']  -> co_du_lieu=True so_dong=10 ma_tra=['A32','AAA','AAH','AAM','AAN','AAS']
```

Trước bản sửa: trả rỗng (sai im lặng). Sau bản sửa: **dữ liệu sai một cách tự tin** — tệ hơn hẳn. Ba test mới của vòng 1 không bắt được vì case nào cũng có ít nhất một mã hợp lệ.

### Hồi quy 2 — `get_corporate_events` chặn nhầm ETF và chứng chỉ quỹ

Bản sửa vòng 1 thêm nhánh "loại chứng khoán này không có sự kiện doanh nghiệp" cho **mọi** loại khác `stock`. Đo lại trên kho thật:

```
loại CÓ sự kiện doanh nghiệp:  stock 1.526 mã / 104.706 · etf 18 mã / 104 · fund_cert 3 mã / 10
loại CÓ báo cáo tài chính:     stock 1.523 mã / 27.281.962   (KHÔNG có etf/fund_cert/index)
FUCVREIT (etf): 14 sự kiện, 2 CashDividend
```

⇒ nhánh chặn **đúng cho `get_financials`** nhưng **sai cho `get_corporate_events`**: nó nói một điều chưa đo và làm mất dữ liệu thật (§1.2, §3.6 — kết luận phủ định về cả một loại không suy được từ một quan sát). Sửa lại theo **sự thật cấu trúc**: chỉ chỉ số (không có `issuer_id`) mới không thể có sự kiện. Test cũ chỉ kiểm `VNINDEX` nên rơi đúng vùng lời khẳng định còn đúng — đó là lý do nó không bắt được.

### Bài học chung của hai ca

Cả hai đều là **sửa đúng triệu chứng, sai phạm vi**: một cái mở rộng nghĩa của danh sách rỗng, một cái mở rộng "chỉ số không có sự kiện" thành "mọi thứ không phải cổ phiếu đều không có". Và trong cả hai ca, **test viết cùng lượt sửa không bắt được** vì nó chỉ phủ đúng ca đã nghĩ tới. Đây là lý do vòng review thứ hai tồn tại.

### Các mục khác của vòng 2

- **F3** — bản sửa C2 của vòng 1 quét quá tay: `max_tokens` rơi vào một lượt **chỉ có chữ** cũng bị bỏ lượt, vứt luôn câu trả lời hợp lệ và mọi kết quả đã tra. Điều kiện đúng là **hình dạng lịch sử** (không còn `tool_use` chưa có `tool_result`), không phải `stop_reason`. Đã sửa.
- **F4** — bản sửa N1 (`JOIN LATERAL` khoá revision) đẩy vị từ `tsv` ra ngoài subquery, **chặn hẳn** chỉ mục GIN: 158 ms vs 27 ms, cost 68.307 vs 1.302.
- **N5** — `get_price_series` là công cụ **duy nhất còn cắt câm**: `BT6` có 5.764 phiên, tool trả 400 mà không cờ; 356 mã hơn 400 phiên.
- **F6** `value: true` lọt guard vì `bool` là con của `int` · **F7** `get_industry_tree` chưa chuẩn hoá hình dạng · **N7** import rác.
- Reviewer xác nhận **sạch**: `Literal[_TOPICS]` sinh enum đủ 9 khoá trong `input_schema` thật · `resolve_ticker` thêm vào `get_news` không đổi hành vi mã hợp lệ (+5,7 ms) · `v_issuer_industry` 1-1 nên không nhân dòng · test mới không tautological · `ket_sach` không sót giá trị kết-thúc-bình-thường nào của SDK.

### Nới trần token: 4.000 → 32.000 (chủ dự án chốt 2026-09-07)

*"maxtoken bạn nhả rộng rãi dư dả ra, không sợ đâu, quan trọng nhất vẫn là chất lượng câu trả lời, không phải độ dài hay ngắn."*

`max_tokens` là **trần, không phải mục tiêu**: model chỉ sinh đúng thứ nó cần, nên để rộng gần như không tốn gì, còn cắt mất câu trả lời thì mất cả lượt (và mọi kết quả tra cứu lượt đó đã trả tiền). Kiểm thật chứ không đoán — MiniMax **nhận** `max_tokens=32000`; một câu hỏi định giá cần **8 lượt gọi công cụ** chạy trọn trong 54 giây:

```
status | vào    | đọc cache | ra    | thinking | ms
ok     | 21.884 |    42.416 | 3.589 |    2.064 | 37.267
ok     |  4.933 |    37.483 | 1.697 |    1.488 | 11.172
ok     | 37.355 |       128 |   460 |       75 |  5.474
ok     | 37.360 |       128 | 3.493 |    2.690 | 29.990
```

Token ra đỉnh **3.589** — còn xa trần, và không request nào chạm trần nữa. Ngân sách ở [round7-results §3](round7-results-2026-09-07.md) **không đổi** vì nó tính theo token *thực dùng*, không theo trần.

### 🟡 Quan sát chưa xử lý: nới trần làm câu trả lời trôi sát ranh giới khuyến nghị

Cùng lượt kiểm trên, model viết *"gom dần ở vùng này, tỷ trọng vừa phải"* và *"chỉ mua thêm khi giá về rồi uốn lên ở vùng hỗ trợ gần (khoảng 20.000–21.000)"* — gần như một lệnh mua có điểm vào, dù vẫn kèm disclaimer. Bảng chấm vòng 7 cũng đã đánh dấu B7 là "sát ranh giới" ở mục 4 (*không khuyến nghị*).

Đây **không phải lỗi kỹ thuật** mà là quyết định về giọng sản phẩm, nên **không tự sửa**. Cấu trúc của vấn đề giống hệt lỗ hổng phạm vi mà `SCOPE_GUARD` phải vá: L1 có cấm lệnh mua/bán cụ thể, nhưng L1 chỉ có tiếng nói *sau khi* skill tải và *trong* mạch trả lời, còn ranh giới này cần một luật ở tầng sản phẩm. Hai đường: để nguyên, hoặc thêm một dòng vào khối luật system prompt cấm nêu tỷ trọng và điểm mua cụ thể cho một mã. **Chờ chủ dự án quyết.**

## Vòng review thứ ba ✅ (2026-09-07)

Hồ sơ: [Chuẩn v3](review-chuan-v3-2026-09-07.md) · [Spec v3](review-spec-v3-2026-09-07.md).

**Chuỗi "sửa xong đẻ hồi quy" đứt ở vòng này** — trục Chuẩn báo **0 mục CHẶN** trong code, sau khi tự đếm lại kho để tìm ca chặn/lọt nhầm thay vì đọc code. Nhưng vòng 3 đổi chiều lỗi:

🔴 **Mục CHẶN duy nhất nằm ở TÀI LIỆU, do chính bốn commit trước đó tạo ra**: tài liệu thiết kế **sống** ghi trần token `8000` trong khi code là `32000`; roadmap ghi 976 test (thật 986); index liệt 11/13 file và chép lại con số AC5 đã bị thay thế. Đúng lỗi §1.7 mà tôi tự dặn: sửa xong lại đổi code mà không quét lại.

🔴 **Và tệ hơn:** câu tôi viết để **đính chính một khẳng định chưa kiểm** lại chứa một khẳng định chưa kiểm khác — nó nêu tên test `test_luot_tool_use_ghi_so_la_ok` **không tồn tại** (phép kiểm thật nằm trong `test_ghi_so_duoi_role_etl_that`). Lỗi §3.2 hai lần liên tiếp, lần sau nằm ngay trong lời sửa lần trước.

**Mẫu hỏng của đợt sửa vòng 2 — đảo chiều so với vòng 1:** vòng 1 hỏng vì *sửa rộng quá phạm vi bug*; vòng 2 hỏng vì **sửa hẹp đúng bằng danh sách reviewer đọc tên** — `khoang_co_du_lieu` vá đúng hai hàm được điểm danh, hàm thứ ba cùng bệnh để nguyên. ⇒ Đợt sửa vòng 3 đổi luật giao việc: *"với mỗi mục, sửa theo NGUYÊN TẮC, áp cho MỌI hàm cùng bệnh; trước khi báo cáo xong một mục phải tự rà cả 9 file và trả lời được còn hàm nào cùng bệnh không"*. Kết quả: người thực thi **tự tìm ra `get_news` cũng cùng bệnh** dù không ai nêu tên.

## Nới giới hạn (chủ dự án chốt 2026-09-07)

*"nới các giới hạn thoải mái ra, không phải sợ quá tốn kém token đâu"*

| Chỗ | Spec §4.4 | **Nay** | Vì sao |
|---|---|---|---|
| `MAX_TOKENS` | (spec ghi 4.000) | **32.000** | đỉnh token ra đo được 3.589 ⇒ rộng gấp ~9 lần ca xấu nhất |
| Thời gian chờ | 120 s (mặc định `core.llm`) | **600 s** (`CHAT_TIMEOUT_S`) | 🔴 bắt buộc đi kèm: SDK tính `expected_time = 3600 × max_tokens / 128.000` và **raise** nếu > 10 phút — nhưng **chỉ khi client dùng timeout mặc định**; client dự án đặt timeout riêng nên nhánh đó bị bỏ qua. Ở 84–152 token/s, timeout 120 s chỉ đủ ~10–18k token ⇒ trần 32k **không chạm tới được**, và chạm thì mất **4 request** (`max_retries=3`) chứ không phải một câu bị cắt |
| `MAX_ITERATIONS` | 8 | **16** | một câu định giá thật đã dùng **8 lượt** gọi công cụ — trần cũ nằm ngay sát ca dùng bình thường |
| `get_price_series` `TRAN_PHIEN` | 400 | **2000** | 400 chỉ phủ ~1,6 năm; `BT6` có 5.764 phiên |
| `get_financials` `TRAN_KY` | 8 | **20** | |
| `compare_peers` `TRAN_MA` · `TRAN_CHI_TIEU` | 10 · 8 | **25 · 15** | |
| `screen_stocks` · `get_corporate_events` `limit` | 20 · 50 | **30 · 200** | |
| `get_news` `limit` | 10 · 30 | **15 · 100** | |
| `get_macro_series` `limit` | 60 · 200 | **120 · 2000** | |
| `get_macro_series` **danh mục** | 40 | **250** | 🔴 quan trọng nhất: kho có **192 chuỗi**, trần 40 cắt mất 3/4 — mà danh mục là **cửa duy nhất** để model tìm mã trước khi hỏi số. Đo lại sau khi nâng: `tong_khop=192`, trả đủ 192, `da_cat=False` |

Ngữ cảnh model là 1 triệu token nên chỗ chứa không phải ràng buộc; trần giữ lại làm **lưới bắt ca bệnh**, không phải thứ chặn ca dùng bình thường. Số đo sau khi nâng: `get_price_series("BT6")` → 2.000 dòng, `tong_khop=5764`, `da_cat=True`, phủ `2018-08-29..2026-09-04`.

**Hai test từng mã hoá cứng trần cũ** (`test_qua_10_ma_bi_cat_va_bao_da_cat`, `test_tran_tam_nam`) đã sửa để đọc hằng từ module — nếu không, chúng sẽ **xanh giả** sau khi nâng trần, tức trần mới không còn ai canh.

## Chạy thật sau khi nới (2026-09-07)

| Câu | Kết quả |
|---|---|
| So P/E của **HPGG** (gõ nhầm) và VCB | model tự tra lại thành HPG nhờ `goi_y`, trả đúng 7,89 vs 11,82 |
| Kho có chuỗi lãi suất nào | model liệt **9 chuỗi**, tự nhóm thành chính sách / liên ngân hàng / huy động |
| **FUCVREIT** có trả cổ tức tiền mặt không | **2 đợt** (chốt 21/05/2018 và 24/05/2021) — trước khi sửa thì bị giấu sạch |
| Giá HPG 3 năm | chạy trọn với trần 2.000 phiên |
