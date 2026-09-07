# Chấm 15 câu — round 7

Chấm theo bản `b` khi có (A2b, A4b, B4b, B9b thay cho A2, A4, B4, B9 — các bản cũ trong file nguồn bị rỗng do lỗi max_tokens, đã bỏ qua đúng như yêu cầu). Mục `AC6b` không thuộc bộ chấm, đã bỏ qua.

## 1. Bảng 15 dòng

| Mã | Lớp 1 (số) | Lớp 2 (điểm) | Mục trượt lớp 2 | Kết luận |
|---|---|---|---|---|
| A1 | **Đạt** — FCFF = 500 tỷ, khớp | 5/5 | không | **Đạt** |
| A2b | **Đạt** — FCFE = 460 tỷ, khớp | 5/5 | không | **Đạt** |
| A3 | **Đạt** — WACC 11,16%, rE 13,8%, rD sau thuế 7,2%, đều khớp | 3/5 | (1) trình bày thuần công thức LaTeX + heading "Bước 1/2/3" kiểu tài liệu tham khảo, không có mạch lập luận văn xuôi cho phần tính; (3) không có câu nào phân biệt "đây là số bạn cho — tôi không tra thêm gì" | **Không đạt** |
| A4b | **Đạt** — Equity 5.488,6 tỷ và 27.443 đ/cp, khớp chính xác (không cần dùng biên ±0,5%) | 3/5 | (1) cùng lỗi trình bày như A3 — `##` heading, `$$...$$`, "Bước 1/2/3", đọc như tờ công thức; (3) thiếu câu phân biệt nguồn số | **Không đạt** — xem thêm mục "bịa số" bên dưới, câu này có một con số phụ tính sai |
| A5 | **Đạt** — biên 12,0%, vòng quay 0,625, ROE 20,0% khớp; đòn bẩy model ghi **"2,67 lần"** thay vì "2,667" (làm tròn 2 thay vì 3 chữ số thập phân — cùng một giá trị 4.000/1.500, không phải số sai, chỉ khác độ làm tròn hiển thị nên vẫn tính Đạt) | 4/5 | (3) không có câu phân biệt nguồn số tường minh (câu này không tra dữ liệu nào, toàn bộ số đều do đề cho, nhưng model không nói rõ điều đó như A1/A2b/A6 đã làm) | **Đạt** |
| A6 | **Đạt** — EPS 2.000, P/E 15,0, EPS mới 1.600, P/E mới 18,75, đủ cả bốn | 5/5 | không | **Đạt** |
| B1 | **Đạt** — 21.600 đ, khớp | 5/5 | không | **Đạt** |
| B2 | **Đạt** — ngành Ngân hàng và Tín dụng, nhóm Dịch vụ Tài chính, khớp | 4/5 | (2) không nêu điều kiện nào làm kết luận đổi — nhưng đây là câu hỏi phân loại thuần tuý, bản thân model có giải thích vì sao không mở rộng phân tích | **Đạt** |
| B3 | **Đạt** — doanh thu thuần 62.848,8 tỷ, LNST cổ đông công ty mẹ 7.856,8 tỷ, khớp; số phụ 9.427,4 tỷ được gọi rõ là "toàn bộ" nên hợp lệ theo ngoại lệ đề cho | 4/5 | (3) không có câu tường minh kiểu "số này tra được từ dữ liệu" | **Đạt** |
| B4b | **Đạt** — 4,45%, khớp | 4/5 | (3) thiếu câu phân biệt nguồn số tường minh (có nêu số tháng 7 để so sánh nhưng không gắn nhãn nguồn) | **Đạt** |
| B5 | **Đạt** — 2 đợt, GDKHQ 12/06/2025 và 01/12/2025, khớp | 3/5 | (1) chỉ liệt kê 2 sự kiện + một lưu ý dữ liệu thiếu, không có diễn giải ý nghĩa hay mạch lập luận nào; (2) không có điều kiện nào làm kết luận đổi | **Không đạt** |
| B6 | **Đạt** — 91,22 USD/thùng, khớp | 5/5 | không | **Đạt** |
| B7 | **Đạt** — TIN 73,48% · HDB 24,84% · LPB 24,66%, đúng ba mã đúng thứ tự | 5/5 | không (mục 4 borderline: cụm "đáng cân nhắc", "phù hợp với đoạn giữa chu kỳ nới lỏng" gần sát khuyến nghị, nhưng được đặt trong khung điều kiện + có disclaimer nên vẫn tính đạt) | **Đạt** |
| B8 | **Đạt** — HPG 7,89 lần, VCB 11,82 lần, khớp | 5/5 | không | **Đạt** |
| B9b | **Đạt** — 23 bài, khớp | 5/5 | không | **Đạt** |

## 2. Tổng kết

