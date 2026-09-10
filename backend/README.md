# backend — API · ETL · Ingester

**Stack đã chốt:** Python + FastAPI *(2026-08-24, [ADR 0007](../docs/00-overview/decisions/0007-monorepo-layout-and-stack.md))*. Ba khối chạy như process riêng nhưng dùng chung models/clients trong package này:

| Khối | Vai trò |
|---|---|
| `api` | REST + SSE + chatbot function calling |
| `etl` | Thu thập theo lịch từ 9 nguồn — xem [`docs/10-sources/`](../docs/10-sources/README.md) |
| `ingester` | Realtime BVSC, tick thô + sổ lệnh + nến 1', ghi batch vào ClickHouse |

**Đang có:** [`agent/skills/`](agent/skills/) — hai skill sản phẩm `vn-stock-advisor` · `vn-stock-knowledge` (3.046 dòng, đã test 6 vòng). ⚠️ **Trước khi sửa bất cứ gì trong đó, bắt buộc đọc [`docs/30-skills/maintenance.md`](../docs/30-skills/maintenance.md).** `agent/` nay đã chứa system prompt, vòng chat REPL và glue function-calling (lát 10, 2026-09-07 — xem mục "Chạy vòng chat" dưới).

**Trạng thái phần code** *(2026-09-06 — năm job REST `screener` · `events` · `price` · `snapshot` · `fundamentals` từ 2026-09-04, job `etl wichart` (vĩ mô · tiền tệ · hàng hoá WiChart → `macro.observation` + `asset.price_daily`, [hồ sơ](../docs/90-records/plans/2026-09-05-wichart-macro-etl/)), **năm job quốc tế** `etl fred` · `fx` · `lbma` · `yahoo` · `binance` từ 2026-09-05 chiều ([hồ sơ lát 7](../docs/90-records/plans/2026-09-05-global-etl/)), và job **`etl news`** (47 feed RSS + 6 nguồn crawl HTML → `news.*`, không AI, dedupe URL + tiêu đề 48 giờ, gắn mã tầng 1–2, `--loop`, `--backfill-sitemap` TinnhanhCK) từ 2026-09-06 ([hồ sơ lát 8](../docs/90-records/plans/2026-09-05-news-collect/)), và job **`etl classify`** (lưới AI MiniMax M3 qua `core/llm`: 21 sub + `summary_ai` + mã tầng 3 + gắn 24 ngành, có trần bắt buộc, `ops.llm_call`) từ 2026-09-06 chiều ([hồ sơ lát 9a](../docs/90-records/plans/2026-09-06-news-classify-llm/)), mỗi job một mục dưới)*: `ingester` (socket BVSC → Redis + ClickHouse) · job `etl omo` (crawl OMO của SBV → Postgres) · job `etl refdata` (danh bạ + danh mục mã + cây ICB → Postgres, [hồ sơ](../docs/90-records/plans/2026-08-26-reference-data-etl/)) · job `etl screener` (52 trang `GetScreenerItems` → `market.screener_daily`, [hồ sơ](../docs/90-records/plans/2026-09-03-screener-daily-etl/)) · job `etl events` (sáu họ `Calendar/GetCorporate*` → `market.corporate_event`, [hồ sơ](../docs/90-records/plans/2026-09-03-events-daily-etl/)) · job `etl price` (`getPriceData` trang 1 mọi cổ phiếu niêm yết + backfill có con trỏ → `market.price_daily`, [hồ sơ](../docs/90-records/plans/2026-09-03-price-daily-etl/)). Hồ sơ lát ingester/OMO: [`docs/90-records/plans/2026-08-26-ingester-omo-first-slice/`](../docs/90-records/plans/2026-08-26-ingester-omo-first-slice/). `api` chưa bắt đầu.

**`etl/data/`** — dữ liệu tra cứu máy đọc mà job cần lúc chạy: `field-dictionary.json` (729 mã BCTC, `fundamentals`), `feeds.json` (47 feed + 8 crawl + taxonomy, `news`/`classify`), `market-field-selection.json` (chọn trường, `screener`); bảng đo WiChart ở `etl/wichart_source.py`. Dời từ `docs/` vào code 2026-09-08 (lát 12): code không đọc `docs/`, image không mang `docs/`. Tài liệu người đọc vẫn ở `docs/10-sources/`.

---

## Scheduler — `python -m etl` không tham số *(lát 13, 2026-09-09)*

Chạy `python -m etl` **không tham số** là bật **scheduler**: một vòng lặp nhịp **20 giây**, mỗi nhịp đọc sổ
`ops.etl_run` của ngày hôm nay (biên ngày giờ VN), tính mốc nào tới hạn, rồi spawn `python -m etl <job>` làm
**tiến trình con**. Lỗi của một job không kéo đổ job khác; ngoại lệ trong một nhịp chỉ được log, vòng lặp chạy tiếp.

```bash
cd backend
uv run python -m etl        # native dev: MỘT cửa sổ cho cả hệ; Ctrl+C dừng sạch
```

Trong container: service `etl` của `docker-compose.yml` chạy đúng lệnh này (`docker compose up -d`), log vào
volume `etl_logs` tại `/var/lib/dlck/etl-logs`. **Mã thoát của chính scheduler:** `2` khi thiếu
`ETL_DATABASE_URL` (chết trước khi chạm kho) · `0` khi dừng sạch.

### Bảng lịch — giờ VN, chép từ `etl/scheduler/schedule.py`

| Tên job (`ops.etl_run.job`) | Lệnh sau `python -m etl` | Loại | Mốc / nhịp | Ngày |
|---|---|---|---|---|
| `market.refdata` | `refdata` | daily | 08:00 | T2–T6 |
| `market.screener` | `screener` | daily | 15:20 | T2–T6 |
| `market.price_daily` | `price` | daily | 15:40 | T2–T6 |
| `market.events` | `events` | daily | 18:10 | T2–T6 |
| `market.snapshot` | `snapshot` | daily | **sau khi `market.events` success** | T2–T6 |
| `market.fundamentals` | `fundamentals` | daily | **sau khi `market.snapshot` success** | T2–T6 |
| `macro.omo_crawl` | `omo` | daily | 11:30 · 15:30 · 18:00 · 21:30 | cả tuần |
| `macro.wichart` | `wichart` | daily | 08:15 | cả tuần |
| `global.yahoo` | `yahoo` | daily | 11:00 | cả tuần |
| `global.binance` | `binance` | daily | 07:15 | cả tuần |
| `global.fred` | `fred` | daily | 05:00 · 20:00 | cả tuần |
| `global.ecb` | `fx` | daily | 22:30 | cả tuần |
| `global.lbma` | `lbma` | daily | 22:30 | cả tuần |
| `global.yahoo` | `yahoo --intraday` | intraday | mỗi **600 s** | cả tuần |
| `global.binance` | `binance --intraday` | intraday | mỗi **300 s** | cả tuần |
| `macro.wichart` | `wichart --intraday` | intraday | mỗi **300 s** | cả tuần |
| `news.classify` | `classify --limit 1000` | intraday | mỗi **900 s** (15 phút) | cả tuần |
| `news.collect` | `news --loop` | daemon | giữ sống liên tục | cả tuần |
| `market.price_backfill` | `price --backfill` | daemon | giữ sống 24/7 tới khi `pass_complete` | cả tuần |

Một **tên job** được phép có nhiều dòng (bản trọn ngày và bản `--intraday`): tên là khoá của `ops.etl_run`, còn
chống chạy chồng do runner lo theo tên. Ba dòng `--intraday` mang `weekdays=ALL_DAYS` — chúng chạy 24/7 theo đồng
hồ của runner, để mặc định T2–T6 sẽ đọc nhầm thành chỉ chạy ngày thường.

Hằng số cùng file: `MAX_CONCURRENT_CHILDREN = 6` · `RETRY_AFTER_MIN = 10` · `TICK_SECONDS = 20` ·
`SHUTDOWN_GRACE_S = 60` · `LOG_KEEP_DAYS = 30` · `SUMMARY_AT = (6, 0)`.

### Sáu luật chạy bù (`etl/scheduler/planner.py` — thuần, 0 I/O)

1. **Mốc đã qua hôm nay mà chưa có `success`** kể từ mốc đó ⇒ chạy bù ngay nhịp kế. Tắt máy qua 15:40 rồi bật lúc
   17:00 thì `price` chạy lúc 17:00, không chờ sang mai.
2. **Chỉ mốc của HÔM NAY.** Sổ đọc theo biên ngày VN; mốc hôm qua không bao giờ được bù — chạy bù muộn một ngày
   với dữ liệu theo ngày là ghi nhầm ngày, không phải cứu.
3. **`intraday` và `daemon` planner bỏ qua.** Runner tự lo: intraday theo `interval_s` bằng đồng hồ của nó (RAM,
   mất khi khởi động lại — vô hại), daemon thì giữ sống.
4. **Nhiều mốc cùng tên tự đúng.** OMO 4 mốc, FRED 2 mốc: chỉ xét **mốc gần nhất đã qua**, một
   `success` có `started_at ≥` mốc đó là đủ.
5. **exit 1 không thử lại; exit 2 thử lại đúng một lần sau 10 phút.** Trong các dòng `failed` kể từ mốc: có dòng
   mang `stats.guard_refused = true` ⇒ thôi (chốt chặn từ chối là *hành vi đúng*, chạy lại chỉ tốn nguồn); không
   có, đúng một dòng, và `now ≥ started_at + 10 phút` ⇒ thử lại; từ hai dòng trở lên ⇒ thôi tới ngày sau.
6. **Job mang `once_until_flag` tắt vĩnh viễn** khi có bất kỳ `success` nào mang `stats.pass_complete = true` —
   backfill giá đi hết một vòng thì không tự mở vòng mới. Luật này áp cho cả `weekly_once` (planner) lẫn `daemon`
   (`loop.run_once` đọc `once_done` **trước** bước daemon, nếu không nhịp kế tiếp bật lại đúng cái vừa xong).

Sổ đọc mỗi nhịp **loại** các dòng mang `stats.intraday` / `stats.subset` / `stats.dry_run` = `true`: lượt hẹp và
lượt khô không được tính là "mốc hôm nay đã chạy".

### Runner — trần, chặn trùng, hạ nhiệt

