# Spec — lát 7 ETL quốc tế: FRED · ECB (Frankfurter) · Yahoo · LBMA · Binance

**Ngày:** 2026-09-05 · **Nhánh:** `feat/global-etl` · **Trạng thái:** chờ chủ dự án duyệt spec
**Tiền đề:** [roadmap — Điểm vào cho lát 7](../../../00-overview/roadmap.md) · 5 tài liệu nguồn [`10-sources/global/`](../../../10-sources/global/) · [bước 4 (macro)](../2026-08-25-postgres-data-schema/step-04-macro.md) và [bước 5 (asset)](../2026-08-25-postgres-data-schema/step-05-asset.md) của spec schema · [spec lát 6](../2026-09-05-wichart-macro-etl/spec.md) (khuôn registry hai chủ, UPSERT chỉ-khi-đổi, guard trước giao dịch ghi)
**Brainstorm:** 6 câu hỏi, chủ dự án chốt 2026-09-05 chiều — ghi tại §4. Số đo trong ngày: [`measure-fred`](measure-fred-2026-09-05.txt) · [`measure-fx`](measure-fx-2026-09-05.txt) · [`measure-yahoo`](measure-yahoo-2026-09-05.txt) · [`measure-yahoo2`](measure-yahoo2-2026-09-05.txt) · [`measure-lbma`](measure-lbma-2026-09-05.txt) · [`measure-binance`](measure-binance-2026-09-05.txt).

Tiêu chí xuyên suốt (kế thừa lát 6): **kho là sự thật nguồn sau khi chuẩn hoá đơn vị và neo ngày, không có gì tự tính**; mọi luật đều phải truy được về một số đo. Thêm một tiêu chí riêng của lát này: **năm nguồn, năm luật thời gian và năm kiểu chết khác nhau — không dùng chung một hàm parse ngày hay một cổng độ tươi cho hai nguồn.**

---

## 1. Vì sao lát này, và lát này là gì

Lát 7 theo [thứ tự chuẩn](../../../00-overview/roadmap.md): nạp khối "bối cảnh toàn cầu" mà kho đang trống — lãi suất và lạm phát Mỹ, tỷ giá ECB, 36 chỉ số chứng khoán quốc tế, vàng bạc fixing London, vàng 24/7 và crypto. Năm job, mỗi job một nguồn (§4.2), cắm vào **cùng ổ cắm registry** mà lát 6 vừa dựng:

| Job | Nguồn | Series | Đích | Lời gọi/lượt |
|---|---|---|---|---|
| `etl fred` | FRED (`api.stlouisfed.org`, khoá `FRED_API`) | 15 (11 macro + 4 asset) | `macro.observation` · `asset.price_daily` | 15 |
| `etl fx` | ECB qua Frankfurter (`api.frankfurter.dev/v1`) | 6 cặp | `asset.price_daily` (`fixing`) | 1 |
| `etl lbma` | LBMA (`prices.lbma.org.uk`) | 2 (vàng PM, bạc, USD) | `asset.price_daily` (`fixing`) | 2 |
| `etl yahoo` | Yahoo (`query1.finance.yahoo.com/v8/finance/chart`) | 37 (36 chỉ số + DXY ICE) | `asset.ohlc_daily` | 37 |
| `etl binance` | Binance (`api.binance.com/api/v3/klines`) | 11 (PAXG + 10 coin) | `asset.ohlc_daily` | 11 |

Tổng **66 lời gọi/ngày**, ≈ 2 phút tuần tự. Lược đồ đã có từ migration `0005`/`0006`/`0008`; **không migration mới** (§2.1 đối chiếu CHECK thật).

Đây là lần **thứ hai** cùng một khuôn ghi (registry → điểm → UPSERT chỉ-khi-đổi) được dùng, nên phần **không phụ thuộc nguồn** của lát 6 được trích thành module chung (§4.1) — đúng điều kiện "trích chung khi lát 7 cần lần thứ hai" mà điểm vào lát 7 ghi. Lát này cũng là lần đầu ghi `asset.ohlc_daily`.

## 2. Dữ kiện đã đo vs giả định *(§4.8 bước 0)*

### 2.1 Đã đo — 2026-09-05 chiều (thứ 7), ~120 lời gọi thật + đọc migration

| Dữ kiện | Bằng chứng |
|---|---|
| **Lược đồ thật** (đọc `0005`/`0006`/`0008`, không tin văn bản): `macro.indicator.region` CHECK `('vn','us','global')` · `asset.asset_class` CHECK `('commodity','crypto','index','fund','fx')` · `asset.price_daily.price_type` CHECK `('spot','futures','fixing','close')` · `asset.ohlc_daily` PK `(asset_id, obs_date)` **không có `price_type`** · `asset.asset.region` text tự do · `data_domain_state.domain` có `'macro.indicator'` và `'asset'` · `staging.raw_payload.source` text tự do | migration |
| Ổ cắm registry **đã có dữ liệu thật**: 53 `indicator_source` + 52 `asset_external_id` của `source='wichart'`; `load_registry` xoá dòng ánh xạ vắng mặt **theo `source`** — lát này gọi với source khác phải giữ bộ lọc đó | `wichart_store.load_registry` · kho production |
| **FRED**: 15/15 series `200`; `DGS10` 2026-09-03 = 4,77; `PAYEMS` 07/2026 nay = **158.913** (lúc khảo sát 2026-08-15 là 158.858 ⇒ **vá hồi tố lần nữa, có bằng chứng**); `DTWEXBGS`/`DEXCHUS` dừng 08-28 (H.10 tuần, đúng tài liệu); trọn chuỗi lớn nhất `DFF` 2,5 MB thô / 0,7 s; **không ETag**; khoá sai ⇒ `400` JSON rõ nghĩa | measure-fred |
| **Frankfurter**: 🔴 host cũ `api.frankfurter.app` trả **`301` → `api.frankfurter.dev/v1/`** (fx.md ghi host cũ — sửa ở §8); trọn chuỗi `1999-01-04..` = **7.086 ngày, 672 KB, 2,4 s, 0 ngày thiếu cặp**; ETag yếu + `cache-control: max-age=86400`; v2 `providers=ECB` khớp v1 từng số | measure-fx |
| **LBMA** (chưa kiểm trong commodities.md §2.3, nay kiểm): body là **mảng `{d: 'YYYY-MM-DD', v: [USD, GBP, EUR], is_cms_locked}`**, tăng dần theo ngày, vàng 14.676 điểm từ 1968-04-01, bạc 14.839 từ 1968-01-02, điểm cuối **2026-09-04** (vàng 4.415,40 · bạc 66,835 USD/oz); `null` trong `v` = tiền tệ chưa có (EUR trước 1999) — **7.737 / 7.847 dòng có null**; ETag có nhưng `If-None-Match` vẫn trả `200` trọn body ⇒ **không có 304**; `last-modified` 05:20 GMT thứ 7 | measure-lbma |
| **Yahoo**: host `query1`/`query2.finance.yahoo.com` đều `200`, không ETag; `period1` âm cho `^GSPC` = **24.787 nến từ 1927-12-30, 2,65 MB**, có `adjclose`; **37/37 mã kế hoạch `200`, `dataGranularity=1d`, `regularMarketTime` = phiên 2026-09-04** | measure-yahoo |
| 🔴 **Yahoo đổi hợp đồng so với 2026-08-15: `meta.quoteType` KHÔNG còn**, cờ chết nằm ở **`meta.instrumentType`** (`TIO=F` → `ALTSYMBOL`, chỉ số → `INDEX`); `^BCOM` vẫn `INDEX` với `regularMarketTime` 2020-05-28 và **0 nến** trong cửa sổ 40 ngày ⇒ cổng độ tươi vẫn bắt được | measure-yahoo |
| 🔴 **Cửa sổ 40 ngày không đủ**: `^SET.BK` và `PSEI.PS` trả **1 nến** (chỉ nến hiện tại) khi `period1 = now − 40 ngày`, nhưng **272/286 nến** khi 400 ngày, 1.999/2.144 khi 3.000 ngày — hai sàn này đủ lịch sử, chỉ là tổ hợp tham số ngắn bị Yahoo đối xử khác (cùng họ Bẫy 3) | measure-yahoo2 |
| Nến Yahoo định danh bằng **giờ mở phiên theo múi giờ sàn** (`^GSPC` 13:30 UTC, `^N225` 00:00 UTC, `DX-Y.NYB` 04:00 UTC); `meta.currentTradingPeriod.regular.end` cho biết phiên đã đóng chưa; `^MERV` trả **`currency` rỗng** | measure-yahoo2 |
| **Binance**: 11/11 mã `TRADING`, quote `USDT`; `klines` `limit=40` trả 40 nến kể cả **nến hôm nay chưa đóng** (`closeTime` 23:59 UTC hôm nay); nến đầu `PAXGUSDT` 2020-08-28, `BTCUSDT` 2017-08-17; header `x-mbx-used-weight-1m` tăng 2/lời gọi, hạn 6.000; đồng hồ máy chậm hơn server **991 ms** | measure-binance |

