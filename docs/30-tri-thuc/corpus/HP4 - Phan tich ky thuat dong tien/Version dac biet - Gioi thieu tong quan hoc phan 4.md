# Version dac biet - Gioi thieu tong quan hoc phan 4

Bài giảng giới thiệu tổng quan học phần 4 (Phân tích kỹ thuật dòng tiền) trong hệ thống 5 học phần của QMV. Đây là buổi học thứ ba, dành cho người mới tiếp cận phân tích kỹ thuật theo cách đơn giản của QMV: chọn ít chỉ số, hiểu bản chất, không học thuộc mọi mẫu hình. Bài quay ngày 12/08/2024. Phần Hỏi đáp cuối buổi có thầy phân tích VN-Index tại thời điểm quay.

## Tổng quan 5 chủ đề của học phần 4

HP4 gồm 5 chủ đề: thứ nhất là cung cầu, giá lượng, ngưỡng kháng cự và hỗ trợ; thứ hai là nến và cách phán đoán hành động mua bán dựa trên nến; thứ ba là các chỉ số kỹ thuật; thứ tư là mẫu hình giá (thống kê xu hướng lớn); thứ năm là khoảng trống giá, lý thuyết đột phá, và các lý thuyết phổ biến về chứng khoán như Dow, Wyckoff, Elliott.

Trong buổi tổng quan này, thầy chọn tập trung kỹ vào 3 chủ đề đầu tiên, coi chủ đề 4 và 5 là phần tham khảo thêm. Lý do: mẫu hình giá là thống kê từ thị trường phương Tây với khung thời gian rất ngắn, mức độ tin cậy ở thị trường Việt Nam không cao, dù có hay nhờ nhiều người cùng biết. Còn Dow, Wyckoff, Elliott là lý thuyết dựa trên chu kỳ kinh tế gắn với luân chuyển ngành và luân chuyển dòng tiền, cùng triết lý 3 phần (quá, bình thường, quá) mà QMV đang xây dựng. Thầy nhấn mạnh 3 chủ đề đầu đơn giản nhưng cực kỳ quan trọng, và là phần thầy dùng nhiều nhất khi phân tích kỹ thuật.

## Cung cầu, giá lượng và phân tích VPA

Cung cầu là biểu hiện của thông tin, nhưng ta chỉ quan sát được khối lượng giao dịch, không biết cung lớn hơn hay cầu lớn hơn và lớn bao nhiêu. Tuy nhiên giá tăng chứng tỏ cầu lớn hơn cung. Để hiểu một ngày cụ thể cần kết hợp cả cung cầu lẫn viên nến.

Nguyên tắc chung: giá tăng, lượng tăng bình thường hoặc không tăng, đều bình thường. Nhưng giá tăng mà lượng tăng đột biến là bất thường, chuẩn bị có chuyện. Khi giá giảm, lượng giảm là bình thường; lượng tăng đột biến cũng bất thường, dù mức độ đột biến ở vùng giảm không tương đương vùng đỉnh. Thầy dùng nguyên tắc ngược lại với những người thấy lượng lớn là mua ngay hay bán ngay: lượng bao giờ cũng là cảnh báo. "Lượng đi trước giá" là nguyên tắc chung nhưng có trường hợp lượng đi sau giá, nên không thể kết luận chắc chắn.

Theo nguyên lý kinh tế: đường cung dốc xuống (giá thấp lượng bán ít, giá cao lượng bán nhiều), đường cầu dốc xuống (giá thấp lượng mua nhiều, giá cao lượng mua ít). Hai đường giao nhau tạo ra khối lượng và giá giao dịch. Trong chứng khoán, cầu tăng có 2 lý do: người ta nhiều tiền hơn, hoặc kỳ vọng giá trị tương lai lớn hơn. Lý do thứ hai vẫn phụ thuộc vào việc cuối cùng người ta có tiền để mua hay không, thầy luôn nhấn mạnh "tiền vẫn là quan trọng nhất". Vì vậy phải đi theo luân chuyển ngành rồi mới đến luân chuyển dòng tiền.