- **Trần 6 tiến trình con.** `daemon` được đảm bảo trước và **không chiếm slot**; task dư không spawn nhịp này,
  nhịp sau `due()` tính lại.
- **Con cùng tên còn sống ⇒ không spawn** (lớp ngoài của chống chạy chồng). Dòng log `đang chạy, bỏ qua lượt` in
  **một lần cho mỗi con đang sống**, không phải mỗi nhịp — bản đầu in mỗi 20 s, riêng `price` đã ~360 dòng/ngày.
- 🔴 **Hạ nhiệt 10 phút sau khi con thoát mã ≠ 0.** Job chết **trước** khi kịp `open_run` (ví dụ kho chưa áp
  migration) **không để lại dòng nào trong sổ**, nên planner cấp lại mốc đó mỗi nhịp và đập nguồn mỗi 40 giây.
  Runner nhớ trong RAM và từ chối spawn lại **cùng tên** trong 10 phút *(đo 2026-09-09 17:35 với `news.classify`
  khi kho dev chưa áp migration `0021` — spawn lặp 17:36:04 · 17:36:44 · 17:37:24)*. Daemon có backoff riêng.
- **Daemon `news --loop`**: chết thì khởi động lại sau 30 s, nhân đôi tới trần 300 s; sống quá 5 phút thì đếm lại
  từ 30 s.

### Log — một file mỗi job mỗi ngày

stdout + stderr của con vào `ETL_LOG_DIR/<job>-YYYYMMDD.log` (mở chế độ nối). Native mặc định
`<repo>/../dlck-runtime/etl-logs`; container `/var/lib/dlck/etl-logs` (volume `etl_logs`). Con thoát thì scheduler
in một dòng `[<YYYY-MM-DD HH:MM:SS>] <job> rc=<rc> <s>s (<lý do>)` — đúng chuỗi đó, để grep được.

🔴 **Dọn log theo NGÀY TRONG TÊN FILE** (`<job>-YYYYMMDD.log` cũ hơn 30 ngày), không theo `mtime`: file của ngày cũ
vẫn có thể được ghi thêm, và `mtime` bị mọi thao tác chép/khôi phục làm mới.

**Tóm tắt sáng 06:00** in ra stdout: bảng đếm 24 giờ qua theo job (success · exit 1 · exit 2 · 130) và dòng
`news --loop đang sống từ HH:MM`. Khởi động **sau** 06:00 thì bảng này in luôn một lần lúc khởi động.

### Dừng — và cái bẫy Windows

`SIGTERM` / `SIGINT` / `SIGBREAK` chỉ **đặt cờ**; nhịp kế mọi con đang sống nhận `SIGTERM` (POSIX) hoặc
`CTRL_BREAK_EVENT` (Windows), chờ tối đa **60 s**, còn sống thì `kill()`; scheduler thoát `0`.
`stop_grace_period` của service `etl` là **90 s** — cố ý rộng hơn 60 s đó, để Docker không giết cả scheduler
ngay lúc nó vừa bắt đầu chờ con (`ingester` cũng 90 s).

🔴 **Windows: con phải bắt `SIGBREAK`, không chỉ `SIGINT`.** Python ánh xạ `CTRL_BREAK_EVENT` sang `SIGBREAK`; con
chỉ cài handler `SIGINT` sẽ **chết với mã `0xC000013A`, không đi qua `except KeyboardInterrupt`** và để lại dòng
`running` treo trong sổ *(đo 2026-09-09 bằng một cặp script cha/con)*. Vì thế
`core.shutdown.install_signal_handlers` **và** vòng lặp scheduler cùng ánh xạ `SIGBREAK` về đúng đường Ctrl+C khi
nền tảng có thuộc tính đó. Linux không có `SIGBREAK` ⇒ không đổi gì.

### Hai lớp chặn chạy chồng, và mã thoát 1 khi khoá bận

**Lớp trong — khoá advisory Postgres.** `open_run` (điểm nghẽn chung của cả 15 họ job) mở một connection **riêng,
sống suốt đời lượt chạy** và giữ `pg_try_advisory_lock(hashtext(<tên job>))`. `close_run` đóng connection đó trong
`finally` ⇒ khoá nhả kể cả khi tiến trình bị giết cứng (phiên đóng là khoá tự nhả).

Khoá bận ⇒ job ghi một dòng `failed` với `error = lock busy: lượt khác đang chạy`, `stats = {"lock_busy": true,
"guard_refused": true}`, in một dòng stderr rồi **thoát 1** — ném trước cả `try` của job, nên không job nào phải sửa.

**Hợp đồng mã thoát chung cho mọi họ job** *(mở rộng bảng của `screener` dưới đây)*:

| Mã | Nghĩa |
|---:|---|
| `0` | ghi xong, `etl_run.status = success` |
| `1` | **chốt chặn từ chối** *hoặc* **khoá bận** — dữ liệu lành, không cần người; dòng `failed` luôn mang `stats.guard_refused = true`, riêng khoá bận thêm `stats.lock_busy = true` |
| `2` | lỗi thật (thiếu biến môi trường, nguồn hỏng sau retry, DB lỗi) — không ghi kho |
| `130` | dừng tay: Ctrl+C · `docker stop` · scheduler tắt con — sổ đóng `failed: dừng tay (Ctrl+C)` |

**Một dòng `market.price_backfill` `subset` mọc ra cạnh mỗi lượt `market.snapshot` là ĐÚNG, không phải người chạy
tay.** `snapshot_job._recrawl` kéo lại giá cho những mã có ngày không hưởng quyền trong cửa sổ vài ngày, bằng cách
gọi `price --backfill --codes … --max-minutes 20` **ngay trong tiến trình snapshot** — lượt con đó tự mở sổ dưới tên
`market.price_backfill` với `stats.subset = true`, và `stats.recrawl` của lượt snapshot ghi lại đúng những mã ấy
*(ví dụ thật: run 48 `market.snapshot` → run 49 lúc 2026-09-09 17:30, 4 mã DIG/HUB/ITC/VPI)*. Planner loại mọi dòng
`subset` nên nó không bao giờ bị tính là lượt backfill của mốc. Khoá `market.price_backfill` đang bận (daemon
backfill đang chạy vòng đầu, hay một lượt chạy tay) thì lượt con đó **không** còn giết lượt snapshot nữa:
`omo_store.LockBusy` được bắt tại chỗ, lượt snapshot vẫn đóng `success` và `stats.recrawl` mang `{"lock_busy": true}`.

⚠️ **Suốt vòng backfill đầu, re-crawl quyền của snapshot bị bỏ qua MỖI NGÀY** — daemon `price --backfill` giữ khoá
`market.price_backfill` từ đầu tới cuối vòng (~20 giờ gọi, thực tế dài hơn vì thang nghỉ), nên mọi lượt con của
`_recrawl` đều `lock_busy`. Chấp nhận cho đúng một vòng này *(phán quyết R33, 2026-09-10)*: giá điều chỉnh của mã có
ngày không hưởng quyền trong khoảng đó sẽ cũ cho tới khi được kéo lại. **Khi vòng xong (`pass_complete`), người vận
hành chạy TAY một lượt** `python -m etl price --backfill --codes <mã có ngày không hưởng quyền trong khoảng chạy
vòng>` — danh sách mã lấy từ `stats.recrawl` của các lượt `market.snapshot` mang `lock_busy` trong khoảng đó.

### Chạy thử native 10 phút — 2026-09-09 17:35:24 → 17:45:45

Bù đúng bốn mốc đã lỡ ngay nhịp đầu (`refdata` 08:00 · `price` 15:40 · `classify` 17:00 · `yahoo` 11:00) và **chạm
trần 6**; `yahoo` bản ngày bị chính con `--intraday` cùng tên chặn, rồi chạy ngay khi con kia nhả tên. Chạy chồng
cố ý (`python -m etl price` lúc 17:36 trong lúc lượt 15:40 còn chạy) ⇒ `lock busy`, **exit 1**, một dòng `failed`
mang `lock_busy`. Dừng bằng CTRL_BREAK lúc 17:45:24 ⇒ scheduler thoát `0` sau **21 s**, ba con đóng sổ `dừng tay
(Ctrl+C)`, **0 lần giết cứng, 0 dòng `running` mồ côi**.

## Chạy `ingester`

Cần: stack `docker compose up -d` ở gốc repo (kho + migrate), `.env` nguyên tố (bootstrap đã cấp `ingester_worker`).

```bash
cd backend                          # luôn đặt PYTHONIOENCODING=utf-8
uv run python -m ingester --measure --minutes 5   # ĐO: ghi frame thô ra file, KHÔNG đụng DB
uv run python -m ingester                          # daemon: ngoài 08:30–15:05 giờ VN thì ngủ, trong phiên ghi thật
uv run python -m ingester --minutes N              # chạy N phút rồi thoát — chạy tay/nghiệm thu ngoài giờ
uv run python -m ingester --reconcile [--date 2026-08-26]   # chỉ đối chứng cuối phiên
uv run python -m ingester --count 20260827 --db    # bộ đếm d[]: replay bản đo dry-run,
                                                    # so expected với count() rt.* thật
```

🔴 **Gate trước khi bật ghi thật:** phải có **một phiên đo trọn trong giờ giao dịch** (08:40–15:05) và chủ dự án duyệt luật `SM`/dedup — [spec §3.5](../docs/90-records/plans/2026-08-26-ingester-omo-first-slice/spec.md). Trước khi qua gate, chỉ chạy `--measure`.

**Bốn chế độ** (`run` mặc định · `measure` · `reconcile` · `count`, `ingester/__main__.py`) đều nối cùng một socket khi có socket; `--measure` thêm 20 topic × mã phái sinh + `pth` (câu hỏi đo còn treo — [roadmap §5.1](../docs/00-overview/roadmap.md)). File đo là JSONL gzip theo giờ trong `INGESTER_MEASURE_DIR`. `--count` là công cụ **offline, không nối socket** — replay lại `frames-*.jsonl[.gz]` của một ngày đo qua đúng `process_record` mà `run` dùng (dry-run, không ghi DB) để tính số dòng kỳ vọng mỗi bảng, đối chứng bằng số với kho thật khi thêm `--db` ([spec tràn-ra-đĩa §11](../docs/90-records/plans/2026-08-28-ingester-spill-to-disk/spec.md)); nhận `--from`/`--to` để cắt cửa sổ theo `received_at`, mặc định trọn ngày suy từ đối số đầu.

