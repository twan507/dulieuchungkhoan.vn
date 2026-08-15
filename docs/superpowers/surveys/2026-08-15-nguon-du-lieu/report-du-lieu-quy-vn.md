# Dữ liệu quỹ Việt Nam — nguồn nào có gì, có giá trị không · đo 2026-08-15

Câu hỏi chủ dự án: rà lại các nguồn đã khảo sát, xem chỗ nào ghi dữ liệu quỹ ở VN, dữ liệu cụ thể thế nào, **có giá trị không**.

## 0. Kết luận

**Có giá trị, và có một thứ hẳn hoi mà dự án chưa biết mình đang có: `iNav` của FiinTrade** — cho phép tính **chênh lệch giá thị trường so với giá trị tài sản ròng** của ETF, tức đo trực tiếp áp lực mua/bán chứng chỉ quỹ. Cộng thêm **quỹ Việt Nam niêm yết ở nước ngoài** trên Yahoo với **23 năm lịch sử**.

**Thứ KHÔNG có ở bất kỳ nguồn nào: NAV quỹ mở** (quỹ không niêm yết).

## 1. Bản đồ — nguồn nào ghi gì

| Nguồn | Có gì về quỹ VN | Chi tiết đo được |
|---|---|---|
| **BVSC** `/quotes` | **31 mã** `StockType=3` (ETF + chứng chỉ quỹ niêm yết) | Giá trần/sàn/tham chiếu, tên quỹ |
| **BVSC** `/datafeed/instruments` | Giá đầy đủ + **số chứng chỉ lưu hành** + **room ngoại** | `FundType` (`E`=ETF, `M`=khác) · `ListedShare` · `TotalListingQtty` · `foreignRoom` · `foreignRemain`. 🔴 **Không có NAV** |
| **FiinTrade** `GetPriceData` | 🔵 **`iNav` và `iIndex`** — thứ giá trị nhất | Lịch sử tới **2.963 phiên (~12 năm)** cho `E1VFVN30` |
| **FiinTrade** tham chiếu | Phân loại `QU` = Quỹ đầu tư, **24 mã** | Dùng `GetSnapshotNoneBank` |
| **Yahoo** `.VN` | Cùng 31 mã, `quoteType: ETF`, **kèm tên công ty quản lý quỹ** | Dragon Capital · SSIAM · VinaCapital · KIM · Mirae Asset |
| 🔵 **Yahoo** — sàn ngoại | **Quỹ Việt Nam niêm yết nước ngoài** — dự án hoàn toàn chưa có | Xem §3 |
| WiChart · FRED · Frankfurter · LBMA · Binance · SBV · akshare | ❌ không có gì | |

## 2. 🔵 `iNav` của FiinTrade — chênh lệch giá và NAV

`GET FIIN_TECH/PriceData/GetPriceData?Code={mã ETF}&Frequently=Daily&PageSize=30`
Header `Origin: https://fiinapp.bvsc.com.vn`. Hai trường chuyên biệt: **`iNav`** (NAV nội suy) và **`iIndex`** (mức chỉ số cơ sở).

Phiên 14/08/2026:

| Mã ETF | Số phiên | Giá đóng | `iNav` | **Chênh** | KL khớp |
|---|---:|---:|---:|---:|---:|
| `E1VFVN30` *(DCVFMVN30)* | **2.963** | 33.900 | 33.770,13 | **+0,38%** | 429.417 |
| `FUEVFVND` *(DCVFMVN Diamond)* | 1.566 | 33.500 | 33.345,30 | **+0,46%** | 152.251 |
| `FUEMAV30` *(MAFM VN30)* | 1.417 | 23.220 | 23.026,35 | **+0,84%** | 3.763 |
| `FUEVN100` *(VinaCapital VN100)* | 1.516 | 25.190 | 24.679,12 | **+2,07%** | 37.352 |
| `FUESSV30` *(SSIAM VN30)* | 1.496 | 24.090 | 23.594,00 | **+2,10%** | 23.040 |

**Chênh trung bình +1,17%, biên độ +0,38% … +2,10%. Cả 5 quỹ đều giao dịch CAO HƠN NAV.**

### Vì sao đây là dữ liệu có giá trị

Chênh lệch giá–NAV của ETF là **thước đo áp lực mua/bán chứng chỉ quỹ theo thời gian thực**:
- **Premium kéo dài** ⇒ cầu mua chứng chỉ vượt cung ⇒ tổ chức tạo lập phải **phát hành thêm** ⇒ họ **mua rổ cổ phiếu cơ sở** ⇒ tiền chảy vào thị trường.
- **Discount kéo dài** ⇒ ngược lại, có lực rút.

Đây là **kênh dòng tiền quan sát được trước khi nó hiện ra ở giá cổ phiếu** — đúng loại tín hiệu mà phương pháp "đầu tư theo chu kỳ chính sách" của skill quan tâm ở tầng dòng tiền.

