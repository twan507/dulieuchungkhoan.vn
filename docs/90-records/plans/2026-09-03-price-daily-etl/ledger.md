# Sổ ghi thực thi — `etl price` (lát 3)

**Nhánh:** `feat/price-daily-etl` *(tách từ `main` tại `48b4e3c`)* · **Bắt đầu:** 2026-09-04 00:20 · **Chỉ thị chủ dự án:** *"làm liên tục, vừa làm vừa kiểm, chỉ dừng khi có lỗi hoặc quyết định khó"*

Sổ này ghi **cái đã chạy và output thật**, không ghi ý định. Quy tắc: chưa dán được output thì chưa được đánh ✅.

---

## Bước 0 — Trước khi viết dòng code nào

| Việc | Kết quả |
|---|---|
| Đo nguồn, 18 lời gọi thật + 2 nguồn đối chứng (cổ tức lát 2, tick BVSC trong ClickHouse) | `7680788` — [`measurements.md`](measurements.md). **Hai điều tài liệu ghi sai:** `closePrice` là giá thô lịch sử; `status` lẫn `0`/`"Success"` |
| Spec (ba quyết định §4.8 kèm phương án loại + điều kiện đảo ngược) | `7680788` |
| Plan 8 task + fixture cắt từ bản đo | `48b4e3c` |
| Kiểm kho trước: `price_daily` 0 dòng · 1.523 cổ phiếu `listed` · 0 mã thiếu `issuer` · 0 issuer có > 1 security listed · `dlck_etl` có INSERT/SELECT/UPDATE/DELETE trên `price_daily` | truy vấn thật 2026-09-03 23:00 |

**Cách thực thi — tự làm, không giao subagent thực thi:** mỗi task là 1–2 file và cần nhìn output của vòng đỏ→xanh ngay (ô *"Tự làm"* của bảng CLAUDE.md §4.1). Review hai trục ở cuối vẫn giao subagent độc lập.

**Sự cố giữa chừng:** máy **reboot ~23:35** (uptime 1 h 05 lúc 00:40) và **Docker Desktop không tự lên** — đúng ca đã ghi ở [service-topology §5](../../../20-design/service-topology.md) ngày 03/09. Test e24 đỏ với `connection timeout expired` trước khi lộ ra bất kỳ lỗi code nào. Xử lý theo đúng tài liệu: mở Docker Desktop, **không** chạy `dev-start`; ba container `infra-*` tự lên sau ~10 s, Postgres healthy sau 5 s. Không mất gì trong repo (mọi file đã ghi trước reboot đều còn, kiểm bằng `ls` + `git status`).

---

## Nhật ký từng task — TDD đỏ → xanh, mỗi task một commit

| Task | Module | Đỏ | Xanh | Commit | Ghi chú |
|---|---|---|---|---|---|
| 1 | `price_fetch` | `ImportError: cannot import name 'price_fetch'` | 9 passed | `5bab4f1` | 🔴 **Một lỗi quy trình + một lỗi test.** Lần chạy đầu 3 đỏ mà commit vẫn đi qua vì `\| tail -3` nuốt exit code của pytest — gỡ bằng `git reset --soft`, từ đó mọi lệnh commit đứng sau `code=$?` tường minh. Lỗi test: đồng hồ giả **đứng yên** làm bộ giãn cách ngủ 0,5 s giữa mọi lời gọi ⇒ `slept == [2, 4]` thành `[2, 0.5, 4, 0.5]`. Sửa helper cho đồng hồ trôi theo latency (1,8 s > 0,5 s); plan sửa theo |
| 2 | `price_normalize` | `ImportError` | 6 passed | `3e40344` | Expected là literal thật từ fixture: `5747.8202873773` vs `14500`; DMX 17/08 `88500`/`84499.8` |
| 3 | `price_guard` | `ImportError` | 5 passed | `344a3f6` | Ca biên đúng ngưỡng: 31/1.523 = 2,04 % từ chối, 30/1.523 = 1,97 % qua |
| 4 | `price_store` | `ImportError` → rồi **`IndeterminateDatatype: could not determine data type of parameter $8`** | 5 passed | `c323ccd` | Tham số `:fa` trần trong `jsonb_build_object` (hàm variadic `any`) — Postgres không suy được kiểu; `cast(:fa AS text)`. **Xác nhận `rowcount` của executemany qua psycopg3 cộng dồn đúng**: `rows_changed` = 5 · 0 · 1 như spec seam 16 |
| 5 | `price_job` + CLI | `ImportError` (5 test đỏ theo lỗi $8 của Task 4) | 8 passed | `7c59593` | Test job không phụ thuộc dữ liệu của test khác trong `dulieu_test`: fetch giả trả `items: []` cho mã lạ, thứ tự con trỏ đọc từ `list_codes` thật thay vì assert tên mã |
| 5b | `price_job` | — | 8 passed | *(commit sau)* | httpx ghi INFO **từng request** — lượt AC3 lộ 148 dòng `HTTP Request: GET …` trong 135 dòng log đầu; các job trước gọi ≤ 52 lần nên chưa ai thấy. Hạ logger `httpx` xuống WARNING |

