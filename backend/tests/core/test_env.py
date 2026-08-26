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
