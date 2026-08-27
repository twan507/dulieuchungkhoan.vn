# Sổ rà lớp 2 — gán tay đè lên lớp 1

**Trạng thái: đang rà, CHƯA CHỐT GÌ.** Mọi dòng dưới đây là *ứng viên*, không phải quyết định.

Ba nguồn ứng viên:

| Nguồn | Nghĩa |
|---|---|
| **Lớp 1** | ICB tự gán qua `industry_icb_map` — nền để so |
| **Claude** | tôi suy từ tên doanh nghiệp khi dựng worksheet 2026-08-27 |
| **Chủ dự án** | danh sách 712 mã đã phân tay của hệ thống cũ |

🔴 **Luật lọc:** mã nào cả ba cùng một ngành thì KHÔNG vào lớp 2 — 485/712 mã của danh sách cũ trùng lớp 1 và đã bị loại. Đưa chúng vào là đóng băng lớp 1, sau này sửa map ICB sẽ không lan tới nữa.

Mã cũ → mã mới khi đọc cột *Chủ dự án*: `BDS`→`DANDUNG` · `KCN`→`KHUCONGNGHIEP` · `VLXD`→`VATLIEU` · `YTEGD`→`YTE` · `CONGNGHIEP`→`THIETBI`. `KHOANGSAN` và `TIENICH` trùng mã nhưng **đổi nghĩa** — xem G4 và G6.

## Tiến độ

| Nhóm | Chủ đề | Số mã | Trạng thái |
|---|---|---|---|
| G1 | Khu công nghiệp và Bất động sản | 40 | ✅ xong |
| G2 | Cao su thiên nhiên | 12 | ✅ xong |
| G3 | Thủy sản · Nông nghiệp · Thực phẩm | 68 | ✅ xong |
| G4 | Khoáng sản · Kim loại · Giấy | 23 | ✅ xong |
| G5 | Vật liệu ↔ Xây dựng | 55 | ✅ xong |
| G6 | Dầu khí · Tiện ích · Vận tải | 24 | ✅ xong |
| G7 | Bán lẻ · Dệt may · Gia dụng · Thiết bị · Nhựa · Hóa chất | 33 | ✅ xong |
| G8 | Tài chính · Công nghệ · Y tế · Du lịch và mã lẻ | 11 | ✅ xong |
| G9 | Không có icb_code — lớp 1 trả NULL | 29 | ✅ xong |

**Tổng ứng viên: 295**

---

## G1 — Khu công nghiệp và Bất động sản

40 mã — đã chốt 40.

| Mã | Sàn | Doanh nghiệp | Nhánh ICB | Lớp 1 | Claude | Chủ dự án | CHỐT |
|---|---|---|---|---|---|---|---|
| BAX | HNX | Công ty Cổ phần Thống Nhất | `2357` Xây dựng | XAYDUNG | KHUCONGNGHIEP | — | **KHUCONGNGHIEP** |
| BCM | HOSE | Tập đoàn Đầu tư và Phát triển Công nghiệp Beca | `8633` Bất động sản | DANDUNG | KHUCONGNGHIEP | KHUCONGNGHIEP | **KHUCONGNGHIEP** |
| CCL | HOSE | Công ty Cổ phần Đầu tư và Phát triển Đô thị Dầ | `8633` Bất động sản | DANDUNG | — | KHUCONGNGHIEP | **KHUCONGNGHIEP** |
| CRE | HOSE | Công ty Cổ phần Bất động sản Thế Kỷ | `8633` Bất động sản | DANDUNG | — | DANDUNG | **KHUCONGNGHIEP** |
| D2D | HOSE | Công ty Cổ phần Phát triển Đô thị Công nghiệp  | `8633` Bất động sản | DANDUNG | KHUCONGNGHIEP | KHUCONGNGHIEP | **KHUCONGNGHIEP** |
| DPR | HOSE | Công ty Cổ phần Cao su Đồng Phú | `1353` Nhựa, cao su & sợi | NHUA | CAOSU | KHUCONGNGHIEP | **KHUCONGNGHIEP** |
| DRH | HOSE | Công ty Cổ phần DRH Holdings | `8633` Bất động sản | DANDUNG | — | DANDUNG | **KHUCONGNGHIEP** |
| DTD | HNX | Công ty Cổ phần Đầu tư Phát triển Thành Đạt | `8633` Bất động sản | DANDUNG | — | KHUCONGNGHIEP | **KHUCONGNGHIEP** |
| GVR | HOSE | Tập đoàn Công nghiệp Cao su Việt Nam - Công ty | `1353` Nhựa, cao su & sợi | NHUA | CAOSU | KHUCONGNGHIEP | **KHUCONGNGHIEP** |
| HAR | HOSE | Công ty Cổ phần Đầu tư Thương mại Bất động sản | `8633` Bất động sản | DANDUNG | — | KHUCONGNGHIEP | **KHUCONGNGHIEP** |
| HPI | UPCOM | Công ty Cổ phần Khu công nghiệp Hiệp Phước | `8633` Bất động sản | DANDUNG | KHUCONGNGHIEP | — | **KHUCONGNGHIEP** |
| HTN | HOSE | Công ty Cổ phần Hưng Thịnh Incons | `8633` Bất động sản | DANDUNG | — | XAYDUNG | **LOP1** |
| IDC | HNX | Tổng Công ty IDICO - CTCP | `8633` Bất động sản | DANDUNG | KHUCONGNGHIEP | KHUCONGNGHIEP | **KHUCONGNGHIEP** |
| IDV | HNX | Công ty Cổ phần Phát triển Hạ tầng Vĩnh Phúc | `8633` Bất động sản | DANDUNG | KHUCONGNGHIEP | — | **KHUCONGNGHIEP** |
| ITA | UPCOM | Công ty Cổ phần Đầu tư và Công nghiệp Tân Tạo | `8633` Bất động sản | DANDUNG | KHUCONGNGHIEP | DANDUNG | **KHUCONGNGHIEP** |
| KBC | HOSE | Tổng Công ty Phát triển Đô thị Kinh Bắc - CTCP | `8633` Bất động sản | DANDUNG | KHUCONGNGHIEP | KHUCONGNGHIEP | **KHUCONGNGHIEP** |
| KOS | HOSE | Công ty Cổ phần KOSY | `8633` Bất động sản | DANDUNG | — | KHUCONGNGHIEP | **KHUCONGNGHIEP** |
| LHG | HOSE | Công ty Cổ phần Long Hậu | `8633` Bất động sản | DANDUNG | KHUCONGNGHIEP | KHUCONGNGHIEP | **KHUCONGNGHIEP** |
| LMH | UPCOM | Công ty Cổ phần Quốc Tế Holding | `8633` Bất động sản | DANDUNG | — | BANLE | **LOP1** |
| MH3 | UPCOM | Công ty Cổ phần Khu công nghiệp Cao su Bình Lo | `8633` Bất động sản | DANDUNG | KHUCONGNGHIEP | — | **KHUCONGNGHIEP** |
| NTC | HOSE | Công ty Cổ phần Khu Công nghiệp Nam Tân Uyên | `8633` Bất động sản | DANDUNG | KHUCONGNGHIEP | DANDUNG | **KHUCONGNGHIEP** |
| NTL | HOSE | Công ty Cổ phần Phát triển Đô thị Từ Liêm | `8633` Bất động sản | DANDUNG | — | DANDUNG | **KHUCONGNGHIEP** |
| PHR | HOSE | Công ty Cổ phần Cao su Phước Hòa | `1353` Nhựa, cao su & sợi | NHUA | CAOSU | KHUCONGNGHIEP | **KHUCONGNGHIEP** |
| PIV | UPCOM | Công ty Cổ phần PIV | `8637` Tư Vấn, Định giá, Môi gi | DANDUNG | — | BANLE | **LOP1** |
| PRT | UPCOM | Tổng Công ty Sản xuất - Xuất nhập khẩu Bình Dư | `8633` Bất động sản | DANDUNG | — | KHOANGSAN | **LOP1** |
| PXL | UPCOM | Công ty Cổ phần Đầu tư Khu Công Nghiệp Dầu khí | `8633` Bất động sản | DANDUNG | KHUCONGNGHIEP | DANDUNG | **KHUCONGNGHIEP** |
| SIP | HOSE | Công ty Cổ phần Đầu tư Sài Gòn VRG | `8633` Bất động sản | DANDUNG | KHUCONGNGHIEP | KHUCONGNGHIEP | **KHUCONGNGHIEP** |
| SNZ | UPCOM | Tổng Công ty Cổ phần Phát triển Khu Công nghiệ | `2357` Xây dựng | XAYDUNG | KHUCONGNGHIEP | — | **KHUCONGNGHIEP** |
| SZB | HNX | Công ty Cổ phần Sonadezi Long Bình | `8633` Bất động sản | DANDUNG | KHUCONGNGHIEP | — | **KHUCONGNGHIEP** |
| SZC | HOSE | Công ty Cổ phần Sonadezi Châu Đức | `8633` Bất động sản | DANDUNG | KHUCONGNGHIEP | KHUCONGNGHIEP | **KHUCONGNGHIEP** |
| SZG | UPCOM | Công ty Cổ phần Sonadezi Giang Điền | `8633` Bất động sản | DANDUNG | KHUCONGNGHIEP | — | **KHUCONGNGHIEP** |
| SZL | HOSE | Công ty Cổ phần Sonadezi Long Thành | `8633` Bất động sản | DANDUNG | KHUCONGNGHIEP | DANDUNG | **KHUCONGNGHIEP** |
| TID | UPCOM | Công ty Cổ phần Tổng Công ty Tín Nghĩa | `8633` Bất động sản | DANDUNG | KHUCONGNGHIEP | NONGNGHIEP | **KHUCONGNGHIEP** |
| TIP | HOSE | Công ty Cổ phần Phát triển Khu công nghiệp Tín | `8633` Bất động sản | DANDUNG | KHUCONGNGHIEP | KHUCONGNGHIEP | **KHUCONGNGHIEP** |
| TIX | HOSE | Công ty Cổ phần Sản xuất Kinh doanh Xuất nhập  | `8633` Bất động sản | DANDUNG | — | — | **KHUCONGNGHIEP** |
| V21 | HNX | Công ty Cổ phần Vinaconex 21 | `8633` Bất động sản | DANDUNG | — | XAYDUNG | **LOP1** |
| VC3 | HNX | Công ty Cổ phần Tập đoàn Nam Mê Kông | `8637` Tư Vấn, Định giá, Môi gi | DANDUNG | — | DANDUNG | **KHUCONGNGHIEP** |
| VEF | UPCOM | Công ty Cổ phần Trung tâm Hội chợ Triển lãm Vi | `8633` Bất động sản | DANDUNG | — | DULICH | **LOP1** |
| VGC | HOSE | Tổng Công ty Viglacera - Công ty Cổ phần | `2353` Vật liệu xây dựng & Nội  | VATLIEU | KHUCONGNGHIEP | KHUCONGNGHIEP | **KHUCONGNGHIEP** |
| VRG | UPCOM | Công ty Cổ phần Phát triển Đô thị và Khu Công  | `8633` Bất động sản | DANDUNG | KHUCONGNGHIEP | DANDUNG | **KHUCONGNGHIEP** |

