# V4 2023-01 - 11 - Tong ket hoc phan - Bai giang va hoi dap

Buổi tổng kết học phần phân tích kỹ thuật, vừa ôn lại 5 chủ đề lý thuyết đã học vừa thực hành trên đồ thị chỉ số theo 6 bước, kết thúc bằng phần hỏi đáp dài. Tại thời điểm bài giảng (khoảng đầu 01/2023, theo tên file), thầy đánh giá xu thế dài hạn vẫn là giảm, ngắn hạn vừa trải qua một đợt hồi phục tăng và đang đi vào kết thúc, chiến lược là mua nhanh vào nhanh ra nhanh hoặc đứng ngoài.

## Tổng kết 5 chủ đề đã học

Học phần phân tích kỹ thuật gồm 5 nhóm chủ đề chính, học theo hướng đơn giản nhất thay vì đi vào chi tiết phức tạp.

Chủ đề 1 là cung cầu, giá trị, hỗ trợ kháng cự và các đường xu hướng. Chủ đề 2 là nến và các hành động giá ở từng cây nến khác nhau. Chủ đề 3 là phân tích các chỉ số kỹ thuật và cách sử dụng kết hợp với giá. Chủ đề 4 là các mẫu hình kỹ thuật — học phần đã giới thiệu 36 mẫu hình, nhưng thầy thống nhất là có nhiều nhóm mẫu hình tương tự nhau, không cần nhớ hết 36 mà chỉ cần nắm nguyên tắc. Chủ đề 5 là khoảng trống giá và đột phá, kèm theo nhận diện các loại khoảng trống giá khi xuất hiện, và đề cập một chút chiến lược mua bán — phá vỡ kháng cự, breakdown, mua hỗ trợ hay mua đuổi momentum, cùng các lý thuyết phổ biến như Dow, sóng Elliott, Wyckoff.

Trong 5 nội dung, chủ đề 5 chủ yếu là phần thầy giới thiệu để học viên biết. Các lý thuyết phổ biến thoạt nhìn rất phức tạp nhưng thực ra đều dựa trên nguyên tắc đơn giản: thị trường luôn ở một trong 3 trạng thái — trung bình, quá lên hoặc quá xuống. Mỗi lý thuyết đưa ra nhìn nhận khác nhau nhưng đều không nằm ngoài những gì QMV đã đề cập: liên quan tới chu kỳ kinh tế, luân chuyển ngành, luân chuyển ròng tiền và 3 trạng thái tâm lý.

## Nguyên tắc nhận diện xu hướng

Khi thực hiện phân tích kỹ thuật, điểm cực kỳ quan trọng là phải nhận diện được xu hướng thị trường và không nên cưỡng lại thị trường. Đây là nguyên tắc cơ bản nhất.

Về công cụ, người theo trường phái kỹ thuật thường dùng các chỉ số và đường kẻ kỹ thuật, nhưng thực tế phải kết hợp cả phán đoán vĩ mô, không thể bỏ qua vĩ mô. Trong giới hạn học phần này thầy tập trung vào chỉ số kỹ thuật, nhưng nhắc lại là khi nhận diện xu hướng phải đặt trong bối cảnh vĩ mô, không được bỏ qua cơ bản.

Khi nhận diện được xu hướng rồi, bản chất sẽ có 3 trạng thái. Một là thị trường tăng, hai là thị trường giảm, ba là sideways. Khi thị trường tăng thì nguyên tắc là mua và nắm giữ dài hơn, gia tăng vị thế. Khi thị trường giảm thì nguyên tắc là đứng ngoài hoặc chơi phái sinh. Khi thị trường sideways thì mua bán ngắn hạn, T+, vào nhanh ra nhanh, kết hợp rebalancing. Ví dụ khi thị trường vừa trải qua giai đoạn giảm mạnh và đang ở giai đoạn sideways giằng co thì nguyên tắc là mua bán ngắn hạn, T+, vào nhanh ra nhanh.

Trong bất cứ tình huống nào khi phân tích cổ phiếu, nguyên tắc là không nên cưỡng thị trường. Thị trường phải đi trước, cổ phiếu đi sau.

## Sáu bước phân tích kỹ thuật

Bước mang tính chi tiết cụ thể để học viên hình dung cách thực hiện. Khi đã quen thì không nhất thiết phải theo tất cả các bước.

### Bước 1: Xác định xu hướng

Trong phạm vi bước này, thầy dùng kỹ thuật là chính, không bàn vĩ mô. Để xác định xu hướng có thể dùng đường trung bình, đường xu hướng, sóng Elliott, lý thuyết Dow, lý thuyết Wyckoff.

#### Đường trung bình

Bắt đầu bằng đường trung bình. Trên đồ thị sẽ có hệ thống chỉ số, gõ tìm moving average. Bấm 3 lần vì muốn chọn 3 thông số thông dụng nhất để xác định xu hướng rồi chỉnh sửa sau. Thông số 9 là mặc định, phục vụ quyết định ngắn hạn. Để xác định xu hướng dài hơn, thầy chọn 3 thông số thông dụng là 20 ngày (đại diện 1 tháng giao dịch), 50 ngày (đại diện 1 quý) và 200 đơn vị (đại diện 5 quý). Ba đường này có thể tô màu khác nhau cho dễ nhìn, cùng với đường giá.

