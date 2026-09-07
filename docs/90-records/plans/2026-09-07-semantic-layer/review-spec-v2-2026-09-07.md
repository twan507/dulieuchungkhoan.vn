# Review trục SPEC — vòng 2, lát 10, nhánh `feat/semantic-layer`

**Ngày:** 2026-09-07 · **Reviewer:** độc lập, chỉ đọc · **Thước đo:** `spec.md`, `plan.md`, `ledger.md`, `regression-round7.md`, `round7-results-2026-09-07.md`

**Trạng thái cây lúc review:** đề bài giao HEAD `4c72c09`. Trong lúc tôi làm việc, nhánh đi thêm **hai commit tài liệu**: `34071fc` (index `90-records` liệt 5/11 file, còn chép lại khẳng định "có test canh" đã đính chính) và `653971e` (roadmap còn ghi AC5 4/4, hạ xuống 2/4). Cả hai đều là sửa đúng hướng vòng 1. Báo cáo này đọc theo **HEAD `653971e`**, cây sạch.

**Đã chạy để tự kiểm:** `pytest tests -q` toàn bộ (**976 passed, 2 skipped in 88.10s**) · `pytest tests/agent -q` (**99 passed**) · dump `input_schema` thật của cả 9 tool · **gọi thẳng 8 function dữ liệu trên kho dev** qua `AGENT_DATABASE_URL` với các đầu vào biên (mã bịa, mã chỉ số, mã huỷ niêm yết, khoảng ngày rỗng) · truy vấn `pg_stat_activity`. Không gọi model thật.

---

## 0. Tóm tắt

| | Số |
|---|---|
| **CHẶN** | **1** |
| **NÊN SỬA** | 5 |
| **GHI NHẬN** | 6 |

Năm trong sáu phát hiện vòng 1 đã đóng **thật** — tôi tái kiểm bằng lời gọi hàm, không đọc code rồi tin. Nhưng **một trong các bản sửa tạo ra lỗi nặng hơn lỗi nó chữa**: `compare_peers` khi mọi mã hỏi đều không tra được nay trả về **10 mã bất kỳ của thị trường** kèm `co_du_lieu: true, so_dong: 10`, thay vì hình dạng "không tìm thấy". Trước khi sửa nó trả 0 dòng — sai theo kiểu im lặng; sau khi sửa nó trả **dữ liệu sai một cách tự tin**. Đây là mục CHẶN duy nhất.

---

## 1. Bảng kiểm sáu phát hiện vòng 1

