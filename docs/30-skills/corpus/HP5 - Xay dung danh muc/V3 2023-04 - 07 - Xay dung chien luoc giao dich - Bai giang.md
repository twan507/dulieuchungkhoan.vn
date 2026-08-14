# V3 2023-04 - 07 - Xay dung chien luoc giao dich - Bai giang

Bài cuối của học phần 5 (Xây dựng danh mục), hệ thống hoá ba trụ cột của chiến lược giao dịch: vĩ mô, sự kiện, và kỹ thuật. Nội dung mới so với phiên bản cũ gồm mô hình Chín Quả Bóng (phân nhóm ngành và dòng tiền theo chu kỳ kinh tế - chính sách) và chiến lược giao dịch theo sự kiện với khái niệm giai đoạn cửa sổ. Phần phân tích kỹ thuật chỉ ôn gọn để dành thời gian hướng dẫn ghép các công cụ thành hệ thống giao dịch cá nhân. Bài giảng quay và đăng ngày 02/06/2024, các nhận định về tình hình thị trường trong bài được neo theo thời điểm này.

## Tổng quan buổi học và bối cảnh học phần

Bốn bài trước trong học phần đã trang bị: mục tiêu xây dựng danh mục và phân biệt rủi ro cá nhân với rủi ro cổ phiếu; nhận diện chu kỳ kinh tế; lựa chọn nhóm ngành phù hợp với tình trạng kinh tế; lựa chọn dòng tiền (cấp ngành và cấp cổ phiếu) dựa trên chất lượng và định giá. Sau bốn bài đó, người học đã có danh sách cổ phiếu cần theo dõi; bài này trả lời câu hỏi tiếp theo: khi nào và bằng cách nào quyết định mua bán.

Điểm nhấn lại từ bài đầu: rủi ro của cổ phiếu mang tính khách quan, nhà đầu tư không can thiệp được; rủi ro của chính nhà đầu tư là chủ quan và hoàn toàn có thể kiểm soát bằng nguyên tắc. Phân biệt an toàn hay rủi ro nằm ở chỗ có nguyên tắc hay không, không phải ở việc chọn cổ phiếu an toàn hay rủi ro. Thầy lưu ý thêm: chọn cổ phiếu an toàn không đồng nghĩa với giao dịch an toàn, vì nguyên tắc mới là yếu tố quyết định.

So với các phiên bản trước, bài này bổ sung mô hình chín quả bóng (chiến lược vĩ mô) và chiến lược giao dịch theo sự kiện, ngoài phần phân tích kỹ thuật truyền thống.

## Chiến lược vĩ mô: mô hình Chín Quả Bóng

### Cấu trúc mô hình

Chia toàn bộ cổ phiếu niêm yết thành ba nhóm ngành. Trong mỗi nhóm ngành lại phân thành ba nhóm dòng tiền, đặc trưng bởi mức độ an toàn khác nhau. Ba nhân ba bằng chín, ứng với chín quả bóng. Mô hình này được thầy chuẩn bị từ khoảng hai năm trước thời điểm giảng và đến lúc giảng vẫn phù hợp với diễn biến thị trường, nên thầy dùng lại.

### Quy luật luân chuyển theo chu kỳ lớn

Chu kỳ chính sách lớn (đơn vị một đến hai năm, không phải một đến hai tuần) trải qua ba giai đoạn: tích lũy kết hợp tăng nghi ngờ, tăng, tăng mạnh kết hợp bão hòa. Tương ứng có ba nhóm ngành chủ chốt để quan sát.

Trong giai đoạn tích lũy và tăng nghi ngờ, dòng tiền ưu tiên tìm đến nhóm ngành 1 trước, rồi đến dòng tiền 2 và 3 trong cùng nhóm ngành. Dòng tiền 1 được định nghĩa là nhóm an toàn nhất nên biến động thấp hơn. Dòng tiền 2 và 3 (thường là cổ phiếu vốn hoá nhỏ, thị giá thấp, hay gọi nôm na là cổ phiếu trà đá) có biên độ mạnh hơn: tăng nhanh hơn nhưng giảm cũng sâu hơn.

