# Bai 4 - Su dung phan tich ky thuat don gian

Bài cuối trong chuỗi 4 bài HP0, quay ngày 09/06/2024. Thầy dạy cách đọc và vận dụng phân tích kỹ thuật ở mức cơ bản, trọng tâm là tư duy đằng sau các công cụ chứ không phải nhớ từng mẫu hình. Sáu nội dung chính: đọc đồ thị nến, quan hệ cung cầu qua giá và lượng, hỗ trợ - kháng cự - đường xu hướng, chỉ số kỹ thuật, các mẫu hình thường gặp, và khoảng trống (gap). Bài không có khuyến nghị mua bán cụ thể và không có phần hỏi đáp của học viên.

## Cách đọc đồ thị nến

Thầy dùng đồ thị hình nến thay vì các dạng đồ thị khác, vì nến vừa cho người mới vừa có giá trị với người lâu năm. Mỗi cây nến thể hiện một phiên giao dịch: thân nến là hình chữ nhật, hai bóng nến ở trên và dưới thể hiện giá cao nhất và giá thấp nhất trong phiên. Nến xanh tức là giá đóng cửa cao hơn giá mở cửa; nến đỏ là giá đóng cửa thấp hơn giá mở cửa.

Cách đọc quan trọng nhất không phải là nhìn giá cao - giá thấp - giá mở - giá đóng, mà là nhìn độ dài cây nến như một cuộc chiến giữa bên mua và bên bán. Một cây nến xanh dài nghĩa là bên mua đã kéo giá từ dưới lên trên một đoạn dài, tức bên mua thắng thế rõ rệt. Cây nến đỏ dài thì ngược lại, bên bán thắng. Độ dài cây nến phản ánh mức độ nghiêm trọng của trận đánh trong phiên đó.

Có những phiên mà giá mở cửa và giá đóng cửa gần như bằng nhau, thân nến rất hẹp, nhưng bóng nến trên hoặc dưới lại dài. Loại nến này cho thấy cuộc chiến rất căng thẳng, hai bên giằng co, không rõ bên nào thắng. Nếu bóng dưới dài, nghĩa là dù cuộc chiến cân bằng nhưng nỗ lực của bên mua đẩy giá lên từ vùng thấp là lớn hơn.

Một cây nến đứng riêng chưa nói lên điều gì. Ý nghĩa chỉ xuất hiện khi xét trong chuỗi nến và xu hướng trước đó. Trong một xu hướng tăng mà xuất hiện cây nến thân rất hẹp, thường là dấu hiệu cần suy nghĩ thêm, vì bên mua đang mất thế.

Khi hai cây nến đứng cạnh nhau: nếu cây trước là nến đỏ thân hẹp (cuộc chiến không rõ thắng thua) và cây sau là nến xanh dài bao phủ hoàn toàn cây trước, đó là dấu hiệu bên mua đã khẳng định thế. Ngược lại, một cây nến đỏ dài xuất hiện sau chuỗi nến xanh thân hẹp là cảnh báo: bên bán đang thắng thế hoàn toàn.

Khi ba cây nến đứng cạnh nhau mà tổng thể tạo thành một cây nến dài, xu hướng trước đó là xu hướng tăng mạnh. Nhưng nếu sau đó xuất hiện thêm một cây nến dài theo hướng ngược lại thì rất nguy hiểm, vì bên bán đã thắng hoàn toàn. Nói cách khác, đừng cố nhớ tên mẫu hình ba nến, hãy hiểu diễn biến giá và lượng đằng sau.

Một lưu ý quan trọng: cây nến có thể bị làm giả, nhất là với cổ phiếu nhỏ. Có trường hợp chỉ 1 đến 10 cổ phiếu khớp lệnh trần ngay đầu phiên, tạo cây nến xanh dài, nhưng cả phiên sau giá giảm dần. Hoặc ngược lại, khớp 1-2 lệnh đầu phiên rồi giá giảm, tạo cây nến đỏ dài trong khi thực chất bên mua đang gom. Vì vậy luôn phải kết hợp với diễn biến trong phiên, đặc biệt là khối lượng tại các điểm quan trọng: khối lượng cao hay thấp, chỉ 10 cổ phiếu hay nhiều hơn nhiều. Nếu khối lượng quá nhỏ, cây nến đó chỉ là nhiễu.

