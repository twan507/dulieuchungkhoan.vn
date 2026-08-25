"""asset registry and observations (fx as asset class)

Revision ID: 0006
Revises: 0005
Create Date: 2026-08-25

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE asset.asset (
          asset_id       bigint generated always as identity PRIMARY KEY,
          code           text NOT NULL UNIQUE,   -- mã của MÌNH: 'wti', 'gold.intl', 'gold.lbma',
                                                 -- 'gold.sjc_buy'/'gold.sjc_sell', 'paxg', 'btc', 'sp500',
                                                 -- 'dxy.ice', 'fx.usd_eur', 'thep_hrc'…
          name_vi        text NOT NULL,
          asset_class    text NOT NULL CHECK (asset_class IN ('commodity','crypto','index','fund','fx')),
                                                 -- 'fx' thêm, 'rate' bỏ (lãi suất/lợi suất thuộc macro —
                                                 --  luật phân miền bước 4 §0; review vòng 2, I2/I3)
          quote_currency text NOT NULL,          -- 'USD' | 'USDT' | 'VND' | 'GBp'… — KHÔNG suy đoán,
                                                 -- đọc từ nguồn (bẫy đã đo: USX = cent Mỹ, GBp = pence)
          unit           text,                   -- 'USD/thùng', 'USD/oz', 'VND/lượng', 'điểm', 'EUR/1 USD'…
          calendar       text NOT NULL DEFAULT 'trading_days'
                         CHECK (calendar IN ('trading_days','24x7')),
                                                 -- lịch của CHUỖI — không suy được từ obs_date: một số
                                                 -- chuỗi phiên có điểm cuối tuần carry-forward (vàng
                                                 -- WiChart 36,8% ngày đứng giá) — review vòng 2, M11
          region         text,
          notes          text
        );

        CREATE TABLE asset.asset_external_id (   -- Ổ CẮM nguồn
          asset_id      bigint NOT NULL REFERENCES asset.asset,
          source        text NOT NULL,           -- 'wichart' | 'fred' | 'yahoo' | 'lbma' | 'binance'
          external_code text NOT NULL,           -- 'dau_wti' | 'DCOILWTICO' | '^GSPC' | 'PAXGUSDT'…
          external_sub  text NOT NULL DEFAULT '',-- series trong document đa chuỗi — WiChart một key chứa
                                                 -- nhiều series ('xang_dau' 4 loại xăng, 'vang' giá mua/bán),
                                                 -- trỏ theo VỊ TRÍ như macro.indicator_source
                                                 -- (review 2026-08-25 — trước đó thiếu, ổ cắm không đủ chân)
          scale         numeric NOT NULL DEFAULT 1,   -- hệ số đơn vị hardcode — lỗi nhãn 1000× của WiChart
                                                      -- nằm CHỦ YẾU ở nhóm hàng hoá (vang ×1e3, xang_dau
                                                      -- ×1e3, U1000…) — review vòng 2, I1
          active        boolean NOT NULL DEFAULT true,-- series chết/đóng băng ở nguồn (thiec DEAD,
                                                      -- ca_tra FROZEN, RON 95 SUBDEAD…)
          price_type    text,                         -- chuỗi này đổ vào price_type nào (spot/futures/
                                                      -- fixing/close) — neo ở registry để hai nguồn cùng
                                                      -- price_type không đè nhau lặng lẽ khi migrating
          meta          jsonb,                        -- múi giờ sàn, firstTradeDate, quoteType, mốc chốt…
          PRIMARY KEY (source, external_code, external_sub),
          UNIQUE (asset_id, source)
        );

        CREATE TABLE asset.price_daily (         -- giá trị ĐƠN theo ngày: hàng hoá, fixing, NAV quỹ
          asset_id    bigint NOT NULL REFERENCES asset.asset,
          obs_date    date   NOT NULL,
          price_type  text   NOT NULL CHECK (price_type IN ('spot','futures','fixing','close')),
          value       numeric NOT NULL,
          ingested_at timestamptz NOT NULL DEFAULT now(),
          PRIMARY KEY (asset_id, obs_date, price_type)
        );

        CREATE TABLE asset.ohlc_daily (          -- nến ngày: chỉ số quốc tế (Yahoo), crypto (Binance)
          asset_id    bigint NOT NULL REFERENCES asset.asset,
          obs_date    date   NOT NULL,           -- Binance: từ thời điểm MỞ nến, epoch ms UTC → date UTC
          open numeric, high numeric, low numeric, close numeric,
          close_adj   numeric,                   -- Yahoo adjclose — nguồn đổi hồi tố, UPSERT
          volume      numeric,
          ingested_at timestamptz NOT NULL DEFAULT now(),
          PRIMARY KEY (asset_id, obs_date)
        );
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE asset.price_daily;
        DROP TABLE asset.ohlc_daily;
        DROP TABLE asset.asset_external_id;
        DROP TABLE asset.asset;
        """
    )
