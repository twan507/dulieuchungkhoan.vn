# Review trục SPEC — lát 10, nhánh `feat/semantic-layer`

**Phạm vi:** `git diff 56743b0..4ff1e62` (18 commit) · thước đo: `spec.md`, `plan.md`, `ledger.md`, `round7-results-2026-09-07.md`
**Ngày review:** 2026-09-07 · **Reviewer:** độc lập, chỉ đọc + chạy test, không sửa repo
**Đã chạy lại để tự kiểm:** `pytest tests -q` (toàn bộ), `pytest tests/agent -q`, dump `input_schema` của 9 tool, và gọi thẳng 4 function trên kho dev bằng `AGENT_DATABASE_URL` (chỉ đọc).

> ⚠️ **Hồ sơ đổi giữa lượt review.** Trong lúc tôi viết, `round7-results`, `regression-round7`, `roadmap.md`, `90-records/README.md` được sửa và thêm `round7-grading-v2-2026-09-07.md` (chưa commit, nằm trên `4ff1e62`): rubric lớp 2 được sửa, **chấm lại cả 15 câu**, kết quả **13/15** (vẫn dưới ngưỡng 14 ⇒ AC7 vẫn không đạt), và số test AC2 được sửa thành 953/+76. Báo cáo này đã cập nhật theo trạng thái **đĩa hiện tại**; chỗ nào còn sót thì nói rõ còn sót ở file nào.

---

## 0. Tóm tắt

| | Số phát hiện |
|---|---|
| **CHẶN** | 0 |
| **NÊN SỬA** | 7 |
| **GHI NHẬN** | 7 |
| **DƯ (scope creep)** | **không tìm thấy** |

Phần hợp đồng 9 function làm rất sát spec: đúng tên, đúng bộ tham số, đúng trần, đúng nguồn, **không thừa một tham số nào, không thiếu một tham số nào**. Bảng nhãn đúng 21 mã. Đơn vị `%` của macro không bị nhân 100. `prf`/`rev` bị chặn khỏi mọi đường hiển thị. Không có migration, endpoint HTTP, streaming, embedding hay task Scheduler nào lọt vào.

Ba chỗ lệch thật, theo thứ tự nặng: **(1)** bốn hình dạng trạng thái dữ liệu chỉ được thực hiện đầy đủ ở 2/8 function — bốn function còn lại gộp "không tìm thấy" / "kho không có loại dữ liệu này" vào "rỗng", đúng cái spec §4.6 dựng ra để cấm; **(2)** `topic` của `load_knowledge_reference` không phải `Literal` enum đóng như spec chốt, nên seam S5 "từ chối ở tầng schema" không đúng như mô tả; **(3)** hai seam test S6/S7 mang tên đúng nhưng **không kiểm đúng thứ spec chốt**. Kèm theo là vài chỗ bằng chứng nghiệm thu bị thiếu hoặc lệch số.

---

## 1. Chín function — đối chiếu từng dòng với spec §4.4

Nguồn đối chiếu: `backend/agent/tools/__init__.py` (chữ ký model nhìn thấy) + từng file `tools/*.py` (trần, nguồn) + dump `input_schema` thật.

| # | Function | Tham số spec chốt | Code | Trần spec | Trần code | Nguồn |
|---|---|---|---|---|---|---|
| 1 | `screen_stocks` | criteria, industry_code, exchange, sort_by, limit | ✅ khớp | ≤ 50 | `cap_limit(limit, 20, 50)` ✅ | `screener_daily` ⋈ `security` ⋈ `v_issuer_industry` ✅ |
| 2 | `get_financials` | ticker*, statement_type, from_year, to_year, period, metric_codes | ✅ khớp | ≤ 8 năm | `TRAN_KY = 8` ✅ | `financial_statement` ✅ |
| 3 | `get_price_series` | ticker*, from_date, to_date, adjusted | ✅ khớp | ≤ 400 phiên | `TRAN_PHIEN = 400` ✅ (thiếu `da_cat`, §2.7) | `price_daily` ✅ |
| 4 | `get_corporate_events` | ticker*, event_type, from_date, to_date, limit | ✅ khớp | ≤ 50 | `cap_limit(limit, 20, 50)` ✅ | `corporate_event` ✅ |
| 5 | `compare_peers` | tickers, metric_codes, industry_code | ✅ khớp | ≤ 10 mã, ≤ 8 chỉ tiêu | `TRAN_MA, TRAN_CHI_TIEU = 10, 8` ✅ | `screener_daily` ngày mới nhất ✅ |
| 6 | `get_news` | query, ticker, group_no, sub, industry_code, from_date, to_date, limit | ✅ khớp | ≤ 30 | `cap_limit(limit, 10, 30)` ✅ | `article` ⋈ `article_revision` ✅ |
| 7 | `get_industry_tree` | industry_code, ticker — **không có `icb_level`** | ✅ khớp, **không có `icb_level`**, có `nguon_gan` | — | — | `industry`, `v_issuer_industry` ✅ |
| 8 | `get_macro_series` | code, keyword, from_date, to_date, limit | ✅ khớp | ≤ 200 | `cap_limit(limit, 60, 200)` ✅ | `observation_spliced` + **cả hai** bảng `asset` ✅; lấy `value_spliced`, kèm `gia_tri_cong_bo` khi khác ✅ |
| 9 | `load_knowledge_reference` | topic*, **`Literal` 9 giá trị** | ⚠️ `topic: str`, **không enum** (§2.2) | — | — | file `vn-stock-knowledge/` ✅ |

