# Tầng ngữ nghĩa cho chatbot — hợp đồng giữa dữ liệu và tri thức

**Ngày:** 2026-08-14 · **Trạng thái:** 🟡 **đề xuất, chưa duyệt** — phần duy nhất trong kho tài liệu chưa qua kiểm chứng thực tế

Hai đầu của hợp đồng này đã tồn tại và đều đã được test riêng. Phần ở giữa thì chưa ai viết:

| Đầu | Đã có gì | Ở đâu |
|---|---|---|
| **Dữ liệu** | 5 function, từ điển chỉ tiêu, bộ view người-đọc-được | [kho dữ liệu §6](kho-du-lieu-thi-truong.md) |
| **Tri thức** | Kiến trúc phân tầng L1/L2, đã test 6 vòng | [`.claude/skills/`](../../.claude/skills/) |

Tài liệu này viết phần ở giữa. Nó **không lặp lại** §6 của kho dữ liệu — đọc file đó trước.

---

## 1. Luật phân định — ai quyết định gì

Hệ thống có bốn thứ có thể "quyết định" nội dung câu trả lời. Xếp nhầm thứ tự là nguồn lỗi lớn nhất.

| Thứ tự | Thành phần | Quyết định | Không được quyết định |
|---|---|---|---|
| 1 | **System prompt** | Có trả lời hay không (phạm vi lĩnh vực) | Trả lời cái gì |
| 2 | **Skill L1** `co-van-chung-khoan-vn` | **Hình dạng** câu trả lời: mạch lập luận, độ dài, kết luận có điều kiện, disclaimer | Con số, công thức |
| 3 | **Skill L2** `kien-thuc-chung-khoan-vn` | **Nội dung** chấm được đúng/sai: công thức, quy trình, định nghĩa | Nhận định thị trường, tỷ trọng |
| 4 | **Function calling** | **Dữ kiện thật**: giá, BCTC, chỉ tiêu, tin | Cách diễn giải dữ kiện |

Ba luật đã được test và phải giữ nguyên:

- **L2 cấp nội dung, L1 quyết định hình dạng** khi câu hỏi cần cả hai tầng.
- **L1 giữ bản mỏng ở mức *kết luận*, cấm ở mức *cơ chế*.** Câu trong L1 chứa công thức, số bước, hoặc ngưỡng số là sai chỗ. *(Khi quét kiểm, bắt cả cơ chế viết bằng chữ — "thứ hai", "ba bước" — quét chữ số thôi sẽ sót.)*
- **Skill phải đúng cả khi có function calling lẫn khi không có.** Function làm câu trả lời chính xác hơn, không được làm skill hỏng khi vắng nó.

## 2. Bộ function — mở rộng từ 5 lên 8

Năm function ở [§6.3](kho-du-lieu-thi-truong.md) chỉ phủ nhánh dữ liệu thị trường. Nhánh tin tức và khung ngành chưa có đường vào.

**Giữ nguyên 5 function đã định nghĩa:**

```
screen_stocks(criteria, exchange, sector, limit)
get_financials(ticker, statement_type, from_year, to_year)
get_price_series(ticker, from_date, to_date, resolution)
get_corporate_events(ticker, event_type, from_date)
compare_peers(ticker, metrics)
```

**Đề xuất thêm ba:**

```
get_news(ticker?, group?, sub?, from_date, to_date, limit)
    → nhánh tin. group/sub theo taxonomy 20 sub của pipeline tin.
      ticker rỗng = tin vĩ mô và quốc tế, không gắn mã.

get_industry_tree(icb_level?, ticker?)
    → cây ICB 4 cấp, hoặc ngành của một mã.
      Đây là "khung ngành do hệ thống dữ liệu cung cấp" mà skill đang chờ.

get_macro_series(indicator, from_date, to_date)
    → nhánh WiChart: vĩ mô, tiền tệ, giá hàng hoá.
      🔴 Chỉ bật sau khi chốt giấy phép WiFeed.
```

