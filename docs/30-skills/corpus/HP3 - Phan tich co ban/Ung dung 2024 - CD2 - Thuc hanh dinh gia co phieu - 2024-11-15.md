# Ung dung 2024 - CD2 - Thuc hanh dinh gia co phieu - 2024-11-15

Buổi học ngày 15/11/2024 dạy về thực hành định giá cổ phiếu theo khung QMV. Thầy trình bày hai phương pháp tiếp cận lớn (so sánh và chiết khấu dòng tiền), ý nghĩa thật sự của con số định giá, mối liên hệ giữa PE/PB với dòng tiền, rồi thực hành trên Blackbox với hai mã ngành dầu khí: PVD và BSR. Điểm xuyên suốt: định giá chỉ là công cụ so sánh tương đối giữa hai cổ phiếu đang cân nhắc, không phải mục tiêu giá tuyệt đối.

## Tổng quan và hai phương pháp tiếp cận

Có hai phương pháp lớn để định giá cổ phiếu. Phương pháp thứ nhất là định giá so sánh: so sánh công ty đang quan tâm với các công ty khác trong cùng ngành tại cùng một thời điểm, hoặc so sánh với chính nó ở các thời điểm khác nhau trong quá khứ. Phương pháp thứ hai là định giá dựa trên cơ sở dòng tiền, còn gọi là giá trị nội tại hay giá trị thực: ước lượng các dòng tiền tương lai rồi so sánh giá trị tạo ra từ các dòng tiền đó với giá cổ phiếu hiện tại.

Cách phân biệt truyền thống: người theo phương pháp so sánh nhìn hiện tại và quá khứ, người theo phương pháp dòng tiền nhìn tương lai. Nhưng thầy cảnh báo cả hai đều có vấn đề riêng. Dùng hoàn toàn dữ liệu hiện tại và quá khứ thì không trả lời được câu hỏi tương lai sẽ ra sao. Dùng số liệu tương lai thì tương lai lại bất định, không thể ước lượng chính xác. Kinh nghiệm cá nhân của thầy khi làm lâu năm trong ngành chứng khoán: bản thân thầy cũng không biết năm sau công ty chứng khoán thầy làm sẽ hoạt động thế nào, dù mỗi năm họ đều có kế hoạch triển khai. Phần lớn các kế hoạch đó khi triển khai thực tế lại dùng dữ liệu quá khứ và hiện tại để dự báo tương lai, ví dụ chứng khoán thì dựa vào index lên bao nhiêu thì thu được bao nhiêu phí.

Kết luận của thầy: định giá là một trò chơi, và là trò chơi về ý chí chủ quan của người định giá. Phân tích kỹ thuật cũng vậy, đếm Fibonacci hay vẽ hỗ trợ kháng cự bản chất cũng chỉ là ước lượng dựa trên thông lệ. Tất cả đều là ý chí chủ quan. Nếu nhiều phương pháp cho cùng một câu trả lời khi so sánh các công ty đang lựa chọn thì rất có thể đó là điểm chung phản ánh sự thật.

Lưu ý thực dụng thầy đưa ra ngay từ đầu: khi định giá ra một con số, ví dụ cổ phiếu A giá 10 mà định giá ra 20, đừng nhìn vào con số 20 như mục tiêu. Hãy nhìn tỷ lệ phần trăm, tức 100% tăng. Nhưng cũng đừng dính vào con số 100% đó. Phải so với các công ty khác cùng ngành. Ví dụ công ty B trong cùng ngành, cùng phương pháp định giá, ra kết quả 30, giá hiện tại 15, cũng cho 100% tăng. Còn nếu giá B đang là 10 và định giá 30 thì là 200% tăng. Vậy thì chọn B, không phải vì mua B để chờ lên 30, mà vì con số 200% tốt hơn 100%. Định giá dùng như phương pháp bảo hiểm cho quyết định đầu tư: cho biết doanh nghiệp đó có tốt hay không.

## Định giá so sánh: PE, PB và các nhân tố