⚠️ **Ràng buộc phải ghi:**
- **Chỉ 5/8 mã thử được FiinTrade nhận.** `FUEDCMID`, `FUESSVFL`, `FUCVREIT` → `status: "Failed"`, `"Code not valid"`. **Độ phủ là tập con, chưa đo hết 31 mã.**
- **Thanh khoản rất lệch.** `E1VFVN30` 429k chứng chỉ, nhưng `FUEMAV30` chỉ **3.763**. Chênh lệch giá–NAV của quỹ thanh khoản mỏng **là nhiễu, không phải tín hiệu**.
- Cả 5 cùng dương trong **một phiên** — chưa đủ để nói xu hướng.

## 3. 🔵 Quỹ Việt Nam niêm yết nước ngoài — Yahoo, lịch sử rất sâu

| Mã | Quỹ | Sàn | Số phiên | Từ | Giá |
|---|---|---|---:|---|---|
| **`VOF.L`** | **VinaCapital Vietnam Opportunity Fund** | London | **5.799** | **2003-09-30** | 442,5 GBp |
| `1VV.F` | *(cùng quỹ, niêm yết Frankfurt)* | Frankfurt | 2.642 | 2016-03-23 | 5,12 EUR |
| `KPHO` | KraneShares Dragon Capital Vietnam Growth ETF | Mỹ | 174 | 2025-12-04 | 22,39 USD |

Thêm: `1VV.MU` (Munich), `VCVOF` (OTC Mỹ), `FUEVN100.VN` — Yahoo trả kèm tên công ty quản lý.

**`VOF.L` là mục đáng giá nhất: 23 năm lịch sử liên tục.** Đây là quỹ đóng lớn niêm yết London chuyên đầu tư Việt Nam. **Mức chiết khấu so với NAV của VOF là chỉ báo khẩu vị của nhà đầu tư nước ngoài với Việt Nam** — chiết khấu doãng ra khi dòng vốn ngoại rút, thu hẹp khi họ quay lại.

⚠️ **Chưa kiểm:** Yahoo có trả NAV của `VOF.L` không, hay chỉ có giá. Nếu chỉ có giá thì phải lấy NAV từ nơi khác mới tính được chiết khấu. **Phải kiểm trước khi tính vào kế hoạch.**

## 4. 🔴 Thứ không nguồn nào có: NAV quỹ mở

Toàn bộ trên là **quỹ niêm yết**. **Quỹ mở** (VESAF, DCDS, VCBF, SSISCA, MBVF…) — loại nhà đầu tư cá nhân mua nhiều nhất qua Fmarket — **không nguồn nào trong 10 nguồn đã khảo sát có NAV**.

Đã kiểm: Yahoo không có mã `0P…VN` nào cho quỹ mở Việt Nam *(các mã `0P…` tìm được đều là quỹ nước ngoài: `.SW`, `.F`, `.T`)*.

**Hướng chưa dò:** Fmarket *(nền tảng phân phối quỹ mở, `vnstock` khai là một backend của nó)* · trang công bố của từng công ty quản lý quỹ · Fiin­Pro X.

**Nhưng nên cân nhắc mức ưu tiên:** NAV quỹ mở công bố **theo tuần hoặc theo ngày với độ trễ**, và quỹ mở **không giao dịch trên sàn** nên không tạo tín hiệu dòng tiền tức thời như ETF. Giá trị phân tích **thấp hơn** hai mục ở §2 và §3.

## 5. Đề xuất mức ưu tiên

| Ưu tiên | Việc | Vì sao |
|---|---|---|
| **1** | **Lấy `iNav` + `iIndex` cho các mã ETF FiinTrade nhận** | Miễn phí, cùng endpoint đã dùng, ~12 năm lịch sử, cho tín hiệu dòng tiền thật |
| **2** | Lấy 31 mã quỹ niêm yết từ BVSC *(giá + `ListedShare` + room ngoại)* | Đã nằm trong luồng ETL cổ phiếu, gần như không thêm chi phí |
| **3** | **`VOF.L` từ Yahoo** — 23 năm, chỉ báo khẩu vị ngoại | Cần kiểm xem có NAV không |
| 4 | Dò độ phủ `iNav` cho đủ 31 mã | Mới thử 8, nhận 5 |
| 5 | NAV quỹ mở *(Fmarket…)* | Giá trị phân tích thấp hơn, chưa dò |

## 6. Ảnh hưởng tới tài liệu

`10-sources/README.md` §2 *"Ngoài phạm vi"* đang liệt **"ETF/Quỹ"** và **"NAV quỹ mở"**. Cần tách:
- **ETF/chứng chỉ quỹ niêm yết → VÀO phạm vi** *(BVSC 31 mã + FiinTrade `iNav`)*
- **Quỹ Việt Nam niêm yết nước ngoài → vào phạm vi** *(mục mới)*
- **NAV quỹ mở → vẫn ngoài phạm vi**, kèm lý do đo được

## 7. Chưa kiểm

- Độ phủ `iNav` trên đủ 31 mã *(mới thử 8, nhận 5)*
- `iNav` có bị vá hồi tố không; lịch cập nhật trong ngày
- `VOF.L` có NAV trên Yahoo không
- Ý nghĩa chính xác của `FundType = M` ở BVSC *(mã `FUCVREIT` là quỹ bất động sản)*
- `VFMVF1` có trong `/quotes` nhưng **không có trong `/datafeed/instruments`** — thêm một bằng chứng hai endpoint BVSC lệch độ phủ
- Fmarket và trang công ty quản lý quỹ — chưa dò lần nào
