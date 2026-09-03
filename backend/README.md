# backend — API · ETL · Ingester

**Stack đã chốt:** Python + FastAPI *(2026-08-24, [ADR 0007](../docs/00-overview/decisions/0007-monorepo-layout-and-stack.md))*. Ba khối chạy như process riêng nhưng dùng chung models/clients trong package này:

| Khối | Vai trò |
|---|---|
| `api` | REST + SSE + chatbot function calling |
| `etl` | Thu thập theo lịch từ 9 nguồn — xem [`docs/10-sources/`](../docs/10-sources/README.md) |
| `ingester` | Realtime BVSC, tick thô + sổ lệnh + nến 1', ghi batch vào ClickHouse |

**Đang có:** [`agent/skills/`](agent/skills/) — hai skill sản phẩm `vn-stock-advisor` · `vn-stock-knowledge` (3.046 dòng, đã test 6 vòng). ⚠️ **Trước khi sửa bất cứ gì trong đó, bắt buộc đọc [`docs/30-skills/maintenance.md`](../docs/30-skills/maintenance.md).** `agent/` sau này chứa luôn system prompt và glue function-calling.

**Trạng thái phần code:** `ingester` (socket BVSC → Redis + ClickHouse) · job `etl omo` (crawl OMO của SBV → Postgres) · job `etl refdata` (danh bạ + danh mục mã + cây ICB → Postgres, [hồ sơ](../docs/90-records/plans/2026-08-26-reference-data-etl/)) · job `etl screener` (52 trang `GetScreenerItems` → `market.screener_daily`, [hồ sơ](../docs/90-records/plans/2026-09-03-screener-daily-etl/)) · job `etl events` (sáu họ `Calendar/GetCorporate*` → `market.corporate_event`, [hồ sơ](../docs/90-records/plans/2026-09-03-events-daily-etl/)). Hồ sơ lát ingester/OMO: [`docs/90-records/plans/2026-08-26-ingester-omo-first-slice/`](../docs/90-records/plans/2026-08-26-ingester-omo-first-slice/). `api` chưa bắt đầu.

---

## Chạy `ingester`

Cần: Redis + ClickHouse đang chạy (`docker compose -f deploy/infra/docker-compose.yml --profile realtime up -d`), schema `rt` đã migrate (`python -m core.ch_migrate upgrade`), và các biến `CLICKHOUSE_INGESTER_URL` / `REDIS_URL` trong `.env` (mẫu ở `.env.example`; user ứng dụng tạo per-môi-trường — xem [`database/README.md`](../database/README.md)).

```bash
cd backend                          # luôn đặt PYTHONIOENCODING=utf-8
uv run python -m ingester --measure --minutes 5   # ĐO: ghi frame thô ra file, KHÔNG đụng DB
uv run python -m ingester                          # GHI THẬT: Redis + ClickHouse, tự thoát ~15:05
uv run python -m ingester --reconcile [--date 2026-08-26]   # chỉ đối chứng cuối phiên
uv run python -m ingester --count 20260827 --db    # bộ đếm d[]: replay bản đo dry-run,
                                                    # so expected với count() rt.* thật
```

🔴 **Gate trước khi bật ghi thật:** phải có **một phiên đo trọn trong giờ giao dịch** (08:40–15:05) và chủ dự án duyệt luật `SM`/dedup — [spec §3.5](../docs/90-records/plans/2026-08-26-ingester-omo-first-slice/spec.md). Trước khi qua gate, chỉ chạy `--measure`.

**Bốn chế độ** (`run` mặc định · `measure` · `reconcile` · `count`, `ingester/__main__.py`) đều nối cùng một socket khi có socket; `--measure` thêm 20 topic × mã phái sinh + `pth` (câu hỏi đo còn treo — [roadmap §5.1](../docs/00-overview/roadmap.md)). File đo là JSONL gzip theo giờ trong `INGESTER_MEASURE_DIR`. `--count` là công cụ **offline, không nối socket** — replay lại `frames-*.jsonl[.gz]` của một ngày đo qua đúng `process_record` mà `run` dùng (dry-run, không ghi DB) để tính số dòng kỳ vọng mỗi bảng, đối chứng bằng số với kho thật khi thêm `--db` ([spec tràn-ra-đĩa §11](../docs/90-records/plans/2026-08-28-ingester-spill-to-disk/spec.md)); nhận `--from`/`--to` để cắt cửa sổ theo `received_at`, mặc định trọn ngày suy từ đối số đầu.

