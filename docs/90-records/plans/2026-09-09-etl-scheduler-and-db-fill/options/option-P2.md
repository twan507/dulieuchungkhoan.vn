# Phương án P2 — scheduler `etl` dùng APScheduler 3.x (thư viện lịch chín muồi)

Trục tối ưu: dùng thư viện cron/lịch trưởng thành, tự viết ÍT NHẤT phần "lịch". Không sửa file thật — đây là tài liệu thiết kế.

## 1. Kiến trúc + thư viện

Nhánh không tham số của `python -m etl` (hiện là `_heartbeat_loop`, `backend/etl/__main__.py:19-20`) đổi thành gọi `etl.scheduler.main.run()`. Hàm này dựng MỘT `BlockingScheduler` (APScheduler 3.x), nạp bảng lịch tĩnh từ `table.py`, đăng ký mỗi mốc bằng `CronTrigger`/`IntervalTrigger` với `timezone="Asia/Ho_Chi_Minh"`, rồi `scheduler.start()` — block thread chính, y hệt cách `_heartbeat_loop` block hiện nay. Callback của mỗi trigger là hàm đồng bộ trong `runner.py`: spawn `python -m etl <job> [cờ]` bằng `subprocess.Popen`, chờ thoát, ghi log, đọc mã thoát. `news --loop` KHÔNG qua APScheduler — một thread riêng (`newsloop.py`) giữ sống nó song song với `scheduler.start()`. Chạy bù (`catchup.py`) là một job APScheduler khác (`IntervalTrigger(minutes=5)`) cộng một lời gọi trực tiếp lúc khởi động.

```
python -m etl (không tham số)
        │
        ▼
  etl.scheduler.main.run()
        │
        ├── build.py: SCHEDULE (table.py) → BlockingScheduler.add_job(...) × N
        │        CronTrigger 08:00/15:20/... · IntervalTrigger 5-10 phút (intraday) · IntervalTrigger 5 phút (catchup)
        │
        ├── newsloop.py: thread riêng — Popen "news --loop", restart có giãn cách nếu chết
        │
        └── scheduler.start()  (block)
                 │  mỗi lần trigger bắn
                 ▼
            runner.run_child(spec)  →  Popen("python","-m","etl",*spec.argv)
                 │                         (job tự pg_try_advisory_lock lúc open_run — §6)
                 ├── stdout/stderr → <job>-YYYYMMDD.log trong ETL_LOG_DIR
                 └── đọc returncode → in 1 dòng tóm tắt ra stdout scheduler
```

**Thư viện chọn: APScheduler 3.11.x, `BlockingScheduler` + `CronTrigger`/`IntervalTrigger`, `MemoryJobStore`.**

Vì sao:
- Kiểm PyPI (`pypi.org/pypi/APScheduler/json`, 2026-09-09): bản mới nhất 3.11.3, `requires_python >= 3.8`, classifier liệt kê tường minh Python 3.12 → khớp yêu cầu môi trường. Phụ thuộc lõi chỉ có `tzlocal>=3.0` (SQLAlchemy/Mongo/Redis/etcd… là *extras* tuỳ chọn, không cài) — cài qua `uv add apscheduler` thêm đúng 2 gói (apscheduler + tzlocal) vào `uv.lock`.
- `tzlocal` chỉ dùng khi trigger KHÔNG được truyền `timezone` tường minh (tự dò TZ hệ điều hành). Mọi trigger trong `table.py` truyền `timezone="Asia/Ho_Chi_Minh"` tường minh — nhánh tự dò của `tzlocal` không bao giờ chạy trong code của ta, chỉ tồn tại vì là phụ thuộc bắt buộc của gói.
- Không cần `SQLAlchemyJobStore`: bảng lịch là dữ liệu TĨNH trong code (`table.py`), không phải job động ghi ở DB — `MemoryJobStore` mặc định là đủ; khi tiến trình khởi động lại, lịch được XÂY LẠI TỪ ĐẦU từ `table.py`, không cần bền (persist) qua restart. Điều này đồng thời tránh một phụ thuộc nữa (đã có `sqlalchemy`/`psycopg` trong `pyproject.toml`, nhưng job store SQL kéo theo bảng riêng, migration riêng — không cần cho lịch tĩnh).
- Đã trưởng thành lâu năm (dòng 3.x ổn định từ ~2015, dùng rộng rãi), tài liệu đủ cho `CronTrigger`/`misfire_grace_time`/`coalesce`/`max_instances` — đúng thứ cần, không cần async/persistent (đó là APScheduler 4.x, còn phát triển).

Chưa kiểm (nêu rõ để không giả định):
- Kích thước wheel cụ thể của `apscheduler`+`tzlocal` (ước < 1 MB, chưa cân đo).
- `BlockingScheduler.start()` có tự bắt gọn `KeyboardInterrupt` ném giữa lúc executor thread đang chạy hay không khi handler của `core.shutdown.install_signal_handlers()` đã nâng SIGTERM thành `KeyboardInterrupt` TRƯỚC khi APScheduler cài handler riêng của nó — cần đọc mã nguồn `BlockingScheduler._main_loop`/thứ tự `signal.signal` thật trước khi viết `main.py`, không suy đoán.
- Có patch bảo mật/độ tần suất release của APScheduler 3.x (đang ở chế độ bảo trì, tính năng đóng băng) — chưa tra changelog.

## 2. Danh sách file

Mới:
- `backend/etl/scheduler/__init__.py` — trống, đánh dấu package.
- `backend/etl/scheduler/table.py` — bảng lịch tĩnh (`JobSpec`, `SCHEDULE`) — nguồn sự thật DUY NHẤT của mốc giờ.
- `backend/etl/scheduler/build.py` — dựng `BlockingScheduler` từ `SCHEDULE` (ánh xạ `JobSpec.trigger` → `add_job`).
- `backend/etl/scheduler/chain.py` — `run_events_chain()`: chuỗi events → snapshot → fundamentals, idempotent.
- `backend/etl/scheduler/runner.py` — spawn tiến trình con, ghi log theo ngày, đọc mã thoát, chuyển SIGTERM.
- `backend/etl/scheduler/catchup.py` — suy chạy bù từ `ops.etl_run` theo 6 luật đã chốt.
- `backend/etl/scheduler/lock.py` — `acquire(engine, job)`/`release(conn)` — advisory lock Postgres theo tên job.
- `backend/etl/scheduler/newsloop.py` — supervisor `news --loop`: giữ sống, khởi động lại có giãn cách.
- `backend/etl/scheduler/main.py` — lắp ráp toàn bộ, `run() -> int` gọi từ `__main__.py`.

