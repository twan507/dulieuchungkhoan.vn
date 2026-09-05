"""`python -m etl yahoo` — 37 chỉ số quốc tế → asset.ohlc_daily. Spec lát 7."""
from __future__ import annotations

import time

from etl import series_job, yahoo_fetch, yahoo_normalize, yahoo_registry

SPEC = series_job.SourceSpec(job="global.yahoo", source=yahoo_registry.SOURCE, domains=("asset",),
                             guard_mode="ratio", log_name="yahoo", build=yahoo_registry.build,
                             fetch_all=yahoo_fetch.fetch_all, normalize=yahoo_normalize.bars,
                             supports_backfill=True, supports_intraday=True)


def run(keys=None, dry_run=False, backfill=False, intraday=False, get=None, sleep=time.sleep, now=None) -> int:
    return series_job.run(SPEC, keys=keys, dry_run=dry_run, backfill=backfill, intraday=intraday, get=get, sleep=sleep, now=now)