Các tình huống cụ thể: khi cầu tăng (đường cầu dịch phải) thì giá tăng và lượng tăng, đó là bình thường. Khi cung tăng (đường cung dịch phải) thì lượng tăng, giá giảm, đây là dấu hiệu bán ra mạnh. Khi cung giảm thì lượng nhỏ, giá tăng, thầy gọi là "tiết cung" `[?ASR nghe "tết cung"]`. Đây là trạng thái tốt vì bên bán hạn chế bán. Tuy nhiên tiết cung đồng nghĩa với việc có ngày nào đó sẽ bán giấc mạnh, giống như nhóm tích lũy đẩy giá lên sẽ có hôm bán ra. Nguyên tắc chung: dù tiết cung hay không, quan trọng là giá tăng, chứng tỏ cầu lớn hơn. Nếu khối lượng tăng đột biến mà giá chững lại hoặc giảm, thì đó chắc chắn là bán rất mạnh.

Giá tăng nhưng lượng giảm cũng là trạng thái bình thường, nhưng cuối cùng sẽ có ngày khối lượng phải mạnh. "Đột biến" ở đây không có nghĩa là phải cao phải lớn, mà chỉ là khác với bình thường. Khi nhìn thấy cái gì đó khác bình thường, đó là lúc nó biến.

### Phân tích theo giai đoạn

Một xu thế giảm luôn đặc trưng bởi giá giảm, lượng giảm (cầu không quan tâm). Nhưng khi giá ngừng giảm, lượng lại tăng, đó là dấu hiệu cầu bắt đầu quan tâm. Còn một xu thế tăng đặc trưng bởi giá tăng, lượng bình thường hoặc tăng. Khi giá ngừng tăng, lượng tăng đột biến, đó là bán.

Thầy thường xuyên dùng con số 3 và nguyên tắc chia 3 mức (thấp quá, bình thường, cao quá). Áp dụng: giá đang tăng từ vùng thấp chạy lên vùng bình thường thì lần điều chỉnh đầu tiên chưa đáng ngại, hy vọng còn tiếp tục tăng; giá ở vùng bình thường rồi mà chỉnh thì có lý do để lo ngại; giá ở vùng quá cao mà chỉnh thì phải lo ngại. Thầy dặn: "đừng có dại mà bắt đáy ở những lần đầu tiên" trong xu thế xấu, lần thứ 2 cơ hội cao hơn, lần thứ 3 cao hơn nữa.

Kinh nghiệm thầy: khi gặp khối lượng đột biến, bao giờ cũng có một độ trễ, chủ yếu do T+ (chu kỳ thanh toán). Trước đây thầy nói T+3, thực tế T+2 đến T+3 là chính xác hơn. Khối lượng giảm lớn muốn bắt đáy phải đợi đến ngày thứ 3, vội quá thường hơi sớm. Tuy nhiên quy tắc này thường đúng khi khối lượng giao dịch lớn. Nếu khối lượng lớn mà giá vẫn tăng thì vẫn còn hy vọng tăng thêm 1-2 hôm, nhưng phải bán trước ngày T+3.

### VPA trong xu thế tăng

Giá tăng mạnh mà lượng giảm gợi ý mua mạnh nhưng bên bán không bán, xu thế tiếp diễn. Giá tăng lượng tăng cũng bình thường, mua mạnh thì bên bán cũng bán ra. Khi nhiều người biết về tiết cung, một ngày xuất hiện khối lượng mạnh thì việc bán gần như chắc chắn. Còn trường hợp giá tăng, lượng tăng đều, một hôm xuất hiện khối lượng lớn thì bán là đúng nhưng mức độ tin cậy thấp hơn tình huống tiết cung. Thầy cảnh báo: các nhóm lái thường rơi vào tình huống giá tăng lượng tăng, hết sức chú ý.

