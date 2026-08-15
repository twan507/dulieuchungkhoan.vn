# Lộ trình hợp nhất

**Ngày:** 2026-08-14 · Gộp danh sách "việc tiếp theo" của ba khối tài liệu, xếp lại theo **phụ thuộc thật** thay vì theo thứ tự từng khối được viết ra.

Ba khối vốn có ba danh sách việc riêng, mỗi danh sách tự cho mình là gốc. Xếp chung mới lộ ra: **một số việc chặn nhiều thứ hơn vẻ ngoài của nó, và một số việc tưởng chặn thì thực ra đã có đáp án.**

---

## 0. Trạng thái hiện tại

| Khối | Trạng thái | Bằng chứng |
|---|---|---|
| Tài liệu nguồn thị trường | ✅ Hoàn chỉnh, kiểm chứng bằng lời gọi thật | 131 endpoint, mẫu 51 mã |
| Tài liệu nguồn vĩ mô WiChart | ✅ Hoàn chỉnh + bộ tự kiểm chạy được | 87 key, 509 khẳng định |
| Tài liệu nguồn tin | ✅ Đo thật trên 307 URL, 1.408 tiêu đề | ~570 tin/ngày chưa dedupe |
| Thiết kế kho dữ liệu thị trường | ✅ Đã duyệt | chưa viết dòng code nào |
| Thiết kế pipeline tin | ✅ Đã duyệt | chưa viết dòng code nào |
| Hai skill chứng khoán | ✅ Xong, test 6 vòng, **dự án đã đóng 2026-08-14** | 3.046 dòng · [bảo trì skill](../30-skills/maintenance.md) |
| Tầng ngữ nghĩa nối dữ liệu ↔ skill | 🟡 Mới đề xuất, chưa duyệt | [chatbot-semantic-layer.md](../20-design/chatbot-semantic-layer.md) |
| **Từ điển mã trường FiinGroup** | ✅ 729 mã · tên VI/EN 98,5% · đơn vị 99,7% | [field-dictionary.json](../10-sources/market/field-dictionary.json) |
| **Chọn nguồn chuẩn cho từng chỉ tiêu** | ✅ Đã chốt | [chọn trường cho ETL thị trường](../20-design/market-field-selection.md) |
| **Giấy phép WiFeed với WiGroup** | ✅ **Đã chốt 2026-08-15** — mở khoá 87 endpoint vĩ mô/hàng hoá | chủ dự án xác nhận |
| **Repo vào git** | ✅ `git init` + commit đầu 2026-08-14 | toàn bộ docs + hai skill |
| **Toàn bộ phần cài đặt** | ❌ Chưa bắt đầu | |

## 1. Việc chặn nhiều thứ nhất — làm trước