Phương pháp so sánh phổ biến nhất là PE và PB, ngoài ra còn có định giá theo Doanh thu, EBITDA. Trong PE và PB có thể so sánh chiều ngang (so với chính mình theo thời gian) hoặc chiều dọc (so với các doanh nghiệp trong cùng ngành).

Lưu ý quan trọng nhất: giá trị định giá không tồn tại vĩnh viễn. Chỉ cần một giây sau khi giá thay đổi là định giá đã thay đổi. PE các công ty đều thay đổi theo giá, chỉ 50 phút sau khi vào phiên giao dịch là định giá rất khác. Cho nên đừng bao giờ nhìn vào con số định giá tuyệt đối để ra quyết định. Phải hiểu: tại thời điểm tôi ra quyết định, công ty nào đang có định giá hấp dẫn hơn đối với tôi, chứ không phải giá trị định ra của nó.

Quan niệm thường gặp cần sửa: PE thấp = định giá rẻ, PE cao = định giá cao. Thầy nhấn mạnh quan niệm này sai. Công ty PE thấp có thể do không ai quan tâm, công ty PE cao có thể do nhiều người kỳ vọng vào khả năng tăng trưởng. PE cao và PE thấp thực ra là vấn đề thị trường đang như thế nào, chứ không phải bản chất cổ phiếu.

Thầy dẫn nghiên cứu Fama-French (được giải Nobel tài chính), trong đó đưa ra ba nhân tố chính. Thứ nhất là Size (vốn hoá lớn hay nhỏ): trong giai đoạn ngắn hạn theo chu kỳ, các công ty lớn tăng trưởng tốt. Nhưng nắm giữ dài hạn nhiều năm, cổ phiếu vốn hoá nhỏ lại cho lợi nhuận tốt hơn. Thứ hai là Value (giá trị): cổ phiếu PE thấp được gọi là cổ phiếu giá trị, cổ phiếu PE cao được gọi là cổ phiếu tăng trưởng. Cách nói chính xác hơn: cổ phiếu giá trị được biểu hiện bởi PE thấp, cổ phiếu tăng trưởng được biểu hiện bởi PE cao. Thứ ba là Momentum do Carhart đưa ra, không thuộc Fama-French: những cổ phiếu đang tăng tốt sẽ có xu hướng tăng tốt trong một chu kỳ tăng trưởng. Áp dụng: thị trường chứng khoán đang tăng thì cổ phiếu đang có tiền vào sẽ tiếp tục có tiền vào.

Kết luận nghiên cứu thực nghiệm: trong giai đoạn thị trường tăng trưởng nóng (do giảm lãi suất, do chu kỳ kinh tế), cổ phiếu PE cao tốt hơn PE thấp. Nhưng trong khoảng thời gian 10 năm hoặc lâu hơn, cổ phiếu PE thấp vượt trội PE cao. PE thấp tăng đều theo năm giống đường thẳng, PE cao tăng rồi giảm rồi tăng nhưng tổng lại không bằng PE thấp. Áp dụng: người giao dịch chọn cổ phiếu PE cao khi điều kiện thị trường ổn định. Lúc thị trường bắt đầu e ngại thì chọn cổ phiếu PE thấp vì những người theo PE thấp tìm kiếm sự an toàn. Size áp dụng cho lựa chọn danh mục dài hạn. Momentum áp dụng cho chuyện định thời điểm. Value áp dụng cho định giá.

Lưu ý cuối phần: đừng dùng con số định giá tuyệt đối. Ai đó viết báo cáo định giá PE/PB ra giá trị 50 thì cũng chỉ để tham khảo, ngày mai nó đã thay đổi.

## Định giá chiết khấu dòng tiền

Trong định giá dòng tiền có ba cách: định giá theo dòng tiền của doanh nghiệp, định giá theo dòng tiền của cổ đông, và định giá theo giá trị còn lại (residual value).

### Định giá theo dòng tiền doanh nghiệp

