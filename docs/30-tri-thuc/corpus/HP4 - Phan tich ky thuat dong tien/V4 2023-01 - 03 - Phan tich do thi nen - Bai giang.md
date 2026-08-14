# V4 2023-01 - 03 - Phan tich do thi nen - Bai giang

Bài này là chủ đề thứ hai trong học phần 4 về phân tích kỹ thuật, dành cho học viên đã nắm bài đầu về kháng cự, hỗ trợ và khối lượng. Nội dung tập trung vào cách đọc một cây nến, cách hiểu hành động giá qua các mẫu hình nến cơ bản, kỹ thuật ghép nến và cách kết hợp nến với các yếu tố kỹ thuật khác khi vào lệnh. Triết lý của QMV mà thầy nhấn mạnh suốt bài là đi vào hiểu bản chất hành động giá thay vì học thuộc tên mẫu hình, vì vậy học xong học viên có thể nhìn bất cứ cây nến nào cũng phán đoán được tâm lý và khả năng đảo chiều, mà không cần nhớ danh sách hàng trăm mô hình. Phần cuối bài có phân tích đồ thị tại thời điểm giảng nên neo mốc thời gian rõ ràng.

## Cấu tạo một cây nến

Một cây nến gồm bốn mức giá trong một phiên giao dịch: giá mở cửa, giá đóng cửa, giá cao nhất và giá thấp nhất. Nến màu xanh thể hiện giá đóng cửa cao hơn giá mở cửa, tức bên mua thắng thế trong phiên đó; nến màu đỏ thì ngược lại, giá đóng cửa thấp hơn giá mở cửa và bên bán thắng thế. Màu sắc chỉ phản ánh ai thắng, không phản ánh sức mạnh tương đối giữa hai bên.

Phần giữa cây nến, tính từ giá mở cửa đến giá đóng cửa, gọi là thân nến. Phần trên và phía dưới thân nến, kéo dài tới giá cao nhất và giá thấp nhất trong phiên, gọi là bóng nến. Có người gọi bóng nến là râu nến, đầu nến hay đuôi nến, các tên gọi khác nhau nhưng về cấu tạo không khác. Toàn bộ từ giá thấp nhất đến giá cao nhất, tức từ chân bóng dưới tới đỉnh bóng trên, thầy gọi là nội giải của một cây nến, phân biệt với thân nến chỉ phần giữa.

Khi nhìn một cây nến, người đọc phải hình dung được câu chuyện trong phiên đó. Một cây nến xanh thân dài, bóng ngắn có nghĩa là bên bán đẩy giá xuống, bên mua nhảy vào kéo lên, hai bên đấu nhau nhưng cuối cùng bên mua thắng và giá đóng cửa ở mức cao. Một cây nến đỏ thân dài thì câu chuyện đảo ngược, bên bán thắng và giá đóng cửa dưới giá mở cửa. Đó là cách hiểu cơ bản nhất trước khi đi vào mẫu hình.

## Ba yếu tố để đọc một cây nến

Để đọc một cây nến, có ba yếu tố cần quan tâm là bóng nến, thân nến và vị trí của thân nến. Ba yếu tố này tương quan với nhau, không xét riêng từng cái.

Về độ dài, thầy tổng quát hoá bằng cách lấy nội giải của cây nến làm 100% rồi chia làm ba phần: một phần ba phía trên, một phần ba phía dưới, và phần 50% ở giữa. Cách chia này tương đồng với tỷ lệ Fibonacci 38%, 50%, 68% mà nhiều người hay dùng, nhưng cách chia ba đơn giản hơn nên không cần nhớ riêng. Khi cần phân tích nhanh, có thể chỉ cần chia đôi nội giải làm hai phần bằng nhau.

Bóng nến dài thể hiện có sự biến động tâm lý lớn trong phiên, tức người tham gia dao động từ lo sợ sang lạc quan rồi ngược lại rất nhanh, nhưng sự thay đổi cơ bản thì không nhiều. Ngược lại, thân nến dài thể hiện có sự thay đổi căn bản, có thể là thông tin mới xuất hiện trong phiên mà người đọc biết hoặc không biết, và sự thay đổi đó mang tính dài hơn so với một cú biến động tâm lý đơn thuần. Vị trí thân nến quan trọng nhất khi thân nến nhỏ, vì lúc đó vị trí nói lên phần nào đang thắng thế. Nếu thân nến đã to thì vị trí tương đối kém quan trọng hơn, vì sức mạnh áp đảo đã rõ.

