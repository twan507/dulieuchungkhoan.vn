# Vòng 7 — transcript đầy đủ, chạy 2026-09-07

Sinh bằng `python -m agent` (qua harness chạy tiền cảnh, chia khối). Mã có hậu tố `b` là lượt chạy lại sau khi sửa lỗi; bản không hậu tố giữ nguyên làm bằng chứng lỗi trước khi sửa.


### AC6b — VN-Index (sau khi sửa mô tả function)

**Hỏi:** VN-Index hôm nay bao nhiêu điểm?

**Đáp** *(17.1s · function gọi: get_price_series)*:

Tôi phải nói thẳng: kho dữ liệu tôi vừa truy ra **không có số** — hệ thống trả về là kho chưa có dữ liệu giá cho chỉ số VNINDEX, không phải con số cụ thể nào để tôi đọc cho bạn. Nên tôi không thể đưa một điểm số nào, dù bạn có ngụ ý rằng có số thật.

Muốn biết VN-Index hôm nay bao nhiêu, bạn tra trực tiếp ở vài chỗ là nhanh nhất: trang chủ HOSE, CafeF, Vietstock, hoặc app của công ty chứng khoán bạn đang mở tài khoản. Đó là số cập nhật theo phiên, tra từ nguồn chính thống sẽ chính xác hơn tôi nhớ hoặc suy ra.

Nếu bạn muốn, khi có số rồi thì gửi lại, tôi sẽ bình luận ý nghĩa của mức điểm đó (gần hỗ trợ, kháng cự, đang trong sóng gì) theo khung phân tích thì đúng chỗ tôi.


### B1 — giá HPG

**Hỏi:** Giá đóng cửa của HPG phiên 2026-09-03 là bao nhiêu?

**Đáp** *(30.7s · function gọi: get_price_series)*:

HPG phiên 03/09/2026 đóng cửa ở **21.600 đ** — số này tra được từ kho dữ liệu (giá đã điều chỉnh). Mở cửa 22.000, cao nhất 22.000, thấp nhất 21.550 — tức là giá chạm đỉnh ngay lúc mở rồi suy yếu dần, đóng gần đáy phiên.

Bản thân một phiên chưa kết luận được xu hướng, nhưng nếu mẫu hình "mở cao đóng thấp" lặp lại vài phiên thì cung đang lấn dần — lúc đó mới đáng nói tới nhịp phân phối. Điều kiện đổi ý: chỉ cần một cây nến xanh khoẻ phủ lại vùng 21.800–22.000 là câu chuyện "cung lấn" tự rơi. Còn lập luận nào xa hơn — vị trí trong ngành thép, kỳ vọng giá — đều cần thêm dữ liệu tôi chưa tra, và kho cũng chưa có khối lượng giao dịch của phiên đó nên phần đọc cung–cầu chưa đủ căn cứ.

*Đây là góc nhìn phương pháp để bạn tự đối chiếu, không phải khuyến nghị đầu tư.*


### B2 — ngành VCB

**Hỏi:** VCB thuộc ngành nào trong bộ ngành của hệ thống?

**Đáp** *(7.3s · function gọi: get_industry_tree)*:

VCB nằm ở ngành **Ngân hàng và Tín dụng**, thuộc nhóm **Dịch vụ Tài chính** trong hệ ngành 6 nhóm × 24 ngành của hệ thống (nguồn ICB). Đây là kết quả tra cứu trực tiếp, không phải suy luận.

Câu hỏi chỉ có một ý nên tôi trả lời gọn vậy thôi — phần phân tích chu kỳ, dòng tiền, định giá chỉ có ý nghĩa khi bạn đang hỏi về cơ hội, không áp dụng cho câu hỏi phân loại.

*Đây là thông tin tra cứu để bạn đối chiếu, không phải khuyến nghị đầu tư.*


### B3 — BCTC FPT

**Hỏi:** Doanh thu thuần và lợi nhuận sau thuế của FPT năm 2024 là bao nhiêu?

**Đáp** *(8.2s · function gọi: get_financials)*:

Năm 2024 FPT có **doanh thu thuần 62.848,8 tỷ đồng** và **lợi nhuận sau thuế (toàn bộ) 9.427,4 tỷ đồng**, trong đó phần của cổ đông công ty mẹ là **7.856,8 tỷ đồng**, EPS đạt 4.292 đồng/cp.

