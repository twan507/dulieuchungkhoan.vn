# Finext v2

Nền tảng dữ liệu và phân tích chứng khoán Việt Nam: thu thập dữ liệu thị trường và tin tức từ nhiều nguồn, lưu vào kho riêng, phân phối lại qua REST và SSE, và một chatbot AI trả lời bằng phương pháp phân tích đã được hệ thống hoá thành skill.

**Trạng thái — 2026-08-15:** thiết kế hoàn chỉnh, **chưa viết dòng code sản phẩm nào**. Hai skill chứng khoán đã xong và đã test 6 vòng. **Không còn việc chặn nào phụ thuộc bên ngoài** — giấy phép WiFeed đã chốt và rate limit FiinGroup đã kiểm, cùng ngày 2026-08-15.

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

## Không còn việc chặn bên ngoài — 2026-08-15

Cả ba việc phải chờ bên thứ ba đều đã xong. **Việc kế tiếp là dựng hạ tầng DB (Postgres + Redis)** — việc tự làm được, không phải chờ ai.

> *Xác nhận ngưỡng rate limit với FiinGroup* — **đã kiểm bằng đúng tải ETL kế hoạch ngày 2026-08-15**: burst Screener 52 trang chạy tuần tự (~29 request/phút, 1,8 phút) không gặp tín hiệu chặn nào, và nguồn không trả header hạn mức nào. Xác nhận chính thức từ FiinGroup không còn là điều kiện chặn. Chủ đích **không dò ngưỡng trần**, và nhịp 8 luồng của ETL hằng ngày thì **chưa kiểm** — xem [quy ước chung §10](docs/10-sources/market/00-conventions.md).

> *Chốt giấy phép WiFeed với WiGroup* — **đã chốt ngày 2026-08-15** (chủ dự án xác nhận). Toàn bộ nhánh vĩ mô và hàng hoá, 87 endpoint, không còn bị chặn về pháp lý. Xem [tình trạng pháp lý WiChart](docs/10-sources/macro/wichart.md).

> Việc thứ ba trước đây — *xin bảng ánh xạ mã chỉ tiêu báo cáo tài chính từ FiinGroup* — **đã tự giải quyết ngày 2026-08-14**, không cần chờ họ nữa: 729 mã lấy từ bundle JS của ứng dụng FiinTrade, phủ 100% response thật, kèm tên Việt/Anh (98,5%) và đơn vị dữ liệu (99,7%). Xem [Phụ lục A §A.5](docs/10-sources/market/appendix-A-field-codes.md).

Và một việc gấp không chặn ai nhưng **mỗi ngày trì hoãn là một ngày mất vĩnh viễn**: dựng Ingester để bắt đầu tích luỹ nến 1 phút. Nến intraday không tồn tại ở bất kỳ nguồn nào — không backfill lại được. **Ingester chờ dựng xong hạ tầng DB** (quyết định chủ dự án 2026-08-15); lý do gấp thì không mất đi, và chính nó là lý do hạ tầng DB phải làm ngay.

## Nguyên tắc chung

- **Mọi thứ nguồn tự khai về chính nó đều phải kiểm lại bằng dữ liệu.** Nguyên tắc này đã bắt được 22 cạm bẫy thật trên ba nguồn, không phải giả định.
- **Tài liệu trong `10-sources/` chỉ sửa khi đo lại.** Sửa số mà không đo là nói dối.
- **Số liệu trong skill là tham số ví dụ, không phải dữ kiện.** Toàn bộ là 2022–2024 và đã chết. Công thức thì còn nguyên giá trị.