**Không có function nào thiếu tham số spec chốt, và không có tham số nào thêm mà không ai xin.**

---

## 2. Phát hiện

### 2.1 THIẾU · NÊN SỬA (nặng nhất) — bốn hình dạng trạng thái dữ liệu chỉ đúng ở 2/8 function

**Cam kết** — spec §4.6: *"Phân biệt bằng trường tường minh, **không** bằng độ dài mảng"*, bốn hình dạng: (1) mã không tồn tại → `tim_thay:false` + `goi_y`; (2) mã tồn tại nhưng **kho không có loại dữ liệu này** → `co_du_lieu:false` + `ly_do` + `loai`; (3) khoảng ngày rỗng → `so_dong:0` + `khoang_co_du_lieu`; (4) có dữ liệu. Lý do tồn tại của luật này ghi ngay ở F3: *"bắt buộc có hình dạng 'có mã, không có dữ liệu' tách khỏi 'không tìm thấy mã'"*, và `_shared.py` mở đầu bằng đúng câu *"model không được phép nhầm '0 bản ghi' với 'kho không có loại dữ liệu này'"*.

**Thực tế** — gọi thật trên kho dev, role `dlck_api`:

```
financials(HNX30):     {"tim_thay": true, "co_du_lieu": true, "so_dong": 0, "ma": "HNX30"}
events(HNX30):         {"tim_thay": true, "co_du_lieu": true, "so_dong": 0, "ma": "HNX30"}
compare_peers(ZZZZ):   {"tim_thay": true, "co_du_lieu": true, "so_dong": 0, "ngay_du_lieu": "2026-09-04"}
news(ticker=ZZZZ):     {"tim_thay": true, ..., "so_dong": 0, "ghi_chu": "không có bài nào khớp nhãn;
                        trong khoảng này còn 7918 bài chưa phân loại nên chưa thể lọc theo nhãn"}
```

Bốn ca, ba kiểu sai:

- `get_financials` / `get_corporate_events` với một **chỉ số** (không có `issuer_id`) ra **hình dạng #3** trong khi đúng phải là **#2** — kho không bao giờ có BCTC cho chỉ số. `khong_co_du_lieu()` chỉ được gọi ở `get_price_series` và `get_industry_tree`.
- `compare_peers` **không gọi `resolve_ticker` một lần nào**: mã bịa ra hoàn toàn không phân biệt được với "phiên này mã đó không có dòng screener" ⇒ **#1 bị gộp vào #3**, đúng câu spec cấm.
- `get_news(ticker=...)` tệ hơn một bậc: với mã không tồn tại nó vẫn trả `ghi_chu` nói *"còn 7918 bài chưa phân loại"* — một lời giải thích **sai nguyên nhân**, mời model kết luận "chưa phân loại nên chưa thấy tin về ZZZZ" thay vì "không có mã ZZZZ".
- `khoang_co_du_lieu` của hình dạng #3 chỉ có ở `get_price_series`; `rong()` cho phép truyền `khoang` nhưng không caller nào khác truyền.

