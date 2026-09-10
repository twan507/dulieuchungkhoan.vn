# Spec — lát 13: scheduler trong service `etl` + hoàn thiện toàn bộ kho (seed OMO FiinProX, nạp đầu, lịch chạy)

**Ngày:** 2026-09-09 · **Trạng thái:** 🟡 chờ chủ dự án duyệt · **Nhánh:** `feat/etl-scheduler`
**Điểm vào:** [roadmap §3 "Điểm vào cho lát 13"](../../../00-overview/roadmap.md) · **Hồ sơ tiền nhiệm:** [`2026-09-08-container-runtime/`](../2026-09-08-container-runtime/) (lát 12) · **Phương án đã sinh và chấm:** [`options/`](options/) (`criteria.md` viết trước, `option-P1/P2/P3.md` sinh độc lập bởi ba subagent Sonnet song song)

---

## 1. Vì sao lát này, và lát này là gì

Sau lát 12 mọi họ job chạy được trong container nhưng **không có gì chạy tự động** ngoài ingester: service `etl` là vỏ heartbeat, 11 task Windows đã gỡ, kho dev vừa dựng lại nên mỗi họ chỉ có một lượt hẹp. Chủ dự án chốt 2026-09-09: kho dev này **là kho thật**, không xoá dựng lại nữa, lên VPS mang nguyên dữ liệu; lát 13 vừa dựng scheduler vừa **hoàn thiện toàn bộ kho** để từ 10/09 mọi thứ ghi đồng bộ.

**Lát này là gì, một câu:** sau lát này, `docker compose up -d` là cả hệ tự chạy theo bảng lịch giờ VN trong code, chết lúc nào dựng lại cũng tự bù đúng, không hai lượt cùng job chồng nhau kể cả khi có người chạy tay; kho đã nạp đầy lịch sử (giá 12,5 năm, BCTC toàn sàn, snapshot trọn sàn, quốc tế, tin một tuần, OMO một năm từ FiinProX nối khít vào crawl SBV) và số dư OMO tính được từ ngày đầu.

Ba việc gộp trong một lát vì cùng một đích "kho chạy thật từ 10/09": (A) nạp đầu và seed OMO, chạy ngay trong ngày 09/09 bằng job sẵn có; (B) hai sửa nhỏ ở job đã có (bỏ quota snapshot, `classify_attempts`); (C) scheduler.

## 2. Dữ kiện đã kiểm vs giả định *(§4.8 bước 0)*

### 2.1 Đã kiểm — 2026-09-09, đọc code, đo file FiinProX, chạy thật một phần nạp đầu

| Dữ kiện | Nguồn |
|---|---|
| CLI `python -m etl <job>` cho 15 họ; không tham số = heartbeat 15 s. Mã thoát 0/1/2/130 có test hợp đồng (`test_e63`); SIGTERM → KeyboardInterrupt → đóng sổ "dừng tay", exit 130 (`core/shutdown.py`); `stop_grace_period` của `etl` 60 s | `etl/__main__.py`, `tests/etl/test_e63_exit_code_contract.py` |
| `ops.etl_run`: `run_id, job, started_at, finished_at, status ∈ {running,success,failed}, stats jsonb, error`. **Không có cột mã thoát**: exit 1 và exit 2 cùng `failed`, chỉ khác tiền tố chuỗi `error` | migration `0008` |
| Mọi nhánh trả 1 hiện có: 6 `except GuardRefused` (`events refdata screener price snapshot fundamentals`), `wichart_job:126`, `series_job:143` (5 nguồn quốc tế), `news_classify` `ModelDown` (2 chỗ) | grep 2026-09-09 |
| Lượt `--intraday` cùng tên job với lượt trọn (`stats.intraday=true`); lượt `--keys/--codes` có `stats.subset=true`; `--dry-run` có `stats.dry_run=true`; backfill giá ghi `stats.pass_complete` khi hết vòng | `series_job.py`, `price_job.py` |
| `open_run/close_run` ở `etl/omo_store.py` là **điểm nghẽn duy nhất** cả 15 họ đi qua để mở/đóng sổ | grep `open_run(` |
| `pg_try_advisory_lock(hashtext(:job))` chạy được trên Postgres 16 của kho (kiểm 08:40) | `psql` |
| Khuôn vòng lặp `daemon()` + `next_window()` của ingester, test literal `test_i16_daemon.py`; `core.clock.now_vn/today_vn`; `test_tz_contract` cấm giờ trần | code |
| Dockerfile tạo `/var/lib/dlck/{logs,measure,spill}` thuộc `appuser`; `test_d03` ghim đúng tập biến `environment` của `etl`; `pyproject` không có thư viện lịch | code |
| Snapshot: quota 24/70/70/70 là hằng số tự đặt ở spec lát 4 (`QUOTA` trong `snapshot_store.py`), không phải giới hạn API; lượt `--codes` bỏ quota; `plan_due` chọn cặp tới hạn theo `checked_at` rồi `LIMIT :quota` | `snapshot_store.py:84-160`, spec lát 4 §4.2 |
| Classify: bài lỗi giữ `classified_from NULL`, được chọn lại mãi; lỗi chỉ nằm ở `ops.llm_call`. Cột `ticker_step_ran` và `labels` đã phân biệt "không có mã" và "không xếp được nhóm" | `news_classify.py`, migration `0007`/`0018` |
| **FiinProX** file kết quả đấu thầu: 826 dòng, 248 ngày, 08/09/2025–07/09/2026, kỳ hạn 7/14/21/28/35/42/56/63/91/105; không có cột loại hình; file chuỗi ngày xác nhận tín phiếu = 0 cả năm; 03/02/2026 hai phiên cùng ngày cùng kỳ hạn 7/28/56; 22/08/2026 (thứ 7) ba dòng khối lượng 0; 03/11/2025 thứ hai không có phiên; 78/826 dòng khối lượng 0 | đo 2026-09-09 sáng |
| Phiên 14/08/2026 trong file **khớp từng số** với mẫu SBV ở `sbv-omo.md` §5. Phát hành theo ngày khớp 100 % cột chuỗi ngày của FiinPro; số dư lưu hành do công thức `omo_flow` tính từ file **bằng đúng** cột lưu hành FiinPro từ 19/12/2025 tới 07/09/2026, trừ hai chỗ chính cột FiinPro tự mâu thuẫn với cột phát hành/đáo hạn của họ (14/08 lệch 6.777,40 tự hoàn 17/08; 24/08–04/09 lệch 4.526,61, khớp lại 07/09). Lưu hành 07/09 = **250.778,26 tỷ** hai bên | đo 2026-09-09 sáng |
| Kho hiện có đúng một phiên OMO 08/09/2026 từ SBV (7 ngày 6.469,47 tỷ · 91 ngày 652,15 tỷ · 14 và 35 ngày 0). Đáo hạn 08/09 suy từ file 8.536,44 ⇒ lưu hành 08/09 kỳ vọng **249.363,44 tỷ** | `psql` + đo |
| Nạp đầu đã chạy sáng 09/09 (kết quả ở ledger): `yahoo --backfill` 54, `binance --backfill` 39, `wichart` 68, `fred` 14, `fx` 1, `lbma` 2 lời gọi đều `success`; `price --backfill` và `fundamentals --backfill` đang chạy song song; FiinTrade trả "Timeout expired" cho 3/4 mã đầu của backfill giá lúc 08:27–08:36 trong khi BCTC 1.200 lời gọi 0 retry | `ops.etl_run` |
| Ingester **đã dừng 07:59** theo yêu cầu chủ dự án; hôm nay không có tick | `docker compose ps` |

