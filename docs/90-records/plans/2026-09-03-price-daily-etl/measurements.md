# Lượt đo nguồn giá theo ngày — 2026-09-03

Đo trước khi viết spec lát 3, theo [CLAUDE.md §4.8 bước 0](../../../../CLAUDE.md): tách dữ kiện đã kiểm khỏi giả định. Lát này treo lên bốn hành vi của `PriceData/GetPriceData` mà tài liệu nguồn ghi từ 2026-08-15, và **hai trong bốn hoá ra đã sai hoặc thiếu**.

**Cách đo:** 18 lời gọi `GET` tuần tự tới `https://wlgw-technical.fiintrade.vn/PriceData/GetPriceData`, header `Origin: https://fiinapp.bvsc.com.vn`, `PageSize=60`, không ghi kho, ~22:00 giờ VN sau phiên 03/09. Cộng 2 nguồn đối chứng độc lập: `market.corporate_event` (lát 2) và tick BVSC trong ClickHouse `rt.trade` (phiên 28/08 và 03/09). Bản thô đầy đủ (~3 MB) không commit — bằng chứng rút gọn ở [`samples/`](samples/).

| File bằng chứng | Nội dung |
|---|---|
| [`shape-20260903.json`](samples/shape-20260903.json) | Vỏ response, **99 trường**, 3 bản ghi đầu trang 1 + 1 bản ghi trang 52 của BID, trang 53 (22 bản ghi) và trang 54 nguyên văn |
| [`exdividend-raw-vs-adjusted-20260903.json`](samples/exdividend-raw-vs-adjusted-20260903.json) | DMX và BFC quanh ngày không hưởng quyền — cặp `closePrice`/`closeValue` từng ngày |
| [`calls-log-20260903.json`](samples/calls-log-20260903.json) | 16 lời gọi: HTTP, latency, byte, **kiểu của `status`**, `totalCount`; response mã sai; kết quả `FromDate`; trang 1 vs trang 2 |

---

## 1. 🔴 `closePrice` là giá THÔ lịch sử, `closeValue` là giá đã điều chỉnh

Tài liệu ([`09-fiin-market-price.md`](../../../10-sources/market/09-fiin-market-price.md) và [bẫy 8](../../../10-sources/market/00-conventions.md)) viết *"giá thô chỉ có ở phiên hiện tại"*, và thiết kế [`step-03 §1`](../2026-08-25-postgres-data-schema/step-03-market-data.md) chốt *"backfill chỉ điền `close_adj`; `close_raw` để NULL, không bịa"*. **Sai.** Endpoint trả **hai cột song song**:

| Trường | Nghĩa | BID 2026-06-08 | BID 2014-06-03 |
|---|---|---|---|
| `closeValue` | đã điều chỉnh hồi tố | 37.934,676 | 5.747,8203 |
| `closePrice` | **thô, đúng giá khớp sàn** | **41.000** | **14.500** |
| `referenceValue` / `referencePrice` | cùng cặp cho giá tham chiếu | 38.859,912 / 41.900 | 5.787,46 / 14.600 |

Ba phép kiểm độc lập:

1. **Hệ số điều chỉnh khớp cổ tức đã ghi ở lát 2.** DMX: `exright_date = 2026-08-18`, `valuePerShare = 4.000`. Ngày 17/08 `closePrice = 88.500`, `closeValue = 84.499,8` ⇒ tỷ số **0,9548** = (88.500 − 4.000)/88.500 = 0,95480 — trùng **4 chữ số**; từ 18/08 tỷ số = 1 đúng ngày ex. BFC: cổ tức 3.500, tham chiếu 53.100 ⇒ (53.100 − 3.500)/53.100 = 0,93409, đo được **0,9341**. Nguồn làm tròn hệ số 4 chữ số thập phân.
2. **Khớp tick BVSC trong ClickHouse — 10/10.** `argMax(price)` của `rt.trade` lúc 14:45 phiên 28/08 và 03/09 cho BID · FPT · HPG · SHS · PVS **bằng đúng `closePrice`** của cùng ngày (36.850 · 36.450 · 73.200 · 72.200 · 22.100 · 21.600 · 15.800 · 15.400 · 39.600 · 39.000).
3. **Dạng số:** `closePrice` luôn là bội của bước giá (số nguyên), `closeValue` mang phần thập phân ở mọi phiên trước ngày điều chỉnh gần nhất.

