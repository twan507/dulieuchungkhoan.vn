# Nguồn dữ liệu — tài liệu tra cứu

**Phiên bản:** 3.0 · **Ngày:** 2026-08-12 · **Trạng thái:** Hoàn chỉnh — 131 endpoint REST + 5 topic realtime + 47 feed tin

---

## 1. Tầng tài liệu này là gì

Toàn bộ `10-nguon-du-lieu/` là **tài liệu tra cứu (reference)** theo phân loại Diátaxis: trung lập, đầy đủ, chính xác. Nó mô tả *nguồn bên ngoài có gì và cư xử thế nào*, không hướng dẫn *nên xây sản phẩm thế nào*.

> **Ranh giới quan trọng nhất của kho tài liệu này:** những gì ở đây là **sự thật đo được về hệ thống của người khác** — sửa một con số ở đây mà không đo lại là nói dối. Những gì ở [`20-thiet-ke/`](../20-thiet-ke/) là **lựa chọn của Finext** — sửa được, nhưng phải ghi lý do.

Ba nguồn độc lập:

| Nguồn | Nằm ở | Nội dung | Ngày kiểm chứng |
|---|---|---|---|
| BVSC + FiinTrade | [`thi-truong/`](thi-truong/) — file `00`–`11`, phụ lục A/B | Cổ phiếu, chỉ số, BCTC, dòng tiền, realtime | 2026-08-10, mẫu 51 mã |
| WiChart (WiGroup) | [`vi-mo-hang-hoa/wichart.md`](vi-mo-hang-hoa/wichart.md) | Vĩ mô, tiền tệ, giá hàng hoá | 2026-08-12, toàn bộ 87 key |
| 10 báo điện tử | [`tin-tuc/README.md`](tin-tuc/README.md) | 47 feed RSS + 6 crawler HTML, encoding, khối lượng | 2026-08-13, 307 URL · 1.408 tiêu đề |

Mọi thông tin đều được **kiểm chứng bằng lời gọi thật**. Không có nội dung nào suy đoán từ tên endpoint. Riêng WiChart còn kèm **bộ tự kiểm chứng chạy được** ([`verify_wichart.py`](../../scripts/verify_wichart.py)) đối chiếu từng khẳng định với API sống.

**Thiết kế hệ thống dựng trên ba nguồn này** nằm ở [`20-thiet-ke/`](../20-thiet-ke/): [kho dữ liệu thị trường](../20-thiet-ke/kho-du-lieu-thi-truong.md) và [pipeline tin tức](../20-thiet-ke/pipeline-tin-tuc.md).

## 2. Phạm vi

Mục này nói về phạm vi **hai nguồn API** (thị trường và vĩ mô). Phạm vi nguồn tin tức có bảng riêng ở [`tin-tuc/README.md`](tin-tuc/README.md).

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

- **Cổ phiếu** 1.972 mã · **chỉ số** 20 · **giao dịch thoả thuận** *(BVSC/FiinTrade)*
- **Vĩ mô** 18 chỉ tiêu · **tiền tệ & lãi suất** 8 · **giá hàng hoá** 61 mặt hàng *(WiChart)*

Trong 87 key WiChart, phân loại sau audit: **61 lõi · 6 phụ · 20 loại bỏ**. Chi tiết ở [13-wichart-vi-mo-hang-hoa.md](vi-mo-hang-hoa/wichart.md).

### Ngoài phạm vi

Chứng quyền · Lô lẻ · Phái sinh · Trái phiếu · ETF/Quỹ · Toàn bộ luồng cần đăng nhập (tài khoản, danh mục, đặt lệnh) · Realtime FiinTrade (SignalR) · Cổ phiếu và chỉ số quốc tế · Crypto · NAV quỹ mở.

*(Tin tức từng nằm trong danh sách này khi tài liệu chỉ phủ hai nguồn API. Nay đã có nguồn riêng — xem [`tin-tuc/`](tin-tuc/README.md).)*

