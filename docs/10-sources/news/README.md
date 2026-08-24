# Nguồn tin chứng khoán — danh mục và đặc tính kỹ thuật

**Loại tài liệu:** tra cứu (reference) · **Đo ngày** 13/08/2026 · **cấu trúc trang bài** 15/08/2026 · **Trạng thái** đã kiểm chứng, chưa cài đặt

Mọi con số ở đây đo bằng `curl` trên 307 URL ứng viên và 1.408 tiêu đề đã đọc thật. Không có số nào là ước lượng.

Tài liệu này mô tả **nguồn tin có gì và cư xử thế nào** — 47 feed RSS, 6 nguồn crawl HTML, encoding, định dạng thời gian, khối lượng đo được, và những nguồn đã loại. Phần *dulieuchungkhoan.vn quyết định xử lý ra sao* nằm ở [thiết kế pipeline tin tức](../../20-design/news-pipeline.md).

> **Đánh số mục kế thừa tài liệu gốc `THIET_KE_PIPELINE.md` v3** và cố ý không đánh lại, vì hàng chục tham chiếu chéo dạng *"xem mục 6.5"* nằm rải trong cả hai file. Mục nào ở file nào:
>
> | Mục | File |
> |---|---|
> | 1 Tổng quan · 2 Kiến trúc · 3 Taxonomy | [thiết kế](../../20-design/news-pipeline.md) |
> | **4 Danh sách 47 feed · 5 Sáu nguồn crawl · 6 Quy tắc chuẩn hoá** | **file này** |
> | 7 Quy tắc phân loại · 8 Gắn mã cổ phiếu · 9 Kho lưu trữ · 10 Giám sát | [thiết kế](../../20-design/news-pipeline.md) |
> | **11.1–11.3 Nguồn và feed đã loại** | **file này** |
> | 11.4 Ý tưởng thiết kế bị loại · 12 Còn để ngỏ · 14 Trạng thái | [thiết kế](../../20-design/news-pipeline.md) |
> | **13 Khối lượng đã đo** | **file này** |
> | Cấu trúc trang bài và luật bỏ boilerplate *(đo 15/08/2026, 8 nguồn)* | [article-structure.md](article-structure.md) |

**File máy đọc đi kèm:** [`feeds.json`](feeds.json) — 47 feed, taxonomy 20 sub, nhật ký loại bỏ.

---

## 4. Danh sách 47 feed RSS

### Nhóm 1 — Vĩ mô trong nước (14 feed)

| # | Nguồn | URL feed | Bài | Encoding | Ghi chú lấy tin |
|---|---|---|---:|---|---|
| 1 | cafef | `https://cafef.vn/vi-mo-dau-tu.rss` | 50 | UTF-8 | chuẩn |
| 2 | vietstock | `https://vietstock.vn/761/kinh-te/vi-mo.rss` | 20 | UTF-8 | ID quyết định, slug trang trí |
| 3 | vietstock | `https://vietstock.vn/758/tai-chinh/thue-va-ngan-sach.rss` | 20 | UTF-8 | ID quyết định, slug trang trí |
| 4 | vneconomy | `https://vneconomy.vn/tieu-diem.rss` | 50 | UTF-8 | chuẩn |
| 5 | vneconomy | `https://vneconomy.vn/dau-tu.rss` | 50 | UTF-8 | chuẩn |
| 6 | vietnambiz | `https://vietnambiz.vn/thoi-su.rss` | 30 | **UTF-16LE** | chuẩn |
| 7 | vietnambiz | `https://vietnambiz.vn/du-bao.rss` | 30 | **UTF-16LE** | chuẩn |
| 8 | bnews | `https://bnews.vn/rss/kinh-te-viet-nam-1.rss` | 20 | **UTF-16LE** | ID quyết định, slug trang trí |
| 9 | nguoiquansat | `https://nguoiquansat.vn/rss/vi-mo` | 40 | UTF-8 | đường dẫn không có đuôi .rss |
| 10 | baochinhphu | `https://baochinhphu.vn/kinh-te.rss` | 50 | UTF-8 | pubDate M/D/YYYY AM/PM, không TZ |
| 11 | baochinhphu | `https://baochinhphu.vn/chinh-sach-va-cuoc-song.rss` | 50 | UTF-8 | pubDate M/D/YYYY AM/PM, không TZ |
| 12 | vietstock | `https://vietstock.vn/757/tai-chinh/ngan-hang.rss` | 20 | UTF-8 | ID quyết định, slug trang trí |
| 13 | vietnambiz | `https://vietnambiz.vn/tai-chinh.rss` | 30 | **UTF-16LE** | chuẩn |
| 14 | bnews | `https://bnews.vn/rss/ngan-hang-18.rss` | 20 | **UTF-16LE** | ID quyết định, slug trang trí |

