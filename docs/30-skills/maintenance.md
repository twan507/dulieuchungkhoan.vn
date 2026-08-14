# Bảo trì hai skill chứng khoán

**Ngày:** 2026-08-14 · **Trạng thái:** dự án đã đóng — hai skill xong, test 6 vòng, không còn việc treo

Đọc file này **trước khi sửa bất cứ gì** trong [`.claude/skills/`](../../.claude/skills/). Nó không kể quá trình dựng skill; nó ghi những thứ mà **sửa nhầm sẽ làm hỏng skill và không có gì báo lỗi**.

Bảng thuật ngữ đi kèm là [`terminology.md`](terminology.md) — bắt buộc, không phải tham khảo.

---

## 1. Trạng thái cuối

| | Quy mô | Kiểm chứng |
|---|---:|---|
| `vn-stock-advisor` (L1) | 774 dòng | 5 vòng test riêng, hội tụ 250–275 chữ |
| `vn-stock-knowledge` (L2) | 2.272 dòng | bao phủ cơ học **342/342** tiêu đề section gốc |
| Test hệ hai tầng | 6 vòng | vòng 6 tính toán trên số liệu thật **10/10 đúng** |

**Tiêu chí dừng đã dùng:** hai vòng liên tiếp không tìm thấy lỗi trong tầm skill, và mọi lỗi đã sửa không tái phát. Ép thêm sẽ cắt vào phần lõi. Dùng lại tiêu chí này nếu mở vòng tối ưu mới.

**Rủi ro còn lại, đã chấp nhận:** L2 không có luật độ dài (một câu ra 1.035 chữ nhưng đúng lúc người dùng xin chi tiết) · định dạng disclaimer lúc in nghiêng lúc không · vài mâu thuẫn nội tại của corpus chưa bị hỏi trực diện (khung gap, quy đổi kỳ hạn MA).

## 2. Quyết định thiết kế không được đảo

Đảo bất kỳ dòng nào dưới đây là quay lại một vấn đề đã tốn một vòng audit để giải.

**Về giọng và phạm vi phát ngôn:**

- Xưng **"tôi" / "bạn"**, không thầy/em
- **Bỏ hết tầng công cụ độc quyền** — tên phần mềm, thang điểm sao, nhãn "nhóm 1/2/3", "dòng tiền 1/2/3"
- **Bỏ hình ảnh dân dã hoá người chơi** → dùng *nhà tạo lập · kênh loan tin · nhà đầu tư nhỏ lẻ*
- Kết luận **luôn có điều kiện**, kèm **điều kiện đổi ý**
- Ngôn ngữ **"sức mua"** thay mua/bán; **không đưa lệnh cho mã cụ thể**
- **Không bịa số**; thiếu dữ liệu thì kịch bản hoá tối đa 2 nhánh
- **Không kết bài bằng câu hỏi ngược**
- **Giữ các quan điểm ngược dòng** — đầu tư công không phải bơm tiền · ngân hàng tạo tiền từ hư không · cơ hội nằm ở sự vô lý

**Về tính tổng quát — chốt ở vòng audit 2, để hệ dữ liệu cấp khung ngành:**

- Bảng phân bậc nêu **tiêu chí**, không nêu **danh sách**. Xếp một ngành cụ thể thì chấm bốn thành phần rủi ro rồi chia dải làm ba
- Sáu tiêu chí phân bậc dòng tiền là **bộ tối thiểu, không phải bộ đóng** — thêm được, thiếu vẫn xếp được
- Ngưỡng số phải ghi rõ là **quy ước** và nêu điều kiện đổi. Đặc tả hợp đồng phái sinh phải tra tại thời điểm dùng
- Viết sao cho **đúng cả khi có công cụ tra dữ liệu lẫn khi không có**. Function calling làm câu trả lời chính xác hơn, không được làm skill hỏng khi vắng nó

**Về cách viết luật — nguyên tắc tối ưu:**

> **Ví dụ mẫu neo hành vi mạnh hơn mệnh lệnh.** Vòng 3 thêm rule về độ dài → cải thiện **0%**. Vòng 4 thêm **một ví dụ mẫu ngắn** → cải thiện **15%**. Model bắt chước *cỡ và dáng* của ví dụ, không đếm chữ theo lệnh.

