# Thiết kế pipeline gom và phân loại tin chứng khoán

**Loại tài liệu:** thiết kế (explanation) · **Phiên bản** v3 · **Chốt ngày** 13/08/2026 · **Trạng thái** đã duyệt, chưa cài đặt

Tài liệu này ghi **lựa chọn của dulieuchungkhoan.vn**: kiến trúc xử lý, taxonomy 20 sub, quy tắc phân loại, cách gắn mã cổ phiếu, lược đồ kho. Phần *nguồn tin có gì và cư xử thế nào* — 47 feed, 6 crawler, encoding, khối lượng đo được — nằm ở [danh mục nguồn tin](../10-sources/news/README.md).

> **Đánh số mục kế thừa tài liệu gốc v3** và cố ý không đánh lại, vì hàng chục tham chiếu chéo dạng *"xem mục 6.5"* nằm rải trong cả hai file. Mục 4, 5, 6, 11.1–11.3 và 13 nằm ở [danh mục nguồn tin](../10-sources/news/README.md); các mục còn lại ở file này.

**File máy đọc đi kèm:** [`news/feeds.json`](../10-sources/news/feeds.json).

---

## 1. Tổng quan

| | |
|---|---|
| Nguồn báo | 10 |
| Feed RSS | **47** |
| Nguồn crawl HTML | **6** |
| Nhóm mặc định | Vĩ mô 14 · Quốc tế 12 · DN niêm yết 21 |
| Phân loại | 3 nhóm × **20 sub** + nhãn `x` loại bỏ |
| Khối lượng | 1.620 bài mỗi vòng quét (tổng nội dung feed, **chưa phải** tin mới) |
| Chu kỳ quét | 5–7 phút · riêng CafeF CBTT ≤ 15 phút |

Ba nhóm đích:

1. **Vĩ mô trong nước** — chính sách, tiền tệ, đầu tư công, số liệu
2. **Tài chính quốc tế** — chứng khoán thế giới, ngân hàng trung ương, hàng hoá, địa chính trị, chính sách thương mại
3. **Doanh nghiệp niêm yết** — công bố thông tin, giao dịch nội bộ, vốn, KQKD, nhận định

---

## 2. Kiến trúc

```
47 RSS feed ──┐                                    ┌─► nhóm 3 ─► Gắn mã CP ─┐
              ├─► Chuẩn hoá ─► Lấy + làm sạch ─► Lưới AI ─┤                 ├─► Kho
6 crawler ────┘   encoding       nội dung        MỌI tin  ├─► nhóm 1 / 2 ───┘
                  pubDate        HTML → text     đọc      │
                  dedupe URL     cắt trần 3–4k   TOÀN VĂN └─► nhãn x ─► loại bỏ
```

**Ba nguyên tắc bất biến:**

1. **Không có đường tắt.** Mọi tin đều đi qua lưới AI, kể cả tin từ những feed thuần nhất. Phương án lai (gán sub thẳng cho ~12 feed thuần, tiết kiệm ~40% lượt gọi) đã bị loại: hai đường xử lý song song tạo ra lỗi im lặng khi feed đổi nội dung mà config không đổi theo.

2. **Nhóm từ feed chỉ là gợi ý.** Classifier được quyền ghi đè sang nhóm khác. Xem mục 7.

3. **Làm sạch trước, phân loại sau.** Nội dung phải được bóc về text thuần và cắt trần trước khi vào classifier. Xem mục 6.5.

**Đánh đổi đã chấp nhận:** chi phí phân loại cao hơn ~1,6 lần so với phương án lai, cộng thêm phần nạp toàn văn (~2.000 token/bài). Đã đo thật: **~570 tin/ngày chưa dedupe** (mục 13) → khoảng **1,1 triệu token đầu vào mỗi ngày** nếu phân loại toàn bộ trước khi dedupe. Dedupe trước khi phân loại sẽ hạ xuống ~300–400 nghìn token/ngày — nên **đặt bước dedupe trước lưới AI**, không phải sau.