### Nhóm 2 — Tài chính quốc tế (12 feed)

| # | Nguồn | URL feed | Bài | Encoding | Ghi chú lấy tin |
|---|---|---|---:|---|---|
| 1 | cafef | `https://cafef.vn/tai-chinh-quoc-te.rss` | 50 | UTF-8 | chuẩn |
| 2 | vietstock | `https://vietstock.vn/772/the-gioi/tai-chinh-quoc-te.rss` | 20 | UTF-8 | ID quyết định, slug trang trí |
| 3 | vietstock | `https://vietstock.vn/773/the-gioi/chung-khoan-the-gioi.rss` | 20 | UTF-8 | ID quyết định, slug trang trí |
| 4 | vneconomy | `https://vneconomy.vn/chung-khoan-quoc-te.rss` | 50 | UTF-8 | chuẩn |
| 5 | vneconomy | `https://vneconomy.vn/kinh-te-the-gioi.rss` | 50 | UTF-8 | chuẩn |
| 6 | bnews | `https://bnews.vn/rss/kinh-te-the-gioi-2.rss` | 20 | **UTF-16LE** | ID quyết định, slug trang trí |
| 7 | nguoiquansat | `https://nguoiquansat.vn/rss/the-gioi` | 40 | UTF-8 | đường dẫn không có đuôi .rss |
| 8 | vneconomy | `https://vneconomy.vn/thi-truong-von-tai-chinh.rss` | 50 | UTF-8 | chuẩn |
| 9 | vneconomy | `https://vneconomy.vn/thi-truong-xuat-nhap-khau.rss` | 50 | UTF-8 | chuẩn |
| 10 | vietstock | `https://vietstock.vn/118/hang-hoa/nong-san-thuc-pham.rss` | 20 | UTF-8 | ID quyết định, slug trang trí |
| 11 | vietstock | `https://vietstock.vn/742/hang-hoa/kim-loai.rss` | 20 | UTF-8 | ID quyết định, slug trang trí |
| 12 | vietstock | `https://vietstock.vn/34/hang-hoa/nhien-lieu.rss` | 20 | UTF-8 | ID quyết định, slug trang trí |

### Nhóm 3 — Doanh nghiệp niêm yết (21 feed)

