# Chọn trường cho ETL thị trường — bảng tường minh theo từng mã

**Ngày:** 2026-08-14 · **Trạng thái:** ✅ đã chốt · **Trải từ quyết định chọn nguồn ngày 2026-08-14**

Tài liệu này trả lời đúng một câu hỏi của người viết ETL: **trường này lấy hay bỏ, nguồn chuẩn là ai, vì sao.**
Lý do ghi thẳng tại từng dòng — không phải tra chỗ khác, không phải diễn giải lại quyết định của ai.

Số đo nền: Screener `getScreenerItems` trả **193 trường** quan sát được trên VN30 ngày 2026-08-14 *(tài liệu
endpoint ghi 223 — chênh 30 trường chỉ xuất hiện ở một số loại hình doanh nghiệp)*, `GetSnapshot` **54**,
BVSC `datafeed/instruments` **62** *(tài liệu endpoint mô tả 50)*.

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
| **Mã** | Tên trường đúng như endpoint trả về. Screener trả chữ thường (`rtq12`) còn `GetScreenerParameters` trả hoa chữ đầu (`Rtq12`) — cùng một chỉ tiêu |
| **Tên** | Tên tiếng Việt. `—` nghĩa là **không nguồn nào có tên cho mã này** — hoặc mã mang trạng thái chưa giải mã trong từ điển, hoặc không có trong từ điển |
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

57 lấy · 60 bỏ · 10 cần kiểm API — trên 127 trường liệt kê được.

### 4.1 Lấy — 57 trường

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
| `rtd20avg` | Tỉ Suất Cổ Tức T.Bình 3 Năm | từ điển | lấy | Screener | tỷ số tài chính — nằm trong cụm 55 tỷ số được nêu đích danh khi chốt nguồn; không nguồn nào khác có · nhóm cổ tức | chốt |

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
| `revgrowth` | Tăng trưởng doanh thu quý gần nhất (YoY) | từ điển | lấy | Screener | tỷ số tài chính/định giá — không rơi vào bất kỳ nhóm bỏ nào trong 113 trường bị loại, nên thuộc 80 trường giữ | chốt |
| `prfgrowth` | Tăng trưởng lợi nhuận thuần quý gần nhất (YoY) | từ điển | lấy | Screener | tỷ số tài chính/định giá — không rơi vào bất kỳ nhóm bỏ nào trong 113 trường bị loại, nên thuộc 80 trường giữ | chốt |

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

**Sở hữu** — 2 trường

| Mã | Tên | Nguồn tên | Lấy/Bỏ | Nguồn chuẩn | Lý do | Trạng thái |
|---|---|---|---|---|---|---|
| `corpownership` | Tỉ lệ tổ chức sở hữu | từ điển | lấy | Screener | hai chỉ tiêu sở hữu tổ chức KHÁC NHAU, không phải trùng tên — FPT 0,0567 vs 0,1555, ACB có cái này thiếu cái kia; `GetOwnership` không có tỷ lệ tổng hợp mà chỉ có danh sách cổ đông lớn | chốt |
| `organizationownership` | Sở hữu tổ chức (chỉ tiêu thứ hai, khác `corpownership`) | tự đặt | lấy | Screener | hai chỉ tiêu sở hữu tổ chức KHÁC NHAU, không phải trùng tên — FPT 0,0567 vs 0,1555, ACB có cái này thiếu cái kia; `GetOwnership` không có tỷ lệ tổng hợp mà chỉ có danh sách cổ đông lớn | chốt |

**TTM/Y** — 13 trường