Khi dòng tiền 1 của nhóm ngành 1 đã chạy, dòng tiền 1 của nhóm ngành 2 có thể xuất hiện ngay, không cần chờ dòng tiền 2 và 3 của nhóm ngành 1 kết thúc. Đây là sự đan xen: quả bóng tiếp theo không nhất thiết phải đợi quả bóng trước chạy xong. Đến giai đoạn ba (tăng mạnh), dòng tiền 3 của nhóm ngành 3 cũng có thể xuất hiện.

Khi tất cả cổ phiếu trà đá của các ngành đều đã chạy, thị trường chuẩn bị bước vào giai đoạn bão hòa. Khi nhóm này dừng lại hoặc hết đà, cần nghĩ ngay đến khả năng điều chỉnh trong ngắn hạn, và trong chu kỳ lớn thì đó cũng là dấu hiệu chu kỳ chính sách tích cực sắp kết thúc. Khi chu kỳ kết thúc và thị trường giảm, dòng tiền quay lại nhóm an toàn trước: ưu tiên mua cổ phiếu an toàn của nhóm ngành 1, rồi đến nhóm ngành 2, rồi nhóm ngành 3.

Thầy nhấn mạnh hai lần: khi nhóm ngành 2 hoạt động không có nghĩa là nhóm ngành 1 kết thúc; nhóm 2 chỉ đang có tiền vào nhiều hơn và có khả năng tăng mạnh hơn. Các nhóm ngành hoạt động đan xen, không tuần tự tuyệt đối.

### Áp dụng cho chu kỳ nhỏ trong chu kỳ lớn

Cùng nguyên lý trên áp dụng được cho chu kỳ nhỏ nằm trong chu kỳ lớn, dù trong ngắn hạn ranh giới các giai đoạn không rõ bằng. Cụ thể: nếu dòng tiền 3 của nhóm ngành 2 điều chỉnh nhưng người mua vẫn quay lại nhóm này, đó là một lần điều chỉnh trong giai đoạn tăng mạnh. Nếu dòng tiền 3 của nhóm ngành 3 điều chỉnh nhưng người mua vẫn quay lại mua an toàn của nhóm ngành 3, đó thường vừa là điều chỉnh vừa là kết thúc chu kỳ.

Trong giai đoạn tích lũy và tăng nghi ngờ, mục tiêu chính vẫn là nhóm ngành 1, có thể nghĩ đến dòng tiền 1 của nhóm ngành 2. Trong nhóm ngành 1, ba dòng tiền vẫn là chủ đạo.

Về hiện tượng cổ phiếu penny thỉnh thoảng đánh lên rồi rơi xuống: sau một thời gian đánh lên kết thúc chu kỳ, phe lớn gom trở lại, khi gom đủ sẽ đẩy giá lên. Ở giai đoạn tích lũy và tăng nghi ngờ, các cổ phiếu này thường bắt đầu có dấu hiệu chạy vì lực ép giá không còn.

### Tín hiệu đảo chiều cần theo dõi

Thầy dùng từ "điều chỉnh" thay cho "rơi" để nhấn mạnh: dù khó rơi nhưng sẽ có sự điều chỉnh. Hai tình huống cụ thể cần chú ý:

- Dòng tiền 3 vẫn tăng tốt nhưng đang dừng lại, đồng thời xuất hiện dòng tiền an toàn nhóm 1 được mua (ví dụ ngân hàng), thì khả năng điều chỉnh cao.
- Dòng tiền 3 đã chạy rồi dừng, dòng tiền 1 lại được mua, thì thị trường có sự điều chỉnh trong giai đoạn ngắn thuộc chu kỳ lớn.