**Hệ quả thiết kế:** `close_raw` **điền được cho toàn bộ lịch sử** từ chính endpoint này. View `market.price_factor` (= `close_adj / close_raw`) vì thế có giá trị trên cả 12 năm, không chỉ từ ngày vận hành. Chi tiết cách ghi (điền một lần, không đè) ở spec §5.5.

`openValue` · `highestValue` · `lowestValue` **chỉ có bản đã điều chỉnh** (không có cặp `*Price`) — đúng như chú thích M10 của lược đồ.

## 2. 🔴 `status` trả lẫn `0` và `"Success"` trên CÙNG endpoint

| Lời gọi | `status` | Kiểu | Latency |
|---|---|---|---|
| 14/16 lời gọi thành công | `"Success"` | chuỗi | 1,5–3,2 s |
| `bid-p1-fromdate`, `hpg-p1` | **`0`** | **số nguyên** | **0,65 s** |

Hai response mang `0` đều nhanh bất thường — nhiều khả năng trả từ lớp cache hoặc máy chủ đời khác sau cân bằng tải *(§10.4 quy ước chung ghi hai `server` IIS 8.5 / 10.0 xen kẽ)*. Kiểm `status == "Success"` như lát 1 và lát 2 sẽ **coi ~1/8 lời gọi là hỏng và thử lại vô ích**. Phải dùng đúng công thức §6.1: `status ∈ {0, "Success"}`.

## 3. Mã sai trả `Failed / Code not valid`, không phải `items` rỗng

Bẫy 1 của quy ước chung ghi *"gọi sai `organCode` → `200` với `items` rỗng, không có lỗi"* *(đo 2026-08-15)*. Đo lại 2026-09-03 trên chính endpoint này:

```
Code=VHM (ticker, sai)   →  200 · {"status":"Failed","errors":["Code not valid: VHM"],"items":null,"totalCount":0}
Code=NHN (organCode)     →  200 · 60 phiên, totalCount 3485
Code=ASIAGF (ETF)        →  200 · "Code not valid: ASIAGF"
```

Với `PriceData` mã sai là **lỗi có tên**, phân biệt được với lỗi tạm thời (Redis timeout) qua chuỗi `Code not valid` — job không cần thử lại ca này.

## 4. `FromDate` / `ToDate` bị bỏ qua hoàn toàn

`FromDate=2026-08-01&ToDate=2026-08-05` trả **đúng 60 phiên mới nhất** (03/09 lùi về 09/06), `totalCount` không đổi. Không có cách lấy "phần mới" — trang 1 là đơn vị nhỏ nhất. Cùng bài học 1 của lát 2, nhưng ở đây tham số bị **bỏ qua** chứ không phải lọc theo trục khác.

## 5. Phân trang: `totalCount` đáng tin, trang cuối ngắn, không chồng

| Trang | Bản ghi | Ghi chú |
|---|---|---|
| 1 · 2 · 52 | 60 | p1 kết thúc 09/06/2026, p2 bắt đầu 08/06/2026 — **liền nhau, giao = ∅** |
| 53 | **22** | trang cuối ngắn |
| 54 | **0** | `status: "Success"`, `items: []` |

`totalCount = 3.142 = 52 × 60 + 22` — khớp tuyệt đối. Điều kiện dừng đúng cho vòng backfill: **trang trả < 60 bản ghi là trang cuối**; `ceil(totalCount/60)` dùng làm trần phòng hờ. Bẫy 6 *(`totalCount` không đáng tin)* **không áp dụng** cho endpoint này.

## 6. Ngày nghỉ không có dòng, dữ liệu tươi cùng ngày trên cả ba sàn

Trang 1 của BID · FPT · SHS · VGI · TD6 đều có bản ghi mới nhất **`2026-09-03`** (phiên vừa đóng), và **không có dòng nào cho 31/08 – 02/09** (nghỉ lễ). Khác Screener, nguồn này **không đóng dấu ngày không giao dịch** ⇒ job không cần vế guard "có phiên không"; chạy vào ngày lễ chỉ ghi lại đúng 60 phiên đã có (idempotent).

