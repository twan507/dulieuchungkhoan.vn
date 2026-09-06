# Tầng ngữ nghĩa cho chatbot — hợp đồng giữa dữ liệu và tri thức

**Ngày:** 2026-08-14 · **Trạng thái:** ✅ **đã dựng và kiểm chứng thực tế 2026-09-07** — xem hồ sơ [`90-records/plans/2026-09-07-semantic-layer/`](../90-records/plans/2026-09-07-semantic-layer/)

Hai đầu của hợp đồng này đã tồn tại và đều đã được test riêng. Phần ở giữa thì chưa ai viết:

| Đầu | Đã có gì | Ở đâu |
|---|---|---|
| **Dữ liệu** | 9 function, từ điển chỉ tiêu, bộ view người-đọc-được | [kho dữ liệu §6](market-data-store.md) |
| **Tri thức** | Kiến trúc phân tầng L1/L2, đã test 6 vòng | [`backend/agent/skills/`](../../backend/agent/skills/) |

Tài liệu này viết phần ở giữa. Nó **không lặp lại** §6 của kho dữ liệu — đọc file đó trước.

---

## 1. Luật phân định — ai quyết định gì

Hệ thống có bốn thứ có thể "quyết định" nội dung câu trả lời. Xếp nhầm thứ tự là nguồn lỗi lớn nhất.

| Thứ tự | Thành phần | Quyết định | Không được quyết định |
|---|---|---|---|
| 1 | **System prompt** | Có trả lời hay không (phạm vi lĩnh vực) | Trả lời cái gì |
| 2 | **Skill L1** `vn-stock-advisor` | **Hình dạng** câu trả lời: mạch lập luận, độ dài, kết luận có điều kiện, disclaimer | Con số, công thức |
| 3 | **Skill L2** `vn-stock-knowledge` | **Nội dung** chấm được đúng/sai: công thức, quy trình, định nghĩa | Nhận định thị trường, tỷ trọng |
| 4 | **Function calling** | **Dữ kiện thật**: giá, BCTC, chỉ tiêu, tin | Cách diễn giải dữ kiện |

Ba luật đã được test và phải giữ nguyên:

- **L2 cấp nội dung, L1 quyết định hình dạng** khi câu hỏi cần cả hai tầng.
- **L1 giữ bản mỏng ở mức *kết luận*, cấm ở mức *cơ chế*.** Câu trong L1 chứa công thức, số bước, hoặc ngưỡng số là sai chỗ. *(Khi quét kiểm, bắt cả cơ chế viết bằng chữ — "thứ hai", "ba bước" — quét chữ số thôi sẽ sót.)*
- **Skill phải đúng cả khi có function calling lẫn khi không có.** Function làm câu trả lời chính xác hơn, không được làm skill hỏng khi vắng nó.

## 2. Bộ 9 function — hợp đồng thật, dựng và kiểm chứng 2026-09-07

Chữ ký chép nguyên văn từ [`backend/agent/tools/__init__.py`](../../backend/agent/tools/__init__.py) — đây là **nguồn sự thật duy nhất**, không phải bản diễn giải. Mọi tham số tuỳ chọn có giá trị mặc định (bẫy MiniMax đã đo — §5 dưới); mọi tool trả `str` (JSON tiếng Việt không dấu).

```
get_price_series(ticker, from_date=None, to_date=None, adjusted=True)
get_financials(ticker, statement_type="IS", from_year=None, to_year=None,
                period="nam", metric_codes=[])
screen_stocks(criteria=[], industry_code=None, exchange=None, sort_by=None, limit=None)
compare_peers(tickers=[], metric_codes=[], industry_code=None)
get_corporate_events(ticker, event_type=None, from_date=None, to_date=None, limit=None)
get_industry_tree(industry_code=None, ticker=None)
get_macro_series(code=None, keyword=None, from_date=None, to_date=None, limit=None)
get_news(query=None, ticker=None, group_no=None, sub=None, industry_code=None,
          from_date=None, to_date=None, limit=None)
load_knowledge_reference(topic)   # Literal đóng 9 giá trị — đường vào L2
```