Về nguyên tắc, nếu đường ngắn hạn cắt đường dài hạn thì phản ánh xu thế tương ứng với kỳ hạn đó. Ví dụ xu thế ngắn cắt lên xu thế trung hạn (khung 50) thì phản ánh xu thế tăng. Khi có dấu hiệu quay trở lại thì xu thế tăng đó đã yếu và chuẩn bị kết thúc. Nếu nhìn xu thế tăng lớn thì thực ra không có xu thế tăng lớn vì đường 50 vẫn đang nằm dưới đường 200 — đây là lúc xu thế tăng trưởng dài hạn tính theo chu kỳ kinh tế đã kết thúc.

Tại thời điểm bài giảng, thầy nhận xét xu thế tăng trưởng lớn của thị trường là xu thế giảm. Tính theo chu kỳ kinh tế thì thị trường đang ở trong xu thế giảm, dài hạn là chưa tốt, vẫn đang giảm. Ngắn hạn và trung hạn thì xong, ngắn hạn vừa trải qua giai đoạn tăng và đã kết thúc, có thể dẫn tới giảm tiếp theo.

Về Golden Cross (điểm cắt vàng) — khi đường 50 cắt đường 200, tăng lên thì có ý nghĩa tích cực, giảm xuống thì thị trường đã chuyển sang giai đoạn giảm điểm. Những người theo trường phái mua và nắm giữ dài hạn thì khi thấy điểm cắt vàng đi xuống sẽ đứng ngoài thị trường, dù điểm đó hình thành thì thị trường đã điều chỉnh một đoạn rồi. Về mặt dài hạn, xu thế giảm sau khi xảy ra điểm cắt vàng sẽ kéo dài.

#### Đường xu hướng

Khi vẽ đường xu hướng dài hạn, với xu thế giảm thì nối đỉnh, với xu thế tăng thì nối đáy. Đường giảm dài hạn đạt yêu cầu khi đỉnh sau thấp hơn đỉnh trước, đáy sau thấp hơn đáy trước. Khi đáy sau không còn thấp hơn đáy trước nữa thì tạm coi đường xu thế giảm đã bị phá vỡ. Đường xu hướng không nhất thiết phải vẽ chính xác tuyệt đối, có thể vẽ đơn giản cũng được, quan trọng là hình dung được giai đoạn giảm mạnh.

Khi giá cắt xuống đường xu hướng tăng ngắn hạn, đoạn tăng gần nhất đã kết thúc, đoạn hồi phục ngắn hạn kết thúc. Đường MA chậm hơn đường xu hướng vì phản ánh trung bình giá. Đường xu hướng phản ánh cái nhìn tức thời và mới chỉ nói lên xu hướng tăng mạnh ngắn hạn kết thúc. Khi giá rơi xuống dưới vùng đáy trước đó thì xu thế tăng mới coi như bị phá vỡ.

#### Sóng Elliott

Sóng Elliott có thể vẽ trong giai đoạn ngắn hạn hoặc dài hạn. Nguyên tắc của sóng Elliott nguyên bản yêu cầu sóng 3 phải dài nhất và sóng 4 không được rơi xuống dưới đỉnh của sóng 1. Nếu vẽ không đảm bảo nguyên tắc này thì phải đếm lại sóng.

Ví dụ khi vẽ sóng 1, 2, 3, 4, 5 mà đảm bảo nguyên tắc sóng 3 lớn nhất, sóng 4 không rơi xuống dưới sóng 1, và cả đoạn 1, 2, 4 và sóng ABC đều đang đẩy vào bức cựu đó, thì đang nằm trong sóng C điều chỉnh — có nghĩa là có thể tiếp tục làm một giai đoạn giảm. Tại thời điểm bài giảng, dù vẽ theo cách nào thì xu hướng ngắn hạn đang nghiêng về khả năng giảm. Về dài hạn, đường MA 50 vẫn đang dưới 200 và sóng Elliott dài hạn đang nằm ở sóng 5, nên thị trường cũng chưa tăng. Sóng C điều chỉnh thông thường còn dài hơn sóng A.

#### Fibonacci

Khi sóng A, B, C đang giảm và muốn biết giảm tối đa đâu, dùng Fibonacci. Cách làm là lấy đoạn tăng trước đó, kéo Fibonacci retracement từ đáy lên đỉnh. Các đường Fibonacci phản ánh retracement, mức 38,3% là mức đầu tiên cần chú ý, các mức tiếp theo tương ứng với kháng cự và hỗ trợ — những vùng có thể xảy ra phản ứng. Nếu tin bước 6 năm thì giá hoàn toàn có thể về tới đó, thậm chí xa hơn. Cá nhân thầy nghiêng về khả năng giá sẽ đi kéo dài hơn là dễ về tới vùng dưới 38,3%.

### Bước 2: Kiểm tra kháng cự hỗ trợ

Khi nói tới hỗ trợ thì nên dùng một vùng chứ không phải một con số cụ thể. Hỗ trợ bao giờ cũng lấy đáy gần nhất, nhưng nếu vùng đó tạo ra sự lưỡng lự thì nên coi cả vùng rộng hơn là vùng hỗ trợ.

Kháng cự cũng có thể có nhiều vùng. Vùng kháng cự mạnh là khi khối lượng giao dịch lớn và tương ứng với đỉnh trước đó. Nếu giá hồi phục thì khi chạm vùng kháng cự nhiều khả năng sẽ rơi. Nếu giá rơi thì sẽ gặp vùng hỗ trợ.

