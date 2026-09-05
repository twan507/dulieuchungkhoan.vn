# SDD ledger — plan: docs/90-records/plans/2026-09-05-global-etl/plan.md

Sổ thực thi lát 7. Artifact subagent (brief, report, gói diff) ở scratchpad ngoài repo; đây là bản ghi còn lại.
Nhánh `feat/global-etl`, gốc `main` = `b799b1d` (sau nợ Ctrl+C). Test trước lát: 650 passed, 2 skipped.

## 0. Rà tiền kiểm plan (2026-09-05, trước Task 2)

| Cặp / task | Bên sản xuất → bên tiêu thụ | Kết quả |
|---|---|---|
| T1 → T2–T6 | `Series(band, max_lag_days, shape, extra)`, `Point`, `Bar`, `SeriesError(reason)` | khớp: mọi normalize dùng đúng tên |
| T1 → T2–T6 | `SourceSpec.fetch_all(series, get, sleep, backfill) -> (docs, texts, failed, calls, retries)` | khớp 5 nguồn; ECB trả cùng doc cho 6 khoá, `texts={"all": …}` |
| T1 → T2–T6 | `SourceSpec.normalize(s, doc, now)`; `shape='ohlc'` ⇒ `apply_ohlc` | khớp: Yahoo/Binance khai `shape="ohlc"`, `price_type=None` |
| T1 → T2 | asset `wti` dùng chung: T1 đổi `name_vi` WiChart thành "Giá dầu WTI", T2 dùng cùng tên | khớp |
| T1 ↔ T2 | cleanup test job để lại `wti` ⇒ `test_s06_asset` vỡ UNIQUE (gặp thật ở T1) | đã sửa cả e43 và brief T2: xoá `wti` khi không còn ánh xạ |
| T2 | `test_backfill_flag_is_rejected_for_fred` mong 2 | `series_job.run` trả 2 trước `open_run` — khớp |
| T5 | `_synthetic` sửa doc từ `_doc()` (json.loads mỗi lần) | không rò rỉ giữa test |
| T6 → T2–T5 | `test_e49` import cả 5 registry + wichart | chạy sau cùng — khớp thứ tự |
| T6 | `binance_fetch.fetch_all` bản plan bọc `get` thật bằng cách gán `f._get` | **Ruling:** implementer bọc `get` một lần trước `open_fetcher` cho cả hai nhánh (giả/thật) — cùng hành vi, không đụng thuộc tính riêng; nếu sai chỉ tốn một vòng sửa |
| Toàn plan | Global Constraints: subagent không commit | dispatch ghi rõ; controller commit theo mốc |

Kết luận: không có xung đột chặn. Bắt đầu Task 2.

## 1. Tiến trình

- Task 1: complete (commits `49f08a3`, tự làm, TDD, 661 passed / 2 skipped; sửa một test sai assertion và một va chạm `wti` với `test_s06_asset`)
- Task 2: implementer (Sonnet) DONE_WITH_CONCERNS — 10/10 e44, `tests/etl` 393 xanh. **Ruling:** brief ghi "11/11" nhưng chỉ định nghĩa 10 test — lỗi đếm của plan, 10 là đúng; nếu sai chỉ thiếu một test phụ, không ảnh hưởng code.
- Task 2: review (Sonnet) ✅ spec, Approved, 0 Critical/Important; Minor: `redact()` là lớp phòng hờ (khoá đã không thể vào message nhờ `http_fetch` chỉ giữ tên lớp exception) — giữ theo brief. complete (commit `9c45462`, 671 passed / 2 skipped)
- Task 3+4: gộp một implementer (Sonnet) DONE — e45 7/7, e46 5/5, `tests/etl` 405. Review (Sonnet) ✅ cả hai, Approved, 0 Critical/Important. Minor (deferred): `fx_normalize` xét độ tươi theo ngày cuối của cả dict `rates` chứ không theo từng tiền tệ — chốt `shape` đã đòi đủ 6 tiền tệ ở ngày cuối nên không lọt; `*_fetch` lặp khuôn `classify/fetch_all` không trích chung (chủ đích §4.4.2). complete (commits `8ffb02e` fx, `2b54798` lbma; 683 passed / 2 skipped)
- Task 5: implementer (Sonnet) DONE_WITH_CONCERNS — e47 11/11, `tests/etl` 416. **Ruling:** brief ghi "12/12", file test chỉ có 11 hàm — cùng lỗi đếm như Task 2, 11 là đúng.
- Task 5: review (Sonnet) ✅ spec (diff byte-identical với brief, 5 fixture đối chiếu tay), Approved, 0 Critical/Important. complete (commit `1f64283`, 694 passed / 2 skipped)
- Task 6: implementer (Sonnet) DONE_WITH_CONCERNS — 9/10 e48+e49 xanh; `test_first_btc_candle_literal_and_shape_stale` đỏ vì chốt `band` áp lên nến cuối của doc mà fixture 3 nến BTC 2017 (~4.140) nằm ngoài dải hôm nay (7.900–800.000). **Ruling:** lỗi của plan/test, không phải code — `band` là chốt cho giá trị HIỆN TẠI; backfill thật luôn có nến hiện tại ở trang cuối nên band đúng; test nới dải riêng bằng `dataclasses.replace` để kiểm phép parse nến đầu. Nếu sai: một backfill thật của mã mà giá hiện tại ngoài dải sẽ bị từ chối — đúng ý thiết kế. Fix round 1: implementer mới (Sonnet) áp ruling — 10/10, `tests/etl` 426. Review (Sonnet) ✅ spec + hai ruling (bọc `_guard_418` một lần cho cả hai đường, không đụng `f._get`), Approved, 0 Critical/Important. Minor (deferred): client thật dựng trong `binance_fetch` lặp logic client mặc định của `open_fetcher` (hệ quả của ruling, không phải sót); `_pause` không chạy khi lời gọi ném lỗi (plan-mandated). complete (commit `fd6b2ba`, 704 passed / 2 skipped)

