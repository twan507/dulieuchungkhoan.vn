# 0005 · Tái cấu trúc cây tiếng Anh

**Ngày:** 2026-08-15 · **Trạng thái:** đã áp dụng · **Sửa đổi một phần** [ADR 0001](0001-docs-structure.md) §1/§5

## Bối cảnh

ADR 0001 dựng cây thư mục theo đúng thứ tự tài liệu được sinh ra: ba phiên làm việc, ba khối nguồn gốc, cộng hai thư mục "vai trò" ở gốc. Dự án skill đã đóng ([ADR 0003](0003-close-skill-project.md)), nhật ký phiên đã bỏ ([ADR 0004](0004-drop-session-logs.md)). Phần còn lại lộ ba chỗ sai:

| Chỗ sai | Biểu hiện |
|---|---|
| **Cây kể lịch sử dựng tài liệu, không tả sản phẩm** | Thư mục đặt theo phiên sinh ra chúng. Repo này sắp có frontend, backend, database thật — người mở repo lần đầu thấy `config/` và `scripts/` ở gốc sẽ tưởng đó là config và script của ứng dụng |
| **Tên tiếng Việt không dấu mơ hồ** | `tri-thuc` là tri thức của ai; `thi-truong` với `vi-mo-hang-hoa` phải mở ra mới biết cái nào ứng với nguồn nào; gõ `du` ra ba thư mục. Cây tài liệu tiếng Việt không dấu đứng cạnh cây code tiếng Anh là hai quy ước đặt tên trong một repo |
| **`config/` và `scripts/` là thư mục "vai trò", mỗi cái đúng một file** | `config/feeds.json` là bản máy đọc của chính tài liệu nguồn tin. `scripts/verify_wichart.py` đọc registry 509 khẳng định nằm ngay trong `wichart.md`. Cả hai gắn chặt với **một nguồn cụ thể**, nhưng bị xếp theo *dạng file* nên nằm cách tài liệu của nó hai tầng — sửa tài liệu mà quên file ở gốc thì lệch, và không có gì ở gốc nhắc |

## Quyết định

**1 · Toàn bộ tên file và thư mục sang tiếng Anh. Nội dung file giữ nguyên tiếng Việt** — kể cả heading, mục lục, bảng. Chỉ các chuỗi tên file / đường dẫn / tên skill xuất hiện trong văn bản được thay theo bảng dưới.

**Bảng ánh xạ đổi tên — toàn bộ, nguyên văn:**

### Gốc repo

| Cũ | Mới |
|---|---|
| `config/feeds.json` | `docs/10-sources/news/feeds.json` |
| `scripts/verify_wichart.py` | `docs/10-sources/macro/verify_wichart.py` |
| `config/`, `scripts/` | xoá (rỗng sau khi di chuyển) |

### docs/ — thư mục

| Cũ | Mới |
|---|---|
| `docs/00-tong-quan/` | `docs/00-overview/` |
| `docs/00-tong-quan/quyet-dinh/` | `docs/00-overview/decisions/` |
| `docs/10-nguon-du-lieu/` | `docs/10-sources/` |
| `docs/10-nguon-du-lieu/thi-truong/` | `docs/10-sources/market/` |
| `docs/10-nguon-du-lieu/vi-mo-hang-hoa/` | `docs/10-sources/macro/` |
| `docs/10-nguon-du-lieu/tin-tuc/` | `docs/10-sources/news/` |
| `docs/20-thiet-ke/` | `docs/20-design/` |
| `docs/30-tri-thuc/` | `docs/30-skills/` |

### docs/ — file (basename đổi)

| Cũ | Mới |
|---|---|
| `kien-truc-tong-the.md` | `architecture.md` |
| `lo-trinh.md` | `roadmap.md` |
| `0001-cau-truc-kho-tai-lieu.md` | `0001-docs-structure.md` |
| `0002-chon-nguon-du-lieu.md` | `0002-data-source-selection.md` |
| `0003-dong-du-an-skill.md` | `0003-close-skill-project.md` |
| `0004-bo-nhat-ky-phien.md` | `0004-drop-session-logs.md` |
| `00-quy-uoc-chung.md` | `00-conventions.md` |
| `03-fiin-tham-chieu.md` | `03-fiin-reference.md` |
| `04-fiin-ho-so-doanh-nghiep.md` | `04-fiin-company-profile.md` |
| `05-fiin-bao-cao-tai-chinh.md` | `05-fiin-financial-statements.md` |
| `06-fiin-cham-diem-dinh-gia.md` | `06-fiin-scoring-valuation.md` |
| `07-fiin-dong-tien.md` | `07-fiin-money-flow.md` |
| `08-fiin-lich-su-kien.md` | `08-fiin-event-calendar.md` |
| `09-fiin-gia-thi-truong.md` | `09-fiin-market-price.md` |
| `10-fiin-tu-dien.md` | `10-fiin-dictionary.md` |
| `phu-luc-A-ma-field.md` | `appendix-A-field-codes.md` |
| `phu-luc-B-do-phu-du-lieu.md` | `appendix-B-coverage.md` |
| `tu-dien-ma-field.json` | `field-dictionary.json` |
| `kho-du-lieu-thi-truong.md` | `market-data-store.md` |
| `pipeline-tin-tuc.md` | `news-pipeline.md` |
| `tang-ngu-nghia-chatbot.md` | `chatbot-semantic-layer.md` |
| `bao-tri-skill.md` | `maintenance.md` |
| `thuat-ngu.md` | `terminology.md` |

