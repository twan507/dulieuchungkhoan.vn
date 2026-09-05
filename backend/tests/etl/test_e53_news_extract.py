"""Bóc 9 trang bài thật chụp 2026-09-05 theo luật article-structure §2: container đúng, boilerplate biến mất, tiền tố/hậu tố literal."""
import pathlib
from datetime import datetime, timezone, timedelta

import pytest

from etl import news_extract as ne

FIX = pathlib.Path(__file__).parent / "fixtures" / "news"
VN = timezone(timedelta(hours=7))


def _page(name):
    return (FIX / f"article-{name}.html").read_text(encoding="utf-8")


def test_rules_cover_nine_keys_and_min_chars():
    assert set(ne.RULES) == {"cafef", "cafef_cbtt", "vietstock", "vneconomy", "vietnambiz", "bnews", "nguoiquansat", "baochinhphu", "tinnhanhck"}
    assert ne.MIN_CHARS == 100


def test_cafef_drops_tin_moi_block_and_keeps_body():
    x = ne.extract(_page("cafef"), "cafef")
    assert x.title == "Green SM có động thái mới tại loạt tỉnh thành phía Nam"
    assert x.content.startswith("Công ty Cổ phần Di chuyển Xanh và Thông minh GSM vừa chính thức")
    assert x.content.endswith("giao thông bền vững ở quy mô toàn cầu.")
    assert "TIN MỚI" not in x.content and 2826 <= len(x.content) <= 3124
    assert x.sapo and len(x.sapo) > 50
    assert x.published_at == datetime(2026, 9, 5, 17, 9, tzinfo=VN)


def test_cafef_cbtt_short_text_is_legal_and_title_is_not_h1():
    x = ne.extract(_page("cafef_cbtt"), "cafef_cbtt")
    assert x.title == "HBC: Báo cáo tài chính bán niên năm 2026"
    assert x.content.startswith("Báo cáo tài chính bán niên năm 2026") and x.content.endswith("Theo HNX") and 646 <= len(x.content) <= 714
    assert x.published_at is None and x.sapo is None


def test_vietstock_drops_title_sapo_signature_and_keeps_body():
    x = ne.extract(_page("vietstock"), "vietstock")
    assert x.title == "Chỉ 2 phiên giao dịch, VIC đưa VN-Index qua những cung bậc trái chiều"
    assert not x.content.startswith("Chỉ 2 phiên giao dịch") and "Huy Khải" not in x.content and "FILI" not in x.content
    assert 1211 <= len(x.content) <= 1339 and x.published_at == datetime(2026, 9, 5, 19, 30, tzinfo=VN)
    assert x.sapo and "<" not in x.sapo


def test_vneconomy_keeps_body_and_drops_lead():
    x = ne.extract(_page("vneconomy"), "vneconomy")
    assert x.title.startswith("Sau soát xét, QCG báo lãi 181,7 tỷ đồng")
    # h4.article-content__lead lặp đúng nội dung sapo ngay đầu container (§2.4/§3.2) — bị bỏ, nên
    # câu thân bài THẬT bắt đầu ngay sau khối lead + ảnh minh hoạ bị gỡ.
    assert x.content.startswith("Cụ thể: doanh thu thuần trên BCTC bán niên 2026 đã soát xét đạt gần 81 tỷ đồng")
    assert "Công ty Cổ phần Quốc Cường Gia Lai (mã QCG-HOSE) công bố giải trình" not in x.content
    assert x.content.endswith("giả định hoạt động liên tục.") and 4300 <= len(x.content) <= 4500
    # published_at đọc từ span thời gian trang bài (không phải pubDate feed): 09:43, 04/09/2026
    assert x.published_at == datetime(2026, 9, 4, 9, 43, tzinfo=VN)


def test_vietnambiz_cleanest_source():
    x = ne.extract(_page("vietnambiz"), "vietnambiz")
    assert x.content.startswith("Trong tháng 8, ba cổ phiếu tăng tốt nhất trong danh mục là TCH, FRT và")
    assert x.content.endswith("hành khách quốc tế trong dài hạn.") and 3300 <= len(x.content) <= 3591
    assert x.title.startswith("TCH và hai mã họ FPT")


