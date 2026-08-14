# 0003 · Đóng dự án skill, xoá `CAN-SUA.md`

**Ngày:** 2026-08-14 · **Trạng thái:** đã áp dụng · **Sửa đổi một phần** [ADR 0001](0001-cau-truc-kho-tai-lieu.md) §6

> ⚠️ **Cùng ngày, [ADR 0004](0004-bo-nhat-ky-phien.md) đi xa hơn:** ADR này giữ `HANDOFF.md` và `BAN-DO-KHAI-NIEM.md` vì cho rằng chúng ghi *mạch quyết định*. Kiểm kỹ hơn thì hai file đó là **nhật ký phiên đã hết hạn và tự mô tả sai trạng thái**, nên đã xoá nốt. Mục 2 (quyết định A9) và mục 3 (quy ước heading) của ADR này **vẫn nguyên hiệu lực**; chỉ mục 4 bị mở rộng.

## Bối cảnh

`CAN-SUA.md` sinh ra như một **đơn đặt hàng**: bảng 20 chỗ cần sửa, rà lượt cuối trước Giai đoạn 4, chờ duyệt. Nó khác hai file nhật ký còn lại ở đúng một điểm, và điểm đó quyết định số phận của nó:

| File | Ghi cái gì | Làm xong thì |
|---|---|---|
| `HANDOFF.md` | Việc **đã làm** và vì sao | Vẫn còn giá trị — là mạch quyết định |
| `BAN-DO-KHAI-NIEM.md` | Kiểm kê **đã đo** và ngân sách dòng | Vẫn còn giá trị — `HANDOFF` trỏ vào mục 3 |
| `CAN-SUA.md` | Việc **cần làm**, chờ duyệt | Hết vai trò |

Tới 2026-08-14 toàn bộ 20 mục đã đóng: 18 mục làm hoặc quyết giữ ở các phiên trước, **A9** chủ dự án quyết hôm nay, **B11** sửa hôm nay.

Vấn đề không chỉ là thừa. File tự mở đầu bằng *"**Chưa sửa gì** — chờ duyệt"* trong khi thực tế đã sửa gần hết, và ô A9 trong thân bảng vẫn ghi *"Cần bạn quyết"* sau khi đã có quyết định. Đây là **thứ đầu tiên một phiên sau đọc thấy** — một bảng việc tồn giả, đúng loại tài liệu tự nói dối mà kho này có luật riêng để chống.

## Quyết định

**1 · Dự án skill đóng, không còn việc treo.**

Hai skill xong, test 6 vòng, đã dừng tối ưu theo tiêu chí *"hai vòng liên tiếp không tìm thấy lỗi trong tầm skill"*. Việc còn lại duy nhất liên quan tới skill nằm ở **tầng sản phẩm, không phải tầng skill**: dán đoạn giới hạn phạm vi vào system prompt khi dựng backend — xem [kiến trúc tổng thể §4](../kien-truc-tong-the.md).

**2 · A9 — giữ nguyên tên "ngân hàng" trong luận điểm *ngành báo hiệu*.**

Câu ở [`danh-muc-va-luan-chuyen.md`](../../../.claude/skills/kien-thuc-chung-khoan-vn/references/danh-muc-va-luan-chuyen.md): *"Ngân hàng đứng đầu bảng xếp hạng an toàn nhưng lại hút tiền đầu tiên… nên nó là ngành báo hiệu"*.

Lý do giữ: đây là **cơ chế**, không phải danh sách ngành cứng, nên nó không vi phạm quyết định gỡ danh sách ngành ở phần A — và là luận điểm có giá trị riêng, mất đi thì không nguồn nào khác cấp lại. Ba lựa chọn từng cân nhắc: giữ nguyên · đổi thành "nhóm tài chính" · bỏ hẳn.

**3 · B11 — heading trùng nguyên văn chữ trong mục lục; anchor giữ không dấu.**

Đây **không phải quy ước mới đặt ra**, mà là quy ước sẵn có ở 4 file vốn đã nhất quán (`van-phong`, `doc-hanh-vi-thi-truong`, `ky-thuat-cung-cau`, `tam-ly-va-thong-tin`). Tám file còn lại đang dùng *anchor viết lại có dấu* làm heading — `#ket-hop-nhan-to` → `## Kết hợp nhân tố` trong khi mục lục ghi "Kết hợp các nhân tố và hạn chế".

Đã sửa **61 heading trên 8 file**, kèm **6 chỗ trong văn bản gọi tên mục theo heading cũ** — đổi heading mà bỏ qua chúng là vá một lớp lệch rồi tạo ra lớp khác. Anchor giữ nguyên dạng không dấu theo quyết định B10 (file đọc như văn bản thuần, không render HTML).

