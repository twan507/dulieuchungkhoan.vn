"""`python -m etl news` — thu 47 feed + 6 crawl → news.* (spec lát 8 §5.2). Khuôn `series_job`: open_run ngay trước try,
Ctrl+C ⇒ failed 'dừng tay (Ctrl+C)' exit 130; KHÔNG từ chối cả lượt (tin bỏ lỡ là mất thật) — tally + warnings.
--loop: mỗi vòng một etl_run, nhịp 300 s, sitemap mỗi 3 vòng; --sources: lượt con không đụng domain state.
9b-2: bài mới còn qua một khoá dedupe nữa — tiêu đề GẦN GIỐNG (pg_trgm 0,6, khác báo, 48 giờ) ⇒ merged_near.
8b: `--backfill-sitemap --source`, kỳ tháng/ngày theo `SITEMAPS`, job `news.backfill_sitemap:<source>` (TinnhanhCK đọc thêm tên cũ)."""
from __future__ import annotations

import calendar
import dataclasses
import logging
import os
import re
import sys
import time
from collections.abc import Iterable
from datetime import date, datetime, timedelta, timezone

import sqlalchemy as sa

from core.clock import VN, today_vn
from core.env import load_dotenv
from etl import news_extract, news_fetch, news_registry, news_store, news_tag, omo_store
from etl.news_parse import PARSERS, Item, ParseError
from etl.price_job import _next_open

log = logging.getLogger("etl.news")
JOB = "news.collect"
LEGACY_JOB = "news.backfill_sitemap"          # lát 8: chỉ TinnhanhCK, một job — 8b đọc thêm để không mất con trỏ
CYCLE_SECONDS = 300
SITEMAP_EVERY = 3
MAX_FAILED_RATE = 0.20
MAX_REFUSED_RATE = 0.05
MAX_CONSECUTIVE_FAILED = 10
STALE_DAYS = 7
MONTH = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


class SourceDown(Exception):
    """10 bài liên tiếp hỏng — nguồn hoặc mạng chết, dừng lượt (khuôn backfill giá)."""

    def __init__(self, msg: str, stats: dict):
        self.stats = stats
        super().__init__(msg)


def _engine():
    url = os.environ.get("ETL_DATABASE_URL")
    if not url:
        raise RuntimeError("thiếu ETL_DATABASE_URL")
    return sa.create_engine(url, pool_pre_ping=True)


def _empty_stats(now_vn, cycle):
    return {"sources_total": 0, "lists_ok": 0, "lists_failed": 0, "lists_stored": 0, "items": 0, "seen": 0, "merged_url": 0,
            "merged_title": 0, "merged_near": 0, "new": 0, "skipped_refused": 0, "stale_feeds": [], "warnings": [], "calls": 0, "retries": 0,
            "run_date": now_vn.date().isoformat(), "cycle": cycle}


def _newest(items):
    ts = [it.published_at for it in items if it.published_at]
    return max(ts) if ts else None


def merge_items(items: Iterable[Item]) -> dict[str, Item]:
    """C1 (spec §4.6-III): TinnhanhCK sitemap chỉ VÁ LỖ — không được thắng bản đã có nhóm từ trang chuyên mục.
    Thuần, không phụ thuộc thứ tự đưa vào: bản có `group_from_feed` luôn thắng; nếu bản thắng thiếu `published_at`
    mà bản thua có, giữ lại `published_at`/`published_at_src` của bản thua (không mất ngày chỉ vì đổi bản thắng)."""
    out: dict[str, Item] = {}
    for it in items:
        cu = it.canonical_url
        old = out.get(cu)
        if old is None:
            out[cu] = it
            continue
        if old.group_from_feed is None and it.group_from_feed is not None:
            new = it
            if new.published_at is None and old.published_at is not None:
                new = dataclasses.replace(new, published_at=old.published_at, published_at_src=old.published_at_src)
            out[cu] = new
    return out


