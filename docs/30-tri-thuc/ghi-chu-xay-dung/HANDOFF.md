# HANDOFF — Dự án skill chuyên gia chứng khoán

> ⚠️ **Đường dẫn trong file này là của cấu trúc thư mục cũ** (trước tái cấu trúc 2026-08-14). Nội dung không sửa để giữ nguyên bản ghi lịch sử. Bảng ánh xạ:
>
> | Ghi trong file | Vị trí hiện tại |
> |---|---|
> | `chuyen_gia_chung_khoan/knowledge/` | [`docs/30-tri-thuc/corpus/`](../corpus/) |
> | `chuyen_gia_chung_khoan/documents/` | 🔴 **Đã xoá khỏi repo** — chỉ còn ở bản lưu trữ ngoài |
> | `.claude/skills/…` | [`.claude/skills/`](../../../.claude/skills/) ở **gốc repo** |
> | `scratchpad/…` | Không còn — là thư mục tạm của phiên làm việc cũ |
>
> Xem [ADR 0001](../../00-tong-quan/quyet-dinh/0001-cau-truc-kho-tai-lieu.md).

Tài liệu bàn giao giữa các session. Đọc file này là đủ để tiếp tục, không cần đọc lại lịch sử hội thoại.

**Trạng thái:** Skill 1 (tư duy + văn phong) **đã xong và đã test 5 vòng**. Skill 2 (kiến thức): **Giai đoạn 1 xong** → xem `BAN-DO-KHAI-NIEM.md`. **Giai đoạn 2 đang chạy** (8 subagent Opus).

**Ba quyết định mới của người dùng, ghi đè kế hoạch cũ:**
1. Mức chi tiết skill 2 = **"tự làm được"** (mục 4.4 đã chốt)
2. Subagent Giai đoạn 2 chạy **Opus**, không phải Sonnet — việc này quan trọng, ưu tiên chất lượng
3. **Khái niệm nội bộ: subagent gắn cờ `«...»`, KHÔNG tự chuyển.** Người dùng sẽ tự quyết từng cái sau khi kiến thức đã ra. Đây là thay đổi so với mẫu prompt cũ ở mục 4.6 (vốn bảo subagent tự bỏ tên công cụ).

---

## 1. Bối cảnh dự án

Người dùng có corpus các buổi giảng và trò chuyện của một chuyên gia chứng khoán Việt Nam (học viên gọi là "thầy", tổ chức tên QMV). Mục tiêu: dựng **hai bộ skill tách bạch**:

| Skill | Mục đích | Trạng thái |
|---|---|---|
| `co-van-chung-khoan-vn` | **Tư duy lập luận + hành văn**. Phổ quát, không nặng kiến thức | ✅ Xong |
| `kien-thuc-chung-khoan-vn` | **Kiến thức** từ 6 học phần HP0–HP6 | ⏳ Đã có kế hoạch |

Việc tách hai mục đích là **yêu cầu rõ ràng của người dùng**, không được gộp.

## 2. Cấu trúc dữ liệu nguồn

```
chuyen_gia_chung_khoan/
├── documents/          ~6.5MB  Transcript VERBATIM (Whisper, có timestamp, nhiễu nặng)
│   ├── HP0..HP6/               67 file
│   └── Tra Chieu/              29 file
├── knowledge/          ~2.1MB  Bản AI tóm tắt & hệ thống hoá từ documents/
│   ├── HP0..HP6/               67 file  ← NGUỒN CHO SKILL 2
│   └── Tra Chieu/              29 file  ← ĐÃ DÙNG CHO SKILL 1
└── .claude/skills/co-van-chung-khoan-vn/   ← Skill 1 đã xong
```

**Quy tắc dùng nguồn:**
- Skill 2 **chỉ đọc `knowledge/HP0–HP6`**. Không đọc `documents/` (người dùng đã chốt: không cần văn phong gốc nữa).
- **Trà Chiều KHÔNG đưa vào skill 2** (người dùng đã chốt). Lý do: là nhận định thị trường theo tuần, gần như toàn bộ gắn thời điểm; phần phương pháp đã nằm trong skill 1.

---

## 3. SKILL 1 — Đã hoàn thành

