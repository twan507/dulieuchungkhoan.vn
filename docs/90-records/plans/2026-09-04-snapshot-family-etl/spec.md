# Spec — `etl snapshot`: lát 4 của [7] ETL REST hằng ngày

**Ngày:** 2026-09-04 · **Nhánh:** `feat/snapshot-family-etl` · **Trạng thái:** chờ chủ dự án duyệt

Hồ sơ kèm: [số đo](measurements.md) · [bản thô](measurements-raw.json) · [mẫu payload](samples/)

---

## 1. Vì sao lát này, và lát này là gì

Lát 4 theo [luật thứ tự](../../../00-overview/roadmap.md) chốt 2026-09-04 — đi từ trên xuống, không nhảy lát. Lát 2 (lịch sự kiện) đã mở khoá đúng thứ nó chặn: **tín hiệu kích hoạt**.

Lát này dựng job `python -m etl snapshot` nạp **họ Snapshot** — bốn kind `snapshot` · `valuation` · `ownership` · `dividend` — vào `market.snapshot_daily`, theo kiến trúc **hai lớp** mà [market-data-store §4.1b](../../../20-design/market-data-store.md) đã chốt: lịch sự kiện bắn trigger (đường nhanh, phủ 96–100%), quét sàn định kỳ bắt phần lịch bỏ sót (lưới, **và là thước đo lỗ của lịch**).

Điểm khác mọi lát trước: **họ này không có nội dung đổi theo ngày**. Soi 18 trường ta lưu cho thấy không trường nào là chuỗi thời gian — nên chạy mọi mã mỗi ngày là ghi lại cùng một thứ 250 lần một năm. Ngân sách vì thế xuống **234 lời gọi/ngày** (quota §5.4; ước lượng thô từ nhịp là 231) thay vì ~6.000 của bản thiết kế 2026-08-14.

## 2. Dữ kiện đã đo vs giả định *(§4.8 bước 0 — bắt buộc)*

### 2.1 Đã đo — 38 lời gọi thật, 2026-09-04

Chi tiết và bằng chứng: [measurements.md](measurements.md). Bốn điều quyết định thiết kế:

1. **`status` trong cùng họ có ba giá trị** — `GetSnapshot` (ngân hàng) trả `0`, `GetSnapshotNoneBank` trả `"Success"`, `GetValuation` hỏng trả `"Failed"`.
2. **`"Failed"` = lỗi Redis phía nguồn**, đã được [quy ước §10.5](../../../10-sources/market/00-conventions.md) phân loại là lỗi tạm thời từ 2026-08-15; lượt hỏng tốn **12,3 giây**.
3. **Trường phái sinh từ giá có ở cả `snapshot` lẫn `dividend`** — bốn phép đối chứng với `price_daily` của lát 3 khớp tới 5–6 chữ số.
4. **Hình dạng `dividend` trong tài liệu nguồn là sai** — 5 chỉ tiêu là object `ratioYears` 9 năm, không phải số. Đã sửa tầng reference cùng ngày (`fad9b6b`).

### 2.2 Giả định — CHƯA kiểm, ghi để người sau biết mình đứng trên gì

| Giả định | Vì sao chưa kiểm được hôm nay | Bắt bằng gì |
|---|---|---|
| Ba kind `ownership` · `valuation` · `dividend` **không jitter ngày-qua-ngày** ngoài các trường đã loại | Muốn biết chắc phải có hai ngày, hôm nay mới có một | **AC5** — chạy lại hôm sau, `changed` phải bằng 0 |
| `rtd35` và `vnIndexEquityRisk` trong `valuation` là số theo thị trường ⇒ jitter | Chưa có hai điểm thời gian | Đã **loại khỏi tập hash** từ đầu; AC5 kiểm ngược lại |
| Nhịp gọi ~234 lời gọi/ngày an toàn | Lát 3 đo 1.523 lời gọi ~40 request/phút không tín hiệu chặn — lát này thấp hơn 6 lần | AC3 |
| `majorShareHolders`/`boardOfDirectors` đổi khi có công bố sở hữu thật | Không có nguồn thứ hai để đối chiếu | Đếm `changed_by_floor` qua vài tháng |

