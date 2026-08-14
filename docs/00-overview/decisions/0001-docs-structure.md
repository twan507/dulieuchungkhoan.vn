# 0001 · Cấu trúc kho tài liệu

**Ngày:** 2026-08-14 · **Trạng thái:** đã áp dụng · ⚠️ **§6 đã bị thay thế bởi [ADR 0004](0004-drop-session-logs.md)** — nhật ký phiên nay bỏ hẳn, không còn giữ cả bốn file. Các mục còn lại vẫn hiệu lực · §1/§5 **sửa đổi một phần** bởi [ADR 0005](0005-english-tree.md).

## Bối cảnh

Tài liệu dự án được sinh ra trong ba phiên làm việc độc lập, mỗi phiên để lại một thư mục tự đầy đủ: `bvsc-api-docs/`, `nguon_tin_chung_khoan/`, `chuyen_gia_chung_khoan/`. Ba thư mục trộn lẫn năm loại nội dung khác nhau — tài liệu tra cứu, tài liệu thiết kế, corpus nguyên liệu, sản phẩm chạy được, và nhật ký dự án — mà không có ranh giới nào giữa chúng.

Repo này sẽ trở thành **repo dự án thật**, có frontend, backend và database. Nếu không đặt tài liệu đúng chỗ ngay bây giờ, mỗi lần thêm code sẽ phải dọn lại một lần.

## Quyết định

**1 · Phân tầng theo vai trò tài liệu, không theo nguồn gốc.**

```
docs/00-tong-quan/     hợp nhất, lộ trình, sổ quyết định
docs/10-nguon-du-lieu/ REFERENCE  — sự thật đo được về hệ thống của người khác
docs/20-thiet-ke/      EXPLANATION — lựa chọn của Finext
docs/30-tri-thuc/      corpus + nhật ký dựng skill
.claude/skills/        sản phẩm chạy được
config/ · scripts/     file máy đọc và script vận hành
```

Ranh giới `10` / `20` là quan trọng nhất: **sửa số ở `10` mà không đo lại là nói dối; sửa `20` là đổi ý và phải ghi lý do.** Phân loại Diátaxis mà tài liệu API gốc đã dùng được giữ và mở rộng cho cả ba nguồn.

**2 · Skill đặt ở `.claude/skills/` gốc, không nằm trong `docs/`.**

Skill vừa là công cụ dev vừa là artifact sản phẩm — chatbot sẽ nạp chính nó. Giữ **một bản nguồn duy nhất**, không nhân bản. Đặt ở gốc thì skill dùng được cho toàn repo thay vì chỉ khi làm việc trong một thư mục con.

**3 · Corpus ở `docs/30-tri-thuc/corpus/`, không phải `data/` gốc.**

`data/` sau này là dữ liệu runtime của database. Corpus là nguyên liệu đã dùng xong để dựng skill — nó thuộc về tài liệu.

**4 · Tách `THIET_KE_PIPELINE.md` làm hai theo ranh giới `10`/`20`, nhưng giữ nguyên số mục gốc.**

Hàng chục tham chiếu chéo dạng *"xem mục 6.5"* nằm rải trong cả hai nửa. Đánh số lại sẽ làm vỡ hết. Mỗi nửa mang một bảng chỉ mục chéo chỉ rõ mục nào nằm ở file nào. Nội dung không đổi một chữ.

**5 · Giữ nguyên tên file `00`–`11` và phụ lục A/B trong `thi-truong/`.**

55 link tương đối giữa chúng vẫn đúng khi cả nhóm di chuyển cùng nhau. Chỉ ba file rời nhóm mới đổi tên: `12` → `20-thiet-ke/kho-du-lieu-thi-truong.md`, `13` → `vi-mo-hang-hoa/wichart.md`, `verify_wichart.py` → `scripts/`.

**6 · Không hợp nhất bốn file nhật ký dựng skill.**

`HANDOFF` / `BAN-DO-KHAI-NIEM` / `CAN-SUA` là ba lát cắt thời gian của cùng một dự án. Gộp lại sẽ mất mạch *quyết định nào có trước, đè lên cái gì* — mà đó chính là giá trị của chúng.

**7 · Xoá `documents/` (96 transcript verbatim, 6,5 MB).**

Người dùng đã có bản lưu trữ riêng bên ngoài repo.

## Hệ quả

**Tốt:**

- Ba mắt xích vốn treo hai đầu nay nối được thành tài liệu: danh sách mã niêm yết, cây ngành ICB, hợp đồng function calling ↔ skill. Xem [kiến trúc tổng thể §3](../architecture.md).
- Bốn mục trong danh sách *"Còn để ngỏ"* của pipeline tin hoá ra đã có đáp án ở khối tài liệu khác.
- Chỗ cho `apps/` hoặc `frontend/` + `backend/` để trống, thêm vào không phải dọn gì.

**Phải chấp nhận:**

- Mất khả năng đối chiếu ngược transcript gốc khi skill gặp thuật ngữ nghi là lỗi nhận dạng giọng nói. Rủi ro này có thật và đã xảy ra một lần: «nội giải» xuất hiện **đúng 1 lần** trong transcript nhưng bản tóm tắt nâng thành thuật ngữ dùng 10 lần. Còn một việc treo cần đúng nguồn này — kiểm lại mâu thuẫn doji ở `Ứng dụng 2024 CD2`. Nay phải lấy từ bản lưu trữ ngoài.
- Đánh số mục của hai file pipeline không liền mạch. Đã bù bằng bảng chỉ mục chéo ở đầu mỗi file.

## Đã cân nhắc và loại

| Phương án | Vì sao loại |
|---|---|
| Giữ nguyên ba thư mục, chỉ thêm README nối | Rẻ và không vỡ link, nhưng tài liệu kiến trúc Finext vẫn nằm lẫn trong tài liệu API của người khác — đúng cái ranh giới cần dựng |
| Phân theo vòng đời: `nguon/` `thiet-ke/` `tri-thuc/` `van-hanh/` | Gần như phương án đã chọn nhưng phẳng hơn; mất chỗ đặt tài liệu hợp nhất ở tầng `00` |
| Đánh số lại toàn bộ mục sau khi tách file | Vỡ hàng chục tham chiếu chéo, lợi ích thẩm mỹ thuần tuý |