| # | Việc | Chặn cái gì | Nguồn |
|---|---|---|---|
| **1** | **Xác nhận rate limit với FiinGroup** và dựng hạ tầng Postgres + Redis. *(Gửi kèm luôn danh sách 11 mã chỉ tiêu chưa giải mã được — xem [Phụ lục A §A.5](../10-sources/market/appendix-A-field-codes.md))* | Mọi ETL | kho dữ liệu §8 GĐ 0 |
| ~~2~~ | ~~Chốt giấy phép WiFeed với WiGroup~~ | ✅ **Đã chốt 2026-08-15** — chủ dự án xác nhận. Mở khoá toàn bộ nhánh vĩ mô/hàng hoá, 87 endpoint. Còn một việc ngỏ về endpoint/spec chính thức — xem [§5](#5-việc-còn-thật-sự-để-ngỏ) | |
| ~~3~~ | ~~Yêu cầu FiinGroup bảng ánh xạ mã chỉ tiêu BCTC~~ | ✅ **Đã tự giải quyết 2026-08-14** — 729 mã, độ phủ 100% trên response thật, lấy từ bundle JS ứng dụng FiinTrade. Kèm tên Việt/Anh (98,5%) và **đơn vị dữ liệu** (99,7%). Xem [Phụ lục A §A.5](../10-sources/market/appendix-A-field-codes.md). Còn 11 mã chưa giải mã — không chặn việc gì | |

Ba việc này đều **phụ thuộc bên ngoài**, không tự làm được, và thời gian chờ không kiểm soát được. Hai việc đã xong; **chỉ còn việc 1 đang chờ** — gửi đi trước, làm việc khác trong lúc chờ.

## 2. Việc gấp vì mất dữ liệu theo thời gian

> Xếp riêng vì chúng không chặn thứ gì, nhưng **mỗi ngày trì hoãn là một ngày mất vĩnh viễn.**

| # | Việc | Vì sao không hoãn được |
|---|---|---|
| **4** | **Ingester realtime + tích luỹ `bar_1m`** | Nến intraday **không tồn tại ở bất kỳ nguồn nào**. Mọi dữ liệu khác crawl lại lúc nào cũng được, riêng cái này không |
| **5** | **Backfill lịch sử tin** từ sitemap TinnhanhCK / BNews / NguoiQuanSat | Dữ liệu chỉ còn chừng nào họ còn giữ sitemap |

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
     └─→ [4] Ingester realtime (song song, ưu tiên cao)

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
| **Endpoint/spec chính thức của WiFeed** | Giấy phép đã chốt là cho sản phẩm **WiFeed**; toàn bộ số đo trong tài liệu hiện tại thực hiện trên endpoint nội bộ `api.wichart.vn`. Chưa xác nhận endpoint/spec chính thức của WiFeed có khác không | Hỏi WiGroup |
| **Luật bỏ boilerplate cho từng nguồn** | Phải viết riêng cho mỗi trong 10 nguồn báo. Chưa khảo sát cấu trúc trang bài | Một vòng soi tương tự vòng soi feed đã làm |
| **Chọn mô hình embedding** | Chốt **trước** khi nạp dữ liệu — embed lại toàn kho về sau rất tốn | Nhớ embed cả `summary` và `summary_ai`, giữ riêng |
| **Ngưỡng `confidence`** phân loại | Dưới bao nhiêu thì vào hàng chờ rà tay | Sau vài tuần chạy thật |
| **Trần 3.000 hay 4.000 ký tự** | | Đối chiếu `content_chars` với các ca phân loại sai |
| **Tách từ tiếng Việt** | Chỉ làm nếu có bằng chứng `simple` + `unaccent` không đủ | |
| ~~**Câu treo cuối của dự án skill**~~ | ✅ **Đã quyết 2026-08-14: giữ nguyên tên "ngân hàng"** trong luận điểm *ngành báo hiệu* — là cơ chế, không phải danh sách ngành cứng. Bảng rà `CAN-SUA.md` hết việc và đã xoá | |
| **Đoạn giới hạn phạm vi vào system prompt** | Skill không tự gác cổng được — xem [§4](architecture.md) | Làm khi dựng backend |

## 6. Ba bẫy sẽ cắn ngay ngày đầu cài đặt

Ghi lại ở đây vì chúng nằm rải trong ba file khác nhau và đều đã gặp thật:

1. **`organCode ≠ ticker` ở 41% doanh nghiệp** — gọi bằng ticker trả `HTTP 200` với dữ liệu rỗng, không báo lỗi gì.
2. **Timestamp WiChart phải parse bằng `Asia/Ho_Chi_Minh`**, không phải UTC — parse sai tạo ảo giác lệch nhãn 1 tháng trên toàn bộ chuỗi tháng.
3. **Nhãn `unit` của WiChart sai ở 15 series**, lệch 1000 lần, **rải rác ngẫu nhiên không theo quy luật** — phải dùng bảng hệ số đã hardcode.
4. **Nhãn `unit` của FiinTrade cũng không phải đơn vị dữ liệu** — `Percentage` thực ra là thập phân (`0.1821` = 18,21%), `BillionVND` thực ra là VND đầy đủ. Dùng `don_vi_du_lieu` trong [từ điển mã trường](../10-sources/market/field-dictionary.json), không dùng nhãn của API.
5. **`getScreenerItems` timeout khi gửi nhiều tiêu chí** — 79 tiêu chí thì server FiinTrade trả lỗi Redis timeout, 1 tiêu chí thì chạy ngay. Vẫn đủ 223 trường bất kể số tiêu chí.
6. **`isa20ttm` không bằng tổng 4 quý `isa20`** — lệch tới 9,4%. Screener dùng lợi nhuận cổ đông công ty mẹ, BCTC dùng lợi nhuận thuần. Đừng tự tính lại.

> Bẫy 3 và 4 là **cùng một loại lỗi trên hai nhà cung cấp khác nhau** — nhãn đơn vị do nguồn tự khai không khớp dữ liệu nguồn tự trả. Nếu thêm nguồn thứ tư, kiểm đơn vị bằng dải giá trị thật trước khi tin nhãn.

Danh sách đầy đủ: [9 bẫy triển khai](../10-sources/market/00-conventions.md) · [6 bẫy WiChart](../10-sources/macro/wichart.md) · [7 cạm bẫy nguồn tin](../10-sources/news/README.md).

**Điểm chung của cả ba nhóm bẫy:** mọi thứ nguồn tự khai về chính nó đều phải kiểm lại bằng dữ liệu.

> **Và một bài học ngược lại, cũng đắt ngang:** không phải bất thường nào cũng là lỗi của nguồn. Khi bộ phân loại đơn vị tụt từ 19/19 xuống 16/19 sau khi thêm dữ liệu Screener, kết luận đầu tiên là *"Screener dùng thang khác"* — sai. Kiểm lại bằng `valueRange` của chính API thì thấy Screener dùng đúng thang, còn nguyên nhân là **luật phân loại của mình gãy trên giá trị cực trị toàn thị trường**. Đổ lỗi cho nguồn thì dễ, và nó chặn mất việc tìm ra lỗi thật.

