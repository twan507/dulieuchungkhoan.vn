# Review trục CHUẨN — vòng 3 (`backend/agent/`, lát 10)

Diff soi: `4c72c09..HEAD -- backend/` (bốn commit chạm code: `22db31e`, `5943534`, `910e0b2`,
`ec15459`, `b937ba2`) · 16 file, +253/−29. Nhánh `feat/semantic-layer`.
**Lưu ý:** HEAD đã chạy tiếp tới `8601759` trong lúc review — commit đó chỉ chạm `docs/`;
`git diff b937ba2..HEAD -- backend/` **rỗng**, nên mọi kết luận dưới đây vẫn đúng với HEAD.

Nhiệm vụ vòng này: **soi chính tám bản sửa của đợt 2 để tìm hồi quy tiếp theo**, không soi lại
code đã sạch ở hai vòng trước.

Bộ test chạy xanh trước khi soi:

```
$ set -a && . ./.env && set +a && cd backend && pytest tests/agent/ -q
........................................................................ [ 66%]
.....................................                                    [100%]
109 passed in 3.17s
```

Mọi con số dưới đây đo trên **kho dev 2026-09-07**, gọi thẳng hàm tool qua
`AGENT_DATABASE_URL` (role `agent_reader`/`dlck_api`), `EXPLAIN ANALYZE` cho phần kế hoạch truy
vấn, `httpx2.MockTransport` cho phần chat. **Không gọi model thật.**

---

## 1. Bảng tám thay đổi

| # | Thay đổi | Kết quả | Bằng chứng ngắn |
|---|---|---|---|
| 1 | `compare_peers` — chốt "mọi mã tra trượt ⇒ dừng" | 🟡 **sửa đúng phần CHẶN, sót hai chỗ** | `tickers=["ZZZZ"]` → `tim_thay:false, du_lieu:[]` (hết 10 mã lạ). Nhưng **vứt `goi_y`** mà `resolve_ticker` đã tính (`HPGG` → `goi_y:['HPG']` bị bỏ) → **F1**; và câu "không mã nào trong danh sách tồn tại" chỉ soi 10 mã đầu → **F2** |
| 2 | `get_corporate_events` — chặn theo `issuer_id is None` | ✅ **sửa đúng, mọi con số docstring đúng** | Đếm lại `market.security`: stock 439/1.965 · etf 10/31 · fund_cert 0/3 · index 18/18 — **khớp docstring từng số**. `FUCVREIT` → 14 sự kiện (trước: khẳng định "kho không có"). 439 mã `stock` thiếu `issuer_id` **đều là `delisted`** (0 mã `listed`) |
| 3 | `get_price_series` — `da_cat`/`tong_khop` + câu đếm | ✅ **sửa đúng, rẻ** | `BT6` → `so_dong:400, da_cat:true, tong_khop:5764`; `A32` → `400/1961`; `HPG` (60 phiên) → `da_cat:false`. Câu đếm là **Index Only Scan, Heap Fetches 0, 2,9 ms nguội** |
| 4 | `khoang_co_du_lieu` cho financials + events | 🟡 **sửa đúng, một chỗ nói rộng hơn dữ liệu** | Cả hai chỉ chạy ở **đường nguội** (`if not rows`), 1,2–3,8 ms. Nhưng câu khoảng của `get_financials` **bỏ qua `length_report` và `metric_code`** → khoảng báo về rộng hơn cái vừa hỏi → **F4** |
| 5 | `get_news` — `NOT EXISTS` thay `JOIN LATERAL` | ✅ **sửa đúng, sạch — mọi số trong docstring tái lập được** | 4 truy vấn trên kho thật: tập `article_id` **giống hệt**. Dữ liệu tổng hợp 0/1/2/3 revision: cả hai chọn đúng `version` lớn nhất. PK `(article_id, version)` ⇒ tương đương về cấu trúc, không chỉ về dữ liệu hiện có |
| 6 | `get_industry_tree` — chuẩn hoá hình dạng | ❌ **đẻ hồi quy nhẹ + comment nói sai** | `industry_code="KHONGCO"` → `{"tim_thay": true, "co_du_lieu": false, "so_dong": 0}` — **khẳng định mã ngành bịa là có thật**, và không có `ly_do`. Comment nói hình dạng này "đúng khuôn `khong_co_du_lieu`/`rong`" — **không khuôn nào như vậy** → **F5** |
| 7 | `screen_stocks` — chặn `bool` | ✅ **sửa đúng, không sót chỗ nào** | `value: true` → `{"loi": true}`. `grep` toàn `agent/`: đây là chỗ **duy nhất** kiểm `isinstance(..., (int, float))` |
| 8 | `chat.py` — `ket_sach` theo hình dạng + `MAX_TOKENS` 4k→32k | ❌ **sửa đúng F3 nhưng đẻ hồi quy mới** | `max_tokens` giữa văn bản nay giữ câu trả lời ✅. Nhưng `ket_sach` nay nhận **mọi** `stop_reason`: `model_context_window_exceeded` và `refusal` **được giữ vào lịch sử** (trước bị bỏ), kể cả khi `content` là `[]` → **F3**. `MAX_TOKENS=32000` vượt xa cái timeout 120 s của client → **F6** |

**Kết luận của bảng:** hai mục CHẶN vòng 2 (`compare_peers`, `get_corporate_events`) đã được
**sửa đúng và đúng phạm vi** — tôi đã cố tìm ca lọt/chặn nhầm cho cả hai và không tìm được ca
nào có thật trên kho. Chuỗi "sửa xong đẻ hồi quy nặng hơn" **đứt ở đợt này**: cái nặng nhất còn
lại (`F3`, `F5`) là loại "khẳng định sai một điều nhỏ", không phải "trả dữ liệu sai một cách tự
tin".

