# Hướng dẫn làm việc trên repo dulieuchungkhoan.vn

File này là **tri thức làm việc của dự án** — luật, quyết định đã chốt, và bài học đã trả giá. Đọc trước khi động vào bất cứ thứ gì.

*(Trước đây các mục này nằm trong bộ nhớ riêng của trợ lý AI. Chuyển vào repo ngày 2026-08-15 vì tri thức dự án phải đi theo dự án, không đi theo một máy hay một phiên làm việc.)*

---

## 1. Luật cứng về tài liệu

### 1.1 Tài liệu sống phải tường minh — không trỏ về ADR

`docs/00-overview/decisions/` **chỉ để tra cứu lịch sử**. Mọi tài liệu sống phải ghi đủ tri thức vận hành ngay tại chỗ.

> **Phép thử:** xoá cả thư mục `decisions/` thì chỉ được phép mất **lịch sử**, không được mất **tri thức vận hành**.

### 1.2 Tầng reference chỉ sửa khi đo lại

`docs/10-sources/` là tầng **reference** — chép sự thật đo được về hệ thống của người khác, không diễn giải.

- Mọi con số **phải kèm ngày đo**: *(đo 2026-08-15)*
- Chưa đo thì ghi **"chưa kiểm"**. **Sửa số mà không đo là nói dối.**

### 1.3 Gọi thật là chưa đủ

Tiêu chí kiểm chứng đúng là **gọi thật + đối chiếu độ tươi với lịch công bố**.

Bài học: akshare gọi thành công, trả đủ 294 dòng, không exception, không cờ lỗi — mà **dữ liệu chết một năm**. Mọi kiểm tra kỹ thuật đều xanh, chỉ có dữ liệu là sai.

### 1.4 Mục "ngoài phạm vi" phải kèm lý do, phân ba loại

| Loại | Nghĩa |
|---|---|
| **Loại có chủ đích** | Có dữ liệu, nhưng không phục vụ phân tích |
| **Đã có đường khác** | Có dữ liệu, nhưng đã chọn nguồn khác |
| **Đã kiểm — không có** | Đã đi tìm và xác nhận không nguồn nào có |

Ba loại trông giống nhau nếu chỉ liệt tên, nhưng **hàm ý hoàn toàn khác** khi ai đó rà lại về sau. Danh sách không có lý do đã từng khiến người rà tốn công mở lại những mục vốn đã bị loại có chủ đích.

### 1.5 Tên tiếng Anh, nội dung tiếng Việt

Tên file và thư mục dùng tiếng Anh *(quyết định 0005)*. Nội dung viết tiếng Việt.

---

## 2. Quyết định đã chốt — đừng mở lại

### 2.1 Pháp lý: chủ dự án tự xử lý, đã xong

**Toàn bộ giấy phép nguồn dữ liệu đã được chủ dự án xử lý xong:**

| Nguồn | Trạng thái |
|---|---|
| BVSC / FiinTrade | Vốn đã được phép |
| WiFeed (WiGroup) | Chốt 2026-08-15, phủ đúng endpoint `api.wichart.vn` đang dùng |
| FRED (St. Louis Fed) | Chốt 2026-08-15 — chủ dự án làm việc trực tiếp, họ đồng ý vì dulieuchungkhoan.vn cung cấp miễn phí |

**Cách ghi trong tài liệu:** chuyện pháp lý chỉ ghi **trạng thái một dòng** (ai, ngày, đã xong). Không thêm câu hỏi mở, không phân tích phạm vi giấy phép, không đề xuất việc pháp lý vào lộ trình.

Có thắc mắc pháp lý thật thì **hỏi thẳng chủ dự án một câu**, đừng ghi vào tài liệu.

### 2.2 Bốn khối dữ liệu loại có chủ đích

| Khối | Lý do |
|---|---|
| **Chứng quyền** (342 mã) | Không có tác dụng cho phân tích |
| **Lô lẻ** (1.890 mã) | nt |
| **Trái phiếu** (187 mã) | nt |
| **Realtime FiinTrade (SignalR)** | Đã chốt dùng realtime của **BVSC**, không dựng hai kênh song song |

