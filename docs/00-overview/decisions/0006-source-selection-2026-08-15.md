# 0006 · Chốt nguồn dữ liệu sau khảo sát 2026-08-15

**Ngày:** 2026-08-15 · **Trạng thái:** đã chốt · **Mở rộng** [ADR 0002](0002-data-source-selection.md) · **Thêm một nhánh vào cây của** [ADR 0005](0005-english-tree.md)

## Bối cảnh

Đợt khảo sát nguồn ngày 2026-08-15 gọi thật khoảng 400 lời gọi trên 9 nguồn. Hồ sơ đo và toàn bộ bằng chứng nằm ở [`docs/superpowers/surveys/2026-08-15-nguon-du-lieu/`](../../90-records/surveys/2026-08-15-nguon-du-lieu/README.md). ADR này chỉ ghi những gì phải **quyết**, không ghi những gì chỉ cần **chép**.

Ba chỗ buộc phải ra quyết định:

| Chỗ buộc quyết định | Vì sao không tự trả lời được |
|---|---|
| **Nhiều nguồn cùng có một chỉ tiêu** | ADR 0002 mới xử tranh chấp BVSC ↔ FiinTrade trong phạm vi Việt Nam. Đợt này thêm nguồn quốc tế cho tỷ giá, vàng, dầu, chỉ số, crypto — không nguồn nào là mặc định, và hai nguồn "lệch nhau" có khi đang đo hai thứ khác nhau |
| **Hai kết luận cũ bị lật ngược** | *"WiChart lệch giá dầu, nên thay"* — con số dựng nên kết luận đó sai vì lỗi parse múi giờ. *"Chỉ số quốc tế lấy từ FiinTrade"* — kết luận cũ dựa trên khảo sát 4 chỉ số, đợt này đo 36. Lật một kết luận đã ghi thì phải để lại vết, nếu không lần sau có người lật ngược lại |
| **Bốn khối có dữ liệu đầy đủ nhưng không muốn dùng** | Chính trong đợt này đã có người gọi thử lại ba khối vốn đã bị loại từ trước và tưởng là phát hiện mới, vì danh sách *"ngoài phạm vi"* chỉ liệt tên mục mà không kèm lý do |

## Quyết định

### 1 · OMO lấy từ **SBV**, Vietstock hạ xuống dự phòng và backfill

Ba đường khả dĩ: WiFeed gói tiền tệ · Vietstock · crawl SBV. WiFeed đóng về mặt kỹ thuật (WiGroup xác nhận không mở thêm API). Vietstock có sẵn trường bơm/hút ròng nhưng **cần đăng nhập** — chủ dự án chốt là rào khó, không đưa vào đường chạy chính. SBV là nguồn gốc, miễn phí, không cần danh tính.

Đánh đổi đã biết và đã chấp nhận: SBV chỉ dựng được chuỗi từ hôm bật crawler trở đi. Vietstock giữ lại đúng cho vai lấp phần lịch sử.

➜ Cách gọi, lược đồ, bốn giới hạn và cách dựng bơm ròng: [`10-sources/macro/sbv-omo.md`](../../10-sources/macro/sbv-omo.md).

### 2 · Giá dầu: **giữ WiChart**, và **lưu cả giao ngay lẫn tương lai**

Chênh khoảng 2% giữa FRED và WiChart/Yahoo **không phải sai số của bên nào** — FRED đo giá giao ngay, WiChart và Yahoo đo giá hợp đồng tương lai, và thị trường đang backwardation. Cấu trúc kỳ hạn WTI đo được xác nhận trực tiếp điều đó.

Nên câu hỏi đúng không phải *"nguồn nào đúng"* mà *"dự án muốn loại giá nào"*. Chủ dự án chốt: **lưu cả hai**, không chọn một.

🔴 Hệ quả bắt buộc: **lược đồ phải có cột phân biệt loại giá.** Trộn chung một cột "giá dầu" sẽ tạo bậc nhảy 2% ngay tại điểm đổi nguồn.

➜ Số đo và cờ lệch của từng chuỗi: [`10-sources/macro/wichart.md`](../../10-sources/macro/wichart.md). Bẫy "giao ngay ≠ tương lai": [`10-sources/market/00-conventions.md`](../../10-sources/market/00-conventions.md).

### 3 · Tỷ giá: **Frankfurter chính, Yahoo dự phòng**

Frankfurter phục vụ dữ liệu ECB, mã nguồn mở nên **tự dựng lại được nếu dịch vụ công cộng ngừng** — đó là lý do quyết định, không phải độ tươi hay độ phủ. Yahoo tươi hơn nhưng là dịch vụ đóng, không có đường tự chủ nào; nên nó giữ vai dự phòng và đối chứng.

