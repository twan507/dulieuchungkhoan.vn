"""Một lần chạy price: list_codes → fetch → (summarize → guard) → apply → close_run (spec §5).

Hai chế độ dùng chung fetch/normalize/store:
- hằng ngày: trang 1 mọi mã, MỘT giao dịch, guard TRƯỚC commit (khuôn events_job);
- --backfill: mọi trang, mỗi mã một giao dịch, con trỏ ghi sau từng mã, ngân sách --max-minutes
  kiểm GIỮA hai mã (mã đang dở luôn được làm xong). Mã hỏng/sai vẫn đẩy con trỏ đi — nó được
  làm lại ở vòng sau, dấu vết là `failed_tickers`/`invalid_tickers`.
"""
from __future__ import annotations

import logging
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import sqlalchemy as sa

from core.env import load_dotenv
from etl import omo_store, price_fetch, price_guard, price_normalize, price_store

log = logging.getLogger("etl.price")
VN = ZoneInfo("Asia/Ho_Chi_Minh")
_wall_clock = time.time      # seam cho test: patch toàn cục time.time thì SQLAlchemy pool cũng ăn tick


class GuardRefused(Exception):
    def __init__(self, verdict):
        self.verdict = verdict
        super().__init__("; ".join(verdict.reasons))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _names(by_organ, codes):
    return [by_organ[c].ticker for c in codes[:price_store.SAMPLE]]


def _next_open(now: datetime) -> datetime:
    """08:45 của ngày giao dịch kế tiếp (Thứ 2–6, chưa biết ngày lễ) — hạn cho task backfill:
    kích hoạt tay tối thứ 3 ⇒ dừng trước phiên sáng thứ 4; chạy thứ 7 ⇒ chạy liền tới sáng thứ 2."""
    d = now.replace(hour=8, minute=45, second=0, microsecond=0)
    if d <= now:
        d += timedelta(days=1)
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d


def _codes_or_raise(engine, tickers):
    with engine.connect() as conn:
        cl = price_store.list_codes(conn, tickers)
    if not cl.codes:
        # Không có gì để gọi thì lỗi ở tham số/danh bạ, không phải ở nguồn — để guard (0) báo
        # "nguồn hỏng" là chẩn đoán sai hướng (review 2026-09-04).
        raise ValueError("không mã nào có organCode để gọi FiinTrade"
                         f" (no_organ_code: {cl.no_organ_code[:price_store.SAMPLE]})")
    return cl