Doanh nghiệp và cổ đông là hai đối tượng khác nhau. Doanh nghiệp có thể làm ăn có lãi nếu không vay nợ, nhưng nếu vay nhiều thì lợi nhuận từ hoạt động có thể không đủ trả lãi vay. Hai doanh nghiệp cùng mô hình kinh doanh nhưng đòn bẩy tài chính khác nhau thì ông không vay nợ có lợi nhuận tốt hơn ông có vay nợ. Trong điều kiện lãi suất cao, doanh nghiệp vay nợ nhiều dễ vỡ. Trong điều kiện lãi suất thấp, doanh nghiệp vay nợ lại tốt.

Vì vậy nhà đầu tư quan tâm đến ROE (lợi nhuận chia cho vốn chủ sở hữu). Cùng nền tảng vốn, nếu vay nợ thì equity ít. Lợi nhuận sau khi trả lãi chia cho equity nhỏ có thể vẫn cao hơn doanh nghiệp không vay nợ mà toàn bộ là vốn chủ sở hữu. Đó chính là ý nghĩa đòn bẩy. Áp dụng: nếu lãi suất tăng thì phải rời bỏ ngay doanh nghiệp có đòn bẩy tài chính cao. Lãi suất giảm thì lựa chọn doanh nghiệp có đòn bẩy tài chính cao. Đây cũng là lý do QMV xây dựng chỉ số DF (đòn bẩy tài chính) để đánh giá doanh nghiệp nào có DF cao, DF thấp cho dễ lựa chọn. Dù không dùng DF thì nguyên tắc vẫn là: ông vay nợ nhiều, lãi suất tăng thì rời; lãi suất giảm thì tìm đến.

### Định giá theo dòng tiền cổ đông

Tách tiền dành cho doanh nghiệp ra, chỉ tập trung vào dòng tiền dành cho cổ đông. Các dòng tiền cổ đông nhận được: cổ tức, mua lại cổ phiếu, thanh lý tài sản, cổ tức bằng cổ phiếu, tỷ lệ sở hữu.

Đơn giản nhất là cổ tức, cổ tức là thứ duy nhất cổ đông nhận được. Nhưng ở Việt Nam các doanh nghiệp trả cổ tức rất ít. Doanh nghiệp trên thế giới cũng không phải ai cũng trả cổ tức, nhưng giá cổ phiếu vẫn tăng. Đừng nhầm lẫn: dòng tiền dành cho cổ đông (ví dụ cổ tức) lớn thì chưa hẳn tốt. Cổ tức cao chưa hẳn là tốt, vì còn phụ thuộc cổ tức đó nếu không trả thì được tái đầu tư tạo giá trị nhiều hơn thế nào. Phương pháp dòng tiền cổ đông nhấn mạnh vào việc cổ đông nhận được gì cụ thể (cổ tức), nhưng cổ tức cao hay thấp không có nghĩa là doanh nghiệp đó tốt, không có nghĩa là doanh nghiệp đó được định giá cao, và doanh nghiệp không trả cổ tức cũng không phải là vô nghĩa.

Dòng tiền cổ đông (như cổ tức) chỉ giúp hiểu giá trị ước lượng từ những dòng tiền thực tế nhận được. Giá trị từ dòng tiền có thể nhận được trong tương lai có thể lớn hơn rất nhiều.

### Giá trị còn lại

Lấy lợi nhuận sau thuế chia cho equity ta có ROE. ROE chỉ có ý nghĩa nếu chi phí của nó thấp hơn. Nếu lợi nhuận không đủ trang trải chi phí, hoặc không đủ trả chi phí cơ hội của việc dùng equity, thì bị coi là bào mòn giá trị cổ đông. Ví dụ ROE 12% hay 20% chưa có ý nghĩa gì cả, cho đến khi biết chi phí vay vốn là bao nhiêu. Giả sử gửi ngân hàng 6%/năm, về nguyên tắc ROE phải cao hơn 6% thì mới tạm có giá trị mới (chưa tính yếu tố rủi ro).