### 2.2 Giả định — CHƯA kiểm

1. **Rate limit** của Frankfurter/LBMA/Yahoo/Binance ở mức tải kế hoạch (1 · 2 · 37 · 11 lời gọi/lượt): hôm nay đo đúng mức đó, 0 tín hiệu chặn, nhưng chỉ một lượt. Kết luận giữ ở dạng *"mức 66 lời gọi/lượt an toàn"* (§4.3 CLAUDE.md), không suy ngưỡng.
2. Yahoo `adjclose` của chỉ số bằng `close` (không có cổ tức) — chưa đối chiếu; UPSERT `close_adj` đúng dù giả định sai.
3. LBMA có vá quá khứ hay không — chưa biết; UPSERT chỉ-khi-đổi đo được qua `stats.changed`.
4. `is_cms_locked` của LBMA là cờ CMS nội bộ, không mang nghĩa dữ liệu — không dùng, chỉ giữ trong bằng chứng thô.
5. Giờ nạp thật của từng nguồn (FRED ~16:00 St. Louis, ECB 16:00 CET, LBMA sau 15:00 London, Yahoo ngay khi phiên đóng, Binance 00:00 UTC) — lấy từ tài liệu, ảnh hưởng bảng lịch lát 13, không ảnh hưởng lát này (chạy tay).

## 3. Phạm vi

### 3.1 Trong phạm vi

- Năm job `python -m etl fred|fx|lbma|yahoo|binance`, cờ chung `--dry-run`, cờ lượt con `--keys a,b` (tên series/mã nguồn), cờ `--backfill` cho `yahoo`/`binance` (§5.1).
- Module chung trích từ lát 6: `registry.py` (`Series` + `load_registry(conn, series, source)`), `series_store.py` (`apply` cho `observation`/`price_daily`, **`apply_ohlc`** mới cho `ohlc_daily`, bằng chứng từ chối, `upsert_domain_state`), `series_guard.py` (hai chế độ §5.4); `wichart_*` chuyển sang dùng module chung, hành vi không đổi (test lát 6 giữ nguyên xanh).
- Năm registry `<src>_registry.py` (§4.1, Phụ lục A–E), năm cặp `<src>_fetch.py`/`<src>_normalize.py`, năm `<src>_job.py`.
- Sửa tài liệu sống theo checklist §8, gồm ba sửa ở tầng reference **vì đã đo lại** (Yahoo `instrumentType`, host Frankfurter, cấu trúc JSON LBMA).

### 3.2 Ngoài phạm vi — ba loại *(§1.4)*

| Mục | Loại | Lý do |
|---|---|---|
| Yahoo: lợi suất `^TNX`/`^TYX`/`^FVX`/`^IRX`, tỷ giá `*=X`, `VND=X`, `0P0000HY8X.VN`, cổ phiếu `.VN` | **Đã có đường khác** | FRED có DGS2/DGS10; ECB là nguồn tỷ giá chính; BVSC/FiinTrade là nguồn Việt Nam. Vai "dự phòng/đối chứng" là việc của lát 12 |
| Yahoo: họ biến động `^MOVE` `^SPGSCI` `^SOX` `^OVX` `^GVZ` `^SKEW` `^VVIX`, ETF quốc gia, `VNM`, `VOF.L`/`1VV.F`/`KPHO`, hàng hoá `HG=F`/`HRC=F`/`ALI=F` | **Loại có chủ đích** | Chủ dự án chốt câu 3: 36 chỉ số + DXY ICE. ETF/quỹ dời tới khi thiết kế chỉ báo dòng tiền ETF (tiền lệ lát 3); ba mã hàng hoá mới tươi chưa đúng (yahoo.md §5.6) |
| FRED: `DCOILBRENTEU`, `DHHNGSP`, `IMP5520`/`EXP5520`, chỉ số `SP500`/`NASDAQCOM`, vintage `output_type=4`, `series/release` để đặt lịch | **Loại có chủ đích** | Chưa gọi thật hoặc chưa có tiêu thụ; bảng vintage hoãn theo bước 4; lịch công bố thuộc lát 13 |
| LBMA giá GBP/EUR (`v[1]`, `v[2]`), `gold_am` | **Loại có chủ đích** | Kho định giá vàng bằng USD; không tiêu thụ nào cần GBP/EUR. Ổ cắm `external_sub` theo vị trí sẵn sàng khi cần |
| Binance: nhóm TradFi perpetual (`CLUSDT`, `XAUUSDT`…), `XAUTUSDT`, WebSocket, kho file `data.binance.vision` | **Loại có chủ đích** | crypto.md §7 đã đo và loại; REST `klines` đủ cho backfill (BTC 9 năm = 4 lời gọi) |
| DXY dựng lại từ 6 cặp ECB; tăng trưởng tự tính; DXY dựng lại so DXY ICE | **Loại có chủ đích** | Tầng tự tính (bước 5 §3.4); giám sát sai lệch thuộc lát 12 |
| `ops.series_health`, `contract_snapshot` | **Đã có đường khác** | Lát 12; lát này chỉ ghi `stats` đủ để lát 12 đọc |
| Đăng ký task Scheduler; ETag/304 | **Loại có chủ đích** | Lịch thuộc lát 13; đo được: chỉ Frankfurter có ETag mà 1 lời gọi/ngày không đáng tối ưu, LBMA ETag không sinh 304, FRED/Yahoo không ETag |
| Pháp lý | — | FRED chốt 2026-08-15 (CLAUDE.md §2.1). Điều khoản Yahoo/Binance/LBMA/Frankfurter chưa đọc — việc của chủ dự án, một dòng, không mở ở đây |