| Mã | Tên | Nguồn tên | Lấy/Bỏ | Nguồn chuẩn | Lý do | Trạng thái |
|---|---|---|---|---|---|---|
| `revttm` | Doanh thu (tỉ đồng) (TTM) | từ điển | lấy | Screener | khối TTM/Y lấy trọn cụm — `isa20ttm` chính là mẫu số P/E của FiinTrade (vốn hoá ÷ `isa20ttm` khớp 9/10 mã VN30) và KHÔNG bằng tổng 4 quý `isa20` (lệch tới 9,4%); tự tính lại sẽ ra P/E khác cột P/E ngay bên cạnh | chốt |
| `revy` | Doanh thu (tỉ đồng) (năm trước) | từ điển | lấy | Screener | khối TTM/Y lấy trọn cụm — `isa20ttm` chính là mẫu số P/E của FiinTrade (vốn hoá ÷ `isa20ttm` khớp 9/10 mã VN30) và KHÔNG bằng tổng 4 quý `isa20` (lệch tới 9,4%); tự tính lại sẽ ra P/E khác cột P/E ngay bên cạnh | chốt |
| `isa1ttm` | Doanh số (TTM) — suy từ `isa1` | suy theo luật kỳ | lấy | Screener | khối TTM/Y lấy trọn cụm — `isa20ttm` chính là mẫu số P/E của FiinTrade (vốn hoá ÷ `isa20ttm` khớp 9/10 mã VN30) và KHÔNG bằng tổng 4 quý `isa20` (lệch tới 9,4%); tự tính lại sẽ ra P/E khác cột P/E ngay bên cạnh | chốt |
| `isa1y` | Doanh số (năm trước) — suy từ `isa1` | suy theo luật kỳ | lấy | Screener | khối TTM/Y lấy trọn cụm — `isa20ttm` chính là mẫu số P/E của FiinTrade (vốn hoá ÷ `isa20ttm` khớp 9/10 mã VN30) và KHÔNG bằng tổng 4 quý `isa20` (lệch tới 9,4%); tự tính lại sẽ ra P/E khác cột P/E ngay bên cạnh | chốt |
| `isa20ttm` | LN ròng (tỉ đồng) (TTM) | từ điển | lấy | Screener | khối TTM/Y lấy trọn cụm — `isa20ttm` chính là mẫu số P/E của FiinTrade (vốn hoá ÷ `isa20ttm` khớp 9/10 mã VN30) và KHÔNG bằng tổng 4 quý `isa20` (lệch tới 9,4%); tự tính lại sẽ ra P/E khác cột P/E ngay bên cạnh | chốt |
| `isa20y` | LN ròng (tỉ đồng) (năm trước) | từ điển | lấy | Screener | khối TTM/Y lấy trọn cụm — `isa20ttm` chính là mẫu số P/E của FiinTrade (vốn hoá ÷ `isa20ttm` khớp 9/10 mã VN30) và KHÔNG bằng tổng 4 quý `isa20` (lệch tới 9,4%); tự tính lại sẽ ra P/E khác cột P/E ngay bên cạnh | chốt |
| `isa3ttm` | Doanh số thuần (TTM) — suy từ `isa3` | suy theo luật kỳ | lấy | Screener | khối TTM/Y lấy trọn cụm — `isa20ttm` chính là mẫu số P/E của FiinTrade (vốn hoá ÷ `isa20ttm` khớp 9/10 mã VN30) và KHÔNG bằng tổng 4 quý `isa20` (lệch tới 9,4%); tự tính lại sẽ ra P/E khác cột P/E ngay bên cạnh | chốt |
| `isb25ttm` | Thu nhập lãi và các khoản thu nhập tương tự (TTM) — suy từ `isb25` | suy theo luật kỳ | lấy | Screener | khối TTM/Y lấy trọn cụm — `isa20ttm` chính là mẫu số P/E của FiinTrade (vốn hoá ÷ `isa20ttm` khớp 9/10 mã VN30) và KHÔNG bằng tổng 4 quý `isa20` (lệch tới 9,4%); tự tính lại sẽ ra P/E khác cột P/E ngay bên cạnh | chốt |
| `isb25y` | Thu nhập lãi và các khoản thu nhập tương tự (năm trước) — suy từ `isb25` | suy theo luật kỳ | lấy | Screener | khối TTM/Y lấy trọn cụm — `isa20ttm` chính là mẫu số P/E của FiinTrade (vốn hoá ÷ `isa20ttm` khớp 9/10 mã VN30) và KHÔNG bằng tổng 4 quý `isa20` (lệch tới 9,4%); tự tính lại sẽ ra P/E khác cột P/E ngay bên cạnh | chốt |
| `isi103ttm` | Doanh thu phí bảo hiểm (TTM) — suy từ `isi103` | suy theo luật kỳ | lấy | Screener | khối TTM/Y lấy trọn cụm — `isa20ttm` chính là mẫu số P/E của FiinTrade (vốn hoá ÷ `isa20ttm` khớp 9/10 mã VN30) và KHÔNG bằng tổng 4 quý `isa20` (lệch tới 9,4%); tự tính lại sẽ ra P/E khác cột P/E ngay bên cạnh | chốt |
| `isi103y` | Doanh thu phí bảo hiểm (năm trước) — suy từ `isi103` | suy theo luật kỳ | lấy | Screener | khối TTM/Y lấy trọn cụm — `isa20ttm` chính là mẫu số P/E của FiinTrade (vốn hoá ÷ `isa20ttm` khớp 9/10 mã VN30) và KHÔNG bằng tổng 4 quý `isa20` (lệch tới 9,4%); tự tính lại sẽ ra P/E khác cột P/E ngay bên cạnh | chốt |
| `rev` | Doanh thu (tỉ đồng) (quý gần nhất) | từ điển | lấy | Screener | khối TTM/Y lấy trọn cụm — `isa20ttm` chính là mẫu số P/E của FiinTrade (vốn hoá ÷ `isa20ttm` khớp 9/10 mã VN30) và KHÔNG bằng tổng 4 quý `isa20` (lệch tới 9,4%); tự tính lại sẽ ra P/E khác cột P/E ngay bên cạnh | chốt |
| `prf` | Lợi nhuận ròng (tỉ đồng) (quý gần nhất) | từ điển | lấy | Screener | khối TTM/Y lấy trọn cụm — `isa20ttm` chính là mẫu số P/E của FiinTrade (vốn hoá ÷ `isa20ttm` khớp 9/10 mã VN30) và KHÔNG bằng tổng 4 quý `isa20` (lệch tới 9,4%); tự tính lại sẽ ra P/E khác cột P/E ngay bên cạnh | chốt |

### 4.2 Bỏ — 60 trường

**Trùng BVSC** — 4 trường

| Mã | Tên | Nguồn tên | Lấy/Bỏ | Nguồn chuẩn | Lý do | Trạng thái |
|---|---|---|---|---|---|---|
| `closeprice` | Giá | từ điển | bỏ | BVSC | trùng BVSC — `closePrice`/`reference`; giá lấy nguồn realtime khớp sàn | chốt |
| `totalmatchvolume` | Khối lượng GD | từ điển | bỏ | BVSC | trùng BVSC — `totalTrading` | chốt |
| `totalmatchvalue` | Giá trị GD | từ điển | bỏ | BVSC | trùng BVSC — `totalTradingValue` | chốt |
| `foreignerroom` | Room nước ngoài | từ điển | bỏ | BVSC | trùng BVSC — `foreignRoom` | chốt |

**Biến động giá** — 7 trường