🔴 **Đối chứng `--db` phải cắt `--to` về đúng vòng đời tiến trình `run` — đừng dùng mặc định trọn ngày.** Job đo và job ghi không đóng cùng lúc (`SESSION_END_MEASURE` 15:10 sau `SESSION_END_RUN` 15:05), nên cửa sổ trọn ngày tính cả frame mà bản đo bắt được **sau khi tiến trình ghi đã thoát**. Nó hiện ra thành thâm hụt ma ở `index_delta`, vì đợt tính lại chỉ số ATC bắn ngay sau giờ đóng. Lấy mốc cắt từ chính kho:

```bash
docker exec infra-clickhouse-1 clickhouse-client --password "$CLICKHOUSE_PASSWORD"   -q "select max(received_at) from rt.quote where toDate(received_at)=today()"
```

rồi truyền vào `--to` dạng **giờ địa phương trần, KHÔNG kèm offset TZ** (`_iso_to_ms` gắn sẵn `Asia/Ho_Chi_Minh`; gõ offset vào sẽ bị nuốt). Ca thật 2026-08-28: cửa sổ mặc định ra `index_delta −15`; cắt `--to "2026-08-28 15:04:59.999"` ra **dư 0 cả 5 bảng**, bốn bảng kia không đổi một dòng.

Chế độ `run` (chạy ghi thật) còn dùng **`INGESTER_SPILL_DIR`** (mặc định `dlck-runtime/spill`, cùng họ `INGESTER_MEASURE_DIR`) — thư mục hàng đợi tràn-ra-đĩa khi RAM chạm trần hoặc ClickHouse trục trặc kéo dài; xem [market-data-store §3.7](../docs/20-design/market-data-store.md) và [spec tràn-ra-đĩa](../docs/90-records/plans/2026-08-28-ingester-spill-to-disk/spec.md).

## Chạy job crawl OMO

```bash
cd backend
uv run python -m etl omo            # một lần chạy, ghi rồi thoát
uv run python -m etl omo --seed <file.csv> [--dry-run]   # nạp một lần lịch sử phiên từ bản xuất FiinProX
```

Cần `ETL_DATABASE_URL` (user thuộc role `dlck_etl`). Job idempotent theo **ngày trong tiêu đề bài của SBV**: ngày đã có trong `macro.omo_session` thì bỏ qua, không ghi đè. Bị WAF chặn → `ops.etl_run` ghi `failed`, **không** ghi kho lẫn staging.

**`--seed` — nạp lịch sử một lần từ CSV.** SBV chỉ hiện phiên mới nhất nên chuỗi lịch sử phải nhập từ ngoài: bản xuất FiinProX (xlsx → CSV, chuyển bằng công cụ ngoài repo — job **không** đọc xlsx). Mỗi dòng CSV là một dòng trúng thầu; job gộp các dòng **cùng phiên + cùng kỳ hạn** thành một dòng `omo_auction` (khối lượng cộng lại, `note` ghi rõ đã gộp), bỏ qua phiên đã có trong kho (chạy lại ⇒ 0 phiên mới), và **dừng ngay** khi hai dòng cùng kỳ hạn có lãi suất khác nhau hoặc CSV có cột lạ. `--dry-run` in đủ `sessions_new` / `auctions` / `rows_merged` / `outstanding_*` mà không ghi gì. Lượt thật 2026-09-09: **248 phiên** 2025-09-08 → 2026-09-07 nối khít phiên SBV 08/09, 823 dòng đấu thầu, 3 dòng gộp; `macro.omo_flow.outstanding_vnd` 07/09 = **250.778,26 tỷ**, 08/09 = **249.363,44 tỷ** — khớp tới từng đồng với cột lưu hành của FiinProX.

## Chạy job refdata (danh bạ + danh mục mã + cây ICB)

```bash
cd backend
uv run python -m etl refdata                  # một lần chạy, ghi rồi thoát
uv run python -m etl refdata --accept-drop    # mở khoá MỘT lượt khi chốt chặn từ chối đúng
```

Cần `ETL_DATABASE_URL` (user thuộc role `dlck_etl`). Idempotent: lượt hai không đổi gì, `updated_at` không bị đụng. Chốt chặn sụt hai tầng — mốc là `ops.etl_run.stats` của lượt success gần nhất; bị từ chối thì rollback trọn, payload bằng chứng vào `staging.raw_payload` (`refdata:*`), và cần `--accept-drop` nếu cú sụt là thật (huỷ niêm yết hàng loạt).

**Ngành hai lớp — luật đã đảo (2026-08-28):** trước đây ETL bị cấm đụng `issuer.industry_id`. Nay ETL **sở hữu** cột đó — mỗi lượt ghi đè theo `market.industry_icb_map` (khớp `icb_code` chính xác trước, không có thì leo `icb_code_path` lấy tổ tiên gần nhất). Lớp tay nằm ở bảng riêng `market.issuer_industry_override`, mà ETL **không đọc, không ghi** — DB đã `REVOKE` cả `SELECT`/`INSERT`/`UPDATE`/`DELETE` của role `dlck_etl` trên bảng đó (migration `0012`). **Đường đọc hợp nhất duy nhất là view `market.v_issuer_industry`** = `COALESCE(override.industry_id, issuer.industry_id)` kèm cột `source` ∈ `manual` | `icb` | `NULL` — đọc thẳng `issuer.industry_id` là bỏ qua lớp tay, đọc thẳng `issuer_industry_override` là chỉ thấy lớp tay.

**Cảnh báo `%d doanh nghiệp không tra được ngành` mỗi lượt là bình thường, không phải hỏng.** Log phát dòng `WARNING etl.refdata_store 24 doanh nghiệp không tra được ngành (cả tay lẫn máy) — để NULL, không chặn job` và stats mang khoá `issuers_without_industry` **ở mọi lượt chạy**. Đây là trạng thái ổn định, không phải hỏng — nhưng **mốc "bình thường" đã đổi**, nên đọc con số phải kèm mốc:

| Mốc | `issuers_without_industry` | Gồm những gì |
|---|---|---|
| Trước 2026-09-03 | **24** *(đo 2026-08-28, [ledger](../docs/90-records/plans/2026-08-27-industry-two-layer-mapping/ledger.md))* | 24 chứng chỉ quỹ/ETF (`com_type_code = 'QU'`, `icb_code = '8985'`) — ETF và quỹ không có ngành theo thiết kế (dòng ICB `8980` "Quỹ đầu tư" cố ý không nạp vào `industry_icb_map`) |
| Từ 2026-09-03 | **541** *(đo 2026-09-03)* | 24 quỹ/ETF **+ 517 issuer tối thiểu** do [`etl events`](../docs/90-records/plans/2026-09-03-events-daily-etl/) đúc cho `organCode` vắng danh bạ (chính sách F7) — chúng không có `com_type_code`, không có `icb_code`, nên không tra được ngành |

🔴 **517 dòng thêm KHÔNG phải hồi quy.** Chúng là doanh nghiệp đã rời sàn hoặc chưa niêm yết, **không có dòng `security` nào trỏ tới** — nên bất biến A vẫn `0` *(kiểm 2026-09-03: 0 issuer thiếu ngành mà có cổ phiếu đang niêm yết)*. Con số vượt **541** đáng kể mới là dấu hiệu có gì đó đổi, và cách kiểm đúng là **chạy lại câu bất biến A**, không phải nhìn tổng:

```sql
SELECT count(DISTINCT v.issuer_id) FROM market.v_issuer_industry v
  JOIN market.security s ON s.issuer_id = v.issuer_id
 WHERE v.industry_id IS NULL AND s.security_type = 'stock' AND s.status = 'listed';
```

**Chốt chặn luật BCTC — khoá `bctc_violations` trong `ops.etl_run.stats`.** Mỗi lượt job đếm số doanh nghiệp vi phạm luật hai chiều `com_type_code` NH/CK/BH ⟺ ngành NGANHANG/CHUNGKHOAN/BAOHIEM (qua `market.v_issuer_industry`), ghi vào `stats["bctc_violations"]`, phát `WARNING etl.refdata_store %d doanh nghiệp vi phạm luật BCTC (com_type_code ⟺ ngành tài chính) — xem market.v_issuer_industry` khi khác 0 — **không chặn job**. Trạng thái khoẻ mạnh là **0**; gặp WARNING này thì tra `market.v_issuer_industry` theo `com_type_code` để tìm đúng doanh nghiệp lệch (thường là mã mới niêm yết gán sai lớp 1, hoặc lớp 2 đè tay vào nhầm ngành tài chính).

## Chạy job screener (bảng sàng lọc theo ngày)

```bash
cd backend
set -a; . ../.env; set +a; PYTHONIOENCODING=utf-8 uv run python -m etl screener
```

Cần `ETL_DATABASE_URL` (user thuộc role `dlck_etl`). Một lượt = 52 trang tuần tự (~2–3 phút), ghi
`market.screener_daily` UPSERT theo `(security_id, trading_date)` — chạy lại trong ngày đè bản của chính
ngày đó, không đẻ dòng mới.

**Hợp đồng mã thoát** — đọc `ops.etl_run` để biết chuyện gì đã xảy ra, đừng đoán từ log:

| Mã | Nghĩa |
|---:|---|
| `0` | ghi xong, `etl_run.status = success`, `data_domain_state('market.scores','fiintrade')` cập nhật watermark |
| `1` | **chốt chặn từ chối** — rollback trọn, 0 dòng ghi; `etl_run.status = failed` với lý do, bằng chứng trang 1 vào `staging.raw_payload` (`screener:page1`). Ngày lễ rơi vào đây và **đó là hành vi đúng** |
| `2` | lỗi thật (thiếu `ETL_DATABASE_URL`, nguồn hỏng sau retry, DB lỗi) — `etl_run.status = failed`, không ghi kho |

