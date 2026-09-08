# Bản đồ tài liệu dulieuchungkhoan.vn

Bốn tầng, đọc theo số. Mỗi tầng có một loại nội dung và một luật sửa riêng. Dòng cuối bảng không phải một tầng — nó là kho lịch sử.

| Tầng | Chứa gì | Luật sửa |
|---|---|---|
| [`00-overview/`](00-overview/) | Hợp nhất ba khối, lộ trình, sổ quyết định (chỉ lịch sử) | Cập nhật khi kiến trúc đổi |
| [`10-sources/`](10-sources/) | **Reference** — sự thật đo được về hệ thống của người khác | Chỉ sửa khi **đo lại** |
| [`20-design/`](20-design/) | **Explanation** — lựa chọn của dulieuchungkhoan.vn | Sửa được, lý do viết thẳng tại chỗ |
| [`30-skills/`](30-skills/) | Corpus và tài liệu bảo trì hai skill chứng khoán | Corpus bất biến; tài liệu bảo trì cập nhật theo trạng thái thật |
| [`90-records/`](90-records/) | **Hồ sơ làm việc** — spec/plan của task lớn và hồ sơ khảo sát | Bản ghi lịch sử — thêm mới, không viết lại quá khứ. Tri thức rút ra phải đi vào tài liệu sống |
| [`00-overview/decisions/`](00-overview/decisions/) | [Sổ quyết định (ADR)](00-overview/decisions/) — bản ghi lịch sử | Chỉ ghi lịch sử quyết định. Tài liệu sống phải tường minh, không trỏ về đây; xoá cả thư mục này chỉ được phép mất lịch sử |

---

## Đọc gì trước

**Muốn hiểu toàn cảnh** → [kiến trúc tổng thể](00-overview/architecture.md). Bốn tầng hệ thống, ba mắt xích nối ba khối, và lỗ hổng gác cổng phạm vi — đã vá ở lát 10.

**Sắp bắt tay làm** → [lộ trình hợp nhất](00-overview/roadmap.md). Việc nào chặn việc nào, việc nào gấp vì mất dữ liệu theo thời gian, việc nào tưởng để ngỏ mà đã có đáp án.

**Sắp gọi API** → [quy ước chung](10-sources/market/00-conventions.md) trước tiên, 14 bẫy triển khai nằm ở đó.

**Sắp sửa skill** → [bảo trì skill](30-skills/maintenance.md) và [bảng thuật ngữ](30-skills/terminology.md). Cả hai là **bắt buộc**, không phải tham khảo — file đầu ghi những chỗ sửa nhầm sẽ hỏng skill mà không có gì báo lỗi.

## Toàn bộ tài liệu

### 00 · Tổng quan

| File | Nội dung |
|---|---|
| [architecture.md](00-overview/architecture.md) | Bốn tầng L0–L4 · ranh giới tài liệu · ba mắt xích nối ba khối · lỗ hổng gác cổng phạm vi *(đã vá lát 10)* · rủi ro pháp lý theo nguồn |
| [roadmap.md](00-overview/roadmap.md) | Trạng thái từng khối · việc chặn nhiều nhất · việc gấp vì mất dữ liệu · cây phụ thuộc · việc còn để ngỏ · ba bẫy ngày đầu |
| [reference-repos.md](00-overview/reference-repos.md) | Sổ đăng ký repo GitHub tham chiếu — đã dùng · kho nguồn · đã loại kèm lý do |
| [decisions/](00-overview/decisions/) | Kho lịch sử quyết định kiến trúc. **Danh sách ADR do [`decisions/README.md`](00-overview/decisions/README.md) sở hữu** — không chép lại ở đây, hai bản sẽ trôi lệch (§1.6); bản chép cũ đã dừng ở 0006 trong khi 0007 đã tồn tại |

### 10 · Nguồn dữ liệu — *reference*

