# 12 — Kiến trúc triển khai dulieuchungkhoan.vn

**Phạm vi:** thiết kế hệ thống thu thập, lưu trữ và phân phối lại dữ liệu từ 44 endpoint REST và 5 topic realtime sang nền tảng dulieuchungkhoan.vn.

**Bối cảnh:** dulieuchungkhoan.vn được phép thu thập, lưu trữ và phái sinh toàn bộ dữ liệu từ nguồn BVSC/FiinTrade, phục vụ khách hàng cuối và một chatbot AI truy vấn không giới hạn.

> ⚠️ **2026-08-24 — [ADR 0007](../00-overview/decisions/0007-monorepo-layout-and-stack.md):** kho realtime đã chốt đổi sang **ClickHouse** (lưu tick thô + sổ lệnh; Postgres giữ dữ liệu REST/BCTC/tin; Redis giữ pub/sub + leader lock). Phiên thiết kế lại **đã xong 2026-08-26** — xem banner thứ ba bên dưới, nơi ghi chính xác phần nào bị thay. Các phần lược đồ TimescaleDB / continuous aggregate / nén-retention bên dưới giữ nguyên văn làm **bối cảnh lịch sử**, không phải lược đồ hiện hành.
>
> 🔴 **2026-08-25 — lược đồ Postgres đã có bản CHÍNH THỨC thay thế §5:** [spec 7 bước](../90-records/plans/2026-08-25-postgres-data-schema/) (đã thực thi — 9 migration trong `database/`, xem [database/README.md](../../database/README.md)). Khác biệt chính so với §5: tách `issuer`/`security` với khoá nội bộ + registry ánh xạ nguồn; **không cột `source` ở bảng dữ liệu** (override mục "làm ngay" của §9.6 — xuất xứ nằm ở registry/staging/ops); ngành theo [bộ riêng 6×24](industry-tree.md) thay ICB; BCTC dùng `length_report`; thêm các miền macro/asset/news/staging/ops. **§5 dưới đây giữ nguyên văn làm bối cảnh thiết kế, không phải DDL hiện hành.**
>
> 🔴 **2026-08-26 — kho realtime đã có bản CHÍNH THỨC thay thế, dùng ClickHouse thay Postgres/TimescaleDB:** [spec ClickHouse realtime store](../90-records/plans/2026-08-25-clickhouse-realtime-store/spec.md) (đã thực thi — schema `rt` với 2 migration, xem [database/README.md](../../database/README.md)). Phần bị thay: **§3.2 bước 4** (batch writer gom nến `bar_1m` — nay ghi ClickHouse, không phải Postgres), **§5.3** (bảng `bar_1m` + continuous aggregate kiểu TimescaleDB), **§5.7 dòng `bar_1m`**. Thay đổi không chỉ là đổi engine lưu trữ: **khoá nến đổi từ `organ_code` sang `symbol` (ticker)** — ClickHouse không có bảng `organization` để tra `organ_code`, danh mục mã vẫn nằm ở Postgres. Nội dung realtime bên dưới **giữ nguyên văn làm bối cảnh lịch sử**, không phải lược đồ hiện hành.

---

## 1. Bốn nguyên tắc

| | |
|---|---|
| **Cách ly hoàn toàn** | dulieuchungkhoan.vn không bao giờ gọi thẳng BVSC/FiinTrade khi phục vụ người dùng. Mọi truy vấn đi qua kho riêng |
| **Lưu đầy đủ** | Kho ~10 GB chứa toàn bộ lịch sử khả dụng *(ước tính này chỉ tính phần Postgres REST/BCTC — chưa gồm tick thô ClickHouse, xem banner đầu trang và §5.7)*. Độc lập nhà cung cấp, chatbot không giới hạn |
| **Giá lưu thô, điều chỉnh lúc đọc** | Không bao giờ sửa quá khứ. Hệ số suy ngược từ chính dữ liệu FiinTrade |
| **Một socket vào, SSE ra** | Ingester tập trung ghép delta, fan-out một chiều qua SSE |
| **Mỗi chỉ tiêu một nguồn chuẩn** | Nhiều nguồn cùng có thì chọn một. Nhóm chỉ tiêu dẫn xuất lẫn nhau thì lấy trọn bộ từ một nguồn, vì trộn nguồn giữa chừng tạo dữ liệu tự mâu thuẫn trong cùng một bảng. Nguồn chuẩn của từng mã trường: [chọn trường cho ETL thị trường](market-field-selection.md) |

### Vì sao cách ly hoàn toàn

Ba lý do, đều đo được:

1. **Độ trễ.** `GetCorporateEarning` 7,4 s · `getPriceData` 3,5 s · `GetScreenerItems` 2,4 s · `GetListOrganization` 4,4 s. Từ PostgreSQL là 1–10 ms — chênh khoảng 1.000 lần. Cache TTL không cứu được lần gọi đầu, mà với 1.974 mã thì đa số truy vấn là lần đầu.
2. **Không có cam kết.** API này không có versioning, không thông báo thay đổi, schema đổi bất cứ lúc nào (xem [00-conventions.md](../10-sources/market/00-conventions.md)). Phụ thuộc trực tiếp là đặt sản phẩm lên nền không kiểm soát được.
3. **Chatbot.** Bot hỏi hàng chục câu mỗi phút. Mỗi câu đi ra FiinTrade sẽ vừa chậm vừa chạm rate limit.

---

## 2. Sơ đồ tổng thể

```
                       ┌──────────────────────────────────────────┐
BVSC / FiinTrade       │                                          │
  44 endpoint REST ────┼──→ ETL Workers (rải lô, rate-limited)     │
                       │         │                                │
  wss://wss.bvsc.com.vn┼──→ Ingester (active + standby)           │
    5 topic            │         │                                │
                       │         ├──→ Redis                        │
                       │         │     ├─ HASH: trạng thái hiện tại│
                       │         │     └─ Pub/Sub: fan-out         │
                       │         │                                │
                       │         └──→ PostgreSQL + TimescaleDB     │
                       │                    (kho đầy đủ)           │
                       └──────────────────┬───────────────────────┘
```

> 🔴 **Nhánh "Ingester → PostgreSQL + TimescaleDB" ở trên đã lỗi thời.** Ingester ghi tick thô/sổ lệnh vào **ClickHouse** (schema `rt`), không phải PostgreSQL/TimescaleDB — xem banner đầu trang. Sơ đồ giữ nguyên văn làm lịch sử.

```
                                          │
                              ┌───────────┴─────────────┐
                              │ dulieuchungkhoan.vn API │
                              ├─ SSE   → realtime       │
                              ├─ REST  → lịch sử, BCTC  │
                              └─ Chatbot AI             │
                                 (function calling)
```

---

## 3. Luồng realtime

### 3.1 Ingester

Một instance chạy, một standby giữ kết nối ấm nhưng không publish. Leader election qua Redis lock, tiếp quản trong **dưới 2 giây**.

```
wss://wss.bvsc.com.vn/market/socket.io/?EIO=3&transport=websocket
    &__sails_io_sdk_version=1.2.1&__sails_io_sdk_platform=browser
    &__sails_io_sdk_language=javascript
```

Topic đăng ký:

| Topic | Nội dung |
|---|---|
| `i:<mã>` | Snapshot delta — 34 trường |
| **`o10:<mã>`** | Sổ lệnh 3 bậc |
| `t:<mã>` | Từng lệnh khớp, có chiều BU/SD |
| `idx:<chỉ số>` | 15 mã chỉ số |
| `ptm:<sàn>` | Thoả thuận đã khớp |

> 🔴 **Phải dùng `o10:`, không phải `o:`.** Topic `o:` được server chấp nhận và trả ack `statusCode: 200` nhưng không bao giờ đẩy dữ liệu. Xem [11-bvsc-realtime.md](../10-sources/market/11-bvsc-realtime.md).

### 3.2 Xử lý trong Ingester

```
1. Ghép delta      → dựng state đầy đủ mỗi mã (i và idx chỉ gửi trường thay đổi)
2. Ép kiểu         → o, t, idx trả số dưới dạng CHUỖI
3. Ghi Redis       → HASH state + PUBLISH kênh fan-out   ← ưu tiên, trong hot path
4. Đẩy hàng đợi    → batch writer gom nến 1 phút, COPY mỗi 1–2 giây  ← ngoài hot path
```

> 🔴 **Bước 4 đã lỗi thời.** Batch writer ghi nến `bar_1m` vào **ClickHouse** (schema `rt`), không phải Postgres qua `COPY` — xem banner đầu trang. Nguyên tắc "không ghi database trong hot path" vẫn đúng.

**Không ghi database trong hot path.** Ghi đồng bộ cộng thêm 5–20 ms vào mọi frame.

### 3.3 Xử lý mất kết nối

Đo được **2 lần rớt trong 4 phút** vận hành liên tục. Quy trình bắt buộc:

```
onclose → chờ 3–5 s → nối lại
        → đăng ký lại TOÀN BỘ topic      (server không nhớ trạng thái đăng ký)
        → gọi /datafeed/instruments      (đồng bộ lại state, vì delta đã mất)
```

⚠️ **Khoảng thời gian Ingester chết là mất vĩnh viễn** — API không có endpoint replay. Đây là lý do bắt buộc phải có standby.

