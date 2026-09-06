# Lát 9b-2 — embedding: đo nhu cầu trước, chọn mô hình sau

**Ngày:** 2026-09-06 tối · **Trạng thái:** 🟡 **đề xuất — chờ chủ dự án duyệt** (chọn mô hình/hạ tầng là quyết định khó đảo ngược, CLAUDE.md §4.8; chưa cài gì).

## 0. Dữ kiện đã đo vs giả định *(§4.8 bước 0)*

### Đã đo (2026-09-06, trên chính kho `news.*`, 8.105 bài)

| # | Dữ kiện | Cách đo |
|---|---|---|
| F1 | Gộp theo **tiêu đề y hệt** (khoá dedupe lát 8) chỉ bắt **≈ 0,5 %** bài — 14 gộp / 1.860 bài mới trong ngày | ledger §2.1 |
| F2 | Gộp theo **tiêu đề gần giống** (`pg_trgm`, đã cài, không tốn thêm gì) trên 7.444 bài 30 ngày, cửa sổ 48 giờ, **khác báo**: sim ≥ 0,75 → 77 cặp · ≥ 0,6 → 176 cặp / **146 bài (2,0 %)** · ≥ 0,45 → 602 cặp / **439 bài (5,9 %)** | truy vấn 2026-09-06 21:10 |
| F3 | Mẫu cặp bắt được ở dải 0,5–0,85 đều là **trùng thật**: "Nợ công của Mỹ vượt mốc 40.000 tỷ USD" ↔ "Nợ công Mỹ chính thức vượt mốc 40.000 tỷ USD" (0,73); "MSB chốt quyền chia cổ phiếu thưởng, tỷ lệ 20%" ↔ "Một ngân hàng chốt quyền phát hành cổ phiếu thưởng tỷ lệ 20%" (0,52 — **khác hẳn từ ngữ, vẫn bắt được**) | mẫu 6 cặp |
| F4 | `embo-01` của MiniMax bị chặn dưới Token Plan, 1536 chiều ≠ `halfvec(768)` đã chốt | [minimax.md §8](../../../10-sources/llm/minimax.md) |
| F5 | Kho `news.*` chưa có cột vector; thêm là migration `0020` | `0007`, `0019` |

### Giả định — chưa kiểm

| # | Giả định | Kiểm thế nào |
|---|---|---|
| A1 | Phần trùng mà trigram **bỏ sót** (cùng chuyện, tiêu đề viết khác hẳn, không chung n-gram) đáng kể | lấy 100 cặp bài cùng ngày cùng nhóm/sub mà trigram < 0,45, người/Opus soi xem bao nhiêu là trùng thật |
| A2 | Mô hình 768 chiều tự host chạy đủ nhanh trên máy dev/VPS (350 bài/ngày) | đo sau khi chọn |

## 1. Phát hiện làm đổi bài toán

Embedding vốn được đặt ra để **gộp tin trùng** (news-pipeline §9.5). Nhưng F2 cho thấy **trigram — thứ đã cài sẵn, không tốn tiền, không cần GPU — bắt được gấp 4 đến 12 lần khoá tiêu đề y hệt**, và F3 cho thấy nó bắt cả những cặp diễn đạt khác hẳn. Vậy giá trị *biên* của embedding cho việc dedupe nhỏ hơn nhiều so với giả định ban đầu.

Giá trị thật sự còn lại của embedding là **tìm kiếm ngữ nghĩa cho chatbot** (lát 10: "tin về ảnh hưởng thuế quan Mỹ lên ngành dệt may" — câu hỏi khái niệm mà `tsvector` không bắt được, news-pipeline §9.5). Đó là nhu cầu của lát 10, không phải của pipeline tin.

## 2. Ba phương án

| | A — Trigram trước, embedding sau | B — Tự host mô hình 768 chiều ngay | C — Embedding qua API trả tiền |
|---|---|---|---|
| Trục tối ưu | scope/YAGNI, không thêm hạ tầng | chất lượng tìm kiếm sớm | không vận hành mô hình |
| Làm gì | thêm bước dedupe `pg_trgm` ngưỡng 0,6 vào `news_store.Seen` (một câu SQL, index GIN đã có ở `trade_name`, thêm index cho tiêu đề); embedding để lát 10 quyết theo nhu cầu chatbot | `sentence-transformers` + `multilingual-e5-base` hoặc `vietnamese-bi-encoder`, migration `0020` cột `halfvec(768)` + HNSW, job sinh vector | đổi `LLM_API` sang khoá pay-go dùng `embo-01` (1536 chiều ⇒ phải đổi quyết định `halfvec(768)`) |
| Chi phí | ≈ 0 (đã cài) | +torch ≈ 2,5 GB đĩa, RAM ≈ 1,5 GB khi chạy — VPS 6 GiB/60 GB phải cân | tiền theo lượng + phụ thuộc nhà cung cấp |
| Rủi ro tự khai | bỏ sót phần A1; không phục vụ được tìm kiếm khái niệm | cài hạ tầng cho nhu cầu **chưa chứng minh**; VPS chật | phá quyết định `halfvec(768)`; `embo-01` chưa đo được chất lượng tiếng Việt |

## 3. Đề xuất: **A**, và dời quyết định embedding sang lát 10

Lý do: dedupe — mục tiêu ban đầu của embedding — đã được trigram giải quyết phần lớn với chi phí 0. Nhu cầu còn lại (tìm kiếm khái niệm) thuộc chatbot; chọn mô hình khi biết chatbot hỏi gì thì mới đo được "tốt hay không", còn chọn bây giờ là chọn mù. Loại B vì cài 2,5 GB phụ thuộc cho nhu cầu chưa chứng minh, đúng thứ §4.4.2 cấm. Loại C vì phá một quyết định đã chốt (`halfvec(768)`) để đổi lấy một mô hình chưa đo.

**Điều kiện đảo ngược:** (i) A1 đo ra > 5 % bài trùng mà trigram bỏ sót ⇒ quay lại B; (ii) lát 10 cần tìm kiếm khái niệm ⇒ B, và lúc đó đo mô hình bằng chính câu hỏi thật của chatbot; (iii) VPS có sẵn GPU hoặc RAM dư ⇒ B rẻ hơn.

**Việc kèm theo nếu chọn A** (chưa làm, chờ duyệt): thêm dedupe trigram vào `Seen.decide` (ngưỡng 0,6 — F2/F3 cho thấy 0,45 bắt nhiều nhưng bắt đầu lẫn tin "giá vàng hôm nay" các ngày khác nhau), một index GIN trên tiêu đề chuẩn hoá, và một test seam với đúng cặp trong F3.
