"""Không giá trị bí mật nào của `.env` THẬT được xuất hiện trong file đã track của repo.

Bài học 2026-09-09: mật khẩu owner Postgres nằm công khai trong repo từ 2026-08-24 — một plan dán
`.env` mẫu bằng giá trị thật, `.env.example` mang nó tới 2026-09-08, ba hồ sơ khác trích lại; GitGuardian
chỉ báo khi lát 12 push. Test này chạy native (image không mang tests, không mang `.env`): đọc giá trị
trong bộ nhớ, tìm bằng `git grep -F`, và **chỉ in tên khoá + tên file** khi đỏ — không bao giờ in giá trị.
Không có `.env` (CI, máy mới) ⇒ skip có lý do, không giả xanh.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from core.env import parse_dotenv

REPO = Path(__file__).resolve().parents[3]
SECRET_SUFFIXES = ("_PASSWORD", "_API", "_KEY", "_TOKEN", "_SECRET")
MIN_LEN = 8          # giá trị ngắn hơn là placeholder/kiểm thử, không phải bí mật thật


def secret_values(env: dict[str, str]) -> dict[str, str]:
    """Khoá bí mật theo hậu tố, giá trị đủ dài; expected của test đến từ `.env` thật lúc chạy."""
    return {k: v for k, v in env.items() if k.endswith(SECRET_SUFFIXES) and len(v) >= MIN_LEN}


def tracked_files_containing(value: str) -> list[str]:
    r = subprocess.run(["git", "grep", "-l", "-F", "--", value], cwd=REPO, capture_output=True, text=True, encoding="utf-8")
    return [ln for ln in r.stdout.splitlines() if ln]


def test_secret_values_pick_only_long_secret_keys():
    env = {"POSTGRES_PASSWORD": "abcdefgh12345", "POSTGRES_USER": "dulieu", "LLM_API": "x" * 40, "FRED_API": "short"}
    assert set(secret_values(env)) == {"POSTGRES_PASSWORD", "LLM_API"}


def test_no_env_secret_value_is_tracked_in_the_repo():
    env_path = REPO / ".env"
    if not env_path.is_file():
        pytest.skip("không có .env thật để đối chiếu (CI/máy mới)")
    leaks = {k: tracked_files_containing(v) for k, v in secret_values(parse_dotenv(env_path.read_text(encoding="utf-8"))).items()}
    leaks = {k: files for k, files in leaks.items() if files}
    assert not leaks, "giá trị bí mật của .env xuất hiện trong repo (xoay ngay, rồi che): " + "; ".join(
        f"{k} -> {', '.join(files)}" for k, files in leaks.items())