Sửa:
- `backend/etl/__main__.py` — nhánh `if not args:` gọi `etl.scheduler.main.run()` thay `_heartbeat_loop()` (heartbeat cũ có thể xoá hoặc giữ làm lệnh con `heartbeat` riêng — ngoài phạm vi lát này, chỉ đổi đường mặc định).
- 15 file `etl/*_job.py` (`refdata_job.py`, `screener_job.py`, `events_job.py`, `price_job.py`, `snapshot_job.py`, `fundamentals_job.py`, `wichart_job.py`, `omo_job.py`, `series_job.py` — dùng chung cho fred/fx/lbma/yahoo/binance, `news_job.py`, `news_classify.py`) — bọc `run()`/`run_backfill()` bằng `lock.acquire`/`lock.release` (mẫu ở §6).
- `backend/core/env.py` — thêm `ETL_LOG_DIR` vào `OPTIONAL_KEYS` (dòng 51, cùng nhóm với `INGESTER_LOG_DIR`).
- `docker-compose.yml` — thêm `ETL_LOG_DIR: /var/lib/dlck/etl-logs` vào anchor `x-app-env` (dòng 11-18, theo đúng tiền lệ `INGESTER_LOG_DIR` — khai chung cho mọi service app, dù chỉ `etl` mount volume tương ứng); thêm volume `etl_logs:/var/lib/dlck/etl-logs` vào `services.etl.volumes` (dòng 126-127); khai `etl_logs:` ở khối `volumes:` gốc (dòng 180-186).
- `deploy/backend.Dockerfile` — thêm `/var/lib/dlck/etl-logs` vào `mkdir -p` và `chown -R appuser` (dòng 10).
- `backend/pyproject.toml` — thêm `"apscheduler>=3.10,<4"` vào `dependencies` (dòng 5-17).
- `.env.example` (gốc repo) — thêm dòng `# ETL_LOG_DIR=` cạnh khối `INGESTER_LOG_DIR` (dòng 43-47), cùng chú thích "để trống khi native".
- `backend/tests/docs/test_d03_compose_contract.py` — thêm `ETL_LOG_DIR` vào `OVERRIDES` (dòng 16-20, tự động lan sang `ETL_OVERRIDES` vì spread `{**OVERRIDES, ...}`); thêm một assertion volume cho `etl` tương tự `test_ingester_runtime_dirs_are_named_volumes_and_stop_grace_is_generous` (dòng 72-76).

## 3. Bảng lịch dữ liệu Python

```python
# backend/etl/scheduler/table.py
from dataclasses import dataclass, field
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

VN = "Asia/Ho_Chi_Minh"

@dataclass(frozen=True)
class JobSpec:
    name: str                          # id APScheduler / tên trong log — duy nhất
    argv: tuple[str, ...]              # đuôi lệnh sau "python -m etl"
    ops_jobs: tuple[str, ...] = ()     # tên trong ops.etl_run.job — để catchup dò (chain: nhiều tên)
    trigger: object = None             # CronTrigger | IntervalTrigger | None (None = chain con / daemon)
    catchup_times: tuple[tuple[int, int], ...] = ()   # (giờ, phút) — bản đọc lại được của chính trigger,
                                        # KHÔNG hỏi ngược API nội bộ CronTrigger; test đối chiếu 2 bên khớp nhau
    catchup: bool = True               # luật 6.2: nhịp ngắn (intraday) & news_loop = False
    chain_after: str | None = None     # tên JobSpec đứng trước trong cùng chuỗi (None = job gốc/độc lập)
    once_flag: str | None = None       # backfill thứ 7: tên cờ SQL kiểm tra "đã pass_complete bao giờ chưa"

SCHEDULE: list[JobSpec] = [
    # Ngày làm việc (thứ 2-6, giờ VN)
    JobSpec("refdata", ("refdata",), ("market.refdata",),
            CronTrigger(day_of_week="mon-fri", hour=8, minute=0, timezone=VN), catchup_times=((8, 0),)),
    JobSpec("screener", ("screener",), ("market.screener",),
            CronTrigger(day_of_week="mon-fri", hour=15, minute=20, timezone=VN), catchup_times=((15, 20),)),
    JobSpec("price", ("price",), ("market.price_daily",),
            CronTrigger(day_of_week="mon-fri", hour=15, minute=40, timezone=VN), catchup_times=((15, 40),)),
    # Chuỗi events → snapshot → fundamentals: MỘT trigger (18:10), 2 bước sau là chain_after, không tự có trigger.
    JobSpec("events_chain", ("events",), ("market.events",),
            CronTrigger(day_of_week="mon-fri", hour=18, minute=10, timezone=VN), catchup_times=((18, 10),)),
    JobSpec("snapshot_chain", ("snapshot",), ("market.snapshot",), None, chain_after="events_chain"),
    JobSpec("fundamentals_chain", ("fundamentals",), ("market.fundamentals",), None, chain_after="snapshot_chain"),

    # OMO — mọi ngày, 4 mốc cùng tên ops.etl_run (giờ:phút không cùng khuôn cron → 4 CronTrigger riêng)
    JobSpec("omo_1130", ("omo",), ("macro.omo_crawl",), CronTrigger(hour=11, minute=30, timezone=VN), catchup_times=((11, 30),)),
    JobSpec("omo_1530", ("omo",), ("macro.omo_crawl",), CronTrigger(hour=15, minute=30, timezone=VN), catchup_times=((15, 30),)),
    JobSpec("omo_1800", ("omo",), ("macro.omo_crawl",), CronTrigger(hour=18, minute=0, timezone=VN), catchup_times=((18, 0),)),
    JobSpec("omo_2130", ("omo",), ("macro.omo_crawl",), CronTrigger(hour=21, minute=30, timezone=VN), catchup_times=((21, 30),)),

    # Trọn — mọi ngày
    JobSpec("wichart_full", ("wichart",), ("macro.wichart",), CronTrigger(hour=8, minute=15, timezone=VN), catchup_times=((8, 15),)),
    JobSpec("yahoo_full", ("yahoo",), ("global.yahoo",), CronTrigger(hour=11, minute=0, timezone=VN), catchup_times=((11, 0),)),
    JobSpec("binance_full", ("binance",), ("global.binance",), CronTrigger(hour=7, minute=15, timezone=VN), catchup_times=((7, 15),)),
    JobSpec("fred_0500", ("fred",), ("global.fred",), CronTrigger(hour=5, minute=0, timezone=VN), catchup_times=((5, 0),)),
    JobSpec("fred_2000", ("fred",), ("global.fred",), CronTrigger(hour=20, minute=0, timezone=VN), catchup_times=((20, 0),)),
    JobSpec("fx_2230", ("fx",), ("global.ecb",), CronTrigger(hour=22, minute=30, timezone=VN), catchup_times=((22, 30),)),
    JobSpec("lbma_2230", ("lbma",), ("global.lbma",), CronTrigger(hour=22, minute=30, timezone=VN), catchup_times=((22, 30),)),

    # Nhịp 24/7 — không chạy bù (luật 6.2)
    JobSpec("yahoo_intraday", ("yahoo", "--intraday"), (), IntervalTrigger(minutes=10, timezone=VN), catchup=False),
    JobSpec("binance_intraday", ("binance", "--intraday"), (), IntervalTrigger(minutes=5, timezone=VN), catchup=False),
    JobSpec("wichart_intraday", ("wichart", "--intraday"), (), IntervalTrigger(minutes=5, timezone=VN), catchup=False),

    # classify — 8 mốc mọi ngày (suy luận: criteria không ghi "mọi ngày" tường minh cho classify như omo/wichart;
    # tin tức không nghỉ cuối tuần nên suy daily — CẦN CHỦ DỰ ÁN XÁC NHẬN lúc duyệt spec, không tự chốt)
    *[JobSpec(f"classify_{h:02d}00", ("classify", "--limit", "1000"), ("news.classify",),
              CronTrigger(hour=h, minute=0, timezone=VN), catchup_times=((h, 0),))
      for h in (7, 9, 11, 13, 15, 17, 19, 21)],

    # Backfill giá thứ 7 — tắt vĩnh viễn sau pass_complete lần đầu (cờ suy từ ops.etl_run, không bảng mới — §5)
    JobSpec("price_backfill_sat", ("price", "--backfill", "--stop-before-open"), ("market.price_backfill",),
            CronTrigger(day_of_week="sat", hour=0, minute=5, timezone=VN),
            catchup_times=((0, 5),), once_flag="price_backfill_pass_complete"),

    # Daemon con — ngoài APScheduler, supervise riêng (newsloop.py)
    JobSpec("news_loop", ("news", "--loop"), ("news.collect",), None, catchup=False),

    # --- Lát 14: thêm MỘT dòng JobSpec giám sát tại đây, ví dụ ---
    # JobSpec("monitor", ("monitor",), ("ops.monitor",), CronTrigger(hour=6, minute=30, timezone=VN), catchup_times=((6, 30),)),
]
```