## 4. Quyết định *(§4.8 — phương án, lý do loại, điều kiện đảo ngược; chủ dự án chốt 2026-09-05 chiều)*

### 4.1 Registry: mỗi nguồn một module, phần ghi trích chung *(câu 1)*

| Phương án | Trục tối ưu | Lý do loại |
|---|---|---|
| **A · `<src>_registry.py` mỗi nguồn chỉ giữ bảng "mã của mình"; `Series` + `load_registry(conn, series, source)` trích thành `registry.py` chung** ✅ | ranh giới rõ, một đường ghi | — chọn |
| B · một `global_registry.py` phẳng cho 5 nguồn | ít file | ~70 dòng trộn 5 lược đồ nguồn khác nhau (FRED có `max_lag` theo lịch công bố, Yahoo có múi giờ sàn, LBMA có vị trí trong `v[]`); sửa một nguồn là đụng file chung |
| C · nhân bản nguyên khối `wichart_*` cho từng nguồn | nhanh nhất | 6 bản `load_registry` gần giống nhau — bug ở đường ghi phải sửa 6 chỗ, đúng bẫy hai nguồn sự thật §1.7 |

Khác lát 6: các tài liệu `10-sources/global/*.md` **không có khối Python** để `exec`, nên bảng trong module là **chủ duy nhất** của ánh xạ; sự thật đo (đơn vị, tần suất, độ trễ) vẫn nằm ở tài liệu nguồn và test ràng buộc bằng **literal chép tay từ tài liệu** (ví dụ `PAYEMS` đơn vị nghìn người ⇒ `scale = 1000`, `DTWEXBGS` trễ tới 9 ngày ⇒ `max_lag_days = 12`). `Series` chung có thêm hai trường lát 6 chưa cần: `band: (lo, hi) | None` **theo series** (không theo đơn vị — chỉ số 14 điểm và chỉ số 3.049.122 điểm cùng đơn vị "điểm"), và `max_lag_days` (cổng độ tươi §5.3). `wichart_registry.Series` giữ nguyên, thêm `external_key`/`meta` để cùng giao diện với `load_registry` chung.

**Đảo ngược khi:** một nguồn thứ sáu cần lược đồ khác hẳn (ví dụ series nhiều chiều) ⇒ tách `Series` theo hình dạng, không theo nguồn.

### 4.2 Mỗi nguồn một job, một sổ *(câu 2)*

Năm job `global.fred` · `global.ecb` · `global.lbma` · `global.yahoo` · `global.binance` trong `ops.etl_run`; `data_domain_state` theo `(domain, source)`: `('macro.indicator','fred')`, `('asset','fred')`, `('asset','ecb')`, `('asset','lbma')`, `('asset','yahoo')`, `('asset','binance')`. Loại B (một job, một sổ): một nguồn hỏng phải định nghĩa "thành công một phần", và lát 13 không xếp lịch riêng được (FRED sau 16:00 St. Louis, ECB sau 16:00 CET, Binance sau 00:00 UTC). Loại C (một lệnh, năm sổ): là mini-scheduler trước lát 13. **Đảo ngược khi:** lát 13 thấy 5 dòng lịch cho 66 lời gọi là thừa ⇒ gom ở bảng lịch, không gom ở job.

Tên `source` là **danh tính dữ liệu**, không phải tên API: `'ecb'` cho Frankfurter (đổi sang ECB SDMX thì cùng fixing, cùng số, cùng dòng ánh xạ) — cùng lý do `'fred'` chứ không phải `'eia'` cho dầu.

### 4.3 Phạm vi Yahoo 37 mã, Binance 11 mã *(câu 3, 4)* — bảng ở Phụ lục D/E, lý do loại ở §3.2.

### 4.4 Cửa sổ theo chi phí nguồn *(câu 5)*

| Nguồn | Mỗi lượt | `--backfill` |
|---|---|---|
| FRED · ECB · LBMA | **trọn chuỗi** (15 lời gọi ≈ 12 MB thô / 1 lời gọi 672 KB / 2 lời gọi 1,8 MB); UPSERT chỉ-khi-đổi, `stats.changed` đo vá hồi tố | không cần |
| Yahoo | **cửa sổ 400 ngày** (đo: 40 ngày trả 1 nến ở `^SET.BK`/`PSEI.PS`, 400 ngày trả đủ; ≈ 50 KB/mã) | `period1 = −2208988800` (1900-01-01), một lời gọi/mã |
| Binance | **`limit=40`** nến (24x7, đủ bù một tháng không chạy) | phân trang `startTime` từ 0, `limit=1000`, tới khi trả < 1000 (BTC ≈ 4 lời gọi) |

Loại "tất cả trọn mỗi lượt": Yahoo 2,65 MB × 37 mỗi ngày trên nguồn không cam kết. Loại "tất cả cửa sổ ngắn": mất phép đo vá hồi tố của FRED ngoài cửa sổ, LBMA vốn không lọc được ở nguồn. **Đảo ngược khi:** FRED thêm chuỗi tick/phút (không có).

### 4.5 Guard: tất-cả-hoặc-không cho nguồn ≤ 20 series *(câu 6)*

FRED (15), ECB (6), LBMA (2), **Binance (11)**: một series `failed`/`shape`/`band`/`stale` ⇒ **từ chối cả lượt**, 0 dòng ghi, bằng chứng vào `raw_payload`. Lý do: các series này đều là xương sống và hỏng lẻ ở nguồn có khoá/định danh rõ thường là lỗi tham số, không phải sự cố lẻ. Yahoo (37 ≥ `MIN_SAMPLE`): khuôn tỷ lệ của lát 6 — `failed` > 20 % · `shape` > 5 % · `band` > 5 % · **`stale` > 20 %** từ chối; dưới ngưỡng thì **bỏ series đó khỏi lượt ghi**, đếm vào `tally`. **Đảo ngược khi:** một series FRED chết hẳn ở nguồn (ví dụ ngừng công bố) ⇒ gỡ khỏi registry, không nới guard.

### 4.6 Bằng chứng thô: khi từ chối + mẫu dòng đổi, KHÔNG lưu body mỗi lần hash đổi *(khác lát 6, quyết định mới)*

