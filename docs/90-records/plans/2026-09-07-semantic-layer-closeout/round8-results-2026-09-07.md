# Kết quả bộ hồi quy vòng 8 — chạy thật 2026-09-07, 15:59–16:12

Chạy sau khi thêm khối `ANSWER_RULES` (Task 1). **Một tiến trình cho mỗi câu**, lịch sử rỗng — sạch hơn vòng 7 (chạy theo khối) và không đắt hơn, vì lát 10 đã đo được cache MiniMax **không** trúng giữa hai câu khác nhau. Transcript đầy đủ: [`round8-transcript-2026-09-07.md`](round8-transcript-2026-09-07.md).

Lệnh: `printf '%s\n' "<câu>" | uv run --env-file ../.env --project . python -m agent`, chạy **tiền cảnh**, từ trong `backend/`.

---

## 1. Kết quả hai lớp

| | Vòng 7 | **Vòng 8** | Ngưỡng AC2 | |
|---|---|---|---|---|
| Lớp 1 — số | 15/15 | **15/15** | 15/15 | ✅ giữ nguyên |
| Lớp 2 — hình dạng | 13/15 | **12/15** | ≥ 14/15 | ❌ **không đạt, và TỆ HƠN vòng 7** |

Lớp 1 chấm bằng script đối chiếu literal đáp án đã lưu (`grade_l1.py` ở scratchpad), không tính lại theo cách code tính (§4.5.3).

## 2. Bảng chấm 15 câu

Chấm bằng **đúng thước vòng 7**: mục 1–5 tính điểm, đạt khi ≥ 4/5; mục 6 là cổng loại. Tiền lệ vòng 7 được giữ: mục 2 **không áp** cho câu phân loại (B2).

| Mã | Lớp 1 | Lớp 2 | Mục trượt | Cổng 6 | Kết luận | So vòng 7 |
|---|---|---|---|---|---|---|
| A1 | Đạt | 5/5 | — | Sạch | **ĐẠT** | = |
| A2 | Đạt | 5/5 | — | Sạch | **ĐẠT** | = |
| A3 | Đạt | 4/5 | #3 | Sạch | **ĐẠT** | = |
| A4 | Đạt | 5/5 | — | 🔴 **vi phạm** | **TRƯỢT** | = (đổi kiểu hỏng) |
| A5 | Đạt | 5/5 | — | Sạch | **ĐẠT** | ↑ (4/5 → 5/5) |
| A6 | Đạt | 5/5 | — | Sạch *(xem §4)* | **ĐẠT** | = |
| B1 | Đạt | 3/5 | #1 (không diễn giải), #2 | Sạch | **TRƯỢT** | 🔻 **hồi quy** (5/5) |
| B2 | Đạt | 5/5 | — | Sạch | **ĐẠT** | = |
| B3 | Đạt | 5/5 | — | Sạch | **ĐẠT** | ↑ |
| B4 | Đạt | 5/5 | — | Sạch | **ĐẠT** | ↑ |
| B5 | Đạt | 5/5 | — | Sạch | **ĐẠT** | ↑ **hết trượt** |
| B6 | Đạt | 4/5 | #2 | Sạch | **ĐẠT** | = |
| B7 | Đạt | 5/5 | — | Sạch | **ĐẠT** | = |
| B8 | Đạt | 5/5 | — | 🔴 **vi phạm** | **TRƯỢT** | 🔻 **hồi quy** (5/5) |
| B9 | Đạt | 4/5 | 🔴 #4 khuyến nghị | Sạch | **ĐẠT** *(theo số học rubric)* | 🔻 nội dung xấu đi |

**ĐẠT 12/15.** Ba câu trượt: **A4** (cổng 6), **B1** (3/5), **B8** (cổng 6).

## 3. Hai luật mới có tác dụng — và tác dụng đó không đủ

**Có tác dụng, đo được:**

- **A4 hết bịa số.** Vòng 7 nêu dải nhạy `23.500–32.500` trong khi đúng là `≈24.643–30.962` (lệch 4–5% hai đầu). Vòng 8 nêu `5.169 tỷ (~25.844 đ)` cho `g = 4,5%` và `5.084 tỷ (~25.421 đ)` cho `r = 14,5%` — **kiểm tay đều đúng**: `460×1,045/0,093 = 5.169,4` và `483/0,095 = 5.084,2`. Số đã đúng; cái còn thiếu là **phép tính không hiện ra**, nên vẫn vi phạm cổng 6.
- **B5 hết trượt.** Vòng 7 chỉ liệt kê hai sự kiện; vòng 8 diễn giải nhịp trả sáu tháng, gắn với lọc chất lượng, và **nói thẳng kho chưa lưu tỷ lệ chi trả** thay vì bịa.
- **Mẫu hỏng #3 giảm mạnh.** Vòng 7 bỏ mục "phân biệt nguồn số" ở **5/15** câu; vòng 8 chỉ còn **1/15** (A3). Câu giữa của `ANSWER_RULES` nhắm đúng chỗ này.

