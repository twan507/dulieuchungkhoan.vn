"""Cấp user login từ env: tạo nếu chưa có, LUÔN đổi mật khẩu theo env, thuộc đúng role (spec §5.4).
Chạy trên `dulieu_test` bằng owner; role cấp cluster nên tên bắt đầu `zz_test_` và dọn ở finally."""
import json
import os
import pathlib

import sqlalchemy as sa

from core import bootstrap

MAP_JSON = pathlib.Path(__file__).resolve().parents[3] / "docs" / "20-design" / "industry-mapping.json"


def _can_connect(base_url: sa.URL, user: str, password: str) -> bool:
    url = base_url.set(username=user, password=password)
    eng = sa.create_engine(url)
    try:
        with eng.connect() as c:
            return c.execute(sa.text("SELECT 1")).scalar_one() == 1
    except sa.exc.OperationalError:
        return False
    finally:
        eng.dispose()


def test_provision_creates_login_user_in_role_and_rotates_password(migrated_engine):
    name = "zz_test_etl_login"
    try:
        assert bootstrap.provision_postgres(migrated_engine, [(name, "pw-one", "dlck_etl")]) == [name]
        with migrated_engine.connect() as c:
            assert c.execute(sa.text("SELECT pg_has_role(:n, 'dlck_etl', 'member')"), {"n": name}).scalar_one() is True
            assert c.execute(sa.text("SELECT rolcanlogin FROM pg_roles WHERE rolname = :n"), {"n": name}).scalar_one() is True
        assert _can_connect(migrated_engine.url, name, "pw-one")
        bootstrap.provision_postgres(migrated_engine, [(name, "pw-two", "dlck_etl")])
        assert _can_connect(migrated_engine.url, name, "pw-two")
        assert not _can_connect(migrated_engine.url, name, "pw-one")
    finally:
        with migrated_engine.begin() as c:
            c.execute(sa.text(f"DROP ROLE IF EXISTS {name}"))


def test_provision_rejects_a_name_that_is_not_an_identifier(migrated_engine):
    import pytest
    with pytest.raises(ValueError):
        bootstrap.provision_postgres(migrated_engine, [("bad name; --", "x", "dlck_etl")])


def test_reseed_skips_when_security_is_empty(migrated_engine):
    cfg = bootstrap.alembic_config(os.environ["TEST_DATABASE_URL"])
    assert bootstrap.reseed_industry_if_needed(migrated_engine, cfg) == ("skipped:security-rong", 0)


def test_reseed_seeds_the_matching_ticker_then_skips(migrated_engine):
    ticker = json.loads(MAP_JSON.read_text(encoding="utf-8"))["layer2"][0]["ticker"]   # đọc từ chủ, không hardcode
    with migrated_engine.begin() as c:
        iid = c.execute(sa.text(
            "INSERT INTO market.issuer (name, com_type_code, icb_code) VALUES ('ZZ seed probe', 'NH', '8355') RETURNING issuer_id"
        )).scalar_one()
        c.execute(sa.text(
            "INSERT INTO market.security (ticker, exchange, security_type, issuer_id) VALUES (:t, 'HOSE', 'stock', :i)"),
            {"t": ticker, "i": iid})
    try:
        cfg = bootstrap.alembic_config(os.environ["TEST_DATABASE_URL"])
        assert bootstrap.reseed_industry_if_needed(migrated_engine, cfg) == ("seeded", 1)
        with migrated_engine.connect() as c:
            assert c.execute(sa.text("SELECT count(*) FROM market.issuer_industry_override WHERE issuer_id = :i"),
                             {"i": iid}).scalar_one() == 1
        assert bootstrap.reseed_industry_if_needed(migrated_engine, cfg)[0] == "skipped:da-co"
    finally:
        with migrated_engine.begin() as c:
            c.execute(sa.text("DELETE FROM market.issuer_industry_override"))
            c.execute(sa.text("DELETE FROM market.security WHERE issuer_id = :i"), {"i": iid})
            c.execute(sa.text("DELETE FROM market.issuer WHERE issuer_id = :i"), {"i": iid})