---

## 3. Taxonomy — 20 sub

### Nhóm 1 · Vĩ mô trong nước (6 sub)

| Mã | Sub | Tỷ trọng đo được |
|---|---|---:|
| `1a` | Thể chế và văn bản pháp quy | 12,5% |
| `1b` | Điều hành Chính phủ *(gồm kiến nghị / tiếng nói khu vực tư nhân)* | 8,8% |
| `1c` | Tiền tệ và tỷ giá | **16,0%** |
| `1d` | Đầu tư công và hạ tầng | 11,6% |
| `1e` | Số liệu vĩ mô | 5,5% |
| `1f` | Thuế và ngân sách | 6,6% |

> Tỷ trọng đo trên 457 tiêu đề. Sub `1a` ban đầu gom cả bốn thứ (văn bản, điều hành, thuế, cải cách) và chiếm ~33% — gấp ba mọi sub khác, nên đã tách. Sub `1g` (môi trường KD và khu vực tư nhân) chỉ đạt 3,1% nên đã gộp vào `1b`.

### Nhóm 2 · Tài chính quốc tế (5 sub)

| Mã | Sub |
|---|---|
| `2a` | Chứng khoán thế giới |
| `2b` | Ngân hàng trung ương |
| `2c` | Hàng hoá và năng lượng |
| `2d` | An ninh và địa chính trị |
| `2e` | Thương mại và thuế quan |

> `2d` và `2e` được thêm ở vòng audit cuối. Trước đó địa chính trị bị xếp nhầm vào nhãn loại bỏ — sai, vì thuế quan và cấm vận tác động trực tiếp lên doanh nghiệp xuất khẩu niêm yết (dệt may, thuỷ sản, thép).

### Nhóm 3 · Doanh nghiệp niêm yết (9 sub)

| Mã | Sub |
|---|---|
| `3a` | CBTT và sự kiện quyền |
| `3b` | Giao dịch nội bộ và cổ đông lớn |
| `3c` | Vốn và cấu trúc |
| `3d` | KQKD và vận hành |
| `3e` | Nhận định và diễn biến thị trường |
| `3f` | Phái sinh, chứng quyền, ETF/quỹ |
| `3g` | Vi phạm và xử phạt |
| `3h` | Margin và ký quỹ |
| `3i` | Xếp hạng tín nhiệm và ESG |

> `3a`–`3f` lấy từ cây chuyên mục có sẵn của Vietstock. `3g`, `3h`, `3i` phát hiện khi kiểm chứng ngược 483 tiêu đề không khớp sub nào.

### Nhãn `x` — loại bỏ

Tin xã hội, thể thao, giáo dục, y tế thuần; PR và advertorial.

---

## 7. Quy tắc phân loại

### 7.1 Đầu vào / đầu ra

**Vào:** tiêu đề · **toàn văn đã làm sạch và cắt trần** · sapo gốc · tên nguồn · slug feed · **nhóm gợi ý từ feed**

**Ra:** `group` (1/2/3 hoặc `x`) · `sub` · `confidence` · `summary_ai` · `tickers[]` nếu group = 3

**Vì sao đọc toàn văn thay vì tiêu đề + sapo:** phân loại chính xác hơn hẳn ở những ca nhảy nhóm 1↔3 mà tiêu đề gây hiểu nhầm (mục 7.2). Và một khi đã nạp toàn văn thì sinh `summary_ai` trong cùng lượt gọi gần như miễn phí — chỉ thêm ~100 token đầu ra.

**Khuôn `summary_ai` phải cố định**, vì nhất quán chính là lý do sinh ra nó: 2–3 câu, 200–300 ký tự, không mở đầu bằng "Bài viết nói về…", **giữ nguyên mọi con số xuất hiện trong bản gốc**. Lưu song song với `summary` gốc, không ghi đè — bản gốc giữ được từ ngữ nguyên bản của toà soạn, đôi khi chính cách chọn chữ là thứ cần tìm. Nên embed cả hai và giữ riêng.

