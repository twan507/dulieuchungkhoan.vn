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
| Hai skill chứng khoán | ✅ Xong, test 6 vòng, đã dừng tối ưu | 3.045 dòng |
| Tầng ngữ nghĩa nối dữ liệu ↔ skill | 🟡 Mới đề xuất, chưa duyệt | [tang-ngu-nghia-chatbot.md](../20-thiet-ke/tang-ngu-nghia-chatbot.md) |
| **Từ điển mã trường FiinGroup** | ✅ 729 mã · tên VI/EN 98,5% · đơn vị 99,7% | [tu-dien-ma-field.json](../10-nguon-du-lieu/thi-truong/tu-dien-ma-field.json) |
| **Chọn nguồn chuẩn cho từng chỉ tiêu** | ✅ Đã chốt | [ADR 0002](quyet-dinh/0002-chon-nguon-du-lieu.md) |
| **Toàn bộ phần cài đặt** | ❌ Chưa bắt đầu | |

## 1. Việc chặn nhiều thứ nhất — làm trước

| # | Việc | Chặn cái gì | Nguồn |
|---|---|---|---|
| **1** | **Xác nhận rate limit với FiinGroup** và dựng hạ tầng Postgres + Redis. *(Gửi kèm luôn danh sách 11 mã chỉ tiêu chưa giải mã được — xem [Phụ lục A §A.5](../10-nguon-du-lieu/thi-truong/phu-luc-A-ma-field.md))* | Mọi ETL | kho dữ liệu §8 GĐ 0 |
| **2** | **Chốt giấy phép WiFeed** với WiGroup | Toàn bộ nhánh vĩ mô/hàng hoá — 87 endpoint | README nguồn §7 |
| ~~3~~ | ~~Yêu cầu FiinGroup bảng ánh xạ mã chỉ tiêu BCTC~~ | ✅ **Đã tự giải quyết 2026-08-14** — 729 mã, độ phủ 100% trên response thật, lấy từ bundle JS ứng dụng FiinTrade. Kèm tên Việt/Anh (98,5%) và **đơn vị dữ liệu** (99,7%). Xem [Phụ lục A §A.5](../10-nguon-du-lieu/thi-truong/phu-luc-A-ma-field.md). Còn 11 mã chưa giải mã — không chặn việc gì | |

Ba việc này đều **phụ thuộc bên ngoài**, không tự làm được, và thời gian chờ không kiểm soát được. Gửi đi trước, làm việc khác trong lúc chờ.

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

**[6] là nút thắt thật của cả hệ.** Nó xuất hiện trong kho dữ liệu như "giai đoạn 1", nhưng pipeline tin cũng phụ thuộc nó mà không biết — xem [mắt xích 3.1](kien-truc-tong-the.md). Làm xong [6] là mở khoá cả hai nhánh cùng lúc.

## 4. Việc đã có đáp án, chỉ cần áp dụng

Bốn mục đang nằm trong danh sách **"Còn để ngỏ"** của pipeline tin nhưng thực ra đã được trả lời ở khối tài liệu khác:

| Đang ghi là để ngỏ | Đáp án đã có |
|---|---|
| Danh sách ~1.600 mã niêm yết | `getListOrganization` — **1.972 cổ phiếu** (số ~1.600 là ước lượng sai). Lọc mã huỷ niêm yết bằng `getAllQuotes` |
| Bảng tên thương mại → mã | `organName` + `organShortName` trong cùng endpoint |
| Khung ngành để lọc tin | `getAllIcbIndustry` — cây ICB 4 cấp |
| Khung ngành cho skill | Cùng nguồn trên, nối theo hợp đồng ở [§3.2](kien-truc-tong-the.md) |
| Bảng ánh xạ mã chỉ tiêu BCTC | **729 mã đã giải mã** từ bundle JS FiinTrade — xem [Phụ lục A §A.5](../10-nguon-du-lieu/thi-truong/phu-luc-A-ma-field.md) |
| Đơn vị của các mã chỉ tiêu | **727/729 mã có `don_vi_du_lieu`**, 392 xác thực bằng đẳng thức kế toán |
| Lấy trường nào từ nguồn nào | [ADR 0002](quyet-dinh/0002-chon-nguon-du-lieu.md) — Screener 80/193, Snapshot 16/54, giá từ BVSC |

## 5. Việc còn thật sự để ngỏ

