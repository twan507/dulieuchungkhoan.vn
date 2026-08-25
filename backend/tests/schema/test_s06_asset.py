import sqlalchemy as sa

from conftest import expect_violation


def _asset(db, code, cls="commodity", ccy="USD"):
    return db.execute(sa.text(
        "INSERT INTO asset.asset (code,name_vi,asset_class,quote_currency) "
        "VALUES (:c,'T',:k,:q) RETURNING asset_id"), {"c": code, "k": cls, "q": ccy}).scalar()

def test_wti_spot_futures_coexist_and_upsert(db):                   # seam 1
    a = _asset(db, "wti")
    ins = ("INSERT INTO asset.price_daily (asset_id,obs_date,price_type,value) VALUES (:a,'2026-08-20',:p,:v) "
           "ON CONFLICT (asset_id,obs_date,price_type) DO UPDATE SET value=EXCLUDED.value")
    db.execute(sa.text(ins), {"a": a, "p": "spot",    "v": 84.77})
    db.execute(sa.text(ins), {"a": a, "p": "futures", "v": 82.40})
    db.execute(sa.text(ins), {"a": a, "p": "spot",    "v": 85.00})  # UPSERT đè spot, không nhân đôi
    rows = dict(db.execute(sa.text("SELECT price_type, value FROM asset.price_daily WHERE asset_id=:a"),
                           {"a": a}).all())
    assert {k: float(v) for k, v in rows.items()} == {"spot": 85.00, "futures": 82.40}

def test_price_type_check(db):                                      # seam 2 — 'perp' đã loại
    a = _asset(db, "btc", cls="crypto", ccy="USDT")
    assert expect_violation(db,
        f"INSERT INTO asset.price_daily (asset_id,obs_date,price_type,value) "
        f"VALUES ({a},'2026-08-20','perp',1)")

def test_ohlc_close_adj_upsert(db):                                 # seam 3
    a = _asset(db, "sp500", cls="index")
    ins = ("INSERT INTO asset.ohlc_daily (asset_id,obs_date,open,high,low,close,close_adj) "
           "VALUES (:a,'2026-08-20',1,2,0.5,1.5,:adj) "
           "ON CONFLICT (asset_id,obs_date) DO UPDATE SET close_adj=EXCLUDED.close_adj")
    db.execute(sa.text(ins), {"a": a, "adj": 1.5})
    db.execute(sa.text(ins), {"a": a, "adj": 1.4})
    row = db.execute(sa.text("SELECT close, close_adj FROM asset.ohlc_daily WHERE asset_id=:a"), {"a": a}).one()
    assert (float(row[0]), float(row[1])) == (1.5, 1.4)             # close gốc giữ nguyên

def test_fx_as_asset(db):                                           # seam 5 (I-3-mới)
    a = _asset(db, "fx.usd_eur", cls="fx", ccy="EUR")
    db.execute(sa.text("INSERT INTO asset.price_daily (asset_id,obs_date,price_type,value) "
                       "VALUES (:a,'2026-08-14','fixing',0.86453)"), {"a": a})
    inv = db.execute(sa.text("SELECT round(1/value, 6) FROM asset.price_daily WHERE asset_id=:a"),
                     {"a": a}).scalar()
    assert float(inv) == 1.156698                                   # literal fx.md — tính ở tầng đọc
    db.execute(sa.text("INSERT INTO asset.price_daily (asset_id,obs_date,price_type,value) "
                       "VALUES (:a,'2026-08-14','close',0.86500)"), {"a": a})  # khác mốc chốt — cùng tồn tại

def test_registry_constraints(db):                                  # seam 6 + calendar M11
    _asset(db, "gold.lbma")
    assert expect_violation(db, "INSERT INTO asset.asset (code,name_vi,asset_class,quote_currency) "
                                "VALUES ('gold.lbma','T','commodity','USD')")
    assert expect_violation(db, "INSERT INTO asset.asset (code,name_vi,asset_class,quote_currency,calendar) "
                                "VALUES ('x1','T','commodity','USD','sometimes')")
    a = _asset(db, "paxg", cls="crypto", ccy="USDT")
    db.execute(sa.text("INSERT INTO asset.asset_external_id (asset_id,source,external_code,external_sub) "
                       "VALUES (:a,'binance','PAXGUSDT','')"), {"a": a})
    assert expect_violation(db, f"INSERT INTO asset.asset_external_id (asset_id,source,external_code,external_sub) "
                                f"VALUES ({a},'binance','PAXGUSDT','')")
