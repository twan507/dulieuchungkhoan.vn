# Spec — `etl screener`: lát 1 của [7] ETL REST hằng ngày

> ✅ **ĐÃ DUYỆT 2026-09-03** — chủ dự án chốt cả ba điểm §9 theo đúng đề xuất. Viết cùng ngày sau brainstorm (bắt đầu 2026-08-28, nạp lại context 2026-09-03).
>
> ⚠️ **Ràng buộc phát sinh cùng lúc duyệt:** toàn bộ 7 task ghi dữ liệu đã `Disabled` 2026-09-03 ~08:55 (ưu tiên dev — roadmap [4d]). Vì vậy **AC6 đổi**: `dlck-screener` đăng ký + assert xong thì **để `Disabled`**, không bật; *"lượt tự động đầu tiên"* dời tới khi cả đội bật lại. AC3/AC4 (chạy tay một lượt thật dưới `ETL_DATABASE_URL`) vẫn làm — đó là nghiệm thu dev, không phải job định kỳ.

## 1. Vì sao lát này, và lát này là gì

[7] trong [roadmap §3](../../../00-overview/roadmap.md) — *ETL hằng ngày: giá, snapshot, screener, lịch sự kiện* — thực ra là **bốn họ dữ liệu cộng một lớp hạ tầng chưa có** (~6.040 lời gọi/ngày, [`00-conventions §10.1`](../../../10-sources/market/00-conventions.md)). Gói vào một spec thì spec phình và một tiêu chí hỏng chặn cả bốn. Chủ dự án chốt 2026-08-28: **tách thành chuỗi lát, Screener đi trước** vì nó là họ duy nhất mà **đúng tải kế hoạch đã được đo an toàn** (52 lời gọi tuần tự, ~29 request/phút, 2026-08-15) — mọi họ khác đều đòi một giả định về nhịp chưa kiểm.

Lát này: một subcommand `python -m etl screener` ghi **`market.screener_daily`** mỗi ngày giao dịch sau 15:00, y khuôn job `refdata` đã nghiệm thu thật. Đi kèm **một việc tài liệu bắt buộc** (§4) vì không làm thì ETL âm thầm thiếu trường.

## 2. Dữ kiện đã đo vs giả định *(§4.8 bước 0 — bắt buộc)*

### 2.1 Đã đo — hai lời gọi thật, response lưu ở [`samples/`](samples/)

| | 28/08 **sau phiên** (20:51) | 03/09 **trước mở cửa** (08:38, ngay sau nghỉ lễ 31/08–02/09) |
|---|---|---|
| `status` / `totalCount` | `Success` / 1.545 | `Success` / 1.545 |
| Khoá phân biệt / khoá trùng >1 khối | **193 / 27** — khớp tài liệu nguồn | 193 / 27 |
| `priceInfo.tradingDate` | `2026-08-28T15:00:01.533` — **timestamp riêng từng mã**, 29 giá trị khác nhau / 30 mã, 14:45–15:00 | **`2026-09-03T08:22:46`** — đã là hôm nay, dù chưa có phiên |
| `priceInfo.referenceDate` | `2026-08-27` | `2026-08-28` ⇒ HOSE nghỉ 31/08, 01/09, 02/09 |
| `closePrice > 0` | **30/30** | **0/30** |
| `totalVolume > 0` | 20/30 *(mã kém thanh khoản = 0 dù có phiên)* | 0/30 |
| `marketStatus` | `None` ×30 | `None` ×30 — vô dụng |
| Tỷ số tài chính giữa hai lần | — | **đổi** (`financial` 103 giá trị, `stockScreenerItem` 733) dù không có phiên nào ở giữa |
| Khối `null` nguyên khối | `V68.technical = null` | — |
| Giá trị `null` trong khối có mặt | 1.339 / 6.672 = 20,1% | — |
| Kích thước một mã (JSON nén) | 5 khối lồng đủ 193: **4.784 B** · phẳng + tiền tố 223 khoá: 7.984 B | — |
| Body nguồn | `pageSize` **chỉ nhận 30** ⇒ 1.545 mã = **52 trang** | — |
| Tài liệu nguồn thiếu | Response thật có thêm `page`, `pageSize`, `packageId`, `errors` ở tầng đỉnh — [`10-fiin-dictionary`](../../../10-sources/market/10-fiin-dictionary.md) chỉ chép `totalCount, items, status` | — |

