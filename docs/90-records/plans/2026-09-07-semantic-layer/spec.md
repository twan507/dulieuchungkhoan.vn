# Spec — Lát 10: tầng ngữ nghĩa, nối kho ↔ hai skill bằng function calling

**Ngày:** 2026-09-07 · **Nhánh:** `feat/semantic-layer` · **Trạng thái:** chốt (chủ dự án uỷ quyền tự chốt sau một lượt review độc lập bằng Opus — goal phiên 2026-09-06 tối)

Lát 10 dựng phần **ở giữa** hai đầu đã có: kho dữ liệu (đã đầy) và hai skill dạng prompt (đã test 6 vòng). Phần giữa này là [`chatbot-semantic-layer.md`](../../../20-design/chatbot-semantic-layer.md) — **tài liệu duy nhất trong kho chưa qua kiểm chứng thực tế**.

---

## 0. Câu hỏi lát này phải trả lời

Tài liệu thiết kế tự khai bốn điều chưa biết. Lát 10 tồn tại để đóng ba trong bốn:

| Chưa biết | Lát 10 đóng bằng |
|---|---|
| **Skill có chịu được function calling không** (6 vòng test đều chạy *không* có công cụ) | chạy bộ hồi quy có function, so hình dạng câu trả lời |
| **Ai gọi function trước — skill hay bot** | quyết định bằng thiết kế: L1 nằm trong `system`, nạp trước mọi lượt, không bao giờ đến sau function |
| **Chi phí mỗi câu** | đo thật, ghi vào ledger |
| ~~Đơn vị của các mã chỉ tiêu~~ | đã giải trước lát này (729 mã, `don_vi_du_lieu`) |

**Phép kiểm chứng số một** vẫn giữ nguyên tinh thần của [`maintenance.md §6`](../../../30-skills/maintenance.md): 10 câu có đáp án xác định, chạy *có* function, 10/10 đúng **và** câu trả lời vẫn giữ hình dạng L1 thì hợp đồng đứng vững — xem §5 (bộ câu phải **dựng lại**, lý do ở §2.3).

## 1. Phạm vi

**Trong phạm vi**

1. 8 function dữ liệu + 1 function đọc tri thức L2, chạy dưới role `dlck_api`.
2. Một vòng chat chạy trong terminal (`python -m agent`), đủ để hỏi–đáp nhiều lượt.
3. System prompt gác phạm vi lĩnh vực (vá lỗ hổng đã đo ở vòng 5).
4. Nạp skill: L1 trọn vào `system`; L2 nạp theo nhu cầu qua function.
5. Dựng lại bộ hồi quy 10 câu **và lưu vào repo**.
6. Test seam theo TDD, gồm test chạy dưới đúng role production.
7. Cập nhật các tài liệu mà lát này làm cho sai (§9).

**Ngoài phạm vi — có lý do, không phải quên**

| Việc | Loại | Lý do |
|---|---|---|
| Endpoint HTTP / web chat | đã có đường khác | chủ dự án chốt: lát 10 chỉ terminal; `backend/api/` để nguyên |
| Streaming câu trả lời | đã kiểm — chưa đo | `stream` chưa từng đo với MiniMax; đo và dựng streaming là việc của lát API |
| Embedding / tìm kiếm khái niệm | đã có đường khác | chủ dự án chốt để sau; lát 10 dùng `tsvector` + trigram đã có |
| Chạy lưới phân loại cho 7.902 bài chưa nhãn | có chủ đích | chủ dự án: sẽ xoá sạch và backfill lại khi lên prod |
| Sửa ba ô thiếu trong cây ngành (ô tô/xe điện, holding, dịch vụ dầu khí) | có chủ đích | đổi cây kéo theo gán lại ~1.500 mã — chỉ chủ dự án quyết |
| Nạp 83 chỉ tiêu `GetScreenerParameters` vào `metric_dictionary` | đã có đường khác | việc của lát ETL, không phải lát này (ảnh hưởng: §4.5.3) |
| Đăng ký task Scheduler cho bất cứ thứ gì | có chủ đích | lát 10 không có job tự động |

## 2. Dữ kiện đã đo và giả định *(CLAUDE.md §4.8 bước 0)*

Nền dữ kiện đầy đủ nằm ở `scratchpad/slice10-facts.md` của phiên; phần dưới chỉ chép những gì **quyết định thiết kế**. Mọi số đo ngày **2026-09-06/07** trên kho dev.

### 2.1 Dữ kiện đã kiểm — kho dữ liệu

