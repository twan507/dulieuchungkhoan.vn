# 0002 · Chọn nguồn dữ liệu khi nhiều nguồn cùng có

**Ngày:** 2026-08-14 · **Trạng thái:** đã chốt

## Bối cảnh

Ba nguồn dữ liệu thị trường chồng lấn nhau khá nhiều. `getScreenerItems` trả **223 trường mỗi mã** *(đo thật trên VN30 ngày 2026-08-14 được **193** — chênh 30 trường chỉ xuất hiện ở một số loại hình doanh nghiệp)*, `GetSnapshot` trả **54 trường**, BVSC `datafeed/instruments` trả **62 trường** — và một phần lớn trong đó nói cùng một chuyện.

Lưu hết thì kho có hai ba chỗ cùng ghi giá đóng cửa của một mã, và khi chúng lệch nhau thì không ai biết tin cái nào. Bỏ bừa thì mất những chỉ tiêu chỉ một nguồn có.

## Nguyên tắc

**Mỗi chỉ tiêu có đúng một nguồn chuẩn.** Chọn nguồn theo hai tiêu chí, xét theo thứ tự:

1. **Nguồn nào realtime và khớp với sàn** — ưu tiên tuyệt đối cho giá và mọi thứ dẫn xuất từ giá
2. **Nguồn nào cho trọn bộ ngữ cảnh của chỉ tiêu đó** — trùng lặp không phải lý do đủ để bỏ, nếu lấy cả bộ từ một nguồn thì toàn vẹn và dễ dùng hơn

> **Hệ quả quan trọng nhất:** khi một nhóm chỉ tiêu có **quan hệ dẫn xuất** với nhau — biến TTM sinh ra tỷ số, giá sinh ra chỉ báo — thì lấy **trọn bộ từ một nguồn**. Trộn nguồn giữa chừng trong một dây chuyền tính toán tạo ra dữ liệu **tự mâu thuẫn trong cùng một bảng**, và loại sai lệch đó không có cách nào phát hiện tự động.

## Quyết định

### 1 · Giá, chỉ báo kỹ thuật, khối ngoại, thoả thuận → **BVSC**

BVSC là nguồn realtime và khớp trực tiếp với sàn. Đã kiểm bằng lời gọi thật, `datafeed/instruments` có đủ:

| Nhóm | Trường BVSC |
|---|---|
| Giá | `closePrice` `ceiling` `floor` `reference` `open` `high` `low` `averagePrice` `PRIOR_PRICE` |
| Khối lượng, giá trị | `totalTrading` `totalTradingValue` `closeVol` |
| Sổ lệnh 3 bậc | `bidPrice1-3` `bidVol1-3` `offerPrice1-3` `offerVol1-3` `TOTAL_BID_QTTY` `TOTAL_OFFER_QTTY` |
| Khối ngoại | `foreignBuy` `foreignSell` `foreignRemain` `foreignRoom` |
| Thoả thuận | `PT_MATCH_QTTY` `PT_MATCH_PRICE` `PT_TOTAL_TRADED_QTTY` `PT_TOTAL_TRADED_VALUE` |

**Chỉ báo kỹ thuật tự tính từ giá BVSC**, không lấy của FiinTrade — nếu không, chỉ báo và giá sẽ đến từ hai chuỗi khác nhau.

⚠️ **Đánh đổi đã chấp nhận:** Beta và các tỷ số định giá của Screener được tính trên giá của FiinTrade, nên sẽ lệch nhẹ so với giá BVSC ta lưu. Không tránh được. Biết trước để không hoảng khi thấy P/E lệch ở chữ số thập phân thứ hai.

### 2 · Screener → giữ **80/193** trường quan sát được

**Bỏ 113 trường:**

