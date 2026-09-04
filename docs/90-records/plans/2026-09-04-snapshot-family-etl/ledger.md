# Sổ ghi thực thi — lát 4 `etl snapshot`

**Ngày:** 2026-09-04 · **Nhánh:** `feat/snapshot-family-etl` · [spec](spec.md) · [plan](plan.md) · [số đo nguồn](measurements.md)

Thực thi bằng subagent (Sonnet, chỉ định tường minh), review hai trục sau mỗi task, artifact điều phối để ở scratchpad ngoài repo.

---

## 1. Tiêu chí nghiệm thu

| | Nội dung | Kết quả |
|---|---|---|
| AC1 | Toàn bộ test xanh | ✅ **532 passed, 2 skipped** *(trước lát này: 456)* |
| AC2 | `--codes` 3 mã → 12 dòng, 4 kind | ✅ run 88 |
| AC3 | Lượt đầy đủ vào kho production | ✅ run 91 — **234 target, 234 lời gọi, 0 retry** |
| AC4 | Chạy lại cùng ngày | ✅ run 89 — `unchanged 12`, `rows_written 0` |
| **AC5** | **Chạy lại ngày hôm sau: `changed_floor = 0`** | ⏳ **CHƯA CHẠY ĐƯỢC** — phép đo ngày-qua-ngày, mở lại 2026-09-05 |
| AC6 | Re-crawl giá theo sự kiện quyền | ✅ run 90 → `rows_changed 18.429`; run 92 → `0` |
| AC7 | Ép hỏng ⇒ lượt `failed`, 0 dòng ghi | ✅ run 93 |

### AC2 — ba mã, đường ghi thật

```
uv run python -m etl snapshot --codes A32,BAB,BVB
{'tally': {'attempted': 12, 'failed': 0, 'bad_shape': 0, 'checked': 12, 'first': 12,
           'floor_compared': 0, 'changed_floor': 0, 'changed_event': 0, 'unchanged': 0},
 'rows_written': 12, 'calls': 12, 'retries': 0, 'run_date': '2026-09-04'}
```

### AC3 — lượt đầy đủ, 2026-09-04

```
{'tally': {'attempted': 234, 'failed': 0, 'bad_shape': 0, 'checked': 234, 'first': 234,
           'floor_compared': 0, 'changed_floor': 0, 'changed_event': 0, 'unchanged': 0},
 'rows_written': 234, 'calls': 234, 'retries': 0, 'stopped_early': False,
 'watermark': '2026-09-03'}
```

**234 target = đúng quota** 70 (`ownership`) + 70 (`valuation`) + 70 (`dividend`) + 24 (`snapshot`). Cộng 12 dòng của AC2 thành 246 dòng `snapshot_daily` trong ngày. Phần snapshot chạy **~123 giây**; tổng lượt 654 giây vì kèm re-crawl giá (531 giây).

**0 tín hiệu chặn** trên 234 lời gọi tuần tự — nhịp thấp hơn 6 lần so với lát 3 (1.523 lời gọi ~40 request/phút, cũng không bị chặn).

### AC4 — chạy lại cùng ngày

```
{'tally': {'attempted': 12, 'checked': 12, 'first': 0, 'floor_compared': 12,
           'changed_floor': 0, 'unchanged': 12}, 'rows_written': 0, 'calls': 12}
```

Tập trắng đứng vững qua lượt hai: 12/12 mã × kind cho ra **cùng hash**, không dòng nào được ghi thêm.

### AC6 — re-crawl giá, và một phép đo idempotent ngoài dự kiến

| Lượt | Mã | Trang | Dòng gửi | **Dòng đổi** | Thời gian |
|---|---|---|---|---|---|
| run 90 *(lần đầu)* | 8 | 320 | 18.909 | **18.429** | 517 s |
| run 92 *(lần hai)* | 8 | 320 | 18.909 | **0** | 531 s |

Chuỗi điều chỉnh **đổi thật** ở lượt đầu và **đứng yên** ở lượt hai. Hệ số kiểm trực tiếp trên kho:

| Mã | Sự kiện 2026-09-03 | Hệ số trước ngày ex | Từ ngày ex |
|---|---|---|---|
| RYG | `StockDividend` + 2 × `ShareIssuance` | **0,8547** | 1,0 |
| TCH | `ShareIssuance` | **0,9091** | 1,0 |
| DCF | chỉ `AGM` | 1,0 | 1,0 |

Dòng DCF là bằng chứng độc lập cho quyết định lọc loại sự kiện ở §2.5 dưới: `AGM` không đụng tới hệ số điều chỉnh.

