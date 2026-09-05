# SDD ledger — plan: docs/90-records/plans/2026-09-05-intraday-refresh/plan.md

Sổ thực thi lát 7b. Artifact subagent (brief, report, gói diff) ở scratchpad ngoài repo (`…/scratchpad/sdd/`); đây là bản ghi còn lại.
Nhánh `feat/intraday-refresh`, gốc `main` = `f12dc3a`. Spec duyệt 2026-09-05 tối (chủ dự án: "ok spec này"); nhịp Yahoo chốt **10 phút 24/7** sau khi xem A2.

## 0. Rà tiền kiểm plan (2026-09-05 tối, trước Task 1)

| Cặp / task | Bên sản xuất → bên tiêu thụ | Kết quả |
|---|---|---|
| T1 → T2 | `http_fetch.Fetcher(get, classify, sleep, rng, gap, retries, backoff, timeout)`, không `clock`/`min_interval`; `gaps`, `retries_done` | T2 bọc: `Fetcher(get, sleep, clock=None, rng=None)` giữ chữ ký lát 6, `retries` = `retries_done` — khớp |
| T1 → T3 | 4 `*_fetch` gọi `open_fetcher(classify, get=, sleep=, [headers=], [timeout=])` | T3 chỉ thêm tham số `intraday` vào `fetch_all`, không đụng `open_fetcher` — khớp |
| T3 → T5/T6 | `fetch_all(series, get, sleep, backfill, intraday)` 5 tham số ở cả 5 nguồn; e43 `_fake_fetch_all`, e44 `boom` đổi theo | T5 không đổi chữ ký; T6 (`wichart_job._fetch_all`) không dùng `SourceSpec` — khớp |
| T3 → T6 | `__main__` khối `wichart` chưa có `--intraday` ở T3 (T3 chỉ sửa khối 5 nguồn) | T6 thêm — không giẫm nhau (hai khối khác nhau trong cùng file; T6 chạy sau T3) |
| T4 → T5 | T4 dùng `FX_EUR`/`FX_CAD` tạm (`dataclasses.replace` từ `REG["^GSPC"]`); T5 đổi sang `REG["EUR=X"]` | thứ tự T4 → T5 bắt buộc; ghi vào dispatch T5 |
| T4 (e48) | `test_job_writes_44_closed_bars`: `_fake_get` trả PAXG 5 nến cho mọi mã ⇒ 11 × 5 = 55 | khớp với plan (55) |
| T5 (e47) | `_synthetic` sinh 8 nến/mã từ GSPC-10d; FX 17 mã không có fixture ⇒ 296 + 136 = 432 bars | `_synthetic` set `currency = s.quote_currency` (đã có) — cổng (c) qua; khớp |
| T5 (e45) | fixture `ecb-2026-08.json` thay bản có CNY (Task 0): 22 ngày × 7 = 154; EUR 08-14 = 0.86453, JPY 159.01 giữ nguyên; **CNY 08-14 = 6.7413** | đã kiểm lúc chụp — khớp literal test cũ |
| T5 (e45) | test mới dùng `Resolved` — tên trường phải kiểm (`grep class Resolved`) | ghi vào dispatch T5 |
| T5 → T7 | mã `fx.usd_cny` cùng `asset_id` FRED/ECB; T7 xoá dòng FRED trước lượt ECB | khớp §4.2 |
| T6 | guard intraday: 4 key đơn `dau_wti,bac,dong,kem` bad shape = 4/61 = 6,6 % > 5 % ⇒ từ chối | `wichart_guard.MAX_SHAPE 0.05`, `series_total` ≥ 20 — khớp |
| T6 | `_fake_get` trả 2-tuple — đúng chữ ký `wichart_fetch` sau T2 (bọc `_three`) | khớp |
| Toàn plan | Global Constraints: subagent không commit; không `.superpowers/` trong repo (artifact ở scratchpad) | dispatch ghi rõ; controller commit theo mốc |

**Ruling (rà tiền kiểm):** plan Task 0 Step 2 ghi "A4 khi xong" — A4 đã xong lúc viết ledger (296 lời gọi/19 phút sạch), số đã vào spec §2.2 ở commit `c19f1d0`. Không xung đột chặn. Bắt đầu Task 1.