### 2.2 Giả định — CHƯA kiểm, kiểm trong plan

1. `SystemExit(1)` ném từ `open_run` (trước `try`) thoát sạch ở cả 15 họ mà không để dòng `running` treo — kiểm bằng test hợp đồng tham số hoá như `test_e63`.
2. Sáu tiến trình con Python đồng thời nằm trong ngân sách RAM VPS — chưa đo; đo RSS trong mấy ngày chạy thử.
3. `CREATE_NEW_PROCESS_GROUP` + `CTRL_BREAK_EVENT` dừng được con trên Windows native — chỉ ảnh hưởng dev, kiểm tay một lần.
4. Giờ WiChart nạp vĩ mô tháng trước 08:15 — đo trong mấy ngày chạy thử.

## 3. Phạm vi

### 3.1 Trong phạm vi

1. **Seed OMO từ FiinProX** (§5.1) + parser SBV gộp dòng cùng kỳ hạn (§5.2).
2. **Bỏ quota quét sàn snapshot** — tới nhịp thì quét trọn (§5.3).
3. **Classify**: cột `classify_attempts` (migration `0021`), bỏ qua bài quá 3 lần thử (§5.4).
4. **Nạp đầu hôm nay** bằng job sẵn có, kèm phép thử tải trong phiên (§5.5).
5. **Scheduler P3** trong `backend/etl/scheduler/` (§5.6–5.11), compose/env/test hợp đồng (§5.12).
6. Tài liệu sống (§8), khép roadmap bằng "Điểm vào cho lát 14".

### 3.2 Ngoài phạm vi — ba loại *(§1.4)*

| Mục | Loại | Lý do |
|---|---|---|
| Kênh báo động khi exit 2 (mail/Telegram), dọn dòng `running` mồ côi, job giám sát hợp đồng | **Đã có đường khác** | Lát 14; scheduler chừa một dòng trong bảng lịch |
| Lịch nghỉ lễ trong scheduler | **Loại có chủ đích** | Chủ dự án chốt: screener tự từ chối, OMO bỏ ngày trùng, ingester nối vô hại; ngày lễ đầu tiên người soi `stats.counts.priced` (roadmap §5) |
| Thư viện scheduler (APScheduler…) | **Loại có chủ đích** | §4.1: P2 bị loại |
| Lưu file xlsx FiinProX vào `staging.raw_payload` hay repo | **Loại có chủ đích** | Chủ dự án: không lưu; chỉ ghi nguồn ở `omo_session.note`; repo public, không commit dữ liệu sản phẩm trả tiền |
| Backfill tin sâu hơn một tuần; classify tồn đọng cũ | **Loại có chủ đích** | Chủ dự án: sitemap lùi một tuần; tồn đọng cũ đã xoá cùng kho cũ |
| Bật lại backfill giá định kỳ mỗi thứ 7 sau vòng đầu | **Loại có chủ đích** | Chủ dự án: một vòng rồi tắt, làm mới bằng re-crawl theo sự kiện quyền |
| Tick hôm 09/09 | **Đã kiểm — không có** | Ingester dừng theo yêu cầu, tick không backfill được |
| Cột `exit_code` trong `ops.etl_run` | **Loại có chủ đích** | Khoá jsonb `stats.guard_refused` đủ cho planner, không migration bảng sổ |

## 4. Quyết định

### 4.1 Hình dạng scheduler — P3 "supervisor không giữ trạng thái" *(§4.8; ba phương án độc lập, chấm theo `options/criteria.md` viết trước)*