### 7.1b Đường lui khi không lấy được nội dung

Phân loại giờ phụ thuộc vào việc bóc được nội dung. Fetch hỏng — 404, timeout, đổi cấu trúc trang — mà không có đường lui thì bài đó không bao giờ được phân loại và rơi khỏi kho lặng lẽ.

**Quy tắc:** không có nội dung thì vẫn phân loại trên tiêu đề + sapo gốc, đặt `classified_from: "title_only"`.

Hai trường hợp rơi vào đường này, phải phân biệt được:

| Trường hợp | Bản chất | Theo dõi |
|---|---|---|
| **CafeF CBTT** (~200 tin/ngày) | **Hợp lệ, không phải lỗi.** Trang công bố thông tin là bảng hoặc file đính kèm, bóc ra gần rỗng. Nhưng tiêu đề đã mang gần hết thông tin (*"HBH: Ngày đăng ký cuối cùng trả cổ tức bằng tiền mặt"*), mã lấy từ URL chắc chắn 100%, sub gần như luôn là `3a` | Coi là bình thường, đừng cố sửa |
| Nguồn khác | Lỗi thật — fetch hỏng hoặc bộ bóc xuống cấp | Thống kê tỷ lệ theo nguồn, tăng đột biến là báo động |

Đây là nguồn đơn lẻ lớn nhất trong ngày, nên nếu không ghi rõ thì sau này sẽ có người tưởng bộ bóc đang hỏng.

### 7.2 Nhóm từ feed là tín hiệu, không phải ràng buộc

Ma trận nhảy nhóm quan sát được:

| Hướng | Tần suất | Ví dụ thật |
|---|---|---|
| 1 → 3 | **thường xuyên** | *"70% cổ phiếu giảm giá từ đầu năm, chuyên gia nói gì trước mùa báo cáo quý II?"* và *"Dragon Capital chỉ ra 3 cú hích cho thị trường chứng khoán nửa cuối năm"* — cả hai nằm trong feed chính sách/vĩ mô |
| 3 → 1 | **thường xuyên** | *"Giá USD tự do, ngân hàng giảm mạnh"*, *"Lãi tiết kiệm bình quân tiến sát mốc 8%"* — nằm trong feed tài chính/ngân hàng vốn xếp nhóm 3 |
| 2 → 1 | hiếm | *"Tuyên bố chung Việt Nam–Australia"* — đối ngoại nằm trong feed quốc tế |
| bất kỳ → `x` | rải rác | PR, tin xã hội |

Nhóm 2 gần như **không nhảy nhóm lớn** — nó chỉ đổi sub bên trong.

### 7.3 Bắt buộc ghi log ghi đè

Mỗi lần `group != group_from_feed` phải bật cờ `group_overridden` và ghi log.

**Vì sao:** feed nào bị ghi đè quá thường xuyên là dấu hiệu nhóm mặc định của nó đang đặt sai. Đây đúng là cách 4 feed xếp nhầm bị phát hiện trong quá trình khảo sát (`vietnambiz/tai-chinh`, `bnews/ngan-hang-18`, `vietstock/ngan-hang` thực chất là tiền tệ → nhóm 1; `vneconomy/thi-truong-von-tai-chinh` thực chất là hàng hoá → nhóm 2). Biến việc audit thủ công đó thành cơ chế tự động.

---

## 8. Gắn mã cổ phiếu — 3 tầng

Chỉ chạy cho tin được phân vào nhóm 3. Dừng ở tầng đầu tiên khớp.

**Tầng 1 · Tách từ URL** — chắc chắn tuyệt đối, chỉ áp dụng CafeF CBTT.

```
/du-lieu/MQN-2951937/… → MQN
```