Phương pháp giá trị còn lại: lấy giá trị equity tại thời điểm cuối cùng của chu kỳ trước, cộng với giá trị tăng thêm được tạo ra ở chu kỳ năm kế tiếp, ra giá trị mới. Người ta lấy doanh nghiệp tạo ra trong năm (ví dụ thu nhập) nhưng phải trừ đi chi phí cơ hội. Phần còn lại mới gọi là giá trị tăng thêm.

### Lưu ý chung về ba phương pháp

Gọi là "giá trị thực" nhưng thực tế không phải giá trị thực. Công thức dòng tiền có quá nhiều biến số. Tử số là cash flow, mẫu số là r (chi phí vốn). Cash flow tương lai không biết, r phụ thuộc lãi suất chính sách và mặt bằng lãi suất thị trường vốn thay đổi hàng năm. Gọi là "giá trị thực" chỉ là tên gọi của phương pháp, không phải giá trị thực. Kể cả định giá dòng tiền cũng không nên dùng như giá trị tuyệt đối, giống hệt PE, PB.

Định giá không phải toán học, dù giỏi toán thì làm nhanh. Quan trọng là giả định về các biến số. Trong phương pháp so sánh, lựa chọn cổ phiếu so sánh khác nhau thì giá trị ra cho cổ phiếu mình quan tâm cũng khác nhau. Trong định giá dòng tiền, thay đổi tỷ lệ r một chút thôi thì định giá thay đổi rất nhiều. Thay đổi đó không ai dạy được, tự mỗi người quyết. Nhiều sinh viên ra trường cứ để tỷ lệ r là 10% hoặc 12% vì sách lấy ví dụ như vậy, hỏi tại sao thì trả lời vì sách nói. Mỗi người có quan điểm rất khác nhau về giả định.

## Mối liên hệ giữa các phương pháp

Thầy chứng minh bằng công thức rằng bản chất so sánh và dòng tiền là một. Xét công thức định giá theo dòng cổ tức rút gọn: giá trị cổ phiếu = (DPS × (1 + g)) / (r - g), trong đó DPS là Dividend Per Share (cổ tức trên mỗi cổ phiếu), g là tỷ lệ tăng trưởng, r là tỷ lệ lợi suất yêu cầu (phụ thuộc lãi suất). Lãi suất tín phiếu tăng giảm thì r tăng giảm. g giống như tốc độ tăng trưởng GDP, tỷ lệ tăng trưởng thường xuyên hợp lý.

Chia cả hai vế cho EPS (Earnings Per Share) thì vế trái ra PE ratio. Vế phải: DPS chia EPS chính là payout ratio (tỷ lệ trả cổ tức). Vậy PE hoàn toàn có thể ước lượng dựa vào số liệu tài chính. Nếu payout ratio không đổi, PE cao hay thấp phụ thuộc vào r. Nếu payout ratio cao thì PE cao. Từ đây giải thích tại sao công ty trả cổ tức lớn thì PE tăng lên, tức giá trị tăng lên khi các nhân tố khác không đổi. Khi công ty trả cổ tức nhiều thường được kỳ vọng làm ăn tốt thì mới trả được cổ tức cao, nên PE tăng, giá tăng. PE cao chưa hẳn xấu vì không biết cao do g tăng hay r giảm.

Chia cả hai vế cho Book Value Per Share, dựa trên nguyên tắc tỷ lệ tăng trưởng bằng tỷ lệ giữ lại lợi nhuận nhân với ROE. Nếu tỷ lệ trả cổ tức nhiều thì tỷ lệ tăng trưởng thấp, tức công ty trả cổ tức nhiều chưa hẳn tốt. Nếu ổn định ở mức cao thì tốt, nhưng tự nhiên trả nhiều hơn thì tỷ lệ tăng trưởng kém đi, nghĩa là công ty đã hết khả năng tăng trưởng. Kết quả khi chia cho Book Value Per Share ra công thức cho P/B. P/B tăng lên phụ thuộc ROE và r. ROE cao và r thấp thì tốt. ROE cao và r cao thì chưa chắc tốt. Trong giai đoạn tăng trưởng mạnh, thị trường tốt thì g cao là tốt. Trong điều kiện tăng trưởng yếu thì g cao lại không tốt.

