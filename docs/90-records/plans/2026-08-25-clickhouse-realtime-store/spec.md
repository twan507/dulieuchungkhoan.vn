# Spec — Kho realtime ClickHouse

**Ngày:** 2026-08-25 · **Trạng thái:** 🟡 chờ chủ dự án duyệt · **Loại:** kiến trúc — thay phần kho realtime TimescaleDB trong [market-data-store.md](../../../20-design/market-data-store.md) theo [ADR 0007](../../../00-overview/decisions/0007-monorepo-layout-and-stack.md)

**Phạm vi:** lược đồ ClickHouse cho dữ liệu realtime BVSC (5 topic), materialized view sinh nến, chính sách giữ dữ liệu, cách Ingester ghi, quyền truy cập, hạ tầng compose, cơ chế migration. **Không** thiết kế lại Ingester ở mức code (thuộc plan dựng ingester) và **không** đụng Postgres/Redis — ranh giới ba kho giữ nguyên [service-topology §4](../../../20-design/service-topology.md).

**Nguồn số đo dùng trong spec:** [11-bvsc-realtime.md](../../../10-sources/market/11-bvsc-realtime.md) — đo phiên chiều 10/08/2026, 3.266 frame, 12 mã. Ước lượng toàn thị trường là **suy rộng từ mẫu này, chưa đo toàn thị trường** — sẽ đo lại khi Ingester chạy thật.

---

## 1. Quyết định chốt trong phiên brainstorm 2026-08-25 (chủ dự án)

| # | Quyết định | Lý do |
|---|---|---|
| 1 | **Lưu cả 5 topic** (`t` · `o10` · `i` · `idx` · `ptm`), mỗi loại sự kiện một bảng chuẩn hoá đã ép kiểu | Đủ dựng lại mọi thứ, truy vấn được ngay; `idx` bắt buộc phải hứng vì nến chỉ số chỉ dựng được từ nó |
| 2 | **Frame thô giữ cửa sổ trượt 3 tháng** (TTL DELETE — cửa sổ thật 3–4 tháng, xem §2), không giữ ròng năm này qua năm khác | Vi cấu trúc chỉ phân tích theo cửa sổ; 3 tháng đủ hồi cứu một mùa BCTC và đủ thời gian phát hiện lỗi gom nến. Dung lượng: **một chủ duy nhất ở §10** — chạm đầu cao của dải thì rút TTL bằng một lệnh ALTER |
| 3 | **Nến 1 phút giữ vĩnh viễn, đắp thêm mãi** — gồm `bar_1m` (cổ phiếu, kèm `v_bu`/`v_sd` và `val` = giá trị giao dịch) và `index_bar_1m` (chỉ số) | Nguyên tắc "chưng cất trước khi quên": thứ cần dài hạn phải gom về dạng nhỏ trước khi frame thô trôi khỏi cửa sổ. `v_bu`/`v_sd` giữ chuỗi dòng tiền chủ động, `val` giữ VWAP/turnover theo phút — đều chi phí ~0. *(`val` bổ sung theo review 2026-08-25 lượt 1: thiếu nó thì VWAP mất vĩnh viễn sau TTL mà chưa từng được quyết tường minh)* |
| 4 | **Hệ số điều chỉnh giá: `api` tự ghép** — đọc factor từ Postgres, nến từ ClickHouse, nhân khi trả kết quả | ClickHouse giữ giá thô thuần tuý, không phụ thuộc runtime nào sang Postgres. Factor ít, cache được, đổi ~vài mã/ngày |
| 5 | **Migration ClickHouse: file SQL đánh số + runner Python nhỏ tự viết**, ghi bảng `rt.schema_migrations` | Alembic không hỗ trợ ClickHouse tử tế; cùng triết lý "SQL thô, kiểm soát từng dòng" đã chọn cho Postgres |
| 6 | Buffer ghi batch **trong tiến trình Ingester**, chu kỳ flush **cố định 1 giây** — N dòng chỉ là **trần kích thước block** (chạm N thì cắt block chờ nhịp sau + cảnh báo), **không** rút ngắn chu kỳ | Giữ "batch writer ngoài hot path" của thiết kế cũ, và giữ trần 1 part/giây/bảng của §10. Chấp nhận có ý thức: ingester chết mất tối đa ~1 s frame chưa flush — cùng bậc với failover < 2 s đã chấp nhận |
| 7 | **Chưa có gì cho phái sinh** — bảng bám cổ phiếu/chỉ số | Chưa đo được realtime phái sinh trong phiên ([roadmap §5.1](../../../00-overview/roadmap.md)); cấm giả định |
| 8 | **Phạm vi đăng ký: toàn bộ mã cổ phiếu + ETF đang giao dịch**, danh mục **hợp nhất `/quotes` + `/datafeed/instruments`** khử trùng theo mã, phân loại bằng bảng `StockType` **của `/quotes`** × 3 topic `i`/`o10`/`t` + **15 mã chỉ số** `idx` + **3 sàn** `ptm` | Mục tiêu là nến 1' **toàn thị trường** ([roadmap §2 việc 4](../../../00-overview/roadmap.md)) — đăng ký rổ con là tự tạo lỗ hổng dữ liệu vĩnh viễn. ⚠️ Không lọc bằng `StockType` của `/datafeed/instruments`: **bảng mã chỉ có nghĩa trong phạm vi một endpoint** ([00-conventions bẫy 10](../../../10-sources/market/00-conventions.md) — cùng mã trả `12` ở `/quotes` nhưng `1` ở instruments), và **không endpoint nào một mình đủ làm danh mục** (bẫy 11 — `VFMVF1` chỉ có ở `/quotes`). Chứng quyền/lô lẻ/trái phiếu **loại có chủ đích** theo [CLAUDE.md §2.2](../../../../CLAUDE.md). N thật chưa đếm trên danh mục hợp nhất — §10 dùng dải. Tải kéo theo: xem §10 |
| 9 | **Danh sách mã do ingester tự sở hữu lúc runtime**: gọi REST BVSC hợp nhất hai endpoint lúc khởi động + làm mới **trước phiên mỗi ngày**; reconnect giữa phiên dùng cache, **không** gọi lại. **Không đọc Postgres** | Đọc `market.security` bên Postgres là tạo đúng phụ thuộc runtime chéo kho mà quyết định #4 dựng ra để tránh. Mã niêm yết mới **trong ngày** chờ lần làm mới hôm sau — chấp nhận có ý thức (danh mục tăng ~4 mã/5 ngày, [01-bvsc-rest](../../../10-sources/market/01-bvsc-rest.md): "bảng này không tĩnh") |
| 10 | **Backup hằng đêm, dung lượng chặn trên không phình** *(mở rộng theo yêu cầu chủ dự án 2026-08-26: phủ cả cửa sổ frame, lưu đè theo phiên)*. Disk `backups` trỏ **thư mục host ngoài Docker volume**; chạy bằng user quản trị theo lịch (cơ chế lịch chốt ở plan). Hai lớp: **(a) hai bảng nến vĩnh viễn** — full backup mỗi đêm, giữ 7 bản gần nhất + 1 bản đầu mỗi tháng; **(b) 5 bảng frame** — backup **theo partition tháng, lăn theo cửa sổ TTL**: partition đã đóng backup **một lần** (bất biến, không chép lại); partition tháng hiện tại backup lại mỗi đêm; file backup của partition đã bị TTL drop thì xoá ⇒ tổng backup frame ≈ **1× cửa sổ (~5–60 GB), không phình theo thời gian**, I/O mỗi đêm chỉ cỡ partition đang mở. "Đè" = **ghi tên mới → xoá bản cũ sau khi thành công** (ghi trùng tên bị CH chặn `BACKUP_ALREADY_EXISTS` — đo T15; cách này cũng tránh hỏng cả bản cũ lẫn mới nếu chết giữa chừng) | `bar_1m` là **dữ liệu không tái tạo được** (nguồn không có replay) trên một instance đơn không replica; frame window cũng không nguồn nào cấp lại — tiền đề "data thị trường crawl lại được nên không cần backup" của [service-topology §4](../../../20-design/service-topology.md) **không áp dụng** cho miền này; câu đó phải sửa theo (checklist §13). Cơ chế đã kiểm trên CH thật *(§12, T15)*: `BACKUP TABLE … PARTITION 'YYYYMM' TO Disk('backups', …)` và `RESTORE … SETTINGS allow_non_empty_tables=true` chạy đúng; **RESTORE gắn part trực tiếp, không kích MV** — khôi phục `trade` không làm nến đếm đôi. Backup nằm cùng máy chỉ chống mất volume/lỗi thao tác, chưa chống chết đĩa — đưa bản sao ra máy khác là việc vận hành sau, ghi ở plan |

**Đã cân nhắc và loại (loại có chủ đích):**