**Hệ quả trực tiếp của số đo:**

- `trading_date` **không** thể lấy thô từ `tradingDate` rồi ghi: ngày lễ nguồn vẫn đóng dấu *ngày hôm đó* với giá 0 ⇒ UPSERT theo PK sẽ **đẻ dòng ma cho ngày không giao dịch**. Giả định ban đầu của brainstorm (*"ngày lễ `tradingDate` đứng ở phiên cũ nên UPSERT tự đè"*) **đã bị số đo bác bỏ** — đây là lý do spec có §5.4.
- *"Payload trùng lượt trước ⇒ ngày lễ"* cũng **không dùng được**: tỷ số tài chính đổi hằng ngày kể cả không có phiên.
- Tín hiệu phân biệt dùng được: **`closePrice > 0`** (30/30 vs 0/30). `totalVolume` không dùng được vì mã kém thanh khoản = 0 ngay trong ngày có phiên.
- 27 khoá trùng ⇒ **giữ nguyên khối lồng của nguồn**, không làm phẳng. Phẳng + tiền tố to hơn 66% mà không được gì. *(Số đo trên là của cả 193 khoá, tức 5 khối; sau khi lọc theo `keep` thì chỉ còn hai khối `stockScreenerItem` và `financial` có khoá — xem đính chính §5.3.)*

### 2.2 Giả định — CHƯA kiểm, ghi để người sau biết mình đứng trên gì

1. 🔴 **Ngày lễ lúc 15:20 trông giống trước mở cửa** (`closePrice = 0` toàn thị trường). Đã đo trạng thái *trước mở cửa của ngày có phiên*; chưa đo *trong ngày lễ thật sau 15:00*. Hợp lý — không có phiên thì không có gì để chốt giá — nhưng là suy luận. AC5 biến nó thành cổng: **lượt chạy ngày lễ đầu tiên phải được soi tay.**
2. Nguồn không đổi số trang/kích thước trong lúc phân trang (1.545 mã ổn định trong một lượt 2–3 phút). Guard §5.4 (ii) bắt được nếu sai.
3. 18 mã tỷ số ở §4.2 đúng là nhóm *"giữ"* còn hụt của quyết định 2026-08-14. Suy từ luật đã chốt, **cần chủ dự án xác nhận** (§9).

## 3. Phạm vi

**Trong:** (a) vá bảng chọn trường cho đủ 193/193 khoá Screener; (b) `python -m etl screener` + task Scheduler `dlck-screener`; (c) fixture + seam test; (d) cập nhật tài liệu sống theo checklist §8.

**Ngoài** — phân ba loại *(§1.4)*:

| Mục | Loại | Lý do |
|---|---|---|
| Giải mã nghĩa 13 mã tỷ số chưa có trong từ điển 729 mã | **Đã có đường khác** | Cùng cách đã lấy 729 mã (bundle JS FiinTrade). **Lưu không cần biết nghĩa** — chỉ *dùng* mới cần; ghi `chưa giải mã` trong bảng chọn |
| Nhịp 8 luồng / lớp `core/http` + token bucket dùng chung | **Loại có chủ đích** | 52 lời gọi tuần tự trên một host đã đúng mức đo an toàn. Rút thành lớp chung khi lát giá (1.974 lời gọi, nhiều host) thật sự cần — §4.4.2 cấm abstraction cho code dùng một lần |
| Giá theo ngày · snapshot · lịch sự kiện · [8] giám sát hợp đồng | **Đã có đường khác** | Các lát sau của cùng chuỗi [7] |
| Cột hoá / index từng trường trong `payload` | **Loại có chủ đích** | Chưa có truy vấn thật nào để chọn cột — step-03 §3 đã chốt jsonb, thăng cấp cột khi có nhu cầu đo được |
| Backfill Screener | **Đã kiểm — không có** | Body không nhận tham số ngày; endpoint là ảnh chụp sống. Lịch sử bắt đầu từ ngày lát này chạy |

## 4. Phần A — vá bảng chọn trường cho đủ 193/193

**Chỗ hở.** [`market-field-selection.md`](../../../20-design/market-field-selection.md) liệt kê **127/193** dòng Screener, `keep = 59`. Quyết định 2026-08-14 nói *"giữ 80"*. §7.5 của chính tài liệu đã tiên đoán: *"Screener thiếu 66 mã — không tài liệu nguồn nào liệt kê đủ"*. ETL tra bảng theo `keep=true` sẽ lấy **59**, thiếu **21**, **không có gì báo**.

