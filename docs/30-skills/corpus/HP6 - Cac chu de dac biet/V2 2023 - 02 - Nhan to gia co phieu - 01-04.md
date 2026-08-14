# V2 2023 - 02 - Nhan to gia co phieu - 01-04

Bài giảng chuyên sâu về các nhân tố ảnh hưởng tới giá cổ phiếu, dựa trên các nghiên cứu tài chính phổ biến từ giới hàn lâm (trong đó có Fama-French, hai nhà nghiên cứu đoạt giải Nobel). Bài quay tháng 06/2024, có tính hàn lâm cao hơn các buổi thông thường. Thầy dùng mô hình APT làm khung đi qua từng nhóm nhân tố — vĩ mô, cơ bản, kỹ thuật, lịch, sự kiện — rồi tổng hợp lại thành 3 nhân tố vĩ mô và 4 nhân tố cơ bản mà thầy cho là đủ để ra quyết định. Trong buổi không có phần hỏi đáp; thầy nói sẽ trả lời câu hỏi học viên ở buổi sau (Bia Hơi Vỉa Hè).

## Mở đầu: vì sao hỏi "nhân tố giá cổ phiếu"

Thầy bắt đầu từ bước 4 của quy trình định giá — chiết khấu dòng tiền về hiện tại bằng tỷ lệ lợi nhuận yêu cầu (required of return). Câu hỏi đặt ra: tỷ lệ lợi nhuận yêu cầu được xác định như thế nào, và những nhân tố nào tác động tới nó? Trả lời câu hỏi này cũng chính là trả lời câu hỏi nhân tố nào tác động tới định giá chứng khoán.

Mục tiêu thầy đặt ra không phải trình bày lý thuyết, mà là giúp người học hiểu các lý thuyết đó được xây dựng và thực hiện như thế nào, để từ đó tự quyết định khi nào nên dùng, dùng trong điều kiện nào.

## Mô hình APT — cách nhà nghiên cứu tìm nhân tố

Các mô hình định giá phổ biến đều dựa trên số liệu quá khứ và hồi quy (regression) trong kinh tế lượng (econometrics). Phương trình hồi quy chuẩn có dạng lợi nhuận vượt trội của cổ phiếu i so với lợi nhuận phi rủi ro bằng tổ hợp các nhân tố F1, F2, ... Fn cộng sai số, với hệ số tương quan (coefficient) cho từng nhân tố. Phần mềm sẽ chạy ra các hệ số; nhân tố nào có ý nghĩa thống kê (significant) ở một trong ba mức 1%, 5%, 10% thì được giữ lại, các mức tin cậy tương ứng là 99%, 95%, 90%. Hệ số dương hay âm phản ánh tương quan thuận hay nghịch.

Nguyên lý cốt lõi: mọi nhân tố trong mô hình đều là `F − E(F)`, tức lấy giá trị thực tế trừ kỳ vọng. Nhà đầu tư ra quyết định dựa trên kỳ vọng của họ, nên chỉ phần khác với kỳ vọng mới có tác động; phần trùng với kỳ vọng thì không. Thầy ví dụ: lãi suất không phải là "tăng bao nhiêu" mà là "tăng bao nhiêu so với kỳ vọng"; lạm phát cũng vậy.

Mô hình APT (Arbitrage Pricing Theory) là dạng tổng quát đầu tiên, đưa vào nhiều nhân tố. Điểm yếu của APT là có quá nhiều nhân tố, nhà đầu tư không đủ thời gian để theo dõi hết. Vì vậy các mô hình về sau đều là dạng rút gọn của APT, tập trung vào một số nhân tố có ý nghĩa nhất.

## Fama-French 3 yếu tố

Mô hình rút gọn phổ biến nhất là mô hình 3 yếu tố của Fama và French, phát triển khoảng những năm 1990. Ba yếu tố gồm:

Yếu tố thị trường, đo bằng `Rm − Rf` (lợi nhuận thị trường trừ lợi nhuận phi rủi ro), với hệ số beta. Yếu tố quy mô, viết tắt SMB (small minus big), so sánh lợi nhuận nhóm vốn hóa nhỏ với nhóm vốn hóa lớn. Yếu tố giá trị, viết tắt HML (high minus low), trong nghiên cứu gốc Fama-French dùng B/P (book value per share trên price per share), tức lấy giá trị sổ sách chia cho giá thị trường; B/P cao nghĩa là giá trị sổ sách lớn hơn giá thị trường, tương đương P/B thấp. Khi chuyển sang cách nói Việt Nam, thầy dùng P/E và P/B thấp đại diện cho cổ phiếu giá trị.

Khi chạy hồi quy, cả ba nhân tố đều có ý nghĩa thống kê. Kết luận: cổ phiếu vốn hóa nhỏ tốt hơn cổ phiếu vốn hóa lớn, cổ phiếu giá trị tốt hơn cổ phiếu tăng trưởng.