Kết luận: PE, PB bản chất là so sánh, nhưng kỳ vọng liên quan đến PE, PB bản chất là kỳ vọng về doanh nghiệp. Hiểu lúng thì chỉ cần tập trung vào PE là đủ, hoặc PB. Để đánh giá cổ phiếu, chỉ cần nhìn vào PE hoặc PB, một trong hai là đủ. Với Việt Nam doanh nghiệp ít trả cổ tức, phần lớn giống nhau, ai trả cổ tức thì tốt hơn một chút. ROE cao thường là những doanh nghiệp tốt hơn về định giá.

Hai kết luận quan trọng: thứ nhất, đừng quên ngày mai định giá đã khác. Thứ hai, mặc dù có nhiều phương pháp, bản chất kỳ vọng thị trường qua các phương pháp đều tương quan với nhau.

## Ví dụ và ứng dụng: Thực hành trên Blackbox với PVD và BSR

Phần thực hành dùng dữ liệu từ Vietstock, thực hiện định giá hai mã ngành dầu khí là PVD và BSR. Thời điểm thực hiện: cuối quý 3 năm 2024, ngày 15/11/2024.

Trước khi vào phần định giá, thầy nhắc cách đọc tín hiệu dòng tiền trên Blackbox: cổ phiếu có dòng tiền uốn lên xuống theo cách làm trên Blackbox thì là vùng uốn trên 20 và uốn dưới 30. Các ký hiệu T+ swing, T+ consolidation nói rằng cơ hội nhanh, tiền đang uốn nhanh, hoặc uốn dài, hoặc uốn vừa. Đây chỉ là cách tạo ra tổ hợp filter từ dữ liệu có sẵn, là sự lựa chọn chứ không phải tiền tăng trong ngày.

### Định giá PVD bằng PE so sánh với chính nó trong quá khứ

Số liệu PVD tại ngày 15/11/2024: EPS 4 quý gần nhất = 1.216đ, giá = 23.200đ. PE hiện tại = 23.200 / 1.216 ≈ 19,24. PE các quý trước trong quá khứ: 22, 25, 27, 33. Min PE trong quá khứ là 22,96 và max PE là 27,46.

Kết luận: PVD đang có PE thấp nhất trong lịch sử quan sát được (19,24 so với min cũ 22,96). Nhân EPS với khoảng PE quá khứ: định giá hợp lý của PVD theo phương pháp này nằm trong khoảng 27-33 (1.216 × 22,96 ≈ 27.929 và 1.216 × 27,46 ≈ 33.391). So với giá hiện tại 23.200 thì nhìn vào quá khứ, PVD đang rất rẻ. Tuy nhiên định giá này còn có thể rẻ nữa, có thể mua ở vùng tốt hơn, nhưng trong ví dụ này thì PVD tỏ ra ổn.

### So sánh PE PVD với PE ngành dầu khí

PE ngành dầu khí hiện tại: 7,4 (theo phương pháp cộng rồn) hoặc 7,7 (tính theo trung bình). PVD có PE 19,24. So với chính nó trong quá khứ thì PVD rẻ, nhưng so với ngành thì PVD đắt. Đây là sự phụ thuộc vào cách nhìn nhận, không có câu trả lời duy nhất.

### Định giá BSR bằng PE

Số liệu BSR: EPS 4 quý gần nhất = 961đ, giá hiện tại 18.900đ. Min PE BSR trong quá khứ: 6,78. Max PE BSR: 25,76 và 20,7. Khi tính cụ thể: BSR cao giá hơn so với chính nó và cao giá hơn so với ngành.

So sánh PVD và BSR: PVD thì thấp giá so với chính nó nhưng cao giá so với ngành. BSR thì cao giá hơn so với chính nó và cao giá hơn so với ngành. Nhìn ông PVD là ổn hơn so với BSR nếu đơn thuần về mặt định giá. Nếu đang cân nhắc giữa PVD và BSR thì sẽ có xu hướng lựa chọn PVD vì tiềm năng tăng giá của PVD cao hơn BSR về mặt định giá.