## Quan hệ cung cầu qua giá và lượng

Nguyên lý cơ bản: cầu lớn hơn cung thì giá tăng, cung lớn hơn cầu thì giá giảm. Nhưng quan trọng hơn là phải hiểu ai quyết định khối lượng giao dịch.

Trong xu hướng tăng: nếu ai cũng kỳ vọng giá còn tăng, người mua nhảy vào mua, người bán giữ cổ phiếu không chịu bán. Lúc đó khối lượng giao dịch phải thấp, vì người bán quyết định có bán hay không. Khi giá tăng mà khối lượng cũng tăng lên, đó là dấu hiệu người bán bắt đầu chịu bán ra, không phải dấu hiệu dòng tiền đang mạnh một chiều. Nếu khối lượng bất thường tăng đột biến trong một xu hướng tăng, cần cẩn trọng, vì khả năng cao là người bán đang bán ra nhiều.

Trong xu hướng giảm: ngược lại, người mua quyết định có mua hay không. Khi giá giảm mà khối lượng giảm, nghĩa là người mua đứng ngoài, không mua. Khối lượng thấp trong xu hướng giảm cho thấy người bán đang bán nhưng không có ai hứng.

Tóm lại: khối lượng trong xu hướng tăng phản ánh quyết định của người bán, khối lượng trong xu hướng giảm phản ánh quyết định của người mua. Hiểu được điều này thì đã hiểu được phần lớn diễn biến giá và lượng trên thị trường.

## Hỗ trợ, kháng cự và đường xu hướng

Hỗ trợ là mức giá thấp trước đó, kháng cự là mức giá cao trước đó. Khi giá trở lại vùng giá thấp trước đó, người ta có tâm lý mua vào vì nghĩ rẻ, gọi là hỗ trợ. Khi giá lại vùng giá cao trước đó, người ta có tâm lý bán ra, gọi là kháng cự. Đặc điểm quan trọng là người mua thường mua sớm hơn một chút, nên đáy sau có thể cao hơn đáy trước.

Lưu ý quan trọng: hỗ trợ và kháng cự không phải là một đường chính xác, mà là một vùng, vì tâm lý luôn có sai số. Đừng bao giờ nghĩ rằng giá phải giảm đúng bằng mức hỗ trợ rồi mới bật lên, hoặc phải tăng đúng bằng mức kháng cự rồi mới giảm. Nếu giá chưa tới mức mà đã quay đầu thì rất nguy hiểm, vì hàm ý nhiều người tin rằng giá không thể về tới vùng cũ. Ngược lại, nếu giá vượt qua mức cũ thì hàm ý thị trường vẫn suy nghĩ tích cực.

Tại các vùng hỗ trợ và kháng cự, cần quan sát diễn biến khối lượng. Dù khối lượng nhỏ, nó vẫn cho thấy mức độ quan tâm của thị trường tại vùng đó. Hỗ trợ và kháng cự thường phát huy tác dụng tốt nhất khi thị trường đi ngang, không rõ xu hướng.

Khi thị trường có xu hướng rõ ràng, hỗ trợ và kháng cự không còn là đường nằm ngang nữa mà trở thành đường xu hướng. Đường xu hướng tăng nối các đáy tăng dần, đường xu hướng giảm nối các đỉnh giảm dần.

Nguyên tắc xu hướng tăng: đỉnh sau cao hơn đỉnh trước, đáy sau cao hơn đáy trước. Nguyên tắc xu hướng giảm: đỉnh sau thấp hơn đỉnh trước, đáy sau thấp hơn đáy trước. Bất cứ điều gì làm thay đổi hai nguyên tắc này thì xu hướng đã thay đổi. Để xác định một xu hướng cần ít nhất hai đáy, đến đáy thứ ba mới bắt đầu có cơ sở khẳng định. Tương tự với đỉnh.

