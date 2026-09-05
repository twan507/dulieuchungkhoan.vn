"""`python -m etl lbma` — vàng/bạc fixing LBMA (USD) → asset.price_daily. Spec lát 7."""
from __future__ import annotations

import time

from etl import lbma_fetch, lbma_normalize, lbma_registry, series_job

SPEC = series_job.SourceSpec(job="global.lbma", source=lbma_registry.SOURCE, domains=("asset",),
                             guard_mode="all_or_nothing", log_name="lbma", build=lbma_registry.build,
                             fetch_all=lbma_fetch.fetch_all, normalize=lbma_normalize.series_points)


def run(keys=None, dry_run=False, backfill=False, get=None, sleep=time.sleep, now=None) -> int:
    return series_job.run(SPEC, keys=keys, dry_run=dry_run, backfill=backfill, get=get, sleep=sleep, now=now)