Ý nghĩa của việc xác định kháng cự và hỗ trợ là: một là nhiều khả năng tạo điểm mua khi giá về vùng hỗ trợ; hai là rất quan trọng để quyết định vào lệnh hay không vào lệnh. Khi giá về vùng hỗ trợ, cần so sánh tỷ lệ rủi ro/lợi nhuận: nếu mục tiêu giá đạt yêu cầu và lợi nhuận kỳ vọng lớn hơn 1 lần stop-loss thì đó là quyết định tốt. Nếu tỷ lệ tương đương nhau (5-5 thua) thì không phải good trade, không nên vào lệnh. Nếu stop-loss lớn hơn mục tiêu thì tỷ lệ thắng/thua nhỏ hơn 1, cũng không nên vào.

### Bước 3: Mẫu hình kỹ thuật

Khi kiểm tra mẫu hình kỹ thuật, có thể tưởng tượng hoặc cần công cụ chính xác đều được. Nếu coi đoạn hiện tại là kênh giao động ngang thì kỳ vọng đây là điểm chạm, và đây cũng là điểm chạm. Khi kênh giao động gặp đường kháng cự, có thể bật lên. Lần thứ 2 chạm thì khả năng bật cao, lần thứ 3 thì chưa chắc lắm, nhưng vẫn có thể đi theo kênh.

Có thể có kênh dao động xuống — đây cũng là cái thầy vẽ trên Bia Hơi Vỉa Hè. Thầy nghiêng về kênh dao động xuống hơn. Về mặt xu hướng thì vẫn giảm, nhưng khi gặp vùng hỗ trợ thì sẽ bật lên, gặp vùng kháng cự thì lại rơi xuống rồi tiếp tục xu thế giảm. Đỉnh 1, 2 — nếu điểm thứ 3 bứt lên được thì sẽ bứt, nếu không bứt thì khả năng cao sẽ gặp lên rồi lại rơi xuống một lần nữa.

Kênh giao động xuống có thể tạo thế bật lên, nhưng khi bật lên thì sẽ gặp đường kháng cự.

### Bước 4: Chỉ số kỹ thuật

Thầy đưa chỉ số CCI và RSI. Về xu hướng thì đường RSI vẫn giảm — đỉnh sau thấp hơn đỉnh trước, đáy sau thấp hơn đáy trước. Mọi nguyên tắc phân tích kỹ thuật dùng cho giá đều có thể áp dụng tương tự cho chỉ số kỹ thuật. Nếu coi toàn bộ khu vực RSI đang dao động là khu hỗ trợ thì cả khu vực này cũng là khu cầu/hỗ trợ. Nếu chỉ số tiếp tục đi xuống trong khi đường trung bình hướng lên thì sẽ tạo ra phân kỳ dương — đó là cơ hội mua khi chỉ số chạm vùng hỗ trợ.

Tại thời điểm bài giảng, xu hướng của các chỉ số RSI và CCI đều vẫn đang xuống, vì đều có đỉnh sau thấp hơn đỉnh trước, không có dấu hiệu tạo đỉnh uốn. Theo nguyên tắc thì cứ để cho nó chạy bình thường, đừng cố nghĩ. Một khi nó tạo ra điểm uốn theo hướng tạo phân kỳ dương thì đó là cơ hội chốt đỉnh. Dựa trên phân tích ở các bước trước thì đây chỉ là cơ hội ngắn hạn, chốt đỉnh ngắn — vào nhanh, ra nhanh, T+. Nếu không nhanh, không tự tin hoặc không có thời gian thì tốt nhất đứng ngoài. Một khi không tin rằng thị trường tăng thì cứ đứng ngoài.

### Bước 5: Phân tích giá/lượng

Phân tích giá/lượng là cái rất quan trọng. Khi giá đang xuống thì khối lượng cũng đang xuống — khối lượng giảm là bình thường. Có thể làm đường MA cho khối lượng, dùng MA mặc định hoặc 5 ngày, 1 tuần. Khi khối lượng nằm dưới đường trung bình tức là không có gì đột biến, mọi thứ bình thường.

Cái cần chú ý là khi giá không còn giảm nữa (lưỡng lự hoặc giao động) và lượng cũng không giảm nữa, rồi có dấu hiệu tăng lên — tức là vượt lên khỏi đường trung bình. Không nhất thiết phải đột biến, chỉ cần tăng lên là đã có cơ hội. Vì khi giá giảm, về nguyên tắc khối lượng phải giảm: bên mua thấy chưa hấp dẫn nên không mua, giá cứ giảm, khối lượng cứ giảm. Nhưng đến lúc giá không giảm và khối lượng giao dịch cũng không giảm thì bắt đầu có cơ hội.

Ví dụ với nến 30 phút: nếu giá tăng 2 cây và lượng tăng lên thì tức là tăng trên pha người ta bán. Sau đó một cây nến đỏ giảm mạnh nhưng khối lượng không tăng — cây nến tiếp theo giá tăng nhẹ, lượng không tăng nhiều. Như vậy lượng lớn ở đây là do bị úp sọan: những người chờ mua bị bán bất ngờ, chưa có điểm mua thực sự về giá. Nếu vậy thì khả năng để giá chạy tiếp diễn là cao.

