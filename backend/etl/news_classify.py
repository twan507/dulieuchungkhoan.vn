"""Lưới AI phân loại tin (lát 9a, spec 2026-09-06-news-classify-llm): taxonomy 3 nhóm / 20 sub / x (news-pipeline §3, §7),
gắn mã tầng 3 (§8: mã AI LỌC qua danh sách niêm yết — model bịa `VFM`, minimax.md §7.1), gắn NGÀNH hai đường
(`ticker` suy từ mã, `ai` đọc hiểu, mọi nhóm). Danh sách 24 ngành NẠP TỪ market.industry lúc chạy — industry-tree.md là chủ,
không chép cứng (chatbot-semantic-layer §3.2). Schema công cụ có enum cho mọi trường phân loại: đó là thứ cho 0 lỗi/232 lời gọi.
Phần thuần (schema, prompt) ở trên; phần DB (chọn bài, ghi) và job ở dưới. Mọi lượt có TRẦN, không có chế độ chạy hết."""
from __future__ import annotations

import json
import logging
import sys
import time
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

import sqlalchemy as sa
from pydantic import BaseModel, ConfigDict, Field, create_model, model_validator

from core.env import load_dotenv
from core.llm import LLMClient, LLMConfigError, LLMError, LLMSettings, Usage
from etl import news_store, news_tag, omo_store
from etl.news_job import _engine

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


PURPOSE = "news.classify"
MAX_INDUSTRIES = 3


def _bucket_sql(hint) -> str:
    return "a.group_from_feed IS NULL" if hint is None else "a.group_from_feed = :g"


_SELECT = """
SELECT a.article_id, a.primary_source, a.feed, a.group_from_feed, a.ticker_step_ran, a.canonical_url, r.title, r.sapo, r.content
FROM news.article a
JOIN LATERAL (SELECT title, sapo, content FROM news.article_revision r WHERE r.article_id = a.article_id ORDER BY version DESC LIMIT 1) r ON true
WHERE a.classified_from IS NULL AND {bucket}
ORDER BY a.published_at DESC NULLS LAST, a.article_id DESC
LIMIT :n"""


def select_articles(conn, *, limit: int | None = None, per_group: int | None = None) -> list[Row]:
    """Bài chưa phân loại, mới nhất trước (spec §4.2-XI). per_group: N bài đầu của MỖI bucket group_from_feed 1 · 2 · 3 · NULL."""
    if (limit is None) == (per_group is None):
        raise ValueError("cần đúng một trong limit / per_group")
    out: list[Row] = []
    if limit is not None:
        rows = conn.execute(sa.text(_SELECT.format(bucket="true")), {"n": limit}).all()
        return [Row(*r) for r in rows]
    for hint in (1, 2, 3, None):
        rows = conn.execute(sa.text(_SELECT.format(bucket=_bucket_sql(hint))), {"n": per_group, "g": hint}).all()
        out.extend(Row(*r) for r in rows)
    return out


