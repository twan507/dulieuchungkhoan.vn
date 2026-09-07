# Review trục CHUẨN — `backend/agent/` (lát 10, tầng ngữ nghĩa)

Diff soi: `56743b0..4ff1e62 -- backend/` · 35 file, ~2.270 dòng thêm.
Người review: agent độc lập, chỉ soi **đúng repo + lỗi kỹ thuật/code smell**. Không đánh giá đủ/thiếu so với spec.

Bộ test của lát chạy xanh trước khi soi:

```
$ set -a && . ./.env && set +a && cd backend && pytest tests/agent/ -q
........................................................................ [ 94%]
....                                                                     [100%]
76 passed in 2.21s
```

---

## CHẶN

### C1 · `backend/agent/tools/get_news.py:28-29, 90-91, 100-101` — so `timestamptz` với `date` dưới TZ phiên UTC ⇒ lệch ngày, đúng bẫy CLAUDE.md §3.1

**Vấn đề.** `news.article.published_at` là `timestamptz`; phiên Postgres của dự án chạy `Etc/UTC`. Mọi so sánh trong file đều để Postgres tự ép `date → timestamptz` theo TZ phiên, tức **theo ngày UTC, không theo ngày Việt Nam**. Cùng lỗi ở đường hiển thị: `str(r.published_at.date())` và `format_date_vi(r.published_at)` lấy `.date()` của datetime UTC.

**Bằng chứng (đo trên kho dev 2026-09-07).**

```
SHOW timezone                     ->  Etc/UTC
lech ngay UTC vs VN: 404 / 8147   (5% số bài bị sai ngày khi hiển thị)

vi du:
 published_at(UTC)= 2026-09-06 23:28:08+00  | ngay VN thuc te= 2026-09-07 | Chạy đua tìm vốn!
 published_at(UTC)= 2026-09-06 23:02:00+00  | ngay VN thuc te= 2026-09-07 | 07/09: Đọc gì trước giờ giao dịch chứng khoán?
```

Gọi thẳng hàm cho đúng bài đầu tiên:

```
TOOL tra: 2026-09-06  06/09/2026  | Chạy đua tìm vốn!
```

Bài thứ hai tự mang ngày trong tiêu đề — "**07/09**: Đọc gì trước giờ giao dịch" — mà công cụ sẽ khai với model là 06/09.

Bộ lọc khoảng ngày cũng trượt 7 giờ:

```
ngay VN 2026-09-06:  kho co 228 bai | bo loc cua tool tra 221 | bo sot 18 bai
```

(18 bài của ngày VN 06/09 bị loại, đồng thời các bài 07/09 trước 07:00 VN bị nhét vào.)

**Khuôn mẫu repo đã có, file này đi lệch.** `backend/etl/fundamentals_store.py:121` và `backend/etl/snapshot_store.py:125` đều viết `(c.checked_at AT TIME ZONE 'Asia/Ho_Chi_Minh')::date`. 12 file khác trong `etl/`, `ingester/`, `core/` khai `VN = ZoneInfo("Asia/Ho_Chi_Minh")`. Chỉ `agent/tools/get_news.py` bỏ qua.

**Đề xuất sửa.**

```sql
-- lọc
"((a.published_at AT TIME ZONE 'Asia/Ho_Chi_Minh')::date >= CAST(:tu AS date))"
"((a.published_at AT TIME ZONE 'Asia/Ho_Chi_Minh')::date <= CAST(:den AS date))"
-- chọn (dùng luôn cho hiển thị, khỏi convert ở Python)
SELECT (a.published_at AT TIME ZONE 'Asia/Ho_Chi_Minh')::date AS ngay_vn, ...
```

Kèm một test seam chèn bài lúc `23:30+00` và khẳng định công cụ trả ngày VN hôm sau — fixture hiện tại đặt mọi bài lúc `08:00+07` nên không thể bắt được lỗi này.

---

### C2 · `backend/agent/chat.py:42-69, 84-88` — hai đường thoát để lại `history` hỏng, khoá chết cả phiên chat

