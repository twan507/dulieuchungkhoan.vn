# Bảng map ngành — ICB → 24 ngành riêng

> ⚠️ **File này sinh tự động** từ [`gen_industry_mapping.py`](gen_industry_mapping.py). Sửa nội dung thì sửa trong script rồi chạy lại — **cấm sửa tay**. Bản máy đọc: [`industry-mapping.json`](industry-mapping.json).

**Trạng thái:** ✅ chốt 2026-08-27, chủ dự án duyệt từng nhóm chủ đề. File này là **chủ sở hữu duy nhất** của nội dung map; [industry-tree.md](industry-tree.md) sở hữu cây 24 ngành, không chép bảng này.

## 1. Hai lớp

| Lớp | Bảng | Ai ghi | Luật |
|---|---|---|---|
| **1 · máy** | `market.industry_icb_map` → `market.issuer.industry_id` | job `etl refdata`, mỗi lượt | khớp `icb_code` chính xác trước; không có thì leo `icb_code_path` lấy **tổ tiên gần nhất** |
| **2 · tay** | `market.issuer_industry_override` | người, qua migration seed | ETL không đọc, không ghi |
| **đọc** | view `market.v_issuer_industry` | — | `COALESCE(lớp 2, lớp 1)` |

Vì luật phân giải leo từ dưới lên, **dòng cấp 4 thắng dòng cấp 3 cùng nhánh**, còn dòng cấp 3 làm lưới hứng cho mọi con cháu chưa có dòng riêng — kể cả mã ICB lá chưa từng xuất hiện. Đây là lý do bảng trộn hai cấp thay vì dùng cấp-4-thuần.

🔴 **Cổ phiếu không có issuer thì không gán ngành.** Ngành gán ở doanh nghiệp, mã thừa hưởng — không có issuer thì không có hàng nào để gắn, ở cả hai lớp. 437 mã trong kho thuộc diện này *(đo 2026-08-27)*, đều đã huỷ niêm yết.

🔴 **Ba ngành tài chính khoá theo mẫu BCTC.** `com_type_code = NH` ⟺ `NGANHANG`, `CK` ⟺ `CHUNGKHOAN`, `BH` ⟺ `BAOHIEM` — ràng buộc hai chiều, không ngoại lệ. Ba nhóm này là ba **biểu mẫu báo cáo tài chính** khác nhau, không so sánh chỉ tiêu với doanh nghiệp thường được.

## 2. Lớp 1 — 56 dòng

Dòng `L4` thụt vào là ngoại lệ của nhánh ngay trên nó.