| Tiêu chí | P1 tối giản | P2 APScheduler | P3 supervisor |
|---|---|---|---|
| a cùng code native/container, giờ VN | ✓✓ | ✓✓ | ✓✓ |
| b bảng lịch một màn hình | ✓✓ | ✓ | ✓✓ |
| c spawn con, log, mã thoát | ✓✓ | ✓✓ | ✓✓ |
| d chạy bù đúng 6 luật, suy từ sổ | ✓ RAM cho luật exit 1/2 | ✓ so chuỗi `error` | ✓✓ khoá jsonb, tính lại mỗi nhịp |
| e chặn chồng hai lớp, phủ lượt tay | ✓✓ | ~ thoát 0 trái hợp đồng | ✓ |
| f dừng sạch, chết dựng lại bù đúng | ✓ | ✓ | ✓✓ |
| g test literal, seam rõ | ✓✓ | ✓ | ✓✓ planner thuần |
| h bán kính hỏng, rollback | ✓✓ | ~ 15 file + thư viện | ✓ |
| i phụ thuộc mới | ✓✓ 0 | ✓ 1, dòng bảo trì | ✓✓ 0 |
| j ước lượng | ~260 dòng · 16 test · 10–14 h | ~850 · 44 · ~25 h | ~520 · 23 · 14–15 h |
| k trần tiến trình con | ✓ | ✓✓ | ✓✓ |

**Chọn P3 nguyên vẹn** (chủ dự án gật 2026-09-09 ~08:40). Loại **P1** vì luật "exit 1 không bù, exit 2 thử lại một lần" nằm trong RAM, mất khi scheduler khởi động lại — đúng chỗ lát này cần đúng. Loại **P2** vì hai cơ chế cùng quyết một việc (trigger thư viện + vòng poll bù) phải bóp `misfire_grace_time` để không đè nhau, thoát 0 khi khoá bận mở rộng nghĩa mã 0, phân biệt exit 1 bằng so chuỗi, đắt gấp đôi cho một thư viện đóng băng tính năng.

**Một chi tiết mượn từ P1, đã kiểm P3 còn đứng:** xử lý khoá bận. P3 gốc trả `None` rồi sửa 15 chỗ gọi; thay bằng `open_run` ghi một dòng `failed` (`stats.lock_busy=true, guard_refused=true`) rồi `raise SystemExit(1)` — không sửa file job nào. Planner thấy dòng `guard_refused` nên không thử lại mốc đó trong ngày (đúng nghĩa "đã có người chạy"); nếu không ghi dòng, scheduler sẽ spawn lại mỗi nhịp suốt lúc lượt tay đang chạy.

**Điều kiện đảo ngược:** đo RAM sáu tiến trình con vượt trần VPS ⇒ hạ hằng số trần, không đổi kiến trúc · cần scheduler chủ động giết job quá hạn ⇒ thêm watchdog ở runner · cần lịch động do người dùng đặt ⇒ lúc đó mới xét thư viện.

### 4.2 Quyết định chủ dự án 2026-09-09 (brainstorm sáng) — không mở lại

| # | Chốt |
|---|---|
| 1 | Kho dev là kho thật, **không xoá dựng lại nữa**; lên VPS mang nguyên dữ liệu |
| 2 | FiinProX được dùng; **không lưu xlsx**; nguồn ghi ở `note` |
| 3 | Nạp đầu mức (b): backfill mọi nguồn tới hôm nay, sitemap tin **lùi một tuần**, classify chạy dần; **kết phiên nạp ngày 09/09**, từ 10/09 đồng bộ |
| 4 | Hôm nay dừng ingester, chỉ nạp đầu; trong phiên thử `price` hằng ngày **song song** backfill, chấp nhận vượt mức tải đã đo |
| 5 | Từ mai (10/09): bật ingester, chạy tay các mốc theo bảng lịch; scheduler tiếp quản khi xong review (cách (b)) |
| 6 | Snapshot: ép trọn sàn hôm nay bằng `--codes`; sau đó **bỏ quota**, tới nhịp 30/90 ngày thì quét trọn |
| 7 | Khoá chạy chồng: **advisory lock Postgres** trong job lúc mở sổ |
| 8 | Sáu luật chạy bù (§5.8) |
| 9 | Log: mỗi job một file theo ngày trong volume mới, giữ 30 ngày |
| 10 | `news --loop` là tiến trình con sống dai; `classify` **8 mốc** 07:00–21:00 cách 2 giờ, trần 1.000 bài/mốc, thêm `classify_attempts` |
| 11 | `wichart` trọn 08:15 mọi ngày; backfill giá một vòng rồi tắt; exit 2 chỉ log + bảng tóm tắt sáng; không lịch nghỉ lễ |
| 12 | OMO giữ cách crawl SBV, thêm phòng thủ gộp dòng cùng kỳ hạn |

### 4.3 Điểm trợ lý tự chốt — ghi §9 để rà

1. Dòng `running` mồ côi sau kill cứng để nguyên làm dấu vết, dọn ở lát 14.
2. Nhịp vòng scheduler 20 giây; trần tiến trình con 6.
3. Job trọn và job `--intraday` cùng tên dùng chung khoá ⇒ không bao giờ chồng nhau; lượt `--intraday` lỡ vì khoá bận là chấp nhận được (nhịp kế bù tự nhiên).
4. Thư mục log container `/var/lib/dlck/etl-logs`, native `<repo>/../dlck-runtime/etl-logs`.
5. `heartbeat.py` và test của nó xoá (rác do chính thay đổi tạo ra).
6. Seed OMO đọc **CSV** bằng stdlib (chuyển từ xlsx bằng script dùng một lần ở scratchpad, lệnh ghi ledger), chạy native; không thêm `openpyxl` vào image.

## 5. Thiết kế

### 5.1 Seed OMO từ FiinProX — `etl omo --seed <csv>`

CSV sáu cột `session_date,tenor_days,participants,winners,volume_bn,rate` (một dòng một dòng gốc, chưa gộp). Job:

1. Đọc, chuẩn hoá: `volume_vnd = volume_bn × 1e9` (Decimal), `rate_pct = rate × 100`, thành viên int; **gộp** dòng cùng `(session_date, tenor_days)` (cộng khối lượng và thành viên, lãi suất phải bằng nhau, khác thì fail); mọi dòng `op_type = 'reverse_repo'` — job **từ chối cả lượt** nếu file có cột/nhãn loại hình khác, vì file này chỉ hợp lệ khi tín phiếu = 0 (đã kiểm bằng file chuỗi ngày).
2. Ghi theo đúng đường `omo_store.store` hiện có, từng phiên một giao dịch: `omo_session(session_date, crawled_at=<ngày trích xuất>, has_reverse_repo=true, has_repo=false, has_outright_sale=false, note='seed FiinProX export 2026-09-08')`; ngày đã có ⇒ bỏ qua (idempotent theo PK). Không ghi `staging.raw_payload`.
3. Sau cùng `omo_flow.rebuild`, mở/đóng sổ `ops.etl_run` job `macro.omo_seed`, `stats` = số phiên ghi, số bỏ qua, số dòng gộp, `min/max session_date`.
4. `--dry-run` in cùng stats + ba literal đối chứng: bốn dòng 14/08/2026, lưu hành 07/09 và 08/09 (§7 AC1).

`omo_flow` không đổi. Số dư trước 19/12/2025 thấp hơn thực (thiếu phần lưu hành trước 08/09/2025) và cờ `complete` theo luật cũ — chấp nhận, ghi tài liệu.

### 5.2 Parser SBV — phòng thủ hai phiên một ngày

`omo_parse.parse`: hai dòng cùng nhóm cùng kỳ hạn ⇒ **gộp** (cộng khối lượng, thành viên; lãi suất khác nhau ⇒ `ParseError`), `OmoResult` thêm `merged: int`; `omo_store.store` ghi `note='gộp N dòng cùng kỳ hạn'` khi `merged > 0`. Đối chiếu tổng nhóm giữ nguyên.

### 5.3 Snapshot — bỏ quota quét sàn

`snapshot_store.plan_due`: bỏ `LIMIT :quota` và hằng `QUOTA`; giữ `CADENCE_DAYS`, `NULLS FIRST`, nhánh trigger và `MAX_TRIGGER`. Hệ quả: sau lượt ép trọn hôm nay, đúng 30 ngày sau ba kind tháng cùng tới hạn ⇒ job ngày đó quét trọn (~4.600 lời gọi, 40–75 phút); 90 ngày sau đến `snapshot`. Hai test quota ở `test_e29` đổi thành test "mọi cặp tới hạn đều được trả, không cắt". README backend và `market-data-store §4.1b` sửa theo.

### 5.4 Classify — `classify_attempts` và 8 mốc

Migration `0021`: `ALTER TABLE news.article ADD COLUMN classify_attempts smallint NOT NULL DEFAULT 0`. `news_classify`: bài lỗi ⇒ `UPDATE … SET classify_attempts = classify_attempts + 1`; `_SELECT` thêm `AND a.classify_attempts < 3`; `stats.skipped_attempts` đếm bài bị bỏ qua. Trạng thái đọc được từ bảng: chưa xử lý (`classified_from NULL`, `attempts < 3`) · bỏ cuộc (`NULL`, `attempts ≥ 3`) · không xếp được nhóm (`labels` có `x…`) · không có mã (`ticker_step_ran` và không `article_ticker`).

### 5.5 Nạp đầu 09/09 — bằng job sẵn có, trước khi scheduler xong

| Thứ tự | Lệnh (`docker compose run --name dlck-fill-<x> etl python -m etl …`) | Trạng thái |
|---|---|---|
| 1 | `yahoo --backfill` · `binance --backfill` · `wichart` · `fred` · `fx` · `lbma` | ✅ xong 08:24–08:35, 6/6 success |
| 2 | `price --backfill` (không `--stop-before-open`, chạy xuyên phiên và qua đêm) | đang chạy từ 08:24 |
| 3 | `fundamentals --backfill` song song | đang chạy từ 08:24 |
| 4 | **Phép thử tải**: `price` hằng ngày trọn 1.523 mã lúc ~10:00 và ~13:30 trong lúc hai backfill đang chạy — ghi số lỗi "Timeout expired", retry, thời lượng, `rows_changed`; đọc dòng `market.price_daily` ngày 09/09 sau lượt 15:40 | chưa |
| 5 | Seed OMO (§5.1) sau khi code xong: `--dry-run` rồi thật, native | chưa |
| 6 | `snapshot --codes <1.523 mã niêm yết>` ép trọn sàn (có người đọc `stats.tally`) | chưa, sau khi backfill BCTC xong để không ba luồng FiinTrade |
| 7 | `news --backfill-sitemap --source {tinnhanhck,bnews,nguoiquansat} --from 2026-09` | chưa |
| 8 | Sau 15:05: `screener`, `price`, `events`, `snapshot`, `fundamentals`, `omo`; tối: `classify --limit 1000` lặp tới hết | chưa |

Mọi lượt ghi vào ledger kèm `run_id`, mã thoát, số đo.

### 5.6 Scheduler — kiến trúc (P3)

```
backend/etl/scheduler/
  schedule.py   dữ liệu thuần: JobSpec, SCHEDULE, MAX_CONCURRENT_CHILDREN = 6
  planner.py    due(schedule, now_vn, ledger_rows) -> list[Task]   THUẦN, 0 I/O
  runner.py     Runner: spawn/poll/kill con, log theo ngày, dọn log 30 ngày, trần, chặn spawn trùng
  loop.py       main(): mỗi 20 s: now → SELECT sổ hôm nay → planner.due → runner.reconcile; SIGTERM → cờ → tắt con ≤ 60 s
```

`etl/__main__.py` nhánh không tham số gọi `scheduler.loop.main()`; `command` compose không đổi. Hợp đồng: `LedgerRow(job, started_at, finished_at, status, stats, error)`; `Task(spec, reason)`; runner nhận `spawn_fn`/`clock`/`sleep` tiêm được.

