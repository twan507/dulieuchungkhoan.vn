"""`.env.example` ↔ `core.env` ↔ code phải cùng nói một chuyện (spec lát 12 §6, CLAUDE.md §1.7).

Ba vế: (1) mọi khoá trong `.env.example` đều là khoá `core.env` biết; (2) mọi khoá bắt buộc
có mặt và KHÔNG bị comment; (3) không khai khoá nào trong bảy URL RÁP (`ASSEMBLED_KEYS`) — URL kết nối là thứ ráp,
không phải thứ khai; khoá `*_URL` khác (vd `LLM_BASE_URL`) hợp lệ khi thuộc `KNOWN_KEYS`.
Vế 4 soi CODE: mọi tên env đọc bằng literal trong code sản phẩm phải là khoá biết hoặc khoá ráp.
"""
from __future__ import annotations

import re
from pathlib import Path

from core.env import ASSEMBLED_KEYS, KNOWN_KEYS, REQUIRED_KEYS, parse_dotenv

REPO = Path(__file__).resolve().parents[3]
CODE_DIRS = [REPO / "backend" / d for d in ("core", "etl", "ingester", "agent", "api")] + [
    REPO / "database" / "migrations"]
# Tên env code đọc nhưng KHÔNG thuộc `.env` của dự án (do hệ điều hành/compose cấp).
FOREIGN = {"TZ"}
_READ = re.compile(r'(?:os\.environ|\benv)(?:\.get\(|\[)\s*"([A-Z][A-Z0-9_]+)"')


def _example_keys() -> tuple[set[str], set[str]]:
    text = (REPO / ".env.example").read_text(encoding="utf-8")
    active = set(parse_dotenv(text))
    commented = set(re.findall(r"^#\s*([A-Z][A-Z0-9_]+)=", text, re.M))
    return active, commented


def test_example_only_contains_keys_core_env_knows():
    active, commented = _example_keys()
    assert (active | commented) <= KNOWN_KEYS, sorted((active | commented) - KNOWN_KEYS)


def test_example_has_every_required_key_uncommented():
    active, _ = _example_keys()
    assert REQUIRED_KEYS <= active, sorted(REQUIRED_KEYS - active)


def test_example_declares_no_assembled_url():
    """URL kết nối là thứ RÁP, không phải thứ khai. (Ruling khi thực thi 2026-09-08: bản đầu còn cấm mọi
    khoá đuôi `_URL` — sai, vì `LLM_BASE_URL` là endpoint API tuỳ chọn hợp lệ trong `OPTIONAL_KEYS`;
    khoá lạ đuôi `_URL` đã bị vế `test_example_only_contains_keys_core_env_knows` chặn.)"""
    active, commented = _example_keys()
    keys = active | commented
    assert not (keys & ASSEMBLED_KEYS), sorted(keys & ASSEMBLED_KEYS)


def test_every_env_name_read_in_code_is_a_known_or_assembled_key():
    seen: dict[str, str] = {}
    for d in CODE_DIRS:
        for p in d.rglob("*.py"):
            for m in _READ.finditer(p.read_text(encoding="utf-8")):
                seen.setdefault(m.group(1), p.relative_to(REPO).as_posix())
    assert len(seen) >= 10, f"phép kiểm quét được quá ít tên ({len(seen)}) — nghi regex hụt"
    unknown = {k: v for k, v in seen.items() if k not in KNOWN_KEYS | ASSEMBLED_KEYS | FOREIGN}
    assert not unknown, unknown