---

## G2 — Cao su thiên nhiên

12 mã — đã chốt 12.

| Mã | Sàn | Doanh nghiệp | Nhánh ICB | Lớp 1 | Claude | Chủ dự án | CHỐT |
|---|---|---|---|---|---|---|---|
| BRC | HOSE | Công ty Cổ phần Cao su Bến Thành | `1353` Nhựa, cao su & sợi | NHUA | CAOSU | — | **CAOSU** |
| BRR | UPCOM | Công ty Cổ phần Cao su Bà Rịa | `1353` Nhựa, cao su & sợi | NHUA | CAOSU | — | **CAOSU** |
| DRG | UPCOM | Công ty Cổ phần Cao su Đắk Lắk | `1353` Nhựa, cao su & sợi | NHUA | CAOSU | — | **CAOSU** |
| DRI | UPCOM | Công ty Cổ phần Đầu tư Cao su Đắk Lắk | `1353` Nhựa, cao su & sợi | NHUA | CAOSU | CAOSU | **CAOSU** |
| HRC | HOSE | Công ty Cổ phần Cao su Hòa Bình | `1353` Nhựa, cao su & sợi | NHUA | CAOSU | — | **CAOSU** |
| IRC | UPCOM | Công ty Cổ phần Cao su Công nghiệp | `1353` Nhựa, cao su & sợi | NHUA | CAOSU | — | **CAOSU** |
| RBC | UPCOM | Công ty Cổ phần Công Nghiệp và Xuất nhập khẩu  | `1353` Nhựa, cao su & sợi | NHUA | CAOSU | — | **CAOSU** |
| RTB | UPCOM | Công ty Cổ phần Cao su Tân Biên | `1353` Nhựa, cao su & sợi | NHUA | CAOSU | — | **CAOSU** |
| SBR | UPCOM | Công ty Cổ phần Cao su Sông Bé | `1353` Nhựa, cao su & sợi | NHUA | CAOSU | — | **CAOSU** |
| TNC | HOSE | Công ty Cổ phần Cao su Thống Nhất | `1353` Nhựa, cao su & sợi | NHUA | CAOSU | — | **CAOSU** |
| TRC | HOSE | Công ty Cổ phần Cao su Tây Ninh | `1353` Nhựa, cao su & sợi | NHUA | CAOSU | CAOSU | **CAOSU** |
| VKC | UPCOM | Công ty Cổ phần VKC Holdings | `3357` Lốp xe | CAOSU | — | BANLE | **NHUA** |

---

## G3 — Thủy sản · Nông nghiệp · Thực phẩm

68 mã — đã chốt 68.