Ngược lại, khi giá về vùng hỗ trợ và khối lượng giao dịch tăng lên thì khả năng cao do bên mua nhiều — lúc đó khả năng tạo điểm uốn để đi lên là cao.

### Bước 6: Phân tích mẫu nến tại khu vực hiện tại

Mẫu nến ở khu vực hiện tại khá chừng — có nến giảm, nến lưỡng lự, nến lưỡng lự nữa rồi tạo kênh nến sang, nhiều mẫu phù hợp cho bên đang giảm: nến lưỡng lự và giá tăng, nhưng giá tăng tạo kênh nến lưỡng lự và nến lưỡng lự ngay lập tức dẫn tới giảm. Giai đoạn này là giai đoạn mà bên mua và bên bán rất bất an, không có xu hướng rõ ràng.

Nếu nhìn nến ngày gần nhất, đây là mẫu hình không tốt — đang tăng gặp mẫu Evening Star. May mắn là đoạn tăng trước đó rất ngắn nên đoạn giảm tiếp theo có thể cũng ngắn tương tự. Khi giá rơi về vùng hỗ trợ và tạo mẫu nến spring (nến rút chân) kết hợp nhiều yếu tố (gặp vùng kháng cự/hỗ trợ) thì đó là dấu hiệu tốt.

Tại buổi học, thầy nghiêng về khả năng thứ hai: giá sẽ rơi xuống rồi hồi phục lại một chút, rồi sẽ lình xình vài phiên trước khi về được vùng hỗ trợ theo kênh đã vẽ, rồi bật lên.

Trong buổi học không có khoảng trống giá đặc biệt để xem xét, nên không cần quan tâm nhiều.

## Điểm thầy nhấn mạnh

Tóm lại qua 6 bước phân tích thì xu thế hiện tại ngắn hạn của thị trường là đang đi xuống. Khi về vùng hỗ trợ có khả năng tạo phân kỳ dương, và khi khối lượng giao dịch vượt lên khỏi đường trung bình thì có thể tạo cơ hội đảo chiều. Đảo chiều ở đây chỉ là ngắn hạn — vẫn đang trong giai đoạn chốt đỉnh ngắn hạn. Cách phân tích thị trường như vậy có thể áp dụng tương tự cho cổ phiếu mà mình quan tâm. Cổ phiếu dù tốt mấy cũng không nằm ngoài quy luật thị trường — thị trường phân tích trước, cổ phiếu phân tích sau.

Khi có người giới thiệu cổ phiếu, điều đơn giản nhất là phải nhìn vào đồ thị. Đừng nhắm mắt nghe người khác phím mà không nhìn đồ thị. Thầy biết nhiều trường hợp lái, người gieo tin hay kêu gọi phân lớn đều ở đỉnh. Rất ít tình huống người mới gom nói chắc chắn mà bảo mua đi. Nếu nói mua ở vùng đáy thì đồng nghĩa chỉ tăng vài ba phiên là bán rồi, họ không còn cơ hội ra hàng. Nguyên tắc là các đội làm giá, làm lái bao giờ cũng ra tin và kêu gọi mua ở một chỗ đau đó đủ để người ta bắt đầu ra hàng — tức là dụ người ta vào để mua và để bán. Cho nên tuyệt đối đừng nhắm mắt mà phải nhìn chart.

Đường xu hướng dùng để đánh giá độ mạnh yếu thôi. Để xác định kháng cự và hỗ trợ thì phải nhìn theo nguyên tắc ngang — cái gì ngang bằng thì người ta dễ nhìn thấy hơn. Cái gì mang tính đường chéo thì người ta không tính được. Khi thấy thông tin kêu gọi cổ phiếu mà nhìn thấy nó ở vùng đỉnh trong kháng cự, khối lượng giao dịch lớn thì tốt nhất là bỏ qua. Đây là bài học xương máu: rất nhiều người thấy hay quá vì lúc đó ra toàn tin cơ bản rất hay, rất đẹp về cổ phiếu nào đó, khối lượng rất lớn — tuyệt đối không nên mua.

Phân tích kỹ thuật phản ánh tâm lý thị trường. Nếu đọc phân tích kỹ thuật tốt thì có thể hiểu thị trường đang nghĩ gì. Cá nhân thầy đánh giá rất cao khối lượng giao dịch đột biến — nó luôn cảnh báo một cái gì đó. Mua bên bán hay lái, người ta có thể dấu, có thể lừa, nhưng riêng khối lượng giao dịch thì không lừa được. Người ta phải mua vào bán, mua bán thì phải tạo ra khối lượng. Kể cả khi gom muốn tạo dấu chuối, mua trao tay thì cũng vẫn tạo ra khối lượng. Ở những giai đoạn cổ phiếu giảm mạnh và tạo ra vùng có khối lượng giao dịch cực lớn thì chắc chắn người ta đang gom. Việc gom không có nghĩa người ta sẽ đánh lên — vùng này người ta phải gom vì nếu không gom thì đội khác có thể gom.

Khi phân tích mà thấy sai thì tốt nhất là chuyển lạng, phải thay đổi ngay, đừng cố thay đổi quan điểm. Mua vì lý do gì thì bán theo đúng lý do đó.

## Bối cảnh thị trường lúc giảng (01/2023)

### Nhóm ngành ưu tiên khi chuẩn bị ra báo cáo tài chính

