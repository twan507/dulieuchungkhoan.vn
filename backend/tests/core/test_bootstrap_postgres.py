"""Cấp user login từ env: tạo nếu chưa có, LUÔN đổi mật khẩu theo env, thuộc đúng role (spec §5.4).
Chạy trên `dulieu_test` bằng owner; role cấp cluster nên tên bắt đầu `zz_test_` và dọn ở finally."""
import json
import os
import pathlib

import pytest
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
    with pytest.raises(ValueError):
        bootstrap.provision_postgres(migrated_engine, [("bad name; --", "x", "dlck_etl")])


def test_provision_raises_a_clear_error_naming_the_role_when_the_target_role_is_missing(migrated_engine):
    """`provision_postgres` không tự validate role đích tồn tại (chỉ `_ident` canh identifier sạch) —
    câu `GRANT` cuối cùng chết ở Postgres. Đo thật 2026-09-08: `psycopg.errors.UndefinedObject`
    (subclass của `psycopg.Error`), message đã nêu sẵn tên role, KHÔNG bị bootstrap.py nuốt hay bọc
    lại thành lỗi mơ hồ, và cũng không tạo login role bừa — cả giao dịch rollback cùng nhau (đã đo:
    role login không còn tồn tại sau exception). Không cần sửa code, chỉ chốt hồi quy bằng test."""
    import psycopg
    name = "zz_test_missing_role_login"
    try:
        with pytest.raises(psycopg.Error, match="zz_test_missing_role_target"):
            bootstrap.provision_postgres(migrated_engine, [(name, "pw-x", "zz_test_missing_role_target")])
        with migrated_engine.connect() as c:
            assert c.execute(sa.text("SELECT 1 FROM pg_roles WHERE rolname = :n"), {"n": name}).fetchone() is None
    finally:
        with migrated_engine.begin() as c:
            c.execute(sa.text(f"DROP ROLE IF EXISTS {name}"))


@pytest.fixture(scope="module")
def empty_security(migrated_engine):
    """Nhóm test reseed cần `market.security` RỖNG lúc bắt đầu. Bộ test dùng một DB phiên tích luỹ
    (các module ETL cố ý commit dòng), nên chạy `tests/etl` trước `tests/core` để lại security ⇒
    nhánh "skipped:security-rong" không bao giờ xảy ra và nhánh seed đếm thừa (đo 2026-09-09:
    `('seeded', 2)`). Tự dựng tiền đề thay vì trông vào thứ tự chạy: dọn CASCADE, chỉ trên DB đuôi
    `_test`; không module nào được dựa vào dòng của module khác nên không mất gì của ai."""
    assert migrated_engine.url.database.endswith("_test"), migrated_engine.url.database
    with migrated_engine.begin() as c:
        c.execute(sa.text("TRUNCATE market.issuer_industry_override, market.security CASCADE"))


def test_reseed_skips_when_security_is_empty(migrated_engine, empty_security):
    cfg = bootstrap.configure_alembic_for(os.environ["TEST_DATABASE_URL"])
    assert bootstrap.reseed_industry_if_needed(migrated_engine, cfg) == ("skipped:security-rong", 0)


def test_reseed_seeds_the_matching_ticker_then_skips(migrated_engine, empty_security):
    ticker = json.loads(MAP_JSON.read_text(encoding="utf-8"))["layer2"][0]["ticker"]   # đọc từ chủ, không hardcode
    with migrated_engine.begin() as c:
        iid = c.execute(sa.text(
            "INSERT INTO market.issuer (name, com_type_code, icb_code) VALUES ('ZZ seed probe', 'NH', '8355') RETURNING issuer_id"
        )).scalar_one()
        c.execute(sa.text(
            "INSERT INTO market.security (ticker, exchange, security_type, issuer_id) VALUES (:t, 'HOSE', 'stock', :i)"),
            {"t": ticker, "i": iid})
    try:
        cfg = bootstrap.configure_alembic_for(os.environ["TEST_DATABASE_URL"])
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


def test_main_exits_2_naming_the_missing_variable_before_it_touches_any_store(monkeypatch, capsys):
    """T8a — `main()` chưa có test trực tiếp. Phép kiểm env chạy TRƯỚC mọi kết nối (đọc `main()`:
    `missing` ngay sau `load_dotenv`), nên ca này không cần DB; nếu ai đảo thứ tự, test đỏ vì
    `DATA_DATABASE_URL='x'` không phải URL kết nối được.

    `load_dotenv` phải bị vô hiệu: nó `setdefault` từ `.env` THẬT ở gốc repo, nên biến vừa xoá sẽ
    được nạp lại và ca "thiếu biến" không bao giờ xảy ra trên máy dev."""
    monkeypatch.setattr(bootstrap, "load_dotenv", lambda: None)
    for k in bootstrap.REQUIRED:
        monkeypatch.setenv(k, "x")
    monkeypatch.delenv("CLICKHOUSE_INGESTER_PASSWORD")
    assert bootstrap.main() == 2
    assert "bootstrap: thiếu env: CLICKHOUSE_INGESTER_PASSWORD" in capsys.readouterr().err