Hai hệ quả: **rule chết là rule tốn chỗ** (từng có rule cấm một từ mà model không có nguồn nào để biết — đã xoá), và khi gặp ca lỗi thì **tổng quát hoá luật đang có**, đừng thêm luật mới. Ví dụ thật: thay vì thêm một dòng ngoại lệ "người mới, vốn nhỏ" vào bảng số mã, luật được tổng quát thành *"bị chặn trên bởi tần suất giao dịch **và** sức theo dõi, lấy cái nào chặt hơn"* — ca đó nằm trong luật thay vì thành ngoại lệ.

## 3. Đừng gỡ nhầm khi audit danh sách ngành

Quyết định *"không nhúng danh sách ngành"* tốn 9 chỗ sửa và một vòng audit. Nhưng có **bốn chỗ nêu tên ngành mà không phải phân bậc luân chuyển** — gỡ chúng là làm hỏng nội dung đúng:

| Chỗ | Vì sao giữ |
|---|---|
| Ba phụ lục đọc BCTC ngân hàng / chứng khoán / bảo hiểm | Là **kế toán**, không phải luân chuyển |
| Cơ chế tăng vốn ở ngành có điều kiện về vốn · cảnh báo lãi suất với bảo hiểm | Là **cơ chế ngành**, gắn với đặc thù bảng cân đối |
| Chọn PB hay PE theo mức thâm dụng vốn | Là **phương pháp định giá** |
| Cơ chế hành vi khi lãi suất thấp | Là **tâm lý**, tên ngành chỉ là ví dụ |

Và một chỗ đã cân nhắc riêng rồi quyết **giữ**: *"ngân hàng đứng đầu xếp hạng an toàn nhưng hút tiền đầu tiên → **ngành báo hiệu**"* ở [`portfolio-and-rotation.md`](../../.claude/skills/vn-stock-knowledge/references/portfolio-and-rotation.md). Đây là **cơ chế**, không phải danh sách.

## 4. Năm thứ trông như lỗi nhưng là cố ý

Cả năm đã bị soi một lượt trong vòng rà cuối và **quyết giữ, có lý do**.

| Trông như lỗi | Vì sao cố ý |
|---|---|
| **Chu kỳ giảm ba bước nằm ở cả hai skill** | Khác góc thật: L2 dạy **cơ chế** (bảng có cột margin, cột bẫy), L1 dạy **phản xạ** (văn xuôi hành động). Cắt bên nào cũng làm bên kia cụt. Đã có dòng trỏ qua lại |
| **Vài kết luận lặp ở cả hai skill** — "đừng tin giá mục tiêu", "bên chất lượng kém quảng bá mạnh hơn" | Ở L2 chúng là **hệ quả của ma trận lợi ích**; cắt thì phần cơ chế cụt. Ở L1 chúng là phản xạ dùng ngay |
| **Marker `[?…]` còn trong văn bản** | Đánh dấu chỗ **nguồn nghe không rõ**. Xoá là giả vờ chắc chắn về thứ không chắc |
| **Anchor mục lục không dấu, heading có dấu** | File đọc như **văn bản thuần, không render HTML** — anchor không cần khớp. Đổi hàng loạt là đổi quy ước, lợi ích bằng 0 |
| **"Hành động ở nhịp 2" vs "quan sát từ điểm chạm thứ 3"** | Hai phép đếm khác nhau, **tình cờ dùng chung con số**: *nhịp* là lần phản ứng tâm lý trước một vùng giá; *điểm chạm* là số lần giá uốn lại ở một đường của mẫu hình. Câu phân biệt đã đặt tại chỗ trong `technical-indicators.md` |

**Một quy ước ngược lại, phải giữ đúng:** chữ trong **heading trùng nguyên văn** chữ trong mục lục, anchor giữ không dấu. Thống nhất 2026-08-14 trên 61 heading / 8 file. Thêm mục mới thì viết mục lục và heading cùng một chữ.

## 5. Lỗi của nguồn đã sửa — đừng "sửa ngược"

Đã xác minh tận file, không phải nghe báo lại. Cả năm chỗ đều là **nguồn nói sai và skill đã sửa đúng** — người đọc đối chiếu corpus sẽ tưởng skill sai.