**Đề xuất:** `compare_peers` và `get_news` gọi `resolve_ticker` cho từng mã và trả danh sách mã không tra được (hoặc hình dạng #1 khi tất cả đều trượt); `get_financials`/`get_corporate_events` trả `khong_co_du_lieu(loai, ...)` khi `issuer_id` là NULL hoặc `loai != 'stock'`; các nhánh `rong()` kèm `khoang_co_du_lieu` như `get_price_series` đã làm.

---

### 2.2 SAI · NÊN SỬA — `topic` không phải `Literal` enum đóng

**Cam kết** — spec §4.4 #9: *"`topic` **bắt buộc**, `Literal` 9 giá trị"*; §4.3: *"`topic` là **enum đóng 9 giá trị**"*; §6 S5: *"`topic="../../../etc/passwd"` bị từ chối **ở tầng schema**"*. Dữ kiện G8 dựa hẳn vào enum: *"ép công cụ + enum ⇒ 0 lỗi schema/232 lời gọi"*.

**Thực tế** — schema thật model nhận được:

```json
load_knowledge_reference {"properties": {"topic": {"title": "Topic", "type": "string"}}, "required": ["topic"]}
```

Không có `enum`. Việc chặn nằm ở thân hàm (`doc_tri_thuc` trả lỗi có cấu trúc), và test `test_doc_tri_thuc_chu_de_la_thi_bao_loi_kem_danh_sach` kiểm đúng tầng hàm — **không phải tầng schema như S5 chốt**. `plan.md` không nhắc `Literal` ở bất kỳ dòng nào, tức lệch phát sinh từ bước plan và **không được ghi lý do trong ledger**.

Hệ quả thực tế nhẹ (đường path traversal vẫn không khả dĩ vì tra `dict` hằng), nhưng model mất ràng buộc schema và mỗi lần đoán sai chủ đề tốn thêm một vòng request — đúng thứ G8 đo được là enum giúp tránh.

**Đề xuất:** đổi chữ ký thành `topic: Literal["tong-quan", "advanced", ...]`, sửa lại lời hứa của S5 hoặc thêm assert trên `input_schema["properties"]["topic"]["enum"]`.

---

### 2.3 THIẾU · NÊN SỬA — hai seam test S6/S7 không kiểm đúng thứ đã chốt

**Cam kết** — spec §6:

| Seam | Test spec chốt |
|---|---|
| S6 | `test_tool_called_exactly_once` · `test_tool_result_carries_reminder` · **`test_history_survives_two_turns`** |
| S7 | **`test_log_written_under_etl_role`** (role thật) · `test_log_failure_does_not_break_chat` |

**Thực tế:**

- `test_lich_su_song_qua_hai_luot` (`test_a13_chat.py:91`) gọi `run_turn` **đúng một lần** rồi đếm `len(lich_su) == 4`. "Hai lượt" ở đây là hai vòng model trong cùng một câu, **không phải hai lượt người dùng**. Mà G5 — cái bẫy spec dựng seam này để canh — là *"runner đã cạn iterator, gọi lại không ném lỗi, không gửi request, trả lại message cũ — hỏng im lặng"*. Không có test nào truyền `history` trả về vào một `run_turn` thứ hai, tức **đúng bẫy G5 không có ai canh**.
- `test_ghi_so_duoi_role_etl_that` (`test_a12_tools_log.py:37`) chạy một câu `INSERT` viết tay dưới `SET LOCAL ROLE dlck_etl` — **không gọi `log_llm_call`**. Nó chứng minh role ghi được bảng, không chứng minh seam `llm_log.log_llm_call` ghi được. Chính vì thế lỗi ánh xạ trạng thái (mọi lượt `tool_use` bị ghi `failed`) chỉ lộ ra khi chạy thật, và **sau khi sửa vẫn không có test nào canh** (grep `tools_log`: chỉ còn `test_loi_ghi_so_khong_lam_sap_chat` dùng engine hỏng).

**Đề xuất:** thêm `run_turn` lần hai với `history` trả về (mock model trả 2 lượt), và một test gọi `log_llm_call(ops_eng_thật, msg(stop_reason="tool_use"))` rồi `SELECT status` — hai test này rẻ và canh đúng hai chỗ đã hỏng thật.

---

### 2.4 SAI · NÊN SỬA — tài liệu khẳng định "ba lỗi đã sửa, **có test canh**", thật ra chỉ 1/3

**Cam kết** — `round7-results-2026-09-07.md` §5 tiêu đề: *"Ba lỗi code mà lượt chạy thật lộ ra (**đã sửa, có test canh**)"*; `docs/90-records/README.md` chép lại nguyên ý: *"ba lỗi hỏng-im-lặng … **đã sửa có test canh**"*.

**Thực tế** — `git show --stat d23913c` cho thấy commit sửa cả ba lỗi chỉ thêm test cho **một**:

| Lỗi | Test canh |
|---|---|
| `max_tokens=4000` cắt câu trả lời thành rỗng | ❌ không có test nào chạm `MAX_TOKENS` hay nhánh "lượt này không sinh được câu trả lời" (`grep MAX_TOKENS tests/agent/` → 0) |
| model từ chối tra vì tưởng mốc thời gian ngoài tri thức | ✅ `test_khoi_luat_cong_cu_neo_ngay_va_bat_tra_truoc_khi_phu_dinh` + `test_khoi_luat_cong_cu_dung_CUOI_...` |
| sổ ghi mọi lượt `tool_use` thành `failed` | ❌ không có (xem §2.3) |

Đây đúng họ với §3.2 của CLAUDE.md — **viết "đã có X" khi chưa có X**, và cái giá là người sau tin rằng hai chỗ hỏng-im-lặng đã được canh trong khi chúng đang trần.

**Đề xuất:** hoặc thêm hai test, hoặc sửa hai câu văn thành "một trong ba có test canh, hai còn lại chưa" ngay trong cùng lượt.

---

### 2.5 SAI · NÊN SỬA (nhẹ, còn sót một chỗ) — số test của AC2

**Cam kết** — AC2: *"chạy `pytest -q` trên `main` **và** trên nhánh, **dán cả hai dòng tóm tắt**"*.

**Thực tế** — chạy lại hôm nay trên chính commit `4ff1e62`:

```
953 passed, 2 skipped in 83.35s
```

và `pytest tests/agent -q` → **76 passed**. Con số `main` = 877 khớp (953 − 76). Con số đúng là **nhánh 953 passed, 2 skipped, +76**; con số **951/+74** từng có trong hồ sơ là ảnh chụp **trước** commit sửa lỗi `d23913c` (commit đó thêm đúng 2 test).

Trong lượt sửa vừa diễn ra, `round7-results` §4 và `90-records/README.md` **đã được sửa đúng thành 953/+76** ✅. **Còn sót đúng một chỗ:** `ledger.md:62` vẫn ghi *"`main` **877 passed, 2 skipped** → nhánh **951 passed, 2 skipped** (+74, không skip mới)"*. Hai file cạnh nhau đang nói hai con số — đúng loại "tài liệu tự đá nhau" mà §1.7 cấm.

Ngoài ra **không có dòng tóm tắt nguyên văn nào được dán** ở bất kỳ đâu, dù AC2 đòi đúng chữ đó. Phần còn lại của AC2 đạt: số test mới (76) ≥ số seam (7); không có `skip`/`xfail` mới (2 skipped ở cả hai phía).

---

### 2.6 THIẾU · NÊN SỬA — AC5 không có bằng chứng nào trong repo

**Cam kết** — AC5: *"hỏi **4 câu ngoài phạm vi (sức khoẻ, pháp lý, lập trình, nấu ăn)** — 4/4 bị từ chối, **dán transcript**"*.

**Thực tế** — `round7-results` §4 ghi *"✅ — 4/4 (ẩm thực, lập trình, và **hai câu trong lượt nghiệm thu**)"*. `round7-transcript-2026-09-07.md` chỉ có `AC6b` + 15 câu hồi quy, **không có một câu ngoài phạm vi nào**. Grep cả thư mục hồ sơ cho "sức khoẻ / pháp lý / nấu ăn / ẩm thực" → 0 hit ngoài chính spec.

Nghĩa là: AC5 hiện chỉ là **lời khai**, không kiểm lại được, và hai trong bốn câu thậm chí không nêu được là câu gì. Chưa kể spec chỉ đích danh bốn lĩnh vực, còn báo cáo đổi "sức khoẻ/pháp lý" thành "hai câu trong lượt nghiệm thu".

**Đề xuất:** chạy lại 4 câu (mất ~1 phút) và dán transcript vào file transcript, hoặc hạ AC5 xuống "chưa có bằng chứng lưu".

---

### 2.7 THIẾU · NÊN SỬA (nhẹ) — hai chỗ hợp đồng nhỏ không đúng chữ

**a) `get_macro_series` trả danh mục thiếu "khoảng ngày".** Spec §4.4 ghi chú #8: *"`code=None, keyword=...` ⇒ trả **danh mục** chuỗi khớp (**mã + tên + đơn vị + khoảng ngày**)"*. Thực tế:

```json
{"ma": "diesel_vn", "ten": "Giá dầu diesel bán lẻ", "don_vi": "VND/lít", "nguon": "asset"}
```

Có `nguon` (không ai xin), **không có khoảng ngày** (spec xin). Hệ quả: model chọn được mã nhưng không biết chuỗi đó có phủ khoảng ngày nó cần hay không ⇒ tốn thêm một vòng gọi. Lệch này bắt nguồn từ plan (dòng 1711) và không có ghi chú lý do.

**b) `get_price_series` không có `da_cat`.** Quy ước chung §4.4: *"`limit` mặc định nhỏ, có trần cứng; **vượt trần thì cắt và ghi `da_cat: true`**"*. `get_price_series` cắt cứng ở `LIMIT 400` và trả về khoá `['tim_thay','co_du_lieu','so_dong','ma','gia_dieu_chinh','ghi_chu']` — **không có `da_cat`**. Hỏi 24 năm giá HPG thì model không biết mình chỉ nhận được 400 phiên cuối. (Lưu ý phụ: ở các function khác, `cap_limit` chỉ bật `da_cat` khi **người gọi xin quá trần**, không bật khi kết quả bị cắt bởi giới hạn mặc định — cùng một chữ, hai nghĩa.)

---

## 3. Ghi nhận — lệch có lý do đứng vững, hoặc không đáng sửa ngay