**Cách vá.** Response thật 28/08 cho tên cả 66 khoá. Sửa [`gen_field_selection.py`](../../../20-design/gen_field_selection.py) bằng đúng khuôn `add(codes, source, nguon_chuan, keep, reason, status, names, block)` sẵn có, rồi chạy lại script — `.md`/`.json` sinh tự động, **cấm sửa tay**.

### 4.1 48 khoá áp được luật đã chốt, không cần quyết

| Nhóm | Số | `keep` | Khoá |
|---|---:|---|---|
| Metadata — không phải chỉ tiêu | 10 | `False`, lý do *"metadata"* | `comGroupCode` `icbCode` `isForecastTime` `marketStatus` `matchType` `organCode` `rateAdjusted` `referenceDate` `ticker` `tradingDate` |
| Trùng BVSC | 29 | `False` | `atoPrice` `atoVolume` `averagePrice` `ceilingPrice` `dealPrice` `dealValue` `dealVolume` `expectedTradePrice` `expectedTradeVolume` `floorPrice` `foreignBuyValueTotal` `foreignBuyVolumeTotal` `foreignCurrentRoom` `foreignSellValueTotal` `foreignSellVolumeTotal` `foreignTotalRoom` `highestPrice` `lowestPrice` `matchPrice` `matchValue` `matchVolume` `openPrice` `percentPriceChange` `priceChange` `referencePrice` `totalDealValue` `totalDealVolume` `totalValue` `totalVolume` |
| Biến động giá — tính lại từ chuỗi giá | 4 | `False` | `percentPriceChange1Year` `percentPriceChange2Month` `percentPriceChange2Week` `percentPriceChange9Month` |
| Chấm điểm — quyết định chủ dự án: không dùng điểm bên thứ ba | 3 | `False` | `icbTotalRanked` `indexRank` `indexTotalRanked` |
| Chỉ báo kỹ thuật — tính lại được | 2 | `False` | `cmf` `sma20Past4` |

### 4.2 18 mã tỷ số tài chính — `keep = True`, cần xác nhận (§9)

Không rơi vào nhóm bỏ nào; cùng họ với *"55 mã tỷ số không nguồn nào khác có"* của quyết định gốc.

| Có tên trong từ điển 729 mã (5) | Chưa có — `status = "chưa giải mã"` (13) |
|---|---|
| `isa3` Doanh số thuần · `isa5` Lãi gộp · `ryq2` Thanh toán nhanh · `ryq3` Thanh toán hiện hành · `ryq6` Nợ/VCSH (TTM) | `fryq30` `grossMargin` `profitGrowth` `revenueGrowth` `roe` `rqd25` `rqd52` `rtd20` `rtd36Avg` `rtq160` `rtq166` `rtq176` `ryq4` |

### 4.3 🔴 Không ép con số 80

59 + 18 = **77**, không phải 80. "80" là ước lượng theo *nhóm* ngày 2026-08-14, không phải số đếm. Tiêu chí nghiệm thu là **193/193 dòng có mặt** (AC1); số `keep` là *kết quả*, không phải chỉ tiêu. Ra 77 thì ghi 77 và đính chính "80" ở mọi chỗ đang chép nó (§8). **Số chốt sau review cuối 2026-09-03: 81/193** — Ruling 15 áp cùng luật *lưu trước, giải mã sau* cho 4 mã `rtd39` `rtd53` `rtd54` `rtq81` vốn mang `keep = None` (`cần kiểm API`) nên bị ETL bỏ, dù chúng có thật và có giá trị. Ép cho khớp 80 chính là *"sửa số mà không đo"* (CLAUDE.md §1.2).

## 5. Phần B — job `python -m etl screener`

### 5.1 Khuôn — y `refdata_job.run`, không sáng tạo