Có ba trạng thái điển hình minh hoạ. Thứ nhất, thân nến rất lớn so với nội giải, nghĩa là một bên áp đảo, có thể là sau một giai đoạn tiêu cực và có sự thay đổi bước ngoặt về tâm lý, hoặc cũng có thể có yếu tố cơ bản đặc biệt xảy ra. Thầy gọi đây là trạng thái đặc biệt và rất đáng chú ý. Thứ hai, thân nến trung bình, đây là những cây nến bình thường, nếu nó tăng thì là một ngày tăng bình thường, nếu giảm thì là một ngày giảm bình thường, không có gì đặc biệt để quan tâm. Thứ ba, thân nến quá ngắn, gần như bằng không, đây là dạng lưỡng lự mà phần dưới sẽ phân tích riêng.

## Ba mẫu hình nến cơ bản: doji, marubozu, hammer

Thầy giới thiệu hai tình huống đặc biệt mà người đọc cần nắm, dựa trên cấu trúc vừa mô tả.

Tình huống thứ nhất là các mẫu hình doji. Một cây nến doji có thân rất ngắn, gần như bằng giá mở cửa, nhưng độ dài nội giải thì lớn. Độ tin cậy của doji càng cao nếu nội giải càng lớn so với thân. Tuy nhiên, thầy nhấn mạnh một lưu ý quan trọng: nếu gặp một phiên giảm mạnh hoặc tăng mạnh mà cây nến trông giống doji, thì không nên máy móc kết luận đó là lưỡng lự, vì bản chất nó vẫn là một cây nến có xu thế rõ ràng. Nói cách khác, phải xem độ dài nội giải của cây nến đó có lớn hay không, chứ không phải cứ thân ngắn là doji. Khi cây nến ngắn mà không có bóng, bản chất giống với hai trường hợp đặc biệt về thân nến, tức xu thế chắc chắn và khả năng tiếp diễn cao. Nếu đang giảm thì nhiều khả năng giảm tiếp, nếu đang tăng thì nhiều khả năng tăng tiếp.

Vị trí của thân nến trong doji cũng thay đổi ý nghĩa. Nếu thân nằm ở vùng giữa, tức chiếm 1/3 ở giữa cây nến, đó là mô hình lưỡng lự đảo chiều. Nếu xu thế trước đó là tăng thì đó là dấu hiệu đảo chiều đi xuống, và ngược lại. Nếu thân nằm ở phần 1/3 phía trên và xu thế trước đó là giảm, thì khả năng đảo chiều xu thế giả đi lên là rất cao. Nếu thân nằm ở phần 1/3 phía dưới và xu thế trước đó là tăng, thì khả năng đảo chiều xu thế tăng đi xuống cũng rất cao. Cùng một cây doji nhưng vị trí thân khác nhau thì mức độ tin cậy của cảnh báo đảo chiều khác nhau.

Tình huống thứ hai là mẫu hình marubozu. Marubozu là cây nến thân dài, bóng nến rất ngắn hoặc không có, phản ánh sự thay đổi tâm lý hoặc thay đổi cơ bản ngay trong phiên. Theo kinh nghiệm của thầy, nếu marubozu gắn với thay đổi cơ bản thì nó tạo ra xu hướng mới rất nhanh, còn nếu chỉ là tâm lý thì xu hướng chỉ ngắn hạn. Một điểm đáng lưu ý là thay đổi cơ bản không nhất thiết phải là từ xấu chuyển sang tốt. Trong chứng khoán, khi thị trường đã cạn hết tin xấu thì đó cũng là một sự thay đổi cơ bản, vì đơn giản không còn gì xấu hơn. Tương tự, khi đang trong trạng thái hưng phấn thái quá hoặc bi quan thái quá, chính sự cực đoan đó cũng là thay đổi cơ bản. Vì vậy khi gặp marubozu, người đọc phải tự hỏi hôm đó có thông tin mới hay không, có phải là tâm lý thuần tuý hay không, vì câu trả lời quyết định độ bền của xu hướng.