## 2. Nghiệm thu (Task 7)

**AC2 — `--dry-run` trên nguồn sống 2026-09-05 ~14:15 (credential production, `dry_run` không ghi kho):**

| Job | tally | calls | points/bars | Kết quả |
|---|---|---|---|---|
| fx | 6/6 ok | 1 | 42.516 điểm | ✅ |
| lbma | 2/2 ok | 2 | 29.496 điểm | ✅ |
| binance | 11/11 ok | 11 | 429 nến | ✅ |
| yahoo | 37/37 ok, 0 stale/shape/band | 37 | 10.016 nến | ✅ |
| fred lần 1 | 14/15, **`CPIAUCSL` stale** (07-01, 66 ngày > 60) | 15 | 115.420 | ❌ guard từ chối đúng thiết kế, ngưỡng sai |
| fred lần 2 | 15/15 ok | 15 | 116.374 | ✅ sau hiệu chỉnh |

**Ruling (AC2):** "trễ 45 ngày" của fred.md cho chuỗi tháng là ảnh chụp ngày 15/08; ngay trước kỳ công bố kế tiếp độ trễ chạm ~72 ngày (CPI tháng 8 ra ~10/09), PCE ~87. `max_lag` tháng 60 → **75**, PCE 90 → **100** — sửa `fred_registry` + spec §5.3/Phụ lục A (commit `fix(etl): fred monthly freshness lag`). Nếu sai: một tháng nguồn ngừng công bố sẽ được phát hiện muộn hơn 15 ngày, không mất dữ liệu.

**AC3 — lượt đầu vào kho production 2026-09-05 14:16–14:17 (`ETL_DATABASE_URL`, role `dlck_etl`), commit `fdf6e91`:**

| Job | calls | inserted | registry | Đối chiếu literal spec §7 |
|---|---|---|---|---|
| fred | 15 | 116.374 | 11 macro + 4 asset | `us.yield.10y` 2026-09-03 = **4,77** ✅ · `us.payrolls` 2026-08-01 = **159.075.000** ✅ |
| fx | 1 | 42.516 | 6 asset | `fx.usd_eur` 2026-09-04 fixing = **0,86044** ✅ |
| lbma | 2 | 29.496 | 2 asset | `gold.lbma` = **4.415,4** ✅ · `silver.lbma` = **66,835** ✅ |
| binance | 11 | 429 nến | 11 asset | xem AC6 |
| yahoo | 37 | 10.016 nến | 37 asset | xem AC6 |

`wti` một `asset_id` (28, tên "Giá dầu WTI"), hai chuỗi: `futures` 624 dòng (WiChart, tới 05/09) · `spot` 10.236 dòng (FRED, tới 01/09); ngày 01/09 spot 91,48 / futures 89,56. Ánh xạ theo source: binance 11 · ecb 6 · fred 4 (+11 indicator) · lbma 2 · wichart 52 (+53) · yahoo 37 — WiChart nguyên vẹn. `data_domain_state` 6 dòng mốc `2026-09-05`.

**AC4 — lượt hai cùng ngày (14:18–14:20):** cả 5 job `inserted 0 · changed 0 · changes_sample []` (fred/fx/lbma trước backfill; binance/yahoo sau backfill), `ingested_at` không tiến. FRED chưa có vá hồi tố trong ngày — `changes_sample` sẽ lộ ở kỳ công bố kế.

