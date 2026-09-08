"""Hợp đồng compose/Dockerfile ↔ spec lát 12 §5.2–5.3 — kiểm tĩnh, không dựng container.

Danh sách biến compose được đè là TOÀN BỘ danh sách §5.2: thêm/bớt một biến là đỏ, để lệch giữa
`.env.example`, `core.env` và YAML không thể xảy ra âm thầm.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[3]
COMPOSE = REPO / "docker-compose.yml"
OVERRIDES = {
    "POSTGRES_HOST": "postgres", "REDIS_HOST": "redis", "CLICKHOUSE_HOST": "clickhouse",
    "TZ": "Asia/Ho_Chi_Minh",
    "INGESTER_LOG_DIR": "/var/lib/dlck/logs", "INGESTER_MEASURE_DIR": "/var/lib/dlck/measure",
    "INGESTER_SPILL_DIR": "/var/lib/dlck/spill",
}
# `etl` là service DUY NHẤT trong nhóm app mount `/backups` (cạnh `clickhouse`) — bốn service kia
# không mang biến trỏ vào đường không mount (bất đồng nhẹ với phán quyết #9, review toàn nhánh 2026-09-08).
ETL_OVERRIDES = {**OVERRIDES, "CLICKHOUSE_BACKUP_DIR": "/backups"}
APP = {"migrate", "api", "etl", "ingester", "ingester-measure", "agent"}
# Bắt "docs" đứng một mình trong nháy (Path / "docs", os.path.join(..., "docs", ...), D = "docs")
# và "/docs/" bên trong literal/f-string (p = f"{root}/docs/a.json") — đo review 2026-09-08: mẫu cũ
# chỉ bắt 1/5 hình dạng tái diễn thật. Văn xuôi kiểu "xem docs/…" (khoảng trắng trước "docs/", không
# phải quote/slash) không match — đã đo trên toàn bộ backend/database, 0 hit ngoài code thật.
_DOCS_PATH_RE = re.compile(r"""["']docs["']|/docs/""")


def _services():
    return yaml.safe_load(COMPOSE.read_text(encoding="utf-8"))["services"]


def test_root_compose_exists_and_the_split_files_are_gone():
    assert COMPOSE.is_file()
    for old in ("deploy/infra/docker-compose.yml", "deploy/infra/docker-compose.vps.yml", "deploy/app/docker-compose.yml"):
        assert not (REPO / old).exists(), old


def test_app_services_override_exactly_the_documented_variables():
    for name in APP - {"etl"}:
        env = _services()[name].get("environment") or {}
        assert env == OVERRIDES, f"{name}: {sorted(set(env) ^ set(OVERRIDES))}"


def test_etl_additionally_overrides_the_clickhouse_backup_dir():
    """`etl` mount `/backups` (cạnh `clickhouse`) nên là service DUY NHẤT trong nhóm app còn giữ
    `CLICKHOUSE_BACKUP_DIR` — bốn service kia đã bỏ biến trỏ vào đường không mount."""
    env = _services()["etl"].get("environment") or {}
    assert env == ETL_OVERRIDES, f"etl: {sorted(set(env) ^ set(ETL_OVERRIDES))}"


def test_no_service_declares_a_url_variable():
    for name, svc in _services().items():
        for key in (svc.get("environment") or {}):
            assert not key.endswith("_URL"), f"{name}.{key}"


def test_every_app_service_waits_for_migrate():
    for name in APP - {"migrate"}:
        dep = _services()[name]["depends_on"]["migrate"]
        assert dep == {"condition": "service_completed_successfully"}, name


def test_migrate_is_a_one_shot_running_bootstrap():
    m = _services()["migrate"]
    assert m["restart"] == "no" and m["command"] == ["python", "-m", "core.bootstrap"]


def test_ingester_runtime_dirs_are_named_volumes_and_stop_grace_is_generous():
    ing = _services()["ingester"]
    targets = {v.split(":")[1] for v in ing["volumes"]}
    assert targets == {"/var/lib/dlck/logs", "/var/lib/dlck/measure", "/var/lib/dlck/spill"}
    assert ing["stop_grace_period"] == "90s" and _services()["etl"]["stop_grace_period"] == "60s"


def test_image_never_carries_secrets_or_tests():
    dockerfile = (REPO / "deploy" / "backend.Dockerfile").read_text(encoding="utf-8")
    ignore = (REPO / ".dockerignore").read_text(encoding="utf-8").splitlines()
    assert ".env" in ignore and ".env.*" in ignore and "backend/tests" in ignore
    assert not (REPO / "backend" / ".dockerignore").exists()


def test_image_owns_the_runtime_dirs_for_appuser():
    """Volume có tên lấy quyền từ thư mục điểm gắn trong image; không có sẵn thì Docker tạo root:root và appuser không ghi được (AC4 lát 12)."""
    dockerfile = (REPO / "deploy" / "backend.Dockerfile").read_text(encoding="utf-8")
    for d in ("/var/lib/dlck/logs", "/var/lib/dlck/measure", "/var/lib/dlck/spill", "/backups"):
        assert d in dockerfile, d
    # [^\n&]* không vắt qua `&&` — chặn regex khớp lem sang một lệnh khác trên cùng dòng RUN (Chuẩn M8).
    assert re.search(r"chown -R appuser [^\n&]*/var/lib/dlck[^\n&]*/backups", dockerfile)
    # Lý do tồn tại của chown là chạy non-root — bỏ dòng USER appuser thì không test nào ở trên đỏ (Chuẩn M8).
    assert re.search(r"^USER appuser$", dockerfile, re.M)


def test_docs_path_regex_catches_five_real_world_shapes():
    """Đối chứng dương (Chuẩn I4) — regex cũ chỉ bắt 1/5 hình dạng tái diễn thật (đo review 2026-09-08):
    literal ghép bằng `/`, biến gán riêng, `os.path.join`, f-string, và khoá đứng một mình rồi ghép sau."""
    samples = [
        'ROOT / "docs" / "a.json"',
        'P = ROOT / "docs"',
        'os.path.join(root, "docs", "x.json")',
        'p = f"{root}/docs/a.json"',
        'D = "docs"',
    ]
    for s in samples:
        assert _DOCS_PATH_RE.search(s), s


def test_production_code_never_reads_docs():
    """Image không mang `docs/` (spec §5.3, `.dockerignore`) — mọi tri thức code cần lúc chạy phải nằm trong
    backend/ hoặc database/ (chỉ đạo chủ dự án 2026-09-08). Task 10 lát 12: `fundamentals` chết exit 2 trong
    container vì đọc docs/10-sources/…; `news` · `screener` · `wichart` cùng lỗi. Quét tĩnh, không dựng container."""
    skip = {".venv", "__pycache__", ".pytest_cache", "node_modules"}
    hits = []
    n_files = 0
    for root in (REPO / "backend", REPO / "database"):
        for py in sorted(root.rglob("*.py")):
            rel = py.relative_to(REPO).as_posix()
            parts = set(rel.split("/"))
            if parts & skip or rel.startswith("backend/tests/"):
                continue
            n_files += 1
            for n, line in enumerate(py.read_text(encoding="utf-8").splitlines(), 1):
                if _DOCS_PATH_RE.search(line):
                    hits.append(f"{rel}:{n}: {line.strip()}")
    assert n_files >= 100, f"chỉ quét {n_files} file — nghi phạm vi hụt (đo 2026-09-08: 153)"
    assert not hits, "code ráp đường dẫn vào docs/ — dời tri thức vào backend/ hoặc database/:\n  " + "\n  ".join(hits)
    ignore = (REPO / ".dockerignore").read_text(encoding="utf-8").splitlines()
    assert "docs" in ignore                                    # image vẫn không mang docs/