def collect(engine, registry, *, run_id, now, dry_run, subset, cycle, get, sleep, rng) -> dict:
    now_vn = now.astimezone(VN)
    st = _empty_stats(now_vn, cycle)
    st["sources_total"] = len(registry)
    item_list: list = []
    ok_sources: set[str] = set()
    with news_fetch.open_news_fetcher(get=get, sleep=sleep, rng=rng) as f:
        for s in registry:
            if s.backfill_only:                                   # 8b: BNews/NguoiQuanSat sitemap chỉ dùng ở backfill
                continue
            if s.kind == "sitemap" and cycle % SITEMAP_EVERY != 0:
                continue
            if s.kind == "sitemap":                             # khoá kỳ theo đơn vị của nguồn (tháng/ngày), không giả định tháng
                key_fmt = "%Y-%m" if news_registry.SITEMAPS[s.name].period == "month" else "%Y-%m-%d"
                url = news_registry.sitemap_url(s.name, now_vn.strftime(key_fmt))
            else:
                url = s.url
            try:
                text = f.fetch_one(url, f"{s.name}/{s.feed_slug}")[1]
                parsed = PARSERS[s.kind](text, s)
            except (news_fetch.BadShape, news_fetch.FetchError, ParseError) as e:
                st["lists_failed"] += 1
                log.warning("%s", e)
                continue
            st["lists_ok"] += 1
            ok_sources.add(s.name)
            if not dry_run:
                with engine.begin() as c:
                    if news_store.store_list_if_changed(c, s.name, url, text, run_id, "text" if s.kind in ("rss", "sitemap") else "html"):
                        st["lists_stored"] += 1
            newest = _newest(parsed)
            if s.kind == "rss" and newest and now - newest > timedelta(days=STALE_DAYS):
                st["stale_feeds"].append(f"{s.name}/{s.feed_slug}")
            item_list.extend(parsed)
        items = merge_items(item_list)
        st["items"] = len(items)
        with engine.connect() as c:
            seen = news_store.Seen.load(c, now)
            listed = news_store.load_listed(c)
        if not dry_run:
            st.update({"articles_ok": 0, "articles_failed": 0, "refused": 0, "tickers_url": 0, "tickers_lookup": 0})
        for it in items.values():
            decision, aid = seen.decide(it, now)
            if decision == "seen":
                st["seen"] += 1
                continue
            if decision == "refused_recent":              # §4.6-VII: đã từ chối gần đây — đừng tải lại, đừng ghi bằng chứng lại
                st["skipped_refused"] += 1
                continue
            if decision in ("merge_url", "merge_title"):
                st[decision.replace("merge_", "merged_")] += 1
                if not dry_run:
                    with engine.begin() as c:
                        news_store.add_source(c, aid, it.source, it.url)
                    seen.urls.add(it.url)
                continue
            if not dry_run:                       # 9b-2: gộp "cùng chuyện, khác tít" (pg_trgm 0,6 — news_store.find_near_duplicate)
                with engine.connect() as c:
                    near = news_store.find_near_duplicate(c, it.title, it.published_at or now, it.source)
                if near is not None:
                    st["merged_near"] += 1
                    with engine.begin() as c:
                        news_store.add_source(c, near, it.source, it.url)
                    seen.urls.add(it.url)
                    continue
            st["new"] += 1
            if dry_run:
                seen.remember(it, -1, now)
                continue
            # C2 (§4.5): MỘT bài hỏng không được giết cả vòng — bọc toàn bộ fetch → extract → tag → insert.
            # KeyboardInterrupt không kế thừa Exception nên vẫn thoát được giữa chừng.
            try:
                html_text = f.fetch_one(it.url, it.source)[1]
                if len(html_text.encode("utf-8")) < news_fetch.ARTICLE_MIN_BYTES:
                    st["refused"] += 1
                    with engine.begin() as c:
                        news_store.store_refused(c, it.source, it.url, html_text, "soft404", run_id)
                    seen.refused.add(it.url)
                    continue
                try:
                    ext = news_extract.extract(html_text, it.rule)
                except news_extract.ExtractError as e:
                    st["refused"] += 1
                    with engine.begin() as c:
                        news_store.store_refused(c, it.source, it.url, html_text, e.reason, run_id)
                    seen.refused.add(it.url)
                    continue
                tickers: list[tuple[str, str, int]] = []
                if it.group_from_feed == 3:
                    for t in news_tag.tickers_from_url(it.url):
                        if t in listed:
                            tickers.append((t, "url", listed[t]))
                            st["tickers_url"] += 1
                    for t in news_tag.tickers_lookup(ext.title, ext.sapo, listed):
                        tickers.append((t, "lookup", listed[t]))
                        st["tickers_lookup"] += 1
                with engine.begin() as c:
                    aid, _inserted = news_store.insert_article(c, it, ext, fetched_at=now, tickers=tickers)
                seen.remember(it, aid, now)
                st["articles_ok"] += 1
            except (news_fetch.BadShape, news_fetch.FetchError) as e:
                st["articles_failed"] += 1
                log.warning("%s: %s", type(e).__name__, it.url)
            except Exception as e:                        # noqa: BLE001 — biên một bài, không để giết cả vòng (§4.5)
                st["articles_failed"] += 1
                log.warning("%s: %s", type(e).__name__, it.url)
        st["calls"], st["retries"] = f.calls, f.retries_done
    lists_total = st["lists_ok"] + st["lists_failed"]
    if lists_total and st["lists_failed"] / lists_total > MAX_FAILED_RATE:
        st["warnings"].append(f"feed/danh sách hỏng {st['lists_failed']}/{lists_total} > {MAX_FAILED_RATE:.0%}")
    if not dry_run and st["new"] and st["refused"] / st["new"] > MAX_REFUSED_RATE:
        st["warnings"].append(f"bóc từ chối {st['refused']}/{st['new']} > {MAX_REFUSED_RATE:.0%}")
    if st["stale_feeds"]:
        st["warnings"].append(f"feed im > {STALE_DAYS} ngày: {st['stale_feeds']}")
    st["_ok_sources"] = sorted(ok_sources)
    if subset:
        st["subset"] = True
    if dry_run:
        st["dry_run"] = True
    return st


