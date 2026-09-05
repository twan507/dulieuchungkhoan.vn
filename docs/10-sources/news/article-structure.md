# Cấu trúc trang bài và luật bỏ boilerplate — 8 nguồn tin

**Loại tài liệu:** tra cứu (reference) · **Ngày đo: 2026-08-15 · mẫu: 4 bài / nguồn** (riêng CafeF thêm 1 trang CBTT) · **Trạng thái** đã kiểm chứng trên mẫu · **đã cài đặt lát 8 (2026-09-06)**

Tài liệu này trả lời việc **từng** để ngỏ ở [thiết kế pipeline tin tức](../../20-design/news-pipeline.md) mục 12 và mục 6.5 tầng 2 của [danh mục nguồn tin](README.md) — nguyên văn khi đó: *"luật bỏ boilerplate phải viết riêng cho từng nguồn — chưa khảo sát cấu trúc trang bài"*. Cả hai chỗ nay đã đánh dấu ✅ và trỏ ngược về tài liệu này. Đặc tính feed, encoding và khối lượng cũng nằm ở [danh mục nguồn tin](README.md).

Mọi luật dưới đây **đã được chạy thật** trên chính các trang đã tải về; dòng *Đã kiểm* của từng nguồn ghi phần trăm ký tự mà luật loại khỏi container chính, đo trên từng bài.

**Cách đọc bảng — hai mức bằng chứng, không trộn lẫn:**

| Dòng | Nghĩa |
|---|---|
| **Bỏ — đã quan sát** | Selector **có khớp node thật bên trong container chính**. Số trong ngoặc là tổng số node khớp trên toàn bộ mẫu của nguồn đó |
| **Bỏ — phòng thủ** | Selector **không khớp node nào bên trong container chính** trên mẫu. Mỗi hàng nói rõ thêm nó thuộc loại nào trong hai loại: **tồn tại nhưng nằm ngoài container** (tầng 0 đã lo, giữ để đề phòng CMS đổi vị trí) hay **không xuất hiện ở đâu trên trang** (thuần suy đoán từ nguồn cùng CMS) |

**21 trong 61 selector là loại phòng thủ.** Chúng được ghi riêng để người triển khai biết chỗ nào đo được và chỗ nào là suy luận — cần bộ luật tối giản thì dùng đúng phần *đã quan sát*. Mọi con số ở dòng *Đã kiểm* đều sinh ra từ bộ luật đầy đủ, nhưng vì phần phòng thủ không khớp node nào trong container nên bỏ chúng đi kết quả **không đổi một ký tự**.

---

## 1. Phạm vi và phương pháp

### 1.1 Số nguồn: 8, không phải 10

Tài liệu hiện có ghi *"10 nguồn báo"*. Đếm lại theo host thật trong [`feeds.json`](feeds.json) và [README](README.md) mục 4–5 thì chỉ có **8 host phân biệt**:

| Host | Feed RSS | Crawler HTML |
|---|---:|---:|
| vietstock.vn | 20 | — |
| vneconomy.vn | 9 | — |
| vietnambiz.vn | 5 | — |
| bnews.vn | 4 | — |
| nguoiquansat.vn | 4 | — |
| cafef.vn | 3 | 1 — CBTT `du-lieu/tin-doanh-nghiep.chn` |
| baochinhphu.vn | 2 | 1 — `chi-dao-dieu-hanh.htm` |
| tinnhanhchungkhoan.vn | 0 | 4 — sitemap tháng + 3 trang chuyên mục |
| **Cộng** | **47** | **6** |

Con số 10 nhiều khả năng là số đếm trước khi loại VietnamFinance, Stockbiz, fili.vn và chinhphu.vn ([README](README.md) mục 11.1). **Khảo sát này phủ đủ 8/8 host** — không nguồn nào bị bỏ sót, cũng không có nguồn thứ 9, 10 để khảo sát.

### 1.2 Cách lấy mẫu

| | |
|---|---|
| Ngày đo | 15/08/2026 |
| URL bài lấy từ | RSS mục "chứng khoán" của 7 nguồn có feed · sitemap tháng 8 cho TinnhanhCK · trang CBTT cho CafeF |
| Số trang bài đã tải | **33** (4/nguồn + 1 trang CBTT CafeF) |
| Tổng lượt HTTP | **42** (9 feed/index + 33 bài) |
| Cách gọi | tuần tự, giãn 1,5 giây, User-Agent khai thật `FinextNewsSurvey/0.1` |
| Mã trả về | **200 cả 42 lượt** — không nguồn nào trả 403/429 |

HTML thô được giữ ngoài repo (thư mục tạm), **không commit**.

### 1.3 Ba tầng làm sạch, không phải hai

[Danh mục nguồn tin](README.md) mục 6.5 vốn mô tả hai tầng (bỏ thẻ · bỏ khối phi nội dung) — [thiết kế](../../20-design/news-pipeline.md) chỉ tham chiếu tới đó chứ không chứa mục này. Đo thực tế cho thấy phải chèn thêm một tầng trước cả hai — mục 6.5 đã cập nhật theo:

| Tầng | Việc | Vì sao |
|---|---|---|
| **0** | Cắt đúng **container chính** rồi mới xử lý | Không cắt thì "bỏ thẻ" sẽ nuốt cả header, footer, box tin liên quan của toàn trang. Trang thô nặng 94–527 KB, thân bài chỉ 155–6.671 ký tự |
| 1 | Decode entity → bỏ thẻ → **bỏ HTML comment** | Xem mục 3.1 |
| 2 | Bỏ khối phi nội dung theo selector riêng từng nguồn | Bảng ở mục 2 |

