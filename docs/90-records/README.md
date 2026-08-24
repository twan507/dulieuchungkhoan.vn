# Hồ sơ làm việc

Tầng này lưu **bản ghi lịch sử của từng đợt làm việc lớn** — không phải tài liệu sống. Hai loại hồ sơ:

- **`plans/`** — spec + plan của một task lớn, theo quy trình [CLAUDE.md §4.1](../../CLAUDE.md): việc lớn thì viết đặc tả và kế hoạch trước, rồi mới thực thi.
- **`surveys/`** — hồ sơ một đợt khảo sát: số liệu đo thật, báo cáo từng nguồn/chủ đề, brief tóm tắt.

**Luật sửa:** bản ghi lịch sử — **thêm mới, không viết lại quá khứ**. Một hồ sơ đã đóng phản ánh điều đúng *tại thời điểm đó*; tri thức vận hành rút ra từ nó phải đi vào tài liệu sống ở [`10-sources/`](../10-sources/) hoặc [`20-design/`](../20-design/), không nằm lại đây.

> Hồ sơ ở đây là **bằng chứng đo**, không phải nguồn tra cứu vận hành. Muốn biết "hệ thống hiện thế nào" thì đọc tài liệu sống; muốn biết "vì sao con số này ra thế" thì mới lần về đây.

---

## `plans/` — đặc tả và kế hoạch từng task lớn

Mỗi thư mục là một task, đặt tên `YYYY-MM-DD-<tên>`. File bên trong: `spec.md` (đặc tả mục tiêu + nghiệm thu), `plan.md` (kế hoạch từng bước), đôi khi `ledger.md` (sổ theo dõi lúc thực thi).

| Thư mục | Task | Kết quả |
|---|---|---|
| [`2026-08-14-restructure-english-tree/`](plans/2026-08-14-restructure-english-tree/) | Tái cấu trúc kho tài liệu sang cây tiếng Anh — `spec.md` · `plan.md` | Đã áp dụng → [ADR 0005](../00-overview/decisions/0005-english-tree.md) |
| [`2026-08-15-cap-nhat-tai-lieu-nguon/`](plans/2026-08-15-cap-nhat-tai-lieu-nguon/) | Cập nhật tài liệu nguồn theo khảo sát 2026-08-15 — `spec.md` · `plan.md` · `ledger.md` | Đã áp dụng → tài liệu 9 nguồn |
| [`2026-08-24-monorepo-restructure/`](plans/2026-08-24-monorepo-restructure/) | Chuẩn hoá cây monorepo + chốt stack — `spec.md` · `plan.md` | Đã áp dụng → [ADR 0007](../00-overview/decisions/0007-monorepo-layout-and-stack.md) |

## `surveys/` — hồ sơ khảo sát

Mỗi thư mục là một đợt khảo sát, có README riêng làm mục lục chi tiết. Ở đây chỉ liệt kê đợt.

| Thư mục | Đợt | Quy mô |
|---|---|---|
| [`2026-08-15-nguon-du-lieu/`](surveys/2026-08-15-nguon-du-lieu/README.md) | Khảo sát nguồn dữ liệu — báo cáo từng nguồn, brief, rà soát nguồn cũ và việc chưa kiểm | 9 nguồn · ~400 lời gọi thật · mục lục ở README của đợt |