## Fama-French 5 yếu tố

Khoảng một thập kỷ sau, Fama và French bổ sung thêm hai yếu tố, thành mô hình 5 yếu tố. Yếu tố thứ tư là lợi nhuận hoạt động, viết tắt RMW (robust minus weak), dựa trên operating profit. Cách dùng: lấy lợi nhuận của các công ty có lợi nhuận hoạt động tốt trừ lợi nhuận của các công ty có lợi nhuận hoạt động yếu. Yếu tố thứ năm là quy mô đầu tư, viết tắt CMA (conservative minus aggressive), dựa trên tốc độ tăng trưởng tổng tài sản (investment capital). Công ty nào tăng trưởng tài sản lớn gọi là aggressive, tăng trưởng nhỏ gọi là conservative; lấy lợi nhuận của conservative trừ aggressive.

Cả hai nhân tố mới đều có ý nghĩa thống kê. Kết luận: ngoài 3 yếu tố ban đầu, lợi nhuận hoạt động và tăng trưởng tài sản cũng tác động tới giá cổ phiếu.

## Tầm quan trọng của nhân tố thị trường

Toàn bộ 5 yếu tố Fama-French cùng giải thích được khoảng 95% lợi nhuận yêu cầu, nghĩa là còn 5% không giải thích được. Trong 95% đó, riêng nhân tố thị trường đã giải thích tới hơn 80%. Thầy nhấn mạnh đây là lý do tại sao những người theo trường phái cho rằng chỉ cần đi theo thị trường là đủ: thị trường giải thích phần lớn lợi nhuận yêu cầu của bất kỳ cổ phiếu nào.

Điều kiện tiên quyết khi áp dụng: phải xác định được thị trường trước, rồi mới dùng các yếu tố còn lại (quy mô, giá trị, lợi nhuận, đầu tư). Nếu dùng các yếu tố cơ bản mà bỏ qua bối cảnh thị trường thì có thể sai. Thầy lấy ví dụ thời điểm cuối năm 2021: nếu áp dụng tiêu chí chọn cổ phiếu vốn hóa nhỏ, giá trị, lợi nhuận tốt mà không xét thị trường thì sẽ thua lỗ.

Quan điểm "chọn cổ phiếu tốt nắm giữ lâu dài" có thể đúng hoặc sai; thầy nghiêng về sai nhiều hơn vì thị trường mới là yếu tố quyết định, còn giá trị, lợi nhuận, tăng trưởng chỉ là yếu tố phụ.

## Nhân tố vĩ mô — 3 yếu tố chính

Khi test nhiều nhân tố vĩ mô (lạm phát, tăng trưởng, tỷ giá, các chỉ số khác), kết quả cuối cùng chỉ còn 3 yếu tố có ý nghĩa:

Lạm phát: lạm phát bất thường (khác với kỳ vọng) thường tỷ lệ nghịch với lợi nhuận cổ phiếu, vì lạm phát cao buộc lãi suất phải tăng để chống lạm phát. Tuy nhiên thầy cho rằng bằng chứng về tác động của lạm phát tới thu nhập khá yếu. Tăng trưởng GDP: thường tỷ lệ thuận với cổ phiếu. Lãi suất trái phiếu chính phủ: thầy nhấn mạnh đây là yếu tố quan trọng, tỷ lệ nghịch với cổ phiếu. Nhà đầu tư không quan sát trực tiếp được lãi suất, nhưng quan sát được sự thay đổi tỷ suất trái phiếu, bao gồm cả sự dịch chuyển của đường cong lợi suất các kỳ hạn. Khi đường cong lợi suất dịch lên, đó là tín hiệu xấu.

Bộ 3 lạm phát, tăng trưởng, lãi suất chính là bộ 3 vĩ mô mà thầy thường nhắc tới trong các bản tin tiền tệ. Giá hàng hóa cũng được nhắc tới nhưng tỷ lệ nghịch không đáng tin cậy và phụ thuộc nhiều vào ngành.

## Nhân tố cơ bản ở cấp độ ngành và doanh nghiệp

Tổng hợp từ Fama-French và các nghiên cứu khác, thầy liệt kê các nhân tố cơ bản có ý nghĩa:

Quy mô, tức vốn hóa nhỏ, vượt trội so với vốn hóa lớn. Giá trị, đo bằng P/E và P/B thấp, vượt trội; trong nghiên cứu gốc Fama-French dùng B/P và E/P cao, nhưng thầy quy đổi về cách nói Việt Nam. Lợi nhuận hoạt động, tức lợi nhuận trên tài sản cao, vượt trội. Tốc độ tăng trưởng tài sản thấp (doanh nghiệp conservative, không mở rộng quá mức), vượt trội.