Vì mô hình chín quả bóng có tính giả định, thầy gợi ý thêm: với chu kỳ lớn thì hoàn toàn giữ dài hạn và rebalancing; với chu kỳ nhỏ thì cũng áp dụng được nguyên lý tương tự, dù trong ngắn hạn không rõ bằng.

## Chiến lược giao dịch theo sự kiện

### Ba giai đoạn phản ứng với tin

Mọi sự kiện vĩ mô hay doanh nghiệp đều trải qua ba giai đoạn: dọn đường, thông báo, thực hiện. Quy luật chung: giai đoạn dọn đường và thông báo phản ứng mạnh nhất; giai đoạn thực hiện phản ứng yếu hơn. Nguyên lý này áp dụng cho cả tin tốt lẫn tin xấu, chỉ khác nhau ở mức độ điều chỉnh sau tin.

Phân loại theo bản chất tin:

- Tin tốt dẫn đến tiền ra thật (ví dụ giảm lãi suất) thì khả năng giữ và tăng tiếp sau điều chỉnh sẽ cao hơn.
- Tin tốt dạng đồn đại, không dẫn đến thực hiện thì điều chỉnh sẽ mạnh hơn.
- Tin xấu được thực hiện thật thì thường chỉ quanh quẩn.
- Tin xấu không phải tin xấu thật thì có xu hướng quay trở lại.

Tóm lại: càng gần giai đoạn đồn đoán và thông báo, phản ứng càng mạnh; càng xa (sau xác nhận và thực hiện) thì phản ứng càng yếu.

Với doanh nghiệp cũng vậy: tin ra, xác nhận kiểm toán, điều chỉnh kiểm toán đều là dạng sự kiện. Giai đoạn đồn đoán và phản ứng trước khi tin ra thường mạnh nhất; sau khi tin ra thì chững lại; giai đoạn xác nhận cũng không tác động nhiều nữa.

### Giai đoạn cửa sổ

Hình ảnh thầy vẽ: ngày sự kiện là điểm zero, trước và sau là hai giai đoạn cửa sổ. Giai đoạn cửa sổ kéo dài bao lâu tuỳ trường hợp, có thể một tuần, một tháng, hoặc vài ngày. Thầy nhấn mạnh giai đoạn cửa sổ cần một số phiên T+, không phải T+0; những người hiểu theo nghĩa T+0 là hoàn toàn sai.

Thầy dẫn một ví dụ thực tế về một mã cổ phiếu `[?mã - ASR: "HANNERG"]`: thầy viết status Facebook về trường hợp này, nhiều bạn phản đối vì nghĩ rằng phải vào ngay ngày sự kiện. Lý do sai là vì luôn có giai đoạn cửa sổ, không ai nhảy vào sự kiện tại đúng ngày.

### Nguyên tắc hành động quanh ngày sự kiện

- Tin tốt ra mà cổ phiếu vẫn tăng: cứ để chạy đến khi có điểm uốn thì cân nhắc bán, không bán ngay tại ngày sự kiện.
- Cổ phiếu đang giảm mà tin tốt ra: cân nhắc mua nhưng không mua ngay ngày công bố, chờ giai đoạn cửa sổ.

Tương tự cho tin xấu. Thầy dùng nguyên tắc chung: vào vì lý do gì thì ra vì lý do đó. Không nên hành động gì tại ngày sự kiện, dù tin tốt hay tin xấu; hành động dựa trên điểm uốn, áp dụng cho cả mua và bán.

Trước ngày sự kiện, nếu tin đồn xuất hiện (tin đồn tốt có khả năng xảy ra), cổ phiếu có thể có giai đoạn tích lũy rồi bật lên: đó có thể là điểm mua tốt vì vẫn nằm trong giai đoạn cửa sổ.