| Cấp | Mã ICB | Tên nhánh ICB | → Ngành | Vì sao |
|---|---|---|---|---|
| L3 | `0530` | Sản xuất Dầu khí | **DAUKHI** | lọc dầu + phân phối (BSR, OIL, PLX) |
| L3 | `0570` | Thiết bị, Dịch vụ và Phân phối Dầu khí | **DAUKHI** | thiết bị và dịch vụ dầu khí |
| L3 | `0580` | Năng lượng thay thế | **TIENICH** | Năng lượng thay thế — chưa có DN; ở VN là nhà phát điện tái tạo |
| L3 | `1350` | Hóa chất | **HOACHAT** | nền là hóa dầu/nông dược 1357; nhựa-cao su tách ở 1353 |
| L4 | ⤷ `1353` | Nhựa, cao su & sợi | **NHUA** | tách khỏi 1350 — nhựa/sợi; cao su thiên nhiên bóc ở lớp 2 |
| L3 | `1730` | Lâm nghiệp và Giấy | **DETMAY** | nền là gỗ nội thất 1733 — giải luôn ca TTF/ACG/SAV; giấy tách ở 1737 |
| L4 | ⤷ `1737` | Sản xuất giấy | **NHUA** | tách khỏi 1730 — giấy & bao bì giấy (DHC, HHP) |
| L3 | `1750` | Kim loại | **KIMLOAI** | thép + nhôm + kim loại màu |
| L3 | `1770` | Khai khoáng | **KHOANGSAN** | khai khoáng + than + vàng |
| L3 | `2350` | Xây dựng và Vật liệu | **XAYDUNG** | nền của nhánh; vật liệu tách ở dòng 2353 |
| L4 | ⤷ `2353` | Vật liệu xây dựng & Nội thất | **VATLIEU** | tách khỏi 2350 — vật liệu & nội thất |
| L3 | `2710` | Hàng không & Quốc phòng | **THIETBI** | Hàng không & Quốc phòng — chưa có DN; là CHẾ TẠO máy bay, không phải hãng bay |
| L3 | `2720` | Hàng công nghiệp | **NHUA** | nền là bao bì 2723; phức hợp tách ở 2727 |
| L4 | ⤷ `2727` | Công nghiệp phức hợp | **THIETBI** | tách khỏi 2720 — công nghiệp phức hợp |
| L3 | `2730` | Điện tử & Thiết bị điện | **THIETBI** | thiết bị điện + hàng điện tử |
| L3 | `2750` | Công nghiệp nặng | **THIETBI** | máy công nghiệp + đóng tàu |
| L3 | `2770` | Vận tải | **VANTAI** | cả 5 nhánh con đều là vận tải/kho bãi |
| L3 | `2790` | Tư vấn & Hỗ trợ Kinh doanh | **TIENICH** | nền là môi trường đô thị 2799 — chủ dự án chốt 2026-08-27 |
| L4 | ⤷ `2791` | Tư vấn & Hỗ trợ KD | **XAYDUNG** | tách khỏi 2790 — tư vấn xây lắp điện (TV1-TV4, PPE, VNC) |
| L4 | ⤷ `2793` | Đào tạo & Việc làm | **YTE** | tách khỏi 2790 — đào tạo & việc làm |
| L4 | ⤷ `2797` | Nhà cung cấp thiết bị | **THIETBI** | tách khỏi 2790 — nhà cung cấp thiết bị |
| L3 | `3350` | Ô tô và phụ tùng | **BANLE** | nền là đại lý ô tô 3353, 6/7 mã HOSE là đại lý — chốt 2026-08-27; lốp tách ở 3357 |
| L4 | ⤷ `3355` | Phụ tùng ô tô | **THIETBI** | tách khỏi 3350 — phụ tùng ô tô |
| L4 | ⤷ `3357` | Lốp xe | **CAOSU** | tách khỏi 3350 — săm lốp (CSM, DRC, SRC) |
| L3 | `3530` | Bia và đồ uống | **THUCPHAM** | bia + đồ uống + rượu |
| L3 | `3570` | Sản xuất thực phẩm | **THUCPHAM** | nền là chế biến 3577; nuôi trồng tách ở dòng 3573 |
| L4 | ⤷ `3573` | Nuôi trồng nông & hải sản | **THUYSAN** | tách khỏi 3570 — thủy sản là đa số 29/45; 16 mã nông nghiệp bóc ở lớp 2 |
| L3 | `3720` | Hàng gia dụng | **DETMAY** | hàng gia dụng — giải luôn ca GDT |
| L3 | `3740` | Hàng hóa giải trí | **DETMAY** | hàng hóa giải trí; điện tử tiêu dùng tách ở 3743 |
| L4 | ⤷ `3743` | Điện tử tiêu dùng | **THIETBI** | tách khỏi 3740 — điện tử tiêu dùng |
| L3 | `3760` | Hàng cá nhân | **DETMAY** | may mặc 47 + hàng cá nhân 8 + giày dép 2 |
| L3 | `3780` | Thuốc lá | **THUCPHAM** | thuốc lá |
| L3 | `4530` | Thiết bị và Dịch vụ Y tế | **YTE** | thiết bị + dụng cụ + chăm sóc y tế |
| L3 | `4570` | Dược phẩm | **YTE** | dược phẩm + công nghệ sinh học |
| L3 | `5330` | Phân phối thực phẩm & dược phẩm | **BANLE** | phân phối thực phẩm & dược phẩm |
| L3 | `5370` | Bán lẻ | **BANLE** | bán lẻ phức hợp + phân phối chuyên dụng |
| L3 | `5550` | Truyền thông | **YTE** | nền là sách/ấn bản giáo dục 5557 — chốt 2026-08-27 |
| L4 | ⤷ `5553` | Giải trí & Truyền thông | **DULICH** | tách khỏi 5550 — giải trí & truyền thông (YEG, VNZ) |
| L4 | ⤷ `5555` | Dịch vụ truyền thông | **DULICH** | tách khỏi 5550 — dịch vụ truyền thông |
| L3 | `5750` | Du lịch & Giải trí | **DULICH** | gồm 5751 dịch vụ hàng không — tên ngành đã có "Hàng không" |
| L3 | `6530` | Viễn thông cố định | **CONGNGHE** | viễn thông cố định |
| L3 | `6570` | Viễn thông di động | **CONGNGHE** | viễn thông di động |
| L3 | `7530` | Sản xuất & Phân phối Điện | **TIENICH** | sản xuất & phân phối điện |
| L3 | `7570` | Nước & Khí đốt | **TIENICH** | nền là nước 7577; xăng dầu-khí tách ở dòng 7573 |
| L4 | ⤷ `7573` | Phân phối xăng dầu & khí đốt | **DAUKHI** | tách khỏi 7570 — xăng dầu & LPG, theo giá dầu (chốt 2026-08-27) |
| L3 | `8350` | Ngân hàng | **NGANHANG** |  |
| L3 | `8530` | Bảo hiểm phi nhân thọ | **BAOHIEM** | phi nhân thọ + tái bảo hiểm |
| L3 | `8570` | Bảo hiểm nhân thọ | **BAOHIEM** | bảo hiểm nhân thọ (BVH) |
| L3 | `8630` | Bất động sản | **DANDUNG** | gồm cả tư vấn/môi giới 8637; KCN ICB không tách → lớp 2 |
| L3 | `8670` | Quỹ ủy thác BĐS | **DANDUNG** | Quỹ ủy thác BĐS — chưa có DN |
| L3 | `8770` | Dịch vụ tài chính | **CHUNGKHOAN** | nền là môi giới 8777; tín dụng tách ở 8775/8773 |
| L4 | ⤷ `8773` | Tài chính cá nhân | **NGANHANG** | tách khỏi 8770 — tài chính tiêu dùng (EVF, F88) |
| L4 | ⤷ `8775` | Tài chính đặc biệt | **NGANHANG** | tách khỏi 8770 — tài chính đặc biệt |
| L3 | `8980` | Quỹ đầu tư | **— không nạp** | KHÔNG NẠP — 24 chứng chỉ quỹ; ETF/quỹ không có ngành |
| L3 | `9530` | Phần mềm & Dịch vụ Máy tính | **CONGNGHE** | phần mềm + dịch vụ máy tính + internet |
| L3 | `9570` | Thiết bị và Phần cứng | **CONGNGHE** | thiết bị viễn thông + phần cứng |

