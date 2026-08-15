# Bản đồ tài liệu Finext

Bốn tầng, đọc theo số. Mỗi tầng có một loại nội dung và một luật sửa riêng. Dòng cuối bảng không phải một tầng — nó là kho lịch sử.

| Tầng | Chứa gì | Luật sửa |
|---|---|---|
| [`00-overview/`](00-overview/) | Hợp nhất ba khối, lộ trình, sổ quyết định (chỉ lịch sử) | Cập nhật khi kiến trúc đổi |
| [`10-sources/`](10-sources/) | **Reference** — sự thật đo được về hệ thống của người khác | Chỉ sửa khi **đo lại** |
| [`20-design/`](20-design/) | **Explanation** — lựa chọn của Finext | Sửa được, lý do viết thẳng tại chỗ |
| [`30-skills/`](30-skills/) | Corpus và tài liệu bảo trì hai skill chứng khoán | Corpus bất biến; tài liệu bảo trì cập nhật theo trạng thái thật |
| [`00-overview/decisions/`](00-overview/decisions/) | Sổ quyết định — bản ghi lịch sử | Chỉ ghi lịch sử quyết định. Tài liệu sống phải tường minh, không trỏ về đây; xoá cả thư mục này chỉ được phép mất lịch sử |

---

## Đọc gì trước

**Muốn hiểu toàn cảnh** → [kiến trúc tổng thể](00-overview/architecture.md). Bốn tầng hệ thống, ba mắt xích nối ba khối, một lỗ hổng đã biết chưa vá.

**Sắp bắt tay làm** → [lộ trình hợp nhất](00-overview/roadmap.md). Việc nào chặn việc nào, việc nào gấp vì mất dữ liệu theo thời gian, việc nào tưởng để ngỏ mà đã có đáp án.

**Sắp gọi API** → [quy ước chung](10-sources/market/00-conventions.md) trước tiên, 13 bẫy triển khai nằm ở đó.

**Sắp sửa skill** → [bảo trì skill](30-skills/maintenance.md) và [bảng thuật ngữ](30-skills/terminology.md). Cả hai là **bắt buộc**, không phải tham khảo — file đầu ghi những chỗ sửa nhầm sẽ hỏng skill mà không có gì báo lỗi.

## Toàn bộ tài liệu

### 00 · Tổng quan

| File | Nội dung |
|---|---|
| [architecture.md](00-overview/architecture.md) | Bốn tầng L0–L4 · ranh giới tài liệu · ba mắt xích nối ba khối · lỗ hổng gác cổng phạm vi · rủi ro pháp lý theo nguồn |
| [roadmap.md](00-overview/roadmap.md) | Trạng thái từng khối · việc chặn nhiều nhất · việc gấp vì mất dữ liệu · cây phụ thuộc · việc còn để ngỏ · ba bẫy ngày đầu |
| [decisions/](00-overview/decisions/) | Kho lịch sử quyết định kiến trúc — 0001 cấu trúc kho · 0002 chọn nguồn dữ liệu · 0003 đóng dự án skill · 0004 bỏ nhật ký phiên · 0005 tái cấu trúc cây tiếng Anh · 0006 chốt nguồn sau khảo sát 2026-08-15 |

### 10 · Nguồn dữ liệu — *reference*

| Thư mục | Nguồn | Quy mô | Kiểm chứng |
|---|---|---|---|
| [market/](10-sources/market/) | BVSC + FiinTrade | 44 REST + 5 topic realtime · **phái sinh 14 hợp đồng · ETF/quỹ 31 mã** | 2026-08-10, mẫu 51 mã · phái sinh và ETF 2026-08-15 |
| [macro/](10-sources/macro/) | WiChart (WiGroup) · **SBV** | 87 REST + **1 trang crawl OMO** | 2026-08-12, toàn bộ 87 key · OMO 2026-08-15 |
| **[global/](10-sources/global/)** | **FRED · Frankfurter (ECB) · Yahoo · LBMA · Binance** | 15 series vĩ mô Mỹ · 6 cặp tiền + DXY dựng lại · 36 chỉ số/21 nước · vàng-bạc từ 1968 · 10 đồng crypto + PAXG | **2026-08-15**, ~400 lời gọi thật cả đợt |
| [news/](10-sources/news/) | 8 báo điện tử | 47 RSS + 6 crawler | 2026-08-13, 307 URL · 1.408 tiêu đề · cấu trúc trang bài 2026-08-15, 33 bài |

Mỗi nguồn tự chứa đủ đồ nghề: `macro/` có [`verify_wichart.py`](10-sources/macro/verify_wichart.py) — tự kiểm 509 khẳng định của tài liệu WiChart với API sống; `news/` có [`feeds.json`](10-sources/news/feeds.json) — 47 feed + taxonomy dạng máy đọc — và [`article-structure.md`](10-sources/news/article-structure.md) — selector container chính cùng luật bỏ boilerplate riêng từng nguồn.

**`global/` là nhóm mới, lập 2026-08-15.** Lý do tách khỏi `macro/`: chỉ số cổ phiếu quốc tế và crypto không phải vĩ mô. Năm file: [fred.md](10-sources/global/fred.md) · [fx.md](10-sources/global/fx.md) · [yahoo.md](10-sources/global/yahoo.md) · [commodities.md](10-sources/global/commodities.md) · [crypto.md](10-sources/global/crypto.md).

Mục lục chi tiết từng file: [10-sources/README.md](10-sources/README.md).

### 20 · Thiết kế — *explanation*

| File | Nội dung | Trạng thái |
|---|---|---|
| [market-data-store.md](20-design/market-data-store.md) | Cách ly hoàn toàn · Ingester + SSE · lược đồ Timescale · ETL · giám sát hợp đồng | ✅ đã duyệt |
| [news-pipeline.md](20-design/news-pipeline.md) | Lưới AI không đường tắt · taxonomy 20 sub · gắn mã 3 tầng · kho toàn văn | ✅ đã duyệt |
| [chatbot-semantic-layer.md](20-design/chatbot-semantic-layer.md) | Luật phân định 4 tầng · 8 function · ba quy tắc nối dữ liệu vào skill | 🟡 **đề xuất, chưa duyệt** |
| [market-field-selection.md](20-design/market-field-selection.md) | Bảng lấy/bỏ từng trường cho ETL thị trường — 213 dòng, lý do tại chỗ, kèm [bản JSON máy đọc](20-design/market-field-selection.json). Cả hai sinh tự động từ [`gen_field_selection.py`](20-design/gen_field_selection.py), cấm sửa tay | ✅ đã chốt |

### 30 · Tri thức chuyên môn

| Đường dẫn | Nội dung |
|---|---|
| [maintenance.md](30-skills/maintenance.md) | **Đọc trước khi sửa skill** — quyết định không được đảo · 5 lỗi nguồn đã sửa · 5 thứ cố ý · bộ test hồi quy · đoạn dán vào system prompt · ngân sách dòng |
| [terminology.md](30-skills/terminology.md) | Bảng tra **bắt buộc** — hai trục phân loại, chuyển đổi thuật ngữ nguồn, lỗi nhận dạng giọng nói đã sửa |
| [corpus/](30-skills/corpus/) | 96 file tóm tắt bài giảng HP0–HP6 + Trà Chiều — nguyên liệu, không phải tài liệu |

### Ngoài `docs/`

| Đường dẫn | Nội dung |
|---|---|
| [`.claude/skills/`](../.claude/skills/) | Hai skill chứng khoán — sản phẩm chạy được, 3.046 dòng |
