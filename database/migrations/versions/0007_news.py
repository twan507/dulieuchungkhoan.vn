"""news articles, revisions, tagging, and search

Revision ID: 0007
Revises: 0006
Create Date: 2026-08-25

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE FUNCTION news.immutable_unaccent(text) RETURNS text
        LANGUAGE sql IMMUTABLE PARALLEL SAFE STRICT
        RETURN extensions.unaccent('extensions.unaccent'::regdictionary, $1);
        -- unaccent() gốc không IMMUTABLE (phụ thuộc search_path) nên không đứng được trong
        -- generated column / index biểu thức; wrapper qualify dictionary tường minh để IMMUTABLE.

        CREATE TABLE news.article (               -- một TIN canonical (sau dedupe) — phần định danh + phân loại
          article_id     bigint generated always as identity PRIMARY KEY,
          canonical_url  text NOT NULL UNIQUE,
          primary_source text NOT NULL,           -- báo của bản canonical: 'cafef', 'vietstock'…
          feed           text,                    -- feed đã bắt tin này (review vòng 2, I5)
          published_at   timestamptz,             -- NULLABLE có chủ đích (vòng 3, I-2): VietnamBiz để
                                                  -- pubDate TRỐNG — NOT NULL sẽ ép ETL bịa timestamp,
                                                  -- đúng bẫy "feed chết vẫn báo tươi" nguồn đã ghi
          published_at_src text NOT NULL DEFAULT 'feed'
                           CHECK (published_at_src IN ('feed','url','unknown')),
                                                  -- 'url' = suy từ timestamp trong URL (luật VietnamBiz);
                                                  -- 'unknown' ⇔ published_at NULL; sắp xếp tầng đọc dùng
                                                  -- coalesce(published_at, fetched_at)
          fetched_at     timestamptz NOT NULL,
          group_no       smallint CHECK (group_no BETWEEN 1 AND 3),
                                                  -- nhóm taxonomy — do lưới AI quyết; nhóm 'x' (loại bỏ)
                                                  -- biểu diễn bằng group_no NULL + nhãn trong labels
                                                  -- (ghi tường minh — vòng 3, M-3); CHECK cho sub: danh
                                                  -- sách 20 mã từ news-pipeline, liệt kê trong migration
          group_from_feed smallint,               -- nhóm GỢI Ý từ feed — cặp với group_no để tự phát hiện
                                                  -- feed xếp sai nhóm (news-pipeline §7.3; review vòng 2, I5)
          sub            text,                    -- sub-taxonomy ('3b'…) — 20 sub đã chốt
          group_overridden boolean NOT NULL DEFAULT false,
                           -- bật khi group_no KHÁC group_from_feed — ETL phải so bằng IS DISTINCT FROM
                           -- (vòng 4, F14: tin nhãn 'x' có group_no NULL, phép != trả NULL và cờ không
                           --  bao giờ bật → mất tín hiệu phát hiện feed xếp sai nhóm)
          confidence     numeric,
          classified_from text CHECK (classified_from IN ('content','title_only')),
          content_chars  int,                     -- số ký tự nạp classifier (đối chiếu chọn trần 3k/4k sau)
          ticker_step_ran boolean NOT NULL DEFAULT false,   -- phân biệt "không có mã" vs "chưa chạy gắn mã"
          labels         text[] NOT NULL DEFAULT '{}'       -- nhãn loại bỏ: 'x_pr', 'x_social'…
        );
        CREATE INDEX ON news.article (published_at);
        CREATE INDEX ON news.article (group_no, sub);
        -- Review vòng 2, I4: hai index của lớp "lọc cấu trúc" — bảng §3 khai mà DDL bản trước quên;
        -- news-pipeline §9.5: "phần lớn truy vấn dừng ở đây".

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
          url         text NOT NULL UNIQUE,       -- unique TOÀN CỤC — cùng một URL báo không được treo
                                                  -- dưới hai tin canonical (vỡ tín hiệu "mấy báo cùng
                                                  -- đăng"; review vòng 2, M13)
          PRIMARY KEY (article_id, url)
        );
        -- Ngữ nghĩa ghi (M8): append qua pipeline, idempotent theo URL — gặp URL đã có thì bỏ qua.

        CREATE TABLE news.article_ticker (
          article_id  bigint NOT NULL REFERENCES news.article,
          security_id bigint NOT NULL REFERENCES market.security,  -- FK chéo schema, CÙNG instance — hợp lệ
          via         text NOT NULL CHECK (via IN ('url','lookup','ai')),
                      -- BA tầng gắn mã của pipeline (§8): 'url' = tách từ URL CafeF CBTT (~75 tin/ngày —
                      -- đo 2026-08-15; số ~200 cũ là suy sai, nguồn đã đính chính — vòng 3, I-8)
                      -- / 'lookup' = đối chiếu chuỗi / 'ai' = đọc hiểu. Lưu tầng để đo độ chính xác.
          PRIMARY KEY (article_id, security_id, via)
                      -- 'via' TRONG PK (vòng 3, I-1): cùng (bài, mã) do hai tầng cùng tìm ra là HAI dòng —
                      -- chính là phép giám sát "đối chiếu mã tầng 2 vs tầng 3 trên cùng một tin"
                      -- (news-pipeline §10); PK cũ không chứa via làm phép này bất khả thi.
        );
        CREATE INDEX ON news.article_ticker (security_id);          -- "mọi tin về HPG" — truy vấn chủ lực
        -- Ngữ nghĩa ghi (M8, sửa vòng 3): idempotent theo PK; tầng đọc dedupe theo (article, security).

        CREATE TABLE news.trade_name (            -- tên thương mại → mã, cho tầng 3 (khớp gần đúng)
          name        text NOT NULL,              -- 'Hòa Phát', 'Thế Giới Di Động'…
          security_id bigint NOT NULL REFERENCES market.security,
          PRIMARY KEY (name, security_id)
        );
        CREATE INDEX ON news.trade_name
          USING gin (news.immutable_unaccent(name) extensions.gin_trgm_ops);
          -- opclass qualify theo luật extension-schema bước 1 (vòng 4, F3 — bản trước để trần)
        -- Index trên BIỂU THỨC unaccent — khuôn truy vấn §3 so sánh qua unaccent, index trên cột thô
        -- sẽ không được dùng (review vòng 2, I4).
        -- Ngữ nghĩa ghi (M8): seed tay + bổ sung dần (UPSERT theo PK); không có đường ghi tự động từ AI.
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE news.trade_name;
        DROP TABLE news.article_ticker;
        DROP TABLE news.article_source;
        DROP TABLE news.article_revision;
        DROP TABLE news.article;
        DROP FUNCTION news.immutable_unaccent(text);
        """
    )