**Vấn đề.** `run_turn` luôn trả `messages` làm lịch sử mới, kể cả khi vòng lặp kết thúc ở trạng thái dở dang. Có hai đường:

**(a) Chạm `MAX_ITERATIONS`** — `_should_stop()` của SDK kiểm ở **đầu** vòng (`_beta_runner.py:194`), nên runner dừng ngay sau một lượt `tool_use`, không có lượt assistant cuối. Nhánh `else` (chỗ duy nhất đặt `tra_loi`, và cũng là chỗ duy nhất có lưới "không bao giờ trả rỗng im lặng" ở dòng 66) **không bao giờ chạy**.

**(b) `stop_reason == "max_tokens"` rơi đúng giữa một block `tool_use`** — SDK xếp `max_tokens` vào `stop` (`_STOP_REASON_STEPS`), thoát vòng mà không sinh `tool_result`. Đây không phải giả định: chú thích ngay tại `chat.py:37` ghi *"4000 CẮT THẬT 3/40 request (đo 2026-09-07)"* — tỷ lệ cắt đã đo là 7,5% ở mức cũ.

**Bằng chứng (chạy thật, model giả bằng `MockTransport`, script ở scratchpad).**

```
so request gui di      : 8
tra_loi                : ''
in ra man hinh se la   : 'Trợ lý: '
vai tro cuoi lich su   : user
luot sau se thanh      : ['assistant', 'user', 'user']      <-- hai lượt user liên tiếp

== stop_reason=max_tokens giua tool_use ==
tra_loi                : "[lượt này không sinh được câu trả lời — model dừng vì 'max_tokens'...]"
chuoi vai tro          : ['user', 'assistant']
khoi cuoi cua assistant: ['tool_use']
=> lich su co tool_use MA KHONG co tool_result theo sau
```

Cả hai trạng thái đều **vi phạm hợp đồng Messages API** — chính docstring của file (dòng 19-21) viết *"Messages API không cho hai lượt `user` liên tiếp"*, còn `core/llm/client.py:3` viết *"server strict kiểu Anthropic đòi tool_result cho mọi tool_use"*.

**Vì sao là CHẶN chứ không phải phiền toái.** `repl` bắt exception ở dòng 86 và in *"lượt này bỏ qua, **lịch sử giữ nguyên**"* — tức là **giữ nguyên lịch sử đã nhiễm độc**. Từ lượt đó trở đi mọi câu hỏi đều nổ cùng một lỗi; người dùng phải giết tiến trình. Ca (a) còn tệ hơn: không có exception nào cả, chỉ in ra `Trợ lý: ` trống rồi im lặng hỏng ở lượt sau.

**Đề xuất sửa.** Chỉ nhận lịch sử mới khi lượt kết thúc sạch; ngược lại trả lại `history` cũ kèm câu giải thích:

```python
sach = message is not None and message.stop_reason in ("end_turn", "stop_sequence") \
       and not any(b.type == "tool_use" for b in message.content)
if not sach:
    return ("[lượt này dừng giữa chừng (%s) — bỏ lượt, lịch sử giữ như trước]" % stop, history)
return tra_loi, messages
```

và đưa lưới "không trả rỗng" ra **ngoài** vòng `for` thay vì nằm trong nhánh `else`.

---

## NÊN SỬA

### N1 · `get_news.py:63, 76, 85` — join `news.article_revision` không khoá `version`, lệch khuôn mẫu của toàn repo

Mọi consumer khác của bảng này đều khoá bản:

| File | Cách khoá |
|---|---|
| `backend/etl/news_classify.py:110,119` | `JOIN LATERAL (... ORDER BY version DESC LIMIT 1)` |
| `backend/etl/news_store.py:43, 90` | `AND r.version = 1` |
| `backend/agent/tools/get_news.py` | **không khoá gì** |