| # | Nguồn | URL feed | Bài | Encoding | Ghi chú lấy tin |
|---|---|---|---:|---|---|
| 1 | cafef | `https://cafef.vn/thi-truong-chung-khoan.rss` | 50 | UTF-8 | chuẩn |
| 2 | vietstock | `https://vietstock.vn/144/chung-khoan.rss` | 30 | UTF-8 | ID quyết định, slug trang trí |
| 3 | vietstock | `https://vietstock.vn/830/chung-khoan/co-phieu.rss` | 20 | UTF-8 | ID quyết định, slug trang trí |
| 4 | vietstock | `https://vietstock.vn/733/doanh-nghiep.rss` | 30 | UTF-8 | ID quyết định, slug trang trí |
| 5 | vietstock | `https://vietstock.vn/741/chung-khoan/niem-yet.rss` | 20 | UTF-8 | ID quyết định, slug trang trí |
| 6 | vietstock | `https://vietstock.vn/738/doanh-nghiep/co-tuc.rss` | 20 | UTF-8 | ID quyết định, slug trang trí |
| 7 | vietstock | `https://vietstock.vn/739/chung-khoan/giao-dich-noi-bo.rss` | 20 | UTF-8 | ID quyết định, slug trang trí |
| 8 | vietstock | `https://vietstock.vn/746/doanh-nghiep/ipo-co-phan-hoa.rss` | 20 | UTF-8 | ID quyết định, slug trang trí |
| 9 | vietstock | `https://vietstock.vn/764/doanh-nghiep/tang-von-m-a.rss` | 20 | UTF-8 | ID quyết định, slug trang trí |
| 10 | vietstock | `https://vietstock.vn/3118/doanh-nghiep/trai-phieu-doanh-nghiep.rss` | 20 | UTF-8 | ID quyết định, slug trang trí |
| 11 | vietstock | `https://vietstock.vn/4186/chung-khoan/chung-khoan-phai-sinh.rss` | 20 | UTF-8 | ID quyết định, slug trang trí |
| 12 | vietstock | `https://vietstock.vn/3358/chung-khoan/etf-va-cac-quy.rss` | 20 | UTF-8 | ID quyết định, slug trang trí |
| 13 | vietstock | `https://vietstock.vn/1636/nhan-dinh-phan-tich/nhan-dinh-thi-truong.rss` | 20 | UTF-8 | ID quyết định, slug trang trí |
| 14 | vneconomy | `https://vneconomy.vn/doanh-nghiep-niem-yet.rss` | 50 | UTF-8 | chuẩn |
| 15 | vneconomy | `https://vneconomy.vn/chung-khoan.rss` | 50 | UTF-8 | chuẩn |
| 16 | vneconomy | `https://vneconomy.vn/khung-phap-ly-chung-khoan.rss` | 50 | UTF-8 | chuẩn |
| 17 | vietnambiz | `https://vietnambiz.vn/chung-khoan.rss` | 30 | **UTF-16LE** | chuẩn |
| 18 | vietnambiz | `https://vietnambiz.vn/doanh-nghiep.rss` | 30 | **UTF-16LE** | chuẩn |
| 19 | bnews | `https://bnews.vn/rss/chung-khoan-33.rss` | 20 | **UTF-16LE** | ID quyết định, slug trang trí |
| 20 | nguoiquansat | `https://nguoiquansat.vn/rss/chung-khoan` | 40 | UTF-8 | đường dẫn không có đuôi .rss |
| 21 | nguoiquansat | `https://nguoiquansat.vn/rss/doanh-nghiep` | 40 | UTF-8 | đường dẫn không có đuôi .rss |

---

## 5. Sáu nguồn crawl HTML

Những nguồn này không có RSS dùng được, phải lấy bằng cách khác.

### 5.1 CafeF — công bố thông tin

```
https://cafef.vn/du-lieu/tin-doanh-nghiep.chn
```

| | |
|---|---|
| Nhóm mặc định | 3 · sub `3a` |
| Chu kỳ | **≤ 15 phút** — không thương lượng |
| Vì sao gấp | Trang chỉ giữ ~26 tin. Đo bằng hai bản chụp cách nhau 5,05 giờ: 22 tin mới, chỉ 3 tin cũ còn sót → buffer khoảng 5–6 giờ giữa trưa nhưng **ngắn hơn nhiều vào buổi sáng** khi doanh nghiệp dồn nộp hồ sơ (~20 tin/giờ lúc 9h so với 4,4 tin/giờ lúc trưa). Poll thưa là mất tin trong khung sáng. |

**Đây là nguồn quan trọng nhất không có RSS.** Nó phủ cả mã nhỏ và UPCoM mà báo chí không bao giờ viết bài — với những mã đó, đây là nguồn tin duy nhất.

Mã cổ phiếu nằm sẵn trong đường dẫn, không phải đoán:

```
/du-lieu/MQN-2951937/mqn-nghi-quyet-hoi-dong-quan-tri.chn
          ^^^
```

Lưu ý:
- Loại `HNX`, `HOSE`, `UPCOM` — đó là sở giao dịch tự công bố số liệu, không phải cổ phiếu
- Dedupe thêm theo (mã + tiêu đề): có tin trùng nội dung nhưng khác ID, ví dụ `HNX-2951892` và `HNX-2951895` cùng tiêu đề
- Tiêu đề lấy từ HTML nên dính rác (ký tự xuống dòng, chữ thừa) — phải làm sạch

### 5.2 TinnhanhCK — sitemap tháng

```
https://www.tinnhanhchungkhoan.vn/sitemaps/news-2026-{M}.xml
```

Site **không có RSS**: `/rss.html` trả HTTP 200 nhưng body đúng 12 byte, nội dung là chuỗi `RssPage.html` — tên template CMS bị lộ, route tồn tại nhưng hỏng. Mọi đường dẫn `.rss` khác đều 404.

Bù lại sitemap tốt hơn RSS:

```xml
<loc>.../scic-se-thoai-toan-bo-von-tai-66-doanh-nghiep-post395840.html</loc>
<lastmod>2026-08-13T09:15:10+07:00</lastmod>
```

- `lastmod` = **giờ đăng thật kèm +07:00**
- Giữ nguyên cả tháng (723 URL trong tháng 8), lùi được nhiều năm → backfill lịch sử được, RSS không làm được
- File xếp theo thứ tự thời gian, bài mới nằm cuối → chỉ cần đọc phần đuôi mới thêm
- Phải dùng `curl --compressed` (sitemap gzip)

Sitemap cho URL + giờ đăng nhưng **không cho chuyên mục**. Ghép với 3 trang chuyên mục dưới đây theo post ID trong URL:

| Trang | Nhóm mặc định |
|---|---|
| `https://www.tinnhanhchungkhoan.vn/ck-quoc-te/` | 2 |
| `https://www.tinnhanhchungkhoan.vn/chung-khoan/` | 3 |
| `https://www.tinnhanhchungkhoan.vn/dau-tu/` | 1 |

Mỗi trang trả ~101 bài mỗi lần tải. Phân trang `?page=2` bị bỏ qua (trả lại bộ cũ) — dựa vào sitemap để backfill.

### 5.3 BaoChinhPhu — chỉ đạo điều hành

```
https://baochinhphu.vn/chi-dao-dieu-hanh.htm
```

Nhóm mặc định 1, sub `1b`. Phải crawl HTML vì **RSS của mục này chết từ tháng 6/2014** — trang HTML vẫn có bài 2026 bình thường.

---

## 6. Quy tắc chuẩn hoá

### 6.1 Encoding

| Nguồn | Xử lý |
|---|---|
| **BNews** | `iconv -f UTF-16LE -t UTF-8` — UTF-16 thật |
| **VietnamBiz** | **UTF-8**, không convert — mặc dù prolog XML khai `encoding="utf-16"` |
| Còn lại | UTF-8, không cần xử lý |

> **Đừng tin phần khai encoding.** VietnamBiz khai `utf-16` nhưng bytes thực tế là UTF-8, không có null byte nào. Chạy `iconv` lên nó sẽ hỏng toàn bộ feed. BNews mới là UTF-16 thật (100 null byte trong 200 byte đầu).
>
> **Cách kiểm đúng:** đếm null byte trong ~100 byte đầu. Trên 10 thì là UTF-16, bằng 0 thì là UTF-8. Và khi convert phải dùng `UTF-16LE` chứ không phải `UTF-16` — cái sau đoán big-endian và trả ra ký tự rác.

### 6.2 Thời gian đăng

| Nguồn | Định dạng | Xử lý |
|---|---|---|
| **VietnamBiz** | **`<pubDate>` RỖNG hoàn toàn** — cả 30 thẻ đều trống, không có thẻ thời gian nào khác | Bắt buộc lấy từ URL: `202681312363179` = `YYYY` + `M` + `DD` + `HHMMSS` + serial |
| BaoChinhPhu | `M/D/YYYY h:mm:ss AM/PM` | **Không có timezone** → giả định +07. URL cũng nhúng giờ: `102` + `YYMMDD` + `HHMMSS` + serial |
| TinnhanhCK | ISO 8601 `+07:00` trong sitemap | dùng trực tiếp |
| Còn lại | RFC 822 | dùng trực tiếp |

> **Bẫy chết người:** `pubDate` rỗng đưa qua hàm parse ngày thường trả về **thời điểm hiện tại** thay vì lỗi. Nghĩa là VietnamBiz sẽ luôn trông như vừa cập nhật, kể cả khi feed đã chết. Phải coi giá trị rỗng là *không xác định*, không phải *bây giờ*. Xem thêm mục 10.

**Không bao giờ lấy giờ crawl làm giờ đăng.** WiData mắc đúng lỗi này: trường `time` của họ là giờ ingest chứ không phải giờ đăng, lại còn gắn hậu tố `Z` trong khi giá trị là giờ Việt Nam. Hệ quả là bài từ tháng 6 bị hiển thị "1 giờ trước".

### 6.3 Dedupe

