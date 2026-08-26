"""Backup hằng đêm theo quyết định #10 của spec ClickHouse realtime store.

Hai lớp: (a) hai bảng nến vĩnh viễn — full backup mỗi ngày, giữ 7 bản gần nhất
+ mọi bản ngày 01; (b) 5 bảng frame — theo partition tháng, lăn theo cửa sổ TTL:
tháng đóng backup một lần, tháng mở đè mỗi ngày (ghi tên mới → xoá bản cũ),
partition đã TTL drop thì xoá file backup. Dung lượng chặn trên ≈ 1× cửa sổ.
"""
import os
import re
from datetime import date
from pathlib import Path

BAR_TABLES = ["bar_1m", "index_bar_1m"]
FRAME_TABLES = ["trade", "quote", "snapshot_delta", "index_delta", "pt_match"]
_PART_RE = re.compile(r"^\d{6}$")


def _active_partitions(client, table: str) -> set[str]:
    rows = client.query(
        "SELECT DISTINCT partition FROM system.parts"
        " WHERE database = 'rt' AND table = %(t)s AND active", parameters={"t": table}
    ).result_rows
    return {r[0] for r in rows if _PART_RE.fullmatch(str(r[0]))}


def _prune_bars(backup_dir: Path, table: str, keep: int = 7) -> list[str]:
    files = sorted(backup_dir.glob(f"{table}-????????.zip"), reverse=True)
    removed = []
    for f in files[keep:]:
        day = f.stem.rsplit("-", 1)[1]
        if day.endswith("01"):                     # giữ bản đầu tháng
            continue
        f.unlink()
        removed.append(f"prune:{f.name}")
    return removed


def run_backup(client, backup_dir: Path, today: date | None = None) -> list[str]:
    today = today or date.today()
    stamp = today.strftime("%Y%m%d")
    cur_month = today.strftime("%Y%m")
    actions: list[str] = []

    for t in BAR_TABLES:                                          # (a) nến — full mỗi ngày
        fname = f"{t}-{stamp}.zip"
        if not (backup_dir / fname).exists():
            client.command(f"BACKUP TABLE rt.{t} TO Disk('backups', '{fname}')")
            actions.append(fname)
        actions += _prune_bars(backup_dir, t)

    for t in FRAME_TABLES:                                        # (b) frame — theo partition
        parts = _active_partitions(client, t)
        for p in sorted(parts):
            if p == cur_month:
                fname = f"{t}-{p}-{stamp}.zip"
                if not (backup_dir / fname).exists():
                    client.command(f"BACKUP TABLE rt.{t} PARTITION '{p}' TO Disk('backups', '{fname}')")
                    for old in backup_dir.glob(f"{t}-{p}-????????.zip"):
                        if old.name != fname:
                            old.unlink()
                    actions.append(fname)
            else:
                fname = f"{t}-{p}.zip"
                if not (backup_dir / fname).exists():
                    client.command(f"BACKUP TABLE rt.{t} PARTITION '{p}' TO Disk('backups', '{fname}')")
                    for old in backup_dir.glob(f"{t}-{p}-????????.zip"):
                        old.unlink()                              # bản daily khi tháng còn mở
                    actions.append(fname)
        for f in backup_dir.glob(f"{t}-*.zip"):                   # (c) prune partition đã TTL drop
            m = re.fullmatch(rf"{t}-(\d{{6}})(-\d{{8}})?\.zip", f.name)
            if m and m.group(1) not in parts:
                f.unlink()
                actions.append(f"prune:{f.name}")
    return actions


def main() -> None:
    from core.ch_migrate import get_client
    backup_dir = Path(os.environ["CLICKHOUSE_BACKUP_DIR"])
    acts = run_backup(get_client(), backup_dir)
    print(f"backup: {acts or 'không có gì mới'}")


if __name__ == "__main__":
    main()
