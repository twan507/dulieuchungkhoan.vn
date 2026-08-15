# Brief — Khảo sát yfinance: nguồn CUỐI CÙNG của đợt chốt nguồn

## Bối cảnh — đọc trước

Repo `D:\twan-projects\finext-v2` — nền tảng dữ liệu & phân tích **chứng khoán Việt Nam**.

Chủ dự án: *"yfinance cũng là 1 nguồn khá rộng, tôi nghĩ đây là nguồn cuối cùng chúng ta cần, khảo sát nốt xem nó lấy được những gì — tôi nghĩ khá nhiều đó — và chọn lọc xem."*

**Hai từ khoá của đề bài: "khá rộng" và "chọn lọc".** yfinance chắc chắn lấy được rất nhiều thứ. Việc của bạn **không phải liệt kê tất cả** mà là **lọc ra thứ dự án thật sự cần và chưa có**. Một báo cáo liệt kê 40 khả năng của yfinance mà không nói cái nào đáng lấy là **báo cáo hỏng**.

### Đọc để biết đã có gì — TRÁNH LÀM TRÙNG

| File | Nội dung |
|---|---|
| `scratchpad/report-more-sources.md` | ⚠️ **§3 đã đo endpoint Yahoo `v8/finance/chart` trực tiếp** — 24/24 lời gọi `200`, trung vị ~170 ms, đã xác nhận `^GSPC` (1927→), `^DJI`, `^N225`, `^VIX`, **`DX-Y.NYB`** (DXY ICE, 1971→), và 6 cặp tiền. **ĐỪNG đo lại những cái này.** |
| `scratchpad/report-vang-dau-doi-chieu-investing.md` | Yahoo `CL=F` = tương lai WTI, trùng khít Investing. Đã đo. |
| `scratchpad/report-fred.md` | FRED đã chốt lấy (chủ dự án đã xin phép xong) |
| `scratchpad/report-akshare.md` | akshare — **đọc §1 và §10**, bài học về hỏng im lặng và cách phòng |
| `docs/10-sources/README.md` · `macro/wichart.md` | nguồn hiện có |

### Bức tranh nguồn sau khi chốt

| Khối | Đã chốt |
|---|---|
| Cổ phiếu/chỉ số/phái sinh Việt Nam | BVSC + FiinTrade |
| Vĩ mô & hàng hoá Việt Nam/Trung Quốc | WiChart |
| OMO | SBV (crawl) |
| Vĩ mô Mỹ | FRED |
| Tỷ giá → dựng DXY | Frankfurter (ECB) |
| Vàng | WiChart + PAXG (24/7) + LBMA (lịch sử 1968) |
| Dầu | **cả giao ngay (FRED) lẫn tương lai (WiChart/`CL=F`)** |
| Chỉ số quốc tế | FiinTrade (`DJI`/`NASDAQ`/`N225`) |

## Nhiệm vụ

### Bước 1 — Nắm thư viện
- Phiên bản hiện tại, nhịp bảo trì, **số commit vá do Yahoo đổi giao thức** (dấu hiệu rủi ro, giống bài học akshare `fix(...)` 11/19 commit)
- **Cơ chế xác thực:** yfinance nay cần cookie + crumb, và có bản dùng `curl_cffi` để giả vân tay TLS. Đây là **dấu hiệu Yahoo đang chủ động chặn** — ghi rõ mức độ.
- Giấy phép thư viện; **điều khoản dữ liệu Yahoo quan sát được** (chỉ ghi cái đọc được, không phân tích pháp lý — chủ dự án tự xử lý)

### Bước 2 — Lập bản đồ khả năng, rồi LỌC
yfinance cho: giá lịch sử, thông tin công ty, BCTC, cổ tức/chia tách, giữ cổ phần, khuyến nghị phân tích, chuỗi quyền chọn, tin tức, sàng lọc, dữ liệu nhiều mã cùng lúc…

Với mỗi nhóm, trả lời đúng một câu: **dự án đã có chưa, và yfinance hơn/kém ở điểm nào?** Nhóm nào trùng thì loại thẳng, đừng mô tả dài.

### Bước 3 — Bốn câu hỏi ưu tiên (làm trước, đây là chỗ có giá trị nhất)

