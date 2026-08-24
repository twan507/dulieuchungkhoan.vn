# dulieuchungkhoan.vn

Nền tảng dữ liệu và phân tích chứng khoán Việt Nam: thu thập dữ liệu thị trường và tin tức từ nhiều nguồn, lưu vào kho riêng, phân phối lại qua REST và SSE, và một chatbot AI trả lời bằng phương pháp phân tích đã được hệ thống hoá thành skill.

**Trạng thái — 2026-08-15:** thiết kế hoàn chỉnh, **chưa viết dòng code sản phẩm nào**. Hai skill chứng khoán đã xong và đã test 6 vòng. **Không còn việc chặn nào phụ thuộc bên ngoài** — giấy phép WiFeed đã chốt và rate limit FiinGroup đã kiểm, cùng ngày 2026-08-15. Cùng ngày, một **đợt khảo sát nguồn 9 nguồn / ~400 lời gọi thật** đã khép độ rộng dữ liệu: thêm **6 nguồn mới** và mở **5 khối dữ liệu** trước nay bỏ trống.

| Khối | Trạng thái | Bằng chứng |
|---|---|---|
| Tài liệu **9 nguồn** — thị trường · vĩ mô VN · quốc tế · tin | ✅ đo thật bằng lời gọi sống | 131 endpoint VN · 87 key · 307 URL · 6 nguồn mới đo 2026-08-15 |
| Độ rộng nguồn dữ liệu | ✅ **khép 2026-08-15** — danh sách *"Ngoài phạm vi"* phân rã hết, không còn mục nào chưa có câu trả lời | [phạm vi nguồn](docs/10-sources/README.md) |
| Từ điển 729 mã trường FiinGroup | ✅ phủ 100% response thật | [field-dictionary.json](docs/10-sources/market/field-dictionary.json) |
| Chọn nguồn chuẩn cho từng chỉ tiêu | ✅ đã chốt | [chọn trường cho ETL thị trường](docs/20-design/market-field-selection.md) |
| Dự án skill | ✅ **đã đóng**, không còn việc treo | [bảo trì skill](docs/30-skills/maintenance.md) |
| Thiết kế kho dữ liệu · pipeline tin | ✅ đã duyệt | chưa cài đặt |
| Tầng ngữ nghĩa nối dữ liệu ↔ skill | 🟡 đề xuất, **chưa duyệt** | [chatbot-semantic-layer.md](docs/20-design/chatbot-semantic-layer.md) |
| Hai skill chứng khoán | ✅ xong, test 6 vòng, đã dừng tối ưu | 3.046 dòng |
| Repo vào git | ✅ khởi tạo 2026-08-14 | commit đầu tiên |
| Toàn bộ phần cài đặt | ❌ chưa bắt đầu | |

Bảng đầy đủ kèm bằng chứng: [lộ trình §0](docs/00-overview/roadmap.md).

**Khối dữ liệu đã phủ — sau khảo sát 2026-08-15**

| Khối | Nguồn chuẩn | Quy mô đo được *(2026-08-15)* |
|---|---|---|
| Cổ phiếu · chỉ số · sổ lệnh · khối ngoại | BVSC | 1.974 cổ phiếu · 20 chỉ số |
| BCTC · tỷ số · dòng tiền · lịch sự kiện | FiinTrade | 729 mã chỉ tiêu |
| **Phái sinh** *(mới)* | BVSC + FiinTrade | 14 hợp đồng · 62 trường · backfill 2.233 phiên từ 31/08/2017 |
| **ETF/quỹ niêm yết** *(mới)* | BVSC + FiinTrade | 31 mã · `iNav` phủ **6/31**, chỉ **2 mã** có thanh khoản thật |
| Vĩ mô · tiền tệ · hàng hoá Việt Nam | WiChart | 87 key |
| **OMO** *(mới)* | SBV | crawl HTML · 🔴 **không backfill được** |
| **Vĩ mô Mỹ** *(mới)* | FRED | 15 series |
| **Tỷ giá + chỉ số đô** *(mới)* | Frankfurter (ECB) | 6 cặp · DXY dựng lại, lệch trung bình **0,180%** trên 248 phiên |
| **Chỉ số quốc tế** *(mới)* | Yahoo Finance | **36 chỉ số / 21 nước** · lợi suất TPCP Mỹ · họ biến động |
| **Vàng/bạc mốc chuẩn** *(mới)* | LBMA | từ **1968**, 14.662 điểm một lời gọi |
| **Crypto + vàng 24/7** *(mới)* | Binance | 10 đồng · PAXG |
| Tin tức | 8 báo điện tử | 47 RSS + 6 crawler |