### 5.7 Bảng lịch (`schedule.py`), giờ VN

```python
@dataclass(frozen=True)
class JobSpec:
    name: str                       # tên trong ops.etl_run
    cmd: tuple[str, ...]            # sau `python -m etl`
    kind: str                       # daily | intraday | daemon | weekly_once
    times: tuple[tuple[int, int], ...] = ()
    weekdays: tuple[int, ...] = MON_FRI
    depends_on: str | None = None
    interval_s: int | None = None
    once_until_flag: str | None = None

SCHEDULE = [
  JobSpec("market.refdata",      ("refdata",),      "daily", times=((8, 0),)),
  JobSpec("market.screener",     ("screener",),     "daily", times=((15, 20),)),
  JobSpec("market.price_daily",  ("price",),        "daily", times=((15, 40),)),
  JobSpec("market.events",       ("events",),       "daily", times=((18, 10),)),
  JobSpec("market.snapshot",     ("snapshot",),     "daily", depends_on="market.events"),
  JobSpec("market.fundamentals", ("fundamentals",), "daily", depends_on="market.snapshot"),
  JobSpec("macro.omo_crawl", ("omo",), "daily", weekdays=ALL_DAYS, times=((11,30),(15,30),(18,0),(21,30))),
  JobSpec("macro.wichart",  ("wichart",), "daily", weekdays=ALL_DAYS, times=((8, 15),)),
  JobSpec("global.yahoo",   ("yahoo",),   "daily", weekdays=ALL_DAYS, times=((11, 0),)),
  JobSpec("global.binance", ("binance",), "daily", weekdays=ALL_DAYS, times=((7, 15),)),
  JobSpec("global.fred",    ("fred",),    "daily", weekdays=ALL_DAYS, times=((5, 0), (20, 0))),
  JobSpec("global.ecb",     ("fx",),      "daily", weekdays=ALL_DAYS, times=((22, 30),)),
  JobSpec("global.lbma",    ("lbma",),    "daily", weekdays=ALL_DAYS, times=((22, 30),)),
  JobSpec("global.yahoo",   ("yahoo", "--intraday"),   "intraday", interval_s=600),
  JobSpec("global.binance", ("binance", "--intraday"), "intraday", interval_s=300),
  JobSpec("macro.wichart",  ("wichart", "--intraday"), "intraday", interval_s=300),
  JobSpec("news.classify", ("classify", "--limit", "1000"), "daily", weekdays=ALL_DAYS,
          times=((7,0),(9,0),(11,0),(13,0),(15,0),(17,0),(19,0),(21,0))),
  JobSpec("news.collect", ("news", "--loop"), "daemon"),
  JobSpec("market.price_backfill", ("price", "--backfill", "--stop-before-open"), "weekly_once",
          weekdays=(5,), times=((0, 5),), once_until_flag="pass_complete"),
  # lát 14: một dòng JobSpec giám sát tại đây
]
```

### 5.8 Planner — `due()` và sáu luật chạy bù

`loop.py` đọc sổ hôm nay (giờ VN, biên ngày tính ở Python rồi truyền UTC):

```sql
SELECT job, started_at, finished_at, status, stats, error
FROM ops.etl_run
WHERE started_at >= :day_start_utc AND started_at < :day_end_utc
  AND job = ANY(:job_names)
  AND coalesce(stats->>'intraday','false') <> 'true'
  AND coalesce(stats->>'subset','false')   <> 'true'
  AND coalesce(stats->>'dry_run','false')  <> 'true'
ORDER BY job, started_at
```

`due()` thuần, theo `kind`:

- **daily có `times`**: với mốc `m` gần nhất đã qua hôm nay và `weekday ∈ weekdays`: due nếu chưa có `success` với `started_at ≥ m` (luật 1, 4 — OMO bốn mốc chung tên tự đúng).
- **daily có `depends_on`**: due nếu cha có `success` hôm nay và chính nó chưa `success` hôm nay (thứ tự events → snapshot → fundamentals).
- **weekly_once**: due nếu đúng thứ, qua mốc, chưa `success` hôm nay; **tắt vĩnh viễn** khi tồn tại bất kỳ `success` nào có `stats.pass_complete=true` (luật 6).
- **intraday, daemon**: planner bỏ qua (luật 3); runner tự chạy theo `interval_s` bằng đồng hồ của nó; daemon giữ sống.
- **exit 1 / exit 2** (luật 5): trong các dòng `failed` có `started_at ≥ m`: có dòng `stats.guard_refused=true` ⇒ không due; không có, đúng 1 dòng và `now ≥ started_at + 10 phút` ⇒ due (thử lại một lần); ≥ 2 dòng ⇒ thôi.
- Chỉ mốc **hôm nay** (luật 2): sổ đọc theo biên ngày VN.

`Task.reason` ghi nhánh sinh ra ("mốc 15:40", "bù mốc 08:00", "thử lại sau exit 2 lúc 15:41", "chuỗi: cha success").

**Khoá `stats.guard_refused=true`**: đặt ở **mọi** nhánh trả 1: 6 `except GuardRefused`, `wichart_job`/`series_job` nhánh `verdict` từ chối, `news_classify` `ModelDown`, và nhánh khoá bận ở `open_run` (§5.9). Test hợp đồng tham số hoá kiểu `test_e63` canh: mọi họ khi trả 1 phải có `stats.guard_refused=true` trong dòng `failed` của lượt đó.

### 5.9 Chặn chạy chồng — hai lớp

