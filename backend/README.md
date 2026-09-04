# backend — API · ETL · Ingester

**Stack đã chốt:** Python + FastAPI *(2026-08-24, [ADR 0007](../docs/00-overview/decisions/0007-monorepo-layout-and-stack.md))*. Ba khối chạy như process riêng nhưng dùng chung models/clients trong package này:

| Khối | Vai trò |
|---|---|
| `api` | REST + SSE + chatbot function calling |
| `etl` | Thu thập theo lịch từ 9 nguồn — xem [`docs/10-sources/`](../docs/10-sources/README.md) |
| `ingester` | Realtime BVSC, tick thô + sổ lệnh + nến 1', ghi batch vào ClickHouse |

**Đang có:** [`agent/skills/`](agent/skills/) — hai skill sản phẩm `vn-stock-advisor` · `vn-stock-knowledge` (3.046 dòng, đã test 6 vòng). ⚠️ **Trước khi sửa bất cứ gì trong đó, bắt buộc đọc [`docs/30-skills/maintenance.md`](../docs/30-skills/maintenance.md).** `agent/` sau này chứa luôn system prompt và glue function-calling.

**Trạng thái phần code:** `ingester` (socket BVSC → Redis + ClickHouse) · job `etl omo` (crawl OMO của SBV → Postgres) · job `etl refdata` (danh bạ + danh mục mã + cây ICB → Postgres, [hồ sơ](../docs/90-records/plans/2026-08-26-reference-data-etl/)) · job `etl screener` (52 trang `GetScreenerItems` → `market.screener_daily`, [hồ sơ](../docs/90-records/plans/2026-09-03-screener-daily-etl/)) · job `etl events` (sáu họ `Calendar/GetCorporate*` → `market.corporate_event`, [hồ sơ](../docs/90-records/plans/2026-09-03-events-daily-etl/)) · job `etl price` (`getPriceData` trang 1 mọi cổ phiếu niêm yết + backfill có con trỏ → `market.price_daily`, [hồ sơ](../docs/90-records/plans/2026-09-03-price-daily-etl/)). Hồ sơ lát ingester/OMO: [`docs/90-records/plans/2026-08-26-ingester-omo-first-slice/`](../docs/90-records/plans/2026-08-26-ingester-omo-first-slice/). `api` chưa bắt đầu.

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

## Chạy job price (giá theo ngày)

```bash
cd backend
set -a; . ../.env; set +a; PYTHONIOENCODING=utf-8 uv run python -m etl price                      # hằng ngày: trang 1 (60 phiên) mọi cổ phiếu niêm yết
set -a; . ../.env; set +a; PYTHONIOENCODING=utf-8 uv run python -m etl price --codes BID,VHM       # chỉ vài mã — chạy thử dưới quyền production, hoặc re-crawl theo sự kiện quyền
set -a; . ../.env; set +a; PYTHONIOENCODING=utf-8 uv run python -m etl price --backfill --stop-before-open   # lùi trọn lịch sử (~12,5 năm), dừng trước 08:45 ngày giao dịch kế — đây là lệnh của task dlck-price-backfill
```

Cần `ETL_DATABASE_URL` (user thuộc role `dlck_etl`). `Code` gửi cho FiinTrade là **`organCode`** tra qua
`issuer_external_id('fiintrade')` — 41 % mã có `organCode ≠ ticker`, gửi ticker là nhận `Code not valid`.
Ghi `market.price_daily` UPSERT theo `(security_id, trading_date)`: **5 cột** (`close_adj` ← `closeValue`,
**`close_raw` ← `closePrice` — giá thô lịch sử, điền một lần rồi không đè**, O/H/L) + `raw.fiintrade` giữ nguyên
99 trường; dòng có payload không đổi được **bỏ qua** nên `stats.rows_changed` của lượt chạy lại phải là 0.
Hồ sơ và ba quyết định thiết kế (tuần tự thay vì 8 luồng · `close_raw` từ `closePrice` · không mở cột mới):
[`docs/90-records/plans/2026-09-03-price-daily-etl/`](../docs/90-records/plans/2026-09-03-price-daily-etl/).