Ánh xạ sang trigger (`build.py`): với mỗi `spec` có `spec.trigger is not None`, gọi
`scheduler.add_job(func=partial(runner.run_child, spec), trigger=spec.trigger, id=spec.name, max_instances=1, coalesce=True, misfire_grace_time=90, replace_existing=True)`.
`spec.chain_after is not None` → KHÔNG `add_job` riêng (không có trigger) — được gọi TRONG `chain.run_events_chain` theo thứ tự cố định `events → snapshot → fundamentals`.
`spec.trigger is None and spec.chain_after is None` (chỉ có `news_loop`) → không qua APScheduler, `main.py` khởi `newsloop.supervise(spec)` trong thread riêng trước khi `scheduler.start()`.
`catchup.py` tự đăng ký thêm một `add_job` với `IntervalTrigger(minutes=5, timezone=VN)`, `id="__catchup__"`, **executor riêng** (`executors={"catchup": ThreadPoolExecutor(1)}`, xem §9) để không bị 5 slot chạy job dài (backfill 20h) chiếm hết.

## 4. Vòng lặp/điều phối

`BlockingScheduler.start()` block thread chính (giữ vòng đời tiến trình, thay cho `while True: sleep(15)` cũ). Mỗi lần trigger bắn, APScheduler tự gọi callback trong `ThreadPoolExecutor` — callback ĐỒNG BỘ, chặn tới khi `subprocess.wait()` xong (không fire-and-forget), nhờ vậy `max_instances=1` của APScheduler (mặc định) tự chặn CHÍNH TRIGGER ĐÓ bắn lần hai khi lần trước còn chạy (log cảnh báo "maximum number of running instances reached" của thư viện — không cần code thêm).

Chuỗi events → snapshot → fundamentals: MỘT job APScheduler (`events_chain`, 18:10). Callback gọi `chain.run_events_chain(engine)` — hàm TỰ VIẾT duyệt 3 bước cố định theo thứ tự; TRƯỚC mỗi bước kiểm `already_succeeded_today(engine, ops_job)`; có rồi thì bỏ qua bước, chưa có thì `runner.run_child`; bước trả rc ∈ {1, 2} (guard-từ-chối hoặc lỗi thật) → DỪNG chuỗi, không chạy bước sau (dữ liệu bước sau phụ thuộc bước trước, chạy tiếp là vô nghĩa). Chọn "một job chuỗi" thay vì ba job APScheduler + `add_listener(EVENT_JOB_EXECUTED)`:
- Không cần học/test cơ chế listener của thư viện (so khớp `job_id`, tránh callback đệ quy khi listener tự `add_job` job kế).
- Hàm chuỗi ĐÃ idempotent (tự kiểm `ops.etl_run` trước mỗi bước) → DÙNG LẠI NGUYÊN VẸN cho catch-up: `catchup.py` gọi lại đúng `run_events_chain`, nó tự biết bước nào còn thiếu — một hàm phục vụ cả lịch đúng giờ lẫn chạy bù, không có hai đường logic phải giữ đồng bộ.

`misfire_grace_time=90`, `coalesce=True` (mặc định) cho MỌI CronTrigger job. Đây là lựa chọn CÓ CHỦ ĐÍCH, không phải quên cấu hình: tiến trình đứng quá 90 giây so với mốc cron ⇒ APScheduler ÂM THẦM BỎ lần bắn đó (không tự chạy trễ); `coalesce=True` gộp nhiều lần lỡ liên tiếp thành một lần bắn duy nhất nếu vẫn còn trong cửa sổ 90s.

