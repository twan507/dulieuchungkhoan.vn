"""seed industry_icb_map (55) + issuer_industry_override (161)

Revision ID: 0013
Revises: 0012
Create Date: 2026-08-27

Nội dung do docs/20-design/industry-mapping.json sở hữu (sinh từ
gen_industry_mapping.py). Hai bảng này KHÔNG có đường ghi runtime nên seed ở
migration là đúng chỗ — khác market.security, nơi ETL ghi hằng ngày.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0013"
down_revision: Union[str, None] = "0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        -- LỚP 1 — 55 dòng (56 dòng worksheet trừ 8980 'Quỹ đầu tư' KHÔNG NẠP).
        -- Trộn cấp 3 (nền cả nhánh) với cấp 4 (ngoại lệ) là CỐ Ý: luật phân giải
        -- khớp chính xác trước, không có thì leo icb_code_path lấy tổ tiên gần nhất.
        INSERT INTO market.industry_icb_map (icb_code, industry_id)
        SELECT v.icb_code, i.industry_id
        FROM (VALUES
         ('0530','DAUKHI'),
         ('0570','DAUKHI'),
         ('0580','TIENICH'),
         ('1350','HOACHAT'),
         ('1353','NHUA'),
         ('1730','DETMAY'),
         ('1737','NHUA'),
         ('1750','KIMLOAI'),
         ('1770','KHOANGSAN'),
         ('2350','XAYDUNG'),
         ('2353','VATLIEU'),
         ('2710','THIETBI'),
         ('2720','NHUA'),
         ('2727','THIETBI'),
         ('2730','THIETBI'),
         ('2750','THIETBI'),
         ('2770','VANTAI'),
         ('2790','TIENICH'),
         ('2791','XAYDUNG'),
         ('2793','YTE'),
         ('2797','THIETBI'),
         ('3350','BANLE'),
         ('3355','THIETBI'),
         ('3357','CAOSU'),
         ('3530','THUCPHAM'),
         ('3570','THUCPHAM'),
         ('3573','THUYSAN'),
         ('3720','DETMAY'),
         ('3740','DETMAY'),
         ('3743','THIETBI'),
         ('3760','DETMAY'),
         ('3780','THUCPHAM'),
         ('4530','YTE'),
         ('4570','YTE'),
         ('5330','BANLE'),
         ('5370','BANLE'),
         ('5550','YTE'),
         ('5553','DULICH'),
         ('5555','DULICH'),
         ('5750','DULICH'),
         ('6530','CONGNGHE'),
         ('6570','CONGNGHE'),
         ('7530','TIENICH'),
         ('7570','TIENICH'),
         ('7573','DAUKHI'),
         ('8350','NGANHANG'),
         ('8530','BAOHIEM'),
         ('8570','BAOHIEM'),
         ('8630','DANDUNG'),
         ('8670','DANDUNG'),
         ('8770','CHUNGKHOAN'),
         ('8773','NGANHANG'),
         ('8775','NGANHANG'),
         ('9530','CONGNGHE'),
         ('9570','CONGNGHE')
        ) AS v(icb_code, industry_code)
        JOIN market.industry i ON i.code = v.industry_code AND i.level = 2;

        -- LỚP 2 — 161 dòng gán tay. Khoá theo ticker ở worksheet, đổi sang issuer_id
        -- qua market.security. Đi qua bảng tạm để chốt chặn đọc được dữ liệu trước khi ghi.
        CREATE TEMP TABLE _seed_l2 (ticker text, industry_code text, reason text) ON COMMIT DROP;
        INSERT INTO _seed_l2 (ticker, industry_code, reason) VALUES
         ('AAN','NONGNGHIEP','G3a nông nghiệp bóc khỏi 3573 sau khi đảo'),
         ('ACC','XAYDUNG','G5a xây lắp Bình Dương'),
         ('ACV','DULICH','G6 cảng hàng không tên ngành đã có Hàng không'),
         ('AFX','NONGNGHIEP','G3b B1'),
         ('AGM','NONGNGHIEP','G3b B1 lợi nhuận chạy theo giá nông sản'),
         ('AMS','XAYDUNG','G5d AMECC kết cấu thép công trình'),
         ('APC','NONGNGHIEP','G7 chiếu xạ nông sản thủy sản xuất khẩu CAN XAC NHAN'),
         ('AST','DULICH','G7 bán lẻ trong sân bay cùng luật với SCS'),
         ('BAF','NONGNGHIEP','G3a nông nghiệp bóc khỏi 3573 sau khi đảo'),
         ('BAX','KHUCONGNGHIEP','chủ KCN Bàu Xéo'),
         ('BCM','KHUCONGNGHIEP','1a cả hai cùng KCN'),
         ('BDT','XAYDUNG','G5a xây lắp Đồng Tháp'),
         ('BIG','XAYDUNG','G3a BIG Invest Group đầu tư xây dựng ICB xếp sai'),
         ('BMP','NHUA','G5d Nhựa Bình Minh chạy theo giá hạt nhựa PVC'),
         ('BRC','CAOSU','G2 cao su thiên nhiên ICB xếp nhầm 1353'),
         ('BRR','CAOSU','G2 cao su thiên nhiên ICB xếp nhầm 1353'),
         ('CCL','KHUCONGNGHIEP','1b theo chủ dự án'),
         ('CET','NONGNGHIEP','G3b B2'),
         ('CIA','DULICH','G6 dịch vụ sân bay Cam Ranh'),
         ('CIG','DANDUNG','G5b theo chủ dự án BĐS'),
         ('CMM','THUYSAN','G3a Camimex nằm ở 3577 nên vẫn cần đè'),
         ('CNA','NONGNGHIEP','G3a nông nghiệp bóc khỏi 3573 sau khi đảo'),
         ('CRE','KHUCONGNGHIEP','nguồn uy tín'),
         ('CSC','DANDUNG','G5b COTANA BĐS'),
         ('CTR','CONGNGHE','G5d Viettel Construction hạ tầng viễn thông và towerco'),
         ('CVN','XAYDUNG','G5d Vinam xây dựng dân dụng ICB xếp thiết bị y tế là sai'),
         ('D2D','KHUCONGNGHIEP','1a cả hai cùng KCN'),
         ('DBC','NONGNGHIEP','G3a nông nghiệp bóc khỏi 3573 sau khi đảo'),
         ('DCV','DANDUNG','luật BCTC CT công ty quản lý quỹ không dùng mẫu BCTC CK'),
         ('DDB','DETMAY','G5d Đông Dương sản xuất sản phẩm từ gỗ'),
         ('DDG','TIENICH','G6 tra web cung cấp hơi nhiệt điện công nghiệp và nhiên liệu biomass'),
         ('DGT','XAYDUNG','G5a công trình giao thông'),
         ('DID','XAYDUNG','G5a xây lắp họ DIC'),
         ('DLG','DANDUNG','G5b Đức Long Gia Lai holding BĐS BOT'),
         ('DMN','NONGNGHIEP','G3a nông nghiệp bóc khỏi 3573 sau khi đảo'),
         ('DPR','KHUCONGNGHIEP','1d ăn sóng BĐS KCN do chuyển đổi đất'),
         ('DQC','THIETBI','G7 Điện Quang sản xuất bóng đèn thiết bị chiếu sáng cùng luật với MBG'),
         ('DRG','CAOSU','G2 cao su thiên nhiên ICB xếp nhầm 1353'),
         ('DRH','KHUCONGNGHIEP','nguồn uy tín'),
         ('DRI','CAOSU','G2 cao su thiên nhiên ICB xếp nhầm 1353'),
         ('DTD','KHUCONGNGHIEP','1b theo chủ dự án'),
         ('DTI','DANDUNG','G8 theo chủ dự án độ tin cậy thấp'),
         ('EIN','DANDUNG','G8 theo chủ dự án độ tin cậy thấp'),
         ('F88','BANLE','luật BCTC CT chuỗi cửa hàng cầm đồ'),
         ('FID','DANDUNG','luật BCTC com_type=CT không được vào CHUNGKHOAN holding có sàn BĐS'),
         ('FIT','DANDUNG','G8 F.I.T Group holding dược nước khoáng BĐS nông nghiệp'),
         ('FOC','CONGNGHE','G8 FPT Online quảng cáo trực tuyến và nội dung số'),
         ('GEL','DANDUNG','G5d chủ dự án chốt BĐS không xếp KCN'),
         ('GPC','NONGNGHIEP','G3b B2'),
         ('GSP','DAUKHI','G6 vận tải sản phẩm khí theo luật tên dầu khí'),
         ('GVR','KHUCONGNGHIEP','1d ăn sóng BĐS KCN do chuyển đổi đất'),
         ('HAG','NONGNGHIEP','G3a nông nghiệp bóc khỏi 3573 sau khi đảo'),
         ('HAR','KHUCONGNGHIEP','1b theo chủ dự án'),
         ('HHG','VANTAI','G7 Hoàng Hà xe khách tuyến cố định cùng luật với VNS'),
         ('HHS','DANDUNG','G7 Hoàng Huy nay là BĐS Hải Phòng'),
         ('HKB','NONGNGHIEP','G3b B1'),
         ('HMR','KHOANGSAN','G5a khai thác mỏ đá cùng luật với KSB và TTZ'),
         ('HNG','NONGNGHIEP','G3a nông nghiệp bóc khỏi 3573 sau khi đảo'),
         ('HPA','NONGNGHIEP','G3a nông nghiệp bóc khỏi 3573 sau khi đảo'),
         ('HPI','KHUCONGNGHIEP','nguồn uy tín'),
         ('HRC','CAOSU','G2 cao su thiên nhiên ICB xếp nhầm 1353'),
         ('HSL','NONGNGHIEP','G3b B1'),
         ('HVA','CONGNGHE','luật BCTC CT fintech cho vay ngang hàng'),
         ('IDC','KHUCONGNGHIEP','1a cả hai cùng KCN'),
         ('IDV','KHUCONGNGHIEP','nguồn uy tín'),
         ('ILA','NONGNGHIEP','G3b B2'),
         ('IPA','DANDUNG','G5d luật BCTC com_type=CT holding mẹ của VND'),
         ('IRC','CAOSU','G2 cao su thiên nhiên ICB xếp nhầm 1353'),
         ('ITA','KHUCONGNGHIEP','nguồn uy tín'),
         ('KBC','KHUCONGNGHIEP','1a cả hai cùng KCN'),
         ('KGM','NONGNGHIEP','G3b B1'),
         ('KOS','KHUCONGNGHIEP','1b theo chủ dự án'),
         ('KPF','DANDUNG','luật BCTC com_type=CT holding đầu tư tài sản'),
         ('KSB','KHOANGSAN','G4 B mỏ đá thật'),
         ('L14','DANDUNG','G5b Licogi 14 BĐS và đầu tư'),
         ('LAI','DANDUNG','G5b theo chủ dự án'),
         ('LHG','KHUCONGNGHIEP','1a cả hai cùng KCN'),
         ('LIX','HOACHAT','G7 bột giặt thực chất là hóa chất chủ dự án chốt'),
         ('MAC','VANTAI','G6 Macstar tiền thân cung ứng dịch vụ kỹ thuật hàng hải'),
         ('MBG','THIETBI','G5d sản xuất thiết bị chiếu sáng và thiết bị điện'),
         ('MH3','KHUCONGNGHIEP','tên là KCN'),
         ('MLS','NONGNGHIEP','G3a nông nghiệp bóc khỏi 3573 sau khi đảo'),
         ('NCG','NONGNGHIEP','G3a Anova Agri là thức ăn chăn nuôi và thú y'),
         ('NDF','NONGNGHIEP','G3b B1'),
         ('NET','HOACHAT','G7 bột giặt Net cùng luật với LIX'),
         ('NHA','DANDUNG','G5b Nhà và Đô thị Nam Hà Nội'),
         ('NHV','NONGNGHIEP','G3b B3'),
         ('NSC','NONGNGHIEP','G3a nông nghiệp bóc khỏi 3573 sau khi đảo'),
         ('NSS','NONGNGHIEP','G3a nông nghiệp bóc khỏi 3573 sau khi đảo'),
         ('NTC','KHUCONGNGHIEP','nguồn uy tín'),
         ('NTL','KHUCONGNGHIEP','nguồn uy tín'),
         ('NTP','NHUA','G5d Nhựa Tiền Phong'),
         ('OCH','DULICH','G3b chủ dự án chốt One Capital Hospitality đã xoay sang khách sạn'),
         ('OGC','DANDUNG','luật BCTC CT Đại Dương BĐS và khách sạn qua OCH'),
         ('PC1','TIENICH','G5c lợi nhuận chính từ thủy điện và điện gió'),
         ('PFL','DANDUNG','G5b Dầu khí Đông Đô BĐS'),
         ('PGN','HOACHAT','G7 phụ gia nhựa là hóa chất không phải nhựa'),
         ('PGT','DANDUNG','G6 tra web nay là holding M&A BĐS khách sạn không còn taxi'),
         ('PHR','KHUCONGNGHIEP','1d ăn sóng BĐS KCN do chuyển đổi đất'),
         ('PLC','DAUKHI','G6 hóa dầu Petrolimex dầu nhờn nhựa đường'),
         ('PNJ','BANLE','G7 bán lẻ trang sức cả hai nguồn đồng ý'),
         ('PSL','NONGNGHIEP','G3a nông nghiệp bóc khỏi 3573 sau khi đảo'),
         ('PSP','DAUKHI','G6 cảng dịch vụ dầu khí'),
         ('PTB','VATLIEU','G5d Phú Tài đá granite theo chủ dự án'),
         ('PVM','DAUKHI','G6 máy thiết bị dầu khí'),
         ('PVO','DAUKHI','G6 dầu nhờn PV Oil'),
         ('PVP','DAUKHI','G6 nt'),
         ('PVT','DAUKHI','G6 nt lưu ý PVT là đội tàu chở dầu lớn nhất VN'),
         ('PVV','DAUKHI','G5d chủ dự án chốt theo tên Dầu khí'),
         ('PVX','DAUKHI','G5d chủ dự án chốt theo tên Dầu khí'),
         ('PXL','KHUCONGNGHIEP','tên là KCN'),
         ('RBC','CAOSU','G2 cao su thiên nhiên ICB xếp nhầm 1353'),
         ('RTB','CAOSU','G2 cao su thiên nhiên ICB xếp nhầm 1353'),
         ('SAS','DULICH','G7 SASCO bán lẻ sân bay Tân Sơn Nhất'),
         ('SBB','DETMAY','G3b chủ dự án chốt giữ phân loại cũ'),
         ('SBR','CAOSU','G2 cao su thiên nhiên ICB xếp nhầm 1353'),
         ('SBV','NHUA','G7 Siam Brothers dây thừng lưới đánh cá từ nhựa PP PE'),
         ('SGI','DANDUNG','G7 tra web holding sản xuất tài chính BĐS độ tin cậy thấp'),
         ('SHN','BANLE','G4 C HANIC thương mại VLXD và XNK mã than của ICB đã lỗi thời'),
         ('SIP','KHUCONGNGHIEP','1a cả hai cùng KCN'),
         ('SKG','VANTAI','G6 tàu cao tốc chở khách'),
         ('SNZ','KHUCONGNGHIEP','nguồn uy tín'),
         ('SSC','NONGNGHIEP','G3a nông nghiệp bóc khỏi 3573 sau khi đảo'),
         ('STH','BANLE','G7 theo chủ dự án độ tin cậy thấp'),
         ('SVT','THIETBI','G4 B Savitech cơ khí chế tạo xe đạp xe máy phụ tùng'),
         ('SZB','KHUCONGNGHIEP','cùng họ Sonadezi'),
         ('SZC','KHUCONGNGHIEP','1a cả hai cùng KCN'),
         ('SZG','KHUCONGNGHIEP','cùng họ Sonadezi'),
         ('SZL','KHUCONGNGHIEP','nguồn uy tín'),
         ('TAR','NONGNGHIEP','G3a nông nghiệp bóc khỏi 3573 sau khi đảo'),
         ('TCJ','NONGNGHIEP','G3a nông nghiệp bóc khỏi 3573 sau khi đảo'),
         ('TCO','VANTAI','G3a Janus Group tiền thân Vận tải Duyên Hải ICB xếp sai'),
         ('THG','XAYDUNG','G5a xây dựng Tiền Giang'),
         ('TID','KHUCONGNGHIEP','holding mẹ của TIP'),
         ('TIN','NGANHANG','luật BCTC com_type=NH lớp 1 đưa nhầm sang CHUNGKHOAN'),
         ('TIP','KHUCONGNGHIEP','1a cả hai cùng KCN'),
         ('TIX','KHUCONGNGHIEP','nguồn uy tín'),
         ('TLD','XAYDUNG','G5a xây dựng đô thị Thăng Long'),
         ('TLG','YTE','G7 Thiên Long văn phòng phẩm giáo dục cùng mùa khai giảng CAN XAC NHAN'),
         ('TNC','CAOSU','G2 cao su thiên nhiên ICB xếp nhầm 1353'),
         ('TRC','CAOSU','G2 cao su thiên nhiên ICB xếp nhầm 1353'),
         ('TT6','NONGNGHIEP','G3b B1'),
         ('TTH','BANLE','G4 D thời trang Valentino và khoáng sản ICB xếp thép là sai'),
         ('TTZ','KHOANGSAN','G5d tra web khai thác cát đá sỏi Thái Bình'),
         ('TV1','TIENICH','G5c tư vấn thiết kế công trình điện theo chu kỳ đầu tư ngành điện'),
         ('TV2','TIENICH','G5c nt'),
         ('TV3','TIENICH','G5c nt danh sách cũ ghi THIETBI có vẻ nhầm'),
         ('TVC','DANDUNG','luật BCTC CT holding T Corp'),
         ('VC3','KHUCONGNGHIEP','nguồn uy tín'),
         ('VGC','KHUCONGNGHIEP','1a cả hai cùng KCN dù ICB xếp vật liệu'),
         ('VHG','DANDUNG','G7 theo chủ dự án độ tin cậy thấp'),
         ('VIW','TIENICH','G5c VIWASEEN cấp nước'),
         ('VKC','NHUA','G2 thực chất cáp và ống nhựa không phải lốp'),
         ('VLC','NONGNGHIEP','G3a nông nghiệp bóc khỏi 3573 sau khi đảo'),
         ('VNS','VANTAI','G6 Vinasun taxi'),
         ('VRG','KHUCONGNGHIEP','tên là KCN'),
         ('VTK','CONGNGHE','G5d Tư vấn và Dịch vụ Viettel'),
         ('VTV','KHOANGSAN','G5a VICEM EE cấp 100% than cho 4 nhà máy xi măng thương mại theo mặt hàng'),
         ('VVS','THIETBI','G7 Đầu tư Phát triển Máy Việt Nam'),
         ('XMC','XAYDUNG','G5a xây dựng Xuân Mai'),
         ('XPH','HOACHAT','G7 Xà phòng Hà Nội cùng nhánh 3767 cùng luật')
        ;

        -- CHỐT CHẶN: hai ticker cùng issuer mà khác ngành thì DISTINCT ON bên dưới sẽ
        -- lặng lẽ giữ một dòng và vứt dòng kia. Dừng hẳn còn hơn seed sai âm thầm.
        DO $$
        DECLARE bad text;
        BEGIN
          SELECT string_agg(x.txt, '; ') INTO bad FROM (
            SELECT s.issuer_id || ': ' || string_agg(l.ticker || '=' || l.industry_code, ',') AS txt
            FROM _seed_l2 l
            JOIN market.security s ON s.ticker = l.ticker AND s.issuer_id IS NOT NULL
            GROUP BY s.issuer_id
            HAVING count(DISTINCT l.industry_code) > 1
          ) x;
          IF bad IS NOT NULL THEN
            RAISE EXCEPTION 'seed lop 2: hai ticker cung issuer nhung khac nganh - %', bad;
          END IF;
        END $$;

        -- Ticker chưa có issuer thì BỎ QUA (DB test rỗng issuer ⇒ nạp 0 dòng, đúng
        -- hành vi mong đợi). DISTINCT ON gộp ca một ticker có nhiều dòng security
        -- (listed + delisted) — chốt chặn ở trên đã loại ca nguy hiểm.
        INSERT INTO market.issuer_industry_override (issuer_id, industry_id, note)
        SELECT DISTINCT ON (s.issuer_id) s.issuer_id, i.industry_id, l.reason
        FROM _seed_l2 l
        JOIN market.security s ON s.ticker = l.ticker AND s.issuer_id IS NOT NULL
        JOIN market.industry i ON i.code = l.industry_code AND i.level = 2
        ORDER BY s.issuer_id, s.security_id
        ON CONFLICT (issuer_id) DO NOTHING;

        DO $$
        DECLARE n_rows int; n_matched int;
        BEGIN
          SELECT count(*) INTO n_rows FROM market.issuer_industry_override;
          SELECT count(DISTINCT l.ticker) INTO n_matched FROM _seed_l2 l
            JOIN market.security s ON s.ticker = l.ticker AND s.issuer_id IS NOT NULL;
          RAISE NOTICE 'seed lop 2: %/161 ticker khop issuer, % dong override', n_matched, n_rows;
        END $$;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM market.issuer_industry_override;
        DELETE FROM market.industry_icb_map;
        """
    )