⚠️ Ba khối đầu **KHÔNG phải "không có dữ liệu"** — gọi thử `/datafeed/instruments` thì cả ba đều trả đầy đủ. **Loại vì không có giá trị phân tích.** Đừng đề xuất khám phá lại.

### 2.3 Giá dầu: lưu cả giao ngay lẫn tương lai

| Loại | Nguồn | Độ tươi |
|---|---|---|
| Giao ngay | FRED `DCOILWTICO` (EIA Cushing) | trễ 4 ngày |
| Tương lai | WiChart `dau_wti` / Yahoo `CL=F` | T−1 |

Chênh ~2% giữa hai loại là **backwardation**, không phải sai số — xác nhận bằng cấu trúc kỳ hạn *(đo 2026-08-15)*: Sep 82,40 · Oct 81,47 · Nov 80,10 · Dec 78,49.

🔴 **Lược đồ phải có cột phân biệt loại giá.** Trộn chung một cột "giá dầu" sẽ tạo bậc nhảy 2% tại điểm đổi nguồn.

---

## 3. Bẫy kỹ thuật đã trả giá

### 3.1 🔴 Múi giờ WiChart — luôn parse `Asia/Ho_Chi_Minh`

Epoch của mọi chuỗi WiChart là **nửa đêm giờ Việt Nam**:

```
1786726800000  →  2026-08-14 17:00 UTC  →  2026-08-15 00:00 giờ VN
```

Parse theo UTC làm **lệch cả chuỗi một ngày**. Lỗi này đã tạo ra một kết luận sai hoàn toàn *("WiChart lệch giá dầu 3,35%, nên thay" — thật ra 0,50%, không cần thay)*.

### 3.2 🔴 Không viết "đã thử X" nếu chưa chạy X

Một báo cáo trong đợt khảo sát viết *"đã thử ghép ngày d−1, không khớp hơn"* trong khi **chưa hề chạy phép thử đó**. Câu bịa ra để gia cố kết luận lại chính là câu **chặn mất phép kiểm sẽ tìm ra lỗi múi giờ**.

Đây là loại lỗi tự đầu độc: nó không chỉ sai, nó còn ngăn người sau phát hiện cái sai.

### 3.3 Khi "toàn bộ đều lỗi" — nghi tham số của mình trước

Đo độ phủ `iNav` bằng `PageSize=1` → **31/31 lỗi**, suýt kết luận *"FiinTrade không có iNav cho quỹ nào"*. Nguyên nhân: `PageSize` có **whitelist cứng, chỉ nhận `30` và `60`** — đúng cái bẫy tài liệu của chính dự án đã ghi.

**Bẫy đã viết ra vẫn cắn được người viết.** Đọc `docs/10-sources/market/00-conventions.md` trước khi gọi bất kỳ endpoint FiinTrade nào.

### 3.4 Kết luận phủ định về toàn nguồn không suy được từ một endpoint

Tài liệu từng khẳng định *"BVSC không cung cấp dữ liệu phái sinh qua bất kỳ endpoint public nào"* — suy ra từ việc `/quotes` không có mã phái sinh. Quan sát đúng, **suy luận sai**: phái sinh nằm ở `/datafeed/instruments`, 14 hợp đồng, 62 trường.

Muốn kết luận phủ định thì phải **dò từ ứng dụng thật của nguồn** (mở trang, đọc bundle JS), không suy từ một endpoint.

---

## 4. Quy trình làm việc

### 4.1 Việc lớn cần spec và plan

Task lớn thì **viết spec, viết plan cho từng việc**, rồi **giao subagent thực thi và kiểm soát lại** — không tự làm một mạch.

- Spec và plan **lưu trong repo**: `docs/90-records/plans/YYYY-MM-DD-<tên>/`
- Hồ sơ khảo sát lưu ở `docs/90-records/surveys/YYYY-MM-DD-<tên>/`
- Subagent giao cho **Opus**

### 4.2 Song song thì phải cách ly

Nhánh git trong **cùng một checkout KHÔNG cách ly** các agent chạy song song — hai agent đã từng giẫm commit nhau, một `amend` rơi nhầm nhánh.