| Thư mục | Nguồn | Quy mô | Kiểm chứng |
|---|---|---|---|
| [market/](10-sources/market/) | BVSC + FiinTrade | 44 REST + 5 topic realtime · **phái sinh 14 hợp đồng · ETF/quỹ 31 mã** | 2026-08-10, mẫu 51 mã · phái sinh và ETF 2026-08-15 |
| [macro/](10-sources/macro/) | WiChart (WiGroup) · **SBV** | 87 REST + **1 trang crawl OMO** | 2026-08-12, toàn bộ 87 key · OMO 2026-08-15 |
| **[global/](10-sources/global/)** | **FRED · Frankfurter (ECB) · Yahoo · LBMA · Binance** | 15 series vĩ mô Mỹ · 6 cặp tiền + DXY dựng lại · 36 chỉ số/21 nước · vàng-bạc từ 1968 · 10 đồng crypto + PAXG | **2026-08-15**, ~400 lời gọi thật cả đợt |
| [news/](10-sources/news/) | 8 báo điện tử | 47 RSS + 8 nguồn crawl *(6 thường + 2 backfill)* | 2026-08-13, 307 URL · 1.408 tiêu đề · cấu trúc trang bài 2026-08-15, 33 bài |
| **[llm/](10-sources/llm/)** | **MiniMax M3** — nhà cung cấp LLM duy nhất (Token Plan) | 1 model · 2 giao diện tương thích · endpoint quota | **2026-09-06**, ≈45 lời gọi thật |

Mỗi nguồn tự chứa đủ đồ nghề: `macro/` có [`verify_wichart.py`](10-sources/macro/verify_wichart.py) — tự kiểm 509 khẳng định của tài liệu WiChart với API sống; `news/` có [`feeds.json`](../backend/etl/data/feeds.json) — 47 feed + taxonomy dạng máy đọc — và [`article-structure.md`](10-sources/news/article-structure.md) — selector container chính cùng luật bỏ boilerplate riêng từng nguồn.

**`global/` là nhóm mới, lập 2026-08-15.** Lý do tách khỏi `macro/`: chỉ số cổ phiếu quốc tế và crypto không phải vĩ mô. Năm file: [fred.md](10-sources/global/fred.md) · [fx.md](10-sources/global/fx.md) · [yahoo.md](10-sources/global/yahoo.md) · [commodities.md](10-sources/global/commodities.md) · [crypto.md](10-sources/global/crypto.md).

Mục lục chi tiết từng file: [10-sources/README.md](10-sources/README.md).

### 20 · Thiết kế — *explanation*

**Danh sách file do [`20-design/README.md`](20-design/README.md) sở hữu** — không chép lại ở đây, hai bản sẽ trôi lệch (§1.6). Bản chép cũ đã thiếu `industry-mapping.md` và còn tả `industry-tree.md` bằng một mục §5 đã bị xoá.

Vào đó nếu muốn biết: ranh giới process · chiến lược test · kho dữ liệu thị trường · pipeline tin · tầng ngữ nghĩa chatbot · chọn trường ETL · **cây ngành** và **bảng map ngành**.

⚠️ Ba file trong đó **sinh tự động, cấm sửa tay** — `market-field-selection.md` và `industry-mapping.*`; bản JSON của market-field-selection cùng luật đó nhưng nay nằm ở `backend/etl/data/` (dời 2026-09-08).

### 30 · Tri thức chuyên môn

**Danh sách file do [`30-skills/README.md`](30-skills/README.md) sở hữu** — không chép lại ở đây, hai bản sẽ trôi lệch (§1.6). Bản chép cũ đã tồn tại tới 2026-09-07 và là một trong ba chỗ trùng chủ mà đợt audit bắt được.

Vào đó nếu muốn biết: **bảo trì skill** (đọc trước mọi thay đổi trong `backend/agent/skills/`) · **bảng thuật ngữ** (bắt buộc) · **corpus** bài giảng.

### Ngoài `docs/`

| Đường dẫn | Nội dung |
|---|---|
| [`backend/agent/skills/`](../backend/agent/skills/) | Hai skill chứng khoán — sản phẩm chạy được, 3.046 dòng |
