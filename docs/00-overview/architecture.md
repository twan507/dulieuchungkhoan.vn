# Kiến trúc tổng thể Finext

**Ngày:** 2026-08-14 · **Trạng thái:** bản hợp nhất đầu tiên — nối ba khối tài liệu vốn được viết rời

Ba khối tài liệu của dự án được dựng trong ba phiên làm việc độc lập, mỗi khối tự đầy đủ. Tài liệu này không lặp lại chúng — nó chỉ trả lời một câu hỏi mà không khối nào tự trả lời được: **ba khối ghép vào nhau thành cái gì.**

---

## 1. Bốn tầng

```
┌─ L0 · NGUỒN NGOÀI ─────────────────────────────────────────────────┐
│  BVSC + FiinTrade        WiChart (WiGroup)      10 báo điện tử     │
│  44 REST + 5 topic RT    87 REST                47 RSS + 6 crawler │
└───────┬────────────────────────┬─────────────────────┬─────────────┘
        │                        │                     │
┌───────▼────────────────────────▼─────────────────────▼─────────────┐
│  L1 · THU THẬP                                                      │
│  ETL Workers · Ingester (active+standby)   │  Gom tin · Lưới AI    │
│  → market-data-store.md                    │  → news-pipeline.md   │
└───────┬─────────────────────────────────────────────┬──────────────┘
        │                                             │
┌───────▼─────────────────────────────────────────────▼──────────────┐
│  L2 · KHO                                                           │
│  PostgreSQL + TimescaleDB + Redis                                   │
│  giá · BCTC · sự kiện · vĩ mô  │  tin toàn văn + tsvector + pgvector│
└───────┬─────────────────────────────────────────────┬──────────────┘
        │                                             │
┌───────▼─────────────────────────────────────────────▼──────────────┐
│  L3 · TẦNG NGỮ NGHĨA                                                │
│  view người-đọc-được · từ điển chỉ tiêu · function calling          │
│  → chatbot-semantic-layer.md                                        │
└───────┬─────────────────────────────────────────────────────────────┘
        │
┌───────▼─────────────────────────────────────────────────────────────┐
│  L4 · TRI THỨC — .claude/skills/                                     │
│  vn-stock-advisor    (tư duy, văn phong — luôn có mặt)              │
│  vn-stock-knowledge  (công thức, quy trình — tải khi cần)           │
└───────┬─────────────────────────────────────────────────────────────┘
        │
   Chatbot · SSE realtime · REST · giao diện web
```

**Đọc theo chiều dọc:** L0–L2 là *dữ kiện*, L3 là *cách hỏi dữ kiện*, L4 là *cách nghĩ về câu trả lời*. Một câu hỏi của người dùng đi ngược từ dưới lên: skill quyết định cần gì, function calling lấy dữ kiện, skill định hình câu trả lời.

**Đọc theo chiều ngang:** hai nhánh dữ liệu (thị trường và tin tức) độc lập tới tận L2, gặp nhau lần đầu ở L3 qua **mã cổ phiếu** — khoá nối duy nhất giữa hai nhánh.

## 2. Ranh giới tài liệu — luật một dòng

| Tầng thư mục | Chứa gì | Sửa được không |
|---|---|---|
| [`10-sources/`](../10-sources/) | Sự thật đo được về hệ thống của người khác | **Chỉ khi đo lại.** Sửa mà không đo là nói dối |
| [`20-design/`](../20-design/) | Lựa chọn của Finext | Được, nhưng ghi lý do vào [`decisions/`](decisions/) |
| [`30-skills/`](../30-skills/) | Nguyên liệu và nhật ký dựng skill | Corpus bất biến; ghi chú chỉ thêm, không xoá |
| [`.claude/skills/`](../../.claude/skills/) | Sản phẩm chạy được | Được, nhưng phải test lại — xem quy trình 6 vòng ở ghi chú |

## 3. Ba mắt xích nối ba khối

Đây là phần chưa từng được viết ở đâu. Mỗi mắt xích là **một câu hỏi để ngỏ ở khối này đã có sẵn đáp án ở khối khác**.

### 3.1 Danh sách mã niêm yết → gắn mã cho tin

