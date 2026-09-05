# Spec — lát 7b: cập nhật trong phiên cho dữ liệu có biểu đồ (giãn cách ngẫu nhiên · `--intraday` · nến đang chạy · FX qua Yahoo)

**Ngày:** 2026-09-05 tối · **Nhánh:** `feat/intraday-refresh` · **Trạng thái:** chờ chủ dự án duyệt spec
**Tiền đề:** [brief lát 7b](brief.md) (D1–D6 đã chốt, không mở lại) · [roadmap — Điểm vào cho lát 7b](../../../00-overview/roadmap.md) · [spec lát 7](../2026-09-05-global-etl/spec.md) (lõi series, năm nguồn) · [spec lát 6](../2026-09-05-wichart-macro-etl/spec.md) (WiChart)
**Brainstorm:** 5 câu hỏi, chủ dự án chốt 2026-09-05 chiều–tối — ghi tại §4. Số đo trong ngày: [`measure-yahoo-fx`](measure-yahoo-fx-2026-09-05.txt) · [`measure-binance-limit3`](measure-binance-limit3-2026-09-05.txt) · [`measure-frankfurter-cny`](measure-frankfurter-cny-2026-09-05.txt) · [`measure-yahoo-5d-partial`](measure-yahoo-5d-partial-2026-09-05.txt).

Tiêu chí xuyên suốt (kế thừa lát 6–7): **kho là sự thật nguồn sau chuẩn hoá đơn vị và neo ngày, không có gì tự tính**; mọi luật truy được về một số đo. Tiêu chí riêng của lát này: **lượt interval và lượt trọn/ngày là cùng một job, cùng một đường ghi, chỉ khác cửa sổ** — không có đường ghi thứ hai cho "giá mới nhất".

---

## 1. Vì sao lát này, và lát này là gì

Lát 7 thiết kế `asset.ohlc_daily` là nến đã chốt (Yahoo bỏ nến khi `now < regular.end`, Binance bỏ nến `closeTime > now`) nên chỉ số quốc tế và crypto luôn trễ một phiên. Chủ dự án chốt 2026-09-05 tối: **mọi dữ liệu có biểu đồ ngoài giá chứng khoán Việt Nam (đã realtime) và ngoài dữ liệu chu kỳ dài phải cập nhật liên tục trong phiên**. Lát này sửa ba lớp, **không đụng lược đồ**:

| Lớp | Hiện tại (lát 6–7) | Lát 7b |
|---|---|---|
| Luật chuẩn hoá | bỏ nến đang chạy (Yahoo, Binance) | **nến đang chạy vào kho**, UPSERT chỉ-khi-đổi tới khi phiên đóng (D1) |
| Cách gọi nguồn | cửa sổ 400 ngày / 40 nến, giãn cách cố định theo nguồn | cờ **`--intraday`** = cửa sổ ngắn (Yahoo 5 ngày, Binance 3 nến, WiChart tập key tần suất ngày); **giãn cách ngẫu nhiên đều 1–5 s** giữa hai lời gọi liên tiếp cùng nguồn (D5) |
| Phạm vi nguồn | Yahoo 37 chỉ số | Yahoo **+17 cặp FX** (D4, câu 1); ECB **+CNY**; FRED **−`DEXCHUS`** (câu 2) |

Bảng job sau lát:

| Job | Lượt trọn/ngày | Lượt `--intraday` | Lời gọi/lượt intraday |
|---|---|---|---|
| `etl yahoo` | cửa sổ 400 ngày, 54 mã | cửa sổ **5 ngày**, 54 mã, nhịp **30 phút**, 24/7 | 54 (~3 phút với giãn cách trung bình 3 s) |
| `etl binance` | 40 nến, 11 mã | **`limit=3`**, 11 mã, nhịp **5 phút**, 24/7 | 11 (~35 s) |
| `etl wichart` | 68 key | **47 key tần suất ngày** (43 `hang_hoa` + `dhtg`, `lsdh`, `lslnh`, `lshd`), nhịp **5 phút**, 24/7 | 47 (~2,4 phút) |
| `etl fred` | trọn chuỗi, 14 series | — (2 lượt/ngày, D3) | — |
| `etl fx` (ECB) · `etl lbma` | trọn chuỗi, 7 · 2 series | — (1 lượt/ngày) | — |

Không đăng ký task, lịch thuộc lát 13 (D6). Lát này chỉ làm cho job **chạy được ở nhịp đó** và **đo tải ở đúng nhịp**.

## 2. Dữ kiện đã đo vs giả định *(§4.8 bước 0)*

### 2.1 Đã đo — 2026-09-05 chiều (thứ 7), ~60 lời gọi thật + đọc kho

