# V4 2022-11 - 07 - Dinh gia thu nhap co tuc - Bai giang

Bài nằm trong học phần phân tích doanh nghiệp và định giá, dạy phương pháp định giá cổ phiếu theo mô hình chiết khấu dòng tiền: lấy dòng tiền mà cổ đông thực sự nhận (cổ tức, hoặc thu nhập thay thế khi cổ tức không đều) rồi chiết khấu về hiện tại theo tỷ suất lợi nhuận yêu cầu. Bài bao gồm các khái niệm nền (dòng tiền, giá trị thời gian của tiền, tỷ lệ chiết khấu), công thức chiết khấu dòng tiền ở dạng tổng quát và dạng tăng trưởng đều, phân tích tác động của độ đều đặn cổ tức, mô hình CAPM để ước lượng tỷ suất lợi nhuận yêu cầu, quy trình bảy bước định giá, và một ví dụ mô phỏng với cổ phiếu QMV. Bài quay ngày 27/05/2024.

## Dòng tiền và giá trị thời gian của tiền

Trong định giá, dòng tiền (cash flow) cần hiểu là dòng tiền mà doanh nghiệp tạo ra cho cổ đông, sau khi trừ các phí tổn cần thiết để phục vụ tăng trưởng (đầu tư vào tài sản lưu động, tài sản cố định). Dòng tiền xuất hiện tại các thời điểm khác nhau trong tương lai - năm 1, năm 2, ..., năm 10, và có thể vĩnh viễn - nên không thể cộng trực tiếp các con số với nhau.

Sở dĩ giá trị của cùng một dòng tiền ở các thời điểm khác nhau lại khác nhau là vì ba yếu tố: lạm phát làm sức mua giảm, rủi ro vì không biết điều gì sẽ xảy ra trong tương lai, và chi phí cơ hội (đáng ra số tiền đó có thể được dùng cho việc khác có lợi hơn). Từ đó dẫn tới khái niệm giá trị thời gian của tiền: tiền ở hiện tại có giá trị hơn cùng số tiền đó ở tương lai.

Để so sánh các dòng tiền ở các thời điểm khác nhau, cần một hệ số quy đổi về cùng một thời điểm hiện tại - đó là tỷ lệ chiết khấu.

Đây chính là điểm khác biệt cơ bản giữa kế toán và tài chính. Kế toán nhìn con số dòng tiền gốc, không quy đổi theo thời gian; tài chính và đầu tư nhìn theo giá trị thời gian. Có những trường hợp về mặt kế toán có lợi nhưng về mặt tài chính lại không có lợi.

## Tỷ lệ chiết khấu và chi phí cơ hội

Tỷ lệ chiết khấu là cái mà nhà đầu tư yêu cầu, tương tự kỳ vọng lợi nhuận. Nếu kỳ vọng lợi nhuận cao thì phải chấp nhận rủi ro cao hơn, và ngược lại.

Cụ thể: chi phí cơ hội là cái mà đáng ra chúng ta nhận được nếu thực hiện một hoạt động khác mà tin chắc sẽ nhận. Khi đầu tư chứng khoán, cơ hội bị mất đi chính là tiền lãi tiết kiệm. Vậy nên tỷ suất lợi nhuận yêu cầu khi đầu tư cổ phiếu chắc chắn phải lớn hơn lãi suất tiết kiệm. Nếu lãi suất tiết kiệm tăng thì tỷ suất lợi nhuận yêu cầu cũng phải tăng tương ứng.

Công thức chung: tỷ lệ chiết khấu (r) = lãi suất tiết kiệm + phần bù rủi ro. Phần bù rủi ro càng lớn thì r càng cao và định giá càng giảm. Nếu đầu tư vào cổ phiếu an toàn thì tỷ suất lợi nhuận yêu cầu sẽ gần với lãi suất tiết kiệm hơn; cổ phiếu rủi ro hơn thì phần bù phải cao hơn, r cao hơn, và định giá thấp xuống.

Khi chiết khấu tất cả dòng tiền tương lai về hiện tại rồi cộng lại, ta có giá trị hợp lý (intrinsic value) của cổ phiếu, doanh nghiệp. Bản chất định giá là vậy.

## Giá trị doanh nghiệp và giá trị cổ phiếu