## 3. Lớp 2 — 161 dòng gán tay

Xếp theo ngành. Mã nào cả lớp 1 lẫn phán đoán tay cùng một ngành thì **không có mặt ở đây** — đưa vào là đóng băng lớp 1, sửa map ICB về sau sẽ không lan tới được.

### NGANHANG — Ngân hàng và Tín dụng · 1 mã

| Mã | Doanh nghiệp | Vì sao đè |
|---|---|---|
| `TIN` | Công ty Tài chính Tổng hợp cổ phần Tín Việt | luật BCTC com_type=NH lớp 1 đưa nhầm sang CHUNGKHOAN |

### DANDUNG — Bất động sản Dân dụng · 21 mã

| Mã | Doanh nghiệp | Vì sao đè |
|---|---|---|
| `CIG` | Công ty Cổ phần COMA 18 | G5b theo chủ dự án BĐS |
| `CSC` | Công ty Cổ phần Tập đoàn COTANA | G5b COTANA BĐS |
| `DCV` | Công ty Cổ phần Quản Lý Quỹ đầu tư Dragon Capital Việt Nam | luật BCTC CT công ty quản lý quỹ không dùng mẫu BCTC CK |
| `DLG` | Công ty Cổ phần Tập đoàn Đức Long Gia Lai | G5b Đức Long Gia Lai holding BĐS BOT |
| `DTI` | Công ty Cổ phần Đầu tư Đức Trung | G8 theo chủ dự án độ tin cậy thấp |
| `EIN` | Công ty Cổ phần Đầu tư - Thương Mại - Dịch vụ Điện lực | G8 theo chủ dự án độ tin cậy thấp |
| `FID` | Công ty Cổ phần Đầu tư và Phát triển Doanh nghiệp Việt Nam | luật BCTC com_type=CT không được vào CHUNGKHOAN holding có sàn BĐS |
| `FIT` | Công ty Cổ phần Tập đoàn F.I.T | G8 F.I.T Group holding dược nước khoáng BĐS nông nghiệp |
| `GEL` | Công ty Cổ phần Hạ tầng GELEX | G5d chủ dự án chốt BĐS không xếp KCN |
| `HHS` | Công ty Cổ phần Đầu tư Dịch vụ Hoàng Huy | G7 Hoàng Huy nay là BĐS Hải Phòng |
| `IPA` | Công ty Cổ phần Tập đoàn Đầu tư I.P.A | G5d luật BCTC com_type=CT holding mẹ của VND |
| `KPF` | Công ty Cổ phần Đầu tư Tài sản KOJI | luật BCTC com_type=CT holding đầu tư tài sản |
| `L14` | Công ty Cổ phần Licogi 14 | G5b Licogi 14 BĐS và đầu tư |
| `LAI` | Công ty Cổ phần Đầu tư Xây dựng Long An IDICO | G5b theo chủ dự án |
| `NHA` | Tổng Công ty Đầu tư Phát triển Nhà và Đô thị Nam Hà Nội | G5b Nhà và Đô thị Nam Hà Nội |
| `OGC` | Công ty Cổ phần Tập đoàn Đại Dương | luật BCTC CT Đại Dương BĐS và khách sạn qua OCH |
| `PFL` | Công ty Cổ phần Dầu khí Đông Đô | G5b Dầu khí Đông Đô BĐS |
| `PGT` | Công ty Cổ phần PGT Holdings | G6 tra web nay là holding M&A BĐS khách sạn không còn taxi |
| `SGI` | Công ty Cổ phần Đầu tư SGI Holdings | G7 tra web holding sản xuất tài chính BĐS độ tin cậy thấp |
| `TVC` | Công ty Cổ phần Tập đoàn Quản lý tài sản T-Corp | luật BCTC CT holding T Corp |
| `VHG` | Công ty Cổ phần Đầu tư và Phát triển Việt Trung Nam | G7 theo chủ dự án độ tin cậy thấp |

