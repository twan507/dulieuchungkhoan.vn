# Spec — Lát 10: tầng ngữ nghĩa, nối kho ↔ hai skill bằng function calling

**Ngày:** 2026-09-07 · **Nhánh:** `feat/semantic-layer` · **Trạng thái:** ✅ **chốt** sau một lượt review độc lập bằng Opus (6 mục CHẶN + 16 mục NÊN SỬA đã đóng — xem §11). Chủ dự án uỷ quyền tự chốt.

Lát 10 dựng phần **ở giữa** hai đầu đã có: kho dữ liệu (đã đầy) và hai skill dạng prompt (đã test 6 vòng). Phần giữa này là [`chatbot-semantic-layer.md`](../../../20-design/chatbot-semantic-layer.md) — **tài liệu duy nhất trong kho chưa qua kiểm chứng thực tế**.

---

## 0. Câu hỏi lát này phải trả lời

| Chưa biết (tài liệu tự khai) | Lát 10 đóng bằng |
|---|---|
| **Skill có chịu được function calling không** (6 vòng test đều chạy *không* có công cụ) | bộ hồi quy §5 chạy **có** function, chấm cả số lẫn hình dạng |
| **Ai gọi function trước — skill hay bot** | quyết định bằng thiết kế: L1 nằm trong `system`, đứng trước mọi `tool_result`, không bao giờ đến sau |
| **Chi phí mỗi câu** | đo thật từ `ops.llm_call`, ghi ledger |
| ~~Đơn vị của các mã chỉ tiêu~~ | đã giải trước lát này |

## 1. Phạm vi

**Trong phạm vi**

1. 8 function dữ liệu + 1 function đọc tri thức L2, chạy dưới role `dlck_api`.
2. Vòng chat nhiều lượt trong terminal (`python -m agent`).
3. System prompt gác phạm vi lĩnh vực (vá lỗ hổng đo được ở vòng 5).
4. Nạp skill: L1 trọn vào `system`; L2 theo nhu cầu qua function.
5. **Dựng lại bộ hồi quy (vòng 7) và lưu vào repo** — bộ vòng 6 đã mất (§2.3).
6. Test seam theo TDD, gồm test dưới đúng quyền production.
7. Cập nhật tài liệu bị lát này làm cho sai (§9).

**Ngoài phạm vi — có lý do**

| Việc | Loại | Lý do |
|---|---|---|
| Endpoint HTTP / web chat | đã có đường khác | chủ dự án chốt: lát 10 chỉ terminal |
| Streaming | đã kiểm — chưa đo | `stream` chưa từng đo với MiniMax; việc của lát API |
| Embedding / tìm kiếm khái niệm | có chủ đích | chủ dự án chốt để sau; dùng `tsvector` + trigram đã có. **`roadmap.md` dòng 145 nói "dời sang lát 10" — phải gỡ (§9)** |
| Chạy lưới phân loại 7.900 bài chưa nhãn | có chủ đích | sẽ xoá sạch và backfill lại khi lên prod |
| Ba ô thiếu trong cây ngành | có chủ đích | đổi cây kéo theo gán lại ~1.500 mã — chỉ chủ dự án quyết |
| Nạp 83 chỉ tiêu `GetScreenerParameters` | đã có đường khác | việc của lát ETL |
| Đăng ký task Scheduler | có chủ đích | lát 10 không có job tự động |

**Lát 11 gộp vào lát 10.** `roadmap.md` dòng 150 xếp *"lát 11 — test vòng 6 có function calling"* thành lát riêng. Không tách được nữa: bộ vòng 6 đã mất, mà lát 10 **phải** có bộ hồi quy để tự nghiệm thu. Vậy §5 chính là lát 11. Roadmap phải ghi rõ điều này (§9); số hiệu các lát sau **giữ nguyên** (12, 13, 14) để không phá tham chiếu chéo trong repo.

## 2. Dữ kiện đã đo và giả định *(CLAUDE.md §4.8 bước 0)*

Mọi số đo **2026-09-06/07** trên kho dev đang chạy.

### 2.1 Kho dữ liệu

| # | Dữ kiện | Hệ quả thiết kế |
|---|---|---|
| F1 | `market.price_daily` 1.115.219 dòng, **chỉ cổ phiếu** (1.523 mã, 2002-04-18 → 2026-09-04). `close_adj`/`close_raw` đầy đủ 100 %. **`total_trading` và `total_trading_value` NULL 100 %** (`count()` = 0 trên cả bảng) | `get_price_series` **không** trả khối lượng, và nói rõ là kho không có |
| F2 | Phiên 2026-09-04 chỉ có **335 mã** (lượt chạy dở); 2026-09-03 có 1.521 | mốc kiểm chứng giá dùng **2026-09-03** |
| F3 | 🔴 **VN-Index không có một điểm giá nào**: `price_daily` 0 dòng cho `security_type='index'`; `market.index_stat_daily` **0 dòng**; `asset.asset` chỉ có chỉ số quốc tế; `macro.indicator` không có. 18 chỉ số có **danh tính** trong `market.security` nhưng rỗng dữ liệu | bắt buộc có hình dạng "**có mã, không có dữ liệu**" tách khỏi "không tìm thấy mã" (§4.6) |
| F4 | `market.financial_statement` **27.281.962 dòng**; `length_report` 1–4 = quý, **5 = cả năm**; `canonical_code` **NULL toàn bộ** | luôn lọc `issuer_id` trước; bộ chỉ tiêu mặc định đóng (§4.5.2) |
| F5 | `market.metric_dictionary` 729 mã, `unit` nạp từ **`don_vi_du_lieu`**: `VND` 582 · `ty_le_thap_phan` 80 · `lan` 46 · `VND/CP` 10 · `co_phieu` 8 · `so_luong` 1 · **NULL 2** | bảng quy đổi §4.5.1 |
| F6 | 🔴 **`name_vi` KHÔNG duy nhất**: `isa20` và `isa22` **cùng tên** "LỢI NHUẬN THUẦN" (FPT 2024: 9.427,4 vs 7.856,8 tỷ — chênh đúng bằng `isa21` lợi ích cổ đông thiểu số); "Giá trị hao mòn lũy kế" 4 mã; BVPS 3 mã (`rsd7`/`rtd7`/`ryd7`) | luật "dịch mã sang tên" **không đủ** ⇒ dùng **bảng nhãn đóng** do dự án tự viết (§4.5.2) |
| F7 | `market.screener_daily` **2 ngày** (2026-09-03, 2026-09-04), payload `financial` (5 khoá) + `stockScreenerItem` (70 khoá) | `screen_stocks` đọc ngày mới nhất **có dữ liệu**, luôn trả kèm `ngay_du_lieu` |
| F8 | ⚠️ `prf` = "Lợi nhuận ròng **(tỉ đồng)**" nhưng `unit='VND'`; `rev` tương tự — tên và đơn vị đá nhau | loại khỏi mọi đường hiển thị; ghi nợ (§8) |
| F9 | Cây ngành riêng 6 nhóm × 24 ngành ở `market.industry`; đường đọc ngành doanh nghiệp là view `market.v_issuer_industry` (`issuer_id, industry_id, source ∈ manual\|icb`) | `get_industry_tree` chỉ đọc hai chỗ này |
| F10 | `asset` chia **hai bảng**: `asset.price_daily` (commodity 49, fx 12, index 2) và `asset.ohlc_daily` (crypto 11, fx 17, index 37) | function chuỗi tài sản đọc **cả hai** |
| F11 | View `macro.observation_spliced` có cột **`value_spliced`** và **`value_as_published`** — **không có cột `value`** | §4.4 #8 chốt lấy cột nào |
| F12 | `news.article` 8.137 bài (2025-04-06 → 2026-09-06, đang tăng), **230 có nhãn**; `article_revision.tsv` là cột GENERATED `to_tsvector('simple', news.immutable_unaccent(title \|\| ' ' \|\| content))` | truy vấn tìm kiếm **bắt buộc** bọc `news.immutable_unaccent()` cho cả chuỗi hỏi |
| F13 | 🔴 **`plainto_tsquery` AND từng âm tiết ⇒ nhiễu nặng với tiếng Việt.** Đo: "cổ phiếu thưởng" `plainto` **1.168** bài / `phraseto` **41**; "lãi suất điều hành" 1.050 / 31; "thuế quan" 1.816 / 211 | `get_news` dùng `phraseto_tsquery` trước (§4.5.4) |
| F14 | `news.trade_name` **0 dòng** (bảng thật, chưa ai nạp) | gợi ý mã không dựa vào bảng này (§4.6) |
| F15 | 442 mã `delisted` có **0 dòng** trong `price_daily`; ETF cũng 0 | mã huỷ niêm yết luôn rơi vào hình dạng "không có dữ liệu" khi hỏi giá |
| F16 | 4 extension nằm trong schema `extensions`, không phải `public` | mọi SQL qualify `extensions.similarity(...)`, `OPERATOR(extensions.%)` |