| # | Nội dung | Đánh giá |
|---|---|---|
| G1 | **`system` là 3 block, spec §4.3 nói 2** (thêm `TOOL_RULES` neo ngày). Ledger + `round7-results` §5 ghi rõ nguyên nhân đo được (model từ chối tra CPI 8/2026 vì tưởng ngoài tri thức) | **Lý do đứng vững.** Có test canh cả nội dung lẫn vị trí cuối (không phá tiền tố cache). S3 vẫn thoả |
| G2 | **`status='ok'` cho cả `tool_use`**, spec §4.7 chỉ cho `end_turn` | **Lý do đứng vững** — mapping cũ làm sổ nói dối. Nhưng xem §2.3: chưa có test |
| G3 | **`ops.llm_call` không ghi dòng `failed` cho exception / chạm `max_iterations`** như spec §4.7 đòi. `log_llm_call` chỉ chạy trong vòng `for message in runner`; exception thoát thẳng ra `repl` | Lệch thật, chưa ghi ở đâu. Hệ quả: sổ **thiếu hẳn** các lượt hỏng nặng nhất |
| G4 | **`limit` khai `None` thay vì `20`/`10`/`60`** như bảng §4.4 | Hành vi cuối giống hệt (`cap_limit` áp mặc định). Bắt nguồn từ plan, tài liệu §9 đã chép đúng theo code ⇒ nhất quán. Chỉ mất chỗ: model không thấy mặc định trong schema |
| G5 | **§4.5.3 "luôn kèm cả `ngay` và `ngay_hien_thi`"** chỉ đúng một phần: `ngay_cong_bo`, `ngay_thanh_toan`, `ngay_du_lieu` chỉ có bản ISO | Nhỏ, không gây hiểu sai |
| G6 | **Gợi ý mã** chỉ khớp mờ trên `ticker` + `issuer.short_name`; spec §4.6 viết `name`/`short_name` | Nhỏ; comment trong `_shared.py` đã nói rõ chỗ nối thêm khi `news.trade_name` có dữ liệu ✅ |
| G7 | **`roadmap.md:321` vẫn ghi** *"Thiết kế đã có, **chưa duyệt** … **8 function** … tài liệu duy nhất trong kho chưa qua kiểm chứng thực tế"* | Nằm trong khối *"~~Điểm vào cho lát 10~~ — ĐÃ DÙNG XONG, giữ làm ngữ cảnh"*, nên đã có rào. Nhưng `roadmap.md` là **tài liệu sống**, không thuộc vùng lịch sử §1.7 ⇒ AC10 "không còn chỗ đá nhau" mạnh hơn thực tế. Một dòng ghi chú trong khối là đóng được |

Ngoài ra, **working tree đang có một loạt sửa chưa commit** (rubric lớp 2 viết lại + chấm lại 15 câu + `round7-grading-v2-2026-09-07.md` + sửa số test). Xem §8 — cách làm này được khai báo đầy đủ và **giữ nguyên bảng chấm lượt đầu**, nên không tạo mâu thuẫn; chỉ còn `ledger.md` chưa theo kịp (§2.5).

---

## 4. Ngoài phạm vi (spec §1) — không tìm thấy vi phạm

Kiểm từng mục spec ghi là NGOÀI phạm vi:

| Mục ngoài phạm vi | Kiểm bằng | Kết quả |
|---|---|---|
| Endpoint HTTP / web chat | `grep -rn "fastapi\|APIRouter\|uvicorn" backend/agent backend/tests/agent`; `git diff --stat -- backend/api` | **0 hit**, `backend/api` không đổi |
| Streaming | grep `stream` trong `agent/` | **0 hit** |
| Embedding / tìm kiếm khái niệm | grep `embedding` | **0 hit**; và `roadmap.md` dòng 145 đã **gỡ** đúng như §9 đòi |
| Chạy lưới phân loại 7.900 bài | diff `backend/etl` | không đổi |
| Ba ô thiếu trong cây ngành | diff migration | không đổi |
| Nạp 83 chỉ tiêu `GetScreenerParameters` | bảng nhãn 21 mã, mã ngoài bảng bị từ chối | không đụng |
| Đăng ký task Scheduler | diff `scripts/`, `deploy/` | **không đổi** |
| Migration mới | `ls database/migrations/versions` | head vẫn **`0020`** ✅ |

Hai thứ code có mà spec không viết ra chữ — block `TOOL_RULES` và `SET LOCAL statement_timeout = '20s'` — **không tính là DƯ**: cái đầu là bản vá lỗi đo được, ghi đủ trong ledger; cái sau nằm sẵn trong `plan.md:2079`.

---

## 5. Quy ước trình bày (spec §4.5) — kiểm từng câu hỏi được giao