| # | Phát hiện vòng 1 | Trạng thái | Bằng chứng gọi hàm thật |
|---|---|---|---|
| **1a** | Bốn hình dạng §4.6 chỉ đúng ở 2/8 function — `get_financials`/`get_corporate_events` với chỉ số ra #3 thay vì #2 | ✅ **đóng thật** | `bao_cao_tai_chinh(VNINDEX)` → `{"tim_thay":true,"co_du_lieu":false,"loai":"index","ly_do":"kho không có báo cáo tài chính cho chỉ số","ma":"VNINDEX"}`; `su_kien_doanh_nghiep(VNINDEX)` → cùng hình dạng, `ly_do` đúng loại dữ liệu |
| **1b** | `compare_peers` không gọi `resolve_ticker` lần nào ⇒ #1 gộp vào #3 | ⚠️ **đóng nửa vời — sinh lỗi mới nặng hơn** | `so_sanh_cung_nganh(["HPG","VNINDEX","ZZZZ"])` phân biệt đúng ba loại ✅. Nhưng `so_sanh_cung_nganh(["ABCDE"])` → `so_dong: 10`, `du_lieu` = `A32, AAA, AAH, AAM, AAN, AAS, AAT, AAV, ABB, ABC` — **10 mã không ai hỏi**. Xem §2 M1 |
| **1c** | `get_news(ticker=ZZZZ)` đổ lỗi sai nguyên nhân ("còn 7918 bài chưa phân loại") | ✅ **đóng thật** | `tim_tin(ticker="ZZZZ")` → `{"tim_thay":false,"ma_da_tra":"ZZZZ","goi_y":[]}`. `ghi_chu` "chưa phân loại" nay chỉ xuất hiện với mã **có thật** (`ticker="VNINDEX"`) — đúng nguyên nhân |
| **1d** | `khoang_co_du_lieu` của hình dạng #3 chỉ có ở `get_price_series` | ❌ **chưa đóng** | `bao_cao_tai_chinh(HPG, 1990, 1990)` → `{"tim_thay":true,"co_du_lieu":true,"so_dong":0,"ma":"HPG"}` — không `khoang_co_du_lieu`. `su_kien_doanh_nghiep(HPG, 1990…)` y hệt. Chỉ `gia_theo_ngay(HPG,"1990-01-01","1990-12-31")` trả `"khoang_co_du_lieu":{"tu":"2026-06-09","den":"2026-09-03"}` ✅. Xem §2 M6 |
| **2** | `topic` không phải `Literal` enum đóng ⇒ S5 "từ chối ở tầng schema" sai mô tả | ✅ **đóng thật** | Dump `input_schema` thật: `"topic": {"enum": ["tong-quan","advanced","financial-statements","macro-money-creation","portfolio-and-rotation","psychology-information","technical-indicators","technical-supply-demand","valuation"], "type":"string"}`. Enum lấy từ `L2_TOPICS` nên không sinh nguồn sự thật thứ hai; có test canh (`test_topic_la_enum_dong_du_9_gia_tri`) |
| **3a** | `test_history_survives_two_turns` chỉ gọi `run_turn` **một lần** ⇒ bẫy G5 không ai canh | ✅ **đóng thật** | `test_luot_thu_hai_that_su_gui_lai_lich_su_luot_dau` (`test_a13_chat.py:99`) gọi `run_turn` hai lượt, assert `ghi["n"] == 2` (lượt hai gửi request THẬT) và `"Câu một?" in noi_dung` — canh đúng chỗ runner cạn iterator |
| **3b** | `test_log_written_under_etl_role` chạy `INSERT` viết tay, không gọi `log_llm_call` | ✅ **đóng thật** | `test_ghi_so_duoi_role_etl_that` (`test_a12_tools_log.py:88`) `SET LOCAL ROLE dlck_etl` rồi gọi **chính** `log_llm_call` ba lần (`end_turn`→ok · `tool_use`→ok · `max_tokens`→failed kèm `error`), `SELECT` lại từng dòng |
| **4** | Hồ sơ khẳng định "ba lỗi đã sửa, **có test canh**" nhưng chỉ 1/3 | ⚠️ **đóng nửa vời** | Đính chính đã có ở `round7-results` §5 và index đã bỏ câu chép lại (`34071fc`); hai test còn thiếu **có thật**. Nhưng chính câu đính chính lại nêu tên một test **không tồn tại** — xem §2 M3 |
| **5** | AC5 không có transcript nào | ✅ **đóng thật (bằng cách hạ khai báo)** | `acceptance-transcript` lưu 2 câu (ẩm thực, lập trình) kèm câu tự khai *"hai câu ngoài phạm vi còn lại chạy trong lượt nghiệm thu đầu tiên và không lưu transcript — đó là thiếu sót của lượt đó, ghi lại đây thay vì khai là có"*. `round7-results`, `90-records/README`, `roadmap` đều đã hạ xuống **2/4**. AC5 vẫn **không đạt**, nhưng khai đúng |
| **6a** | AC3 chỉ có lời khai, không dán output | ⚠️ **đóng gần đủ** | `round7-results` §7 dán nguyên văn (`thuoc dlck_api: True` · `co quyen INSERT: False` · `ghi bi chan dung: ProgrammingError`). Lệch chữ: AC nói *"chạy tay `python -m agent`"*, output dán lại là của một script gọi `read_engine()`/`ops_engine()`. Cùng đường khởi động, và 15 transcript vòng 7 chứng minh REPL đã chạy thật — nên tôi coi là đủ về thực chất |
| **6b** | AC9 chỉ có kết luận "= 0", không dán `pg_stat_activity` | ✅ **đóng thật** | `round7-results` §7 dán `idle in transaction: 0 / tổng kết nối agent_reader: 0`. Tôi đo lại vừa xong: `idle in transaction = 0`, tổng kết nối `agent_reader = 1` (chính phiên đo của tôi) |
| **6c** | AC2 lệch số, `ledger.md:62` còn số cũ | ✅ **đóng thật** | `round7-results` §7 dán cả hai dòng tóm tắt (`main: 877 passed, 2 skipped` / `feat/semantic-layer: 976 passed, 2 skipped`). Tôi chạy lại: **976 passed, 2 skipped**, `tests/agent` = **99** ⇒ +99 khớp từng con số |