🔴 **Đối chứng `--db` phải cắt `--to` về đúng vòng đời tiến trình `run` — đừng dùng mặc định trọn ngày.** Job đo và job ghi không đóng cùng lúc (`SESSION_END_MEASURE` 15:10 sau `SESSION_END_RUN` 15:05), nên cửa sổ trọn ngày tính cả frame mà bản đo bắt được **sau khi tiến trình ghi đã thoát**. Nó hiện ra thành thâm hụt ma ở `index_delta`, vì đợt tính lại chỉ số ATC bắn ngay sau giờ đóng. Lấy mốc cắt từ chính kho:

```bash
docker exec infra-clickhouse-1 clickhouse-client --password "$CLICKHOUSE_PASSWORD"   -q "select max(received_at) from rt.quote where toDate(received_at)=today()"
```

rồi truyền vào `--to` dạng **giờ địa phương trần, KHÔNG kèm offset TZ** (`_iso_to_ms` gắn sẵn `Asia/Ho_Chi_Minh`; gõ offset vào sẽ bị nuốt). Ca thật 2026-08-28: cửa sổ mặc định ra `index_delta −15`; cắt `--to "2026-08-28 15:04:59.999"` ra **dư 0 cả 5 bảng**, bốn bảng kia không đổi một dòng.

Chế độ `run` (chạy ghi thật) còn dùng **`INGESTER_SPILL_DIR`** (mặc định `dlck-runtime/spill`, cùng họ `INGESTER_MEASURE_DIR`) — thư mục hàng đợi tràn-ra-đĩa khi RAM chạm trần hoặc ClickHouse trục trặc kéo dài; xem [market-data-store §3.7](../docs/20-design/market-data-store.md) và [spec tràn-ra-đĩa](../docs/90-records/plans/2026-08-28-ingester-spill-to-disk/spec.md).

## Chạy job crawl OMO

```bash
cd backend
uv run python -m etl omo            # một lần chạy, ghi rồi thoát
```

Cần `ETL_DATABASE_URL` (user thuộc role `dlck_etl`). Job idempotent theo **ngày trong tiêu đề bài của SBV**: ngày đã có trong `macro.omo_session` thì bỏ qua, không ghi đè. Bị WAF chặn → `ops.etl_run` ghi `failed`, **không** ghi kho lẫn staging.

## Chạy job refdata (danh bạ + danh mục mã + cây ICB)

```bash
cd backend
uv run python -m etl refdata                  # một lần chạy, ghi rồi thoát
uv run python -m etl refdata --accept-drop    # mở khoá MỘT lượt khi chốt chặn từ chối đúng
```

Cần `ETL_DATABASE_URL` (user thuộc role `dlck_etl`). Idempotent: lượt hai không đổi gì, `updated_at` không bị đụng. Chốt chặn sụt hai tầng — mốc là `ops.etl_run.stats` của lượt success gần nhất; bị từ chối thì rollback trọn, payload bằng chứng vào `staging.raw_payload` (`refdata:*`), và cần `--accept-drop` nếu cú sụt là thật (huỷ niêm yết hàng loạt).