---

## 2. Trả lời từng câu hỏi đã đặt

### 2.1 Mục 2 — `issuer_id is None` có chặn đúng không?

**Có.** Đếm `market.security` theo `(security_type, issuer_id IS NULL)`:

```
('etf',        False, 21)   ('etf',        True, 10)
('fund_cert',  False,  3)
('index',      True,  18)
('stock',      False, 1526) ('stock',      True, 439)
```

Kho **có** mã `security_type='stock'` mà thiếu `issuer_id`: **439 mã**. Hàm xử lý ra hình dạng
#2 với `loai:"stock"`:

```
su_kien_doanh_nghiep(ABA) ->
 {"tim_thay": true, "co_du_lieu": false, "loai": "stock",
  "ly_do": "mã này không có issuer_id trong kho — …", "ma": "ABA"}
```

Không phải chặn nhầm: **cả 439 mã đều `status='delisted'`** (`listed` thiếu `issuer_id` chỉ có
18 `index` + 10 `etf`), và không mã nào trong số đó có dòng nào trong `market.corporate_event`
— vì sự kiện khoá theo `issuer_id`, không có `issuer_id` thì về mặt cấu trúc không thể có.
Chiều ngược lại cũng đúng: ETF/fund_cert **có** `issuer_id` nay trả sự kiện thật
(`FUCVREIT` → 14 sự kiện), đúng thứ vòng 2 gọi tên.

Mọi con số trong docstring mới đều tái lập được:

```
non-stock co su kien : etf 18 ma/104 su kien · fund_cert 3 ma/10 su kien   ✔ khớp docstring
FUCVREIT             : 14 su kien, 2 CashDividend                          ✔
non-stock co BCTC    : 0 (so issuer co BCTC = 1.523, đúng số 'stock listed' = 1.523)  ✔
```

⇒ Nhánh chặn của `get_financials` (vẫn giữ `loai != "stock"`) **đúng với kho**, và docstring của
nó nói rõ đây là "phạm vi thu thập thực tế của riêng bảng này", không suy rộng — đúng §3.6.

### 2.2 Mục 3 và 4 — truy vấn thêm có chạy trên đường nóng, có đắt không?

| Truy vấn thêm | Chạy khi nào | `EXPLAIN ANALYZE` |
|---|---|---|
| `get_price_series` đếm phiên | **Mọi lời gọi thành công** (đường nóng) | `Index Only Scan using price_daily_pkey`, `Heap Fetches: 0`, buffers 49, **2,9 ms nguội** (BT6, 5.764 phiên, không lọc ngày) |
| `get_financials` min/max năm | Chỉ khi 0 dòng (nguội) | Hai `InitPlan` → `Index Only Scan (Backward)` trên PK, `Heap Fetches: 0`, **1,2 ms** (FPT) / **3,8 ms** (issuer nhiều dòng nhất, 41.688 dòng) |
| `get_corporate_events` min/max ngày | Chỉ khi 0 dòng (nguội) | `Bitmap Index Scan on corporate_event_issuer_id_exright_date_idx` (177 dòng), 33,8 ms **nguội cache** / 1,8–2,0 ms ấm |

Bảng 27,3 triệu dòng là `market.financial_statement` — PK
`(issuer_id, year_report, length_report, statement_type, metric_code)` phủ đúng vị từ, nên
min/max chỉ là hai lần dò đầu/cuối index, **không** quét bảng. `market.price_daily` là 1,1 triệu
dòng và PK `(security_id, trading_date)` phủ trọn vị từ đếm.

Đo đầu-cuối cả hàm (3 lần, ms):

```
price BT6 full   : [6.3, 6.5, 7.2]      price HPG 60 phien : [3.6, 2.6, 2.8]
fin FPT rong     : [2.6, 2.1, 2.8]      fin FPT co du lieu : [7.3, 5.9, 6.0]
event FPT rong   : [2.0, 1.8, 2.0]      event FPT co       : [1.5, 1.5, 1.6]
```

**Không có vấn đề hiệu năng.** Ngân sách `statement_timeout = '20s'` mỗi lời gọi
(`tools/__init__.py:33`) còn nguyên vẹn.

### 2.3 Mục 5 — `NOT EXISTS` có cho **cùng** kết quả với `LATERAL` trong mọi ca không?

**Có**, và chứng minh được ở hai tầng.

*Tầng cấu trúc:* `news.article_revision` có `PRIMARY KEY (article_id, version)` ⇒ `version`
**duy nhất trong một bài và NOT NULL** (đo: `version is null` = 0 dòng). Với khoá duy nhất,
"không tồn tại `r2` có `version` lớn hơn" ⇔ "là `version` lớn nhất" ⇔ đúng dòng
`ORDER BY version DESC LIMIT 1` chọn. Bài không có revision nào bị loại ở **cả hai** bản (đều là
inner join).

*Tầng đo:* kho thật (mỗi bài đúng 1 revision, 8.191/8.191) — bốn truy vấn, so **tập
`article_id`**, không chỉ so số đếm:

```
'lãi suất điều hành': LATERAL=1059  NOTEXISTS=1059  giong nhau=True
'cổ tức'            : LATERAL=5687  NOTEXISTS=5687  giong nhau=True
'ngân hàng nhà nước': LATERAL=1835  NOTEXISTS=1835  giong nhau=True
'xuất khẩu'         : LATERAL=1674  NOTEXISTS=1674  giong nhau=True
```

