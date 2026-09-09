# Ledger — lát 12: chạy được trong container

**Nhánh:** `feat/container-runtime` · **Spec:** [`spec.md`](spec.md) · **Plan:** [`plan.md`](plan.md)

Mỗi task ghi output THẬT của bước kiểm (đỏ trước · xanh sau · lệnh nghiệm thu). Không dán giá trị secret.

## Task 0 — xuất phát 2026-09-08

- `git log --oneline -1`: `e1c9c27 docs(plan): slice 12 implementation plan, 12 TDD tasks, with a spec erratum on the seed step`
- `docker ps … | grep infra`: `infra-clickhouse-1 Up 2 days (healthy)` · `infra-postgres-1 Up 2 days (healthy)` · `infra-redis-1 Up 2 days (healthy)` — kho cũ còn chạy, giữ tới Task 9
- `docker volume ls … | grep -E 'infra|dlck'`: `dlck-infra_chdata` `dlck-infra_pgdata` `dlck-infra_redisdata` `infra_chdata` `infra_pgdata` `infra_redisdata` (sáu volume sẽ xoá ở Task 12) · `tutor-infra_pgdata` (**dự án khác, không đụng**)
- `cd backend && uv run pytest tests -q` (kho cũ, `.env` cũ): **`1072 passed, 2 skipped in 92.23s`** — khớp số `database/README.md` sở hữu

Sổ SDD (brief · report · gói diff review) nằm ở scratchpad ngoài repo, đúng luật cấm `.superpowers/` trong repo (CLAUDE.md §4.1).

## Task 1–3 — hình dạng cấu hình P2 (2026-09-08)

- **Task 1** `1182b99` — `core/env.py`: `compose_urls` · `check`; 9 test `test_env.py` (RED `ImportError` → GREEN `11 passed` cùng hai test hợp đồng cũ). Review sạch, 2 Minor để dành.
- **Task 2** `68aa1d5` + `21ef1cc` — `.env.example` nguyên tố + `test_env_contract.py` (4 test; RED 3/4 trên file cũ → GREEN `13 passed`). **Ruling khi thực thi:** bỏ vế cấm mọi khoá đuôi `_URL` (`LLM_BASE_URL` là khoá tuỳ chọn hợp lệ), giữ vế `ASSEMBLED_KEYS` — plan `15f6e71`, `5cf5c52`. Review: 1 Important (docstring lệch phán quyết) → sửa `21ef1cc`, re-review đóng.
- **Task 3** `00a7fde` — conftest đọc `POSTGRES_DB`, tên DB test lấy từ URL và kiểm identifier; `alembic.ini` `prepend_sys_path = backend`; `migrations/env.py`, `ch_migrate.main`, `ch_backup.main` gọi `load_dotenv()`; `resolve_backup_dir` theo gốc repo (2 test literal). Kiểm: `test_t06_backup` + `tests/schema` + hợp đồng env **76 passed**.
- **Giả định spec 2.2.4 ĐÓNG:** từ gốc repo, shell không export biến DB nào, `uv run --project backend alembic -c database/alembic.ini current` in `0020 (head)` — `env.py` tự ráp `DATA_DATABASE_URL`.

## Task 4–5 — múi giờ, tín hiệu dừng, về hưu đồ Windows (2026-09-08)

- **Task 4** `4d0384f` — `core/clock.py` (`VN` · `now_vn` · `today_vn`, naive ⇒ `ValueError`); ba chỗ `date.today()` trần đổi sang `today_vn()` (`refdata_job`, `system_prompt`, `ch_backup.run_backup`); `test_tz_contract` quét 129 file, RED đúng 3 hit → GREEN. Kiểm: `tests/core` + `tests/agent` + `test_e10` + `test_t06` **217 passed**. Ruling: docstring `clock.py` không được viết nguyên `date.today()` vì phép kiểm quét cả docstring. Review sạch, 2 Minor để dành.
- **Task 5** `c9a4998` + `3e4e39d` — `core/shutdown.py` (SIGTERM → `KeyboardInterrupt`), gắn đầu `main()` của `etl`/`ingester`; xoá `core/console.py` + test, `scripts/register-tasks.ps1`, `scripts/stack.mjs`, `stack.test.mjs`, `package.json`; `price_job.banner` → `log.info`. Kiểm: 65 passed, 1 skipped (test SIGTERM tiến trình thật chỉ chạy POSIX). 🔴 **Review bắt được lỗ có sẵn:** `ingester/main.py` không có `except KeyboardInterrupt`, ngoại lệ từ handler thoát thẳng `asyncio.run()` — đuôi phiên (xả hàng đợi, đối chứng) không chạy, với cả Ctrl+C từ trước. **Ruling:** Task 5 chỉ thu hẹp docstring (`3e4e39d`); đường dừng tử tế `install_loop_stop` (tín hiệu → `stop.set()` trên loop) chuyển sang Task 6 — spec có đính chính, plan Task 6 Step 3b (`8c9b806`).

## Task 6 — ingester thành daemon (2026-09-08)

- `b604386` — `SESSION_START` · `next_window` · `daemon` · `install_loop_stop` (Step 3b); `run()` rẽ nhánh: không `--minutes` ⇒ daemon, có ⇒ một phiên có hạn như cũ. RED `ImportError: SESSION_START` → GREEN `tests/ingester` **181 passed, 1 skipped**.
- Implementer tự khai hai lỗi trong thiết kế Step 3b của tôi: (a) `session_timer` và tín hiệu dừng dùng chung một event ⇒ hết phiên là daemon thoát, nhánh "chờ phiên kế" không bao giờ chạy thật; (b) ba test cũ gọi `run("run")` không `minutes` sẽ ngủ tới 08:30 nếu chạy ngoài giờ. **Ruling Step 3c** `21dfdb1`: event `shutdown` (tín hiệu) tách khỏi `stop` của từng phiên, nối bằng `_relay`/`_session_with_relay`, mỗi phiên một `stop` mới; ba test cũ đổi sang `run("run", minutes=1)`.
- Review bắt thêm một Important từ plan: cài `install_loop_stop` trước nhánh chọn chế độ làm `count`/`reconcile` mất đường ngắt trên POSIX. **Ruling Step 3d** `371b427`: chỉ cài ở `run`/`measure`, test dispatcher bằng recorder. Re-review đóng. Kiểm cuối `test_i16` 13 test `-W error` sạch; 3 Minor để dành.
- ⚠️ Nhánh POSIX của `install_loop_stop` (SIGTERM thật → xả + đối chứng) chưa chạy được trên máy dev Windows — nghiệm thu ở Task 10 (AC-SIGTERM trong container).

## Task 7 — image tự đủ, compose gốc, overlay VPS (2026-09-08)

- `7943b72` — `deploy/backend.Dockerfile` context gốc repo (`/app/backend` + `/app/database`, `REPO_ROOT` trong image = `/app` — probe `docker run` in `backend database` rồi `/app`); `.dockerignore` gốc (`.env*`, `backend/tests`, `.venv`, `docs`); `docker-compose.yml` gốc `name: dlck` (9 service, neo `x-app`, 6 volume); `docker-compose.vps.yml` chuyển nguyên từ `deploy/infra`; ba file compose cũ + `backend/.dockerignore` xoá; `pyyaml` vào dev; `test_d03_compose_contract.py` 7 test (RED `FileNotFoundError` → GREEN). `docker compose config --quiet` OK, `docker compose build migrate` OK. Review sạch (reviewer tự chạy lại contract test và `config --quiet`); ghi nhận rác có sẵn: `test_c99_dedup_probe.py:20` import ba tên đã dời khỏi `tests/clickhouse/conftest.py` từ 2026-09-07, chỉ vỡ khi `RUN_PROBE=1` — báo, không sửa (§4.4.3).

## Task 8 — `core.bootstrap` (2026-09-08)

- `9e725d7` — alembic head → `ch_migrate.upgrade` → cấp 4 user login (Postgres: `CREATE ROLE` nếu thiếu, **luôn** `ALTER ROLE … PASSWORD` qua `sql.Literal`, `GRANT`; ClickHouse: `CREATE USER IF NOT EXISTS`, **luôn** `ALTER USER … IDENTIFIED WITH sha256_password`, `GRANT`, `DEFAULT ROLE`) → tự seed lớp 2 khi `security` có dòng mà override rỗng, bằng cách chạy lại **riêng revision `0013`** dưới `Operations.context` (không `downgrade 0012` — với head `0020` lệnh đó xoá dữ liệu tám migration). Test: 5 passed (Postgres `dulieu_test` role `zz_test_*` + ClickHouse tạm), rotation mật khẩu kiểm cả chiều bị từ chối; **giả định spec 2.2.3 ĐÓNG** (`ALTER USER … IDENTIFIED WITH` trên tag `26.3.22.7`). `create_users.sql.example` xoá. Review sạch; reviewer kiểm ba rủi ro nêu tên trên thư viện đã cài (alembic `Operations.context`, psycopg3 `driver_connection` commit chung transaction, escape literal ClickHouse).

## `.env` chuyển sang nguyên tố — 2026-09-08 16:00

Chủ dự án uỷ quyền sửa thẳng `.env`. Script ở scratchpad đọc bản cũ, bóc host/port/user/mật khẩu từ bảy URL sang biến nguyên tố, giữ nguyên hai mật khẩu owner và ba mật khẩu user có trong URL, **sinh mới** `CLICKHOUSE_API_PASSWORD` (`api_reader` chưa từng tồn tại), bỏ 10 khoá cũ (`*_URL` ×7, `APP_ENV`, `LOG_LEVEL`, `COMPOSE_PROFILES`); bản cũ giữ ở `.env.bak-2026-09-08` (gitignore). Không giá trị nào được in. `python -m core.env check` → **`đủ 18 biến bắt buộc, không biến lạ`**. Đối chứng: `test_conftest_env_contract` + `test_env_contract` + `tests/schema/test_s02_identity.py` **12 passed** trên kho cũ qua URL ráp.

## Task 9 — dựng kho mới trên project `dlck` (2026-09-08 16:05–16:12, Thứ Ba, ngoài giờ 08:30–15:05)

**Step 1 — hạ kho cũ, giữ volume:** `docker rm -f infra-postgres-1 infra-redis-1 infra-clickhouse-1` → xoá cả ba; `docker network rm dlck-net` → xoá mạng cũ. `docker ps -a --format '{{.Names}}' | grep -E '^infra-'` → **rỗng**, khớp Expected. Đối chứng không mất volume: `docker volume ls | grep -E 'infra|dlck|tutor'` vẫn đủ sáu volume cũ (`dlck-infra_chdata/pgdata/redisdata`, `infra_chdata/pgdata/redisdata`) + `tutor-infra_pgdata` — không đụng.

**Step 2 — lên (gốc repo, project `dlck`):** `docker compose up -d --build` build xong, tạo lại `dlck-net`; log rút gọn: `clickhouse Healthy` · `redis Healthy` · `migrate Exited` (×2, in log do compose in trùng dòng) · `api/etl/ingester Starting → Started`. `docker compose ps -a`:

```
NAME                IMAGE                                    SERVICE      STATUS
dlck-api-1          dlck-backend                             api          Up
dlck-clickhouse-1   clickhouse/clickhouse-server:26.3.22.7   clickhouse   Up (healthy)
dlck-etl-1          dlck-backend                             etl          Up
dlck-ingester-1     dlck-backend                             ingester     Up
dlck-migrate-1      dlck-backend                             migrate      Exited (0)
dlck-postgres-1     pgvector/pgvector:pg16                   postgres     Up (healthy)
dlck-redis-1        redis:7-alpine                           redis        Up (healthy)
```

Khớp Expected nguyên văn. `docker compose logs migrate`: brief ghi "4 dòng `bootstrap:`" nhưng liệt 5 mục — thực tế **5 dòng**, cả 5 khớp nguyên văn: `bootstrap: postgres migrate xong (head)` · `bootstrap: clickhouse migrate: ['0001_roles', '0002_rt_schema']` · `bootstrap: postgres user: etl_worker, agent_reader` · `bootstrap: clickhouse user: ingester_worker, api_reader` · `bootstrap: seed ngành lớp 2: skipped:security-rong (0 dòng override)` (đúng — `security` rỗng lúc này, chưa chạy refdata).

**Step 3 — AC2 còn lại:** `curl -s http://127.0.0.1:8000/api/healthz` → `{"status":"ok","service":"api"}`. `docker compose logs --tail 3 etl` → `[etl] alive at 2026-09-08T09:07:06...` (heartbeat). `docker compose logs --tail 3 ingester` → `run: ngoài phiên, chờ tới 2026-09-09T08:30:00+07:00`. Cả ba khớp Expected nguyên văn. **→ AC2: PASS.**

