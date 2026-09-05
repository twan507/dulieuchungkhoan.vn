"""Ghi kho thật (fixture `db` = một giao dịch, rollback cuối test)."""
import dataclasses
from datetime import date
from decimal import Decimal

import sqlalchemy as sa

from etl import wichart_registry as wr
from etl import wichart_store as ws
from etl.wichart_normalize import Point


def _count(db, sql, **p):
    return db.execute(sa.text(sql), p).scalar()


def test_load_registry_upserts_53_indicators_and_52_assets_idempotently(db):
    series = wr.build()
    resolved, stats = ws.load_registry(db, series)
    assert stats == {"macro": 53, "asset": 52, "removed": 0}
    assert len(resolved) == 105 and resolved["vn.cpi"].domain == "macro" and resolved["wti"].price_type == "futures"
    n_ind = _count(db, "SELECT count(*) FROM macro.indicator WHERE code LIKE 'vn.%'")
    n_src = _count(db, "SELECT count(*) FROM macro.indicator_source WHERE source = 'wichart'")
    n_ast = _count(db, "SELECT count(*) FROM asset.asset_external_id WHERE source = 'wichart'")
    assert (n_ind, n_src, n_ast) == (53, 53, 52)
    first_id = resolved["vn.cpi"].row_id
    resolved2, stats2 = ws.load_registry(db, series)                      # lượt hai: không nhân đôi, id giữ
    assert stats2 == stats and resolved2["vn.cpi"].row_id == first_id
    assert _count(db, "SELECT count(*) FROM macro.indicator_source WHERE source = 'wichart'") == 53
    row = db.execute(sa.text("SELECT external_key, external_sub, scale, active FROM macro.indicator_source s"
                             " JOIN macro.indicator i USING (indicator_id) WHERE i.code = 'vn.credit'")).one()
    assert tuple(row) == ("td", "0", Decimal("1000000000"), True)
    row = db.execute(sa.text("SELECT a.asset_class, a.quote_currency, a.unit, a.calendar, x.price_type, x.scale"
                             " FROM asset.asset a JOIN asset.asset_external_id x USING (asset_id) WHERE a.code = 'cotton_us'")).one()
    assert tuple(row) == ("commodity", "USD", "USD/lb", "trading_days", "spot", Decimal("0.01"))


def test_series_missing_from_registry_has_its_mapping_row_removed_but_keeps_the_indicator(db):
    series = wr.build()
    ws.load_registry(db, series)
    trimmed = [s for s in series if s.code != "vn.pmi"]
    _, stats = ws.load_registry(db, trimmed)
    assert stats["removed"] == 1
    assert _count(db, "SELECT count(*) FROM macro.indicator WHERE code = 'vn.pmi'") == 1
    assert _count(db, "SELECT count(*) FROM macro.indicator_source WHERE source='wichart' AND external_key='pmi'") == 0
    pmi_id_before = db.execute(sa.text("SELECT indicator_id FROM macro.indicator WHERE code='vn.pmi'")).scalar()
    _, stats = ws.load_registry(db, series)                               # nạp trọn lại: dòng pmi quay lại
    assert _count(db, "SELECT count(*) FROM macro.indicator_source WHERE source='wichart' AND external_key='pmi'") == 1
    pmi_id_after = db.execute(sa.text("SELECT indicator_id FROM macro.indicator WHERE code='vn.pmi'")).scalar()
    assert pmi_id_before == pmi_id_after                                  # indicator_id không đổi


def test_series_with_changed_idx_does_not_violate_unique_constraint(db):
    series = wr.build()
    ws.load_registry(db, series)
    cpi_id_before = db.execute(sa.text("SELECT indicator_id FROM macro.indicator WHERE code='vn.cpi'")).scalar()
    changed = [dataclasses.replace(s, idx=1) if (s.key, s.idx) == ("cpi", 0) else s for s in series]
    ws.load_registry(db, changed)                                         # KHÔNG raise UniqueViolation
    row = db.execute(sa.text("SELECT external_key, external_sub FROM macro.indicator_source"
                             " WHERE source='wichart' AND external_key='cpi'")).all()
    assert [tuple(r) for r in row] == [("cpi", "1")]
    cpi_id_after = db.execute(sa.text("SELECT indicator_id FROM macro.indicator WHERE code='vn.cpi'")).scalar()
    assert cpi_id_before == cpi_id_after