### AC1 — trọn bộ test backend

```
432 passed, 2 skipped, 1 warning in 28.61s
```

Đúng con số plan dự đoán: 399 *(mốc sau lát 2)* + 33 mới (9 + 6 + 5 + 5 + 8).

---

## Task 6 — chạy thật dưới credential production, 2026-09-04

### AC2 — chạy thử 3 mã TRƯỚC lượt toàn tập (§3.5)

```
python -m etl price --codes BID,VHM,TD6          exit 0, real 5.5 s

price xong: {'codes': 3, 'with_data': 3, 'invalid': 0, 'failed': 0, 'no_organ_code': [],
             'retries': 0, 'latest_trading_date': '2026-09-03', 'subset': True,
             'rows_sent': 180, 'rows_changed': 180, 'dup_dates': 0,
             'raw_close_mismatch': 0, 'elapsed_s': 5}

rows by ticker: BID 60 (2026-06-09 → 2026-09-03, 0 close_raw NULL) · TD6 60 · VHM 60
etl_run 71: success, rows_changed 180, raw_close_mismatch 0, subset true
data_domain_state('market.price'): 0 dòng  ← lượt subset không đụng công tắc miền, đúng spec
```

`VHM` đi qua `organCode = NHN` và `TD6` qua `5702162138` — hai ca bẫy 1 của quy ước chung, cả hai 60 phiên.

### AC3 — lượt hằng ngày toàn tập (đây cũng là phép đo nhịp tuần tự 1.523 lời gọi)

```
python -m etl price                              exit 0, 00:40:55 → 01:19:03 giờ VN

price xong: {'codes': 1523, 'with_data': 1523, 'invalid': 0, 'failed': 0, 'no_organ_code': [],
             'retries': 0, 'latest_trading_date': '2026-09-03',
             'rows_sent': 91165, 'rows_changed': 90985, 'dup_dates': 0,
             'raw_close_mismatch': 0, 'elapsed_s': 2288}
```

| Đối chiếu kho (truy vấn thật sau lượt) | Giá trị | Nghĩa |
|---|---|---|
| `count(*) price_daily` | **91.165** = `rows_sent` | mỗi mã ghi đúng số phiên trang 1 trả |
| `rows_changed` | **90.985 = 91.165 − 180** | 180 dòng của AC2 có payload y hệt ⇒ **bị bỏ qua đúng** — vế `WHERE … IS DISTINCT FROM` chạy thật trong production |
| security có dòng / cổ phiếu listed không có dòng | 1.523 / **0** | `with_data + invalid + failed + no_organ_code = codes` ✓ |
| phiên/mã min · max · trung bình | 10 · 60 · 59,9 | mã thưa giao dịch nhất chỉ có 10 phiên trong lịch sử |
| dải ngày | 2013-07-19 → 2026-09-03, 249 ngày phân biệt | 60 phiên gần nhất của mã thưa lùi tới 2013 |
| dòng mang ngày mới nhất 03/09 | 1.521 | 2 mã không có phiên 03/09 — hợp lệ (mã thưa) |
| `close_raw` NULL · `close_adj` NULL | **0 · 0** | quyết định §4.2 áp thật: giá thô điền đủ ngay lượt đầu |
| khoá `raw` | chỉ `fiintrade` (91.165) | |
| `price_factor ≠ 1` | 22.064 dòng | mã có sự kiện quyền trong 60 phiên gần nhất — view có nghĩa ngay |
| `data_domain_state('market.price')` | `active`, watermark `2026-09-03` | |
| log | 0 WARNING | không mã nào phải retry; không tín hiệu chặn (không 429/403/5xx, không `Failed` tạm) |

