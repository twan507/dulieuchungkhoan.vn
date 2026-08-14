# BẢN ĐỒ KHÁI NIỆM — Skill 2 `kien-thuc-chung-khoan-vn`

Kết quả Giai đoạn 1 (kiểm kê). Chờ duyệt trước khi chạy Giai đoạn 2.
Mức chi tiết đã chốt: **"tự làm được"**.

---

## 1. Số liệu kiểm kê

| Chỉ số | Giá trị |
|---|---:|
| File nguồn (HP0–HP6) | 67 |
| Section thô | 460 |
| Section sau lọc khung | **355** |
| Tiêu đề duy nhất | 342 |
| Marker `[?...]` | 111 |
| File nhắc tên công cụ độc quyền | 8 (31 lần nhắc) |
| Tiêu đề chứa mã cổ phiếu | 3 |

Đã lọc bỏ khỏi 460: `Hỏi đáp` (33) · `Điểm thầy nhấn mạnh` (27) · `Bối cảnh thị trường lúc giảng` (28) · `Khuyến nghị đầu tư` (6) · `Dữ liệu kinh tế…` (4) · vài mục khác.

`Điểm thầy nhấn mạnh` **không bị vứt** — lọc khỏi danh sách khái niệm vì là section meta, nhưng vẫn đọc trước để làm xương sống, đúng kế hoạch.

Phân bố 355 section: HP0 43 · HP1 31 · HP2 50 · HP3 83 · HP4 56 · HP5 43 · HP6 49.

---

## 2. Bốn phát hiện làm lệch kế hoạch cũ

### 2.1 HP6 phần lớn là bài ôn, không phải kiến thức mới
Trong 49 section HP6, khoảng **20 là ôn lại HP1–HP5**: *Vĩ mô — hạt nhân nền kinh tế*, *Cơ bản và định giá*, *Kỹ thuật — cung cầu và VPA*, *Hành vi — thông tin không cân xứng*, *Quy trình đầu tư 3 bước và 5 học phần*, *Chu kỳ kinh tế và cách đọc chính sách tiền tệ*…

Kiến thức thật sự mới của HP6 chỉ còn ~15 mục: Fama-French 3 & 5 nhân tố, APT, hạn chế CAPM, hedging bằng hợp đồng tương lai, Open Interest, rebalancing, lưới nhóm ngành × dòng tiền, nhân tố lịch / sự kiện.

**Đề xuất:** `nang-cao.md` chỉ chứa phần mới. 20 section ôn tập chuyển thành **vật liệu soát chéo ở Giai đoạn 3** — chúng là bản đúc kết muộn nhất nên là trọng tài tốt khi các thế hệ giáo trình mâu thuẫn.

### 2.2 Rebalancing bị xếp nhầm file
Kế hoạch cũ để rebalancing trong HP6 → `nang-cao.md`. Nhưng nó là quản trị danh mục thuần tuý. **Chuyển sang `danh-muc-va-luan-chuyen.md`.**

Ngược lại, HP4 có mục *Phái sinh* lẻ loi → **gộp vào `nang-cao.md`** cùng hedging và Open Interest.

### 2.3 HP0 không "tan vào SKILL.md" được
HP0 là một khoá thu nhỏ dạy lại toàn bộ: PE, nến, gap, Dow, luân chuyển ngành, chính sách. 43 section, trùng nội dung HP2/HP3/HP4 nhưng ở mức đơn giản hơn.

**Đề xuất:** HP0 đóng hai vai
- Cấp **bản đồ khái niệm + định tuyến** cho `SKILL.md`
- Cấp **đoạn giải thích mức đơn giản** mở đầu mỗi mục trong file references, trước khi vào mức "tự làm được"

Đây là lợi thế: mỗi khái niệm có sẵn hai tầng độ sâu do chính giáo trình cung cấp, không phải tự chế.

### 2.4 Nhãn "dòng tiền 1/2/3" — nối được với skill 1
HP5 có mục *Sáu tiêu chí đơn giản để phân dòng tiền 1, 2, 3*. Đã đọc: đây là **cơ chế thật, dùng được**, sáu tiêu chí là vốn hoá · thanh khoản · P/E-P/B · cổ tức và thu nhập · thị giá · danh tiếng. Kèm một quan sát ngược dòng đáng giá: ở thị trường Việt Nam P/E–P/B thấp phản ánh **rủi ro** chứ không phải rẻ.