### 2.2 Quyền và hạ tầng gọi model

| # | Dữ kiện | Hệ quả |
|---|---|---|
| G1 | `dlck_api` chỉ `SELECT` trên `market`/`macro`/`asset`/`news`, **không có USAGE trên `ops`**. User login duy nhất là `etl_worker` (thuộc `dlck_etl`) — **chưa có user nào thuộc `dlck_api`** | phải tạo user login mới + biến môi trường mới (§4.7) |
| G2 | `ops.llm_call.purpose` **không có CHECK** ⇒ ghi `'chat'` chạy được. *(Chú thích `lát 10: 'chat'` là comment SQL trong file migration `0018` dòng 40, **không** phải `COMMENT ON` trong DB.)* Ràng buộc thật: `status ∈ ok\|repaired\|failed`, `thinking ∈ adaptive\|disabled`, NOT NULL `purpose, model, thinking, status, http_calls, latency_ms` | ánh xạ trạng thái ở §4.7 |
| G3 | SDK `anthropic==1.4.0`: `client.beta.messages.tool_runner(...)` tồn tại, nhận `system`, `thinking`, `tools`, `max_iterations` | dùng SDK |
| G4 | Đọc mã `lib/tools/_beta_runner.py`: khi `stop_reason='tool_use'`, runner nối lượt sau bằng `append_messages(message, response)` với `message` nguyên văn ⇒ **`thinking.signature` echo đúng** (reviewer đã dán payload thật: `{"signature":"SIG-123","thinking":"…","type":"thinking"}`) | không tự chép logic serialize |
| G5 | `self._iterator = self.__run__()` tạo **một lần** trong `__init__`. Runner đã cạn iterator, khi gọi lại **không ném lỗi, không gửi request, trả lại message cũ** — **hỏng im lặng** | mỗi lượt người dùng dựng **runner mới** |
| G6 | 🔴 `generate_tool_call_response()` **có cache**; `append_messages()` **xoá cache** (`_beta_runner.py:150`). Gọi tay `generate…` rồi `append_messages` ⇒ `__run__` gọi `generate…` lần nữa với cache rỗng ⇒ **mọi function chạy HAI LẦN**, lịch sử message vẫn đúng nên **không có gì báo** (reviewer tái hiện: `TOOL INVOCATIONS: 2 ['HPG','HPG']`) | §4.2 sửa: **sửa `response` tại chỗ, KHÔNG gọi `append_messages`** |
| G7 | `BetaFunctionTool.call(input)` gọi `self._func_with_validate(**input)` — **chỉ** đối số do model sinh, không có khe truyền `Connection`; và SDK đặt nguyên giá trị trả về vào `tool_result.content` (`:295`), không kiểm kiểu | tool phải là **closure ôm engine** và **trả `str`** (§4.4) |
| G8 | MiniMax: ép công cụ + enum ⇒ 0 lỗi schema/232 lời gọi. 🔴 **Trường mảng rỗng phải TUỲ CHỌN**. Reviewer đo thêm: **vô hướng `str\|None` không có default cũng vào `required`** (`get_news required: ['query','ticker']`) | mọi tham số tuỳ chọn **phải có giá trị mặc định** |
| G9 | Tokenizer tiếng Việt **1,62 ký tự/token**. L1 trọn 61.240 ký tự ≈ **37.802 token** | ngân sách §4.3 |
| G10 | Cache tự động trúng **≈ 50 %** khi chạy lô; giá pay-go $0,30/1M vào · $1,20/1M ra · $0,06/1M đọc cache | §4.3 |
| G11 | Độ trễ lô adaptive: p50 8,0 s · p90 16,5 s · max 50 s | một câu nhiều vòng function có thể 30–60 s |
| G12 | 🔴 Mọi lượt chạy **nền** của job gọi model đều đóng băng; **tiền cảnh thì sạch**. Nguyên nhân chưa xác định | bộ hồi quy chạy **tiền cảnh, chia khối** |
| G13 | `dlck_api` **đủ quyền cho toàn bộ 21 đường đọc** lát 10 cần, gồm 3 view và `extensions.unaccent`/`similarity`/`%`, và `EXECUTE` trên `news.immutable_unaccent`; `ops` và mọi INSERT bị chặn đúng *(reviewer đo)* | không cần migration nào |

### 2.3 Hai phát hiện làm đổi tiêu chí nghiệm thu

**P1 — bộ 10 câu vòng 6 KHÔNG còn trong repo.** `grep` toàn bộ `docs/` và `backend/`: chỉ còn *mô tả phương pháp* ở `maintenance.md §6`. Không có câu hỏi, không có số liệu đầu vào, không có transcript. ⇒ dựng bộ mới, gọi là **vòng 7**, và **lưu vào repo**.

**P2 — con số "FCFF phải ra 260 tỷ" không đối chiếu được.** `maintenance.md §6` ghi 260, còn ví dụ DCF duy nhất còn lại (`valuation.md` "Ví dụ 1") cho **270** (600×0,8 + 180 − 330 − 60). Câu test vòng 6 gần như chắc chắn dùng số khác ví dụ trong skill — đúng cách làm, nhưng đã mất. ⇒ **không sửa 260 thành 270** (sửa số mà không đo là nói dối, §1.2); chỉ ghi chú và trỏ sang bộ vòng 7.

### 2.4 Giả định — chưa kiểm

