import argparse
import asyncio
from datetime import date

from ingester.main import run


def main() -> int:
    ap = argparse.ArgumentParser("ingester")
    ap.add_argument("--measure", action="store_true")
    ap.add_argument("--out", default=None, help="thư mục frame đo (default INGESTER_MEASURE_DIR)")
    ap.add_argument("--minutes", type=float, default=None)
    ap.add_argument("--reconcile", action="store_true")
    ap.add_argument("--date", type=date.fromisoformat, default=None)
    ap.add_argument("--count", default=None, metavar="YYYYMMDD|DIR",
                    help="bộ đếm d[] offline — replay bản đo qua process_record dry-run"
                         " (spec spill §11)")
    ap.add_argument("--from", dest="t_from", default=None,
                    help="mốc BẮT ĐẦU cửa sổ đếm, ISO giờ VN (vd 2026-08-27T08:30:00);"
                         " mặc định đầu ngày suy từ tên thư mục --count")
    ap.add_argument("--to", dest="t_to", default=None,
                    help="mốc KẾT THÚC cửa sổ đếm, ISO giờ VN; mặc định cuối ngày")
    ap.add_argument("--db", action="store_true",
                    help="so expected với count() rt.* qua CLICKHOUSE_INGESTER_URL")
    a = ap.parse_args()
    if a.count is not None:
        mode = "count"
    elif a.measure:
        mode = "measure"
    elif a.reconcile:
        mode = "reconcile"
    else:
        mode = "run"
    return asyncio.run(run(mode, minutes=a.minutes, out=a.out, d=a.date,
                           count=a.count, t_from=a.t_from, t_to=a.t_to, use_db=a.db))


if __name__ == "__main__":
    raise SystemExit(main())