Tại thời điểm bài giảng, thầy nhận xét nhóm ngân hàng đã tăng rất nhiều và sẽ không còn thú vị nữa. Khi nhóm này hết thú vị thì các nhóm có dấu hiệu ổn hơn ở giai đoạn sắp tới sẽ thay thế. Các nhóm phù hợp với giai đoạn này gồm: vật liệu xây dựng, bất động sản (luôn nằm ở đầu mỗi đoạn tăng), dịch vụ tài chính nhưng là chứng khoán (không phải bảo hiểm — bảo hiểm không thuộc nhóm này), thực phẩm đồ uống, hóa chất, ngân hàng, tài nguyên cơ bản. Tài nguyên cơ bản như sắt thép cũng là cơ hội có thể chuẩn bị tới.

Nhóm ngân hàng đang hút hơi — mỗi khi nhóm ngân hàng dừng cuộc trời thì chuẩn bị bước sang một giai đoạn mới. Nhóm hóa chất và thực phẩm đồ uống đảm bảo được cả cơ bản tốt và tính chu kỳ dòng tiền ngành ổn. Đây là những nhóm phù hợp với giai đoạn này.

Nếu xét về nhóm có lợi nhuận vượt trội thì dầu khí hay hóa chất là những ngành đáng quan sát. Danh mục quan sát QMV dựa trên thuật toán cơ bản đánh giá rủi ro mô hình kinh doanh, kết hợp phân tích chu kỳ luân chuyển ngành và dòng tiền, sẽ sớm được chốt lại và gửi tín hiệu cho học viên.

### Về bất động sản và chứng khoán dính trái phiếu

Tại thời điểm bài giảng, nếu nói về vùng mua lớn thì bất động sản có thể đang ở giai đoạn xấu nhất. Thầy khuyên chờ thêm một chút, chờ đến khi kết quả kinh doanh của họ ra đã. Lý do: sau khi lo ngại lãi suất phát đi nhẹ nhàng, lo ngại tiếp theo của thị trường là vấn đề kinh doanh bất ổn kéo dài. Kinh tế còn khó khăn, người ta sẽ cần thêm một lần chiết khấu giá nữa. Suy nghĩ con người phải đi tuần tự: lãi suất ảnh hưởng tới định giá, còn kết quả kinh doanh phản ứng, điều chỉnh — có thể làm giá cổ phiếu tăng dạng theo kỳ vọng giá trị. Cho nên kiên nhẫn chờ đợi thêm.

### Về nhịp mua gom khi giá và khối lượng đều thấp

Cổ phiếu ở vùng giá thấp nhưng khối lượng giao dịch vẫn thấp thì chưa nên mua gom. Căn nguyên không phải là khối lượng giao dịch vẫn thấp mà là khối lượng giao dịch không giảm nữa. Khi giá không giảm, dừng giảm, khối lượng giao dịch cũng dừng giảm thì lúc đó bắt đầu ổn. Đến khi khối lượng giao dịch bắt đầu tăng lên là lúc tăng rồi. Câu hỏi "chưa nên mua gom" vừa đúng vừa không đúng: hoàn toàn có thể chia ra để mua ở những tình huống như vậy. Ví dụ định mua làm 3 lần thì lần 1 vào 1 phần 3, sau đó vào tiếp khi giá dừng giảm, khối lượng giao dịch không giảm nữa. Không thể biết đến khi nào bùng lên nhưng hoàn toàn có thể chia ra mua.

### Về nhận diện vùng hỗ trợ mạnh qua đồ thị

Vùng hỗ trợ khó giảm (đội nhóm đang gom) có thể nhận biết qua đồ thị bằng cách nhìn vào khối lượng giao dịch tại vùng đó. Ở vùng hỗ trợ thông thường khối lượng giao dịch rất ít. Nếu vùng đó có khối lượng giao dịch lúc giá tăng lên mà lớn thì đó là vùng hỗ trợ tương đối mạnh, vì nó đạt yêu cầu là có nhiều người quan tâm. Ở vùng đỉnh khối lượng mới mạnh, còn ở vùng đáy khối lượng thường rất nhỏ.

Về việc đội nhóm gom — đoán thôi, không biết thông tin chính xác. Khi giá không giảm và thấy duy trì trong một khoảng thời gian, thực sự trên thị trường có rất nhiều nhóm gom. Ví dụ gom rất điển hình: giá không tăng, không giảm; lượng cũng vậy; trong khoảng thời gian rất dài. Thầy nhắc tới một số cổ phiếu thân thuộc có mô hình gom điển hình nhưng transcript không nhận dạng rõ tên mã `[?mã — ASR: "tc 6 thân cọc 6" và "nbc"]`.

### Về quan sát phản ứng giá ở vùng kháng cự/hỗ trợ

Khi giá về vùng kháng cự và hỗ trợ, phải quan sát phản ứng ở các điểm kháng cự và hỗ trợ trước đó: phản ứng nhanh, phản ứng mạnh hay phản ứng từ từ. Đó là dấu hiệu để xem người ta cò cưa về giá như thế nào — giống kiểu mặc cả. Ví dụ vùng hỗ trợ trước đó kéo dài rất lâu chứng tỏ người ta mặc cả, thấy mua cũng được nhưng chưa hấp dẫn lắm. Phán đoán liệu tình huống tương tự có xảy ra hay không. Đừng máy móc cứ nhìn ở đó rồi nghĩ nó phải bật lên. Bên cạnh đó phải tìm thông tin xem nó có bật lên hay phải mặc cả nữa. Diễn biến giá và lượng ở giai đoạn đó cho rất nhiều thông tin về việc người mua người bán đang mặc cả thế nào.