| Dữ kiện | Bằng chứng |
|---|---|
| 🔵 **`<CCY>=X` của Yahoo đúng chiều "quote trên 1 USD"**: `EUR=X` 0,8605 vs ECB fixing 04/09 0,86044 (**+0,007 %**) · `GBP=X` +0,10 % · `JPY=X` −0,02 % · `CHF=X` −0,03 % · `SEK=X` +0,15 %; `EURUSD=X`/`GBPUSD=X` là chiều ngược (`currency=USD`). 17/17 cặp kế hoạch `200`, `instrumentType=CURRENCY`, `meta.currency` = mã tiền quote, `exchangeTimezoneName=Europe/London`, `dataGranularity=1d` | measure-yahoo-fx |
| 🔴 **FX Yahoo có HAI nến cùng ngày London**: nến tại 23:00 UTC hôm trước (mở phiên London) có `close ≈ open` (dạng "rỗng"), và nến live tại `regularMarketTime` (21:29 UTC cho `EUR=X`) có H/L **khớp `regularMarketDayHigh/Low`** của `meta`. Dedupe theo ngày sàn "nến sau ghi đè nến trước" của `yahoo_normalize` lấy đúng nến live | measure-yahoo-fx (A1b) |
| Nến live của FX **không đồng bộ giữa các cặp** (`EUR=X` 21:29 UTC thứ 6, `CAD=X`/`CNY=X`/… 00:26–04:21 UTC **thứ 7** ⇒ ngày London 09-05, nến rất hẹp) — cùng quan sát yahoo.md §5.5 đo 15/08. Phiên `currentTradingPeriod.regular` = `[23:00 UTC hôm trước → 22:59 UTC]` | measure-yahoo-fx |
| **Binance `limit=3`** = 2 nến đã đóng + nến hôm nay đang chạy (`closeTime > now`), weight +2/lời gọi (A6 đúng) | measure-binance-limit3 |
| **Frankfurter có CNY**: `to=…,CNY` trả 6,7109 ngày 04/09 (FRED `DEXCHUS` cùng vai, trễ 3–9 ngày) | measure-frankfurter-cny |
| **Cửa sổ 5 ngày của Yahoo** trả 5–6 nến ở 50/54 mã, 4 nến ở 2 mã, **1 nến ở `^SET.BK`/`PSEI.PS`** (chỉ nến hiện tại — cùng họ Bẫy 3 "cửa sổ ngắn"); 44/44 lời gọi `200`, 77 ms trung bình | measure-yahoo-5d-partial |
| **WiChart registry**: 47 series `hang_hoa` đều `freq='d'`; nhóm `vi_mo` 25 key chỉ **4 key ngày** (`dhtg` 5 series, `lsdh` 3, `lslnh` 3, `lshd` 3), 21 key còn lại tháng/quý/năm | `wichart_registry.build()` |
| **WiChart hàng hoá có cập nhật trong ngày, vĩ mô một lần/ngày** — *chủ dự án đã kiểm, chốt 2026-09-05 tối*; giả định A3 của brief đóng theo lời chủ dự án, không phải theo số đo của trợ lý | brainstorm câu 4 |
| Kho trước lát: `ohlc_daily` Yahoo 335.601 nến / Binance 30.951, cả hai dừng ở **2026-09-04** (nến 09-05 đang chạy chưa vào — đúng lát 7); `wichart_guard.MIN_SAMPLE = 20` | truy vấn kho |

### 2.2 Giả định — CHƯA kiểm, đo trong plan (Task đo, trước khi chạy thật)

| # | Giả định | Cách đo | Nếu sai |
|---|---|---|---|
| A2 | Yahoo chịu **54 lời gọi mỗi 30 phút, giãn cách 1–5 s** | 4 lượt cách 30 phút (~2 giờ), 0 lỗi HTTP ⇒ "mức này an toàn" (§4.3 CLAUDE.md), không dò ngưỡng | hạ nhịp 60 phút, ghi vào bảng nhịp cho lát 13 |
| A4 | WiChart chịu **47 key × 12 lượt/giờ** (~13.500 lời gọi/ngày; đã đo 90 lời gọi liên tiếp sạch 05/09 sáng) | 12 lượt cách 5 phút (1 giờ) | hạ nhịp 15 phút |
| A5 | Nến Yahoo đang chạy trong cửa sổ 5 ngày **đổi `close` giữa hai lời gọi trong phiên** và ngày sàn không đổi | cần phiên thật: TA-125 chủ nhật 13:00–21:25 VN hoặc Nikkei thứ 2 07:00–13:00 VN — chính là AC3 | không có nến live cho chỉ số ⇒ chỉ FX/Binance có trong ngày; D1 vẫn đúng |
| A7 | FX Yahoo cuối tuần: nến "thứ 7" hẹp (`CAD=X` 09-05) là dòng hợp lệ trong `ohlc_daily` (giá thật, nguồn tự ghi) | quan sát sau lượt thật thứ 7/chủ nhật | nếu tầng đọc thấy nhiễu: lọc theo `calendar` ở tầng đọc, không xoá ở ETL |

## 3. Phạm vi

### 3.1 Trong phạm vi

- `http_fetch.Fetcher`: giãn cách ngẫu nhiên đều **[1, 5] s** trước mỗi lời gọi **có lời gọi trước đó** trong cùng `Fetcher` (kể cả lần thử lại và trang backfill); `rng` bơm được; giữ retry 3 + backoff 2/4/8.
- `wichart_fetch` chuyển sang `http_fetch` (đóng nợ lát 7), giữ mặt ngoài `Fetcher(get, sleep, clock)` / `fetch_one(key, group)` / `calls` / `retries` / `url` / `classify` / `FetchError` / `BadShape` để `wichart_job` và test lát 6 không đổi (trừ test giãn cách cố định).
- Cờ `--intraday` cho `yahoo` · `binance` · `wichart`; `series_job.run(..., intraday=False)`, `SourceSpec.supports_intraday`, `fetch_all(series, get, sleep, backfill, intraday)` cho cả 5 nguồn (FRED/ECB/LBMA nhận rồi bỏ qua); `stats["intraday"] = True`.
- Bỏ luật cắt nến đang chạy ở `yahoo_normalize` (cổng (d) §5.3 lát 7) và `binance_normalize`.
- Registry: Yahoo +17 FX (Phụ lục F); ECB +CNY; FRED −`DEXCHUS`.
- WiChart `--intraday` = lượt trên tập **`[s for s in registry if s.freq == 'd']`** (47 key), guard tỷ lệ như lượt trọn, **không** đẩy mốc nước.
- Ba phép đo A2/A4/A5 và tài liệu §8.