Giai đoạn cửa sổ của bên bán và bên mua hoàn toàn khác nhau; các nghiên cứu tài chính phân chia theo khung thời gian (một tuần, một tháng), nhưng về mặt cá nhân thầy chỉ nhấn mạnh rằng bao giờ cũng phải có giai đoạn cửa sổ.

Chiến lược giao dịch theo sự kiện về bản chất là ngắn hạn, không phải dài hạn. Các sự kiện thường xuyên xuất hiện ở thị trường Việt Nam gồm: cổ tức, kết quả kinh doanh, cổ phiếu thưởng, tăng vốn. Đặc biệt trong giai đoạn thị trường tốt, các sự kiện này diễn ra rất nhiều.

## Ôn tập phân tích kỹ thuật

Bài ôn gồm năm khối kiến thức đã học ở học phần 4, thầy chỉ nhắc lại gọn.

### Khối 1: Phân tích giá, khối lượng, xu hướng, kháng cự và hỗ trợ

Mục tiêu là xác định khu vực đảo chiều. Hai quy tắc dùng khối lượng:

- Xu thế giá tăng kết hợp khối lượng giao dịch tăng kết hợp giá chững lại, khả năng đảo chiều có.
- Xu thế giá giảm kết hợp khối lượng không giảm thêm kết hợp giá chững lại, khả năng đảo chiều cũng cao.

Vùng kháng cự và hỗ trợ là vùng có khả năng xảy ra điểm uốn. Đường xu hướng cũng đóng vai trò như hỗ trợ và kháng cự nhưng thường là đường chéo nên nhà đầu tư nhìn ngang dễ hơn nhìn chéo. Vì vậy so với hỗ trợ và kháng cự, vai trò của đường xu hướng yếu hơn, không nên lệ thuộc.

### Khối 2: Phân tích nến

Ba loại nến đáng quan tâm trong bất kỳ xu hướng nào, phân loại theo tương quan thân nến so với độ dài nến (vùng biến động so với điểm cao nhất và điểm thấp nhất). Nến đảo chiều có thân dài và bóng ngắn, thân ngắn nghĩa là nằm gọn về một nửa trên, một nửa dưới, hoặc một phần ba trên hoặc dưới. Nến nằm hẳn một phía đáng tin cậy hơn nến nằm ở giữa.

Thay vì nhớ tên các mẫu nến phức tạp (như Morning Star, Evening Star, ba người lĩnh), có thể ghép 2-3 nến lại thành một nến lớn và đọc theo nguyên tắc trên. Bản chất mọi mẫu nến đều quy về một nến, nên không nhất thiết phải nhớ tên từng mẫu.

### Khối 3: Phân tích chỉ số

Chỉ số có tính chất xác nhận, không phải công cụ tạo tín hiệu chính. Càng nhiều yếu tố cùng phản ánh một kết luận, khả năng kết luận đó xảy ra càng cao.

Các chỉ số nằm dưới đồ thị giá (chỉ số sức mạnh xu hướng như RSI) có vùng quá mua, vùng quá bán và các đường giao cắt ngắn dài. Các chỉ số đều có kháng cự và hỗ trợ riêng, có vùng quá mua tương tự đỉnh và vùng quá bán tương tự đáy. Khi vùng quá mua hoặc vùng quá bán của chỉ số không tương ứng với giá, tạo ra sự mất cân đối gọi là phân kỳ. Phân kỳ dương là cơ hội mua, phân kỳ âm là cơ hội bán.

### Khối 4: Phân tích mẫu hình

Có 36 mẫu hình phổ biến. Bản chất tất cả mẫu hình đều thể hiện sự lưỡng lự và chờ đợi, tương tự giai đoạn tích lũy. Mẫu hình chỉ đáng tin cậy ở khung thời gian ngắn (vài ngày); ở khung dài hơn, tin vào mẫu hình tuyệt đối là rủi ro.