## 3. Cấu trúc tài liệu

### 3.1 Nguồn thị trường — `thi-truong/`

| File | Nội dung | Số endpoint |
|---|---|---|
| [00-quy-uoc-chung.md](thi-truong/00-quy-uoc-chung.md) | **Đọc trước tiên.** Base URL, xác thực, cấu trúc response, xử lý lỗi, kiểu dữ liệu, đơn vị, và 9 bẫy triển khai | — |
| [01-bvsc-rest.md](thi-truong/01-bvsc-rest.md) | Danh mục mã, snapshot, sổ lệnh khớp, chỉ số | 7 |
| [02-bvsc-tvcharts.md](thi-truong/02-bvsc-tvcharts.md) | Biểu đồ lịch sử chuẩn TradingView UDF | 4 |
| [03-fiin-tham-chieu.md](thi-truong/03-fiin-tham-chieu.md) | Danh bạ doanh nghiệp, cây ngành ICB | 2 |
| [04-fiin-ho-so-doanh-nghiep.md](thi-truong/04-fiin-ho-so-doanh-nghiep.md) | Snapshot, sở hữu, cổ tức, xếp hạng | 5 |
| [05-fiin-bao-cao-tai-chinh.md](thi-truong/05-fiin-bao-cao-tai-chinh.md) | CĐKT, KQKD, LCTT, bản PDF gốc | 4 |
| [06-fiin-cham-diem-dinh-gia.md](thi-truong/06-fiin-cham-diem-dinh-gia.md) | Chỉ số tài chính, chấm điểm, định giá | 6 |
| [07-fiin-dong-tien.md](thi-truong/07-fiin-dong-tien.md) | Khối ngoại, tự doanh, đóng góp chỉ số | 3 |
| [08-fiin-lich-su-kien.md](thi-truong/08-fiin-lich-su-kien.md) | ĐHCĐ, cổ tức, KQKD, IPO, phát hành, vĩ mô | 8 |
| [09-fiin-gia-thi-truong.md](thi-truong/09-fiin-gia-thi-truong.md) | Giá lịch sử 97 trường, thanh khoản, BU/SD | 3 |
| [10-fiin-tu-dien.md](thi-truong/10-fiin-tu-dien.md) | Từ điển mã trường + **bộ sàng lọc toàn thị trường** | 2 |
| [11-bvsc-realtime.md](thi-truong/11-bvsc-realtime.md) | **Socket.IO** — bắt tay, đăng ký, 5 sự kiện, 86 trường, tần suất | 5 topic |
| [phu-luc-A-ma-field.md](thi-truong/phu-luc-A-ma-field.md) | Bảng tra mã trường (`rtd11`, `rtq12`, `bsa1`…) | — |
| [phu-luc-B-do-phu-du-lieu.md](thi-truong/phu-luc-B-do-phu-du-lieu.md) | Kết quả kiểm thử độ phủ trên 51 mã | — |

### 3.2 Nguồn vĩ mô và hàng hoá — `vi-mo-hang-hoa/`

| File | Nội dung | Số endpoint |
|---|---|---|
| [wichart.md](vi-mo-hang-hoa/wichart.md) | **WiChart** — vĩ mô, tiền tệ, giá hàng hoá. 6 bẫy, bộ ký hiệu, bảng tra 87 key kèm hệ số đơn vị, bảng hardcode Python, bản đồ hàng hoá → mã niêm yết | 87 |
| [`scripts/verify_wichart.py`](../../scripts/verify_wichart.py) | **Script tự kiểm chứng** — đọc registry ngay trong `wichart.md` rồi đối chiếu 509 khẳng định với API sống. Dùng làm bộ giám sát hợp đồng hàng ngày | — |

### 3.3 Nguồn tin tức — `tin-tuc/`

