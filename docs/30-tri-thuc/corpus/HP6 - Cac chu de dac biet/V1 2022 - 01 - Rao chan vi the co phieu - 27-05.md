# V1 2022 - 01 - Rao chan vi the co phieu - 27-05

Bài đầu tiên trong học phần 6 (HP6 - các chủ đề đặc biệt) của khoá học QMV. Chủ đề: rào chắn rủi ro vị thế cổ phiếu. Hai kỹ thuật chính là rebalancing và hedging bằng hợp đồng tương lai. Bài quay ngày 27/5/2024, dùng nhiều ví dụ đang diễn ra trên thị trường (chỉ số VN-Index quanh 1.300, cổ phiếu HPG) để minh hoạ, nên các nhận định thị trường trong bài mang tính thời điểm. Phần lý thuyết về rebalancing, hedging và Open Interest là nội dung cốt lõi và còn nguyên giá trị.

## Tổng quan: hai kỹ thuật rào chắn vị thế

Mở đầu, thầy phân biệt hai khái niệm thường bị đồng nhất. Speculation (đầu cơ) là nắm giữ một chiều với kỳ vọng giá tăng hoặc giảm, bản chất giống hệt việc mua cổ phiếu với kỳ vọng giá lên, hoặc short phái sinh với kỳ vọng giá xuống. Arbitrage (kinh doanh chênh lệch giá) đòi hỏi sự nhanh nhạy hơn: mua bán đồng thời cùng loại tài sản ở hai thị trường để chốt lời khoảng chênh lệch, ví dụ đứng giữa một bên bán và một bên mua rồi khớp lệnh hai phía. Arbitrage rất hiếm trên thị trường; thầy sẽ trình bày ở bài khác.

Bài này tập trung vào hai kỹ thuật trong rào chắn vị thế đầu tư: rebalancing và hedging. Thầy nhấn mạnh: bài học hôm nay tập trung vào rào chắn vị thế rủi ro, tức là khóa vị thế lại chứ không phải đầu cơ. Với phái sinh, bài giả định người học đã nắm khái niệm cơ bản, chỉ tập trung cách dùng nó làm công cụ rào chắn.

## Rebalancing - nguyên lý và điều kiện áp dụng

Rebalancing áp dụng khi nhà đầu tư đang giữ cổ phiếu và chưa muốn bán, tức mục tiêu là nắm giữ dài hạn nhưng muốn tận dụng biến động ngắn hạn để cơ cấu lại vị thế. Nếu mua bán theo một hướng thì không đặt vấn đề rebalancing. Cơ hội rebalancing xuất hiện khi cổ phiếu hoặc thị trường tiệm cận vùng hỗ trợ hoặc vùng kháng cự, hoặc khi gặp các đường trend line quan trọng. Việc xuất hiện cơ hội không có nghĩa là phải hành động ngay, cần thêm phân tích kỹ thuật.

Nguyên lý cốt lõi: phải mua bán cùng lượng cổ phiếu, không để vị thế thay đổi. Nếu mua bán khác lượng, rebalancing biến thành đầu cơ, ý nghĩa rào chắn không còn. Cách xử lý: tại vùng kháng cự, ưu tiên bán trước mua sau; tại vùng hỗ trợ, ưu tiên mua trước bán sau. Mục đích là phòng vệ rủi ro, không phải tìm kiếm lợi nhuận.

## Tín hiệu kỹ thuật và khung quan sát

Khi cổ phiếu tiệm cận vùng hỗ trợ hoặc kháng cự, dùng nến 30 phút để quan sát diễn biến tâm lý mua bán trong phiên. Thầy chọn 30 phút vì khung này đủ ngắn để bắt nhịp thay đổi tâm lý, đủ dài để nhà đầu tư "bình tĩnh lại" sau phản ứng ban đầu. Nến 15 phút hoặc 1 giờ cũng dùng được, nhưng 30 phút là khung cân bằng nhất. Có thể dùng nến ngắn hơn 30 phút nhưng thầy cho rằng 30 phút là đủ để người ta "hoàn hồn" hoặc bình tâm trở lại.

