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
    "INGESTER_SPILL_DIR": "/var/lib/dlck/spill", "CLICKHOUSE_BACKUP_DIR": "/backups",
}
APP = {"migrate", "api", "etl", "ingester", "ingester-measure", "agent"}


def _services():
    return yaml.safe_load(COMPOSE.read_text(encoding="utf-8"))["services"]


def test_root_compose_exists_and_the_split_files_are_gone():
    assert COMPOSE.is_file()
    for old in ("deploy/infra/docker-compose.yml", "deploy/infra/docker-compose.vps.yml", "deploy/app/docker-compose.yml"):
        assert not (REPO / old).exists(), old


def test_app_services_override_exactly_the_documented_variables():
    for name in APP:
        env = _services()[name].get("environment") or {}
        assert env == OVERRIDES, f"{name}: {sorted(set(env) ^ set(OVERRIDES))}"


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
    assert ".env" not in dockerfile
    ignore = (REPO / ".dockerignore").read_text(encoding="utf-8").splitlines()
    assert ".env" in ignore and ".env.*" in ignore and "backend/tests" in ignore
    assert not (REPO / "backend" / ".dockerignore").exists()


def test_image_owns_the_runtime_dirs_for_appuser():
    """Volume có tên lấy quyền từ thư mục điểm gắn trong image; không có sẵn thì Docker tạo root:root và appuser không ghi được (AC4 lát 12)."""
    dockerfile = (REPO / "deploy" / "backend.Dockerfile").read_text(encoding="utf-8")
    for d in ("/var/lib/dlck/logs", "/var/lib/dlck/measure", "/var/lib/dlck/spill", "/backups"):
        assert d in dockerfile, d
    assert re.search(r"chown -R appuser [^\n]*/var/lib/dlck", dockerfile)