---

## 2. Luật từng nguồn

Trong dòng *Đã kiểm*, phần trăm là tỷ lệ ký tự mà tầng 2 loại khỏi container chính, liệt kê theo từng bài mẫu; *sạch* là số ký tự text còn lại. Hai mức bằng chứng của dòng *Bỏ* đọc theo bảng ở đầu tài liệu.

### 2.1 CafeF — bài thường

| | |
|---|---|
| **Container chính** | `div.detail-content.afcbc-body` |
| **Bỏ — đã quan sát** | `div.chisochungkhoan` (1 — ô giá cổ phiếu, chỉ có ở bài gắn mã) · `div.tindnd` (4) + `#listNewsInContent` (4 — khối "TIN MỚI") · `div.c-banner` (8), `div.h-show-pc` (4), `div.h-show-mobile` (4) — quảng cáo, rỗng text nhưng cắt câu · `figure` (5), `figcaption` (9 — chú thích ảnh) |
| **Bỏ — phòng thủ** | **0 node trong container trên cả 4 mẫu.** `#reactRelate` (có 1/trang) và `div.VCSortableInPreviewMode` (có 1/trang ở 3/4 mẫu) tồn tại thật nhưng **nằm ngoài** container — giữ để đề phòng CMS đổi vị trí. `div.admzone` và `table` thì **không xuất hiện ở đâu trên trang** — thuần suy đoán |
| **Tiêu đề** | `h1.title[itemprop=headline]` |
| **Sapo** | `p.sapo[itemprop=description]` — **nằm ngoài** container chính |
| **Thời gian** | `span.pdate` — dạng `15-08-2026 - 01:01 AM` |
| **Tác giả** | `span.author` |
| **Bẫy riêng** | ① `div.w640.fr.clear` là **tổ tiên** của container chính, không phải anh em: sapo (`p.sapo`) và khối *"Theo Nhịp sống thị trường · Copy link · Link bài gốc"* nằm cùng trong `w640` nhưng ngoài `div.detail-content`. Kiểm trên 4/4 mẫu. Hệ quả: chọn `w640` làm container là dính cả sapo lẫn chân bài; chọn `div.detail-content` thì sạch. ② Ô `div.chisochungkhoan` chèn chuỗi *"VIC: Giá hiện tại Thay đổi Xem hồ sơ doanh nghiệp"* ngay đầu thân bài — chỉ xuất hiện ở bài có gắn mã (1/4 mẫu). ③ **Bẫy đo 2026-09-05:** `span.pdate` trả `05-09-2026 - 17:09 PM` — giờ đã ở dạng 24h nhưng vẫn dán nhãn `AM`/`PM`; parse phải dùng `%H` và bỏ qua `%p`, dùng `%I` sẽ vỡ |
| **Đã kiểm** | 4/4 bài — bỏ 1,3% / 3,9% / 4,6% / 6,0%; sạch 1.768–3.535 ký tự; đầu và cuối text đều là câu thật. Kiểm lại 05/09/2026: container + tiêu đề còn đúng, text sạch 2.975 ký tự |

### 2.2 CafeF — trang công bố thông tin (CBTT)

**Template hoàn toàn khác bài thường.** Không dùng chung luật được.

| | |
|---|---|
| **Container chính** | `div#newscontent` |
| **Bỏ — đã quan sát** | `div.FileWrapper` (1 — tên file PDF đính kèm) |
| **Bỏ — phòng thủ** | `table` — 0 node trong container, nhưng **tồn tại ngoài container** (23 node/trang: trang CBTT dựng bằng bảng lồng bảng kiểu WebForms) |
| **Tiêu đề** | `td.text_noibat_cacbaikhac span.cms_blue` |
| **Sapo / tác giả** | không có |
| **Bẫy riêng** | ① `<h1>` trên trang này là **tên doanh nghiệp**, không phải tiêu đề tin — lấy `h1` sẽ ra *"Công ty cổ phần Đầu tư Y Tế - Dược phẩm Việt Nam (HOSE)"*. ② Toàn trang bọc trong `<form id="form1">` (ASP.NET WebForms) — bộ bóc nào xoá thẻ `form` sẽ mất sạch nội dung. ③ Nội dung thật nằm trong file PDF; text còn lại chỉ 155 ký tự |
| **Đã kiểm** | 1/1 trang — 209 → 155 ký tự (bỏ 25,8%), text sạch: *"…thông báo Giấy chứng nhận đăng ký doanh nghiệp thay đổi lần thứ 25 như sau: Các tập tin đính kèm Theo HOSE"*. Kiểm lại 05/09/2026: container + tiêu đề còn đúng, text sạch 680 ký tự |

> Xác nhận đúng dự đoán ở [thiết kế](../../20-design/news-pipeline.md) mục 7.1b: CBTT bóc ra **gần rỗng là hợp lệ**, không phải lỗi bộ bóc. Phải đặt `classified_from: "title_only"` cho nhánh này chứ đừng báo động.

### 2.3 Vietstock