Cần phân biệt giá trị doanh nghiệp và giá trị cổ phiếu. Giá trị doanh nghiệp là tổng giá trị chiết khấu của các dòng tiền hoạt động trong tương lai, bao gồm cả phần trả cho cổ đông lẫn phần trả cho chủ nợ. Giá trị doanh nghiệp = giá trị nợ + giá trị cổ phiếu. Suy ra giá trị cổ phiếu = giá trị doanh nghiệp - giá trị nợ.

Khi chiết khấu dòng tiền, nếu là dòng tiền cho doanh nghiệp thì gọi là dòng tiền hoạt động; nếu là dòng tiền dành cho cổ đông thì gọi là dòng tiền dành cho cổ đông. Chỉ khi chiết khấu dòng tiền dành cho cổ đông thì mới có giá trị hợp lý của cổ phiếu. Chiết khấu dòng tiền hoạt động rồi lấy kết quả gọi là giá trị cổ đông là sai.

Thầy lưu ý: nhiều người trên diễn đàn hay nói về giá trị doanh nghiệp (doanh nghiệp có tài sản lớn, tiềm năng sinh lời đặc biệt ở lĩnh vực bất động sản), nhưng giá trị doanh nghiệp đã bao gồm cả phần trả nợ, nên không phải cái mà nhà đầu tư cổ phiếu nên nhìn vào. Nhà đầu tư cổ phiếu phải nhìn giá trị dành cho cổ đông.

Cũng cần phân biệt: dòng tiền trong định giá là dòng tiền doanh nghiệp tạo ra cho cổ đông, không phải dòng tiền vào/ra thị trường chứng khoán (cung tiền, nguồn tiền) mà thường được nhắc tới trên truyền thông.

## Công thức chiết khấu dòng tiền và mô hình tăng trưởng đều

Về mặt toán học, chiết khấu dòng tiền rất đơn giản: gọi các dòng tiền tương lai là CF1, CF2, ..., CFn (có thể kéo dài mãi mãi), tỷ lệ chiết khấu là r. Mỗi dòng tiền ở thời điểm t được chia cho (1+r)^t, rồi cộng tất cả lại. Tổng này chính là giá trị hợp lý.

Tuy nhiên, để tính được ta phải dự báo dòng tiền hàng năm, và điều này gần như không thể. Vài năm tới có thể đoán được, nhưng 10 năm hay 50 năm sau thì không. Vì vậy các nhà nghiên cứu đưa ra công thức với giả định đơn giản hơn: các dòng tiền tăng trưởng cố định theo một tỷ lệ g hàng năm. Khi đó công thức biến đổi thành:

V = CF0 x (1+g) / (r - g)

Đây gọi là công thức 2 trong bài. r vừa là tỷ suất chiết khấu vừa là tỷ suất lợi nhuận yêu cầu, g là tốc độ tăng trưởng của dòng tiền. Nếu giả định không có tăng trưởng (g = 0), công thức còn đơn giản hơn: V = CF / r (công thức 3).

Ví dụ: một doanh nghiệp trả cổ tức thường xuyên 10-15% mỗi năm. Lấy 15% tương ứng 1.500 đồng/cp mỗi năm (trên cơ sở giá 10.000 đồng). Áp dụng công thức 3 với r = 15%: V = 1.500 / 0,15 = 10.000 đồng/cp. Ở Việt Nam doanh nghiệp ít trả cổ tức thường xuyên, nhưng về mặt ý nghĩa thì có thể dùng công thức này.

Công thức 2 và 3 làm cho việc tính toán trở nên khả thi: thay vì phải ngồi tính từng dòng tiền qua từng năm, ta chỉ cần dòng tiền đầu, tỷ lệ tăng trưởng và tỷ lệ chiết khấu. Phần toán học dễ, cái khó là hiểu các biến số và đánh giá sự thay đổi của chúng tác động đến định giá như thế nào.

Công thức cổ tức có thể áp dụng cả khi nhà đầu tư không nắm giữ cổ phiếu lâu dài. Vì tại thời điểm PT (giá bán), người mua tiếp theo vẫn phải dùng mô hình cổ tức để định giá PT. Dù là P0, PT hay PT+10 thì cuối cùng người bán vẫn phải định giá - công thức vẫn đúng.

## Độ đều đặn của cổ tức

Có một quan sát quan trọng: doanh nghiệp trả cổ tức càng đều đặn theo một quy luật thì phần bù rủi ro càng thấp, vì khi biết được quy luật trả cổ tức thì rủi ro dòng tiền thấp đi.