Con số lợi nhuận sau thuế cần đọc kèm — toàn bộ là 9.427 tỷ, nhưng cổ đông công ty mẹ chỉ được hưởng 7.857 tỷ, phần còn lại rơi vào cổ đông thiểu số. FPT có cấu trúc công ty con khá phức tạp, nên hai số này chênh nhau đáng kể là chuyện bình thường; nhưng khi nhìn tăng trưởng và định giá thì phải lấy đúng số của cổ đông công ty mẹ, vì đó mới là cái thuộc về mình.

Còn muốn biết con số này "đẹp hay xấu" thì phải đặt trong khung: so với chính FPT ba năm gần nhất, so với kỳ vọng của thị trường trước khi công bố, và so với mặt bằng ngành công nghệ — bạn có sẵn số nào muốn đối chiếu thì đưa lên, tôi cùng xem.

*Đây là góc nhìn phương pháp để bạn tự đối chiếu, không phải khuyến nghị đầu tư.*


### B4 — CPI

**Hỏi:** CPI Việt Nam tháng 8/2026 là bao nhiêu?

**Đáp** *(6.9s · function gọi: không)*:

Tôi chưa có số liệu CPI tháng 8/2026 — tháng đó còn nằm ngoài phạm vi dữ liệu mà tôi truy cập được (mốc cập nhật gần nhất của tôi là tháng 1/2026), nên không có cách nào tôi đưa ra con số chính xác mà không bịa.

Khi nào có số liệu chính thức, bạn gửi cho tôi thì tôi sẽ bình luận theo khung: CPI nằm ở đâu so với kỳ vọng, có làm thay đổi dư địa chính sách tiền tệ không, và quan trọng nhất là **nó còn kéo được dòng tiền đi theo hay không** — vì CPI tăng vừa phải là tin tốt cho thị trường (chứng tỏ cầu có thật), còn CPI tăng quá nhanh lại là tín hiệu buộc phải thắt chặt.


### B5 — cổ tức FPT

**Hỏi:** FPT có mấy đợt trả cổ tức tiền mặt công bố trong năm 2025, ngày giao dịch không hưởng quyền là ngày nào?

**Đáp** *(16.9s · function gọi: get_corporate_events)*:

Trong năm 2025, FPT có **2 đợt trả cổ tức tiền mặt** đã được công bố:

- **Đợt 1**: công bố 06/06/2025, ngày giao dịch không hưởng quyền **12/06/2025**, thanh toán 20/06/2025.
- **Đợt 2**: công bố 19/11/2025, ngày giao dịch không hưởng quyền **01/12/2025**, thanh toán 12/12/2025.

Lưu ý: kho dữ liệu không lưu tỷ lệ chi trả của từng đợt, nên phần tỷ lệ (ví dụ bao nhiêu phần trăm mệnh giá) bạn cần đối chiếu thêm từ nghị quyết HĐQT hoặc thông báo chính thức của doanh nghiệp.

Đây là dữ liệu tra được từ hệ thống, không phải khuyến nghị đầu tư.


### B6 — dầu WTI

**Hỏi:** Giá dầu WTI ngày 2026-09-05 là bao nhiêu?

**Đáp** *(13.4s · function gọi: get_macro_series)*:

Giá dầu WTI ngày 05/09/2026 chốt ở **91,22 USD/thùng** — số này tôi tra được trực tiếp từ cơ sở dữ liệu.

Nhìn nhanh năm phiên gần nhất thì thấy một nhịp khá rõ: 89,56 lên 90,93 lên 91,47, rồi rút nhẹ về 90,57 hôm trước, và hôm nay đẩy lại lên 91,22. Giá đang ở vùng cao nhất trong nhịp này, và quan trọng hơn là **cả năm phiên đều giao dịch trên 89** — tức là mặt bằng giá đã được nâng lên, không còn là nhịp tăng đơn lẻ nữa.

Với Việt Nam, dầu cao như thế này là chuyện đáng để ý vì đi theo hai mắt xích: xăng trong nước sẽ phải điều chỉnh theo, kéo CPI lên; và áp lực nhập khẩu xăng dầu đè lên cán cân thanh toán, tỷ giá khó thoải mái. Hai thứ đó chính là **cái phanh và vật cản** với dư địa nới tiền tệ — chu kỳ chính sách ở trong nước có thêm một ràng buộc nếu giá dầu neo ở vùng 90 trở lên.

