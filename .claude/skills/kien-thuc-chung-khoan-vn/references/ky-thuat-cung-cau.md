# Kỹ thuật: cung cầu, hỗ trợ kháng cự và đồ thị nến

File này trả lời ba câu: đọc quan hệ giá – khối lượng thế nào, xác định hỗ trợ kháng cự và xu hướng ra sao, đọc một cây nến thế nào. Đây là lớp công cụ cho bước cuối của chuỗi top-down — chọn thời điểm vào ra, không phải chọn cổ phiếu.

## Mục lục

- [Giả định và phạm vi áp dụng](#gia-dinh-va-pham-vi)
- [Cung cầu và bốn kịch bản giá – lượng](#bon-kich-ban)
- [Ai quyết định khối lượng](#ai-quyet-dinh-khoi-luong)
- [Ba giai đoạn tăng giá và ba lần chỉnh](#ba-giai-doan)
- [Ví dụ chạy được: đọc một chuỗi giá – lượng](#vi-du-chay-duoc)
- [Hỗ trợ, kháng cự, đường xu hướng](#ho-tro-khang-cu)
- [Phá vỡ và đảo vai](#pha-vo-va-dao-vai)
- [Khoảng trống giá](#khoang-trong-gia)
- [Đọc một cây nến](#doc-mot-cay-nen)
- [Ghép nến](#ghep-nen)
- [Nến là điểm uốn — quy trình bắt đáy bắt đỉnh](#nen-la-diem-uon)
- [Nối đồ thị với chính sách tiền tệ](#noi-voi-chinh-sach)

---

## Giả định và phạm vi áp dụng

**Giả định nền:** mọi thông tin về doanh nghiệp và cổ phiếu đều đã hiện ra trong **giá** và **khối lượng**. Gần như mọi chỉ báo đều dựng từ hai biến này. Việc cần làm không phải nhớ nhiều chỉ báo mà là chuyển dữ liệu thành thông tin.

- **Kỹ thuật mạnh nhất ở khung thời gian ngắn** — lúc đó cơ bản chưa kịp đổi, tâm lý chưa kịp đổi, nên giá phản ánh chủ yếu tâm lý, đúng thứ kỹ thuật đo được. Giữ qua đêm là bài toán khác giao dịch trong ngày: qua một đêm, hưng phấn và sợ hãi đã sang trạng thái khác.
- **Kỹ thuật nói được "cơ bản đang tốt hơn hay xấu hơn", không nói được tốt xấu ở khía cạnh gì.** Chiều ngược lại không tồn tại — không suy được từ đồ thị ra doanh nghiệp đang đổi cái gì. **Kháng cự hoặc hỗ trợ quan trọng bị phá là dấu hiệu kỳ vọng về cơ bản đã đổi**, không phải cơ bản đã đổi: người ta đã biết cái xấu và thôi sợ nó, nên động lực hành động khác đi.
- **Không dùng đơn lẻ.** Một tín hiệu đứng một mình không đủ kết luận; mọi mảnh phải dùng cùng nhau. **Nến có thể bị làm giả** ở cổ phiếu thanh khoản thấp — khớp vài trăm cổ phiếu giá trần đầu phiên là đã có cây nến xanh dài. Luôn soi khối lượng tại điểm quan trọng; lượng quá nhỏ thì nến chỉ là nhiễu.

## Cung cầu và bốn kịch bản giá – lượng

Đường cầu dốc xuống, đường cung dốc lên. Khi một đường **dịch chuyển** (không phải trượt dọc đường cũ), điểm cân bằng mới cho ra một cặp giá – lượng mới. Đọc giá lượng là đọc ngược từ cặp quan sát được ra hướng dịch chuyển.

- **Chỉ quan sát được khối lượng khớp, không quan sát được cung hay cầu.** Không thể quy lượng tăng về một bên. "Lượng tăng nghĩa là cầu tăng" là hiểu lầm phổ biến nhất và là chỗ đội lái khai thác — hô "tiền vào mạnh" để dụ người mua. **Suy luận chắc chắn duy nhất từ giá: giá tăng thì cầu đang lớn hơn cung.** Mọi kết luận còn lại phải đọc kèm lượng.

| Giá | Lượng | Dịch chuyển đằng sau | Kết luận |
|---|---|---|---|
| Tăng | Tăng bình thường | Cầu dịch phải | Cầu tăng đơn thuần. Bình thường, tiếp diễn được |
| Tăng | Tăng rất ít hoặc không tăng | Cầu dịch phải **và** cung dịch trái | **Tiết cung** — người bán không chịu bán. Tốt nhất, hay gặp ở cổ phiếu khó mua |
| Giảm | Tăng | Cung dịch phải | Bên bán thắng thế. Quan sát thêm |
| Giảm mạnh | Không tăng | Cung dịch phải **và** cầu dịch trái | Xấu nhất: bán mạnh mà không ai đón |
| *Giảm ít / ngừng giảm* | *Tăng* | *Cung tăng, cầu cũng tăng* | *Biến thể, chỉ có nghĩa sau đoạn giảm dài: bên mua bắt đầu vào. Phải chờ **giá uốn lên** mới xác nhận* |

- **"Đột biến" không có nghĩa là to, mà là khác bình thường của chính mã đó.** Cách đo: lấy trung bình khối lượng 5 phiên (hoặc trung bình 1 tuần) làm mốc, cột lượng vượt rõ khỏi mốc là đột biến. Mỗi mã có nhóm nhà đầu tư và kiểu giao dịch riêng nên chỉ so với lịch sử của chính nó.
- **Lượng đi trước giá** — nhưng có trường hợp lượng đi sau giá, và quan trọng hơn: **lượng là cảnh báo, không phải lệnh hành động.** Gặp đột biến thì quan sát 1–2 phiên (T+2, trước đây T+3) kèm tín hiệu khác rồi mới quyết.
- **Mức cảnh báo của một cây lượng đột biến trong xu thế tăng tăng dần theo bối cảnh trước đó:** lượng tăng đều rồi bất chợt một phiên lớn (thấp nhất) → lượng cố định kéo dài rồi vọt gấp nhiều lần (trung bình) → **đoạn tiết cung kéo dài rồi mới đột biến (cao nhất, gần như chắc chắn là bán ra)**. Còn phụ thuộc giá đã tăng bao lâu: tăng càng dài thì cùng tín hiệu càng nặng.

## Ai quyết định khối lượng

- **Trong xu thế tăng, bên bán quyết định khối lượng.** Giá tăng vì nhiều người muốn mua, nhưng có giao dịch thì phải có người chịu bán. Câu hỏi đúng lúc giá tăng là *"tiền có ra không"*. Nếu ai cũng tin giá còn tăng thì người bán giữ hàng và lượng phải thấp — lượng tăng nghĩa là người bán đã bắt đầu chịu bán.
- **Trong xu thế giảm, bên mua quyết định khối lượng.** Giá giảm vì cung nhiều, lượng khớp được bao nhiêu là do bên mua chịu đỡ bấy nhiêu. Câu hỏi đúng là *"tiền có vào không"*. Giá giảm mà lượng cạn nghĩa là người mua đứng ngoài hoàn toàn.
- **Hệ quả:** cùng một cây nến tăng kèm lượng lớn mang hai nghĩa ngược nhau tuỳ xu thế đang chạy — trong xu thế tăng là cung ra (cảnh báo), trong xu thế giảm là cầu vào (tích cực). Không xác định xu thế trước thì không đọc được lượng.

## Ba giai đoạn tăng giá và ba lần chỉnh

Một đợt tăng giá điển hình đi qua ba giai đoạn. Đây cũng là bộ khung đọc tích luỹ – phân phối.

| Giai đoạn | Giá | Lượng | Lý do duy nhất | Ứng xử |
|---|---|---|---|---|
| **A — cầu tăng** | Tăng | Tăng bình thường | Cầu vào | Bình thường và tốt. Để chạy |
| **B — tiết cung** | Vẫn tăng | Giảm | Cung rút đi | Rất tốt, tiếp diễn được. Nhưng chuẩn bị tâm lý: sau tiết cung thường là một nhịp tăng tốc rồi mới đến bán ra |
| **C — phân phối** | Đứng hoặc giảm | Tăng rất mạnh | Cung vượt cầu | Đảo chiều. Đây là bán ra, **đừng đọc thành "tiền vào nhiều"** |

- Chuỗi thực tế: gom xong → kéo giá bình thường → mất thanh khoản vì không ai bán → tăng tốc → xả. **Không phải mã nào cũng đủ ba giai đoạn** — có mã nhảy thẳng A sang C, khi đó cảnh báo xuất hiện đột ngột giữa đoạn tăng đang bình thường. **Sau tiết cung mà thấy lượng lớn thì ra cho chắc**, nhất là với cổ phiếu trước đó khó mua: "ăn ít cho chắc" hơn "ăn thêm vài phần trăm rồi mất hết".
- **Xu thế giảm đặc trưng bởi giá giảm kèm lượng giảm** — cầu không quan tâm. Khi giá ngừng giảm mà lượng lại tăng, đó là lúc cầu bắt đầu quan tâm: đầu vùng tích luỹ.

**Ba lần chỉnh** (nguồn còn gọi là ba lần lưỡng lự trong một đợt tăng) — thang ba mức:

- **Lần 1** — người bị kẹt bán ra vì sợ; tài chính hành vi cho thấy nhóm này ra sớm. Chưa đáng lo.
- **Lần 2** — cảnh báo cao hơn, có thể ra ở đây. Nếu sau lần 2 mà giá **vẫn vượt lên**, tâm lý và kỳ vọng về nền tảng cơ bản đã đổi, "người ta hết sợ" — phải quay lại vĩ mô tìm xem cái gì đã đổi.
- **Lần 3** — lực rơi mạnh hơn hai lần trước. Mức cao nhất, gần như chắc chắn nên ra.
- Chiều ngược lại khi bắt đáy: **đừng bắt đáy ở lần giảm đầu tiên.** Lần 2 xác suất cao hơn, lần 3 cao hơn nữa. **Nguyên tắc ba phần:** không chắc thì chia lệnh ba phần, vào hoặc ra dần. Mức lo còn tuỳ giá đang ở đâu trong dải định giá — chia ba mức thấp quá / bình thường / cao quá. **Khi xu hướng tăng yếu đi: rời dòng tiền đầu cơ trước, giữ dòng tiền dẫn dắt**, không giữ mã thị trường đang hô hào; khi xu hướng giảm yếu đi thì vào ngược lại — dẫn dắt trước, lan toả sau, đầu cơ cuối cùng (thị trường Việt Nam hay làm ngược vì muốn hồi nhanh).

## Ví dụ chạy được: đọc một chuỗi giá – lượng

Cổ phiếu giả định X, đã giảm dài trước đó. Nền khối lượng 5 phiên liền trước phiên 1 đều xấp xỉ 1,0 triệu cp. **KL/TB5** = khối lượng phiên đó chia trung bình khối lượng 5 phiên liền trước.

| Phiên | Đóng cửa | Thay đổi | KL (triệu cp) | TB5 trước đó | KL/TB5 |
|---|---|---|---|---|---|
| 1 | 20,0 | −3,0% | 1,8 | 1,00 | 1,8× |
| 2 | 19,8 | −1,0% | 2,4 | 1,16 | 2,1× |
| 3 | 19,9 | +0,5% | 2,6 | 1,44 | 1,8× |
| 4 | 20,4 | +2,5% | 2,2 | 1,76 | 1,3× |
| 5 | 20,9 | +2,5% | 2,3 | 2,00 | 1,2× |
| 6 | 21,6 | +3,3% | 1,4 | 2,26 | 0,6× |
| 7 | 22,1 | +2,3% | 0,9 | 2,18 | 0,4× |
| 8 | 22,2 | +0,5% | 3,1 | 1,88 | 1,7× |

Kiểm phép tính mốc phiên 8: TB5 = (2,6 + 2,2 + 2,3 + 1,4 + 0,9) / 5 = 9,4 / 5 = 1,88 → 3,1 / 1,88 = 1,65 ≈ **1,7×**. So với hai phiên liền trước chỉ ở mức 0,4–0,6× nền, tỷ lệ nhảy hơn 4 lần: đột biến rõ.

1. **Phiên 1–3 — xu thế đang giảm nên bên mua quyết định khối lượng.** Giá giảm mà lượng lớn: có người đỡ ở vùng thấp. Phiên 3 rơi vào biến thể thứ năm — ngừng giảm, lượng vẫn cao, cung ra nhưng cầu hứng hết. Cầu đã vào, chưa xác nhận.
2. **Phiên 4–5 — giai đoạn A.** Giá uốn lên, lượng tăng bình thường, tỷ lệ so với nền đang co lại. Xác nhận bên mua mạnh hơn. Đoạn phiên 1–3 là **tích luỹ**.
3. **Phiên 6–7 — giai đoạn B, tiết cung.** Giá tăng nhanh hơn mà lượng cạn còn 0,4× nền. Người bán không chịu bán. Trạng thái tốt, nhưng đây là lúc bật cảnh giác chứ không phải lúc mua thêm.
4. **Phiên 8 — giai đoạn C.** Giá đứng (+0,5%) trong khi lượng vọt 1,7× ngay sau đoạn tiết cung. Xu thế lúc này là tăng nên bên bán quyết định khối lượng: cây lượng này là **cung ra**, không phải tiền vào. Đây là cấu hình cảnh báo nặng nhất — đột biến ngay sau tiết cung.

**Kết luận:** chuỗi bắt đầu bằng **tích luỹ** (phiên 1–3), kết thúc bằng dấu hiệu **phân phối** (phiên 8). Ứng xử: hạ tỷ trọng, ưu tiên ra vì đã ăn trọn đoạn A và B; chưa chắc thì chia ba phần và quan sát thêm 1–2 phiên theo T+2. **Kiểm tra chéo bắt buộc:** soi thêm cây nến ngày của phiên 8 (thân dài hay lưỡng lự, vị trí thân) và vị trí giá so với kháng cự gần nhất. Một mình chuỗi giá lượng chưa đủ kết luận.

## Hỗ trợ, kháng cự, đường xu hướng

- **Hỗ trợ** — vùng đáy trước đó; giá về vùng cũ, người ta thấy rẻ nên mua. **Kháng cự** — vùng đỉnh trước đó; người ta thấy đắt nên bán. **Đường xu hướng tăng** nối các đáy quan trọng, đóng vai trò hỗ trợ, cần ít nhất 2 đáy; **đường xu hướng giảm** nối các đỉnh quan trọng, đóng vai trò kháng cự, cần ít nhất 2 đỉnh.
- **Là vùng, không phải đường.** Tâm lý luôn có sai số nên nối điểm chỉ là tương đối. Đừng ép vào một mức giá chính xác, cũng đừng chờ giá chạm đúng mức mới hành động.
- **Chọn đỉnh đáy ở nơi có khối lượng lớn**; vùng đỉnh đáy kèm lượng lớn đáng tin hơn hẳn vùng lượng mỏng. **2 điểm để vẽ, điểm thứ 3 mới khẳng định.** Đã xác định thì giữ nguyên, đừng vẽ lại cho vừa ý mình. **Vùng gần có ý nghĩa trước vùng xa:** giả định giá uốn lên ở vùng gần nhất, vùng đó bị phá thì kỳ vọng về vùng xa hơn.
- **Đường xu hướng yếu hơn hỗ trợ kháng cự ngang**, vì mắt người bám mức giá ngang dễ hơn bám một độ dốc. Hỗ trợ kháng cự ngang phát huy tốt nhất khi thị trường đi ngang; khi xu hướng đã rõ thì vai trò chuyển sang đường xu hướng.
- **Bản chất của cả ba là niềm tin của thị trường vào driver đang chi phối giá.** Giá đổi vì tin tức, tin tức ngẫu nhiên. Đọc hỗ trợ kháng cự và xu hướng thực chất là đo niềm tin vào driver đang mạnh lên hay yếu đi.

| Xu hướng | Điều kiện | Vế nào quan trọng hơn |
|---|---|---|
| **Tăng mạnh** | Đáy sau cao hơn đáy trước **và** đỉnh sau cao hơn đỉnh trước | Đáy sau không phá đường xu hướng tăng |
| **Giảm mạnh** | Đỉnh sau thấp hơn đỉnh trước **và** đáy sau thấp hơn đáy trước | Đỉnh sau không phá đường xu hướng giảm |

Xu hướng tăng **khoẻ hay yếu** đo bằng khoảng chênh giữa đỉnh sau và đỉnh trước: đỉnh sau cao hơn nhưng không đáng kể là xu hướng tăng yếu — hình thức vẫn tăng nhưng đã phải cảnh giác. Nhịp điều chỉnh nhanh một hai ngày thì bỏ qua, coi cả đoạn là một đoạn tăng.

## Phá vỡ và đảo vai

**Kháng cự bị phá trở thành hỗ trợ, và ngược lại.** Một mức bị test nhiều lần chứng tỏ là ngưỡng tâm lý hoặc ngưỡng cơ bản mạnh; khi vượt qua được — nhất là bằng một cây nến mạnh — nỗi sợ không vượt qua được biến mất và mức đó đổi vai.

1. **Xác định kháng cự hỗ trợ cần ít nhất một đỉnh/đáy trước đó; đường xu hướng cần ít nhất 2 đỉnh hoặc 2 đáy.**
2. **Đã phá thì đừng cố nắng.** Lập tức giả định xu hướng mới đã xuất hiện. Giữ kết luận cũ sau khi cấu trúc đã vỡ là điều tối kỵ.
3. **Không dùng một mảnh kiến thức đơn lẻ để kết luận.**

- **Sai lầm điển hình:** hỗ trợ bị phá rồi cố vẽ lại một đường hỗ trợ mới cao hơn. Làm vậy là tự cho phép giá rơi về mức đó, trong khi theo nguyên tắc giá sẽ quay lại test vùng vừa phá rồi mới đi tiếp.
- **Ba trạng thái: tăng, giảm, sideway.** Một trạng thái kết thúc thì nghĩ ngay tới hai trạng thái còn lại và vẽ đường mới. Xu hướng tăng mà đỉnh sau không còn cao hơn đỉnh trước là đã yếu; yếu rồi bị phá thì lập tức chuyển giả định. **Nếu xu hướng đổi thì phải có một thông tin nào đó chi phối** — kỹ thuật không biết tin gì, nhưng đọc được rằng tin cũ đã hết tác dụng. **Dấu hiệu cuối một xu hướng tăng: cả dòng tiền dẫn dắt lẫn dòng tiền đầu cơ đều chạy cùng lúc** — bước cuối của đoạn tăng, đặc trưng của phân phối lớn, và phân phối lớn có thể kéo dài thêm một đoạn chứ không gãy ngay.

## Khoảng trống giá

**Khoảng trống (gap)** là khoảng hở giá giữa hai phiên liên tiếp. Phân loại bằng ba câu hỏi: *có tin gì mới không, tiền có vào không, tâm lý thế nào.* Nếu khối lượng không tăng đủ mạnh thì diễn biến vẫn chỉ ngắn hạn, chưa đủ nhận diện một xu hướng mới.

**Bảng phân loại bốn loại khoảng trống, hai tiêu chí phân biệt, và giới hạn của gap ở thị trường có biên độ trong ngày nằm ở `ky-thuat-chi-bao.md`, mục *Khoảng trống giá, đột phá, ba kiểu mua*** — file này không lặp lại.

## Đọc một cây nến

Một cây nến gồm bốn mức giá của một phiên: mở cửa, đóng cửa, cao nhất, thấp nhất. **Thân nến** là phần từ mở cửa đến đóng cửa; **bóng nến** là phần nhô ra hai đầu, kéo tới giá cao nhất và thấp nhất (còn gọi râu, đầu, đuôi — tên khác nhau, cấu tạo không khác); **biên độ** là toàn bộ biên độ từ giá thấp nhất tới giá cao nhất. **Màu** chỉ nói ai thắng (xanh: đóng cao hơn mở), không nói thắng mạnh cỡ nào. Nhìn một cây nến là hình dung lại cuộc chiến trong phiên: độ dài cây nến phản ánh mức độ nghiêm trọng của trận đánh, bóng nến cho thấy nỗ lực đã bị đẩy lùi.

| Ba yếu tố phải xét cùng nhau | Ý nghĩa |
|---|---|
| **Bóng nến dài** | Biến động **tâm lý** lớn trong phiên — lo sang lạc quan và ngược lại rất nhanh. Thay đổi cơ bản thì ít |
| **Thân nến dài** | Thay đổi **căn bản** — có thể có tin mới trong phiên, người đọc biết hoặc không. Bền hơn một cú biến động tâm lý thuần |
| **Vị trí thân trong biên độ** | Quan trọng **nhất khi thân nhỏ**, vì lúc đó vị trí là thứ duy nhất nói bên nào thắng. Thân đã to thì vị trí kém quan trọng |

**Cách chia để đọc vị trí:** lấy biên độ làm 100%, chia ba — 1/3 trên, 1/3 giữa, 1/3 dưới. Tương đương các mốc Fibonacci 38 – 50 – 62% nhưng dễ nhớ hơn; cần nhanh thì chia đôi cũng đủ. Ba trạng thái thân nến: **rất lớn so với biên độ** (một bên áp đảo, đáng chú ý), **trung bình** (ngày bình thường, không có gì để quan tâm), **gần bằng không** (lưỡng lự).

| Mẫu hình | Cấu trúc | Đọc |
|---|---|---|
| **Doji** | Thân rất ngắn, gần như đóng bằng mở, nhưng biên độ **lớn** | Lưỡng lự. Càng tin cậy khi biên độ càng lớn so với thân |
| **Marubozu** | Thân dài, bóng rất ngắn hoặc không có | Chắc chắn. Thay đổi tâm lý hoặc cơ bản ngay trong phiên, thường tiếp diễn sang phiên sau |
| **Hammer** | Thân ngắn, lớn hơn doji chút — thân ≤ 1/3 biên độ | Bản phổ thông của doji, dùng giống doji |

- **Bẫy hay mắc nhất với doji:** một phiên tăng mạnh hoặc giảm mạnh vẫn có thể cho thân ngắn. Phải xem **biên độ có lớn không**. Thân ngắn mà cây nến cũng ngắn, không bóng, thì bản chất là xu thế chắc chắn và tiếp diễn: đang giảm thì giảm tiếp, đang tăng thì tăng tiếp.
- **Vị trí thân đổi hoàn toàn kết luận** (áp cho cả doji và hammer): thân ở **1/3 giữa** → lưỡng lự đảo chiều ngược xu thế trước, tin cậy trung bình; thân ở **1/3 trên** sau xu thế **giảm** → khả năng đảo chiều tăng rất cao; thân ở **1/3 dưới** sau xu thế **tăng** → khả năng đảo chiều giảm rất cao. Ở vị trí khác vẫn là lưỡng lự, chỉ xác suất thấp hơn. **Quy tắc chốt: giả thiết thứ nhất luôn là lưỡng lự, rồi mới xét màu để chỉnh độ tin cậy** — trong xu thế tăng, hammer đỏ đáng tin hơn hammer xanh; màu không đổi bản chất, chỉ cộng trừ độ tin cậy.
- **Với marubozu, câu hỏi bắt buộc: hôm đó có tin mới không?** Gắn với thay đổi cơ bản thì tạo xu hướng mới rất nhanh và bền; chỉ là tâm lý thì xu hướng ngắn hạn và giá dễ điều chỉnh lại. **Thay đổi cơ bản không nhất thiết là từ xấu sang tốt** — cạn hết tin xấu cũng là thay đổi cơ bản vì không còn gì xấu hơn; hưng phấn hay bi quan thái quá cũng vậy. **Marubozu sau một đoạn lưỡng lự tích luỹ dài**, tức sau khi thị trường thẩm thấu xong thông tin cũ, là cấu hình đổi xu hướng đáng tin nhất.

## Ghép nến

Kỹ thuật thay cho việc học thuộc hàng trăm tên mẫu hình. **Bốn bước:** lấy giá mở cửa của cây đầu tiên → lấy giá đóng cửa của cây cuối cùng → lấy giá cao nhất và thấp nhất của cả cụm → vẽ thành một cây nến duy nhất rồi đọc lại bằng ba yếu tố ở trên, quy về hai tình huống **lưỡng lự** hoặc **chắc chắn**. **Ghép tối đa 3 cây** — ba phiên là vừa đủ một vòng T+ và vừa đủ thể hiện tâm lý. Muốn nhìn dài hơn thì dùng nến tuần, vốn đã là nến ngày ghép sẵn.

| Mẫu hình | Cấu trúc | Ghép lại ra gì | Kết luận |
|---|---|---|---|
| **Nhấn chìm tăng** (engulfing) | Đỏ trước, xanh sau bao trùm toàn bộ cây đỏ | Hammer nằm phía trên vùng giá | Đảo chiều xu thế giảm |
| **Nhấn chìm giảm** | Xanh trước, đỏ sau bao trùm | Hammer nằm phía dưới | Đảo chiều xu thế tăng |
| **Hammer ngược ở vùng đỉnh (shooting star)** | Hai cây, ghép ra thân nhỏ nằm dưới biên độ | Hammer ngược | Nhiều khả năng đảo chiều xu thế tăng |
| **Kẹp** (tweezer) | Nến dài xanh rồi nến dài đỏ độ dài tương đương | Nến hai đầu bóng dài | Đảo chiều. Tin cậy **thấp hơn** engulfing |
| **Harami** (mẹ bồng con) | Thân nến sau nằm gọn trong thân nến trước | Thân nhỏ | Đảo chiều, tin cậy **thấp hơn** engulfing vì không bao trùm |
| **Morning Star** | Đỏ → doji hoặc hammer → xanh | Thân nhỏ ở 1/3 **trên** biên độ | Đảo chiều xu thế giảm, khả năng cao |
| **Evening Star** | Xanh → doji → đỏ | Thân nhỏ ở 1/3 **dưới** | Đảo chiều xu thế tăng |
| **Ba người lính** | Ba cây cùng màu liên tiếp | Một marubozu rất dài | Xu thế chắc chắn, tiếp diễn cao |

- **Engulfing mạnh nhất khi xu hướng trước đó là xu hướng mạnh.** Trước đó chỉ dao động nhẹ hoặc đi ngang thì độ tin cậy giảm hẳn — phải rất thận trọng.
- **Quy tắc 50% của piercing line và dark cloud:** hai nến có gap ở nến sau, nến thứ hai hồi lại và **phải vượt quá 50% độ dài nến thứ nhất** thì mẫu hình mới đáng tin. Piercing line vượt 50% nghĩa là bên mua thực sự vào cuộc; dark cloud xuống dưới 50% xác nhận đảo chiều. **Mẫu hình 3 nến có xác suất đúng cao hơn** dù bản chất vẫn quy về 1 cây — vì nó phổ biến nên nhiều người cùng hành động theo. Các tên upthrust, spring, "kéo lên để xả", "đạp xuống để kéo" chỉ là tên; cái quyết định vẫn là vị trí thân và độ dài sau khi ghép.

## Nến là điểm uốn — quy trình bắt đáy bắt đỉnh

> **Nến dùng để xác định khả năng tạo đỉnh, tạo đáy — tức điểm uốn. Nến không dùng để dự đoán xu hướng.** Xu hướng phải xác định bằng vĩ mô và cấu trúc giá, không bằng một cây nến.

- **Một cây nến đứng riêng không nói lên gì**; ý nghĩa chỉ xuất hiện khi xét trong chuỗi nến và xu thế trước đó. Nến không đặc biệt thì để yên, giống giá tăng lượng tăng bình thường. **Nến là công cụ cuối cùng, không phải công cụ đầu tiên** — phân tích xong các yếu tố kỹ thuật khác rồi mới mở nến để chọn điểm. Nến bắt mắt nhất khi mở đồ thị, nên đây là kỷ luật ngược bản năng.
- **Ít nhất hai dấu hiệu trùng nhau mới có cơ sở** — ví dụ lượng bán tăng **và** nến lưỡng lự trong xu thế tăng, hoặc nến lạ đúng vùng kháng cự, hỗ trợ, đường xu hướng. **Nến lạ thường xuất hiện ở vùng kháng cự hỗ trợ hoặc khi hết tin**; không có gì đỡ cho xu thế mà xuất hiện nến lạ ngược chiều là dấu hiệu nguy hiểm.
- **Khung thời gian: nến ngày** là khung chính ở Việt Nam (trong phiên phần lớn là tâm lý, qua một đêm người ta dùng lý trí nhiều hơn) — dùng phán đoán khu vực. **Nến tuần** chỉ có ý nghĩa như nến ngày ghép sẵn. **Nến 30 phút / 15 phút** chỉ mở ở vùng quan trọng — nơi có lượng đột biến hoặc nến đặc biệt — để xác nhận trong vùng đó thực sự có người mua hay bán và chọn thời điểm đặt lệnh; **không dùng để xác định xu hướng**. Phần đáng giá nhất là diễn biến cuối phiên: càng cuối phiên giá càng xuống mà lượng vẫn không giảm là lực cầu chủ động, không phải lệnh chờ bị quét.
- **Đọc thân nến như trạng thái thông tin:** thân ngắn suốt cả cây = thị trường không có tin mới hoặc đang chờ tin. Thân dài = có tác động tâm lý hoặc có tin mới, phải đi tìm cho ra tin đó. **Mỗi cổ phiếu có kiểu giao dịch riêng** — soi lại mẫu hình nến trong quá khứ của chính mã đó; đã từng đúng thì khả năng tiếp tục đúng là cao.

**Bốn điều kiện phải đủ trước khi dùng nến để bắt đáy:**

1. **Vĩ mô hoặc cơ bản doanh nghiệp** — nền tảng ủng hộ xu hướng hiện tại đã ngấm chưa, đã lâu chưa. Đã ngấm, đã lâu, mọi người thấy bình thường rồi thì phần còn lại chỉ là tâm lý, đúng lúc kỹ thuật có tác dụng.
2. **Giá đã về vùng hỗ trợ quan trọng.**
3. **Khối lượng giao dịch không giảm nữa.**
4. **Xu thế chính đã giảm ít nhất 2 nhịp** — theo cách chia ba mức, cần tối thiểu 2 nhịp trước khi kỳ vọng đảo chiều; lần 3 tin cậy hơn lần 2.

Đủ bốn điều kiện, xuất hiện thêm **mẫu hình nến đảo chiều tăng nằm trong vùng hỗ trợ** thì xác suất bắt đáy cao; có phân kỳ dương thì tốt hơn nữa. **Bắt đỉnh là ảnh gương:** xu thế trước là tăng, hỏi vĩ mô đã ngấm chưa (không tốt thêm được hoặc có khả năng xấu đi thì càng ủng hộ bán), giá đã vào vùng kháng cự, khối lượng tăng cao, xu thế tăng đã có ít nhất 2 nhịp — rồi ghép với mẫu hình nến đảo chiều giảm, thêm phân kỳ âm càng tốt.

- **Vào lệnh:** xác định vùng nghi ngờ bằng nến ngày → mở nến khung ngắn để chọn thời điểm đặt lệnh. **Luôn dùng cây nến liền trước để đặt stop loss** — mua thì stop ở đáy nến trước, bán thì stop ở đỉnh nến trước. Với harami: mua ở vùng giá đóng cửa và giá thấp nhất của nến harami, stop ở đáy nến trước. Với Morning Star: vào ở vùng giá đang được đẩy lên của cây thứ ba, stop ở đáy cây doji.
- **Đợi cây nến hình thành xong rồi mới đi theo, không đoán trước.** Gặp tình huống 50–50 — ví dụ hai cây lưỡng lự liên tiếp tại vùng quan trọng, chưa biết cây thứ ba xanh hay đỏ — thì chờ. Bù lại, **danh sách cổ phiếu theo dõi phải chuẩn bị sẵn**, vì khi thị trường xác nhận thì phải chọn rất nhanh.

## Nối đồ thị với chính sách tiền tệ

**Không đọc đồ thị tách rời bối cảnh tiền tệ tại thời điểm đó.** Cùng một mẫu hình ở hai giai đoạn khác nhau mang ý nghĩa khác nhau nếu bối cảnh tiền tệ khác nhau. Chỉ nhìn hình rồi chờ nó lặp lại là đi sai hướng.

1. **Đánh dấu giai đoạn chính sách lên trục thời gian của đồ thị** — đoạn thắt chặt, đoạn nới lỏng, mốc chuyển.
2. **Gán driver cho từng đoạn xu hướng.** Một xu hướng giảm nằm trọn trong đoạn thắt chặt phải được hiểu là do thắt chặt chi phối, không phải do đồ thị tự nó.
3. **Tách sự kiện tâm lý khỏi chính sách.** Một sự kiện đơn lẻ (vụ việc doanh nghiệp, thiên tai) làm giá xấu thêm nhưng mang tính tâm lý; nhận diện được đó là sự kiện chứ không phải chính sách thì kỳ vọng giá quay về vùng trước khi sự kiện xảy ra.
4. **Phân loại vùng theo lượng tiền.** Vùng tích luỹ hình thành *trước* thắt chặt là vùng nhiều tiền; hình thành *sau* thắt chặt là vùng ít tiền. Đang ở vùng ít tiền mà có tin bơm thêm tiền thì về nguyên tắc phải tốt hơn.
5. **Đặt trần cho kỳ vọng theo lượng tiền chính sách.** Tiền bơm ra chỉ đẩy thị trường tới một mức đỉnh nhất định rồi dừng. Muốn vượt trần đó phải có nới lỏng thêm hoặc cơ bản thay đổi thật.

- **Trong một vùng dao động đã xác định được bằng chính sách, vùng thấp là vùng mua, vùng đỉnh là vùng chốt.** Bán ở vùng kháng cự an toàn hơn mua ở vùng hỗ trợ, vì cái sau còn phụ thuộc tiền có tiếp tục vào hay không.
- **Thị trường cần thời gian thẩm thấu thông tin chính sách** — có tin hạ lãi suất không có nghĩa giá tăng ngay. Đây là chỗ kỹ thuật hữu dụng: nó cho biết thẩm thấu đã xong chưa, qua việc giá có ngừng giảm và lượng có ngừng cạn hay không. **Phân biệt ba lớp chu kỳ vì chúng chi phối ba loại quyết định khác nhau:** chu kỳ chính sách cho người nắm giữ dài, chu kỳ dòng tiền cho nhịp quý, chu kỳ tâm lý trên nền kỹ thuật cho giao dịch ngày. Đừng lấy kết luận của lớp này áp cho lớp kia.

---
