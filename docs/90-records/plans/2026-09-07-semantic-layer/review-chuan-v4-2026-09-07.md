# Review trục CHUẨN — vòng 4 (cửa cuối trước `main`)

Nhánh `feat/semantic-layer`. Diff soi: `6b99fb9~1..HEAD -- backend/` = ba commit
`6e2342f` · `6b99fb9` · `5e69011`, 13 file, +324/−59.

**HEAD đã chạy tiếp trong lúc review** (`5e69011` → `81dd1f8` → `b576643`); hai commit sau
chỉ chạm `docs/`, `git diff 5e69011..HEAD -- backend/` **rỗng**, nên mọi kết luận dưới đây
vẫn đúng với HEAD `b576643`.

Bộ test xanh trước khi soi:

```
$ set -a && . ./.env && set +a && cd backend && PYTHONIOENCODING=utf-8 uv run --project . pytest tests/agent/ -q
........................................................................ [ 60%]
................................................                         [100%]
120 passed in 3.96s
```

Mọi số dưới đây đo trên **kho dev 2026-09-07**, gọi thẳng hàm tool qua `AGENT_DATABASE_URL`
dưới role `dlck_api`, `EXPLAIN (ANALYZE, BUFFERS)` cho phần truy vấn, đọc thẳng mã SDK
`anthropic 1.4.0` cho phần chat. **Không gọi model thật.**

---

## 0. Việc làm được: mọi con số trong docstring mới đều tái lập được

Ghi trước phần lỗi, vì đây là thứ dễ hỏng nhất ở repo này (§1.2, §3.2). Đo lại từng khẳng
định do ba commit thêm vào:

| Khẳng định trong docstring/comment mới | Đo lại | |
|---|---|---|
| `macro.indicator` 64 + `asset.asset` 128 = **192 chuỗi** | 64 · 128 · 192 | ✅ |
| `BT6` có **5.764 phiên**, `2002-04-18..2026-09-04` | 5764, đúng hai mốc | ✅ |
| **356 mã** đang niêm yết có > 400 phiên | 356 | ✅ |
| `financial_statement` **27,3 triệu dòng** | 27.281.962 | ✅ |
| **1.523** mã `stock listed` | 1523 | ✅ |
| `metric_dictionary` `field_dictionary` **729 dòng** | 729 | ✅ |
| **24** ngành cấp 2 luôn có sẵn ⇒ `industry_code=None` không rơi nhánh không-tìm-thấy | `cay_nganh(None)` → `so_dong=24`, 6 nhóm | ✅ |
| SDK raise khi `max_tokens > 21.333`, **chỉ khi** client dùng timeout mặc định | `_calculate_nonstreaming_timeout` đúng ở dòng **762**; chốt gọi nó là `if not stream and not is_given(timeout) and self._client.timeout == DEFAULT_TIMEOUT` (`resources/beta/messages/messages.py:1105`) ⇒ client dự án đặt timeout riêng nên **bỏ qua thật** | ✅ |
| `84–152 token/s` · `đỉnh token ra 3.589` · `8 lượt gọi công cụ` | truy được về `review-chuan-v3:420` và `ledger.md:176` — là số đo, không phải số bịa | ✅ |

**Không docstring nào trong ba commit khẳng định một con số chưa đo.** Ngoại lệ duy nhất là
một khẳng định **suy luận** (không phải số) — mục N1.

---

## 🔴 CHẶN

### C1 · `backend/agent/tools/__init__.py:57` — hợp đồng gửi cho MODEL vẫn nói "Tối đa 8 kỳ"

**Vấn đề.** `5e69011` nâng `TRAN_KY` 8 → 20, nhưng docstring của `@beta_tool get_financials`
— chính là `description` gửi vào `tools=[...]` cho model — vẫn viết:

```python
        Tối đa 8 kỳ mỗi lần gọi.
```

Model đọc docstring, không đọc hằng số. Với câu này trong tay nó sẽ tự giới hạn `from_year`/
`to_year` về 8 kỳ và **không bao giờ chạm tới 20 kỳ vừa mở**. Nghĩa là với `get_financials`,
commit "open up the result limits" **không mở gì cả**.

**Bằng chứng đo.** Tại HEAD `b576643`:

```
$ git show HEAD:backend/agent/tools/__init__.py | grep -n "Tối đa"
57:        Tối đa 8 kỳ mỗi lần gọi.
76:        """So sánh nhiều mã ... Tối đa 10 mã."""
$ git show HEAD:backend/agent/tools/get_financials.py | grep -n "^TRAN_KY"
26:TRAN_KY = 20
```

Gọi thật xác nhận hằng số mới CÓ tác dụng, chỉ lời mô tả là sai:
`get_financials(FPT, IS, nam)` → `so_dong=20, da_cat=True`.

Đúng lỗi §1.7 (*sửa một chỗ, quét mọi chỗ*): `ledger.md` đã ghi bảng trần mới, nhưng chỗ
**duy nhất model thật sự đọc** thì bỏ sót.

**Đề xuất.** `Tối đa 20 kỳ mỗi lần gọi.` — hoặc bỏ hẳn con số và để `da_cat` nói, nhưng
đừng để một con số sai.

---

### C2 · `backend/agent/tools/__init__.py:76` — hợp đồng model vẫn nói "Tối đa 10 mã"

**Vấn đề.** Cùng bệnh C1, ở `compare_peers`: `TRAN_MA` 10 → **25**, docstring vẫn `Tối đa 10 mã.`

**Bằng chứng đo.** `compare_peers.py:35` → `TRAN_MA, TRAN_CHI_TIEU = 25, 15`; gọi thật với 26
mã có thật → trả 25 dòng, `da_cat=True`. Trần mới chạy; chỉ lời mô tả chặn model ở 10.

Đáng lưu ý: đây là **hai trong bảy trần** được nới ở `5e69011`, và là **đúng hai trần duy nhất
có nêu số bằng chữ trong docstring**. Năm trần còn lại (`screen_stocks`,
`get_corporate_events`, `get_news`, `get_macro_series`, `get_price_series`) không nêu số nên
không lệch — tức lượt sửa đã bỏ sót **100% số chỗ có thể bỏ sót**.

**Đề xuất.** `Tối đa 25 mã.` Sửa luôn `get_financials.py:4` (`"trần 8 kỳ"`) trong cùng lượt.

---

## 🟡 NÊN SỬA

### N1 · `agent/tools/compare_peers.py:117-125` — `da_cat` **vẫn** dương tính giả, và comment khẳng định điều đã sai

**Vấn đề.** `5e69011` nêu mục B2 "cờ `da_cat` hết dương tính giả" và viết lại comment:

```python
    #   mã, cỡ cắt thật duy nhất là len(mas_xin) > TRAN_MA — đã xét ở vế trái.
    da_cat = len(mas_xin) > TRAN_MA or (not mas_xin and len(rows) >= TRAN_MA)
```

Câu comment đó **đúng trước `6b99fb9`** (khi ấy `mas = mas_xin[:TRAN_MA]`), nhưng chính
`6b99fb9` — commit ngay trước — đã dời điểm cắt sang danh sách **hợp lệ**:

```python
    ma_hop_le = ma_hop_le_full[:TRAN_MA]      # compare_peers.py:75
```

Điều kiện đúng do đó là `len(ma_hop_le_full) > TRAN_MA`. Dùng `len(mas_xin)` khiến **mã không
tồn tại cũng được tính vào cỡ cắt**: cứ đủ mã bịa đẩy tổng vượt 25 là cờ bật, dù không dòng
nào bị cắt.

Nó cũng vi phạm thẳng luật đã ghi trong tài liệu thiết kế **sống**
(`docs/20-design/chatbot-semantic-layer.md:75`): *"Cắt kết quả thì phải trả `da_cat` **tính từ
kết quả thật**, không phải từ việc người gọi có xin nhiều hơn trần hay không."* — `mas_xin`
chính là "người gọi xin bao nhiêu".

**Bằng chứng đo.** Gọi thật, `TRAN_MA=25`, kho dev:

```
ca                                              xin  hop le  tra ve  da_cat   DUNG?
2 that + 30 bia                                  32       2       2    True     SAI  (cat that=False)
25 that + 1 bia                                  26      25      25    True     SAI  (cat that=False)
25 that + 5 bia                                  30      25      25    True     SAI  (cat that=False)
26 that (cat that 1 ma)                          26      26      25    True      OK  (cat that=True)
25 that (khong cat)                              25      25      25   False      OK  (cat that=False)
24 that + 2 bia                                  26      24      24    True     SAI  (cat that=False)
```

