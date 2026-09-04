"""Danh sách tới hạn và ghi kết quả họ Snapshot (spec §5.4). SQL thuần.

KHÔNG có con trỏ, và không cần: `ops.snapshot_check.checked_at` CHÍNH LÀ con trỏ —
lượt sau tự lấy nhóm cũ nhất chưa tới lượt, nên lượt bị giết giữa chừng không mất chỗ.
"""
from __future__ import annotations

import datetime as dt
import json
import logging
from dataclasses import dataclass

import sqlalchemy as sa

from etl.snapshot_fetch import KINDS, Target
from etl.snapshot_guard import Tally, Verdict
from etl.snapshot_normalize import keep_hash

log = logging.getLogger("etl.snapshot")

JOB = "market.snapshot"
DOMAIN = "market.snapshot"
SOURCE = "fiintrade"

MAX_EVIDENCE = 20                                  # đủ để nhìn ra vì sao guard từ chối
MAX_TRIGGER = 300                                  # trần nhánh trigger/lượt — xem due_list()
COLD_START = dt.date(1900, 1, 1)                   # mốc khởi tạo của load_watermark()

CADENCE_DAYS = {"snapshot": 90, "valuation": 30, "ownership": 30, "dividend": 30}
QUOTA = {"snapshot": 24, "valuation": 70, "ownership": 70, "dividend": 70}
# Một loại sự kiện có thể bắn NHIỀU kind: `outstandingShare` nằm trong tập trắng của CẢ
# `snapshot` lẫn `valuation`, và ShareIssuance/StockDividend là hai loại duy nhất làm nó đổi
# (review #7) — CashDividend không đổi số cổ phiếu nên chỉ bắn `dividend`.
TRIGGER_KINDS = {"Earning": ("snapshot",), "ShareIssuance": ("snapshot", "valuation"),
                 "CashDividend": ("dividend",), "StockDividend": ("snapshot", "valuation")}

# Vũ trụ: issuer có ÍT NHẤT một cổ phiếu đang niêm yết. Quỹ/ETF tự rơi ra vì không có
# security dạng stock (đo 2026-09-04) — không cần luật loại riêng.
_UNIVERSE = """
WITH uni AS (
  SELECT i.issuer_id, x.external_code AS organ_code, i.com_type_code,
         (SELECT s.ticker FROM market.security s
           WHERE s.issuer_id = i.issuer_id AND s.status = 'listed' AND s.security_type = 'stock'
           ORDER BY s.security_id LIMIT 1) AS ticker
  FROM market.issuer i
  JOIN market.issuer_external_id x ON x.issuer_id = i.issuer_id AND x.source = 'fiintrade'
  WHERE EXISTS (SELECT 1 FROM market.security s
                 WHERE s.issuer_id = i.issuer_id AND s.status = 'listed'
                   AND s.security_type = 'stock')
)
"""


def load_watermark(conn) -> dt.date:
    got = conn.execute(sa.text(
        "SELECT watermark FROM ops.data_domain_state"
        " WHERE domain = :d AND source = :s"), {"d": DOMAIN, "s": SOURCE}).scalar()
    return dt.date.fromisoformat(got) if got else COLD_START


def _target(row, kind: str, found_by: str) -> Target:
    return Target(kind=kind, issuer_id=row.issuer_id, organ_code=row.organ_code,
                  ticker=row.ticker, com_type=row.com_type_code, found_by=found_by)


