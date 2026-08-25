# Spec — Kho realtime ClickHouse

**Ngày:** 2026-08-25 · **Trạng thái:** 🟡 chờ chủ dự án duyệt · **Loại:** kiến trúc — thay phần kho realtime TimescaleDB trong [market-data-store.md](../../../20-design/market-data-store.md) theo [ADR 0007](../../../00-overview/decisions/0007-monorepo-layout-and-stack.md)

**Phạm vi:** lược đồ ClickHouse cho dữ liệu realtime BVSC (5 topic), materialized view sinh nến, chính sách giữ dữ liệu, cách Ingester ghi, quyền truy cập, hạ tầng compose, cơ chế migration. **Không** thiết kế lại Ingester ở mức code (thuộc plan dựng ingester) và **không** đụng Postgres/Redis — ranh giới ba kho giữ nguyên [service-topology §4](../../../20-design/service-topology.md).

**Nguồn số đo dùng trong spec:** [11-bvsc-realtime.md](../../../10-sources/market/11-bvsc-realtime.md) — đo phiên chiều 10/08/2026, 3.266 frame, 12 mã. Ước lượng toàn thị trường là **suy rộng từ mẫu này, chưa đo toàn thị trường** — sẽ đo lại khi Ingester chạy thật.

---

## 1. Quyết định chốt trong phiên brainstorm 2026-08-25 (chủ dự án)

| # | Quyết định | Lý do |
|---|---|---|
| 1 | **Lưu cả 5 topic** (`t` · `o10` · `i` · `idx` · `ptm`), mỗi loại sự kiện một bảng chuẩn hoá đã ép kiểu | Đủ dựng lại mọi thứ, truy vấn được ngay; `idx` bắt buộc phải hứng vì nến chỉ số chỉ dựng được từ nó |
| 2 | **Frame thô giữ cửa sổ trượt 3 tháng** (TTL DELETE), không giữ ròng năm này qua năm khác | Vi cấu trúc chỉ phân tích theo cửa sổ; 3 tháng đủ hồi cứu một mùa BCTC và đủ thời gian phát hiện lỗi gom nến. Dung lượng ổn định ~6–12 GB |
| 3 | **Nến 1 phút giữ vĩnh viễn, đắp thêm mãi** — gồm `bar_1m` (cổ phiếu, kèm `v_bu`/`v_sd`) và `index_bar_1m` (chỉ số) | Nguyên tắc "chưng cất trước khi quên": thứ cần dài hạn phải gom về dạng nhỏ trước khi frame thô trôi khỏi cửa sổ. `v_bu`/`v_sd` giữ vĩnh viễn chuỗi dòng tiền chủ động với chi phí ~0 |
| 4 | **Hệ số điều chỉnh giá: `api` tự ghép** — đọc factor từ Postgres, nến từ ClickHouse, nhân khi trả kết quả | ClickHouse giữ giá thô thuần tuý, không phụ thuộc runtime nào sang Postgres. Factor ít, cache được, đổi ~vài mã/ngày |
| 5 | **Migration ClickHouse: file SQL đánh số + runner Python nhỏ tự viết**, ghi bảng `rt.schema_migrations` | Alembic không hỗ trợ ClickHouse tử tế; cùng triết lý "SQL thô, kiểm soát từng dòng" đã chọn cho Postgres |
| 6 | Buffer ghi batch **trong tiến trình Ingester**, flush mỗi 1 giây hoặc đủ N dòng | Giữ nguyên "batch writer ngoài hot path" của thiết kế cũ. Chấp nhận có ý thức: ingester chết mất tối đa ~1 s frame chưa flush — cùng bậc với failover < 2 s đã chấp nhận |
| 7 | **Chưa có gì cho phái sinh** — bảng bám cổ phiếu/chỉ số | Chưa đo được realtime phái sinh trong phiên ([roadmap §5.1](../../../00-overview/roadmap.md)); cấm giả định |

**Đã cân nhắc và loại (loại có chủ đích):**