**Step 4 — giả định 2.2.1 (one-shot chạy lại ở lần `up` sau):** `docker compose up -d` lần hai, lọc `migrate`: `Recreate → Recreated → Starting → Started → Waiting ×3 → Exited ×3`. `docker compose ps -a migrate` → `dlck-migrate-1 Exited (0) 6 seconds ago` — mốc giờ mới, xác nhận **đã chạy lại**. `docker compose logs migrate | grep -c "bootstrap: seed"` → **1**, không phải `2` như Expected. Lý do: `up` làm **Recreate** (container mới, không phải restart container cũ), nên `docker compose logs` chỉ còn giữ log của container hiện tại — dòng seed của lượt đầu biến mất cùng container bị thay. Đối chứng độc lập không phụ thuộc phép đếm cộng dồn: log lượt hai tự nó có đủ **cả 5 dòng `bootstrap:` tươi** (kể cả `clickhouse migrate: không có gì mới` — khác hẳn lượt 1, đúng vì Postgres/ClickHouse đã ở head), tức toàn bộ script bootstrap chạy lại trọn vẹn chứ không phải một phần bị cache. **→ Giả định 2.2.1: XÁC NHẬN ĐÚNG** (container one-shot chạy lại mỗi lượt `up`, đúng như spec giả định). Phép đếm log cộng dồn trong brief không dùng được vì cách Docker xử lý log khi recreate — đây là phát hiện về phương pháp đo, không phải về hành vi hệ thống; không cần đổi runbook §5.8 sang `docker compose run --rm migrate` (chỉ áp dụng khi **không** chạy lại, không phải trường hợp này).

**Step 5 — danh bạ + seed 161:** `docker compose run --rm etl python -m etl refdata` → `exit=0`; `refdata xong: {'sec_inserted': 2017, 'issuers_inserted': 1550, 'icb_rows': 176, ...}`. `docker compose run --rm migrate` (lượt seed, sau khi `security` đã có dòng) → `bootstrap: seed ngành lớp 2: seeded (161 dòng override)` — khớp nguyên văn Expected, `exit=0`. `psql -c "select count(*) from market.security, market.issuer_industry_override"`:

```
 security | override
----------+----------
     2017 |      161
```

`security` = 2017 (> 1.500) · `override` = 161 đúng. **→ Seed 161: PASS.**

**Step 6 — AC4, ingester ngoài giờ: BLOCKED.** `docker compose run --rm ingester python -m ingester --minutes 2` → traceback Python, dừng ở `logging.FileHandler(...)`:

```
PermissionError: [Errno 13] Permission denied: '/var/lib/dlck/logs/ingester-20260908.log'
exit=1
```

Không có dòng `reconcile: p1=… p2=… ok=…` (crash trước khi tới đó, ngay lúc gắn log-handler đầu phiên). Lệnh dò thêm theo đúng brief (`ls -la /var/lib/dlck/logs /var/lib/dlck/spill`):

```
/var/lib/dlck/logs:
drwxr-xr-x 2 root root 4096 Sep  8 16:06 .
/var/lib/dlck/spill:
drwxr-xr-x 2 root root 4096 Sep  8 16:06 .
```

`tail -5 .../ingester-*.log` → `No such file or directory` (chưa từng tạo được). Cả hai thư mục (volume `ingester_logs`/`ingester_spill`) thuộc `root:root`, mode `755` — không ai khác ghi được. `docker compose run --rm ingester id` → `uid=1000(appuser) gid=1000(appuser)`.

**Chẩn đoán (chỉ đọc, không sửa code):** `deploy/backend.Dockerfile` chỉ `chown -R appuser /app` trước `USER appuser`; ba thư mục runtime `/var/lib/dlck/{logs,measure,spill}` nằm ngoài `/app`, không được tạo/chown trong image — Docker tự tạo mount-point cho named volume mới (`ingester_logs`, `ingester_measure`, `ingester_spill`) với chủ mặc định `root`. Đọc `ingester/main.py`: nhánh `mode=="run"` có `--minutes` (dòng ~782) gọi `_day_log_handler(cfg)` **ngay lập tức** → mọi lượt `--minutes N` đều crash. Nhánh **daemon thật** (không `--minutes`, đang chạy ở service `dlck-ingester-1`, `docker compose logs ingester` chỉ có đúng 1 dòng `run: ngoài phiên, chờ tới …`, container vẫn `Up 3 minutes` không crash) chỉ gọi `_day_log_handler` **bên trong `session()`** (dòng ~783–793) — tức chỉ khi một phiên giao dịch thật bắt đầu. Daemon hiện ngủ "ngoài phiên" nên **chưa chạm bug**, nhưng sẽ chạm **đúng lỗi này** vào phiên kế (08:30 ngày mai) nếu không sửa trước — không phải lỗi riêng của phép thử `--minutes 2`.

**→ AC4: FAIL.** Giả định 2.2.2 (khoá file `SpillStore` trên volume Docker Desktop WSL2) **chưa kiểm được** — crash xảy ra trước khi chạm `SpillStore`, không mở được cũng không đóng được giả định này.

Theo luật nghiệm thu (dừng khi lệch Expected, không tự sửa Dockerfile/code), **dừng tại Step 6** — không chạy Step 7. **→ AC7: CHƯA KIỂM** (bị chặn bởi Step 6, không phải do backup tự nó có vấn đề).

**Việc cần làm tiếp (ngoài phạm vi task này):** `deploy/backend.Dockerfile` cần tạo + `chown -R appuser` ba thư mục `/var/lib/dlck/{logs,measure,spill}` trước dòng `USER appuser` (cùng cách đang làm với `/app`), hoặc một bước chown khi container khởi động. Không sửa ở đây theo đúng ràng buộc "không đổi code ứng dụng" của task vận hành này.

## Task 9a — volume runtime thuộc root, appuser không ghi được (2026-09-08, sau khi Task 9 chặn ở AC4)

- **Sự thật đo (Task 9 Step 6):** probe `ingester --minutes 2` chết `PermissionError … /var/lib/dlck/logs/ingester-20260908.log`, exit 1. Ba volume có tên được Docker tạo `root:root` vì image không có sẵn điểm gắn; container chạy `appuser`. Daemon đang ngủ cũng sẽ chết y hệt lúc 08:30. Lỗ thứ hai: mở file log nằm ngoài hợp đồng khởi động ⇒ traceback exit 1 thay vì 2.
- **Ruling:** plan thêm Task 9a. `1081a3a` — Dockerfile tạo sẵn `/var/lib/dlck/{logs,measure,spill}` + `/backups`, `chown -R appuser`; `main.py` thêm `_attach_day_log` (không mở được log ⇒ in lý do, trả None ⇒ ba đường `reconcile`/`--minutes`/daemon trả **2**); test `test_run_exits_2_when_the_day_log_cannot_be_opened` (RED `OSError` → GREEN) + hợp đồng tĩnh Dockerfile; **23 passed**. Review duyệt; một Important từ plan **để nguyên có lý do**: `chown /backups` trong image vô tác dụng vì `/backups` là bind mount từ host và ingester không gắn nó — vô hại, AC7 là phép kiểm thật cho quyền ghi thư mục host.
- Bước vận hành: `down` → xoá đúng ba volume `dlck_ingester_*` (đo trước: 0 entry, owner root) → `up -d --build` → kiểm `ls -ld` → chạy lại AC4, AC7 (ghi ở mục kế).

## Task 9 (tiếp) — tạo lại volume runtime, AC4, AC7 (2026-09-08 16:33–16:41)

**Dựng lại volume (Task 9a Step 5):** `docker compose down` (không `-v`) → xoá gọn 7 container + mạng `dlck_dlck-net`, không đụng volume nào (đối chứng trước/sau: đủ 12 volume `infra|dlck|tutor`, không thiếu cái nào). `docker volume rm dlck_ingester_logs dlck_ingester_measure dlck_ingester_spill` → xoá đúng ba volume mục tiêu, thành công cả ba; đối chứng sau: còn lại 9 volume, đủ `dlck_pgdata`/`dlck_chdata`/`dlck_redisdata`/ba `infra_*`/ba `dlck-infra_*`/`tutor-infra_pgdata` — không mất cái nào ngoài dự kiến.

`docker compose up -d --build` → build lại image, 7 service lên: `migrate` `Exited (0)`, `postgres`/`redis`/`clickhouse` `(healthy)`, `api`/`etl`/`ingester` `Up`.

`docker compose run --rm ingester sh -c 'ls -ld /var/lib/dlck/logs /var/lib/dlck/measure /var/lib/dlck/spill'`:

```
drwxr-xr-x 2 appuser root 4096 Sep  8 16:36 /var/lib/dlck/logs
drwxr-xr-x 2 appuser root 4096 Sep  8 16:36 /var/lib/dlck/measure
drwxr-xr-x 2 appuser root 4096 Sep  8 16:36 /var/lib/dlck/spill
```

**Lệch Expected:** brief Task 9a dự đoán `appuser appuser` (owner + group); đo được owner=`appuser`, group=`root`. Nguyên nhân: dòng Dockerfile `chown -R appuser /app /var/lib/dlck /backups` chỉ đổi **owner** (không có `:group`), group giữ nguyên `root` từ lúc `mkdir` chạy dưới root. Không dừng ở đây: mode `rwxr-xr-x` cho owner đủ `rwx` bất kể group, nên đây là sai khác vô hại về hiển thị, không phải chặn chức năng — đúng tinh thần CLAUDE.md §3.5 (nghiệm thu bằng cái THỰC SỰ chạy, không bằng trạng thái hiển thị), xác nhận bằng phép đo chức năng thật ngay ở Step 6 dưới đây.

**Step 6 — AC4 (ingester ngoài giờ trong container):**

```
$ docker compose run --rm ingester python -m ingester --minutes 2
2026-09-08 16:38:12,444 INFO httpx HTTP Request: GET https://online.bvsc.com.vn/quotes?symbols=ALL "HTTP/1.1 200 OK"
2026-09-08 16:38:12,610 INFO httpx HTTP Request: GET https://online.bvsc.com.vn/datafeed/instruments "HTTP/1.1 200 OK"
2026-09-08 16:38:12,904 INFO ingester run: 2021 mã, 6081 topic
2026-09-08 16:38:12,905 INFO ingester run chạy tới 2026-09-08T16:40:12.905167+07:00
2026-09-08 16:38:12,996 INFO ingester đã subscribe 6081 topic trong 61 lô
2026-09-08 16:38:13,515 INFO ingester đã init_state (giành leader)
2026-09-08 16:39:12,909 INFO ingester run counters: {'orphan_tmp': 0, 'replay_corrupt': 0, 'seq_collision': 0, 'spill_io_error': 0, 'spill_bytes': 0, 'pending_depth_rows': 0, 'pending_depth_bytes': 0}
2026-09-08 16:40:12,906 INFO ingester run counters: {'orphan_tmp': 0, 'replay_corrupt': 0, 'seq_collision': 0, 'spill_io_error': 0, 'spill_bytes': 0, 'pending_depth_rows': 0, 'pending_depth_bytes': 0}
reconcile: p1=0 p2=0 ok=0
2026-09-08 16:40:13,044 INFO ingester reconcile: p1=0 p2=0 ok=0
exit=0
```

```
$ docker compose run --rm ingester sh -c 'ls -la /var/lib/dlck/logs /var/lib/dlck/spill && tail -5 /var/lib/dlck/logs/ingester-*.log'
/var/lib/dlck/logs:
-rw-r--r-- 1 appuser appuser 1242 Sep  8 16:40 ingester-20260908.log

/var/lib/dlck/spill:
-rw-r--r-- 1 appuser appuser    0 Sep  8 16:38 owner.lock

(tail: 4 dòng run counters/insert percentiles + dòng reconcile cuối, trùng nội dung log ở trên)
exit=0
```

**Verdict: PASS.** exit=0 (trong tập cho phép {0,1}); có dòng `run: 2021 mã, 6081 topic` (khớp mẫu "N mã, M topic"); có `reconcile: p1=0 p2=0 ok=0`; file log (1242 byte) và `owner.lock` đều tồn tại và thuộc `appuser appuser` — file mới tạo lấy group theo gid hiệu lực của appuser chứ không theo group thư mục cha, càng xác nhận group=`root` ở thư mục cha vô hại. `spill_io_error: 0`, không có dòng "lỗi I/O trên thư mục spill", không exit 3. **→ AC4 = PASS.** Giả định 2.2.2 (khoá file `SpillStore` trên volume Docker Desktop WSL2) **đóng**: `owner.lock` tạo/giữ bình thường, `spill_io_error=0`.

**Step 7 — AC7 (backup trong container):**