Phân tích VPA của thầy gần như trùng với phân tích giá lượng (VPA trong transcript có khi bị ASR nghe thành "VTA") và dựa trên kiến thức kinh tế học vĩ mô. Cần kết hợp cả giá lượng lẫn tâm lý hành vi.

## Nến

Một cây nến là biểu hiện của cung cầu tại một thời điểm, phản ánh tương tác cung cầu trong ngày và tâm lý bên mua bên bán. Nến cũng biểu hiện thông tin cơ bản, với giả định người ta chỉ mua khi thấy điều gì đó tích cực (tâm lý hoặc cơ bản). Một cây nến bất thường (ví dụ nến đỏ dài xen giữa xu hướng tăng) có 2 khả năng: do thông tin (bền) hoặc do tâm lý (không bền, nhanh quay về bình thường). Nếu nến lạ xuất hiện mà không có thông tin gì thì có thể chỉ là tâm lý và không tiếp diễn.

Cách đọc nến của thầy không dựa vào tên mẫu hình mà dựa trên 3 yếu tố: độ dài thân nến, độ dài bóng nến (bóng trên, bóng dưới), vị trí thân nến so với 1/3 cây nến. Ba tình huống cơ bản: thân nến ngắn (gần như đường nằm ngang) thì thị trường không thay đổi gì, thường tiếp diễn xu thế trước đó; thân nến dài nhưng bóng ngắn, hoặc bóng dài ở một phía, thể hiện lưỡng lự cực lớn giữa bên mua và bên bán, khả năng đảo chiều, mức độ tin cậy phụ thuộc vào vị trí thân nến (1/3 trên hay 1/3 dưới) và chiều giá trước đó; thân nến bao phủ toàn bộ cây nến thì tương tự thân nến và độ dài bằng nhau, xu thế tiếp diễn.

Thầy gọi tắt là 2 tình huống: lưỡng lự và chắc chắn. Cây nến cũng có thể ở trạng thái bình thường (giữa) nhưng ý nghĩa thông tin thấp. Quy tắc quan trọng: nến đỏ lưỡng lự trong xu thế tăng thì tin cậy hơn nến xanh lưỡng lự; vị trí thân nến ở 1/3 trên thì khả năng đảo chiều cao hơn ở giữa; nến lạ thường xuất hiện ở vùng kháng cự/hỗ trợ hoặc khi hết tin, nếu không có gì hỗ trợ xu thế mà xuất hiện nến lạ chiều ngược thì là dấu hiệu nguy hiểm; kết hợp nến với VPA thì mức độ tin cậy cao hơn.

### Ghép nến

Thầy ghép tối đa 3 cây nến, vì trong vòng 3 hôm còn đủ vòng quay T+ và thể hiện tâm lý. Ghép 2 nến đỏ liên tiếp: lấy giá mở cửa của nến đầu, giá đóng cửa của nến sau, cao nhất và thấp nhất của cả giai đoạn, thành 1 cây nến hợp nhất. Ghép 3 nến cũng tương tự. Sau khi ghép, quay lại áp dụng nguyên lý 2 tình huống (lưỡng lự hoặc chắc chắn). Thầy nhấn mạnh không cần nhớ nhiều mẫu hình (Morning Star, Evening Star), cuối cùng tất cả đều quy về 1 cây nến duy nhất và 2 tình huống cơ bản. Vẫn nên biết nhiều mô hình nhưng phải hiểu gốc của nó.

## Chỉ số kỹ thuật

Phần lớn chỉ số kỹ thuật đều dựa trên giá và lượng, và phần lớn giống nhau. Phần lớn dựa trên giá mà bỏ qua lượng. Thầy khẳng định: không cần biết hết chỉ số, chỉ cần biết một vài cái dễ dùng và thấy tin cậy. Có người chỉ dùng 1 chỉ số để giao dịch thông suốt.