def apply(conn, row: Row, value, *, content_chars: int, classified_from: str, listed: dict[str, int], industry_ids: dict[str, int]) -> dict:
    """Ghi MỘT bài trong giao dịch của caller. x ⇒ group_no NULL + labels {x} (0007). Mã: chỉ nhóm 3 — tầng 2 bù nếu chưa chạy
    (bài backfill), tầng 3 = mã model ∩ niêm yết. Ngành: 'ai' từ model (≤ 3), 'ticker' từ MỌI article_ticker qua v_issuer_industry."""
    st = {"overridden": 0, "tickers_url": 0, "tickers_lookup": 0, "tickers_ai": 0, "tickers_ai_dropped": 0, "industries_ai": 0, "industries_ticker": 0}
    group_no = None if value.group == "x" else int(value.group)
    sub = None if value.group == "x" else value.sub
    overridden = row.group_from_feed is not None and group_no != row.group_from_feed
    st["overridden"] = int(overridden)
    conn.execute(sa.text(
        "UPDATE news.article SET group_no = :g, sub = :s, confidence = :c, classified_from = :cf, content_chars = :cc,"
        " group_overridden = :o, labels = :l, ticker_step_ran = ticker_step_ran OR :g3 WHERE article_id = :a"),
        {"g": group_no, "s": sub, "c": value.confidence, "cf": classified_from, "cc": content_chars, "o": overridden,
         "l": ["x"] if group_no is None else [], "g3": group_no == 3, "a": row.article_id})
    conn.execute(sa.text(
        "UPDATE news.article_revision SET summary_ai = :s WHERE article_id = :a AND summary_ai IS NULL"
        " AND version = (SELECT max(version) FROM news.article_revision WHERE article_id = :a)"), {"s": value.summary_ai, "a": row.article_id})
    if group_no == 3:
        tickers: list[tuple[str, str]] = []
        if not row.ticker_step_ran:                                    # tầng 1–2 chưa chạy (group_from_feed ≠ 3 ở lát 8) ⇒ chạy bù
            for t in news_tag.tickers_from_url(row.url):
                if t in listed:
                    tickers.append((t, "url"))
                    st["tickers_url"] += 1
            for t in news_tag.tickers_lookup(row.title, row.sapo, listed):
                tickers.append((t, "lookup"))
                st["tickers_lookup"] += 1
        for t in dict.fromkeys(x.strip().upper() for x in value.tickers if x.strip()):
            if t in listed:
                tickers.append((t, "ai"))
                st["tickers_ai"] += 1
            else:
                st["tickers_ai_dropped"] += 1                          # VFM bịa (minimax.md §7.1) — không vào kho
        for t, via in tickers:
            conn.execute(sa.text("INSERT INTO news.article_ticker (article_id, security_id, via) VALUES (:a, :s, :v) ON CONFLICT DO NOTHING"),
                         {"a": row.article_id, "s": listed[t], "v": via})
    for code in list(dict.fromkeys(value.industries))[:MAX_INDUSTRIES]:
        conn.execute(sa.text("INSERT INTO news.article_industry (article_id, industry_id, via, confidence) VALUES (:a, :i, 'ai', :c) ON CONFLICT DO NOTHING"),
                     {"a": row.article_id, "i": industry_ids[code], "c": value.confidence})
        st["industries_ai"] += 1
    st["industries_ticker"] = conn.execute(sa.text(
        "INSERT INTO news.article_industry (article_id, industry_id, via)"
        " SELECT DISTINCT t.article_id, v.industry_id, 'ticker' FROM news.article_ticker t"
        " JOIN market.security s USING (security_id) JOIN market.v_issuer_industry v ON v.issuer_id = s.issuer_id"
        " WHERE t.article_id = :a AND v.industry_id IS NOT NULL ON CONFLICT DO NOTHING"), {"a": row.article_id}).rowcount
    return st


def log_call(conn, *, run_id, article_id, model: str, thinking: str, status: str, usage: Usage | None, latency_s: float, error: str | None = None) -> None:
    u = usage
    conn.execute(sa.text(
        "INSERT INTO ops.llm_call (purpose, model, thinking, run_id, article_id, status, http_calls, input_tokens, cache_read_tokens,"
        " output_tokens, thinking_tokens, latency_ms, error)"
        " VALUES (:p, :m, :t, :r, :a, :s, :hc, :i, :c, :o, :th, :ms, :e)"),
        {"p": PURPOSE, "m": model, "t": thinking, "r": run_id, "a": article_id, "s": status, "hc": u.calls if u else 1,
         "i": u.input_tokens if u else None, "c": u.cache_read_tokens if u else None, "o": u.output_tokens if u else None,
         "th": u.thinking_tokens if u else None, "ms": int(round(latency_s * 1000)), "e": error})


log = logging.getLogger("etl.classify")
JOB = "news.classify"
QUOTA_EVERY = 25
QUOTA_MIN_INTERVAL_PCT = 20       # cửa sổ 5 giờ — giữ phần cho chatbot/dev (brainstorm §4.4)
QUOTA_MIN_WEEKLY_PCT = 10
MAX_CONSECUTIVE_FAILED = 5


class ModelDown(Exception):
    """5 lời gọi liên tiếp lỗi thử-lại-được — model/mạng/quota chết, dừng lượt (khuôn SourceDown)."""

    def __init__(self, msg: str, stats: dict):
        self.stats = stats
        super().__init__(msg)