**Nhịp thật:** 1.523 lời gọi / 2.288 s = **1,50 s/lời gọi ≈ 40 request/phút**, liên tục 38 phút — cao hơn burst Screener đã đo (~29/phút) mà **không gặp tín hiệu chặn nào**. Đây là mức tải kế hoạch, chạy đúng rồi dừng (§4.3) — ghi vào [00-conventions §10](../../../10-sources/market/00-conventions.md).

### AC4 — idempotent

```
python -m etl price                              exit 0, 01:19:25 → 01:55:00, elapsed 2138 s

price xong: {'codes': 1523, 'with_data': 1523, 'invalid': 0, 'failed': 0, 'retries': 0,
             'latest_trading_date': '2026-09-03', 'rows_sent': 91165, 'rows_changed': 0,
             'dup_dates': 0, 'raw_close_mismatch': 0, 'elapsed_s': 2138}

count(*) price_daily: 91165 → 91165
```

**`rows_changed = 0` trên 91.165 dòng gửi lại** — không một payload nào đổi giữa 00:41 và 01:55 (kể cả dòng T+1 của phiên 03/09: nguồn chưa điền dòng tiền lúc đó). Lượt hai nhanh hơn 150 s vì không phải UPDATE dòng nào. 1.523 lời gọi nữa, 0 retry ⇒ tổng đêm nay **3.046 + 100 + 54 lời gọi liên tiếp** không tín hiệu chặn.

### AC5 — guard từ chối thật bằng đột biến

Đột biến bằng script thay chuỗi *(không dùng `git checkout` để khôi phục — bài học lát 2)*: trong `Fetcher.many`, mỗi mã thứ 33 raise `CodeInvalid` ⇒ 3/100 mã đầu bảng. Chạy `--codes` 100 mã đầu (`A32,AAA,AAH,…`):

```
MUTATED
price từ chối: ('3/100 mã không có dữ liệu (3 mã sai, 0 mã hỏng) — quá 2%',)        exit 1
REVERTED
rows: 91165 → 91165                                   KHÔNG GHI GÌ
etl_run 74: failed, error = "guard refused: 3/100 mã không có dữ liệu (3 mã sai, 0 mã hỏng) — quá 2%"
            stats.invalid_tickers = ['AGP', 'ATS', 'BHN']     ← bộ đếm NÊU TÊN
staging.raw_payload 'price:refusal': 1 dòng, meta.run_id = 74
git diff --stat etl/price_fetch.py: rỗng
```

### AC6 — `price_factor` có nghĩa trên lịch sử

```
python -m etl price --backfill --codes DMX,BID    exit 0, 121 s
backfill xong: {'cursor': None, 'codes_done': 2, 'pages': 54, 'rows_sent': 3160, 'rows_changed': 3082,
                'invalid_tickers': [], 'failed_tickers': [], 'retries': 0, 'budget_hit': False,
                'pass_complete': False, 'subset': True}
```

`rows_changed = 3.082 = 3.160 − 78` — 78 dòng (60 BID + 18 DMX) đã có từ lượt hằng ngày với payload y hệt, bị bỏ qua đúng. `cursor = None` và `pass_complete = False` vì là lượt `--codes` (subset không đụng con trỏ).

