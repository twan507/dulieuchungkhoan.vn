# Review trục CHUẨN — vòng 2 (`backend/agent/`, lát 10)

Diff soi: `4ff1e62..4c72c09 -- backend/` (bốn commit sửa `597e546`, `7277a5e`, `a82e600`, `437626c`) · 18 file.
Nhánh `feat/semantic-layer`. **Lưu ý:** HEAD đã chạy tiếp tới `653971e` trong lúc review — hai commit đó chỉ chạm `docs/`, `backend/` không đổi kể từ `4c72c09`.

Bộ test chạy xanh trước khi soi:

```
$ set -a && . ./.env && set +a && cd backend && pytest tests/agent/ -q
........................................................................ [ 72%]
...........................                                              [100%]
99 passed in 3.80s
```

Mọi con số dưới đây đo trên **kho dev 2026-09-07**, gọi thẳng hàm tool (nhiều chỗ gọi qua
`tool.call(...)` — đúng đường model đi, có pydantic validate). Không gọi model thật.

---

## 1. Bảng kiểm các bản sửa vòng 1

| Mục | Kết quả | Bằng chứng ngắn |
|---|---|---|
| **C1** múi giờ `get_news` | ✅ **sửa đúng, không sót nhánh** | lọc ngày VN 06/09: kho 229 — tool `tong_khop=229`; bài `23:28+00` nay khai `2026-09-07`; `published_at` là cột `timestamptz` **duy nhất** agent lọc, mọi lối đi đều qua `_NGAY_VN`. Kèm hệ quả kế hoạch truy vấn → **F5** |
| **C2** lịch sử chat | 🟡 **sửa đúng phần chính, thừa tay + còn khe hở** | hai ca CHẶN cũ nay bỏ lượt, giữ lịch sử (đo bằng MockTransport). Nhưng `max_tokens` khi lượt cuối **chỉ có text** cũng bị vứt → **F3**; còn `pause_turn` và `end_turn` rỗng → **G7/G8** |
| **N1** khoá `version` revision | 🟡 **đúng ngữ nghĩa, hỏng kế hoạch truy vấn** | `JOIN LATERAL` chặn hẳn GIN `article_revision_tsv_idx`: 158ms vs 27ms, cost 68.307 vs 1.302 → **F4** |
| **N2** cờ `da_cat` | ✅ **sửa đúng, mọi caller đã đổi** | `cap_limit` nay trả `int`; 4 caller (`get_news`, `get_macro_series`, `get_corporate_events`, `screen_stocks`) đều dùng dạng một giá trị, không sót chỗ nào còn unpack tuple. Sự kiện FPT: `so_dong=20, da_cat=True` (trước: `False`). Riêng `compare_peers` còn nói quá → **G2** |
| **N3** danh mục macro | ✅ **sửa đúng** | không keyword: `40 mục / tong_khop=192 / da_cat=true`; keyword `vn`: `40 / 69 / true` |
| **N4** `compare_peers` | ❌ **SỬA HỎNG THÊM — CHẶN mới** | `tickers=["ZZZZ"]` → **10 mã lạ** `A32, AAA, AAH…` kèm `so_dong=10` → **F1** |
| **N5** `get_price_series` cắt câm 400 phiên | ❌ **CHƯA SỬA** | `BT6`: kho 5.764 phiên (2002→2026), tool trả 400 phiên (từ 2025-01-21), khoá trả về không có `da_cat`. 356 mã có >400 phiên → **G1** |
| **N6** `criteria` sai hình dạng | 🟡 **sửa đúng trong `screen_stocks`; sót một kiểu và không đồng bộ file khác** | thiếu khoá / không phải object / falsy đều ra `{"loi":true,...}` ✅; nhưng `value: true` (bool) lọt qua `isinstance(..., (int,float))` → `ProgrammingError` → **F6**. `get_financials`/`compare_peers` vẫn ném `TypeError` khi gọi thẳng (pydantic chặn trên đường model) → **G5** |
| **N7** test sổ `ops.llm_call` | 🟡 **sửa đúng phần quan trọng, còn hai điểm** | nay gọi CHÍNH `log_llm_call` dưới `SET LOCAL ROLE dlck_etl` ✅; nhưng **không assert 4 loại token** như đề xuất, và **import rác `from agent.db import ops_engine` (`test_a12_tools_log.py:10`) vẫn còn nguyên** → **G4** |
| **N8a** `get_industry_tree` hình dạng | ❌ **CHƯA SỬA** | `get_industry_tree(industry_code="KHONGCO")` → `{"nhom": []}`, không `tim_thay`, không `co_du_lieu` → **F7** |
| **N8b** `get_news` đổ lỗi sai chỗ | ✅ **sửa đúng** | `get_news(ticker="ZZZZ")` → `{"tim_thay": false, "ma_da_tra": "ZZZZ", "goi_y": []}`, không còn `ghi_chu` |