Thầy đưa ví dụ hai công ty hoạt động tương đương, kết quả kinh doanh tương đương. Công ty 1 trả cổ tức 10% đều đặn mỗi năm. Công ty 2 có năm trả 10%, có năm trả 20%, có năm không trả. Cả hai đều có cổ tức kỳ vọng 10%, nhưng độ biến động khác nhau - công ty 2 biến động từ 0 đến 20% nên rủi ro dòng tiền cổ tức kỳ vọng lớn hơn. Vì vậy, khi định giá hai công ty tương đương nhau, phần bù rủi ro của công ty 1 thấp hơn, và định giá của công ty 1 phải cao hơn. Yếu tố này được gọi là dividend pattern.

## Cùng một cổ phiếu, hai cách định giá: nhà đầu tư A và B

Thầy lấy ví dụ minh hoạ với cổ phiếu QMV. Công ty có EPS = 10.000 đồng/cp, ROE = 20%/năm, tỷ lệ chi trả cổ tức ổn định ở mức 60% EPS. Từ đó cổ tức hàng năm là 6.000 đồng/cp, phần giữ lại là 4.000 đồng/cp.

Tốc độ tăng trưởng g được tính bằng ROE x tỷ lệ giữ lại = 20% x 40% = 8%.

Giá hiện tại cổ phiếu QMV là 250.000 đồng/cp.

Có hai nhà đầu tư cùng nhìn vào đúng các con số trên. Nhà đầu tư A không hiểu rõ QMV, đánh giá rủi ro cao, đặt tỷ suất lợi nhuận yêu cầu r = 12%. Nhà đầu tư B hiểu rõ hoạt động QMV hơn, đánh giá rủi ro thấp, đặt r = 10%.

Áp dụng công thức 2:
- A: V = 6.000 x 1,08 / (0,12 - 0,08) = 6.480 / 0,04 = 162.000 đồng/cp.
- B: V = 6.000 x 1,08 / (0,10 - 0,08) = 6.480 / 0,02 = 324.000 đồng/cp.

Với giá thị trường 250.000, A thấy giá đắt (giá trị chỉ 162.000) nên không mua, còn B thấy giá rẻ (giá trị lên tới 324.000) nên mua. Điều này giải thích tại sao cùng một thời điểm luôn có người mua và người bán - sự khác biệt nằm ở hoàn cảnh tài chính và mức độ lợi nhuận yêu cầu, không phải ở khả năng tính toán.

Khi thị trường nhiều người vay (margin) thì rủi ro cao hơn; khi ít người vay thì phần lớn dùng tiền tiết kiệm thật, tỷ suất lợi nhuận yêu cầu thấp hơn, rủi ro thị trường thấp hơn. Người đi vay để đầu tư và người dùng tiền tiết kiệm thật sẽ định giá khác nhau cho cùng một cổ phiếu.

## Buy-side và sell-side

Trong định giá, người ta phân biệt hai phía. Sell-side (bên bán) có xu hướng định giá cao hơn. Buy-side (bên mua, kể cả nhà đầu tư cá nhân) có xu hướng định giá thấp hơn. Đây là một trong những lý do khi nghe các đội ngũ phân tích nói về vùng giá mục tiêu, cần chiết khấu. Thầy thường dùng nguyên tắc giảm ít nhất 1/3 vùng giá mục tiêu mà sell-side đưa ra. Ở thị trường chứng khoán Việt Nam, nhiều khi sell-side đưa mục tiêu cao hơn 50-100% so với giá trị hợp lý - cần hết sức lưu ý.

Quan trọng hơn cả định giá của bản thân mình: trên thị trường, số lượng người theo phe nào mới quyết định giá. Nếu đa số là B (lạc quan, chấp nhận r thấp) thì giá sẽ tăng; nếu đa số là A (bi quan, yêu cầu r cao) thì giá sẽ giảm. Cho nên hiểu thị trường đang nghĩ gì quan trọng hơn bản thân mình nghĩ gì. Khi mình hợp lý trong một thị trường vô lý thì sẽ không có cơ hội - phải tận dụng sự vô lý của thị trường mới có cơ hội trong đầu tư chứng khoán.

## Thực tế Việt Nam: thay cổ tức bằng thu nhập

Ở Việt Nam rất nhiều doanh nghiệp không trả cổ tức, hoặc trả nhưng không có quy luật, nên rất khó định giá theo mô hình cổ tức. Thầy đề xuất dùng phương pháp thay thế: lấy toàn bộ thu nhập thay vì EPS, vì khi doanh nghiệp tăng vốn thì EPS có thể không còn chính xác. Dùng tổng thu nhập, sau đó quy đổi ngược.