Chia 2 nhóm chính: chỉ số sức mạnh xu hướng xoay quanh một mốc (ví dụ 0-100, hoặc xoay quanh một ngưỡng) như RSI, Stochastic; đường trung bình động gắn liền với đường giá, tính theo chu kỳ (50 ngày tương đương 1 tháng, 200 ngày tương đương 1 năm).

Ba cách dùng chỉ số trong QMV: đường ngắn cắt đường dài là tín hiệu (cả MACD, Stochastic, MA đều dùng nguyên lý này); vùng quá mua/quá bán, ví dụ Stochastic dải 30-70, CCI dải -100 đến +100, khi vào vùng này là dấu hiệu chú ý chứ không phải vào là bán ngay; phân kỳ, tức đường giá và đường chỉ số không cùng hướng. Phân kỳ âm (giá tăng tạo đỉnh sau cao hơn đỉnh trước, nhưng chỉ số đỉnh sau thấp hơn đỉnh trước): giá có thể dừng tăng hoặc điều chỉnh, chưa kết luận là giảm ngay. Phân kỳ dương (giá giảm tạo đáy sau thấp hơn, chỉ số đáy sau cao hơn): giá có thể khó giảm thêm.

Cách dùng kết hợp vùng quá mua/quá bán với phân kỳ thì mức độ tin cậy cao hơn. Phân tích kỹ thuật phải dùng kết hợp nhiều thứ với nhau, kể cả cơ bản và vĩ mô. Thầy dặn: nếu chỉ dùng phân tích kỹ thuật thì đủ trong khoảng thời gian ngắn khi các thông tin vĩ mô chưa kịp thay đổi; nhìn trong thời gian dài hơn thì các yếu tố vĩ mô chi phối.

Thầy đưa ví dụ các đường MA 5, 50, 200 ngày. Đường 5 cắt 50 là tín hiệu ngắn hạn. Đường 50 cắt 200 là tín hiệu mang tính chất dài hạn cho xu thế giá tăng. Dải Bollinger cũng là dạng đường trung bình động có độ lệch chuẩn. MACD là chỉ số giữa momentum và trung bình động, nguyên lý sử dụng vẫn là cắt lên cắt xuống quanh đường 0; khoảng cách 2 đường MACD lớn vượt lên 0 thể hiện xu thế giá tăng, rơi xuống dưới 0 thể hiện xu thế giá giảm.

## Mẫu hình giá

Có 36 mẫu hình (thực tế có thể tới cả trăm), là thống kê từ thị trường nước ngoài, không phải luôn đúng. Ở Việt Nam, mức độ tin cậy thấp hơn, đặc biệt là các đường xu hướng chéo. Nguyên tắc: cái gì dễ nhìn mới đáng tin. Hỗ trợ và kháng cự nằm ngang dễ nhìn, đường xu hướng khó nhìn. Vì vậy các đột phá ngưỡng kháng cự/hỗ trợ ngang tin cậy hơn đột phá đường xu hướng chéo.

Thầy ưa thích mẫu hình có ít nhất 2 điểm chạm, thông thường xảy ra ở điểm chạm thứ 2 và 3. Quy tắc đơn giản cuối cùng: mẫu hình đi ngang (dao động ngang) thì xu hướng tiếp diễn; mẫu hình dao động lên hoặc xuống thì xu hướng đảo chiều (hồi lại). Mẫu hình chỉ bổ trợ thông tin, không thay thế được thị trường chung và kinh tế vĩ mô.

## Khoảng trống giá, lý thuyết Dow, Wyckoff, Elliott

Khoảng trống giá (gap) cũng giống một nến đặc biệt, là nến mở cửa rất sớm, giống nến marubuzu đặc biệt. Nếu xác định là gap mà không có thông tin gì thì chứng tỏ đó là nến mang tính tâm lý, không phải cơ bản. Đột phá ngưỡng kháng cự/hỗ trợ tương tự nhau, nhưng đột phá khó hơn, mức độ chính xác ít hơn.

