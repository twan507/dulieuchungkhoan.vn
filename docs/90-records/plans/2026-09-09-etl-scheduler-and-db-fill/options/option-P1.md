# Phương án P1 — Scheduler tối giản (YAGNI): một file, không thư viện mới

Trục tối ưu: ít code nhất, ít file nhất, không abstraction cho thứ dùng một lần. Toàn bộ logic
lịch nằm trong MỘT module mới, viết vòng lặp tay theo đúng khuôn `daemon()` của
`backend/ingester/main.py` (clock/sleep tiêm được, ngủ lát ≤ 60 s, `asyncio.Event` stop).

## 1. Kiến trúc một đoạn + sơ đồ chữ

`backend/etl/scheduler.py` là toàn bộ scheduler: một bảng lịch dữ liệu literal (`SCHEDULE`),
một hàm thuần `is_due()` quyết định job nào tới hạn (dùng chung một truy vấn `ops.etl_run` cho
cả "tick bình thường" lẫn "chạy bù sau khởi động lại" — không có đường chạy bù riêng), một vòng
`asyncio` chính spawn tiến trình con qua `subprocess.Popen`, giới hạn đồng thời bằng
`asyncio.Semaphore`, và một supervisor riêng cho `news --loop`. Chặn chạy chồng hai lớp: lớp
trong-job là `pg_try_advisory_lock` được ghép thẳng vào `etl.omo_store.open_run()` — chokepoint
DUY NHẤT mà cả 15 họ job đã gọi (không cần sửa 15 file gọi nó); lớp scheduler là một dict PID
trong bộ nhớ tiến trình scheduler.

```
docker compose etl (command không đổi: ["python","-m","etl"])
        |
        v
etl/__main__.py: args rỗng -> etl.scheduler.main()
        |
        v
+---------------------- vòng lặp, tick <= 60s (etl/scheduler.py) --------------------+
| now = clock()  (core.clock.now_vn, tiêm được cho test)                             |
| runs_today = 1 SELECT ops.etl_run (hôm nay, lọc intraday/subset/dry_run)           |
| for e in SCHEDULE:                                                                 |
|     if e.kind == "loop": bỏ qua (supervisor riêng)                                 |
|     if e.job đang có task sống trong `running{}`: bỏ qua  <- lớp chặn chồng #2     |
|     if is_due(e, now, runs_today, last_outcome): running[e.job] = spawn qua sem(6) |
| await sleep(min(60, tới phút kế))                                                  |
+--------------------------------------------------------------------------------------+
        |                                              news --loop: supervisor riêng,
        v                                              giữ sống + backoff (§8)
subprocess con: python -m etl <job> [cờ]
        |
        v
etl.omo_store.open_run(engine, job)
   SELECT pg_try_advisory_lock(hashtext('etl.'+job))  <- lớp chặn chồng #1, phủ cả
   bận -> ghi sổ failed ngay + sys.exit(1)               `docker compose run` tay
   rảnh -> INSERT ops.etl_run(status='running') RETURNING run_id, giữ connection mở
```

## 2. File mới / sửa

| File | Trách nhiệm |
|---|---|
| `backend/etl/scheduler.py` (mới) | Bảng lịch, `is_due`, truy vấn `ops.etl_run`, spawn, quản lý concurrency, supervisor `news --loop`, dọn log 30 ngày. |
| `backend/etl/__main__.py` (sửa) | Nhánh `args` rỗng gọi `etl.scheduler.main()` thay vì `_heartbeat_loop()`; xoá import/hàm heartbeat. |
| `backend/etl/heartbeat.py` (xoá) | Không còn dùng — lát 12 để lại làm vỏ tạm. |
| `backend/tests/test_heartbeat.py` (xoá) | Test của module bị xoá. |
| `backend/etl/omo_store.py` (sửa) | `open_run()` thêm khoá advisory; `close_run()` thêm giải khoá. Đây là chokepoint chung 15 job — không sửa file job nào khác. |
| `docker-compose.yml` (sửa) | Thêm `ETL_LOG_DIR` vào `environment` của `etl`, thêm volume `etl_logs:/var/lib/dlck/logs`, thêm `etl_logs:` vào khối `volumes:` gốc. `command` KHÔNG đổi (đã là `["python","-m","etl"]`). |
| `.env.example` (sửa) | Thêm dòng comment `ETL_LOG_DIR=` cạnh khối `INGESTER_*_DIR`. |
| `backend/core/env.py` (sửa) | Thêm `"ETL_LOG_DIR"` vào `OPTIONAL_KEYS`. |
| `backend/tests/docs/test_d03_compose_contract.py` (sửa) | `ETL_OVERRIDES` thêm `ETL_LOG_DIR`; test mới xác nhận volume `etl_logs` mount đúng `/var/lib/dlck/logs` cạnh `/backups`. |
| `deploy/backend.Dockerfile` | KHÔNG đổi — `/var/lib/dlck/logs` đã được `mkdir`+`chown appuser` từ lát 12 (dùng chung path segment, khác volume theo service). |
| `backend/tests/etl/test_scheduler_due.py`, `test_scheduler_lock.py`, `test_scheduler_spawn.py`, `test_scheduler_concurrency.py`, `test_scheduler_news_loop.py` (mới) | Seam test — xem §11. |

