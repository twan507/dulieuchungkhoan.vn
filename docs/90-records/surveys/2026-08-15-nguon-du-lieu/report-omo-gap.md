# Truy tìm dữ liệu OMO · tín phiếu · repo — đo 2026-08-15

Câu hỏi chủ dự án: nguồn BVSC và FiinTrade (cũ lẫn mới) có dữ liệu nghiệp vụ thị trường mở, tín phiếu NHNN, repo không?

## Kết luận: KHÔNG. Cả ba nguồn đều không có.

| Nguồn | Đã kiểm bằng cách nào | OMO / tín phiếu / repo |
|---|---|---|
| **WiChart** (vĩ mô, 87 key) | Đọc toàn bộ danh mục §5.1 (18 vĩ mô) + §5.2 (8 tiền tệ & lãi suất) | ❌ không có |
| **FiinTrade** | Gọi thật `FIIN_CORE/Master/GetAllChartEconomy` → 36 chỉ tiêu | ❌ không có |
| **BVSC** | Toàn bộ 7 endpoint REST + bảng giá; nguồn thuần giao dịch | ❌ không có |

Gần nhất mà các nguồn có: **lãi suất** liên ngân hàng (giá của thanh khoản), **không phải khối lượng bơm/hút** (lượng thanh khoản).

## Vì sao đây là chỗ trống thật, không phải chi tiết vụn

`vn-stock-knowledge/references/macro-money-creation.md:320` liệt **năm nhân tố quyết định thanh khoản hằng ngày**, và OMO đứng đầu: *"**OMO** (hút ròng thì căng), **lãi suất liên ngân hàng** (tăng thì căng), **tỷ giá**… **tín dụng**… **lạm phát**"*.

Đối chiếu với dữ liệu đang có:

| Nhân tố skill yêu cầu | Nguồn hiện có | Trạng thái |
|---|---|---|
| Lãi suất liên ngân hàng | WiChart `lslnh` (qua đêm/1t/2t, ngày, trễ 1d) | ✅ đủ |
| Tỷ giá | WiChart `dhtg` (5 series, ngày) | ✅ đủ |
| Tín dụng | WiChart `td` (tháng, trễ 72d) | ✅ đủ |
| Lạm phát | WiChart `cpi` (tháng, trễ 42d) | ✅ đủ |
| **OMO** | — | ❌ **thiếu hoàn toàn** |

Tức là **4/5 nhân tố có dữ liệu, đúng nhân tố mà skill xếp đầu tiên thì không**. Skill còn nói rõ vì sao nó khác các nhân tố kia: *"muốn biết thanh khoản hôm nay thì nhìn OMO và lãi suất liên ngân hàng"* (`:179`) — OMO là biến số **hằng ngày**, trong khi tín dụng và lạm phát trễ 42–72 ngày.

⚠️ Nhưng cũng chính skill cảnh báo đừng đọc OMO ngây thơ (`:178`): *"OMO phần lớn thời gian là điều hoà… Chỉ khi tạo thành xu hướng kéo dài mới nói tới chuyện đổi cung tiền."* Nên thứ cần lưu là **chuỗi ròng luỹ kế**, không phải con số từng phiên.

## Phát hiện phụ — hai thứ đáng lấy mà chưa ai biết

Trong lúc dò ra danh mục 36 chỉ tiêu của FiinTrade (`GetAllChartEconomy`, endpoint **chưa có trong tài liệu dự án**):

**1. `OV_V` — Doanh số bình quân liên ngân hàng qua đêm.**
WiChart chỉ có **lãi suất** qua đêm (`lslnh`); FiinTrade có thêm **khối lượng giao dịch**. Đây là thứ gần OMO nhất tìm được: lãi suất cho biết *giá* của thanh khoản, doanh số cho biết *lượng*. Hai cái lệch nhau chính là tín hiệu — lãi suất tăng mà doanh số cũng tăng thì là cầu tiền tăng, khác hẳn lãi suất tăng mà doanh số teo (hệ thống kẹt). Đúng sắc thái mà `macro-money-creation.md:159` mô tả là "ngoại lệ phải nhớ".

**2. Bảy chỉ tiêu quốc tế nằm ngay trong FiinTrade:** `DJI` (Dow 30) · `NASDAQ` · `N225` (Nikkei 225) · `GoldS` (giá vàng thế giới) · `OilWTI` · `Last5Y` / `Last10Y` (giá đóng cửa TPCP 5 và 10 năm).

Điều này chạm thẳng vào khối "vĩ mô quốc tế" đang giao cho FRED/akshare — **một phần nhu cầu có thể lấy từ nguồn đã tích hợp sẵn**, cùng cơ chế xác thực, cùng hợp đồng dữ liệu, không thêm phụ thuộc ngoài. Cần so độ phủ và độ sâu với FRED trước khi quyết.

*(Chưa kiểm: cả 36 chỉ tiêu mới chỉ có **danh mục**; chưa gọi endpoint dữ liệu để biết tần suất, độ sâu lịch sử, độ trễ. `Last5Y`/`Last10Y` là **giá** trái phiếu, chưa rõ có suy ra lợi suất được không.)*

**3. Hai host FiinTrade chưa có trong bảng Base URL** (`00-conventions.md §1` liệt 6): `wlgw-news.fiintrade.vn` và `wl-realtime.fiintrade.vn`.

## Muốn có OMO thì lấy ở đâu — chưa kiểm, chỉ là hướng

Không nguồn nào trong dự án có. Các hướng khả dĩ, **chưa dò**:
- **NHNN (sbv.gov.vn)** — nơi công bố gốc kết quả đấu thầu OMO và phát hành tín phiếu. Là nguồn có thẩm quyền, nhưng thường ở dạng bảng/PDF, phải crawl.
- **WiFeed/WiChart gói khác** — giấy phép đã chốt; có thể có key ngoài 87 key đang dùng.
  → **Đã thử: không thấy.** Dò 11 tên key khả dĩ (`omo` · `thi_truong_mo` · `ttm` · `tin_phieu` · `tinphieu` · `repo` · `nhnn` · `bom_hut` · `thanh_khoan` · `ls_omo` · `dau_thau`) — **cả 11 đều trả `500`**, đúng hành vi "key không tồn tại" mà `wichart.md §2.1` đã ghi.
  ⚠️ **Bằng chứng yếu, đừng đọc thành kết luận chắc.** Đây là đoán tên, không phải liệt kê danh mục — API không có endpoint liệt kê key, nên "500 với 11 cái tên tôi nghĩ ra" chỉ loại được 11 cái tên đó. Muốn chắc phải hỏi thẳng WiFeed danh mục key đầy đủ.
- Báo điện tử trong 8 nguồn tin đã khảo sát đưa tin OMO hằng ngày, nhưng là **văn bản**, không phải chuỗi số — chỉ hợp làm đối chiếu, không làm nguồn dữ liệu.

**Đề xuất thứ tự:** thử WiChart trước (rẻ, đã có quyền), rồi mới tính tới NHNN.