| Mã | Tên | Nguồn tên | Lấy/Bỏ | Nguồn chuẩn | Lý do | Trạng thái |
|---|---|---|---|---|---|---|
| `percentpricechange1day` | Biến động giá 1 ngày | từ điển | bỏ | BVSC (tự tính) | biến động giá — tính lại được từ chuỗi giá BVSC | chốt |
| `percentpricechange1week` | Biến động giá 1 tuần | từ điển | bỏ | BVSC (tự tính) | biến động giá — tính lại được từ chuỗi giá BVSC | chốt |
| `percentpricechange1month` | Biến động giá 1 tháng | từ điển | bỏ | BVSC (tự tính) | biến động giá — tính lại được từ chuỗi giá BVSC | chốt |
| `percentpricechange3month` | Biến động giá 3 tháng | từ điển | bỏ | BVSC (tự tính) | biến động giá — tính lại được từ chuỗi giá BVSC | chốt |
| `percentpricechange6month` | Biến động giá 6 tháng | từ điển | bỏ | BVSC (tự tính) | biến động giá — tính lại được từ chuỗi giá BVSC | chốt |
| `percentpricechange52week` | Biến động giá 52 tuần | từ điển | bỏ | BVSC (tự tính) | biến động giá — tính lại được từ chuỗi giá BVSC | chốt |
| `percentpricechangeytd` | Biến động giá từ đầu năm | từ điển | bỏ | BVSC (tự tính) | biến động giá — tính lại được từ chuỗi giá BVSC | chốt |

**KL bình quân** — 4 trường

| Mã | Tên | Nguồn tên | Lấy/Bỏ | Nguồn chuẩn | Lý do | Trạng thái |
|---|---|---|---|---|---|---|
| `averagevolume1week` | Kl T.bình 5 phiên | từ điển | bỏ | BVSC (tự tính) | khối lượng bình quân 5/10/20 phiên và 3 tháng — tính lại được từ chuỗi khối lượng BVSC | chốt |
| `averagevolume2week` | Kl T.bình 10 phiên | từ điển | bỏ | BVSC (tự tính) | khối lượng bình quân 5/10/20 phiên và 3 tháng — tính lại được từ chuỗi khối lượng BVSC | chốt |
| `averagevolume1month` | Kl T.bình 20 phiên | từ điển | bỏ | BVSC (tự tính) | khối lượng bình quân 5/10/20 phiên và 3 tháng — tính lại được từ chuỗi khối lượng BVSC | chốt |
| `averagevolume3month` | Kl T.bình 3 tháng | từ điển | bỏ | BVSC (tự tính) | khối lượng bình quân 5/10/20 phiên và 3 tháng — tính lại được từ chuỗi khối lượng BVSC | chốt |

**Chấm điểm** — 13 trường

| Mã | Tên | Nguồn tên | Lấy/Bỏ | Nguồn chuẩn | Lý do | Trạng thái |
|---|---|---|---|---|---|---|
| `icbrank` | FiinTrade Rank | từ điển | bỏ | — (không lưu) | nhóm chấm điểm riêng của FiinTrade — quyết định của chủ dự án: không dùng điểm do bên thứ ba chấm | chốt |
| `value` | Value (FiinTrade Score) | từ điển | bỏ | — (không lưu) | nhóm chấm điểm riêng của FiinTrade — quyết định của chủ dự án: không dùng điểm do bên thứ ba chấm | chốt |
| `growth` | Growth (FiinTrade Score) | từ điển | bỏ | — (không lưu) | nhóm chấm điểm riêng của FiinTrade — quyết định của chủ dự án: không dùng điểm do bên thứ ba chấm | chốt |
| `momentum` | Momentum (FiinTrade Score) | từ điển | bỏ | — (không lưu) | nhóm chấm điểm riêng của FiinTrade — quyết định của chủ dự án: không dùng điểm do bên thứ ba chấm | chốt |
| `vgm` | VGM (FiinTrade Score) | từ điển | bỏ | — (không lưu) | nhóm chấm điểm riêng của FiinTrade — quyết định của chủ dự án: không dùng điểm do bên thứ ba chấm | chốt |
| `fscore` | F-Score (TTM) | từ điển | bỏ | — (không lưu) | nhóm chấm điểm riêng của FiinTrade — quyết định của chủ dự án: không dùng điểm do bên thứ ba chấm | chốt |
| `canslim` | Canslim (TTM) | từ điển | bỏ | — (không lưu) | nhóm chấm điểm riêng của FiinTrade — quyết định của chủ dự án: không dùng điểm do bên thứ ba chấm | chốt |
| `capitalstructure` | Thành phần chấm điểm VGM | tự đặt | bỏ | — (không lưu) | thành phần chấm điểm VGM — bỏ cùng nhóm chấm điểm, không dùng điểm bên thứ ba chấm | chốt |
| `financialstrength` | Thành phần chấm điểm VGM | tự đặt | bỏ | — (không lưu) | thành phần chấm điểm VGM — bỏ cùng nhóm chấm điểm, không dùng điểm bên thứ ba chấm | chốt |
| `financialplan` | Thành phần chấm điểm VGM | tự đặt | bỏ | — (không lưu) | thành phần chấm điểm VGM — bỏ cùng nhóm chấm điểm, không dùng điểm bên thứ ba chấm | chốt |
| `cfo` | Thành phần chấm điểm VGM | tự đặt | bỏ | — (không lưu) | thành phần chấm điểm VGM — bỏ cùng nhóm chấm điểm, không dùng điểm bên thứ ba chấm | chốt |
| `debt` | Thành phần chấm điểm VGM | tự đặt | bỏ | — (không lưu) | thành phần chấm điểm VGM — bỏ cùng nhóm chấm điểm, không dùng điểm bên thứ ba chấm | chốt |
| `equityinssurance` | Thành phần chấm điểm VGM | tự đặt | bỏ | — (không lưu) | thành phần chấm điểm VGM — bỏ cùng nhóm chấm điểm, không dùng điểm bên thứ ba chấm | chốt |

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
| `oversma50` | Giá so với trung bình động 50 phiên | tự đặt | bỏ | BVSC (tự tính) | chỉ báo kỹ thuật — tự tính từ giá BVSC; lấy của FiinTrade thì chỉ báo và giá đến từ hai chuỗi khác nhau | chốt |

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
| `totalbuytradevolume` | Khối lượng theo chiều mua | tự đặt | bỏ | MoneyFlow | trùng MoneyFlow — chuỗi mua/bán chủ động lấy trọn bộ ở MoneyFlow | chốt |
| `totalselltradevolume` | Khối lượng theo chiều bán | tự đặt | bỏ | MoneyFlow | trùng MoneyFlow — chuỗi mua/bán chủ động lấy trọn bộ ở MoneyFlow | chốt |