Khi thấy một hiện tượng xảy ra thường xuyên thì khả năng đúng cao hơn. Mức kháng cự hoặc hỗ trợ mà đã xảy ra nhiều lần thì chứng tỏ đó là mức hỗ trợ và kháng cự mạnh.

## Hỏi đáp

Khi phân tích theo các bước đều ổn nhưng xem lệnh toàn thỏ vào thì có nên mua không, hoặc ngược lại chỉ 1-2 tín hiệu nhưng sói bắt đầu mua thì có nên mua theo? Khi quyết định mua hay không, điều cực kỳ quan trọng là mức giá. Nếu tin vào phân tích kỹ thuật và vùng giá đó là vùng nghĩ là nhảy vào mua thì người ta không đổ vào. Ví dụ người ta gom một cổ phiếu mất vài tháng, sau đó giá vừa mới tăng khoảng 10% thì chẳng ai lại đi đổ vào cho cả. Nếu giả sử bán thì đó chỉ là hành động của thị trường đơn thuần. Một khi đã tin vào phân tích kỹ thuật và mọi thứ đều ổn thì nên vào. Trường hợp thứ 2 — 1-2 tín hiệu mà sói bắt đầu mua: sói thì cũng là lệnh lớn hơn thôi. Quan điểm thầy là dựa vào phân tích kỹ thuật trước, sử dụng thông tin thỏ cáo để hỗ trợ. Phải xác định cái gì là chính, cái gì là hỗ trợ — kỹ thuật là chính, thông tin thỏ cáo là hỗ trợ. Đừng nhầm lẫn đảo vị trí hai cái này.

Trong sóng Elliott, tại sao sóng 3 lại là sóng dài nhất? Sóng 3 là sóng dài nhất trong lý thuật của Elliott. Nếu giống như mô hình nghi ngờ, đoạn thứ 2 vừa thấy hiện tăng dựa trên cơ sở nền tảng cơ bản và sự tăng trưởng hồi hồi thái quá. Đoạn thứ 3 tạm gọi là tăng trưởng trong trạng thái hồ hời thái quá dẫn tới chủ quan. Đoạn 1 mang tính nghi ngờ, đoạn 3 hoàn toàn tin tưởng và dẫn tới lạc quan, đoạn 4 lạc quan thái quá. Sóng Elliott dựa trên 3 trạng thái vừa tâm lý vừa cơ bản kết hợp, nên sóng 3 phải dài nhất để đảm bảo lý thuyết. Nguyên bản còn yêu cầu sóng 4 không được thấp hơn sóng 1. Thực tế sau này người ta vẽ cũng khá linh hoạt, không nhất thiết phải theo đúng lý thuyết.

Giai đoạn này nên chờ điểm 4 để rebalancing hay ra luôn? Khi dùng từ rebalancing thì đã xác định là dài hạn rồi. Nếu đã xác định giữ dài hạn thì hoàn toàn có thể nghĩ tới việc cứ để, vì nếu đang ở gần vùng hỗ trợ thì không phải lúc bán. Nếu rebalancing thì phải rebalancing từ trước đó. Còn ngắn hạn thì vào nhanh ra nhanh — vào nhanh, nếu sai thì vẫn phải ra. Ví dụ ngày thứ 2 mà giá giảm mạnh mà lại ra thì không hợp lý, vì đang gần tiệm cận vùng có điểm uốn. Nếu ngày thứ 2 đầu tiên lình xình (không tăng) thì hoàn toàn có thể bán và sẽ có lúc chụp xuống để vào lại. Ngày thứ 2 sẽ tình trạng tăng rồi giảm, nhưng khả năng chạm về vùng hỗ trợ và tạo cây nến khá cao — có thể ngày thứ 2 hoặc ngày thứ 3.

VNlutch hiện tại vẫn trong trạng thái thoát khỏi trend giảm dài hạn. Nếu mua bán cổ phiếu theo chu kỳ dài hạn thì có nên yên tâm nắm giữ cổ phiếu cơ bản tốt và định giá dài đẹp cao hơn định giá hiện tại không? `[?mã — ASR: "VNNlutch"]`. Theo nhìn của thầy, vùng này có thể nghĩ đến việc mua dài hạn rồi nhưng thời điểm mua thì nên đợi tới hết quý 1 để xem kết quả kinh doanh. Thị trường chắc chắn sẽ phản ứng với kết quả kinh doanh. Về mặt vùng giá không kể giảm 10% hay vài phần trăm thì không nói, về mặt thời điểm thì ổn có thể là hết quý 1.

Thông thích thêm về nhóm đầu tư công xem khối lượng như vậy đã đột biến chưa, có phải tín hiệu đang ra hàng không hay mới chỉ tăng, vì báo chí nói đầu tư công còn mạnh trong cả năm nay. Thầy yêu cầu lấy một cổ phiếu cụ thể, làm thử rồi post ở phần hỏi đáp kiến thức để thầy và mọi người cùng nhìn vào — nêu cổ phiếu cụ thể đầu tư công cũng giống phân tích index, không có nhiều ý nghĩa.

