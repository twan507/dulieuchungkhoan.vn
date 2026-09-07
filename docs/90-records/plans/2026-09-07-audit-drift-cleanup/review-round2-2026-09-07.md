# Vòng review 2 — ba reviewer độc lập soi lại chính đợt dọn

**Ngày:** 2026-09-07 chiều · **Nhánh:** `fix/review-round2` · **Yêu cầu chủ dự án:** *"thả 3 reviewer độc lập, xong lại kiểm lại kết quả từng review rồi mỗi lỗi lại làm 3 bước check sửa test"*

Đợt dọn 47 phát hiện đã merge `main` (`a92462b`). Vòng này thả **ba reviewer chạy song song, ba trục khác nhau**, rồi tôi **tự kiểm lại từng phát hiện bằng lệnh** trước khi tin, và sửa theo đúng ba nhịp **Kiểm → Sửa → Xác nhận**.

## Ràng buộc đặt cho reviewer

| Luật | Vì sao |
|---|---|
| 🔴 Cấm chạy `pytest tests` toàn bộ | Ba agent song song trên **một** DB `dulieu_test` sẽ giẫm nhau và đẻ fail giả — bẫy đã ghi ở `database/README.md`. Chỉ cho `pytest tests/docs` (không đụng DB) và `ruff` |
| 🔴 Cấm gọi API ngoài (R3) | §1.2: số ở `10-sources/` chỉ sửa khi đo lại ⇒ reviewer **không được** kết luận một số đo là sai, chỉ được báo **mâu thuẫn nội bộ** |
| 🔴 Cấm sửa file | Reviewer đọc và báo, người sửa chịu trách nhiệm cuối |
| "Không có" là kết luận hợp lệ | Chặn thói bịa phát hiện cho đủ số |

## Ba trục

| | Soi gì | Kết quả |
|---|---|---|
| **R1 · Chuẩn** | `git diff 46c3d41..HEAD` — luật repo + chất lượng bộ kiểm mới | 1 🔴 · 3 🟡 · 2 ⚪ |
| **R2 · Spec** | 47 mã phát hiện: khai gì / làm gì / khớp không | 0 🔴 · 2 🟡 · 3 ⚪ |
| **R3 · Rà mới** | Vùng đợt trước bỏ sót: `10-sources/market/` 14 file, `wichart.md`, ba file ngành, `30-skills/`, 7 ADR, `deploy/` | 3 🔴 · 1 🟡 · 2 ⚪ |

---

## Phát hiện đã xác thực và đã sửa

Mọi mục dưới đây **tôi tự chạy lệnh tái hiện** trước khi sửa, không tin thẳng báo cáo.

### 🔴 F1 — bộ kiểm chống mồ côi TỰ VÔ HIỆU *(R1)*

`90-records/README.md:16` có câu quy ước *"File bên trong: `spec.md`, `plan.md`, `ledger.md`"*. Luật cũ nhận **"README.md bất kỳ có nhắc tên file"** là đủ ⇒ **mọi** file mang ba tên đó, ở **bất kỳ** thư mục nào, kể cả thư mục chưa hề vào bảng index, đều được tính "có chủ".

**Tái hiện:** dựng `plans/9999-99-99-thu-mo-coi/` với `spec.md` + `bao-cao-la.md`.

```
truoc khi va:  bat duoc bao-cao-la.md  ·  spec.md LOT SACH
sau khi va:    "thu muc plan khong co dong nao trong docs/90-records/README.md: 9999-99-99-thu-mo-coi"
```

AC5 vốn mù đúng ở **ba loại file phổ biến nhất**. Vá bằng cách tách hai vế: (1) thư mục phải có tên trong bảng index; (2) từng file phải được **dòng index của chính thư mục đó** hoặc **file anh em cùng thư mục** nhắc tên — xét theo **dòng**, không theo cả file, nếu không câu quy ước chung lại miễn trừ tất cả.

Vá xong lộ thêm một orphan thật: `.../news-classify-llm/eval/README.md`. Kiểm ra đó là **index của chính thư mục nó** (và `eval/` có được `ledger.md` nhắc) ⇒ miễn trừ `README.md` khỏi phép kiểm từng-file: một index không cần index.

