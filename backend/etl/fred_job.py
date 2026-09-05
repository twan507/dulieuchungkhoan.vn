"""`python -m etl fred` — 14 series → macro.observation (11) + asset.price_daily (3). Spec lát 7."""
from __future__ import annotations

import os
import time

from etl import fred_fetch, fred_normalize, fred_registry, series_job

SPEC = series_job.SourceSpec(job="global.fred", source=fred_registry.SOURCE, domains=("macro.indicator", "asset"),
                             guard_mode="all_or_nothing", log_name="fred", build=fred_registry.build,
                             fetch_all=fred_fetch.fetch_all, normalize=fred_normalize.series_points,
                             redact=lambda s: fred_fetch.redact(s, os.environ.get("FRED_API", "")))


def run(keys=None, dry_run=False, backfill=False, get=None, sleep=time.sleep, now=None) -> int:
    return series_job.run(SPEC, keys=keys, dry_run=dry_run, backfill=backfill, get=get, sleep=sleep, now=now)
