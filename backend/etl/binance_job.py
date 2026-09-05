"""`python -m etl binance` — PAXG + 10 coin → asset.ohlc_daily. Spec lát 7."""
from __future__ import annotations

import time

from etl import binance_fetch, binance_normalize, binance_registry, series_job

SPEC = series_job.SourceSpec(job="global.binance", source=binance_registry.SOURCE, domains=("asset",),
                             guard_mode="all_or_nothing", log_name="binance", build=binance_registry.build,
                             fetch_all=binance_fetch.fetch_all, normalize=binance_normalize.bars,
                             supports_backfill=True, supports_intraday=True)


def run(keys=None, dry_run=False, backfill=False, intraday=False, get=None, sleep=time.sleep, now=None) -> int:
    return series_job.run(SPEC, keys=keys, dry_run=dry_run, backfill=backfill, intraday=intraday, get=get, sleep=sleep, now=now)
