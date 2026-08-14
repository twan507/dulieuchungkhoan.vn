# V4 2022-11 - 05 - Dinh gia so sanh - Bai giang

Bài giảng thuộc học phần 3, chủ đề định giá doanh nghiệp theo phương pháp so sánh. Bài trình bày 4 cách tiếp cận cụ thể (cùng ngành, cùng nhóm dòng tiền, theo tâm lý, cộng dồn) và 5 bước triển khai chung, kèm ví dụ minh hoạ bằng số. Đây là bài dạy lý thuyết thuần tuý, không có khuyến nghị mua bán cụ thể. Học xong học viên nắm được cách tính và cách đọc kết quả định giá so sánh, đồng thời hiểu vì sao phương pháp này chỉ phản ánh giá trị tại một thời điểm chứ không phải giá trị bất biến. Số liệu ví dụ trong bài lấy từ đầu năm 2024, thầy đã thay tên doanh nghiệp gốc bằng mã QMV để giữ tính chất mẫu.

## Tổng quan hai cách tiếp cận định giá

Có hai cách tiếp cận định giá chính. Cách thứ nhất là định giá so sánh, chỉ trả lời câu hỏi "giá trị hiện tại trông như thế nào" bằng cách so với một chuẩn tại thời điểm định giá. Cách thứ hai là định giá chiết khấu dòng tiền, trả lời câu hỏi "những gì nhận được trong tương lai có giá trị bao nhiêu khi quy về hiện tại", mang tính chất dài hạn hơn.

Trong phương pháp so sánh có hai cách nhỏ. Một là so sánh với các công ty có đặc điểm tương ứng (so ngang tại cùng thời điểm), hai là so sánh với chính công ty đó tại các thời điểm khác nhau trong quá khứ. Cách thứ hai trả lời câu hỏi thị trường sẵn sàng trả giá bao nhiêu cho công ty này trong tương lai, căn cứ vào tình hình trước đó của chính nó.

Định giá dù làm bằng cách nào cũng chỉ có ý nghĩa tại thời điểm định. Ngày mai giá các công ty so sánh thay đổi thì định giá thay đổi, tỷ lệ chiết khấu thay đổi thì định giá chiết khấu dòng tiền cũng thay đổi. Vì vậy không nên tìm ra một con số định giá rồi dùng mãi về sau; con số ấy chỉ đúng một tiếng, một ngày, một tuần, một tháng rồi thay đổi.

## Năm bước định giá so sánh

Bước 1 là chọn doanh nghiệp so sánh phù hợp, thường là cùng ngành hoặc cùng nhóm dòng tiền, có thanh khoản cao. Nếu có quá nhiều doanh nghiệp thì lọc theo quy mô doanh thu để đảm bảo tính đại diện. Khi làm thủ công, chỉ cần 3-5 doanh nghiệp là so sánh được; phương pháp so sánh cả toàn ngành thì cần thuật toán và máy tính.

Bước 2 là tính PE và PB cho từng doanh nghiệp được chọn, đồng thời tính PE và PB của doanh nghiệp muốn định giá.

Bước 3 là tính trung bình PE và PB của các doanh nghiệp so sánh. Cách đơn giản là lấy tổng chia đôi, dễ hiểu và phù hợp với cách thị trường nhìn nhận. Cách chuyên nghiệp hơn là tính theo trọng số vốn hoá hoặc quy mô tài sản.

Bước 4 là tính tỷ lệ PE và PB tương đối của doanh nghiệp theo dõi so với trung bình ngành, thay vì dùng giá trị tuyệt đối. Đây là điểm khác biệt của QMV với phần lớn thị trường.

Bước 5 có hai hướng tiếp cận. Hướng 5a là lấy giá trị cao nhất và thấp nhất trong kỳ quan sát, từ đó tính ra dải giá trị hợp lý (dải dao động từ thấp đến cao). Hướng 5b là lấy trung bình của bốn con số gần nhất, cho ra một con số duy nhất.

## So sánh cùng ngành

Công thức cốt lõi: giá trị của doanh nghiệp bằng EPS nhân với PE trung bình ngành, hoặc book value per share nhân với PB trung bình ngành. Ví dụ, nếu EPS là 5.500 đồng, giá thị trường là 82.500 đồng, PE hiện tại của chính doanh nghiệp đó là 15. Lấy hai doanh nghiệp cùng ngành có PE lần lượt là 12 và 16, PE trung bình ngành bằng (12+16)/2 = 14. Khi đó giá trị thực = 5.500 × 14 = 77 (đơn vị nghìn đồng). So với giá thị trường 82.500 đồng, doanh nghiệp đang cao hơn giá trị thực.