## 3. Bảng lịch — dữ liệu Python

```python
# backend/etl/scheduler.py
from dataclasses import dataclass

@dataclass(frozen=True)
class Entry:
    job: str                       # tên trong ops.etl_run — khớp bảng JOB ở criteria.md
    argv: tuple[str, ...]          # đối số cho `python -m etl`
    kind: str                      # "daily" | "everyday" | "weekly" | "chained" | "interval" | "loop"
    at: tuple[int, int] | None = None      # (giờ, phút) giờ VN — daily/everyday/weekly
    every_min: int | None = None           # interval
    weekday: int | None = None             # weekly: 5 = thứ 7
    workdays_only: bool = False
    after: str | None = None               # chained: job cha phải success TRƯỚC

CLASSIFY_MARKS = [(7,0),(9,0),(11,0),(13,0),(15,0),(17,0),(19,0),(21,0)]

SCHEDULE: tuple[Entry, ...] = (
    # --- Ngày làm việc: refdata -> screener -> price, rồi chuỗi events -> snapshot -> fundamentals
    Entry("market.refdata",      ("refdata",),  "daily", at=(8, 0),   workdays_only=True),
    Entry("market.screener",     ("screener",), "daily", at=(15, 20), workdays_only=True),
    Entry("market.price_daily",  ("price",),    "daily", at=(15, 40), workdays_only=True),
    Entry("market.events",       ("events",),   "daily", at=(18, 10), workdays_only=True),
    Entry("market.snapshot",     ("snapshot",), "chained", after="market.events",      workdays_only=True),
    Entry("market.fundamentals", ("fundamentals",), "chained", after="market.snapshot", workdays_only=True),

    # --- OMO: 4 mốc, CHUNG một tên job (criteria §2.2 — is_due dùng "since" theo mốc, không theo tên) ---
    Entry("macro.omo_crawl", ("omo",), "everyday", at=(11, 30)),
    Entry("macro.omo_crawl", ("omo",), "everyday", at=(15, 30)),
    Entry("macro.omo_crawl", ("omo",), "everyday", at=(18, 0)),
    Entry("macro.omo_crawl", ("omo",), "everyday", at=(21, 30)),

    # --- Trọn, mọi ngày ---
    Entry("macro.wichart",  ("wichart",), "everyday", at=(8, 15)),
    Entry("global.yahoo",   ("yahoo",),   "everyday", at=(11, 0)),
    Entry("global.binance", ("binance",), "everyday", at=(7, 15)),
    Entry("global.fred",    ("fred",),    "everyday", at=(5, 0)),
    Entry("global.fred",    ("fred",),    "everyday", at=(20, 0)),
    Entry("global.ecb",     ("fx",),      "everyday", at=(22, 30)),
    Entry("global.lbma",    ("lbma",),    "everyday", at=(22, 30)),

    # --- Nhịp 24/7 — KHÔNG chạy bù (criteria §2.2 luật 6) ---
    Entry("global.yahoo",   ("yahoo", "--intraday"),   "interval", every_min=10),
    Entry("global.binance", ("binance", "--intraday"), "interval", every_min=5),
    Entry("macro.wichart",  ("wichart", "--intraday"), "interval", every_min=5),

    # --- classify: 8 mốc/ngày, literal từ CLASSIFY_MARKS ---
    *(Entry("news.classify", ("classify", "--limit", "1000"), "everyday", at=hm) for hm in CLASSIFY_MARKS),

    # --- news --loop: daemon con sống dai, quản riêng (§8), không nằm trong vòng tick ---
    Entry("news.collect", ("news", "--loop", "--classify", "1000"), "loop"),

    # --- backfill giá, thứ 7 00:05, chạy tới pass_complete rồi tự tắt (--stop-before-open) ---
    Entry("market.price_backfill", ("price", "--backfill", "--stop-before-open"), "weekly",
          at=(0, 5), weekday=5),

    # Lát 14: thêm MỘT dòng Entry(...) job giám sát tại đây — không cần sửa gì khác trong file này.
)

CONCURRENCY_CAP = 6            # criterion k — hằng số, sửa tại đây khi lát 14 thêm job
RETRY_AFTER_EXIT_2_MIN = 10
```