| | |
|---|---|
| **Container chính** | `div#vst_detail[itemprop=articleBody]` |
| **Bỏ — đã quan sát** | `p.pTitle` (4 — lặp tiêu đề) · `p.pHead` (4 — lặp sapo) · `p.pAuthor` (4), `p.pSource` (4), `p.pPublishTimeSource` (4) — chữ ký *"Huy Khải · FILI · - 18:25 14/08/2026"* · `table.img-content` (9 — bảng bọc biểu đồ, chỉ chứa caption + iframe) |
| **Bỏ — phòng thủ** | `div.article-sharing` — 0 node trong container, nhưng **tồn tại ngoài container** (2/trang × 4, nút chia sẻ, rỗng text) |
| **Tiêu đề** | `h1.article-title` |
| **Sapo** | `p.pHead` — nằm **trong** thân bài, phải bỏ khỏi `content` |
| **Thời gian** | `p.pPublishTimeSource` (`- 19:30 05/09/2026`) — `div.meta span.date` chỉ có giờ tương đối `2 giờ trước` và nằm ngoài container *(đo 2026-09-05; bản 15/08 ghi `span.date`)* |
| **Tác giả** | `p.pAuthor` |
| **Bẫy riêng** | ① **Cuộn vô hạn — bẫy chọn container, không phải bẫy bỏ boilerplate.** Mỗi trang có đúng **1 khối** `div.row.scroll-content-sub` chứa **10 link bài khác** cùng chuyên mục, dài 2.354–2.670 ký tự (4/4 mẫu). Khối này **nằm ngoài** `div#vst_detail` — chọn đúng container là nó không bao giờ lọt vào, nên selector này **không có mặt trong danh sách bỏ**. Nhưng chọn container rộng hơn (`div.article-content`, `section#page-content`) là mỗi bản ghi phình thêm ~2,5 K ký tự của bài khác. ② Trang nặng nhất bộ (376–527 KB) do nhúng nhiều iframe biểu đồ. ③ Có modal *"chính sách bảo mật thông tin"* (`div.information-security-policy__modal-text`) chứa ~1.250 ký tự `<p>` — heuristic *"lấy thẻ có nhiều `<p>` nhất"* sẽ chọn nhầm chính cái modal này |
| **Đã kiểm** | 4/4 bài — bỏ 10,8% / 13,1% / 26,9% / **40,1%**; sạch 672–4.540 ký tự. Tỷ lệ 40,1% ở bài ngắn là do tiêu đề + sapo + chữ ký chiếm phần lớn. Kiểm lại 05/09/2026: container + tiêu đề còn đúng, text sạch 1.275 ký tự |

### 2.4 VnEconomy

| | |
|---|---|
| **Container chính** | `main#article-editor.article-editor` |
| **Bỏ — đã quan sát** | `h4.article-content__lead` (4 — lặp sapo, 130–244 ký tự/bài) · `figure` (7), `figcaption` (5) |
| **Bỏ — phòng thủ** | `div.container-adv`, `section`, `div.article-tags`, `table` — **0 node trong container trên cả 4 mẫu.** `div.container-adv` (13/trang ở 3 mẫu, 0 ở mẫu thứ tư) và `section` (5/trang) có thật trên trang nhưng đều nằm ngoài `main#article-editor`; `div.article-tags` và `table` **không xuất hiện ở đâu** — khối tag thật là `div.tags` (1/trang, cũng ngoài container) |
| **Tiêu đề** | `h1.article-header__title` |
| **Sapo** | `h4.article-content__lead` — nằm **trong** thân bài |
| **Thời gian** | `time.article-meta__time` — `18:53, 14/08/2026` |
| **Tác giả** | `div.article-meta__author` — **chuỗi gộp, phải tách; có bài không có tên.** Xem bẫy ① |
| **Bẫy riêng** | ① `div.article-meta__author` **không phải trường tên tác giả** mà là chuỗi gộp: chữ cái avatar + tên + giờ đăng — `"K Kim Phong 15:21, 14/08/2026"`, `"T Thu Linh 15:00, 14/08/2026"`. Tệ hơn: **1/4 mẫu (`vneconomy_01`) chỉ chứa `"18:53, 14/08/2026"`, không có tên nào.** Luật tách tên phải chịu được ca rỗng và tuyệt đối không lấy giờ làm tên. ② `<p>` chứa **xuống dòng cứng giữa câu** (`"giai đoạn này\nchưa"`) — bắt buộc chuẩn hoá `\s+` → một dấu cách. ③ URL bài **phần lớn không có ID số**, chỉ slug + `.htm`; chỉ một phần có đuôi `-1299966.htm`. Đừng viết luật nhận diện bài dựa vào ID số. ④ Chuỗi "Blog chứng khoán" kết bài bằng đoạn miễn trừ trách nhiệm cố định (*"…mang tính chất cá nhân và không đại diện cho ý kiến của VnEconomy…"*) nằm trong `p.text-justify` **không có class riêng** — chỉ bỏ được bằng luật theo văn bản, không bỏ được bằng selector |
| **Đã kiểm** | 4/4 bài — bỏ 2,5% / 5,7% / 8,3% / 8,5%; sạch 3.124–5.659 ký tự. Đoạn miễn trừ ở bài blog **vẫn còn** trong text sạch — ghi nhận là hạn chế đã biết. Kiểm lại 05/09/2026: container + tiêu đề còn đúng, text sạch ≈4.400 ký tự |

### 2.5 VietnamBiz

