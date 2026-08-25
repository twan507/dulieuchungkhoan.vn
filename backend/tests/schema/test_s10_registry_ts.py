import sqlalchemy as sa

REGISTRY_TABLES = [  # step-01 §3 (M-2): registry do ETL nạp mang ingested_at
    ("market", "icb_industry"), ("market", "issuer_external_id"), ("market", "security_external_id"),
    ("market", "metric_dictionary"), ("market", "metric_mapping"),
    ("macro", "indicator"), ("macro", "indicator_source"),
    ("asset", "asset"), ("asset", "asset_external_id"),
    ("news", "article_source"), ("news", "article_ticker"),
]

def test_registry_tables_have_ingested_at(db):
    for schema, table in REGISTRY_TABLES:
        row = db.execute(sa.text(
            "SELECT is_nullable, column_default FROM information_schema.columns "
            "WHERE table_schema=:s AND table_name=:t AND column_name='ingested_at'"),
            {"s": schema, "t": table}).one_or_none()
        assert row is not None, f"{schema}.{table} thiếu ingested_at"
        assert row[0] == "NO" and row[1] and "now()" in row[1]