Kho thật **không có bài 2 bản** nên ca đó phải dựng bằng dữ liệu tổng hợp (CTE chỉ đọc) — bài 1
không revision, bài 2 một bản, bài 3 hai bản, bài 4 ba bản:

```
('LATERAL', 2, 1, 'B v1')   ('NOTEXISTS', 2, 1, 'B v1')
('LATERAL', 3, 2, 'C v2')   ('NOTEXISTS', 3, 2, 'C v2')
('LATERAL', 4, 3, 'D v3')   ('NOTEXISTS', 4, 3, 'D v3')
                              (bài 1 — không revision — vắng ở cả hai bản)
```

*Hiệu năng*, câu đếm `phraseto_tsquery('lãi suất điều hành')`, 3 lần sau khi làm ấm:

```
LATERAL (bản cũ) : n=31  [25.2, 25.4, 26.0] ms   cost=68.628  buffers=51.584
JOIN+NOT EXISTS  : n=31  [20.6, 23.7, 22.1] ms   cost= 2.070  buffers=29.060
```

Và `SET LOCAL enable_seqscan = off`:

```
LATERAL   -> vẫn Nested Loop, 8.195 loops, 32,8 ms   (không có đường tới GIN)
NOTEXISTS -> Bitmap Index Scan on article_revision_tsv_idx, 7,9 ms
```

Số của tôi lệch docstring vài phần trăm (cost 2.070 vs 2.062, buffers 29.060 vs 28.994, 7,9 ms
vs "~6 ms") — trong sai số cache/`ANALYZE`. **Docstring không nói quá điều gì**: nó tự khai rằng
planner mặc định vẫn chọn Seq Scan và lợi ích GIN là "khi kho lớn lên". Đây là bản sửa sạch nhất
của đợt.

### 2.4 Mục 8 — `stop_reason` nào mà chấp nhận là sai?

Danh sách thật, đọc từ `anthropic/types/beta/beta_stop_reason.py` (SDK 1.4.0):
`end_turn · max_tokens · stop_sequence · tool_use · pause_turn · compaction · refusal ·
model_context_window_exceeded`. Bảng phân loại của runner
(`lib/tools/_beta_runner.py:63` `_STOP_REASON_STEPS`): `tool_use`→`run_tools`;
`pause_turn`,`compaction`→`resume`; năm giá trị còn lại →`stop`.

`ket_sach` **không còn nhìn `stop_reason`**, nên nó nhận cả năm giá trị `stop` + hai giá trị
`resume` + giá trị `None`/lạ. Đo bằng `MockTransport`:

| `stop_reason` | `content` | Trước đợt 2 | Sau đợt 2 |
|---|---|---|---|
| `refusal` | có chữ | bỏ lượt | **giữ** — trả nguyên câu từ chối |
| `refusal` | `[]` | bỏ lượt | **giữ**, lịch sử có `assistant: []` |
| `model_context_window_exceeded` | `[]` | bỏ lượt | **giữ**, lịch sử có `assistant: []` |
| `max_tokens` | chỉ `thinking` | bỏ lượt | **giữ**, lịch sử có `assistant: ['thinking']` |
| `end_turn` | `[]` | giữ (G8 cũ) | giữ |
| `None` | có chữ | bỏ lượt | giữ |

Hai giá trị **chấp nhận là sai**: `model_context_window_exceeded` (xem **F3**) và, nhẹ hơn,
`refusal`. Ba ca cuối bảng để lại message `content: []` hoặc `content: ['thinking']` trong lịch
sử — đúng loại nhiễm độc mà chính C2 sinh ra để chữa. Đề xuất của vòng 2 có ghi *"cắt giữa
`thinking` không lọt lưới này vì `tra_loi` rỗng"* — **bản cài đặt không làm vậy**: nhánh
`if not tra_loi.strip()` chỉ đổi văn bản trả về rồi `return tra_loi, messages`, tức vẫn nhận
lịch sử.

**`MAX_TOKENS=32000` có hệ quả** — xem **F6** (trần thật là timeout 120 s, không phải 32.000
token) và **F7** (`ops.llm_call` ghi lượt trả lời được thành `failed`).

### 2.5 Có docstring nào khẳng định điều chưa đo không?

Tôi kiểm từng lời khẳng định mới thêm trong tám thay đổi:

| Chỗ | Lời khẳng định | Phán quyết |
|---|---|---|
| `get_corporate_events.py:7-14` | 4 con số `security`, `etf 18/104`, `fund_cert 3/10`, `FUCVREIT 14 gồm 2 CashDividend` | ✅ **đúng từng số**, đã đếm lại |
| `get_financials.py:24-29` | "0 issuer non-stock có BCTC", "1.523 issuer" | ✅ đúng |
| `get_news.py:53-66` | cost/buffers/ms hai bản, `enable_seqscan=off` không cứu được LATERAL | ✅ tái lập được, lệch vài phần trăm |
| `get_price_series.py:8-13` | BT6 5.764 phiên, 356 mã >400 phiên | ✅ đúng (đếm lại: 356) |
| `get_industry_tree.py:53-54` | "co_du_lieu=False đúng khuôn `khong_co_du_lieu`/`rong` ở `_shared.py`" | ❌ **SAI** — xem **F5** |
| `chat.py:37-43` | "đặt rộng gần như không tốn gì" | ⚠️ **chưa đo hết** — xem **F6** |