def due_list(conn, watermark: dt.date, kinds=None, codes=None,
             quota=None, cadence=None, max_trigger=None) -> list[Target]:
    kinds = list(kinds or KINDS)
    quota = quota or QUOTA
    cadence = cadence or CADENCE_DAYS
    max_trigger = max_trigger or MAX_TRIGGER

    if codes:                                   # lượt ép: mọi kind, bỏ qua nhịp và quota
        rows = conn.execute(sa.text(
            _UNIVERSE + "SELECT * FROM uni WHERE ticker = ANY(:codes) ORDER BY ticker"),
            {"codes": list(codes)}).all()
        return [_target(r, k, "floor") for r in rows for k in kinds]

    out: list[Target] = []
    seen: set[tuple[int, str]] = set()

    event_types = [t for t, ks in TRIGGER_KINDS.items() if any(k in kinds for k in ks)]
    if event_types and watermark == COLD_START:
        # Cold start: chưa có dòng data_domain_state ⇒ mốc là 1900-01-01 ⇒ điều kiện
        # `public_date > watermark` đúng cho MỌI sự kiện từng có — gần trọn vũ trụ × nhiều
        # kind, hàng nghìn lời gọi. Quét sàn (nhánh B) đã tự phủ trọn sàn trong 30/90 ngày,
        # không cần bắn trigger cho toàn bộ lịch sử ở lượt đầu (review, phát hiện #2).
        log.info("bỏ qua nhánh trigger: mốc nước còn ở mốc khởi tạo %s (cold start) —"
                 " quét sàn sẽ tự phủ trong 30/90 ngày", COLD_START.isoformat())
    elif event_types:
        rows = conn.execute(sa.text(
            _UNIVERSE + """
            SELECT DISTINCT u.*, e.event_type, e.public_date
            FROM uni u
            JOIN market.corporate_event e ON e.issuer_id = u.issuer_id
            WHERE e.event_type = ANY(:types)
              AND e.public_date > :wm
            ORDER BY e.public_date ASC, u.issuer_id
            LIMIT :limit
            """), {"types": event_types, "wm": watermark, "limit": max_trigger + 1}).all()
        if len(rows) > max_trigger:
            # Một mã hỏng dai dẳng giữ mốc đứng yên ⇒ danh sách trigger phình mỗi ngày, không
            # có đường tự thoát nếu không có trần. Lấy public_date CŨ NHẤT trước để không bỏ
            # sót vĩnh viễn cái cũ (review, phát hiện #2).
            log.info("nhánh trigger vượt trần %d: cắt %d target, giữ %d cũ nhất theo public_date",
                     max_trigger, len(rows) - max_trigger, max_trigger)
            rows = rows[:max_trigger]
        for r in rows:
            for kind in TRIGGER_KINDS[r.event_type]:
                if kind not in kinds:
                    continue
                if (r.issuer_id, kind) not in seen:
                    seen.add((r.issuer_id, kind))
                    out.append(_target(r, kind, "event"))

    for kind in kinds:
        rows = conn.execute(sa.text(
            _UNIVERSE + """
            SELECT u.* FROM uni u
            LEFT JOIN ops.snapshot_check c ON c.issuer_id = u.issuer_id AND c.kind = :kind
            WHERE c.checked_at IS NULL
               OR c.checked_at < now() - make_interval(days => :cadence)
            ORDER BY c.checked_at NULLS FIRST, u.issuer_id
            LIMIT :quota
            """), {"kind": kind, "cadence": cadence[kind], "quota": quota[kind]}).all()
        for r in rows:
            if (r.issuer_id, kind) not in seen:      # trigger đã lấy rồi thì thôi
                seen.add((r.issuer_id, kind))
                out.append(_target(r, kind, "floor"))
    return out


@dataclass
class Fetched:
    target: Target
    item: dict
    text: str


def apply(conn, fetched: list[Fetched], run_date: dt.date) -> tuple[Tally, int]:
    """Ghi KHI ĐỔI vào snapshot_daily; mọi lượt kiểm đều cập nhật sổ kiểm."""
    tally, written = Tally(), 0
    for f in fetched:
        t = f.target
        tally.checked += 1
        h = keep_hash(t.kind, f.item)
        prev = conn.execute(sa.text(
            "SELECT keep_hash FROM ops.snapshot_check"
            " WHERE issuer_id = :i AND kind = :k"), {"i": t.issuer_id, "k": t.kind}).scalar()

        if prev is None:
            tally.first += 1
            changed = True
        else:
            changed = prev != h
            if t.found_by == "floor":
                tally.floor_compared += 1
                tally.changed_floor += int(changed)
            elif changed:
                tally.changed_event += 1
            if not changed:
                tally.unchanged += 1

        if changed:
            conn.execute(sa.text(
                "INSERT INTO market.snapshot_daily (issuer_id, trading_date, kind, payload)"
                " VALUES (:i, :d, :k, cast(:p AS jsonb))"
                " ON CONFLICT (issuer_id, trading_date, kind) DO UPDATE"
                " SET payload = excluded.payload, ingested_at = now()"),
                {"i": t.issuer_id, "d": run_date, "k": t.kind,
                 "p": json.dumps(f.item, ensure_ascii=False)})
            written += 1

        # clock_timestamp(), KHÔNG now(): trong CÙNG một giao dịch (fixture test `db`, và mọi
        # lượt apply() thật đều chạy trong một giao dịch) now() đứng yên ở giờ transaction bắt
        # đầu — hai lần gọi apply() liên tiếp sẽ ra CÙNG một checked_at. Bài học đã có sẵn ở
        # events_store.py/price_store.py (ingested_at = clock_timestamp()); áp lại ở đây vì
        # test đo đúng tính đơn điệu của checked_at.
        conn.execute(sa.text(
            "INSERT INTO ops.snapshot_check (issuer_id, kind, checked_at, keep_hash,"
            " changed_at, found_by) VALUES (:i, :k, clock_timestamp(), :h, clock_timestamp(), :f)"
            " ON CONFLICT (issuer_id, kind) DO UPDATE"
            " SET checked_at = clock_timestamp(), keep_hash = :h, found_by = :f,"
            "     changed_at = CASE WHEN :c THEN clock_timestamp()"
            "                       ELSE ops.snapshot_check.changed_at END"),
            {"i": t.issuer_id, "k": t.kind, "h": h, "f": t.found_by, "c": changed})
    return tally, written