Cổ phiếu ở vùng giá thấp nhưng khối lượng giao dịch vẫn thấp, chưa gom được, chưa nên mua gom đúng không? (xem phần Bối cảnh thị trường lúc giảng)

Về ngưỡng hỗ trợ mạnh, khó giảm, đội nhóm đang gom được không, ví dụ với người ít thông tin về cổ phiếu mà chỉ nhìn đồ thị? (xem phần Bối cảnh thị trường lúc giảng)

Sóng Elliott mang tính cảm tính rất nhiều, mẫu hình cũng tùy quan điểm, chưa kể chỉ số RSI và CCI đôi lúc trái ngược nhau. Khi sóng Elliott, mẫu hình, chỉ báo mâu thuẫn thì thầy sẽ theo dõi thêm hay dựa vào tiêu chí nào khác để đánh giá, hay cứ để nó chạy? Khi dùng quen một vài chỉ số thì tự nhiên tạo ra niềm tin. Trong tình huống các chỉ số thể hiện cùng một kết luận thì tin nhiều hơn. Trong tình huống chỉ số này theo kết luận khác, chỉ số kia theo kết luận khác thì rất khó ra quyết định. Tốt nhất trong tình huống đó thì cứ để nó chạy — nguyên tắc là cứ để chạy, đừng lấy đường đoán. Nếu nó đang tăng thì tại sao phải nghĩ nó chuẩn bị điều chỉnh để tăng? Nếu đang giảm thì cũng vậy. Khi điều chỉnh cả biến số thì định giá cũng thay đổi, cùng một biến số vĩ mô ông thấy tốt thì khen vĩ mô tốt, ông thấy xấu thì cho rằng vĩ mô không đúng kỳ vọng — có rất nhiều cách, hoàn toàn cảm tính. Dần dần dùng nhiều thì tạo thành thói quen. Lời khuyên là có thể tham khảo nhiều nguồn, nhiều chuyên gia nhưng để biết thông tin chứ không phải để nghe chuyên gia kết luận. Nếu không bảo ra được phán đoán riêng thì kết quả sẽ giống kiểu chuyên gia này là chỉ số kỹ thuật, chuyên gia khác là chỉ số kỹ thuật khác, mỗi chỉ số lại khác nhau. Cái quan trọng là cuối cùng phải hình thành được đánh giá cho chính mình. Thầy hay dùng RSI và CCI nhưng có người khác dùng chỉ số hoàn toàn khác cũng ok — chọn cái cảm thấy tin được, quen dùng thì cứ dùng đó.

Mua nhóm đầu tư công hôm bùng nổ, chiều thứ 6 hàng về mình thấy tăng nhẹ và VNNDX `[?chỉ số — ASR: "VNNDX"]` thì bị bán. Quyết định bán lúc 2h25 là đúng hay sai, vì khoảng 2h20 phút có thể bùng lên theo cách đã xác định? Rủi ro chứng khoán không nằm ở cổ phiếu mà nằm ở nguyên tắc. Nguyên tắc mà sai thì đó là rủi ro. Cổ phiếu thì đừng nghĩ mình là người an toàn hay không an toàn — mình là người an toàn, hoàn toàn có thể chơi cổ phiếu đánh đấm bình thường, rủi ro của cổ phiếu là khách quan. Hai cái đó rất khác nhau. Một khi đã xác định giai đoạn này vào nhanh ra nhanh, kể cả cắt lỗ thì đó là nguyên tắc. Việc vào hàng xem ra không có sai — quan điểm thầy lúc này là phải vào nhanh ra nhanh, vào vì nghĩ rằng nó bật thì khi bật rồi và kể cả không bật thì vẫn ra. Đừng thay đổi là đợi thêm.

Với kinh nghiệm của thầy, cho xin chút view trong phiên sáng và phiên chiều của ngày thứ 2. Nhận định cá nhân phiên thứ 6 tạo nến đỏ nhưng vẫn cao hơn phiên trước đó, khối lượng không giảm, có thể phiên thứ 2 sẽ tiếp tục giảm để chiều tạo nên spring. Thầy cũng nghĩ thị trường ngày thứ 2 nhiều khả năng sẽ trộn xuống rồi kéo lên — không kéo nên vào ngày thứ 2 thì ngày thứ 3 chắc kéo lên. Nếu ngày thứ 2 đầu phiên lình xình, thậm chí tăng nhẹ thì rồi cũng lại giảm xuống một lần nữa. Với điều kiện thị trường như thế này, có thể cần thêm một lần nhúng rồi mới kéo lên. Bước sóng hiện tại đang là bước sóng giảm và có sự lình sinh trong vài phiên. Phiên gần nhất là nến giảm mạnh thì khả năng tiếp diễn cao, nhưng thực ra giảm mạnh hôm thứ 2 mà đầu phiên tốt thì khả năng bật lên cao, đến phiên thứ 3 sẽ hình thành bước sóng tiếp theo trong hộp đang nhìn.