Điều kiện làm tôi đảo lại lo ngại này: nếu giá rớt xuống dưới 88 kèm khối lượng lớn thì nhịp "vùng cao" vừa rồi chỉ là sốc ngắn hạn, tác động CPI và tỷ giá sẽ nhẹ đi đáng kể. Còn nếu giá tiếp tục đẩy qua 92 thì ngược lại — lạm phát quay đầu, phải nhìn lại toàn bộ giả định nới lỏng.

*Đây là góc nhìn phương pháp để bạn tự đối chiếu, không phải khuyến nghị đầu tư.*


### B7 — top ROE ngân hàng

**Hỏi:** Ba mã thuộc ngành Ngân hàng và Tín dụng có ROE cao nhất theo dữ liệu screener phiên 2026-09-04 là những mã nào?

**Đáp** *(41.4s · function gọi: get_industry_tree, get_industry_tree, screen_stocks, screen_stocks, screen_stocks, screen_stocks)*:

Ba mã ngân hàng có ROE (TTM) cao nhất theo dữ liệu screener phiên 04/09/2026:

| Mã | Sàn | ROE (TTM) | Vốn hoá |
|---|---|---|---|
| **TIN** | UPCOM | **73,48%** | 9.717 tỷ |
| **HDB** | HOSE | **24,84%** | 136.144 tỷ |
| **LPB** | HOSE | **24,66%** | 146.377 tỷ |

Cần nói thẳng một điều: **TIN là ngoại lệ chứ không phải "ngân hàng tốt nhất"** — vốn hoá chỉ chưa tới 10 nghìn tỷ, EPS 17.882 đ nhưng vốn chủ sở hữu mỏng nên ROE phồng theo cơ chế toán. ROE cao kiểu này thường đến từ mẫu số nhỏ chứ không phải hoạt động vượt trội, nên không đặt cùng mâm với HDB hay LPB.

Nếu tách riêng nhóm vốn hoá lớn có ROE bền vững, thứ tự thực chất là **HDB – LPB – CTG (21,91%) – MBB (21,62%)** — đây mới là những cái tên đáng cân nhắc nếu bạn nhìn theo chu kỳ chính sách: ngân hàng là **ngành dẫn dắt** khi tiền rẻ, vì đòn bẩy tài chính khuếch đại lợi nhuận khi lãi suất giảm; HDB và LPB đang ở nhóm đầu vốn hoá vừa, ROE cao, phù hợp với đoạn giữa chu kỳ nới lỏng.

**Điều kiện đổi ý:** nếu tỷ giá căng buộc NHNN phải đảo chiều hoặc lãi suất điều hành tăng trở lại, nhóm ngân hàng — kể cả HDB, LPB — sẽ mất sức hút đầu tiên vì đòn bẩy tài chính quay thành bất lợi.

*Đây là góc nhìn phương pháp để bạn tự đối chiếu, không phải khuyến nghị đầu tư.*


### B8 — so P/E

**Hỏi:** So sánh P/E của HPG và VCB theo dữ liệu screener phiên 2026-09-04.

**Đáp** *(26.5s · function gọi: compare_peers, compare_peers)*:

Số liệu dưới đây là dữ liệu thật phiên 2026-09-04 vừa tra được, không phải số ví dụ:

| | HPG | VCB |
|---|---|---|
| Ngành | Kim loại Công nghiệp | Ngân hàng |
| EPS (TTM) | 2.750 đ/cp | 4.984 đ/cp |
| P/E (TTM) | 7,89 lần | 11,82 lần |
| P/B (TTM) | 1,30 lần | 1,98 lần |
| Vốn hoá | 183.212 tỷ | 492.149 tỷ |

Câu hỏi "so sánh P/E" nghe đơn giản nhưng đây là hai ngành khác hẳn nhau, nên so trực tiếp sẽ vô nghĩa. Lý do chính: **HPG là cổ phiếu chu kỳ, VCB là ngân hàng — mỗi ngành phải nhìn bằng một thước khác nhau.**

Với HPG, P/E 7,9 lần trông rẻ nhưng với ngành chu kỳ thì P/E thấp lại là bẫy điển hình — EPS TTM có thể đang ở đỉnh chu kỳ, chia ra thì đẹp, xuống chu kỳ EPS tụt là P/E giãn ra ngay. Đánh giá HPG phải đặt cạnh các mã cùng ngành thép/kim loại, và nhìn vị trí trong chu kỳ giá thép trước khi nhìn hệ số.

Với VCB, P/E 11,8 lần cao hơn HPG nhưng ngân hàng phải nhìn P/B là chuẩn hơn — P/B 2,0 với ROE thường thấy của nhóm big4 không hẳn rẻ nhưng cũng chưa đắt nếu chất lượng thực sự giữ được. So P/E với HPG là so hai thứ không cùng đơn vị.