def new_watermark(conn) -> dt.date:
    """Mốc 'sự kiện MỚI CÔNG BỐ' — CHỈ `public_date`.

    Bug thật đo 2026-09-22 (`--codes A32,BAB,BVB`): bản cũ lấy `max(greatest(public_date,
    exright_date))`. `exright_date` là ngày KHÔNG HƯỞNG QUYỀN — nguồn công bố nó có thể xa
    hơn hôm nay hàng tuần/tháng — nên một dòng như vậy kéo watermark vượt luôn ngày hiện
    tại, làm điều kiện trigger `public_date > :wm` của due_list() không bao giờ đúng cho
    bất kỳ sự kiện MỚI nào công bố trước cái mốc giả đó. `public_date` không bao giờ ở
    tương lai nên tự nó đã là thước đo "mới với ta" đúng nghĩa — không cần trộn cột nào
    khác. Việc re-crawl giá theo `exright_date` chuyển hẳn sang `recrawl_codes()`, không
    dùng watermark nữa.
    """
    got = conn.execute(sa.text(
        "SELECT max(public_date) FROM market.corporate_event")).scalar()
    return got or dt.date(1900, 1, 1)


def recrawl_codes(conn, days: int = 3) -> list[str]:
    """Mã có ngày không hưởng quyền VỪA ĐI QUA trong `days` ngày gần đây.

    Không dùng watermark: mốc nước đo "sự kiện mới công bố", còn việc re-crawl giá phải xảy
    ra khi ngày ex ĐÃ QUA (trước ngày ex thì chuỗi close_adj chưa đổi, kéo về cũng vô ích).
    Cửa sổ vài ngày để một hôm job không chạy cũng không mất; kéo lại nhiều lần là vô hại vì
    `etl price --backfill --codes` idempotent.

    CHỈ ba loại `CashDividend`/`StockDividend`/`ShareIssuance` — đúng spec §5.6 gốc, bị đánh
    rơi khi viết lại theo cửa sổ ngày ở vòng trước. Đây là ba loại DUY NHẤT đổi hệ số điều
    chỉnh giá; `AGM` (ngày chốt quyền dự đại hội) và `IPO` cũng có `exright_date` nhưng không
    đụng tới chuỗi `close_adj` — kéo lại là phí. Số đo thật (kho production, 2026-09-04):
    bản không lọc loại trả 8 mã (DCF·KSV·PVO·RYG·SAS·SMT·TCH·VXT) mà 6/10 sự kiện của chúng
    là AGM; lọc lại còn đúng 2 mã (RYG, TCH) thật sự cần backfill trọn ~12,5 năm lịch sử.
    """
    rows = conn.execute(sa.text(
        _UNIVERSE + """
        SELECT DISTINCT u.ticker FROM uni u
        JOIN market.corporate_event e ON e.issuer_id = u.issuer_id
        WHERE e.exright_date BETWEEN current_date - :days AND current_date
          AND e.event_type IN ('CashDividend', 'StockDividend', 'ShareIssuance')
        ORDER BY u.ticker
        """), {"days": days}).scalars().all()
    return list(rows)


def upsert_domain_state(engine, watermark: str) -> None:
    with engine.begin() as conn:
        conn.execute(sa.text(
            "INSERT INTO ops.data_domain_state (domain, source, status, last_success_at, watermark)"
            " VALUES (:d, :s, 'active', now(), :w)"
            " ON CONFLICT (domain, source) DO UPDATE"
            " SET last_success_at = now(), watermark = :w, status = 'active'"),
            {"d": DOMAIN, "s": SOURCE, "w": watermark})


def store_refusal_evidence(engine, fetched: list[Fetched], run_id: int, verdict: Verdict) -> None:
    """Bằng chứng ở giao dịch RIÊNG — lượt chính đã rollback. Ưu tiên bản ghi của nhóm quét sàn."""
    picked = [f for f in fetched if f.target.found_by == "floor"][:MAX_EVIDENCE] or fetched[:MAX_EVIDENCE]
    meta = json.dumps({"run_id": run_id, "reasons": verdict.reasons}, ensure_ascii=False)
    with engine.begin() as conn:
        for f in picked:
            conn.execute(sa.text(
                "INSERT INTO staging.raw_payload (source, endpoint_key, content_type, payload, meta)"
                " VALUES ('snapshot', :ek, 'json', cast(:p AS jsonb), cast(:m AS jsonb))"),
                {"ek": f"snapshot:{f.target.kind}:{f.target.organ_code}", "p": f.text, "m": meta})