def run(backfill: bool = False, codes: list[str] | None = None,
        max_minutes: float | None = None, stop_before_open: bool = False) -> int:
    logging.basicConfig(level=logging.INFO, stream=sys.stderr,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    # httpx ghi INFO cho TỪNG request — 1.523 dòng "HTTP Request: GET …" mỗi ngày trong price.log,
    # lấp mất dòng tiến độ và dòng cảnh báo của chính job. Các job trước chỉ gọi ≤ 52 lần nên chưa lộ.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    load_dotenv()
    url = os.environ.get("ETL_DATABASE_URL")
    if not url:
        log.error("thiếu ETL_DATABASE_URL")
        return 2
    # pool_pre_ping: máy ngủ theo lịch (02:00) giữa lượt — kết nối nằm trong pool suốt 38 phút fetch
    # thường chết sau giấc ngủ; không pre-ping thì load_baseline/giao dịch ghi ném OperationalError
    # sau khi đã gọi xong 1.523 lời gọi. Fetch tự sống qua giấc ngủ nhờ retry exception vận chuyển.
    engine = sa.create_engine(url, pool_pre_ping=True)
    try:
        return (_backfill(engine, codes, max_minutes, stop_before_open) if backfill
                else _daily(engine, codes))
    finally:
        engine.dispose()


def _daily(engine, tickers: list[str] | None) -> int:
    run_id = omo_store.open_run(engine, price_store.JOB_DAILY)
    t0 = time.monotonic()
    stats: dict = {}
    try:
        cl = _codes_or_raise(engine, tickers)
        by_organ = {c.organ_code: c for c in cl.codes}
        with price_fetch.open_fetcher() as f:
            res = f.many([c.organ_code for c in cl.codes], max_pages=1)
            retries = f.retries
        summaries = {code: price_normalize.summarize(texts) for code, texts in res.pages.items()}
        with_data = sum(1 for s in summaries.values() if s.n_rows)
        empty = [code for code, s in summaries.items() if not s.n_rows]   # Success mà items rỗng
        latest = max((s.latest for s in summaries.values() if s.latest), default=None)
        subset = tickers is not None
        baseline = None if subset else price_store.load_baseline(engine)
        stats = {"codes": len(cl.codes), "with_data": with_data,
                 "empty": len(empty), "empty_tickers": _names(by_organ, empty),
                 "invalid": len(res.invalid), "invalid_tickers": _names(by_organ, res.invalid),
                 "failed": len(res.failed), "failed_tickers": _names(by_organ, res.failed),
                 "no_organ_code_count": len(cl.no_organ_code),
                 "no_organ_code": cl.no_organ_code[:price_store.SAMPLE], "retries": retries,
                 "latest_trading_date": latest.isoformat() if latest else None}
        if subset:
            stats["subset"] = True                 # lượt --codes không được làm mốc cho lượt toàn tập
        try:
            verdict = price_guard.check(len(cl.codes), with_data, len(res.invalid), len(res.failed),
                                        latest, datetime.now(VN).date(), baseline, empty=len(empty))
            if not verdict.ok:
                raise GuardRefused(verdict)
            fetched_at = _now_iso()
            sent = changed = dups = 0
            bounds: list[tuple[int, object]] = []
            with engine.begin() as conn:
                for code, texts in res.pages.items():
                    rows, d = price_normalize.normalize_code(code, texts)
                    if not rows:
                        continue
                    sid = by_organ[code].security_id
                    a = price_store.apply(conn, sid, rows, fetched_at)
                    sent += a["rows_sent"]
                    changed += a["rows_changed"]
                    dups += d
                    bounds.append((sid, min(r.trading_date for r in rows)))
                mism, sample = price_store.raw_close_mismatches(conn, bounds)
        except GuardRefused as e:
            price_store.store_refusal_evidence(engine, run_id, e.verdict.reasons, stats, res.pages)
            omo_store.close_run(engine, run_id, "failed", stats,
                                error="guard refused: " + "; ".join(e.verdict.reasons))
            log.error("price từ chối: %s", e.verdict.reasons)
            return 1
        stats.update({"rows_sent": sent, "rows_changed": changed, "dup_dates": dups,
                      "raw_close_mismatch": mism, "raw_close_mismatch_sample": sample,
                      "elapsed_s": round(time.monotonic() - t0)})
        omo_store.close_run(engine, run_id, "success", stats)
        if not subset:
            price_store.upsert_domain_state(engine, stats["latest_trading_date"])
        log.info("price xong: %s", stats)
        return 0
    except Exception as e:  # noqa: BLE001 — job biên ngoài: mọi lỗi đều phải vào etl_run
        omo_store.close_run(engine, run_id, "failed", stats or None, error=f"{type(e).__name__}: {e}")
        log.exception("price thất bại")
        return 2


def _resume_point(todo, cursor):
    """Mã kế sau con trỏ. So theo VỊ TRÍ trong danh sách (cùng thứ tự ORDER BY của Postgres);
    chỉ khi mã con trỏ đã rời sàn mới lùi về so chuỗi — hai thứ tự này trùng với ticker ASCII hiện
    tại, nhưng không nên treo tính đúng vào collation (review 2026-09-04)."""
    idx = next((i for i, c in enumerate(todo) if c.ticker == cursor), None)
    return todo[idx + 1:] if idx is not None else [c for c in todo if c.ticker > cursor]


def _backfill(engine, tickers: list[str] | None, max_minutes: float | None,
              stop_before_open: bool = False) -> int:
    run_id = omo_store.open_run(engine, price_store.JOB_BACKFILL)
    t0 = time.monotonic()
    # Hạn theo đồng hồ TƯỜNG, không theo monotonic: máy ngủ 4 giờ giữa chừng thì thức dậy là hết
    # ngân sách ⇒ dừng sau mã đang dở, không đem phần ngân sách còn lại chạy lấn vào giờ giao dịch.
    # Hai cách đặt hạn cộng được với nhau: ngân sách phút, và/hoặc 08:45 ngày giao dịch kế tiếp.
    deadlines = []
    if max_minutes is not None:
        deadlines.append(_wall_clock() + max_minutes * 60)
    if stop_before_open:
        deadlines.append(_next_open(datetime.now(VN)).timestamp())
    deadline = min(deadlines) if deadlines else None
    stop_at = datetime.fromtimestamp(deadline, VN).isoformat(timespec="minutes") if deadline else None
    stats: dict = {"cursor": None, "stop_at": stop_at,
                   "codes_done": 0, "pages": 0, "rows_sent": 0, "rows_changed": 0,
                   "dup_dates": 0, "raw_close_mismatch": 0, "raw_close_mismatch_sample": [],
                   "invalid_tickers": [], "failed_tickers": [], "retries": 0,
                   "budget_hit": False, "pass_complete": False, "elapsed_s": 0}
    try:
        cl = _codes_or_raise(engine, tickers)
        todo = cl.codes
        if tickers is None:
            cursor = price_store.load_cursor(engine)
            if cursor:
                after = _resume_point(todo, cursor)
                if after:
                    log.info("tiếp tục sau con trỏ %s: còn %d mã", cursor, len(after))
                    todo = after
                else:
                    log.info("con trỏ %s đã ở cuối danh sách — bắt đầu vòng mới từ %s",
                             cursor, todo[0].ticker)
        else:
            stats["subset"] = True
        with price_fetch.open_fetcher() as f:
            for i, c in enumerate(todo, 1):
                texts: list[str] = []
                try:
                    texts = f.pages(c.organ_code, max_pages=None)
                except price_fetch.CodeInvalid:
                    stats["invalid_tickers"].append(c.ticker)
                except price_fetch.SourceDown:
                    raise
                except price_fetch.FetchError as e:
                    stats["failed_tickers"].append(c.ticker)
                    log.warning("%s hỏng: %s", c.ticker, e)
                if texts:
                    rows, d = price_normalize.normalize_code(c.organ_code, texts)
                    stats["dup_dates"] += d
                    if rows:
                        with engine.begin() as conn:
                            a = price_store.apply(conn, c.security_id, rows, _now_iso())
                            n, sample = price_store.raw_close_mismatches(
                                conn, [(c.security_id, min(r.trading_date for r in rows))])
                        stats["rows_sent"] += a["rows_sent"]
                        stats["rows_changed"] += a["rows_changed"]
                        stats["raw_close_mismatch"] += n
                        room = price_store.SAMPLE - len(stats["raw_close_mismatch_sample"])
                        stats["raw_close_mismatch_sample"].extend(sample[:max(room, 0)])
                    stats["pages"] += len(texts)
                stats["codes_done"] += 1
                stats["retries"] = f.retries
                if tickers is None:
                    stats["cursor"] = c.ticker
                stats["elapsed_s"] = round(time.monotonic() - t0)
                price_store.save_progress(engine, run_id, stats)
                if i % 20 == 0:
                    log.info("backfill %d/%d mã, %d trang, %d dòng đổi", i, len(todo), stats["pages"],
                             stats["rows_changed"])
                if deadline is not None and _wall_clock() >= deadline and i < len(todo):
                    stats["budget_hit"] = True
                    break
            else:
                stats["pass_complete"] = tickers is None       # hết danh sách, không vì ngân sách
        omo_store.close_run(engine, run_id, "success", stats)
        log.info("backfill xong: %s", stats)
        return 0
    except Exception as e:  # noqa: BLE001
        omo_store.close_run(engine, run_id, "failed", stats, error=f"{type(e).__name__}: {e}")
        log.exception("backfill thất bại")
        return 2