### 3.2 Ngoài phạm vi — ba loại *(§1.4)*

| Mục | Loại | Lý do |
|---|---|---|
| Cột cờ `is_final`/bảng quote riêng cho nến đang chạy | **Loại có chủ đích** | D1 chốt cách đơn giản; đảo ngược §10 brief: thêm cột bằng một migration nếu lát 10 chứng minh cần |
| Lịch chạy, task Scheduler, vòng lặp interval trong `etl` | **Đã có đường khác** | Lát 13 (bảng lịch trong code); §5.7 chỉ ghi bảng nhịp gợi ý |
| FRED interval; ETag/304 cho FRED/Yahoo | **Loại có chủ đích** | D3: 2 lượt/ngày; 46 lượt còn lại chỉ tải 12 MB để nhận `changed 0`; nguồn không có ETag (đo lát 7) |
| `DTWEXBGS` (`dxy.broad`) | **Giữ** — chủ dự án chốt câu 2 (a) | chỉ số broad trade-weighted khác DXY ICE, 1 lời gọi/lượt, không đụng khoá ai |
| Yahoo `CNH=X`, lợi suất `^TNX`…, họ biến động, ETF | **Loại có chủ đích** | ngoài danh sách chủ dự án chốt (câu 1 (b)); cùng lý do spec lát 7 §3.2 |
| Nghịch đảo OHLC (`EURUSD=X` → 1/x) | **Đã kiểm — không cần** | `<CCY>=X` đã đúng chiều (§2.1) |
| Binance `429`/`Retry-After`, `_pause` khi lỗi, `ZoneInfo` tên lạ | **Đã có đường khác** | nợ lát 7, không mở ở đây |
| Pháp lý | — | trạng thái một dòng ở CLAUDE.md §2.1; Yahoo/Binance/LBMA/Frankfurter việc của chủ dự án |

## 4. Quyết định *(§4.8 — chủ dự án chốt 2026-09-05 chiều–tối)*

### 4.1 Danh sách FX Yahoo: 6 ECB + 10 châu Á + VND *(câu 1 → (b))*

| Phương án | Lời gọi thêm/lượt | Lý do loại |
|---|---|---|
| (a) 6 cặp ECB | 6 | thiếu nhóm châu Á — bối cảnh tỷ giá sát Việt Nam nhất |
| **(b) 6 + CNY, KRW, THB, SGD, TWD, INR, IDR, MYR, PHP, HKD + `VND=X`** ✅ | 17 | — chọn; cả 17 đã đo `200` cùng ngày |

`VND=X` là tỷ giá thị trường, **không thay `dhtg`** (yahoo.md §6.1) — vai đối chứng, mã `fx.usd_vnd.market`. **Đảo ngược khi:** A2 cho thấy 54 mã/30 phút không an toàn ⇒ cắt nhóm châu Á trước, giữ 6 ECB + VND.

### 4.2 Bỏ `DEXCHUS`, thêm CNY vào ECB, giữ `DTWEXBGS` *(câu 2 → (a))*

Hệ quả bắt buộc của 4.1 và luật khoá: ECB ghi `('fx.usd_cny', ngày, 'fixing')` đúng khoá `DEXCHUS` đang ghi ⇒ hai nguồn giành một dòng. Loại (b) bỏ cả `DTWEXBGS`: mất chuỗi broad của Fed mà không có gì thay. Loại (c) đổi FRED CNY thành asset riêng `fx.usd_cny.ny`: đúng luật "khác mốc chốt = asset khác" nhưng thêm asset chưa ai cần. Bỏ = xoá dòng registry ⇒ `load_registry` xoá dòng ánh xạ `(fred, DEXCHUS)` đầu lượt (luật I1), **dòng `asset` và dữ liệu `price_daily` giữ nguyên**; `test_e49` không còn cần ngoại lệ cho `fx.usd_cny`. **Đảo ngược khi:** cần chuỗi noon-NY riêng ⇒ thêm lại dòng với mã `fx.usd_cny.ny`.

### 4.3 Tên mã FX Yahoo: hậu tố `.market` cho cả 17 *(câu 3 → (a))*

`fx.usd_<ccy>.market` — một hậu tố cho cùng nguồn, cùng bản chất (giá thị trường liên tục, nến chốt nửa đêm London), khớp cách WiChart đặt `fx.usd_vnd.central/.bank_sell/.free_sell` theo mốc. Loại (b) `.close` + `.market`: hai hậu tố cho một loại chuỗi, "close" gây hiểu nhầm với chuỗi cập nhật trong phiên. Loại (c) `.yahoo`: đặt theo tên nguồn, trái luật "source là danh tính dữ liệu" (spec lát 7 §4.2). Đây là điểm **khó đảo ngược nhất** của lát (đổi tên sau tốn migration) — §9.1.

### 4.4 WiChart `--intraday` = mọi key tần suất ngày, chạy 24/7 *(câu 4–5)*