| Mục | Lý do loại |
|---|---|
| Bảng frame thô JSON làm landing zone (kiểu `staging.raw_payload`) | Tốn ~2× dung lượng và một đường ghi nữa; bảng sự kiện đã ép kiểu + cột `extra` hứng trường lạ là đủ phòng schema đổi |
| Bảng chưng cất khối ngoại intraday (`FB`/`FS` cuối mỗi phút) | Chủ dự án chốt chỉ nến 1' là vĩnh viễn. Khối ngoại EOD đã có từ REST; intraday hồi cứu được trong cửa sổ 3 tháng. Nếu sau này cần chuỗi dài hạn: thêm một MV là xong, nhưng dữ liệu trước thời điểm thêm không dựng lại được |
| Chưng cất độ rộng thị trường (breadth) dài hạn | Cùng lý do trên — trong cửa sổ 3 tháng đọc từ `index_delta`; ngoài cửa sổ chấp nhận không có |
| Nến 5m/15m/60m vật chất hoá (chuỗi aggregate phân cấp kiểu Timescale cũ) | ClickHouse quét `bar_1m` cỡ này trong ms — tính lúc đọc. Thêm MV sau nếu đo thấy chậm |
| `async_insert` server-side · Buffer table engine | Kém kiểm soát hơn buffer trong tiến trình, thêm điểm mù khi mất dữ liệu |
| ClickHouse dictionary trỏ sang Postgres lấy factor · ETL đẩy factor sang ClickHouse | Tạo phụ thuộc runtime chéo kho / vi phạm "một người ghi mỗi miền" — quyết định #4 đã thay |
| Topic `pth` | Không có dữ liệu qua ~6 phút đo — ngoài phạm vi từ tài liệu nguồn |

## 2. Bố cục: database `rt` — 5 bảng frame + 2 bảng nến + 2 MV (+ sổ migration)

```
ClickHouse (instance duy nhất, người ghi duy nhất: ingester)
└── rt                          realtime thị trường VN
    ├── trade                   topic t   — TTL 3 tháng
    ├── quote                   topic o10 — TTL 3 tháng
    ├── snapshot_delta          topic i   — TTL 3 tháng
    ├── index_delta             topic idx — TTL 3 tháng
    ├── pt_match                topic ptm — TTL 3 tháng
    ├── bar_1m                  nến 1' cổ phiếu + BU/SD   — VĨNH VIỄN (MV từ trade)
    ├── index_bar_1m            nến 1' chỉ số             — VĨNH VIỄN (MV từ index_delta)
    └── schema_migrations       sổ migration của runner
```

Quy ước chung mọi bảng:

| Quy ước | Chốt |
|---|---|
| Engine | MergeTree family, `PARTITION BY toYYYYMM(<ngày>)` |
| Múi giờ | `DateTime`/`DateTime64` khai tường minh `'Asia/Ho_Chi_Minh'`. Trường thời gian dạng chuỗi của nguồn (`TD`+`FT`, `TD`+`TI`) parse theo giờ VN — bẫy [CLAUDE.md §3.1](../../../../CLAUDE.md) |
| Ép kiểu | Nguồn trả **số dạng chuỗi** ở `o`/`t`/`idx` — ingester ép tại cổng. Giá `Decimal64(2)` · khối lượng `UInt64` · giá trị luỹ kế `Decimal128(2)` (giá trị khớp toàn sàn ~3×10¹³ VND, chừa dư địa) |
| Mã | `symbol LowCardinality(String)` — luồng realtime dùng **ticker**, không phải organ_code (khác REST FiinTrade) |
| Trường phân loại của nguồn | `LowCardinality(String)`, **không dùng Enum** — danh sách giá trị của nguồn chưa chắc đóng (bài học `i` tăng 22→34 trường) |
| Trường lạ | Bảng delta (`snapshot_delta`, `index_delta`) có cột `extra String` chứa JSON các trường ngoài danh sách đã biết — "xử lý trường lạ an toàn" theo [11-bvsc-realtime §11.9](../../../10-sources/market/11-bvsc-realtime.md) |
| Truy vết | Mọi bảng frame có `received_at DateTime64(3)` — lúc ingester nhận, để đo độ trễ và truy sự cố |
| TTL | `TTL <ngày> + INTERVAL 3 MONTH DELETE` trên 5 bảng frame. `bar_1m`/`index_bar_1m` **không TTL** |