Lát 6 lưu body khi hash đổi vì 68 key × ≤ 730 điểm là rẻ. Ở đây body **trọn chuỗi** FRED (12 MB/lượt, `DFF` đổi mỗi ngày), LBMA (1,8 MB, đổi mỗi ngày), Yahoo 400 nến × 37 — ≈ **15 MB/ngày ≈ 5 GB/năm** trong `staging.raw_payload`, không hợp VPS 60 GB. Thay bằng:

- `raw_payload` **chỉ khi guard từ chối** (`meta.refused`, đủ mọi body của lượt) — y lát 1–5.
- `stats.changed` + **`stats.changes_sample`**: tối đa 50 dòng `(code, obs_date, giá cũ, giá mới)` — chính là lịch sử vá hồi tố ở dạng gọn (giả định §2.2.3 và bằng chứng `PAYEMS`). `apply` đọc giá cũ bằng CTE trước UPSERT.

**Đảo ngược khi:** cần vintage đầy đủ để backtest ⇒ bảng vintage của bước 4 (đã hoãn có chủ đích), không phải bật lại lưu body.

### 4.7 Tên mã và phân loại *(điểm duyệt §9.1–9.4)*

- `indicator.code` Mỹ tiền tố `us.`; `asset.code` slug tiếng Anh như lát 6; chỉ số Yahoo tiền tố `idx.`; DXY ICE = `dxy.ice`, DXY broad của Fed = `dxy.broad`; giữ tên bước 5 (`wti`, `gold.lbma`, `paxg`, `fx.usd_eur`…).
- `wti`: FRED ghi `('wti', ngày, 'spot')` **cùng `asset_id`** với chuỗi `futures` của WiChart — `load_registry` upsert `asset.asset` theo `code` nên trùng `asset_id` tự nhiên, thêm một dòng `asset_external_id (fred, DCOILWTICO)`; PK có `price_type` nên hai chuỗi không đè nhau (CLAUDE.md §2.3).
- `price_type`: FRED `DCOILWTICO` = `spot` · `DEXCHUS` = `fixing` (noon buying rate NY, bước 5) · `DTWEXBGS` và `VIXCLS` = **`close`** (giá trị cuối ngày của chỉ số, không có mốc fixing) · ECB và LBMA = `fixing`. OHLC không có `price_type` (NULL ở `asset_external_id`).
- `quote_currency` của chỉ số = **đồng tiền định giá** mà nguồn khai (`^N225` JPY, `^GSPC` USD…); `^MERV` nguồn trả rỗng ⇒ registry ghi `ARS` và cổng tiền tệ (§5.3) bỏ qua khi nguồn rỗng. `unit = 'điểm'`.
- `paxg` `asset_class='crypto'`, `quote_currency='USDT'`, `calendar='24x7'` — là token, dù vai là vàng 24/7; tên và vai ghi ở `name_vi`/`notes`.
- FRED đơn vị về **đơn vị gốc không nghìn/tỷ** (luật bước 1): `PAYEMS` nghìn người ⇒ `scale 1000`, unit `người`; chỉ số CPI/PCE giữ nguyên chỉ số (`unit` ghi rõ năm gốc); `%` giữ nguyên.

## 5. Năm job

### 5.1 Khuôn — y `wichart_job`

`open_run` ngay trước `try` → `build()` registry (hợp đồng khởi động) → fetch → normalize → **guard trước giao dịch ghi** → `load_registry` + `apply`/`apply_ohlc` trong một giao dịch → `close_run` → `upsert_domain_state`. `KeyboardInterrupt` ⇒ `failed: dừng tay (Ctrl+C)`, exit 130 (nợ đã trả 2026-09-05 chiều, `test_e42`).

| Cờ | Nghĩa |
|---|---|
| `--dry-run` | fetch + normalize + guard, không ghi gì, in `stats` |
| `--keys a,b` | lượt con theo `external_key` (`DGS10`, `EUR`, `gold_pm`, `^GSPC`, `PAXGUSDT`); **không** guard tỷ lệ, **không** đụng domain state (bài học 1c lát 4) |
| `--backfill` | chỉ `yahoo`/`binance` (§4.4); một mã một giao dịch, không con trỏ (37 + 11 mã, ≤ 3 phút) |

Mốc nước `data_domain_state.watermark` = ngày VN của lượt (như lát 6).

### 5.2 `<src>_fetch` — I/O thuần, `get` bơm được

Cùng khuôn `wichart_fetch.Fetcher` (timeout 30 s, retry 3, backoff 2/4/8, exception vận chuyển cùng đường với response xấu, `MIN_INTERVAL` theo nguồn). Khác nhau ở `classify` và URL:

| Nguồn | URL | `classify` `ok` khi | `MIN_INTERVAL` |
|---|---|---|---|
| FRED | `series/observations?series_id=X&api_key=…&file_type=json` | `200` + JSON có `observations` list. `400` ⇒ **`bad_shape`** (lỗi tham số/khoá, thử lại vô ích — FRED trả lỗi rõ). 🔴 URL/exception **che `api_key`** trước khi vào log hay `stats` (Bẫy 7) | 0,5 s |
| ECB | `https://api.frankfurter.dev/v1/1999-01-04..?from=USD&to=EUR,JPY,GBP,CAD,SEK,CHF` (host mới, đo hôm nay) | `200` + `rates` dict; `base == 'USD'` | — |
| LBMA | `json/gold_pm.json` · `json/silver.json` | `200` + list, phần tử có `d` và `v` list | 1 s |
| Yahoo | `https://query1.finance.yahoo.com/v8/finance/chart/{sym}?period1&period2&interval=1d`, header `User-Agent` của dự án | `200` + `chart.result[0]` có `meta` và `timestamp`; `404` ⇒ `retry` một lần bằng cùng tham số rồi `bad_shape` (Luật 3 yahoo.md) | 1,1 s |
| Binance | `api/v3/klines?symbol&interval=1d&limit&timeZone=0[&startTime]` | `200` + list of list 12 phần tử. Đọc `x-mbx-used-weight-1m` sau mỗi lời gọi: ≥ 3.000 ⇒ ngủ 60 s; `429` ⇒ ngủ theo `Retry-After` rồi retry; **`418` ⇒ dừng cả lượt** | 0,3 s |

### 5.3 `<src>_normalize` — thuần; năm luật thời gian, năm cổng

Chung: `Point(domain, code, obs_date, value: Decimal, price_type)` cho `observation`/`price_daily`; **`Bar(code, obs_date, open, high, low, close, close_adj, volume)`** mới cho `ohlc_daily`. Lỗi `SeriesError(reason)` với `reason ∈ {shape, band, stale}` (lát 6 có `freq`, ở đây tần suất không suy — mỗi nguồn khai tường minh).

