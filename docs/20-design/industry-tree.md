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

*(Bộ code và tên rà lại toàn diện 2026-08-27 khi lát ngành thật — xem cuối mục.)*

| Code | Tên | Thuộc nhóm |
|---|---|---|
| NGANHANG | Ngân hàng và Tín dụng | TAICHINH |
| CHUNGKHOAN | Công ty Chứng khoán | TAICHINH |
| BAOHIEM | Kinh doanh Bảo hiểm | TAICHINH |
| DANDUNG | Bất động sản Dân dụng | BATDONGSAN |
| KHUCONGNGHIEP | Bất động sản Khu công nghiệp | BATDONGSAN |
| XAYDUNG | Thi công Xây dựng | BATDONGSAN |
| VATLIEU | Vật liệu Xây dựng | BATDONGSAN |
| KIMLOAI | Kim loại Công nghiệp | SANXUAT |
| KHOANGSAN | Than và Khoáng sản | SANXUAT |
| HOACHAT | Hóa chất và Phân bón | SANXUAT |
| NHUA | Nhựa, Bao bì và Giấy | SANXUAT |
| THIETBI | Thiết bị Điện và Máy móc | SANXUAT |
| NONGNGHIEP | Nông nghiệp và Chăn nuôi | XUATKHAU |
| THUYSAN | Chế biến Thủy sản | XUATKHAU |
| DETMAY | Dệt may, Gỗ và Gia dụng | XUATKHAU |
| CAOSU | Cao su và Săm lốp | XUATKHAU |
| BANLE | Bán buôn và Bán lẻ | TIEUDUNG |
| THUCPHAM | Thực phẩm và Đồ uống | TIEUDUNG |
| DULICH | Hàng không, Du lịch và Truyền thông | TIEUDUNG |
| YTE | Y tế, Giáo dục và Xuất bản | TIEUDUNG |
| TIENICH | Điện, Nước và Môi trường | NANGLUONG |
| DAUKHI | Dầu mỏ và Khí đốt | NANGLUONG |
| VANTAI | Vận tải, Cảng biển và Kho bãi | NANGLUONG |
| CONGNGHE | Công nghệ Thông tin và Viễn thông | NANGLUONG |

### Rà lại 2026-08-27 — 6 code và 7 tên đổi

Khi lát ngành thật *(hồ sơ: [plans/2026-08-27-industry-two-layer-mapping/](../90-records/plans/2026-08-27-industry-two-layer-mapping/))*, đối chiếu 24 ngành với nội dung ICB thật lộ ra hai loại lệch: **code viết tắt lạc phong cách** và **code ghép hai khái niệm** — đều phạm luật 5 ở §3.

| Code cũ → mới | Vì sao |
|---|---|
| `BDS` → **`DANDUNG`** · `KCN` → **`KHUCONGNGHIEP`** · `VLXD` → **`VATLIEU`** | Bỏ viết tắt — cả bộ còn lại viết đầy đủ (`BATDONGSAN`, `CHUNGKHOAN`, `NONGNGHIEP`) |
| `YTEGD` → **`YTE`** · `DIENNUOC` → **`TIENICH`** | Bỏ ghép hai khái niệm (Y Tế + Giáo Dục, Điện + Nước) |
| `TAINGUYEN` → **`KHOANGSAN`** | `TAINGUYEN` mượn nhãn nhóm cấp 2 của ICB, mà nhóm đó gồm cả kim loại và giấy — hai thứ nay ở ngành khác |

| Tên đổi | Vì sao |
|---|---|
| Dược phẩm, Y tế và Giáo dục → **Y tế, Giáo dục và Xuất bản** | "Y tế" đã bao dược phẩm — đúng cách ICB gộp (`4570` và `4530` cùng nhóm *Y tế*); thêm "Xuất bản" để đón `5557` sách giáo khoa |
| Hàng không, Du lịch và Giải trí → **Hàng không, Du lịch và Truyền thông** | Thành viên `5755` "Dịch vụ giải trí" thật ra là công viên và resort — "Du lịch" đã bao; chỗ trống dành cho `5553`/`5555` truyền thông |
| Điện, Nước và Khí đốt → **Điện, Nước và Môi trường** | `7573` khí đốt đã chuyển sang DAUKHI; ngành nay có 29 mã môi trường đô thị mà tên không nhắc |
| Dầu khí và Nhiên liệu → **Dầu mỏ và Khí đốt** | Sau khi nhận `7573`, nhóm khí chiếm phần lớn mà tên không nói ra |
| Tài nguyên Cơ bản → **Than và Khoáng sản** | Tên cũ rộng hơn nội dung thật (chỉ khai khoáng + than + vàng) |
| Nhựa và Bao bì → **Nhựa, Bao bì và Giấy** | Ngành ôm `1737` Sản xuất giấy — 8 mã không được tên nhắc |
| Dệt may và Gia dụng → **Dệt may, Gỗ và Gia dụng** | "Gia dụng" không gợi tới gỗ, mà ngành có 12 mã `1733` Lâm sản và Chế biến gỗ |