| Câu hỏi | Kết quả |
|---|---|
| **Bảng nhãn đóng có đúng 21 mã spec liệt kê?** | ✅ **Đúng 21/21**, không thừa không thiếu: 7 mã `isa*` + 6 mã `bsa*` + `cfa18` (14 BCTC) + 7 mã tỷ số. Tên hiển thị khớp nguyên văn spec §4.5.2, gồm cả cặp `isa20` "Lợi nhuận sau thuế (toàn bộ)" ↔ `isa22` "…của cổ đông công ty mẹ" |
| **Đơn vị `%` của macro có bị nhân 100 nhầm?** | ✅ **Không.** `display_series_value(4.45, "%") → "4,45%"` (không nhân), `display_metric(0.17377625, "ty_le_thap_phan") → "17,38%"` (nhân 100). Hai ca đặt **cạnh nhau** trong `test_a02_format.py:20-25` đúng như S2 yêu cầu |
| **`prf`/`rev` có bị loại khỏi mọi đường hiển thị?** | ✅ **Có, kín.** Không nằm trong `LABELS`; `get_financials`, `screen_stocks`, `compare_peers` đều chặn mã ngoài bảng trước khi chạm SQL; `screen_stocks`/`compare_peers` chỉ đọc khoá payload nằm trong `LABELS`; `_don_vi()` chỉ truy vấn `code = ANY(list(LABELS))`. Có test: `label_for("prf") is None`, `so_sanh_cung_nganh(..., metric_codes=["rev"]) → loi` |

---

## 6. Seam test (spec §6) — bảy seam, có test hết, hai seam sai nội dung

| Seam | Có test? | Đúng thứ spec chốt? |
|---|---|---|
| S1 `assert_read_only` | ✅ `test_a01_db.py` (5 test) | ✅ đủ: `pg_has_role` + `has_table_privilege` false + INSERT bị chặn + 3 view + `immutable_unaccent` |
| S2 `format.*` | ✅ `test_a02_format.py` (12 test) | ✅ đủ cả 5 ca spec liệt kê |
| S3 `build_system_blocks` | ✅ `test_a03_system_prompt.py` | ✅ đủ: block[0] nguyên văn, block[1] có tiêu đề thật L1, **không** có L2 |
| S4 8 function dữ liệu | ✅ 7 file test | ✅ mỗi function ≥ 1 test giá trị + ≥ 1 test biên/trạng-thái-thiếu; `get_news` có đủ ca `phraseto` (1 bài) vs `plainto` (2 bài). *(Nhẹ: `screen_stocks` không có test biên riêng — ca từ chối mã ngoài bảng nằm ở `compare_peers`)* |
| S5 `load_knowledge_reference` | ✅ | ⚠️ **từ chối ở tầng hàm, không phải tầng schema** như spec viết (§2.2) |
| S6 `chat` với model giả | ✅ `test_a13_chat.py` (5 test) | ⚠️ `test_tool_chay_dung_mot_lan` ✅ (canh đúng G6), `test_loi_nhac_di_kem_tool_result` ✅, **`test_history_survives_two_turns` không đúng nội dung** (§2.3) |
| S7 `log_llm_call` | ✅ 2 test | ⚠️ **`test_log_written_under_etl_role` không gọi `log_llm_call`** (§2.3) |

Thứ tự TDD S1 → S2 → S3 → S5 → S4 → S6 → S7 khớp thứ tự commit (`32ddfb0` → `79edcbb` → `f068aaa` → `4208cf6` → … → `effa125`) ✅.

---

## 7. Bảng AC1–AC10

