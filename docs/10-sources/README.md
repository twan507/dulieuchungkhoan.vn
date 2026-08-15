# Nguồn dữ liệu — tài liệu tra cứu

**Phiên bản:** 4.5 · **Ngày:** 2026-08-15 · **Trạng thái:** Hoàn chỉnh — 131 endpoint REST + 5 topic realtime + 47 feed tin

---

## 1. Tầng tài liệu này là gì

Toàn bộ `10-sources/` là **tài liệu tra cứu (reference)** theo phân loại Diátaxis: trung lập, đầy đủ, chính xác. Nó mô tả *nguồn bên ngoài có gì và cư xử thế nào*, không hướng dẫn *nên xây sản phẩm thế nào*.

> **Ranh giới quan trọng nhất của kho tài liệu này:** những gì ở đây là **sự thật đo được về hệ thống của người khác** — sửa một con số ở đây mà không đo lại là nói dối. Những gì ở [`20-design/`](../20-design/) là **lựa chọn của Finext** — sửa được, nhưng phải ghi lý do.

Ba nguồn độc lập:

| Nguồn | Nằm ở | Nội dung | Ngày kiểm chứng |
|---|---|---|---|
| BVSC + FiinTrade | [`market/`](market/) — file `00`–`11`, phụ lục A/B | Cổ phiếu, chỉ số, BCTC, dòng tiền, realtime | 2026-08-10, mẫu 51 mã |
| WiChart (WiGroup) | [`macro/wichart.md`](macro/wichart.md) | Vĩ mô, tiền tệ, giá hàng hoá | 2026-08-12, toàn bộ 87 key |
| 8 báo điện tử | [`news/README.md`](news/README.md) | 47 feed RSS + 6 crawler HTML, encoding, khối lượng | 2026-08-13, 307 URL · 1.408 tiêu đề |

Mọi thông tin đều được **kiểm chứng bằng lời gọi thật**. Không có nội dung nào suy đoán từ tên endpoint. Riêng WiChart còn kèm **bộ tự kiểm chứng chạy được** ([`verify_wichart.py`](macro/verify_wichart.py)) đối chiếu từng khẳng định với API sống.

**Thiết kế hệ thống dựng trên ba nguồn này** nằm ở [`20-design/`](../20-design/): [kho dữ liệu thị trường](../20-design/market-data-store.md), [pipeline tin tức](../20-design/news-pipeline.md) và [chọn trường cho ETL](../20-design/market-field-selection.md).

## 2. Phạm vi

Mục này nói về phạm vi **hai nguồn API** (thị trường và vĩ mô). Phạm vi nguồn tin tức có bảng riêng ở [`news/README.md`](news/README.md).

### Trong phạm vi

| Nhóm | Số endpoint |
|---|---|
| REST — BVSC (`online.bvsc.com.vn`) | 7 |
| REST — Biểu đồ BVSC (`apis.bvsc.com.vn`) | 4 |
| REST — FiinTrade (6 host `*.fiintrade.vn`) | 33 |
| REST — WiChart (`api.wichart.vn`) | 87 |
| **Tổng REST** | **131** |
| Realtime — Socket.IO BVSC | 1 kênh / 5 topic |

Đối tượng dữ liệu:

- **Cổ phiếu** 1.974 mã *(đo 2026-08-15)* · **chỉ số** 20 · **giao dịch thoả thuận** *(BVSC/FiinTrade)*
- **Vĩ mô** 18 chỉ tiêu · **tiền tệ & lãi suất** 8 · **giá hàng hoá** 61 mặt hàng *(WiChart)*

Trong 87 key WiChart, phân loại sau audit: **61 lõi · 6 phụ · 20 loại bỏ**. Chi tiết ở [wichart.md](macro/wichart.md).

### Ngoài phạm vi

Chứng quyền · Lô lẻ · Phái sinh · Trái phiếu · ETF/Quỹ · Toàn bộ luồng cần đăng nhập (tài khoản, danh mục, đặt lệnh) · Realtime FiinTrade (SignalR) · Cổ phiếu và chỉ số quốc tế · Crypto · NAV quỹ mở.

*(Tin tức từng nằm trong danh sách này khi tài liệu chỉ phủ hai nguồn API. Nay đã có nguồn riêng — xem [`news/`](news/README.md).)*

## 3. Cấu trúc tài liệu

### 3.1 Nguồn thị trường — `market/`

