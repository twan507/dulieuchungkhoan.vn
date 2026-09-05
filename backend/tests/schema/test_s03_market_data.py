import sqlalchemy as sa

from tests.conftest import expect_violation


def _issuer(db):
    return db.execute(
        sa.text("INSERT INTO market.issuer (name) VALUES ('CTCP T') RETURNING issuer_id")
    ).scalar()


def _sec(db, t="TST", stype="stock"):
    return db.execute(
        sa.text(
            "INSERT INTO market.security (ticker, exchange, security_type) "
            "VALUES (:t, 'HOSE', :st) RETURNING security_id"
        ),
        {"t": t, "st": stype},
    ).scalar()


def test_price_factor_view(db):  # seam 1 — giải tay
    sid = _sec(db)
    db.execute(
        sa.text(
            "INSERT INTO market.price_daily (security_id, trading_date, close_adj, close_raw) "
            "VALUES (:s, '2026-08-20', 50, 100), (:s, '2026-08-21', 50, 0)"
        ),
        {"s": sid},
    )
    rows = dict(
        db.execute(
            sa.text(
                "SELECT trading_date::text, factor FROM market.price_factor WHERE security_id = :s"
            ),
            {"s": sid},
        ).all()
    )
    assert float(rows["2026-08-20"]) == 0.5
    assert rows["2026-08-21"] is None  # chia 0 → NULL, không lỗi


def test_price_upsert_keeps_raw(db):  # seam 2
    sid = _sec(db, "TS2")
    ins = (
        "INSERT INTO market.price_daily (security_id, trading_date, close_adj, close_raw) "
        "VALUES (:s, '2026-08-20', :a, :r) "
        "ON CONFLICT (security_id, trading_date) DO UPDATE SET close_adj = EXCLUDED.close_adj"
    )
    db.execute(sa.text(ins), {"s": sid, "a": 50, "r": 100})
    db.execute(sa.text(ins), {"s": sid, "a": 25, "r": 999})  # writer sau KHÔNG đụng raw
    row = db.execute(
        sa.text("SELECT close_adj, close_raw FROM market.price_daily WHERE security_id = :s"),
        {"s": sid},
    ).one()
    assert (float(row[0]), float(row[1])) == (25.0, 100.0)


def test_fs_restate_upsert(db):  # seam 3 — mô phỏng restate
    iid = _issuer(db)
    ins = (
        "INSERT INTO market.financial_statement "
        "(issuer_id, year_report, length_report, statement_type, metric_code, value) "
        "VALUES (:i, 2026, 2, 'BS', 'bsa1', :v) "
        "ON CONFLICT (issuer_id, year_report, length_report, statement_type, metric_code) "
        "DO UPDATE SET value = EXCLUDED.value, ingested_at = now()"
    )
    db.execute(sa.text(ins), {"i": iid, "v": 159001})
    db.execute(sa.text(ins), {"i": iid, "v": 158927})
    got = db.execute(
        sa.text("SELECT count(*), max(value) FROM market.financial_statement WHERE issuer_id = :i"),
        {"i": iid},
    ).one()
    assert (got[0], float(got[1])) == (1, 158927.0)


def test_event_natural_key(db):  # seam 4 + 5b (C-3/F6 + F4 NULLS DISTINCT)
    iid = _issuer(db)
    db.execute(
        sa.text(
            "INSERT INTO market.corporate_event (event_type, issuer_id, public_date, payload) "
            "VALUES ('AGM', :i, '2026-08-20', '{}'::jsonb)"
        ),
        {"i": iid},
    )
    assert expect_violation(  # trùng khoá tự nhiên, exright NULL cả hai → vẫn chặn
        db,
        f"INSERT INTO market.corporate_event (event_type, issuer_id, public_date, payload) "
        f"VALUES ('AGM', {iid}, '2026-08-20', '{{}}'::jsonb)",
    )
    assert expect_violation(  # cả public_date lẫn exright_date đều NULL → vẫn chặn (F4)
        db,
        f"INSERT INTO market.corporate_event (event_type, issuer_id, payload) "
        f"VALUES ('IPO', {iid}, '{{}}'::jsonb)",
    ) is False  # dòng ĐẦU hợp lệ
    assert expect_violation(
        db,
        f"INSERT INTO market.corporate_event (event_type, issuer_id, payload) "
        f"VALUES ('IPO', {iid}, '{{}}'::jsonb)",
    )  # dòng THỨ HAI y hệt → chặn
    db.execute(  # Earning 2 kỳ cùng ngày → 2 dòng (C-3)
        sa.text(
            "INSERT INTO market.corporate_event "
            "(event_type, issuer_id, public_date, year_report, length_report, payload) VALUES "
            "('Earning', :i, '2026-08-20', 2026, 1, '{}'::jsonb), "
            "('Earning', :i, '2026-08-20', 2026, 2, '{}'::jsonb)"
        ),
        {"i": iid},
    )
    db.execute(  # CashDividend 2 đợt cùng ngày → 2 dòng (F6)
        sa.text(
            "INSERT INTO market.corporate_event "
            "(event_type, issuer_id, public_date, stage_key, payload) VALUES "
            "('CashDividend', :i, '2026-08-20', '2025:con-lai', '{}'::jsonb), "
            "('CashDividend', :i, '2026-08-20', '2026:tam-ung', '{}'::jsonb)"
        ),
        {"i": iid},
    )
    n = db.execute(
        sa.text("SELECT count(*) FROM market.corporate_event WHERE issuer_id = :i"), {"i": iid}
    ).scalar()
    assert n == 6