### 4.3 Cần kiểm API — 10 trường

**Sở hữu** — 2 trường

| Mã | Tên | Nguồn tên | Lấy/Bỏ | Nguồn chuẩn | Lý do | Trạng thái |
|---|---|---|---|---|---|---|
| `foreignerpercentage` | Sở hữu nước ngoài | từ điển | chưa rõ | — | BVSC chỉ có room theo số cổ phiếu (`foreignRemain`/`foreignRoom`), không có trường tỷ lệ; không nhóm bỏ nào nêu đích danh trường này ⚠️ Snapshot cũng có trường này và ở đó đã bỏ với nguồn chuẩn *dự kiến* là Screener — hai bên phải chốt CÙNG LÚC: Screener mà cũng bỏ thì không nguồn nào lưu chỉ tiêu này | cần kiểm API |
| `freefloatrate` | % Free Float | từ điển | chưa rõ | — | không nhóm bỏ nào nêu, cũng không nằm trong danh sách giữ được liệt kê đích danh ⚠️ Snapshot cũng có trường này và ở đó đã bỏ với nguồn chuẩn *dự kiến* là Screener — hai bên phải chốt CÙNG LÚC: Screener mà cũng bỏ thì không nguồn nào lưu chỉ tiêu này | cần kiểm API |

**GTGD bình quân** — 4 trường

| Mã | Tên | Nguồn tên | Lấy/Bỏ | Nguồn chuẩn | Lý do | Trạng thái |
|---|---|---|---|---|---|---|
| `averagevalue1week` | Giá trị GD T.bình 5D | từ điển | chưa rõ | — | nhóm bỏ chỉ nêu KHỐI LƯỢNG bình quân, không nêu GIÁ TRỊ bình quân; chưa đủ căn cứ xếp lấy hay bỏ | cần kiểm API |
| `averagevalue2week` | Giá trị GD T.bình 10D | từ điển | chưa rõ | — | nhóm bỏ chỉ nêu KHỐI LƯỢNG bình quân, không nêu GIÁ TRỊ bình quân; chưa đủ căn cứ xếp lấy hay bỏ | cần kiểm API |
| `averagevalue1month` | Giá trị GD T.bình 20D | từ điển | chưa rõ | — | nhóm bỏ chỉ nêu KHỐI LƯỢNG bình quân, không nêu GIÁ TRỊ bình quân; chưa đủ căn cứ xếp lấy hay bỏ | cần kiểm API |
| `averagevalue3month` | Giá trị GD T.bình 3M | từ điển | chưa rõ | — | nhóm bỏ chỉ nêu KHỐI LƯỢNG bình quân, không nêu GIÁ TRỊ bình quân; chưa đủ căn cứ xếp lấy hay bỏ | cần kiểm API |

**Chưa giải mã** — 4 trường

| Mã | Tên | Nguồn tên | Lấy/Bỏ | Nguồn chuẩn | Lý do | Trạng thái |
|---|---|---|---|---|---|---|
| `rtd53` | — | — | chưa rõ | — | có trong từ điển 729 mã nhưng mang trạng thái CHƯA GIẢI MÃ — không nguồn nào có tên, chưa biết là chỉ tiêu gì nên chưa xếp được vào nhóm nào | cần kiểm API |
| `rtq81` | — | — | chưa rõ | — | có trong từ điển 729 mã nhưng mang trạng thái CHƯA GIẢI MÃ — không nguồn nào có tên, chưa biết là chỉ tiêu gì nên chưa xếp được vào nhóm nào | cần kiểm API |
| `rtd39` | — | — | chưa rõ | — | có mặt trong khối `financial` của response nhưng KHÔNG có trong từ điển 729 mã — chưa biết là chỉ tiêu gì | cần kiểm API |
| `rtd54` | — | — | chưa rõ | — | có mặt trong khối `financial` của response nhưng KHÔNG có trong từ điển 729 mã — chưa biết là chỉ tiêu gì | cần kiểm API |

🔴 **Hai mã phải chốt cùng lúc với Snapshot: `freefloatrate` và `foreignerpercentage`.** Ở §5.2, Snapshot bỏ
hai trường cùng nghĩa (`freeFloatRate`, `foreignerPercentage`) với nguồn chuẩn ghi là *Screener (chờ chốt)*.
Nếu đọc rời từng bảng rồi cài luôn, kết quả là **không nguồn nào lưu hai chỉ tiêu này** — sở hữu nước ngoài
theo tỷ lệ và free float biến mất khỏi kho. Thứ tự đúng: chốt phía Screener trước (một lời gọi thật là đủ),
rồi mới cài phần Snapshot theo kết quả đó. Nếu Screener hoá ra cũng bỏ, phải mở lại quyết định — không có
nguồn thứ ba cho hai chỉ tiêu này.