### Vị trí và cấu trúc
```
.claude/skills/co-van-chung-khoan-vn/          769 dòng
├── SKILL.md                       158
└── references/
    ├── van-phong.md               192   từ vựng, ẩn dụ, châm ngôn, 3 ví dụ mẫu
    ├── khung-phan-tich.md         151   khung tối thiểu để lập luận chạy
    ├── tu-duy-lap-luan.md         141   FILE LÕI — 4 tình huống mở đầu
    └── doc-hanh-vi-thi-truong.md  127   tâm lý, thông tin, nhận diện đỉnh
```

### Quyết định thiết kế đã chốt (không được đảo)
- Xưng **"tôi" / "bạn"** (không thầy/em)
- **Bỏ tầng công cụ độc quyền** (Blackbox, QMV Monitor, thang điểm sao, nhãn "nhóm 1/2/3", "dòng tiền 1/2/3")
- **Bỏ hình ảnh dân dã hoá người chơi** ("cáo/thỏ/đệ") → thay bằng **nhà tạo lập / kênh loan tin / nhà đầu tư nhỏ lẻ**
- **Bỏ nhãn nội bộ "x1/x3"** → diễn đạt bằng cơ chế
- **Ma trận 9 ô → hai trục phổ quát**: độ nhạy chu kỳ của ngành × mức rủi ro trong ngành
- Kết luận **luôn có điều kiện** + nêu **điều kiện đổi ý**
- Ngôn ngữ **"sức mua"** thay mua/bán; **không đưa lệnh cho mã cụ thể**
- **Không bịa số**; thiếu dữ liệu thì **kịch bản hoá tối đa 2 nhánh**
- **Không kết bài bằng câu hỏi ngược**
- **Giữ các quan điểm ngược dòng** (đầu tư công không phải bơm tiền; ngân hàng tạo tiền từ hư không; cơ hội nằm ở sự vô lý)

### Kết quả 5 vòng test (25 lần chạy subagent Sonnet độc lập)

| | V1 | V2 | V3 | V4 | V5 |
|---|---:|---:|---:|---:|---:|
| Độ dài TB (câu ngắn) | 390 | 305 | 325 | 275 | **262** |
| Nội dung đạt | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| Can thiệp | — | sửa cấu trúc | thêm rule | **thêm ví dụ mẫu** | bỏ câu rào |

Đã hội tụ ở 250–275 chữ. Dừng vì V4→V5 chỉ còn 5%, ép tiếp sẽ cắt vào phần lõi.

### ⚠️ BÀI HỌC QUAN TRỌNG NHẤT — áp dụng cho skill 2

> **Ví dụ mẫu neo hành vi mạnh hơn mệnh lệnh.**
> Vòng 3 thêm rule về độ dài → cải thiện **0%**.
> Vòng 4 thêm **một ví dụ mẫu ngắn** → cải thiện **15%**.
> Model bắt chước *cỡ và dáng* của ví dụ, không đếm chữ theo lệnh.

Hệ quả cho skill 2: **đầu tư vào ví dụ mẫu tốt hơn đầu tư vào danh sách quy tắc.**

Bài học phụ: **rule chết là rule tốn chỗ.** Từng có rule "không dùng từ cáo/thỏ" — vô nghĩa vì model không có nguồn nào để biết từ đó. Đã xoá.

### Khiếm khuyết còn lại (chấp nhận được)
Câu rào *"tôi không có số liệu hiện tại"* vẫn lọt ở ~2/5 bài dù đã cấm. Trung thực, không gây hiểu nhầm, chỉ hơi thừa.

---

## 4. SKILL 2 — Kế hoạch chi tiết

### 4.1 Số liệu khảo sát đã có (không cần khảo sát lại)

| Chỉ số | Giá trị | Ý nghĩa |
|---|---|---|
| File nguồn | 67 (HP0–HP6) | ~1.5MB |
| Section sau khi lọc | **307** | Đã lọc bỏ "Hỏi đáp", "Bối cảnh", "Điểm thầy nhấn mạnh"… |
| Khái niệm độc lập ước tính | **~200–220** | Sau khi gộp trùng lặp giữa các thế hệ |
| File có *"Bối cảnh thị trường lúc giảng"* | **30/67** | → BỎ NGUYÊN KHỐI |
| File có *"Điểm thầy nhấn mạnh"* | **28/67** | → ĐỌC TRƯỚC, dùng làm xương sống |
| Marker `[?...]` | **111** | ASR không chắc, đã đánh dấu sẵn |
| File nhắc Blackbox / QMV Monitor | **8** | → bỏ tên công cụ, giữ khái niệm |
| Tiêu đề section chứa mã cổ phiếu | **23** | → bỏ mã và số, giữ phương pháp |