**Lớp trong** (`omo_store.open_run`, điểm nghẽn chung 15 họ): mở một connection **riêng, sống suốt đời job**, `SELECT pg_try_advisory_lock(hashtext(:job))`; được ⇒ `INSERT ops.etl_run` như cũ, giữ connection trong `_lock_conns[run_id]`; `close_run` đóng connection đó (phiên đóng = khoá tự nhả, kể cả bị giết cứng). Bận ⇒ `INSERT ops.etl_run (job, status='failed', finished_at=now(), error='lock busy: lượt khác đang chạy', stats='{"lock_busy":true,"guard_refused":true}')`, log một dòng, `raise SystemExit(1)` — ném trước `try` của mọi job, không sửa file job nào, exit 1 đúng hợp đồng "dữ liệu lành, không cần người".

**Lớp ngoài** (`runner`): dict `Popen` theo `spec.name`; con cùng tên còn sống ⇒ không spawn, log một dòng. Bản trọn và `--intraday` cùng tên ⇒ tự không chồng.

### 5.10 Runner — spawn, log, dừng, trần

- Spawn `[sys.executable, "-m", "etl", *cmd]`, `env=os.environ`, `cwd=backend`; POSIX `start_new_session=True`; Windows `CREATE_NEW_PROCESS_GROUP`.
- stdout+stderr → `ETL_LOG_DIR/<name>-YYYYMMDD.log` (mở `a`); `prune_old_logs` xoá file `mtime` > 30 ngày mỗi nhịp; sau khi con thoát in một dòng stdout `<job> mã <rc> sau <s>s (<reason>)`.
- **Tóm tắt sáng**: lúc 06:00 mỗi ngày in ra stdout bảng đếm 24 giờ qua theo job: success / exit 1 / exit 2 / 130, và dòng "news --loop đang sống từ HH:MM".
- Dừng: `loop.py` cài handler SIGTERM/SIGINT **đặt cờ** (không dùng `core.shutdown` vì cần đóng từng con có trật tự); cờ bật ⇒ mỗi con sống: POSIX `terminate()` (SIGTERM → con đóng sổ 130), Windows `CTRL_BREAK_EVENT`; chờ tối đa 60 s, còn sống ⇒ `kill()`; thoát 0.
- Trần `MAX_CONCURRENT_CHILDREN = 6`: daemon luôn được đảm bảo trước; task dư không spawn nhịp này, nhịp sau `due()` tính lại.
- Intraday: runner giữ `last_spawn[name]` (RAM, vô hại) và spawn khi đủ `interval_s`, nhưng chỉ khi không có con cùng tên sống.

### 5.11 `news --loop` — daemon con

Runner spawn nếu chưa có hoặc đã chết; giãn cách khởi động lại 30 s nhân đôi tới 300 s khi chết lại trong 5 phút, reset khi sống quá 5 phút. Mỗi vòng bên trong `news --loop` tự mở/đóng một dòng `news.collect` như hiện tại; khoá advisory theo `news.collect` chặn hai tiến trình loop.

### 5.12 Compose / env / test hợp đồng

- `docker-compose.yml`: service `etl` thêm `ETL_LOG_DIR: /var/lib/dlck/etl-logs` vào `environment` (cùng khuôn `CLICKHOUSE_BACKUP_DIR`), volume `etl_logs:/var/lib/dlck/etl-logs`, khai `etl_logs:` gốc; `command` giữ nguyên; sửa comment.
- `deploy/backend.Dockerfile`: thêm `/var/lib/dlck/etl-logs` vào `mkdir`/`chown`.
- `core/env.py` `OPTIONAL_KEYS` thêm `ETL_LOG_DIR`; `.env.example` thêm `# ETL_LOG_DIR=`; native mặc định `REPO_ROOT.parent/dlck-runtime/etl-logs`.
- `tests/docs/test_d03_compose_contract.py`: `ETL_OVERRIDES` thêm biến; test volume `etl_logs`; test Dockerfile thêm thư mục.
- Xoá `etl/heartbeat.py`, `tests/test_heartbeat.py`.

## 6. Seam test *(expected là literal, không tính lại theo code)*

| Seam | Test đỏ trước | Case biên/sai |
|---|---|---|
| `scheduler.planner.due` | 12 ca literal (ngày thật tuần 2026-09-07…13): mốc qua chưa chạy ⇒ due; đã success ⇒ không; OMO success 11:35, now 15:31 ⇒ due mốc 15:30; success 15:31, now 15:35 ⇒ không; snapshot chờ events; snapshot due ngay sau events success 18:12; exit 2 lúc 15:41: now 15:49 không, 15:52 due; hai lần failed ⇒ thôi; `guard_refused` ⇒ không; thứ 7 `pass_complete` ⇒ không; thứ 7 00:05 sổ rỗng ⇒ due; intraday/daemon không bao giờ xuất hiện | now đúng 15:40:00 ⇒ due (biên ≥); chủ nhật job MON_FRI không due |
| `planner.day_bounds_utc` | now 2026-09-10 00:30 VN ⇒ (2026-09-09T17:00Z, 2026-09-10T17:00Z) | — |
| `omo_store.open_run` (DB thật) | khoá trống ⇒ run_id, dòng `running`; khoá bị connection khác giữ ⇒ `SystemExit` code 1 và một dòng `failed` với `stats.lock_busy=true, guard_refused=true`; `close_run` xong ⇒ khoá lấy lại được từ connection mới | job crash không gọi `close_run` nhưng engine dispose ⇒ khoá nhả |
| Hợp đồng exit 1 ⇒ `guard_refused` (tham số hoá 15 họ, khuôn `test_e63`) | ép guard từ chối ⇒ rc 1 và dòng failed có `stats.guard_refused=true` | `test_e63` (exit 2) không có cờ |
| `runner.Runner` (spawn giả) | không spawn trùng khi con sống; spawn lại khi chết; file log `<name>-YYYYMMDD.log`; trần 6 chặn con thứ 7; shutdown gọi kill sau 60 s giả lập; daemon backoff `[30, 60, 120]` | con treo `poll()` None mãi |
| CLI | `main([])` gọi `scheduler.loop.main` | `main(["omo","--seed",…])` chuyển đúng đường |
| Seed OMO (`omo_seed`, DB thật) | CSV 8 dòng mẫu gồm 03/02 hai dòng kỳ hạn 7 ⇒ một dòng `omo_auction` khối lượng tổng, `note` gộp; chạy lại ⇒ 0 phiên mới; lãi suất khác nhau cùng kỳ hạn ⇒ fail; cột lạ ⇒ fail | dòng khối lượng 0 vẫn ghi |
| `omo_parse` gộp | HTML hai dòng "Kỳ hạn 7 ngày" cùng nhóm ⇒ một `OmoRow`, `merged=1`, tổng nhóm vẫn khớp | lãi suất khác ⇒ `ParseError` |
| `snapshot_store.plan_due` không quota | 5 cặp tới hạn ⇒ trả đủ 5 (bản cũ cắt 2) | cặp chưa tới hạn không trả |
| `news_classify` attempts (DB thật) | bài lỗi ⇒ `classify_attempts` 0→1; bài `attempts=3` không được chọn; `stats.skipped_attempts` | bài `attempts=2` vẫn chọn |
| Hợp đồng compose/Dockerfile/env | `ETL_LOG_DIR` trong `ETL_OVERRIDES`; volume `etl_logs`; Dockerfile có thư mục; `.env.example` có khoá và có người đọc | — |