Skill 1 đã bỏ nhãn "dòng tiền 1/2/3" và thay bằng trục **mức rủi ro trong ngành**. **Đề xuất:** giữ nguyên sáu tiêu chí, đổi nhãn thành *rủi ro thấp / trung / cao*. Bỏ mọi câu "tra trên web QMV". Cơ chế nguyên vẹn, khớp trục của skill 1.

---

## 3. Bản đồ 355 section → 8 file

Ngân sách dòng **đo từ dung lượng nội dung thật**, không suy từ số section.
Tổng nội dung trong phạm vi: **875.415 byte**. Tỷ lệ nén xuống 2.150 dòng ≈ **3,5 : 1**.

| File đích | Nguồn chính | Byte | % corpus | Dòng |
|---|---|---:|---:|---:|
| `SKILL.md` | HP0 bản đồ + định tuyến | — | — | 150 |
| `vi-mo-va-tao-tien.md` | HP2 + HP0 bài 1 + HP6 vĩ mô | 146k | 16,7% | 330 |
| `danh-muc-va-luan-chuyen.md` | HP5 + rebalancing HP6 + HP0 bài 2 | 149k | 17,0% | 300 |
| `doc-bao-cao-tai-chinh.md` | HP3 khối BCTC | 118k | 13,5% | 290 |
| `dinh-gia.md` | HP3 khối định giá + HP0 bài 3 | 100k | 11,4% | 300 |
| `ky-thuat-chi-bao.md` | HP4 chủ đề 3–5 + HP6 tín hiệu | 98k | 11,2% | 230 |
| `tam-ly-va-thong-tin.md` | HP1 + HP6 hành vi | 100k | 11,5% | 190 |
| `ky-thuat-cung-cau.md` | HP4 chủ đề 1–2 + HP0 bài 4 | 75k | 8,6% | 190 |
| `nang-cao.md` | HP6 nhân tố giá + hedging + HP4 phái sinh | 42k | 4,7% | 170 |
| | | | | **2.150** |

**Bốn chỗ lệch tỷ lệ, có lý do:**

- `dinh-gia` ↑ và `doc-bao-cao-tai-chinh` ↑ — công thức và quy trình bốn bước không nén theo tỷ lệ như văn nói. Đây là lõi "tự làm được".
- `nang-cao` ↑ mạnh (4,7% corpus nhưng 8% ngân sách) — Fama-French, APT, CAPM là công thức thuần, không nén được.
- `danh-muc` ↓ và `tam-ly` ↓ — hai file này chồng lấn skill 1 nhiều nhất: HP5 top-down đã có trong `khung-phan-tich.md`, HP1 tâm lý đã có trong `doc-hanh-vi-thi-truong.md`. Chỉ viết tầng cơ chế mà skill 1 cố tình bỏ.

**Nếu Giai đoạn 3 vượt ngân sách:** nén tiếp đúng `danh-muc` và `tam-ly` (chồng skill 1). **Không cắt** HP3 — đó là mức "tự làm được" đã chốt. **Không cắt** `nang-cao` — 4,7% corpus, cắt không tiết kiệm được gì mà mất hẳn Fama-French/APT/hedging vì không nguồn nào khác có.

---

## 4. Danh sách BỎ có lý do

**Khung bài, không có nội dung (~20):** *Mở đầu* · *Tổng kết* · *Tổng kết và ghi nhớ* · *Tổng kết 5 chủ đề đã học* · *Tóm tắt cuối buổi* · *Giới thiệu học phần* · *Mục đích của bài học* · *Vị trí của bài trong hệ thống HP5* · *Lý do thực hiện khoá học và cấu trúc buổi học* · *Cộng dồn* · *Tổng quan chương trình QMV* · *Tổng quan học phần 3* · *Tổng quan 5 chủ đề của học phần 4* · *Tổng quan buổi học và bối cảnh học phần* · *Ví dụ và ứng dụng* (5 lần) · *Ví dụ minh hoạ*

Ngoại lệ — bốn mục có chữ "Tổng quan" nhưng **có nội dung phân loại**, giữ lại làm khung mở đầu file: *Tổng quan hai cách tiếp cận định giá* · *Tổng quan về đọc hiểu báo cáo tài chính* · *Tổng quan và hai phương pháp tiếp cận* · *Tổng quan: hai kỹ thuật rào chắn vị thế*