## 1. Tiến trình

- Task 0: fixture chụp 2026-09-05 ~17:47 VN (4 lời gọi): `yahoo-EURX-5d.json` (6 nến, hai nến London 09-04: `1788476400` close 0.859969973564148 và `1788557390` close 0.8604999780654907, high 0.8626999855041504, low 0.8593999743461609), `yahoo-CADX-5d.json` (nến cuối `1788582071` = 04:21Z thứ 7, close 1.3837000131607056; nến 09-04 close 1.3789499998092651), `binance-BTCUSDT-3.json` (3 nến: 09-03 81270.37 · 09-04 79660.77 · 09-05 đang chạy 79600.00, closeTime 1788652799999 > now 1788605224000), `ecb-2026-08.json` thay (22 ngày, 7 tiền tệ, CNY 08-14 = 6.7413). Bộ test nền: **709 passed, 2 skipped** (46 s). Fixture ECB có CNY không đổi test e45 hiện có vì `fx_normalize` chỉ đọc tiền tệ trong registry.
- Task 1: implementer (Sonnet) DONE — e50 5/5, `tests/etl` 436 xanh. Review (Sonnet) ✅ Spec, Approved; Minor (deferred): test e50 đọc `f._rng.seen` (private) — plan-mandated, giữ. complete (commit `9cd2fc1`)
- Task 2: implementer (Sonnet) DONE — e3x/e4[01] 111 xanh, `tests/etl` 437. Review (Sonnet) ✅ Spec, Approved; Minor (deferred): `noqa: F401` ở wichart_fetch:16 phủ cả tên có dùng (plan-mandated). complete (commit `94d7be2`)
- Task 3: implementer (Sonnet) DONE — e43/e47/e48/e51 mới xanh, `tests/etl` 443, toàn bộ 721 passed / 2 skipped. Review (Sonnet) ✅ Spec, Approved, 0 finding. complete (commit `8f9ba91`)
- Task 4: implementer (Sonnet) DONE_WITH_CONCERNS — e47/e48/e43 40 xanh, toàn bộ 724 passed / 2 skipped; e43 thêm đường UPDATE `apply_ohlc` dưới `dlck_etl` (`changed == 1`). **Ruling:** brief ghi close PAXG 09-05 = 4433.13 (số đo sáng 05/09, spec lát 7 Phụ lục E) nhưng fixture `binance-PAXGUSDT-5.json` là **4433.56** (brief 7b §6 đã ghi đúng) — lỗi chép của plan, fixture là chuẩn; nếu sai chỉ lệch một literal test. Review (Sonnet) ✅ Spec (đối chiếu literal bằng script độc lập), Chuẩn: 2 Minor — docstring dòng 1 của `test_e47_yahoo.py`/`test_e48_binance.py` còn "bỏ nến chưa đóng" (rác do thay đổi tạo ra) ⇒ giao Task 5 sửa cùng lượt. complete (commit `a3f78e1`)
- Task 5: implementer (Sonnet) DONE — e44/e45/e47/e49 37 xanh, toàn bộ 725 passed / 2 skipped; hai chỗ ngoài dải dòng brief (`tally.failed` 6→7, mệnh đề `NOT EXISTS` ở `_cleanup` e45) là hệ quả cơ học/đã nêu trong văn xuôi brief — chấp nhận; e44 bound `inserted` hạ 12→11 series synthetic (DEXCHUS bỏ), reviewer tính độc lập khớp. Review (Sonnet) ✅ Spec (17 dòng `_FX_ROWS` so từng ký tự với Phụ lục F, CNY 08-14 = 6.7413 khớp fixture), Chuẩn: 2 Important (docstring e44 "15 series", e45 "6 cặp") + 1 Minor (3 dòng trắng). **Ruling:** docstring `fred_job`/`fx_job`/`yahoo_job` lệch số cùng loại rác — sửa trong cùng vòng vì không task nào khác chạm ba file; nếu sai chỉ là ba dòng chú thích. Fix round 1/5 (implementer mới, Sonnet; SendMessage không có trong phiên): 4/4 ADDRESSED, re-review có phạm vi (Sonnet) không breakage. complete (commit `f3f08d3`)
- Task 6: implementer (Sonnet) DONE — e41+e51 13 xanh, `tests/etl` 451, toàn bộ 729 passed / 2 skipped. Review (Sonnet) ✅ Spec, Approved; Minor (deferred): `INTRADAY_KEYS` trong e41 tính bằng cùng predicate `freq == "d"` (plan-mandated; neo bằng literal 47/61/`cpi`/`dhtg`). complete (commit `a302628`)