Thầy lưu ý phải đọc chiều ngược trong bảng Fama-French gốc vì tác giả dùng B/P, không dùng P/B. Khi B/P tăng từ thấp lên cao, tương ứng P/B giảm từ cao xuống thấp, tức cổ phiếu giá trị. Dữ liệu nghiên cứu Fama-French gốc kéo dài 50 năm, từ 1963 đến 2013.

Ngoài ra còn các nhân tố khác: momentum, tức một cổ phiếu đang tăng thì có khả năng tăng tiếp; contrarian, tức ngược thị trường, một cổ phiếu tăng quá nhiều thì khả năng đảo chiều giảm. Thầy giải thích hai trường phái này thực ra cùng đúng, chỉ khác nhau về giai đoạn: momentum áp dụng cho đoạn đầu của xu hướng tăng, contrarian áp dụng khi giá đã tăng dài và lớn.

Thanh khoản: nghiên cứu cho thấy cổ phiếu có thanh khoản thấp lại mang lại lợi nhuận tốt hơn về dài hạn. Thầy nhấn mạnh "thanh khoản thấp" nghĩa là cổ phiếu ít được giao dịch, không phải thanh khoản kém. Biến động giá: biến động lớn trong tháng trước thì tháng sau thường giảm.

## Nhân tố kỹ thuật

Các nghiên cứu cũng test nhiều chỉ số kỹ thuật. Kết luận phổ biến:

Đường cắt lên cắt xuống: khi đường ngắn hạn cắt đường dài hạn (ví dụ MA ngắn cắt MA dài), theo quy tắc mua/bán tỷ lệ cố định và tuân thủ kỷ luật, về dài hạn (vài chục năm) thì thắng. Quy tắc chi tiết hơn của momentum: sau khi đường ngắn cắt lên đường dài, phải đợi thêm 2-3 phiên không cắt xuống thì mới mua. Trạm giải giao dịch: tương tự kháng cự và hỗ trợ. Bật ngược từ hỗ trợ tương đương contrarian; vượt lên khỏi kháng cự (breakout) tương đương momentum.

Thầy lưu ý kết luận "thắng trong dài hạn" dựa trên số liệu vài chục năm, không phải vài năm. Người dùng có thể rơi đúng vào giai đoạn mà quy tắc không hiệu quả.

Thầy cũng nhắc tới các chỉ số khác như RSI, CCI, Bollinger, đều có thể quy về dạng cắt lên cắt xuống. Nghiên cứu viên đã test hàng nghìn chỉ số kỹ thuật; kết luận mang tính dài hạn. Theo kinh nghiệm thầy, các phát hiện từ nghiên cứu kỹ thuật khó áp dụng trong thực tế vì phụ thuộc nhiều vào điều kiện thị trường, dù bản thân thầy thấy các đường cắt lên cắt xuống là có ý nghĩa.

Mối liên hệ giữa kỹ thuật và định giá: đường trung bình 50 ngày về bản chất là định giá trung bình 50 phiên, nên khi giá cắt lên đường trung bình, có thể hiểu là giá đang cao hơn giá trị hợp lý và ngược lại. Người không thích phân tích cơ bản có thể dùng đường trung bình để xác định vùng giá hợp lý, dù bản chất định giá vẫn mang tính chủ quan.

## Nhân tố lịch

Các hiệu ứng lịch phổ biến trong nghiên cứu: tháng riêng (đầu năm thường tốt hơn), "sell in May and go away" (bán tháng 5 đi chơi, mua lại tháng 11), thứ 6 và thứ 2 có tính chất đặc biệt.

Thầy giải thích "sell in May" có nguồn gốc từ nước Anh thế kỷ 17-18: từ tháng 11 đến tháng 4 thời tiết xấu, từ tháng 5 đến tháng 10 thời tiết đẹp, người ta bán hết nghỉ. Câu nói dần lan sang lĩnh vực chứng khoán và tự thành một quy luật vì nhiều người cùng tin nên nó trở thành đúng. Về sau các nhà nghiên cứu giải thích bằng lý do cuối năm được thưởng, đầu năm chi tiêu nhiều, kế hoạch mới, nên chứng khoán tăng tốt đầu năm rồi đến tháng 5 thì bán chốt lời.

Với thứ 6, thầy nhận thấy không có bằng chứng vững chắc rằng cứ thứ 6 là phải yếu. Lý do thường được nêu (tin xấu ra cuối tuần) thầy thấy không thuyết phục. Theo thầy, nếu thứ 6 yếu thì thường vì thị trường đã có sự nghi ngờ trước đó, chứ không phải quy luật cố định.