Hôm nay chưa nổ (`SELECT max(version) FROM news.article_revision` → `1`; 0/8148 bài có >1 bản), nhưng `news_store.py:156-161` đọc bản mới nhất rồi **chèn version+1** khi nội dung đổi trong phiên (tính năng lát 7b). Ngày bản 2 xuất hiện, `tim_tin` nhân đôi bài trong `du_lieu` và thổi phồng `tong_khop`. Fixture `kho` chỉ seed một revision nên test không thể bắt.

Sửa: dùng `JOIN LATERAL (... ORDER BY version DESC LIMIT 1) r ON true` như `news_classify.py`, và thêm case fixture có hai revision.

### N2 · `_shared.py:19-25` (+ mọi caller) — cờ `da_cat` nói dối cả hai chiều

`cap_limit` chỉ báo "đã cắt" khi **người gọi xin nhiều hơn trần**, không hề biết kết quả có bị cắt thật hay không.

```
su kien FPT: kho co 177 su kien | tool tra 20 | da_cat = False
```

Model nhận 20/177 sự kiện kèm cờ nói "chưa cắt" ⇒ đủ để kết luận sai *"FPT chỉ chia cổ tức 2 lần"*. Chiều ngược lại cũng sai: `limit=500` trên tập 3 dòng vẫn ra `da_cat=True`.

Sửa: tính cờ từ kết quả thật (`da_cat = len(rows) >= lim`), hoặc trả thêm `tong_khop` như `get_news` đã làm. Test `test_a04_shared.py:19-22` hiện mã hoá đúng ngữ nghĩa sai này nên phải sửa theo.

### N3 · `get_macro_series.py:32` — danh mục cắt câm ở 40 mục, mà danh mục là cửa duy nhất để model tìm mã

```
danh muc khong keyword : tra ve 40 | tong that 192 | khong co truong nao bao cat
danh muc keyword 'vn'  : kho khop 69 | tra ve 40   | khong co truong nao bao cat
```

Docstring của chính file (dòng 13-14) nói đây là *"cách model tìm mã mà không phải nhồi hàng trăm mã vào system prompt"* — cắt câm 40/192 làm hỏng đúng mục đích đó, và đẩy model tới kết luận phủ định sai.

Sửa: trả `tong_khop` + `da_cat`, hoặc nâng trần khi có `keyword`.

### N4 · `compare_peers.py:44` — cắt câm ở 10 mã và **im lặng nuốt mã không tra được**

```
industry_code='NGANHANG' -> so_dong 10: ['ABB','ACB','BAB','BID','BVB','CTG','EIB','EVF','HDB','KLB']
   (10 mã đầu bảng chữ cái, không cờ, không tổng)
tickers=['HPG','ZZZZ']   -> {"so_dong": 1, "du_lieu": [{"ma": "HPG", ...}]}
   (không một chữ nào nói ZZZZ không tồn tại)
```

Hai công cụ khác (`get_price_series`, `get_corporate_events`) đều gọi `resolve_ticker` và trả `khong_tim_thay` + gợi ý; `compare_peers` bỏ qua bước đó nên model có thể trả lời về một mã nó tự nghĩ ra mà không bị chặn.

### N5 · `get_price_series.py:18, 45` — cắt 400 phiên câm, và cắt mất **đầu** khoảng hỏi

`ORDER BY trading_date DESC LIMIT 400` giữ 400 phiên **mới nhất** trong khoảng, rồi `reversed`. Hỏi 5 năm sẽ nhận ~1,5 năm cuối, không cờ `da_cat` (mọi công cụ anh em đều có). Đủ để sinh câu trả lời sai kiểu *"đáy 3 năm là X"*. Hiện chưa chạm được trên dev vì HPG mới có 60 phiên, nhưng đây là đường code, không phải trạng thái dữ liệu.

### N6 · `screen_stocks.py:34-37, 49-51` — nổ `KeyError`/`AttributeError` với đối số model sinh; whitelist lọt giá trị falsy

```
criteria=[{"metric_code":"rtd21","operator":"<"}]  -> KeyError 'value'
criteria=[{"operator":"<","value":5}]              -> KeyError 'metric_code'
criteria=["rtd21 < 5"]                             -> AttributeError 'str' object has no attribute 'get'
```