### 3.4 Phân phối SSE

Dữ liệu thị trường chảy một chiều từ sàn tới màn hình. SSE đủ dùng và đơn giản hơn WebSocket: không cần sticky session, trình duyệt tự lo việc nối lại qua `Last-Event-ID`.

| Hạng mục | Cấu hình |
|---|---|
| Giao thức | **HTTP/2 bắt buộc** |
| Khởi tạo | Client tải **snapshot đầy đủ** qua REST, sau đó chỉ nhận **delta** qua SSE |
| Gộp frame | **250 ms** mặc định · **100 ms** cho mã đang mở chi tiết |
| Lọc | Mỗi kết nối chỉ nhận mã trên màn hình người dùng |
| Fan-out đa instance | Redis Pub/Sub |

> 🔴 **HTTP/1.1 giới hạn 6 kết nối đồng thời mỗi domain.** SSE giữ 1 kết nối mở → người dùng mở 6 tab là treo. HTTP/2 multiplexing giải quyết triệt để.

Cấu hình Nginx bắt buộc — thiếu là độ trễ nhảy lên hàng giây:

```nginx
proxy_buffering off;
proxy_read_timeout 24h;
add_header X-Accel-Buffering no;
```

### 3.5 Vì sao gộp frame 250 ms

Đo được **2–2,5 frame/giây mỗi mã hoạt động mạnh**. Bảng 50 mã ≈ **100 frame/giây**. Mắt người không phân biệt được dưới 200 ms, nên gộp về 4 gói/giây — **giảm khoảng 10 lần lưu lượng** mà trải nghiệm không đổi.

Giữ nguyên mô hình delta tới tận trình duyệt: đo được `V1` (khối lượng mua bậc 1) đổi 292 lần trong khi `FB` (khối ngoại mua) chỉ đổi 16 lần trên cùng 843 frame. Đẩy đủ 34 trường mỗi lần là lãng phí.

### 3.6 Ngân sách độ trễ

| Chặng | Mục tiêu |
|---|---|
| BVSC → Ingester | 1–5 ms |
| Parse + ghép delta | < 1 ms |
| Redis publish | < 1 ms |
| Fan-out SSE | < 5 ms |
| Gộp frame | 0–250 ms |
| **Tổng cộng thêm** | **~10 ms + chu kỳ gộp** |


### 3.7 Hợp đồng ghi ClickHouse — mất một dòng hay mất năm nghìn dòng

*(Viết vào tài liệu sống 2026-08-26 theo §1.1: trước đó hợp đồng này chỉ nằm trong spec ở `90-records/` và trong comment code — xoá thư mục kế hoạch là mất luôn tri thức vận hành.)*

Batch writer gom dòng rồi xả mỗi giây. Khi một lô ghi hỏng, **cách phân loại lỗi quyết định mất bao nhiêu dữ liệu**:

| Loại lỗi | Xử lý | Thiệt hại |
|---|---|---|
| **Dữ liệu** (dòng sai kiểu, tràn số) | Chia đôi lô đệ quy để cô lập | **1 dòng** |
| **Mọi lỗi khác** (mạng, quá tải, cấu hình) | Thử lại nguyên lô tới hạn chót, hết hạn thì bỏ | tới **5.000 dòng** ≈ 1 giây tick |

Bốn luật rút ra từ những lần trả giá, mỗi luật chống một chiều hỏng khác nhau:

1. **Phân loại theo MÃ SỐ lỗi, không theo chuỗi trong thông điệp.** ClickHouse đặt mã ở **header HTTP** nên nó luôn có; còn tên ký hiệu và phần chi tiết nằm trong **body**, và biến mất sạch khi server tắt `show_clickhouse_errors` — lúc đó thông điệp rút gọn thành một câu chung chung không còn dấu vết gì. Dò chuỗi vì thế hỏng đúng lúc cần nhất.

2. **Mã lạ ⇒ coi là transient**, không phải ngược lại. Hai chiều sai không cân nhau: đọc nhầm lỗi dữ liệu thành transient chỉ mất một lô sau một khoảng có hạn, còn đọc nhầm **quá tải** thành lỗi dữ liệu sẽ chia đôi đệ quy thành 5.000 lệnh ghi một dòng — giáng thẳng vào đúng cái server đang ngộp. Vì vậy danh sách mã dữ liệu là **danh sách đóng**, mọi thứ ngoài nó đi nhánh có hạn.

3. **Ngân sách thử lại phải đo THỜI GIAN THỰC và là HẠN CHÓT CHUNG cho cả cây chia đôi.** Hai bẫy đã cắn thật:
   - Đếm bằng tổng thời gian *ngủ* thì thời gian nằm trong lệnh ghi không vào sổ. Driver mặc định chờ đọc **300 giây**, nên một server treo cho ra **40 phút** thực trong khi bộ đếm mới tới 63 giây.
   - Truyền xuống đệ quy một *khoảng* thay vì một *hạn chót* thì mỗi tầng chia đôi được cấp lại trọn ngân sách — đo được **778 giây cho một lần xả**.

   🔴 **Viết lại 2026-08-27** *(lát [tràn-ra-đĩa](../90-records/plans/2026-08-28-ingester-spill-to-disk/spec.md) §7/§9, đo thật trên ClickHouse 26.3.22.7)*: câu ràng buộc trước đây ở đây — *"ngân sách phải nhỏ hơn cửa sổ chống trùng của ClickHouse (~100 giây)"* — **sai đơn vị**. `non_replicated_deduplication_window = 100` (DDL `0002_rt_schema.sql`) đếm **100 BLOCK gần nhất mỗi bảng**, không đếm giây — biến thể tính theo thời gian không có tác dụng quan sát được (probe: chờ 130 s không chen block khác, lô cũ vẫn bị nuốt y như chờ 0 s; chen 105 block cùng bảng dù chỉ vài giây thì lô cũ đã ra khỏi cửa sổ). "~100 giây" chỉ đúng tình cờ ở nhịp đúng 1 block/giây; khi phát lại bắn nhiều block một nhịp, cửa sổ tính theo đồng hồ **co lại** còn vài giây — mỏng nhất đúng lúc cần nó nhất.

   Ràng buộc `RETRY_BUDGET_S = 60 < 100 block` (không phải `< 100 giây`) vẫn đúng nguyên vẹn cho **chế độ RAM không có lưới đĩa** (đường `no_spill_dropped` — `spill` là `None` hoặc thư mục spill chưa giành được khoá): cạn ngân sách ở đó vẫn phải **bỏ** block, không có đĩa để giữ. Nhưng **có lưới đĩa thì luật đảo** — quyết định #4 đầu spec spill (không mở lại): cạn ngân sách retry không còn là bỏ — block ghi xuống đĩa dạng `-r` (nguyên văn, giữ nguyên hash để lưới dedup còn cơ hội bắt), tiến trình chuyển hẳn sang **chế độ đĩa** (tóm tắt hợp đồng ngay dưới). Ack thất lạc sau đó phát lại trùng là **kết quả mong đợi, không phải sự cố** — trùng có dấu vết qua bộ đếm `d[]` khi đối chứng cuối phiên, mất thì không có gì lần ra. Luật *"đếm đôi tệ hơn mất dòng"* vì vậy không còn tuyệt đối: nó vẫn đúng cho chế độ RAM, nhưng bị **đảo** trong chế độ đĩa.

4. 🔴 **Viết lại 2026-08-27:** ngân sách xả cuối phiên **không còn suy ra từ `RETRY_BUDGET_S`**. Căn cứ cũ mất hiệu lực vì cạn ngân sách retry giờ chuyển sang chế độ đĩa (luật 3), không còn bỏ block — "chờ đủ để một lần retry cũ tự thoát" không còn là kịch bản xấu nhất cần phòng. Kịch bản xấu nhất bây giờ là **xả một hàng đợi đo bằng GiB**. Cơ chế mới (`drain_writer` trong `backend/ingester/main.py`, spec spill §5):

   - **Đĩa rỗng (hoặc không dùng đĩa):** ngân sách **75 giây** — đủ để thread ghi cũ còn kẹt trong một nhịp retry transient tự thoát (`_write_lock` làm lời gọi mới về ngay, không giẫm lên nó); vòng dưới quay lại tới khi `writer.clean()`.
   - **Còn nợ đĩa** (`disk_mode` đang bật, hoặc `SpillStore` mình đã giành khoá mà chưa rỗng): **trần cứng 10 phút** (`DRAIN_HARD_CAP_S = 600`).
   - Hết ngân sách mà đĩa còn file → **để lại, không vứt** — log cấu trúc "còn X block / Y byte", `drained = False`, cảnh báo *"PHÁN QUYẾT KHÔNG ĐÁNG TIN"* **giữ nguyên** (nó đang nói đúng sự thật), exit code khác 0 như cũ. Sáng hôm sau lúc khởi động, `replay_debt()` xả nốt nợ **trước khi vào phiên** rồi tự chạy lại `reconcile --date <ngày nợ>` cho đúng ngày đó — trong đường khởi động, không chờ tay (spec spill §5 mục 3).

**Chế độ đĩa — tóm tắt hợp đồng ghi khi RAM chạm trần** *(thiết kế đầy đủ: [spec tràn-ra-đĩa §2–§4](../90-records/plans/2026-08-28-ingester-spill-to-disk/spec.md); code: `backend/ingester/chwriter.py` + `spill.py`)*:

- **Hai cửa vào chế độ đĩa:** (1) tổng dòng trong hàng đợi RAM vượt trần `N_CAP_ROWS`; (2) một block cạn ngân sách retry ở luật 3 trên.
- **FIFO toàn cục:** đầu RAM (cũ nhất) xả trước, rồi tới đĩa theo thứ tự tên file (`seq` zero-pad, bền qua restart — khởi tạo lại từ max `seq` quét được trên đĩa, không đè file cũ).
- **Trần K mỗi nhịp phát lại:** `K_REPLAY_ROWS` là trần TỔNG số dòng insert của MỘT lần gọi vòng ghi, tính cả phần lấy từ đầu RAM — không có nhịp "xả dồn" khi ClickHouse vừa gượng dậy.
- **Hai loại file:** `-r` (đã từng gửi, sinh từ cửa 2) phát lại **nguyên văn, không gộp** — giữ hash cho lưới dedup; `-n` (cắt mới trong chế độ đĩa, chưa từng gửi) được **gộp** các file liền kề cùng bảng tới `BLOCK_CAP` dòng một insert khi phát lại.
- **Không drop theo thời gian** trong chế độ đĩa — block chỉ rời hàng đợi khi insert thành công hoặc dòng độc đã cô lập. Chạm **trần đĩa** (`SPILL_CAP_BYTES`) mới bỏ, và chỉ bỏ **block mới đến** (`spill_drop_newest.<bảng>`, có sổ sách log cấu trúc theo bảng — spec §6); hàng đợi đã ghi trên đĩa giữ nguyên.

**Giá của một dòng trùng — đọc P1 đầu tiên sau ngày phát lại cho đúng.** Đổi "thà trùng hơn mất" lấy một cái giá có thật và **vĩnh viễn**: một dòng `rt.trade` phát lại trùng làm phồng tổng khối lượng trong `rt.bar_1m` mãi mãi. Nến khoá theo giá trị cột nên OHLC là **idempotent** (ghi lại cùng giá trị, kết quả không đổi), nhưng tổng thì **không** — `AggregatingMergeTree` cộng dồn `sumState`, nên dòng thứ hai cộng thêm lần nữa và không có gì trừ lại. Triệu chứng: nó nổi lên đúng dạng **P1 (đếm đôi)** ở đối chứng cuối phiên. Vì vậy **P1 ĐẦU TIÊN sau một ngày có phát lại nợ đĩa phải đọc là "trùng đã lường trước, khối lượng nến phồng"**, không phải "dữ liệu hỏng" — phân biệt bằng `replay_rows` của ngày đó (spec spill §7 cho cửa sổ dedup và vì sao lưới của ClickHouse có thể trượt).

> 🔗 **Phụ thuộc ngầm phải nhớ:** danh sách mã lỗi dữ liệu đủ dùng **vì** các bảng `rt.*` hiện chỉ dùng `String` · `UInt*` · `Decimal64(2)` · `DateTime*`. **Thêm cột kiểu `UUID`, `Float`, `IPv4/6` thì phải rà lại danh sách** — không có gì tự báo, triệu chứng sẽ là những lô bị bỏ mà không rõ vì sao.

**Trần chờ đọc phải tách riêng cho ghi và cho đọc.** Trần hợp lý cho một lệnh ghi (giây) quá ngắn cho truy vấn đối chứng cuối phiên (quét trọn ngày) — dùng chung một trần sẽ biến một phiên sạch thành phiên báo lỗi dù dữ liệu đã vào đủ.

---

## 4. ETL REST

> **2026-08-26 — job đầu tiên của nhóm này đã chạy thật:** `python -m etl refdata` (danh bạ + danh mục mã + cây ICB), 08:00 ngày làm việc, trước ingester 08:30. Hợp nhất `/quotes` + `indexsnaps` + 2 endpoint FiinTrade; chốt chặn sụt hai tầng (mốc = `ops.etl_run.stats` lượt success gần nhất — KHÔNG dùng `contract_snapshot`, bảng đó thuộc bộ giám sát hợp đồng); bằng chứng khi từ chối vào `staging.raw_payload` (`refdata:*`) trong giao dịch riêng — ngoại lệ hẹp có chủ đích so với luật "danh bạ không vào staging". Thiết kế: [spec](../90-records/plans/2026-08-26-reference-data-etl/spec.md).

### 4.1 Lịch chạy

| Nhóm | Nhịp | Số lời gọi |
|---|---|---|
| Danh bạ, ngành ICB, `/quotes`, `/mapping` | Trước phiên | 4 |
| `getPriceData` Page 1 | Sau 15:00 | 1.974 |
| **Họ Snapshot — KHÔNG chạy hằng ngày** *(chốt 2026-09-03, xem §4.1b)*: `snapshot` `valuation` `ownership` `dividend`; hai kind chấm điểm đã bỏ khỏi lược đồ (migration `0015`) | **Kích hoạt theo sự kiện + quét sàn định kỳ** | **≈ 200–260** |
| `GetScreenerItems` — **lưu 80/193 trường** (ước lượng 2026-08-14; đếm 2026-09-03: **75/193** — 66 khoá đặt tên từ response thật, trừ 4 nhãn xếp hạng và 2 dòng KQKD trùng BCTC) *(gửi 1 tiêu chí, nhiều hơn sẽ timeout)* — **lát 1 XONG 2026-09-03: `etl screener` 15:20 — chạy thật sau phiên, 1.541 dòng/ngày, 52 trang ~30–70 s** ([spec](../90-records/plans/2026-09-03-screener-daily-etl/spec.md) · [ledger](../90-records/plans/2026-09-03-screener-daily-etl/ledger.md)) | Sau 15:00 | 52 |
| Lịch sự kiện *(tải TRỌN sáu họ `GetCorporate*` — đo 2026-09-03: `FromDate` không dùng được, mỗi họ lọc theo một trục ngày khác nhau và `Earning` lọc theo trường không có trong response; [`08-fiin-event-calendar.md`](../10-sources/market/08-fiin-event-calendar.md))* | Hằng ngày | 9 |
| BCTC + PDF | **Kích hoạt** theo `GetCorporateEarning` | ~100–300/quý |
| Re-crawl giá một mã | **Kích hoạt** theo sự kiện quyền của mã đó | tuỳ |

**Hằng ngày ≈ 1.850 lời gọi** *(4 danh bạ + **1.523** giá + 52 Screener + 9 lịch sự kiện + ~200–260 họ Snapshot; sửa 2026-09-04 — số 1.974 cũ đếm trước lượt dọn 442 mã huỷ niêm yết)* — **thấp hơn con số ~6.000 của bản 2026-08-14**, vì họ Snapshot chuyển từ chạy-mọi-mã-mỗi-ngày sang kích hoạt theo sự kiện.

### 4.1b Vì sao họ Snapshot không chạy hằng ngày — chốt 2026-09-03

Soi nội dung thật cả 6 endpoint và **18 trường ta thật sự lưu** cho thấy: **không trường nào đổi theo ngày.** Các trường đổi theo giá (`rtd11` vốn hoá · `rtd14` EPS · `rtd21` P/E · `rtd25` P/B) đã cố ý **không lấy** từ Snapshot vì Screener có rồi trong 52 lời gọi. Phần còn lại chia đúng ba nguồn thay đổi, và `quarter`/`year` nằm ngay trong tập lưu — nguồn tự đóng dấu kỳ:

| Nhóm trường | Đổi khi | Kích hoạt bằng |
|---|---|---|
| `rtq10` `rtq44` `rqq41` `rtq137` `quarter` `year` | ra báo cáo quý | `getCorporateEarning` |
| `outstandingShare` `freeFloat` | phát hành thêm CP | `getCorporateShareIssuance` |
| `foreignerVolumn` `statePercentage` `stateVolumn` `majorHoldings` `totalForeignRoom` `maximumForeignPercentage` | có công bố sở hữu | **không có loại sự kiện nào** — dùng Screener làm máy dò (`corpOwnership` · `organizationOwnership` · `freeFloatRate` có hằng ngày) |
| `ceo` `comTypeCode` `valuePerShare` `competitors` | hiếm | quét sàn |

🔴 **Chỉ trigger là KHÔNG đủ — lịch sự kiện có sót, đã đo.** Độ phủ đo 2026-09-03 ([`08-fiin-event-calendar.md`](../10-sources/market/08-fiin-event-calendar.md)): `ShareIssuance` 100 % · `Earning` 96,4 % *(mọi chỗ sót ≤ 2022, từ 2023 tới nay sạch)* · `CashDividend` 98,6 % **và có một chỗ sót ở vùng gần đây** (SSI, đợt 2026-08). Nên kiến trúc là **hai lớp**:

```
lịch sự kiện (9 lời gọi/ngày)    →  kích hoạt fetch ngay        ← đường nhanh, bắt ~96–100 %
quét sàn định kỳ toàn bộ         →  bắt phần lịch bỏ sót        ← lưới, và là THƯỚC ĐO
```

