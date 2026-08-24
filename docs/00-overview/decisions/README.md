# Sổ quyết định kiến trúc (ADR)

Thư mục này là **kho lịch sử quyết định** — vì sao kiến trúc thành ra thế này. Mỗi ADR ghi một quyết định tại một thời điểm, kèm bối cảnh và hệ quả.

🔴 **Chỉ để tra cứu lịch sử** *(CLAUDE.md §1.1)*. Tài liệu sống **không được trỏ về đây** để lấy tri thức vận hành — mọi thứ cần để vận hành phải tường minh tại chỗ trong [`10-sources/`](../../10-sources/) hoặc [`20-design/`](../../20-design/). Phép thử: xoá cả thư mục này thì chỉ được mất **lịch sử**, không được mất **cách làm**.

ADR không sửa lại nội dung cũ; một quyết định bị thay đổi thì ghi bằng **một ADR mới** trỏ ngược lại, và cột "Quan hệ" dưới đây phản ánh chuỗi đó.

---

| № | Tiêu đề | Ngày | Trạng thái · quan hệ |
|---|---|---|---|
| [0001](0001-docs-structure.md) | Cấu trúc kho tài liệu | 2026-08-14 | Đã áp dụng · §6 **bị thay** bởi 0004 · §1/§5 **sửa một phần** bởi 0005 |
| [0002](0002-data-source-selection.md) | Chọn nguồn dữ liệu khi nhiều nguồn cùng có | 2026-08-14 | Đã chốt · **được mở rộng** bởi 0006 |
| [0003](0003-close-skill-project.md) | Đóng dự án skill, xoá `CAN-SUA.md` | 2026-08-14 | Đã áp dụng · **sửa một phần** 0001 §6 |
| [0004](0004-drop-session-logs.md) | Bỏ nhật ký phiên, giữ tài liệu trạng thái | 2026-08-14 | Đã áp dụng · **thay** 0001 §6 |
| [0005](0005-english-tree.md) | Tái cấu trúc cây tiếng Anh | 2026-08-15 | Đã áp dụng · **sửa một phần** 0001 §1/§5 |
| [0006](0006-source-selection-2026-08-15.md) | Chốt nguồn dữ liệu sau khảo sát 2026-08-15 | 2026-08-15 | Đã chốt · **mở rộng** 0002 · thêm nhánh vào cây 0005 |
| [0007](0007-monorepo-layout-and-stack.md) | Cây monorepo và stack sản phẩm | 2026-08-24 | Đã chốt (chủ dự án) |

> Số ADR chỉ tăng, không tái sử dụng. ADR kế tiếp là **0008**.
