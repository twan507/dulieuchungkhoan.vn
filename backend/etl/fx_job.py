"""`python -m etl fx` — 6 cặp EUR/USD… từ một lời gọi Frankfurter → asset.price_daily. Spec lát 7."""
from __future__ import annotations

import time

from etl import fx_fetch, fx_normalize, fx_registry, series_job

SPEC = series_job.SourceSpec(job="global.ecb", source=fx_registry.SOURCE, domains=("asset",),
                             guard_mode="all_or_nothing", log_name="fx", build=fx_registry.build,
                             fetch_all=fx_fetch.fetch_all, normalize=fx_normalize.series_points)


def run(keys=None, dry_run=False, backfill=False, get=None, sleep=time.sleep, now=None) -> int:
    return series_job.run(SPEC, keys=keys, dry_run=dry_run, backfill=backfill, get=get, sleep=sleep, now=now)