Chủ dự án chốt: hàng hoá cập nhật trong ngày, vĩ mô một lượt/ngày ở khung cố định; **`dhtg` và các key lãi suất ngày cũng phải interval** (rà lại 25 key `vi_mo`: `dhtg` NHTM/tự do đổi nhiều lần trong ngày; `lslnh` SBV đăng sau phiên; `lsdh` đổi vài lần/năm nhưng phải thấy ngay; `lshd` ngân hàng đổi biểu bất kỳ ngày nào). Tiêu chí ghi vào code là **`freq == 'd'`** (47 key), không phải danh sách tay — thêm key ngày sau này tự vào. Loại "đo từng key giờ nào đổi rồi chọn tập": tốn một ngày đo cho một quyết định chủ dự án đã kiểm; loại "chỉ `dhtg`": sót lãi suất. **Đảo ngược khi:** A4 cho thấy 47 × 12/giờ không an toàn ⇒ nhịp 15 phút trước, cắt key sau.

### 4.5 Giờ chạy interval: 24/7 cho cả ba nguồn *(câu 4)*

Chủ dự án: "cập nhật thì cứ chạy 24/7". Cuối tuần Yahoo/WiChart `changed = 0` vô hại, Binance vẫn có nến. Chi phí Yahoo ≈ 2.600 lời gọi/ngày (nằm trong A2). Loại "chỉ khi có sàn mở": bảng giờ 21 sàn + FX + DXY gần như phủ 24/5, phức tạp không đổi lấy gì.

### 4.6 Bốn điểm trợ lý tự chốt (đảo ngược được, §9 để rà)

| # | Chốt | Vì sao | Đảo ngược khi |
|---|---|---|---|
| I | Lượt `--intraday` Yahoo/Binance **đẩy `watermark`** (lượt trọn registry, có guard); WiChart `--intraday` là lượt con (47/68 key) ⇒ **không** đẩy, lượt trọn hằng ngày giữ mốc | một luật: "đẩy mốc khi lượt trọn registry" — y `series_job` hiện tại, không thêm nhánh | lát 12 cần phân biệt "mốc lượt trọn" và "mốc lượt ngắn" ⇒ thêm cột, không đổi luật |
| II | Guard lượt intraday: Yahoo 54 và WiChart 47 ≥ `MIN_SAMPLE` ⇒ **tỷ lệ như thường**; Binance 11 giữ tất-cả-hoặc-không | không ngưỡng mới; cổng `stale` của Yahoo (≥ 1 nến trong cửa sổ, `regularMarketTime` ≤ 14 ngày) với cửa sổ 5 ngày: sàn nghỉ lễ dài (Tết 2 sàn CN + HK/TW) rơi vào `stale` ≤ 5/54 = 9 % < 20 % ⇒ bỏ series đó, lượt vẫn ghi | một kỳ nghỉ đồng thời > 20 % sàn ⇒ nới `stale` cho intraday, không nới cho lượt trọn |
| III | Giãn cách áp **giữa hai lời gọi liên tiếp** trong cùng `Fetcher` (không trước lời gọi đầu), **cộng thêm** backoff khi thử lại | D5 "kể cả backfill và retry"; ECB 1 lời gọi/lượt không ngủ vô ích | — |
| IV | `--intraday` và `--backfill` **loại trừ nhau** (exit 2 trước `open_run`); `fred`/`fx`/`lbma` không có `--intraday` (exit 2 như `--backfill`) | hai cửa sổ trái nhau trong một lượt vô nghĩa | — |

## 5. Thiết kế

### 5.1 `http_fetch.Fetcher` — giãn cách ngẫu nhiên

`Fetcher(get, classify, sleep, clock, rng=random.Random(), gap=(1.0, 5.0), retries=3, backoff=(2, 4, 8), timeout=30.0)`; **bỏ `min_interval`** (mọi nguồn đang truyền `MIN_INTERVAL` bỏ đối số đó). Trước **mỗi lần gọi `get`** (mỗi attempt): nếu đã có lời gọi trước trong `Fetcher` này ⇒ `sleep(rng.uniform(*gap))`; retry vẫn `sleep(backoff[attempt])` sau lời gọi hỏng như cũ. Ghi `self.gaps: list[float]` để test và log đọc. `open_fetcher(classify, get=None, sleep, clock, headers, rng=None, **kw)`.

Thời gian một lượt với trung bình 3 s: Yahoo 54 ≈ 2,7 phút · Binance 11 ≈ 33 s · WiChart 47 ≈ 2,4 phút · trọn 68 ≈ 3,4 phút · FRED 15 ≈ 45 s · backfill Yahoo 54 ≈ 3 phút, Binance ~39 trang ≈ 2 phút. Không lượt nào chồng lên lượt kế của chính nó.

### 5.2 `wichart_fetch` — mặt ngoài giữ, ruột dùng `http_fetch`

`wichart_fetch.Fetcher(get, sleep, clock, rng=None)` là lớp bọc mỏng quanh `http_fetch.Fetcher`: `get` của WiChart trả **2-tuple** `(status, text)` (test e37/e41 tiêm vậy) ⇒ bọc thành 3-tuple `(status, text, {})`; `fetch_one(key, group)` gọi `inner.fetch_one(url(key, group), key)`; `calls`/`retries` đọc từ `inner.calls`/`inner.retries_done`; `FetchError`/`BadShape` **là** lớp của `http_fetch` (re-export). Thông điệp lỗi: `BadShape` vẫn `"{key}: response không có chart.series"` (test e37 assert chuỗi này) — `classify` của WiChart trả `bad_shape` và `wichart_fetch` bọc lại thông điệp. Xoá `MIN_INTERVAL`, `TIMEOUT`, `RETRIES`, `BACKOFF`, `HEADERS` riêng (dùng `DEFAULT_HEADERS` chung — cùng User-Agent). `verify_wichart.py` không đụng (script tài liệu, không import module này).

### 5.3 `--intraday` xuyên suốt

