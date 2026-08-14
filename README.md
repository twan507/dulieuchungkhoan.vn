# Finext v2

Nền tảng dữ liệu và phân tích chứng khoán Việt Nam: thu thập dữ liệu thị trường và tin tức từ nhiều nguồn, lưu vào kho riêng, phân phối lại qua REST và SSE, và một chatbot AI trả lời bằng phương pháp phân tích đã được hệ thống hoá thành skill.

**Trạng thái:** thiết kế hoàn chỉnh, chưa cài đặt. Hai skill chứng khoán đã xong và đã test 6 vòng.

---

## Bắt đầu từ đâu

| Bạn muốn | Đọc |
|---|---|
| Hiểu toàn cảnh hệ thống | [Kiến trúc tổng thể](docs/00-tong-quan/kien-truc-tong-the.md) |
| Biết làm gì tiếp theo | [Lộ trình hợp nhất](docs/00-tong-quan/lo-trinh.md) |
| Tra một endpoint cụ thể | [Bản đồ tài liệu](docs/README.md) |

## Cấu trúc repo

```
finext-v2/
├── docs/            Toàn bộ tài liệu — 4 tầng, xem docs/README.md
│   ├── 00-tong-quan/     hợp nhất · lộ trình · sổ quyết định
│   ├── 10-nguon-du-lieu/ reference: API và nguồn tin bên ngoài
│   ├── 20-thiet-ke/      explanation: lựa chọn kiến trúc của Finext
│   └── 30-tri-thuc/      corpus và nhật ký dựng skill
├── .claude/skills/  Hai skill chứng khoán — vừa là công cụ dev, vừa là artifact sản phẩm
├── config/          File cấu hình máy đọc (feeds.json)
├── scripts/         Script vận hành (giám sát hợp đồng dữ liệu)
└── (chưa có)        Chỗ cho frontend / backend — layout sẽ chốt khi bắt đầu code
```

## Bốn tầng hệ thống

```
L0  Nguồn ngoài    BVSC+FiinTrade · WiChart · 10 báo điện tử
L1  Thu thập       ETL + Ingester realtime  │  Gom tin + lưới AI
L2  Kho            PostgreSQL + TimescaleDB + Redis
L3  Ngữ nghĩa      view người-đọc-được · function calling
L4  Tri thức       hai skill: tư duy (luôn có mặt) + kiến thức (tải khi cần)
```

## Ba việc chặn nhiều thứ nhất

Đều phụ thuộc bên ngoài, thời gian chờ không kiểm soát được — gửi đi trước, làm việc khác trong lúc chờ:

1. **Xác nhận ngưỡng rate limit** với FiinGroup
2. **Chốt giấy phép WiFeed** với WiGroup — 🔴 chưa có, chặn toàn bộ nhánh vĩ mô và hàng hoá
3. **Xin bảng ánh xạ mã chỉ tiêu báo cáo tài chính** từ FiinGroup

Và một việc gấp không chặn ai nhưng **mỗi ngày trì hoãn là một ngày mất vĩnh viễn**: dựng Ingester để bắt đầu tích luỹ nến 1 phút. Nến intraday không tồn tại ở bất kỳ nguồn nào — không backfill lại được.

## Nguyên tắc chung

- **Mọi thứ nguồn tự khai về chính nó đều phải kiểm lại bằng dữ liệu.** Nguyên tắc này đã bắt được 22 cạm bẫy thật trên ba nguồn, không phải giả định.
- **Tài liệu trong `10-nguon-du-lieu/` chỉ sửa khi đo lại.** Sửa số mà không đo là nói dối.
- **Số liệu trong skill là tham số ví dụ, không phải dữ kiện.** Toàn bộ là 2022–2024 và đã chết. Công thức thì còn nguyên giá trị.