| Mục | Lý do loại |
|---|---|
| Bảng frame thô JSON làm landing zone (kiểu `staging.raw_payload`) | Tốn ~2× dung lượng và một đường ghi nữa; bảng sự kiện đã ép kiểu + cột `extra` hứng trường lạ là đủ phòng schema đổi |
| Bảng chưng cất khối ngoại intraday (`FB`/`FS` cuối mỗi phút) | Chủ dự án chốt chỉ nến 1' là vĩnh viễn. Khối ngoại EOD đã có từ REST; intraday hồi cứu được trong cửa sổ 3 tháng. Nếu sau này cần chuỗi dài hạn: thêm một MV là xong, nhưng dữ liệu trước thời điểm thêm không dựng lại được |
| Chưng cất độ rộng thị trường (breadth) dài hạn | Cùng lý do trên — trong cửa sổ 3 tháng đọc từ `index_delta`; ngoài cửa sổ chấp nhận không có |
| Nến 5m/15m/60m vật chất hoá (chuỗi aggregate phân cấp kiểu Timescale cũ) | Tính lúc đọc từ `bar_1m_v` — **dự kiến** đủ nhanh ở quy mô này, đo lại khi có một tháng dữ liệu thật; chậm mới thêm MV |
| `async_insert` server-side · Buffer table engine | Kém kiểm soát hơn buffer trong tiến trình, thêm điểm mù khi mất dữ liệu |
| ClickHouse dictionary trỏ sang Postgres lấy factor · ETL đẩy factor sang ClickHouse | Tạo phụ thuộc runtime chéo kho / vi phạm "một người ghi mỗi miền" — quyết định #4 đã thay |

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
| Ép kiểu | Nguồn trả **số dạng chuỗi** ở `o`/`t`/`idx` — ingester ép tại cổng. Giá `Decimal64(2)` · khối lượng `UInt64` · giá trị tiền `Decimal64(2)` (trần đo được **9,2×10¹⁶** *(lượt 3: `toDecimal64(9223372036854775807,0)/100`)* — giá trị khớp toàn sàn cỡ 10¹³/ngày *(ước lượng, chưa đo)*, dư ~9.200×; không dùng `Decimal128` cho cột frame vì tốn gấp đôi byte trên hàng triệu dòng/ngày). Riêng cột tổng `val` của `bar_1m` dùng `Decimal128(2)` vì là tích `price × volume` cộng dồn. Tràn Decimal là **lỗi cứng, không tràn im lặng** *(đo lượt 3)* — xử lý ở luật block độc §5.8. Chuỗi thừa thập phân (`"100.005"` → cột scale 2) bị CH **cắt im lặng** *(đo lượt 3)* — ingester phải tự chuẩn hoá, không dựa CH |
| Mã | `symbol LowCardinality(String)` — luồng realtime dùng **ticker**, không phải organ_code (khác REST FiinTrade) |
| Trường phân loại của nguồn | `LowCardinality(String)`, **không dùng Enum** — danh sách giá trị của nguồn chưa chắc đóng (bài học `i` tăng 22→34 trường) |
| Trường lạ / không map | `snapshot_delta`, `index_delta`, `pt_match` có cột `extra String` chứa JSON **mọi trường không map vào cột** — gồm cả trường lạ chưa từng thấy ("xử lý trường lạ an toàn", [11-bvsc-realtime §11.9](../../../10-sources/market/11-bvsc-realtime.md)) lẫn trường đã biết nhưng cố ý không lên cột (`MKI`/`IAC` của `ptm`). `trade`/`quote` **không có `extra`** — chấp nhận có ý thức, **chưa đo tính đóng** của bộ trường `t`/`o` (nguồn quan sát 10/11 trường ổn định nhưng mẫu nhỏ); bù bằng ingester log khoá lạ, xem §5.6 |
| Mẫu truy vấn tối ưu | `ORDER BY (symbol, ts, …)` chọn có ý thức cho mẫu chủ đạo "**một mã theo thời gian**". Cắt ngang toàn thị trường tại một thời điểm phải quét partition tháng — chấp nhận (cỡ vài GB/partition); nếu sau này đo thấy chậm mới thêm skip index minmax theo `ts` |
| Truy vết | Mọi bảng frame có `received_at DateTime64(3)` — lúc ingester nhận, để đo độ trễ và truy sự cố |
| TTL | `TTL toDate(ts) + INTERVAL 3 MONTH DELETE` trên 5 bảng frame, kèm `SETTINGS ttl_only_drop_parts = 1` — đơn vị xoá là **PART** (không phải partition): một part chỉ bị drop khi **dòng trẻ nhất trong part** qua hạn, part hết hạn rơi thì part khác cùng partition vẫn còn *(đo lượt 3: hai part cùng partition — part hết hạn bị drop, part kia còn; hai dòng bị merge chung một part — dòng đã hết hạn sống tới khi cả part hết hạn)*. Hệ quả: thời gian giữ thật là **hệ quả của hành vi merge**, thực tế dao động **3–4 tháng** vì merge gom part theo partition tháng — không phải hằng số suy từ lược đồ. `bar_1m`/`index_bar_1m` **không TTL** |

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
  received_at   DateTime64(3, 'Asia/Ho_Chi_Minh') DEFAULT now64(3)
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
- **`non_replicated_deduplication_window`** — lưới chống ghi trùng **mức block** cho kịch bản retry (xem §5); đặt trên **cả 5 bảng frame lẫn `bar_1m`** — MV thì chỉ nến cổ phiếu nhạy (`sum`), nhưng bảng thô nào cũng là **mặt đọc trực tiếp** (breadth từ `index_delta`, khối ngoại từ `snapshot_delta`, tổng thoả thuận từ `pt_match`) nên block retry nhân đôi dòng thô cũng là sai — xem bất biến ở §5. `received_at` có `DEFAULT now64(3)` làm lưới chống quên cột (không có DEFAULT, writer bỏ sót sẽ ra `1970-01-01` im lặng); writer vẫn phải tự cấp giá trị thật vì nó nằm trong khoá argMin của nến (§4.1).

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
  received_at DateTime64(3, 'Asia/Ho_Chi_Minh') DEFAULT now64(3)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(toDate(ts))
ORDER BY (symbol, ts, top)
TTL toDate(ts) + INTERVAL 3 MONTH DELETE
SETTINGS ttl_only_drop_parts = 1, non_replicated_deduplication_window = 100;
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
  last_vol    Nullable(UInt64),                         -- CV  (CV và P1 cùng nghĩa "KL lệnh khớp gần nhất",
  last_vol2   Nullable(UInt64),                         -- P1   quan sát trùng giá trị (đo 10/08/2026) — giữ cả hai vì là delta, frame có thể chỉ mang một)
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
  received_at DateTime64(3, 'Asia/Ho_Chi_Minh') DEFAULT now64(3)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(toDate(ts))
ORDER BY (symbol, ts)
TTL toDate(ts) + INTERVAL 3 MONTH DELETE
SETTINGS ttl_only_drop_parts = 1, non_replicated_deduplication_window = 100;
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
  total_value Nullable(Decimal64(2)),                   -- TVA (đo được 5,7×10¹²; dải kiểu xem §2 — PHẢI khớp kiểu với state cum_value ở §4.2)
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
  received_at DateTime64(3, 'Asia/Ho_Chi_Minh') DEFAULT now64(3)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(toDate(ts))
ORDER BY (symbol, ts)
TTL toDate(ts) + INTERVAL 3 MONTH DELETE
SETTINGS ttl_only_drop_parts = 1, non_replicated_deduplication_window = 100;
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
  received_at DateTime64(3, 'Asia/Ho_Chi_Minh') DEFAULT now64(3)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(toDate(ts))