🔴 **Nguồn đóng dấu `tradingDate` = hôm nay ngay từ trước mở cửa, với `closePrice = 0`** (đo 2026-09-03).
Chốt chặn vế (i) đòi **≥ 20 % số mã gom được có `closePrice > 0`**; không có vế này thì mỗi ngày nghỉ đẻ
~1.545 dòng ma. Ba vế còn lại: đủ trang · tỷ lệ không ghép được `security_id` ≤ 2 % · tỷ lệ `comGroupCode`
lạ ≤ 2 %.

🔴 **Vì sao 20 % chứ không phải 50 %** *(hạ 0.5 → 0.2 lúc 2026-09-03 13:38, sau lượt chạy thật đầu tiên)*:
ngưỡng 0,5 đặt từ số đo **trang 1** (30/30 sau phiên vs 0/30 trước mở cửa), nhưng toàn thị trường **giữa
phiên** chỉ đạt **831/1.545 = 53,8 %** — nhiều mã UPCoM chưa khớp lệnh — tức chỉ hơn ngưỡng 3,8 điểm. Hai
hậu quả lệch hẳn nhau: từ chối nhầm một phiên thật là **mất vĩnh viễn** ảnh chụp ngày đó (Screener không có
backfill), còn nhận nhầm một ngày nghỉ chỉ là vài dòng ma xoá được. Nên ngưỡng phải nằm **xa vùng phiên
thật**: 0,2 ở giữa 0 % (ngày không phiên, đo 2 lần) và 53,8 % (phiên thật tệ nhất đo được).

## Chạy job events (lịch sự kiện doanh nghiệp)

```bash
cd backend
set -a; . ../.env; set +a; PYTHONIOENCODING=utf-8 uv run python -m etl events
```

Cần `ETL_DATABASE_URL` (user thuộc role `dlck_etl`). Một lượt = 9 lời gọi tải TRỌN sáu họ
`Calendar/GetCorporate*` (~2,5 phút), ghi `market.corporate_event` UPSERT theo khoá tự nhiên —
chạy lại trong ngày đè bản của chính lượt đó, không đẻ dòng mới.

Cờ `--accept-new` mở khoá lượt tạo NHIỀU issuer tối thiểu cho mã vắng danh bạ — chỉ dùng cho lượt
backfill đầu tiên (517 issuer, 2026-09-03), phải có người nhìn số trước khi chạy; task tự động
(`dlck-events`) **không bao giờ** mang cờ này.

## Chạy job price (giá theo ngày)

```bash
cd backend
set -a; . ../.env; set +a; PYTHONIOENCODING=utf-8 uv run python -m etl price                      # hằng ngày: trang 1 (60 phiên) mọi cổ phiếu niêm yết
set -a; . ../.env; set +a; PYTHONIOENCODING=utf-8 uv run python -m etl price --codes BID,VHM       # chỉ vài mã — chạy thử dưới quyền production, hoặc re-crawl theo sự kiện quyền
set -a; . ../.env; set +a; PYTHONIOENCODING=utf-8 uv run python -m etl price --backfill                     # lùi trọn lịch sử (~12,5 năm) — đây là lệnh scheduler chạy, dạng daemon 24/7
set -a; . ../.env; set +a; PYTHONIOENCODING=utf-8 uv run python -m etl price --backfill --stop-before-open   # chỉ khi chạy TAY: dừng trước 08:45 ngày giao dịch kế
```

Cần `ETL_DATABASE_URL` (user thuộc role `dlck_etl`). `Code` gửi cho FiinTrade là **`organCode`** tra qua
`issuer_external_id('fiintrade')` — 41 % mã có `organCode ≠ ticker`, gửi ticker là nhận `Code not valid`.
Ghi `market.price_daily` UPSERT theo `(security_id, trading_date)`: **5 cột** (`close_adj` ← `closeValue`,
**`close_raw` ← `closePrice` — giá thô lịch sử, điền một lần rồi không đè**, O/H/L) + `raw.fiintrade` giữ nguyên
99 trường; dòng có payload không đổi được **bỏ qua** nên `stats.rows_changed` của lượt chạy lại phải là 0.
Hồ sơ và ba quyết định thiết kế (tuần tự thay vì 8 luồng · `close_raw` từ `closePrice` · không mở cột mới):
[`docs/90-records/plans/2026-09-03-price-daily-etl/`](../docs/90-records/plans/2026-09-03-price-daily-etl/).

| Chế độ | Sổ `ops.etl_run.job` | Giao dịch | Guard |
|---|---|---|---|
| hằng ngày | `market.price_daily` | một giao dịch cho cả lượt, guard **trước** commit | (0) không mã nào có dữ liệu · (i) mã sai + mã hỏng > 2 % · (ii) số mã có dữ liệu sụt > 2 % so lượt success toàn tập gần nhất · (iii) ngày mới nhất ở tương lai · (iv) ngày mới nhất lùi so mốc |
| `--backfill` | `market.price_backfill` | mỗi mã một giao dịch; `stats.cursor` ghi sau từng mã (mã hỏng/sai **vẫn đẩy con trỏ đi** — làm lại ở vòng sau, dấu vết ở `failed_tickers`/`invalid_tickers`) | không guard tổng — cầu chì **10 mã liên tiếp** hỏng ⇒ **nghỉ rồi thử lại đúng mã đó**, nghỉ dài dần **10 → 20 → 40 → 60 → 60 …** phút theo số lần nghỉ LIÊN TIẾP (`stats.source_down_pauses`, `stats.source_down_pause_s`); một mã tải được là thang về lại 10 phút. Sau mỗi lần nghỉ chỉ thăm dò **một mã** (`Fetcher.resume`) nên mỗi quãng nghỉ tốn **≤ 4 lời gọi** — nguồn đang xấu vẫn được để yên. **Không bao giờ bỏ dở vòng** *(sửa 2026-09-10: đo 09/09–10/09 thấy `getPriceData` trả HTTP 200 kèm `status: Failed, "Timeout expired…"` cho ~4–9 mã MỖI GIỜ ở mọi giờ, dù một luồng hay ba — nghẽn là nền của nguồn; bản bỏ cuộc sau 3 lần nghỉ chết 02:02 ngày 10/09 sau 194 mã, con trỏ `CK8`, không ai bật lại)*. Nghỉ tới **6 lần liên tiếp tại cùng một vị trí con trỏ** (~4,5 giờ) mà mã vẫn không tải nổi ⇒ **bỏ qua mã đó**, ghi vào `failed_tickers`, con trỏ đi tiếp và làm lại ở vòng sau — một mã hỏng vĩnh viễn không được treo cả vòng *(R30)*. Mỗi quãng nghỉ ngủ thành **lát 30 giây** để Ctrl+C/CTRL_BREAK đóng được sổ trong ≤ 30 giây *(R32: trên Windows `time.sleep` không bị CTRL_BREAK đánh thức, mà scheduler chỉ chờ con 60 giây)*; vẫn đếm `dup_dates` và `raw_close_mismatch` từng mã |

Bốn bộ đếm "không có dữ liệu" của lượt hằng ngày, đều nêu tên ≤ 20 mã: `invalid` (nguồn trả `Code not valid`) ·
`failed` (hỏng sau 3 retry, kể cả timeout/đứt kết nối) · `empty` (trả `Success` nhưng 0 phiên) · `no_organ_code_count`
(cổ phiếu niêm yết chưa có `issuer_external_id('fiintrade')` — không gọi được, không tính vào `codes`). Bất biến:
`with_data + empty + invalid + failed = codes`; guard (i) cộng ba số giữa vào tử số.

**Máy ngủ theo lịch (02:00) giữa lượt — job sống qua được, thiết kế cho đúng ca này** *(chủ dự án đặt lịch ngủ đêm;
máy không tự ngủ vì nhàn rỗi)*. Sự cố 2026-09-04 02:00 lộ ba chỗ hở, nay đóng cả ba: (1) lời gọi HTTP treo qua giấc
ngủ thức dậy thành `httpx.ReadTimeout` — từ `e7f80f6` được thử lại 3 lần như response xấu; (2) kết nối Postgres nằm
trong pool suốt 38 phút fetch chết sau giấc ngủ — `pool_pre_ping=True` thay nó trước khi dùng; (3) ngân sách
`--max-minutes` tính theo **đồng hồ tường**, giờ ngủ vẫn tính ⇒ thức dậy là dừng sau mã đang dở, không chạy lấn vào
giờ giao dịch; con trỏ đã lưu sau từng mã nên lượt sau nối tiếp. Giữ máy thức bằng `SetThreadExecutionState` **không** dùng được: nó chỉ chặn ngủ do nhàn rỗi, không chặn được lệnh
suspend theo lịch.

**Backfill do scheduler chạy, không chạy tay trong phiên chat** *(quyết định chủ dự án 2026-09-04; chủ lịch đổi từ
task Windows sang scheduler ở lát 13)*: dòng `market.price_backfill` kiểu **`daemon`** — `price --backfill`, **giữ
sống 24/7**, và **tắt vĩnh viễn** khi đã có một lượt `success` mang `stats.pass_complete = true` *(chủ dự án chốt
2026-09-10 sáng: nguồn nghẽn đều ở mọi giờ nên không có "giờ đẹp" để hẹn — cứ chạy, và nghỉ dài dần khi nguồn xấu)*.
Không đặt hạn giờ: dòng này không mang `--stop-before-open` cũng không mang `--max-minutes`. Nguồn nghẽn ⇒ nghỉ theo
thang 10/20/40/60 phút rồi đi tiếp, **không bỏ dở vòng** (một mã nghỉ hết 6 lần vẫn không tải được thì bỏ qua mã đó,
không treo vòng); crash thật ⇒ runner bật lại ở nhịp sau và con trỏ nối tiếp. Suốt vòng này daemon **giữ khoá**
`market.price_backfill`, nên re-crawl quyền của snapshot bị bỏ qua mỗi ngày với `stats.recrawl.lock_busy` — xong vòng
thì chạy tay một lượt `price --backfill --codes …` cho những mã đó *(xem ô ⚠️ ở mục "Mã thoát", phán quyết R33)*.
Chạy tay vẫn được (`uv run python -m etl price --backfill --stop-before-open`): cờ `--stop-before-open` còn nguyên
cho lượt tay, tính hạn **08:45 của ngày giao dịch kế tiếp** ngay lúc bắt đầu nên tối thứ 3 dừng trước phiên sáng thứ 4.
Máy ngủ 02:00 giữa chừng: job sống qua và chạy tiếp; con trỏ nối các lượt. ⚠️ Hết vòng (`pass_complete`) thì scheduler **thôi hẳn** dòng
này; muốn làm mới toàn bộ chuỗi điều chỉnh (~20 giờ gọi) thì chạy tay một lượt, còn cập nhật thường ngày đi bằng
re-crawl theo sự kiện quyền với `--codes` (lát 4). Tiến độ: `stats.cursor` /
`codes_done` / `stop_at` của job `market.price_backfill` trong `ops.etl_run`.