## 2. Nghiệm thu (Task 7)

Mọi lượt dưới `ETL_DATABASE_URL` (role `dlck_etl`), kho production, 2026-09-05 18:40–19:05 VN (thứ 7). Log ở scratchpad.

| AC | Bằng chứng | Kết quả |
|---|---|---|
| AC1 | `uv run pytest -q`: **729 passed, 2 skipped** (trước lát 709) | ✅ |
| AC2 | `yahoo --intraday --dry-run`: tally 54/54 ok, 54 lời gọi, **272 nến** (≈5/mã), `intraday: true` · `binance --intraday --dry-run`: 11/11, **33 nến** (3/mã) · `wichart --intraday --dry-run`: 47 key, 61 series ok, 31.725 điểm | ✅ |
| AC3 Binance | `binance --intraday` 18:47:43 ⇒ `inserted 11`; lượt 2 18:54:10 ⇒ `inserted 0 · changed 11`; `btc` 09-05 close **79.608 → 79.666,06**, `ingested_at` 11:48:20 → 11:54:46 UTC; nến 09-04 `ingested_at` 07:16:55 UTC không tiến | ✅ |
| AC3 WiChart (nửa) | `wichart --intraday` 18:50 (sau lượt trọn 08:11 cùng ngày): `inserted 17 · changed 29 · payloads_stored 0` — điểm 09-05 của `gold.sjc_buy/sell` (144,6/147,6 triệu), `coffee_robusta_vn`, `natgas_hh`, `phosphorus_cn`, `galv_sheet_color_hoasen` đổi; 22 điểm tháng 8 `cotton_us` vá hồi tố; `data_domain_state` wichart giữ mốc lượt trọn | ✅ bằng chứng thứ 7; xác nhận giờ làm việc 07/09 (nợ) |
| AC3 Yahoo chỉ số | không có sàn mở thứ 7 — **nợ 07/09** (`yahoo --intraday --keys ^N225`, 07:00–13:00 VN, hai lần cách 15 phút) | ⏳ |
| AC4 | lượt thường ngay sau: `yahoo` **`changed 0`** (`inserted 4.743` = lịch sử 400 ngày của 17 FX mới) · `binance` `inserted 0 · changed 11`, dòng ingested chỉ ngày 09-05 (11) · `wichart` `0/0`, `payloads_stored 23` (lượt intraday không lưu body nên hash lệch — đúng ruling) | ✅ (thứ 7); đủ ba nguồn có phiên: nợ 07/09 |
| AC5 | 17 mã `fx.usd_*.market` có dòng mới nhất (09-04 hoặc 09-05); so ECB fixing 04/09: EUR 0,8605/0,86044 **+0,007 %** · GBP 0,73981/0,7391 +0,10 % · JPY 156,221/156,25 −0,02 % · CHF 0,8090/0,80924 −0,03 % · SEK 9,5655/9,5513 +0,15 % · CAD (nến 09-04) 1,37895/1,38 −0,08 % · CNY 6,7108/6,7109 −0,001 % — đều < 1 %, đúng chiều. Cut-over CNY: **DELETE 11.397 dòng FRED** (role ETL, được phép) → `etl fx` `registry asset 7 · inserted 6.819` → `fx.usd_cny` min 2000-01-13, max 2026-09-04, 6.819 dòng, ánh xạ chỉ `(ecb, CNY)` → `etl fred` `registry 11+3 · removed 1`, `DEXCHUS` 0 | ✅ |
| AC6 | bọc `httpx.Client.get` ghi `monotonic`: `yahoo --intraday --keys` 6 mã ⇒ 5 khoảng **4,06 · 2,06 · 4,55 · 2,35 · 3,23 s**; `lbma` 2 lời gọi ⇒ 4,82 s; tất cả ∈ [1, 5,5] (gồm ~0,1 s phản hồi), không trùng tới 0,01 s | ✅ |
| AC7 | A2 216 lời gọi/16 phút, A4 296/19 phút — 0 lỗi (spec §2.2); ghi vào yahoo.md §7 / wichart.md §2.5 ở Task 8 | ✅ |
| AC8 | log stderr lượt `fred` (361 byte): khoá **0** lần; `ops.etl_run.stats||error` của `global.fred` (1.995 ký tự): 0; `raw_payload` fred: 0 | ✅ |

