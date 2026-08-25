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
| 3 | **Nến 1 phút giữ vĩnh viễn, đắp thêm mãi** — gồm `bar_1m` (cổ phiếu, kèm `v_bu`/`v_sd` và `val` = giá trị giao dịch) và `index_bar_1m` (chỉ số) | Nguyên tắc "chưng cất trước khi quên": thứ cần dài hạn phải gom về dạng nhỏ trước khi frame thô trôi khỏi cửa sổ. `v_bu`/`v_sd` giữ chuỗi dòng tiền chủ động, `val` giữ VWAP/turnover theo phút — đều chi phí ~0. *(`val` bổ sung theo review 2026-08-25 lượt 1: thiếu nó thì VWAP mất vĩnh viễn sau TTL mà chưa từng được quyết tường minh)* |
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
| Topic `pth` | **Chưa kết luận được** — 0 frame qua ~6 phút đo (10/08/2026), nguồn ghi hai khả năng: kênh ngừng phát hoặc không có lệnh chào trong khoảng đo. Ngoài phạm vi cho tới khi có bằng chứng ngược |

## 2. Bố cục: database `rt` — 8 bảng · 2 materialized view · 2 view đọc

```
ClickHouse (instance duy nhất, người ghi duy nhất: ingester)
└── rt                          realtime thị trường VN
    ├── trade                   topic t   — TTL 3 tháng
    ├── quote                   topic o10 — TTL 3 tháng
    ├── snapshot_delta          topic i   — TTL 3 tháng
    ├── index_delta             topic idx — TTL 3 tháng
    ├── pt_match                topic ptm — TTL 3 tháng
    ├── bar_1m                  nến 1' cổ phiếu + BU/SD + giá trị — VĨNH VIỄN
    │     ← mv_trade_to_bar_1m (MV từ trade) · đọc qua view bar_1m_v
    ├── index_bar_1m            nến 1' chỉ số                     — VĨNH VIỄN
    │     ← mv_index_to_bar_1m (MV từ index_delta) · đọc qua view index_bar_1m_v
    └── schema_migrations       sổ migration của runner
```

Quy ước chung mọi bảng:

| Quy ước | Chốt |
|---|---|
| Engine | MergeTree family, `PARTITION BY toYYYYMM(<ngày>)` |
| Múi giờ | `DateTime`/`DateTime64` khai tường minh `'Asia/Ho_Chi_Minh'`. Trường thời gian dạng chuỗi của nguồn (`TD`+`FT`, `TD`+`TI`) parse theo giờ VN — bẫy [CLAUDE.md §3.1](../../../../CLAUDE.md) |
| Ép kiểu | Nguồn trả **số dạng chuỗi** ở `o`/`t`/`idx` — ingester ép tại cổng. Giá `Decimal64(2)` · khối lượng `UInt64` · giá trị tiền `Decimal64(2)` (precision 18, trần ~10¹⁶ VND — giá trị khớp toàn sàn cỡ 10¹³/ngày *(ước lượng, chưa đo)*, dư ~300×; không dùng `Decimal128` cho cột frame vì tốn gấp đôi byte trên hàng triệu dòng/ngày). Riêng cột tổng `val` của `bar_1m` dùng `Decimal128(2)` vì là tích `price × volume` cộng dồn |
| Mã | `symbol LowCardinality(String)` — luồng realtime dùng **ticker**, không phải organ_code (khác REST FiinTrade) |
| Trường phân loại của nguồn | `LowCardinality(String)`, **không dùng Enum** — danh sách giá trị của nguồn chưa chắc đóng (bài học `i` tăng 22→34 trường) |
| Trường lạ / không map | `snapshot_delta`, `index_delta`, `pt_match` có cột `extra String` chứa JSON **mọi trường không map vào cột** — gồm cả trường lạ chưa từng thấy ("xử lý trường lạ an toàn", [11-bvsc-realtime §11.9](../../../10-sources/market/11-bvsc-realtime.md)) lẫn trường đã biết nhưng cố ý không lên cột (`MKI`/`IAC` của `ptm`). `trade`/`quote` **không có `extra`**: bộ trường của `t`/`o` cố định 10/11 trường, nguồn chỉ cảnh báo danh sách chưa đóng cho `i` |
| Mẫu truy vấn tối ưu | `ORDER BY (symbol, ts, …)` chọn có ý thức cho mẫu chủ đạo "**một mã theo thời gian**". Cắt ngang toàn thị trường tại một thời điểm phải quét partition tháng — chấp nhận (cỡ vài GB/partition); nếu sau này đo thấy chậm mới thêm skip index minmax theo `ts` |
| Truy vết | Mọi bảng frame có `received_at DateTime64(3)` — lúc ingester nhận, để đo độ trễ và truy sự cố |
| TTL | `TTL toDate(ts) + INTERVAL 3 MONTH DELETE` trên 5 bảng frame, kèm `SETTINGS ttl_only_drop_parts = 1` — partition tháng hết hạn thì **drop nguyên part** thay vì merge viết lại từng dòng, gần như miễn phí. Hệ quả phải biết: thời gian giữ thật dao động **3–4 tháng** (cả partition đợi dòng trẻ nhất hết hạn), không phải đúng 3. `bar_1m`/`index_bar_1m` **không TTL** |