### AC7 — ép nguồn hỏng

```
uv run python -c "... sj.run(kinds=['valuation'], get=lambda u, t: (503, ''), ...)"
ERROR etl.snapshot snapshot từ chối: ['tỷ lệ lời gọi hỏng 100.0% > 20% (70/70) — nguồn đang sự cố']
EXIT 1
```

Kiểm sau lượt: `ops.etl_run` run 93 `failed` đúng lý do · `snapshot_daily` vẫn **246 dòng** · `ops.snapshot_check` mốc kiểm mới nhất vẫn là `03:18:48` của AC3 — lượt hỏng **không** đụng sổ kiểm.

🔴 **Một vế của AC7 KHÔNG được chứng minh bởi lượt này:** `staging.raw_payload` có **0 dòng**, vì mọi target đều hỏng nên không có payload nào để làm bằng chứng. Đường ghi bằng chứng được chứng minh ở tầng test job (`test_a_partial_outage_refuses_the_run_and_leaves_real_evidence`: 4/20 mã thành công, 16 hỏng ⇒ guard từ chối, 0 dòng `snapshot_daily`, và đúng 4 dòng `staging.raw_payload` với `endpoint_key` dạng `snapshot:<kind>:<organCode>`). Ghi ra đây vì lượt chạy thật **không** thay được phép kiểm đó.

## 2. Năm vòng sửa — tất cả đều là lỗi của spec/plan, không phải của người thực thi

### 2.1 Literal lấy nhầm kỳ báo cáo *(Task 4)*

Plan chép `rtq44`/`rtq137`/`rqq41` từ `quarterly[0]` — **kỳ cũ nhất** — trong khi cùng một assert đòi `year == 2026, quarter == 2`. Người thực thi phát hiện mâu thuẫn nội tại, dump fixture để xác minh, sửa **expected** chứ không sửa code. Giá trị đúng: `0.02058553 / 0.0113022 / 0.10735799`.

### 2.2 Cột `organ_code` không tồn tại *(Task 6)*

Plan viết SQL join `market.corporate_event` qua `organ_code`. Bảng thật chỉ có `issuer_id`. **Nguồn của lỗi là tài liệu thiết kế**: `market-data-store.md` §5.6 vẫn chép lược đồ nháp từ trước khi migration `0004` ra đời. Đã đồng bộ tài liệu theo migration cùng ngày (`af3eeb1`) kèm luật: *lược đồ thật nằm ở migration; hai bên lệch thì migration đúng.*

### 2.3 `now()` đông cứng trong giao dịch *(Task 7)*

`now()` giữ nguyên giá trị suốt một giao dịch Postgres, nên hai lượt `apply()` trong cùng giao dịch test có cùng `checked_at`. Đổi sang `clock_timestamp()`, khớp tiền lệ `price_store.py` / `events_store.py`.

### 2.4 🔴 Hai đồng hồ bị trộn làm một *(phát hiện lớn nhất của lát)*

Lượt chạy thật đầu tiên ghi `watermark: '2026-09-22'` — **một ngày ở tương lai**. Kho có **20 sự kiện mang `exright_date` tương lai** trong khi `public_date` không bao giờ ở tương lai (0 dòng). Vì spec định nghĩa mốc nước là `max(greatest(public_date, exright_date))`, mốc nhảy tới 22/09 và **trigger sẽ chết ba tuần, im lặng**.

Gốc rễ là trộn hai câu hỏi khác nhau:

| Câu hỏi | Đo bằng | Dùng cho |
|---|---|---|
| Sự kiện nào **mới được công bố**? | `public_date` so với mốc nước | trigger fetch |
| Ngày không hưởng quyền nào **vừa đi qua**? | `exright_date` so với **hôm nay** | re-crawl giá |

`ingested_at` đã được cân nhắc và **loại**: `events_store` upsert kèm `DO UPDATE SET ingested_at = clock_timestamp()`, mà job events tải trọn 110.695 dòng mỗi lượt ⇒ cả bảng được làm mới mỗi ngày.

Mốc nước hỏng **tự lành** ở lượt success kế tiếp (`2026-09-22` → `2026-09-03`, quan sát ở run 89) vì `upsert_domain_state` ghi đè bằng giá trị mới.

**Không phát hiện nào trong 523 test bắt được lỗi này — chỉ có chạy thật mới thấy.**

### 2.5 Re-crawl thiếu trần thời gian và thiếu bộ lọc loại sự kiện

Hai hệ quả vận hành, cùng lộ ra khi chạy thật:

- **Không trần thời gian.** Mỗi mã re-crawl là một lượt backfill trọn ~12,5 năm. Phân bố ngày ex 8 tuần gần đây: 8 · 22 · 34 · 23 · **48** · 32 · 41 · 46 mã/tuần ⇒ mùa cổ tức chạm đúng trần `MAX_RECRAWL = 50`, job hằng ngày thành job hàng giờ. Thêm `RECRAWL_MAX_MINUTES = 20`; mã chưa kịp kéo không mất vì cửa sổ 3 ngày cho hai lượt sau bắt lại.
- **Thiếu bộ lọc loại sự kiện.** Cửa sổ ngày lấy **mọi** loại sự kiện có `exright_date`: 8 mã được chọn nhưng **6/10 sự kiện là `AGM`** — chốt quyền dự đại hội, không đụng hệ số điều chỉnh. Thêm `event_type IN ('CashDividend','StockDividend','ShareIssuance')` ⇒ 8 mã còn 2.

## 3. Hai lỗi trong plan mà bộ test lộ ra trước khi chạy thật

- **Test `due_list` không cách ly.** 9/20 test đỏ khi chạy chung cả bộ (xanh khi chạy riêng file): chúng assert trên kết quả `due_list` **toàn cục** trong khi CSDL test dùng chung và các test job khác commit issuer thật nằm lại vĩnh viễn. Sửa ở tầng test bằng helper dập nền + lọc theo mã của chính test. Cùng bệnh này còn tái phát ở `new_watermark` (xanh do trùng hợp dữ liệu) — sửa nốt.
- **Hai test guard-từ-chối bất khả thi.** Plan dựng chúng với 1 mã = 4 target, trong khi `MIN_SAMPLE = 20` khiến chốt chặn **không thể** kích hoạt ở cỡ mẫu đó. Sửa: seed 20 mã, giới hạn một kind.

## 3b. Review toàn nhánh — hai lỗi Critical mà 523 test không thấy

Review độc lập trên toàn nhánh (23 commit) bắt **2 Critical, 8 Important, 9 Minor**. Đã vá gộp một lượt (`b5cbf84` · `8ccbd92` · `08e36c0` · `826ac00`), **532 test xanh** (+9 test, mỗi test đỏ trước xanh sau).

### A1 — lượt con vẫn đẩy mốc nước toàn bảng *(Critical)*

`run()` ghi mốc nước bằng `max(public_date)` **toàn bảng** kể cả lượt `--codes`/`--kinds` chỉ phục vụ vài mã. Mọi sự kiện của ~1.520 issuer còn lại rơi xuống dưới mốc mới ⇒ **mất trigger vĩnh viễn**, chỉ còn lưới quét sàn 30/90 ngày bắt lại.

Luật chống chuyện này đã có trong spec nhưng chỉ soi đường `failed`, bỏ đường lượt con. Và **repo đã có tiền lệ đúng** ở `price_job.py` (`stats["subset"]`, chỉ `upsert_domain_state` khi không phải lượt con) — bản plan không nhân bản.

🔴 **Trớ trêu: chính lệnh AC5 (`--codes` tập mã hôm trước) là lệnh kích hoạt lỗi này.** Chạy AC5 trên code cũ là tự phá bằng chính phép nghiệm thu.

### A2 — nhánh trigger không trần *(Critical)*

Nhánh trigger chỉ lọc `public_date > watermark`, không quota, không đối chiếu sổ kiểm:

- **Cold start** (mốc `1900-01-01`): lấy **mọi issuer từng có** bốn loại sự kiện — gần trọn vũ trụ × nhiều kind. Nhánh quét sàn đã được bảo vệ khỏi đúng ca này bằng quota, nhánh trigger thì không. *(AC3 chỉ đo được 234 lời gọi vì mốc nước lúc đó tình cờ đang hỏng theo hướng ngược lại.)*
- **Vòng lặp tự khuếch đại**: một mã hỏng dai dẳng giữ mốc đứng yên ⇒ danh sách trigger phình mỗi ngày ⇒ càng dễ có mã hỏng ⇒ mốc càng không tiến.

Vá: bỏ qua nhánh trigger ở cold start (quét sàn phủ trọn trong 30/90 ngày) + trần `MAX_TRIGGER = 300`, lấy `public_date` cũ nhất trước.

### Bảy mục Important còn lại, đã vá