**Tầng 2 · Regex + đối chiếu danh sách niêm yết** — bắt chuỗi 3 ký tự in hoa rồi **bắt buộc** đối chiếu danh sách ~1.600 mã HOSE/HNX/UPCoM.

> Không được nhận dạng bằng regex đơn thuần. `USD`, `GDP`, `CPI`, `FDI`, `ESG`, `IPO`, `ETF`, `EVN` đều là chuỗi 3 chữ in hoa — và trớ trêu là `SME` lại đúng là một mã thật.

**Tầng 3 · AI + bảng ánh xạ tên doanh nghiệp** — xử lý tiêu đề gọi tên thay vì gọi mã.

```
"Lãnh đạo Gemadept hé lộ thời điểm triển khai Gemalink giai đoạn 3" → GMD
```

Cần bảng tên thương mại → mã: "Hoà Phát", "Thế Giới Di Động", "Vinamilk" không bao giờ xuất hiện dưới dạng mã trong tiêu đề.

**Một tin có thể mang nhiều mã.** Ví dụ *"22/27 ngân hàng ghi nhận CASA giảm"* gắn cùng lúc CTG, EIB, STB, TCB, TPB. Lưu dạng mảng, kèm tầng nào sinh ra mã đó để về sau đo được độ chính xác từng tầng.

**Mã rỗng là kết quả hợp lệ.** Tin *"Chuyên gia chỉ ra 3 sai lầm nhà đầu tư dễ mắc khi xuống tiền"* thuộc sub `3e` nhưng không nhắc mã nào. Trường `ticker_step_ran` phân biệt "không có mã" với "chưa chạy" — ép buộc phải có mã sẽ khiến AI bịa.

---

## 9. Kho lưu trữ

Mục đích của kho không phải phục vụ tin trong ngày, mà là **tra cứu lịch sử nhiều năm** — "giai đoạn quý II/2026 có tin gì về ngành thép". Điều đó chi phối mọi quyết định dưới đây.

### 9.1 Lưu toàn văn ngay khi nhận

Lấy nội dung ngay lúc thu thập, không dùng cache lười.

Lý do quyết định **không phải dung lượng mà là link rot**. Cache lười chỉ đúng khi nội dung vẫn còn ở đó lúc cần tra — mà với kho nhiều năm thì chính những bài muốn tra lại sau 2 năm là những bài dễ biến mất nhất. Báo Việt Nam đổi CMS, gỡ bài, đổi cấu trúc URL khá thường xuyên; ngay trong khảo sát này đã gặp TinnhanhCK có route RSS hỏng nằm nguyên đó và VietnamFinance đóng băng feed nửa tháng mà không dấu hiệu gì.

Kho chỉ có link chết thì giá trị bằng không. Giá trị của nó chính là bản ghi nội dung tại thời điểm đó.

### 9.2 Dung lượng — không phải yếu tố cần cân nhắc

**Khối lượng đã đo thật** (quét ngày 11–13/08/2026, xem mục 13):

| | |
|---|---|
| Tin mỗi ngày, **chưa dedupe** | **~570** |
| Ước tính sau dedupe chặt | ~150–200 (tỷ lệ nén ~3,5 lần) |
| Text thuần mỗi bài | 4–8 KB |
| Mỗi năm (sau dedupe) | ~275–365 MB · nén còn ~70–90 MB |
| 5 năm | ~1,4–1,8 GB |

Postgres tự nén cột `text` lớn qua TOAST nên con số thực tế còn thấp hơn.

