# Brief — Khảo sát API công khai của Binance: có gì hợp với Finext

## Bối cảnh

Repo `D:\twan-projects\finext-v2` — nền tảng dữ liệu & phân tích **chứng khoán Việt Nam** (không phải sàn crypto).

**Đọc trước để biết dự án đã có gì và đang thiếu gì:**
- `docs/10-sources/README.md` — bản đồ nguồn. ⚠️ Lưu ý mục *Ngoài phạm vi* hiện đang liệt **"Crypto"**.
- `scratchpad/report-fred.md` — khảo sát FRED
- `scratchpad/report-wichart-oil-deviation.md` — **đọc kỹ**, đây là chỗ đau đã đo được
- `docs/10-sources/macro/wichart.md` §5.3 — 61 mặt hàng hàng hoá hiện có

**Chỉ thị chủ dự án:** *"nghiên cứu binance xem họ public những gì hợp với ta không, tôi vẫn hay thấy bảo binance có api dữ liệu ổn lắm."*

## ⚠️ Đề bài thật — đọc kỹ chỗ này

Binance nổi tiếng vì **hạ tầng API tốt** (miễn phí, không cần khoá cho dữ liệu thị trường, hạn mức rộng, có WebSocket, lịch sử sâu). **Điều đó gần như chắc chắn đúng và KHÔNG phải câu hỏi.**

Câu hỏi thật là: **Binance cho dự án này dữ liệu gì mà ta chưa có?** Một báo cáo khen API Binance nhanh và ổn định mà không trả lời được câu đó là **báo cáo hỏng**.

Đây là dự án chứng khoán Việt Nam. Crypto tự thân **đang nằm ngoài phạm vi**. Nên hãy soi vào những chỗ Binance chạm được vào nhu cầu đã biết:

### Giả thuyết 1 (mạnh nhất) — Vàng token hoá làm nguồn giá vàng realtime
Binance niêm yết **PAXG** (Paxos Gold, 1 token ≈ 1 ounce vàng vật chất) và có thể có **XAUT** (Tether Gold). Nếu đúng thì đây là **giá vàng thế giới 24/7, realtime, miễn phí, không cần khoá** — trong khi WiChart `vang_the_gioi` chỉ cập nhật theo ngày.

**Phải đo:** lấy chuỗi `PAXGUSDT` nến ngày, ghép theo ngày với WiChart `vang_the_gioi`
(`GET https://api.wichart.vn/vietnambiz/vi-mo?key=hang_hoa&name=vang_the_gioi`, mảng xếp **mới trước**, mốc thời gian là epoch **mili giây**)
rồi tính **lệch tuyệt đối trung bình, độ lệch chuẩn, biên độ, tỉ lệ ngày lệch >2%** — đúng phương pháp đã dùng cho dầu ở `report-wichart-oil-deviation.md`.
Nếu PAXG bám sát vàng thật thì nó là ứng viên **thay hoặc bổ trợ** WiChart ở mặt hàng vàng.
⚠️ Cảnh báo: PAXG là **tài sản giao dịch trên sàn**, có thể có premium/discount so với giá vàng giao ngay, và thanh khoản mỏng hơn thị trường vàng thật. Phải đo premium, đừng giả định bằng 0.

### Giả thuyết 2 — Cặp tiền cho việc dựng lại DXY
Dự án cần 6 cặp: EUR, JPY, GBP, CAD, SEK, CHF (công thức và kiểm chứng ở `scratchpad/brief-more-sources.md`).
Binance có `EURUSDT`, `GBPUSDT`, và một số cặp fiat khác. **Phải kiểm đủ 6 cặp có không** — nghi ngờ mạnh là **thiếu SEK và CAD**, có thể thiếu cả JPY/CHF dạng dùng được.
Nếu thiếu dù chỉ một cặp thì **không dựng được DXY** → nói thẳng, đừng cố vớt vát.
⚠️ Thêm nữa: giá là **so với USDT (stablecoin), không phải USD**. Phải đo chênh lệch USDT/USD (kiểm `USDCUSDT` hoặc tương đương) — nếu USDT lệch neo thì mọi tỷ giá suy ra đều lệch theo.

### Giả thuyết 3 — Khẩu vị rủi ro toàn cầu
`vn-stock-advisor` cần đo khẩu vị rủi ro (hiện dùng VIX từ FRED, mà VIX lại **có bản quyền CBOE**). BTC/ETH là thước khẩu vị rủi ro chạy 24/7, không bản quyền.
Đây là **đề xuất mở**, không phải nhu cầu skill đã nêu — ghi như một khả năng, đừng thổi lên.