## 3. DDL từng bảng

> DDL dưới đây là bản thiết kế để duyệt; câu chữ cuối cùng nằm trong file migration ở bước plan. Tên cột đối chiếu tên trường nguồn ghi trong chú thích.

### 3.1 `rt.trade` — topic `t`, từng lệnh khớp

```sql
CREATE TABLE rt.trade (
  symbol        LowCardinality(String),                 -- SB
  ts            DateTime('Asia/Ho_Chi_Minh'),           -- TD + FT (độ phân giải GIÂY — nguồn không có epoch ms)
  seq           UInt64,                                 -- SM: số thứ tự message từ sở — thứ tự trong cùng giây
  price         Decimal64(2),                           -- FMP
  volume        UInt64,                                 -- FV
  side          LowCardinality(String),                 -- LC: 'B' mua chủ động · 'S' bán chủ động
  change        Decimal64(2),                           -- FCV
  cum_volume    UInt64,                                 -- AVO
  cum_value     Decimal64(2),                           -- AVA
  received_at   DateTime64(3, 'Asia/Ho_Chi_Minh')
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(toDate(ts))
ORDER BY (symbol, ts, seq)
TTL toDate(ts) + INTERVAL 3 MONTH DELETE
SETTINGS ttl_only_drop_parts = 1, non_replicated_deduplication_window = 100;
```

Ba điểm có chủ đích:

- **`TD` không thành cột riêng** — `toDate(ts)` là cùng thông tin; hai cột cho một sự thật sẽ trôi lệch nhau nếu ingester parse lỗi. Đối lại, seam ép kiểu của ingester phải assert `TD == toDate(ts đã dựng)` (bắt bug parse `FT` qua nửa đêm/ATC ngay tại cổng).
- **`MergeTree` thuần, không `ReplacingMergeTree`** — Replacing trên khoá `(symbol, ts, seq)` chỉ an toàn nếu `SM` duy nhất trong (mã, giây); tài liệu nguồn **chưa đo** tính chất đó của SM ([11-bvsc-realtime §6](../../../10-sources/market/11-bvsc-realtime.md) chỉ ghi "số thứ tự message từ sở"). Replacing đặt trên giả định sai sẽ **nuốt lệnh khớp thật**. Chống trùng nằm ở hai lưới của §5, không ở engine.
- **`non_replicated_deduplication_window`** — lưới chống ghi trùng **mức block** cho kịch bản retry (xem §5); chỉ cặp `trade` + `bar_1m` cần (phải đặt ở **cả hai** — đo §12/T4) vì chỉ MV nến cổ phiếu có `sum` — xem bất biến ở §5.

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
ENGINE = MergeTree
PARTITION BY toYYYYMM(toDate(ts))
ORDER BY (symbol, ts, top)
TTL toDate(ts) + INTERVAL 3 MONTH DELETE
SETTINGS ttl_only_drop_parts = 1;
```

*(Trường `id` của nguồn không lưu — nó chỉ là `{mã}:{bậc}`, trùng thông tin `(symbol, top)`. Engine `MergeTree` thuần có chủ đích: không MV nào đọc `quote` nên dòng trùng vô hại lúc đọc, còn `ReplacingMergeTree` với `ts` mili-giây có thể **gộp nhầm hai cập nhật thật cùng bậc trong cùng mili-giây** — burst ATC là lúc dễ đụng nhất.)*

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
  total_value Nullable(Decimal64(2)),                   -- TV
  -- khối ngoại
  foreign_buy    Nullable(UInt64),                      -- FB
  foreign_sell   Nullable(UInt64),                      -- FS
  foreign_remain Nullable(UInt64),                      -- FR
  -- thoả thuận
  pt_price     Nullable(Decimal64(2)),                  -- PMP
  pt_qty       Nullable(UInt64),                        -- PMQ
  pt_total_qty Nullable(UInt64),                        -- PTQ
  pt_total_val Nullable(Decimal64(2)),                  -- PTV
  extra       String DEFAULT '',                        -- JSON trường không map vào cột
  received_at DateTime64(3, 'Asia/Ho_Chi_Minh')
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(toDate(ts))
ORDER BY (symbol, ts)
TTL toDate(ts) + INTERVAL 3 MONTH DELETE
SETTINGS ttl_only_drop_parts = 1;
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
  pt_value    Nullable(Decimal64(2)),                   -- PTV
  extra       String DEFAULT '',
  received_at DateTime64(3, 'Asia/Ho_Chi_Minh')
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(toDate(ts))
ORDER BY (symbol, ts)
TTL toDate(ts) + INTERVAL 3 MONTH DELETE
SETTINGS ttl_only_drop_parts = 1;
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
  extra       String DEFAULT '',                        -- JSON trường không map vào cột: MKI, IAC, và trường lạ
  received_at DateTime64(3, 'Asia/Ho_Chi_Minh')
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(toDate(ts))
ORDER BY (symbol, ts, order_id)
TTL toDate(ts) + INTERVAL 3 MONTH DELETE
SETTINGS ttl_only_drop_parts = 1;
```