*(Ngoài phạm vi đợt 2 nhưng ghi cho đủ: `get_price_series.py:5` còn ghi "0/442 mã `delisted`";
hôm nay đếm được **445** mã `delisted`, trong đó vẫn **0** mã có giá. Con số 442 là của lần đo
trước, kho đã lớn thêm — phần kết luận không đổi.)*

---

## 3. Phát hiện

### 🟠 F1 · NÊN SỬA · `agent/tools/compare_peers.py:51-53` — nhánh mới **vứt `goi_y`** mà chính nó vừa tính, để model không còn đường tự sửa

**Vấn đề.** Bản sửa dừng đúng chỗ, nhưng trả về một payload **không có `goi_y`**. Trong khi đó
`resolve_ticker` ở dòng 45 **đã chạy truy vấn `extensions.similarity`** và đã có sẵn gợi ý — code
chỉ lấy `["tim_thay"]` rồi bỏ phần còn lại. Nhánh này giờ là **câu trả lời cuối cùng** cho ca gõ
nhầm một mã, tức là ca thường gặp nhất.

**Bằng chứng chạy thật (kho dev, `dlck_api`).**

```
so_sanh_cung_nganh(tickers=["HPGG"], metric_codes=["rtd21"])
 -> {"tim_thay": false, "khong_tim_thay": ["HPGG"], "so_dong": 0, "du_lieu": [],
     "ly_do": "không mã nào trong danh sách tồn tại trong danh bạ"}

resolve_ticker(conn, "HPGG")
 -> {"tim_thay": False, "ma_da_tra": "HPGG", "goi_y": ["HPG"]}      <-- đã có, bị bỏ đi
```

Cùng một lỗi gõ, `get_price_series("HPGG")` / `get_news(ticker="HPGG")` **đều** trả `goi_y`; chỉ
`compare_peers` là ngõ cụt. Payload cũng lệch hình dạng #1 của spec §4.6
(`{tim_thay, ma_da_tra, goi_y}`): thiếu `ma_da_tra`, thiếu `goi_y`, thừa `so_dong`/`du_lieu`.

**Đề xuất.** Giữ nguyên kết quả `resolve_ticker` thay vì chỉ đọc một khoá, rồi gộp gợi ý vào:

```python
tra = {t: resolve_ticker(conn, t) for t in mas}
ma_hop_le   = [t for t, r in tra.items() if r["tim_thay"]]
khong_ton_tai = [t for t, r in tra.items() if not r["tim_thay"]]
if mas and not ma_hop_le:
    return to_json({"tim_thay": False, "khong_tim_thay": khong_ton_tai, "so_dong": 0,
                    "du_lieu": [], "goi_y": sorted({g for t in khong_ton_tai for g in tra[t]["goi_y"]}),
                    "ly_do": "…"})
```

*(Nhân thể trả `goi_y` cho cả nhánh có mã hợp lệ — G3 vòng 2 đã nêu.)*

---

### 🟠 F2 · NÊN SỬA · `agent/tools/compare_peers.py:37, 51-53` — câu "không mã nào trong danh sách tồn tại" chỉ soi **10 mã đầu**

**Vấn đề.** `mas = mas_xin[:TRAN_MA]` (dòng 37) cắt danh sách xuống 10 **trước** vòng
`resolve_ticker`. Chốt mới xét `if mas and not ma_hop_le` — tức xét trên **bản đã cắt**. Nếu 10
mã đầu đều bịa còn mã thứ 11–12 có thật, hàm khẳng định một điều **sai sự thật** và không hề nói
là mình đã cắt (nhánh này không có `da_cat`).

**Bằng chứng chạy thật.**

```
so_sanh_cung_nganh(tickers=["ZZ00".."ZZ09","HPG","VCB"], metric_codes=["rtd21"])
 -> {"tim_thay": false,
     "khong_tim_thay": ["ZZ00","ZZ01","ZZ02","ZZ03","ZZ04","ZZ05","ZZ06","ZZ07","ZZ08","ZZ09"],
     "so_dong": 0, "du_lieu": [],
     "ly_do": "không mã nào trong danh sách tồn tại trong danh bạ"}
```

HPG và VCB **có thật**, không bao giờ được tra, và không trường nào nói chúng đã bị bỏ. Model
đọc câu này rất dễ nói lại với người dùng "HPG không có trong danh bạ".

Xác suất thấp (đòi >10 mã và 10 mã đầu đều sai), nhưng đây là **khẳng định phủ định về cả danh
sách suy từ một phần** — đúng khuôn §3.6, và là loại lỗi mà hai vòng trước đã trả giá.

**Đề xuất.** Hoặc xét chốt trên `mas_xin` (`if mas_xin and not ma_hop_le`), hoặc thêm
`da_cat`/`khong_kiem` vào payload để nói rõ phần đuôi chưa được xét. Kèm test 11+ mã.

---

### 🟠 F3 · NÊN SỬA · `agent/chat.py:81` — `ket_sach` bỏ hẳn `stop_reason` nên **giữ lại cả lượt `model_context_window_exceeded`**, biến một trạng thái hồi phục được thành phiên chết cứng

**Vấn đề.** Điều kiện mới chỉ hỏi "lượt cuối còn `tool_use` treo không?". Đúng cho ca F3 của
vòng 2, nhưng nó cũng **nhận** hai `stop_reason` mang nghĩa *lượt hỏng*:

- `model_context_window_exceeded` — lịch sử vừa làm tràn cửa sổ ngữ cảnh nay **được nối thêm vào
  chính lịch sử đó**. Lượt sau dài hơn ⇒ tràn tiếp ⇒ vòng lặp không lối ra. Trước đợt 2, bỏ lượt
  trả `history` cũ, người dùng hỏi câu ngắn hơn là chạy tiếp được.
