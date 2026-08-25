import sqlalchemy as sa


def test_grants_matrix(db):
    def can(role, priv, rel):
        return db.execute(sa.text("SELECT has_table_privilege(:r, :t, :p)"),
                          {"r": role, "t": rel, "p": priv}).scalar()
    assert can("dlck_etl", "INSERT", "market.price_daily") is True
    assert can("dlck_etl", "INSERT", "staging.raw_payload") is True
    assert can("dlck_api", "SELECT", "market.price_daily") is True
    assert can("dlck_api", "INSERT", "market.price_daily") is False
    ok_schema = db.execute(sa.text(
        "SELECT has_schema_privilege('dlck_api','staging','USAGE')")).scalar()
    assert ok_schema is False                                       # api không THẤY staging
    assert db.execute(sa.text(
        "SELECT has_schema_privilege('dlck_api','ops','USAGE')")).scalar() is False


def test_default_privileges_on_new_identity_table(db):
    # bug fix-round Task 9 (thiếu default priv ON SEQUENCES) chưa có test tái hiện — final review #4
    db.execute(sa.text("CREATE TABLE market._tmp_priv_check (id bigint GENERATED ALWAYS AS IDENTITY, v int)"))
    def can(role, priv, rel):
        return db.execute(sa.text("SELECT has_table_privilege(:r, :t, :p)"),
                          {"r": role, "t": rel, "p": priv}).scalar()
    assert can("dlck_etl", "INSERT", "market._tmp_priv_check") is True
    assert can("dlck_api", "SELECT", "market._tmp_priv_check") is True
    assert can("dlck_api", "INSERT", "market._tmp_priv_check") is False
    seq_ok = db.execute(sa.text(
        "SELECT has_sequence_privilege('dlck_etl', 'market._tmp_priv_check_id_seq', 'USAGE')")).scalar()
    assert seq_ok is True   # chính là hành vi fix round Task 9 bảo vệ
    seq_api = db.execute(sa.text(
        "SELECT has_sequence_privilege('dlck_api', 'market._tmp_priv_check_id_seq', 'USAGE')")).scalar()
    assert seq_api is False