Lượt `--codes` ghi `stats.subset = true`: **không** làm mốc cho guard (ii)/(iv), **không** đụng
`data_domain_state('market.price')`, **không** dời con trỏ backfill. Backfill hết vòng (`pass_complete`)
thì lượt kế bắt đầu vòng mới từ mã đầu — log ghi rõ. `stats.raw_close_mismatch` phải là **0**: đó là
mắt của luật điền-một-lần `close_raw`; khác 0 là nguồn đã sửa hồi tố giá thô, xem tên mã trong
`raw_close_mismatch_sample`.

Bốn điều nguồn làm mà tài liệu cũ không nói *(đo 2026-09-03, [`09-fiin-market-price.md`](../docs/10-sources/market/09-fiin-market-price.md))*:
`status` trả lẫn `0` và `"Success"` (job nhận cả hai) · `FromDate`/`ToDate` bị bỏ qua · nhóm dòng tiền theo
nhà đầu tư điền trễ **T+1** (trang 1 = 60 phiên nên lượt hôm sau tự vá) · ngày nghỉ không có dòng (chạy ngày lễ
là idempotent, không cần vế "có phiên không" như Screener).

## Chạy job snapshot (họ hồ sơ doanh nghiệp)

```bash
uv run python -m etl snapshot                       # lượt bình thường: trigger + quét sàn cuốn chiếu
uv run python -m etl snapshot --codes A32,BAB       # ép một tập mã, mọi kind, bỏ qua nhịp
uv run python -m etl snapshot --kinds dividend      # chỉ một vài kind
uv run python -m etl snapshot --max-minutes 5       # trần thời gian, dừng sau target đang dở
```

Bốn kind `snapshot` · `valuation` · `ownership` · `dividend` vào `market.snapshot_daily`.

**Quét sàn chạy theo NHỊP, không theo trần ngày** *(bỏ trần 2026-09-09, lát 13)*: mỗi lượt lấy **mọi** cặp
`(issuer, kind)` đã tới nhịp — `snapshot` 90 ngày, `valuation` · `ownership` · `dividend` 30 ngày — thay vì cắt
theo một hạn mức lời gọi mỗi ngày. Ngày thường vẫn cỡ **234 lời gọi** (fetch ~2 phút) vì nhịp tự rải đều; ngày mà
một khối lớn cùng tới nhịp thì lượt đó quét trọn khối, chấp nhận dài hơn. Trần duy nhất còn lại là
`--max-minutes` (dừng sau target đang dở, `checked_at` giữ chỗ) và trần **300 issuer** của nhánh trigger.

**Kho chỉ nhận dòng KHI NỘI DUNG ĐỔI** — họ này không có trường nào đổi theo ngày. Phép so tính hash trên
**danh sách trắng theo kind**, cố tình bỏ ngoài mọi trường tính từ giá (`rtd11` `rtd21` `rtd25`,
`priceEarningRatio`, `dividendYield`): hash trọn payload thì ngày nào cũng "đổi". Payload vẫn lưu **trọn** vì bốn
endpoint chỉ trả giá trị hiện tại, không backfill được — trường không lưu hôm nay là mất vĩnh viễn.

**Không có con trỏ, và không cần:** `ops.snapshot_check.checked_at` chính là con trỏ — lượt sau tự lấy nhóm cũ
nhất chưa tới lượt, nên lượt bị giết giữa chừng không mất chỗ. Bảng này cũng là chỗ **đếm lỗ của lịch sự kiện**:
quét sàn tìm ra thay đổi mà trigger không bắn thì `changed_floor` tăng.

**Hai đồng hồ, đừng trộn** *(bài học trả giá 2026-09-04)*: mốc nước ở `ops.data_domain_state('market.snapshot')`
đo **ngày công bố** (`max(public_date)`) và chỉ tiến khi lượt không có mã nào hỏng hay sai hình dạng — đẩy mốc
khi còn target chưa phục vụ là mất trigger vĩnh viễn. Còn **re-crawl giá** không dùng mốc nước mà theo cửa sổ
`exright_date` trong 3 ngày gần đây, chỉ với `CashDividend`/`StockDividend`/`ShareIssuance` (`AGM` không đụng hệ
số điều chỉnh), trần `MAX_RECRAWL = 50` mã và `RECRAWL_MAX_MINUTES = 20` phút. Lỗi re-crawl **không** kéo đổ lượt
snapshot; mã chưa kịp kéo được cửa sổ 3 ngày bắt lại.

**Trần trigger và mốc nước** *(sửa 2026-09-04 tối, cùng công thức lát 5)*: nhánh trigger loại những cặp
`(issuer, kind)` đã có `snapshot_check.checked_at` (ngày VN) từ ngày công bố trở đi — "đã phục vụ" — rồi mới cắt
trần `MAX_TRIGGER` × số kind; bị cắt thì mốc chỉ tiến tới ngày cắt − 1 (`stats.trigger_cut`), không bao giờ lùi.
Bản cũ đẩy mốc tới `max(public_date)` toàn cục ⇒ phần bị cắt mất trigger vĩnh viễn; còn "mốc = ngày cắt − 1"
một mình sẽ kẹt ở ngày hạn nộp khi hàng trăm mã cùng `public_date`.

🔴 **Nếu job bị từ chối nhiều ngày liền, đọc dòng này trước khi nghi nguồn hỏng.** Chốt chặn (i) tính tỷ lệ
đổi trên **cả lượt**, gộp bốn kind. `ownership` chiếm 70/234 target, và `majorShareHolders`/`boardOfDirectors`
mang dấu thời gian **kỳ công bố** — khi nguồn cập nhật kỳ mới, mọi mã `ownership` được so trong 30 ngày kế tiếp
đều đổi ⇒ 70/234 = **29,9% > ngưỡng 20%** ⇒ lượt bị từ chối, có thể lặp lại nhiều ngày, bốn lần một năm. Đây là
**vận hành bình thường chạm ngưỡng**, không phải nguồn hỏng. Chưa sửa vì lời giải không hiển nhiên: tách ngưỡng
theo từng kind làm ca này nổ **dễ hơn** (100% của `ownership`), còn nới ngưỡng thì mất khả năng bắt tập trắng sai.
Cần vài tháng số thật của `changed_floor` mới quyết được. Gặp ca này: đọc `stats.tally` của lượt bị từ chối, nếu
phần đổi dồn hết vào một kind thì chạy tay từng kind bằng `--kinds` để đi tiếp, và ghi số vào hồ sơ lát 4.

**Lịch:** scheduler chạy job này **ngay sau khi `market.events` thành công** (kiểu `depends_on`, xem mục
Scheduler ở đầu file) — trigger đọc đúng bảng mà `events` 18:10 vừa ghi, nên thứ tự này là ràng buộc, không phải
sở thích. Không xếp `snapshot` trước ~15:20: trong phiên thì `valuation` đổi theo P/E·P/B nhóm ngành nên lượt nào
cũng "đổi" (số đo lát 4/11).

## Chạy job fundamentals (báo cáo tài chính + danh sách PDF + từ điển)

```bash
uv run python -m etl fundamentals                              # lượt thường: trigger Earning + quét sàn 90 ngày, quota 20 mã/kind
uv run python -m etl fundamentals --codes A32,BAB              # ép một tập mã, mọi kind, bỏ nhịp/quota — chạy thử dưới quyền production
uv run python -m etl fundamentals --kinds bs,reports           # chỉ vài kind: bs · is · cf · reports
uv run python -m etl fundamentals --backfill --stop-before-open --max-minutes 40   # lượt điền đầu: mọi cặp CHƯA KIỂM, không quota, dừng trước 08:45
```

Bốn kind `bs` · `is` · `cf` (→ `market.financial_statement`, dạng dài, **bỏ null**, `metric_code` chữ thường) và `reports`
(→ `market.financial_report_file`, khoá `source_id`). Mỗi lượt nạp lại từ điển 729 mã vào `market.metric_dictionary` từ
`backend/etl/data/field-dictionary.json` trước khi gọi nguồn — file hỏng thì lượt chết ngay, chưa gọi gì.

**Ghi KHI ĐỔI, hash trên TRỌN payload đã chuẩn hoá** (ba endpoint không có trường tính từ giá). Đổi ⇒ xoá trọn
`(issuer, statement_type)` rồi chèn lại trong một giao dịch, cộng một dòng `staging.raw_payload` — đó là lịch sử điều
chỉnh hồi tố. `reports` upsert theo `source_id`, không xoá. **Rỗng không bao giờ xoá:** mã từng có dữ liệu mà nguồn trả
rỗng thì giữ nguyên kho, không đánh dấu đã kiểm, đếm vào `tally.empty`.

**Con trỏ là `ops.fundamentals_check.checked_at`** — cả lượt thường lẫn `--backfill`; giết giữa chừng không mất chỗ,
`stats.remaining` là số cặp (issuer, kind) chưa kiểm còn lại. Lượt điền trọn sàn ≈ 6.092 lời gọi, ≥ 51 phút chỉ tính giãn cách; chạy thật 2026-09-04 tối: 6.082 lời gọi, ~1 giờ 45 phút kể cả ghi, 0 retry (quy ước §10.8).

**Mốc nước** (`ops.data_domain_state('market.fundamentals')`) đo `public_date` của `Earning`, chỉ tiến khi lượt đầy đủ,
không mã nào hỏng/sai hình dạng/rỗng và không bị cắt giờ. Nhánh trigger **loại cặp đã kiểm sau ngày công bố** rồi mới
cắt trần 300 issuer; bị cắt thì mốc chỉ tiến tới ngày cắt − 1 (`stats.trigger_cut`) — nếu không, ngày hạn nộp với hàng
trăm mã cùng `public_date` sẽ làm phần dư mất trigger vĩnh viễn (review 2026-09-04).