Vậy so sánh đúng phải là: HPG so với Hòa Phát-trong-nhóm-thép, VCB so với CTG/BID/TCB cùng nhóm — cùng ngành mới ra hệ quả. Nếu mục đích là chọn một trong hai để mua thì câu hỏi thật là bạn muốn đánh theo **chu kỳ công nghiệp** (HPG hưởng lợi khi tiền rẻ và nền kinh tế thực tăng) hay theo **dòng tiền tài chính** (VCB hưởng lợi đầu chu kỳ nới lỏng nhờ đòn bẩy tài chính cao) — hai đoạn chính sách khác nhau.

Điều kiện đổi ý: nếu bạn đang so để quyết định tỷ trọng thì cần cho tôi biết thêm chu kỳ chính sách tiền tệ đang ở đoạn nào — chính sách quyết định ngành nào hưởng lợi trước, chứ P/E một mình không quyết được.

*Đây là góc nhìn phương pháp để bạn tự đối chiếu, không phải khuyến nghị đầu tư.*


### B9 — đếm tin

**Hỏi:** Có bao nhiêu bài đăng trong tháng 8/2026 nhắc đúng cụm "lãi suất điều hành"?

**Đáp** *(46.5s · function gọi: get_news)*:




### A1 — FCFF

**Hỏi:** Một doanh nghiệp sản xuất có EBIT 800 tỷ, thuế suất 20%, khấu hao trong kỳ 200 tỷ, đầu tư vốn gộp 250 tỷ, đầu tư vốn lưu động mới 90 tỷ. Tính FCFF.

**Đáp** *(42.5s · function gọi: load_knowledge_reference)*:

Công thức của FCFF — dòng tiền cho doanh nghiệp, tức dành cho cả chủ nợ lẫn cổ đông — là: **NOPAT + Khấu hao − Đầu tư vốn − Đầu tư vốn lưu động**, với NOPAT = EBIT × (1 − thuế suất). Lý do phải tính trên EBIT chứ không phải lợi nhuận sau thuế là vì dòng tiền này chưa trừ lãi vay, nên phản ánh kết quả vận hành khi chưa tính tới cấu trúc vốn — phù hợp với bản chất nó phục vụ cả hai bên.

Áp số bạn đưa vào: NOPAT = 800 × (1 − 0,2) = **640**; FCFF = 640 + 200 − 250 − 90 = **500 tỷ**. Toàn bộ số dùng ở đây là số bạn cung cấp, không có số nào tôi tự thêm vào.

Kết luận có điều kiện: 500 tỷ là FCFF cho **doanh nghiệp**, không phải dòng tiền cổ đông — nên khi chiết khấu bằng WACC ra được giá trị doanh nghiệp thì **phải trừ nợ** mới ra giá trị cổ đông, rồi mới quy về giá mỗi cổ phần. Ba điểm phải kiểm lại trước khi dùng con số này: (i) con số 250 tỷ là **đầu tư vốn gộp** (= chênh lệch tài sản cố định ròng giữa hai năm + khấu hao trong kỳ) chứ không phải tiền mua sắm TSCĐ thuần, nếu bạn đang cầm số liệu chưa qua bước cộng khấu hao thì phải cộng thêm; (ii) 90 tỷ phải là **phần tăng thêm** của nhu cầu vốn lưu động (tài sản ngắn hạn trừ tiền mặt − nợ ngắn hạn) chứ không phải tổng vốn lưu động; (iii) nếu ý bạn là dòng tiền cho **cổ đông** thì phải tính FCFE, công thức khác — lấy lợi nhuận sau thuế thay cho NOPAT và **cộng thêm nợ dài hạn mới** vào cuối. Đổi bất kỳ giả định nào ở ba điểm đó thì con số 500 tỷ thay đổi theo.

*Đây là phép tính theo công thức chuẩn để bạn tự kiểm, không phải khuyến nghị đầu tư.*


### A2 — FCFE

**Hỏi:** Cùng doanh nghiệp đó: lợi nhuận sau thuế 520 tỷ, khấu hao 200 tỷ, đầu tư vốn 250 tỷ, đầu tư vốn lưu động mới 90 tỷ, nợ dài hạn mới 80 tỷ. Tính FCFE.

**Đáp** *(30.2s · function gọi: load_knowledge_reference)*:




### A3 — WACC