```
open_run(engine, JOB)                       JOB = "market.screener"
  raw   = screener_fetch.fetch()            52 trang, tuần tự, retry có kiểm soát
  items = screener_normalize.normalize(raw) lọc keep, tradingDate → date, chịu null khối
  t     = screener_merge.merge(engine, items)  ticker+exchange → security_id
  baseline = screener_store.load_baseline(engine)
  with engine.begin() as conn:
      verdict = screener_guard.check(...)   ĐÁNH GIÁ TRƯỚC COMMIT
      if not verdict.ok: raise GuardRefused  → giao dịch tự rollback
      stats = screener_store.apply(conn, t)  UPSERT theo PK
  close_run(success, stats) · upsert_domain_state('market.scores','fiintrade', watermark=trading_date)
except GuardRefused → store_refusal_evidence (giao dịch riêng, staging.raw_payload source='screener') — trang 1 (đủ cho vế (i)/(iii)), mọi trang khi lý do là thiếu trang · close_run('failed') · exit 1
except Exception   → close_run('failed', error) · exit 2
```

`open_run`/`close_run` dùng lại từ `omo_store` như refdata đang dùng. Miền `data_domain_state` là **`market.scores`** — DDL `0008` đã dành sẵn *("'market.scores' = snapshot/screener — tầng C")*.

### 5.2 `screener_fetch` — I/O thuần

- `POST https://wlgw-tools.fiintrade.vn/Screener/GetScreenerItems?language=vi`, header `Origin: https://fiinapp.bvsc.com.vn` (bắt buộc cho `*.fiintrade.vn`, như `refdata_fetch`). Body: `comGroupCode=ALL`, `icbCode=ALL`, `pageSize=30`, **một tiêu chí** `ClosePrice` với `selectedValue = valueRange` *(gửi nhiều tiêu chí là timeout Redis phía nguồn — `10-fiin-dictionary`)*.
- Trang 1 cho `totalCount` ⇒ số trang = `ceil(totalCount / 30)`; lặp tuần tự, **không** luồng.
- Một trang được coi là **hỏng** khi: HTTP ≠ 200, hoặc `status != "Success"`, hoặc thiếu `items`. Hỏng ⇒ retry **tối đa 3 lần**, backoff 2 s · 4 s · 8 s. Hết retry ⇒ **raise**, job `failed`, **không ghi trang nào** — [`00-conventions §10.5`](../../../10-sources/market/00-conventions.md): *"coi là rỗng sẽ ghi một trang trắng vào kho mà không ai biết"*.
- Trả `list[str]` — text thô từng trang, giữ nguyên để làm bằng chứng khi guard từ chối.

### 5.3 `screener_normalize` — thuần, không I/O

Một item → `ScreenerRow(ticker, exchange, organ_code, trading_date, payload)`:

- `exchange` từ `priceInfo.comGroupCode`: `VNINDEX → HOSE`, `HNXIndex → HNX`, `UpcomIndex → UPCOM`. Giá trị khác ⇒ đếm `unknown_com_group`, bỏ dòng.
- `trading_date = date(priceInfo.tradingDate)` — **cắt phần ngày**; đây là timestamp riêng từng mã (14:45–15:00), không dùng thô.
- `payload` = khối lồng của nguồn, mỗi khối chỉ giữ khoá có `keep = True` trong `market-field-selection.json` (`source = "Screener"`); khối `null` hoặc không còn khoá nào ⇒ **bỏ khối**, không nổ. Khoá `keep` đọc từ file JSON lúc import — không hardcode danh sách trong code.
- Không đổi đơn vị, không tính lại gì — *"Không tự tính lại chỉ tiêu nguồn đã cấp"* (step-03).

> **Đính chính sau review cuối 2026-09-03 — ĐÃ CHỐT cùng ngày:** 10 khoá keep nằm ở cả `stockScreenerItem` lẫn `financial`; 7 mã `rtd*` hai bản luôn bằng nhau, nhưng **`rtq12` · `rtq27` · `rtq83` khác nhau ở 52/90 cặp trên mẫu 28/08, kể cả đổi dấu**. Spec ban đầu chỉ xét kích thước, không xét hai bản có bằng nhau không — đó là lỗ hổng của spec. **Khối chuẩn = `stockScreenerItem`**, mỗi mã lưu đúng MỘT bản (`BLOCK_PRIORITY` trong `screener_normalize`); `financial` chỉ giữ 7 mã riêng nó có (`isa3` `isa5` `fryq30` `rtd39` `rtd53` `rtd54` `rtq81`). Hai bằng chứng độc lập: (1) bundle JS của chính FiinTrade khai `"stockScreenerItem.rtq12"` cho ROE, mọi mã keep khác cũng khai khối đó; (2) đẳng thức ROE = LNST(TTM) × P/B ÷ vốn hoá — `stockScreenerItem` sai số trung vị **8,1 %** (4 mã khớp trong 2 %), `financial` **23,0 %** (**0** mã khớp trong 2 %). ⚠️ Bằng chứng (2) chỉ chạy được cho `rtq12`; `rtq27`/`rtq83` theo cùng luật vì bundle xếp cùng nhóm — **suy luận, chưa đo riêng** *(thử `rtq83` = `isa20TTM/isa20Y − 1` thì CẢ HAI bản đều lệch >76 %, tức công thức thử sai, không kết luận được)*. `dup_conflicts` giữ nguyên làm **chỉ báo sức khoẻ nguồn**. Sau lọc chỉ còn hai khối có khoá keep.