## 7. Tiêu chí nghiệm thu *(chạy thật, dán output vào ledger; hỏng thì báo nguyên trạng)*

| # | Tiêu chí | Cách kiểm |
|---|---|---|
| AC1 | Seed OMO: 248 phiên vào kho, nối phiên 08/09; bốn dòng 14/08/2026 = 6.307,47 · 3.466,54 · 210,17 · 909,92 tỷ; `omo_flow.outstanding_vnd` 07/09 = **250.778,26 tỷ**, 08/09 = **249.363,44 tỷ**; chạy lại ⇒ 0 phiên mới | `--dry-run` rồi thật; `psql` |
| AC2 | Nạp đầu 09/09: backfill giá `pass_complete`, BCTC `remaining = 0`, snapshot trọn sàn (`ops.snapshot_check` ≈ 6.092), sitemap ba nguồn tháng 9, quốc tế 6/6, các job ngày 09/09 success sau phiên | `ops.etl_run` |
| AC3 | Phép thử tải trong phiên: hai lượt `price` trọn song song hai backfill — báo số lỗi nguồn, retry, thời lượng, kết luận "mức X an toàn / không" (§4.3 CLAUDE.md) | log + `stats` |
| AC4 | Scheduler chạy native (`uv run python -m etl`) và container; đủ mốc trong 24 giờ đầu: mỗi job `daily` có ≥ 1 `success` đúng sau mốc; intraday đúng nhịp; `news --loop` sống liên tục | sổ + log |
| AC5 | Chạy bù: `docker compose stop etl` qua một mốc rồi `start` ⇒ mốc lỡ được bù trong ≤ 40 s, thứ tự events → snapshot → fundamentals đúng; `restart` giữa job dài ⇒ job đóng sổ 130, bù đúng luật | thao tác thật, sổ |
| AC6 | Chặn chồng: chạy tay `docker compose run etl python -m etl price` trùng mốc 15:40 ⇒ một lượt thật, một dòng `failed lock_busy`, exit 1; không dòng `running` treo | sổ |
| AC7 | Dừng sạch: `docker compose stop etl` khi có con chạy ⇒ con đóng sổ "dừng tay" 130 trong ≤ 60 s, scheduler thoát 0 | log |
| AC8 | Cả bộ test xanh, `[DEBUG-` 0; số test do `database/README.md` sở hữu | pytest |
| AC9 | Chạy thử ≥ 3 ngày dev (10–12/09): 0 exit 2 không giải thích, 0 chạy chồng, bảng tóm tắt sáng có đủ job; giờ nạp WiChart vĩ mô đo được | log, sổ |
| AC10 | Ingester phiên thật đầu tiên trong container **10/09**: log giành leader, reconcile cuối phiên, số dòng `rt.trade`/`rt.quote` ngày 10/09 > 0 — phép kiểm ☐ của roadmap dời sang 10/09 | log, ClickHouse |

## 8. Checklist tài liệu sống — cùng lượt với code *(§1.6, §1.7)*

- `backend/README.md`: mục scheduler (bảng lịch, chạy bù, khoá, log, mã thoát 1 khi khoá bận, tóm tắt sáng), `etl omo --seed`, snapshot không quota, `classify_attempts`, bỏ câu "chưa đăng ký task Scheduler" ở mọi job.
- `docs/10-sources/macro/sbv-omo.md`: Giới hạn 2 và §8 điều kiện 140 ngày hết đúng khi có seed; kỳ hạn 42/105; hai phiên một ngày; trạng thái pháp lý FiinProX một dòng.
- `docs/20-design/service-topology.md` §2/§5/§6: `etl` = scheduler + volume `etl_logs`; `docs/20-design/market-data-store.md` §4.1b: quét sàn theo nhịp, không quota.
- `database/README.md`: migration `0021`, số test.
- `docs/00-overview/roadmap.md`: [4d] cập nhật (từ 10/09 mọi thứ chạy; ingester bật lại 10/09; kho dev là kho thật); đóng lát 13, viết "Điểm vào cho lát 14".
- `docs/90-records/README.md`: dòng hồ sơ này. `.env.example`: `ETL_LOG_DIR`.
- `git grep`: `heartbeat` · `QUOTA` · `quota` (snapshot) · `chưa đăng ký task` — hit còn lại phải thuộc vùng lịch sử.

## Đính chính khi viết plan — 2026-09-09 *(không sửa phần trên: đó là bản duyệt)*