def _one_cycle(engine, registry, *, subset, dry_run, cycle, get, sleep, now, rng) -> int:
    run_id = omo_store.open_run(engine, JOB)
    try:
        st = collect(engine, registry, run_id=run_id, now=now, dry_run=dry_run, subset=subset, cycle=cycle, get=get, sleep=sleep, rng=rng)
        ok_sources = set(st.pop("_ok_sources"))
        if not subset and not dry_run:
            st["watermark"] = st["run_date"]
        omo_store.close_run(engine, run_id, "success", st)
        if not subset and not dry_run:
            news_store.upsert_domain_state(engine, ok_sources, st["run_date"])
        log.info("news cycle %s: items %s · new %s · merged %s/%s/%s · seen %s · refused %s · warnings %s",
                 cycle, st["items"], st["new"], st["merged_url"], st["merged_title"], st["merged_near"], st["seen"], st.get("refused", "-"), st["warnings"])
        return 0
    except KeyboardInterrupt:
        omo_store.close_run(engine, run_id, "failed", error="dừng tay (Ctrl+C)")
        log.warning("news dừng tay (Ctrl+C)")
        return 130
    except Exception as e:                    # noqa: BLE001 — job biên ngoài
        omo_store.close_run(engine, run_id, "failed", error=f"{type(e).__name__}: {e}")
        log.exception("news thất bại")
        return 2


def run(sources=None, dry_run=False, loop=False, minutes=None, get=None, sleep=time.sleep, now=None, rng=None, clock=time.monotonic,
        classify_per_cycle: int | None = None) -> int:
    """`classify_per_cycle`: sau mỗi vòng thu thập, phân loại tối đa N bài mới (job `news.classify` riêng, có quota guard).
    MẶC ĐỊNH TẮT — lưới chỉ chạy khi người vận hành truyền `--classify N` (chủ dự án chưa bật live, 2026-09-06)."""
    logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    load_dotenv()
    try:
        engine = _engine()
        registry = news_registry.build()
        if sources is not None:
            unknown = sorted(set(sources) - set(news_registry.SOURCES))
            if unknown:
                raise RuntimeError(f"báo không có trong registry: {unknown}")
            registry = [s for s in registry if s.name in set(sources)]
    except (RuntimeError, news_registry.RegistryError) as e:
        log.error("%s", e)
        return 2
    subset = sources is not None
    t0 = clock()
    cycle = 0
    try:
        while True:
            started = clock()
            rc = _one_cycle(engine, registry, subset=subset, dry_run=dry_run, cycle=cycle,
                            get=get, sleep=sleep, now=now or datetime.now(timezone.utc), rng=rng)
            if rc != 0 or not loop:
                return rc
            if classify_per_cycle:
                from etl import news_classify
                crc = news_classify.run(limit=classify_per_cycle)      # sổ riêng `news.classify`; hết quota ⇒ quota_stop, không giết vòng thu thập
                if crc != 0:
                    log.warning("classify sau vòng %s trả mã %s — vòng thu thập vẫn tiếp tục", cycle, crc)
            cycle += 1
            if minutes is not None:
                # I5: --minutes là TRẦN tổng thời gian chạy, không phải "thêm tối đa một vòng + một nhịp đầy" —
                # nhịp ngủ cuối cùng phải cắt ngắn còn đúng phần thời gian còn lại trong ngân sách.
                remaining = minutes * 60 - (clock() - t0)
                if remaining <= 0:
                    return 0
                nap = min(max(0.0, CYCLE_SECONDS - (clock() - started)), remaining)
            else:
                nap = max(0.0, CYCLE_SECONDS - (clock() - started))
            try:
                sleep(nap)
            except KeyboardInterrupt:
                log.warning("news dừng tay (Ctrl+C) giữa hai vòng")
                return 130
    finally:
        engine.dispose()