```
$ docker compose run --rm etl python -m core.ch_backup
backup: ['bar_1m-20260908.zip', 'index_bar_1m-20260908.zip']
exit=0

$ ls deploy/infra/clickhouse-backups | head
(rỗng)
```

**Lệch Expected:** lệnh `ls` đúng theo brief cho thư mục rỗng. Dò thêm (chỉ đọc một khoá không phải secret): `grep -n "^CLICKHOUSE_BACKUP_DIR" .env` → `CLICKHOUSE_BACKUP_DIR=./clickhouse-backups` — `.env` (sau khi chuyển sang hình dạng nguyên tố ở Task 2) ghi đè default của compose (`./deploy/infra/clickhouse-backups`) sang `./clickhouse-backups` tại **gốc repo**; brief Task 9 viết theo default cũ, không tính override này. Kiểm đúng chỗ:

```
$ ls -la ./clickhouse-backups
-rw-r--r-- 1 tuanb 197609 913 Sep  8 16:40 bar_1m-20260908.zip
-rw-r--r-- 1 tuanb 197609 900 Sep  8 16:40 index_bar_1m-20260908.zip
```

Đối chứng thêm bên trong container, `docker compose run --rm etl sh -c 'ls -la /backups'`: đúng hai file `bar_1m-20260908.zip` (913 byte) và `index_bar_1m-20260908.zip` (900 byte), chủ `101:101` — uid của tiến trình `clickhouse-server` (ghi qua lệnh SQL `BACKUP`, không phải tiến trình Python `etl` ghi trực tiếp).

**Verdict: PASS** (đúng chức năng, chỉ lệch địa chỉ thư mục do brief dùng default cũ). `backup: [...]` khớp mẫu Expected; file `.zip` xuất hiện trên host, đúng tại đường dẫn `.env` cấu hình. **→ AC7 = PASS.**

**Việc phát sinh, không thuộc phạm vi task vận hành này (không sửa):** `./clickhouse-backups` ở gốc repo hiện là thư mục chưa track, chưa có trong `.gitignore` — để nguyên, chỉ ghi nhận.

**Tóm tắt:** AC4 = PASS · AC7 = PASS · giả định 2.2.2 đóng. Task 9 (lát 12 "chạy được trong container") hoàn tất cả bốn AC còn lại (AC2, AC4, AC7, seed 161) trên project `dlck`.

**Đính chính sau Task 9 (tiếp), 2026-09-08 16:45 — đường backup.** `.env` cũ mang `CLICKHOUSE_BACKUP_DIR=./clickhouse-backups` (viết cho gốc `deploy/infra` thời compose cũ); từ Task 3 đường tương đối giải theo gốc repo nên AC7 rơi zip vào `./clickhouse-backups` chưa gitignore. Sửa: `.env` → `./deploy/infra/clickhouse-backups` (đường mặc định trong `.env.example`), dời hai zip, `docker compose up -d` tạo lại `clickhouse`/`etl`/`api`/`ingester` (mount đổi), chạy lại `core.ch_backup` trong container → `backup: không có gì mới` (job thấy hai zip ở đúng chỗ). Cây git sạch. Ghi chú thêm từ operator: quyền volume runtime là `appuser:root` (Dockerfile `chown` không có `:group`), đủ để ghi — đã kiểm bằng chính AC4.

## ⏸️ ĐIỂM DỪNG TẠM — 2026-09-08 ~16:50 (hết hạn mức phiên, chủ dự án gọi dừng)

**Xong và đã review:** Task 0–8, 9, 9a (HEAD `1e6e6dc` trên `feat/container-runtime`, chưa merge, chưa push). AC2 · 2.2.1 · seed 161 · AC4 · AC7 đạt (mục trên).

**Đang dở — Task 10:** operator bị ngắt ngay khi bắt đầu họ `events --accept-new`; container `docker compose run` của job đó vẫn chạy lúc dừng (`ops.etl_run`: `market.events | running`). **Khi tiếp tục:** kiểm `select job,status,error from ops.etl_run where job='market.events' order by run_id desc limit 1` — `success` thì tính là xong họ `events`; `running` mà không còn container `dlck-etl-run-*` ⇒ lượt chết giữa chừng, đóng dòng đó tay (`update … set status='failed', error='dừng phiên 2026-09-08'`) rồi chạy lại. Còn lại của AC3 theo thứ tự brief Task 10: `price --codes FPT,VNM` · `snapshot --codes FPT --kinds snapshot` · `fundamentals --codes FPT --kinds bs` · `screener` (ngoài phiên ⇒ exit 1 là đúng) · `omo` · `wichart --keys vang` · `fred --keys DGS10` · `fx` · `lbma` · `yahoo --keys '^GSPC'` · `binance --intraday` · `news --sources cafef` · `classify --limit 1`; rồi AC-SIGTERM (Step 2), AC5 (Step 3), native `omo` (Step 5). **AC6 (Step 4) do trợ lý làm** (chủ dự án đã uỷ quyền sửa `.env`): đổi `ETL_DB_PASSWORD`, `docker compose run --rm migrate`, `run --rm etl python -m etl omo` exit 0.

**Sau đó:** Task 11 (tài liệu sống + "Điểm vào cho lát 13" + cả bộ test = AC8 + số vào `database/README.md`), Task 12 (review toàn nhánh hai trục, gỡ 11 task Windows — chủ dự án, xoá 6 volume cũ `infra_*`/`dlck-infra_*` — không đụng `tutor-infra_pgdata`, build sạch từ clone, khép nhánh).

**Trạng thái máy lúc dừng:** project `dlck` đang chạy (7 service, `migrate` Exited 0); ba container `infra-*` cũ đã gỡ, sáu volume cũ còn nguyên; `.env` hình dạng nguyên tố (`CLICKHOUSE_BACKUP_DIR=./deploy/infra/clickhouse-backups`), bản cũ `.env.bak-2026-09-08`; sổ SDD (brief/report/gói diff) ở scratchpad phiên `24deb585-…`, không trong repo.

## Sổ phán quyết — gom từ sổ SDD (mọi quyết định trợ lý tự ra thay chủ dự án, theo thứ tự)

| # | Ở đâu | Phán quyết | Nếu sai thì mất gì |
|---|---|---|---|
| 1 | Viết plan | Spec §5.4 nói `downgrade 0012 → upgrade head`; head `0020` ⇒ lệnh đó xoá dữ liệu tám migration. Bootstrap chạy **riêng revision `0013`** qua `Operations.context`; spec có đính chính | Cách seed khác chữ README cũ — Task 11 thay README |
| 2 | Tiền kiểm SDD | `.env` là việc chủ dự án, không chặn Task 1–8; sau đó chủ dự án **uỷ quyền trợ lý sửa thẳng** (16:00), chuyển bằng script không in giá trị | — |
| 3 | Task 2 | Bỏ vế cấm mọi khoá đuôi `_URL` (`LLM_BASE_URL` hợp lệ), giữ vế `ASSEMBLED_KEYS`; docstring sửa theo | Khoá `*_URL` mới chỉ bị chặn nếu chưa có trong `KNOWN_KEYS` |
| 4 | Task 3 | Thêm `path_separator = os` vào `alembic.ini` (alembic 1.19 cảnh báo deprecation mỗi lượt) | — |
| 5 | Task 4 | Docstring `core/clock.py` không viết nguyên `date.today()` (phép kiểm quét cả docstring); import module-level ở `ch_backup` | — |
| 6 | Task 5 | Hit grep còn lại là `backend/README.md` (docs, Task 11); gỡ import `sys` mồ côi; docstring `core/shutdown.py` **thu hẹp** vì ingester không có `except KeyboardInterrupt` — đường dừng tử tế chuyển sang Task 6 (`install_loop_stop`), spec có đính chính | Mất hàng đợi RAM chưa xả nếu `install_loop_stop` sai — đã trả bằng Task 6 và đo thật 2026-09-08 21:34 (sửa ô sau review) |
| 7 | Task 6 | Step 3c: tách event `shutdown` (tín hiệu) khỏi `stop` của từng phiên (mốc giờ), relay mỗi phiên; ba test cũ gọi `run("run", minutes=1)`. Step 3d: chỉ cài `install_loop_stop` ở `run`/`measure` để `count`/`reconcile` còn ngắt được | Thêm một task relay mỗi phiên |
| 8 | Task 9 | Chặn ở AC4 ⇒ Task 9a: Dockerfile tạo sẵn và `chown` ba thư mục runtime + `/backups`; mở file log vào hợp đồng exit 2; xoá ba volume `dlck_ingester_*` rỗng rồi tạo lại | Volume tạo lại một lần (rỗng); thêm một đường thoát 2 mới cho ingester (mở log ngày) — `restart: unless-stopped` không phân biệt 2/3 nên chi phí nhỏ (sửa ô sau review) |
| 9 | Task 9a | `chown /backups` trong image vô tác dụng (bind mount) — **giữ, vô hại**; AC7 là phép kiểm thật | Một thư mục thừa trong image |
| 10 | Sau AC7 | `.env` cũ `CLICKHOUSE_BACKUP_DIR=./clickhouse-backups` (gốc `deploy/infra` cũ) ⇒ sửa về `./deploy/infra/clickhouse-backups`, dời zip, tạo lại service | — |
| 11 | Task 10 dispatch | Họ nào `exit 1` không phải guard ⇒ ghi lại và chạy tiếp họ kế (các họ độc lập, một lượt cho đủ bức tranh); `exit 2` ⇒ dừng ngay. Không kích hoạt vế đầu (lỗi gặp là exit 2) | Vài lượt chạy thừa |
| 12 | Task 10 → 10a | Trợ lý định đưa `docs/10-sources` + `docs/20-design` vào image; **chủ dự án bác**: code không đọc `docs/`, không đưa `docs/` vào image. Thực thi: ba JSON `git mv` sang `backend/etl/data/`, khối §9 `wichart.md` thành `backend/etl/wichart_source.py`, test tĩnh cấm đường dẫn `docs/` trong code ngoài test; `.dockerignore` giữ nguyên; docs chỉ trỏ tới (một chủ sở hữu) | Nếu sau này thêm file tra cứu mới mà đặt lại dưới `docs/` thì test tĩnh bắt ngay; chi phí là đổi ~20 link tài liệu một lần |
| 13 | Task 10 Step 4 | Harness chặn lệnh ghi `.env` (xoay `ETL_DB_PASSWORD`) hai lần ⇒ **không lách**, để AC6 cho chủ dự án chạy tay theo lệnh sẵn trong ledger; các bước còn lại (AC3 · AC-SIGTERM · AC5 · AC8 native) làm trọn | AC6 chưa có output thật tới khi chủ dự án chạy; lát chưa khép hoàn toàn nếu bỏ qua |
| 14 | Task 10 (tiếp) | Dự đoán spec §9.3 "`screener` ngoài phiên ⇒ exit 1" sai — guard chỉ kiểm hình dạng dữ liệu; exit 0 sau giờ đóng cửa là hành vi đúng, không sửa gì | — |
| 15 | Task 12 Step 1 | Phép kiểm grep §8: vùng lịch sử của repo gồm cả mục "Điểm vào cho lát N" đã gạch và mục gạch ngang đã xong trong `roadmap.md`, dòng có ngày trong `reference-repos.md`; ba dòng thì-hiện-tại thêm "(đã xoá ở lát 12)", khối khảo sát tiền-lát-12 dán banner; spec có đính chính | Người đọc roadmap có thể đọc bảng khảo sát cũ như hiện tại — banner giảm rủi ro |
| 16 | Task 12 Step 1 | Seam env §6 "có người đọc" mã hoá thật vào `test_env_contract` (readers = code ngoài test ∪ `URL_SPECS` ∪ compose `${…}` ∪ `COMPOSE_*`) thay vì chỉ ghi phán quyết; từ Task 2 tới lúc này test chỉ kiểm `KNOWN_KEYS` | Một khoá đọc theo dạng bộ quét chưa bắt sẽ hiện là mồ côi ⇒ nới bộ quét, không whitelist |
| 17 | Task 12 Step 1 | Chấp nhận bất đồng với #9: `CLICKHOUSE_BACKUP_DIR: /backups` rời neo `x-app`, chỉ service `etl` (nơi mount `/backups`) mang; hợp đồng `test_d03` tách bộ chung + phần riêng `etl` | Service mới cần backup phải khai biến tường minh |