| # | Giả định | Kiểm thế nào |
|---|---|---|
| A1 | `tool_runner` chạy được với MiniMax ở hình dạng lát 10. **Rủi ro cụ thể: `beta.messages.parse` LUÔN gắn header `anthropic-beta: structured-outputs-2025-12-15`** (`resources/beta/messages/messages.py:1228–1240`), không tắt được qua tham số — MiniMax có thể trả 400 | **task 1 của plan**: một lượt gọi thật; hỏng thì **in nguyên văn status + body** để phân biệt "không chịu tool_runner" với "không chịu một header" |
| A2 | Schema `@beta_tool` sinh ra (`anyOf: [string, null]` cho tham số tuỳ chọn) được MiniMax nuốt | task 1 kiểm cùng lượt; hỏng thì đổi sang `str = ""` thay cho `str \| None = None` |
| A3 | Chèn câu nhắc "quay lại mạch L1" vào lượt `tool_result` giúp giữ hình dạng | bộ hồi quy chạy **có** nhắc; ≥ 1 câu hỏng hình dạng thì chạy lại **không** nhắc để biết nhắc có tác dụng không |
| A4 | Model tự biết gọi `load_knowledge_reference` khi cần công thức | 6 câu nhóm A bắt buộc chạm L2; đếm số lần gọi |
| A5 | ~10 lượt chat/ngày không làm cạn cửa sổ Token Plan | in `token_plan_remains()` cuối mỗi lượt |

## 3. Ba phương án và quyết định *(CLAUDE.md §4.8)*

Ba phương án sinh **độc lập, song song** bởi ba subagent trên cùng fact pack, mỗi phương án tối ưu một trục và tự khai rủi ro. Bản đầy đủ ở scratchpad phiên (`option-A.md`, `option-B.md`, `option-C.md`).

| | **A — tối giản (YAGNI)** | **B — bán kính hỏng nhỏ, kiểm chứng được** | **C — chất lượng câu trả lời** |
|---|---|---|---|
| Cây file | 5 file phẳng | tách seam tối đa, `tools/` 9 file | ~19 file, tách theo "mỗi chỗ giấu một loại lỗi" |
| Vòng chat | `until_done()` | `tool_runner` + mock transport | `tool_runner`, **lặp tay**, chèn nhắc quay-lại-L1 |
| Dữ liệu trả model | JSON thô, giữ mã chỉ tiêu | JSON + view mới `v_screener_latest` | dịch nhãn, quy đổi đơn vị, cờ tường minh cho trạng thái thiếu dữ liệu |
| Quyền DB | `SET LOCAL ROLE` trên `etl_worker` | user mới + **role mới `dlck_chatlog`** | user mới + **migration nới INSERT cho `dlck_api`** |
| Bộ hồi quy | chạy tay, không lưu | script ngoài pytest, lưu hồ sơ | dựng lại bộ câu, rubric 2 lớp |
| Tự khai rủi ro nặng nhất | quên gọi `api_conn()` ⇒ âm thầm chạy full quyền `dlck_etl` | trừu tượng thừa nếu lát API không tới | prompt phình, chi phí chưa đo |

**Chấm theo tiêu chí viết trước:**

1. *Trả lời được câu hỏi lớn của lát* — cả ba đạt.
2. *Tuân luật đã có, không phải tuỳ chọn* — `market-data-store §6.2` cấm phơi mã thô cho LLM. **Chỉ C tuân.**
3. *§3.5 test dưới đúng quyền production* — B mạnh nhất, C đạt, **A vi phạm tinh thần** (production và test chung user, đúng/sai phụ thuộc lập trình viên nhớ gọi `api_conn()` — chính A tự khai).
4. *Tối giản §4.4.2* — A mạnh nhất; B thêm **role mới + view mới + migration** cho nhu cầu chưa chứng minh.
5. *Bán kính rollback* — cả ba là code mới trong thư mục mới; B và C thêm thay đổi DB nên nhỉnh hơn về rủi ro.

**Chọn C.** Câu hỏi lớn của lát là *chất lượng hợp đồng*; đổ `rtq12: 0.17377625` vào model thì thí nghiệm hỏng vì lý do tầm thường chứ không phải vì hợp đồng sai. C cũng là phương án đọc kỹ nhất phần tri thức — nó tìm ra P1 và P2, hai lỗ hổng nghiệm thu mà hai phương án kia không thấy.

**Loại A**: cắt đúng những thứ lát này tồn tại để kiểm chứng, và để lại bẫy quyền do chính nó khai.
**Loại B**: tối ưu cho thế giới nhiều consumer trong khi lát 10 chỉ có **một** consumer là vòng chat terminal. Giữ làm tham chiếu cho lát API.

**Mượn từ phương án khác — nói rõ:**

| Mượn | Từ | Vì sao C vẫn đứng vững |
|---|---|---|
| Seam test **đầu tiên** là test quyền, không phải test format | B | chỉ đổi **thứ tự** TDD, không đụng thiết kế |
| Lưu kết quả bộ hồi quy thành hồ sơ để lượt sau so được | B | bổ sung thuần |
| **Bỏ migration nới quyền `ops.llm_call`**; ghi sổ bằng kết nối thứ hai dưới `ETL_DATABASE_URL` | A | giữ `dlck_api` đúng hợp đồng "chỉ đọc"; **lát 10 không có migration nào** |

**Điều kiện đảo ngược:**

| Nếu | Thì |
|---|---|
| A1/A2 sai (header hoặc schema bị MiniMax từ chối) | đổi sang vòng lặp `messages.create` tay, tự echo `thinking` + `signature`; task 1 là chỗ phát hiện |
| Chi phí thật **> 3 lần** ước lượng §4.3 (tức > $0,15/câu), hoặc một câu > 90 s | cắt L1 xuống chỉ `SKILL.md` + nạp references theo nhu cầu — **đổi quyết định #4 của chủ dự án, phải hỏi** |
| Bộ hồi quy < 15/15 số đúng, hoặc ≥ 2/15 hỏng hình dạng L1 | dừng, không mở rộng; báo nguyên trạng — đây chính là kết quả lát cần biết |
| Lát API cần ghi `ops.llm_call` từ tiến trình chỉ-đọc | tách role `dlck_chatlog` chỉ INSERT một bảng, theo hướng B |

## 4. Thiết kế

### 4.1 Cây file

```
backend/agent/
├── __init__.py
├── __main__.py            entry `python -m agent`: nạp .env, dựng LLMClient + 2 engine, chạy REPL, đóng sạch ở finally
├── system_prompt.py       SCOPE_GUARD (nguyên văn maintenance.md §7) + build_system_blocks()
├── skills.py              nạp trọn L1 lúc khởi động (thiếu file ⇒ raise ngay); bảng 9 khoá L2 → Path
├── db.py                  read_engine (AGENT_DATABASE_URL, role dlck_api) + ops_engine (ETL_DATABASE_URL);
│                          assert_read_only() chạy lúc khởi động
├── labels.py              BẢNG NHÃN ĐÓNG: 21 mã → nhãn hiển thị (§4.5.2); ngoài bảng ⇒ từ chối
├── format.py              display_metric(value, unit), display_series_value(value, unit), format_date_vi
├── llm_log.py             ghi 1 dòng ops.llm_call mỗi request; lỗi ghi sổ KHÔNG làm sập chat
├── chat.py                vòng REPL nhiều lượt: dựng runner mỗi lượt, lặp tay, chèn nhắc, in kết quả
└── tools/
    ├── __init__.py        build_tools(read_engine) -> list[BetaFunctionTool] — 9 tool, mỗi tool là closure
    ├── _shared.py         resolve_ticker(), cap_limit(), 4 khuôn trạng thái dữ liệu, to_json()
    ├── screen_stocks.py · get_financials.py · get_price_series.py · get_corporate_events.py
    ├── compare_peers.py · get_news.py · get_industry_tree.py · get_macro_series.py
    └── load_knowledge_reference.py
```

