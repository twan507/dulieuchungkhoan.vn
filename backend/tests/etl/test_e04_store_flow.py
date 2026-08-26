import json
from datetime import date
from decimal import Decimal

import sqlalchemy as sa

from etl.omo_flow import rebuild
from etl.omo_parse import OmoResult, OmoRow
from etl.omo_store import store

R1 = OmoResult(
    session_date=date(2026, 8, 14),
    rows=[
        OmoRow("reverse_repo", 7, 4, 4, Decimal("6307.47") * 10**9, Decimal("4.5")),
        OmoRow("reverse_repo", 35, 4, 4, Decimal("3466.54") * 10**9, Decimal("4.5")),
    ],
    groups_present=frozenset({"reverse_repo"}),
)


def test_store_writes_session_auction_staging(db):
    stats = store(R1, "<html>raw</html>", db)
    assert stats == {"sessions": 1, "auctions": 2}
    s = db.execute(sa.text(
        "SELECT has_reverse_repo, has_repo, has_outright_sale FROM macro.omo_session"
        " WHERE session_date = '2026-08-14'")).one()
    assert tuple(s) == (True, False, False)
    vol = db.execute(sa.text(
        "SELECT volume_vnd FROM macro.omo_auction WHERE session_date='2026-08-14'"
        " AND op_type='reverse_repo' AND tenor_days=7")).scalar_one()
    assert vol == Decimal("6307470000000")
    raw = db.execute(sa.text(
        "SELECT content_type, body, meta FROM staging.raw_payload"
        " WHERE source='sbv' AND endpoint_key='omo'")).one()
    assert raw.content_type == "html" and raw.body == "<html>raw</html>"
    assert raw.meta["bytes"] == len("<html>raw</html>".encode())


def test_store_skips_duplicate_date(db):
    store(R1, "x" , db)
    assert store(R1, "x", db) == {"skipped": True}
    n = db.execute(sa.text("SELECT count(*) FROM macro.omo_auction")).scalar_one()
    assert n == 2


def _seed(db, d, tenor, vol_billion, op="reverse_repo"):
    db.execute(sa.text(
        "INSERT INTO macro.omo_session (session_date, crawled_at, has_reverse_repo,"
        " has_repo, has_outright_sale) VALUES (:d, now(), true, false, false)"
        " ON CONFLICT DO NOTHING"), {"d": d})
    db.execute(sa.text(
        "INSERT INTO macro.omo_auction (session_date, op_type, tenor_days, volume_vnd)"
        " VALUES (:d, :op, :t, :v)"),
        {"d": d, "op": op, "t": tenor, "v": Decimal(str(vol_billion)) * 10**9})


def test_flow_hand_solved(db):
    _seed(db, date(2026, 8, 14), 7, "6307.47")
    _seed(db, date(2026, 8, 21), 7, "5000")
    rebuild(db)
    r = db.execute(sa.text(
        "SELECT injection_vnd, maturing_vnd, net_vnd, complete FROM macro.omo_flow"
        " WHERE flow_date = '2026-08-21'")).one()
    assert r.injection_vnd == Decimal("5000") * 10**9
    assert r.maturing_vnd == Decimal("6307.47") * 10**9
    assert r.net_vnd == Decimal("-1307.47") * 10**9
    assert r.complete is False        # price_daily rỗng → không đánh giá được cửa sổ


def test_flow_outright_sale_reversed_sign(db):
    _seed(db, date(2026, 8, 14), 7, "1000", op="outright_sale")
    rebuild(db)
    r = db.execute(sa.text(
        "SELECT injection_vnd, net_vnd FROM macro.omo_flow WHERE flow_date='2026-08-14'")).one()
    assert r.injection_vnd == Decimal("-1000") * 10**9    # phát hành tín phiếu = hút
    m = db.execute(sa.text(
        "SELECT net_vnd FROM macro.omo_flow WHERE flow_date='2026-08-21'")).one()
    assert m.net_vnd == Decimal("1000") * 10**9           # đáo hạn tín phiếu = bơm trả lại


def test_flow_rebuild_idempotent(db):
    _seed(db, date(2026, 8, 14), 7, "6307.47")
    rebuild(db)
    first = db.execute(sa.text("SELECT * FROM macro.omo_flow ORDER BY flow_date")).all()
    rebuild(db)
    assert db.execute(sa.text("SELECT * FROM macro.omo_flow ORDER BY flow_date")).all() == first