## 4. Thuật toán vòng lặp chính

Mốc tới hạn quy hết về MỘT phép so sánh: `at`/mốc phụ thuộc chuyển thành `datetime` giờ VN của
HÔM NAY (`core.clock.today_vn`), rồi hỏi "đã có `success` NÀO sau mốc đó chưa". Cách này đúng
luôn cho cả OMO (4 mốc cùng tên — so theo mốc, không theo tên) lẫn `chained` (mốc = giờ job cha
thành công) lẫn backfill thứ 7 (mốc = 00:05 thứ 7).

```
def is_due(e, now, runs_today, last_outcome) -> bool:
    if e.kind == "interval":
        return tick_elapsed_since_last_spawn(e, now) >= e.every_min   # trạng thái trong RAM, không bù
    if e.kind in ("daily", "everyday", "weekly", "chained"):
        if e.workdays_only and now.weekday() >= 5: return False
        if e.kind == "weekly" and now.weekday() != e.weekday: return False
        if e.kind == "chained":
            since = latest_success_at(runs_today, e.after)
            if since is None: return False
        else:
            since = datetime.combine(today_vn(now), time(*e.at), tzinfo=VN)
            if now < since: return False
        if has_success_since(runs_today, e.job, since): return False
        return not declined_today(e, since, last_outcome, now)        # xem §5, luật exit 1/2
    return False   # "loop" quản riêng
```

Vòng chính:

```
async def main_loop(clock=lambda: now_vn(), sleep=asyncio.sleep, stop=None, engine=...):
    stop = stop or asyncio.Event()
    sem = asyncio.Semaphore(CONCURRENCY_CAP)
    running: dict[str, asyncio.Task] = {}
    last_outcome: dict[str, tuple[int, datetime]] = {}     # (job, mốc) -> (exit_code, khi)
    news_task = asyncio.create_task(news_loop_supervisor(NEWS_ENTRY, stop))
    while not stop.is_set():
        now = clock()
        runs_today = fetch_todays_runs(engine, today_vn(now))         # §5
        for e in SCHEDULE:
            if e.kind == "loop": continue
            t = running.get(e.job)
            if t is not None and not t.done(): continue               # lớp chặn chồng #2
            if is_due(e, now, runs_today, last_outcome):
                running[e.job] = asyncio.create_task(run_one(e, sem, now, last_outcome))
        await sleep(min(60.0, 60 - now.second))
    for t in list(running.values()) + [news_task]:
        t.cancel()      # cancel() ở đây chỉ huỷ task Python; con thật nhận SIGTERM ở §7
    await asyncio.gather(*running.values(), news_task, return_exceptions=True)
```

## 5. Chạy bù — suy từ `ops.etl_run`, 6 luật

Một truy vấn mỗi tick, KHÔNG bảng trạng thái mới:

```sql
SELECT job, status, started_at, finished_at, stats
FROM ops.etl_run
WHERE started_at >= :day_start   -- 00:00 giờ VN hôm nay, quy đổi UTC bằng core.clock
  AND started_at <  :day_end
  AND coalesce(stats->>'intraday','false') <> 'true'
  AND coalesce(stats->>'subset','false')   <> 'true'
  AND coalesce(stats->>'dry_run','false')  <> 'true'
ORDER BY started_at
```

- **Không cần "chạy bù" như một đường code riêng**: `is_due()` chạy y hệt lúc tick bình thường
  lẫn lúc scheduler vừa khởi động lại — nếu mốc 08:00 đã qua và chưa có `success` hôm nay, tick
  ĐẦU TIÊN sau khi container `etl` dựng lại (bất kể do restart hay do khởi động lại có giãn cách)
  sẽ thấy `is_due() == True` và spawn ngay. Đây chính là "chạy bù".