def test_bnews_text_nodes_not_p_tags_and_drops_label_and_signature():
    x = ne.extract(_page("bnews"), "bnews")
    assert x.title == "VN-Index tăng hơn 25 điểm nhờ cổ phiếu đầu ngành bất động sản"
    assert not x.content.startswith("BNEWS") and "Văn Giáp" not in x.content and "vnanet.vn" not in x.content
    assert x.content.endswith("hình thành trong những phiên trước đó.") and 2810 <= len(x.content) <= 3106
    assert x.sapo and not x.sapo.startswith("BNEWS") and x.published_at is None          # BNews: giờ từ feed


def test_nguoiquansat_drops_header_block():
    x = ne.extract(_page("nguoiquansat"), "nguoiquansat")
    assert not x.content.startswith("Doanh nghiệp A-Z") and "(Theo số liệu từ Tổng điều tra" not in x.content
    # div.sc-hightlight-box (bỏ theo §2.7 — tiểu sử doanh nghiệp lặp lại giữa nhiều bài) chính là khối
    # chứa câu "(Theo số liệu...)" ở CUỐI TRANG; bỏ nó thì câu cuối THẬT của thân bài là câu BIWASE 24MW.
    assert x.content.endswith("trong những năm tới.") and "Tổng điều tra kinh tế năm 2025" not in x.content
    assert 2900 <= len(x.content) <= 3050
    assert x.title.startswith("Doanh nghiệp cấp nước cho hơn 32 triệu dân")


def test_baochinhphu_drops_comments_and_related_box():
    x = ne.extract(_page("baochinhphu"), "baochinhphu")
    assert x.title == "Cơ chế, chính sách xác định giá sản phẩm in, đúc tiền"
    assert "GMT+0700" not in x.content and "Indochina" not in x.content and "Tham khảo thêm" not in x.content
    assert not x.content.endswith("in, đúc tiền") and 1499 <= len(x.content) <= 1657
    assert x.sapo and not x.sapo.startswith("(Chinhphu.vn)")
    # published_at đọc từ div.detail-time trang bài: 05/09/2026 13:30
    assert x.published_at == datetime(2026, 9, 5, 13, 30, tzinfo=VN)


def test_tinnhanhck_uses_cms_date_not_sitemap_lastmod():
    x = ne.extract(_page("tinnhanhck"), "tinnhanhck")
    assert x.title.startswith("Thái Nguyên: Dự án 1.100 tỷ đồng dang dở sau 4 năm")
    assert x.published_at == datetime(2026, 9, 5, 9, 18, 48, tzinfo=VN)
    assert x.content.endswith("không còn là lãnh đạo tại Hừng Đông.") and 4152 <= len(x.content) <= 4590 and "Từ Khoá" not in x.content
    assert x.sapo and not x.sapo.startswith("(ĐTCK)")


def test_errors_no_container_no_title_too_short():
    with pytest.raises(ne.ExtractError) as e:
        ne.extract("<html><body><p>nothing</p></body></html>", "cafef")
    assert e.value.reason == "no_container"
    with pytest.raises(ne.ExtractError) as e:
        ne.extract('<html><div class="detail-content afcbc-body">' + "x " * 200 + "</div></html>", "cafef")
    assert e.value.reason == "no_title"
    with pytest.raises(ne.ExtractError) as e:
        ne.extract('<html><h1 class="title">T</h1><div class="detail-content afcbc-body">ngắn quá</div></html>', "cafef")
    assert e.value.reason == "too_short"
    short = ne.extract('<html><td class="text_noibat_cacbaikhac"><span class="cms_blue">ABC: x</span></td><div id="newscontent">ngắn</div></html>', "cafef_cbtt")
    assert short.content == "ngắn"                                                   # CBTT được phép ngắn
    with pytest.raises(KeyError):
        ne.extract("<html></html>", "khong_co")