**Có mâu thuẫn với 6 luật chạy bù không — CÓ, nếu để APScheduler tự "bù":** thư viện không biết OMO 4 mốc chung tên, không biết bỏ qua `stats.intraday/subset/dry_run`, không biết "guard-từ-chối thì đừng bù", không biết "lỗi thật thì bù đúng 1 lần sau 10 phút", không biết thứ tự phụ thuộc của chuỗi. Nếu để `misfire_grace_time` lớn (vài giờ) cho APScheduler tự chạy bù, nó sẽ chạy lại một job ĐÃ CÓ chạy bù đúng luật từ `catchup.py` — hai cơ chế cùng cố spawn, không cơ chế nào biết cơ chế kia đã làm (advisory lock vẫn chặn ĐỤNG ĐỘ tức thời, nhưng không chặn được việc job chạy 2 lần TUẦN TỰ trong ngày, phá luật "lỗi thật chỉ bù đúng 1 lần"). Vì vậy: `misfire_grace_time` CỐ Ý đặt nhỏ để thư viện gần như không bao giờ tự bù — toàn bộ trách nhiệm chạy bù giao cho `catchup.py` tự viết (§5), chạy trên trigger riêng, đọc thẳng `ops.etl_run`.

## 5. Chạy bù

`catchup.py` chạy: (a) MỘT LẦN ngay khi `main.run()` khởi động (phủ trường hợp process đứng/khởi động lại giữa ngày, sống qua reboot — tiêu chí f), và (b) mỗi 5 phút qua `IntervalTrigger` riêng executor (§3/§9).

Thuật toán mỗi lượt, cho từng `spec` có `spec.catchup=True`:

1. `now = core.clock.now_vn()` (tiêm được qua tham số `clock=` mặc định `now_vn`).
2. Lọc `spec.catchup_times` còn phần tử `(h, m)` mà `dtime(h, m) <= now.time()` (mốc "của hôm nay đã qua"); lấy phần tử LỚN NHẤT (mốc gần nhất đã qua). Không có phần tử nào qua ⇒ bỏ spec này lượt này.
3. Tính `since` — mốc để so `started_at >=`:
   - Job thường (1 mốc/ngày, không phải OMO): `since = datetime.combine(today_vn(), time(0,0), tzinfo=VN)` — luật 2: "chỉ mốc CỦA HÔM NAY".
   - OMO (nhiều mốc chung tên `macro.omo_crawl`): `since = datetime.combine(today_vn(), time(h, m), tzinfo=VN)` — đúng mốc gần nhất đã qua, KHÔNG phải đầu ngày (luật: "bù khi mốc gần nhất đã qua mà chưa có success SAU mốc đó").
   - `price_backfill_sat`: TRƯỚC bước 3, kiểm EXISTS riêng (xem bên dưới) — nếu đã pass_complete bao giờ chưa thì bỏ hẳn spec này (không chạy nữa, mãi mãi).
4. Truy vấn xem đã có success hợp lệ chưa (bỏ qua lượt `--intraday`/`--codes`/`--dry-run` — luật: coi các lượt đó KHÔNG tính):

```sql
SELECT 1 FROM ops.etl_run
WHERE job = :job
  AND status = 'success'
  AND started_at >= :since
  AND (stats->>'intraday') IS DISTINCT FROM 'true'
  AND (stats->>'subset')   IS DISTINCT FROM 'true'
  AND (stats->>'dry_run')  IS DISTINCT FROM 'true'
LIMIT 1
```

   Có dòng ⇒ đã bù, bỏ qua job này lượt này.

5. Chưa có success — kiểm lượt `failed` gần nhất kể từ `since` để phân guard-từ-chối (rc=1) khỏi lỗi thật (rc=2). `ops.etl_run.status` KHÔNG có cột phân biệt hai trường hợp (cả hai đều `status='failed'`) — dựa vào quy ước ĐÃ CÓ SẴN, không phải thêm mới: 8/15 job module (`refdata_job.py:53`, `screener_job.py:49`, `events_job.py:49`, `price_job.py:142`, `snapshot_job.py:139`, `fundamentals_job.py:104`, `wichart_job.py:126`, `series_job.py:143`) đều ghi `error` bắt đầu đúng chuỗi `"guard refused: "` khi từ chối — kiểm bằng `error LIKE 'guard refused:%'`:

```sql
SELECT status, error, started_at FROM ops.etl_run
WHERE job = :job AND started_at >= :since
ORDER BY started_at DESC LIMIT 1
```

   - Dòng mới nhất `status='failed'` và `error LIKE 'guard refused:%'` ⇒ KHÔNG bù (luật "exit 1 không bù lại trong ngày").
   - Dòng mới nhất `status='failed'` và `error` KHÔNG khớp tiền tố trên (lỗi thật, rc=2) ⇒ đếm số lượt `failed` không-guard kể từ `since`: đúng 1 lượt VÀ `now - started_at >= 10 phút` ⇒ bù (chạy lại đúng 1 lần); ≥ 2 lượt ⇒ đã thử lại rồi, THÔI (luật "thử lại đúng 1 lần sau 10 phút rồi thôi").
   - Không có dòng nào (chưa từng chạy hôm nay/mốc này) ⇒ bù ngay.

6. `price_backfill_sat` — cờ `once_flag` không cần bảng trạng thái mới, suy thẳng từ `ops.etl_run`:

```sql
SELECT 1 FROM ops.etl_run
WHERE job = 'market.price_backfill' AND status = 'success'
  AND (stats->>'pass_complete') = 'true'
LIMIT 1
```

   Có dòng (BẤT KỲ LÚC NÀO trong lịch sử, không chỉ hôm nay) ⇒ spec này bị loại khỏi mọi lượt catch-up VÀ khỏi chính trigger thứ 7 (callback tự kiểm câu này trước khi spawn) — tắt vĩnh viễn đúng như chốt "chỉ tới khi pass_complete lần đầu rồi tắt".

7. Job đủ điều kiện bù ở các bước trên ⇒ `runner.run_child(spec)` y hệt đường lịch đúng giờ (dùng chung một hàm, không có "đường bù" riêng biệt cho spawn/log).

Quan hệ với misfire của thư viện: KHÔNG chồng chéo — vì `misfire_grace_time=90s` khiến APScheduler gần như không bao giờ tự bù (mục 4), `catchup.py` là đường bù DUY NHẤT có hiệu lực trong thực tế.

## 6. Chặn chạy chồng

Hai lớp, đúng chốt:

**Lớp trong (Postgres advisory lock, trong job, phủ cả lượt tay):** `lock.py`:

```python
def acquire(engine, job: str) -> Connection | None:
    conn = engine.connect()
    got = conn.execute(sa.text("SELECT pg_try_advisory_lock(hashtext(:j))"), {"j": job}).scalar()
    if not got:
        conn.close()
        return None
    return conn                      # giữ NGUYÊN kết nối mở suốt đời job — khoá session-level tự nhả khi connection đóng

def release(conn: Connection | None) -> None:
    if conn is not None:
        conn.close()                 # đóng session = Postgres tự pg_advisory_unlock_all(); không cần gọi tay
```

Mỗi `*_job.py` bọc `run()` (mẫu, ví dụ `refdata_job.py`):

```python
def run(accept_drop: bool = False) -> int:
    lock_conn = lock.acquire(engine, refdata_store.JOB)
    if lock_conn is None:
        log.info("refdata: lượt khác đang chạy, bỏ qua")
        return 0                     # không ghi ops.etl_run — không có gì "chạy" để ghi sổ
    try:
        ...thân hàm hiện có, không đổi...
    finally:
        lock.release(lock_conn)
```

Vì sao dùng CONNECTION riêng giữ mở (không phải wrap trong `open_run`/`close_run` hiện có ở `omo_store.py`): `omo_store.open_run`/`close_run` mỗi hàm tự mở-đóng connection ngắn hạn (`with engine.connect() as c: ... c.commit()`) — khoá session-level lấy trong đó sẽ NHẢ NGAY khi connection đóng, tức TRƯỚC KHI job thật sự chạy xong. Phải tách lock ra một connection SỐNG SUỐT ĐỜI job, không đụng vào `omo_store.py` (giữ nguyên, không sửa chữ ký `open_run`/`close_run` đang được ~15 file gọi).

Khi bận: job thoát NGAY, KHÔNG ghi `ops.etl_run` (không có gì thật sự "chạy"), exit 0 — không phải lỗi, không cần người nhìn; log 1 dòng vào file `<job>-YYYYMMDD.log` để soát tay khi cần. **Rủi ro tự khai:** đây MỞ RỘNG nghĩa mã 0 (trước là "ghi xong", nay thêm "bỏ qua vì đang bận") — hai tình huống đều "không cần báo động" nên gộp hợp lý, nhưng cần ghi rõ trong `backend/README.md` §Mã thoát khi thực thi thật, và một test literal xác nhận không có dòng `ops.etl_run` mới được tạo khi lock bận (khác `test_e63` vốn luôn kỳ vọng CÓ dòng mới).

**Lớp ngoài (scheduler, trong tiến trình):** `runner.py` giữ `dict[str, subprocess.Popen]` (`_running: dict[str, Popen]`, khoá theo `spec.name` — không phải theo `ops_jobs`, vì `omo_1130`/`omo_1530`/... là 4 `spec.name` khác nhau cùng `ops_jobs`, cố ý KHÔNG coi là "cùng job" ở lớp này vì chúng không bao giờ trùng mốc). TRƯỚC khi spawn: nếu `_running.get(spec.name)` còn sống (`poll() is None`) ⇒ bỏ qua, log, không spawn (tránh phí một lượt kết nối DB/subprocess khi biết chắc đang bận). Đây là "lớp ngoài" TỰ VIẾT (không phải tính năng thư viện) vì nó phải phủ ĐÚNG `spec.name`, còn `max_instances=1` của APScheduler (mục 4) là lớp phòng thủ THỨ BA, miễn phí từ thư viện, chỉ phủ CHÍNH MỘT trigger tự bắn trùng chính nó — không phủ được va chạm giữa lịch đúng giờ và `catchup.py` gọi cùng job (hai trigger APScheduler khác `id`). Ba lớp cộng lại: dict trong tiến trình (rẻ, tức thời) → `max_instances` (miễn phí, cùng trigger) → advisory lock Postgres (đắt hơn nhưng là lớp DUY NHẤT phủ được lượt `docker compose run` thủ công, đúng tiêu chí e).

## 7. Spawn tiến trình con

`runner.py::run_child(spec: JobSpec) -> int`:

```python
def run_child(spec: JobSpec) -> int:
    if _alive(spec.name):
        log.info("%s: còn tiến trình cũ, bỏ qua lượt này", spec.name)
        return 0
    log_path = Path(os.environ["ETL_LOG_DIR"]) / f"{spec.name}-{now_vn():%Y%m%d}.log"
    with open(log_path, "a", encoding="utf-8") as fh:
        proc = subprocess.Popen(["python", "-m", "etl", *spec.argv], stdout=fh, stderr=subprocess.STDOUT)
        _running[spec.name] = proc
        rc = proc.wait()             # đồng bộ — chặn thread executor tới khi con thoát (mục 4)
    del _running[spec.name]
    print(f"[{now_vn():%H:%M:%S}] {spec.name} rc={rc} dur={...}s", flush=True)   # 1 dòng/lượt ra stdout scheduler
    return rc
```

- `stdout`/`stderr` con GỘP CHUNG vào một file `<job>-YYYYMMDD.log` (mở `"a"` — nhiều lượt cùng ngày nối tiếp nhau, không ghi đè; tên file dùng `spec.name`, không phải `ops_jobs`, vì 4 mốc OMO cần 4 file riêng để soát tay theo mốc).
- Giữ 30 ngày: một job dọn RIÊNG (`IntervalTrigger(hours=24)`, chạy trong `main.py`, không phải APScheduler thư viện làm hộ) — quét `ETL_LOG_DIR/*.log`, xoá file có `mtime` quá 30 ngày.
- Mã thoát đọc qua `proc.wait()` — 0/1/2 đã có ý nghĩa theo hợp đồng job; scheduler CHỈ ĐỌC LẠI, không diễn giải thêm (diễn giải "cần báo động không" nằm ở bảng tóm tắt sáng, mục riêng, không phải trong `runner.py`).
- SIGTERM → chuyển cho con: `core.shutdown.install_signal_handlers()` đã nâng SIGTERM/`docker stop` thành `KeyboardInterrupt` trong tiến trình SCHEDULER (cha). Bọc `run_child` bằng `try/except KeyboardInterrupt: proc.terminate(); proc.wait(timeout=60)`; hết 60s con chưa thoát ⇒ `proc.kill()`. Đây là "chuyển tín hiệu" — cha nhận SIGTERM trước, quyết định terminate() con, không dựa vào process-group signal propagation của OS (tránh khác biệt Windows/Linux, xem dưới). Sau khi con thoát (hoặc bị kill), cha `raise` lại `KeyboardInterrupt` để tự thoát 130, đúng hợp đồng có sẵn.
- **Windows native khác gì:** `signal.SIGTERM` không tới handler Python trên Windows (đã ghi ở criteria — Ctrl+C là đường dừng thật). Trên dev Windows, `subprocess.Popen.terminate()` gọi `TerminateProcess` (không phải SIGTERM POSIX) — hoạt động, nhưng con Python KHÔNG có cơ hội chạy `finally`/`except KeyboardInterrupt` của chính nó (terminate cứng, không phải tín hiệu bắt được) — con dừng NGAY, không kịp đóng sổ `ops.etl_run` (`status` treo ở `running`). Đây là bất đối xứng CHẤP NHẬN ĐƯỢC cho dev-only (Windows không chạy production), nhưng phải ghi rõ trong docstring `runner.py` để không ai nhầm hành vi dev = hành vi container. Container (Linux) dùng SIGTERM thật → con vào đúng nhánh `except KeyboardInterrupt` sẵn có, đóng sổ `failed: dừng tay`, exit 130.

