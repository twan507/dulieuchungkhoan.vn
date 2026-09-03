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