## 3. DDL từng bảng

> DDL dưới đây là bản thiết kế để duyệt; câu chữ cuối cùng nằm trong file migration ở bước plan. Tên cột đối chiếu tên trường nguồn ghi trong chú thích.

### 3.1 `rt.trade` — topic `t`, từng lệnh khớp

```sql
CREATE TABLE rt.trade (
  symbol        LowCardinality(String),                 -- SB
  trading_date  Date,                                   -- TD (dd/MM/yyyy, giờ VN)
  ts            DateTime('Asia/Ho_Chi_Minh'),           -- TD + FT (độ phân giải GIÂY — nguồn không có epoch ms)
  seq           UInt64,                                 -- SM: số thứ tự message từ sở — thứ tự trong cùng giây
  price         Decimal64(2),                           -- FMP
  volume        UInt64,                                 -- FV
  side          LowCardinality(String),                 -- LC: 'B' mua chủ động · 'S' bán chủ động
  change        Decimal64(2),                           -- FCV
  cum_volume    UInt64,                                 -- AVO
  cum_value     Decimal128(2),                          -- AVA
  received_at   DateTime64(3, 'Asia/Ho_Chi_Minh')
)
ENGINE = ReplacingMergeTree
PARTITION BY toYYYYMM(trading_date)
ORDER BY (symbol, ts, seq)
TTL trading_date + INTERVAL 3 MONTH DELETE;
```

`ReplacingMergeTree` trên khoá `(symbol, ts, seq)` là **lưới đỡ thứ hai** chống frame trùng; lưới chính là dedup tại ingester (§5) — vì MV gom nến đọc **lúc insert**, trùng lọt vào là nến đếm đôi dù bảng gốc có dedup về sau.

### 3.2 `rt.quote` — topic `o10`, sổ lệnh 3 bậc (mỗi dòng một bậc)

```sql
CREATE TABLE rt.quote (
  symbol      LowCardinality(String),                   -- SB
  ts          DateTime64(3, 'Asia/Ho_Chi_Minh'),        -- t (epoch ms)
  top         UInt8,                                    -- TOP: 1..3
  action      LowCardinality(String),                   -- ACT (quan sát thấy 'U')
  bid_price   Decimal64(2),                             -- BP
  bid_qty     UInt64,                                   -- BQ
  ask_price   Decimal64(2),                             -- SP
  ask_qty     UInt64,                                   -- SQ
  cum_bid     UInt64,                                   -- CBV
  cum_ask     UInt64,                                   -- CSV
  received_at DateTime64(3, 'Asia/Ho_Chi_Minh')
)
ENGINE = ReplacingMergeTree
PARTITION BY toYYYYMM(toDate(ts))
ORDER BY (symbol, ts, top)
TTL toDate(ts) + INTERVAL 3 MONTH DELETE;
```

### 3.3 `rt.snapshot_delta` — topic `i`, delta 34 trường

Ba trường định danh luôn có (`SB`/`EX`/`t`); 31 trường còn lại chỉ xuất hiện khi đổi ⇒ cột `Nullable`, NULL nghĩa là "frame này không nhắc tới" (nén cột xử lý tốt cột thưa). Trường ngoài danh sách 34 đã biết → gom vào `extra` (JSON), **không rơi rụng**.