| | |
|---|---|
| **Container chính** | `div.vnbcbc-body` (biến thể `.vceditor-content`, `.wi-active` — chỉ khớp theo `vnbcbc-body`) |
| **Bỏ — đã quan sát** | `div.VnBizPreviewMode` (7 — khối ảnh + chú thích) · `figure` (7), `figcaption` (7) — cùng bọc trong `VnBizPreviewMode`, giữ cả ba cho chắc |
| **Bỏ — phòng thủ** | `table` — 0 node ở đâu trên trang |
| **Tiêu đề** | `h1.vnbcb-title` — chú ý **`vnbcb`**, không phải `vnbcbc` như thân bài |
| **Sapo** | `div.vnbcbc-sapo` (bài cũ dùng `div.sapo`) |
| **Thời gian** | `span.vnbcba-time.time-detail` — `18:27 \| 14/08/2026`, có ký tự `\|` ở giữa |
| **Tác giả** | `p.author` — có bài kèm nguồn dịch: *"Khải Nguyên (Theo Bloomberg)"* |
| **Bẫy riêng** | ① Bốn tiền tố class rất giống nhau và **dễ nhầm**: `vnbcb-` (khung bài) · `vnbcbc-` (nội dung bài) · `vnbcba-` (meta) · `vnbcbcbs-` (tag). Sai một chữ là chọn nhầm khối — bản đầu của chính tài liệu này ghi `div.vnbcbc-relate` trong khi class thật là **`div.vnbcbc-relate-box`** (3 node/trang ở 3/4 mẫu), và nó **nằm ngoài** `div.vnbcbc-body` nên không cần bỏ. Tag thật là `div.vnbcbcbs-tags` / `div.box-tag-detail`, cũng ngoài container. ② `div.vnbcb-author` chứa giờ + nút "Chia sẻ" chứ **không** chứa tên tác giả — tên nằm ở `p.author` |
| **Đã kiểm** | 4/4 bài — bỏ 0,0% / 0,6% / 2,3% / 3,5%; sạch 2.024–3.999 ký tự. **Nguồn sạch nhất bộ**: thân bài gần như chỉ có `<p>`. Kiểm lại 05/09/2026: container + tiêu đề còn đúng, text sạch ≈3.445 ký tự |

### 2.6 BNews

| | |
|---|---|
| **Container chính** | `div.lr-ct` |
| **Bỏ — đã quan sát** | `div.lr-summary-post` (4 — sapo, mở đầu bằng nhãn `BNEWS`) · `div.insertImage` (4 — ảnh + chú thích, 89–157 ký tự) · `div.editor_inpage` / `#divAdmicro_inpage` (4 — quảng cáo chèn giữa bài, rỗng text) · `div.lr-author` (4) · `figure` (4, rỗng text) |
| **Bỏ — phòng thủ** | `figcaption`, `table` — 0 node ở đâu trên trang (chú thích ảnh nằm trong `div.insertImage`, không dùng `figcaption`) |
| **Tiêu đề** | `h1.font-42` |
| **Sapo** | `div.lr-summary-post` — bỏ luôn nhãn `BNEWS` ở đầu |
| **Thời gian** | **không có trong thân trang** ở cả 4 mẫu — `time#currentDate` là *ngày hôm nay của server*, không phải giờ đăng. Lấy giờ đăng từ `pubDate` của RSS |
| **Tác giả** | `div.lr-author` — dạng `Văn Giáp/Bnews/vnanet.vn` |
| **Bẫy riêng** | ① **Bẫy nặng nhất bộ: BNews chạy hai template song song trong cùng một chuyên mục.** Ở template A, đoạn văn nằm trong `<p>` bình thường. Ở template B, **đoạn văn là text node trần còn `<p>` rỗng chỉ làm dấu ngắt**. Đo trên 4 mẫu (sau khi bỏ boilerplate) — xem bảng ngay dưới. Hệ quả: bộ bóc gom `find_all('p')` trả **0 ký tự** cho 2/4 bài và chỉ 24% cho bài thứ ba, **không báo lỗi lần nào**. Phải duyệt text node, không duyệt `<p>` — và đừng dựa vào một bài mẫu để kết luận nguồn này "ổn". ② Có **HTML comment `<!--lr-ct-->`** ngay đầu container — xem mục 3.1 để biết cách bóc nào rò và cách nào không. ③ **Trang bài là UTF-8, khác feed.** Feed RSS của BNews đúng là UTF-16LE (100 null byte/200 byte đầu, [README](README.md) mục 6.1) nhưng cả 4 trang bài đều trả `charset=utf-8` và **không có null byte nào**. Đừng đem luật `iconv` của feed áp cho trang bài — làm thế là hỏng toàn văn. ④ **Đo 2026-09-05:** tiêu đề trang bài ở dạng tổ hợp rời (NFD, không phải NFC) — chuẩn hoá NFC trước khi dùng làm khoá dedupe |
| **Đã kiểm** | 4/4 bài — bỏ 7,2% / 8,7% / 13,0% / 15,7%; sạch 1.572–3.712 ký tự; đầu text sạch chuỗi `lr-ct`, cuối text sạch chữ ký `.../Bnews/vnanet.vn`. Kiểm lại 05/09/2026: container + tiêu đề còn đúng, text sạch 2.958 ký tự |

**Hai template BNews — đo trên container đã bỏ boilerplate:**

| Bài | Số `<p>` | Ký tự **trong** `<p>` | Ký tự ở **text node trần** | Tổng sạch | `find_all('p')` lấy được |
|---|---:|---:|---:|---:|---:|
| bnews_01 | 13 | 3.413 | 0 | 3.425 | **99,6%** |
| bnews_04 | 21 | 893 | 2.801 | 3.712 | **24,1%** |
| bnews_02 | 9 | 0 | 1.997 | 2.010 | **0%** |
| bnews_03 | 9 | 0 | 1.304 | 1.572 | **0%** |

Ba hành vi khác nhau trên 4 bài của **cùng một feed, cùng một ngày**: đầy đủ `<p>` · trộn · rỗng `<p>` hoàn toàn. Không suy ra được tỷ lệ thật ở cỡ mẫu này (xem mục 4).

### 2.7 NguoiQuanSat

