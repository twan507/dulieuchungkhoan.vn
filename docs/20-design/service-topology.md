# Ranh giới service backend dulieuchungkhoan.vn

**Ngày:** 2026-08-24 · **Trạng thái:** ✅ chốt trước khi viết dòng code đầu tiên · **Phạm vi:** cách chia backend thành các process, ai ghi cái gì, ai mở cổng cho ai

Tài liệu này chốt **ranh giới runtime** của `backend/` — không phải chia code, mà chia **process**. Nó trả lời một câu duy nhất mà các tài liệu thiết kế khác để ngỏ: *ba–bốn thứ chạy trong backend là mấy tiến trình, tiến trình nào deploy độc lập tiến trình nào, và dữ liệu đi vào–ra qua đâu.* Chốt trước khi code vì đảo ranh giới process sau khi đã viết là đắt.

Nền tảng đã có: monorepo + stack chốt ở [ADR 0007](../00-overview/decisions/0007-monorepo-layout-and-stack.md) *(Next.js · Python/FastAPI · Postgres + ClickHouse + Redis)*. Luồng realtime và cách ly nguồn ở [kho dữ liệu thị trường](market-data-store.md). Tài liệu này đứng trên cả hai, không lặp lại chúng.

---

## 1. Quyết định một câu

**Backend là một monorepo, chạy thành ba tiến trình tách biệt theo vòng đời, dùng chung một thư viện lõi.** Không phải một khối, cũng không phải ba repo.

```
                        backend/  (một monorepo, một thư viện lõi dùng chung)
   ┌───────────────────────────┬───────────────────────────┬───────────────────────────┐
   │  ingester (daemon)        │  etl (job theo lịch)       │  api (web server)         │
   │  active + standby         │  cron/scheduler            │  stateless, scale ngang   │
   │  socket BVSC sống dai     │  batch sau phiên           │  cổng công khai cho FE    │
   └───────────┬───────────────┴─────────────┬─────────────┴──────────────┬────────────┘
               │ ghi                          │ ghi                        │ đọc (+ghi user)
   ┌───────────▼──────────────────────────────▼────────────────────────────▼────────────┐
   │  Redis  (pub/sub · HASH state · leader lock · token bucket phân tán)                │
   │  ClickHouse  (tick thô · sổ lệnh · bar_1m)                                          │
   │  Postgres  (tham chiếu · giá EOD · BCTC · snapshot · sự kiện · tin · DỮ LIỆU USER)  │
   └────────────────────────────────────────────────────────────────────────────────────┘
                                              ▲
                                              │  realtime: ingester → Redis pub/sub → SSE của api → FE
                                              │  FE chỉ nói chuyện với api, không bao giờ với ingester/etl
```

## 2. Ba tiến trình

| Service | Loại | Cổng người dùng | Sở hữu (ghi) | Mô hình chạy | Deploy độc lập với |
|---|---|---|---|---|---|
| **`ingester`** | Daemon socket sống dai | ❌ không *(chỉ health/metrics nội bộ)* | Redis HASH state + pub/sub · tick + `bar_1m` (ClickHouse) | **Active + standby**, leader election qua Redis lock, tiếp quản < 2 s | `api`, `etl` |
| **`etl`** | Job theo lịch (batch) | ❌ không *(chỉ metrics)* | Bảng tham chiếu · giá EOD · snapshot · screener · sự kiện · BCTC (Postgres) · crawl OMO/vĩ mô/quốc tế · tin | Scheduler gọi, chạy rồi thoát; một số job kích hoạt theo sự kiện | `api`, `ingester` |
| **`api`** | FastAPI web server | ✅ **cổng công khai duy nhất** | **Dữ liệu user** (tài khoản, watchlist, danh mục…) trên Postgres | **Stateless, nhân bản ngang** nhiều instance sau load balancer | `ingester`, `etl` |

### `ingester` — vì sao phải một mình

Đây là ràng buộc cứng, không phải thẩm mỹ. Ba lý do, xếp theo sức nặng:

1. **Vòng đời đối nghịch với `api`.** `api` deploy lại liên tục mỗi lần thêm tính năng. Nếu ingester chung tiến trình, mỗi lần deploy `api` là **ngắt websocket → rớt tick → mất vĩnh viễn** *(kho dữ liệu §3.3 — API không có endpoint replay)*. Tách ra để redeploy `api` bao nhiêu lần cũng không đụng luồng thu.
2. **Mô hình lỗi đối nghịch.** Ingester phải là **một-leader active+standby** *(kho dữ liệu §3.1)*. `api` thì ngược lại — **nhiều instance ngang nhau**. Không nhét được hai mô hình này vào một tiến trình.
3. **Hình dạng runtime khác.** Ingester = một socket outbound sống dai + batch writer ngoài hot path. `api` = request/response. Một cái chết không được kéo cái kia.

Ingester **không mở cổng cho FE**. FE lấy realtime qua **SSE của `api`**, mà `api` đọc từ **Redis pub/sub** do ingester bơm vào *(kho dữ liệu §3.4)*. Ranh giới thật ở đây là **tiến trình + vòng đời**, không phải "hai server hai cổng".

### `etl` — gom mọi việc ghi theo lịch, tách khỏi ingester

Ingester lo dữ liệu **perishable theo giây** (tick). `etl` lo mọi thứ ghi **theo lịch/theo lô**: bảng tham chiếu, giá EOD, snapshot, screener, sự kiện, BCTC *(kho dữ liệu §4)*, cộng các crawl nguồn khác (OMO của SBV, vĩ mô WiChart, quốc tế, tin). Để chung tiến trình với ingester là sai — một cái socket dai không được ngắt, một cái batch ngắt quãng chạy-rồi-thoát. Nhưng cả hai **chung thư viện lõi**.

> ⚠️ **Crawl OMO cũng perishable** *(SBV chỉ hiện phiên mới nhất — [`macro/sbv-omo.md`](../10-sources/macro/sbv-omo.md))*, nhưng nó là **HTML theo ngày**, không phải tick theo giây, nên thuộc `etl` (một job chạy mỗi ngày), không thuộc `ingester`.

### `api` — tiến trình duy nhất người dùng chạm tới

Phục vụ: REST (lịch sử, BCTC), SSE (realtime, subscribe Redis pub/sub), chatbot (function calling), và **CRUD dữ liệu tương tác user** (tài khoản, watchlist, danh mục). Là tiến trình **duy nhất** mở cổng công khai. Stateless → scale ngang thoải mái.

🔴 **`api` không bao giờ gọi thẳng BVSC/FiinTrade khi phục vụ user** *(nguyên tắc cách ly hoàn toàn — kho dữ liệu §1)*. Mọi dữ liệu thị trường `api` phục vụ đều đọc từ kho riêng hoặc Redis.

## 3. Thư viện lõi dùng chung

Ba tiến trình **không sao chép code**. Một package lõi trong monorepo giữ phần chung, mỗi service là một entrypoint mỏng trên nó:

- Client kết nối DB + model/schema (Postgres, ClickHouse, Redis)
- Client nguồn (BVSC, FiinTrade, WiChart, FRED, ECB, Yahoo, LBMA, Binance)
- Từ điển mã trường + bảng hệ số đơn vị *(các bẫy đơn vị ở [quy ước chung](../10-sources/market/00-conventions.md))*
- **Rate limiter phân tán trên Redis** *(xem §5)*
- Config + nạp bí mật *(`.env`, không in giá trị khoá)* + logging

## 4. Ai ghi cái gì — một người ghi cho mỗi miền

Luật để tránh hai tiến trình cùng ghi một chỗ rồi giẫm nhau:

| Miền dữ liệu | Kho | Người ghi duy nhất | Người đọc |
|---|---|---|---|
| Tick · sổ lệnh · `bar_1m` · realtime state | ClickHouse + Redis | `ingester` | `api` (qua Redis pub/sub + ClickHouse) |
| Tham chiếu · giá EOD · BCTC · snapshot · sự kiện · tin | **`postgres-data`** | `etl` | `api` |
| Tài khoản · watchlist · danh mục · tương tác user | **`postgres-app`** | `api` | `api` |