## 5 · Snapshot `GetSnapshot` / `GetSnapshotNoneBank`

16 lấy · 32 bỏ *(trong đó 2 dòng bỏ CÓ ĐIỀU KIỆN, mang trạng thái `cần kiểm API` — xem cuối §5.2)* · 4 chưa rõ — trên 52 trường liệt kê được
(28 trường khối `summary` + các mã được nêu đích danh trong khối `quarterly`/`yearly`).

🔴 Chọn sai endpoint **không báo lỗi** mà làm gần một nửa số trường thành `null`: `comTypeCode = NH` dùng
`GetSnapshot`, còn `CT` `CK` `BH` dùng `GetSnapshotNoneBank`.

### 5.1 Lấy — 16 trường

**Hồ sơ doanh nghiệp** — 4 trường

| Mã | Tên | Nguồn tên | Lấy/Bỏ | Nguồn chuẩn | Lý do | Trạng thái |
|---|---|---|---|---|---|---|
| `ceo` | Tên tổng giám đốc | tài liệu endpoint | lấy | Snapshot | hồ sơ doanh nghiệp — chỉ Snapshot có; `competitors` là danh sách mã cùng ngành, dùng ngay cho so sánh ngang ngành; `comTypeCode` quyết định gọi `GetSnapshot` hay `GetSnapshotNoneBank` | chốt |
| `competitors` | Danh sách mã cùng ngành để so sánh | tài liệu endpoint | lấy | Snapshot | hồ sơ doanh nghiệp — chỉ Snapshot có; `competitors` là danh sách mã cùng ngành, dùng ngay cho so sánh ngang ngành; `comTypeCode` quyết định gọi `GetSnapshot` hay `GetSnapshotNoneBank` | chốt |
| `majorHoldings` | Các khoản đầu tư lớn | tài liệu endpoint | lấy | Snapshot | hồ sơ doanh nghiệp — chỉ Snapshot có; `competitors` là danh sách mã cùng ngành, dùng ngay cho so sánh ngang ngành; `comTypeCode` quyết định gọi `GetSnapshot` hay `GetSnapshotNoneBank` | chốt |
| `comTypeCode` | Loại hình doanh nghiệp | tài liệu endpoint | lấy | Snapshot | hồ sơ doanh nghiệp — chỉ Snapshot có; `competitors` là danh sách mã cùng ngành, dùng ngay cho so sánh ngang ngành; `comTypeCode` quyết định gọi `GetSnapshot` hay `GetSnapshotNoneBank` | chốt |

**Sở hữu chi tiết** — 5 trường

| Mã | Tên | Nguồn tên | Lấy/Bỏ | Nguồn chuẩn | Lý do | Trạng thái |
|---|---|---|---|---|---|---|
| `statePercentage` | Tỷ lệ sở hữu nhà nước | tài liệu endpoint | lấy | Snapshot | sở hữu chi tiết — nằm trong 16 trường độc quyền của Snapshot, không nguồn nào khác có | chốt |
| `stateVolumn` | Khối lượng nhà nước nắm | tài liệu endpoint | lấy | Snapshot | sở hữu chi tiết — nằm trong 16 trường độc quyền của Snapshot, không nguồn nào khác có | chốt |
| `foreignerVolumn` | Khối lượng nước ngoài nắm | tài liệu endpoint | lấy | Snapshot | sở hữu chi tiết — nằm trong 16 trường độc quyền của Snapshot, không nguồn nào khác có | chốt |
| `totalForeignRoom` | Tổng room | tài liệu endpoint | lấy | Snapshot | sở hữu chi tiết — nằm trong 16 trường độc quyền của Snapshot, không nguồn nào khác có | chốt |
| `maximumForeignPercentage` | Trần sở hữu nước ngoài | tài liệu endpoint | lấy | Snapshot | sở hữu chi tiết — nằm trong 16 trường độc quyền của Snapshot, không nguồn nào khác có | chốt |

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
| `freeFloatRate` | Tỷ lệ free float | tài liệu endpoint | bỏ | Screener *(chờ chốt)* | trùng Screener — `freefloatrate` / `foreignerpercentage` trong 83 tiêu chí, nên KHÔNG lấy ở Snapshot. ⚠️ Nhưng phía Screener hai mã này đang `cần kiểm API` chứ chưa chốt giữ — cho tới khi chốt, đây là nguồn chuẩn DỰ KIẾN, không phải nguồn chuẩn đã chốt. Chốt Screener trước, rồi mới cài phần này | cần kiểm API |
| `foreignerPercentage` | Tỷ lệ sở hữu nước ngoài | tài liệu endpoint | bỏ | Screener *(chờ chốt)* | trùng Screener — `freefloatrate` / `foreignerpercentage` trong 83 tiêu chí, nên KHÔNG lấy ở Snapshot. ⚠️ Nhưng phía Screener hai mã này đang `cần kiểm API` chứ chưa chốt giữ — cho tới khi chốt, đây là nguồn chuẩn DỰ KIẾN, không phải nguồn chuẩn đã chốt. Chốt Screener trước, rồi mới cài phần này | cần kiểm API |
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
| `averageMatchVolume1Month` | KLGD bình quân 1 tháng | tài liệu endpoint | bỏ | BVSC (tự tính) | KLGD bình quân 1 tháng — tính lại từ chuỗi khối lượng BVSC; Screener cũng có trường tương đương `averagevolume1month` và cũng bỏ | chốt |

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