## 3. Phạm vi

### 3.1 Trong phạm vi

- Job `python -m etl snapshot` (`--codes` · `--kinds` · `--max-minutes`), 5 module theo khuôn lát 1–3.
- Migration `0016`: bảng `ops.snapshot_check` + thêm `'market.snapshot'` vào CHECK của `ops.data_domain_state`.
- Danh sách tới hạn hai nguồn: trigger từ `market.corporate_event` + quét sàn cuốn chiếu theo quota ngày.
- Ghi `market.snapshot_daily` **khi nội dung đổi**; mọi lượt kiểm cập nhật `ops.snapshot_check`.
- Re-crawl giá theo sự kiện quyền bằng đường có sẵn của lát 3.
- Cập nhật tài liệu sống theo checklist §8.

### 3.2 Ngoài phạm vi — phân ba loại *(§1.4)*

| Mục | Loại | Lý do |
|---|---|---|
| Hai kind `company_score`, `rate_indicator` | **Loại có chủ đích** | Điểm chữ và cờ 0/1 của bên thứ ba — đã bỏ khỏi lược đồ ở migration `0015` |
| `snapshot.quarterly[]` / `yearly[]` (mã `bsa*` `isa*` `cfa*`) | **Đã có đường khác** | Là dữ liệu BCTC — thuộc **lát 5**, nạp từ `getCorporateEarning`; ở lát này chúng vẫn nằm trong payload lưu trọn, chỉ không bóc ra bảng riêng |
| `valuation.valuationSector.valuationStocks[]` (46 mã cùng ngành ở A32) | **Đã có đường khác** | Danh sách so sánh theo ngành — cây ngành đã có từ lát refdata; giữ trong payload, không bóc |
| Đăng ký task Windows cho job này | **Loại có chủ đích** | 11 task đang `Disabled` theo [4d]; lịch chuyển vào bảng lịch của **lát 7**. Lát này chạy tay hoặc do lát 7 gọi |
| **Máy dò sở hữu bằng Screener** *(diff `corpOwnership`/`organizationOwnership`/`freeFloatRate` ngày-qua-ngày để bắn trigger cho `ownership`)* — [market-data-store §4.1b](../../../20-design/market-data-store.md) có nêu | **Hoãn có lý do** | Thêm một cơ chế dò thứ hai trước khi biết quét sàn tháng có đủ hay không là tối ưu hoá mù. **Điều kiện làm:** sau 2–3 tháng, nếu `changed_by_floor` của `ownership` cao (nhiều thay đổi chỉ quét sàn mới thấy) thì dựng máy dò; nếu thấp thì nhịp tháng là đủ và mục này khép hẳn |
| ETF/quỹ | **Đã kiểm — không có** | Truy vấn `com_type_code='QU'` không trả mã nào có security niêm yết dạng stock ⇒ tự rơi khỏi vũ trụ, không cần luật riêng |

## 4. Bốn quyết định theo §4.8 — phương án, lý do loại, điều kiện đảo ngược

### 4.1 Ghi khi ĐỔI + sổ kiểm riêng *(chủ dự án chọn 2026-09-04)*

| Phương án | Tối ưu trục | Lý do loại |
|---|---|---|
| **A · ghi khi đổi + `ops.snapshot_check`** ✅ | đúng nghĩa dữ liệu | — chọn |
| B · ghi mọi lượt kiểm | ít code nhất | ~200 MB/năm dòng trùng lặp chỉ riêng `ownership`; "đã kiểm chưa" và "có đổi không" trộn một bảng ⇒ không đếm được lỗ lịch |
| C · ghi khi đổi, không sổ kiểm | ít bảng nhất | danh sách tới hạn phải dựng bằng cách đọc `jsonb` của `etl_run`; lượt `failed` làm lệch; số đếm lỗ lịch không có chỗ cố định |

**Đảo ngược khi:** có tiêu thụ thật cần trả lời *"ngày X trường Y bằng bao nhiêu"* mà không muốn nội suy từ lần đổi gần nhất ⇒ chuyển sang B, dữ liệu cũ vẫn dùng được vì A là tập con của B.

