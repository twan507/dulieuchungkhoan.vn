# Kiến trúc tổng thể dulieuchungkhoan.vn

**Ngày:** 2026-08-14 · **Trạng thái:** bản hợp nhất đầu tiên — nối ba khối tài liệu vốn được viết rời

Ba khối tài liệu của dự án được dựng trong ba phiên làm việc độc lập, mỗi khối tự đầy đủ. Tài liệu này không lặp lại chúng — nó chỉ trả lời một câu hỏi mà không khối nào tự trả lời được: **ba khối ghép vào nhau thành cái gì.**

---

## 1. Bốn tầng

```
┌─ L0 · NGUỒN NGOÀI ─────────────────────────────────────────────────┐
│  BVSC + FiinTrade        WiChart · SBV          8 báo điện tử      │
│  44 REST + 5 topic RT    87 REST + 1 crawl      47 RSS + 6 crawler │
│  phái sinh · ETF/quỹ     FRED · ECB · Yahoo                        │
│                          LBMA · Binance                            │
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
│  L4 · TRI THỨC — backend/agent/skills/                              │
│  vn-stock-advisor    (tư duy, văn phong — luôn có mặt)              │
│  vn-stock-knowledge  (công thức, quy trình — tải khi cần)           │
└───────┬─────────────────────────────────────────────────────────────┘
        │
   Chatbot · SSE realtime · REST · giao diện web
```

**L0 sau khảo sát 2026-08-15 — chín nguồn, không còn ba:**

| Khối | Nguồn | Đi vào nhánh nào của L1 | Tài liệu |
|---|---|---|---|
| Thị trường Việt Nam | **BVSC + FiinTrade** — cổ phiếu, chỉ số, **phái sinh 14 hợp đồng**, **ETF/quỹ 31 mã**, BCTC, realtime | ETL + Ingester | [`market/`](../10-sources/market/) |
| Vĩ mô Việt Nam | **WiChart** 87 key · **SBV** — OMO, crawl HTML *(mới 2026-08-15)* | ETL | [`macro/`](../10-sources/macro/) |
| Bối cảnh quốc tế *(khối mới 2026-08-15)* | **FRED** 15 series vĩ mô Mỹ · **Frankfurter (ECB)** 6 cặp tiền + DXY dựng lại · **Yahoo** 36 chỉ số/21 nước · **LBMA** vàng-bạc từ 1968 · **Binance** PAXG + 10 đồng crypto | ETL | [`global/`](../10-sources/global/) |
| Tin tức | **8 báo điện tử** — 47 RSS + 6 crawler | Gom tin · Lưới AI | [`news/`](../10-sources/news/) |

🔴 **Hai nguồn có ràng buộc thời gian mà thiết kế phải chịu, không thể vá về sau:**

1. **Nến 1 phút** — không tồn tại ở bất kỳ nguồn nào; không chạy Ingester ngày nào là mất ngày đó vĩnh viễn.
2. **OMO của SBV** — nguồn **chỉ hiển thị đúng phiên mới nhất, không có kho lưu** *(đo 2026-08-15)*. Cùng loại rủi ro với nến 1 phút, và cũng không backfill được. Chi tiết: [`macro/sbv-omo.md`](../10-sources/macro/sbv-omo.md).

**Đọc theo chiều dọc:** L0–L2 là *dữ kiện*, L3 là *cách hỏi dữ kiện*, L4 là *cách nghĩ về câu trả lời*. Một câu hỏi của người dùng đi ngược từ dưới lên: skill quyết định cần gì, function calling lấy dữ kiện, skill định hình câu trả lời.

**Đọc theo chiều ngang:** hai nhánh dữ liệu (thị trường và tin tức) độc lập tới tận L2, gặp nhau lần đầu ở L3 qua **mã cổ phiếu** — khoá nối duy nhất giữa hai nhánh.

## 2. Ranh giới tài liệu — luật một dòng

| Tầng thư mục | Chứa gì | Sửa được không |
|---|---|---|
| [`10-sources/`](../10-sources/) | Sự thật đo được về hệ thống của người khác | **Chỉ khi đo lại.** Sửa mà không đo là nói dối |
| [`20-design/`](../20-design/) | Lựa chọn của dulieuchungkhoan.vn | Được, nhưng lý do phải viết thẳng tại chỗ |
| [`30-skills/`](../30-skills/) | Corpus và tài liệu bảo trì hai skill chứng khoán | Corpus bất biến; tài liệu bảo trì cập nhật theo trạng thái thật |
| [`backend/agent/skills/`](../../backend/agent/skills/) | Sản phẩm chạy được | Được, nhưng phải test lại — xem quy trình 6 vòng và bộ test hồi quy ở [`30-skills/maintenance.md`](../30-skills/maintenance.md) |

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

🔴 **Một bẫy phải xử lý:** danh sách này **gồm cả mã đã huỷ niêm yết**. Phải lọc chéo với `getAllQuotes` của BVSC (**2.534** mã niêm yết, trong đó **1.974 cổ phiếu** — đo 2026-08-15) trước khi dùng làm từ điển gắn mã — nếu không, tin sẽ được gắn mã của doanh nghiệp đã rời sàn.

⚠️ Con số *"~1.600 mã"* trong tài liệu pipeline là **ước lượng chưa kiểm chứng**; số đo thật là **1.974** *(đếm `StockType=2` từ `getAllQuotes` của BVSC, đo 2026-08-15; ngày 2026-08-10 là 1.972)*. Dùng số 1.974 (đo 2026-08-15) — và lưu ý con số này **đổi theo tuần**, nên lọc động thay vì hardcode.