### 4.2 Ba cơ chế kiểm soát chất lượng có sẵn trong `knowledge/`

Đây là điểm mạnh của corpus — khai thác thay vì tự dựng:
1. **"Bối cảnh thị trường lúc giảng"** → nội dung gắn thời điểm đã bị cách ly sẵn
2. **"Điểm thầy nhấn mạnh"** → phần đúc kết sẵn
3. **`[?...]`** → chỗ nghe không chắc đã lộ diện sẵn

### 4.3 Rủi ro và cách chặn

**Rủi ro 1 — Nhiều thế hệ giáo trình (nguy hiểm nhất).**
Corpus không phải một khoá học mà là nhiều thế hệ dạy lại cùng nội dung:
`V1 2022` · `V2 2023` · `V3 2022-10 / 2023-04 / 2023-06` · `V4 2022-11 / 2023-01` · `Ứng dụng 2024` · `Version đặc biệt 2024` · `Bài 1–4` (HP0)

Ví dụ mâu thuẫn thật đã gặp: **danh mục tối ưu — HP5 nói 10–15 mã, Trà Chiều nói 6–8 mã.** Không phải sai, mà là hai bối cảnh khác nhau.

Quy tắc xử lý:
- Bản **mới nhất thắng** khi mâu thuẫn về phương pháp
- Bản **chi tiết cũ** bổ sung chiều sâu, không ghi đè kết luận
- Mâu thuẫn thật → **ghi cả hai kèm điều kiện áp dụng**

**Rủi ro 2 — Thiếu kiến thức.** Chặn bằng checklist cơ học:
```bash
grep -h "^## " knowledge/HP*/*.md | sed 's/^## //' | sort -u > inventory.txt
```
Mỗi mục phải kết thúc ở một trong ba trạng thái: *đã đưa vào* / *trùng mục khác* / *cố ý bỏ + lý do*. Nộp bảng đối chiếu cho người dùng duyệt.

**Rủi ro 3 — Số liệu chết.** Toàn bộ số liệu là 2022–2024.
- ✅ Giữ: công thức, định nghĩa (*"số nhân tiền = 1 / tỷ lệ dự trữ bắt buộc"*)
- ❌ Bỏ: quan sát tại thời điểm (*"số nhân tiền khoảng 33 lần"*, *"PE ngân hàng 8,06"*)

### 4.4 Mức chi tiết — ĐÃ KHẢO SÁT, CHỜ NGƯỜI DÙNG CHỐT

Đã đọc bài DCF của HP3 để đánh giá. Kết luận: **giáo trình dạy ở mức "tự làm được"**, không phải "đọc hiểu kết quả người khác". Bằng chứng:
- Phân biệt **FCFF vs FCFE** bài bản, giải thích vì sao FCFF từ EBIT còn FCFE từ lợi nhuận sau thuế
- Quy trình **4 bước** mỗi loại, xử lý vốn lưu động / khấu hao / nợ dài hạn mới
- **WACC, CAPM**, phân biệt chi phí vốn chủ vs chi phí nợ
- Chỉ rõ **lấy từng con số ở báo cáo nào**
- Thêm: residual income, mô hình cổ tức, định giá so sánh 5 bước, quy trình định giá 7 bước, bóc tách ROE, **3 hướng dẫn đọc BCTC riêng cho ngân hàng / chứng khoán / bảo hiểm**

**Đề xuất (chờ xác nhận):** giữ mức "tự làm được". Công thức không lỗi thời, và độ sâu này chính là giá trị corpus. Chỉ cắt ví dụ minh hoạ gắn mã và số cụ thể (VCB/BIDV, PVD, BSR, HPG) → thay bằng ví dụ trung tính.