### 4.2 Quét sàn cuốn chiếu trong chính job hằng ngày *(chủ dự án chọn 2026-09-04)*

| Phương án | Tối ưu trục | Lý do loại |
|---|---|---|
| **A · cuốn chiếu theo quota ngày** ✅ | không đỉnh tải, một mốc lịch | — chọn |
| B · tách `--scan` chạy tháng/quý | rành mạch khái niệm | đỉnh ~4.500 lời gọi một lượt, thêm mốc lịch phải quản, cửa sổ chạy dài dễ đụng giờ |
| C · lô cố định N mã/ngày | code đơn giản nhất | nhịp theo kind không đảm bảo; mã vừa fetch theo trigger vẫn bị quét lại đúng lượt |

**Đảo ngược khi:** ngân sách ngày vượt ~400 lời gọi (thêm kind, hoặc vũ trụ mã tăng) ⇒ tách quét sàn ra lượt riêng ngoài giờ.

### 4.3 Hash trên DANH SÁCH TRẮNG của tập giữ

| Phương án | Tối ưu trục | Lý do loại |
|---|---|---|
| **A · danh sách trắng theo kind** ✅ | bán kính hỏng nhỏ | — chọn: trường mới ở nguồn không tự sinh báo động giả |
| B · danh sách đen (hash cả payload trừ trường đã biết jitter) | ít phải bảo trì | nguồn thêm một trường theo giá là mọi mã báo đổi, im lặng |
| C · hash trọn payload | không phải nghĩ | đo được: `rtd11`/`rtd21`/`rtd25`/`priceEarningRatio` đổi mỗi ngày ⇒ 100% mã "đổi" mỗi lượt |

**Tập trắng theo kind** *(payload vẫn lưu TRỌN — bốn endpoint chỉ trả giá trị hiện tại, không backfill được; trường không lưu hôm nay là mất vĩnh viễn)*:

| Kind | Vào hash | Cố ý ngoài hash |
|---|---|---|
| `snapshot` | 18 trường của [market-field-selection §5.1](../../../20-design/market-field-selection.md) | `rtd11` `rtd14` `rtd21` `rtd25` `rtd53` · `highestPrice1Year` `lowestPrice1Year` · `averageMatchVolume1Month` · `foreignerPercentage` `foreignerRoom` `freeFloatRate` |
| `dividend` | `cashDividendPayouts` · `cashDividendPlans` · `dps` · `dividendPayoutRatio` · `eps` | `priceEarningRatio` · `dividendYield` |
| `valuation` | `estimatedEPS` `forecastEPS` `estimatedBookValue` `forcastBookValue` · `riskFreeRate` · `recommendMethod` · `rtd7` · `rtq180` · `outstandingShare` | `rtd14` · `rtd35` · `vnIndexEquityRisk` · `valuationSector` |
| `ownership` | `majorShareHolders` · `boardOfDirectors` · `overviewChartData` · `majorOwnershipsChartData` | — |

**Đảo ngược khi:** AC5 đỏ (còn trường jitter lọt vào hash) ⇒ bỏ trường đó khỏi tập trắng và ghi lý do; hoặc `changed_by_floor` đứng ở 0 suốt 3 tháng trong khi lịch sự kiện vẫn bắn ⇒ tập trắng quá hẹp, đang bỏ sót thay đổi thật.

### 4.4 Thêm domain `'market.snapshot'`

`ops.data_domain_state` khoá chính `(domain, source)`; lát 1 đã chiếm `('market.scores','fiintrade')`.

| Phương án | Lý do loại |
|---|---|
| **A · thêm `'market.snapshot'` vào CHECK** ✅ | — chọn: CHECK vốn là danh sách đóng do dự án tự định nghĩa, thêm một giá trị là một dòng SQL |
| B · dùng chung dòng của screener | hai job đè watermark của nhau ⇒ con số vô nghĩa, và không job nào biết mình đang đọc mốc của ai |
| C · mượn `'market.fundamentals'` | lát 5 (BCTC) sẽ đụng lại đúng chỗ này — chỉ dời va chạm sang tương lai |