### KHUCONGNGHIEP — Bất động sản Khu công nghiệp · 34 mã

| Mã | Doanh nghiệp | Vì sao đè |
|---|---|---|
| `BAX` | Công ty Cổ phần Thống Nhất | chủ KCN Bàu Xéo |
| `BCM` | Tập đoàn Đầu tư và Phát triển Công nghiệp Becamex - CTCP | 1a cả hai cùng KCN |
| `CCL` | Công ty Cổ phần Đầu tư và Phát triển Đô thị Dầu khí Cửu Long | 1b theo chủ dự án |
| `CRE` | Công ty Cổ phần Bất động sản Thế Kỷ | nguồn uy tín |
| `D2D` | Công ty Cổ phần Phát triển Đô thị Công nghiệp số 2 | 1a cả hai cùng KCN |
| `DPR` | Công ty Cổ phần Cao su Đồng Phú | 1d ăn sóng BĐS KCN do chuyển đổi đất |
| `DRH` | Công ty Cổ phần DRH Holdings | nguồn uy tín |
| `DTD` | Công ty Cổ phần Đầu tư Phát triển Thành Đạt | 1b theo chủ dự án |
| `GVR` | Tập đoàn Công nghiệp Cao su Việt Nam - Công ty Cổ phần | 1d ăn sóng BĐS KCN do chuyển đổi đất |
| `HAR` | Công ty Cổ phần Đầu tư Thương mại Bất động sản An Dương Thảo Điền | 1b theo chủ dự án |
| `HPI` | Công ty Cổ phần Khu công nghiệp Hiệp Phước | nguồn uy tín |
| `IDC` | Tổng Công ty IDICO - CTCP | 1a cả hai cùng KCN |
| `IDV` | Công ty Cổ phần Phát triển Hạ tầng Vĩnh Phúc | nguồn uy tín |
| `ITA` | Công ty Cổ phần Đầu tư và Công nghiệp Tân Tạo | nguồn uy tín |
| `KBC` | Tổng Công ty Phát triển Đô thị Kinh Bắc - CTCP | 1a cả hai cùng KCN |
| `KOS` | Công ty Cổ phần KOSY | 1b theo chủ dự án |
| `LHG` | Công ty Cổ phần Long Hậu | 1a cả hai cùng KCN |
| `MH3` | Công ty Cổ phần Khu công nghiệp Cao su Bình Long | tên là KCN |
| `NTC` | Công ty Cổ phần Khu Công nghiệp Nam Tân Uyên | nguồn uy tín |
| `NTL` | Công ty Cổ phần Phát triển Đô thị Từ Liêm | nguồn uy tín |
| `PHR` | Công ty Cổ phần Cao su Phước Hòa | 1d ăn sóng BĐS KCN do chuyển đổi đất |
| `PXL` | Công ty Cổ phần Đầu tư Khu Công Nghiệp Dầu khí Long Sơn | tên là KCN |
| `SIP` | Công ty Cổ phần Đầu tư Sài Gòn VRG | 1a cả hai cùng KCN |
| `SNZ` | Tổng Công ty Cổ phần Phát triển Khu Công nghiệp | nguồn uy tín |
| `SZB` | Công ty Cổ phần Sonadezi Long Bình | cùng họ Sonadezi |
| `SZC` | Công ty Cổ phần Sonadezi Châu Đức | 1a cả hai cùng KCN |
| `SZG` | Công ty Cổ phần Sonadezi Giang Điền | cùng họ Sonadezi |
| `SZL` | Công ty Cổ phần Sonadezi Long Thành | nguồn uy tín |
| `TID` | Công ty Cổ phần Tổng Công ty Tín Nghĩa | holding mẹ của TIP |
| `TIP` | Công ty Cổ phần Phát triển Khu công nghiệp Tín Nghĩa | 1a cả hai cùng KCN |
| `TIX` | Công ty Cổ phần Sản xuất Kinh doanh Xuất nhập khẩu Dịch vụ và Đầu tư Tân Bình | nguồn uy tín |
| `VC3` | Công ty Cổ phần Tập đoàn Nam Mê Kông | nguồn uy tín |
| `VGC` | Tổng Công ty Viglacera - Công ty Cổ phần | 1a cả hai cùng KCN dù ICB xếp vật liệu |
| `VRG` | Công ty Cổ phần Phát triển Đô thị và Khu Công nghiệp Cao Su Việt Nam | tên là KCN |

