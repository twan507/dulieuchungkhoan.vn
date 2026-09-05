# Brief — lát 7b: cập nhật trong phiên cho dữ liệu có biểu đồ (interval, nến đang chạy, FX qua Yahoo)

**Ngày viết:** 2026-09-05 tối, ngay sau khi lát 7 gộp `main` (`7405184`) · **Người viết:** trợ lý, theo yêu cầu chủ dự án · **Trạng thái:** brief để session mới đi đủ quy trình [CLAUDE.md §4.1](../../../CLAUDE.md) (brainstorm → spec → plan → subagent → review → verify). **Đây không phải spec** — spec viết ở session mới, sau khi đo phần giả định ở §4.

**Vị trí trong lộ trình:** chèn **ngay sau lát 7, trước lát 8** (chủ dự án gọi tên 2026-09-05 tối — đúng luật "việc cắt ngang chỉ làm khi chủ dự án gọi tên" của roadmap §3). Thứ tự sau đó giữ nguyên: lát 8 tin tức → … → lát 13 scheduler → lát 14 VPS.

---

## 1. Vì sao có lát này

Lát 7 thiết kế `asset.ohlc_daily` là bảng **nến ngày đã chốt**: nến đang chạy bị bỏ (Yahoo: khi `now < currentTradingPeriod.regular.end`; Binance: khi `closeTime > now`), nên giá mới nhất của chỉ số quốc tế và crypto luôn trễ **một phiên**. Chủ dự án chốt 2026-09-05 tối: **mọi dữ liệu có biểu đồ mà không phải giá chứng khoán Việt Nam (đã có realtime ClickHouse) và không phải dữ liệu chu kỳ dài (vĩ mô, BCTC) đều phải cập nhật liên tục trong phiên qua cơ chế interval**. Chậm một phiên với Bitcoin hay S&P 500 là không chấp nhận được.

Việc này chạm ba lớp: luật chuẩn hoá (cho nến đang chạy vào kho), cách gọi nguồn (cửa sổ ngắn cho lượt interval, giãn cách ngẫu nhiên), và phạm vi nguồn (Yahoo bao thêm tỷ giá để có FX trong ngày). Không đụng lược đồ.

## 2. Quyết định chủ dự án đã chốt (2026-09-05 tối) — không mở lại ở brainstorm

| # | Quyết định | Ghi chú |
|---|---|---|
| D1 | **Nến đang chạy vào kho** `asset.ohlc_daily`, ghi đè bằng UPSERT chỉ-khi-đổi tới khi phiên đóng. **Không thêm cột cờ, không migration.** Tầng đọc hiểu "dòng mới nhất của mỗi mã có thể đang chạy" theo lịch sàn | Trợ lý đã đề xuất cột cờ hoặc bảng quote riêng, chủ dự án chọn cách đơn giản |
| D2 | **Giữ đủ 6 nguồn** (WiChart, FRED, ECB, LBMA, Yahoo, Binance); trong ETL thiết kế để chúng **kết hợp** với nhau, không bỏ nguồn nào | ECB giữ làm mốc chuẩn fixing/DXY; LBMA giữ vì lịch sử vàng từ 1968 (WiChart chỉ có cửa sổ 2 năm, PAXG từ 2020) |
| D3 | **Nhịp chạy** (bảng §3): Yahoo 30 phút · Binance 5 phút · WiChart asset 5 phút, vĩ mô 1 lượt/ngày · FRED **tối ưu cho đúng 2 lượt/ngày** · ECB, LBMA 1 lượt/ngày | Nhịp Yahoo chủ dự án chọn 30 phút vì "khá căng", không rõ giới hạn |
| D4 | **Yahoo bao phần FX** để có tỷ giá cập nhật trong ngày; ECB fixing vẫn giữ, hai chuỗi là hai asset khác nhau (luật bước 5: khác mốc chốt = asset khác) | |
| D5 | **Giãn cách ngẫu nhiên 1–5 giây** (phân bố đều) giữa các lời gọi liên tiếp tới cùng một nguồn, mô phỏng request thường, tránh dồn cục | Áp cho mọi nguồn qua fetcher chung, kể cả backfill và retry |
| D6 | Không đăng ký task; lịch vẫn thuộc lát 13. Lát này chỉ làm cho job **chạy được ở nhịp đó** (cờ, cửa sổ, giãn cách) và **đo tải** ở đúng nhịp | [4d] roadmap vẫn giữ mọi task `Disabled` |