Giữ nguyên: mọi `README.md`, `01-bvsc-rest.md`, `02-bvsc-tvcharts.md`, `11-bvsc-realtime.md`, `wichart.md`, `feeds.json`, `verify_wichart.py`.

### .claude/skills/

| Cũ | Mới |
|---|---|
| `co-van-chung-khoan-vn/` | `vn-stock-advisor/` |
| `co-van…/references/van-phong.md` | `writing-style.md` |
| `co-van…/references/khung-phan-tich.md` | `analysis-framework.md` |
| `co-van…/references/tu-duy-lap-luan.md` | `reasoning.md` |
| `co-van…/references/doc-hanh-vi-thi-truong.md` | `market-behavior.md` |
| `kien-thuc-chung-khoan-vn/` | `vn-stock-knowledge/` |
| `kien-thuc…/references/vi-mo-va-tao-tien.md` | `macro-money-creation.md` |
| `kien-thuc…/references/doc-bao-cao-tai-chinh.md` | `financial-statements.md` |
| `kien-thuc…/references/dinh-gia.md` | `valuation.md` |
| `kien-thuc…/references/ky-thuat-cung-cau.md` | `technical-supply-demand.md` |
| `kien-thuc…/references/ky-thuat-chi-bao.md` | `technical-indicators.md` |
| `kien-thuc…/references/danh-muc-va-luan-chuyen.md` | `portfolio-and-rotation.md` |
| `kien-thuc…/references/tam-ly-va-thong-tin.md` | `psychology-information.md` |
| `kien-thuc…/references/nang-cao.md` | `advanced.md` |

Hai `SKILL.md`: frontmatter `name:` đổi theo tên thư mục mới. `description:` giữ nguyên tiếng Việt (định danh kích hoạt theo nội dung, không đổi).

**2 · Mỗi nguồn tự chứa đủ đồ nghề của nó.** `config/` và `scripts/` giải tán.

| File | Về đâu | Vì sao gắn chặt |
|---|---|---|
| `feeds.json` | `10-sources/news/` | Là bản máy đọc của chính tài liệu nguồn tin — 47 feed + taxonomy. Danh sách feed đổi thì tài liệu và file phải đổi cùng lúc |
| `verify_wichart.py` | `10-sources/macro/` | Đọc registry 509 khẳng định nằm ngay trong `wichart.md`. Script và dữ liệu nó kiểm phải nằm cạnh nhau, nếu không sửa registry là script gãy mà không ai thấy |

Tiêu chí đặt file: **file đi theo thứ nó mô tả, không đi theo dạng của chính nó.**

*Ghi chú tương lai:* khi có code pipeline tin thật, `feeds.json` **chuyển về config của app đó** — chỗ hiện tại trong `docs/` đúng cho hôm nay (nó đang là tài liệu máy đọc, chưa có app nào đọc), không phải vĩnh viễn. `verify_wichart.py` thì ở lại: nó kiểm tài liệu, không phải một phần của app.

**3 · Hai skill đổi định danh** sang `vn-stock-advisor` và `vn-stock-knowledge` (hai dòng thư mục trong bảng `.claude/skills/` ở trên).

Hệ quả cần biết: **tên thư mục skill chính là định danh kích hoạt** — đổi tên thư mục là đổi định danh, nên `name:` trong frontmatter của cả hai `SKILL.md` phải đổi theo cho khớp. Ngược lại, `description:` **giữ nguyên tiếng Việt**: skill được chọn theo nội dung mô tả chứ không theo tên, nên hành vi trigger không đổi một chút nào sau lần đổi tên này.

**4 · Luật mới: tài liệu sống phải tường minh — `decisions/` chỉ là kho lịch sử.**

> Tài liệu sống phải tự đứng được. `decisions/` (ADR) chỉ là kho lịch sử — tra khi muốn biết "vì sao hồi đó", không bao giờ là nơi duy nhất chứa một quyết định đang hiệu lực, và tài liệu sống không trỏ về nó.

**Phép kiểm:** xoá cả `decisions/` thì hệ tài liệu chỉ mất lịch sử, không mất tri thức vận hành.