**Ranh giới:**

- `tools/*` **không** biết gì về model; **không** nhận `Connection` từ ngoài (SDK không có khe truyền — G7). Mỗi tool là **closure ôm `read_engine`**, tự `with engine.connect() as conn:` trong thân hàm, chạy xong đóng ngay.
- 🔴 **Không giữ kết nối hay giao dịch nào bắc qua một lời gọi model.** Một câu chạy 30–60 s với 2–5 request HTTP; giữ transaction mở suốt thời gian đó tạo `idle in transaction`, chặn autovacuum. Bất biến kiểm được: sau một lượt chat, `pg_stat_activity` không còn dòng `idle in transaction` nào của `agent_reader`.
- `chat.py` chỉ lắp ráp, không chứa SQL. `format.py`/`labels.py` là hàm thuần, không chạm DB.

### 4.2 Vòng chat

```python
runner = llm.raw.beta.messages.tool_runner(
    model=settings.model, max_tokens=4000, system=build_system_blocks(),
    messages=history, tools=build_tools(read_engine),
    thinking={"type": "adaptive"}, max_iterations=8,
)
for message in runner:
    log_llm_call(ops_engine, message, purpose="chat")
    if message.stop_reason == "tool_use":
        response = runner.generate_tool_call_response()   # có cache — gọi ở đây để chèn nhắc
        if response is not None:
            response["content"] = [*response["content"], {"type": "text", "text": REMINDER}]
            # 🔴 KHÔNG gọi append_messages: nó xoá cache ⇒ __run__ chạy lại toàn bộ tool (G6).
            # Để __run__ tự lấy CÙNG object đã sửa từ cache và tự nối.
```

- **Vì sao dùng SDK** (G4): runner echo nguyên văn block `thinking` kèm `signature`. Tự viết là tự chép lại đúng chỗ hỏng im lặng dự án đã trả giá (§3.4).
- **Vì sao lặp tay** (không `until_done()`): cần chỗ chen nội dung. Hai lượt `user` liên tiếp không hợp lệ trên Messages API ⇒ cách hợp lệ duy nhất để nhắc model là **thêm block `text` vào cùng mảng `content` của lượt `tool_result`**.
- **🔴 Không `append_messages` sau khi gọi `generate_tool_call_response`** (G6) — đây là lỗi nhân đôi mọi lời gọi function, im lặng hoàn toàn. Có test seam canh (§6 S6).
- **Nhiều lượt chat** (G5): runner không tái dụng được và tái dụng hỏng im lặng. `chat.py` tự giữ `history`, dựng runner mới mỗi lượt, **không đọc `_params`**.
- `max_iterations=8`: trần cứng chống vòng gọi vô hạn — **số chọn, chưa đo**; chạm trần thì báo lỗi rõ ràng, không treo.
- `REMINDER` ≈ 350 ký tự (≈ 215 token), chỉ ở lượt **có gọi function**: dùng đúng số vừa tra, giữ hình dạng L1, không lộ mã chỉ tiêu thô.

### 4.3 System prompt, nạp skill, ngân sách

`system` là list 2 block: `[SCOPE_GUARD, L1_TOÀN_VĂN]`.

- `SCOPE_GUARD` chép **nguyên văn** ba đoạn ở `maintenance.md §7`.
- `L1_TOÀN_VĂN` = `vn-stock-advisor/SKILL.md` + 4 file `references/`, nối theo thứ tự cố định. **61.240 ký tự ≈ 37.802 token.**
- L2 qua `load_knowledge_reference(topic)`, `topic` là **enum đóng 9 giá trị**; mô tả function liệt kê 9 chủ đề kèm một dòng nội dung.

**Ngân sách một câu — tính theo SỐ REQUEST, không theo một lần gửi.** Mỗi vòng gọi function là **một request mới gửi lại toàn bộ `system`**. Một câu điển hình có 2 vòng function ⇒ **3 request**:

| | Token vào/request | ×3 request | $ (không cache) | $ (cache 50 %) |
|---|---:|---:|---:|---:|
| `system` (SCOPE_GUARD + L1) | 38.100 | 114.300 | 0,0343 | 0,0189 |
| Định nghĩa 9 tool | 1.200 | 3.600 | 0,0011 | 0,0006 |
| Kết quả function + nhắc | — | ≈ 2.500 | 0,0008 | 0,0008 |
| Một file L2 nếu model gọi | 16.700 | ≈ 33.400 | 0,0100 | 0,0055 |
| Đầu ra (thinking + trả lời) | — | ≈ 1.500 | 0,0018 | 0,0018 |
| **Câu không chạm L2** | | **≈ 121.900** | **≈ 0,038** | **≈ 0,022** |
| **Câu có chạm L2** | | **≈ 155.300** | **≈ 0,048** | **≈ 0,028** |

Đây là **ước lượng**, phải thay bằng số đo thật (AC8). Ngưỡng đảo ngược ở §3 (> $0,15/câu) tính trên con số này.

### 4.4 Hợp đồng 9 function

Quy ước chung:

- 🔴 **Mọi tham số tuỳ chọn phải có giá trị mặc định** — mảng `= []`, vô hướng `= None` (G8). Không có default là vào `required`, đúng bẫy đã đo.
- 🔴 **Mọi tool trả `str`** — `json.dumps(payload, ensure_ascii=False)` qua helper `to_json()`. SDK đặt nguyên giá trị trả về vào `tool_result.content` mà không kiểm kiểu (G7); trả `dict` sinh content là object, API thật từ chối.
- Khoá JSON tiếng Việt không dấu (`ma`, `ten`, `gia_tri`, `ngay`); **không bao giờ có khoá là mã chỉ tiêu thô**.
- Mọi kết quả kèm `ngay_du_lieu` hoặc `khoang_ngay`.
- `limit` mặc định nhỏ, có trần cứng; vượt trần thì cắt và ghi `da_cat: true`.

