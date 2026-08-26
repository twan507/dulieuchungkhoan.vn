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
    a = ap.parse_args()
    mode = "measure" if a.measure else ("reconcile" if a.reconcile else "run")
    return asyncio.run(run(mode, minutes=a.minutes, out=a.out, d=a.date))


if __name__ == "__main__":
    raise SystemExit(main())