- `refusal` — giữ lượt từ chối vào lịch sử. *(MiniMax có phát `refusal` hay không: **chưa đo**.)*

Cộng thêm: cả hai ca này (và `max_tokens` cắt giữa `thinking`) thường **không có block `text`
nào**, nên lịch sử nhận về một message `content: []` hoặc chỉ có `thinking` — đúng loại message
mà C2 sinh ra để dọn.

**Bằng chứng (MockTransport, không gọi model thật).**

```
== model_context_window_exceeded, co lich su cu ==
  tra_loi: [model kết thúc bằng 'model_context_window_exceeded' nhưng không sinh câu trả lời nào.]
  so message trong lich su: 4
    - user: hoi truoc | - assistant: ['text'] | - user: Cau hoi? | - assistant: []
                                                                    ^^ luot hong duoc GIU

== refusal, KHONG co block nao ==   -> lich su: user + assistant: []
== max_tokens giua thinking       ->  lich su: user + assistant: ['thinking']
```

**Đối chiếu bản trước đợt 2** — chạy **chính** `chat.py` của `4c72c09` (lấy ra bằng `git show`,
nạp làm module riêng, cùng `MockTransport`, cùng bốn ca):

```
BAN CU · refusal, content rong        : so message = 0  -> '[lượt này dừng giữa chừng (refusal) …'
BAN CU · model_context_window_exceeded: so message = 0  -> '[lượt này dừng giữa chừng (model_context_window_exceeded) …'
BAN CU · max_tokens giua thinking     : so message = 0
BAN CU · max_tokens chi co chu        : so message = 0   <-- ca F3 vòng 2, đúng cái đợt 2 chữa
```

Tức ba ca đầu **là hồi quy do bản sửa đợt 2 mở ra**, không phải hành vi có sẵn.

Ghi chú ở `chat.py:71-76` vẫn liệt kê đúng hai đường thoát dở dang cần chặn, nhưng điều kiện bên
dưới nay rộng hơn ghi chú.

**Đề xuất.** Giữ ý "hình dạng lịch sử" nhưng loại riêng những `stop_reason` mang nghĩa hỏng, và
đừng nhận message rỗng:

```python
HONG = ("model_context_window_exceeded", "refusal")
co_tool_treo = cuoi is not None and any(b.type == "tool_use" for b in cuoi.content)
ket_sach = (cuoi is not None and not co_tool_treo
            and cuoi.stop_reason not in HONG and len(cuoi.content) > 0)
```

Kèm test cho `model_context_window_exceeded` (hiện `grep` toàn `tests/agent/` **không có test
nào** nhắc tới `refusal`, `model_context_window_exceeded`, `pause_turn`, `compaction`).

---

### 🟠 F4 · NÊN SỬA · `agent/tools/get_financials.py:71-75` — `khoang_co_du_lieu` **rộng hơn** câu vừa hỏi

**Vấn đề.** Câu chính (`_SQL_BCTC`) lọc bốn thứ: `statement_type`, `length_report`
(`period` → `[5]` hoặc `[1,2,3,4]`), `metric_code`, và khoảng năm. Câu khoảng mới chỉ lọc
**`issuer_id` + `statement_type`**. Nên khi 0 dòng vì `period` hoặc `metric_codes` — chứ không
phải vì năm — hàm vẫn báo về một khoảng năm, và model đọc thành "kho có kỳ này, mình hỏi sai
năm".

**Bằng chứng.** `market.financial_statement` có đủ `length_report` 1..5
(`1:5.108.467 · 2:5.086.114 · 3:4.784.207 · 4:4.783.151 · 5:7.520.023`), nên trên kho dev chưa
bắt được ca nổ; nhưng khoảng trả về **không đổi theo `period`**, chứng minh trực tiếp:

```
bao_cao_tai_chinh(FPT, "IS", 1990, 1995, period="nam")  -> khoang_co_du_lieu {tu_nam:2002, den_nam:2026}
(cùng câu khoảng đó dùng lại nguyên vẹn cho period="quy" — nó không có :lens trong WHERE)
```

Một issuer chỉ có báo cáo năm (không có quý) sẽ trả `khoang_co_du_lieu {2002..2026}` cho câu hỏi
**quý** — chính là "khẳng định điều chưa kiểm" ở mức payload.

Phụ, cùng chỗ: `get_financials` dùng khoá `{"tu_nam","den_nam"}` còn `get_price_series` và
`get_corporate_events` dùng `{"tu","den"}` (spec §4.6 viết `{"tu","den"}`). Ba công cụ, hai tên
khoá — đúng thứ `_shared.py:3-5` muốn dẹp.

**Đề xuất.** Thêm `AND length_report = ANY(:lens)` (và cân nhắc `metric_code = ANY(:codes)`) vào
câu khoảng, để nó nói về **chính lát dữ liệu vừa hỏi**. Đổi khoá về `{"tu","den"}` cho khớp hai
công cụ kia hoặc ghi rõ trong docstring vì sao khác.

---

### 🟠 F5 · NÊN SỬA · `agent/tools/get_industry_tree.py:51-56` — hình dạng mới **khẳng định mã ngành bịa là có thật**, và comment mô tả sai chính nó

**Vấn đề.** Bản sửa thêm `tim_thay: True` **cứng**. Với `industry_code` không tồn tại, truy vấn
ra 0 dòng và hàm trả về:

```
cay_nganh(industry_code="KHONGCO")
 -> {"tim_thay": true, "co_du_lieu": false, "so_dong": 0, "nhom": []}
```

`tim_thay: true` trong bảng bốn hình dạng nghĩa là **"mã có tồn tại"**. Ở đây nó không tồn tại.
Model nhận về "mã ngành này có thật, chỉ là kho chưa có ngành con nào" — sai, và không có `ly_do`
để cứu. Trước bản sửa, payload là `{"nhom": []}` — vô nghĩa nhưng **không khẳng định gì**; nay nó
khẳng định một điều sai. Đây là hồi quy nhỏ do chính bản sửa tạo ra.

Comment dòng 53-54 viết *"co_du_lieu=False đúng khuôn `khong_co_du_lieu`/`rong` ở `_shared.py`"*
— **không khuôn nào như vậy**: `khong_co_du_lieu()` luôn kèm `loai` **và** `ly_do`; `rong()` luôn
có `co_du_lieu=True`. Hình dạng đang trả là hình dạng thứ năm, không có trong spec §4.6.

Thêm hai chuyện nhỏ cùng chỗ:

- `so_dong` đếm **số ngành cấp 2**, không phải độ dài `nhom`: `cay_nganh()` không tham số →
  `{"so_dong": 24, "nhom": <6 phần tử>}`. Prompt hệ thống và L1 **không** giải thích nghĩa các
  khoá này cho model (`grep tim_thay|co_du_lieu|so_dong` trong `agent/system_prompt.py`,
  `agent/skills/` → 0 hit), nên model chỉ có tên trường để suy — "so_dong 24 / nhom 6" mời đọc
  nhầm thành "24 nhóm ngành".
- Test mới `test_industry_code_khong_ton_tai_van_dong_bo_hinh_dang`
  (`tests/agent/test_a06_industry.py`) **assert `tim_thay is True`** cho mã ngành bịa — tức là
  nó **khoá chết** hình dạng sai này thành hợp đồng. Ai sửa đúng sau này sẽ thấy test đỏ và
  tưởng mình sai.

**Đề xuất.** Với `industry_code` không khớp mã nhóm/mã ngành nào, trả hình dạng #1 hoặc #2 có lý
do — ví dụ
`{"tim_thay": False, "ma_da_tra": industry_code, "goi_y": [...mã ngành gần đúng...]}` — và sửa
test theo. Với nhánh trả cây thật thì `tim_thay: True` là đúng; chỉ cần tách hai nhánh.

---

### 🟠 F6 · NÊN SỬA · `agent/chat.py:37-43` + `core/llm/client.py:57-59` — `MAX_TOKENS=32000` vượt xa trần thật (timeout 120 s), và trần đó **hỏng đắt hơn** trần cũ

**Vấn đề.** Chính SDK có một chốt cho chuyện này: yêu cầu **không streaming** với
`max_tokens` lớn bị **từ chối thẳng**. Ngưỡng tính được từ
`_base_client.py:761` (`expected_time = 3600 * max_tokens / 128_000`, trần 600 s):

```
max_tokens=  4000 -> SDK cho phep (uoc 112s)
max_tokens=  8000 -> SDK cho phep (uoc 225s)
max_tokens= 21333 -> SDK cho phep (uoc 600s)      <-- nguong
max_tokens= 21334 -> SDK TU CHOI: "Streaming is required for operations that may take longer than 10 minutes"
max_tokens= 32000 -> SDK TU CHOI                  (uoc 900s > 600s)
```

Chốt này **không nổ** chỉ vì `LLMClient` truyền `timeout=settings.timeout_s` tường minh, nên
`self._client.timeout == DEFAULT_TIMEOUT` là `False` và cả nhánh kiểm bị bỏ qua (đo:
`client.timeout = 120.0`). Tức là trần thật của dự án **không phải 32.000 token mà là 120 giây**.

Ước lượng trần thật từ chính bốn lượt đo trong ledger (`token ra / ms`, đã gồm cả thời gian nạp
prompt nên là **cận dưới**): 84 – 152 token/s ⇒ trong 120 s sinh được **~10.000 – 18.000 token**.
Trên mức đó, request không bị cắt gọn như trước mà **đọc quá hạn** → SDK thử lại
(`max_retries = 3`, đo trực tiếp trên client) → **4 lần gửi lại toàn bộ ngữ cảnh** (ledger:
21.884 – 37.360 token vào mỗi request) và tới ~8 phút chờ, rồi `repl` mới bỏ lượt.

⇒ Câu trong comment *"đặt rộng gần như không tốn gì"* **đúng cho vùng 0–~10k và sai cho vùng
~10k–32k**: ở vùng đó nó đổi "câu trả lời bị cắt, mất 1 request" lấy "timeout, mất 4 request".
Đó là một khẳng định chưa đo hết trong docstring (§1.2).

Phụ, cùng hướng: không có deadline cho cả lượt. `MAX_ITERATIONS = 8` × 120 s ⇒ một lượt hỏi có
thể treo tới **16 phút** trước khi báo lỗi; và trần token trên mỗi vòng là 32.000 nên trần lý
thuyết một lượt là 8 × 32.000 = 256.000 token ra (Token Plan trả tiền theo token thực dùng nên
đây là rủi ro đuôi, không phải chi phí thường trực).

**Đề xuất — chọn một, đừng để hai con số đá nhau:**

