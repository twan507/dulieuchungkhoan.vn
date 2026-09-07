# Ledger lát 11 — đóng hợp đồng tầng ngữ nghĩa và trả bảy nợ

Nhánh `feat/semantic-layer-closeout`, gốc `main` = `69ce724`. Spec duyệt 2026-09-07 (bốn điểm §9 chủ dự án giao lại cho tôi chốt). Test trước lát: **1.025 passed, 2 skipped**.

---

## 1. Tiến trình

| Task | Kết quả | Commit |
|---|---|---|
| — | Lệnh test trong tài liệu chạy trần cho **425 error** (thiếu `--env-file`), sửa `database/README` | `2379a71` |
| 1 · `ANSWER_RULES` | Block system thứ ba; hai test seam mới, hai test cũ sửa từ "3 block" sang "4 block". **1.026 passed** | `76061a8` |
| 2 · `/moi` | `la_lenh_moi()` + xử lý trong `repl`; 2 test (hàm thuần + `repl` với `input` giả) | `5d1e4ff` |
| 3 · test khởi động | `test_a14_startup.py` chạy dưới `AGENT_DATABASE_URL`; **chứng minh đỏ** bằng cách bỏ `timeout_s` ⇒ `assert 120.0 == 600.0` | `aa74d52` |
| 4 · vòng 8 | Hình dạng **12/15** ⇒ cổng dừng của plan, báo chủ dự án | `ffd5929` |
| — | Đo nhiễu; đo nguyên nhân chậm | `5a69092`, `ee2a907` |
| 4b · vòng 9 | Thêm câu luật về dải nhạy + rubric v2 ⇒ hình dạng **14/15** ✅ | `7ace237`, `d48e513` |
| 4c · vòng 10 | Đổi hướng: **bỏ số kịch bản tự phát** ⇒ A4 sạch cổng 6 | `e84a0f5` |
| 5 · payload | Bỏ `ngay_hien_thi`: **292.009 → 230.009 ký tự (−21,2%)** | `cbb10bb` |
| 6 · A/B `REMINDER` | Hoà 14/15–14/15 ⇒ **giữ** | `17fc015` |

## 2. Rulings

1. **Thứ tự block.** `ANSWER_RULES` tách khỏi `TOOL_RULES` thay vì nhập chung: khối kia tự khai chỉ nói cách dùng công cụ, **và mang ngày hôm nay** nên đổi mỗi ngày — gói luật ổn định vào đó là tự huỷ tiền tố cache mỗi ngày. Nếu sai: một block thừa, không ảnh hưởng kết quả.
2. **Thêm một luật ngoài hai nợ đã chốt** (phân biệt nguồn số). Lý do: mẫu hỏng lặp nhiều nhất vòng 7 (5/15 câu), cùng khối nên giá bằng 0. **Đo được là đúng**: vòng 9 chỉ còn 1/15.
3. **Không nâng "không khuyến nghị" thành cổng loại** — chủ dự án chốt: *"cấm khuyến nghị chỉ cần vừa phải, ngôn ngữ chung chung lọt thì không sao, tối ưu chất lượng và chuyên nghiệp là được."*
4. **Sửa rubric bằng file MỚI** (`rubric-v2.md`) chứ không sửa `regression-round7.md` — file đó là bản ghi tại-thời-điểm của vòng 7 (§1.7).
5. **A/B `REMINDER` đo bằng sửa tạm, không thêm biến môi trường** cho một lượt đo (§4.4.2). Đã `git checkout` hoàn nguyên và kiểm `git status` sạch.
6. **Task 5 chỉ sửa `get_price_series`.** `get_macro_series` và `get_news` cũng có trường lặp cùng kiểu — **báo, không tự sửa**: chưa ai đo phần dư của chúng, và spec giới hạn ở chuỗi giá.

## 3. Ba thứ lát này đo được mà trước đó không ai biết

### 3.1 🔴 Bộ hồi quy có nhiễu ở **cả hai lớp**

Chạy lại cùng một câu, cùng prompt, cùng code:

| Câu | Kết quả |
|---|---|
| B1 (hình dạng) | 3 lượt ra **3 hình dạng khác nhau**: đầy đủ · vừa · một câu trần |
| A4 (số) | 3 lượt: **2 đúng công thức Gordon, 1 bỏ mất `(1+g)`** |

⇒ Ba vòng trước đều báo *"lớp 1: 15/15"* nên lớp số trông như chỗ chắc chắn nhất. Thật ra **chưa ai đo tính ổn định của nó**. Từ nay "15/15" đọc là *"đúng ở lượt được chấm"*.

