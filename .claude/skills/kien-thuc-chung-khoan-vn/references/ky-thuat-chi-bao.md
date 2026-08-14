# Kỹ thuật: chỉ báo, mẫu hình và ba lý thuyết kinh điển

File này trả lời ba câu: dùng chỉ báo kỹ thuật thế nào cho đúng, đọc mẫu hình giá ra sao, ba lý thuyết kinh điển nói được gì và giới hạn ở đâu. Kết thúc bằng quy trình sáu bước phân tích kỹ thuật kèm một ví dụ chạy đủ đầu-cuối.

## Mục lục

- [Hai nhóm chỉ số và ba tác dụng](#hai-nhom-chi-so)
- [Nhóm trung bình động](#nhom-trung-binh-dong)
- [Nhóm sức mạnh xu hướng](#nhom-suc-manh-xu-huong)
- [Phân kỳ và điểm vào ra](#phan-ky-va-diem-vao-ra)
- [Tham số và khung thời gian](#tham-so-va-khung-thoi-gian)
- [Mẫu hình giá: bản chất, giới hạn, bốn yếu tố](#mau-hinh-gia)
- [Bảng mẫu hình](#bang-mau-hinh)
- [Khoảng trống giá, đột phá, ba kiểu mua](#khoang-trong-gia)
- [Ba lý thuyết kinh điển](#ba-ly-thuyet)
- [Sáu bước phân tích kỹ thuật](#sau-buoc)
- [Ví dụ chạy đủ sáu bước](#vi-du-sau-buoc)

---

## Hai nhóm chỉ số

Hàng nghìn chỉ số quy về **hai nhóm**, phân biệt bằng mắt không cần đọc công thức:

| Nhóm | Ví dụ | Vẽ ở đâu | Hợp cảnh nào | Vai trò |
|---|---|---|---|---|
| **Trung bình động** | MA, Bollinger Band, Ichimoku | Chung khung với đồ thị giá | Thị trường **có xu hướng** rõ | Kháng cự/hỗ trợ động |
| **Sức mạnh xu hướng** (oscillator, momentum) | RSI, CCI, Stochastic, Money Flow Index, Chaikin Money Flow | Khung riêng tách khỏi giá | Thị trường **sideways** | Đo tương quan lực mua – lực bán |

**MACD là chỉ số lưỡng tính** — vừa là hiệu hai trung bình động, vừa đọc được như momentum.

Bốn đặc điểm chung của mọi chỉ số:

- **Tất cả đều trễ.** Bản chất chỉ là công thức từ giá và lượng quá khứ; dự báo là suy từ khuôn mẫu, không phải nhìn thấy tương lai.
- **Đổi tham số là tạo ra một chỉ số mới.** RSI 14 và RSI 20 là hai chỉ số khác nhau. Không có bộ tham số đúng cho mọi cổ phiếu — phải chỉnh sao cho đúng trong quá khứ của chính mã đó rồi mới hy vọng đúng ở tương lai. Không rõ thì dùng tham số mặc định, vì đông người dùng thì tín hiệu tự ứng nghiệm cao hơn.
- **Không dùng một mình.** Phân tích kỹ thuật giả định nền vĩ mô không đổi, nên chỉ đúng trong khung ngắn khi tâm lý chi phối.
- **Thành thạo ít hơn là biết nhiều.** Mỗi nhóm 2–3 chỉ số là đủ; RSI và CCI bản chất giống nhau, chỉ chọn một. Chỉ số trông phức tạp cũng chỉ là các đường trung bình cắt nhau khoác vỏ khác.

**Ba tác dụng, xếp theo độ tin cậy giảm dần:** (1) **cảnh báo** — sắp xảy ra, mọi chỉ số đều dùng được ở mức này và nên dừng ở mức này; (2) **xác nhận** — đã xảy ra rồi, chỉ đáng tin khi xu hướng thật lớn, thường gắn với thay đổi chính sách tiền tệ, rủi ro là xác nhận xong thì thị trường quay sang sideways; (3) **dự đoán** — cấp thấp nhất, vì cùng một chỉ số đổi tham số đã cho kết quả khác. Chuỗi ba cấp trên một tình huống: giá đang tiến gần kháng cự → cảnh báo; giá đã vào vùng kháng cự → xác nhận; suy ra hướng đi tiếp → dự đoán.

Ba câu hỏi cơ bản mỗi khi mở một chỉ số lên: chỉ số nói gì về tương quan mua–bán và hướng xu hướng; chỉ số đang ở vùng quá mua, quá bán hay bình thường; sức mạnh xu hướng và sức mạnh giá có đồng điệu không hay đang phân kỳ.

---

## Nhóm trung bình động

**Đường MA.** `MA(n) = trung bình cộng giá đóng cửa của n phiên gần nhất`; mỗi phiên mới thêm vào thì bỏ phiên cũ nhất. Dùng trung bình đơn giản, không cần bản trọng số hay làm mượt. Ba cách dùng: **như kháng cự/hỗ trợ động** — xu thế tăng thì mỗi lần giá chạm MA rồi bật là điểm mua, xu thế giảm thì đảo ngược vì lúc đó MA là kháng cự; **theo điểm cắt** — giá cắt lên MA ngắn hạn là tín hiệu mua ngắn, giá cắt lên MA trung hạn xác nhận xu thế trung hạn tăng, **MA50 cắt lên MA200 gọi là Golden Cross** còn cắt xuống hàm ý chu kỳ giảm và thường kéo dài (nhược điểm: chờ được điểm cắt thì giá đã đi trước một đoạn); và **chỉnh tham số** cho hợp cổ phiếu, hợp khung thời gian.

Hai cách dùng hữu ích hơn chờ cắt: **lấy khoảng cách giá so với MA trong quá khứ làm "cỡ"** để ước lượng biên độ dao động hiện tại; và theo dõi lúc **giá nằm dưới MA rồi uốn lên** — đó đã là cảnh báo, không cần đợi cắt. Khi thị trường sideways, MA cắt lên cắt xuống liên tục, gần như vô dụng. Việc MA xác nhận xu thế dài hạn chỉ đáng tin khi nền vĩ mô đã xác nhận trước đó, chứ không phải cứ thấy đường ngắn cắt đường dài là kết luận chu kỳ mới.

**MACD.** `MACD = MA nhanh − MA chậm` (mặc định phổ biến 12 và 26 phiên); đường tín hiệu là MA 9 phiên của chính MACD; **đồ thị cột chính là khoảng cách giữa hai đường**, nên khi hai đường cắt nhau thì cột bằng 0. Đường nhanh cắt lên đường chậm là tín hiệu mua, cắt xuống là tín hiệu bán. Tín hiệu này trễ; để cảnh báo sớm hơn thì nhìn **khoảng cách hai đường thu hẹp dần** rồi mới cắt.

**Bollinger Band.** Đường giữa là MA20; hai dải là `MA20 ± 2 × độ lệch chuẩn của 20 phiên gần nhất`. Tham số 20 và 2 xuất phát từ quan sát rằng phần lớn cổ phiếu dao động trong khoảng 2 lần độ lệch chuẩn. Cách đọc: **dải rộng ra** = biến động lớn, xu hướng mạnh nhưng kém chắc chắn; **dải hẹp lại** = giá ít biến động, thường báo hiệu một biến cố sắp xảy ra nhưng không cho biết hướng (kinh nghiệm: trước đó giảm thì biến cố thường là tăng và ngược lại). Dùng **dải trên như kháng cự, dải dưới như hỗ trợ** — giá ra khỏi dải thì xu hướng là quay vào lại dải, không có nghĩa phải đảo chiều ngay. Giá **bám sát dải trên và vượt ra** phản ánh xu thế tăng rất mạnh, đừng bán vội; chỉ khi giá **quay lại vào trong** dải mới là dấu hiệu xu thế yếu đi.

**Ichimoku.** Năm đường, trông phức tạp nhưng bản chất vẫn là các đường trung bình cắt lên cắt xuống. Cách dùng phổ biến: giá vượt lên trên đám mây là điểm mua, nằm dưới là giảm, nằm trong là sideways; điểm cắt càng xa đám mây thì xu thế càng mạnh. Không cần thiết phải dùng — giữ ở đây chỉ để thấy công cụ trông chuyên nghiệp cũng không nói gì mới hơn MA.

---

## Nhóm sức mạnh xu hướng

| Chỉ số | Công thức | Ngưỡng quy ước |
|---|---|---|
| **RSI(n)** | `RSI = 100 − 100/(1+RS)`, với `RS = trung bình mức tăng / trung bình mức giảm` trong n phiên (mặc định 14) | 70 quá mua, 30 quá bán |
| **CCI(n)** | Độ lệch của giá điển hình `TP = (cao + thấp + đóng cửa)/3` so với trung bình TP n phiên, chia cho độ lệch tuyệt đối trung bình | ±100 |
| **Stochastic** | Vị trí giá đóng cửa trong biên độ cao–thấp của n phiên; gồm đường nhanh và đường chậm | 70/30 |
| **Money Flow Index (14)** | Mỗi phiên tính `TP × khối lượng`; phiên tăng là tiền vào, phiên giảm là tiền ra; cộng dồn 14 phiên rồi lấy `MFI = 100 × tiền vào / (tiền vào + tiền ra)` | Như RSI |
| **Chaikin Money Flow** | Tính tỷ trọng tiền vào/ra **trong cùng một phiên**, nên phản ánh xu hướng tích lũy tiền đúng hơn MFI | Đọc xu hướng, không đọc từng phiên |

**Ngưỡng quá mua/quá bán không cố định.** Nó phụ thuộc biên độ dao động giá của chính mã đó trong giai đoạn quan sát. Một mã chỉ dao động 1–2%/phiên mà chỉ số rơi về 20 rồi vọt lên 80 là cảnh báo sớm; cùng mức 20–80 trên mã dao động 10–20% thì ý nghĩa hoàn toàn khác. **Nhìn biên độ giá trước, nhìn ngưỡng sau.**

Ba cách dùng: (1) **hướng đi và điểm uốn của chính chỉ số** — chờ chỉ số uốn trong vùng quá bán/quá mua, dùng hai chỉ số cùng lúc để tăng độ tin cậy, chỉ số hai đường thì dùng điểm cắt; (2) **vùng ngưỡng như cân tâm lý** — mọi nguyên tắc kỹ thuật dùng cho giá đều áp được cho chính đường chỉ số, vì chỉ số cũng có kháng cự, hỗ trợ và đường xu hướng của nó, và chỉ số breakout khỏi đường xu hướng giảm của chính nó thì giá cũng có thể breakout; (3) **phân kỳ**.

**Nguyên tắc ủng hộ xu hướng chính** — không dùng ngưỡng máy móc hai chiều như nhau:

| Xu thế lớn | Chỉ số vào vùng quá bán | Chỉ số vào vùng quá mua |
|---|---|---|
| **Tăng** | Tác dụng mạnh → nghĩ ngay tới mua sớm | Thận trọng, đừng bán vội, có thể còn tăng tiếp |
| **Giảm** | Thận trọng, từ từ mà mua, đừng bắt đáy | Tác dụng mạnh → bán nhanh |

Cách dùng chặt hơn: coi mức chỉ số như kháng cự/hỗ trợ. Vào vùng quá mua mà lực mua **chưa đạt mức lớn nhất từng xảy ra** trên chính mã đó thì còn dư địa — đợi tới mức đó rồi bán chắc hơn. Chiều ngược lại tương tự với vùng đã từng bán mạnh nhất.

---

## Phân kỳ và điểm vào ra

**Phân kỳ** là khi giá và chỉ số không cùng hướng. Giá tăng thì so đỉnh, giá giảm thì so đáy.

| Loại | Dấu hiệu | Bối cảnh | Hàm ý |
|---|---|---|---|
| **Âm thường** | Đỉnh giá sau cao hơn, đỉnh chỉ số sau thấp hơn | Xu thế tăng | Đảo chiều — tăng khó tiếp diễn |
| **Âm ẩn** | Đỉnh giá sau thấp hơn, đỉnh chỉ số sau cao hơn | Xu thế giảm | Tiếp diễn — đoạn tới còn giảm |
| **Dương thường** | Đáy giá sau thấp hơn, đáy chỉ số sau cao hơn | Xu thế giảm | Đảo chiều — giảm khó tiếp diễn |
| **Dương ẩn** | Đáy giá sau cao hơn, đáy chỉ số sau thấp hơn | Xu thế tăng | Tiếp diễn — xu thế tăng còn nguyên |

Không cần thuộc bốn tên: **cứ gặp phân kỳ thì đoán rằng xu thế hiện tại đang chững lại**, bối cảnh xu thế lớn sẽ tự cho biết đó là loại thường hay ẩn. Giới hạn: phân kỳ không đảm bảo giá phải giảm mạnh hay tăng mạnh ngay, nó chỉ báo xu thế đang chững; nó **tăng độ tin cậy** của tín hiệu chứ không phải điều kiện bắt buộc để ra quyết định. Bản chất vẫn là cung cầu: bán mạnh mà giá không xuống thì giá sẽ lên, mua mạnh mà giá không lên thì giá sẽ xuống. **Hai đáy gần nhau cho phân kỳ đáng tin hơn hai đáy xa nhau**, vì đáy xa có thể nằm ở môi trường chính sách đã khác hẳn.

Điểm vào và điểm ra, mỗi bên bốn điều kiện — càng đủ càng chắc:

- **Điểm vào tốt:** giá ngập ngừng không giảm nữa; lượng thấp và không giảm nữa, có dấu hiệu tăng lại; đang ở vùng hỗ trợ hoặc đường xu hướng giảm quan trọng; kèm phân kỳ dương.
- **Điểm ra (hoặc ít nhất là không vào):** giá ngập ngừng không tăng nữa; lượng ở mức cao hoặc tăng mạnh; đang ở vùng kháng cự hoặc đường xu hướng quan trọng; kèm phân kỳ âm.

Điều kiện quan trọng nhất không phải là kháng cự, mà là **giá không tăng nữa trong khi lượng ở mức cao**. Mục tiêu thực tế của việc đọc tín hiệu này là tránh mua đúng chỗ người khác đang xả, không phải bắt đúng đỉnh đáy.

---

## Tham số và khung thời gian

Bộ tham số MA nên đặt, theo khung ý nghĩa ở thị trường Việt Nam: **MA9** (~2 tuần, quyết định ngắn hạn), **MA20** (1 tháng giao dịch), **MA50** (1 quý), **MA200** (nhiều quý — cặp 50–200 gắn với chu kỳ chính sách tiền tệ). Chỉ số theo năm trở lên khó chính xác, vì tới lúc đó nền vĩ mô đã thay đổi.

Khung quan sát: **khung ngày** là mặc định cho toàn bộ quy trình sáu bước; chuyển sang **khung 30 phút** khi giá đang tiệm cận kháng cự/hỗ trợ và cần bắt thời điểm bật — 30 phút đủ ngắn để bắt nhịp đổi tâm lý, đủ dài để nhà đầu tư bình tĩnh lại sau phản ứng đầu phiên (15 phút hoặc 1 giờ cũng dùng được). **Không dùng Dow và Wyckoff cho khung 30 phút hay 1 tuần** vì hai lý thuyết đó nói về chu kỳ lớn; Elliott thì áp được cho cả khung ngắn lẫn chu kỳ lớn.

**Nguyên tắc "nhịp thứ 2"** ở khung ngắn: tâm lý thường có 3 lần phản ứng trước một vùng quan trọng. Nhịp 1 giá tiến lên rồi lùi — chưa rõ là breakout hay bật lại. Nhịp 2 giá tiến lên lần nữa, tức đã có đàm phán tại vùng đó; hành động ở nhịp này an toàn nhất.

---

## Mẫu hình giá

**Bản chất:** mẫu hình phản ánh **sự lưỡng lự giữa bên mua và bên bán** — thị trường chưa quyết định đi hướng nào. Thống kê cho thấy đa số mẫu hình nghiêng về một hướng với xác suất khoảng **60–80%**, tức 20–40% còn lại vẫn sai. Không bao giờ đạt 100%.

**Giới hạn — đây là phần hạ vai trò nhất trong bộ công cụ kỹ thuật:** mẫu hình được thống kê từ thị trường phát triển, cho giao dịch ngắn hạn, với giả định nền tảng cơ bản không đổi và tâm lý là yếu tố quyết định; ở thị trường đang phát triển, thông tin không phản ánh đầy đủ và tức thời vào giá và khối lượng nên độ tin cậy thấp hơn. Thêm hai điểm: **cái gì dễ nhìn mới đáng tin** — kháng cự/hỗ trợ nằm ngang ai cũng thấy, đường xu hướng chéo mỗi người vẽ một kiểu, nên đột phá ngưỡng ngang đáng tin hơn đột phá đường chéo; và **mọi mẫu hình đều là một dạng kháng cự hoặc hỗ trợ** — hai đỉnh và vai đầu vai là chuyện kháng cự, hai đáy và vai đầu vai ngược là chuyện hỗ trợ, kháng cự bị test ba mươi lần thì vẫn là kháng cự dù có tên gọi gì. Kết luận: **mẫu hình chỉ bổ trợ thông tin**, không thay thế bối cảnh thị trường chung và bối cảnh vĩ mô, không phải tín hiệu chắc chắn.

**Nguyên tắc sử dụng.** **Đừng cố ép để vẽ ra mẫu hình** — cứ nhìn kháng cự và hỗ trợ, xem hai đường co hẹp lại hay mở rộng ra, kết hợp khối lượng và phân tích cung cầu giá lượng. **Cách nhớ thay cho thuộc tên:** mẫu hình hướng lên → đảo chiều đi xuống, hướng xuống → đảo chiều đi lên, ngang → tiếp diễn theo hướng trước đó. **Mẫu hình đẹp cần xu hướng trước đó rõ ràng** (tăng rõ hoặc giảm rõ) và vùng dao động quan sát được cũng phải rõ. **Mỗi cổ phiếu một cách đánh riêng:** mã đã từng có mẫu hình nào trong quá khứ thì khả năng lặp lại mẫu hình tương tự là cao.

**Bốn yếu tố ảnh hưởng độ tin cậy** — kiểm đủ bốn trước khi tin một mẫu hình:

1. **Hướng của xu hướng trước đó.** Cùng một mẫu hình tăng giá, độ tin cậy khác nhau tùy trước đó giá đang tăng hay đang giảm.
2. **Số lần mẫu hình đã xuất hiện trên chính mã đó.** Lần đầu tin cậy cao nhất, lần thứ hai giảm, từ lần thứ ba trở đi rất thấp.
3. **Độ dốc.** Mẫu hình hướng lên mà độ dốc quá nhỏ thì bản chất gần với đi ngang — phải đọc như mẫu hình ngang, đừng áp máy móc.
4. **Điểm chạm.** Mẫu hình vùng giao dịch (hai đường kháng cự và hỗ trợ) cần **ít nhất 2 điểm chạm mỗi đường**, nhưng chạm quá nhiều lần thì độ tin cậy lại giảm. Nên quan sát **từ điểm chạm thứ ba trở lên** vì lần thứ ba thường cho kết quả rõ nhất.

**Đừng lẫn *nhịp* với *điểm chạm*:** nhịp là lần phản ứng tâm lý trước một vùng giá, hành động ở nhịp 2; điểm chạm là số lần giá về đến rồi uốn lại ở một đường của mẫu hình, mẫu hình đáng tin từ lần chạm thứ 3. Hai phép đếm khác nhau, tình cờ dùng chung con số.

Yếu tố 2, 4 và cách đọc hai đỉnh/hai đáy đều xoay quanh **con số 3**. Hệ quả thực dụng: lỡ lần thứ nhất thì còn lần thứ hai, lỡ lần thứ hai thì còn lần thứ ba; rất ít người bắt được đúng đỉnh đúng đáy, sau ba lần mà vẫn không nhận ra thì đó mới là vấn đề.

**Xác định vùng giá mục tiêu** — cách đơn giản hơn Fibonacci: **đo đoạn tăng (hoặc giảm) trước đó rồi áp cho đoạn tiếp theo**. Khi giá vượt kháng cự ở điểm chạm thứ ba, lấy biên độ đoạn tăng gần nhất làm tham chiếu cho lần tăng tới. Đây là phán đoán có căn cứ, không phải dự báo; chỉ dùng được khi có vùng giá tham chiếu rõ ràng, giá vừa đảo chiều mà chưa có tham chiếu thì quay về dùng kháng cự và hỗ trợ.

---

## Bảng mẫu hình

Nhóm dao động (1–8) và nhóm phễu (9–16). Điểm chung: **tất cả đều là biểu hiện của sự lưỡng lự**, chỉ khác nhau ở hướng nào có xác suất cao hơn.

| Nhóm | Dáng | Điều kiện lượng / bối cảnh | Hàm ý |
|---|---|---|---|
| **1–4 Dao động ngang** | Hai đường song song nằm ngang | Lực mua bán cân bằng, không tin mới, lượng đều | **Tiếp diễn** theo hướng trước đó |
| **5–6 Dao động xuống** | Đỉnh sau và đáy sau đều thấp hơn, hai đường song song dốc xuống | Bên bán ưu thế, lượng giảm dần; lượng ngừng giảm ở đoạn sau là dấu hiệu tốt | **Tăng giá.** Tin cậy cao nếu xu hướng trước là tăng, thấp nếu trước đó đã giảm |
| **7–8 Dao động lên** | Đỉnh sau và đáy sau đều cao hơn, hai đường song song dốc lên | Bên mua ưu thế nhưng **lượng tăng dần** | **Giảm giá** — sau 3 lần bên mua không vượt được thì giá thường giảm |
| **9–12 Phễu ngang** | Hai đường hội tụ, trục nằm ngang | Hai bên dò vùng giá hợp lý, dòng tiền yếu, lượng đều | **Tiếp diễn** theo hướng trước đó; hai đường càng hẹp thì khả năng bật càng cao và càng sắp xảy ra |
| **13–14 Phễu xuống** | Hai đường hội tụ, trục dốc xuống | Bên bán bán dứt khoát không đợi giá cũ, bên mua vẫn mua gần giá cũ; lượng thấp hoặc giảm dần | **Tăng giá**, bất kể xu hướng trước đó |
| **15–16 Phễu lên** | Hai đường hội tụ, trục dốc lên | Bên mua mua mạnh không đợi giá cũ, bên bán rất vững, giá lên là bán ngay | **Giảm giá** — vài lần công phá không được thì xu hướng đảo |

Đọc bảng bằng bốn yếu tố độ tin cậy, đừng đọc bằng cột "Hàm ý" một mình. Ví dụ dao động ngang lần thứ ba: nếu có giảm thì chỉ giảm ngắn, và đó là cơ hội mua sớm hơn so với hai lần đầu.

**Tam giác lên và tam giác xuống.** Hai đường trên dưới tạo vùng ngày càng hẹp, lượng đều, không tin nổi bật. **Hai đường hội tụ càng chặt thì hướng đi tiếp càng phụ thuộc hướng trước đó.** Nếu hai đường mở rộng ra thì không còn là tam giác mà là **phễu mở** — hai đường phân kỳ ra thay vì hội tụ. *Phễu mở xuống:* bên mua chờ mua ở giá thấp và cố đẩy giá cao hơn mỗi lần, bên bán đợi gần giá cũ mới bán; lượng giảm dần → **mẫu hình tăng giá**. *Phễu mở lên:* đi sau một xu hướng tăng, lượng tăng dần → **mẫu hình giảm giá**. *Phễu mở ngang:* hướng phụ thuộc hướng trước đó, thường là giai đoạn tin tốt và tin xấu lẫn lộn.

**Hai đỉnh / hai đáy.** Bản chất là dao động ngang cộng hai điều kiện: **khối lượng rất lớn** và **trước đó giá đã tăng rất mạnh** (hai đỉnh) hoặc **giảm rất mạnh** (hai đáy). Hai đỉnh xuất hiện sau giai đoạn tăng mạnh, không có tin tốt mới, khối lượng ở mức cao → mẫu hình giảm điểm. Hai đáy xuất hiện sau giai đoạn giảm mạnh, khối lượng ổn định → mẫu hình tăng điểm. Lần đầu thường **chưa** phải lần kết thúc; thường phải tới lần thứ hai, thứ ba mới quan trọng.

**Vai đầu vai và vai đầu vai ngược.** Cũng là dao động ngang, chỉ thêm những đoạn thái quá rồi mới bật lên hoặc rơi xuống. **Phần đầu (head) phản ánh một nỗ lực bất thành của bên mua**, khối lượng lúc đó thường rất cao; ghép với hai vai thành mẫu hình giảm điểm, chiều ngược lại cho vai đầu vai ngược. Không cần vẽ chính xác từng đỉnh — có thể coi **toàn bộ khu vực là một vùng dao động ngang ở cuối giai đoạn tăng mạnh, đã dao động vài lần**, cách đọc này đơn giản và cho cùng kết luận. Đây cũng là điểm trùng với Wyckoff.

---

## Khoảng trống giá

Ở thị trường có biên độ trong ngày bị chặn (mức trần theo quy định từng sàn, ở Việt Nam trong khoảng 7–10%), ý nghĩa của khoảng trống bị giới hạn: một nến thân rất dài về bản chất đã gần tương đương một khoảng trống. Bốn loại, phân biệt bằng **hai tiêu chí: khoảng trống rơi vào lần dao động thứ mấy, và đặc điểm khối lượng + thông tin tại đó**:

| Loại | Vị trí trong xu hướng | Khối lượng | Thông tin | Hàm ý |
|---|---|---|---|---|
| **Thường** | Vùng thanh khoản kém, có thể ở hỗ trợ hoặc kháng cự | Hoàn toàn bình thường | Không có tin mới | Chỉ cho thấy nhiều người quan tâm và sợ lỡ. **Sẽ được lấp đầy ngay sau đó** |
| **Đột phá** | Sau một giai đoạn tăng tốt (thường là đoạn tăng đầu tiên), tiếp theo là vùng lưỡng lự | **Tăng mạnh** | **Có tin tốt làm thay đổi nền tảng** | Kỳ vọng giá tiếp tục tăng tốt |
| **Tiếp diễn** | Trước đó có đoạn giảm, giá mới tăng trở lại, thậm chí rất nhẹ — "tăng trong nghi ngờ" | Tăng mạnh | Tin tốt vẫn đang được cân nhắc | Xu hướng mới có thể đang hình thành |
| **Hết hơi** | Sau giai đoạn tăng mạnh kéo dài, qua nhiều lần dao động | **Cực lớn**, không chỉ lớn hơn đoạn trước | Không có gì mới, tâm lý lo ngại bắt đầu xuất hiện | Nỗ lực cuối. Dễ nhầm với tiếp diễn — điểm phân biệt là lượng phải **cực** lớn |

**Giao dịch đột phá.** Đột phá ngược với logic thông thường: gặp kháng cự thì thường rơi, gặp hỗ trợ thì thường bật — đột phá là khi giá xuyên qua, nên khó phán đoán là tiếp diễn hay lần cuối. **Điều kiện chung: cần thời gian, cần khối lượng, cần thông tin.** **Phần lớn đột phá đều hỏng, đặc biệt lần đầu tiên**, nên **"mua sau đột phá" thay vì "mua đột phá"**: đợi giá phá xong rồi quay lại test, không rơi xuống dưới vùng vừa phá thì mới vào — lúc đó kháng cự cũ đã thành hỗ trợ mới. Sáu dấu hiệu để một đột phá có khả năng thành công: (1) **phù hợp xu hướng** — các đường trung bình xác nhận lẫn nhau, thông tin ủng hộ; (2) **khối lượng lớn tại phiên phá**, trước đó lượng càng thấp và vùng dao động càng dài thì càng tốt; (3) **vùng kháng cự bị phá phải là vùng quan trọng**; (4) **khu vực đột phá có biến động mạnh** — nến dài hoặc khoảng trống; (5) **mẫu hình tại đó là mẫu hình tiếp diễn**, không phải đảo chiều; (6) **sau phiên đột phá giá có thể điều chỉnh nhưng không được rơi xuống dưới vùng đột phá**.

**Luôn có giá mục tiêu và giá cắt lỗ trước khi vào:** `tỷ lệ = (giá mục tiêu − giá vào) / (giá vào − mức hỗ trợ gần nhất)`. **Tỷ lệ > 1 mới đáng vào.** Bằng nhau (5 ăn 5 thua) thì không phải giao dịch tốt; nhỏ hơn 1 thì không vào.

**Ba kiểu mua cổ phiếu:**

| Kiểu | Cách làm | Đặc điểm |
|---|---|---|
| **Mua hỗ trợ** | Chia tiền 3 lần: lần 1 khi giá lần đầu điều chỉnh về hỗ trợ, lần 2 khi giá điều chỉnh thêm lần nữa, lần 3 khi giá vượt lên — lúc đó cả vùng đã thành hỗ trợ | Trận dài hơn; kiểu được ưa dùng nhất, hợp thị trường bình thường |
| **Mua đột phá** | Mua ngay tại phiên phá kháng cự hoặc phá đường xu hướng | Nhanh và ngắn; lần đầu thường hỏng. Chỉ dùng khi thị trường thực sự khỏe và **phải có thông tin rất tốt** |
| **Mua theo đà** | Đợi đột phá thành công, chờ giá điều chỉnh (retest) rồi mới vào | Gần với "mua sau đột phá"; thống kê ủng hộ kiểu này hơn mua tại thời điểm phá |

Mua ở hỗ trợ và mua sau breakout của một xu thế giảm về bản chất gần như nhau. Thị trường sideways thì hai chiến thuật hợp lý là mua ở hỗ trợ và mua theo đà — **không mua ngay lúc breakout**.

---

## Ba lý thuyết

Ba lý thuyết này đưa vào để **biết**, không phải để áp dụng máy móc. Điểm chung: tất cả đều quy về **ba trạng thái — quá mua, trung tính, quá bán** — và nói lại bằng ngôn ngữ khác những gì cung cầu, giá lượng, kháng cự hỗ trợ đã nói. Đừng vì chúng nổi tiếng mà cố dùng cho phức tạp.

**Lý thuyết Dow — sáu điểm:** (1) **chỉ số thị trường phản ánh tất cả**, tương ứng lý thuyết thị trường hiệu quả — nhưng ở thị trường đang phát triển mức độ hiệu quả thấp nên phải kết hợp phân tích cơ bản, chỉ dựa vào kỹ thuật thì chỉ nên giao dịch ngắn hạn; (2) **ba cấp độ xu hướng: lớn, trung bình và nhỏ**, và khi xác định một xu hướng thì **các chỉ số phải xác nhận lẫn nhau** — các chỉ số sàn đều tăng, các chỉ số ngành cùng tăng, cả ba bậc dòng tiền dẫn dắt – lan toả – đầu cơ đều tăng (kèm cảnh báo: phần lớn thời điểm khi nhận ra xu hướng thì đã muộn, vì chỉ số chỉ đang xác nhận cái đã xảy ra); (3) **khối lượng phải đi cùng giá** — giá tăng mà lượng không tăng thì xu hướng không khỏe; (4) **thị trường vận động theo ba giai đoạn: tích lũy, tăng trưởng, phân phối**; (5) **ngành dẫn dắt nền kinh tế tăng trước rồi kéo theo các ngành hỗ trợ** — đừng bê nguyên danh sách ngành gốc của Dow, ngành quan trọng của mỗi nền kinh tế trong mỗi thời kỳ là khác nhau, và tiền vào nhóm ít rủi ro trước rồi mới sang nhóm rủi ro cao hơn; (6) **dựa trên xu thế để xác định đang là phân phối hay tích lũy**, thường dùng MA20 / MA50 / MA200 cho ngắn – trung – dài hạn.

*Dùng được gì:* khung ba cấp độ xu hướng, nguyên tắc chỉ số xác nhận lẫn nhau, ba giai đoạn thị trường. *Giới hạn:* nói về chu kỳ lớn, không dùng cho khung 30 phút hay 1 tuần.

**Lý thuyết Wyckoff.** Cũng ba giai đoạn tích lũy – tăng trưởng – phân phối như Dow, nhưng **thiên về giải thích kỹ thuật**, đặc biệt hiện tượng breakout giả. Ba điểm riêng đáng dùng: **trước khi đi theo xu hướng của chu kỳ, bao giờ cũng có một lần breakout hỏng**; nếu đó là **lần thứ 3** trong chu kỳ tăng thì thường là lúc thị trường bắt đầu cảnh giác, và nếu giá đang tạo đỉnh mà có một lần bứt lên trong khi mọi tin tốt đã phản ánh hết thì đó **có thể là lần cuối**; gắn liền với giá và lượng — khối lượng rất lớn rồi xuất hiện nến upthrust thì gần như chắc chắn giá giảm, còn nến rút chân (spring) ở vùng đáy dao động thì thường sẽ tăng. *Giới hạn:* như Dow — chu kỳ lớn, không hợp khung ngắn.

**Lý thuyết sóng Elliott.** Một chu kỳ gồm **5 sóng tăng + 3 sóng giảm A, B, C = 8 sóng**; trong 5 sóng tăng thì 1, 3, 5 là sóng đẩy và 2, 4 là sóng điều chỉnh.

| Sóng | Quy tắc tỷ lệ | Ràng buộc bắt buộc |
|---|---|---|
| 2 | Điều chỉnh 50–61,8% sóng 1 | Không được xuống dưới điểm xuất phát (sóng 0) |
| 3 | Có thể tới 150–161,8% sóng 1 | **Phải là sóng dài nhất**, đỉnh cao hơn đỉnh sóng 1 |
| 4 | Điều chỉnh 38,2–61,8% sóng 3 | Không nên thấp hơn đỉnh sóng 1 |
| 5 | Tăng ít hơn sóng 1 | Đỉnh cao hơn đỉnh sóng 3 |
| A – B – C | A giảm 1/2 đến 2/3 sóng 5; B tăng 50% đến 2/3 sóng A; C giảm mạnh nhất, hơn 100% sóng A | B không được vượt đỉnh sóng 5 (vượt thì phải đếm lại sóng); điểm cuối sóng C vẫn phải cao hơn điểm xuất phát của cả chu kỳ |

Cách nhớ đơn giản hóa: **1/3, 2/3, 1/2, 2/3** thay cho các tỷ lệ Fibonacci chính xác. Vì sao sóng 3 dài nhất: sóng 1 là đoạn tăng trong nghi ngờ, sóng 3 là đoạn tin tưởng hoàn toàn dẫn tới lạc quan, sóng 4 là lạc quan thái quá — Elliott dựa trên ba trạng thái tâm lý cộng nền tảng cơ bản nên sóng 3 buộc phải dài nhất.

*Dùng được gì:* áp được cho cả khung ngắn lẫn chu kỳ lớn, khác Dow và Wyckoff. *Giới hạn nghiêm trọng:* **đếm sóng rất chủ quan** — cùng một đoạn giá, một người đếm 1-2-3-4-5 và kỳ vọng còn giảm tiếp, người kia đếm 1-2-3-4-5-A-B-C và kết luận chu kỳ giảm đã xong, cả hai đều hợp lệ theo nguyên tắc. Nếu dùng thì phải xác định rõ điểm đầu và điểm kết thúc trước, rồi mới áp tỷ lệ.

**Fibonacci** chỉ là công cụ phụ. Muốn biết giá tăng tới đâu sau một đoạn giảm thì vẽ lên chính đoạn giảm đó; các mức 38,2% – 50% – 61,8% – 100% là những vùng dễ ngập ngừng. Nhưng **vùng hỗ trợ/kháng cự có sẵn trước đó quan trọng hơn** — Fibonacci chỉ có ý nghĩa khi gần như không nhìn thấy hỗ trợ nào để tham chiếu.

---

## Sáu bước

Quy trình tổng, chạy trên khung ngày. Đây là bản chi tiết cho người mới; khi đã quen thì không nhất thiết theo đủ các bước. **Phân tích thị trường chung trước, phân tích cổ phiếu sau** — cổ phiếu dù tốt cũng không nằm ngoài quy luật thị trường. Thiếu dữ liệu thì bỏ bước, không đảo thứ tự: **bước 1, 2 và 5 là bắt buộc** — chúng chỉ cần giá và khối lượng, và bước 2 là điều kiện chặn; bước 3, 4, 6 đòi dữ liệu chi tiết hơn, thiếu thì bỏ và hạ độ tin cậy của kết luận.

1. **Xác định xu hướng.** Dùng MA (bộ 20/50/200), đường xu hướng (xu thế giảm nối đỉnh, xu thế tăng nối đáy), và nếu muốn thì Elliott. Nguyên tắc nền: **không cưỡng lại thị trường**. Ba trạng thái và hành động tương ứng — tăng: mua và nắm giữ dài, gia tăng vị thế; giảm: đứng ngoài; sideways: mua bán ngắn hạn, vào nhanh ra nhanh, kết hợp cân lại tỷ trọng.
2. **Kiểm tra kháng cự và hỗ trợ.** Luôn dùng **vùng**, không dùng một con số. Ý nghĩa chính của bước này là tính được tỷ lệ lợi nhuận kỳ vọng trên mức cắt lỗ — **nhỏ hơn hoặc bằng 1 thì không vào lệnh**.
3. **Mẫu hình kỹ thuật.** Nhận diện vùng dao động hoặc kênh, đếm điểm chạm, rồi soi qua bốn yếu tố độ tin cậy.
4. **Chỉ số kỹ thuật.** Một chỉ số momentum (RSI hoặc CCI) cộng một chỉ số dòng tiền — hai vai trò đó mới là cái bắt buộc, chỉ số cụ thể thì dùng bộ nào đang có. Đọc hướng, vùng ngưỡng và phân kỳ; nhớ rằng mọi nguyên tắc kỹ thuật dùng cho giá đều áp được cho chính đường chỉ số.
5. **Phân tích giá và lượng.** Bước quan trọng nhất trong sáu bước. Đặt một đường MA cho khối lượng để biết thế nào là bình thường.
6. **Phân tích mẫu nến tại khu vực hiện tại.** Chỉ đọc nến ở vùng đang đứng, đặt trong bối cảnh kháng cự/hỗ trợ đã xác định ở bước 2.

Sau sáu bước, nếu các tín hiệu mâu thuẫn nhau thì **cứ để thị trường chạy** — đừng lấy suy đoán bù vào chỗ thiếu tín hiệu. Khi đã vào lệnh: **mua vì lý do gì thì bán theo đúng lý do đó**; thấy phân tích sai thì đổi ngay, đừng cố bảo vệ quan điểm cũ.

---

## Ví dụ sáu bước

Cổ phiếu **X**, giả định trung tính. Bối cảnh: giá giảm từ 30,0 xuống 18,0 trong bốn tháng, sau đó hồi lên 21,0 là mức hiện tại.

**Bước 1 — xu hướng.** MA20 = 20,4; MA50 = 22,6; MA200 = 25,1. MA50 vẫn dưới MA200 → chu kỳ lớn còn là giảm. Giá 21,0 trên MA20 nhưng dưới MA50 → nhịp hồi mới đủ sức vượt trung bình ngắn hạn. Đường xu hướng giảm nối ba đỉnh 30,0 → 26,0 → 23,5 hiện cắt vùng 21,5, giá chưa phá. *Kết luận trung gian: xu thế lớn giảm, đang ở nhịp hồi ngắn hạn trong xu thế đó; hành động mặc định là mua bán ngắn hạn hoặc đứng ngoài, không phải mua nắm giữ.*

**Bước 2 — kháng cự và hỗ trợ.** Kháng cự vùng **21,5–22,0** (đỉnh gần nhất, kèm khối lượng lớn). Hỗ trợ vùng **18,0–18,5** (đáy gần nhất, giá đã dao động ở đó nhiều phiên). Nếu mua ngay tại 21,0: lợi nhuận kỳ vọng tới kháng cự = 21,5 − 21,0 = 0,5; rủi ro nếu thủng hỗ trợ = 21,0 − 18,3 = 2,7; tỷ lệ = 0,5 / 2,7 ≈ **0,19**. *Kết luận trung gian: 0,19 < 1 → không vào lệnh tại giá hiện tại, bất kể các bước sau nói gì.*

**Bước 3 — mẫu hình.** Bốn tháng qua giá đi trong một kênh **dao động xuống**: ba đỉnh 23,5 → 22,0 → 21,6 và hai đáy 19,0 → 18,0. Theo bảng, dao động xuống là mẫu hình tăng giá. Soi bốn yếu tố: (1) xu hướng trước đó là giảm → độ tin cậy thấp hơn, lực tăng nếu có sẽ nhỏ; (2) đây là lần thứ hai mẫu này xuất hiện trên X trong một năm → giảm một bậc; (3) độ dốc rõ ràng, không phải trường hợp gần ngang; (4) đường trên đã có 3 điểm chạm, đường dưới mới 2. *Kết luận trung gian: mẫu hình nghiêng tăng nhưng yếu; điểm đáng vào là lần chạm thứ ba của đường dưới, tức vùng hỗ trợ, không phải ở đây.*

**Bước 4 — chỉ số.** RSI(14) = 62, CCI(14) = +95 → nửa trên, tiệm cận vùng quá mua nhưng chưa vào. So đỉnh: đỉnh giá gần nhất 21,6 ứng RSI 68, đỉnh hiện tại 21,0 ứng RSI 62 → giá thấp hơn, chỉ số cũng thấp hơn → **đồng điệu, không có phân kỳ**. Biên độ dao động ngày của X khoảng 2–3%, nên RSI 62 chưa phải tín hiệu mạnh. *Kết luận trung gian: không có tín hiệu đảo chiều, xu thế giảm còn nguyên, đây không phải vùng mua theo chỉ số.*

**Bước 5 — giá và lượng.** MA20 của khối lượng = 1,2 triệu cp/phiên. Nhịp hồi từ 18,0 lên 21,0 diễn ra với khối lượng 0,8–1,0 triệu, tức **dưới đường trung bình suốt cả nhịp**. *Kết luận trung gian: hồi trong lượng thấp — bên mua chưa thực sự vào, đây là hồi kỹ thuật chứ không phải đảo chiều xu hướng.*

**Bước 6 — nến tại khu vực hiện tại.** Ba phiên gần nhất thân nến ngắn dần. Phiên gần nhất là nến đỏ thân ngắn có bóng trên dài, đỉnh bóng chạm 21,5 rồi bị đẩy về 21,0 — nỗ lực vượt kháng cự bất thành ngay tại vùng đã xác định ở bước 2. *Kết luận trung gian: bên bán đang thắng tại kháng cự.*

**Tổng hợp sáu bước.** Cả sáu bước nói cùng một hướng: đứng ngoài ở vùng giá hiện tại. Kế hoạch — chờ giá về vùng **18,0–18,5** (lần chạm thứ ba của đường dưới) và yêu cầu **ba điều kiện đồng thời**: khối lượng ngừng giảm và có dấu hiệu vượt lên MA20 của lượng; RSI tạo phân kỳ dương (giá tạo đáy thấp hơn 18,0 mà đáy RSI cao hơn); xuất hiện nến rút chân tại vùng đó. Khi đủ ba điều kiện, giả sử vào ở 18,3 với cắt lỗ 17,5 và mục tiêu 21,5: tỷ lệ = (21,5 − 18,3) / (18,3 − 17,5) = 3,2 / 0,8 = **4,0 > 1** → đáng vào. Chia tiền làm 3 lần theo kiểu mua hỗ trợ. Vì xu thế lớn vẫn giảm, đây là vị thế ngắn hạn — vào nhanh ra nhanh, và bán theo đúng lý do đã mua.

---