**Ngành hai lớp — luật đã đảo (2026-08-28):** trước đây ETL bị cấm đụng `issuer.industry_id`. Nay ETL **sở hữu** cột đó — mỗi lượt ghi đè theo `market.industry_icb_map` (khớp `icb_code` chính xác trước, không có thì leo `icb_code_path` lấy tổ tiên gần nhất). Lớp tay nằm ở bảng riêng `market.issuer_industry_override`, mà ETL **không đọc, không ghi** — DB đã `REVOKE` cả `SELECT`/`INSERT`/`UPDATE`/`DELETE` của role `dlck_etl` trên bảng đó (migration `0012`). **Đường đọc hợp nhất duy nhất là view `market.v_issuer_industry`** = `COALESCE(override.industry_id, issuer.industry_id)` kèm cột `source` ∈ `manual` | `icb` | `NULL` — đọc thẳng `issuer.industry_id` là bỏ qua lớp tay, đọc thẳng `issuer_industry_override` là chỉ thấy lớp tay.

**Cảnh báo `%d doanh nghiệp không tra được ngành` mỗi lượt là bình thường, không phải hỏng.** Log phát dòng `WARNING etl.refdata_store 24 doanh nghiệp không tra được ngành (cả tay lẫn máy) — để NULL, không chặn job` và stats mang khoá `issuers_without_industry` **ở mọi lượt chạy**. Đây là trạng thái ổn định, không phải hỏng — nhưng **mốc "bình thường" đã đổi**, nên đọc con số phải kèm mốc:

| Mốc | `issuers_without_industry` | Gồm những gì |
|---|---|---|
| Trước 2026-09-03 | **24** *(đo 2026-08-28, [ledger](../docs/90-records/plans/2026-08-27-industry-two-layer-mapping/ledger.md))* | 24 chứng chỉ quỹ/ETF (`com_type_code = 'QU'`, `icb_code = '8985'`) — ETF và quỹ không có ngành theo thiết kế (dòng ICB `8980` "Quỹ đầu tư" cố ý không nạp vào `industry_icb_map`) |
| Từ 2026-09-03 | **541** *(đo 2026-09-03)* | 24 quỹ/ETF **+ 517 issuer tối thiểu** do [`etl events`](../docs/90-records/plans/2026-09-03-events-daily-etl/) đúc cho `organCode` vắng danh bạ (chính sách F7) — chúng không có `com_type_code`, không có `icb_code`, nên không tra được ngành |

🔴 **517 dòng thêm KHÔNG phải hồi quy.** Chúng là doanh nghiệp đã rời sàn hoặc chưa niêm yết, **không có dòng `security` nào trỏ tới** — nên bất biến A vẫn `0` *(kiểm 2026-09-03: 0 issuer thiếu ngành mà có cổ phiếu đang niêm yết)*. Con số vượt **541** đáng kể mới là dấu hiệu có gì đó đổi, và cách kiểm đúng là **chạy lại câu bất biến A**, không phải nhìn tổng:

```sql
SELECT count(DISTINCT v.issuer_id) FROM market.v_issuer_industry v
  JOIN market.security s ON s.issuer_id = v.issuer_id
 WHERE v.industry_id IS NULL AND s.security_type = 'stock' AND s.status = 'listed';
```

**Chốt chặn luật BCTC — khoá `bctc_violations` trong `ops.etl_run.stats`.** Mỗi lượt job đếm số doanh nghiệp vi phạm luật hai chiều `com_type_code` NH/CK/BH ⟺ ngành NGANHANG/CHUNGKHOAN/BAOHIEM (qua `market.v_issuer_industry`), ghi vào `stats["bctc_violations"]`, phát `WARNING etl.refdata_store %d doanh nghiệp vi phạm luật BCTC (com_type_code ⟺ ngành tài chính) — xem market.v_issuer_industry` khi khác 0 — **không chặn job**. Trạng thái khoẻ mạnh là **0**; gặp WARNING này thì tra `market.v_issuer_industry` theo `com_type_code` để tìm đúng doanh nghiệp lệch (thường là mã mới niêm yết gán sai lớp 1, hoặc lớp 2 đè tay vào nhầm ngành tài chính).

## Chạy job screener (bảng sàng lọc theo ngày)

```bash
cd backend
set -a; . ../.env; set +a; PYTHONIOENCODING=utf-8 uv run python -m etl screener
```

