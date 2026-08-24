# Lộ trình hợp nhất

**Ngày:** 2026-08-14 · **Cập nhật 2026-08-15** theo đợt khảo sát nguồn *(9 nguồn, ~400 lời gọi thật)* · Gộp danh sách "việc tiếp theo" của ba khối tài liệu, xếp lại theo **phụ thuộc thật** thay vì theo thứ tự từng khối được viết ra.

Ba khối vốn có ba danh sách việc riêng, mỗi danh sách tự cho mình là gốc. Xếp chung mới lộ ra: **một số việc chặn nhiều thứ hơn vẻ ngoài của nó, và một số việc tưởng chặn thì thực ra đã có đáp án.**

---

## 0. Trạng thái hiện tại

| Khối | Trạng thái | Bằng chứng |
|---|---|---|
| Tài liệu nguồn thị trường | ✅ Hoàn chỉnh, kiểm chứng bằng lời gọi thật · **phái sinh và ETF/quỹ bổ sung 2026-08-15** | 131 endpoint, mẫu 51 mã · 14 hợp đồng phái sinh · 31 mã ETF |
| Tài liệu nguồn vĩ mô WiChart | ✅ Hoàn chỉnh + bộ tự kiểm chạy được | 87 key, 509 khẳng định |
| **Tài liệu OMO (SBV)** | ✅ **Mới 2026-08-15** — tải và parse thật 1 phiên | [`macro/sbv-omo.md`](../10-sources/macro/sbv-omo.md) |
| **Tài liệu 5 nguồn quốc tế** | ✅ **Mới 2026-08-15** — FRED · Frankfurter · Yahoo · LBMA · Binance | [`10-sources/global/`](../10-sources/global/) |
| Tài liệu nguồn tin | ✅ Đo thật trên 307 URL, 1.408 tiêu đề | ~570 tin/ngày chưa dedupe |
| Thiết kế kho dữ liệu thị trường | ✅ Đã duyệt | chưa viết dòng code nào |
| Thiết kế pipeline tin | ✅ Đã duyệt | chưa viết dòng code nào |
| Hai skill chứng khoán | ✅ Xong, test 6 vòng, **dự án đã đóng 2026-08-14** | 3.046 dòng · [bảo trì skill](../30-skills/maintenance.md) |
| Tầng ngữ nghĩa nối dữ liệu ↔ skill | 🟡 Mới đề xuất, chưa duyệt | [chatbot-semantic-layer.md](../20-design/chatbot-semantic-layer.md) |
| **Từ điển mã trường FiinGroup** | ✅ 729 mã · tên VI/EN 98,5% · đơn vị 99,7% | [field-dictionary.json](../10-sources/market/field-dictionary.json) |
| **Chọn nguồn chuẩn cho từng chỉ tiêu** | ✅ Đã chốt | [chọn trường cho ETL thị trường](../20-design/market-field-selection.md) |
| **Giấy phép WiFeed với WiGroup** | ✅ **Đã chốt 2026-08-15** — mở khoá 87 endpoint vĩ mô/hàng hoá | chủ dự án xác nhận |
| **Rate limit FiinGroup** | ✅ **Đã kiểm bằng đúng tải ETL kế hoạch 2026-08-15** — 64 lời gọi tuần tự, không tín hiệu chặn | [quy ước chung §10](../10-sources/market/00-conventions.md) |
| **Độ rộng nguồn** | ✅ **Khép 2026-08-15** — 9 nguồn, ~400 lời gọi thật. Danh sách *"Ngoài phạm vi"* đã phân rã hết, **không còn mục nào chưa có câu trả lời** | [`10-sources/README.md` §2](../10-sources/README.md) |
| **Repo vào git** | ✅ `git init` + commit đầu 2026-08-14 | toàn bộ docs + hai skill |
| **Stack sản phẩm + cây monorepo** | ✅ **Chốt 2026-08-24** — Next.js · Python/FastAPI · Postgres + ClickHouse (lưu tick thô) · skill dời về `backend/agent/skills/` | [ADR 0007](decisions/0007-monorepo-layout-and-stack.md) |
| **Toàn bộ phần cài đặt** | ❌ Chưa bắt đầu | |
| **Realtime phái sinh** | 🔴 **Chưa đo được** — đo ngày thứ Bảy, thị trường đóng. Phải đo **trong phiên** | [§5](#5-việc-còn-thật-sự-để-ngỏ) |

## 1. Việc chặn nhiều thứ nhất — làm trước

| # | Việc | Chặn cái gì | Nguồn |
|---|---|---|---|
| **1** | **Dựng hạ tầng Postgres + ClickHouse (+ Redis)** | Mọi ETL | kho dữ liệu §8 GĐ 0 · [ADR 0007](decisions/0007-monorepo-layout-and-stack.md) |
| ~~1b~~ | ~~Xác nhận rate limit với FiinGroup~~ | ✅ **Đã kiểm bằng tải kế hoạch 2026-08-15** — burst Screener 52 trang chạy tuần tự (~29 request/phút, 1,8 phút) không gặp tín hiệu chặn nào, và không có header hạn mức nào. Xác nhận chính thức từ FiinGroup **không còn là điều kiện chặn**. Chủ đích không dò ngưỡng trần; nhịp 8 luồng thì chưa kiểm — xem [§10 quy ước chung](../10-sources/market/00-conventions.md). *(Danh sách 11 mã chỉ tiêu chưa giải mã vẫn gửi kèm khi có dịp trao đổi — xem [Phụ lục A §A.5](../10-sources/market/appendix-A-field-codes.md), không chặn việc gì)* | |
| ~~2~~ | ~~Chốt giấy phép WiFeed với WiGroup~~ | ✅ **Đã chốt 2026-08-15** — chủ dự án xác nhận. Mở khoá toàn bộ nhánh vĩ mô/hàng hoá, 87 endpoint | |
| ~~3~~ | ~~Yêu cầu FiinGroup bảng ánh xạ mã chỉ tiêu BCTC~~ | ✅ **Đã tự giải quyết 2026-08-14** — 729 mã, độ phủ 100% trên response thật, lấy từ bundle JS ứng dụng FiinTrade. Kèm tên Việt/Anh (98,5%) và **đơn vị dữ liệu** (99,7%). Xem [Phụ lục A §A.5](../10-sources/market/appendix-A-field-codes.md). Còn 11 mã chưa giải mã — không chặn việc gì | |

Ba việc 1b–3 đều **phụ thuộc bên ngoài**, không tự làm được, và thời gian chờ không kiểm soát được. **Cả ba nay đã xong.** Việc chặn duy nhất còn lại là dựng hạ tầng — việc tự làm được, không phải chờ ai.

## 2. Việc gấp vì mất dữ liệu theo thời gian

> Xếp riêng vì chúng không chặn thứ gì, nhưng **mỗi ngày trì hoãn là một ngày mất vĩnh viễn.**

| # | Việc | Vì sao không hoãn được |
|---|---|---|
| **4** | **Ingester realtime + tích luỹ `bar_1m`** — *chờ hạ tầng DB, xem ghi chú dưới bảng* | Nến intraday **không tồn tại ở bất kỳ nguồn nào**. Mọi dữ liệu khác crawl lại lúc nào cũng được, riêng cái này không |
| **5** | **Backfill lịch sử tin** từ sitemap TinnhanhCK / BNews / NguoiQuanSat | Dữ liệu chỉ còn chừng nào họ còn giữ sitemap |

**Ingester chờ hạ tầng DB — quyết định chủ dự án 2026-08-15.** Nó không còn chạy song song ngay từ đầu nữa mà xếp sau [1]. Lý do gấp thì **không mất đi**: mỗi ngày chưa có Ingester vẫn là một ngày nến 1 phút mất vĩnh viễn, không nguồn nào backfill lại được. Đó chính là **lý do dựng hạ tầng DB là việc kế tiếp** — làm xong hạ tầng là đồng hồ mất dữ liệu dừng lại.

## 3. Việc theo thứ tự phụ thuộc

```
[1] hạ tầng
     │
     ├─→ [6] Bảng tham chiếu + ETL danh bạ/ngành/instrument  ◄── nút thắt
     │        │
     │        ├─→ [7]  ETL hằng ngày: giá, snapshot, screener, lịch sự kiện
     │        │         └─→ [8] Bộ giám sát hợp đồng (dựng cùng, dùng chung script)
     │        │              └─→ [9] Backfill lịch sử giá, rải 1–2 tuần
     │        │
     │        └─→ [10] Khung thu thập tin + chuẩn hoá, chạy KHÔNG có AI 1 tuần
     │                  └─→ [11] Đo tỷ lệ dedupe thật
     │                       └─→ [12] Chốt ngân sách token → bật lưới phân loại
     │
     └─→ [4] Ingester realtime (ưu tiên cao, ngay sau khi hạ tầng DB xong)

[7] + [12] ─→ [13] Tầng ngữ nghĩa + function calling
                    └─→ [14] Test lại vòng 6 CÓ function calling
```

**[6] là nút thắt thật của cả hệ.** Nó xuất hiện trong kho dữ liệu như "giai đoạn 1", nhưng pipeline tin cũng phụ thuộc nó mà không biết — xem [mắt xích 3.1](architecture.md). Làm xong [6] là mở khoá cả hai nhánh cùng lúc.

## 4. Việc đã có đáp án, chỉ cần áp dụng

Bốn mục đang nằm trong danh sách **"Còn để ngỏ"** của pipeline tin nhưng thực ra đã được trả lời ở khối tài liệu khác:

| Đang ghi là để ngỏ | Đáp án đã có |
|---|---|
| Danh sách ~1.600 mã niêm yết | `getListOrganization` cho danh bạ doanh nghiệp (**gồm cả mã đã huỷ niêm yết**); con số **1.974 cổ phiếu** là đếm `StockType=2` từ **`getAllQuotes` của BVSC**, đo 2026-08-15 — không phải số của `getListOrganization`. Số ~1.600 là ước lượng sai. Lọc mã huỷ niêm yết bằng `getAllQuotes` |
| Bảng tên thương mại → mã | `organName` + `organShortName` trong cùng endpoint |
| Khung ngành để lọc tin | `getAllIcbIndustry` — cây ICB 4 cấp |
| Khung ngành cho skill | Cùng nguồn trên, nối theo hợp đồng ở [§3.2](architecture.md) |
| Bảng ánh xạ mã chỉ tiêu BCTC | **729 mã đã giải mã** từ bundle JS FiinTrade — xem [Phụ lục A §A.5](../10-sources/market/appendix-A-field-codes.md) |
| Đơn vị của các mã chỉ tiêu | **727/729 mã có `don_vi_du_lieu`**, 392 xác thực bằng đẳng thức kế toán |
| Lấy trường nào từ nguồn nào | [chọn trường cho ETL thị trường](../20-design/market-field-selection.md) — Screener 80/193, Snapshot 16/54, giá từ BVSC |

## 5. Việc còn thật sự để ngỏ

| Việc | Ghi chú | Chốt bằng cách nào |
|---|---|---|
| ~~**Luật bỏ boilerplate cho từng nguồn**~~ | ✅ **Đã khảo sát 2026-08-15** — luật riêng cho cả 8 nguồn báo nằm ở [cấu trúc trang bài](../10-sources/news/article-structure.md) (33 bài, chạy thật trên trang đã tải). Còn ngỏ: dạng bài longform/video/bài cũ chưa phủ | Đã làm — đúng bằng một vòng soi tương tự vòng soi feed |
| **Chọn mô hình embedding** | Chốt **trước** khi nạp dữ liệu — embed lại toàn kho về sau rất tốn | Nhớ embed cả `summary` và `summary_ai`, giữ riêng |
| **Ngưỡng `confidence`** phân loại | Dưới bao nhiêu thì vào hàng chờ rà tay | Sau vài tuần chạy thật |
| **Trần 3.000 hay 4.000 ký tự** | | Đối chiếu `content_chars` với các ca phân loại sai |
| **Tách từ tiếng Việt** | Chỉ làm nếu có bằng chứng `simple` + `unaccent` không đủ | |
| ~~**Câu treo cuối của dự án skill**~~ | ✅ **Đã quyết 2026-08-14: giữ nguyên tên "ngân hàng"** trong luận điểm *ngành báo hiệu* — là cơ chế, không phải danh sách ngành cứng. Bảng rà `CAN-SUA.md` hết việc và đã xoá | |
| **Đoạn giới hạn phạm vi vào system prompt** | Skill không tự gác cổng được — xem [§4](architecture.md) | Làm khi dựng backend |

### 5.1 🔴 Realtime phái sinh — chưa đo được, phải đo TRONG PHIÊN

**Việc gấp nhất còn lại của khối nguồn.** Đợt khảo sát chạy ngày **thứ Bảy 2026-08-15**, thị trường đóng (`tradingSessionID: "CLOSED"`), nên **không phép kiểm nào ngoài giờ có giá trị**: server BVSC trả ack `statusCode: 200` cho **mọi** chuỗi topic rồi im lặng — đăng ký thành công không chứng minh topic hợp lệ *(đã ghi ở [`11-bvsc-realtime.md` §1.4](../10-sources/market/11-bvsc-realtime.md))*.

**Đã biết chắc, rút từ mã nguồn bảng giá BVSC** *(đọc 2026-08-15)*:

| Mục | Giá trị |
|---|---|
| Máy chủ | `https://wss.bvsc.com.vn`, đường dẫn `/market/socket.io`, thư viện **sails.io**, `transports: ["websocket"]` |
| Bảng hằng số topic | 20 topic dùng chung toàn bảng giá — `i` · `i_ol` · `o10` · `o_ol10` · `o` · `o_ol` · `t` · `t_ol` · `tm` · `e` · `e_ol` · `im` · `e_im` · `om` · `idx` · `pth` · `ptm` · `p` · `u` · `d` |
| Hạ tầng | Bảng phái sinh render từ `psStocks` và **ăn cùng module socket** với bảng cổ phiếu ⇒ **dùng chung hạ tầng realtime, không phải kênh riêng** |

**Chưa biết:** topic nào mang tick phái sinh · định dạng frame · tần suất · có `openInterest` realtime không.

**Quy trình đo — khung 08:45–15:00** *(⚠️ phái sinh mở sớm hơn cổ phiếu 15 phút; sớm nhất là phiên kế tiếp sau 2026-08-15)*:

1. Nối `wss.bvsc.com.vn/market/socket.io`.
2. Đăng ký **toàn bộ 20 topic** với 2–3 mã phái sinh — `41I1G8000` là **mã duy nhất có thanh khoản thật** *(đo 2026-08-15)*.
3. Ghi frame trong ~5 phút, xem **topic nào thật sự đẩy dữ liệu** — đây là phép kiểm duy nhất có giá trị.
4. Đối chiếu giá trong frame với `/datafeed/instruments` gọi cùng lúc.

**Ảnh hưởng thiết kế:** cho tới khi đo xong, lược đồ và Ingester **không được giả định** là có tick phái sinh realtime.

### 5.2 Việc treo khác phát sinh từ khảo sát 2026-08-15

| Việc | Vì sao ảnh hưởng thiết kế | Chốt bằng cách nào |
|---|---|---|
| 🔴 **Cập nhật `market-data-store.md` theo ClickHouse** | Chốt 2026-08-24 ([ADR 0007](decisions/0007-monorepo-layout-and-stack.md)): kho realtime đổi TimescaleDB → ClickHouse để lưu tick thô + sổ lệnh. Thiết kế đã duyệt chưa phản ánh: DDL ClickHouse, materialized view sinh nến, buffer ghi batch cho Ingester; Redis giữ nguyên vai trò pub/sub + leader lock | Một phiên thiết kế riêng, làm **trước khi dựng hạ tầng [1]** |
| 🔴 **Lược đồ giá dầu phải có cột phân biệt loại giá** | Quyết định chủ dự án 2026-08-15: **lưu cả hai** — giao ngay *(FRED `DCOILWTICO`, trễ 4 ngày)* và tương lai *(WiChart `dau_wti`, T−1)*. Chênh cơ sở đo được **~+2,0% ổn định**. Trộn chung một cột "giá dầu" thì lịch sử có **bậc nhảy 2% tại điểm đổi nguồn** | Thêm cột loại giá vào lược đồ trước khi nạp dòng đầu tiên |
| 🔴 **Crawl OMO phải chạy từ ngày đầu** | SBV **chỉ hiển thị phiên mới nhất, không có kho lưu** — mỗi ngày không crawl là mất vĩnh viễn. Và cột **đáo hạn/bơm ròng phải tự dựng** từ kỳ hạn, cần **~140 ngày tích luỹ** mới có con số ròng đầy đủ | Xếp cùng nhóm gấp với [4] ở §2 — [`macro/sbv-omo.md`](../10-sources/macro/sbv-omo.md) |
| **Kho FRED phải UPSERT, không append-only** | FRED **vá hồi tố**: `PAYEMS` tháng 5/2026 có **3 giá trị** khác nhau. Append-only sẽ giữ số đã bị thay thế | Làm mới cửa sổ 24 tháng mỗi lần chạy — [`global/fred.md` §4](../10-sources/global/fred.md) |
| ~~**Khoá EIA miễn phí**~~ — ⚪ **đã cân nhắc và BỎ QUA** *(chủ dự án quyết 2026-08-15)* | EIA chỉ chuyên năng lượng: trong 15 series FRED đang dùng, **đúng 1 series là của EIA** (`DCOILWTICO`); 14 series còn lại của FRB · BLS · BEA · Fed NY · CBOE. Nên EIA **không thay được FRED**, chỉ bớt một mắt xích cho dầu khí. Đăng ký lại khi nào thật sự cần tồn kho/sản lượng dầu khí Mỹ — mất 5 phút | — |
| **`.gitignore` chưa bao giờ được commit** *(việc chủ dự án)* | Đang che `.env` ở máy hiện tại, nhưng **bảo vệ đó không đi theo repo** | Commit file |
| **Rà lại các cờ `lệch x%` khác trong `wichart.md`** | Cờ `dau_wti` sai vì chấm một điểm và so nhầm chuẩn. Cờ `vang_the_gioi` đã kiểm trên 712 ngày và **đúng** ⇒ **không được suy đoán đồng loạt cả bộ cờ sai** | So chuỗi, không chấm điểm; nhớ parse `Asia/Ho_Chi_Minh` |
| **Đồng, thép, than, bạc** | Chưa tìm được nguồn ngày miễn phí có mốc chuẩn để đối chiếu | Chưa chặn việc gì |
| **TPCP phái sinh "chưa từng giao dịch"** | Kết luận mới dựa trên **1 phiên** | Đo thêm vài phiên trước khi đưa vào lược đồ |

## 6. Sáu bẫy sẽ cắn ngay ngày đầu cài đặt

Ghi lại ở đây vì chúng nằm rải trong ba file khác nhau và đều đã gặp thật:

1. **`organCode ≠ ticker` ở 41% doanh nghiệp** — gọi bằng ticker trả `HTTP 200` với dữ liệu rỗng, không báo lỗi gì.
2. **Timestamp WiChart phải parse bằng `Asia/Ho_Chi_Minh`**, không phải UTC — parse sai tạo ảo giác lệch nhãn 1 tháng trên toàn bộ chuỗi tháng.
3. **Nhãn `unit` của WiChart sai ở 15 series**, lệch 1000 lần, **rải rác ngẫu nhiên không theo quy luật** — phải dùng bảng hệ số đã hardcode.
4. **Nhãn `unit` của FiinTrade cũng không phải đơn vị dữ liệu** — `Percentage` thực ra là thập phân (`0.1821` = 18,21%), `BillionVND` thực ra là VND đầy đủ. Dùng `don_vi_du_lieu` trong [từ điển mã trường](../10-sources/market/field-dictionary.json), không dùng nhãn của API.
5. **`getScreenerItems` timeout khi gửi nhiều tiêu chí** — 79 tiêu chí thì server FiinTrade trả lỗi Redis timeout, 1 tiêu chí thì chạy ngay. Vẫn đủ 223 trường bất kể số tiêu chí.
6. **`isa20ttm` không bằng tổng 4 quý `isa20`** — lệch tới 9,4%. Screener dùng lợi nhuận cổ đông công ty mẹ, BCTC dùng lợi nhuận thuần. Đừng tự tính lại.

> Bẫy 3 và 4 là **cùng một loại lỗi trên hai nhà cung cấp khác nhau** — nhãn đơn vị do nguồn tự khai không khớp dữ liệu nguồn tự trả. Nếu thêm nguồn thứ tư, kiểm đơn vị bằng dải giá trị thật trước khi tin nhãn.

Danh sách đầy đủ: [13 bẫy triển khai](../10-sources/market/00-conventions.md) · [6 bẫy WiChart](../10-sources/macro/wichart.md) · [7 cạm bẫy nguồn tin](../10-sources/news/README.md) · [3 bẫy cấu trúc Yahoo](../10-sources/global/yahoo.md) · [8 bẫy FRED](../10-sources/global/fred.md) · [5 bẫy tỷ giá](../10-sources/global/fx.md) · [4 bẫy Binance](../10-sources/global/crypto.md).

**Điểm chung của cả ba nhóm bẫy:** mọi thứ nguồn tự khai về chính nó đều phải kiểm lại bằng dữ liệu.

> **Và một bài học ngược lại, cũng đắt ngang:** không phải bất thường nào cũng là lỗi của nguồn. Khi bộ phân loại đơn vị tụt từ 19/19 xuống 16/19 sau khi thêm dữ liệu Screener, kết luận đầu tiên là *"Screener dùng thang khác"* — sai. Kiểm lại bằng `valueRange` của chính API thì thấy Screener dùng đúng thang, còn nguyên nhân là **luật phân loại của mình gãy trên giá trị cực trị toàn thị trường**. Đổ lỗi cho nguồn thì dễ, và nó chặn mất việc tìm ra lỗi thật.