## 3. Bảng nhịp chạy mục tiêu

| Nguồn | Nhịp | Cửa sổ lượt interval | Cửa sổ lượt trọn/ngày | Ghi chú |
|---|---|---|---|---|
| Yahoo (chỉ số + FX) | **30 phút** | 5 ngày | 400 ngày, 1 lượt/ngày | ~57 lời gọi/lượt sau khi thêm FX ⇒ ~2.700/ngày nếu 24 giờ; giờ chạy (24 giờ hay chỉ khi có sàn mở) là điểm brainstorm |
| Binance | **5 phút**, 24/7 | `limit=3` | 40 nến | header `x-mbx-used-weight-1m`, phanh ở 3.000/6.000 |
| WiChart asset | **5 phút** trong giờ nguồn cập nhật | tập `INTRADAY_KEYS` (~12 key) | 68 key, 1 lượt/ngày | ⚠️ giả định A3 §4: WiChart có cập nhật trong ngày không — **phải đo trước** |
| WiChart vĩ mô | 1 lượt/ngày | — | trong lượt 68 key | không đổi |
| FRED | **2 lượt/ngày**: ~05:00 và ~20:00 VN | — | trọn chuỗi | 05:00 bắt chuỗi ngày (FRED cập nhật sau 16:15 New York); 20:00 bắt báo cáo tháng (08:30 New York = 19:30 VN). Không interval: 46 lượt còn lại chỉ tải 12 MB để nhận `changed 0` |
| ECB (Frankfurter) | 1 lượt/ngày, ~22:30 VN | — | trọn chuỗi | fixing 14:15 CET, gọi thêm vô ích |
| LBMA | 1 lượt/ngày, ~22:30 VN | — | trọn chuỗi | fixing 15:00/12:00 London |

Thời gian mỗi lượt với giãn cách trung bình 3 giây (D5): Yahoo ~3 phút · Binance ~35 giây · WiChart interval ~40 giây, trọn ~3,5 phút · FRED ~45 giây · backfill Yahoo/Binance ~2 phút. Không lượt nào chồng lên lượt kế của chính nó.

## 4. Dữ kiện đã đo vs giả định phải đo trước khi viết spec (§4.8 bước 0)

### 4.1 Đã đo (2026-09-05, hồ sơ lát 7: [`measure-*.txt`](../2026-09-05-global-etl/))