**AC6 — backfill thật (14:18–14:19):** `yahoo --backfill` 37 lời gọi, 335.601 nến, 325.585 chèn mới (10.016 đã có từ lượt ngày) · `binance --backfill` 39 lời gọi (BTC 4 trang, PAXG 3…), 30.951 nến, 30.522 mới. Đối chiếu: `idx.sp500` **min 1927-12-30, 24.787 nến** (= measure-yahoo), 2026-09-04 close **7.718,60009765625** / volume 4.103.570.000 (= fixture); `btc` từ **2017-08-17** (3.306 nến); `paxg` từ **2020-08-28** tới 09-04 (2.199 nến), close 09-04 = **4.431,81**, **không** có dòng 09-05 (nến chưa đóng bị bỏ); `idx.set` 7.218 nến từ 1996-12-11 (cửa sổ 400 ngày và backfill đều trả đủ). `staging.raw_payload` cho 5 nguồn: **0 dòng** — đúng §4.6 (chỉ khi từ chối). Kho sau lát: `ohlc_daily` 335.601 (index, 37) + 30.951 (crypto, 11).

**AC8 — khoá FRED:** log trọn một lượt `etl fred` (stderr → file) chứa khoá **0 lần**; `ops.etl_run.stats/error` và `staging.raw_payload` của `fred` chứa khoá **0 lần**.

**AC7 — nến chưa đóng trên nguồn sống:** đã kiểm bằng dữ liệu thật ở phía Binance (nến 09-05 đang chạy bị bỏ, xem AC6). Phía Yahoo cần chạy `etl yahoo --keys ^N225` **trong giờ Tokyo ngày giao dịch** (07:00–13:00 VN thứ 2 07/09) — hôm nay thứ 7, **chờ**, không bịa. Hành vi đã pin bằng test `test_open_candle_is_dropped_while_the_regular_session_is_still_running` trên fixture thật.

**AC5** — qua test job của từng nguồn (fred 1/15 hỏng ⇒ từ chối; yahoo 3/37 ALTSYMBOL ⇒ từ chối, 1/37 ⇒ bỏ series), không ép hỏng trên kho production.

## 3. Review toàn nhánh (Opus, hai trục, 2026-09-05 tối) và đợt sửa

**Trục Chuẩn — Important 1:** `yahoo_normalize` truy cập `meta["regularMarketTime"]`/`indicators` không bọc ⇒ `KeyError` thoát khỏi `_normalize_all`, một mã lạ giết cả lượt 37 mã thay vì bị bỏ theo guard tỷ lệ. **Trục Spec — Important:** (1) checklist tài liệu §8 chưa làm lúc review chụp (đã làm sau đó, cùng tối); (2) ledger thiếu AC3–AC8 (đã bổ sung §2 trên); (3) §5.1 "backfill một mã một giao dịch" mà code gộp một giao dịch. **Minor** (8 Chuẩn, 6 Spec): comment vòng import sai ở `wichart_store`; re-export `_hash` riêng tư; `redact` không phủ nhánh `except Exception` chung; SELECT giá cũ chạy cả khi mẫu đã đủ; khoá `old/new` thiếu `price_type`; guard cắt 10 lý do; `period2` không bơm được; cleanup `wti` xoá cả dòng WiChart; Yahoo `404` rơi vào `failed` (20 %) thay vì `shape` (5 %); cổng (d) dùng `now` khác câu chữ spec; chỉ báo `count` FRED không làm; 4 seam §6 thiếu test; CTE vs SELECT; Binance `429` không đọc `Retry-After`.

**Rulings:**
- **Ruling:** cổng (d) Yahoo theo `now < regular.end` là đúng, spec sửa theo code — vì `DX-Y.NYB` có `regular.end` 03:59 UTC ngày kế còn `regularMarketTime` đứng 16:59 ET, so theo spec cũ sẽ bỏ nến thứ 6 mãi. Hệ quả cho lát 13: **xếp `yahoo` sau 11:00 VN** (ghi §5.6), nếu không nến DXY vào kho trễ một ngày (không mất, cửa sổ 400 ngày vá hôm sau).
- **Ruling:** Yahoo `404` ⇒ `bad_shape` (đếm `shape`, trần 5 %) — lời gọi đã đúng tham số nên `404` là mã chết; spec §5.2 sửa.
- **Ruling:** backfill một mã một giao dịch — **làm theo spec** (F2), registry nạp riêng một giao dịch trước; mã hỏng dừng lượt nhưng mã đã commit giữ nguyên. Nếu sai: backfill chậm hơn không đáng kể (48 mã).
- **Ruling:** SELECT giá cũ thay CTE — chấp nhận, không có ghi đồng thời; spec §5.5 sửa theo code. Chỉ báo `count` FRED — bỏ khỏi spec (YAGNI).
- **Ruling:** Binance `429` không đọc `Retry-After` — hoãn: 11–13 lời gọi/ngày, weight 2/lời gọi trên hạn 6.000; backoff 2/4/8 đủ. Ghi nợ.
- **Ruling (F6c):** cleanup `test_e44` không thêm `AND price_type='spot'` nguyên văn vì FRED còn sở hữu dòng `close`/`fixing` của mã khác (xoá thiếu ⇒ FK khi xoá asset) — implementer dùng điều kiện "spot hoặc không phải `wti`", cùng tác dụng bảo vệ dòng WiChart; chấp nhận.

