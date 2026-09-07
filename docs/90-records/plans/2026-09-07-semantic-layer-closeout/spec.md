# Spec lát 11 — đóng hợp đồng tầng ngữ nghĩa và trả hết bảy nợ

**Ngày:** 2026-09-07 · **Trạng thái:** ✅ **DUYỆT 2026-09-07** — bốn điểm §9 chủ dự án giao cho tôi chốt theo đề xuất · **Nhánh dự kiến:** `feat/semantic-layer-closeout`
**Điểm vào:** [roadmap §3 "Điểm vào cho lát 11"](../../../00-overview/roadmap.md) · **Hồ sơ lát 10:** [`2026-09-07-semantic-layer/`](../2026-09-07-semantic-layer/)

---

## 0. Dữ kiện đã kiểm và giả định (§4.8 Bước 0)

**Đã kiểm — đọc file trong phiên này:**

| Dữ kiện | Nguồn |
|---|---|
| `system_prompt.py` có **ba** block theo thứ tự `SCOPE_GUARD` → `L1` → `TOOL_RULES`; hai block đầu bất biến, block cuối mang ngày hôm nay nên đổi mỗi ngày | `backend/agent/system_prompt.py:44-55` |
| Luật *"số dẫn xuất phải kèm phép tính"* hiện **chỉ nằm ở rubric chấm** (mục 6, cổng loại) — không có dòng nào trong prompt | `regression-round7.md:137` |
| Vòng 7: **số 15/15**, **hình dạng 13/15**, ngưỡng 14. Hai câu trượt: A4b bịa dải nhạy `23.500–32.500` (đúng phải `≈ 24.643–30.962`), B5 chỉ liệt kê không diễn giải | `round7-results-2026-09-07.md:9-30` |
| Mẫu hỏng lặp nhiều nhất: bỏ mục *"phân biệt số tra được / số giả định của đề"* ở **5/15 câu** | nt |
| `repl()` giữ `history` vô hạn, **không lệnh nào xoá** ⇒ tràn cửa sổ là ngõ cụt, chỉ thoát bằng Ctrl+C | `chat.py:128-150` · `review-chuan-v4 §G3` |
| Đường khởi động `agent/__main__.py` **không test nào chạm**; lát 10 chỉ kiểm tay | `review-chuan-v4 §G5` |
| `REMINDER` chèn sau **mọi** kết quả công cụ ⇒ lát 10 không có lượt đối chứng nào | `chat.py:31,91` |
| Chi phí thật ≈ **$0,016/câu**, p50 6,9 s · p90 34,5 s ⇒ một lượt 15 câu ≈ **$0,25**, ~10–15 phút | `round7-results §3` |

**Giả định — chưa kiểm, ghi ra để không lẫn với dữ kiện:**

1. Hai câu trượt (A4b, B5) sẽ đạt khi luật xuống tầng prompt. **Chưa có bằng chứng**, chỉ có suy luận từ ca `SCOPE_GUARD` (cùng cấu trúc: luật nằm trong L1 chỉ có tiếng nói *sau khi* skill tải).
2. Thêm một block system ổn định **không** phá cache tiền tố của MiniMax.
3. Cấm nêu tỷ trọng/điểm mua **không** kéo tụt các mục khác của rubric.

Cả ba chỉ kiểm được bằng **chính lượt chạy thử** — nên lát này lấy lượt chạy làm phép đo, không lấy lập luận làm bằng chứng.

---

## 1. Mục tiêu

Đưa **hai luật** xuống tầng prompt, chạy lại bộ hồi quy 15 câu, và **đóng cả bảy nợ** lát 10 để lát 12 bắt đầu trên nền sạch.

**Ngoài phạm vi, có lý do** *(§1.4)*: đổi hình dạng kết quả của 9 function · thêm function mới · sửa nội dung L1/L2 · dựng service API.

---

## 2. Bảy nợ → việc cụ thể