| Mã | Sàn | Doanh nghiệp | Nhánh ICB | Lớp 1 | Claude | Chủ dự án | CHỐT |
|---|---|---|---|---|---|---|---|
| AAM | HOSE | Công ty Cổ Phần Thủy Sản MeKong | `3573` Nuôi trồng nông & hải sả | THUYSAN | THUYSAN | — | **LOP1** |
| AAN | HOSE | Công ty Cổ phần Lương thực A An | `3573` Nuôi trồng nông & hải sả | THUYSAN | — | NONGNGHIEP | **NONGNGHIEP** |
| ABT | HOSE | Công ty Cổ phần Xuất nhập khẩu Thủy sản Bến Tr | `3573` Nuôi trồng nông & hải sả | THUYSAN | THUYSAN | — | **LOP1** |
| ACL | HOSE | Công ty Cổ phần Xuất nhập khẩu Thủy sản Cửu Lo | `3573` Nuôi trồng nông & hải sả | THUYSAN | THUYSAN | THUYSAN | **LOP1** |
| AFX | HOSE | Công ty Cổ phần Xuất Nhập khẩu Nông sản Thực p | `5337` Phân phối thực phẩm | BANLE | — | NONGNGHIEP | **NONGNGHIEP** |
| AGF | UPCOM | Công ty Cổ phần Xuất nhập khẩu Thủy sản An Gia | `3573` Nuôi trồng nông & hải sả | THUYSAN | THUYSAN | — | **LOP1** |
| AGM | UPCOM | Công ty Cổ phần Xuất nhập khẩu An Giang | `3577` Thực phẩm | THUCPHAM | — | NONGNGHIEP | **NONGNGHIEP** |
| ANV | HOSE | Công ty Cổ phần Nam Việt | `3573` Nuôi trồng nông & hải sả | THUYSAN | THUYSAN | THUYSAN | **LOP1** |
| APT | UPCOM | Công ty Cổ phần Kinh doanh thủy hải sản Sài Gò | `3573` Nuôi trồng nông & hải sả | THUYSAN | THUYSAN | — | **LOP1** |
| ASM | HOSE | Công ty Cổ phần Tập đoàn Sao Mai | `3573` Nuôi trồng nông & hải sả | THUYSAN | THUYSAN | DANDUNG | **LOP1** |
| ATA | UPCOM | Công ty Cổ phần NTACO | `3573` Nuôi trồng nông & hải sả | THUYSAN | THUYSAN | — | **LOP1** |
| BAF | HOSE | Công ty Cổ phần Nông nghiệp BAF Việt Nam | `3573` Nuôi trồng nông & hải sả | THUYSAN | — | NONGNGHIEP | **NONGNGHIEP** |
| BIG | UPCOM | Công ty Cổ phần Tập đoàn Đầu tư BIG | `3573` Nuôi trồng nông & hải sả | THUYSAN | — | XAYDUNG | **XAYDUNG** |
| BLF | UPCOM | Công ty Cổ phần Thủy sản Bạc Liêu | `3573` Nuôi trồng nông & hải sả | THUYSAN | THUYSAN | — | **LOP1** |
| CAD | UPCOM | Công ty Cổ phần Chế biến và Xuất khẩu Thủy sản | `3573` Nuôi trồng nông & hải sả | THUYSAN | THUYSAN | — | **LOP1** |
| CAT | UPCOM | Công ty Cổ phần Thủy sản Cà Mau | `3573` Nuôi trồng nông & hải sả | THUYSAN | THUYSAN | — | **LOP1** |
| CCA | UPCOM | Công ty Cổ phần Xuất nhập khẩu Thủy sản Cần Th | `3573` Nuôi trồng nông & hải sả | THUYSAN | THUYSAN | — | **LOP1** |
| CET | HNX | Công ty Cổ phần HTC Holding | `3767` Hàng cá nhân | DETMAY | — | NONGNGHIEP | **NONGNGHIEP** |
| CLX | UPCOM | Công ty Cổ phần Xuất nhập khẩu và Đầu tư Chợ L | `3577` Thực phẩm | THUCPHAM | — | BANLE | **LOP1** |
| CMM | UPCOM | Công ty Cổ phần Camimex | `3577` Thực phẩm | THUCPHAM | THUYSAN | — | **THUYSAN** |
| CMX | HOSE | Công ty Cổ phần CAMIMEX Group | `3573` Nuôi trồng nông & hải sả | THUYSAN | THUYSAN | THUYSAN | **LOP1** |
| CNA | UPCOM | Công ty Cổ phần Tổng công ty Chè Nghệ An | `3573` Nuôi trồng nông & hải sả | THUYSAN | — | — | **NONGNGHIEP** |
| CTP | HNX | Công ty Cổ phần Tập đoàn CTP Group | `3537` Đồ uống & giải khát | THUCPHAM | — | NONGNGHIEP | **LOP1** |
| DAT | HOSE | Công ty Cổ phần Đầu tư Du lịch và Phát triển T | `3573` Nuôi trồng nông & hải sả | THUYSAN | THUYSAN | — | **LOP1** |
| DBC | HOSE | Công ty Cổ phần Tập đoàn Dabaco Việt Nam | `3573` Nuôi trồng nông & hải sả | THUYSAN | — | NONGNGHIEP | **NONGNGHIEP** |
| DMN | UPCOM | Công ty Cổ phần Domenal | `3573` Nuôi trồng nông & hải sả | THUYSAN | — | — | **NONGNGHIEP** |
| FMC | HOSE | Công ty Cổ phần Thực phẩm Sao Ta | `3573` Nuôi trồng nông & hải sả | THUYSAN | THUYSAN | THUYSAN | **LOP1** |
| GPC | UPCOM | Công ty Cổ phần Tập đoàn Green+ | `4577` Dược phẩm | YTE | — | NONGNGHIEP | **NONGNGHIEP** |
| HAG | HOSE | Công ty Cổ phần Hoàng Anh Gia Lai | `3573` Nuôi trồng nông & hải sả | THUYSAN | — | NONGNGHIEP | **NONGNGHIEP** |
| HKB | UPCOM | Công ty Cổ phần Nông nghiệp và Thực phẩm Hà Nộ | `3577` Thực phẩm | THUCPHAM | — | NONGNGHIEP | **NONGNGHIEP** |
| HNG | UPCOM | Công ty Cổ phần Nông nghiệp Quốc tế Hoàng Anh  | `3573` Nuôi trồng nông & hải sả | THUYSAN | — | NONGNGHIEP | **NONGNGHIEP** |
| HPA | HOSE | Công ty Cổ phần Phát triển Nông nghiệp Hoà Phá | `3573` Nuôi trồng nông & hải sả | THUYSAN | — | NONGNGHIEP | **NONGNGHIEP** |
| HSL | HOSE | Công ty Cổ phần Đầu tư Phát triển Thực phẩm Hồ | `3577` Thực phẩm | THUCPHAM | — | NONGNGHIEP | **NONGNGHIEP** |
| ICF | UPCOM | Công ty Cổ phần Đầu tư - Thương mại - Thuỷ sản | `3573` Nuôi trồng nông & hải sả | THUYSAN | THUYSAN | — | **LOP1** |
| IDI | HOSE | Công ty Cổ phần Đầu tư và Phát triển Đa Quốc G | `3573` Nuôi trồng nông & hải sả | THUYSAN | THUYSAN | THUYSAN | **LOP1** |
| ILA | UPCOM | Công ty Cổ phần ILA | `2353` Vật liệu xây dựng & Nội  | VATLIEU | — | NONGNGHIEP | **NONGNGHIEP** |
| JOS | UPCOM | Công ty Cổ phần Chế biến Thủy sản Xuất khẩu Mi | `3573` Nuôi trồng nông & hải sả | THUYSAN | THUYSAN | — | **LOP1** |
| KGM | UPCOM | Công ty Cổ phần Xuất nhập khẩu Kiên Giang | `5373` Bán lẻ phức hợp | BANLE | — | NONGNGHIEP | **NONGNGHIEP** |
| KHS | HNX | Công ty Cổ phần Kiên Hùng | `3573` Nuôi trồng nông & hải sả | THUYSAN | THUYSAN | THUYSAN | **LOP1** |
| MLS | UPCOM | Công ty Cổ phần Chăn nuôi - Mitraco | `3573` Nuôi trồng nông & hải sả | THUYSAN | — | NONGNGHIEP | **NONGNGHIEP** |
| MPC | UPCOM | Công ty Cổ phần Tập đoàn Thủy sản Minh Phú | `3573` Nuôi trồng nông & hải sả | THUYSAN | THUYSAN | THUYSAN | **LOP1** |
| NCG | UPCOM | Công ty Cổ phần Đầu tư Anova Agri | `3573` Nuôi trồng nông & hải sả | THUYSAN | — | THUYSAN | **NONGNGHIEP** |
| NDF | UPCOM | Công ty Cổ phần Chế biến thực phẩm nông sản xu | `3577` Thực phẩm | THUCPHAM | — | NONGNGHIEP | **NONGNGHIEP** |
| NGC | UPCOM | Công ty Cổ phần Chế biến Thủy sản Xuất khẩu Ng | `3573` Nuôi trồng nông & hải sả | THUYSAN | THUYSAN | — | **LOP1** |
| NHV | UPCOM | Công ty Cổ phần Sức khỏe Hồi sinh Việt Nam | `1755` Kim Loại màu | KIMLOAI | — | NONGNGHIEP | **NONGNGHIEP** |
| NSC | HOSE | Công ty Cổ phần Tập đoàn Giống cây trồng Việt  | `3573` Nuôi trồng nông & hải sả | THUYSAN | — | — | **NONGNGHIEP** |
| NSS | UPCOM | Công ty Cổ phần Nông súc sản Đồng Nai | `3573` Nuôi trồng nông & hải sả | THUYSAN | — | — | **NONGNGHIEP** |
| OCH | HNX | Công ty Cổ phần One Capital Hospitality | `3577` Thực phẩm | THUCPHAM | — | DULICH | **DULICH** |
| PSL | UPCOM | Công ty Cổ phần Chăn nuôi Phú Sơn | `3573` Nuôi trồng nông & hải sả | THUYSAN | — | — | **NONGNGHIEP** |
| SBB | UPCOM | Công ty Cổ phần Tập đoàn Bia Sài Gòn Bình Tây | `3533` Sản xuất bia | THUCPHAM | — | DETMAY | **DETMAY** |
| SEA | UPCOM | Tổng Công ty Thủy sản Việt Nam - Công ty Cổ ph | `3573` Nuôi trồng nông & hải sả | THUYSAN | THUYSAN | THUYSAN | **LOP1** |
| SJ1 | HNX | Công ty Cổ phần Nông nghiệp Hùng Hậu | `3573` Nuôi trồng nông & hải sả | THUYSAN | THUYSAN | — | **LOP1** |
| SJF | UPCOM | Công ty Cổ phần Đầu tư Sao Thái Dương | `1733` Lâm sản và Chế biến gỗ | DETMAY | — | NONGNGHIEP | **LOP1** |
| SNC | UPCOM | Công ty Cổ phần Xuất nhập khẩu Thủy sản Năm Că | `3573` Nuôi trồng nông & hải sả | THUYSAN | THUYSAN | — | **LOP1** |
| SPD | UPCOM | Công ty Cổ phần Xuất nhập khẩu Thủy sản Miền T | `3573` Nuôi trồng nông & hải sả | THUYSAN | THUYSAN | — | **LOP1** |
| SPH | UPCOM | Công ty Cổ phần Xuất Nhập khẩu Thủy sản Hà Nội | `3573` Nuôi trồng nông & hải sả | THUYSAN | THUYSAN | — | **LOP1** |
| SPV | UPCOM | Công ty Cổ phần Thủy Đặc Sản | `3573` Nuôi trồng nông & hải sả | THUYSAN | THUYSAN | — | **LOP1** |
| SSC | HOSE | Công ty Cổ phần Giống cây trồng Miền Nam | `3573` Nuôi trồng nông & hải sả | THUYSAN | — | — | **NONGNGHIEP** |
| TAR | UPCOM | Công ty Cổ phần Nông nghiệp Công nghệ cao Trun | `3573` Nuôi trồng nông & hải sả | THUYSAN | — | NONGNGHIEP | **NONGNGHIEP** |
| TCJ | UPCOM | Công ty Cổ phần Tô Châu | `3573` Nuôi trồng nông & hải sả | THUYSAN | — | — | **NONGNGHIEP** |
| TCO | HOSE | Công ty Cổ phần Janus Group | `3573` Nuôi trồng nông & hải sả | THUYSAN | — | VANTAI | **VANTAI** |
| THP | UPCOM | Công ty Cổ phần Thủy sản và Thương mại Thuận P | `3573` Nuôi trồng nông & hải sả | THUYSAN | THUYSAN | — | **LOP1** |
| TT6 | UPCOM | Công ty Cổ Phần Tập Đoàn Tiến Thịnh | `3577` Thực phẩm | THUCPHAM | — | NONGNGHIEP | **NONGNGHIEP** |
| UXC | UPCOM | Công ty Cổ phần Chế biến Thủy sản Út Xi | `3573` Nuôi trồng nông & hải sả | THUYSAN | THUYSAN | — | **LOP1** |
| VHC | HOSE | Công ty Cổ phần Vĩnh Hoàn | `3573` Nuôi trồng nông & hải sả | THUYSAN | THUYSAN | THUYSAN | **LOP1** |
| VHE | HNX | Công ty Cổ phần Dược liệu và Thực phẩm Việt Na | `4577` Dược phẩm | YTE | — | NONGNGHIEP | **LOP1** |
| VLC | UPCOM | Tổng Công ty Chăn nuôi Việt Nam - Công ty Cổ p | `3573` Nuôi trồng nông & hải sả | THUYSAN | — | NONGNGHIEP | **NONGNGHIEP** |
| VNH | UPCOM | Công ty Cổ phần Đầu tư Việt Việt Nhật | `3573` Nuôi trồng nông & hải sả | THUYSAN | THUYSAN | THUYSAN | **LOP1** |