➜ Cách dựng DXY, sai số nghiệm thu, năm cái bẫy: [`10-sources/global/fx.md`](../../10-sources/global/fx.md).

### 4 · Chỉ số quốc tế: **Yahoo chính**, FiinTrade xuống đối chứng

Đảo vai so với dự định trước. FiinTrade cho ba chỉ số; Yahoo cho 36 chỉ số của 21 nước, lịch sử sâu hơn nhiều bậc. Kết luận cũ *"Yahoo chỉ dùng cho vài mã"* hình thành khi mới khảo sát 4 chỉ số — nó không sai vào lúc viết, nó chỉ dựa trên mẫu quá nhỏ.

⚠️ Ranh giới của quyết định này: Yahoo lên chính **cho chỉ số quốc tế**, không lên chính cho dữ liệu cổ phiếu Việt Nam (độ phủ mã `.VN` thủng ở HNX và UPCOM) và không thay tỷ giá điều hành.

➜ Bảng phủ, ba bẫy cấu trúc, cách nhận biết mã chết im lặng: [`10-sources/global/yahoo.md`](../../10-sources/global/yahoo.md).

### 5 · **Bỏ thư viện `yfinance`** khỏi đường chạy sản xuất, gọi thẳng REST

Thư viện tốn hai lời gọi cho mỗi mã và **tự bung request song song**, tức nó quyết định nhịp thay ta. Dự án có luật *"chạy đúng tải kế hoạch, không dò ngưỡng chặn"* — luật đó không thi hành được nếu tầng dưới tự ý chạy song song. Gọi thẳng REST còn cho phép lấy theo lô, rẻ hơn nhiều bậc cho cùng một tập mã.

Đánh đổi: phải tự làm phần thư viện vẫn làm hộ — ghép lô, phân trang, nhận biết mã chết im lặng.

➜ Cách gọi thẳng và cờ nhận biết: [`10-sources/global/yahoo.md`](../../10-sources/global/yahoo.md).

### 6 · **akshare chỉ dùng backfill một lần**, không đưa vào đường chạy hằng ngày

Toàn bộ nhóm vĩ mô Mỹ của akshare đã chết gần một năm mà vẫn trả HTTP 200, đủ số dòng, không exception, không cờ báo. Đây là dạng hỏng mà mọi kiểm tra kỹ thuật đều xanh — không thể canh bằng giám sát thông thường.

Giá trị còn lại là thật và chỉ một: phần **lịch sử dài mà nguồn chính vĩnh viễn không trả** (nguồn chính cắt cửa sổ). Chạy một lần rồi thôi thì né được đúng ba điểm yếu nặng nhất của nó: chậm, gãy vặt, phải chạy hằng ngày.

➜ Vì thế **cố ý không lập file cho akshare trong `10-sources/`** — nó không phải nguồn vận hành. Ai cần chạy backfill đọc [`report-akshare.md`](../../90-records/surveys/2026-08-15-nguon-du-lieu/report-akshare.md) trong hồ sơ khảo sát.

### 7 · **Loại có chủ đích bốn khối:** chứng quyền · lô lẻ · trái phiếu · realtime FiinTrade

| Khối | Lý do loại |
|---|---|
| **Chứng quyền** | Không phục vụ phương pháp phân tích của dự án |
| **Lô lẻ** | nt |
| **Trái phiếu** | nt |
| **Realtime FiinTrade** | Đã chốt dùng realtime của BVSC — không dựng hai kênh realtime song song |

⚠️ **Ba khối đầu không phải "không có dữ liệu".** Gọi thử trong đợt khảo sát thì cả ba đều trả đầy đủ. Loại vì **không có giá trị phân tích**, không vì thiếu nguồn. Ghi rõ ở đây để lần sau ai rà lại không tưởng là chỗ bỏ sót.

Muốn mở lại thì mở lại **quyết định này**, không phải đi khám phá lại nguồn.

### 8 · Thêm thư mục **`global/`** cho nguồn quốc tế

Cây `10-sources/` trước có ba nhóm: `market/` · `macro/` · `news/`. Chỉ số cổ phiếu quốc tế và crypto **không phải vĩ mô**, nhét vào `macro/` là sai nghĩa và sẽ sai thêm mỗi lần có nguồn quốc tế mới.

Tiêu chí chia nay là **phạm vi địa lý và loại thị trường**, không phải loại chỉ tiêu. SBV vào `macro/` vì đó là vĩ mô Việt Nam; FRED, Frankfurter, Yahoo, LBMA, Binance vào `global/`.

## Hệ quả

**Tốt:**

