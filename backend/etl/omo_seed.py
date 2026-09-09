"""Seed OMO từ CSV chuyển từ file FiinProX (spec lát 13 §5.1). CSV không nằm trong repo — dữ liệu sản phẩm trả tiền, repo public.

Cột bắt buộc: session_date,tenor_days,participants,winners,volume_bn,rate (rate là PHÂN SỐ, 0.045 = 4,5 %/năm).
Mọi dòng là Mua kỳ hạn (reverse_repo): file kết quả đấu thầu FiinProX không có cột loại hình, và file chuỗi ngày cùng
kỳ xác nhận tín phiếu = 0 suốt 08/09/2025–07/09/2026 — file có cột lạ thì từ chối cả lượt, không đoán.
"""
from __future__ import annotations

import csv
import logging
import os
import sys
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

import sqlalchemy as sa

from core.env import load_dotenv
from etl import omo_flow, omo_store
from etl.omo_parse import OmoResult, OmoRow

log = logging.getLogger("etl.omo_seed")
JOB = "macro.omo_seed"
COLUMNS = ["session_date", "tenor_days", "participants", "winners", "volume_bn", "rate"]
BILLION = Decimal(10) ** 9
NOTE = "seed FiinProX export 2026-09-08"
CRAWLED_AT = datetime(2026, 9, 8, 3, 52, tzinfo=timezone.utc)     # 10:52 VN, "Ngày trích xuất" trong file


@dataclass(frozen=True)
class SeedRow:
    session_date: date
    tenor_days: int
    participants: int | None
    winners: int | None
    volume_vnd: Decimal
    rate_pct: Decimal | None


def _int_or_none(s: str) -> int | None:
    s = s.strip()
    return None if s == "" else int(s)


def read_csv(path) -> list[SeedRow]:
    with open(path, encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames != COLUMNS:
            raise ValueError(f"cột CSV phải đúng {COLUMNS}, nhận {reader.fieldnames}")
        out = []
        for i, r in enumerate(reader, 2):
            try:
                out.append(SeedRow(date.fromisoformat(r["session_date"]), int(r["tenor_days"]),
                                   _int_or_none(r["participants"]), _int_or_none(r["winners"]),
                                   Decimal(r["volume_bn"]) * BILLION,
                                   None if r["rate"].strip() == "" else Decimal(r["rate"]) * 100))
            except (ValueError, InvalidOperation) as e:
                raise ValueError(f"dòng {i} hỏng: {e}") from e
    return out


def to_results(rows: list[SeedRow]) -> list[OmoResult]:
    by_day: dict[date, dict[int, OmoRow]] = {}
    merged: dict[date, int] = {}
    for r in rows:
        day = by_day.setdefault(r.session_date, {})
        prev = day.get(r.tenor_days)
        if prev is None:
            day[r.tenor_days] = OmoRow("reverse_repo", r.tenor_days, r.participants, r.winners, r.volume_vnd, r.rate_pct)
            continue
        if prev.rate_pct != r.rate_pct:
            raise ValueError(f"{r.session_date} kỳ hạn {r.tenor_days}: hai dòng khác lãi suất {prev.rate_pct} vs {r.rate_pct}")
        day[r.tenor_days] = OmoRow("reverse_repo", r.tenor_days,
                                   None if prev.participants is None or r.participants is None else prev.participants + r.participants,
                                   None if prev.winners is None or r.winners is None else prev.winners + r.winners,
                                   prev.volume_vnd + r.volume_vnd, prev.rate_pct)
        merged[r.session_date] = merged.get(r.session_date, 0) + 1
    return [OmoResult(d, [day[t] for t in sorted(day)], frozenset({"reverse_repo"}), merged.get(d, 0))
            for d, day in sorted(by_day.items())]


def _seed(conn, results: list[OmoResult]) -> dict:
    st = {"sessions_new": 0, "sessions_skipped": 0, "auctions": 0, "rows_merged": sum(r.merged for r in results),
          "min_session_date": results[0].session_date.isoformat() if results else None,
          "max_session_date": results[-1].session_date.isoformat() if results else None}
    for r in results:
        w = omo_store.store_seed(r, conn, crawled_at=CRAWLED_AT, note=NOTE)
        if w.get("skipped"):
            st["sessions_skipped"] += 1
        else:
            st["sessions_new"] += 1
            st["auctions"] += w["auctions"]
    st["flow_rows"] = omo_flow.rebuild(conn)
    return st


def _outstanding(conn, days) -> dict[str, str]:
    out = {}
    for d in days:
        v = conn.execute(sa.text("SELECT outstanding_vnd FROM macro.omo_flow WHERE flow_date <= :d ORDER BY flow_date DESC LIMIT 1"),
                         {"d": d}).scalar()
        out[f"outstanding_{d.isoformat()}"] = "n/a" if v is None else f"{(Decimal(v) / BILLION):.2f}"
    return out


def run(path: str, dry_run: bool = False, checks: tuple[date, ...] = (date(2026, 9, 7), date(2026, 9, 8))) -> int:
    logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    load_dotenv()
    url = os.environ.get("ETL_DATABASE_URL")
    if not url:
        log.error("thiếu ETL_DATABASE_URL")
        return 2
    try:
        results = to_results(read_csv(Path(path)))
    except (OSError, ValueError) as e:
        log.error("CSV hỏng: %s", e)
        return 2
    engine = sa.create_engine(url, pool_pre_ping=True)
    try:
        if dry_run:
            try:
                with engine.connect() as conn:
                    tx = conn.begin()
                    st = _seed(conn, results)
                    st.update(_outstanding(conn, checks))
                    tx.rollback()
                print(" ".join(f"{k}={v}" for k, v in st.items()), flush=True)
                return 0
            except KeyboardInterrupt:
                log.warning("omo seed dry-run dừng tay (Ctrl+C)")
                return 130
            except Exception:  # noqa: BLE001 — job biên ngoài, không có ops.etl_run để đóng
                log.exception("omo seed dry-run thất bại")
                return 2
        run_id = omo_store.open_run(engine, JOB)
        try:
            with engine.begin() as conn:
                st = _seed(conn, results)
                st.update(_outstanding(conn, checks))
            omo_store.close_run(engine, run_id, "success", st)
            print(" ".join(f"{k}={v}" for k, v in st.items()), flush=True)
            return 0
        except KeyboardInterrupt:
            omo_store.close_run(engine, run_id, "failed", error="dừng tay (Ctrl+C)")
            return 130
        except Exception as e:  # noqa: BLE001 — job biên ngoài
            omo_store.close_run(engine, run_id, "failed", error=f"{type(e).__name__}: {e}")
            log.exception("omo seed thất bại")
            return 2
    finally:
        engine.dispose()