---

## 2. Lệch mới — do chính các bản sửa tạo ra

### M1 · SAI · 🔴 **CHẶN** — `compare_peers` trả 10 mã bất kỳ khi mọi mã hỏi đều không tra được

**Cam kết** — spec §4.6: *"Phân biệt bằng trường tường minh… (1) Mã không tồn tại trong `market.security` → `{"tim_thay": false, "ma_da_tra": "XYZ", "goi_y": [...]}`"*. Và §4.6 dựng ra chính là để *"model không được phép nhầm '0 bản ghi' với 'kho không có loại dữ liệu này'"*.

**Thực tế** — gọi thật trên kho dev, role `dlck_api`:

```
so_sanh_cung_nganh(["ABCDE"])
→ {"tim_thay": true, "co_du_lieu": true, "so_dong": 10,
   "du_lieu": [A32, AAA, AAH, AAM, AAN, AAS, AAT, AAV, ABB, ABC …],
   "ngay_du_lieu": "2026-09-04", "da_cat": true, "khong_tim_thay": ["ABCDE"]}

so_sanh_cung_nganh(["ZZZZ","QQQQ"])  → cũng 10 mã đó, "khong_tim_thay": ["ZZZZ","QQQQ"]
```

**Nguyên nhân, và tại sao nó là hệ quả trực tiếp của bản sửa vòng 1.** Bản cũ (`4ff1e62`) truyền **mọi mã người hỏi** vào truy vấn:

```python
mas = [t.upper() for t in (tickers or [])][:TRAN_MA]
...  {"mas": mas, ...}
```

Bản sửa (`437626c`) thay bằng **chỉ những mã tra được**:

```python
(ma_hop_le if resolve_ticker(conn, t)["tim_thay"] else khong_ton_tai).append(t)
...  {"mas": ma_hop_le, ...}
```

nhưng giữ nguyên mệnh đề canh của SQL:

```sql
AND (cardinality(CAST(:mas AS text[])) = 0 OR upper(s.ticker) = ANY(:mas))
```

Mệnh đề đó có nghĩa *"danh sách rỗng ⇒ không lọc theo mã"* — đúng khi `:mas` là **mã người hỏi** (rỗng nghĩa là người ta lọc theo ngành), sai hẳn khi `:mas` là **mã tra được** (rỗng nghĩa là **không mã nào tra được**). Chốt chặn duy nhất ở đầu hàm (`if not mas and not industry_code`) kiểm danh sách **xin**, không kiểm danh sách **đã phân giải**, nên nó không đỡ được ca này.

**Vì sao nặng hơn lỗi cũ.** Vòng 1 chê ca này vì trả `so_dong: 0` — model có thể tưởng "phiên này không có dòng". Nay model hỏi so sánh `ABCDE` nhận về **bảng chỉ tiêu đầy đủ của mười doanh nghiệp có thật, xếp theo alphabet**, kèm cờ `co_du_lieu: true`. Trường `khong_tim_thay: ["ABCDE"]` có nằm trong payload, nhưng nó bị chôn cạnh 10 dòng dữ liệu trông rất thuyết phục. Đây đúng họ "hỏng im lặng" mà CLAUDE.md §3.4 và cả spec §4.6 tồn tại để chặn.