*(`MKI` (mã sàn dạng số — trùng thông tin `market`) và `IAC` (cờ trạng thái, bản chất chưa xác định) không lên cột mà đi vào `extra` — không rơi rụng, và khi nào hiểu `IAC` thì nâng thành cột bằng migration mới. `TD`/`TI` không lưu — `ts` từ `LS` đã đủ. Engine `MergeTree` thuần cùng lý do với `quote`.)*

## 4. Nến — hai bảng vĩnh viễn + hai materialized view

### 4.1 `rt.bar_1m` — nến cổ phiếu, gồm dòng tiền chủ động

Giá **THÔ**, không bao giờ sửa (nguyên tắc "lưu thô, điều chỉnh lúc đọc" giữ nguyên). Trạng thái aggregate để MV gom đúng kể cả khi frame một phút đến rải nhiều block insert:

```sql
CREATE TABLE rt.bar_1m (
  symbol LowCardinality(String),
  ts     DateTime('Asia/Ho_Chi_Minh'),                  -- đầu phút
  o    AggregateFunction(argMin, Decimal64(2), Tuple(DateTime('Asia/Ho_Chi_Minh'), UInt64)),
  h    AggregateFunction(max, Decimal64(2)),
  l    AggregateFunction(min, Decimal64(2)),
  c    AggregateFunction(argMax, Decimal64(2), Tuple(DateTime('Asia/Ho_Chi_Minh'), UInt64)),
  v    AggregateFunction(sum, UInt64),
  val  AggregateFunction(sum, Decimal128(2)),           -- giá trị giao dịch = Σ price×volume → VWAP = val/v
  v_bu AggregateFunction(sum, UInt64),                  -- khối lượng mua chủ động (LC='B')
  v_sd AggregateFunction(sum, UInt64)                   -- khối lượng bán chủ động (LC='S')
)
ENGINE = AggregatingMergeTree
PARTITION BY toYYYYMM(ts)
ORDER BY (symbol, ts)
SETTINGS non_replicated_deduplication_window = 100;
-- KHÔNG TTL — giữ vĩnh viễn, đắp thêm mãi

CREATE MATERIALIZED VIEW rt.mv_trade_to_bar_1m TO rt.bar_1m AS
SELECT
  symbol,
  toStartOfMinute(event_ts)                      AS ts,
  argMinState(price, (event_ts, seq))            AS o,
  maxState(price)                                AS h,
  minState(price)                                AS l,
  argMaxState(price, (event_ts, seq))            AS c,
  sumState(volume)                               AS v,
  sumState(toDecimal128(price, 2) * volume)      AS val,
  sumState(if(side = 'B', volume, toUInt64(0)))  AS v_bu,
  sumState(if(side = 'S', volume, toUInt64(0)))  AS v_sd
FROM (SELECT symbol, ts AS event_ts, seq, price, volume, side FROM rt.trade)
GROUP BY symbol, ts;
```

Hai chi tiết cú pháp **bắt buộc**, đã kiểm trên ClickHouse thật *(xem §12)*:

- Kiểu khoá trong `AggregateFunction(argMin, …)` phải khai **đủ múi giờ** `Tuple(DateTime('Asia/Ho_Chi_Minh'), UInt64)` — khớp đúng kiểu cột `ts` của `trade`; đây cũng là quy ước §2 "khai múi giờ tường minh".
- MV đọc qua **subquery đổi tên** `ts AS event_ts` để loại hẳn tình trạng alias `toStartOfMinute(ts) AS ts` **che khuất cột gốc** — hành vi phân giải alias trùng tên phụ thuộc analyzer từng phiên bản, không được dựa vào.

Cột `val` tồn tại vì nguyên tắc "chưng cất trước khi quên": không có nó thì **VWAP và giá trị giao dịch theo phút không suy được** từ o/h/l/c/v, và sau 3 tháng `trade` bị TTL xoá là mất vĩnh viễn. `Decimal128(2)` cho riêng cột này vì là tích cộng dồn.

View đọc đã finalize (mặt tiếp xúc cho `api`):