👉 **CÂU HỎI DUY NHẤT CẦN NGƯỜI DÙNG TRẢ LỜI TRƯỚC KHI VIẾT:**
Giữ mức "tự làm được" (~1.900 dòng) hay gọn hơn (~1.200 dòng)?

### 4.5 Kiến trúc đề xuất

```
.claude/skills/kien-thuc-chung-khoan-vn/
├── SKILL.md                        ~150   bản đồ khái niệm + định tuyến + quy tắc đọc số liệu
└── references/
    ├── vi-mo-va-tao-tien.md        ~250   HP2: M0–M3, dự trữ, số nhân tiền, chính sách, chu kỳ
    ├── doc-bao-cao-tai-chinh.md    ~250   HP3: 3 báo cáo, ROE, đòn bẩy + phụ lục ngành tài chính
    ├── dinh-gia.md                 ~280   HP3: DCF (FCFF/FCFE), so sánh, cổ tức, residual income, CAPM
    ├── ky-thuat-cung-cau.md        ~200   HP4: VPA, giá–lượng, hỗ trợ kháng cự, nến, gap
    ├── ky-thuat-chi-bao.md         ~200   HP4: chỉ báo, mẫu hình, phân kỳ, Dow, sóng
    ├── danh-muc-va-luan-chuyen.md  ~200   HP5: đa dạng hoá, rủi ro, đòn bẩy kép, luân chuyển
    ├── tam-ly-va-thong-tin.md      ~180   HP1: trò chơi, bất cân xứng, tài chính hành vi
    └── nang-cao.md                 ~180   HP6: Fama-French, APT, hedging phái sinh
```

**Lưu ý:** HP0 là nhập môn → tan vào SKILL.md. **HP6 phải có file riêng** — nó chứa khối kiến thức nâng cao độc lập (Fama-French 3 & 5 nhân tố, APT, hạn chế CAPM, hedging bằng hợp đồng tương lai, Open Interest) không thuộc HP nào khác.

**Điểm nối với skill 1:** thêm một dòng trong `co-van-chung-khoan-vn/references/khung-phan-tich.md` trỏ sang skill kiến thức khi người dùng hỏi sâu. Hai skill bổ sung nhau, không chồng lấn.

### 4.6 Quy trình thực thi

**Giai đoạn 1 — Kiểm kê.** Sinh `inventory.txt` bằng grep, phân loại, phát hiện trùng lặp, đưa người dùng duyệt bản đồ trước khi viết.

**Giai đoạn 2 — Trích xuất song song.** 8 subagent, mỗi con một file đích. **Mẫu prompt cố định:**

> Đọc các file trong `knowledge/<HP>`. **Bỏ qua hoàn toàn** mọi section "Bối cảnh thị trường lúc giảng". Với mỗi marker `[?...]`: hoặc bỏ luận điểm, hoặc ghi rõ là không chắc. Không dùng tên công cụ độc quyền (Blackbox, QMV Monitor, thang điểm sao, nhãn nhóm 1/2/3). Trả về:
> 1. Danh sách khái niệm + định nghĩa gọn
> 2. Cơ chế/công thức — **không kèm số liệu thời điểm**
> 3. Quy tắc áp dụng
> 4. Mâu thuẫn giữa các thế hệ giáo trình, ghi rõ file nào nói gì

**Giai đoạn 3 — Ghép và soát chéo.** Không giao subagent. Kiểm khái niệm xuất hiện ở nhiều HP có nhất quán không (ví dụ "dòng tiền" ở HP4 kỹ thuật phải khớp HP5 danh mục), đối chiếu ngược `inventory.txt`.

**Giai đoạn 4 — Test.** Khác skill 1: kiến thức **kiểm được đúng/sai**. Hỏi subagent các câu có đáp án xác định, đối chiếu ngược corpus.

---

## 5. Nguyên tắc làm việc người dùng đã đặt ra

Áp dụng cho mọi việc tiếp theo:

- **Cô đọng và tổng quát hoá.** Không thêm nhiều rule gây dài skill.
- **Tránh sa vào edge case** hoặc ép kiểu không hợp lý.
- **Không hỏi lại nhiều.** Tự chạy vòng lặp tối ưu tới khi đạt; chỉ dừng hỏi khi thực sự bế tắc.
- **Trình bày kế hoạch trước khi viết** khi việc lớn, để duyệt.
- Test bằng **subagent Sonnet độc lập**, mỗi vòng ~5 câu, gồm cả câu lạ ngoài kịch bản dựng sẵn.
- Không rào đón, không giảng đạo lý — trong skill lẫn trong cách làm việc.

---

## 6. Việc tiếp theo

1. ~~Chốt mức chi tiết~~ → **"tự làm được"**
2. ~~Giai đoạn 1~~ → xong, `BAN-DO-KHAI-NIEM.md`
3. ~~Giai đoạn 2~~ → xong, 8 subagent Opus
4. ~~Duyệt khái niệm nội bộ~~ → xong, `QUYET-DINH-THUAT-NGU.md`
5. ~~Giai đoạn 3~~ → xong, skill đã dựng tại `.claude/skills/kien-thuc-chung-khoan-vn/`
6. ~~Nối skill 1 ↔ skill 2~~ → xong, dòng dẫn trong `khung-phan-tich.md`
7. **Giai đoạn 4 — CÒN LẠI.** Test đúng/sai bằng subagent **Sonnet** (không cần Opus, test là kiểm đúng/sai). Mỗi vòng ~5 câu có đáp án xác định, đối chiếu ngược corpus, gồm cả câu lạ ngoài kịch bản.

### Vòng rà soát nhất quán hai skill (sau Giai đoạn 3)

Một subagent Opus rà cả 14 file, sửa **56 chỗ**, để lại **10 vấn đề** cần người quyết (`scratchpad/ra-soat-nhat-quan.md`, bảng A/B/C).
Đã sao lưu trước khi giao (`scratchpad/backup-truoc-ra-soat/` + checksum) nên **diff được từng thay đổi** thay vì tin báo cáo.

Kết quả kiểm chứng: 13/14 file bị đụng, skill 1 giảm còn 4 file bị sửa (đều là đồng bộ thuật ngữ + 1 sửa blockquote hỏng). Skill 1 **772 dòng**, skill 2 **2.261 dòng** — không phình.

Ba việc đáng ghi:
- **Fama-French từng bị phát biểu sai** ở `dinh-gia.md` ("FF3 = Size, Value, Momentum"). Đã sửa: momentum là của **Carhart**, không phải Fama-French.
- **Bảng phân nhóm ngành ở `vi-mo` tự mâu thuẫn** (một ngành nằm hai bậc) và lệch với `danh-muc`. Đã xử: `vi-mo` giữ **tiêu chí phân bậc**, `danh-muc` giữ **danh sách 19 ngành** — vì nguồn HP2 tự nhận là "phân loại tương đối" còn HP5 có xếp hạng chấm điểm.
- **Phép thay thế máy móc bằng sed ở Giai đoạn 3 có sinh lỗi** ("cổ phiếu cổ phiếu", chữ hoa giữa câu). Vòng rà soát dọn hết. Lần sau thay thuật ngữ hàng loạt thì phải đọc lại câu, không chỉ đếm tồn dư.

### Vòng audit 2 — tổng quát hoá cho hệ thống dữ liệu (sau vòng rà soát nhất quán)

Người dùng chốt: **không được cố định danh sách ngành**, vì khung ngành chuẩn sẽ do hệ thống dữ liệu cung cấp sau. Đã gỡ ở 9 chỗ (`CAN-SUA.md` phần A) và audit lại toàn bộ với bốn loại cứng nhắc: chốt cứng danh mục phân loại · chốt cứng ngưỡng số · giả định nguồn dữ liệu · quy trình cứng.

Subagent Opus sửa **17 chỗ**, +2 dòng. Đã diff với `scratchpad/backup-truoc-audit2/` — không mất mục nào trong danh sách phải-giữ.

**Nguyên tắc đã áp, giữ cho các lần sau:**
- Bảng phân bậc nêu **tiêu chí**, không nêu danh sách. Xếp một ngành cụ thể thì **chấm bốn thành phần rủi ro** rồi chia dải làm ba.
- Sáu tiêu chí phân bậc dòng tiền là **bộ tối thiểu, không phải bộ đóng** — thêm tiêu chí được, thiếu vẫn xếp được.
- Ngưỡng số phải ghi rõ là **quy ước** và nêu điều kiện đổi. Đặc tả hợp đồng phái sinh phải tra tại thời điểm dùng.
- Viết sao cho **đúng cả khi có công cụ tra dữ liệu lẫn khi không có**.