def test_apply_counts_inserted_then_changed_and_leaves_unchanged_rows_untouched(db):
    resolved, _ = ws.load_registry(db, wr.build())
    pts = [Point("macro", "vn.cpi", date(2026, 7, 1), Decimal("3.19"), None),
           Point("macro", "vn.cpi", date(2026, 8, 1), Decimal("4.45"), None),
           Point("asset", "gold.sjc_buy", date(2026, 9, 4), Decimal("145600000"), "spot")]
    w = ws.apply(db, pts, resolved)
    assert (w.inserted, w.changed) == (3, 0)
    ts1 = _count(db, "SELECT max(o.ingested_at) FROM macro.observation o JOIN macro.indicator i USING (indicator_id) WHERE i.code='vn.cpi'")
    w = ws.apply(db, pts, resolved)                                         # chạy lại: không chạm dòng nào
    assert (w.inserted, w.changed) == (0, 0)
    assert _count(db, "SELECT max(o.ingested_at) FROM macro.observation o JOIN macro.indicator i USING (indicator_id) WHERE i.code='vn.cpi'") == ts1
    pts[1] = Point("macro", "vn.cpi", date(2026, 8, 1), Decimal("4.50"), None)   # vá hồi tố một điểm
    w = ws.apply(db, pts, resolved)
    assert (w.inserted, w.changed) == (0, 1)
    got = dict(db.execute(sa.text("SELECT obs_date, value FROM macro.observation o JOIN macro.indicator i USING (indicator_id)"
                                  " WHERE i.code='vn.cpi'")).all())
    assert got == {date(2026, 7, 1): Decimal("3.19"), date(2026, 8, 1): Decimal("4.50")}
    assert _count(db, "SELECT value FROM asset.price_daily p JOIN asset.asset a USING (asset_id)"
                      " WHERE a.code='gold.sjc_buy' AND price_type='spot'") == Decimal("145600000")


def test_series_break_seed_makes_the_spliced_view_scale_the_old_segment(db):
    resolved, _ = ws.load_registry(db, wr.build())
    ws.apply(db, [Point("macro", "vn.gdp.real", date(2025, 10, 1), Decimal("1642683"), None),
                  Point("macro", "vn.gdp.real", date(2026, 1, 1), Decimal("2401927"), None)], resolved)
    ws.seed_series_break(db)
    ws.seed_series_break(db)                                                # idempotent
    rows = dict(db.execute(sa.text("SELECT obs_date, value_spliced FROM macro.observation_spliced v"
                                   " JOIN macro.indicator i USING (indicator_id) WHERE i.code='vn.gdp.real'")).all())
    assert rows[date(2025, 10, 1)] == Decimal("1642683") * Decimal("1.6005")   # đoạn CŨ × hệ số
    assert rows[date(2026, 1, 1)] == Decimal("2401927")                        # kỳ đầu của nền mới, không nhân
    n = db.execute(sa.text("SELECT count(*), max(factor), max(verified_at)::date FROM macro.series_break")).one()
    assert n[0] == 1 and n[1] == Decimal("1.6005") and n[2] == date(2026, 9, 5)


def test_payload_is_stored_only_when_its_hash_changes(db):
    assert ws.store_payload_if_changed(db, "cpi", '{"a":1}', run_id=1) is True
    assert ws.store_payload_if_changed(db, "cpi", '{"a":1}', run_id=2) is False
    assert ws.store_payload_if_changed(db, "cpi", '{"a":2}', run_id=3) is True
    rows = db.execute(sa.text("SELECT endpoint_key, meta->>'run_id' FROM staging.raw_payload"
                              " WHERE source='wichart' ORDER BY payload_id")).all()
    assert [tuple(r) for r in rows] == [("wichart:cpi", "1"), ("wichart:cpi", "3")]


def test_store_works_under_etl_role(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    resolved, stats = ws.load_registry(db, wr.build())
    assert stats["macro"] == 53
    w = ws.apply(db, [Point("macro", "vn.cpi", date(2026, 8, 1), Decimal("4.45"), None),
                      Point("asset", "wti", date(2026, 9, 4), Decimal("62.1"), "futures")], resolved)
    assert w.inserted == 2
    ws.seed_series_break(db)
    assert ws.store_payload_if_changed(db, "cpi", '{"x":1}', run_id=9) is True