| Nguồn | `obs_date` | Giá trị | Cổng độ tươi (`stale`) | Cổng khác |
|---|---|---|---|---|
| FRED | `date` ISO (chuỗi tháng đã neo ngày 1 = luật kho) | `value` chuỗi; `"."` ⇒ **bỏ điểm**, không dòng; `Decimal(str) × scale` | `max(obs_date) ≥ hôm nay(UTC) − max_lag_days` theo series (d: 6; H.10 `DTWEXBGS`/`DEXCHUS`: 12; m: 60; `PCEPILFE`: 90) | `count` ≥ số điểm đã có trong kho − 0 (chuỗi không co lại) — chỉ báo, không từ chối |
| ECB | khoá ngày của `rates` | `rates[day][ccy]` số ⇒ `Decimal(str)` | ngày cuối ≥ hôm nay − 6 (TARGET nghỉ dài nhất 4 ngày + cuối tuần) | đủ 6 tiền tệ ở ngày cuối; `start_date` đọc từ response, không giả định |
| LBMA | `d` | `v[idx]` với `idx` = `external_sub` (0 = USD); `null` ⇒ bỏ điểm | `d` cuối ≥ hôm nay − 6 | mảng `v` đúng 3 phần tử; ngày tăng dần |
| Yahoo | `timestamp[i]` → múi giờ **`meta.exchangeTimezoneName`** → date (13:30 UTC `^GSPC` = 09:30 New York = 09-04) | `open/high/low/close/volume` theo vị trí, `adjclose` → `close_adj`; nến có `close` null ⇒ bỏ | `regularMarketTime ≥ hôm nay − max_lag_days` (mặc định 14, phủ Tết Trung Quốc; `^BCOM` 2020 chết) **và** ≥ 1 nến trong cửa sổ | (a) `dataGranularity == '1d'`; (b) **`instrumentType != 'ALTSYMBOL'`** (đo hôm nay: `quoteType` không còn); (c) `meta.currency` nếu không rỗng phải bằng registry; (d) **bỏ nến cuối chưa đóng**: nến cuối cùng ngày với `regularMarketTime` **và** `regularMarketTime < currentTradingPeriod.regular.end` |
| Binance | `k[0]` epoch ms mở nến → **date UTC** (`1786752000000` = 2026-08-15, seam 4 bước 5) | `k[1..5]` chuỗi ⇒ `Decimal`, không float | nến đã đóng cuối ≥ hôm nay(UTC) − 2 | 12 phần tử/nến; **bỏ nến có `k[6]` (closeTime) > now** (đo: `limit=40` trả cả nến hôm nay) |

`band` theo series trên **điểm mới nhất** (Phụ lục), so có dấu như lát 6 (`T10Y2Y` âm được). Ngày trong mọi cổng lấy từ đồng hồ tường bơm được (`now=`), không hardcode.

### 5.4 `series_guard` — thuần, trước giao dịch ghi

`check(tally, mode)`: `mode='all_or_nothing'` (FRED, ECB, LBMA, Binance): `failed + shape + band + stale > 0` ⇒ từ chối, lý do liệt kê từng series. `mode='ratio'` (Yahoo): ngưỡng §4.5 với `MIN_SAMPLE 20`. `changed = 0` **không phải lỗi** (ngày nghỉ) — `success`.

### 5.5 `series_store` (trích từ `wichart_store`, thêm OHLC)

- `load_registry(conn, series, source)`: y lát 6, tham số `source` thay hằng; xoá ánh xạ vắng mặt **cùng `source`**; `meta` từ `s.meta`. Test pin: chạy `load_registry(…, 'fred')` **không** đụng dòng `wichart` (điểm vào lát 7 cảnh báo).
- `apply(conn, points, resolved) -> Written(inserted, changed, changes_sample)`: UPSERT chỉ-khi-đổi y lát 6, thêm CTE đọc giá cũ cho mẫu §4.6.
- `apply_ohlc(conn, bars, resolved)`: `INSERT … ON CONFLICT (asset_id, obs_date) DO UPDATE SET open,high,low,close,close_adj,volume, ingested_at = clock_timestamp() WHERE (o.open, o.high, o.low, o.close, o.close_adj, o.volume) IS DISTINCT FROM (excluded.…)`, `RETURNING (xmax = 0)`.
- `store_refusal_evidence(engine, source, texts, run_id, reasons)`, `upsert_domain_state(engine, source, domains, watermark)`.
- `wichart_store` giữ `seed_series_break`, `JOB`, `DOMAINS`, `SOURCE`; các hàm còn lại gọi sang module chung với `SOURCE` — test lát 6 không đổi.

### 5.6 Lịch và vận hành

Không đăng ký task. Chạy tay `uv run python -m etl <src>`. Vị trí gợi ý cho bảng lịch lát 13 (giờ VN, chưa đo giờ nạp): `binance` 07:15 (nến UTC đóng 07:00) · `yahoo` 08:00 (phiên Mỹ đóng 03:00–04:00) · `fred` 08:00 (FRED cập nhật ~16:00 St. Louis = 04:00–05:00 VN) · `lbma` 08:00 · `fx` 22:30 (ECB ~16:00 CET = 21:00–22:00 VN). Hằng ngày kể cả cuối tuần cho `binance`; nguồn khác chạy cuối tuần vô hại (`changed = 0`).

## 6. Seam test *(chốt cùng plan — §4.5.2)*

Expected từ mẫu thật chụp 2026-09-05 lưu ở `samples/` (một response mỗi nguồn: `fred-DGS10-tail.json` (100 điểm cuối, có `"."` ngày 07-03), `fred-PAYEMS-tail.json`, `ecb-2026-08.json`, `lbma-gold_pm-tail.json`, `yahoo-GSPC-10d.json`, `yahoo-TIO=F.json`, `yahoo-BCOM.json`, `yahoo-MERV-10d.json`, `binance-PAXGUSDT-5.json`) hoặc giải tay, không tính lại theo cách code tính.