```sql
CREATE VIEW rt.bar_1m_v AS
SELECT symbol, ts,
       argMinMerge(o) AS o, maxMerge(h) AS h, minMerge(l) AS l, argMaxMerge(c) AS c,
       sumMerge(v) AS v, sumMerge(val) AS val,
       sumMerge(v_bu) AS v_bu, sumMerge(v_sd) AS v_sd
FROM rt.bar_1m
GROUP BY symbol, ts;
```

Ba luật nghiệp vụ của nến:

1. **Thoả thuận không vào nến** — nến chỉ tính khớp lệnh (luồng `t`); `ptm` đứng ngoài. Đúng quy ước nến của mọi bảng giá.
2. **Nến lớn (5m/15m/60m/ngày) tính lúc đọc** từ `bar_1m_v` bằng `toStartOfInterval` — dự kiến đủ nhanh ở quy mô ~540k dòng nến/ngày; **đo lại khi có một tháng dữ liệu thật**, chậm mới thêm MV (đúng mục "đã cân nhắc và loại" §1).
3. **Điều chỉnh lúc đọc, ở `api`**: giá trả cho người dùng = giá thô × factor, factor đọc từ view hệ số bên Postgres (`market`), cache trong `api`. ClickHouse không biết Postgres tồn tại. **Chuỗi khoá ghép phải đi ba chặng**: `symbol` của ClickHouse là **ticker** → tra `market.security` ra `security_id` → lấy factor — không phải quan hệ trực tiếp (bẫy `organCode ≠ ticker` 41% nằm đúng đây). **Ngày chưa có factor** (nến trong phiên — `getPriceData` crawl sau 15:00): dùng **factor = 1**, vì sự kiện quyền có hiệu lực từ đầu ngày giao dịch không hưởng quyền — giá thô hôm nay đã ở thang sau điều chỉnh, các hệ số lịch sử mới là thứ co giá quá khứ về thang hiện tại.

### 4.2 `rt.index_bar_1m` — nến chỉ số

Chỉ số không có "lệnh khớp" — nến gom từ chuỗi `index_value` của `index_delta` (chỉ frame có `MI`). Khối lượng của nguồn là **luỹ kế trong ngày** ⇒ lưu luỹ kế cuối phút (max), khối lượng theo phút suy ra bằng hiệu khi đọc.

> ⚠️ **Chất lượng khác `bar_1m`:** nguồn đẩy `idx` ~0,09 frame/giây mỗi chỉ số *(đo 10/08/2026)* ≈ **5 mẫu/phút**. `h`/`l` của nến chỉ số là cao/thấp **của các mẫu**, không phải cao/thấp thật trong phút — khác `bar_1m` gom từ **từng lệnh khớp** nên o/h/l/c chính xác. Ghi ở đây vì bảng là vĩnh viễn, người đọc sau không được tưởng hai bảng cùng chất lượng.

```sql
CREATE TABLE rt.index_bar_1m (
  symbol LowCardinality(String),
  ts     DateTime('Asia/Ho_Chi_Minh'),
  o AggregateFunction(argMin, Decimal64(2), DateTime64(3, 'Asia/Ho_Chi_Minh')),
  h AggregateFunction(max, Decimal64(2)),
  l AggregateFunction(min, Decimal64(2)),
  c AggregateFunction(argMax, Decimal64(2), DateTime64(3, 'Asia/Ho_Chi_Minh')),
  cum_vol   AggregateFunction(max, Nullable(UInt64)),
  cum_value AggregateFunction(max, Nullable(Decimal64(2)))
)
ENGINE = AggregatingMergeTree
PARTITION BY toYYYYMM(ts)
ORDER BY (symbol, ts);
-- KHÔNG TTL

CREATE MATERIALIZED VIEW rt.mv_index_to_bar_1m TO rt.index_bar_1m AS
SELECT
  symbol,
  toStartOfMinute(toDateTime(event_ts))                     AS ts,
  argMinState(assumeNotNull(index_value), event_ts)         AS o,
  maxState(assumeNotNull(index_value))                      AS h,
  minState(assumeNotNull(index_value))                      AS l,
  argMaxState(assumeNotNull(index_value), event_ts)         AS c,
  maxState(total_vol)                                       AS cum_vol,
  maxState(total_value)                                     AS cum_value
FROM (SELECT symbol, ts AS event_ts, index_value, total_vol, total_value
      FROM rt.index_delta WHERE index_value IS NOT NULL)
GROUP BY symbol, ts;
```