| Kiểm | Kết quả |
|---|---|
| DMX `price_factor` 14/08 · 17/08 · **18/08** · 19/08 | **0,9548 · 0,9548 · 1,0000 · 1,0000** — bậc đúng ngày không hưởng quyền, đúng hệ số (88.500 − 4.000)/88.500 |
| BID | **3.142 dòng** = `totalCount` nguồn, 2014-01-24 *(ngày niêm yết)* → 2026-09-03, **0** `close_raw` NULL |
| BID 2014-06-03 | `factor 0,3964` — `close_adj 5747.8202873773` / `close_raw 14500` — đúng số spec dự đoán từ bản đo |

### Sự cố giữa AC7 — máy NGỦ, và một lỗi thật lộ ra

Lượt backfill thứ nhất (`etl_run` 76) bắt đầu **02:00:01**; Windows vào sleep **02:00:06** (System event 42), thức **05:56** (event 107/1). Lời gọi đầu tiên treo qua giấc ngủ, thức dậy thành `httpx.ReadTimeout` — và **exception đó lọt qua vòng retry**, giết cả lượt ở mã đầu tiên: `codes_done = 0`, `status = failed`. Spec §5.2 ghi *"retry 3 lần cho mọi lỗi khác"*, nhưng `_page` chỉ xử lý **response xấu**, không bắt exception vận chuyển — cùng khuôn với `events_fetch`/`screener_fetch` (ở đó 9–52 lời gọi nên chưa ai gặp).

Sửa theo TDD, commit `e7f80f6`: hai test đỏ (`ReadTimeout` 2 lần rồi hồi ⇒ `retries = 2`, ngủ `[2, 4]`; `ConnectError` mãi ⇒ `FetchError` cho mã đó, `many` xếp vào `failed` không ném) → `_page` bắt `httpx.HTTPError` và cho đi cùng đường với response xấu → **11 passed**. Ngắt khẩn 10 mã liên tiếp vẫn giữ nguyên nên mạng chết thật vẫn dừng lượt.

**Điều code không chống được:** máy ngủ 4 tiếng. Ghi thành luật vận hành ở [backend/README](../../../../backend/README.md) (tắt sleep trước khi backfill qua đêm) và dạng hỏng thứ ba ở [service-topology §5](../../../20-design/service-topology.md).

### AC7 — backfill tiếp tục được (hai lượt `--max-minutes 3` nối nhau, cộng lượt 76 chết giữa chừng)

```
run 76  failed   cursor NULL  codes_done 0     ← ngủ máy, ReadTimeout ở mã đầu (trước bản vá)
run 77  success  cursor AAM   codes_done 4  pages 183  rows_sent 10864  rows_changed 10624  budget_hit true  256 s
        (A32 · AAA · AAH · AAM)
run 78  success  cursor ABC   codes_done 6  pages 151  rows_sent  8916  rows_changed  8556  budget_hit true  240 s
        log: "tiếp tục sau con trỏ AAM: còn 1519 mã"   (AAN · AAS · AAT · AAV · ABB · ABC)
```

Không mã nào làm hai lần: 4 + 6 = 10 mã, và `securities có > 60 dòng = 11` = 10 mã này + BID của AC6 (DMX chỉ 18 phiên). `rows_changed` = `rows_sent` − 60 × số mã *(60 phiên/mã đã có từ lượt hằng ngày với payload y hệt)* ở cả hai lượt — vế bỏ-qua-dòng-không-đổi chạy đúng cả trong backfill. Lượt 76 `failed` nhưng **không làm mất gì**: con trỏ NULL nên lượt 77 bắt đầu từ mã đầu, đúng thiết kế *"con trỏ ghi sau từng mã"*. Kho sau AC7: **113.427 dòng**.

Nhịp backfill đo được: 334 trang / 496 s ≈ **1,5 s/trang**, 33 trang/mã ⇒ ước toàn tập ~50.000 trang ≈ **20 giờ tuần tự**, tức 2–3 đêm `--max-minutes 600` với máy không ngủ.

### AC1 (lại) sau bản vá `e7f80f6`

```
434 passed, 2 skipped, 1 warning in 28.91s
```

### AC8 — đăng ký task `dlck-price`: ⏳ chờ chủ dự án (cần cửa sổ Run as Administrator)