| # | Dữ kiện | Hệ quả thiết kế |
|---|---|---|
| F1 | `market.price_daily` 1.115.219 dòng, **chỉ cổ phiếu** (1.523 mã, 2002-04-18 → 2026-09-04). `close_adj`/`close_raw` đầy đủ 100 %; **`total_trading` và `total_trading_value` NULL** ở các dòng đã kiểm | `get_price_series` **không** trả khối lượng |
| F2 | Phiên 2026-09-04 chỉ có **335 mã** (lượt chạy dở); 2026-09-03 có 1.521 | mọi mốc kiểm chứng dùng **2026-09-03**, không dùng phiên mới nhất |
| F3 | 🔴 **VN-Index không có một điểm giá nào trong kho**: `price_daily` 0 dòng cho `security_type='index'`, `market.index_stat_daily` **0 dòng**, `asset.asset` chỉ có chỉ số quốc tế, `macro.indicator` không có. Danh tính 18 chỉ số có trong `market.security` nhưng rỗng dữ liệu | phải có hình dạng trả lời "**có mã, không có dữ liệu**" tách khỏi "không tìm thấy mã" (§4.6) |
| F4 | `market.financial_statement` **27.281.962 dòng**, PK `(issuer_id, year_report, length_report, statement_type, metric_code)`, `length_report` 1–4 = quý, **5 = cả năm**; `canonical_code` **NULL toàn bộ** | truy vấn luôn lọc `issuer_id` trước; bộ chỉ tiêu mặc định đóng (§4.5.2) |
| F5 | `market.metric_dictionary` 729 mã, `unit` nạp từ **`don_vi_du_lieu`**; phân bố: `VND` 582 · `ty_le_thap_phan` 80 · `lan` 46 · `VND/CP` 10 · `co_phieu` 8 · `so_luong` 1 · **NULL 2** | bảng quy đổi hiển thị §4.5.1; mã `unit` NULL bị loại khỏi kết quả |
| F6 | `market.screener_daily` **chỉ 2 ngày** (2026-09-03, 2026-09-04), payload hai nhánh `financial` (5 khoá) + `stockScreenerItem` (70 khoá) | `screen_stocks` đọc **ngày mới nhất có dữ liệu**, luôn trả kèm `ngay_du_lieu` |
| F7 | Mã tỷ số **có tên trong từ điển**: `rtd11` Vốn hóa (VND) · `rtd14` EPS (TTM) (VND/CP) · `rtd21` P/E (TTM) (lan) · `rtd25` P/B (TTM) (lan) · `rtd7` BVPS (VND/CP) · `rtq12` ROE (TTM) (ty_le_thap_phan) · `rtq14` ROA (TTM) | bộ chỉ tiêu mặc định của `screen_stocks`/`compare_peers` lấy đúng 7 mã này |
| F8 | ⚠️ `prf` = "Lợi nhuận ròng **(tỉ đồng)** (quý gần nhất)" nhưng `unit='VND'`; `rev` tương tự — **tên và đơn vị đá nhau, chưa giải** | loại `prf`/`rev` khỏi mọi đường hiển thị; ghi nợ (§8) |
| F9 | Cây ngành riêng: 6 nhóm × 24 ngành trong `market.industry`; đường đọc ngành của doanh nghiệp là view `market.v_issuer_industry` (`issuer_id, industry_id, source ∈ manual\|icb`) | `get_industry_tree` chỉ đọc hai chỗ này |
| F10 | `asset` chia **hai bảng**: `asset.price_daily` (commodity 49, fx 12, index 2) và `asset.ohlc_daily` (crypto 11, fx 17, index 37) | function chuỗi tài sản phải đọc **cả hai**, không chỉ một |
| F11 | `macro.indicator` 64 mã (`vn.cpi`, `vn.m2`, `us.yield.10y`…), `macro.observation` 90.801 dòng, có view `macro.observation_spliced` (chuỗi đã nối) | đọc qua view nối, không đọc bảng thô |
| F12 | `news.article` 8.132 bài (2025-04-06 → 2026-09-06), **230 có nhãn** (`classified_from='content'`), 7.902 NULL; `article_revision.tsv` là cột GENERATED; `article_industry` 222 dòng; `article_ticker` 508 dòng | `get_news` lọc nhãn chỉ khớp bài đã phân loại; tìm toàn văn chạy trên tất cả (§4.5.6) |
| F13 | 4 extension nằm trong schema `extensions`, **không phải `public`** | mọi SQL qualify `extensions.unaccent(...)`, `OPERATOR(extensions.%)` |

### 2.2 Dữ kiện đã kiểm — quyền và hạ tầng gọi model

| # | Dữ kiện | Hệ quả |
|---|---|---|
| G1 | `dlck_api` chỉ `SELECT` trên `market`/`macro`/`asset`/`news`; **không có USAGE trên `ops`**. User login duy nhất hiện có là `etl_worker` (thuộc `dlck_etl`) — **chưa có user nào thuộc `dlck_api`** | phải tạo user login mới + biến môi trường mới (§4.7) |
| G2 | `ops.llm_call` đã có cột `purpose` với chú thích sẵn `'news.classify' · lát 10: 'chat'` | ghi sổ chat đi bằng **kết nối thứ hai** dưới `ETL_DATABASE_URL`, không nới quyền `dlck_api` (§4.7) |
| G3 | SDK `anthropic==1.4.0`: `client.beta.messages.tool_runner(...)` **tồn tại**, nhận `system`, `thinking`, `tools`, `max_iterations` | dùng SDK, không tự viết vòng lặp |
| G4 | Đọc mã SDK `lib/tools/_beta_runner.py`: khi `stop_reason='tool_use'`, runner nối lượt sau bằng `append_messages(message, response)` với `message` là **nguyên văn** `{"role", "content"}` — **không bóc lại block**, tức `thinking.signature` được echo đúng | không phải tự chép logic serialize — đúng chỗ dễ hỏng im lặng |
| G5 | Đọc mã SDK: `self._iterator = self.__run__()` tạo **một lần** trong `__init__` và `return` khi `stop_reason='stop'` ⇒ **runner không tái dụng được cho lượt chat sau** | mỗi lượt người dùng dựng **runner mới**, truyền lại lịch sử do mình tự giữ |
| G6 | `append_messages()` và `generate_tool_call_response()` đều **public**; `__run__` bỏ qua bước tự nối khi `_messages_modified` đã bật | lặp tay giữ được lịch sử **mà không đụng field private** |
| G7 | MiniMax: ép công cụ + schema có enum ⇒ 0 lỗi schema/232 lời gọi. 🔴 **Trường mảng có thể rỗng phải TUỲ CHỌN, mặc định `[]`** — đặt `required` làm model bỏ hẳn khoá | mọi tham số mảng khai `list[...] = []` |
| G8 | Tokenizer tiếng Việt **1,62 ký tự/token**. L1 trọn 61.240 ký tự ≈ **37.802 token**; L2 trọn 243.545 ≈ 150.336 token | ngân sách §4.3 |
| G9 | Cache tự động chỉ trúng **≈ 50 %** khi chạy lô; giá pay-go $0,30/1M vào · $1,20/1M ra · $0,06/1M đọc cache | tính ngân sách theo token vào đầy đủ |
| G10 | Độ trễ lô phân loại adaptive: p50 8,0 s · p90 16,5 s · max 50 s | một câu chat nhiều lượt function có thể 30–60 s — chấp nhận, đây là terminal |
| G11 | 🔴 Mọi lượt chạy **nền/tách tiến trình** của job gọi model đều đóng băng; **tiền cảnh thì sạch**. Nguyên nhân gốc chưa xác định | bộ hồi quy chạy **tiền cảnh**, chia khối |

### 2.3 Hai phát hiện làm đổi tiêu chí nghiệm thu