**Ngữ nghĩa NULL của hai cột luỹ kế — quyết định spec, không phải chi tiết plan** (vì bảng vĩnh viễn, sai là không dựng lại được): `idx` là delta nên **cả phút có thể không frame nào mang `TV`/`TVA`**. Nếu ép `assumeNotNull` như hai cột giá, phút đó thành `cum_vol = 0` → người đọc suy khối lượng-theo-phút bằng hiệu sẽ được **một cặp hiệu âm/dương khổng lồ**. Chốt: state khai `Nullable`, `maxState` **bỏ qua NULL và trả NULL khi cả phút NULL** *(đã kiểm hành vi trên ClickHouse thật — §12)* — NULL nghĩa trung thực là "phút này nguồn không cập nhật luỹ kế", người đọc carry-forward bằng window function. `assumeNotNull` chỉ dùng cho `index_value` vì subquery đã `WHERE index_value IS NOT NULL`.

Kèm view đọc `rt.index_bar_1m_v` tương tự `bar_1m_v` (`maxMerge(cum_vol)`, `maxMerge(cum_value)`).

## 5. Ingester ghi thế nào — hợp đồng writer

Chi tiết code thuộc plan dựng ingester; spec chốt **hợp đồng**:

1. **Hot path không đụng ClickHouse** (giữ nguyên [market-data-store §3.2](../../../20-design/market-data-store.md)): frame → ghép delta → Redis HASH + PUBLISH. Ghi ClickHouse qua hàng đợi trong tiến trình.
2. **Batch flush:** mỗi bảng một buffer, flush khi **1 giây trôi qua hoặc đủ N dòng** (N chốt ở plan, cỡ vài nghìn) bằng INSERT native qua `clickhouse-connect`. ClickHouse ghét insert lắt nhắt — đây là lý do buffer tồn tại.
3. **Ép kiểu tại cổng:** chuỗi → số trước khi vào buffer; parse `TD`+`FT`/`TD`+`TI` theo `Asia/Ho_Chi_Minh`; `LS` là epoch **giây**.
4. **Chống trùng hai lưới, đặt đúng hai tầng khác nhau** — vì MV gom **lúc insert**: bản sao lọt vào `trade` là `v`/`val`/`v_bu`/`v_sd` đếm đôi **vĩnh viễn** trong nến, không cơ chế nào sau đó chữa được:
   - **Lưới frame (tại ingester):** bỏ frame đã thấy khi nguồn đẩy lại sau nối lại + đăng ký lại. Cấu trúc cụ thể (tập khoá trong cửa sổ trượt — **không phải** chỉ nhớ một khoá cuối, vì reconnect đẩy lại cả loạt) chốt ở plan ingester. ⚠️ **Giả định chưa đo:** dedup theo `SM` giả định SM đơn điệu/duy nhất theo mã — tài liệu nguồn chưa đo tính chất này; plan ingester phải kèm một phiên đo SM trước khi chốt luật, trước đó dùng tập-khoá-đã-thấy, không dùng so sánh thứ tự.
   - **Lưới block (tại ClickHouse):** bắt kịch bản lưới frame **không thể** bắt: flush thành công nhưng ack rớt (timeout, CH restart) → writer retry **nguyên block** → block trùng bị server nuốt im lặng. Đo trên CH thật *(§12, T4)* cho thấy cần **đủ bộ ba**, thiếu một là nến vẫn đếm đôi dù bảng gốc dedup thành công: (1) `non_replicated_deduplication_window` trên `rt.trade`; (2) **cả trên `rt.bar_1m`** — dedup của bảng gốc KHÔNG tự lan xuống bảng đích MV; (3) writer INSERT với setting `deduplicate_blocks_in_dependent_materialized_views = 1`. Hệ quả cho writer: **retry một INSERT phải gửi lại đúng block cũ nguyên vẹn** (không gộp thêm dòng mới vào block retry — đổi nội dung là đổi hash, mất tác dụng dedup).
   - **Bất biến phải giữ:** `snapshot_delta`/`index_delta` không cần hai lưới này vì mọi aggregate của MV chỉ số là `max`/`argMin`/`argMax` — **idempotent với bản sao**. Ràng buộc đi kèm: **cấm thêm aggregate cộng dồn (`sum`/`count`) lên `index_delta`/`snapshot_delta`** mà không bổ sung dedup tương đương `trade`.
5. **Mất mát chấp nhận có ý thức:** ingester chết → mất tối đa ~1 s buffer chưa flush + thời gian standby tiếp quản (< 2 s). Không có cơ chế replay từ nguồn — đã biết từ khảo sát. Retry INSERT lỗi được phép (an toàn nhờ lưới block), nhưng **giới hạn số lần rồi bỏ** — không giữ block cũ mãi làm phình bộ nhớ.
6. **Trường lạ không rơi rụng:** trường ngoài danh sách đã biết của `i`/`idx` → JSON vào `extra`; bộ giám sát hợp đồng theo dõi tỷ lệ `extra != ''` để biết nguồn vừa thêm trường.

## 6. Quyền truy cập — thi hành "một người ghi" bằng chính DB

Soi gương **đúng mô hình** role Postgres ([database/README.md](../../../../database/README.md)): migration tạo **ROLE**, user login thật tạo **per-môi-trường, ngoài migration** — mật khẩu không bao giờ vào git.