**Minor để dành cho review toàn nhánh (Task 12), không mở vòng sửa:** T1 import giữa file `test_env.py`; `check()` coi khoá khai rỗng là có; T2 contract test không có fixture phản ví dụ, hai docstring nói cùng ý; T3 `resolve_backup_dir` thiếu ca `""`/`"."`; T4 năm chỗ `datetime.now(VN).date()` có sẵn chưa dùng `today_vn`, `today_vn()` không đối số chưa test đồng hồ giả; T5 `install_signal_handlers` để lại handler trong test in-process, danh sách test hồi quy của brief thiếu 7 file CLI (reviewer đã chạy: 48 passed); T6 docstring `daemon()` thiếu nhánh thoát theo tín hiệu, ba khối import rải trong `test_i16`, `shutdown` tạo cả cho `count`/`reconcile`; T7 contract compose không chặn `profiles` quay lại, **rác có sẵn** `test_c99_dedup_probe.py:20` import ba tên đã dời (chỉ vỡ khi `RUN_PROBE=1`); T8 `main()` chưa test trực tiếp, `_ch_literal` chưa test mật khẩu có quote; T9a regex Dockerfile không ghim `/backups` trong `chown`, hai dấu cách trước `&&`.

## Hướng dẫn nối phiên (đọc trước khi làm gì)

1. Nhánh `feat/container-runtime`, HEAD là commit ledger này; **chưa merge, chưa push**. Điểm dừng ở mục ⏸️ phía trên; việc còn lại = plan Task 10 (từ họ `events`), AC6, Task 11, Task 12.
2. Quy trình: `superpowers:subagent-driven-development` với plan [`plan.md`](plan.md); **mọi subagent model `sonnet`** (review toàn nhánh Task 12 nâng `opus`); workspace SDD đặt ở **scratchpad ngoài repo** (không tạo `.superpowers/`); brief từng task trích lại bằng `scripts/task-brief plan.md <N> <file>` của skill; harness **không có SendMessage** ⇒ mỗi vòng sửa là một implementer mới mang brief + report + findings.
3. **`tests/docs` đang đỏ có chủ đích** (link chết tới file đã xoá ở Task 5/7) cho tới Task 11 Step 7b; đừng "sửa" bằng cách nới test. Cả bộ `pytest tests -q` chỉ chạy ở Task 11 Step 8 và Task 12.
4. Chủ dự án đã **uỷ quyền sửa `.env`** (AC6 dùng quyền này: đổi `ETL_DB_PASSWORD`, `docker compose run --rm migrate`, `run --rm etl python -m etl omo`). Không bao giờ in giá trị.
5. Kho dev là **disposable** (chủ dự án chốt xoá dựng lại); stack `dlck` để nguyên là được — `docker compose run --rm etl …` tự chạy lại `migrate` (idempotent) qua `depends_on`.
6. Sáu volume cũ `infra_*`/`dlck-infra_*` chỉ xoá ở Task 12 sau khi mọi AC xanh; **không đụng `tutor-infra_pgdata`**. 11 task Windows: chủ dự án gỡ bằng một lệnh PowerShell ở Task 12 Step 2.

**Cập nhật lúc khép phiên:** họ `events` đã tự kết thúc `success` sau khi operator bị ngắt — Task 10 nối từ họ `price`.

## ▶️ NỐI PHIÊN — 2026-09-08 18:47 (phiên mới, ledger là điểm vào)

Kiểm trước khi làm: stack `dlck` `Up 2 hours` (máy không reboot); `ops.etl_run`: run 1 `market.refdata` success · run 2 `market.events` success (09:47–09:50 UTC) — họ `events` xong; không còn container `run-*`; `python -m core.env check` → `đủ 18 biến bắt buộc, không biến lạ`; `LLM_API` + `FRED_API` có mặt (đếm tên, không in). Sổ SDD ở scratchpad phiên mới (`93c5abe1-…`), kế thừa `progress.md` phiên cũ; brief Task 10 trích lại giống hệt bản cũ.

## Task 10 (phần 1) — AC3 từ `price` · AC-SIGTERM · AC5 (2026-09-08 18:50–18:55, operator Sonnet)

**Step 1 — AC3:** `price --codes FPT,VNM` → `exit=0`, `price xong: {'codes': 2, 'with_data': 2, … 'rows_sent': 120, 'rows_changed': 120, … 'latest_trading_date': '2026-09-08' …}` (run 3, success). `snapshot --codes FPT --kinds snapshot` → `exit=0`, `snapshot xong: {'tally': {'attempted': 1, … 'first': 1 …}, 'rows_written': 1, 'calls': 1 …}` (run 4, success). `fundamentals --codes FPT --kinds bs` → **`exit=2`** (run 5, `failed`):

```
FileNotFoundError: [Errno 2] No such file or directory: '/app/docs/10-sources/market/field-dictionary.json'
```

Đúng luật "`exit=2` ⇒ dừng, không tự lách": chuỗi dừng, 10 họ còn lại (`screener` `omo` `wichart` `fred` `fx` `lbma` `yahoo` `binance` `news` `classify`) chưa chạy.

**Chẩn đoán (đọc, không sửa):** `etl/fundamentals_store.py:37` ráp `parents[2]/docs/10-sources/market/field-dictionary.json`; `.dockerignore` (Task 7, chép spec §5.3) loại nguyên `docs`, Dockerfile không `COPY docs/` — image đúng thiết kế, **code sai chỗ đọc**. Grep code ngoài test cho thấy không chỉ một file: `etl/news_registry.py:13` → `docs/10-sources/news/feeds.json` · `etl/screener_normalize.py:29` → `docs/20-design/market-field-selection.json` · `etl/wichart_registry.py:15` → `docs/10-sources/macro/wichart.md` (khối Python §9, `exec`). Bốn họ `fundamentals` `news` `screener` `wichart` cùng chết trong container — lỗi tất định, sẽ tái diễn mọi lượt. Trợ lý định đưa `docs/10-sources` + `docs/20-design` (1,7 MB) vào image; **chủ dự án bác** (~19:05): *code không được đọc docs; tri thức code cần thì viết lại vào code (backend/db); không đưa thứ không kiểm soát được vào image.* **→ AC3: CHƯA ĐẠT (chặn) — Ruling #12 · Task 10a** (mục kế); Task 10 nối lại từ `screener` sau khi image mới chạy được `fundamentals`.

**Step 2 — AC-SIGTERM:** `docker compose run -d --name sigterm-probe etl python -m etl price --backfill --max-minutes 5` → container lên ngay (`-d --name` được chấp nhận); 20 s sau `docker stop -t 60 sigterm-probe`. Log container:

```
2026-09-08 18:53:03,446 INFO etl.price bắt đầu 18:53 · con trỏ đầu danh sách · còn 1523 mã · hạn 18:58 08/09
2026-09-08 18:53:32,662 WARNING etl.price backfill dừng tay (Ctrl+C) tại con trỏ A32
```

`docker inspect --format '{{.State.ExitCode}}'` → **`130`**. `ops.etl_run` (`market.price_backfill`, run 6): `failed | dừng tay (Ctrl+C)`. Khớp Expected nguyên văn — `SIGTERM` trong container đi đúng đường Ctrl+C (`core/shutdown.py`), PID 1 là Python nhận tín hiệu trực tiếp. **→ AC-SIGTERM: PASS.**

**Step 3 — AC5:** đếm TRƯỚC `ops.etl_run`=**6** · `market.security`=**2017** · `rt.schema_migrations`=**2**; danh sách 6 volume `dlck_*` (`chdata` `ingester_logs` `ingester_measure` `ingester_spill` `pgdata` `redisdata`) lưu file; `docker compose down && docker compose up -d` (không `-v`): 7 container + mạng gỡ rồi tạo lại, `migrate` `Exited (0) 6 seconds ago`; đếm SAU ngay lập tức, không job nào chen: **6 · 2017 · 2** — bằng cả ba; `diff` danh sách volume rỗng → `volume: không đổi`. **→ AC5: PASS.**

Bảng 15 họ ghi một lần ở "Task 10 (tiếp)" sau khi chạy nốt; tới lúc này: `refdata` ✓ · `events` ✓ · `price` ✓ · `snapshot` ✓ · `fundamentals` ✗ exit 2 · 10 họ chưa chạy.

## Task 10a — code không đọc `docs/`: dữ liệu tra cứu dời vào code (2026-09-08 19:15–19:47)

- **Chỉ đạo chủ dự án (~19:05):** code không được đọc `docs/`; tri thức code cần thì viết lại vào code (`backend/`/`database/`); không đưa `docs/` vào image. `.dockerignore` giữ nguyên. Plan Task 10a `e20071f`, spec có đính chính.
- `7875ac3` — `git mv` ba JSON sang `backend/etl/data/` (`field-dictionary.json` · `feeds.json` · `market-field-selection.json`, nội dung không đổi — `git diff -M` rỗng); khối Python §9 của `wichart.md` (dòng 611–798) thành `backend/etl/wichart_source.py` **nguyên văn** (`diff` byte-identical; import ngoài pytest: `WICHART 72 keys; TIER_X 20`); `wichart_registry` import module thay `exec` markdown, `load_doc()` không đối số, `build(doc=None, tier_x=None)`; `database/gen_price_columns.py`, `docs/20-design/gen_field_selection.py`, `docs/10-sources/macro/verify_wichart.py` trỏ đường mới (chạy thật `gen_price_columns.py` → 34 cột); `.gitattributes` theo. Test tĩnh `test_production_code_never_reads_docs` (`tests/docs/test_d03`): **RED đúng 5 hit** (`fundamentals_store:37` · `news_registry:13` · `screener_normalize:29` · `wichart_registry:15` · `gen_price_columns:17`) → GREEN `9 passed`; `test_e36` viết lại không đọc md; hồi quy `tests/etl` **600 passed**, 5 file liên quan 51 passed, `test_d01` 7/8 — chỉ `test_no_dead_internal_links` còn đỏ (nợ Task 11), danh sách link chết **không thêm cái nào**: `diff` trước/sau chỉ là hai link cũ ở `backend/README.md` lệch +2 dòng do đoạn `etl/data/` chèn phía trên (Ruling: cosmetic, chấp nhận). `git grep` đường dẫn `docs/` trong code ngoài test → **0**.
- Tài liệu: 11 file sống trong brief + 3 file ngoài bảng brief (`docs/README.md`, `docs/20-design/market-data-store.md`, `docs/10-sources/market/05-fiin-financial-statements.md`) đổi link/câu chữ theo thanh kiểm Step 6 (0 hit đường cũ ngoài vùng lịch sử); 6 file `docs/90-records/` vỡ link do lượt dời → **chỉ href**, giữ nhãn. `wichart.md` §9 còn tiêu đề + đoạn trỏ tới module (`-190/+1`).
- **Vận hành:** `docker compose up -d --build` → 7 service, `migrate` `Exited (0)`; `docker run --rm dlck-backend sh -c 'test ! -e /app/docs && test -f /app/backend/etl/data/… && test -f /app/backend/etl/wichart_source.py'` → `image-data: OK`; `docker compose run --rm etl python -m etl fundamentals --codes FPT --kinds bs` →

```
2026-09-08 19:45:34,047 INFO etl.fundamentals từ điển 729 mã; tới hạn: 1 target (0 theo sự kiện)
2026-09-08 19:45:40,379 INFO etl.fundamentals fundamentals xong: {'tally': {'attempted': 1, 'failed': 0, … 'first': 1 …}, 'rows_written': 15904, 'calls': 1, 'retries': 0, … 'dictionary_rows': 729, 'remaining': 1522 …}
exit=0
```

  `ops.etl_run`: run 7 `market.fundamentals | success` (run 5 `failed | FileNotFoundError…` giữ làm bằng chứng). **→ họ `fundamentals` trong container: PASS.** Task 10 nối từ `screener`.
- Implementer tự khai: `roadmap.md:468–472` vẫn dẫn `[wichart.md §9]` làm link bằng chứng (đích còn tồn tại, §9 nay là đoạn trỏ) và `:467` giữ vế lịch sử "`verify_wichart.py` đã đọc được khối này bằng `exec`" (neo ngày 2026-08-12) — để Task 11/12 rà cùng lượt roadmap.

**Task 10a — review (2026-09-08 19:50–20:05):** reviewer (Sonnet) xác nhận hai rủi ro nêu tên — khối WiChart dời **nguyên văn** (đọc so từng dòng đầu/giữa/cuối), danh sách link chết chỉ lệch +2 dòng do đoạn `etl/data/` chèn vào `backend/README.md` (cosmetic). 2 Important: docstring `verify_wichart.py` còn nói "đọc registry trực tiếp từ file md" (sót thật) và `roadmap.md:467` còn nói "đã đọc được khối này bằng `exec`" (do brief khoanh hẹp — **Ruling: sửa**, tài liệu sống không được sai §1.7, giữ mốc lịch sử 2026-08-12 và thêm sự thật hiện tại). Vòng sửa 1/5 `2f28c1c`; re-review: cả hai ADDRESSED, không vỡ gì mới. Minor để dành: chuỗi lỗi trong `build()` còn chữ "§9" (thân hàm giữ nguyên theo brief); `roadmap.md:467` lặp ý trong một ô; `verify_wichart.py:89` in "Đọc registry từ file"; các dòng `roadmap.md:468–472` dẫn `[wichart.md §9]` làm link bằng chứng. **Task 10a: xong** (`7875ac3` + `2f28c1c`).