| Seam | Ca phải có |
|---|---|
| `registry.load_registry` | 15 series FRED tạo 11 `indicator` + 11 `indicator_source(fred)` + 4 `asset_external_id(fred)`; `wti` **không** tạo asset mới khi asset `wti` đã có (cùng `asset_id`, thêm dòng ánh xạ `fred`); chạy `load_registry(..., 'fred')` sau khi có 52 dòng `wichart` ⇒ **52 dòng `wichart` còn nguyên**; chạy hai lần ⇒ số không đổi |
| `<src>_registry.build` | số series đúng (15 · 6 · 2 · 37 · 11); mã không trùng toàn cục giữa 5 module **và** với `wichart_registry`; mọi asset có `quote_currency`/`unit`; mọi `Series` có `band` |
| `fred_normalize` | `"."` ⇒ không dòng; `PAYEMS` `"159075"` × 1000 ⇒ `159075000` người; `T10Y2Y` `"0.41"` ⇒ `0.41` (âm hợp lệ trong band); `DTWEXBGS` cuối 08-28 với `now=09-05` ⇒ **không** stale (12 ngày), với `now=09-15` ⇒ stale; `Content-Type` XML ⇒ `bad_shape` (Bẫy 3) |
| `fx_normalize` | `EUR: 0.86453` ngày 2026-08-14 ⇒ `Point('fx.usd_eur', 2026-08-14, 0.86453, 'fixing')` (literal fx.md); ngày thiếu 1 tiền tệ ⇒ `shape`; `start_date` trước ngày xin ⇒ cắt |
| `lbma_normalize` | `{"d":"2026-09-04","v":[4415.4,3269.16,3803.43]}` ⇒ `gold.lbma` 4415.4; `v[2] = null` (1968) ⇒ không dòng cho EUR (không map) và USD vẫn ghi; `v` 2 phần tử ⇒ `shape` |
| `yahoo_normalize` | `^GSPC` 13:30 UTC ⇒ `obs_date 2026-09-04` (múi giờ NY), parse UTC ra cùng ngày nên thêm ca `^N225` 00:00 UTC ⇒ 09-04 và `DX-Y.NYB` 04:00 UTC ⇒ 09-04; `dataGranularity='1mo'` ⇒ `shape`; `instrumentType='ALTSYMBOL'` (`TIO=F`) ⇒ `shape`; `^BCOM` `regularMarketTime` 2020 ⇒ `stale`; nến cuối chưa đóng (`regularMarketTime < regular.end`) ⇒ bỏ; `^MERV` `currency=''` ⇒ qua, `currency='EUR'` khi registry `USD` ⇒ `shape`; `adjclose` → `close_adj` |
| `binance_normalize` | `1786752000000` ⇒ `2026-08-15` UTC (seam 4 bước 5; luật giờ VN phải đỏ); `"4433.13000000"` ⇒ `Decimal('4433.13')` không float; nến `closeTime > now` ⇒ bỏ; 11 phần tử ⇒ `shape` |
| `*_fetch.classify` | FRED `400` ⇒ `bad_shape`, log không chứa khoá (assert chuỗi khoá giả không xuất hiện trong message); Yahoo `404` ⇒ retry rồi `bad_shape`; Binance `418` ⇒ dừng lượt; weight ≥ 3000 ⇒ `sleep(60)` được gọi |
| `series_guard.check` | `all_or_nothing`: 1 stale/15 ⇒ từ chối; `ratio`: 2 shape/37 ⇒ từ chối (5,4 %), 1/37 ⇒ qua nhưng series bị bỏ; `changed = 0` ⇒ ok |
| `series_store.apply_ohlc` | first ⇒ `inserted = n`; chạy lại ⇒ 0/0, `ingested_at` không đổi; đổi `close_adj` ⇒ `changed = 1`, `close` giữ nguyên (seam 3 bước 5) |
| `series_store.apply` | `changes_sample` chứa `(code, date, cũ, mới)` khi giá đổi (literal `PAYEMS` 159001 → 158927, seam 1 bước 4) |
| job (mỗi nguồn, `get` giả) | lượt trọn ghi cả miền + domain state; lượt hai 0 đổi; `--keys` không đụng domain state; guard từ chối ⇒ `failed`, 0 dòng, `raw_payload.meta.refused`; `--dry-run` không ghi |
| quyền | `test_global_works_under_etl_role`: `SET LOCAL ROLE dlck_etl` đi qua registry + `observation` + `price_daily` + **`ohlc_daily`** (bảng chưa job nào ghi — kiểm GRANT thật của `0009`) |
| lát 6 không đổi | toàn bộ `test_e36`–`e41` xanh sau khi `wichart_*` chuyển sang module chung |

## 7. Tiêu chí nghiệm thu

| | Nội dung | Bằng chứng phải dán |
|---|---|---|
| AC1 | Toàn bộ test xanh | số test trước (650 + 2 skipped) / sau |
| AC2 | `--dry-run` 5 nguồn trên nguồn sống: FRED 15/15, ECB 6/6, LBMA 2/2, Yahoo 37/37 (0 `shape`, `stale` chỉ ở sàn đang nghỉ nếu có), Binance 11/11 | `stats` từng job |
| AC3 | Lượt đầu vào kho production (`ETL_DATABASE_URL`, role `dlck_etl`), đối chiếu tay với 6 literal đo 2026-09-05: `us.yield.10y` 2026-09-03 = **4,77** · `fx.usd_eur` 2026-09-04 = **0,86044** · `gold.lbma` 2026-09-04 = **4.415,4** · `silver.lbma` 2026-09-04 = **66,835** · `idx.sp500` 2026-09-04 close = **7.718,60** · `paxg` 2026-09-04 nến đóng (giá theo `samples/`); `wti` có **hai** dòng cùng ngày `spot`/`futures` chênh ~2 % | truy vấn đếm theo series + 6 literal |
| AC4 | Lượt hai cùng ngày: `inserted = 0`; `changed = 0` trừ FRED (được phép > 0 kèm `changes_sample` giải thích được); `max(ingested_at)` của dòng không đổi **không** tiến | `stats` + truy vấn |
| AC5 | Ép hỏng mỗi chế độ guard: FRED 1/15 series `503` ⇒ `failed`, 0 dòng, bằng chứng; Yahoo 3/37 `ALTSYMBOL` giả ⇒ `failed` (8 % > 5 %) | `etl_run` + `raw_payload` |
| AC6 | `yahoo --backfill`: `idx.sp500` **24.787 nến từ 1927-12-30**; `binance --backfill`: `btc` từ **2017-08-17**, `paxg` từ **2020-08-28**; lượt thường sau đó 0 đổi | truy vấn min/count |
| AC7 | Nến chưa đóng: chạy `yahoo --keys ^N225` **trong giờ Tokyo** (07:00–13:00 VN ngày giao dịch) ⇒ không có dòng ngày hôm đó; chạy `binance --keys BTCUSDT` bất kỳ lúc nào ⇒ không có dòng ngày UTC hôm nay | hai truy vấn |
| AC8 | Mọi lượt trên chạy dưới credential production trước khi coi là xong; log không chứa khoá FRED (`grep` chuỗi khoá vào log ra 0 — chạy dưới `set -a; . .env`) | dòng lệnh + exit code + grep |

## 8. Checklist tài liệu sống — cùng lượt với code *(§1.6, §1.7)*