Các tín hiệu kỹ thuật cần chú ý: mẫu hình phân kỳ, các mẫu nến, tương quan giữa khối lượng giao dịch và giá (VPA - phân tích giá-khối lượng). Trong khung thời gian ngắn, các yếu tố cơ bản chưa kịp thay đổi nên tâm lý và hành vi là yếu tố chi phối chính. Tuy nhiên, thầy lưu ý: ngay cả thông tin cơ bản cũng cần quan sát vì nó ảnh hưởng tâm lý ngay lập tức. Ví dụ, phát biểu của chủ tịch Hòa Phát tạo biến động giá cổ phiếu HPG; việc định giá thực sự thì cần thời gian rất dài, không phản ánh tức thì lên giá.

Khi đã xác định thực hiện rebalancing, quan điểm thầy là phải làm trong ngày. Nếu để sang ngày sau rồi lại đợi tiếp thành T+2, T+3, bản chất trở thành mua thêm chứ không phải rebalance. Sai cũng được, nhưng phải làm trong ngày. T+1 có thể chờ, T+2, T+3 là phải làm trong ngày. Quy tắc cao nhất: làm ngay trong ngày, làm sớm hơn T+3.

Nguyên tắc "nhịp thứ 2": vì tâm lý con người thường có 3 lần phản ứng trước một vùng quan trọng, nên hành động ở nhịp thứ 2 thường an toàn nhất. Nhịp 1: giá tiến lên rồi giảm (chưa rõ breakout hay bật lại). Nhịp 2: giá tiến lên lần nữa, đây là dấu hiệu đã có sự đàm phán tại vùng kháng cự, giống hai đứa trẻ đánh nhau. Lúc này bán ở vùng kháng cự hoặc mua ở vùng hỗ trợ sẽ chắc chắn hơn. Phán đoán dựa trên nến của ngày kế tiếp phải đặt trong bối cảnh kháng cự/hỗ trợ, nếu không sẽ rỗng.

## Ví dụ rebalancing với VN-Index quanh 1.300 điểm

Tại thời điểm bài giảng (27/5/2024), thầy dùng chỉ số VN-Index như một cổ phiếu để minh hoạ. Quan sát khung ngày 24/5: chỉ số trong mẫu hình giao dịch đi ngang, đã chạm điểm chạm thứ 3 tạo mẫu hình 3 điểm chạm. Khi chuyển sang nến 30 phút, các điểm chạm giãn ra và nằm trong khung. Tín hiệu thứ 2: nến ở vùng hỗ trợ (cạnh dưới giao dịch đi ngang) có dấu hiệu rút chân. Tín hiệu thứ 3: khối lượng giao dịch tăng lên trong khi giá đang giảm, cho thấy bên mua mạnh hơn nhảy vào.

Hành động: mua ngay khi thấy nến rút chân (nến đỏ) và bán ngay sau đó, hoặc đợi hôm sau. Một khi đã xác định rebalancing thì phải thực hiện trong ngày. Khi thấy nến rút chân và khối lượng tăng, phải mua ngay, ở nến đỏ hoặc ít nhất là nến tiếp theo.

Sang ngày 27/5, khi phân tích phiên tiếp theo: vì 27/5 là nến xanh, giá chỉ còn cách vùng kháng cự quanh 1.300 điểm khoảng hơn 10 điểm (chỉ một phiên), thầy dự đoán phiên 30/5 sẽ có sự lưỡng lự khi tiệm cận kháng cự, cụ thể là "khỏe đầu yếu sau". Logic: đà tăng từ nến 27/5 vẫn còn nhưng sẽ gặp lực cản tại 1.300; nếu tăng hơn 10 điểm thì tiệm cận vùng kháng cự, sẽ lưỡng lự. Việc dùng nến ngày 27/5 để phán đoán diễn biến phiên 30/5 cũng tương tự cách dùng nến ngày 23/5 để dự đoán ngày 24/5.

Tại thời điểm bài giảng (27/5/2024), thầy dự đoán ngày 30/5 có thể thực hiện rebalancing nếu chỉ số tiệm cận 1.300 điểm. Hành động: bán khi chỉ số ở vùng kháng cự, đặc biệt khi khối lượng tăng, rồi mua lại sau. Điều kiện tiên quyết: bạn vẫn tin cổ phiếu còn cơ hội lên nữa, chỉ muốn tận dụng sự ngập ngừng của thị trường để cơ cấu lại vị thế. Nếu đã định bán vì nghĩ thị trường giảm nhiều hơn thì không phải rebalancing nữa mà là bán thật. Rebalancing là làm trong ngày; nếu đợi thêm 1-2 hôm thì đó là kỳ vọng thị trường sẽ giảm, câu chuyện khác.