| File | Nội dung | Số endpoint |
|---|---|---|
| [00-conventions.md](market/00-conventions.md) | **Đọc trước tiên.** Base URL, xác thực, cấu trúc response, xử lý lỗi, kiểu dữ liệu, đơn vị, 9 bẫy triển khai, và **kết quả đo rate limit** | — |
| [01-bvsc-rest.md](market/01-bvsc-rest.md) | Danh mục mã, snapshot, sổ lệnh khớp, chỉ số | 7 |
| [02-bvsc-tvcharts.md](market/02-bvsc-tvcharts.md) | Biểu đồ lịch sử chuẩn TradingView UDF | 4 |
| [03-fiin-reference.md](market/03-fiin-reference.md) | Danh bạ doanh nghiệp, cây ngành ICB | 2 |
| [04-fiin-company-profile.md](market/04-fiin-company-profile.md) | Snapshot, sở hữu, cổ tức, xếp hạng | 5 |
| [05-fiin-financial-statements.md](market/05-fiin-financial-statements.md) | CĐKT, KQKD, LCTT, bản PDF gốc | 4 |
| [06-fiin-scoring-valuation.md](market/06-fiin-scoring-valuation.md) | Chỉ số tài chính, chấm điểm, định giá | 6 |
| [07-fiin-money-flow.md](market/07-fiin-money-flow.md) | Khối ngoại, tự doanh, đóng góp chỉ số | 3 |
| [08-fiin-event-calendar.md](market/08-fiin-event-calendar.md) | ĐHCĐ, cổ tức, KQKD, IPO, phát hành, vĩ mô | 8 |
| [09-fiin-market-price.md](market/09-fiin-market-price.md) | Giá lịch sử 97 trường, thanh khoản, BU/SD | 3 |
| [10-fiin-dictionary.md](market/10-fiin-dictionary.md) | Từ điển mã trường + **bộ sàng lọc toàn thị trường** | 2 |
| [11-bvsc-realtime.md](market/11-bvsc-realtime.md) | **Socket.IO** — bắt tay, đăng ký, 5 sự kiện, 86 trường, tần suất | 5 topic |
| [appendix-A-field-codes.md](market/appendix-A-field-codes.md) | Bảng tra mã trường (`rtd11`, `rtq12`, `bsa1`…) | — |
| [appendix-B-coverage.md](market/appendix-B-coverage.md) | Kết quả kiểm thử độ phủ trên 51 mã | — |

### 3.2 Nguồn vĩ mô và hàng hoá — `macro/`

| File | Nội dung | Số endpoint |
|---|---|---|
| [wichart.md](macro/wichart.md) | **WiChart** — vĩ mô, tiền tệ, giá hàng hoá. 6 bẫy, bộ ký hiệu, bảng tra 87 key kèm hệ số đơn vị, bảng hardcode Python, bản đồ hàng hoá → mã niêm yết | 87 |
| [`verify_wichart.py`](macro/verify_wichart.py) | **Script tự kiểm chứng** — đọc registry ngay trong `wichart.md` rồi đối chiếu 509 khẳng định với API sống. Dùng làm bộ giám sát hợp đồng hàng ngày | — |

### 3.3 Nguồn tin tức — `news/`

| File | Nội dung | Số nguồn |
|---|---|---|
| [news/README.md](news/README.md) | 47 feed RSS, 6 crawler HTML, quy tắc chuẩn hoá encoding và thời gian đăng, khối lượng đo được, nguồn đã loại | 8 báo |
| [`news/feeds.json`](news/feeds.json) | Cùng nội dung ở dạng máy đọc — feed, taxonomy 20 sub, nhật ký loại bỏ | 47 feed |

### 3.4 Tài liệu thiết kế dựng trên các nguồn này

Không nằm trong tầng tra cứu, nhưng đọc kèm:

| File | Nội dung |
|---|---|
| [market-data-store.md](../20-design/market-data-store.md) | **Kiến trúc Finext** — thu thập, lưu trữ, phân phối lại. Sơ đồ, DDL, lịch ETL, SSE, chatbot, giám sát hợp đồng |
| [news-pipeline.md](../20-design/news-pipeline.md) | Kiến trúc gom tin, taxonomy, quy tắc phân loại, gắn mã cổ phiếu, kho lưu trữ |

## 4. Quy ước trình bày

Mỗi endpoint được mô tả theo cấu trúc thống nhất, lấy theo OpenAPI 3.1 Operation Object:

```
### <operationId>
Tóm tắt · Mô tả · Method + Path · Tham số · Header
Response 200 (schema + ví dụ) · Lỗi · Ghi chú & bẫy · Độ phủ · Hiệu năng
```

