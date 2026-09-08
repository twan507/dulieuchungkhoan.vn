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
| 6 | Task 5 | Hit grep còn lại là `backend/README.md` (docs, Task 11); gỡ import `sys` mồ côi; docstring `core/shutdown.py` **thu hẹp** vì ingester không có `except KeyboardInterrupt` — đường dừng tử tế chuyển sang Task 6 (`install_loop_stop`), spec có đính chính | — |
| 7 | Task 6 | Step 3c: tách event `shutdown` (tín hiệu) khỏi `stop` của từng phiên (mốc giờ), relay mỗi phiên; ba test cũ gọi `run("run", minutes=1)`. Step 3d: chỉ cài `install_loop_stop` ở `run`/`measure` để `count`/`reconcile` còn ngắt được | Thêm một task relay mỗi phiên |
| 8 | Task 9 | Chặn ở AC4 ⇒ Task 9a: Dockerfile tạo sẵn và `chown` ba thư mục runtime + `/backups`; mở file log vào hợp đồng exit 2; xoá ba volume `dlck_ingester_*` rỗng rồi tạo lại | Volume tạo lại một lần (rỗng) |
| 9 | Task 9a | `chown /backups` trong image vô tác dụng (bind mount) — **giữ, vô hại**; AC7 là phép kiểm thật | Một thư mục thừa trong image |
| 10 | Sau AC7 | `.env` cũ `CLICKHOUSE_BACKUP_DIR=./clickhouse-backups` (gốc `deploy/infra` cũ) ⇒ sửa về `./deploy/infra/clickhouse-backups`, dời zip, tạo lại service | — |

**Minor để dành cho review toàn nhánh (Task 12), không mở vòng sửa:** T1 import giữa file `test_env.py`; `check()` coi khoá khai rỗng là có; T2 contract test không có fixture phản ví dụ, hai docstring nói cùng ý; T3 `resolve_backup_dir` thiếu ca `""`/`"."`; T4 năm chỗ `datetime.now(VN).date()` có sẵn chưa dùng `today_vn`, `today_vn()` không đối số chưa test đồng hồ giả; T5 `install_signal_handlers` để lại handler trong test in-process, danh sách test hồi quy của brief thiếu 7 file CLI (reviewer đã chạy: 48 passed); T6 docstring `daemon()` thiếu nhánh thoát theo tín hiệu, ba khối import rải trong `test_i16`, `shutdown` tạo cả cho `count`/`reconcile`; T7 contract compose không chặn `profiles` quay lại, **rác có sẵn** `test_c99_dedup_probe.py:20` import ba tên đã dời (chỉ vỡ khi `RUN_PROBE=1`); T8 `main()` chưa test trực tiếp, `_ch_literal` chưa test mật khẩu có quote; T9a regex Dockerfile không ghim `/backups` trong `chown`, hai dấu cách trước `&&`.

## Hướng dẫn nối phiên (đọc trước khi làm gì)

1. Nhánh `feat/container-runtime`, HEAD là commit ledger này; **chưa merge, chưa push**. Điểm dừng ở mục ⏸️ phía trên; việc còn lại = plan Task 10 (từ họ `events`), AC6, Task 11, Task 12.
2. Quy trình: `superpowers:subagent-driven-development` với plan [`plan.md`](plan.md); **mọi subagent model `sonnet`** (review toàn nhánh Task 12 nâng `opus`); workspace SDD đặt ở **scratchpad ngoài repo** (không tạo `.superpowers/`); brief từng task trích lại bằng `scripts/task-brief plan.md <N> <file>` của skill; harness **không có SendMessage** ⇒ mỗi vòng sửa là một implementer mới mang brief + report + findings.
3. **`tests/docs` đang đỏ có chủ đích** (link chết tới file đã xoá ở Task 5/7) cho tới Task 11 Step 7b; đừng "sửa" bằng cách nới test. Cả bộ `pytest tests -q` chỉ chạy ở Task 11 Step 8 và Task 12.
4. Chủ dự án đã **uỷ quyền sửa `.env`** (AC6 dùng quyền này: đổi `ETL_DB_PASSWORD`, `docker compose run --rm migrate`, `run --rm etl python -m etl omo`). Không bao giờ in giá trị.
5. Kho dev là **disposable** (chủ dự án chốt xoá dựng lại); stack `dlck` để nguyên là được — `docker compose run --rm etl …` tự chạy lại `migrate` (idempotent) qua `depends_on`.
6. Sáu volume cũ `infra_*`/`dlck-infra_*` chỉ xoá ở Task 12 sau khi mọi AC xanh; **không đụng `tutor-infra_pgdata`**. 11 task Windows: chủ dự án gỡ bằng một lệnh PowerShell ở Task 12 Step 2.

**Cập nhật lúc khép phiên:** họ `events` đã tự kết thúc `success` sau khi operator bị ngắt — Task 10 nối từ họ `price`.