## Task 10 (tiếp) — 10 họ còn lại · bảng 15 họ (2026-09-08 19:49–20:06, operator Sonnet, image `7875ac3`)

**Tiền kiểm:** `docker compose ps -a` — đủ 7 service: `migrate` `Exited (0)`, `postgres`/`redis`/`clickhouse` `(healthy)`, `api`/`etl`/`ingester` `Up`. Chạy tiếp AC3 từ họ `screener` theo đúng thứ tự brief, mỗi lệnh `docker compose run --rm etl python -m etl …`.

**`screener`** — 52 lượt `POST …/Screener/GetScreenerItems` đều `200 OK`, rồi:

```
screener xong: {'counts': {'items': 1545, 'pages': 52, 'priced': 1545, 'trading_dates': 1}, 'rows_written': 1541, 'unmapped': 4, …, 'trading_date': '2026-09-08'}
exit=0
```

**Lệch dự đoán của spec §9.3 / plan** ("ngoài phiên ⇒ guard từ chối, exit 1"): job chạy trọn, ghi 1.541 dòng cho phiên hôm nay. Kiểm code: guard của screener (`etl/screener_guard.check`) chỉ kiểm **hình dạng dữ liệu** — tỷ lệ mã có `closePrice > 0` ("không phải ngày giao dịch"), thiếu trang, `totalCount` sụt, tỷ lệ không ghép được `security_id`, `comGroupCode` lạ — **không có guard theo giờ**. 19:50 của một ngày giao dịch là sau giờ đóng cửa, dữ liệu trong ngày đã đủ nên thành công là hành vi đúng; dự đoán "guard có phiên" trong spec là giả định sai, không phải lỗi job. Không vi phạm AC3.

**`omo`** → `omo xong: {'sessions': 1, 'auctions': 4, 'flow_rows': 5}`, `exit=0`. **`wichart --keys vang`** → `wichart xong: {… 'points': 1036, … 'inserted': 1036 …}`, `exit=0`. **`fred --keys DGS10`** → `fred xong: {… 'points': 16154, … 'inserted': 16154 …}`, `exit=0`. **`fx`** → `fx xong: {'tally': {'total': 7, 'failed': 0 …}, … 'inserted': 49342 …}`, `exit=0` (sổ ghi tên job `global.ecb`). **`lbma`** → `lbma xong: {'tally': {'total': 2, 'failed': 0 …}, … 'inserted': 29498 …}`, `exit=0`. **`yahoo --keys '^GSPC'`** → `yahoo xong: {'tally': {'total': 1, 'failed': 0 …}, 'bars': 275, 'inserted': 275 …}`, `exit=0`. **`binance --intraday`** → `binance xong: {'tally': {'total': 11, 'failed': 0 …}, 'bars': 33, 'inserted': 33 …}`, `exit=0` — không bị chặn địa lý từ mạng này. **`news --sources cafef`** → `news cycle 0: items 179 · new 179 · merged 0/0/0 · seen 0 · refused 5 · warnings []`, `exit=0` (job dài nhất, ~9–10 phút; sổ ghi `news.collect`). **`classify --limit 1`** → `classify xong: {… 'selected': 1, 'classified': 1, 'failed': 0, … 'quota_stop': False, 'budget_hit': False, 'model_down': False, 'warnings': []}`, `exit=0` (sổ ghi `news.classify`; không giá trị `LLM_API` nào lộ trong log).

**Kiểm chứng `ops.etl_run`** (`select distinct on (job) …`):

```
          job          | status  |       error       |          finished_at
-----------------------+---------+-------------------+-------------------------------
 global.binance        | success |                   | 2026-09-08 12:55:12.030813+00
 global.ecb            | success |                   | 2026-09-08 12:54:00.968734+00
 global.fred           | success |                   | 2026-09-08 12:53:48.993869+00
 global.lbma           | success |                   | 2026-09-08 12:54:16.821911+00
 global.yahoo          | success |                   | 2026-09-08 12:54:24.997346+00
 macro.omo_crawl       | success |                   | 2026-09-08 12:53:30.198896+00
 macro.wichart         | success |                   | 2026-09-08 12:53:39.361526+00
 market.events         | success |                   | 2026-09-08 09:50:22.684167+00
 market.fundamentals   | success |                   | 2026-09-08 12:45:40.376938+00
 market.price_backfill | failed  | dừng tay (Ctrl+C) | 2026-09-08 11:53:32.660967+00
 market.price_daily    | success |                   | 2026-09-08 11:51:01.590263+00
 market.refdata        | success |                   | 2026-09-08 09:09:07.321998+00
 market.screener       | success |                   | 2026-09-08 12:52:25.839957+00
 market.snapshot       | success |                   | 2026-09-08 11:51:13.411022+00
 news.classify         | success |                   | 2026-09-08 13:05:12.047497+00
 news.collect          | success |                   | 2026-09-08 13:04:53.830158+00
(16 rows)
```

`select count(*) from ops.etl_run` → **17** = 16 tên job phân biệt (`price` chiếm `market.price_daily` + `market.price_backfill`; `fx` ghi dưới `global.ecb`) + một dòng lịch sử (`market.fundamentals` run 5 `failed` exit 2 trên image cũ; `distinct on` chỉ giữ run 7 `success`).

**Bảng 15 họ (AC3):**

| họ | cờ | exit | status | ghi chú |
|---|---|---|---|---|
| refdata | (không) | 0 | success | run 1, Task 9 |
| events | `--accept-new` | 0 | success | run 2, tự xong cuối phiên trước |
| price | `--codes FPT,VNM` | 0 | success | job `market.price_daily` (run 3) |
| snapshot | `--codes FPT --kinds snapshot` | 0 | success | run 4 |
| fundamentals | `--codes FPT --kinds bs` | 2 → 0 | failed → success | run 5 exit 2 trên image cũ (`FileNotFoundError`, image không mang `docs/`) → Task 10a → run 7 success (`dictionary_rows: 729`, 15.904 dòng) |
| screener | (không) | 0 | success | chạy trọn sau giờ đóng cửa — guard kiểm dữ liệu, không kiểm giờ (xem trên) |
| omo | (không) | 0 | success | — |
| wichart | `--keys vang` | 0 | success | 1.036 điểm |
| fred | `--keys DGS10` | 0 | success | 16.154 điểm |
| fx | (không) | 0 | success | job `global.ecb`, 49.342 dòng |
| lbma | (không) | 0 | success | 29.498 dòng |
| yahoo | `--keys '^GSPC'` | 0 | success | 275 nến |
| binance | `--intraday` | 0 | success | 33 nến, không geo-block |
| news | `--sources cafef` | 0 | success | job `news.collect`, 179 bài mới |
| classify | `--limit 1` | 0 | success | job `news.classify`, 1 bài |

**→ AC3: PASS** — cả 15 họ có ít nhất một dòng `ops.etl_run` `success`; dòng `failed` duy nhất còn lại (`market.price_backfill`) là phép thử SIGTERM có chủ đích (Step 2, PASS); không lệnh nào `exit=2` trên image đã sửa.

**Step 5 — AC8 nửa native (2026-09-08 20:11):** `cd backend && PYTHONIOENCODING=utf-8 uv run python -m etl omo` → `omo xong: {'skipped': True}`, **`exit=0`** — native vào cùng kho `dlck` qua `127.0.0.1`, cùng `.env` nguyên tố (skipped = không có phiên mới sau lượt trong container 5 phút trước, đúng idempotent). **→ AC8 (nửa native): PASS**; cả bộ pytest ở Task 11 Step 8.

