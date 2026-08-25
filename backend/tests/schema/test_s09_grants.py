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