Khi xu hướng đã thay đổi thì cần nghĩ ngay đến việc xu hướng đã thay đổi, đừng chủ quan giữ quan điểm cũ. Việc nhận ra sớm xu hướng thay đổi giúp tránh sai lầm khi cố ép thị trường đi theo hướng mình muốn.

## Chỉ số kỹ thuật

Phân tích kỹ thuật có cả ngàn chỉ số, nhưng thực chất chỉ có hai nhóm lớn.

Nhóm thứ nhất là nhóm dao động được chuẩn hoá (oscillator), gồm các chỉ số như RSI, CCI. Đặc điểm là chỉ số giao động quanh một mức được chuẩn hoá: ví dụ RSI chuẩn hoá ở mức 70 và 30, vùng trên 70 là quá mua, dưới 30 là quá bán. CCI cũng được chuẩn hoá để giao động quanh một mức. Nhóm này phản ánh sức mạnh của xu hướng, có tính chất lý tính, có thể dự báo, và thường phát huy tác dụng tốt nhất khi thị trường đi ngang.

Nhóm thứ hai là nhóm trung bình động (moving average), ví dụ đường MA trên đồ thị. Nhóm này không được chuẩn hoá mà giao động quanh một mức giá. Đặc điểm là mang tính chất nhận biết cái đang diễn ra, lạc hậu so với nhóm oscillator, và thường phát huy tác dụng tốt nhất khi thị trường có xu hướng rõ ràng. Trong xu hướng rõ, đường trung bình động hoạt động như đường hỗ trợ hoặc kháng cự động.

Thầy nhấn mạnh: biết nhiều chỉ số không tốt bằng thông thạo một đến hai chỉ số. Nếu đã chọn được chỉ số phù hợp thì phải hiểu nó được tính như thế nào. Khi dùng chỉ số, không nên dùng nó như một chỉ số đứng yên mà phải dùng nó trong sự vận động với các mô hình khác và với diễn biến giá.

Một cách sử dụng phổ biến là phân kỳ (divergence). Phân kỳ xảy ra khi giá và chỉ số di chuyển ngược chiều nhau. Ví dụ: giá tăng nhưng chỉ số sức mạnh xu hướng lại giảm, nghĩa là xu hướng tăng đang yếu dần, cần cẩn trọng. Ngược lại, giá giảm ít nhưng chỉ số sức mạnh giảm mạnh có thể tạo ra phân kỳ dương, là điểm có thể cân nhắc vào. Tuy nhiên phân kỳ chỉ là dấu hiệu nghi ngờ, không phải tín hiệu bán ngay. Khi nghi ngờ thì phải quan sát thêm các yếu tố khác.

Một nguyên tắc quan trọng: đừng bao giờ cố ép một mô hình theo mong muốn của mình. Nếu mô hình không xác nhận, phải chấp nhận rằng xu hướng hiện tại vẫn đang tiếp diễn.

## Mẫu hình kỹ thuật

Có rất nhiều mẫu hình, cả mẫu hình tiếp diễn lẫn mẫu hình đảo chiều. Thầy lấy ví dụ mẫu hình phễu giảm `[?mẫu hình nêm giảm / falling wedge]` để giải thích cách đọc.

Trong mẫu hình phễu giảm, xu hướng trước đó là giảm, đáy sau thấp hơn đáy trước và đỉnh sau thấp hơn đỉnh trước, nhưng đoạn phễu lại càng về sau càng hẹp, sức mạnh bên bán yếu dần. Đáy sau không còn thấp hơn đáy trước nhiều nữa, dù đỉnh vẫn thấp hơn. Như vậy sức mạnh bên bán đang giảm dần trong khi bên mua kiên định hứng chịu. Khi khối lượng tại điểm đáy phễu lớn, đó là dấu hiệu bên mua đang thắng thế và mẫu hình này gợi ý xu hướng tăng. Vì vậy thầy thường coi phễu giảm là mẫu hình tăng chứ không phải giảm, vì quan tâm diễn biến tại đoạn phễu hơn là xu hướng trước đó.

