# Bản đồ tài liệu Finext

Bốn tầng, đọc theo số. Mỗi tầng có một loại nội dung và một luật sửa riêng.

| Tầng | Chứa gì | Luật sửa |
|---|---|---|
| [`00-tong-quan/`](00-tong-quan/) | Hợp nhất ba khối, lộ trình, sổ quyết định | Cập nhật khi kiến trúc đổi |
| [`10-nguon-du-lieu/`](10-nguon-du-lieu/) | **Reference** — sự thật đo được về hệ thống của người khác | Chỉ sửa khi **đo lại** |
| [`20-thiet-ke/`](20-thiet-ke/) | **Explanation** — lựa chọn của Finext | Sửa được, ghi lý do vào [`quyet-dinh/`](00-tong-quan/quyet-dinh/) |
| [`30-tri-thuc/`](30-tri-thuc/) | Corpus và tài liệu bảo trì hai skill chứng khoán | Corpus bất biến; tài liệu bảo trì cập nhật theo trạng thái thật |

---

## Đọc gì trước

**Muốn hiểu toàn cảnh** → [kiến trúc tổng thể](00-tong-quan/kien-truc-tong-the.md). Bốn tầng hệ thống, ba mắt xích nối ba khối, một lỗ hổng đã biết chưa vá.

**Sắp bắt tay làm** → [lộ trình hợp nhất](00-tong-quan/lo-trinh.md). Việc nào chặn việc nào, việc nào gấp vì mất dữ liệu theo thời gian, việc nào tưởng để ngỏ mà đã có đáp án.

**Sắp gọi API** → [quy ước chung](10-nguon-du-lieu/thi-truong/00-quy-uoc-chung.md) trước tiên, 9 bẫy triển khai nằm ở đó.

**Sắp sửa skill** → [bảo trì skill](30-tri-thuc/bao-tri-skill.md) và [bảng thuật ngữ](30-tri-thuc/thuat-ngu.md). Cả hai là **bắt buộc**, không phải tham khảo — file đầu ghi những chỗ sửa nhầm sẽ hỏng skill mà không có gì báo lỗi.

## Toàn bộ tài liệu

### 00 · Tổng quan

| File | Nội dung |
|---|---|
| [kien-truc-tong-the.md](00-tong-quan/kien-truc-tong-the.md) | Bốn tầng L0–L4 · ranh giới tài liệu · ba mắt xích nối ba khối · lỗ hổng gác cổng phạm vi · rủi ro pháp lý theo nguồn |
| [lo-trinh.md](00-tong-quan/lo-trinh.md) | Trạng thái từng khối · việc chặn nhiều nhất · việc gấp vì mất dữ liệu · cây phụ thuộc · việc còn để ngỏ · ba bẫy ngày đầu |
| [quyet-dinh/](00-tong-quan/quyet-dinh/) | Sổ quyết định kiến trúc (ADR) — 0001 cấu trúc kho · 0002 chọn nguồn dữ liệu · 0003 đóng dự án skill · 0004 bỏ nhật ký phiên |

### 10 · Nguồn dữ liệu — *reference*

| Thư mục | Nguồn | Quy mô | Kiểm chứng |
|---|---|---|---|
| [thi-truong/](10-nguon-du-lieu/thi-truong/) | BVSC + FiinTrade | 44 REST + 5 topic realtime | 2026-08-10, mẫu 51 mã |
| [vi-mo-hang-hoa/](10-nguon-du-lieu/vi-mo-hang-hoa/) | WiChart (WiGroup) | 87 REST | 2026-08-12, toàn bộ 87 key |
| [tin-tuc/](10-nguon-du-lieu/tin-tuc/) | 10 báo điện tử | 47 RSS + 6 crawler | 2026-08-13, 307 URL · 1.408 tiêu đề |

Mục lục chi tiết từng file: [10-nguon-du-lieu/README.md](10-nguon-du-lieu/README.md).

### 20 · Thiết kế — *explanation*

| File | Nội dung | Trạng thái |
|---|---|---|
| [kho-du-lieu-thi-truong.md](20-thiet-ke/kho-du-lieu-thi-truong.md) | Cách ly hoàn toàn · Ingester + SSE · lược đồ Timescale · ETL · giám sát hợp đồng | ✅ đã duyệt |
| [pipeline-tin-tuc.md](20-thiet-ke/pipeline-tin-tuc.md) | Lưới AI không đường tắt · taxonomy 20 sub · gắn mã 3 tầng · kho toàn văn | ✅ đã duyệt |
| [tang-ngu-nghia-chatbot.md](20-thiet-ke/tang-ngu-nghia-chatbot.md) | Luật phân định 4 tầng · 8 function · ba quy tắc nối dữ liệu vào skill | 🟡 **đề xuất, chưa duyệt** |

### 30 · Tri thức chuyên môn

| Đường dẫn | Nội dung |
|---|---|
| [bao-tri-skill.md](30-tri-thuc/bao-tri-skill.md) | **Đọc trước khi sửa skill** — quyết định không được đảo · 5 lỗi nguồn đã sửa · 5 thứ cố ý · bộ test hồi quy · đoạn dán vào system prompt · ngân sách dòng |
| [thuat-ngu.md](30-tri-thuc/thuat-ngu.md) | Bảng tra **bắt buộc** — hai trục phân loại, chuyển đổi thuật ngữ nguồn, lỗi nhận dạng giọng nói đã sửa |
| [corpus/](30-tri-thuc/corpus/) | 96 file tóm tắt bài giảng HP0–HP6 + Trà Chiều — nguyên liệu, không phải tài liệu |

### Ngoài `docs/`

| Đường dẫn | Nội dung |
|---|---|
| [`.claude/skills/`](../.claude/skills/) | Hai skill chứng khoán — sản phẩm chạy được, 3.045 dòng |
| [`config/feeds.json`](../config/feeds.json) | 47 feed + taxonomy dạng máy đọc |
| [`scripts/verify_wichart.py`](../scripts/verify_wichart.py) | Tự kiểm 509 khẳng định của tài liệu WiChart với API sống |