```sql
CREATE TABLE rt.snapshot_delta (
  symbol      LowCardinality(String),                   -- SB
  exchange    LowCardinality(String),                   -- EX
  ts          DateTime64(3, 'Asia/Ho_Chi_Minh'),        -- t (epoch ms)
  -- sổ lệnh 3 bậc
  b1 Nullable(Decimal64(2)), b2 Nullable(Decimal64(2)), b3 Nullable(Decimal64(2)),
  v1 Nullable(UInt64),       v2 Nullable(UInt64),       v3 Nullable(UInt64),
  s1 Nullable(Decimal64(2)), s2 Nullable(Decimal64(2)), s3 Nullable(Decimal64(2)),
  u1 Nullable(UInt64),       u2 Nullable(UInt64),       u3 Nullable(UInt64),
  total_bid   Nullable(UInt64),                         -- TB
  total_offer Nullable(UInt64),                         -- TO
  -- khớp lệnh
  close_price Nullable(Decimal64(2)),                   -- CP
  change      Nullable(Decimal64(2)),                   -- CH
  change_pct  Nullable(Decimal64(2)),                   -- CHP
  avg_price   Nullable(Decimal64(2)),                   -- AP
  high        Nullable(Decimal64(2)),                   -- HI
  last_vol    Nullable(UInt64),                         -- CV
  last_vol2   Nullable(UInt64),                         -- P1
  last_price  Nullable(Decimal64(2)),                   -- P2
  total_vol   Nullable(UInt64),                         -- TT
  total_value Nullable(Decimal128(2)),                  -- TV
  -- khối ngoại
  foreign_buy    Nullable(UInt64),                      -- FB
  foreign_sell   Nullable(UInt64),                      -- FS
  foreign_remain Nullable(UInt64),                      -- FR
  -- thoả thuận
  pt_price     Nullable(Decimal64(2)),                  -- PMP
  pt_qty       Nullable(UInt64),                        -- PMQ
  pt_total_qty Nullable(UInt64),                        -- PTQ
  pt_total_val Nullable(Decimal128(2)),                 -- PTV
  extra       String DEFAULT '',                        -- JSON trường ngoài danh sách
  received_at DateTime64(3, 'Asia/Ho_Chi_Minh')
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(toDate(ts))
ORDER BY (symbol, ts)
TTL toDate(ts) + INTERVAL 3 MONTH DELETE;
```

### 3.4 `rt.index_delta` — topic `idx`, delta 18 trường

```sql
CREATE TABLE rt.index_delta (
  symbol      LowCardinality(String),                   -- MC (HOSE, 30, HNX, ...)
  ts          DateTime64(3, 'Asia/Ho_Chi_Minh'),        -- t (epoch ms)
  index_value Nullable(Decimal64(2)),                   -- MI
  change      Nullable(Decimal64(2)),                   -- ICH
  change_pct  Nullable(Decimal64(2)),                   -- IPC
  total_vol   Nullable(UInt64),                         -- TV
  total_value Nullable(Decimal128(2)),                  -- TVA
  advances    Nullable(UInt16),                         -- ADV
  declines    Nullable(UInt16),                         -- DE
  unchanged   Nullable(UInt16),                         -- NC
  ceiling_cnt Nullable(UInt16),                         -- NOC
  adv_vol     Nullable(UInt64),                         -- AV
  dec_vol     Nullable(UInt64),                         -- DV
  unch_vol    Nullable(UInt64),                         -- NCV
  pt_total    Nullable(UInt64),                         -- PTT (bản chất chưa xác định rõ — giữ nguyên số)
  pt_value    Nullable(Decimal128(2)),                  -- PTV
  extra       String DEFAULT '',
  received_at DateTime64(3, 'Asia/Ho_Chi_Minh')
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(toDate(ts))
ORDER BY (symbol, ts)
TTL toDate(ts) + INTERVAL 3 MONTH DELETE;
```

*(`IT`/`TD` dạng chuỗi không lưu — `ts` đã đủ; nếu quan sát thấy lệch `IT` vs `t` thì đó là việc của bộ giám sát hợp đồng, không phải của lược đồ.)*

### 3.5 `rt.pt_match` — topic `ptm`, thoả thuận đã khớp

