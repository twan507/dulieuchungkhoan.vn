"""Đăng ký 9 function cho model.

build_tools là FACTORY chứ không phải hằng module: BetaFunctionTool.call(input) chỉ truyền
đối số do model sinh, không có khe nhận Connection ⇒ engine phải đi vào bằng closure.
Mỗi tool tự mở và đóng kết nối trong thân hàm — KHÔNG giữ kết nối bắc qua lời gọi model.
"""
from __future__ import annotations

from typing import Literal

import sqlalchemy as sa
from anthropic import beta_tool

from agent.skills import L2_TOPICS
from agent.tools.compare_peers import so_sanh_cung_nganh
from agent.tools.get_corporate_events import su_kien_doanh_nghiep
from agent.tools.get_financials import bao_cao_tai_chinh
from agent.tools.get_industry_tree import cay_nganh
from agent.tools.get_macro_series import chuoi_vi_mo
from agent.tools.get_news import tim_tin
from agent.tools.get_price_series import gia_theo_ngay
from agent.tools.load_knowledge_reference import doc_tri_thuc
from agent.tools.screen_stocks import loc_co_phieu

# spec §4.4 #9 / §6 S5: topic bị từ chối Ở TẦNG SCHEMA, không chỉ ở thân doc_tri_thuc — 9 khoá
# lấy thẳng từ agent.skills.L2_TOPICS để không có nguồn sự thật thứ hai (CLAUDE.md §1.7).
_TOPICS = tuple(L2_TOPICS)