Mấu chốt cần hiểu: bản chất định giá chỉ là so doanh nghiệp A với doanh nghiệp 1 và 2, không có doanh nghiệp nào được khẳng định là đang ở giá trị thực. Nếu doanh nghiệp A đang hợp lý thì 1 và 2 phải hướng về PE 15, chứ không phải A hướng về PE trung bình 14. Thị trường thường chỉ tính trung bình đơn giản, còn người làm chuyên nghiệp phải đưa cả A vào nhóm trung bình.

Có ba loại earnings per share cần biết: loại trong quá khứ (ít chính xác nhất, vì là EPS cuối năm đã công bố), loại trượt (bốn quý gần nhất, phản ánh kết quả tới thời điểm hiện tại), và loại dự báo (dựa trên EPS tương lai, khó dự báo nên phần lớn nhà đầu tư nhỏ lẻ không dùng được). Thầy khuyến nghị tập trung vào loại trượt vì phản ánh thông tin tới hiện tại và ai cũng có thể nhìn thấy.

### Ví dụ minh hoạ với QMV

Thầy lấy ví dụ doanh nghiệp QMV (placeholder, số liệu gốc từ HPG đầu năm 2024 nhưng thầy đã thay tên để giữ tính mẫu) so sánh với hai doanh nghiệp cùng ngành QMV-I1 và QMV-I2. Tính PE và PB trung bình ngành theo hai cách: không bao gồm QMV, và có bao gồm QMV. Trong trường hợp bao gồm QMV, lấy PE ba doanh nghiệp cộng lại chia 3.

Tại ngày định giá, PE của QMV đang là 127% so với trung bình ngành. Nhìn vào lịch sử, PE tương đối của QMV luôn dao động trong khoảng từ 106% đến 150%. Vậy 127% nằm trong vùng bình thường, không phải cao giá, dù nhìn theo tuyệt đối thì PE cao hơn ngành 27% nghe có vẻ cao.

Khi tính dải giá trị hợp lý: lấy EPS gần nhất của QMV nhân với PE trung bình ngành, rồi nhân thêm với tỷ lệ thấp nhất 1.06 (106%) hoặc cao nhất 1.50 (150%). Kết quả dải giá trị thấp nhất theo PE là 39.076 (đơn vị nghìn đồng, theo ví dụ trên slide). Tương tự với PB, tính theo cùng nguyên tắc.

Theo hướng 5b, trung bình bốn con số tỷ lệ gần nhất là 135%. Tại 127%, QMV thấp hơn trung bình 8%, tức là nằm trong nửa dưới của vùng bình thường chứ không phải cao giá. Mục tiêu hợp lý nằm trong dải trung bình, không phải lấy thấp nhất cộng cao nhất chia đôi.

Tại sao phải dùng tỷ lệ tương đối thay vì tuyệt đối? Vì có những cổ phiếu như Hòa Phát (HPG) thì PE lịch sử luôn thấp, trong khi FPT và SSI thì PE lịch sử luôn cao. Nếu chỉ nhìn PE tuyệt đối thì sẽ kết luận nhầm HPG cao giá và FPT/SSI rẻ, nhưng thực tế nhà đầu tư luôn chuộng mô hình kinh doanh của FPT/SSI hơn nên PE cao là bình thường.

## So sánh cùng nhóm dòng tiền

Cách làm hoàn toàn tương tự so sánh cùng ngành, chỉ khác là chọn doanh nghiệp theo cùng nhóm dòng tiền thay vì cùng ngành. Ví dụ so sánh đầu ngành với nhau, hay các doanh nghiệp có cùng đặc điểm tạo dòng tiền.

Điểm khác biệt duy nhất: khi so sánh cùng nhóm dòng tiền thì không còn câu chuyện có nên bao gồm doanh nghiệp đang định giá vào trung bình hay không, vì đang so sánh với nhóm khác chứ không phải so với chính nó.

Với ví dụ QMV, khi so với nhóm dòng tiền (QMV-C1, QMV-C2, QMV-C3), PE tương đối của QMV lúc này chỉ có 42%, thấp hơn các doanh nghiệp khác. Nhưng nhìn lại lịch sử, QMV luôn luôn thấp hơn nhóm, chỉ có một lần cao nhất là 103%, còn lại phần lớn là nhỏ hơn. Vậy thì 42% nằm trong vùng bình thường 39-65% của QMV, không hề rẻ. Bài học: không dựa vào việc PE thấp hơn mà kết luận rẻ, phải xem trong quá khứ nhà đầu tư có ưa thích nó không.

Thầy cũng nhấn mạnh: với phương pháp này, có khi chỉ cần nhìn con số phần trăm tương đối là đủ kết luận, không nhất thiết phải làm tới các bước tính giá trị cuối. Ngày mai định giá lại thay đổi, việc tính chi tiết ra một con số cụ thể không cần thiết bằng việc quan sát vị trí trong dải lịch sử.