def job_name(source: str) -> str:
    return f"news.backfill_sitemap:{source}"


def periods_desc(source: str, from_month: str, to_month: str, today: date | None = None) -> list[str]:
    """Khoá kỳ đi LÙI: nguồn tháng 'YYYY-MM'; nguồn ngày 'YYYY-MM-DD' mọi ngày của các tháng đó, không vượt hôm nay (VN)."""
    if not (MONTH.match(from_month) and MONTH.match(to_month)):
        raise ValueError(f"tháng phải dạng YYYY-MM: {from_month!r}, {to_month!r}")
    y, m = int(to_month[:4]), int(to_month[5:])
    months = []
    while f"{y:04d}-{m:02d}" >= from_month:
        months.append(f"{y:04d}-{m:02d}")
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    today = today or today_vn()
    months = [ym for ym in months if ym <= today.strftime("%Y-%m")]       # không sinh kỳ tương lai (cả nguồn tháng lẫn ngày)
    if news_registry.SITEMAPS[source].period == "month":
        return months
    out = []
    for ym in months:
        yy, mm = int(ym[:4]), int(ym[5:])
        for dd in range(calendar.monthrange(yy, mm)[1], 0, -1):
            d = date(yy, mm, dd)
            if d <= today:
                out.append(d.isoformat())
    return out


def load_cursor(engine, source: str) -> str | None:
    jobs = [job_name(source)] + ([LEGACY_JOB] if source == "tinnhanhck" else [])
    with engine.connect() as c:
        return c.execute(sa.text(
            "SELECT stats->>'cursor' FROM ops.etl_run WHERE job = ANY(:j) AND stats->>'cursor' IS NOT NULL"
            " ORDER BY run_id DESC LIMIT 1"), {"j": jobs}).scalar()


def backfill_sitemap(engine, source, periods, *, run_id, max_minutes, stop_before_open, get, sleep, now, rng, clock) -> dict:
    t0 = clock()
    deadline_s = max_minutes * 60 if max_minutes is not None else None
    stop_at = _next_open(datetime.now(VN)) if stop_before_open else None
    st = {"source": source, "period_unit": news_registry.SITEMAPS[source].period, "cursor": None, "periods_done": [], "periods_failed": [],
          "period": None, "urls_in_sitemap": 0, "skipped_seen": 0, "skipped_refused": 0, "articles_ok": 0, "articles_failed": 0,
          "refused": 0, "budget_hit": False, "calls": 0, "retries": 0, "stop_at": stop_at.isoformat(timespec="minutes") if stop_at else None}
    try:
        with engine.connect() as c:
            seen = news_store.Seen.load(c, now)
        src = news_registry.Source(source, "sitemap", news_registry.SITEMAPS[source].url, None, "sitemap")
        streak = 0
        frozen = False   # spec 8b §4.2-V: kỳ hỏng ⇒ đóng băng con trỏ TRƯỚC kỳ đó — không tổ hợp --from/--to nào bỏ qua
                          # được kỳ hỏng nếu con trỏ lỡ vượt qua nó (WAF NguoiQuanSat 403 chập chờn, 31 kỳ/tháng).

        def _over_budget() -> bool:
            return (deadline_s is not None and clock() - t0 >= deadline_s) or (stop_at is not None and datetime.now(VN) >= stop_at)

        with news_fetch.open_news_fetcher(get=get, sleep=sleep, rng=rng) as f:
            for key in periods:
                st["period"] = key
                try:
                    text = f.fetch_one(news_registry.sitemap_url(source, key), f"sitemap {source} {key}")[1]
                    items = PARSERS["sitemap"](text, src)
                except (news_fetch.BadShape, news_fetch.FetchError, ParseError) as e:
                    # I2: kỳ hỏng (503/XML rách…) không được làm mất stats/cursor của các kỳ khác — ghi nhận rồi qua kỳ
                    # sau; KHÔNG đếm vào streak cầu chì (đó là cho lỗi BÀI liên tiếp, không phải lỗi TRANG SITEMAP kỳ).
                    st["periods_failed"].append(key)
                    log.warning("%s", e)
                    frozen = True
                    continue
                st["urls_in_sitemap"] += len(items)
                for it in items:
                    if it.url in seen.urls or it.canonical_url in seen.canon:
                        st["skipped_seen"] += 1
                    elif it.url in seen.refused or it.canonical_url in seen.refused:   # §4.6-VII
                        st["skipped_refused"] += 1
                    else:
                        try:
                            html_text = f.fetch_one(it.url, source)[1]
                            if len(html_text.encode("utf-8")) < news_fetch.ARTICLE_MIN_BYTES:
                                raise news_fetch.BadShape("soft404")
                            ext = news_extract.extract(html_text, it.rule)
                        except (news_fetch.BadShape, news_fetch.FetchError) as e:
                            st["articles_failed"] += 1
                            streak += 1
                            log.warning("%s", e)
                            if streak >= MAX_CONSECUTIVE_FAILED:
                                st["calls"], st["retries"] = f.calls, f.retries_done
                                raise SourceDown(f"{streak} bài liên tiếp hỏng — nguồn hoặc mạng chết, dừng lượt", st) from e
                        except news_extract.ExtractError as e:
                            st["refused"] += 1
                            with engine.begin() as c:
                                news_store.store_refused(c, source, it.url, html_text, e.reason, run_id)
                            seen.refused.add(it.url)
                        else:
                            streak = 0
                            with engine.begin() as c:
                                aid, _inserted = news_store.insert_article(c, it, ext, fetched_at=now, tickers=[])
                            seen.remember(it, aid, now)
                            st["articles_ok"] += 1
                    if _over_budget():
                        st["budget_hit"] = True
                        break
                if st["budget_hit"]:
                    break
                st["periods_done"].append(key)
                if not frozen:
                    st["cursor"] = key
            st["calls"], st["retries"] = f.calls, f.retries_done
        return st
    except Exception as e:                    # noqa: BLE001 — I2: mọi exception thoát khỏi hàm này mang theo st đã tích luỹ
        e.stats = st
        raise