| # | Function | Tham số (đều có mặc định trừ chỗ ghi *bắt buộc*) | Nguồn | Trần |
|---|---|---|---|---|
| 1 | `screen_stocks` | `criteria: list[{metric_code, operator, value}] = []`, `industry_code = None`, `exchange = None`, `sort_by = None`, `limit = 20` | `screener_daily` (ngày mới nhất) ⋈ `security` ⋈ `v_issuer_industry` | limit ≤ 50 |
| 2 | `get_financials` | `ticker` *bắt buộc*, `statement_type = 'IS'`, `from_year = None`, `to_year = None`, `period = 'nam'`, `metric_codes = []` | `financial_statement` | ≤ 8 năm |
| 3 | `get_price_series` | `ticker` *bắt buộc*, `from_date = None`, `to_date = None`, `adjusted = True` | `price_daily` | ≤ 400 phiên |
| 4 | `get_corporate_events` | `ticker` *bắt buộc*, `event_type = None`, `from_date = None`, `to_date = None`, `limit = 20` | `corporate_event` | limit ≤ 50 |
| 5 | `compare_peers` | `tickers = []`, `metric_codes = []`, `industry_code = None` | `screener_daily` ngày mới nhất | ≤ 10 mã, ≤ 8 chỉ tiêu |
| 6 | `get_news` | `query = None`, `ticker = None`, `group_no = None`, `sub = None`, `industry_code = None`, `from_date = None`, `to_date = None`, `limit = 10` | `article` ⋈ `article_revision` | limit ≤ 30 |
| 7 | `get_industry_tree` | `industry_code = None`, `ticker = None` | `industry`, `v_issuer_industry` | — |
| 8 | `get_macro_series` | `code = None`, `keyword = None`, `from_date = None`, `to_date = None`, `limit = 60` | `macro.observation_spliced` ⋈ `macro.indicator`; `asset.price_daily` **và** `asset.ohlc_daily` ⋈ `asset.asset` | limit ≤ 200 |
| 9 | `load_knowledge_reference` | `topic` *bắt buộc*, `Literal` 9 giá trị | file trong `agent/skills/vn-stock-knowledge/` | — |

Ghi chú bắt buộc:

- **#7 không có `icb_level`** — cây ICB không bao giờ ra tới model. Trả kèm `nguon_gan: 'manual'|'icb'` (siêu dữ liệu về phép gán, không phải cây ICB).
- **#8**: trả `gia_tri` = **`value_spliced`** (chuỗi đã nối, F11); kèm `gia_tri_cong_bo` = `value_as_published` **khi hai giá trị khác nhau**, để model nói được là chuỗi đã nối. `code=None, keyword=...` ⇒ trả **danh mục** chuỗi khớp (mã + tên + đơn vị + khoảng ngày), không trả số — đây là cách model tìm mã, thay cho nhồi 192 mã vào system prompt.
- **#9** `topic` tra `dict` hằng → `Path`, **không nối chuỗi từ đầu vào** ⇒ path traversal không khả dĩ về cấu trúc; vẫn có test chứng minh.

### 4.5 Quy ước trình bày dữ liệu

#### 4.5.1 Đơn vị của `metric_dictionary` (bảng đóng 6 giá trị)

| `unit` | Hiển thị | Ví dụ |
|---|---|---|
| `VND` | so sánh theo **trị tuyệt đối**: \|v\| ≥ 1 tỷ ⇒ "x,y tỷ VND" (1 chữ số thập phân, **giữ dấu**); nhỏ hơn ⇒ "n đ" | `62848794351367` → `"62.848,8 tỷ VND"`; `-6115961971783` → `"-6.116,0 tỷ VND"` |
| `ty_le_thap_phan` | **×100**, 2 chữ số, hậu tố `%` | `0.17377625` → `"17,38%"` |
| `lan` | 2 chữ số, hậu tố ` lần` | `7.89115654` → `"7,89 lần"` |
| `VND/CP` | số nguyên có phân cách, hậu tố ` đ/cp` | `2749.91` → `"2.750 đ/cp"` |
| `co_phieu` | số nguyên có phân cách, hậu tố ` cp` | |
| `so_luong` | số nguyên có phân cách | |
| `NULL` (2 mã) | **loại khỏi kết quả** | |

#### 4.5.1b Đơn vị của `macro` và `asset` — từ vựng KHÁC, không dùng bảng trên

`macro.indicator.unit` và `asset.asset.unit` là văn bản tự do, đo được: `%`, `VND`, `USD`, `người`, `điểm`, `USD/thùng`, `CNY/tấn`, `USDT`, `VND/kg`, `VND/1 USD`, `USD/oz`, `VND/lít`…

| Đơn vị | Hiển thị |
|---|---|
| `%` | 2 chữ số + `%` — 🔴 **KHÔNG nhân 100** (khác hẳn `ty_le_thap_phan`; đây là chỗ dễ sai 100 lần nhất của cả lát) |
| `VND` / `USD` | quy tắc tỷ như §4.5.1 kèm ký hiệu tiền |
| mọi đơn vị khác | số có phân cách + hậu tố **nguyên văn** `unit` |

Test S2 đặt `(4.45, '%') → "4,45%"` **ngay cạnh** `(0.17377625, 'ty_le_thap_phan') → "17,38%"` — hai ca cạnh nhau là chốt chống lỗi nhân-100.

#### 4.5.2 Bảng nhãn đóng — thay cho việc tra `name_vi`

`name_vi` **không duy nhất** (F6), nên tra từ điển là chưa đủ. Dự án tự giữ bảng nhãn cho tập chỉ tiêu đóng; **mã ngoài bảng bị từ chối** kèm danh sách mã hợp lệ. Điều này cũng giải quyết luôn F8 (`prf`/`rev`) và chuyện 83 chỉ tiêu screener chưa nạp.

**BCTC (14 mã)** — `IS`: `isa3` Doanh thu thuần · `isa9` Chi phí bán hàng · `isa10` Chi phí quản lý doanh nghiệp · `isa16` Lợi nhuận trước thuế · `isa20` **Lợi nhuận sau thuế (toàn bộ)** · `isa22` **Lợi nhuận sau thuế của cổ đông công ty mẹ** · `isa23` Lãi cơ bản trên cổ phiếu (EPS). `BS`: `bsa1` Tài sản ngắn hạn · `bsa2` Tiền và tương đương tiền · `bsa53` Tổng tài sản · `bsa54` Nợ phải trả · `bsa78` Vốn chủ sở hữu · `bsa96` Tổng nguồn vốn. `CF`: `cfa18` Lưu chuyển tiền thuần từ hoạt động kinh doanh.

**Tỷ số (7 mã)** — `rtd11` Vốn hoá thị trường · `rtd14` EPS (TTM) · `rtd21` P/E (TTM) · `rtd25` P/B (TTM) · `rtd7` Giá trị sổ sách mỗi cổ phiếu (BVPS, TTM) · `rtq12` ROE (TTM) · `rtq14` ROA (TTM).

Đơn vị vẫn đọc từ `metric_dictionary.unit` (nguồn sự thật về đơn vị); bảng nhãn chỉ quyết **tên hiển thị**.

#### 4.5.3 Ngày tháng

Luôn kèm cả `"ngay": "2026-09-03"` (ISO) và `"ngay_hien_thi": "03/09/2026"`.

#### 4.5.4 `get_news` — tìm kiếm và hai đường lọc