```sql
CREATE TABLE rt.pt_match (
  symbol      LowCardinality(String),                   -- SB
  market      LowCardinality(String),                   -- MC
  ts          DateTime('Asia/Ho_Chi_Minh'),             -- LS (⚠️ epoch GIÂY, khác các topic khác)
  price       Decimal64(2),                             -- PR
  volume      UInt64,                                   -- MVL
  ref_price   Nullable(Decimal64(2)),                   -- RE
  ceil_price  Nullable(Decimal64(2)),                   -- CE
  floor_price Nullable(Decimal64(2)),                   -- FL
  order_id    String,                                   -- CNO (chứa ISIN + số hiệu)
  extra       String DEFAULT '',
  received_at DateTime64(3, 'Asia/Ho_Chi_Minh')
)
ENGINE = ReplacingMergeTree
PARTITION BY toYYYYMM(toDate(ts))
ORDER BY (symbol, ts, order_id)
TTL toDate(ts) + INTERVAL 3 MONTH DELETE;
```

## 4. Nến — hai bảng vĩnh viễn + hai materialized view

### 4.1 `rt.bar_1m` — nến cổ phiếu, gồm dòng tiền chủ động

Giá **THÔ**, không bao giờ sửa (nguyên tắc "lưu thô, điều chỉnh lúc đọc" giữ nguyên). Trạng thái aggregate để MV gom đúng kể cả khi frame một phút đến rải nhiều block insert:

```sql
CREATE TABLE rt.bar_1m (
  symbol LowCardinality(String),
  ts     DateTime('Asia/Ho_Chi_Minh'),                  -- đầu phút
  o    AggregateFunction(argMin, Decimal64(2), Tuple(DateTime, UInt64)),
  h    AggregateFunction(max, Decimal64(2)),
  l    AggregateFunction(min, Decimal64(2)),
  c    AggregateFunction(argMax, Decimal64(2), Tuple(DateTime, UInt64)),
  v    AggregateFunction(sum, UInt64),
  v_bu AggregateFunction(sum, UInt64),                  -- khối lượng mua chủ động (LC='B')
  v_sd AggregateFunction(sum, UInt64)                   -- khối lượng bán chủ động (LC='S')
)
ENGINE = AggregatingMergeTree
PARTITION BY toYYYYMM(ts)
ORDER BY (symbol, ts);
-- KHÔNG TTL — giữ vĩnh viễn, đắp thêm mãi

CREATE MATERIALIZED VIEW rt.mv_trade_to_bar_1m TO rt.bar_1m AS
SELECT
  symbol,
  toStartOfMinute(ts)                            AS ts,
  argMinState(price, (rt.trade.ts, seq))         AS o,
  maxState(price)                                AS h,
  minState(price)                                AS l,
  argMaxState(price, (rt.trade.ts, seq))         AS c,
  sumState(volume)                               AS v,
  sumState(if(side = 'B', volume, toUInt64(0)))  AS v_bu,
  sumState(if(side = 'S', volume, toUInt64(0)))  AS v_sd
FROM rt.trade
GROUP BY symbol, ts;
```

View đọc đã finalize (mặt tiếp xúc cho `api`):

```sql
CREATE VIEW rt.bar_1m_v AS
SELECT symbol, ts,
       argMinMerge(o) AS o, maxMerge(h) AS h, minMerge(l) AS l, argMaxMerge(c) AS c,
       sumMerge(v) AS v, sumMerge(v_bu) AS v_bu, sumMerge(v_sd) AS v_sd
FROM rt.bar_1m
GROUP BY symbol, ts;
```

Ba luật nghiệp vụ của nến:

1. **Thoả thuận không vào nến** — nến chỉ tính khớp lệnh (luồng `t`); `ptm` đứng ngoài. Đúng quy ước nến của mọi bảng giá.
2. **Nến lớn (5m/15m/60m/ngày) tính lúc đọc** từ `bar_1m_v` bằng `toStartOfInterval` — không vật chất hoá cho tới khi đo thấy chậm.
3. **Điều chỉnh lúc đọc, ở `api`**: giá trả cho người dùng = giá thô × factor, factor đọc từ view hệ số bên Postgres (`market`), cache trong `api`. ClickHouse không biết Postgres tồn tại.

### 4.2 `rt.index_bar_1m` — nến chỉ số

Chỉ số không có "lệnh khớp" — nến gom từ chuỗi `index_value` của `index_delta` (chỉ frame có `MI`). Khối lượng của nguồn là **luỹ kế trong ngày** ⇒ lưu luỹ kế cuối phút (max), khối lượng theo phút suy ra bằng hiệu khi đọc.