def run_backfill(from_month, to_month=None, max_minutes=None, stop_before_open=False, source="tinnhanhck",
                 get=None, sleep=time.sleep, now=None, rng=None, clock=time.monotonic) -> int:
    logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    load_dotenv()
    now = now or datetime.now(timezone.utc)
    to_month = to_month or now.astimezone(VN).strftime("%Y-%m")
    engine = None
    try:
        if source not in news_registry.SITEMAPS:
            raise ValueError(f"--source phải là một trong {sorted(news_registry.SITEMAPS)}, nhận {source!r}")
        engine = _engine()
        periods = periods_desc(source, from_month, to_month, today=now.astimezone(VN).date())
        cursor = load_cursor(engine, source)
        if cursor and periods and cursor <= periods[0]:           # nối sau kỳ đã xong (lùi dần)
            filtered = [p for p in periods if p < cursor]
            # cursor == kỳ đầu VÀ periods chỉ có đúng kỳ đó (không có kỳ nào cũ hơn để lọc ra) ⇒ chạy lại đúng kỳ đó
            # (khoảng --from/--to chỉ xin đúng một kỳ đã xong); nếu còn kỳ cũ hơn (spec 8b §4.2-V: con trỏ đóng băng
            # TRƯỚC kỳ hỏng, có thể trùng periods[0]) thì lọc bình thường — bỏ đúng kỳ đã xong, giữ các kỳ cũ hơn.
            if filtered or len(periods) > 1:
                periods = filtered
        if not periods:
            log.info("%s: con trỏ %s đã qua --from %s — không còn gì để làm", source, cursor, from_month)
            engine.dispose()
            return 0
    except (RuntimeError, ValueError) as e:
        log.error("%s", e)
        if engine is not None:                     # lỗi sau khi đã mở engine (tham số sai) — đừng rò pool
            engine.dispose()
        return 2
    run_id = omo_store.open_run(engine, job_name(source))
    try:
        st = backfill_sitemap(engine, source, periods, run_id=run_id, max_minutes=max_minutes, stop_before_open=stop_before_open,
                              get=get, sleep=sleep, now=now, rng=rng, clock=clock)
        omo_store.close_run(engine, run_id, "success", st)
        log.info("news backfill xong: %s", st)
        return 0
    except SourceDown as e:
        omo_store.close_run_refused(engine, run_id, str(e), e.stats)
        log.error("%s", e)
        return 1
    except KeyboardInterrupt:
        omo_store.close_run(engine, run_id, "failed", error="dừng tay (Ctrl+C)")
        return 130
    except Exception as e:                    # noqa: BLE001
        omo_store.close_run(engine, run_id, "failed", getattr(e, "stats", None), error=f"{type(e).__name__}: {e}")
        log.exception("news backfill thất bại")
        return 2
    finally:
        engine.dispose()
