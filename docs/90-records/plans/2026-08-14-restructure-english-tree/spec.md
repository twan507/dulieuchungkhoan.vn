# SPEC — Tái cấu trúc kho tài liệu Finext v2 sang cây tiếng Anh

**Ngày:** 2026-08-14 · **Repo:** D:\twan-projects\finext-v2 · **Nhánh làm việc:** restructure/english-tree

## 1. Mục tiêu

1. Cây thư mục phản ánh **cấu trúc sản phẩm**, không phản ánh lịch sử dựng tài liệu.
2. Toàn bộ **tên file và thư mục** sang tiếng Anh. **Nội dung file giữ nguyên tiếng Việt** — kể cả heading, mục lục, bảng.
3. Mỗi nguồn dữ liệu **tự chứa đủ đồ nghề của nó**: `feeds.json` về nguồn tin, `verify_wichart.py` về nguồn WiChart. Giải tán `config/` và `scripts/` ở gốc.
4. Quy tắc cứng mới, ghi thành luật trong `docs/README.md`:
   > **Tài liệu sống phải tường minh, tự đứng được. `decisions/` (ADR) chỉ là kho lịch sử — tra khi muốn biết "vì sao hồi đó", không bao giờ là nơi duy nhất chứa một quyết định đang hiệu lực, và tài liệu sống không trỏ về nó.**
   Phép kiểm: xoá `decisions/` thì hệ tài liệu chỉ mất lịch sử, không mất tri thức vận hành.
5. Quyết định chọn trường (hiện chỉ nằm trong ADR 0002) phải có **tài liệu sống tường minh** trong `20-design/`.

## 2. Bảng ánh xạ đổi tên — TOÀN BỘ, dùng nguyên văn

### 2.1 Gốc repo

| Cũ | Mới |
|---|---|
| `config/feeds.json` | `docs/10-sources/news/feeds.json` |
| `scripts/verify_wichart.py` | `docs/10-sources/macro/verify_wichart.py` |
| `config/`, `scripts/` | xoá (rỗng sau khi di chuyển) |

### 2.2 docs/ — thư mục

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

### 2.3 docs/ — file (basename đổi)

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

### 2.4 .claude/skills/

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

## 3. Vùng BẤT KHẢ XÂM PHẠM

1. **`corpus/` trừ `corpus/README.md`**: không đổi tên, không sửa nội dung, không chạy replace. `corpus/README.md` là chỉ mục — được sửa.
2. **Phần chữ (prose) của ADR 0001–0004**: mô tả quyết định trên tên cũ — viết lại là làm sai lệch bản ghi. **Chỉ sửa link** trong đó cho khỏi treo (giữ nguyên text hiển thị của link).
3. **Nội dung tiếng Việt của mọi file**: chỉ đổi tên file/đường dẫn/tên skill xuất hiện trong văn bản; không dịch, không viết lại câu.

## 4. Quy tắc quét "xem ADR" (Task 4)

- Tài liệu sống (mọi file ngoài `decisions/`): **gỡ mọi con trỏ "xem ADR"**. Chỗ nào phát biểu đã tường minh → chỉ gỡ con trỏ. Chỗ nào đang dựa hẳn vào ADR để hiểu → viết thẳng nội dung vào tại chỗ.
- **Ngoại lệ**: mục "Nhật ký thay đổi" (changelog) trong tài liệu sống là bản ghi lịch sử — được phép giữ nhắc ADR.
- `decisions/` giữ nguyên toàn văn, được phép trùng nội dung với tài liệu sống.

## 5. Tài liệu chọn trường (Task 3)

Tạo `docs/20-design/market-field-selection.md` (+ `market-field-selection.json` máy đọc):

- Trải quyết định của ADR 0002 ra **từng mã trường**: mã, nguồn chuẩn, lấy/bỏ, lý do ghi thẳng tại chỗ (vd "trùng BVSC", "chỉ báo kỹ thuật — tính từ giá BVSC", "nhóm chấm điểm — không dùng điểm bên thứ ba chấm").
- Nguồn đối chiếu: ADR 0002 (nhóm lý do + số đếm) · `10-fiin-dictionary.md` · `appendix-A-field-codes.md` · `field-dictionary.json` · `appendix-B-coverage.md` · `04-fiin-company-profile.md` (Snapshot).
- **Cấm bịa**: mỗi dòng phải truy được về một câu trong tài liệu nguồn hoặc một nhóm trong ADR 0002. Mã không phân loại chắc chắn được → đánh dấu `cần kiểm API`, đếm riêng.
- **Số đếm phải khớp ADR 0002** (Screener giữ 80/193, bỏ 113 theo 11 nhóm; Snapshot giữ 16/54). Không khớp → báo cáo độ lệch, không ép số.
- Không trỏ về ADR trong file này. Cập nhật `architecture.md` §3.4: câu "Đầy đủ: ADR 0002" đổi thành trỏ tới file mới.

## 6. Tiêu chí nghiệm thu toàn cục

> Vùng loại trừ chung của mọi phép kiểm: nội dung corpus (trừ `corpus/README.md`), `decisions/` (bản ghi lịch sử, chứa tên cũ), `docs/superpowers/` (spec/plan này — tự chứa bảng ánh xạ tên cũ).

1. Script kiểm link: **0 link treo** trên toàn bộ `.md` trong vùng kiểm; bỏ qua chuỗi trong code fence.
2. Script kiểm mục lục↔heading skill: **0 lệch**.
3. Grep tồn dư slug cũ (danh sách trong plan) trong vùng kiểm: **0 hit**.
4. `git status` nhận diện **rename**, không phải delete+add hàng loạt (cho phép similarity thấp ở file bị sửa nhiều).
5. Gốc repo chỉ còn: `README.md`, `docs/`, `.claude/`, `.git/`.
6. Nội dung tiếng Việt không đổi ngoài các chuỗi tên file/đường dẫn/tên skill — kiểm bằng diff xem mẫu.
7. Grep `ADR` trong tài liệu sống chỉ còn hit ở changelog, `decisions/` và `docs/superpowers/`.
8. ADR 0005 tồn tại, mang bảng ánh xạ đầy đủ.
9. Không commit nào lên `main` cho tới khi review toàn cục sạch.