Script đã có task thứ 10 (`51850f4`): `dlck-price` 15:40, `Assert-TaskCommand -MustContain "python -m etl price" -MustNotContain "--backfill"`. Khi đăng ký, kiểm bằng lệnh thật rồi tắt lại cùng cả đội:

```powershell
pwsh scripts/register-tasks.ps1 -LogonType S4U          # cửa sổ admin; script -Force sẽ BẬT lại task đang tắt — tắt lại ngay sau
(Get-ScheduledTask -TaskName "dlck-price").Triggers[0].StartBoundary   # phải có T15:40:00+07:00
(Get-ScheduledTask -TaskName "dlck-price").Actions[0].Arguments        # phải có "python -m etl price", KHÔNG có "--backfill"
(Get-ScheduledTask -TaskName "dlck-price-backfill").Triggers[0].DaysOfWeek          # Saturday
(Get-ScheduledTask -TaskName "dlck-price-backfill").Settings.ExecutionTimeLimit     # P3D (3 ngày)
(Get-ScheduledTask -TaskName "dlck-price-backfill").Actions[0].Arguments            # có "--backfill --stop-before-open"
Get-ScheduledTask -TaskName "dlck-*" | Disable-ScheduledTask           # giữ Disabled theo [4d]
# Muốn backfill chạy ngay tối nay: Enable-ScheduledTask dlck-price-backfill; Start-ScheduledTask dlck-price-backfill
```

**AC1–AC7 ✅ — AC8 ⏳ admin.**

---

## Review toàn nhánh — hai trục độc lập, `opus`, 2026-09-04

Hai reviewer chạy song song, không thấy nhau, báo riêng không xếp hạng chéo (§4.1.5). Cả hai tự chạy lại pytest và ra đúng `434 passed, 2 skipped`. Tổng cộng **8 lỗi thật đã sửa**, 1 lỗi test lộ ra khi sửa, và 7 ghi nhận.

### Đã sửa — một commit sau `89d255e`