## So sánh theo tâm lý

Tâm lý ở đây nghĩa là so sánh với chính cổ phiếu đó trong quá khứ, tại các giai đoạn thị trường khác nhau. Bốn bước triển khai:

Bước 1, chọn giai đoạn tăng trưởng trước đó của thị trường để xác định diễn biến tâm lý. Có thể chọn một giai đoạn, hai giai đoạn rồi lấy trung bình, hoặc chỉ chọn giai đoạn gần nhất.

Bước 2, tính PE và PB tại các thời điểm: thời điểm bắt đầu đi lên, thời điểm đạt đỉnh, và thời điểm hiện tại. Lưu ý chọn quý phù hợp: nếu ngày quan sát là tháng 10 thì dùng số liệu quý 3; nếu là tháng 9 thì dùng số liệu quý 2, vì người ta chưa biết kết quả quý 3.

Bước 3, tính giá vùng dự kiến: lấy giá giai đoạn hiện tại nhân với PE cao nhất hoặc thấp nhất trong quá khứ, chia cho PE hiện tại. Cách này về bản chất vẫn là so sánh tỷ lệ phần trăm tương đối, không phải PE tuyệt đối.

Nếu đoạn thị trường chọn nằm gọn trong cùng quý, kháng cự và hỗ trợ chính là vùng giá hợp lý, không cần tính thêm.

Bước 4 (cách 2), có thể chọn nhiều vùng rồi lấy trung bình. Ví dụ vùng 1 PE tăng từ 5 lên 6, tức tăng 20%; vùng 2 PE tăng từ 10 lên 11, tức tăng 10%. Trung bình hai vùng là 15%. Với PE hiện tại là 4, tăng 15% thì giá dự kiến khoảng 4,6.

Ví dụ bằng số: giả sử cổ phiếu tăng giá từ 20 lên 30 trong quá khứ, tương ứng PE tăng từ 5 lên 6. Hiện tại PE đang là 4. Nếu cổ phiếu tăng theo cùng kiểu, PE sẽ tăng 20% từ 4 lên 4,8.

Ý nghĩa: phương pháp này trả lời câu hỏi "nếu tăng thì tăng tới bao nhiêu" bằng cách dựa trên các giai đoạn tương tự trong quá khứ. Không phải dự báo tuyệt đối mà là dựa trên tỷ lệ phần trăm tương đối.

## Cộng dồn

Phương pháp cộng dồn giống so sánh cùng ngành nhưng khác ở cách tính PE và PB trung bình. Thay vì tính PE riêng rẽ từng doanh nghiệp rồi lấy trung bình, cộng dồn lợi nhuận sau thuế, cộng dồn vốn chủ sở hữu, cộng dồn vốn hoá của tất cả công ty so sánh lại trước khi tính PE và PB. Lúc này coi toàn bộ doanh nghiệp trong ngành là một ngành duy nhất.

Lưu ý quan trọng: lợi nhuận phải cộng dồn bốn quý gần nhất, không lấy earnings per share của tổng lợi nhuận bốn quý. Vốn chủ sở hữu và vốn hoá lấy tại thời điểm quan sát, không cần cộng dồn.

Cách này cho PE và PB mang tính đại diện ngành cao hơn, hợp lý hơn cách trung bình đơn lẻ. Nhưng đòi hỏi khối lượng tính toán lớn, thường cần máy tính hỗ trợ. Cá nhân thầy không làm thủ công được phương pháp này.

Với ví dụ QMV theo cộng dồn: tại ngày định giá, PE tương đối của QMV là 130%, PB tương đối là 29%. Trong quá khứ, QMV luôn cao hơn ngành nhưng chỉ ở mức 107% (PE) và cao nhất khoảng 6% đến 69% (PB). Như vậy lần này QMV đang cao giá hơn mọi lần trước, tức là tăng quá mức so với ngành.

Tính ra tổng giá trị theo PE và PB, thấp nhất và cao nhất, sau đó chia theo số lượng cổ phần để ra giá mỗi cổ phần. Tuy nhiên thầy nhấn mạnh: đôi khi chỉ cần nhìn tỷ lệ phần trăm là đủ kết luận, không nhất thiết phải tính tới các bước cuối.

Thầy cá nhân ưa thích phương pháp tâm lý hơn vì nó thể hiện sự ưa thích của nhà đầu tư với một cổ phiếu cụ thể, giúp trả lời câu hỏi "nếu cổ phiếu này bị đánh đấm thì tâm lý nó thế nào, nếu không bị đánh đấm thì tâm lý thế nào". Với cổ phiếu ít bị tác động từ bên ngoài, mẫu tâm lý độc lập và đồng nhất hơn, nên phương pháp tâm lý phù hợp. Khi có máy tính hỗ trợ, nên quan sát thêm cả cộng dồn để đánh giá tính hợp lý của giá trị ngành.