Luật này đã ghi vào bảng luật sửa của `docs/README.md`, nên nó là luật của kho chứ không phải điều khoản nằm trong một ADR. Hai việc kèm theo đã làm xong: mọi con trỏ "xem ADR" trong tài liệu sống được gỡ (ngoại lệ duy nhất: mục changelog — đó là bản ghi lịch sử), và quyết định chọn trường trước chỉ nằm trong [ADR 0002](0002-data-source-selection.md) nay có tài liệu sống tường minh tới từng mã trường ở `docs/20-design/market-field-selection.md`. ADR này cũng theo đúng luật: không tài liệu sống nào trỏ về đây.

## Hệ quả

**Tốt:**

- Đọc tên là đoán được nội dung, không cần mở: `docs/10-sources/market/` · `docs/20-design/` · `docs/30-skills/`. Một quy ước đặt tên duy nhất cho cả tài liệu lẫn code sắp thêm.
- Gốc repo còn đúng bốn mục — `README.md`, `docs/`, `.claude/`, `.git/`. Chỗ trống ở gốc để dành cho code thật, không bị hai thư mục một-file chiếm tên.
- Mở một nguồn ra là có đủ: tài liệu + file máy đọc + script tự kiểm của chính nguồn đó.
- Phép kiểm "xoá `decisions/`" nay chạy được thật: tri thức vận hành nằm hết ở tài liệu sống.

**Phải chấp nhận:**

- **ADR 0001–0004 nay mô tả những đường dẫn không còn tồn tại.** Prose của chúng cố ý đóng băng — viết lại tên trong đó là làm sai lệch bản ghi về một quyết định đã ra trên tên cũ. Chỉ link được sửa cho khỏi treo, text hiển thị giữ nguyên tên cũ. **Bảng ánh xạ ở Quyết định 1 là chìa khoá tra** cũ → mới; không có nó thì bốn ADR đầu thành khó đọc.
- **Spec và plan của chính lần tái cấu trúc này nằm trong repo** tại `docs/superpowers/plans/2026-08-14-restructure-english-tree/`. Chúng là tài liệu có cấu trúc — mang bảng ánh xạ nguyên văn, tiêu chí nghiệm thu đo được — được chủ dự án chấp nhận giữ, không phải loại nhật ký phiên mà ADR 0004 bỏ. Đổi lại, cả thư mục `docs/superpowers/` phải nằm **ngoài vùng của mọi bộ kiểm và mọi script thay tên**: nó tự chứa tên cũ nguyên văn, quét vào là báo giả hoặc phá chính bảng ánh xạ.
- Lịch sử git của từng file bị cắt ở lần đổi tên: `git log` hay `git blame` một file phải thêm `--follow`.

## Đã cân nhắc và loại

| Phương án | Vì sao loại |
|---|---|
| **Giữ tên tiếng Việt, chỉ dọn `config/` và `scripts/`** | Sửa được một trong ba chỗ sai. Cây vẫn trộn hai quy ước đặt tên khi code vào repo, và mỗi lần thêm thư mục lại phải quyết định lại ngôn ngữ — quyết định lặp lại là quyết định chưa chốt |
| **Dịch cả nội dung sang tiếng Anh cho nhất quán** | Tài liệu để người Việt đọc và để skill tiếng Việt tra. Dịch là đổi độc giả, và mất chính xác ở đúng chỗ đắt nhất — thuật ngữ tài chính. Đổi tên là thao tác cơ học, kiểm được bằng script; dịch thì không |
| **Giữ `config/` và `scripts/` ở gốc để code sau này dùng chung** | Khi có app thật, hai thư mục đó sẽ có chủ thật — lúc ấy `config/` là config của app, không phải chỗ để bản máy đọc của một tài liệu. Cách để dành chỗ cho chúng là **để trống**, không phải chiếm sẵn bằng một file lạc chủ |
| **Đổi tên nhưng để lại file cũ làm stub trỏ sang tên mới** | Kho tài liệu đọc bằng mắt và bằng `grep`, không có cơ chế redirect. Stub là file hết hạn ngay lúc sinh ra và sẽ bị grep bắt như tồn dư — đúng loại rác ADR 0004 vừa dọn |
| **Ra luật "ADR chỉ là lịch sử" mà không gỡ con trỏ trong tài liệu sống** | Luật không có phép kiểm thì không thi hành được. Phép kiểm "xoá `decisions/`" chỉ cho kết quả đúng khi không còn con trỏ nào — nên phải gỡ hết con trỏ trước, luật mới có nghĩa |
| **Đổi tên thư mục skill mà giữ `name:` cũ trong frontmatter** | Tên thư mục là định danh kích hoạt; để lệch với `name:` là tạo hai định danh cho một skill, hỏng đúng thứ không có gì báo lỗi khi hỏng |