FE chỉ đọc–ghi qua `api`. `api` chỉ ghi **miền user**; với dữ liệu thị trường nó là **read-only**.

> **2026-08-26 — retention ClickHouse (schema `rt`, [spec](../90-records/plans/2026-08-25-clickhouse-realtime-store/spec.md)):** 5 bảng frame thô (`trade`/`quote`/`snapshot_delta`/`index_delta`/`pt_match`) giữ **cửa sổ trượt TTL 3 tháng khai báo, thực tế 3–4 tháng** do hành vi drop theo part; hai bảng nến `bar_1m`/`index_bar_1m` **không TTL, giữ vĩnh viễn**. Đây là cơ sở cho ngoại lệ backup ở dưới.
>
> **Điểm nối hệ số điều chỉnh giá — đã đổi hướng so với thiết kế Postgres ban đầu:** ClickHouse chỉ lưu **giá thô**, không biết Postgres tồn tại và không phụ thuộc nó. Chiều phụ thuộc là ngược lại — **`api` cần đọc view hệ số bên Postgres (`market`)** để điều chỉnh giá lúc trả cho người dùng (giá thô × factor), tra qua ba chặng `symbol` (ClickHouse, là ticker) → `market.security` → `security_id` → factor.

> 🔴 **Hai instance Postgres riêng — chốt D (2026-08-25).** Dữ liệu thị trường và dữ liệu user nằm ở **hai instance Postgres tách hẳn** (`postgres-data` và `postgres-app`), **không** chỉ khác schema, **không** chung instance. Ba lý do:
> 1. **Backup khác chế độ (điểm quyết định):** data user cần **PITR**/backup dày (mất là mất thật); data thị trường **crawl lại được** nên không cần — **ngoại lệ: `bar_1m`/`index_bar_1m` bên ClickHouse KHÔNG crawl lại được** (nguồn realtime không có endpoint replay — [kho dữ liệu §3.3](market-data-store.md)) nên có backup hằng đêm riêng ([quyết định #10 của spec ClickHouse](../90-records/plans/2026-08-25-clickhouse-realtime-store/spec.md)); tiền đề "crawl lại được nên không cần backup" chỉ còn đúng cho phần Postgres. PITR/WAL là **theo cả instance** → muốn hai chế độ thì buộc hai instance.
> 2. **Blast-radius:** kho thị trường **churn nặng** (migrate/rebuild liên tục) — không được chung volume với account.
> 3. **Tuning riêng:** phân tích (buffer lớn) vs OLTP nhẹ.
>
> **Kỷ luật giữ ngay từ thiết kế** (làm C↔D chỉ là đổi config, không sửa code): **hai connection string tách** (`DATA_DATABASE_URL` / `APP_DATABASE_URL`) và **cấm JOIN chéo hai miền** (watchlist = danh sách mã, giá lấy qua đường bình thường). **Thời điểm dựng:** `postgres-app` thêm vào [`deploy/infra`](../90-records/plans/2026-08-24-deploy-scaffold/spec.md) khi dựng `api` auth/watchlist; lát REST-first chỉ cần `postgres-data`.

## 5. Hệ quả bắt buộc phải tôn trọng

Tách tiến trình kéo theo vài ràng buộc không được quên:

1. 🔴 **Rate limiter phải lên Redis, không để in-memory.** Thiết kế *(kho dữ liệu §4.3)* yêu cầu `etl` và chatbot **dùng chung một ngân sách token bucket** — "nếu không, quét đêm làm chatbot ban ngày bị chặn". Khi `etl` và chatbot ở hai tiến trình khác nhau, token bucket trong bộ nhớ không chia sẻ được nữa ⇒ **bucket phải sống trong Redis**.
2. **Redis là trục nối bắt buộc giữa ba tiến trình**, không phải cache tuỳ chọn: pub/sub fan-out realtime, HASH current-state, leader lock cho ingester, và token bucket phân tán. Mất Redis là mất cả realtime lẫn điều phối.
3. **`ingester` deploy độc lập.** Pipeline CI/CD phải cho phép redeploy `api` mà không chạm `ingester`. Đây là toàn bộ lý do tách ở §2.
4. **`api` không có trạng thái cục bộ.** Mọi trạng thái chia sẻ (session realtime, current-state) nằm ở Redis/DB, để nhân bản ngang không lệch nhau.
5. ✅ **Task Scheduler đã chuyển `S4U` 2026-08-28 — cửa sổ `cmd` không còn.** **Cả 9 task** mang `LogonType=S4U` — 7 task đầu (`dlck-ingester`, `dlck-ingester-measure`, `dlck-refdata`, 4 task OMO) từ 2026-08-28, thêm `dlck-screener` 15:20 và `dlck-events` **18:10** đăng ký thật **2026-09-03** *(task thứ 10 `dlck-price` **15:40** đã vào script 2026-09-04, đăng ký thật chờ cửa sổ admin — [plan lát 3](../90-records/plans/2026-09-03-price-daily-etl/plan.md) Task 7)* *(giờ của `dlck-events` chọn 18:00 lúc đầu, dời sang 18:10 ngay trong ngày vì đụng `dlck-omo-1800` — cùng lý do `dlck-screener` đặt lệch 15:30)*, `RunLevel=Limited`, `UserId=tuanb` *(nghiệm thu bằng cách soi `Principal` TỪNG task, không soi trạng thái — `Assert-TaskPrincipal` trong `scripts/register-tasks.ps1`, soi CẢ `LogonType` LẪN danh tính chạy dưới quyền ai)*. Trước đó là `Interactive` với ba hệ quả: (a) chỉ chạy khi có người đăng nhập; (b) mỗi lượt hiện một cửa sổ `cmd` — bấm nhầm dấu X trên cửa sổ `dlck-ingester` là **giết phiên ghi tick**, thứ duy nhất không crawl lại được; (c) không có quyền admin. **(b) là cái đắt nhất và nay đã hết.**

    🔴 **Nhưng "chạy cả khi không đăng nhập" chỉ đúng MỘT NỬA — đừng đọc thành "pipeline sống sót qua log off".** Bản thân task S4U chạy được khi không ai đăng nhập, nhưng **hai kho và Redis nằm trong Docker Desktop, mà Docker Desktop sống trong session người dùng** *(đo 2026-08-28: `com.docker.service` = `Stopped`/`Manual`, các tiến trình `Docker Desktop` đều ở `SessionId = 1`)*. Log off là container tắt theo, task vẫn nổ đúng giờ nhưng **không có gì để kết nối**. Muốn thật sự chạy không cần đăng nhập thì phải đưa engine ra khỏi session trước — việc riêng, **chưa làm**.

    🔴 **Đã xảy ra thật 2026-09-03 — và không phải log off, là REBOOT.** Máy boot lại **08:00:45** *(ngay sau lượt `refdata` 08:00:03 của boot cũ)*. **Docker Desktop không tự khởi động sau reboot trên máy này** — 08:35 vẫn không có tiến trình nào. Task S4U nổ đúng 08:30: `dlck-ingester` chết ở **hợp đồng khởi động** (`assert_migrated` → ClickHouse 8123 từ chối kết nối → exit 3); `dlck-ingester-measure` sống vì chỉ ghi đĩa. Log không có lượt khởi động lại nào giữa 08:30 và 08:37 dù task đăng ký `RestartInterval` 5 phút — **đừng trông vào RestartCount cho ca này**. Dựng lại tay: mở Docker Desktop *(engine lên sau ~5 s, ba container `infra-*` tự lên nhờ `restart: unless-stopped`)* → `Start-ScheduledTask dlck-ingester` **08:37:34** → giành leader, 6.081 topic, chạy tới 15:05; 08:48 kho đã có 710 quote. **Không mất tick** (phái sinh mở 08:45). Bẫy phụ: `npm run dev-start` trên máy này dựng bộ `dlck-infra-*` **thứ hai** đụng cổng 5432 (README §"Hai bộ volume") — sau reboot chỉ cần mở Docker Desktop, không chạy `dev-start`. **Việc chưa làm** *(quyết định chủ dự án)*: bật *Start Docker Desktop when you sign in*, và/hoặc cho ingester **chờ kho có giới hạn** lúc khởi động thay vì thoát ngay. **Lặp lại lần hai 2026-09-03 ~23:35** *(reboot, Docker Desktop lại không lên; test của lát 3 đỏ với `connection timeout` trước khi lộ lỗi code nào — dựng lại đúng cách trên, ~10 s)*. **Và một dạng hỏng thứ ba, 2026-09-04 02:00: máy NGỦ** *(System event 42 → 107/1 lúc 05:56)* — ba container sống qua giấc ngủ, nhưng tiến trình đang gọi HTTP thức dậy với `httpx.ReadTimeout`; job dài chạy đêm (backfill giá, 25–40 giờ) phải tắt sleep trước — [backend/README](../../backend/README.md) mục `etl price`.

    ⚠️ **Đăng ký lại phải làm ngoài giờ chạy** — `Register-ScheduledTask -Force` lên task đang `Running` sẽ giết tiến trình; cửa sổ an toàn là sau **15:10**. Và script đăng ký lại **cả bảy** bằng `-Force`, nên task nào đang cố ý `Disabled` sẽ sống lại ở trạng thái BẬT — script tự in dòng nhắc tắt lại. Bẫy `-UserId` phải qualified `DOMAIN\user` nằm ngay trong comment của script, không chép lại ở đây.

## 6. Bố cục thư mục và cổng (đề xuất)

```
backend/
├── core/            thư viện lõi dùng chung (db, clients, ratelimit, config, dictionary)
├── ingester/        entrypoint daemon realtime
├── etl/             entrypoint job theo lịch + các crawler
├── api/             entrypoint FastAPI
└── agent/skills/    hai skill chứng khoán (đã có, sản phẩm chạy được)
```

| Tiến trình | Cổng (dev) | Ghi chú |
|---|---|---|
| `api` | 8000 | cổng công khai, FE (Next.js :3000) gọi vào đây |
| `ingester` | 8100 | chỉ health/metrics, không phục vụ dữ liệu |
| `etl` | — | không cổng; scheduler kích hoạt (metrics 8200 nếu cần) |

## 7. Lát cắt dọc đầu tiên chỉ cần phía writer

Để **dừng đồng hồ mất dữ liệu** *(nến 1 phút + OMO — [lộ trình §2](../00-overview/roadmap.md))*, lát cắt đầu tiên **không cần `api`**, vì chưa có gì để phục vụ:

```
hạ tầng (docker-compose: PG + ClickHouse + Redis)
   → DDL tối thiểu: bar_1m/tick (ClickHouse) + instrument tối thiểu (PG)
      → ingester: nối socket BVSC → Redis → ClickHouse   ← dựng trước
      → etl: một job crawl OMO → Postgres                ← dựng cùng
```

`api` (reader + user) dựng sau khi kho đã có dữ liệu. Điều này khớp với hướng "làm phía backend ghi dữ liệu trước" — hiểu đúng nghĩa hẹp là **phía writer trước**.

> ✅ **Đã đo 2026-08-26** *(cập nhật — trước đó mục này ghi "chưa được giả định có tick phái sinh")*: phái sinh **có** tick realtime và **đi chung ba topic `i`/`o10`/`t`** với cổ phiếu, phân biệt bằng `EX = "XHNF"`, cấu trúc trường giống hệt, **không có `openInterest`** trong luồng ([hồ sơ đo](../90-records/surveys/2026-08-26-bvsc-realtime-session/README.md)). Lát cắt đầu **vẫn chỉ đăng ký cổ phiếu/ETF/chỉ số** — mã phái sinh không có trong `/quotes` nên danh mục runtime không thấy chúng; mở rộng là quyết định phạm vi riêng, cần chốt cùng lược đồ (dùng chung bảng hay tách).

> **Lát cắt này đã dựng xong và merge `main` 2026-08-26** — `ingester` chạy theo phiên (3 chế độ: đo · ghi thật · đối chứng) và job `etl omo` chạy 4 mốc/ngày. Hồ sơ: [plans/2026-08-26-ingester-omo-first-slice/](../90-records/plans/2026-08-26-ingester-omo-first-slice/).

## 7b. Ngân sách tài nguyên VPS — 6 GiB / 4 core / 60 GB

*(Đo 2026-08-27 trên máy dev đang chạy phiên ghi thật 2.021 mã. Máy đích: 4 core · 6 GiB RAM · 60 GB đĩa.)*

**Con số hiển thị KHÔNG phải nhu cầu.** ClickHouse tự cấp cache theo RAM nó nhìn thấy: trên dev (container thấy 31 GiB) nó lấy trần 18,74 GiB và mark cache 5 GiB, RSS 1,41 GB — trong khi **nhu cầu thật `MemoryTracking` chỉ 427 MB**. Đọc RSS rồi kết luận "ClickHouse cần 1,4 GB" là đọc nhầm cache thành nhu cầu.

| Thành phần | Đo trọn phiên 2026-08-27 | Cấp trên VPS |
|---|---|---|
| ClickHouse | trung bình 373 MB · **đỉnh 1,18 GiB** (RSS đỉnh 1,80 GiB) | 2,0 GiB mềm · **2,6 GiB cứng** |
| Postgres | 74 MB | 1 GiB |
| Redis | 11 MB | 256 MiB (trần 192 MB) |
| Ingester (ghi, nền — KHÔNG gồm hàng đợi spill) | **97 MB** | 200 MB *(chung với phiên đo)* |
| Ingester (đo `--measure`, chạy thường trực cạnh phiên ghi từ 2026-08-27) | **13 MB** | — nằm trong 200 MB trên |
| ↳ Hàng đợi ghi RAM `pending` *(lát [tràn-ra-đĩa](../90-records/plans/2026-08-28-ingester-spill-to-disk/spec.md), Task 6)* | tách riêng khỏi dòng "97 MB" — trần `N_CAP_ROWS = 100.000` dòng × 497 B ≈ **49,7 MB** | ≤ ~50 MB *(200 − 97 nền − 13 đo − ~12 `buffers` 5 bảng × 5.000 dòng, spec §2.5)* — **97/200 KHÔNG còn dư nguyên**, phần dư đã cấp cho hàng đợi này |
| OS + Docker · API · ETL · pipeline tin | — | ~1,6 GB |
| **Cộng** | | **~5,6 GB — dư ~0,4 GB** |

> **Đĩa — vùng spill** *(lát tràn-ra-đĩa, spec §2.5/§3, code `backend/ingester/spill.py`)*: trần **`SPILL_CAP_BYTES = 10 GiB`**, căn cứ pickle đo thật **65 B/dòng** (`rt.trade`, block 5.000 dòng = 323.657 B — probe §9.2 spec) — đích chịu **≥ 2 giờ sự cố ở tải đỉnh × hệ số an toàn 3**: 6.496 dòng/s × 7.200 s × 65 B × 3 ≈ 9,1 GB ≤ 10 GiB. Thư mục spill (mặc định `dlck-runtime/spill`, biến `INGESTER_SPILL_DIR`) **không nằm trong RAM** ở trên — nó cộng vào cột đĩa 60 GB cùng kho CH ~5 GB + bản đo 30 ngày ~2,8 GB, vẫn thoải mái trong ngân sách.

🔴 **Đính chính bản đầu (viết sáng 2026-08-27, trước khi có phiên trọn):** bản đầu ghi *"ClickHouse cần thật 427 MB, biên ~3,5×"* và kết luận dư 1,5 GB. **Sai** — 427 MB là số đo lúc 09:00, tức **đầu phiên chứ không phải đỉnh**. Đo trọn phiên cho đỉnh **1,18 GiB**, gần gấp ba. Trần mềm 1,5 GiB của bản đầu sẽ bị tải thật chạm 79%; nay nâng lên 2,0 / 2,6 GiB.

> Bài học đúng họ §1.3: một phép đo *thành công* vẫn có thể trả lời **sai câu hỏi** — hỏi "đỉnh là bao nhiêu" mà đo một điểm giữa phiên yên tĩnh.

**Hai lớp trần, lớp mềm chạm trước.** ClickHouse có `max_server_memory_usage` (mềm — ném `MEMORY_LIMIT_EXCEEDED`, hỏng có kiểm soát) thấp hơn `mem_limit` của Docker (cứng — OOM-kill). Thứ tự này là chủ đích: lỗi có dấu vết trong log ứng dụng dễ chẩn đoán hơn một tiến trình biến mất.

`memswap_limit` đặt **bằng** `mem_limit` ở cả ba service = **cấm swap**. Swap trên VPS biến một sự cố bộ nhớ thành cả máy đứng, khó chẩn hơn nhiều so với một service chết dứt khoát.

🔴 **Ràng buộc RAM đổi bản chất quyết định mô hình embedding.** Tài liệu trước chỉ ràng buộc theo **đĩa** (`halfvec(768)` vì 50 GB — [news-pipeline §9.5](news-pipeline.md)). Trên máy 6 GiB, **chạy model cục bộ ngốn 1–2 GB thường trú, tức ăn hết phần dư 1,5 GB**. Hệ quả: **embedding phải gọi qua API, không chạy cục bộ** — trừ khi nâng máy. Đây là ràng buộc RAM, không phải ràng buộc đĩa, và nó phải nằm trong quyết định chọn model.

**50 người dùng đồng thời không phải ràng buộc.** Gánh nặng là ingester ghi liên tục 2.021 mã (2,3 triệu frame một phiên chiều — [hồ sơ đo](../90-records/surveys/2026-08-26-bvsc-realtime-session/README.md)) và ClickHouse nuốt chúng; vài chục người đọc API là chuyện nhỏ bên cạnh.

**Cách chạy hồ sơ VPS:**

```bash
docker compose -f docker-compose.yml -f docker-compose.vps.yml --profile realtime up -d
```

Overlay [`deploy/infra/docker-compose.vps.yml`](../../deploy/infra/docker-compose.vps.yml) + [`clickhouse/memory-vps.xml`](../../deploy/infra/clickhouse/memory-vps.xml). Không sửa file gốc: máy dev 64 GB ép xuống hồ sơ VPS chỉ làm test chậm mà không lộ thêm điều gì.

### Đỉnh ATO đã đo — 2026-08-27

`block_cap.quote` chạm **đúng một lần**, lúc **09:00:14** — đúng phiên ATO. Trần block chỉ *cắt sớm rồi xếp hàng*, không vứt dòng; cả phiên **0 `dropped_block`, 0 `poison_row`, 0 `normalize_error`**, đối chứng cuối phiên `p1=0 p2=0 ok=868`.

Ghi được **4,27 triệu dòng / 82,2 MB** một phiên *(quote 3,12tr · snapshot_delta 890k · trade 205k · index_delta 56k · nến 1 phút 37k)*. Suy ra ~250 phiên/năm ≈ **20,5 GB/năm frame thô**, mà TTL 3 tháng ⇒ **~5 GB thường trực**; nến vĩnh viễn ~470 MB/năm. Cộng bản đo thô JSONL của phiên `--measure` hằng ngày: **~93 MB gzip/ngày** *(đo 2026-08-27, trọn phiên)*, giữ 30 ngày (job đo tự xoá — `prune_old`, `backend/ingester/measure.py`) ⇒ **~2,8 GB thường trực**. **60 GB đĩa thoải mái.**

⚠️ **Vẫn chưa được nói "đủ".** Đỉnh 1,18 GiB đo trên **dev**, nơi ClickHouse được cấp mark cache 5 GiB và trần 18,74 GiB — nó dùng những gì được cấp. Dưới hồ sơ hẹp (cache 256 MiB) đỉnh sẽ thấp hơn, **thấp bao nhiêu thì chưa biết**. Phải chạy một phiên dưới trần cứng rồi mới kết luận.

### Phiên ĐẦU TIÊN chạy code tràn-ra-đĩa — 2026-08-28

*(Phiên trọn 27/08 ở trên chạy bằng code cũ; lát spill xong tối 27. Nên đây là số đầu tiên nói được điều gì về cơ chế đó.)*

| | 28/08 *(code spill)* | 27/08 *(code cũ)* |
|---|---|---|
| Dòng vào kho | **4.722.406** — quote 3.417.375 · snapshot_delta 1.009.350 · trade 237.450 · index_delta 56.168 · pt_match 2.063 | 4,27 triệu *(quote 3.122.376)* |
| Đỉnh hàng đợi RAM | **3.090 dòng / 1.535.730 B lúc 13:00:04** — **3,09%** của `N_CAP_ROWS = 100.000` | — |
| Chế độ đĩa | `spill_bytes = 0` — **cả phiên chưa lần nào vào** | chưa có cơ chế |
| Sổ sách spill | `orphan_tmp` · `replay_corrupt` · `seq_collision` · `spill_io_error` = **0** | — |
| Đối chứng cuối phiên | `p1=0 p2=0 ok=971` · `pending_depth_rows = 0` lúc đóng | `p1=0 p2=0 ok=868` |
| Độ trễ insert cuối phiên | p50 **14,7** · p95 73,6 · p99 77,4 ms | — |
| **AC3 — hằng đẳng thức sổ sách** | ✅ **dư = 0 trên cả 5 bảng** *(`dup_dropped` 1.974 khớp khít hai vế)* | — |

🔴 **Đỉnh hàng đợi KHÔNG rơi vào ATO.** Mẫu lúc 09:00:02 là 2.948 dòng — gần bằng, nhưng đỉnh thật **3.090 lúc 13:00:04**. Ai lấy mẫu ATO rồi gọi đó là đỉnh sẽ ra số thấp hơn thực tế; phải quét cả phiên. *(Chính bẫy này đã xảy ra một lần: bản đầu của bảng runbook ghi "2.948 lúc 09:00:02" đúng vì lý do sai.)*

Đọc ra hai điều cho ngân sách RAM ở bảng trên: **trần 100.000 dòng rộng gấp ~32 lần đỉnh thật của một phiên bình thường**, và **chế độ đĩa chưa lần nào phải kích hoạt** — nghĩa là ngân sách ~50 MB cấp cho hàng đợi đang dư rất nhiều, nhưng nó được cấp cho **phiên bất thường** (kho trục trặc), không phải phiên bình thường, nên **chưa có căn cứ để hạ trần**.

⚠️ **RSS của tiến trình ghi trong phiên 28/08: chưa có số.** Log phiên không ghi RSS *(kiểm 2026-08-28: 0 hit `rss`/`memory` trong `ingester-20260828.log`)*. Dòng "97 MB" ở bảng trên vẫn là số đo **27/08**. Muốn có số cho phiên chạy code spill thì phải thêm phép lấy mẫu RSS vào chính job, hoặc đo tay trong phiên.


---

## 8. Quyết định mềm — ghi rõ để không chọn ngầm

Hai điểm dưới đây chốt theo mặc định hợp lý, **có thể đảo** khi có lý do, và phải sửa thẳng vào tài liệu này *(luật tầng 20-design)*:

| Điểm | Chốt mặc định | Đảo khi |
|---|---|---|
| **Chatbot ở đâu** | Trong `api` (function calling) — theo [kho dữ liệu §2](market-data-store.md) | Tải LLM/độ trễ chatbot làm ảnh hưởng độ sẵn sàng của `api` request thường ⇒ tách `chatbot` thành tiến trình thứ tư |
| **Pipeline tin (lưới AI)** | Một họ job trong `etl` — [news-pipeline.md](news-pipeline.md) | Lưới AI ngốn tài nguyên/lịch chạy riêng biệt tới mức cần tiến trình `news` riêng |

Hai điểm này **không chặn** lát cắt đầu tiên (chỉ có `ingester` + `etl`), nên để mở tới khi dựng `api`. *(Điểm "dữ liệu user" trước đây ở đây đã **chốt cứng — tách instance D**, xem §4.)*
