"""macro indicators, spliced view, OMO cluster

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-25

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE macro.indicator (
          indicator_id bigint generated always as identity PRIMARY KEY,
          code         text NOT NULL UNIQUE,     -- mã của MÌNH: 'vn.cpi', 'vn.gdp', 'us.fedfunds', 'us.cpi'…
          name_vi      text NOT NULL,
          name_en      text,
          unit         text NOT NULL,            -- đơn vị GỐC sau chuẩn hoá: 'VND', 'USD', '%', 'nghin_nguoi'…
          freq         text NOT NULL CHECK (freq IN ('d','w','m','q','y')),
          region       text NOT NULL CHECK (region IN ('vn','us','global')),
          role         text NOT NULL DEFAULT 'data' CHECK (role IN ('data','growth_ref')),
          notes        text
        );
        -- role='growth_ref': series "Tăng trưởng" của WiChart không bị loại — nguyên liệu để tính
        -- factor nối đứt gãy và giám sát phát hiện break mới; vẫn nạp observation như thường,
        -- tầng đọc/API chỉ phơi role='data'.

        CREATE TABLE macro.indicator_source (     -- Ổ CẮM: tháo lắp nguồn tại đây
          indicator_id bigint NOT NULL REFERENCES macro.indicator,
          source       text NOT NULL,             -- 'wichart' | 'fred' | 'sbv'
          external_key text NOT NULL,             -- WiChart key ('cpi') / FRED series_id ('CPIAUCSL')
          external_sub text NOT NULL DEFAULT '',  -- series_idx WiChart — theo VỊ TRÍ, không theo tên
          scale        numeric NOT NULL DEFAULT 1,-- hệ số đơn vị hardcode, ETL nhân trước khi ghi
          active       boolean NOT NULL DEFAULT true,  -- false = series chết/đóng băng ở nguồn
          meta         jsonb,                     -- tier, lag, freq khai vs freq thật, cờ đặc thù nguồn
          PRIMARY KEY (source, external_key, external_sub),
          UNIQUE (indicator_id, source)
        );

        CREATE TABLE macro.observation (
          indicator_id bigint NOT NULL REFERENCES macro.indicator,
          obs_date     date   NOT NULL,           -- NGÀY ĐẦU KỲ (quy ước §2.1 step-04)
          value        numeric NOT NULL,          -- NHƯ NGUỒN CÔNG BỐ (sau chuẩn hoá đơn vị) — KHÔNG splice
          ingested_at  timestamptz NOT NULL DEFAULT now(),
          PRIMARY KEY (indicator_id, obs_date)
        );
        -- Giá trị thiếu = KHÔNG CÓ DÒNG (FRED trả "." thì bỏ qua), không chèn NULL.

        CREATE TABLE macro.series_break (         -- sổ đăng ký đứt gãy cấu trúc (vd đổi năm gốc GDP)
          indicator_id bigint NOT NULL REFERENCES macro.indicator,
          break_date   date   NOT NULL,           -- điểm ĐẦU TIÊN thuộc nền mới
          factor       numeric NOT NULL CHECK (factor > 0),  -- nhân đoạn CŨ với hệ số này để nối
          reason       text NOT NULL,
          verified_by  text, verified_at timestamptz,
          PRIMARY KEY (indicator_id, break_date)
        );

        CREATE VIEW macro.observation_spliced AS  -- chuỗi ĐÃ NỐI — tính lúc đọc, không lưu
        SELECT o.indicator_id, o.obs_date,
               o.value * coalesce((SELECT exp(sum(ln(b.factor)))
                                   FROM macro.series_break b
                                   WHERE b.indicator_id = o.indicator_id
                                     AND b.break_date  > o.obs_date), 1) AS value_spliced,
               o.value AS value_as_published
        FROM macro.observation o;

        CREATE TABLE macro.omo_session (          -- mỗi phiên ĐÃ CRAWL một dòng
          session_date      date PRIMARY KEY,     -- lấy từ TIÊU ĐỀ bài của SBV, cấm lấy ngày hệ thống
          crawled_at        timestamptz NOT NULL,
          has_reverse_repo  boolean NOT NULL,     -- có nhóm "Mua kỳ hạn"  (bơm có kỳ hạn)
          has_repo          boolean NOT NULL,     -- có nhóm "Bán kỳ hạn"  (hút có kỳ hạn)
          has_outright_sale boolean NOT NULL,     -- có nhóm "Bán hẳn"     (hút, tín phiếu)
          note              text
        );
        -- Vắng nhóm là DỮ KIỆN: cờ false ghi nhận SBV không mở nhóm đó hôm nay, khác "chưa crawl"
        -- (không có dòng).

        CREATE TABLE macro.omo_auction (          -- kết quả: một dòng = (phiên × loại hình × kỳ hạn)
          session_date  date NOT NULL REFERENCES macro.omo_session,
          op_type       text NOT NULL CHECK (op_type IN ('reverse_repo','repo','outright_sale')),
          tenor_days    smallint NOT NULL,        -- 7|14|21|28|35|56|63|91|140
          participants  smallint,                 -- số thành viên tham gia
          winners       smallint,                 -- số trúng thầu
          volume_vnd    numeric NOT NULL,         -- VND ĐƠN VỊ GỐC — nguồn công bố tỷ VND, ETL nhân 1e9
                                                  -- tại cổng ('6.307,47' tỷ → 6.30747e12)
          rate_pct      numeric,                  -- %/năm
          ingested_at   timestamptz NOT NULL DEFAULT now(),
          PRIMARY KEY (session_date, op_type, tenor_days)
        );

        CREATE TABLE macro.omo_flow (             -- TỰ DỰNG toàn phần từ omo_auction
          flow_date       date PRIMARY KEY,
          injection_vnd   numeric NOT NULL,       -- bơm trong ngày (VND)
          maturing_vnd    numeric NOT NULL,       -- đáo hạn: phiên (D−k, kỳ hạn k) đến hạn tại D
          net_vnd         numeric NOT NULL,       -- ròng = bơm − đáo hạn (dương = bơm ròng)
          outstanding_vnd numeric,                -- đang lưu hành (cộng dồn)
          complete        boolean NOT NULL DEFAULT false
        );
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE macro.omo_flow;
        DROP TABLE macro.omo_auction;
        DROP TABLE macro.omo_session;
        DROP VIEW macro.observation_spliced;
        DROP TABLE macro.series_break;
        DROP TABLE macro.observation;
        DROP TABLE macro.indicator_source;
        DROP TABLE macro.indicator;
        """
    )
