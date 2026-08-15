# Brief — Khảo sát FRED làm nguồn VĨ MÔ QUỐC TẾ cho Finext

## Bối cảnh (đọc trước khi làm)

Repo: `D:\twan-projects\finext-v2` — nền tảng dữ liệu & phân tích chứng khoán Việt Nam.
Đọc để biết chỗ trống:

- `docs/10-sources/README.md` — bản đồ nguồn + mục "Ngoài phạm vi"
- `docs/10-sources/macro/wichart.md` — nguồn vĩ mô **trong nước** đã có (87 endpoint: 18 chỉ tiêu vĩ mô, 8 tiền tệ/lãi suất, 61 hàng hoá). Đọc cả cấu trúc tài liệu này — báo cáo của bạn nên cùng dòng họ.
- `.claude/skills/vn-stock-advisor/` — phương pháp top-down của sản phẩm. **Việc quan trọng: rút ra danh sách chỉ báo quốc tế mà skill THỰC SỰ dùng** (Fed funds, DXY, lợi suất TPCP Mỹ 10 năm, CPI Mỹ, bảng lương phi nông nghiệp…). Danh sách này là tiêu chí chọn series, đừng chọn theo cảm tính.

**Chỗ trống cần lấp:** vĩ mô quốc tế. Hiện `10-sources/README.md` liệt "Cổ phiếu và chỉ số quốc tế" là *Ngoài phạm vi* — khối này đang được mở rộng.

**Đây là khảo sát bước đầu**, không phải xây pipeline.

## Khoá API

File `.env` ở gốc repo có biến `FRED_API` (repo đã gitignore file này).
- Đọc bằng code (`python-dotenv` hoặc tự parse), **TUYỆT ĐỐI KHÔNG in giá trị khoá ra output, không viết khoá vào bất kỳ file báo cáo/log nào**. Nếu URL có chứa khoá, che thành `api_key=***` trước khi ghi.

## Nhiệm vụ

### Bước 1 — Nắm API
`https://fred.stlouisfed.org/docs/api/fred/` — St. Louis Fed. Nắm:
- Các nhóm endpoint (`series`, `series/observations`, `series/search`, `category`, `releases`, `tags`)
- Tham số chung, định dạng, phân trang, giới hạn kích thước
- **Rate limit chính thức** là bao nhiêu (tài liệu có nêu) — ghi lại con số tài liệu công bố
- Điều khoản sử dụng / giấy phép dữ liệu: FRED phân phối lại dữ liệu của bên thứ ba, **có series bị hạn chế phân phối lại**. Ghi rõ ranh giới này — dự án sẽ lưu và phục vụ lại cho khách hàng cuối. (Chủ dự án tự xử lý pháp lý; bạn chỉ cần ghi ĐÚNG điều khoản quan sát được, không đề xuất việc pháp lý.)

### Bước 2 — Chọn series theo nhu cầu thật
Từ danh sách chỉ báo rút ra ở Bước 1 (đọc skill), tìm mã series FRED tương ứng. Ví dụ định hướng (tự xác minh, đừng tin sẵn): `DFF`/`FEDFUNDS`, `DGS10`, `DGS2`, `CPIAUCSL`, `DTWEXBGS` (chỉ số USD), `T10Y2Y`, `UNRATE`, `VIXCLS`, giá dầu `DCOILWTICO`.
Kiểm thêm: FRED có dữ liệu **Việt Nam** không (nhóm series quốc tế/IMF/World Bank) — nếu có thì tần suất và độ trễ thế nào so với WiChart.

### Bước 3 — GỌI THẬT, đo thật
**Trần cứng: 60 lời gọi cho toàn bộ phiên.** Tuần tự. Không dò ngưỡng chặn — FRED công bố hạn mức rồi, chạy dưới mức đó là đủ.

Với mỗi series đại diện (~12–20 series), đo và ghi:
- Lược đồ response thật (JSON): các trường, kiểu, ý nghĩa
- Khoảng phủ (từ ngày nào), tần suất, **độ trễ công bố thật** (so ngày quan sát cuối với hôm nay 2026-08-15) — con số này quyết định dùng được cho phân tích realtime hay không
- Đơn vị và các biến thể `units` (`lin`, `chg`, `pch`, `pc1`…) — thử ít nhất một series với `units=pc1` để xác nhận hành vi
- Giá trị thiếu biểu diễn thế nào (FRED dùng dấu chấm `.`) — bẫy tích hợp, xác nhận bằng dữ liệu thật
- **Bản vá hồi tố (revision)**: FRED có `realtime_start`/`realtime_end` và ALFRED. Kiểm xem một chuỗi bị sửa lại số cũ ra sao — quan trọng vì kho dữ liệu phải quyết định lưu bản nào.
- Độ trễ mạng, kích thước

### Bước 4 — Kết luận có căn cứ
- Bảng series đề xuất lấy, kèm lý do gắn với phương pháp phân tích của skill
- Ngân sách request nếu pull định kỳ (bao nhiêu series × tần suất = bao nhiêu request/ngày)
- Rủi ro & ranh giới phân phối lại quan sát được

## Luật viết (quan trọng — repo này rất nghiêm)

- **Chỉ ghi cái ĐO ĐƯỢC.** Chưa gọi thật thì đánh dấu "chưa kiểm". Suy đoán gắn nhãn suy đoán.
- Ghi ngày đo (2026-08-15) cạnh mọi con số.
- Không tô hồng. Nếu FRED thiếu thứ dự án cần, nói thẳng.
- Tiếng Việt.

## Đầu ra — CHỈ GHI ĐÚNG 2 CHỖ, KHÔNG ĐỘNG VÀO GIT

1. **Báo cáo chính:** `C:\Users\tuanb\AppData\Local\Temp\claude\D--twan-projects-finext-v2\8bdadd16-750b-49f9-979c-7dea29fe37ac\scratchpad\report-fred.md`
2. **Log thô:** thư mục `...\scratchpad\fred-raw\` (đã che khoá API)

**CẤM TUYỆT ĐỐI:** `git add` / `git commit` / `git checkout` / tạo nhánh / sửa bất kỳ file nào trong `D:\twan-projects\finext-v2`. Có việc khác chạy song song trên repo; controller sẽ tự đưa kết quả vào. Bạn chỉ đọc repo, ghi ra scratchpad.

**KHÔNG dispatch subagent.** Tự làm.

Trả về ngắn gọn: trạng thái, số lời gọi đã dùng, 5 phát hiện quan trọng nhất, khuyến nghị. Chi tiết để trong file báo cáo.