### 5.4 `screener_guard` — thuần, đánh giá trước commit

Bốn vế, **vế nào hỏng cũng từ chối**:

| # | Vế | Vì sao |
|---|---|---|
| (i) | **Phiên có giao dịch**: số mã có `priceInfo.closePrice > 0` phải **≥ 50 % số mã gom được** (`MIN_PRICED_RATIO = 0.5` — đo được 30/30 sau phiên vs 0/30 trước mở cửa; ngưỡng tỷ lệ thay cho "> 0" sau review cuối 2026-09-03: một mã lẻ có giá trong ngày lễ không được phép mở cửa ghi 1.545 dòng ma) | Ngày lễ nguồn vẫn đóng dấu hôm nay với giá 0 (đo 03/09). Không có vế này, mỗi ngày lễ đẻ 1.545 dòng ma |
| (ii) | **Đủ trang**: số item gom được == `totalCount` của trang 1, và `totalCount ≥ (1 − 2%) × mốc` | Mốc = `stats.counts.items` của lượt `success` gần nhất trong `ops.etl_run` — khuôn `refdata_guard` tầng 1, `DROP_RATIO = 0.02`. Lượt đầu không mốc thì bỏ vế sụt |
| (iii) | **Ghép được**: tỷ lệ dòng không tìm thấy `security_id` ≤ 2% | Mã có trong Screener mà chưa có trong `market.security` là bất thường (refdata chạy 08:00 cùng ngày) |
| (iv) | **Sàn lạ**: số dòng bị bỏ vì `comGroupCode` không thuộc {VNINDEX, HNXIndex, UpcomIndex} ≤ 2 % | Nguồn đổi tên sàn thì không được im lặng mất trọn một sàn (review cuối 2026-09-03) |

Vế (i) là lý do tồn tại của guard này; (ii), (iii) và (iv) là bảo hiểm rẻ theo khuôn có sẵn.

### 5.5 `screener_merge` + `screener_store`

- Ghép theo `(ticker, exchange)` với `market.security WHERE status = 'listed'` — đúng unique index đã có. Không ghép qua `organCode → issuer` vì một issuer có thể có nhiều security.
- `apply`: `INSERT … ON CONFLICT (security_id, trading_date) DO UPDATE SET payload = EXCLUDED.payload, ingested_at = clock_timestamp()` *(`clock_timestamp()` thay `now()` — Ruling 2 trong ledger: `now()` đóng băng theo transaction nên test một-transaction không thấy lượt hai; production mỗi lượt một transaction, tương đương)* — **UPSERT theo PK**, đúng ngữ nghĩa step-03 §3 *("chạy lại trong ngày đè bản của chính ngày đó")*.
- `stats` ghi vào `ops.etl_run`: `counts.items`, `counts.pages`, `counts.priced`, `counts.trading_dates`, `rows_written`, `unmapped`, `unknown_com_group`, `null_blocks`, `dup_conflicts`, `retries`, `trading_date`.

### 5.6 Lịch và vận hành