### XAYDUNG — Thi công Xây dựng · 10 mã

| Mã | Doanh nghiệp | Vì sao đè |
|---|---|---|
| `ACC` | Công ty Cổ phần Đầu tư và Xây dựng Bình Dương ACC | G5a xây lắp Bình Dương |
| `AMS` | Công ty Cổ phần Cơ khí Xây dựng AMECC | G5d AMECC kết cấu thép công trình |
| `BDT` | Công ty Cổ phần Xây lắp và Vật liệu xây dựng Đồng Tháp | G5a xây lắp Đồng Tháp |
| `BIG` | Công ty Cổ phần Tập đoàn Đầu tư BIG | G3a BIG Invest Group đầu tư xây dựng ICB xếp sai |
| `CVN` | Công ty Cổ phần Vinam | G5d Vinam xây dựng dân dụng ICB xếp thiết bị y tế là sai |
| `DGT` | Công ty Cổ phần Công trình Giao thông Đồng Nai | G5a công trình giao thông |
| `DID` | Công ty Cổ phần DIC - Đồng Tiến | G5a xây lắp họ DIC |
| `THG` | Công ty Cổ phần Đầu tư và Xây dựng Tiền Giang | G5a xây dựng Tiền Giang |
| `TLD` | Công ty Cổ phần Đầu tư Xây dựng và Phát triển Đô thị Thăng Long | G5a xây dựng đô thị Thăng Long |
| `XMC` | Công ty cổ phần Đầu tư và Xây dựng Xuân Mai | G5a xây dựng Xuân Mai |

### VATLIEU — Vật liệu Xây dựng · 1 mã

| Mã | Doanh nghiệp | Vì sao đè |
|---|---|---|
| `PTB` | Công ty Cổ phần Phú Tài | G5d Phú Tài đá granite theo chủ dự án |

### KHOANGSAN — Than và Khoáng sản · 4 mã

| Mã | Doanh nghiệp | Vì sao đè |
|---|---|---|
| `HMR` | Công ty Cổ phần Đá Hoàng Mai | G5a khai thác mỏ đá cùng luật với KSB và TTZ |
| `KSB` | Công ty Cổ phần Khoáng sản và Xây dựng Bình Dương | G4 B mỏ đá thật |
| `TTZ` | Công ty Cổ phần Đầu tư Xây dựng và Công nghệ Tiến Trung | G5d tra web khai thác cát đá sỏi Thái Bình |
| `VTV` | Công ty Cổ phần Năng lượng và Môi trường VICEM | G5a VICEM EE cấp 100% than cho 4 nhà máy xi măng thương mại theo mặt hàng |

### HOACHAT — Hóa chất và Phân bón · 4 mã

| Mã | Doanh nghiệp | Vì sao đè |
|---|---|---|
| `LIX` | Công ty Cổ phần Bột Giặt LIX | G7 bột giặt thực chất là hóa chất chủ dự án chốt |
| `NET` | Công ty Cổ phần Bột giặt Net | G7 bột giặt Net cùng luật với LIX |
| `PGN` | Công ty Cổ phần Phụ Gia Nhựa | G7 phụ gia nhựa là hóa chất không phải nhựa |
| `XPH` | Công ty Cổ phần Xà phòng Hà Nội | G7 Xà phòng Hà Nội cùng nhánh 3767 cùng luật |

### NHUA — Nhựa, Bao bì và Giấy · 4 mã

| Mã | Doanh nghiệp | Vì sao đè |
|---|---|---|
| `BMP` | Công ty Cổ phần Nhựa Bình Minh | G5d Nhựa Bình Minh chạy theo giá hạt nhựa PVC |
| `NTP` | Công ty Cổ phần Nhựa Thiếu niên Tiền Phong | G5d Nhựa Tiền Phong |
| `SBV` | Công ty Cổ phần Siam Brothers Việt Nam | G7 Siam Brothers dây thừng lưới đánh cá từ nhựa PP PE |
| `VKC` | Công ty Cổ phần VKC Holdings | G2 thực chất cáp và ống nhựa không phải lốp |

### THIETBI — Thiết bị Điện và Máy móc · 4 mã