def test_checks_and_index_tables(db):  # seam 5 + 5c
    iid = _issuer(db)
    sid = _sec(db, "TS3")
    assert expect_violation(  # length_report = 6 → lỗi CHECK
        db,
        f"INSERT INTO market.financial_statement "
        f"(issuer_id, year_report, length_report, statement_type, metric_code) "
        f"VALUES ({iid}, 2026, 6, 'BS', 'bsa1')",
    )
    assert expect_violation(  # kind lạ ở snapshot → lỗi CHECK
        db,
        f"INSERT INTO market.snapshot_daily (issuer_id, trading_date, kind, payload) "
        f"VALUES ({iid}, '2026-08-20', 'weird', '{{}}'::jsonb)",
    )
    # 0015: hai kind chấm điểm bên thứ ba đã bị bỏ khỏi CHECK (quyết định 2026-09-03)
    for gone in ("company_score", "rate_indicator"):
        assert expect_violation(
            db,
            f"INSERT INTO market.snapshot_daily (issuer_id, trading_date, kind, payload) "
            f"VALUES ({iid}, '2026-08-20', '{gone}', '{{}}'::jsonb)",
        ), f"{gone} phải bị CHECK từ chối"
    for keep in ("snapshot", "valuation", "ownership", "dividend"):
        db.execute(
            sa.text(
                "INSERT INTO market.snapshot_daily (issuer_id, trading_date, kind, payload)"
                " VALUES (:i, '2026-08-20', :k, '{}'::jsonb)"
            ),
            {"i": iid, "k": keep},
        )
    idx = _sec(db, "VNI2", stype="index")
    # payload truyền qua bind param — dấu ':' trong literal JSON bị sa.text() hiểu nhầm là param
    ins_stat = (
        "INSERT INTO market.index_stat_daily (security_id, trading_date, payload) "
        "VALUES (:x, '2026-08-20', CAST(:p AS jsonb)) "
        "ON CONFLICT (security_id, trading_date) DO UPDATE SET payload = EXCLUDED.payload"
    )
    db.execute(sa.text(ins_stat), {"x": idx, "p": '{"a": 1}'})  # UPSERT — 1 dòng sau 2 lần ghi
    db.execute(sa.text(ins_stat), {"x": idx, "p": '{"a": 2}'})
    n = db.execute(
        sa.text("SELECT count(*) FROM market.index_stat_daily WHERE security_id = :x"), {"x": idx}
    ).scalar()
    assert n == 1
    db.execute(  # contribution khoá 3 chiều — cùng (chỉ số, ngày) hai mã → 2 dòng
        sa.text(
            "INSERT INTO market.index_contribution_daily "
            "(index_security_id, security_id, trading_date, payload) VALUES "
            "(:x, :s, '2026-08-20', '{}'::jsonb), (:x, :y, '2026-08-20', '{}'::jsonb)"
        ),
        {"x": idx, "s": sid, "y": _sec(db, "TS4")},
    )


def test_metric_dictionary_two_dicts(db):  # seam 6
    db.execute(
        sa.text(
            "INSERT INTO market.metric_dictionary (dictionary, code) "
            "VALUES ('screener_params', 'zz_test'), ('field_dictionary', 'zz_test')"   # không đụng 729 mã job fundamentals (e35) đã commit
        )
    )
    assert expect_violation(
        db,
        "INSERT INTO market.metric_dictionary (dictionary, code) VALUES ('bogus', 'x1')",
    )
