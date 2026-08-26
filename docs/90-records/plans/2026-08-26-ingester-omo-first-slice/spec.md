# Spec — Lát cắt dọc đầu tiên: `ingester` realtime + job `etl` crawl OMO

**Ngày:** 2026-08-26 · **Trạng thái:** ✅ hướng đã duyệt trong brainstorm 2026-08-26 (4 quyết định chủ dự án ở §1) — chủ dự án uỷ quyền đi trọn chuỗi spec → plan → thực thi trong cùng phiên, tự rà và sửa điểm bất nhất phát hiện dọc đường · **Loại:** lát cắt dọc đầu tiên của code sản phẩm ([service-topology §7](../../../20-design/service-topology.md))

**Phạm vi:** hai track độc lập, một lát cắt — mục tiêu là **dừng đồng hồ mất dữ liệu** ([roadmap §2](../../../00-overview/roadmap.md)):

- **Track A — `ingester`** (daemon, `backend/ingester/`): socket BVSC → Redis (hot path) → ClickHouse schema `rt` (batch), theo đúng hợp đồng writer [spec ClickHouse §5](../2026-08-25-clickhouse-realtime-store/spec.md) và hợp đồng khởi động §8 của cùng spec.
- **Track B — job `etl` crawl OMO** (`backend/etl/`): HTML SBV → `macro.omo_session`/`omo_auction` + `staging.raw_payload` (Postgres), rebuild `macro.omo_flow`.

**Không thuộc spec này:** `api` (chưa có gì để phục vụ), SSE, mọi ETL REST khác, phái sinh (chưa đo — [roadmap §5.1](../../../00-overview/roadmap.md), cấm giả định). Danh sách đầy đủ ở §8.

**Nguồn ràng buộc phải tôn trọng** (spec này không lặp lại nội dung, chỉ trỏ và bổ sung phần chưa chốt):