- Yahoo `v8/finance/chart`: host `query1`, không ETag, `meta.instrumentType` là cờ chết (`quoteType` không còn), cửa sổ 40 ngày trả 1 nến ở `^SET.BK`/`PSEI.PS` (400 ngày trả đủ), `currentTradingPeriod.regular` có; `DX-Y.NYB` có `regular.end` = 03:59 UTC ngày kế (ICE gần 24 giờ). 37 mã chạy 1,1 giây/lời gọi sạch; **chưa đo** ở nhịp 30 phút suốt ngày.
- Yahoo FX (đo 2026-08-15, [yahoo.md §5.5](../../../10-sources/global/yahoo.md)): 22/23 cặp có dữ liệu; nến ngày đã đóng chốt 23:00 UTC; trong cùng phiên các cặp **không đồng bộ** `regularMarketTime` (`EURUSD=X` 21:29 UTC, `JPY=X` 04:21 UTC hôm sau); `VND=X` là tỷ giá thị trường, nằm giữa giá tự do và NHTM bán, **không thay `dhtg`**.
- Binance: `klines limit=40` trả cả nến hôm nay chưa đóng; weight +2 mỗi lời gọi; đồng hồ máy chậm hơn server ~1 giây; 11 mã + backfill 39 lời gọi sạch.
- WiChart: 90 lời gọi liên tiếp không giãn cách sạch (đo 2026-09-05 sáng); 68 key/lượt ≈ 15 giây với 0,2 giây giãn cách.
- FRED: chuỗi ngày cập nhật ~16:15 New York, `T10Y2Y`/`T10YIE` 16:03; báo cáo tháng 08:30 New York; trọn chuỗi 15 lời gọi ~12 MB thô, không ETag; `max_lag` tháng 75, PCE 100 (hiệu chỉnh lát 7).
- Lõi lát 7: `series_job.run(spec, keys, dry_run, backfill, get, sleep, now)`; `SourceSpec.fetch_all(series, get, sleep, backfill)`; `http_fetch.Fetcher(get, classify, sleep, clock, min_interval, retries, backoff, timeout)`; `wichart_fetch` vẫn có `Fetcher` riêng (nợ lát 7).

### 4.2 Giả định — CHƯA kiểm, đo trước khi spec

| # | Giả định | Cách đo |
|---|---|---|
| A1 | Yahoo có mã FX **đúng chiều "quote trên 1 USD"** cho 6 cặp ECB: `EUR=X`, `GBP=X` (USD/EUR, USD/GBP) bên cạnh `EURUSD=X`/`GBPUSD=X` (chiều ngược) — nếu không có thì phải nghịch đảo OHLC (open→1/open, high→1/low, low→1/high) | gọi `chart` cho `EUR=X`, `GBP=X`, `JPY=X`, `CAD=X`, `SEK=X`, `CHF=X`, `CNY=X`, `KRW=X`, `THB=X`, `SGD=X`, `TWD=X`, `INR=X`, `IDR=X`, `MYR=X`, `PHP=X`, `HKD=X`, `VND=X`; đọc `meta.currency`, `regularMarketPrice`, so với ECB fixing cùng ngày (lệch < 1 %) |
| A2 | Yahoo chịu được **~57 lời gọi mỗi 30 phút, giãn cách ngẫu nhiên 1–5 giây, suốt một ngày** | chạy đúng nhịp đó ít nhất 2 giờ (4 lượt); kết luận chỉ ở dạng "mức này an toàn" (§4.3 CLAUDE.md), không dò ngưỡng |
| A3 | **WiChart có cập nhật trong ngày** cho một số key (vàng SJC, vàng thế giới, USD/VND, dầu WTI, bạc, đồng, kim loại Trung Quốc…) — nếu nguồn chỉ nạp một lần trước 08:00 giờ VN (giả định lát 6 chưa kiểm) thì interval 5 phút vô ích | poll 10–15 key ứng viên mỗi 15 phút trong một ngày làm việc, ghi giờ mà điểm cuối đổi giá trị; chọn `INTRADAY_KEYS` từ số đo, không từ suy đoán |
| A4 | WiChart chịu **12 key × 12 lượt/giờ** | đo 1 giờ ở đúng nhịp |
| A5 | Nến đang chạy của Yahoo trong cửa sổ 5 ngày có `regularMarketPrice` = close hiện tại (nến cuối cập nhật theo phiên) | đo trong giờ Tokyo hoặc New York: gọi 2 lần cách 15 phút, close của nến cuối phải đổi |
| A6 | Binance `limit=3` đủ cho interval kể cả khi lượt trước hỏng tới 1 ngày | suy từ luật: nến ngày UTC, 3 nến = hôm nay + 2 ngày bù; xác nhận bằng test |

## 5. Quyết định còn mở — đưa vào brainstorm §4.8