| File | Nội dung | Số nguồn |
|---|---|---|
| [tin-tuc/README.md](tin-tuc/README.md) | 47 feed RSS, 6 crawler HTML, quy tắc chuẩn hoá encoding và thời gian đăng, khối lượng đo được, nguồn đã loại | 10 báo |
| [`config/feeds.json`](../../config/feeds.json) | Cùng nội dung ở dạng máy đọc — feed, taxonomy 20 sub, nhật ký loại bỏ | 47 feed |

### 3.4 Tài liệu thiết kế dựng trên các nguồn này

Không nằm trong tầng tra cứu, nhưng đọc kèm:

| File | Nội dung |
|---|---|
| [kho-du-lieu-thi-truong.md](../20-thiet-ke/kho-du-lieu-thi-truong.md) | **Kiến trúc Finext** — thu thập, lưu trữ, phân phối lại. Sơ đồ, DDL, lịch ETL, SSE, chatbot, giám sát hợp đồng |
| [pipeline-tin-tuc.md](../20-thiet-ke/pipeline-tin-tuc.md) | Kiến trúc gom tin, taxonomy, quy tắc phân loại, gắn mã cổ phiếu, kho lưu trữ |

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

**FiinTrade** — trước khi gọi bất kỳ endpoint nào, ứng dụng **bắt buộc** phải nạp và cache bảng ánh xạ `ticker → organCode` từ [`Master/GetListOrganization`](thi-truong/03-fiin-tham-chieu.md). 41% doanh nghiệp có `organCode` khác `ticker`, và gọi sai sẽ nhận `HTTP 200` với dữ liệu rỗng, không có bất kỳ thông báo lỗi nào. Xem chi tiết tại [00-quy-uoc-chung.md](thi-truong/00-quy-uoc-chung.md).

**WiChart** — hai điều kiện bắt buộc trước khi lưu bất kỳ giá trị nào:

1. **Parse epoch bằng `Asia/Ho_Chi_Minh`**, không phải UTC. Mọi timestamp là 17:00 UTC = nửa đêm giờ VN; parse sai sẽ tạo ảo giác lệch nhãn 1 tháng trên toàn bộ chuỗi tháng.
2. **Dùng bảng hệ số đơn vị đã hardcode** ở [13-wichart-vi-mo-hang-hoa.md §9](vi-mo-hang-hoa/wichart.md). Nhãn `unit` của API sai ở 15 series, sai lệch 1000 lần, **rải rác ngẫu nhiên không theo quy luật nào** — kể cả giữa hai series cùng họ sản phẩm.

## 6. Nhật ký thay đổi

