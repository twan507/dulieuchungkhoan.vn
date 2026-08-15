# 14 — OMO Ngân hàng Nhà nước (`sbv.gov.vn`)

**Ngày khảo sát:** 2026-08-15 · **Trạng thái:** đã tải và parse thật một phiên (14/08/2026) · **Kiểu nguồn:** crawl HTML, không có API

> Đây là **nguồn công bố gốc** kết quả đấu thầu nghiệp vụ thị trường mở của NHNN. Không token, không đăng nhập, không giới hạn gói. Đổi lại: không có API, không có kho lưu, và thiếu đúng hai cột mà phân tích cần nhất.

---

## 1. Tóm tắt

| | |
|---|---|
| Host | `https://sbv.gov.vn` |
| Chủ dữ liệu | **Ngân hàng Nhà nước Việt Nam** — cơ quan công bố gốc |
| Định dạng | HTML bài viết (portlet Liferay Asset Publisher), **không phải API** |
| Xác thực | Không. Không token, không cookie, không đăng nhập |
| Độ trễ | **T+0** — bài đăng trong ngày đấu thầu *(đo 2026-08-15: bài mang ngày `14.08.26`)* |
| Lịch sử truy hồi được | **0 ngày** 🔴 — chỉ hiển thị đúng phiên mới nhất |
| Kích thước một lời gọi | **414.559 byte** *(đo 2026-08-15)* |
| Nhịp cần | **1 lời gọi/ngày** |
| Thời gian phản hồi | *chưa kiểm* |

URL thật *(đo 2026-08-15)*:

```
GET https://sbv.gov.vn/vi/nghiệp-vụ-thị-trường-mở
# dạng đã mã hoá percent — nên dùng dạng này trong code:
GET https://sbv.gov.vn/vi/nghi%E1%BB%87p-v%E1%BB%A5-th%E1%BB%8B-tr%C6%B0%E1%BB%9Dng-m%E1%BB%9F
```

---

## 2. Vì sao cần OMO

Skill phân tích (`vn-stock-knowledge/references/macro-money-creation.md`) xếp **OMO đứng đầu năm nhân tố quyết định thanh khoản hằng ngày**: OMO · lãi suất liên ngân hàng · tỷ giá · tín dụng · lạm phát.

Đối chiếu với nguồn đang có *(khảo sát 2026-08-15)*:

| Nhân tố | Nguồn hiện có | Trạng thái |
|---|---|---|
| Lãi suất liên ngân hàng | WiChart `lslnh` — ngày, trễ 1 ngày | ✅ đủ |
| Tỷ giá | WiChart `dhtg` — 5 series, ngày | ✅ đủ |
| Tín dụng | WiChart `td` — tháng, trễ 72 ngày | ✅ đủ |
| Lạm phát | WiChart `cpi` — tháng, trễ 42 ngày | ✅ đủ |
| **OMO** | — | ❌ **thiếu hoàn toàn** trước đợt này |

**Ba nguồn dự án đang dùng đều không có OMO** *(đo 2026-08-15)*: WiChart 87 key — đã đọc hết danh mục, không có; FiinTrade `Master/GetAllChartEconomy` — 36 chỉ tiêu, không có; BVSC 7 endpoint REST — thuần giao dịch, không có. Thứ gần nhất họ có là **lãi suất** liên ngân hàng, tức *giá* của thanh khoản, không phải *lượng* bơm/hút.

⚠️ Skill cũng cảnh báo đừng đọc OMO ngây thơ: phần lớn thời gian OMO là **điều hoà**, chỉ khi thành xu hướng kéo dài mới nói tới chuyện đổi cung tiền. Nghĩa là thứ phải lưu là **chuỗi ròng theo ngày để cộng dồn**, không phải con số từng phiên.

---

## 3. Endpoint và cách gọi

Một lời gọi `GET`, không tham số. Không có tham số ngày, không có phân trang, không có endpoint JSON nào phía sau.

```bash
curl -s \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36" \
  -H "Accept: text/html,application/xhtml+xml" \
  -H "Accept-Language: vi,en;q=0.9" \
  "https://sbv.gov.vn/vi/nghi%E1%BB%87p-v%E1%BB%A5-th%E1%BB%8B-tr%C6%B0%E1%BB%9Dng-m%E1%BB%9F"
```

