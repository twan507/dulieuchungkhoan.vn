# Chọn trường cho ETL thị trường — bảng tường minh theo từng mã

**Ngày:** 2026-08-14 · **Đo lại và chốt thêm:** 2026-08-15 · **Trạng thái:** ✅ đã chốt ·
**Trải từ quyết định chọn nguồn ngày 2026-08-14**

**File sinh tự động** từ [`gen_field_selection.py`](gen_field_selection.py) — sửa qua script rồi chạy lại, không sửa tay. Bản [`market-field-selection.json`](market-field-selection.json) sinh cùng nguồn.

Tài liệu này trả lời đúng một câu hỏi của người viết ETL: **trường này lấy hay bỏ, nguồn chuẩn là ai, vì sao.**
Lý do ghi thẳng tại từng dòng — không phải tra chỗ khác, không phải diễn giải lại quyết định của ai.

Số đo nền — **đo lại toàn bộ ngày 2026-08-15**, khớp con số cũ và giải luôn hai chỗ vênh:

| Nguồn | Số trường | Ghi chú số đo 2026-08-15 |
|---|---:|---|
| Screener `getScreenerItems` | **193** | 193 là số khoá **phân biệt**. Con số 223 của tài liệu endpoint là **tổng kích thước 5 khối** (43+129+12+21+18) — 27 khoá nằm ở từ hai khối trở lên, dư đúng 30 lần. Cả hai đều đúng, không mâu thuẫn. Đo trên `comGroupCode=ALL` và `VN30` đều ra 193 |
| `GetSnapshot` (BID, ngân hàng) | **54** | `summary` 28 + `quarterly[0]`/`yearly[0]` 27, hợp lại 54 khoá phân biệt |
| BVSC `datafeed/instruments` | **62** | Đếm thật trên BID/FPT/VNM: 62/62/62 |

Chốt luôn ba điểm vênh cũ: **223 vs 193** không phải do loại hình doanh nghiệp mà do khoá lặp giữa các khối ·
BVSC **62 vs 50** thì 62 đúng *(chính ví dụ response trong tài liệu endpoint cũng có đủ 62 khoá — con số 50 ở
tiêu đề là đếm sai của tài liệu, đã sửa)* · mã trường Screener **không viết thường toàn bộ** mà chỉ hạ chữ cái
đầu: `ForeignerRoom` → `foreignerRoom`, `Rtq12` → `rtq12`.

Nguồn dẫn của từng bảng: [10 — Từ điển mã trường & Bộ sàng lọc](../10-sources/market/10-fiin-dictionary.md) ·
[Phụ lục A — mã trường](../10-sources/market/appendix-A-field-codes.md) ·
[field-dictionary.json](../10-sources/market/field-dictionary.json) ·
[04 — Hồ sơ doanh nghiệp](../10-sources/market/04-fiin-company-profile.md) ·
[01 — BVSC REST](../10-sources/market/01-bvsc-rest.md) ·
[Phụ lục B — độ phủ](../10-sources/market/appendix-B-coverage.md).

---

## 1 · Luật chọn nguồn

Chép nguyên từ [kiến trúc tổng thể §3.4](../00-overview/architecture.md):

> **Mỗi chỉ tiêu có đúng một nguồn chuẩn.** Chọn theo hai tiêu chí, xét theo thứ tự: *(1)* nguồn nào realtime
> và khớp sàn — ưu tiên tuyệt đối cho giá và mọi thứ dẫn xuất từ giá; *(2)* nguồn nào cho trọn bộ ngữ cảnh —
> trùng lặp không đủ là lý do để bỏ.
>
> **Nhóm chỉ tiêu dẫn xuất lẫn nhau thì lấy trọn bộ từ một nguồn.** Biến TTM sinh ra tỷ số, giá sinh ra chỉ
> báo. Trộn nguồn giữa chừng tạo ra dữ liệu **tự mâu thuẫn trong cùng một bảng** — chatbot lấy vốn hoá chia
> lợi nhuận sẽ ra P/E khác cột P/E ngay bên cạnh, mà không có gì báo sai.

| Nhóm | Nguồn chuẩn | Quy mô |
|---|---|---|
| Giá, KL, sổ lệnh, khối ngoại, thoả thuận, chỉ báo kỹ thuật | **BVSC** | ~40 trường, realtime |
| Tỷ số tài chính, Beta, sở hữu tổ chức, TTM | **Screener** | 80/193 |
| Hồ sơ DN, sở hữu chi tiết | **Snapshot** | 16/54 |
| Mọi mã `bs*` `is*` `cf*` `no*` | **BCTC đầy đủ** | 556 |
| Tự doanh, đóng góp chỉ số, chuỗi khối ngoại | **MoneyFlow** | BVSC không có |

Hai đánh đổi đã chấp nhận, ghi ở đây để không ai hoảng khi thấy số lệch:

- Beta và các tỷ số định giá của Screener tính trên **giá FiinTrade**, nên lệch nhẹ so với giá BVSC ta lưu.
  Lệch ở chữ số thập phân thứ hai của P/E là bình thường.
- ATO/ATC không lấy từ Screener: ETL Screener chạy sau 15:00 nên số đó đã là chuyện đã rồi. Chỗ nó có nghĩa
  là realtime — BVSC topic `i:` đã có. Ingester không bắt được thì sửa ở Ingester, không vá bằng bản chết.

## 2 · Cách đọc bảng

| Cột | Nghĩa |
|---|---|
| **Mã** | Tên trường **đúng như endpoint trả về**, đã đối chiếu với 193 khoá thật ngày 2026-08-15. `GetScreenerParameters` trả hoa chữ đầu (`Rtq12`, `ForeignerRoom`) còn `getScreenerItems` **chỉ hạ chữ cái đầu**, giữ nguyên phần sau: `rtq12`, `foreignerRoom`, `freeFloatRate`, `averageValue1Week`, `overSma50`, `isa20TTM`. Chuẩn hoá bằng cách viết thường TOÀN BỘ là sai — tra khoá sẽ trượt |
| **Tên** | Tên tiếng Việt. `—` nghĩa là **không nguồn nào đặt tên cho mã này, và tôi cũng không tự đặt** — mã mang trạng thái chưa giải mã trong từ điển, hoặc không có trong từ điển, mà mô tả nhóm ở tài liệu nguồn cũng không đủ để đặt một nhãn. Phân biệt với `tự đặt` ở dòng dưới: đó cũng là mã không nguồn nào đặt tên, nhưng có nhãn do tôi đặt theo mô tả nhóm |
| **Nguồn tên** | Tên đó ở đâu ra. `từ điển` = `ten_vi` trong từ điển 729 mã · `tài liệu endpoint` = chép từ bảng mô tả trường của tài liệu endpoint · `suy theo luật kỳ` = mã TTM/Y, suy từ mã gốc theo luật *cùng chữ số + cùng chữ thứ ba = cùng chỉ tiêu, khác kỳ* · **`tự đặt` = tôi đặt theo mô tả NHÓM trong tài liệu nguồn, KHÔNG phải tên chính thức của FiinGroup** |
| **Lấy/Bỏ** | `lấy` = ETL ghi vào kho · `bỏ` = không ghi · `chưa rõ` = chưa phân loại được |
| **Nguồn chuẩn** | Nơi duy nhất chỉ tiêu này được lấy. `(tự tính)` = tính lại từ chuỗi của nguồn đó |
| **Trạng thái** | `chốt` = suy được thẳng từ tài liệu nguồn hoặc từ nhóm lý do đã chốt · `cần kiểm API` = tài liệu không đủ căn cứ, phải gọi API đo mới kết luận được |

Phân bố cột **Nguồn tên** trên 213 dòng: `từ điển` 114 · `tài liệu endpoint` 52 ·
`suy theo luật kỳ` 7 · **`tự đặt` 31** · `—` 9. Con số `tự đặt` đáng để ý: đó là những
mã mà **không nguồn nào cho tên**, tên trong bảng chỉ là nhãn mô tả để đọc cho tiện — đừng đem hiển thị cho
người dùng cuối như tên chính thức, và đừng dùng nó làm căn cứ suy nghĩa. Việc phân loại lấy/bỏ của các dòng
này **không dựa vào tên** mà dựa vào nhóm lý do, nên tên có là nhãn tự đặt cũng không ảnh hưởng.