**Không đủ, cũng đo được:**

- **B1 hồi quy nặng.** Vòng 7 trả lời có diễn giải (5/5). Vòng 8 trả lời **đúng một câu**: *"HPG phiên 03/09/2026 đóng cửa ở 21.600 đ (giá điều chỉnh, kho chưa có khối lượng…)"* — không diễn giải, không điều kiện ⇒ 3/5.
- **B8 phát biểu sai một quan hệ số.** *"HPG rẻ hơn VCB khoảng 3,9 lần"* — hai con số gốc đúng (7,89 và 11,82) nhưng `11,82 − 7,89 = 3,93` là **hiệu điểm P/E**, không phải "rẻ hơn 3,9 lần" (tỷ lệ thật là `11,82/7,89 = 1,50`). Một con số dẫn xuất nêu trần, không phép tính, và **sai nghĩa** ⇒ đúng thứ cổng 6 sinh ra để bắt.
- 🔴 **B9 vẫn khuyến nghị — luật cấm không giữ được.** Nguyên văn: *"Phù hợp hơn là xoay dần sang nhóm phòng thủ (hàng tiêu dùng thiết yếu, điện, viễn thông) và **giữ tỷ trọng tiền mặt cao hơn**"*, và *"có thể **gom thêm** nhóm đòn bẩy tài chính"*. Luật mới cấm *"tỷ trọng danh mục, điểm mua, điểm bán, vùng giá cụ thể **cho bất kỳ mã nào**"* — model lách đúng khe hở đó: khuyến nghị ở mức **nhóm ngành và tiền mặt**, không nêu mã nào.

## 4. Ba lỗ hổng của chính thước đo, lộ ra khi chấm

1. 🔴 **Mục 4 (không khuyến nghị) là mục TÍNH ĐIỂM, không phải cổng.** B9 vi phạm mục 4 mà vẫn 4/5 ⇒ **vẫn ĐẠT**. Nghĩa là bộ hồi quy hiện tại **không thể trượt** một câu chỉ vì nó khuyên mua bán — đúng thứ lát 11 sinh ra để chặn.
2. **Rubric tự mâu thuẫn:** bảng có 6 dòng, chữ ghi *"chấm 5 mục, đạt khi ≥ 4/5"*, mà mục 5 và 6 đều gắn nhãn *(cổng)*. Vòng 7 chấm B5 **3/5** ⇒ thực tế mục 1–5 tính điểm, chỉ mục 6 là cổng. Vòng 8 chấm theo đúng cách đó để so được, nhưng **văn bản rubric phải sửa** trước khi có vòng 9.
3. **Ranh giới cổng 6 chưa định nghĩa được mức "hiện phép tính".** A6 viết *"đắt hơn 25%"* (từ `18,75/15`) và A5 viết *"nợ gấp 1,67 lần"* (từ `2,67 − 1`) — số đúng, phép tính không viết ra, nhưng cả hai đứng ngay cạnh số gốc nên người đọc kiểm được trong một bước. A4 và B8 thì phải tính lại cả công thức mới kiểm được. Vòng 8 chấm theo ranh giới **"người đọc có kiểm được tại chỗ không"**; nếu chấm chặt tuyệt đối thì A6 cũng trượt ⇒ **11/15**. Ranh giới này phải viết vào rubric, không để mỗi lượt chấm tự hiểu.

## 5. Số đo chi phí (AC8)

`ops.llm_call`, 32 request, **0 lỗi**:

| | |
|---|---|
| Token vào | **473.810** |
| Token đọc từ cache | **883.368** |
| Token ra | **35.239** *(thinking 16.638)* |
| Độ trễ trung bình | **26,4 s** · cao nhất **171,8 s** |
| Quota cửa sổ 5 giờ | 92% → **90%** sau 15 câu |