---

## G4 — Khoáng sản · Kim loại · Giấy

23 mã — đã chốt 23.

| Mã | Sàn | Doanh nghiệp | Nhánh ICB | Lớp 1 | Claude | Chủ dự án | CHỐT |
|---|---|---|---|---|---|---|---|
| BCA | UPCOM | Công ty cổ phần B.C.H | `1757` Thép và sản phẩm thép | KIMLOAI | — | KHOANGSAN | **LOP1** |
| BKG | HOSE | Công ty Cổ phần Đầu tư BKG Việt Nam | `3726` Thiết bị gia dụng | DETMAY | — | KHOANGSAN | **LOP1** |
| DHC | HOSE | Công ty Cổ phần Đông Hải Bến Tre | `1737` Sản xuất giấy | NHUA | — | KHOANGSAN | **LOP1** |
| FCM | HOSE | Công ty Cổ phần Bê tông Phan Vũ Hà Nam | `2353` Vật liệu xây dựng & Nội  | VATLIEU | — | KHOANGSAN | **LOP1** |
| HAP | HOSE | Công ty Cổ phần Tập Đoàn Hapaco | `1737` Sản xuất giấy | NHUA | — | KHOANGSAN | **LOP1** |
| HHP | HOSE | Công ty Cổ phần HHP Global | `1737` Sản xuất giấy | NHUA | — | KHOANGSAN | **LOP1** |
| HSV | UPCOM | Công ty Cổ phần Tập đoàn HSV Việt Nam | `1757` Thép và sản phẩm thép | KIMLOAI | — | KHOANGSAN | **LOP1** |
| ITQ | HNX | Công ty Cổ phần Tập đoàn Thiên Quang | `1757` Thép và sản phẩm thép | KIMLOAI | — | KHOANGSAN | **LOP1** |
| KSB | HOSE | Công ty Cổ phần Khoáng sản và Xây dựng Bình Dư | `2353` Vật liệu xây dựng & Nội  | VATLIEU | — | KHOANGSAN | **KHOANGSAN** |
| KSQ | UPCOM | Công ty Cổ phần CNC Capital Việt Nam | `2353` Vật liệu xây dựng & Nội  | VATLIEU | — | KHOANGSAN | **LOP1** |
| MZG | HOSE | Công ty Cổ Phần Miza | `1737` Sản xuất giấy | NHUA | — | KHOANGSAN | **LOP1** |
| NSH | HNX | Công ty Cổ phần Tập đoàn Nhôm Sông Hồng Shalum | `1753` Nhôm | KIMLOAI | — | KHOANGSAN | **LOP1** |
| PAT | UPCOM | Công ty Cổ phần Phốt pho Apatit Việt Nam | `1357` Sản phẩm hóa dầu, Nông d | HOACHAT | — | KHOANGSAN | **LOP1** |
| SHA | HOSE | Công ty Cổ phần Sơn Hà Sài Gòn | `1757` Thép và sản phẩm thép | KIMLOAI | — | KHOANGSAN | **LOP1** |
| SHI | HOSE | Công ty Cổ phần Quốc tế Sơn Hà | `1757` Thép và sản phẩm thép | KIMLOAI | — | BANLE | **LOP1** |
| SHN | HNX | Công ty Cổ phần Đầu tư Tổng hợp Hà Nội | `1771` Khai thác Than | KHOANGSAN | — | BANLE | **BANLE** |
| SPI | UPCOM | Công ty Cổ phần Spiral Galaxy | `1775` Khai khoáng | KHOANGSAN | — | XAYDUNG | **LOP1** |
| SVT | HOSE | Công ty Cổ phần Công nghệ Sài Gòn Viễn Đông | `5377` Dịch vụ tiêu dùng chuyên | BANLE | — | KHOANGSAN | **THIETBI** |
| TNA | UPCOM | Công ty Cổ phần Thương mại Xuất nhập khẩu Thiê | `1757` Thép và sản phẩm thép | KIMLOAI | — | BANLE | **LOP1** |
| TNI | HOSE | Công ty Cổ phần Tập đoàn Thành Nam | `1757` Thép và sản phẩm thép | KIMLOAI | — | THIETBI | **LOP1** |
| TNT | HOSE | Công ty Cổ phần Tập đoàn TNT | `2353` Vật liệu xây dựng & Nội  | VATLIEU | — | KHOANGSAN | **LOP1** |
| TTH | HNX | Công ty Cổ phần Thương mại và Dịch vụ Tiến Thà | `1757` Thép và sản phẩm thép | KIMLOAI | — | BANLE | **BANLE** |
| VID | HOSE | Công ty Cổ phần Đầu tư Phát triển Thương mại V | `1737` Sản xuất giấy | NHUA | — | KHOANGSAN | **LOP1** |

