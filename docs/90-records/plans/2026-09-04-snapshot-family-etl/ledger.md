# Sổ ghi thực thi — lát 4 `etl snapshot`

**Ngày:** 2026-09-04 · **Nhánh:** `feat/snapshot-family-etl` · [spec](spec.md) · [plan](plan.md) · [số đo nguồn](measurements.md)

Thực thi bằng subagent (Sonnet, chỉ định tường minh), review hai trục sau mỗi task, artifact điều phối để ở scratchpad ngoài repo.

---

## 1. Tiêu chí nghiệm thu

| | Nội dung | Kết quả |
|---|---|---|
| AC1 | Toàn bộ test xanh | ✅ **533 passed, 2 skipped** *(trước lát này: 456)* |
| AC2 | `--codes` 3 mã → 12 dòng, 4 kind | ✅ run 88 |
| AC3 | Lượt đầy đủ vào kho production | ✅ run 91 — **234 target, 234 lời gọi, 0 retry** |
| AC4 | Chạy lại cùng ngày | ✅ run 89 — `unchanged 12`, `rows_written 0` |
| **AC5** | **Chạy lại, `changed_floor = 0`** | 🟡 **Nửa dưới-ngày ĐẠT** · nửa qua-mốc-đóng-cửa **CÒN NỢ** — nguồn chưa nạp giá 04/09 tính tới 16:42; xem §1b và §1d |
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

### 1b. AC5 — vì sao nó KHÔNG cần chờ sang ngày mới

Bản spec viết AC5 là *"chạy lại ngày hôm sau"*. **Sai trọng tâm:** thứ phép thử cần không phải một ngày mới mà là **một giá đóng cửa mới**. Đo 2026-09-04 lúc 12:28 *(xem [measurements §4b](measurements.md))*: gọi lại A32 cho ra `rtd11` và hash **y hệt** lúc 09:57 — bốn endpoint làm mới theo phiên đóng cửa, không theo thời gian thực. Nên mốc là **sau 15:00 cùng ngày**, và sáng hôm sau lại còn là thứ 7, không có phiên nào.

**Nửa "trôi trong ngày" đã chạy, 12:31 — 292 lời gọi trên 73 mã × 4 kind:**

```
attempted 292 · first 46 · floor_compared 246 · changed_floor 3 · unchanged 243
subset: True · recrawl: ['RYG','TCH']
```

**Ba target đổi đều là kind `ownership`** (BVB · VLS · VVS). Truy tiếp: gọi lại ba mã đó **3 lần liên tiếp** cho ra hash giống hệt nhau ⇒ **không phải jitter theo từng response**, tức giả thuyết *"hash nhạy thứ tự phần tử mảng"* không đúng ở đây. Lượt thứ ba lúc 12:51 (73 mã, chỉ kind `ownership`) cho **`changed_floor = 0`**. Kết luận: ba thay đổi đó là **công bố thật một lần** trong khoảng 10:20–12:31.

🔴 **Và chúng chính là số đo "lỗ của lịch" đầu tiên.** `ownership` không có loại sự kiện nào bắn trigger — nếu không có quét sàn, ba công bố này lọt hoàn toàn. Đây là kiến trúc hai lớp làm đúng việc nó sinh ra để làm.

**Hai bản vá được nghiệm thu trên production trong cùng lượt:** mốc nước **đứng yên** ở `2026-09-03` với nguyên dấu thời gian `03:27:39` sau lượt `--codes` *(bản vá A1)*, và re-crawl chỉ còn **2 mã** thay vì 8 *(bộ lọc loại sự kiện)*.

### 1d. Vì sao merge trước khi AC5 xong — và AC5 còn nợ những gì

**Trạng thái đo tới 16:42 ngày 2026-09-04:** nguồn **chưa nạp** giá đóng cửa 04/09. Kiểm trên 4 mã **đã xác minh là có biến động giá hôm nay** (AAA 7.090→7.130 · AAM 7.600→7.480 · AAT 2.240→2.270 · ABB 17.200→17.100 theo `getPriceData`) — cả bốn vẫn mang giá 03/09, sau 1 giờ 42 phút kể từ lúc đóng phiên.

🔴 **Phép đo này hỏng hai lần vì chọn sai mã chuẩn — ghi lại vì rất dễ lặp:**