| Kind | Trigger | Nhịp quét sàn | Vì sao nhịp đó |
|---|---|---|---|
| `snapshot` | `Earning` + `ShareIssuance` | **quý** | feed gần đây sạch 100 %/96,4 %; sàn chỉ để phòng |
| `dividend` | `CashDividend` + `StockDividend` | **tháng** | có sót ở vùng gần đây ⇒ sàn phải dày hơn |
| `ownership` | *(không có sự kiện)* — Screener dò tỷ lệ | **tháng** | chỉ có máy dò gián tiếp |
| `valuation` | *(không có sự kiện)* — dự phóng đổi khi phân tích viên cập nhật | **tháng** | `riskFreeRate` khác nhau giữa các mã ⇒ mỗi mã được cập nhật vào lúc khác nhau |

**Quét sàn vừa là lưới vừa là thước đo:** mỗi lần nó tìm ra thay đổi mà trigger không bắn = **một lỗ của lịch, đếm được**. Sau vài tháng có số thật thì siết hay nới nhịp bằng dữ liệu, không bằng cảm giác. Đây là việc của [§7.1 giám sát hợp đồng dữ liệu](#71-giám-sát-hợp-đồng-dữ-liệu).

⚠️ **Ràng buộc thứ tự:** kiến trúc này đòi **lát lịch sự kiện chạy TRƯỚC lát Snapshot**. Lịch chỉ 9 lời gọi/ngày — rẻ nhất cả nhóm — mà mở khoá cho Snapshot, BCTC và re-crawl giá.

### 4.2 Backfill một lần

| Việc | Lời gọi | Thời gian |
|---|---|---|
| `getPriceData` mọi trang × **1.523** cổ phiếu niêm yết *(đo 2026-09-03 — số 1.974 cũ đếm trước lượt dọn 442 mã huỷ niêm yết; độ sâu mỗi mã theo tuổi niêm yết: BID 53 trang, TD6 6 trang)* | **~50.000–80.000** | **tuần tự**, ~25–40 giờ, rải vài đêm bằng `python -m etl price --backfill --max-minutes N` — con trỏ trong `ops.etl_run.stats.cursor` nên lượt sau đi tiếp từ mã kế, không làm lại ([spec lát 3 §5.5e](../90-records/plans/2026-09-03-price-daily-etl/spec.md)) |
| BCTC 3 loại × 1.974 mã | 5.922 | ~25 phút |
| Lịch sự kiện toàn bộ | 9 | ~2,5 phút |

*(đo 2026-09-03)* Lịch sự kiện tải TRỌN sáu họ mỗi lượt — **backfill và job hằng ngày nay là cùng một đường code** (`python -m etl events`), khác nhau đúng một cờ: `--accept-new` mở khoá lượt tạo nhiều issuer tối thiểu (517 ở lượt đầu), lượt hằng ngày sau đó chạy không cờ vì gần như không còn issuer mới. Xem [`08-fiin-event-calendar.md`](../10-sources/market/08-fiin-event-calendar.md).

⚠️ Giới hạn **2 request/giây** *(cài thành giãn cách ≥ 0,5 s giữa hai lần bắt đầu lời gọi trong `price_fetch`; với latency trung vị 1,76 s bộ giãn cách hầu như không phải ngủ)*, chạy ngoài giờ giao dịch, **rải nhiều đêm**. Quét ồ ạt hàng chục nghìn lời gọi là mức tải đáng kể lên hạ tầng FiinGroup.

### 4.3 Rate limiter

Token bucket riêng cho từng host FiinTrade. ETL và chatbot **dùng chung ngân sách** — nếu không, quét đêm sẽ làm chatbot ban ngày bị chặn.

Đo 2026-08-15 bằng đúng tải kế hoạch: burst Screener 52 trang chạy tuần tự (~29 request/phút) **không gặp tín hiệu chặn nào**, và **không có header hạn mức** để dựa vào — xem [§10 quy ước chung](../10-sources/market/00-conventions.md). Ngưỡng trần thì vẫn chưa biết, và **cố tình không dò**. Vì vậy token bucket phải tự giữ nhịp, và **nhịp 8 luồng ở §4.1 chưa được kiểm** — đo lại ở đúng nhịp đó trước khi bật chạy thật.

**Chốt 2026-09-04 — lát giá chạy TUẦN TỰ, chưa cần token bucket dùng chung** *(quyết định §4.8 ở [spec lát 3 §4.1](../90-records/plans/2026-09-03-price-daily-etl/spec.md))*: nhu cầu 8 luồng biến mất khi ngân sách ngày còn 1.523 lời gọi (~45 phút tuần tự); backfill rải nhiều đêm. Bộ giãn cách nằm trong `price_fetch` vì chưa có người dùng thứ hai. **Đảo ngược khi** `api` bắt đầu gọi FiinTrade (cần ngân sách chung ⇒ tách `core/http`) hoặc backfill thật đo được > 60 giờ.

### 4.4 Luật huỷ niêm yết trong danh mục mã

Danh mục mã hợp nhất hai nguồn lệch nhau: bảng giá `/quotes` của BVSC **giữ lại dòng cũ**, còn danh bạ doanh nghiệp `GetListOrganization` của FiinTrade thì **không**. Hai chiều vắng mặt vì vậy mang hai ý nghĩa khác nhau, và job `etl refdata` hiện chỉ bắt một chiều:

| Chiều vắng mặt | Ý nghĩa | Job hiện xử lý |
|---|---|---|
| Có trong danh bạ, vắng khỏi bảng giá | Đã rời sàn | ✅ Lật `delisted` — hai đường lật, cả đường "vắng hẳn" lẫn đường "có trong đích với `status='delisted'`" |
| **Có trong bảng giá, vắng khỏi danh bạ** | **Cũng đã rời sàn** | ✅ **Đã cài 2026-08-28** — cột dấu `directory_absent_since` + ngưỡng ân hạn, xem dưới |

🔴 **Hệ quả đo được 2026-08-28:** **438 cổ phiếu** không có doanh nghiệp tương ứng vẫn mang nhãn `listed` — UPCOM 378 · HNX 39 · HOSE 21. Kiểm bằng danh tính chứ không bằng cờ: trong đó có **Habubank** (sáp nhập SHB từ **2012**), Bibica, Đường Biên Hoà, Tường An, PVFinance, Chứng khoán Kim Long — **không mã nào còn giao dịch**. Cờ `status` gần như trống thông tin: toàn kho 2.015 mã chỉ có **4 dòng `delisted`**, nên không dùng nó để kiểm giả thuyết được.

Ảnh hưởng mọi thống kê *"mã đang niêm yết"*, và ảnh hưởng thẳng vào [ETL giá §4.1](#41-lịch-chạy): vòng lặp `getPriceData` đi trên tập `listed` sẽ gọi API cho **438 mã chết mỗi ngày** — 22% tập cổ phiếu.

**Ba ràng buộc phải tôn trọng khi cài luật này:**

1. **Chỉ áp cho `security_type = 'stock'`.** ETF (10 mã) và chỉ số (18 mã) không có doanh nghiệp phát hành — với chúng "không có issuer" là trạng thái bình thường vĩnh viễn, không phải tín hiệu gì. Chứng chỉ quỹ đóng thì khác: chúng **có** issuer `com_type_code='QU'` nên không rơi vào diện này.
2. **Chốt chặn sụt sẽ từ chối lượt dọn đầu tiên.** `refdata_guard` đặt `DELIST_RATIO = 0.01` — lật quá 1% số mã đang niêm yết là chặn trọn lượt. 438/1.962 = **22%**, gấp 22 lần ngưỡng. Lượt dọn đầu phải chạy tay một lần với `--accept-drop`; từ đó về sau mỗi ngày chỉ còn lác đác vài mã, nằm dưới ngưỡng.
3. **Vắng mặt một lượt chưa chắc là chết.** Một mã **mới niêm yết** có thể xuất hiện ở bảng giá BVSC trước khi vào danh bạ FiinTrade — luật thô sẽ đánh `delisted` cho mã vừa lên sàn. ✅ **Đã giải bằng ngưỡng ân hạn 3 ngày**, xem cơ chế dưới.

**Làm cùng lát nào:** gộp với lát **mở rộng danh mục — phái sinh + `/datafeed/instruments`**. Ba việc đó sửa đúng cùng ba đoạn: `refdata_merge` (trạng thái đích) · `plan_delist` (ai bị lật) · `refdata_guard` (ngưỡng). Làm rời là ba lần đụng đoạn code nguy hiểm nhất của job và ba lần chỉnh lại ngưỡng chốt chặn. Nhưng **phải xong trước ETL giá** — nếu không, ETL giá xây trên một tập niêm yết mà 22% là mã ma. ✅ **Đã xong trước lát giá:** lượt dọn `--accept-drop` chạy 2026-09-03 06:49 UTC (run 62, `delisted: 439`); tập `listed` còn **1.523** cổ phiếu và `etl price` đi trên đúng tập đó.

### Cơ chế đã cài — 2026-08-28

Cột **`market.security.directory_absent_since timestamptz`** *(migration `0014`)*. `NULL` = mã đang có mặt trong danh bạ.

| Ai | Làm gì |
|---|---|
| `apply()` | **Đóng dấu** `now()` cho cổ phiếu `listed` không có `issuer_id` mà **chưa** mang dấu · **gỡ dấu** khi mã quay lại danh bạ. Trả `directory_absent_marked` / `directory_absent_cleared` |
| `plan_delist()` | Chọn mã mang dấu **cũ hơn `DIRECTORY_ABSENT_DAYS = 3`** làm ứng viên lật, cộng vào `flips` để chốt chặn nhìn thấy |

🔴 **Thứ tự chạy là phần dễ sai nhất.** Job gọi `plan_delist` → `guard.check` → `apply`, nên `plan_delist` **chỉ đọc dấu do các lượt TRƯỚC đóng**. Nếu đóng dấu rồi lật ngay trong cùng một lượt thì ngưỡng ân hạn thành vô nghĩa.

**Ngưỡng đếm bằng NGÀY LỊCH, không phải số lượt job** *(chốt 2026-08-28, chủ dự án)*. `etl refdata` là job REST nên ngày lễ vẫn quan sát bình thường ⇒ mọi ngày Thứ 2–6 đều có một lượt thật. Hở duy nhất là **cuối tuần**: dấu đóng thứ 6 thì lượt thứ 2 đã thoả, tức lật sau **2 lượt** thay vì 4 như ca giữa tuần. Chấp nhận vì chốt chặn 1% vẫn chặn mọi lượt lật hàng loạt.

**Nghiệm thu trên DB thật 2026-08-28 19:41** — hai lượt job liên tiếp, cả hai `exit 0`:

| Phép kiểm | Kết quả |
|---|---|
| Lượt 1 · `directory_absent_marked` | **438** |
| Lượt 2 · `directory_absent_marked` | **0** *(đóng dấu một lần rồi thôi)* |
| `delisted` cả hai lượt | **0** *(ngưỡng chưa tới — đúng)* |
| A · số mã mang dấu | **438** |
| B · dấu đặt sai loại (`security_type <> 'stock'`) | **0** |
| C · không issuer mà chưa mang dấu | **0** |
| D · tổng `delisted` | **4** *(không đổi so với trước)* |
| Số mốc thời gian khác nhau | **1** — chứng minh lượt hai không dời dấu, bằng dữ liệu chứ không bằng counter |

🔴 **Việc còn lại là một lượt dọn TAY, và nó sẽ làm job báo đỏ trước.** Dấu đóng lúc **2026-08-28 19:41**, nên ngưỡng 3 ngày thoả lúc **31/08 19:41** — sau mốc chạy 08:00 của thứ 2. **Lượt job đầu tiên nhìn thấy 438 ứng viên là thứ 3 2026-09-01, 08:00.** Lượt đó chốt chặn `DELIST_RATIO = 0.01` sẽ **từ chối** (438/1.962 = 22,3%): job báo `failed` và **không ghi gì** — đó là hành vi đúng, không phải sự cố. Muốn dọn thì chạy tay, có người nhìn:

```bash
cd backend && uv run python -m etl refdata --accept-drop
```

Sau lượt dọn đó, mỗi ngày chỉ còn lác đác vài mã, nằm dưới ngưỡng, job tự chạy lại bình thường.

---

## 5. Lược đồ dữ liệu

### 5.1 Bảng tham chiếu

```sql
CREATE TABLE organization (
  organ_code        text PRIMARY KEY,
  ticker            text NOT NULL,
  com_group_code    text,          -- VNINDEX | HNXIndex | UpcomIndex
  icb_code          text,
  com_type_code     text,          -- NH | CT | CK | BH | QU
  organ_name        text,
  organ_short_name  text,
  updated_at        timestamptz DEFAULT now()
);
CREATE INDEX ON organization (ticker);
```

> `com_type_code` quyết định gọi `GetSnapshot` (khi `NH`) hay `GetSnapshotNoneBank` (còn lại). Chọn sai làm ~46% trường thành `null` mà API vẫn báo thành công.

> `organ_code` là **khoá chính**, `ticker` chỉ là thuộc tính hiển thị. 41% doanh nghiệp có hai giá trị này khác nhau.

```sql
CREATE TABLE icb_industry (
  icb_code        text PRIMARY KEY,
  icb_name        text,
  icb_short_name  text,
  parent_icb_code text,
  icb_level       smallint,        -- 1..4
  icb_code_path   text,            -- '8000/8300/8350'
  icb_name_path   text
);

CREATE TABLE instrument (
  symbol      text PRIMARY KEY,
  exchange    text,                -- HOSE | HNX | UPCOM
  stock_type  text,                -- 2 CP | 3 ETF | 4 CW | 12 TP
  tradelot    int,
  full_name   text,
  updated_at  timestamptz DEFAULT now()
);
```

### 5.2 Giá theo ngày — hypertable

```sql
CREATE TABLE price_daily (
  organ_code    text NOT NULL,
  trading_date  date NOT NULL,
  close_adj     numeric,      -- getPriceData.closeValue  → ĐÃ điều chỉnh
  close_raw     numeric,      -- getPriceData.closePrice  → giá THÔ, điền MỘT LẦN rồi không đè
                              --   (đo 2026-09-03: closePrice là giá thô lịch sử — tỷ số với closeValue
                              --   khớp cổ tức tới 4 chữ số, 10/10 khớp tick BVSC; bản cũ ghi
                              --   "/datafeed/instruments EOD" vì tưởng quá khứ không có giá thô ở nguồn nào.
                              --   Writer EOD của BVSC nay chỉ còn vai trò đối chứng — bộ đếm
                              --   raw_close_mismatch của job lộ mọi lệch, spec lát 3 §5.5c)
  open_value    numeric,
  highest_value numeric,
  lowest_value  numeric,
  -- ... 90+ trường còn lại: khối lượng, thoả thuận, khối ngoại,
  --     dòng tiền cá nhân/tổ chức/tự doanh, cờ sự kiện ...
  raw           jsonb,        -- landing zone, giữ nguyên response
  ingested_at   timestamptz DEFAULT now(),
  PRIMARY KEY (organ_code, trading_date)
);
SELECT create_hypertable('price_daily', 'trading_date');
```

**Hệ số điều chỉnh là view suy ra, không phải bảng riêng:**

```sql
CREATE VIEW price_factor AS
SELECT organ_code, trading_date,
       close_adj / NULLIF(close_raw, 0) AS factor
FROM price_daily;
```

Mỗi lần crawl lại `getPriceData`, `close_adj` đổi theo điều chỉnh mới của FiinTrade → hệ số tự đổi → **mọi nến quá khứ hiển thị đúng ngay, không phải viết lại một dòng nào**.

### 5.3 Nến intraday — hypertable + continuous aggregate

> 🔴 **Toàn bộ §5.3 đã lỗi thời.** Nến `bar_1m` (và các cấp gộp) nay sống trong **ClickHouse** (schema `rt`, khoá theo `symbol` chứ không phải `organ_code`), không phải hypertable Postgres/TimescaleDB dưới đây — xem banner đầu trang và [spec ClickHouse](../90-records/plans/2026-08-25-clickhouse-realtime-store/spec.md). Nội dung dưới giữ nguyên văn làm lịch sử.

```sql
CREATE TABLE bar_1m (
  organ_code text NOT NULL,
  ts         timestamptz NOT NULL,
  o numeric, h numeric, l numeric, c numeric,   -- GIÁ THÔ
  v bigint,
  PRIMARY KEY (organ_code, ts)
);
SELECT create_hypertable('bar_1m', 'ts');
SELECT add_compression_policy('bar_1m', INTERVAL '7 days');
```

> 🔴 **Lưu giá thô, không bao giờ sửa.** Giá thô là sự thật lịch sử bất biến — một mã khớp 62.300 lúc 13:45 thì vĩnh viễn là 62.300, không sự kiện quyền nào làm nó sai. Chỉ *cách hiển thị* mới cần điều chỉnh.

Nến lớn hơn dựng phân cấp bằng continuous aggregate:

```sql
CREATE MATERIALIZED VIEW bar_5m WITH (timescaledb.continuous) AS
SELECT organ_code,
       time_bucket('5 minutes', ts) AS ts,
       first(o, ts) AS o, max(h) AS h, min(l) AS l, last(c, ts) AS c,
       sum(v) AS v
FROM bar_1m GROUP BY 1, 2;
-- tương tự bar_15m ← bar_5m, bar_60m ← bar_15m
```

**Đọc thì điều chỉnh:**

```sql
SELECT b.ts,
       b.o * f.factor AS o, b.h * f.factor AS h,
       b.l * f.factor AS l, b.c * f.factor AS c,
       b.v
FROM bar_5m b
JOIN price_factor f
  ON f.organ_code = b.organ_code
 AND f.trading_date = b.ts::date;
```

Khối lượng: ~200k dòng/ngày · **~1 GB/năm** sau nén.

### 5.4 Báo cáo tài chính — dạng dài

```sql
CREATE TABLE financial_statement (
  organ_code     text NOT NULL,
  year_report    smallint NOT NULL,
  quarter_report smallint NOT NULL,   -- 1..4 = quý, 5 = cả năm
  statement_type text NOT NULL,       -- BS | IS | CF
  metric_code    text NOT NULL,       -- bsa1, isa22, cfa18 ...
  value          numeric,
  ingested_at    timestamptz DEFAULT now(),
  PRIMARY KEY (organ_code, year_report, quarter_report, statement_type, metric_code)
);
```

Chọn **dạng dài** vì bộ chỉ tiêu khác nhau theo loại hình doanh nghiệp (`bsa*` phi ngân hàng vs `bsb*` ngân hàng) — dạng cột rộng sẽ thưa hàng trăm cột `null`. Và hợp với việc mã chỉ tiêu chưa có bảng giải mã đầy đủ.

```sql
CREATE TABLE financial_report_file (
  id          bigint PRIMARY KEY,
  organ_code  text,
  year_report smallint,
  length_report smallint,
  title       text,
  source_url  text
);
```

### 5.5 Snapshot theo ngày

```sql
CREATE TABLE snapshot_daily (
  organ_code   text NOT NULL,
  trading_date date NOT NULL,
  kind         text NOT NULL,   -- snapshot | valuation | ownership | dividend
                                -- (company_score và rate_indicator ĐÃ BỎ — migration 0015,
                                --  quyết định 2026-09-03: điểm chữ và cờ 0/1 của bên thứ ba)
  payload      jsonb NOT NULL,
  PRIMARY KEY (organ_code, trading_date, kind)
);
SELECT create_hypertable('snapshot_daily', 'trading_date');

CREATE TABLE screener_daily (
  security_id  bigint NOT NULL REFERENCES market.security,
  trading_date date NOT NULL,
  payload      jsonb NOT NULL,   -- trường có `keep` trong market-field-selection (75/193, đếm 2026-09-03),
                                 -- lồng theo khối nguồn — sau lọc chỉ còn `stockScreenerItem` và `financial`
  PRIMARY KEY (security_id, trading_date)
);
SELECT create_hypertable('screener_daily', 'trading_date');
```

> Đây là chỗ **tự tạo ra lịch sử** cho những thứ API chỉ trả giá trị hiện tại: định giá, cơ cấu sở hữu, tỷ số không nguồn nào khác có. *(Đính chính 2026-09-03: bản cũ nêu "điểm VGM" — nhóm chấm điểm của FiinTrade đã bị **loại có chủ đích** ở [chọn trường §4.2](market-field-selection.md), không lưu.)* Screener không có endpoint lịch sử — chuỗi bắt đầu từ ngày job chạy, không backfill được. ⚠️ Ba mã `rtq12` `rtq27` `rtq83` có ở cả hai khối của **response** với giá trị KHÁC NHAU (đo 2026-09-03). **Kho chỉ lưu bản của khối chuẩn `stockScreenerItem`**, mỗi mã đúng một bản; `financial` chỉ giữ 5 mã riêng nó có, đều thuộc họ tỷ số/thị trường mà BCTC cũng không cấp. Bằng chứng và giới hạn: spec etl screener §5.3.

### 5.6 Sự kiện doanh nghiệp

```sql
CREATE TABLE corporate_event (
  event_type   text NOT NULL,     -- AGM | CashDividend | StockDividend
                                  -- | Earning | IPO | ShareIssuance
  organ_code   text NOT NULL,
  public_date  date,
  exright_date date,
  record_date  date,
  payout_date  date,
  payload      jsonb NOT NULL,
  source_url   text,
  PRIMARY KEY (event_type, organ_code, public_date, coalesce(exright_date, '1900-01-01'))
);
CREATE INDEX ON corporate_event (organ_code, exright_date);
```

### 5.7 Chính sách nén và lưu trữ

| Bảng | Nén sau | Xoá |
|---|---|---|
| `bar_1m` và các aggregate ⚠️ *(lỗi thời — nay ở ClickHouse, xem banner đầu trang)* | 7 ngày | **không xoá** |
| `price_daily` | 30 ngày | **không xoá** |
| `snapshot_daily`, `screener_daily` | 30 ngày | **không xoá** |
| `financial_statement`, `corporate_event` | 90 ngày | **không xoá** |

Kho là tài sản — không đặt retention drop. Nén cột của TimescaleDB đạt 10–20× với dữ liệu chuỗi thời gian.

**Tổng dung lượng ước tính: dưới 10 GB cho toàn bộ lịch sử**, cộng ~1 GB/năm cho nến intraday *(con số nến intraday này đã lỗi thời cùng §5.3 — dung lượng thật của kho ClickHouse theo TTL frame thô 3–4 tháng + nến vĩnh viễn, xem [spec ClickHouse](../90-records/plans/2026-08-25-clickhouse-realtime-store/spec.md))*.

---

## 6. Tầng ngữ nghĩa cho chatbot

### 6.1 Từ điển chỉ tiêu

```sql
CREATE TABLE metric_dictionary (
  code       text PRIMARY KEY,   -- chuẩn hoá chữ thường: rtq12
  name_vi    text,
  name_en    text,
  unit       text,               -- VND | Percentage | ThousandUnit | Unit
  value_min  numeric,            -- valueRange[0] toàn thị trường
  value_max  numeric
);
```

Nạp từ `Screener/GetScreenerParameters` — 83 tiêu chí, kèm tên tiếng Việt và đơn vị.

⚠️ Endpoint trả mã viết hoa chữ đầu (`Rtq12`), dữ liệu trả về viết thường (`rtq12`). **Chuẩn hoá về chữ thường khi nạp.**

⚠️ Từ điển này **không phủ** mã chỉ tiêu BCTC (`bsa*`, `isa*`, `isb*`, `cfa*`, `nob*`). Chúng có nguồn giải mã riêng — **729 mã, độ phủ 100% trên response thật**, lấy từ bundle JS của ứng dụng FiinTrade chứ không phải API. Xem [Phụ lục A §A.5](../10-sources/market/appendix-A-field-codes.md).

> **Hệ quả cho ETL:** nạp `metric_dictionary` từ **hai nguồn**, không phải một. `GetScreenerParameters` cấp 83 chỉ tiêu thị trường kèm `valueRange`; file [`field-dictionary.json`](../10-sources/market/field-dictionary.json) cấp 729 chỉ tiêu (556 BCTC + 173 tỷ số) kèm **`don_vi_du_lieu`** cho 727 mã (99,7%), **392 mã đã xác thực** bằng đẳng thức kế toán và kiểm nhất quán thang. **Đưa cả bảy phép kiểm đó vào bộ giám sát hợp đồng** — chúng phát hiện được cả việc nguồn đổi thang đơn vị lẫn việc dữ liệu hỏng. File JSON là ảnh chụp tĩnh: bundle đổi hash mỗi lần FiinTrade deploy, nên đặt việc trích lại vào [bộ giám sát hợp đồng](#71-giám-sát-hợp-đồng-dữ-liệu) thay vì coi nó là bất biến.

Các mã đã xác minh bằng đối chiếu số học: `rtd11` vốn hoá · `rtd14` EPS · `rtd7` BVPS · `rtd21` P/E · `rtd25` P/B · `rtq12` ROE · `rtq14` ROA · `bsa1` tổng tài sản. Xem [Phụ lục A](../10-sources/market/appendix-A-field-codes.md).

### 6.2 View đặt tên người đọc được

Không bao giờ phơi mã thô cho LLM — `rtq12` không có nghĩa gì với mô hình ngôn ngữ.

```sql
CREATE VIEW v_financial_ratios AS
SELECT o.ticker, fs.year_report, fs.quarter_report,
       max(value) FILTER (WHERE metric_code='rtq12') AS roe,
       max(value) FILTER (WHERE metric_code='rtq14') AS roa,
       max(value) FILTER (WHERE metric_code='rtd21') AS pe,
       max(value) FILTER (WHERE metric_code='rtd25') AS pb
FROM financial_statement fs
JOIN organization o USING (organ_code)
GROUP BY 1,2,3;
```

Bộ view tối thiểu: `v_financial_ratios` · `v_price_adjusted` · `v_company_profile` · `v_corporate_calendar` · `v_money_flow`.

### 6.3 Function calling thay vì SQL tự do

Cho bot gọi tập function đã định nghĩa, không cho sinh SQL tuỳ ý:

```
screen_stocks(criteria, exchange, sector, limit)
get_financials(ticker, statement_type, from_year, to_year)
get_price_series(ticker, from_date, to_date, resolution)
get_corporate_events(ticker, event_type, from_date)
compare_peers(ticker, metrics)
```

Chính xác hơn, tránh truy vấn quét toàn bảng, và kiểm soát được chi phí.

---

## 7. Rủi ro vận hành

| Rủi ro | Xử lý |
|---|---|
| **Ingester là điểm chết đơn** | Standby giữ kết nối ấm, leader election, tiếp quản < 2 s. Mất bao lâu là mất vĩnh viễn |
| **Dữ liệu bị điều chỉnh hồi tố** | Re-crawl BCTC mỗi quý sau mùa báo cáo. Re-crawl giá của mã có sự kiện quyền, bắt tín hiệu từ `corporate_event.exright_date`. Giữ cột `ingested_at` |
| **Schema đổi không báo trước** | Cột `raw jsonb` làm landing zone + **bộ giám sát hợp đồng hằng ngày** (mục 7.1) — phát hiện sớm, dựng lại không phải crawl lại |
| **Nguồn mục ruỗng thầm lặng** | Giám sát tập trường, kiểu dữ liệu, độ phủ. Theo dõi hash bundle của nguồn để biết họ vừa deploy (mục 7.1) |
| **Chạm rate limit** | Token bucket dùng chung giữa ETL và chatbot. Nhịp tuần tự đã kiểm 2026-08-15; nhịp 8 luồng thì chưa — đo lại trước khi bật |
| **Sai `organCode`** | Ràng buộc khoá ngoại tới `organization`. Không cho phép truyền ticker vào tầng ETL |

### 7.1 Giám sát hợp đồng dữ liệu

Nguồn hiện tại **không có versioning, không changelog, không thông báo thay đổi**. Và dulieuchungkhoan.vn không phải khách hàng của API này — đây là API nội bộ chạy website bảng giá của BVSC, không ai cam kết bề mặt đó cho bên thứ ba.

Hệ quả: **phòng vệ duy nhất là tự phát hiện.** Không thể chờ được báo.

#### Vì sao đây không phải rủi ro lý thuyết

Khảo sát dựng tài liệu này đã tìm thấy **tám bề mặt đã chết mà client vẫn gọi**:

| Bề mặt | Trạng thái | Client |
|---|---|---|
| `/datafeed/indexs/getTime` | Luôn rỗng, kể cả trong phiên | Vẫn trong `PriceService` constants |
| `/datafeed/prevTradingDate` · `/alltranslogs` | `404` | Vẫn khai báo |
| `/datafeed/m-instruments` | `500` | Vẫn khai báo |
| `/priceservice/derivative/*` · `/ptorder/*` · `/adorder/*` | `404` toàn bộ | Đủ hàm và hằng số |
| Topic `idx:DER` | App vẫn subscribe lúc khởi động, server không đẩy | Còn nguyên |
| Topic `o:` | Ack `200`, **không bao giờ có dữ liệu** | Còn dùng |
| Topic `pth:` | Handler tồn tại, 0 frame qua ~6 phút đo | Còn nguyên |
| `chartinday` khoá `X200` | Luôn mảng rỗng | Vẫn được yêu cầu |

Phía FiinTrade: `Frequently=Weekly/Monthly` **trả nến ngày âm thầm**, tham số `Ticker=` bị bỏ qua không báo, lỗi runtime .NET lộ ra ngoài.

Kiểu hỏng nguy hiểm nhất ở đây không phải endpoint chết — mà là **API vẫn trả `200`, dữ liệu vẫn có, nhưng sai**.

#### Bộ kiểm thử hợp đồng chạy hằng ngày

```sql
contract_snapshot(
  endpoint         text,
  checked_at       timestamptz,
  field_set_hash   text,      -- hash danh sách trường đã sắp xếp
  field_types      jsonb,     -- tên trường → kiểu
  record_count     int,
  coverage_pct     numeric,   -- độ phủ trên bộ mã mẫu
  p95_latency_ms   int,
  sample_payload   jsonb,
  PRIMARY KEY (endpoint, checked_at)
);
```

Chạy trước phiên, trên **bộ mã mẫu cố định 51 mã** *(xem [Phụ lục B](../10-sources/market/appendix-B-coverage.md))*, đối chiếu với baseline:

| Kiểm tra | Phát hiện |
|---|---|
| Tập trường đổi | Trường biến mất hoặc xuất hiện mới |
| Kiểu dữ liệu đổi | Số thành chuỗi, hoặc ngược lại |
| Số bản ghi lệch quá ngưỡng | Nguồn bắt đầu cắt dữ liệu |
| Độ phủ tụt | Nhóm mã nào đó ngừng có dữ liệu |
| Giá trị bất thường | Giá ≤ 0, tỷ lệ ngoài khoảng, ngày quá cũ |
| Độ trễ p95 tăng | Nguồn đang xuống cấp |

**Kiểm tra riêng cho các lỗi âm thầm đã biết:**

- `o10:` còn đẩy frame không *(và `o:` vẫn im lặng — nếu `o:` bắt đầu chạy thì cũng là thay đổi cần biết)*
- `Frequently=Weekly` còn trả nến ngày không *(nếu họ sửa, kết quả đổi)*
- Kiểu của trường `status` theo từng nhóm endpoint — `0` hay `"Success"`
- Số mã có `organCode ≠ ticker` — hiện 647/1.553. Lệch nhiều nghĩa là danh bạ đã đổi cấu trúc
- Bộ 34 trường của `i:` và 18 trường của `idx:` trên luồng realtime

#### Theo dõi bản build của nguồn — cảnh báo sớm

Kỹ thuật rẻ nhất và báo trước sớm nhất: **giám sát hash bundle JavaScript của chính ứng dụng nguồn**.

| Nguồn | Cách lấy | Hash tại thời điểm khảo sát |
|---|---|---|
| BVSC | `GET /priceboard/` → đọc `src` các thẻ script | `3241ea7a` *(dùng chung mọi chunk)* |
| FiinTrade | `GET /screen/bvsc-analysis` → đọc chunk | `2.d5375412` · `main.876ed868` |

Hash đổi nghĩa là **họ vừa deploy**. Khi đó tự động:
1. Chạy full contract test ngay, không chờ lịch
2. Tải lại bundle, grep lại registry endpoint — phát hiện endpoint mới thêm hoặc bị gỡ
3. So bộ hằng số `PriceService`, `ServiceUrl`, danh sách topic với bản trước

Cách này cho biết nguồn đã đổi **trước khi** dữ liệu của bạn bị ảnh hưởng, thay vì phát hiện sau khi khách hàng phàn nàn.

#### Mức độ cảnh báo

| Mức | Điều kiện | Hành động |
|---|---|---|
| **P1** | Endpoint trả `403`/`404`/`500` · topic realtime ngừng đẩy · Ingester mất kết nối > 60 s | Báo ngay, mất dữ liệu đang diễn ra |
| **P2** | Tập trường đổi · kiểu dữ liệu đổi · giá trị bất thường | Báo trong giờ làm việc — nguy cơ **sai thầm lặng** |
| **P3** | Độ phủ tụt · p95 tăng · **hash bundle đổi** | Xem trong ngày |

#### Vòng lặp thích ứng

Chiến lược là **thích ứng liên tục với nguồn hiện tại**, không phải chuẩn bị đổi nguồn. Ba thứ làm cho vòng lặp này chạy nhanh:

1. **Cột `raw jsonb` là bắt buộc, không phải tuỳ chọn.** Khi schema đổi, bạn dựng lại bảng chuẩn hoá từ payload gốc đã lưu — không phải crawl lại 102.648 lời gọi.
2. **Toàn bộ thay đổi hấp thụ ở tầng ánh xạ, không đụng lược đồ.** Bảng canonical giữ nguyên, chỉ sửa mapping vendor → canonical *(xem mục 9.3)*.
3. **Giữ năng lực đọc bundle.** Kỹ thuật grep registry từ JS bundle là cách duy nhất biết nguồn có endpoint mới. Nên viết thành script chạy được, không phải việc làm tay một lần.

### 7.2 Ba bẫy sẽ cắn ngay ngày đầu triển khai

1. **`organCode ≠ ticker` ở 41% doanh nghiệp** — gọi bằng ticker trả `HTTP 200` với dữ liệu rỗng, không có lỗi
2. **FiinTrade luôn trả `HTTP 200` kể cả khi lỗi** — phải đọc `status` và `errors` trong body
3. **`status` có hai kiểu dữ liệu** — `0` (số) ở nhóm Snapshot, `"Success"` (chuỗi) ở nhóm Calendar

Mười ba bẫy đầy đủ: [00-conventions.md](../10-sources/market/00-conventions.md).

---

## 8. Thứ tự triển khai đề xuất

| Giai đoạn | Nội dung | Điều kiện |
|---|---|---|
| **0** | Dựng hạ tầng Postgres + Redis. *(Rate limit: nhịp tuần tự đã kiểm bằng tải kế hoạch 2026-08-15 — xem [§10 quy ước chung](../10-sources/market/00-conventions.md); nhịp 8 luồng thì phải đo lại trước khi bật)* | — |
| **1** | Bảng tham chiếu + ETL danh bạ/ngành/instrument | Sau GĐ 0 |
| **2** | Ingester realtime + Redis + SSE — **bắt đầu tích luỹ `bar_1m` càng sớm càng tốt** | Song song GĐ 1 |
| **3** | ETL hằng ngày: giá, snapshot, screener, lịch sự kiện | Sau GĐ 1 |
| **3b** | **Bộ giám sát hợp đồng** + theo dõi hash bundle — dựng cùng ETL, dùng chung script | Cùng GĐ 3 |
| **4** | Backfill lịch sử, rải 1–2 tuần | Sau GĐ 3 |
| **5** | Tầng ngữ nghĩa + function calling cho chatbot | Sau GĐ 4 |

> Giai đoạn 2 nên chạy sớm nhất có thể. Mọi dữ liệu khác crawl lại lúc nào cũng được, riêng nến intraday **không tồn tại ở bất kỳ nguồn nào** — mỗi ngày chưa thu là một ngày mất vĩnh viễn.

---

## 9. Định hướng nghiên cứu — thích ứng nguồn và khả năng thay thế

> **Phần này chưa phải thiết kế chi tiết.**

### 9.0 Chiến lược: thích ứng liên tục, không phải chuẩn bị đổi nguồn

Chiến lược chính là **bám sát và thích ứng liên tục với nguồn BVSC/FiinTrade**, dựa trên bộ giám sát hợp đồng ở [mục 7.1](#71-giám-sát-hợp-đồng-dữ-liệu). Lý do:

- Chi phí thích ứng một thay đổi schema là **vài giờ** — sửa tầng ánh xạ, dựng lại từ `raw jsonb`
- Chi phí đổi nguồn là **hàng tuần**, và mất toàn bộ dữ liệu Tầng C *(mục 9.2)*
- Nguồn hiện tại phủ rất sâu: 12,5 năm giá 99 trường, 21 năm BCTC, toàn bộ lịch sử sự kiện

Đổi nguồn là **phương án dự phòng**, không phải kế hoạch. Vì vậy mục tiêu của phần này không phải xây khả năng thay thế, mà chỉ là **không tự khoá mình vào một nguồn** — để nếu buộc phải đổi thì không phải làm lại từ đầu.

### 9.1 Kết luận ngắn

Đổi nguồn **khả thi**, với **hai quyết định về lược đồ nên chốt ngay từ đầu**. Hai thứ đó rẻ nếu làm bây giờ, đắt nếu retrofit sau. Mọi thứ còn lại để đến khi thật sự cần.

### 9.2 Phân tầng theo mức độ khoá nhà cung cấp

| Tầng | Dữ liệu | Đổi nguồn |
|---|---|---|
| **A — Phổ quát** | OHLCV ngày và phút · khối lượng, giá trị · danh mục mã, sàn · chỉ số · sự kiện doanh nghiệp *(gốc từ VSD)* | ✅ Dễ. Nguồn nào cũng có, định nghĩa gần như đồng nhất |
| **B — Có ở nhiều nguồn, định nghĩa khác nhau** | Báo cáo tài chính · phân ngành · dòng tiền theo nhóm NĐT · khối ngoại · thoả thuận | ⚠️ Được, nhưng **phải ánh xạ**. Mỗi nguồn có bộ mã chỉ tiêu và cách gộp khoản mục riêng |
| **C — Độc quyền FiinGroup** | 32 chỉ tiêu `RateIndicator` · mô hình định giá (`estimatedEPS`, `forecastEPS`, `recommendMethod`) · `ZMFScore` · **75/193** trường screener (đếm 2026-09-03). *Điểm VGM và các nhãn xếp hạng (`roe` `grossMargin` `profitGrowth` `revenueGrowth`) thuộc tầng này về bản chất nhưng **cố ý không lưu** — quyết định của chủ dự án: không dùng điểm do bên thứ ba chấm* | ❌ Mất là mất. Không nguồn nào khác có |

Tầng A và B chiếm phần lớn giá trị sử dụng. Tầng C thì chấp nhận **đóng băng**: giữ nguyên lịch sử đã tích luỹ, các ngày sau để `NULL`. Đây chính là mô hình *"phần thiếu kệ nó, phần đủ cứ chạy"*.

### 9.3 Hai điểm khoá nhà cung cấp trong lược đồ hiện tại

#### Điểm 1 — `organ_code` đang là khoá chính

Lược đồ ở mục 5 dùng `organ_code` làm `PRIMARY KEY` của `organization` và khoá ngoại của mọi bảng khác. **Đó là khoá nội bộ của FiinGroup**, không phải định danh phổ quát — 41% doanh nghiệp có `organ_code` khác `ticker`, và 72 mã dùng mã số thuế (`TAH → 3801140300`).

Nguồn khác sẽ không biết `NHN` nghĩa là `VHM`. Đổi nguồn với lược đồ hiện tại nghĩa là viết lại khoá ngoại của toàn bộ kho.

**Hướng nghiên cứu:** tách khoá nội bộ do dulieuchungkhoan.vn sở hữu ra khỏi mã của nhà cung cấp.

```sql
security(security_id BIGSERIAL PK, ticker, exchange, ...)         -- khoá của dulieuchungkhoan.vn
security_external_id(security_id, source, external_code)          -- ánh xạ đa nguồn
```

`organ_code` trở thành một dòng trong `security_external_id` với `source = 'fiintrade'`. Thêm nguồn mới chỉ là thêm dòng.

Chi phí làm ngay: một bảng phụ và một lần chuyển khoá. Chi phí retrofit: động vào mọi khoá ngoại trong kho.

#### Điểm 2 — `metric_code` đang lưu mã FiinGroup thô

`financial_statement.metric_code` chứa `bsa1`, `isa22`, `cfa18` — mã của FiinGroup. Nguồn khác dùng bộ mã hoàn toàn khác.

**Hướng nghiên cứu:** giữ mã gốc của nguồn, đồng thời gắn thêm mã chuẩn hoá của dulieuchungkhoan.vn.

```sql
ALTER TABLE financial_statement ADD COLUMN canonical_code text;
metric_mapping(source, vendor_code, canonical_code, name_vi, unit)
```

`canonical_code` có thể để trống lúc đầu và điền dần — không chặn tiến độ. Nhưng cột phải có sẵn, và ETL phải ghi `source` ngay từ ngày đầu.

Việc này còn giải quyết luôn khoảng trống hiện tại: mã BCTC (`bsa*`, `isa*`, `cfa*`) chưa có bảng giải mã từ FiinGroup. Xây taxonomy riêng thì vừa gỡ khoá nhà cung cấp, vừa có tên chỉ tiêu cho chatbot.

### 9.4 ETL độc lập theo miền

Mô hình bạn mô tả — *phần thiếu kệ nó, phần đủ cứ chạy* — đúng và nên làm ngay vì rẻ:

```sql
data_domain_state(
  domain          text,      -- reference | price_daily | intraday
                             -- | fundamentals | events | scores
  source          text,      -- fiintrade | bvsc | <nguồn mới>
  status          text,      -- active | frozen | migrating
  last_success_at timestamptz,
  watermark       text
);
```

Mỗi miền có **job riêng, watermark riêng, nguồn riêng**. Ba nguyên tắc:

1. Miền mất nguồn thì chuyển `frozen` — các miền khác không bị ảnh hưởng
2. Mọi bảng có cột `source` để biết dòng nào đến từ đâu
3. **View đọc phải chịu được `NULL`, không được lỗi.** Đây là điều kiện để phần thiếu không làm sập phần đủ

Điểm cộng của thiết kế hiện tại: quyết định **lưu giá thô, điều chỉnh lúc đọc** đã giúp phần giá gần như miễn nhiễm với việc đổi nguồn. Giá thô là sự thật bất biến; đổi nguồn chỉ cần tính lại `price_factor` từ chuỗi điều chỉnh của nguồn mới.

### 9.5 Hướng tìm nguồn thay thế

Chưa kiểm chứng nguồn nào trong số này — liệt kê để nghiên cứu sau:

| Hướng | Ghi chú |
|---|---|
| **FiinGroup trực tiếp** | Bỏ qua BVSC, làm việc thẳng với chủ dữ liệu. Cùng schema, cùng mã chỉ tiêu → chi phí đổi gần bằng 0 |
| **DNSE** — `datafeed.dnse.com.vn` | Đáng chú ý: chính bundle FiinTrade có sẵn cấu hình `REACT_APP_REAL_TIME_HOST: "datafeed.dnse.com.vn"` kèm `REACT_APP_REAL_TIME_CLIENTID` — tức FiinTrade đã từng hoặc đang tích hợp DNSE làm nguồn realtime |
| **API các CTCK khác** | SSI, VNDirect, VPS, TCBS đều có API dữ liệu ở mức độ khác nhau |
| **Sở GDCK trực tiếp** | HOSE/HNX — nguồn gốc, đắt nhất, nhưng độc lập hoàn toàn |
| **Nguồn dữ liệu cơ bản** | Vietstock, Wichart, Simplize cho BCTC và chỉ số tài chính |

Thứ tự ưu tiên nghiên cứu nên theo **tầng A trước** — có nguồn thay thế cho OHLCV và sự kiện doanh nghiệp là đã giữ được phần lớn giá trị kho.

### 9.6 Việc nên làm và không nên làm

| | |
|---|---|
| ✅ **Làm ngay** | Tách `security_id` khỏi `organ_code` · thêm cột `source` và `canonical_code` · bảng `data_domain_state` *(đã làm 2026-08-25 với một override có ý thức: cột `source` KHÔNG đặt ở bảng dữ liệu — nguồn có thể đổi, xuất xứ nằm ở bảng ánh xạ registry/staging/ops; `canonical_code` và `data_domain_state` giữ nguyên — xem [spec](../90-records/plans/2026-08-25-postgres-data-schema/README.md) quyết định #4)* |
| ⏳ **Làm khi cần** | Tầng adapter cho nguồn cụ thể · logic hoà giải khi hai nguồn chồng lấn · điền đầy `metric_mapping` |
| ❌ **Không làm** | Đừng dựng khung plugin trừu tượng cho nguồn chưa biết. Trừu tượng hoá sớm dựa trên một nguồn duy nhất thường tạo ra đúng cái khung sai |

Nguyên tắc: **không cần hệ thống có thể đổi nguồn ngay, chỉ cần hệ thống không tự khoá mình vào một nguồn.** Ba việc ở cột "làm ngay" đủ để đạt điều đó, tổng chi phí khoảng một ngày công.
