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