**Vì sao 99 test xanh không thấy.** Ba test mới của `compare_peers` đều có **ít nhất một mã tra được**: `["HPG","ZZZZ"]`, `["HPG","VNINDEX","ZZZZ"]`, và ca 11 mã có 6 mã thật. **Không test nào phủ ca "mọi mã đều trượt"** — đúng chỗ lỗi nằm.

**Đề xuất:** sau vòng `resolve_ticker`, nếu `not ma_hop_le and not industry_code` thì trả thẳng hình dạng #1 (`khong_tim_thay(...)` cho một mã, hoặc `{"tim_thay": false, "ma_da_tra": [...], "goi_y": [...]}` cho nhiều mã) **trước khi** chạm truy vấn screener; thêm test `so_sanh_cung_nganh(["ABCDE"])` assert `du_lieu` rỗng.

---

### M2 · SAI · NÊN SỬA — docstring `llm_log` khẳng định phủ `max_iterations` và exception, code không phủ

**Cam kết** — spec §4.7: *"`'failed'` cho mọi kết thúc khác (`max_tokens`, chạm `max_iterations`, exception) **kèm `error` mô tả**"*.

**Thực tế** — `backend/agent/llm_log.py:6` viết:

> `'failed' dành cho 'max_tokens', chạm max_iterations, và exception.`

Nhưng `log_llm_call` chỉ được gọi **bên trong** `for message in runner` (`chat.py:51-55`), và ánh xạ chỉ đọc `message.stop_reason`:

- **chạm `max_iterations`**: SDK dừng ngay sau một lượt `tool_use`, nên message cuối cùng được ghi mang `stop_reason='tool_use'` ⇒ ghi **`'ok'`**, không có dòng `failed` nào.
- **exception**: `chat.py:99` bắt ở `repl`, ngoài vòng lặp ⇒ **không ghi dòng nào**.

Chỉ `max_tokens` là đúng. Vòng 1 đã ghi chuyện này (G3, "lệch thật, chưa ghi ở đâu"); vòng này nó **nặng thêm một bậc** vì bản sửa `d23913c`/`437626c` viết docstring khẳng định điều code không làm — đúng loại §3.2 (*viết "đã có X" khi chưa có X*), lần này ngay trong file bị ảnh hưởng.

**Đề xuất:** hoặc ghi dòng `failed` ở `chat.py` khi `not ket_sach` và trong `except` của `repl`; hoặc sửa docstring thành *"chỉ phủ `max_tokens`; `max_iterations` và exception chưa có dòng sổ nào — nợ, xem §8"* và thêm dòng nợ vào ledger.

---

### M3 · SAI · NÊN SỬA — câu đính chính overclaim lại nêu tên một test không tồn tại

**Cam kết** — chính `round7-results-2026-09-07.md:80`, đoạn viết ra để đóng lỗi §3.2 của vòng 1:

> *"Hai test còn thiếu đã bổ sung sau lượt review (`test_ket_thuc_sach_nhung_khong_co_chu_van_khong_tra_rong` cho lỗi 1, **`test_luot_tool_use_ghi_so_la_ok`** cho lỗi 3)."*

**Thực tế** — `grep -rn "test_luot_tool_use_ghi_so_la_ok" backend/` ⇒ **0 hit**. `test_a12_tools_log.py` chỉ có 6 test và không có tên đó. Phần kiểm `tool_use → 'ok'` **có thật**, nhưng nằm **bên trong** `test_ghi_so_duoi_role_etl_that` (dòng 102-108), không phải một test riêng.

Nội dung đúng, tên sai. Nhẹ hơn overclaim gốc, nhưng vẫn là một khẳng định không grep ra được — trong đúng đoạn văn viết ra để chữa loại lỗi ấy.

