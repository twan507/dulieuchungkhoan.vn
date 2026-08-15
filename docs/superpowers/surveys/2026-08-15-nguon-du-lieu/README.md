# Khảo sát nguồn dữ liệu — đợt 2026-08-15

**Đây là hồ sơ khảo sát thô, không phải tài liệu sống.** Tài liệu chính thức nằm ở [`docs/10-sources/`](../../../10-sources/README.md). Thư mục này giữ **bằng chứng đo** để tra lại khi nghi ngờ một con số, và giữ **hồ sơ sai lầm** để không lặp lại.

Toàn bộ số liệu đo ngày **2026-08-15**, bằng lời gọi thật. Tổng ~400 lời gọi mạng trên 9 nguồn.

## Đọc gì

| File | Nội dung |
|---|---|
| [ra-soat-nguon-cu.md](ra-soat-nguon-cu.md) | **Đọc trước** — trạng thái 10 mục "Ngoài phạm vi": mở được mục nào, loại có chủ đích mục nào |
| [ra-soat-viec-chua-kiem.md](ra-soat-viec-chua-kiem.md) | 56 mục "chưa kiểm" phân loại A/B/C/D |
| [viec-con-treo.md](viec-con-treo.md) | Việc phải làm tiếp, kèm quy trình đo sẵn |
| [ops-ledger.md](ops-ledger.md) | Sổ vận hành — mọi phán quyết và lý do, theo thứ tự thời gian |

## Báo cáo theo nguồn

| Nguồn | Báo cáo | Kết luận một dòng |
|---|---|---|
| BVSC — phái sinh | [report-bvsc-derivative.md](report-bvsc-derivative.md) | Có phái sinh; tài liệu cũ ghi sai. 14 hợp đồng, 9 năm lịch sử qua FiinTrade |
| OMO — chỗ trống | [report-omo-gap.md](report-omo-gap.md) | Không nguồn nào có OMO |
| OMO — tìm nguồn | [report-omo-sources.md](report-omo-sources.md) | **Chốt SBV** (crawl hằng ngày, không backfill được) |
| FRED | [report-fred.md](report-fred.md) | Lấy, 15 series. Giấy phép chủ dự án đã xử lý xong |
| akshare | [report-akshare.md](report-akshare.md) | Gần như bỏ — vĩ mô Mỹ chết ~1 năm mà vẫn trả HTTP 200 |
| Nguồn miễn phí + DXY | [report-more-sources.md](report-more-sources.md) | **Frankfurter** dựng lại DXY, sai số 0,18% |
| Binance | [report-binance.md](report-binance.md) | Lấy PAXG (vàng 24/7) + 10 đồng crypto lớn |
| yfinance | [report-yfinance.md](report-yfinance.md) | **36 chỉ số quốc tế/21 nước**, trễ 0 ngày |
| Vàng & dầu — đối chiếu | [report-vang-dau-doi-chieu-investing.md](report-vang-dau-doi-chieu-investing.md) | WiChart **không lệch**; chênh 2% là backwardation |
| Quỹ Việt Nam | [report-du-lieu-quy-vn.md](report-du-lieu-quy-vn.md) | `iNav` của FiinTrade — 6/31 mã, 2 mã có thanh khoản thật |

## 🔴 Hồ sơ sai lầm — giữ lại có chủ đích

[report-wichart-oil-deviation.md](report-wichart-oil-deviation.md) **SAI và đã bị thay thế**. Giữ lại vì hai bài học:

1. **Mốc thời gian WiChart là nửa đêm giờ Việt Nam, không phải UTC.** Parse UTC làm lệch cả chuỗi một ngày và tạo ra kết luận sai hoàn toàn ("WiChart lệch 3,35%, nên thay" → thật ra 0,50%, không cần thay).
2. **Báo cáo đó viết "đã thử ghép d−1" trong khi chưa hề chạy phép thử ấy.** Câu bịa để gia cố kết luận lại chính là câu chặn mất phép kiểm sẽ tìm ra lỗi.

## Dữ liệu thô

**Không commit** — ~80 MB log gọi thật nằm ở scratchpad của phiên khảo sát và sẽ mất. Mọi con số cần thiết đã nằm trong các báo cáo trên.

## Ba luật rút ra, áp cho mọi việc sau

1. **Mọi chuỗi WiChart phải parse bằng `Asia/Ho_Chi_Minh`.**
2. **Không viết "đã thử X" nếu chưa chạy X.**
3. **Gọi thật là chưa đủ** — phải **gọi thật + đối chiếu độ tươi với lịch công bố**. akshare gọi thành công, trả đủ 294 dòng, dữ liệu chết một năm, không lỗi nào.