| Lần | Mã chuẩn | Vì sao vô nghĩa |
|---|---|---|
| 1 | A32 | mã UPCOM mỏng — không khớp lệnh thì giá đóng cửa không đổi |
| 2 | thêm ACB | thanh khoản cao **nhưng hôm nay đứng giá đúng 22.200 cả hai phiên** |

Cả hai lần đều cho ra *"nguồn chưa nạp"*, trong khi sự thật là *"giá không đổi nên không kết luận được gì"*. Chỉ khi đối chiếu `getPriceData` mới thấy 9/14 mã có biến động. **Bài học: mã chuẩn cho phép thử phải được CHỨNG MINH là có biến động, không phải được PHỎNG ĐOÁN là thanh khoản cao.**

**Một phát hiện phụ, có ích cho lát 7:** hai họ endpoint làm mới ở hai thời điểm khác nhau — `getPriceData` đã có phiên 04/09 từ trước 15:51, họ Snapshot thì chưa. Task `dlck-price` đặt 15:40 là hợp lý; job snapshot **không** đặt cùng khung đó được.

**Vì sao vẫn merge:** nếu danh sách trắng sai thì hỏng **rất to chứ không lặng lẽ**. Một trường bám giá lọt vào tập hash sẽ khiến toàn bộ nhóm quét sàn báo đổi ⇒ `changed_floor / floor_compared` ≈ 100% ⇒ chốt chặn (i) **từ chối cả lượt, exit 1, không ghi dòng nào**. Cộng thêm: nhánh **không đăng ký task nào** nên merge không khởi động gì, và 292 dòng đã nằm trong kho là do chính code này ghi.

**Cách đóng nốt, một lệnh:**

```bash
cd backend && uv run python -m etl snapshot --codes AAA,ABB,AAM,AAT
```

Đọc `stats`: `changed_floor = 0` là AC5 đạt. Khác 0 thì so hai dòng `snapshot_daily` liền nhau của mã đổi để tìm trường jitter, rồi **bỏ trường đó khỏi `KEEP`** — đúng điều kiện đảo ngược đã ghi ở [spec §4.3](spec.md), **không** phải nới ngưỡng guard. Lượt đó đồng thời trả lời câu còn bỏ ngỏ: nguồn nạp **cuối ngày** hay **qua đêm**.

*Kiểm lại 17:10 ngày 04/09 (phiên chuẩn bị lát 5): AAA `rtd11 ÷ outstandingShare` = 7.090 — vẫn giá 03/09. Nguồn chưa nạp sau 2 giờ 10 phút; AC5 tiếp tục treo, lệnh đóng không đổi. Chi tiết: [khảo sát BCTC §6.5](../../surveys/2026-09-04-bctc-endpoints/README.md).*

### 1c. Lỗi cùng họ với A1, lộ ra ở chính lượt kiểm trên

Ba lượt `--codes` liên tiếp đều kéo lại `['RYG','TCH']` — ba lần backfill trọn 12,5 năm cho hai mã **không nằm trong tập người chạy ép**. Lượt đầu đổi dữ liệu thật, hai lượt sau `rows_changed = 0`, thuần lãng phí.

Cùng bản chất với lỗi mốc nước: **lượt con là hành động thủ công phạm vi hẹp, không được gây tác dụng phụ toàn cục.** Vá: chỉ gọi `_recrawl` khi `not subset` (`4d193f5`), kèm test chứng minh lượt `--codes` không gọi `price_job` lần nào.

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
| Test | **533 passed, 2 skipped** |
| Migration head | **`0016`** — `ops.snapshot_check` + domain `market.snapshot` |
| Module mới | `snapshot_fetch` · `snapshot_normalize` · `snapshot_guard` · `snapshot_store` · `snapshot_job` |
| Dữ liệu đã nạp | `snapshot_daily` **246 dòng**/2026-09-04 · `ops.snapshot_check` 246 dòng |
| Task Scheduler | **không đăng ký** — lịch thuộc lát 7, đúng phạm vi spec §3.2 |
| Còn nợ | **AC5 nửa qua-mốc-đóng-cửa** — nguồn chưa nạp tính tới 16:42 ngày 04/09, đóng bằng một lệnh (§1d) · một Minor: import nằm giữa file test *(do plan viết "thêm vào cuối file")* |