Mẫu hình đáng tin cậy hơn (tam giác, khung giao động có độ giật nhỏ) cần quan tâm nhiều hơn. Ví dụ khung giao động đi xuống nhưng mức độ giật nhỏ đáng tin cậy hơn khung có độ giật lớn.

Nếu mẫu hình thể hiện sự lưỡng lự, bước tiếp theo phụ thuộc vào tin (xấu nhiều hay tốt nhiều), không nên chỉ dựa vào mẫu hình.

### Khối 5: Sóng và lý thuyết cơ bản

Các lý thuyết sóng (sóng Elliott, Nowzone, Wyckoff) đều dựa trên cơ sở 2 lần đổi gác tạo ra 3 lần bước sóng tăng. Sóng Elliott có 5 bước (3 lần tăng: bước 1, 3, 5; 2 lần điều chỉnh: bước 2, 4). Nowzone có 3 giai đoạn chính. Wyckoff có 3 giai đoạn chính với đặc trưng riêng: ở vùng tích lũy đáy phải giảm mạnh xuống rồi bật lên, ở vùng đỉnh tăng mạnh rồi giảm xuống, Wyckoff đưa thêm yếu tố tâm lý.

Lý do chia ba là vì có trạng thái trung bình, trạng thái tích cực thái quá, và trạng thái tiêu cực thái quá. Điểm chạm thứ ba quan trọng hơn vì khả năng phản ứng theo hướng mẫu hình và các yếu tố khác cao hơn.

Wyckoff và Wycliffe giải thích thêm: ở vùng lưỡng lự dạng mẫu hình, trước khi tăng phải có một lần rơi xuống khỏi vùng đó (thường là vùng thứ 3), sau đó nếu bật lên sẽ vượt được cả vùng tích lũy trước; bên bán không chịu nổi ở lần thứ 3 nên mới lên được. Ở đỉnh, lần chạm thứ 3 vọt lên rồi không tăng được, rơi xuống, bên mua nhảy vào nhưng bên bán quá mạnh nên không cầm được, rơi luôn.

## Xây dựng hệ thống giao dịch

### Quan điểm chung

Chiến lược giao dịch viết trong sách vở thường không rõ ràng, có thể chỉ là chiến lược dựa trên Stochastic, MA, hay ROE, nghe thì phức tạp nhưng thực chất không có bí kíp gì. Mọi chiến lược đều là sự ghép các kiến thức kỹ thuật đã học.

Các hệ thống giao dịch, kể cả hệ thống AI, chỉ tạo ra tín hiệu để quan tâm, không thay thế được việc xem xét bằng mắt. Tất cả hệ thống đều có tỷ lệ đúng giới hạn, dù backtest hay theo dõi thực tế đều cho thấy vậy.

Khi xây dựng chiến lược, không nhất thiết phải dùng tất cả năm khối kiến thức. Ví dụ sóng khó đo bằng bot, nến có thể đo từng tín hiệu lẻ nhưng khi kết hợp nhiều chỉ báo khác nhau thì khó. Chiến lược đơn giản là một điểm báo, dùng thêm nhiều yếu tố đầu vào (vùng quá mua/quá bán, kháng cự/hỗ trợ) sẽ hiệu quả hơn.

Thị trường có xu hướng rõ thì chỉ số kỹ thuật là đủ. Thị trường sideway thì chỉ dùng chỉ số là khó, phải nhìn thêm nhiều yếu tố khác.

Kết luận thầy nhấn mạnh: dùng bằng mắt, dùng hệ thống đơn giản, và luôn test lại bằng mắt.

### Ví dụ với đường MA

Dùng ba đường MA ngắn, trung, dài hạn. Tham số phổ biến:

- 5/20/60 ngày (giao dịch ngắn hạn)
- 20/60/100 ngày
- 50/200 ngày (1 quý / 1 năm), hoặc 60/200 ngày