Trong giai đoạn này nên dùng chỉ báo gì phù hợp nhất, RSI và CCI vào vùng quá bán nhưng tâm lý thị trường xấu thì hành động thế nào? Khi chỉ số vào vùng quá bán thì chưa nói lên điều gì nhiều, phải nhìn tiếp tục xu hướng của nó và xem mức kháng cự/hỗ trợ của chính những chỉ số đó trước đây thế nào. Nếu máy móc chỉ nhìn vào vùng quá bán thì đang nhìn rất đơn giản. Các chỉ số khi phân tích có thể sử dụng tất cả nguyên tắc phân tích kỹ thuật cho chỉ số. Phải xem nó đã tiếp cận vùng hỗ trợ của chính nó chưa, dù vào vùng quá bán nhưng có thể còn quá bán nữa. Câu hỏi đặt ra là nó vào vùng hỗ trợ chưa, hay có khả năng tạo phân kỳ không. Khi lên vùng quá mua thì cũng không hẳn là phải bán ngay.

Nhận định về kinh tế Việt Nam năm 2023 và các quỹ tài chính đánh giá thị trường Việt Nam thế nào? Đánh giá nhiều lần trong các chương trình Trà Chiều. Về quỹ đầu tư, những quỹ nắm giữ tài sản và phân bổ tài sản lớn không coi Việt Nam là điểm đầu tư. Các quỹ đầu tư vào Việt Nam của người nước ngoài thì hoặc đem quà về hộ, hoặc vào với tư cách đánh nhanh thắng nhanh thôi. Một số quỹ đang bay dở Việt Nam như Dragon Capital hay Vina Capital thì chắc chắn luôn nói tốt về thị trường. Các tổ chức kinh tế như ADB hay Ngân hàng Thế Giới thì chưa bao giờ nói xấu kinh tế Việt Nam — nếu chỉ đọc báo thì thấy người ta luôn nói Việt Nam là điểm sáng. Nhìn nhận cá nhân thầy: kinh tế Việt Nam năm 2023 sẽ tiếp tục gặp khó khăn, doanh nghiệp khó khăn rất nhiều.

Trước khi vào chương trình Bia Hơi Vỉa Hè, thầy có thể chia sẻ một vài ý vĩ mô cá nhân được không? Thầy chưa hiểu ý của hỏi, tốt nhất viết vào phòng hỏi đáp kiến thức để trao đổi sau. Về Fama-French — đây là nhân vật làm chủ yếu về mô hình định giá, đã tới 5 factor rồi (các nhân tố tác động tới lợi nhuận chứng khoán: ví dụ vốn hóa nhỏ, cổ phiếu giá trị sẽ mang lại lợi nhuận tốt hơn, vượt trội so với nhóm khác). Trong mô hình gần đây khoảng 10 năm trở lại đây còn nói về giá trị, mức tăng trưởng của doanh nghiệp, momentum. Nghiên cứu kiểu Fama-French dựa trên số liệu quan sát được trong vài chục năm qua và trên rất nhiều nước thì xung khắc với Việt Nam — vì Việt Nam chủ yếu đánh ngắn hạn, cứ mỗi 1 năm rebalancing 1 lần nhưng phải giữ cổ phiếu trong vài chục năm thì mới đúng.

Khi nhiều người biết quá thì xác suất bị sai, chia sẻ với số lượng học viên ít hơn? Ý này cũng hay nhưng có một câu chuyện nữa: nhóm nghe Bia Hơi Vỉa Hè so với cả thị trường rất ít. Một khi muốn những gì mình nghĩ là đúng thì cần nhiều người biết. Tại sao lại không nghĩ ngược lại — nếu có cách tiếp cận hay cổ phiếu quan tâm mà tốt thì phải muốn cho nhiều người biết, vì mình biết tốt chưa đủ, người khác phải biết tốt thì giá mới lên được. Đề nghị này thầy lưu ý nhưng câu chuyện có 2 mặt: nếu mình nghĩ là ổn nhưng người khác không nhìn thấy điều đó thì nó có thể thành không ổn. Chuyện này rất hay nhưng phải chia sẻ ở thật là bao giờ nó có hai mặt.

Nhóm cổ phiếu bất động sản, chứng khoán có dính đến trái phiếu, như bây giờ có được coi là xấu nhất chưa? (xem phần Bối cảnh thị trường lúc giảng)

Ý kiến về nhóm cổ phiếu nên ưu tiên khi ra báo cáo tài chính quý 1? (xem phần Bối cảnh thị trường lúc giảng)

Nhóm hóa chất giai đoạn này, Trung Quốc mở cửa bị cạnh tranh cao, mấy năm trước phát triển do Trung Quốc đóng cửa, năm nay kỳ vọng giảm, đánh giá thế nào? Đánh giá dựa trên cơ sở mô hình kinh doanh và bản chất giữa Trung Quốc mở cửa bị cạnh tranh thì nằm trong vấn đề chiết khấu giá — giá phải lành điều đó rồi. Nhìn theo mô hình kinh doanh, mức độ rủi ro chu kỳ kinh doanh, đừng nhìn vào kết quả cụ thể. Trung Quốc mở cửa thực ra ảnh hưởng rất nhiều nhóm chứ không chỉ hóa chất. Đánh giá chung về mô hình kinh doanh theo ngành để phán đoán ngành nào được chú ý và hưởng lợi trong giai đoạn hiện tại.

Khi giá về đến điểm kháng cự hay hỗ trợ, thầy bảo nên quan sát lại phản ứng của giá ở các điểm kháng cự hỗ trợ trước đó có nghĩa là như thế nào? (xem phần Bối cảnh thị trường lúc giảng)