**a) 🔵 Yahoo có mã Việt Nam không, và chất lượng thế nào?**
Thử hậu tố `.VN` (ví dụ `VNM.VN`, `FPT.VN`, `HPG.VN`) và mã chỉ số VN nếu có.
Nếu có → **đối chiếu với BVSC** (dữ liệu BVSC ở `scratchpad/bvsc-deriv-2026-08-15/`, và gọi được `https://online.bvsc.com.vn/datafeed/instruments?symbols=<mã>`).
Đây **không phải để thay BVSC** — mà là **nguồn kiểm chứng chéo độc lập**, thứ dự án đang hoàn toàn không có. Đo: độ phủ, độ trễ, có giá điều chỉnh cổ tức không, khớp/lệch bao nhiêu.

**b) Lấp nốt chỗ trống hàng hoá:** đồng (`HG=F`), thép, than, quặng sắt, cao su. Dự án **chưa tìm được nguồn ngày miễn phí** cho nhóm này. yfinance có gì, và có mốc chuẩn nào để kiểm độ tin cậy không? Nếu không có mốc chuẩn thì **nói thẳng là không kiểm được**, đừng nhận bừa.

**c) Lợi suất TPCP Mỹ (`^TNX`, `^TYX`, `^FVX`) và VIX (`^VIX`):** FRED đã có, nhưng `VIXCLS` trên FRED **có bản quyền CBOE**. Yahoo có phải đường thoáng hơn không? Đối chiếu `^TNX` với FRED `DGS10` để đo chất lượng.

**d) Dữ liệu Yahoo KHÔNG có/kém:** nói rõ ranh giới. Đặc biệt: BCTC doanh nghiệp Việt Nam (FiinTrade đã có 729 mã chỉ tiêu — Yahoo gần như chắc chắn thua, xác nhận rồi loại).

### Bước 4 — Gọi thật
**Trần 60 lời gọi mạng.** Tuần tự, nghỉ ≥1 s. **Không dò ngưỡng chặn.**
⚠️ Cẩn thận: một lệnh `yf.download()` có thể bung nhiều HTTP request. **Đếm request thật**, đừng đếm số lệnh — đây đúng là bẫy akshare đã mắc (trần không kiểm soát được ở tầng gọi hàm).

Với mỗi thứ đáng lấy, đo: độ phủ lịch sử · độ trễ thật so với 2026-08-15 · lược đồ trả về · kiểu dữ liệu · giá trị thiếu biểu diễn thế nào · độ trễ mạng · **có bị chặn từ Việt Nam không**.

### Bước 5 — Kết luận, ba dạng, không lấp lửng
- **"Lấy, cho mục X"** — kèm số chứng minh
- **"Không lấy, vì trùng nguồn Y"** — nói rõ trùng chỗ nào
- **"Không lấy, vì rủi ro Z"** — kèm bằng chứng đo được

Kèm **ngân sách request/ngày** nếu lấy, và **đánh giá rủi ro vỡ** so với akshare (akshare hỏng im lặng, chết 1 năm mà vẫn trả HTTP 200 — yfinance có kiểu hỏng nào?).

## Luật viết
- **Chỉ ghi cái đo được.** Chưa gọi thật → "chưa kiểm". Suy đoán → gắn nhãn.
- Ngày đo 2026-08-15 cạnh mọi con số. Tiếng Việt. Không tô hồng, không quảng cáo hộ Yahoo.
- Python: luôn `PYTHONIOENCODING=utf-8` (Windows cp1252 sẽ crash).
- **Không đăng ký tài khoản, không tạo khoá API.**
- ⚠️ **Nếu dữ liệu có mốc thời gian, kiểm múi giờ trước khi so sánh.** Đợt này đã có một kết luận sai hoàn toàn vì parse UTC thay vì giờ địa phương. Ghi rõ múi giờ của mọi mốc thời gian.

## Đầu ra
1. Báo cáo: `C:\Users\tuanb\AppData\Local\Temp\claude\D--twan-projects-finext-v2\8bdadd16-750b-49f9-979c-7dea29fe37ac\scratchpad\report-yfinance.md`
2. Mẫu thô: `...\scratchpad\yfinance-raw\`

⚠️ **Harness có thể chặn ghi file `.md`.** Nếu vậy, ghi `.txt` **HOẶC** trả toàn văn báo cáo trong tin nhắn cuối — đừng bỏ mất nội dung.

**CẤM:** mọi lệnh git; sửa bất kỳ file nào trong `D:\twan-projects\finext-v2`. Chỉ đọc repo, ghi scratchpad. **KHÔNG dispatch subagent.**

Trả về ngắn gọn: trạng thái, số request THẬT đã dùng, kết quả 4 câu hỏi ưu tiên, danh sách chọn lọc "lấy gì / bỏ gì", khuyến nghị một dòng.
