"""Lát 9a — gắn ngành cho tin + sổ lời gọi model.

- news.article_industry: bài ↔ ngành level 2 (industry-tree.md, 24 ngành). Hai đường: 'ticker' = suy từ article_ticker qua
  market.v_issuer_industry (xác định, không confidence) · 'ai' = model đọc hiểu (mọi nhóm — chủ dự án 2026-09-06: tin vĩ mô
  trong nước/quốc tế cũng thuộc ngành). `via` TRONG PK như article_ticker: cùng (bài, ngành) do hai đường tìm ra là HAI dòng —
  phép đo "AI trùng suy-từ-mã bao nhiêu" chạy bằng SQL. Bảng riêng, không cột mảng: giữ FK, giữ via, giữ confidence.
- ops.llm_call: một dòng mỗi lời gọi model (token 4 loại, độ trễ, trạng thái) — đo token/thời gian là mục tiêu lát này, và
  lát 10 (chatbot) tính quota trên cùng sổ. `error` KHÔNG BAO GIỜ chứa khoá (core/llm chỉ ghi tên lớp + status).
- Quyền: default privileges của 0009 phủ (dlck_etl ghi news/ops, dlck_api đọc news) — test s15 chứng dưới role thật.

Revision ID: 0018
Revises: 0017
Create Date: 2026-09-06
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0018"
down_revision: Union[str, None] = "0017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE news.article_industry (
          article_id  bigint  NOT NULL REFERENCES news.article,
          industry_id bigint  NOT NULL REFERENCES market.industry,      -- luôn level 2 (kỷ luật code; v_issuer_industry chỉ có level 2)
          via         text    NOT NULL CHECK (via IN ('ticker','ai')),
          confidence  numeric CHECK (confidence BETWEEN 0 AND 1),       -- NULL với 'ticker'
          PRIMARY KEY (article_id, industry_id, via)
        );
        CREATE INDEX ON news.article_industry (industry_id);            -- "mọi tin ngành thép" — truy vấn chủ lực

        CREATE TABLE ops.llm_call (
          call_id           bigint generated always as identity PRIMARY KEY,
          called_at         timestamptz NOT NULL DEFAULT now(),
          purpose           text NOT NULL,                              -- 'news.classify' · lát 10: 'chat'
          model             text NOT NULL,
          thinking          text NOT NULL CHECK (thinking IN ('adaptive','disabled')),
          run_id            bigint REFERENCES ops.etl_run,
          article_id        bigint REFERENCES news.article,
          status            text NOT NULL CHECK (status IN ('ok','repaired','failed')),
          http_calls        smallint NOT NULL DEFAULT 1,                -- 2 khi phải gọi lại sửa schema
          input_tokens      int,
          cache_read_tokens int,
          output_tokens     int,
          thinking_tokens   int,
          latency_ms        int NOT NULL,
          error             text                                        -- 'rate_limit: RateLimitError 429' — không khoá
        );
        CREATE INDEX ON ops.llm_call (purpose, called_at);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE ops.llm_call;
        DROP TABLE news.article_industry;
        """
    )