SDK có bắt (`_tool_dispatch.tool_error_content` trả `repr(exc)` kèm `is_error=True`) nên chat không sập — nhưng model nhận `KeyError('value')` thô, trong khi **mọi đầu vào sai khác** của lát này đều trả `{"loi": true, "ly_do": ..., "..._hop_le": [...]}` có cấu trúc. Lệch khuôn ngay trong cùng một file.

Về SQL injection: **không khai thác được**. `metric_code`/`sort_by` phải nằm trong `LABELS` mới đi tiếp. Nhưng phép kiểm `if c and c not in LABELS` **bỏ qua mọi giá trị falsy** (`None`, `""`, `0`), và chúng vẫn được nội suy vào f-string ở dòng 51/63/65 (thành `'None'`, `''`…). Vô hại hôm nay vì falsy không mang được ký tự nào, song đây là whitelist dựa trên truthiness — nên siết thành `if not isinstance(c, str) or c not in LABELS` để lối vào chuỗi động không phụ thuộc may mắn.

### N7 · `tests/agent/test_a12_tools_log.py:37-44` — test "ghi sổ dưới role thật" không chạy câu lệnh mà production chạy

Test tự viết một `INSERT` 8 cột, còn `agent/llm_log.py:25-30` chạy `_SQL` **11 cột** (thêm `cache_read_tokens`, `thinking_tokens`, `error`). Đây đúng cái §3.5 cấm: nghiệm thu bằng một thứ khác với thứ tiến trình thật sự chạy. Nguy hiểm gấp đôi vì `log_llm_call` **nuốt mọi exception** (dòng 51-52, chỉ in stderr) — quyền thiếu hay CHECK vi phạm sẽ im lặng suốt đời, giống hệt ca `assert_migrated` của ingester.

Sửa: gọi thẳng `log_llm_call(engine_role_etl, msg_gia, ...)` rồi `SELECT` lại dòng vừa ghi và assert 4 loại token.

Cùng file, dòng 10: `from agent.db import ops_engine` **không dùng ở đâu** — rác import (§4.4.3).

### N8 · Hình dạng trạng thái không đồng nhất ở hai chỗ

- `get_industry_tree.py:46-51`: mã ngành bịa → `{"nhom": []}`, không `tim_thay`, không `co_du_lieu`. Đúng cái mà docstring `_shared.py:3-5` cấm ("phân biệt bằng TRƯỜNG TƯỜNG MINH chứ không bằng độ dài mảng").
- `get_news.py:97-103`: `tim_tin(ticker="ZZZZ")` trả `ghi_chu: "…còn 7918 bài chưa phân loại nên chưa thể lọc theo nhãn"` — đổ lỗi sai chỗ, nguyên nhân thật là mã không tồn tại. Đường tin không gọi `resolve_ticker`.

---

## GHI NHẬN

### G1 · Ba docstring khẳng định một sự thật **chưa đo** về kho thật (`screener_params`)

`get_financials.py:8-11`, `screen_stocks.py:7-9`, `compare_peers.py:3-5` (và `ledger.md:57`) viết: *"cùng một code có thể tồn tại song song ở 'screener_params' — không khoá sẽ **nhân đôi dòng trên kho thật**"*. Đo hôm nay:

```
SELECT dictionary, count(*) FROM market.metric_dictionary GROUP BY 1
   ('field_dictionary', 729)          -- KHÔNG có dòng screener_params nào
SELECT code FROM ... GROUP BY code HAVING count(*)>1   -> 0 dòng
```

**Code thì đúng** (PK là `(dictionary, code)`, CHECK của migration `0004` cho phép cả hai giá trị, khoá `dictionary` là phòng thủ hợp lý). Chỉ có **câu chữ** là sai: không có ca nhân đôi nào trên kho thật. Sửa thành *"sẽ nhân đôi nếu `screener_params` được nạp"* — §1.2 / §3.2.

