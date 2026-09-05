"""Khuôn job chung cho 5 nguồn quốc tế (spec lát 7 §5.1) — y `wichart_job`, tham số hoá bằng `SourceSpec`.

Hợp đồng: `open_run` ngay trước `try`; `--keys` (theo `external_key`) = lượt con không guard, không đụng domain state,
registry vẫn nạp trọn; `dry_run` không ghi gì; guard từ chối ⇒ bằng chứng ở giao dịch riêng + `failed` + exit 1;
`KeyboardInterrupt` ⇒ `failed: dừng tay (Ctrl+C)`, exit 130; exception khác ⇒ exit 2."""
from __future__ import annotations

import logging
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable
from zoneinfo import ZoneInfo

import sqlalchemy as sa

from core.env import load_dotenv
from etl import omo_store, series_guard, series_store
from etl.registry import SeriesError, load_registry

VN = ZoneInfo("Asia/Ho_Chi_Minh")
MAX_DETAILS = 50


@dataclass
class SourceSpec:
    job: str
    source: str
    domains: tuple[str, ...]
    guard_mode: str
    log_name: str
    build: Callable[[], list]
    fetch_all: Callable[..., tuple[dict, dict, list, int, int]]   # (series, get, sleep, backfill) -> docs, texts, failed, calls, retries
    normalize: Callable[..., list]                                # (series, doc, now) -> list[Point] | list[Bar]; raise SeriesError
    supports_backfill: bool = False
    redact: Callable[[str], str] = staticmethod(lambda s: s)      # che khoá trong lỗi/log (FRED — khoá đi trong URL)


def _engine():
    url = os.environ.get("ETL_DATABASE_URL")
    if not url:
        raise RuntimeError("thiếu ETL_DATABASE_URL")
    return sa.create_engine(url, pool_pre_ping=True)


def _normalize_all(spec, series, docs, failed, now):
    t = series_guard.Tally(total=len(series))
    points: list = []
    bars: list = []
    for s in series:
        if s.external_key in failed:
            t.failed += 1
            t.details.append(f"{s.external_key} failed")
            continue
        try:
            out = spec.normalize(s, docs[s.external_key], now)
            (bars if s.shape == "ohlc" else points).extend(out)
            t.ok += 1
        except SeriesError as e:
            setattr(t, e.reason, getattr(t, e.reason) + 1)
            t.details.append(f"{s.external_key} {e.reason}: {e}")
    t.details = t.details[:MAX_DETAILS]
    return points, bars, t


def _apply_backfill_per_code(engine, points, bars, resolved) -> series_store.Written:
    """`--backfill`: một mã một giao dịch (spec §5.1) — một mã hỏng dừng lượt nhưng không kéo lùi
    các mã đã ghi và commit xong trước đó. Thứ tự xử lý theo `code` sắp xếp, để deterministic."""
    by_code: dict[str, dict] = {}
    for p in points:
        by_code.setdefault(p.code, {"points": [], "bars": []})["points"].append(p)
    for b in bars:
        by_code.setdefault(b.code, {"points": [], "bars": []})["bars"].append(b)
    w = series_store.Written()
    for code in sorted(by_code):
        group = by_code[code]
        with engine.begin() as conn:
            if group["points"]:
                w1 = series_store.apply(conn, group["points"], resolved)
                w.inserted += w1.inserted
                w.changed += w1.changed
                w.changes_sample.extend(w1.changes_sample)
            if group["bars"]:
                w2 = series_store.apply_ohlc(conn, group["bars"], resolved)
                w.inserted += w2.inserted
                w.changed += w2.changed
    return w