| Chỗ | Đổi |
|---|---|
| `__main__` | `--intraday` cho `yahoo`, `binance`, `wichart`; `yahoo`/`binance` truyền `intraday=` vào `mod.run`; `--intraday --backfill` ⇒ `parser.error` (exit 2) |
| `series_job.SourceSpec` | `supports_intraday: bool = False`; `fetch_all: (series, get, sleep, backfill, intraday)` |
| `series_job.run` | tham số `intraday=False`; `intraday and not spec.supports_intraday` ⇒ log + `return 2` trước `open_run` (y `backfill`); `stats["intraday"] = True`; **không** đổi luật `subset`/`watermark`/guard (4.6-I, II) |
| `yahoo_fetch.fetch_all` | `INTRADAY_WINDOW_DAYS = 5`: `period1 = now − 5·86400` khi `intraday`; 400 ngày khi thường; `BACKFILL_PERIOD1` khi backfill |
| `binance_fetch._fetch_with` | `INTRADAY_LIMIT = 3` khi `intraday`, `DAILY_LIMIT = 40` khi thường |
| `fred_fetch`/`fx_fetch`/`lbma_fetch.fetch_all` | nhận `intraday` và bỏ qua (`supports_intraday=False` chặn từ `run`) |
| `wichart_job.run(keys, dry_run, intraday=False, get, sleep, rng=None)` | `intraday` ⇒ `series = [s for s in registry if s.freq == 'd']` (47 key); `keys` và `intraday` cùng lúc ⇒ `RuntimeError` trước fetch; guard **có** (không phải `subset`); `stats["intraday"] = True`; **không** `upsert_domain_state`, **không** `stats["watermark"]`; `store_payload_if_changed` vẫn chạy (payload WiChart nhỏ, luật lát 6) |

### 5.4 Nến đang chạy vào kho — hai luật bỏ, một luật giữ

| Nguồn | Bỏ | Giữ | Ngày của nến đang chạy |
|---|---|---|---|
| Yahoo | biến `cut` (cổng (d) §5.3 lát 7) và mọi tham chiếu `currentTradingPeriod` trong `bars` | dedupe theo ngày sàn "nến sau ghi đè nến trước" — với FX chính là luật chọn nến live thay nến rỗng 23:00 UTC (§2.1); cổng (a)(b)(c), `stale`, `band` trên nến cuối | `_utc(ts).astimezone(exchangeTimezoneName).date()` — chỉ số: ngày phiên; FX: ngày London của `regularMarketTime` |
| Binance | `if k[6]/1000 > now.timestamp(): continue` | `stale` đổi câu chữ: "nến cuối" thay "nến đóng cuối" (`last_day ≥ today − max_lag`); `band` | ngày UTC của `k[0]` (seam 4 bước 5) |

Hệ quả cho lát 13 (ghi §5.7): ruling "xếp `yahoo` sau 11:00 VN vì DXY" của lát 7 **hết hiệu lực** — nến DXY vào kho ngay trong lượt intraday. `changes_sample` chỉ có ở `apply` (điểm) nên FRED không nhiễu; `stats.changed` của Yahoo/Binance/WiChart-hàng-hoá > 0 mỗi lượt intraday là **hành vi mong đợi** (lát 12 không coi là bất thường).

### 5.5 Registry

- **Yahoo +17** (Phụ lục F): `asset_class='fx'`, `quote_currency=<ccy>`, `unit='<CCY>/1 USD'`, `region` theo nước, `calendar='trading_days'`, `price_type=None`, `shape='ohlc'`, **`max_lag_days=6`** (cùng ECB; FX cập nhật mỗi ngày làm việc, khác chỉ số 14 ngày phủ Tết), `band` = (đo ÷ 10, × 10) làm tròn trên `close` 04/09 — bắt lỗi 100×, không bắt biến động. Yahoo thành 54 series.
- **ECB +CNY**: `("CNY", "fx.usd_cny", "Tỷ giá CNY/USD (fixing ECB)", "3", "15")` — mã **giữ `fx.usd_cny`** (asset đã có từ FRED, cùng `asset_id`, dòng ánh xạ mới `(ecb, CNY)`), `name_vi` đổi theo nguồn mới. URL `to=EUR,JPY,GBP,CAD,SEK,CHF,CNY`; cổng "đủ tiền tệ ở ngày cuối" thành 7.
- **FRED −`DEXCHUS`**: 14 series (11 macro + 3 asset). Phụ lục A spec lát 7 sửa kèm ghi "bỏ ở lát 7b".
- `test_e49`: 5 registry + WiChart không trùng mã — `fx.usd_cny` nay chỉ ECB; `fx.usd_vnd.market` không trùng 5 mã `fx.usd_vnd.*` của WiChart.

### 5.6 Bằng chứng và sổ

Y lát 7: `raw_payload` chỉ khi từ chối; `ops.etl_run` mỗi lượt intraday một dòng (288 dòng/ngày Binance, 288 WiChart, 48 Yahoo — chấp nhận, bảng nhỏ; lát 12 đọc `stats.intraday` để tách). Job name không đổi (`global.yahoo`…), phân biệt bằng `stats.intraday`.

### 5.7 Bảng nhịp cho lát 13 (thay §5.6 spec lát 7, giờ VN)