### G2 · `format.py:46-49` — nhánh `co_phieu` / `so_luong` là code chết

21 mã trong bảng nhãn đóng chỉ mang 4 đơn vị (đo):

```
('VND', 14) ('VND/CP', 3) ('ty_le_thap_phan', 2) ('lan', 2)
```

`co_phieu`/`so_luong` chỉ tồn tại ở các mã đã bị bảng nhãn từ chối ⇒ không đường nào tới được. §4.4.2 ("không xử lý cho kịch bản không thể xảy ra").

### G3 · `labels.py:46-47` — `label_for()` chỉ có test gọi

Production đọc thẳng `LABELS[...]`. Một hàm public tồn tại chỉ để test gọi là abstraction thừa (§4.4.2).

### G4 · `tools/__init__.py:45, 55, 67` — đối số mặc định là list rỗng (mutable default)

`metric_codes: list[str] = []`, `criteria: list[dict] = []`, `tickers: list[str] = []`. Hôm nay an toàn vì mọi hàm đều `list(x or [])`, nhưng đây là bẫy Python kinh điển và có lý do khác (`test_a12` giải thích: tham số không mặc định sẽ rơi vào `required`). `list[str] | None = None` đạt cùng mục tiêu — đúng khuôn `str | None = None` các tham số khác đang dùng. Nếu MiniMax không nuốt được `anyOf`, giữ nguyên nhưng ghi lý do vào chỗ khai báo.

### G5 · `chat.py:44, 56` — lịch sử chat không có trần, tri thức L2 nằm lại vĩnh viễn

System prompt L1 = **81.242 ký tự** mỗi request. Mỗi lần model gọi `load_knowledge_reference`, toàn văn file đi vào `tool_result` rồi **ở lại `history` cả phiên**, gửi lại ở mọi lượt sau:

```
financial-statements.md  49.652 | valuation.md 45.994 | macro-money-creation.md 44.450
technical-indicators.md  40.003 | portfolio-and-rotation.md 38.102 | ...
```

Ba chủ đề trong một phiên ≈ 140k ký tự lặp lại mỗi lượt. Không có cắt tỉa, không có chốt chặn cửa sổ ngữ cảnh. Đề nghị: cắt lịch sử theo số lượt hoặc thay `tool_result` L2 cũ bằng một dòng tóm tắt sau khi đã dùng.

### G6 · `screen_stocks.py:51, 63, 65` — `::numeric` trên giá trị đến từ nguồn ngoài

Một giá trị không phải số trong `payload->'stockScreenerItem'` cho mã đang sắp/lọc sẽ giết cả câu (`invalid input syntax for type numeric`), không riêng một dòng. Đo phiên 2026-09-04 (1.541 dòng): **0 giá trị lệch** trên 8 mã đang dùng ⇒ hiện là rủi ro tiềm ẩn, không phải lỗi đang sống. Hoá giải rẻ: `NULLIF(...,'')::numeric` + guard regex, hoặc `to_number` an toàn.

### G7 · `test_a03_system_prompt.py:35` và `test_a13_chat.py:106` — tiêu chí là số thời điểm

`assert len(load_l1()) >= 61_240` và `assert len(system[1]["text"]) > 50_000` đo độ dài file skill. Skill là tài liệu **được bảo trì** (`docs/30-skills/maintenance.md`); rút gọn một đoạn văn sẽ làm đỏ test mà không có hành vi nào sai. §4.4.4 "tiêu chí phải bất biến, không phải số thời điểm". Chính test đó (dòng 27-29) đã có cách kiểm tốt hơn — mốc nội dung (`"# Cố vấn chứng khoán Việt Nam"`, `"analysis-framework"`).

### G8 · `test_a01_db.py:35-39` — test chỉ khẳng định "không ném"