| | |
|---|---|
| **Container chính** | `article.entry` (biến thể `.entry-no-padding`) |
| **Bỏ — đã quan sát** | `div.sc-longform-header` (4 — khối gộp chuyên mục + tiêu đề + sapo + tác giả + giờ, 246–435 ký tự) · `div.sc-hightlight-box` (**2/4 bài** — box "thông tin thêm" về doanh nghiệp, 512 và 542 ký tự) · `div.c-box` (4 — quảng cáo `ads_after_sapo_*`, rỗng text) · `figure` (9), `figcaption` (8) · `div.sc-empty-layer` (4, rỗng text) |
| **Bỏ — phòng thủ** | `table` — 0 node ở đâu trên trang |
| **Tiêu đề** | `h1.sc-longform-header-title` |
| **Sapo** | `p.sc-longform-header-sapo` |
| **Thời gian** | `span.sc-longform-header-date` — `14/08/2026 - 21:20`, có bài dùng `14/08/2026 19:26` (không có gạch nối) |
| **Tác giả** | `span.sc-longform-header-author` |
| **Bẫy riêng** | ① `div.sc-hightlight-box` là **văn xuôi hợp lệ** nhưng là nền tiểu sử doanh nghiệp lặp lại giữa nhiều bài — để lại thì vừa tốn token vừa làm hỏng dedupe theo nội dung. ② Toàn bộ metadata nằm **trong** `article.entry`; quên bỏ `sc-longform-header` là mỗi bài dính thêm ~250–435 ký tự trùng sapo. ③ Có `div.c-author-page` ở cuối trang ghi *"Theo Kiến thức Đầu tư"* — nguồn gốc bài, ngoài container chính |
| **Đã kiểm** | 4/4 bài — bỏ 9,2% / 13,8% / 17,1% / **24,9%**; sạch 2.540–5.658 ký tự. Tỷ lệ bỏ cao nhất nhì bộ. Kiểm lại 05/09/2026: container + tiêu đề còn đúng, text sạch ≈2.975 ký tự |

### 2.8 BaoChinhPhu

| | |
|---|---|
| **Container chính** | `div.detail-content.afcbc-body` — **cùng CMS với CafeF**, cùng tên class |
| **Bỏ — đã quan sát** | `div.VCSortableInPreviewMode` (4 — box *"Tham khảo thêm"*, danh sách bài liên quan chèn giữa/cuối bài, 159–287 ký tự) · `figure` (5), `figcaption` (5) |
| **Bỏ — phòng thủ** | `div.detail-relate`, `div.c-banner`, `div.admzone`, `table` — **0 node ở bất kỳ đâu trên cả 4 trang.** Ba cái đầu là suy từ việc dùng chung CMS với CafeF, **không quan sát được ở nguồn này** |
| **Tiêu đề** | `h1.detail-title` |
| **Sapo** | `h2.detail-sapo` — **luôn** có tiền tố `(Chinhphu.vn) - `, bỏ theo [README](README.md) mục 6.6 |
| **Thời gian** | `div.detail-time` — `15/08/2026 06:54` |
| **Tác giả** | **không có selector riêng.** Tên đứng ở `<p>` cuối cùng của thân bài (*"Đỗ Hương (thực hiện)"*, *"Anh Minh"*, *"Lê Anh"*) — chỉ bỏ được bằng luật theo văn bản |
| **Bẫy riêng** | ① **HTML comment rò rỉ:** trong container có `<!--bonewsrelation-->`, `<!--eonewsrelation-->`, các mốc `<!--react-text: 118-->` và **ba dấu thời gian đầy đủ** dạng `Sat Aug 15 2026 06:54:00 GMT+0700 (Indochina Time) -- …`. Hàm nào duyệt mọi `NavigableString` sẽ nhét cả đống này vào cuối `content`, vì `Comment` của BeautifulSoup **là** lớp con của `NavigableString`. Regex `<[^>]+>` thì tình cờ thoát trên mẫu này — xem mục 3.1 để biết vì sao đó không phải chỗ dựa. ② Chuỗi timezone đổi ngôn ngữ giữa các bài: `(Indochina Time)` và `(Giờ Đông Dương)`. ③ Trang nặng 337–342 KB dù thân bài chỉ 3,6–6,7 K ký tự |
| **Đã kiểm** | 4/4 bài — bỏ 8,8% / 9,3% / 9,3% / 19,1%; sạch 3.644–6.671 ký tự. Sau khi loại comment, cuối text chỉ còn dòng tên tác giả. Kiểm lại 05/09/2026: container + tiêu đề còn đúng, text sạch 1.578 ký tự |

### 2.9 TinnhanhCK