**Đợt sửa (một implementer Sonnet, TDD, 7 finding F1–F7):** F1 bọc cổng Yahoo ⇒ `SeriesError('shape')`; F2 `_apply_backfill_per_code` + test mã thứ hai hỏng thì mã đầu vẫn commit; F3 import ở đầu module, `hash_text` public; F4 bỏ SELECT khi mẫu đủ + khoá có `price_type`; F5 `404` ⇒ `bad_shape`; F6 test band/quote_currency/unit toàn registry, role test thêm `price_daily`, cleanup `wti` thu hẹp; F7 `SourceSpec.redact` áp lên lỗi ghi `etl_run` + log, FRED cấu hình redact, test lỗi mang khoá ⇒ `error` chứa `<REDACTED>`. **709 passed, 2 skipped** (+5 test).

**Re-review có phạm vi (Sonnet):** F1–F7 **ADDRESSED** (có file:line), không vỡ gì mới; kiểm riêng `staticmethod` làm default của dataclass gọi được trên instance. Ngoài phạm vi: `ZoneInfo(tzname)` ném `ZoneInfoNotFoundError` nếu Yahoo trả tên múi giờ lạ nhưng là chuỗi — ghi nợ (chưa gặp trên 37 mã).

## 4. Trạng thái bàn giao

- Nhánh `feat/global-etl` gộp vào `main` bằng `--no-ff`; **709 passed, 2 skipped**; migration head `0017` (không migration mới).
- Kho production: `macro.indicator` 64 (53 WiChart + 11 FRED) · `asset.asset` 108 (52 + 56, `wti` chung) · `asset_external_id` 6 nguồn · `macro.observation` +116.374 · `asset.price_daily` +72.012 (FRED 4 series, ECB 6, LBMA 2) · **`asset.ohlc_daily` 366.552 nến** (37 chỉ số, 11 coin) · `data_domain_state` 6 dòng quốc tế mốc `2026-09-05` · `staging.raw_payload` 0 dòng cho 5 nguồn.
- Nợ để lại: xem roadmap "Lát 7 — Nợ để lại"; thêm từ review: `_pause` Binance không đọc weight khi lời gọi lỗi, `429` không đọc `Retry-After`, `period2` Yahoo không bơm được, guard tất-cả-hoặc-không cắt 10 lý do trong message (đủ ở `stats.tally.details`), `ZoneInfo` tên lạ.
- Việc chờ: AC7 nửa Yahoo (thứ 2 07/09, 07:00–13:00 VN, `etl yahoo --keys ^N225`).

## 5. Rulings (toàn bộ, theo thứ tự)

1. Task 6 brief bọc `f._get` ⇒ bọc `get` một lần trước `open_fetcher` (rà tiền kiểm).
2. Plan đếm sai số test Task 2/5/7 (10 ≠ 11, 11 ≠ 12, 704 ≠ 707) — số test thật là đúng.
3. Test BTC 2017 đỏ vì `band` — lỗi test, nới dải bằng `dataclasses.replace`, code giữ.
4. AC2: `max_lag` chuỗi tháng FRED 60 → 75, PCE 90 → 100 (đo lịch công bố).
5. Cổng (d) Yahoo theo `now < regular.end` (spec sửa theo code); lát 13 xếp `yahoo` sau 11:00 VN.
6. Yahoo `404` ⇒ `bad_shape`.
7. Backfill một mã một giao dịch — làm theo spec.
8. SELECT giá cũ thay CTE; bỏ chỉ báo `count` FRED.
9. Binance `429`/`Retry-After` hoãn.
10. Cleanup `test_e44` dùng điều kiện "spot hoặc không phải `wti`" thay vì `AND price_type='spot'` nguyên văn.