| Mã | Doanh nghiệp | Vì sao đè |
|---|---|---|
| `DQC` | Công ty Cổ phần Tập đoàn Điện Quang | G7 Điện Quang sản xuất bóng đèn thiết bị chiếu sáng cùng luật với MBG |
| `MBG` | Công ty Cổ phần Tập đoàn MBG | G5d sản xuất thiết bị chiếu sáng và thiết bị điện |
| `SVT` | Công ty Cổ phần Công nghệ Sài Gòn Viễn Đông | G4 B Savitech cơ khí chế tạo xe đạp xe máy phụ tùng |
| `VVS` | Công ty Cổ phần Đầu tư Phát triển Máy Việt Nam | G7 Đầu tư Phát triển Máy Việt Nam |

### NONGNGHIEP — Nông nghiệp và Chăn nuôi · 29 mã

| Mã | Doanh nghiệp | Vì sao đè |
|---|---|---|
| `AAN` | Công ty Cổ phần Lương thực A An | G3a nông nghiệp bóc khỏi 3573 sau khi đảo |
| `AFX` | Công ty Cổ phần Xuất Nhập khẩu Nông sản Thực phẩm An Giang | G3b B1 |
| `AGM` | Công ty Cổ phần Xuất nhập khẩu An Giang | G3b B1 lợi nhuận chạy theo giá nông sản |
| `APC` | Công ty Cổ phần Chiếu xạ An Phú | G7 chiếu xạ nông sản thủy sản xuất khẩu CAN XAC NHAN |
| `BAF` | Công ty Cổ phần Nông nghiệp BAF Việt Nam | G3a nông nghiệp bóc khỏi 3573 sau khi đảo |
| `CET` | Công ty Cổ phần HTC Holding | G3b B2 |
| `CNA` | Công ty Cổ phần Tổng công ty Chè Nghệ An | G3a nông nghiệp bóc khỏi 3573 sau khi đảo |
| `DBC` | Công ty Cổ phần Tập đoàn Dabaco Việt Nam | G3a nông nghiệp bóc khỏi 3573 sau khi đảo |
| `DMN` | Công ty Cổ phần Domenal | G3a nông nghiệp bóc khỏi 3573 sau khi đảo |
| `GPC` | Công ty Cổ phần Tập đoàn Green+ | G3b B2 |
| `HAG` | Công ty Cổ phần Hoàng Anh Gia Lai | G3a nông nghiệp bóc khỏi 3573 sau khi đảo |
| `HKB` | Công ty Cổ phần Nông nghiệp và Thực phẩm Hà Nội - Kinh Bắc | G3b B1 |
| `HNG` | Công ty Cổ phần Nông nghiệp Quốc tế Hoàng Anh Gia Lai | G3a nông nghiệp bóc khỏi 3573 sau khi đảo |
| `HPA` | Công ty Cổ phần Phát triển Nông nghiệp Hoà Phát | G3a nông nghiệp bóc khỏi 3573 sau khi đảo |
| `HSL` | Công ty Cổ phần Đầu tư Phát triển Thực phẩm Hồng Hà | G3b B1 |
| `ILA` | Công ty Cổ phần ILA | G3b B2 |
| `KGM` | Công ty Cổ phần Xuất nhập khẩu Kiên Giang | G3b B1 |
| `MLS` | Công ty Cổ phần Chăn nuôi - Mitraco | G3a nông nghiệp bóc khỏi 3573 sau khi đảo |
| `NCG` | Công ty Cổ phần Đầu tư Anova Agri | G3a Anova Agri là thức ăn chăn nuôi và thú y |
| `NDF` | Công ty Cổ phần Chế biến thực phẩm nông sản xuất khẩu Nam Định | G3b B1 |
| `NHV` | Công ty Cổ phần Sức khỏe Hồi sinh Việt Nam | G3b B3 |
| `NSC` | Công ty Cổ phần Tập đoàn Giống cây trồng Việt Nam | G3a nông nghiệp bóc khỏi 3573 sau khi đảo |
| `NSS` | Công ty Cổ phần Nông súc sản Đồng Nai | G3a nông nghiệp bóc khỏi 3573 sau khi đảo |
| `PSL` | Công ty Cổ phần Chăn nuôi Phú Sơn | G3a nông nghiệp bóc khỏi 3573 sau khi đảo |
| `SSC` | Công ty Cổ phần Giống cây trồng Miền Nam | G3a nông nghiệp bóc khỏi 3573 sau khi đảo |
| `TAR` | Công ty Cổ phần Nông nghiệp Công nghệ cao Trung An | G3a nông nghiệp bóc khỏi 3573 sau khi đảo |
| `TCJ` | Công ty Cổ phần Tô Châu | G3a nông nghiệp bóc khỏi 3573 sau khi đảo |
| `TT6` | Công ty Cổ Phần Tập Đoàn Tiến Thịnh | G3b B1 |
| `VLC` | Tổng Công ty Chăn nuôi Việt Nam - Công ty Cổ phần | G3a nông nghiệp bóc khỏi 3573 sau khi đảo |