| Ràng buộc | Ở đâu |
|---|---|
| Hợp đồng writer ClickHouse (buffer 1 s, hai lưới dedup, block độc, retry, `received_at` đơn điệu, trường lạ, đối chứng §5.7) | [spec ClickHouse §5](../2026-08-25-clickhouse-realtime-store/spec.md) |
| Hợp đồng khởi động (`assert_migrated` trước khi nối socket) | spec ClickHouse §8 — hàm `core.ch_migrate.assert_migrated` đã tồn tại, yêu cầu `0002_rt_schema` |
| Phạm vi đăng ký + danh mục runtime (quyết định #8/#9) | spec ClickHouse §1 |
| Giao thức socket, 20 topic, bẫy `o10:`/ack-200/reconnect | [11-bvsc-realtime.md](../../../10-sources/market/11-bvsc-realtime.md) |
| Bẫy REST (StockType theo endpoint, hai endpoint danh mục lệch phủ, Origin) | [00-conventions.md](../../../10-sources/market/00-conventions.md) bẫy 10/11 · [01-bvsc-rest.md](../../../10-sources/market/01-bvsc-rest.md) |
| Nguồn OMO (WAF, 4 cột, ngày trong tiêu đề, chỉ phiên mới nhất) | [sbv-omo.md](../../../10-sources/macro/sbv-omo.md) |
| Schema đích OMO (3 bảng + staging + ops) | [postgres-data step-04 §3](../2026-08-25-postgres-data-schema/step-04-macro.md) · migration `0008` |

---

## 1. Quyết định chốt trong brainstorm 2026-08-26 (chủ dự án)

| # | Quyết định | Lý do |
|---|---|---|
| 1 | **Build socket client trước, phiên đo chạy bằng chính nó** (chế độ `--measure`, ghi frame ra file, không ghi DB) | Không có code vứt đi; client được kiểm trên dữ liệu thật trước khi được phép ghi kho. Phiên đo là **gate cứng trước khi bật ghi thật** (spec ClickHouse §4.1/§10, roadmap §5.1) |
| 2 | **Leader lock Redis dựng từ đầu, lát đầu chạy 1 instance** | Active+standby là ràng buộc cứng của [service-topology §2](../../../20-design/service-topology.md); dựng lock ngay thì standby chỉ là "chạy thêm bản thứ hai", không phải retrofit đường ghi |
| 3 | **OMO poll ~4 lần/ngày** (11:30 · 15:30 · 18:00 · 21:30, ngày làm việc), idempotent theo ngày trong tiêu đề | Giờ SBV đăng bài **chưa kiểm** ([sbv-omo.md §10](../../../10-sources/macro/sbv-omo.md)); lỡ một phiên là hỏng cửa sổ 140 ngày. Tuần đầu ghi nhận giờ bài lên thật rồi rút lịch |
| 4 | **Chạy thật trên máy Windows này, dài hạn** — ingester mỗi phiên + OMO mỗi ngày, tới khi có server Linux thì dời | Đồng hồ mất dữ liệu dừng ngay khi lát này xong, không chờ hạ tầng deploy |

**Quyết định kỹ thuật của kiến trúc sư (đã trình trong brainstorm, chủ dự án duyệt gộp):**

| # | Quyết định | Lý do |
|---|---|---|
| 5 | **Socket client EIO3/sails.io tự viết** trên thư viện `websockets`, không dùng `python-socketio` | Bản python-socketio nói EIO3 đã ngừng bảo trì; phần sails.io envelope (`["get",{"url":"/client/subscribe",…}]`) đằng nào cũng phải tự viết; giao thức đã đo đủ ở [11-bvsc-realtime §1](../../../10-sources/market/11-bvsc-realtime.md) và rất nhỏ (5 loại frame) |
| 6 | **Ingester là daemon THEO PHIÊN, không chạy 24/7**: Task Scheduler khởi động ~08:30, tiến trình tự thoát sau đối chứng cuối phiên (~15:15) | "Làm mới danh mục trước phiên mỗi ngày" (quyết định #9 spec ClickHouse) trở thành *khởi động lại mỗi sáng* — bỏ hẳn logic refresh trong tiến trình; đêm không treo socket vô ích; crash giữa phiên thì Task Scheduler restart |
| 7 | **Chạy như process host (`uv run`), không docker hoá ingester/etl lượt này** | ClickHouse/Redis/Postgres bind `127.0.0.1` sẵn; docker hoá thêm phức tạp mạng mà không thêm giá trị trên máy dev Windows; entry compose `deploy/app` để lượt deploy Linux (đúng chỗ spec ClickHouse §7 đã để dành) |
| 8 | **Lưới dedup frame = hash nội dung frame đã chuẩn hoá, cửa sổ trượt theo thời gian** — KHÔNG dùng luật thứ tự `SM` trước phiên đo | Spec ClickHouse §5.4 cấm so sánh thứ tự SM khi tính chất SM chưa đo; hash nội dung an toàn với mọi topic: frame trùng thật (nguồn đẩy lại sau reconnect) thì nội dung bằng nhau từng byte sau chuẩn hoá, frame khác nội dung không bao giờ bị nuốt |
| 9 | **Hợp đồng Redis đặt tên trường theo tên cột ClickHouse** (một từ điển ánh xạ dùng chung cho cả hai đường ghi) — chi tiết §3.4 | Hai bảng tên trường (nguồn `SB`/`CP`… và cột `symbol`/`close_price`…) đã buộc phải tồn tại; thêm bộ tên thứ ba riêng cho Redis là mời bẫy "hai nguồn sự thật" |
| 10 | **Phiên đo ghi file frame thô replay được**: sau khi chốt luật, có thể nạp lại phiên đo qua đúng đường writer (tuỳ chọn, không chặn AC) | Phiên đo không bị mất trắng — frame đã bắt được là dữ liệu thật |

**Đã cân nhắc và loại (loại có chủ đích):**

| Mục | Lý do loại |
|---|---|
| HTTP health endpoint cổng 8100 ngay lượt này | Chưa có ai gọi; giám sát lát đầu bằng log có cấu trúc + exit code + Task Scheduler restart. Dựng khi có monitoring thật (service-topology §6 giữ chỗ cổng 8100) |
| Docker hoá ingester + entry compose `deploy/app` | Đã có đường khác — quyết định #7 trên; làm khi deploy Linux |
| Metrics server / Prometheus | Cùng lý do health endpoint; danh sách đo tuần đầu (spec ClickHouse §10) phủ được bằng log + SQL trực tiếp |
| Dedup theo `SM` (bỏ frame có SM ≤ SM cuối) | Chưa đo tính đơn điệu/duy nhất của SM — chính là thứ phiên đo phải trả lời; quyết định #8 dùng hash nội dung thay thế |
| Crawl OMO trong ingester (vì cùng perishable) | OMO là HTML theo ngày, thuộc `etl` — đã chốt ở [service-topology §2](../../../20-design/service-topology.md), không mở lại |

---

## 2. Track A — hình dạng tiến trình `ingester`

Một tiến trình asyncio, entrypoint `python -m ingester`. Các task đồng thời:

```
main ─┬─ leader_loop      giữ/giành lock Redis (§3.6)
      ├─ socket_loop      nối wss → parse frame → (đo: ghi file) | (thật: chuẩn hoá → dedup → state/Redis + buffer CH)
      ├─ flush_loop       mỗi 1 s flush buffer → INSERT ClickHouse (hợp đồng writer §5 spec ClickHouse)
      ├─ log_loop         mỗi 60 s in counter (frame/loại, dòng ghi, retry, poison, dedup drop, khoá lạ)
      └─ (cuối phiên)     sau 15:05 → đối chứng §3.7 → in kết quả → thoát
```

### 2.1 Trình tự khởi động (hợp đồng — thứ tự cứng)

1. Nạp config từ env (§5). Thiếu biến bắt buộc → thoát lỗi rõ, exit code ≠ 0.
2. `core.ch_migrate.assert_migrated(client)` — thiếu migration → **không nối socket**, thoát lỗi rõ (spec ClickHouse §8). *(Chế độ `--measure` bỏ qua bước này — không đụng DB.)*
3. Nối Redis, kiểm `PING`. *(`--measure` bỏ qua.)*
4. Dựng **danh mục runtime** (§3.2): hợp nhất `/quotes?symbols=ALL` + `/datafeed/instruments` (không tham số).
5. Khởi tạo **state nền** mỗi mã từ chính response `/datafeed/instruments` vừa gọi (`open`/`low`/`ceiling`/`floor`/`reference` không được đẩy qua socket — [11-bvsc-realtime §4](../../../10-sources/market/11-bvsc-realtime.md)).
6. Giành leader lock (§3.6). Chưa giành được → giữ chế độ standby: vẫn nối socket + subscribe (giữ ấm state + seen-set), **không ghi** Redis/ClickHouse.
7. Nối socket, đăng ký topic theo danh mục.

### 2.2 Ba chế độ chạy

| Chế độ | Lệnh | Ghi gì |
|---|---|---|
| Thật | `python -m ingester` | Redis + ClickHouse |
| Đo | `python -m ingester --measure --out <dir>` | Chỉ file frame thô (§3.5); không Redis, không ClickHouse, không cần lock |
| Đối chứng tay | `python -m ingester --reconcile [--date YYYY-MM-DD]` | Chỉ đọc ClickHouse, in kết quả §3.7 (mặc định ngày hiện tại) |

## 3. Track A — từng khối

### 3.1 Socket client (EIO3 / sails.io)

Bám nguyên văn [11-bvsc-realtime §1](../../../10-sources/market/11-bvsc-realtime.md):

- URL đủ tham số `EIO=3&transport=websocket&__sails_io_sdk_version=1.2.1&__sails_io_sdk_platform=browser&__sails_io_sdk_language=javascript`.
- Parse 5 loại packet: `0{json}` (open — đọc `pingInterval`/`pingTimeout` từ server, không hardcode), `2`/`3` (ping/pong — client phải tự gửi `2` theo `pingInterval`), `40` (namespace ready), `42[…]`/`43<ackId>[…]` (event/ack). Packet lạ → log, không crash.
- Subscribe: `42<ackId>["get",{"url":"/client/subscribe","method":"get","headers":{},"data":{"op":"subscribe","args":[…]}}]`. Args chia lô (kích thước lô chốt ở plan) — 2.000 mã × 3 topic không nhét một frame.
- **Ack `statusCode: 200` không xác nhận gì** (bẫy §1.4) — client không dùng ack làm bằng chứng topic sống; bằng chứng duy nhất là frame về.
- Reconnect: `onclose → chờ 5 s → nối lại → đăng ký lại TOÀN BỘ → gọi lại /datafeed/instruments đồng bộ state` ([market-data-store §3.3](../../../20-design/market-data-store.md)). Backoff giữ 5 s cố định như client gốc BVSC; rớt ~2 lần/4 phút là bình thường, không phải sự cố.
- Sự kiện nhận: `i` · `o` (đăng ký `o10:`) · `t` · `idx` · `ptm`. Sự kiện ngoài danh sách → đếm + log, bỏ qua.

### 3.2 Danh mục runtime (quyết định #8/#9 spec ClickHouse)

- Gọi `GET {BVSC}/quotes?symbols=ALL` và `GET {BVSC}/datafeed/instruments` (không tham số — `symbols=ALL` ở endpoint này trả rỗng, [01-bvsc-rest](../../../10-sources/market/01-bvsc-rest.md)).
- Hợp nhất khử trùng theo `symbol`. Phân loại **chỉ bằng `StockType` của `/quotes`** (bẫy 10 — bảng mã chỉ có nghĩa trong phạm vi một endpoint): `2` (cổ phiếu) + `3` (ETF/CCQ) → đăng ký `i:`/`o10:`/`t:`. Mã chỉ có ở `/datafeed/instruments` mà không có ở `/quotes` (vd phái sinh) → **không đăng ký** lượt này (phái sinh cấm giả định). Mã chỉ có ở `/quotes` (vd `VFMVF1`) → vẫn đăng ký nếu StockType ∈ {2,3}; state nền của mã đó lấy `ceiling`/`floor`/`reference` từ chính `/quotes` (instruments không có nó), các trường còn lại để trống tới khi frame đầu tiên về.
- Chứng quyền (`4`) · trái phiếu (`12`) · lô lẻ: **loại có chủ đích** ([CLAUDE.md §2.2](../../../../CLAUDE.md)).
- 15 mã chỉ số ([11-bvsc-realtime §2](../../../10-sources/market/11-bvsc-realtime.md)) → `idx:`; 3 sàn `HOSE`/`HNX`/`UPCOM` → `ptm:`.
- Danh mục sống trong bộ nhớ suốt phiên; reconnect dùng cache, không gọi lại `/quotes` (quyết định #9) — riêng `/datafeed/instruments` gọi lại để đồng bộ state (đó là đồng bộ *giá trị*, không phải đổi *danh mục*).

### 3.3 Chuẩn hoá tại cổng (một module, dùng chung cho cả Redis lẫn ClickHouse)

Từ điển ánh xạ trường nguồn → tên cột `rt.*` là **một bảng duy nhất** trong code (nguồn sự thật: DDL [spec ClickHouse §3](../2026-08-25-clickhouse-realtime-store/spec.md)). Luật ép kiểu — đúng hợp đồng writer §5.3 + seam "ép kiểu + timezone" đã ghi trước ở §9 spec ClickHouse:

- Chuỗi số → `Decimal`/`int`; **không đi qua float**; khối lượng nguồn lúc có lúc không đuôi `.0` (`"215271860.0"` → `215271860`).
- Thừa thập phân so với scale cột (`"100.005"` → cột `Decimal64(2)`): chuẩn hoá tại cổng theo luật **làm tròn half-even về scale 2 + đếm metric** — không thả cho ClickHouse cắt im lặng.
- `t` (topic `t`): `ts` dựng từ `TD dd/MM/yyyy` + `FT HH:mm:ss` theo `Asia/Ho_Chi_Minh`. *(Đính chính khi thực thi 2026-08-26: yêu cầu **assert `TD == toDate(ts)`** ghi ở đây và ở [spec ClickHouse §3.1](../2026-08-25-clickhouse-realtime-store/spec.md) là **tautology với đường parse này** — `ts` dựng TRỰC TIẾP từ `TD`, không có cách nào lệch. Guard thật là `strptime` hỏng → `NormalizeError` → đường block độc. Assert chỉ có nghĩa nếu sau này `ts` đến từ nguồn khác `TD`; đổi đường dựng `ts` thì phải thêm assert lại.)*
- `ptm`: `LS` là epoch **giây**; `i`/`o`/`idx`: `t` là epoch **ms**.
- `i`/`idx`/`ptm`: trường không map vào cột → JSON vào `extra` (kể cả `MKI`/`IAC` của ptm). `t`/`o`: khoá lạ → **đếm + log, không lưu** (hợp đồng §5.6).
- Frame `i` có cả `CV` lẫn `P1` → assert mềm `CV == P1`, lệch thì log (nghi `P1` đổi nghĩa).
- `received_at`: cấp tại cổng, **đơn điệu tăng theo mã trong một phiên chạy**: `max(now_ms, last_của_mã + 1 ms)` (bất biến khoá argMin/argMax — spec ClickHouse §4.1).

### 3.4 State + hợp đồng Redis (mặt tiếp xúc cho `api` sau này — đổi phải qua spec khi dựng `api`)

Chỉ leader ghi. Tên trường = tên cột ClickHouse (quyết định #9 §1). Giá trị số serialize dạng chuỗi thập phân đã chuẩn hoá.

| Khoá / kênh | Nội dung |
|---|---|
| HASH `rt:state:{symbol}` | State đầy đủ mỗi mã: các cột `rt.snapshot_delta` (trừ `extra`/`received_at`) + `open`/`low`/`ceiling`/`floor`/`reference` (từ REST) + `ts` (epoch ms lần cập nhật cuối) |
| HASH `rt:state:idx:{code}` | State chỉ số: các cột `rt.index_delta` (trừ `extra`/`received_at`) + `ts` |
| PUBLISH `rt:pub:i:{symbol}` · `rt:pub:t:{symbol}` · `rt:pub:o:{symbol}` · `rt:pub:idx:{code}` · `rt:pub:ptm:{floor}` | JSON delta: chỉ trường frame vừa mang, tên theo cột, kèm `symbol` + `ts` |
| Lock `rt:ingester:leader` | §3.6 |

State dựng lại từ `/datafeed/instruments` khi khởi động/reconnect, **không hâm nóng từ ClickHouse** (hợp đồng §5.9 — quan hệ một chiều). HASH ghi bằng `HSET` các trường vừa đổi (delta), kèm `EXPIRE` 24 h (state cũ tự chết qua đêm, mỗi sáng dựng mới).

### 3.5 Chế độ đo `--measure` + phiên đo trong giờ (GATE cứng)

**Chế độ đo:** nối socket, đăng ký như thật **cộng thêm**: toàn bộ 20 topic của bảng hằng số ([roadmap §5.1](../../../00-overview/roadmap.md)) cho 2–3 mã phái sinh (`41I1G8000` là mã duy nhất có thanh khoản thật, đo 2026-08-15) + `pth:` ba sàn. Mỗi frame ghi một dòng JSONL: `{"r":<received_at_ms>,"p":"<packet nguyên văn>"}` — lưu **cả packet chưa parse** để round-trip đúng từng byte; xoay file theo giờ, nén gzip khi đóng file. Không ghi DB, không cần Redis/lock.

**Phiên đo** (một phiên giao dịch trọn, 08:40–15:05, sớm nhất là phiên kế tiếp):

1. Chạy `--measure` trọn phiên (chú ý phái sinh mở 08:45, sớm hơn cổ phiếu 15 phút).
2. Script phân tích offline trả lời, tối thiểu:
   - **Tính chất `SM`** trong (mã, giây) và trong (mã, phiên): duy nhất? đơn điệu? bộ đếm toàn sở hay theo mã? — quyết định luật dedup/khoá nến (spec ClickHouse §4.1: "điều kiện tiên quyết trước khi bật ghi thật").
   - **Topic nào mang tick phái sinh**, định dạng frame, tần suất, có `openInterest` không (roadmap §5.1 — 4 bước nguyên văn).
   - **Phút sớm nhất/muộn nhất** có frame `idx` và `t` (guard `MI > 0` quanh ATO — spec ClickHouse §4.2).
   - Khoá lạ trong `t`/`o` (kiểm tính đóng của bộ trường — hợp đồng §5.6); `CV == P1` giữ được không; tải thật (frame/giây theo loại — đối chiếu dải §10 spec ClickHouse).
   - `pth` có frame nào không (đóng nốt câu treo [11-bvsc-realtime §9](../../../10-sources/market/11-bvsc-realtime.md)).
3. **Deliverable:** báo cáo đo vào `docs/90-records/surveys/2026-08-XX-bvsc-realtime-session/` + cập nhật [11-bvsc-realtime.md](../../../10-sources/market/11-bvsc-realtime.md) (tầng reference — mọi số kèm ngày đo) + cập nhật [roadmap §5.1](../../../00-overview/roadmap.md).
4. **Gate:** chủ dự án duyệt kết luận SM/dedup → mới bật ghi thật từ phiên kế tiếp. Trước đó mọi lần chạy `python -m ingester` (không cờ) trong giờ giao dịch bị coi là chưa hợp lệ về quy trình — không có khoá kỹ thuật, kỷ luật nằm ở trình tự thực thi plan.
5. *(Tuỳ chọn — quyết định #10)*: nạp lại file frame phiên đo qua đúng đường chuẩn hoá + writer để không mất phiên đó; chỉ làm **trước** khi ghi realtime phiên sau (tránh xen kẽ), và chỉ khi luật đã chốt.

### 3.6 Leader lock (Redis)

- Khoá `rt:ingester:leader`, `SET NX PX <ttl>`, giá trị = id tiến trình (host+pid+random). TTL 5 s, leader renew mỗi 2 s (so id trước khi renew — không renew khoá của người khác); mất renew 2 lần → tự hạ cấp về standby (ngừng ghi ngay). Standby thử giành mỗi 500 ms → tiếp quản < 2 s ([market-data-store §3.1](../../../20-design/market-data-store.md)).
- Chỉ leader ghi Redis state/pub + đẩy buffer ClickHouse. Standby vẫn nhận frame để giữ state + seen-set ấm (dedup liền mạch khi tiếp quản). Renew/hạ cấp phải **atomic phía Redis** (script Lua so-id-rồi-gia-hạn) — chi tiết ở plan.
- Lát đầu chạy 1 instance; chạy thêm bản thứ hai là có standby, không đổi code.

### 3.7 Đối chứng cuối phiên (hợp đồng §5.7 spec ClickHouse — chủ sở hữu: lát này)

Sau 15:05 (hoặc `--reconcile`): với mỗi (mã, ngày), so `Σ bar_1m_v.v` với `max(trade.cum_volume)` và `Σ val` với `max(cum_value)`:

- `Σv > max(AVO)` → **P1** (đếm đôi — luôn là lỗi, mọi mức lệch).
- `Σv < max(AVO)` quá **0,1%** → **P2**; dưới ngưỡng → metric (mất mát đã chấp nhận §5.5).
- Lát này P1/P2 = dòng log mức ERROR/WARNING + exit code riêng của bước đối chứng; nối vào bộ giám sát hợp đồng khi ETL 3b dựng (đúng ghi chú §5.7).

### 3.8 Vận hành trên máy Windows

- Task Scheduler: ngày làm việc 08:30 chạy `ingester`, tiến trình tự thoát ~15:15 sau đối chứng; cấu hình restart-on-crash của Task Scheduler bật. Ngày lễ không cần loại trừ — nối socket không frame, đối chứng rỗng, vô hại.
- Log ra file theo ngày (thư mục chốt ở plan, ngoài repo), `PYTHONIOENCODING=utf-8` ([CLAUDE.md §5](../../../../CLAUDE.md)). Không in giá trị secret.
- Lệnh đăng ký Task Scheduler là deliverable của plan (script `scripts/` hoặc hướng dẫn trong README backend — chốt ở plan).

## 4. Track B — job `etl` crawl OMO

Module trong `backend/etl/`; CLI mở rộng `python -m etl` hiện có thành subcommand: không đối số → heartbeat như cũ (giữ tương thích compose `deploy/app`), `python -m etl omo` → job này.

### 4.1 Fetcher + cổng WAF (bắt buộc, đứng trước mọi thứ)

- `GET https://sbv.gov.vn/vi/nghi%E1%BB%87p-v%E1%BB%A5-th%E1%BB%8B-tr%C6%B0%E1%BB%9Dng-m%E1%BB%9F` bằng httpx, header trình duyệt đầy đủ (UA Chrome, `Accept`, `Accept-Language: vi,en;q=0.9` — [sbv-omo.md §3](../../../10-sources/macro/sbv-omo.md); WAF chặn dấu vân tay `python-requests` bằng **HTTP 200 body 246 byte**).
- Cổng: body ≥ 100 KB (trang thật ~414 KB; < 10 KB chắc chắn bị chặn — ngưỡng 100 KB có biên an toàn) **VÀ** chứa `KẾT QUẢ ĐẤU THẦU THỊ TRƯỜNG MỞ`. Hụt một điều kiện → log ERROR + `ops.etl_run.status='failed'`, **không ghi kho, không ghi staging** (step-04 §2).
- Không retry rát: một lần retry sau 60 s cho lỗi mạng/transient; bị WAF chặn thì dừng (lần poll sau trong ngày là retry tự nhiên — quyết định #3).

### 4.2 Parser phòng thủ

- **Ngày lấy từ tiêu đề bài** `KẾT QUẢ ĐẤU THẦU THỊ TRƯỜNG MỞ (dd.mm.yy)` — cấm ngày hệ thống. Không tìm thấy tiêu đề/ngày → fail.
- Bảng dò theo **tiêu đề cột** (`Loại hình giao dịch`…), class `ls01-*` chỉ là gợi ý phụ; số cột ≠ 4 → fail kèm cảnh báo markup đổi.
- Nhóm (`ls01-group` / nhãn dòng): `Mua kỳ hạn` → `reverse_repo` · `Bán kỳ hạn` → `repo` · `Bán hẳn` → `outright_sale`; **nhóm lạ → fail to, không đoán** (cấu trúc hai nhóm sau chưa từng quan sát — sbv-omo.md §10). Vắng nhóm là dữ kiện → cờ `has_*` = false.
- Kỳ hạn parse từ nhãn dòng trong nhóm (danh mục 7/14/21/28/35/56/63/91/140 — giá trị ngoài danh mục vẫn ghi nếu là số nguyên dương, kèm log WARNING).
- Số định dạng Việt `6.307,47` (tỷ VND) → `Decimal` → × 1e9 → VND gốc (luật C2 step-04); `4/4` tách participants/winners; đối chiếu tổng nhóm (`ls01-total`) với tổng các dòng — lệch → fail (parse sai đâu đó).

### 4.3 Writer Postgres (user thuộc role `dlck_etl`)

Một transaction:

1. `session_date` đã có trong `macro.omo_session` → **bỏ qua toàn bộ, không ghi đè** (phiên cũ chưa cập nhật — sbv-omo.md §9.2), log INFO, `etl_run` success với stats `{"skipped": true}`.
2. Chưa có → INSERT `omo_session` (cờ ba nhóm) + `omo_auction` (mỗi dòng nhóm × kỳ hạn) + HTML gốc vào `staging.raw_payload` (`source='sbv'`, `endpoint_key='omo'`, `content_type='html'`, `meta` giữ độ dài body + hash).
3. Rebuild `macro.omo_flow` (§4.4).
4. `ops.etl_run`: mở dòng `job='macro.omo_crawl'` đầu run, đóng success/failed cuối run. `ops.data_domain_state` upsert (`domain='macro.omo'`, `source='sbv'`, `status='active'`, `last_success_at`, `watermark=session_date`).

### 4.4 Rebuild `macro.omo_flow` — toàn phần, idempotent

- Xoá-dựng lại toàn bảng từ `omo_auction` (tầng tự tính — luật step-04): `injection`/`maturing`/`net` theo công thức [sbv-omo.md §8](../../../10-sources/macro/sbv-omo.md); chiều dấu: `reverse_repo` phát hành = bơm, đáo hạn = hút; `repo`/`outright_sale` phát hành = hút, đáo hạn = bơm — **chiều của repo/outright_sale chưa kiểm trên phiên thật** (step-04), gặp phiên đầu tiên có nhóm này thì đối chiếu tay trước khi tin.
- `complete(D)` = đủ ≥ 140 ngày lịch sử **và** không thiếu phiên nào trong cửa sổ [D−140, D] đối chiếu lịch ngày làm việc từ `SELECT DISTINCT trading_date FROM market.price_daily`. **`price_daily` hiện rỗng → điều kiện (2) không đánh giá được → `complete` giữ `false`** — đúng ngữ nghĩa (140 ngày đầu vốn dĩ false), ghi chú trong code; khi ETL giá dựng xong thì tự lành.
- `outstanding_vnd`: cộng dồn ròng từ ngày đầu có dữ liệu; chỉ có nghĩa khi `complete` — tầng đọc lọc theo cờ, job cứ ghi.

### 4.5 Lịch chạy

Task Scheduler 4 mốc 11:30 · 15:30 · 18:00 · 21:30 (Thứ Hai–Thứ Sáu) chạy `python -m etl omo`. Tuần đầu: so `crawled_at` với thời điểm ngày tiêu đề đổi để suy giờ đăng bài thật → rút lịch còn 1–2 mốc (ghi lại vào [sbv-omo.md](../../../10-sources/macro/sbv-omo.md) mục "chưa kiểm" giờ đăng bài, kèm ngày đo).

## 5. Cấu hình & phụ thuộc

| Biến env (thêm vào `.env.example` cùng lượt) | Dùng bởi | Ghi chú |
|---|---|---|
| `CLICKHOUSE_INGESTER_URL` | ingester | user login `ingester_worker` gắn role `dlck_ingester` (tạo per-môi-trường theo [create_users.sql.example](../../../../database/clickhouse/create_users.sql.example)); KHÔNG dùng user quản trị để ghi |
| `REDIS_URL` | ingester | `redis://127.0.0.1:6379/0` (host/port đã có trong `.env.example` dạng rời — gộp thành URL, giữ hai biến cũ cho compose) |
| `ETL_DATABASE_URL` | job omo | user login `etl_worker IN ROLE dlck_etl` (per-môi-trường — lệnh mẫu ở [database/README.md](../../../../database/README.md)) |
| `INGESTER_LOG_DIR` / `INGESTER_MEASURE_DIR` | ingester | thư mục ngoài repo; default chốt ở plan |

Phụ thuộc mới trong `backend/pyproject.toml`: `websockets`, `redis`, `httpx` (chuyển từ dev lên chính — etl dùng runtime), `beautifulsoup4` (parser OMO; markup viết tay, BS4 khoan dung lỗi HTML hơn parser strict). Múi giờ bằng `zoneinfo` + `tzdata` (đã có).

## 6. Test — seam dự kiến (danh sách chốt lại ở plan, theo [CLAUDE.md §4.5](../../../../CLAUDE.md))

Nguồn ngoài (socket, HTTP SBV/BVSC) mock bằng **literal đã ghi trong tài liệu nguồn**; ClickHouse/Postgres test dùng container thật như bộ test hiện có ([test-strategy.md](../../../20-design/test-strategy.md)). Hai seam "ghi trước cho plan ingester" của spec ClickHouse §9 (**ép kiểu + timezone**, **trường lạ**) được thực thi tại đây.

| Seam | Kiểm gì | Case biên tối thiểu |
|---|---|---|
| Parse packet EIO3 | Chuỗi frame literal (`0{…}`, `40`, `42["t",{…}]`, `43 ack`, `2`) → sự kiện đúng loại đúng payload | packet lạ không crash · frame `42` payload không phải JSON → log + bỏ |
| Dựng lệnh subscribe | Danh mục N mã → các frame `42<ackId>["get",…]` đúng envelope sails.io, chia lô đúng | unsubscribe đúng op |
| Hợp nhất danh mục | Fixture 2 response literal (`/quotes` có `VFMVF1` + StockType đủ 4 loại; `/datafeed/instruments` có phái sinh) → tập topic đăng ký đúng: cổ phiếu+ETF × 3, không CW/trái phiếu/phái sinh, 15 idx, 3 ptm | mã chỉ có một bên xử lý đúng cả hai chiều |
| Ép kiểu + timezone (seam ghi trước §9) | `"42100.0"` → Decimal; `"215271860.0"` → UInt; `"100.005"` → chuẩn hoá scale 2 + metric; `TD`+`FT` giờ VN, assert `TD == toDate(ts)`; `LS` giây vs `t` ms; Decimal không qua float | frame qua nửa đêm giả lập assert bắt được · `CV != P1` → log |
| Trường lạ (seam ghi trước §9) | Frame `i` có trường ngoài 34 → vào `extra` JSON đúng; frame không lạ → `extra=''`; khoá lạ `t`/`o` đếm + log không lưu | `MKI`/`IAC` của ptm vào `extra` |
| Ghép delta + state | Chuỗi frame `i` literal → HASH đúng trường đổi, trường cũ giữ; khởi tạo nền từ instruments literal | frame chỉ mang định danh (không trường nào đổi) không phá state |
| Dedup hash nội dung | Cùng frame đẩy 2 lần trong cửa sổ → 1 dòng vào buffer; frame khác 1 trường → 2 dòng | cửa sổ trượt đẩy khoá cũ ra (frame lại sau khi hết cửa sổ vẫn ghi — chấp nhận, lưới block CH đỡ tầng dưới) |
| `received_at` đơn điệu | 2 frame cùng mã cùng ms → received_at thứ hai = thứ nhất + 1 ms; khác mã không ảnh hưởng nhau | đồng hồ lùi (giả lập) vẫn đơn điệu |
| Writer flush (CH thật) | Buffer 3 bảng có dòng → flush → đủ dòng, đúng kiểu; retry nguyên block → không nhân đôi (lưới block đã có ở schema) | block độc: 1 dòng tràn Decimal → chia đôi đệ quy, dòng hỏng log, dòng lành ghi đủ |
| Leader lock (Redis thật) | Giành → renew → tiến trình 2 không giành được; TTL hết → tiếp quản | renew không đè khoá của id khác |
| Đối chứng §5.7 (CH thật) | Bộ tick literal giải tay: khớp → OK; thêm dòng đôi → P1; xoá bớt quá 0,1% → P2 | lệch dưới 0,1% → chỉ metric |
| File đo JSONL | Frame → dòng JSONL đúng format, xoay file theo giờ | payload giữ nguyên văn (round-trip bằng đúng byte JSON) |
| OMO: cổng WAF | Body 246 byte "Request Rejected" → fail, không ghi staging; body thật thiếu chuỗi mốc → fail | body ≥100 KB có mốc → qua |
| OMO: parser | HTML fixture thật (phiên đầu crawl được, cắt gọn) → đúng bảng [sbv-omo.md §5](../../../10-sources/macro/sbv-omo.md): 4 dòng `Mua kỳ hạn` 7/35/63/91, `6.307,47` tỷ → `6.30747e12` VND, `4/4` tách đúng, tổng khớp | nhóm lạ → fail · số cột ≠ 4 → fail · `float()` thẳng phải fail test số Việt |
| OMO: writer (PG thật) | Phiên mới → 3 nơi có dòng trong 1 transaction; chạy lại cùng ngày → skip không ghi đè; etl_run đóng đúng status | fail giữa chừng → transaction rollback, etl_run failed |
| OMO: flow rebuild (PG thật) | Giải tay step-04 §5.4: D bơm 6.307,47 tỷ kỳ hạn 7; D+7 bơm 5.000 tỷ → `maturing(D+7)=6.30747e12`, `net(D+7)=−1.30747e12`; `complete=false` khi `price_daily` rỗng | rebuild 2 lần → kết quả y hệt (idempotent) · nhóm `outright_sale` đảo dấu |

## 7. Tiêu chí nghiệm thu (bất biến, kiểm được trên máy khác)

- **AC1** — `uv run pytest` toàn backend xanh (bộ cũ 37+29 + bộ mới của lát này), trên Postgres/ClickHouse container thật.
- **AC2** — Ngoài giờ giao dịch: `python -m ingester --measure` nối được socket thật, ack subscribe về, tự reconnect khi bị ngắt, ghi file JSONL hợp lệ (phiên đóng cửa: 0 frame dữ liệu là kết quả hợp lệ).
- **AC3** — Một **phiên đo trọn** đã chạy, báo cáo nằm ở `docs/90-records/surveys/`, `11-bvsc-realtime.md` + roadmap §5.1 cập nhật, luật SM/dedup chốt có chữ ký chủ dự án trong ledger.
- **AC4** — Sau gate AC3: một **phiên ghi thật trọn** trên máy này — cả 5 bảng frame có dữ liệu ngày đó, `bar_1m_v`/`index_bar_1m_v` có nến, đối chứng cuối phiên không P1 và không P2 (hụt < 0,1%), log không còn block độc chưa xử lý; số đo tuần đầu bắt đầu ghi vào [spec ClickHouse §10](../2026-08-25-clickhouse-realtime-store/spec.md).
- **AC5** — Job OMO chạy thật ít nhất một phiên: `omo_session` + `omo_auction` + `staging.raw_payload` + `ops.etl_run` đủ; chạy lại cùng ngày không đổi gì; `omo_flow` khớp giải tay.
- **AC6** — Task Scheduler đã đăng ký: ingester theo phiên (ngày làm việc) + OMO 4 mốc/ngày; lệnh/hướng dẫn đăng ký nằm trong repo.

AC2/AC5 kiểm được bất kỳ lúc nào; AC3/AC4 phụ thuộc giờ giao dịch — plan xếp chúng thành mốc riêng, các task khác không chờ.

## 8. Ngoài phạm vi (ba loại theo [CLAUDE.md §1.4](../../../../CLAUDE.md))

| Mục | Loại | Ghi chú |
|---|---|---|
| Tick phái sinh ghi vào kho | **chưa đo được** | Phiên đo của lát này chính là phép đo; có kết quả thì bổ sung bảng/cột bằng migration mới + mở rộng danh mục — việc của lát sau |
| `api` / SSE / đọc ClickHouse phục vụ user | đã có đường khác | [service-topology §7](../../../20-design/service-topology.md): dựng sau khi kho có dữ liệu |
| ETL REST (giá EOD, snapshot, screener, BCTC…) | đã có đường khác | Việc [6]/[7] roadmap — lát sau |
| Health/metrics HTTP cổng 8100, Prometheus | loại có chủ đích | §1 — log + exit code đủ cho lát đầu |
| Docker hoá ingester, entry compose `deploy/app` | loại có chủ đích | Quyết định #7 — khi deploy Linux |
| Backfill OMO 60 ngày từ Vietstock | loại có chủ đích | Cần đăng nhập ([sbv-omo.md §10](../../../10-sources/macro/sbv-omo.md)); cân nhắc riêng khi chủ dự án quyết dùng tài khoản |
| Chuông báo động (email/telegram) cho P1/P2/WAF | loại có chủ đích | Cơ chế cảnh báo chung dựng cùng bộ giám sát hợp đồng (ETL 3b) |

## 9. Checklist quét tài liệu sống khi thực thi ([CLAUDE.md §1.7](../../../../CLAUDE.md))

- [ ] `docs/90-records/README.md` — thêm dòng plan này; **sửa hai dòng lệch sẵn** (thiếu `2026-08-25-clickhouse-realtime-store`; `postgres-data-schema` còn ghi "đang duyệt" dù đã xong)
- [ ] `.env.example` — thêm khối biến §5
- [ ] `backend/pyproject.toml` — phụ thuộc §5
- [ ] `backend/README.md` — cách chạy ingester (3 chế độ) + job omo + đăng ký Task Scheduler
- [ ] Sau phiên đo: `11-bvsc-realtime.md` (kèm ngày đo) · `roadmap.md` §0/§5.1 · spec ClickHouse §10 (điền số đo tuần đầu khi có)
- [ ] Sau khi ghi thật ổn định: `roadmap.md` §0 (dòng "Code sản phẩm ❌") + §2 việc [4] đánh dấu tiến độ
- [ ] `sbv-omo.md` — điền giờ đăng bài thật sau tuần đầu (kèm ngày đo)
- [ ] `git grep` các tên/khoá mới (`rt:state:`, `rt:pub:`, `CLICKHOUSE_INGESTER_URL`, `ETL_DATABASE_URL`) khi đổi — mỗi sự thật một chủ