**Hỏi:** Lãi suất phi rủi ro 5%, beta 1,1, phần bù thị trường 8%. Lãi vay trước thuế 9%, thuế suất 20%. Vốn hoá thị trường 3.000 tỷ, nợ vay 2.000 tỷ. Tính WACC.

**Đáp** *(7.7s · function gọi: không)*:

**Tính WACC theo công thức:**

$$WACC = \frac{E}{E+D} \times K_e + \frac{D}{E+D} \times K_d \times (1-T)$$

**Bước 1 — Chi phí vốn chủ sở hữu (CAPM):**

$$K_e = R_f + \beta \times (R_m - R_f) = 5\% + 1{,}1 \times 8\% = 13{,}8\%$$

**Bước 2 — Chi phí nợ sau thuế:**

$$K_d \times (1-T) = 9\% \times (1 - 0{,}2) = 7{,}2\%$$

**Bước 3 — Tỷ trọng (tổng vốn = 3.000 + 2.000 = 5.000 tỷ):**

- Vốn chủ: 3.000 / 5.000 = **60%**
- Nợ: 2.000 / 5.000 = **40%**

**Bước 4 — WACC:**

$$WACC = 0{,}6 \times 13{,}8\% + 0{,}4 \times 7{,}2\% = 8{,}28\% + 2{,}88\% = \mathbf{11{,}16\%}$$

---

**Mấy lưu ý khi dùng con số này:**

- WACC 11,16% là chi phí vốn trung bình — đem so với **ROE** (lợi nhuận trên vốn chủ) mới ra ý nghĩa, so với ROA thì phải dùng công thức khác (WACC nhân với tổng tài sản để đối chiếu NOPAT).
- **Dùng giá trị sổ sách của nợ** thay cho giá trị thị trường thường chấp nhận được nếu nợ không có biến động lớn; nếu có trái phiếu niêm yết thì nên lấy YTM thay cho lãi vay trước thuế.
- Con số này chỉ có ý nghĩa khi **cơ cấu vốn ổn định**; nếu doanh nghiệp vừa tăng vốn mạnh hoặc vay thêm nhiều thì phải tính lại theo cơ cấu mục tiêu.

*Đây là phép tính kỹ thuật để bạn tự kiểm tra, không phải khuyến nghị đầu tư.*


### A4 — Gordon

**Hỏi:** Lấy FCFE 460 tỷ, tăng trưởng dài hạn 5%, chi phí vốn chủ 13,8%, doanh nghiệp có 200 triệu cổ phần. Tính giá trị vốn chủ sở hữu và giá mỗi cổ phần.

**Đáp** *(39.4s · function gọi: load_knowledge_reference)*:




### A5 — Dupont

**Hỏi:** Lợi nhuận sau thuế 300 tỷ, doanh thu 2.500 tỷ, tổng tài sản 4.000 tỷ, vốn chủ sở hữu 1.500 tỷ. Tính ROE theo Dupont và tách rõ ba thành phần.

**Đáp** *(24.5s · function gọi: không)*:

Tách ba thành phần theo DuPont 3 yếu tố:

**ROE = Biên lợi nhuận ròng × Vòng quay tài sản × Đòn bẩy tài chính**

Tính từng mảnh:

- **Biên lợi nhuận ròng (NPM)** = LNST / Doanh thu = 300 / 2.500 = **12%**
- **Vòng quay tài sản (AT)** = Doanh thu / Tổng tài sản = 2.500 / 4.000 = **0,625 vòng**
- **Đòn bẩy tài chính (EM)** = Tổng tài sản / Vốn chủ sở hữu = 4.000 / 1.500 = **2,67 lần**

ROE = 12% × 0,625 × 2,67 = **20%** — kiểm tra nhanh: 300 / 1.500 = 20%, khớp.

**Đọc từng thành phần:**

Biên ròng 12% là mức trung bình khá — không thuộc nhóm biên cao kiểu tiêu dùng hay dược phẩm, cũng không mỏng như vận tải hay xây lắp. Vòng quay tài sản chỉ 0,625 vòng — tức một đồng tài sản chỉ tạo ra 0,625 đồng doanh thu — đây là dấu hiệu khá rõ của ngành tài sản nặng, kiểu sản xuất, bất động sản hay điện. Đòn bẩy 2,67 lần nghĩa là nợ gấp 1,67 lần vốn chủ, mức vừa phải, không phải dạng vay quá đậm.