## Lưu ý khi sử dụng định giá so sánh

### Chọn hệ số PE hay PB tuỳ ngành

PB thường dùng nhiều hơn với doanh nghiệp mà vốn và tài sản là yếu tố quan trọng (ngân hàng, tài chính, bất động sản). PE được sử dụng rộng rãi hơn, đặc biệt với loại hình kinh doanh tạo dòng tiền là yếu tố quan trọng, không đòi hỏi nhiều vốn. PE gần như dùng được cho tất cả các loại hình doanh nghiệp.

### So sánh đầu ngành với non-leader

Khi định giá cổ phiếu cùng ngành, đừng so cổ phiếu không dẫn đầu ngành với nhau, cũng đừng lấy cổ phiếu dẫn đầu ngành so với nhóm không dẫn đầu. Hai cách này đều lệch.

Cách hợp lý: định giá cổ phiếu dẫn đầu ngành thì so với toàn bộ ngành bằng cách cộng dồn. Định giá cổ phiếu không dẫn đầu (các ông chạy sau) thì so với cổ phiếu dẫn đầu ngành. Cách này còn có thêm ý nghĩa gợi ý: nếu cổ phiếu dẫn đầu ngành đã chạy rồi thì cổ phiếu nào sẽ chạy tiếp theo, dựa trên PB hay PE tương đối so với nhóm đầu ngành.

### So sánh khác ngành theo nhóm dòng tiền

Khi so sánh công ty khác ngành theo nhóm dòng tiền, cố gắng chọn quy mô tương đối giống nhau. Việc so sánh khác ngành giúp gợi ý ngành nào sẽ chạy tiếp theo, trong khi so sánh cùng ngành giúp gợi ý cổ phiếu nào sẽ chạy tiếp theo trong cùng ngành.

### Phương pháp tâm lý và cộng dồn

Định giá theo tâm lý (so với chính nó trong quá khứ) phù hợp với tất cả cổ phiếu. Định giá cộng dồn mang tính đại diện ngành cao hơn, áp dụng cho tất cả cổ phiếu, nhưng cần máy tính hỗ trợ.

### Đừng bị dính vào con số định giá

Định giá thay đổi hàng ngày vì giá thị trường thay đổi. Đừng dùng định giá theo nghĩa tuyệt đối, hãy dùng làm căn cứ so sánh trong ngắn hạn. Thầy khuyên chỉ nên theo một phương pháp thôi cho đỡ phức tạp, và nhớ rằng ngày mai định giá đã khác rồi.

Đối với định giá so sánh, giá trị phụ thuộc vào tình trạng thị trường: thị trường tốt thì định giá tự nhiên cao lên, thị trường xấu thì định giá thấp xuống. Với phương pháp chiết khấu dòng tiền, thị trường tốt thường đi kèm lãi suất thấp, tỷ lệ chiết khấu thấp, định giá cao; thị trường xấu thì lãi suất cao, tỷ lệ chiết khấu cao, định giá thấp.

### Cách ứng dụng sau bài học

Gợi ý ứng dụng: chọn các ngành có dòng tiền tốt (đã có sẵn trên Bót), chọn cổ phiếu cho từng ngành, thực hiện định giá, chọn cổ phiếu có định giá thấp hoặc trong vùng hợp lý. Sau đó dùng kỹ thuật modern portfolio theory (có sẵn trên Bót) để loại bỏ các cổ phiếu có yếu tố tương quan, chọn ra danh mục tối ưu.

Đa dạng hoá danh mục là giảm thiểu rủi ro bằng cách hạn chế nắm giữ cổ phiếu cùng ngành, cùng nhóm rủi ro. Nguyên tắc danh mục là nắm giữ cổ phiếu có đặc tính khác nhau để cái này mất thì cái kia được, nhìn chung vẫn có lợi nhuận khi thị trường ổn định. Tránh mua 3-4 cổ phiếu ngân hàng cùng lúc, hay 3-4 cổ phiếu chứng khoán cùng lúc.

## Bối cảnh thị trường lúc giảng (05/2024)

Tại thời điểm bài giảng được upload (05/2024), thầy nhận định giai đoạn thị trường hiện tại giống với giai đoạn thị trường giảm năm 2018 hơn các giai đoạn khác về tính chất và đặc điểm kinh tế. Nhận định này được dùng làm căn cứ để chọn giai đoạn tăng trưởng trong quá khứ phục vụ phương pháp định giá theo tâm lý.