- Task `dlck-screener` **15:20** Thứ 2–6, đăng ký qua `Register-DlckTask` trong `scripts/register-tasks.ps1` + `Assert-TaskCommand -MustContain "python -m etl screener"`. 15:20 vì ingester ghi xong 15:05, và **tránh 15:30 của OMO** (đang tắt, sẽ bật lại theo roadmap [4d]).
- Chạy thật dưới `ETL_DATABASE_URL` (role `dlck_etl`) — role đã có `SELECT, INSERT, UPDATE, DELETE` trên `market.*`, `staging.*`, `ops.*` (`0009`), không cần grant mới.
- Thời lượng dự kiến: 52 × ~2,4 s ≈ **2–3 phút**.
- Ngày lễ: guard (i) từ chối ⇒ `etl_run.status = 'failed'`, error *"chỉ 0/1.545 mã có closePrice > 0 — không phải ngày giao dịch"*, bằng chứng vào `staging.raw_payload`. **Đó là hành vi đúng**, không phải sự cố — cùng triết lý với job huỷ niêm yết báo đỏ 01/09.

## 6. Seam test *(chốt cùng plan — §4.5.2; expected từ mẫu thật ở `samples/`, không tính lại theo code)*

| # | Seam | Ca | Assert giá trị cụ thể |
|---|---|---|---|
| 1 | normalize | item `DDB` trang 1 ngày 28/08 | `trading_date == date(2026,8,28)`, `exchange == "UPCOM"`, ba giá trị `keep` bằng literal chép từ mẫu |
| 2 | normalize | item `V68` (`technical = null`) | không nổ; `payload` **không có** khoá `technical`; các khối khác vẫn đủ |
| 3 | normalize | `tradingDate = "2026-08-28T14:45:00.057"` | `date(2026,8,28)` — ca biên ≠ 15:00 |
| 4 | normalize | `comGroupCode = "XYZ"` | dòng bị bỏ, `unknown_com_group == 1` |
| 5 | fetch | trang trả `status: "Failed"` + `"Timeout performing"` rồi `Success` | retry đúng 1 lần, **không** có trang rỗng trong kết quả |
| 6 | fetch | trang hỏng 4 lần liên tiếp | raise; **không** trả về danh sách thiếu trang |
| 7 | guard (i) | **mẫu thật 03/09 trước mở cửa** (0/30 `closePrice > 0`) | `ok == False`, lý do chứa *"không phải ngày giao dịch"* — **đây là test quan trọng nhất của lát** |
| 8 | guard (ii) | `totalCount = 1.545`, mốc 1.600 | từ chối (sụt 3,4% > 2%); mốc 1.560 ⇒ chấp nhận |
| 9 | guard (iii) | 40/1.545 không ghép được | từ chối (2,6% > 2%) |
| 10 | store, DB thật | apply hai lượt cùng `trading_date` | `count(*)` không đổi, `ingested_at` lượt 2 > lượt 1 |
| 11 | job, DB thật | fetch giả trả mẫu 28/08 (30 mã) | exit 0, 30 dòng, `etl_run.status='success'`, `data_domain_state('market.scores','fiintrade').watermark == '2026-08-28'` |
| 12 | job, DB thật | fetch giả trả mẫu 03/09 | exit 1, **0 dòng**, `etl_run.status='failed'`, có bản ghi `staging.raw_payload source='screener'` |
| 13 | job, DB thật, **dưới role `dlck_etl`** | như 11 nhưng `SET LOCAL ROLE dlck_etl` | pass — bài học §3.5: test đường ghi *và* đường đọc dưới đúng quyền production |

Fixture: hai file trong `samples/` chép sang `backend/tests/etl/fixtures/screener/` (plan làm).

## 7. Tiêu chí nghiệm thu

| AC | Nội dung | Bằng chứng phải dán |
|---|---|---|
| **AC1** | Bảng chọn trường: `source=Screener` đếm **193 dòng**; mọi khoá của response thật đều có dòng; số `keep` ghi ra là số đếm được (dự kiến 77) | output script đếm + diff `market-field-selection.md` |
| **AC2** | 13 seam test §6 xanh, cả bộ `uv run pytest tests` xanh, không giảm số test hiện có (321) | output pytest nguyên văn |
| **AC3** | **Chạy tay một lượt thật dưới `ETL_DATABASE_URL` sau 15:05 của một ngày giao dịch** — trước khi đăng ký task (§3.5: chạy tay đúng lệnh dưới đúng credential trước khi tự động hoá) | log + `SELECT count(*), min(trading_date), max(trading_date) FROM market.screener_daily` ≈ 1.545 dòng một ngày |
| **AC4** | Chạy lại ngay lượt thứ hai cùng ngày ⇒ số dòng không đổi, `etl_run` có 2 lượt `success` | cùng câu SQL |
| **AC5** | 🔴 **Cổng giả định §2.2.1:** lượt chạy **ngày không giao dịch đầu tiên** (ngày lễ, hoặc chạy tay trước 09:00 một ngày thường) phải **từ chối** với lý do vế (i), 0 dòng ghi. Chưa có phép này thì task vẫn được bật, nhưng mục này để mở trong ledger | log + `SELECT * FROM ops.etl_run WHERE job='market.screener' ORDER BY run_id DESC LIMIT 1` |
| **AC6** | Task `dlck-screener` đăng ký, `Assert-TaskCommand` + `Assert-TaskPrincipal` qua, rồi **`Disable-ScheduledTask`** vì cả đội đang tạm dừng (xem ràng buộc đầu spec). Lượt tự động đầu tiên `success` → **hoãn**, ghi vào ledger khi [4d] bật lại | `Get-ScheduledTask` cho thấy `Disabled` + lệnh đúng |

