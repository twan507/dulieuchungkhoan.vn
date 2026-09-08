import os

from core.env import load_dotenv


def test_load_dotenv_reads_and_does_not_override(tmp_path, monkeypatch):
    f = tmp_path / ".env"
    f.write_text("# comment\nFOO_X=abc\nBAR_Y=1\n\n", encoding="utf-8")
    monkeypatch.delenv("FOO_X", raising=False)
    monkeypatch.setenv("BAR_Y", "keep")
    load_dotenv(f)
    assert os.environ["FOO_X"] == "abc"
    assert os.environ["BAR_Y"] == "keep"


def test_load_dotenv_missing_file_is_noop(tmp_path):
    load_dotenv(tmp_path / "khong-ton-tai.env")  # không raise


import io

from core.env import ASSEMBLED_KEYS, REQUIRED_KEYS, check, compose_urls

BASE = {
    "POSTGRES_HOST": "127.0.0.1", "POSTGRES_PORT": "5432", "POSTGRES_DB": "dulieu",
    "POSTGRES_USER": "dulieu", "POSTGRES_PASSWORD": "pw-owner",
    "ETL_DB_USER": "etl_worker", "ETL_DB_PASSWORD": "p@ss:w/rd",
    "AGENT_DB_USER": "agent_reader", "AGENT_DB_PASSWORD": "pw-agent",
    "REDIS_HOST": "127.0.0.1", "REDIS_PORT": "6379",
    "CLICKHOUSE_HOST": "127.0.0.1", "CLICKHOUSE_PORT": "8123", "CLICKHOUSE_PASSWORD": "pw-ch",
    "CLICKHOUSE_INGESTER_USER": "ingester_worker", "CLICKHOUSE_INGESTER_PASSWORD": "pw-ing",
}


def test_compose_urls_literal_shapes():
    """Expected là chuỗi literal (§4.5.3) — mật khẩu `p@ss:w/rd` phải thành `p%40ss%3Aw%2Frd`."""
    assert compose_urls(BASE) == {
        "DATA_DATABASE_URL": "postgresql+psycopg://dulieu:pw-owner@127.0.0.1:5432/dulieu",
        "TEST_DATABASE_URL": "postgresql+psycopg://dulieu:pw-owner@127.0.0.1:5432/dulieu_test",
        "ETL_DATABASE_URL": "postgresql+psycopg://etl_worker:p%40ss%3Aw%2Frd@127.0.0.1:5432/dulieu",
        "AGENT_DATABASE_URL": "postgresql+psycopg://agent_reader:pw-agent@127.0.0.1:5432/dulieu",
        "CLICKHOUSE_URL": "http://default:pw-ch@127.0.0.1:8123",
        "CLICKHOUSE_INGESTER_URL": "http://ingester_worker:pw-ing@127.0.0.1:8123",
        "REDIS_URL": "redis://127.0.0.1:6379/0",
    }


def test_compose_urls_skips_a_url_whose_part_is_missing():
    env = dict(BASE)
    del env["ETL_DB_PASSWORD"]
    urls = compose_urls(env)
    assert "ETL_DATABASE_URL" not in urls
    assert urls["DATA_DATABASE_URL"] == "postgresql+psycopg://dulieu:pw-owner@127.0.0.1:5432/dulieu"


def test_compose_urls_optional_parts_override_defaults():
    urls = compose_urls({**BASE, "POSTGRES_TEST_DB": "khac_test", "REDIS_DB": "3"})
    assert urls["TEST_DATABASE_URL"] == "postgresql+psycopg://dulieu:pw-owner@127.0.0.1:5432/khac_test"
    assert urls["REDIS_URL"] == "redis://127.0.0.1:6379/3"