Cần `ETL_DATABASE_URL` (user thuộc role `dlck_etl`). Một lượt = 52 trang tuần tự (~2–3 phút), ghi
`market.screener_daily` UPSERT theo `(security_id, trading_date)` — chạy lại trong ngày đè bản của chính
ngày đó, không đẻ dòng mới.

**Hợp đồng mã thoát** — đọc `ops.etl_run` để biết chuyện gì đã xảy ra, đừng đoán từ log:

| Mã | Nghĩa |
|---:|---|
| `0` | ghi xong, `etl_run.status = success`, `data_domain_state('market.scores','fiintrade')` cập nhật watermark |
| `1` | **chốt chặn từ chối** — rollback trọn, 0 dòng ghi; `etl_run.status = failed` với lý do, bằng chứng trang 1 vào `staging.raw_payload` (`screener:page1`). Ngày lễ rơi vào đây và **đó là hành vi đúng** |
| `2` | lỗi thật (thiếu `ETL_DATABASE_URL`, nguồn hỏng sau retry, DB lỗi) — `etl_run.status = failed`, không ghi kho |

🔴 **Nguồn đóng dấu `tradingDate` = hôm nay ngay từ trước mở cửa, với `closePrice = 0`** (đo 2026-09-03).
Chốt chặn vế (i) đòi **≥ 50 % số mã gom được có `closePrice > 0`**; không có vế này thì mỗi ngày nghỉ đẻ
~1.545 dòng ma. Ba vế còn lại: đủ trang · tỷ lệ không ghép được `security_id` ≤ 2 % · tỷ lệ `comGroupCode`
lạ ≤ 2 %.

## Chạy job events (lịch sự kiện doanh nghiệp)

```bash
cd backend
set -a; . ../.env; set +a; PYTHONIOENCODING=utf-8 uv run python -m etl events
```

Cần `ETL_DATABASE_URL` (user thuộc role `dlck_etl`). Một lượt = 9 lời gọi tải TRỌN sáu họ
`Calendar/GetCorporate*` (~2,5 phút), ghi `market.corporate_event` UPSERT theo khoá tự nhiên —
chạy lại trong ngày đè bản của chính lượt đó, không đẻ dòng mới.

Cờ `--accept-new` mở khoá lượt tạo NHIỀU issuer tối thiểu cho mã vắng danh bạ — chỉ dùng cho lượt
backfill đầu tiên (517 issuer, 2026-09-03), phải có người nhìn số trước khi chạy; task tự động
(`dlck-events`) **không bao giờ** mang cờ này.

## Lịch chạy (Windows Task Scheduler)

```bash
pwsh scripts/register-tasks.ps1
```

Đăng ký **9 task**, tất cả hằng ngày làm việc: 4 mốc OMO (11:30 · 15:30 · 18:00 · 21:30) · `dlck-refdata` 08:00 (danh bạ tươi trước phiên) · `dlck-ingester` 08:30 (ghi thật — gate mở 2026-08-26) · `dlck-screener` 15:20 (sau khi ingester đóng 15:05, tránh 15:30 của OMO — đăng ký ở Task 8 của [plan screener](../docs/90-records/plans/2026-09-03-screener-daily-etl/plan.md), để `Disabled` cùng cả đội) · `dlck-events` **18:10** (sau phiên, dùng danh bạ tươi từ 08:00, và **tránh 18:00 của OMO** — cùng lý do đặt `dlck-screener` lệch 15:30; giờ này sửa 2026-09-03 sau khi đăng ký lượt đầu lộ ra va lịch — đăng ký ở Task 7 của [plan events](../docs/90-records/plans/2026-09-03-events-daily-etl/plan.md), để `Disabled` cùng cả đội) · `dlck-ingester-measure` 08:30 (bắt frame thô song song làm lưới an toàn + đường nghiệm thu, thường trực từ 2026-08-27; bản đo giữ 30 ngày, job tự dọn). Bật/tắt tay bằng cmdlet `Enable-ScheduledTask` / `Disable-ScheduledTask`, **không dùng `schtasks.exe`** — xem cảnh báo đầu [`scripts/register-tasks.ps1`](../scripts/register-tasks.ps1).
