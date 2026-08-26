import uuid

import clickhouse_connect
import pytest

EXPECTED_OBJECTS = {
    "trade": "MergeTree", "quote": "MergeTree", "snapshot_delta": "MergeTree",
    "index_delta": "MergeTree", "pt_match": "MergeTree",
    "bar_1m": "AggregatingMergeTree", "index_bar_1m": "AggregatingMergeTree",
    "schema_migrations": "ReplacingMergeTree",
    "mv_trade_to_bar_1m": "MaterializedView", "mv_index_to_bar_1m": "MaterializedView",
    "bar_1m_v": "View", "index_bar_1m_v": "View",
}


def test_du_12_object_dung_engine(migrated):
    rows = migrated.query("SELECT name, engine FROM system.tables WHERE database='rt'").result_rows
    assert {r[0]: r[1] for r in rows} == EXPECTED_OBJECTS


def test_create_table_query_khop_ky_vong_chong_drift(migrated):
    """IF NOT EXISTS che drift — đối chiếu định nghĩa thật với các mảnh bất biến (spec §8)."""
    ddl = {r[0]: r[1] for r in migrated.query(
        "SELECT name, create_table_query FROM system.tables WHERE database='rt'").result_rows}
    for t in ["trade", "quote", "snapshot_delta", "index_delta", "pt_match"]:
        assert "TTL toDate(ts) + toIntervalMonth(3)" in ddl[t]
        assert "ttl_only_drop_parts = 1" in ddl[t]
        assert "non_replicated_deduplication_window = 100" in ddl[t]
    assert "non_replicated_deduplication_window = 100" in ddl["bar_1m"]
    assert "TTL" not in ddl["bar_1m"] and "TTL" not in ddl["index_bar_1m"]
    assert "Tuple(DateTime('Asia/Ho_Chi_Minh'), UInt64, DateTime64(3, 'Asia/Ho_Chi_Minh'))" in ddl["bar_1m"]
    assert "Tuple(DateTime64(3, 'Asia/Ho_Chi_Minh'), DateTime64(3, 'Asia/Ho_Chi_Minh'))" in ddl["index_bar_1m"]
    assert "index_value > 0" in ddl["mv_index_to_bar_1m"]


def test_profile_gan_role_ingester(migrated):
    row = migrated.query(
        "SELECT value FROM system.settings_profile_elements WHERE profile_name='dlck_ingester_profile'"
        " AND setting_name='deduplicate_blocks_in_dependent_materialized_views'").result_rows
    assert row and str(row[0][0]) == "1"


@pytest.fixture()
def api_user(migrated):
    name = f"t_api_{uuid.uuid4().hex[:6]}"
    migrated.command(f"CREATE USER {name} IDENTIFIED WITH plaintext_password BY 'x' DEFAULT ROLE dlck_api")
    yield name
    migrated.command(f"DROP USER IF EXISTS {name}")


def test_quyen_dlck_api(migrated, api_user):
    import os
    base = os.environ["CLICKHOUSE_URL"].rsplit("@", 1)[1]      # 127.0.0.1:PORT
    c = clickhouse_connect.get_client(dsn=f"http://{api_user}:x@{base}")
    assert c.command("SELECT count() >= 0 FROM rt.bar_1m_v") in (0, 1)   # SELECT qua view được
    with pytest.raises(Exception):
        c.command("INSERT INTO rt.trade (symbol, ts, seq, price, volume, side, change, cum_volume, cum_value) VALUES ('X', now(), 1, 1, 1, 'B', 0, 1, 1)")
    with pytest.raises(Exception):
        c.command("DROP TABLE rt.trade")
    dbs = [r[0] for r in c.query("SHOW DATABASES").result_rows]
    assert "rt" in dbs and all(d in ("rt", "system", "INFORMATION_SCHEMA", "information_schema", "default") for d in dbs)