⛔ **Loại có chủ đích, đừng mở lại:** chứng quyền (342 mã) · lô lẻ (1.890 mã) · trái phiếu (187 mã) — **cả ba đều có dữ liệu**, loại vì không phục vụ phân tích · realtime FiinTrade *(dùng của BVSC)* · luồng cần đăng nhập. **Đã kiểm, không nguồn nào có:** NAV quỹ mở. Lý do từng mục: [phạm vi nguồn §2](docs/10-sources/README.md).

---

## Bắt đầu từ đâu

| Bạn muốn | Đọc |
|---|---|
| Hiểu toàn cảnh hệ thống | [Kiến trúc tổng thể](docs/00-overview/architecture.md) |
| Biết làm gì tiếp theo | [Lộ trình hợp nhất](docs/00-overview/roadmap.md) |
| Tra một endpoint cụ thể | [Bản đồ tài liệu](docs/README.md) |

## Cấu trúc repo

```
dulieuchungkhoan.vn/
├── docs/                Toàn bộ tài liệu — bản đồ ở docs/README.md
│   ├── 00-overview/     kiến trúc · lộ trình · sổ quyết định (chỉ lịch sử)
│   ├── 10-sources/      reference: market · macro · global · news — mỗi nguồn tự chứa đủ đồ nghề
│   ├── 20-design/       lựa chọn kiến trúc của dulieuchungkhoan.vn
│   └── 30-skills/       tài liệu bảo trì + corpus của hai skill
├── .claude/skills/      vn-stock-advisor · vn-stock-knowledge — sản phẩm chạy được
└── (chưa có)            chỗ cho frontend / backend — chốt khi bắt đầu code
```

## Bốn tầng hệ thống

```
L0  Nguồn ngoài    BVSC+FiinTrade · WiChart · SBV · FRED · ECB · Yahoo · LBMA · Binance · 8 báo
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

Và **hai** việc gấp không chặn ai nhưng **mỗi ngày trì hoãn là một ngày mất vĩnh viễn**:

1. **Ingester để tích luỹ nến 1 phút.** Nến intraday không tồn tại ở bất kỳ nguồn nào — không backfill lại được. **Ingester chờ dựng xong hạ tầng DB** (quyết định chủ dự án 2026-08-15); lý do gấp thì không mất đi, và chính nó là lý do hạ tầng DB phải làm ngay.
2. 🔴 **Crawl OMO của Ngân hàng Nhà nước** — phát hiện 2026-08-15. Nguồn **chỉ hiển thị đúng phiên mới nhất, không có kho lưu**; ngày nào không crawl là mất hẳn ngày đó. Thêm nữa, cột **bơm ròng phải tự dựng** từ kỳ hạn và cần **~140 ngày tích luỹ** mới đầy đủ ⇒ càng bắt đầu muộn thì con số ròng càng đến muộn. Xem [`sbv-omo.md`](docs/10-sources/macro/sbv-omo.md).

> 🔴 **Một việc đo chưa xong, phải làm trong phiên:** realtime phái sinh của BVSC. Đợt khảo sát chạy thứ Bảy, thị trường đóng, và server nhận **mọi** chuỗi topic rồi im lặng — nên đăng ký ngoài giờ không chứng minh được gì. Phải nối socket **trong khung 08:45–15:00** *(phái sinh mở sớm hơn cổ phiếu 15 phút)*. Quy trình đo: [lộ trình §5.1](docs/00-overview/roadmap.md).

## Nguyên tắc chung

- **Mọi thứ nguồn tự khai về chính nó đều phải kiểm lại bằng dữ liệu.** Nguyên tắc này đã bắt được **53 cạm bẫy và giới hạn thật** *(đếm 2026-08-15: 26 ở ba nguồn ban đầu — 13 quy ước chung, 6 WiChart, 7 nguồn tin; 27 ở sáu nguồn mới — 8 FRED, 5 tỷ giá, 4 Binance, 4 SBV, 3 Yahoo, 3 LBMA)*, không phải giả định.
- 🔴 **Gọi thật vẫn chưa đủ — phải đối chiếu độ tươi với lịch công bố.** Bài học đắt nhất của đợt 2026-08-15: một nguồn trả `HTTP 200`, đủ 294 dòng, không lỗi nào, mà **dữ liệu đã chết gần một năm**.
- **Tài liệu trong `10-sources/` chỉ sửa khi đo lại.** Sửa số mà không đo là nói dối.
- **Số liệu trong skill là tham số ví dụ, không phải dữ kiện.** Toàn bộ là 2022–2024 và đã chết. Công thức thì còn nguyên giá trị.