- Mỗi khối dữ liệu quốc tế có đúng một nguồn chính và một đường dự phòng đã nêu tên — không còn chỗ nào phải quyết lại lúc dựng ETL.
- Bốn khối loại có chủ đích nay có chỗ ghi lý do. Danh sách *"ngoài phạm vi"* ở tầng sống cũng đã tách ba loại *(loại có chủ đích · đã có đường khác · đã kiểm không nguồn nào có)*, nên đọc là biết ngay mục nào đáng mở lại.
- Cây tài liệu có chỗ đặt cho nguồn quốc tế tiếp theo mà không phải quyết định lại.

**Phải chấp nhận:**

- **OMO không backfill được từ SBV.** Mỗi ngày không crawl là mất vĩnh viễn phần dữ liệu ngày đó. Cửa sổ cứu bằng Vietstock có hạn — đây là việc gấp nhất trong các hệ quả của ADR này.
- **Lưu hai loại giá dầu là lưu hai chuỗi.** Mọi biểu đồ, mọi câu trả lời của skill phải nói rõ đang dùng loại nào; không nói rõ thì người đọc tự ghép hai thứ khác nhau.
- **Frankfurter chốt giá theo giờ cố định trong ngày, không phải giá đóng cửa.** Chuỗi dựng từ nó không đặt cạnh chuỗi giá đóng cửa thật được — đó là cái giá của việc chọn nguồn tự chủ được.
- **Gọi thẳng REST là tự gánh phần thư viện đang làm hộ.** Đổi lấy quyền kiểm soát nhịp.
- **akshare không có tài liệu sống.** Ai muốn chạy backfill phải vào hồ sơ khảo sát tìm — cố ý, vì nó không được phép thành nguồn hằng ngày.
- **Bảng ánh xạ cây của ADR 0005 nay có thêm một nhánh.** Đọc riêng ADR 0005 sẽ thấy thiếu `global/`; hai ADR phải đọc cùng nhau.

## Đã cân nhắc và loại

| Phương án | Vì sao loại |
|---|---|
| **Bỏ WiChart cho dầu, ghép chuỗi giao ngay với suất sinh lời của hợp đồng tương lai** | Đã đề xuất rồi rút lại rồi khôi phục theo mục tiêu thay đổi. Nay chốt lưu cả hai loại giá **thô**, nên đây thành việc của tầng thiết kế chuỗi tổng hợp — không phải quyết định chọn nguồn |
| **Thay nguồn vàng bằng LBMA** | LBMA chốt giá theo phiên fixing, khác loại với giá đang dùng. Vai đúng của nó là **mốc chuẩn và backfill lịch sử dài**, không phải thay chỗ |
| **Nghi cả bộ cờ "lệch x%" của WiChart là sai** | Cơ sở nghi ngờ chính là con số sai do lỗi parse múi giờ của người rà. Một cờ đã kiểm trên chuỗi dài và **đúng** — không được suy đoán đồng loạt từ một mẫu hỏng |
| **Lấy chỉ số chứng khoán quốc tế từ FRED** | FRED mạnh ở lãi suất, lạm phát, đồng đô, dầu. Lấy chỉ số cổ phiếu ở đó là dùng sai sở trường của nguồn |
| **Dựng chỉ số đồng đô từ Binance** | Thiếu hẳn vài cặp tiền cần thiết, một cặp đã ngừng. Không dựng nổi thì không có gì để cân nhắc tiếp |
| **Dùng WiFeed cho OMO qua đường dữ liệu công khai của biểu đồ nhúng** | Dữ liệu ở đó là ảnh chụp tĩnh, dừng từ lâu, chưa từng xuất bản lại. Không có rào kỹ thuật nào để vượt vì **dữ liệu không tồn tại** |
| **Giữ nguồn quốc tế trong `macro/` cho khỏi thêm thư mục** | Sai nghĩa ngay từ file thứ hai, và mỗi nguồn quốc tế mới lại phải quyết định lại chỗ đặt — quyết định lặp lại là quyết định chưa chốt |
| **Giữ thư viện `yfinance` nhưng tự siết nhịp** | Không siết được từ ngoài: chính thư viện quyết định bung bao nhiêu request cho một lời gọi |
| **Để bốn khối bị loại nằm im trong danh sách "ngoài phạm vi" như cũ** | Đã thử rồi và đã trả giá: danh sách không kèm lý do khiến người rà mở lại đúng những mục đã loại, đồng thời suýt che mất hai mục thật sự đáng mở |

---

*ADR này theo đúng luật của kho ([ADR 0005](0005-english-tree.md) §4): không tài liệu sống nào trỏ về đây, và mọi tri thức vận hành — endpoint, tham số, lược đồ, bẫy, con số đo — nằm ở các file được nhắc tên phía trên. Xoá cả `decisions/` thì chỉ mất lịch sử vì sao chọn như vậy, không mất cách làm.*