Hệ quả vận hành: bảng `organization` của [kho dữ liệu thị trường §5.1](../20-design/market-data-store.md) trở thành **phụ thuộc cứng của pipeline tin**. Pipeline tin không được tự nạp danh sách riêng — hai bản sao sẽ lệch nhau.

### 3.2 Cây ngành ICB → khung ngành cho skill

Hai skill **cố ý bỏ trống danh sách ngành**. Đây không phải thiếu sót mà là quyết định đã ghi rõ: *"không được cố định danh sách ngành, vì khung ngành chuẩn sẽ do hệ thống dữ liệu cung cấp sau"* — đã gỡ ở 9 chỗ. ⚠️ Có bốn chỗ nêu tên ngành **không được gỡ nhầm** (kế toán, định giá, hành vi) — liệt kê ở [`30-skills/README.md`](../30-skills/README.md).

Khung ngành đó chính là [`getAllIcbIndustry`](../10-sources/market/03-fiin-reference.md) — cây ICB **4 cấp**, có `icbCodePath` và `icbNamePath` nên lấy ngành cha ở cấp bất kỳ không cần duyệt cây.

Hợp đồng giữa hai bên:

| Bên | Cấp gì | Không được làm gì |
|---|---|---|
| Hệ dữ liệu | Cây ICB + `icbCode` của từng mã | Không phán một ngành thuộc bậc dẫn dắt / lan toả / phòng thủ |
| Skill | **Tiêu chí phân bậc** + phương pháp chấm 4 thành phần rủi ro | Không chốt cứng ngành nào ở bậc nào |

Việc xếp một ngành cụ thể vào bậc nào là **kết quả chạy lúc trả lời**, không phải hằng số trong tài liệu: lấy ngành từ ICB, chấm bốn thành phần rủi ro theo phương pháp ở [`portfolio-and-rotation.md`](../../backend/agent/skills/vn-stock-knowledge/references/portfolio-and-rotation.md), chia dải làm ba.

Nhờ vậy khung ngành đổi thì câu trả lời đổi theo, không phải sửa skill.

### 3.3 Function calling ↔ tầng skill

[Kho dữ liệu §6.3](../20-design/market-data-store.md) định nghĩa 5 function cho chatbot. [Skill L2](../../backend/agent/skills/vn-stock-knowledge/SKILL.md) viết: *"có công cụ tra dữ liệu thì gọi và dùng số hiện hành, không có thì nói rõ là cần tra"*.

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

Đầy đủ tới từng mã trường — lấy/bỏ, nguồn chuẩn, lý do tại chỗ: [chọn trường cho ETL thị trường](../20-design/market-field-selection.md).

## 4. Một lỗ hổng kiến trúc đã biết, chưa vá

Skill **không thể tự gác cổng phạm vi của chính nó.** Luật *"chỉ trả lời chứng khoán, tài chính, kinh tế"* nằm trong thân `SKILL.md` chỉ đọc được **sau khi skill đã tải** — mà câu ngoài phạm vi thì không kích hoạt skill nào, nên luật không bao giờ tới đúng lúc. Đo được ở vòng test 5: **3/4 câu ngoài phạm vi vẫn được trả lời đầy đủ**, kể cả viết trọn một đoạn code Python.

Cách vá duy nhất: dán đoạn giới hạn phạm vi vào **system prompt của sản phẩm**, không nhét thêm vào skill. Nguyên văn đoạn cần dán nằm ở [`maintenance.md` §5](../30-skills/maintenance.md).

**Đây là việc của tầng sản phẩm, không phải tầng skill.** Ghi ở đây để nó không rơi mất khi dựng backend.

## 5. Rủi ro pháp lý — không đồng đều giữa các nguồn

| Nguồn | Được thu thập, lưu, phái sinh | Ghi chú |
|---|---|---|
| BVSC + FiinTrade | ✅ Có | |
| WiChart (WiGroup) | ✅ Có | **Giấy phép WiFeed đã chốt — xác nhận 2026-08-15.** Trước đó chỉ truy cập được qua endpoint nội bộ phục vụ trang đối tác |
| SBV | ✅ Có | Cơ quan nhà nước công bố công khai, không xác thực, không giới hạn gói *(đo 2026-08-15)* |
| FRED | ✅ Có | **Chủ dự án đã làm việc với FRED và được đồng ý (2026-08-15)** |
| Frankfurter (ECB) | ✅ Có | API mở, mã nguồn mở, **tự dựng lại được bằng Docker**. Điều khoản quan sát 2026-08-15: không hạn mức tháng/ngày |
| Yahoo · LBMA · Binance | ⚠️ **Chưa quan sát trực tiếp** | Điều khoản của cả ba **chưa đọc** tính tới 2026-08-15. Riêng Yahoo là **API nội bộ không tài liệu, không cam kết, không phiên bản** — xem [`global/yahoo.md`](../10-sources/global/yahoo.md) |
| 8 báo điện tử | ⚠️ Có điều kiện | Xem mục bản quyền ở [pipeline tin §9.7](../20-design/news-pipeline.md) |

Hệ quả thiết kế vẫn giữ nguyên: **ETL WiChart phải tách được khỏi hệ thống mà không kéo đổ thứ gì khác.** Giấy phép đã chốt nên đây không còn là hàng rào pháp lý, nhưng WiChart vẫn là nhánh duy nhất sống nhờ một hợp đồng riêng với bên thứ ba — nếu quan hệ đó đổi, mất 87 endpoint vĩ mô/hàng hoá mà phần cổ phiếu vẫn chạy. Nguyên tắc *ETL độc lập theo miền* ở [kho dữ liệu §9.4](../20-design/market-data-store.md) đã lo việc này — giữ nó như lớp phòng thủ thứ hai, đừng gộp cho gọn.
