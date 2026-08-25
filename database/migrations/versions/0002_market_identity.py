"""market identity tables

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-25

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE market.industry (            -- bộ ngành RIÊNG — nội dung: docs/20-design/industry-tree.md
          industry_id  bigint generated always as identity PRIMARY KEY,
          code         text NOT NULL UNIQUE,      -- viết hoa không dấu: 'TAICHINH', 'NGANHANG' (luật đặt tên §3 industry-tree)
          name_vi      text NOT NULL,             -- 'Ngân hàng và Tín dụng'
          parent_id    bigint REFERENCES market.industry,
          level        smallint NOT NULL CHECK (level IN (1,2)),  -- cây đã chốt 2 CẤP: 6 nhóm × 24 ngành
          sort_order   smallint,
          CHECK ((level = 1) = (parent_id IS NULL))  -- nhóm không có cha, ngành bắt buộc có cha
        );
        -- Level 1 chỉ phục vụ điều hướng web; chỉ số phân tích (dòng tiền, breadth, xếp hạng)
        -- đọc ở level 2 — cấp có "sóng ngành" thật (industry-tree §1). Không tính chỉ số tổng hợp level 1.
        -- SEED: nạp từ industry-tree.md (chủ sở hữu nội dung duy nhất) trong migration seed;
        -- test đối chiếu bảng sau seed với file (6 + 24 code) để hai bản không trôi lệch.

        CREATE TABLE market.industry_icb_map (    -- ICB (nguồn) → ngành riêng: gán hàng loạt
          icb_code    text PRIMARY KEY,           -- + tự gán mã mới niêm yết
          industry_id bigint NOT NULL REFERENCES market.industry
        );
        -- LUẬT PHÂN GIẢI (review vòng 2, I10): map đăng ký ở CẤP NHÁNH ICB, còn issuer mang mã LÁ
        -- (cấp 4) — hai cấp không join thẳng được. Thứ tự tra: khớp icb_code chính xác trước;
        -- không có thì leo icb_code_path ('8000/8300/8350') lấy TỔ TIÊN GẦN NHẤT có trong map.
        -- Mã ICB lạ chưa có trong cây → industry_id để NULL + cảnh báo, không chặn job.

        CREATE TABLE market.icb_industry (        -- cây ICB của nguồn — CHỈ THAM KHẢO
          icb_code        text PRIMARY KEY,
          icb_name        text,
          parent_icb_code text,
          icb_level       smallint,               -- 1..4
          icb_code_path   text                    -- '8000/8300/8350'
        );

        CREATE TABLE market.issuer (
          issuer_id     bigint generated always as identity PRIMARY KEY,
          name          text NOT NULL,
          short_name    text,
          com_type_code text,                     -- NH|CT|CK|BH|QU — quyết định endpoint snapshot
          industry_id   bigint REFERENCES market.industry,  -- MỖI DOANH NGHIỆP 1 NGÀNH, luôn là LEVEL 2
                                                            -- (nhóm suy từ cha — không gán nhóm trực tiếp)
          icb_code      text,                               -- tham khảo THUẦN, KHÔNG FK — review vòng 3 C-2:
                                                            -- FK sẽ chặn job danh bạ khi nguồn trả icbCode
                                                            -- chưa có trong cây (2 endpoint khác nhịp),
                                                            -- trái luật "mã ICB lạ không chặn job" ở trên
          updated_at    timestamptz NOT NULL DEFAULT now()
        );

        CREATE TABLE market.issuer_external_id (
          issuer_id     bigint NOT NULL REFERENCES market.issuer,
          source        text NOT NULL,            -- 'fiintrade'
          external_code text NOT NULL,            -- organ_code — 41% khác ticker, 72 mã là mã số thuế
          PRIMARY KEY (source, external_code),
          UNIQUE (issuer_id, source)
        );

        CREATE TABLE market.security (
          security_id   bigint generated always as identity PRIMARY KEY,
          ticker        text NOT NULL,            -- thuộc tính hiển thị, KHÔNG phải khoá
          exchange      text NOT NULL,            -- HOSE|HNX|UPCOM — NOT NULL vì unique một phần
                                                  -- (ticker, exchange) sẽ thủng với NULL (NULLS DISTINCT;
                                                  --  review 2026-08-25)
          security_type text NOT NULL CHECK (security_type IN ('stock','etf','index','fund_cert')),
          issuer_id     bigint REFERENCES market.issuer,    -- NULL với index
          status        text NOT NULL DEFAULT 'listed' CHECK (status IN ('listed','delisted')),
          tradelot      int,
          full_name     text,
          updated_at    timestamptz NOT NULL DEFAULT now()
        );
        CREATE UNIQUE INDEX ON market.security (ticker, exchange) WHERE status = 'listed';
        CREATE INDEX ON market.security (ticker);

        CREATE TABLE market.security_external_id (
          security_id   bigint NOT NULL REFERENCES market.security,
          source        text NOT NULL,            -- 'fiintrade'|'bvsc'|'yahoo'…
          external_code text NOT NULL,
          external_sub  text NOT NULL DEFAULT '', -- ngữ cảnh mã trong CÙNG nguồn — review vòng 3 I-3:
                                                  -- BVSC dùng HAI bộ mã chỉ số song song (TVC 'VNINDEX'
                                                  -- vs getIndexSnapshots 'HOSE'); VN-Index cần cả hai
                                                  -- dòng, đối xứng với macro/asset registry
          PRIMARY KEY (source, external_code),
          UNIQUE (security_id, source, external_sub)
        );
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE market.security_external_id;
        DROP TABLE market.security;
        DROP TABLE market.issuer_external_id;
        DROP TABLE market.issuer;
        DROP TABLE market.industry_icb_map;
        DROP TABLE market.industry;
        DROP TABLE market.icb_industry;
        """
    )