## 8. `news --loop` như daemon con

`newsloop.py::supervise(spec)` — thread riêng, khởi trước `scheduler.start()`, vòng lặp:

```python
def supervise(spec: JobSpec, backoff_s: float = 30.0) -> None:
    while not _shutdown.is_set():
        with open(log_path_for_today(spec.name), "a", encoding="utf-8") as fh:
            proc = subprocess.Popen(["python", "-m", "etl", *spec.argv], stdout=fh, stderr=subprocess.STDOUT)
            _running[spec.name] = proc
            rc = proc.wait()
        del _running[spec.name]
        if _shutdown.is_set():
            return
        log.warning("news --loop chết (rc=%d), khởi động lại sau %.0fs", rc, backoff_s)
        _shutdown.wait(backoff_s)     # ngủ tỉnh theo sự kiện dừng, không sleep trần
```

`news --loop` TỰ nó là vòng sống dai (300s/vòng) — `supervise` chỉ giữ nó SỐNG (restart khi tiến trình con chết vì lý do bất kỳ), không gọi từng vòng riêng lẻ (đúng chốt). `_shutdown` là cùng `threading.Event` mà `main.py` set khi nhận SIGTERM (song song với việc dừng `BlockingScheduler`); `terminate()`+`wait(60)` áp y hệt runner.py §7 lên tiến trình `news --loop` đang chạy lúc dừng.

## 9. Trần tiến trình con đồng thời

`BlockingScheduler(executors={"default": ThreadPoolExecutor(5), "catchup": ThreadPoolExecutor(1)})` — **giới hạn bằng cấu hình executor của thư viện**, không tự đếm. `catchup` tách executor riêng (1 slot) để không bị 5 slot "default" chiếm hết bởi job dài (backfill giá ~20h, fundamentals backfill ~1h45) — `catchup.py` khai `add_job(..., executor="catchup")`.

Trần thực tế đồng thời: 5 (default executor, mọi CronTrigger/IntervalTrigger job thường) + 1 (catchup, hiếm khi trùng vì catchup chỉ SPAWN khi có job thiếu, bản thân catchup không giữ slot lâu) + 1 (`news --loop`, NGOÀI APScheduler, thread riêng không cạnh tranh executor) ≈ **6–7**, khớp ước lượng criteria (~6). Ba nhịp intraday (yahoo/binance/wichart, 5-10 phút/lần) mỗi lượt chiếm 1 slot default vài giây tới vài chục giây rồi trả ngay — không phải nguồn nghẽn thật, chỉ job dài (backfill) mới chiếm slot lâu.

## 10. Compose/env/test hợp đồng

- `docker-compose.yml`: `ETL_LOG_DIR: /var/lib/dlck/etl-logs` vào anchor `x-app-env` (áp cho mọi service app, theo đúng tiền lệ `INGESTER_LOG_DIR` — chỉ `etl` thật sự mount, các service khác nhận biến nhưng không dùng, vô hại); `services.etl.volumes` thêm `etl_logs:/var/lib/dlck/etl-logs`; khối `volumes:` gốc thêm `etl_logs:`.
- `deploy/backend.Dockerfile`: `mkdir -p ... /var/lib/dlck/etl-logs ...` + gộp vào `chown -R appuser .../var/lib/dlck...` sẵn có (dòng 10) — KHÔNG cần dòng `chown` mới vì regex test đã bắt cả cụm `/var/lib/dlck`.
- `.env.example`: thêm `# ETL_LOG_DIR=` cạnh khối `INGESTER_LOG_DIR` (dòng 43-47), chú thích giống hệt style "để trống khi native".
- `backend/core/env.py`: `OPTIONAL_KEYS` (dòng 50-53) thêm `"ETL_LOG_DIR"`.
- `backend/pyproject.toml`: `dependencies` thêm `"apscheduler>=3.10,<4"`.
- `backend/tests/docs/test_d03_compose_contract.py`: `OVERRIDES` (dòng 16-20) thêm `"ETL_LOG_DIR": "/var/lib/dlck/etl-logs"` — tự lan sang `ETL_OVERRIDES` qua spread, KHÔNG cần sửa dòng `ETL_OVERRIDES` riêng; thêm hàm test mới `test_etl_log_dir_is_a_named_volume` (đối chứng `services.etl.volumes` có target `/var/lib/dlck/etl-logs`) theo khuôn `test_ingester_runtime_dirs_are_named_volumes_and_stop_grace_is_generous`.
- `backend/README.md` §"Mã thoát": ghi thêm 1 câu — exit 0 khi bị advisory lock chặn (§6) không ghi `ops.etl_run` — để tài liệu sống không nói dối hợp đồng thật (CLAUDE.md §1.1).

## 11. Seam test

