"""Lát 5 — báo cáo tài chính.

- financial_report_file: khoá theo `source_id` (id của nguồn). Đo 2026-09-04: BID và BAB mỗi mã có
  hai `id` khác nhau trỏ CÙNG một URL (bản quý 3 và bản 9 tháng luỹ kế cùng một file PDF), nên
  UNIQUE (source_url) cũ vỡ ngay trong một response.
- length_report: nguồn phát 6 (bán niên) và 9 (9 tháng) ở getFinancialReports — 28/307 dòng trên
  4 mã — nới cho financial_report_file và corporate_event (getCorporateEarning cùng họ, chưa phát
  nhưng không có gì chặn). Viết IN (...) chứ không BETWEEN: 7, 8 chưa ai thấy, dải liền sẽ lọt.
- financial_statement GIỮ 1–5: ba endpoint số liệu chỉ phát quarterReport 1–5 (0 dòng khác trên
  5 mã). Nếu một ngày phát 6/9, normalize xếp bad_shape và guard báo — không lặng lẽ nạp dòng bán
  niên làm sai mọi phép cộng quý.
- ops.fundamentals_check: sổ kiểm cùng hình với ops.snapshot_check (0016).
- `downgrade()` sẽ VỠ trên một kho đã có dữ liệu thật: `source_url` trùng (BID/BAB, xem trên) khiến
  không thể thêm lại UNIQUE (source_url), và mọi dòng `length_report` 6/9 khiến không thể thêm lại
  CHECK (length_report BETWEEN 1 AND 5) — chỉ downgrade trên kho rỗng hoặc vừa reset.

Revision ID: 0017
Revises: 0016
Create Date: 2026-09-04
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0017"
down_revision: Union[str, None] = "0016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE market.financial_report_file ADD COLUMN source_id bigint;
        UPDATE market.financial_report_file SET source_id = file_id WHERE source_id IS NULL;
        ALTER TABLE market.financial_report_file
          ALTER COLUMN source_id SET NOT NULL,
          ADD CONSTRAINT financial_report_file_source_id_key UNIQUE (source_id),
          DROP CONSTRAINT financial_report_file_source_url_key,
          DROP CONSTRAINT financial_report_file_length_report_check,
          ADD CONSTRAINT financial_report_file_length_report_check
              CHECK (length_report IN (1,2,3,4,5,6,9));   -- 1-4 quý · 5 năm · 6 bán niên · 9 chín tháng
        ALTER TABLE market.corporate_event
          DROP CONSTRAINT corporate_event_length_report_check,
          ADD CONSTRAINT corporate_event_length_report_check
              CHECK (length_report IN (1,2,3,4,5,6,9));

        CREATE TABLE ops.fundamentals_check (
          issuer_id    bigint NOT NULL REFERENCES market.issuer,
          kind         text   NOT NULL CHECK (kind IN ('bs','is','cf','reports')),
          checked_at   timestamptz NOT NULL,
          payload_hash text   NOT NULL,      -- sha256 của TOÀN BỘ dòng đã chuẩn hoá (không tập trắng)
          changed_at   timestamptz,          -- lần đầu kiểm cũng tính là đổi — không NULL trong thực tế
          found_by     text   NOT NULL CHECK (found_by IN ('event','floor')),
          PRIMARY KEY (issuer_id, kind)
        );
        CREATE INDEX ON ops.fundamentals_check (kind, checked_at);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE ops.fundamentals_check;
        ALTER TABLE market.corporate_event
          DROP CONSTRAINT corporate_event_length_report_check,
          ADD CONSTRAINT corporate_event_length_report_check CHECK (length_report BETWEEN 1 AND 5);
        ALTER TABLE market.financial_report_file
          DROP CONSTRAINT financial_report_file_length_report_check,
          ADD CONSTRAINT financial_report_file_length_report_check CHECK (length_report BETWEEN 1 AND 5),
          ADD CONSTRAINT financial_report_file_source_url_key UNIQUE (source_url),
          DROP CONSTRAINT financial_report_file_source_id_key,
          DROP COLUMN source_id;
        """
    )