⚠️ Phạm vi thật lớn gấp đôi con số ghi trong `CAN-SUA.md` mục B11 — bảng ghi 4 file, đo ra 8.

**4 · Xoá `CAN-SUA.md`. Sửa đổi một phần ADR 0001 §6.**

ADR 0001 §6 chốt *"không hợp nhất bốn file nhật ký dựng skill"*, lý do: gộp lại sẽ mất mạch *quyết định nào có trước, đè lên cái gì*. Lý do đó **vẫn đúng và vẫn giữ** cho `HANDOFF` và `BAN-DO-KHAI-NIEM`. Nó không áp cho `CAN-SUA` vì file này không chứa mạch quyết định — nó chứa **danh sách việc**, và mọi quyết định phát sinh từ nó đã có chỗ ở lâu dài trước khi xoá:

| Nội dung của `CAN-SUA.md` | Nay nằm ở |
|---|---|
| Phần A — chữ sau khi sửa | Chính trong 2 skill; lý do ở [`bao-tri-skill.md`](../../30-tri-thuc/bao-tri-skill.md) §2 |
| Phần A — 4 chỗ nêu tên ngành **không được gỡ nhầm** | [`30-tri-thuc/README.md`](../../30-tri-thuc/README.md) §*Ba điều dễ làm hỏng skill*, mục 1 |
| A9 và B11 | ADR này, mục 2 và 3 |
| B3, B4, B9, B10, B6 — quyết **giữ nguyên**, có lý do | [`30-tri-thuc/README.md`](../../30-tri-thuc/README.md) §*Năm thứ trông như lỗi nhưng là cố ý* |
| Chữ **trước khi** sửa, bảng khối lượng | Không giữ. Là lịch sử, và commit `a14eb54` còn nguyên |

Điểm cuối là điều kiện đủ để xoá: repo đã vào git ngày 2026-08-14, nên file không mất, chỉ rời khỏi đường đọc.

## Hệ quả

**Tốt:**

- Thư mục `ghi-chu-xay-dung/` còn hai file, cả hai đều **đang còn hiệu lực**. Không còn tài liệu nào tự mô tả sai trạng thái của mình.
- Bốn nhóm "cố ý, đừng sửa" chuyển từ một bảng rà soát dùng một lần sang [`30-tri-thuc/README.md`](../../30-tri-thuc/README.md) — chỗ mà luật kho quy định phải đọc **trước mọi thay đổi nội dung skill**. Trước đây chúng nằm ở file mà không ai có lý do đọc lại.
- Danh sách việc treo của cả dự án còn đúng hai, cả hai đều chờ bên ngoài.

**Phải chấp nhận:**

- Mất khả năng đọc nhanh chữ **trước khi sửa** của 9 chỗ trong phần A. Phải `git show a14eb54` mới thấy. Đánh đổi có ý thức: xác suất cần lại thấp, còn xác suất một phiên sau đọc nhầm bảng việc tồn giả là cao.
- ADR 0001 §6 nay đúng một phần. Đã ghi rõ ở đây thay vì sửa vào file cũ — sổ quyết định chỉ thêm, không viết lại.

## Đã cân nhắc và loại

| Phương án | Vì sao loại |
|---|---|
| **Giữ file, chỉ thêm khối trạng thái ở đầu** | Đã làm thử trong chính phiên này. Kết quả: một file 77 dòng mà 100% nội dung là việc đã đóng, và thân bảng vẫn ghi "cần bạn quyết" ở ô A9 — người đọc lướt vẫn hiểu sai. Chồng lớp cải chính lên một tài liệu đã hết vai trò thì tài liệu càng khó đọc, không dễ hơn |
| **Gộp `CAN-SUA` vào `HANDOFF`** | Đúng cái ADR 0001 §6 cấm, và cấm có lý: `HANDOFF` là mạch thời gian, chèn một bảng việc đã đóng vào giữa làm loãng mạch |
| **Xoá luôn `BAN-DO-KHAI-NIEM.md`** | Không. `HANDOFF` mục *ngân sách dòng* đang trỏ vào mục 3 của nó, và số liệu kiểm kê 355 section là thứ duy nhất giải thích vì sao mỗi file dày như hiện tại |
| **Giữ nguyên, coi như tài liệu lịch sử** | Đây là lựa chọn đúng cho `BAN-DO-KHAI-NIEM` (đã đo, bất biến) nhưng sai cho `CAN-SUA` (đã đóng, và tự mô tả sai) |