| Lý do | Số |
|---|---:|
| Trùng BVSC (giá, KL, sổ lệnh, khối ngoại, thoả thuận) | 31 |
| Chỉ báo kỹ thuật — tính từ giá BVSC | 20 |
| Nhóm chấm điểm riêng của FiinTrade | 20 |
| Biến động giá 1d–52w, YTD — tính từ chuỗi giá | 11 |
| OHLC hai phiên gần nhất (`c1 c2 h1 h2 l1 l2 o1 o2`) | 8 |
| Trùng BCTC đầy đủ (`isa20` `isa22` `cfa18`…) | 5 |
| Thành phần chấm điểm VGM (`capitalstructure` `financialstrength` `financialplan` `cfo` `debt` `equityinssurance`) | 6 |
| ATO/ATC | 4 |
| Khối lượng bình quân 5/10/20 phiên, 3 tháng | 4 |
| Sức mạnh tương đối `rs52w` `rs6m` | 2 |
| Trùng MoneyFlow (`totalbuytradevolume` `totalselltradevolume`) | 2 |

**Bỏ hẳn nhóm chấm điểm** là quyết định của chủ dự án: không dùng điểm do bên thứ ba chấm.

**ATO/ATC bỏ** vì chỉ có nghĩa trong lúc khớp lệnh định kỳ. ETL Screener chạy sau 15:00 nên số đó đã là chuyện đã rồi. Chỗ nó có nghĩa là realtime — BVSC topic `i:` đã có. Nếu Ingester không bắt được thì sửa ở Ingester, không vá bằng một bản chết từ Screener.

**Giữ 80 trường:**

- **55 mã tỷ số tài chính** — phần đáng giá nhất, không nguồn nào khác có: `rtd26` P/S · `rtd27` Giá/TS hữu hình · `rtd28` Giá/Dòng tiền · `rtd40` Giá/FCF · nhóm cổ tức `rtd36` `rtd43` `rtd51` `rtd20avg` · nhóm đòn bẩy `rtq4` `rtq6` `rtq7` `rtq77` · nhóm tăng trưởng `rtq78` `rtq79` `rtq83` `rtd52` `ryq160` `ryq166` `ryq176` · biên theo quý `rqq23` `rqq25` `rqq27` `rqq29`
- **`rtd19` Beta** — giữ theo quyết định của chủ dự án; tự tính được nhưng phải chọn chuẩn thị trường và số phiên, sẽ lệch số FiinTrade
- **`corpownership` + `organizationownership`** — hai chỉ tiêu **khác nhau**, không phải trùng tên. FPT: 0,0567 vs 0,1555; ACB có cái này thiếu cái kia. `GetOwnership` không có tỷ lệ tổng hợp, chỉ có danh sách cổ đông lớn
- **Khối TTM/Y trọn cụm** — `revttm` `revy` `isa1ttm` `isa1y` `isa20ttm` `isa20y` `isa3ttm` `isb25ttm` `isb25y` `isi103ttm` `isi103y` `rev` `prf`

### 3 · Snapshot → cắt từ **54 xuống 16** trường

Đo được: 18 trường trùng Screener, 15 trùng BCTC đầy đủ, 5 trùng BVSC. **Chỉ 16 trường là độc quyền**, và đó là phần giữ lại:

| Nhóm | Trường |
|---|---|
| Hồ sơ doanh nghiệp | `ceo` `competitors` `majorholdings` `comtypecode` |
| Sở hữu chi tiết | `statepercentage` `statevolumn` `foreignervolumn` `totalforeignroom` `maximumforeignpercentage` |
| Chỉ tiêu riêng | `rtq10` (Nợ/VCSH) · `rtq44` (NIM) · `rtq137` · `rqq41` · `valuepershare` |
| Metadata | `year` `quarter` |

`competitors` đáng chú ý — danh sách mã cùng ngành để so sánh, dùng được ngay cho tính năng so sánh ngang ngành.

### 4 · MoneyFlow → **giữ FiinTrade**, BVSC không có

Đã kiểm bằng lời gọi thật, dữ liệu sống ngày 14/08/2026:

| Endpoint | Dữ liệu | BVSC có? |
|---|---|---|
| `getForeign` | 227 điểm intraday, khối ngoại mua 2.090 tỷ / bán 2.964 tỷ | ⚠️ Chỉ có theo từng mã, muốn tổng thị trường phải cộng 2.534 mã |
| `getProprietaryV2` | Tự doanh mua 46,5 triệu CP / 728 tỷ | ❌ Không có |
| `getContribution` | VN-INDEX 1.729,08 · thay đổi −36,55 | ❌ Không có |

**Kiểm chứng chéo:** `getContribution` trả 1.729,08 và −36,55 — khớp chính xác với bảng giá BVSC cùng thời điểm. Hai nguồn độc lập cho cùng một số.

## Bức tranh sau khi dọn

| Nguồn | Trước | Sau | Vai trò |
|---|---:|---:|---|
| BVSC | — | ~40 | Giá, KL, sổ lệnh, khối ngoại, thoả thuận — realtime |
| Screener | 193 *(tài liệu ghi 223)* | **80** | Tỷ số tài chính, Beta, sở hữu tổ chức, TTM |
| Snapshot | 54 | **16** | Hồ sơ DN, sở hữu chi tiết |
| BCTC | 556 | 556 | Nguyên vẹn — nguồn chuẩn cho mọi mã `bs*` `is*` `cf*` `no*` |
| MoneyFlow | — | giữ | Tự doanh, đóng góp chỉ số, chuỗi khối ngoại |

Mỗi trường có đúng một chỗ.

## Bốn phát hiện kỹ thuật kèm theo

**1 · `getScreenerItems` timeout khi gửi nhiều tiêu chí.** 79 tiêu chí → `status: Failed` với lỗi Redis timeout phía server FiinTrade. 1 tiêu chí → chạy ngay. Vẫn trả đủ 223 trường mỗi mã bất kể số tiêu chí, nên **luôn gửi một tiêu chí duy nhất** với `selectedValue = valueRange` để lấy toàn bộ.

**2 · `isa20ttm` KHÔNG bằng tổng 4 quý `isa20`.** Lệch tới **9,4%** (FPT). Nguyên nhân: `isa20` trong BCTC là *lợi nhuận thuần* gồm cả lợi ích cổ đông thiểu số, còn `isa20ttm` là *lợi nhuận sau thuế của cổ đông công ty mẹ*. Đo trên HPG, VNM, FPT, MWG.

**3 · `P/E = vốn hoá ÷ isa20ttm` khớp 9/10 mã VN30.** Đây là bằng chứng `isa20ttm` chính là mẫu số FiinTrade dùng. Tự tính lợi nhuận TTM sẽ cho P/E khác cột P/E của chính họ.

**4 · `revttm` không phải mẫu số của P/S với ngân hàng.** `P/S = vốn hoá ÷ revttm` chỉ khớp 4/10, sáu ca lệch **đều là ngân hàng** — vì ngân hàng không có "doanh thu" theo nghĩa thông thường.

Phát hiện 2–4 là lý do **giữ trọn cụm TTM** thay vì tự tính phần tính được: nếu lưu P/E của FiinTrade mà lưu lợi nhuận tự tính, thì chatbot lấy vốn hoá chia lợi nhuận sẽ ra P/E khác với cột P/E ngay bên cạnh.

## Đã cân nhắc và loại

| Phương án | Vì sao loại |
|---|---|
| Bỏ hẳn Screener | Mất 55 tỷ số không nguồn nào khác có |
| Lưu cả 223 trường | Hai ba chỗ cùng ghi giá một mã; lệch nhau thì không biết tin cái nào |
| Tự tính phần TTM tính được, lấy phần còn lại | Nửa vời — tạo dữ liệu tự mâu thuẫn trong cùng bảng. Xem phát hiện 2–4 |
| Giữ ATO/ATC từ Screener làm dự phòng | Bản chết của dữ liệu chỉ có nghĩa realtime. Tạo cảm giác an toàn giả |