Khi sử dụng thu nhập thay cho cổ tức, cần hiểu rằng thu nhập không chắc sẽ được trả hết cho cổ đông, và chưa chắc đã được trả. Vậy nên kết quả định giá từ thu nhập là giá trị tối đa - dễ lạc quan hơn so với dùng mô hình cổ tức thuần.

Đây cũng là lý do thầy nhấn mạnh phải sử dụng cùng phương pháp và cùng nguồn số liệu khi so sánh. Không thể lấy định giá chiết khấu dòng tiền của công ty chứng khoán A so sánh với định giá P/E, P/B của công ty chứng khoán B - hai phương pháp tiếp cận khác nhau, không so sánh được.

## Mô hình CAPM

Đối với tỷ suất lợi nhuận yêu cầu, biết rằng nó phải cao hơn lợi nhuận an toàn (lãi suất phi rủi ro) nhưng cụ thể là 13%, 14% hay 15% thì không biết chính xác. Trong định giá, người ta dùng mô hình CAPM (Capital Asset Pricing Model - mô hình định giá tài sản vốn).

CAPM dựa trên sự cân bằng của thị trường - tức là trung bình chung của toàn thị trường ở trạng thái cân bằng. Công thức:

r(i) = Rf + beta(i) x (Rm - Rf)

Trong đó Rf là lợi suất phi rủi ro (risk-free), thường dùng lãi suất trái phiếu chính phủ dài hạn. Beta(i) là beta của cổ phiếu i, đo mức biến động của cổ phiếu so với thị trường. Rm là lợi nhuận kỳ vọng của thị trường. (Rm - Rf) là phần bù rủi ro thị trường.

Vì Rf và Rm là giống nhau cho mọi cổ phiếu, sự khác biệt của tỷ suất lợi nhuận yêu cầu giữa các cổ phiếu hoàn toàn do beta quyết định. Beta cao thì tỷ suất lợi nhuận yêu cầu cao, định giá thấp xuống; beta thấp thì ngược lại. Cùng ngành, hai doanh nghiệp hoạt động tương đương nhưng một bên "đánh đấm" thường xuyên (beta cao) thì định giá dài hạn phải thấp hơn.

Về beta: cổ phiếu biến động mạnh hơn thị trường (cả lên cả xuống) thì beta > 1; biến động yếu hơn thị trường thì beta < 1. Beta có thể tìm trên bất cứ trang tài chính nào. Thông thường beta được tính cho 52 tuần (1 năm). Khi định giá hai công ty để so sánh phải lấy beta từ cùng một nguồn, vì phương pháp tính beta mỗi nơi khác nhau.

Về Rm: phải là kỳ vọng, không phải lịch sử. Nếu lấy Rm từ VN-Index những năm gần nhất (có thể âm) thì sai, vì kỳ vọng phải là số dương và phải lớn hơn lãi suất tiết kiệm. Thực tế, người ta phải theo dõi tăng trưởng của Index trong khoảng thời gian đủ dài. Thầy nêu ví dụ: trong vòng 20 năm qua, VN-Index tạo ra mức tăng trưởng khoảng 12%/năm. Nếu lãi suất tiết kiệm cũng là 12% thì ở giai đoạn đó không nên đầu tư chứng khoán, vì kỳ vọng lợi nhuận thị trường chỉ ngang lãi tiết kiệm.

Có nhiều sinh viên dùng CAPM nhưng máy móc lấy Rm từ Index thì sai - Rm là kỳ vọng, là số dương, là con số riêng.

Một cách khác để tính Rm là dựa trên khảo sát kỳ vọng nhà đầu tư. Trong QMV, thầy dùng phương pháp implied (lợi nhuận kỳ vọng hàm ý) - tính từ tăng trưởng lợi nhuận các công ty so với mức giá hiện tại. Khi vào trang QMV hoặc dùng on-bot, tỷ suất lợi nhuận yêu cầu hiển thị chính là Rm theo implied.

Về g (tăng trưởng dài hạn): có thể tính từ ROE x tỷ lệ giữ lại, nhưng về dài hạn cần giả định mức vừa phải vì doanh nghiệp luôn có giai đoạn tăng trưởng, bão hòa, suy thoái. Lấy g theo ROE gần nhất (ví dụ 20-30%) thì vô lý. Phương pháp đơn giản nhất là lấy g bằng tăng trưởng GDP, vì GDP đã bù trừ được cả giai đoạn tăng và giảm.