**Trường không có trong bảng nghĩa là chưa liệt kê được**, không phải đã bỏ — xem [§7 đối soát](#7--đối-soát-số-đếm).

## 3 · BVSC — giá, sổ lệnh, khối ngoại, thoả thuận

34 trường được nêu đích danh, tất cả **lấy**. BVSC là nguồn realtime khớp trực tiếp với sàn; đây là
nhóm được ưu tiên tuyệt đối theo luật §1.

**Giá** — 9 trường

| Mã | Tên | Nguồn tên | Lấy/Bỏ | Nguồn chuẩn | Lý do | Trạng thái |
|---|---|---|---|---|---|---|
| `closePrice` | Giá khớp gần nhất | tài liệu endpoint | lấy | BVSC | giá — nguồn realtime khớp trực tiếp với sàn, ưu tiên tuyệt đối cho giá và mọi thứ dẫn xuất từ giá | chốt |
| `ceiling` | Trần | tài liệu endpoint | lấy | BVSC | giá — nguồn realtime khớp trực tiếp với sàn, ưu tiên tuyệt đối cho giá và mọi thứ dẫn xuất từ giá | chốt |
| `floor` | Sàn | tài liệu endpoint | lấy | BVSC | giá — nguồn realtime khớp trực tiếp với sàn, ưu tiên tuyệt đối cho giá và mọi thứ dẫn xuất từ giá | chốt |
| `reference` | Tham chiếu | tài liệu endpoint | lấy | BVSC | giá — nguồn realtime khớp trực tiếp với sàn, ưu tiên tuyệt đối cho giá và mọi thứ dẫn xuất từ giá | chốt |
| `open` | Mở cửa | tài liệu endpoint | lấy | BVSC | giá — nguồn realtime khớp trực tiếp với sàn, ưu tiên tuyệt đối cho giá và mọi thứ dẫn xuất từ giá | chốt |
| `high` | Cao nhất | tài liệu endpoint | lấy | BVSC | giá — nguồn realtime khớp trực tiếp với sàn, ưu tiên tuyệt đối cho giá và mọi thứ dẫn xuất từ giá | chốt |
| `low` | Thấp nhất | tài liệu endpoint | lấy | BVSC | giá — nguồn realtime khớp trực tiếp với sàn, ưu tiên tuyệt đối cho giá và mọi thứ dẫn xuất từ giá | chốt |
| `averagePrice` | Giá bình quân phiên | tài liệu endpoint | lấy | BVSC | giá — nguồn realtime khớp trực tiếp với sàn, ưu tiên tuyệt đối cho giá và mọi thứ dẫn xuất từ giá | chốt |
| `PRIOR_PRICE` | — | — | lấy | BVSC | giá — nguồn realtime khớp trực tiếp với sàn, ưu tiên tuyệt đối cho giá và mọi thứ dẫn xuất từ giá | chốt |

**Khối lượng, giá trị** — 3 trường

| Mã | Tên | Nguồn tên | Lấy/Bỏ | Nguồn chuẩn | Lý do | Trạng thái |
|---|---|---|---|---|---|---|
| `totalTrading` | Tổng khối lượng khớp lệnh | tài liệu endpoint | lấy | BVSC | khối lượng và giá trị khớp lệnh — lấy cùng nguồn với giá để không lệch chuỗi | chốt |
| `totalTradingValue` | Tổng giá trị khớp lệnh | tài liệu endpoint | lấy | BVSC | khối lượng và giá trị khớp lệnh — lấy cùng nguồn với giá để không lệch chuỗi | chốt |
| `closeVol` | Khối lượng của lệnh khớp gần nhất | tài liệu endpoint | lấy | BVSC | khối lượng và giá trị khớp lệnh — lấy cùng nguồn với giá để không lệch chuỗi | chốt |

**Sổ lệnh 3 bậc** — 14 trường

| Mã | Tên | Nguồn tên | Lấy/Bỏ | Nguồn chuẩn | Lý do | Trạng thái |
|---|---|---|---|---|---|---|
| `bidPrice1` | Giá dư mua bậc 1 | tài liệu endpoint | lấy | BVSC | sổ lệnh 3 bậc — chỉ có nghĩa ở nguồn realtime; BVSC cấp 3 bậc cho mọi sàn | chốt |
| `bidPrice2` | Giá dư mua bậc 2 | tài liệu endpoint | lấy | BVSC | sổ lệnh 3 bậc — chỉ có nghĩa ở nguồn realtime; BVSC cấp 3 bậc cho mọi sàn | chốt |
| `bidPrice3` | Giá dư mua bậc 3 | tài liệu endpoint | lấy | BVSC | sổ lệnh 3 bậc — chỉ có nghĩa ở nguồn realtime; BVSC cấp 3 bậc cho mọi sàn | chốt |
| `bidVol1` | Khối lượng dư mua bậc 1 | tài liệu endpoint | lấy | BVSC | sổ lệnh 3 bậc — chỉ có nghĩa ở nguồn realtime; BVSC cấp 3 bậc cho mọi sàn | chốt |
| `bidVol2` | Khối lượng dư mua bậc 2 | tài liệu endpoint | lấy | BVSC | sổ lệnh 3 bậc — chỉ có nghĩa ở nguồn realtime; BVSC cấp 3 bậc cho mọi sàn | chốt |
| `bidVol3` | Khối lượng dư mua bậc 3 | tài liệu endpoint | lấy | BVSC | sổ lệnh 3 bậc — chỉ có nghĩa ở nguồn realtime; BVSC cấp 3 bậc cho mọi sàn | chốt |
| `offerPrice1` | Giá dư bán bậc 1 | tài liệu endpoint | lấy | BVSC | sổ lệnh 3 bậc — chỉ có nghĩa ở nguồn realtime; BVSC cấp 3 bậc cho mọi sàn | chốt |
| `offerPrice2` | Giá dư bán bậc 2 | tài liệu endpoint | lấy | BVSC | sổ lệnh 3 bậc — chỉ có nghĩa ở nguồn realtime; BVSC cấp 3 bậc cho mọi sàn | chốt |
| `offerPrice3` | Giá dư bán bậc 3 | tài liệu endpoint | lấy | BVSC | sổ lệnh 3 bậc — chỉ có nghĩa ở nguồn realtime; BVSC cấp 3 bậc cho mọi sàn | chốt |
| `offerVol1` | Khối lượng dư bán bậc 1 | tài liệu endpoint | lấy | BVSC | sổ lệnh 3 bậc — chỉ có nghĩa ở nguồn realtime; BVSC cấp 3 bậc cho mọi sàn | chốt |
| `offerVol2` | Khối lượng dư bán bậc 2 | tài liệu endpoint | lấy | BVSC | sổ lệnh 3 bậc — chỉ có nghĩa ở nguồn realtime; BVSC cấp 3 bậc cho mọi sàn | chốt |
| `offerVol3` | Khối lượng dư bán bậc 3 | tài liệu endpoint | lấy | BVSC | sổ lệnh 3 bậc — chỉ có nghĩa ở nguồn realtime; BVSC cấp 3 bậc cho mọi sàn | chốt |
| `TOTAL_BID_QTTY` | Tổng dư mua | tài liệu endpoint | lấy | BVSC | sổ lệnh 3 bậc — chỉ có nghĩa ở nguồn realtime; BVSC cấp 3 bậc cho mọi sàn | chốt |
| `TOTAL_OFFER_QTTY` | Tổng dư bán | tài liệu endpoint | lấy | BVSC | sổ lệnh 3 bậc — chỉ có nghĩa ở nguồn realtime; BVSC cấp 3 bậc cho mọi sàn | chốt |

**Khối ngoại** — 4 trường

| Mã | Tên | Nguồn tên | Lấy/Bỏ | Nguồn chuẩn | Lý do | Trạng thái |
|---|---|---|---|---|---|---|
| `foreignBuy` | Khối ngoại mua trong phiên | tài liệu endpoint | lấy | BVSC | khối ngoại trong phiên — nguồn realtime, khớp sàn | chốt |
| `foreignSell` | Khối ngoại bán trong phiên | tài liệu endpoint | lấy | BVSC | khối ngoại trong phiên — nguồn realtime, khớp sàn | chốt |
| `foreignRemain` | Room còn lại | tài liệu endpoint | lấy | BVSC | khối ngoại trong phiên — nguồn realtime, khớp sàn | chốt |
| `foreignRoom` | Tổng room | tài liệu endpoint | lấy | BVSC | khối ngoại trong phiên — nguồn realtime, khớp sàn | chốt |

**Thoả thuận** — 4 trường

| Mã | Tên | Nguồn tên | Lấy/Bỏ | Nguồn chuẩn | Lý do | Trạng thái |
|---|---|---|---|---|---|---|
| `PT_MATCH_QTTY` | Khối lượng lệnh thoả thuận gần nhất | tài liệu endpoint | lấy | BVSC | thoả thuận — nguồn realtime, khớp sàn | chốt |
| `PT_MATCH_PRICE` | Giá lệnh thoả thuận gần nhất | tài liệu endpoint | lấy | BVSC | thoả thuận — nguồn realtime, khớp sàn | chốt |
| `PT_TOTAL_TRADED_QTTY` | Luỹ kế khối lượng thoả thuận trong phiên | tài liệu endpoint | lấy | BVSC | thoả thuận — nguồn realtime, khớp sàn | chốt |
| `PT_TOTAL_TRADED_VALUE` | Luỹ kế giá trị thoả thuận trong phiên | tài liệu endpoint | lấy | BVSC | thoả thuận — nguồn realtime, khớp sàn | chốt |

⚠️ `bidPrice1` và `offerPrice1` trả về dạng **chuỗi**, bậc 2–3 trả về **số** — ép kiểu khi xử lý.
Chỉ báo kỹ thuật **tự tính từ chuỗi giá này**, không lấy của FiinTrade.
`PRIOR_PRICE` để trống tên là cố ý: nó chỉ xuất hiện trong ví dụ response, tài liệu endpoint không mô tả.

## 4 · Screener `getScreenerItems`

59 lấy · 64 bỏ · 4 cần kiểm API — trên 127 trường liệt kê được.

### 4.1 Lấy — 59 trường

**Định giá** — 9 trường

| Mã | Tên | Nguồn tên | Lấy/Bỏ | Nguồn chuẩn | Lý do | Trạng thái |
|---|---|---|---|---|---|---|
| `rtd26` | P/S (TTM) | từ điển | lấy | Screener | tỷ số tài chính — nằm trong cụm 55 tỷ số được nêu đích danh khi chốt nguồn; không nguồn nào khác có | chốt |
| `rtd27` | Giá - T.sản hữu hình (TTM) | từ điển | lấy | Screener | tỷ số tài chính — nằm trong cụm 55 tỷ số được nêu đích danh khi chốt nguồn; không nguồn nào khác có | chốt |
| `rtd28` | Giá - Dòng Tiền (TTM) | từ điển | lấy | Screener | tỷ số tài chính — nằm trong cụm 55 tỷ số được nêu đích danh khi chốt nguồn; không nguồn nào khác có | chốt |
| `rtd40` | Giá - Dòng Tiền Tự Do (TTM) | từ điển | lấy | Screener | tỷ số tài chính — nằm trong cụm 55 tỷ số được nêu đích danh khi chốt nguồn; không nguồn nào khác có | chốt |
| `rtd11` | Vốn hóa | từ điển | lấy | Screener | tỷ số tài chính/định giá — không rơi vào bất kỳ nhóm bỏ nào trong 113 trường bị loại, nên thuộc 80 trường giữ; vốn hoá và EPS là mẫu số của chính các tỷ số FiinTrade nên phải lấy cùng bộ | chốt |
| `rtd21` | P/E (TTM) | từ điển | lấy | Screener | tỷ số tài chính/định giá — không rơi vào bất kỳ nhóm bỏ nào trong 113 trường bị loại, nên thuộc 80 trường giữ; vốn hoá và EPS là mẫu số của chính các tỷ số FiinTrade nên phải lấy cùng bộ | chốt |
| `rtd25` | P/B (TTM) | từ điển | lấy | Screener | tỷ số tài chính/định giá — không rơi vào bất kỳ nhóm bỏ nào trong 113 trường bị loại, nên thuộc 80 trường giữ; vốn hoá và EPS là mẫu số của chính các tỷ số FiinTrade nên phải lấy cùng bộ | chốt |
| `rtd14` | EPS (TTM) | từ điển | lấy | Screener | tỷ số tài chính/định giá — không rơi vào bất kỳ nhóm bỏ nào trong 113 trường bị loại, nên thuộc 80 trường giữ; vốn hoá và EPS là mẫu số của chính các tỷ số FiinTrade nên phải lấy cùng bộ | chốt |
| `rtd7` | Giá trị sổ sách trên mỗi cổ phiếu (BVPS) | từ điển | lấy | Screener | tỷ số tài chính/định giá — không rơi vào bất kỳ nhóm bỏ nào trong 113 trường bị loại, nên thuộc 80 trường giữ; vốn hoá và EPS là mẫu số của chính các tỷ số FiinTrade nên phải lấy cùng bộ | chốt |

**Cổ tức** — 4 trường

| Mã | Tên | Nguồn tên | Lấy/Bỏ | Nguồn chuẩn | Lý do | Trạng thái |
|---|---|---|---|---|---|---|
| `rtd36` | Tỉ Suất Cổ Tức | từ điển | lấy | Screener | tỷ số tài chính — nằm trong cụm 55 tỷ số được nêu đích danh khi chốt nguồn; không nguồn nào khác có · nhóm cổ tức | chốt |
| `rtd43` | Cổ Tức | từ điển | lấy | Screener | tỷ số tài chính — nằm trong cụm 55 tỷ số được nêu đích danh khi chốt nguồn; không nguồn nào khác có · nhóm cổ tức | chốt |
| `rtd51` | Tỉ Lệ Chi Trả Cổ Tức | từ điển | lấy | Screener | tỷ số tài chính — nằm trong cụm 55 tỷ số được nêu đích danh khi chốt nguồn; không nguồn nào khác có · nhóm cổ tức | chốt |
| `rtd20Avg` | Tỉ Suất Cổ Tức T.Bình 3 Năm | từ điển | lấy | Screener | tỷ số tài chính — nằm trong cụm 55 tỷ số được nêu đích danh khi chốt nguồn; không nguồn nào khác có · nhóm cổ tức | chốt |

**Đòn bẩy, thanh toán** — 8 trường

| Mã | Tên | Nguồn tên | Lấy/Bỏ | Nguồn chuẩn | Lý do | Trạng thái |
|---|---|---|---|---|---|---|
| `rtq4` | Nợ dài hạn/ Vốn chủ sở hữu (TTM) | từ điển | lấy | Screener | tỷ số tài chính — nằm trong cụm 55 tỷ số được nêu đích danh khi chốt nguồn; không nguồn nào khác có · nhóm đòn bẩy | chốt |
| `rtq6` | Nợ phải trả/ Vốn chủ sở hữu (TTM) | từ điển | lấy | Screener | tỷ số tài chính — nằm trong cụm 55 tỷ số được nêu đích danh khi chốt nguồn; không nguồn nào khác có · nhóm đòn bẩy | chốt |
| `rtq7` | Nợ phải trả/ Tổng tài sản (TTM) | từ điển | lấy | Screener | tỷ số tài chính — nằm trong cụm 55 tỷ số được nêu đích danh khi chốt nguồn; không nguồn nào khác có · nhóm đòn bẩy | chốt |
| `rtq77` | Khả năng chi trả lãi vay (TTM) | từ điển | lấy | Screener | tỷ số tài chính — nằm trong cụm 55 tỷ số được nêu đích danh khi chốt nguồn; không nguồn nào khác có · nhóm đòn bẩy | chốt |
| `rqq6` | Nợ phải trả/ Vốn chủ sở hữu (quý) | từ điển | lấy | Screener | tỷ số tài chính/định giá — không rơi vào bất kỳ nhóm bỏ nào trong 113 trường bị loại, nên thuộc 80 trường giữ | chốt |
| `rtq3` | Tỉ suất thanh toán hiện hành (TTM) | từ điển | lấy | Screener | tỷ số tài chính/định giá — không rơi vào bất kỳ nhóm bỏ nào trong 113 trường bị loại, nên thuộc 80 trường giữ | chốt |
| `rtq2` | Tỉ suất thanh toán nhanh (TTM) | từ điển | lấy | Screener | tỷ số tài chính/định giá — không rơi vào bất kỳ nhóm bỏ nào trong 113 trường bị loại, nên thuộc 80 trường giữ | chốt |
| `rtq1` | Tỉ suất thanh toán tiền mặt (TTM) | từ điển | lấy | Screener | tỷ số tài chính/định giá — không rơi vào bất kỳ nhóm bỏ nào trong 113 trường bị loại, nên thuộc 80 trường giữ | chốt |

**Tăng trưởng** — 9 trường

| Mã | Tên | Nguồn tên | Lấy/Bỏ | Nguồn chuẩn | Lý do | Trạng thái |
|---|---|---|---|---|---|---|
| `rtq78` | T.trưởng D.thu (YoY) | từ điển | lấy | Screener | tỷ số tài chính — nằm trong cụm 55 tỷ số được nêu đích danh khi chốt nguồn; không nguồn nào khác có · nhóm tăng trưởng | chốt |
| `rtq79` | T.trưởng LN gộp (YoY) | từ điển | lấy | Screener | tỷ số tài chính — nằm trong cụm 55 tỷ số được nêu đích danh khi chốt nguồn; không nguồn nào khác có · nhóm tăng trưởng | chốt |
| `rtq83` | Tăng Trưởng Lãi Thuần | từ điển | lấy | Screener | tỷ số tài chính — nằm trong cụm 55 tỷ số được nêu đích danh khi chốt nguồn; không nguồn nào khác có · nhóm tăng trưởng | chốt |
| `rtd52` | T.trưởng EPS (TTM) | từ điển | lấy | Screener | tỷ số tài chính — nằm trong cụm 55 tỷ số được nêu đích danh khi chốt nguồn; không nguồn nào khác có · nhóm tăng trưởng | chốt |
| `ryq160` | T.trưởng K.doanh 3 năm | từ điển | lấy | Screener | tỷ số tài chính — nằm trong cụm 55 tỷ số được nêu đích danh khi chốt nguồn; không nguồn nào khác có · nhóm tăng trưởng | chốt |
| `ryq166` | T.trưởng LN ròng 3 năm | từ điển | lấy | Screener | tỷ số tài chính — nằm trong cụm 55 tỷ số được nêu đích danh khi chốt nguồn; không nguồn nào khác có · nhóm tăng trưởng | chốt |
| `ryq176` | T.trưởng vốn CSH 3 năm | từ điển | lấy | Screener | tỷ số tài chính — nằm trong cụm 55 tỷ số được nêu đích danh khi chốt nguồn; không nguồn nào khác có · nhóm tăng trưởng | chốt |
| `revGrowth` | Tăng trưởng doanh thu quý gần nhất (YoY) | từ điển | lấy | Screener | tỷ số tài chính/định giá — không rơi vào bất kỳ nhóm bỏ nào trong 113 trường bị loại, nên thuộc 80 trường giữ | chốt |
| `prfGrowth` | Tăng trưởng lợi nhuận thuần quý gần nhất (YoY) | từ điển | lấy | Screener | tỷ số tài chính/định giá — không rơi vào bất kỳ nhóm bỏ nào trong 113 trường bị loại, nên thuộc 80 trường giữ | chốt |

**Sinh lời** — 11 trường

| Mã | Tên | Nguồn tên | Lấy/Bỏ | Nguồn chuẩn | Lý do | Trạng thái |
|---|---|---|---|---|---|---|
| `rqq23` | ROIC (quý) | từ điển | lấy | Screener | tỷ số tài chính — nằm trong cụm 55 tỷ số được nêu đích danh khi chốt nguồn; không nguồn nào khác có · nhóm chỉ tiêu theo quý | chốt |
| `rqq25` | Biên LN gộp (quý) | từ điển | lấy | Screener | tỷ số tài chính — nằm trong cụm 55 tỷ số được nêu đích danh khi chốt nguồn; không nguồn nào khác có · nhóm chỉ tiêu theo quý | chốt |
| `rqq27` | Biên EBIT (quý) | từ điển | lấy | Screener | tỷ số tài chính — nằm trong cụm 55 tỷ số được nêu đích danh khi chốt nguồn; không nguồn nào khác có · nhóm chỉ tiêu theo quý | chốt |
| `rqq29` | Biên LN ròng (quý) | từ điển | lấy | Screener | tỷ số tài chính — nằm trong cụm 55 tỷ số được nêu đích danh khi chốt nguồn; không nguồn nào khác có · nhóm chỉ tiêu theo quý | chốt |
| `rtq12` | ROE (TTM) | từ điển | lấy | Screener | tỷ số tài chính/định giá — không rơi vào bất kỳ nhóm bỏ nào trong 113 trường bị loại, nên thuộc 80 trường giữ | chốt |
| `rtq14` | ROA (TTM) | từ điển | lấy | Screener | tỷ số tài chính/định giá — không rơi vào bất kỳ nhóm bỏ nào trong 113 trường bị loại, nên thuộc 80 trường giữ | chốt |
| `rtq25` | Biên Lãi Gộp | từ điển | lấy | Screener | tỷ số tài chính/định giá — không rơi vào bất kỳ nhóm bỏ nào trong 113 trường bị loại, nên thuộc 80 trường giữ | chốt |
| `ryq25` | Biên Lãi Gộp | từ điển | lấy | Screener | tỷ số tài chính/định giá — không rơi vào bất kỳ nhóm bỏ nào trong 113 trường bị loại, nên thuộc 80 trường giữ | chốt |
| `rtq29` | BIên Lãi Thuần | từ điển | lấy | Screener | tỷ số tài chính/định giá — không rơi vào bất kỳ nhóm bỏ nào trong 113 trường bị loại, nên thuộc 80 trường giữ | chốt |
| `ryq29` | BIên Lãi Thuần | từ điển | lấy | Screener | tỷ số tài chính/định giá — không rơi vào bất kỳ nhóm bỏ nào trong 113 trường bị loại, nên thuộc 80 trường giữ | chốt |
| `rtq27` | Biên EBIT (TTM) | từ điển | lấy | Screener | tỷ số tài chính/định giá — không rơi vào bất kỳ nhóm bỏ nào trong 113 trường bị loại, nên thuộc 80 trường giữ | chốt |

**Beta** — 1 trường

| Mã | Tên | Nguồn tên | Lấy/Bỏ | Nguồn chuẩn | Lý do | Trạng thái |
|---|---|---|---|---|---|---|
| `rtd19` | Beta | từ điển | lấy | Screener | Beta — giữ theo quyết định của chủ dự án: tự tính được nhưng phải chọn chuẩn thị trường và số phiên, kết quả sẽ lệch số FiinTrade | chốt |

**Sở hữu** — 4 trường

| Mã | Tên | Nguồn tên | Lấy/Bỏ | Nguồn chuẩn | Lý do | Trạng thái |
|---|---|---|---|---|---|---|
| `corpOwnership` | Tỉ lệ tổ chức sở hữu | từ điển | lấy | Screener | hai chỉ tiêu sở hữu tổ chức KHÁC NHAU, không phải trùng tên — FPT 0,0567 vs 0,1555, ACB có cái này thiếu cái kia; `GetOwnership` không có tỷ lệ tổng hợp mà chỉ có danh sách cổ đông lớn | chốt |
| `organizationOwnership` | Sở hữu tổ chức (chỉ tiêu thứ hai, khác `corpOwnership`) | tự đặt | lấy | Screener | hai chỉ tiêu sở hữu tổ chức KHÁC NHAU, không phải trùng tên — FPT 0,0567 vs 0,1555, ACB có cái này thiếu cái kia; `GetOwnership` không có tỷ lệ tổng hợp mà chỉ có danh sách cổ đông lớn | chốt |
| `foreignerPercentage` | Sở hữu nước ngoài | từ điển | lấy | Screener | **đo 2026-08-15** — có thật trong khối `stockScreenerItem`, key camelCase `foreignerPercentage`. BVSC `datafeed/instruments` đo cùng lúc chỉ có room theo số cổ phiếu, không có trường tỷ lệ nào. Giá trị trùng khít Snapshot ở BID và FPT (0,17545313 · 0,27350383), lệch nhẹ ở VNM (0,496079 vs 0,49580332). Đây là nguồn duy nhất còn lại → **lấy**, và Snapshot bỏ theo | chốt |
| `freeFloatRate` | % Free Float | từ điển | lấy | Screener | **đo 2026-08-15** — có thật trong khối `stockScreenerItem`, key camelCase `freeFloatRate`, giá trị trùng khít Snapshot cả 3/3 mã đo (BID 0,06 · FPT 0,85 · VNM 0,4). → **lấy** ở Screener, Snapshot bỏ theo | chốt |

**TTM/Y** — 13 trường

| Mã | Tên | Nguồn tên | Lấy/Bỏ | Nguồn chuẩn | Lý do | Trạng thái |
|---|---|---|---|---|---|---|
| `revTTM` | Doanh thu (tỉ đồng) (TTM) | từ điển | lấy | Screener | khối TTM/Y lấy trọn cụm — `isa20TTM` chính là mẫu số P/E của FiinTrade (vốn hoá ÷ `isa20TTM` khớp 9/10 mã VN30) và KHÔNG bằng tổng 4 quý `isa20` (lệch tới 9,4%); tự tính lại sẽ ra P/E khác cột P/E ngay bên cạnh | chốt |
| `revY` | Doanh thu (tỉ đồng) (năm trước) | từ điển | lấy | Screener | khối TTM/Y lấy trọn cụm — `isa20TTM` chính là mẫu số P/E của FiinTrade (vốn hoá ÷ `isa20TTM` khớp 9/10 mã VN30) và KHÔNG bằng tổng 4 quý `isa20` (lệch tới 9,4%); tự tính lại sẽ ra P/E khác cột P/E ngay bên cạnh | chốt |
| `isa1TTM` | Doanh số (TTM) — suy từ `isa1` | suy theo luật kỳ | lấy | Screener | khối TTM/Y lấy trọn cụm — `isa20TTM` chính là mẫu số P/E của FiinTrade (vốn hoá ÷ `isa20TTM` khớp 9/10 mã VN30) và KHÔNG bằng tổng 4 quý `isa20` (lệch tới 9,4%); tự tính lại sẽ ra P/E khác cột P/E ngay bên cạnh | chốt |
| `isa1Y` | Doanh số (năm trước) — suy từ `isa1` | suy theo luật kỳ | lấy | Screener | khối TTM/Y lấy trọn cụm — `isa20TTM` chính là mẫu số P/E của FiinTrade (vốn hoá ÷ `isa20TTM` khớp 9/10 mã VN30) và KHÔNG bằng tổng 4 quý `isa20` (lệch tới 9,4%); tự tính lại sẽ ra P/E khác cột P/E ngay bên cạnh | chốt |
| `isa20TTM` | LN ròng (tỉ đồng) (TTM) | từ điển | lấy | Screener | khối TTM/Y lấy trọn cụm — `isa20TTM` chính là mẫu số P/E của FiinTrade (vốn hoá ÷ `isa20TTM` khớp 9/10 mã VN30) và KHÔNG bằng tổng 4 quý `isa20` (lệch tới 9,4%); tự tính lại sẽ ra P/E khác cột P/E ngay bên cạnh | chốt |
| `isa20Y` | LN ròng (tỉ đồng) (năm trước) | từ điển | lấy | Screener | khối TTM/Y lấy trọn cụm — `isa20TTM` chính là mẫu số P/E của FiinTrade (vốn hoá ÷ `isa20TTM` khớp 9/10 mã VN30) và KHÔNG bằng tổng 4 quý `isa20` (lệch tới 9,4%); tự tính lại sẽ ra P/E khác cột P/E ngay bên cạnh | chốt |
| `isa3TTM` | Doanh số thuần (TTM) — suy từ `isa3` | suy theo luật kỳ | lấy | Screener | khối TTM/Y lấy trọn cụm — `isa20TTM` chính là mẫu số P/E của FiinTrade (vốn hoá ÷ `isa20TTM` khớp 9/10 mã VN30) và KHÔNG bằng tổng 4 quý `isa20` (lệch tới 9,4%); tự tính lại sẽ ra P/E khác cột P/E ngay bên cạnh | chốt |
| `isb25TTM` | Thu nhập lãi và các khoản thu nhập tương tự (TTM) — suy từ `isb25` | suy theo luật kỳ | lấy | Screener | khối TTM/Y lấy trọn cụm — `isa20TTM` chính là mẫu số P/E của FiinTrade (vốn hoá ÷ `isa20TTM` khớp 9/10 mã VN30) và KHÔNG bằng tổng 4 quý `isa20` (lệch tới 9,4%); tự tính lại sẽ ra P/E khác cột P/E ngay bên cạnh | chốt |
| `isb25Y` | Thu nhập lãi và các khoản thu nhập tương tự (năm trước) — suy từ `isb25` | suy theo luật kỳ | lấy | Screener | khối TTM/Y lấy trọn cụm — `isa20TTM` chính là mẫu số P/E của FiinTrade (vốn hoá ÷ `isa20TTM` khớp 9/10 mã VN30) và KHÔNG bằng tổng 4 quý `isa20` (lệch tới 9,4%); tự tính lại sẽ ra P/E khác cột P/E ngay bên cạnh | chốt |
| `isi103TTM` | Doanh thu phí bảo hiểm (TTM) — suy từ `isi103` | suy theo luật kỳ | lấy | Screener | khối TTM/Y lấy trọn cụm — `isa20TTM` chính là mẫu số P/E của FiinTrade (vốn hoá ÷ `isa20TTM` khớp 9/10 mã VN30) và KHÔNG bằng tổng 4 quý `isa20` (lệch tới 9,4%); tự tính lại sẽ ra P/E khác cột P/E ngay bên cạnh | chốt |
| `isi103Y` | Doanh thu phí bảo hiểm (năm trước) — suy từ `isi103` | suy theo luật kỳ | lấy | Screener | khối TTM/Y lấy trọn cụm — `isa20TTM` chính là mẫu số P/E của FiinTrade (vốn hoá ÷ `isa20TTM` khớp 9/10 mã VN30) và KHÔNG bằng tổng 4 quý `isa20` (lệch tới 9,4%); tự tính lại sẽ ra P/E khác cột P/E ngay bên cạnh | chốt |
| `rev` | Doanh thu (tỉ đồng) (quý gần nhất) | từ điển | lấy | Screener | khối TTM/Y lấy trọn cụm — `isa20TTM` chính là mẫu số P/E của FiinTrade (vốn hoá ÷ `isa20TTM` khớp 9/10 mã VN30) và KHÔNG bằng tổng 4 quý `isa20` (lệch tới 9,4%); tự tính lại sẽ ra P/E khác cột P/E ngay bên cạnh | chốt |
| `prf` | Lợi nhuận ròng (tỉ đồng) (quý gần nhất) | từ điển | lấy | Screener | khối TTM/Y lấy trọn cụm — `isa20TTM` chính là mẫu số P/E của FiinTrade (vốn hoá ÷ `isa20TTM` khớp 9/10 mã VN30) và KHÔNG bằng tổng 4 quý `isa20` (lệch tới 9,4%); tự tính lại sẽ ra P/E khác cột P/E ngay bên cạnh | chốt |

### 4.2 Bỏ — 64 trường

**Trùng BVSC** — 4 trường

| Mã | Tên | Nguồn tên | Lấy/Bỏ | Nguồn chuẩn | Lý do | Trạng thái |
|---|---|---|---|---|---|---|
| `closePrice` | Giá | từ điển | bỏ | BVSC | trùng BVSC — `closePrice`/`reference`; giá lấy nguồn realtime khớp sàn | chốt |
| `totalMatchVolume` | Khối lượng GD | từ điển | bỏ | BVSC | trùng BVSC — `totalTrading` | chốt |
| `totalMatchValue` | Giá trị GD | từ điển | bỏ | BVSC | trùng BVSC — `totalTradingValue` | chốt |
| `foreignerRoom` | Room nước ngoài | từ điển | bỏ | BVSC | trùng BVSC — `foreignRemain` (room CÒN LẠI), **không phải** `foreignRoom` (tổng room). Đo 2026-08-15: `foreignerRoom` của Screener khớp cỡ `foreignRemain` của BVSC chứ không khớp `foreignRoom` — BID 906.709.318 vs `foreignRemain` 906.101.718 vs `foreignRoom` 2.184.019.563; FPT 371.145.103 vs 368.745.271 vs 840.019.946. Tên hai bên đặt ngược nhau | chốt |

**Biến động giá** — 7 trường

| Mã | Tên | Nguồn tên | Lấy/Bỏ | Nguồn chuẩn | Lý do | Trạng thái |
|---|---|---|---|---|---|---|
| `percentPriceChange1Day` | Biến động giá 1 ngày | từ điển | bỏ | BVSC (tự tính) | biến động giá — tính lại được từ chuỗi giá BVSC | chốt |
| `percentPriceChange1Week` | Biến động giá 1 tuần | từ điển | bỏ | BVSC (tự tính) | biến động giá — tính lại được từ chuỗi giá BVSC | chốt |
| `percentPriceChange1Month` | Biến động giá 1 tháng | từ điển | bỏ | BVSC (tự tính) | biến động giá — tính lại được từ chuỗi giá BVSC | chốt |
| `percentPriceChange3Month` | Biến động giá 3 tháng | từ điển | bỏ | BVSC (tự tính) | biến động giá — tính lại được từ chuỗi giá BVSC | chốt |
| `percentPriceChange6Month` | Biến động giá 6 tháng | từ điển | bỏ | BVSC (tự tính) | biến động giá — tính lại được từ chuỗi giá BVSC | chốt |
| `percentPriceChange52Week` | Biến động giá 52 tuần | từ điển | bỏ | BVSC (tự tính) | biến động giá — tính lại được từ chuỗi giá BVSC | chốt |
| `percentPriceChangeYTD` | Biến động giá từ đầu năm | từ điển | bỏ | BVSC (tự tính) | biến động giá — tính lại được từ chuỗi giá BVSC | chốt |

**KL bình quân** — 4 trường

| Mã | Tên | Nguồn tên | Lấy/Bỏ | Nguồn chuẩn | Lý do | Trạng thái |
|---|---|---|---|---|---|---|
| `averageVolume1Week` | Kl T.bình 5 phiên | từ điển | bỏ | BVSC (tự tính) | khối lượng bình quân 5/10/20 phiên và 3 tháng — tính lại được từ chuỗi khối lượng BVSC | chốt |
| `averageVolume2Week` | Kl T.bình 10 phiên | từ điển | bỏ | BVSC (tự tính) | khối lượng bình quân 5/10/20 phiên và 3 tháng — tính lại được từ chuỗi khối lượng BVSC | chốt |
| `averageVolume1Month` | Kl T.bình 20 phiên | từ điển | bỏ | BVSC (tự tính) | khối lượng bình quân 5/10/20 phiên và 3 tháng — tính lại được từ chuỗi khối lượng BVSC | chốt |
| `averageVolume3Month` | Kl T.bình 3 tháng | từ điển | bỏ | BVSC (tự tính) | khối lượng bình quân 5/10/20 phiên và 3 tháng — tính lại được từ chuỗi khối lượng BVSC | chốt |

**Chấm điểm** — 13 trường

| Mã | Tên | Nguồn tên | Lấy/Bỏ | Nguồn chuẩn | Lý do | Trạng thái |
|---|---|---|---|---|---|---|
| `icbRank` | FiinTrade Rank | từ điển | bỏ | — (không lưu) | nhóm chấm điểm riêng của FiinTrade — quyết định của chủ dự án: không dùng điểm do bên thứ ba chấm | chốt |
| `value` | Value (FiinTrade Score) | từ điển | bỏ | — (không lưu) | nhóm chấm điểm riêng của FiinTrade — quyết định của chủ dự án: không dùng điểm do bên thứ ba chấm | chốt |
| `growth` | Growth (FiinTrade Score) | từ điển | bỏ | — (không lưu) | nhóm chấm điểm riêng của FiinTrade — quyết định của chủ dự án: không dùng điểm do bên thứ ba chấm | chốt |
| `momentum` | Momentum (FiinTrade Score) | từ điển | bỏ | — (không lưu) | nhóm chấm điểm riêng của FiinTrade — quyết định của chủ dự án: không dùng điểm do bên thứ ba chấm | chốt |
| `vgm` | VGM (FiinTrade Score) | từ điển | bỏ | — (không lưu) | nhóm chấm điểm riêng của FiinTrade — quyết định của chủ dự án: không dùng điểm do bên thứ ba chấm | chốt |
| `fScore` | F-Score (TTM) | từ điển | bỏ | — (không lưu) | nhóm chấm điểm riêng của FiinTrade — quyết định của chủ dự án: không dùng điểm do bên thứ ba chấm | chốt |
| `canslim` | Canslim (TTM) | từ điển | bỏ | — (không lưu) | nhóm chấm điểm riêng của FiinTrade — quyết định của chủ dự án: không dùng điểm do bên thứ ba chấm | chốt |
| `capitalStructure` | Thành phần chấm điểm VGM | tự đặt | bỏ | — (không lưu) | thành phần chấm điểm VGM — bỏ cùng nhóm chấm điểm, không dùng điểm bên thứ ba chấm | chốt |
| `financialStrength` | Thành phần chấm điểm VGM | tự đặt | bỏ | — (không lưu) | thành phần chấm điểm VGM — bỏ cùng nhóm chấm điểm, không dùng điểm bên thứ ba chấm | chốt |
| `financialPlan` | Thành phần chấm điểm VGM | tự đặt | bỏ | — (không lưu) | thành phần chấm điểm VGM — bỏ cùng nhóm chấm điểm, không dùng điểm bên thứ ba chấm | chốt |
| `cfo` | Thành phần chấm điểm VGM | tự đặt | bỏ | — (không lưu) | thành phần chấm điểm VGM — bỏ cùng nhóm chấm điểm, không dùng điểm bên thứ ba chấm | chốt |
| `debt` | Thành phần chấm điểm VGM | tự đặt | bỏ | — (không lưu) | thành phần chấm điểm VGM — bỏ cùng nhóm chấm điểm, không dùng điểm bên thứ ba chấm | chốt |
| `equityInssurance` | Thành phần chấm điểm VGM | tự đặt | bỏ | — (không lưu) | thành phần chấm điểm VGM — bỏ cùng nhóm chấm điểm, không dùng điểm bên thứ ba chấm | chốt |

**Chỉ báo kỹ thuật** — 17 trường

| Mã | Tên | Nguồn tên | Lấy/Bỏ | Nguồn chuẩn | Lý do | Trạng thái |
|---|---|---|---|---|---|---|
| `rsi` | RSI | từ điển | bỏ | BVSC (tự tính) | chỉ báo kỹ thuật — tự tính từ giá BVSC; lấy của FiinTrade thì chỉ báo và giá đến từ hai chuỗi khác nhau | chốt |
| `adx` | ADX | từ điển | bỏ | BVSC (tự tính) | chỉ báo kỹ thuật — tự tính từ giá BVSC; lấy của FiinTrade thì chỉ báo và giá đến từ hai chuỗi khác nhau | chốt |
| `cci` | CCI | từ điển | bỏ | BVSC (tự tính) | chỉ báo kỹ thuật — tự tính từ giá BVSC; lấy của FiinTrade thì chỉ báo và giá đến từ hai chuỗi khác nhau | chốt |
| `roc` | ROC | từ điển | bỏ | BVSC (tự tính) | chỉ báo kỹ thuật — tự tính từ giá BVSC; lấy của FiinTrade thì chỉ báo và giá đến từ hai chuỗi khác nhau | chốt |
| `stochastic` | STOCH | từ điển | bỏ | BVSC (tự tính) | chỉ báo kỹ thuật — tự tính từ giá BVSC; lấy của FiinTrade thì chỉ báo và giá đến từ hai chuỗi khác nhau | chốt |
| `williams` | Williams | từ điển | bỏ | BVSC (tự tính) | chỉ báo kỹ thuật — tự tính từ giá BVSC; lấy của FiinTrade thì chỉ báo và giá đến từ hai chuỗi khác nhau | chốt |
| `mfi` | MFI | từ điển | bỏ | BVSC (tự tính) | chỉ báo kỹ thuật — tự tính từ giá BVSC; lấy của FiinTrade thì chỉ báo và giá đến từ hai chuỗi khác nhau | chốt |
| `ma9` | Trung bình động 9 phiên | tự đặt | bỏ | BVSC (tự tính) | chỉ báo kỹ thuật — tự tính từ giá BVSC; lấy của FiinTrade thì chỉ báo và giá đến từ hai chuỗi khác nhau | chốt |
| `ma20` | Trung bình động 20 phiên | tự đặt | bỏ | BVSC (tự tính) | chỉ báo kỹ thuật — tự tính từ giá BVSC; lấy của FiinTrade thì chỉ báo và giá đến từ hai chuỗi khác nhau | chốt |
| `ma50` | Trung bình động 50 phiên | tự đặt | bỏ | BVSC (tự tính) | chỉ báo kỹ thuật — tự tính từ giá BVSC; lấy của FiinTrade thì chỉ báo và giá đến từ hai chuỗi khác nhau | chốt |
| `ma75` | Trung bình động 75 phiên | tự đặt | bỏ | BVSC (tự tính) | chỉ báo kỹ thuật — tự tính từ giá BVSC; lấy của FiinTrade thì chỉ báo và giá đến từ hai chuỗi khác nhau | chốt |
| `ma100` | Trung bình động 100 phiên | tự đặt | bỏ | BVSC (tự tính) | chỉ báo kỹ thuật — tự tính từ giá BVSC; lấy của FiinTrade thì chỉ báo và giá đến từ hai chuỗi khác nhau | chốt |
| `ma200` | Trung bình động 200 phiên | tự đặt | bỏ | BVSC (tự tính) | chỉ báo kỹ thuật — tự tính từ giá BVSC; lấy của FiinTrade thì chỉ báo và giá đến từ hai chuỗi khác nhau | chốt |
| `sma20` | Trung bình động giản đơn 20 phiên | tự đặt | bỏ | BVSC (tự tính) | chỉ báo kỹ thuật — tự tính từ giá BVSC; lấy của FiinTrade thì chỉ báo và giá đến từ hai chuỗi khác nhau | chốt |
| `sma50` | Trung bình động giản đơn 50 phiên | tự đặt | bỏ | BVSC (tự tính) | chỉ báo kỹ thuật — tự tính từ giá BVSC; lấy của FiinTrade thì chỉ báo và giá đến từ hai chuỗi khác nhau | chốt |
| `sma100` | Trung bình động giản đơn 100 phiên | tự đặt | bỏ | BVSC (tự tính) | chỉ báo kỹ thuật — tự tính từ giá BVSC; lấy của FiinTrade thì chỉ báo và giá đến từ hai chuỗi khác nhau | chốt |
| `overSma50` | Giá so với trung bình động 50 phiên (đo 2026-08-15: kiểu bool) | tự đặt | bỏ | BVSC (tự tính) | chỉ báo kỹ thuật — tự tính từ giá BVSC; lấy của FiinTrade thì chỉ báo và giá đến từ hai chuỗi khác nhau | chốt |

**OHLC 2 phiên** — 8 trường

| Mã | Tên | Nguồn tên | Lấy/Bỏ | Nguồn chuẩn | Lý do | Trạng thái |
|---|---|---|---|---|---|---|
| `c1` | OHLC hai phiên gần nhất | tự đặt | bỏ | BVSC | OHLC hai phiên gần nhất — đã có trong chuỗi giá BVSC | chốt |
| `c2` | OHLC hai phiên gần nhất | tự đặt | bỏ | BVSC | OHLC hai phiên gần nhất — đã có trong chuỗi giá BVSC | chốt |
| `h1` | OHLC hai phiên gần nhất | tự đặt | bỏ | BVSC | OHLC hai phiên gần nhất — đã có trong chuỗi giá BVSC | chốt |
| `h2` | OHLC hai phiên gần nhất | tự đặt | bỏ | BVSC | OHLC hai phiên gần nhất — đã có trong chuỗi giá BVSC | chốt |
| `l1` | OHLC hai phiên gần nhất | tự đặt | bỏ | BVSC | OHLC hai phiên gần nhất — đã có trong chuỗi giá BVSC | chốt |
| `l2` | OHLC hai phiên gần nhất | tự đặt | bỏ | BVSC | OHLC hai phiên gần nhất — đã có trong chuỗi giá BVSC | chốt |
| `o1` | OHLC hai phiên gần nhất | tự đặt | bỏ | BVSC | OHLC hai phiên gần nhất — đã có trong chuỗi giá BVSC | chốt |
| `o2` | OHLC hai phiên gần nhất | tự đặt | bỏ | BVSC | OHLC hai phiên gần nhất — đã có trong chuỗi giá BVSC | chốt |

**Trùng BCTC** — 3 trường

| Mã | Tên | Nguồn tên | Lấy/Bỏ | Nguồn chuẩn | Lý do | Trạng thái |
|---|---|---|---|---|---|---|
| `isa20` | LỢI NHUẬN THUẦN | từ điển | bỏ | BCTC đầy đủ | trùng bộ báo cáo tài chính đầy đủ — nguồn chuẩn cho mọi mã `bs*` `is*` `cf*` `no*` là bộ 556 mã | chốt |
| `isa22` | LỢI NHUẬN THUẦN | từ điển | bỏ | BCTC đầy đủ | trùng bộ báo cáo tài chính đầy đủ — nguồn chuẩn cho mọi mã `bs*` `is*` `cf*` `no*` là bộ 556 mã | chốt |
| `cfa18` | Lưu chuyển tiền thuần từ hoạt động kinh doanh | từ điển | bỏ | BCTC đầy đủ | trùng bộ báo cáo tài chính đầy đủ — nguồn chuẩn cho mọi mã `bs*` `is*` `cf*` `no*` là bộ 556 mã | chốt |

**Sức mạnh tương đối** — 2 trường

| Mã | Tên | Nguồn tên | Lấy/Bỏ | Nguồn chuẩn | Lý do | Trạng thái |
|---|---|---|---|---|---|---|
| `rs52w` | Sức mạnh tương đối 52 tuần | tự đặt | bỏ | BVSC (tự tính) | sức mạnh tương đối — tính lại được từ chuỗi giá BVSC | chốt |
| `rs6m` | Sức mạnh tương đối 6 tháng | tự đặt | bỏ | BVSC (tự tính) | sức mạnh tương đối — tính lại được từ chuỗi giá BVSC | chốt |

**Trùng MoneyFlow** — 2 trường

| Mã | Tên | Nguồn tên | Lấy/Bỏ | Nguồn chuẩn | Lý do | Trạng thái |
|---|---|---|---|---|---|---|
| `totalBuyTradeVolume` | Khối lượng theo chiều mua | tự đặt | bỏ | MoneyFlow | trùng MoneyFlow — chuỗi mua/bán chủ động lấy trọn bộ ở MoneyFlow | chốt |
| `totalSellTradeVolume` | Khối lượng theo chiều bán | tự đặt | bỏ | MoneyFlow | trùng MoneyFlow — chuỗi mua/bán chủ động lấy trọn bộ ở MoneyFlow | chốt |

**GTGD bình quân** — 4 trường

| Mã | Tên | Nguồn tên | Lấy/Bỏ | Nguồn chuẩn | Lý do | Trạng thái |
|---|---|---|---|---|---|---|
| `averageValue1Week` | Giá trị GD T.bình 5D | từ điển | bỏ | BVSC (tự tính) | **đo 2026-08-15** — có thật, key camelCase `averageValue1Week`…, nằm ngay cạnh `averageVolume*` trong cùng khối `stockScreenerItem` và cùng dạng chuỗi bình quân 5/10/20 phiên + 3 tháng. BVSC `datafeed/instruments` đo cùng lúc có `totalTradingValue` theo phiên, nên chuỗi GTGD bình quân tính lại được y như chuỗi KL bình quân → cùng nhóm lý do với `averageVolume*`, **bỏ** | chốt |
| `averageValue2Week` | Giá trị GD T.bình 10D | từ điển | bỏ | BVSC (tự tính) | **đo 2026-08-15** — có thật, key camelCase `averageValue1Week`…, nằm ngay cạnh `averageVolume*` trong cùng khối `stockScreenerItem` và cùng dạng chuỗi bình quân 5/10/20 phiên + 3 tháng. BVSC `datafeed/instruments` đo cùng lúc có `totalTradingValue` theo phiên, nên chuỗi GTGD bình quân tính lại được y như chuỗi KL bình quân → cùng nhóm lý do với `averageVolume*`, **bỏ** | chốt |
| `averageValue1Month` | Giá trị GD T.bình 20D | từ điển | bỏ | BVSC (tự tính) | **đo 2026-08-15** — có thật, key camelCase `averageValue1Week`…, nằm ngay cạnh `averageVolume*` trong cùng khối `stockScreenerItem` và cùng dạng chuỗi bình quân 5/10/20 phiên + 3 tháng. BVSC `datafeed/instruments` đo cùng lúc có `totalTradingValue` theo phiên, nên chuỗi GTGD bình quân tính lại được y như chuỗi KL bình quân → cùng nhóm lý do với `averageVolume*`, **bỏ** | chốt |
| `averageValue3Month` | Giá trị GD T.bình 3M | từ điển | bỏ | BVSC (tự tính) | **đo 2026-08-15** — có thật, key camelCase `averageValue1Week`…, nằm ngay cạnh `averageVolume*` trong cùng khối `stockScreenerItem` và cùng dạng chuỗi bình quân 5/10/20 phiên + 3 tháng. BVSC `datafeed/instruments` đo cùng lúc có `totalTradingValue` theo phiên, nên chuỗi GTGD bình quân tính lại được y như chuỗi KL bình quân → cùng nhóm lý do với `averageVolume*`, **bỏ** | chốt |

### 4.3 Cần kiểm API — 4 trường

**Chưa giải mã** — 4 trường

| Mã | Tên | Nguồn tên | Lấy/Bỏ | Nguồn chuẩn | Lý do | Trạng thái |
|---|---|---|---|---|---|---|
| `rtd53` | — | — | chưa rõ | — | có trong từ điển 729 mã nhưng mang trạng thái CHƯA GIẢI MÃ — không nguồn nào có tên, chưa biết là chỉ tiêu gì nên chưa xếp được vào nhóm nào. **Đo 2026-08-15**: cả hai CÓ THẬT trong khối `financial` và có giá trị (FPT `rtd53`=5426,73780245 `rtq81`=−0,03335415 · VNM 4702,49259309 và 0,22632399 · BID cả hai `null`) — nhưng số đo chỉ chứng minh trường tồn tại, KHÔNG cho ra tên, nên vẫn chưa xếp được | cần kiểm API |
| `rtq81` | — | — | chưa rõ | — | có trong từ điển 729 mã nhưng mang trạng thái CHƯA GIẢI MÃ — không nguồn nào có tên, chưa biết là chỉ tiêu gì nên chưa xếp được vào nhóm nào. **Đo 2026-08-15**: cả hai CÓ THẬT trong khối `financial` và có giá trị (FPT `rtd53`=5426,73780245 `rtq81`=−0,03335415 · VNM 4702,49259309 và 0,22632399 · BID cả hai `null`) — nhưng số đo chỉ chứng minh trường tồn tại, KHÔNG cho ra tên, nên vẫn chưa xếp được | cần kiểm API |
| `rtd39` | — | — | chưa rõ | — | có mặt trong khối `financial` của response nhưng KHÔNG có trong từ điển 729 mã — chưa biết là chỉ tiêu gì. **Đo 2026-08-15**: đã dump khoá khối `financial` — cả hai CÓ THẬT và có giá trị (`rtd39` BID 3,42582495 · FPT 15,93348656 · VNM 15,38168732; `rtd54` FPT 12,5858301 · VNM 13,09943584 · BID `null`). Vế *có thật không* đã xong; vế *là chỉ tiêu gì* thì số đo không trả lời được nên vẫn giữ | cần kiểm API |
| `rtd54` | — | — | chưa rõ | — | có mặt trong khối `financial` của response nhưng KHÔNG có trong từ điển 729 mã — chưa biết là chỉ tiêu gì. **Đo 2026-08-15**: đã dump khoá khối `financial` — cả hai CÓ THẬT và có giá trị (`rtd39` BID 3,42582495 · FPT 15,93348656 · VNM 15,38168732; `rtd54` FPT 12,5858301 · VNM 13,09943584 · BID `null`). Vế *có thật không* đã xong; vế *là chỉ tiêu gì* thì số đo không trả lời được nên vẫn giữ | cần kiểm API |

✅ **`freeFloatRate` và `foreignerPercentage` đã chốt bằng số đo 2026-08-15 — không còn treo.** Trước đây hai
mã này phải chốt cùng lúc với §5.2 (Snapshot bỏ chúng với nguồn chuẩn *dự kiến* là Screener), và rủi ro là
**không nguồn nào lưu**. Lời gọi thật đã trả lời: cả hai có mặt trong khối `stockScreenerItem`, giá trị trùng
khít Snapshot, nên **Screener giữ · Snapshot bỏ** — xem §4.1 và §5.2. Không còn thứ tự cài đặt nào phải chờ.

🔴 **Bẫy tên ngược ở `foreignerRoom`** *(đo 2026-08-15)*. Screener `foreignerRoom` là **room CÒN LẠI**, cùng
nghĩa với `foreignRemain` của BVSC — **không phải** `foreignRoom` (tổng room) dù tên gần giống hệt. Số đo:
BID `foreignerRoom` = 906.709.318 · BVSC `foreignRemain` = 906.101.718 · BVSC `foreignRoom` = 2.184.019.563.
Tổng room của Screener nằm ở khoá khác, trong khối `priceInfo`: `foreignTotalRoom` (BID 2.184.019.563, bằng
đúng `foreignRoom` của BVSC). Ánh xạ nhầm hai khoá này là **sai 2–2,4 lần** mà không có gì báo
*(tỷ lệ đo được: BID 2,409 · FPT 2,263 · VNM 1,984 — không phải hằng số)*.

## 5 · Snapshot `GetSnapshot` / `GetSnapshotNoneBank`

18 lấy · 32 bỏ · 2 chưa rõ — trên 52 trường liệt kê được
(28 trường khối `summary` + các mã được nêu đích danh trong khối `quarterly`/`yearly`).

🔴 Chọn sai endpoint **không báo lỗi** mà làm gần một nửa số trường thành `null`: `comTypeCode = NH` dùng
`GetSnapshot`, còn `CT` `CK` `BH` dùng `GetSnapshotNoneBank`.

### 5.1 Lấy — 18 trường

**Hồ sơ doanh nghiệp** — 4 trường

| Mã | Tên | Nguồn tên | Lấy/Bỏ | Nguồn chuẩn | Lý do | Trạng thái |
|---|---|---|---|---|---|---|
| `ceo` | Tên tổng giám đốc | tài liệu endpoint | lấy | Snapshot | hồ sơ doanh nghiệp — chỉ Snapshot có; `competitors` là danh sách mã cùng ngành, dùng ngay cho so sánh ngang ngành; `comTypeCode` quyết định gọi `GetSnapshot` hay `GetSnapshotNoneBank` | chốt |
| `competitors` | Danh sách mã cùng ngành để so sánh | tài liệu endpoint | lấy | Snapshot | hồ sơ doanh nghiệp — chỉ Snapshot có; `competitors` là danh sách mã cùng ngành, dùng ngay cho so sánh ngang ngành; `comTypeCode` quyết định gọi `GetSnapshot` hay `GetSnapshotNoneBank` | chốt |
| `majorHoldings` | Các khoản đầu tư lớn | tài liệu endpoint | lấy | Snapshot | hồ sơ doanh nghiệp — chỉ Snapshot có; `competitors` là danh sách mã cùng ngành, dùng ngay cho so sánh ngang ngành; `comTypeCode` quyết định gọi `GetSnapshot` hay `GetSnapshotNoneBank` | chốt |
| `comTypeCode` | Loại hình doanh nghiệp | tài liệu endpoint | lấy | Snapshot | hồ sơ doanh nghiệp — chỉ Snapshot có; `competitors` là danh sách mã cùng ngành, dùng ngay cho so sánh ngang ngành; `comTypeCode` quyết định gọi `GetSnapshot` hay `GetSnapshotNoneBank` | chốt |

**Sở hữu chi tiết** — 7 trường

| Mã | Tên | Nguồn tên | Lấy/Bỏ | Nguồn chuẩn | Lý do | Trạng thái |
|---|---|---|---|---|---|---|
| `statePercentage` | Tỷ lệ sở hữu nhà nước | tài liệu endpoint | lấy | Snapshot | sở hữu chi tiết — nằm trong 16 trường độc quyền của Snapshot, không nguồn nào khác có | chốt |
| `stateVolumn` | Khối lượng nhà nước nắm | tài liệu endpoint | lấy | Snapshot | sở hữu chi tiết — nằm trong 16 trường độc quyền của Snapshot, không nguồn nào khác có | chốt |
| `foreignerVolumn` | Khối lượng nước ngoài nắm | tài liệu endpoint | lấy | Snapshot | sở hữu chi tiết — nằm trong 16 trường độc quyền của Snapshot, không nguồn nào khác có | chốt |
| `totalForeignRoom` | Tổng room | tài liệu endpoint | lấy | Snapshot | sở hữu chi tiết — nằm trong 16 trường độc quyền của Snapshot, không nguồn nào khác có | chốt |
| `maximumForeignPercentage` | Trần sở hữu nước ngoài | tài liệu endpoint | lấy | Snapshot | sở hữu chi tiết — nằm trong 16 trường độc quyền của Snapshot, không nguồn nào khác có | chốt |
| `outstandingShare` | Số CP đang lưu hành | tài liệu endpoint | lấy | Snapshot | **đo 2026-08-15** — phép kiểm đã định sẵn là *bằng `ListedShare` của BVSC thì bỏ, khác thì lấy*. Kết quả: BID 7.280.065.210 và VNM 2.089.955.445 bằng đúng `ListedShare`, nhưng **FPT 1.714.326.422 vs `ListedShare` 1.703.507.121 — lệch 10.819.301 CP (0,64%)**. Hai bên KHÔNG bằng nhau ⇒ **lấy** | chốt |
| `freeFloat` | Khối lượng tự do chuyển nhượng | tài liệu endpoint | lấy | Snapshot | **đo 2026-08-15** — đã dump đủ 193 khoá `getScreenerItems`: Screener chỉ có tỷ lệ `freeFloatRate`, KHÔNG có trường khối lượng free float nào; BVSC `datafeed/instruments` (62 khoá) cũng không có. Snapshot là nguồn duy nhất (BID 436.803.912 · FPT 1.457.177.458 · VNM 835.982.178) ⇒ **lấy** | chốt |

**Chỉ tiêu riêng** — 5 trường

| Mã | Tên | Nguồn tên | Lấy/Bỏ | Nguồn chuẩn | Lý do | Trạng thái |
|---|---|---|---|---|---|---|
| `rtq10` | Nợ/VCSH | từ điển | lấy | Snapshot | chỉ tiêu riêng của Snapshot — không có trong 83 tiêu chí Screener | chốt |
| `rtq44` | Biên lãi thuần (NIM) | từ điển | lấy | Snapshot | chỉ tiêu riêng của Snapshot — không có trong 83 tiêu chí Screener | chốt |
| `rtq137` | — | — | lấy | Snapshot | chỉ tiêu riêng của Snapshot — không có trong 83 tiêu chí Screener | chốt |
| `rqq41` | — | — | lấy | Snapshot | chỉ tiêu riêng của Snapshot — không có trong 83 tiêu chí Screener | chốt |
| `valuePerShare` | Mệnh giá | tài liệu endpoint | lấy | Snapshot | chỉ tiêu riêng của Snapshot — không có trong 83 tiêu chí Screener | chốt |

**Metadata** — 2 trường

| Mã | Tên | Nguồn tên | Lấy/Bỏ | Nguồn chuẩn | Lý do | Trạng thái |
|---|---|---|---|---|---|---|
| `year` | Năm báo cáo | tự đặt | lấy | Snapshot | metadata kỳ báo cáo — bắt buộc để gắn chuỗi `quarterly`/`yearly` vào đúng kỳ | chốt |
| `quarter` | Quý báo cáo | tự đặt | lấy | Snapshot | metadata kỳ báo cáo — bắt buộc để gắn chuỗi `quarterly`/`yearly` vào đúng kỳ | chốt |

⚠️ `rtq137` và `rqq41` **được giữ dù chưa có tên** — từ điển 729 mã ghi trạng thái chưa giải mã cho cả hai.
Giữ vì đây là chỉ tiêu chỉ Snapshot có, không phải vì đã hiểu nó là gì. Manh mối đã đo được: `rtq137` chỉ
ngân hàng mới có, dải 0,47%–2,23%, luôn nhỏ hơn NIM. Lưu thô, đừng gắn nhãn cho người dùng cuối cho tới khi
có tên chính thức.

### 5.2 Bỏ — 32 trường

**Trùng Screener** — 13 trường

| Mã | Tên | Nguồn tên | Lấy/Bỏ | Nguồn chuẩn | Lý do | Trạng thái |
|---|---|---|---|---|---|---|
| `rtd11` | Vốn hóa | từ điển | bỏ | Screener | trùng Screener — cùng mã, lấy ở Screener cho trọn bộ tỷ số | chốt |
| `rtd14` | EPS (TTM) | từ điển | bỏ | Screener | trùng Screener — cùng mã, lấy ở Screener cho trọn bộ tỷ số | chốt |
| `rtd21` | P/E (TTM) | từ điển | bỏ | Screener | trùng Screener — cùng mã, lấy ở Screener cho trọn bộ tỷ số | chốt |
| `rtd25` | P/B (TTM) | từ điển | bỏ | Screener | trùng Screener — cùng mã, lấy ở Screener cho trọn bộ tỷ số | chốt |
| `rtq12` | ROE (TTM) | từ điển | bỏ | Screener | trùng Screener — cùng mã, lấy ở Screener cho trọn bộ tỷ số | chốt |
| `rtq14` | ROA (TTM) | từ điển | bỏ | Screener | trùng Screener — cùng mã, lấy ở Screener cho trọn bộ tỷ số | chốt |
| `rtq29` | BIên Lãi Thuần | từ điển | bỏ | Screener | trùng Screener — cùng mã, lấy ở Screener cho trọn bộ tỷ số | chốt |
| `freeFloatRate` | Tỷ lệ free float | tài liệu endpoint | bỏ | Screener | trùng Screener — **đo 2026-08-15 đã gỡ điều kiện**: cả hai có thật ở khối `stockScreenerItem` của `getScreenerItems` và đã chốt **lấy** bên Screener (xem §4.1), nên bỏ ở đây là bỏ đúng, không còn là *chờ chốt*. Giá trị hai bên trùng khít trên `freeFloatRate` 3/3 mã và trên `foreignerPercentage` 2/3 (VNM lệch 0,000276 — cùng chỉ tiêu, khác thời điểm chốt số) | chốt |
| `foreignerPercentage` | Tỷ lệ sở hữu nước ngoài | tài liệu endpoint | bỏ | Screener | trùng Screener — **đo 2026-08-15 đã gỡ điều kiện**: cả hai có thật ở khối `stockScreenerItem` của `getScreenerItems` và đã chốt **lấy** bên Screener (xem §4.1), nên bỏ ở đây là bỏ đúng, không còn là *chờ chốt*. Giá trị hai bên trùng khít trên `freeFloatRate` 3/3 mã và trên `foreignerPercentage` 2/3 (VNM lệch 0,000276 — cùng chỉ tiêu, khác thời điểm chốt số) | chốt |
| `rtq25` | Biên Lãi Gộp | từ điển | bỏ | Screener | trùng Screener — cùng mã trong 83 tiêu chí, lấy ở Screener | chốt |
| `rtq1` | Tỉ suất thanh toán tiền mặt (TTM) | từ điển | bỏ | Screener | trùng Screener — cùng mã trong 83 tiêu chí, lấy ở Screener | chốt |
| `rtq2` | Tỉ suất thanh toán nhanh (TTM) | từ điển | bỏ | Screener | trùng Screener — cùng mã trong 83 tiêu chí, lấy ở Screener | chốt |
| `rtq3` | Tỉ suất thanh toán hiện hành (TTM) | từ điển | bỏ | Screener | trùng Screener — cùng mã trong 83 tiêu chí, lấy ở Screener | chốt |

**Trùng BVSC** — 4 trường

| Mã | Tên | Nguồn tên | Lấy/Bỏ | Nguồn chuẩn | Lý do | Trạng thái |
|---|---|---|---|---|---|---|
| `foreignerRoom` | Room còn lại | tài liệu endpoint | bỏ | BVSC | trùng BVSC — `foreignRemain` (room còn lại) | chốt |
| `lowestPrice1Year` | Thấp nhất 52 tuần | tài liệu endpoint | bỏ | BVSC (tự tính) | giá thấp nhất/cao nhất 52 tuần — dẫn xuất từ chuỗi giá, nguồn chuẩn là giá BVSC | chốt |
| `highestPrice1Year` | Cao nhất 52 tuần | tài liệu endpoint | bỏ | BVSC (tự tính) | giá thấp nhất/cao nhất 52 tuần — dẫn xuất từ chuỗi giá, nguồn chuẩn là giá BVSC | chốt |
| `averageMatchVolume1Month` | KLGD bình quân 1 tháng | tài liệu endpoint | bỏ | BVSC (tự tính) | KLGD bình quân 1 tháng — tính lại từ chuỗi khối lượng BVSC; Screener cũng có trường tương đương `averageVolume1Month` và cũng bỏ | chốt |

**Trùng BCTC** — 15 trường

| Mã | Tên | Nguồn tên | Lấy/Bỏ | Nguồn chuẩn | Lý do | Trạng thái |
|---|---|---|---|---|---|---|
| `isa1` | Doanh số | từ điển | bỏ | BCTC đầy đủ | trùng bộ báo cáo tài chính đầy đủ — nguồn chuẩn cho mọi mã `bs*` `is*` `cf*` `no*` là bộ 556 mã | chốt |
| `isa22` | LỢI NHUẬN THUẦN | từ điển | bỏ | BCTC đầy đủ | trùng bộ báo cáo tài chính đầy đủ — nguồn chuẩn cho mọi mã `bs*` `is*` `cf*` `no*` là bộ 556 mã | chốt |
| `isb27` | Thu nhập lãi thuần | từ điển | bỏ | BCTC đầy đủ | trùng bộ báo cáo tài chính đầy đủ — nguồn chuẩn cho mọi mã `bs*` `is*` `cf*` `no*` là bộ 556 mã | chốt |
| `isi103` | Doanh thu phí bảo hiểm | từ điển | bỏ | BCTC đầy đủ | trùng bộ báo cáo tài chính đầy đủ — nguồn chuẩn cho mọi mã `bs*` `is*` `cf*` `no*` là bộ 556 mã | chốt |
| `bsa53` | TỔNG TÀI SẢN | từ điển | bỏ | BCTC đầy đủ | trùng bộ báo cáo tài chính đầy đủ — nguồn chuẩn cho mọi mã `bs*` `is*` `cf*` `no*` là bộ 556 mã | chốt |
| `bsb104` | Cho vay khách hàng | từ điển | bỏ | BCTC đầy đủ | trùng bộ báo cáo tài chính đầy đủ — nguồn chuẩn cho mọi mã `bs*` `is*` `cf*` `no*` là bộ 556 mã | chốt |
| `bsa1` | TÀI SẢN NGẮN HẠN | từ điển | bỏ | BCTC đầy đủ | trùng bộ báo cáo tài chính đầy đủ — nguồn chuẩn cho mọi mã `bs*` `is*` `cf*` `no*` là bộ 556 mã | chốt |
| `bsa23` | TÀI SẢN DÀI HẠN | từ điển | bỏ | BCTC đầy đủ | trùng bộ báo cáo tài chính đầy đủ — nguồn chuẩn cho mọi mã `bs*` `is*` `cf*` `no*` là bộ 556 mã | chốt |
| `bsa54` | NỢ PHẢI TRẢ | từ điển | bỏ | BCTC đầy đủ | trùng bộ báo cáo tài chính đầy đủ — nguồn chuẩn cho mọi mã `bs*` `is*` `cf*` `no*` là bộ 556 mã | chốt |
| `bsa78` | VỐN CHỦ SỞ HỮU | từ điển | bỏ | BCTC đầy đủ | trùng bộ báo cáo tài chính đầy đủ — nguồn chuẩn cho mọi mã `bs*` `is*` `cf*` `no*` là bộ 556 mã | chốt |
| `bsa80` | Vốn góp | từ điển | bỏ | BCTC đầy đủ | trùng bộ báo cáo tài chính đầy đủ — nguồn chuẩn cho mọi mã `bs*` `is*` `cf*` `no*` là bộ 556 mã | chốt |
| `bsb98` | Tiền gửi tại các TCTD khác và cho vay các TCTD khác | từ điển | bỏ | BCTC đầy đủ | trùng bộ báo cáo tài chính đầy đủ — nguồn chuẩn cho mọi mã `bs*` `is*` `cf*` `no*` là bộ 556 mã | chốt |
| `bsb113` | Tiền gửi của khách hàng | từ điển | bỏ | BCTC đầy đủ | trùng bộ báo cáo tài chính đầy đủ — nguồn chuẩn cho mọi mã `bs*` `is*` `cf*` `no*` là bộ 556 mã | chốt |
| `nob44` | — | — | bỏ | BCTC đầy đủ | trùng bộ báo cáo tài chính đầy đủ — nguồn chuẩn cho mọi mã `bs*` `is*` `cf*` `no*` là bộ 556 mã | chốt |
| `cfa18` | Lưu chuyển tiền thuần từ hoạt động kinh doanh | từ điển | bỏ | BCTC đầy đủ | trùng bộ báo cáo tài chính đầy đủ — nguồn chuẩn cho mọi mã `bs*` `is*` `cf*` `no*` là bộ 556 mã | chốt |

✅ Hai dòng `freeFloatRate` và `foreignerPercentage` **đã hết "chờ chốt"** — số đo 2026-08-15 xác nhận
Screener có và giữ cả hai (§4.1), nên bỏ ở đây là bỏ đúng. Cài được ngay, không phải chờ gì nữa.

### 5.3 Cần kiểm API — 2 trường chưa phân loại

**Định danh** — 1 trường

| Mã | Tên | Nguồn tên | Lấy/Bỏ | Nguồn chuẩn | Lý do | Trạng thái |
|---|---|---|---|---|---|---|
| `organCode` | Mã doanh nghiệp | tài liệu endpoint | chưa rõ | — | khoá định danh, không phải chỉ tiêu — không nằm trong 16 trường độc quyền được liệt kê; khoá nối hiện lấy từ bảng `organization`. **Đo 2026-08-15**: có mặt trong `summary` của Snapshot và trong CẢ NĂM khối của `getScreenerItems`, nên không thiếu nguồn — nhưng đây là quyết định lúc cài ETL (lưu lại khoá hay nối sang bảng `organization`), không phải câu hỏi số đo trả lời được | cần kiểm API |

**Chưa giải mã** — 1 trường

| Mã | Tên | Nguồn tên | Lấy/Bỏ | Nguồn chuẩn | Lý do | Trạng thái |
|---|---|---|---|---|---|---|
| `rtd53` | — | — | chưa rõ | — | mã mang trạng thái chưa giải mã; cũng có mặt trong khối `financial` của Screener nên nếu quyết định lưu thì nguồn chuẩn là Screener. **Đo 2026-08-15**: hai bên trả cùng một số ở FPT và VNM (5426,73780245 · 4702,49259309) nên xác nhận là cùng chỉ tiêu; riêng BID thì Snapshot trả `0.0` còn Screener trả `null`. Vẫn chưa có tên nên chưa xếp được lấy hay bỏ | cần kiểm API |

## 6 · Hai nhóm quyết định theo họ mã, không theo từng trường

**BCTC đầy đủ — giữ nguyên vẹn 556 mã.** Mọi mã tiền tố `bs*` `is*` `cf*` `no*` đều **lấy**, nguồn chuẩn là
bộ báo cáo tài chính đầy đủ. Không trải từng dòng ở đây vì quyết định là *theo họ mã*, không có trường hợp
ngoại lệ nào phải cân nhắc riêng; danh sách máy đọc đủ 556 mã kèm tên và đơn vị đã có sẵn ở
[field-dictionary.json](../10-sources/market/field-dictionary.json). Hệ quả trực tiếp: mọi mã `bs*` `is*`
`cf*` `no*` xuất hiện ở Screener hay Snapshot đều **bỏ** — đã ghi ở §4.2 và §5.2.

**MoneyFlow — giữ FiinTrade, BVSC không có.** Ba endpoint: `getForeign` (chuỗi khối ngoại intraday — BVSC
chỉ có theo từng mã, muốn tổng thị trường phải cộng 2.534 mã), `getProprietaryV2` (tự doanh — BVSC không
có), `getContribution` (đóng góp chỉ số — BVSC không có). Đã kiểm chứng chéo: `getContribution` trả
VN-INDEX 1.729,08 và −36,55, khớp chính xác bảng giá BVSC cùng thời điểm.

## 7 · Đối soát số đếm

Số bên trái là con số của quyết định chọn nguồn ngày 2026-08-14; số bên phải là số dòng tài liệu này thực sự
liệt kê được từ tài liệu nguồn. **Lệch không bị ép cho khớp** — lệch ở đâu ghi ở đó.

### 7.1 Screener — nhóm bỏ

| Nhóm lý do | Đã chốt | Liệt kê được | Lệch |
|---|---:|---:|---|
| Trùng BVSC (giá, KL, sổ lệnh, khối ngoại, thoả thuận) | 31 | 4 | thiếu 27 |
| Chỉ báo kỹ thuật — tính từ giá BVSC | 20 | 17 | thiếu 3 |
| Nhóm chấm điểm riêng của FiinTrade | 20 | 7 | thiếu 13 |
| Biến động giá 1d–52w, YTD | 11 | 7 | thiếu 4 |
| OHLC hai phiên gần nhất | 8 | 8 | khớp |
| Thành phần chấm điểm VGM | 6 | 6 | khớp |
| Trùng BCTC đầy đủ | 5 | 3 | thiếu 2 |
| ATO/ATC | 4 | 0 | thiếu 4 |
| Khối lượng bình quân 5/10/20 phiên, 3 tháng | 4 | 4 | khớp |
| Sức mạnh tương đối | 2 | 2 | khớp |
| Trùng MoneyFlow | 2 | 2 | khớp |
| Giá trị GD bình quân 5/10/20 phiên, 3 tháng — *chốt bằng số đo 2026-08-15* | — | 4 | mới đo 2026-08-15 |
| **Tổng bỏ** | **113** | **64** | **thiếu 49** |

### 7.2 Screener — nhóm giữ

| Nhóm | Đã chốt | Liệt kê được | Lệch |
|---|---:|---:|---|
| 55 mã tỷ số tài chính | 55 | 41 | thiếu 14 |
| `rtd19` Beta | 1 | 1 | khớp |
| `corpOwnership` + `organizationOwnership` | 2 | 2 | khớp |
| Khối TTM/Y trọn cụm | 13 | 13 | khớp |
| Phần còn lại của 80 trường — không nguồn nào nêu đích danh | 9 | 0 | thiếu 9 |
| `freeFloatRate` + `foreignerPercentage` — *chốt bằng số đo 2026-08-15* | — | 2 | mới đo 2026-08-15 |
| **Tổng giữ** | **80** | **59** | **thiếu 21** |

### 7.3 Screener — tổng

| Hạng mục | Số |
|---|---:|
| Tổng trường quan sát được trên VN30 | 193 |
| Liệt kê được trong tài liệu này | 127 |
| — trong đó `chốt` | 123 |
| — trong đó `cần kiểm API` | 4 |
| **Chưa liệt kê được** (không tài liệu nguồn nào nêu mã) | **66** |

Phép cộng khép kín: thiếu 21 trường ở nhóm giữ + thiếu 49 trường ở nhóm bỏ =
70 trường chưa phân loại, bằng đúng 66 trường chưa liệt kê được + 4 trường
`cần kiểm API`. Không có trường nào bị đếm hai lần.

### 7.4 Snapshot

| Nhóm | Đã chốt | Liệt kê được | Lệch |
|---|---:|---:|---|
| Giữ — 16 trường độc quyền | 16 | 16 | khớp |
| Giữ thêm — `outstandingShare` + `freeFloat`, *chốt bằng số đo 2026-08-15* | — | 2 | mới đo 2026-08-15 |
| Bỏ — trùng Screener | 18 | 13 | thiếu 5 |
| Bỏ — trùng BCTC đầy đủ | 15 | 15 | khớp |
| Bỏ — trùng BVSC | 5 | 4 | thiếu 1 |
| Ngoài nhóm — `cần kiểm API`, chưa xếp được vào nhóm nào | — | 2 | ngoài nhóm |
| **Tổng** | **54** | **52** | **thiếu 2** |

Phép cộng khép kín: thiếu 5 trường ở nhóm trùng Screener + thiếu 1 ở nhóm trùng BVSC
= 6 trường chưa phân loại theo các nhóm của quyết định 2026-08-14; trừ 2 trường đã
chốt **lấy** bằng số đo 2026-08-15 *(`outstandingShare`, `freeFloat` — trước đây nằm trong chính khoảng
trống này)* còn 4, bằng đúng 2 dòng `cần kiểm API` + 2 trường chưa liệt kê
được.

**Khớp tuyệt đối ở hai nhóm quan trọng nhất:** 16/16 trường giữ và 15/15 trường trùng BCTC — đúng từng mã.
Đây là bằng chứng mạnh rằng phân rã 54 trường khi chốt nguồn dựa trên đúng hai khối `summary` và
`quarterly` mà tài liệu nguồn mô tả.

### 7.5 Ba chỗ lệch, nguyên nhân đã truy được

1. **Screener thiếu 66 mã.** Không tài liệu nguồn nào liệt kê đủ 193 trường của response. Chỉ có:
   83 tiêu chí của `GetScreenerParameters`, các mã được nêu đích danh khi chốt nguồn, và vài mã trong mô tả
   5 khối response (`priceInfo` 43 · `stockScreenerItem` 129 · `performance` 12 · `financial` 21 ·
   `technical` 18). Phần lớn 129 trường của `stockScreenerItem` không có mã nào được ghi ra.
2. **Nhóm ATO/ATC (4 trường) vẫn không liệt kê được dòng nào** — quyết định nêu nhóm nhưng không nêu mã.
   Số đo 2026-08-15 tìm được **hai** khoá ATO thật trong khối `priceInfo`: `atoPrice` và `atoVolume` (BID
   38.700 · 26.700), **không có khoá ATC nào** trong 193 khoá. Nghĩa là nhóm "ATO/ATC 4 trường" của quyết
   định 2026-08-14 không có đủ 4 mã tương ứng trong response. Chưa thêm dòng vào bảng vì chưa biết quyết
   định định đếm 4 trường nào; ghi lại đây để lần sau khỏi đo lại.
3. **Snapshot thiếu 2 trường trên 54.** Tài liệu endpoint mô tả `summary` 28 trường và một ví dụ
   khối `quarterly` **của bản ngân hàng**; bản phi ngân hàng có bộ chỉ tiêu khác. Số 54 là số đo, không phải
   danh sách được viết ra ở đâu. ✅ Đo 2026-08-15 xác nhận đúng như vậy: BID (`GetSnapshot`, ngân hàng) ra
   **54** khoá, còn FPT và VNM (`GetSnapshotNoneBank`) ra **56** — `summary` 28 giống nhau, khác nhau ở khối
   `quarterly`/`yearly` (27 của ngân hàng vs 28 của phi ngân hàng).

### 7.6 Giả định đã dùng — **đã kiểm bằng số đo 2026-08-15**

83 tiêu chí của `GetScreenerParameters` được coi là **đều có mặt trong response `getScreenerItems`**. Tài
liệu nguồn không khẳng định điều đó. Đã đối chiếu thật hai danh sách ngày 2026-08-15: **83/83 tiêu chí đều
có mặt** trong 193 khoá response, sau khi hạ chữ cái đầu. Giả định đúng, tổng đối soát §7.3 không phải đổi.

### 7.7 Hai điểm về tài liệu nguồn — **đã xử lý bằng số đo 2026-08-15**

- BVSC `datafeed/instruments`: quyết định chọn nguồn ghi **62 trường**, tài liệu endpoint ghi **50 trường**.
  ✅ **Đếm thật ngày 2026-08-15 trên BID/FPT/VNM: 62/62/62.** Số 62 đúng. Con số 50 là lỗi đếm của tài liệu
  endpoint — chính ví dụ response ngay dưới tiêu đề đó liệt kê đủ 62 khoá, không thiếu khoá nào so với số
  đo. Tài liệu endpoint đã sửa tiêu đề.
- `rtd39` và `rtd54` được tài liệu endpoint nêu là trường của khối `financial` của Screener, nhưng **không
  có trong từ điển 729 mã**. Đây **không** phải mâu thuẫn với tuyên bố phủ 100% của từ điển: các tuyên bố
  100% đều có phạm vi rõ ràng và **không phạm vi nào bao Screener** — 100% đo trên `GetBalanceSheet`,
  `GetIncomeStatement`, `GetCashFlow`, tức họ mã báo cáo tài chính. Với họ tỷ số thì từ điển tự ghi ngược
  lại: 173 mã nhưng chỉ **83 mã** truy được qua `GetScreenerParameters`, phần còn lại lấy từ bundle. Hai mã
  này rơi đúng vào vùng 90 mã không có nguồn API xác nhận. ✅ **Đã đo khối `financial` ngày 2026-08-15: cả
  hai có thật và có giá trị số** (`rtd39` BID 3,42582495 · FPT 15,93348656; `rtd54` FPT 12,5858301, BID
  `null`). Vế *có thật không* đã xong. Vế *là chỉ tiêu gì* thì số đo không trả lời được, nên hai mã vẫn nằm
  ở §8 — nhưng nay là chờ **tên**, không còn là chờ **bằng chứng tồn tại**.

Số đo 2026-08-15 còn dựng được đủ 21 khoá của khối `financial`, trước đây tài liệu chỉ nêu một phần:
`organCode` `rtd7` `rtd11` `rtd14` `rtd19` `rtd21` `rtd25` `rtd39` `rtd51` `rtd53` `rtd54` `rtq12` `rtq81`
`rtq27` `rtq83` `isa3` `isa5` `isa20` `isa22` `cfa18` `fryq30`.

## 8 · Danh sách cần kiểm API — 6 trường

Danh sách này **đã rút từ 16 xuống 6 sau đợt đo 2026-08-15**. Mười dòng được chốt bằng số đo thật;
6 dòng còn lại thì số đo đã dùng hết công dụng — chúng chờ một cái **tên chỉ tiêu** hoặc một
**quyết định lúc cài ETL**, không phải chờ một lời gọi API nào nữa.

| Mã | Nguồn | Vì sao chưa chốt được | Phép kiểm sẽ kết luận |
|---|---|---|---|
| `rtd53` | Screener | có trong từ điển 729 mã nhưng mang trạng thái CHƯA GIẢI MÃ — không nguồn nào có tên, chưa biết là chỉ tiêu gì nên chưa xếp được vào nhóm nào. **Đo 2026-08-15**: cả hai CÓ THẬT trong khối `financial` và có giá trị (FPT `rtd53`=5426,73780245 `rtq81`=−0,03335415 · VNM 4702,49259309 và 0,22632399 · BID cả hai `null`) — nhưng số đo chỉ chứng minh trường tồn tại, KHÔNG cho ra tên, nên vẫn chưa xếp được | chưa có phép kiểm nào kết luận được — 5 cách đã thử đều không ra tên, và số đo 2026-08-15 chỉ thêm được dải giá trị chứ không thêm tên; chỉ giải được khi FiinGroup trả lời hoặc bundle mới có tên |
| `rtq81` | Screener | có trong từ điển 729 mã nhưng mang trạng thái CHƯA GIẢI MÃ — không nguồn nào có tên, chưa biết là chỉ tiêu gì nên chưa xếp được vào nhóm nào. **Đo 2026-08-15**: cả hai CÓ THẬT trong khối `financial` và có giá trị (FPT `rtd53`=5426,73780245 `rtq81`=−0,03335415 · VNM 4702,49259309 và 0,22632399 · BID cả hai `null`) — nhưng số đo chỉ chứng minh trường tồn tại, KHÔNG cho ra tên, nên vẫn chưa xếp được | chưa có phép kiểm nào kết luận được — 5 cách đã thử đều không ra tên, và số đo 2026-08-15 chỉ thêm được dải giá trị chứ không thêm tên; chỉ giải được khi FiinGroup trả lời hoặc bundle mới có tên |
| `rtd39` | Screener | có mặt trong khối `financial` của response nhưng KHÔNG có trong từ điển 729 mã — chưa biết là chỉ tiêu gì. **Đo 2026-08-15**: đã dump khoá khối `financial` — cả hai CÓ THẬT và có giá trị (`rtd39` BID 3,42582495 · FPT 15,93348656 · VNM 15,38168732; `rtd54` FPT 12,5858301 · VNM 13,09943584 · BID `null`). Vế *có thật không* đã xong; vế *là chỉ tiêu gì* thì số đo không trả lời được nên vẫn giữ | **số đo đã dùng hết công dụng** — dump khối `financial` ngày 2026-08-15 xác nhận trường có thật, nên việc còn lại là bổ sung vào từ điển 729 mã một cái TÊN. Không lời gọi nào cho ra tên; chỉ giải được khi FiinGroup trả lời hoặc bundle JS mới có |
| `rtd54` | Screener | có mặt trong khối `financial` của response nhưng KHÔNG có trong từ điển 729 mã — chưa biết là chỉ tiêu gì. **Đo 2026-08-15**: đã dump khoá khối `financial` — cả hai CÓ THẬT và có giá trị (`rtd39` BID 3,42582495 · FPT 15,93348656 · VNM 15,38168732; `rtd54` FPT 12,5858301 · VNM 13,09943584 · BID `null`). Vế *có thật không* đã xong; vế *là chỉ tiêu gì* thì số đo không trả lời được nên vẫn giữ | **số đo đã dùng hết công dụng** — dump khối `financial` ngày 2026-08-15 xác nhận trường có thật, nên việc còn lại là bổ sung vào từ điển 729 mã một cái TÊN. Không lời gọi nào cho ra tên; chỉ giải được khi FiinGroup trả lời hoặc bundle JS mới có |
| `organCode` | Snapshot | khoá định danh, không phải chỉ tiêu — không nằm trong 16 trường độc quyền được liệt kê; khoá nối hiện lấy từ bảng `organization`. **Đo 2026-08-15**: có mặt trong `summary` của Snapshot và trong CẢ NĂM khối của `getScreenerItems`, nên không thiếu nguồn — nhưng đây là quyết định lúc cài ETL (lưu lại khoá hay nối sang bảng `organization`), không phải câu hỏi số đo trả lời được | quyết định lúc cài ETL: khoá nối lấy ở bảng `organization` hay lưu lại ở bảng Snapshot |
| `rtd53` | Snapshot | mã mang trạng thái chưa giải mã; cũng có mặt trong khối `financial` của Screener nên nếu quyết định lưu thì nguồn chuẩn là Screener. **Đo 2026-08-15**: hai bên trả cùng một số ở FPT và VNM (5426,73780245 · 4702,49259309) nên xác nhận là cùng chỉ tiêu; riêng BID thì Snapshot trả `0.0` còn Screener trả `null`. Vẫn chưa có tên nên chưa xếp được lấy hay bỏ | chưa có phép kiểm nào kết luận được — 5 cách đã thử đều không ra tên, và số đo 2026-08-15 chỉ thêm được dải giá trị chứ không thêm tên; chỉ giải được khi FiinGroup trả lời hoặc bundle mới có tên |

Hai phép kiểm dự kiến gỡ khoảng trống §7.5 **đã chạy ngày 2026-08-15**, kết quả:

1. **`getScreenerItems` một tiêu chí duy nhất, dump đủ khoá của 5 khối** *(`ClosePrice`, `comGroupCode` =
   `ALL` rồi `VN30`, `pageSize` 30)*. Ra đúng **193 khoá phân biệt / 223 lượt xuất hiện**, giống nhau ở cả
   hai `comGroupCode`. Chốt được giả định §7.6 (83/83 tiêu chí đều có trong response), giải được cách chuẩn
   hoá hoa/thường, và cho thấy nhóm ATO chỉ có 2 khoá (`atoPrice`, `atoVolume`) chứ không phải 4 (§7.5).
   Vẫn còn **66 mã chưa liệt kê được** — phần lớn nằm trong 129 khoá của `stockScreenerItem` mà
   không tài liệu nguồn nào ghi mã ra; số đo cho biết chúng TÊN gì nhưng không cho biết chúng LÀ gì, nên
   chưa xếp lấy/bỏ được.
2. **`GetSnapshot` (BID) và `GetSnapshotNoneBank` (FPT, VNM), dump khoá cả ba khối.** Bản ngân hàng ra đúng
   **54** khoá (`summary` 28 + `quarterly`/`yearly` 27); bản phi ngân hàng ra **56** (`summary` 28 +
   `quarterly`/`yearly` 28) — tức hai bản thật sự khác bộ chỉ tiêu, đúng như §7.5 điểm 3 dự đoán. Con số 54
   dùng làm mẫu số trong tài liệu này là của **bản ngân hàng**; với phi ngân hàng mẫu số là 56.

## 9 · Nhật ký thay đổi

| Ngày | Thay đổi |
|---|---|
| 2026-08-14 | Bản đầu — trải quyết định chọn nguồn ngày 2026-08-14 ra từng mã trường. 213 dòng: 57+34+16 lấy · 92 bỏ · 14 chưa rõ. 16 dòng mang trạng thái `cần kiểm API` (gồm 2 dòng đã xếp *bỏ* nhưng bỏ có điều kiện) |
| 2026-08-15 | **Đo thật, chốt 10/16 dòng `cần kiểm API`.** Gọi `GetScreenerParameters` (83 tiêu chí), `GetScreenerItems` 1 tiêu chí trên `ALL` và `VN30` (193 khoá), BVSC `/quotes?symbols=ALL` (2.534 bản ghi) và `/datafeed/instruments` (62 khoá), `GetSnapshot`/`GetSnapshotNoneBank` (54 / 56 khoá). Kết quả: `foreignerPercentage` + `freeFloatRate` → **lấy** ở Screener nên Snapshot bỏ hết điều kiện · `averageValue*` 4 mã → **bỏ** · `outstandingShare` + `freeFloat` → **lấy** ở Snapshot *(FPT lệch `ListedShare` 10.819.301 CP)* · `rtd39`/`rtd54` xác nhận có thật. Sửa **mã trường về đúng hoa/thường thật** — `getScreenerItems` chỉ hạ chữ cái đầu, viết thường toàn bộ sẽ trượt 31/83 khoá. Giải ba chỗ vênh: 223 = tổng 5 khối vs 193 khoá phân biệt · BVSC 62 đúng, 50 sai · `foreignerRoom` của Screener = `foreignRemain` của BVSC chứ không phải `foreignRoom`. Còn 6 dòng `cần kiểm API`: 213 dòng · 111 lấy · 96 bỏ · 6 chưa rõ |