⚠️ **Lượt `--codes` dưới 20 target không được guard bảo vệ** (`MIN_SAMPLE`): đọc `stats.tally` bằng mắt — `bad_shape`
khác 0 là nguồn đổi hình dạng (đã gặp: `"quarterly": null` thay cho `[]` trên cùng mã trong cùng ngày).

🔴 **Chốt (i) mùa báo cáo:** như `snapshot`, tỷ lệ đổi nhóm quét sàn > 20 % có thể là vận hành bình thường khi quét sàn
rơi vào mã vừa có kỳ mới mà lịch sự kiện sót. Đọc `stats.tally`, chạy tay `--kinds` để đi tiếp, ghi số vào hồ sơ lát 5;
**không** nới ngưỡng.

**Lịch:** scheduler chạy job này **ngay sau khi `market.snapshot` thành công**, tức chuỗi `events` 18:10 → `snapshot` → `fundamentals` trong cùng buổi tối (mục Scheduler ở đầu file).

## Chạy job wichart (vĩ mô · tiền tệ · giá hàng hoá WiChart)

```bash
uv run python -m etl wichart                     # 68 key, 105 series → macro.observation (53) + asset.price_daily (52); registry nạp lại mỗi lượt
uv run python -m etl wichart --dry-run           # fetch + chuẩn hoá + guard, KHÔNG ghi gì (kể cả registry/raw_payload); in stats
uv run python -m etl wichart --keys cpi,vang     # lượt con: tập ép, không guard, không đụng data_domain_state; registry vẫn nạp trọn
```

Một lượt ≈ 68 lời gọi, ~15 giây (đo 2026-09-05: 0 retry). Không có `--backfill`: lượt đầu đã nạp trọn cửa sổ 2 năm của
chuỗi ngày và toàn lịch sử tháng/quý/năm. Hồ sơ: [`docs/90-records/plans/2026-09-05-wichart-macro-etl/`](../docs/90-records/plans/2026-09-05-wichart-macro-etl/).

**Hai chủ sở hữu của registry, lệch là chết trước khi fetch:** khối Python §9 của
[`docs/10-sources/macro/wichart.md`](../docs/10-sources/macro/wichart.md) giữ sự thật đo về nguồn (tên series, đơn vị gốc,
`scale`, role, cờ, tần suất); `etl/wichart_registry.py` giữ mã của mình (`vn.cpi`, `gold.sjc_buy`, `fx.usd_vnd.central`…)
và trường thiết kế (lớp tài sản, tiền tệ, `price_type`). `build()` ghép theo `(key, idx)` và raise `RegistryError` khi
một bên có series mà bên kia không — thêm/bỏ series là sửa **cả hai** chỗ. Series chết (`xang_dau[0]` RON 95, `ncp[1]`,
20 key Tier X) **không có dòng registry**; dòng ánh xạ của series biến mất khỏi module bị **xoá đầu lượt** (dòng `indicator`/`asset` giữ nguyên nên observation không mất chủ) — xoá chứ không tắt vì tắt vẫn vỡ `UNIQUE (indicator_id, source)` khi một mã đổi vị trí series (review 2026-09-05). Cột `active` để dành **lát 14** *(giám sát hợp đồng — số cũ là lát 12)*.

**Chuẩn hoá tại cổng** (`etl/wichart_normalize.py`): epoch parse bằng `Asia/Ho_Chi_Minh` (nửa đêm giờ VN) · neo **đầu kỳ**
(quý của nguồn neo tháng cuối ⇒ đổi về tháng đầu; năm ⇒ 01-01) · `value = raw × scale` (`Decimal`) · tên series phải khớp
§9 (trừ cờ `NAMEWRONG` — `td` nguồn ghi "Tổng tiền gửi" nhưng là tín dụng) · tần suất thật (trung vị khoảng cách) phải
khớp khai · giá trị mới nhất phải nằm trong dải đơn vị (`BANDS`). **Điểm cuối tuần của asset chỉ bỏ khi là chép lại** của
điểm liền trước (đo 2026-09-05: vàng thế giới có 123 điểm T7/CN thật vì phiên Mỹ đóng rạng sáng T7 giờ VN, còn `lua`/`gao`
thì 172/174 điểm cuối tuần là chép lại); macro giữ mọi điểm.

**Ghi:** UPSERT trọn mọi điểm, nhưng `… DO UPDATE … WHERE value IS DISTINCT FROM excluded.value` — dòng không đổi **không
bị chạm** (`ingested_at` = lúc giá trị hiện tại về); `stats.inserted`/`stats.changed` đếm qua `RETURNING (xmax = 0)`.
`staging.raw_payload` (`wichart:<key>`) chỉ ghi khi hash response đổi so với dòng gần nhất. Một dòng `macro.series_break`
cho `vn.gdp.real` (`2026-01-01`, hệ số 1,6005 — đổi năm gốc) được seed mỗi lượt; chuỗi đã nối là view
`macro.observation_spliced`, bảng lưu số như nguồn công bố.

**Guard trước giao dịch ghi** (`etl/wichart_guard.py`, `MIN_SAMPLE 20`): key hỏng > 20 % · series sai hình dạng > 5 % ·
series ngoài dải > 5 % ⇒ `failed`, bằng chứng = body của **các key fetch được** vào `raw_payload` với `meta.refused` (key hỏng không có body để lưu), exit 1. Tần suất lệch chỉ ghi
`stats.tally.series_freq`. Một series lẻ `band`/`shape` **không** chặn lượt nhưng **không được ghi** — đọc `stats.errors`
rồi soi rồi chạy `--keys` sau khi hiểu vì sao. **Mốc nước** = ngày VN của lượt, hai dòng `data_domain_state`
(`macro.indicator`/`wichart` và `asset`/`wichart`), chỉ tiến ở lượt đầy đủ.

**Lịch:** scheduler chạy `wichart` **08:15 mỗi ngày, kể cả cuối tuần**, và `wichart --intraday` mỗi **300 s** 24/7. Giờ nạp thật của nguồn **vẫn chưa đo** (giả định trước 08:00 giờ VN) — ba ngày chạy thử của lát 13 là dịp đo.

## Chạy 5 job quốc tế (FRED · ECB · LBMA · Yahoo · Binance)

```bash
uv run python -m etl fred                        # 14 series FRED (DEXCHUS bỏ, CNY về ECB) → macro.observation (11) + asset.price_daily (3); cần FRED_API trong .env
uv run python -m etl fx                          # 7 cặp ECB qua Frankfurter (EUR·GBP·JPY·CAD·SEK·CHF·CNY, 1 lời gọi, trọn chuỗi từ 1999/2000) → asset.price_daily, fixing
uv run python -m etl lbma                        # vàng PM + bạc LBMA (2 lời gọi, trọn lịch sử từ 1968, cột USD) → asset.price_daily, fixing
uv run python -m etl yahoo [--backfill]          # 54 mã (36 chỉ số + DXY ICE + 17 cặp FX Yahoo) → asset.ohlc_daily; hằng ngày cửa sổ 400 ngày, --backfill từ 1900 (period1 âm)
uv run python -m etl binance [--backfill]        # PAXG + 10 coin (quote USDT, 24x7) → asset.ohlc_daily; hằng ngày 40 nến, --backfill phân trang từ 0
uv run python -m etl <src> --dry-run             # fetch + chuẩn hoá + guard, KHÔNG ghi gì; in stats
uv run python -m etl <src> --keys DGS10,PAYEMS   # lượt con theo mã nguồn (EUR · gold_pm · ^GSPC · PAXGUSDT…): không guard, không đụng data_domain_state

# lát 7b (2026-09-05 tối) — cập nhật trong phiên, cửa sổ ngắn
uv run python -m etl yahoo --intraday            # cửa sổ 5 ngày (thay 400), 54 mã, đẩy watermark, guard tỷ lệ như lượt trọn
uv run python -m etl binance --intraday          # limit=3 (thay 40), 11 mã, đẩy watermark, guard tất-cả-hoặc-không như lượt trọn
uv run python -m etl wichart --intraday          # 47 key tần suất ngày (freq='d', bỏ vĩ mô tháng/quý/năm), guard tỷ lệ; KHÔNG đẩy watermark, KHÔNG lưu body raw_payload trừ khi từ chối
```

`--intraday` chỉ có ở `yahoo`/`binance`/`wichart`. FRED/ECB/LBMA **không có cờ này** — không có nến/điểm trong ngày để cập nhật — nên truyền vào là `exit 2` (`unrecognized arguments`), không phải "nhận rồi bỏ qua". `--backfill` cũng vậy: chỉ `yahoo`/`binance` có ([`__main__.py:150-152`](etl/__main__.py)). Với `yahoo`/`binance`, `--intraday` **loại trừ với `--backfill`** và với `--keys` của `wichart` — dùng cùng lúc là `exit 2` trước khi mở lượt. Nến/điểm của Yahoo và Binance nay **là nến đang chạy, ghi đè liên tục tới khi phiên đóng** (luật cũ "bỏ nến chưa đóng"/`currentTradingPeriod`, `closeTime > now` đã gỡ hẳn — cả lượt trọn lẫn `--intraday`); dedupe theo ngày sàn, nến sau ghi đè nến trước. `stats["intraday"] = True` mỗi lượt; `stats.changed > 0` của Yahoo/Binance/WiChart-hàng-hoá ở **mọi** lượt `--intraday` là **hành vi mong đợi**, không phải bất thường. Mọi lời gọi HTTP của cả 6 nguồn (kể cả lượt trọn) nay giãn cách **ngẫu nhiên đều 1–5 s** qua `http_fetch` chung (thay `MIN_INTERVAL` cố định theo nguồn).

Đo 2026-09-05: cả 5 lượt hằng ngày **66 lời gọi ≈ 2 phút**, 0 retry; backfill Yahoo 37 lời gọi / 335.601 nến, Binance 39 lời gọi / 30.951 nến. Tải `--intraday` (17:20–17:39 VN): Yahoo 216 lời gọi/16 phút, WiChart 296 lời gọi/19 phút, cả hai **0 lỗi** — mức đó an toàn cho nhịp kế hoạch. Test sau lát 7b: **729 passed, 2 skipped** (+20 so với lát 7). Hồ sơ: [`docs/90-records/plans/2026-09-05-global-etl/`](../docs/90-records/plans/2026-09-05-global-etl/) (spec §5 luật từng nguồn, 6 file đo, ledger nghiệm thu) · [`docs/90-records/plans/2026-09-05-intraday-refresh/`](../docs/90-records/plans/2026-09-05-intraday-refresh/) (lát 7b: `--intraday`, 17 cặp FX Yahoo, CNY về ECB).