---

## G5 — Vật liệu ↔ Xây dựng

55 mã — đã chốt 55.

| Mã | Sàn | Doanh nghiệp | Nhánh ICB | Lớp 1 | Claude | Chủ dự án | CHỐT |
|---|---|---|---|---|---|---|---|
| ACC | HOSE | Công ty Cổ phần Đầu tư và Xây dựng Bình Dương  | `2353` Vật liệu xây dựng & Nội  | VATLIEU | — | XAYDUNG | **XAYDUNG** |
| ALV | UPCOM | Công ty Cổ phần Tập đoàn MCST | `2357` Xây dựng | XAYDUNG | — | VATLIEU | **LOP1** |
| AMS | UPCOM | Công ty Cổ phần Cơ khí Xây dựng AMECC | `2797` Nhà cung cấp thiết bị | THIETBI | — | XAYDUNG | **XAYDUNG** |
| ANI | UPCOM | Công ty Cổ phần ANI | `7535` Sản xuất & Phân phối Điệ | TIENICH | — | VATLIEU | **LOP1** |
| BDT | UPCOM | Công ty Cổ phần Xây lắp và Vật liệu xây dựng Đ | `2353` Vật liệu xây dựng & Nội  | VATLIEU | — | XAYDUNG | **XAYDUNG** |
| BMP | HOSE | Công ty Cổ phần Nhựa Bình Minh | `2353` Vật liệu xây dựng & Nội  | VATLIEU | — | NHUA | **NHUA** |
| CGV | UPCOM | Công ty Cổ phần Vinaceglass | `2353` Vật liệu xây dựng & Nội  | VATLIEU | — | XAYDUNG | **LOP1** |
| CIG | HOSE | Công ty Cổ phần COMA 18 | `2357` Xây dựng | XAYDUNG | — | DANDUNG | **DANDUNG** |
| CSC | HNX | Công ty Cổ phần Tập đoàn COTANA | `2357` Xây dựng | XAYDUNG | — | DANDUNG | **DANDUNG** |
| CTR | HOSE | Tổng Công ty Cổ phần Công trình Viettel | `2357` Xây dựng | XAYDUNG | — | CONGNGHE | **CONGNGHE** |
| CVN | UPCOM | Công ty Cổ phần Vinam | `4535` Thiết bị y tế | YTE | — | XAYDUNG | **XAYDUNG** |
| CVT | HOSE | Công ty Cổ phần CMC | `2353` Vật liệu xây dựng & Nội  | VATLIEU | — | XAYDUNG | **LOP1** |
| DDB | UPCOM | Công ty Cổ Phần Thương Mại Và Xây Dựng Đông Dư | `2353` Vật liệu xây dựng & Nội  | VATLIEU | — | YTE | **DETMAY** |
| DFF | UPCOM | Công ty Cổ phần Tập đoàn Đua Fat | `2357` Xây dựng | XAYDUNG | — | VATLIEU | **LOP1** |
| DGT | UPCOM | Công ty Cổ phần Công trình Giao thông Đồng Nai | `2353` Vật liệu xây dựng & Nội  | VATLIEU | — | XAYDUNG | **XAYDUNG** |
| DIC | UPCOM | Công ty Cổ phần Đầu tư và Thương mại DIC | `2353` Vật liệu xây dựng & Nội  | VATLIEU | — | XAYDUNG | **LOP1** |
| DID | UPCOM | Công ty Cổ phần DIC - Đồng Tiến | `2353` Vật liệu xây dựng & Nội  | VATLIEU | — | XAYDUNG | **XAYDUNG** |
| DLG | HOSE | Công ty Cổ phần Tập đoàn Đức Long Gia Lai | `2357` Xây dựng | XAYDUNG | — | DANDUNG | **DANDUNG** |
| DSH | UPCOM | Công ty Cổ phần Đông Sơn Holdings | `2357` Xây dựng | XAYDUNG | — | VATLIEU | **LOP1** |
| DST | HNX | Công ty Cổ phần Đầu tư Sao Thăng Long | `5557` Sách, ấn bản & sản phẩm  | YTE | — | XAYDUNG | **LOP1** |
| FID | HNX | Công ty Cổ phần Đầu tư và Phát triển Doanh ngh | `2353` Vật liệu xây dựng & Nội  | VATLIEU | — | XAYDUNG | **DANDUNG** |
| GEL | HOSE | Công ty Cổ phần Hạ tầng GELEX | `2353` Vật liệu xây dựng & Nội  | VATLIEU | — | DANDUNG | **DANDUNG** |
| HMR | HNX | Công ty Cổ phần Đá Hoàng Mai | `2353` Vật liệu xây dựng & Nội  | VATLIEU | — | XAYDUNG | **KHOANGSAN** |
| HTE | UPCOM | Công ty Cổ phần Đầu tư Kinh doanh Điện lực Thà | `2737` Thiết bị điện | THIETBI | — | XAYDUNG | **LOP1** |
| HUB | HOSE | Công ty Cổ phần Xây lắp Thừa Thiên Huế | `2357` Xây dựng | XAYDUNG | — | VATLIEU | **LOP1** |
| HUT | HNX | Công ty Cổ phần Tasco | `3353` Sản xuất ô tô | BANLE | — | XAYDUNG | **LOP1** |
| IPA | HNX | Công ty Cổ phần Tập đoàn Đầu tư I.P.A | `2791` Tư vấn & Hỗ trợ KD | XAYDUNG | CHUNGKHOAN | TIENICH | **DANDUNG** |
| KPF | UPCOM | Công ty Cổ phần Đầu tư Tài sản KOJI | `2353` Vật liệu xây dựng & Nội  | VATLIEU | — | XAYDUNG | **DANDUNG** |
| L14 | HNX | Công ty Cổ phần Licogi 14 | `2357` Xây dựng | XAYDUNG | — | DANDUNG | **DANDUNG** |
| LAI | UPCOM | Công ty Cổ phần Đầu tư Xây dựng Long An IDICO | `2357` Xây dựng | XAYDUNG | — | DANDUNG | **DANDUNG** |
| MBG | HNX | Công ty Cổ phần Tập đoàn MBG | `2353` Vật liệu xây dựng & Nội  | VATLIEU | — | BANLE | **THIETBI** |
| NAG | HNX | Công ty Cổ phần Tập đoàn Nagakawa | `2733` Hàng điện & điện tử | THIETBI | — | XAYDUNG | **LOP1** |
| NED | UPCOM | Công ty Cổ phần Đầu tư và Phát triển Điện Tây  | `2357` Xây dựng | XAYDUNG | — | TIENICH | **LOP1** |
| NHA | HOSE | Tổng Công ty Đầu tư Phát triển Nhà và Đô thị N | `2357` Xây dựng | XAYDUNG | — | DANDUNG | **DANDUNG** |
| NO1 | HOSE | Công ty Cổ phần Tập đoàn 911 | `2757` Máy công nghiệp | THIETBI | — | XAYDUNG | **LOP1** |
| NTP | HNX | Công ty Cổ phần Nhựa Thiếu niên Tiền Phong | `2353` Vật liệu xây dựng & Nội  | VATLIEU | — | NHUA | **NHUA** |
| PC1 | HOSE | Công ty Cổ phần Tập đoàn PC1 | `2357` Xây dựng | XAYDUNG | — | TIENICH | **TIENICH** |
| PDB | HNX | Công ty Cổ phần Tập đoàn Đầu tư DIN Capital | `2353` Vật liệu xây dựng & Nội  | VATLIEU | — | XAYDUNG | **LOP1** |
| PFL | UPCOM | Công ty Cổ phần Dầu khí Đông Đô | `2357` Xây dựng | XAYDUNG | — | DANDUNG | **DANDUNG** |
| PTB | HOSE | Công ty Cổ phần Phú Tài | `1733` Lâm sản và Chế biến gỗ | DETMAY | — | VATLIEU | **VATLIEU** |
| PVV | UPCOM | Công ty Cổ phần Vinaconex 39 | `2357` Xây dựng | XAYDUNG | — | DAUKHI | **DAUKHI** |
| PVX | UPCOM | Tổng Công ty Cổ phần Xây lắp Dầu khí Việt Nam | `2357` Xây dựng | XAYDUNG | — | DAUKHI | **DAUKHI** |
| SCG | HNX | Công ty Cổ phần Tập đoàn Xây dựng SCG | `2357` Xây dựng | XAYDUNG | — | VATLIEU | **LOP1** |
| THG | HOSE | Công ty Cổ phần Đầu tư và Xây dựng Tiền Giang | `2353` Vật liệu xây dựng & Nội  | VATLIEU | — | XAYDUNG | **XAYDUNG** |
| TLD | HOSE | Công ty Cổ phần Đầu tư Xây dựng và Phát triển  | `2353` Vật liệu xây dựng & Nội  | VATLIEU | — | XAYDUNG | **XAYDUNG** |
| TTB | UPCOM | Công ty Cổ phần TTBGROUP | `2353` Vật liệu xây dựng & Nội  | VATLIEU | — | XAYDUNG | **LOP1** |
| TTZ | UPCOM | Công ty Cổ phần Đầu tư Xây dựng và Công nghệ T | `2353` Vật liệu xây dựng & Nội  | VATLIEU | — | VANTAI | **KHOANGSAN** |
| TV1 | UPCOM | Công ty Cổ phần Tư vấn Xây dựng Điện 1 | `2791` Tư vấn & Hỗ trợ KD | XAYDUNG | — | TIENICH | **TIENICH** |
| TV2 | HOSE | Công ty Cổ phần Tư vấn Xây dựng Điện 2 | `2791` Tư vấn & Hỗ trợ KD | XAYDUNG | — | TIENICH | **TIENICH** |
| TV3 | HNX | Công ty Cổ phần Tư vấn Xây dựng Điện 3 | `2791` Tư vấn & Hỗ trợ KD | XAYDUNG | — | THIETBI | **TIENICH** |
| VIW | UPCOM | Tổng công ty Đầu tư Nước và Môi trường Việt Na | `2357` Xây dựng | XAYDUNG | — | TIENICH | **TIENICH** |
| VSE | UPCOM | Công ty Cổ phần Dịch vụ Đường cao tốc Việt Nam | `2777` Kho bãi, hậu cần và bảo  | VANTAI | — | XAYDUNG | **LOP1** |
| VTK | UPCOM | Công ty Cổ phần Tư vấn và Dịch vụ Viettel | `2791` Tư vấn & Hỗ trợ KD | XAYDUNG | — | CONGNGHE | **CONGNGHE** |
| VTV | HNX | Công ty Cổ phần Năng lượng và Môi trường VICEM | `2353` Vật liệu xây dựng & Nội  | VATLIEU | — | XAYDUNG | **KHOANGSAN** |
| XMC | UPCOM | Công ty cổ phần Đầu tư và Xây dựng Xuân Mai | `2353` Vật liệu xây dựng & Nội  | VATLIEU | — | XAYDUNG | **XAYDUNG** |

