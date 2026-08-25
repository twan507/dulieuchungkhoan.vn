"""seed industry tree

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-25

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        -- Seed cây ngành riêng 6 nhóm x 24 ngành — nội dung chép nguyên văn từ
        -- docs/20-design/industry-tree.md §2 (chủ sở hữu nội dung duy nhất).
        INSERT INTO market.industry (code, name_vi, parent_id, level, sort_order) VALUES
         ('TAICHINH','Dịch vụ Tài chính',NULL,1,1), ('BATDONGSAN','Bất động sản và Xây dựng',NULL,1,2),
         ('SANXUAT','Sản xuất Công nghiệp',NULL,1,3), ('XUATKHAU','Xuất khẩu Chủ lực',NULL,1,4),
         ('TIEUDUNG','Tiêu dùng Đời sống',NULL,1,5), ('NANGLUONG','Năng lượng và Hạ tầng',NULL,1,6);

        INSERT INTO market.industry (code, name_vi, parent_id, level, sort_order)
        SELECT v.code, v.name_vi, p.industry_id, 2, v.ord
        FROM (VALUES
         ('NGANHANG','Ngân hàng và Tín dụng','TAICHINH',1), ('CHUNGKHOAN','Công ty Chứng khoán','TAICHINH',2),
         ('BAOHIEM','Kinh doanh Bảo hiểm','TAICHINH',3),
         ('BDS','Bất động sản Dân dụng','BATDONGSAN',1), ('KCN','Bất động sản Khu công nghiệp','BATDONGSAN',2),
         ('XAYDUNG','Thi công Xây dựng','BATDONGSAN',3), ('VLXD','Vật liệu Xây dựng','BATDONGSAN',4),
         ('KIMLOAI','Kim loại Công nghiệp','SANXUAT',1), ('TAINGUYEN','Tài nguyên Cơ bản','SANXUAT',2),
         ('HOACHAT','Hóa chất và Phân bón','SANXUAT',3), ('NHUA','Nhựa và Bao bì','SANXUAT',4),
         ('THIETBI','Thiết bị Điện và Máy móc','SANXUAT',5),
         ('NONGNGHIEP','Nông nghiệp và Chăn nuôi','XUATKHAU',1), ('THUYSAN','Chế biến Thủy sản','XUATKHAU',2),
         ('DETMAY','Dệt may và Gia dụng','XUATKHAU',3), ('CAOSU','Cao su và Săm lốp','XUATKHAU',4),
         ('BANLE','Bán buôn và Bán lẻ','TIEUDUNG',1), ('THUCPHAM','Thực phẩm và Đồ uống','TIEUDUNG',2),
         ('DULICH','Hàng không, Du lịch và Giải trí','TIEUDUNG',3), ('YTEGD','Dược phẩm, Y tế và Giáo dục','TIEUDUNG',4),
         ('DIENNUOC','Điện, Nước và Khí đốt','NANGLUONG',1), ('DAUKHI','Dầu khí và Nhiên liệu','NANGLUONG',2),
         ('VANTAI','Vận tải, Cảng biển và Kho bãi','NANGLUONG',3), ('CONGNGHE','Công nghệ Thông tin và Viễn thông','NANGLUONG',4)
        ) AS v(code, name_vi, parent_code, ord)
        JOIN market.industry p ON p.code = v.parent_code;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM market.industry_icb_map;
        DELETE FROM market.industry;
        """
    )