| Chỗ | Nguồn nói | Skill dùng |
|---|---|---|
| **FCFE tính trùng khấu hao** | công thức gốc của nguồn | *đầu tư vốn gộp = chênh lệch TSCĐ ròng + khấu hao trong kỳ* |
| **«nội giải»** | thuật ngữ dùng 10 lần trong bản tóm tắt | Lỗi nhận dạng giọng nói — thực ra là *biên độ cây nến*. Xuất hiện đúng 1 lần trong transcript gốc |
| **"50 ngày = 1 tháng"** | Version đặc biệt | 5 ngày ≈ 1 tuần · 20 ≈ 1 tháng · 50–60 ≈ 1 quý · 200 ≈ nhiều quý |
| **Fama-French 3 nhân tố** | từng bị phát biểu là "Size, Value, Momentum" | Momentum là của **Carhart**. FF3 không có momentum |
| **P/E cao = kém an toàn** | phát biểu đơn điệu | Phân biệt *P/E cao do tăng trưởng* với *P/E cao do lợi nhuận sụp về gần 0* |

**Bảng phân loại bốn loại khoảng trống giá chỉ nằm ở `technical-indicators.md`**, file cung cầu trỏ sang chứ không giữ bản riêng. Đây là **khung riêng của nguồn, khác quy ước quốc tế** — đừng "sửa" theo sách tây: *đột phá* = sau đoạn tăng đầu tiên rồi có vùng lưỡng lự, có tin đổi nền tảng; *tiếp diễn* = giá tăng lại sau một đoạn giảm, "tăng trong nghi ngờ"; *hết hơi* = sau đoạn tăng dài, khối lượng **cực lớn**, không tin mới.

⚠️ **Một chỗ ngược lại — mâu thuẫn doji KHÔNG phải ảo.** Hai nguồn thật sự đọc ngược nhau. Cách hoà giải đang dùng: *thân ngắn + biên độ **lớn** = lưỡng lự; thân ngắn + biên độ **ngắn**, không bóng = xu thế chắc chắn, tiếp diễn.* Muốn chắc thì phải kiểm bản gốc `Ứng dụng 2024 CD2` — mà transcript verbatim **không còn trong repo**, phải lấy từ bản lưu trữ ngoài.

## 6. Bộ test hồi quy

Vòng 6 là **phép thử tốt nhất** cho lỗi FCFE: đưa số liệu, bắt tính ra kết quả. **FCFF phải ra 260 tỷ, không phải 380.** Ai đó "sửa ngược" công thức về bản gốc của nguồn thì con số lệch hẳn và bài test bắt được ngay.

Chạy lại bộ này khi: sửa nội dung `valuation.md` · nối function calling vào skill · thêm skill mới vào hệ.

Cách test đã dùng: subagent **Sonnet độc lập**, mỗi vòng ~10 câu **có đáp án xác định**, tự chọn skill, kèm câu lạ ngoài kịch bản dựng sẵn. Kiến thức kiểm được đúng/sai nên không cần model mạnh để chấm.

## 7. Lỗ hổng phạm vi — phải vá ở tầng sản phẩm

**Skill không thể là người gác cổng cho chính nó.** Luật *"chỉ trả lời chứng khoán, tài chính, kinh tế"* nằm trong thân `SKILL.md` chỉ đọc được **sau khi skill đã tải**, mà câu ngoài phạm vi thì không kích hoạt skill nào. Đo được ở vòng 5: **3/4 câu ngoài phạm vi vẫn được trả lời đầy đủ**, kể cả viết trọn một đoạn code Python.

Bằng chứng chẩn đoán đúng: câu **nửa trong nửa ngoài** (bóng đá + cổ phiếu ngành thể thao) thì skill được tải và tách đúng hai vế. Luật hoạt động khi skill tải, vô hiệu khi không.

**Khi dựng backend, dán nguyên văn đoạn này vào system prompt** — không nhét thêm vào skill:

> Bạn chỉ trả lời trong lĩnh vực chứng khoán, tài chính và kinh tế: thị trường và cổ phiếu, doanh nghiệp niêm yết, vĩ mô, chính sách tiền tệ và tài khoá, các loại tài sản tài chính và quan hệ giữa chúng.
>
> Câu hỏi ngoài lĩnh vực đó — sức khoẻ, pháp lý, lập trình, ẩm thực, đời tư, kiến thức phổ thông — từ chối gọn trong một câu, nói rõ bạn chỉ làm mảng này, rồi dừng. Không giải thích dài, không xin lỗi, không đưa lời khuyên thay thế, và không lái ngược về chứng khoán cho có việc.
>
> Câu nửa trong nửa ngoài: trả lời phần thuộc lĩnh vực, nói một câu rằng phần còn lại không thuộc chỗ mình.