Ngoài hai tình huống trên, thầy còn nhắc tới mẫu hình hammer. Hammer bản chất là cây nến thân ngắn, lớn hơn doji một chút, với thân nến chỉ nhỏ hơn hoặc bằng 1/3 nội giải. Cách xác định bằng mắt là chia nội giải làm ba phần, thấy thân nến chỉ chiếm 1/3 trở xuống thì gọi là hammer. Hammer về cấu trúc là tình huống phổ thông hơn của doji, nên cách dùng giống doji. Trong hammer, màu sắc ảnh hưởng đến độ tin cậy. Nếu xu thế trước là tăng và gặp hammer màu đỏ thì khả năng đảo chiều đáng tin cậy hơn hammer màu xanh, nhưng bản chất vẫn là lưỡng lự đảo chiều, màu sắc chỉ tăng hay giảm độ tin cậy thêm một chút chứ không thay đổi bản chất.

Thầy nhấn mạnh lại quy tắc chung: luôn luôn giả thiết thứ nhất là lưỡng lự, rồi mới xét màu sắc để đánh giá độ tin cậy. Nếu hammer nằm ở 1/3 trên và xu thế trước là giảm thì khả năng đảo chiều tăng là cao nhất, nếu nằm ở 1/3 dưới và xu thế trước là tăng thì khả năng đảo chiều giảm là cao nhất. Nhưng kể cả khi nằm ở vị trí khác thì vẫn là lưỡng lự, vẫn có xác suất đảo chiều, chỉ là thấp hơn.

## Ghép nến — đọc hai hoặc ba cây liên tiếp

Khi nhìn thấy hai hoặc ba cây nến đứng cạnh nhau mà không biết nó thuộc mẫu hình nào, thầy đề xuất kỹ thuật ghép nến: xác định đỉnh và đáy, xác định giá mở cửa của ngày đầu tiên và giá đóng cửa của ngày cuối cùng, rồi ghép lại thành một cây nến duy nhất rồi đọc theo các quy tắc trên. Kỹ thuật này giúp người đọc khỏi phải nhớ hàng trăm mô hình mà vẫn hiểu được bản chất.

Trường hợp hai cây nến, nếu cây đỏ trước rồi cây xanh sau bao trùm toàn bộ cây đỏ thì đó là mẫu hình nhấn chìm tăng, bản chất là đảo chiều xu thế giả. Ngược lại, nếu cây xanh trước rồi cây đỏ sau bao trùm thì đó là nhấn chìm giảm, đảo chiều xu thế tăng. Khi ghép lại, nhấn chìm tăng cho ra cây nến tương tự hammer, nằm ở phía trên vùng giá. Một biến thể khác là hai cây nến mà khi ghép lại ra cây nến thân nhỏ nằm ở phía dưới nội giải, tạo thành dạng tương tự hammer ngược, thầy gọi vui là mẫu hình cái mũ rơi, và nhiều khả năng là đảo chiều xu thế tăng.

Thầy cũng nhắc tới các tên gọi phổ biến như upthrust, spring, kéo lên để xả, đạp xuống để kéo, nhưng nhấn mạnh rằng đó chỉ là tên gọi, cái quan trọng vẫn là vị trí thân nến và độ dài khi ghép lại. Nếu cứ phải nhớ hết tên thì rất khó, nhưng hiểu bản chất thì ghép nến là cách đơn giản nhất.

Trường hợp ba cây nến, mẫu hình Morning Star gồm cây đỏ, cây doji hoặc hammer, rồi cây xanh. Bản chất khi ghép lại là cây nến có thân nhỏ nằm ở 1/3 phía trên của nội giải, và theo quy tắc đã học thì đó là hammer trong xu thế giả, nên khả năng đảo chiều xu thế giả là cao. Evening Star là ngược lại, gồm cây xanh, cây doji, rồi cây đỏ, đảo chiều xu thế tăng. Nếu cây doji trong Morning Star chuyển thành cây xanh thì khi ghép lại vẫn cho hình dạng hammer.

Một tình huống khác là ba cây nến liên tiếp cùng màu tạo thành mẫu hình ba người lính. Ba người lính tăng là ba cây xanh liên tiếp, ba người lính giả là ba cây đỏ liên tiếp, nhưng khi ghép lại thì bản chất chỉ là một cây nến rất dài tương tự marubozu. Nếu ba cây nến đỏ xen lẫn một cây lưỡng lự thì khi ghép lại cho ra marubozu đỏ, mà marubozu phản ánh xu thế chắc chắn nên khả năng tiếp diễn cao.