**Đảo ngược khi:** không — danh sách đóng, thêm giá trị không phá dữ liệu cũ.

## 5. Job `python -m etl snapshot`

### 5.1 Khuôn — y `events_job.run`, không sáng tạo

`open_run` → fetch → normalize → **guard trước commit** → apply trong một giao dịch → `close_run` → `upsert_domain_state`. Guard từ chối thì `raise` bên trong `engine.begin()` để tự rollback; bằng chứng ghi ở giao dịch riêng.

### 5.2 `snapshot_fetch` — I/O thuần

- Bốn URL theo [measurements §4](measurements.md); `snapshot` chọn endpoint theo `com_type_code`: `NH` → `GetSnapshot`, còn lại → `GetSnapshotNoneBank`.
- `dividend` là endpoint **duy nhất** cần cả `OrganCode` lẫn `Code` (ticker).
- Header `Origin: https://fiinapp.bvsc.com.vn`; giãn cách ≥ 0,5 s giữa hai lần bắt đầu lời gọi.
- Timeout: **30 s** cho `valuation`, 15 s cho ba kind còn lại (đo: lượt hỏng 12,3 s).
- Phân loại kết quả — **hàm thuần `classify(http, body)`**, ba nhánh: `ok` (`status ∈ {0, "Success"}` và `items[0]` có khoá gốc đúng) · `retry` (`status == "Failed"`, HTTP ≠ 200, JSON hỏng, **hoặc exception vận chuyển**) · `bad_shape`.
- Retry 3 lần, backoff 2/4/8 s. **Exception vận chuyển đi cùng đường với response xấu** — bài học 3 của lát 3, nhân bản từ bản đã vá `356cdc9`, không chép từ code lát 1.
- Hết lượt thử ⇒ mã đó **chưa kiểm**: không ghi `snapshot_daily`, không đụng `snapshot_check`, đếm vào `failed`.

### 5.3 `snapshot_normalize` — thuần, không I/O

`unwrap(kind, body)` → `items[0]` hoặc `None`; `keep(kind, item)` → dict theo tập trắng §4.3; `keep_hash(kind, item)` → `sha256` của `json.dumps(keep(...), sort_keys=True, ensure_ascii=False, separators=(",", ":"))`.

### 5.4 `snapshot_store` — danh sách tới hạn và ghi

**`due_list(conn, today, quota)`** — hợp hai nguồn, khử trùng theo `(issuer_id, kind)`:

```
A · trigger   corporate_event có greatest(public_date, exright_date) > watermark
              Earning | ShareIssuance      -> kind snapshot
              CashDividend | StockDividend -> kind dividend
              (ownership và valuation KHÔNG có loại sự kiện nào -> chỉ đi đường B)
B · quét sàn  mỗi kind: issuer chưa có dòng snapshot_check, HOẶC checked_at < now() - nhịp
              ORDER BY checked_at NULLS FIRST, issuer_id   LIMIT quota[kind]
```

| Kind | Nhịp | Quota/ngày | Phủ trọn sàn sau |
|---|---|---|---|
| `snapshot` | 90 ngày | 24 | 64 ngày |
| `ownership` · `valuation` · `dividend` | 30 ngày | 70 mỗi kind | 22 ngày |

Cộng lại **234 lời gọi/ngày** cho phần quét sàn, cộng trigger (vài chục). `NULLS FIRST` khiến lượt đầu tiên (bảng rỗng) đi đúng quota chứ không nổ 6.092 lời gọi.

**Không có con trỏ, và không cần** — khác lát 3. `checked_at` CHÍNH LÀ con trỏ: lượt sau tự lấy nhóm cũ nhất chưa tới lượt. Nên `--max-minutes` chỉ cần dừng sau mã đang dở, không phải lưu gì; lượt bị giết giữa chừng cũng không mất chỗ.

**`apply(conn, results)`** — với mỗi kết quả `ok`:

- hash khác dòng `snapshot_check` cũ (hoặc chưa có dòng) ⇒ `INSERT … ON CONFLICT (issuer_id, trading_date, kind) DO UPDATE` vào `snapshot_daily`, payload **trọn**, `trading_date` = ngày chạy (giờ VN);
- hash trùng ⇒ **không ghi** `snapshot_daily`;
- mọi trường hợp ⇒ upsert `ops.snapshot_check`.