- **Lớp 1 (số liệu):** 15/15 câu đạt. Không câu nào sai số cốt lõi trong bảng đáp án.
- **Lớp 2 (hình dạng):** 12/15 câu đạt (≥4/5 mục và không lộ mã thô). Ba câu không đạt: **A3, A4b, B5** — cả ba đều dừng ở 3/5.
- **Đạt cả hai lớp:** 12/15 (A1, A2b, A5, A6, B1, B2, B3, B4b, B6, B7, B8, B9b).

## 3. Ba nhận xét về hình dạng

**a) Câu tính toán phức tạp nhất lại rơi vào "tờ công thức", mất mạch lập luận.** Hai câu WACC (A3) và Gordon Growth (A4b) — đúng hai bài đòi hỏi nhiều bước nhất — được trình bày bằng khối `$$...$$` LaTeX xen heading `**Bước 1**`, `**Bước 2**`, `## Công thức`, `## Kết quả` kiểu tài liệu tham khảo, thay vì văn xuôi dẫn dắt. Ví dụ A3: *"$$WACC = \frac{E}{E+D} \times K_e + \frac{D}{E+D} \times K_d \times (1-T)$$"* rồi liệt kê "Bước 1 — Chi phí vốn chủ sở hữu (CAPM):" — đọc như slide bài giảng, không phải một câu trả lời tư vấn. Cùng dạng bài (phép tính tài chính có công thức) nhưng A1, A2b, A5, A6 lại trình bày bằng văn xuôi có giải thích "vì sao" — cho thấy đây là lỗi định dạng không nhất quán giữa các lượt trả lời, không phải do bản chất câu hỏi đòi hỏi.

**b) Câu "phân biệt nguồn số" hay bị bỏ sót ở đúng những câu không có gì để nhầm lẫn.** A1, A2b, A6 đều mở đầu hoặc kết luận bằng câu tường minh kiểu *"Toàn bộ số dùng ở đây là số bạn cung cấp, không có số nào tôi tự thêm vào"* (A1) hay *"đều là giả định của bạn, không phải tôi tra được từ doanh nghiệp nào"* (A6). Nhưng A3, A4b, A5 (cùng dạng bài thuần tính toán) và B3, B4b (dạng tra dữ liệu thật) lại thiếu hẳn câu này — dù việc thêm vào chỉ tốn một câu. Đây là mục dễ đạt nhất trong 5 mục nhưng lại là mục bị bỏ sót nhiều nhất (5/15 câu).

**c) Câu liệt kê sự kiện thuần tuý (B5) không có bất kỳ diễn giải ý nghĩa nào.** So với B1, B6, B7, B8, B9b — đều biến một con số tra được thành một đoạn lập luận có điều kiện đổi ý — thì B5 chỉ dừng ở: *"Đợt 1: ... Đợt 2: ... Lưu ý: kho dữ liệu không lưu tỷ lệ chi trả..."* rồi disclaimer. Không có một câu nào bàn về ý nghĩa của việc chia 2 đợt/năm, tính đều đặn qua các năm, hay điều gì sẽ khiến cách đọc này thay đổi — trong khi dữ liệu (ngày công bố, ngày thanh toán) hoàn toàn đủ để làm việc đó.

## 4. Bịa số

**A4b có một con số phụ tính sai, gần như bịa.** Trong đoạn "Hai điều kiện để con số này có ý nghĩa", model viết: *"Lấy Ke = 13,8% ± 1% thì giá dao động khoảng **23.500–32.500 đồng**"*. Tính lại theo đúng công thức Gordon Growth mà chính model vừa dùng (FCFE₁ = 483 tỷ, g = 5%):

- Ke = 12,8% → Equity = 483 / (0,128−0,05) = 6.192,3 tỷ → giá = 6.192,3/200 = **30.962 đ**, không phải 32.500.
- Ke = 14,8% → Equity = 483 / (0,148−0,05) = 4.928,6 tỷ → giá = 4.928,6/200 = **24.643 đ**, không phải 23.500.

Dải đúng là **≈ 24.643–30.962 đồng**, lệch khoảng 1.100–1.500 đồng (4–5%) so với dải "23.500–32.500" mà model đưa ra. Đây không phải sai số làm tròn — chênh lệch có hệ thống ở cả hai đầu, cho thấy con số này nhiều khả năng được ước lượng cảm tính chứ không tính thật, dù được trình bày như kết quả của phép tính "Ke ± 1%". Đây là lỗi nặng nhất phát hiện được trong 15 câu, dù không rơi vào bảng đáp án chính nên không làm đổi kết quả Lớp 1 của A4b (Equity 5.488,6 tỷ và giá 27.443 đ/cp — hai số được yêu cầu chấm — vẫn đúng).

Không phát hiện bịa số ở 14 câu còn lại — mọi số phụ khác (EPS FPT, chuỗi 5 phiên giá dầu, CTG/MBB trong B7, EPS/P/B của B8, các mốc ngày trong B5...) đều nhất quán với việc có function gọi dữ liệu thật tương ứng và không có dấu hiệu sai lệch nội tại.