```sql
CREATE TABLE rt.index_bar_1m (
  symbol LowCardinality(String),
  ts     DateTime('Asia/Ho_Chi_Minh'),
  o AggregateFunction(argMin, Decimal64(2), DateTime64(3, 'Asia/Ho_Chi_Minh')),
  h AggregateFunction(max, Decimal64(2)),
  l AggregateFunction(min, Decimal64(2)),
  c AggregateFunction(argMax, Decimal64(2), DateTime64(3, 'Asia/Ho_Chi_Minh')),
  cum_vol   AggregateFunction(max, UInt64),
  cum_value AggregateFunction(max, Decimal128(2))
)
ENGINE = AggregatingMergeTree
PARTITION BY toYYYYMM(ts)
ORDER BY (symbol, ts);
-- KHÔNG TTL

CREATE MATERIALIZED VIEW rt.mv_index_to_bar_1m TO rt.index_bar_1m AS
SELECT
  symbol, toStartOfMinute(toDateTime(ts)) AS ts,
  argMinState(assumeNotNull(index_value), rt.index_delta.ts) AS o,
  maxState(assumeNotNull(index_value))    AS h,
  minState(assumeNotNull(index_value))    AS l,
  argMaxState(assumeNotNull(index_value), rt.index_delta.ts) AS c,
  maxState(assumeNotNull(total_vol))      AS cum_vol,
  maxState(assumeNotNull(total_value))    AS cum_value
FROM rt.index_delta
WHERE index_value IS NOT NULL
GROUP BY symbol, ts;
```

*(`total_vol`/`total_value` NULL trong frame chỉ đổi `MI`: `maxState` bỏ qua NULL sau `WHERE`? — không: `WHERE` chỉ lọc theo `index_value`. Chi tiết xử lý NULL của hai cột luỹ kế chốt ở plan cùng test — đây là một seam phải có case biên.)*

Kèm view đọc `rt.index_bar_1m_v` tương tự `bar_1m_v`.

## 5. Ingester ghi thế nào — hợp đồng writer

Chi tiết code thuộc plan dựng ingester; spec chốt **hợp đồng**:

1. **Hot path không đụng ClickHouse** (giữ nguyên [market-data-store §3.2](../../../20-design/market-data-store.md)): frame → ghép delta → Redis HASH + PUBLISH. Ghi ClickHouse qua hàng đợi trong tiến trình.
2. **Batch flush:** mỗi bảng một buffer, flush khi **1 giây trôi qua hoặc đủ N dòng** (N chốt ở plan, cỡ vài nghìn) bằng INSERT native qua `clickhouse-connect`. ClickHouse ghét insert lắt nhắt — đây là lý do buffer tồn tại.
3. **Ép kiểu tại cổng:** chuỗi → số trước khi vào buffer; parse `TD`+`FT`/`TD`+`TI` theo `Asia/Ho_Chi_Minh`; `LS` là epoch **giây**.
4. **Dedup tại ingester là lưới chính:** nhớ `seq` (SM) cuối theo mã cho `trade`, khoá `(symbol, ts, top)` gần nhất cho `quote`, `(symbol, ts, order_id)` cho `pt_match` — bỏ frame đã thấy (tình huống thật: nhận trùng khi nối lại + đăng ký lại). Lý do phải dedup **trước** insert: MV gom lúc insert, trùng lọt vào là `v`/`v_bu`/`v_sd` đếm đôi vĩnh viễn trong nến, dù bảng gốc ReplacingMergeTree có dọn về sau.
5. **Mất mát chấp nhận có ý thức:** ingester chết → mất tối đa ~1 s buffer chưa flush + thời gian standby tiếp quản (< 2 s). Không có cơ chế replay từ nguồn — đã biết từ khảo sát.
6. **Trường lạ không rơi rụng:** trường ngoài danh sách đã biết của `i`/`idx` → JSON vào `extra`; bộ giám sát hợp đồng theo dõi tỷ lệ `extra != ''` để biết nguồn vừa thêm trường.