def _empty_stats(thinking: str, cap: int, selected: int) -> dict:
    return {"thinking": thinking, "cap_chars": cap, "selected": selected, "classified": 0, "failed": 0, "failed_schema": 0, "repaired": 0,
            "groups": {"1": 0, "2": 0, "3": 0, "x": 0}, "overridden": 0, "title_only": 0, "tickers_url": 0, "tickers_lookup": 0,
            "tickers_ai": 0, "tickers_ai_dropped": 0, "industries_ai": 0, "industries_ticker": 0,
            "tokens": {"input": 0, "cache_read": 0, "output": 0, "thinking": 0}, "latency_s": {"p50": None, "p90": None, "max": None, "total": 0.0},
            "usd_estimate": 0.0, "quota": {}, "quota_stop": False, "budget_hit": False, "warnings": []}


def _quota_ok(client, st: dict, key: str) -> bool:
    try:
        q = client.token_plan_remains()
    except LLMError as e:                                          # guard hỏng ⇒ cảnh báo, không chặn (spec §4.2-VIII)
        st["warnings"].append(f"quota: {e}")
        return True
    st["quota"][key] = {"interval_pct": q.interval_pct, "weekly_pct": q.weekly_pct}
    return q.interval_pct >= QUOTA_MIN_INTERVAL_PCT and q.weekly_pct >= QUOTA_MIN_WEEKLY_PCT


def _pct(xs: list[float], p: float) -> float:
    s = sorted(xs)
    return s[int(p * (len(s) - 1))]


def classify_run(engine, client, rows: list[Row], *, run_id, schema, system: str, thinking: str, listed: dict, industry_ids: dict,
                 dry_run: bool = False, out=None, max_minutes: float | None = None, cap: int = CAP_CHARS, clock=time.monotonic) -> dict:
    t0 = clock()
    st = _empty_stats(thinking, cap, len(rows))
    lat: list[float] = []
    tok = Usage()
    try:
        if not _quota_ok(client, st, "before"):
            st["quota_stop"] = True
            return st
        streak = 0
        for i, row in enumerate(rows):
            if i and i % QUOTA_EVERY == 0 and not _quota_ok(client, st, "after"):
                st["quota_stop"] = True
                break
            if max_minutes is not None and clock() - t0 >= max_minutes * 60:
                st["budget_hit"] = True
                break
            user, content_chars, classified_from = user_prompt(row, cap)
            t1 = clock()
            try:
                r = client.structured(schema, system=system, user=user, thinking=thinking)
            except LLMError as e:
                st["failed"] += 1
                if e.reason == "schema":
                    st["failed_schema"] += 1
                if not dry_run:
                    with engine.begin() as c:
                        log_call(c, run_id=run_id, article_id=row.article_id, model=client.settings.model, thinking=thinking, status="failed",
                                 usage=None, latency_s=clock() - t1, error=str(e))
                log.warning("bài %s: %s", row.article_id, e)
                if e.reason == "auth":
                    raise
                if e.retryable:
                    streak += 1
                    if streak >= MAX_CONSECUTIVE_FAILED:
                        raise ModelDown(f"{streak} lời gọi liên tiếp lỗi thử-lại-được — model/mạng/quota chết, dừng lượt", st) from e
                continue
            streak = 0
            lat.append(r.usage.latency_s)
            tok = tok + r.usage
            st["repaired"] += int(r.repaired)
            st["groups"][r.value.group] += 1
            st["title_only"] += int(classified_from == "title_only")
            if dry_run:
                out.write(json.dumps({"article_id": row.article_id, "hint": row.group_from_feed, "source": row.primary_source, "title": row.title[:80],
                                      "classified_from": classified_from, "content_chars": content_chars, "value": r.value.model_dump(),
                                      "usage": r.usage.__dict__, "repaired": r.repaired}, ensure_ascii=False) + "\n")
                st["classified"] += 1
                continue
            with engine.begin() as c:
                a = apply(c, row, r.value, content_chars=content_chars, classified_from=classified_from, listed=listed, industry_ids=industry_ids)
                log_call(c, run_id=run_id, article_id=row.article_id, model=client.settings.model, thinking=thinking,
                         status="repaired" if r.repaired else "ok", usage=r.usage, latency_s=r.usage.latency_s)
            for k, v in a.items():
                st[k] += v
            st["classified"] += 1
        if not st["quota_stop"]:
            _quota_ok(client, st, "after")
        return st
    finally:
        st["tokens"] = {"input": tok.input_tokens, "cache_read": tok.cache_read_tokens, "output": tok.output_tokens, "thinking": tok.thinking_tokens}
        if lat:
            st["latency_s"] = {"p50": _pct(lat, 0.5), "p90": _pct(lat, 0.9), "max": max(lat), "total": round(sum(lat), 3)}
        st["usd_estimate"] = round(tok.estimate_usd(), 4)


