# Nâng cao: mô hình đa nhân tố và rào chắn vị thế

Hai khối kiến thức đứng riêng. Khối A trả lời "cái gì thực sự quyết định giá một cổ phiếu" bằng ngôn ngữ mô hình đa nhân tố. Khối B trả lời "làm sao khóa vị thế cổ phiếu đang cầm bằng hợp đồng tương lai".

## Mục lục

- [Câu hỏi và giới hạn của CAPM](#cau-hoi-va-gioi-han-capm)
- [APT — cách nhà nghiên cứu đi tìm nhân tố](#apt)
- [Fama-French 3 và 5 nhân tố](#fama-french)
- [Nhân tố thị trường quan trọng tới mức nào](#nhan-to-thi-truong)
- [Phân loại nhân tố theo nhóm](#phan-loai-nhan-to)
- [Kết hợp các nhân tố và hạn chế](#ket-hop-nhan-to)
- [Áp dụng vào Việt Nam](#ap-dung-viet-nam)
- [Hai kỹ thuật rào chắn vị thế](#hai-ky-thuat-rao-chan)
- [Hợp đồng tương lai làm công cụ rào chắn](#hop-dong-tuong-lai)
- [Tính tỷ lệ rào chắn và số hợp đồng](#tinh-ty-le-rao-chan)
- [Ví dụ chạy được: rào chắn một danh mục](#vi-du-rao-chan)
- [Giới hạn và rủi ro của hedging](#gioi-han-hedging)
- [Open Interest và dòng tiền phái sinh](#open-interest)

---

## Câu hỏi và giới hạn của CAPM

Câu hỏi này là bước cuối của chuỗi định giá. Chiết khấu dòng tiền về hiện tại cần một **tỷ suất lợi nhuận yêu cầu**. Hỏi cái gì quyết định tỷ suất đó chính là hỏi cái gì quyết định giá cổ phiếu. Mục đích không phải học thuộc kết luận nghiên cứu mà hiểu mô hình được dựng thế nào, để biết khi nào dùng được.

**CAPM chỉ có một nhân tố**: thị trường, truyền vào cổ phiếu qua beta (công thức và cách lấy từng biến ở `dinh-gia.md`, mục *Tỷ suất chiết khấu: CAPM và WACC*). Thực tế giá còn chịu hàng loạt biến vĩ mô và vi mô khác, nên giới nghiên cứu mở rộng sang mô hình nhiều nhân tố.

Nguyên lý xuyên suốt mọi mô hình dạng này: **mọi nhân tố đều đo bằng `F − E(F)`** — thực tế trừ kỳ vọng. Nhà đầu tư đã ra quyết định dựa trên kỳ vọng của mình, nên phần trùng kỳ vọng đã nằm trong giá và không tạo tác động. Không đọc "lãi suất tăng bao nhiêu" mà đọc "tăng bao nhiêu **so với kỳ vọng**"; lạm phát, tăng trưởng, lợi nhuận doanh nghiệp đều vậy. Cách nói tương đương: mọi biến số xét "so với bình thường", không xét giá trị tuyệt đối.

## APT — cách nhà nghiên cứu đi tìm nhân tố

**APT** (Arbitrage Pricing Theory) là dạng tổng quát đầu tiên cho phép đưa vào nhiều nhân tố. Cách nhà nghiên cứu đi tìm nhân tố:

1. Lấy số liệu quá khứ, chạy **hồi quy** (regression) dạng `R_i − R_f = α + b₁·(F₁ − E(F₁)) + … + bₙ·(Fₙ − E(Fₙ)) + e`. Vế trái là lợi nhuận vượt trội của cổ phiếu i so với lợi nhuận phi rủi ro; `bₖ` là hệ số của nhân tố k; `e` là sai số.
2. Giữ lại nhân tố **có ý nghĩa thống kê** ở một trong ba mức 1%, 5%, 10% — tương ứng độ tin cậy 99%, 95%, 90%.
3. Dấu hệ số cho chiều tác động: dương là tỷ lệ thuận, âm là tỷ lệ nghịch.

Khác CAPM ở chỗ: CAPM áp đặt trước một nhân tố duy nhất bằng lý thuyết; APT không nói trước có bao nhiêu nhân tố và là nhân tố nào — để dữ liệu chọn. Điểm yếu của APT: ra quá nhiều nhân tố, không ai theo dõi hết nổi. Vì vậy các mô hình về sau đều là **bản rút gọn của APT**.

## Fama-French 3 và 5 nhân tố

Bản rút gọn phổ biến nhất. Bản 3 nhân tố ra thập niên 1990, bản 5 nhân tố bổ sung năm 2015. Dữ liệu nghiên cứu gốc trải 50 năm (1963–2013).

| Nhân tố | Ký hiệu | Cách đo | Kết luận |
|---|---|---|---|
| **Thị trường** | `Rm − Rf` | Lợi nhuận thị trường trừ lợi nhuận phi rủi ro, hệ số là beta | Chi phối phần lớn |
| **Quy mô** | **SMB** (small minus big) | Lợi nhuận rổ vốn hóa nhỏ trừ rổ vốn hóa lớn | Nhỏ vượt trội lớn |
| **Giá trị** | **HML** (high minus low) | Lợi nhuận rổ B/P cao trừ rổ B/P thấp. B/P = giá trị sổ sách / thị giá | Giá trị vượt trội tăng trưởng |
| **Khả năng sinh lời** | **RMW** (robust minus weak) | Rổ lợi nhuận hoạt động cao trừ rổ lợi nhuận hoạt động thấp | Sinh lời cao vượt trội |
| **Quy mô đầu tư** | **CMA** (conservative minus aggressive) | Rổ tài sản tăng chậm trừ rổ tài sản tăng nhanh | Đầu tư thấp vượt trội |

Mô hình 5 nhân tố: `R_i − R_f = α + β·(Rm − Rf) + s·SMB + h·HML + r·RMW + c·CMA + e`. Bản 3 nhân tố là ba số hạng đầu. Cả năm nhân tố đều có ý nghĩa thống kê.

- **Lợi nhuận hoạt động** = doanh thu − giá vốn hàng bán − chi phí bán hàng và quản lý − chi phí tài chính (lãi vay; không tính lãi/lỗ mua bán tài sản hay cổ phiếu). Chia cho **vốn chủ sở hữu**, lấy 4 quý gần nhất.
- **Quy mô đầu tư** = tổng tài sản kỳ này / tổng tài sản kỳ trước (năm so năm hoặc quý so quý). Dùng CAPE cũng được nhưng phức tạp hơn mà không thêm được gì.
- **Đọc ngược chiều B/P.** Nghiên cứu gốc dùng B/P chứ không dùng P/B. B/P cao = giá trị sổ sách lớn hơn thị giá = **P/B thấp** = cổ phiếu giá trị. Quy về cách nói Việt Nam: P/E và P/B thấp đại diện cho cổ phiếu giá trị.

## Nhân tố thị trường quan trọng tới mức nào

Con số cần nhớ: **5 nhân tố Fama-French cùng giải thích khoảng 95% lợi nhuận yêu cầu; riêng nhân tố thị trường đã chiếm hơn 80%.** Còn 5% không mô hình nào giải thích được.

- **Xác định thị trường trước, lọc cơ bản sau.** Áp bộ tiêu chí vốn hóa nhỏ, giá trị, lợi nhuận tốt vào một thị trường đang xuống vẫn thua lỗ.
- Quan điểm "chọn cổ phiếu tốt rồi nắm giữ dài hạn" thiếu vế thị trường thì hỏng. Giá trị, lợi nhuận, tăng trưởng là yếu tố phụ. Trong thực hành, chọn vài yếu tố chính là đủ — đào sâu các yếu tố phụ là tranh giành phần 5% không đáng thời gian.

## Phân loại nhân tố theo nhóm

| Nhóm | Nhân tố có ý nghĩa và chiều tác động |
|---|---|
| **Vĩ mô** — 3 yếu tố chính | **Lạm phát bất thường**: nghịch, vì lạm phát cao buộc lãi suất tăng (bằng chứng qua kênh thu nhập khá yếu). **Tăng trưởng GDP / thu nhập**: thuận, quan hệ dài hạn. **Lãi suất trái phiếu chính phủ**: nghịch, quan sát qua thay đổi lợi suất và dịch chuyển đường cong lợi suất — đường cong dịch lên là tín hiệu xấu |
| **Cơ bản** — ngành và doanh nghiệp | Quy mô nhỏ (vốn hóa, thị giá, mệnh giá) vượt trội, nhưng nhỏ quá thì không tốt — chọn nhỏ vừa. Giá trị (P/E, P/B thấp) vượt trội. Lợi nhuận hoạt động trên vốn chủ cao vượt trội. Tăng trưởng tổng tài sản thấp vượt trội. Momentum và contrarian. Thanh khoản thấp cho lợi nhuận dài hạn tốt hơn — "thấp" nghĩa là ít được giao dịch, không phải doanh nghiệp yếu. Biến động giá lớn tháng trước thì tháng sau thường giảm |
| **Kỹ thuật** | Đường trung bình cắt lên/cắt xuống, và vùng kháng cự — hỗ trợ. Mọi chỉ số kỹ thuật đều quy về hai dạng này |
| **Lịch** | Hiệu ứng tháng Giêng, "sell in May and go away", hiệu ứng cuối tuần. Phụ thuộc năm tài chính từng nước nên không kết luận máy móc |
| **Sự kiện** | Cổ tức, cổ phiếu thưởng, chia tách, phát hành thêm, mua cổ phiếu quỹ. Chỉ hiệu ứng tâm lý, chỉ tồn tại trong cửa sổ ngắn quanh sự kiện rồi bão hòa |

- **Hai biến lãi suất mở rộng.** Chênh lệch lợi suất trái phiếu doanh nghiệp so với chính phủ giãn ra — nhất là giãn bất thường ở một nhóm ngành — báo giai đoạn ảm đạm. Cùng với đường cong lợi suất, hai biến này nói chung một điều: mặt bằng lãi suất lên là bất lợi. Giá hàng hóa (vàng, dầu) tăng thường không phải giai đoạn tốt, nhưng quan hệ yếu và phụ thuộc ngành.
- **Momentum và contrarian không mâu thuẫn.** Momentum áp cho đoạn đầu xu hướng tăng, contrarian áp khi giá đã tăng dài và lớn. Trên đồ thị: breakout khỏi kháng cự là momentum, bật ngược từ hỗ trợ là contrarian. Lọc nhiễu tín hiệu cắt: sau khi đường ngắn cắt lên đường dài, đợi thêm 2–3 phiên không cắt xuống mới mua.
- **Đường trung bình chính là định giá.** MA 50 phiên là mức định giá trung bình 50 phiên; giá cắt lên MA nghĩa là đang cao hơn mức đó. Đây là cách xác định vùng giá hợp lý cho người không làm phân tích cơ bản.
- **Sự kiện không tạo giá trị.** Cổ tức và cổ phiếu thưởng tạo "hiệu ứng giá trị"; chia tách tạo "hiệu ứng giá rẻ" và tăng thanh khoản; mua cổ phiếu quỹ tạo cảm giác doanh nghiệp đang tăng trưởng. Tổng tài sản cổ đông không đổi. Chiến lược sự kiện là **bán trước ngày chốt quyền**.
- **Phát hành riêng lẻ khác hẳn phát hành cho cổ đông hiện hữu.** Phát hành cho cổ đông hiện hữu điều chỉnh giá theo bình quân gia quyền giá cũ và giá phát hành nên có động lực đánh giá lên để cổ đông chịu nộp tiền. Phát hành riêng lẻ không bị điều chỉnh giá và bên mua vào ở giá thấp — bán xuống sát giá mua vẫn lời, nên động lực đánh lên rất thấp.

## Kết hợp các nhân tố và hạn chế

Quy trình lọc danh mục, làm được bằng công cụ lọc của bất kỳ trang dữ liệu tài chính nào:

1. **Chia rổ theo quy mô trước.** Xếp toàn thị trường theo vốn hóa (hoặc thị giá), chia 3 hoặc 5 nhóm đều nhau theo cách Fama-French. Lấy nhóm nhỏ — nhưng tránh nhóm nhỏ nhất.
2. **Trong nhóm đó, lọc lợi nhuận hoạt động trên vốn chủ cao.** Chỉ tiêu này phải tự tính. Thay tạm bằng E/P được, nhưng E/P gánh cả thu nhập tài chính nên kém sạch hơn.
3. **Lọc tiếp tốc độ tăng tổng tài sản thấp.** Loại dần sẽ ra danh sách cuối.

Kết quả khi kết hợp: **nhỏ vừa + B/P cao (P/B thấp) + lợi nhuận hoạt động cao** là tổ hợp mạnh nhất. Nhóm vốn hóa nhỏ vượt trội nhóm lớn ở hầu hết các ô, trừ ô lợi nhuận thấp và giá trị thấp — ở đó cả hai nhóm đều kém. Bốn hạn chế khi dùng kết quả nghiên cứu:

- **Sai lệch do dữ liệu (data mining).** Người nghiên cứu có thể chọn mẫu và phương pháp để ra kết quả đẹp. Đã có trường hợp làm lại với cùng dữ liệu và phương pháp mà không tái lập được kết quả.
- **Sai lệch sau công bố.** McLean & Pontiff (2016) làm lại 97 chiến lược đã công bố: lợi nhuận vượt trội **giảm tới 58% sau khi công bố**. Chiến thuật càng phổ biến càng mất lợi thế.
- **Kết luận chỉ đúng ở tầm vài chục năm.** Một nhà đầu tư có thể rơi trọn vào đoạn quy tắc không hiệu quả. Không áp máy móc.
- **Áp dụng phải kiên trì và nhất quán.** Nay vốn hóa nhỏ mai vốn hóa lớn thì mất hết chiều sâu — đó là giao dịch ngắn hạn, không phải đầu tư theo nhân tố.

## Áp dụng vào Việt Nam

- **Vĩ mô:** vẫn là bộ ba lạm phát — lãi suất — tăng trưởng, trong đó tăng trưởng gắn liền với hai cái kia nên thường gộp còn lạm phát và lãi suất. Các quan hệ này là quan hệ **dài hạn**; với tầm nhìn ngắn hạn thì chu kỳ chính sách quan trọng hơn.
- **Cơ bản:** bốn nhân tố giữ nguyên. Nhân tố quy mô hoạt động khá tốt ở Việt Nam, kèm hiệu ứng thị giá nhỏ — nhà đầu tư cá nhân chuộng cổ phiếu thị giá thấp vì cảm giác rẻ và cảm giác dễ tăng. Khi thị trường tăng mạnh, nhóm P/E và P/B cao đôi khi chạy tốt hơn; nhưng dài hạn thì P/E và P/B thấp vẫn vượt trội.
- **Cảnh báo về tăng trưởng tài sản:** ở Việt Nam tài sản tăng nhanh thường đi kèm tăng vốn và các trò chơi tài chính. Ngắn hạn giai đoạn tăng vốn hay đi kèm làm giá nên không thấy tác động xấu; dài hạn nhóm này không vượt trội.
- **Kỹ thuật:** momentum hoạt động khá tốt, breakout yếu hơn.
- **Lịch:** hiệu ứng tháng Giêng phải xét cùng hiệu ứng Tết vì Tết ảnh hưởng rõ tới dòng tiền. Bằng chứng cho hiệu ứng cuối tuần không vững — phiên cuối tuần yếu thường vì thị trường đã nghi ngờ từ trước, không phải quy luật cố định.
- **Sự kiện:** hiệu ứng mạnh và xuất hiện thường xuyên, nhưng luôn giới hạn trong cửa sổ.
- **Đặc điểm chung:** thị trường đi theo xu hướng, theo đám đông và theo dòng tiền.

---

## Hai kỹ thuật rào chắn vị thế

Phân biệt ba trạng thái trước khi bàn kỹ thuật:

- **Đầu cơ** (speculation): nắm một chiều với kỳ vọng giá tăng hoặc giảm. Mua cổ phiếu chờ lên và short phái sinh chờ xuống cùng là đầu cơ.
- **Chênh lệch giá** (arbitrage): mua bán đồng thời cùng một tài sản ở hai thị trường để chốt khoản chênh. Rất hiếm gặp.
- **Rào chắn** (hedge): khóa vị thế lại. Mục tiêu là phòng vệ rủi ro, không phải tìm lợi nhuận.

Hai kỹ thuật rào chắn vị thế cổ phiếu: **rebalancing** — mua bán **cùng một lượng** cổ phiếu quanh vùng hỗ trợ/kháng cự để cơ cấu lại vị thế mà không đổi số cổ phiếu nắm giữ (chi tiết ở `danh-muc-va-luan-chuyen.md`, mục *Rebalancing*); và **hedging bằng hợp đồng tương lai** — mở vị thế phái sinh ngược chiều để trung hòa rủi ro thị trường của danh mục, toàn bộ phần dưới.

## Hợp đồng tương lai làm công cụ rào chắn

**Hợp đồng tương lai chỉ số** là thỏa thuận mua hoặc bán chỉ số cơ sở (ở Việt Nam là VN30) ở một mức giá xác định vào một ngày trong tương lai. Nói gọn: đoán chỉ số. **Long** = mua = đoán lên. **Short** = bán = đoán xuống.

- **Giá trị một hợp đồng** = điểm chỉ số phái sinh × **hệ số nhân**. Hệ số nhân và chỉ số cơ sở được phép nằm trong đặc tả hợp đồng, phải tra tại thời điểm dùng; ví dụ trong file lấy hệ số nhân 100.000 đồng mỗi điểm chỉ số.
- **Ký quỹ ban đầu** là một tỷ lệ phần trăm giá trị hợp đồng, do sở giao dịch và công ty chứng khoán quy định — phải tra tại thời điểm dùng. Tỷ lệ này tạo đòn bẩy: bỏ một phần vốn nhưng chịu lãi/lỗ trên toàn bộ giá trị hợp đồng.
- **Đánh dấu theo thị trường hàng ngày** (mark to market): lãi/lỗ ghi nhận ngay trong ngày. Tài khoản tụt dưới mức ký quỹ duy trì thì phải nộp thêm tiền.
- **Kỳ hạn**: hợp đồng 1 tháng thanh khoản cao nhất. Càng xa ngày đáo hạn càng khó đoán và **basis** — chênh lệch giữa giá phái sinh và chỉ số cơ sở — càng lớn. Đến ngày đáo hạn hợp đồng tự đóng, nhưng không bắt buộc chờ đáo hạn mới chốt lời.

**Vì sao rào chắn được vị thế cổ phiếu.** Danh mục cổ phiếu là vị thế long, chịu rủi ro thị trường chung. Short hợp đồng tương lai chỉ số tạo vị thế ngược chiều với đúng nguồn rủi ro đó. Long cổ phiếu + short tương lai = **vị thế đã khóa** (closed position). Điều kiện để bù được: danh mục phải tương quan với chỉ số cơ sở. Hai tình huống điển hình:

1. **Sửa sai khi chưa bán được cổ phiếu.** Vừa mua xong thì nhận ra sai, chu kỳ thanh toán chưa về nên chưa bán được. Short hợp đồng tương lai để chặn lỗ trong mấy ngày chờ. Đoán đúng thì lãi phái sinh bù lỗ cổ phiếu; đoán sai thì lỗ cả hai phía.
2. **Khóa vị thế tại kháng cự.** Đang cầm cổ phiếu tới vùng kháng cự, muốn đợi breakout nhưng sợ giảm, mà bán đi lại sợ mua không kịp. Short hợp đồng tương lai giá trị tương đương danh mục. Breakout thật thì đóng vị thế phái sinh, giữ nguyên cổ phiếu.

**Đọc mùa vụ của phái sinh.** Phần lớn vị thế mở trong tháng phục vụ phòng ngừa; chỉ tới gần ngày đáo hạn mới chuyển sang đầu cơ. Vì vậy theo dõi số hợp đồng mở và đóng suốt tháng, đậm nhất là tuần cuối trước đáo hạn.

## Tính tỷ lệ rào chắn và số hợp đồng

1. **Giá trị danh mục cần khóa** `V = Σ (số cổ phiếu × thị giá)` của từng mã.
2. **Beta danh mục** `β_p = Σ (tỷ trọng mã i × beta mã i)`. Beta từng mã lấy từ hồi quy lợi nhuận mã đó theo lợi nhuận chỉ số cơ sở. Beta là hệ số biến động: danh mục beta 1,2 kỳ vọng biến động 1,2% khi chỉ số biến động 1%.
3. **Giá trị một hợp đồng** `C = F × m`, với `F` là điểm hợp đồng tương lai đang giao dịch, `m` là hệ số nhân.
4. **Số hợp đồng cần mở: `N = (V × β_p × h) / (F × m)`** — `h` là **tỷ lệ rào chắn** muốn đạt (`h = 1` khóa toàn phần, `h = 0,5` khóa một nửa). Làm tròn về số nguyên. Đang long cổ phiếu thì **short** N hợp đồng.
5. **Ký quỹ cần chuẩn bị** `= N × F × m × tỷ lệ ký quỹ`, cộng một khoản đệm cho mark-to-market hàng ngày.

Khi `β_p = 1` và `h = 1`, công thức thu về đúng quy tắc đơn giản: bán hợp đồng tương lai có tổng giá trị bằng giá trị danh mục.

## Ví dụ chạy được: rào chắn một danh mục

**Dữ liệu giả định.** Danh mục 6 mã, tổng giá trị `V = 1,25 tỷ đồng`, beta danh mục `β_p = 1,2`. Hợp đồng tương lai kỳ hạn 1 tháng đang ở `F = 1.250 điểm`, hệ số nhân `m = 100.000 đồng/điểm`, tỷ lệ ký quỹ giả định 13%. Khóa toàn phần: `h = 1`.

- Giá trị một hợp đồng: `C = 1.250 × 100.000 = 125.000.000 đồng`
- Số hợp đồng: `N = (1.250.000.000 × 1,2 × 1) / 125.000.000 = 12` → **short 12 hợp đồng**
- Ký quỹ: `12 × 125.000.000 × 13% = 195.000.000 đồng`, cộng đệm cho biến động hàng ngày

**Kịch bản 1 — thị trường giảm 5%.** Chỉ số về 1.187,5 điểm, giảm 62,5 điểm. Cổ phiếu: `1,25 tỷ × (−5% × 1,2) = −75.000.000`. Short 12 hợp đồng: `62,5 × 100.000 × 12 = +75.000.000`. **Ròng: 0.**

**Kịch bản 2 — thị trường tăng 5%.** Chỉ số lên 1.312,5 điểm, tăng 62,5 điểm. Cổ phiếu: `1,25 tỷ × (+5% × 1,2) = +75.000.000`. Short 12 hợp đồng: `−62,5 × 100.000 × 12 = −75.000.000`. **Ròng: 0.**

**Đọc kết quả.** Hedge cắt cả hai chiều. Nó không tạo lợi nhuận — nó mua thời gian: giữ nguyên tài khoản trong lúc chờ bán được cổ phiếu hoặc chờ tín hiệu rõ hơn. Đổi lại là chi phí ký quỹ, phí và thuế giao dịch.

**Kịch bản 3 — hedge không hoàn hảo.** Chỉ số vẫn giảm 5% nhưng danh mục thực tế chỉ giảm 4%: cổ phiếu lỗ 50 triệu, phái sinh lãi 75 triệu → **lãi ròng 25 triệu**. Nếu danh mục giảm 8%: cổ phiếu lỗ 100 triệu, phái sinh lãi 75 triệu → **lỗ ròng 25 triệu**. Phần lệch này là rủi ro tương quan, không bao giờ khử hết được.

## Giới hạn và rủi ro của hedging

Phần hay bị bỏ qua nhất. Hedge không phải cái khiên tuyệt đối.

- **Rủi ro tương quan là rủi ro lớn nhất ở Việt Nam.** Cổ phiếu đang cầm không đi giống chỉ số cơ sở thì hedge lệch. Khắc phục một phần: chọn mã có beta gần 1 với chỉ số, hoặc chỉ hedge khi danh mục **từ 5 mã trở lên**. Con số 5 chỉ là sàn thô — thước đo thật là tương quan giữa danh mục và chỉ số cơ sở; đo được tương quan thì dùng nó thay cho số mã. **Hedge một mã đơn lẻ hầu như không hiệu quả**, vì cá nhân không thể nắm đủ 30 mã theo đúng tỷ trọng rổ chỉ số.
- **Beta không ổn định.** Beta ước lượng từ quá khứ; beta thực trong kỳ hedge lệch đi thì kết quả ròng lệch theo, như kịch bản 3. Cộng thêm **rủi ro basis**: giá phái sinh không bằng chỉ số và khoảng chênh tự biến động.
- **Chi phí và dòng tiền.** Khóa lỗ thì cũng khóa lãi — đó là cái giá, không phải lỗi. Cộng thêm phí, thuế, chi phí vốn ký quỹ. Mark-to-market có thể gọi thêm tiền giữa chừng dù kết cục cuối cùng hòa — không đủ tiền nộp thì bị đóng vị thế ở đúng chỗ xấu nhất.
- **Thị trường đi ngang thì hedge tốn công vô ích.** Hedge có nghĩa khi xu thế rõ ràng.
- **Sai thời điểm mở.** Hedge chỉ có nghĩa khi đã nhận ra vị thế cổ phiếu sai. Mở phái sinh **trước** khi mua cổ phiếu là vừa mua vừa bán, triệt tiêu nhau, vô nghĩa.
- **Bên đối diện mạnh hơn.** Quỹ lớn nắm cả cổ phiếu cơ sở lẫn vị thế phái sinh, có thể tác động lên chỉ số để phục vụ vị thế của họ — hiện tượng ép vị thế đối ứng qua tác động lên chỉ số cơ sở. Đây là nghi vấn về động cơ, không phải kết luận.
- **Đừng trượt từ hedge sang đầu cơ.** Đòn bẩy khiến lãi có thể rất lớn trong 1–2 ngày, nhưng lỗ đến đúng tốc độ đó.

## Open Interest và dòng tiền phái sinh

**Open Interest (OI)** là số hợp đồng đang mở tại một thời điểm. Khác **khối lượng giao dịch** (volume) — volume là số hợp đồng khớp trong phiên, kể cả những người đang có vị thế trao tay cho nhau. OI tăng nghĩa là có người mới mở vị thế, tiền mới vào; OI giảm là có người đóng vị thế rời đi; OI đứng yên mà volume lớn là người trong cuộc trao tay nhau, gần với giao dịch trao tay giữa các vị thế cũ. Đọc OI theo vùng giá, tương tự phân tích giá — khối lượng:

| OI theo vùng giá | Hàm ý |
|---|---|
| OI cao ở vùng giá thấp, giảm dần khi giá lên | Tiền vào yếu, khả năng đảo chiều cao |
| OI thấp ở vùng giá cao, tăng dần ở vùng giá thấp | Tiền vào nhiều, khả năng đảo chiều xu thế giảm cao |
| OI thấp ở vùng giá thấp, tăng dần ở vùng giá cao | Xu thế tăng nhiều khả năng tiếp diễn |
| OI cao ở vùng giá cao, giảm dần ở vùng giá thấp | Xu thế giảm tiếp diễn |

- **Đột biến OI ở vùng giá cao và ở vùng giá thấp là hai chuyện khác nhau** dù dùng chung một từ. Đột biến chỉ cần cao hơn mức bình thường của chính nó, không cần OI hai vùng bằng nhau.
- **Basis bổ sung cho OI.** Giá phái sinh cao hơn cơ sở là kỳ vọng chỉ số tăng, thấp hơn là kỳ vọng giảm; basis giãn liên tục phản ánh kỳ vọng mạnh. Chỉ mang tính tương đối — người chơi phái sinh có thể đoán sai hoặc cố tình tác động giá. Số liệu OI có sẵn trên phần mềm giao dịch phái sinh và một số trang dữ liệu tài chính.

---