**Không lưu HTML thô.** Đo thật trên 33 trang bài của cả 8 nguồn (2026-08-15, [cấu trúc trang bài](../10-sources/news/article-structure.md) mục 3.5): HTML thô trung bình **97–446 KB/trang** tuỳ nguồn (KB thập phân; trang nặng nhất bộ 527 KB), tức **gấp 23–184 lần** phần text sạch bóc ra từ chính nó — tỷ lệ đó so byte HTML với ký tự text, quy về cùng đơn vị byte là **≈18–146 lần**. Con số *"khoảng 50 KB/bài, gấp 10 lần"* ghi ở bản trước là ước lượng thấp. Kết luận không đổi, chỉ chắc thêm: HTML thô không mang thêm thông tin và làm tìm kiếm khó hơn.

> **CafeF CBTT gần như không dedupe được** — mỗi bản công bố thông tin là một doanh nghiệp khác nhau. Ở mức ~75 tin/ngày thì đó là phần sàn không nén được của kho.
>
> Kể cả nếu dedupe kém hơn dự kiến và giữ nguyên 570/ngày thì cũng chỉ ~1 GB/năm. Dung lượng không phải yếu tố cần cân nhắc ở bất kỳ kịch bản nào.

### 9.3 Bản ghi

```jsonc
{
  "id"               : "uuid",
  "url"              : "…",          // canonical, đã bỏ utm_*, gidzl, fragment
  "source_urls"      : [ "…", "…" ], // mọi báo đã đưa tin này — xem 9.4
  "title"            : "…",
  "summary"          : "…",          // sapo GỐC đã làm sạch — xem 6.6
  "summary_ai"       : "…",          // AI sinh, 200–300 ký tự, khuôn cố định — xem 7.1
  "content"          : "…",          // TEXT THUẦN toàn văn, không cắt, không HTML
  "content_fetched_at": "2026-08-13T09:26:10+07:00",
  "version"          : 1,            // tăng khi báo sửa bài — xem 9.4

  "source"           : "vietstock",
  "feed"             : "739/chung-khoan/giao-dich-noi-bo",
  "group_from_feed"  : 3,            // gợi ý, không ràng buộc

  "published_at"     : "2026-08-13T09:15:10+07:00",
  "fetched_at"       : "2026-08-13T09:25:48+07:00",

  "group"            : 3,            // do AI quyết
  "sub"              : "3b",
  "group_overridden" : false,        // bật khi group != group_from_feed
  "confidence"       : 0.91,
  "classified_from"  : "content",    // "content" | "title_only" — xem 7.1b
  "content_chars"    : 3200,         // số ký tự thực nạp vào classifier (sau cắt trần)

  "tickers"          : [ { "code": "GMD", "via": "ai" },
                         { "code": "MBS", "via": "lookup" } ],
  "ticker_step_ran"  : true,         // phân biệt "không mã" vs "chưa chạy"

  "labels"           : []            // ["x_pr"], ["x_social"]…
}
```

### 9.4 Dedupe và bất biến

**Dedupe giữ lại độ phủ.** Gộp về một bản ghi canonical cho phần nội dung, nhưng giữ mảng `source_urls` liệt kê mọi báo đã đưa tin đó. Tốn vài trăm byte và giữ lại một tín hiệu không tái tạo được về sau: tin 8 báo cùng đăng khác hẳn tin một báo đăng.

**Không ghi đè.** Báo có sửa bài sau khi đăng. Nếu bóc lại thấy nội dung khác, thêm bản ghi mới với `version` tăng thay vì đè bản cũ. Ghi đè khiến kho lịch sử phản ánh hiện tại chứ không phản ánh quá khứ — mất luôn mục đích tồn tại của nó.

**Ghi `content_fetched_at`** để biết bản text ứng với thời điểm nào.

### 9.5 Tìm kiếm trên Postgres

Ở quy mô 55.000–150.000 bản ghi mỗi năm, **Postgres một mình là đủ** — không cần vector DB riêng. Dùng ba lớp bổ sung nhau, không thay thế nhau:

| Lớp | Công cụ | Dùng cho |
|---|---|---|
| Lọc cấu trúc | index thường trên `published_at`, `group`, `sub`, `tickers` | "tin nhóm 3b về HPG trong quý II/2026" — phần lớn truy vấn dừng ở đây |
| Từ khoá | `tsvector` + GIN | "bài nào nhắc *chống bán phá giá*" |
| Ngữ nghĩa | `pgvector` + HNSW | "tin về ảnh hưởng thuế quan Mỹ lên ngành dệt may" — câu hỏi khái niệm, từ khoá không bắt được |

**Về full-text tiếng Việt.** Postgres không có từ điển tiếng Việt. Nhưng tiếng Việt gần như không biến hình nên **không cần stemmer** — vấn đề duy nhất là tách từ: `simple` cắt theo khoảng trắng nên "chứng khoán" thành hai token rời.

```
to_tsvector('simple', unaccent(title || ' ' || content))
```

- `unaccent` là bắt buộc, không phải tuỳ chọn — người dùng gõ không dấu rất phổ biến
- Cụm từ thì dùng `phraseto_tsquery` thay vì `to_tsquery`, Postgres xử lý được thứ tự token
- Nếu về sau thấy độ chính xác từ khoá không đủ, giải pháp đúng là **tách từ tiếng Việt trước khi index** (underthesea / pyvi / VnCoreNLP) để "chứng khoán" thành một token `chứng_khoán`. Đây là thêm một phụ thuộc vào pipeline nên chỉ làm khi có bằng chứng cần

**`pg_trgm`** nên bật luôn — nó phục vụ hai việc: tìm gần đúng tên doanh nghiệp, và chính là công cụ cho **tầng 3 gắn mã cổ phiếu** (bảng ánh xạ tên thương mại → mã ở mục 8).

**Embedding.** Ở mức 150/ngày thì embed mọi bài là rẻ. Bài báo ngắn nên một vector cho mỗi bài (title + sapo + phần đầu content) thường đủ; chỉ chia nhỏ khi bài dài. HNSW trên 150k vector là chuyện nhẹ với Postgres.

> Quyết định mô hình embedding nên chốt sớm. Embed lại 50.000 bài về sau tốn hơn embed dần từ đầu rất nhiều.

**Chưa cần partition.** 55–150k dòng/năm là nhỏ. Chỉ tính đến khi chạm vài triệu dòng.

### 9.6 Backfill lịch sử — làm sớm

Vì mục đích là tra cứu quá khứ, đừng đợi kho tự tích luỹ. Backfill ngay khi dựng:

- **TinnhanhCK** — `sitemaps/news-{YYYY}-{M}.xml` lùi được nhiều năm, có `lastmod` là giờ đăng thật
- **BNews**, **NguoiQuanSat** — có sitemap tương tự

Đây là cách duy nhất có dữ liệu trước ngày bật hệ thống, và nó chỉ khả dụng chừng nào họ còn giữ sitemap.

### 9.7 Bản quyền

Lưu tiêu đề + link để tham chiếu là một chuyện, lưu toàn văn là chuyện khác. Với kho tra cứu nội bộ dùng riêng thì rủi ro thấp. Nhưng trước khi chia sẻ hay phát hành lại nội dung thì phải xem lại — và nên kiểm tra `robots.txt` của 9 nguồn xem có tuyên bố `Content-Signal` như Stockbiz (`ai-train=no, use=reference`) hay không.

---

## 10. Giám sát và cảnh báo