- Theo **URL đã chuẩn hoá**: bỏ `utm_*`, `gidzl`, fragment
- Nhiều feed cùng một site trỏ về chung một kênh — ví dụ VnEconomy có 5 slug khác nhau (`thi-truong`, `thi-truong-bat-dong-san`, `thi-truong-chung-khoan`, `thi-truong-tieu-dung`, `kin-te-thi-truong`) đều trả kênh "Thị trường"
- Riêng CafeF CBTT: dedupe thêm theo (mã + tiêu đề)

### 6.4 Bẫy slug

Vietstock và BNews **chỉ đọc ID số trong URL, slug chỉ là trang trí**. Slug sai vẫn trả HTTP 200 với nội dung của ID đó.

```
vietstock.vn/739/kinh-te/vi-mo.rss      → trả "Giao dịch nội bộ" (ID 739), KHÔNG phải vĩ mô
bnews.vn/rss/tai-chinh-ngan-hang-4.rss  → trả "Thị trường" (ID 4)
```

Luôn lấy ID từ trang index chính thức: `vietstock.vn/rss` (55 feed), `bnews.vn/rss.html` (~27 feed), `cafef.vn/rss.chn` (25 feed), `vneconomy.vn/rss.html` (~90 chuyên mục).

### 6.5 Làm sạch nội dung trước khi vào classifier

Đây là bước bắt buộc nằm **trước** lưới AI, không phải sau. Classifier đọc toàn văn (mục 7.1) nên mọi ký tự rác đều là token phải trả tiền.

**Ba tầng, không phải hai.** [Khảo sát cấu trúc trang bài](article-structure.md) (đo 15/08/2026, 33 bài / 8 nguồn) cho thấy phải chèn một tầng **trước** hai tầng vốn có:

0. **Cắt đúng container chính rồi mới xử lý.** Không cắt thì tầng 1 nuốt cả header, footer và box tin liên quan của toàn trang: trang thô nặng 94–527 KB trong khi thân bài chỉ 155–6.671 ký tự. Cắt đúng còn khiến phần lớn khối "bài liên quan" biến mất mà không cần luật nào — ví dụ khối cuộn vô hạn ~2,5 K ký tự của Vietstock vốn nằm **ngoài** container. **Selector container và luật bỏ boilerplate của từng nguồn nằm ở [article-structure.md](article-structure.md)** — đó là bảng tra sống, sửa ở đó chứ không chép lại vào đây.
1. **Bỏ thẻ HTML** — nhưng phải **decode entity trước rồi mới strip tag**. Làm ngược thứ tự sẽ hỏng với Vietstock (xem cảnh báo dưới).
2. **Bỏ khối phi nội dung** — "Xem thêm", danh sách bài liên quan, tên tác giả, chú thích ảnh, ô quảng cáo. Đây mới là phần ngốn token nhiều nhất: chúng là text hợp lệ nên tầng 1 không đụng tới, mà có thể chiếm 20–40% độ dài. Phải viết luật riêng cho từng nguồn.

**Cắt trần 3.000–4.000 ký tự.** Với tin tức, tín hiệu phân loại nằm gần trọn trong mấy đoạn đầu. Bài phân tích dài 15.000 ký tự mà nạp hết là trả tiền cho phần đuôi gần như vô ích. Ghi lại số ký tự thực nạp vào `content_chars` để về sau kiểm chứng: nếu các bài phân loại sai đều chạm trần thì biết trần đang đặt thấp.

**Lưu ý:** `content` trong kho lưu **toàn văn đầy đủ**, không cắt. Cắt trần chỉ áp dụng cho phần nạp vào classifier.

### 6.6 Làm sạch sapo

Đo trên 1.497 sapo của 47 feed: không nguồn nào rỗng, trung bình 159–250 ký tự tuỳ nguồn (chênh 1,6 lần), 73% nằm trong khoảng 150–400, chỉ 1% dưới 80 ký tự. **Chất lượng sapo gốc đủ dùng** — những cái ngắn là do tin ngắn chứ không phải sapo hỏng.

Nhưng có ba lỗi bóc bắt buộc phải xử lý:

| Nguồn | Vấn đề | Xử lý |
|---|---|---|
| **Vietstock** | Nhét thẻ `<img>` dưới dạng **entity đã escape** (`&lt;img src=…&gt;`). Bộ strip tag thông thường không bắt được vì lúc đó nó vẫn là text | Decode entity trước, rồi mới strip tag. Không làm thì 420 sapo dính ~120 ký tự rác mỗi cái |
| **CafeF**, **NguoiQuanSat** | Nhét khối `<a><img></a>` vào đầu description | Strip tag bình thường |
| **BaoChinhPhu** | Tiền tố `(Chinhphu.vn) - ` ở **100/100** bài | Bỏ tiền tố |