| AC | Bằng chứng có? | Đủ? | Ghi chú |
|---|---|---|---|
| **AC1** `tool_runner` × MiniMax | ✅ ledger Task 0, **dán nguyên văn** output gồm cả `SCHEMA:` | ✅ **đủ** | Đóng đúng A1, A2, G6, G8 bằng một lượt chạy trước khi xây gì — làm đúng ý spec |
| **AC2** không test xanh thành đỏ | ⚠️ có số (**đã sửa đúng thành 953/+76** trong lượt vừa rồi), **không dán dòng tóm tắt**; `ledger.md:62` còn số cũ | ⚠️ **gần đủ** | Đo lại khớp: **953 passed, 2 skipped**; agent = 76. Phần "≥ số seam" và "không skip mới" đạt (§2.5) |
| **AC3** đọc dưới `dlck_api`, không ghi được | ⚠️ S1 xanh ✅ (chạy lại: 76/76 xanh); lượt chạy tay chỉ có **lời khai**, không dán output | ⚠️ **một nửa** | AC yêu cầu *"chạy tay `python -m agent` một lần dưới đúng credential production, **dán output**"*. `database/README.md` mô tả kết quả nhưng không có output. Tôi tự kiểm được phần đọc: gọi 4 function qua `AGENT_DATABASE_URL` chạy tốt |
| **AC4** 9 function trả đúng dữ liệu thật | ✅ S4+S5 xanh; `round7-results` §2 liệt kê cả 9 function được model gọi đúng chỗ | ✅ **đủ** | Lưu ý: test chạy trên fixture `kho` (kho thu nhỏ) chứ không phải kho thật — đúng luật §4.4.4, có ghi rõ trong docstring. Riêng `test_a05` khai *"đường lấy expected KHÁC đường của hàm"* hơi quá lời: hằng số expected chính là giá trị fixture vừa seed (`test_a07` khai đúng: *"cùng đường, chỉ là chốt hồi quy"*) |
| **AC5** 4 câu ngoài lĩnh vực bị từ chối | ❌ **không có transcript nào** | ❌ **chưa đủ** | Chỉ có một dòng tự khai, hai trong bốn câu không nêu được là câu gì (§2.6) |
| **AC6** VN-Index nói thẳng kho chưa có | ✅ transcript `AC6b` đầy đủ | ✅ **đủ** | Trung thực: khai rõ lượt đầu model **không gọi function nào** (đúng kết quả, sai đường) và chỉ đạt sau khi sửa mô tả function. Câu trả lời không bịa số, không thay bằng chỉ số khác ✅ |
| **AC7** 15/15 số + ≥ 14/15 hình dạng | ✅ hai bảng chấm (lượt đầu **12/15**, lượt sửa rubric **13/15**) + transcript + kết quả | ✅ **đủ, và trung thực** | ❌ vẫn **không đạt** ngưỡng 14 sau khi chấm lại. Xem §8 |
| **AC8** đo chi phí, độ trễ | ✅ bảng số từ `ops.llm_call`: 47 request/22 câu, p50 6,9 s · p90 34,5 s, $0,016/câu, token vào "lạnh" ≈ 36.750 | ✅ **đủ** | Đủ mọi chỉ số AC8 liệt kê. Còn khai thêm một phát hiện **ngược** với ghi chép cũ (cache không trúng giữa hai câu) — đúng tinh thần §1.2 |
| **AC9** không còn `idle in transaction` | ⚠️ chỉ có kết luận "= 0", **không dán `pg_stat_activity`** | ⚠️ **một nửa** | Thiết kế code thì đúng (mỗi tool `with engine.connect()`), nhưng bất biến spec ghi là "kiểm được" mà lại không lưu số đo |
| **AC10** tài liệu đã đồng bộ | ⚠️ ledger kể đã chạy `git grep` và bắt được 2 chỗ (`architecture.md`, `20-design/README.md`), **không dán kết quả grep**; còn một hit sống | ⚠️ **một nửa** | Tôi chạy lại: `git grep "8 function"` vẫn ra `roadmap.md:321` "chưa duyệt … 8 function … tài liệu duy nhất chưa qua kiểm chứng" (trong khối đã gạch ngang). `git grep icb_level` — mọi hit còn lại **đúng là tầng lưu trữ ICB**, khớp lời ledger ✅ |

---

## 8. Riêng AC7 — cách tự khai có trung thực không?

**Có, và trung thực hơn mức tối thiểu.**

- Không làm tròn kết quả cho đẹp: ghi thẳng **"❌ không đạt"** ở `round7-results` §1, ledger, `roadmap.md`, `90-records/README.md` và `chatbot-semantic-layer.md` — trước là 12/15, sau lượt chấm lại là 13/15, **cả hai đều dưới ngưỡng 14 và đều được khai là không đạt**.
- Nêu đích danh các câu trượt kèm lý do từng câu, và nêu **mẫu hỏng lặp lại** (mục "phân biệt nguồn số" bị bỏ ở 5/15 câu, giữ nguyên qua cả hai lượt chấm) — thông tin bất lợi mà không AC nào bắt phải khai.
- **Tự khai một lỗi bịa số** không nằm trong bảng đáp án và không ảnh hưởng lớp 1: dải nhạy "23.500–32.500 đ" của A4b, kèm phép tính lại cho ra "≈ 24.643–30.962 đ" và kết luận *"đây là lỗi nặng nhất phát hiện được trong 15 câu"*. Đây là kiểu khai mà một báo cáo muốn đẹp sẽ bỏ qua.
- Giữ nguyên transcript lượt hỏng (A2, A4, B4, B9 rỗng vì `max_tokens`) làm bằng chứng, chỉ chấm bản `b` và **nói rõ vì sao** — không xoá dấu vết.
- §6 kết luận *"Đây là kết quả của lát, không phải lỗi cần giấu"* và liệt kê ba việc kế tiếp — đúng câu spec §7 dặn (*"AC7 không phải cổng chặn merge… báo nguyên trạng, không sửa cho đẹp"*).

**Về lượt sửa rubric và chấm lại (diễn ra trong lúc review):** rubric lớp 2 được viết lại sau khi đã biết kết quả — về nguyên tắc đây là con đường ngắn nhất để một AC "không đạt" biến thành "đạt". **Ở đây thì không thành vấn đề**, vì bốn dấu hiệu ngược lại:

- Lý do sửa là **quyết định của chủ dự án** (*"phép tính phải ghi số chứ không ghi văn xuôi"*), được chép nguyên văn vào `round7-results` §1, không phải người thực thi tự nới thước đo.
- **Bảng chấm lượt đầu được giữ nguyên** (`round7-grading-2026-09-07.md`), bảng mới nằm ở file riêng (`…-v2-…`), và §1 trỏ tới cả hai. Không có gì bị xoá dấu vết.
- Kết quả vẫn là **không đạt** (13/15 < 14). Rubric mới thậm chí **thêm một cổng loại** (số dẫn xuất phải kèm phép tính) và chính cổng đó làm A4b trượt dù đạt 5/5 điểm — tức thước đo mới **chặt hơn ở chỗ khác**, không phải nới đều.
- Bảng chấm v2 tự khai chỗ rubric mâu thuẫn (5 mục tính điểm nhưng bảng liệt 6 dòng) và tự khai ba ca "đạt lỏng" (A5, B3, B2 mục 2; B7, B8 mục 4) — kiểu ghi chú làm giảm sức thuyết phục của chính kết quả mình vừa chấm.

**Một điểm còn lại nên nói một câu trong hồ sơ:** bốn câu được chấm ở bản chạy lại (`A2b, A4b, B4b, B9b`) sau khi sửa code, nghĩa là **15/15 số đúng là kết quả của lượt thứ hai**, không phải lượt đầu. Transcript có ghi hậu tố `b` và lý do, nhưng bảng kết quả §1 không nhắc.

---

## 9. Tài liệu §9 — bảy file, đối chiếu với code thật

| File | Sửa? | Nội dung có khớp code? |
|---|---|---|
| `chatbot-semantic-layer.md` | ✅ | ✅ **Khớp từng chữ ký** — tôi so với `tools/__init__.py`: 9 dòng chữ ký đúng nguyên văn, gồm cả `limit=None`. Bỏ nhãn "chưa duyệt" ✅, xoá `icb_level` kèm giải thích ✅, đóng 3/4 "điều chưa biết" bằng số đo ✅ |
| `market-data-store.md` §6.2–6.3 | ✅ | ✅ 9 tên function đúng; có cảnh báo ví dụ view dùng tên bảng cũ `organization` ✅; không chép lại hợp đồng (một sự thật một chủ) ✅ |
| `maintenance.md` §6 | ✅ | ✅ ghi bộ vòng 6 không tái lập được, **giữ nguyên 260** đúng như §1.2 đòi, trỏ sang vòng 7 ✅ |
| `roadmap.md` | ✅ | ✅ đóng lát 10, gộp lát 11 (cả dòng 150 lẫn bảng ánh xạ `[14]`), **gỡ dòng embedding** ✅, viết "Điểm vào cho lát 12" ✅, số test đã sửa. ⚠️ khối "Điểm vào lát 10" cũ (đã gạch ngang) còn "8 function / chưa duyệt" |
| `database/README.md` | ✅ | ✅ thêm `agent_reader IN ROLE dlck_api` vào mục per-môi-trường; mô tả `assert_read_only` khớp `db.py` từng vế (`pg_has_role` + `has_table_privilege`) |
| `90-records/README.md` | ✅ | ✅ có dòng hồ sơ mới, số test đã sửa thành 953/+76, AC7 đã cập nhật 13/15. ⚠️ còn khẳng định "có test canh" (§2.4); danh sách file trong ô không kể `plan.md`/`ledger.md`/`round7-grading-v2` |
| `.env` | ✅ | ✅ `AGENT_DATABASE_URL` có mặt (kiểm bằng `grep -c` tên khoá, **không đọc giá trị**); `.env` vẫn bị `.gitignore:2` che |

Ba file ngoài danh sách §9 cũng được sửa (`architecture.md`, `20-design/README.md`, `backend/README.md`) — đó là kết quả của chính phép kiểm AC10, hợp lệ. `backend/README.md` ghi lệnh chạy đúng (`cd backend && uv run --project . python -m agent`) kèm lý do; cách xử lý "không sửa spec/plan vì là bản ghi tại-thời-điểm, ghi lệnh đúng ở nơi sở hữu sự thật" là **đúng §1.7**.

---

## 10. Phán quyết

**Nhánh này làm đúng phần lớn cam kết — hợp đồng 9 function, bảng nhãn 21 mã, ranh giới đơn vị, ranh giới ngoài-phạm-vi đều sạch, và cách tự khai AC7 trung thực kể cả khi phải khai một ca model bịa số — nhưng chưa xong: bốn hình dạng trạng thái dữ liệu mới đúng ở 2/8 function (đã tái hiện bằng lời gọi thật), `topic` mất enum đóng mà spec chốt, hai seam test S6/S7 mang đúng tên nhưng kiểm sai chỗ, và ba khẳng định nghiệm thu (test "có canh" cho ba lỗi, AC5 không có transcript, AC9 không có số đo) chưa có bằng chứng đứng được — không cái nào đủ nặng để chặn merge, nhưng phải đóng trước khi lát 12 dựa lên nó.**