| Rủi ro | Cách phát hiện |
|---|---|
| **Feed chết âm thầm** | Mọi feed đều trả `lastBuildDate` = giờ hiện tại, **kể cả feed chết từ 2014**. Trường đó vô dụng. Giám sát bằng `pubDate` của item đầu tiên; cảnh báo khi > 7 ngày |
| **`pubDate` rỗng báo tươi giả** | VietnamBiz để `pubDate` trống; hàm parse ngày thường biến chuỗi rỗng thành giờ hiện tại nên feed chết vẫn báo tươi. Luật giám sát phải kiểm chuỗi rỗng **trước khi** parse, và với VietnamBiz thì đo độ tươi bằng timestamp trong URL |
| CafeF CBTT trôi tin | Đếm khoảng trống ID giữa hai vòng quét liên tiếp |
| Encoding hỏng | Kiểm tra tỷ lệ ký tự thay thế trong tiêu đề |
| Nhóm mặc định sai | Thống kê tỷ lệ `group_overridden` theo feed |
| PR lọt lưới | Thống kê tỷ lệ nhãn `x` theo feed |
| Mã CP nhận nhầm | Đối chiếu mã sinh ở tầng 2 với tầng 3 trên cùng một tin |

---

## 11. Đã loại bỏ — và vì sao

> Mục 11.1–11.3 (nguồn, cách lấy tin và feed bị loại) nằm ở [danh mục nguồn tin](../10-sources/news/README.md) vì chúng là dữ kiện về nguồn. Ở đây chỉ giữ phần lựa chọn thiết kế.

### 11.4 Ý tưởng thiết kế bị loại

| Ý tưởng | Lý do |
|---|---|
| **Fast-path cho feed thuần** | Gán sub thẳng từ config cho ~12 feed có độ thuần ≥ 70%, tiết kiệm ~40% lượt gọi AI. Loại vì hai đường xử lý song song phải bảo trì riêng và tạo lỗi im lặng khi feed đổi nội dung mà config không đổi theo |
| **Sub `1g` môi trường KD và khu vực tư nhân** | Chỉ đạt 3,1% — yếu nhất bộ. Gộp vào `1b` |
| **Sub cải cách hành chính** | 2,4% — quá nhỏ. Gộp vào `1a` |
| **Sub tội phạm KT và xử lý sai phạm ở nhóm 1** | 2,2% — đã có `3g` vi phạm và xử phạt gánh |
| **Sub địa phương / vùng kinh tế** | 8,1% nhưng trùng gần hết với `1d`. Là *chiều* (địa lý), không phải sub chủ đề |
| **Xếp địa chính trị vào nhãn loại bỏ** | Sai. Thuế quan, cấm vận, kiểm soát xuất khẩu tác động trực tiếp lên DN xuất khẩu niêm yết. Đã sửa thành `2d` và `2e` |

---

## 12. Còn để ngỏ

| Việc | Ghi chú |
|---|---|
| **Đo tỷ lệ dedupe thật** | Khối lượng thô đã đo (~570/ngày, mục 13). Còn lại là tỷ lệ trùng giữa 8 nguồn — ước tính ~3,5 lần nhưng chưa kiểm chứng. Đây là số quyết định ngân sách phân loại |
| **Danh sách mã niêm yết** | Cần nguồn cập nhật ~1.600 mã HOSE/HNX/UPCoM cho tầng 2 |
| **Bảng tên thương mại → mã** | Cho tầng 3. Dùng `pg_trgm` để khớp gần đúng |
| **Ngưỡng `confidence`** | Dưới bao nhiêu thì đưa vào hàng chờ rà tay |
| **Chọn mô hình embedding** | Nên chốt trước khi chạy thật — embed lại toàn kho về sau rất tốn. Nhớ embed cả `summary` và `summary_ai`, giữ riêng |
| **Tách từ tiếng Việt** | Chỉ làm khi có bằng chứng `simple` + `unaccent` không đủ chính xác |
| **Luật bỏ boilerplate từng nguồn** | ✅ đã khảo sát 2026-08-15 — luật từng nguồn ở [article-structure.md](../10-sources/news/article-structure.md); còn ngỏ: dạng bài longform/video/bài cũ chưa phủ |
| **Trần 3.000 hay 4.000 ký tự** | Chốt bằng cách đối chiếu `content_chars` với các ca phân loại sai sau vài tuần chạy. Đã có số nền: trên 33 bài mẫu, **17/33 dài ≥ 3.000 ký tự, 9/33 ≥ 4.000, trung vị 3.124** (đo 2026-08-15, [article-structure.md](../10-sources/news/article-structure.md) mục 3.5). Cả hai mức đều chạm trần đủ thường xuyên để `content_chars` đáng ghi lại, nhưng chưa có ca phân loại sai thật nên chưa chốt được mức nào |