| # | Nợ | Việc trong lát này |
|---|---|---|
| 1 | Hình dạng 13/15 | Luật *"số dẫn xuất phải kèm phép tính bằng số"* xuống prompt; chạy lại 15 câu, đích **≥ 14/15** |
| 2 | Model trôi sát ranh giới khuyến nghị | **Chủ dự án chốt 2026-09-07: CẤM.** Thêm luật cấm nêu tỷ trọng danh mục và điểm mua/bán cụ thể |
| 3 | `REMINDER` chưa đo được tác dụng | Lượt A/B: cùng 15 câu, **không** nhắc; so hai bảng chấm rồi quyết giữ/bỏ |
| 4 | Tràn cửa sổ không có đường ra | Lệnh `/moi` trong `repl` xoá `history` |
| 5 | Đường khởi động không có test | Test chạy **dưới đúng role production**, khuôn `assert_migrated` của ingester (§3.5) |
| 6 | Bốn commit cuối chưa review độc lập | Review hai trục cho `56ceeaa` `943bcfd` `8624c38` `7ec99c7` + toàn bộ thay đổi lát này |
| 7 | Ba nợ nhỏ | Xem §5 — **một làm, hai đóng bằng lý do** |

---

## 3. Thiết kế thay đổi

### 3.1 Khối luật mới `ANSWER_RULES` — block thứ ba, đứng trước `TOOL_RULES`

Không nhét vào `TOOL_RULES`: khối đó tự khai là *"chỉ nói CÁCH dùng công cụ và neo ngày hiện tại"* — nhét luật trình bày vào là làm tên nói dối. Không đụng `L1` (nội dung skill) và `SCOPE_GUARD` (tầng phân định).

Thứ tự mới: `SCOPE_GUARD` → `L1` → **`ANSWER_RULES`** → `TOOL_RULES`. Ba khối đầu **bất biến** nên tiền tố cache dài ra chứ không ngắn đi; khối mang ngày vẫn nằm cuối.

**Nội dung dự kiến** *(câu chữ mở để bạn sửa — §9)*:

> Mọi con số bạn tự tính ra — không có trong câu hỏi và không do công cụ trả về — phải hiện phép tính **bằng số** ngay tại chỗ: thay số vào công thức, ra kết quả. Nêu một con số dẫn xuất trần, kể cả dải nhạy hay ước lượng nhanh, là bịa.
>
> Nói rõ số nào tra được từ dữ liệu, số nào là giả định của đề.
>
> Không nêu tỷ trọng danh mục, điểm mua, điểm bán hay vùng giá cụ thể cho bất kỳ mã nào, và không dùng câu mang nghĩa hành động ("gom dần", "mua thêm khi giá về…"). Nêu điều kiện làm kết luận đổi thì được.

Câu giữa nhắm đúng **mẫu hỏng lặp nhiều nhất** (5/15 câu) — rẻ, cùng khối, không tốn lượt chạy riêng.

### 3.2 `/moi` — đường ra khỏi phiên tràn

Hàm thuần `la_lenh_moi(cau: str) -> bool` trong `chat.py`; `repl` gọi trước khi vào `run_turn`, khớp thì xoá `history` và in một dòng xác nhận. **Không** tự cắt lịch sử — cắt tự động là đoán ý người dùng, đắt hơn lợi.

### 3.3 Test đường khởi động

Test dựng runtime **dưới `AGENT_DATABASE_URL`** (user thuộc role đọc của agent), khẳng định: kết nối mở được, `LLMSettings.from_env()` còn đúng tên trường, `timeout_s` thật sự bằng `CHAT_TIMEOUT_S`. **Đỏ trước:** đổi tên trường trong bản nháp phải làm test đỏ.

---

## 4. Seam sẽ test *(§4.5.2 — chốt cùng spec)*

| Seam | Vì sao là seam thật |
|---|---|
| `system_prompt.build_system_blocks()` | Ranh giới public mà `chat.run_turn` đi qua — kiểm **số block và thứ tự** |
| `chat.la_lenh_moi()` | Hàm thuần, quyết định hành vi `/moi` |
| `repl()` với `input` giả | Kiểm `/moi` thật sự xoá lịch sử giữa hai lượt |
| Đường khởi động `agent.__main__` | §3.5: mọi đường tiến trình production đi qua, đọc lẫn ghi |

**Không** test câu chữ prompt bằng so chuỗi cứng — luật có tác dụng hay không do **bộ hồi quy** trả lời, không do `assert "cấm" in prompt` (test tautological, §4.5.3).

---

## 5. Nợ #7 — một làm, hai đóng bằng lý do