Luật trong L1 §Ranh giới **vẫn giữ** vì nó xử lý tốt ca nửa trong nửa ngoài — ca phổ biến hơn nhiều so với ca ngoài hẳn.

## 8. Ngân sách dòng — nếu phải cắt thì cắt đâu

Tổng corpus trong phạm vi **875.415 byte**, nén tỷ lệ **3,5 : 1**. Ngân sách đo từ dung lượng nội dung thật, không suy từ số section. Mọi file hiện nằm trong sai số ±10%.

Bốn chỗ lệch tỷ lệ **có lý do, đừng "cân bằng" lại**: `valuation` và `financial-statements` dày hơn vì công thức và quy trình không nén theo tỷ lệ như văn nói — đây là lõi *"tự làm được"*. `advanced` chiếm 4,7% corpus nhưng 8% ngân sách vì Fama-French, APT, CAPM là công thức thuần. `portfolio-and-rotation` và `psychology-information` mỏng hơn vì chồng lấn skill 1 nhiều nhất, chỉ viết tầng cơ chế mà skill 1 cố tình bỏ.

**Nếu vượt ngân sách:** nén tiếp đúng `portfolio-and-rotation` và `psychology-information`. **Không cắt** khối HP3 — đó là mức "tự làm được" đã chốt. **Không cắt** `advanced` — 4,7% corpus, cắt không tiết kiệm được gì mà mất hẳn Fama-French/APT/hedging vì không nguồn nào khác có.

## 9. Nguồn và giới hạn của nó

Skill dựng từ [`corpus/`](corpus/) — bản **AI tóm tắt** từ transcript gốc, không phải transcript. Skill 2 chỉ đọc HP0–HP6; **Trà Chiều không đưa vào skill 2** vì gần như toàn bộ gắn thời điểm, phần phương pháp đã nằm ở skill 1.

Corpus là **nhiều thế hệ giáo trình dạy lại cùng nội dung** (V1 2022 → Ứng dụng 2024). Quy tắc xử lý mâu thuẫn: bản **mới nhất thắng** khi khác nhau về phương pháp · bản chi tiết cũ **bổ sung chiều sâu**, không ghi đè kết luận · mâu thuẫn thật thì **ghi cả hai kèm điều kiện áp dụng**. Ví dụ mâu thuẫn thật còn trong skill: số mã tối ưu — một nguồn nói 10–15, nguồn khác nói 6–8.

🔴 **Corpus có thể khuếch đại nhiễu nhận dạng giọng nói** — một từ nghe nhầm xuất hiện 1 lần trong transcript thành thuật ngữ dùng 10 lần trong bản tóm tắt. Đã xảy ra thật với «nội giải». Gặp thuật ngữ nghe lạ thì đối chiếu ngược transcript, mà transcript nay chỉ còn ở **bản lưu trữ ngoài repo**.

Số liệu trong skill toàn bộ là **2022–2024 và đã chết**. Giữ công thức và định nghĩa, bỏ quan sát tại thời điểm. Marker `[?…]` đánh dấu chỗ nguồn nghe không rõ — **cố ý giữ**, xoá là giả vờ chắc chắn về thứ không chắc.

## 10. Ba thao tác đã trả giá

- **`bash grep` không đọc được ký tự `«` trong locale máy này.** Kiểm tồn dư thuật ngữ **phải dùng PowerShell**, nếu không sẽ báo sạch trong khi còn sót.
- **Thay thế hàng loạt bằng `sed` có sinh lỗi** — "cổ phiếu cổ phiếu", chữ hoa giữa câu. Thay thuật ngữ hàng loạt thì phải **đọc lại câu**, không chỉ đếm tồn dư.
- **Sao lưu trước khi giao cho subagent sửa hàng loạt**, rồi diff từng thay đổi thay vì tin báo cáo. Vòng rà soát nhất quán từng sửa 56 chỗ trên 13/14 file — không diff thì không cách nào biết nó đã đụng vào đâu.