1. Nâng `LLM_TIMEOUT_S` lên ~600 s cho tiến trình chat (giữ 120 s cho job lô), hoặc
2. Hạ `MAX_TOKENS` về ~12.000 (vẫn gấp 3 lần đỉnh quan sát 3.589, và nằm trong 120 s), hoặc
3. Dùng `stream=True` cho vòng chat — cách SDK khuyên và là cách duy nhất đúng nếu thật sự muốn
   32.000.

Dù chọn cách nào, sửa comment `chat.py:37-43` cho khớp: nói rõ trần thật là timeout, kèm ngày đo.

---

### 🟡 F7 · GHI NHẬN · `agent/llm_log.py:42,48` vs `agent/chat.py:81` — lượt **trả lời được** nay bị ghi sổ là `failed`

`llm_log` ghi `status = "ok" if stop in ("end_turn","tool_use") else "failed"`. Sau đợt 2,
`chat.py` **nhận và trả về** các lượt `max_tokens`, `stop_sequence`, `refusal`,
`model_context_window_exceeded`, `pause_turn`, `compaction` — tất cả đều vào sổ là
`failed` kèm `error='stop_reason=…'`. Vòng 2 đã nêu chuyện này (G6) khi mới lệch ở `stop_sequence`
(giá trị MiniMax bỏ qua, không bao giờ xảy ra); bản sửa vòng 2 làm nó lệch ở **ca thật sự xảy
ra**: `max_tokens` là ca mà `chat.py` cố ý giữ câu trả lời.

Hệ quả: mọi thống kê sau này lấy từ `ops.llm_call` (đúng cái bảng ledger đang dùng làm bằng
chứng) sẽ **đếm thừa số lượt hỏng**. Nên cho hai chỗ dùng chung một danh sách.

### 🟡 F8 · GHI NHẬN · `agent/tools/get_corporate_events.py:25-26` — `ly_do` lộ khái niệm lược đồ (`issuer_id`) vào ngữ cảnh model

```
su_kien_doanh_nghiep("VFMVF1")   # etf listed, không có issuer_id
 -> "ly_do": "mã này không có issuer_id trong kho — sự kiện doanh nghiệp gắn theo issuer,
              không suy được nếu thiếu liên kết"
```

Cùng tinh thần với luật "không lộ mã chỉ tiêu thô" trong `REMINDER`: `issuer_id` là chi tiết nội
bộ, còn `REMINDER` bảo model *"dùng đúng số này"* nên chuỗi này rất dễ được chép nguyên vào câu
trả lời cho người dùng. Câu thân thiện hơn mà vẫn đúng: *"kho chưa liên kết mã này với tổ chức
phát hành nên chưa tra được sự kiện doanh nghiệp"*.

### 🟡 F9 · GHI NHẬN · `agent/tools/get_corporate_events.py:55-62` — issuer **chưa từng có sự kiện nào** ra hình dạng #3 câm

```
su_kien_doanh_nghiep("FUEMITEC")   # etf CÓ issuer_id, kho có 0 sự kiện
 -> {"tim_thay": true, "co_du_lieu": true, "so_dong": 0, "ma": "FUEMITEC"}
```

Không `khoang_co_du_lieu`, không `ly_do`. Quy ước "vắng `khoang_co_du_lieu` ⇒ kho không có gì
hết" **không được ghi ở đâu cho model đọc** (prompt hệ thống và L1 không mô tả bốn hình dạng).
Vẫn tốt hơn hẳn bản trước (khẳng định sai), nên chỉ ghi nhận: nên kèm một `ly_do` ngắn khi khoảng
là `None`.

### 🟡 F10 · GHI NHẬN · `agent/tools/get_price_series.py:47-64` — đường rỗng chạy 3 truy vấn thay vì 2

Khi khoảng hỏi rỗng: câu đếm (trả 0, rồi bị vứt) → câu lấy dòng (0 dòng) → `_SQL_KHOANG`. Giá trị
`tong = 0` đã đủ để biết không cần đếm nữa. Rẻ (2,6 ms tổng) nên chỉ ghi nhận; gộp được thì gọn
hơn.

Cùng chỗ: `ghi_chu` nay nối hai chuyện không liên quan vào một chuỗi
(`"kho chưa có khối lượng giao dịch theo ngày; đã cắt còn 400/5764 phiên GẦN NHẤT…"`). Hai trường
riêng dễ đọc hơn cho model, nhưng đây là chuyện thẩm mỹ.

### 🟡 F11 · GHI NHẬN · ledger ghi sai điểm xuất phát của trần token

`docs/90-records/plans/2026-09-07-semantic-layer/ledger.md:172` đặt tiêu đề
**"Nới trần token: 4.000 → 32.000"**. Diff thật của `ec15459` là **8.000 → 32.000**
(`git show 4c72c09:backend/agent/chat.py` → `MAX_TOKENS = 8000`); mốc 4.000 → 8.000 đã xảy ra
trước đó ở `d23913c` và **chính ledger dòng 70 ghi đúng chuyện đó**. Hai dòng trong cùng một file
nói hai điểm xuất phát khác nhau — đúng loại "tài liệu tự đá nhau" ở §1.7. Sửa tiêu đề thành
"8.000 → 32.000" là đủ.

### 🟡 F12 · GHI NHẬN · test mới — hai chốt canh yếu hơn ca chúng bảo vệ

- `test_hoi_toan_ma_khong_ton_tai_thi_khong_tra_ma_bat_ky` (`test_a09_screener.py`) assert
  `du_lieu == []`, `so_dong == 0`, `khong_tim_thay == ["ABCDE"]` — **không** assert
  `tim_thay is False`. Nếu ai đó đưa nhánh về `rong()` (`tim_thay:true, co_du_lieu:true`) thì test
  vẫn xanh dù hình dạng lại sai.