## 6. Quyền truy cập — thi hành "một người ghi" bằng chính DB

Soi gương kỷ luật role Postgres ([database/README.md](../../../../database/README.md)):

| User ClickHouse | Quyền | Dùng bởi |
|---|---|---|
| `dlck_ingester` | INSERT + SELECT trên `rt.*` | tiến trình `ingester` |
| `dlck_api` | **chỉ SELECT** trên `rt.*` | tiến trình `api` |
| user quản trị (mặc định của image, đổi mật khẩu qua env) | DDL — chỉ runner migration dùng | migration |

`etl` **không có user ClickHouse** — nó không có việc gì ở kho realtime ([service-topology §4](../../../20-design/service-topology.md)).

## 7. Hạ tầng — compose profile `realtime`

Đúng chỗ [spec deploy-scaffold §3](../2026-08-24-deploy-scaffold/spec.md) để dành:

- Service `clickhouse` trong `deploy/infra/docker-compose.yml`, **profile `realtime`** — mặc định không chạy, `dev-start`/`docker-up` hiện tại không đổi hành vi.
- Image pin phiên bản LTS cụ thể (chốt số ở plan, kiểm bản LTS mới nhất lúc thực thi — không dùng tag `latest`).
- Cổng bind `127.0.0.1`: `8123` (HTTP — `clickhouse-connect` dùng) và `9000` (native TCP).
- Named volume `chdata` + healthcheck + các chốt an toàn volume như Postgres/Redis (kiểm sống sau `docker-down`, cấm bind-mount data dir).
- `.env` thêm khối ClickHouse (`CLICKHOUSE_USER`/`CLICKHOUSE_PASSWORD` bắt buộc, fail-fast; mật khẩu hai user ứng dụng cấp qua env riêng). Không in giá trị ra log.
- Cấu hình mem thấp cho máy đơn (giới hạn `max_server_memory_usage_to_ram_ratio`) — con số chốt ở plan.

## 8. Migration — `database/clickhouse/` + runner

```
database/clickhouse/
├── versions/0001_rt_schema.sql        (đánh số 4 chữ số, mỗi file một mục đích)
└── ...
backend/…                              runner: python -m <module> upgrade
```

- Runner Python nhỏ trong backend (dùng env `CLICKHOUSE_URL`): đọc `versions/*.sql` theo thứ tự, mỗi file chưa chạy thì thực thi rồi ghi dòng vào `rt.schema_migrations (version, applied_at)`. Idempotent — chạy lại không làm gì.
- **Không có downgrade** (khác Alembic): ClickHouse không transaction cho DDL; sửa sai = viết migration tiếp theo. Cùng luật "không sửa file migration đã chạy" của Postgres.
- Một file SQL có thể chứa nhiều statement, tách bằng `;` — quy ước parse chốt ở plan.
- Vị trí chính xác của module runner (trong `backend/core/` hay script riêng) chốt ở plan cùng cấu trúc test.

## 9. Test — seam dự kiến (danh sách chốt lại ở plan, theo §4.5)

Chạy trên **ClickHouse thật** (container test, giống cách test schema Postgres dùng DB thật — [test-strategy.md](../../../20-design/test-strategy.md)); TDD đỏ trước xanh; expected từ nguồn độc lập (bộ tick literal giải tay).

