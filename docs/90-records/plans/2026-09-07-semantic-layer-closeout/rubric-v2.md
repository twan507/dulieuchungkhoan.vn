# Rubric v2 — thước chấm hình dạng, từ vòng 9

Thay cho phần *"Chấm → Lớp 2"* của [`regression-round7.md`](../2026-09-07-semantic-layer/regression-round7.md). **Bộ 15 câu và đáp án giữ nguyên**, chỉ thước đo đổi. File cũ **không sửa** — nó là bản ghi tại-thời-điểm của vòng 7 (§1.7).

Ba thứ được sửa, đều là lỗi lộ ra khi chấm vòng 8 ([kết quả](round8-results-2026-09-07.md) §4, §5b).

---

## 1. Cách tính điểm — hết mâu thuẫn

Bản cũ viết *"chấm 5 mục, đạt khi ≥ 4/5"* nhưng bảng có **6 dòng**, trong đó dòng 5 và 6 đều gắn nhãn *(cổng)*. Vòng 7 chấm B5 là **3/5** ⇒ thực tế đã chấm **mục 1–5 tính điểm, mục 6 là cổng**. Nay ghi thẳng ra:

| # | Mục | Vai | Đạt khi |
|---|---|---|---|
| 1 | Trình bày đúng loại câu | **tính điểm** | **Nhóm A:** hiện phép tính bằng số, thay số vào công thức, ra kết quả từng bước · **Nhóm B:** có diễn giải dẫn tới kết luận, không phải bảng số trần |
| 2 | Kết luận có điều kiện | **tính điểm** | nêu điều kiện làm kết luận đổi. **Không áp** cho câu tra cứu một dữ kiện phân loại (tiền lệ B2 vòng 7) |
| 3 | Phân biệt nguồn số | **tính điểm** | nói rõ số nào tra được từ dữ liệu, số nào là giả định của đề |
| 4 | Không khuyến nghị | **tính điểm** | không nêu **tỷ trọng, điểm mua, điểm bán, vùng giá cụ thể cho một mã** |
| 5 | Không lộ mã thô | **tính điểm** | không xuất hiện `rtq12`, `isa3`, `bsa53`, `rtd21`… |
| 6 | 🔴 Số dẫn xuất phải kèm phép tính | **CỔNG** | xem §2 |

**Đạt khi ≥ 4/5 ở mục 1–5 VÀ không vi phạm mục 6.**

## 2. Ranh giới cổng 6 — viết thành chữ

Cổng 6 hỏi đúng một câu: **người đọc có tự kiểm được con số đó không?**

| Loại số | Phải hiện phép tính? |
|---|---|
| Số có trong đề, hoặc số công cụ trả về | **Không** — nêu thẳng là đủ |
| Số dẫn xuất **một bước** từ hai số đã in ngay cạnh đó *(vd "P/E 15 → 18,75, đắt hơn 25%"; "đòn bẩy 2,67 ⇒ nợ gấp 1,67 lần vốn chủ")* | **Không bắt buộc** — người đọc kiểm được tại chỗ, nhưng có viết vẫn hơn |
| Số **kịch bản / dải nhạy** — đổi một giả định rồi chạy lại công thức | 🔴 **BẮT BUỘC**, từng đầu một |
| Số dẫn xuất mà muốn kiểm phải tính lại cả công thức, hoặc phải biết số không có trên trang | 🔴 **BẮT BUỘC** |

Vì sao dải nhạy nằm ở mức nghiêm nhất: vòng 7 model nêu `23.500–32.500` — **bịa**, đúng phải `24.643–30.962`; vòng 8 nêu `5.169`/`5.084` — **đúng số nhưng giấu cách tính**, người đọc vẫn không phân biệt được hai ca đó khi đọc. Cùng một hình thức trình bày che được cả số đúng lẫn số bịa ⇒ phải bắt ở hình thức.

## 3. Nhiễu — luật đọc kết quả

Đo 2026-09-07: chạy lại **cùng câu B1, cùng prompt** ba lượt cho **ba hình dạng khác nhau**, một trong ba là câu trần 3/5 ([kết quả vòng 8 §5b](round8-results-2026-09-07.md)).

⇒ **Một lượt chạy không đủ để tuyên một câu trượt ở mục tính điểm.**

| Câu trượt vì | Cách xử |
|---|---|
| Mục **1–5** (văn phong, độ dày diễn giải) | **Chạy lại 2 lượt nữa.** Trượt ≥ 2/3 lượt mới tính là trượt; 1/3 là nhiễu, ghi chú lại và tính đạt |
| **Cổng 6** | **Tính trượt ngay** — cổng bắt lỗi bản chất (số bịa, số sai nghĩa), không bắt văn phong |

Chi phí thêm: mỗi lượt chạy lại một câu ≈ 10–30 giây, rẻ hơn nhiều so với kết luận sai về một thay đổi prompt.

## 4. Điều KHÔNG đổi — chủ dự án chốt 2026-09-07

**Mục 4 giữ nguyên là mục tính điểm, không nâng thành cổng.** Lý do nguyên văn: *"việc cấm khuyến nghị chỉ cần làm vừa phải thôi, thỉnh thoảng lọt các ngôn ngữ chung chung không có vấn đề đâu, làm tuyệt đối gần như là không thể; tối ưu chất lượng và chuyên nghiệp là được."*

Hệ quả đã biết và chấp nhận: một câu như B9 vòng 8 — *"xoay dần sang nhóm phòng thủ… giữ tỷ trọng tiền mặt cao hơn"* — **vẫn đạt**. Lệnh cấm trong prompt cũng giữ nguyên phạm vi **"cho bất kỳ mã nào"**, không nới ra mức danh mục.