- `test_table_catchup_times_match_cron_fields` (mới): với MỌI `spec` có `spec.trigger` là `CronTrigger` VÀ `spec.catchup_times`, đọc `trigger.fields` (đã kiểm tay API này ổn định trước khi viết — nếu không ổn định, thay bằng gọi `trigger.get_next_fire_time(None, vn(2026,9,7,0,0))` và so `.hour/.minute` với phần tử `catchup_times`) — literal: `refdata` phải có đúng `(8, 0)`, `omo_1800` phải có đúng `(18, 0)` (không phải `(18, 30)` — bẫy gõ nhầm minute).
- `test_build_registers_29_apscheduler_jobs` (mới): đếm `scheduler.get_jobs()` sau `build.assemble(SCHEDULE)` — literal `29` (33 `JobSpec` trừ 2 chain-con trừ 1 `news_loop` trừ 1 dòng lát-14 chưa có = đúng số CronTrigger/IntervalTrigger thật sự add_job; con số chốt lại khi viết plan, không đoán ở đây).
- `test_chain_stops_after_events_guard_refused` (mới, seam `chain.run_events_chain`): `spawn=` giả trả `(rc=1, wrote_ops_row=True)` cho bước `events`; assert `snapshot`/`fundamentals` KHÔNG được gọi (danh sách lệnh giả ghi lại chỉ có 1 phần tử `("events",)`).
- `test_chain_skips_step_already_succeeded_today` (mới): `already_succeeded_today` giả trả `True` cho `events` — assert bước `events` KHÔNG spawn, `snapshot` CÓ spawn.
- `test_catchup_omo_bu_theo_moc_gan_nhat_da_qua` (mới, dùng `migrated_engine` thật + `FakeClock` như `test_i16_daemon.py`): chèn tay 1 dòng `ops.etl_run` success cho `macro.omo_crawl` lúc 11:35 (VN), đặt đồng hồ giả 18:30 (VN) — assert `catchup.due_jobs(...)` TRẢ VỀ `omo_1800` (mốc 18:00 chưa có success sau 18:00), KHÔNG trả `omo_1130` (đã có success sau 11:30).
- `test_catchup_guard_refused_khong_bu_lai` (mới): chèn `status='failed', error='guard refused: X'` cho `market.refdata` lúc 08:05 hôm nay; đồng hồ giả 20:00 — assert `refdata` KHÔNG nằm trong `due_jobs(...)`.
- `test_catchup_loi_that_bu_dung_1_lan_sau_10_phut` (mới): 1 dòng `failed, error='RuntimeError: X'` lúc 08:05; đồng hồ giả 08:10 (< 10 phút) — KHÔNG bù; đồng hồ giả 08:20 (≥ 10 phút) — CÓ bù; thêm 1 dòng `failed` thứ 2 lúc 08:25 — đồng hồ giả 09:00 — KHÔNG bù nữa (đã thử đủ 1 lần).
- `test_catchup_price_backfill_tat_vinh_vien_sau_pass_complete` (mới): chèn `success, stats={"pass_complete": true}` cho `market.price_backfill` ở BẤT KỲ thứ 7 nào trong quá khứ — đồng hồ giả một thứ 7 khác, mốc 00:05 đã qua, KHÔNG có success hôm nay — assert `price_backfill_sat` KHÔNG nằm trong `due_jobs`.
- `test_lock_second_acquire_on_same_job_fails_while_first_holds_connection` (mới, cần `migrated_engine` thật — advisory lock không mock được đúng nghĩa, ghi rõ trong test-strategy): mở `conn1 = lock.acquire(engine, "market.refdata")` → không đóng; `conn2 = lock.acquire(engine, "market.refdata")` → assert `conn2 is None`; `lock.release(conn1)`; `conn3 = lock.acquire(engine, "market.refdata")` → assert `conn3 is not None` (khoá nhả đúng lúc đóng connection).
- `test_runner_reads_exit_code_and_writes_daily_log` (mới, `spawn=` giả `subprocess.Popen` bằng fake trả `returncode=2` cố định, không gọi tiến trình thật): assert `run_child(spec)` trả đúng `2`; assert file `<tmp>/<spec.name>-YYYYMMDD.log` tồn tại (dùng `FakeClock` cố định ngày, không `datetime.now()` trần — seam `now=` tiêm được).
- `test_runner_sigterm_terminates_child_within_60s` (mới): fake `Popen` có `terminate()` ghi cờ + `wait(timeout=60)` trả ngay — assert `terminate()` được gọi ĐÚNG 1 LẦN, không gọi `kill()` khi con thoát kịp trong 60s giả lập.
- `test_newsloop_restarts_after_crash_with_backoff` (mới, khuôn `test_i16_daemon.py::FakeClock`): fake `Popen` lần 1 trả `rc=2` ngay, lần 2 (sau backoff) trả `rc=0` rồi set `_shutdown` — assert đúng 2 lần spawn, khoảng cách giữa 2 lần = đúng `backoff_s` literal (không phải "> 0").

Không test tautological: mọi test trên so với LITERAL biết trước (giờ:phút cụ thể, số job cụ thể, mã thoát cụ thể, số lần gọi cụ thể) — không có test nào tính lại kỳ vọng bằng đúng công thức code dùng để sinh nó. Seam đồng hồ: `now_vn`/`clock=` tiêm được ở mọi hàm cần "bây giờ" (`catchup.due_jobs(engine, now=...)`, `runner.run_child(spec, clock=...)`), không phụ thuộc đồng hồ hệ thống hay đồng hồ nội bộ APScheduler.

## 12. Ước lượng

| Hạng mục | Dòng code | Số test | Giờ |
|---|---|---|---|
| `table.py` + `build.py` + `chain.py` | ~290 | 8 | 4 |
| `runner.py` (spawn/log/exit/SIGTERM, ghi chú Windows) | ~120 | 8 | 4 |
| `catchup.py` (6 luật + SQL) | ~150 | 12 | 5 |
| `lock.py` + sửa 15 file `*_job.py` (bọc acquire/release) | ~40 + ~90 (15×6) | 6 | 4 |
| `newsloop.py` | ~60 | 5 | 2 |
| `main.py` (lắp ráp, dọn log 30 ngày, wiring SIGTERM) | ~60 | 3 | 2 |
| compose/Dockerfile/env.py/pyproject/test_d03/.env.example/README | ~40 | 2 | 1.5 |
| Buffer review/tích hợp | — | — | 3 |
| **Tổng** | **~850** | **~44** | **~25.5** |

## 13. Rủi ro tự khai + điều kiện đảo ngược