- `query` ⇒ **`phraseto_tsquery('simple', news.immutable_unaccent(:q))`** trước. Lý do đo được (F13): `plainto_tsquery` AND từng âm tiết nên "cổ phiếu thưởng" khớp **1.168** bài, còn `phraseto` khớp **41**. Nếu `phraseto` ra 0 bài thì thử lại `plainto` và trả kèm `kieu_tim: 'cum'|'tu_khoa'` để model biết độ chặt.
- Bọc `news.immutable_unaccent()` là **bắt buộc** — `tsv` được sinh qua hàm đó (F12); quên là khớp 0 bài.
- Sắp xếp theo `ts_rank` giảm dần, rồi `published_at` giảm dần.
- Tìm toàn văn chạy trên **toàn bộ** `article_revision`, không lọc theo trạng thái phân loại.
- `ticker`/`group_no`/`sub`/`industry_code` ⇒ lọc theo nhãn, **chỉ khớp bài đã phân loại**.
- Mỗi bài trả kèm `da_phan_loai: bool`. Khi lọc theo nhãn mà rỗng, trả thêm `ghi_chu` nói rõ có bao nhiêu bài **chưa phân loại** trong khoảng ngày đó — để model không kết luận "không có tin nào".
- Khi backfill xong, `da_phan_loai` luôn `true` và `ghi_chu` biến mất **mà không phải sửa code**.

### 4.6 Bốn hình dạng trạng thái dữ liệu

Phân biệt bằng trường tường minh, **không** bằng độ dài mảng:

| # | Tình huống | Trả về |
|---|---|---|
| 1 | Mã không tồn tại trong `market.security` | `{"tim_thay": false, "ma_da_tra": "XYZ", "goi_y": [...]}` |
| 2 | Mã tồn tại nhưng **kho không có loại dữ liệu này** (VN-Index hỏi giá; mã huỷ niêm yết hỏi giá) | `{"tim_thay": true, "co_du_lieu": false, "ly_do": "kho chưa có dữ liệu giá cho chỉ số", "loai": "index"}` |
| 3 | Mã và loại đúng, khoảng ngày rỗng | `{"tim_thay": true, "co_du_lieu": true, "so_dong": 0, "khoang_co_du_lieu": {"tu": "…", "den": "…"}}` |
| 4 | Có dữ liệu | `{"tim_thay": true, "co_du_lieu": true, "so_dong": n, "du_lieu": [...]}` |

`trang_thai: "delisted"` là **cờ kèm thêm** trên bất kỳ hình dạng nào, không phải hình dạng riêng. Riêng `get_price_series`, mã huỷ niêm yết **luôn** ra hình dạng #2 vì kho chưa có giá lịch sử của mã đã huỷ (F15: 0/442).

