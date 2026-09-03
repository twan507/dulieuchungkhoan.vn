# Sổ ghi thực thi — `etl events` (lát 2)

**Nhánh:** `feat/events-daily-etl` *(tách từ `main` tại `194f5e1`)* · **Bắt đầu:** 2026-09-03

Sổ này ghi **cái đã chạy và output thật**, không ghi ý định. Quy tắc: chưa dán được output thì chưa được đánh ✅.

---

## Bước 0 — Trước khi viết dòng code nào

| Việc | Kết quả |
|---|---|
| Đo nguồn, 46 lời gọi thật | `02a8a8e` — [`measurements.md`](measurements.md) |
| Spec, chủ dự án duyệt | `5572937` |
| Plan 7 task | `194f5e1` |
| **Chạy thử toàn bộ code của plan ở scratchpad ngoài repo** | **34/34 xanh** (21 thuần + 13 trên Postgres thật) |
| Kiểm câu `ON CONFLICT` trên `postgres-data` thật, role `dlck_etl`, trong giao dịch rollback | Arbiter suy được · ghi lại cùng khoá ⇒ 1 dòng · khác `stage_key` ⇒ 2 dòng · cả 5 cột `coalesce` cùng NULL vẫn dedupe |
| Kiểm quyền `dlck_etl` trên mọi đường ghi | `issuer` · `issuer_external_id` · `staging.raw_payload` · `data_domain_state('market.events')` · `etl_run` — đủ cả năm |
| Kiểm dữ liệu có phá CHECK không | `lengthReport` ∈ {1..5} ✓ · `yearReport` 2015–2026 vừa `smallint` ✓ · `organCode`/`publicDate` không bao giờ rỗng ✓ |

**Một lỗi thật bắt được ở lượt chạy thử**, đã vá trong plan trước khi giao: ngưỡng vế (iv) `DUP_RATIO = 0.5%` đúng cho lượt thật (42/110.737 = 0,037%) nhưng **sai cho fixture dày ca biên** (4/28 = 14,3%) — job bị chính guard của nó từ chối, 3 test của Task 5 đỏ. Vá bằng cách ghim ngưỡng **trong test đấu nối** (`test_e20`), giữ nguyên ngưỡng production; `test_e18` vẫn là chủ sở hữu ngưỡng.

---

## Nhật ký từng task

### Task 1 · 2 · 3 — giao song song, `sonnet`, 2026-09-03

Ba task sở hữu file rời nhau nên chạy song song được; theo §4.2 **subagent chỉ ghi file, người điều phối commit** — không agent nào được chạy lệnh git.

| Task | Module | Test | Commit |
|---|---|---|---|
| 1 | `events_fetch` | 5 xanh | `c8655ac` |
| 2 | `events_normalize` | 9 xanh | `4c7a906` |
| 3 | `events_guard` | 7 xanh | `5a3197b` |

**Cách review — không tin bản dán của agent:** `diff` từng file trong repo với bản đã tự chạy xanh ở scratchpad *(bỏ nhiễu CRLF)*. Cả 6 file **trùng khít**. Sau đó tự chạy lại trong repo: `12 passed` (e16 + e18), `9 passed` (e17). Kiểm thêm: ba ngưỡng của `events_guard` nguyên vẹn (`0.02 / 0.005 / 20`), và plan không bị agent nào tick checkbox (41 chưa tick, 0 đã tick).

🔴 **Plan sai một chỗ, hai agent độc lập cùng bắt được.** Plan ghi lượt đỏ sẽ báo `ModuleNotFoundError: No module named 'etl.events_fetch'`; thực tế pytest báo `ImportError: cannot import name 'events_fetch' from 'etl'` vì test dùng dạng `from etl import X`. Một agent còn chạy `python -c` để chứng minh cả hai dạng import cho hai thông điệp khác nhau. **Cả ba đều báo lại thay vì bẻ test cho khớp** — đúng hành vi plan yêu cầu. Sửa plan theo thực tế: `1ed1b9e`.

Một phát hiện môi trường, cả ba agent cùng vấp: `TEST_DATABASE_URL` **bắt buộc kể cả với test thuần không đụng database**, vì `tests/etl/conftest.py` nạp `tests/schema/conftest.py` và file đó đọc biến này ngay lúc import — thiếu là hỏng ở bước thu thập test. Đã ghi thành ràng buộc toàn cục trong plan.