| Job | Nhịp | Ghi chú |
|---|---|---|
| `binance --intraday` | 5 phút, 24/7 | `binance` trọn 07:15 (nến UTC đóng 07:00) |
| `wichart --intraday` | 5 phút, 24/7 | `wichart` trọn 1 lượt/ngày, khung cố định **08:30** (giả định nạp trước 08:00 của lát 6 — chưa đo, chỉ ảnh hưởng vĩ mô) |
| `yahoo --intraday` | 30 phút, 24/7 | `yahoo` trọn 1 lượt/ngày 11:00 (cửa sổ 400 ngày vá lỗ) — ràng buộc "sau 11:00 vì DXY" hết hiệu lực nhưng giờ này vẫn tiện |
| `fred` | 05:00 và 20:00 | chuỗi ngày sau 16:15 New York; báo cáo tháng 08:30 New York = 19:30 VN |
| `fx` (ECB) · `lbma` | 22:30 | fixing 14:15 CET · 15:00/12:00 London |

## 6. Seam test *(chốt cùng plan — §4.5.2)*

Expected từ mẫu thật chụp 2026-09-05 (`samples/yahoo-EURX-5d.json` — bản chụp 3 nến cuối `EUR=X`, có hai nến ngày 09-04; `samples/binance-BTCUSDT-3.json` — `limit=3` với nến 09-05 `closeTime > now`) hoặc mẫu lát 7 đã có, hoặc giải tay.

| Seam | Ca phải có |
|---|---|
| `http_fetch.Fetcher` | với `rng` giả trả `[1.0, 4.99, 3.2]` và `clock` giả: hai lời gọi liên tiếp ⇒ `sleep` gọi đúng 1 lần với 1.0 (không ngủ trước lời gọi đầu); lời gọi hỏng rồi thử lại ⇒ `sleep(gap)` **và** `sleep(2)` đều được gọi; với `random.Random(0)` thật 20 khoảng ∈ [1, 5] và không phải mọi khoảng bằng nhau; `gaps` ghi đúng số khoảng |
| `wichart_fetch.Fetcher` | toàn bộ `test_e37` xanh trừ `test_min_interval_sleeps_between_two_calls` đổi thành `test_random_gap_between_two_calls` (khoảng ∈ [1, 5]); `get` 2-tuple vẫn chạy; `BadShape` thông điệp `"cpi: response không có chart.series"` |
| `series_job.run` | `intraday=True` ⇒ `spec.fetch_all` nhận `intraday=True`, `stats.intraday == True`, watermark **có** (lượt trọn); `intraday` với `supports_intraday=False` ⇒ `2` trước `open_run` (0 dòng `etl_run`) |
| `__main__` | `etl yahoo --intraday --backfill` ⇒ exit 2; `etl fred --intraday` ⇒ exit 2 |
| `yahoo_fetch.fetch_all` | `intraday=True` ⇒ URL có `period1 = period2 − 432000`; thường ⇒ `− 34 560 000`; backfill ⇒ `−2208988800` |
| `binance_fetch` | `intraday=True` ⇒ URL `limit=3`; thường `limit=40` |
| `yahoo_normalize` | `test_open_candle_is_dropped_while_the_regular_session_is_still_running` đổi thành `…is_kept…`: fixture `yahoo-GSPC-10d.json` với `now` **trong** phiên 09-04 (14:00 UTC) ⇒ **8** bars, nến cuối 09-04 close = literal fixture 7718.60009765625; `EUR=X` mẫu mới: hai nến ngày London 09-04 ⇒ **một** bar 09-04 với `close = 0.8604999780654907` (nến live), `high = 0.8626999855041504` (khớp `regularMarketDayHigh`), không phải 0.859969973564148; `CAD=X` nến 04:21 UTC 09-05 ⇒ bar ngày 09-05 |
| `binance_normalize` | `test_open_time_utc_date_string_prices_and_open_candle_dropped` đổi: 5 nến `binance-PAXGUSDT-5.json` với `NOW` ⇒ **5** bars, nến 09-05 close `Decimal('4433.13')` (literal fixture); `stale` khi nến cuối < today − 2 |
| `yahoo_registry.build` | 54 series; 17 `asset_class='fx'` có `unit == f"{ccy}/1 USD"`, `max_lag_days == 6`; `fx.usd_eur.market` band chứa 0.8605, không chứa 86.05; `VND=X` → `fx.usd_vnd.market` |
| `fx_registry`/`fx_normalize` | 7 series; `CNY: 6.7109` ngày 2026-09-04 ⇒ `Point('fx.usd_cny', 2026-09-04, 6.7109, 'fixing')`; ngày thiếu 1/7 tiền tệ ⇒ `shape` |
| `fred_registry` | 14 series, không có `DEXCHUS`; `test_e44` số đếm 15 → 14, registry `asset` 4 → 3 |
| `registry.load_registry` | chạy `load_registry(…, 'fred')` với 14 series khi kho có dòng `(fred, DEXCHUS)` ⇒ `removed == 1`, asset `fx.usd_cny` **còn**, dữ liệu `price_daily` của nó còn; rồi `load_registry(…, 'ecb')` 7 series ⇒ `fx.usd_cny` **cùng `asset_id`** (không tạo asset mới), thêm dòng `(ecb, CNY)` |
| `test_e49` | 5 registry + WiChart: 0 mã trùng (không còn ngoại lệ cho `fx.usd_cny`) |
| `wichart_job.run(intraday=True)` | `get` giả: gọi đúng **47 key** (không có `cpi`), `stats.intraday == True`, không có `stats.watermark`, `data_domain_state` **không** đổi; guard chạy (ép 3/47 bad shape = 6,4 % ⇒ `failed`); `keys=[…]` cùng `intraday=True` ⇒ exit 2 |
| quyền | `test_e43` role: thêm `SET LOCAL ROLE dlck_etl` qua `apply_ohlc` với dòng đã có (UPDATE — đường ghi đè nến đang chạy, lần đầu có trong production) |
| lát 6–7 không đổi | `test_e36`–`e48` xanh sau thay đổi, trừ các test đổi tên nêu trên |