1. **Danh sách cặp FX Yahoo:** (a) chỉ 6 cặp ECB, (b) 6 cặp + nhóm châu Á (CNY, KRW, THB, SGD, TWD, INR, IDR, MYR, PHP, HKD) + `VND=X` đối chứng. Trợ lý đề xuất (b) vì cùng một lượt Yahoo, thêm ~11 lời gọi; chủ dự án chưa chốt.
2. **Hai series FRED trùng vai:** chỉ số đô broad của Fed (`DTWEXBGS`, trễ 3–9 ngày, đã có DXY ICE ở Yahoo) và CNY/USD của Fed (`DEXCHUS`, ECB có CNY tươi hơn). Trợ lý đề xuất bỏ cả hai và thêm CNY vào ECB; chủ dự án chưa chốt. Bỏ = xoá dòng registry FRED (ánh xạ bị xoá đầu lượt theo luật I1, dòng `asset` và dữ liệu giữ nguyên).
3. **Giờ chạy Yahoo:** 24 giờ (đơn giản, ~2.700 lời gọi/ngày) hay chỉ khi có sàn mở (07:00–03:00 VN, ~20 giờ). Cuối tuần: Yahoo không có nến mới, Binance vẫn chạy.
4. **Lượt interval có đẩy `data_domain_state.watermark` không:** với Yahoo/Binance lượt interval là lượt **trọn registry** (không `--keys`) nên theo khuôn hiện tại sẽ đẩy mốc nước mỗi 30 phút — vô hại nhưng cần nói rõ; với WiChart `--intraday` là lượt con (không đẩy) — mốc nước do lượt trọn hằng ngày giữ.
5. **Guard cho lượt interval:** Yahoo trọn registry ⇒ guard tỷ lệ như thường; WiChart `--intraday` ~12 key dưới `MIN_SAMPLE` ⇒ không guard (khuôn `--keys`), đọc `stats` — chấp nhận hay đặt ngưỡng tuyệt đối như FRED?
6. **Ngữ nghĩa cho tầng đọc:** "dòng mới nhất có thể đang chạy" ghi ở `market-data-store.md` và spec; API sau này (lát 10) có cần cột suy `is_running` tính từ lịch sàn không — ghi nhận, không làm ở lát này.

## 6. Phạm vi sửa code (dự kiến cho plan; spec chốt lại)