| | |
|---|---|
| **Container chính** | `div.article__body.cms-body[itemprop=articleBody]` |
| **Bỏ — đã quan sát** | `div.ads_middle` (11) và `div[id^=adsWeb_]` (12) — quảng cáo, rỗng text nhưng cắt câu · `figure.article__avatar` (**1/4 bài**, rỗng text) · `a.cms-relate` (**3 node, chỉ ở 1/4 bài** — link *"Chi tiết"* trong bài tổng hợp, 24 ký tự) |
| **Bỏ — phòng thủ** | **0 node trong container trên cả 4 mẫu.** `div.article__tag` tồn tại thật (1/trang × 4, có chữ: *"Từ Khoá · Bitcoin ETF · Bitcoin spot · giá Bitcoin · tài sản mã hóa…"*) nhưng **nằm ngoài** container — giữ để đề phòng CMS đổi vị trí. `figcaption` và `table` thì **không xuất hiện ở đâu trên trang** — thuần suy đoán. (`figure` trần khớp đúng 1 node và chính là `figure.article__avatar`) |
| **Tiêu đề** | `h1.article__header.cms-title` |
| **Sapo** | `div.article__sapo.cms-desc` — có tiền tố `(ĐTCK) ` |
| **Thời gian** | `time.time` — `14/08/2026 18:51`; bản máy đọc ở `meta.cms-date[itemprop=datePublished]` |
| **Tác giả** | `a.cms-author` (*"Thạch Bắc tổng hợp"*); `p.author` là bản có tiền tố *"Tác giả "* |
| **Bẫy riêng** | ① Bài dạng tổng hợp *"Thị trường tài chính 24h"* kết mỗi mục bằng `..>>` + `<a class="cms-relate">Chi tiết</a>`. Bỏ thẻ `a` rồi thì **chuỗi `..>>` vẫn còn** vì nó là text node đứng trước — cần thêm luật văn bản dọn `\.\.>>\s*`. ② Đây là dạng bài *nhiều tin trong một*, nội dung trộn vàng, ngoại tệ, dầu, bitcoin, chứng khoán Mỹ/Á — cắt trần 3–4 K ký tự sẽ cắt mất phần chứng khoán Việt nằm cuối. ③ Nguồn nhẹ nhất bộ (94–101 KB/trang) và **sạch nhất về nội dung**: 3/4 bài không bị bỏ một ký tự nào — các selector có khớp node nhưng đều là khối quảng cáo rỗng text. ④ **Đo 2026-09-05, sitemap:** `meta.cms-date[itemprop=datePublished]` trên trang là giờ đăng thật; `lastmod` của sitemap tháng ([README §5.2](README.md)) là giờ **SỬA** bài, không phải giờ đăng — ETL lấy giờ trang, `lastmod` chỉ để dự phòng |
| **Đã kiểm** | 4/4 bài — bỏ 0,0% / 0,0% / 0,0% / 0,5%; sạch 2.452–6.359 ký tự. Kiểm lại 05/09/2026: container + tiêu đề còn đúng, text sạch 4.371 ký tự |

---

## 3. Điểm chung giữa các nguồn

### 3.1 HTML comment là rác thật, không phải rác vô hình

Hai nguồn giấu chữ trong HTML comment ngay bên trong container chính: **BaoChinhPhu** (9 comment — `bonewsrelation`, `eonewsrelation`, các mốc `react-text`, và **ba dấu thời gian đầy đủ** `Sat Aug 15 2026 06:54:00 GMT+0700 (Indochina Time) -- …`) và **BNews** (1 comment — `lr-ct`).

Đã thử ba cách bóc trên chính `baochinhphu_01` và `bnews_01`:

| Cách bóc | Nội dung comment lọt vào text? |
|---|---|
| regex `<[^>]+>` → `" "` | **không** — trên mẫu này |
| duyệt mọi `NavigableString` (`find_all(string=True)`, `.descendants`) | **có** — `Comment` là lớp con của `NavigableString` |
| `Tag.get_text()` của BeautifulSoup | không |

> **Đính chính so với bản đầu của tài liệu này.** Bản đầu ghi regex `<[^>]+>` để lọt nội dung comment. Chạy thật thì **sai**: comment ở cả hai nguồn **không chứa ký tự `>` bên trong** nên `<[^>]+>` nuốt trọn cả khối `<!--…-->`. Đường bằng chứng đúng là parser DOM, không phải regex.
>
> Điều đó **không** biến regex thành cách bóc an toàn — nó chỉ đúng nhờ một tính chất của dữ liệu mà nguồn không cam kết gì: chỉ cần một comment chứa `>` (rất thường gặp trong comment điều kiện hoặc HTML bị comment lại) là nó vỡ, và vỡ **im lặng**.

Luật chung vẫn không đổi: **xoá node comment trước, rồi mới lấy text.** Đây là cách duy nhất không phụ thuộc vào việc thư viện có lọc hộ hay dữ liệu có may mắn hay không.

### 3.2 Sapo bị lặp trong thân bài ở 4/8 nguồn

| Nguồn | Sapo nằm trong container chính | Selector phải bỏ |
|---|---|---|
| Vietstock | có | `p.pHead` |
| VnEconomy | có | `h4.article-content__lead` |
| BNews | có | `div.lr-summary-post` |
| NguoiQuanSat | có (trong khối header gộp) | `div.sc-longform-header` |
| CafeF · VietnamBiz · BaoChinhPhu · TinnhanhCK | không | — |

Bản ghi lưu `summary` riêng ([thiết kế](../../20-design/news-pipeline.md) mục 9.3) nên để sapo lặp trong `content` là trả tiền hai lần cho cùng một đoạn chữ, và làm nhiễu embedding.

### 3.3 Ba loại khối phải bỏ có mặt ở gần như mọi nguồn