Lượt kiểm đầu tiên của một `(issuer, kind)` tính là **`first`**, không tính `changed` — nếu không thì lượt cold start tự vi phạm chốt chặn (i) *(§4.4.4: điều kiện kiểm không được để hệ thống chạy bình thường tự vi phạm)*.

**Migration `0016`:**

```sql
CREATE TABLE ops.snapshot_check (
  issuer_id  bigint NOT NULL REFERENCES market.issuer,
  kind       text   NOT NULL CHECK (kind IN ('snapshot','valuation','ownership','dividend')),
  checked_at timestamptz NOT NULL,
  keep_hash  text   NOT NULL,
  changed_at timestamptz,
  found_by   text   NOT NULL CHECK (found_by IN ('event','floor')),
  PRIMARY KEY (issuer_id, kind)
);
CREATE INDEX ON ops.snapshot_check (kind, checked_at);   -- phục vụ ORDER BY của due_list

ALTER TABLE ops.data_domain_state DROP CONSTRAINT data_domain_state_domain_check;
ALTER TABLE ops.data_domain_state ADD CONSTRAINT data_domain_state_domain_check
  CHECK (domain IN ('market.reference','market.price','market.fundamentals','market.events',
                    'market.scores','market.index_stat','macro.indicator','macro.omo',
                    'asset','news','market.snapshot'));   -- 10 giá trị cũ giữ nguyên, thêm 1
```

Quyền: `ALTER DEFAULT PRIVILEGES` của migration `0009` đã phủ bảng mới trong schema `ops` — **nhưng vẫn phải kiểm bằng test chạy dưới role `dlck_etl`**, không suy từ việc đọc migration (§3.5, ca thứ ba).

### 5.5 `snapshot_guard` — thuần, đánh giá trước commit

| Chốt | Ngưỡng | Bắt cái gì |
|---|---|---|
| (i) tỷ lệ đổi của nhóm **quét sàn** | > **20%** số mã quét sàn đã kiểm *(bỏ nhóm `first`)* | tập trắng sai · nguồn đổi cách tính · sự cố nguồn |
| (ii) tỷ lệ lời gọi hỏng | > **20%** tổng lời gọi | nguồn đang sự cố ⇒ dừng, đừng ghi nửa vời |
| (iii) tỷ lệ `bad_shape` | > **5%** | nguồn đổi hình dạng response |
| (iv) danh sách tới hạn rỗng | — | **không phải lỗi**: `success` với `checked = 0` |

Từ chối ⇒ toàn bộ lượt rollback, bằng chứng vào `staging.raw_payload` (`endpoint_key = 'snapshot:<kind>:<organCode>'`) ở giao dịch riêng, `etl_run.status = 'failed'`, exit 1.

### 5.6 Re-crawl giá theo sự kiện quyền

Cuối lượt, với mã có `exright_date` mới từ `CashDividend`/`StockDividend`/`ShareIssuance`: gọi `price_job.run(backfill=True, codes=[…])` — đường đã có sẵn của lát 3, **không thêm code trong `price_*`**. Lỗi ở bước này **không** kéo đổ lượt snapshot: bắt riêng, ghi `stats.recrawl = {codes, status}`.

Lý do làm tự động thay vì để chạy tay: chuỗi `close_adj` sai **im lặng** cho tới khi có người nhớ ra.

### 5.7 Lịch và vận hành

Không đăng ký task Windows (§3.2). Chạy tay: `uv run python -m etl snapshot`. Vị trí trong bảng lịch của lát 7: **sau `events` 18:10**, vì trigger đọc đúng bảng mà `events` vừa ghi.

## 6. Seam test *(chốt cùng plan — §4.5.2)*

Expected lấy từ mẫu thật trong [`samples/`](samples/) hoặc giải tay, **không tính lại theo cách code tính** (§4.5.3).