### THUYSAN — Chế biến Thủy sản · 1 mã

| Mã | Doanh nghiệp | Vì sao đè |
|---|---|---|
| `CMM` | Công ty Cổ phần Camimex | G3a Camimex nằm ở 3577 nên vẫn cần đè |

### DETMAY — Dệt may, Gỗ và Gia dụng · 2 mã

| Mã | Doanh nghiệp | Vì sao đè |
|---|---|---|
| `DDB` | Công ty Cổ Phần Thương Mại Và Xây Dựng Đông Dương | G5d Đông Dương sản xuất sản phẩm từ gỗ |
| `SBB` | Công ty Cổ phần Tập đoàn Bia Sài Gòn Bình Tây | G3b chủ dự án chốt giữ phân loại cũ |

### CAOSU — Cao su và Săm lốp · 11 mã

| Mã | Doanh nghiệp | Vì sao đè |
|---|---|---|
| `BRC` | Công ty Cổ phần Cao su Bến Thành | G2 cao su thiên nhiên ICB xếp nhầm 1353 |
| `BRR` | Công ty Cổ phần Cao su Bà Rịa | G2 cao su thiên nhiên ICB xếp nhầm 1353 |
| `DRG` | Công ty Cổ phần Cao su Đắk Lắk | G2 cao su thiên nhiên ICB xếp nhầm 1353 |
| `DRI` | Công ty Cổ phần Đầu tư Cao su Đắk Lắk | G2 cao su thiên nhiên ICB xếp nhầm 1353 |
| `HRC` | Công ty Cổ phần Cao su Hòa Bình | G2 cao su thiên nhiên ICB xếp nhầm 1353 |
| `IRC` | Công ty Cổ phần Cao su Công nghiệp | G2 cao su thiên nhiên ICB xếp nhầm 1353 |
| `RBC` | Công ty Cổ phần Công Nghiệp và Xuất nhập khẩu Cao Su | G2 cao su thiên nhiên ICB xếp nhầm 1353 |
| `RTB` | Công ty Cổ phần Cao su Tân Biên | G2 cao su thiên nhiên ICB xếp nhầm 1353 |
| `SBR` | Công ty Cổ phần Cao su Sông Bé | G2 cao su thiên nhiên ICB xếp nhầm 1353 |
| `TNC` | Công ty Cổ phần Cao su Thống Nhất | G2 cao su thiên nhiên ICB xếp nhầm 1353 |
| `TRC` | Công ty Cổ phần Cao su Tây Ninh | G2 cao su thiên nhiên ICB xếp nhầm 1353 |

### BANLE — Bán buôn và Bán lẻ · 5 mã

| Mã | Doanh nghiệp | Vì sao đè |
|---|---|---|
| `F88` | Công ty Cổ phần Đầu tư F88 | luật BCTC CT chuỗi cửa hàng cầm đồ |
| `PNJ` | Công ty Cổ phần Vàng bạc Đá quý Phú Nhuận | G7 bán lẻ trang sức cả hai nguồn đồng ý |
| `SHN` | Công ty Cổ phần Đầu tư Tổng hợp Hà Nội | G4 C HANIC thương mại VLXD và XNK mã than của ICB đã lỗi thời |
| `STH` | Công ty Cổ phần STH Holdings | G7 theo chủ dự án độ tin cậy thấp |
| `TTH` | Công ty Cổ phần Thương mại và Dịch vụ Tiến Thành | G4 D thời trang Valentino và khoáng sản ICB xếp thép là sai |

### DULICH — Hàng không, Du lịch và Truyền thông · 5 mã

| Mã | Doanh nghiệp | Vì sao đè |
|---|---|---|
| `ACV` | Tổng Công ty Cảng Hàng không Việt Nam - CTCP | G6 cảng hàng không tên ngành đã có Hàng không |
| `AST` | Công ty Cổ phần Dịch vụ Hàng không Taseco | G7 bán lẻ trong sân bay cùng luật với SCS |
| `CIA` | Công ty Cổ Phần Dịch Vụ Sân Bay Quốc Tế Cam Ranh | G6 dịch vụ sân bay Cam Ranh |
| `OCH` | Công ty Cổ phần One Capital Hospitality | G3b chủ dự án chốt One Capital Hospitality đã xoay sang khách sạn |
| `SAS` | Công ty Cổ phần Dịch vụ Hàng không Sân bay Tân Sơn Nhất | G7 SASCO bán lẻ sân bay Tân Sơn Nhất |