| Loại | Xuất hiện ở | Ghi chú |
|---|---|---|
| **Bài liên quan — nằm TRONG container, phải bỏ ở tầng 2** | CafeF (`#listNewsInContent`) · BaoChinhPhu (`.VCSortableInPreviewMode`) · TinnhanhCK (`a.cms-relate`) · NguoiQuanSat (`.sc-hightlight-box`) | Là **văn bản hợp lệ** nên tầng bỏ thẻ không đụng tới. Đây đúng là phần mà [thiết kế](../../20-design/news-pipeline.md) mục 6.5 dự đoán chiếm 20–40% |
| **Bài liên quan — nằm NGOÀI container, tầng 0 lo** | Vietstock (`.scroll-content-sub`, 1 khối × 10 link × ~2,5 K ký tự) · VietnamBiz (`.vnbcbc-relate-box`) · VnEconomy (`section.news-detail` "Đọc tiếp") | Không có trong danh sách bỏ vì chọn đúng container là chúng không lọt vào. Chỉ nguy hiểm khi ai đó nới container cho "chắc ăn" |
| **Chú thích ảnh** | 7/8 nguồn có node thật trong container | Cơ chế khác nhau: `figure`/`figcaption` (CafeF, VnEconomy, NguoiQuanSat, BaoChinhPhu) · `div.VnBizPreviewMode` (VietnamBiz) · `div.insertImage` (BNews — **không** dùng `figcaption`) · `table.img-content` (Vietstock). TinnhanhCK chỉ có `figure.article__avatar` rỗng text |
| **Quảng cáo chèn giữa bài** | CafeF · BNews · NguoiQuanSat · TinnhanhCK — có node thật trong container | Gần như luôn rỗng text, nhưng cắt câu làm đôi nếu nối text thô. VnEconomy có `div.container-adv` nhưng nằm ngoài container |

### 3.4 Ba dạng chữ ký cuối bài

| Dạng | Nguồn | Bỏ được bằng selector |
|---|---|---|
| Thẻ riêng | Vietstock (`p.pAuthor`+`p.pSource`+`p.pPublishTimeSource`) · BNews (`div.lr-author`) | có |
| Ngoài container | CafeF (cùng trong tổ tiên `div.w640.fr.clear`, ngoài `div.detail-content`) · NguoiQuanSat (`div.c-author-page`) | không cần — chọn đúng container là xong |
| `<p>` trần cuối bài | BaoChinhPhu · VnEconomy (đoạn miễn trừ của "Blog chứng khoán") | **không** — cần luật văn bản |

### 3.5 Kích thước — đối chiếu với trần ký tự

Đo trên 33 bài (đã làm sạch, chưa cắt trần):

| | |
|---|---|
| Ngắn nhất | 155 (CafeF CBTT) · ngắn nhất trong bài thường: 672 (Vietstock) |
| Trung vị | 3.124 |
| Dài nhất | 6.671 (BaoChinhPhu) |
| Chạm trần 3.000 | **17/33** |
| Chạm trần 4.000 | **9/33** |

Nghĩa là **trần 3.000 sẽ cắt hơn nửa số bài, trần 4.000 cắt hơn một phần tư.** Số này không tự chốt được câu hỏi 3.000 hay 4.000 ở [thiết kế](../../20-design/news-pipeline.md) mục 12 — nó chỉ nói rằng ở cả hai mức, `content_chars` sẽ chạm trần đủ thường xuyên để việc ghi lại nó là có ích thật.

Tỷ lệ nén HTML thô → text sạch dao động rất mạnh giữa các nguồn:

| Nguồn | HTML thô TB | Text sạch TB | Thô/sạch |
|---|---:|---:|---:|
| TinnhanhCK | 97 KB | 4.188 | 23× |
| CafeF | 108 KB | 2.696 | 40× |
| VietnamBiz | 124 KB | 2.768 | 45× |
| BNews | 135 KB | 2.680 | 50× |
| NguoiQuanSat | 142 KB | 3.404 | 42× |
| VnEconomy | 284 KB | 4.158 | 68× |
| BaoChinhPhu | 339 KB | 5.159 | 66× |
| Vietstock | 446 KB | 2.414 | **184×** |

> **Đơn vị của hai cột số** — đọc kỹ trước khi trích:
> - *HTML thô TB* là **KB thập phân** (byte ÷ 1.000), thống nhất với mọi con số KB khác trong tài liệu. Bản trước ghi cột này bằng byte ÷ 1.024 (tức KiB) nhưng dán nhãn KB — đã quy hết về KB thập phân ngày 15/08/2026, số byte đo được không đổi. Riêng CafeF là trung bình của **4 bài thường**; trang CBTT tính riêng ở mục 2.2.
> - *Thô/sạch* chia **byte HTML cho ký tự text**, nên **không phải tỷ lệ byte thuần**. Text tiếng Việt ở mẫu này đo được 1,31 byte/ký tự, nên quy về cùng đơn vị byte thì tỷ lệ là **≈18–146×**.

Con số này củng cố quyết định **không lưu HTML thô** ([thiết kế](../../20-design/news-pipeline.md) mục 9.2) — mức "gấp 10 lần" ghi trong tài liệu đó là **ước lượng thấp**; đo thật là 23–184 lần (≈18–146 lần nếu so byte với byte).

### 3.6 Hai CMS dùng chung

CafeF và BaoChinhPhu dùng **cùng một CMS** (họ VCCorp/Admicro): cùng `div.detail-content.afcbc-body`, cùng `div.VCSortableInPreviewMode`, cùng `figcaption.PhotoCMS_Caption`. Luật viết cho một bên áp được phần lớn cho bên kia — nhưng **không phải toàn bộ**: BaoChinhPhu rò comment, CafeF thì không; CafeF có ô giá cổ phiếu, BaoChinhPhu thì không.

### 3.7 Encoding trang bài: cả 8 nguồn đều UTF-8

Đếm null byte trên toàn bộ 33 file HTML: **0 byte null ở mọi file**, mọi phản hồi khai `charset=utf-8`.

Đây là điểm khác feed và cần ghi rõ: [README](README.md) mục 6.1 bắt BNews phải `iconv -f UTF-16LE` — **quy tắc đó chỉ đúng cho feed RSS**. Trang bài của BNews là UTF-8 thuần. Áp nhầm luật của feed cho trang bài sẽ phá toàn văn của cả 4 feed BNews.