**Đề xuất:** sửa tên thành *"nhánh `tool_use` thêm vào `test_ghi_so_duoi_role_etl_that`"*.

---

### M4 · THIẾU · NÊN SỬA — `get_price_series` vẫn không có `da_cat`, và cắt mất **đầu** khoảng hỏi

**Cam kết** — spec §4.4 quy ước chung: *"`limit` mặc định nhỏ, có trần cứng; **vượt trần thì cắt và ghi `da_cat: true`**"*. Trần của #3 là *"≤ 400 phiên"*.

**Thực tế** — gọi `gia_theo_ngay(HPG, "2002-01-01", "2026-09-03")`, khoá trả về:

```
['co_du_lieu','du_lieu','ghi_chu','gia_dieu_chinh','ma','so_dong','tim_thay']
```

Không có `da_cat`. Truy vấn là `ORDER BY trading_date DESC LIMIT 400` rồi `reversed(rows)` ⇒ hỏi 24 năm nhận **400 phiên cuối**, mất phần đầu, và không cờ nào nói. Mọi function anh em (`get_financials`, `get_corporate_events`, `screen_stocks`, `compare_peers`, `get_news`, `get_macro_series`) đều có `da_cat`; đúng một file này không.

Đây là chỗ **cả hai vòng review đều gọi tên** (vòng này §2.7b, trục Chuẩn N5) và là **file duy nhất trong `tools/` không bị bốn commit sửa chạm tới**. Không có dòng nợ nào ghi lý do hoãn.

*(Chưa lộ trên kho dev vì HPG mới có 60 phiên — đúng lý do trục Chuẩn nói: "đây là đường code, không phải trạng thái dữ liệu".)*

---

### M5 · THIẾU · NÊN SỬA — danh mục `get_macro_series` vẫn thiếu **khoảng ngày**

**Cam kết** — spec §4.4 ghi chú #8: *"`code=None, keyword=...` ⇒ trả **danh mục** chuỗi khớp (**mã + tên + đơn vị + khoảng ngày**)"*.

**Thực tế** — gọi thật:

```json
{"kieu":"danh_muc","danh_muc":[{"ma":"wti","ten":"Giá dầu WTI","don_vi":"USD/thùng","nguon":"asset"}],"tong_khop":1,"da_cat":false}
```

Có `nguon` (không ai xin), **không có khoảng ngày** (spec xin). Bản sửa `a82e600` có chạm file này (thêm `tong_khop`/`da_cat` theo N3 của trục Chuẩn) nhưng không thêm khoảng ngày. Hệ quả đúng như vòng 1 đã nêu: danh mục là **cửa duy nhất** để model tìm mã, model chọn được mã nhưng không biết chuỗi có phủ khoảng nó cần hay không ⇒ tốn thêm một vòng gọi.

---

### M6 · THIẾU · NÊN SỬA — hình dạng #3 vẫn khuyết `khoang_co_du_lieu` ở 2 function

**Cam kết** — spec §4.6 hình dạng #3 viết nguyên văn trường bắt buộc: `{"tim_thay": true, "co_du_lieu": true, "so_dong": 0, "khoang_co_du_lieu": {"tu": "…", "den": "…"}}`.

**Thực tế** — `get_financials` và `get_corporate_events` gọi `rong()` **không tham số**, trả `so_dong: 0` trơ. Helper `_shared.rong(khoang=None)` có sẵn khe, chỉ `get_price_series` truyền. Model hỏi BCTC FPT năm 1990 nhận "0 dòng" mà không biết kho có BCTC từ năm nào — nó phải đoán hoặc gọi mò.

Vòng 1 đã đề xuất đúng việc này; bản sửa đóng phần #2 (chỉ số) mà bỏ phần #3.

---

## 3. Ghi nhận — lệch có lý do, hoặc không đủ nặng để sửa ngay