| Seam | Ca phải có |
|---|---|
| `classify(http, body)` | `status=0` → ok *(mẫu `BAB-snapshot-bank-status0.json`)* · `"Success"` → ok · `"Failed"` → retry *(mẫu `BVB-valuation-failed.json`)* · exception vận chuyển → retry · thiếu khoá gốc → bad_shape |
| `keep(kind, item)` | 4 kind × mẫu A32: trả đúng tập trắng, đúng số khoá |
| `keep_hash` | **tính chất, không tautology**: đổi `rtd11` ⇒ hash **không đổi**; đổi `outstandingShare` ⇒ hash **đổi**; thêm khoá lạ vào payload ⇒ hash không đổi |
| `due_list` | trigger-only · floor-only · trùng cả hai chỉ ra một dòng · quota chặn đúng số · bảng rỗng đi theo `NULLS FIRST` |
| `guard.check` | qua · (i) đỏ · (ii) đỏ · (iii) đỏ · (iv) rỗng vẫn `ok` · nhóm `first` không tính vào (i) |
| `apply` | đổi ⇒ 1 dòng; không đổi ⇒ 0 dòng nhưng `snapshot_check.checked_at` vẫn tiến; chạy lại ⇒ idempotent |
| quyền | `test_snapshot_check_works_under_etl_role` — `SET LOCAL ROLE dlck_etl` rồi đọc/ghi thật |

## 7. Tiêu chí nghiệm thu

| | Nội dung | Bằng chứng phải dán |
|---|---|---|
| AC1 | Toàn bộ test xanh | số test trước/sau |
| AC2 | `--codes` 3 mã → 12 dòng, 4 kind | truy vấn đếm theo kind |
| AC3 | Lượt đầy đủ vào kho production | số lời gọi · thời gian · số `retry` · `0` tín hiệu chặn |
| AC4 | Chạy lại **cùng ngày** | `changed = 0`, `rows_written = 0` |
| **AC5** | **Chạy lại NGÀY HÔM SAU, ép đúng tập mã của hôm trước bằng `--codes`: `changed_by_floor = 0`** | `stats` hai lượt liền nhau — phép chứng minh tập trắng đúng. Mã có sự kiện mới trong đêm được loại khỏi phép so, nêu tên trong ledger |
| AC6 | Mã có `exright_date` mới ⇒ re-crawl chạy, `close_adj` đổi | `stats.recrawl` + truy vấn giá trước/sau |
| AC7 | Ép hỏng hàng loạt ⇒ lượt `failed`, 0 dòng ghi | `etl_run` + `staging.raw_payload` |

## 8. Checklist tài liệu sống — cùng lượt với code *(§1.6, §1.7)*

- [ ] [roadmap.md](../../../00-overview/roadmap.md): lát 4 ✅ + viết **"Điểm vào cho lát 5"**; sửa số test; bảng §4.1 ETL.
- [ ] [market-data-store.md](../../../20-design/market-data-store.md) §4.1/§4.1b: nhịp và quota thật, bảng `ops.snapshot_check`.
- [ ] [database/README.md](../../../../database/README.md): migration head `0016`.
- [ ] [backend/README.md](../../../../backend/README.md): cách chạy `etl snapshot`, ba cờ.
- [ ] `git grep` số cũ (`16/54`, `~200–260`) — đối chiếu hoặc sửa mọi chỗ.
- [ ] `ledger.md` trong chính thư mục này, commit theo mốc.

## 9. Điểm cần chủ dự án duyệt tường minh

1. **Quota 24/70/70/70** và nhịp 90/30 ngày — lượt quét trọn sàn đầu tiên vì thế mất **22 ngày** (ba kind tháng) và **64 ngày** (`snapshot`). Muốn phủ nhanh hơn thì nâng quota, đổi lại ngân sách ngày tăng tuyến tính.
2. **`snapshot_daily.trading_date` = ngày chạy job**, không phải ngày thị trường có phiên — vì họ này không gắn với phiên. Chạy vào ngày nghỉ vẫn ghi hợp lệ.
3. **Ba tập trắng của `ownership`/`valuation`/`dividend` là suy luận, chưa đo ngày-qua-ngày** — AC5 là chỗ nó bị kiểm thật, và AC5 chỉ chạy được sau một đêm.
