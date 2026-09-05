"""LBMA: mảng {d, v:[USD, GBP, EUR]} đo 2026-09-05; chỉ USD (v[0]) vào kho."""
import json
import os
import pathlib
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
import sqlalchemy as sa

from etl import lbma_fetch as lf
from etl import lbma_job as lj
from etl import lbma_normalize as ln
from etl import lbma_registry as lr
from etl.registry import SeriesError

FIX = pathlib.Path(__file__).parent / "fixtures" / "global"
GOLD = json.loads((FIX / "lbma-gold_pm-trimmed.json").read_text(encoding="utf-8"))
SILVER = json.loads((FIX / "lbma-silver-trimmed.json").read_text(encoding="utf-8"))
REG = {s.external_key: s for s in lr.build()}
NOW = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)


def test_registry_two_usd_fixings():
    s = lr.build()
    assert [(x.external_key, x.external_sub, x.code) for x in s] == [("gold_pm", "0", "gold.lbma"), ("silver", "0", "silver.lbma")]
    assert all(x.price_type == "fixing" and x.unit == "USD/oz" and x.quote_currency == "USD" and x.source == "lbma" for x in s)


def test_url_and_classify():
    assert lf.url("gold_pm") == "https://prices.lbma.org.uk/json/gold_pm.json"
    assert lf.classify(200, json.dumps(GOLD))[0] == "ok"
    assert lf.classify(200, '{"d": "x"}') == ("bad_shape", None)
    assert lf.classify(200, "[]") == ("bad_shape", None)
    assert lf.classify(502, "") == ("retry", None)


def test_usd_column_only_and_null_rows_skipped():
    pts = ln.series_points(REG["gold_pm"], GOLD, NOW)
    assert len(pts) == 32 and pts[0].obs_date == date(1968, 4, 1) and pts[0].value == Decimal("37.7")
    last = pts[-1]
    assert (last.obs_date, last.value, last.code, last.price_type) == (date(2026, 9, 4), Decimal("4415.4"), "gold.lbma", "fixing")
    assert ln.series_points(REG["silver"], SILVER, NOW)[-1].value == Decimal("66.835")
    doc = json.loads(json.dumps(GOLD))
    doc[-1]["v"][0] = None                                          # USD null ở ngày cuối ⇒ không dòng, ngày cuối lùi
    assert ln.series_points(REG["gold_pm"], doc, NOW)[-1].obs_date == date(2026, 9, 3)


def test_shape_stale_band():
    doc = json.loads(json.dumps(GOLD))
    doc[-1]["v"] = [4415.4, 3269.16]
    with pytest.raises(SeriesError) as e:
        ln.series_points(REG["gold_pm"], doc, NOW)
    assert e.value.reason == "shape"
    with pytest.raises(SeriesError) as e:
        ln.series_points(REG["gold_pm"], GOLD, datetime(2026, 9, 12, tzinfo=timezone.utc))
    assert e.value.reason == "stale"
    doc = json.loads(json.dumps(GOLD))
    doc[-1]["v"][0] = 44154.0
    with pytest.raises(SeriesError) as e:
        ln.series_points(REG["gold_pm"], doc, NOW)
    assert e.value.reason == "band"


def _cleanup(engine):
    with engine.begin() as c:
        c.execute(sa.text("DELETE FROM asset.price_daily WHERE asset_id IN (SELECT asset_id FROM asset.asset_external_id WHERE source='lbma')"))
        c.execute(sa.text("DELETE FROM staging.raw_payload WHERE source='lbma'"))
        c.execute(sa.text("DELETE FROM ops.etl_run WHERE job='global.lbma'"))
        c.execute(sa.text("DELETE FROM ops.data_domain_state WHERE source='lbma'"))
        c.execute(sa.text("DELETE FROM asset.asset_external_id WHERE source='lbma'"))
        c.execute(sa.text("DELETE FROM asset.asset WHERE code IN ('gold.lbma','silver.lbma')"))


@pytest.fixture()
def clean(migrated_engine, monkeypatch):
    monkeypatch.setenv("ETL_DATABASE_URL", os.environ["TEST_DATABASE_URL"])
    monkeypatch.setattr("etl.series_job.load_dotenv", lambda *a, **k: None)
    _cleanup(migrated_engine)
    yield migrated_engine
    _cleanup(migrated_engine)


def _get(u, t):
    name = u.rsplit("/", 1)[1].removesuffix(".json")
    return 200, json.dumps(GOLD if name == "gold_pm" else SILVER), {}


def test_job_two_calls_64_rows(clean):
    assert lj.run(get=_get, sleep=lambda s: None, now=NOW) == 0
    with clean.connect() as c:
        stats = c.execute(sa.text("SELECT stats FROM ops.etl_run WHERE job='global.lbma' ORDER BY run_id DESC LIMIT 1")).scalar()
        assert stats["calls"] == 2 and stats["inserted"] == 64 and stats["registry"]["asset"] == 2
        assert c.execute(sa.text("SELECT value FROM asset.price_daily p JOIN asset.asset a USING (asset_id)"
                                 " WHERE a.code='silver.lbma' AND obs_date='2026-09-04'")).scalar() == Decimal("66.835")
    assert lj.run(get=_get, sleep=lambda s: None, now=NOW) == 0