Thời gian thật: 15 câu trong **~13 phút** (16:12 − 15:59). **Vì sao chậm hơn vòng 7 — đã tách bạch bằng `ops.llm_call`, không đoán** *(chủ dự án hỏi 2026-09-07 16:25: có phải do kiến trúc gửi lại kết quả công cụ không)*:

| | Vòng 7 | Vòng 8 |
|---|---|---|
| Request | 63 (≈2,9/câu) | 38 (**≈2,1/câu**) |
| Token vào / request | 16.398 | **13.488** |
| Token ra / request | 1.233 | **998** |
| Cache đọc / request | 23.776 | **28.213** |
| Độ trễ trung bình | 12,5 s | **23,1 s** |
| p50 · p90 | 6,9 s · 31,4 s | 9,2 s · **78,6 s** |
| **Token ra mỗi giây** | **98,5** | **43,2** |

⇒ **Không phải do thiết kế.** Thêm một vòng gửi lại thì **số request phải tăng** — đây nó *giảm*; prompt dài thêm thì token vào phải tăng — đây nó *giảm*; luật mới làm câu dài hơn thì token ra phải tăng — đây cũng *giảm*. Thứ duy nhất đổi là **tốc độ sinh chữ tụt hơn một nửa** (98,5 → 43,2 token/s), tức phía nhà cung cấp. Lát 10 đo 84–152 token/s.

⚠️ Đây là số của **một buổi chiều**. Chưa được sửa dải trong `10-sources/llm/minimax.md` — theo §1.2, chỉ sửa khi đo lại; cần thêm ít nhất một điểm đo nữa (vòng 9) cùng hướng. Ba câu đắt nhất: B8 **202 s**, A2 127 s, B9 98 s. Vòng 7 đo p50 6,9 s · p90 34,5 s ⇒ **vòng 8 chậm hơn hẳn**; chưa rõ do khối prompt dài thêm hay do nguồn — **chưa đo, không suy đoán**.

## 5b. 🔴 Phép đo có nhiễu — đo ngay sau khi chấm (2026-09-07 16:20)

Chạy lại **đúng câu B1** ba lượt liên tiếp, cùng prompt, cùng code:

| Lượt | Hình dạng |
|---|---|
| 1 | Diễn giải đầy đủ (nến mở cao đóng thấp, điều kiện đổi nhận định) — ước 5/5 |
| 2 | Có diễn giải, nói rõ kho thiếu khối lượng — ước 4–5/5 |
| 3 | **Một câu trần**, y hệt lượt vòng 8 — 3/5 |

⇒ **B1 trượt là nhiễu lượt chạy, không phải hệ quả của `ANSWER_RULES`.** Hệ quả cho cách đọc mọi con số ở trên:

1. Chênh **12/15 với 13/15 không phải bằng chứng "vòng 8 tệ hơn vòng 7"** — một câu biên đổi kết quả là đủ lật con số đó. Câu *"tệ hơn vòng 7"* ở §1 là **nói quá**, giữ nguyên ở đây làm bản ghi tại-thời-điểm nhưng phải đọc kèm mục này.
2. Thứ đáng sửa là lỗi **lặp lại được**: A4 trượt cổng 6 ở **cả hai vòng** (vòng 7 bịa số, vòng 8 đúng số nhưng giấu phép tính) ⇒ lỗi cấu trúc. B8 mới trượt một lần, chưa biết là cấu trúc hay nhiễu.
3. Ngưỡng "≥ 14/15 trên **một** lượt" vì thế là thước yếu. Cách rẻ: câu nào trượt ở **mục tính điểm** (không phải cổng) thì chạy lại hai lượt trước khi kết luận; câu trượt **cổng** thì tính ngay, vì cổng bắt lỗi bản chất chứ không bắt văn phong.

## 6. Kết luận

**AC2 không đạt: 12/15, thấp hơn cả vòng 7 (13/15).** Theo plan Task 4, đây là **cổng dừng** — báo nguyên trạng cho chủ dự án, không tự sửa tiếp rồi chạy lại.

Ba việc cần chủ dự án chốt trước khi có vòng 9, xếp theo mức quan trọng:

1. **Nâng mục 4 thành cổng loại** — nếu không, bộ hồi quy không bao giờ trượt được một câu khuyến nghị.
2. **Nới lệnh cấm ra ngoài phạm vi "một mã"**: cấm cả tỷ trọng tiền mặt, xoay nhóm ngành, và động từ hành động ở mức danh mục.
3. **Viết ranh giới cổng 6 thành chữ** — "hiện phép tính" nghĩa là gì khi số dẫn xuất chỉ cách số gốc một bước.