### 🔴 F2 — `feeds.json` là bản lạc hậu nhất, dù tự xưng "bản máy đọc" *(tôi tìm ra khi kiểm F4 của R2; R3 độc lập cũng thấy)*

```
feeds.json taxonomy:  1a–1f (6) · 2a–2e (5) · 3a–3i (9) = 20
code SUBS:            1a–1f (6) · 2a–2f (6) · 3a–3i (9) = 21
migration 0019_sub_2f.py: da co 2f
```

Thiếu `2f`. Không code nào đọc khối `taxonomy` (chỉ đọc `crawl_html`, `_meta`, ba nhóm feed) nên **không hỏng chức năng** — nhưng đây là file được chính README của nó gọi là *"File máy đọc đi kèm"*, tức đúng nghĩa hai-nguồn-sự-thật. Nhãn `2f` lấy **từ file chủ** `news-pipeline.md`, không tự bịa; viết theo đúng style không dấu chữ thường của các mục anh em.

### 🔴 F3 — docstring của chính code nói sai code

`backend/etl/news_classify.py:1` ghi *"taxonomy 3 nhóm / **20** sub"* — ngay **trên** `SUBS` ở dòng 29 có 21.

### 🔴 F10 — "13 bẫy" sống sót ở ba tài liệu sống *(R3)*

Đợt trước đổi tiêu đề `00-conventions.md:169` "Mười ba" → "Mười bốn" rồi **dừng**. Còn `docs/README.md:22`, `10-sources/README.md:103`, `roadmap.md:752` vẫn ghi 13, trong khi `grep -c "^### Bẫy"` = **14**.

### 🟡 F4 — "20 sub" sống sót ở bốn tài liệu sống *(R2, tôi mở rộng)*

`backend/README.md:13` · `10-sources/README.md:145` · `news/README.md:21` · `20-design/README.md:12`.

**Cố ý KHÔNG sửa** *(đều là bản ghi tại-thời-điểm — `2f` thêm ở lát 9b)*: `roadmap.md:30,144` (mô tả lát 9a giao gì; dòng 30 đã có câu 9b *"taxonomy mở rộng (`0019`)"* ngay sau nên đọc vẫn đúng) · `roadmap.md:314,410` (nằm trong mục `~~Điểm vào~~ ĐÃ DÙNG XONG`) · `minimax.md:46,70` (mô tả prompt **lúc đo** 2026-09-06).

### 🟡 F11 — tóm tắt Tier WiChart lệch bảng chủ *(R3)*

`10-sources/README.md:65` ghi *"61 lõi · 6 phụ · 20 loại bỏ"*. Đếm lại bảng §5 của `wichart.md` bằng parser bám đúng cột `Tier` từng bảng: **A = 62 · B = 6** ⇒ X = 87 − 68 = **19**. Nguyên nhân: `ca_tra` chuyển **X → A**, và chính `wichart.md:368` ghi rõ lý do — *"`FROZEN` tại audit 12/08 — **đã sống lại**: (đo 2026-09-05)"*.

🔴 Đây là `10-sources/`, nên phải nói rõ: **không sửa số đo**, chỉ đồng bộ **số dẫn xuất** với bảng chủ đã có đo lại. Ghi kèm lý do ngay tại chỗ.

### 🟡 F12 — bảng chọn trường đã lớn thêm 66 dòng *(R3)*

`10-sources/README.md:161` ghi *"213 dòng"*; `market-field-selection.json` có **279** phần tử và chính file `.md` ghi 279 ở hai chỗ. 213 là số của bản đầu 2026-08-14.

### 🟡 F5 — D11 làm nửa, ledger lại khai trọn *(R1)*

`plan.md:308` đòi **hai** việc: thêm script `test` vào `package.json` **và** nhắc ở `database/README.md`. Chỉ làm việc đầu (`grep "npm test" database/README.md` = 0), nhưng ledger §5 xếp D11 vào *"✅ đã sửa (8)"*. Đã làm nốt vế hai.

### 🟡 F7 — phép cộng sai trong chính file vừa được phong "chủ sở hữu duy nhất" *(R2)*