---

## 11. Đã loại bỏ — và vì sao

### 11.1 Nguồn bị loại

| Nguồn | Lý do |
|---|---|
| **VietnamFinance** | Toàn bộ feed chuyên mục **đóng băng từ 28/07/2026** (`chung-khoan` từ 10/06). Trang vẫn xuất bản — trang chủ ở `d149026` trong khi RSS đứng ở `d148245`, chênh ~780 bài. Mọi đường dẫn **không tồn tại** lại trả feed tươi (kiểm chứng bằng slug tự bịa `khong-ton-tai-abc123.rss` → trả feed ngày 13/08). CMS có handler mặc định cho route không khớp. Dùng được nhưng là xây trên lỗi của họ. Giá trị riêng thấp: nặng bất động sản/advertorial, không giữ mảng nào độc quyền |
| **Stockbiz** | Không RSS, không sitemap. Next.js SPA chỉ render 11 bài mỗi chuyên mục. Backend là FireAnt, token nhúng trong trang — không đụng vào. robots cho phép crawl tham chiếu nhưng chặn bot AI |
| **fili.vn** | Mirror 100% của Vietstock (cùng VAFE). Feed vĩ mô hai bên: cùng 20 item, cùng tiêu đề, cùng thứ tự |
| **chinhphu.vn** | Không tự host bài nào — mọi link trỏ sang baochinhphu.vn. Không RSS, không sitemap. ASP.NET WebForms, phân trang bằng `__doPostBack` |

### 11.2 Cách lấy tin bị loại

| Đối tượng | Lý do |
|---|---|
| **BaoChinhPhu timelinelist** | Phân trang sạch (20 bài/trang, trang 1 và 2 không trùng bài nào) nhưng **54% không phân loại được** — trộn cả thể thao, giáo dục, y tế, hình sự. Dùng RSS chuyên mục thay thế |
| **API WiData** | `POST wichart.vn/wichartapi/wichart/news/getnews` có tồn tại nhưng ký request (6 header, `sign` 32 ký tự hex) và mã hoá response bằng AES CryptoJS. Là cơ chế chống crawl cố ý |

### 11.3 Feed bị loại

| Nhóm | Feed | Lý do |
|---|---|---|
| Chết > 1 năm | `vietstock/1328/dong-duong` · `vneconomy/an-pham-tu-van-va-tieu-dung` | 518 và 499 ngày |
| BaoChinhPhu chết | `chi-dao-dieu-hanh` (6/2014) · `thi-truong` (1/2022) · `chinh-sach` (12/2021) · `doanh-nghiep` (5/2026) | — |
| PR trả tiền | `cafef/doanh-nghiep-gioi-thieu` | Tươi 50 bài nhưng là advertorial. Không bộ lọc tự động nào bắt được |
| Sai nhóm nặng | `baochinhphu/quoc-te` | Đo được 4% thương mại / 10% địa chính trị. Nội dung là đối ngoại, không phải thị trường tài chính |
| Tên đánh lừa | `bnews/phan-tich-doanh-nghiep-41` | Không có phân tích nào. 6 bài, mẫu: *"Kinh gõm đa thanh âm an nhiên lên núi Bà Đen"* — là PR |
| Lẫn quảng cáo | `cafef/doanh-nghiep` | *"Trải nghiệm tham quan HEINEKEN Việt Nam tại Đà Nẵng"*, *"Cập nhật tiến độ Aqua City"* |
| Sai nhóm | `cafef/tai-chinh-ngan-hang` | Mẫu toàn giá USD/vàng SJC — thuộc nhóm 1, không phải nhóm 3 |
| Sai nhóm | `vneconomy/chuyen-dong-doanh-nghiep` | *"Italia siết quy trình SPS nông sản"* — thương mại, không phải DN niêm yết |
| Trùng lặp | `vneconomy/chuyen-dong-kinh-te-the-gioi-24h` | Trùng gần hết với `chung-khoan-quoc-te` |
| Nửa lạc đề | `vietnambiz/chuyen-dong-thi-truong` | Có Becamex TDC, cổ phiếu V68 — nhưng cũng có *"Van Gogh Timeless khai mạc tại Hà Nội"* |
| Nặng tin tỉnh | `vietstock/768/kinh-te-dau-tu` | — |
| Ít giá trị đầu tư | `bnews/doanh-nghiep-6` · `nguoiquansat/tai-chinh-ngan-hang` | Thông cáo doanh nghiệp / giá vàng và khảo sát thương hiệu |
| Biên | `vietstock/775/kinh-te-nganh` | 10% thương mại, 20% địa chính trị — không đủ đặc trưng |
| Không liên quan CK | ~200 feed | lifestyle · phong-cach · noi-that-phong-thuy · tim-viec-lam · bi-quyet-lam-giau · suc-khoe · giao-duc · dep · am-thuc · du-lich · giai-tri · video · multimedia · thoi-tiet · lich-cat-dien · o-to-xe-may · nhan-luc · y-te · van-hoa · khoa-giao |