| Đối tượng | Quyền | Tạo ở đâu | Dùng bởi |
|---|---|---|---|
| ROLE `dlck_ingester` | INSERT + SELECT trên `rt.*` | migration | — |
| ROLE `dlck_api` | **chỉ SELECT** trên `rt.*` (không DDL, không thấy database khác) | migration | — |
| user login (vd `ingester_worker`, `api_reader`) | `GRANT <role> TO <user>` | script per-môi-trường, ngoài migration | `ingester` / `api` |
| user quản trị mặc định của image | DDL — chỉ runner migration dùng | env của container | migration |

Điều kiện tiên quyết: image ClickHouse mặc định **tắt** SQL access management cho user default — container phải bật qua env (`CLICKHOUSE_DEFAULT_ACCESS_MANAGEMENT=1` — kiểm trên CH thật ở §12) thì `CREATE ROLE` trong migration mới chạy được.

`etl` **không có user ClickHouse** — nó không có việc gì ở kho realtime ([service-topology §4](../../../20-design/service-topology.md)).

## 7. Hạ tầng — compose profile `realtime`

Đúng chỗ [spec deploy-scaffold §3](../2026-08-24-deploy-scaffold/spec.md) để dành:

- Service `clickhouse` trong `deploy/infra/docker-compose.yml`, **profile `realtime`** — mặc định không chạy, `dev-start`/`docker-up` hiện tại không đổi hành vi.
- Image pin phiên bản LTS cụ thể (chốt số ở plan, kiểm bản LTS mới nhất lúc thực thi — không dùng tag `latest`).
- Cổng bind `127.0.0.1`: `8123` (HTTP — `clickhouse-connect` dùng) và `9000` (native TCP).
- Named volume `chdata` + healthcheck + các chốt an toàn volume như Postgres/Redis (kiểm sống sau `docker-down`, cấm bind-mount data dir).
- `.env` thêm khối ClickHouse (`CLICKHOUSE_USER`/`CLICKHOUSE_PASSWORD` bắt buộc, fail-fast; mật khẩu các user ứng dụng cấp qua env riêng cho script per-môi-trường). Không in giá trị ra log.
- Env `CLICKHOUSE_DEFAULT_ACCESS_MANAGEMENT=1` — bắt buộc để migration tạo được ROLE (§6).
- `ulimits: nofile 262144` cho service — image ClickHouse cần trần file descriptor cao; mặc định Docker Desktop thấp hơn, triệu chứng khi thiếu là "Too many open files" lúc số part tăng.
- Cấu hình mem thấp cho máy đơn (giới hạn `max_server_memory_usage_to_ram_ratio`) — con số chốt ở plan.

## 8. Migration — `database/clickhouse/` + runner

```
database/clickhouse/
├── versions/0001_rt_schema.sql        (đánh số 4 chữ số, mỗi file một mục đích)
└── ...
backend/…                              runner: python -m <module> upgrade
```

- Runner Python nhỏ trong backend (dùng env `CLICKHOUSE_URL`): **tự bootstrap** `CREATE DATABASE IF NOT EXISTS rt` + `CREATE TABLE IF NOT EXISTS rt.schema_migrations (version String, applied_at DateTime('Asia/Ho_Chi_Minh')) ENGINE = MergeTree ORDER BY version` trước khi đọc `versions/` (giải bài con gà quả trứng — sổ migration nằm trong chính database mà migration tạo). Sau đó: file nào chưa có trong sổ thì thực thi rồi ghi dòng.
- **Idempotent ở mức statement, không chỉ mức file** — vì ClickHouse **không có transaction cho DDL**: file chết ở statement thứ k thì các object 1..k−1 đã tồn tại mà sổ chưa ghi; lần chạy lại phải đi qua được. Luật cứng: **mọi statement DDL trong `versions/` phải viết `IF NOT EXISTS` / `IF EXISTS`**.
- **Không có downgrade** (khác Alembic): sửa sai = viết migration tiếp theo. Cùng luật "không sửa file migration đã chạy" của Postgres.
- Một file SQL có thể chứa nhiều statement, tách bằng `;` — quy ước parse chốt ở plan.
- Vị trí chính xác của module runner (trong `backend/core/` hay script riêng) chốt ở plan cùng cấu trúc test.

## 9. Test — seam dự kiến (danh sách chốt lại ở plan, theo §4.5)

Chạy trên **ClickHouse thật** (container test, giống cách test schema Postgres dùng DB thật — [test-strategy.md](../../../20-design/test-strategy.md)); TDD đỏ trước xanh; expected từ nguồn độc lập (bộ tick literal giải tay).