`database/README.md:92`: *"+7 test `tests/docs`, **+3** test bịt lỗ hổng"* ⇒ 1029+7+3 = 1039 ≠ 1038. Đếm thật `git diff | grep -c "^+def test_"` = **2** — phần NguoiQuanSat là assertion chèn vào hàm sẵn có, không thêm hàm. Số cuối 1038 vẫn đúng, chỉ số hạng sai.

### 🟡 F8 · F9 — gốc rễ: bộ kiểm soi quá hẹp

- **F8** `test_sub_count_matches_code` **chỉ soi `news-pipeline.md`**. Đây mới là lý do F2/F3/F4 tồn tại: đợt trước sửa đúng file audit gọi tên rồi dừng. Nay quét thêm 6 tài liệu sống + docstring code + đối chiếu **từng mã sub** với `feeds.json`.
- **F9** phép kiểm crawl cố ý bỏ dạng `"N crawl"` trần để né câu OMO của SBV — hệ quả là hai ô ASCII (`architecture.md:14`, `news-pipeline.md:38`) nằm ngoài vùng phủ. Nay bắt cả dạng trần, loại trừ đúng một chuỗi `"REST + 1 crawl"`.
- **Mới** thêm `test_trap_count_matches_conventions_headings` — số bẫy nêu ở tài liệu phải khớp `grep -c "^### Bẫy"`, cùng họ với phép kiểm sub.

---

## Ghi nhận, cố ý KHÔNG sửa

| Mục | Lý do |
|---|---|
| `audit.md` ghi *"44 bảng"* mà thật ra 44 là **riêng Postgres**, cộng 7 bảng `rt.*` của ClickHouse là **51** *(R2 + R3 cùng chỉ ra)* | `audit.md` nằm trong `90-records/` — bản ghi tại-thời-điểm, §1.7 chỉ cho sửa href. Ghi đính chính ở đây, chỗ đúng của nó |
| `news-collect/spec.md:5` — đợt trước gỡ link và **thêm chú thích mới** vào file lịch sử, vượt quá "chỉ sửa href" *(R1)* | Nhận là R1 đúng về chữ nghĩa. Giữ nguyên vì: file đích **chưa từng tồn tại** nên không có href nào để sửa, và chú thích có **dán ngày** nên không giả làm nội dung gốc. Đường thay thế (để link chết vĩnh viễn) làm `test_no_dead_internal_links` đỏ mãi |
| `maintenance.md` §8 *"875.415 byte, nén 3,5:1"* — R3 đếm HP0–HP6 ra 1.363.262 byte | Tài liệu không định nghĩa "trong phạm vi" là gì ⇒ **chưa kiểm**, không kết luận sai. Y hệt kết luận của đợt audit đầu |
| Thụt lề lạ trong `gen_industry_mapping.py` *(R1)* | Cú pháp hợp lệ, sinh lại byte-identical. Thuần phong cách |
| ADR 0007 không nối 0005 ở cột "Quan hệ" *(R3)* | 0007 không phủ định 0005; R3 tự xếp là ghi chú, không phải lỗi |

---

## Nghiệm thu

```
pytest tests/docs -q     8 passed          (7 cũ + 1 phép kiểm bẫy mới)
pytest tests -q          1.039 passed, 2 skipped, 89,45 s
ruff check --select F    All checks passed!
npm test                 7/7
sinh lai 4 file generator -> cmp byte-by-byte KHỚP cả 4
```

## Bài học của chính vòng này

**Đợt dọn §1.7 lại vi phạm §1.7.** Audit gọi tên `news-pipeline.md`, tôi sửa đúng file đó rồi dừng — **không `git grep "20 sub"` toàn repo**. Trước lượt sửa, năm chỗ cùng sai nên *nhất quán*; sau lượt sửa chúng **mâu thuẫn nhau**. Ở khía cạnh đó tôi làm tình trạng **tệ đi**. Y hệt với "13 bẫy".

Bài học không phải "cẩn thận hơn" — mà là **phép kiểm phải quét mọi chỗ, vì con người sẽ luôn chỉ sửa chỗ được gọi tên**. Vì vậy vòng này sửa **bộ kiểm trước**, rồi để nó tự liệt kê 5 + 3 vị trí còn lại thay vì tôi phải nhớ.