## 7. Tiêu chí nghiệm thu

| | Nội dung | Bằng chứng phải dán |
|---|---|---|
| AC1 | Toàn bộ test xanh | số test trước (**709 passed, 2 skipped**) / sau |
| AC2 | `--intraday --dry-run` trên nguồn sống: `yahoo` 54/54 ok (trừ `stale` ở sàn nghỉ nếu có), mỗi mã ≤ 6 nến; `binance` 11/11, 3 nến/mã; `wichart` 47/47 key | `stats` ba job (`calls`, `bars`/`points`, `intraday: true`) |
| AC3 | **Nến đang chạy vào kho và đổi** — thay AC7 nửa Yahoo của lát 7: `binance --intraday --keys BTCUSDT` hai lần cách 5 phút (bất kỳ lúc nào) ⇒ dòng ngày UTC hôm nay tồn tại, `close` **khác nhau**, `ingested_at` tiến; `yahoo --intraday --keys ^TA125.TA` (chủ nhật 13:00–21:25 VN) hoặc `^N225` (thứ 2 07:00–13:00 VN) hai lần cách 15 phút ⇒ dòng ngày hôm đó, `close` khác nhau; `wichart --intraday --keys vang_the_gioi,dhtg` hai lần trong giờ làm việc ⇒ điểm ngày hôm đó đổi (WiChart: chờ ngày làm việc — thứ 2) | 6 truy vấn kèm giờ chạy |
| AC4 | Lượt thường (không `--intraday`) ngay sau AC3: `changed` **chỉ** ở nến/điểm ngày hiện tại, `inserted = 0`, không đụng nến đã chốt (`max(ingested_at)` của dòng < hôm nay không tiến) | `stats.changed` + truy vấn |
| AC5 | FX Yahoo: 17 cặp có dòng ngày gần nhất trong `ohlc_daily`; 7 cặp có ECB (6 + CNY) lệch fixing cùng ngày **< 1 %**, đúng chiều quote trên 1 USD; `fx.usd_cny` có dòng ECB `fixing` ngày mới nhất và dòng `(fred, DEXCHUS)` **không còn** trong `asset_external_id` | bảng đối chiếu + 2 truy vấn |
| AC6 | Giãn cách: từ log có timestamp của một lượt `fred` thật (15 lời gọi), 14 khoảng đều ∈ [1, 5] s (cộng thời gian phản hồi), không hai khoảng nào bằng nhau tới 0,01 s | log + bảng khoảng |
| AC7 | Tải ở đúng nhịp: A2 Yahoo 4 lượt × 54 cách 30 phút; A4 WiChart 12 lượt × 47 cách 5 phút — **0 lỗi HTTP, 0 tín hiệu chặn** ⇒ ghi "mức này an toàn" vào yahoo.md §7 / wichart.md §2.5 kèm ngày đo | log đếm + số ms |
| AC8 | Mọi lượt trên chạy dưới credential production (`ETL_DATABASE_URL`, role `dlck_etl`); khoá FRED 0 lần trong log/`stats`/`raw_payload` | dòng lệnh + exit code + grep |

## 8. Checklist tài liệu sống — cùng lượt với code *(§1.6, §1.7)*

- [ ] [spec lát 7](../2026-09-05-global-etl/spec.md): §4.4 cửa sổ (+intraday), §5.2 `MIN_INTERVAL` → giãn cách ngẫu nhiên, §5.3 bỏ cổng (d) Yahoo và luật `closeTime` Binance, §5.6 trỏ sang §5.7 ở đây, Phụ lục A bỏ `DEXCHUS`, Phụ lục B +CNY, Phụ lục D +Phụ lục F — mỗi chỗ ghi *"đổi ở lát 7b"* kèm ngày sửa, không xoá câu cũ.
- [ ] [market-data-store.md](../../../20-design/market-data-store.md): ghi chú kèm ngày sửa — "dòng mới nhất của mỗi mã trong `asset.ohlc_daily`, và điểm ngày hiện tại của series tần suất ngày trong `asset.price_daily`/`macro.observation` từ WiChart, **có thể đang chạy** — tầng đọc suy 'đang chạy' từ lịch sàn (`calendar`), không có cột cờ".
- [ ] [yahoo.md](../../../10-sources/global/yahoo.md) *(đo 2026-09-05)*: §5.5 chiều mã `<CCY>=X` đã kiểm 17 cặp, **hai nến cùng ngày London** (nến 23:00 rỗng vs nến live), nến cuối tuần hẹp; §7 mức tải A2 "an toàn"; §8 cổng (d) không còn dùng.
- [ ] [fx.md](../../../10-sources/global/fx.md): §7 vai Yahoo = chuỗi trong ngày `.market`, ECB vẫn mốc chuẩn; CNY thêm vào ETL.
- [ ] [fred.md](../../../10-sources/global/fred.md): `DEXCHUS` không nạp nữa (đã có đường khác: ECB).
- [ ] [wichart.md](../../../10-sources/macro/wichart.md): §2.5 mức tải A4; ghi "hàng hoá và 4 key ngày cập nhật trong ngày — chủ dự án kiểm 2026-09-05; giờ nạp vĩ mô chưa đo".
- [ ] [backend/README.md](../../../../backend/README.md): mục 5 job quốc tế + WiChart: `--intraday`, giãn cách, bảng nhịp §5.7, cách đọc `stats.intraday`/`changed`.
- [ ] [roadmap.md](../../../00-overview/roadmap.md): lát 7b ✅, bảng nhịp cho lát 13, AC7 lát 7 đóng bằng AC3 ở đây, số test, "Điểm vào cho lát 8" cập nhật.
- [ ] [10-sources/README.md](../../../10-sources/README.md): ngày đo mới cho Yahoo/WiChart/Frankfurter.
- [ ] [database/README.md](../../../../database/README.md): số test.
- [ ] [90-records/README.md](../../README.md): trạng thái dòng plan này; `ledger.md` cùng thư mục.