Thầy lưu ý thêm: nếu một tuần sau PVD tăng lên 30k và BSR giảm về 10k thì tình thế sẽ khác. Định giá thay đổi hàng ngày, hàng giờ. Làm ra định giá, tính ra con số, bản chất là để lựa chọn quyết định tại thời điểm đó, chứ không phải để dính vào con số định giá.

### Định giá dòng tiền BSR

Công thức cơ bản: giá trị = cash flow × (1 + g) / (r - g). Thầy dùng lợi nhuận sau thuế (lãi cơ bản trên mỗi cổ phiếu) thay cho cash flow. EPS 4 quý gần nhất của BSR = 961đ. Thầy nhắc con số này lấy cho dễ tính, bản chất gặp vấn đề khi doanh nghiệp thay đổi vốn chủ sở hữu thì EPS bị ảnh hưởng.

Tính r theo CAPM (Capital Asset Pricing Model): r = rf + beta × (Rm - Rf). Thành phần rf (risk free rate) lấy lợi suất trái phiếu chính phủ 10 năm, khoảng 2,8%. Beta 52 tuần của BSR: 1,13. Rm - Rf (market premium): thống kê chỉ số Việt Nam hơn 20 năm, kỳ vọng thị trường 10-12%, lấy 10,5%. r của BSR: khoảng 14%.

Tính g: lấy tăng trưởng kinh tế Việt Nam = 6,92%.

Kết quả: giá trị BSR = 961 × (1 + 6,92%) / (14% - 6,92%) = 13.266đ.

### Định giá dòng tiền PVD

Cùng phương pháp, chỉ thay EPS và beta. Beta PVD = 1,36. EPS PVD = 1.216đ. Kết quả: giá trị PVD = 12.691đ.

Cả hai mã đều có giá hiện tại cao hơn định giá dòng tiền: PVD giá 23.200 so với 12.691 (cao hơn nhiều), BSR giá 18.900 so với 13.266 (cao hơn ít hơn). Vậy BSR cao giá hơn ít hơn so với PVD.

### Lưu ý về tính đồng nhất khi so sánh

Khi so sánh hai doanh nghiệp, các giả định phải giống nhau. Nếu dùng dòng tiền cho BSR mà dùng PE ngành cho PVD thì so sánh khập kiểm, không đồng nhất, không cùng kiểu. Khi thống nhất được các chỉ số thì bản chất khác nhau chỉ ở beta. Ông nào rủi ro hơn, biến động nhiều hơn, có ý nghĩa. Ông nào làm ăn tốt hơn có ý nghĩa trong câu chuyện định giá. Thầy khuyên hiểu để dùng thay vì hiểu để làm: QMV đang phát triển phần định giá, tìm kiếm cổ phiếu có định giá thấp cao theo các phương pháp khác nhau, và việc cần làm là so sánh phần trăm giữa các mã, không phải dính vào con số tuyệt đối.

### Ví dụ VCB ngân hàng

VCB định giá theo dòng tiền cho con số rất cao, nhưng thầy nhấn mạnh con số đó hoàn toàn không có ý nghĩa. Nó chỉ đảm bảo rằng VCB làm ăn rất tốt so với mức lợi suất yêu cầu chung của thị trường. Nếu định giá theo PE thời vụ thì VCB lại thấp. Về mặt lâu dài, bỏ tiền vào VCB là ổn theo kiểu dòng tiền, giá trị thời gian của tiền. Nhưng người nhìn theo kiểu chuyến định lần này ăn được bao nhiêu thì lại không yêu thích VCB.

Khi định giá hiện tại cao quá so với định giá so sánh, nghĩa là cao giá quá. Khi định giá dài hạn hấp dẫn, ngân hàng này vẫn ổn hơn các ngân hàng khác cùng ngành. Giá cổ phiếu có thể tăng giảm, nhưng chọn ông nào thì lựa chọn lại ông đó. VCB có thể cao giá ngắn hạn, nhưng dài hạn vẫn ổn.