| Việc | Ghi chú | Chốt bằng cách nào |
|---|---|---|
| **Luật bỏ boilerplate cho từng nguồn** | Phải viết riêng cho mỗi trong 10 nguồn báo. Chưa khảo sát cấu trúc trang bài | Một vòng soi tương tự vòng soi feed đã làm |
| **Chọn mô hình embedding** | Chốt **trước** khi nạp dữ liệu — embed lại toàn kho về sau rất tốn | Nhớ embed cả `summary` và `summary_ai`, giữ riêng |
| **Ngưỡng `confidence`** phân loại | Dưới bao nhiêu thì vào hàng chờ rà tay | Sau vài tuần chạy thật |
| **Trần 3.000 hay 4.000 ký tự** | | Đối chiếu `content_chars` với các ca phân loại sai |
| **Tách từ tiếng Việt** | Chỉ làm nếu có bằng chứng `simple` + `unaccent` không đủ | |
| **`CAN-SUA.md` mục A9** | Giữ tên "ngân hàng" trong luận điểm *ngành báo hiệu*, đổi thành "nhóm tài chính", hay bỏ hẳn | Cần bạn quyết |
| **Đoạn giới hạn phạm vi vào system prompt** | Skill không tự gác cổng được — xem [§4](kien-truc-tong-the.md) | Làm khi dựng backend |

## 6. Ba bẫy sẽ cắn ngay ngày đầu cài đặt

Ghi lại ở đây vì chúng nằm rải trong ba file khác nhau và đều đã gặp thật:

1. **`organCode ≠ ticker` ở 41% doanh nghiệp** — gọi bằng ticker trả `HTTP 200` với dữ liệu rỗng, không báo lỗi gì.
2. **Timestamp WiChart phải parse bằng `Asia/Ho_Chi_Minh`**, không phải UTC — parse sai tạo ảo giác lệch nhãn 1 tháng trên toàn bộ chuỗi tháng.
3. **Nhãn `unit` của WiChart sai ở 15 series**, lệch 1000 lần, **rải rác ngẫu nhiên không theo quy luật** — phải dùng bảng hệ số đã hardcode.
4. **Nhãn `unit` của FiinTrade cũng không phải đơn vị dữ liệu** — `Percentage` thực ra là thập phân (`0.1821` = 18,21%), `BillionVND` thực ra là VND đầy đủ. Dùng `don_vi_du_lieu` trong [từ điển mã trường](../10-nguon-du-lieu/thi-truong/tu-dien-ma-field.json), không dùng nhãn của API.
5. **`getScreenerItems` timeout khi gửi nhiều tiêu chí** — 79 tiêu chí thì server FiinTrade trả lỗi Redis timeout, 1 tiêu chí thì chạy ngay. Vẫn đủ 223 trường bất kể số tiêu chí.
6. **`isa20ttm` không bằng tổng 4 quý `isa20`** — lệch tới 9,4%. Screener dùng lợi nhuận cổ đông công ty mẹ, BCTC dùng lợi nhuận thuần. Đừng tự tính lại.

> Bẫy 3 và 4 là **cùng một loại lỗi trên hai nhà cung cấp khác nhau** — nhãn đơn vị do nguồn tự khai không khớp dữ liệu nguồn tự trả. Nếu thêm nguồn thứ tư, kiểm đơn vị bằng dải giá trị thật trước khi tin nhãn.

Danh sách đầy đủ: [9 bẫy triển khai](../10-nguon-du-lieu/thi-truong/00-quy-uoc-chung.md) · [6 bẫy WiChart](../10-nguon-du-lieu/vi-mo-hang-hoa/wichart.md) · [7 cạm bẫy nguồn tin](../10-nguon-du-lieu/tin-tuc/README.md).

**Điểm chung của cả ba nhóm bẫy:** mọi thứ nguồn tự khai về chính nó đều phải kiểm lại bằng dữ liệu.

> **Và một bài học ngược lại, cũng đắt ngang:** không phải bất thường nào cũng là lỗi của nguồn. Khi bộ phân loại đơn vị tụt từ 19/19 xuống 16/19 sau khi thêm dữ liệu Screener, kết luận đầu tiên là *"Screener dùng thang khác"* — sai. Kiểm lại bằng `valueRange` của chính API thì thấy Screener dùng đúng thang, còn nguyên nhân là **luật phân loại của mình gãy trên giá trị cực trị toàn thị trường**. Đổ lỗi cho nguồn thì dễ, và nó chặn mất việc tìm ra lỗi thật.

---

## 7. Bàn giao phiên 2026-08-14

Phiên này làm ba việc, không viết dòng code nào.