| # | Nội dung | Đánh giá |
|---|---|---|
| **G1** | **`cap_limit` đổi chữ ký** — bỏ cờ trả về, bên gọi tự tính. Spec §4.4 **có** nói về `da_cat`: *"vượt trần thì cắt và ghi `da_cat: true`"* | **Lý do đứng vững.** Docstring mới giải thích rõ: hàm chạy *trước* truy vấn nên không biết kết quả thật có bị cắt hay không; xin 500 dòng trên bảng 3 dòng thì bị hạ trần mà chẳng cắt gì. Nghĩa mới (*"kết quả bị cắt"*) hữu ích hơn nghĩa cũ (*"yêu cầu vượt trần"*) và có hai test đối xứng canh (`test_da_cat_bao_dung…`, `test_da_cat_khong_bao_sai…`). **Một chỗ còn lẫn:** `compare_peers` dùng `len(mas_xin) > TRAN_MA or len(rows) >= TRAN_MA` — trộn cả hai nghĩa; xin đúng 10 mã hợp lệ và nhận đủ 10 sẽ báo `da_cat: true` sai |
| **G2** | **`compare_peers` thêm `khong_co_du_lieu_phien`** — có phải hình dạng thứ năm tự phát? | **Không, và lý do đứng vững.** §4.6 mô tả bốn hình dạng cho function **một mã**; `compare_peers` nhận **danh sách**, nên phải phơi trạng thái theo từng phần tử. `khong_co_du_lieu_phien` là hình dạng **#2 áp cho một phần tử**, `khong_tim_thay` là **#1 áp cho một phần tử** — cùng tinh thần với câu spec *"`trang_thai: delisted` là cờ kèm thêm trên bất kỳ hình dạng nào"*. Có test canh (`test_ma_ton_tai_nhung_khong_co_phien_khac_ma_khong_ton_tai`). **Chỗ gợn:** khoá `khong_tim_thay` ở đây là **mảng mã**, trong khi cùng tên đó ở `_shared.khong_tim_thay()` là **hình dạng #1 với `tim_thay: false`** — hai nghĩa một tên, dễ làm người sau đọc nhầm |
| **G3** | **`get_news` thêm `kieu_tim`** | **Không phải lệch.** Spec §4.5.4 viết thẳng: *"Nếu `phraseto` ra 0 bài thì thử lại `plainto` và trả kèm `kieu_tim: 'cum'\|'tu_khoa'` để model biết độ chặt"*. Code làm đúng chữ |
| **G4** | **`chat.py` đổi hợp đồng `run_turn`: lượt không kết thúc sạch thì trả lại lịch sử cũ.** §4.2 không mô tả hành vi này | **Lệch *cần ghi*, không phải lệch *phải sửa* — và đã ghi đủ.** §4.2 chỉ chốt *"chạm trần thì báo lỗi rõ ràng, không treo"*; bỏ lượt và báo là một cách thoả câu đó. Nguyên nhân (C2 của trục Chuẩn: lịch sử nhiễm độc khoá chết cả phiên) ghi ở ledger, comment 8 dòng trong `chat.py:67-72`, và **hai test canh** (`test_cham_tran_vong_lap…`, `test_het_max_tokens_giua_luot_cong_cu…`). Cùng nhóm: `MAX_TOKENS` 4000 → 8000, lệch với khối mã ở §4.2 nhưng có số đo (3/40 request bị cắt) và test |
| **G5** | **Rubric lớp 2 nay có 6 mục, spec §5.3 chốt 5** | **Minh bạch, kết quả khớp.** `regression-round7.md` mở đầu mục Chấm bằng ghi chú in nghiêng có ngày và trích nguyên văn quyết định chủ dự án; `round7-results` §1 nhắc lại; **bảng chấm lượt đầu giữ nguyên** (`round7-grading-2026-09-07.md`, 48 dòng, không bị xoá), bảng mới ở file riêng. Tôi đối chiếu bảng v2: 13 dòng **ĐẠT**, 2 dòng **TRƯỢT** (A4b vi phạm cổng 6, B5 3/5) ⇒ **13/15 khớp con số công bố**, và vẫn dưới ngưỡng 14. Rubric mới **chặt hơn** (thêm một cổng loại) chứ không nới. **Chỗ chưa quét:** `spec.md` §5.3 vẫn ghi "5 mục… không câu nào vi phạm mục 5" mà không có dòng trỏ sang rubric đã sửa — hai file cùng thư mục nói hai thước đo |
| **G6** | **`get_industry_tree`**: `industry_code` bịa → `{"nhom": []}`, không `tim_thay`/`co_du_lieu`; hình dạng #2 cho ticker thiếu `loai`, và `ly_do` ghi *"quỹ/ETF theo thiết kế không có ngành"* cho một **chỉ số** | Lệch với câu §4.6 *"phân biệt bằng trường tường minh, **không** bằng độ dài mảng"*. Trục Chuẩn cũng bắt (N8a). Nhẹ, nhưng là **một trong hai mục NÊN SỬA của trục Chuẩn không được sửa mà cũng không được ghi là nợ** (mục kia là M4) — 6/8 mục N đã sửa, không chỗ nào nói hai mục còn lại đi đâu |