### Thông báo cuối buổi

Sau khi hoàn thiện định giá, thầy dự kiến tháng 12 sẽ làm lại toàn bộ các vấn đề liên quan tới định giá, tín hiệu và dòng tiền để có số liệu được xử lý và ra quyết định. Bài học này giúp hiểu định giá được tính như thế nào và có ý nghĩa gì khi sử dụng.

## Điểm thầy nhấn mạnh

Thứ nhất, đừng dùng định giá như giá trị tuyệt đối. Ngày mai định giá đã khác. Định giá chỉ dùng để so sánh tương đối giữa hai cổ phiếu đang cân nhắc, không phải tìm đến con số cụ thể.

Thứ hai, PE cao chưa hẳn xấu, PE thấp chưa hẳn tốt. Phụ thuộc điều kiện thị trường. Trong giai đoạn tăng trưởng nóng, PE cao tốt hơn. Trong giai đoạn dài hạn 10 năm trở lên, PE thấp vượt trội.

Thứ ba, cổ tức cao chưa hẳn tốt. Nếu ổn định ở mức cao thì tốt, nhưng tăng cổ tức tự nhiên đồng nghĩa tỷ lệ tăng trưởng kém đi, nghĩa là công ty đã hết khả năng tăng trưởng.

Thứ tư, hai phương pháp so sánh và dòng tiền bản chất là một. Nếu hiểu là một thì chỉ cần lựa chọn biết một thứ thôi, biết nhiều quá lại rối.

Thứ năm, định giá không phải toán học, quan trọng là giả định. Trong dòng tiền, thay đổi r một chút thôi thì định giá thay đổi rất nhiều. Phần thay đổi này tự mỗi người quyết.

Thứ sáu, khi so sánh hai doanh nghiệp, các giả định phải thống nhất. Không thể dùng phương pháp này cho doanh nghiệp này mà phương pháp khác cho doanh nghiệp kia.

## Bối cảnh thị trường lúc giảng (11/2024)

Tại thời điểm bài giảng ngày 15/11/2024, thầy nhận xét thị trường đang xuống. Thầy khuyên học viên nên đầu tư thời gian vào việc học vì khi thị trường xuống thì mới cần học, còn khi thị trường lên thì lại thấy không cần học nữa.

Về công cụ và AI: thầy nói đang tham gia khóa học về AI, tự đánh giá chưa thành thạo để hướng dẫn. Tuy nhiên thầy đang dùng AI (Co-Pilot) để viết lại bộ code tín hiệu dựa trên diễn giải bằng lời nói. Thầy nhấn mạnh AI rất hữu ích như trợ lý thông tin, nhưng người dùng phải có kiến thức lập trình nền tảng (ví dụ Pascal, Visual Basic, Python) thì mới sửa lỗi được.

Về lịch học: từ thời gian tới, thầy chuyển chương trình Bia Hơi Vỉa Hè buổi tối sang Trà Chiều chủ nhật để có nhiều thời gian hơn. Từ nay các buổi học sẽ thiên về thực hành. Học viên có nhu cầu về nội dung kinh tế, tài chính, chứng khoán theo chủ đề thì đề xuất trong phần hỏi đáp kiến thức.

## Hỏi đáp

Về số liệu EPS của BSR: học viên thắc mắc thầy có điện nhầm earning per share của BSR không. Thầy trả lời nếu thầy có nhầm thì khi làm lại có thể làm theo cách đó, vì thầy làm trực tiếp hướng dẫn nên có thể nhầm. Thầy nhắc cả khi sinh viên thực hiện ở Đinh Cần ở Anh cũng gần như làm trực tiếp như vậy, trong quá trình thực hiện có thể có nhầm lẫn. Nhưng sự nhầm lẫn chỉ là về số liệu, hoàn toàn có thể làm lại.

Về template định giá: học viên hỏi thầy có thể cho xin template định giá không. Thầy sẽ lấy file đang dùng hôm nay upload lên nhưng trình bày không chuẩn lắm, quan trọng là hiểu được làm thế nào.