Thầy nhấn mạnh một lần nữa: đừng nhớ tên mẫu hình như nhớ tên cờ, hãy hiểu logic giá và lượng đằng sau. Ví dụ mẫu hình hai đỉnh, vai đầu vai, hai đáy - tất cả bản chất đều là vấn đề kháng cự và hỗ trợ. Kháng cự test ba mươi lần thì cũng vẫn là kháng cự, dù có tên gọi khác. Vai đầu vai ngược hay hai đáy thì bản chất vẫn là vấn đề hỗ trợ.

Nguyên tắc chung: khi giá cố gắng vượt qua mức kháng cự mà không thành công, đó là dấu hiệu nguy hiểm. Khi giá không rơi xuống khỏi mức hỗ trợ nhiều lần, đó là dấu hiệu đáng mừng.

## Khoảng trống (gap)

Gap là khoảng trống giá giữa hai phiên liên tiếp. Có bốn loại gap phổ biến, mỗi loại cần hiểu khác nhau.

Gap bình thường xảy ra khi thị trường đi ngang, ít giao dịch, không có tin tức mới, nhiều người không quan tâm đến thị trường. Loại gap này thường được lấp lại bởi các phiên sau, vì không có lý do để giá duy trì khoảng trống. Cần tránh nhầm gap bình thường với các loại gap khác.

Gap hết hơi (exhaustion gap) xảy ra khi thị trường đã tăng điểm rất lâu, khối lượng giao dịch bắt đầu tăng và có dấu hiệu phân phối. Nếu một ngày xuất hiện gap mà không có tin tức mới nào, xu hướng cũ vẫn là xu hướng cũ, thì nhiều khả năng đó là gap hết hơi, giống như nỗ lực cuối cùng nhưng không có gì hỗ trợ. Để xác định, cần trả lời ba câu hỏi: có tin tức gì mới không, tiền có vào không, tâm lý thế nào.

Gap đột phá xảy ra ở giữa một xu hướng tăng, không phải ở đỉnh. Tức là trước đó thị trường đã đạt mức tăng trưởng tương đối nhưng vẫn còn dư địa. Khi ba câu hỏi nêu trên có câu trả lời tương đối tích cực thì khả năng cao xuất hiện gap đột phá. Trước gap đột phá thường có giai đoạn tích luỹ hay củng cố. Gap đột phá xuất hiện ở giữa xu hướng tăng chứ không phải ở cuối.

Gap tiếp diễn (run away gap) xuất hiện ở đầu một xu hướng mới, sau khi xu hướng cũ đã kết thúc, và thường đi kèm khối lượng giao dịch tăng nhanh và tăng mạnh. Loại gap này ám chỉ một xu hướng mới có thể hình thành. Tại thời điểm bài giảng (06/2024), thầy cho biết kỳ vọng khối lượng giao dịch phải tăng mạnh thì mới có thể tạo ra xu hướng mới, còn nếu chưa đạt được điều đó thì diễn biến hiện tại vẫn mang tính chất ngắn hạn, chưa thể nhận diện được xu hướng rõ ràng.

## Năm câu hỏi để xây dựng chiến lược đầu tư

Phần cuối bài, thầy tổng kết bốn buổi học HP0 bằng năm câu hỏi mà nhà đầu tư cần tự trả lời.

Câu hỏi thứ nhất: đang ở đâu trong chu kỳ kinh tế, tâm lý và thị trường. Chu kỳ chứng khoán bao giờ cũng đi trước chu kỳ kinh tế nhưng không nhất thiết phải bám sát. Có khi nền kinh tế còn đang tăng trưởng nhưng thị trường chứng khoán đã kết thúc tăng trưởng và bước vào giai đoạn đi ngang. Nếu chu kỳ kinh tế tốt và đang ở giai đoạn tăng trưởng, có quyền kỳ vọng chu kỳ thị trường chứng khoán tăng có thể kết thúc nhưng chu kỳ đi ngang theo hướng tốt lên vẫn có thể tương đồng với thời kỳ phát triển ở mức cao của nền kinh tế.

Câu hỏi thứ hai: cần có danh sách cổ phiếu và biết cổ phiếu nào phù hợp với giai đoạn nào. Nếu là nhà đầu tư theo dòng tiền, hãy chọn cổ phiếu theo tiêu chí liên quan đến rủi ro. Nếu là nhà đầu tư giá trị, hãy quan tâm cổ phiếu được phân chia theo nhóm ngành.