- **Thứ tự phụ thuộc**: `chained` chỉ due khi `latest_success_at(runs_today, e.after)` có giá trị
  — tự nhiên ép snapshot chờ events, fundamentals chờ snapshot, không cần hàng đợi riêng.
- **Nhịp ngắn/`news --loop` không bù**: đúng vì chúng có `kind` khác (`interval`/`loop`), không
  đi qua nhánh `has_success_since`.
- **OMO nhiều mốc chung tên**: mỗi `Entry` tính `since` từ CHÍNH mốc của nó — mốc 15:30 hỏi "có
  success nào SAU 15:30 hôm nay chưa", không quan tâm mốc 11:30 đã chạy.
- **exit 1 không bù lại trong ngày / exit 2 thử lại đúng 1 lần sau 10 phút**: DB không phân biệt
  được exit 1 và 2 (cả hai đều `status='failed'`) — hai luật này cần thông tin CHỈ scheduler vừa
  spawn mới biết (mã thoát thật), nên giữ trong RAM (`last_outcome`), KHÔNG thêm cột:
  ```
  def declined_today(e, since, last_outcome, now):
      prev = last_outcome.get(key(e, since))
      if prev is None: return False
      code, at = prev
      if today_vn(at) != today_vn(now): return False
      if code == 1: return True
      if code == 2: return not (now >= at + timedelta(minutes=RETRY_AFTER_EXIT_2_MIN)
                                 and not retried_flag(e, since, last_outcome))
      return False
  ```
  Giới hạn thật (khai ở §13 rủi ro 1): scheduler restart giữa ngày làm mất trạng thái này — tick
  sau restart có thể thử lại một job đã "declined". Chấp nhận được vì DB vẫn đảm bảo không job nào
  bị bỏ vĩnh viễn — cái mất chỉ là một lần thử thừa, không phải một lần thử thiếu.
- **Backfill giá thứ 7 lỡ mốc thì bù**: cùng cơ chế `is_due` (`kind="weekly"`) — nếu container
  chết đúng 00:05 thứ 7 và dựng lại 09:00 cùng ngày, tick đầu tiên thấy chưa có `success` từ
  00:05 hôm nay ⇒ spawn ngay.

## 6. Chặn chạy chồng — hai lớp

**Lớp 1 (trong job, phủ cả `docker compose run` tay)** — sửa `backend/etl/omo_store.py`, chokepoint
duy nhất 15 job đều gọi:

```python
_LOCKS: dict[int, tuple[sa.Connection, str]] = {}   # run_id -> (connection giữ khoá, job)

def open_run(engine, job: str) -> int:
    lock_conn = engine.connect()                    # checkout RIÊNG, giữ mở suốt đời job
    key = f"etl.{job}"
    locked = lock_conn.execute(sa.text("SELECT pg_try_advisory_lock(hashtext(:k))"), {"k": key}).scalar_one()
    if not locked:
        lock_conn.execute(sa.text(
            "INSERT INTO ops.etl_run (job, status, finished_at, error, stats)"
            " VALUES (:j, 'failed', now(), 'job đang chạy — advisory lock bận', '{\"lock_busy\":true}')"),
            {"j": job})
        lock_conn.commit()
        lock_conn.close()
        log.warning("job %s đang chạy ở tiến trình khác — bỏ lượt này", job)
        raise SystemExit(1)      # BaseException, không bị `except Exception` của job nuốt; sạch, không traceback
    with engine.connect() as c:
        rid = c.execute(sa.text("INSERT INTO ops.etl_run (job) VALUES (:j) RETURNING run_id"), {"j": job}).scalar_one()
        c.commit()
    _LOCKS[rid] = (lock_conn, key)
    return rid

def close_run(engine, run_id, status, stats=None, error=None) -> None:
    ...  # UPDATE như cũ
    conn, key = _LOCKS.pop(run_id, (None, None))
    if conn is not None:
        conn.execute(sa.text("SELECT pg_advisory_unlock(hashtext(:k))"), {"k": key})
        conn.close()
```

`sys.exit(1)` ở nhánh bận KHÔNG cần sửa 15 file job: nó ném ra TRƯỚC dòng `run_id =
omo_store.open_run(...)` return, nằm ngoài mọi `try/except Exception` sẵn có (đúng cấu trúc hiện
tại của `omo_job.py`/`price_job.py`/…), `SystemExit` không phải `Exception` nên xuyên thẳng ra
`main()`, Python tự chuyển thành exit code 1, không traceback. Trùng đúng exit 1 = "guard từ
chối" đã có sẵn trong hợp đồng — scheduler đọc exit 1 thì hiểu "đã có người chạy, không bù trong
ngày" (§5), khớp nghĩa.