🔴 **Luật mới kèm theo — ba ngành tài chính khoá theo mẫu BCTC.** `NGANHANG`, `CHUNGKHOAN`, `BAOHIEM` không phải ba ngành như 21 ngành kia mà là ba **biểu mẫu báo cáo tài chính**. Ràng buộc hai chiều: `issuer.com_type_code = NH` ⟺ `NGANHANG`, `CK` ⟺ `CHUNGKHOAN`, `BH` ⟺ `BAOHIEM`, không ngoại lệ. Cây 24 ngành **không có ô cho holding đầu tư phi ngân hàng** — 7 mã `CT` như OGC, TVC, F88, DCV nằm nhờ ở `DANDUNG`/`BANLE`/`CONGNGHE`, là vùng xám đã biết. Chi tiết và test nghiệm thu: [spec §2b](../90-records/plans/2026-08-27-industry-two-layer-mapping/spec.md).

**Đổi so với bộ 24 tên gốc của chủ dự án** *(để truy vết, không phải để dùng)*: code gốc là `BDS` `KCN` `VLXD` `CONGNGHIEP` `KHOANGSAN` `TIENICH` `YTEGD` — nay `CONGNGHIEP` → `THIETBI`, còn `KHOANGSAN` và `TIENICH` **quay lại đúng code gốc** nhưng mang tên khác. Tên gốc đổi nhiều nhất: "Bán lẻ Tiêu dùng" → "Bán buôn và Bán lẻ", "Dệt may Xuất khẩu" → "Dệt may, Gỗ và Gia dụng", "Dịch vụ Dầu khí" → "Dầu mỏ và Khí đốt", "Tài chính ngân hàng" → "Ngân hàng và Tín dụng", "Hạ tầng Tiện ích" → "Điện, Nước và Môi trường", "Y tế Giáo dục" → "Y tế, Giáo dục và Xuất bản", "Du lịch Giải trí" → "Hàng không, Du lịch và Truyền thông", "Vận tải Kho bãi" → "Vận tải, Cảng biển và Kho bãi".

## 3. Quy tắc đặt tên — áp khi thêm hay sửa ngành

1. **Tên dài 2–4 cụm nghĩa** ("bất động sản" đếm là một cụm). Liên từ và dấu phẩy không tính vào ngân sách.
2. **Tên là liệt kê thì phải có liên từ:** 2 vế dùng "và" (*Hóa chất và Phân bón*), 3 vế dùng "A, B và C" (*Điện, Nước và Môi trường*). Cụm khái niệm/bổ nghĩa không chèn liên từ (*Thi công Xây dựng*, *Tài chính Ngân hàng* — chèn "và" là hỏng nghĩa).
3. **Tên cấp 1 phải tổng quát** — khái niệm bao trùm, không phải phép cộng tên con.
4. **Không cặp cha-con nào trùng cụm từ** (đây là lý do NGANHANG không tên "Tài chính Ngân hàng" dưới cha "Dịch vụ Tài chính"). Trùng giữa hai nhánh khác cha chấp nhận được.
5. **Code một khái niệm lõi của tên**, viết hoa không dấu, hai cấp chung phong cách, không code nào trùng nhau.
6. **Viết hoa chữ cái đầu mỗi cụm** (*Kim loại Công nghiệp*, không phải *Kim loại công nghiệp*).

## 4. Nguyên tắc gán ngành cho mã

