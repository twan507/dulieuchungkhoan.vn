"""market data tables

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-25

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE market.price_daily (
          security_id   bigint NOT NULL REFERENCES market.security,
          trading_date  date   NOT NULL,
          close_adj     numeric,        -- giá ĐÃ điều chỉnh (nguồn tự điều chỉnh khi có sự kiện quyền)
          close_raw     numeric,        -- giá THÔ khớp sàn — sự thật lịch sử, KHÔNG BAO GIỜ sửa;
                                        -- NULL với backfill (quá khứ không có giá thô ở nguồn nào)
          open_value    numeric,
          highest_value numeric,
          lowest_value  numeric,
                                        -- ⚠️ O/H/L theo nền ĐÃ điều chỉnh (cùng nền close_adj)
          -- ⚠️ 34 cột này theo nền giá THÔ của BVSC (khớp close_raw) — KHÁC nền đã-điều-chỉnh của
          -- open_value/highest_value/lowest_value ở trên (bẫy trộn hai nền giá — step-03 M10).
          -- 34 cột dưới sinh bởi database/gen_price_columns.py từ market-field-selection.json
          -- (keep & nguon_chuan=BVSC) — không sửa tay:
          close_price numeric,
          ceiling numeric,
          floor numeric,
          reference numeric,
          open numeric,
          high numeric,
          low numeric,
          average_price numeric,
          prior_price numeric,
          total_trading numeric,
          total_trading_value numeric,
          close_vol numeric,
          bid_price1 numeric,
          bid_price2 numeric,
          bid_price3 numeric,
          bid_vol1 numeric,
          bid_vol2 numeric,
          bid_vol3 numeric,
          offer_price1 numeric,
          offer_price2 numeric,
          offer_price3 numeric,
          offer_vol1 numeric,
          offer_vol2 numeric,
          offer_vol3 numeric,
          total_bid_qtty numeric,
          total_offer_qtty numeric,
          foreign_buy numeric,
          foreign_sell numeric,
          foreign_remain numeric,
          foreign_room numeric,
          pt_match_qtty numeric,
          pt_match_price numeric,
          pt_total_traded_qtty numeric,
          pt_total_traded_value numeric,
          raw           jsonb NOT NULL DEFAULT '{}',
                        -- payload gốc KHOÁ THEO ADAPTER: {"fiintrade": {"fetched_at":…, "payload":…}, …}
                        -- hai writer (close_adj ← getPriceData, close_raw ← datafeed EOD) chỉ merge
                        -- khoá của mình, không đè khoá của writer kia
          ingested_at   timestamptz NOT NULL DEFAULT now(),
          PRIMARY KEY (security_id, trading_date)
        );
        CREATE INDEX ON market.price_daily (trading_date);

        CREATE VIEW market.price_factor AS
        SELECT security_id, trading_date,
               close_adj / NULLIF(close_raw, 0) AS factor
        FROM market.price_daily;

        CREATE TABLE market.financial_statement (
          issuer_id      bigint   NOT NULL REFERENCES market.issuer,
          year_report    smallint NOT NULL,
          length_report  smallint NOT NULL CHECK (length_report BETWEEN 1 AND 5),  -- 1..4 quý, 5 cả năm
          statement_type text     NOT NULL CHECK (statement_type IN ('BS','IS','CF','NO')),
          metric_code    text     NOT NULL,   -- mã chỉ tiêu (chữ thường): bsa1, isa22, cfa18…
          canonical_code text,                -- mã chuẩn của mình — điền dần, NULL không chặn
          value          numeric,
          ingested_at    timestamptz NOT NULL DEFAULT now(),
          PRIMARY KEY (issuer_id, year_report, length_report, statement_type, metric_code)
        );
        CREATE INDEX ON market.financial_statement (metric_code, year_report, length_report);

        CREATE TABLE market.metric_dictionary (
          dictionary text NOT NULL CHECK (dictionary IN ('screener_params','field_dictionary')),
          code       text NOT NULL,
          name_vi    text,
          name_en    text,
          unit       text,                    -- don_vi_du_lieu — KHÔNG phải nhãn unit của API
          value_min  numeric,
          value_max  numeric,
          PRIMARY KEY (dictionary, code)
        );

        CREATE TABLE market.metric_mapping (
          source         text NOT NULL,
          vendor_code    text NOT NULL,
          canonical_code text NOT NULL,
          name_vi        text,
          unit           text,
          PRIMARY KEY (source, vendor_code)
        );

        CREATE TABLE market.snapshot_daily (
          issuer_id    bigint NOT NULL REFERENCES market.issuer,
          trading_date date   NOT NULL,
          kind         text   NOT NULL CHECK (kind IN
                       ('snapshot','company_score','valuation','rate_indicator','ownership','dividend')),
          payload      jsonb  NOT NULL,
          ingested_at  timestamptz NOT NULL DEFAULT now(),
          PRIMARY KEY (issuer_id, trading_date, kind)
        );
        CREATE INDEX ON market.snapshot_daily (trading_date);

        CREATE TABLE market.screener_daily (
          security_id  bigint NOT NULL REFERENCES market.security,
          trading_date date   NOT NULL,
          payload      jsonb  NOT NULL,
          ingested_at  timestamptz NOT NULL DEFAULT now(),
          PRIMARY KEY (security_id, trading_date)
        );
        CREATE INDEX ON market.screener_daily (trading_date);

        CREATE TABLE market.index_stat_daily (
          security_id  bigint NOT NULL REFERENCES market.security,
          trading_date date   NOT NULL,
          payload      jsonb  NOT NULL DEFAULT '{}',
          ingested_at  timestamptz NOT NULL DEFAULT now(),
          PRIMARY KEY (security_id, trading_date)
        );
        CREATE INDEX ON market.index_stat_daily (trading_date);

        CREATE TABLE market.index_contribution_daily (
          index_security_id bigint NOT NULL REFERENCES market.security,
          security_id       bigint NOT NULL REFERENCES market.security,
          trading_date      date   NOT NULL,
          payload           jsonb  NOT NULL,
          ingested_at       timestamptz NOT NULL DEFAULT now(),
          PRIMARY KEY (index_security_id, security_id, trading_date)
        );

        CREATE TABLE market.corporate_event (
          event_id      bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
          event_type    text NOT NULL CHECK (event_type IN
                        ('AGM','CashDividend','StockDividend','Earning','IPO','ShareIssuance')),
          issuer_id     bigint NOT NULL REFERENCES market.issuer,
          public_date   date,
          exright_date  date,               -- kích hoạt re-crawl giá của mã thuộc issuer này
          record_date   date,
          payout_date   date,
          year_report   smallint,           -- CHỈ Earning: kỳ báo cáo — phần khoá tự nhiên
          length_report smallint CHECK (length_report BETWEEN 1 AND 5),
          stage_key     text,               -- phân định đợt (CashDividend/StockDividend/ShareIssuance)
          payload       jsonb NOT NULL,
          source_url    text,
          ingested_at   timestamptz NOT NULL DEFAULT now()
        );
        CREATE UNIQUE INDEX corporate_event_natural_key ON market.corporate_event
          (event_type, issuer_id,
           coalesce(public_date,   '1900-01-01'),
           coalesce(exright_date,  '1900-01-01'),
           coalesce(year_report,   0),
           coalesce(length_report, 0),
           coalesce(stage_key,     ''));
        CREATE INDEX ON market.corporate_event (issuer_id, exright_date);

        CREATE TABLE market.financial_report_file (
          file_id       bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
          issuer_id     bigint NOT NULL REFERENCES market.issuer,
          year_report   smallint,
          length_report smallint CHECK (length_report BETWEEN 1 AND 5),
          title         text,
          source_url    text NOT NULL UNIQUE,
          ingested_at   timestamptz NOT NULL DEFAULT now()
        );
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE market.financial_report_file;
        DROP TABLE market.corporate_event;
        DROP TABLE market.index_contribution_daily;
        DROP TABLE market.index_stat_daily;
        DROP TABLE market.screener_daily;
        DROP TABLE market.snapshot_daily;
        DROP TABLE market.metric_mapping;
        DROP TABLE market.metric_dictionary;
        DROP TABLE market.financial_statement;
        DROP VIEW market.price_factor;
        DROP TABLE market.price_daily;
        """
    )