Quy ước thời gian: 5 ngày tương đương 1 tuần, 10 ngày tương đương 2 tuần, 20 ngày tương đương 1 tháng, 60 ngày tương đương 1 quý, 200 ngày tương đương 1 năm.

Cách dùng cơ bản:

- Xu hướng tăng ngắn hạn: giá nằm trên MA ngắn nhất.
- Xu hướng tăng dài hạn: giá nằm trên MA tương ứng (ví dụ MA 200 cho xu hướng một năm).
- Tín hiệu mua: giá vượt lên đường MA thấp nhất (vượt đường ngắn nhất hoặc đường thấp nhất).
- Điểm chốt lời: khi giá chạm đường MA cao hơn kế tiếp (đường MA đóng vai trò như kháng cự).
- Điểm dừng lỗ: điểm tích lũy trước đó.

Lưu ý thực tế: breakout vượt đường MA thường fail lần đầu. Có thể vào ngay hoặc đợi vượt lên rồi retest lại rồi vào. Quy tắc này áp dụng được cho hầu hết chỉ số (Ichimoku, Bollinger Band).

### Ví dụ với RSI

RSI là chỉ số dẫn dắt (leading indicator) nên đi trước giá; khi nó cắt lên hay cắt xuống có thể cảnh báo biến động tiếp theo của giá. Ba cách dùng RSI:

- Quan sát xu hướng của đường RSI: khi đường RSI cắt xuống đường xu hướng tăng của nó thì đó là điểm bán; cắt lên đường xu hướng giảm thì đó là điểm mua.
- So sánh RSI như kháng cự/hỗ trợ.
- Phân kỳ âm hoặc phân kỳ dương.

Ngoài ra có thể thiết lập hai đường RSI ngắn và dài ngày (ví dụ RSI 5 và RSI 14), cắt nhau là điểm vào/ra. Khi chỉ số ở vùng quá bán/quá mua thì tín hiệu cắt có ý nghĩa hơn.

### Ví dụ với MACD

Có đường nhanh, đường chậm. Ở vùng quá bán/quá mua, MACD càng thấp thì độ tin cậy khi cắt lên càng cao. Ví dụ chiến thuật:

- Mua khi giá vượt lên cây nến thấp nhất tại vùng đảo chiều, dừng lỗ tại hỗ trợ gần nhất.
- Chốt lời khi đường nhanh cắt xuống đường chậm; MACD càng cao thì chốt càng nhiều.

Nguyên tắc: đường nhanh cắt lên đường chậm là điểm mua, đường nhanh rơi xuống khỏi đường chậm là điểm bán. Có thể kết hợp với kháng cự/hỗ trợ và phân kỳ.

### Ví dụ với Stochastic Oscillator

Nguyên tắc vẫn là cắt lên cắt xuống các đường. Khi Stochastic ở vùng quá bán cắt lên trên 20 thì có ý nghĩa hơn.

### Nguyên tắc chung khi xây dựng hệ thống

Bản chất mọi hệ thống giao dịch đều dựa trên nguyên tắc cắt lên cắt xuống. Hệ thống thông minh hơn đưa thêm nhiều yếu tố đầu vào để loại trừ nhiễu. Ví dụ đường nhanh cắt đường chậm nhưng cần kèm theo vị trí (nằm ở vùng nào), vượt lên 20 hay không, nến như thế nào.

Đừng tìm hệ thống phức tạp cao siêu. Phức tạp ở đây nghĩa là dùng nhiều chỉ số thường gặp kết hợp với nhau và thêm nhiều yếu tố đầu vào, không phải mô hình phức tạp.

### Tỷ lệ đúng của hệ thống AI và bot QMV

QMV đã nỗ lực xây dựng hệ thống AI và bot cho khoảng 1.700 cổ phiếu. Tỷ lệ báo đúng của AI đến thời điểm giảng vào khoảng 70%, có nơi nêu 70-80% hoặc 68-70%. Tức là vẫn còn khoảng 30% (hoặc 20-30%) là sai; nếu rơi đúng vào phần sai đó thì hệ thống không cứu được.