Thầy lưu ý rằng ở Việt Nam, giao dịch chứng khoán thường là T+3, nên ghép ba cây nến là đủ, không cần ghép bốn hay năm cây. Nếu muốn nhìn dài hơn thì nên dùng nến tuần, vì nến tuần về bản chất đã là sự ghép nến ngày rồi.

## Nến dùng để xác định điểm uốn, không dự đoán xu hướng

Thầy tổng hợp lại cách dùng nến. Đồ thị nến giúp xác định khả năng thay đổi của xu thế và khả năng tạo đỉnh, tạo đáy. Nếu một cây nến không có gì đặc biệt thì nó cũng giống như giá tăng lượng tăng bình thường, cứ để nó chạy. Nhưng nếu gặp cây nến đặc biệt thì đó là lúc cần dùng logic để phán đoán. Nến không dùng để đoán xu hướng, cũng không phải dùng một cây nến để phán đoán xu hướng, mà dùng để xác định những khả năng có thể tạo đỉnh đáy, tức là điểm uốn có thể xảy ra.

Ở Việt Nam, nến ngày phù hợp với giao dịch hơn nến tuần, vì phần lớn giao dịch trong phiên mang tính tâm lý, nhưng sau một ngày giao dịch thì người ta có thời gian dùng lý trí nhiều hơn, nên dùng nến một ngày sẽ tốt hơn. Nến tuần chỉ có ý nghĩa ghép nến. Khi gặp những ngày quan trọng thì nên dùng nến thời gian ngắn hơn, ví dụ nến 30 phút, để xem diễn biến cụ thể trong ngày, vì chỉ nhìn nến ngày thì chỉ thấy kết quả cuối ngày chứ không biết diễn biến là tăng mạnh đầu phiên hay cuối phiên. Theo thói quen, thầy mỗi ngày mở nến 30 phút ra để xem, nhưng bình thường thì chỉ cần mở tại những vùng quan trọng, nơi xuất hiện dấu hiệu đặc biệt `[?ASR: "lợi bột biến", nhiều khả năng là "khối lượng đột biến"]` hoặc nến đặc biệt.

Nến phải được dùng kết hợp với các yếu tố kỹ thuật khác, đặc biệt là khi gặp khối lượng đột biến, gặp vùng kháng cự hoặc hỗ trợ, hoặc đường xu hướng. Khi hai dấu hiệu trở lên xuất hiện cùng lúc, ví dụ khối lượng bán tăng và nến lưỡng lự trong xu thế tăng, thì người đọc có thêm cơ sở để phán đoán điểm uốn.

Có hai loại nến đáng chú ý. Loại thứ nhất là nến thân ngắn, bóng nến dài, phản ánh sự lưỡng lự do tâm lý. Loại thứ hai là nến thân dài, bóng nến rất ngắn, phản ánh sự quyết tâm về tâm lý và có thể phản ánh thay đổi cơ bản. Khi gặp nến thân dài thì người đọc phải tìm hiểu thêm hôm đó có thông tin gì mới không, có làm thay đổi cơ bản không. Nếu có thay đổi cơ bản thì sự thay đổi dài hạn hơn, nếu tìm mãi không thấy thông tin gì thì sự thay đổi đó chỉ là ngắn hạn do tâm lý.

Khi nến thân ngắn toàn bộ cây nến, thầy giải thích rằng thị trường đang không có tin gì mới, hoặc đang chờ đợi thông tin mới. Đây là dấu hiệu cho thấy thị trường đang ở trạng thái tạm dừng, phù hợp với việc dùng các chỉ số kỹ thuật khác để phán đoán xem cơ bản có thay đổi gì không. Còn khi nến thân dài, đó thường là có tác động tâm lý hoặc có thông tin mới, người đọc cần tìm hiểu thêm về thông tin đó.

Sau giai đoạn lưỡng lự tích luỹ, tức sau quá trình thẩm thấu thông tin, nếu gặp một cây nến marubozu thì đó là lúc thay đổi xu hướng. Thầy nói đây là mẫu hình ưa thích của những người mua dài hạn, vì nó phản ánh sự thay đổi cơ bản sau khi thị trường đã tiêu hoá xong thông tin cũ.