## Quy trình bảy bước định giá

Bước 1: thu thập thu nhập sau thuế các năm gần nhất, tính trung bình - thường là trung bình 5 năm để vượt qua một chu kỳ kinh tế. Lý do tính trung bình: doanh nghiệp phải đối mặt với chu kỳ kinh tế, nếu chọn vào năm tăng trưởng tốt thì thu nhập cao mà bỏ qua năm đi xuống thì kết quả lệch.

Bước 2: tìm Rf - lãi suất trái phiếu chính phủ, thường chọn kỳ hạn 10 năm vì định giá cổ phiếu mang tính dài hạn. Có thể lấy 1 năm cũng được, miễn là khi so sánh hai công ty phải dùng cùng kỳ hạn.

Bước 3: tìm Rm và phần bù rủi ro, cùng beta. Beta lấy từ cùng nguồn dữ liệu. Rm có thể lấy từ QMV (Rm implied) hoặc tự tính dựa trên tăng trưởng dài hạn của Index. Trên trang quymvgroup.vn có sẵn tỷ suất lợi nhuận yêu cầu, Rm và Rf.

Bước 4: tính tỷ suất lợi nhuận yêu cầu (r) từ các biến số trên.

Bước 5: giả định mức tăng trưởng dài hạn g - lấy theo GDP là đơn giản nhất, vì GDP đã bù trừ được cả giai đoạn tăng và giảm.

Bước 6: áp dụng công thức 2 để tìm tổng giá trị hợp lý của cổ phần. Vì bước 1 dùng tổng thu nhập nên bước 6 ra tổng giá trị vốn hóa.

Bước 7: quy đổi về giá một cổ phiếu. Công thức: Giá hợp lý mỗi cp = Giá hiện tại x Giá trị hợp lý tổng / Vốn hóa hiện tại. Cả ba thông số này đều có trên các trang tài chính.

Định giá rất chủ quan, thay đổi một biến số là giá trị thay đổi rất nhiều, nên vấn đề so sánh mới là quan trọng. Khi định giá hai công ty để so sánh phải dùng cùng phương pháp, cùng nguồn dữ liệu, cùng kỳ hạn, lý tưởng nhất là cùng một người thực hiện.

## Ví dụ mô phỏng và các tình huống thay đổi biến số

Thầy thực hiện mô phỏng trên bảng tính với dữ liệu đầu vào:
- EPS trung bình 4 năm (lấy từ dữ liệu của cổ phiếu trong ví dụ).
- Giá hiện tại: 19.200.
- Vốn hóa hiện tại: lấy từ thị trường.
- Tỷ suất lợi nhuận yêu cầu của thị trường: lấy từ QMV (implied).
- Lợi tức trái phiếu chính phủ 10 năm: lấy từ thị trường.
- GDP: giả định trong khoảng 6-7%, mục tiêu chính phủ 6,5%.

Tình huống cơ bản: r = 14,5% (tính từ CAPM với Rf + beta x (Rm - Rf)). Dùng công thức 2 với g = 6% (GDP1): giá trị hợp lý tính ra thấp hơn giá hiện tại 19.200 khoảng 44%.

Khi tăng g lên 7% (GDP2): giá trị hợp lý tăng lên 228. Càng tăng g thì giá trị cổ phiếu càng tăng khi các điều kiện khác không đổi. Kỳ vọng trung bình của hai tình huống g cho vùng tối thiểu, vùng tối đa và giá trị trung bình.

Các tình huống thay đổi biến số:

Thay đổi beta: dùng beta từ nguồn khác (tính theo 120 ngày thay vì 52 tuần). Beta cao hơn dẫn tới rủi ro cao hơn, tỷ suất lợi nhuận yêu cầu cao hơn, định giá thấp đi. Khi muốn so sánh hai công ty phải dùng cùng nguồn beta; beta ngắn hạn (120 ngày) rất khác beta dài hạn (1 năm). Kết luận: beta mà tăng - tức rủi ro cổ phiếu tăng do giao dịch - thì định giá sẽ giảm, kém hấp dẫn hơn về mặt dài hạn.

Thay đổi tăng trưởng kinh tế: g cao hơn dẫn tới định giá cao hơn. Khi kỳ vọng tăng trưởng ngành hoặc doanh nghiệp tốt hơn thì định giá tăng theo.