[Pipeline tin §8](../20-design/news-pipeline.md) cần *"danh sách ~1.600 mã HOSE/HNX/UPCoM"* cho tầng 2, và *"bảng tên thương mại → mã"* cho tầng 3. Cả hai đang nằm ở mục **Còn để ngỏ**.

Đáp án đã có trong [`getListOrganization`](../10-sources/market/03-fiin-reference.md):

| Cần cho | Trường có sẵn |
|---|---|
| Tầng 2 — đối chiếu chuỗi 3 chữ in hoa | `ticker` |
| Tầng 3 — tên doanh nghiệp → mã | `organName` (tên đầy đủ tiếng Việt), `organShortName` |
| Lọc ngành khi hiển thị tin | `icbCode` — 100% bản ghi đều có |

🔴 **Một bẫy phải xử lý:** danh sách này **gồm cả mã đã huỷ niêm yết**. Phải lọc chéo với `getAllQuotes` của BVSC (2.530 mã niêm yết, trong đó **1.972 cổ phiếu**) trước khi dùng làm từ điển gắn mã — nếu không, tin sẽ được gắn mã của doanh nghiệp đã rời sàn.

⚠️ Con số *"~1.600 mã"* trong tài liệu pipeline là **ước lượng chưa kiểm chứng**; số đo thật là **1.972**. Dùng số 1.972.

Hệ quả vận hành: bảng `organization` của [kho dữ liệu thị trường §5.1](../20-design/market-data-store.md) trở thành **phụ thuộc cứng của pipeline tin**. Pipeline tin không được tự nạp danh sách riêng — hai bản sao sẽ lệch nhau.

### 3.2 Cây ngành ICB → khung ngành cho skill

Hai skill **cố ý bỏ trống danh sách ngành**. Đây không phải thiếu sót mà là quyết định đã ghi rõ: *"không được cố định danh sách ngành, vì khung ngành chuẩn sẽ do hệ thống dữ liệu cung cấp sau"* — đã gỡ ở 9 chỗ, xem [ADR 0003](decisions/0003-close-skill-project.md). ⚠️ Có bốn chỗ nêu tên ngành **không được gỡ nhầm** (kế toán, định giá, hành vi) — liệt kê ở [`30-skills/README.md`](../30-skills/README.md).

Khung ngành đó chính là [`getAllIcbIndustry`](../10-sources/market/03-fiin-reference.md) — cây ICB **4 cấp**, có `icbCodePath` và `icbNamePath` nên lấy ngành cha ở cấp bất kỳ không cần duyệt cây.

Hợp đồng giữa hai bên:

| Bên | Cấp gì | Không được làm gì |
|---|---|---|
| Hệ dữ liệu | Cây ICB + `icbCode` của từng mã | Không phán một ngành thuộc bậc dẫn dắt / lan toả / phòng thủ |
| Skill | **Tiêu chí phân bậc** + phương pháp chấm 4 thành phần rủi ro | Không chốt cứng ngành nào ở bậc nào |

Việc xếp một ngành cụ thể vào bậc nào là **kết quả chạy lúc trả lời**, không phải hằng số trong tài liệu: lấy ngành từ ICB, chấm bốn thành phần rủi ro theo phương pháp ở [`portfolio-and-rotation.md`](../../.claude/skills/vn-stock-knowledge/references/portfolio-and-rotation.md), chia dải làm ba.

Nhờ vậy khung ngành đổi thì câu trả lời đổi theo, không phải sửa skill.

### 3.3 Function calling ↔ tầng skill

[Kho dữ liệu §6.3](../20-design/market-data-store.md) định nghĩa 5 function cho chatbot. [Skill L2](../../.claude/skills/vn-stock-knowledge/SKILL.md) viết: *"có công cụ tra dữ liệu thì gọi và dùng số hiện hành, không có thì nói rõ là cần tra"*.

Hai câu này nói về **cùng một thứ, từ hai phía** — và chưa bên nào biết bên kia tồn tại. Chi tiết hợp đồng ở [tầng ngữ nghĩa cho chatbot](../20-design/chatbot-semantic-layer.md).