Ký hiệu trong bảng tham số:

| Ký hiệu | Nghĩa |
|---|---|
| **bắt buộc** | Thiếu sẽ lỗi hoặc trả rỗng |
| *tuỳ chọn* | Có thể bỏ qua |
| `enum` | Chỉ nhận đúng các giá trị liệt kê — giá trị khác bị từ chối hoặc bị bỏ qua âm thầm |
| ⚠️ | Có hành vi bất thường, đọc kỹ phần Ghi chú |

## 5. Điều kiện tiên quyết

**FiinTrade** — trước khi gọi bất kỳ endpoint nào, ứng dụng **bắt buộc** phải nạp và cache bảng ánh xạ `ticker → organCode` từ [`Master/GetListOrganization`](market/03-fiin-reference.md). 41% doanh nghiệp có `organCode` khác `ticker`, và gọi sai sẽ nhận `HTTP 200` với dữ liệu rỗng, không có bất kỳ thông báo lỗi nào. Xem chi tiết tại [00-conventions.md](market/00-conventions.md).

**WiChart** — hai điều kiện bắt buộc trước khi lưu bất kỳ giá trị nào:

1. **Parse epoch bằng `Asia/Ho_Chi_Minh`**, không phải UTC. Mọi timestamp là 17:00 UTC = nửa đêm giờ VN; parse sai sẽ tạo ảo giác lệch nhãn 1 tháng trên toàn bộ chuỗi tháng.
2. **Dùng bảng hệ số đơn vị đã hardcode** ở [wichart.md §9](macro/wichart.md). Nhãn `unit` của API sai ở 15 series, sai lệch 1000 lần, **rải rác ngẫu nhiên không theo quy luật nào** — kể cả giữa hai series cùng họ sản phẩm.

## 6. Nhật ký thay đổi