**4/6 ca sai.** Bảng phủ đủ theo yêu cầu: đúng bằng trần ✅ · dưới trần ✅ · trên trần ✅ ·
chỉ `industry_code` ✅ (nhánh rỗng, không có `da_cat`) · vừa mã vừa ngành ✅. Ca hỏng đúng là
ca thường gặp nhất: **mã thật lẫn mã gõ nhầm**.

Hệ quả không phải dữ liệu sai mà là **lời giải thích sai**: model bị bảo "danh sách đã bị cắt"
trong khi thứ thiếu đang nằm ngay cạnh ở `khong_tim_thay`.

**Đề xuất.**

```python
da_cat = len(ma_hop_le_full) > TRAN_MA or (not mas_xin and len(rows) >= TRAN_MA)
```

và sửa comment cho khớp. Test `test_da_cat_khong_bao_sai_khi_hoi_dung_bang_tran_ma` hiện chỉ
canh ca "toàn mã thật" nên không bắt được — thêm một ca `mã thật + mã bịa`.

---

### N2 · `agent/tools/compare_peers.py:58` — `resolve_ticker` fan-out **không còn trần nào**

**Vấn đề.** `6b99fb9` bỏ `mas = mas_xin[:TRAN_MA]` (đúng, để sửa F2) nhưng không thay bằng
trần nào khác, nên vòng resolve chạy trên **toàn bộ** danh sách model gửi:

```python
    tra = {t: resolve_ticker(conn, t) for t in mas_xin}
```

Mỗi mã = 1 truy vấn `_SQL_TRA_MA`; mã trượt cộng thêm 1 truy vấn `_SQL_GOI_Y` (trigram
`extensions.similarity` trên `market.security ⋈ issuer`). Schema công cụ (`__init__.py:74`,
`tickers: list[str] = []`) **không có `maxItems`**, nên số vòng do model quyết. Trước
`6b99fb9`, trần cứng là 10 truy vấn.

**Bằng chứng đo.** Đếm bằng `before_cursor_execute` trên engine thật:

```
25 ma CO THAT  (ca tot)                     29 ms |   28 SQL
25 ma BIA      (ca xau: resolve + goi y)   139 ms |   50 SQL
30 ma BIA                                  183 ms |   60 SQL
100 ma BIA                                 613 ms |  200 SQL
500 ma BIA                               2.882 ms | 1000 SQL
```

Ca xấu nhất **trong trần hiện hành** (25 mã, toàn trượt) = 50 round-trip / 139 ms — chấp nhận
được. Nhưng đường đó không có chốt: tuyến tính, do đầu vào của model điều khiển.
`statement_timeout = 20s` ở `build_tools.chay` **không chặn** vì nó tính trên **từng câu
lệnh**, không phải trên cả lời gọi tool.

**Đề xuất.** Một dòng là đủ, giữ nguyên phần sửa F2: cắt `mas_xin` ở một trần vào rộng (ví dụ
`mas_xin[:TRAN_MA * 4]`) trước vòng resolve, và báo phần bị bỏ. Trần vào rộng hơn `TRAN_MA`
vẫn giữ đúng tinh thần F2 ("mã thứ 11 có thật vẫn phải nhận ra").

---

### N3 · `agent/chat.py:36` + `agent/__main__.py:22` — nâng **cả hai** hệ số, trần chờ một lượt tăng 10×