- `test_hoi_nganh_khong_kem_ma_van_loc_theo_nganh` assert `so_dong > 0` và một quan hệ **tập
  con** — xanh cả khi chỉ còn 1 mã. §4.5.4 đòi "assert giá trị cụ thể".

Hai test khác thì tốt: `test_vuot_tran_phien_bao_da_cat_va_giu_phien_gan_nhat` assert đúng danh
sách ngày và cả chiều ngược (`test_khong_du_400_phien_thi_khong_bao_da_cat`);
`test_etf_co_issuer_van_tra_su_kien_that_khong_phai_hinh_dang_2` assert ngày GDKHQ cụ thể. Fixture
`QUYTN` thêm vào `conftest.py` có ghi rõ lý do và không làm lệch test nào khác (109 xanh).

---

## 4. Đã soi và thấy sạch (ghi để vòng sau khỏi làm lại)

- **`get_news` `NOT EXISTS` tương đương `LATERAL` trong mọi ca**, chứng minh cả bằng ràng buộc
  (`PRIMARY KEY (article_id, version)`, `version` NOT NULL) lẫn bằng đo (4 truy vấn kho thật so
  tập `article_id`, + dữ liệu tổng hợp 0/1/2/3 revision). Docstring hiệu năng tái lập được.
- **Ba truy vấn thêm của mục 3–4 đều dùng index, không quét bảng** — `Heap Fetches: 0` ở cả
  `price_daily_pkey` và `financial_statement_pkey`. Không có chuyện "27 triệu dòng nên chậm".
- **`get_financials` vẫn chặn theo `loai != "stock"` là ĐÚNG với kho** (0 issuer non-stock có
  BCTC), và docstring của nó tự cấm suy rộng lý luận đó sang bảng khác — đúng §3.6.
- **`screen_stocks` là chỗ duy nhất kiểm `isinstance(..., (int,float))`** trong `agent/`; không
  còn lỗ `bool` nào khác.
- **Chốt `max_iterations` không bị bản sửa `ket_sach` làm hỏng**: lượt cuối khi chạm trần là
  message mang `tool_use`, vẫn rơi vào nhánh bỏ lượt
  (`test_cham_tran_vong_lap_thi_giu_nguyen_lich_su_cu` và
  `test_het_max_tokens_giua_luot_cong_cu_thi_bo_luot` vẫn xanh).
- **Import rác `from agent.db import ops_engine` (G4 vòng 2) đã dọn** khỏi
  `tests/agent/test_a12_tools_log.py`.
- **Không có import/biến mồ côi mới** trong 8 file đã sửa; mọi tên nhập vào đều còn dùng
  (`khong_co_du_lieu`, `rong`, `cap_limit`, `co_du_lieu` ở `get_corporate_events`;
  `resolve_ticker`, `to_json` ở `get_industry_tree`).
- **Không in giá trị biến môi trường** ở bất kỳ chỗ nào trong phần thêm mới; thông báo lỗi vẫn
  chỉ mang `type(e).__name__`.
- **MiniMax nhận `max_tokens=32000`** — ledger có 4 dòng `ops.llm_call` thật của lượt kiểm, nên
  đây **không** phải rủi ro "API từ chối"; rủi ro nằm ở timeout, xem F6.

---

## 5. Phán quyết

**Merge được, sau khi xử F3 và F5** (hoặc merge kèm hai mục đó thành việc tiếp theo có tên —
không mục nào tạo ra câu trả lời sai về **số liệu**).

Điều đáng nói nhất của vòng này là chuyện **không** xảy ra: hai mục CHẶN của vòng 2 được sửa
**đúng phạm vi**, và tôi đã đi tìm ca lọt/chặn nhầm cho cả hai bằng cách đếm lại kho chứ không
đọc code — không có. `compare_peers` không còn mở toang thị trường; `get_corporate_events` trả
đúng 14 sự kiện của `FUCVREIT` và chặn đúng 439 mã `stock` thiếu `issuer_id` (đều `delisted`,
không mã `listed` nào bị chặn oan). Bản sửa `get_news` là bản sạch nhất đợt — tương đương chứng
minh được, nhanh hơn, docstring tái lập được từng số. Chuỗi "sửa xong đẻ hồi quy nặng hơn" đứt ở
đây.

Còn lại, xếp theo mức:

- **NÊN SỬA trước khi merge:** **F3** (`ket_sach` giữ lượt `model_context_window_exceeded` ⇒
  phiên chết cứng, và giữ message `content: []` — đúng loại nhiễm độc C2 sinh ra để chữa) và
  **F5** (`get_industry_tree` khẳng định mã ngành bịa là có thật, comment mô tả sai chính nó, và
  **test mới khoá chết hình dạng sai**). F5 rẻ, F3 là ba dòng.
- **Nên gộp cùng đợt vì cùng file / rất rẻ:** **F1** (trả lại `goi_y` đã tính sẵn), **F2**
  (chốt xét trên danh sách đã cắt), **F4** (câu khoảng bỏ quên `length_report`), **F6** (chọn một
  con số giữa `MAX_TOKENS=32000` và `timeout=120s`, rồi sửa comment cho khớp).
- **Để sau:** F7–F12.

Không có mục CHẶN. Cảnh báo còn lại cho người merge: **F5 kèm một test khoá chết hành vi sai** —
nếu để nguyên, ba tháng nữa sẽ có người sửa đúng, thấy test đỏ, rồi tưởng mình sai.