## Rebalancing hàng ngày: cách chia vị thế và ví dụ HPG

Thực tế thị trường Việt Nam bị chi phối bởi T+ (chu kỳ thanh toán): bán cổ phiếu thì có tiền ngay (có thể ứng tiền), nhưng mua cổ phiếu thì phải đợi T+3 mới bán được. Điều này về lý thuyết giới hạn rebalancing hàng ngày, nhưng vì có dịch vụ ứng tiền nên gần như vẫn thực hiện được. Tất nhiên khi ứng tiền sẽ chịu phí, nhưng mua thì rủi ro vì phải đợi T+3.

Cách chia vị thế để rebalancing hàng ngày: chia số cổ phiếu làm 3 phần, cộng thêm 1 phần tiền mặt. Vì bán cổ phiếu có thể ứng tiền ngay, việc chia 3 phần giúp ba phần luân phiên hỗ trợ nhau để giao dịch hàng ngày. Càng chia nhỏ thì càng giao dịch được nhiều lần, vượt qua rào cản T+3. Nguyên tắc: chỉ thực hiện rebalancing hàng ngày khi muốn đầu tư dài hạn, tương tự "tạo kho" của nhà tạo lập; bản thân nhà đầu tư tự tạo kho cổ phiếu cho mình.

Tại thời điểm bài giảng (27/5/2024), thầy lấy ví dụ với cổ phiếu HPG. Giả sử có 30.000 cổ phiếu HPG và 350 triệu tiền mặt, đầu tư dài hạn. Ngày 24/5, HPG bị bán sau phát biểu của chủ tịch. Quan sát: nến 24/5 là nến giả (đỏ) có thân dài, có chân nến dài, khối lượng giao dịch lớn hơn bình thường. Dấu hiệu này cho thấy có sự lưỡng lự, có nhóm đang mua vào, chứ không phải xả hàng hoàn toàn. Phán đoán: ngày 25/5 nhiều khả năng "yếu trước khỏe sau" (vì nến 24/5 là đỏ, theo đà).

Hành động: mua 10.000 cổ phiếu khi giá giảm, bán ngay khi giá tăng, thực hiện lặp lại. Cuối ngày 25/5, nến rút chân, phán đoán giá sẽ tăng lại. Ngày 26/5: nếu tăng thì không làm gì, nếu lưỡng lự thì tiếp tục quan sát cơ hội rebalancing. Vì đã phán đoán có số điểm kênh nến tăng nên mua trước bán sau. Lặp lại quy trình hàng ngày: mua trước bán sau vì phán đoán giá tăng, khả năng giảm tiếp thấp.

Lưu ý: cổ phiếu trên sàn Hà Nội hay TP.HCM đều có thể áp dụng rebalancing hàng ngày. Cổ phiếu trên sàn UpCOM biến động giá rất lớn, cách tính giá trung bình đặc biệt, cơ hội kiếm lợi nhuận từ rebalancing hàng ngày cũng có, nhưng mất thời gian.

## Hedging bằng hợp đồng tương lai

Hợp đồng tương lai là thỏa thuận mua hoặc bán chỉ số cơ sở (ở Việt Nam là VN30) ở một mức giá xác định vào một ngày trong tương lai. Theo cách dân giã nhất: đoán chỉ số. Mua hợp đồng tương lai là đoán lên, bán hợp đồng tương lai là đoán xuống. Nếu đoán đúng, lãi bằng chênh lệch; nếu đoán sai, lỗ tương ứng. Khi đã đoán, càng xa ngày đáo hạn thì đoán càng khó, basis (khoảng cách giữa giá phái sinh và chỉ số cơ sở) càng lớn.

Tại Việt Nam, hợp đồng tương lai 1 tháng là loại giao dịch nhiều nhất, đáo hạn vào khoảng thứ 5 thứ 3 của tháng. Có thể có hợp đồng xa hơn (1 quý trở lên), nhưng 1 tháng phổ biến nhất và đơn giản nhất. Ký quỹ ban đầu khoảng 13% giá trị hợp đồng, tức đòn bẩy khoảng 7-8 lần (bỏ 13 đồng có thể chơi giá trị 100 đồng). Phái sinh được đánh dấu theo thị trường hàng ngày (mark to market), nên lãi/lỗ được ghi nhận ngay. Nếu lỗ làm tài khoản giảm xuống dưới mức ký quỹ duy trì, nhà đầu tư phải nộp thêm tiền (nạp tài khoản). Ở Việt Nam có T+1 cho phái sinh, nên thực tế có thể làm ngay.