| # | Trục | Phát hiện | Vì sao thật | Sửa |
|---|---|---|---|---|
| 1 | Chuẩn · **chặn merge** | `raw_close_mismatches` dùng **một cận ngày cho cả lượt** = min của mã thưa nhất — chính AC3 đã ra `2013-07-19` | Sau backfill đủ, vị từ `trading_date >= 2013-07-19` khớp ~100 % bảng ⇒ seq scan + detoast `raw` hàng triệu dòng **trong giao dịch ghi** của lượt 15:40. §4.4.4 *"còn đúng sau 3 tháng?"* — không | Cận **theo từng mã** qua `unnest(sids, lows)`; test seam 17 thêm ca cận 2026-09-01 bỏ qua dòng 28/08 |
| 2 | Spec · **chặn merge** | Chú thích migration `0004` vẫn *"NULL với backfill (quá khứ không có giá thô ở nguồn nào)"* và *"close_raw ← datafeed EOD"* | `database/migrations/` không thuộc vùng lịch sử (§1.7); người đọc schema đọc thẳng vào đó; AC3 chứng minh 0 dòng `close_raw` NULL | Thêm khối `ĐÍNH CHÍNH 2026-09-04` có ngày, **không đổi DDL** |
| 3 | Spec · **chặn merge** | Tóm tắt đầu `09-fiin-market-price.md` và `10-sources/README.md` còn *"97 trường"* trong khi chính lát này đo 99 và test chốt `len(payload) == 99` | Tầng reference tự mâu thuẫn; điều kiện §1.2 (có phép đo) đã thoả mà chỉ sửa 1/3 chỗ | Sửa cả hai, kèm *(đếm lại 2026-09-03)* |
| 4 | Chuẩn + Spec | Mã trả `Success` với `items: []` **không có tên** trong stats và **không vào vế (i)** | Nguồn đổi hành vi (rỗng thay vì `Code not valid`) cho 10 % mã thì lượt đầu — chưa có mốc cho (ii) — cho qua im lặng. Cũng là lý do đẳng thức AC3 đúng "trivially" | `stats.empty` + `empty_tickers`; `guard.check(..., empty=)` cộng vào tử số (i); test ca biên 31/30 |
| 5 | Chuẩn + Spec | `no_organ_code` chỉ có danh sách cắt 20, **không có tổng** | 30 mã mất organCode báo ra 20 và không ai biết thiếu — trái bài học 3 lát 1 | `stats.no_organ_code_count`; bất biến ghi vào backend/README: `with_data + empty + invalid + failed = codes` |
| 6 | Spec | Backfill thiếu `dup_dates` và `raw_close_mismatch` — đúng nơi `close_raw` được điền lần đầu cho 12,5 năm | §5.4 nói bộ đếm là chốt duy nhất của backfill; mắt của quyết định §4.2 nhắm đúng lúc cần mở | Cộng dồn `dup_dates`; gọi `raw_close_mismatches` cho từng mã trong chính giao dịch của mã đó; test seam 21 assert cả hai |
| 7 | Chuẩn + Spec | Test role `dlck_etl` chỉ chạy nhánh `--codes` (`subset`) ⇒ **không bao giờ** chạm `load_baseline`, `upsert_domain_state`, `store_refusal_evidence` dưới role | Đúng khuôn ba sự cố §3.5 — "luật viết hẹp, bug ở đường không ai test". AC3/AC5 thật đã chứng minh quyền, nhưng đó là ledger, không phải lưới hồi quy | Test chạy lượt toàn tập ×2 (đọc mốc), lượt bị từ chối, và backfill toàn tập dưới role |
| 8 | Chuẩn | `apply(conn, batch, …)` nhận list mà mọi caller truyền đúng một phần tử (§4.4.2) | Chữ ký hứa khả năng gộp không ai dùng; `BATCH` chỉ có nghĩa ở backfill | `apply(conn, security_id, rows, fetched_at)` |
| 9 | Chuẩn *(ghi nhận, sửa vì 2 dòng)* | `--codes` trỏ vào mã listed chưa có organCode ⇒ tập gọi rỗng ⇒ guard (0) nói *"nguồn hỏng"* | Chẩn đoán sai hướng | `_codes_or_raise`: lỗi rõ *"không mã nào có organCode"* trước khi gọi nguồn; test mới |
| 10 | Chuẩn + Spec *(ghi nhận, sửa vì 3 dòng)* | Con trỏ backfill so chuỗi bằng Python `>` trong khi thứ tự do `ORDER BY` của Postgres | Hai collation; trùng nhau với ticker ASCII hiện tại, không nên treo tính đúng vào đó | `_resume_point` nối theo **vị trí** trong danh sách, chỉ lùi về so chuỗi khi mã con trỏ đã rời sàn |
| 11 | Spec *(ghi nhận, sửa vì 2 dòng)* | Trùng organCode chỉ kiểm **trong tập `--codes` đã lọc** | Lượt re-crawl vài mã (đường lát 4 sẽ gọi) không thấy khi giả định §2.2.4 vỡ | Kiểm trên toàn tập listed trước khi lọc; test thêm ca `--codes ["ZZX"]` vẫn đỏ |
| 12 | Chuẩn | Số test **399** còn ở `roadmap.md:29`, `README.md:69`, `README.md:92`, `database/README.md:84` — §8 spec quên chuỗi số test trong phép quét | §1.7 | Quét lại toàn repo → **436** |
| 13 | Chuẩn | [4d] — chủ sở hữu trạng thái task — vẫn *"script đăng ký 9 task"* | Ba nơi không phải chủ đã đúng, bản chuẩn lại sai — bẫy hai nguồn sự thật §1.6 | Thêm mệnh đề: script 10 task, `dlck-price` chưa đăng ký thật, phải tắt lại ngay sau khi đăng ký |

🔴 **Lỗi test lộ ra khi sửa #4:** hai test job toàn tập đỏ **chỉ khi chạy trọn bộ** — DB test có 2 cổ phiếu do `test_e10` để lại, fake fetch trả rỗng cho chúng, và nay `empty` được đếm ⇒ 2/5 = 40 % > 2 % từ chối. Nghĩa là trước review, hai test đó xanh **nhờ đúng cái lỗ vừa vá**. Không xoá dữ liệu của test khác (bài học lát 2); bọc `list_codes` thật để job chỉ thấy mã `ZZ*` — truy vấn thật vẫn chạy, `subset` vẫn `False`.