**Vì sao không cho sinh SQL tự do:** chính xác hơn, tránh quét toàn bảng, kiểm soát được chi phí. Lý do này đã ghi ở §6.3 và giữ nguyên hiệu lực cho cả ba function mới.

## 3. Ba quy tắc bắt buộc khi nối dữ liệu vào skill

### 3.1 Số thật đè số ví dụ, luôn luôn

Skill L2 chứa **số liệu 2022–2024 đã chết** — chúng là *tham số ví dụ để minh hoạ phép tính*, không phải dữ kiện. Luật này đã nằm trong `SKILL.md` và phải được tôn trọng ở tầng sản phẩm:

- Có function trả về số hiện hành → dùng số đó.
- Không có → **nói rõ là cần tra**, không suy số hiện tại từ ví dụ trong file.
- Không bao giờ trích số trong skill như thể nó là hiện tại.

### 3.2 Khung ngành lấy lúc chạy, không nhúng vào skill

Skill nêu **tiêu chí** phân bậc; `get_industry_tree` cấp **danh sách**. Xếp một ngành vào bậc nào là kết quả tính lúc trả lời, không phải hằng số. Chi tiết ở [kiến trúc tổng thể §3.2](../00-tong-quan/kien-truc-tong-the.md).

Nếu ai đó nhúng danh sách ngành vào skill "cho nhanh", họ đang đảo ngược một quyết định đã tốn 9 chỗ sửa và một vòng audit để thực hiện.

### 3.3 Mã cổ phiếu là khoá nối duy nhất giữa hai nhánh

Nhánh thị trường và nhánh tin gặp nhau ở `ticker`. Ba hệ quả:

- Bảng `organization` là **nguồn sự thật duy nhất** cho danh sách mã. Pipeline tin không tự nạp bản riêng.
- Tin có thể mang **nhiều mã**, và **mã rỗng là kết quả hợp lệ**. Câu trả lời của bot phải chịu được cả hai — ép phải có mã sẽ khiến AI bịa.
- Mã đã **huỷ niêm yết** vẫn nằm trong `getListOrganization`. Lọc chéo với `getAllQuotes` trước khi dùng.

## 4. Điều chưa biết

Ghi thẳng để không ai tưởng phần này đã chắc:

| Chưa biết | Vì sao quan trọng |
|---|---|
| **Skill có chịu được function calling không** — 6 vòng test đều chạy *không* có công cụ dữ liệu | Có thể xuất hiện lỗi mới: bot gọi function rồi bỏ qua mạch lập luận của L1, trả về bảng số trần |
| **Ai gọi function trước — skill hay bot** | Nếu bot gọi trước rồi mới tải skill, L1 mất quyền định hình câu trả lời |
| **Chi phí mỗi câu** | Chưa đo. L2 dày 2.273 dòng, tải cả vào context là tốn |
| ~~Đơn vị của các mã chỉ tiêu~~ | ✅ **Đã giải quyết 2026-08-14** — 727/729 mã (99,7%) có `don_vi_du_lieu`, trong đó **392 mã đã xác thực bằng bằng chứng số học** (đẳng thức kế toán + kiểm nhất quán thang trên 25 doanh nghiệp), 308 mức cao, 27 trung bình. Quan trọng hơn: phát hiện **nhãn `unit` của API không phải đơn vị dữ liệu** (`Percentage` thực ra là thập phân, `BillionVND` thực ra là VND). Chatbot phải đọc `don_vi_du_lieu`, không đọc `don_vi` |

**Việc kiểm chứng đầu tiên nên làm:** chạy lại đúng bộ test vòng 6 (10 câu tính toán trên số liệu thật, đã có đáp án đối chiếu) nhưng lần này cho phép gọi function. Nếu 10/10 vẫn đúng và câu trả lời vẫn giữ hình dạng của L1, hợp đồng này đứng vững. Bộ test nằm ở ghi chú xây dựng skill.