ORDER BY (symbol, ts, order_id)
TTL toDate(ts) + INTERVAL 3 MONTH DELETE
SETTINGS ttl_only_drop_parts = 1, non_replicated_deduplication_window = 100;
```

*(`MKI` (mã sàn dạng số — trùng thông tin `market`) và `IAC` (cờ trạng thái, bản chất chưa xác định) không lên cột mà đi vào `extra` — không rơi rụng, và khi nào hiểu `IAC` thì nâng thành cột bằng migration mới. `TD`/`TI` không lưu — `ts` từ `LS` đã đủ. Engine `MergeTree` thuần cùng lý do với `quote`.)*

## 4. Nến — hai bảng vĩnh viễn + hai materialized view

### 4.1 `rt.bar_1m` — nến cổ phiếu, gồm dòng tiền chủ động

Giá **THÔ**, không bao giờ sửa (nguyên tắc "lưu thô, điều chỉnh lúc đọc" giữ nguyên). Trạng thái aggregate để MV gom đúng kể cả khi frame một phút đến rải nhiều block insert:

```sql
CREATE TABLE rt.bar_1m (
  symbol LowCardinality(String),
  ts     DateTime('Asia/Ho_Chi_Minh'),                  -- đầu phút
  o    AggregateFunction(argMin, Decimal64(2), Tuple(DateTime('Asia/Ho_Chi_Minh'), UInt64, DateTime64(3, 'Asia/Ho_Chi_Minh'))),
  h    AggregateFunction(max, Decimal64(2)),
  l    AggregateFunction(min, Decimal64(2)),
  c    AggregateFunction(argMax, Decimal64(2), Tuple(DateTime('Asia/Ho_Chi_Minh'), UInt64, DateTime64(3, 'Asia/Ho_Chi_Minh'))),
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
  toStartOfMinute(event_ts)                            AS ts,
  argMinState(price, (event_ts, seq, received_at))     AS o,
  maxState(price)                                      AS h,
  minState(price)                                      AS l,
  argMaxState(price, (event_ts, seq, received_at))     AS c,
  sumState(volume)                                     AS v,
  sumState(toDecimal128(price, 2) * volume)            AS val,
  sumState(if(side = 'B', volume, toUInt64(0)))        AS v_bu,
  sumState(if(side = 'S', volume, toUInt64(0)))        AS v_sd
FROM (SELECT symbol, ts AS event_ts, seq, price, volume, side, received_at FROM rt.trade)
GROUP BY symbol, ts;
```

**Bất biến của khoá `argMin`/`argMax` — khoá phải TOTAL trong (mã, phút):** khi hai dòng hoà khoá, `argMin`/`argMax` chọn **không xác định và không ổn định qua merge nền** — đo được nến trả một giá trước merge và giá khác sau merge *(phản chứng review lượt 3, 2026-08-26)* — không chấp nhận được trên bảng vĩnh viễn tuyên bố "giá thô bất biến". Vì tính duy nhất của `SM` trong (mã, giây) **chưa đo**, khoá phải thêm `received_at` làm nhánh phân thắng: `(event_ts, seq, received_at)` — đã kiểm ổn định qua nhiều lần `OPTIMIZE FINAL` *(§12, T12)*. Writer vì thế phải cấp `received_at` **đơn điệu tăng theo mã trong một phiên chạy** (đồng hồ tường + tie-break bộ đếm nếu hai frame cùng ms — chi tiết ở plan ingester); hoà cả ba thành phần chỉ còn xảy ra cho frame trùng thật sự — thứ lưới dedup §5.4 đã chặn.

Hai chi tiết cú pháp, đã kiểm trên ClickHouse thật *(xem §12)*:

- Kiểu khoá trong `AggregateFunction(argMin, …)` phải khai **đủ múi giờ và đủ ba thành phần** `Tuple(DateTime('Asia/Ho_Chi_Minh'), UInt64, DateTime64(3, 'Asia/Ho_Chi_Minh'))` — khớp đúng kiểu `(ts, seq, received_at)` của `trade`; đây cũng là quy ước §2 "khai múi giờ tường minh".
- MV đọc qua **subquery đổi tên** `ts AS event_ts` — chọn để an toàn đa phiên bản: bản alias trực tiếp đo trên 26.3 chạy đúng (T7) nhưng hành vi phân giải alias trùng tên phụ thuộc analyzer, không cam kết.

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

1. **Thoả thuận không vào nến** — nến chỉ tính khớp lệnh (luồng `t`); `ptm` đứng ngoài. Đúng quy ước nến của mọi bảng giá. *(Giả định đi kèm — `t` chỉ chứa khớp lệnh, không lẫn thoả thuận: chưa đo trực tiếp; phép đối chứng AVO/AVA ở §5.7 kiểm nó liên tục trên dữ liệu thật.)*
2. **Nến lớn (5m/15m/60m/ngày) tính lúc đọc** từ `bar_1m_v` bằng `toStartOfInterval` — dự kiến đủ nhanh ở quy mô ~540k dòng nến/ngày; **đo lại khi có một tháng dữ liệu thật**, chậm mới thêm MV (đúng mục "đã cân nhắc và loại" §1).
3. **Điều chỉnh lúc đọc, ở `api`**: giá trả cho người dùng = giá thô × factor, factor đọc từ view hệ số bên Postgres (`market`), cache trong `api`. ClickHouse không biết Postgres tồn tại. **Chuỗi khoá ghép phải đi ba chặng**: `symbol` của ClickHouse là **ticker** → tra `market.security` ra `security_id` → lấy factor — không phải quan hệ trực tiếp (bẫy `organCode ≠ ticker` 41% nằm đúng đây). **Ngày chưa có factor** (nến trong phiên — `getPriceData` crawl sau 15:00): dùng **factor = 1**, vì sự kiện quyền có hiệu lực từ đầu ngày giao dịch không hưởng quyền — giá thô hôm nay đã ở thang sau điều chỉnh, các hệ số lịch sử mới là thứ co giá quá khứ về thang hiện tại.

**Giả định chưa đo — thứ tự `seq` trong cùng giây:** `o`/`c` của nến dựa vào `argMin`/`argMax` theo khoá `(ts, seq, received_at)`, tức tin rằng `SM` (rồi tới thứ tự nhận) phản ánh đúng thứ tự khớp của sở trong cùng một giây. Nhờ khoá total, kết quả **luôn ổn định**; nếu giả định thứ tự đổ thì sai lệch giới hạn ở **`o`/`c` của các giây nhiều lệnh** (nặng nhất là phút ATO/ATC — khớp định kỳ dồn vào một giây); `h`/`l`/`v`/`val`/`v_bu`/`v_sd` miễn nhiễm vì không phụ thuộc thứ tự. **Phiên đo SM** (đơn điệu theo mã? duy nhất? bộ đếm toàn sở?) là **điều kiện tiên quyết trước khi bật ghi thật** — ghép cùng phiên đo phái sinh của [roadmap §5.1](../../../00-overview/roadmap.md), không đợi tới plan ingester.

**Thủ tục sửa nến (khi phát hiện MV sai):** `AggregatingMergeTree` cộng dồn state — chạy lại `INSERT INTO bar_1m SELECT … FROM trade` để "vá" sẽ **đếm đôi**, không sửa. Thủ tục chuẩn, **đúng thứ tự**:

0. **Dừng ingester (hoặc `DETACH` MV) trước, gắn lại sau khi xong** — bất kỳ tick nào lọt vào giữa chừng sẽ được đếm **hai lần** (một qua MV lúc insert, một qua SELECT backfill); phản chứng review lượt 3 đo được `v` gấp đôi khi bỏ bước này.
1. `ALTER TABLE rt.bar_1m DROP PARTITION <YYYYMM>`.
2. `INSERT INTO rt.bar_1m SETTINGS insert_deduplication_token = 'repair-<YYYYMM>-<run-id>' SELECT <đúng biểu thức MV, kể cả khoá (event_ts, seq, received_at)> FROM rt.trade WHERE toYYYYMM(toDate(ts)) = <YYYYMM>`. **Token bắt buộc, cố định trong một đợt vá**: cửa sổ dedup **không phủ `INSERT … SELECT`** theo nội dung — retry không token là **nến nhân đôi im lặng** (đo §12/T13: không token retry ra 20 thay vì 10; cùng token thì retry bị nuốt, ra đúng 10). Đợt vá mới (sau một lần DROP mới) dùng `run-id` mới.

Ràng buộc cứng: **chỉ vá được phần `trade` còn trong cửa sổ TTL (3–4 tháng)** — đây chính là lý do "3 tháng đủ thời gian phát hiện lỗi gom nến" ở quyết định #2, và là lý do test MV phải chặt ngay từ đầu. Ngoài cửa sổ đó, nguồn cứu cuối là **backup hằng đêm** (quyết định #10).

### 4.2 `rt.index_bar_1m` — nến chỉ số

Chỉ số không có "lệnh khớp" — nến gom từ chuỗi `index_value` của `index_delta` (chỉ frame có `MI`). Khối lượng của nguồn là **luỹ kế trong ngày** ⇒ lưu luỹ kế cuối phút (max), khối lượng theo phút suy ra bằng hiệu khi đọc.

> ⚠️ **Chất lượng khác `bar_1m`:** nguồn đẩy `idx` ~0,09 frame/giây mỗi chỉ số *(đo 10/08/2026)* ≈ **5 mẫu/phút**. `h`/`l` của nến chỉ số là cao/thấp **của các mẫu**, không phải cao/thấp thật trong phút — khác `bar_1m` gom từ **từng lệnh khớp** nên o/h/l/c chính xác. Ghi ở đây vì bảng là vĩnh viễn, người đọc sau không được tưởng hai bảng cùng chất lượng.

```sql
CREATE TABLE rt.index_bar_1m (
  symbol LowCardinality(String),
  ts     DateTime('Asia/Ho_Chi_Minh'),
  o AggregateFunction(argMin, Decimal64(2), Tuple(DateTime64(3, 'Asia/Ho_Chi_Minh'), DateTime64(3, 'Asia/Ho_Chi_Minh'))),
  h AggregateFunction(max, Decimal64(2)),
  l AggregateFunction(min, Decimal64(2)),
  c AggregateFunction(argMax, Decimal64(2), Tuple(DateTime64(3, 'Asia/Ho_Chi_Minh'), DateTime64(3, 'Asia/Ho_Chi_Minh'))),
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
  argMinState(assumeNotNull(index_value), (event_ts, received_at))  AS o,
  maxState(assumeNotNull(index_value))                              AS h,
  minState(assumeNotNull(index_value))                              AS l,
  argMaxState(assumeNotNull(index_value), (event_ts, received_at))  AS c,
  maxState(total_vol)                                               AS cum_vol,
  maxState(total_value)                                             AS cum_value
FROM (SELECT symbol, ts AS event_ts, index_value, total_vol, total_value, received_at
      FROM rt.index_delta WHERE index_value IS NOT NULL AND index_value > 0)
GROUP BY symbol, ts;
```

*(Khoá argMin/argMax cũng phải **total** ở đây — cùng bất biến §4.1, cùng là bảng vĩnh viễn: phản chứng review lượt 4 đo được khoá một thành phần `event_ts` cho `o`/`c` **đổi giá trị sau merge** khi hai frame hoà mili-giây; khoá `(event_ts, received_at)` đo ổn định qua `OPTIMIZE FINAL` — §12, T14. Xác suất hoà ms của `idx` chưa đo nên không được viện "hiếm". Tính idempotent-với-bản-sao của §5.4 giữ nguyên: frame trùng thật thì cả khoá lẫn giá trị đều bằng nhau.)*

*(Guard `index_value > 0`: chặn nến rác nếu nguồn đẩy `MI = 0` quanh mở phiên — **giờ đẩy `idx` ngoài 13:08–13:12 chưa được đo** (mẫu đo nằm giữa phiên chiều); bảng vĩnh viễn nên thà chặn thừa. Tuần đầu chạy thật phải ghi nhận phút sớm nhất/muộn nhất có frame `idx` và `t` — xem §10.)*

**Ngữ nghĩa NULL của hai cột luỹ kế — quyết định spec, không phải chi tiết plan** (vì bảng vĩnh viễn, sai là không dựng lại được): `idx` là delta nên **cả phút có thể không frame nào mang `TV`/`TVA`**. Nếu ép `assumeNotNull` như hai cột giá, phút đó thành `cum_vol = 0` → người đọc suy khối lượng-theo-phút bằng hiệu sẽ được **một cặp hiệu âm/dương khổng lồ**. Chốt: state khai `Nullable`, `maxState` **bỏ qua NULL và trả NULL khi cả phút NULL** *(đã kiểm hành vi trên ClickHouse thật — §12)* — NULL nghĩa trung thực là "phút này nguồn không cập nhật luỹ kế", người đọc carry-forward bằng window function. `assumeNotNull` chỉ dùng cho `index_value` vì subquery đã `WHERE index_value IS NOT NULL`. Lưu ý cho người đọc dữ liệu: NULL của `cum_vol` có **hai** nguyên nhân — phút không frame nào mang `TV`, **hoặc** frame mang `TV` nhưng không mang `MI` nên bị `WHERE` loại cả dòng; cả hai đều tự lành ở phút sau (luỹ kế), carry-forward xử lý như nhau.

View đọc (mặt tiếp xúc cho `api`):

```sql
CREATE VIEW rt.index_bar_1m_v AS
SELECT symbol, ts,
       argMinMerge(o) AS o, maxMerge(h) AS h, minMerge(l) AS l, argMaxMerge(c) AS c,
       maxMerge(cum_vol) AS cum_vol, maxMerge(cum_value) AS cum_value
FROM rt.index_bar_1m
GROUP BY symbol, ts;
```

**Hợp đồng đọc luỹ kế — ba luật, vì `TV`/`TVA` là luỹ kế TRONG NGÀY:**

1. Carry-forward NULL và tính hiệu đều phải **`PARTITION BY symbol, toDate(ts)`** — không bao giờ xuyên ngày (hiệu giữa nến cuối ngày d và nến đầu ngày d+1 là số âm khổng lồ, cùng họ lỗi với bậc nhảy 0 đã chặn ở trên).
2. Phút đầu tiên trong ngày có `cum_vol` khác NULL: khối-lượng-theo-phút của nó = **chính `cum_vol`** (đã gồm trọn ATO), không phải hiệu với phút trước.
3. Hiệu âm trong cùng ngày = dấu hiệu lỗi (nguồn nhảy lùi) — tầng đọc phải chặn/cảnh báo, không được trả ra cho người dùng.

## 5. Ingester ghi thế nào — hợp đồng writer

Chi tiết code thuộc plan dựng ingester; spec chốt **hợp đồng**:

1. **Hot path không đụng ClickHouse** (giữ nguyên [market-data-store §3.2](../../../20-design/market-data-store.md)): frame → ghép delta → Redis HASH + PUBLISH. Ghi ClickHouse qua hàng đợi trong tiến trình.
2. **Batch flush:** mỗi bảng một buffer, **chu kỳ flush cố định 1 giây** bằng INSERT native qua `clickhouse-connect`. N dòng là **trần kích thước block** (chạm N giữa chu kỳ thì cắt block chờ nhịp flush kế + đánh cảnh báo — tải cao bất thường), **không phải** điều kiện flush sớm: flush nhanh hơn 1 s là vượt trần part/giây của §10. N chốt ở plan, cỡ vài nghìn.
3. **Ép kiểu tại cổng:** chuỗi → số trước khi vào buffer; parse `TD`+`FT`/`TD`+`TI` theo `Asia/Ho_Chi_Minh`; `LS` là epoch **giây**.
4. **Chống trùng hai lưới, đặt đúng hai tầng khác nhau** — vì MV gom **lúc insert**: bản sao lọt vào `trade` là `v`/`val`/`v_bu`/`v_sd` đếm đôi **vĩnh viễn** trong nến, không cơ chế nào sau đó chữa được:
   - **Lưới frame (tại ingester):** bỏ frame đã thấy khi nguồn đẩy lại sau nối lại + đăng ký lại. Cấu trúc cụ thể (tập khoá trong cửa sổ trượt — **không phải** chỉ nhớ một khoá cuối, vì reconnect đẩy lại cả loạt) chốt ở plan ingester. ⚠️ **Giả định chưa đo:** dedup theo `SM` giả định SM đơn điệu/duy nhất theo mã — tài liệu nguồn chưa đo tính chất này; plan ingester phải kèm một phiên đo SM trước khi chốt luật, trước đó dùng tập-khoá-đã-thấy, không dùng so sánh thứ tự.
   - **Lưới block (tại ClickHouse):** bắt kịch bản lưới frame **không thể** bắt: flush thành công nhưng ack rớt (timeout, CH restart) → writer retry **nguyên block** → block trùng bị server nuốt im lặng. `non_replicated_deduplication_window = 100` đặt trên **cả 5 bảng frame và `rt.bar_1m`**. Đã đo *(§12)*: dedup của bảng gốc **không tự lan xuống bảng đích MV** — thiếu window trên `bar_1m` là nến đếm đôi dù `trade` sạch (T4 lượt đầu); có window ở cả hai thì retry bị nuốt trọn **kể cả khi client không truyền** `deduplicate_blocks_in_dependent_materialized_views` (T4 chạy lại sau đổi khoá — trên 26.3, block state của MV trùng hash bị chính window của `bar_1m` chặn). Setting đó vẫn **đặt server-side bằng SETTINGS PROFILE gắn role `dlck_ingester` trong migration** *(đo T9: profile ăn tới tận MV)* làm dây đai phòng hờ — hành vi dedup MV không cam kết đa phiên bản. Cửa sổ dedup **sống qua restart server** *(đo T8)*. Hệ quả cho writer: **retry một INSERT phải gửi lại đúng block cũ nguyên vẹn** (không gộp thêm dòng mới — đổi nội dung là đổi hash, mất tác dụng dedup). Trong migration, `CREATE ROLE` phải đứng **trước** `CREATE SETTINGS PROFILE … TO role` — chiều ngược lại lỗi `Code: 511` *(đo lượt 3)*.
   - **Bất biến phải giữ:** MV chỉ số (`max`/`argMin`/`argMax`) **idempotent với bản sao** — window trên các bảng frame còn lại là để bảo vệ **mặt đọc trực tiếp** của chính bảng thô, không phải MV. Ràng buộc đi kèm: **cấm thêm aggregate cộng dồn (`sum`/`count`) lên `index_delta`/`snapshot_delta`** mà không có dedup + kiểm tương đương `trade`.
5. **Mất mát chấp nhận có ý thức:** ingester chết → mất tối đa ~1 s buffer chưa flush + thời gian standby tiếp quản (< 2 s). Không có cơ chế replay từ nguồn — đã biết từ khảo sát. Retry INSERT lỗi được phép — **an toàn nhờ lưới block chỉ với INSERT native block của writer**; đường `INSERT … SELECT` (thủ tục vá §4.1) **không** được lưới nội dung phủ, phải dùng `insert_deduplication_token` *(đo §12/T13)*. Ngân sách retry phải nhỏ hơn tuổi thọ cửa sổ dedup: window 100 block ở nhịp 1 block/giây ≈ 100 giây — backoff tổng của một block phải xong dưới ngưỡng đó, quá thì bỏ block (mất mát, đếm vào metric) chứ không ghi liều.
6. **Trường lạ:** frame `i`/`idx`/`ptm` — trường không map vào cột → JSON vào `extra`, không rơi rụng; bộ giám sát hợp đồng theo dõi tỷ lệ `extra != ''` để biết nguồn vừa thêm trường. Frame `t`/`o` **không có lưới `extra`** — đây là **chấp nhận có ý thức chưa đo** (nguồn không cảnh báo danh sách mở cho `t`/`o`, nhưng cũng chưa ai đo tính đóng; mẫu chỉ 356 frame `t`/933 frame `o`): bù bằng ingester **đếm và log khoá lạ** gặp trong `t`/`o` (không lưu), khoá lạ xuất hiện là tín hiệu P2 để nâng cột bằng migration.
7. **Đối chứng nội tại cuối phiên (bất biến vận hành):** với mỗi (mã, ngày), so `Σ bar_1m_v.v` với `max(trade.cum_volume)` (tương tự `val` vs `cum_value`). **Chủ sở hữu: plan ingester** — chạy như task cuối phiên của tiến trình ingester (chỉ đọc CH); khi bộ giám sát hợp đồng dựng ở giai đoạn ETL 3b ([market-data-store §7.1](../../../20-design/market-data-store.md) — nơi định nghĩa mức cảnh báo P1/P2/P3 dùng ở đây) thì hợp nhất về đó. **Hai chiều lệch mang nghĩa khác nhau, ngưỡng khác nhau** — vì §5.5 đã chấp nhận mất ~1 s buffer và nguồn rớt kết nối thường xuyên, đẳng thức tuyệt đối sẽ tự vi phạm ngay khi hệ chạy đúng thiết kế (bẫy [CLAUDE.md §4.4.4](../../../../CLAUDE.md)):
   - `Σv > max(AVO)` — **luôn là lỗi** (đếm đôi): cảnh báo **P1** ở mọi mức lệch.
   - `Σv < max(AVO)` — có thể là mất mát đã chấp nhận: dưới 0,1 % ghi metric, **quá 0,1 % thì P2** (ngưỡng hiệu chỉnh lại sau tuần đầu — §10).
   Phép kiểm miễn phí (cột `AVO`/`AVA` đã lưu), và kiểm luôn giả định "`t` không lẫn thoả thuận" (§4.1 luật 1) trên dữ liệu thật mỗi ngày.
8. **Block độc (lỗi tất định, không phải transient):** một giá trị hỏng (tràn Decimal, sai kiểu) làm ClickHouse **từ chối cả block** với lỗi cứng (`ARGUMENT_OUT_OF_BOUND` — đo lượt 3), mà block gom nhiều mã trong 1 giây; retry vô nghĩa vì lỗi lặp y nguyên. Luật: lỗi tất định → **chia đôi block đệ quy để cô lập dòng hỏng**, dòng hỏng ghi log + metric (cảnh báo **P2** — thường là tín hiệu nguồn đổi đơn vị/schema), phần còn lại ghi bình thường. Chỉ lỗi transient (mạng, timeout) mới đi đường retry §5.5.
9. **Quan hệ với Redis — một chiều, không giao nhau:** ingester **chỉ ghi** ClickHouse, không bao giờ đọc; nguồn sự thật của current-state là **Redis HASH** (dựng lại từ `/datafeed/instruments` khi khởi động/reconnect như [market-data-store §3.3](../../../20-design/market-data-store.md), **không** hâm nóng từ ClickHouse). ClickHouse là kho lịch sử cho `api` đọc — hai đường không thay thế nhau.

## 6. Quyền truy cập — thi hành "một người ghi" bằng chính DB

Soi gương **đúng mô hình** role Postgres ([database/README.md](../../../../database/README.md)): migration tạo **ROLE**, user login thật tạo **per-môi-trường, ngoài migration** — mật khẩu không bao giờ vào git.

| Đối tượng | Quyền | Tạo ở đâu | Dùng bởi |
|---|---|---|---|
| ROLE `dlck_ingester` + SETTINGS PROFILE `deduplicate_blocks_in_dependent_materialized_views=1` gắn role (lưới block §5.4, đo T9) | INSERT + SELECT trên `rt.*` | migration | — |
| ROLE `dlck_api` | **chỉ SELECT** trên `rt.*` — không DDL; `SHOW DATABASES` chỉ hiện `rt` *(§12, T10)* | migration | — |
| user login (tên cụ thể chốt ở plan; `ingester_worker`/`api_reader` là ví dụ) | `GRANT <role> TO <user>` | script per-môi-trường, ngoài migration | `ingester` / `api` |
| user quản trị mặc định của image | DDL + `BACKUP` — runner migration và job backup (quyết định #10) dùng; credential từ env container, không in ra log | env của container | migration · backup |

Điều kiện tiên quyết: container phải bật SQL access management qua env `CLICKHOUSE_DEFAULT_ACCESS_MANAGEMENT=1` thì `CREATE ROLE` trong migration mới chạy được *(đo T6: có env này thì tạo được role/user; mặc-định-không-bật là theo tài liệu image, chưa đo mặt phủ định)*.

`etl` **không có user ClickHouse** — nó không có việc gì ở kho realtime ([service-topology §4](../../../20-design/service-topology.md)).

## 7. Hạ tầng — compose profile `realtime`

Đúng chỗ [spec deploy-scaffold §3](../2026-08-24-deploy-scaffold/spec.md) để dành:

- Service `clickhouse` trong `deploy/infra/docker-compose.yml`, **profile `realtime`** — mặc định không chạy.
- ⚠️ **Không đặt `${VAR:?}` bắt buộc cho biến ClickHouse trong compose** — Compose nội suy biến khi **nạp file**, bất kể profile có bật hay không ⇒ `.env` hiện hành thiếu khoá ClickHouse sẽ làm `dev-start`/`docker-up` chết ngay, phá AC1/AC6 của [deploy-scaffold](../2026-08-24-deploy-scaffold/spec.md). Chốt: biến ClickHouse dùng default rỗng trong compose; **fail-fast chuyển vào `scripts/stack.mjs`** — chỉ kiểm khi profile `realtime` được yêu cầu. `.env.example` thêm khối ClickHouse **cùng lượt** (checklist §13).
- Image **pin `clickhouse/clickhouse-server:26.3.22.7` (LTS)** — đúng bản đã chạy toàn bộ phép kiểm §12. Luật: **đổi bản ⇒ chạy lại nguyên bộ §12** trước khi merge (T7 đã cho thấy hành vi phụ thuộc analyzer từng bản).
- Cổng bind `127.0.0.1`: `8123` (HTTP — `clickhouse-connect` dùng) và `9000` (native TCP).
- Named volume `chdata` + healthcheck + các chốt an toàn volume như Postgres/Redis (kiểm sống sau `docker-down` — **thêm `chdata` vào danh sách volume bất biến của `stack.mjs`**, cấm bind-mount data dir).
- `CLICKHOUSE_USER`/`CLICKHOUSE_PASSWORD`, mật khẩu user ứng dụng: qua env, không in giá trị ra log.
- Env `CLICKHOUSE_DEFAULT_ACCESS_MANAGEMENT=1` — bắt buộc để migration tạo được ROLE (§6).
- `ulimits: nofile 262144` cho service *(khuyến nghị của ClickHouse cho image chính thức — chưa kiểm ngưỡng thấp hơn trên máy này)*.
- **Pin `TZ`/`<timezone>` của container = `Asia/Ho_Chi_Minh`** — mọi cột đã khai tz tường minh, nhưng `DEFAULT now64(3)`, literal không tz và output client đều ăn theo tz server; pin để loại cả lớp bẫy [CLAUDE.md §3.1](../../../../CLAUDE.md).
- Entry `ingester` trong `deploy/app/docker-compose.yml` (deploy-scaffold §3 gộp chung profile `realtime`) **không thuộc lượt thực thi spec này** — plan ingester dựng sau; lượt này chỉ thêm service `clickhouse` phía `infra`.
- Cấu hình mem thấp cho máy đơn (`max_server_memory_usage_to_ram_ratio` — khuyến nghị, con số chốt ở plan).
- **TTL cho bảng log hệ thống**: 7 bảng `system.*_log` của image **không có TTL mặc định** và nằm cùng volume `chdata` — `metric_log` tích ~1 dòng/giây, `part_log` phình theo nhịp insert *(đo lượt 3)*; chốt TTL (cỡ 30 ngày) hoặc tắt bảng không dùng qua config server, con số ở plan.
- Ghi chú cho dev: **lát cắt dọc đầu tiên** ([service-topology §7](../../../20-design/service-topology.md)) cần ClickHouse ⇒ dev chạy lát ingester phải bật profile `realtime` tường minh — `dev-start` mặc định không kéo nó lên.
- Thư mục backup của quyết định #10: bind-mount host, **ngoài** volume `chdata`, cấu hình disk `backups` trong config server — chi tiết ở plan.

## 8. Migration — `database/clickhouse/` + runner

```
database/clickhouse/
├── versions/0001_rt_schema.sql        (đánh số 4 chữ số, mỗi file một mục đích)
└── ...
backend/…                              runner: python -m <module> upgrade
```

- Runner Python nhỏ trong backend (dùng env `CLICKHOUSE_URL`): **tự bootstrap** `CREATE DATABASE IF NOT EXISTS rt` + `CREATE TABLE IF NOT EXISTS rt.schema_migrations (version String, applied_at DateTime('Asia/Ho_Chi_Minh')) ENGINE = ReplacingMergeTree ORDER BY version` trước khi đọc `versions/` (giải bài con gà quả trứng — sổ migration nằm trong chính database mà migration tạo). `ReplacingMergeTree` để hai lần ghi cùng version không thành hai dòng *(MergeTree thuần đo được `count()=2` — lượt 3)*; runner đọc sổ bằng `SELECT DISTINCT version`. Bảng này **miễn trừ có chủ đích** quy ước partition tháng của §2 (bảng bé, không thời gian tính). Sau đó: file nào chưa có trong sổ thì thực thi rồi ghi dòng.
- **Idempotent ở mức statement, không chỉ mức file** — vì ClickHouse **không có transaction cho DDL**: file chết ở statement thứ k thì các object 1..k−1 đã tồn tại mà sổ chưa ghi; lần chạy lại phải đi qua được. Luật cứng: **mọi statement trong `versions/` phải idempotent** — `CREATE … IF NOT EXISTS` / `DROP … IF EXISTS` cho DDL tạo/xoá; `GRANT`/`REVOKE` vốn idempotent; `ALTER … MODIFY SETTING` idempotent theo bản chất; statement không đưa được về idempotent (INSERT seed…) thì tự bọc điều kiện tồn tại. Mặt trái phải kiểm: `IF NOT EXISTS` **che drift** (bảng tồn tại với định nghĩa cũ thì bỏ qua im lặng) — seam §9 đối chiếu `system.tables.create_table_query` với bản kỳ vọng, bắt drift chứ không chỉ bắt thiếu.
- **Không có downgrade** (khác Alembic): sửa sai = viết migration tiếp theo. Cùng luật "không sửa file migration đã chạy" của Postgres.
- **Thời điểm chạy migration:** **ngoài giờ giao dịch.** Sửa MV = `DROP` + `CREATE` — khoảng giữa hai statement, INSERT vào bảng nguồn **không sinh nến**, và nguồn không có replay. Buộc phải chạy trong phiên thì dừng ingester trước, chạy xong gom bù phần thiếu từ `trade` theo thủ tục sửa nến §4.1.
- **Hợp đồng khởi động (migration ↔ ingester):** khi boot, ingester đọc `rt.schema_migrations` và yêu cầu **version ≥ bản mà build của nó cần** (cách mã hoá hằng số version trong code chốt ở plan); thiếu (DB chưa migrate, khởi động lạnh) thì **không nối socket, thoát với lỗi rõ** — nối rồi INSERT hỏng là đốt ngân sách retry ~100 s/block rồi vứt frame thật. Trình tự bật profile `realtime` lần đầu: container CH lên + healthcheck → runner migration → script tạo user per-môi-trường (deliverable của plan — §13) → ingester. Thứ tự statement trong migration: `CREATE ROLE` trước `CREATE SETTINGS PROFILE … TO role` (§5.4).
- Một file SQL có thể chứa nhiều statement, tách bằng `;` — quy ước parse và **cách chia file `versions/`** (một `0001` cho cả 12 object hay tách nhóm) chốt ở plan.
- Vị trí chính xác của module runner (trong `backend/core/` hay script riêng) chốt ở plan cùng cấu trúc test (kể cả cách dựng container ClickHouse cho CI — [test-strategy.md](../../../20-design/test-strategy.md) cấm gọi nguồn ngoài nhưng DB test dùng thật).

## 9. Test — seam dự kiến (danh sách chốt lại ở plan, theo §4.5)

Chạy trên **ClickHouse thật** (container test, giống cách test schema Postgres dùng DB thật — [test-strategy.md](../../../20-design/test-strategy.md)); TDD đỏ trước xanh; expected từ nguồn độc lập (bộ tick literal giải tay).

**Phân định sở hữu:** seam **không gắn nhãn** thuộc plan thực thi spec này (schema/migration/quyền/compose — thao tác thẳng ClickHouse bằng SQL test). Ba seam gắn nhãn *"plan ingester"* / *"plan api"* chỉ **ghi trước** ở đây để danh sách seam trọn vẹn — plan tương ứng chốt và thực thi, plan này không viết code cho chúng.

| Seam | Kiểm gì | Case biên tối thiểu |
|---|---|---|
| Runner migration | DB rỗng → `upgrade` → đủ bảng/MV/view; chạy lại lần 2 không đổi gì (idempotent mức file) | file mới thêm được chạy tiếp đúng thứ tự · **file chết giữa chừng rồi chạy lại phải đi qua được** (idempotent mức statement — DDL không transaction) · sau `upgrade`, `create_table_query` của từng bảng khớp bản kỳ vọng (bắt drift bị `IF NOT EXISTS` che) |
| MV nến cổ phiếu | Insert bộ tick literal giải tay → `bar_1m_v` trả đúng o/h/l/c/v/**val**/v_bu/v_sd đã tính tay | hai tick cùng giây khác `seq` (o/c theo thứ tự sở, không theo thứ tự insert) · **hai tick hoà cả `(ts, seq)` khác `received_at` → o/c bất biến trước/sau `OPTIMIZE FINAL`** (khoá total — §4.1) · tick rải hai block insert cùng một phút (state gộp đúng) · phút không tick không có dòng · `side` lạ không vào `v_bu`/`v_sd` nhưng vẫn vào `v` |
| MV nến chỉ số | Chuỗi `index_delta` literal → `index_bar_1m_v` đúng o/h/l/c giải tay | **phút không frame nào mang `TV` → `cum_vol` là NULL, không phải 0** (ngữ nghĩa §4.2) · frame `MI = 0` không sinh nến (guard) |
| Hợp đồng đọc luỹ kế (tầng đọc `api` — ghi trước cho plan api) | Chuỗi hai ngày liên tiếp → khối-lượng-theo-phút không bao giờ âm; phút đầu ngày = chính `cum_vol` | ngày chỉ có NULL không phá carry-forward |
| Dedup block | INSERT lại nguyên block đã ghi **không truyền setting phía client** (chỉ dựa PROFILE của role) → số dòng `trade` không tăng **và** `bar_1m_v` không đếm đôi | block *khác nội dung* nhưng trùng khoá vẫn được ghi (dedup theo hash block, không theo khoá) · dedup còn tác dụng sau restart server |
| Sửa nến (thủ tục §4.1) | `DROP PARTITION` + gom lại từ `trade` (có `insert_deduplication_token`) → `bar_1m_v` khớp giải tay, không đếm đôi | partition khác không bị đụng · **retry backfill cùng token bị nuốt, không token thì nhân đôi** (§12/T13) |
| Backup/restore (quyết định #10) | Backup partition → `DROP PARTITION` → restore (`allow_non_empty_tables=true`) → dữ liệu khớp từng dòng, nến không đếm đôi | ghi trùng tên backup phải bị chặn (luật ghi-mới-xoá-cũ) · file backup của partition đã TTL drop được script dọn |
| TTL — hành vi thật | Chèn dòng `ts` lùi 5 tháng + dòng lùi 1 tháng (hai partition) → `ALTER TABLE … MATERIALIZE TTL` (mutations_sync) → dòng cũ biến mất, dòng mới còn | bảng nến: chèn dòng 2 năm trước, `OPTIMIZE FINAL` → **vẫn còn** (không TTL) · **hai dòng cùng PART, một hết hạn → cả hai còn** (khoá cứng ngữ nghĩa part-level của `ttl_only_drop_parts` — §2) |
| Trường lạ (tầng ánh xạ ingester — ghi trước cho plan ingester) | Frame `i` có trường ngoài danh sách → dòng ghi vào `snapshot_delta` với `extra` chứa đúng trường đó (JSON) | frame không trường lạ → `extra = ''` · khoá lạ trong frame `t`/`o` được đếm/log (không lưu) |
| Quyền | `dlck_api` INSERT bị từ chối, SELECT được; `dlck_ingester` INSERT được | `dlck_api` không `DROP`/`ALTER` được; `SHOW DATABASES` của nó không hiện database nghiệp vụ nào ngoài `rt` |
| Ép kiểu + timezone (thuộc plan ingester, ghi trước) | `"42100.0"` → Decimal đúng; `"215271860.0"` → UInt64 = 215271860 (khối lượng nguồn **lúc có lúc không** đuôi `.0`); `"100.005"` → chuẩn hoá tại cổng, **không** thả cho CH cắt im lặng (§2); `TD`+`FT` giờ VN không lệch ngày, assert `TD == toDate(ts)` | epoch `LS` giây vs `t` ms · giá trị Decimal truyền qua `clickhouse-connect` bằng `decimal.Decimal`/chuỗi, **không** bằng `float` (tránh làm tròn nhị phân) · frame `i` có cả `CV` lẫn `P1` → assert `CV == P1`, lệch thì log (nghi `P1` mang giá thay vì khối lượng) |

## 10. Ước lượng tải và dung lượng

Suy từ mẫu 12 mã / 239 s (đo 10/08/2026 — [11-bvsc-realtime §10](../../../10-sources/market/11-bvsc-realtime.md)), cho phạm vi đăng ký **toàn thị trường** (quyết định #8, ~2.000 mã). **Mẫu đo thiên về mã thanh khoản cao nên KHÔNG suy tuyến tính được** — hai mốc chặn:

| Đại lượng | Ước lượng |
|---|---|
| Chặn dưới (đuôi dài ít giao dịch, hoạt động dồn vào ~200 mã đầu) | ~5–15 triệu dòng/ngày |
| Chặn trên (suy tuyến tính thô 1,14 frame/s/mã × 2.000 mã — chắc chắn cao hơn thực tế) | ~35 triệu dòng/ngày |
| Byte/dòng đã đo trên dữ liệu tổng hợp *(lượt 3, 2026-08-26)* | `trade` 9–21 B · `snapshot_delta` **5 B** (31 cột Nullable thưa nén rất tốt) |
| Dung lượng frame thô — **chủ duy nhất của con số này** | ~50–500 MB/ngày ⇒ **cửa sổ thật 3–4 tháng cỡ 5–60 GB** — dải rộng vì chưa đo dữ liệu thật (`quote`/`pt_match` chưa đo byte/dòng bao giờ); đo trong **tuần đầu chạy** rồi ghi lại vào đây. Chạm đầu cao: TTL rút còn 1–2 tháng là **một lệnh ALTER**, không phải thiết kế lại |
| `bar_1m` + `index_bar_1m` | ~200–540k dòng/ngày. **Đo tổng hợp 2026-08-26** (500k nến/ngày, khoá argMin 3 thành phần): **16 MiB/ngày ⇒ ~4 GB/năm**, trong đó hai state `o`/`c` chiếm ~97% — giá của khoá total-order, trả có ý thức cho tính bất biến của nến. Đo lại trên dữ liệu thật sau một tháng |
| Nhịp insert từ ingester | **1 part/giây/bảng** (5 bảng × flush 1 s) — đúng **trần** khuyến nghị của ClickHouse (≤1 insert/giây mỗi bảng), không phải mức thoải mái: **flush không được nhanh hơn 1 s**. Lưu ý MV làm `bar_1m`/`index_bar_1m` nhận part cùng nhịp với bảng nguồn — tổng 7 bảng nhận part, merge nền phải theo kịp (dự kiến ổn ở quy mô này; theo dõi `system.parts` tuần đầu) |

**Điều kiện tiên quyết trước khi bật ghi thật** (không thuộc danh sách tuần đầu): phiên đo tính chất `SM` trong giờ giao dịch — §4.1.

**Danh sách đo tuần đầu Ingester chạy** (cập nhật lại mục này kèm ngày đo; lệch bậc thì cân nhắc lại TTL/nhịp flush):
1. Dòng/ngày và MB/ngày thật của từng bảng frame; kích thước `bar_1m` sau một tháng.
2. Phút sớm nhất/muộn nhất có frame `idx` và `t` (phạm vi giờ đẩy — hiện chỉ đo 13:08–13:12).
3. `system.parts`: số part active giờ cao điểm — merge có theo kịp nhịp 1 part/giây/bảng không.
4. Tỷ lệ lệch của đối chứng §5.7 khi hệ chạy bình thường — hiệu chỉnh ngưỡng 0,1 %.

## 11. Ngoài phạm vi spec này

*(Cột "Loại" dùng ba loại của [CLAUDE.md §1.4](../../../../CLAUDE.md), cộng một nhãn thứ tư **có chủ đích** — "chưa đo được / chưa kết luận được" — cho mục đã đi tìm nhưng phép đo chưa thể chạy hoặc chưa đủ để kết luận; khác "đã kiểm — không có".)*

| Mục | Loại | Ghi chú |
|---|---|---|
| Tick phái sinh | **chưa đo được** | Cấm giả định cho tới khi đo trong phiên ([roadmap §5.1](../../../00-overview/roadmap.md)); khi đo xong sẽ bổ sung bảng/cột bằng migration mới |
| Topic `pth` | chưa kết luận được | 0 frame qua ~6 phút đo — [11-bvsc-realtime §9](../../../10-sources/market/11-bvsc-realtime.md) ghi hai khả năng, chưa đủ để nói "không có" |
| Code Ingester (socket, ghép delta, standby) | đã có đường khác | Plan dựng ingester riêng, dùng hợp đồng §5 |
| SSE / `api` đọc ClickHouse | đã có đường khác | Thiết kế SSE giữ nguyên [market-data-store §3.4](../../../20-design/market-data-store.md); phần đọc dựng khi làm `api` |
| Chưng cất khối ngoại/breadth dài hạn | loại có chủ đích | Xem §1 — thêm được sau bằng MV, không lấy lại quá khứ |

## 12. Kiểm chứng DDL trên ClickHouse thật *(đo 2026-08-25 → 2026-08-26, ba đợt)*

Chạy trên **ClickHouse 26.3.22.7 (LTS)**, container Docker chính thức — đợt 1 sau review lượt 1 (T1–T7), đợt 2 sau review lượt 2 (T8–T10), đợt 3 sau review lượt 3 (T11–T12, gồm chạy lại T1–T4), đợt 4 sau review lượt 4 (T13–T14, gồm chạy lại T3 và toàn bộ DDL bản cuối). Review lượt 3 và 4 còn tự chạy các bộ phản chứng riêng — kết quả các phép **đúng** của nó (GRANT phủ bảng tạo sau, maxState Nullable ổn định qua FINAL, partition pruning qua view, idempotency từng loại statement, MODIFY SETTING trên bảng có dữ liệu, tràn Decimal lỗi cứng, cắt thập phân im lặng…) ghi rải trong thân spec kèm nhãn *(đo lượt 3)*. Mọi khẳng định "đã kiểm" trong spec trỏ về đây:

| # | Phép kiểm | Kết quả đo |
|---|---|---|
| DDL | Toàn bộ DDL §2–§4 + §8 (8 bảng — 7 ở §3–§4, sổ migration ở §8; 2 MV subquery, 2 view, TTL + settings) | ✅ chạy sạch, `system.tables` đủ 12 object đúng engine |
| T1 | MV nến: 3 tick giải tay (2 block insert, cùng phút) | ✅ `o=100 h=101 l=99 c=99 v=350 val=35150 v_bu=150 v_sd=200` — khớp giải tay tuyệt đối |
| T2 | `side` lạ (`'X'`) | ✅ vào `v`, không vào `v_bu`/`v_sd` |
| T3 | Phút không frame nào mang `TV` — và phút có `TVA` thật | ✅ `cum_vol`/`cum_value` = **NULL** (không phải 0) — ngữ nghĩa §4.2 đứng vững; phút sau có `TVA = 12.000.000,00` đọc ra đúng số qua state `Nullable(Decimal64(2))` (đường ghi không-NULL cũng được phủ; DDL đem kiểm dùng `Decimal64` nhất quán ở cả `index_delta.total_value` lẫn state — đúng bản spec sau sửa lượt 2) |
| T4 | Retry nguyên block (dedup) | ⚠️ Phát hiện quan trọng: dedup window chỉ đặt ở `trade` thì bảng gốc không nhận block trùng **nhưng nến vẫn đếm đôi** (`v=450` thay vì 350). Đủ bộ ba §5.4 (window ở cả `trade` + `bar_1m`, INSERT với `deduplicate_blocks_in_dependent_materialized_views=1`) → ✅ `trade` 1 dòng, `v=100` — nuốt trọn retry |
| T5 | TTL hành vi thật: dòng 5 tháng + dòng 1 tháng, `MATERIALIZE TTL` | ✅ dòng cũ biến mất, dòng mới còn; dòng `bar_1m` của phút cũ **vẫn còn** (không TTL) |
| T6 | `CLICKHOUSE_DEFAULT_ACCESS_MANAGEMENT=1` + `CREATE ROLE`/`GRANT`/`CREATE USER` | ✅ tạo được role/user từ SQL; user gắn `dlck_api`: SELECT được, INSERT và DROP đều bị `ACCESS_DENIED` |
| T7 | Bản MV **gốc** (alias `toStartOfMinute(ts) AS ts` che cột) | Trên 26.3: phân giải về **alias**, ghi đúng 1 dòng/phút — không lỗi. Vẫn giữ dạng subquery vì hành vi này phụ thuộc analyzer, không cam kết đa phiên bản |
| T8 | Dedup qua **restart server**: insert → `docker restart` → retry nguyên block | ✅ `trade` 1 dòng, nến không đếm đôi — cửa sổ hash sống qua restart, kịch bản "CH restart" của §5.4 được phủ thật |
| T9 | SETTINGS PROFILE `deduplicate_blocks_in_dependent_materialized_views=1` gắn role `dlck_ingester`; INSERT bằng user đó **không truyền setting phía client** | ✅ retry bị nuốt trọn (`trade` 1 dòng, `v` không đôi) — dây đai server-side hoạt động, không phụ thuộc kỷ luật code writer |
| T10 | `SHOW DATABASES` của user gắn `dlck_api` (tồn tại database nghiệp vụ khác) | ✅ chỉ hiện `rt` |
| T11 *(2026-08-26, sau sửa lượt 3)* | Chạy lại **toàn bộ DDL bản cuối** (khoá 3 thành phần, dedup window 5 bảng + `bar_1m`, DEFAULT `received_at`, guard `MI>0`, `ReplacingMergeTree` cho sổ migration) + nguyên bộ T1–T4, **không truyền setting dedup phía client** | ✅ T1 khớp giải tay nguyên vẹn (o/h/l/c/v/val/v_bu/v_sd) · T2/T3 như cũ · T4: retry bị nuốt **dù không có client setting** — window của chính `bar_1m` chặn block state trùng hash; ghi nhận: điều kiện (3) của §5.4 trên 26.3 là dây đai, không phải điều kiện sống còn |
| T12 *(2026-08-26)* | Khoá argMin/argMax **total** `(ts, seq, received_at)`: hai tick hoà `(ts,seq)` ở hai block, khác `received_at` → đọc trước/sau 2 lần `OPTIMIZE FINAL` · đo kích thước với 2 triệu tick → 500k nến | ✅ `o`/`c` ổn định tuyệt đối qua merge (khoá cũ 2 thành phần: **đổi giá trị sau merge** — phản chứng lượt 3) · `bar_1m` = 16 MiB/500k nến, `o`+`c` chiếm ~97% |
| T13 *(2026-08-26, sau review lượt 4)* | Thủ tục vá §4.1: DROP PARTITION → backfill `INSERT … SELECT` → retry — không token và có `insert_deduplication_token` cố định | ✅ backfill sau DROP ghi bình thường (nội dung trùng block MV cũ **không** bị window chặn) · ❗ retry **không token: nhân đôi** (`v` 10→20 — `INSERT … SELECT` không được dedup nội dung phủ) · cùng token: retry bị nuốt, `v` giữ 10. Bài học phụ lúc đo: dòng có `ts` ngoài cửa sổ TTL bị **loại ngay tại INSERT** (part toàn dòng hết hạn bị drop) nhưng MV vẫn kịp sinh nến từ block — backfill/ghi muộn quá 3–4 tháng không đưa dữ liệu về `trade` được nữa |
| T14 *(2026-08-26, sau review lượt 4)* | Nến chỉ số khoá total `(event_ts, received_at)`: hai frame `idx` hoà mili-giây, khác `received_at`, hai block → trước/sau `OPTIMIZE FINAL`; chạy lại T3 (ngữ nghĩa NULL) trên DDL mới | ✅ `o=700 c=800` bất biến qua merge (khoá một thành phần: phản chứng lượt 4 đo `o`/`c` **đổi giá trị sau merge**) · T3 nguyên vẹn: phút không `TV` → NULL, phút có → đúng số |
| T15 *(2026-08-26)* | Backup/restore theo partition (quyết định #10): config disk `backups` qua `config.d` → `BACKUP TABLE rt.trade PARTITION '202607'` (tháng đóng) + `'202608'` (tháng mở) → `DROP PARTITION '202607'` → `RESTORE … PARTITION '202607'` | ✅ restore đủ dòng, dữ liệu khớp; cần `SETTINGS allow_non_empty_tables=true` khi bảng còn dữ liệu (thiếu → `CANNOT_RESTORE_TABLE`); ghi trùng tên backup bị chặn `BACKUP_ALREADY_EXISTS` (⇒ luật ghi-tên-mới-xoá-bản-cũ); **RESTORE không kích MV** — nến giữ nguyên, không đếm đôi sau restore `trade` |

Giới hạn của phép kiểm: chạy trên dữ liệu literal vài dòng — **chưa đo tải thật** (tần suất part, merge, RAM); mục §10 vẫn là ước lượng. Guard `index_value > 0` (§4.2) thêm **sau** đợt đo theo review lượt 2 — chỉ là thêm một vị từ WHERE, ngữ nghĩa NULL/không-NULL đã kiểm không đổi; bộ seam §9 sẽ phủ nó chính thức. Kịch bản kiểm lưu ở scratchpad phiên làm việc, sẽ tái lập thành test seam chính thức ở bước plan (§9).

## 13. Checklist quét tài liệu sống khi spec chốt (luật §1.7)

- [ ] `market-data-store.md` — banner: phần realtime (§3.2 điểm 4, §5.3, §5.7 dòng `bar_1m`) được thay bởi spec này; giữ nguyên văn làm lịch sử. Câu chốt phải nói rõ **khoá nến đổi `organ_code` → `symbol` (ticker)**, không chỉ đổi engine. Sửa/banner thêm ba chỗ sẽ thành sai: §1 "Kho ~10 GB" (dòng 18) · §5.7 "Tổng dung lượng dưới 10 GB + ~1 GB/năm nến" (dòng 380) · sơ đồ §2 vẽ ingester ghi "PostgreSQL + TimescaleDB" (dòng 46)
- [ ] `database/README.md` — thêm mục ClickHouse: trạng thái, cách chạy migration + test; **gỡ banner dòng 12** ("chưa cập nhật theo ClickHouse" — sẽ thành sai); thêm một câu phân định **hai role trùng tên `dlck_api`** (Postgres đọc 4 schema ≠ ClickHouse đọc `rt`)
- [ ] `service-topology.md` — §4: thêm nhắc TTL frame thô / nến vĩnh viễn, và **sửa câu "data thị trường crawl lại được nên không cần [backup]"** — không áp dụng cho `bar_1m`/`index_bar_1m` (quyết định #10 của spec này)
- [ ] Điểm nối factor đã đổi hướng so với `step-01 §2` ("ClickHouse cần view hệ số từ market" → nay là **`api` cần**, ClickHouse không phụ thuộc Postgres): ghi câu chốt mới ở tài liệu sống (`market-data-store`/`service-topology`), **không sửa** `step-01` (vùng lịch sử 90-records); nếu cần, một dòng ghi chú ở `database/README.md`
- [ ] `roadmap.md` §5.2 — đánh dấu dòng "Cập nhật market-data-store theo ClickHouse" đã xong, trỏ hồ sơ này
- [ ] `deploy-scaffold` spec/ledger — **không sửa** (vùng lịch sử 90-records); profile `realtime` ghi ở compose thật khi thực thi
- [ ] `.env.example` — thêm khối ClickHouse cùng lượt thực thi (biến default rỗng trong compose, fail-fast ở `stack.mjs` khi bật profile — §7)
- [ ] `scripts/stack.mjs` — thêm **`dlck-infra_chdata`** (tên đầy đủ kèm tiền tố project — tên trần `chdata` không khớp) vào danh sách volume bất biến, **ở cả hai call site hardcode (dòng 127 và 141)**. ⚠️ Guard hiện tại **fail-open**: tên không tồn tại trong `before` thì luôn `ok:true` — smoke test của lần thực thi phải kiểm `existed=true` sau khi bật profile `realtime`, nếu không đăng ký sai tên sẽ câm lặng
- [ ] Script tạo user per-môi-trường cho ClickHouse (§6/§8) — deliverable của plan, chưa tồn tại
- [ ] `git grep` "TimescaleDB\|bar_1m\|hypertable" toàn repo — xác nhận mọi hit còn lại hoặc đã đúng, hoặc thuộc vùng lịch sử