Ba lý thuyết Dow, Wyckoff, Elliott đều xoay quanh 3 giai đoạn. Dow: các chỉ số các ngành cùng chiều hoặc bổ trợ cho nhau, có giai đoạn tích lũy, tăng trưởng, phân phối. Wyckoff: cũng 3 giai đoạn tích lũy, tăng trưởng, phân phối, thêm yếu tố tâm lý hành vi qua Spring (nến đạp xuống kéo lên) và Upthrust (kéo lên xả ra). Sóng Elliott: xu thế tăng gồm 5 sóng (3 sóng đẩy 1, 3, 5 và 2 sóng điều chỉnh 2, 4), xu thế giảm là 3 sóng điều chỉnh. Bản chất cũng là 3 phần: quá, bình thường, quá (quá tích cực).

Thầy khẳng định: lý thuyết Dow, Wyckoff, Elliott thực chất đang nói cùng một triết lý 3 phần mà QMV xây dựng trong luân chuyển ngành và luân chuyển dòng tiền. QMV cũng đang xây dựng lý thuyết riêng về chứng khoán dựa trên triết lý này, thể hiện qua luân chuyển ngành, luân chuyển dòng tiền và mô hình tiền-cổ phiếu. Dow, Wyckoff, Elliott là lý thuyết chuyên sâu, gắn với chu kỳ kinh tế, áp dụng trong chu kỳ dài thì khả năng đúng cao hơn. Áp dụng trong khung ngắn (ngày, tuần) sẽ không đúng vì xa rời bối cảnh lý thuyết ban đầu. Riêng sóng Elliott thì áp dụng khung ngắn còn ổn.

## Hỏi đáp

Tăng giảm như thế nào là bình thường? Câu hỏi liên quan đến việc xác định mức bình thường của khối lượng. Thầy nhắc lại: phải nhìn bằng mắt, con số tăng 20-30% không có nhiều ý nghĩa vì còn phụ thuộc tương quan giữa giá và lượng. Khi có Blackbox, sẽ nhìn được tăng giảm bất bình thường. Thầy cho biết đội ngũ IT đang làm rất khẩn trương, dự kiến cuối tuần (thứ 2 tuần sau) sẽ có bản dùng thử.

Áp dụng phân tích giá lượng vào VN-Index hiện tại như thế nào? Thầy giao bài tập: phân tích rồi đưa lên Discord để cùng xem, chuẩn bị cho buổi Bia Hơi Vỉa Hè cuối tuần. Gợi ý cụ thể: nến cuối tuần là nến mua khỏe, lượng có tăng không, tăng bình thường hay đột biến.

Phân tích về RSI và VN-Index. Học viên hỏi RSI giảm sâu nhưng giá không đi theo là phân kỳ. Thầy thừa nhận không rõ cơ hỏi vì thầy hay dùng RSI và CCI. Câu hỏi tiếp: VN-Index đồ thị thứ 6 thấy bật lên rồi, RSI đang ở vùng thấp, có phải điều tốt để mua không? Thầy đáp: nhìn vào RSI và CCI thì thấy bình thường, giá vẫn trong xu thế tăng, chỉ số vẫn trong xu thế tăng bình thường, không thấy dấu hiệu bất thường. Theo nguyên tắc, cái gì bình thường thì cứ để nó chạy.

Tại thời điểm bài giảng (08/2024), thầy phân tích diễn biến giá lượng VN-Index trên đồ thị. Kết luận: giá tăng, lượng không tăng (lượng bình thường), đây là dấu hiệu tiết cung, bên bán hạn chế bán, bên mua giữ giá. Đây là điều tốt. Tuy nhiên nếu một hôm xuất hiện khối lượng giao dịch lớn mà là nến đỏ thì phải cẩn thận. Về nến: nến ngày thứ 6 là nến tốt. Về chỉ số kỹ thuật: không thấy dấu hiệu lạ, mọi thứ vẫn bình thường. Đây là phân tích thuần kỹ thuật, chưa tính đến yếu tố vĩ mô.