Điều quan trọng nhất cần giữ: **skill viết sao cho đúng cả khi có công cụ tra dữ liệu lẫn khi không có** — nguyên tắc đã chốt ở vòng audit 2. Function calling làm câu trả lời chính xác hơn, không được làm skill hỏng khi vắng nó.

## 3.4 Nguyên tắc chọn nguồn khi nhiều nguồn cùng có

Ba nguồn thị trường chồng lấn nhau nhiều: Screener 193 trường *(tài liệu ghi 223)*, Snapshot 54, BVSC 62 — phần lớn nói cùng một chuyện. Luật đã chốt:

**Mỗi chỉ tiêu có đúng một nguồn chuẩn.** Chọn theo hai tiêu chí, xét theo thứ tự: *(1)* nguồn nào realtime và khớp sàn — ưu tiên tuyệt đối cho giá và mọi thứ dẫn xuất từ giá; *(2)* nguồn nào cho trọn bộ ngữ cảnh — trùng lặp không đủ là lý do để bỏ.

> **Nhóm chỉ tiêu dẫn xuất lẫn nhau thì lấy trọn bộ từ một nguồn.** Biến TTM sinh ra tỷ số, giá sinh ra chỉ báo. Trộn nguồn giữa chừng tạo ra dữ liệu **tự mâu thuẫn trong cùng một bảng** — chatbot lấy vốn hoá chia lợi nhuận sẽ ra P/E khác cột P/E ngay bên cạnh, mà không có gì báo sai.

| Nhóm | Nguồn chuẩn | Quy mô |
|---|---|---|
| Giá, KL, sổ lệnh, khối ngoại, thoả thuận, chỉ báo kỹ thuật | **BVSC** | ~40 trường, realtime |
| Tỷ số tài chính, Beta, sở hữu tổ chức, TTM | **Screener** | 80/193 |
| Hồ sơ DN, sở hữu chi tiết | **Snapshot** | 16/54 |
| Mọi mã `bs*` `is*` `cf*` `no*` | **BCTC đầy đủ** | 556 |
| Tự doanh, đóng góp chỉ số, chuỗi khối ngoại | **MoneyFlow** | BVSC không có |

Đầy đủ: [ADR 0002](decisions/0002-data-source-selection.md).

## 4. Một lỗ hổng kiến trúc đã biết, chưa vá

Skill **không thể tự gác cổng phạm vi của chính nó.** Luật *"chỉ trả lời chứng khoán, tài chính, kinh tế"* nằm trong thân `SKILL.md` chỉ đọc được **sau khi skill đã tải** — mà câu ngoài phạm vi thì không kích hoạt skill nào, nên luật không bao giờ tới đúng lúc. Đo được ở vòng test 5: **3/4 câu ngoài phạm vi vẫn được trả lời đầy đủ**, kể cả viết trọn một đoạn code Python.

Cách vá duy nhất: dán đoạn giới hạn phạm vi vào **system prompt của sản phẩm**, không nhét thêm vào skill. Nguyên văn đoạn cần dán nằm ở [`maintenance.md` §5](../30-skills/maintenance.md).

**Đây là việc của tầng sản phẩm, không phải tầng skill.** Ghi ở đây để nó không rơi mất khi dựng backend.

## 5. Rủi ro pháp lý — không đồng đều giữa các nguồn

| Nguồn | Được thu thập, lưu, phái sinh | Ghi chú |
|---|---|---|
| BVSC + FiinTrade | ✅ Có | |
| WiChart (WiGroup) | 🔴 **Chưa** | Đang truy cập qua endpoint nội bộ phục vụ trang đối tác. **Phải chốt giấy phép WiFeed trước khi thương mại hoá** |
| 10 báo điện tử | ⚠️ Có điều kiện | Xem mục bản quyền ở [pipeline tin §9.7](../20-design/news-pipeline.md) |

Hệ quả thiết kế: **ETL WiChart phải tách được khỏi hệ thống mà không kéo đổ thứ gì khác.** Nếu giấy phép không chốt được, mất 87 endpoint vĩ mô/hàng hoá nhưng phần cổ phiếu vẫn chạy. Nguyên tắc *ETL độc lập theo miền* ở [kho dữ liệu §9.4](../20-design/market-data-store.md) đã lo việc này — giữ nó, đừng gộp cho gọn.
