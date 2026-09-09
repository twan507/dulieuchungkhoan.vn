"""User ClickHouse: SELECT được `rt.*`, DDL bị chặn, mật khẩu đổi theo env — trên container CH tạm (fixture gốc)."""
import os

import clickhouse_connect
import pytest
from clickhouse_connect.driver.exceptions import ClickHouseError

from core import bootstrap


def _client(host_port: str, user: str, password: str):
    return clickhouse_connect.get_client(dsn=f"http://{user}:{password}@{host_port}")


def test_provision_clickhouse_user_can_select_not_ddl_and_password_rotates(migrated):
    host_port = os.environ["CLICKHOUSE_URL"].rsplit("@", 1)[1]
    name = "zz_test_ingester_login"
    try:
        assert bootstrap.provision_clickhouse(migrated, [(name, "pw-one", "dlck_ingester")]) == [name]
        c1 = _client(host_port, name, "pw-one")
        assert int(c1.command("SELECT count() FROM rt.schema_migrations")) >= 1
        with pytest.raises(ClickHouseError):
            c1.command("CREATE TABLE rt.zz_probe (x UInt8) ENGINE = Memory")
        bootstrap.provision_clickhouse(migrated, [(name, "pw-two", "dlck_ingester")])
        with pytest.raises(ClickHouseError):
            _client(host_port, name, "pw-one").command("SELECT 1")
        assert int(_client(host_port, name, "pw-two").command("SELECT 1")) == 1
    finally:
        migrated.command(f"DROP USER IF EXISTS {name}")
