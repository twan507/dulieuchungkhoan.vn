"""Một lượt `etl wichart`: registry → fetch 68 key → normalize → guard → apply (spec §5.1).

Khác lát 4–5: guard đánh giá TRƯỚC khi mở giao dịch ghi (chưa ghi gì nên không cần rollback);
bằng chứng từ chối ở giao dịch riêng. `--keys` = lượt con: không guard, không đụng domain state.
`--intraday` = lượt trên tập tần suất ngày: guard như lượt trọn, KHÔNG đẩy mốc nước (lượt trọn hằng ngày giữ),
không lưu body.
"""
from __future__ import annotations

import logging
import os
import sys
import time
from datetime import datetime

import sqlalchemy as sa

from core.env import load_dotenv
from etl import omo_store, wichart_fetch, wichart_guard, wichart_normalize, wichart_registry, wichart_store
from etl.wichart_fetch import BadShape, FetchError
from etl.wichart_normalize import VN, SeriesError

log = logging.getLogger("etl.wichart")
JOB = wichart_store.JOB
MAX_ERRORS_IN_STATS = 50


def intraday_series(registry):
    """Lượt --intraday = mọi series tần suất NGÀY (47 key: 43 hang_hoa + dhtg, lsdh, lslnh, lshd) — spec 7b §4.4:
    tiêu chí là `freq`, không phải danh sách tay; nhóm tháng/quý/năm chỉ chạy ở lượt trọn hằng ngày."""
    return [s for s in registry if s.freq == "d"]


def _engine():
    url = os.environ.get("ETL_DATABASE_URL")
    if not url:
        raise RuntimeError("thiếu ETL_DATABASE_URL")
    return sa.create_engine(url, pool_pre_ping=True)


def _fetch_all(groups, get, sleep):
    docs, texts, failed, bad = {}, {}, [], []
    with wichart_fetch.open_fetcher(get=get, sleep=sleep) as f:
        for key, group in groups:
            try:
                docs[key], texts[key] = f.fetch_one(key, group)
            except BadShape as e:
                bad.append(key)
                log.warning("%s", e)
            except FetchError as e:
                failed.append(key)
                log.warning("%s", e)
        return docs, texts, failed, bad, f.calls, f.retries


def _normalize_all(series, docs, failed, bad):
    t = wichart_guard.Tally(series_total=len(series))
    points, errors = [], []
    for s in series:
        if s.key in failed:
            continue                                   # key hỏng: không tính vào hình dạng
        if s.key in bad:
            t.series_shape += 1
            continue
        try:
            points.extend(wichart_normalize.series_points(s, docs[s.key]["chart"]["series"]))
            t.series_ok += 1
        except SeriesError as e:
            errors.append(f"{s.key}[{s.idx}] {e.reason}: {e}")
            if e.reason == "shape":
                t.series_shape += 1
            elif e.reason == "freq":
                t.series_freq += 1
            else:
                t.series_band += 1
    return points, t, errors


def run(keys=None, dry_run=False, intraday=False, get=None, sleep=time.sleep) -> int:
    logging.basicConfig(level=logging.INFO, stream=sys.stderr,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    load_dotenv()
    subset = keys is not None
    try:
        engine = _engine()
    except RuntimeError as e:
        log.error("%s", e)
        return 2
    run_id = omo_store.open_run(engine, JOB)
    try:
        registry = wichart_registry.build()                     # hợp đồng khởi động: lệch là chết trước fetch
        if subset and intraday:
            raise RuntimeError("--keys và --intraday loại trừ nhau")
        series = registry
        if subset:
            known = {s.key for s in registry}
            unknown = sorted(set(keys) - known)
            if unknown:
                raise RuntimeError(f"key không có trong registry: {unknown}")
            series = [s for s in registry if s.key in set(keys)]
        elif intraday:
            series = intraday_series(registry)
        groups = wichart_registry.key_groups(series)

        docs, texts, failed, bad, calls, retries = _fetch_all(groups, get, sleep)
        points, tally, errors = _normalize_all(series, docs, failed, bad)
        tally.keys_total, tally.keys_failed, tally.keys_bad_shape = len(groups), len(failed), len(bad)
        verdict = wichart_guard.check(tally) if not subset else wichart_guard.Verdict(ok=True)
        run_date = datetime.now(VN).date()
        stats = {"tally": vars(tally), "calls": calls, "retries": retries, "points": len(points),
                 "run_date": run_date.isoformat(), "errors": errors[:MAX_ERRORS_IN_STATS],
                 "failed_keys": failed, "bad_shape_keys": bad}
        if subset:
            stats["subset"] = True
        if intraday:
            stats["intraday"] = True
        if dry_run:
            stats["dry_run"] = True
            stats["refused"] = verdict.reasons
            omo_store.close_run(engine, run_id, "success" if verdict.ok else "failed", stats,
                                error=None if verdict.ok else "guard refused (dry-run): " + "; ".join(verdict.reasons))
            log.info("wichart dry-run: %s", stats)
            return 0 if verdict.ok else 1
        if not verdict.ok:
            wichart_store.store_refusal_evidence(engine, texts, run_id, verdict)
            omo_store.close_run(engine, run_id, "failed", stats, error="guard refused: " + "; ".join(verdict.reasons))
            log.error("wichart từ chối: %s", verdict.reasons)
            return 1

        with engine.begin() as conn:
            resolved, reg_stats = wichart_store.load_registry(conn, registry)   # registry TRỌN, kể cả lượt con/intraday
            written = wichart_store.apply(conn, points, resolved)
            wichart_store.seed_series_break(conn)
            # Lượt intraday KHÔNG lưu body khi hash đổi: 47 key × 288 lượt/ngày × ~30 KB — đúng lý do lát 7 bỏ lưu body (ruling 7b)
            stored = 0 if intraday else sum(1 for key, text in texts.items() if wichart_store.store_payload_if_changed(conn, key, text, run_id))
        stats.update({"registry": reg_stats, "inserted": written.inserted, "changed": written.changed,
                      "payloads_stored": stored})
        if not subset and not intraday:
            stats["watermark"] = run_date.isoformat()
        omo_store.close_run(engine, run_id, "success", stats)      # close_run TRƯỚC, domain state SAU
        if not subset and not intraday:
            wichart_store.upsert_domain_state(engine, run_date.isoformat())
        log.info("wichart xong: %s", stats)
        return 0
    except KeyboardInterrupt:
        # Ctrl+C là cách dừng chính thức của cửa sổ task — sổ phải ghi lý do, không treo 'running' (khuôn price_job)
        omo_store.close_run(engine, run_id, "failed", error="dừng tay (Ctrl+C)")
        log.warning("wichart dừng tay (Ctrl+C)")
        return 130
    except Exception as e:                    # noqa: BLE001 — job biên ngoài: mọi lỗi vào etl_run
        omo_store.close_run(engine, run_id, "failed", error=f"{type(e).__name__}: {e}")
        log.exception("wichart thất bại")
        return 2
    finally:
        engine.dispose()