Nếu job crash không gọi tới `close_run` (bug hiếm), `_LOCKS` rò một entry trong RAM của TIẾN
TRÌNH JOB (không phải scheduler) — vô hại vì tiến trình đó thoát ngay sau đó; khoá Postgres tự
giải phóng khi `engine.dispose()` ở `finally:` của job đóng hết connection trong pool (ngắt kết
nối = Postgres tự nhả advisory lock theo session).

**Lớp 2 (scheduler)**: dict `running: dict[str, asyncio.Task]` — trước khi tạo task mới cho một
job, kiểm `t.done()`; bận thì bỏ lượt tick này (không log riêng — lớp 1 đã ghi sổ nếu ai đó chạy
tay chồng lên).

## 7. Spawn tiến trình con

```python
def spawn(e: Entry, log_dir: Path) -> subprocess.Popen:
    fname = log_dir / f"{e.job.replace('/', '_')}-{now_vn():%Y%m%d}.log"
    f = open(fname, "a", encoding="utf-8")                     # để rỗng process cha đóng lúc wait() xong
    return subprocess.Popen([sys.executable, "-m", "etl", *e.argv],
                            stdout=f, stderr=subprocess.STDOUT, env=os.environ.copy())

async def run_one(e, sem, when, last_outcome):
    async with sem:
        proc = spawn(e, LOG_DIR)
        code = await asyncio.to_thread(proc.wait)
        print(f"{e.job} {when.isoformat()} exit={code}", flush=True)   # 1 dòng/ lượt, criteria §2.2 luật 4
        last_outcome[key(e, since_of(e, when))] = (code, now_vn())
```

- Lệnh: `[sys.executable, "-m", "etl", *argv]` — `sys.executable` đúng interpreter đang chạy
  scheduler (uv venv native lẫn container), không hardcode `python`.
- `env`: kế thừa `os.environ` của scheduler nguyên vẹn — scheduler tự gọi `core.env.load_dotenv()`
  MỘT lần lúc khởi động (native đọc `.env`; container compose đã bơm nguyên tố + `*_URL` ráp lại
  y hệt mọi job khác).
- stdout/stderr: một file `<job>-YYYYMMDD.log` mỗi ngày trong `ETL_LOG_DIR` (biến MỚI, container
  = `/var/lib/dlck/logs`, native mặc định `REPO_ROOT.parent / "dlck-runtime" / "logs"` — TÁI DÙNG
  đúng thư mục ingester đã dùng, chỉ khác tiền tố tên file, không cần khái niệm thư mục mới).
- Giữ 30 ngày: `prune_logs(log_dir, days=30)` — quét `*-YYYYMMDD.log`, parse ngày từ tên, xoá file
  cũ hơn 30 ngày; gọi 1 lần lúc `main()` khởi động (đủ, vì container sống nhiều ngày liên tục,
  không cần cron riêng).
- Đọc mã thoát: `proc.wait()` trong thread riêng (`asyncio.to_thread`) — không chặn vòng chính.
- Chuyển SIGTERM cho con, chờ ≤ 60 s: khi `stop` được set, với mỗi `Popen` còn sống trong
  `running`: `proc.terminate()` rồi `proc.wait(timeout=60)`; hết giờ thì `proc.kill()`. Khớp
  `stop_grace_period: 60s` sẵn có của service `etl` — KHÔNG cần đổi số này trong compose.
- **Windows native khác gì**: `Popen.terminate()` trên Windows gọi `TerminateProcess` NGAY (không
  có handler SIGTERM để con tự đóng sổ tử tế) — khác POSIX nơi con nhận SIGTERM thật, `core.shutdown`
  của nó nâng thành `KeyboardInterrupt`, đóng sổ `failed: dừng tay` rồi thoát 130 sạch. Trên
  Windows, dừng tay `Ctrl+C` ở cửa sổ chạy `uv run python -m etl` vẫn đi đúng đường (Ctrl+C gửi
  `CTRL_C_EVENT` cho cả cây tiến trình) — chỉ riêng đường "scheduler tự terminate() con" mới cứng
  trên Windows. Vì scheduler native chỉ chạy trên máy dev để thử tay, rủi ro này chấp nhận được.