**P1 — bộ 10 câu vòng 6 KHÔNG còn trong repo.** Đã `grep` toàn bộ `docs/` và `backend/`: chỉ còn *mô tả phương pháp* ở `maintenance.md §6` và một câu tóm tắt trong `CLAUDE.md`. Không có câu hỏi gốc, không có số liệu đầu vào, không có transcript. ⇒ **Không tái lập được bộ cũ.** Lát 10 dựng bộ mới, tự tính đáp án, và **lưu vào repo** để không mất lần nữa (§5).

**P2 — con số "FCFF phải ra 260 tỷ" không đối chiếu được.** `maintenance.md §6` ghi *"FCFF phải ra 260 tỷ, không phải 380"*, trong khi ví dụ DCF đầy đủ duy nhất còn trong repo (`valuation.md`, "Ví dụ 1") cho **FCFF = 270 tỷ** (600×0,8 + 180 − 330 − 60). Hai số khác nhau vì gần như chắc chắn câu test vòng 6 dùng số liệu khác ví dụ trong skill — đúng cách làm, nhưng số liệu đó đã mất. ⇒ **Không sửa 260 thành 270** (sửa số mà không đo là nói dối, §1.2); ghi chú vào `maintenance.md` rằng con số này không tái lập được và bộ mới ở §5 thay thế vai trò của nó.

### 2.4 Giả định — chưa kiểm

| # | Giả định | Kiểm thế nào, khi nào |
|---|---|---|
| A1 | `tool_runner` (đi qua `beta.messages.parse`, kèm header helper của SDK) chạy được với MiniMax **trong hình dạng lát 10 dùng** (9 tool, system 2 block, thinking adaptive) | **Task đầu tiên của plan** là một lượt gọi thật nhỏ; hỏng thì đổi sang vòng lặp `messages.create` tay trước khi xây tiếp |
| A2 | Chèn câu nhắc "quay lại mạch L1" vào cùng lượt `tool_result` giúp giữ hình dạng câu trả lời | đo ở bộ hồi quy: chạy 10 câu **có** nhắc; nếu ≥ 1 câu hỏng hình dạng thì chạy lại **không** nhắc để biết nhắc có tác dụng hay không |
| A3 | Model tự biết gọi `load_knowledge_reference` khi cần công thức | đo ở bộ hồi quy nhóm A: 6 câu tính toán bắt buộc phải chạm L2; đếm số lần model gọi |
| A4 | ~10 lượt chat/ngày khi dev không làm cạn cửa sổ Token Plan | quan sát `token_plan_remains()` in ra cuối mỗi lượt |

## 3. Ba phương án và quyết định *(CLAUDE.md §4.8)*

Ba phương án sinh **độc lập, song song** bởi ba subagent Sonnet trên cùng fact pack, mỗi phương án tối ưu một trục khác và tự khai rủi ro của chính nó. Bản đầy đủ: `scratchpad/option-{A,B,C}.md`.

| | **A — tối giản (YAGNI)** | **B — bán kính hỏng nhỏ, kiểm chứng được** | **C — chất lượng câu trả lời** |
|---|---|---|---|
| Cây file | 5 file phẳng, ~600 dòng | `db`/`knowledge`/`llm_log`/`chat`/`cli` + `tools/` 9 file, tách seam tối đa | ~19 file, tách theo "mỗi chỗ dễ giấu một loại lỗi" |
| Vòng chat | `tool_runner.until_done()` | `tool_runner`, mock qua `httpx2.MockTransport` | `tool_runner`, **lặp tay**, chèn nhắc quay-lại-L1 vào lượt `tool_result` |
| Dữ liệu trả model | JSON thô, giữ mã chỉ tiêu | JSON + view mới `market.v_screener_latest` | dịch mã → `name_vi`, quy đổi đơn vị, cờ tường minh cho ba trạng thái "không có" |
| Quyền DB | `SET LOCAL ROLE dlck_api` trên `etl_worker` (cần `GRANT dlck_api TO etl_worker`) | user login mới + **role mới `dlck_chatlog`** chỉ INSERT 1 bảng | user login mới + **migration nới `INSERT ops.llm_call` cho `dlck_api`** |
| Bộ hồi quy | chạy tay, không lưu | script ngoài pytest, lưu hồ sơ | dựng lại bộ câu, rubric 2 lớp (số + hình dạng) |
| Tự khai rủi ro nặng nhất | quên gọi `api_conn()` ⇒ âm thầm chạy full quyền `dlck_etl` | 2 engine + role mới có thể là trừu tượng thừa nếu lát API không tới | prompt phình, chi phí/độ trễ chưa đo |

**Chấm theo tiêu chí viết trước** (mục §0 + luật dự án):

1. *Trả lời được câu hỏi lớn của lát* — cả ba đạt.
2. *Tuân luật đã có, không phải tuỳ chọn* — `market-data-store §6.2` cấm phơi mã thô cho LLM; `metric_dictionary.unit` là đơn vị thật còn nhãn API sai. **Chỉ C tuân**; A cố tình bỏ (trả JSON thô), B không đặt trọng tâm ở đó.
3. *§3.5 test dưới đúng quyền production* — B mạnh nhất, C đạt, **A vi phạm tinh thần**: production và test dùng chung user `etl_worker`, đúng/sai phụ thuộc lập trình viên nhớ gọi `api_conn()` — chính A tự khai.
4. *Tối giản §4.4.2* — A mạnh nhất, C nặng nhất, B ở giữa nhưng thêm **role mới + view mới + migration** cho nhu cầu chưa chứng minh.
5. *Bán kính rollback* — cả ba đều là code mới trong thư mục mới, `git revert` gỡ được; B và C thêm thay đổi DB nên nhỉnh hơn về rủi ro.

**Chọn C.** Lý do: câu hỏi lớn của lát là *chất lượng hợp đồng*, và C là phương án duy nhất tôn trọng luật đã có về trình bày dữ liệu — nếu đổ `rtq12: 0.17377625` vào model thì thí nghiệm hỏng vì một lý do tầm thường, không phải vì hợp đồng sai. C cũng là phương án đọc kỹ nhất phần hợp đồng tri thức: nó tìm ra P1 và P2 ở §2.3, hai lỗ hổng nghiệm thu mà hai phương án kia không thấy.

