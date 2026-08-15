# Brief — Nguồn dữ liệu miễn phí khác + nguồn 6 cặp tiền dựng DXY hằng ngày

## Bối cảnh

Repo `D:\twan-projects\finext-v2` — nền tảng dữ liệu & phân tích chứng khoán Việt Nam.

**Đọc trước để biết đã có gì, tránh làm trùng:**
- `docs/10-sources/README.md` — bản đồ nguồn hiện có
- `docs/10-sources/macro/wichart.md` — vĩ mô trong nước (87 endpoint)
- `scratchpad/report-fred.md` — khảo sát FRED vừa xong
- `scratchpad/report-omo-gap.md` — FiinTrade có sẵn 7 chỉ tiêu quốc tế

**Đã khảo sát rồi, ĐỪNG làm lại:** WiChart · BVSC · FiinTrade · FRED · akshare *(một agent khác đang chạy akshare song song — tuyệt đối không đụng vào akshare)*.

## Hai việc

### VIỆC 1 (ưu tiên cao) — Nguồn 6 cặp tiền hằng ngày để dựng lại DXY

**Bối cảnh đã đo:** FRED có chỉ số đô Mỹ (`DTWEXBGS`) nhưng thuộc bản công bố **H.10 của Fed, ra mỗi thứ Hai** → trễ dao động 3–9 ngày. DXY "chuẩn" (chỉ số ICE) có bản quyền, không có trên FRED.

**Controller đã kiểm và xác nhận:** dựng lại DXY từ 6 cặp tiền **chạy đúng**. Công thức:

```
DXY = 50.14348112 × EURUSD^(-0.576) × USDJPY^(0.136) × GBPUSD^(-0.119)
                  × USDCAD^(0.091)  × USDSEK^(0.042) × USDCHF^(0.036)
```

Kiểm bằng dữ liệu FRED ngày 2026-08-07 (EURUSD 1,1559 · USDJPY 157,54 · GBPUSD 1,3498 · USDCAD 1,3933 · USDSEK 9,4751 · USDCHF 0,8078) → **99,5642**, giá trị hợp lý. Tổng trị tuyệt đối trọng số = 1 ✓.

**Vấn đề còn lại:** cả 6 series `DEX*` trên FRED **cũng dừng ở 2026-08-07** — cùng bản H.10 theo tuần. Nên phải tìm nguồn khác cho 6 cặp.

**Việc của bạn:** tìm và **gọi thật** các nguồn tỷ giá miễn phí, cập nhật ít nhất hằng ngày. Ứng viên gợi ý (tự xác minh, đừng tin sẵn): ECB reference rates / Frankfurter API · exchangerate.host · open.er-api.com · Stooq · Yahoo Finance · Alpha Vantage · Twelve Data · ExchangeRate-API · Currency API (Fawaz Ahmed, trên CDN).

Với mỗi nguồn dùng được, đo: có đủ **cả 6 cặp** không · tần suất & giờ cập nhật · độ trễ thật · **có lịch sử không và sâu bao nhiêu** (quan trọng — cần backfill) · cần khoá API không · hạn mức · định dạng · điều khoản quan sát được.

**Nghiệm thu Việc 1:** chọn nguồn tốt nhất, lấy 6 cặp của **một ngày gần nhất**, **tự tính DXY bằng công thức trên**, và **đối chiếu với giá trị DXY thật cùng ngày** tìm được từ một nguồn độc lập. Ghi rõ sai lệch. Nếu lệch nhiều thì nói thẳng và truy nguyên nhân (khác giờ chốt? khác convention?).

⚠️ Sắc thái phải ghi: tỷ giá ECB là **fixing 14:15 CET**, không phải giá đóng cửa liên tục như ICE DXY. Nên DXY dựng lại ≈ ảnh chụp tại thời điểm fixing, không trùng khít DXY đóng cửa. Với phân tích vĩ mô thì đủ, nhưng phải ghi rõ.

### VIỆC 2 — Còn nguồn miễn phí nào tốt hơn / phủ rộng hơn

Chỉ thị chủ dự án: *"ngoài akshare và fred cũng thử nghiên cứu thêm xem còn nguồn nào miễn phí mà dữ liệu dùng đc tốt hơn để phủ kín hơn ko."*

Khảo sát các hướng sau, mỗi hướng kết luận có/không kèm bằng chứng:

| Nhóm | Ứng viên (tự xác minh) |
|---|---|
| **Tổng hợp nhiều nhà cung cấp** | **DBnomics** (gộp IMF/OECD/BIS/Eurostat, có API — ứng viên mạnh, kiểm kỹ) · Nasdaq Data Link (Quandl) |
| **Tổ chức quốc tế** | World Bank API · IMF (IFS, WEO) · OECD · Eurostat · BIS · ADB |
| **Thị trường & giá** | Stooq · Yahoo Finance (`yfinance`) · Alpha Vantage · Twelve Data · Finnhub · Tiingo · Marketstack |
| **Năng lượng & hàng hoá** | EIA API · World Bank Pink Sheet · LME/CME công khai |
| **Việt Nam** | GSO (Tổng cục Thống kê) · Bộ Tài chính · vnstock (thư viện Python VN) |

Với mỗi nguồn đáng giá: **nó lấp được chỗ nào mà WiChart/FiinTrade/FRED chưa có?** Nếu chỉ trùng lặp thì nói thẳng là không cần.

**Quan tâm đặc biệt hai chỗ hụt đã biết:**
1. **Chỉ số đô Mỹ hằng ngày** (Việc 1)
2. **Chỉ số chứng khoán quốc tế** — FRED có nhưng `SP500`/`DJIA`/`NASDAQCOM` đều **`copyrighted: pre-approval required`**. Có nguồn miễn phí nào cho chỉ số quốc tế mà điều khoản thoáng hơn không?

### Trần request
**Tổng 60 lời gọi mạng cho cả hai việc.** Tuần tự, nghỉ ≥1s giữa các lời gọi cùng host. **Không dò ngưỡng chặn** — chạy đủ để kết luận là được.

## Luật viết
- **Chỉ ghi cái đo được.** Chưa gọi thật → "chưa kiểm". Suy đoán → gắn nhãn.
- Ngày đo 2026-08-15 cạnh mọi con số. Tiếng Việt. Không tô hồng.
- Pháp lý: chỉ ghi điều khoản **quan sát được**, không phân tích, không đề xuất việc pháp lý.
- Python: luôn `PYTHONIOENCODING=utf-8` (Windows cp1252 sẽ crash).
- Nếu nguồn nào đòi khoá API mà không có sẵn thì ghi "cần đăng ký, chưa kiểm" — **đừng tự đăng ký tài khoản**.

## Đầu ra
1. Báo cáo: `C:\Users\tuanb\AppData\Local\Temp\claude\D--twan-projects-finext-v2\8bdadd16-750b-49f9-979c-7dea29fe37ac\scratchpad\report-more-sources.md`
2. Mẫu thô: `...\scratchpad\more-sources-raw\`

⚠️ **Nếu harness chặn ghi file `.md`**, ghi bằng `.txt` HOẶC trả toàn văn trong tin nhắn cuối — đừng bỏ mất nội dung.

**CẤM:** mọi lệnh git; sửa file trong `D:\twan-projects\finext-v2`. Chỉ đọc repo, ghi scratchpad. **KHÔNG dispatch subagent.** **KHÔNG đụng akshare** (agent khác đang làm).

Trả về ngắn gọn: trạng thái, số lời gọi, kết quả Việc 1 (nguồn chọn + sai lệch DXY), 5 nguồn đáng lấy nhất ở Việc 2, khuyến nghị.