## 8. `news --loop` như daemon con

```python
async def news_loop_supervisor(e: Entry, stop: asyncio.Event, sleep=asyncio.sleep):
    backoff = 5
    while not stop.is_set():
        proc = spawn(e, LOG_DIR)
        started = time.monotonic()
        code = await wait_or_stop(proc, stop)          # trả sớm nếu stop được set (terminate + wait ≤ 60s)
        if stop.is_set():
            return
        if time.monotonic() - started > 300:            # sống > 5 phút coi như một lượt "ổn", reset backoff
            backoff = 5
        log.warning("news --loop chết (exit %d) — khởi động lại sau %ss", code, backoff)
        await sleep(backoff)
        backoff = min(backoff * 2, 300)
```

Không nằm trong `SCHEDULE`'s `is_due` — `kind="loop"` chỉ để LIỆT KÊ trong bảng lịch cho người đọc
thấy, vòng chính bỏ qua nó tường minh; `main_loop` khởi `news_loop_supervisor` một lần lúc `main()`
chạy, song song với vòng tick.

## 9. Trần tiến trình con đồng thời

`asyncio.Semaphore(CONCURRENCY_CAP)` với `CONCURRENCY_CAP = 6` (hằng số literal ở đầu
`scheduler.py`, đúng số criteria k nêu: `news --loop` + 3 intraday + 1 job ngày + 1 backfill).
`run_one()` await `sem` TRƯỚC khi `spawn()` — job due nhưng hết chỗ thì task Python đã tạo (đứng
trong `running{}`, đã chặn chồng lớp 2) chỉ ĐỢI ở `sem`, không bị bỏ lượt, spawn muộn hơn khi có
chỗ trống. `news --loop` không qua `sem` (daemon con riêng, không được phép bị semaphore chặn —
nó phải luôn sống).

## 10. Thay đổi compose/env/test

- `docker-compose.yml`, service `etl`: thêm `ETL_LOG_DIR: /var/lib/dlck/logs` vào `environment`;
  thêm `- etl_logs:/var/lib/dlck/logs` vào `volumes:`; thêm `etl_logs:` vào khối `volumes:` gốc.
  `command`, `stop_grace_period: 60s` giữ nguyên.
- `.env.example`: thêm dòng `# ETL_LOG_DIR=` cạnh khối `INGESTER_*_DIR` (để trống = mặc định
  native `dlck-runtime/logs`).
- `backend/core/env.py`: `OPTIONAL_KEYS` thêm `"ETL_LOG_DIR"`.
- `backend/tests/docs/test_d03_compose_contract.py`: `ETL_OVERRIDES` thêm
  `"ETL_LOG_DIR": "/var/lib/dlck/logs"`; test mới `test_etl_log_dir_is_a_named_volume` — mirror
  `test_ingester_runtime_dirs_are_named_volumes_and_stop_grace_is_generous`, xác nhận `etl`'s
  `volumes` chứa CẢ `/var/lib/dlck/logs` LẪN `/backups` (etl đã mount `/backups` từ trước).
- `deploy/backend.Dockerfile`: không đổi.

## 11. Seam test — literal, không tautological

`backend/tests/etl/test_scheduler_due.py`:
- `test_daily_job_due_after_its_clock_mark`: `Entry(at=(15,20))`, `now=vn(...,15,21)`, `runs_today={}` ⇒ `is_due(...) is True`.
- `test_daily_job_not_due_before_its_mark`: cùng entry, `now=vn(...,15,19)` ⇒ `False`.
- `test_daily_job_not_due_after_success_today`: `runs_today` có dòng `success` lúc `15:25` ⇒ `is_due(..., now=vn(...,16,0))` `False`.
- `test_omo_marks_are_independent_by_time_not_by_name`: entry mốc `15:30`, `runs_today` chỉ có `success` lúc `11:30` (job cùng tên `macro.omo_crawl`) ⇒ `is_due(..., now=vn(...,15,31))` vẫn `True`.
- `test_workdays_only_skips_saturday`: `now=vn(2026,9,12,9,0)` (thứ 7, đo bằng lịch thật) ⇒ `False` bất kể giờ.
- `test_chained_snapshot_waits_for_events_success`: `runs_today` không có `market.events` success ⇒ `False`; thêm success lúc `18:12` ⇒ `is_due(snapshot, now=vn(...,18,13))` `True`.
- `test_weekly_backfill_only_saturday_after_0005`: `vn(2026,9,12,0,6)` `True`; `vn(2026,9,13,0,6)` (Chủ nhật) `False`.
- `test_exit_1_suppresses_retry_same_day`: `last_outcome[key]=(1, vn(...,15,25))` ⇒ `is_due(..., now=vn(...,20,0))` `False` dù không có `success`.
- `test_exit_2_retries_once_then_stops`: `last_outcome[key]=(2, vn(...,15,20))` ⇒ `False` lúc `15,25`; `True` lúc `15,31` (đủ 10 phút); sau lần retry thứ hai cũng `(2, ...)` ⇒ `False` phần còn lại của ngày.