---

## 4. Bảng AC1–AC10 trên trạng thái hiện tại

| AC | Bằng chứng | Đủ? | Ghi chú |
|---|---|---|---|
| **AC1** `tool_runner` × MiniMax | ✅ ledger Task 0, dán nguyên văn `SCHEMA:` + `STOP:` + `SO LAN TOOL CHAY THAT: 1` | ✅ **đủ** | Đóng A1, A2, G6, G8 bằng một lượt chạy trước khi xây gì |
| **AC2** không test xanh thành đỏ | ✅ `round7-results` §7 dán **cả hai** dòng tóm tắt | ✅ **đủ** | Tôi chạy lại: **976 passed, 2 skipped in 88.10s**; `tests/agent` **99 passed** ⇒ +99 khớp. 99 ≥ 7 seam; 2 skipped ở cả hai phía ⇒ không skip mới. Con số `main` 877 tôi không tự kiểm được (không được `checkout`), lấy theo bản ghi bàn giao ở `roadmap.md` |
| **AC3** đọc dưới `dlck_api`, không ghi được | ✅ S1 xanh + output nguyên văn §7 | ⚠️ **đủ về thực chất, lệch về chữ** | AC đòi output của *"chạy tay `python -m agent`"*; block dán là của script gọi `read_engine()`/`ops_engine()`. Cùng đường khởi động, và 15 transcript vòng 7 chứng minh REPL chạy thật. Tôi tự kiểm đường đọc: gọi 8 function qua `AGENT_DATABASE_URL` chạy tốt, `has_table_privilege INSERT = false` |
| **AC4** cả 9 function trả **đúng** dữ liệu thật | ✅ S4+S5 xanh (99 test); `round7-results` §2 liệt 9/9 function được model gọi đúng chỗ | ❌ **không còn đứng** | **M1 phá AC này**: `compare_peers` trả 10 mã không ai hỏi, gắn cờ `co_du_lieu: true`. Đây không phải "thiếu dữ liệu", đây là **dữ liệu sai**. AC4 chỉ đạt lại sau khi M1 đóng |
| **AC5** 4 câu ngoài lĩnh vực bị từ chối | ⚠️ 2/4 có transcript, 2/4 tự khai là **không lưu** | ❌ **không đạt, nhưng khai đúng** | Đã hạ nhất quán ở `round7-results`, `90-records/README`, và `roadmap` (`653971e`). Cách xử lý trung thực; AC vẫn hở, và chạy lại 2 câu mất chưa tới một phút |
| **AC6** VN-Index nói thẳng kho chưa có | ✅ transcript `AC6b` | ✅ **đủ** | Khai rõ lượt đầu model **không gọi function nào** (đúng kết quả, sai đường), chỉ đạt sau khi sửa mô tả function. Tôi xác nhận đường dữ liệu: `gia_theo_ngay(VNINDEX)` → `co_du_lieu:false, loai:"index"`, không bịa số |
| **AC7** 15/15 số + ≥ 14/15 hình dạng | ✅ hai bảng chấm (12/15 lượt đầu, 13/15 lượt v2) + 15 transcript | ✅ **bằng chứng đủ, kết quả ❌ không đạt** | Tôi đếm lại bảng v2: 13 ĐẠT / 2 TRƯỢT — khớp. Không phải cổng chặn merge (spec §7). Khai thẳng ở 5 chỗ, kể cả ca model **bịa dải nhạy** của A4b kèm phép tính lại |
| **AC8** đo chi phí, độ trễ | ✅ bảng số từ `ops.llm_call`: 47 request/22 câu, p50 6,9 s · p90 34,5 s · $0,016/câu, token vào "lạnh" ≈ 36.750 | ✅ **đủ** | Đủ mọi chỉ số AC8 liệt kê, kèm một phát hiện **ngược** ghi chép cũ (cache không trúng giữa hai câu) — đúng tinh thần §1.2 |
| **AC9** không còn `idle in transaction` | ✅ output nguyên văn §7 | ✅ **đủ** | Tôi đo lại ngay lúc review: `idle in transaction = 0`, tổng kết nối `agent_reader = 1` (phiên đo của tôi) |
| **AC10** tài liệu đồng bộ, không đá nhau | ⚠️ ledger **kể** đã chạy `git grep` và bắt được 2 chỗ, **không dán kết quả grep**; hai commit mới (`34071fc`, `653971e`) tiếp tục đóng hai chỗ đá nhau | ⚠️ **gần đủ** | AC đòi *"dán kết quả"*, chưa có. Tôi chạy lại: `git grep "8 function"` vẫn ra **`roadmap.md:321`** — *"Thiết kế đã có, **chưa duyệt** … 8 function … tài liệu duy nhất trong kho chưa qua kiểm chứng thực tế"*. Nằm trong khối `~~Điểm vào cho lát 10~~ — ĐÃ DÙNG XONG`, có rào và có ngày, nên nhẹ; nhưng `roadmap.md` là tài liệu **sống**. Vòng 1 đã nêu (G7), chưa đóng |

