"""Đo dung lượng thật của dữ liệu realtime khi nạp vào ClickHouse — phục vụ quyết định TTL.

CHỈ ĐO — không đụng database `rt`. Ghi vào database tạm `measure_tmp`, xoá sau khi đo.
Chạy: cd backend && PYTHONIOENCODING=utf-8 uv run python <path đến file này>
"""
from __future__ import annotations

import glob
import gzip
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, r"D:\twan_projects\dulieuchungkhoan.vn\backend")

import clickhouse_connect

from core.env import REPO_ROOT, load_dotenv
from ingester.dedup import Stamper
from ingester.eio import Event, parse_packet
from ingester.normalize import COLUMNS, Metrics, NormalizeError, normalize, records_of, symbol_of

load_dotenv()
import os

CH_URL = os.environ["CLICKHOUSE_URL"]
DATA_DIR = Path(r"D:\twan_projects\dlck-runtime\measure\20260826")
DDL_PATH = REPO_ROOT / "database" / "clickhouse" / "versions" / "0002_rt_schema.sql"
DB = "measure_tmp"
EVENTS = {"i", "t", "o", "idx", "ptm"}
BATCH = 50_000

TABLE_ORDER = ["trade", "quote", "snapshot_delta", "index_delta", "pt_match", "bar_1m", "index_bar_1m"]


def build_ddl_statements() -> list[str]:
    raw = DDL_PATH.read_text(encoding="utf-8")
    # bỏ MỌI dòng comment trước khi tách statement — comment không có ';' riêng nên nếu
    # tách trước rồi lọc theo prefix "--", cả statement CREATE TABLE trade đứng liền sau
    # 2 dòng comment mở đầu file bị nuốt chung vào "comment", làm mất bảng `trade` (đã
    # tự bắt lỗi này khi chạy thật: MV trade_to_bar_1m báo "Unknown table trade").
    lines = [ln for ln in raw.splitlines() if not ln.strip().startswith("--")]
    sql = "\n".join(lines).replace("rt.", f"{DB}.")
    stmts = [s.strip() for s in sql.split(";")]
    return [s for s in stmts if s]


