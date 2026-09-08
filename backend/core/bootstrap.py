"""Bootstrap hai kho — lệnh của service one-shot `migrate` (spec lát 12 §5.4).

Thứ tự cứng, idempotent, chạy bằng OWNER hai kho (URL ráp từ nguyên tố): (1) alembic head ·
(2) ch_migrate · (3) bốn user login — tạo nếu chưa có, LUÔN đổi mật khẩu theo env để `.env` là nguồn
thật · (4) tự seed ngành lớp 2 khi `market.security` có dòng mà bảng override rỗng (bước 3 của
"Bootstrap DB mới" trong database/README.md — trước đây phải nhớ làm tay).

Mọi lỗi ⇒ exit 2 kèm một dòng lý do. Không in giá trị secret.
"""
from __future__ import annotations

import logging
import os
import re
import sys

import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from alembic.operations import Operations
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from psycopg import sql

from core import ch_migrate
from core.env import REPO_ROOT, load_dotenv

log = logging.getLogger("bootstrap")
_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
# (biến tên, biến mật khẩu, role) — tên role là của migration 0009 / 0001_roles.sql
PG_USERS = (("ETL_DB_USER", "ETL_DB_PASSWORD", "dlck_etl"), ("AGENT_DB_USER", "AGENT_DB_PASSWORD", "dlck_api"))
CH_USERS = (("CLICKHOUSE_INGESTER_USER", "CLICKHOUSE_INGESTER_PASSWORD", "dlck_ingester"),
            ("CLICKHOUSE_API_USER", "CLICKHOUSE_API_PASSWORD", "dlck_api"))
REQUIRED = ("DATA_DATABASE_URL", "CLICKHOUSE_URL") + tuple(v for u in PG_USERS + CH_USERS for v in u[:2])


def _ident(name: str) -> str:
    if not _IDENT.fullmatch(name):
        raise ValueError(f"tên không phải identifier: {name!r}")
    return name


def alembic_config(url: str) -> Config:
    cfg = Config(str(REPO_ROOT / "database" / "alembic.ini"))
    os.environ["DATA_DATABASE_URL"] = url      # migrations/env.py đọc biến này — GÁN, không setdefault
    os.chdir(REPO_ROOT)                        # script_location tương đối gốc repo
    return cfg


def provision_postgres(engine: sa.Engine, users) -> list[str]:
    done: list[str] = []
    with engine.begin() as conn:
        raw = conn.connection.driver_connection          # psycopg.Connection — để ghép identifier/literal an toàn
        for name, password, role in users:
            _ident(name), _ident(role)
            with raw.cursor() as cur:
                cur.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (name,))
                if cur.fetchone() is None:
                    cur.execute(sql.SQL("CREATE ROLE {} LOGIN").format(sql.Identifier(name)))
                cur.execute(sql.SQL("ALTER ROLE {} WITH LOGIN PASSWORD {}").format(sql.Identifier(name), sql.Literal(password)))
                cur.execute(sql.SQL("GRANT {} TO {}").format(sql.Identifier(role), sql.Identifier(name)))
            done.append(name)
    return done


def _ch_literal(s: str) -> str:
    return "'" + s.replace("\\", "\\\\").replace("'", "\\'") + "'"


def provision_clickhouse(client, users) -> list[str]:
    done: list[str] = []
    for name, password, role in users:
        _ident(name), _ident(role)
        client.command(f"CREATE USER IF NOT EXISTS {name} IDENTIFIED WITH sha256_password BY {_ch_literal(password)}")
        client.command(f"ALTER USER {name} IDENTIFIED WITH sha256_password BY {_ch_literal(password)}")
        client.command(f"GRANT {role} TO {name}")
        client.command(f"ALTER USER {name} DEFAULT ROLE {role}")
        done.append(name)
    return done


SEED_REVISION = "0013"      # seed industry_icb_map (55) + issuer_industry_override (161)


def _rerun_seed_revision(engine: sa.Engine, cfg: Config) -> None:
    """Chạy lại ĐÚNG MỘT migration `0013` (downgrade = DELETE hai bảng seed, upgrade = nạp lại) trong một
    transaction, KHÔNG đụng `alembic_version`, KHÔNG đụng migration nào khác.

    🔴 Vì sao không `alembic downgrade 0012` → `upgrade head` như README từng ghi: câu đó đúng khi head
    là `0013`. Head nay là `0020`, nên `downgrade 0012` lùi TÁM migration — DROP `news.article_industry`,
    `ops.llm_call`, `ops.snapshot_check`… kèm dữ liệu. Phát hiện lúc viết plan lát 12 (2026-09-08).
    """
    module = ScriptDirectory.from_config(cfg).get_revision(SEED_REVISION).module
    with engine.begin() as conn:
        ctx = MigrationContext.configure(conn)
        with Operations.context(ctx):          # cài proxy `alembic.op` để `op.execute` trong migration chạy
            module.downgrade()
            module.upgrade()


def reseed_industry_if_needed(engine: sa.Engine, cfg: Config) -> tuple[str, int]:
    """Kho mới: `0013` chạy lúc `market.security` rỗng ⇒ lớp 2 0 dòng, không báo. Khi security đã có
    dòng mà override rỗng thì chạy lại riêng `0013` (xem `_rerun_seed_revision`)."""
    q_sec = sa.text("SELECT count(*) FROM market.security WHERE issuer_id IS NOT NULL")
    q_ovr = sa.text("SELECT count(*) FROM market.issuer_industry_override")
    with engine.connect() as c:
        n_sec, n_ovr = c.execute(q_sec).scalar_one(), c.execute(q_ovr).scalar_one()
    if n_sec == 0:
        return "skipped:security-rong", n_ovr
    if n_ovr > 0:
        return "skipped:da-co", n_ovr
    _rerun_seed_revision(engine, cfg)
    with engine.connect() as c:
        n_after = c.execute(q_ovr).scalar_one()
    if n_after == 0:
        raise RuntimeError("seed lớp 2 chạy lại mà vẫn 0 dòng — security có dòng nhưng không ticker nào khớp")
    return "seeded", n_after


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    missing = [k for k in REQUIRED if not os.environ.get(k)]
    if missing:
        print("bootstrap: thiếu env: " + ", ".join(missing), file=sys.stderr)
        return 2
    pg_url = os.environ["DATA_DATABASE_URL"]
    try:
        cfg = alembic_config(pg_url)
        command.upgrade(cfg, "head")
        print("bootstrap: postgres migrate xong (head)")
        ch = ch_migrate.get_client(os.environ["CLICKHOUSE_URL"])
        ran = ch_migrate.upgrade(ch)
        print(f"bootstrap: clickhouse migrate: {ran or 'không có gì mới'}")
        engine = sa.create_engine(pg_url, pool_pre_ping=True)
        try:
            pg_users = [(os.environ[u], os.environ[p], role) for u, p, role in PG_USERS]
            print("bootstrap: postgres user: " + ", ".join(provision_postgres(engine, pg_users)))
            ch_users = [(os.environ[u], os.environ[p], role) for u, p, role in CH_USERS]
            print("bootstrap: clickhouse user: " + ", ".join(provision_clickhouse(ch, ch_users)))
            how, n = reseed_industry_if_needed(engine, cfg)
            print(f"bootstrap: seed ngành lớp 2: {how} ({n} dòng override)")
        finally:
            engine.dispose()
    except Exception as e:  # noqa: BLE001 — one-shot: mọi lỗi là exit 2 kèm lý do, không traceback trần
        print(f"bootstrap: LỖI {type(e).__name__}: {e}", file=sys.stderr)
        log.exception("bootstrap thất bại")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
