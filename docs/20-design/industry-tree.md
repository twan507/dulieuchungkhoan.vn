# Cây ngành riêng — 6 nhóm × 24 ngành

**Trạng thái:** ✅ chốt 2026-08-25, chủ dự án duyệt từng vòng (nhóm → tên → liên từ → code) trong phiên brainstorm bước 2 của spec PostgreSQL. File này là **chủ sở hữu nội dung cây ngành** — schema chứa nó ở `market.industry` ([step-02](../90-records/plans/2026-08-25-postgres-data-schema/step-02-market-identity.md)), mọi tài liệu khác trỏ về đây, không chép bản thứ hai.

## 1. Vai trò và ranh giới

- **Bộ ngành riêng là chuẩn duy nhất khi hiển thị và phân tích.** ICB chỉ giữ ba vai trò tham khảo: nạp nhanh qua `industry_icb_map`, tự gán mã mới niêm yết, đối chiếu khi nghi gán sai *(luật nghiệp vụ bước 2)*.
- **Level 1 chỉ phục vụ điều hướng web.** Chỉ số phân tích (dòng tiền, breadth, xếp hạng ngành) đọc ở level 2 — cấp có "sóng ngành" thật của thị trường Việt Nam (sóng ngân hàng, sóng thép…). Không tính chỉ số tổng hợp ở level 1.
- **Không đóng bậc *dẫn dắt / lan toả / phòng thủ* vào cây.** Xếp bậc là kết quả chạy của skill lúc trả lời — chấm 4 thành phần rủi ro rồi chia dải làm ba *(hợp đồng [architecture §3.2](../00-overview/architecture.md); phương pháp chấm ở [portfolio-and-rotation.md](../../backend/agent/skills/vn-stock-knowledge/references/portfolio-and-rotation.md))*. Cây chỉ cấp khung và mã ngành.

## 2. Cây ngành

Phân bố ngành con: 3 · 4 · 5 · 4 · 4 · 4. Đều tuyệt đối 4-4-4-4-4-4 đã cân nhắc và bỏ — ép được thì phải ghép khiên cưỡng.

### Level 1 — 6 nhóm

| Code | Tên |
|---|---|
| TAICHINH | Dịch vụ Tài chính |
| BATDONGSAN | Bất động sản và Xây dựng |
| SANXUAT | Sản xuất Công nghiệp |
| XUATKHAU | Xuất khẩu Chủ lực |
| TIEUDUNG | Tiêu dùng Đời sống |
| NANGLUONG | Năng lượng và Hạ tầng |

### Level 2 — 24 ngành

| Code | Tên | Thuộc nhóm |
|---|---|---|
| NGANHANG | Ngân hàng và Tín dụng | TAICHINH |
| CHUNGKHOAN | Công ty Chứng khoán | TAICHINH |
| BAOHIEM | Kinh doanh Bảo hiểm | TAICHINH |
| BDS | Bất động sản Dân dụng | BATDONGSAN |
| KCN | Bất động sản Khu công nghiệp | BATDONGSAN |
| XAYDUNG | Thi công Xây dựng | BATDONGSAN |
| VLXD | Vật liệu Xây dựng | BATDONGSAN |
| KIMLOAI | Kim loại Công nghiệp | SANXUAT |
| TAINGUYEN | Tài nguyên Cơ bản | SANXUAT |
| HOACHAT | Hóa chất và Phân bón | SANXUAT |
| NHUA | Nhựa và Bao bì | SANXUAT |
| THIETBI | Thiết bị Điện và Máy móc | SANXUAT |
| NONGNGHIEP | Nông nghiệp và Chăn nuôi | XUATKHAU |
| THUYSAN | Chế biến Thủy sản | XUATKHAU |
| DETMAY | Dệt may và Gia dụng | XUATKHAU |
| CAOSU | Cao su và Săm lốp | XUATKHAU |
| BANLE | Bán buôn và Bán lẻ | TIEUDUNG |
| THUCPHAM | Thực phẩm và Đồ uống | TIEUDUNG |
| DULICH | Hàng không, Du lịch và Giải trí | TIEUDUNG |
| YTEGD | Dược phẩm, Y tế và Giáo dục | TIEUDUNG |
| DIENNUOC | Điện, Nước và Khí đốt | NANGLUONG |
| DAUKHI | Dầu khí và Nhiên liệu | NANGLUONG |
| VANTAI | Vận tải, Cảng biển và Kho bãi | NANGLUONG |
| CONGNGHE | Công nghệ Thông tin và Viễn thông | NANGLUONG |