*(Nhóm GHI NHẬN G1–G10 của vòng 1 không nằm trong phạm vi bắt buộc; chỉ soi lại chỗ bản sửa
chạm vào — xem G4, G6.)*

---

## 2. Phát hiện mới

### 🔴 F1 · CHẶN · `agent/tools/compare_peers.py:44-46, 57, 61` — bản sửa N4 làm bộ lọc mã **tự tắt** khi mọi mã đều tra trượt

**Vấn đề.** Bản sửa thay tham số truyền vào SQL từ `mas` (danh sách model xin) sang `ma_hop_le`
(danh sách đã lọc qua `resolve_ticker`). Nhưng điều kiện SQL vẫn là

```sql
AND (cardinality(CAST(:mas AS text[])) = 0 OR upper(s.ticker) = ANY(:mas))
```

`cardinality = 0` là **mã hiệu "không lọc theo mã"**. Mọi mã tra trượt ⇒ `ma_hop_le = []` ⇒ vế
đầu đúng ⇒ **bộ lọc biến mất**, câu lệnh trả 10 mã đầu bảng chữ cái của toàn sàn.

**Bằng chứng (gọi qua `tool.call`, đúng đường model đi).**

```
compare_peers({"tickers": ["ZZZZ"]})
 -> {"tim_thay": true, "co_du_lieu": true, "so_dong": 10,
     "du_lieu": [{"ma":"A32",...},{"ma":"AAA"},{"ma":"AAH"},{"ma":"AAM"},{"ma":"AAN"},
                 {"ma":"AAS"},{"ma":"AAT"},{"ma":"AAV"},{"ma":"ABB"},{"ma":"ABC"}],
     "khong_tim_thay": ["ZZZZ"], "da_cat": true}

compare_peers({"tickers": ["ZZZZ"], "industry_code": "NGANHANG"})
 -> 10 mã ngân hàng đầu bảng chữ cái, cũng không ai xin
```

**Đây là hồi quy do chính bản sửa đẻ ra.** Bản trước (`git show 4ff1e62:…/compare_peers.py:44`)
truyền `mas` thô ⇒ `cardinality=1` ⇒ lọc vẫn chạy ⇒ 0 dòng ⇒ trả `rong()`. Tức là **trước khi
sửa, ca này đúng; sau khi sửa, sai**.

**Vì sao là CHẶN.** Model hỏi so sánh một mã gõ nhầm và nhận về **bảng chỉ tiêu đầy đủ của 10
doanh nghiệp không liên quan**, gắn nhãn `co_du_lieu: true, so_dong: 10`. `khong_tim_thay`
nằm cuối payload không cứu được: hình dạng nói "đây là kết quả so sánh của bạn". Cùng loại lỗi
với N2 mà vòng 1 gọi tên — sinh câu trả lời sai một cách thầm lặng, chỉ nặng hơn.