Theo cách tiếp cận của QMV, người đọc nên phân tích tất cả các yếu tố kỹ thuật trước rồi dùng nến như công cụ cuối cùng để xác định điểm uốn. Mặc dù khi mở đồ thị giá thì nến hiện ra rất rõ và bắt mắt, nhưng thầy khuyến nghị nên dùng nó sau cùng, không nên bắt đầu từ nến.

## Ví dụ và ứng dụng

Phần này thầy lấy các ví dụ trên đồ thị thực tế để minh hoạ.

Trước hết thầy chỉ ra các mẫu hình quen thuộc. Ba người lính tăng là ba cây nến tăng liên tiếp, bản chất khi ghép lại chỉ là một cây nến marubozu tăng rất chắc chắn. Ngược lại, nếu gặp nến đỏ trước rồi nến lưỡng lự rồi ba cây xanh, khi ghép lại sẽ thành doji hoặc hammer trong xu thế giả, tức là dấu hiệu đảo chiều. Thầy cũng chỉ ví dụ một cây nến bao trùm toàn bộ quá trình trước đó, nghĩa là giá mở cửa ở dưới đáy cũ và giá đóng cửa ở trên đỉnh cũ, đó là dấu hiệu đảo chiều mạnh.

Một ví dụ khác là tình huống hai cây nến mà khi ghép lại thành nến lưỡng lự nằm ở phía dưới 1/3 nội giải. Đây chính là mẫu hình Evening Star, bản chất là dấu hiệu đảo chiều xu thế tăng. Thầy cũng vẽ thêm ví dụ về đường kháng cự cũ bị phá, khi đó người đọc phải tìm hiểu xem hôm đó có thay đổi căn bản nào không, hay chỉ là yếu tố cơ bản đã được hấp thụ hết. Nếu toàn bộ quá trình trước đó đã được phá lên một nền tảng cơ bản mới thì đường kháng cự cũ trở thành hỗ trợ, và việc quan sát hành vi tại vùng hỗ trợ đó rất quan trọng.

Thầy lấy ví dụ cụ thể về một xu thế tăng mạnh ngắn hạn gặp một cây nến dài phá xu thế tăng. Khi gặp cây nến này, người đọc phải hiểu rằng tin tốt ở giai đoạn đó đã hết tác dụng, vì xu thế tăng mạnh mà bị phá thì chỉ có thể là do lực cầu đã cạn hoặc có thông tin tiêu cực. Tuy nhiên, xu thế tăng của cả thị trường thì chưa có khả năng phá vỡ, nên nếu giá rơi về vùng hỗ trợ lớn thì cần quan sát xem có lực mua đẩy lên hay không. Lúc này mới là lúc mở nến 30 phút ra xem, đặc biệt là các nến cuối phiên, vì nếu cuối phiên giá càng xuống mà người ta vẫn mua thì đó là dấu hiệu lực cầu mạnh.

Trong phần ví dụ trên đồ thị hiện tại, thầy chỉ ra rằng vĩ mô đã được phán đoán sai nên sẽ tạo ra một bước sóng lớn ở vùng này. Trên đồ thị có một vùng đi ngang lớn, tức biên độ giao dịch rộng. Khi cây nến vọt lên khỏi vùng đó, người đọc phải tìm hiểu có thông tin đặc biệt nào không, nếu có thì xu hướng kéo dài, nếu không thì chỉ ngắn hạn. Thường khi không rõ về mặt cơ bản thì giá retest lại vùng cũ. Trong hai ngày gần nhất, hai cây nến lưỡng lự liên tiếp xuất hiện tại vùng quan trọng, vừa tiếp xúc trend tăng ngắn hạn vừa tiếp xúc đường kháng cự cũ đã trở thành hỗ trợ. Nếu ngày tiếp theo xuất hiện cây nến xanh thì đó chính là mẫu hình Morning Star đảo chiều, ngược lại nếu là cây nến đỏ rơi xuống thì không có cơ hội. Trong tình huống 50-50 này, thầy khuyến nghị đợi cây nến hình thành rồi mới đi theo, không nên đoán trước. Nếu muốn vào thì phải chuẩn bị sẵn danh sách cổ phiếu theo dõi trước, vì khi thị trường xác nhận thì phải chọn nhanh.