Thay đổi lãi suất: tăng lãi suất dẫn tới hai việc đồng thời - lợi tức trái phiếu chính phủ tăng, và tỷ suất lợi nhuận yêu cầu của thị trường cũng tăng tương ứng (vì phải duy trì chênh lệch với lãi suất tiết kiệm, dù không nhất thiết tăng đúng 1%). Kết quả: định giá giảm xuống rõ rệt. Trong ví dụ mô phỏng, khi lãi suất tăng, định giá xuống còn 30.000-44.000 so với tình huống cơ bản. Kết luận: lãi suất tăng thì định giá giảm, hấp dẫn của cổ phiếu giảm.

Tổng kết các tình huống: chỉ cần một kỳ vọng thay đổi (lãi suất, lạm phát, beta, tăng trưởng kinh tế, kỳ vọng dòng tiền/thu nhập/cổ tức) thì định giá thay đổi theo. Một doanh nghiệp đang bình thường trở nên "đánh đấm" thì beta tăng, định giá giảm; ngược lại, một doanh nghiệp "đánh đấm" trở nên ổn định thì định giá tăng. Định giá không hề cố định - một định giá của tuần trước sang tuần này có thể không còn đúng nữa.

## Điểm thầy nhấn mạnh

Định giá chỉ là một gợi ý tương đối, dùng để so sánh hai cổ phiếu cùng ngành, cùng nhóm dòng tiền tại một thời điểm. Nó đóng vai trò tài sản đảm bảo cho quyết định, có ý nghĩa về mặt dài hạn, nhưng không phải giá trị tuyệt đối.

Định giá so sánh (P/E, P/B) phục vụ giao dịch ngắn hạn vì chỉ đơn giản là so sánh ngang. Định giá chiết khấu (DCF) về bản chất vẫn là so sánh cổ phiếu với nhau, nhưng phục vụ cho đầu tư nắm giữ dài hạn vì nhìn vào tương lai.

Khi thực hiện định giá, hãy tiếp cận cách đơn giản nhất để có thể làm được. Càng đưa ra giả định phức tạp thì càng chính xác về mặt toán học, nhưng thực tế các nhà đầu tư không có thời gian nghĩ sâu đến mức đó, và bản chất các biến số trong công thức cũng là tương đối. Quan trọng là nhìn được xu hướng (định giá tăng hay giảm) chứ không phải con số chính xác tuyệt đối. Không ai có thể phán đoán chính xác nếu lãi suất tăng 1% thì định giá giảm bao nhiêu - vì bản chất các biến số trong công thức cũng là tương đối.

Định giá chỉ chứng minh được cổ phiếu nào là cổ phiếu tốt theo thống kê vài chục năm (số lớn). Trong những năm cổ phiếu giảm, nếu lỡ nắm giữ thì định giá vô nghĩa - thống kê số lớn chỉ dựa trên trung bình các năm. Không có khái niệm cổ phiếu tốt vĩnh viễn - chỉ có cổ phiếu tốt tại thời điểm quyết định. Định giá không phải phương pháp tốt để quyết định vào/ra; cần kết hợp phân tích kỹ thuật cho điểm vào/ra.

Đầu tư thuần tuý dựa trên định giá đòi hỏi rất nhiều thời gian thì mới có lời.

## Bối cảnh thị trường lúc giảng (05/2024)

Bài giảng sử dụng một số dữ kiện thị trường làm ví dụ minh hoạ cho bài học:
- Lãi suất tiết kiệm 12%/năm (làm ví dụ về chi phí cơ hội - thầy nói "lãi suất tiết kiệm mới đây lên tới 12%").
- VN-Index tăng trưởng trung bình khoảng 12%/năm trong 20 năm qua (làm ví dụ về Rm kỳ vọng). Thầy nhận xét nếu lãi suất tiết kiệm và Rm đều khoảng 12% thì ở giai đoạn đó không nên đầu tư chứng khoán.
- GDP mục tiêu 6,5% (làm ví dụ về g, thầy giả định khoảng 6-7% trong mô phỏng).
- Giá cổ phiếu QMV 250.000 đồng/cp, EPS 10.000 đồng/cp (ví dụ minh hoạ chính).
- Một cổ phiếu khác trong ví dụ mô phỏng ở phần sau có giá hiện tại 19.200, dùng làm đầu vào để quy đổi về giá trị hợp lý mỗi cp.