### Việc 1 — Hệ thống hoá kho tài liệu

Ba thư mục rời (`bvsc-api-docs`, `nguon_tin_chung_khoan`, `chuyen_gia_chung_khoan`) gộp thành cấu trúc bốn tầng theo vai trò tài liệu. Chi tiết và lý do: [ADR 0001](quyet-dinh/0001-cau-truc-kho-tai-lieu.md).

Ba mắt xích vốn treo hai đầu nay nối được: danh sách mã niêm yết cho pipeline tin, cây ngành ICB cho skill, hợp đồng function calling ↔ skill.

### Việc 2 — Từ điển mã trường FiinGroup

**729 mã** giải mã đầy đủ. Trước phiên này tài liệu ghi *"chưa có nguồn giải mã công khai"*.

| | Kết quả |
|---|---|
| Tên tiếng Việt / Anh | 718/729 (98,5%) |
| Đơn vị dữ liệu | 727/729 (99,7%) — **392 xác thực** bằng đẳng thức kế toán |
| Chưa giải mã | 11 mã, không nằm trong ba báo cáo chính |

Nguồn: bundle JS của ứng dụng FiinTrade, **không phải API**. Hash đổi mỗi lần họ deploy — đọc `<script src>` để lấy tên file hiện hành.

Phát hiện quan trọng nhất: **nhãn `unit` của API không phải đơn vị dữ liệu**. `Percentage` thực ra là thập phân, `BillionVND` thực ra là VND. Đây là cùng loại lỗi với bẫy WiChart đã biết, chỉ khác nhà cung cấp.

### Việc 3 — Chốt nguồn chuẩn cho từng chỉ tiêu

Screener 193 → **80** trường · Snapshot 54 → **16** · giá và chỉ báo kỹ thuật chuyển sang **BVSC** · bỏ hẳn nhóm chấm điểm · giữ MoneyFlow cho tự doanh và đóng góp chỉ số. Chi tiết: [ADR 0002](quyet-dinh/0002-chon-nguon-du-lieu.md).

### Ba việc còn treo, cần người quyết

| Việc | Ai quyết | Chặn gì |
|---|---|---|
| **Giấy phép WiFeed** với WiGroup | Bên ngoài | 87 endpoint vĩ mô/hàng hoá |
| **Rate limit** với FiinGroup — gửi kèm danh sách 11 mã chưa giải | Bên ngoài | Mọi ETL |
| **`CAN-SUA.md` mục A9** — giữ hay bỏ tên "ngân hàng" trong luận điểm *ngành báo hiệu* | Chủ dự án | Không chặn gì, nhưng là câu treo cuối của dự án skill |

Và một tài liệu chờ duyệt: [tầng ngữ nghĩa cho chatbot](../20-thiet-ke/tang-ngu-nghia-chatbot.md) — phần duy nhất trong kho chưa qua kiểm chứng thực tế.

### Việc làm được ngay, không chờ ai

1. **`git init`** — repo chưa có git, mọi thay đổi tới giờ không hoàn tác được
2. **Dựng Ingester** để bắt đầu tích luỹ nến 1 phút — mỗi ngày trì hoãn là một ngày mất vĩnh viễn
3. **Khảo sát cấu trúc trang bài của 10 nguồn tin** để viết luật bỏ boilerplate — việc chặn nhiều thứ nhất trong nhánh tin

### Bài học phương pháp, đáng giữ

**Mọi thứ nguồn tự khai về chính nó đều phải kiểm lại bằng dữ liệu.** Đã bắt được 22 cạm bẫy thật trên ba nguồn, cộng thêm ba cái mới trong phiên này.

**Nhưng không phải bất thường nào cũng là lỗi của nguồn.** Khi bộ phân loại đơn vị tụt từ 19/19 xuống 16/19, kết luận đầu tiên là *"Screener dùng thang khác"* — sai. Nguyên nhân thật là luật phân loại của mình gãy trên giá trị cực trị. Đổ lỗi cho nguồn thì dễ và nó chặn mất việc tìm ra lỗi thật.

**Phép kiểm tốt vừa xác nhận vừa bắt lỗi.** Kiểm nhất quán thang không chỉ xác thực 390 mã mà còn tìm ra ba mã từ điển ghi sai đơn vị. Bảy phép kiểm đẳng thức kế toán đã đưa vào [bộ giám sát hợp đồng](../20-thiet-ke/kho-du-lieu-thi-truong.md) để chạy hằng ngày.