`test_dlck_api_can_read_the_three_views` chạy `SELECT 1 FROM <view> LIMIT 1` cho ba view, không assert giá trị nào (§4.5 luật 4). Chấp nhận được như phép thử quyền, nhưng rẻ hơn nếu assert luôn cột mà tầng ngữ nghĩa thật sự đọc (`v.source`, `value_spliced`) — quyền cột và đổi tên cột sẽ cùng được canh.

### G9 · `__main__.py:23` — thiếu `ETL_DATABASE_URL` là chết cả chat, trái với chính chủ trương của sổ

`llm_log.py:14` viết *"Sổ là phụ, chat là chính"* và nuốt mọi lỗi ghi. Nhưng `ops_engine()` gọi lúc khởi động sẽ ném `RuntimeError("thieu ETL_DATABASE_URL")` và chặn hẳn REPL. Nên để `ops_eng = None` khi biến vắng (vòng `run_turn` đã có nhánh `if ops_eng is not None`).

### G10 · `chat.py:78` — Ctrl+C giữa lượt gọi model thoát ra ngoài kèm traceback

`except (EOFError, KeyboardInterrupt)` chỉ bọc `input()`. `KeyboardInterrupt` không phải `Exception` nên `except Exception` ở dòng 86 không bắt; một câu chat 30–60 giây bị ngắt sẽ in traceback thay vì "Tạm biệt.".

---

## Những chỗ làm đúng (ghi để khỏi sửa nhầm)

- **Không một chỗ nào viết `:x::type`** — grep toàn `agent/` chỉ ra 6 dòng *chú thích* nhắc luật, không có usage. Mọi ép kiểu đều `CAST(:x AS ...)`.
- **Ba join `metric_dictionary` đều khoá `dictionary='field_dictionary'`** (`get_financials.py:28`, `screen_stocks.py:26`, `compare_peers.py:50`).
- **SQL qualify đủ `schema.object`**, kể cả hàm extension (`extensions.similarity` ở `_shared.py:63-65`, `news.immutable_unaccent` ở `get_news.py`).
- **Bảng 27,3 triệu dòng lọc `issuer_id` trước** và trúng PK index — đo thật:
  `Bitmap Heap Scan ... Recheck Cond: ((issuer_id = $0) AND (statement_type='IS') AND (metric_code = ANY(...)))`, cả lời gọi công cụ hết **0,234s**.
- **Không kết nối/transaction nào bắc qua lời gọi model**: `chay()` (`tools/__init__.py:24-27`) mở–đóng trong thân từng tool; `log_llm_call` mở–commit–đóng riêng.
- `SET LOCAL statement_timeout = '20s'` **thật sự có hiệu lực** (kiểm: `SHOW statement_timeout` → `20s` trong cùng kết nối, `0` ở kết nối mới) — SQLAlchemy autobegin giữ đúng transaction cho `SET LOCAL`.
- **Không in giá trị biến môi trường ở đâu**: `os.environ.get` chỉ đọc; mọi thông báo lỗi chỉ mang `type(e).__name__` (`chat.py:87`, `llm_log.py:52`), `db.py:39` chỉ in **tên** biến.
- `assert_read_only` được test **dưới đúng role production** (`test_a01`), và mọi test tool đều `SET LOCAL ROLE dlck_api` — đúng tinh thần §3.5.

---

## Phán quyết

**Chưa merge được.** Phải sửa xong hai mục CHẶN trước: **C1** (lệch múi giờ ở `get_news` — 404/8147 bài đang bị khai sai ngày, 18/228 bài lọt lưới của một ngày, đúng bẫy đã trả giá ở §3.1) và **C2** (`chat.py` để lại lịch sử hỏng khi chạm `MAX_ITERATIONS` hoặc `max_tokens` giữa `tool_use`, khoá chết cả phiên và in ra câu trả lời trống). Nhóm NÊN SỬA — nhất là **N1** (join `article_revision` không khoá version, lệch khuôn mẫu repo) và **N2** (cờ `da_cat` nói dối: 20/177 sự kiện mà báo "chưa cắt") — nên gộp vào cùng đợt vì cả hai đều sinh câu trả lời sai một cách thầm lặng.