---

## G6 — Dầu khí · Tiện ích · Vận tải

24 mã — đã chốt 24.

| Mã | Sàn | Doanh nghiệp | Nhánh ICB | Lớp 1 | Claude | Chủ dự án | CHỐT |
|---|---|---|---|---|---|---|---|
| ACV | UPCOM | Tổng Công ty Cảng Hàng không Việt Nam - CTCP | `2777` Kho bãi, hậu cần và bảo  | VANTAI | — | DULICH | **DULICH** |
| ASP | HOSE | Công ty Cổ phần Tập đoàn Dầu khí An Pha | `7573` Phân phối xăng dầu & khí | DAUKHI | — | TIENICH | **LOP1** |
| CIA | HNX | Công ty Cổ Phần Dịch Vụ Sân Bay Quốc Tế Cam Ra | `2777` Kho bãi, hậu cần và bảo  | VANTAI | — | DULICH | **DULICH** |
| DDG | UPCOM | Công ty Cổ phần Đầu tư Công nghiệp Xuất nhập k | `7573` Phân phối xăng dầu & khí | DAUKHI | — | THIETBI | **TIENICH** |
| DS3 | HNX | Công ty Cổ phần DS3 | `2777` Kho bãi, hậu cần và bảo  | VANTAI | — | DULICH | **LOP1** |
| GEE | HOSE | Công ty Cổ phần Điện lực Gelex | `2737` Thiết bị điện | THIETBI | — | TIENICH | **LOP1** |
| GSP | HOSE | Công ty Cổ phần Vận tải Sản phẩm Khí Quốc tế | `2773` Vận tải Thủy | VANTAI | — | DAUKHI | **DAUKHI** |
| MAC | HNX | Công ty Cổ phần Tập đoàn Macstar | `2753` Xe tải & Đóng tàu | THIETBI | — | VANTAI | **VANTAI** |
| PCG | UPCOM | Công ty Cổ phần Đầu tư Phát triển Gas Đô thị | `7573` Phân phối xăng dầu & khí | DAUKHI | — | TIENICH | **LOP1** |
| PGC | HOSE | Tổng Công ty Gas Petrolimex - Công ty Cổ phần | `7573` Phân phối xăng dầu & khí | DAUKHI | — | TIENICH | **LOP1** |
| PGD | HOSE | Công ty Cổ phần Phân phối khí thấp áp dầu khí  | `7573` Phân phối xăng dầu & khí | DAUKHI | — | TIENICH | **LOP1** |
| PGS | HNX | Công ty Cổ phần Kinh doanh Khí Miền Nam | `7573` Phân phối xăng dầu & khí | DAUKHI | — | TIENICH | **LOP1** |
| PGT | HNX | Công ty Cổ phần PGT Holdings | `5759` Vận tải hành khách & Du  | DULICH | — | VANTAI | **DANDUNG** |
| PLC | HNX | Tổng Công ty Hóa dầu Petrolimex - Công ty Cổ p | `1357` Sản phẩm hóa dầu, Nông d | HOACHAT | — | DAUKHI | **DAUKHI** |
| PMG | HOSE | Công ty Cổ phần Đầu tư và Sản xuất Petro Miền  | `7573` Phân phối xăng dầu & khí | DAUKHI | — | TIENICH | **LOP1** |
| PSP | UPCOM | Công ty Cổ phần Cảng Dịch vụ Dầu khí Đình Vũ | `2779` Dịch vụ vận tải | VANTAI | — | DAUKHI | **DAUKHI** |
| PVM | UPCOM | Công ty Cổ phần Máy - Thiết bị Dầu khí | `2797` Nhà cung cấp thiết bị | THIETBI | — | DAUKHI | **DAUKHI** |
| PVO | UPCOM | Công ty Cổ phần Dầu nhờn PV Oil | `1357` Sản phẩm hóa dầu, Nông d | HOACHAT | — | DAUKHI | **DAUKHI** |
| PVP | HOSE | Công ty Cổ phần Vận tải Dầu khí Thái Bình Dươn | `2779` Dịch vụ vận tải | VANTAI | — | DAUKHI | **DAUKHI** |
| PVT | HOSE | Tổng Công ty Cổ phần Vận tải Dầu khí | `2773` Vận tải Thủy | VANTAI | — | DAUKHI | **DAUKHI** |
| SCS | HOSE | Công ty Cổ phần Dịch vụ Hàng hóa Sài Gòn | `5751` Dịch vụ hàng không | DULICH | — | VANTAI | **LOP1** |
| SKG | HOSE | Công ty Cổ phần Tàu Cao tốc Superdong - Kiên G | `5759` Vận tải hành khách & Du  | DULICH | — | VANTAI | **VANTAI** |
| SSG | UPCOM | Công ty Cổ phần Vận tải Biển Hải Âu | `2773` Vận tải Thủy | VANTAI | — | THIETBI | **LOP1** |
| VNS | HOSE | Công ty Cổ phần Ánh Dương Việt Nam | `5759` Vận tải hành khách & Du  | DULICH | — | VANTAI | **VANTAI** |