**Đổi so với bộ 24 tên gốc của chủ dự án** *(để truy vết, không phải để dùng — tên chuẩn là bảng trên)*: bộ code gốc giữ nguyên trừ CONGNGHIEP → THIETBI, TIENICH → DIENNUOC, KHOANGSAN → TAINGUYEN; các tên đổi nhiều nhất là "Bán lẻ Tiêu dùng" → "Bán buôn và Bán lẻ", "Dệt may Xuất khẩu" → "Dệt may và Gia dụng", "Dịch vụ Dầu khí" → "Dầu khí và Nhiên liệu", "Tài chính ngân hàng" → "Ngân hàng và Tín dụng", "Thiết bị Công nghiệp" → "Thiết bị Điện và Máy móc", "Hạ tầng Tiện ích" → "Điện, Nước và Khí đốt", "Y tế Giáo dục" → "Dược phẩm, Y tế và Giáo dục", "Du lịch Giải trí" → "Hàng không, Du lịch và Giải trí", "Vận tải Kho bãi" → "Vận tải, Cảng biển và Kho bãi", "Công nghệ Viễn thông" → "Công nghệ Thông tin và Viễn thông".

## 3. Quy tắc đặt tên — áp khi thêm hay sửa ngành

1. **Tên dài 2–4 cụm nghĩa** ("bất động sản" đếm là một cụm). Liên từ và dấu phẩy không tính vào ngân sách.
2. **Tên là liệt kê thì phải có liên từ:** 2 vế dùng "và" (*Hóa chất và Phân bón*), 3 vế dùng "A, B và C" (*Điện, Nước và Khí đốt*). Cụm khái niệm/bổ nghĩa không chèn liên từ (*Thi công Xây dựng*, *Tài chính Ngân hàng* — chèn "và" là hỏng nghĩa).
3. **Tên cấp 1 phải tổng quát** — khái niệm bao trùm, không phải phép cộng tên con.
4. **Không cặp cha-con nào trùng cụm từ** (đây là lý do NGANHANG không tên "Tài chính Ngân hàng" dưới cha "Dịch vụ Tài chính"). Trùng giữa hai nhánh khác cha chấp nhận được.
5. **Code một khái niệm lõi của tên**, viết hoa không dấu, hai cấp chung phong cách, không code nào trùng nhau.
6. **Viết hoa chữ cái đầu mỗi cụm** (*Kim loại Công nghiệp*, không phải *Kim loại công nghiệp*).

## 4. Nguyên tắc gán ngành cho mã

- **Ngành gán ở doanh nghiệp (issuer), mã thừa hưởng** — một doanh nghiệp một ngành theo hoạt động chính, chuẩn GICS/ICB. ETF và chỉ số không có ngành *(luật bước 2)*.
- **Holding đa ngành** (GEX, ASM, BCG…) xếp theo mảng đóng góp lợi nhuận chính; vùng xám là tất yếu, cơ chế **gán tay thắng máy** của bước 2 xử lý dần.
- Gán hàng loạt bằng `industry_icb_map` (mỗi nhánh ICB map một lần về một ngành riêng) — nhờ đó 24 ngành phủ 100% mã niêm yết dù không ai gán tay từng mã.

## 5. Điểm mở cấp mã — chưa quyết, xử khi nạp dữ liệu thật

*(Ghi 2026-08-25, từ phiên rà soát bộ ngành. Đây là việc gán từng mã, không ảnh hưởng cấu trúc cây.)*

| Điểm | Hiện trạng | Hướng cân nhắc |
|---|---|---|
| TRC, DRI (cao su thiên nhiên) nằm cùng CAOSU với nhóm săm lốp (CSM, DRC, SRC) | Hai nửa **ngược chiều giá cao su** trong một ngành 5 mã — chỉ số dòng tiền ngành tự triệt tiêu | Dời TRC, DRI sang NONGNGHIEP |
| Nhóm gỗ nội thất xuất khẩu (TTF, ACG, GDT, SAV) đang ở BANLE | Hồ sơ rủi ro giống hàng xuất khẩu (đơn hàng Mỹ, tỷ giá) hơn bán lẻ nội địa | Dời sang DETMAY — tên mới "Dệt may và Gia dụng" đón vừa khít nhóm này |
| IPA đang ở DIENNUOC | Bản chất là holding tài chính (công ty mẹ của VND) | Xét lại khi gán tay |
| VEF đang ở DULICH | Bản chất hiện tại là bất động sản dự án | Xét lại khi gán tay |