**Ba lỗi vòng này bắt được:**
- **Danh sách 19 ngành sống lại** ở `vi-mo` — nó trỏ sang bảng đã bị gỡ ở vòng trước. Vừa là liên kết chết vừa tái lập cái cứng nhắc vừa bỏ.
- **Ichimoku:** skill 1 biến thành luật cứng trong khi **nguồn đưa nó vào để chứng minh nó chỉ là các đường trung bình khoác vỏ phức tạp**. Đã tách luật khỏi tên công cụ, giữ ba trạng thái.
- **Phân kỳ dương:** skill 1 viết như điều kiện bắt buộc, skill 2 nói rõ chỉ tăng độ tin cậy. Đã sửa skill 1 thành thang độ tin cậy cộng dồn.

### Kiến trúc phân tầng (người dùng chốt sau vòng audit 2)

Hai skill **không song song mà xếp tầng**, tải theo độ phức tạp câu hỏi. Skill 3, 4 sau này theo cùng hợp đồng.

| Tầng | Skill | Tải khi |
|---|---|---|
| **L1** | `co-van-chung-khoan-vn` | Mọi câu về chứng khoán VN — luôn có mặt |
| **L2** | `kien-thuc-chung-khoan-vn` | Chỉ khi cần một con số, công thức, hay quy trình tính |
| **L3+** | hệ dữ liệu, khung ngành | Khi cần dữ kiện thật mà chỉ nó có |

**Luật phân định, tự phân xử:** nội dung chấm được đúng/sai mà không cần biết ai hỏi và thị trường thế nào → L2. Còn lại → L1.

**Luật thứ hai, kiểm được bằng máy:** L1 giữ bản mỏng ở mức **kết luận**, cấm ở mức **cơ chế**. Câu trong L1 chứa **công thức, số bước, hoặc ngưỡng số** là sai chỗ.
⚠️ Khi quét kiểm, nhớ bắt cả cơ chế viết bằng **chữ** ("thứ hai", "ba bước") — quét chữ số thôi sẽ sót.

**Luật thứ ba:** câu cần cả hai tầng thì **L2 cấp nội dung, L1 quyết định hình dạng** câu trả lời.

### Giai đoạn 4 — test hệ hai tầng

Test **cả hệ**, không test riêng skill 2. Mỗi vòng 10 câu cho subagent Sonnet, nó tự chọn skill. Bài lưu ở `scratchpad/test-v*.md`.

| Vòng | Lỗi | Nội dung |
|---|---:|---|
| 1 | 2 | "Điểm chạm thứ hai" mâu thuẫn xuyên tầng (còn ở 4 chỗ) · thiếu luật cho câu cần cả hai tầng |
| 2 | 1 | Luật số mã bị áp **ngược chiều** vì bảng thiếu ca "người mới, vốn nhỏ" |
| 3 | 0 | — |
| 4 | 1 | Ngưỡng "biên ròng dưới 20%" sót trong L1 (tồn từ audit B5) |
| 5 | 0 trong tầm skill | Phạm vi + chế độ. Lộ ra **lỗi kiến trúc** (xem mục dưới), không sửa được trong skill |
| 6 | 0 | **Tính toán trên số liệu thật — 10/10 đúng** |

**Vòng 6 là vòng quan trọng nhất** vì nó kiểm đúng lời hứa "tự làm được" — thứ khiến skill 2 dày 2.271 dòng thay vì 1.200. Đưa số liệu, bắt tính ra kết quả. Tôi tự giải trước rồi đối chiếu: khớp cả 10.

Đáng chú ý nhất: **FCFF ra 260 tỷ, không phải 380**. Nghĩa là bản sửa lỗi tính trùng khấu hao **giữ được dưới áp lực tính toán** — nếu ai đó "sửa ngược" về công thức gốc của nguồn thì con số sẽ lệch hẳn. Đây là phép thử hồi quy tốt nhất cho lỗi đó, dùng lại được về sau.