| Mục | Xử lý |
|---|---|
| ~20 % payload chuỗi giá là dữ liệu dư | **Làm trong lát này**: đo lại phần dư rồi cắt — đúng tầng đọc |
| `ops.llm_call` ghi qua role `dlck_etl` | **Đóng bằng lý do — *đã có đường khác***: đúng cho vòng chat terminal, sai cho service; tách `dlck_chatlog` là việc của lát dựng API |
| `news.trade_name` rỗng | **Đóng bằng lý do — *loại có chủ đích ở tầng này***: seed tên thương mại là việc ETL tin |

---

## 6. Tiêu chí nghiệm thu

| | Nội dung | Bằng chứng phải dán |
|---|---|---|
| AC1 | Toàn bộ test xanh | số trước (**1.025 passed, 2 skipped**) / sau |
| AC2 | **Bộ hồi quy vòng 8** — đúng 15 câu, đúng rubric vòng 7: **số 15/15** và **hình dạng ≥ 14/15** | bảng chấm hai lớp + transcript |
| AC3 | Không câu nào nêu tỷ trọng/điểm mua cụ thể | rubric mục 4 + `git grep` cụm hành động trên transcript |
| AC4 | Lượt A/B `REMINDER`: cùng 15 câu, không nhắc | hai bảng chấm cạnh nhau + kết luận giữ/bỏ |
| AC5 | `/moi` xoá lịch sử | test seam + một lượt chạy tay |
| AC6 | Test khởi động dưới đúng role production, **đỏ trước xanh** | output pytest hai lần |
| AC7 | Review độc lập hai trục, không Critical còn mở | báo cáo reviewer |
| AC8 | Chi phí lượt chạy | truy vấn `ops.llm_call` |

---

## 7. Chi phí và thời gian

Một lượt hồi quy ≈ **$0,25**, ~10–15 phút **tiền cảnh** (job gọi model chạy nền bị đóng băng — lát 10 đã trả giá). Lát này dự kiến **hai lượt** (AC2 và AC4) ≈ **$0,5**; mỗi lần sửa rồi chạy lại thêm ≈ $0,25.

---

## 8. Tài liệu sống phải sửa cùng lượt *(§1.6, §1.7)*

`20-design/chatbot-semantic-layer.md` (khối luật mới, thứ tự block) · `backend/README` (lệnh `/moi`) · `roadmap` (bảy nợ → trạng thái; `ops.llm_call` chuyển sang lát API) · ledger cùng thư mục.

---

## 9. Bốn điểm đã chốt (2026-09-07)

Chủ dự án nghe lý do rồi giao chốt theo đề xuất — ghi lại nguyên trạng để sau này truy được **ai quyết, quyết gì**:

| # | Chốt | Lý do gọn |
|---|---|---|
| 1 | Câu chữ ba đoạn ở §3.1 **giữ nguyên** | Chép sát tiêu chí rubric: dạy và chấm phải cùng một câu, nếu không lượt chạy không nói lên gì |
| 2 | **Giữ** đoạn giữa (phân biệt nguồn số) dù nằm ngoài hai nợ đã nêu | Mẫu hỏng lặp nhiều nhất (5/15 câu), cùng khối nên giá bằng 0; để sau tốn nguyên một lượt $0,25 |
| 3 | `ANSWER_RULES` là **block riêng** | `TOOL_RULES` tự khai chỉ nói cách dùng công cụ **và mang ngày hôm nay** ⇒ nhét luật ổn định vào đó là mỗi ngày tự huỷ cache |
| 4 | Nợ #7 **tách ba** như §5 | Sửa `ops.llm_call` bây giờ là đẻ role cho caller chưa tồn tại (§4.4.2) |

**Rủi ro đã nêu trước khi làm:** chốt 2 làm lượt vòng 8 có **ba** biến thay vì hai; rubric chấm ba mục riêng nên vẫn quy được trách nhiệm, nhưng nếu vòng 8 **tệ đi** thì đây là chỗ nhìn đầu tiên.

### (Nguyên văn phần hỏi, giữ làm ngữ cảnh)

1. **Câu chữ ba đoạn luật ở §3.1** — sửa thẳng vào đây, hay chạy như đang viết?
2. **Đặt `ANSWER_RULES` thành block riêng** thay vì nhét vào `TOOL_RULES` — đồng ý không?
3. **Nợ #7: đóng hai mục bằng lý do** thay vì làm trong lát này — đồng ý không?
4. Ngưỡng dừng nếu vòng 8 **vẫn** dưới 14/15: bạn đã chốt *"chạy thử một lượt rồi tính"* — spec ghi đúng vậy, quyết sau khi có bảng chấm.