## 7. Nhóm dòng tiền theo nhà đầu tư điền trễ **T+1**

Bản ghi **03/09** lúc 22:00: `localIndividual*` · `localInstitutional*` · `foreignIndividual*` · `foreignInstitutional*` · `netInstitution*` đều **null** trên BID và FPT, trong khi `proprietary*`, `foreignBuyValue`, OHLC, khối lượng đã đủ. Bản ghi **28/08** đã điền đủ. HNX/UPCOM (SHS · VGI · TD6) null ở mọi ngày — đúng giới hạn *"chỉ HOSE"* đã ghi.

**Hệ quả:** job hằng ngày lấy trang 1 = 60 phiên nên **bản ghi hôm qua được ghi lại hôm nay** với dòng tiền đã điền — tự lành trong 1 ngày, không cần lượt "vá T+1" riêng. `totalTrade` cũng chỉ HOSE có (HNX/UPCOM = 0).

## 8. Hiệu năng và tập mã

| Chỉ tiêu | Số đo |
|---|---|
| Latency lời gọi thành công (n = 13) | min 648 · **trung vị 1.757** · p90 2.614 · max 3.161 ms |
| Kích thước trang 60 phiên | trung vị **200 KB** |
| `organCode` dạng mã số thuế (`5702162138` = TD6) | hoạt động bình thường, 304 phiên |
| ETF theo ticker (`E1VFVN30`) | hoạt động, 2.974 phiên, `iNav = 35.196,11`, `iIndex = 2.975,46` |
| `percentValueChange` (BID) | `-0.01085482` — 8 chữ số, **không** làm tròn 2 chữ số như tài liệu ghi cho phái sinh; vẫn không lưu cột |

**Tập mã thật** *(kho `market.security` 2026-09-03)*: cổ phiếu `listed` **1.523** — HOSE 405 · HNX 299 · UPCOM 819. Con số **1.974** trong roadmap/market-data-store là số `StockType=2` của BVSC đo 2026-08-15, **trước** lượt dọn 442 mã huỷ niêm yết (2026-09-03). 100% mã listed có `issuer_id`, 100% issuer có `issuer_external_id('fiintrade')`, **624/1.523 (41%)** mang `organCode ≠ ticker`.

**Ngân sách suy ra:** hằng ngày 1.523 lời gọi × 1,76 s ≈ **45 phút tuần tự** (xấu nhất 3,2 s ⇒ 81 phút). Backfill ≈ 1.523 × trung bình ~35 trang *(BID 53 trang; TD6 6; tuổi niêm yết khác nhau)* ≈ **50.000–80.000 lời gọi** ≈ 25–40 giờ tuần tự — rải qua vài đêm là xong, **không cần nhịp 8 luồng chưa ai đo**.

## 9. Điều CHƯA đo — ghi để không ai tưởng đã kiểm

| Chưa đo | Vì sao chưa | Ảnh hưởng |
|---|---|---|
| Trang 1 trả gì **lúc 15:40** (giờ chạy dự kiến) — bản ghi hôm nay đã có đủ OHLCV chưa | đo lúc 22:00 | Nếu 15:40 chưa có thì lượt hôm sau vá; không mất dữ liệu, chỉ trễ 1 ngày |
| Nhịp tuần tự **kéo dài 45 phút** có gặp tín hiệu chặn không | chỉ đo 18 lời gọi | Lượt chạy thật đầu tiên chính là phép đo — chạy đúng tải kế hoạch rồi dừng (§4.3) |
| `closePrice` có bị nguồn **sửa hồi tố** không (điều chỉnh sai rồi sửa) | cần nhiều ngày | Cột `close_raw` điền một lần không đè; bộ đếm `raw_close_mismatch` (spec §5.5) sẽ lộ nếu có |
| Độ sâu lịch sử của mã UPCOM lâu năm và số trang thật của 1.523 mã | chỉ đo 7 mã | Chỉ ảnh hưởng ước lượng thời gian backfill |