1. **Đói executor thread:** job dài (backfill 20h) chiếm 1/5 slot `default` cả buổi — nếu 2 job dài trùng ngày (VD backfill giá + backfill fundamentals) chiếm 2/5, các CronTrigger khác vẫn còn 3 slot, chấp nhận được ở quy mô hiện tại; nhưng nếu tương lai thêm nhiều job dài hơn, 5 slot có thể không đủ và các mốc khác bị `misfire_grace_time=90s` ĐÁ MẤT thay vì chờ — `catchup.py` (chạy executor riêng) sẽ bù lại trong ≤5 phút, nhưng đó là "bù", không phải "đúng giờ".
2. **Rủi ro của chính thư viện — APScheduler 3.x đang bảo trì, tính năng đóng băng:** 4.x (async-first, kiến trúc khác hẳn) đang phát triển song song; nếu dự án sau này cần multi-process hoặc job store bền, phải đánh giá lại/migrate, không nâng cấp mượt trong dòng 3.x.
3. **`misfire_grace_time` nhỏ đá mất occurrence hợp lệ:** container khởi động chậm (>90s sau đúng mốc, VD do `depends_on: migrate` chờ lâu) khiến APScheduler bỏ đúng mốc dù không có sự cố thật — CHẤP NHẬN ĐƯỢC vì `catchup.py` bù trong ≤5 phút, nhưng ai đó "sửa cho chắc" bằng cách tăng `misfire_grace_time` lên vài giờ SẼ tạo chạy đôi với `catchup.py` (mục 4) — cần comment cảnh báo tại chỗ khai báo.
4. **Bán kính sửa của advisory lock rộng hơn 1 file:** phủ cả lượt tay (tiêu chí e) buộc sửa `run()` của cả 15 `*_job.py` — quên bọc một job là job đó chỉ còn lớp scheduler (không phủ `docker compose run` thủ công cho riêng job đó); rollback không còn là "1 file xoá" mà là 15 diff nhỏ (vẫn gộp được trong 1 commit/1 `git revert`, nhưng review khó hơn xác nhận đủ 15/15).
5. **`error LIKE 'guard refused:%'` là quy ước chuỗi, không phải cột có kiểu:** ai đó đổi câu chữ tiền tố ở một `*_job.py` trong tương lai (VD dịch lại, thêm dấu) sẽ ÂM THẦM khiến `catchup.py` coi guard-từ-chối là lỗi thật và bù sai luật — không có CHECK constraint nào bảo vệ chuỗi này; test regression khoá tiền tố (mục 11) giảm rủi ro nhưng không loại trừ (test có thể bị sửa cùng lúc bởi cùng người).
6. **`newsloop.py` chạy trong thread riêng của CHÍNH tiến trình scheduler:** nếu thread này tự crash (exception không bắt hết) mà không kéo sập `BlockingScheduler`, `news --loop` biến mất ÂM THẦM trong khi phần còn lại của scheduler báo xanh — cần try/except bọc TOÀN BỘ thân `supervise()` + log mức lỗi rõ ràng, và bảng tóm tắt sáng (đã chốt ở criteria) nên có riêng 1 dòng "news_loop: đang chạy / đã chết lúc HH:MM".

**Điều kiện đảo ngược:** (a) log `misfire`/đói executor tăng đột biến theo quan sát thật → tách thêm executor theo nhóm hoặc tăng `max_workers`; (b) APScheduler 4.x ổn định và dự án cần persistent job store/multi-process → xét migrate 3.x → 4.x, không phải viết lại từ đầu vì `table.py` (dữ liệu lịch) tách biệt khỏi lớp gắn thư viện (`build.py`); (c) `guard refused:` bị đổi chữ ở đâu đó và test regression không bắt kịp → cân nhắc thêm cột `exit_code smallint` vào `ops.etl_run` (migration mới, ngoài phạm vi lát 13).

## 14. Tự chấm a–k

| # | Điểm | Lý do |
|---|---|---|
| a | ✓✓ | Cùng lệnh `python -m etl` cả hai môi trường; mọi trigger `timezone="Asia/Ho_Chi_Minh"` tường minh, không phụ thuộc TZ hệ điều hành/`tzlocal`; `catchup`/`runner` dùng `core.clock.now_vn`, không `datetime.now()` trần. |
| b | ✓ | 33 `JobSpec` đọc tuyến tính, mỗi dòng tự đủ nghĩa, thêm lát 14 = append 1 dòng — nhưng 33 dòng dài hơn nghĩa đen "một màn hình", không cho ✓✓. |
| c | ✓✓ | `runner.py` tự viết trọn, độc lập thư viện: spawn, log `<job>-YYYYMMDD.log`, đọc đủ 0/1/2/130. |
| d | ✓ | Đủ 6 luật bằng SQL trên `ops.etl_run` có sẵn, không bảng mới — nhưng phải dựa vào quy ước chuỗi `guard refused:` (không phải cột có kiểu, rủi ro #5) nên không ✓✓. |
| e | ✓ | Hai lớp đúng chốt (advisory lock trong 15 job + dict trong tiến trình + `max_instances` miễn phí), phủ cả lượt tay — nhưng bán kính sửa 15 file (rủi ro #4) làm phép kiểm "đủ 15/15" tốn công hơn phương án ít điểm chạm. |
| f | ✓✓ | SIGTERM có sẵn từ `core.shutdown`, `runner`/`newsloop` chuyển đúng cho con, chờ ≤60s; `restart: unless-stopped` + catch-up chạy ngay lúc khởi động → đúng luật khi sống qua reboot/scheduler chết. |
| g | ✓ | Mọi seam tiêm được (clock, spawn giả, `migrated_engine` thật) và literal — trừ `lock.py` cần Postgres thật (không mock được đúng nghĩa advisory lock), chi phí test cao hơn thuần đơn vị. |
| h | ~ | Một job lỗi không đổ scheduler (bọc try/except ở `runner`/`chain`, APScheduler tự bắt exception trong callback) — nhưng 15 diff nhỏ ở `*_job.py` khiến "một `git revert`" đúng về mặt kỹ thuật (1 commit) nhưng rộng về diện review hơn phương án gói gọn trong 1 thư mục mới. |
| i | ✓✓ | Đúng 1 phụ thuộc mới (`apscheduler`, kéo `tzlocal`) — biện minh cụ thể: bản, `requires_python`, classifier 3.12, không extras nặng, cài qua `uv add` một lệnh. |
| j | ✓ | Ước lượng cụ thể: ~850 dòng code, ~44 test, ~25.5 giờ — đủ chi tiết để lên plan, không phải số tròn đoán. |
| k | ✓✓ | `ThreadPoolExecutor(5)` + `ThreadPoolExecutor(1)` cho catchup — giới hạn bằng CẤU HÌNH thư viện, không tự đếm; `news --loop` ngoài executor, cộng vào đúng ~6-7 như ước lượng criteria. |