def run(limit: int | None = None, per_group: int | None = None, thinking: str = "adaptive", dry_run: bool = False, out: str | None = None,
        max_minutes: float | None = None, cap: int = CAP_CHARS, client=None, clock=time.monotonic) -> int:
    logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    logging.getLogger("httpx2").setLevel(logging.WARNING)
    logging.getLogger("anthropic").setLevel(logging.WARNING)
    load_dotenv()
    engine = None
    try:
        engine = _engine()
        if client is None:
            client = LLMClient(LLMSettings.from_env())
        with engine.connect() as c:
            inds = c.execute(sa.text("SELECT industry_id, code, name_vi FROM market.industry WHERE level = 2 ORDER BY sort_order, code")).all()
            if len(inds) != 24:
                raise RuntimeError(f"market.industry level 2 có {len(inds)} mã, mong 24 (industry-tree.md)")
            listed = news_store.load_listed(c)
            rows = select_articles(c, limit=limit, per_group=per_group)
    except (RuntimeError, ValueError, LLMConfigError) as e:
        log.error("%s", e)
        if engine is not None:                     # lỗi sau khi đã mở engine — đừng rò pool (news_job.run_backfill cùng khuôn)
            engine.dispose()
        return 2
    schema = build_schema([r.code for r in inds])
    system = system_prompt([(r.code, r.name_vi) for r in inds])
    industry_ids = {r.code: r.industry_id for r in inds}
    log.info("classify: %s bài, thinking %s, dry_run %s, trần %s ký tự", len(rows), thinking, dry_run, cap)
    kw = dict(schema=schema, system=system, thinking=thinking, listed=listed, industry_ids=industry_ids, max_minutes=max_minutes, cap=cap, clock=clock)
    if dry_run:
        fh = open(out, "w", encoding="utf-8") if out else sys.stdout
        try:
            st = classify_run(engine, client, rows, run_id=None, dry_run=True, out=fh, **kw)
            log.info("classify dry-run xong: %s", st)
            return 0
        except ModelDown as e:
            log.error("%s — stats %s", e, e.stats)
            return 1
        except LLMError as e:
            log.error("%s", e)
            return 2
        except KeyboardInterrupt:
            log.warning("classify dừng tay (Ctrl+C)")
            return 130
        finally:
            if out:
                fh.close()
            engine.dispose()
    run_id = omo_store.open_run(engine, JOB)
    try:
        st = classify_run(engine, client, rows, run_id=run_id, **kw)
        omo_store.close_run(engine, run_id, "success", st)
        log.info("classify xong: %s", st)
        return 0
    except ModelDown as e:
        omo_store.close_run(engine, run_id, "failed", e.stats, error=str(e))
        log.error("%s", e)
        return 1
    except KeyboardInterrupt:
        omo_store.close_run(engine, run_id, "failed", error="dừng tay (Ctrl+C)")
        return 130
    except LLMError as e:                                          # 'auth' — gọi tiếp vô ích
        omo_store.close_run(engine, run_id, "failed", error=str(e))
        log.error("%s", e)
        return 2
    except Exception as e:                                         # noqa: BLE001 — job biên ngoài
        omo_store.close_run(engine, run_id, "failed", error=f"{type(e).__name__}: {e}")
        log.exception("classify thất bại")
        return 2
    finally:
        engine.dispose()