**Kết quả: 434 → 436 test, tất cả xanh.** Smoke lại dưới credential production sau khi đổi code (`eae6140`):

```
python -m etl price --codes BID,VHM,TD6     exit 0, 4 s
  {'codes': 3, 'with_data': 3, 'empty': 0, 'invalid': 0, 'failed': 0, 'no_organ_code_count': 0,
   'rows_sent': 180, 'rows_changed': 0, 'dup_dates': 0, 'raw_close_mismatch': 0, 'subset': True}
python -m etl price --backfill --codes DMX  exit 0, 1 s
  {'codes_done': 1, 'pages': 1, 'rows_sent': 18, 'rows_changed': 0, 'dup_dates': 0,
   'raw_close_mismatch': 0, 'subset': True}
```

Cận theo từng mã và bộ đếm mới chạy thật trên kho production; `rows_changed = 0` ở cả hai vì payload chưa đổi kể từ AC4.

### Còn ghi nhận, KHÔNG sửa ở nhánh này

- **`events_fetch.py` và `screener_fetch.py` mang đúng lỗi `e7f80f6` vừa sửa** (exception vận chuyển lọt qua retry) — §4.4.3 rác có sẵn thì báo, không sửa trong nhánh lát 3. ✅ **Đã vá sau merge theo yêu cầu chủ dự án** (`356cdc9`, merge `4b22e50`): mỗi fetcher hai test đỏ→xanh cùng khuôn e21; trọn bộ **442 passed, 2 skipped**.
- `sa.create_engine(url)` nằm ngoài `try` ở cả 4 job — DSN hỏng in mật khẩu vào traceback; mẫu có sẵn, sửa toàn cục sau.
- `save_progress` 1 UPDATE/mã ⇒ ~1.523 phiên bản dòng `etl_run` mỗi vòng backfill — cố ý theo spec §5.5e.
- Mã làm nổ `SourceDown` không vào `failed_tickers` — lượt dừng nên vô hại.
- `market-data-store.md §5.2` khối DDL minh hoạ còn `organ_code text NOT NULL` — nợ từ lần tách `issuer`/`security`, chủ dự án quyết.
- `Decimal(str(v))` đi qua `float` một nhịp — đo trên fixture 0/N literal lệch; chữ spec rộng hơn cơ chế.
- Roadmap/index ghi "merge `main`" — đúng sau bước merge cuối ledger này.
- `service-topology §5` giữ "cả 9 task" cho task **đã đăng ký thật** — cố ý, phân biệt với 10 task trong script.

---

## Merge và bổ sung sau merge — 2026-09-04

**Merge `main`:** `b07e90d` (`--no-ff`, 13 commit của nhánh). Trọn bộ test chạy lại trên `main`: `436 passed, 2 skipped`.

### Máy ngủ theo LỊCH — thiết kế lại sau khi chủ dự án làm rõ (`01efebb`, merge `0147e8d`)

Chủ dự án: máy **không tự ngủ** vì nhàn rỗi; giấc ngủ 02:00 là **lịch tự đặt** và sẽ còn. Hệ quả: ý *"giữ máy thức bằng `SetThreadExecutionState`"* tôi đề xuất lúc đầu **vô dụng** — nó chỉ chặn ngủ do nhàn rỗi, suspend theo lệnh thì app không chặn được (từ Vista). Thiết kế đúng là job **sống qua giấc ngủ**, ba chỗ hở đóng cả ba:

| Chỗ hở | Trước | Sau |
|---|---|---|
| Lời gọi HTTP treo qua giấc ngủ | `ReadTimeout` giết cả lượt (lượt 76) | `e7f80f6`: thử lại 3 lần như response xấu |
| Kết nối Postgres nằm trong pool suốt 38 phút fetch, chết sau giấc ngủ | `OperationalError` ở `load_baseline`/giao dịch ghi **sau khi đã gọi xong 1.523 lời gọi** | `create_engine(url, pool_pre_ping=True)` — thay kết nối chết trước khi dùng |
| Ngân sách `--max-minutes` | theo `monotonic` — thức dậy còn ngân sách thì chạy tiếp, có thể lấn vào giờ giao dịch | theo **đồng hồ tường** (`_wall_clock`) — giờ ngủ vẫn tính ⇒ thức dậy là dừng sau mã đang dở, con trỏ đã lưu |