| Phiên bản | Ngày | Nội dung |
|---|---|---|
| **4.3** | **2026-08-14** | **Chốt nguồn chuẩn cho từng chỉ tiêu.** Giá/kỹ thuật/khối ngoại/thoả thuận → BVSC. Screener giữ **80/193** trường, Snapshot cắt còn **16/54**, bỏ hẳn nhóm chấm điểm. Giữ MoneyFlow cho tự doanh và đóng góp chỉ số vì BVSC không có. Kèm 4 phát hiện: Screener timeout khi gửi nhiều tiêu chí · `isa20ttm` lệch tổng `isa20` tới 9,4% · `P/E = vốn hoá ÷ isa20ttm` khớp 9/10 · `revttm` không phải mẫu số P/S với ngân hàng. Xem [ADR 0002](../00-tong-quan/quyet-dinh/0002-chon-nguon-du-lieu.md) |
| **4.2** | **2026-08-14** | **Xác định đơn vị dữ liệu cho 727/729 mã** (99,7%), trong đó **392 mã xác thực bằng bằng chứng số học**. Phép kiểm bắt được 3 lỗi đơn vị của chính từ điển. Phát hiện 🔴 **nhãn `unit` của API không phải đơn vị của dữ liệu** — `Percentage` thực ra là thập phân, `BillionVND` thực ra là VND đầy đủ. Bổ sung tên tiếng Anh cho 26 mã, xác định 3 mã bằng đối chiếu số học |
| **4.1** | **2026-08-14** | **Giải mã 729 mã chỉ tiêu** — toàn bộ họ `bs*`, `is*`, `cf*`, `nob*` cho cả bốn loại hình doanh nghiệp. Nguồn là bundle JS của ứng dụng FiinTrade, **không phải API**. Độ phủ đo trên 21 response thật của 5 mã: **100%**. Xem [Phụ lục A §A.5](thi-truong/phu-luc-A-ma-field.md) và [tu-dien-ma-field.json](thi-truong/tu-dien-ma-field.json) |
| **4.0** | **2026-08-14** | **Tái cấu trúc kho tài liệu.** Tách tài liệu kiến trúc Finext (file `12`) ra khỏi tầng tra cứu; gộp nguồn tin tức (47 feed RSS + 6 crawler) vào cùng tầng như nguồn thứ ba; đổi `13` → `vi-mo-hang-hoa/wichart.md`. Nội dung kỹ thuật không đổi một chữ — xem [ADR 0001](../00-tong-quan/quyet-dinh/0001-cau-truc-kho-tai-lieu.md) |
| **3.0** | **2026-08-12** | **Thêm nguồn WiChart** (file `13`) — 87 endpoint vĩ mô/tiền tệ/hàng hoá, audit 4 vòng bằng 7 agent song song + đối chiếu chéo web. Kèm [`verify_wichart.py`](../../scripts/verify_wichart.py) tự kiểm 509 khẳng định. Cập nhật phạm vi và điều kiện tiên quyết |
| 1.0 | 2026-08-10 | Bản đầu — 43 endpoint REST, kiểm chứng trên 51 mã |
| 1.1 | 2026-08-10 | Bổ sung phần Realtime — 5 topic, 86 trường, đo 3.266 frame phiên chiều |
| 2.2 | 2026-08-10 | Thêm mục 7.1 — giám sát hợp đồng dữ liệu và theo dõi bản build của nguồn. Đặt lại chiến lược mục 9: thích ứng liên tục thay vì chuẩn bị đổi nguồn |
| 2.1 | 2026-08-10 | Thêm mục 9 — định hướng nghiên cứu khả năng đổi nguồn dữ liệu |
| 2.0 | 2026-08-10 | Thêm tài liệu kiến trúc triển khai Finext. Bổ sung Bẫy 8 (giá điều chỉnh) và Bẫy 4b (thang đơn vị Screener) |
| 1.2 | 2026-08-10 | Thêm `getScreenerItems` (sàng lọc toàn TT). **Sửa lỗi:** giá lịch sử là giá ĐÃ điều chỉnh, không phải giá thô. Bổ sung độ sâu phân trang: `getPriceData` 12,5 năm, tvcharts chặn 239 nến |

## 7. Giới hạn của tài liệu

- Toàn bộ endpoint mô tả ở đây là API nội bộ, **không phải public API có cam kết**. Không có versioning, không có thông báo thay đổi. Schema có thể đổi bất cứ lúc nào.
- Số liệu hiệu năng đo trên một máy trạm tại Việt Nam, chỉ mang tính tham khảo.
- 🔴 **Tình trạng pháp lý hai nguồn KHÁC NHAU.** Với BVSC/FiinTrade, Finext được phép thu thập, lưu trữ và phái sinh. Với **WiChart thì chưa** — dữ liệu thuộc bản quyền CTCP WiGroup và đang được truy cập qua endpoint nội bộ phục vụ trang đối tác. Phải chốt giấy phép **WiFeed** trước khi đưa vào sản phẩm thương mại. Xem [`wichart.md` §1](vi-mo-hang-hoa/wichart.md) và [§10](vi-mo-hang-hoa/wichart.md).
- Ngưỡng rate limit của WiChart **chưa đo**. Không có header `X-RateLimit-*` hay `Retry-After`.