| Seam | Kiểm gì | Case biên tối thiểu |
|---|---|---|
| Runner migration | DB rỗng → `upgrade` → đủ bảng/MV/view; chạy lại lần 2 không đổi gì (idempotent mức file) | file mới thêm được chạy tiếp đúng thứ tự · **file chết giữa chừng rồi chạy lại phải đi qua được** (idempotent mức statement — DDL không transaction) |
| MV nến cổ phiếu | Insert bộ tick literal giải tay → `bar_1m_v` trả đúng o/h/l/c/v/**val**/v_bu/v_sd đã tính tay | hai tick cùng giây khác `seq` (o/c theo thứ tự sở, không theo thứ tự insert) · tick rải hai block insert cùng một phút (state gộp đúng) · phút không tick không có dòng · `side` lạ không vào `v_bu`/`v_sd` nhưng vẫn vào `v` |
| MV nến chỉ số | Chuỗi `index_delta` literal → `index_bar_1m_v` đúng o/h/l/c giải tay | **phút không frame nào mang `TV` → `cum_vol` là NULL, không phải 0** (ngữ nghĩa §4.2) |
| Dedup block | INSERT lại nguyên block đã ghi → số dòng `trade` không tăng **và** `bar_1m_v` không đếm đôi (dedup lan xuống MV) | block *khác nội dung* nhưng trùng khoá vẫn được ghi (dedup theo hash block, không theo khoá) |
| TTL — hành vi thật | Chèn dòng `ts` lùi 5 tháng + dòng lùi 1 tháng → `ALTER TABLE … MATERIALIZE TTL` (mutations_sync) → dòng cũ biến mất, dòng mới còn | bảng nến: chèn dòng 2 năm trước, `OPTIMIZE FINAL` → **vẫn còn** (không TTL) |
| Trường lạ | Frame `i` có trường ngoài danh sách → dòng ghi vào `snapshot_delta` với `extra` chứa đúng trường đó (JSON) | frame không trường lạ → `extra = ''` |
| Quyền | `dlck_api` INSERT bị từ chối, SELECT được; `dlck_ingester` INSERT được | `dlck_api` không `DROP`/`ALTER` được, không thấy database ngoài `rt` |
| Ép kiểu + timezone (thuộc plan ingester, ghi trước) | `"42100.0"` → Decimal đúng; `"215271860.0"` → UInt64 = 215271860 (khối lượng nguồn **lúc có lúc không** đuôi `.0`); `TD`+`FT` giờ VN không lệch ngày, assert `TD == toDate(ts)` | epoch `LS` giây vs `t` ms · giá trị Decimal truyền qua `clickhouse-connect` bằng `decimal.Decimal`/chuỗi, **không** bằng `float` (tránh làm tròn nhị phân) |

## 10. Ước lượng tải và dung lượng

Suy từ mẫu 12 mã / 239 s (đo 10/08/2026 — [11-bvsc-realtime §10](../../../10-sources/market/11-bvsc-realtime.md)), **chưa đo toàn thị trường**:

| Đại lượng | Ước lượng |
|---|---|
| Frame toàn thị trường giờ cao điểm | vài trăm frame/s (12 mã ≈ 13,7 frame/s) |
| Dòng ghi mỗi ngày (5 bảng frame) | ~3–6 triệu |
| Dung lượng frame thô | ~100–200 MB/ngày sau nén ⇒ **cửa sổ 3 tháng ổn định ~6–12 GB** |
| `bar_1m` + `index_bar_1m` | ~200–540k dòng/ngày ⇒ **~1 GB/năm**, tích luỹ vĩnh viễn |
| Nhịp insert từ ingester | **1 part/giây/bảng** (5 bảng × flush 1 s) — đúng **trần** khuyến nghị của ClickHouse (≤1 insert/giây mỗi bảng), không phải mức thoải mái: **flush không được nhanh hơn 1 s**. Lưu ý MV làm `bar_1m`/`index_bar_1m` nhận part cùng nhịp với bảng nguồn — tổng 7 bảng nhận part, merge nền phải theo kịp (dự kiến ổn ở quy mô này; theo dõi `system.parts` tuần đầu) |

Đo lại bằng số thật trong tuần đầu Ingester chạy; nếu lệch bậc thì cập nhật tài liệu sống kèm ngày đo.

## 11. Ngoài phạm vi spec này

| Mục | Loại | Ghi chú |
|---|---|---|
| Tick phái sinh | **chưa đo được** | Cấm giả định cho tới khi đo trong phiên ([roadmap §5.1](../../../00-overview/roadmap.md)); khi đo xong sẽ bổ sung bảng/cột bằng migration mới |
| Topic `pth` | chưa kết luận được | 0 frame qua ~6 phút đo — [11-bvsc-realtime §9](../../../10-sources/market/11-bvsc-realtime.md) ghi hai khả năng, chưa đủ để nói "không có" |
| Code Ingester (socket, ghép delta, standby) | đã có đường khác | Plan dựng ingester riêng, dùng hợp đồng §5 |
| SSE / `api` đọc ClickHouse | đã có đường khác | Thiết kế SSE giữ nguyên [market-data-store §3.4](../../../20-design/market-data-store.md); phần đọc dựng khi làm `api` |
| Chưng cất khối ngoại/breadth dài hạn | loại có chủ đích | Xem §1 — thêm được sau bằng MV, không lấy lại quá khứ |