🔴 Hai dòng `freeFloatRate` và `foreignerPercentage` mang nguồn chuẩn **dự kiến**, chưa chốt — đọc ô cảnh
báo cuối §4.3 trước khi cài. Bỏ ở đây mà phía Screener cũng bỏ thì hai chỉ tiêu này không còn nguồn nào.

### 5.3 Cần kiểm API — 4 trường

**Định danh** — 1 trường

| Mã | Tên | Nguồn tên | Lấy/Bỏ | Nguồn chuẩn | Lý do | Trạng thái |
|---|---|---|---|---|---|---|
| `organCode` | Mã doanh nghiệp | tài liệu endpoint | chưa rõ | — | khoá định danh, không phải chỉ tiêu — không nằm trong 16 trường độc quyền được liệt kê; khoá nối hiện lấy từ bảng `organization` | cần kiểm API |

**Sở hữu chi tiết** — 2 trường

| Mã | Tên | Nguồn tên | Lấy/Bỏ | Nguồn chuẩn | Lý do | Trạng thái |
|---|---|---|---|---|---|---|
| `outstandingShare` | Số CP đang lưu hành | tài liệu endpoint | chưa rõ | — | không nằm trong 16 trường độc quyền; BVSC có `ListedShare`/`TotalListingQtty` nhưng tài liệu nguồn không nói hai bên bằng nhau | cần kiểm API |
| `freeFloat` | Khối lượng tự do chuyển nhượng | tài liệu endpoint | chưa rõ | — | không nằm trong 16 trường độc quyền; Screener chỉ có tỷ lệ `freefloatrate`, không có khối lượng | cần kiểm API |

**Chưa giải mã** — 1 trường

| Mã | Tên | Nguồn tên | Lấy/Bỏ | Nguồn chuẩn | Lý do | Trạng thái |
|---|---|---|---|---|---|---|
| `rtd53` | — | — | chưa rõ | — | mã mang trạng thái chưa giải mã; cũng có mặt trong khối `financial` của Screener nên nếu quyết định lưu thì nguồn chuẩn là Screener | cần kiểm API |

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
| **Tổng bỏ** | **113** | **60** | **thiếu 53** |

### 7.2 Screener — nhóm giữ

| Nhóm | Đã chốt | Liệt kê được | Lệch |
|---|---:|---:|---|
| 55 mã tỷ số tài chính | 55 | 41 | thiếu 14 |
| `rtd19` Beta | 1 | 1 | khớp |
| `corpownership` + `organizationownership` | 2 | 2 | khớp |
| Khối TTM/Y trọn cụm | 13 | 13 | khớp |
| Phần còn lại của 80 trường — không nguồn nào nêu đích danh | 9 | 0 | thiếu 9 |
| **Tổng giữ** | **80** | **57** | **thiếu 23** |

### 7.3 Screener — tổng

| Hạng mục | Số |
|---|---:|
| Tổng trường quan sát được trên VN30 | 193 |
| Liệt kê được trong tài liệu này | 127 |
| — trong đó `chốt` | 117 |
| — trong đó `cần kiểm API` | 10 |
| **Chưa liệt kê được** (không tài liệu nguồn nào nêu mã) | **66** |

Phép cộng khép kín: thiếu 23 trường ở nhóm giữ + thiếu 53 trường ở nhóm bỏ =
76 trường chưa phân loại, bằng đúng 66 trường chưa liệt kê được + 10 trường
`cần kiểm API`. Không có trường nào bị đếm hai lần.

### 7.4 Snapshot

| Nhóm | Đã chốt | Liệt kê được | Lệch |
|---|---:|---:|---|
| Giữ — 16 trường độc quyền | 16 | 16 | khớp |
| Bỏ — trùng Screener | 18 | 13 | thiếu 5 |
| Bỏ — trùng BCTC đầy đủ | 15 | 15 | khớp |
| Bỏ — trùng BVSC | 5 | 4 | thiếu 1 |
| **Tổng** | **54** | **52** | **thiếu 2** |

Phép cộng khép kín: thiếu 5 trường ở nhóm trùng Screener + thiếu 1 ở nhóm trùng BVSC
= 6 trường chưa phân loại, bằng đúng 4 dòng `cần kiểm API` + 2 trường chưa
liệt kê được.

**Khớp tuyệt đối ở hai nhóm quan trọng nhất:** 16/16 trường giữ và 15/15 trường trùng BCTC — đúng từng mã.
Đây là bằng chứng mạnh rằng phân rã 54 trường khi chốt nguồn dựa trên đúng hai khối `summary` và
`quarterly` mà tài liệu nguồn mô tả.

### 7.5 Ba chỗ lệch, nguyên nhân đã truy được

1. **Screener thiếu 66 mã.** Không tài liệu nguồn nào liệt kê đủ 193 trường của response. Chỉ có:
   83 tiêu chí của `GetScreenerParameters`, các mã được nêu đích danh khi chốt nguồn, và vài mã trong mô tả
   5 khối response (`priceInfo` 43 · `stockScreenerItem` 129 · `performance` 12 · `financial` 21 ·
   `technical` 18). Phần lớn 129 trường của `stockScreenerItem` không có mã nào được ghi ra.
2. **Nhóm ATO/ATC (4 trường) không liệt kê được dòng nào** — quyết định nêu nhóm nhưng không nêu mã, và
   không tài liệu endpoint nào ghi tên trường ATO/ATC của Screener.
