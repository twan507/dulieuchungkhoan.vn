# Rà soát nguồn cũ — kết quả: KHÔNG còn chỗ nào bỏ sót · 2026-08-15

Rà `docs/10-sources/` và `docs/00-overview/roadmap.md` tìm chỗ tài liệu tự khai là chưa khám phá, kiểu ETF/Quỹ vừa mở ra được.

## 0. Kết luận

**Không còn mục nào bị bỏ quên.** Danh sách *"Ngoài phạm vi"* đã được rà hết: phần chưa mở đều là **quyết định loại có chủ đích của chủ dự án**, không phải sơ suất.

## 1. Danh sách "Ngoài phạm vi" — trạng thái đầy đủ

`10-sources/README.md:49` liệt 10 mục:

| Mục | Trạng thái |
|---|---|
| Phái sinh | ✅ **Đã mở** — 14 hợp đồng, 9 năm lịch sử qua FiinTrade |
| ETF/Quỹ | ✅ **Đã mở** — 31 mã niêm yết + `iNav` cho 6 mã |
| Cổ phiếu và chỉ số quốc tế | ✅ **Đã mở** — 36 chỉ số/21 nước qua Yahoo |
| Crypto | ✅ **Đã mở** — 10 đồng lớn qua Binance |
| NAV quỹ mở | ✅ **Đã kiểm — không nguồn nào có.** Giữ ngoài phạm vi, có lý do đo được |
| **Chứng quyền** | ⛔ **LOẠI CÓ CHỦ ĐÍCH** — chủ dự án: không có tác dụng cho phân tích |
| **Lô lẻ** | ⛔ **LOẠI CÓ CHỦ ĐÍCH** — như trên |
| **Trái phiếu** | ⛔ **LOẠI CÓ CHỦ ĐÍCH** — như trên |
| **Realtime FiinTrade (SignalR)** | ⛔ **LOẠI CÓ CHỦ ĐÍCH** — đã chốt dùng realtime của **BVSC** |
| Luồng cần đăng nhập | ⛔ Loại có chủ đích — cần tài khoản, không phải dữ liệu thị trường |

## 2. ⛔ Bốn mục loại có chủ đích — GHI RÕ ĐỂ KHÔNG AI MỞ LẠI

**Chỉ thị chủ dự án 2026-08-15, nguyên văn tinh thần:** *"chứng quyền, lô lẻ và trái phiếu tôi chủ động bỏ qua vì nó không có tác dụng cho phân tích, note lại không dùng nhé; realtime FiinTrade cũng không dùng vì dùng của BVSC, cái đó cũng đã chốt rồi."*

| Mục | Quyết định | Lý do |
|---|---|---|
| **Chứng quyền** *(342 mã)* | **Không dùng** | Không phục vụ phương pháp phân tích của dự án |
| **Lô lẻ** *(1.890 mã)* | **Không dùng** | nt |
| **Trái phiếu** *(187 mã)* | **Không dùng** | nt |
| **Realtime FiinTrade (SignalR)** | **Không dùng** | Đã chốt dùng realtime **BVSC** — không dựng hai kênh realtime song song |

⚠️ **Ba mục đầu KHÔNG phải "không có dữ liệu".** Controller có gọi thử trong lúc rà và cả ba đều trả dữ liệu đầy đủ. **Loại vì không có giá trị phân tích, không phải vì thiếu nguồn** — ghi rõ để lần sau không ai tưởng là chỗ bỏ sót rồi đi khám phá lại.

## 3. 🔴 Bài học về cách viết tài liệu

Danh sách *"Ngoài phạm vi"* hiện tại chỉ liệt **tên mục, không có lý do**:

> *Chứng quyền · Lô lẻ · Phái sinh · Trái phiếu · ETF/Quỹ · … · NAV quỹ mở.*

Chính vì thiếu lý do mà trong đợt này controller đã **tốn công mở lại ba mục vốn đã bị loại có chủ đích**, và trước đó suýt bỏ qua hai mục *thật sự* đáng mở (Phái sinh, ETF).

➜ **Khi viết tài liệu, mỗi mục ngoài phạm vi phải kèm lý do, và phân biệt ba loại:**

| Loại | Nghĩa | Ví dụ |
|---|---|---|
| **Loại có chủ đích** | Có dữ liệu, nhưng không phục vụ phân tích | Chứng quyền · Lô lẻ · Trái phiếu |
| **Đã có đường khác** | Có dữ liệu, nhưng đã chọn nguồn khác | Realtime FiinTrade *(dùng BVSC)* |
| **Đã kiểm — không có** | Đã đi tìm và xác nhận không nguồn nào có | NAV quỹ mở |

Ba loại này trông giống nhau trong danh sách hiện tại, nhưng **hàm ý hoàn toàn khác nhau** khi ai đó rà lại về sau.

## 4. Các mục "để ngỏ" khác — không phải khám phá nguồn

Rà `roadmap.md §5` và `00-conventions.md §10`: phần còn lại không thuộc loại *"có dữ liệu mà chưa nhìn"*.

| Nhóm | Mục | Vì sao không thuộc phiên này |
|---|---|---|
| **Quyết định thiết kế** | Chọn mô hình embedding · ngưỡng `confidence` · trần 3.000/4.000 ký tự · tách từ tiếng Việt · đoạn giới hạn phạm vi vào system prompt | Là lựa chọn khi dựng, không phải khám phá nguồn |
| **Đo tải** | Nhịp **8 luồng** ETL · trần **2 request/giây** backfill · hai nhóm lớn nhất của lịch ngày | Chỉ đo được khi có ETL thật, và đúng nguyên tắc **không dò trần** |
| **Chi tiết lẻ tầng reference** | `Screener/DownloadScreenerItems` chưa thử · `rtd35` vs `rtd19` khác nhau ở đâu · `rtd39`/`rtd54` có thật nhưng chưa có tên | Nhỏ, không chặn |
| **Mẫu tin còn thiếu** | BáoChínhPhủ mục chỉ đạo điều hành · TinnhanhCK 3 trang chuyên mục · 3 chỗ chưa bỏ được bằng selector · dạng longform/video/bài cũ | Đã ghi trong `article-structure.md §4`, thuộc vòng soi tin |

## 5. Trạng thái độ rộng nguồn — chốt

Mục *"Ngoài phạm vi"* từ 10 mục nay phân rã hết:
- **4 mục đã mở** và có nguồn thật *(phái sinh · ETF/quỹ · chỉ số quốc tế · crypto)*
- **5 mục loại có chủ đích** *(chứng quyền · lô lẻ · trái phiếu · realtime FiinTrade · luồng đăng nhập)*
- **1 mục đã kiểm, xác nhận không nguồn nào có** *(NAV quỹ mở)*

**Không còn mục nào chưa có câu trả lời. Đủ độ rộng và độ sâu để khép phiên khảo sát nguồn.**