- **Ngành gán ở doanh nghiệp (issuer), mã thừa hưởng** — một doanh nghiệp một ngành theo hoạt động chính, chuẩn GICS/ICB. ETF và chỉ số không có ngành *(luật bước 2)*.
- **Holding đa ngành** (GEX, ASM, BCG…) xếp theo mảng đóng góp lợi nhuận chính; vùng xám là tất yếu, cơ chế **gán tay thắng máy** của bước 2 xử lý dần.
- Gán hàng loạt bằng `industry_icb_map` — nội dung ở [industry-mapping.md](industry-mapping.md). **Trộn hai cấp ICB có chủ đích**: 40 dòng cấp 3 làm nền cho cả nhánh, cộng 16 dòng cấp 4 cho những nhánh chứa từ hai ngành riêng trở lên — con số THIẾT KẾ ở worksheet [industry-mapping.md](industry-mapping.md); DB thật nạp qua migration `0013` chỉ **39 dòng cấp 3 + 16 dòng cấp 4 = 55 dòng** (đo 2026-08-28), vì dòng `8980` "Quỹ đầu tư" cố ý không nạp — xem `market.industry_icb_map` **55 dòng** ở [database/README.md](../../database/README.md). Luật phân giải *(DDL 0002)*: khớp `icb_code` chính xác trước, không có thì leo `icb_code_path` lấy tổ tiên gần nhất — nên dòng cấp 4 **thắng** dòng cấp 3 cùng nhánh, còn dòng cấp 3 đón cả mã ICB lá mới chưa từng thấy. Nhờ đó 24 ngành phủ **1.526/1.526** cổ phiếu có doanh nghiệp *(đo 2026-08-27)*. Tái xác nhận trên DB thật 2026-08-28 sau khi migration `0013` nạp: hai bất biến `A=0` (không doanh nghiệp nào có cổ phiếu `listed` mà thiếu ngành) và `E=none` (không ngành nào trống mã) đều đạt — xem [ledger](../90-records/plans/2026-08-27-industry-two-layer-mapping/ledger.md).
- **Ai ghi cột nào:** lớp 1 (máy) ở `market.issuer.industry_id` — job `etl refdata` ghi đè mỗi lượt theo `industry_icb_map`; lớp 2 (tay) ở `market.issuer_industry_override`, ETL không đọc không ghi (DB đã thu hồi quyền ghi của role `dlck_etl`). **Đường đọc duy nhất là view `market.v_issuer_industry`** = `COALESCE(tay, máy)` kèm cột `source` ∈ `manual` | `icb` | `NULL` — đọc thẳng `issuer.industry_id` là bỏ qua lớp tay.
- 🔴 **Cổ phiếu không có issuer thì không gán ngành** — xem §5.

## 5. Bốn điểm mở cấp mã — đã đóng 2026-08-27

*(Ghi 2026-08-25 từ phiên rà soát bộ ngành; đóng khi lát ngành thật.)*

| Điểm mở 2026-08-25 | Kết quả sau khi đo |
|---|---|
| Nhóm gỗ nội thất (TTF, ACG, GDT, SAV) đang ở BANLE | ✅ **Lớp 1 tự giải** — ICB `1733` Lâm sản & Chế biến gỗ → DETMAY, GDT ở `3726` → DETMAY. Không cần gán tay |
| VEF đang ở DULICH | ✅ **Lớp 1 tự giải** — ICB xếp VEF vào `8633` Bất động sản → DANDUNG |
| IPA đang ở DIENNUOC *(mã cũ, nay TIENICH)* | ✅ **Cần lớp 2** — ICB xếp `2791` Tư vấn → XAYDUNG; đè sang DANDUNG *(không được vào CHUNGKHOAN vì luật BCTC — `com_type_code = CT`)* |
| TRC, DRI cùng CAOSU với nhóm săm lốp — lo hai nửa triệt tiêu nhau | 🔴 **Tiền đề sai.** §5 giả định CAOSU có 5 mã (2 thiên nhiên, 3 săm lốp). Đo thật: **11 mã cao su thiên nhiên vs 4 mã săm lốp** — thiên nhiên áp đảo, chỉ số bám giá cao su chứ không tự triệt tiêu. **Không dời sang NONGNGHIEP.** Riêng DPR, GVR, PHR chuyển sang KHUCONGNGHIEP vì nay ăn theo sóng chuyển đổi đất KCN |

Bảng map đầy đủ — **56 dòng lớp 1 + 161 dòng lớp 2**, kèm lý do từng mã — nằm ở [industry-mapping.md](industry-mapping.md), **chủ sở hữu duy nhất** của nội dung map. Quá trình rà và các phương án đã loại: [sổ rà lớp 2](../90-records/plans/2026-08-27-industry-two-layer-mapping/layer2-review.md).

🔴 **Cổ phiếu không có issuer thì không gán ngành.** 437 mã trong kho không có doanh nghiệp tương ứng; kiểm danh tính cho thấy chúng **đã huỷ niêm yết** (Habubank, Bibica, Đường Biên Hòa, Tường An, PVFinance…). Ngành gán ở doanh nghiệp nên không có chỗ để gắn — để trống, không phải lỗi. Chi tiết: [spec §7b–7c](../90-records/plans/2026-08-27-industry-two-layer-mapping/spec.md). Tập này **tự nở theo thời gian** (438 mã tính tới 2026-08-28) vì job danh bạ chưa có luật lật `delisted` cho chiều *có trong bảng giá mà vắng khỏi danh bạ* — luật và ba ràng buộc khi cài: [market-data-store §4.4](market-data-store.md).