Thầy cũng mở nến 30 phút ra phân tích diễn biến trong ngày. Cây nến 30 phút đầu tiên chưa có nhiều thông tin vì chỉ là phản ánh phần mở phiên, nhưng cây nến thứ hai cho thấy mặc dù giá giảm mạnh nhưng khối lượng vẫn cao, tức là bên mua vẫn chủ động nhảy vào mua chứ không phải lệnh chờ bị quét. Nếu bên mua sợ thì khối lượng cây tiếp theo sẽ thấp, nhưng ở đây khối lượng vẫn cao, nghĩa là lực mua đang tăng lên. Cây nến cuối cùng trong ngày là một cây tăng nhẹ với khối lượng tăng theo, phản ánh cuối phiên có mua vào. Thầy đánh giá khả năng bật lên nhẹ là cao hơn rơi xuống, dù vẫn chưa confirm được tin xấu hay tin tốt.

## Bối cảnh thị trường lúc giảng (05/2024)

Tại thời điểm bài giảng, thầy nêu rõ không nói về vĩ mô vì vĩ mô đã phán đoán sai trước đó, và sẽ tạo ra một bước sóng lớn ở vùng giá hiện tại `[?nguyên ASR: "cho đến rửa nào", không rõ ý]`. Tại thời điểm bài giảng, thầy đánh giá thị trường đang ở trạng thái cưa, vì các yếu tố ngắn hạn chưa rõ ràng, chỉ có thể khẳng định tin xấu đã được phản ánh hết. Tại thời điểm bài giảng, thầy cho rằng phải chờ thêm khoảng 2 đến 3 tuần nữa mới có thông tin mới về lạm phát, nên khả năng thị trường đi ngang là cao.

Trong ngắn hạn thì có thể có những đợt điều chỉnh nhẹ, nhưng khả năng tăng lên thì thầy đánh giá thấp. Theo đánh giá của thầy tại thời điểm đó, lợi nhuận có thể thu được là ngắn còn rủi ro giảm có thể là mạnh. Cơ hội vẫn có nhưng nằm ở các cổ phiếu chứ không phải cơ hội của cả thị trường. Thầy chỉ ra mẫu hình tán giác hướng lên trên đồ thị, vì hướng lên nên khả năng có những đợt điều chỉnh nhẹ tiếp theo là cao, tức là tăng thì tăng rất ngắn nhưng giả thì giả khá mạnh. Vì vậy thầy khuyến nghị phải nhanh và phải chọn được cổ phiếu, nếu không có danh sách ngắm sẵn thì không nên vào lệnh.

## Điểm thầy nhấn mạnh

Thầy nhấn mạnh triết lý của QMV là đi vào hiểu thay vì nhớ, vì vậy các mẫu hình nến không cần phải nhớ tên mà chỉ cần hiểu hành động giá dựa trên ba yếu tố: bóng nến, thân nến và vị trí thân nến. Có thể dùng cách chia đơn giản 1/3, 1/2, 2/3 thay cho việc nhớ tỷ lệ Fibonacci 38%, 50%, 68%.

Khi đọc nến, cần đặt giả thiết thứ nhất là lưỡng lự, rồi mới xét màu sắc để đánh giá độ tin cậy. Màu sắc không thay đổi bản chất, chỉ tăng hay giảm độ tin cậy của cảnh báo đảo chiều.

Nến xác định khả năng thay đổi xu thế chứ không dùng một cây nến để phán đoán xu hướng. Nên dùng nến kết hợp với các yếu tố kỹ thuật khác, đặc biệt tại các vùng quan trọng như kháng cự, hỗ trợ và đường xu hướng, cùng với khối lượng giao dịch. Trong QMV, có 5 yếu tố kỹ thuật cần xét, nến chỉ là một trong năm và nên dùng cuối cùng, sau khi đã phân tích xong các yếu tố khác.

Khi gặp nến quan trọng, nên mở nến 30 phút để xem diễn biến cụ thể trong ngày, đặc biệt là diễn biến cuối phiên, vì chỉ nhìn nến ngày thì không biết lực mua bán phân bổ thế nào trong phiên. Mỗi cổ phiếu có kiểu đánh riêng, nên cần xem xét mẫu hình nến trong quá khứ của chính cổ phiếu đó. Nếu trong quá khứ mẫu hình đã từng đúng thì khả năng tiếp tục đúng là cao.