Hai test mới (TDD): `pool_pre_ping` có mặt trong tham số `create_engine`; và ngân sách 60 phút + "nhảy 4 giờ" ⇒ `codes_done = 1`, `budget_hit = true`. 🔴 **Một test xanh giả suýt lọt:** patch `time.time` toàn cục thì **SQLAlchemy pool cũng gọi `time.time()`** khi tạo kết nối trong `open_run` (trước khi đặt hạn) và ăn mất tick đầu ⇒ hạn đặt sai, `codes_done = 3`. Sửa bằng seam `_wall_clock` trong job, test patch đúng seam đó.

```
438 passed, 2 skipped, 1 warning in 27.97s
smoke production: python -m etl price --codes BID  → exit 0, with_data 1, rows_changed 0, raw_close_mismatch 0
```

Cách chạy backfill qua đêm nay ghi ở [backend/README](../../../../backend/README.md): chọn `--max-minutes N` hết trước 02:00; máy ngủ giữa chừng cũng không hỏng, chỉ dừng sớm.

### Backfill chuyển sang task Scheduler — quyết định chủ dự án 2026-09-04 (`6b8b27e`)

Sau merge, `events_fetch`/`screener_fetch` được vá cùng lỗi timeout (`356cdc9`, 442 test). Tôi đã dựng một driver bash ngoài repo chạy backfill trong phiên chat theo cửa sổ ngoài giờ giao dịch; chủ dự án **bác**: backfill phải là **task trên máy**, kích hoạt tay buổi tối khi cần và chạy liên tục thứ 7/chủ nhật, không chạy trong chat. Driver và tiến trình bị kill lúc ~06:55 (`lượt 82`: con trỏ `ACC`, 7 mã, 381 trang trong lượt đó — đóng tay `failed` với lý do, con trỏ còn nguyên; kho **135.629 dòng**).

Thiết kế thay thế, TDD (3 test mới, **444 passed, 2 skipped**):

| Thành phần | Nội dung |
|---|---|
| `--stop-before-open` | hạn = **08:45 của ngày giao dịch kế tiếp** (Thứ 2–6, chưa biết ngày lễ), tính lúc job bắt đầu — tối thứ 3 ⇒ sáng thứ 4; thứ 7 ⇒ sáng thứ 2 (~56 giờ, đủ trọn vòng ~20 giờ). Cộng được với `--max-minutes` (lấy hạn sớm hơn); `stats.stop_at` ghi hạn để người vận hành thấy |
| Task `dlck-price-backfill` | `etl price --backfill --stop-before-open`, trigger **thứ 7 00:05**, `ExecutionTimeLimit` 3 ngày (mặc định 12 giờ sẽ giết lượt cuối tuần), `MultipleInstances IgnoreNew`, đăng ký `Disabled` cùng cả đội; kích hoạt tay: `Start-ScheduledTask dlck-price-backfill` |
| `Register-DlckTask` | thêm `-DaysOfWeek` (mặc định Thứ 2–6) và `-ExecutionTimeLimit` (mặc định 12 giờ) — hai task cũ không đổi hành vi |

Ghi chú thiết kế: hết vòng thì lượt kế là vòng mới — task bật thường trực nghĩa là làm mới toàn bộ chuỗi điều chỉnh mỗi cuối tuần (~20 giờ gọi); tắt sau vòng đầu nếu chỉ muốn re-crawl theo sự kiện (lát 4). Ghi ở backend/README.

**AC8 nay gồm hai task**, cùng một cửa sổ admin — lệnh cập nhật ở mục AC8 trên (thêm kiểm `dlck-price-backfill`: `Triggers[0].DaysOfWeek` = Saturday, `Settings.ExecutionTimeLimit` = `P3D`, lệnh chứa `--stop-before-open`).