Tại Việt Nam, thầy cho rằng cần cân nhắc tác động tháng riêng cùng với tác động Tết vì Tết có ảnh hưởng rõ ràng tới dòng tiền.

## Nhân tố sự kiện

Các sự kiện doanh nghiệp phổ biến mà nghiên cứu test: chia cổ tức, chia cổ phiếu thưởng, chia tách cổ phiếu, phát hành thêm, mua cổ phiếu quỹ. Tất cả tạo ra hiệu ứng tâm lý chứ không làm thay đổi giá trị doanh nghiệp hay tài sản của cổ đông. Chia cổ tức và cổ phiếu thưởng tạo "hiệu ứng giá trị"; chia tách tạo "hiệu ứng giá rẻ" và tăng thanh khoản; mua cổ phiếu quỹ tạo "hiệu ứng tăng trưởng" (vì thị trường cho rằng công ty đang tăng trưởng).

Vì chỉ là hiệu ứng tâm lý nên tác động chỉ kéo dài trong một giai đoạn cửa sổ (window) ngắn quanh sự kiện, sau đó bão hoà và biến mất. Thầy nhấn mạnh phải phân biệt sự kiện ngắn hạn với giá trị dài hạn; tại Việt Nam, hiệu ứng sự kiện khá mạnh và khá nhiều, nhưng luôn chỉ giới hạn trong giai đoạn cửa sổ.

## Áp dụng vào Việt Nam

Thầy chốt lại bằng cách đưa các kết luận nghiên cứu về bối cảnh Việt Nam.

Vĩ mô, 3 nhân tố chính vẫn là lạm phát, lãi suất, tăng trưởng. Thầy bỏ tăng trưởng ra khỏi tổng kết riêng vì tăng trưởng gắn liền với lạm phát và lãi suất. Cơ bản, 4 nhân tố quan trọng: vốn hóa (thị giá nhỏ, vốn hóa nhỏ, mệnh giá nhỏ), giá trị (P/E và P/B thấp), lợi nhuận hoạt động cao, tốc độ tăng trưởng tài sản thấp. Lưu ý: ở Việt Nam, doanh nghiệp tăng trưởng tài sản nhanh thường gắn với đầu tư mở rộng (kể cả các trò chơi tài chính), nên việc xác định ngắn hạn và dài hạn trong bối cảnh này khó hơn.

Kỹ thuật: thầy nhận thấy momentum ở Việt Nam khá tốt, breakout thì hơi yếu. Lịch: tác động cuối năm và Tết có ảnh hưởng tới dòng tiền. Sự kiện: khá căng thẳng và thường xuyên ở thị trường Việt Nam. Đặc điểm chung: thị trường Việt Nam thường đi theo xu hướng, theo đám đông và theo dòng tiền.

## Điểm thầy nhấn mạnh

Mọi nhân tố trong các mô hình định giá đều được đo bằng `F − E(F)`, tức lấy thực tế trừ kỳ vọng. Nếu thực tế trùng kỳ vọng thì không có tác động. Đây là lý do vì sao thầy luôn so sánh với kỳ vọng trong các phân tích vĩ mô.

Nhân tố thị trường quan trọng hơn tất cả các yếu tố còn lại. Thầy nói thẳng: "đừng bao giờ bỏ qua thị trường", vì thị trường giải thích tới hơn 80% lợi nhuận yêu cầu. Trình tự đúng là xác định thị trường trước, rồi mới kết hợp các yếu tố cơ bản.

Các kết luận nghiên cứu chỉ mang tính dài hạn (vài chục năm), không áp dụng được cho vài năm hay vài tháng. Thầy nhắc: người dùng có thể rơi đúng vào giai đoạn quy tắc không hiệu quả. Vì vậy không nên máy móc áp dụng.

Thầy cảnh báo về vấn đề "làm đẹp số liệu" (data mining): một số nghiên cứu có thể chọn mẫu và phương pháp sao cho ra kết quả đẹp. Đã có trường hợp làm lại nghiên cứu với cùng bộ dữ liệu và phương pháp mà không tái lập được kết quả, thậm chí có cáo buộc làm giả dữ liệu. Tuy nhiên, nghiên cứu Fama-French được giải Nobel và được sử dụng rộng rãi nên thầy cho rằng có thể đi theo hướng đó.

Cuối cùng, tóm tắt thầy đưa ra: 4 yếu tố cơ bản (quy mô, giá trị, lợi nhuận hoạt động, tăng trưởng tài sản) cộng với thị trường giải thích được 95% lợi nhuận yêu cầu, còn 5% không giải thích được. Không có mô hình định giá nào hoàn hảo. Trong thực tế đầu tư, nên chọn vài yếu tố chính thay vì đi sâu vào quá nhiều yếu tố phụ, vì phần còn lại chỉ chiếm 5% và không đáng thời gian.
