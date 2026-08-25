# Bước 6 — Tin tức: bài viết, phiên bản, gắn mã, tìm kiếm

**Trạng thái:** 🟡 chờ duyệt · **Phụ thuộc:** bước 1–5 (✅) · **Phạm vi:** schema `news` — kho toàn văn ~570 tin/ngày trước dedupe từ 8 báo, đầu ra của pipeline tin ([news-pipeline.md](../../../20-design/news-pipeline.md)). Đây là schema **duy nhất ghi nguồn** — báo nào đăng là dữ kiện nghiệp vụ, không phải xuất xứ kỹ thuật.

---

## 1. Bài viết và phiên bản — không ghi đè

```sql
CREATE TABLE news.article (               -- một TIN canonical (sau dedupe) — phần định danh + phân loại
  article_id     bigint generated always as identity PRIMARY KEY,
  canonical_url  text NOT NULL UNIQUE,
  primary_source text NOT NULL,           -- báo của bản canonical: 'cafef', 'vietstock'…
  published_at   timestamptz NOT NULL,
  fetched_at     timestamptz NOT NULL,
  group_no       smallint,                -- nhóm taxonomy (1..3) — do lưới AI quyết
  sub            text,                    -- sub-taxonomy ('3b'…) — 20 sub đã chốt
  group_overridden boolean NOT NULL DEFAULT false,  -- AI ghi đè gợi ý từ feed → phải log
  confidence     numeric,
  classified_from text CHECK (classified_from IN ('content','title_only')),
  content_chars  int,                     -- số ký tự nạp classifier (đối chiếu chọn trần 3k/4k sau)
  ticker_step_ran boolean NOT NULL DEFAULT false,   -- phân biệt "không có mã" vs "chưa chạy gắn mã"
  labels         text[] NOT NULL DEFAULT '{}'       -- nhãn loại bỏ: 'x_pr', 'x_social'…
);

CREATE TABLE news.article_revision (      -- NỘI DUNG theo phiên bản — báo sửa bài thì THÊM, không đè
  article_id   bigint  NOT NULL REFERENCES news.article,
  version      smallint NOT NULL DEFAULT 1,
  title        text NOT NULL,
  sapo         text,                      -- sapo gốc của báo
  summary_ai   text,                      -- tóm tắt AI sinh — lưu SONG SONG sapo, không thay
  content      text NOT NULL,             -- toàn văn đã bóc boilerplate
  content_fetched_at timestamptz NOT NULL,-- bản text này ứng với thời điểm nào
  tsv tsvector GENERATED ALWAYS AS
      (to_tsvector('simple', news.immutable_unaccent(title || ' ' || content))) STORED,
  PRIMARY KEY (article_id, version)
);
CREATE INDEX ON news.article_revision USING gin (tsv);
-- unaccent() gốc không đứng được trong generated column (không IMMUTABLE);
-- migration tạo wrapper news.immutable_unaccent — kỹ thuật chuẩn, chi tiết trong plan.

CREATE TABLE news.article_source (        -- dedupe GIỮ ĐỘ PHỦ: mọi báo đã đăng tin này
  article_id  bigint NOT NULL REFERENCES news.article,
  source_name text NOT NULL,
  url         text NOT NULL,
  PRIMARY KEY (article_id, url)
);
```

- **Ngữ nghĩa ghi:** `article` chèn một lần khi tin vào kho; các cột **phân loại** (group/sub/confidence/labels) được job AI cập nhật — chúng là *nhận định của mình*, sửa được. Còn **nội dung** bất biến: bóc lại thấy báo đã sửa bài → thêm dòng `revision` version+1, bản cũ giữ nguyên (kho lịch sử phải phản ánh quá khứ, không phản ánh hiện tại).
- **Dedupe giữ độ phủ:** 8 báo cùng đăng một tin → một `article` + 8 dòng `article_source`. Tốn vài trăm byte, giữ lại tín hiệu không tái tạo được: *tin cả làng đăng* khác hẳn *tin một báo đăng*.

## 2. Gắn mã cổ phiếu và tên thương mại

```sql
CREATE TABLE news.article_ticker (
  article_id  bigint NOT NULL REFERENCES news.article,
  security_id bigint NOT NULL REFERENCES market.security,  -- FK chéo schema, CÙNG instance — hợp lệ
  via         text NOT NULL CHECK (via IN ('lookup','ai')),-- tầng 2 đối chiếu / tầng 3 AI
  PRIMARY KEY (article_id, security_id)
);
CREATE INDEX ON news.article_ticker (security_id);          -- "mọi tin về HPG" — truy vấn chủ lực

CREATE TABLE news.trade_name (            -- tên thương mại → mã, cho tầng 3 (khớp gần đúng)
  name        text NOT NULL,              -- 'Hòa Phát', 'Thế Giới Di Động'…
  security_id bigint NOT NULL REFERENCES market.security,
  PRIMARY KEY (name, security_id)
);
CREATE INDEX ON news.trade_name USING gin (name gin_trgm_ops);
```