## 13. Khối lượng đã đo — 11–13/08/2026

Đo thật, không ước lượng. Phương pháp và cạm bẫy ghi lại để sau này đo lại còn so sánh được.

### 13.1 Kết quả

| Nguồn | Tin/ngày | Cách đo |
|---|---:|---|
| 42 feed RSS có `pubDate` chạy | 394 | tốc độ tính theo giờ: `(n−1) / span_giờ × 24` |
| 5 feed VietnamBiz | 22 | `pubDate` rỗng → lấy giờ từ URL |
| **Cộng 47 feed RSS** | **416** | |
| TinnhanhCK | 76 | **số tuyệt đối** từ sitemap: 77 bài ngày 11/8, 75 bài ngày 12/8 |
| CafeF CBTT | ~75 | so hai bản chụp trang cách nhau 5,05 giờ |
| BaoChinhPhu chỉ đạo điều hành | ~3 | |
| **TỔNG, chưa dedupe** | **~570** | |

Kiểm chứng chéo cho ngày 12/8: đếm trực tiếp được 209 tin trên 35 feed phủ đủ, cộng ước tính 12 feed bị cắt (~227) ra ~436 — khớp với 416 tính bằng tốc độ.

### 13.2 Cạm bẫy phương pháp

**Đếm thô theo ngày cho số sai.** Cách ngây thơ (gom hết `pubDate` rồi đếm theo ngày) cho ra 358 tin ngày 12/8 và **164 tin ngày 11/8**. Con số 164 sai hoàn toàn.

Lý do: RSS chỉ giữ 20–50 bài mới nhất. Feed nào ra tin nhiều thì bài của ngày 11/8 đã trôi khỏi feed. Trong 47 feed có **12 feed không vươn tới ngày 11/8** — và đó chính là những feed ra tin nhiều nhất, nên phần bị mất là phần lớn nhất.

**Cách đo đúng:** tính tốc độ từng feed theo giờ (`bài chia cho số giờ phủ sóng`), rồi cộng lại. Muốn đếm trực tiếp một ngày thì chỉ được tính những feed có bài cũ nhất **trước** ngày đó.

**Ngày phải là ngày làm việc.** 11 và 12/8/2026 đều là thứ Ba và thứ Tư. Cuối tuần khối lượng thấp hơn nhiều, đo vào đó sẽ ra số vô nghĩa.

### 13.3 Bốn lỗi trong tài liệu mà lần đo này phát hiện

| Lỗi | Đã sửa ở |
|---|---|
| VietnamBiz bị ghi là UTF-16 — thực tế là UTF-8, chỉ khai sai trong prolog XML | 6.1 |
| VietnamBiz có `<pubDate>` rỗng hoàn toàn — phải lấy giờ từ URL | 6.2 |
| `pubDate` rỗng parse thành "bây giờ" → feed chết vẫn báo tươi, luật giám sát không bắt được | 6.2, 10 |
| CafeF CBTT ghi ~200 tin/ngày — suy sai từ một cụm dồn buổi sáng. Thực tế ~75 | 5.1, 9.2 |

Ba trong bốn lỗi này cùng một dạng: **tin vào phần metadata mà nguồn tự khai** thay vì kiểm bằng dữ liệu. Giống hệt bẫy `lastBuildDate` và bẫy slug đã gặp trước đó.

---