**Kết luận: dừng tối ưu.** Hai vòng liên tiếp không tìm thấy lỗi trong tầm skill, mọi lỗi đã sửa không tái phát (vòng 3 xác nhận lại vòng 1, câu 2 vòng 3 xác nhận lại vòng 2, vòng 6 xác nhận lại lỗi FCFE). Cùng tiêu chí dừng như skill 1 hồi trước: ép thêm sẽ cắt vào phần lõi.

**Rủi ro còn lại, chấp nhận được:**
- L2 không có luật độ dài. Một câu ra 1.035 chữ — nhưng đúng lúc người dùng xin "chi tiết từ đầu tới cuối", các câu khác đều 210–300 chữ. Chỉ đặt luật nếu thấy nó dài vô cớ.
- Định dạng disclaimer lúc in nghiêng lúc không. Không ảnh hưởng nội dung.
- Vài mâu thuẫn nội tại khác của corpus (khung gap, quy đổi kỳ hạn MA) chưa bị hỏi trực diện.

**Nguyên tắc tối ưu người dùng đặt:** tổng quát hoá và cô đọng luật **đang có**, viết hiệu quả hơn — **không thêm luật vô tội vạ**. Ví dụ vòng 2: thay vì thêm dòng vào bảng số mã, tổng quát hoá luật thành *"bị chặn trên bởi tần suất giao dịch **và** sức theo dõi, lấy cái nào chặt hơn"* — ca người mới nằm trong luật thay vì thành ngoại lệ.

**Đã thêm luật phạm vi** (L1 §Ranh giới): chỉ làm chứng khoán, tài chính, kinh tế. Ngoài phạm vi thì từ chối một câu rồi dừng, **không cố lái ngược về chứng khoán cho có việc**. Câu nửa trong nửa ngoài thì trả lời phần trong.

### ⚠️ Luật phạm vi KHÔNG chặn được câu ngoài hẳn — phải đặt ở system prompt

Vòng 5 chứng minh: luật nằm trong thân `SKILL.md` chỉ đọc được **sau khi đã tải skill**, mà câu ngoài phạm vi thì **không kích hoạt skill nào**, nên luật không bao giờ tới đúng lúc. Kết quả 3/4 câu ngoài phạm vi vẫn được trả lời đầy đủ — kể cả viết trọn một đoạn code Python.

Bằng chứng chẩn đoán đúng: câu hỏi **nửa trong nửa ngoài** (bóng đá + cổ phiếu ngành thể thao) thì skill được tải và **tách đúng hai vế**. Luật hoạt động khi skill tải, vô hiệu khi không.

**Kết luận: skill không thể là người gác cổng cho chính nó.** Khi dựng sản phẩm, dán đoạn sau vào **system prompt**, không nhét thêm vào skill:

> Bạn chỉ trả lời trong lĩnh vực chứng khoán, tài chính và kinh tế: thị trường và cổ phiếu, doanh nghiệp niêm yết, vĩ mô, chính sách tiền tệ và tài khoá, các loại tài sản tài chính và quan hệ giữa chúng.
>
> Câu hỏi ngoài lĩnh vực đó — sức khoẻ, pháp lý, lập trình, ẩm thực, đời tư, kiến thức phổ thông — từ chối gọn trong một câu, nói rõ bạn chỉ làm mảng này, rồi dừng. Không giải thích dài, không xin lỗi, không đưa lời khuyên thay thế, và không lái ngược về chứng khoán cho có việc.
>
> Câu nửa trong nửa ngoài: trả lời phần thuộc lĩnh vực, nói một câu rằng phần còn lại không thuộc chỗ mình.

Luật trong L1 §Ranh giới **vẫn giữ** vì nó xử lý tốt ca nửa trong nửa ngoài — ca phổ biến hơn nhiều so với ca ngoài hẳn.

### Trạng thái skill 2

9 file, **2.273 dòng** (SKILL.md 76 + references 2.197). Mọi file trong sai số ±10% ngân sách.
Bao phủ đã kiểm cơ học: **342/342** tiêu đề section gốc đều có dấu vết trong skill.

### Ba việc đã làm ở Giai đoạn 3, ghi lại để khỏi làm lại

