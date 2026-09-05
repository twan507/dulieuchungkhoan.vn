"""FRED: registry 15 series, classify, normalize từ fixture thật 2026-09-05, job trọn vòng với `get` giả.
Expected là literal đọc tay từ fixture/fred.md — không tính lại theo code. Khoá KHÔNG được lộ (Bẫy 7)."""
import json
import logging
import os
import pathlib
from datetime import date, datetime, timezone
from decimal import Decimal

import httpx
import pytest
import sqlalchemy as sa

from etl import fred_fetch as ff
from etl import fred_job as fj
from etl import fred_normalize as fn
from etl import fred_registry as fr
from etl.registry import SeriesError

FIX = pathlib.Path(__file__).parent / "fixtures" / "global"
REG = {s.external_key: s for s in fr.build()}
NOW = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)
KEY = "ZZTESTKEY0000000000000000000000x"


def _doc(name):
    return json.loads((FIX / f"fred-{name}-tail.json").read_text(encoding="utf-8"))


def test_registry_has_15_series_split_11_macro_4_asset_with_spec_codes():
    s = fr.build()
    assert len(s) == 15 and sum(1 for x in s if x.domain == "macro") == 11
    assert REG["DCOILWTICO"].code == "wti" and REG["DCOILWTICO"].price_type == "spot" and REG["DCOILWTICO"].max_lag_days == 10
    assert REG["DTWEXBGS"].price_type == "close" and REG["DTWEXBGS"].code == "dxy.broad" and REG["DTWEXBGS"].max_lag_days == 12
    assert REG["DEXCHUS"].price_type == "fixing" and REG["DEXCHUS"].quote_currency == "CNY" and REG["DEXCHUS"].asset_class == "fx"
    assert REG["PAYEMS"].scale == Decimal(1000) and REG["PAYEMS"].unit == "người" and REG["PAYEMS"].freq == "m"
    assert REG["DGS10"].code == "us.yield.10y" and REG["DGS10"].region == "us" and REG["DGS10"].band == (Decimal(-1), Decimal(25))
    assert all(x.source == "fred" for x in s) and len({x.code for x in s}) == 15


def test_classify_400_is_bad_shape_and_xml_body_is_bad_shape():
    assert ff.classify(400, '{"error_code":400,"error_message":"Bad Request."}') == ("bad_shape", None)
    assert ff.classify(200, "<?xml version='1.0'?><observations/>") == ("bad_shape", None)
    assert ff.classify(503, "") == ("retry", None)
    assert ff.classify(200, '{"observations": []}')[0] == "ok"
    assert ff.classify(200, '{"seriess": []}') == ("bad_shape", None)


def test_dot_values_are_skipped_and_latest_value_is_literal_from_fixture():
    pts = fn.series_points(REG["DGS10"], _doc("DGS10"), NOW)
    assert len(pts) == 97                                              # 100 − 3 điểm "."
    assert {p.obs_date for p in pts}.isdisjoint({date(2026, 7, 3), date(2026, 6, 19), date(2026, 5, 25)})
    last = max(pts, key=lambda p: p.obs_date)
    assert (last.obs_date, last.value, last.domain, last.code, last.price_type) == (date(2026, 9, 3), Decimal("4.77"), "macro", "us.yield.10y", None)


def test_payems_scales_thousands_to_persons():
    last = max(fn.series_points(REG["PAYEMS"], _doc("PAYEMS"), NOW), key=lambda p: p.obs_date)
    assert (last.obs_date, last.value) == (date(2026, 8, 1), Decimal("159075000"))


def test_freshness_gate_uses_per_series_lag():
    assert fn.series_points(REG["DTWEXBGS"], _doc("DTWEXBGS"), NOW)                       # 08-28, 8 ngày ≤ 12
    with pytest.raises(SeriesError) as e:
        fn.series_points(REG["DTWEXBGS"], _doc("DTWEXBGS"), datetime(2026, 9, 10, tzinfo=timezone.utc))   # 13 > 12
    assert e.value.reason == "stale"
    with pytest.raises(SeriesError) as e:
        fn.series_points(REG["DGS10"], _doc("DGS10"), datetime(2026, 9, 15, tzinfo=timezone.utc))
    assert e.value.reason == "stale"


def test_band_and_shape_errors():
    doc = json.loads(json.dumps(_doc("DGS10")))
    doc["observations"][0]["value"] = "477"                            # lỗi 100×
    with pytest.raises(SeriesError) as e:
        fn.series_points(REG["DGS10"], doc, NOW)
    assert e.value.reason == "band"
    with pytest.raises(SeriesError) as e:
        fn.series_points(REG["DGS10"], {"observations": []}, NOW)
    assert e.value.reason == "shape"


def test_transport_error_message_never_contains_the_api_key(monkeypatch, caplog):
    monkeypatch.setenv("FRED_API", KEY)

    def get(u, timeout):
        raise httpx.ConnectError(f"boom {u}")                          # str(e) mang URL có khoá
    with caplog.at_level(logging.WARNING):
        docs, texts, failed, calls, retries = ff.fetch_all([REG["DGS10"]], get, lambda s: None, False)
    assert failed == ["DGS10"] and calls == 4 and retries == 3
    assert KEY not in caplog.text and KEY not in "".join(texts.values())


# ---- job trọn vòng ----
MACRO_CODES = [s.code for s in fr.build() if s.domain == "macro"]
ASSET_CODES = [s.code for s in fr.build() if s.domain == "asset" and s.code != "wti"]   # wti có thể là của wichart