def run(spec: SourceSpec, keys=None, dry_run=False, backfill=False, get=None, sleep=time.sleep, now=None) -> int:
    logging.basicConfig(level=logging.INFO, stream=sys.stderr,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)      # URL FRED có khoá: không để httpx in request
    log = logging.getLogger(f"etl.{spec.log_name}")
    load_dotenv()
    now = now or datetime.now(timezone.utc)
    subset = keys is not None
    if backfill and not spec.supports_backfill:
        log.error("%s không có --backfill", spec.log_name)
        return 2
    try:
        engine = _engine()
    except RuntimeError as e:
        log.error("%s", e)
        return 2
    run_id = omo_store.open_run(engine, spec.job)
    try:
        registry = spec.build()
        series = registry
        if subset:
            known = {s.external_key for s in registry}
            unknown = sorted(set(keys) - known)
            if unknown:
                raise RuntimeError(f"key không có trong registry: {unknown}")
            series = [s for s in registry if s.external_key in set(keys)]
        docs, texts, failed, calls, retries = spec.fetch_all(series, get, sleep, backfill)
        points, bars, tally = _normalize_all(spec, series, docs, failed, now)
        verdict = series_guard.check(tally, spec.guard_mode) if not subset else series_guard.Verdict(ok=True)
        run_date = now.astimezone(VN).date()
        stats: dict = {"tally": vars(tally), "calls": calls, "retries": retries, "points": len(points), "bars": len(bars),
                       "run_date": run_date.isoformat()}
        for flag, on in (("subset", subset), ("dry_run", dry_run), ("backfill", backfill)):
            if on:
                stats[flag] = True
        if dry_run:
            stats["refused"] = verdict.reasons
            omo_store.close_run(engine, run_id, "success" if verdict.ok else "failed", stats,
                                error=None if verdict.ok else "guard refused (dry-run): " + "; ".join(verdict.reasons))
            log.info("%s dry-run: %s", spec.log_name, stats)
            return 0 if verdict.ok else 1
        if not verdict.ok:
            series_store.store_refusal_evidence(engine, spec.source, texts, run_id, verdict.reasons)
            omo_store.close_run(engine, run_id, "failed", stats, error="guard refused: " + "; ".join(verdict.reasons))
            log.error("%s từ chối: %s", spec.log_name, verdict.reasons)
            return 1
        if backfill:
            with engine.begin() as conn:
                resolved, reg_stats = load_registry(conn, registry, spec.source)     # registry TRỌN, riêng giao dịch
            w = _apply_backfill_per_code(engine, points, bars, resolved)             # rồi một mã một giao dịch
            stats.update({"registry": reg_stats, "inserted": w.inserted, "changed": w.changed,
                          "changes_sample": [[str(x) for x in c] for c in w.changes_sample]})
        else:
            with engine.begin() as conn:
                resolved, reg_stats = load_registry(conn, registry, spec.source)     # registry TRỌN, kể cả lượt con
                w1 = series_store.apply(conn, points, resolved)
                w2 = series_store.apply_ohlc(conn, bars, resolved)
            stats.update({"registry": reg_stats, "inserted": w1.inserted + w2.inserted, "changed": w1.changed + w2.changed,
                          "changes_sample": [[str(x) for x in c] for c in w1.changes_sample]})
        if not subset:
            stats["watermark"] = run_date.isoformat()
        omo_store.close_run(engine, run_id, "success", stats)      # close_run TRƯỚC, domain state SAU
        if not subset:
            series_store.upsert_domain_state(engine, spec.source, spec.domains, run_date.isoformat())
        log.info("%s xong: %s", spec.log_name, stats)
        return 0
    except KeyboardInterrupt:
        # Ctrl+C là cách dừng chính thức của cửa sổ task — sổ phải ghi lý do, không treo 'running' (khuôn price_job)
        omo_store.close_run(engine, run_id, "failed", error="dừng tay (Ctrl+C)")
        log.warning("%s dừng tay (Ctrl+C)", spec.log_name)
        return 130
    except Exception as e:                    # noqa: BLE001 — job biên ngoài: mọi lỗi vào etl_run
        err = spec.redact(f"{type(e).__name__}: {e}")
        omo_store.close_run(engine, run_id, "failed", error=err)
        log.exception("%s thất bại: %s", spec.log_name, err)
        return 2
    finally:
        engine.dispose()
