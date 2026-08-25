"""staging landing zone and ops tables

Revision ID: 0008
Revises: 0007
Create Date: 2026-08-25

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE staging.raw_payload (
          payload_id   bigint generated always as identity PRIMARY KEY,
          source       text NOT NULL,            -- 'wichart' | 'sbv' | 'fred' | 'lbma' | 'binance' | 'yahoo'…
          endpoint_key text NOT NULL,            -- định danh lời gọi: key/series/URL
          fetched_at   timestamptz NOT NULL DEFAULT now(),
          content_type text NOT NULL CHECK (content_type IN ('json','html','text')),
          payload      jsonb,                    -- json → payload; html/text → body
          body         text,
          meta         jsonb,                    -- HTTP status, độ dài…; khoá 'hash' giữ hash nội dung
                                                 -- cho chính sách "lưu khi đổi" (khoá đặt tên cố định)
          CHECK ( (content_type = 'json' AND payload IS NOT NULL AND body IS NULL)
               OR (content_type IN ('html','text') AND body IS NOT NULL AND payload IS NULL) )
          -- Review vòng 2, M5: CHECK cũ (payload OR body) cho phép content_type='json' mà chỉ có body.
        );
        CREATE INDEX ON staging.raw_payload (source, endpoint_key, fetched_at);

        CREATE TABLE ops.data_domain_state (      -- CÔNG TẮC miền × nguồn: "phần thiếu kệ nó, phần đủ cứ chạy"
          domain          text NOT NULL CHECK (domain IN
                            ('market.reference','market.price','market.fundamentals',
                             'market.events','market.scores','market.index_stat',
                             'macro.indicator','macro.omo','asset','news')),
                          -- danh sách ĐÓNG do mình định nghĩa → CHECK theo quy ước bước 1 §3
                          -- (vòng 3, M-8; 'market.scores' = snapshot/screener — tầng C "mất là mất")
          source          text NOT NULL,
          status          text NOT NULL CHECK (status IN ('active','frozen','migrating')),
          last_success_at timestamptz,
          watermark       text,                   -- điểm đã nạp tới (ngày/trang/id — tuỳ miền)
          note            text,
          PRIMARY KEY (domain, source)
        );

        CREATE TABLE ops.contract_snapshot (      -- giám sát hợp đồng dữ liệu — nguồn không có versioning
          endpoint       text NOT NULL,
          checked_at     timestamptz NOT NULL DEFAULT now(),
          field_set_hash text,                    -- hash danh sách trường đã sắp — trường biến mất/mới là biết
          field_types    jsonb,                   -- tên trường → kiểu (số thành chuỗi là biết)
          record_count   int,
          coverage_pct   numeric,                 -- độ phủ trên bộ mã mẫu cố định 51 mã
          p95_latency_ms int,
          sample_payload jsonb,
          PRIMARY KEY (endpoint, checked_at)
        );

        CREATE TABLE ops.series_health (          -- độ tươi Ở CẤP SERIES — vòng 3, B7-2: contract_snapshot
          source       text NOT NULL,             -- theo endpoint KHÔNG bắt được kiểu chết-từng-series
          external_key text NOT NULL,             -- (xang_dau sống mà RON 95 chết 76 ngày; be_tong_mac_300
          external_sub text NOT NULL DEFAULT '',  --  có điểm mới hằng tháng nhưng giá đứng 407 ngày)
          checked_at   timestamptz NOT NULL DEFAULT now(),
          last_obs_date     date,
          days_since_change smallint,             -- giá đứng bao nhiêu ngày (bắt carry-forward/đóng băng)
          gap_median_days   numeric,              -- so với freq khai để bắt FREQMIS
          source_last_updated timestamptz,        -- dấu thời gian NGUỒN TỰ KHAI (FRED last_updated) —
                                                  -- so với lần check trước để bắt vá-hồi-tố-im-lặng
                                                  -- ("last_updated đổi mà giá trị cũ cũng đổi" — fred.md
                                                  --  §8; vòng 4, F12)
          note         text,
          PRIMARY KEY (source, external_key, external_sub, checked_at)
        );

        CREATE TABLE ops.source_build (           -- hash bundle JS của nguồn — cảnh báo sớm "họ vừa deploy"
          source      text NOT NULL,              -- (P3, §7.1 kho dữ liệu). Bảng riêng vì nhét vào
          checked_at  timestamptz NOT NULL DEFAULT now(),  -- contract_snapshot.field_set_hash là phá nghĩa
          bundle_hash text NOT NULL,              -- cột đó (vòng 3, B7-1). Baseline: BVSC '3241ea7a',
          urls        jsonb,                      -- FiinTrade '2.d5375412'/'main.876ed868' (đo 2026-08-15)
          PRIMARY KEY (source, checked_at)
        );

        CREATE TABLE ops.etl_run (                -- nhật ký từng lần chạy job
          run_id      bigint generated always as identity PRIMARY KEY,
          job         text NOT NULL,              -- 'market.price_daily' | 'macro.omo_crawl'…
          started_at  timestamptz NOT NULL DEFAULT now(),
          finished_at timestamptz,
          status      text NOT NULL DEFAULT 'running' CHECK (status IN ('running','success','failed')),
          stats       jsonb,                      -- số dòng ghi, số lời gọi, dải ngày…
          error       text
        );
        CREATE INDEX ON ops.etl_run (job, started_at DESC);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE ops.etl_run;
        DROP TABLE ops.source_build;
        DROP TABLE ops.series_health;
        DROP TABLE ops.contract_snapshot;
        DROP TABLE ops.data_domain_state;
        DROP TABLE staging.raw_payload;
        """
    )