---

## G7 — Bán lẻ · Dệt may · Gia dụng · Thiết bị · Nhựa · Hóa chất

33 mã — đã chốt 33.

| Mã | Sàn | Doanh nghiệp | Nhánh ICB | Lớp 1 | Claude | Chủ dự án | CHỐT |
|---|---|---|---|---|---|---|---|
| AAT | HOSE | Công ty Cổ phần Tập đoàn Tiên Sơn Thanh Hóa | `3763` Hàng May mặc | DETMAY | — | BANLE | **LOP1** |
| ACG | HOSE | Công ty Cổ phần Gỗ An Cường | `1733` Lâm sản và Chế biến gỗ | DETMAY | — | BANLE | **LOP1** |
| APC | UPCOM | Công ty Cổ phần Chiếu xạ An Phú | `4573` Công nghệ sinh học | YTE | — | HOACHAT | **NONGNGHIEP** |
| AST | HOSE | Công ty Cổ phần Dịch vụ Hàng không Taseco | `5379` Phân phối hàng chuyên dụ | BANLE | — | DULICH | **DULICH** |
| AVG | UPCOM | Công ty Cổ phần Phân Bón Quốc Tế Âu Việt | `1357` Sản phẩm hóa dầu, Nông d | HOACHAT | — | NHUA | **LOP1** |
| DCS | UPCOM | Công ty Cổ phần Tập đoàn EDX | `3726` Thiết bị gia dụng | DETMAY | — | BANLE | **LOP1** |
| DQC | HOSE | Công ty Cổ phần Tập đoàn Điện Quang | `3726` Thiết bị gia dụng | DETMAY | — | THIETBI | **THIETBI** |
| ECO | UPCOM | Công ty Cổ Phần Nhựa Sinh Thái Việt Nam | `1353` Nhựa, cao su & sợi | NHUA | — | HOACHAT | **LOP1** |
| GDT | HOSE | Công ty Cổ phần Chế biến Gỗ Đức Thành | `3726` Thiết bị gia dụng | DETMAY | — | BANLE | **LOP1** |
| HHG | UPCOM | Công ty Cổ phần Hoàng Hà | `5759` Vận tải hành khách & Du  | DULICH | — | THIETBI | **VANTAI** |
| HHS | HOSE | Công ty Cổ phần Đầu tư Dịch vụ Hoàng Huy | `3353` Sản xuất ô tô | BANLE | — | DANDUNG | **DANDUNG** |
| HTT | UPCOM | Công ty Cổ phần Thương mại Hà Tây | `5373` Bán lẻ phức hợp | BANLE | — | DANDUNG | **LOP1** |
| KSD | HNX | Công ty Cổ phần Đầu tư DNA | `3722` Đồ gia dụng lâu bền | DETMAY | — | BANLE | **LOP1** |
| LIX | HOSE | Công ty Cổ phần Bột Giặt LIX | `3767` Hàng cá nhân | DETMAY | — | HOACHAT | **HOACHAT** |
| LPT | UPCOM | Công ty Cổ phần Thương mại và Sản xuất Lập Phư | `2793` Đào tạo & Việc làm | YTE | — | THIETBI | **LOP1** |
| MPT | UPCOM | Công ty Cổ phần Tập đoàn MPT | `3763` Hàng May mặc | DETMAY | — | BANLE | **LOP1** |
| NET | HNX | Công ty Cổ phần Bột giặt Net | `3767` Hàng cá nhân | DETMAY | — | — | **HOACHAT** |
| PBP | HNX | Công ty Cổ phần Bao bì Dầu khí Việt Nam | `2723` Containers & Đóng gói | NHUA | — | THIETBI | **LOP1** |
| PGN | HNX | Công ty Cổ phần Phụ Gia Nhựa | `1353` Nhựa, cao su & sợi | NHUA | — | HOACHAT | **HOACHAT** |
| PNJ | HOSE | Công ty Cổ phần Vàng bạc Đá quý Phú Nhuận | `3767` Hàng cá nhân | DETMAY | BANLE | BANLE | **BANLE** |
| SAS | UPCOM | Công ty Cổ phần Dịch vụ Hàng không Sân bay Tân | `5379` Phân phối hàng chuyên dụ | BANLE | — | DULICH | **DULICH** |
| SAV | HOSE | Công ty Cổ phần Hợp tác Kinh tế và Xuất nhập k | `1733` Lâm sản và Chế biến gỗ | DETMAY | — | BANLE | **LOP1** |
| SBV | HOSE | Công ty Cổ phần Siam Brothers Việt Nam | `5379` Phân phối hàng chuyên dụ | BANLE | — | NHUA | **NHUA** |
| SDA | UPCOM | Công ty Cổ phần SIMCO Sông Đà | `2793` Đào tạo & Việc làm | YTE | — | THIETBI | **LOP1** |
| SGI | UPCOM | Công ty Cổ phần Đầu tư SGI Holdings | `3763` Hàng May mặc | DETMAY | — | BANLE | **DANDUNG** |
| STH | UPCOM | Công ty Cổ phần STH Holdings | `5557` Sách, ấn bản & sản phẩm  | YTE | — | BANLE | **BANLE** |
| TLG | HOSE | Công ty Cổ phần Tập đoàn Thiên Long | `3724` Đồ gia dụng một lần | DETMAY | — | BANLE | **YTE** |
| TMT | HOSE | Công ty Cổ phần Ô tô TMT | `3353` Sản xuất ô tô | BANLE | THIETBI | BANLE | **LOP1** |
| TTF | HOSE | Công ty Cổ phần Tập đoàn Kỹ nghệ Gỗ Trường Thà | `1733` Lâm sản và Chế biến gỗ | DETMAY | — | BANLE | **LOP1** |
| VEC | UPCOM | Tổng Công ty Cổ phần Điện tử và Tin học Việt N | `9572` Phần cứng | CONGNGHE | — | THIETBI | **LOP1** |
| VHG | UPCOM | Công ty Cổ phần Đầu tư và Phát triển Việt Trun | `2727` Công nghiệp phức hợp | THIETBI | — | DANDUNG | **DANDUNG** |
| VVS | HOSE | Công ty Cổ phần Đầu tư Phát triển Máy Việt Nam | `3353` Sản xuất ô tô | BANLE | — | THIETBI | **THIETBI** |
| XPH | UPCOM | Công ty Cổ phần Xà phòng Hà Nội | `3767` Hàng cá nhân | DETMAY | — | — | **HOACHAT** |

