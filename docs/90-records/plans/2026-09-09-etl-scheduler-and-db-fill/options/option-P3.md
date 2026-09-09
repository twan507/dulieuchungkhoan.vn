# Phương án P3 — Scheduler tối ưu bán kính hỏng và độ đúng khi khôi phục

Trục: scheduler KHÔNG giữ trạng thái quyết định trong RAM. Mọi câu "mốc nào tới hạn, mốc nào đã
xong, mốc nào đang chạy" phải suy lại được từ `ops.etl_run` + đồng hồ mỗi nhịp. Trạng thái tiến
trình con (handle `Popen`) là ngoại lệ bắt buộc — không tránh được với bất kỳ supervisor nào — và
được tách khỏi phần quyết định thuần bằng ranh giới module rõ.

## 1. Kiến trúc

```
loop.py (vòng mỏng, đồng bộ)
  │  mỗi nhịp 20s:
  │    now = clock()                              [core.clock.now_vn]
  │    ledger = query_today(engine, now)           [SQL, chỉ đọc]
  │    tasks  = planner.due(SCHEDULE, now, ledger)  [THUẦN]
  │    runner.reconcile(tasks, now)                 [spawn/giám sát/log/lock ngoài]
  │    prune_old_logs(); sleep(20)
  └─ SIGTERM/SIGINT → cờ dừng → runner.shutdown(grace=60s) → thoát

schedule.py   — dữ liệu thuần: List[JobSpec], không hàm nghiệp vụ, không I/O
planner.py    — due(schedule, now_vn, ledger_rows) -> list[Task], THUẦN, 0 I/O
runner.py     — spawn/poll/kill tiến trình con, ghi log theo ngày, dọn log > 30 ngày,
                 trần đồng thời, kiểm "còn sống" trước khi spawn trùng
loop.py       — nối ba module trên với DB thật + đồng hồ thật + tín hiệu hệ điều hành
```

Hợp đồng giữa các module:

- `schedule.py → planner.py`: `list[JobSpec]` (dataclass thuần, xem §3).
- `loop.py → planner.py`: `now_vn: datetime` (có tz) và `ledger_rows: list[LedgerRow]`
  (`LedgerRow` = namedtuple `(job, started_at, finished_at, status, stats, error)`, ánh xạ
  1-1 từ `SELECT` bên dưới — không phải `ops.etl_run` thô).