def _synthetic(s):
    d = NOW.date().replace(day=1) if s.freq == "m" else NOW.date()
    lo, hi = s.band
    v = (lo + hi) / 2 / s.scale
    return json.dumps({"observations": [{"date": d.isoformat(), "value": str(v)}], "count": 1})


def _fake_get(calls=None, fail=()):
    def get(u, timeout):
        sid = u.split("series_id=")[1].split("&")[0]
        if calls is not None:
            calls.append(sid)
        if sid in fail:
            return 503, "", {}
        p = FIX / f"fred-{sid}-tail.json"
        return 200, (p.read_text(encoding="utf-8") if p.exists() else _synthetic(REG[sid])), {}
    return get


def _cleanup(engine):
    with engine.begin() as c:
        c.execute(sa.text("DELETE FROM macro.observation WHERE indicator_id IN (SELECT indicator_id FROM macro.indicator_source WHERE source='fred')"))
        c.execute(sa.text("DELETE FROM asset.price_daily WHERE asset_id IN (SELECT asset_id FROM asset.asset_external_id WHERE source='fred')"))
        c.execute(sa.text("DELETE FROM staging.raw_payload WHERE source='fred'"))
        c.execute(sa.text("DELETE FROM ops.etl_run WHERE job='global.fred'"))
        c.execute(sa.text("DELETE FROM ops.data_domain_state WHERE source='fred'"))
        c.execute(sa.text("DELETE FROM macro.indicator_source WHERE source='fred'"))
        c.execute(sa.text("DELETE FROM asset.asset_external_id WHERE source='fred'"))
        c.execute(sa.text("DELETE FROM macro.indicator WHERE code = ANY(:c)"), {"c": MACRO_CODES})
        c.execute(sa.text("DELETE FROM asset.asset WHERE code = ANY(:c)"), {"c": ASSET_CODES})
        # 'wti' dùng chung với wichart: chỉ xoá khi không còn dòng ánh xạ nào trỏ tới — để lại là test_s06_asset
        # (literal 'wti') vỡ UNIQUE(code) khi chạy cả bộ (bẫy I6 lát 6, gặp lại ở Task 1)
        c.execute(sa.text("DELETE FROM asset.asset a WHERE a.code='wti'"
                          " AND NOT EXISTS (SELECT 1 FROM asset.asset_external_id x WHERE x.asset_id = a.asset_id)"))


@pytest.fixture()
def clean(migrated_engine, monkeypatch):
    monkeypatch.setenv("ETL_DATABASE_URL", os.environ["TEST_DATABASE_URL"])
    monkeypatch.setenv("FRED_API", KEY)
    monkeypatch.setattr("etl.series_job.load_dotenv", lambda *a, **k: None)
    _cleanup(migrated_engine)
    yield migrated_engine
    _cleanup(migrated_engine)


def _last(engine):
    with engine.connect() as c:
        return c.execute(sa.text("SELECT status, stats, error FROM ops.etl_run WHERE job='global.fred' ORDER BY run_id DESC LIMIT 1")).one()


def test_job_writes_both_domains_and_wti_spot_beside_futures(clean):
    calls = []
    assert fj.run(get=_fake_get(calls), sleep=lambda s: None, now=NOW) == 0
    assert len(calls) == 15
    status, stats, _ = _last(clean)
    assert status == "success" and stats["registry"] == {"macro": 11, "asset": 4, "removed": 0}
    assert stats["tally"]["ok"] == 15 and stats["inserted"] >= 97 + 12 + 20 + 12 and stats["changed"] == 0
    assert KEY not in json.dumps(stats)
    with clean.connect() as c:
        v = c.execute(sa.text("SELECT value FROM macro.observation o JOIN macro.indicator i USING (indicator_id)"
                              " WHERE i.code='us.yield.10y' AND obs_date='2026-09-03'")).scalar()
        assert v == Decimal("4.77")
        pt = c.execute(sa.text("SELECT price_type FROM asset.price_daily p JOIN asset.asset a USING (asset_id)"
                               " WHERE a.code='wti' ORDER BY obs_date DESC LIMIT 1")).scalar()
        assert pt == "spot"
        assert c.execute(sa.text("SELECT count(*) FROM asset.asset WHERE code='wti'")).scalar() == 1
        rows = dict(c.execute(sa.text("SELECT domain, watermark FROM ops.data_domain_state WHERE source='fred'")).all())
    assert rows == {"macro.indicator": "2026-09-05", "asset": "2026-09-05"}
    assert fj.run(get=_fake_get(), sleep=lambda s: None, now=NOW) == 0
    assert (_last(clean)[1]["inserted"], _last(clean)[1]["changed"]) == (0, 0)


def test_job_refuses_when_one_series_fails(clean):
    assert fj.run(get=_fake_get(fail=("UNRATE",)), sleep=lambda s: None, now=NOW) == 1
    status, stats, error = _last(clean)
    assert status == "failed" and stats["tally"]["failed"] == 1 and "tất cả hoặc không gì" in error
    with clean.connect() as c:
        assert c.execute(sa.text("SELECT count(*) FROM macro.indicator_source WHERE source='fred'")).scalar() == 0
        assert c.execute(sa.text("SELECT count(*) FROM staging.raw_payload WHERE source='fred' AND (meta->>'refused')::bool")).scalar() == 14


def test_backfill_flag_is_rejected_for_fred(clean):
    assert fj.run(backfill=True, get=_fake_get(), sleep=lambda s: None, now=NOW) == 2