Cách sử dụng giá lượng để phát triển Blackbox? Thầy trả lời ngắn: sẽ nói khi giới thiệu công cụ, có thể tìm bản ghi trên Discord.

Bot chốt đỉnh, robot chốt đỉnh có ưu thế thống kê và tốc độ, cá nhân/thủ công sẽ dần khó hơn? Thầy nhận xét: ở phương Tây, bot chốt đỉnh đã chiếm khoảng 60% giao dịch cách đây 10 năm, 40% còn lại là giao dịch chủ động của quỹ. Tuy nhiên thanh khoản thị trường phương Tây lớn hơn nhiều. Ở Việt Nam, dùng iCopyTrade hay bot thì tạo ra sự nguy hiểm: khi bot báo, tất cả cùng nhảy vào mua hoặc bán, dẫn tới mất thanh khoản ngay lập tức. Thay vì bị người dụ thì bị máy dụ, kẹt lại. Thanh khoản cổ phiếu Việt Nam ít quá, chỉ có một vài mã làm được. Ví dụ 1 sản phẩm giao dịch tự động có 1.000 người copy theo cùng một lập luận là chết. Tự tạo công cụ cho mình thì OK, đi theo công cụ chung thì không khác gì bị một người dụ cả thị trường.

Trong Blackbox Money có phải chính là lượng trong phân tích kỹ thuật không? Giá tăng nhẹ nhưng Blackbox Money rút tiền ra khỏi hộp nhiều. Thầy xác nhận: dựa trên nguyên lý cung cầu sẽ xác định được tiền vào/ra cổ phiếu. Thuật toán thì không tiết lộ.

Trong một ngày có 2 tay to sang tay cổ phiếu chiếm phần lớn khối lượng giao dịch thì ảnh hưởng đến giá và xu hướng như thế nào? Thầy thừa nhận: khi người ta cố tình tạo ra giao dịch mang tính chất không thật thì rất khó nói. Chúng ta học để biết nguyên lý chung, còn gặp tình huống người ta cố tình lừa thì khó. Đây là lý do trên thị trường Việt Nam phân biệt cổ phiếu game và cổ phiếu live, phải để ý đến ý chí của đội live chứ không đơn giản chỉ dùng kiến thức kỹ thuật.

Phân kỳ ngắn và dài. Học viên hỏi: khi phân tích khung dài, nhiều phiên, phân kỳ sẽ không còn tin cậy. Thầy giải thích: khi phân tích phải giữ trên cơ sở tại giai đoạn đó có thông tin gì thay đổi hay không. Nếu có thông tin thay đổi thì đỉnh cũ/đáy cũ có thể không còn ý nghĩa nhiều. Đáy gần nhau thì mức độ tin cậy cao hơn đáy xa nhau, vì môi trường chính sách ở xa có thể đã khác.

Lên cao xét cung, xuống dưới xét cầu, hay ngược lại là quan trọng hơn? Thầy không phân định cái nào quan trọng hơn, chỉ phân tích theo đúng logic nguyên lý cung cầu trong kinh tế học. Giá đang tăng (cầu lớn hơn cung) thì khối lượng giao dịch do bên bán quyết định, vì cầu lớn, người ta bán ra bao nhiêu thì giao dịch bấy nhiêu. Vì vậy khi khối lượng lớn, giá tăng, thầy coi đó là tiền ra chứ không coi là tiền vào, nhiều người nghĩ tiền vào nhưng thầy nói tiền ra.

Công ty chứng khoán có nhiều công cụ giống Blackbox hay MarketStructure không? Thầy nói: việc họ có công cụ nào là do người lãnh đạo nghĩ được cái gì thì thiết kế cái đó, không phải cứ công ty chứng khoán là có. Blackbox của QMV là công cụ đưa cả tính toán số cổ phiếu mua vào bán ra, số tiền vào và bán ra, số tiền vào và thu về ở trên thị trường. Chỗ khác có thể chấm điểm, nhưng thầy không thích chấm điểm mà thăm dò tâm lý con người.