**Ruling (Task 7):** lịch sử FX Yahoo chỉ có 400 ngày (cửa sổ lượt thường); `etl yahoo --backfill` sẽ kéo từ 2003 cho 17 cặp (~3 phút) — không thuộc AC, để chủ dự án chạy khi cần; nếu sai chỉ thiếu lịch sử FX trước 08/2025.

## 3. Task 8 và review toàn nhánh

- Task 8: implementer (Sonnet) DONE — 12 file tài liệu; `git grep` sweep phân loại đủ (hit còn lại: đã chú lát 7b · code hợp lệ `price/snapshot/fundamentals_fetch` · lịch sử `90-records/` · trùng chữ "30 phút" ở corpus). Review (Sonnet) ✅ 12/12 mục, Approved; Minor (deferred): `crypto.md:188` câu cũ "bỏ nến closeTime > now" đứng trước câu mới dễ đọc nhầm; chú ở `10-sources/README.md` gắn cùng chuỗi cho cả FRED/Frankfurter/LBMA (plan-mandated). complete (commit `d9b9ec9`)

**Review toàn nhánh (Opus, hai trục, 2026-09-05 ~19:40):** tự chạy lại 729 passed / 2 skipped; đối chiếu 17/17 dòng Phụ lục F bằng script; 5 truy vấn kho production.
- **Trục Chuẩn — Critical C1:** nến FX ngày của Yahoo (`<CCY>=X`) có `close ≈ open` ở MỌI ngày đã chốt, không riêng nến 23:00 UTC "rỗng" của ngày hiện tại — tức Yahoo ghi `close` = giá đầu ngày (quirk đã biết của Yahoo với tiền tệ). Controller đo lại độc lập trên kho (263 ngày): `avg|close−open|/close` EUR 0,0095 % · JPY 0,0135 % · CNY 0,0015 % (chỉ số: S&P 0,48 %, Nikkei 0,98 %); `avg|close−open|/(high−low)` FX 1,8–3,0 % vs chỉ số 47–49 %. Hệ quả: nến live (giá hiện tại) chỉ tồn tại trong ngày London đang chạy; sang ngày kế Yahoo trả lại nến 23:00 UTC và dòng hôm qua bị ghi đè về giá đầu ngày (dự đoán kiểm chứng được sáng thứ 2: `fx.usd_eur.market` 09-04 sẽ đổi 0,8605 → 0,85997). Cổng, test, AC5 (< 1 %) đều không bắt được — đúng họ lỗi §1.3. **Quyết định thuộc chủ dự án — dừng hỏi** (xem cuối ledger).
- Important I1–I4 + Minor M1/M2: sửa một đợt (Sonnet), re-review có phạm vi 6/6 ADDRESSED, commit `2337e22`.
- Minor để lại (ruling): e50 đọc `_rng.seen` · `noqa F401` rộng · `clock` chết ở `wichart_fetch` (giữ chữ ký lát 6) · `--keys`+`--intraday` ở `wichart_job` ném sau `open_run` (CLI đã chặn trước; khác khuôn `series_job`) · e37 assert dải [1, 5] thay vì tiêm `rng` · `INTRADAY_KEYS` cùng predicate · roadmap ghi "`main` = lát 7b" trước merge (sửa khi merge).
- **Trục Spec ❌** chỉ vì C1 (lỗ của spec §2.1: chỉ đo trạng thái trong ngày) và I4 (đã sửa). Mọi mục khác khớp, không scope-creep.

**Ruling (C1, chủ dự án 2026-09-05 tối): phương án 1 — chấp nhận, ghi bẫy ở yahoo.md/fx.md/market-data-store.md/spec §2.1·§5.4·§9; không đổi code. Nếu sai: tầng đọc dùng nhầm close lịch sử của .market cho biểu đồ FX — chi phí là một luật đọc, không mất dữ liệu.**