Lưu ý thầy: nếu ai nói có chiến lược giao dịch thắng chắc 100% thì không có thật, tất cả đều dựa trên nguyên tắc cắt lên cắt xuống tương tự như trên. Thầy từng chứng kiến nhiều chuyên gia nước ngoài sang Việt Nam dạy những thứ rất đơn giản với học phí cả ngàn đô một ngày, gọi là bí kíp nhưng thực ra không có bí kíp gì.

## Ba cách mua

Thầy phân biệt ba cách mua, đồng thời cũng khẳng định đây là ba lý thuyết mua phổ biến, không riêng QMV: mua hỗ trợ, mua đột phá (breakout), và mua theo đà (momentum). Tín hiệu bot của QMV (ví dụ các hệ thống Phoenix, Phoenix Energy `[?ASR - có thể là tên hệ thống/bot, không phải mã cổ phiếu]`) cũng đưa vào cả ba kiểu mua này.

### Mua hỗ trợ

Mua tại vùng hỗ trợ, tức vùng giá tương ứng với vùng thấp trước đó. Cách mua này phù hợp với giai đoạn tích lũy, tích lũy và tăng nghi ngờ. Khi thị trường tạo vùng giao động, có thể mua ở vùng giao động; nếu vùng đó tạo phân kỳ thì mua được.

Trong thực tế, mua hỗ trợ thường đòi hỏi gom trước ở hai đoạn đầu (khi khối lượng giao dịch còn nhỏ) rồi đến khi đột phá mua thêm. Thầy dùng ví dụ cổ phiếu trà đá: mua ở vùng hỗ trợ thì khối lượng giao dịch phải nhỏ, mua ở vùng đột phá thì khối lượng lớn hơn.

### Mua đột phá (breakout)

Mua tại vùng giá vượt lên khỏi vùng kháng cự. Những người mua breakout căn cứ vào đường xu hướng (ví dụ đường xu hướng giảm, cứ mỗi lần giá vượt lên là điểm mua tiềm năng).

Cảnh báo: mua breakout ở vùng giá đã tăng mạnh thì rủi ro. Trong định nghĩa breakout, mua ở lần đầu vượt là rủi ro, mua ở khung giao động hẹp thì bình thường. Thường chỉ nên dùng breakout khi thị trường đang tăng. Theo kinh nghiệm thầy, mua breakout ở vùng đã tăng và mua ở lần đầu vượt là rủi ro hơn so với mua theo đà.

### Mua theo đà (momentum)

Mua sau khi đã đột phá, có thể chậm 1-2 phiên để xem có điều chỉnh không. Nếu khoảng cách đến mục tiêu kế tiếp đủ lớn thì mua theo đà có ý nghĩa. Trong ngắn hạn có thể tính theo T+2 đến T+2.5 `[?T+2 đến T+2.5 - ASR: "tê cộp 2, 2 rữ"]`; nếu thấy mục tiêu đủ thì áp dụng được.

Lý do: khi cổ phiếu đã tăng chưa hẳn đã hết cơ hội, cần nhìn mục tiêu tiếp theo. Người mua theo đà chờ xem đột phá thành công rồi mới nhảy vào, không mua kiểu năm thắng năm thua.

### Khi nào dùng cách nào

- Giai đoạn tích lũy, tích lũy và tăng nghi ngờ: mua hỗ trợ phù hợp hơn.
- Giai đoạn tăng mạnh: mua đột phá và mua theo đà phù hợp hơn.

Về nhận diện cụ thể: nếu cổ phiếu đang trong giai đoạn giao động và vừa vượt lên thì breakout và momentum an toàn hơn. Nếu cổ phiếu đã tăng mạnh rồi và đến đó vượt lên thì bot vẫn báo nhưng mua kiểu này rủi ro.