### Task 4 — `events_store`, `sonnet`, commit `75a2fdf`

8 test xanh. Agent **tự đối chiếu `SQL_UPSERT` với migration `0004`** trước khi chép, không đợi được nhắc. Người điều phối kiểm lại: năm dòng `coalesce` khớp từng ký tự, đúng thứ tự, đúng giá trị mặc định. Diff với bản đã chạy xanh: trùng khít.

### Task 5 — `events_job` + CLI, `sonnet`, commit `fa2ee8c`

🔴 **Lượt chạy trọn bộ test lộ một test đỏ, agent DỪNG và báo nguyên trạng thay vì sửa** — đúng chỉ thị. Agent còn tự chứng minh lỗi không do mình gây ra: chạy lại trọn bộ nhưng loại trừ hai file nó vừa tạo, lỗi vẫn y hệt.

**Người điều phối tự tái hiện, không nhận chẩn đoán theo mặt chữ:**

```
tests/etl/test_e19_events_store.py chạy riêng      → 8 passed
test_e10_refdata_job.py rồi test_e19 chạy nối nhau → 1 failed
8 dòng issuer_external_id còn lại sau lượt chạy: ['0106839469','0107490477','12615',
  '2172623','ACVN','ANOVA','NHN','SHB']
```

**Lỗi là của test tôi viết, không phải của `test_e10`.** `ensure_issuers` trả về **bảng tra toàn cục** — đó là hợp đồng đúng, vì `apply()` phải tra `issuer_id` cho mọi dòng. Assert `len(by_organ) == 17` là assert lên trạng thái toàn cục của database: chạy riêng thì đúng, chạy chung thì thành 25 vì `test_e10` commit thật và không dọn. Vi phạm §4.4.4 — *tiêu chí phải bất biến, không phải số thời điểm*.

Sửa thành điều hợp đồng thật sự hứa: mọi `organ_code` của lô đều tra được, và lượt hai không tạo thêm gì (`6071eab`). **Không sửa `test_e10`** — rác có sẵn thì báo, không tự dọn (§4.4.3).

```
386 passed, 2 skipped, 1 warning in 28.60s
```

Đúng con số plan dự đoán: 351 *(mốc sau lát 1)* + 35 mới.

---

## Task 6 — chạy thật vào kho production, 2026-09-03

Người điều phối tự chạy, không giao subagent.

**Bước 1 — dọn danh bạ: KHÔNG cần làm.** Kiểm `ops.etl_run` thì thấy lượt `--accept-drop` **đã chạy 2026-09-03 06:49 UTC** (run 62, `accept_drop: true`, `delisted: 439`), `directory_absent_since` nay bằng 0. Roadmap ghi *"lượt dọn chưa chạy"* đã lỗi thời — sửa ở Task 7.

**Trạng thái trước:** `corporate_event = 0` · `issuer = 1552` · `issuer_external_id(fiintrade) = 1552`.

### AC2 — lượt backfill đầu tiên

```
python -m etl events --accept-new        exit 0, real 2m39s

{'counts': {'AGM': 23467, 'CashDividend': 17970, 'StockDividend': 2100,
            'Earning': 57026, 'IPO': 77, 'ShareIssuance': 10097},
 'collected': {... y hệt counts ...},
 'rows_written': 110695, 'issuers_created': 517, 'dup_conflicts': 42,
 'retries': 0, 'watermark': '2026-09-03'}

AC2 — stats.rows_written == count(*) thật: True
```

🎯 **Ba con số dự đoán từ lượt đo trúng chính xác từng đơn vị:** 110.695 dòng · 517 issuer · 42 khoá đụng. Số gộp từng họ cũng khớp tuyệt đối — AGM 8 · CashDividend 4 · StockDividend 3 · ShareIssuance 27 · Earning 0 · IPO 0.

| Họ | Dòng trong kho |
|---|---|
| Earning | 57.026 |
| AGM | 23.459 |
| CashDividend | 17.966 |
| ShareIssuance | 10.070 |
| StockDividend | 2.097 |
| IPO | 77 |
| **Tổng** | **110.695** |

`issuer` 1.552 → **2.069** (+517). Công tắc miền: `active / 2026-09-03`.