| Phiên bản | Ngày | Nội dung |
|---|---|---|
| **4.5** | **2026-08-15** | **Kiểm rate limit FiinGroup bằng đúng tải ETL kế hoạch — không dò ngưỡng trần.** 64 lời gọi tuần tự, một luồng: burst thường nhật `GetScreenerItems` **52 trang liên tiếp** *(`comGroupCode=ALL`, 1 tiêu chí, 1.549 mã, 7,7 MB)* chạy trọn trong **1 phút 49 giây ≈ 29 request/phút**, cộng mẫu 10 lời gọi họ `Snapshot/*`. **Không gặp tín hiệu chặn nào** — `HTTP 200` trên cả 64 lời gọi, không `429`, không `Retry-After`, latency trang 52 không cao hơn trang 1 *(trung vị 2.074 ms)*. **Xác nhận nguồn không có header hạn mức:** hợp nhất header của 64 response không có `X-RateLimit-*` — ETL phải tự giữ nhịp bằng token bucket. **Một lời gọi hỏng, và không phải do chặn:** request thứ 2 của phiên trả `status: "Failed"` kèm **Redis timeout nội bộ của chính FiinTrade** — đã ghi là lỗi tạm thời cần thử lại có kiểm soát, không được coi là dữ liệu rỗng. **Giới hạn của kết luận, ghi rõ trong tài liệu:** phép đo chỉ chứng minh **nhịp tuần tự** an toàn; nhịp **8 luồng** của lịch ETL hằng ngày *(~6.000 lời gọi / 20–30 phút ≈ 200–300 request/phút)* và trần 2 request/giây của backfill **chưa kiểm**. Kết quả đầy đủ: [`00-conventions.md` §10](market/00-conventions.md). **Đồng bộ latency [`10-fiin-dictionary.md`](market/10-fiin-dictionary.md):** 52 mẫu `getScreenerItems` ALL cho **trung vị 2,07 s** *(min 1,08 · p90 2,68 · max 3,10)* — trả lời xong câu treo *"endpoint chậm đi thật hay chỉ gặp một lần tải cao"* của bản 4.4: **là tải cao nhất thời**, con số 6,44 s chỉ là một điểm dữ liệu của lần đo sớm hơn trong cùng ngày. Gỡ cờ 🔴 *"đo lại trước khi đặt lịch ETL"* vì ngân sách 52 lời gọi nay **đo trực tiếp**: 1 phút 49 giây. `GetScreenerParameters` cũng ghi cả hai lần đo cùng ngày (6,33 s và 2,77 s). Kéo theo: hạ mục rate limit khỏi danh sách chặn ở [roadmap](../00-overview/roadmap.md) và [README](../../README.md), cập nhật [kho dữ liệu §4.3 · §7 · §8](../20-design/market-data-store.md) |
| **4.4** | **2026-08-15** | **Đo lại thật, chốt 10/16 dòng `cần kiểm API` và ba chỗ vênh của tầng reference.** Gọi lại `GetScreenerParameters` (13 nhóm / 83 tiêu chí, không đổi), `GetScreenerItems` một tiêu chí trên `ALL` và `VN30`, BVSC `/quotes?symbols=ALL` và `/datafeed/instruments`, `GetSnapshot` + `GetSnapshotNoneBank`. **Ba chỗ vênh đã giải:** *(1)* **223 vs 193** — 223 là tổng kích thước 5 khối, 193 là số khoá **phân biệt**; 27 khoá nằm ở ≥2 khối, dư đúng 30. Không liên quan loại hình doanh nghiệp. *(2)* BVSC `datafeed/instruments` **62 trường** đúng, con số 50 ở tiêu đề [`01-bvsc-rest.md`](market/01-bvsc-rest.md) là lỗi đếm — đã sửa. *(3)* 🔴 **`foreignerRoom` của Screener là room CÒN LẠI** (= `foreignRemain` của BVSC), **không phải** tổng room; tổng room nằm ở `priceInfo.foreignTotalRoom`. **Sửa quy tắc hoa/thường:** `getScreenerItems` chỉ hạ **chữ cái đầu** (`ForeignerRoom` → `foreignerRoom`), viết thường toàn bộ trượt 31/83 khoá — đã sửa [`field-dictionary.json`](market/field-dictionary.json) `_meta.quy_tac_tra.chuan_hoa` và thu hẹp phạm vi tuyên bố độ phủ 100% về đúng ba endpoint BCTC. **Số đếm đo lại:** BVSC `getAllQuotes` **2.534** bản ghi *(2026-08-10: 2.530)* · Screener `totalCount` **1.549** *(2026-08-10: 1.517)* · `GetSnapshot` 54 khoá, `GetSnapshotNoneBank` **56**. `rtd39`/`rtd54` xác nhận **có thật** trong khối `financial` nhưng vẫn chưa có tên. **Vá nhất quán sau review:** số cổ phiếu 1.972 → **1.974** ở mọi nơi còn chép số cũ *(README §2, [architecture](../00-overview/architecture.md), [roadmap](../00-overview/roadmap.md), [09-fiin-market-price](market/09-fiin-market-price.md), [market-data-store](../20-design/market-data-store.md))*, và roadmap sửa cả chỗ **gán nhầm nguồn** — 1.974 là đếm `StockType=2` từ `getAllQuotes` của BVSC, không phải của `getListOrganization`. Ngân sách lời gọi Screener 51 → **52**. **Hiệu năng:** ba dòng đo lại đều ghi rõ *"1 lần chạy"* — FiinTrade chậm hơn số 2026-08-10 khoảng một bậc (`GetScreenerParameters` 1,45 s → 6,33 s; `GetScreenerItems` ALL ~682 ms → 6,44 s), **chưa đủ để kết luận** endpoint đã chậm đi, nhưng đủ để không dựng SLA lên nó. **Nhãn nguồn:** `foreignerroom.ten_vi` giữ nguyên nhãn API tự khai *("Room nước ngoài")*; ngữ nghĩa đo được *(là room CÒN LẠI)* nằm ở `ghi_chu_do_2026_08_15` và ở [Phụ lục A](market/appendix-A-field-codes.md) — tầng reference chép nguồn, không viết lại nguồn. Chi tiết từng mã: [chọn trường cho ETL thị trường](../20-design/market-field-selection.md) |
| **4.3** | **2026-08-14** | **Chốt nguồn chuẩn cho từng chỉ tiêu.** Giá/kỹ thuật/khối ngoại/thoả thuận → BVSC. Screener giữ **80/193** trường, Snapshot cắt còn **16/54**, bỏ hẳn nhóm chấm điểm. Giữ MoneyFlow cho tự doanh và đóng góp chỉ số vì BVSC không có. Kèm 4 phát hiện: Screener timeout khi gửi nhiều tiêu chí · `isa20ttm` lệch tổng `isa20` tới 9,4% · `P/E = vốn hoá ÷ isa20ttm` khớp 9/10 · `revttm` không phải mẫu số P/S với ngân hàng. Xem [ADR 0002](../00-overview/decisions/0002-data-source-selection.md) |
| **4.2** | **2026-08-14** | **Xác định đơn vị dữ liệu cho 727/729 mã** (99,7%), trong đó **392 mã xác thực bằng bằng chứng số học**. Phép kiểm bắt được 3 lỗi đơn vị của chính từ điển. Phát hiện 🔴 **nhãn `unit` của API không phải đơn vị của dữ liệu** — `Percentage` thực ra là thập phân, `BillionVND` thực ra là VND đầy đủ. Bổ sung tên tiếng Anh cho 26 mã, xác định 3 mã bằng đối chiếu số học |
| **4.1** | **2026-08-14** | **Giải mã 729 mã chỉ tiêu** — toàn bộ họ `bs*`, `is*`, `cf*`, `nob*` cho cả bốn loại hình doanh nghiệp. Nguồn là bundle JS của ứng dụng FiinTrade, **không phải API**. Độ phủ đo trên 21 response thật của 5 mã: **100%**. Xem [Phụ lục A §A.5](market/appendix-A-field-codes.md) và [field-dictionary.json](market/field-dictionary.json) |
| **4.0** | **2026-08-14** | **Tái cấu trúc kho tài liệu.** Tách tài liệu kiến trúc Finext (file `12`) ra khỏi tầng tra cứu; gộp nguồn tin tức (47 feed RSS + 6 crawler) vào cùng tầng như nguồn thứ ba; đổi `13` → `macro/wichart.md`. Nội dung kỹ thuật không đổi một chữ — xem [ADR 0001](../00-overview/decisions/0001-docs-structure.md) |
| **3.0** | **2026-08-12** | **Thêm nguồn WiChart** (file `13`) — 87 endpoint vĩ mô/tiền tệ/hàng hoá, audit 4 vòng bằng 7 agent song song + đối chiếu chéo web. Kèm [`verify_wichart.py`](macro/verify_wichart.py) tự kiểm 509 khẳng định. Cập nhật phạm vi và điều kiện tiên quyết |
| 1.0 | 2026-08-10 | Bản đầu — 43 endpoint REST, kiểm chứng trên 51 mã |
| 1.1 | 2026-08-10 | Bổ sung phần Realtime — 5 topic, 86 trường, đo 3.266 frame phiên chiều |
| 2.2 | 2026-08-10 | Thêm mục 7.1 — giám sát hợp đồng dữ liệu và theo dõi bản build của nguồn. Đặt lại chiến lược mục 9: thích ứng liên tục thay vì chuẩn bị đổi nguồn |
| 2.1 | 2026-08-10 | Thêm mục 9 — định hướng nghiên cứu khả năng đổi nguồn dữ liệu |
| 2.0 | 2026-08-10 | Thêm tài liệu kiến trúc triển khai Finext. Bổ sung Bẫy 8 (giá điều chỉnh) và Bẫy 4b (thang đơn vị Screener) |
| 1.2 | 2026-08-10 | Thêm `getScreenerItems` (sàng lọc toàn TT). **Sửa lỗi:** giá lịch sử là giá ĐÃ điều chỉnh, không phải giá thô. Bổ sung độ sâu phân trang: `getPriceData` 12,5 năm, tvcharts chặn 239 nến |