3. **Snapshot thiếu 2 trường trên 54.** Tài liệu endpoint mô tả `summary` 28 trường và một ví dụ khối
   `quarterly` **của bản ngân hàng**; bản phi ngân hàng có bộ chỉ tiêu khác. Số 54 là số đo, không phải danh
   sách được viết ra ở đâu.

### 7.6 Một giả định đã dùng, ghi rõ để ai cũng kiểm được

83 tiêu chí của `GetScreenerParameters` được coi là **đều có mặt trong response `getScreenerItems`**. Tài
liệu nguồn không khẳng định điều đó — nó chỉ nói endpoint tham số là "bảng giải mã mã trường". Nếu một số
tiêu chí chỉ dùng để lọc mà không trả về, tổng đối soát §7.3 đổi theo. Một lời gọi thật là đủ để chốt.

### 7.7 Hai điểm về tài liệu nguồn, đã truy nhưng chưa xử lý được

- BVSC `datafeed/instruments`: quyết định chọn nguồn ghi **62 trường**, tài liệu endpoint ghi **50 trường**.
  Không ảnh hưởng bảng §3 (34 trường lấy đều có trong cả hai bản mô tả), nhưng số 62 chưa truy được nguồn.
- `rtd39` và `rtd54` được tài liệu endpoint nêu là trường của khối `financial` của Screener, nhưng **không
  có trong từ điển 729 mã**. Đây **không** phải mâu thuẫn với tuyên bố phủ 100% của từ điển: các tuyên bố
  100% đều có phạm vi rõ ràng và **không phạm vi nào bao Screener** — 100% đo trên `GetBalanceSheet`,
  `GetIncomeStatement`, `GetCashFlow`, tức họ mã báo cáo tài chính. Với họ tỷ số thì từ điển tự ghi ngược
  lại: 173 mã nhưng chỉ **83 mã** truy được qua `GetScreenerParameters`, phần còn lại lấy từ bundle. Hai mã
  này rơi đúng vào vùng 90 mã không có nguồn API xác nhận. Việc cần làm không phải là sửa chỗ nào sai, mà là
  **đo khối `financial` một lần** để biết chúng có thật và là chỉ tiêu gì — đã đưa vào danh sách cần kiểm API.

## 8 · Danh sách cần kiểm API — 16 trường

Mỗi dòng ghi phép kiểm nào sẽ kết luận được. Tất cả đều là **một lời gọi thật**, không cần đo lại toàn bộ.
Gồm 14 dòng chưa phân loại được lấy hay bỏ, cộng 2 dòng Snapshot đã xếp *bỏ* nhưng **bỏ có điều
kiện** (`freeFloatRate`, `foreignerPercentage` — bỏ đúng chỉ khi Screener giữ).