Luật đọc kết quả viết vào [rubric v2 §3](rubric-v2.md): trượt ở mục tính điểm ⇒ chạy lại 2 lượt, trượt ≥ 2/3 mới tính; trượt **cổng** ⇒ tính ngay.

### 3.2 Luật ở tầng prompt không diệt được họ lỗi "số không kiểm được"

Câu A4 trượt cổng 6 **ba vòng liên tiếp, ba kiểu khác nhau**: bịa dải nhạy → đúng số nhưng giấu phép tính → sai công thức. Ra luật thẳng vào nó (*"kịch bản phải viết phép tính từng đầu"*) **không ăn**.

Cái ăn là **bỏ hẳn thứ không ai yêu cầu**: model tự thêm dải nhạy vì L1 dạy kết luận phải có điều kiện — đúng ý định, sai chỗ xuất ra. Luật mới bỏ số kịch bản tự phát, giữ cảnh báo mong manh bằng lời và bằng số đã có trên trang. Vòng 10: A4 sạch, 6/6 câu nhóm A đúng số, **0 số kịch bản tự phát**.

### 3.3 Chậm là phía nhà cung cấp, không phải kiến trúc

Chủ dự án hỏi có phải do vòng gửi lại kết quả công cụ không. `ops.llm_call` trả lời: vòng 8 dùng **ít** vòng gửi lại hơn vòng 7 (2,1 so với 2,9 mỗi câu), **ít** token vào hơn, câu trả lời **ngắn** hơn — mà vẫn chậm gấp đôi. Thứ đổi là **tốc độ sinh chữ: 98,5 → 43,2 token/s**. Vòng 9 và 10 nhanh trở lại. Chi tiết: [vòng 8 §5](round8-results-2026-09-07.md).

## 4. Nợ còn lại sau lát 11

| Mục | Trạng thái |
|---|---|
| `ops.llm_call` ghi qua role `dlck_etl` | **Đóng bằng lý do — *đã có đường khác***: đúng cho vòng chat terminal, sai cho service; tách `dlck_chatlog` là việc của lát dựng API |
| `news.trade_name` rỗng | **Đóng bằng lý do — *loại có chủ đích ở tầng này***: seed tên thương mại là việc ETL tin |
| Trường lặp trong `get_macro_series` · `get_news` | **Chưa đo** — cùng hình dạng với `get_price_series`, nhưng chưa ai đo phần dư |
| **Hàng rào số** *(mới, xem §5)* | Ghi lại để tối ưu sau, không thuộc lát 11 |

## 5. Việc để dành: hàng rào số lúc chạy

Chủ dự án nêu 2026-09-07: *"model chỉ viết chữ, còn số liệu và công thức thì dùng tool fill, như vậy không bao giờ bịa số liệu — có khả thi không?"*

**Khả thi, và là cách duy nhất trong bốn cách đã cân mà thực sự đóng được họ lỗi này** — ba vòng ra luật ở tầng prompt là bằng chứng ngược cho cách rẻ hơn. Hình dạng dự kiến:

1. **Thêm nhóm function TÍNH** — `gordon(...)`, `wacc(...)`, `dupont(...)` hoặc một `tinh(biểu_thức)` an toàn; tool trả **cả kết quả lẫn chuỗi phép tính đã thay số**.
2. **Hàng rào lúc chạy**: quét câu trả lời, mỗi con số phải truy được về (a) đề bài, (b) kết quả tool đọc kho, hoặc (c) kết quả tool tính. Không thuộc ba nguồn ⇒ chặn hoặc gắn cờ.

🔴 **Vì sao hôm nay chưa dựng được hàng rào đó:** số dẫn xuất hợp lệ **vốn không nằm trong kết quả tool nào**, nên không có gì để đối chiếu. Phải có tool tính trước thì hàng rào mới có nguồn so.

**Ba rủi ro phải đo trước khi xây:** model vẫn tự nhẩm thay vì gọi tool (nên hàng rào phải chặn được, không chỉ dặn); tách số trong văn tiếng Việt dễ báo nhầm (`27.443 đ` · `12%` · năm `2024` · ngày `03/09`); thêm vòng gọi tool là thêm thời gian.

**Bước rẻ nhất làm trước:** viết bộ **dò** (không chặn), quét lại transcript vòng 7–11 đã lưu trong repo, đếm mỗi câu trả lời có bao nhiêu số không truy được về đề hay về tool. Hiện ta mới biết họ lỗi này xảy ra ở A4 — **chưa biết 14 câu kia thế nào**.

## 6. Trạng thái bàn giao

*(điền khi đóng lát — sau review Task 7 và verify Task 8)*