### AC3 — idempotent

```
python -m etl events                     exit 0, real 1m58s
'rows_written': 110695, 'issuers_created': 0, 'retries': 2

110695 dòng, event_id từ 6 tới 110700
   dải id chỉ đủ chứa 110695 dòng ⇒ lượt 2 KHÔNG chèn dòng nào mới: True
   ingested_at được cập nhật ở lượt 2: 110695/110695 dòng ⇒ DO UPDATE có chạy thật
```

⚠️ **Một phép kiểm sai cách, tự bắt được:** ban đầu tôi kiểm `max(event_id) == count(*)` và nó ra `False` (110.700 vs 110.695). Phép kiểm đó **vô nghĩa** — `DO UPDATE` không đổi `event_id`, và dải id lệch 5 là do phép thử `ON CONFLICT` lúc trước đã đốt vài id trong giao dịch rollback. Kiểm đúng là **dải id + `ingested_at`**, như trên.

Lượt này còn tình cờ chứng minh đường retry chạy thật trong production: `retries: 2` — nguồn hỏng hai lần rồi tự phục hồi.

### AC4 — guard từ chối thật, bằng đột biến

Bỏ 1 bản ghi khỏi trang IPO rồi chạy:

```
exit code       : 1
corporate_event : 110695 -> 110695 | KHÔNG GHI GÌ: True
issuer          : 2069   -> 2069   | issuer cũng rollback: True
bằng chứng      : 0 -> 1
lý do từ chối   : guard refused: IPO: gom được 76 bản ghi, totalCount báo 77 — thiếu trang
```

Cột `issuer` rollback theo là bằng chứng guard **thật sự chạy TRƯỚC commit**, không phải sau.

### AC5 — dữ liệu dùng được cho lát sau

```
SELECT count(*) FROM market.corporate_event WHERE exright_date >= current_date;  →  30
```

30 sự kiện quyền còn ở phía trước — đúng tín hiệu lát 3/4 sẽ đọc để kích hoạt re-crawl giá.

### AC6 — đăng ký task, chủ dự án chạy trong cửa sổ admin

```
Đăng ký events (18:00 ngày làm việc — sau phiên và sau screener 15:20, dùng danh bạ tươi từ 08:00):
  + dlck-events              18:00             ->  python -m etl events

Đã kiểm lệnh của cả 9 task.
✅ Cả 9 task đăng ký S4U (đã soi Principal thật từng task, không chỉ soi lệnh)

<sau khi tắt lại>   9 task, TẤT CẢ Disabled

(Get-ScheduledTask -TaskName "dlck-events").Actions[0].Arguments
/c cd /d "...\backend" && set PYTHONIOENCODING=utf-8 && "...\uv.exe" run python -m etl events
   >> "D:\twan_projects\dlck-runtime\logs\events.log" 2>&1
```

`Assert-TaskCommand` (kèm `-MustNotContain "--accept-new"`) và `Assert-TaskPrincipal` chạy sạch. Nghiệm thu bằng **lệnh thật**, không bằng trạng thái hiển thị — §3.5.

⚠️ Script `-Force` bật lại 8 task đang tắt, đúng như cảnh báo của chính nó; khối lệnh đã gộp bước tắt lại ngay sau đó nên trạng thái cuối là **cả 9 `Disabled`**.

**AC1–AC6 ✅ — đóng trọn.**

---

## Nợ phát hiện sau khi đóng AC6

🔴 **`dlck-events` 18:00 đụng đầu `dlck-omo-1800` 18:00.** Bốn mốc OMO là 11:30 · 15:30 · **18:00** · 21:30. Spec §5.6 chọn 18:00 mà **không soi lịch task sẵn có** — trong khi repo đã có tiền lệ ngược lại: `dlck-screener` đặt 15:20 với lý do ghi thẳng trong script *"tránh 15:30 của OMO"*.

Nguy hiểm thực tế thấp *(khác nguồn, khác bảng, OMO xong trong vài giây, không tranh khoá)*, nhưng **trái quy ước dự án tự đặt**. Chờ chủ dự án quyết: dời sang 18:10, hay giữ 18:00 và ghi rõ là đã cân nhắc. Đổi giờ cần một lượt chạy lại script trong cửa sổ admin — không gấp vì cả 9 task đang `Disabled`.