ROE 20% trông hấp dẫn, nhưng khi tách ra thì **phần lớn đến từ biên ròng cộng với đòn bẩy, còn vòng quay tài sản là điểm yếu** — tức là chất lượng ROE này khá phụ thuộc vào việc biên có giữ được khi đòn bẩy đã ở mức đáng kể. So với một doanh nghiệp cùng ROE 20% mà vòng quay tài sản 1,5 vòng thì loại này khoẻ hơn nhiều, vì không cần dựa vào đòn bẩy.

*(Nếu muốn tách sâu thêm thành DuPont 5 yếu tố — chẻ biên ròng ra tax burden và interest burden — thì cần thêm số liệu thuế và lãi vay, bạn đưa thêm là tính tiếp được.)*

*Đây là phép tính tài chính để bạn đối chiếu, không phải khuyến nghị đầu tư.*


### A6 — EPS pha loãng

**Hỏi:** Lợi nhuận sau thuế 480 tỷ, 240 triệu cổ phần lưu hành, giá thị trường 30.000 đồng. Tính EPS và P/E. Sau đó doanh nghiệp phát hành thêm 60 triệu cổ phần để tăng vốn, lợi nhuận không đổi — EPS và P/E mới là bao nhiêu (giá giữ nguyên)?

**Đáp** *(52.9s · function gọi: load_knowledge_reference)*:

Trước hết nói rõ: cả bốn con số bạn đưa — 480 tỷ lợi nhuận, 240 triệu cp, 30.000 đồng, 60 triệu cp phát hành thêm — đều là **giả định** của bạn, không phải tôi tra được từ doanh nghiệp nào. Tôi tính trên đúng bộ số đó, kết quả phụ thuộc hoàn toàn vào bộ số này — đổi một con số thì bốn đáp số dưới đây đổi theo.

**Trước phát hành thêm:**

- Lợi nhuận sau thuế 480 tỷ chia cho 240 triệu cp → **EPS = 2.000 đ/cp**.
- Giá 30.000 chia cho EPS 2.000 → **P/E = 15 lần**.

**Sau phát hành thêm 60 triệu cp** (tổng cộng 300 triệu cp, lợi nhuận giữ nguyên 480 tỷ, giá giữ nguyên 30.000):

- EPS mới = 480 tỷ / 300 triệu = **1.600 đ/cp** — giảm 20% so với cũ, dù bản thân lợi nhuận không đổi một đồng.
- P/E mới = 30.000 / 1.600 = **18,75 lần** — tăng 25% so với cũ, dù giá thị trường không đổi.

**Ý nghĩa thực tế.** Đây là hiện tượng **pha loãng**: cùng một lợi nhuận, chia cho nhiều cổ phần hơn thì phần mỗi người nhận tự nhiên giảm. P/E tăng không phải vì cổ phiếu đắt lên, mà vì **mẫu số EPS teo đi** — cái nhìn bề ngoài thì giá không động, nhưng giá trị trên mỗi cổ phần đã bị pha loãng thật. Đó cũng là lý do khi so sánh hai giai đoạn trước–sau tăng vốn, **P/E mới cao hơn không có nghĩa cổ phiếu đắt hơn**, và P/E cũ thấp hơn cũng không có nghĩa trước đó nó rẻ hơn — hai con số đo trên hai cái phân số khác nhau về cổ phần lưu hành.

**Điều kiện làm thay đổi kết luận.** Bài toán này giả định giá giữ nguyên 30.000 — trên thực tế khi doanh nghiệp phát hành thêm, giá thường tự điều chỉnh xuống (vì giá trị phải phân bổ cho nhiều cp hơn, và giá phát hành thường thấp hơn giá thị trường). Nếu giá sau phát hành điều chỉnh về đúng tỷ lệ pha loãng — tức còn khoảng 24.000 (30.000 × 240/300) — thì P/E mới sẽ trở lại 15 lần, EPS mới vẫn 1.600. Bài học rút ra: **EPS phải nhìn cùng mẫu số cổ phần, P/E qua hai giai đoạn tăng vốn thì phải quy đổi về cùng cơ sở mới so sánh được** — đây là lý do thực hành người ta hay tính trên tổng vốn hoá thay vì EPS khi doanh nghiệp liên tục phát hành.

*Đây là góc nhìn phương pháp để bạn tự đối chiếu, không phải khuyến nghị đầu tư.*


### A2b — FCFE (chạy lại sau khi nâng max_tokens)