| Chế độ | Sổ `ops.etl_run.job` | Giao dịch | Guard |
|---|---|---|---|
| hằng ngày | `market.price_daily` | một giao dịch cho cả lượt, guard **trước** commit | (0) không mã nào có dữ liệu · (i) mã sai + mã hỏng > 2 % · (ii) số mã có dữ liệu sụt > 2 % so lượt success toàn tập gần nhất · (iii) ngày mới nhất ở tương lai · (iv) ngày mới nhất lùi so mốc |
| `--backfill` | `market.price_backfill` | mỗi mã một giao dịch; `stats.cursor` ghi sau từng mã (mã hỏng/sai **vẫn đẩy con trỏ đi** — làm lại ở vòng sau, dấu vết ở `failed_tickers`/`invalid_tickers`) | không guard tổng — chỉ ngắt khẩn khi **10 mã liên tiếp** hỏng; vẫn đếm `dup_dates` và `raw_close_mismatch` từng mã |

Bốn bộ đếm "không có dữ liệu" của lượt hằng ngày, đều nêu tên ≤ 20 mã: `invalid` (nguồn trả `Code not valid`) ·
`failed` (hỏng sau 3 retry, kể cả timeout/đứt kết nối) · `empty` (trả `Success` nhưng 0 phiên) · `no_organ_code_count`
(cổ phiếu niêm yết chưa có `issuer_external_id('fiintrade')` — không gọi được, không tính vào `codes`). Bất biến:
`with_data + empty + invalid + failed = codes`; guard (i) cộng ba số giữa vào tử số.

**Máy ngủ theo lịch (02:00) giữa lượt — job sống qua được, thiết kế cho đúng ca này** *(chủ dự án đặt lịch ngủ đêm;
máy không tự ngủ vì nhàn rỗi)*. Sự cố 2026-09-04 02:00 lộ ba chỗ hở, nay đóng cả ba: (1) lời gọi HTTP treo qua giấc
ngủ thức dậy thành `httpx.ReadTimeout` — từ `e7f80f6` được thử lại 3 lần như response xấu; (2) kết nối Postgres nằm
trong pool suốt 38 phút fetch chết sau giấc ngủ — `pool_pre_ping=True` thay nó trước khi dùng; (3) ngân sách
`--max-minutes` tính theo **đồng hồ tường**, giờ ngủ vẫn tính ⇒ thức dậy là dừng sau mã đang dở, không chạy lấn vào
giờ giao dịch; con trỏ đã lưu sau từng mã nên lượt sau nối tiếp. Giữ máy thức bằng `SetThreadExecutionState` **không** dùng được: nó chỉ chặn ngủ do nhàn rỗi, không chặn được lệnh
suspend theo lịch.

**Backfill chạy bằng task Scheduler `dlck-price-backfill`, không chạy tay trong phiên chat** *(quyết định chủ dự án
2026-09-04)*: lệnh `etl price --backfill --stop-before-open`, trigger **thứ 7 00:05**, giới hạn chạy 3 ngày, đăng ký
`Disabled` cùng cả đội. Hai cách dùng: kích hoạt tay buổi tối bất kỳ (`Start-ScheduledTask dlck-price-backfill`) —
`--stop-before-open` tính hạn **08:45 của ngày giao dịch kế tiếp** ngay lúc bắt đầu nên tối thứ 3 dừng trước phiên
sáng thứ 4; hoặc bật task để tự chạy thứ 7 và đi liền tới sáng thứ 2 (~20 giờ đủ trọn vòng). Máy ngủ 02:00 giữa
chừng: job sống qua và chạy tiếp tới hạn; con trỏ nối các lượt. ⚠️ Hết vòng (`pass_complete`) thì lượt kế là **vòng
mới** — làm mới toàn bộ chuỗi điều chỉnh (~20 giờ gọi mỗi cuối tuần): giữ task bật nếu muốn làm mới định kỳ, tắt
nếu chỉ cần một vòng rồi re-crawl theo sự kiện quyền bằng `--codes` (lát 4). Tiến độ: `stats.cursor` /
`codes_done` / `stop_at` của job `market.price_backfill` trong `ops.etl_run`.

Lượt `--codes` ghi `stats.subset = true`: **không** làm mốc cho guard (ii)/(iv), **không** đụng
`data_domain_state('market.price')`, **không** dời con trỏ backfill. Backfill hết vòng (`pass_complete`)
thì lượt kế bắt đầu vòng mới từ mã đầu — log ghi rõ. `stats.raw_close_mismatch` phải là **0**: đó là
mắt của luật điền-một-lần `close_raw`; khác 0 là nguồn đã sửa hồi tố giá thô, xem tên mã trong
`raw_close_mismatch_sample`.