🔴 **`get_industry_tree` KHÔNG có tham số `icb_level`.** Bản đề xuất ban đầu ở đây từng có — đã bỏ khi dựng thật. Hàm chỉ trả **cây 24 ngành riêng của dự án** (6 nhóm × 24 ngành, xem [industry-tree.md](industry-tree.md)) hoặc ngành của một mã cụ thể qua view `market.v_issuer_industry`; cây ICB **không bao giờ** ra tới model, kể cả gián tiếp — mọi tham chiếu ICB trong đề xuất cũ (`get_industry_tree(icb_level?, ...)`, "cây ICB 4 cấp") đã sai và đã được sửa khi dựng.

`load_knowledge_reference` là function thứ 9, không nằm trong đề xuất ban đầu — đường duy nhất tới L2, `topic` tra `dict` hằng → `Path`, không nối chuỗi từ đầu vào nên không có đường path traversal.

**Vì sao không cho sinh SQL tự do:** chính xác hơn, tránh quét toàn bảng, kiểm soát được chi phí. Lý do này đã ghi ở [§6.3 kho dữ liệu](market-data-store.md) và giữ nguyên hiệu lực cho cả 9 function.

## 3. Ba quy tắc bắt buộc khi nối dữ liệu vào skill

### 3.1 Số thật đè số ví dụ, luôn luôn

Skill L2 chứa **số liệu 2022–2024 đã chết** — chúng là *tham số ví dụ để minh hoạ phép tính*, không phải dữ kiện. Luật này đã nằm trong `SKILL.md` và phải được tôn trọng ở tầng sản phẩm:

- Có function trả về số hiện hành → dùng số đó.
- Không có → **nói rõ là cần tra**, không suy số hiện tại từ ví dụ trong file.
- Không bao giờ trích số trong skill như thể nó là hiện tại.

### 3.2 Khung ngành lấy lúc chạy, không nhúng vào skill

Skill nêu **tiêu chí** phân bậc; `get_industry_tree` cấp **danh sách**. Xếp một ngành vào bậc nào là kết quả tính lúc trả lời, không phải hằng số. Chi tiết ở [kiến trúc tổng thể §3.2](../00-overview/architecture.md).

Nếu ai đó nhúng danh sách ngành vào skill "cho nhanh", họ đang đảo ngược một quyết định đã tốn 9 chỗ sửa và một vòng audit để thực hiện.

### 3.3 Mã cổ phiếu là khoá nối duy nhất giữa hai nhánh

Nhánh thị trường và nhánh tin gặp nhau ở `ticker`. Ba hệ quả:

- **`market.issuer` + `market.security`** (spec schema 2026-08-25 — trước là bảng `organization`) là nguồn sự thật duy nhất cho danh bạ. Pipeline tin không tự nạp bản riêng.
- Tin có thể mang **nhiều mã**, và **mã rỗng là kết quả hợp lệ**. Câu trả lời của bot phải chịu được cả hai — ép phải có mã sẽ khiến AI bịa.
- Mã đã **huỷ niêm yết** vẫn nằm trong `getListOrganization`. Lọc chéo với `getAllQuotes` trước khi dùng.

## 4. Điều chưa biết

Ghi thẳng để không ai tưởng phần này đã chắc:

| Chưa biết | Vì sao quan trọng |
|---|---|
| ~~**Skill có chịu được function calling không**~~ | ✅ **Đóng 2026-09-07** — bộ hồi quy vòng 7 (15 câu, **có** function calling): **lớp 1 (số) 15/15 đúng**; **lớp 2 (hình dạng L1) 12/15 đạt** (ngưỡng AC7 là ≥ 14/15 — **không đạt**). Ba câu trượt hình dạng, cùng hai kiểu hỏng: A3 (WACC) và A4b (Gordon) rơi vào lối trình bày công thức LaTeX + heading "Bước 1/2/3" như tờ công thức, mất mạch lập luận; B5 (cổ tức FPT) chỉ liệt kê sự kiện rồi dừng, không diễn giải. Function calling **không** làm hỏng độ chính xác, nhưng L1 mất quyền định hình đúng ở những câu khó nhất |
| ~~**Ai gọi function trước — skill hay bot**~~ | ✅ **Đóng bằng thiết kế** — L1 nằm nguyên trong block `system` (`build_system_blocks()`), gửi kèm **mọi** request kể cả các vòng sau khi có `tool_result`; L1 luôn đứng trước, không bao giờ đến sau. Không có tình huống "bot gọi function trước khi tải skill" trong kiến trúc này |
| ~~**Chi phí mỗi câu**~~ | ✅ **Đo thật 2026-09-07** — đọc từ `ops.llm_call`: **≈ $0,016/câu** (22 câu, quy giá pay-go), độ trễ **p50 6,9 s · p90 34,5 s · max 41,8 s**, **≈ 2,1 request/câu**. Thấp hơn ước lượng $0,022–0,048 của spec vì cache MiniMax trúng tốt các lượt gọi function *trong cùng một câu* — chi tiết ở §5 dưới |
| ~~Đơn vị của các mã chỉ tiêu~~ | ✅ **Đã giải quyết 2026-08-14** — 727/729 mã (99,7%) có `don_vi_du_lieu`, trong đó **392 mã đã xác thực bằng bằng chứng số học** (đẳng thức kế toán + kiểm nhất quán thang trên 25 doanh nghiệp), 308 mức cao, 27 trung bình. Quan trọng hơn: phát hiện **nhãn `unit` của API không phải đơn vị dữ liệu** (`Percentage` thực ra là thập phân, `BillionVND` thực ra là VND). Chatbot phải đọc `don_vi_du_lieu`, không đọc `don_vi` |

**Việc kiểm chứng đã chạy — 2026-09-07.** Bộ vòng 6 (10 câu) nhắc ở trên **đã mất khỏi repo trước khi chạy được** — không tái lập được. Lát 10 dựng bộ thay thế gọi là **vòng 7** (15 câu, có function calling) và lưu vào repo: [`regression-round7.md`](../90-records/plans/2026-09-07-semantic-layer/regression-round7.md) · kết quả đầy đủ [`round7-results-2026-09-07.md`](../90-records/plans/2026-09-07-semantic-layer/round7-results-2026-09-07.md). Bộ test hồi quy cũ ở [`30-skills/maintenance.md`](../30-skills/maintenance.md) §6 nay ghi rõ đây là bộ thay thế.

## 5. Ba bẫy đã trả giá khi dựng — 2026-09-07

Đo thật lúc chạy bộ hồi quy vòng 7. Cả ba đều **hỏng im lặng**: không exception, không cờ lỗi — đúng họ bẫy CLAUDE.md §3.4 đã ghi. Ghi ra để người sau không lặp lại.

1. **`max_tokens` quá nhỏ cắt câu trả lời thành rỗng im lặng.** Đặt `max_tokens=4000`: 3/40 request có `stop_reason=max_tokens`, một request tiêu **3.999 token chỉ cho phần thinking** rồi hết chỗ cho chữ ⇒ ba câu (A2, A4, B9) trả về **rỗng**. Sửa: nâng lên `8000`; vòng chat không bao giờ được trả rỗng im lặng mà phải nói rõ model dừng vì lý do gì.
2. **Model từ chối tra dữ liệu vì tưởng mốc thời gian nằm ngoài tri thức của nó.** Hỏi CPI tháng 8/2026 — model trả lời *"mốc cập nhật gần nhất của tôi là tháng 1/2026"* và **không gọi function nào**, trong khi kho có sẵn đúng số 4,45%. Sửa: thêm block `system` thứ ba neo ngày hôm nay, kèm yêu cầu bắt buộc gọi công cụ trước khi nói "không có dữ liệu".
3. **Cache MiniMax trúng trong cùng cuộc hội thoại nhưng không trúng giữa hai câu hỏi khác nhau.** Lượt gọi function thứ hai của cùng một câu: vào 409 token, đọc cache 36.886 — trúng gần như tuyệt đối. Nhưng **mọi request đầu của một câu mới** đều `cache_read = 128` (mức nền), dù tiền tố `system + tools` giống hệt câu trước và cách nhau vài giây. ⇒ ngân sách chi phí phải tính **mỗi câu mới trả đủ ~36,7k token "lạnh"**, phần cache chỉ cứu được các lượt gọi function tiếp theo trong cùng câu đó — không cứu được giữa các câu.
