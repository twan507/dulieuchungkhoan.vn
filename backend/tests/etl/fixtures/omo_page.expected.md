# Expected giải tay cho `omo_page.html` (bắt 2026-08-26, phiên 25/08/2026)

Đọc bằng mắt từ bảng trong fixture — dùng làm literal cho test parser (Task 5).

- `session_date` = **2026-08-25** — từ `<div class="ls01-date">Ngày 25 tháng 08 năm 2026</div>`
  ⚠️ **Markup đã đổi so với sbv-omo.md §4** (đo 2026-08-26): ngày KHÔNG còn nằm trong tiêu đề
  dạng `(dd.mm.yy)`; tiêu đề giờ là `<h4 class="ls01-subheading">KẾT QUẢ ĐẤU THẦU THỊ TRƯỜNG MỞ</h4>`
  (không ngày), ngày nằm ở div `ls01-date` dạng `Ngày DD tháng MM năm YYYY`.
  Parser phải nhận CẢ HAI dạng ngày (dạng cũ có thể quay lại — markup viết tay).
- Header 4 cột, cột 3/4 có `<br>`: `Khối lượng trúng thầu<br>(Tỷ đồng)` · `Lãi suất trúng thầu<br>(%/năm)`.
- Nhóm: một dòng `<tr class="ls01-group"><td colspan="4">Mua kỳ hạn</td></tr>` → chỉ `reverse_repo`.
- Dòng kỳ hạn có tiền tố `- `: `- Kỳ hạn 14 ngày`.
- Dòng tổng: `<tr class="ls01-total">`, nhãn `Tổng cộng` (không phải `Tổng`), giá trị ở cột 3.

| op_type | tenor_days | participants/winners | volume (tỷ) | volume_vnd | rate_pct |
|---|---|---|---|---|---|
| reverse_repo | 14 | 2/2 | 5.131,64 | 5131640000000 | 4,5 |
| reverse_repo | 35 | 2/2 | 3.447,79 | 3447790000000 | 4,5 |
| reverse_repo | 63 | 2/2 | 3.897,22 | 3897220000000 | 4,5 |
| reverse_repo | 91 | 3/3 | 4.569,61 | 4569610000000 | 4,5 |

Tổng cộng: 17.046,26 tỷ — khớp Σ 4 dòng (5131,64+3447,79+3897,22+4569,61 = 17046,26 ✓).
`groups_present` = {"reverse_repo"}; `has_repo` = `has_outright_sale` = false (vắng nhóm là dữ kiện).