| File | Hiện tại | Sửa |
|---|---|---|
| `backend/etl/http_fetch.py` | `Fetcher(min_interval=…)` giãn cách cố định | thay bằng giãn cách ngẫu nhiên đều **1–5 giây** trước mỗi lời gọi kế tiếp; `rng` bơm được (`random.Random`) để test cố định; giữ retry/backoff. Test: mọi khoảng nghỉ ∈ [1, 5], với rng thật hai khoảng liên tiếp không luôn bằng nhau; với `sleep` giả đếm số lần gọi |
| `backend/etl/wichart_fetch.py` | `Fetcher` riêng, `MIN_INTERVAL 0.2` | chuyển sang `http_fetch.open_fetcher(classify=…)` (đóng nợ lát 7); giữ `url`, `classify`, `FetchError`/`BadShape` re-export để `wichart_job`/test lát 6 không đổi |
| `backend/etl/yahoo_normalize.py` | bỏ nến cuối khi `now < regular.end` | **bỏ luật cắt**, giữ dedupe theo ngày (nến sau ghi đè nến trước cùng ngày) và mọi cổng khác; test `test_open_candle_is_dropped_while_the_regular_session_is_still_running` đổi thành `…is_kept_and_overwritten…` (8 bars với `now` trong phiên, close nến cuối = literal fixture) |
| `backend/etl/binance_normalize.py` | bỏ nến `closeTime > now` | bỏ luật; test `test_open_time_utc_date_string_prices_and_open_candle_dropped` đổi: 5 nến với `NOW`, nến 09-05 close `4433.56` (literal fixture `binance-PAXGUSDT-5.json`) |
| `backend/etl/yahoo_fetch.py` | cửa sổ 400 ngày cố định | tham số `intraday`: cửa sổ **5 ngày**; giữ 400 cho lượt thường, `-2208988800` cho backfill |
| `backend/etl/binance_fetch.py` | `DAILY_LIMIT 40` | `intraday` ⇒ `limit=3` |
| `backend/etl/series_job.py` | `run(spec, keys, dry_run, backfill, get, sleep, now)`; `fetch_all(series, get, sleep, backfill)` | thêm `intraday=False` truyền xuống `fetch_all(..., intraday)`; `stats["intraday"] = True`; **chữ ký `fetch_all` đổi ⇒ cả 5 nguồn nhận tham số** (FRED/ECB/LBMA bỏ qua) |
| `backend/etl/__main__.py` | `--keys`, `--dry-run`, `--backfill` | thêm `--intraday` cho `yahoo`, `binance`, `wichart` |
| `backend/etl/yahoo_registry.py` | 37 chỉ số | thêm cặp FX theo quyết định §5.1: mã `fx.usd_<ccy>.close`, `asset_class='fx'`, `quote_currency=<ccy>`, unit `<CCY>/1 USD`, `shape='ohlc'`, `price_type=None`, `band` theo số đo A1, `region` theo nước; `VND=X` (nếu chọn) mã `fx.usd_vnd.market` |
| `backend/etl/wichart_registry.py` + `wichart_job.py` | `--keys` | `INTRADAY_KEYS` (từ số đo A3) và `run(intraday=True)` = lượt con trên tập đó |
| `backend/etl/fred_registry.py` | 15 series | theo §5.2: có thể bỏ `DTWEXBGS`, `DEXCHUS`; `fx_registry` thêm `CNY` |
| Tests | `test_e43`–`e49`, `test_e37` (wichart fetch), `test_e41` | cập nhật theo trên; thêm test cho `--intraday` (cửa sổ/limit đúng, stats có cờ), giãn cách ngẫu nhiên, FX registry, `wichart --intraday` |

Không đụng: lược đồ (`0005`–`0017`), `series_store.py`, `registry.py`, `series_guard.py`, ECB/LBMA (trừ thêm `CNY` nếu chốt), FRED fetch/normalize.

## 7. Tiêu chí nghiệm thu (dự kiến, spec chốt)

| | Nội dung | Bằng chứng |
|---|---|---|
| AC1 | Toàn bộ test xanh (trước: **709 passed, 2 skipped**) | số trước/sau |
| AC2 | `etl yahoo --intraday --dry-run` và `etl binance --intraday --dry-run` trên nguồn sống: cửa sổ đúng, số nến/lượt nhỏ (Yahoo ≤ 5 nến/mã, Binance 3) | `stats` |
| AC3 | **Nến đang chạy vào kho và đổi**: trong giờ New York (20:30–03:00 VN) hoặc Tokyo (07:00–13:00 VN), chạy `yahoo --intraday --keys ^GSPC` (hoặc `^N225`) hai lần cách 15 phút ⇒ dòng ngày hôm đó tồn tại và `close` **khác nhau** giữa hai lần, `ingested_at` tiến; Binance: `binance --intraday --keys BTCUSDT` hai lần cách 5 phút ⇒ dòng ngày UTC hôm nay đổi `close` | 4 truy vấn |
| AC4 | Lượt thường (không `--intraday`) sau đó: `changed` chỉ ở nến đang chạy, không đụng nến đã chốt | `stats.changed` + truy vấn |
| AC5 | FX Yahoo: 6 cặp ECB có dòng ngày gần nhất; so với ECB fixing cùng ngày lệch < 1 % (đúng chiều quote trên 1 USD) | bảng đối chiếu |
| AC6 | Giãn cách: log thời gian giữa 15 lời gọi FRED của một lượt thật nằm trong [1, 5] giây, không hai khoảng nào bằng nhau | đo từ log có timestamp |
| AC7 | Tải: Yahoo 4 lượt liên tiếp cách 30 phút (~57 lời gọi/lượt), WiChart `--intraday` 12 lượt cách 5 phút — 0 lỗi HTTP, 0 tín hiệu chặn ⇒ ghi "mức này an toàn" vào yahoo.md/wichart.md kèm ngày đo | log + số đếm |
| AC8 | Mọi lượt chạy dưới credential production; khoá FRED không xuất hiện trong log/stats | grep |