- [ ] [roadmap.md](../../../00-overview/roadmap.md): lát 7 ✅ + **"Điểm vào cho lát 8"** (tin tức — thu thập); số test; §0.
- [ ] [yahoo.md](../../../10-sources/global/yahoo.md) *(đo 2026-09-05)*: host `query1.finance.yahoo.com` (§1.1 ghi chưa ghi host); **`meta.quoteType` không còn, cờ chết ở `meta.instrumentType`** (§1.3, §3, §8 cổng 3); cửa sổ ngắn trả 1 nến ở `^SET.BK`/`PSEI.PS` (bổ sung Bẫy 3); `^MERV` `currency` rỗng (§5.7); `currentTradingPeriod` để bỏ nến chưa đóng.
- [ ] [fx.md](../../../10-sources/global/fx.md) *(đo 2026-09-05)*: host v1 chuyển `api.frankfurter.dev/v1/` (301 từ host cũ); ETag/cache-control đã đo (§9 hết "chưa kiểm" cho mục này); trọn chuỗi 7.086 ngày / 672 KB.
- [ ] [commodities.md](../../../10-sources/global/commodities.md) *(đo 2026-09-05)*: §2.3 lược đồ JSON đã kiểm (`{d, v:[USD,GBP,EUR], is_cms_locked}`, null = tiền tệ chưa có); §6 ETag có nhưng không 304; dung lượng bạc 897 KB; giá trị điểm cuối.
- [ ] [fred.md](../../../10-sources/global/fred.md) *(đo 2026-09-05)*: §4.1 thêm bằng chứng vá hồi tố thứ hai (`PAYEMS` 07/2026: 158.858 → 158.913); ETag không có (§9 đóng mục).
- [ ] [crypto.md](../../../10-sources/global/crypto.md) *(đo 2026-09-05)*: lệch đồng hồ 991 ms; `limit=40` trả cả nến hôm nay chưa đóng (thêm vào Bẫy 3).
- [ ] [10-sources/README.md](../../../10-sources/README.md): ngày đo mới ở 5 dòng nguồn quốc tế.
- [ ] [market-data-store.md](../../../20-design/market-data-store.md): dòng ở §4/§8 ghi khối quốc tế đã có job.
- [ ] [backend/README.md](../../../../backend/README.md): mục "Chạy 5 job quốc tế", cờ, chế độ guard, cách đọc `changes_sample`, che khoá FRED.
- [ ] [database/README.md](../../../../database/README.md): số test.
- [ ] [90-records/README.md](../../README.md): dòng plan này (đã thêm lúc tạo thư mục, cập nhật trạng thái khi xong).
- [ ] `ledger.md` cùng thư mục, commit theo mốc.

## 9. Điểm cần chủ dự án duyệt tường minh

1. **Bảng mã Phụ lục A–E** — mặt API về sau; đổi sau này tốn migration đổi tên.
2. **`source='ecb'`** cho Frankfurter (danh tính dữ liệu, không phải tên API) — §4.2.
3. **`price_type`**: `DTWEXBGS` và `VIXCLS` = `close`; `DEXCHUS` = `fixing`; `DCOILWTICO` = `spot` — §4.7.
4. **LBMA chỉ USD** (`gold.lbma`, `silver.lbma`); GBP/EUR loại có chủ đích.
5. **Bằng chứng thô chỉ khi từ chối + `changes_sample`** thay cho "lưu body khi hash đổi" của lát 6 — §4.6, vì 15 MB/ngày.
6. **Cửa sổ Yahoo 400 ngày** thay vì 40 (số đo §2.1) và **`max_lag_days` 14** mặc định cho chỉ số.
7. **`paxg` là `crypto`/USDT/24x7**; **`quote_currency` của chỉ số = đồng tiền định giá**, `^MERV` = `ARS` hardcode.
8. **FRED `PAYEMS` × 1000 ⇒ `người`**, CPI/PCE giữ chỉ số kèm năm gốc trong `unit`.
9. **Guard Binance theo chế độ tất-cả-hoặc-không** (11 < 20) dù là nguồn "hiển thị".
10. `--keys` không guard, không đụng mốc nước — như lát 4–6.

---

## Phụ lục A — FRED (15 series, `source='fred'`)

`scale` nhân raw; `band` trên điểm mới nhất sau scale; `max_lag` ngày lịch so với hôm nay (UTC), suy từ fred.md §5.1 (T+1 → 6 để phủ cuối tuần dài; H.10 → 12; tháng → 60; PCE → 90).

| series_id | miền | code | name_vi | unit | freq | scale | band | max_lag | price_type |
|---|---|---|---|---|---|---|---|---|---|
| DFF | macro | us.rate.fedfunds.daily | Fed funds hiệu lực (ngày) | % | d | 1 | (−1, 25) | 6 | — |
| FEDFUNDS | macro | us.rate.fedfunds | Fed funds bình quân tháng | % | m | 1 | (−1, 25) | 60 | — |
| SOFR | macro | us.rate.sofr | SOFR | % | d | 1 | (−1, 25) | 6 | — |
| DGS2 | macro | us.yield.2y | Lợi suất TPCP Mỹ 2 năm | % | d | 1 | (−1, 25) | 6 | — |
| DGS10 | macro | us.yield.10y | Lợi suất TPCP Mỹ 10 năm | % | d | 1 | (−1, 25) | 6 | — |
| T10Y2Y | macro | us.yield.spread_10y2y | Chênh lợi suất 10 năm − 2 năm | % | d | 1 | (−5, 5) | 6 | — |
| T10YIE | macro | us.breakeven.10y | Lạm phát hoà vốn 10 năm | % | d | 1 | (−5, 15) | 6 | — |
| CPIAUCSL | macro | us.cpi | CPI Mỹ (SA, 1982–84 = 100) | chỉ số (1982-84=100) | m | 1 | (100, 1000) | 60 | — |
| PCEPILFE | macro | us.pce.core | PCE lõi (2017 = 100) | chỉ số (2017=100) | m | 1 | (50, 500) | 90 | — |
| UNRATE | macro | us.unemployment | Tỷ lệ thất nghiệp Mỹ | % | m | 1 | (0, 30) | 60 | — |
| PAYEMS | macro | us.payrolls | Việc làm phi nông nghiệp | người | m | 1000 | (1e8, 3e8) | 60 | — |
| DCOILWTICO | asset | wti *(có sẵn)* | Giá dầu WTI giao ngay | USD/thùng | d | 1 | (5, 500) | 10 | spot |
| DTWEXBGS | asset | dxy.broad | Chỉ số đô Mỹ broad (Fed, 01/2006 = 100) | điểm | d | 1 | (50, 200) | 12 | close |
| VIXCLS | asset | vix | VIX | điểm | d | 1 | (5, 150) | 6 | close |
| DEXCHUS | asset | fx.usd_cny | Tỷ giá CNY/USD (Fed H.10, noon NY) | CNY/1 USD | d | 1 | (3, 15) | 12 | fixing |

`region='us'` cho macro; asset: `wti` giữ `us`, `dxy.broad`/`vix` `us`, `fx.usd_cny` `cn`. Asset class: `wti` commodity (có sẵn), `dxy.broad`/`vix` **index** (`quote_currency='USD'`), `fx.usd_cny` **fx** (`quote_currency='CNY'`). `calendar='trading_days'`.

## Phụ lục B — ECB qua Frankfurter (6 series, `source='ecb'`)

`external_key` = mã tiền tệ trong `rates`, `external_sub=''`. Tất cả: class `fx`, unit `<CCY>/1 USD`, `price_type='fixing'`, `region='eu'`, `calendar='trading_days'`, `max_lag 6`.

