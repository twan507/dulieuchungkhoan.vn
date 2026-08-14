# Tâm lý và thông tin

Tầng lý thuyết phía sau việc đọc hành vi thị trường: thông tin bất cân xứng vận hành thế nào, tài chính hành vi phát biểu gì, lý thuyết trò chơi soi sáng động cơ từng bên ra sao. File này giải thích **cơ chế**; phần đọc tâm lý thực hành nằm ở `co-van-chung-khoan-vn/references/doc-hanh-vi-thi-truong.md`, file này không lặp lại.

## Mục lục

- [Ba cấp độ người chơi và ba cấp độ thông tin](#ba-cap-do-nguoi-choi-va-ba-cap-do-thong-tin)
- [Lý thuyết trò chơi: tù nhân, Nash và các dạng mở rộng](#ly-thuyet-tro-choi-tu-nhan-nash-va-cac-dang-mo-rong)
- [Ví dụ: ma trận lợi ích trò chơi giữ tin – lộ tin](#vi-du-ma-tran-loi-ich-tro-choi-giu-tin-lo-tin)
- [Trò chơi ra hàng và bốn giai đoạn đẩy giá](#tro-choi-ra-hang-va-bon-giai-doan-day-gia)
- [Thông tin bất cân xứng và ba hệ quả](#thong-tin-bat-can-xung-va-ba-he-qua)
- [Quy trình chính sách](#quy-trinh-chinh-sach)
- [Tín hiệu doanh nghiệp và event study](#tin-hieu-doanh-nghiep-va-event-study)
- [Áp dụng: thị trường tín dụng](#ap-dung-thi-truong-tin-dung)
- [Thị trường hiệu quả và tài chính hành vi](#thi-truong-hieu-qua-va-tai-chinh-hanh-vi)
- [Thiên lệch có tên và chân dung nhà đầu tư](#thien-lech-co-ten-va-chan-dung-nha-dau-tu)
- [Đầu tư giá trị nằm ở sự vô lý](#dau-tu-gia-tri-nam-o-su-vo-ly)

---

## Ba cấp độ người chơi và ba cấp độ thông tin

| Cấp | Chủ thể | Vai | Tính chất thông tin phát ra |
|---|---|---|---|
| 1 | Chính phủ | Đặt luật chơi, không phải người chơi | Chính sách. Tác động toàn thị trường |
| 2 | Doanh nghiệp | Người chơi | Kết quả kinh doanh, tăng vốn, phát hành, cổ tức. Chỉ đưa ra thứ họ muốn mình thấy |
| 3 | Trò chơi ở cấp một mã: nhà tạo lập, kênh loan tin, nhà đầu tư nhỏ lẻ | Người chơi | Tin loan qua kênh không chính thống, kèm giá mục tiêu. Phạm vi một mã |

- **Xếp hạng chính sách theo mức quan trọng với chứng khoán:** tiền tệ (quan trọng nhất, tác động toàn thị trường) → tài khoá và chương trình hỗ trợ (chủ yếu tạo ưu thế ngành) → chính sách kinh tế khác. Tỷ giá không phải chính sách tiền tệ nhưng tác động gần như vậy.
- **Trong chính sách tiền tệ, tách hai lớp:** kênh liên ngân hàng (thị trường 2) là thanh khoản liên ngân hàng — nhạy nhất, tác động ngay; kênh tín dụng vào kinh tế thực (thị trường 1) là tiền giao dịch thực trong nền kinh tế — phụ thuộc kỳ vọng, chạy chậm.
- **Mọi thông tin nhận được đều là tin thứ cấp**, kể cả tin nội gián — nó vẫn là một phần của trò chơi; kiểm chứng bằng vùng giá và khối lượng trước khi đọc nội dung. Và **điều mình nghĩ đúng không quan trọng bằng điều thị trường nghĩ**: biết một doanh nghiệp kém trong khi cả thị trường tin nó tốt thì vẫn phải thừa nhận giá đang lên, việc của mình là chọn khung thời gian tham gia chứ không phải chứng minh mình đúng.

## Lý thuyết trò chơi: tù nhân, Nash và các dạng mở rộng

**Ngắn hạn, chứng khoán là trò chơi tổng bằng không** — kỳ vọng hai bên trái ngược, giá đi một hướng thì một bên được, bên kia mất. Lập luận phản bác dựa trên lợi nhuận và cổ tức doanh nghiệp chỉ đúng nếu giả định nhà đầu tư giữ suốt vòng đời doanh nghiệp và không giao dịch. Dài hạn thì khác: với người đầu tư dài hạn dựa trên doanh nghiệp tốt, hai bên cùng có lợi. Tình huống tù nhân, số năm tù:

| A \ B | B im lặng | B khai |
|---|---|---|
| **A im lặng** | 1 / 1 | 3 / 0 |
| **A khai** | 0 / 3 | 2 / 2 |

Với A: B im lặng thì khai được 0 so với im lặng 1; B khai thì khai chịu 2 so với im lặng chịu 3. **Khai là chiến lược áp đảo**, B suy luận đối xứng, kết cục (2, 2) dù (1, 1) tốt hơn cho cả hai.

**Cân bằng Nash** là trạng thái không ai đơn phương đổi chiến lược để có lợi hơn — muốn lợi thêm thì phải làm người khác thiệt. Cốt lõi: **tối ưu Nash không đồng nghĩa tối ưu tập thể.** Hai hàm ý: **cùng một phòng, cùng giữ một mã, khoe lời với nhau — bản chất là đang lấy tiền của nhau**, nên đầu tư là việc riêng tư; và **trong nhóm đẩy giá, ai cũng cân nhắc bán trước và ai cũng nghi ngờ người còn lại**, không cam kết nào giữ được nhóm ở lại tới giá mục tiêu. Các dạng cùng cấu trúc, khác bối cảnh:

| Tình huống | Ẩn số | Mâu thuẫn |
|---|---|---|
| Đấu giá | Đối thủ ra giá bao nhiêu, dừng ở đâu | Trả cao thì mất lời, trả thấp thì mất hàng |
| Thương lượng lương | Mức phù hợp — phụ thuộc năng lực, khả năng chi trả, mức cạnh tranh ngành | Đòi ít thì thiệt, đòi cao thì mất việc |
| Ra sản phẩm mới; tự sản xuất hay đi thuê | Mức ăn mòn dòng cũ; nhu cầu tương lai | Doanh thu mới nhưng giảm giá trị dòng cũ; xây nhà máy so với đi thuê |
| Trả lương theo giờ hay theo sản phẩm | Không quan sát được nỗ lực thật | Theo giờ thì ổn định nhưng không kích thích; theo sản phẩm thì ngược lại |
| Trò chơi con gà (chicken game) | Đối thủ có nhượng bộ không | Hợp tác thì chia bánh lớn hơn; không hợp tác thì thắng đối thủ nhưng bánh nhỏ hơn |

Với chicken game, người ta hợp tác khi miếng bánh còn nhỏ, nhưng khi bánh lớn thì phần lớn hành động vì lợi ích riêng. **Trò chơi vẫn có thể chơi sáng tạo để cả hai cùng được:** ngành xe hơi Mỹ thập niên 1980 đang cạnh tranh bằng giảm giá, cả hai cùng mất biên lợi nhuận; một hãng phát hành thẻ tín dụng cho tích điểm từ chi tiêu, điểm chỉ dùng được để mua hoặc thuê xe của chính hãng đó. Khách bị khoá vào hãng bằng phần thưởng tích luỹ chứ không bằng giá, đối thủ nhờ đó cũng không phải giảm giá nữa. **Điều kiện thắng đổi thì cân bằng đổi.**

## Ví dụ: ma trận lợi ích trò chơi giữ tin – lộ tin

**Bối cảnh.** Hai bên A và B cùng biết một thông tin chưa công bố về doanh nghiệp giả định X và đang gom cổ phiếu X. Mỗi bên chọn **giữ tin** (im tới khi gom đủ) hoặc **lộ tin** (loan ra sớm để được ghi nhận là người biết trước).

**Quy ước điểm.** Chỉ số lợi nhuận kỳ vọng, 10 là cao nhất trong bài toán. Cơ chế đứng sau con số: tin loan sớm thì người ngoài mua đuổi, giá chạy trước khi bên biết tin gom đủ, giá vốn bình quân bị đẩy lên và quy mô vị thế bị thu nhỏ.

| A \ B | B giữ tin | B lộ tin |
|---|---|---|
| **A giữ tin** | **10 / 10** | 6 / 4 |
| **A lộ tin** | 4 / 6 | 2 / 2 |

**Bước 1 — phản ứng tốt nhất của A.** B giữ tin: A giữ được 10, A lộ được 4 → giữ. B lộ tin: A giữ được 6, A lộ được 2 → giữ. **Bước 2 — chiến lược áp đảo.** Giữ tin tốt hơn lộ tin ở *mọi* nước đi của đối phương; ma trận đối xứng nên B cũng vậy.

**Bước 3 — cân bằng Nash.** Ô (giữ, giữ) = (10, 10). Kiểm tra: A đơn phương chuyển sang lộ tin thì rơi từ 10 xuống 4 — không có lợi; B tương tự. Đây là cân bằng Nash duy nhất. **Bước 4 — so với tối ưu tập thể.** Tổng ở (10, 10) là 20, cao nhất bảng. **Khác tình huống tù nhân, cân bằng Nash ở đây trùng tối ưu tập thể của phía biết tin** — không có mâu thuẫn nội bộ nào đẩy tin ra ngoài.

**Bước 5 — hàm ý cho người ở phía thiếu thông tin:**

- **Tin rò rỉ không phải do trò chơi thất bại.** Cấu trúc lợi ích không sinh ra rò rỉ. Tin đến tay người ngoài là quyết định phát tin có chủ đích, không phải sơ suất.
- **Suy ra thời điểm và vai của người đưa tin.** Tin chỉ được phát khi giữ tin hết giá trị — tức khi gom đã xong; từ đó mục tiêu chuyển từ *mua rẻ* sang *bán được*, mà bán được thì cần người mua. Người loan tin sớm nhất kèm giá mục tiêu không phải người vô tình biết trước — theo cấu trúc trên, họ thuộc nhóm phát tin.
- **Suy ra thứ tự kiểm tra.** Nhận tin thì đọc vùng giá trước, đọc nội dung sau. Giá chưa chạy và ít người biết — còn cơ hội. Giá đã chạy và tin ở khắp nơi — người đến muộn là thanh khoản cho người đến sớm.
- **Không bao giờ là người đầu tiên có tin.** Không phải lời khuyên khiêm tốn mà là kết luận từ ma trận: ô (10, 10) đã được chọn xong trước khi tin tới.

## Trò chơi ra hàng và bốn giai đoạn đẩy giá

Trò chơi thứ hai, ở pha phân phối, giữa những người cùng cầm hàng:

| A \ B | B bán muộn | B bán sớm |
|---|---|---|
| **A bán muộn** | 8 / 8 | 2 / 10 |
| **A bán sớm** | 10 / 2 | **5 / 5** |

Bán sớm áp đảo (10 > 8 và 5 > 2). Cân bằng Nash là (5, 5), **thấp hơn ô (8, 8)** — đúng cấu trúc tình huống tù nhân. Và ô (8, 8) chỉ đạt được nếu có dòng người mua mới đủ lớn ở vùng giá mục tiêu: **nếu tất cả cùng giữ tới giá mục tiêu thì bán cho ai.** Ba hệ quả:

- **Đừng bao giờ tin giá mục tiêu.** Đó là mức người ta muốn *người khác* hướng tới, một cái neo, không phải mức người ta định giữ tới.
- **Luôn có điểm dừng trên đường đi.** Vì phần lớn bán sớm ở đợt đầu, một pha đẩy giá thường chia thành **hai lần điều chỉnh, tức ba đoạn**; bên chủ động biết quy luật này và chủ động tạo điều chỉnh để giữ nhịp.
- **Bên chủ động quan sát chính dòng tiền nhỏ lẻ.** Người mua mới vào càng đông thì càng dám để giá tiến xa; vào yếu thì bán luôn.

| Giai đoạn | Giá và khối lượng | Thông tin |
|---|---|---|
| **1. Gom** | Biên độ hẹp, khối lượng thấp và đều; kéo dài 1–3 tháng | Rất ít hoặc chỉ có tin xấu; tin được chuẩn bị nhưng không tiết lộ, kể cả trong nhóm |
| **2. Đẩy giá** | Giá lên dần, khối lượng tăng; thường có một phiên mua chủ động đột biến báo "gom xong" | Tin tích cực tràn ra kèm giá mục tiêu; mức quan tâm của xã hội tăng dần |
| **3. Xả hàng** | Khối lượng lớn nhất trùng vùng giá cao nhất | Tin thưa dần khi sắp xả xong; mức quan tâm đạt đỉnh rồi giảm |
| **4. Giá rơi, mở vòng mới** | Giá rơi | Tin xấu được đưa ra, kể cả tin cổ đông nội bộ bán |

**Nguyên tắc nghịch đảo ở giai đoạn 4:** giá đang rơi mà tin xấu tràn ngập là dấu hiệu vòng mới sắp khởi động. **Biên độ tham chiếu:** một trò chơi chuẩn bị kỹ thường đẩy tối thiểu 50% tính từ vùng gom, không tính từ đáy tuyệt đối; tiền dồi dào thì đủ ba đoạn (hai lần điều chỉnh), tiền ít thì rút còn hai đoạn hoặc một. **Bẫy phân phối trên đường về:** sau khi đẩy rất xa, thả giá rơi tự do vài phiên về khoảng nửa đường để tạo cảm giác "đã chiết khấu sâu", rồi ra hàng ở chính nhịp bắt đáy đó — phần lớn xảy ra ở cuối chu kỳ tăng.

## Thông tin bất cân xứng và ba hệ quả

Lý thuyết đoạt Nobel Kinh tế 2001 (Akerlof, Spence, Stiglitz). Phát biểu: **hai bên của một giao dịch không có cùng lượng thông tin** — đúng với mọi giao dịch và mọi quan hệ. **Ví dụ xe hơi cũ (Lemon Problem):** người bán biết chất lượng, người mua chỉ nhìn bề ngoài nên chỉ trả giá trung bình ước lượng; người bán xe tốt thấy giá đó thấp hơn giá trị thực nên rời thị trường, chỉ còn xe dưới trung bình; người mua nhận ra và cũng rời đi — **thất bại thị trường vì thiếu thông tin**. Hoặc giao dịch vẫn xảy ra nhưng kèm chi phí kiểm định lớn: không có bữa trưa miễn phí, nhận tin là đang chuẩn bị trả phí sàng lọc.

| Hệ quả | Ai | Cơ chế | Trong chứng khoán |
|---|---|---|---|
| **Lựa chọn ngược** (adverse selection) | Akerlof | Bên tốt rời thị trường, bên xấu ở lại | Chọn nhầm doanh nghiệp; ngân hàng cho vay sai người |
| **Phát tín hiệu** (signaling) | Spence | Bên có lợi thế thông tin chủ động chứng minh mình tốt | Kết quả kinh doanh, hiệu quả sử dụng vốn, cổ tức, cách huy động vốn |
| **Sàng lọc** (screening) | Stiglitz | Bên thiếu thông tin chủ động tách tín hiệu khỏi nhiễu | Phân tích, kiểm chứng chéo, dựa vào nguồn có uy tín |

- **Hệ quả ngược đời quan trọng nhất: bên chất lượng kém có động cơ quảng bá mạnh hơn bên chất lượng tốt.** Lợi nhuận kỳ vọng của bên kém nằm ở việc được tin nên họ sẵn sàng bịa nhiều hơn; bên an toàn có lợi nhuận thấp hơn nhưng chắc chắn hơn, quảng bá thêm chỉ làm giảm kỳ vọng. Suy ra: càng được quảng bá dồn dập, đặc biệt qua kênh không chính thống, càng phải nghi ngờ.
- **Rủi ro đạo đức (moral hazard)** là lớp thứ hai, xảy ra *sau* giao dịch: hồ sơ ban đầu ổn nhưng sau khi nhận tiền thì làm khác cam kết — vay làm dự án dài hạn rồi đem lướt sóng tài sản.
- **Trung gian không giải quyết được vấn đề, chỉ dịch chuyển nó.** Bản chất của trung gian không phải thông tin mà là *chất lượng* thông tin: phải xử lý và kiểm định, đưa tin thô thì vô ích. Bản thân trung gian phân tích và tư vấn gặp đúng vấn đề thông tin như mình. Kết luận vận hành: **tin người, nhưng thiếu tin tưởng, và tự ra quyết định.**

## Quy trình chính sách

| Bước | Dấu hiệu nhận biết | Phản ứng thị trường |
|---|---|---|
| **Dọn đường** | Chuyên gia và báo chí bình luận theo một mô típ; báo chí luôn nghiêng về một phía vì có biên tập kiểm soát | Yếu. Chủ yếu giúp thị trường ngừng giảm |
| **Thông báo** | Công bố chính thức | **Mạnh nhất** |
| **Thực hiện** | Chính sách đi vào vận hành | Bão hoà dần |

- **Độ giãn giữa ba bước quyết định hình dạng phản ứng.** Với công cụ tác động ngay tới kênh liên ngân hàng (thị trường 2), ba bước gần như trùng nhau nên phản ứng tức thì. Với tín dụng hoặc đầu tư công — kênh tín dụng vào kinh tế thực (thị trường 1) và chính sách tài khoá — ba bước giãn rất xa: kỳ vọng duy trì lâu trong khi dòng tiền thật chưa chạy — kỳ vọng chưa thành hiện thực vẫn làm thị trường khó giảm, nhưng không tạo cú đẩy.
- **Quy luật bão hoà của chính sách tiền tệ.** Trong chuỗi giảm lãi suất, lần đầu phản ứng mạnh nhất, tới khoảng lần thứ tư thì yếu hẳn; từ điểm bão hoà, thị trường vận động theo kết quả kinh doanh chứ không theo chính sách nữa. Mục tiêu của chính phủ luôn là ổn định và họ thử sai, nên đừng suy diễn quá xa — chuỗi "tín dụng chạy → lạm phát tăng → nâng lãi suất trở lại" đúng logic nhưng số liệu vĩ mô công bố theo tháng và quý.
- **Quy tắc lan toả.** Tiền vào thật thì tất cả nhóm ngành đều phản ứng, khớp lý thuyết Dow. Tiền vào thì phản ứng nhanh và dễ thấy, **tiền ra thì ra từ từ, khó cảm nhận**. Toàn thị trường đồng loạt tăng nghĩa là có tin tốt mình chưa biết; đồng loạt giảm nghĩa là có sự kiện đặc biệt.

## Tín hiệu doanh nghiệp và event study

Cơ chế đứng sau việc phân biệt tốt thật với tốt giả là **thứ tự ưu tiên về vốn (pecking order)**: khi cần vốn, doanh nghiệp tốt lấy theo thứ tự **lợi nhuận giữ lại → vay nợ → cuối cùng mới phát hành cổ phiếu**. Lý do: lợi nhuận giữ lại không tốn chi phí phát hành và không phát tín hiệu gì; vay nợ làm tăng giá trị cho cổ đông khi suất sinh lời cao hơn lãi vay; phát hành cổ phiếu pha loãng và chỉ hợp lý khi ban lãnh đạo cho rằng cổ phiếu đang được định giá cao hơn giá trị thật. Thứ tự đọc tín hiệu:

- **Tăng vốn bằng vốn vay** — tín hiệu tự tin thật: chấp nhận nghĩa vụ trả lãi cố định vì tin suất sinh lời cao hơn lãi vay. **Phát hành cho cổ đông hiện hữu** — bất thường, vì doanh nghiệp tốt đã dùng lợi nhuận giữ lại trước. **Phát hành cho cổ đông mới** — bất thường hơn, đi kèm thường là kết quả kinh doanh **đột biến đúng lúc cần** thay vì ổn định qua các kỳ, bỏ cổ tức nhiều năm rồi bất ngờ thông báo chia, tiền mặt nhiều mà không triển khai gì.
- **Nghịch lý phải nói thẳng: cơ hội giao dịch ngắn hạn nằm ở nhóm tốt giả, không nằm ở nhóm tốt thật** — vì nhóm tốt giả mới cần sự kiện và mới có sóng. Chơi được, nhưng không đổi giữa chừng thành nắm giữ dài hạn.

**Event study** đo phản ứng giá quanh một sự kiện: cửa sổ trước, ngày sự kiện, cửa sổ sau. Cửa sổ thường dùng cho phản ứng ngắn hạn là **7–10 ngày mỗi phía**, tính cả hai phía thì 2 tuần tới 3–4 tuần, hiếm khi quá 1 tháng. Cơ chế: tin tốt nâng mặt bằng giá lên mức mới, từ đó có hai kịch bản lệch — **phản ứng thái quá** (vọt quá xa rồi phải chỉnh về) hoặc **phản ứng chậm** (đi lên dần).

| Tình huống | Diễn giải | Hành động |
|---|---|---|
| Tin tốt, giá **chưa** tăng trước đó, ngày tin ra gần như không nhúc nhích | Phản ứng chậm | Kỳ vọng giá tăng dần |
| Tin tốt, giá **đã** tăng trước đó, khối lượng lớn khi tin ra | Tin ra để bán | Không mua |
| Tin tốt, ngày tin ra giá vọt rất mạnh | Phản ứng thái quá | Chờ chỉnh về mặt bằng mới |
| Tin xấu, giá đã giảm rồi còn giảm mạnh thêm | Đoạn giảm thêm là thái quá | Không bán tiếp |
| Tin xấu, giá gần như không phản ứng | Chưa hạ về mặt bằng mới | Cơ hội bán |

Hai điểm neo: **mua khi giá đã phản ánh xong tin là đu đỉnh**; và **sau tin xấu, dù có hồi thì giá cũng khó về mức trước tin** vì kỳ vọng đã đổi.

## Áp dụng: thị trường tín dụng

Thị trường tín dụng không tuân quy luật cung cầu hàng hoá thông thường vì người bán không quan sát được chất lượng người mua. Hai chiều phân loại — người vay *có khả năng* (kiến thức, kinh nghiệm, trình độ) hay *không*; cơ hội *an toàn* (sinh lời tốt nhất ở một mức rủi ro cho trước, hoặc rủi ro thấp nhất ở một mức lợi nhuận kỳ vọng cho trước) hay *rủi ro* (lợi nhuận có thể cao nhưng xác suất thấp nên kỳ vọng thấp):

| | Cơ hội an toàn | Cơ hội rủi ro |
|---|---|---|
| **Người có khả năng** | Tốt nhất cho nền kinh tế | Chấp nhận được |
| **Người không có khả năng** | Trung bình | Tệ nhất |

Ngân hàng đối mặt **lựa chọn ngược** (không biết người vay thuộc ô nào) và **rủi ro đạo đức** (dùng tiền sai mục đích sau giải ngân). Cả hai đẩy chi phí lên — phải sàng lọc trước và theo dõi sau — nên nền kinh tế càng rủi ro thì chi phí ngân hàng càng cao, không chỉ vì lãi suất.

- **Lãi suất cao.** Người ta chỉ vay khi lợi nhuận kỳ vọng lớn hơn lãi suất; lãi suất tăng thì ngưỡng lợi nhuận tối thiểu tăng, kéo theo mức rủi ro tối thiểu của dự án tăng. Người có cơ hội an toàn rời thị trường, chỉ còn người theo cơ hội rủi ro. Ngân hàng thấy rủi ro mất vốn tăng nhanh hơn phần bù lãi suất nên **chủ động hạn chế tín dụng — không phải vì thiếu tiền mà vì sợ mất vốn**.
- **Lãi suất thấp.** Vay rẻ kích thích cả người không có khả năng tham gia, đồng thời cơ hội đầu cơ tài sản được vẽ ra nhiều hơn. Ngân hàng không phân biệt được ai là ai nên lại tự hạn chế — lần này vì lo tiền chảy vào đầu cơ.
- **Điểm chuyển dịch.** Tín dụng chỉ thực sự chạy khi lãi suất giảm đủ để chi phí vốn bình quân của ngân hàng hạ tương ứng, và người *có khả năng với cơ hội an toàn* thấy lãi suất đủ hấp dẫn để quay lại vay. Trong pha tự hạn chế, luôn có tiếng kêu từ cả hai phía — người có khả năng kêu không vay được, người không có khả năng lại vay được — nhưng tổng tín dụng ra nền kinh tế vẫn thấp.

## Thị trường hiệu quả và tài chính hành vi

Lý thuyết của Eugene Fama: **giá tài sản phản ánh thông tin hiện có; khi có thông tin mới, giá phản ứng ngay theo đúng hướng và đúng quy mô**, dựa trên lý trí người tham gia. Giả định: con người hành động lý trí, xử lý được thông tin, kiến thức tương đương nhau ở mức trung bình. **"Lý trí" không có nghĩa là chọn cái an toàn** — nghĩa đúng là chọn lợi nhuận cao hơn ở cùng mức rủi ro, và rủi ro thấp hơn ở cùng mức lợi nhuận kỳ vọng. **Hệ quả:** không ai kiếm được **lợi nhuận vượt trội** từ thông tin đã công bố; vượt trội là phần cao hơn mức chung của thị trường — thị trường tăng 1% mà cổ phiếu tăng 3% thì vượt trội là 2%. Nguyên lý gọn: **tin đã ra rồi là hết cơ hội.**

| Dạng | Tập thông tin đã phản ánh | Nếu đúng thì cái gì vô dụng |
|---|---|---|
| **Yếu** | Thông tin quá khứ | Phân tích kỹ thuật, phân tích chuỗi giá quá khứ |
| **Vừa** | Quá khứ + thông tin đã và đang công bố | Thêm: phân tích cơ bản trên dữ liệu công khai |
| **Mạnh** | Toàn bộ, kể cả thông tin nội gián | Thêm: cả lợi thế nội gián |

Nếu tin lý thuyết này thì phân tích đồ thị, vĩ mô, cơ bản đều vô nghĩa và cách hợp lý duy nhất là đầu tư thụ động vào quỹ chỉ số. Ba lý do khiến tài chính hành vi ra đời cuối thập niên 1980:

1. **Chứng minh thị trường hiệu quả rất khó** — mỗi bằng chứng chỉ là một mảnh. Kiểm định kéo dài tới hàng trăm năm dữ liệu, trong khi nhà đầu tư thực tế chỉ tham gia vài năm, thậm chí vài tháng.
2. **Bằng chứng thực nghiệm mâu thuẫn** — đường trung bình động, chỉ báo động lượng, và các nhóm vốn hoá thấp / thị giá thấp / P/E thấp / P/B thấp đều cho lợi nhuận vượt trội. Ở thị trường phát triển, dạng yếu và vừa khá đúng nhưng **nội gián vẫn tạo lợi nhuận vượt trội** — chính vì vậy pháp luật cấm. Chính Fama thừa nhận thị trường hiệu quả chỉ đúng dài hạn, và dài hạn là bao lâu thì không ai biết.
3. **Con người hành động theo cảm xúc, không theo lý trí** — lúc vui khác, lúc buồn khác, một mình khác, trong đám đông khác.

**Hai giả định nền tảng đối lập nhau.** Fama lấy *lý trí* làm gốc; tài chính hành vi lấy *sự bối rối* làm gốc: con người thường xuyên bị cảm xúc chi phối và **kể cả khi biết cái gì tốt nhất thì vẫn không làm theo**. Cảm xúc bị chi phối bởi **thành kiến** (nghe người khác nói xấu thì hình thành đánh giá không có cơ sở) và **trải nghiệm cá nhân**. Thị trường hiệu quả còn giả định mọi người chơi có thông tin và suy nghĩ giống nhau — trực tiếp đối lập với thông tin bất cân xứng. **Phương pháp luận cũng khác:** thị trường hiệu quả dựa trên *empirical* (dữ liệu quá khứ để chứng minh), tài chính hành vi dựa trên *experience* (quan sát cái đang diễn ra), vì mô hình toán trên dữ liệu quá khứ đơn giản hoá quá mức. Đây cũng là lý do chiến lược tăng trưởng và chiến lược giá trị cùng hoạt động tốt — chúng nhìn hai khoảng thời gian khác nhau.

## Thiên lệch có tên và chân dung nhà đầu tư

| Thiên lệch | Phát biểu | Biểu hiện — cũng là chân dung nhà đầu tư điển hình |
|---|---|---|
| **Thuyết triển vọng** (Prospect Theory) | Sợ rủi ro khi đối mặt với lãi, chấp nhận rủi ro khi đối mặt với lỗ | Chốt lời sớm; giữ khoản lỗ lâu; cắt lỗ rồi thì tìm cơ hội rủi ro hơn để gỡ |
| **Ác cảm mất mát** (Loss Aversion) | Nỗi đau khi mất tiền lớn hơn niềm vui khi được tiền cùng đơn vị | Đường giá trị là đường cong: mất thì đau sắc, được thì dửng dưng |
| **Hiệu ứng sở hữu** (Endowment Effect) | Đề cao những gì thuộc về mình | Ai nói về một cổ phiếu thì gần như chắc chắn đang cầm nó, và vì cầm nên nói quá lên; hay quay lại mã từng thắng |
| **Hiệu ứng khung** (Framing) | Cùng thông tin, trình bày khác thì phản ứng khác | "Lợi nhuận quý 3 thấp hơn kỳ vọng" và "cao hơn quý 2" có thể là cùng một con số |
| **Tâm lý hối tiếc** (Regret Aversion) | Tránh hành động dẫn tới hối tiếc | Sai rồi thì bỏ phán đoán riêng, theo đám đông; chọn cổ phiếu nổi tiếng để "mất thì mất cùng mọi người" |
| **Sai lệch neo** (Anchoring) | Hành động theo dấu ấn đã có thay vì theo thông tin mới | Neo vào giá vốn của mình, vào giá mục tiêu được hô. Đưa giá mục tiêu là kỹ thuật tạo neo |
| **Thiên kiến xác nhận** (Confirmation Bias) | Tìm thông tin ủng hộ lập luận của mình, bỏ qua thông tin trái chiều | Chỉ giữ lại thông tin có lợi cho vị thế đang cầm; khi mọi phân tích đều ngợi ca xu thế hiện hữu thì thiên kiến này đang chi phối |
| **Hiệu ứng đám đông** (Herding) | Mặc định đám đông đã nghĩ thay cho mình | Chọn cổ phiếu theo những gì nghe thấy, đọc thấy; hưng phấn khi giá tăng mạnh, hoảng sợ khi giá giảm mạnh |
| **Kế toán tâm lý** (Mental Accounting) | Hành động khác nhau tuỳ nguồn tiền, dù tiền là như nhau | Tiền của mình thì cẩn trọng, tiền quản hộ thì chấp nhận rủi ro cao hơn |
| **Thiên lệch gần đây** (Recency Bias) | Chú ý sự kiện vừa xảy ra, quên sự kiện cũ | Quên bài học cũ rất nhanh; mua lại một mã vừa hồi như thể chưa từng có cú giảm |
| **Thiên lệch bảo thủ** (Conservatism) | Bám thông tin đã có, coi nhẹ thông tin mới | Đã nêu luận điểm đầu tư thì bỏ qua báo cáo trái chiều; người có tiếng nói công khai bảo thủ hơn vì đã hô là phải bảo vệ |
| **Nhận thức muộn** (Hindsight Bias) | Tin rằng mình đã dự báo đúng, sau khi sự kiện đã xảy ra | Giá lên thì tin mình có tài dự báo; nêu 5–6 lần đúng trong 100 lần và bỏ qua 90 lần sai |

- **Thuyết triển vọng giải thích vì sao hai chiều thị trường không đối xứng.** Xu thế giảm hồi chậm vì người lỗ liên tục bình quân giá xuống; xu thế tăng luôn phải qua ít nhất một lần điều chỉnh vì người lãi chốt sớm. Suy ra: **xu thế tăng thì mua nhanh bán chậm, xu thế giảm thì mua chậm bán nhanh.** Và **nhận thức muộn là lý do không nên tin vào năng lực dự báo của bất kỳ ai**, kể cả của chính mình — hệ quả chung: **ở mỗi thời điểm phải coi các cổ phiếu là như nhau**, bất kể mã đó từng có lịch sử đẩy giá hay từng được nói nhiều.
- **Quy mô vốn quyết định cách ra quyết định**, nên không thể áp khung của bên này sang bên kia. Vốn lớn phải mua dàn trải nên tâm lý phân tán, coi đỉnh và đáy là **vùng**, gom trong thời gian dài, mua cả khi giá còn giảm và bán khi giá lên. Vốn nhỏ chọn tập trung được, coi đỉnh đáy là **điểm**, đi tiền nhanh, xử lý được trong một phiên. Áp khung quản lý một quỹ lớn vào tài khoản nhỏ thì không bao giờ hiểu được tài khoản đó nên đi tiền như thế nào — và ngược lại.

## Đầu tư giá trị nằm ở sự vô lý

Quan điểm ngược dòng, cần giữ nguyên dạng. Cách hiểu phổ biến trong sách: đầu tư giá trị là tìm cổ phiếu chưa ai biết tới rồi chờ giá lên. **Cách hiểu ở đây khác: đầu tư giá trị là nhận diện cảm xúc sai của đám đông — tham lam hoặc sợ hãi — rồi hướng tới thực tế đúng.** Nếu giá đang chạy trên thông tin sai và hành động dựa trên cảm xúc thì cuối cùng nó phải quay về thực tế đúng; chỗ chênh lệch đó là cơ hội. Lập luận nền: **sự hợp lý của thị trường không mang lại cơ hội.** Nếu giá phản ứng đúng mức thì không còn gì để khai thác; đợi tới khi mọi thứ hợp lý — kinh tế đã tốt, doanh nghiệp đã có lãi rõ ràng — thì cơ hội đã qua. Câu của John Maynard Keynes rơi đúng chỗ này: đợi cho tới khi con người hành động hợp lý thì đã phá sản.

- **Cái gì vô lý thì đừng dài hạn với nó** — vô lý không tồn tại lâu, chơi trò vô lý thì chơi theo sự kiện và ra trước khi sự kiện kết thúc. Ngược lại, **không lướt sóng cổ phiếu hợp lý**: cổ phiếu tốt thật thì ổn định, không có sóng để lướt.
- **Quyết định khung thời gian trước, chọn cổ phiếu sau** — tuyệt đối không làm ngược. Lý do gọn: **chơi tốt một trò chơi sai không bằng chơi sai một trò chơi đúng.** Trò chơi sai là sai cổ phiếu, sai dòng tiền — vào đúng đáy giá nhưng không phải đáy thị trường. Trò chơi đúng thì vào sớm hay muộn cơ hội vẫn còn.
- **Lần điều chỉnh đầu tiên trong xu thế tăng thì đừng lo** — nó do người chốt lời sớm tạo ra. Điều chỉnh để còn đi tiếp thì **không vượt quá 50% phần đã tăng**, phải giữ được cảm giác đáy sau cao hơn đáy trước; chỉnh về sát vùng giá cũ thì trò chơi coi như kết thúc. Biên độ chính xác bao nhiêu phần trăm không quan trọng bằng việc **có** điều chỉnh.
- **Đã tăng mà khối lượng chưa đột biến thì đừng vội bán**; đã tăng tốt rồi mà đột nhiên tăng mạnh kèm khối lượng vọt lên thì đừng mua; đang giảm mà xuất hiện một phiên giảm mạnh đột ngột thì đừng bán nữa.
- **Sau khi thị trường tăng và bắt đầu điều chỉnh, nếu dòng tiền dẫn dắt có tiếng bất ngờ được mua vào** thì đó là dấu hiệu nhà đầu tư đang bối rối (ác cảm mất mát cộng tâm lý hối tiếc), không phải cơ hội ở bậc đó — tiền vẫn còn trong thị trường, cơ hội tiếp theo nằm ở bậc rủi ro hơn.
- **Nguyên tắc phải được tạo ra bởi thực hành, không phải bởi lý thuyết.** Ghi nguyên tắc ra giấy không giải quyết được vấn đề cảm xúc. Và dù có cảnh giác thì vẫn bị ảnh hưởng bởi dấu ấn tâm lý về một cổ phiếu mình đang theo dõi — đó là bản chất của tài chính hành vi, chỉ giảm bớt được bằng lặp lại.

---