Test hiện có không bắt được vì mọi case đều **có ít nhất một mã hợp lệ**
(`test_ma_khong_tra_duoc_bi_bao_ro_khong_am_tham_nuot` dùng `["HPG","ZZZZ"]`).

**Đề xuất.** Tách mã hiệu "không lọc" khỏi "lọc ra rỗng" — đừng để hai chuyện dùng chung một
biểu thức:

```python
if mas and not ma_hop_le:           # xin theo mã mà không mã nào tra được
    return to_json({**rong(), "ngay_du_lieu": str(ngay), "khong_tim_thay": khong_ton_tai})
```

(hoặc đổi điều kiện SQL thành `CAST(:loc_theo_ma AS bool) IS FALSE OR upper(s.ticker) = ANY(:mas)`
với `loc_theo_ma = bool(mas)`). Kèm test `tickers=["ZZZZ"]` một mình.

---

### 🔴 F2 · CHẶN · `agent/tools/get_corporate_events.py:18, 44` — nhánh "loại chứng khoán này không có" **nói sai về kho**, và đây cũng là hồi quy

**Vấn đề.** Bản sửa `437626c` thêm nhánh: `ma["loai"] != "stock"` ⇒ trả
`khong_co_du_lieu(loai, "kho không có sự kiện doanh nghiệp cho chứng chỉ quỹ ETF")`. Docstring
dòng 16-17 khẳng định *"sự kiện doanh nghiệp gắn với issuer, nên chỉ số và ETF/chứng chỉ quỹ
**không bao giờ có**"*. **Khẳng định này chưa đo và nó sai.**

**Bằng chứng.**

```
-- so ma NON-stock co su kien trong market.corporate_event:
   ('etf', 18 ma)  ('fund_cert', 3 ma)

  FUCVREIT   etf   kho co 14 su kien (CashDividend: 2) moi nhat 2026-02-26
  FUESSV50   etf   kho co 13 su kien
  E1VFVN30   etf   kho co 10 su kien
  issuer cua FUCVREIT co dung chung voi ma stock nao khong: 0   (khong phai su kien di lac)

tool tra loi:
  get_corporate_events({"ticker":"FUCVREIT"})
  -> {"tim_thay": true, "co_du_lieu": false, "loai": "etf",
      "ly_do": "kho không có sự kiện doanh nghiệp cho chứng chỉ quỹ ETF", "ma": "FUCVREIT"}
```

Model hỏi *"FUCVREIT đã trả cổ tức bao giờ chưa"* nay nhận một câu **phủ định dứt khoát** trong
khi kho có 2 đợt `CashDividend` cho đúng mã đó. Bản trước sửa đi thẳng vào truy vấn theo
`issuer_id` và **trả đủ 14 sự kiện** — lại là hồi quy do bản sửa tạo ra.

Đây đúng hai luật đã trả giá của repo: **§3.6** (kết luận phủ định về cả một lớp, suy từ một
quan sát hẹp) và **§1.2** (viết ra một sự thật về kho mà không đo). Đo `financial_statement` thì
khẳng định tương tự **đúng** (0 issuer non-stock có BCTC) — nên `get_financials` không dính; chỉ
`get_corporate_events` chép nguyên câu chữ sang mà không đo lại.

Test `test_chi_so_khong_co_su_kien_la_hinh_dang_2_khong_phai_rong` chỉ kiểm `VNINDEX` — vùng mà
lời khẳng định đúng, nên không ai bắt được phần sai.

**Đề xuất.** Thu nhánh về đúng phần đã đo: chỉ `index` mới là "loại này không bao giờ có"
(`index` không có `issuer_id` thật). ETF/`fund_cert` để chạy tiếp truy vấn — có dòng thì trả,
không có thì `rong()`. Sửa cả docstring cho khớp số đo, kèm ngày đo.

---

### 🟠 F3 · NÊN SỬA · `agent/chat.py:73-78` — `ket_sach` quét quá rộng: vứt luôn câu trả lời **hợp lệ** bị cắt cuối

