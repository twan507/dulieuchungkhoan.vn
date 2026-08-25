import sqlalchemy as sa

EXPECTED_SCHEMAS = {"market", "macro", "asset", "news", "staging", "ops", "extensions"}  # 7 — step-01 §2
EXPECTED_EXTS = {"unaccent", "pg_trgm", "vector", "fuzzystrmatch"}                        # 4 — step-01 §3


def test_seven_schemas(db):
    rows = db.execute(
        sa.text("SELECT nspname FROM pg_namespace WHERE nspname = ANY(:s)"),
        {"s": list(EXPECTED_SCHEMAS)},
    )
    assert {r[0] for r in rows} == EXPECTED_SCHEMAS


def test_four_extensions_in_extensions_schema(db):
    rows = db.execute(
        sa.text(
            "SELECT e.extname, n.nspname FROM pg_extension e "
            "JOIN pg_namespace n ON n.oid = e.extnamespace WHERE e.extname = ANY(:x)"
        ),
        {"x": list(EXPECTED_EXTS)},
    )
    got = {r[0]: r[1] for r in rows}
    assert set(got) == EXPECTED_EXTS
    assert all(v == "extensions" for v in got.values())  # I-7/F2: đúng schema, không rơi vào public


def test_public_schema_locked(db):
    ok = db.execute(sa.text("SELECT has_schema_privilege('public', 'public', 'CREATE')")).scalar()
    assert ok is False  # step-01 §2: khoá CREATE trên public