Hai tình huống dùng phái sinh để rào chắn:

Một, khi mua cổ phiếu xong nhưng nhận thấy mình sai (thị trường có thể giảm), T+3 chưa đến để bán, bán hợp đồng tương lai để sửa sai. Nếu đoán đúng, lời từ phái sinh bù một phần lỗ từ cổ phiếu; nếu sai, lỗ cả hai phía.

Hai, khi đang giữ cổ phiếu đến vùng kháng cự, muốn đợi breakout nhưng sợ giảm. Bán hợp đồng tương lai với giá trị tương đương danh mục để khóa vị thế. Nếu breakout thật, đóng vị thế phái sinh và tiếp tục nắm cổ phiếu; nếu giảm, lời từ short phái sinh bù lỗ từ cổ phiếu. Cách này cần ký quỹ chỉ khoảng 1/5 số tiền đã bán cổ phiếu.

Lưu ý: chọn thời điểm mua bán phái sinh dùng phân tích kỹ thuật thông thường. Thầy nhấn mạnh phân tích kỹ thuật áp dụng cho phái sinh còn tốt hơn cho cổ phiếu vì phái sinh diễn ra thường xuyên, hàng ngày. Trong phái sinh, phân tích kỹ thuật là đúng nhất vì diễn biến ngay trong ngày, dùng khung thời gian ngắn, điểm uốn là phù hợp.

Thầy cũng nói: giá trị phái sinh lớn gấp mấy lần cơ sở chỉ là so sánh tương đối với quy mô. Thực chất phải xét số tiền ký quỹ thôi, vì nhiều khi nhà đầu tư đã để sẵn tiền ký quỹ trong tài khoản từ trước, không phải bỏ thêm.

## Open Interest và phân tích dòng tiền

Trên đồ thị kỹ thuật ta nhìn khối lượng giao dịch (volume), thể hiện khớp lượng mua bán giữa các bên cũ và mới. Open Interest (OI) thể hiện số hợp đồng đang mở, phản ánh dòng tiền mới vào hoặc rút ra. Hai chỉ số này khác nhau: khi OI không đổi nhưng volume tăng, giống trường hợp "ông cũ chơi với nhau" (làm giá quay tay). Khi OI tăng, có nhà đầu tư mới tham gia; khi OI giảm, có người rời khỏi thị trường. Nếu OI không thay đổi mà volume lớn, đó là dấu hiệu những người trong sới đang trao đổi với nhau, gần giống làm giá quay tay.

Áp dụng phân tích OI theo vùng giá (tương tự phân tích giá-khối lượng, thầy nêu bốn tình huống mang tính minh hoạ):

OI cao ở vùng giá thấp, giảm dần ở vùng giá cao, hàm ý tiền vào yếu, khả năng đảo chiều cao.

OI thấp ở vùng giá cao, tăng dần ở vùng giá thấp, hàm ý tiền vào nhiều, khả năng đảo chiều xu thế giảm cao.

OI thấp ở vùng giá thấp, tăng dần ở vùng giá cao, xu thế nhiều khả năng tiếp diễn.

OI cao ở vùng giá cao, giảm dần ở vùng giá thấp, xu thế giảm tiếp diễn.

Cần chú ý đột biến OI ở cả vùng giá cao và vùng giá thấp, đây là hai khái niệm khác nhau dù chung từ "đột biến". Đột biến chỉ cần hơn bình thường là đủ, không nhất thiết OI phải bằng nhau giữa hai vùng.

Ngoài ra: nếu giá phái sinh khác xa giá cơ sở (basis lớn và liên tục mở rộng), phản ánh kỳ vọng mạnh về xu hướng. Phái sinh cao hơn cơ sở là kỳ vọng cơ sở tăng; thấp hơn là kỳ vọng giảm. Đây chỉ mang tính tương đối vì nhà đầu tư phái sinh có thể đoán sai hoặc cố tình thao túng giá.

## Ví dụ số về hedging

Tại thời điểm bài giảng (27/5/2024), thầy lấy ví dụ số cụ thể:

Giả sử vừa mua 2.000 cổ phiếu ABC giá 60.000 đồng/cổ phiếu, tổng giá trị 120 triệu đồng. Lo ngại thị trường giảm nhưng cổ phiếu chưa đến T+3 để bán. Hợp đồng tương lai VN30 1 tháng hiện tại có chỉ số nhân với 100.000 đồng, giá trị hợp đồng khoảng 132 triệu 250 ngàn đồng. Số tiền ký quỹ ban đầu cần có khoảng 17 triệu 192 ngàn 500 đồng.

Nếu thị trường giảm 5% như dự đoán: vị thế short hợp đồng tương lai sẽ lời khoảng 6.612.500 đồng (5% × 1 điểm × 100.000). Vị thế cổ phiếu lỗ 6 triệu. Trạng thái ròng: lời 612.500 đồng. Con số này không quan trọng về mặt tuyệt đối, vấn đề là trong 3 ngày chờ T+3, nhà đầu tư gần như không bị thay đổi tài khoản. Nếu không hedge, mỗi ngày lỗ 6-7 triệu từ cổ phiếu.

Vị thế khi đó: long cổ phiếu + short hợp đồng tương lai = closed position (đã khóa). Đây chính là hedge. Lưu ý: hedge không hoàn hảo vì giá trị cổ phiếu (120 triệu) khác giá trị hợp đồng (132 triệu 250 ngàn). Quy tắc: mở vị thế cổ phiếu thì phải đóng bằng một vị thế phái sinh tương ứng.

## Giới hạn và rủi ro của hedging

Hedging vẫn có rủi ro, đơn giản nhất là dự đoán sai. Tại Việt Nam, rủi ro lớn nhất là cổ phiếu không đi giống VN30 (correlation thấp). Cách khắc phục một phần: chọn cổ phiếu có beta gần 1 với VN30, hoặc hedging cả danh mục từ 5 mã trở lên (correlation với VN30 tốt hơn). Hedging chỉ một cổ phiếu đơn lẻ rất khó hiệu quả, vì nhà đầu tư cá nhân gần như không thể mua tất cả 30 cổ phiếu VN30 theo đúng tỷ lệ để tính ra chỉ số.

Với danh mục đa cổ phiếu, có thể bán hợp đồng tương lai để hedge cả danh mục. Nếu xu thế thị trường rõ ràng, dù cổ phiếu cụ thể không tương quan mạnh, vẫn có thể hedge bằng phái sinh. Nếu thị trường sideway thì hedge cũng khó, hedge trong một cổ phiếu đơn lẻ là mệt.

Thầy nhấn mạnh: hedging là phòng vệ rủi ro, không phải đầu cơ. Khi dùng phái sinh, hãy nhớ long = mua, short = bán. Hợp đồng tương lai phù hợp với người muốn khóa vị thế khi rơi vào tình huống T+3 không làm gì được. Nếu muốn đầu cơ, cần xác định rõ rủi ro: lời có thể lên tới 100% trong 1-2 ngày, nhưng lỗ cũng rất nhanh. Đừng sa đà vào speculation.

## Hỏi đáp

Có phải mở hợp đồng phái sinh trước khi mua cổ phiếu vì lo ngại giảm? Khi mua cổ phiếu, bản chất là đầu cơ để giá lên. Nếu mua xong thấy sai, T+3 chưa đến, lúc đó cách xử lý nhanh nhất là bán một hợp đồng tương lai (short phái sinh). Nếu đoán đúng thị trường giảm, có lời từ phái sinh; nếu cổ phiếu tăng thì lời cả hai; nếu cổ phiếu giảm nhiều thì lỗ cả hai. Hedging chỉ có ý nghĩa khi nhận thấy vị thế cổ phiếu bị sai rồi mới hành động, chứ nếu mua phái sinh trước khi mua cổ phiếu thì giống vừa mua vừa bán, không có ý nghĩa.