`backend/tests/etl/test_scheduler_lock.py` (DB test thật, theo `test-strategy.md`):
- `test_open_run_returns_run_id_when_lock_free`: lock trống ⇒ trả `int`, dòng `ops.etl_run` có `status='running'`.
- `test_open_run_exits_1_when_lock_held`: chiếm khoá bằng connection riêng trước, gọi `open_run` ⇒ `pytest.raises(SystemExit) as e; e.value.code == 1`; có dòng `failed` mới với `error` chứa `"đang chạy"`.
- `test_close_run_releases_the_lock`: `close_run` xong, `pg_try_advisory_lock` cùng key từ connection MỚI trả `True`.

`backend/tests/etl/test_scheduler_spawn.py`:
- `test_spawn_writes_to_the_per_job_daily_log_file`: `tmp_path` làm `ETL_LOG_DIR`, entry chạy `sys.executable -c "print('x')"` (giả lập qua `argv` test-only) ⇒ file `<job>-YYYYMMDD.log` chứa `"x\n"`.
- `test_prune_logs_keeps_recent_deletes_old`: tạo `job-20250101.log` (cũ) và `job-<hôm nay>.log` (mới) ⇒ sau `prune_logs(dir, 30)` chỉ còn file mới.

`backend/tests/etl/test_scheduler_concurrency.py`:
- `test_at_most_six_run_at_once`: 10 entry due cùng lúc, `spawn` giả lập ghi mốc bắt đầu/kết thúc vào list dùng `asyncio.sleep(0.05)` thay tiến trình thật ⇒ max đồng thời quan sát được `== 6` (đếm bằng overlap interval, không phải đoán).

`backend/tests/etl/test_scheduler_news_loop.py`:
- `test_restarts_with_growing_backoff`: process giả chết ngay 3 lần liên tiếp ⇒ chuỗi backoff quan sát `[5, 10, 20]` (literal, không suy từ code tính lại).
- `test_stop_event_ends_supervisor_without_restart`: `stop.set()` giữa lúc con đang "chạy" ⇒ supervisor trả về, không spawn thêm lần nào.

Ca biên đã phủ: OMO nhiều mốc cùng tên, thứ 7 vs Chủ nhật, exit 1 vs exit 2, lock bận thật (Postgres), backoff tăng dần rồi reset.

## 12. Ước lượng

- `backend/etl/scheduler.py`: ~230–260 dòng (Entry + SCHEDULE ~60 dòng, is_due/due-helpers ~50,
  truy vấn + spawn + prune ~60, main_loop + news supervisor ~60).
- `backend/etl/omo_store.py`: +35–45 dòng (khoá/giải khoá).
- `backend/etl/__main__.py`: -12 dòng (bỏ heartbeat), +3 dòng (gọi scheduler).
- Xoá `heartbeat.py` (~6 dòng) + `test_heartbeat.py`.
- `docker-compose.yml` +4 dòng, `.env.example` +2, `core/env.py` +1, `test_d03…` +10–15.
- Test mới: 5 file, ~16 case (liệt kê §11).
- Thời gian: ~10–14 giờ một dev quen codebase (TDD từng seam); nếu giao subagent, đủ dài/nhiều
  mục theo bảng CLAUDE.md §4.1 ⇒ giao **Opus ngay từ đầu**, không Sonnet nhiều vòng.

## 13. Rủi ro tự khai (≥ 4) + điều kiện đảo ngược

1. **Trạng thái "đã declined/đã retry" chỉ ở RAM** — scheduler restart giữa ngày làm mất nó; một
   job vừa bị "declined" (exit 1) hoặc đã dùng hết lượt retry (exit 2) có thể bị thử lại sau
   restart. *Đảo ngược*: nếu quan sát thấy nhiều lượt thử thừa không mong muốn trong log, thêm cột
   đếm attempt/declined vào `ops.etl_run.stats` thay vì giữ RAM.