Mốc nước đọc hai lần nên có cửa sổ đua *(nay đọc trong cùng giao dịch với `due_list`)* · `--max-minutes` không phủ pha re-crawl *(nay pha fetch bị cắt thì bỏ luôn re-crawl)* · sáu test còn assert trên trạng thái **toàn cục** · thiếu test cho chính cơ chế chặn cold start *(N issuer chưa kiểm > quota ⇒ đúng quota)* · `valuation` thiếu đường trigger dù tập trắng của nó có `outstandingShare` · thứ tự `close_run`/`upsert_domain_state` ngược với họ job *(mốc nước lỗi làm mất sạch `stats` của lượt đã commit)* · chú thích `changed_at` mô tả trạng thái code không tạo ra được.

### Một hỏng mới do chính lượt vá gây ra — và cách nó bị bắt

Lượt vá cho `ShareIssuance` bắn thêm kind `valuation` là đúng yêu cầu, **nhưng `StockDividend` bị ghi đè chứ không phải cộng thêm**: nó mất hẳn kind `dividend`. Báo cáo của người vá mô tả là *"cộng thêm"* — **sai so với code thật**. Không test nào phủ ánh xạ này nên **531 test xanh vẫn không bắt được**; re-review có phạm vi hẹp đọc thẳng code mới thấy, và kiểm lại bằng `git show` của commit trước lượt vá mới xác nhận được.

Đã khôi phục thành `("snapshot", "valuation", "dividend")` — cổ tức bằng cổ phiếu làm đổi số CP lưu hành **và** là sự kiện cổ tức — kèm test phủ đúng ánh xạ ba kind.

**Bài học:** báo cáo của người thực thi là *lời khai*, không phải *bằng chứng*. Chỗ duy nhất bắt được ca này là đọc diff và đối chiếu với bản trước đó.

### Phát hiện có thật nhưng cố ý chưa sửa — kèm lý do và điều kiện xét lại

| Mục | Vì sao chưa sửa | Xét lại khi |
|---|---|---|
| Chốt (i) gộp bốn kind — vừa che được lỗi của kind nhỏ, vừa **tự nổ** khi `ownership` đảo đồng loạt theo kỳ công bố (70/234 = 29,9% > 20%) | Ngưỡng theo từng kind **không** phải lời giải hiển nhiên: nó làm ca `ownership` nổ **dễ hơn** | Có vài tháng số thật của `changed_floor`. Đã cảnh báo ở [backend/README](../../../../backend/README.md) để người trực không tưởng nguồn hỏng |
| `riskFreeRate` trong tập trắng `valuation` có thể jitter cùng họ với hai trường đã loại | Chưa có hai điểm thời gian để biết nó có nhích không | **AC5** là phép đo đầu tiên |
| Hash nhạy với **thứ tự phần tử** trong mảng (`ownership` là 4 mảng) | Chưa quan sát được nguồn đảo thứ tự | Thấy `changed_floor` cao bất thường mà nội dung không đổi |
| `_newest_period` rơi từ `quarterly` sang `yearly` khi mảng rỗng | Nguồn hiện chỉ để `quarterly` rỗng ở 1/9 mã | Nguồn bắt đầu điền `quarterly` cho phi ngân hàng ⇒ lật đồng loạt, mà 24/234 = 10% nên chốt (i) **không bắt** |
| Target hỏng giữ `checked_at` NULL nên luôn đứng đầu hàng đợi quét sàn | Hành vi đó cũng **đúng nghĩa** (chưa kiểm được thì phải thử lại); thiệt hại có trần là vài lời gọi/ngày | Số mã hỏng vĩnh viễn vượt vài chục |
| `open_run` ngoài try/except · import giữa file test · `KeyboardInterrupt` · `--kinds` không kiểm giá trị | Đều nhỏ, và sửa `open_run` riêng ở đây sẽ **phá tính đồng nhất của họ job** | Dọn cả họ job trong một lượt riêng |

## 4. Trạng thái bàn giao

| Mục | Giá trị |
|---|---|
| Test | **532 passed, 2 skipped** |
| Migration head | **`0016`** — `ops.snapshot_check` + domain `market.snapshot` |
| Module mới | `snapshot_fetch` · `snapshot_normalize` · `snapshot_guard` · `snapshot_store` · `snapshot_job` |
| Dữ liệu đã nạp | `snapshot_daily` **246 dòng**/2026-09-04 · `ops.snapshot_check` 246 dòng |
| Task Scheduler | **không đăng ký** — lịch thuộc lát 7, đúng phạm vi spec §3.2 |
| Còn nợ | **AC5** (2026-09-05) · một Minor: import nằm giữa file test *(do plan viết "thêm vào cuối file")* |
