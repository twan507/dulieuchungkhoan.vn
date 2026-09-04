"""ops.snapshot_check + domain market.snapshot

Sổ kiểm của họ Snapshot (lát 4). Bảng TRẠNG THÁI HIỆN TẠI, một dòng mỗi
(issuer, kind) — 6.092 dòng đứng yên, không phình:

  - cấp danh sách tới hạn cho job (ORDER BY checked_at NULLS FIRST),
  - và là thước đo lỗ của lịch sự kiện: đổi mà found_by='floor' nghĩa là
    lịch sự kiện KHÔNG bắn cho thay đổi đó.

Lịch sử nội dung nằm ở market.snapshot_daily; lịch sử phép đếm nằm ở
ops.etl_run.stats. Không dựng bảng lịch sử thứ ba.

Domain 'market.snapshot' thêm vào CHECK vì lát 1 (screener) đã chiếm
('market.scores','fiintrade'); dùng chung thì hai job đè watermark của nhau.

Revision ID: 0016
Revises: 0015
Create Date: 2026-09-04

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0016"
down_revision: Union[str, None] = "0015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE ops.snapshot_check (
          issuer_id  bigint NOT NULL REFERENCES market.issuer,
          kind       text   NOT NULL CHECK (kind IN
                       ('snapshot','valuation','ownership','dividend')),
          checked_at timestamptz NOT NULL,
          keep_hash  text   NOT NULL,       -- sha256 của TẬP TRẮNG, không phải payload trọn
          changed_at timestamptz,           -- lần nội dung đổi gần nhất. Lần kiểm ĐẦU TIÊN của
                                             -- một (issuer, kind) tính là một lần đổi thật (so
                                             -- với "chưa từng kiểm"), nên apply() luôn set giá
                                             -- trị này ngay từ đầu — NULL không xảy ra trong
                                             -- thực tế, không phải "chưa đổi lần nào"
          found_by   text   NOT NULL CHECK (found_by IN ('event','floor')),
          PRIMARY KEY (issuer_id, kind)
        );
        CREATE INDEX ON ops.snapshot_check (kind, checked_at);

        ALTER TABLE ops.data_domain_state DROP CONSTRAINT data_domain_state_domain_check;
        ALTER TABLE ops.data_domain_state ADD CONSTRAINT data_domain_state_domain_check
          CHECK (domain IN ('market.reference','market.price','market.fundamentals',
                            'market.events','market.scores','market.index_stat',
                            'macro.indicator','macro.omo','asset','news',
                            'market.snapshot'));
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM ops.data_domain_state WHERE domain = 'market.snapshot';
        ALTER TABLE ops.data_domain_state DROP CONSTRAINT data_domain_state_domain_check;
        ALTER TABLE ops.data_domain_state ADD CONSTRAINT data_domain_state_domain_check
          CHECK (domain IN ('market.reference','market.price','market.fundamentals',
                            'market.events','market.scores','market.index_stat',
                            'macro.indicator','macro.omo','asset','news'));
        DROP TABLE ops.snapshot_check;
        """
    )