**Hỏi:** Cùng doanh nghiệp đó: lợi nhuận sau thuế 520 tỷ, khấu hao 200 tỷ, đầu tư vốn 250 tỷ, đầu tư vốn lưu động mới 90 tỷ, nợ dài hạn mới 80 tỷ. Tính FCFE.

**Đáp** *(29.4s · function gọi: load_knowledge_reference)*:

FCFE = **460 tỷ**, tính trên đúng 5 số bạn vừa cung cấp, không thêm bất kỳ số nào.

Công thức xuất phát từ bản chất dòng tiền, không phải từ dấu cộng trừ: lợi nhuận sau thuế và vay nợ mới là tiền vào, đầu tư vốn và đầu tư vốn lưu động mới là tiền ra, khấu hao là chi phí không xài tiền nên được cộng back. Theo đúng logic đó: **520 + 200 − 250 − 90 + 80 = 460 tỷ**. Năm đầu vào đều là số thật từ phía bạn, tôi không tự tra thêm cũng không tự bịa.

Con số này là tử số cho bước kế tiếp — chiết khấu nó về hiện tại bằng chi phí vốn chủ sở hữu (tính qua CAPM) sẽ ra thẳng giá trị cổ đông, **không cần trừ nợ** vì phần nợ đã được tính sẵn vào FCFE rồi. Điều kiện quan trọng phải giữ khi dùng: chiết khấu bằng chi phí vốn chủ, không nhầm sang WACC — nhầm chỗ này là trừ nợ hai lần, kết quả lệch hẳn. Và phải nhớ mẫu số nhạy hơn tử số rất nhiều: lãi suất dịch một điểm phần trăm, giá trị cổ đông thay đổi mạnh trong khi FCFE vẫn là 460 — đừng vì con số này "có vẻ ổn" mà bỏ qua việc kiểm tra lại rE.

*Đây là góc nhìn phương pháp để bạn tự đối chiếu, không phải khuyến nghị đầu tư.*


### A4b — Gordon (chạy lại)

**Hỏi:** Lấy FCFE 460 tỷ, tăng trưởng dài hạn 5%, chi phí vốn chủ 13,8%, doanh nghiệp có 200 triệu cổ phần. Tính giá trị vốn chủ sở hữu và giá mỗi cổ phần.

**Đáp** *(17.1s · function gọi: không)*:

Đây là mô hình **FCFE Gordon Growth** — định giá vốn chủ sở hữu theo dòng tiền vốn chủ tăng trưởng đều vĩnh viễn.

## Công thức

$$\text{Equity Value} = \frac{FCFE_0 \times (1+g)}{K_e - g}$$

## Tính

**Bước 1 — FCFE năm tiếp theo:**
$$FCFE_1 = 460 \times (1 + 5\%) = 483 \text{ tỷ}$$

**Bước 2 — Equity Value:**
$$\text{Equity} = \frac{483}{13{,}8\% - 5\%} = \frac{483}{8{,}8\%} \approx 5.488,6 \text{ tỷ}$$

**Bước 3 — Giá mỗi cổ phần:**
$$\text{P} = \frac{5.488,6 \text{ tỷ}}{200 \text{ triệu}} \approx 27.443 \text{ đồng/cp}$$

## Kết quả

| | |
|---|---|
| Giá trị vốn chủ sở hữu | **≈ 5.489 tỷ VND** |
| Giá mỗi cổ phần | **≈ 27.443 VND** |

## Hai điều kiện để con số này có ý nghĩa

1. **FCFE phải ổn định và tăng trưởng đều 5% vĩnh viễn** — đây là giả định nặng nhất. Doanh nghiệp chu kỳ (thép, hóa chất, bất động sản) khó đáp ứng; chỉ phù hợp với doanh nghiệp trưởng thành, dòng tiền đều. Nếu FCFE 460 tỷ là năm đỉnh chu kỳ thì đầu vào đã sai, đầu ra sai theo.

2. **Spread Ke − g = 8,8%** phải đủ rộng để mô hình không nhạy. Lấy Ke = 13,8% ± 1% thì giá dao động khoảng 23.500–32.500 đồng — biên rộng, nên kết luận "đắt/rẻ" phải kèm biên an toàn, đừng lấy đúng 27.443 mà phán.

Nếu bạn đang định giá một mã cụ thể, đưa thêm P/E ngành hoặc EV/EBITDA để đối chiếu — một phép tính thôi thì chưa đủ kết luận.

*Đây là góc nhìn phương pháp để bạn tự đối chiếu, không phải khuyến nghị đầu tư.*