| ccy | code | name_vi | quote_currency | band |
|---|---|---|---|---|
| EUR | fx.usd_eur | Tỷ giá EUR/USD (fixing ECB 14:15 CET) | EUR | (0.5, 2) |
| JPY | fx.usd_jpy | Tỷ giá JPY/USD | JPY | (50, 400) |
| GBP | fx.usd_gbp | Tỷ giá GBP/USD | GBP | (0.4, 1.5) |
| CAD | fx.usd_cad | Tỷ giá CAD/USD | CAD | (0.8, 2.5) |
| SEK | fx.usd_sek | Tỷ giá SEK/USD | SEK | (4, 20) |
| CHF | fx.usd_chf | Tỷ giá CHF/USD | CHF | (0.5, 2) |

Giá trị = số quote trên 1 USD, đúng chiều Frankfurter `from=USD`; chiều hiển thị EURUSD = 1/giá trị tính ở tầng đọc (bước 5).

## Phụ lục C — LBMA (2 series, `source='lbma'`)

`external_key` = tên file, `external_sub='0'` (vị trí USD trong `v`). Class `commodity`, `USD`, `USD/oz`, `fixing`, `region='global'`, `max_lag 6`.

| file | code | name_vi | band |
|---|---|---|---|
| gold_pm | gold.lbma | Vàng LBMA fixing PM (15:00 London) | (100, 20000) |
| silver | silver.lbma | Bạc LBMA fixing (12:00 London) | (1, 500) |

## Phụ lục D — Yahoo (37 series, `source='yahoo'`, → `ohlc_daily`)

Tất cả: class `index`, `unit='điểm'`, `calendar='trading_days'`, `price_type` NULL, `max_lag 14`, `external_sub=''`. `quote_currency` chép từ `meta.currency` đo 2026-09-05 (cổng (c) §5.3 đối chiếu mỗi lượt). `band` = (giá trị đo ÷ 10, × 10) trên `close` cuối, làm tròn — bắt lỗi 100× (đơn vị `USX`) chứ không bắt biến động thị trường.

| symbol | code | name_vi | ccy | region | close 2026-09-04 (đo) |
|---|---|---|---|---|---|
| ^GSPC | idx.sp500 | S&P 500 | USD | us | 7.718,60 |
| ^IXIC | idx.nasdaq | NASDAQ Composite | USD | us | 26.506,99 |
| ^DJI | idx.dow | Dow Jones Industrial | USD | us | 53.414,25 |
| ^RUT | idx.russell2000 | Russell 2000 | USD | us | 2.975,65 |
| ^GSPTSE | idx.tsx | S&P/TSX Composite | CAD | ca | 36.513,80 |
| ^MXX | idx.ipc | IPC Mexico | MXN | mx | 64.866,61 |
| ^BVSP | idx.bovespa | Bovespa | BRL | br | 185.147 |
| ^MERV | idx.merval | MERVAL | ARS *(nguồn rỗng)* | ar | 3.049.122 |
| ^FTSE | idx.ftse100 | FTSE 100 | GBP | gb | 10.831,10 |
| ^GDAXI | idx.dax | DAX | EUR | de | 26.046,40 |
| ^FCHI | idx.cac40 | CAC 40 | EUR | fr | 8.278,77 |
| ^SSMI | idx.smi | SMI | CHF | ch | 14.395,94 |
| ^BFX | idx.bel20 | BEL 20 | EUR | be | 5.852,54 |
| ^AEX | idx.aex | AEX | EUR | nl | 1.113,50 |
| ^IBEX | idx.ibex35 | IBEX 35 | EUR | es | 20.050,70 |
| FTSEMIB.MI | idx.ftsemib | FTSE MIB | EUR | it | 52.100 |
| ^N100 | idx.euronext100 | Euronext 100 | EUR | eu | 1.910,53 |
| ^STOXX50E | idx.stoxx50 | EURO STOXX 50 | EUR | eu | 6.392,93 |
| ^OMX | idx.omx30 | OMX Stockholm 30 | SEK | se | 3.284,08 |
| ^TA125.TA | idx.ta125 | TA-125 | ILS | il | 4.200,19 |
| ^N225 | idx.nikkei225 | Nikkei 225 | JPY | jp | 65.020,94 |
| ^HSI | idx.hsi | Hang Seng | HKD | hk | 25.650,87 |
| ^HSCE | idx.hscei | Hang Seng China Enterprises | HKD | hk | 8.555,03 |
| 000001.SS | idx.shcomp | Thượng Hải Composite | CNY | cn | 3.930,12 |
| 399001.SZ | idx.szcomp | Thâm Quyến Component | CNY | cn | 13.516,97 |
| ^TWII | idx.taiex | TAIEX | TWD | tw | 46.551,13 |
| ^KS11 | idx.kospi | KOSPI | KRW | kr | 6.687,21 |
| ^STI | idx.sti | Straits Times | SGD | sg | 5.801,96 |
| ^KLSE | idx.klci | FTSE Bursa Malaysia KLCI | MYR | my | 1.708,10 |
| ^JKSE | idx.jkse | Jakarta Composite | IDR | id | 6.636,48 |
| ^SET.BK | idx.set | SET | THB | th | 1.595,58 |
| PSEI.PS | idx.psei | PSEi | PHP | ph | 6.090,60 |
| ^BSESN | idx.sensex | BSE SENSEX | INR | in | 76.515,43 |
| ^NSEI | idx.nifty50 | NIFTY 50 | INR | in | 23.897,70 |
| ^AXJO | idx.asx200 | S&P/ASX 200 | AUD | au | 9.005,90 |
| ^NZ50 | idx.nzx50 | S&P/NZX 50 | NZD | nz | 13.974,18 |
| DX-Y.NYB | dxy.ice | Chỉ số đô Mỹ DXY (ICE) | USD | us | 99,16 |

## Phụ lục E — Binance (11 series, `source='binance'`, → `ohlc_daily`)

Tất cả: `quote_currency='USDT'` (không viết USD ở bất kỳ tầng nào), `calendar='24x7'`, `region='global'`, `price_type` NULL, `max_lag 2`, `external_sub=''`. `band` = (đo ÷ 10, × 10) trên `close` cuối.

| symbol | code | class | name_vi | close 2026-09-05 (đo, nến đang chạy) |
|---|---|---|---|---|
| PAXGUSDT | paxg | crypto | PAX Gold — vàng token hoá 24/7 (1 token ≈ 1 oz) | 4.433,13 |
| BTCUSDT | btc | crypto | Bitcoin | 79.520,01 |
| ETHUSDT | eth | crypto | Ethereum | 2.448,71 |
| BNBUSDT | bnb | crypto | BNB | 722,18 |
| ADAUSDT | ada | crypto | Cardano | 0,2106 |
| XRPUSDT | xrp | crypto | XRP | 1,3965 |
| TRXUSDT | trx | crypto | TRON | 0,3319 |
| LINKUSDT | link | crypto | Chainlink | 11,638 |
| DOGEUSDT | doge | crypto | Dogecoin | 0,08461 |
| SOLUSDT | sol | crypto | Solana | 101,68 |
| AVAXUSDT | avax | crypto | Avalanche | 7,408 |