Hai cách an toàn:
- **Agent ghi file, controller commit** — dùng khi các task sở hữu file rời nhau
- **`git worktree` riêng** — dùng khi task cần tự commit

### 4.3 Đo đạc: chạy đúng tải kế hoạch, không dò ngưỡng chặn

Khi kiểm rate limit: **ước lượng số request cần cho việc thật, chạy đúng mức đó, đủ là được.** Không spam tới khi bị chặn.

Kết luận chỉ được phép ở dạng *"mức tải X an toàn"* — không bao giờ *"ngưỡng là Y"*.

### 4.4 Kỷ luật viết code

*Chưng cất từ [karpathy-guidelines](https://github.com/multica-ai/andrej-karpathy-skills) (khảo sát 2026-08-24 — xem [danh mục repo tham chiếu](docs/00-overview/reference-repos.md)). Thiên về thận trọng hơn tốc độ; việc vặt thì tự cân nhắc.*

1. **Nghĩ trước khi code.** Nêu giả định ra thành lời; có nhiều cách hiểu thì trình bày các cách, không tự chọn ngầm. Thấy cách đơn giản hơn thì nói — kể cả khi phải phản biện yêu cầu.
2. **Tối giản trước tiên.** Không tính năng ngoài yêu cầu, không abstraction cho code dùng một lần, không "cấu hình linh hoạt" không ai xin, không xử lý lỗi cho kịch bản không thể xảy ra. Viết 200 dòng mà 50 dòng đủ thì viết lại.
3. **Sửa như phẫu thuật.** Mỗi dòng thay đổi phải truy được về đúng yêu cầu. Không "tiện tay cải thiện" code lân cận, không refactor thứ không hỏng, theo style sẵn có kể cả khi mình sẽ làm khác. Dọn rác **do chính thay đổi của mình tạo ra** (import/biến mồ côi); rác có sẵn thì báo, không tự xoá.
4. **Chạy theo tiêu chí nghiệm thu.** Biến task thành mục tiêu kiểm chứng được trước khi làm: *"sửa bug" → "viết test tái hiện bug rồi làm nó pass"*. Kế hoạch nhiều bước thì mỗi bước kèm cách kiểm — tiêu chí mạnh cho phép tự lặp đến xong, tiêu chí yếu ("làm cho chạy đi") sinh ra hỏi lại liên tục.

---

## 5. Môi trường

| Mục | Giá trị |
|---|---|
| Nền tảng | Windows 11, PowerShell + Git Bash |
| Python | 3.12 — **luôn đặt `PYTHONIOENCODING=utf-8`**, nếu không sẽ crash cp1252 khi in tiếng Việt |
| Git | `core.longpaths true` *(đã bật — worktree từng lỗi "Filename too long")* |
| Bí mật | `.env` ở gốc repo, đã được `.gitignore` che. **Không bao giờ in giá trị khoá ra output hay ghi vào file.** |
| Email dự án | `dulieuchungkhoan.official@gmail.com` *(tạo 2026-08-24)* — dùng khi đăng ký dịch vụ, khai email liên hệ (User-Agent crawler, API key…). Không phải email cá nhân của chủ dự án |

---

## 6. Bản đồ tài liệu

| Bạn muốn | Đọc |
|---|---|
| Toàn cảnh hệ thống | `docs/00-overview/architecture.md` |
| Biết làm gì tiếp | `docs/00-overview/roadmap.md` |
| Tra một endpoint | `docs/README.md` → `docs/10-sources/` |
| **Sắp gọi API bất kỳ** | `docs/10-sources/market/00-conventions.md` — **đọc trước tiên**, các bẫy triển khai nằm ở đó |
| Sắp sửa skill | `docs/30-skills/maintenance.md` — **bắt buộc**, không phải tham khảo |
| Bằng chứng đo của một con số | `docs/90-records/surveys/` |
| Cân nhắc cài công cụ/skill ngoài | `docs/00-overview/reference-repos.md` — sổ đăng ký repo tham chiếu, **ghi mục mới cùng lượt với việc cài/loại** |