## 8. Checklist tài liệu sống — cùng lượt với code (§1.6, §1.7)

| File | Sửa gì |
|---|---|
| [`20-design/market-data-store.md`](../../../20-design/market-data-store.md) §5.5 | `screener_daily` đang ghi *"223 trường, 5 khối lồng"* và *"chuỗi điểm VGM"* — **đá** §4.1 cùng file (80/193) và quyết định bỏ nhóm chấm điểm. Sửa thành *"80/193 trường đã chọn (market-field-selection), 5 khối lồng"*, bỏ ví dụ VGM; §4.1 thêm dòng lịch 15:20 *(đợt sửa review cuối 2026-09-03 làm khác: 81/193, PK `(security_id, trading_date)` khớp migration 0004, và ghi rõ sau lọc chỉ còn hai khối — xem §5.3)* |
| [`10-sources/market/10-fiin-dictionary.md`](../../../10-sources/market/10-fiin-dictionary.md) | *(tầng reference — được sửa vì đã đo lại 2026-08-28/09-03)*: response có thêm `page` `pageSize` `packageId` `errors`; `tradingDate` là timestamp **riêng từng mã**; **trước mở cửa đã là ngày hôm nay với giá 0** — bẫy cho mọi ETL dùng endpoint này |
| [`20-design/gen_field_selection.py`](../../../20-design/gen_field_selection.py) → `.md`/`.json` | §4 — thêm 66 khoá; §7.3/§7.5 của file sinh sẽ tự về 0 "chưa liệt kê" |
| Mọi chỗ chép **"80/193"** | `git grep "80/193"` — sửa thành số đếm thật hoặc ghi *"80 (ước lượng 2026-08-14) → N (đếm 2026-09-xx)"* |
| [`00-overview/roadmap.md`](../../../00-overview/roadmap.md) §3 [7] · §0 | [7] tách lát, lát 1 trạng thái; hàng "Code sản phẩm" thêm `etl screener` |
| [`README.md`](../../../../README.md) bảng dịch vụ + [`20-design/service-topology.md`](../../../20-design/service-topology.md) §5 | thêm task thứ 8 `dlck-screener` 15:20 |
| `scripts/register-tasks.ps1` | thêm `Register-DlckTask "dlck-screener" "15:20" "etl screener" "screener.log"` + assert |
| [`90-records/README.md`](../../README.md) | đổi trạng thái dòng plan này khi xong |

## 9. Ba điểm cần chủ dự án duyệt tường minh

1. **18 mã tỷ số §4.2 → `keep = True`**, 13 mã trong đó ghi `chưa giải mã` (lưu trước, hiểu sau).
2. **Không ép 80** — ghi số đếm thật (§4.3) và đính chính mọi chỗ chép "80/193".
3. **Guard vế (i) `closePrice > 0`** làm tín hiệu *"phiên có giao dịch"* thay cho giả định đã bị bác — kèm cổng AC5 cho lần ngày lễ đầu tiên.
4. ~~**Khối chuẩn cho `rtq12` · `rtq27` · `rtq83`**~~ — ✅ **chốt 2026-09-03: `stockScreenerItem`** (§5.3). Còn treo, không chặn: `rtq27`/`rtq83` mới có bằng chứng gián tiếp — đo riêng khi tìm được công thức đối chiếu đúng.

✅ Duyệt 2026-09-03 ⇒ [`plan.md`](plan.md) cùng thư mục (viết cùng ngày, 8 task).