**Loại A** vì nó cắt đúng những thứ lát này tồn tại để kiểm chứng (hình dạng dữ liệu người-đọc-được, hồ sơ bộ hồi quy), và để lại cái bẫy quyền mà chính nó tự khai.
**Loại B** vì nó tối ưu cho thế giới nhiều consumer (2 engine, role mới, view mới, 9 file `tools/`) trong khi lát 10 chỉ có **một** consumer là vòng chat terminal. Giữ nguyên bản B làm tham chiếu cho lát API.

**Mượn từ phương án khác — nói rõ mượn gì:**

| Mượn | Từ | Vì sao C vẫn đứng vững |
|---|---|---|
| Seam test **đầu tiên** là test quyền (`engine đọc được dưới `dlck_api``), không phải test format | B | không đụng thiết kế C, chỉ đổi **thứ tự** TDD — đặt cái đắt nhất khi sai lên trước |
| Lưu kết quả bộ hồi quy thành hồ sơ trong `docs/90-records/` để lượt sau so được | B | C đã có bộ câu; thêm chỗ lưu là bổ sung thuần |
| **Bỏ hẳn migration nới quyền `ops.llm_call` cho `dlck_api`**; ghi sổ bằng kết nối thứ hai dưới `ETL_DATABASE_URL` sẵn có | A (kết nối riêng) | giữ `dlck_api` đúng hợp đồng "chỉ đọc", **không thêm migration nào trong lát 10**. Điều kiện đảo ngược ở dưới |

**Điều kiện đảo ngược** — quan sát được, không phải cảm tính:

| Nếu | Thì xét lại |
|---|---|
| A1 sai: `tool_runner` không chạy với MiniMax trong hình dạng lát 10 | đổi sang vòng lặp `messages.create` tay, tự echo `thinking` + `signature` (task 1 của plan là chỗ phát hiện) |
| Chi phí thật > 3 lần ước lượng §4.3, hoặc một câu > 60 s | cắt L1 xuống chỉ `SKILL.md` + nạp references theo nhu cầu (đổi quyết định #4 của chủ dự án — phải hỏi) |
| Bộ hồi quy < 10/10 số đúng, hoặc ≥ 2/10 hỏng hình dạng L1 | dừng, không mở rộng; đây chính là kết quả lát cần biết, báo chủ dự án |
| Lát API được dựng và cần ghi `ops.llm_call` từ tiến trình chỉ-đọc | tách role `dlck_chatlog` chỉ INSERT một bảng theo hướng phương án B |

## 4. Thiết kế

### 4.1 Cây file

```
backend/agent/
├── __init__.py                     package marker
├── __main__.py                     entry `python -m agent`: nạp .env, dựng LLMClient + 2 engine, chạy REPL, đóng sạch ở finally
├── system_prompt.py                SCOPE_GUARD (nguyên văn maintenance.md §7) + build_system_blocks()
├── skills.py                       nạp trọn L1 lúc khởi động (thiếu file ⇒ raise ngay); bảng 9 khoá L2 → Path
├── db.py                           engine đọc (AGENT_DATABASE_URL, role dlck_api) + engine sổ (ETL_DATABASE_URL); context manager giao dịch ngắn
├── format.py                       display_metric(value, unit), format_vnd, format_date_vi, metric_name_vi()
├── llm_log.py                      ghi 1 dòng ops.llm_call mỗi lượt model; lỗi ghi sổ KHÔNG được làm sập chat
├── chat.py                         vòng REPL nhiều lượt: dựng runner mỗi lượt, lặp tay, chèn nhắc, in kết quả
└── tools/
    ├── __init__.py                 TOOLS = [...] — 9 BetaFunctionTool
    ├── _shared.py                  resolve_ticker(), cap_limit(), ba khuôn "không có dữ liệu"
    ├── screen_stocks.py
    ├── get_financials.py
    ├── get_price_series.py
    ├── get_corporate_events.py
    ├── compare_peers.py
    ├── get_news.py
    ├── get_industry_tree.py
    ├── get_macro_series.py
    └── load_knowledge_reference.py
```

Ranh giới: `tools/*` **chỉ** nhận kết nối đã mở và trả `dict` thuần — không biết gì về model, không tự mở kết nối. `chat.py` **chỉ** lắp ráp — không chứa SQL. `format.py` là hàm thuần, không chạm DB trừ `metric_name_vi()` (nhận sẵn bảng tra đã nạp một lần).

### 4.2 Vòng chat

Dùng `client.beta.messages.tool_runner`, **không** gọi `.until_done()`, lặp tay:

```python
runner = llm.raw.beta.messages.tool_runner(
    model=settings.model, max_tokens=4000, system=build_system_blocks(),
    messages=history, tools=TOOLS, thinking={"type": "adaptive"}, max_iterations=8,
)
for message in runner:
    log_llm_call(ops_conn, message, purpose="chat")
    if message.stop_reason == "tool_use":
        response = runner.generate_tool_call_response()
        if response is not None:
            response["content"] = [*response["content"], {"type": "text", "text": REMINDER}]
            runner.append_messages(message, response)
```

- **Vì sao dùng SDK** (G4): runner echo nguyên văn block `thinking` kèm `signature`; tự viết là tự chép lại đúng chỗ hỏng im lặng mà dự án đã trả giá (§3.4).
- **Vì sao lặp tay** (G6): `until_done()` là hộp đen, mất chỗ chen nội dung. Hai lượt `user` liên tiếp không hợp lệ trên Messages API ⇒ cách hợp lệ duy nhất để nhắc model là **thêm một block `text` vào cùng mảng `content` của lượt `tool_result`**.
- **Nhiều lượt chat** (G5): runner không tái dụng được. `chat.py` tự giữ `history` và dựng runner mới mỗi lượt người dùng. Lịch sử lấy từ chính các message đi qua vòng lặp (`append_messages` là public), **không đọc `_params`**.
- `max_iterations=8` là trần cứng chống vòng gọi function vô hạn — **không phải số đã đo**; chạm trần thì báo lỗi rõ ràng cho người dùng, không treo.
- `REMINDER` ≈ 350 ký tự (≈ 215 token), chỉ thêm ở lượt **có gọi function**. Nội dung: dùng đúng số vừa tra (không lấy số ví dụ trong tài liệu), giữ hình dạng L1, không lộ mã chỉ tiêu thô.

### 4.3 System prompt và nạp skill

`system` là **list 2 block**: `[SCOPE_GUARD, L1_TOÀN_VĂN]`.

- `SCOPE_GUARD` chép **nguyên văn** ba đoạn ở `maintenance.md §7` — không diễn giải lại. Nó gác câu ngoài lĩnh vực *trước khi* bất cứ skill nào có tiếng nói.
- `L1_TOÀN_VĂN` = `vn-stock-advisor/SKILL.md` + 4 file `references/` nối theo thứ tự cố định, mỗi file có tiêu đề phân cách. **61.240 ký tự ≈ 37.802 token.** Đặt trong `system` (không phải lượt `user` đầu) vì `system` không bị lượt sau đè và đứng trước mọi `tool_result` — đúng yêu cầu "L1 không bao giờ đến sau function".
- L2 nạp qua function `load_knowledge_reference(topic)`, `topic` là **enum đóng 9 giá trị**; mô tả function liệt kê 9 chủ đề kèm một dòng nội dung để model biết khi nào cần gọi.

**Ngân sách một câu** (tỷ lệ 1,62 ký tự/token, giá pay-go, cache coi như 0):

| Thành phần | Token | $ |
|---|---:|---:|
| `system` (SCOPE_GUARD + L1) | ≈ 38.100 | 0,0114 |
| Định nghĩa 9 tool | ≈ 1.200 | 0,0004 |
| Một file L2 nếu model gọi (trung bình 27.000 ký tự) | ≈ 16.700 | 0,0050 |
| Kết quả function + nhắc (3 lượt) | ≈ 2.500 | 0,0008 |
| Đầu ra (thinking + trả lời) | ≈ 1.500 | 0,0018 |
| **Cộng — câu không chạm L2** | **≈ 43.300** | **≈ 0,014** |
| **Cộng — câu có chạm L2** | **≈ 60.000** | **≈ 0,019** |

Con số này là **ước lượng**, phải thay bằng số đo thật ở ledger sau khi chạy bộ hồi quy (AC7).

### 4.4 Hợp đồng 9 function

Quy ước chung, áp cho cả 9:

- Tham số mảng: khai `list[...] = []` (G7). Không bao giờ `required` cho mảng có thể rỗng.
- Trả `dict` JSON-serializable, khoá tiếng Việt không dấu (`ma`, `ten`, `gia_tri`, `ngay`), **không bao giờ có khoá là mã chỉ tiêu thô**.
- Mọi kết quả kèm `ngay_du_lieu` hoặc `khoang_ngay` để model biết số thuộc thời điểm nào.
- `limit` mặc định nhỏ, có trần cứng; vượt trần thì cắt và ghi `da_cat: true`.

| # | Function | Tham số | Nguồn | Trần |
|---|---|---|---|---|
| 1 | `screen_stocks` | `criteria: list[{metric_code, operator, value}] = []`, `industry_code: str\|None`, `exchange: 'HOSE'\|'HNX'\|'UPCOM'\|None`, `sort_by: str\|None`, `limit: int = 20` | `screener_daily` (ngày mới nhất) ⋈ `security` ⋈ `v_issuer_industry` | limit ≤ 50 |
| 2 | `get_financials` | `ticker: str`, `statement_type: 'BS'\|'IS'\|'CF' = 'IS'`, `from_year: int`, `to_year: int`, `period: 'nam'\|'quy' = 'nam'`, `metric_codes: list[str] = []` | `financial_statement` ⋈ `metric_dictionary` | ≤ 8 năm; `metric_codes=[]` ⇒ bộ mặc định §4.5.2 |
| 3 | `get_price_series` | `ticker: str`, `from_date: str`, `to_date: str`, `adjusted: bool = True` | `price_daily` | ≤ 400 phiên |
| 4 | `get_corporate_events` | `ticker: str`, `event_type: str\|None`, `from_date: str\|None`, `limit: int = 20` | `corporate_event` | limit ≤ 50 |
| 5 | `compare_peers` | `tickers: list[str] = []`, `metric_codes: list[str] = []`, `industry_code: str\|None` | `screener_daily` ngày mới nhất | ≤ 10 mã, ≤ 8 chỉ tiêu |
| 6 | `get_news` | `query: str\|None`, `ticker: str\|None`, `group_no: int\|None`, `sub: str\|None`, `industry_code: str\|None`, `from_date: str\|None`, `to_date: str\|None`, `limit: int = 10` | `article` ⋈ `article_revision` (+ `article_ticker`/`article_industry` khi lọc nhãn) | limit ≤ 30 |
| 7 | `get_industry_tree` | `industry_code: str\|None`, `ticker: str\|None` | `industry`, `v_issuer_industry` | — |
| 8 | `get_macro_series` | `code: str\|None`, `keyword: str\|None`, `from_date: str\|None`, `to_date: str\|None`, `limit: int = 60` | `macro.observation_spliced` ⋈ `macro.indicator`; `asset.price_daily` **và** `asset.ohlc_daily` ⋈ `asset.asset` | limit ≤ 200 |
| 9 | `load_knowledge_reference` | `topic: Literal[9 giá trị]` | file trong `agent/skills/vn-stock-knowledge/` | — |

Ghi chú bắt buộc:

- **#7 không có tham số `icb_level`.** Cây ICB không bao giờ ra tới model (quyết định đã chốt #3). Trả kèm `nguon_gan: 'manual'\|'icb'` từ view để model biết độ tin của phép gán — đây là *siêu dữ liệu về phép gán*, không phải cây ICB.
- **#8 `code=None, keyword=...`** ⇒ trả **danh mục** chuỗi khớp (mã + tên + đơn vị + khoảng ngày có dữ liệu), không trả số. Đây là cách model tìm mã trước khi hỏi số, thay cho việc nhồi 192 mã vào system prompt.
- **#9 `topic`** là `Literal` 9 giá trị cố định, tra `dict` hằng → `Path`. **Không nối chuỗi từ đầu vào**, nên path traversal không khả dĩ về mặt cấu trúc; vẫn có test chứng minh (`../../../etc/passwd` bị từ chối ở tầng schema).

### 4.5 Quy ước trình bày dữ liệu

#### 4.5.1 Đơn vị — bảng quy đổi đóng, theo `metric_dictionary.unit`

| `unit` | Hiển thị | Ví dụ |
|---|---|---|
| `VND` | ≥ 1 tỷ ⇒ "x,y tỷ VND" (1 chữ số thập phân); nhỏ hơn ⇒ "n đ" | `62848794351367` → `"62.848,8 tỷ VND"` |
| `ty_le_thap_phan` | ×100, 2 chữ số, hậu tố `%` | `0.17377625` → `"17,38%"` |
| `lan` | 2 chữ số, hậu tố ` lần` | `7.85` → `"7,85 lần"` |
| `VND/CP` | số nguyên có phân cách, hậu tố ` đ/cp` | `2749.91` → `"2.750 đ/cp"` |
| `co_phieu` | số nguyên có phân cách, hậu tố ` cp` | |
| `so_luong` | số nguyên có phân cách | |
| `NULL` (2 mã) | **loại khỏi kết quả** | |

Ngày: luôn kèm cả `"ngay": "2026-09-03"` (ISO, để model so sánh) và `"ngay_hien_thi": "03/09/2026"`.

#### 4.5.2 Bộ chỉ tiêu mặc định

`get_financials` khi `metric_codes=[]` trả đúng bộ đóng sau (đã kiểm có tên trong từ điển và có dữ liệu thật):

- `IS`: `isa3` Doanh số thuần · `isa9` Chi phí bán hàng · `isa10` Chi phí quản lý doanh nghiệp · `isa16` Lãi/(lỗ) ròng trước thuế · `isa22` LỢI NHUẬN THUẦN · `isa23` Lãi cơ bản trên cổ phiếu
- `BS`: `bsa1` TÀI SẢN NGẮN HẠN · `bsa2` Tiền và tương đương tiền · `bsa53` TỔNG TÀI SẢN · `bsa54` NỢ PHẢI TRẢ · `bsa78` VỐN CHỦ SỞ HỮU · `bsa96` TỔNG CỘNG NGUỒN VỐN
- `CF`: `cfa18` Lưu chuyển tiền thuần từ hoạt động kinh doanh

`screen_stocks` / `compare_peers` khi `metric_codes=[]` trả: `rtd11` Vốn hóa · `rtd14` EPS (TTM) · `rtd21` P/E (TTM) · `rtd25` P/B (TTM) · `rtd7` BVPS · `rtq12` ROE (TTM) · `rtq14` ROA (TTM).

🔴 `prf` và `rev` **bị loại khỏi mọi đường hiển thị** (F8: tên nói "tỉ đồng", `unit` nói `VND` — chưa giải).

#### 4.5.3 Mã không tra được tên

Chỉ tiêu không có trong `metric_dictionary` ⇒ **loại khỏi kết quả**, không đưa mã thô ra kèm giải thích. `screen_stocks` chỉ chấp nhận `metric_code` tra được tên; mã lạ trả lỗi rõ ràng liệt kê các mã hợp lệ gần nhất.

#### 4.5.4 `get_news` — hai đường lọc

- `query` ⇒ tìm toàn văn trên `article_revision.tsv` (cột GENERATED, chạy trên **cả 8.132 bài**).
- `ticker`/`group_no`/`sub`/`industry_code` ⇒ lọc theo nhãn, **chỉ khớp bài đã phân loại**.
- Mỗi bài trả kèm `da_phan_loai: bool`. Khi lọc theo nhãn mà kết quả rỗng trong lúc kho còn nhiều bài chưa nhãn, trả thêm `ghi_chu` nói rõ có bao nhiêu bài chưa phân loại trong khoảng ngày đó — để model không kết luận "không có tin nào".
- Khi backfill xong (mọi bài có nhãn), `da_phan_loai` luôn `true` và `ghi_chu` biến mất **mà không phải sửa code**.

### 4.6 Ba hình dạng "không có dữ liệu"

Phân biệt bằng trường tường minh, **không** bằng độ dài mảng:

| Tình huống | Trả về |
|---|---|
| Mã không tồn tại trong `market.security` | `{"tim_thay": false, "ma_da_tra": "XYZ", "goi_y": [...]}` — gợi ý từ khớp mờ `news.trade_name`/ticker gần giống |
| Mã tồn tại nhưng **loại chứng khoán này không có dữ liệu** (VN-Index, ETF khi hỏi giá) | `{"tim_thay": true, "co_du_lieu": false, "ly_do": "kho chưa có dữ liệu giá cho chỉ số", "loai": "index"}` |
| Mã và loại đều đúng, khoảng ngày rỗng | `{"tim_thay": true, "co_du_lieu": true, "so_dong": 0, "khoang_co_du_lieu": {"tu": "...", "den": "..."}}` |
| Mã đã huỷ niêm yết | trả dữ liệu kèm `trang_thai: "delisted"` — không giấu, nhưng model biết mà nói rõ |

### 4.7 Quyền DB và sổ `ops.llm_call`

- **Đường đọc dữ liệu**: user login mới `agent_reader LOGIN IN ROLE dlck_api`, biến `AGENT_DATABASE_URL` trong `.env`. Tạo user là việc **per-môi-trường, ngoài migration** (đúng khuôn `database/README`). Mật khẩu sinh ngẫu nhiên, ghi thẳng vào `.env`, **không in ra output, không commit**.
- **Đường ghi sổ**: kết nối thứ hai dùng `ETL_DATABASE_URL` sẵn có, **chỉ** để `INSERT INTO ops.llm_call`. Không migration, không role mới, `dlck_api` giữ đúng hợp đồng "chỉ đọc".
- Lỗi ghi sổ bị nuốt (in stderr), **không bao giờ làm sập cuộc chat** — sổ là phụ, chat là chính.
- **Không có migration nào trong lát 10.** Migration head giữ nguyên `0020`.

## 5. Bộ hồi quy dựng lại — 10 câu, đáp án độc lập

Lưu tại `docs/90-records/plans/2026-09-07-semantic-layer/regression-round7.md` (gọi là **vòng 7** vì bộ vòng 6 đã mất, §2.3 P1 — không giả vờ là bộ cũ).

### 5.1 Nhóm A — 6 câu tính toán thuần, đáp án tính tay

Số liệu tự đặt, **khác** ví dụ trong `valuation.md` (để không đo trí nhớ chép lại). Phép tính ghi kèm để người sau kiểm được.

| # | Câu hỏi (rút gọn) | Phép tính | Đáp án |
|---|---|---|---|
| A1 | EBIT 800 tỷ, thuế 20%, khấu hao 200, đầu tư vốn gộp 250, đầu tư vốn lưu động mới 90 → FCFF? | 800×0,8 + 200 − 250 − 90 | **500 tỷ** |
| A2 | LNST 520, khấu hao 200, đầu tư vốn 250, vốn lưu động mới 90, **nợ dài hạn mới 80** → FCFE? | 520 + 200 − 250 − 90 + 80 | **460 tỷ** |
| A3 | Rf 5%, beta 1,1, phần bù 8%, lãi vay 9%, thuế 20%, vốn hoá 3.000, nợ vay 2.000 → WACC? | rE = 5+8,8 = 13,8%; rD sau thuế = 7,2%; 0,6×13,8 + 0,4×7,2 | **11,16%** |
| A4 | FCFE 460, g 5%, r 13,8%, 200 triệu cp → giá trị vốn chủ và giá mỗi cp? | 460×1,05/(0,138−0,05) = 483/0,088 | **5.488,6 tỷ → 27.443 đ/cp** |
| A5 | LNST 300, doanh thu 2.500, tổng tài sản 4.000, vốn chủ 1.500 → ROE theo Dupont, tách 3 thành phần? | 12% × 0,625 × 2,667 (kiểm chéo 300/1.500) | **20,0%** |
| A6 | LNST 480 tỷ, 240 triệu cp, giá 30.000 → EPS và P/E; phát hành thêm 60 triệu cp, LNST không đổi → EPS và P/E mới? | 2.000 đ / 15,0; rồi 1.600 đ / 18,75 | **2.000 đ · 15,0 → 1.600 đ · 18,75** |

Bẫy cài sẵn: A2 bắt được lỗi dùng công thức FCFF cho FCFE (ra 500) hoặc trừ thay vì cộng nợ mới (ra 300) — đúng vai trò mà câu FCFF của vòng 6 từng giữ.

### 5.2 Nhóm B — 4 câu bắt buộc phải gọi function, đáp án lấy từ kho (đã chạy SQL 2026-09-07)

| # | Câu hỏi | Đáp án đúng | Nguồn |
|---|---|---|---|
| B1 | Giá đóng cửa HPG phiên **2026-09-03**? | **21.600 đ** (`close_raw` = `close_adj`) | `price_daily` |
| B2 | VCB thuộc ngành nào trong bộ ngành của dự án? | **Ngân hàng và Tín dụng** (`NGANHANG`), nhóm **Dịch vụ Tài chính** (`TAICHINH`), nguồn gán `icb` | `v_issuer_industry` ⋈ `industry` |
| B3 | Doanh số thuần và lợi nhuận thuần của FPT năm 2024? | **62.848,8 tỷ VND** và **7.856,8 tỷ VND** | `financial_statement` `isa3`/`isa22`, `year_report=2024`, `length_report=5` |
| B4 | CPI Việt Nam mới nhất là bao nhiêu, của tháng nào? | **4,45%**, tháng **8/2026** | `macro.observation` ⋈ `indicator` `vn.cpi` |

### 5.3 Chấm hai lớp

**Lớp 1 — số:** đúng/sai tuyệt đối, sai số cho phép ±0,5 % cho câu chia (A3, A4, A6). 10/10 mới đạt.

**Lớp 2 — hình dạng L1:** mỗi câu chấm 5 mục, đạt khi **≥ 4/5** và **không câu nào** vi phạm mục 5:

1. Có mạch lập luận, không phải bảng số trần.
2. Kết luận có điều kiện (nêu điều kiện làm kết luận đổi), không phán chắc nịch.
3. Nêu rõ số nào là số tra được, số nào là giả định.
4. Không khuyến nghị mua/bán cụ thể.
5. 🔴 **Không lộ mã chỉ tiêu thô** (`rtq12`, `isa3`, `bsa53`…) trong câu trả lời cho người dùng.

**Cách chấm:** subagent **Sonnet** độc lập, nhận câu hỏi + đáp án + rubric, **không** biết câu trả lời đến từ đâu. Chạy **tiền cảnh, chia khối** (G11). Kết quả (10 transcript + bảng chấm) lưu cạnh spec.

## 6. Seam test và thứ tự TDD

Seam = ranh giới public mà caller thật đi qua. Chốt tại đây, không test internals.

| # | Seam | Test đỏ đầu tiên của seam |
|---|---|---|
| S1 | `agent.db.read_engine()` — kết nối đọc dưới role `dlck_api` | `test_read_engine_runs_as_dlck_api`: `SELECT current_user, current_role` trả role có `dlck_api`; và một `INSERT` vào `market.industry` **bị từ chối** |
| S2 | `format.display_metric(value, unit)` | `test_display_metric_ty_le_thap_phan`: `(0.17377625, 'ty_le_thap_phan')` → `"17,38%"`; `(62848794351367, 'VND')` → `"62.848,8 tỷ VND"`; `(None, 'VND')` → `None` |
| S3 | `system_prompt.build_system_blocks()` | `test_system_blocks_scope_guard_first`: block[0] chứa nguyên văn câu "chỉ trả lời trong lĩnh vực chứng khoán, tài chính và kinh tế"; block[1] chứa tiêu đề thật của L1; **không** chứa tiêu đề của L2 |
| S4 | Từng function trong `tools/` (8 test file) | mỗi function ≥ 1 test giá trị đúng (expected lấy từ §5.2 hoặc SQL chạy tay ghi trong test), ≥ 1 test biên/không-có-dữ-liệu |
| S5 | `tools.load_knowledge_reference` | `test_reject_path_traversal`: `topic="../../../etc/passwd"` bị từ chối ở tầng schema; `topic="valuation"` trả nội dung bắt đầu bằng tiêu đề thật của file |
| S6 | `chat.run_turn(...)` với model giả | `test_tool_result_carries_reminder`: model giả phát 1 `tool_use` → lượt gửi lại chứa cả `tool_result` **và** block text nhắc; `test_history_survives_two_turns`: lượt 2 thấy được nội dung lượt 1 |
| S7 | `llm_log.log_llm_call` | `test_log_written_under_etl_role` (role thật); `test_log_failure_does_not_break_chat`: kết nối sổ hỏng ⇒ hàm vẫn trả bình thường |

**Thứ tự TDD (mượn từ B):** S1 trước tiên — sai quyền thì mọi thứ khác vô nghĩa và sai muộn thì đắt. Rồi S2, S3 (hàm thuần, nhanh), S5, sau đó S4 từng function một (mỗi function một vòng đỏ→xanh), cuối cùng S6, S7.

**Mock model:** dùng lại đúng khuôn `httpx2.MockTransport` đã có ở `backend/tests/core/test_llm_client.py` — không gọi API thật trong test. Bộ hồi quy §5 là thứ **duy nhất** gọi model thật, và nó không nằm trong `pytest`.

## 7. Tiêu chí nghiệm thu

| AC | Nội dung | Cách kiểm |
|---|---|---|
| **AC1** | `tool_runner` chạy được với MiniMax trong hình dạng lát 10 | một lượt gọi thật, model gọi ít nhất 1 function và trả lời — dán output vào ledger |
| **AC2** | Toàn bộ test cũ **877 passed, 2 skipped** vẫn xanh, cộng test mới | `uv run --project backend pytest -q`, dán số thật |
| **AC3** | Đường đọc chạy dưới `dlck_api`, và role đó **không ghi được** | test S1 xanh |
| **AC4** | Cả 9 function trả đúng dữ liệu thật cho ít nhất một câu hỏi mẫu | test S4 xanh + một lượt chat thật chạm ≥ 5 function |
| **AC5** | Câu ngoài lĩnh vực bị từ chối gọn trong một câu | hỏi 4 câu ngoài phạm vi (sức khoẻ, pháp lý, lập trình, nấu ăn) — 4/4 bị từ chối, dán transcript |
| **AC6** | Hỏi "VN-Index hôm nay bao nhiêu điểm" ⇒ model **nói thẳng là kho chưa có**, không bịa, không thay bằng chỉ số khác | transcript |
| **AC7** | Bộ hồi quy §5: **10/10 số đúng**, và ≥ 9/10 câu đạt hình dạng L1 (≥ 4/5 mục, không câu nào vi phạm mục 5) | bảng chấm lưu cạnh spec |
| **AC8** | Chi phí và độ trễ thật mỗi câu được đo và ghi | đọc `ops.llm_call` sau bộ hồi quy: token vào/ra p50, độ trễ p50/p90, $ quy đổi |
| **AC9** | Tài liệu §9 đã cập nhật, `git grep` không còn chỗ đá nhau | chạy phép kiểm §1.7, dán kết quả |

AC7 **không phải cổng chặn merge**: nếu bộ hồi quy cho kết quả xấu thì đó chính là **phát hiện của lát**, phải báo nguyên trạng cho chủ dự án, không được sửa cho đẹp.

## 8. Nợ và rủi ro

**Nợ mới sinh trong lát này**

| Nợ | Vì sao hoãn |
|---|---|
| `prf`/`rev` có tên "(tỉ đồng)" nhưng `unit='VND'` — chưa giải, đang bị loại khỏi hiển thị | phải đối chiếu giá trị thật với BCTC; việc của lát ETL |
| 83 chỉ tiêu `GetScreenerParameters` chưa nạp vào `metric_dictionary` ⇒ một phần 70 khoá screener không tra được tên | việc của lát ETL |
| Ghi `ops.llm_call` đi bằng kết nối `dlck_etl` — đúng cho tiến trình terminal, **không** đúng cho service | lát API tách role `dlck_chatlog` |
| `max_iterations=8` là số chọn, chưa đo | đo sau khi có nhiều lượt chat thật |

**Nợ mang sang từ lát 9** (không giải trong lát này): `x` recall 81 % · `1a`↔`1b` còn nhầm · ba ô thiếu trong cây ngành · job gọi model chạy nền bị đóng băng.

**Rủi ro lớn nhất của lát:** A1 sai — `tool_runner` không hợp với MiniMax ở hình dạng này. Đặt nó thành **task số 1** của plan chính là để rủi ro này lộ ra khi chưa xây gì.

## 9. Tài liệu phải cập nhật cùng lượt *(CLAUDE.md §1.6, §1.7)*

| File | Sửa gì |
|---|---|
| `docs/20-design/chatbot-semantic-layer.md` | bỏ trạng thái "chưa duyệt"; `get_industry_tree` bỏ `icb_level`; 8 → 9 function; chép hợp đồng thật đã dựng; đóng 3 trong 4 "điều chưa biết" bằng số đo |
| `docs/20-design/market-data-store.md` §6.3 | đồng bộ danh sách function; ghi rõ ví dụ view §6.2 dùng tên bảng cũ (`organization`) đã đổi từ spec 2026-08-25 |
| `docs/30-skills/maintenance.md` §6 | ghi chú: bộ vòng 6 không tái lập được, con số "FCFF 260" không đối chiếu được; trỏ sang bộ vòng 7 mới |
| `docs/00-overview/roadmap.md` | đóng lát 10, viết "Điểm vào cho lát 11" |
| `database/README.md` | thêm user login `agent_reader IN ROLE dlck_api` vào mục per-môi-trường |
| `docs/90-records/README.md` | thêm hồ sơ plan mới vào index |
| `.env` | thêm `AGENT_DATABASE_URL` (giá trị không bao giờ in ra) |

## 10. Điều chủ dự án cần biết

1. **Bộ 10 câu vòng 6 đã mất** — không tái lập được. Lát 10 dựng bộ mới (vòng 7) và lưu vào repo. Con số "FCFF 260 tỷ" trong tài liệu không đối chiếu được với bất cứ thứ gì còn lại; **không sửa nó**, chỉ ghi chú.
2. **VN-Index chưa có trong kho.** Chatbot sẽ nói thẳng là chưa có. Muốn trả lời được thì cần một lát ETL riêng cho chỉ số — chưa nằm trong lộ trình.
3. Lát 10 **không thêm migration nào** và **không bật job tự động nào**.
4. Cần tạo một user Postgres mới trên máy dev (`agent_reader`) — mật khẩu sinh ngẫu nhiên, ghi vào `.env`, không in ra.