Mua đột phá và mua theo đà bản chất gần giống nhau, khác ở chỗ mua theo đà chờ đột phá thành công rồi mới vào, còn mua đột phá có thể vào ngay khi vượt khỏi vùng kháng cự.

## Bối cảnh thị trường lúc giảng (06/2024)

Bài giảng quay ngày 02/06/2024. Một số nhận định thầy đưa ra có tính thời điểm:

- Mô hình Chín Quả Bóng đã được thầy chuẩn bị từ khoảng 2 năm trước, đến lúc giảng vẫn phù hợp với diễn biến thị trường.
- Tại thời điểm bài giảng, thầy đánh giá thị trường đang trong giai đoạn tích lũy và tăng nghi ngờ.
- Thầy quan sát thấy dòng tiền 1, 2, 3 của nhóm ngành 1 vẫn tốt hơn so với nhóm ngành 2; nhóm ngành 2 vẫn đang trong giai đoạn tích lũy.
- Thầy đánh giá lượng tiền trên thị trường khá nhiều, dựa trên các đặc điểm: dòng tiền 1 của nhóm 1 chạy, dòng tiền 2 và 3 chạy, các cổ phiếu đánh lên xuất hiện tương đối nhiều.
- Tuy nhiên, thầy cảnh báo nếu dòng tiền 3 (cổ phiếu vốn hoá nhỏ, thị giá nhỏ) đang tăng tốt mà dừng lại, đồng thời xuất hiện cổ phiếu lớn nhóm an toàn (ví dụ ngân hàng) được mua, thì khả năng điều chỉnh cao.
- Thầy nhấn mạnh dùng từ "điều chỉnh" thay cho "rơi" vì khó rơi nhưng sẽ có sự điều chỉnh.
- Về lựa chọn công cụ: ở giai đoạn tích lũy và tăng nghi ngờ hiện tại, thầy cho rằng dùng chỉ số kỹ thuật là đủ để giao dịch; nếu thị trường sideway thì phải nhìn thêm nhiều yếu tố khác.
- Về cách mua: thầy khuyến nghị mua theo hỗ trợ nhiều hơn ở giai đoạn hiện tại, mua đột phá vẫn có yếu tố rủi ro, mua theo đà thì cần chờ breakout thành công rồi mới vào.

## Điểm thầy nhấn mạnh

- Ba trụ cột chiến lược: vĩ mô, sự kiện, kỹ thuật. Bài giảng bổ sung hai trụ đầu vào chương trình.
- Mô hình Chín Quả Bóng dùng để chọn nhóm ngành và nhóm cổ phiếu cho từng giai đoạn chu kỳ.
- Chiến lược giao dịch theo sự kiện là ngắn hạn, dùng được lâu dài vì sự kiện luôn xuất hiện; áp dụng cho cả tin vĩ mô và tin doanh nghiệp.
- Phân tích kỹ thuật không có gì phức tạp, đừng tìm bí kíp. Tất cả chiến lược (kể cả của chuyên gia nước ngoài với học phí cả ngàn đô một ngày) đều dựa trên nguyên tắc cắt lên cắt xuống các đường chỉ số, không có gì đặc biệt.
- Có nguyên tắc thì không rủi ro, không có nguyên tắc thì rủi ro bất kể cổ phiếu an toàn hay không.
- Dù có hệ thống AI/bot tỷ lệ đúng 70% thì 30% còn lại vẫn có thể sai. Phải luôn xem bằng mắt, không tin tưởng tuyệt đối vào bot.
- Chiến lược đơn giản cộng thêm nhiều yếu tố đầu vào cộng thêm kiểm tra bằng mắt.
- Bài giảng truyền thống về phân tích kỹ thuật được trình bày vắn tắt hơn các phiên bản trước vì mục tiêu chính là giúp người học tự tạo hệ thống giao dịch cho mình.