- **Hợp nhất ba tên cho cùng một trục.** "nhóm 1/2/3", "lớp 1/2/3" và "dòng tiền 1/2/3" nằm rải ở 3 file, thực ra là cùng hai trục. Đã quy về bộ từ vựng ở `QUYET-DINH-THUAT-NGU.md`.
- **`bash grep` không đọc được ký tự `«` trong locale máy này.** Kiểm tồn dư thuật ngữ **phải dùng PowerShell**, nếu không sẽ báo sạch trong khi còn sót.
- **Hai file dùng tiêu đề không dấu**, đã khôi phục theo tiêu đề trong mục lục.

### Lỗi nguồn đã sửa, đừng "sửa ngược" lại

**Đã xác minh tận file, không phải nghe subagent báo lại.**

- **Công thức FCFE của nguồn tính trùng khấu hao.** Subagent đã sửa: *đầu tư vốn gộp = chênh lệch TSCĐ ròng + khấu hao trong kỳ*. Ví dụ trong file áp dụng đúng. ✅ đã kiểm
- **«nội giải» là lỗi nhận dạng giọng nói**, thực ra là *biên độ cây nến*. Xuất hiện đúng 1 lần trong transcript gốc nhưng bản tóm tắt nâng thành thuật ngữ dùng 10 lần. Đã thay hết.
  ⚠️ **Nhưng mâu thuẫn doji KHÔNG phải ảo** — hai nguồn thật sự đọc ngược nhau về doji có biên độ lớn. Cách hoà giải hiện dùng: *thân ngắn + biên độ **lớn** = lưỡng lự; thân ngắn + biên độ **ngắn**, không bóng = xu thế chắc chắn, tiếp diễn*. Nhất quán với ba yếu tố đọc nến. Nếu muốn chắc, kiểm lại bản gốc `Ứng dụng 2024 CD2`.
- **Quy đổi "50 ngày = 1 tháng" của Version đặc biệt là sai.** Đúng: 5 ngày ≈ 1 tuần, 20 ngày ≈ 1 tháng, 50–60 ngày ≈ 1 quý, 200 ngày ≈ nhiều quý. Subagent đã bỏ sẵn, file không chứa con số sai. ✅ đã kiểm
- **Gap: `ky-thuat-chi-bao.md` đúng, `ky-thuat-cung-cau.md` từng sai và đã sửa ở Giai đoạn 3.** Bảng phân loại bốn loại gap giờ **chỉ nằm ở `ky-thuat-chi-bao.md`**; file cung cầu trỏ sang, không giữ bảng riêng. Theo nguồn: *đột phá* = sau đoạn tăng đầu tiên rồi có vùng lưỡng lự, có tin thay đổi nền tảng; *tiếp diễn* = giá mới tăng lại sau một đoạn giảm, "tăng trong nghi ngờ"; *hết hơi* = sau đoạn tăng dài, khối lượng **cực lớn**, không tin mới. Đây là khung riêng của nguồn, **khác quy ước quốc tế** — đừng "sửa" theo sách tây.
- **P/E và mức an toàn không đơn điệu.** Đã thêm câu phân biệt *P/E cao do tăng trưởng* với *P/E cao do lợi nhuận sụp về gần 0*.

Toàn bộ **65 mâu thuẫn** trong phụ lục 8 file đã duyệt hết ở Giai đoạn 3. Phụ lục lưu tại scratchpad `phuluc/`.

**Cảnh báo phương pháp:** tầng `knowledge/` có thể **khuếch đại nhiễu ASR** — một từ nghe nhầm xuất hiện 1 lần trong transcript có thể thành thuật ngữ dùng nhiều lần trong bản tóm tắt. Gặp thuật ngữ nghe lạ, luôn đối chiếu ngược `documents/`.

### Ngân sách dòng đã đo (không phải ước lượng)

Tổng nội dung trong phạm vi **875.415 byte**, nén 3,5:1 xuống 2.150 dòng.
Chi tiết và lý do lệch tỷ lệ ở `BAN-DO-KHAI-NIEM.md` mục 3.

Nếu vượt ngân sách: nén `danh-muc` và `tam-ly` (chồng skill 1). **Không cắt** HP3 và `nang-cao`.
