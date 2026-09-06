"""Lưới AI phân loại tin (lát 9a, spec 2026-09-06-news-classify-llm): taxonomy 3 nhóm / 20 sub / x (news-pipeline §3, §7),
gắn mã tầng 3 (§8: mã AI LỌC qua danh sách niêm yết — model bịa `VFM`, minimax.md §7.1), gắn NGÀNH hai đường
(`ticker` suy từ mã, `ai` đọc hiểu, mọi nhóm). Danh sách 24 ngành NẠP TỪ market.industry lúc chạy — industry-tree.md là chủ,
không chép cứng (chatbot-semantic-layer §3.2). Schema công cụ có enum cho mọi trường phân loại: đó là thứ cho 0 lỗi/232 lời gọi.
Phần thuần (schema, prompt) ở trên; phần DB (chọn bài, ghi) và job ở dưới. Mọi lượt có TRẦN, không có chế độ chạy hết."""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, create_model, model_validator

CAP_CHARS = 3000              # trần ký tự thân bài nạp model (news-pipeline §12: 3.000 hay 4.000 chốt sau khi có ca sai thật)
TITLE_ONLY_BELOW = 200        # thân < 200 ký tự (CafeF CBTT) ⇒ classified_from='title_only' (§7.1b)
GROUPS = ("1", "2", "3", "x")
SUBS = {"1": ["1a", "1b", "1c", "1d", "1e", "1f"], "2": ["2a", "2b", "2c", "2d", "2e"],
        "3": ["3a", "3b", "3c", "3d", "3e", "3f", "3g", "3h", "3i"], "x": ["x"]}
ALL_SUBS = [s for v in SUBS.values() for s in v]

# Khối tĩnh — đặt đầu system để cache tự động (≥ 512 token, minimax.md §6). Taxonomy chép từ news-pipeline §3 (đã đo 232 lời gọi).
SYSTEM_TAXONOMY = """Bạn là bộ phân loại tin tài chính Việt Nam của dulieuchungkhoan.vn. Đọc toàn văn bài và trả về đúng một lời gọi công cụ Classification.
Taxonomy 3 nhóm / 20 sub; nhãn x = loại bỏ (tin xã hội, thể thao, giáo dục, y tế thuần; PR, advertorial). Khi group = x thì sub = x.
Nhóm 1 · Vĩ mô trong nước: 1a Thể chế và văn bản pháp quy · 1b Điều hành Chính phủ (gồm kiến nghị, tiếng nói khu vực tư nhân) · 1c Tiền tệ và tỷ giá · 1d Đầu tư công và hạ tầng · 1e Số liệu vĩ mô · 1f Thuế và ngân sách.
Nhóm 2 · Tài chính quốc tế: 2a Chứng khoán thế giới · 2b Ngân hàng trung ương · 2c Hàng hoá và năng lượng · 2d An ninh và địa chính trị · 2e Thương mại và thuế quan.
Nhóm 3 · Doanh nghiệp niêm yết: 3a CBTT và sự kiện quyền · 3b Giao dịch nội bộ và cổ đông lớn · 3c Vốn và cấu trúc · 3d KQKD và vận hành · 3e Nhận định và diễn biến thị trường · 3f Phái sinh, chứng quyền, ETF/quỹ · 3g Vi phạm và xử phạt · 3h Margin và ký quỹ · 3i Xếp hạng tín nhiệm và ESG."""

SYSTEM_RULES = """Quy tắc: nhóm gợi ý từ feed chỉ là tín hiệu, được phép ghi đè (1↔3 nhảy thường xuyên). confidence trong [0,1].
summary_ai: 2–3 câu, 200–300 ký tự, không mở đầu bằng "Bài viết nói về", giữ nguyên mọi con số trong bản gốc.
tickers: mã niêm yết HOSE/HNX/UPCoM là chủ thể của bài (chỉ khi nhóm 3), rỗng nếu không có; không bịa.
industries: mã ngành (trong danh sách trên) mà bài liên quan TRỰC TIẾP, áp cho mọi nhóm (tin chính sách, giá hàng hoá, thuế quan cũng thuộc ngành);
tối đa 3 ngành, xếp ngành liên quan nhất trước; rỗng nếu bài không thuộc ngành nào (vĩ mô thuần, tin loại bỏ)."""


@dataclass(frozen=True)
class Row:
    article_id: int
    primary_source: str
    feed: str | None
    group_from_feed: int | None
    ticker_step_ran: bool
    url: str                       # canonical_url — tầng 1 (CafeF CBTT) đọc mã từ đây
    title: str
    sapo: str | None
    content: str | None


class _ClassificationBase(BaseModel):
    """Kết quả phân loại một bài"""
    model_config = ConfigDict(extra="forbid")
    group: Literal["1", "2", "3", "x"]
    sub: Literal[tuple(ALL_SUBS)]        # noqa: F821 — Literal nhận tuple như nhiều đối số
    confidence: float = Field(ge=0, le=1)
    summary_ai: str
    tickers: list[str]

    @model_validator(mode="after")
    def _sub_in_group(self):
        if self.sub not in SUBS[self.group]:
            raise ValueError(f"sub {self.sub} không thuộc nhóm {self.group}")
        return self


def build_schema(industry_codes: Sequence[str]) -> type[BaseModel]:
    codes = tuple(industry_codes)
    if not codes or len(codes) != len(set(codes)):
        raise ValueError(f"danh sách ngành rỗng hoặc trùng: {codes}")
    return create_model("Classification", __base__=_ClassificationBase, __doc__="Kết quả phân loại một bài",
                        industries=(list[Literal[codes]], ...))   # type: ignore[valid-type]


def system_prompt(industries: Sequence[tuple[str, str]]) -> str:
    lines = "\n".join(f"{code} — {name}" for code, name in industries)
    return f"{SYSTEM_TAXONOMY}\nNgành (level 2 của dulieuchungkhoan.vn, dùng đúng mã):\n{lines}\n{SYSTEM_RULES}"


def user_prompt(row: Row, cap: int = CAP_CHARS) -> tuple[str, int, str]:
    body = (row.content or "")[:cap]
    n = len(body)
    classified_from = "content" if n >= TITLE_ONLY_BELOW else "title_only"
    hint = row.group_from_feed if row.group_from_feed is not None else "không có"
    text = (f"Nguồn: {row.primary_source} · feed: {row.feed or ''} · nhóm gợi ý: {hint}\nTiêu đề: {row.title}\nSapo: {row.sapo or ''}\n\n"
            f"Toàn văn (đã cắt {cap} ký tự):\n{body}")
    return text, n, classified_from