- `planner.py → runner.py`: `list[Task]` — `Task = (spec: JobSpec, reason: str)`, `reason` chỉ
  để log ("mốc 15:40", "bù mốc 08:00", "thử lại lần 2 sau exit 2", "phiên thứ 7 pass_complete
  chưa xong"). `runner.py` không diễn giải lại `reason`, chỉ in ra.
- `runner.py → hệ điều hành`: `subprocess.Popen([sys.executable, "-m", "etl", *spec.cmd], ...)`.

Tính bất biến khôi phục: `loop.py` khởi động lại (crash, `docker restart`, reboot VPS) → không đọc
gì từ RAM cũ → nhịp đầu tiên gọi lại đúng `due()` với ledger thật → tự vá đúng những gì đã lỡ theo
6 luật ở §5. Không có file trạng thái, không có queue, không có checkpoint riêng của scheduler.

## 2. File mới / sửa

| File | Trách nhiệm |
|---|---|
| `backend/etl/scheduler/__init__.py` | rỗng, đánh dấu package |
| `backend/etl/scheduler/schedule.py` | bảng lịch dạng dữ liệu (`JobSpec`, `SCHEDULE`, hằng trần đồng thời) |
| `backend/etl/scheduler/planner.py` | `due()` thuần + hàm phụ thuần (`day_bounds_utc`, `next_mark_due`, `retry_due`) |
| `backend/etl/scheduler/runner.py` | `Runner` — spawn, log theo ngày, dọn log, trần đồng thời, chặn spawn trùng, tắt sạch |
| `backend/etl/scheduler/loop.py` | `main()` — vòng đồng bộ, đọc ledger thật, nối tín hiệu hệ điều hành |
| `backend/etl/__main__.py` | nhánh không tham số gọi `scheduler.loop.main()` thay vì `_heartbeat_loop()` |
| `backend/etl/omo_store.py` | `open_run` thêm advisory lock (§6); `close_run` không đổi chữ ký |
| `backend/etl/{price,refdata,events,snapshot,fundamentals,screener}_job.py` | 1 dòng: gắn `stats["guard_refused"] = True` trước khi đóng sổ ở nhánh `GuardRefused` (§5) |
| `backend/etl/{omo,refdata,screener,events,price×2,snapshot,fundamentals,wichart,news,series×5}_job.py` | 1 khối 3 dòng: `run_id is None` ⇒ log + `return 1` (§6, 15 điểm gọi `open_run`) |
| `backend/core/env.py` | thêm `ETL_LOG_DIR` vào `OPTIONAL_KEYS` |
| `docker-compose.yml` | service `etl`: thêm `ETL_LOG_DIR: /var/lib/dlck/etl-logs` vào `environment`, thêm volume `etl_logs:/var/lib/dlck/etl-logs`; đổi comment dòng 117 (không đổi `command`) |
| `deploy/backend.Dockerfile` | thêm `/var/lib/dlck/etl-logs` vào danh sách `mkdir`/`chown -R appuser` (test M8 đã quét theo `/var/lib/dlck`, kiểm lại) |
| `.env.example` | thêm khối comment `# ETL_LOG_DIR=` cạnh `INGESTER_LOG_DIR` |
| `backend/tests/docs/test_d03_compose_contract.py` | `ETL_OVERRIDES` thêm `ETL_LOG_DIR`; thêm assert volume `etl_logs` giống kiểu `test_ingester_runtime_dirs_are_named_volumes...` |

Không sửa `backend/etl/heartbeat.py` (chết nhánh nhưng test `tests/test_heartbeat.py` vẫn neo vào
hàm thuần `heartbeat()` — để nguyên, không phải rác của thay đổi này).

## 3. Bảng lịch (`schedule.py`)

```python
from dataclasses import dataclass, field

MON_FRI = (0, 1, 2, 3, 4)
ALL_DAYS = (0, 1, 2, 3, 4, 5, 6)
SAT = (5,)

@dataclass(frozen=True)
class JobSpec:
    name: str                              # tên trong ops.etl_run
    cmd: tuple[str, ...]                   # đối số CLI sau `python -m etl`
    kind: str                              # "daily" | "intraday" | "daemon" | "weekly_once"
    times: tuple[tuple[int, int], ...] = ()   # mốc giờ VN; rỗng = không theo mốc (chain con)
    weekdays: tuple[int, ...] = MON_FRI
    depends_on: str | None = None          # tên job cha phải success HÔM NAY trước khi due
    interval_s: int | None = None          # chỉ kind="intraday"
    once_until_flag: str | None = None     # khoá jsonb trong stats đánh dấu "đã xong vòng" — kind="weekly_once"

MAX_CONCURRENT_CHILDREN = 6   # daemon(1) + intraday(3) + 1 mốc ngày + backfill thứ 7, xem §9

SCHEDULE: list[JobSpec] = [
    JobSpec("market.refdata",       ("refdata",),  "daily", times=((8, 0),)),
    JobSpec("market.screener",      ("screener",), "daily", times=((15, 20),)),
    JobSpec("market.price_daily",   ("price",),    "daily", times=((15, 40),)),
    JobSpec("market.events",        ("events",),   "daily", times=((18, 10),)),
    JobSpec("market.snapshot",      ("snapshot",), "daily", depends_on="market.events"),
    JobSpec("market.fundamentals",  ("fundamentals",), "daily", depends_on="market.snapshot"),

    JobSpec("macro.omo_crawl", ("omo",), "daily", weekdays=ALL_DAYS,
            times=((11, 30), (15, 30), (18, 0), (21, 30))),

    JobSpec("macro.wichart", ("wichart",), "daily", weekdays=ALL_DAYS, times=((8, 15),)),
    JobSpec("global.yahoo",  ("yahoo",),   "daily", weekdays=ALL_DAYS, times=((11, 0),)),
    JobSpec("global.binance",("binance",), "daily", weekdays=ALL_DAYS, times=((7, 15),)),
    JobSpec("global.fred",   ("fred",),    "daily", weekdays=ALL_DAYS, times=((5, 0), (20, 0))),
    JobSpec("global.ecb",    ("fx",),      "daily", weekdays=ALL_DAYS, times=((22, 30),)),
    JobSpec("global.lbma",   ("lbma",),    "daily", weekdays=ALL_DAYS, times=((22, 30),)),

    JobSpec("global.yahoo",   ("yahoo", "--intraday"),   "intraday", weekdays=ALL_DAYS, interval_s=600),
    JobSpec("global.binance", ("binance", "--intraday"), "intraday", weekdays=ALL_DAYS, interval_s=300),
    JobSpec("macro.wichart",  ("wichart", "--intraday"), "intraday", weekdays=ALL_DAYS, interval_s=300),

    JobSpec("news.classify", ("classify", "--limit", "1000"), "daily", weekdays=ALL_DAYS,
            times=((7,0),(9,0),(11,0),(13,0),(15,0),(17,0),(19,0),(21,0))),

    JobSpec("news.collect", ("news", "--loop"), "daemon"),

    JobSpec("market.price_backfill", ("price", "--backfill", "--stop-before-open"),
            "weekly_once", weekdays=SAT, times=((0, 5),), once_until_flag="pass_complete"),

    # lát 14: thêm job giám sát ở đây — một dòng JobSpec, chưa định nghĩa
]
```

Ghi chú: `macro.wichart` và `global.yahoo`/`global.binance` xuất hiện **hai lần** — một `JobSpec`
`kind="daily"` (trọn), một `kind="intraday"` — cùng `name` (đúng "cùng tên job, khác
`stats.intraday`" của criteria). Vì khoá chống chồng ở §6 khoá theo `name`, bản trọn và bản nhịp
ngắn của cùng job **tự động không chạy chồng nhau** — hiệu ứng phụ đúng ý, không phải lỗi.

## 4. Planner — `due()`

```python
LedgerRow = namedtuple("LedgerRow", "job started_at finished_at status stats error")

def day_bounds_utc(now_vn: datetime) -> tuple[datetime, datetime]:
    start = now_vn.replace(hour=0, minute=0, second=0, microsecond=0)
    return start.astimezone(timezone.utc), (start + timedelta(days=1)).astimezone(timezone.utc)

def due(schedule: list[JobSpec], now_vn: datetime, ledger_rows: list[LedgerRow]) -> list[Task]:
    ...
```

`ledger_rows` chỉ chứa các lượt **CANONICAL** của HÔM NAY (giờ VN) — `loop.py` đã lọc
`stats.intraday`/`subset`/`dry_run` ở SQL (§5), planner không thấy chúng. Vì vậy planner không
cần biết ba cờ này tồn tại — seam thuần chỉ xử lý `job/started_at/finished_at/status/stats/error`.

Xử lý theo `kind`:

- **`daily` không `depends_on`** — với mỗi mốc `m` trong `times` đã qua (`now_vn.time() >= m` và
  `now_vn.weekday() in weekdays`): due nếu KHÔNG có `LedgerRow` cùng `job` có
  `status="success"` với `started_at >= mốc m của hôm nay`. Đây là luật "mốc gần nhất đã qua mà
  chưa success sau mốc đó" — áp dụng chung cho job một mốc lẫn OMO bốn mốc (§5.2 criteria).
- **`daily` có `depends_on`, `times=()`** (snapshot, fundamentals) — due nếu job cha có
  `status="success"` hôm nay VÀ chính job này chưa có `status="success"` hôm nay. Không có mốc
  giờ riêng — chuỗi tự chảy theo tốc độ job cha, không đợi đồng hồ.
- **`intraday`** — planner KHÔNG xét (daemon nhịp ngắn nằm ngoài due()/ledger, runner tự gọi theo
  `interval_s` bằng đồng hồ của chính nó — xem §9). `due()` bỏ qua mọi `JobSpec` `kind="intraday"`.
- **`daemon`** — planner KHÔNG xét (giám sát process, không phải lịch — §8).
- **`weekly_once`** — due nếu `now_vn.weekday() in weekdays`, `now_vn.time() >= times[0]`, VÀ
  không có `LedgerRow` `status="success"` hôm nay với `stats[once_until_flag] is True`.

Retry sau exit 2 (áp cho MỌI `daily`/`weekly_once` có mốc): với mốc `m` vừa qua, xét các
`LedgerRow` `status="failed"` có `started_at >= m` **và** `stats.get("guard_refused") is not
True` (tức không phải exit 1 — xem §5 lý do không có cột exit_code):
- 0 dòng thất-bại-thật kể từ `m` ⇒ due ngay khi qua mốc (nhánh trên).
- đúng 1 dòng, và `now_vn >= dòng.started_at + 10 phút` ⇒ due (đây là lần thử lại).
- ≥ 2 dòng ⇒ KHÔNG due nữa hôm nay (đã thử lại đúng 1 lần).
- Có `LedgerRow` `status="failed"` với `stats.guard_refused is True` kể từ `m` ⇒ KHÔNG due (exit 1
  không bù lại trong ngày).

`Task.reason` ghi rõ nhánh nào tạo ra due (ví dụ `"bù mốc 15:40"` / `"thử lại lần 2 sau exit 2 lúc
14:12"` / `"chuỗi: cha market.events đã success"`).

**6 ca literal bắt buộc cho `due()`** (chi tiết seam ở §11): (1) mốc đã qua chưa chạy ⇒ due;
(2) mốc đã qua đã success ⇒ không due; (3) OMO bốn mốc — mốc 15:30 qua, chỉ có success sau 11:30
⇒ due lại cho mốc 15:30; (4) snapshot due khi events success, không due khi events chưa chạy;
(5) exit 2 lúc 15:41, giờ hiện tại 15:49 (< 10 phút) ⇒ chưa due; 15:52 (≥ 10 phút) ⇒ due;
(6) thứ 7 đã có success với `pass_complete=True` ⇒ không due dù chưa tới lần chạy tiếp theo.

## 5. Chạy bù — suy từ `ops.etl_run`, không giữ RAM

```sql
SELECT job, started_at, finished_at, status, stats, error
FROM ops.etl_run
WHERE started_at >= :day_start_utc AND started_at < :day_end_utc
  AND job = ANY(:job_names)
  AND coalesce(stats->>'intraday', 'false') <> 'true'
  AND coalesce(stats->>'subset', 'false')   <> 'true'
  AND coalesce(stats->>'dry_run', 'false')  <> 'true'
ORDER BY job, started_at;
```

`day_start_utc`/`day_end_utc` từ `planner.day_bounds_utc(now_vn)` — `loop.py` tính rồi truyền vào
SQL, không tính lại trong DB (Postgres giữ UTC, quy đổi phải làm ở Python theo `core.clock`).

**Vấn đề đã kiểm, phải nói rõ:** `ops.etl_run` **không có cột exit_code** — chỉ `status
∈ {running,success,failed}` và `error` text. `GuardRefused` (exit 1) và lỗi thật (exit 2) CÙNG
đóng `status="failed"`, phân biệt duy nhất là tiền tố chuỗi `error` ("guard refused: …" so với
"RuntimeError: …") — suy từ chuỗi lỗi là mong manh, không phải hợp đồng. Vì vậy P3 thêm một khoá
`stats.guard_refused = true` vào ĐÚNG 6 nhánh `except GuardRefused` đã có sẵn (bảng §2) — đây là
trường có cấu trúc, planner đọc `stats` (đã là jsonb) thay vì string-match `error`. Việc thêm này
KHÔNG động tới nghiệp vụ, không động tới hợp đồng exit code hiện có (`test_e63` không đổi).

Job không có guard (`omo`, `wichart`, `fred`/`fx`/`lbma`/`yahoo`/`binance`, `news`) không có nhánh
`GuardRefused` — mọi `status="failed"` của chúng LUÔN là exit 2 thật, luật retry ở §4 áp thẳng,
không cần cờ.

Không có bảng trạng thái mới, không có cột mới, không có file JSON side-car. Trạng thái duy nhất
scheduler tin là `ops.etl_run`.

## 6. Chặn chạy chồng — hai lớp

**Lớp trong (job, phủ cả `docker compose run --rm etl … <job>` tay):** advisory lock Postgres đặt
NGAY tại `backend/etl/omo_store.py::open_run` — đây là điểm nghẽn DUY NHẤT mọi 15 họ job đã đi qua
(bảng §2 liệt các nơi gọi). Sửa:

```python
_lock_conns: dict[int, sa.Connection] = {}   # run_id -> connection GIỮ khoá session-level, cùng tiến trình

def open_run(engine, job: str) -> int | None:
    conn = engine.connect()                  # KHÔNG dùng `with` — phải sống hết đời job
    got = conn.execute(sa.text("SELECT pg_try_advisory_lock(hashtext(:j)::bigint)"),
                       {"j": job}).scalar_one()
    if not got:
        conn.close()                         # đóng phiên = tự nhả khoá phía Postgres
        return None                          # KHÔNG insert ops.etl_run — lượt bận không để lại dòng nào
    rid = conn.execute(sa.text("INSERT INTO ops.etl_run (job) VALUES (:j) RETURNING run_id"),
                       {"j": job}).scalar_one()
    conn.commit()
    _lock_conns[rid] = conn
    return rid
```

`close_run` thêm 2 dòng cuối: `conn = _lock_conns.pop(run_id, None); if conn: conn.close()` —
đóng phiên tự nhả `pg_try_advisory_lock` (khoá session-level, không cần gọi `pg_advisory_unlock`
tường minh). Khoá theo `hashtext(job)` — cùng tên job (kể cả biến thể trọn/`--intraday`, xem §3)
dùng chung một khoá, đúng ý "theo tên job".

**Hành vi khi bận:** không ghi sổ (return `None` trước INSERT) — caller in một dòng log rồi
`return 1`. Sổ `ops.etl_run` không có dòng rác cho những lần chạm khoá hụt, giữ `stats
.guard_refused` sạch nghĩa cho §5.

Mỗi trong 15 điểm gọi `open_run` (bảng §2) thêm:
```python
run_id = omo_store.open_run(engine, JOB)
if run_id is None:
    log.warning("%s: đang bị lượt khác giữ khoá — bỏ lượt này", JOB)
    return 1
```

**Lớp ngoài (runner, trong tiến trình scheduler):** `Runner` giữ `dict[str, Popen]` khoá theo
`spec.name`; trước khi spawn một `Task`, nếu đã có `Popen` cho `task.spec.name` và
`.poll() is None` (còn sống) ⇒ bỏ qua, không spawn, log 1 dòng. Lớp này không thay được lớp trong
(không phủ lượt tay), chỉ tránh scheduler tự đâm lệnh hai lần trong cùng tiến trình của chính nó.

**Dòng `running` treo sau khi bị giết cứng (kill -9, mất điện):** phiên Postgres của tiến trình đó
đã chết ⇒ khoá advisory tự nhả (Postgres nhả khoá khi phiên đóng, kể cả đóng đột ngột) ⇒ lượt kế
tiếp giành khoá bình thường, KHÔNG bị chặn. Dòng `status='running'` cũ của nạn nhân **treo vĩnh
viễn** trong `ops.etl_run` — đây là dấu vết pháp y, không phải lỗi chức năng: `due()` chỉ tìm
`status='success'`, một dòng `running` mồ côi không chặn cũng không kích hoạt gì. Dọn dòng mồ côi
này (đánh dấu `failed: orphaned`) là việc của lát 14 (job giám sát) — ghi vào §13 như giới hạn đã
biết, không tự vá ở P3.

## 7. Runner — spawn, log, dừng

Spawn: `subprocess.Popen([sys.executable, "-m", "etl", *spec.cmd], cwd=BACKEND_DIR, env=os.environ,
stdout=logfile_fh, stderr=subprocess.STDOUT, start_new_session=True)` (POSIX) — `env=os.environ`
kế thừa nguyên vẹn (URL, secrets đã có sẵn trong tiến trình scheduler, không lắp lại).

Log: `logfile_fh = open(ETL_LOG_DIR / f"{spec.name}-{today_vn():%Y%m%d}.log", "a", encoding="utf-8")`
— job trọn và job `--intraday` cùng tên ghi chung một file theo ngày (đúng bảng lịch §3). Dọn > 30
ngày: mỗi nhịp, `runner.prune_old_logs()` quét `ETL_LOG_DIR.glob("*-*.log")`, xoá file có
`mtime` > 30 ngày — cùng khuôn `ingester.measure.prune_old`, không thư viện mới.

Đọc mã thoát: mỗi nhịp `loop.py`, với mỗi `Popen` đang giữ, gọi `.poll()`; khác `None` ⇒ tiến
trình đã thoát, đóng `logfile_fh`, gỡ khỏi dict sống, log một dòng
`"<job> mã <rc> sau <giây>s"`. Đây là dòng stdout tóm tắt mỗi lượt theo criteria §4 mục 4.

Dừng sạch: `loop.py` bắt SIGTERM/SIGINT bằng `signal.signal` đặt cờ module-level (KHÔNG dùng
`core.shutdown.install_signal_handlers` — hàm đó `raise KeyboardInterrupt` ngay lập tức, hợp cho
một job đơn; scheduler cần đóng TỪNG con có trật tự trước khi tự thoát, nên cần handler đặt cờ rồi
xử lý ở vòng chính, không unwind ngay tại chỗ nhận tín hiệu). Khi cờ bật: với mỗi `Popen` còn sống,
POSIX gửi `SIGTERM` (`proc.terminate()`), Windows gửi `CTRL_BREAK_EVENT` (cần spawn với
`creationflags=CREATE_NEW_PROCESS_GROUP`) rồi `proc.send_signal(signal.CTRL_BREAK_EVENT)`; đợi tối
đa 60s (khớp `stop_grace_period: 60s` của service `etl`), con nào chưa thoát thì `proc.kill()`.
`daemon` (`news --loop`) dừng CÙNG đường này, không có xử lý riêng — con của nó tự có
`except KeyboardInterrupt` cho SIGINT/Ctrl+C, còn SIGTERM Linux đi qua `core.shutdown` của chính
tiến trình `news` (đã có sẵn, không đổi).

**Windows native khác gì:** `core/shutdown.py` đã ghi chú SIGTERM không tới được handler Python
trên Windows — hạn chế CHUNG của cả `ingester` lẫn `etl`, không phải riêng scheduler. Trên dev
Windows, dừng scheduler bằng Ctrl+C (SIGINT, có tới); dừng MỘT con cụ thể dùng `CTRL_BREAK_EVENT`
(hoạt động nếu con được spawn với `CREATE_NEW_PROCESS_GROUP` — nếu không, rơi thẳng xuống
`proc.terminate()` cứng, con mất cơ hội đóng sổ sạch, dòng `status='failed': dừng tay` không được
ghi, để lại `running` treo — chấp nhận được vì native chỉ dùng cho dev, production chạy Docker/Linux
theo bảng §5 môi trường của CLAUDE.md).

## 8. `news --loop` như daemon con

Runner không đọc `ops.etl_run` để quyết có giữ daemon sống hay không — mỗi vòng bên trong
`news --loop` tự mở/đóng MỘT dòng `ops.etl_run` (đã thấy ở `news_job.py::_one_cycle`), nên ledger
chỉ có LỊCH SỬ các vòng đã xong, không nói được "tiến trình có đang sống ngay bây giờ". Sống-hay-
chết của daemon chỉ suy được từ CHÍNH TIẾN TRÌNH — đúng như criteria gợi ý.

Mỗi nhịp, với `JobSpec kind="daemon"`: nếu chưa có `Popen` hoặc `.poll() is not None` (đã chết) ⇒
spawn lại. Có một biến giãn cách khởi động lại TRONG BỘ NHỚ của `Runner` (không phải quyết định
lịch, chỉ là chống bão restart) — `last_restart_at`, `backoff_s` bắt đầu 30s, nhân đôi tới trần
300s mỗi lần chết lại trong vòng 5 phút kể từ lần restart trước, reset về 30s nếu sống quá 5 phút.
Đây LÀ trạng thái RAM, nhưng vô hại theo trục bài toán: mất nó (scheduler restart) chỉ khiến daemon
được thử spawn lại NGAY thay vì đợi giãn cách — tệ nhất là một đợt restart hơi dày, không sai dữ
liệu, không double-write (khoá advisory theo `job="news.collect"` ở §6 vẫn chặn hai tiến trình
`news --loop` ghi chồng nếu có).

## 9. Trần tiến trình con đồng thời

`MAX_CONCURRENT_CHILDREN = 6` (schedule.py). `Runner.reconcile(tasks, now)`:
1. Đảm bảo daemon sống (spawn nếu cần) — LUÔN chạy trước, không tính vào phần "còn chỗ" của due-task.
2. Với `tasks` từ `due()` (đã lọc trùng bởi lớp ngoài §6): spawn theo thứ tự `tasks` cho tới khi
   `len(self._live) >= MAX_CONCURRENT_CHILDREN`; phần dư KHÔNG bị huỷ hay xếp hàng — đơn giản
   không spawn nhịp này. Nhịp sau `due()` tính lại, thấy job đó vẫn chưa `success` hôm nay ⇒ vẫn
   nằm trong `tasks` ⇒ được thử spawn lại. Không cần cấu trúc hàng đợi (đúng trục: không giữ gì
   ngoài `ops.etl_run`).
3. Thứ tự `tasks` do `planner.due()` trả về ưu tiên theo `SCHEDULE` — job phụ thuộc
   (`snapshot`/`fundamentals`) đã tự nhiên đứng sau job cha trong danh sách, không cần sắp lại.

Nhịp 20s + trần 6 nghĩa là tình huống tệ nhất (daemon sống + 3 intraday trùng lịch + 1 mốc ngày +
backfill thứ 7) khớp đúng ước tính criteria — không đặt trần rời cho từng loại.

## 10. Thay đổi compose / env / test hợp đồng

- `docker-compose.yml` service `etl`: thêm `ETL_LOG_DIR: /var/lib/dlck/etl-logs` vào block
  `environment` (giữ `<<: *app-env` rồi override thêm, đúng khuôn `CLICKHOUSE_BACKUP_DIR` đã có);
  thêm `- etl_logs:/var/lib/dlck/etl-logs` vào `volumes`; thêm `etl_logs:` vào khối `volumes:` gốc.
  KHÔNG đổi `command` (đã là `["python", "-m", "etl"]`, nhánh không tham số bên trong đổi hành vi,
  không đổi giá trị YAML) — chỉ sửa dòng comment giải thích ở trên service.
- `backend/core/env.py`: `OPTIONAL_KEYS` thêm `"ETL_LOG_DIR"`.
- `backend/etl/scheduler/loop.py` đọc `ETL_LOG_DIR` theo đúng khuôn `ingester/config.py`:
  `Path(os.environ.get("ETL_LOG_DIR") or REPO_ROOT.parent / "dlck-runtime" / "etl-logs")`,
  `mkdir(parents=True, exist_ok=True)`, lỗi `OSError` ⇒ in lý do, exit 2 (khớp hợp đồng khởi động).
- `.env.example`: thêm dòng comment `# ETL_LOG_DIR=` cạnh khối `INGESTER_LOG_DIR` (§4 hiện có).
- `deploy/backend.Dockerfile`: thêm `/var/lib/dlck/etl-logs` vào lệnh `mkdir`/`chown -R appuser`
  hiện có (test `test_image_owns_the_runtime_dirs_for_appuser` phải cập nhật danh sách thư mục
  kiểm — thêm `/var/lib/dlck/etl-logs` vào tuple bốn thư mục đang kiểm).
- `backend/tests/docs/test_d03_compose_contract.py`: `ETL_OVERRIDES` thêm
  `"ETL_LOG_DIR": "/var/lib/dlck/etl-logs"`; thêm một test mới
  `test_etl_log_dir_is_a_named_volume` cùng khuôn `test_ingester_runtime_dirs_are_named_volumes...`
  kiểm `targets == {"/var/lib/dlck/etl-logs"}` (hoặc gộp `/backups` nếu muốn một test, nhưng giữ
  tách để thông điệp lỗi rõ theo đúng file cũ).

## 11. Seam test

Tất cả seam thuần nằm ở `planner.py` — literal, không DB, không đồng hồ thật (`now_vn` truyền tay).

| Test | Literal expected |
|---|---|
| `test_due_fires_once_the_mark_has_passed_with_no_success` | `now=vn(9,9,15,41)`, `ledger=[]` ⇒ `"market.price_daily"` có trong kết quả |
| `test_due_is_silent_once_marked_success_after_the_mark` | thêm `LedgerRow("market.price_daily", started=vn(15,40), status="success", ...)` ⇒ không có trong kết quả |
| `test_omo_four_marks_recatches_the_15_30_slot` | success duy nhất `started_at=vn(11,35)`; `now=vn(15,31)` ⇒ `"macro.omo_crawl"` due (mốc 15:30 chưa có success SAU nó) |
| `test_omo_four_marks_quiet_right_after_a_fresh_success` | success `started_at=vn(15,31)`; `now=vn(15,35)` ⇒ không due |
| `test_snapshot_waits_for_events_success_today` | `ledger` không có `market.events` success ⇒ `market.snapshot` không due dù `now` đã 20:00 |
| `test_snapshot_fires_right_after_events_succeeds` | `ledger=[events success lúc 18,12]`, `now=vn(18,13)` ⇒ `market.snapshot` due |
| `test_exit2_retry_waits_the_full_ten_minutes` | `failed` (không `guard_refused`) `started_at=vn(15,41)`, `now=vn(15,49)` ⇒ không due; `now=vn(15,52)` ⇒ due |
| `test_exit2_retry_happens_at_most_once` | hai dòng `failed` (15:41, 15:53), `now=vn(16,30)` ⇒ không due |
| `test_guard_refused_does_not_retry_same_day` | `failed` với `stats={"guard_refused": True}`, `now=vn(20,0)` ⇒ không due |
| `test_saturday_backfill_stops_after_pass_complete` | `success` với `stats={"pass_complete": True}` lúc 00:07 thứ 7 ⇒ `market.price_backfill` không due dù `now` là 10:00 cùng ngày |
| `test_saturday_backfill_due_at_00_05` | `weekdays=(5,)`, `now=vn(12,9,0,5)` (giả 12/09 là thứ 7), `ledger=[]` ⇒ due |
| `test_intraday_and_daemon_specs_never_appear_in_due` | `SCHEDULE` đủ 19 entry, mọi `now`/`ledger` ⇒ không entry `kind in ("intraday","daemon")` nào lọt vào kết quả |

≥ 6 ca literal đạt (12 test liệt kê). Không test tautological: mọi `now`/`ledger` là literal cụ thể
(giờ, ngày thật của tuần 2026-09-08 như file `test_i16_daemon.py` đã dùng), expected là tên job
literal, không tính lại bằng chính công thức `due()`.

Seam runner (không DB, không mạng): `Runner` nhận `spawn_fn` tiêm được (mặc định
`subprocess.Popen`) — test thay bằng fake trả `FakePopen(pid, poll_sequence=[None, None, 0])`,
kiểm: không spawn trùng khi fake còn "sống"; spawn lại khi fake "chết"; log file mở đúng tên
`<job>-YYYYMMDD.log`; trần 6 chặn spawn thứ 7. Case biên: `poll()` trả `None` mãi (con treo) ⇒
`shutdown()` phải gọi `kill_fn` sau khi hết 60s giả lập (đồng hồ tiêm được, không `time.sleep`
thật trong test).

## 12. Ước lượng

- `schedule.py`: ~70 dòng (data).
- `planner.py`: ~120 dòng (due() + 3 hàm phụ thuần).
- `runner.py`: ~150 dòng (spawn/poll/log/prune/shutdown).
- `loop.py`: ~90 dòng (SQL, vòng, tín hiệu).
- Sửa `omo_store.py`: ~15 dòng đổi.
- 6 nhánh `guard_refused` + 15 guard `run_id is None`: ~20 file × 3 dòng ≈ 60 dòng.
- Compose/env/Dockerfile/`.env.example`/test_d03: ~30 dòng đổi rải rác.
- **Tổng ước ~520 dòng code + đổi**, KHÔNG tính test.
- Test: 12 case planner + ~6 case runner + 2–3 case guard/lock (DB thật, `migrated_engine`) + cập
  nhật `test_d03` (3 assert) ≈ **23 test mới/sửa**.
- Thời gian: planner+schedule (thuần, dễ TDD) ~3h; runner (subprocess, cần seam tiêm cẩn thận)
  ~4h; loop + tín hiệu + Windows nhánh ~2h; sửa 20 file guard/lock (cơ học, lặp) ~2h; compose/test
  hợp đồng ~1.5h; review + sửa vòng 2 ~2h. **Tổng ước ~14–15 giờ** — thuộc nhóm "dài/nhiều mục",
  đúng bảng §4.1 CLAUDE.md, giao Opus ngay từ đầu nếu giao subagent.

## 13. Rủi ro tự khai

1. **Suy exit1/exit2 dựa vào `stats.guard_refused` mới thêm — nếu một job guard sau này quên gắn
   cờ này ở nhánh `GuardRefused` mới, `due()` coi lỗi guard là "lỗi thật" và retry sau 10 phút một
   cách vô ích** (không sai dữ liệu, chỉ phí một lượt gọi nguồn ngoài). Giảm nhẹ: test hợp đồng
   riêng quét `except GuardRefused` trong `backend/etl/*.py` phải luôn kèm `guard_refused=True`
   trước `close_run` — CHƯA viết trong P3 này, nên ghi vào plan nếu chọn phương án này.
2. **Dòng `running` mồ côi tồn tại vĩnh viễn sau kill cứng (§6)** — không sai chức năng nhưng làm
   bẩn `ops.etl_run`, và một truy vấn vận hành ngây thơ đếm "job đang chạy" bằng `status='running'`
   sẽ đếm sai mãi mãi. Dọn thuộc lát 14.
3. **Advisory lock giữ MỘT connection sống suốt đời job (§6)** — job backfill giá chạy ~20 giờ giữ
   một connection Postgres 20 giờ liên tục; nếu Postgres restart/network rớt giữa chừng, connection
   chết, khoá coi như nhả (đúng ý), nhưng job vẫn tưởng mình cầm khoá cho tới khi chạm câu SQL kế
   tiếp và nhận lỗi kết nối — job đó vốn đã có retry riêng (`pool_pre_ping=True`), nhưng KHÔNG có
   cơ chế "giành lại khoá" giữa chừng; một job thứ hai có thể nhảy vào khoảng hở này. Chấp nhận
   được vì cửa sổ hở chỉ mở khi hạ tầng đã hỏng (kịch bản hiếm, không phải vận hành thường).
4. **Trần đồng thời 6 không có cơ chế ưu tiên thật** — nếu OMO (11:30) và price daily (15:40) và
   ba intraday cùng due một nhịp trùng backfill thứ 7 (7 due-task cho 6 chỗ), job đứng cuối
   `SCHEDULE` bị hoãn một nhịp (20s) — vô hại cho hầu hết job nhưng OMO có 4 mốc sít nhau
   (11:30/15:30/18:00/21:30), một lần hoãn hiếm gặp không đáng ngại; chưa đo RAM thật của 6 tiến
   trình Python đồng thời trên VPS 1.1GB đã dùng cho API+ETL+news — có thể cần hạ trần sau khi đo.
5. **`backoff_s` của daemon là trạng thái RAM (§8)** — mất khi scheduler restart, không sai dữ
   liệu nhưng có thể gây một đợt restart dày nếu scheduler tự crash-loop đúng lúc `news --loop`
   cũng đang crash-loop — hai vòng lặp restart chồng nhau. Rủi ro thấp (scheduler crash-loop chưa
   từng xảy ra với vòng thuần đơn giản như `loop.py`).

**Điều kiện đảo ngược:** nếu đo RAM thật thấy 6 tiến trình đồng thời vượt trần VPS, hạ
`MAX_CONCURRENT_CHILDREN` hoặc bỏ song song hoàn toàn (chạy tuần tự) — đổi một hằng số, không đổi
kiến trúc. Nếu về sau cần scheduler CHỦ ĐỘNG huỷ job quá hạn (không chỉ chờ job tự thoát), cần thêm
watchdog timeout ở `runner.py` — chưa cần ở P3 vì mọi job đã có `--max-minutes`/`--stop-before-open`
tự giới hạn.

## 14. Tự chấm

| # | Điểm | Lý do |
|---|---|---|
| a | ✓✓ | Không đổi `command` compose; `loop.py` chỉ gọi `core.clock.now_vn()`, không `datetime.now()` trần; cùng `python -m etl` chạy native lẫn container |
| b | ✓✓ | `SCHEDULE` là một list 19 dòng đọc hết trong một màn hình; thêm lát 14 = một dòng, đã chừa comment chỗ đứng |
| c | ✓✓ | `runner.py` spawn đúng `python -m etl <job>`, log `<job>-YYYYMMDD.log`, đọc `.poll()` đủ 0/1/2/130 và ghi log dòng tóm tắt |
| d | ✓✓ | Không bảng mới; chỉ thêm 1 khoá jsonb `guard_refused` vào `stats` sẵn có, biện minh rõ ở §5 (thay thế string-match mong manh) |
| e | ✓ | Hai lớp đúng yêu cầu, phủ cả lượt tay qua điểm nghẽn chung `open_run`; trừ điểm vì cửa sổ hở hiếm khi Postgres rớt giữa job dài (rủi ro 3) |
| f | ✓✓ | SIGTERM → cờ → forward con → chờ 60s khớp `stop_grace_period`; scheduler chết → Docker `restart: unless-stopped` dựng lại → nhịp đầu gọi `due()` với ledger thật, tự vá |
| g | ✓✓ | 4 module tách bạch, `planner.py` 100% thuần, 12 test literal liệt kê cụ thể ở §11, không tautological |
| h | ✓ | Một job lỗi (exit 2) không đụng scheduler (subprocess cô lập); rollback đổi `command` compose về `["python","-m","etl"]` cũ hoặc revert nhánh — không phải một `git revert` đơn (chạm 20 file guard/lock), nên chỉ ✓ không phải ✓✓ |
| i | ✓✓ | 0 thư viện mới — `subprocess`, `signal`, `sqlalchemy` đều đã có trong `pyproject.toml` |
| j | ~ | ~520 dòng + 23 test + ~14–15 giờ — không nhỏ, nhưng phần lớn là 20 chỗ sửa lặp cơ học (guard `None`), không phải độ khó thiết kế |
| k | ✓✓ | Trần cứng `MAX_CONCURRENT_CHILDREN = 6` đúng số criteria nêu, cơ chế đơn giản (không spawn nếu đầy, thử lại nhịp sau) không cần hàng đợi |
