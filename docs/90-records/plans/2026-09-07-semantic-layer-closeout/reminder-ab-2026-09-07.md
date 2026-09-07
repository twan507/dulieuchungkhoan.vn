# Lượt A/B `REMINDER` — nợ #3 lát 10, đo 2026-09-07 16:53–17:00

`REMINDER` là khối chữ ~215 token chèn kèm **mọi** kết quả công cụ (`chat.py:91`). Lát 10 chạy 100% lượt **có** nhắc nên không có đối chứng — đây là lượt đối chứng đó.

**Cách đo:** tắt bằng cách sửa tạm `chat.py:91` (không commit, đã `git checkout` hoàn nguyên và kiểm `git status` sạch), rồi chạy **đúng 15 câu** như vòng 9, cùng cách chạy một tiến trình mỗi câu.

---

## 1. Kết quả

| | Vòng 9 (**có** nhắc) | Lượt này (**không** nhắc) |
|---|---|---|
| Lớp 1 — số | **14/15** *(A4 nhiễu, 2/2 lượt lại đúng)* | **14/15** *(B7 sai thật)* |
| Mã trường thô lọt ra | 0 | **0** |
| Khuyến nghị cụ thể theo mã | 0 | **0** |

**Hoà về số.** Hai câu hỏng là hai câu khác nhau, và cả hai nằm trong dải nhiễu đã đo.

## 2. Hai khác biệt về chất, không phải về điểm

**B7 sai thật khi không có nhắc.** Trả `TIN · CTG · VCB` thay vì `TIN · HDB · LPB` — tức đọc bảng screener ra thứ hạng khác. Vòng 9 có nhắc thì đúng. Một lần, chưa đủ kết luận.

**A3 chuyển sang viết LaTeX khi không có nhắc.** Nguyên văn: `\[ K_E = 5\% + 1{,}1 \times 8\% = 13{,}8\% \]`. Nội dung đúng, đủ bước, nhưng trong terminal thì đó là chữ thô khó đọc. Vòng 9 (có nhắc) viết bằng chữ thường. `REMINDER` có câu *"trả lời tiếp theo đúng hình dạng đã định"* — đây có thể là chỗ nó neo hình dạng, cũng có thể chỉ là nhiễu.

🔴 **Và nó lộ một lỗi của bộ chấm:** script `grade_l1.py` tìm chuỗi `13,8` nên **không thấy** `13{,}8` của LaTeX ⇒ báo A3 trượt trong khi model trả lời đúng. Bộ chấm máy chỉ bắt được đúng một cách viết số; mọi lần chấm sau phải đọc bằng mắt các ca "trượt" trước khi tin.

## 3. Kết luận: GIỮ `REMINDER`

Ba lý do, xếp theo sức nặng:

1. **Không có bằng chứng bỏ đi thì tốt hơn.** Hoà về số, và hai khác biệt về chất đều nghiêng về phía *có* nhắc.
2. **Chi phí nhỏ.** ~215 token mỗi lượt gọi công cụ, trên nền ~13.500 token vào mỗi request — dưới 2%.
3. **Phép đo này yếu.** Một lượt mỗi nhánh, mà [nhiễu đã đo](round8-results-2026-09-07.md) đủ sức lật một câu. Muốn kết luận chắc thì phải chạy nhiều lượt mỗi nhánh — không đáng tiền cho một khối 215 token.

**Điều kiện đảo ngược:** nếu sau này chi phí token thành ràng buộc thật, chạy lại A/B với **3 lượt mỗi nhánh** rồi hãy quyết; đừng bỏ dựa trên lượt đo đơn này.