**Lịch đang chạy** *(bảng đầy đủ ở mục Scheduler đầu file)*: `yahoo --intraday` mỗi 10 phút · `binance --intraday` mỗi 5 phút · `wichart --intraday` mỗi 5 phút — cả ba **24/7**, không chia tuần/cuối tuần; bản trọn ngày `yahoo` 11:00 · `binance` 07:15; `fred` 2 lượt/ngày 05:00 + 20:00 VN; `fx` (ECB) và `lbma` 22:30 VN (fixing 14:15 CET / 15:00–12:00 London). Ruling "xếp `yahoo` sau 11:00 VN vì DXY" của lát 7 hết hiệu lực — nến DXY vào kho ngay trong lượt `--intraday`.

**Cùng khuôn với `wichart`, tham số hoá:** phần không phụ thuộc nguồn nằm ở `etl/registry.py` (`Series`, `load_registry(conn, series, source)` — đường ghi duy nhất vào 4 bảng registry, **xoá ánh xạ vắng mặt theo đúng `source`** nên lượt FRED không đụng dòng WiChart), `etl/series_store.py` (UPSERT chỉ-khi-đổi cho `observation`/`price_daily`/`ohlc_daily`, mẫu ≤ 50 dòng đổi `(mã, ngày, cũ, mới)` trong `stats.changes_sample` — thước đo vá hồi tố của FRED), `etl/series_guard.py` và `etl/series_job.py` (`SourceSpec`). Mỗi nguồn chỉ có `<src>_registry.py` (bảng mã của mình + `band` + `max_lag_days` theo series), `<src>_fetch.py` (URL + `classify`), `<src>_normalize.py` (luật thời gian + cổng), `<src>_job.py` (10 dòng).

**Guard hai chế độ:** nguồn ≤ 20 series (FRED 14 · ECB 7 · LBMA 2 · Binance 11) là **tất-cả-hoặc-không** — một series hỏng/sai hình dạng/ngoài dải/không tươi là `failed`, 0 dòng ghi, mọi body vào `staging.raw_payload` với `meta.refused`; Yahoo (54: 37 chỉ số + 17 FX) theo tỷ lệ như wichart (`failed` > 20 % · `shape`/`band` > 5 % · `stale` > 20 %), dưới ngưỡng thì bỏ series đó. **Không lưu body thô khi hash đổi** (khác wichart): FRED trọn chuỗi 12 MB/lượt, chỉ lưu khi từ chối.

**Năm luật thời gian, năm cổng — không dùng chung:** FRED `"."` = thiếu ⇒ không dòng, `max_lag` theo series (ngày 6 · dầu 10 · H.10 12 · tháng **75** · PCE 100 — chuỗi tháng trước kỳ công bố kế trễ tới ~72 ngày, đo 05/09) · ECB ngày cuối phải đủ 7 tiền tệ · LBMA `v[0]` = USD, `null` bỏ, ngày phải tăng · Yahoo `dataGranularity == '1d'`, **`instrumentType != 'ALTSYMBOL'`** (`quoteType` đã biến mất 2026-09-05), `regularMarketTime` ≥ now − 14 ngày, `currency` khớp registry (rỗng thì bỏ qua — `^MERV`), ngày nến theo **múi giờ sàn** *(luật cũ "bỏ nến cuối khi `now < currentTradingPeriod.regular.end`" gỡ hẳn từ lát 7b, 2026-09-05 — nến đang chạy vào kho, dedupe theo ngày sàn)* · Binance nến theo **UTC** của giờ mở, giá chuỗi ⇒ `Decimal` *(luật cũ "bỏ nến có `closeTime > now`" cũng gỡ hẳn từ lát 7b)*, `x-mbx-used-weight-1m ≥ 3000` ⇒ nghỉ 60 s, `418` dừng cả lượt.

🔴 **Khoá FRED nằm trong URL** — `http_fetch.Fetcher` chỉ giữ **tên lớp** exception (không `str(e)`), `fred_fetch.redact` che khoá trước khi log, `httpx` bị hạ xuống WARNING; test `test_transport_error_message_never_contains_the_api_key` pin điều này, AC8 lát 7 grep log/stats/evidence ra 0.

## Chạy job news (tin tức)

```bash
uv run python -m etl news                                  # một lượt: 47 feed RSS + 6 nguồn crawl HTML → news.*, dedupe URL + tiêu đề 48h, gắn mã tầng 1–2
uv run python -m etl news --dry-run                         # fetch + chuẩn hoá + dedupe, KHÔNG ghi gì; in stats
uv run python -m etl news --sources cafef,vietstock         # lượt con theo nguồn (danh sách phân tách bằng dấu phẩy)
uv run python -m etl news --loop [--minutes N] [--classify N]  # vòng lặp chạy tay, mặc định 5 phút/vòng, sitemap TinnhanhCK mỗi 3 vòng;
                                                             # --classify N: sau MỖI vòng phân loại tối đa N bài mới (job news.classify riêng, quota guard,
                                                             # lỗi không giết vòng thu thập). MẶC ĐỊNH TẮT — lưới chỉ chạy khi truyền cờ (chưa bật live);
                                                             # mỗi vòng một etl_run news.collect; Ctrl+C dừng sạch (đóng sổ "dừng tay")
uv run python -m etl news --backfill-sitemap [--source tinnhanhck|bnews|nguoiquansat] --from 2026-08 [--to 2026-08] [--max-minutes N] [--stop-before-open]
                                                             # job news.backfill_sitemap:<source> (mặc định tinnhanhck): kỳ đi lùi — TinnhanhCK/BNews theo THÁNG,
                                                             # NguoiQuanSat theo NGÀY (--from/--to vẫn YYYY-MM, con trỏ ghi tới ngày); mỗi bài một giao dịch,
                                                             # cầu chì 10 bài liên tiếp hỏng, hạn giờ kiểm sau MỌI URL; kỳ hỏng sau retry ⇒ periods_failed, lượt sau tự vá
```

**Đọc `stats`:** lượt thường `items / new / seen / merged_url / merged_title / refused / articles_failed / warnings / stale_feeds`; backfill sitemap `source / period_unit / cursor / periods_done / periods_failed / budget_hit` (lượt sau nối từ kỳ trước `cursor`; TinnhanhCK còn đọc con trỏ tên job cũ `news.backfill_sitemap` của lát 8). **Quy ước vận hành:** mỗi nguồn tối đa **một** tiến trình backfill (không có khoá trong code; `ON CONFLICT` chỉ bảo vệ dữ liệu). Ước tải *(đo 2026-09-06)*: BNews ~4.000 URL/tháng ≈ 3,5 giờ/tháng (lùi được tới 2015-08); NguoiQuanSat ~5.000 URL/tháng ≈ 4,5 giờ/tháng (tới 2021-07); WAF NguoiQuanSat 403 chập chờn không theo UA — để Fetcher retry, đừng đổi UA.

**Dedupe:** URL thô đã thấy ⇒ bỏ (`seen`); canonical trùng ⇒ `merged_url`, thêm `article_source`; tiêu đề chuẩn hoá (bỏ dấu, đ→d, bỏ tiền tố `(Chinhphu.vn) -`/`(ĐTCK)`/`BNEWS`) trùng trong **48 giờ** ⇒ `merged_title`, thêm `article_source`; tiêu đề **gần giống** báo khác trong 48 giờ (`pg_trgm` ≥ 0,6, chặn khi hai tiêu đề có ngày khác nhau) ⇒ `merged_near`, thêm `article_source`; còn lại tải bài, bóc, ghi `article` + `article_revision` v1 + `article_source` + `article_ticker`.

**Gắn mã** — lát 8 chạy **cả hai** tầng đầu, mỗi tầng một dòng `article_ticker` (`via`) để lát 14 (giám sát hợp đồng — số cũ là 12) đối chiếu: tầng `url` (CafeF CBTT, loại `HNX`/`HOSE`/`UPCOM`) · tầng `lookup` (regex 3 ký tự in hoa trên tiêu đề + sapo, **bắt buộc** đối chiếu `market.security` `listed`). Tầng 3 (AI, lọc niêm yết, trần 5 mã) ở `etl classify` (lát 9a). **2026-09-06:** tầng 2 bỏ thêm `news_tag.AMBIGUOUS` (USD/HCM/CEO/SEA/VND/BOT/PPP… — mã thật trùng chữ thường, đo 60/470 dòng sai) và `load_listed` bỏ chỉ số (`VN30`). `ticker_step_ran = true` cho mọi bài nhóm 3, `false` cho nhóm 1–2.

**Bằng chứng:** không lưu HTML bài thành công; `raw_payload` chỉ giữ XML/HTML danh sách khi hash đổi và HTML bài khi bóc bị từ chối (`meta.refused`).

**Lịch:** `news --loop` là **daemon của scheduler** (`news.collect`) — scheduler giữ nó sống liên tục, chết thì khởi động lại sau 30 s, nhân đôi tới trần 300 s. Muốn chạy tay thì chạy trong **cửa sổ riêng** (giống `ingester`): tiến trình sống nhiều giờ, Ctrl+C dừng sạch, không để dòng `running` treo — và **đừng chạy song song với scheduler**, khoá advisory theo `news.collect` sẽ cho lượt thứ hai exit 1 `lock busy`. Backfill sitemap (job tên khác, không đi qua scheduler) ước tính **~1,5 giờ/tháng**.

Test sau lát 8 (2026-09-06): **791 passed, 2 skipped** (+53 so với lát 7b). Hồ sơ: [`docs/90-records/plans/2026-09-05-news-collect/`](../docs/90-records/plans/2026-09-05-news-collect/) (spec · plan · ledger · `measure-news-2026-09-05.txt`).

## Chạy job classify (lưới AI phân loại tin — lát 9a, 2026-09-06)

