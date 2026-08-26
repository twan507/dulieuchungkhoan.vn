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

> ⚠️ **Chưa được giả định có tick phái sinh realtime** cho tới khi đo xong socket phái sinh BVSC trong phiên *(lộ trình §5.1)*. Lược đồ và ingester của lát cắt đầu bám cổ phiếu/chỉ số trước.

## 8. Quyết định mềm — ghi rõ để không chọn ngầm

Hai điểm dưới đây chốt theo mặc định hợp lý, **có thể đảo** khi có lý do, và phải sửa thẳng vào tài liệu này *(luật tầng 20-design)*:

| Điểm | Chốt mặc định | Đảo khi |
|---|---|---|
| **Chatbot ở đâu** | Trong `api` (function calling) — theo [kho dữ liệu §2](market-data-store.md) | Tải LLM/độ trễ chatbot làm ảnh hưởng độ sẵn sàng của `api` request thường ⇒ tách `chatbot` thành tiến trình thứ tư |
| **Pipeline tin (lưới AI)** | Một họ job trong `etl` — [news-pipeline.md](news-pipeline.md) | Lưới AI ngốn tài nguyên/lịch chạy riêng biệt tới mức cần tiến trình `news` riêng |

Hai điểm này **không chặn** lát cắt đầu tiên (chỉ có `ingester` + `etl`), nên để mở tới khi dựng `api`. *(Điểm "dữ liệu user" trước đây ở đây đã **chốt cứng — tách instance D**, xem §4.)*