Phái sinh sẽ dùng tại khung thời gian nào, có dùng tại các điểm hỗ trợ và kháng cự không? Có hai vấn đề. Nếu dùng phái sinh đơn thuần để giao dịch (đầu cơ mua bán hợp đồng tương lai), thầy khuyên dùng khung thời gian ngắn, 30 phút là vừa đủ để người ta bình tâm trở lại, có thể ngắn hơn. Hợp đồng phái sinh giao dịch hàng ngày nên không dùng nến khung thời gian dài. Nếu đang giữ cổ phiếu và muốn hedge tại vùng kháng cự/hỗ trợ, cách làm: lock cổ phiếu bằng cách bán hợp đồng tương lai có giá trị tương đương danh mục. Ví dụ đang giữ cổ phiếu ở vùng kháng cự, khối lượng tăng, người ta bán, vẫn hy vọng breakout; sợ bán đi mua lại không kịp. Lúc đó bán phái sinh để khóa vị thế. Khi breakout thật thì đóng vị thế phái sinh (dùng long phái sinh để khóa hợp đồng tương lai), chỉ còn lại long cổ phiếu.

Open Interest nằm ở đâu, và trong giao dịch phái sinh trong ngày thì phân tích kỹ thuật tìm điểm uốn để mua đúng không? Open Interest có trên phần mềm giao dịch phái sinh, mục "Open Interest", một số phần mềm như Vietstock có sẵn, có thể mua data. Trong giao dịch phái sinh trong ngày, phân tích kỹ thuật là đúng nhất vì phái sinh diễn biến ngay trong ngày; dùng điểm uốn như đã hướng dẫn với khung thời gian ngắn. Phái sinh thường diễn biến nhanh, thị trường sideway thì hedge mệt, cần dùng phân tích kỹ thuật để ra vào.

Hướng dẫn đọc thông tin trong một tín hiệu phái sinh? Phái sinh ở đây là hợp đồng tương lai, tương tự một cổ phiếu. Tín hiệu long/short tương tự tín hiệu mua/bán cổ phiếu; người ta dùng long/short thay vì buy/sell vì là hợp đồng dựa trên tài sản cơ sở. Đơn giản: long = mua, short = bán. Các tín hiệu trong đó dựa trên phân tích kỹ thuật và Open Interest. Chi tiết hơn về sản phẩm phái sinh thầy đề nghị sẽ có buổi riêng.

Có những dấu hiệu nào để xác định vùng kháng cự và hỗ trợ làm cơ sở cho rebalancing? Nên xem lại bài phân tích kỹ thuật vì đã học vùng kháng cự và hỗ trợ rồi. Giải thích ngắn: kháng cự là vùng cao gần nhất trước đó, hỗ trợ là vùng thấp gần nhất. Các đường trend line lên/xuống cũng tạo vùng kháng cự/hỗ trợ. Cạnh trên/dưới của các mẫu hình giá (đi ngang, đi lên, đi xuống) cũng là vùng kháng cự/hỗ trợ.

Quỹ VN30 có dùng cổ phiếu VN30 để lái phái sinh, toàn bộ danh mục cổ phiếu quỹ có thực sự tốt để mình mua, quỹ có thông tin nên mua bán trước, quỹ cơ cấu mua vào dịp nào? Về lái phái sinh: các quỹ rebalancing dựa trên VN30, ETF dựa trên chỉ số, họ nắm nhiều cổ phiếu trong rổ, có thể có tác động lên giá cổ phiếu ảnh hưởng đến chỉ số, từ đó phục vụ vị thế phái sinh. Quỹ lớn vừa nắm phái sinh vừa nắm cơ sở, nắm cả hai đầu, giống nhà cái; nhà đầu tư cá nhân chơi phái sinh về bản chất là chơi với họ. Ngoài ra, công ty chứng khoán phát hành chứng quyền (cover warrant) cũng có động cơ tương tự. Ở Việt Nam, chỉ có chứng quyền mua, không có chứng quyền bán, trong khi quyền chọn chuẩn cần cả quyền mua và quyền bán để tạo sự cân bằng hai chiều. Tỷ lệ chuyển đổi chứng quyền ở Việt Nam bất lợi (kiểu 1:3, 3:1, khó tính), nên nhà đầu tư thường chỉ ăn chênh lệch giá chứng quyền, không chờ đáo hạn. Công ty chứng khoán nắm giữ cổ phiếu cơ sở phục vụ chứng quyền, chỉ cần tác động nhỏ vào giá cơ sở là chứng quyền nhà đầu tư gần như vô giá trị. Thầy chỉ nêu nghi ngờ, không khẳng định chính thức. Về cổ phiếu quỹ: cần phân biệt danh mục cổ phiếu quỹ đang nắm với cổ phiếu quỹ do công ty mua lại; danh mục quỹ nắm là đầu tư bình thường, cổ phiếu quỹ do công ty mua lại là khái niệm khác. Về thông tin: quỹ không hẳn có thông tin trước; nguyên tắc quỹ là đầu tư dựa trên đánh giá định giá và kỳ vọng, lời một chút thì bán vì giá cao, giá xuống một chút thì mua vì giá thấp. Ở Việt Nam, quỹ cũng hay gọi conference call hỏi nhà môi giới để có thông tin, chứ không phải có thông tin nội bộ. Về cơ cấu: quỹ thường cơ cấu vào ngày cơ cấu, thực hiện ở phiên ATC.

