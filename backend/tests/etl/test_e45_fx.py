"""ECB/Frankfurter: 7 cặp từ một lời gọi (thêm CNY, lát 7b); literal từ fixture 2026-09-05 và fx.md."""
import json
import os
import pathlib
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
import sqlalchemy as sa

from etl import fx_fetch as xf
from etl import fx_job as xj
from etl import fx_normalize as xn
from etl import fx_registry as xr
from etl.registry import SeriesError

FIX = pathlib.Path(__file__).parent / "fixtures" / "global"
DOC = json.loads((FIX / "ecb-2026-08.json").read_text(encoding="utf-8"))
REG = {s.external_key: s for s in xr.build()}
NOW = datetime(2026, 9, 3, 12, 0, tzinfo=timezone.utc)            # fixture kết thúc 08-31: trễ 3 ngày ≤ 6


def test_registry_seven_fx_assets_fixing():
    s = xr.build()
    assert [x.external_key for x in s] == ["EUR", "JPY", "GBP", "CAD", "SEK", "CHF", "CNY"]
    assert all(x.asset_class == "fx" and x.price_type == "fixing" and x.source == "ecb" and x.region == "eu" for x in s)
    assert REG["EUR"].code == "fx.usd_eur" and REG["EUR"].quote_currency == "EUR" and REG["EUR"].unit == "EUR/1 USD"
    assert REG["CNY"].code == "fx.usd_cny" and REG["CNY"].band == (Decimal(3), Decimal(15)) and REG["CNY"].region == "eu"


def test_url_is_the_new_host_with_seven_quotes():
    assert xf.URL == "https://api.frankfurter.dev/v1/1999-01-04..?from=USD&to=EUR,JPY,GBP,CAD,SEK,CHF,CNY"


def test_classify():
    assert xf.classify(200, json.dumps(DOC))[0] == "ok"
    assert xf.classify(200, '{"base":"EUR","rates":{}}') == ("bad_shape", None)      # base phải là USD
    assert xf.classify(301, "<html>") == ("retry", None)
    assert xf.classify(200, "{") == ("retry", None)


def test_eur_point_matches_fx_md_literal_and_direction_is_quote_per_usd():
    pts = xn.series_points(REG["EUR"], DOC, NOW)
    assert len(pts) == 22
    p = next(x for x in pts if x.obs_date == date(2026, 8, 14))
    assert (p.value, p.price_type, p.code, p.domain) == (Decimal("0.86453"), "fixing", "fx.usd_eur", "asset")
    assert next(x for x in xn.series_points(REG["JPY"], DOC, NOW) if x.obs_date == date(2026, 8, 14)).value == Decimal("159.01")


def test_missing_currency_on_last_day_is_shape_and_old_data_is_stale():
    doc = json.loads(json.dumps(DOC))
    del doc["rates"]["2026-08-31"]["SEK"]
    with pytest.raises(SeriesError) as e:
        xn.series_points(REG["SEK"], doc, NOW)
    assert e.value.reason == "shape"
    with pytest.raises(SeriesError) as e:
        xn.series_points(REG["EUR"], DOC, datetime(2026, 9, 10, tzinfo=timezone.utc))
    assert e.value.reason == "stale"


CODES = [s.code for s in xr.build()]


def _cleanup(engine):
    with engine.begin() as c:
        c.execute(sa.text("DELETE FROM asset.price_daily WHERE asset_id IN (SELECT asset_id FROM asset.asset_external_id WHERE source='ecb')"))
        c.execute(sa.text("DELETE FROM staging.raw_payload WHERE source='ecb'"))
        c.execute(sa.text("DELETE FROM ops.etl_run WHERE job='global.ecb'"))
        c.execute(sa.text("DELETE FROM ops.data_domain_state WHERE source='ecb'"))
        c.execute(sa.text("DELETE FROM asset.asset_external_id WHERE source='ecb'"))
        c.execute(sa.text("DELETE FROM asset.asset a WHERE a.code = ANY(:c)"
                          " AND NOT EXISTS (SELECT 1 FROM asset.asset_external_id x WHERE x.asset_id = a.asset_id)"), {"c": CODES})


@pytest.fixture()
def clean(migrated_engine, monkeypatch):
    monkeypatch.setenv("ETL_DATABASE_URL", os.environ["TEST_DATABASE_URL"])
    monkeypatch.setattr("etl.series_job.load_dotenv", lambda *a, **k: None)
    _cleanup(migrated_engine)
    yield migrated_engine
    _cleanup(migrated_engine)


