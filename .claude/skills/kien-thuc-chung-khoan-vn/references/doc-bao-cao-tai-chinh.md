# Đọc hiểu báo cáo tài chính

File này trả lời: đọc ba báo cáo tài chính theo thứ tự nào, rút ra chỉ tiêu gì, nhận ra thủ thuật kế toán qua dấu hiệu nào. Phần định giá (DCF, PE, PB, CAPM, mô hình cổ tức) nằm ở `dinh-gia.md`.

## Mục lục

- [Ba báo cáo và quy trình đọc](#ba-bao-cao)
- [Bảng cân đối kế toán](#bang-can-doi-ke-toan)
- [Báo cáo kết quả kinh doanh](#bao-cao-ket-qua-kinh-doanh)
- [Báo cáo lưu chuyển tiền tệ](#bao-cao-luu-chuyen-tien-te)
- [Dựng ngược báo cáo tài chính](#dung-nguoc-bctc)
- [Khấu hao và hoạt động tài chính](#khau-hao-va-hoat-dong-tai-chinh)
- [Bóc tách ROE — ví dụ tính đầu-cuối](#boc-tach-roe)
- [Đòn bẩy và tăng vốn](#don-bay-va-tang-von)
- [Bộ chỉ tiêu chất lượng doanh nghiệp](#bo-chi-tieu)
- [Thủ thuật đằng sau những con số](#thu-thuat)
- [Key driver theo ngành](#key-driver)
- [Số liệu lấy ở đâu](#so-lieu-lay-o-dau)
- [Giới hạn của báo cáo tài chính](#gioi-han)
- [Phụ lục A — báo cáo tài chính ngân hàng](#phu-luc-a-ngan-hang)
- [Phụ lục B — báo cáo tài chính công ty chứng khoán](#phu-luc-b-chung-khoan)
- [Phụ lục C — báo cáo tài chính bảo hiểm](#phu-luc-c-bao-hiem)
- [Đối chiếu chỉ tiêu phi tài chính ↔ tài chính](#doi-chieu-chi-tieu)

---

## Ba báo cáo

| Báo cáo | Trả lời câu gì | Tính chất |
|---|---|---|
| **Bảng cân đối kế toán** | Doanh nghiệp *có* gì, tiền ở đâu ra | Số dư tại **một thời điểm** |
| **Báo cáo kết quả kinh doanh (KQKD)** | Trong kỳ *lãi lỗ* bao nhiêu | Cộng dồn **trong kỳ** |
| **Báo cáo lưu chuyển tiền tệ (LCTT)** | Lợi nhuận đó có thành **tiền thật** không | Cộng dồn **trong kỳ** |

Ba mắt xích nối chúng: **lợi nhuận sau thuế của kỳ chảy vào vốn chủ sở hữu** ở dòng lợi nhuận chưa phân phối (KQKD → cân đối); **LCTT bắt đầu từ lợi nhuận** rồi điều chỉnh khoản phi tiền mặt và thay đổi vốn lưu động, gọi là phương pháp gián tiếp (KQKD → LCTT); **tiền cuối kỳ của LCTT phải khớp dòng tiền và tương đương tiền trên cân đối** (LCTT → cân đối). **Chỉ có một đẳng thức luôn đúng: tổng tài sản = nợ phải trả + vốn chủ sở hữu.** Mọi con số khác = phần thực tế + sai số + phần doanh nghiệp muốn nó thế nào. Bốn dạng báo cáo theo loại hình — **phi tài chính** (phổ biến nhất), **ngân hàng**, **chứng khoán**, **bảo hiểm** — phản ánh cùng bộ chỉ tiêu, chỉ khác tên gọi; nắm chắc phi tài chính rồi dịch ngang sang ba nhóm kia (ba phụ lục cuối file).

**Quy trình đọc — ba câu hỏi, đúng thứ tự:**

1. **Có tạo ra lợi nhuận không?** — lợi nhuận sau thuế của cổ đông công ty mẹ, theo chuỗi nhiều quý và nhiều năm.
2. **Lợi nhuận đó có bền không?** — ổn định hay đột biến. Một quý nhảy vọt giữa chuỗi quý phẳng thì năng lực thật nằm ở mặt bằng cũ, không nằm ở quý đột biến.
3. **Lợi nhuận có gắn với tiền không?** — lưu chuyển tiền thuần từ hoạt động kinh doanh, đối chiếu khoản phải thu và hàng tồn kho.

Ba câu này áp cho doanh nghiệp phi tài chính; với nhóm tài chính câu 3 mất ý nghĩa. **Đọc qua thời gian dài — một hai năm có ý nghĩa hơn một quý. Câu hỏi cuối cùng luôn là *ổn định hay biến động*, không phải *tăng hay giảm*.**

## Bảng cân đối kế toán

- **Tài sản ngắn hạn** (dưới 1 năm): tiền và tương đương tiền; đầu tư tài chính ngắn hạn; phải thu ngắn hạn; hàng tồn kho. **Ba hạng mục luôn phải kiểm tra: tiền, phải thu, tồn kho** — chúng cấu thành vốn lưu động. **Tài sản dài hạn**: tài sản cố định (gắn khấu hao), tài sản dở dang, đầu tư vào công ty con và liên kết.
- **Nợ phải trả**: ngắn hạn (đáng chú ý nhất là phải trả người bán) và dài hạn. **Vốn chủ sở hữu**: **vốn góp của chủ sở hữu** (ghi theo mệnh giá 10.000 đồng/cp — **chia dòng này cho 10.000 ra số lượng cổ phiếu**, không lấy tổng vốn chủ chia); **thặng dư vốn cổ phần** (phần vượt mệnh giá khi phát hành); chênh lệch tỷ giá; chênh lệch đánh giá lại tài sản; **lợi nhuận sau thuế chưa phân phối**; lợi ích cổ đông không kiểm soát.

**Đọc theo hai lượt.** Lượt 1 — cấu trúc: quét tổng tài sản, tỷ trọng tài sản ngắn hạn, tổng nợ vay, vốn chủ sở hữu; so tài sản ngắn hạn với nợ ngắn hạn (current ratio) để biết khả năng trả nợ — chỉ số này quan trọng với người cho vay, ít quan trọng với nhà đầu tư. Lượt 2 — bất thường: so cùng hạng mục giữa các kỳ, tìm chỗ nhảy. **Cái gì bất thường mới đáng chú ý.**

| Hạng mục nhảy | Đọc thế nào |
|---|---|
| Tài sản ngắn hạn tăng do **phải thu** | Dấu hiệu đẩy doanh thu. Đối chiếu ngay doanh thu và dòng tiền kinh doanh |
| Tài sản ngắn hạn tăng do **tồn kho** | Có thể là khó bán; cũng có thể là cơ hội nếu giá đầu ra đang lên (tồn kho giá thấp, bán giá cao) |
| **Tiền mặt** nhiều bất thường | Không hẳn tốt. Tăng vốn rồi để tiền nằm yên là chi phí cơ hội |
| **Tài sản dài hạn** tăng đột ngột | Thường do hợp nhất công ty con (sở hữu ≥50%) hoặc mua bán tài sản. Kiểm tra thay đổi phạm vi hợp nhất |
| **Nợ dài hạn** tăng đột biến | Tốt hơn giảm đột biến: ngân hàng chịu cho vay tức là đánh giá được. Kết hợp ROA cao thì lợi cho ROE |
| **Vốn chủ sở hữu** nhảy; **lợi nhuận chưa phân phối** tích luỹ cao | Vốn chủ nhảy: kiểm tra tăng vốn, hợp nhất, hoặc bán bớt tỷ lệ để thoát hợp nhất (51% → 49% thì công ty con thành liên kết, tài sản và vốn chủ giảm tương ứng). Lợi nhuận chưa phân phối cao là nguyên liệu cho chia cổ tức tiền hoặc cổ phiếu ở kỳ tới |

**Bất thường không đồng nghĩa với xấu.** Doanh nghiệp thường xuyên bất thường biến động mạnh cả hai chiều: cơ hội đến nhanh hơn khi thị trường tốt, bị bán mạnh hơn khi thị trường xấu. Doanh nghiệp số liệu đều đặn là loại phù hợp nắm giữ dài hạn.

## Báo cáo kết quả kinh doanh

| # | Dòng | Nói lên điều gì |
|---|---|---|
| 1–2 | Doanh thu bán hàng; các khoản giảm trừ | Giảm trừ lớn hoặc thất thường là dấu vết hàng bị trả lại |
| 3 | **Doanh thu thuần** = 1 − 2 | Mẫu số của mọi tỷ lệ |
| 4 | Giá vốn hàng bán | Chi phí của **hàng đã bán**. Xây 100 căn bán 50 thì chỉ ghi giá vốn 50 căn |
| 5 | **Lợi nhuận gộp** = 3 − 4 | **Vị thế cạnh tranh.** Chưa dính quản trị, chưa dính vay nợ |
| 6–8 | Doanh thu / chi phí hoạt động tài chính; lãi lỗ công ty liên doanh liên kết | Lãi tiền gửi, cổ tức, lãi lỗ chứng khoán (sở hữu <20%); phần sở hữu 20%–50% ở dòng 8. **Tách riêng chi phí lãi vay** — phần gắn đòn bẩy |
| 9–11 | Chi phí bán hàng; chi phí quản lý; **lợi nhuận thuần từ HĐKD** | Hai dòng chi phí đo hiệu quả quản trị. Dòng 11 = **khả năng quản trị**, chỉ sau khi loại 6, 7, 8 |
| 12–15 | Thu nhập khác, chi phí khác, lợi nhuận khác; **tổng lợi nhuận kế toán trước thuế** | Khoản **một lần**: thanh lý, bán tài sản đã khấu hao hết. So dòng 15 với dòng 11 để thấy vai trò hoạt động chính |
| 16–18 | Thuế hiện hành, thuế hoãn lại, lợi nhuận sau thuế | Khả năng quản lý thuế; dòng 18 là chỉ tiêu phần lớn nhà đầu tư nhìn |
| 19–20 | Lợi ích cổ đông không kiểm soát; **LNST của cổ đông công ty mẹ** | Dòng 19 **không thuộc về** doanh nghiệp đang quan sát; **dòng 20 mới là phần của cổ đông — dòng cần nhìn nhất** |
| 21–22 | EPS; lãi suy giảm trên cổ phiếu | Lợi nhuận chia số cổ phiếu **bình quân gia quyền** trong kỳ |

Ba chỗ phải dừng lại:

- **Biên lợi nhuận gộp = dòng 5 / dòng 3** — vị thế cạnh tranh. Chỉ có nghĩa khi so **cùng ngành**: cùng ngành thì nhìn riêng chỉ tiêu này đã biết ai tốt hơn, không cần quan tâm quản lý hay vay nợ.
- **Dòng 11 sau khi loại 6, 7, 8** — cùng biên gộp thì ai quản chi phí bán hàng và quản lý tốt hơn sẽ lãi hơn. Phải loại hoạt động tài chính vì doanh thu tài chính lớn làm hiểu sai hiệu quả, còn chi phí lãi vay tuy làm giảm lợi nhuận nhưng đang tạo hiệu ứng đòn bẩy có lợi.
- **Dòng 15 so dòng 11** — chênh lệch nằm ở thu nhập/chi phí khác. Chênh lớn nghĩa là lợi nhuận năm đó đến từ khoản một lần.

**Bẫy tên gọi:** "lợi nhuận thuần từ hoạt động kinh doanh" (dòng 11) **không phải** "lợi nhuận từ hoạt động kinh doanh chính" — dòng 11 đã gồm cả hoạt động tài chính. Doanh nghiệp có kinh doanh chính đi ngang hoặc kém đi vẫn có thể có dòng 11 rất đẹp nhờ doanh thu tài chính. **Cổ đông thiểu số:** sở hữu >50% thì hợp nhất 100% lợi nhuận công ty con, nhưng nếu chỉ nắm 60% thì 40% là của cổ đông không kiểm soát và phải trừ. **Chi phí lãi vay** nhìn theo tỷ lệ trên dư nợ vay hoặc trên doanh thu: tỷ lệ thấp phản ánh vị thế tín dụng tốt — ngân hàng đánh giá doanh nghiệp an toàn nên cho vay rẻ.

## Báo cáo lưu chuyển tiền tệ

| Hoạt động | Gồm gì | Đọc thế nào |
|---|---|---|
| **Kinh doanh** | Lợi nhuận, điều chỉnh phi tiền mặt, thay đổi vốn lưu động | Phải dương và bám sát lợi nhuận. Quan trọng nhất |
| **Đầu tư** | Mua sắm/xây dựng tài sản cố định, góp vốn, thu hồi góp vốn | Âm là bình thường khi mở rộng. Dương lớn thường do bán tài sản hoặc thu hồi vốn góp — kiểm tra vì sao |
| **Tài chính** | Vay, trả nợ gốc, phát hành cổ phiếu, trả cổ tức | Cho biết đang bù dòng tiền bằng vay hay bằng vốn |

Ba dòng cộng lại ra lưu chuyển tiền thuần trong kỳ; cộng tiền đầu kỳ ra tiền cuối kỳ. **Vì sao lợi nhuận khác dòng tiền — bốn nguyên nhân:** (1) **bán chịu** — doanh thu ghi khi giao hàng, không phải khi thu tiền, phải thu tăng thì dòng tiền âm; (2) **tồn kho tăng** — tiền đã ra mua nguyên liệu, hàng chưa bán được; (3) **khấu hao**, chiều ngược lại — giảm lợi nhuận nhưng không chi tiền nên phải **cộng ngược lại** (lợi nhuận gộp 100, khấu hao 20, lợi nhuận trước thuế 80 → trong LCTT cộng lại 20); (4) **đầu tư lớn** — lợi nhuận tốt nhưng tiền đổ vào tài sản cố định thì tiền cuối kỳ vẫn cạn. Ví dụ đọc một chuỗi: kinh doanh −92, đầu tư +66 (chủ yếu thu hồi vốn góp), tài chính +10 (vay mới) → tiền thuần −16; tiền đầu kỳ 23, cuối kỳ 7. Đọc đúng: **lợi nhuận đẹp nhưng tiền âm vì phải thu và tồn kho**, và doanh nghiệp đang lấy tiền thu hồi vốn góp bù cho hoạt động kinh doanh. Chưa mất khả năng thanh toán, nhưng một kỳ nữa như vậy là hết tiền.

## Dựng ngược BCTC

Cho trước một kịch bản kinh doanh, tự dựng ra ba báo cáo. Làm được một lần thì đọc báo cáo thật rất dễ vì biết từng con số sinh ra từ đâu. Đây là phần khó nhất, kể cả với người trong ngành. **Doanh nghiệp giả định: quán nước.** Doanh nghiệp niêm yết khác quán nước đúng hai thứ — tiêu chuẩn về vốn và tiêu chuẩn về kế toán. Bản chất giống hệt: có doanh thu, chi phí, lợi nhuận.

**Bước 1 — thông số đầu vào.** Vốn: 3 người góp 10 triệu mỗi người = 30 triệu vốn chủ. Nợ: vay 50 triệu, lãi 10%/năm → lãi vay 5 triệu/năm. Tài sản cố định 11 triệu (bàn ghế, ấm pha trà, xe máy), khấu hao đều 2 năm → 5,5 triệu/năm. Giá vốn 40.000 đồng/gói, giá bán 78.000 đồng/gói, 20 gói/ngày. Chi phí bán hàng 48 triệu/năm. Vốn lưu động: tồn kho 1 tuần bán; 50% khách trả chậm 1 tuần (phải thu); 50% tiền hàng trả chậm nhà cung cấp 1 tuần (phải trả); tiền mặt tối thiểu 1 ngày bán. 50 triệu nhàn rỗi đem đầu tư tài chính. Phân biệt cần nắm: **giá vốn hàng bán** gắn trực tiếp với sản phẩm bán ra; **chi phí bán hàng** gắn với quá trình hoạt động, không gắn từng sản phẩm.

**Bước 2 — cân đối lúc mới thành lập.** Nguồn vốn 30 (vốn chủ) + 50 (nợ dài hạn) = 80. Tài sản 80, toàn bộ là tiền. Đẳng thức khớp. **Bước 3 — cân đối khi đi vào hoạt động.** Vốn chủ **không đổi** — vốn là nguồn tạo ra tài sản, không phải tài sản. Tiền chuyển hoá thành: tài sản cố định 11, tồn kho 1 tuần, đầu tư tài chính 50, tiền còn lại 13. Tổng tài sản vẫn 80.

**Bước 4 — KQKD năm 1.** Doanh thu thuần − giá vốn = lợi nhuận gộp; trừ chi phí bán hàng 48; trừ chi phí quản lý (đã gồm khấu hao 5,5); cộng doanh thu tài chính; trừ chi phí tài chính (lãi vay 5) → lợi nhuận thuần HĐKD; cộng lợi nhuận khác → lợi nhuận trước thuế; trừ thuế 20% → lợi nhuận sau thuế; trừ lợi ích cổ đông không kiểm soát → LNST cổ đông công ty mẹ. Lưu ý: **doanh thu hoạt động tài chính chỉ là phần lời**, không phải toàn bộ số tiền đem đầu tư; nếu lỗ thì khoản lỗ chuyển sang chi phí tài chính, cộng với lãi vay.

**Bước 5 — đóng vòng lặp.** Lợi nhuận sau thuế chảy vào lợi nhuận chưa phân phối trên cân đối cuối năm 1; tổng tài sản tăng đúng bằng mức tăng nguồn vốn. **Báo cáo thay đổi chủ yếu do lợi nhuận tạo ra** — nếu tài sản tăng mà không do lợi nhuận thì phải hỏi tăng do đâu (tăng vốn, vay thêm, hợp nhất). Khấu hao năm 2 bằng 0 vì đã khấu hao hết; tài sản vẫn dùng được nhưng giá trị sổ sách bằng 0, nên nếu bán thanh lý thì toàn bộ số thu ghi vào **lợi nhuận khác**.

## Khấu hao và hoạt động tài chính

- **Khấu hao không phải tiền mặt.** Là chi phí kế toán đưa vào để giảm lợi nhuận chịu thuế; doanh nghiệp vẫn giữ nguyên số tiền đó. Trong LCTT và trong định giá phải **cộng ngược lại**. Chủ doanh nghiệp muốn khấu hao **nhanh** để thuế thấp, cơ quan thuế có khung riêng để chặn — chỗ giằng co này cũng là chỗ dễ có thủ thuật.
- **Hết khấu hao là tin tốt cho cổ đông**: tài sản vẫn chạy nhưng hết chi phí khấu hao, lợi nhuận sau thuế tăng mà không cần bán thêm hàng. Khấu hao đều hàng năm thì trung tính. Dấu hiệu thủ thuật: **thời gian khấu hao thay đổi giữa các kỳ** — kiểm tra bằng tỷ lệ chi phí khấu hao / nguyên giá tài sản cố định theo chuỗi năm.
- **Trong chi phí tài chính phải tách hai thứ khác bản chất:** chi phí lãi vay gắn với kinh doanh chính và tạo đòn bẩy (cao chưa chắc xấu); lỗ đầu tư tài chính là ngoài ngành, không tạo đòn bẩy. **Quy tắc chẩn đoán: doanh thu ổn định mà lợi nhuận biến động mạnh thì nguyên nhân gần như chắc chắn nằm ngoài hoạt động kinh doanh chính** — mở dòng 6 và 7 ra kiểm tra.

| Tỷ lệ sở hữu | Phân loại | Ghi nhận ở đâu |
|---|---|---|
| Dưới 20% | Đầu tư tài chính | Lãi vào doanh thu tài chính, lỗ vào chi phí tài chính |
| 20%–50% | Công ty liên doanh liên kết | Dòng lãi/lỗ công ty liên doanh liên kết |
| Trên 50% | Công ty con | **Hợp nhất** toàn bộ, trừ ra phần cổ đông không kiểm soát |

## Bóc tách ROE

ROE = lợi nhuận sau thuế / vốn chủ sở hữu. Con số này một mình không nói được gì; bóc tách để biết nó tốt lên **nhờ cái gì**.

```
Dạng ba thành phần (chuẩn dùng):
ROE = (LNST / Doanh thu thuần) × (Doanh thu thuần / Tổng tài sản) × (Tổng tài sản / Vốn chủ sở hữu)
    =   Biên lợi nhuận ròng    ×      Vòng quay tài sản          ×      Đòn bẩy tài chính

Dạng năm thành phần (bản chi tiết, tách thêm thuế và lãi vay):
ROE = (LNST/LNTT) × (LNTT/EBIT) × (EBIT/Doanh thu) × (Doanh thu/Tài sản) × (Tài sản/VCSH)
      gánh thuế     gánh lãi vay    biên EBIT          vòng quay tài sản     đòn bẩy
```

Ba thành phần trả lời ba câu: **bán có lời không — tài sản có được khai thác không — có vay nợ không.** Ở dạng năm thành phần: gánh thuế đo khả năng quản lý thuế (ít biến động ở Việt Nam); gánh lãi vay đo phần lợi nhuận bị lãi vay ăn mất; biên EBIT đo **mô hình kinh doanh** — gộp cả vị thế cạnh tranh lẫn khả năng quản lý; vòng quay đo hiệu quả khai thác tài sản; đòn bẩy đo cấu trúc vốn. Nhân gánh lãi vay với đòn bẩy ra **đòn bẩy gộp**.

**Ví dụ tính đầu-cuối.** Doanh nghiệp giả định **DN-A**, đơn vị tỷ đồng, hai năm liền kề:

| Biến | Lấy ở đâu | Năm N−1 | Năm N |
|---|---|---|---|
| Doanh thu thuần | KQKD dòng 3 | 4.000 | 5.000 |
| EBIT = LNTT + chi phí lãi vay | KQKD dòng 15 + phần lãi vay tách từ dòng 7 | 350 | 560 |
| Lợi nhuận trước thuế | KQKD dòng 15 | 300 | 500 |
| LNST cổ đông công ty mẹ | KQKD dòng 20 | 240 | 400 |
| Tổng tài sản bình quân | Cân đối, dòng tổng tài sản, trung bình đầu kỳ và cuối kỳ | 3.500 | 4.000 |
| Vốn chủ sở hữu bình quân | Cân đối, dòng vốn chủ sở hữu, trung bình đầu kỳ và cuối kỳ | 1.750 | 1.600 |

**Năm N:** biên lợi nhuận ròng = 400 / 5.000 = **8,00%**; vòng quay tài sản = 5.000 / 4.000 = **1,25 lần**; đòn bẩy = 4.000 / 1.600 = **2,50 lần**. ROE = 0,0800 × 1,25 × 2,50 = **25,0%** — kiểm tra 400 / 1.600 = 25,0%, khớp. **Năm N−1:** biên = 240 / 4.000 = **6,00%**; vòng quay = 4.000 / 3.500 = **1,143 lần**; đòn bẩy = 3.500 / 1.750 = **2,00 lần**. ROE = 0,0600 × 1,143 × 2,00 = **13,7%**.

| Thành phần | N−1 | N | Mức tăng tương đối |
|---|---|---|---|
| Biên lợi nhuận ròng | 6,00% | 8,00% | ×1,333 |
| Vòng quay tài sản | 1,143 | 1,250 | ×1,094 |
| Đòn bẩy tài chính | 2,00 | 2,50 | ×1,250 |
| **ROE** | **13,7%** | **25,0%** | **×1,823** |

**Diễn giải.** Kiểm tra trước: 1,333 × 1,094 × 1,250 = 1,823, khớp mức tăng ROE. ROE gần gấp đôi, đóng góp lớn nhất là **biên lợi nhuận ròng** (×1,333) — mô hình kinh doanh và vị thế cạnh tranh cải thiện thật. Thứ hai là **đòn bẩy** (×1,250) — không phải năng lực kinh doanh mà là cấu trúc vốn, sẽ đảo chiều nếu lãi suất tăng. Vòng quay tăng nhẹ, cho thấy tài sản mới đưa vào là tài sản hoạt động chứ không nằm yên. Nếu thứ tự đảo lại — đòn bẩy tăng mạnh nhất, biên đi ngang — thì ROE cải thiện là do vay nợ, chất lượng thu nhập kém hơn hẳn. **Đối chiếu bằng dạng năm thành phần, năm N:** gánh thuế 400/500 = 0,800; gánh lãi vay 500/560 = 0,893; biên EBIT 560/5.000 = 11,20%; vòng quay 1,25; đòn bẩy 2,50. Tích = **25,0%**, khớp — đọc thêm được rằng thuế và lãi vay đang lấy đi 28,6% của EBIT, và mức cải thiện nằm ở biên EBIT chứ không ở gánh thuế. **ROA đối chiếu** = 400 / 4.000 = **10,0%**: ROA tăng cùng chiều ROE là bằng chứng doanh nghiệp tốt lên thật; ROE tăng mà ROA đứng yên thì toàn bộ mức tăng đến từ đòn bẩy.

## Đòn bẩy và tăng vốn

**Đòn bẩy.** Giữ nguyên toàn bộ kịch bản kinh doanh quán nước, chỉ đổi cơ cấu nguồn vốn: kịch bản 1 là 30 vốn chủ + 50 nợ; kịch bản 2 là 10 vốn chủ + 70 nợ. Tổng nguồn vốn vẫn 80, lãi vay 5 triệu thành 7 triệu.

- **Biên lợi nhuận gộp không đổi** — vị thế cạnh tranh không phụ thuộc cấu trúc vốn. **Lợi nhuận sau thuế giảm** ở kịch bản 2 vì lãi vay lớn hơn, nhưng **ROE tăng rõ rệt**.
- **ROA gần như không đổi** vì tổng tài sản không đổi. ROA không bị cơ cấu vốn tác động, **ROE thì có** — và ROE mới là chỉ số của cổ đông.
- **Điều kiện để đòn bẩy có lợi: ROA > lãi suất vay.** ROA càng cao thì vay càng nhiều càng lợi cho cổ đông. **ROA thấp mà vay nhiều thì đòn bẩy bào mòn giá trị cổ đông.** Áp vào DN-A: ROA 10,0%; lãi vay 60 trên dư nợ vay bình quân 800 ≈ lãi suất 7,5%; 10,0% > 7,5% nên đòn bẩy đang tạo giá trị — lãi suất thị trường lên trên 10% thì cùng cấu trúc vốn đó lập tức thành gánh nặng. Công thức DOL, DFL và cách ghép hai đòn bẩy với chu kỳ nằm ở `danh-muc-va-luan-chuyen.md`, mục *Hai đòn bẩy*.

**Tăng vốn.** Năm 2 quán nước làm hai việc: trả cổ tức bằng cổ phiếu tỷ lệ 1:10, và phát hành thêm 10.000 cp giá 35.000 đồng (mệnh giá 10.000). Số cổ phiếu: 3.000 ban đầu + 30.000 (cổ tức cổ phiếu) + 10.000 (phát hành) = **43.000 cổ**.

- **Cổ tức bằng cổ phiếu = vốn hoá lợi nhuận.** 3.000 × 10 × 10.000 = 300 triệu rời lợi nhuận giữ lại (343 triệu còn 43 triệu) và vào vốn góp. **Tổng vốn chủ không đổi, doanh nghiệp không nhận thêm đồng nào.**
- **Phát hành mới thu tiền thật:** 10.000 × 35.000 = 350 triệu, tách hai dòng — 100 triệu (mệnh giá) vào vốn góp, 250 triệu (phần vượt 25.000/cp) vào **thặng dư vốn cổ phần**. Vốn góp sau cùng 430 triệu (30 + 300 + 100), thặng dư 250 triệu, lợi nhuận giữ lại 43 triệu.

| Chỉ tiêu | Chuyện gì xảy ra |
|---|---|
| **EPS** | **Giảm** — lợi nhuận không đổi, mẫu số nhảy từ 3.000 lên 43.000 cổ. Đây là **pha loãng** |
| **Giá trị sổ sách/cp (BVPS)** | **Giảm** — vốn chủ tăng 350 triệu nhưng số cổ phiếu tăng hơn 14 lần |
| **Giá trị theo PE** | **Không đổi** — lợi nhuận không đổi |
| **Giá trị theo PB** | **Tăng** — vốn chủ tăng, dù chỉ có thêm tiền mặt nằm yên |

- **So sánh PE hay EPS giữa các năm phải điều chỉnh tác động tăng vốn**, nếu không sẽ kết luận sai. **Tăng vốn mà không đưa vào kinh doanh thì giá trị theo PB là ảo ảnh.**
- **Ngành có điều kiện về vốn** (ngân hàng, chứng khoán, bất động sản) mới có lợi thế thật khi tăng vốn, vì vốn vào thẳng hoạt động kinh doanh — ngân hàng cho vay, chứng khoán cấp margin. Lợi thế đó vẫn phụ thuộc thời điểm: công ty chứng khoán tăng vốn có lợi khi thị trường tốt (nhu cầu margin cao), vô nghĩa khi thị trường xấu. **Khi thị trường tốt thì doanh nghiệp nào cũng tranh thủ tăng vốn** — phân biệt tăng vốn có mục đích sử dụng rõ ràng với tăng vốn để tăng số.

## Bộ chỉ tiêu

Sáu nhóm chỉ tiêu các nhà cung cấp dữ liệu thường dựng sẵn. Mỗi nhóm là một **proxy** — không chỉ tiêu nào định nghĩa chính xác được khái niệm nó đại diện, nên dùng vài chỉ tiêu cùng lúc.

| Nhóm | Câu hỏi nhóm đó trả lời | Chỉ tiêu thông dụng |
|---|---|---|
| **Hiệu quả sử dụng tài sản** | Tài sản tăng thì doanh thu có tăng tương ứng không | Doanh thu/tổng tài sản; doanh thu/tài sản cố định |
| **Khả năng sinh lời** | Lợi nhuận có gắn với doanh thu và quy mô tài sản không | Biên gộp; biên EBIT; ROA; ROE |
| **Khả năng cạnh tranh** | Vị thế trong ngành, sức mặc cả và sức định giá đầu ra | Biên lợi nhuận gộp so cùng ngành theo chuỗi năm |
| **Hiệu quả đòn bẩy** | Vay nợ tăng thì lợi nhuận có tăng tương ứng không | Nợ/vốn chủ; tài sản/vốn chủ; chi phí lãi vay/dư nợ; đối chiếu ROA với lãi suất vay |
| **Hiệu quả quản lý** | Chi phí hoạt động so doanh thu, có tiết kiệm được không | (Chi phí bán hàng + chi phí quản lý)/doanh thu thuần |
| **An toàn hoạt động** | Có trả được nợ ngắn hạn không | Current ratio; quick ratio; tài sản ngắn hạn/tổng nợ |

Nhóm thứ bảy — **định giá thị trường** (PE, PB) — không đo chất lượng doanh nghiệp mà đo mức giá thị trường đang trả; xem `dinh-gia.md`.

- **Nhà đầu tư cá nhân chỉ cần hai câu:** có tạo lợi nhuận cho cổ đông không, và việc đó có ổn định không. **Đọc theo chuỗi năm, so sánh trong cùng nhóm ngành, không so tuyệt đối** — cùng một chỉ tiêu, năm cao năm thấp thất thường là rủi ro, đều đặn là an toàn. Chấm điểm từng chỉ tiêu rồi tổng hợp là cách phổ biến, nhưng con số tổng hợp chỉ là trung bình cộng các góc nhìn riêng lẻ.
- **Phân tích chất lượng doanh nghiệp không ra được quyết định đầu tư**, nó chỉ phân loại tốt/xấu. Doanh nghiệp tốt có thể đã đắt, hoặc có thể không ai quan tâm. Giá trị thật nằm ở hai chỗ: chọn cổ phiếu nắm dài hạn ở vùng giá thấp, và nhận diện nhóm thất thường. **Riêng nhóm an toàn hoạt động phục vụ người cho vay, không phải nhà đầu tư** — người cho vay nhìn khả năng trả nợ, nhà đầu tư nhìn khả năng sinh lời; doanh nghiệp chưa có lợi nhuận nhưng trả được nợ thì ngân hàng vẫn cho vay, không có nghĩa đó là khoản đầu tư tốt.

## Thủ thuật

Mọi thủ thuật cuối cùng đều tác động vào lợi nhuận, qua doanh thu hoặc qua chi phí. Bốn nhóm:

**1. Tác động vào doanh thu.** Dấu hiệu chính: **doanh thu tăng mạnh và khoản phải thu tăng theo** — ghi nhận doanh thu sớm để kéo lợi nhuận về trước. Phân biệt: doanh thu tăng mà phải thu **không** tăng tương ứng thì nhiều khả năng là thật. Biến thể: bán hàng kèm thoả thuận mua lại; hạch toán doanh thu lệch kỳ; đẩy giá bán lên để giá vốn thấp đi tương đối, biên gộp phồng lên. Kiểm chứng: rà lịch sử khoản giảm trừ doanh thu (hàng trả lại nhiều ở kỳ sau là dấu vết của kỳ trước) và tỷ trọng chi phí bán hàng, chi phí quản lý trên doanh thu. **Hệ quả bắt buộc: đã ghi sớm thì kỳ sau phải trả lại — doanh thu thấp hơn, giá vốn cao hơn. Một quý đột biến gần như luôn kéo theo một quý hụt.**

**2. Tác động vào chi phí.** Dấu hiệu: chi phí biến động khác thường so với doanh thu. **Đổi thời gian khấu hao** — kéo từ 2 năm lên 5 năm thì chi phí mỗi năm nhỏ đi, lợi nhuận đẹp lên; năm sau rút về 3 năm thì dồn chi phí; kiểm tra bằng tỷ lệ khấu hao/nguyên giá theo chuỗi năm. **Điều chỉnh dự phòng giảm giá hàng tồn kho** — có doanh nghiệp trích rất thận trọng khi thị trường xấu, làm báo cáo xấu hẳn đi, rồi hoàn nhập ở chu kỳ sau để lợi nhuận bật lên; kiểm tra bằng tỷ lệ dự phòng/giá trị tồn kho theo chuỗi năm. Ngoài ra là **đẩy chi phí sang kỳ khác**.

**3. Tác động vào cả doanh thu, chi phí và lợi nhuận** — qua **thay đổi tỷ lệ sở hữu**: đưa một công ty từ liên kết lên công ty con để hợp nhất (tài sản và doanh thu nhảy vọt), hoặc bán bớt vài phần trăm để rơi xuống dưới 50% và thoát hợp nhất. **"Niêm yết ngược"** là dạng cực đoan: thâu tóm một công ty nhỏ đang niêm yết rồi đổ tài sản vào qua hợp nhất hoặc mua bán tài sản. Biến thể: nắm khoản đầu tư vào công ty mà mình chi phối được giá, đến kỳ báo cáo thì đẩy giá lên và hạch toán phần lãi. **Doanh nghiệp có nhiều công ty sở hữu chéo trên sàn là nhóm dễ làm việc này nhất.**

**4. Tác động trực tiếp vào lợi nhuận** — qua **thu nhập khác**: bán tài sản đã khấu hao hết (giá trị sổ sách bằng 0) thì toàn bộ số thu ghi thẳng vào lợi nhuận; biến thể phổ biến là bán rồi thuê lại chính tài sản đó. Kiểm tra bằng cách so dòng 15 với dòng 11.

**Cách dùng.** **Khi nhìn thấy thì việc đã xong** — giá trị của việc phát hiện nằm ở chỗ hiểu lợi nhuận đến từ đâu, và ở chỗ **doanh nghiệp từng làm trò thì nhiều khả năng còn làm tiếp**. **Không cần thạo kế toán**, chỉ cần thấy bất thường là đã có tín hiệu; người làm thủ thuật giỏi thì hầu như không phát hiện được trước. **Nhóm có thủ thuật biến động mạnh: ngắn hạn là cơ hội, dài hạn không giải ngân được.** Muốn nắm giữ dài hạn thì chọn doanh nghiệp nghiêm túc — **doanh nghiệp tốt và cổ phiếu tốt là hai chuyện khác nhau.** Cuối cùng, **kiểm tra rủi ro huỷ niêm yết** trước khi coi một cổ phiếu giá thấp là cơ hội; vi phạm bất kỳ điều nào thì bỏ qua, bất kể rẻ tới đâu — ba điều dưới theo quy định niêm yết đang áp dụng, quy định đổi thì tra lại danh sách, cách dùng không đổi: (1) ba năm gần nhất có lỗ liên tiếp không; (2) lỗ luỹ kế có vượt vốn góp thực góp của chủ sở hữu không; (3) vốn chủ sở hữu có âm trong báo cáo tài chính kiểm toán không.

## Key driver

Mỗi ngành chỉ có một vài biến số thật sự chi phối. Đọc hết mọi chỉ tiêu chỉ làm rối. Nhận diện key driver rồi mới biết doanh nghiệp đang ở **đoạn nào của chu kỳ**, chứ không chỉ biết tốt hay xấu. Năm ngành dưới là ví dụ cách nhận diện, không phải danh sách đóng: với ngành khác, key driver là biến số mà lợi nhuận của cả ngành cùng biến động theo.

| Ngành | Key driver | Vì sao |
|---|---|---|
| **Ngân hàng** | Tăng trưởng tín dụng và **NIM**; sâu hơn là **duration** | NIM giữa các ngân hàng khá ổn định nên lãi suất ít tác động trực tiếp; cái quyết định là dư nợ. Duration — chênh lệch kỳ hạn giữa vốn huy động và tài sản cho vay/trái phiếu — cho biết chịu được cú sốc lãi suất tới đâu |
| **Chứng khoán** | **Đòn bẩy hoạt động** (tỷ trọng chi phí cố định) | Chi phí cố định cao thì thị trường xấu lỗ nặng hơn, thị trường tốt lãi mạnh hơn |
| **Bất động sản** | **Đòn bẩy tài chính** | Thâm dụng vốn vay, nhạy trực tiếp với lãi suất |
| **Bảo hiểm** | **Duration** và tình trạng nền kinh tế | Tài sản phần lớn là trái phiếu và tài sản thu nhập cố định; lãi suất tăng kéo dài làm giá trị các tài sản đó giảm |
| **Sản xuất, vật liệu** | Biên lợi nhuận gộp và tồn kho | Chu kỳ giá đầu ra quyết định; tồn kho giá thấp gặp giá bán lên là cơ hội |

## Số liệu lấy ở đâu

| Chỉ tiêu | Báo cáo | Dòng cụ thể |
|---|---|---|
| Doanh thu thuần; giá vốn; lợi nhuận gộp; lợi nhuận trước thuế; LNST cổ đông công ty mẹ; EPS | KQKD | Dòng 3; 4; 5; 15; 20; 21 |
| Chi phí lãi vay; EBIT | KQKD / thuyết minh | Lãi vay tách từ dòng 7 (chi phí tài chính); EBIT = dòng 15 + chi phí lãi vay |
| Tổng tài sản; vốn chủ sở hữu | Cân đối | Dòng tổng cộng của mỗi phần |
| Tiền và tương đương tiền; phải thu ngắn hạn; hàng tồn kho; tài sản cố định (nguyên giá, hao mòn luỹ kế); nợ vay ngắn hạn và dài hạn | Cân đối + thuyết minh | Theo thứ tự: tài sản ngắn hạn (đối chiếu tiền với tiền cuối kỳ ở LCTT); tài sản dài hạn; nợ phải trả |
| Vốn góp chủ sở hữu (chia 10.000 ra số cổ phiếu); thặng dư vốn cổ phần; lợi nhuận chưa phân phối | Cân đối | Trong vốn chủ sở hữu |
| Khấu hao trong kỳ; thay đổi phải thu, tồn kho, phải trả; lưu chuyển tiền thuần từ HĐKD | LCTT | Phần I — hoạt động kinh doanh |
| Chi mua sắm tài sản cố định (capex); tiền vay, trả nợ gốc, cổ tức đã trả | LCTT | Phần II — đầu tư; phần III — tài chính |
| Thời gian khấu hao và chính sách kế toán; dự phòng giảm giá tồn kho và phải thu khó đòi; tỷ lệ sở hữu công ty con và liên kết | Thuyết minh | Phần chính sách kế toán; chi tiết khoản mục; danh sách công ty con và liên kết |

## Giới hạn

- **BCTC luôn chậm.** Công bố sau khi kỳ đã kết thúc, thường chậm thêm nữa. Dùng để **hiểu loại doanh nghiệp**, không dùng để dự đoán giá ngắn hạn. **Chỉ một đẳng thức đúng tuyệt đối** — mọi chỉ tiêu còn lại = phần thực tế + sai số + phần muốn nó thế nào. Sai số có hai loại: khách quan (thông lệ kế toán cho phép nhiều lựa chọn) và chủ quan.
- **Giá cổ phiếu không do BCTC quyết định.** Thứ tự ảnh hưởng: nguồn tiền (chính sách tiền tệ) → định giá doanh nghiệp → tâm lý và dòng tiền. BCTC chỉ nuôi mắt xích thứ hai. **Chuẩn mực kế toán và suy nghĩ nhà đầu tư là hai phạm trù khác nhau.** Doanh nghiệp rất đẹp trên báo cáo nhưng nhà đầu tư không thích thì vẫn bị định giá thấp, vì mức rủi ro yêu cầu cao hơn. **Mỗi chỉ tiêu chỉ là một khía cạnh** — không con số tổng hợp nào đo được toàn bộ chất lượng doanh nghiệp.
- **Số liệu kế toán trả lời "họ đã như thế nào", không trả lời "họ sẽ như thế nào".** Giá trị của nó là giả định quá khứ tiếp diễn — ít biến động thì giả định đó đáng tin hơn. Trong đầu tư, thứ chuyển động giá là **câu chuyện**, không phải con số kế toán; người cần huy động vốn luôn kể chuyện hay.

## Phụ lục A ngân hàng

Ngân hàng kinh doanh bằng tiền, nên khái niệm "có lợi nhuận mà không có tiền" không áp dụng được. **Bảng cân đối** không chia ngắn hạn/dài hạn mà xếp theo hạng mục nghiệp vụ.

| Phía tài sản | Đọc thế nào |
|---|---|
| Tiền mặt tại quỹ; tiền gửi tại NHNN; tiền gửi và cho vay TCTD khác | Ba khoản cộng lại là **dự trữ của ngân hàng**. Tiền gửi tại NHNN là dự trữ bắt buộc (có thể thừa/thiếu); khoản cho vay TCTD khác có dự phòng đi kèm nên giảm trừ khi tính |
| Chứng khoán kinh doanh | Ngắn hạn, tỷ trọng nhỏ |
| **Cho vay khách hàng** | **Hạng mục lớn nhất.** So dư nợ giữa hai thời điểm ra **tăng trưởng tín dụng** |
| Dự phòng rủi ro cho vay | Chia cho dư nợ ra **tỷ lệ dự phòng trên dư nợ** — thước đo chất lượng tín dụng |
| Chứng khoán đầu tư | Chia sẵn sàng để bán và giữ đến ngày đáo hạn, kèm dự phòng riêng |

Phía nguồn vốn: **tiền gửi của khách hàng** là hạng mục lớn nhất; **nợ Chính phủ và NHNN** phản ánh vay NHNN qua chiết khấu, tái chiết khấu — khoản này tăng nghĩa là đang phải vay để tạo thanh khoản; tiền gửi và vay TCTD khác đối ứng hạng mục tương ứng phía tài sản. **Quan hệ cần theo dõi: tín dụng tăng nhanh trong khi tiền gửi tăng chậm hoặc giảm thì ngân hàng phải bù bằng vay NHNN và vay liên ngân hàng.**

```
Thu nhập lãi và các khoản tương tự − Chi phí lãi = Thu nhập lãi thuần   ← tương đương lợi nhuận gộp
Thu nhập dịch vụ − Chi phí dịch vụ = Lãi/lỗ thuần từ dịch vụ
± Lãi/lỗ ngoại hối, vàng, mua bán chứng khoán đầu tư                     ← tương đương hoạt động tài chính
− Chi phí hoạt động (gộp cả bán hàng và quản lý)
− Chi phí dự phòng rủi ro tín dụng
= Lợi nhuận trước thuế
```

- Lợi nhuận đến từ **cho vay** và **dịch vụ**, cho vay chiếm phần lớn; thu nhập dịch vụ bám sát hoạt động cho vay và rất ổn định, nên **tập trung vào tín dụng là đủ**. **Biến số cốt lõi là tăng trưởng tín dụng**, bị chi phối bởi chính sách tiền tệ và hạn mức tín dụng được phân bổ. **Phân tích tăng giảm thu nhập lãi thuần mà tách rời NIM là vô nghĩa** — NIM = chênh lệch lãi suất cho vay và lãi suất huy động, khá ổn định giữa các ngân hàng; ước lượng thô: NIM × tăng trưởng tín dụng.
- **Chi phí dự phòng rủi ro tín dụng là chỗ phân biệt các ngân hàng.** Lấy chi phí dự phòng chia thu nhập từ hoạt động kinh doanh trước dự phòng: dưới 10% và ổn định là chất lượng tín dụng tốt; tới khoảng một nửa là kém hơn hẳn. Hai mốc này để so giữa các ngân hàng trong cùng kỳ, không phải chuẩn cố định. Đây là chỉ tiêu tách biệt rõ nhất hai ngân hàng có bảng cân đối trông giống hệt nhau. **Nhiều tài sản cũng chưa chắc sinh lời cao:** cho vay chiếm tỷ trọng thấp trong tổng tài sản thì ROA thấp hơn ngân hàng cho vay mạnh — ổn định và sinh lời là hai khía cạnh khác nhau.
- **LCTT ít ý nghĩa với ngân hàng:** hoạt động kinh doanh và tài chính gắn liền nhau, hoạt động đầu tư rất nhỏ, tiền cuối kỳ phụ thuộc nặng vào tiền đầu kỳ. Chỉ số dùng: EPS, BVPS, PE, PB, ROA, ROE, NIM, tỷ lệ dự phòng/dư nợ. **Không dùng phương pháp dòng tiền.**

## Phụ lục B chứng khoán

Mô hình ba mảng: **tự doanh, cho vay margin, môi giới** — cả ba đều phụ thuộc trạng thái thị trường. **Bảng cân đối** gần giống doanh nghiệp sản xuất; tài sản dài hạn hầu như không đáng kể vì hoạt động kinh doanh nằm ở tài sản ngắn hạn.

| Hạng mục (tài sản ngắn hạn) | Mảng | Đọc thế nào |
|---|---|---|
| **Tài sản tài chính ghi nhận qua lãi/lỗ (FVTPL)** | Tự doanh | Tăng nghĩa là đã mua vào và đang nắm nhiều chứng khoán |
| **Đầu tư nắm giữ đến ngày đáo hạn (HTM)** | Đầu tư trái phiếu | Thu nhập chắc chắn hơn, chảy đều |
| **Các khoản cho vay** | Margin | Cho vay tăng trong khi HTM giảm nghĩa là đang dịch vốn sang margin |

Kèm **dự phòng** cho khoản cho vay margin và các khoản phải thu. Phía nợ: các khoản vay và nợ thuê tài chính — vay từ ngân hàng và từ chính khách hàng để cấp margin, đối ứng ba hạng mục tài sản trên.

**Kết quả kinh doanh — bốn dòng cần đọc:** lãi/lỗ từ tài sản tài chính ghi nhận qua lãi/lỗ (tự doanh, chỉ ghi nhận **khi bán**); thu nhập lãi từ khoản đầu tư nắm giữ đến ngày đáo hạn (trái phiếu); lãi từ các khoản cho vay và phải thu (margin); doanh thu môi giới. **Chi phí môi giới** là hoa hồng trả cho môi giới, theo thông lệ chiếm khoảng 60–70% doanh thu môi giới. Các mảng còn lại (phí uỷ thác, bảo lãnh phát hành) đều nhỏ.

**Chỉ đọc ba mảng chính**, bỏ qua phần còn lại. **Câu hỏi không phải "tăng hay giảm" mà là "ổn định hay không ổn định"**, và luôn so với một công ty chứng khoán khác — phân tích tăng giảm đơn thuần dễ sai vì cả ba mảng đều bám theo trạng thái thị trường. Mảng tự doanh phụ thuộc **năng lực công ty**; mảng margin vận hành giống hoạt động ngân hàng, đọc như đọc tín dụng. Chỉ số dùng: EPS, BVPS, PE, PB, ROA, ROE.

## Phụ lục C bảo hiểm

Mô hình: **thu phí bảo hiểm rồi đem đầu tư**; hoạt động đầu tư là phụ, không phải hoạt động chính. Hai loại hình: nhân thọ và phi nhân thọ. **Bảng cân đối** có hai đặc điểm chi phối toàn bộ cách đọc: **phía tài sản, phần lớn là trái phiếu** — đầu tư tài chính ngắn hạn và dài hạn đều chủ yếu là khoản nắm giữ đến ngày đáo hạn, nhiều nhất là trái phiếu Chính phủ; về hình thức có thể bán ngay, nhưng bản chất mô hình là nắm tới đáo hạn. **Phía nợ, lớn nhất là dự phòng nghiệp vụ** (dự phòng toán học) — khoản ước lượng để sẵn sàng chi trả bồi thường; ngoài ra có giao dịch mua bán lại trái phiếu Chính phủ, tương tự repo trong ngân hàng.

```
Phí bảo hiểm gộp − Phí nhượng tái bảo hiểm = Doanh thu thuần phí bảo hiểm   ← chỉ tiêu cốt lõi
− Chi phí bồi thường                                                        ← khoản chi phí lớn nhất
+ Doanh thu hoạt động tài chính                                             ← lãi từ danh mục trái phiếu
```

- Nhượng tái bảo hiểm là việc nhượng lại một phần hợp đồng cho công ty bảo hiểm khác — chuyện thường xuyên trong ngành. **Chỉ tiêu cốt lõi là doanh thu thuần phí bảo hiểm**, không phải doanh thu gộp. **Biến số quyết định là tình trạng nền kinh tế**, không phải biến động doanh thu từng quý: dân có thu nhập cao mới nghĩ tới bảo hiểm, giai đoạn khó khăn thì không.
- **Cảnh báo về lãi suất.** Suy luận phổ biến "lãi suất tăng thì bảo hiểm hưởng lợi vì thu tiền trước đem gửi" sai ở trường hợp chung: tài sản phần lớn là trái phiếu, lãi suất tăng thì đánh giá lại các khoản đó giảm giá trị, trung hoà mất phần lợi từ tái đầu tư — mà doanh nghiệp lại phải nắm giữ nên không bán ra để hiện thực hoá lãi/lỗ. **Vị trí trong chu kỳ:** ngành phòng thủ, chạy cuối chu kỳ — sau khi các ngành khác đã tăng, và **trước** khi lãi suất tăng để chống lạm phát. Khi lãi suất đã tăng và thị trường bắt đầu nói nhiều về bảo hiểm thì đó là lúc nghĩ tới bán.

## Đối chiếu chỉ tiêu

Bốn nhóm báo cáo phản ánh cùng bộ chỉ tiêu, chỉ khác tên gọi. Dùng cột phi tài chính làm mốc để dịch ngang.

| Ý nghĩa | Phi tài chính | Ngân hàng | Chứng khoán | Bảo hiểm |
|---|---|---|---|---|
| **Doanh thu** | Doanh thu thuần (dòng 3) | Thu nhập lãi + thu nhập dịch vụ | Tổng doanh thu hoạt động (cộng các mảng) | Doanh thu thuần phí bảo hiểm |
| **Giá vốn** | Giá vốn hàng bán (dòng 4) | Chi phí lãi + chi phí dịch vụ | Tổng chi phí hoạt động | Tổng chi phí kinh doanh bảo hiểm (chủ yếu chi bồi thường) |
| **Vị thế cạnh tranh** (và biên của nó) | Lợi nhuận gộp (dòng 5) → biên lợi nhuận gộp | Thu nhập lãi thuần → **NIM** | Lợi nhuận gộp HĐKD → biên gộp từng mảng | Lợi nhuận gộp kinh doanh bảo hiểm → biên gộp phí |
| **Hoạt động tài chính** | Dòng 6, 7 | Lãi/lỗ ngoại hối, vàng, chứng khoán đầu tư | Doanh thu tài chính khác | Doanh thu tài chính (danh mục trái phiếu) |
| **Chi phí quản trị và khả năng quản trị** | Chi phí bán hàng + quản lý (dòng 9, 10) → lợi nhuận thuần HĐKD (dòng 11) | Chi phí hoạt động (gộp cả hai) → lợi nhuận thuần trước dự phòng | Chi phí quản lý công ty chứng khoán → lợi nhuận thuần HĐKD | Chi phí bán hàng + quản lý → lợi nhuận thuần HĐKD |
| **Rủi ro đặc thù** | Dự phòng giảm giá tồn kho, phải thu khó đòi | Chi phí dự phòng rủi ro tín dụng | Dự phòng cho vay margin và phải thu | Dự phòng nghiệp vụ (toán học) |
| **Tài sản sinh lời chính / nguồn vốn đặc thù** | Tài sản cố định + tồn kho / nợ vay + phải trả người bán | Cho vay khách hàng / tiền gửi khách hàng | FVTPL + HTM + margin / vay ngân hàng và vay khách hàng | Danh mục trái phiếu / dự phòng nghiệp vụ |

**Vì sao nhóm tài chính đọc khác nhóm sản xuất:**

- **Nhóm tài chính kinh doanh bằng chính tiền.** Với doanh nghiệp sản xuất, tiền là kết quả của việc bán hàng; với ngân hàng, tiền là hàng hoá — vừa là nguyên liệu, vừa là sản phẩm, vừa là tài sản. **Vì vậy phương pháp định giá theo dòng tiền gần như không áp dụng được** (không tách được đâu là dòng tiền hoạt động, đâu là dòng tiền tài trợ); với nhóm tài chính, ưu tiên PE và PB. Cùng lý do đó, **câu hỏi "lợi nhuận có gắn với tiền không" mất ý nghĩa** — ngân hàng có tiền hay thiếu tiền phụ thuộc chủ yếu vào số dư đầu kỳ và trạng thái thanh khoản.
- **Nguồn vốn của nhóm tài chính là nghiệp vụ, không phải tài trợ.** Tiền gửi khách hàng, dự phòng nghiệp vụ, tiền vay để cấp margin là đầu vào kinh doanh, không phải "vay nợ" theo nghĩa đòn bẩy; áp tỷ lệ nợ/vốn chủ của doanh nghiệp sản xuất vào ngân hàng sẽ ra kết luận vô nghĩa. **Rủi ro cũng nằm ở khoản dự phòng, không ở hàng tồn kho** — chất lượng tài sản nhóm tài chính nhìn ở tỷ lệ dự phòng rủi ro tín dụng, dự phòng margin, dự phòng nghiệp vụ.
- **Tài sản nhóm tài chính nhạy trực tiếp với lãi suất** vì danh mục trái phiếu được đánh giá lại — lý do duration là key driver của ngân hàng và bảo hiểm, còn với doanh nghiệp sản xuất thì lãi suất chỉ tác động qua chi phí lãi vay. **Và phải đọc theo so sánh trong cùng nhóm**: đọc một ngân hàng đơn lẻ hầu như không kết luận được gì; đặt cạnh một ngân hàng khác thì khác biệt về chất lượng tín dụng và NIM hiện ra ngay.

---
