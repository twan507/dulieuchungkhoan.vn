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
# Bắt os.environ/os.getenv/environ/env, `.get(`/`[`, nháy đơn lẫn nháy kép (Chuẩn I4/T2a — mẫu cũ chỉ
# bắt os.environ*/env* nháy kép; 0 chỗ dùng os.getenv/nháy đơn trong repo hiện nay nên chưa từng thủng).
_READ = re.compile(
    r"""(?:(?:os\.environ|\benviron|\benv)(?:\.get\(|\[)|os\.getenv\()\s*['"]([A-Z][A-Z0-9_]+)['"]""")
# Khoá compose bơm qua `${TÊN...}` — cũng là "có người đọc" dù không có literal trong code Python.
COMPOSE_FILES = [REPO / "docker-compose.yml", REPO / "docker-compose.vps.yml"]
_COMPOSE_VAR = re.compile(r"\$\{([A-Z][A-Z0-9_]+)")


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


def _scan_code_env_names() -> dict[str, str]:
    """Tên biến `_READ` bắt trong code sản phẩm (ngoài test) → file ĐẦU TIÊN bắt được (cho thông báo lỗi)."""
    seen: dict[str, str] = {}
    for d in CODE_DIRS:
        for p in d.rglob("*.py"):
            for m in _READ.finditer(p.read_text(encoding="utf-8")):
                seen.setdefault(m.group(1), p.relative_to(REPO).as_posix())
    return seen


def test_read_regex_catches_all_five_reader_shapes():
    """Đối chứng dương (Chuẩn I4/T2a) — mẫu cũ chỉ bắt `os.environ`/`env` nháy kép; `os.getenv`, nháy
    đơn và `environ` (không tiền tố `os.`) lọt hoàn toàn dù repo hiện chưa dùng dạng nào trong số đó."""
    samples = {
        'os.getenv("FOO")': "FOO",
        "os.environ.get('FOO')": "FOO",
        "environ.get('FOO')": "FOO",
        'os.environ["FOO"]': "FOO",
        'os.environ.get("FOO", "default")': "FOO",
    }
    for s, name in samples.items():
        m = _READ.search(s)
        assert m, s
        assert m.group(1) == name, s


def _compose_readers() -> set[str]:
    seen: set[str] = set()
    for f in COMPOSE_FILES:
        seen |= set(_COMPOSE_VAR.findall(f.read_text(encoding="utf-8")))
    return seen


def unread_keys(example_keys: set[str], readers: set[str]) -> set[str]:
    """Khoá trong `.env.example` mà không nằm trong `readers` — mồ côi (spec §6, Spec I1).

    Hàm thuần — không tự đọc file, không tự quét code. Bên gọi lắp `readers` từ: tên `_READ` bắt
    trong code sản phẩm ∪ `REQUIRED_KEYS` (nguyên tố bảy `URL_SPECS` MÀ `compose_urls` đọc, cộng hai
    biến chỉ `bootstrap` dùng gián tiếp qua tuple `PG_USERS`/`CH_USERS` — xem docstring `REQUIRED_KEYS`
    ở `core/env.py`) ∪ khoá compose bơm qua `${TÊN...}` ∪ khoá bắt đầu `COMPOSE_` (Compose tự đọc,
    không phải code của dự án).
    """
    return example_keys - readers


def _real_readers(active_example_keys: set[str]) -> set[str]:
    compose_prefixed = {k for k in active_example_keys if k.startswith("COMPOSE_")}
    return set(_scan_code_env_names()) | set(REQUIRED_KEYS) | _compose_readers() | compose_prefixed


def test_unread_keys_flags_a_synthetic_orphan():
    """Test âm bằng hàm thuần — không phụ thuộc nội dung `.env.example` thật."""
    assert unread_keys({"ZZ_UNREAD"}, _real_readers(set())) == {"ZZ_UNREAD"}


def test_every_active_example_key_has_a_real_reader():
    """Vế 'có người đọc' THẬT (Spec I1) — trước đây seam này chỉ kiểm 'thuộc KNOWN_KEYS', một danh
    sách viết tay cùng file với chính khoá đó nên không bắt được khoá sống lâu hơn người đọc cuối
    cùng của nó (xoá consumer, giữ tên trong .env.example)."""
    active, _ = _example_keys()
    orphans = unread_keys(active, _real_readers(active))
    assert not orphans, f"khoá trong .env.example không ai đọc: {sorted(orphans)}"


def test_every_env_name_read_in_code_is_a_known_or_assembled_key():
    seen = _scan_code_env_names()
    assert len(seen) >= 10, f"phép kiểm quét được quá ít tên ({len(seen)}) — nghi regex hụt"
    unknown = {k: v for k, v in seen.items() if k not in KNOWN_KEYS | ASSEMBLED_KEYS | FOREIGN}
    assert not unknown, unknown