**Vấn đề.** `6e2342f` nâng `MAX_ITERATIONS` 8 → 16 **và** timeout 120 → 600 s. Hai con số này
nhân với nhau, mà không có deadline nào cho cả lượt. Review vòng 3 đã nêu đúng chỗ này
(`review-chuan-v3:429`: *"không có deadline cho cả lượt. `MAX_ITERATIONS = 8` × 120 s ⇒ một
lượt hỏi có thể treo tới 16 phút"*) và đề xuất **chọn một** trong ba cách; lượt sửa chọn cách 1
(nâng timeout) nhưng đồng thời nâng luôn số vòng — nên ghi chú "phụ, cùng hướng" kia **xấu đi
10 lần** thay vì được xử lý.

**Bằng chứng đo.** Đọc thẳng từ client dựng đúng như production, không gọi model:

```
CHAT_TIMEOUT_S = 600.0 | settings.timeout_s = 600.0
anthropic client .timeout   = 600.0
httpx client .timeout       = Timeout(timeout=600.0)
max_retries                 = 3
MAX_ITERATIONS = 16 MAX_TOKENS = 32000

--- tran cho toi da MOT luot chat ---
  khong retry : 16 vong x 600s =  9.600s =  2,7 gio
  co retry(3) : x4             = 38.400s = 10,7 gio
  (truoc 3 commit: 8 x 120 = 960s = 16 phut; x4 = 64 phut)
```

Trần token ra lý thuyết một lượt cũng đi từ `8 × 32.000 = 256.000` lên **`16 × 32.000 =
512.000`**. Đây là rủi ro đuôi chứ không phải chi phí thường trực (Token Plan tính theo token
thực dùng; đỉnh đo được mới 3.589) — nhưng là con số **không ai canh**: `repl` chỉ thoát bằng
Ctrl+C.

**Đề xuất.** Thêm deadline cho cả lượt trong `run_turn` — mốc `time.monotonic()` đã có sẵn ở
dòng 84, chỉ cần so với một hằng `TRAN_GIAY_MOT_LUOT` (ví dụ 900 s) và thoát vòng `for` như
nhánh "dừng giữa chừng". Không cần đụng vào hai hằng vừa nâng.

---

### N4 · `agent/__main__.py:22` — `CHAT_TIMEOUT_S` kéo theo cả `token_plan_remains`

**Vấn đề.** `LLMClient.__init__` dựng **một** `httpx2.Client(timeout=settings.timeout_s)` dùng
chung cho cả SDK lẫn `token_plan_remains()`. Nâng timeout lên 600 s cho vòng chat nâng luôn cho
lời gọi quota — mà `repl` gọi quota **sau mỗi lượt** (`chat.py:129`). Docstring của
`CHAT_TIMEOUT_S` chỉ lập luận cho request sinh chữ, không nhắc hệ quả này.

**Bằng chứng đo.** `cl._http.timeout` → `Timeout(timeout=600.0)`. Endpoint quota treo ⇒ REPL
đứng im 10 phút rồi mới in `[... không đọc được quota: ...]`; trước đây 2 phút.

**Đề xuất.** Thêm một câu vào docstring `CHAT_TIMEOUT_S`, hoặc truyền timeout ngắn riêng cho
`self._http.get(...)` trong `token_plan_remains` (`client.py:126`) — đây là lời gọi phụ trợ,
không cần 600 s.

---

### N5 · `agent/tools/get_financials.py:4` và `tests/agent/test_a09_screener.py:102` — hai con số cũ còn sót

**Vấn đề.** Cùng họ C1/C2, mức nhẹ hơn vì không phải hợp đồng model:

- `get_financials.py:4` — `"...mã chỉ tiêu; trần 8 kỳ."` (nay 20).
- `test_a09_screener.py:102` — docstring `"xin limit=500 (bị hạ về trần 50)"` (nay **200**).
  Test vẫn đúng về hành vi (NGANHANG chỉ có 4 mã nên `da_cat=False` bất kể trần), chỉ lời
  giải thích sai.

**Bằng chứng đo.** Trả lời luôn câu hỏi *"còn test nào mã hoá cứng trần cũ mà lượt sửa bỏ sót
không"* — rà toàn `tests/agent/`:

```
$ grep -rn "monkeypatch.setattr" tests/agent/*.py
test_a05_price.py:76     TRAN_PHIEN -> 2    (hạ trần — bất biến trước mọi lần nới)
test_a09_screener.py:198 TRAN_MA    -> 3    (nt)
$ grep -rn "TRAN_KY\|TRAN_MA" tests/agent/*.py    # đều import hằng từ module, không viết số
```

⇒ **Không còn test nào xanh giả vì trần đổi.** Hai test nêu trong commit message
(`test_qua_10_ma_bi_cat_va_bao_da_cat`, `test_tran_tam_nam`) đã sửa đúng cách; các test còn
lại dùng `limit=` tường minh nhỏ hoặc `monkeypatch` hạ trần nên bất biến (§4.4.4). Chỉ còn
**chữ** trong hai docstring là lệch.

---

## ⚪ GHI NHẬN

### G1 · Nới trần **không làm hỏng gì** về hiệu năng — đo đủ bảy chỗ

Câu hỏi *"nới trần có làm gì hỏng không"*: **không**, ở phía DB. Gọi thẳng hàm tool, kho thật:

| Lời gọi | Thời gian | Kích thước JSON |
|---|---|---|
| `get_price_series("BT6")` — 2.000 phiên | 42 ms | **300.042 B** |
| `get_financials(FPT, IS, nam)` — 20 kỳ | 45 ms | 11.408 B |
| `get_macro_series()` danh mục 250 | 6 ms | 18.797 B (**192 mục, `da_cat=False`**) |
| `get_macro_series("us.rate.fedfunds.daily", limit=2000)` | 16 ms | 150.172 B |
| `screen_stocks(limit=200)` | 17 ms | 67.054 B |
| `get_corporate_events("FPT", limit=200)` | 4 ms | 20.308 B (177 sự kiện, `da_cat=False`) |
| `get_news(query="ngân hàng", limit=100)` | 69 ms | 52.990 B |

Không lời gọi nào vượt 200 ms; `statement_timeout = 20s` còn dư rất xa. Danh mục vĩ mô nay
trả **đủ 192/192** — đúng như commit tuyên bố.

**`TRAN_KY = 20` không tốn thêm một byte DB nào.** Lý do: `_SQL_BCTC` **không có `LIMIT`** —
trần cắt ở Python (`khoa[:TRAN_KY]`, dòng 98). Nên `EXPLAIN ANALYZE` trước/sau **giống hệt
nhau**, không có gì để so:

```
--- FPT, IS, quy (length 1..4) ---
Sort (cost=8559.56..8559.74 rows=71) (actual time=161.101..161.117 rows=602 loops=1)
  -> Hash Left Join ... -> Bitmap Heap Scan on financial_statement
       BitmapAnd: financial_statement_pkey + ..._metric_code_year_report_length_report_idx
       Buffers: shared hit=306 read=700
Execution Time: 161.155 ms
   => SQL tra ve 602 dong (86 ky phan biet); Python moi cat con 20
```

Câu này đã trả 602 dòng / 86 kỳ **từ trước khi nới**; 8 → 20 chỉ đổi số kỳ được **in ra**.

### G2 · `TRAN_PHIEN = 2000` — model nuốt nổi, nhưng 20% payload là dư thừa

`get_price_series("BT6")` = **292.009 ký tự / 300.042 byte** cho một lời gọi.
Ước token: 73.000 (4 ký tự/token) — 180.000 (1,62 ký tự/token, tỷ lệ tiếng Việt đo ở
`minimax.md`); nội dung là ngày + số ASCII nên nằm gần cận dưới, ~**90–120k token**.

Ngữ cảnh 1M ⇒ **nuốt được**. Hai điều đáng ghi, không đáng chặn:

1. `minimax.md:22` ghi *"Ngữ cảnh 1M token, **tối thiểu đảm bảo 512K**"* và `minimax.md:38`
   ghi *"> 512K **gấp đôi**"* giá. Lập luận "ngữ cảnh 1 triệu token nên chỗ chứa không phải
   ràng buộc" — lặp bảy lần trong `5e69011` — bỏ qua ngưỡng 512K này. Ba lời gọi
   `get_price_series` đầy trần trong một phiên (~330k token) cộng lịch sử là đã tới ngưỡng đó.
2. **19,9% payload là `ngay_hien_thi` lặp lại chính `ngay`** — 58.000/292.009 ký tự cho
   2.000 phiên. Một phiên:
   `{"ngay":"2018-08-29","ngay_hien_thi":"29/08/2018","dong_cua":"2.500 đ",...}`.
   Ở trần 400 cũ không đáng nói; ở 2.000 là ~15k token dư mỗi lời gọi.

### G3 · Phiên tràn cửa sổ ngữ cảnh **không có đường ra**

`6e2342f` đưa `model_context_window_exceeded` vào `STOP_KHONG_DUNG_LAI_DUOC` — **đúng**, và
lý do trong comment chính xác. Nhưng hệ quả đầy đủ: `repl` giữ `history` mãi mãi và **không có
lệnh nào xoá/cắt lịch sử**. Khi lịch sử cũ tự nó đã sát trần, mọi lượt sau đều tràn → đều bị
bỏ → in đúng một câu `[lượt này dừng giữa chừng (model_context_window_exceeded) ...]` vô hạn.
Lối thoát duy nhất là Ctrl+C rồi chạy lại.

Trước `6e2342f` thì tệ hơn (lịch sử tràn được nối thêm), nên đây **không phải hồi quy** — chỉ
là ngõ cụt nay dễ tới hơn vì payload đã to gấp 5 (G2). Một lệnh `/moi` trong `repl` xoá
`history` là đủ.

### G4 · `STOP_KHONG_DUNG_LAI_DUOC` — không thiếu, không quá tay

Đối chiếu danh sách thật (`anthropic/types/beta/beta_stop_reason.py`, `anthropic 1.4.0`) và
chính phân loại của SDK (`lib/tools/_beta_runner.py:62-71`):

| `stop_reason` | SDK xếp | Nên nằm trong danh sách bỏ lượt? |
|---|---|---|
| `end_turn`, `stop_sequence` | stop | Không — kết thúc bình thường |
| `max_tokens` | stop | Không — F3 vòng 2 đã trả giá đúng chỗ này; lịch sử vẫn hợp lệ |
| `tool_use` | run_tools | Không — đã bắt riêng bằng phép kiểm hình dạng `content` |
| `pause_turn` | **resume** | Không — SDK ghi rõ *"send it back unchanged, the server continues it"* |
| `compaction` | **resume** | Không — cùng lý do |
| `model_context_window_exceeded` | stop | **Có** ✅ |
| `refusal` | stop | **Có** ✅ |

⇒ Danh sách **đủ và đúng**: không sót giá trị nào, không đưa nhầm giá trị nào.
(`pause_turn`/`compaction` chỉ lọt vào `cuoi` nếu chạm `MAX_ITERATIONS` ngay tại lượt đó; khi
ấy lịch sử kết thúc bằng `assistant` nên vẫn hợp lệ với Messages API. MiniMax không phát hai
giá trị này.)

### G5 · Đường khởi động `__main__.py` không có test nào canh

`replace(LLMSettings.from_env(), timeout_s=CHAT_TIMEOUT_S)` là thay đổi **duy nhất** ở đường
production và **không test nào chạm tới** — `grep -rn "CHAT_TIMEOUT_S\|agent.__main__" tests/`
ra rỗng; `test_a13_chat.py` tự dựng settings với `timeout_s=30`.

Tôi kiểm tay thay cho test (§3.5 — *kiểm lệnh, không kiểm trạng thái hiển thị*) và **nó chạy
đúng**: `anthropic client .timeout = 600.0`, `httpx client .timeout = Timeout(timeout=600.0)`.
Nên không phải lỗi — chỉ là chỗ không ai canh nếu `LLMSettings` đổi tên trường sau này.

### G6 · Lỗi CÓ SẴN, ngoài ba commit: `get_news()` không tham số **luôn nổ** trên kho dev

Không do ba commit này gây ra — nêu theo §4.4.3 (*rác có sẵn thì báo, không tự xoá*), và vì nó
chặn đúng lời gọi tự nhiên nhất của model ("tin mới nhất").

```
khong loc gi ("tin moi nhat")           -> LOI  AttributeError: 'NoneType' object has no attribute 'strftime'
ticker=HPG                              -> OK   so_dong=6
group_no=1 / sub=1a / query / from_date -> OK
```

Nguyên nhân: `47/8.220` bài có `published_at IS NULL` ⇒ `_NGAY_VN` ra `NULL`; mà
`ORDER BY a.published_at DESC` trong Postgres là **`DESC NULLS FIRST`** ⇒ 47 bài đó luôn đứng
đầu khi không có bộ lọc ngày. `format_date_vi(None)` (`format.py:70`) nổ.

**Không phải do nới trần** — đo cả trần cũ lẫn mới đều nổ như nhau:

```
mac dinh CU (10)  -> CRASH      tran CU (30)   -> CRASH
mac dinh MOI (15) -> CRASH      tran MOI (100) -> CRASH
```

Mức độ thật thấp hơn vẻ ngoài: `_generate_tool_call_response` của SDK bọc `tool.call()` trong
`try/except Exception` nên model nhận `tool_result` báo lỗi, tiến trình không chết. Fixture
test không có bài nào `published_at IS NULL` nên 120 test xanh vẫn không thấy.

**Đề xuất** (một lượt riêng, đừng nhét vào lượt này): `format_date_vi` trả `None` khi vào
`None`, hoặc thêm `NULLS LAST` vào `ORDER BY`.

---

## Kết

**Merge được sau khi sửa C1 và C2** — hai dòng docstring nói sai trần với chính model, khiến
`5e69011` không đạt mục đích của nó ở hai trong bảy công cụ; phần còn lại của ba commit sạch,
mọi con số đo lại đều khớp, và không test nào xanh giả sau khi nới trần.