Bốn điều nguồn làm mà tài liệu cũ không nói *(đo 2026-09-03, [`09-fiin-market-price.md`](../docs/10-sources/market/09-fiin-market-price.md))*:
`status` trả lẫn `0` và `"Success"` (job nhận cả hai) · `FromDate`/`ToDate` bị bỏ qua · nhóm dòng tiền theo
nhà đầu tư điền trễ **T+1** (trang 1 = 60 phiên nên lượt hôm sau tự vá) · ngày nghỉ không có dòng (chạy ngày lễ
là idempotent, không cần vế "có phiên không" như Screener).

## Chạy job snapshot (họ hồ sơ doanh nghiệp)

```bash
uv run python -m etl snapshot                       # lượt bình thường: trigger + quét sàn cuốn chiếu
uv run python -m etl snapshot --codes A32,BAB       # ép một tập mã, mọi kind, bỏ qua nhịp và quota
uv run python -m etl snapshot --kinds dividend      # chỉ một vài kind
uv run python -m etl snapshot --max-minutes 5       # trần thời gian, dừng sau target đang dở
```

Bốn kind `snapshot` · `valuation` · `ownership` · `dividend` vào `market.snapshot_daily`. Ngân sách **234 lời gọi/ngày**
(quota 24 + 70 + 70 + 70), phần fetch ~2 phút.

**Kho chỉ nhận dòng KHI NỘI DUNG ĐỔI** — họ này không có trường nào đổi theo ngày. Phép so tính hash trên
**danh sách trắng theo kind**, cố tình bỏ ngoài mọi trường tính từ giá (`rtd11` `rtd21` `rtd25`,
`priceEarningRatio`, `dividendYield`): hash trọn payload thì ngày nào cũng "đổi". Payload vẫn lưu **trọn** vì bốn
endpoint chỉ trả giá trị hiện tại, không backfill được — trường không lưu hôm nay là mất vĩnh viễn.

**Không có con trỏ, và không cần:** `ops.snapshot_check.checked_at` chính là con trỏ — lượt sau tự lấy nhóm cũ
nhất chưa tới lượt, nên lượt bị giết giữa chừng không mất chỗ. Bảng này cũng là chỗ **đếm lỗ của lịch sự kiện**:
quét sàn tìm ra thay đổi mà trigger không bắn thì `changed_floor` tăng.

**Hai đồng hồ, đừng trộn** *(bài học trả giá 2026-09-04)*: mốc nước ở `ops.data_domain_state('market.snapshot')`
đo **ngày công bố** (`max(public_date)`) và chỉ tiến khi lượt không có mã nào hỏng hay sai hình dạng — đẩy mốc
khi còn target chưa phục vụ là mất trigger vĩnh viễn. Còn **re-crawl giá** không dùng mốc nước mà theo cửa sổ
`exright_date` trong 3 ngày gần đây, chỉ với `CashDividend`/`StockDividend`/`ShareIssuance` (`AGM` không đụng hệ
số điều chỉnh), trần `MAX_RECRAWL = 50` mã và `RECRAWL_MAX_MINUTES = 20` phút. Lỗi re-crawl **không** kéo đổ lượt
snapshot; mã chưa kịp kéo được cửa sổ 3 ngày bắt lại.

⚠️ **Chưa đăng ký task Scheduler** — lịch của job này thuộc lát 7 (bảng lịch trong container `etl`). Chạy tay,
hoặc để lát 7 gọi. Vị trí trong ngày: **sau `events` 18:10**, vì trigger đọc đúng bảng mà `events` vừa ghi.

## Lịch chạy (Windows Task Scheduler)

```bash
pwsh scripts/register-tasks.ps1
```