Gọi **MiniMax M3** qua [`core/llm`](core/llm/) (SDK `anthropic` trỏ `https://api.minimax.io/anthropic`, khoá `LLM_API` trong `.env` — [minimax.md](../docs/10-sources/llm/minimax.md)). **Mọi lượt phải có trần** — không có chế độ "chạy hết" (mỗi bài ≈ 3k token vào, ≈ 10 s; toàn kho 8k bài ≈ 22 giờ và ăn hết cửa sổ quota tuần).

```bash
uv run python -m etl classify --per-group 100                       # 100 bài CHƯA phân loại mới nhất của MỖI nhóm gợi ý feed (1 · 2 · 3 · không nhóm) ⇒ ≤ 400 bài
uv run python -m etl classify --limit 50 [--max-minutes 10]          # 50 bài mới nhất bất kể nhóm; hạn giờ ⇒ budget_hit
uv run python -m etl classify --dry-run --per-group 3 --out x.jsonl  # gọi model THẬT nhưng không ghi kho, không mở etl_run, không ghi llm_call — để đo; JSONL từng bài
uv run python -m etl classify --limit 20 --thinking disabled         # tắt thinking (mặc định adaptive); --cap-chars 4000 đổi trần cắt thân bài (mặc định 3000)
```

**Ba lần là thôi — `news.article.classify_attempts`** *(migration `0021`, lát 13)*: bài lỗi được `+1` trong cùng
giao dịch với dòng `ops.llm_call`, và câu chọn bài thêm `AND a.classify_attempts < 3` ⇒ một bài hỏng vì nội dung
(không phải vì model chết) không quay lại ăn quota mãi. `stats.skipped_attempts` đếm số bài đang bị bỏ qua vì lý
do này — con số đó tăng đều là dấu hiệu phải đọc tay vài bài. Bốn trạng thái đọc thẳng từ bảng: chưa xử lý
(`classified_from IS NULL`, `attempts < 3`) · bỏ cuộc (`NULL`, `attempts ≥ 3`) · không xếp được nhóm (`labels` có
`x`) · không có mã (`ticker_step_ran` mà không dòng `article_ticker`). Đường `--ids-file` (bộ gold) **cố ý không
lọc** theo `attempts`. Lượt `--dry-run` không tăng bộ đếm.

Một bài = một giao dịch: `UPDATE news.article` (`group_no/sub/confidence/classified_from/content_chars/group_overridden/labels`; nhãn `x` ⇒ `group_no NULL` + `labels {x}`), `summary_ai` vào revision mới nhất, mã tầng 3 (`article_ticker via='ai'`, **lọc `market.security listed`** — model bịa `VFM`), tầng 1–2 chạy **bù** cho bài backfill được xếp nhóm 3, ngành hai đường vào `news.article_industry` (`via='ai'` từ model ≤ 3 ngành · `via='ticker'` suy từ mọi mã của bài qua `market.v_issuer_industry`), và một dòng **`ops.llm_call`** (token 4 loại, độ trễ, `ok/repaired/failed`). Bài lỗi giữ nguyên NULL, được chọn lại lượt sau; bài đã có `classified_from` **không bao giờ** chọn lại (chưa có `--force`).

**Guard:** quota Token Plan (`GET /v1/token_plan/remains`) kiểm trước lượt và mỗi 25 bài — dừng (`quota_stop`, vẫn `success`) khi cửa sổ 5 giờ < 20 % hoặc tuần < 10 % (**`success` + `quota_stop=True` + `classified=0` là dạng bình thường** của lượt bị chặn ngay đầu — quota kiểm sau `open_run` để lần chặn có dấu trong sổ); guard hỏng (HTTP ≠ 200, body lỗi) ⇒ `warnings` + `quota.{before,after}={"error":…}`, không chặn; 5 lời gọi liên tiếp lỗi thử-lại-được ⇒ `ModelDown` (exit 1, `failed` kèm stats); lỗi `auth` ⇒ exit 2 ngay. Thiếu `LLM_API` ⇒ exit 2 trước khi mở `etl_run`.

**Đọc `stats`** (`ops.etl_run` job `news.classify`): `selected / classified / failed / failed_schema / repaired / groups{1,2,3,x} / overridden / title_only / tickers_url|lookup|ai|ai_dropped / industries_ai|ticker / tokens{input,cache_read,output,thinking} / latency_s{p50,p90,max,total} / usd_estimate (quy giá pay-go để so, Token Plan tính theo quota) / quota{before,after} / quota_stop / budget_hit / warnings`. Ở `--dry-run` các bộ đếm `overridden`/`tickers_*`/`industries_*` luôn 0 (chỉ `apply` mới đếm) — đọc JSONL.

**Số đo thật** (2026-09-06, [ledger §2](../docs/90-records/plans/2026-09-06-news-classify-llm/ledger.md), 230 bài adaptive + 100 disabled): adaptive **p50 8 s / p90 16,5 s**, ≈ 3,0k token vào (cache trúng ≈ 50 %), ≈ 745 ra (≈ 330 thinking), **≈ $0,0019/bài quy giá, ≈ 6 bài/phút**; disabled p50 3,6 s, 294 ra, $0,0013/bài. 350 bài/ngày adaptive ≈ 1 giờ ≈ 6–7 % cửa sổ quota 5 giờ. Kho còn 7.797 bài chưa phân loại ≈ 22 giờ / ≈ $15 / 3 cửa sổ — chỉ chạy khi chủ dự án gọi tên.

⚠️ `ops.llm_call` tham chiếu `ops.etl_run` và `news.article` (FK không `ON DELETE`): **mọi lệnh dọn `news.article` / `ops.etl_run` (kể cả `TRUNCATE` trong test) phải dọn `news.article_industry` + `ops.llm_call` trước** — test e05/e55/e56 đã sửa theo. ⚠️ Chạy lượt > 10 phút **tách tiến trình** (`Start-Process cmd`), theo dõi qua `ops.etl_run`. **Lịch:** scheduler chạy `classify --limit 1000` kiểu **intraday mỗi 900 s (15 phút), 24/7** (chốt 2026-09-10, thay cho 8 mốc/ngày cũ — độ trễ 2 giờ quá lâu, chi phí token theo số bài không theo số lượt) — độc lập với `news --loop`, kiểu quét sàn, không gắn cờ `--classify` vào vòng thu thập ([news-pipeline §12](../docs/20-design/news-pipeline.md)).

## Chạy vòng chat (`agent` — lát 10, 2026-09-07)

```bash
cd backend && uv run --project . python -m agent   # REPL nhiều lượt — LUÔN chạy tiền cảnh, không có task tự động
```

⚠️ **Phải `cd backend` trước.** `pythonpath = ["."]` trong `backend/pyproject.toml` chỉ có hiệu lực khi rootdir là `backend`; chạy `uv run --project backend python -m agent` từ gốc repo trả `No module named agent` *(đã gặp thật 2026-09-07)*.

**Lệnh trong REPL:** `/moi` (hoặc `/mới`) xoá lịch sử và bắt đầu phiên mới. Dùng khi phiên **tràn cửa sổ ngữ cảnh** — lúc đó mọi lượt sau đều bị bỏ với một dòng `[lượt này dừng giữa chừng…]`, và trước lát 11 lối thoát duy nhất là Ctrl+C rồi chạy lại. Lịch sử **không** tự cắt khi gần trần: cắt tự động là đoán xem bạn còn cần gì trong đoạn hội thoại của mình.

Cần biến môi trường mới **`AGENT_DATABASE_URL`** — user login `agent_reader IN ROLE dlck_api` (chỉ `SELECT` trên `market`/`macro`/`asset`/`news`, không ghi được gì), tạo **per-môi-trường, ngoài migration** (khuôn [`database/README.md`](../database/README.md)), mật khẩu sinh ngẫu nhiên, ghi thẳng `.env`, **không in ra**. `assert_read_only()` chạy lúc khởi động, khẳng định đúng role và không có quyền `INSERT` — sai thì chết ngay, không chạy tiếp.

[`agent/`](agent/) chứa: `system_prompt.py` (gác phạm vi lĩnh vực + neo ngày hôm nay), `skills.py` (nạp trọn L1 lúc khởi động, tra L2 theo nhu cầu), `chat.py` (vòng REPL, dựng `tool_runner` mới mỗi lượt), `db.py`/`llm_log.py`, và [`agent/tools/`](agent/tools/) — 9 function dữ liệu/tri thức chạy dưới `dlck_api`, mỗi tool tự mở/đóng kết nối, không giữ transaction bắc qua lời gọi model. Hợp đồng đầy đủ 9 function: [`docs/20-design/chatbot-semantic-layer.md`](../docs/20-design/chatbot-semantic-layer.md). Bộ hồi quy (15 câu, có function calling) và kết quả chạy thật: [`docs/90-records/plans/2026-09-07-semantic-layer/`](../docs/90-records/plans/2026-09-07-semantic-layer/).

## Chạy trong container (lát 12 — 2026-09-08)

Cùng image, cùng code: `docker compose run --rm etl python -m etl <job> [cờ]` (mọi cờ ở các mục trên). `ingester` là service daemon riêng (`docker compose up -d ingester`), lưới đo `docker compose --profile measure up -d ingester-measure`. `docker stop`/`compose down` gửi `SIGTERM`, nhưng job `etl` và `ingester` KHÔNG đi cùng một đường: job `etl` đi đường Ctrl+C (`core/shutdown.py`) — sổ `ops.etl_run` đóng `failed: dừng tay (Ctrl+C)`, exit 130; `ingester` đi đường `install_loop_stop` — đặt `stop`, phiên đóng đúng đường deadline (xả hàng đợi + đối chứng), exit 0/1, **không** có dòng `ops.etl_run` nào (ingester chưa từng ghi bảng đó). `stop_grace_period` 90 s cho cả `etl` lẫn `ingester` *(đo 2026-09-08 21:34: `docker stop -t 90` phiên `--minutes 3` → `reconcile: p1=0 p2=0 ok=0`, exit 0)*. Lịch chạy tự động là **scheduler trong chính service `etl`** (`docker compose up -d`, mục Scheduler ở đầu file); Task Scheduler và `scripts/register-tasks.ps1` đã về hưu ở lát 12.
