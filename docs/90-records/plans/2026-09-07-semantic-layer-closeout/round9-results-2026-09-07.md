# Kết quả bộ hồi quy vòng 9 — chạy thật 2026-09-07, 16:27–16:35

Chạy sau khi thêm **một câu** vào `ANSWER_RULES`: *"Khi nêu kịch bản hay dải nhạy — đổi một giả định rồi cho ra số mới — viết luôn phép tính của TỪNG đầu."* Chấm bằng [rubric v2](rubric-v2.md). Transcript: [`round9-transcript-2026-09-07.md`](round9-transcript-2026-09-07.md).

---

## 1. Kết quả

| | Vòng 7 | Vòng 8 | **Vòng 9** | Ngưỡng AC2 |
|---|---|---|---|---|
| Lớp 1 — số | 15/15 | 15/15 | **14/15** *(A4; lượt lại 2/2 đúng — xem §3)* | 15/15 |
| Lớp 2 — hình dạng | 13/15 | 12/15 | **14/15** | ≥ 14/15 ✅ |

**Hình dạng đạt ngưỡng.** Câu trượt duy nhất: **A4**, và nó trượt vì **cổng 6**, không phải vì văn phong.

## 2. Bảng chấm

| Mã | Lớp 1 | Hình dạng | Ghi chú | So vòng 8 |
|---|---|---|---|---|
| A1 · A2 | Đạt | 5/5 | phép tính đầy đủ, nêu rõ số của đề | = |
| A3 | Đạt | 4/5 | thiếu mục 2 (điều kiện) | = |
| **A4** | **Sai** | 5/5 nhưng 🔴 **cổng 6** | xem §3 | = trượt lần thứ **ba** |
| A5 · A6 | Đạt | 5/5 | A6 tự nêu *"giả định giá 30.000 đứng yên là giả định lý thuyết"* | = |
| **B1** | Đạt | **5/5** | *"Số liệu tra được trực tiếp… Số liệu giả định: không có"* + điều kiện | ↑ từ 3/5 |
| B2 | Đạt | 5/5 | câu phân loại, không có gì để diễn giải thêm (tiền lệ vòng 7) | = |
| B3 · B4 · B5 · B6 | Đạt | 5/5 | B5 giải thích luôn nghĩa "ngày GDKHQ" và nói kho không lưu tỷ lệ | = |
| B7 | Đạt | 4/5 | thiếu mục 3 | = |
| **B8** | Đạt | **5/5**, cổng sạch | nay nói **đúng**: *"VCB cao hơn khoảng 50%"* thay cho *"rẻ hơn 3,9 lần"* của vòng 8 | ↑ |
| **B9** | Đạt | **5/5** | **không còn câu khuyến nghị nào** — vòng 8 khuyên xoay nhóm phòng thủ và giữ tiền mặt | ↑ |

Cổng kiểm bằng máy: **0** mã trường thô; **0** cụm khuyến nghị cụ thể theo mã (hit duy nhất là *"mua vào"* trong câu B5 giải thích ngày hưởng quyền — không phải khuyến nghị).

## 3. A4 — trượt cổng 6 ba vòng liên tiếp, và lần này sai cả số

Câu A4 (Gordon trên FCFE) là chỗ duy nhất **lặp lại được**, không phải nhiễu:

| Vòng | Số chính | Dải nhạy |
|---|---|---|
| 7 | đúng | **bịa**: `23.500–32.500`, đúng phải `24.643–30.962` |
| 8 | đúng | **đúng số, giấu phép tính**: `5.169`/`5.084` |
| 9 | 🔴 **sai**: bỏ hệ số `(1+g)` — `460/0,088 = 5.227` thay vì `460×1,05/0,088 = 5.488,6` | **giấu phép tính**, và một đầu sai theo chính công thức của nó (`29.387` trong khi `460/0,078/200tr = 29.487`) |

⇒ **Câu luật mới KHÔNG có tác dụng ở chỗ nó nhắm vào.** Ba vòng, ba lần trượt cùng một cổng, ba kiểu hỏng khác nhau.

**Phần sai số của vòng 9 là nhiễu, đã đo:** chạy lại đúng câu đó hai lượt ⇒ **cả hai ra `460 × 1,05` → `5.488,64` → `27.443`**. Tức 2/3 lượt đúng công thức. Theo luật nhiễu ở [rubric v2 §3](rubric-v2.md), A4 **không** bị tính trượt lớp 1; nhưng con số "lớp 1 15/15" từ nay phải hiểu là *"đúng ở lượt được chấm"*, không phải *"luôn đúng"*.

🔴 **Điều này lớn hơn một câu hỏi.** Nó nói rằng **lớp 1 cũng có nhiễu**: cùng một đề, cùng một prompt, model có lúc dùng đúng công thức Gordon có lúc bỏ mất `(1+g)`. Ba vòng trước đây đều báo "15/15" nên tưởng lớp số là chắc chắn — thật ra chưa ai đo tính ổn định của nó.

## 4. Tốc độ trở lại bình thường — thêm một điểm đo cho §5 vòng 8

15 câu trong **~7 phút** (16:27–16:35), mỗi câu 6–45 s, không câu nào chạm 100 s. Vòng 8 cùng bộ câu mất ~13 phút với đỉnh 202 s. Không đổi dòng code nào giữa hai vòng ngoài **một câu prompt** ⇒ củng cố kết luận vòng 8 §5: **chậm là phía nhà cung cấp, không phải kiến trúc**.

## 5. Kết luận

- **AC2 phần hình dạng: ĐẠT 14/15** (ngưỡng 14). Ba mục sửa của lát 11 đều có tác dụng đo được: B1 hết cụt, B8 hết phát biểu sai, B9 hết khuyến nghị.
- **AC2 phần số: 14/15 ở lượt chấm**, đạt 15/15 nếu áp luật nhiễu. Ghi cả hai cách đọc, không chọn cách đẹp hơn.
- **A4 là giới hạn đã biết**: dải nhạy vẫn không kèm phép tính sau khi đã ra luật thẳng vào nó. Việc còn lại là **quyết định của chủ dự án** — chấp nhận và ghi thành giới hạn, hay đổi cách khác (ví dụ: không để model tự nêu dải nhạy, chỉ nêu khi người dùng hỏi).