- Gắn mã chỉ nhận `market.security` đang `listed` (lọc ở pipeline) — danh bạ nguồn chứa cả mã huỷ niêm yết, gắn nhầm là tin đeo mã của doanh nghiệp đã rời sàn (bẫy architecture §3.1). Nhờ bước 2, đây là **một nguồn danh bạ duy nhất** — pipeline tin không nạp danh sách riêng.
- Hai giá trị `via` tách hai tầng gắn mã (đối chiếu chuỗi vs AI đọc hiểu) — số liệu lệch nhau giữa hai tầng là chỉ báo giám sát chất lượng có sẵn trong thiết kế pipeline.

## 3. Tìm kiếm ba lớp — hai lớp bây giờ, một lớp chờ

| Lớp | Công cụ | Trạng thái |
|---|---|---|
| Lọc cấu trúc | index thường: `published_at`, `(group_no, sub)`, `article_ticker(security_id)` | ✅ bước này |
| Từ khoá | `tsv` + GIN, `unaccent` (người Việt gõ không dấu rất phổ biến) | ✅ bước này |
| **Gõ gần đúng (chịu lỗi gõ)** | `pg_trgm` (index, lọc ứng viên) **+ `levenshtein`** (`fuzzystrmatch` — xếp hạng theo số bước sửa ít nhất: `ngui`→`nguoi` = 1 bước) | ✅ bước này *(yêu cầu chủ dự án 2026-08-25)* |
| Ngữ nghĩa | `pgvector` + HNSW | ⏳ **hoãn có chủ đích** |

Lớp gõ-gần-đúng áp cho **chuỗi ngắn** — ô tìm kiếm, tên doanh nghiệp/`trade_name`, ticker — nơi người dùng gõ thiếu/sai ký tự. Khuôn truy vấn chuẩn (chi tiết trong plan): `pg_trgm` quét index ra nhóm ứng viên → `levenshtein(unaccent(query), unaccent(candidate))` xếp hạng — `levenshtein` một mình không dùng được index nên **bắt buộc** đi sau trgm, không thay trgm. Toàn văn bài viết vẫn thuộc lớp từ khoá (`tsv`).

```sql
-- HOÃN: tạo ở migration riêng khi chốt mô hình embedding (chiều vector chưa biết).
-- Thiết kế định trước — embed CẢ sapo lẫn summary_ai, giữ riêng:
-- news.article_embedding(article_id, version, kind CHECK ('content','summary','summary_ai'),
--                        model text, embedding vector(N), PRIMARY KEY (article_id, version, kind))
```

Hoãn vì: chọn model embedding phải chốt **trước khi nạp cả kho** (embed lại 50.000 bài về sau rất tốn — việc để ngỏ của roadmap §5), nhưng **sau** khi có vài tuần dữ liệu thật để thử. Extension `vector` vẫn bật từ migration đầu (bước 1) nên khi chốt chỉ thêm một bảng.

## 4. Điểm cần duyệt ở bước này

- [ ] **Tách bài/phiên bản**: phần định danh + phân loại ở `article` (phân loại sửa được — là nhận định của mình), nội dung ở `revision` bất biến, báo sửa bài thì thêm version — đồng ý?
- [ ] **Dedupe giữ độ phủ**: một tin canonical + danh sách mọi báo đã đăng — đồng ý?
- [ ] **Gắn mã trỏ thẳng `market.security`** (chỉ mã đang niêm yết), phân biệt đường gắn `lookup`/`ai` — đồng ý?
- [ ] **Tìm kiếm**: lọc cấu trúc + từ khoá không dấu + **gõ gần đúng (trgm lọc, Levenshtein xếp hạng)** chạy ngay; lớp ngữ nghĩa (embedding) hoãn tới khi chốt model — đồng ý?
- [ ] **Bảng tên thương mại → mã** với khớp gần đúng (`pg_trgm`) cho tầng gắn mã AI — đồng ý?

## 5. Kiểm chứng của bước này (seam)

1. Bài chứa "chứng khoán" → truy vấn không dấu `'chung khoan'` qua `tsv` bắt được; bài không chứa → không bắt (case sai).
2. Thêm revision version 2 cho bài đã có → 2 dòng cùng `article_id`, bản 1 nguyên vẹn; chèn trùng `(article_id, version)` → lỗi PK.
3. `article_ticker` trỏ `security_id` không tồn tại → lỗi FK; xoá security đang được tin trỏ → bị chặn (FK bảo vệ).
4. `trade_name` khớp gần đúng: seed `'Hòa Phát'` → truy vấn `similarity('Hoà Phát')` (khác dấu thanh) vẫn ra đúng mã (literal, ngưỡng chốt trong plan).
4b. Levenshtein: `levenshtein('ngui','nguoi') = 1` (giải tay — thêm một chữ 'o'); truy vấn `'ngui'` trên seed chứa `'người'` (qua unaccent) xếp ứng viên đó hạng nhất.
5. `canonical_url` trùng → lỗi UNIQUE (dedupe tầng DB là hàng rào cuối, dedupe thật ở pipeline).
6. Migration tạo `news.immutable_unaccent` thành công và `tsv` sinh tự động khi INSERT (không phải NULL).

Chốt xong → bước 7 (staging + ops — hai schema hậu trường, khép vòng spec).