def test_job_one_call_writes_154_fixing_rows(clean):
    calls = []
    assert xj.run(get=lambda u, t: (calls.append(u), (200, json.dumps(DOC), {}))[1], sleep=lambda s: None, now=NOW) == 0
    assert calls == [xf.URL]
    with clean.connect() as c:
        status, stats = c.execute(sa.text("SELECT status, stats FROM ops.etl_run WHERE job='global.ecb' ORDER BY run_id DESC LIMIT 1")).one()
        assert status == "success" and stats["registry"] == {"macro": 0, "asset": 7, "removed": 0} and stats["inserted"] == 154
        assert c.execute(sa.text("SELECT value FROM asset.price_daily p JOIN asset.asset a USING (asset_id)"
                                 " WHERE a.code='fx.usd_chf' AND obs_date='2026-08-14' AND price_type='fixing'")).scalar() == Decimal("0.81179")
        assert c.execute(sa.text("SELECT value FROM asset.price_daily p JOIN asset.asset a USING (asset_id)"
                                 " WHERE a.code='fx.usd_cny' AND obs_date='2026-08-14' AND price_type='fixing'")).scalar() == Decimal("6.7413")
        assert dict(c.execute(sa.text("SELECT domain, watermark FROM ops.data_domain_state WHERE source='ecb'")).all()) == {"asset": "2026-09-03"}


def test_job_refuses_when_the_single_call_fails(clean):
    assert xj.run(get=lambda u, t: (503, "", {}), sleep=lambda s: None, now=NOW) == 1
    with clean.connect() as c:
        stats = c.execute(sa.text("SELECT stats FROM ops.etl_run WHERE job='global.ecb' ORDER BY run_id DESC LIMIT 1")).scalar()
        assert stats["tally"]["failed"] == 7 and stats["calls"] == 4


def test_ecb_cny_reuses_the_asset_fred_created_and_fred_mapping_goes_away(clean):
    # Kho có sẵn asset fx.usd_cny do FRED tạo (ánh xạ (fred, DEXCHUS)) — lượt ECB phải dùng CÙNG asset_id, không tạo mới
    from etl.registry import Series, load_registry
    fred_cny = Series(source="fred", external_key="DEXCHUS", domain="asset", code="fx.usd_cny", name_vi="cũ", unit="CNY/1 USD",
                      freq="d", asset_class="fx", quote_currency="CNY", price_type="fixing", calendar="trading_days",
                      band=(Decimal(3), Decimal(15)), max_lag_days=12)
    with clean.begin() as c:
        c.execute(sa.text("DELETE FROM asset.asset_external_id WHERE source='fred' AND external_code='DEXCHUS'"))
        resolved, _ = load_registry(c, [fred_cny], "fred")
        aid = resolved["fx.usd_cny"].row_id
    assert xj.run(get=lambda u, t: (200, json.dumps(DOC), {}), sleep=lambda s: None, now=NOW) == 0
    with clean.connect() as c:
        assert c.execute(sa.text("SELECT asset_id FROM asset.asset WHERE code='fx.usd_cny'")).scalar() == aid
        assert c.execute(sa.text("SELECT count(*) FROM asset.asset_external_id WHERE asset_id=:a"), {"a": aid}).scalar() == 2
    with clean.begin() as c:                                   # registry FRED 14 series ⇒ ánh xạ (fred, DEXCHUS) bị xoá, asset và dữ liệu giữ
        from etl import fred_registry
        _, st = load_registry(c, fred_registry.build(), "fred")
    assert st["removed"] == 1
    with clean.connect() as c:
        assert c.execute(sa.text("SELECT count(*) FROM asset.asset WHERE code='fx.usd_cny'")).scalar() == 1
    with clean.begin() as c:
        c.execute(sa.text("DELETE FROM macro.indicator_source WHERE source='fred'"))
        c.execute(sa.text("DELETE FROM asset.asset_external_id WHERE source='fred'"))
        c.execute(sa.text("DELETE FROM macro.indicator WHERE code LIKE 'us.%'"))
        c.execute(sa.text("DELETE FROM asset.asset WHERE code IN ('dxy.broad','vix') OR (code='wti' AND NOT EXISTS (SELECT 1 FROM asset.asset_external_id x WHERE x.asset_id = asset.asset_id))"))