Đăng ký **11 task** — 10 task hằng ngày làm việc và `dlck-price-backfill` thứ 7: 4 mốc OMO (11:30 · 15:30 · 18:00 · 21:30) · `dlck-refdata` 08:00 (danh bạ tươi trước phiên) · `dlck-ingester` 08:30 (ghi thật — gate mở 2026-08-26) · `dlck-screener` 15:20 (sau khi ingester đóng 15:05, tránh 15:30 của OMO — đăng ký ở Task 8 của [plan screener](../docs/90-records/plans/2026-09-03-screener-daily-etl/plan.md), để `Disabled` cùng cả đội) · `dlck-events` **18:10** (sau phiên, dùng danh bạ tươi từ 08:00, và **tránh 18:00 của OMO** — cùng lý do đặt `dlck-screener` lệch 15:30; giờ này sửa 2026-09-03 sau khi đăng ký lượt đầu lộ ra va lịch — đăng ký ở Task 7 của [plan events](../docs/90-records/plans/2026-09-03-events-daily-etl/plan.md), để `Disabled` cùng cả đội) · `dlck-price` **15:40** (sau screener 15:20 và OMO 15:30, ~45 phút tuần tự nên xong trước 18:00 của OMO; `-MustNotContain "--backfill"` — task tự động không bao giờ chạy backfill; đăng ký thật 2026-09-04 — AC8 [ledger lát 3](../docs/90-records/plans/2026-09-03-price-daily-etl/ledger.md), để `Disabled` cùng cả đội) · `dlck-price-backfill` **thứ 7 00:05** (`etl price --backfill --stop-before-open`, giới hạn 3 ngày — lùi trọn lịch sử giá tới sáng thứ 2 hoặc tới khi hết vòng; kích hoạt tay buổi tối được, tự dừng trước 08:45 ngày giao dịch kế; đăng ký thật 2026-09-04, để `Disabled` cùng cả đội) · `dlck-ingester-measure` 08:30 (bắt frame thô song song làm lưới an toàn + đường nghiệm thu, thường trực từ 2026-08-27; bản đo giữ 30 ngày, job tự dọn). Bật/tắt tay bằng cmdlet `Enable-ScheduledTask` / `Disable-ScheduledTask`, **không dùng `schtasks.exe`** — xem cảnh báo đầu [`scripts/register-tasks.ps1`](../scripts/register-tasks.ps1).

**Từ 2026-09-04 task chạy `Interactive`** (quyết định chủ dự án — S4U đòi cửa sổ admin mỗi lần thêm task): đăng ký bằng `pwsh scripts/register-tasks.ps1` **không cần admin**; mỗi job hiện một cửa sổ `cmd` có **tiêu đề = tên task** và **một dòng mô tả ngắn** khai trong script (`-Description`: đây là task gì, chạy bao lâu, kết thúc thế nào; tiếng Việt có dấu nhờ `chcp 65001`) — không đường dẫn, không lệnh (output thật của job vào file log). Job giá in thêm một dòng `bắt đầu HH:MM · con trỏ … · còn N mã · hạn HH:MM dd/mm` lúc mở, ghi thẳng ra console (`CONOUT$`, vì output thường đã vào log); xong hay dừng là cửa sổ đóng ngay. **Nút X của cửa sổ bị chính job khoá** lúc khởi động ([`core/console.py`](core/console.py), chỉ khi wrapper đặt `DLCK_LOCK_CONSOLE=1` — chạy tay từ terminal không bị) vì console không thể hỏi lại xác nhận; dừng có chủ đích bằng **Ctrl+C** trong cửa sổ (job `price` ghi `ops.etl_run` = `failed: dừng tay (Ctrl+C)`, thoát mã 130, con trỏ backfill giữ nguyên, cửa sổ đóng ngay — chủ dự án không muốn giữ cửa sổ) hoặc `Stop-ScheduledTask <tên>` (giết tiến trình — lượt treo `running`, đóng tay nếu cần). Task khởi động qua **`conhost.exe`** để mở console cổ điển — trên Windows 11 terminal mặc định là Windows Terminal, cửa sổ thật thuộc `WindowsTerminal.exe` và khoá X không tới được (đo 2026-09-04). Job cũng **tắt QuickEdit** của console lúc khởi động (`SetConsoleMode`): bật QuickEdit thì bấm chuột vào cửa sổ là vào chế độ Select — job bị **tạm dừng** và **Ctrl+C thành copy**, không phải ngắt (đo 2026-09-04: chủ dự án Ctrl+C mà job "treo"). Tắt rồi thì bấm vào cửa sổ vô hại và Ctrl+C luôn là dừng. ⚠️ Task S4U cũ chỉ xoá được bằng admin — sau lần dọn 2026-09-04 không còn task S4U nào.