def test_load_dotenv_composes_urls_but_an_existing_url_wins(tmp_path, monkeypatch):
    f = tmp_path / ".env"
    f.write_text("\n".join(f"{k}={v}" for k, v in BASE.items()) + "\n", encoding="utf-8")
    for k in ASSEMBLED_KEYS | set(BASE):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("REDIS_URL", "redis://da-co-san:1/9")
    load_dotenv(f)
    assert os.environ["ETL_DATABASE_URL"] == "postgresql+psycopg://etl_worker:p%40ss%3Aw%2Frd@127.0.0.1:5432/dulieu"
    assert os.environ["REDIS_URL"] == "redis://da-co-san:1/9"


def test_load_dotenv_composes_even_when_the_file_is_absent(tmp_path, monkeypatch):
    """Container: compose đã bơm nguyên tố vào env, không có file .env — vẫn phải ráp."""
    for k in ASSEMBLED_KEYS | set(BASE):
        monkeypatch.delenv(k, raising=False)
    for k, v in BASE.items():
        monkeypatch.setenv(k, v)
    load_dotenv(tmp_path / "khong-co.env")
    assert os.environ["CLICKHOUSE_URL"] == "http://default:pw-ch@127.0.0.1:8123"


def test_check_prints_names_only_and_exits_1_when_missing(tmp_path):
    f = tmp_path / ".env"
    f.write_text("POSTGRES_HOST=127.0.0.1\nBIEN_LA=gia-tri-bi-mat-xyz\n", encoding="utf-8")
    out = io.StringIO()
    rc = check(f, out=out)
    text = out.getvalue()
    assert rc == 1
    assert "THIẾU  POSTGRES_PASSWORD" in text and "LẠ     BIEN_LA" in text
    assert "gia-tri-bi-mat-xyz" not in text and "127.0.0.1" not in text


def test_check_exits_0_when_every_required_key_is_present(tmp_path):
    f = tmp_path / ".env"
    f.write_text("\n".join(f"{k}=x" for k in sorted(REQUIRED_KEYS)) + "\n", encoding="utf-8")
    out = io.StringIO()
    assert check(f, out=out) == 0
    assert "đủ" in out.getvalue()


def test_check_treats_a_declared_but_empty_key_as_missing(tmp_path):
    """`compose_urls` đã coi rỗng = không có (env.get trả falsy); `check` phải đồng ý, không chỉ nhìn tên khoá."""
    f = tmp_path / ".env"
    lines = [f"{k}=x" for k in sorted(REQUIRED_KEYS) if k != "POSTGRES_PASSWORD"]
    lines.append("POSTGRES_PASSWORD=")
    f.write_text("\n".join(lines) + "\n", encoding="utf-8")
    out = io.StringIO()
    rc = check(f, out=out)
    text = out.getvalue()
    assert rc == 1
    assert "THIẾU  POSTGRES_PASSWORD" in text


def test_check_flags_placeholder_values_as_weak_and_exits_1(tmp_path):
    """`.env.example` đặt `change-me` cho cả 6 mật khẩu — copy nguyên rồi `up -d` không được phép báo xanh."""
    f = tmp_path / ".env"
    lines = [f"{k}=x" for k in sorted(REQUIRED_KEYS) if k != "POSTGRES_PASSWORD"]
    lines.append("POSTGRES_PASSWORD=change-me")
    f.write_text("\n".join(lines) + "\n", encoding="utf-8")
    out = io.StringIO()
    rc = check(f, out=out)
    text = out.getvalue()
    assert rc == 1
    assert "YẾU  POSTGRES_PASSWORD" in text
    assert "change-me" not in text                      # tên biến, không bao giờ giá trị


def test_check_falls_back_to_os_environ_when_there_is_no_file(monkeypatch, tmp_path):
    """Container: image không mang `.env` (`.dockerignore`), compose bơm nguyên tố qua `env_file` —
    `docker compose run --rm --no-deps migrate python -m core.env check` phải chạy được, không trả 2."""
    for k in REQUIRED_KEYS:
        monkeypatch.setenv(k, "x")
    missing_path = tmp_path / "khong-co.env"
    out = io.StringIO()
    rc = check(missing_path, out=out)
    text = out.getvalue()
    assert rc == 0
    assert f"nguồn: môi trường (không có {missing_path})" in text
    assert "đủ" in text