| Seam | Kiểm gì | Case biên tối thiểu |
|---|---|---|
| Runner migration | DB rỗng → `upgrade` → đủ bảng/MV/view; chạy lại lần 2 không đổi gì (idempotent) | file mới thêm được chạy tiếp đúng thứ tự |
| MV nến cổ phiếu | Insert bộ tick literal giải tay → `bar_1m_v` trả đúng o/h/l/c/v/v_bu/v_sd đã tính tay | hai tick cùng giây khác `seq` (o/c theo thứ tự sở, không theo thứ tự insert) · tick rải hai block insert cùng một phút (state gộp đúng) · phút không tick không có dòng · `side` lạ không vào `v_bu`/`v_sd` nhưng vẫn vào `v` |
| MV nến chỉ số | Chuỗi `index_delta` literal → `index_bar_1m_v` đúng o/h/l/c giải tay | frame chỉ đổi `MI` không có volume (NULL) không phá `cum_vol` |
| TTL | `SHOW CREATE TABLE` chứa đúng mệnh đề TTL 3 tháng ở 5 bảng frame, vắng ở 2 bảng nến | *(không chờ TTL chạy thật — kiểm DDL introspection)* |
| Quyền | `dlck_api` INSERT bị từ chối, SELECT được; `dlck_ingester` INSERT được | — |
| Ép kiểu + timezone (thuộc plan ingester, ghi trước) | `"42100.0"` → Decimal đúng; `TD`+`FT` giờ VN không lệch ngày | epoch `LS` giây vs `t` ms |

## 10. Ước lượng tải và dung lượng

Suy từ mẫu 12 mã / 239 s (đo 10/08/2026 — [11-bvsc-realtime §10](../../../10-sources/market/11-bvsc-realtime.md)), **chưa đo toàn thị trường**:

| Đại lượng | Ước lượng |
|---|---|
| Frame toàn thị trường giờ cao điểm | vài trăm frame/s (12 mã ≈ 13,7 frame/s) |
| Dòng ghi mỗi ngày (5 bảng frame) | ~3–6 triệu |
| Dung lượng frame thô | ~100–200 MB/ngày sau nén ⇒ **cửa sổ 3 tháng ổn định ~6–12 GB** |
| `bar_1m` + `index_bar_1m` | ~200–540k dòng/ngày ⇒ **~1 GB/năm**, tích luỹ vĩnh viễn |
| Nhịp insert từ ingester | ~5 INSERT/giây (5 bảng × flush 1 s) — rất nhẹ với ClickHouse |

Đo lại bằng số thật trong tuần đầu Ingester chạy; nếu lệch bậc thì cập nhật tài liệu sống kèm ngày đo.

## 11. Ngoài phạm vi spec này

| Mục | Loại | Ghi chú |
|---|---|---|
| Tick phái sinh | **chưa đo được** | Cấm giả định cho tới khi đo trong phiên ([roadmap §5.1](../../../00-overview/roadmap.md)); khi đo xong sẽ bổ sung bảng/cột bằng migration mới |
| Topic `pth` | đã kiểm — không có dữ liệu | [11-bvsc-realtime §9](../../../10-sources/market/11-bvsc-realtime.md) |
| Code Ingester (socket, ghép delta, standby) | đã có đường khác | Plan dựng ingester riêng, dùng hợp đồng §5 |
| SSE / `api` đọc ClickHouse | đã có đường khác | Thiết kế SSE giữ nguyên [market-data-store §3.4](../../../20-design/market-data-store.md); phần đọc dựng khi làm `api` |
| Chưng cất khối ngoại/breadth dài hạn | loại có chủ đích | Xem §1 — thêm được sau bằng MV, không lấy lại quá khứ |

## 12. Checklist quét tài liệu sống khi spec chốt (luật §1.7)

- [ ] `market-data-store.md` — banner: phần realtime (§3.2 điểm 4, §5.3, §5.7 dòng `bar_1m`) được thay bởi spec này; giữ nguyên văn làm lịch sử
- [ ] `database/README.md` — thêm mục ClickHouse: trạng thái, cách chạy migration + test
- [ ] `service-topology.md` — đối chiếu §4 (miền ClickHouse: thêm nhắc TTL 3 tháng frame thô / nến vĩnh viễn nếu cần một dòng)
- [ ] `roadmap.md` §5.2 — đánh dấu dòng "Cập nhật market-data-store theo ClickHouse" đã xong, trỏ hồ sơ này
- [ ] `deploy-scaffold` spec/ledger — **không sửa** (vùng lịch sử 90-records); profile `realtime` ghi ở compose thật khi thực thi
- [ ] `git grep` "TimescaleDB\|bar_1m\|hypertable" toàn repo — xác nhận mọi hit còn lại hoặc đã đúng, hoặc thuộc vùng lịch sử