---

## 5. Ngoài phạm vi (spec §1) — vẫn sạch

Kiểm lại toàn bộ sau bốn commit sửa: `grep -rn "fastapi\|APIRouter\|uvicorn\|stream\|embedding" backend/agent backend/tests/agent` ⇒ **0 hit**; `backend/api` không đổi; `backend/etl` không đổi; migration head vẫn **`0020`**; `scripts/`, `deploy/` không đổi. **Không có scope creep**, kể cả trong các bản sửa.

---

## 6. Phán quyết

**Nhánh này đã đóng thật năm trong sáu phát hiện vòng 1 — bốn hình dạng dữ liệu nay đúng ở cả 8 function cho ca "sai loại chứng khoán", `topic` là enum đóng thật trong schema, hai seam S6/S7 nay kiểm đúng thứ chúng mang tên, và ba khẳng định nghiệm thu đã có bằng chứng hoặc đã hạ xuống đúng mức — nhưng chưa merge được: bản sửa `compare_peers` chữa một chỗ sai im lặng bằng cách tạo ra một chỗ sai tự tin, trả về mười mã không ai hỏi cho một câu hỏi về mã không tồn tại, và không test nào phủ ca đó. Đóng M1 (một điều kiện chặn trước truy vấn + một test), rồi merge; năm mục NÊN SỬA còn lại — `da_cat` của `get_price_series`, khoảng ngày của danh mục vĩ mô, `khoang_co_du_lieu` của hình dạng #3, docstring sổ nói quá, và tên test không tồn tại trong chính câu đính chính — đều nhỏ, nhưng phải hoặc sửa hoặc ghi thành nợ có tên, đừng để chúng biến mất giữa hai vòng review.**