## 8. Tài liệu phải sửa cùng lượt (§1.6, §1.7)

- [spec lát 7](../2026-09-05-global-etl/spec.md): §4.4 cửa sổ, §5.3 cổng (d) Yahoo và luật Binance (bỏ), §5.6 bảng nhịp thay bằng §3 của brief này, Phụ lục D thêm FX — sửa kèm ghi "đổi ở lát 7b, ngày".
- [market-data-store.md](../../../20-design/market-data-store.md): ngữ nghĩa "dòng mới nhất của `ohlc_daily` có thể đang chạy".
- [yahoo.md](../../../10-sources/global/yahoo.md): cặp FX đã đo chiều (A1), mức tải đã kiểm (A2).
- [wichart.md](../../../10-sources/macro/wichart.md): giờ cập nhật trong ngày (A3) — đóng luôn giả định "nạp trước 08:00" của lát 6.
- [fx.md](../../../10-sources/global/fx.md): vai Yahoo FX là chuỗi trong ngày, ECB vẫn là mốc chuẩn.
- [backend/README.md](../../../../backend/README.md): mục 5 job quốc tế thêm `--intraday`, giãn cách ngẫu nhiên, bảng nhịp.
- [roadmap.md](../../../00-overview/roadmap.md): lát 7b ✅ + bảng nhịp cho lát 13 (thay bảng gợi ý ở spec lát 7 §5.6) + "Điểm vào cho lát 8" cập nhật số test.
- `90-records/README.md`: dòng plan này; `ledger.md` cùng thư mục.

## 9. Gợi ý thứ tự task cho plan (mỗi task một vòng test đỏ→xanh)

1. Đo A1–A5 (script trong scratchpad, kết quả `measure-*.txt` ở thư mục này) → viết spec.
2. `http_fetch` giãn cách ngẫu nhiên + `wichart_fetch` chuyển sang fetcher chung (test e37 giữ hành vi).
3. `series_job` + CLI `--intraday`; `yahoo_fetch`/`binance_fetch` nhận `intraday`.
4. Bỏ hai luật nến đang chạy (Yahoo, Binance) + đổi test.
5. Registry Yahoo thêm FX (+ ECB `CNY`, bỏ hai series FRED nếu chốt); `test_e49` cập nhật số đếm.
6. WiChart `INTRADAY_KEYS` + `--intraday`.
7. Chạy thật AC2–AC8, tài liệu, ledger, merge.

## 10. Rủi ro và điều kiện đảo ngược

- **Yahoo chặn ở nhịp 30 phút** (A2 sai): hạ về 60 phút hoặc chỉ chạy khi có sàn mở; nếu vẫn chặn, FX trong ngày mất nguồn — khi đó cân lại ECB v2 (`providers=ECB` không có trong ngày) hay nguồn khác, không phải việc của lát này.
- **WiChart không cập nhật trong ngày** (A3 sai): bỏ mục WiChart `--intraday`, giữ 1 lượt/ngày; brief này đã ghi để lát 13 không xếp lịch thừa.
- **Nến đang chạy làm `changed` nhiễu**: `changes_sample` chỉ áp cho `apply` (điểm), không cho `apply_ohlc`, nên thước đo vá hồi tố của FRED không bị ảnh hưởng; `stats.changed` của Yahoo/Binance sẽ > 0 mỗi lượt interval — đó là hành vi mong đợi, ghi rõ trong spec để lát 12 không coi là bất thường.
- **Đảo ngược D1** nếu tầng đọc (lát 10) chứng minh cần phân biệt nến chốt/đang chạy ở bảng: thêm cột `is_final` bằng migration, một lần, không đụng PK.