---

## G8 — Tài chính · Công nghệ · Y tế · Du lịch và mã lẻ

11 mã — đã chốt 11.

| Mã | Sàn | Doanh nghiệp | Nhánh ICB | Lớp 1 | Claude | Chủ dự án | CHỐT |
|---|---|---|---|---|---|---|---|
| DCV | UPCOM | Công ty Cổ phần Quản Lý Quỹ đầu tư Dragon Capi | `8771` Quản lý tài sản | CHUNGKHOAN | — | — | **DANDUNG** |
| DTI | UPCOM | Công ty Cổ phần Đầu tư Đức Trung | `5753` Khách sạn | DULICH | — | DANDUNG | **DANDUNG** |
| EIN | UPCOM | Công ty Cổ phần Đầu tư - Thương Mại - Dịch vụ  | `5753` Khách sạn | DULICH | — | DANDUNG | **DANDUNG** |
| F88 | UPCOM | Công ty Cổ phần Đầu tư F88 | `8773` Tài chính cá nhân | NGANHANG | — | NGANHANG | **BANLE** |
| FIT | HOSE | Công ty Cổ phần Tập đoàn F.I.T | `4577` Dược phẩm | YTE | — | DANDUNG | **DANDUNG** |
| FOC | UPCOM | Công ty Cổ phần Dịch vụ Trực tuyến FPT | `5555` Dịch vụ truyền thông | DULICH | — | CONGNGHE | **CONGNGHE** |
| HVA | UPCOM | Công ty Cổ phần Đầu tư HVA | `8775` Tài chính đặc biệt | NGANHANG | — | CHUNGKHOAN | **CONGNGHE** |
| OGC | HOSE | Công ty Cổ phần Tập đoàn Đại Dương | `8775` Tài chính đặc biệt | NGANHANG | — | DANDUNG | **DANDUNG** |
| SRA | HNX | Công ty Cổ phần SARA Việt Nam | `4535` Thiết bị y tế | YTE | — | CONGNGHE | **LOP1** |
| TIN | UPCOM | Công ty Tài chính Tổng hợp cổ phần Tín Việt | `8771` Quản lý tài sản | CHUNGKHOAN | — | NGANHANG | **NGANHANG** |
| TVC | HNX | Công ty Cổ phần Tập đoàn Quản lý tài sản T-Cor | `8775` Tài chính đặc biệt | NGANHANG | — | CHUNGKHOAN | **DANDUNG** |

---

## G9 — Không có icb_code — lớp 1 trả NULL

29 mã — đã chốt 29.

| Mã | Sàn | Doanh nghiệp | Nhánh ICB | Lớp 1 | Claude | Chủ dự án | CHỐT |
|---|---|---|---|---|---|---|---|
| AMD | UPCOM | *(không có issuer)* | *(không có)* | NULL | — | BANLE | ⛔ không gán |
| ATB | UPCOM | *(không có issuer)* | *(không có)* | NULL | — | XAYDUNG | ⛔ không gán |
| AVF | UPCOM | *(không có issuer)* | *(không có)* | NULL | — | THUYSAN | ⛔ không gán |
| BCG | UPCOM | *(không có issuer)* | *(không có)* | NULL | — | TIENICH | ⛔ không gán |
| BCR | UPCOM | *(không có issuer)* | *(không có)* | NULL | — | DANDUNG | ⛔ không gán |
| BII | UPCOM | *(không có issuer)* | *(không có)* | NULL | — | DANDUNG | ⛔ không gán |
| DPS | UPCOM | *(không có issuer)* | *(không có)* | NULL | — | XAYDUNG | ⛔ không gán |
| DTE | UPCOM | *(không có issuer)* | *(không có)* | NULL | — | TIENICH | ⛔ không gán |
| DZM | UPCOM | *(không có issuer)* | *(không có)* | NULL | — | THIETBI | ⛔ không gán |
| FLC | UPCOM | *(không có issuer)* | *(không có)* | NULL | — | DANDUNG | ⛔ không gán |
| GAB | UPCOM | *(không có issuer)* | *(không có)* | NULL | — | KHOANGSAN | ⛔ không gán |
| HAI | UPCOM | *(không có issuer)* | *(không có)* | NULL | — | HOACHAT | ⛔ không gán |
| HIG | UPCOM | *(không có issuer)* | *(không có)* | NULL | — | CONGNGHE | ⛔ không gán |
| HRT | UPCOM | *(không có issuer)* | *(không có)* | NULL | — | VANTAI | ⛔ không gán |
| HVG | UPCOM | *(không có issuer)* | *(không có)* | NULL | — | THUYSAN | ⛔ không gán |
| IBC | UPCOM | *(không có issuer)* | *(không có)* | NULL | — | YTE | ⛔ không gán |
| KLF | UPCOM | *(không có issuer)* | *(không có)* | NULL | — | DULICH | ⛔ không gán |
| KSH | UPCOM | *(không có issuer)* | *(không có)* | NULL | — | KHOANGSAN | ⛔ không gán |
| LCS | UPCOM | *(không có issuer)* | *(không có)* | NULL | — | XAYDUNG | ⛔ không gán |
| LTG | UPCOM | *(không có issuer)* | *(không có)* | NULL | — | HOACHAT | ⛔ không gán |
| NHP | UPCOM | *(không có issuer)* | *(không có)* | NULL | — | THIETBI | ⛔ không gán |
| RDP | UPCOM | *(không có issuer)* | *(không có)* | NULL | — | NHUA | ⛔ không gán |
| ROS | UPCOM | *(không có issuer)* | *(không có)* | NULL | — | XAYDUNG | ⛔ không gán |
| SRT | UPCOM | *(không có issuer)* | *(không có)* | NULL | — | VANTAI | ⛔ không gán |
| SSN | UPCOM | *(không có issuer)* | *(không có)* | NULL | — | NONGNGHIEP | ⛔ không gán |
| TKG | UPCOM | *(không có issuer)* | *(không có)* | NULL | — | KHOANGSAN | ⛔ không gán |
| TS4 | UPCOM | *(không có issuer)* | *(không có)* | NULL | — | THUYSAN | ⛔ không gán |
| VCW | UPCOM | *(không có issuer)* | *(không có)* | NULL | — | TIENICH | ⛔ không gán |
| VOC | UPCOM | *(không có issuer)* | *(không có)* | NULL | — | THUCPHAM | ⛔ không gán |

