# Sổ ghi thực thi — lát 4 `etl snapshot`

**Ngày:** 2026-09-04 · **Nhánh:** `feat/snapshot-family-etl` · [spec](spec.md) · [plan](plan.md) · [số đo nguồn](measurements.md)

Thực thi bằng subagent (Sonnet, chỉ định tường minh), review hai trục sau mỗi task, artifact điều phối để ở scratchpad ngoài repo.

---

## 1. Tiêu chí nghiệm thu

| | Nội dung | Kết quả |
|---|---|---|
| AC1 | Toàn bộ test xanh | ✅ **523 passed, 2 skipped** *(trước lát này: 456)* |
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

## 4. Trạng thái bàn giao

| Mục | Giá trị |
|---|---|
| Test | **523 passed, 2 skipped** |
| Migration head | **`0016`** — `ops.snapshot_check` + domain `market.snapshot` |
| Module mới | `snapshot_fetch` · `snapshot_normalize` · `snapshot_guard` · `snapshot_store` · `snapshot_job` |
| Dữ liệu đã nạp | `snapshot_daily` **246 dòng**/2026-09-04 · `ops.snapshot_check` 246 dòng |
| Task Scheduler | **không đăng ký** — lịch thuộc lát 7, đúng phạm vi spec §3.2 |
| Còn nợ | **AC5** (2026-09-05) · một Minor: import nằm giữa file test *(do plan viết "thêm vào cuối file")* |
