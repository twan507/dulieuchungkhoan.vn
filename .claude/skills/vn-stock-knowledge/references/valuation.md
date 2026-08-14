# Định giá cổ phiếu

Định giá một cổ phiếu bằng những cách nào, mỗi cách làm từng bước ra sao, và dùng kết quả định giá thế nào. Phần lấy số liệu từ báo cáo tài chính nằm ở `financial-statements.md`.

## Mục lục

- [Nguyên tắc gốc](#nguyen-tac-goc)
- [Hai cách tiếp cận: so sánh và dòng tiền](#hai-cach-tiep-can)
- [Công thức chiết khấu và mô hình tăng trưởng đều](#cong-thuc-chiet-khau)
- [Tỷ suất chiết khấu: CAPM và WACC](#ty-suat-chiet-khau)
- [FCFF và FCFE — 4 bước mỗi loại](#fcff-va-fcfe)
- [Ví dụ 1 — một bài DCF đầy đủ](#vi-du-1-dcf)
- [Mô hình cổ tức và cách thay bằng thu nhập](#mo-hinh-co-tuc)
- [Quy trình bảy bước định giá](#quy-trinh-bay-buoc)
- [Định giá theo thu nhập còn lại](#thu-nhap-con-lai)
- [Định giá so sánh: PE, PB và năm bước](#dinh-gia-so-sanh)
- [Ví dụ 2 — định giá so sánh đủ năm bước](#vi-du-2-so-sanh)
- [PE thấp có phải tốt không](#pe-thap-co-tot-khong)
- [Định giá nhanh bằng cơ hội đầu tư thay thế](#dinh-gia-nhanh)
- [Cái gì làm định giá thay đổi](#cai-gi-lam-dinh-gia-thay-doi)
- [Mối liên hệ giữa các phương pháp](#moi-lien-he)
- [Dùng kết quả định giá thế nào](#dung-ket-qua-dinh-gia)

---

## Nguyên tắc gốc

**Giá trị của một doanh nghiệp được xây trên dòng tiền tương lai so với tỷ lệ chiết khấu.** Nôm na: giá trị = dòng tiền tương lai chia cho tỷ lệ chiết khấu. Chỉ cần nhớ hai vế — **tử số** là những gì nhà đầu tư sẽ nhận được (lợi nhuận sau thuế, khấu hao, đầu tư tài sản ròng, vay nợ ròng), tỷ lệ thuận với giá trị; **mẫu số** là giá trị thời gian của tiền, tỷ lệ nghịch.

Vì sao cùng số tiền ở hai thời điểm lại khác giá trị: **lạm phát** làm sức mua giảm, **rủi ro** vì không biết tương lai, **chi phí cơ hội** vì tiền đó dùng được việc khác. Từ đó có **giá trị thời gian của tiền**. Đây là khác biệt gốc giữa kế toán (nhìn con số gốc) và tài chính (quy đổi theo thời gian) — có trường hợp có lợi về kế toán nhưng không có lợi về tài chính. Mẫu số cực kỳ nhạy: một thay đổi rất nhỏ của tỷ lệ chiết khấu gây thay đổi lớn hơn bất kỳ thứ gì liên quan tới dòng tiền. Đó là lý do lãi suất và chính sách tiền tệ là biến số quan trọng nhất với định giá.

**Phân biệt giá trị doanh nghiệp và giá trị cổ phiếu.** Giá trị doanh nghiệp gồm cả phần trả cho chủ nợ:

> Giá trị doanh nghiệp = giá trị nợ + giá trị cổ phiếu → **Giá trị cổ phiếu = giá trị doanh nghiệp − giá trị nợ**

Nhiều người thấy tài sản lớn liền kết luận cổ phiếu đáng giá, quên rằng phần lớn tài sản đó do nợ mà có. Chiết khấu dòng tiền hoạt động rồi gọi kết quả là giá trị cổ đông là sai. Lưu ý từ ngữ: **dòng tiền trong định giá** là dòng tiền doanh nghiệp tạo ra cho cổ đông, không phải dòng tiền vào/ra thị trường (thanh khoản, cung tiền).

---

## Hai cách tiếp cận: so sánh và dòng tiền

| | **So sánh** (comparative) | **Chiết khấu dòng tiền** (valuation) |
|---|---|---|
| Trả lời | Giá trị hiện tại trông thế nào so với một chuẩn | Những gì nhận trong tương lai đáng bao nhiêu khi quy về hiện tại |
| Nhìn về | Hiện tại và quá khứ | Tương lai |
| Thuật ngữ | Giá trị so sánh, giá trị hợp lý tại thời điểm | Giá trị hợp lý, giá trị nội tại (intrinsic value) |
| Hạn dùng | Mang tính thời điểm — **không dùng quá 1 quý** | Lâu hơn, có ý nghĩa theo quý vì trong quý r và g chưa đổi nhiều |
| Phục vụ | Giao dịch ngắn hạn, chốt lời | Nắm giữ dài hạn |
| Điểm yếu | Giả định các công ty đem ra so đã được định giá đúng — chưa chắc | Tương lai bất định, r và g đều là giả định chủ quan |

So sánh có hai nhánh: so ngang với công ty tương ứng tại cùng thời điểm, và so với chính công ty đó trong quá khứ (nhánh sau trả lời: thị trường từng sẵn sàng trả bao nhiêu cho nó).

Khi nào định giá có tác dụng: **thị trường nhiều tiền, tăng nóng** — gần như vô nghĩa ngắn hạn vì giá do tâm lý đẩy, chỉ còn tác dụng khi phân vân giữa hai ba mã; **thị trường ít tiền, buộc phải cân nhắc** — phát huy tác dụng nhiều nhất; **thị trường giảm, tâm lý bắt đáy** — chọn mã mà cả định giá ngắn hạn lẫn dài hạn đều định giá thấp hơn thị giá đáng kể, đó là tiêu chí an toàn chứ không phải tín hiệu điểm vào. Nhiều phương pháp cho cùng câu trả lời thì đáng tin hơn, nhưng **đừng nắn kết quả cho gần nhau** — cái đáng quan tâm là dải dao động.

---

## Công thức chiết khấu và mô hình tăng trưởng đều

Dạng tổng quát, với CF1...CFn là dòng tiền tương lai và r là tỷ lệ chiết khấu. Không ai dự báo được dòng tiền từng năm quá vài năm, nên giả định dòng tiền tăng đều theo tỷ lệ g mỗi năm, ra **mô hình tăng trưởng đều** — và trường hợp riêng g = 0:

> **V = Σ CFt / (1+r)^t**   →   **V = CF0 × (1 + g) / (r − g)**   →   **V = CF / r** (khi g = 0)

CF0 là dòng tiền năm gốc, r là tỷ suất chiết khấu (cũng là tỷ suất lợi nhuận yêu cầu), g là tăng trưởng dài hạn. Bắt buộc **r > g**, nếu không mẫu số âm và công thức vô nghĩa. Phần toán dễ; cái khó là hiểu các biến số và đánh giá thay đổi của chúng tác động thế nào.

**Năm đặc trưng (typical year).** Thay vì dự phóng 5–10 năm, lấy một năm đặc trưng cho một chu kỳ kinh tế làm CF0. Trung bình **5 năm** vượt trọn một chu kỳ kinh tế (chu kỳ thường 4–5 năm); trung bình **3 năm** phản ánh trung hạn, có tính đến chu kỳ; **1 năm gần nhất hoặc 4 quý gần nhất** phản ánh hiện tại, ngắn hạn.

**Quy tắc chọn:** đang ở đỉnh chu kỳ tăng thì dùng trung bình dài hạn; đang ở đầu chu kỳ đi lên thì dùng dữ liệu gần nhất. Với cổ phiếu chu kỳ, tính 3 năm ra giá thấp còn tính 1 năm ra giá cao — chênh lệch đó chính là thông tin về vị trí chu kỳ. Với các khoản mục như tồn kho, năm đặc trưng nhìn **phần tăng thêm** chứ không nhìn giá trị tuyệt đối: tồn kho 100 tỷ năm này, 100 tỷ năm sau thì bản chất không tăng.

---

## Tỷ suất chiết khấu: CAPM và WACC

Tỷ lệ chiết khấu là cái nhà đầu tư yêu cầu. Gốc của nó là **chi phí cơ hội** — cái đáng ra nhận được nếu làm việc khác mà tin chắc sẽ nhận. Khi đầu tư chứng khoán, cơ hội mất đi là tiền lãi tiết kiệm.

> **r = lãi suất tiết kiệm + phần bù rủi ro**

Suy ra tỷ suất yêu cầu khi mua cổ phiếu **chắc chắn phải lớn hơn lãi suất tiết kiệm**; lãi suất tiết kiệm tăng thì r phải tăng theo. Phần bù rủi ro càng lớn thì r càng cao và định giá càng giảm. **CAPM** cụ thể hoá điều đó cho chi phí vốn chủ sở hữu:

> **r(i) = Rf + beta(i) × (Rm − Rf)**

| Biến | Lấy ở đâu | Lưu ý |
|---|---|---|
| **Rf** lợi suất phi rủi ro | Lợi suất trái phiếu chính phủ, thường kỳ hạn 10 năm vì định giá cổ phiếu là dài hạn | Phải dương. Kỳ hạn 1/5/10 năm đều được, miễn **so hai cổ phiếu thì dùng cùng kỳ hạn**. Báo cáo công ty chứng khoán thường không ghi rõ kỳ hạn nên khó so |
| **Rm** lợi nhuận kỳ vọng thị trường | Tăng trưởng dài hạn của chỉ số qua nhiều năm, khảo sát kỳ vọng, hoặc Rm hàm ý (implied market return) tính ngược từ tăng trưởng lợi nhuận so với giá hiện tại | **Phải là kỳ vọng, không phải lịch sử.** Lấy chỉ số của năm âm đưa vào là sai. Rm phải dương và lớn hơn lãi suất tiết kiệm |
| **beta** độ biến động so với thị trường | Trang tài chính bất kỳ, thường tính cho 52 tuần | >1 biến động mạnh hơn thị trường, <1 yếu hơn, có thể âm. **Phải lấy cùng một nguồn khi so sánh**; beta 120 ngày rất khác beta 52 tuần |

Vì Rf và Rm giống nhau cho mọi cổ phiếu, **toàn bộ khác biệt về r giữa các cổ phiếu do beta quyết định.** Beta cao → r cao → định giá thấp: hai doanh nghiệp cùng ngành tương đương nhau, bên bị đánh đấm thường xuyên hơn có beta cao hơn nên định giá dài hạn phải thấp hơn. Không có ngưỡng beta nào là "tốt" — luôn có đánh đổi lợi nhuận và rủi ro. Cách chỉ dựa vào beta là định lượng, không phải phân tích cơ bản.

**WACC — chi phí vốn bình quân,** dùng khi chiết khấu dòng tiền doanh nghiệp vì dòng tiền đó dành cho cả chủ nợ lẫn cổ đông:

> **WACC = wE × rE + wD × rD × (1 − t)**

**rE** là chi phí vốn chủ sở hữu, tính bằng CAPM. **rD** là chi phí nợ: lãi suất ngân hàng với khoản vay, lợi suất (yield) với trái phiếu vì giá trái phiếu thay đổi; thực hành thì lấy chi phí lãi vay chia dư nợ vay bình quân — thông thường thấp hơn rE. **(1 − t)** là lá chắn thuế vì lãi vay được trừ trước thuế. **wE, wD** là tỷ trọng theo giá thị trường: wE = vốn hoá / (vốn hoá + nợ vay). **Quy tắc không được nhầm:** dòng tiền doanh nghiệp chiết khấu bằng **WACC**; dòng tiền cổ đông chiết khấu bằng **rE**, không phải WACC.

---

## FCFF và FCFE — 4 bước mỗi loại

Đây là phần lõi. Hai dòng tiền hoàn toàn khác nhau; khác biệt nằm ở phần nợ.

| | **FCFF** — dòng tiền cho doanh nghiệp | **FCFE** — dòng tiền cho cổ đông |
|---|---|---|
| Xuất phát từ | **EBIT** (lợi nhuận trước lãi vay và thuế) | **Lợi nhuận sau thuế** |
| Vì sao | EBIT phản ánh kết quả của mô hình vận hành khi **chưa** tính chi phí nợ — vì dòng tiền này dành cho cả chủ nợ lẫn cổ đông | Lợi nhuận sau thuế là phần cổ đông được hưởng, **đã** trừ lãi vay và thuế |
| Nợ dài hạn mới | Không đưa vào | **Cộng vào** — cổ đông vay được thì có thêm tiền |
| Chiết khấu bằng | WACC | rE (CAPM) |
| Ra cái gì | Giá trị doanh nghiệp → **phải trừ nợ** mới ra giá trị cổ đông | Giá trị cổ đông luôn, không trừ nợ |
| Hợp việc gì | Mua bán doanh nghiệp (M&A), hoặc doanh nghiệp đang có vấn đề về nợ mà có thể đảo nợ | Đầu tư chứng khoán — tính trực tiếp giá trị cổ phiếu muốn mua |

Hai cách **không cho cùng kết quả**. Đầu tư cổ phiếu là đầu tư vào phần vốn chủ sở hữu nên FCFE trực tiếp và phù hợp hơn.

**FCFF — 4 bước.** (1) Tính dòng tiền: **FCFF = EBIT × (1 − t) + khấu hao − đầu tư vốn − đầu tư vốn lưu động**. (2) Tính WACC từ chi phí vốn chủ (CAPM) và chi phí nợ. (3) Chiết khấu dòng tiền tương lai về hiện tại bằng WACC. (4) **Trừ nợ** — kết quả bước 3 là giá trị doanh nghiệp, trừ giá trị các khoản nợ mới ra giá trị cổ đông, chia số cổ phần ra giá mỗi cổ phần.

**FCFE — 4 bước.** (1) Tính dòng tiền: **FCFE = lợi nhuận sau thuế + khấu hao − đầu tư vốn − đầu tư vốn lưu động mới + nợ dài hạn mới**. (2) Tính chi phí vốn chủ sở hữu bằng CAPM — chỉ lấy phần vốn chủ, không lấy trung bình cả nợ lẫn vốn chủ. (3) Chiết khấu bằng chi phí vốn chủ sở hữu. (4) Ra kết quả luôn: đã là giá trị cổ đông, **không trừ nợ nữa**, chia số cổ phần ra giá mỗi cổ phần.

**Từng biến lấy ở đâu:**

| Biến | Nguồn | Cách tính |
|---|---|---|
| Lợi nhuận sau thuế | Báo cáo kết quả kinh doanh | Lấy thẳng |
| EBIT | Báo cáo kết quả kinh doanh | Lợi nhuận trước thuế + chi phí lãi vay |
| Khấu hao | Báo cáo lưu chuyển tiền tệ | Có sẵn một dòng khấu hao |
| **Đầu tư vốn** (capex) | Cân đối kế toán + lưu chuyển tiền tệ | Đầu tư gộp = chênh lệch tài sản cố định ròng giữa 2 năm **+ khấu hao trong kỳ**. Là đầu tư vào tài sản cố định dài hạn (máy móc, nhà xưởng, dùng trên 1 năm), **không phải** đầu tư tài chính |
| **Đầu tư vốn lưu động mới** | Cân đối kế toán | Nhu cầu vốn lưu động = tài sản ngắn hạn (không gồm tiền mặt) − nợ ngắn hạn. Đầu tư mới = chênh lệch nhu cầu vốn lưu động giữa 2 năm |
| **Nợ dài hạn mới** | Cân đối kế toán | Chênh lệch nợ dài hạn giữa 2 năm |

Ba điểm dễ sai. **Vốn lưu động phải loại tiền mặt** vì tiền mặt không phải tài sản sinh lời dài hạn; sách còn dạy cách phải thu + tồn kho − phải trả, cách đó dễ bị bóp méo vì doanh nghiệp chuyển qua lại giữa các mục, lấy tài sản ngắn hạn trừ nợ ngắn hạn thật hơn. **Đầu tư vốn và khấu hao bù trừ nhau:** đầu tư lớn thì dòng tiền năm nay ít đi, nhưng mỗi năm sau thu về một phần qua khấu hao. **Nợ dài hạn mới là "trừ với trừ thành cộng":** vay thêm thì dòng tiền cổ đông tăng, trả nhiều hơn vay thì giảm — đây là điểm phân biệt quan trọng nhất giữa FCFE và FCFF.

Đừng bị chi phối bởi dấu cộng dấu trừ (mỗi sách viết một kiểu), hiểu bản chất là đủ: **lợi nhuận là dòng tiền vào; khấu hao là chi phí không phải tiền mặt nên là dòng tiền vào; tài sản tăng là dòng tiền ra; vay nợ nhiều hơn là dòng tiền vào.** **Lối tắt khi tính nhanh:** về dài hạn các khoản đầu tư có thể được tài trợ hoàn toàn bằng nợ dài hạn, tổng cộng bằng 0, nên chỉ cần cân nhắc lợi nhuận sau thuế và khấu hao — dùng lợi nhuận sau thuế để đầu tư thì hao mòn giá trị cổ đông nên doanh nghiệp ưu tiên tiền vay. Nhưng thực tế vẫn phải soi từng năm để biết doanh nghiệp có liên tục đầu tư và đầu tư bao nhiêu.

---

## Ví dụ 1 — một bài DCF đầy đủ

Doanh nghiệp giả định **Công ty X**, sản xuất, 100 triệu cổ phần lưu hành, giá thị trường 24.000 đ/cp. Đơn vị: tỷ đồng. Năm gần nhất là N, thuế suất 20%.

| Khoản mục (từ báo cáo) | Cuối N−1 | Cuối N |
|---|---|---|
| EBIT (= lợi nhuận trước thuế 500 + lãi vay 100) | | 600 |
| Chi phí lãi vay (dư nợ vay 1.000, lãi suất 10%) | | 100 |
| Lợi nhuận sau thuế = (600 − 100) × 0,8 | | 400 |
| Khấu hao | | 180 |
| Tài sản cố định ròng | 2.000 | 2.150 |
| Tài sản ngắn hạn (trừ tiền mặt) / Nợ ngắn hạn | 1.200 / 700 | 1.320 / 760 |
| Nhu cầu vốn lưu động (hiệu của hai dòng trên) | 500 | 560 |
| Nợ dài hạn | 900 | 960 |
| Vốn chủ sở hữu | | 2.000 |

Suy ra: **đầu tư vốn gộp** = (2.150 − 2.000) + 180 = **330**; **đầu tư vốn lưu động mới** = 560 − 500 = **60**; **nợ dài hạn mới** = 960 − 900 = **60**.

**Bước 1 — FCFF** = 600 × 0,8 + 180 − 330 − 60 = 480 + 180 − 330 − 60 = **270 tỷ**

**Bước 2 — WACC.** Rf = 5% (trái phiếu chính phủ 10 năm), beta = 1,2, phần bù thị trường (Rm − Rf) = 8%. Vậy rE = 5% + 1,2 × 8% = **14,6%**; rD sau thuế = 10% × 0,8 = **8,0%**. Vốn hoá = 100 triệu × 24.000 = 2.400 tỷ, nợ vay 1.000 tỷ, tổng 3.400 → wE = 70,6%, wD = 29,4%. WACC = 0,706 × 14,6% + 0,294 × 8,0% = 10,31% + 2,35% = **12,7%**

**Bước 3 — Chiết khấu,** lấy g = 6% (bằng tăng trưởng GDP giả định):
Giá trị doanh nghiệp = 270 × 1,06 / (0,127 − 0,06) = 286,2 / 0,067 = **4.272 tỷ**

**Bước 4 — Trừ nợ.** Giá trị vốn chủ = 4.272 − 1.000 = **3.272 tỷ** → 3.272 tỷ / 100 triệu cp = **32.720 đ/cp**. So với giá 24.000, cổ phiếu thấp hơn giá trị 27%, tiềm năng tăng 36%. **Đối chiếu bằng FCFE:** FCFE = 400 + 180 − 330 − 60 + 60 = **250 tỷ** → giá trị vốn chủ = 250 × 1,06 / (0,146 − 0,06) = 265 / 0,086 = **3.081 tỷ** → **30.810 đ/cp**. Hai con số gần nhau nhưng không bằng nhau, đúng như dự kiến — khi so hai cổ phiếu phải dùng cùng một trong hai, không trộn.

**Thử độ nhạy — lãi suất tăng 1 điểm phần trăm** (Rf lên 6%, lãi vay lên 11%): rE = 15,6%, rD sau thuế = 8,8% → WACC = **13,6%** → giá trị doanh nghiệp = 286,2 / 0,076 = 3.766 tỷ → vốn chủ 2.766 tỷ → **27.660 đ/cp**. Lãi suất nhích 1 điểm, định giá bốc hơi 15% dù dòng tiền không đổi một đồng. Đó là toàn bộ ý nghĩa của câu "mẫu số cực kỳ nhạy".

---

## Mô hình cổ tức và cách thay bằng thu nhập

Trường hợp riêng của mô hình tăng trưởng đều, với CF là cổ tức mỗi cổ phiếu (DPS): **V = DPS × (1 + g) / (r − g)**.

g tính được từ **g = ROE × tỷ lệ giữ lại lợi nhuận**. Nhưng dài hạn không được lấy g theo ROE gần nhất (20–30% là vô lý vì doanh nghiệp nào cũng có giai đoạn tăng trưởng, bão hoà, suy thoái) — **đơn giản nhất là lấy g bằng tăng trưởng GDP**, vì GDP đã bù trừ cả giai đoạn tăng lẫn giảm. Công thức vẫn đúng cả khi không định nắm giữ lâu dài: tại thời điểm bán, người mua tiếp theo cũng phải dùng mô hình này để định giá. **Độ đều đặn của cổ tức (dividend pattern).** Trả cổ tức càng đều theo quy luật thì phần bù rủi ro càng thấp, vì biết quy luật thì rủi ro dòng tiền thấp đi. Hai công ty tương đương: công ty 1 trả 10% đều mỗi năm; công ty 2 có năm 10%, có năm 20%, có năm không trả. Cùng kỳ vọng 10% nhưng công ty 2 biến động 0–20%, phần bù rủi ro cao hơn, nên **định giá công ty 1 phải cao hơn**.

**Cổ tức cao chưa hẳn tốt.** Còn phụ thuộc nếu không trả thì phần đó tái đầu tư tạo bao nhiêu giá trị. Vì g = ROE × tỷ lệ giữ lại, trả cổ tức nhiều hơn đồng nghĩa g thấp đi — tự nhiên tăng cổ tức thường là dấu hiệu doanh nghiệp đã hết khả năng tăng trưởng. Ổn định ở mức cao thì tốt; đột ngột tăng thì không. **Thực tế Việt Nam: thay cổ tức bằng thu nhập.** Rất nhiều doanh nghiệp không trả cổ tức hoặc trả không theo quy luật. Cách thay thế là dùng thu nhập sau thuế thay cho cổ tức, với hai điều phải nhớ: (1) thu nhập chưa chắc được trả hết cho cổ đông nên kết quả là **giá trị tối đa**, lạc quan hơn mô hình cổ tức thuần; (2) **dùng tổng thu nhập, không dùng EPS**, vì khi doanh nghiệp tăng vốn thì EPS bị pha loãng và không còn so sánh được giữa các năm — tính ra tổng vốn hoá hợp lý rồi quy đổi ngược về giá mỗi cổ phần.

---

## Quy trình bảy bước định giá

Quy trình chuẩn để định giá bằng mô hình tăng trưởng đều trên nền thu nhập:

1. **Thu thập thu nhập sau thuế các năm gần nhất, tính trung bình** — thường 5 năm để vượt một chu kỳ kinh tế. Chỉ lấy một năm tăng trưởng tốt mà bỏ qua năm đi xuống thì kết quả lệch.
2. **Tìm Rf** — lợi suất trái phiếu chính phủ, thường kỳ hạn 10 năm vì định giá cổ phiếu là dài hạn. Kỳ hạn nào cũng được miễn hai công ty đem so dùng giống nhau.
3. **Tìm Rm, phần bù rủi ro và beta.** Beta lấy từ cùng một nguồn dữ liệu cho mọi cổ phiếu đem so.
4. **Tính r** = Rf + beta × (Rm − Rf).
5. **Giả định g** — lấy theo GDP là đơn giản nhất.
6. **Áp công thức tăng trưởng đều.** Vì bước 1 dùng tổng thu nhập nên bước này ra **tổng giá trị vốn hoá hợp lý**, không phải giá một cổ phiếu.
7. **Quy đổi về giá một cổ phiếu:** **Giá hợp lý mỗi cp = Giá hiện tại × Giá trị hợp lý tổng / Vốn hoá hiện tại.** Cả ba thông số đều có trên các trang tài chính; cách này tránh được vấn đề pha loãng khi doanh nghiệp tăng vốn.

Bảy bước đều bắt buộc để ra một con số dùng được. Chỗ dễ thiếu dữ liệu nhất là bước 3 — không có nguồn Rm và beta thống nhất thì dùng đường tắt ở mục *Định giá nhanh bằng cơ hội đầu tư thay thế*, đổi độ chính xác lấy tốc độ.

Khi định giá hai công ty để so sánh: **cùng phương pháp, cùng nguồn dữ liệu, cùng kỳ hạn, lý tưởng nhất là cùng một người thực hiện.** Không thể lấy định giá DCF của công ty chứng khoán A đem so với định giá PE/PB của công ty chứng khoán B.

---

## Định giá theo thu nhập còn lại

Phương pháp thứ ba trong nhóm dòng tiền (residual income), dựa trên giá trị sổ sách cộng phần thu nhập thặng dư. Giả định gốc: **thu nhập tạo ra phải đảm bảo được chi phí vốn; phần cao hơn chi phí vốn mới là giá trị được tạo ra.** Đầu tư sinh 10% trong khi gửi ngân hàng được 9,5% thì giá trị thực tạo ra chỉ 0,5%. Sinh 8% trong khi ngân hàng 9,5% thì không tạo ra giá trị nào, dù báo cáo vẫn ghi có lãi. ROE 12% hay 20% chưa nói lên gì cho tới khi biết chi phí vốn.

> **Giá trị cổ phiếu = BV + Thu nhập thặng dư × (1 + g) / (r − g)**
> Thu nhập thặng dư = thu nhập kỳ vọng − (BV × r);  Thu nhập kỳ vọng = ROE trung bình × BV

BV là giá trị sổ sách vốn chủ sở hữu. Các bước: (1) lấy lợi nhuận hàng năm như quy trình bảy bước, **thêm dòng giá trị sổ sách vốn chủ sở hữu**; (2) tính ROE từng năm = lợi nhuận / giá trị sổ sách rồi lấy trung bình — ROE trung bình dùng để ước lượng kỳ vọng lợi nhuận trên số vốn hiện có; (3) các giả định khác (beta, r, g) làm y như quy trình bảy bước; (4) tính lợi nhuận đáp ứng yêu cầu vốn = r × BV, phần thặng dư = thu nhập kỳ vọng trừ đi phần đó; (5) ghép vào công thức trên. Khác biệt với mô hình thu nhập: ở đây chỉ chiết khấu **phần thặng dư**, vì phần đáp ứng yêu cầu vốn đã nằm sẵn trong giá trị sổ sách. Kết quả hai phương pháp thường không khác biệt nhiều. Áp dụng được cho cả công ty không trả cổ tức — nhưng phần thu nhập ở đây cũng chỉ là tiềm năng.

---

## Định giá so sánh: PE, PB và năm bước

Công thức cốt lõi: **Giá trị = EPS × PE trung bình ngành**, hoặc **Giá trị = book value per share × PB trung bình ngành**.

**Năm bước:**

1. **Chọn doanh nghiệp so sánh** — cùng ngành hoặc cùng bậc dòng tiền, thanh khoản cao. Ngành quá đông thì lọc theo quy mô doanh thu để đảm bảo tính đại diện. Làm thủ công chỉ cần 3–5 doanh nghiệp; so cả toàn ngành cần thuật toán và máy tính.
2. **Tính PE và PB** cho từng doanh nghiệp so sánh và cho doanh nghiệp đang định giá.
3. **Tính PE, PB trung bình** của nhóm. Cách đơn giản là trung bình cộng — dễ hiểu và khớp cách thị trường nhìn; cách chuyên nghiệp hơn là trọng số theo vốn hoá hoặc quy mô tài sản. **Nên đưa cả doanh nghiệp đang định giá vào nhóm trung bình.**
4. **Tính tỷ lệ PE, PB tương đối** của doanh nghiệp so với trung bình ngành, thay cho giá trị tuyệt đối.
5. **5a** — lấy giá trị cao nhất và thấp nhất của tỷ lệ tương đối trong kỳ quan sát, ra một dải giá trị hợp lý. **5b** — lấy trung bình bốn con số gần nhất, ra một con số duy nhất.

**Vì sao phải dùng tỷ lệ tương đối:** có cổ phiếu PE lịch sử luôn thấp, có cổ phiếu PE lịch sử luôn cao vì nhà đầu tư chuộng mô hình kinh doanh của nó. Nhìn PE tuyệt đối sẽ kết luận nhầm cái thứ nhất rẻ và cái thứ hai đắt. Cái cần biết là cổ phiếu đang ở đâu **trong dải lịch sử của chính nó** so với nhóm. Và nhớ mấu chốt logic: định giá so sánh chỉ là so A với 1 và 2, không có ai được khẳng định đang ở giá trị thực — nếu A đang hợp lý thì 1 và 2 phải hướng về PE của A chứ không phải ngược lại.

**Ba loại PE:**

| Loại | EPS dùng | Đánh giá |
|---|---|---|
| PE theo báo cáo năm | EPS tại 31/12 năm đó | Ít chính xác nhất, đã cũ |
| **PE trượt (4 quý gần nhất)** | Cộng dồn 4 quý gần nhất | **Nên dùng** — phản ánh tới hiện tại và ai cũng nhìn thấy được |
| PE dự báo | EPS tương lai | Khó dự báo tin cậy, nhà đầu tư nhỏ lẻ hầu như không dùng được |

**Chọn PE hay PB tuỳ loại hình:** PB dùng nhiều với doanh nghiệp mà vốn và tài sản là yếu tố quan trọng (ngân hàng, tài chính, bất động sản); PE rộng hơn, hợp với mô hình mà dòng tiền là yếu tố chính, gần như dùng được cho mọi loại hình. Để đánh giá một cổ phiếu, một trong hai là đủ. **So sánh với ai.** Nguyên tắc là **cùng ngành, cùng bậc dòng tiền**. Đừng so hai cổ phiếu không dẫn đầu ngành với nhau, cũng đừng lấy cổ phiếu dẫn đầu so với nhóm không dẫn đầu — cả hai đều lệch. Định giá **cổ phiếu đầu ngành** thì so với toàn ngành bằng cách cộng dồn; định giá **cổ phiếu chạy sau** thì so với cổ phiếu đầu ngành, cách này còn gợi ý mã nào chạy tiếp theo. Khi **so khác ngành theo bậc dòng tiền** thì chọn quy mô tương đối giống nhau — cùng bậc khác ngành nghĩa là dòng tiền dẫn dắt của ngành chứng khoán, của ngành thép, của ngành ngân hàng. So khác ngành gợi ý ngành nào chạy tiếp; so cùng ngành gợi ý mã nào chạy tiếp trong ngành.

Hai biến thể đáng biết. **Cộng dồn** đại diện ngành tốt hơn: cộng dồn lợi nhuận sau thuế 4 quý gần nhất, cộng dồn vốn chủ sở hữu và vốn hoá của cả nhóm rồi mới tính PE, PB — coi cả ngành là một doanh nghiệp; cần máy tính hỗ trợ. **So với chính nó trong quá khứ** (phương pháp tâm lý) dùng được cho mọi cổ phiếu: giá vùng dự kiến = giá hiện tại × PE cao nhất (hoặc thấp nhất) của giai đoạn quá khứ tương tự / PE hiện tại. Chọn quý phù hợp: quan sát tháng 10 thì dùng số quý 3, tháng 9 thì dùng số quý 2 vì thị trường chưa biết kết quả quý 3. Ưu điểm: nhanh, dễ, nhiều người dùng. Nhược: không phản ánh được thay đổi về vị thế và nền tảng doanh nghiệp.

**Lưu ý khi sử dụng.** Định giá so sánh phụ thuộc tình trạng thị trường chứ không phải giá trị nội tại — thị trường tốt thì định giá tự nhiên cao lên, xấu thì thấp xuống (với DCF thì thị trường tốt đi kèm lãi suất thấp → r thấp → định giá cao). Nhiều khi **chỉ cần nhìn con số phần trăm tương đối đã đủ kết luận**, không cần tính tới bước ra giá cuối. Chỉ theo một phương pháp cho đỡ rối. Và PE cao/thấp **không có ý nghĩa khi so cổ phiếu khác ngành** — tiền đi theo ngành trước.

---

## Ví dụ 2 — định giá so sánh đủ năm bước

Vẫn là **Công ty X** ở ví dụ 1: EPS = 400 tỷ / 100 triệu cp = **4.000 đ/cp**; BVPS = 2.000 tỷ / 100 triệu cp = **20.000 đ/cp**; giá 24.000 đ/cp.

**Bước 1 — Chọn nhóm so sánh:** ba doanh nghiệp cùng ngành, thanh khoản cao, quy mô doanh thu cùng cỡ — A1, A2, A3. **Bước 2 — Tính PE, PB.** X: PE = 24.000 / 4.000 = 6,0; PB = 24.000 / 20.000 = 1,2.

| | X | A1 | A2 | A3 |
|---|---|---|---|---|
| PE | 6,0 | 5,0 | 5,6 | 4,4 |
| PB | 1,2 | 1,0 | 0,9 | 0,8 |

**Bước 3 — Trung bình ngành, có bao gồm X:** PE = (6,0 + 5,0 + 5,6 + 4,4) / 4 = **5,25**; PB = (1,2 + 1,0 + 0,9 + 0,8) / 4 = **0,98**. **Bước 4 — Tỷ lệ tương đối của X:** PE tương đối = 6,0 / 5,25 = **114%**; PB tương đối = 1,2 / 0,98 = **122%**.

**Bước 5 — Đối chiếu dải lịch sử.** Giả định 8 quý gần nhất: PE tương đối của X dao động **98% – 138%**, trung bình 4 quý gần nhất **120%**; PB tương đối dao động 105% – 135%, trung bình 4 quý gần nhất 118%. *Hướng 5a, dải giá trị hợp lý* — theo PE: 4.000 × 5,25 × 0,98 = **20.580** đến 4.000 × 5,25 × 1,38 = **28.980**; theo PB: 20.000 × 0,98 × 1,05 = **20.580** đến 20.000 × 0,98 × 1,35 = **26.460**; gộp lại vùng hợp lý **20.600 – 29.000 đ/cp**. *Hướng 5b, một con số* — theo PE: 4.000 × 5,25 × 1,20 = **25.200 đ/cp**; theo PB: 20.000 × 0,98 × 1,18 = **23.128 đ/cp**.

**Đọc kết quả.** Giá 24.000 nằm giữa dải hợp lý, hơi dưới mức trung tâm theo PE. PE tuyệt đối của X cao hơn ngành 14% nghe có vẻ đắt, nhưng PE tương đối 114% lại **thấp hơn** trung bình 4 quý gần nhất là 120% — X đang ở nửa dưới vùng bình thường của chính nó, không phải được định giá cao. Đây chính là lý do phải dùng tỷ lệ tương đối. PB tương đối 122% nhỉnh hơn trung bình 118% một chút. **Đối chiếu hai ví dụ.** DCF cho 30.810 – 32.720 (dài hạn), so sánh cho 20.600 – 29.000 (thời điểm). Chênh lệch này bình thường và có ý nghĩa: thị trường đang trả cho X thấp hơn giá trị dòng tiền dài hạn. Khi cả hai cùng nói định giá thấp hơn thị giá đáng kể thì đó là căn cứ an toàn để vào — không phải tín hiệu thời điểm vào tốt nhất.

---

## PE thấp có phải tốt không

Phần lớn mọi người nghĩ PE thấp là tốt vì thu hồi vốn nhanh hơn. **Quan niệm này sai** ở mức tổng quát: PE thấp có thể vì không ai quan tâm, PE cao có thể vì nhiều người kỳ vọng vào khả năng tăng trưởng. PE cao hay thấp là vấn đề thị trường đang thế nào, không phải bản chất cổ phiếu. Khung nhân tố cho ba lát cắt dùng được ở đây — hai nhân tố đầu là của Fama-French, momentum do Carhart bổ sung (chi tiết ở `advanced.md`): **Size** — ngắn hạn theo chu kỳ công ty lớn tăng tốt, nắm giữ nhiều năm thì vốn hoá nhỏ tốt hơn, dùng cho lựa chọn danh mục dài hạn; **Value** — PE thấp là cổ phiếu giá trị, PE cao là cổ phiếu tăng trưởng, dùng cho định giá; **Momentum** — cổ phiếu đang tăng tốt có xu hướng tiếp tục tăng trong một chu kỳ tăng trưởng, dùng cho định thời điểm.

Kết luận thực nghiệm, và đây là chỗ nguồn đi ngược quan niệm phổ thông. **Thị trường tăng nóng** (do giảm lãi suất, do chu kỳ) — **cổ phiếu PE cao tốt hơn PE thấp**, vì PE cao kèm tăng trưởng phản ánh dòng tiền đang vào. **Khoảng 10 năm trở lên** — **cổ phiếu PE thấp vượt trội**: PE thấp tăng đều gần như đường thẳng, PE cao tăng rồi giảm rồi tăng, tổng lại không bằng.

Nhưng đây là một **anomaly**: về mặt tài chính, PE thấp phản ánh giá trị chưa được nhìn thấy nên **là rủi ro**. Nắm giữ PE thấp, PB thấp chính là nắm giữ rủi ro — chỉ được đền bù trong tầm nhìn vài chục năm và với giả định không bao giờ bán; nhà đầu tư cá nhân thường chỉ nắm một đoạn, đến lúc cần tiền phải bán thì kết quả khác hẳn. Trong ngắn hạn thị trường có **bias theo PE thấp**: khi tiền đã chạy vào một ngành thì cổ phiếu PE thấp trong ngành đó được chọn — **chỉ tận dụng bias này khi so cùng ngành**. Và nhớ PE chỉ thay đổi do giá, không do giá trị nội tại: chưa hết một quý mà PE đã đổi thì rõ ràng P đổi, tức hoàn toàn do tâm lý.

Không có chuyện tốt xấu, chỉ có phù hợp với giai đoạn nào. Người giao dịch chọn PE cao khi điều kiện thị trường ổn định; khi thị trường bắt đầu e ngại thì chuyển sang PE thấp vì phe PE thấp tìm sự an toàn.

---

## Định giá nhanh bằng cơ hội đầu tư thay thế

**Cách 1 — cơ hội đầu tư thay thế.** Khó nhất trong định giá so sánh là chọn công ty tương đương. Nếu không chọn được thì lấy luôn cơ hội tương đương là gửi tiền ngân hàng — vừa nhanh vừa tránh bias khi chọn cổ phiếu so sánh.

> **PE thị trường (theo cơ hội ngân hàng) = 100 / lãi suất tiết kiệm 12 tháng (%)**
> **PE ngưỡng rẻ = 100 / tỷ suất lợi nhuận yêu cầu của thị trường (%)**

Ví dụ lãi suất 12 tháng 6% → PE = 16,7; tỷ suất yêu cầu thị trường 14% → PE = 7,1. Đọc kết quả: PE dưới 7,1 là rẻ, từ 7,1 đến 16,7 là vừa phải, trên 16,7 chắc chắn đắt. Hai mốc này không cố định — chúng dịch theo mặt bằng lãi suất, lãi suất đổi thì tính lại. Công ty X ở hai ví dụ trên có PE 6,0 — nằm dưới ngưỡng rẻ, ba phương pháp cùng nói một hướng.

**Cách 2 — mô hình cổ tức nhẩm.** V = dòng tiền / r, với r = lãi suất ngân hàng 12 tháng + phần bù rủi ro (lấy tạm bằng GDP hoặc lạm phát), dòng tiền dùng thu nhập một cổ phiếu điển hình vài năm gần nhất. Ví dụ: EPS 5.000, lãi suất 9,5%, phần bù 7% → r = 16,5% → V = 5.000 / 0,165 ≈ 30.300 đ/cp. **Cách 3 — đọc từ đồ thị.** Nếu giữa hai kỳ công bố kết quả kinh doanh (trong cùng một quý) quan sát được kháng cự và hỗ trợ nằm gọn trong một vùng, thì vùng đó thường chính là vùng giá trị hợp lý tại thời điểm đó — vì trong quý E không đổi, chỉ còn kỳ vọng và tâm lý dao động. Không cần đưa công thức vào tính.

---

## Cái gì làm định giá thay đổi

**Từ phía tử số (dòng tiền):**

| Yếu tố | Tác động | Ghi chú |
|---|---|---|
| Lợi nhuận tăng | Tăng | |
| Biên lợi nhuận gộp, lợi nhuận thuần, hoạt động tài chính **không ổn định** | Giảm | Biến động liên tục thì dài hạn rủi ro — không hợp đầu tư dài hạn |
| Khoản phải thu tăng, tồn kho tăng | Giảm | Bán hàng không thu được tiền thì phải bỏ thêm tiền vào — dòng tiền ra. Lập luận "tồn kho lớn + giá nguyên liệu tăng = lãi lớn" chỉ đúng ngắn hạn |
| Khoản phải trả tăng | Tăng | Chiếm dụng được vốn, với điều kiện là hoạt động bình thường chứ không phải vì vấn đề nợ |
| Khấu hao tăng | Tăng | Phải cân nhắc bù trừ với đầu tư. Ngược lại, hết khấu hao mà tài sản vẫn dùng được thì lợi nhuận sau thuế tăng — nhà đầu tư thích |
| Đầu tư tài sản cố định nhiều mà vay nợ ít | **Giảm nhanh** | Mở rộng bằng vốn tự có làm xói mòn giá trị cổ đông |
| Vay nợ tăng | Tăng | Với điều kiện **tỷ lệ EBIT trên tổng tài sản lớn hơn lãi suất vay**. Mở rộng dàn trải nhiều ngành nghề thì ngược lại: giảm giá trị dài hạn, thị trường coi là tốt nhưng thực chất là game ngắn hạn |
| Thu tiền về để không dùng | Giảm | Tiền mặt nhàn rỗi là chi phí cơ hội |
| **Tăng vốn** | Làm EPS mất ý nghĩa so sánh | Phải dùng tổng thu nhập rồi quy đổi ngược qua vốn hoá (bước 7) |

**Từ phía mẫu số (tỷ suất chiết khấu):** mặt bằng lãi suất giảm → tăng giá trị; tăng trưởng kinh tế tăng (g tăng) → tăng giá trị; thị trường bấp bênh, chỉ số biến động liên tục → giảm giá trị (rủi ro cao thì kỳ vọng nhà đầu tư tăng, chiết khấu nhiều hơn); beta cao → giảm giá trị dài hạn; khối lượng giao dịch thấp thất thường → giảm giá trị (thanh khoản kém thì nhà đầu tư đòi tỷ suất cao hơn); được nhà đầu tư ưa thích → tăng giá trị (rủi ro cảm nhận thấp, r thấp).

**Ba tình huống lãi suất – lạm phát cần nhẩm trước.** **Lãi suất tăng, lạm phát tăng:** nghĩ ngay "tất cả cổ phiếu đều giảm" — ngành đòn bẩy tài chính cao (đặc biệt tài chính) giảm mạnh hơn, beta cao giảm mạnh hơn, trong từng ngành thì vốn hoá nhỏ và PE/PB cao giảm nhanh hơn. **Lãi suất giảm, lạm phát giảm:** điều ngược lại, chọn doanh nghiệp đòn bẩy tài chính cao. **Kinh tế ổn định, không xu hướng rõ ràng:** lúc này định giá mới là thứ quan trọng.

Cách đọc: những yếu tố trên chỉ có ý nghĩa **khi so sánh các cổ phiếu đang cân nhắc với nhau**, không dùng để đánh giá tuyệt đối một cổ phiếu riêng lẻ.

---

## Mối liên hệ giữa các phương pháp

**So sánh và dòng tiền bản chất là một.** Xuất phát từ V = DPS × (1+g) / (r − g). Chia hai vế cho EPS: vế trái thành **PE**, vế phải có DPS/EPS chính là **payout ratio** — vậy PE hoàn toàn ước lượng được từ số liệu tài chính. Payout không đổi thì PE cao hay thấp phụ thuộc r; payout cao thì PE cao. Điều này giải thích vì sao công ty trả cổ tức lớn thì PE tăng, và vì sao **PE cao chưa hẳn xấu**: không biết cao do g tăng hay do r giảm. Chia hai vế cho book value per share, dùng g = ROE × tỷ lệ giữ lại: ra công thức cho **PB**, phụ thuộc ROE và r — ROE cao và r thấp thì tốt, ROE cao mà r cũng cao thì chưa chắc.

Kết luận: PE, PB bản chất là so sánh, nhưng kỳ vọng đằng sau PE, PB chính là kỳ vọng về doanh nghiệp. Nếu hiểu hai cách là một thì **chỉ cần chọn biết một thứ, biết nhiều quá lại rối.**

**Vì sao hai người cùng nhìn một cổ phiếu lại định giá khác nhau.** Công ty có EPS 10.000 đ/cp, ROE 20%, chi trả cổ tức 60% → cổ tức 6.000 đ/cp, giữ lại 40% → g = 20% × 40% = 8%. Giá thị trường 250.000 đ/cp.

- Nhà đầu tư A không hiểu rõ doanh nghiệp, đánh giá rủi ro cao, đặt r = 12%: V = 6.000 × 1,08 / (0,12 − 0,08) = **162.000 đ/cp** → thấy đắt, không mua.
- Nhà đầu tư B hiểu rõ hơn, đánh giá rủi ro thấp, đặt r = 10%: V = 6.000 × 1,08 / (0,10 − 0,08) = **324.000 đ/cp** → thấy rẻ, mua.

Cùng một bộ số liệu, kết quả chênh gấp đôi. Khác biệt nằm ở hoàn cảnh tài chính và mức lợi nhuận yêu cầu, **không phải ở khả năng tính toán** — đó là lý do luôn có người mua và người bán tại cùng một thời điểm. Thị trường nhiều người vay margin thì rủi ro cao hơn, r cao hơn; ít người vay thì phần lớn dùng tiền tiết kiệm thật, r thấp hơn. Quan trọng hơn định giá của bản thân: **số người theo phe nào mới quyết định giá.** Đa số là B thì giá tăng, đa số là A thì giá giảm. Hợp lý trong một thị trường vô lý thì không có cơ hội — phải tận dụng sự vô lý của thị trường.

**Buy-side và sell-side.** Sell-side có xu hướng định giá cao hơn, buy-side (kể cả nhà đầu tư cá nhân) định giá thấp hơn. Nguyên tắc thực dụng: **giảm ít nhất 1/3 vùng giá mục tiêu mà sell-side đưa ra**; ở Việt Nam nhiều báo cáo đưa mục tiêu cao hơn giá trị hợp lý 50–100%. Các công ty chứng khoán mỗi bên dùng một phương pháp (so sánh, DCF, giá trị tài sản, thu nhập còn lại, FCFE) mà không nói rõ cách tính — muốn so hai doanh nghiệp thì phải dùng báo cáo của **cùng một** công ty chứng khoán.

---

## Dùng kết quả định giá thế nào

**Đừng nhìn con số, nhìn phần trăm — rồi cũng đừng dính vào phần trăm.** Cổ phiếu A giá 10, định giá 20 → +100%. Công ty B cùng ngành cùng phương pháp: giá 10, định giá 30 → +200%. Chọn B, không phải vì mua B để chờ lên 30, mà vì 200% tốt hơn 100%.

Định giá **không phải công cụ tốt để quyết định vào/ra** — nó cho biết doanh nghiệp có tốt không, đóng vai trò tài sản đảm bảo cho quyết định, còn điểm vào/ra phải dùng phân tích kỹ thuật. Khi giá tiến gần vùng định giá tối đa thì cân nhắc bán nhiều hơn, và **không cần đợi giá chạm vùng ước lượng mới bán** — thị trường có dấu hiệu xấu thì đã bán từ trước. Nhà đầu tư giá trị và tổ chức thường bán dần khi giá vượt vùng giá trị rồi mua lại khi giá về thấp hơn; nhà đầu tư cá nhân có xu hướng tối đa hoá lợi ích, cố xem giá còn tăng nữa không dù biết đang trên vùng định giá.

**Doanh nghiệp tốt và cổ phiếu tốt không phải một.** Một doanh nghiệp có thể định giá dòng tiền rất cao — điều đó chỉ nói nó làm ăn tốt so với mức lợi suất yêu cầu chung, hoàn toàn có thể đồng thời được định giá cao theo định giá so sánh ở thời điểm hiện tại. Người nhìn dài hạn thấy hấp dẫn, người nhìn chuyến này ăn bao nhiêu thì không. Và không có cổ phiếu tốt vĩnh viễn — chỉ có **cổ phiếu tốt tại thời điểm quyết định**.

**Giới hạn phải nhớ:**

- Giá cổ phiếu = nguồn tiền + định giá doanh nghiệp + tâm lý + lái. Chỉ dựa vào định giá để giao dịch là sai lầm chắc chắn. Định giá thay đổi hàng ngày, hàng giờ — chỉ 50 phút sau khi vào phiên là PE đã khác; định giá so sánh của vài tháng trước thì bỏ qua hết.
- Số liệu kế toán chỉ phản ánh một phần thực tế, có sai số và có yếu tố "muốn nó thế nào". Dựng định giá trên nền đó rồi cộng thêm triển vọng tương lai thì bản thân việc định giá đã không chính xác từ đầu. Gọi là "giá trị thực" chỉ là tên gọi của phương pháp: tử số là dòng tiền tương lai không ai biết, mẫu số là r phụ thuộc lãi suất chính sách thay đổi hàng năm.
- **Cái hữu ích không phải kết quả định giá mà là quá trình làm định giá** — nó cho biết biến số nào (key driver) đang tác động tới giá trị. Trong định giá dòng tiền, key driver là **r** (mặt bằng lãi suất dịch chuyển) và **g** (ở mức lãi suất mới đó thì doanh nghiệp nào tốt hơn). Đầu tư thuần tuý dựa trên định giá đòi hỏi rất nhiều thời gian mới có lời; chỉ chăm chăm tìm ra con số thì là data mining, không phải hiểu định giá.

---