## 12. Kiểm chứng DDL trên ClickHouse thật *(đo 2026-08-25)*

Chạy trên **ClickHouse 26.3.22.7 (LTS)**, container Docker chính thức, sau review lượt 1 — mọi khẳng định "đã kiểm" trong spec trỏ về đây:

| # | Phép kiểm | Kết quả đo |
|---|---|---|
| DDL | Toàn bộ DDL §2–§4 (8 bảng, 2 MV subquery, 2 view, TTL + settings) | ✅ chạy sạch, `system.tables` đủ 12 object đúng engine |
| T1 | MV nến: 3 tick giải tay (2 block insert, cùng phút) | ✅ `o=100 h=101 l=99 c=99 v=350 val=35150 v_bu=150 v_sd=200` — khớp giải tay tuyệt đối |
| T2 | `side` lạ (`'X'`) | ✅ vào `v`, không vào `v_bu`/`v_sd` |
| T3 | Phút không frame nào mang `TV` | ✅ `cum_vol`/`cum_value` = **NULL** (không phải 0) — ngữ nghĩa §4.2 đứng vững |
| T4 | Retry nguyên block (dedup) | ⚠️ Phát hiện quan trọng: dedup window chỉ đặt ở `trade` thì bảng gốc không nhận block trùng **nhưng nến vẫn đếm đôi** (`v=450` thay vì 350). Đủ bộ ba §5.4 (window ở cả `trade` + `bar_1m`, INSERT với `deduplicate_blocks_in_dependent_materialized_views=1`) → ✅ `trade` 1 dòng, `v=100` — nuốt trọn retry |
| T5 | TTL hành vi thật: dòng 5 tháng + dòng 1 tháng, `MATERIALIZE TTL` | ✅ dòng cũ biến mất, dòng mới còn; dòng `bar_1m` của phút cũ **vẫn còn** (không TTL) |
| T6 | `CLICKHOUSE_DEFAULT_ACCESS_MANAGEMENT=1` + `CREATE ROLE`/`GRANT`/`CREATE USER` | ✅ tạo được role/user từ SQL; user gắn `dlck_api`: SELECT được, INSERT và DROP đều bị `ACCESS_DENIED` |
| T7 | Bản MV **gốc** (alias `toStartOfMinute(ts) AS ts` che cột) | Trên 26.3: phân giải về **alias**, ghi đúng 1 dòng/phút — không lỗi. Vẫn giữ dạng subquery vì hành vi này phụ thuộc analyzer, không cam kết đa phiên bản |

Giới hạn của phép kiểm: chạy trên dữ liệu literal vài dòng — **chưa đo tải thật** (tần suất part, merge, RAM); mục §10 vẫn là ước lượng. Kịch bản kiểm lưu ở scratchpad phiên làm việc, sẽ tái lập thành test seam chính thức ở bước plan (§9).

## 13. Checklist quét tài liệu sống khi spec chốt (luật §1.7)

- [ ] `market-data-store.md` — banner: phần realtime (§3.2 điểm 4, §5.3, §5.7 dòng `bar_1m`) được thay bởi spec này; giữ nguyên văn làm lịch sử
- [ ] `database/README.md` — thêm mục ClickHouse: trạng thái, cách chạy migration + test
- [ ] `service-topology.md` — đối chiếu §4 (miền ClickHouse: thêm nhắc TTL 3 tháng frame thô / nến vĩnh viễn nếu cần một dòng)
- [ ] Điểm nối factor đã đổi hướng so với `step-01 §2` ("ClickHouse cần view hệ số từ market" → nay là **`api` cần**, ClickHouse không phụ thuộc Postgres): ghi câu chốt mới ở tài liệu sống (`market-data-store`/`service-topology`), **không sửa** `step-01` (vùng lịch sử 90-records); nếu cần, một dòng ghi chú ở `database/README.md`
- [ ] `roadmap.md` §5.2 — đánh dấu dòng "Cập nhật market-data-store theo ClickHouse" đã xong, trỏ hồ sơ này
- [ ] `deploy-scaffold` spec/ledger — **không sửa** (vùng lịch sử 90-records); profile `realtime` ghi ở compose thật khi thực thi
- [ ] `git grep` "TimescaleDB\|bar_1m\|hypertable" toàn repo — xác nhận mọi hit còn lại hoặc đã đúng, hoặc thuộc vùng lịch sử