**Gắn thời điểm (4):** *Ứng dụng cho Việt Nam (09/2024)* · *Áp dụng vào thị trường hiện tại* · *Tình trạng 5 nhân tố tại thời điểm buổi học (01/11/2024)* · *Phân tích vùng giao động hiện tại (tháng 10/2024)*

**Hỏi đáp còn sót (2):** *Hỏi đáp về nhân tố giá và phân tích kỹ thuật* · *Hỏi đáp về danh mục và nhận định thị trường*

**Giữ cơ chế, bỏ tên (5):** *Quy trình quản trị lệnh QMV* · *Watchlist Template của QMV* · *Cách tiếp cận của QMV* · *Bốn yếu tố định tính QMV* · *Vị trí của phân tích kỹ thuật trong cách tiếp cận QMV* → giữ nội dung, bỏ tên tổ chức và tên công cụ

**Giữ phương pháp, bỏ mã và số (3):** *Ví dụ và ứng dụng: so sánh VCB và BIDV* · *Ví dụ và ứng dụng: Thực hành trên Blackbox với PVD và BSR* · *Rebalancing hàng ngày: cách chia vị thế và ví dụ HPG* · thêm *Ví dụ rebalancing với VN-Index quanh 1.300 điểm*

**Tổng bỏ hẳn: ~26/355.** Còn lại ~329 section vào skill, trong đó phần trùng lặp sẽ gộp ở Giai đoạn 3.

---

## 5. Sáu điểm trùng lặp phải soát chéo ở Giai đoạn 3

Đây là nơi rủi ro "nhiều thế hệ giáo trình" sẽ bung ra.

| Khái niệm | Xuất hiện ở | Việc phải làm |
|---|---|---|
| Chu kỳ kinh tế – thị trường – tâm lý | HP0, HP2, HP5, HP6 | 4 bản, chọn bản đầy đủ nhất làm chuẩn |
| Định giá / PE | HP0, HP3, HP5, HP6 | HP0 mức đơn giản, HP3 mức tự làm — xếp tầng, không gộp |
| Luân chuyển ngành / dòng tiền | HP0, HP2, HP3, HP5, HP6 | 5 bản. Phân biệt rõ *luân chuyển ngành* ≠ *luân chuyển dòng tiền* (HP5 nói rõ khác biệt cốt lõi) |
| Thông tin không cân xứng | HP1, HP6 | HP6 gọn hơn, HP1 sâu hơn |
| Đòn bẩy | HP3 (lên ROE), HP5 (hoạt động vs tài chính) | Hai góc khác nhau, giữ cả hai |
| CAPM | HP3 (dùng để chiết khấu), HP6 (hạn chế, cần thêm nhân tố) | Nối thành một mạch: dùng → hạn chế → Fama-French |

**Mâu thuẫn thật đã biết:** số mã tối ưu trong danh mục — HP5 nói 10–15, Trà Chiều nói 6–8. Ghi cả hai kèm điều kiện áp dụng.

---

## 6. Ba cơ chế kiểm soát chất lượng, trạng thái

| Cơ chế | Số lượng | Cách dùng |
|---|---:|---|
| `Bối cảnh thị trường lúc giảng` | 28 | Đã cách ly khỏi inventory, subagent được lệnh bỏ qua hoàn toàn |
| `Điểm thầy nhấn mạnh` | 27 | Subagent đọc **trước tiên**, dùng làm xương sống mỗi file |
| `[?...]` | 111 | Mỗi marker: bỏ luận điểm, hoặc ghi rõ không chắc |

---

## 7. Việc kế tiếp sau khi duyệt

1. **Giai đoạn 2** — 8 subagent song song, mỗi con một file đích, dùng mẫu prompt cố định ở HANDOFF mục 4.6, bổ sung ba điều chỉnh ở mục 2 trên đây
2. **Giai đoạn 3** — ghép, soát 6 điểm trùng lặp ở mục 5, đối chiếu ngược danh sách này
3. **Giai đoạn 4** — test đúng/sai bằng subagent Sonnet độc lập, đối chiếu ngược corpus
4. Nối skill 1 ↔ skill 2

**Nguyên tắc mang từ skill 1 sang:** ví dụ mẫu neo hành vi mạnh hơn mệnh lệnh. Mỗi file references phải có **ít nhất một ví dụ tính toán chạy được đầu-cuối** (DCF, bóc tách ROE, định giá so sánh), không phải danh sách công thức rời.