| Mã | Nguồn | Vì sao chưa chốt được | Phép kiểm sẽ kết luận |
|---|---|---|---|
| `foreignerpercentage` | Screener | BVSC chỉ có room theo số cổ phiếu (`foreignRemain`/`foreignRoom`), không có trường tỷ lệ; không nhóm bỏ nào nêu đích danh trường này ⚠️ Snapshot cũng có trường này và ở đó đã bỏ với nguồn chuẩn *dự kiến* là Screener — hai bên phải chốt CÙNG LÚC: Screener mà cũng bỏ thì không nguồn nào lưu chỉ tiêu này | dump đủ 193 khoá `getScreenerItems` để xác nhận trường có thật, rồi chốt: thuộc 9 trường giữ chưa nêu tên hay thuộc một nhóm bỏ |
| `averagevalue1week` | Screener | nhóm bỏ chỉ nêu KHỐI LƯỢNG bình quân, không nêu GIÁ TRỊ bình quân; chưa đủ căn cứ xếp lấy hay bỏ | dump đủ 193 khoá `getScreenerItems` để xác nhận trường có thật, rồi chốt: thuộc 9 trường giữ chưa nêu tên hay thuộc một nhóm bỏ |
| `averagevalue2week` | Screener | nhóm bỏ chỉ nêu KHỐI LƯỢNG bình quân, không nêu GIÁ TRỊ bình quân; chưa đủ căn cứ xếp lấy hay bỏ | dump đủ 193 khoá `getScreenerItems` để xác nhận trường có thật, rồi chốt: thuộc 9 trường giữ chưa nêu tên hay thuộc một nhóm bỏ |
| `averagevalue1month` | Screener | nhóm bỏ chỉ nêu KHỐI LƯỢNG bình quân, không nêu GIÁ TRỊ bình quân; chưa đủ căn cứ xếp lấy hay bỏ | dump đủ 193 khoá `getScreenerItems` để xác nhận trường có thật, rồi chốt: thuộc 9 trường giữ chưa nêu tên hay thuộc một nhóm bỏ |
| `averagevalue3month` | Screener | nhóm bỏ chỉ nêu KHỐI LƯỢNG bình quân, không nêu GIÁ TRỊ bình quân; chưa đủ căn cứ xếp lấy hay bỏ | dump đủ 193 khoá `getScreenerItems` để xác nhận trường có thật, rồi chốt: thuộc 9 trường giữ chưa nêu tên hay thuộc một nhóm bỏ |
| `freefloatrate` | Screener | không nhóm bỏ nào nêu, cũng không nằm trong danh sách giữ được liệt kê đích danh ⚠️ Snapshot cũng có trường này và ở đó đã bỏ với nguồn chuẩn *dự kiến* là Screener — hai bên phải chốt CÙNG LÚC: Screener mà cũng bỏ thì không nguồn nào lưu chỉ tiêu này | dump đủ 193 khoá `getScreenerItems` để xác nhận trường có thật, rồi chốt: thuộc 9 trường giữ chưa nêu tên hay thuộc một nhóm bỏ |
| `rtd53` | Screener | có trong từ điển 729 mã nhưng mang trạng thái CHƯA GIẢI MÃ — không nguồn nào có tên, chưa biết là chỉ tiêu gì nên chưa xếp được vào nhóm nào | chưa có phép kiểm nào kết luận được — 5 cách đã thử đều không ra tên; chỉ giải được khi FiinGroup trả lời hoặc bundle mới có tên |
| `rtq81` | Screener | có trong từ điển 729 mã nhưng mang trạng thái CHƯA GIẢI MÃ — không nguồn nào có tên, chưa biết là chỉ tiêu gì nên chưa xếp được vào nhóm nào | chưa có phép kiểm nào kết luận được — 5 cách đã thử đều không ra tên; chỉ giải được khi FiinGroup trả lời hoặc bundle mới có tên |
| `rtd39` | Screener | có mặt trong khối `financial` của response nhưng KHÔNG có trong từ điển 729 mã — chưa biết là chỉ tiêu gì | dump khoá khối `financial` của một lời gọi thật: mã có thật thì bổ sung vào từ điển, không có thì sửa mô tả endpoint |
| `rtd54` | Screener | có mặt trong khối `financial` của response nhưng KHÔNG có trong từ điển 729 mã — chưa biết là chỉ tiêu gì | dump khoá khối `financial` của một lời gọi thật: mã có thật thì bổ sung vào từ điển, không có thì sửa mô tả endpoint |
| `freeFloatRate` | Snapshot | trùng Screener — `freefloatrate` / `foreignerpercentage` trong 83 tiêu chí, nên KHÔNG lấy ở Snapshot. ⚠️ Nhưng phía Screener hai mã này đang `cần kiểm API` chứ chưa chốt giữ — cho tới khi chốt, đây là nguồn chuẩn DỰ KIẾN, không phải nguồn chuẩn đã chốt. Chốt Screener trước, rồi mới cài phần này | chốt phía Screener trước (dump 193 khoá) — Screener giữ thì bỏ hẳn ở đây, Screener bỏ thì phải mở lại quyết định vì không còn nguồn nào |
| `foreignerPercentage` | Snapshot | trùng Screener — `freefloatrate` / `foreignerpercentage` trong 83 tiêu chí, nên KHÔNG lấy ở Snapshot. ⚠️ Nhưng phía Screener hai mã này đang `cần kiểm API` chứ chưa chốt giữ — cho tới khi chốt, đây là nguồn chuẩn DỰ KIẾN, không phải nguồn chuẩn đã chốt. Chốt Screener trước, rồi mới cài phần này | chốt phía Screener trước (dump 193 khoá) — Screener giữ thì bỏ hẳn ở đây, Screener bỏ thì phải mở lại quyết định vì không còn nguồn nào |
| `organCode` | Snapshot | khoá định danh, không phải chỉ tiêu — không nằm trong 16 trường độc quyền được liệt kê; khoá nối hiện lấy từ bảng `organization` | quyết định lúc cài ETL: khoá nối lấy ở bảng `organization` hay lưu lại ở bảng Snapshot |
| `outstandingShare` | Snapshot | không nằm trong 16 trường độc quyền; BVSC có `ListedShare`/`TotalListingQtty` nhưng tài liệu nguồn không nói hai bên bằng nhau | dump đủ 54 khoá `GetSnapshot` và 193 khoá Screener, đối chiếu giá trị với `ListedShare` của BVSC — bằng nhau thì bỏ, khác nhau thì lấy |
| `freeFloat` | Snapshot | không nằm trong 16 trường độc quyền; Screener chỉ có tỷ lệ `freefloatrate`, không có khối lượng | dump đủ 54 khoá `GetSnapshot` và 193 khoá Screener, đối chiếu giá trị với `ListedShare` của BVSC — bằng nhau thì bỏ, khác nhau thì lấy |
| `rtd53` | Snapshot | mã mang trạng thái chưa giải mã; cũng có mặt trong khối `financial` của Screener nên nếu quyết định lưu thì nguồn chuẩn là Screener | chưa có phép kiểm nào kết luận được — 5 cách đã thử đều không ra tên; chỉ giải được khi FiinGroup trả lời hoặc bundle mới có tên |

Ngoài ra, hai phép kiểm gỡ được phần lớn khoảng trống §7.5:

1. **Gọi `getScreenerItems` một tiêu chí duy nhất, dump đủ khoá của 5 khối response.** Cho ra danh sách 193
   mã thật → phân loại được 66 mã còn thiếu, chốt luôn giả định §7.6 và tìm ra 4 trường ATO/ATC.
2. **Gọi `GetSnapshot` và `GetSnapshotNoneBank` cho một mã mỗi loại hình, dump khoá của cả ba khối.** Cho ra
   đủ 54 trường và bộ chỉ tiêu khác nhau giữa hai bản.

## 9 · Nhật ký thay đổi

| Ngày | Thay đổi |
|---|---|
| 2026-08-14 | Bản đầu — trải quyết định chọn nguồn ngày 2026-08-14 ra từng mã trường. 213 dòng: 107 lấy · 92 bỏ · 14 chưa rõ. 16 dòng mang trạng thái `cần kiểm API` (gồm 2 dòng đã xếp *bỏ* nhưng bỏ có điều kiện) |