**Step 4 — AC6 (đổi mật khẩu một user): ⏳ CHỜ CHỦ DỰ ÁN.** Trợ lý đã viết script xoay `ETL_DB_PASSWORD` không in giá trị (scratchpad `sdd/2026-09-08-container-runtime/rotate_etl_password.py`, kèm `verify_ac6_passwords.py` kiểm "mật khẩu cũ bị từ chối" theo spec §7 AC6), nhưng **bộ phân loại quyền của harness chặn lệnh ghi `.env`** (hai lần, 19:20 và 20:10) — không lách (Ruling #13). Chủ dự án chạy tay (Git Bash, gốc repo), không dán giá trị vào đâu:

```bash
cp .env .env.bak-ac6-2026-09-08                 # bản cũ (gitignore) để kiểm "mật khẩu cũ bị từ chối"
# sửa tay dòng ETL_DB_PASSWORD= trong .env thành một chuỗi chữ-số mới, hoặc:
#   uv run --project backend python <scratchpad>/rotate_etl_password.py .
docker compose run --rm migrate | grep "postgres user"      # Expected: bootstrap: postgres user: etl_worker, agent_reader
docker compose run --rm etl python -m etl omo; echo "exit=$?"   # Expected: exit=0
cd backend && uv run python <scratchpad>/verify_ac6_passwords.py ..   # Expected: old REJECTED (password authentication failed) · new ACCEPTED
cd .. && docker compose up -d                               # tạo lại service với env mới (vệ sinh, không bắt buộc)
```

Ghi output (không giá trị) vào ledger là AC6 đạt.

## Task 11 — tài liệu sống, "Điểm vào cho lát 13", AC8 cả bộ (2026-09-08 20:20–20:50, implementer Sonnet)

- `e8a190f` — bảy file tài liệu sống theo spec §8 (`README.md` · `backend/README.md` · `database/README.md` · `service-topology.md` · `roadmap.md` · `CLAUDE.md` · `docs/90-records/README.md`) + href lịch sử ở `docs/90-records/` (kể cả 6 link trong chính `plan.md` lát này — bảng hướng dẫn Task 10a bị test đọc như link thật, sửa href theo luật lịch sử). Ba phán quyết mang vào brief: ngày thật `2026-09-08` thay `2026-09-0x`; **11 task Windows vẫn còn đăng ký** (đếm 20:15: 10 `Disabled` + `dlck-price-backfill` `Ready`) và 6 volume cũ còn nguyên ⇒ tài liệu viết "về hưu — gỡ ở Task 12", không viết "đã gỡ"; danh sách link chết lấy từ test (19 mục) thay bảng dòng cũ trong plan.
- Implementer tự khai ba lệch có lý do: `docs/90-records/README.md` ghi AC1–AC5/AC7/AC8 đạt, AC6/AC9 chờ (không chép "AC1–AC9 đạt" của brief vì chưa đúng); sửa thêm một câu tham chiếu "bước 3" ở `database/README.md` bị chính Step 3(c) làm lệch; sửa cảnh báo `register-tasks.ps1` thì hiện tại ở `roadmap.md` §0 dòng 30. Phép kiểm §1.7 (grep chín cụm) → mọi hit còn lại là câu "về hưu" có ngày hoặc cảnh báo "đừng dùng `downgrade 0012`".
- **AC8 — cả bộ test, `.env` nguyên tố, kho `dlck`:** `cd backend && uv run pytest tests -q` → **`1109 passed, 3 skipped in 86.27s`**, 0 failed. Skip thứ ba (so với 2 của Task 0) là test SIGTERM tiến trình thật của chính lát này (`test_shutdown.py`, chỉ chạy POSIX). Số này do `database/README.md` sở hữu, ghi kèm ngày. `tests/docs` xanh trở lại (link chết 19 → 0). **→ AC8: PASS.**

## Task 12 — khép lát (bắt đầu 2026-09-08 20:50)

**Step 4 — AC1, build sạch từ clone mới (20:52):** `git clone --quiet . "$CLONE"` vào scratchpad lần đầu **vỡ** `Filename too long` ở `docs/30-skills/corpus/HP2…`/`HP4…` — `git config --global core.longpaths` **chưa bật** (CLAUDE.md §5 ghi "đã bật": chỉ đúng cho config cục bộ của repo, không theo tiến trình clone). Chạy lại `git clone -c core.longpaths=true --quiet . "$CLONE"` → clone HEAD `e8a190f`, `cp .env` vào clone (gitignore, không commit):

```
config: OK
 dlck-backend  Built
clone build: OK
image: OK        # test ! -e /app/.env && test ! -e /app/backend/tests && test ! -e /app/docs && test -f /app/database/alembic.ini && test -f /app/backend/etl/data/feeds.json
clone removed: yes
```

**→ AC1: PASS.** Ghi chú môi trường: lệnh clone ở §5.8/README nên kèm `-c core.longpaths=true` trên Windows khi chưa bật global — để Task 12 Step 5 rà.

**Step 1 — review toàn nhánh hai trục (2026-09-08 21:00–21:40, hai reviewer Opus độc lập, gói diff `1ec3005..7b141d0`: 47 commit, 92 file, +5166/−1290):**

- **Trục Chuẩn:** 0 Critical · **6 Important** · 13 Minor — "with fixes". Bốn đường soi kỹ nhất đứng vững (in secret ở đường lỗi, ghép SQL trong `bootstrap`, chạy lại riêng `0013`, ingester lúc 08:30 mai). Important: (I1) comment `ingester/__main__.py:10` và `backend/README.md` nói ingester đóng sổ `ops.etl_run` + exit 130 — sai, đường thật là `install_loop_stop` (exit 0/1, không có dòng sổ); (I2) `core.env check` coi khoá rỗng là có, cho `change-me` đi lọt, và không chạy được trong container (đọc file `.env` mà image không mang) ⇒ bước 1 README đòi uv/Python trên VPS; (I3) `tests/conftest.py` nới bán kính `DROP DATABASE … WITH (FORCE)` từ hằng `dulieu_test` sang `POSTGRES_TEST_DB` mà không canh "phải là DB test"; (I4) ba bộ quét tĩnh không có đối chứng dương, bộ `docs/` có thể xanh rỗng và regex bắt 1/5 hình dạng tái diễn; (I5) `CLAUDE.md` §5 vẫn ghi `core.longpaths` "đã bật" sau khi AC1 đo ngược lại; (I6) AC-SIGTERM Task 10 chạy trên `etl price --backfill` — đường `core/shutdown.py`, không phải đường `install_loop_stop` của ingester ⇒ đường xả của ingester chưa có bằng chứng thật. Triage 22 Minor để dành: 4 sửa trước merge (T1b, T2a, T8b, T9a), 16 để lại, 1 N/A, 1 mở task riêng (`test_c99_dedup_probe.py:20`, rác có sẵn). Bất đồng nhẹ với phán quyết #9: `CLICKHOUSE_BACKUP_DIR: /backups` nằm ở neo `x-app` nên bốn service không mount `/backups` vẫn mang biến trỏ vào đường không tồn tại.
- **Trục Spec:** 0 Critical · **3 Important** · 9 Minor — "with fixes". Ma trận phủ §5/§6/§7/§8 đủ; mục tiêu một câu của lát đạt trên máy thật. Important: (I1) seam hợp đồng `.env.example` ↔ code giao yếu hơn spec §6 (hai vế "có người đọc thật" thành "∈ `KNOWN_KEYS`") mà không có phán quyết; (I2) phép kiểm grep §8 báo đạt theo tiêu chí khác tiêu chí đã viết (7 hit ngoài `90-records/`/`decisions/`, nằm trong mục "Điểm vào cho lát 12" đã gạch và mục gạch ngang của roadmap); (I3) hai "PASS" thiếu output kèm — `events` ghi `exit 0` mà mã thoát chưa quan sát, AC2 "head `0020`" không có `alembic current` trên kho mới. Audit 14 phán quyết: 14/14 trong quyền tự quyết, không mục nào đáng lẽ phải hỏi chủ dự án (#13 "mẫu mực"); hai ô "nếu sai mất gì" nhẹ hơn thực tế (#6, #8 — đã sửa ô). §9: cả năm điểm đã duyệt tường minh trước khi thực thi; điểm 1(8) và 5 còn nợ Task 12, điểm 3 có tiền đề sai đã ghi (#14).

**Bằng chứng bổ sung do controller lấy ngay sau review (21:20–21:36):**

- *Spec I3(a) — `events`:* `ops.etl_run` run 2 (lượt đầu trên kho mới, tự kết thúc sau khi operator bị ngắt): `issuers_created` = **519** (> 20 như spec §9.3 mong đợi), `rows_written` = 110.728. Chạy lại có quan sát mã thoát: `docker compose run --rm etl python -m etl events --accept-new` → `events xong: {… 'rows_written': 110728, 'issuers_created': 0, 'dup_conflicts': 42, 'retries': 0, 'watermark': '2026-09-08', 'accept_new': True}`, **`exit=0`** (run 19, idempotent). Bảng 15 họ: dòng `events` nay có mã thoát thật.
- *Spec I3(b) — AC2 head:* `docker compose run --rm etl sh -c 'cd /app && alembic -c database/alembic.ini current'` → **`0020 (head)`**; `select version from rt.schema_migrations` → `0001_roles` · `0002_rt_schema`; `select rolname from pg_roles where rolname in ('etl_worker','agent_reader')` → cả hai có mặt.
- *Chuẩn I6 — đường SIGTERM của ingester (`install_loop_stop`), chạy thật trong container 21:33–21:34:*

```
$ docker compose run -d --name ing-sigterm ingester python -m ingester --minutes 3
$ sleep 45 && docker stop -t 90 ing-sigterm      # trả về ngay tại 21:34:19
2026-09-08 21:33:34,594 INFO ingester run: 2022 mã, 6084 topic
2026-09-08 21:33:34,682 INFO ingester đã subscribe 6084 topic trong 61 lô
2026-09-08 21:33:35,102 INFO ingester đã init_state (giành leader)
reconcile: p1=0 p2=0 ok=0
2026-09-08 21:34:19,231 INFO ingester reconcile: p1=0 p2=0 ok=0
$ docker inspect --format '{{.State.ExitCode}}' ing-sigterm
0
```

  SIGTERM → `stop.set()` → socket đóng → xả → đối chứng → **exit 0** (không 137, không 130 — đúng thiết kế Task 6). AC-SIGTERM nay có bằng chứng cho **cả hai** đường: `etl` (Task 10 Step 2, exit 130 + sổ) và ingester (ở đây). Task 6 ⚠️ "nhánh POSIX chưa chạy được trên máy dev" — đóng.
- *Spec M2:* spec §5.9 bước 1 (`docker compose -p infra -f deploy/infra/docker-compose.yml --profile realtime down`) không chạy được vì Task 7 đã xoá file compose đó trước Task 9; Task 9 Step 1 dùng `docker rm -f` ba container + `docker network rm dlck-net`, có đối chứng volume trước/sau — tương đương, nay ghi là lệch có chủ đích.
- *Spec M9 — dán thay vì diễn giải:* log `migrate` lượt `up` thứ hai (Task 9 Step 4), 5 dòng nguyên văn: `bootstrap: postgres migrate xong (head)` · `bootstrap: clickhouse migrate: không có gì mới` · `bootstrap: postgres user: etl_worker, agent_reader` · `bootstrap: clickhouse user: ingester_worker, api_reader` · `bootstrap: seed ngành lớp 2: skipped:security-rong (0 dòng override)`. Task 9 Step 6 `ls -la` nguyên văn: `drwxr-xr-x 2 appuser root 4096 Sep 8 16:38 /var/lib/dlck/logs/.` · `-rw-r--r-- 1 appuser appuser 1242 Sep 8 16:40 ingester-20260908.log` · `-rw-r--r-- 1 appuser appuser 0 Sep 8 16:38 /var/lib/dlck/spill/owner.lock`; riêng `tail -5` file log operator chỉ tóm tắt, không dán — không có bản nguyên văn (ghi nhận, không bịa).

**Phán quyết sau review (#15–#17, bảng sổ phán quyết):** #15 vùng lịch sử của repo gồm cả mục "Điểm vào cho lát N" đã gạch và mục gạch ngang đã xong trong `roadmap.md`, dòng có ngày trong `reference-repos.md`; ba dòng còn nói thì-hiện-tại được thêm "(đã xoá ở lát 12)" và khối khảo sát tiền-lát-12 được dán banner. #16 seam env §6 "có người đọc" **mã hoá thật** vào `test_env_contract` (readers = code ngoài test ∪ `URL_SPECS` ∪ compose `${…}` ∪ `COMPOSE_*`), không chỉ ghi phán quyết. #17 chấp nhận bất đồng với #9: `CLICKHOUSE_BACKUP_DIR` rời neo `x-app`, chỉ `etl` mang.

**Để dành có lý do (không sửa trong nhánh này):** Spec M3 — bảng hướng dẫn Task 10a trong `plan.md` đã bị sửa href sang đường tương đối của chính `plan.md` để test link chết xanh, chỉ dẫn không còn tái lập nguyên văn (kết quả thật nằm ở commit `7875ac3`) — giữ theo luật "chỉ href" của vùng lịch sử; Spec M5 — câu chữ spec §5.2 về vị trí `restart` tự mâu thuẫn, code đúng; Chuẩn M2 (`alembic_config` đổi env/cwd tiến trình, one-shot), M4 (quét `ast` cho hợp đồng múi giờ), M5 (hằng `ZoneInfo` VN nhân bản ở module có sẵn — gộp với T4a), M10 (`chown -R` sau `uv sync` nhân đôi venv thành layer — xét ở lát VPS), M13 (vị trí hai unit test `resolve_backup_dir`, import rải trong `test_i16`, `9000` ghim cứng, import trong thân hàm `ch_backup`); 16 Minor để dành T1a/T2b/T3/T4a/T4b/T5a/T6a/T6b/T6c/T7a/T8a/T8c/T8d/T10a giữ nguyên lý do trong report review; **T7b mở task riêng** (`backend/tests/clickhouse/test_c99_dedup_probe.py:20` import ba tên đã dời từ 2026-09-07 — luôn `ImportError` khi `RUN_PROBE=1`). Ghi nhận thêm từ trục Chuẩn (báo, không sửa — §4.4.3): cổng `8000` mở `0.0.0.0` có sẵn từ `deploy/app` cũ — xem lại trước khi lên VPS thật; sau reboot VPS `depends_on` không được đánh giá lại, ingester trả 3 vài lượt tới khi kho healthy rồi tự ổn — ồn log, không mất dữ liệu.

**Đợt sửa gộp sau review (2026-09-08 21:45–22:42, một implementer Sonnet, brief 20 mục — sổ SDD `final-fix-brief.md`):** bốn commit `12ac34e` (`core.env check`: khoá rỗng = thiếu; `change-me`/`changeme` ⇒ `YẾU  <TÊN>` + exit 1; không có file ⇒ rơi về `os.environ` để chạy được trong container — 12 test) · `bb0ac9d` (`conftest` canh tên DB test `!= POSTGRES_DB` và đuôi `_test` trước `DROP DATABASE`; `bootstrap` bỏ biểu thức tuple vứt đi, docstring reseed nói đúng "> 0" thay "= 161", tắt DEBUG của `clickhouse_connect` cạnh `basicConfig`; `wichart_registry.build` ném khi `doc`/`tier_x` lệch nhau; `price_job` log lazy; comment `ingester/__main__.py` nói đúng đường dừng; cảnh báo ở đầu migration `0013`; `CLICKHOUSE_BACKUP_DIR` rời neo `x-app` về riêng `etl`, comment `stop_grace_period`) · `6021714` (đối chứng dương + ca âm cho ba bộ quét tĩnh; regex `docs/` bắt đủ 5 hình dạng tái diễn và chốt `n_files >= 100`; `_READ` bắt `os.getenv`/nháy đơn/`environ["X"]`; vế "có người đọc thật" của seam env §6 — Ruling #16; test `_ch_literal` với `'` và `\`; ca role đích không tồn tại của `provision_postgres`; hợp đồng Dockerfile khẳng định `USER appuser`, ghim `/backups` trong `chown`, bỏ vế bắt chữ `.env`) · `2eaceab` (README bước 1: `git clone -c core.longpaths=true` + `core.env check` dạng container; `backend/README`/`service-topology` tách hai đường dừng `etl` (130 + sổ) và ingester (0/1, không sổ); CLAUDE.md §5 dòng Git nói đúng longpaths chỉ bật cục bộ; roadmap: banner trên khối khảo sát tiền-lát-12, ba dòng "(đã xoá ở lát 12)", AC6 chờ chủ dự án ở bàn giao lát 13, ghi chú `/backups` cho VPS; spec ba đính chính; số test `database/README.md`). Cả bộ sau đợt sửa: **`1128 passed, 3 skipped in 87.36s`** (+19 test, 0 failed). Bốn lệch so với brief, controller chấp nhận: câu chữ dòng "nguồn"; trên nhánh rơi về `os.environ` không kiểm "biến lạ" (môi trường tiến trình có biến không liên quan); `readers` của seam env lấy `REQUIRED_KEYS` thay `URL_SPECS` thô vì `bootstrap` đọc `CLICKHOUSE_API_*` qua tuple rồi `os.environ[u]` — regex không quy được, `env.py` đã ghi "hai biến chỉ bootstrap dùng"; vị trí chèn trong dòng ASCII roadmap. Controller áp thay đổi: `docker compose config --quiet` OK → `docker compose up -d --build` (image từ `2eaceab`, 7 service tạo lại, `migrate` `Exited (0)`) → **D2 trong container mới:** `docker compose run --rm --no-deps migrate python -m core.env check` → `nguồn: môi trường (không có /app/.env)` · `đủ 18 biến bắt buộc, không biến lạ` · `exit=0` — bước 1 README nay không cần uv/Python trên VPS.

**Re-review đợt sửa gộp (Opus, 22:45–22:55, gói `7b141d0..2eaceab`):** 25/25 mục ADDRESSED; 4 lệch implementer khai đều khớp phán quyết; hỏng mới 0 Critical · 0 Important · 4 Minor · 2 Nit. Controller tự sửa năm chỗ một dòng (§4.1 "việc nhỏ → tự làm") ở `ed121e4`: `core.env check` trên nhánh rơi về `os.environ` in `đủ 18 biến bắt buộc (không kiểm biến lạ trên môi trường)` thay vì khẳng định điều không kiểm; bỏ biến `dockerfile` mồ côi ở `test_d03`; bỏ mệnh lệnh thừa trong docstring `0013`; sửa số dòng ở đính chính spec (b); `roadmap.md:178` câu "exit 130" thêm chủ ngữ "job `etl`"; thụt comment `ingester/__main__.py`. Kiểm: 38 test (`test_env`, `tests/docs`, `test_env_contract`) xanh; image build lại từ HEAD, D2 trong container mới → `nguồn: môi trường (không có /app/.env)` · `đủ 18 biến bắt buộc (không kiểm biến lạ trên môi trường)` · exit 0. Để lại từ re-review (không sửa): `YẾU  <TÊN>` hai dấu cách lệch cột (brief ép literal, test ghim); `README.md:80–83` hai biến thể lệnh chung một fence; ca dương `test_conftest_env_contract` chỉ "không raise"; `_READ` cho nháy mở/đóng khác loại. `0a66ad9` — CLAUDE.md §4.1: luật model subagent mới của chủ dự án (Opus ngay từ đầu cho task dài/nhiều mục/cần suy xét; đợt sửa gộp 20 mục chạy Sonnet mất 57 phút).

**Step 5 — lượt cuối cả bộ tại HEAD `0a66ad9` (22:58):** `cd backend && uv run pytest tests -q` → **`1128 passed, 3 skipped in 87.25s`**; `git grep -n "\[DEBUG-" -- backend | wc -l` → **0**. Stack `dlck`: 7 service (image = HEAD), `migrate` `Exited (0)`; volume: 6 `dlck_*` + 6 cũ (`infra_*`, `dlck-infra_*`) + `tutor-infra_pgdata`.

## Đóng lát — 2026-09-08 23:00 (chưa merge; ba việc chờ chủ dự án)

| AC | Kết quả | Bằng chứng (mục ledger) |
|---|---|---|
| AC1 build sạch từ clone mới | ✅ đạt | Task 12 Step 4 — cần `git clone -c core.longpaths=true` trên Windows (README đã ghi) |
| AC2 `up -d --build` kho mới | ✅ đạt | Task 9 Step 2–3 + Step 1 review (`alembic current` → `0020 (head)`, `rt` `0001`/`0002`, hai role login) |
| AC3 15 họ job trong container | ✅ đạt | Task 10 phần 1 + Task 10a + Task 10 (tiếp): 15/15 `success`, mã thoát 0 quan sát cho cả `events` (chạy lại) — `screener` chạy trọn sau giờ (Ruling #14) |
| AC-SIGTERM | ✅ đạt cả hai đường | `etl` (Task 10 Step 2: exit 130, sổ `dừng tay`) · ingester (Step 1 review: `install_loop_stop`, reconcile, exit 0) |
| AC4 ingester trong container ngoài giờ | ✅ đạt | Task 9 (tiếp) Step 6, sau Task 9a |
| AC5 `down`/`up` không mất gì | ✅ đạt | Task 10 Step 3 (6 · 2017 · 2; 6 volume) |
| AC6 đổi mật khẩu một user | ✅ đạt (23:10) | Ruling #13 — harness chặn ghi `.env`; lệnh sẵn ở "Step 4 — AC6" |
| AC7 backup ClickHouse ra host | ✅ đạt | Task 9 (tiếp) Step 7 + đính chính đường backup |
| AC8 native không hỏng | ✅ đạt | Task 11 Step 8 `1109/3` → sau đợt sửa `1128/3` (Step 5); native `omo` exit 0 (Task 10 Step 5) |
| AC9 gỡ 11 task · xoá 6 volume cũ | ✅ đạt (23:12) | 11 task `dlck-*` còn đăng ký (đếm 20:15); 6 volume cũ còn nguyên — thao tác huỷ, chờ chủ dự án gật rồi controller chạy `docker volume rm` theo plan Task 12 Step 3 |

**Nhánh:** `feat/container-runtime`, HEAD `0a66ad9`, 54 commit từ `1ec3005` (merge-base `main`), **chưa merge, chưa push**. Khép nhánh (merge `--no-ff` vào `main`, chạy lại cả bộ trên `main`, push, xoá nhánh — theo khuôn ledger lát audit) là quyết định chủ dự án; nên làm **sau** ba việc chờ ở trên để `main` không mang trạng thái "AC6/AC9 chờ".

**Ba việc chờ chủ dự án (theo thứ tự):**

1. **AC6** — chạy đúng khối lệnh ở mục "Step 4 — AC6 (đổi mật khẩu một user)" phía trên; dán output (không giá trị) vào ledger, đổi ô AC6 thành ✅.
2. **AC9 phần 1** — PowerShell: `Get-ScheduledTask -TaskName 'dlck-*' | Unregister-ScheduledTask -Confirm:$false` rồi `(Get-ScheduledTask -TaskName 'dlck-*' -ErrorAction SilentlyContinue | Measure-Object).Count` → `0`; dán vào ledger.
3. **AC9 phần 2** — gật một câu; controller chạy `docker volume rm infra_pgdata infra_chdata infra_redisdata dlck-infra_pgdata dlck-infra_chdata dlck-infra_redisdata` và đối chứng còn đúng 6 `dlck_*` + `tutor-infra_pgdata`.

**Nợ để lại (có lý do):** `backend/tests/clickhouse/test_c99_dedup_probe.py:20` import ba tên đã dời từ 2026-09-07 — luôn `ImportError` khi `RUN_PROBE=1` (rác có sẵn, §4.4.3: **mở task riêng**) · cổng `8000` mở `0.0.0.0` có sẵn từ `deploy/app` cũ — xem lại trước khi lên VPS (`127.0.0.1` + reverse proxy) · sau reboot VPS `depends_on` không được đánh giá lại: ingester trả 3 vài lượt tới khi kho healthy rồi tự ổn (ồn log, không mất dữ liệu — ghi vào runbook lát 15) · bind `${CLICKHOUSE_BACKUP_DIR}:/backups` trên Linux sạch tạo thư mục host `root:root` trong khi `clickhouse-server` ghi bằng uid 101 (roadmap điểm vào lát 13 đã ghi cho lát 15) · `chown -R` sau `uv sync` nhân đôi venv thành một layer (M10, xét ở lát VPS) · hằng `ZoneInfo` VN nhân bản ở module có sẵn + 5 chỗ `datetime.now(VN).date()` (T4a/M5, dọn chung một lượt) · quét `ast` cho hợp đồng múi giờ (M4) · `alembic_config` đổi env/cwd tiến trình (M2) · vị trí hai unit test `resolve_backup_dir`, import rải `test_i16`, `9000` ghim cứng (M13) · 16 Minor để dành T1a/T2b/T3/T4b/T5a/T6a/T6b/T6c/T7a/T8a/T8c/T8d/T10a (lý do trong `final-review-standards.md`, sổ SDD) · Spec M3 (bảng hướng dẫn Task 10a trong plan đã sửa href, chỉ dẫn không tái lập nguyên văn) · Spec M5 (câu chữ §5.2 về `restart`).

**Trạng thái máy lúc khép:** stack `dlck` chạy image HEAD (7 service, `migrate` Exited 0); ingester daemon ngủ tới 08:30 09/09 (sẽ chạy phiên thật đầu tiên trong container — theo dõi log `dlck-ingester-1` và volume `dlck_ingester_logs`); `.env` nguyên tố, `CLICKHOUSE_BACKUP_DIR=./deploy/infra/clickhouse-backups`, bản cũ `.env.bak-2026-09-08`; sổ SDD phiên này ở scratchpad `93c5abe1-…/scratchpad/sdd/2026-09-08-container-runtime/` (brief/report/review từng task, hai review toàn nhánh, brief + report + re-review đợt sửa gộp).

## Hướng dẫn nối phiên — cập nhật 2026-09-08 23:00 (thay mục cùng tên phía trên)

1. Nhánh `feat/container-runtime` HEAD `0a66ad9`, chưa merge/push. Việc còn lại = ba việc chờ chủ dự án (mục "Đóng lát") → cập nhật bảng AC → khép nhánh theo `finishing-a-development-branch` (merge `--no-ff`, cả bộ trên `main`, push, xoá nhánh) → ghi ngày merge vào roadmap/`90-records/README.md` → viết memory.
2. Không tự xoá volume, không tự merge khi chủ dự án chưa gật; không lách harness để ghi `.env`.
3. Luật mới trong lát: code không đọc `docs/` (test tĩnh `test_production_code_never_reads_docs`); subagent Opus ngay từ đầu cho task dài/nhiều mục (CLAUDE.md §4.1).

## Ba việc chờ chủ dự án — đã làm 2026-09-08 23:08–23:15 (chủ dự án uỷ quyền 23:05: "tôi cho phép bạn sửa env và chạy code, xử lý nốt 3 việc kia")

**AC6 — đổi mật khẩu một user:** script `rotate_etl_password.py` (scratchpad) → `rotated ETL_DB_PASSWORD: old len=32 -> new len=28; backup=.env.bak-ac6-2026-09-08` (không in giá trị). `docker compose run --rm migrate | grep "postgres user"` → `bootstrap: postgres user: etl_worker, agent_reader`. `docker compose run --rm etl python -m etl omo` → `omo xong: {'skipped': True}`, **`exit=0`** — job đi bằng mật khẩu mới ráp từ `.env` mới. Chiều bị từ chối (spec §7 AC6): `verify_ac6_passwords.py` nối native qua `127.0.0.1` với URL ráp từ bản sao lưu và từ `.env` mới →

```
old password (backup): REJECTED (password authentication failed)
new password (live .env): ACCEPTED (current_user=etl_worker)
```

`docker compose up -d` tạo lại `migrate`/`api`/`etl`/`ingester` với env mới (`migrate` `Exited (0)`). Cây git sạch, `.env*` không tracked (chỉ `.env.example`). **→ AC6: PASS.**

**AC9 phần 1 — gỡ 11 task Windows (PowerShell, không cần admin — task đăng ký `Interactive`):** `Get-ScheduledTask -TaskName 'dlck-*'` → **11**: `dlck-events` `dlck-ingester` `dlck-ingester-measure` `dlck-omo-1130` `dlck-omo-1530` `dlck-omo-1800` `dlck-omo-2130` `dlck-price` `dlck-price-backfill` `dlck-refdata` `dlck-screener`; `| Unregister-ScheduledTask -Confirm:$false`; đếm lại → **0**.

**AC9 phần 2 — xoá sáu volume cũ:** trước: `dlck-infra_chdata dlck-infra_pgdata dlck-infra_redisdata dlck_chdata dlck_ingester_logs dlck_ingester_measure dlck_ingester_spill dlck_pgdata dlck_redisdata infra_chdata infra_pgdata infra_redisdata tutor-infra_pgdata`; `docker volume rm infra_pgdata infra_chdata infra_redisdata dlck-infra_pgdata dlck-infra_chdata dlck-infra_redisdata` → in đủ sáu tên; sau: `dlck_chdata dlck_ingester_logs dlck_ingester_measure dlck_ingester_spill dlck_pgdata dlck_redisdata tutor-infra_pgdata` — đúng 6 `dlck_*` + `tutor-infra_pgdata` không đụng. **→ AC9: PASS.**

Bảng AC ở mục "Đóng lát" cập nhật theo (AC6 ✅, AC9 ✅). Còn lại trước khi khép nhánh: đợt dọn nợ (chủ dự án: "nợ để lại nếu xử lý được thì cũng làm luôn") — subagent Opus, brief `debt-brief.md` ở sổ SDD.

**Dọn Docker theo chỉ đạo chủ dự án 23:20 ("clear hết image và volume cũ luôn, không cần giữ lại gì"):** `docker system df` trước: image 5 (4,08 GB) · **volume 832, 6 đang dùng** (3,2 GB, 2,4 GB thu hồi được) · build cache 37 mục (1,93 GB). Volume vô danh (~825 cái) là rác của các container ClickHouse tạm mà bộ test dựng rồi bỏ — `docker volume prune -f` (chỉ vô danh) → **thu hồi 2,376 GB**; `docker image rm alpine:latest` (không ai dùng) + `docker image prune -f`; `docker builder prune -f` → **1,179 GB**. Sau: image 4 (đều đang dùng) · **volume 7** = 6 `dlck_*` + `tutor-infra_pgdata` (dự án khác — cố ý giữ) · build cache 749 MB đang dùng. Stack `dlck` 7 service nguyên vẹn. Nguồn rác (fixture ClickHouse tạm không tự xoá volume) đưa vào đợt dọn nợ (khoản B13).

**Đợt dọn nợ (chủ dự án: "nợ để lại nếu xử lý được thì cũng làm luôn") — giao subagent Opus 23:25**, brief `debt-brief.md` (sổ SDD): A1 `test_c99` import rác có sẵn · A2 `api` bind `127.0.0.1:8000` · A3 Dockerfile `uv sync` dưới `appuser`, không nhân đôi venv · A4 hằng múi giờ VN về `core.clock` + 10 chỗ `today_vn()` · A5 `configure_alembic_for` · A6 chuỗi "§9" · A7 cột `check` · A8 `_READ` backreference · A9 import `ch_backup` · B1 hợp đồng múi giờ bằng `ast` · B2 unit test `resolve_backup_dir` dời + ca `""`/`"."` · B3–B5 import/docstring test · B6 `today_vn()` · B7–B8 daemon docstring + ca `reconcile` · B9 ba kho không `profiles` · B10 `bootstrap.main()` thiếu biến ⇒ 2 · B11 annotate · B12 ca dương assert giá trị · B13 fixture ClickHouse tạm không để lại volume · C1–C4 tài liệu. Kết quả ghi ở mục kế.

**Đợt dọn nợ — kết quả (2026-09-08 23:25–00:05, implementer Opus, `9eef21a..4f37d67`, 39 file, +268/−148):** `a48219d build(deploy)` — Dockerfile tạo `appuser` + thư mục runtime trước, `USER appuser` rồi `uv sync`, hai `COPY --chown`; image **164.758.755 → 128.549.076 byte (−22 %)**, probe `image: OK` uid 1000, `omo` trong container exit 0, ingester ghi được volume · `f42cf00 refactor(tz)` — một chủ sở hữu `VN` ở `core.clock`, 11 module bỏ hằng riêng, 10 chỗ `datetime.now(…).date()` → `today_vn()` · `1d71061 fix` — `api` bind `127.0.0.1:8000` (healthz OK), `test_c99` import từ `tests.conftest`, `configure_alembic_for`, chuỗi "§9" → "bảng đo", cột `check` căn đều, `_READ` backreference có tên, import `ch_backup` lên đầu · `fec2b1a test` — hợp đồng múi giờ bằng `ast`, `test_ch_backup_paths.py` (+ ca `""`/`"."`), import gom, `today_vn()` đồng hồ đóng băng `2026-01-02`, ca `reconcile` không arm, ba kho không `profiles`, `bootstrap.main()` thiếu biến ⇒ 2, annotate, ca dương assert giá trị, **B13** bốn chỗ dựng container ClickHouse tạm trong test nay tự xoá volume (`--rm` nơi an toàn, `rm -f -v` ở chaos/probe): một file 11→12 trước sửa, 12→12 sau; cả bộ **14→14** · `4f37d67 docs` — README tách hai fence, câu `depends_on` sau reboot ở service-topology §5, roadmap :467 bỏ lặp + ghi chú cổng cho lát 15, số test. Cả bộ tại HEAD (controller chạy lại): **`1136 passed, 3 skipped in 84.77s`**, `[DEBUG-` 0. Lệch có lý do (chấp nhận): A8 backreference có tên + đối chứng âm `FOO` (vì `X` không match cả hai regex, ca sẽ rỗng nghĩa); B6 ghim `2026-01-02` thay ngày hôm nay (không ghim thì test qua kể cả khi không monkeypatch). **Nợ mới phát hiện, để lại:** thứ tự chạy `tests/etl` trước `tests/core` làm `test_reseed_*` (bootstrap) đỏ vì dữ liệu test va nhau — thứ tự mặc định (theo tên) xanh, `pytest tests/core tests/etl` xanh (847 passed); cần cô lập dữ liệu của hai nhóm, ghi cho lát kế. Re-review phạm vi hẹp (Opus): ghi ở mục kế.

**Re-review đợt dọn nợ (Opus, 00:05–00:20):** 27/27 ADDRESSED, 0 Critical/Important mới; reviewer tự chạy lại các phép kiểm (regex `_READ` cũ nuốt `os.getenv("FOO')`, mới trả None; bộ quét `ast` 131 file 0 hit; ba nhãn `check` cùng 7 ký tự NFC; `bootstrap.main()` chạm DB 3 dòng SAU `return 2`; B13 bốn chỗ). Một thay đổi bắt buộc ngoài brief: `test_i15_recovery_drain.py` dời seam giả đồng hồ vì A4 làm `main_mod.datetime` giả bất động — literal và assertion giữ nguyên.

**Nợ mới phát hiện — xử lý luôn (`5ea6a80`, controller tự làm — việc nhỏ §4.1):** `tests/etl` chạy trước `tests/core` ⇒ `test_reseed_skips_when_security_is_empty` đỏ (`('seeded', 2)` thay `('skipped:security-rong', 0)`): hai test reseed **giả định** `market.security` rỗng, còn bộ test dùng một DB phiên tích luỹ (module ETL cố ý commit dòng). Sửa: fixture `empty_security` (scope module) `TRUNCATE market.issuer_industry_override, market.security CASCADE` chỉ trên DB đuôi `_test` — nhóm test tự dựng tiền đề thay vì trông vào thứ tự. RED `pytest tests/etl tests/core` → `1 failed, 609 passed`; GREEN cùng lệnh → **`671 passed, 1 skipped`**; module riêng `6 passed`; cả bộ **`1136 passed, 3 skipped in 85.37s`**.


## Khép nhánh — 2026-09-09 00:40 (chủ dự án chọn "merge cục bộ vào `main`")

Skill `finishing-a-development-branch`: cả bộ trên cây sắp tích hợp (`7f730fc`) → `1136 passed, 3 skipped in 84.87s`; repo thường (không worktree), gốc `main` = `1ec3005`, nhánh đi trước 64 commit, `main` không đổi, `git pull --ff-only` → `Already up to date.` Lần merge đầu thất bại vì thao tác (`git merge -F -` không đọc stdin — `could not read file '-'`), lượt test ngay sau đó chạy nhầm trên `main` **cũ** (`1 failed, 630 passed, 440 errors` — code cũ đọc `.env` kiểu URL, không liên quan kết quả merge; ghi lại vì §3.2). Merge lại đúng: `git merge --no-ff feat/container-runtime -F <file>` → **`fb72a10`** (cha `1ec3005` + `7f730fc`); cả bộ trên `main` đã merge → **`1136 passed, 3 skipped in 86.99s`**. Sau đó: ghi ngày/SHA merge vào `roadmap.md` (dòng lát 12 §3, bàn giao lát 13) và `docs/90-records/README.md` (một commit docs trên `main`, theo khuôn các lát trước), `git push origin main`, `git branch -d feat/container-runtime`. Kết quả push và xoá nhánh ở mục kế.

**Kết quả khép nhánh (00:45):** commit docs trên `main` `bfcd3fe` (roadmap dòng lát 12 §3 + bàn giao lát 13 + §0, `docs/90-records/README.md`, ledger; `tests/docs` 20 passed). `git push origin main` → `09e3a5f..bfcd3fe  main -> main` (fast-forward; remote trước đó ở `09e3a5f`). `git branch -d feat/container-runtime` → `Deleted branch feat/container-runtime (was 7f730fc)`. `main` local = remote = `bfcd3fe`. **Lát 12 khép.** Điểm vào lát 13: roadmap §3 "Điểm vào cho lát 13".

## Sự cố bí mật — 2026-09-09 07:05–07:35 (GitGuardian báo sau khi push `main`)

**Cảnh báo:** "5 internal secret incidents — Generic Password" trỏ commit `1182b99` (Task 1, 12:01 08/09), `9e725d7` (Task 8, 15:44) và merge `fb72a10`. Kiểm: các dòng bị bắt ở hai commit đó là **literal test/template** (`pw-owner` · `p@ss:w/rd` (seam URL-quote spec §6) · `pw-ch` · `pw-ing` · `pw-agent` trong `test_env.py`; `pw-one`/`pw-two` trong test bootstrap; template `postgresql+psycopg://{USER}:{PASSWORD}@…` trong `core/env.py`) — dương tính giả, không phải giá trị thật.

**Nhưng phép kiểm quyết định lộ một rò thật:** quét toàn lịch sử (`git log --all -S<giá trị>`, chỉ in tên khoá + số đếm) cho 26 giá trị bí mật thật (`.env` hiện tại, `.env.bak-2026-09-08` trước chuyển đổi, `.env.bak-ac6-2026-09-08` trước xoay ETL): **`POSTGRES_PASSWORD` (mật khẩu owner Postgres, 23 ký tự) xuất hiện trong 9 commit và 4 file đã track**; 25 giá trị còn lại 0 hit. Nguồn: `8f51702` (2026-08-24, plan deploy-scaffold dán `.env` mẫu bằng mật khẩu thật) → `1e5cc03` (25/08, `.env.example` mang giá trị thật, tới khi Task 2 lát 12 viết lại 13:24 08/09) → ba plan/ledger khác trích lại (`2026-08-25-clickhouse-realtime-store/plan.md`, `2026-08-26-ingester-omo-first-slice/plan.md` — nơi cùng giá trị từng được dùng làm mật khẩu ClickHouse `default`/`ingester_worker`/`etl_worker`, và `2026-09-07-audit-drift-cleanup/ledger.md:71`). Repo **public** (HTTP 200 ẩn danh, raw đọc được) ⇒ giá trị đã công khai từ 24/08. Bán kính thật: Postgres chỉ bind `127.0.0.1` trên máy dev, chưa có VPS; các mật khẩu khác hiện hành không trùng (0 hit).

**Xử lý (07:20–07:33):** (1) xoay mật khẩu owner: `ALTER USER "dulieu" PASSWORD …` trong container qua stdin (không qua dòng lệnh, không in), rồi `.env` (`old len=23 -> new len=32`, sao lưu `.env.bak-pg-2026-09-09`), `docker compose up -d` tạo lại service (postgres tạo lại vì env đổi, dữ liệu trong volume nguyên), `docker compose run --rm migrate` → 5 dòng `bootstrap:`; đối chứng native: **old REJECTED (password authentication failed) · new ACCEPTED (current_user=dulieu)**. (2) `b43710e` — che giá trị trong 4 file (`<REDACTED 2026-09-09>`, 6 chỗ) + test mới `tests/docs/test_d04_no_real_secrets_in_repo.py`: mọi giá trị khoá `*_PASSWORD|_API|_KEY|_TOKEN|_SECRET` dài ≥ 8 của `.env` thật không được có trong file đã track (`git grep -F`, chỉ in tên khoá + tên file; skip khi không có `.env`). RED: 4 file với giá trị cũ · GREEN: 0/0; `tests/docs` 22 passed. Push `0ac7709..b43710e`.

**Còn lại, quyết định chủ dự án:** (a) lịch sử git trên GitHub vẫn chứa giá trị cũ (đã vô hiệu) — muốn sạch hẳn cần viết lại lịch sử (`git filter-repo --replace-text`) + force-push + mọi clone kéo lại; (b) đánh dấu 5 incident GitGuardian là false positive (literal test) và đóng incident của giá trị thật sau khi xoay; (c) nếu mật khẩu cũ từng dùng lại ở nơi khác ngoài repo (thói quen), đổi nốt ở đó. Bài học vào CLAUDE.md §5 ở lượt kế: **không bao giờ dán `.env` mẫu bằng giá trị thật vào plan/ledger** — test `test_d04` nay canh máy móc.

**Quyết định chủ dự án (2026-09-09 ~08:00):** **không** viết lại lịch sử git (không cần thiết — giá trị đã xoay, vô hiệu; mật khẩu cũ chưa từng dùng ở nơi nào khác); đóng incident GitGuardian — thao tác trên dashboard của chủ dự án (trợ lý không có quyền truy cập dịch vụ đó). Sự cố khép; lát 12 khép hoàn toàn tại `main` `d33861d`.