### Kết quả đo 2026-08-15

| Cách gọi | Kết quả |
|---|---|
| Python `requests`, **User-Agent mặc định** | `200` nhưng body **246 byte**: `<title>Request Rejected</title>` kèm `Your support ID is: …` |
| PowerShell `Invoke-WebRequest`, **không thêm header nào** | `200`, **414.534 byte**, HTML hợp lệ đầy đủ |
| Gửi đủ header trình duyệt | `200`, **~414 KB**, HTML hợp lệ đầy đủ |

→ WAF chặn theo **dấu vân tay client cụ thể** *(nhiều khả năng nhắm chuỗi `python-requests`)*, **không phải** chặn mọi client thiếu header trình duyệt. Xem [Giới hạn 4](#-giới-hạn-4--waf-chặn-theo-dấu-vân-tay-client).

---

## 4. Lược đồ bảng

Bảng nằm **trong thân bài viết**, không phải trong một component có cấu trúc. Markup do biên tập viên dán vào, kèm `<style>` nội tuyến ngay trong nội dung.

| Lớp CSS *(quan sát 2026-08-15)* | Vai trò |
|---|---|
| `ls01-table` | Bảng kết quả đấu thầu |
| `ls01-group` | Dòng nhóm — tên loại hình giao dịch (`Mua kỳ hạn`…) |
| `ls01-total` | Dòng tổng của nhóm |

**Bốn cột, không hơn:**

| Cột | Kiểu | Đơn vị | Ghi chú |
|---|---|---|---|
| `Loại hình giao dịch` | string | — | `Mua kỳ hạn` \| `Bán kỳ hạn` \| `Bán hẳn` *(chỉ quan sát được `Mua kỳ hạn` ngày đo)* |
| `Số thành viên tham gia/trúng thầu` | string | thành viên | Dạng `4/4` — phải tách hai số |
| `Khối lượng trúng thầu` | number | **Tỷ đồng** | Định dạng Việt: `6.307,47` — chấm là phân nhóm nghìn, phẩy là thập phân |
| `Lãi suất trúng thầu` | number | **%/năm** | `4,5` |

**Kỳ hạn không có cột riêng** — nó nằm trong **nhãn dòng** bên trong nhóm. Đây là trường phân định, phải parse ra bằng được.

**Ngày không có trong bảng** — ngày nằm trong **tiêu đề bài viết**, dạng `(dd.mm.yy)`:

```
KẾT QUẢ ĐẤU THẦU THỊ TRƯỜNG MỞ (14.08.26)
```

---

## 5. Dữ liệu mẫu thật — phiên 14/08/2026

Đã tải và parse thật *(đo 2026-08-15)*. Toàn bộ bốn dòng thuộc nhóm **`Mua kỳ hạn`**:

| Ngày | Loại hình | Kỳ hạn (ngày) | TV tham gia/trúng | KL trúng thầu (tỷ đồng) | LS trúng thầu (%/năm) |
|---|---|---:|---|---:|---:|
| 14.08.26 | Mua kỳ hạn | 7 | 4/4 | 6.307,47 | 4,5 |
| 14.08.26 | Mua kỳ hạn | 35 | 4/4 | 3.466,54 | 4,5 |
| 14.08.26 | Mua kỳ hạn | 63 | 1/1 | 210,17 | 4,5 |
| 14.08.26 | Mua kỳ hạn | 91 | 3/3 | 909,92 | 4,5 |
| | **Tổng** | | | **10.894,10** | |

Hai điều đọc được ngay từ bảng này:

- **Lãi suất 4,5% phẳng đều trên cả bốn kỳ hạn** — NHNN chào một mức giá duy nhất, không phân biệt 7 ngày hay 91 ngày.
- 🔴 **Phiên đó KHÔNG có nhóm "Bán hẳn"** ⇒ ngày 14/08/2026 **NHNN không phát hành tín phiếu**. Vắng nhóm là dữ liệu, không phải thiếu dữ liệu — parser phải phân biệt hai trạng thái này, đừng ghi `null`.

*(Suy đoán, chưa kiểm: hôm nào NHNN phát hành tín phiếu thì cùng bảng sẽ có thêm nhóm `Bán hẳn` — vì Vietstock và WiGroup đều mô tả ba nhóm `Mua kỳ hạn` / `Bán kỳ hạn` / `Bán hẳn` trên cùng bộ số gốc. Ngày đo chỉ thấy `Mua kỳ hạn`, nên cấu trúc HTML của hai nhóm kia **chưa từng được quan sát**.)*

---

## 6. Bốn giới hạn

### 🔴 Giới hạn 1 — Chỉ phiên mới nhất, không có kho lưu

Portlet Liferay Asset Publisher hiển thị **đúng một bài**. Kiểm chứng độc lập *(đo 2026-08-15)*:

- Toàn trang chỉ có **đúng một** tiêu đề `KẾT QUẢ ĐẤU THẦU THỊ TRƯỜNG MỞ (14.08.26)`
- **Không có dấu hiệu phân trang nào** — đã tìm `page=`, `cur=`, `delta=`, chuỗi "Trang sau" → không có
- Không tham số ngày, không link category
- 4 link trông giống liên quan đều dẫn sang chủ đề khác *(đấu thầu đầu tư, kết quả điều tra…)*
- Tìm kiếm nội bộ của site bị WAF chặn; kho tín phiếu `/-/categories/94000` chỉ có một thông báo đứng yên; bản tiếng Anh không có bảng nào

> **Hệ quả vận hành — đây là điều quan trọng nhất trong cả file này:**
> **Không backfill được từ SBV. Mỗi ngày không crawl là một ngày mất vĩnh viễn.**
> Crawler phải bật trước, bàn thiết kế sau. Chi phí là ~30 dòng code và 1 lời gọi/ngày; chi phí của việc chờ là dữ liệu không bao giờ lấy lại được.

### 🔴 Giới hạn 2 — Thiếu cột đáo hạn và bơm ròng

Bảng chỉ có 4 cột *(mục 4)*. Kiểm chứng: tìm chuỗi `đáo hạn` và `bơm ròng` trong **toàn trang** → **không có** *(đo 2026-08-15)*.

Thiếu: `kl_dao_han` · `bom_hut_rong` · `dang_luu_hanh`.

Vượt được **một phần**: kỳ hạn nằm trong nhãn dòng nên **tự dựng được lịch đáo hạn** — nhưng chỉ đúng **sau khi tích luỹ đủ ~140 ngày tự crawl** *(kỳ hạn dài nhất trong danh mục NHNN là 140 ngày)*, và **sai nếu bỏ lỡ một phiên bất kỳ**. Xem [mục 8](#8-cách-dựng-bơm-ròng).

### ⚠️ Giới hạn 3 — HTML viết tay, có thể đổi bất cứ lúc nào

Class tự chế (`ls01-table` / `ls01-group` / `ls01-total`), `<style>` nội tuyến nằm ngay trong nội dung bài — tức **biên tập viên dán vào**, không phải template hệ thống sinh ra. Không có cam kết nào về tính ổn định của markup.

Ba hệ quả cụ thể:

- Số ở **định dạng Việt** (`6.307,47`) — parse bằng `float()` thẳng sẽ ra sai một nghìn lần hoặc ném lỗi
- **Ngày nằm trong tiêu đề bài** `(dd.mm.yy)`, không nằm trong bảng
- Selector theo class là **giả định mong manh** — nên parse phòng thủ *(dò theo tiêu đề cột, không chỉ theo class)* và cảnh báo khi số cột ≠ 4

### ⚠️ Giới hạn 4 — WAF chặn theo dấu vân tay client

`python-requests` với UA mặc định → `200` nhưng body **246 byte** `Request Rejected`. PowerShell `Invoke-WebRequest` không header → **qua được**. Gửi đủ header trình duyệt → chắc chắn qua. Bảng đo đầy đủ ở [mục 3](#3-endpoint-và-cách-gọi).

🔴 **Bẫy thật ở đây không phải việc bị chặn, mà là bị chặn với `HTTP 200`.** ETL kiểm status code sẽ thấy "thành công" rồi ghi một ngày rỗng vào kho mà không ai biết.

**Bắt buộc:** sau mỗi lời gọi, kiểm **độ dài body** *(trang thật ~414 KB; body < 10 KB là bị chặn)* **và** kiểm sự có mặt của chuỗi `KẾT QUẢ ĐẤU THẦU THỊ TRƯỜNG MỞ`. Thiếu một trong hai thì báo động, không ghi kho.

*(Chưa kiểm: WAF có siết theo tần suất không — đợt đo chỉ gọi vài lần, chủ đích không dò ngưỡng.)*

---

## 7. Trường cần mà nguồn không có

Danh sách trường phân tích cần, đối chiếu với thứ SBV cho *(đo 2026-08-15)*:

| Trường | Bắt buộc? | SBV có? | Ghi chú |
|---|---|---|---|
| `ngay` — ngày đấu thầu | ✅ | ⚠️ gián tiếp | Nằm trong **tiêu đề bài**, không nằm trong bảng |
| `cong_cu` — `OMO_reverse_repo` \| `SBV_bills` | ✅ | ✅ | Suy từ `Loại hình giao dịch`: `Mua kỳ hạn` = bơm; `Bán hẳn` = hút bằng tín phiếu |
| `ky_han_ngay` | ✅ | ⚠️ gián tiếp | Trong **nhãn dòng**, không có cột riêng. Danh mục kỳ hạn: 7/14/21/28/35/56/63/91/140 |
| `kl_trung_thau` (tỷ VND) | ✅ | ✅ | Cột 3 |
| `ls_trung_thau` (%/năm) | ✅ | ✅ | Cột 4 |
| `so_tv_tham_gia` / `so_tv_trung_thau` | ⭕ | ✅ | Cột 2, dạng `4/4` — tín hiệu độ căng hệ thống |
| **`kl_dao_han` (tỷ VND)** | ✅ | ❌ **không** | **Trường phân định** — thiếu nó là không tính được ròng |
| **`bom_hut_rong`** = phát hành − đáo hạn | ✅ | ❌ **không** | Thứ skill cần cộng dồn |
| `dang_luu_hanh` — OMO/Bills outstanding | ⭕ nên có | ❌ **không** | Mức tồn, đọc xu hướng nhanh hơn cộng dồn tay |

---

## 8. Cách dựng bơm ròng

SBV chỉ cho **lượng trúng thầu**. Bơm ròng phải tự dựng qua ba bước:

**Bước 1 — dựng lịch đáo hạn.** Mỗi dòng trúng thầu ngày `D` với kỳ hạn `k` sinh ra một khoản đáo hạn khối lượng bằng đúng nó vào ngày `D + k`.

**Bước 2 — cộng cho từng ngày.**

```
bơm(D)     = Σ KL trúng thầu nhóm "Mua kỳ hạn" tại ngày D
đáo_hạn(D) = Σ KL trúng thầu nhóm "Mua kỳ hạn" của các phiên trước có ngày + kỳ hạn = D
ròng(D)    = bơm(D) − đáo_hạn(D)          # dương = bơm ròng, âm = hút ròng
```

Nhóm `Bán hẳn` (tín phiếu) đi ngược dấu: phát hành là **hút**, đáo hạn là **bơm**. Ngày đo không có nhóm này nên **công thức cho tín phiếu chưa được kiểm trên dữ liệu thật**.

**Bước 3 — cộng dồn.** Thứ skill dùng là **chuỗi ròng luỹ kế**, không phải `ròng(D)` đơn lẻ.

### 🔴 Ba điều kiện để con số ròng có nghĩa

1. **Phải có đủ ~140 ngày lịch sử tự crawl trước đã.** Kỳ hạn dài nhất là 140 ngày; trước mốc đó, `đáo_hạn(D)` luôn thiếu phần sinh ra từ những phiên chưa được ghi ⇒ ròng **luôn bị thổi phồng về phía bơm**.
2. **Bỏ lỡ một phiên là hỏng cả cửa sổ 140 ngày sau đó** — không có cách vá, vì [Giới hạn 1](#-giới-hạn-1--chỉ-phiên-mới-nhất-không-có-kho-lưu).
3. **Đây là số suy ra, không phải số đo.** Phải đánh dấu rõ trong kho là *derived*, và đối chiếu chéo với nguồn có sẵn cột ròng trước khi tin.

⚠️ **Trong ~140 ngày đầu, chỉ dùng `kl_trung_thau` + `ls_trung_thau` thô.** Đừng hiển thị chuỗi ròng chưa đủ dữ liệu — nó sai một chiều có hệ thống, khó phát hiện hơn là không có gì.

---

## 9. Ba lưu ý vận hành

1. **Gửi đủ header trình duyệt.** Không phải vì bắt buộc *(PowerShell trần vẫn qua)*, mà vì rẻ và loại hẳn một loại lỗi câm — xem [Giới hạn 4](#-giới-hạn-4--waf-chặn-theo-dấu-vân-tay-client).
2. **Lấy ngày từ tiêu đề bài `(dd.mm.yy)`, tuyệt đối không lấy ngày hệ thống.** Chạy crawler lúc 23:50 hay lúc bài chưa kịp lên là gán nhầm ngày ngay. Nếu ngày trong tiêu đề **trùng với ngày đã có trong kho** thì đó là phiên cũ chưa cập nhật — bỏ qua, đừng ghi đè.
3. **Lưu cả HTML gốc**, không chỉ lưu bảng đã parse. Markup viết tay sẽ đổi *([Giới hạn 3](#-giới-hạn-3--html-viết-tay-có-thể-đổi-bất-cứ-lúc-nào))*, và khi đổi thì chỉ có HTML gốc mới cho phép parse lại quá khứ — trong khi [Giới hạn 1](#-giới-hạn-1--chỉ-phiên-mới-nhất-không-có-kho-lưu) đảm bảo không tải lại được từ nguồn.

---

## 10. Giới hạn kết luận

**SBV là nguồn gốc, miễn phí, ẩn danh, T+0 — và không thay thế được một kho lịch sử.** Nó cho *hôm nay*, không cho *chuỗi*. Chuỗi phải do chính dự án tích luỹ từ ngày bật crawler.

Bối cảnh các đường khác *(khảo sát 2026-08-15)*:

| Nguồn | Trạng thái |
|---|---|
| **Vietstock Macro API** `POST /Macro/GetReportDataByIDs` | Endpoint và payload **đã đo chính xác**. Có sẵn trường `TotalVolPumpWithdrawOMO` "Giá trị bơm ròng (tỷ đồng)" ⇒ **không phải tự tính**. Gói Free = **60 ngày** gần nhất. **Cần đăng nhập** — gọi ẩn danh trả `RequestUpgradeAccount_Permission`. Dùng để **backfill 60 ngày** và **kiểm chứng chéo** con số tự dựng từ SBV |
| **WiFeed / WiGroup gói "Tiền tệ"** | Schema đúng bằng nhu cầu *(có cả đáo hạn và lưu hành)*, nhưng biểu đồ nhúng trên trang WiGroup đã đo là **ảnh chụp tĩnh dừng ở 15/08/2024**, không phải feed sống; WiGroup trả lời **không sửa/không cung cấp API mới**. ⇒ **đóng lại về mặt kỹ thuật** |
| FiinTrade *(bản BVSC dự án dùng)* | ❌ không có OMO — đã quét toàn bộ bundle |
| VBMA · HNX · CEIC · DBnomics/IMF/BIS | ❌ đã kiểm, không nguồn nào cho chuỗi OMO Việt Nam theo ngày |

**Ba điều file này KHÔNG nói:**

| Chưa kiểm | Vì sao đáng biết |
|---|---|
| Cấu trúc HTML của nhóm `Bán kỳ hạn` và `Bán hẳn` | Chưa từng quan sát — parser cho tín phiếu là **viết mù** cho tới phiên đầu tiên NHNN phát hành |
| SBV đăng bài lúc mấy giờ trong ngày | Quyết định giờ chạy crawler. Đặt sai giờ = mất phiên = [Giới hạn 1](#-giới-hạn-1--chỉ-phiên-mới-nhất-không-có-kho-lưu) |
| WAF có siết theo tần suất không | Đợt đo chỉ gọi vài lần, chủ đích không dò ngưỡng |

Xem thêm: [`wichart.md`](wichart.md) cho bốn nhân tố thanh khoản còn lại · [`../market/00-conventions.md`](../market/00-conventions.md) cho quy ước chung.