Câu hỏi thứ ba: phương pháp định giá nào thích hợp, định giá cổ phiếu theo tương đối, theo thị trường hay theo định giá tuyệt đối. Mỗi phương pháp định giá chỉ đúng cho một số loại doanh nghiệp. Ví dụ doanh nghiệp bất động sản thường dùng giá trị tài sản hay NAV để định giá. Với doanh nghiệp sản xuất thường xuyên, có doanh thu, có chi phí mua bán, thì các phương pháp như P/E, P/B hay chiết khấu dòng tiền có thể sử dụng được. Trong bài viết, thầy trình bày phương pháp Blackbox và P/E vì đó là phương pháp phổ biến mà nhiều người dùng. Nếu dùng P/E và P/B thì chỉ nên so sánh các công ty trong cùng ngành, so sánh công ty ở các ngành khác nhau thì không có ý nghĩa.

Câu hỏi thứ tư: khi dùng phân tích kỹ thuật thì tín hiệu nào là phù hợp, tin vào mô hình nào, chỉ số nào. Khi sử dụng phải kiểm tra tất cả các tín hiệu kỹ thuật xem có ủng hộ việc mua vào hay bán ra hay không, đồng thời luôn chú ý đến diễn biến của yếu tố thị trường và yếu tố cơ bản. Phân tích kỹ thuật là công cụ phát triển bởi các nước phương Tây, dùng cho giao dịch trong ngày như phong phòng, hàng hoá, ngoại tệ, vì trong khoảng thời gian ngắn các yếu tố cơ bản chưa kịp thay đổi, lúc đó phân tích kỹ thuật phản ứng tâm lý và có khả năng đúng cao hơn.

Câu hỏi thứ năm: đang hưng phấn hay lo sợ. Điều này cực kỳ quan trọng, vì khi đang hưng phấn hoặc lo sợ thì quyết định thường sai. Hãy luôn tự trả lời câu hỏi này trước khi ra quyết định.

## Điểm thầy nhấn mạnh

Phân tích kỹ thuật có hàng ngàn chỉ số và mẫu hình, nhưng bản chất chỉ có hai nhóm chỉ số: dao động chuẩn hoá và trung bình động, và mỗi mẫu hình thực chất là một dạng hỗ trợ hoặc kháng cự. Biết nhiều không bằng thông thạo một hai công cụ, hiểu nó được tính như thế nào và biết cách dùng nó trong sự vận động với các yếu tố khác.

Cây nến là hình ảnh của một cuộc chiến giữa bên mua và bên bán, độ dài thân nến phản ánh mức độ nghiêm trọng của trận đánh, bóng nến cho thấy nỗ lực bị đẩy lùi. Và vì cây nến có thể bị làm giả bởi cổ phiếu nhỏ, luôn phải kiểm tra khối lượng giao dịch tại các điểm quan trọng.

Khối lượng trong xu hướng tăng phản ánh quyết định của người bán, khối lượng trong xu hướng giảm phản ánh quyết định của người mua. Khối lượng bất thường tăng đột biến trong xu hướng tăng là dấu hiệu người bán đang bán ra, không phải dòng tiền đang mạnh.

Hỗ trợ và kháng cự là vùng chứ không phải đường, vì tâm lý luôn có sai số. Nguyên tắc xu hướng: đỉnh sau cao hơn đỉnh trước và đáy sau cao hơn đáy trước với xu hướng tăng, ngược lại với xu hướng giảm. Bất cứ điều gì làm thay đổi nguyên tắc này thì xu hướng đã thay đổi.

Đừng bao giờ cố ép một mô hình theo mong muốn. Nếu mô hình không xác nhận, hãy chấp nhận rằng xu hướng hiện tại vẫn đang tiếp diễn. Và khi ra quyết định, hãy luôn tự hỏi mình đang hưng phấn hay lo sợ, vì nếu đang ở một trong hai trạng thái đó thì quyết định thường sai.