VietnamBiz thì ngược lại và nhất quán: feed khai `utf-16` nhưng là UTF-8, trang bài cũng UTF-8.

---

## 4. Chưa kiểm chứng được với cỡ mẫu này

Nói thẳng những gì 4 bài/nguồn **không** đủ để khẳng định:

| Điều chưa biết | Vì sao mẫu này không trả lời được |
|---|---|
| **Bài longform / magazine / eMagazine** | Mẫu rút từ feed chuyên mục chứng khoán của một ngày, toàn bài tin thường. VnEconomy có mục Multimedia/eMagazine riêng, NguoiQuanSat dùng tiền tố class `sc-longform-*` cho **cả bài thường** — gợi ý có một template longform khác chưa gặp. **Selector ở đây có thể không khớp với dạng bài đó** |
| **Bài ảnh, video, infographic, podcast** | Không có mẫu nào. Thân bài nhiều khả năng gần rỗng như CBTT — cần đường lui `title_only` |
| **Bài trực tiếp / tường thuật liên tục** | Không có mẫu. Dạng này thường tải thêm bằng JS, HTML tĩnh chỉ có phần đầu |
| **Bài cũ (trước 2024)** | Mọi mẫu đều đăng trong 3 ngày gần nhất. Backfill lịch sử ([thiết kế](../../20-design/news-pipeline.md) mục 9.6) sẽ chạm vào template cũ — VietnamBiz đã lộ dấu vết: có bài dùng `div.sapo`, có bài dùng `div.vnbcbc-sapo` |
| **Trang CBTT của mã khác** | Chỉ 1 mẫu (JVC). Chưa biết bố cục có đổi theo sàn (HOSE/HNX/UPCoM) hay theo loại công bố không |
| **BaoChinhPhu mục chỉ đạo điều hành** | Crawler `chi-dao-dieu-hanh.htm` chưa lấy mẫu riêng. Mẫu hiện có lấy từ RSS `kinh-te`; giả định cùng template nhưng **chưa kiểm** |
| **TinnhanhCK 3 trang chuyên mục** | Mẫu lấy qua sitemap. Chưa kiểm bài đến từ `/ck-quoc-te/`, `/chung-khoan/`, `/dau-tu/` có khác template không |
| **Tỷ lệ hai template của BNews** | Đã thấy cả ba hành vi trên 4 bài (mục 2.6) nhưng 4 bài **không** cho biết template nào phổ biến hơn, có tương quan với chuyên mục / tác giả / thời điểm hay không, và các nguồn khác có cùng bệnh không. Cần đếm trên vài trăm bài trước khi tin bất kỳ tỷ lệ nào |
| **Tác giả VnEconomy khi bài không ghi tên** | `div.article-meta__author` ở `vneconomy_01` chỉ chứa `"18:53, 14/08/2026"` — **không có tên nào**, trong khi 3 bài kia là `"<chữ avatar> <tên> <giờ>"`. Không suy được từ 4 mẫu là bài không tên hiếm hay thường, nên luật tách tên phải chịu được cả hai và **không được** lấy nhầm giờ làm tên |
| **Selector phòng thủ** | 21 selector chưa từng khớp node nào trong container (mục 2); 7 trong số đó tồn tại ngoài container. Không biết chúng là thừa hẳn hay chỉ chưa gặp dạng bài kích hoạt chúng |
| **Độ ổn định theo thời gian** | Đo một lần, một ngày. Class CMS đổi được bất cứ lúc nào — mục 5 nói cách phát hiện |

Ngoài ra, **ba chỗ chưa bỏ được bằng selector** và đang phải chờ luật theo văn bản (chưa viết, chưa kiểm chứng):

1. Dòng tên tác giả cuối bài BaoChinhPhu
2. Đoạn miễn trừ trách nhiệm của chuỗi "Blog chứng khoán" VnEconomy
3. Chuỗi `..>>` sót lại ở TinnhanhCK sau khi bỏ `a.cms-relate`

---

## 5. Giám sát bộ bóc

Cấu trúc trang sẽ đổi. Ba tín hiệu phát hiện sớm, thêm vào bảng ở [thiết kế](../../20-design/news-pipeline.md) mục 10:

| Rủi ro | Cách phát hiện |
|---|---|
| **Selector container chết** | Đếm tỷ lệ bài `classified_from = "title_only"` theo nguồn. Với CafeF CBTT đó là mức nền bình thường; với 7 nguồn còn lại, vọt lên là container đổi tên class |
| **Selector bỏ boilerplate chết** | Theo dõi `content_chars` trung bình theo nguồn theo tuần. Tăng đột ngột nghĩa là một khối rác quay lại. Mốc nền đo 15/08/2026 ở mục 2 |
| **Bóc dính bài khác** (Vietstock cuộn vô hạn) | Cảnh báo khi `content_chars` vượt 2 lần trung vị của chính nguồn đó |

**Lát 8 (2026-09-06):** ETL đếm số bài `refused` theo lý do (`no_container` / `no_title` / `too_short` / `soft404`) mỗi lượt, cảnh báo khi tỷ lệ từ chối > 5%. HTML bài chỉ lưu vào `raw_payload` khi bị từ chối — bài bóc thành công không giữ HTML thô (news-pipeline §9.2).

---

*Tài liệu đi kèm: [danh mục nguồn tin](README.md) · [thiết kế pipeline tin tức](../../20-design/news-pipeline.md) · [`feeds.json`](feeds.json).*