2. **Advisory lock giữ một connection SQLAlchemy checked-out khỏi pool suốt đời job** — job dài
   nhất (`price --backfill`) chiếm 1 slot pool + 1 kết nối Postgres tới ~20 giờ; cộng dồn tới 6
   job đồng thời có thể chạm `max_connections` trên VPS nhỏ. *Đảo ngược*: đo `max_connections`
   thực tế lúc 6 job cùng chạy; nếu sát trần, tách connection giữ khoá khỏi pool chính (raw
   psycopg, tự mở/đóng).
3. **`CONCURRENCY_CAP = 6` là số tĩnh, không đo RAM thật** — VPS ~1,1 GB, mỗi tiến trình Python
   con ước 60–120 MB (criteria: "chưa đo"); 6 job nặng cùng lúc (snapshot + backfill + 3 intraday
   + classify) có thể chạm trần RAM. *Đảo ngược*: đo RSS thật khi 6 job chạy đồng thời trên VPS;
   hạ `CONCURRENCY_CAP` hoặc phân lớp ưu tiên nếu vượt ngân sách.
4. **Không có healthcheck/watchdog cho service `etl`** — nếu vòng chính treo êm (không crash,
   không tick) mà không phải do lỗi code đã biết, không gì phát hiện ngoài quan sát thủ công log
   một dòng/lượt. *Đảo ngược*: nếu từng gặp treo êm thật, thêm file mốc tick cuối +
   `healthcheck:` trong compose.
5. **`news --loop` sống xuyên đêm không tự xoay file log theo ngày lịch** — file mở lúc spawn
   giữ nguyên tên tới lần restart kế (do backoff hoặc chết), khác `ingester`'s
   `_day_log_handler` (mở lại mỗi phiên riêng). Nếu `news --loop` không chết cả tuần, log của
   nhiều ngày dồn vào một file `<ngày spawn>.log`. *Đảo ngược*: nếu cần log đúng theo ngày lịch,
   thêm logic tự reopen theo ngày TRONG chính `etl news --loop` (phía job, ngoài phạm vi lát 13).

## 14. Tự chấm a–k

| # | Điểm | Lý do |
|---|---|---|
| a | ✓✓ | Một nhánh code, native/container không rẽ; `clock` tiêm được, mọi mốc qua `core.clock`. |
| b | ✓✓ | `SCHEDULE` một tuple literal ~35 dòng, đọc trọn màn hình; chỗ chèn lát 14 ghi rõ bằng comment. |
| c | ✓✓ | `sys.executable -m etl <job>`, log 1 file/ngày/job, `proc.wait()` đọc mã thoát, 1 dòng stdout/lượt. |
| d | ✓ | Một SELECT duy nhất trên `ops.etl_run`, không bảng mới; nhưng luật exit-1/exit-2 cần RAM (rủi ro 1) nên không phải song lẻ tuyệt đối bền qua restart. |
| e | ✓ | Hai lớp đúng yêu cầu, lớp 1 nằm ở chokepoint chung (`open_run`) nên phủ cả `docker compose run` tay mà không sửa 15 file job; nhưng connection giữ lâu có rủi ro pool (rủi ro 2). |
| f | ✓ | SIGTERM → `terminate()` → chờ ≤ 60 s khớp `stop_grace_period` sẵn có; sống qua reboot nhờ `restart: unless-stopped` có sẵn; chưa có watchdog treo êm (rủi ro 4). |
| g | ✓✓ | Seam tách bạch (`is_due`/`spawn`/`open_run`), test literal cụ thể liệt kê đủ ở §11, không tautological. |
| h | ✓✓ | Một job lỗi chỉ là một `exit code` trong subprocess cô lập, không văng ngoại lệ vào vòng chính; rollback = một `git revert` (1 file mới + sửa nhỏ rải rác, không đụng logic job). |
| i | ✓✓ | 0 thư viện mới — chỉ `subprocess`, `asyncio`, `sqlalchemy` đã có sẵn trong `pyproject.toml`. |
| j | — | Xem ước lượng cụ thể ở §12 (không phải cột chấm ✓/✗). |
| k | ✓ | `Semaphore(6)` đúng số criteria nêu, hằng số dễ chỉnh; nhưng chưa đo RAM thật trên VPS (rủi ro 3) nên chưa ✓✓. |