### Giả thuyết 4 — Có hàng hoá nào khác không
Binance từng có sản phẩm phái sinh gắn với hàng hoá. Kiểm xem hiện còn gì liên quan **dầu, bạc, kim loại** không. Nghi ngờ là **không** — nếu vậy thì kết luận thẳng: **Binance không giúp gì cho chỗ đau giá dầu.**

## Nhiệm vụ

### Bước 1 — Nắm API công khai
`https://api.binance.com` (và `data-api.binance.vision` nếu có). Nắm:
- Nhóm endpoint dữ liệu thị trường **không cần xác thực**: `/api/v3/exchangeInfo`, `/ticker/24hr`, `/klines`, `/avgPrice`, `/depth`, `/trades`
- **Hạn mức chính thức Binance công bố** (hệ thống `weight`, header `X-MBX-USED-WEIGHT-*`) — ghi lại con số tài liệu nêu, và ghi header thật quan sát được
- Kho dữ liệu lịch sử `data.binance.vision` (file ZIP/CSV theo ngày/tháng) — có phù hợp cho backfill không
- Điều khoản sử dụng **quan sát được** (chỉ ghi, không phân tích pháp lý — chủ dự án tự xử lý)
- ⚠️ Kiểm luôn: **có bị chặn theo vùng địa lý không** khi gọi từ Việt Nam

### Bước 2 — Gọi thật và đo
**Trần 60 lời gọi mạng.** Tuần tự, nghỉ ≥1s. **KHÔNG dò ngưỡng chặn** — Binance công bố hạn mức rồi, chạy dưới mức đó là đủ.

Bắt buộc làm: kiểm đủ 4 giả thuyết trên, trong đó **Giả thuyết 1 phải có bảng đối chiếu số với WiChart**.
Ghi cho mỗi endpoint dùng được: lược đồ trả về (Binance trả **mảng vị trí, không phải object có tên** ở `/klines` — ghi rõ ý nghĩa từng vị trí), kiểu dữ liệu (Binance hay trả **số dạng chuỗi**), độ trễ, kích thước, độ sâu lịch sử, giới hạn số nến mỗi lần gọi.

### Bước 3 — Kết luận
Bảng: **thứ Binance cho** × **dự án đã có chưa** × **hơn/kém nguồn hiện tại ở điểm nào** × **có nên lấy không**.
Kết luận phải ở một trong ba dạng, không lấp lửng:
- "Lấy, cho mục X" — kèm số chứng minh
- "Chưa lấy, vì crypto ngoài phạm vi — nhưng nếu chủ dự án mở phạm vi thì được cái Y"
- "Không lấy, vì không lấp được chỗ nào" — kèm lý do đo được

## Luật viết
- **Chỉ ghi cái đo được.** Chưa gọi thật → "chưa kiểm". Suy đoán → gắn nhãn suy đoán.
- Ngày đo 2026-08-15 cạnh mọi con số. Tiếng Việt. Không tô hồng, không quảng cáo hộ Binance.
- Python: luôn `PYTHONIOENCODING=utf-8`.
- **Không đăng ký tài khoản, không tạo khoá API, không đụng bất kỳ endpoint giao dịch nào.** Chỉ dữ liệu thị trường công khai, chỉ đọc.

## Đầu ra
1. Báo cáo: `C:\Users\tuanb\AppData\Local\Temp\claude\D--twan-projects-finext-v2\8bdadd16-750b-49f9-979c-7dea29fe37ac\scratchpad\report-binance.md`
2. Mẫu thô: `...\scratchpad\binance-raw\`

⚠️ Nếu harness chặn ghi `.md` thì ghi `.txt` HOẶC trả toàn văn trong tin nhắn cuối — đừng bỏ mất nội dung.

**CẤM:** mọi lệnh git; sửa file trong `D:\twan-projects\finext-v2`. Chỉ đọc repo, ghi scratchpad. **KHÔNG dispatch subagent.**
Có 3 agent khác đang chạy song song (akshare · nguồn OMO · nguồn miễn phí+DXY+hàng hoá) — **đừng đụng vào phần việc của họ**, chỉ làm Binance.

Trả về ngắn gọn: trạng thái, số lời gọi, kết quả 4 giả thuyết (đặc biệt số đối chiếu PAXG↔vàng WiChart), khuyến nghị một dòng.