def main() -> int:
    print(f"[{time.strftime('%H:%M:%S')}] kết nối ClickHouse dev ...")
    client = clickhouse_connect.get_client(dsn=CH_URL)

    print(f"[{time.strftime('%H:%M:%S')}] tạo database {DB} (xoá nếu đã tồn tại từ lần chạy trước) ...")
    client.command(f"DROP DATABASE IF EXISTS {DB}")
    client.command(f"CREATE DATABASE {DB}")

    stmts = build_ddl_statements()
    print(f"[{time.strftime('%H:%M:%S')}] chạy {len(stmts)} statement DDL ...")
    for s in stmts:
        client.command(s)
    print(f"[{time.strftime('%H:%M:%S')}] DDL xong. Bảng: {client.query('SHOW TABLES FROM ' + DB).result_rows}")

    stamper = Stamper()
    metrics = Metrics()
    buffers: dict[str, list[list]] = {t: [] for t in COLUMNS}
    row_counts: dict[str, int] = {t: 0 for t in COLUMNS}
    n_frames = 0
    n_records = 0
    n_normalize_error = 0
    n_not_event = 0
    n_no_symbol = 0
    t0 = time.time()

    def flush(table: str) -> None:
        buf = buffers[table]
        if not buf:
            return
        client.insert(f"{DB}.{table}", buf, column_names=COLUMNS[table])
        row_counts[table] += len(buf)
        buffers[table] = []

    files = sorted(glob.glob(str(DATA_DIR / "frames-*.jsonl.gz")))
    print(f"[{time.strftime('%H:%M:%S')}] {len(files)} file nguồn: {[Path(f).name for f in files]}")

    for fp in files:
        print(f"[{time.strftime('%H:%M:%S')}] đọc {Path(fp).name} ...")
        with gzip.open(fp, "rt", encoding="utf-8") as fh:
            for line in fh:
                n_frames += 1
                row = json.loads(line)
                pkt = parse_packet(row["p"])
                if not isinstance(pkt, Event) or pkt.name not in EVENTS:
                    n_not_event += 1
                    continue
                event = pkt.name
                for record in records_of(pkt.payload):
                    n_records += 1
                    symbol = symbol_of(event, record)
                    if symbol is None:
                        n_no_symbol += 1
                        continue
                    stamped_ms = stamper.stamp(symbol, row["r"])
                    try:
                        norm = normalize(event, record, stamped_ms, metrics)
                    except NormalizeError:
                        n_normalize_error += 1
                        continue
                    buffers[norm.table].append([norm.row.get(c) for c in COLUMNS[norm.table]])
                    if len(buffers[norm.table]) >= BATCH:
                        flush(norm.table)

                if n_frames % 200_000 == 0:
                    elapsed = time.time() - t0
                    print(f"[{time.strftime('%H:%M:%S')}] {n_frames:,} frame · {n_records:,} record · "
                          f"{elapsed:.0f}s · lỗi normalize {n_normalize_error} · "
                          f"đã ghi {sum(row_counts.values()):,} dòng CH")

    for t in COLUMNS:
        flush(t)

    print(f"[{time.strftime('%H:%M:%S')}] xong nạp. Tổng frame={n_frames:,} record={n_records:,} "
          f"not_event={n_not_event:,} no_symbol={n_no_symbol:,} normalize_error={n_normalize_error:,}")
    print(f"Số dòng theo bảng (frame): {row_counts}")
    print(f"Metrics.counters: {metrics.counters}")

    print(f"[{time.strftime('%H:%M:%S')}] OPTIMIZE TABLE ... FINAL cho từng bảng (kể cả nến sinh bởi MV) ...")
    for t in TABLE_ORDER:
        print(f"  optimize {t} ...")
        client.command(f"OPTIMIZE TABLE {DB}.{t} FINAL")

    print(f"[{time.strftime('%H:%M:%S')}] đo system.parts (active=1) ...")
    report_lines = []
    header = f"{'bảng':<16}{'số dòng':>12}{'nén (B)':>16}{'chưa nén (B)':>16}{'tỷ lệ nén':>12}{'B nén/dòng':>14}"
    print(header)
    report_lines.append(header)
    totals = {}
    for t in TABLE_ORDER:
        q = client.query(f"""
            SELECT sum(rows) AS rows, sum(data_compressed_bytes) AS comp,
                   sum(data_uncompressed_bytes) AS uncomp
            FROM system.parts
            WHERE active = 1 AND database = '{DB}' AND table = '{t}'
        """)
        r = q.result_rows[0]
        rows, comp, uncomp = (r[0] or 0), (r[1] or 0), (r[2] or 0)
        ratio = (uncomp / comp) if comp else 0.0
        per_row = (comp / rows) if rows else 0.0
        line = f"{t:<16}{rows:>12,}{comp:>16,}{uncomp:>16,}{ratio:>11.2f}x{per_row:>13.3f}"
        print(line)
        report_lines.append(line)
        totals[t] = {"rows": rows, "compressed_bytes": comp, "uncompressed_bytes": uncomp,
                     "ratio": ratio, "bytes_per_row": per_row}

    out_path = Path(__file__).parent / "size-measurement-raw.json"
    out_path.write_text(json.dumps({
        "n_frames": n_frames, "n_records": n_records, "n_not_event": n_not_event,
        "n_no_symbol": n_no_symbol, "n_normalize_error": n_normalize_error,
        "row_counts_loaded": row_counts, "metrics_counters": metrics.counters,
        "tables": totals,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[{time.strftime('%H:%M:%S')}] đã ghi số liệu thô: {out_path}")

    print(f"[{time.strftime('%H:%M:%S')}] dọn: DROP DATABASE {DB}")
    client.command(f"DROP DATABASE {DB}")
    print(f"[{time.strftime('%H:%M:%S')}] đã dọn xong measure_tmp.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