## 7. Giới hạn của tài liệu

- Toàn bộ endpoint mô tả ở đây là API nội bộ, **không phải public API có cam kết**. Không có versioning, không có thông báo thay đổi. Schema có thể đổi bất cứ lúc nào.
- Số liệu hiệu năng đo trên một máy trạm tại Việt Nam, chỉ mang tính tham khảo.
- ✅ **Tình trạng pháp lý hai nguồn nay đều đã rõ.** Với BVSC/FiinTrade, Finext được phép thu thập, lưu trữ và phái sinh. Với **WiChart**, giấy phép **WiFeed** đã chốt 2026-08-15, phủ đúng endpoint `api.wichart.vn` đang dùng — xem [`wichart.md` §1](macro/wichart.md).
- Ngưỡng rate limit của WiChart **chưa đo**. Không có header `X-RateLimit-*` hay `Retry-After`.
- Với **FiinTrade**, rate limit đã kiểm ngày 2026-08-15 **bằng đúng tải ETL kế hoạch, chủ đích không dò ngưỡng trần** — nhịp tuần tự ~29 request/phút chạy trọn không bị chặn, nguồn cũng không trả header hạn mức nào. **Ngưỡng thật vẫn không biết**, và nhịp 8 luồng chưa kiểm. Chi tiết: [`00-conventions.md` §10](market/00-conventions.md).