**Vấn đề.** Điều kiện `stop_reason in ("end_turn","stop_sequence")` biến **mọi** ca `max_tokens`
thành "bỏ lượt". Nhưng ca C2 chỉ hỏng khi `max_tokens` rơi **giữa một block `tool_use`**. Khi
lượt cuối chỉ có `text`, lịch sử **không** vi phạm hợp đồng nào: mọi `tool_use` đã có
`tool_result`, message cuối là assistant. Bỏ cả lượt là ném đi cả câu trả lời lẫn toàn bộ công
tra cứu đã tốn.

**Bằng chứng (MockTransport, không gọi model thật).**

```
== max_tokens giua VAN BAN (khong tool_use) ==
  tra_loi : [lượt này dừng giữa chừng (max_tokens) — bỏ lượt, lịch sử giữ nguyên như trước...]
  lich su : [] | so message: 0        <-- van ban model da viet bi vut

== goi tool xong roi max_tokens giua van ban ==
  tra_loi : [lượt này dừng giữa chừng (max_tokens) — ...]
  lich su : []                        <-- mat luon ket qua cua luot goi cong cu
```

Không phải ca hiếm: chú thích `chat.py:37` ghi *"4000 CẮT THẬT 3/40 request (đo 2026-09-07)"*.

**Đề xuất.** Tách "lịch sử bẩn" khỏi "câu trả lời cụt":

```python
co_tool_treo = cuoi is not None and any(b.type == "tool_use" for b in cuoi.content)
ket_sach = cuoi is not None and not co_tool_treo and cuoi.stop_reason != "model_context_window_exceeded"
```

rồi khi `stop_reason == "max_tokens"` mà có `tra_loi` thì **giữ lịch sử** và gắn thêm
`"[câu trả lời bị cắt vì chạm max_tokens]"`. Cắt giữa block `thinking` không lọt lưới này: khi
đó không có block `text` nào nên `tra_loi` rỗng và lượt vẫn bị bỏ.

Phụ: ca `refusal` cũng bị gộp vào chung một câu khuyên *"thử hỏi ngắn gọn hơn"* — sai lời khuyên
cho đúng tình huống model từ chối.

---

### 🟠 F4 · NÊN SỬA · `agent/tools/get_news.py:52-56` — bản sửa N1 (`JOIN LATERAL`) **chặn hẳn** index GIN của tìm toàn văn

**Vấn đề.** Khoá bản mới nhất bằng `JOIN LATERAL (… ORDER BY version DESC LIMIT 1) r ON true`
đẩy vị từ `r.tsv @@ …` ra **ngoài** subquery. Postgres không còn đường nào dùng
`article_revision_tsv_idx`: kế hoạch buộc phải quét **mọi** bài rồi mới lọc.

**Bằng chứng (EXPLAIN ANALYZE, cùng câu hỏi `'lãi suất điều hành'`, 8.175 bài).**

```
SAU N1 (JOIN LATERAL):     Nested Loop, loops=8175, cost=68.307, 158,3 ms, buffers 51.476
TRUOC N1 (join thang):     Hash Join,               cost= 1.302,  27,0 ms, buffers 27.772
```

Ép `enable_seqscan=off` vẫn **không** ra index scan cho bản LATERAL (34,6 ms, vẫn 8.175 loops) —
tức đây là chặn về cấu trúc, không phải chuyện thống kê. Một lời gọi `get_news(query=…)` chạy
hình dạng này 2 lần (đếm + lấy dòng), 4 lần khi phải lùi `plainto`; đo thật hôm nay: **77,7 ms**
cho một lời gọi trên kho 8k bài. Chi phí tăng tuyến tính theo số bài (~230 bài/ngày).

**Đề xuất** — giữ vị từ `tsv` trên chính bảng được quét, khoá bản mới nhất bằng anti-join:

```sql
FROM news.article a
JOIN news.article_revision r ON r.article_id = a.article_id
WHERE r.tsv @@ … 
  AND NOT EXISTS (SELECT 1 FROM news.article_revision r2
                  WHERE r2.article_id = r.article_id AND r2.version > r.version)
```

Đo thử ngay trên kho dev — planner **dùng được** GIN:

```
Bitmap Index Scan on article_revision_tsv_idx  … cost=2.497 … 12,7 ms
```

Ngữ nghĩa không đổi (test `test_join_revision_khoa_ban_moi_nhat_khong_nhan_doi` vẫn là chốt canh).

---

### 🟠 F5 · NÊN SỬA · `agent/tools/get_news.py:33` — `AT TIME ZONE` trong vế lọc làm mất index `published_at`

Bản sửa C1 **đúng về ngữ nghĩa** (xem bảng kiểm), nhưng viết vế lọc dưới dạng biểu thức trên cột
⇒ `article_published_at_idx` hết dùng được:

```
loc theo ngay VN :  Seq Scan on article,  rows=266,  buffers 227,  1,66 ms
                    (uoc luong sai: planner doan 2.723 dong, thuc te 266)
loc thang tren published_at: Index Only Scan using article_published_at_idx, buffers 114, 0,54 ms
```

Hôm nay vô hại (8.175 bài). Hai hệ quả khi kho lớn lên: quét tuần tự tăng tuyến tính, và **ước
lượng số dòng sai gần 10 lần** khiến planner chọn sai thứ tự join cho câu lớn.

**Đề xuất** — giữ vế lọc sargable, chỉ ép múi giờ ở cột **hiển thị** (ngữ nghĩa hệt như hiện tại):

```sql
-- loc: mốc nửa đêm giờ VN quy về timestamptz
(CAST(:tu AS date) IS NULL OR a.published_at >= (CAST(:tu AS date))::timestamp AT TIME ZONE 'Asia/Ho_Chi_Minh')
(CAST(:den AS date) IS NULL OR a.published_at <  (CAST(:den AS date) + 1)::timestamp AT TIME ZONE 'Asia/Ho_Chi_Minh')
-- hien thi: giu nguyen (a.published_at AT TIME ZONE 'Asia/Ho_Chi_Minh')::date AS ngay_vn
```

Hai test C1 hiện có (`test_ngay_hien_thi_theo_gio_vn…`, `test_bo_loc_ngay_theo_gio_vn_khong_lot_luoi`)
đủ sức canh phép viết lại này — chúng kiểm biên `23:30+00`, đúng chỗ dễ sai.

---

### 🟠 F6 · NÊN SỬA · `agent/tools/screen_stocks.py:56` — chốt chặn `value` lọt kiểu `bool`

`isinstance(True, int)` là `True`, nên `value: true` qua được vòng kiểm rồi chết ở tầng SQL —
đúng cái N6 muốn dẹp. Đây là **đường model đi được** (pydantic chỉ soi `list[dict]`, không soi
giá trị bên trong):

```
screen_stocks({"criteria":[{"metric_code":"rtd21","operator":"<","value":true}]})
 -> NEM ProgrammingError: operator does not exist: numeric < boolean
```

SDK bọc lại thành `is_error` nên chat không sập, nhưng model nhận một chuỗi lỗi Postgres thô
thay vì `{"loi": true, "ly_do": "value phải là số…"}` mà chính file này trả cho mọi ca khác.

Sửa: `if isinstance(c["value"], bool) or not isinstance(c["value"], (int, float)):`.

---

### 🟠 F7 · NÊN SỬA · `agent/tools/get_industry_tree.py:51` — N8a chưa sửa, nay là **chỗ duy nhất** còn lệch khuôn

Bản sửa `437626c` chuẩn hoá bốn hình dạng trạng thái cho `get_financials`,
`get_corporate_events`, `compare_peers`, `get_news` — nhưng bỏ sót `get_industry_tree`:

```
get_industry_tree({"industry_code":"KHONGCO"}) -> {"nhom": []}
```

Không `tim_thay`, không `co_du_lieu` — đúng cái docstring `_shared.py:3-5` cấm ("phân biệt bằng
TRƯỜNG TƯỜNG MINH chứ không bằng độ dài mảng"). Càng đáng sửa vì sau đợt này nó là **ngoại lệ
duy nhất**, tức người đọc code sẽ tưởng đó là khuôn cố ý.

---

## 3. Ghi nhận

**G1 · `get_price_series` (N5) chưa sửa, và trên kho thật nó nặng hơn vòng 1 đo được.**
Vòng 1 chỉ có HPG (60 phiên) nên không chạm tới. Đo lại:

```
BT6: kho co 5.764 phien (2002-04-18 .. 2026-09-04)
get_price_series({"ticker":"BT6","from_date":"2000-01-01"})
 -> so_dong = 400, ngay dau = 2025-01-21
 -> khoa tra ve: co_du_lieu, du_lieu, ghi_chu, gia_dieu_chinh, ma, so_dong, tim_thay   (KHONG co da_cat)
356 ma dang niem yet co >400 phien
```

Mất 5.364 phiên **đầu** khoảng hỏi, không một trường nào báo. Sau đợt sửa N2 thì đây là công cụ
**duy nhất** còn cắt câm — mọi công cụ anh em đều đã có `da_cat`. Xếp GHI NHẬN vì vòng 1 đã nêu
và chủ dự án có thể đã cố ý hoãn; nếu chưa quyết thì nên xử cùng đợt (một dòng `da_cat`, và cân
nhắc đổi `LIMIT` thành "giữ 400 phiên **gần nhất** *hoặc* nói rõ đã bỏ phần đầu").

**G2 · `compare_peers.py:86` — `da_cat` nói quá khi xin đúng 10 mã.** `len(rows) >= TRAN_MA`
báo `True` dù không cắt gì:

```
compare_peers 10 ma hop le -> so_dong: 10, da_cat: True   (xin dung 10, khong cat gi)
compare_peers 1 ma         -> so_dong: 1,  da_cat: False  (dung)
```

Chiều nói quá ít hại hơn chiều nói thiếu, nhưng ở đây tính chính xác được: khi model xin theo
`tickers`, cắt chỉ xảy ra nếu `len(mas_xin) > TRAN_MA`; heuristic `len(rows) >= TRAN_MA` chỉ cần
cho nhánh `industry_code`.

**G3 · `compare_peers.py:44-46` — N+1 `resolve_ticker`, và **vứt bỏ** phần đắt nhất của nó.**
Mỗi mã một truy vấn; mã tra trượt còn chạy thêm truy vấn gợi ý `extensions.similarity` (seq scan
`security` + `issuer`, 3,7 ms/lần) rồi **bỏ đi**, chỉ lấy `["tim_thay"]`. Đo:

```
compare_peers 1 ma hop le          :   7,3 ms
compare_peers 10 ma hop le         :  18,9 ms
compare_peers 10 ma khong ton tai  :  57,9 ms
compare_peers theo nganh (0 resolve):  3,5 ms
```

Chưa tới mức phải sửa gấp, nhưng nếu sửa F1 thì nhân thể: trả luôn `goi_y` của mã trượt (các
công cụ khác đều trả), và gộp 10 lần tra thành một `WHERE upper(ticker) = ANY(:mas)`.

**G4 · `tests/agent/test_a12_tools_log.py:10` — import rác vòng 1 đã chỉ mặt vẫn còn.**
`from agent.db import ops_engine`, không dùng ở đâu trong file (§4.4.3). Cùng file: bản sửa N7
đã gọi đúng `log_llm_call` dưới `SET LOCAL ROLE dlck_etl` ✅ nhưng **không assert bốn loại
token** như đề xuất — một lỗi ánh xạ cột (`ra`↔`nghi`) vẫn sẽ lọt.

**G5 · `get_financials.py:50`, `compare_peers.py:31` — bản sửa N6 chỉ áp cho một file.**
Gọi thẳng hàm với `metric_codes=[{"a":1}]` vẫn ném `TypeError: cannot use 'dict' as a dict key`;
`compare_peers(tickers=[None])` ném `AttributeError: 'NoneType' object has no attribute 'upper'`.
**Đường model đi thì pydantic chặn trước** (`tool.call` trả `ValueError: Invalid arguments for
function …`), nên không phải lỗi đang sống — ghi lại vì hai file cùng lớp nay xử lý đầu vào lệch
nhau, và test tool gọi thẳng hàm chứ không qua pydantic.

**G6 · lệch nhỏ giữa `chat.py` và `llm_log.py` về "thế nào là kết thúc bình thường".**
`chat.py:73` coi `stop_sequence` là sạch; `llm_log.py:42,48` ghi nó thành `status='failed'` kèm
`error='stop_reason=stop_sequence'`. Không ai cấu hình `stop_sequences` nên chưa nổ, nhưng hai
bảng đối chiếu nên chung một nguồn. (Đối chiếu SDK — `_STOP_REASON_STEPS` trong
`anthropic/lib/tools/_beta_runner.py:63`: `end_turn`/`stop_sequence`/`max_tokens`/
`model_context_window_exceeded`/`refusal` = `stop`; `pause_turn`/`compaction` = `resume`;
`tool_use` = `run_tools`. Danh sách của `ket_sach` **không sót giá trị kết-thúc-bình-thường
nào**: hai giá trị bỏ ra ngoài — `refusal`, `model_context_window_exceeded` — đều là kết thúc
bất thường, chỉ có `max_tokens` là quét quá tay, xem F3.)

**G7 · `chat.py:51-57` — `pause_turn`/`compaction` sinh hai lượt `assistant` liên tiếp trong lịch sử.**
SDK xếp hai giá trị này vào `resume`: nó tự `append_messages(message)` rồi gửi lại, còn `run_turn`
cũng nối message đó vào `messages` ⇒ lịch sử ra `['user','assistant','assistant']` (đo bằng
MockTransport). Đúng loại hình dạng mà C2 muốn dẹp, chỉ đổi vai. MiniMax gần như không phát hai
stop_reason này (chúng gắn với server tool), nên chỉ ghi nhận.

**G8 · `chat.py:79-81` — lượt "kết thúc sạch nhưng không có chữ nào" vẫn để lại `content: []` trong lịch sử.**
`test_ket_thuc_sach_nhung_khong_co_chu_van_khong_tra_rong` khẳng định `len(lich_su) == 2`, tức
message assistant rỗng được giữ. Hợp đồng Messages API đòi mọi message có nội dung khác rỗng
(trừ message assistant cuối cùng), nên lượt kế tiếp có thể bị từ chối — đúng kiểu nhiễm độc mà
C2 chữa. **Chưa gọi API thật để xác nhận trên MiniMax**, nên chỉ ghi nhận; nếu muốn chắc thì bỏ
hẳn message rỗng khỏi lịch sử trước khi trả về.

**G9 · `get_news.py:124-125` — câu `ghi_chu` tự mâu thuẫn khi không còn bài chưa phân loại.**

```
get_news({"group_no":1,"from_date":"2020-01-01","to_date":"2020-01-02"})
 -> "ghi_chu": "không có bài nào khớp nhãn; trong khoảng này còn 0 bài chưa phân loại
                nên chưa thể lọc theo nhãn"
```

"còn 0 bài chưa phân loại **nên** chưa thể lọc" là lời giải thích ngược. Chỉ nên gắn `ghi_chu`
khi `chua > 0`.

**G10 · `get_macro_series._danh_muc(conn, keyword, tran=…)`** — tham số `tran` chỉ có test
truyền (`test_danh_muc_dem_dung_tong_khong_phu_thuoc_tran`). Cùng loại với G3 vòng 1 (API tồn
tại để test gọi). Rất nhỏ.

---

## 4. Những chỗ đã soi và thấy sạch (ghi để vòng sau khỏi làm lại)

- **`cap_limit` đổi chữ ký (bỏ tuple) — không sót caller nào.** `grep` toàn repo: 4 nơi gọi, cả 4
  nhận một giá trị; bản cũ `lim, da_cat = cap_limit(...)` không còn dấu vết.
- **`Literal[_TOPICS]` sinh schema đúng**: `enum` đủ 9 khoá, `required: ["topic"]`; `from __future__
  import annotations` không làm hỏng vì `_TOPICS` là biến module-level.
- **`resolve_ticker` thêm vào `get_news` không đổi hành vi mã hợp lệ**: `ticker="HPG"` vẫn ra đúng
  kết quả, +1 truy vấn (5,7 ms cả lời gọi). Kho không có ticker viết thường (0 dòng
  `ticker <> upper(ticker)`) nên `:tk` không cần `upper()` thêm.
- **`v_issuer_industry` là 1-1**: 0 issuer có >1 dòng ⇒ `LEFT JOIN` trong `compare_peers`/
  `screen_stocks` không nhân dòng, `da_cat`/`LIMIT` không bị lệch vì lý do này.
- **`news.article` không có bài nào thiếu revision** (0 dòng) ⇒ `JOIN LATERAL` (inner) không làm
  `tong_khop` lệch khỏi số dòng trả về.
- **Nhánh "không phải cổ phiếu" của `get_financials` và `get_price_series` là ĐÚNG với kho**:
  0 issuer non-stock có `financial_statement`; 0 security non-stock có `price_daily`; 0 mã
  `delisted` có giá. (Chỉ `get_corporate_events` chép sai — F2.)
- **Không in giá trị biến môi trường ở đâu** trong phần thêm mới; mọi thông báo lỗi vẫn chỉ mang
  `type(e).__name__`.
- **Test mới không tautological**: expected là literal lấy từ fixture hoặc từ tính chất bất biến
  (`2026-08-20` cho bài `23:30+00`, tiêu đề revision 2), có case biên và case ngược
  (`da_cat` cả hai chiều). Fixture C1/N1 thêm vào `conftest.py` đúng chỗ và có lý do viết rõ.
- **`transaction bị abort dây chuyền` KHÔNG phải lỗi production**: mỗi tool tự mở/đóng kết nối
  trong `chay()` (`tools/__init__.py:32`), nên một câu SQL chết không kéo theo lời gọi sau. (Chỉ
  script review dùng chung một connection mới thấy hiện tượng đó.)

---

## 5. Phán quyết

**Chưa merge được** — hai mục CHẶN đều là **hồi quy do chính đợt sửa vòng 1 đẻ ra**: `compare_peers`
trả 10 mã không ai hỏi khi mọi mã đều tra trượt (**F1**), và `get_corporate_events` khẳng định với
model rằng kho không có sự kiện cho ETF trong khi kho có 21 mã, riêng FUCVREIT 14 sự kiện gồm 2
đợt cổ tức (**F2**). Cả hai đều sinh câu trả lời sai một cách thầm lặng, đúng loại lỗi mà vòng 1
gọi tên. Nên gộp cùng đợt: **F4** (LATERAL giết index GIN, 6× chậm và tệ dần theo kho), **F3**
(vứt cả câu trả lời khi `max_tokens` cắt phần văn bản), và hai mục vòng 1 chưa làm — **G1/N5**
(cắt câm 5.364 phiên của BT6) và **F7/N8a**.

C1 và N2/N3/N8b sửa chuẩn, không sót nhánh — phần đó ăn chắc.