Phái sinh có nhiều điểm dễ bị làm giá hơn thị trường cơ sở không? Thị trường phái sinh có nhiều quỹ lớn tham gia, họ vừa nắm cổ phiếu cơ sở vừa đầu tư phái sinh. Ban đầu họ chỉ để ý phái sinh, sau thấy có thể tác động lên chỉ số thì họ làm. Thầy cho rằng họ có thể tác động, nhưng khó nói chính xác mức độ. Về bản chất, quỹ lớn vừa nắm cơ sở vừa chơi phái sinh giống nhà cái; nhà đầu tư cá nhân tham gia phái sinh khó tránh bất lợi.

Dùng cơ sở điều chỉnh phái sinh là sao, Q-long/short là cuộc chiến của các tay to, vậy có nên đầu tư vào VN30 không? Về diệt long/diệt short: khi một bên (long hoặc short) thao túng giá cơ sở để ép bên kia. Ví dụ quỹ short, họ mua cổ phiếu cơ sở để đẩy giá lên, làm bên short lỗ. Cá nhân nhỏ lẻ khó chống lại vì quỹ giao dịch lượng rất lớn hợp đồng. Đôi khi cá lẻ hợp tác gồng mua để đẩy giá lên, nhưng dễ diệt nhau khi đã gồng hết cỡ. Về có nên mua và nắm giữ VN30: theo quan điểm thầy, bình thường vì đã nắm cổ phiếu lớn thì nghĩ đến dài hạn. Dài hạn thị trường vẫn đi lên, và các quỹ nắm VN30 coi như đại diện cho tài sản Việt Nam. Nhưng nhà đầu tư cá nhân thường không nghĩ dài hạn; lý thuyết dài hạn đúng nhưng hành động thực tế ngắn hạn, đó là vấn đề của bản thân nhà đầu tư, không phải lý thuyết sai.

## Bối cảnh thị trường lúc giảng (05/2024)

Bài giảng quay ngày 27/5/2024. Tại thời điểm đó, thầy quan sát thị trường và đưa ra các nhận định mang tính thời điểm, dùng làm ví dụ minh hoạ cho lý thuyết rebalancing:

- Chỉ số VN-Index đang tiệm cận vùng kháng cự quanh 1.300 điểm, cách khoảng hơn 10 điểm (chỉ một phiên). Trong chương trình Bia Hơi Vỉa Hè trước đó, thầy đã đặt câu hỏi về tâm lý hành vi khi gần tiến tới vùng 1.300 điểm.
- Ngày 24/5/2024: chỉ số có dấu hiệu rebalancing tại vùng hỗ trợ (mẫu hình 3 điểm chạm, nến rút chân, khối lượng tăng). Cổ phiếu HPG bị bán sau phát biểu của chủ tịch; nến ngày là nến giả dài có chân dài và khối lượng lớn, cho thấy có sự lưỡng lự.
- Ngày 27/5/2024: nến xanh, giá tiệm cận kháng cự. Thầy dự đoán phiên 30/5 sẽ có sự lưỡng lự tại kháng cự 1.300, cụ thể "khỏe đầu yếu sau".
- Ngày 30/5/2024 (dự đoán): nếu chỉ số tiệm cận 1.300 điểm, có thể thực hiện rebalancing bằng cách bán tại kháng cự khi khối lượng tăng rồi mua lại sau.

Các mốc này chỉ có giá trị minh hoạ cho cách áp dụng lý thuyết rebalancing tại thời điểm bài giảng. Lý thuyết về rebalancing, hedging, Open Interest là nội dung cốt lõi của bài và không phụ thuộc vào ngày tháng.