## 9. Điểm cần chủ dự án duyệt tường minh

1. **Hậu tố `.market`** cho 17 mã FX Yahoo (câu 3) — mặt API, đổi sau tốn migration.
2. **Bỏ `DEXCHUS`**, giữ `DTWEXBGS`, ECB +CNY dùng **cùng mã `fx.usd_cny`** (câu 2) — dữ liệu FRED cũ của `fx.usd_cny` giữ nguyên trong `price_daily` (cùng `price_type='fixing'`, khác mốc chốt: noon NY tới 08/28 rồi ECB 14:15 CET từ nay — **một bậc nhỏ tại điểm đổi nguồn**, cùng loại cảnh báo CLAUDE.md §2.3; chấp nhận vì H.10 là tuần và đã dừng 08/28, hay muốn xoá 10 năm dòng FRED của `fx.usd_cny`?).
3. **`INTRADAY` WiChart theo `freq == 'd'`** = 47 key (câu 4–5), 13.500 lời gọi/ngày.
4. Bốn điểm tự chốt §4.6 (mốc nước, guard, giãn cách kể cả retry, cờ loại trừ).
5. `max_lag_days = 6` cho FX Yahoo (chỉ số giữ 14).
6. A5 đo bằng chính AC3 trên phiên thật (TA-125 chủ nhật hoặc Nikkei thứ 2), không có phép đo riêng.
7. Lượt intraday ghi `ops.etl_run` mỗi lần (≈ 624 dòng/ngày cho 3 job).

---

## Phụ lục F — Yahoo FX (17 series, `source='yahoo'`, → `ohlc_daily`)

Tất cả: `asset_class='fx'`, `unit='<CCY>/1 USD'`, `calendar='trading_days'`, `price_type` NULL, `max_lag 6`, `external_sub=''`, `shape='ohlc'`. `quote_currency` = `meta.currency` đo 2026-09-05 (cổng (c) đối chiếu mỗi lượt). `band` = (đo ÷ 10, × 10) làm tròn trên `regularMarketPrice` 2026-09-05.

| symbol | code | name_vi | ccy | region | giá đo 2026-09-05 | band |
|---|---|---|---|---|---|---|
| EUR=X | fx.usd_eur.market | Tỷ giá EUR/USD (thị trường, Yahoo) | EUR | eu | 0,8605 | (0.08, 9) |
| GBP=X | fx.usd_gbp.market | Tỷ giá GBP/USD (thị trường, Yahoo) | GBP | gb | 0,7398 | (0.07, 7.5) |
| JPY=X | fx.usd_jpy.market | Tỷ giá JPY/USD (thị trường, Yahoo) | JPY | jp | 156,221 | (15, 1600) |
| CAD=X | fx.usd_cad.market | Tỷ giá CAD/USD (thị trường, Yahoo) | CAD | ca | 1,3837 | (0.13, 14) |
| SEK=X | fx.usd_sek.market | Tỷ giá SEK/USD (thị trường, Yahoo) | SEK | se | 9,5655 | (0.9, 96) |
| CHF=X | fx.usd_chf.market | Tỷ giá CHF/USD (thị trường, Yahoo) | CHF | ch | 0,809 | (0.08, 8.1) |
| CNY=X | fx.usd_cny.market | Tỷ giá CNY/USD (thị trường, Yahoo) | CNY | cn | 6,7108 | (0.67, 67) |
| KRW=X | fx.usd_krw.market | Tỷ giá KRW/USD (thị trường, Yahoo) | KRW | kr | 1.351,1 | (135, 13500) |
| THB=X | fx.usd_thb.market | Tỷ giá THB/USD (thị trường, Yahoo) | THB | th | 32,87 | (3.2, 330) |
| SGD=X | fx.usd_sgd.market | Tỷ giá SGD/USD (thị trường, Yahoo) | SGD | sg | 1,2666 | (0.12, 13) |
| TWD=X | fx.usd_twd.market | Tỷ giá TWD/USD (thị trường, Yahoo) | TWD | tw | 31,62 | (3.1, 320) |
| INR=X | fx.usd_inr.market | Tỷ giá INR/USD (thị trường, Yahoo) | INR | in | 94,49 | (9.4, 950) |
| IDR=X | fx.usd_idr.market | Tỷ giá IDR/USD (thị trường, Yahoo) | IDR | id | 17.633 | (1760, 176000) |
| MYR=X | fx.usd_myr.market | Tỷ giá MYR/USD (thị trường, Yahoo) | MYR | my | 4,0425 | (0.4, 41) |
| PHP=X | fx.usd_php.market | Tỷ giá PHP/USD (thị trường, Yahoo) | PHP | ph | 62,62 | (6.2, 630) |
| HKD=X | fx.usd_hkd.market | Tỷ giá HKD/USD (thị trường, Yahoo) | HKD | hk | 7,8407 | (0.78, 79) |
| VND=X | fx.usd_vnd.market | Tỷ giá USD/VND thị trường (Yahoo, đối chứng — không thay `dhtg`) | VND | vn | 26.054 | (2600, 261000) |