### YTE — Y tế, Giáo dục và Xuất bản · 1 mã

| Mã | Doanh nghiệp | Vì sao đè |
|---|---|---|
| `TLG` | Công ty Cổ phần Tập đoàn Thiên Long | G7 Thiên Long văn phòng phẩm giáo dục cùng mùa khai giảng CAN XAC NHAN |

### TIENICH — Điện, Nước và Môi trường · 6 mã

| Mã | Doanh nghiệp | Vì sao đè |
|---|---|---|
| `DDG` | Công ty Cổ phần Đầu tư Công nghiệp Xuất nhập khẩu Đông Dương | G6 tra web cung cấp hơi nhiệt điện công nghiệp và nhiên liệu biomass |
| `PC1` | Công ty Cổ phần Tập đoàn PC1 | G5c lợi nhuận chính từ thủy điện và điện gió |
| `TV1` | Công ty Cổ phần Tư vấn Xây dựng Điện 1 | G5c tư vấn thiết kế công trình điện theo chu kỳ đầu tư ngành điện |
| `TV2` | Công ty Cổ phần Tư vấn Xây dựng Điện 2 | G5c nt |
| `TV3` | Công ty Cổ phần Tư vấn Xây dựng Điện 3 | G5c nt danh sách cũ ghi THIETBI có vẻ nhầm |
| `VIW` | Tổng công ty Đầu tư Nước và Môi trường Việt Nam - Công ty Cổ phần | G5c VIWASEEN cấp nước |

### DAUKHI — Dầu mỏ và Khí đốt · 9 mã

| Mã | Doanh nghiệp | Vì sao đè |
|---|---|---|
| `GSP` | Công ty Cổ phần Vận tải Sản phẩm Khí Quốc tế | G6 vận tải sản phẩm khí theo luật tên dầu khí |
| `PLC` | Tổng Công ty Hóa dầu Petrolimex - Công ty Cổ phần | G6 hóa dầu Petrolimex dầu nhờn nhựa đường |
| `PSP` | Công ty Cổ phần Cảng Dịch vụ Dầu khí Đình Vũ | G6 cảng dịch vụ dầu khí |
| `PVM` | Công ty Cổ phần Máy - Thiết bị Dầu khí | G6 máy thiết bị dầu khí |
| `PVO` | Công ty Cổ phần Dầu nhờn PV Oil | G6 dầu nhờn PV Oil |
| `PVP` | Công ty Cổ phần Vận tải Dầu khí Thái Bình Dương | G6 nt |
| `PVT` | Tổng Công ty Cổ phần Vận tải Dầu khí | G6 nt lưu ý PVT là đội tàu chở dầu lớn nhất VN |
| `PVV` | Công ty Cổ phần Vinaconex 39 | G5d chủ dự án chốt theo tên Dầu khí |
| `PVX` | Tổng Công ty Cổ phần Xây lắp Dầu khí Việt Nam | G5d chủ dự án chốt theo tên Dầu khí |

### VANTAI — Vận tải, Cảng biển và Kho bãi · 5 mã

| Mã | Doanh nghiệp | Vì sao đè |
|---|---|---|
| `HHG` | Công ty Cổ phần Hoàng Hà | G7 Hoàng Hà xe khách tuyến cố định cùng luật với VNS |
| `MAC` | Công ty Cổ phần Tập đoàn Macstar | G6 Macstar tiền thân cung ứng dịch vụ kỹ thuật hàng hải |
| `SKG` | Công ty Cổ phần Tàu Cao tốc Superdong - Kiên Giang | G6 tàu cao tốc chở khách |
| `TCO` | Công ty Cổ phần Janus Group | G3a Janus Group tiền thân Vận tải Duyên Hải ICB xếp sai |
| `VNS` | Công ty Cổ phần Ánh Dương Việt Nam | G6 Vinasun taxi |

### CONGNGHE — Công nghệ Thông tin và Viễn thông · 4 mã

| Mã | Doanh nghiệp | Vì sao đè |
|---|---|---|
| `CTR` | Tổng Công ty Cổ phần Công trình Viettel | G5d Viettel Construction hạ tầng viễn thông và towerco |
| `FOC` | Công ty Cổ phần Dịch vụ Trực tuyến FPT | G8 FPT Online quảng cáo trực tuyến và nội dung số |
| `HVA` | Công ty Cổ phần Đầu tư HVA | luật BCTC CT fintech cho vay ngang hàng |
| `VTK` | Công ty Cổ phần Tư vấn và Dịch vụ Viettel | G5d Tư vấn và Dịch vụ Viettel |

