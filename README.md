# Finext v2

Nền tảng dữ liệu và phân tích chứng khoán Việt Nam: thu thập dữ liệu thị trường và tin tức từ nhiều nguồn, lưu vào kho riêng, phân phối lại qua REST và SSE, và một chatbot AI trả lời bằng phương pháp phân tích đã được hệ thống hoá thành skill.

**Trạng thái — 2026-08-15:** thiết kế hoàn chỉnh, **chưa viết dòng code sản phẩm nào**. Hai skill chứng khoán đã xong và đã test 6 vòng. Chỉ còn **một** việc chặn, phụ thuộc bên ngoài — giấy phép WiFeed đã chốt 2026-08-15.

| Khối | Trạng thái | Bằng chứng |
|---|---|---|
| Tài liệu ba nguồn — thị trường · vĩ mô · tin | ✅ đo thật bằng lời gọi sống | 131 endpoint · 87 key · 307 URL |
| Từ điển 729 mã trường FiinGroup | ✅ phủ 100% response thật | [field-dictionary.json](docs/10-sources/market/field-dictionary.json) |
| Chọn nguồn chuẩn cho từng chỉ tiêu | ✅ đã chốt | [chọn trường cho ETL thị trường](docs/20-design/market-field-selection.md) |
| Dự án skill | ✅ **đã đóng**, không còn việc treo | [bảo trì skill](docs/30-skills/maintenance.md) |
| Thiết kế kho dữ liệu · pipeline tin | ✅ đã duyệt | chưa cài đặt |
| Tầng ngữ nghĩa nối dữ liệu ↔ skill | 🟡 đề xuất, **chưa duyệt** | [chatbot-semantic-layer.md](docs/20-design/chatbot-semantic-layer.md) |
| Hai skill chứng khoán | ✅ xong, test 6 vòng, đã dừng tối ưu | 3.046 dòng |
| Repo vào git | ✅ khởi tạo 2026-08-14 | commit đầu tiên |
| Toàn bộ phần cài đặt | ❌ chưa bắt đầu | |

Bảng đầy đủ kèm bằng chứng: [lộ trình §0](docs/00-overview/roadmap.md).

---

## Bắt đầu từ đâu

| Bạn muốn | Đọc |
|---|---|
| Hiểu toàn cảnh hệ thống | [Kiến trúc tổng thể](docs/00-overview/architecture.md) |
| Biết làm gì tiếp theo | [Lộ trình hợp nhất](docs/00-overview/roadmap.md) |
| Tra một endpoint cụ thể | [Bản đồ tài liệu](docs/README.md) |

## Cấu trúc repo

```
finext-v2/
├── docs/                Toàn bộ tài liệu — bản đồ ở docs/README.md
│   ├── 00-overview/     kiến trúc · lộ trình · sổ quyết định (chỉ lịch sử)
│   ├── 10-sources/      reference: market · macro · news — mỗi nguồn tự chứa đủ đồ nghề
│   ├── 20-design/       lựa chọn kiến trúc của Finext
│   └── 30-skills/       tài liệu bảo trì + corpus của hai skill
├── .claude/skills/      vn-stock-advisor · vn-stock-knowledge — sản phẩm chạy được
└── (chưa có)            chỗ cho frontend / backend — chốt khi bắt đầu code
```

## Bốn tầng hệ thống

```
L0  Nguồn ngoài    BVSC+FiinTrade · WiChart · 10 báo điện tử
L1  Thu thập       ETL + Ingester realtime  │  Gom tin + lưới AI
L2  Kho            PostgreSQL + TimescaleDB + Redis
L3  Ngữ nghĩa      view người-đọc-được · function calling
L4  Tri thức       hai skill: tư duy (luôn có mặt) + kiến thức (tải khi cần)
```

## Một việc chặn còn lại

Nó phụ thuộc bên ngoài, thời gian chờ không kiểm soát được — gửi đi trước, làm việc khác trong lúc chờ:

1. **Xác nhận ngưỡng rate limit** với FiinGroup — chặn mọi ETL. Gửi kèm luôn danh sách 11 mã chỉ tiêu chưa giải mã được

> Việc chặn thứ hai trước đây — *chốt giấy phép WiFeed với WiGroup* — **đã chốt ngày 2026-08-15** (chủ dự án xác nhận). Toàn bộ nhánh vĩ mô và hàng hoá, 87 endpoint, không còn bị chặn về pháp lý. Xem [tình trạng pháp lý WiChart](docs/10-sources/macro/wichart.md).

> Việc thứ ba trước đây — *xin bảng ánh xạ mã chỉ tiêu báo cáo tài chính từ FiinGroup* — **đã tự giải quyết ngày 2026-08-14**, không cần chờ họ nữa: 729 mã lấy từ bundle JS của ứng dụng FiinTrade, phủ 100% response thật, kèm tên Việt/Anh (98,5%) và đơn vị dữ liệu (99,7%). Xem [Phụ lục A §A.5](docs/10-sources/market/appendix-A-field-codes.md).

Và một việc gấp không chặn ai nhưng **mỗi ngày trì hoãn là một ngày mất vĩnh viễn**: dựng Ingester để bắt đầu tích luỹ nến 1 phút. Nến intraday không tồn tại ở bất kỳ nguồn nào — không backfill lại được.

## Nguyên tắc chung

- **Mọi thứ nguồn tự khai về chính nó đều phải kiểm lại bằng dữ liệu.** Nguyên tắc này đã bắt được 22 cạm bẫy thật trên ba nguồn, không phải giả định.
- **Tài liệu trong `10-sources/` chỉ sửa khi đo lại.** Sửa số mà không đo là nói dối.
- **Số liệu trong skill là tham số ví dụ, không phải dữ kiện.** Toàn bộ là 2022–2024 và đã chết. Công thức thì còn nguyên giá trị.