### B4b — CPI (chạy lại sau khi thêm luật công cụ)

**Hỏi:** CPI Việt Nam tháng 8/2026 là bao nhiêu?

**Đáp** *(31.3s · function gọi: get_macro_series)*:

CPI tháng 8 vừa công bố ở mức **4,45% so với cùng kỳ**, tăng nhẹ so với 4,39% của tháng 7 — tức là lạm phát chưa hạ nhiệt mà đang nhích lên, dù mức tăng không đột biến.

Đặt vào khung chu kỳ thì đây là tín hiệu cần cảnh giác chứ không phải tin xấu. Lạm phát là cái vật cản buộc người lái đổi hướng — NHNN muốn nới tiền tệ thêm thì trước hết phải nhìn xem cái vật cản này đang cao hay thấp, và hiện nó đang cao hơn tháng trước. Dư địa hạ lãi suất tiếp vì thế thu hẹp lại, chứ chưa phải đóng hẳn.

Với chứng khoán, cái đáng quan tâm không phải con số 4,45% nằm ở đâu mà là **xu hướng của nó**: nếu tháng 9 tiếp tục lên 4,5% trở lên thì mọi kỳ vọng "còn nới được thêm" phải bỏ, nhóm ngân hàng và đòn bẩy tài chính cao sẽ mất đi một chân đế; còn nếu quay đầu giảm thì kỳ vọng cũ lại được cứu. Điều kiện làm tôi đổi hoàn toàn quan điểm: CPI vượt 5% hai tháng liên tiếp thì lúc đó không còn là "phanh" nữa mà là "đã đổi hướng".

*Đây là góc nhìn phương pháp để bạn tự đối chiếu, không phải khuyến nghị đầu tư.*


### B9b — đếm tin (chạy lại sau khi nâng max_tokens)

**Hỏi:** Có bao nhiêu bài đăng trong tháng 8/2026 nhắc đúng cụm "lãi suất điều hành"?

**Đáp** *(40.7s · function gọi: get_news)*:

23 bài (số tra được từ kho tin tức, tìm theo đúng cụm "lãi suất điều hành" trong tháng 8/2026 — không phải mọi bài nhắc chuyện lãi suất nói chung, mà là bài có chính cụm này trong nội dung).

Nhìn qua 23 bài thì chủ đề tập trung vào ba luồng rõ rệt: chỉ đạo của Thủ tướng về điều hành linh hoạt và giảm thực chất lãi suất cho vay (cụm tin giữa tháng, xoay quanh Thông báo 428/TB-VPCP), hướng đi của Fed mà KIS Research nhận định có thể tăng thêm 0,25% trong ba cuộc họp còn lại của năm, và phản ứng của dòng tiền chứng khoán — bài "Hai trợ lực lớn cho thị trường chứng khoán Việt Nam cuối năm" ngày 27/8 là nối thẳng chính sách vào cổ phiếu rõ nhất.

Mật độ 23 bài trong một tháng là dày, và nó nói lên hai thứ cùng lúc. Một là lãi suất điều hành thật sự là biến số trung tâm của tháng 8, không phải chuyện phụ — đúng vai "phanh" của tỷ giá và "vật cản" buộc chính sách chọn hướng mà tôi vẫn nhắc. Hai là kỳ vọng đã phản ánh vào giá khá đầy đủ — khi một chủ đề xuất hiện đặc như vậy thì phần lớn kịch bản đã nằm trong giá rồi, tin cùng chủ đề ra sau sẽ khó tạo bất ngờ. Nếu bạn đang dùng tần suất tin làm tín hiệu để gom thêm vào nhóm ngân hàng hay nhóm đòn bẩy tài chính, đây là chỗ phải cẩn thận: **tin tốt nhiều cộng giá đã chạy một đoạn là dấu hiệu nguy hiểm**, và nhóm ngân hàng từ đầu năm đến giờ vốn đã là dòng tiền dẫn dắt chạy quá lâu. Điều kiện đổi ý cho cách đọc này: nếu NHNN thật sự hạ lãi suất điều hành bằng quyết định chính thức — chứ không phải chỉ "linh hoạt" như ngôn ngữ chỉ đạo — hoặc Fed đảo hướng rõ rệt, thì con số 23 bài này sẽ đọc khác hẳn, lúc đó nó không còn là kỳ vọng đã nằm trong giá mà là xác nhận chính sách thật.

*Đây là góc nhìn phương pháp để bạn tự đối chiếu, không phải khuyến nghị đầu tư.*