**Gợi ý mã** (hình dạng #1) chạy trên `market.security.ticker` + `market.issuer.name`/`short_name` bằng `extensions.similarity`. **Không dùng `news.trade_name`** — bảng rỗng (F14); viết truy vấn sao cho khi bảng có dữ liệu thì thêm vào được mà không phải sửa hình dạng kết quả.

### 4.7 Quyền DB và sổ `ops.llm_call`

- **Đường đọc**: user login mới `agent_reader LOGIN IN ROLE dlck_api`, biến `AGENT_DATABASE_URL` trong `.env`. Tạo user là việc **per-môi-trường, ngoài migration** (khuôn `database/README`). Mật khẩu sinh ngẫu nhiên, ghi thẳng `.env`, **không in ra output, không commit**.
- **`assert_read_only()` chạy lúc khởi động** (khuôn `assert_migrated` của ingester — §3.5 ca thứ ba là lỗi ở *đường khởi động*): khẳng định `pg_has_role(current_user, 'dlck_api', 'member')` **và** `has_table_privilege('market.security', 'INSERT') = false`. Sai thì chết ngay, không chạy tiếp.
- **Đường ghi sổ**: kết nối thứ hai dùng `ETL_DATABASE_URL` sẵn có, **chỉ** để `INSERT INTO ops.llm_call`. Không migration, không role mới.
- **Ánh xạ trạng thái** (G2): `status='ok'` khi `stop_reason='end_turn'`; `'failed'` cho mọi kết thúc khác (`max_tokens`, chạm `max_iterations`, exception) kèm `error` mô tả; `'repaired'` **không dùng** ở lát 10. `thinking='adaptive'`. `http_calls=1` mỗi dòng — **một dòng = một request**, nên một câu chat nhiều vòng function sinh nhiều dòng.
- Lỗi ghi sổ bị nuốt (in stderr), **không bao giờ làm sập chat**.
- **Lát 10 không thêm migration nào.** Head giữ nguyên `0020`.

## 5. Bộ hồi quy vòng 7 — 15 câu

Lưu tại `regression-round7.md` cùng thư mục này. Gọi **vòng 7** vì bộ vòng 6 đã mất (§2.3 P1) — không giả vờ là bộ cũ.

### 5.1 Nhóm A — 6 câu tính toán thuần (ép chạm L2), đáp án tính tay

Số liệu tự đặt, **khác** ví dụ trong `valuation.md`. Đã tự tính tay hai lượt độc lập (tôi và reviewer Opus) — khớp.

| # | Câu hỏi (rút gọn) | Phép tính | Đáp án |
|---|---|---|---|
| A1 | EBIT 800 tỷ, thuế 20%, khấu hao 200, đầu tư vốn gộp 250, đầu tư vốn lưu động mới 90 → FCFF? | 800×0,8 + 200 − 250 − 90 | **500 tỷ** |
| A2 | LNST 520, khấu hao 200, đầu tư vốn 250, vốn lưu động mới 90, **nợ dài hạn mới 80** → FCFE? | 520 + 200 − 250 − 90 + 80 | **460 tỷ** |
| A3 | Rf 5%, beta 1,1, phần bù 8%, lãi vay 9%, thuế 20%, vốn hoá 3.000, nợ vay 2.000 → WACC? | rE = 13,8%; rD sau thuế 7,2%; 0,6×13,8 + 0,4×7,2 | **11,16%** |
| A4 | FCFE 460, g 5%, r 13,8%, 200 triệu cp → giá trị vốn chủ và giá mỗi cp? | 483/0,088 = 5.488,64 tỷ ÷ 200 tr | **5.488,6 tỷ → 27.443 đ/cp** |
| A5 | LNST 300, doanh thu 2.500, tổng tài sản 4.000, vốn chủ 1.500 → ROE Dupont, **tách 3 thành phần**? | 0,12 × 0,625 × 2,667 | **biên LN 12,0% · vòng quay TS 0,625 · đòn bẩy 2,667 · ROE 20,0%** |
| A6 | LNST 480 tỷ, 240 triệu cp, giá 30.000 → EPS, P/E; phát hành thêm 60 triệu cp, LNST không đổi → EPS, P/E mới? | 2.000 đ; 15,0; 1.600 đ; 18,75 | **cả bốn số** |

Bẫy cài sẵn: A2 bắt lỗi dùng công thức FCFF cho FCFE (ra 500) hoặc trừ thay vì cộng nợ mới (ra 300) — đúng vai trò câu FCFF của vòng 6 từng giữ.

### 5.2 Nhóm B — 9 câu ép gọi function, đáp án lấy từ kho (SQL chạy 2026-09-07)

Mỗi câu ép **ít nhất một** function chưa được phủ; 9 câu phủ đủ 8 function dữ liệu.

| # | Câu hỏi | Function ép | Đáp án đúng |
|---|---|---|---|
| B1 | Giá đóng cửa HPG phiên **2026-09-03**? | `get_price_series` | **21.600 đ** (`close_raw` = `close_adj`) |
| B2 | VCB thuộc ngành nào trong bộ ngành của dự án? | `get_industry_tree` | **Ngân hàng và Tín dụng** (`NGANHANG`), nhóm **Dịch vụ Tài chính**; nguồn gán `icb` |
| B3 | Doanh thu thuần và lợi nhuận sau thuế của FPT năm 2024? | `get_financials` | doanh thu thuần **62.848,8 tỷ**; LNST của cổ đông công ty mẹ **7.856,8 tỷ**. *(Chấp nhận **9.427,4 tỷ** nếu câu trả lời ghi rõ là LNST **toàn bộ, gồm cổ đông thiểu số** — hai mã `isa22`/`isa20` cùng tên trong nguồn, F6.)* |
| B4 | CPI Việt Nam **tháng 8/2026** là bao nhiêu? | `get_macro_series` | **4,45%** |
| B5 | FPT có mấy đợt trả cổ tức tiền mặt công bố trong năm 2025, ngày giao dịch không hưởng quyền là ngày nào? | `get_corporate_events` | **2 đợt**, exright **2025-06-12** và **2025-12-01** |
| B6 | Giá dầu WTI ngày **2026-09-05**? | `get_macro_series` (nhánh `asset`) | **91,22 USD/thùng** |
| B7 | Ba mã ngành Ngân hàng và Tín dụng có ROE (TTM) cao nhất theo screener phiên **2026-09-04**? | `screen_stocks` | **TIN 73,48% · HDB 24,84% · LPB 24,66%** *(TIN là số bất thường — câu trả lời tốt nên nêu nghi vấn, nhưng chấm số theo đúng thứ tự này)* |
| B8 | So P/E (TTM) của HPG và VCB theo screener phiên **2026-09-04**? | `compare_peers` | **HPG 7,89 lần · VCB 11,82 lần** |
| B9 | Có bao nhiêu bài **đăng trong tháng 8/2026** nhắc đúng cụm "lãi suất điều hành"? | `get_news` | **23 bài** |

`load_knowledge_reference` được phủ bởi nhóm A (6 câu đều cần công thức trong L2).

Ba câu B4, B5, B9 dùng **khoảng thời gian đóng trong quá khứ** để đáp án không hết hạn — kho tin vẫn đang nhận bài mới, câu "mới nhất" sẽ tự huỷ.

### 5.3 Chấm hai lớp

**Lớp 1 — số:** một câu đạt khi **mọi** con số trong đáp án đúng. Sai số cho phép **±0,5 % chỉ ở A4** (số vô hạn tuần hoàn); các câu còn lại ra số chẵn tuyệt đối. **15/15 mới đạt.**

**Lớp 2 — hình dạng L1:** mỗi câu chấm 5 mục, đạt khi **≥ 4/5** và **không câu nào** vi phạm mục 5:

1. Có mạch lập luận, không phải bảng số trần.
2. Kết luận có điều kiện (nêu điều kiện làm kết luận đổi).
3. Nêu rõ số nào tra được, số nào là giả định.
4. Không khuyến nghị mua/bán cụ thể.
5. 🔴 **Không lộ mã chỉ tiêu thô** (`rtq12`, `isa3`, `bsa53`…) trong câu trả lời.

**Cách chấm:** subagent **Sonnet** độc lập, nhận câu hỏi + đáp án + rubric, không biết câu trả lời từ đâu. Chạy **tiền cảnh, chia khối** (G12). Lưu 15 transcript + bảng chấm cạnh spec.

## 6. Seam test và thứ tự TDD

| # | Seam | Test đỏ đầu tiên |
|---|---|---|
| S1 | `agent.db.assert_read_only()` | `test_assert_read_only_passes_as_dlck_api`: trong transaction có `SET LOCAL ROLE dlck_api`, `pg_has_role` đúng **và** `has_table_privilege('market.security','INSERT')` **false**; `test_insert_denied_under_dlck_api`: INSERT vào `market.industry` ném `InsufficientPrivilege` |
| S2 | `format.display_metric` / `display_series_value` | `(0.17377625,'ty_le_thap_phan')→"17,38%"` **cạnh** `(4.45,'%')→"4,45%"`; `(-6115961971783,'VND')→"-6.116,0 tỷ VND"`; `(91.22,'USD/thùng')→"91,22 USD/thùng"`; `(None,'VND')→None` |
| S3 | `system_prompt.build_system_blocks` | block[0] chứa nguyên văn câu "chỉ trả lời trong lĩnh vực chứng khoán, tài chính và kinh tế"; block[1] chứa tiêu đề thật của L1; **không** chứa tiêu đề của L2 |
| S4 | 8 function dữ liệu (8 file test) | mỗi function ≥ 1 test giá trị đúng + ≥ 1 test biên/trạng-thái-thiếu-dữ-liệu. `get_news` bắt buộc có ca `phraseto` vs `plainto` (F13) |
| S5 | `load_knowledge_reference` | `topic="../../../etc/passwd"` bị từ chối ở tầng schema; `topic="valuation"` trả nội dung bắt đầu bằng tiêu đề thật |
| S6 | `chat` với model giả | `test_tool_called_exactly_once`: model giả phát 1 `tool_use`, hàm đếm số lần chạy = **1** (canh đúng lỗi G6); `test_tool_result_carries_reminder`; `test_history_survives_two_turns` |
| S7 | `llm_log.log_llm_call` | `test_log_written_under_etl_role` (role thật); `test_log_failure_does_not_break_chat` |

**Thứ tự TDD:** S1 → S2 → S3 → S5 → S4 (từng function một vòng đỏ→xanh) → S6 → S7.

🔴 **Luật lấy expected (chống test tautological, §4.5.3):** expected là **hằng số literal** dán vào test, kèm ngày đo và câu SQL đã dùng, ghi trong docstring. Câu SQL lấy expected phải đi **đường khác** đường của hàm (hàm đọc `screener_daily` thì expected lấy từ `financial_statement`, hoặc ngược lại). Không đi được đường khác thì chép giá trị và ghi rõ *"cùng đường, chỉ là chốt hồi quy — không chứng minh tính đúng"*.

**Mock model:** dùng lại khuôn `httpx2.MockTransport` ở `backend/tests/core/test_llm_client.py`. Bộ hồi quy §5 là thứ **duy nhất** gọi model thật và **không** nằm trong `pytest`.

## 7. Tiêu chí nghiệm thu

| AC | Nội dung | Cách kiểm |
|---|---|---|
| **AC1** | `tool_runner` chạy được với MiniMax ở hình dạng lát 10 | một lượt gọi thật; hỏng thì dán **nguyên văn status + body** (phân biệt lỗi header với lỗi cơ chế) |
| **AC2** | Không test nào đang xanh chuyển thành đỏ | chạy `uv run --project backend pytest -q` trên `main` **và** trên nhánh, dán cả hai dòng tóm tắt; số test mới ≥ số seam §6; **không** có `skip`/`xfail` mới |
| **AC3** | Đường đọc chạy dưới `dlck_api` và role đó **không ghi được**; `assert_read_only()` chặn được cấu hình sai | S1 xanh + chạy tay `python -m agent` một lần dưới đúng credential production, dán output |
| **AC4** | Cả 9 function trả đúng dữ liệu thật | S4 + S5 xanh; bộ hồi quy §5.2 phủ 8 function dữ liệu, nhóm A phủ function thứ 9 |
| **AC5** | Câu ngoài lĩnh vực bị từ chối gọn trong một câu | hỏi 4 câu ngoài phạm vi (sức khoẻ, pháp lý, lập trình, nấu ăn) — 4/4 bị từ chối, dán transcript |
| **AC6** | "VN-Index hôm nay bao nhiêu điểm" ⇒ model **nói thẳng kho chưa có**, không bịa, không thay bằng chỉ số khác | transcript |
| **AC7** | Bộ hồi quy: **15/15 số đúng**, ≥ 14/15 đạt hình dạng L1 | bảng chấm lưu cạnh spec |
| **AC8** | Chi phí và độ trễ thật mỗi câu được đo | `ops.llm_call` sau bộ hồi quy: token vào/ra p50, độ trễ p50/p90, $ quy đổi, số request/câu |
| **AC9** | Không còn `idle in transaction` của `agent_reader` sau một lượt chat | `pg_stat_activity` |
| **AC10** | Tài liệu §9 đã cập nhật, không còn chỗ đá nhau | chạy phép kiểm `git grep` của §1.7, dán kết quả |

**AC7 không phải cổng chặn merge.** Kết quả xấu chính là **phát hiện của lát** — báo nguyên trạng, không sửa cho đẹp.

## 8. Nợ và rủi ro

**Nợ mới sinh**

| Nợ | Vì sao hoãn |
|---|---|
| `prf`/`rev`: tên "(tỉ đồng)" vs `unit='VND'` — chưa giải, đang bị loại khỏi hiển thị | phải đối chiếu giá trị thật với BCTC; việc của lát ETL |
| 83 chỉ tiêu `GetScreenerParameters` chưa nạp ⇒ phần lớn 70 khoá screener nằm ngoài bảng nhãn | việc của lát ETL |
| Ghi `ops.llm_call` qua kết nối `dlck_etl` — đúng cho terminal, **không** đúng cho service | lát API tách role `dlck_chatlog` |
| `max_iterations=8`, `REMINDER` chưa đo hiệu quả | đo sau khi có nhiều lượt chat thật |
| `news.trade_name` rỗng ⇒ gợi ý mã chỉ dựa ticker + tên doanh nghiệp | chờ lát nào đó nạp bảng |

**Nợ mang sang từ lát 9:** `x` recall 81 % · `1a`↔`1b` còn nhầm · ba ô thiếu trong cây ngành · job gọi model chạy nền bị đóng băng.

**Rủi ro lớn nhất:** A1/A2 sai — MiniMax từ chối header beta hoặc schema `anyOf`. Đặt thành **task 1** của plan chính là để nó lộ ra khi chưa xây gì.

## 9. Tài liệu phải cập nhật cùng lượt *(CLAUDE.md §1.6, §1.7)*

| File | Sửa gì |
|---|---|
| `docs/20-design/chatbot-semantic-layer.md` | bỏ trạng thái "chưa duyệt"; `get_industry_tree` bỏ `icb_level`; 8 → 9 function; chép hợp đồng thật; đóng 3 trong 4 "điều chưa biết" bằng số đo |
| `docs/20-design/market-data-store.md` §6.3 | đồng bộ danh sách function; ghi rõ ví dụ view §6.2 dùng tên bảng cũ (`organization`) đã đổi từ spec 2026-08-25 |
| `docs/30-skills/maintenance.md` §6 | ghi chú: bộ vòng 6 không tái lập được, "FCFF 260" không đối chiếu được; trỏ sang bộ vòng 7 |
| `docs/00-overview/roadmap.md` | đóng lát 10; **ghi rõ lát 11 đã gộp vào lát 10** (dòng 150 và bảng ánh xạ `[14]`), số lát sau giữ nguyên; **gỡ "Chọn mô hình embedding DỜI sang lát 10" ở dòng 145**; viết "Điểm vào cho lát 12" |
| `database/README.md` | thêm user login `agent_reader IN ROLE dlck_api` vào mục per-môi-trường |
| `docs/90-records/README.md` | thêm hồ sơ plan mới vào index |
| `.env` | thêm `AGENT_DATABASE_URL` (giá trị không bao giờ in ra) |

## 10. Điều chủ dự án cần biết

1. **Bộ 10 câu vòng 6 đã mất** — không tái lập được. Lát 10 dựng bộ vòng 7 (15 câu) và lưu vào repo. Con số "FCFF 260 tỷ" không đối chiếu được với bất cứ thứ gì còn lại; **không sửa nó**, chỉ ghi chú.
2. **VN-Index chưa có trong kho.** Chatbot sẽ nói thẳng là chưa có. Muốn trả lời được cần một lát ETL riêng cho chỉ số — chưa có trong lộ trình.
3. **Lát 11 gộp vào lát 10** (§1) — vì lát 11 vốn là "chạy lại bộ vòng 6", mà bộ đó đã mất và lát 10 phải tự dựng để nghiệm thu.
4. Lát 10 **không thêm migration** và **không bật job tự động** nào.
5. Cần tạo user Postgres mới trên máy dev (`agent_reader`) — mật khẩu sinh ngẫu nhiên, ghi vào `.env`, không in ra.
6. Ước lượng chi phí **≈ $0,022–0,048 một câu** (đã tính đúng theo số request). Nếu thật > $0,15/câu thì phải đổi cách nạp skill — sẽ hỏi lại.

## 11. Lượt review độc lập

Bản đầu của spec này qua một lượt review độc lập bằng **Opus** (không thấy quá trình viết spec, tự kiểm số bằng truy vấn thật và đọc mã SDK). Kết quả: **6 mục CHẶN + 16 mục NÊN SỬA + 4 ghi nhận**, tất cả đã đóng trong bản này.

Sáu mục chặn, tóm tắt: (1) vòng lặp §4.2 **gọi mọi function hai lần** vì `append_messages` xoá cache — tái hiện được, hỏng im lặng; (2) tool trả `dict` sinh `tool_result.content` không hợp lệ, phải trả `str`; (3) `current_user` không bao giờ trả `dlck_api` nên test quyền cũ đỏ vĩnh viễn; (4) ngân sách thiếu ≈ 3,8 lần vì không tính mỗi vòng function là một request mới; (5) `isa20`/`isa22` trùng tên hiển thị làm đáp án B3 mơ hồ; (6) vô hướng `str|None` thiếu default cũng vào `required`, đúng bẫy G8.

Phần dữ kiện kho được reviewer xác nhận: **30/35 khẳng định trùng khít**, gồm phân bố đơn vị 729 mã, phân chia hai bảng `asset`, và VN-Index rỗng ở cả bốn chỗ. Sáu đáp án nhóm A được tính tay độc lập lần hai — đều đúng. Báo cáo đầy đủ ở scratchpad phiên (`spec-review-opus.md`).