**§5.8 "test hợp đồng tham số hoá kiểu `test_e63`" đổi thành quét tĩnh.** Ép từng họ tới nhánh guard từ chối cần fake fetch riêng cho mỗi họ (15 kịch bản), trong khi thứ cần canh chỉ là *"mọi `return 1` phải đi qua một hàm đóng sổ duy nhất đặt cờ"*. Plan Task 5 gộp cờ vào hàm mới `omo_store.close_run_refused` và canh bằng quét tĩnh `test_e68` (cùng tinh thần `test_e65` vế 2), cộng test DB thật cho chính hàm đó. Hệ quả: `stats.guard_refused` là chủ của một hàm, không rải ở 10 chỗ.

**§5.9 khoá bận** — dòng `failed` ghi trên chính connection giữ khoá (AUTOCOMMIT) trước khi đóng, để không cần connection thứ hai.

**§5.8 giả định "mọi lần thoát đều có dòng sổ" là SAI** *(2026-09-09 chiều, sau lượt chạy thử native)*. Job chết **trước** khi kịp `open_run` — ví dụ `news.classify` gặp kho chưa áp migration `0021` — không để lại dòng nào trong `ops.etl_run`, nên planner thấy mốc vẫn chưa chạy và cấp lại **mỗi nhịp**: đo được ba lần spawn liên tiếp lúc 17:36:04 · 17:36:44 · 17:37:24. Đã thêm ở runner một **hạ nhiệt 10 phút** (RAM) cho mỗi tên job vừa có con thoát mã ≠ 0; daemon giữ backoff riêng.

**§5.10 "prune xoá file `mtime` > 30 ngày" đổi thành theo NGÀY TRONG TÊN FILE** *(2026-09-09 chiều)*. Log mang tên `<job>-YYYYMMDD.log`; một file của ngày cũ vẫn có thể được ghi thêm, và `mtime` bị mọi thao tác chép/khôi phục làm mới. Ngày trong tên là thứ bất biến, nên `prune_old_logs` đọc nó.

**§5.10 thiếu một vế trên Windows: con phải bắt `SIGBREAK`** *(đo 2026-09-09 bằng cặp script cha/con ở scratchpad)*. Runner dừng con bằng `CTRL_BREAK_EVENT`; Python ánh xạ tín hiệu đó sang `SIGBREAK` chứ không sang `SIGINT`, nên con chỉ cài handler `SIGINT` chết với mã `0xC000013A`, không đi qua `except KeyboardInterrupt`, và để lại dòng `running` treo. Đã cho `core.shutdown.install_signal_handlers` và vòng lặp scheduler cùng ánh xạ `SIGBREAK` về đường Ctrl+C khi nền tảng có thuộc tính đó; Linux không đổi gì.

**§5.10 dòng con thoát in đúng dạng `[<ts>] <job> rc=<rc> <s>s (<lý do>)`** *(2026-09-09, review toàn nhánh)* — bản trước ghi `<job> mã <rc> sau <s>s`, không phải chuỗi `runner.py` thật in ra; `backend/README.md` đã sửa theo để grep được.

**§2.1 / §5.12 `stop_grace_period` của `etl` = 60 s → 90 s (đính chính 2026-09-09 tối, review toàn nhánh I2, phán quyết R27).** `SHUTDOWN_GRACE_S = 60` của runner bằng đúng thời hạn `docker compose stop` ⇒ con nào cần ~59 s để đóng sổ sẽ bị SIGKILL cùng PID 1, sinh dòng `running` mồ côi. Compose nâng lên 90s (cùng ingester), runner giữ 60 s; `test_d03` ghim 90s.

**§5.7 dòng `market.price_backfill` đổi từ `weekly_once` (thứ 7 00:05, `--stop-before-open`) sang `daemon` 24/7 tới `pass_complete`, và backfill không bao giờ bỏ dở vòng** *(chủ dự án chốt 2026-09-10 sáng, phán quyết R29)*. Đo 09/09–10/09: `getPriceData` trả HTTP 200 kèm thân `status: Failed, "Timeout expired…"` cho **~4–9 mã mỗi giờ, ở mọi giờ**, dù chạy một luồng hay ba — nghẽn là **nền** của nguồn, không phải sự cố ngắn nên không có "giờ đẹp" để hẹn lịch. Bản cũ (`SOURCE_DOWN_PAUSE_S = 600`, bỏ cuộc sau 3 lần nghỉ) nghỉ lúc 23:09 · 01:18 · 01:31 · 01:50 rồi chết **02:02 với exit 2 sau 194 mã** (con trỏ `CK8`), và không ai bật lại. Nay: thang nghỉ **10 → 20 → 40 → 60 → 60 …** phút theo số lần nghỉ liên tiếp, về lại 10 phút ngay khi một mã tải được; sau mỗi lần nghỉ chỉ thăm dò **một mã** nên mỗi quãng nghỉ tốn ≤ 4 lời gọi; **không còn nhánh bỏ cuộc**. Hệ quả ở scheduler: `loop.run_once` đọc `once_done` **trước** bước daemon, nếu không nhịp ngay sau khi backfill thoát 0 với `pass_complete` sẽ bật lại đúng cái vừa xong. Cờ `--stop-before-open` giữ nguyên cho lượt chạy tay.

## 9. Điểm cần chủ dự án duyệt tường minh

1. Sáu điểm tự chốt §4.3 — đặc biệt (1) dòng `running` mồ côi để lát 14, (6) seed đọc CSV chuyển từ xlsx, không thêm `openpyxl`.
2. Khoá bận ghi một dòng `failed lock_busy` vào sổ (mượn P1) thay vì im lặng.
3. Thứ tự nạp đầu §5.5, nhất là snapshot ép trọn sàn **sau** khi backfill BCTC xong.
4. AC9 "ba ngày chạy thử" là ngưỡng khép lát; AC10 dời phép kiểm ingester sang 10/09.