---

## 14. Trạng thái phiên làm việc

**Chốt ngày 13/08/2026. Chưa viết dòng code nào — tài liệu thiết kế là toàn bộ sản phẩm của phiên này.**

### Đã chốt

- 8 nguồn báo · 47 feed RSS · 6 nguồn crawl HTML *(đếm lại theo host thật ngày 15/08/2026; bản 13/08 ghi nhầm 10 — số feed và số crawler không đổi)*
- Taxonomy 3 nhóm / 20 sub / nhãn `x`
- Mọi tin qua lưới AI, không có đường tắt
- Nhóm từ feed là gợi ý, classifier được ghi đè, phải ghi log
- Classifier đọc toàn văn đã làm sạch và cắt trần
- Sinh `summary_ai` lưu song song sapo gốc
- Lưu toàn văn ngay khi nhận, bất biến, không ghi đè
- Postgres: `tsvector` + `pgvector` + `pg_trgm`
- Khối lượng thô đã đo: ~570 tin/ngày

### Ba file bàn giao

| File | Nội dung |
|---|---|
| `docs/20-design/news-pipeline.md` | tài liệu này — lựa chọn thiết kế |
| `docs/10-sources/news/README.md` | danh mục nguồn và đặc tính kỹ thuật |
| `docs/10-sources/news/feeds.json` | 47 feed + taxonomy + nhật ký loại bỏ, dạng máy đọc |

> Tài liệu gốc một file `THIET_KE_PIPELINE.md` v3 đã được tách làm hai theo ranh giới *dữ kiện về nguồn* / *lựa chọn của dulieuchungkhoan.vn*; `feeds_config_v3.json` đổi tên thành `docs/10-sources/news/feeds.json`. Nội dung không đổi một chữ nào.

### Việc tiếp theo khi quay lại

Theo thứ tự phụ thuộc:

1. ✅ **Đã khảo sát cấu trúc trang bài của cả 8 nguồn** (2026-08-15) — luật bỏ boilerplate từng nguồn (mục 6.5 tầng 2) nằm ở [cấu trúc trang bài](../10-sources/news/article-structure.md). Còn ngỏ: dạng bài longform/video/bài cũ chưa phủ.
2. **Chốt nguồn danh sách mã niêm yết** và bảng tên thương mại → mã.
3. **Chốt mô hình embedding** trước khi bắt đầu nạp dữ liệu.
4. **Dựng khung thu thập + chuẩn hoá**, chạy không có AI trong 1 tuần để đo tỷ lệ dedupe thật.
5. Có số dedupe rồi mới chốt ngân sách và bật lưới phân loại.
6. **Backfill lịch sử** từ sitemap TinnhanhCK / BNews / NguoiQuanSat — làm càng sớm càng tốt, dữ liệu đó chỉ còn chừng nào họ còn giữ sitemap.

### Cảnh báo cho người triển khai

Bảy cạm bẫy trong tài liệu này đều đã gặp thật, không phải giả định: `lastBuildDate` luôn báo tươi · slug feed vô nghĩa với Vietstock và BNews · `pubDate` rỗng của VietnamBiz · encoding khai sai · thẻ HTML escape trong sapo Vietstock · tiền tố `(Chinhphu.vn)` · feed sống mà nội dung đóng băng.

Điểm chung: **mọi thứ nguồn tự khai về chính nó đều phải kiểm lại bằng dữ liệu.**

---

*Tài liệu này đi kèm [`news/feeds.json`](../10-sources/news/feeds.json) — danh sách 47 feed ở dạng máy đọc được.*