def build_tools(engine: sa.Engine) -> list:
    def chay(fn, *args, **kwargs) -> str:
        with engine.connect() as conn:
            conn.execute(sa.text("SET LOCAL statement_timeout = '20s'"))
            return fn(conn, *args, **kwargs)

    @beta_tool
    def get_price_series(ticker: str, from_date: str | None = None, to_date: str | None = None,
                         adjusted: bool = True) -> str:
        """Chuỗi giá theo ngày của một mã cổ phiếu Việt Nam (giá mở/cao/thấp/đóng cửa).

        ticker: mã chứng khoán hoặc mã chỉ số, ví dụ 'HPG', 'VCB', 'VNINDEX'. from_date/to_date:
        'YYYY-MM-DD', bỏ trống lấy các phiên gần nhất. adjusted: true dùng giá đã điều chỉnh.
        **Luôn gọi hàm này trước khi nói về giá hay điểm số của bất kỳ mã nào, kể cả VN-Index
        và các chỉ số khác** — hàm trả lời rõ ràng khi kho chưa có dữ liệu cho mã đó, đừng tự
        phỏng đoán là có hay không có.
        """
        return chay(gia_theo_ngay, ticker, from_date, to_date, adjusted)

    @beta_tool
    def get_financials(ticker: str, statement_type: str = "IS", from_year: int | None = None,
                       to_year: int | None = None, period: str = "nam",
                       metric_codes: list[str] = []) -> str:
        """Số liệu báo cáo tài chính của một doanh nghiệp niêm yết.

        statement_type: 'IS' kết quả kinh doanh, 'BS' cân đối kế toán, 'CF' lưu chuyển tiền tệ.
        period: 'nam' (cả năm) hoặc 'quy'. metric_codes để trống thì trả bộ chỉ tiêu cốt lõi.
        Tối đa 20 kỳ mỗi lần gọi.
        """
        return chay(bao_cao_tai_chinh, ticker, statement_type, from_year, to_year, period, metric_codes)

    @beta_tool
    def screen_stocks(criteria: list[dict] = [], industry_code: str | None = None,
                      exchange: str | None = None, sort_by: str | None = None,
                      limit: int | None = None) -> str:
        """Lọc và xếp hạng cổ phiếu theo chỉ tiêu tài chính của phiên gần nhất.

        criteria: danh sách {"metric_code","operator","value"} với operator ∈ > < >= <= =.
        industry_code: mã ngành trong bộ 24 ngành của hệ thống (lấy bằng get_industry_tree).
        exchange: 'HOSE' | 'HNX' | 'UPCOM'. sort_by: mã chỉ tiêu để xếp hạng giảm dần.
        """
        return chay(loc_co_phieu, criteria, industry_code, exchange, sort_by, limit)

    @beta_tool
    def compare_peers(tickers: list[str] = [], metric_codes: list[str] = [],
                      industry_code: str | None = None) -> str:
        """So sánh nhiều mã trên cùng bộ chỉ tiêu, cùng một phiên dữ liệu. Tối đa 25 mã."""
        return chay(so_sanh_cung_nganh, tickers, metric_codes, industry_code)

    @beta_tool
    def get_corporate_events(ticker: str, event_type: str | None = None,
                             from_date: str | None = None, to_date: str | None = None,
                             limit: int | None = None) -> str:
        """Sự kiện doanh nghiệp: cổ tức tiền mặt, cổ tức cổ phiếu, phát hành thêm, đại hội,
        công bố kết quả kinh doanh, IPO.

        event_type ∈ 'CashDividend' | 'StockDividend' | 'ShareIssuance' | 'AGM' | 'Earning' | 'IPO'.
        """
        return chay(su_kien_doanh_nghiep, ticker, event_type, from_date, to_date, limit)

    @beta_tool
    def get_industry_tree(industry_code: str | None = None, ticker: str | None = None) -> str:
        """Khung ngành của hệ thống: 6 nhóm × 24 ngành, hoặc ngành của một mã cụ thể.

        Đây là khung ngành DUY NHẤT dùng để phân tích và hiển thị. Bỏ trống cả hai tham số để
        lấy toàn bộ cây.
        """
        return chay(cay_nganh, industry_code, ticker)

    @beta_tool
    def get_macro_series(code: str | None = None, keyword: str | None = None,
                         from_date: str | None = None, to_date: str | None = None,
                         limit: int | None = None) -> str:
        """Chuỗi vĩ mô Việt Nam/Mỹ và giá tài sản (hàng hoá, tiền tệ, chỉ số quốc tế, crypto).

        Không biết mã thì để trống code và truyền keyword để lấy DANH MỤC chuỗi khớp, rồi gọi
        lại với code. Ví dụ mã: 'vn.cpi', 'vn.m2', 'us.yield.10y', 'wti', 'gold.sjc_sell',
        'fx.usd_vnd.central', 'idx.sp500', 'btc'.
        """
        return chay(chuoi_vi_mo, code, keyword, from_date, to_date, limit)

    @beta_tool
    def get_news(query: str | None = None, ticker: str | None = None, group_no: int | None = None,
                 sub: str | None = None, industry_code: str | None = None,
                 from_date: str | None = None, to_date: str | None = None,
                 limit: int | None = None) -> str:
        """Tìm tin tức tài chính trong kho.

        query: tìm toàn văn (ưu tiên khớp đúng cụm). ticker/group_no/sub/industry_code: lọc theo
        nhãn — chỉ khớp những bài đã được phân loại. Mỗi bài trả kèm cờ da_phan_loai.
        """
        return chay(tim_tin, query, ticker, group_no, sub, industry_code, from_date, to_date, limit)

    @beta_tool
    def load_knowledge_reference(topic: Literal[_TOPICS]) -> str:
        """Đọc một tài liệu kiến thức chuyên sâu khi cần công thức, quy trình hoặc định nghĩa.

        topic ∈ 'valuation' (định giá, DCF, FCFF/FCFE, WACC, P/E, P/B) | 'financial-statements'
        (đọc BCTC, các chỉ số) | 'macro-money-creation' (vĩ mô, tiền tệ, tín dụng) |
        'technical-indicators' (chỉ báo kỹ thuật) | 'technical-supply-demand' (cung cầu, dòng
        tiền) | 'portfolio-and-rotation' (danh mục, luân chuyển ngành) | 'psychology-information'
        (tâm lý, thông tin) | 'advanced' (CAPM, Fama-French, APT, phòng hộ) | 'tong-quan'.
        """
        return doc_tri_thuc(topic)

    return [get_price_series, get_financials, screen_stocks, compare_peers, get_corporate_events,
            get_industry_tree, get_macro_series, get_news, load_knowledge_reference]
