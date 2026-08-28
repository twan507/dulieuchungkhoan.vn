"""Ghi trạng thái đích refdata vào Postgres (spec §4-5).

`apply`/`plan_delist` chạy TRONG giao dịch đang mở của caller (không tự commit) —
điều phối (`open_run`/`close_run`) là việc của `refdata_job`. `load_baseline` và
`store_refusal_evidence` nhận ENGINE, tự mở giao dịch riêng của chính chúng.

Ngữ nghĩa ghi (spec §5) — bám sát, không suy diễn:
- `issuer` nhận diện qua `issuer_external_id('fiintrade', organ_code)`, KHÔNG qua tên.
  `industry_id` do ETL SỞ HỮU (bước 4c, lớp 1 theo `industry_icb_map`); lớp tay nằm ở
  `market.issuer_industry_override`, ETL không đọc không ghi. Đường đọc:
  `market.v_issuer_industry` = COALESCE(tay, máy).
- `security` khớp theo TICKER một mình — đổi sàn giữ nguyên `security_id`.
- `updated_at` chỉ đổi khi có trường thật đổi (`IS DISTINCT FROM`); `ingested_at`
  chỉ ghi lúc INSERT, không bao giờ UPDATE.
- Không xoá dòng ở bất kỳ bảng nào — huỷ niêm yết là UPDATE status, không DELETE.
"""
from __future__ import annotations

import json

import logging

import sqlalchemy as sa

from etl.refdata_merge import TargetState

log = logging.getLogger(__name__)

JOB = "market.refdata"

# Vắng khỏi danh bạ doanh nghiệp bao lâu thì coi là đã rời sàn (market-data-store §4.4).
# Có ngưỡng vì mã MỚI niêm yết xuất hiện ở bảng giá BVSC trước khi vào danh bạ FiinTrade —
# lật ngay lượt đầu là bắn nhầm mã vừa lên sàn.
DIRECTORY_ABSENT_DAYS = 3


def load_baseline(engine) -> dict | None:
    """Mốc so sánh cho chốt chặn tầng 1 — lượt `success` gần nhất của job này."""
    with engine.connect() as c:
        row = c.execute(
            sa.text(
                "SELECT stats FROM ops.etl_run WHERE job = :j AND status = 'success'"
                " ORDER BY finished_at DESC LIMIT 1"
            ),
            {"j": JOB},
        ).first()
    if row is None:
        return None
    stats = row[0]
    return stats.get("counts") if stats else None


def plan_delist(conn, target: TargetState) -> tuple[list[str], int, int]:
    """(ticker vắng khỏi đích, TỔNG số dòng listed sẽ bị lật delisted, tổng listed).

    Phép lật đi qua HAI đường và tầng 2 của chốt chặn phải thấy cả hai (final
    review I1 — bản đầu chỉ đếm đường vắng-mặt, nên đường phổ biến nhất — mã rời
    /quotes nhưng còn ở FiinTrade, tức CÓ trong đích với status='delisted' —
    tàng hình trước chốt chặn và stats báo 0):
      (a) vắng hẳn khỏi đích  → lật bằng câu UPDATE hàng loạt cuối `apply`;
      (b) có trong đích nhưng đích ghi 'delisted' → lật bằng UPDATE từng dòng.
    """
    rows = conn.execute(
        sa.text("SELECT ticker FROM market.security WHERE status = 'listed'")
    ).all()
    listed = {r[0] for r in rows}
    target_tickers = {t.ticker for t in target.securities}
    target_delisted = {t.ticker for t in target.securities if t.status == "delisted"}
    absent = sorted(listed - target_tickers)
    # Đường (c) — cổ phiếu CÓ trong bảng giá nhưng vắng khỏi danh bạ doanh nghiệp đủ
    # lâu (§4.4). Đọc dấu do các lượt TRƯỚC đóng: `apply` của lượt này mới cập nhật
    # dấu cho lượt sau, nên ngưỡng đếm theo ngày thật, không phải theo một lượt chạy.
    stale = [
        r[0]
        for r in conn.execute(
            sa.text(
                "SELECT ticker FROM market.security"
                " WHERE status = 'listed' AND security_type = 'stock'"
                "   AND issuer_id IS NULL AND directory_absent_since IS NOT NULL"
                "   AND directory_absent_since <= now() - make_interval(days => :d)"
            ),
            {"d": DIRECTORY_ABSENT_DAYS},
        ).all()
    ]
    absent = sorted(set(absent) | set(stale))
    flips = len(absent) + len(listed & target_delisted)
    return absent, flips, len(listed)


def apply(conn, target: TargetState, delist: list[str]) -> dict:
    """Upsert 5 bảng trong giao dịch đang mở của caller. Không commit, không xoá."""
    stats = {
        "sec_inserted": 0,
        "sec_updated": 0,
        "sec_unchanged": 0,
        "delisted": 0,
        "exchange_moves": 0,
        "issuers_inserted": 0,
        "icb_rows": 0,
    }

    # 1. issuer — nhận diện qua issuer_external_id('fiintrade', organ_code)
    issuer_id_by_organ: dict[str, int] = {}
    for it in target.issuers:
        row = conn.execute(
            sa.text(
                "SELECT issuer_id FROM market.issuer_external_id"
                " WHERE source = 'fiintrade' AND external_code = :oc"
            ),
            {"oc": it.organ_code},
        ).first()
        if row is None:
            issuer_id = conn.execute(
                sa.text(
                    "INSERT INTO market.issuer (name, short_name, com_type_code, icb_code)"
                    " VALUES (:n, :s, :c, :ic) RETURNING issuer_id"
                ),
                {"n": it.name, "s": it.short_name, "c": it.com_type_code, "ic": it.icb_code},
            ).scalar_one()
            conn.execute(
                sa.text(
                    "INSERT INTO market.issuer_external_id (issuer_id, source, external_code)"
                    " VALUES (:i, 'fiintrade', :oc)"
                ),
                {"i": issuer_id, "oc": it.organ_code},
            )
            stats["issuers_inserted"] += 1
        else:
            issuer_id = row[0]
            # industry_id gán ở bước 4c (lớp 1) — không nhét vào câu này để updated_at không nhảy oan.
            conn.execute(
                sa.text(
                    "UPDATE market.issuer SET name = :n, short_name = :s,"
                    " com_type_code = :c, icb_code = :ic, updated_at = now()"
                    " WHERE issuer_id = :i AND (name, short_name, com_type_code, icb_code)"
                    " IS DISTINCT FROM (:n, :s, :c, :ic)"
                ),
                {"n": it.name, "s": it.short_name, "c": it.com_type_code, "ic": it.icb_code,
                 "i": issuer_id},
            )
        issuer_id_by_organ[it.organ_code] = issuer_id

    # 2. security — khớp theo TICKER một mình
    security_id_by_ticker: dict[str, int] = {}
    for s in target.securities:
        issuer_id = issuer_id_by_organ.get(s.organ_code) if s.organ_code is not None else None
        row = conn.execute(
            sa.text(
                "SELECT security_id, exchange, security_type, status, tradelot, full_name, issuer_id"
                " FROM market.security WHERE ticker = :t"
                " ORDER BY (status = 'listed') DESC, updated_at DESC LIMIT 1"
            ),
            {"t": s.ticker},
        ).first()
        if row is None:
            security_id = conn.execute(
                sa.text(
                    "INSERT INTO market.security"
                    " (ticker, exchange, security_type, issuer_id, status, tradelot, full_name)"
                    " VALUES (:t, :e, :ty, :iid, :st, :tl, :fn) RETURNING security_id"
                ),
                {"t": s.ticker, "e": s.exchange, "ty": s.security_type, "iid": issuer_id,
                 "st": s.status, "tl": s.tradelot, "fn": s.full_name},
            ).scalar_one()
            stats["sec_inserted"] += 1
        else:
            security_id = row.security_id
            changed = (row.exchange, row.security_type, row.status, row.tradelot,
                       row.full_name, row.issuer_id) != (
                s.exchange, s.security_type, s.status, s.tradelot, s.full_name, issuer_id)
            conn.execute(
                sa.text(
                    "UPDATE market.security SET exchange = :e, security_type = :ty,"
                    " status = :st, tradelot = :tl, full_name = :fn, issuer_id = :iid,"
                    " updated_at = now()"
                    " WHERE security_id = :i AND (exchange, security_type, status, tradelot,"
                    " full_name, issuer_id) IS DISTINCT FROM (:e, :ty, :st, :tl, :fn, :iid)"
                ),
                {"e": s.exchange, "ty": s.security_type, "st": s.status, "tl": s.tradelot,
                 "fn": s.full_name, "iid": issuer_id, "i": security_id},
            )
            if changed:
                stats["sec_updated"] += 1
                if row.status == "listed" and s.status == "delisted":
                    stats["delisted"] += 1     # đường lật (b) — xem plan_delist
                if row.exchange != s.exchange:
                    stats["exchange_moves"] += 1
            else:
                stats["sec_unchanged"] += 1
        security_id_by_ticker[s.ticker] = security_id

        # 3. security_external_id
        for source, code, sub in s.external_ids:
            conn.execute(
                sa.text(
                    "INSERT INTO market.security_external_id"
                    " (security_id, source, external_code, external_sub)"
                    " VALUES (:i, :src, :code, :sub)"
                    " ON CONFLICT (source, external_code) DO NOTHING"
                ),
                {"i": security_id, "src": source, "code": code, "sub": sub},
            )

    # 3b. Dấu vắng danh bạ — bookkeeping cho luật huỷ niêm yết (§4.4). Cố ý KHÔNG
    # đụng `updated_at`: đây là quan sát của job về nguồn, không phải trường dữ liệu
    # của mã. Đóng dấu một lần rồi thôi (điều kiện IS NULL), gỡ khi mã quay lại.
    cleared = conn.execute(
        sa.text(
            "UPDATE market.security SET directory_absent_since = NULL"
            " WHERE directory_absent_since IS NOT NULL AND issuer_id IS NOT NULL"
        )
    ).rowcount
    marked = conn.execute(
        sa.text(
            "UPDATE market.security SET directory_absent_since = now()"
            " WHERE directory_absent_since IS NULL AND issuer_id IS NULL"
            "   AND security_type = 'stock' AND status = 'listed'"
        )
    ).rowcount
    stats["directory_absent_cleared"] = cleared
    stats["directory_absent_marked"] = marked

    # 4. icb_industry
    for r in target.icb:
        conn.execute(
            sa.text(
                "INSERT INTO market.icb_industry"
                " (icb_code, icb_name, parent_icb_code, icb_level, icb_code_path)"
                " VALUES (:c, :n, :p, :l, :path)"
                " ON CONFLICT (icb_code) DO UPDATE SET icb_name = EXCLUDED.icb_name,"
                " parent_icb_code = EXCLUDED.parent_icb_code, icb_level = EXCLUDED.icb_level,"
                " icb_code_path = EXCLUDED.icb_code_path"
                " WHERE (icb_industry.icb_name, icb_industry.parent_icb_code,"
                " icb_industry.icb_level, icb_industry.icb_code_path)"
                " IS DISTINCT FROM (EXCLUDED.icb_name, EXCLUDED.parent_icb_code,"
                " EXCLUDED.icb_level, EXCLUDED.icb_code_path)"
            ),
            {"c": r.icb_code, "n": r.icb_name, "p": r.parent_icb_code, "l": r.icb_level,
             "path": r.icb_code_path},
        )
        stats["icb_rows"] += 1

    # 4b. Mã ICB biến mất khỏi nguồn: GIỮ NGUYÊN dòng (issuer.icb_code có thể còn trỏ
    # tới — không FK nhưng vẫn là tham chiếu), chỉ đếm + log (spec §5).
    if target.icb:
        orphaned = conn.execute(
            sa.text("SELECT count(*) FROM market.icb_industry"
                    " WHERE NOT (icb_code = ANY(:codes))"),
            {"codes": [r.icb_code for r in target.icb]},
        ).scalar_one()
        stats["icb_orphaned"] = orphaned
        if orphaned:
            log.warning("%d mã ICB trong kho không còn ở nguồn — giữ nguyên, không xoá", orphaned)
    else:
        stats["icb_orphaned"] = 0

    # 4c. LỚP 1 — gán industry_id theo industry_icb_map (spec lát ngành hai lớp §2).
    # ETL SỞ HỮU cột này: sửa map ICB rồi chạy lại job là toàn bộ doanh nghiệp cập nhật
    # theo. Lớp tay nằm ở market.issuer_industry_override, ETL không đọc không ghi.
    # Luật phân giải: khớp icb_code chính xác trước; không có thì leo icb_code_path lấy
    # TỔ TIÊN GẦN NHẤT — gần nhất = ở VỊ TRÍ cuối nhất trong path (mọi mã ICB đều 4 ký
    # tự nên sắp theo độ dài là tie-break rỗng nghĩa).
    conn.execute(
        sa.text(
            "UPDATE market.issuer iss SET industry_id = r.industry_id, updated_at = now()"
            " FROM ("
            "   SELECT i.issuer_id, COALESCE("
            "     (SELECT m.industry_id FROM market.industry_icb_map m"
            "       WHERE m.icb_code = i.icb_code),"
            "     (SELECT m.industry_id FROM market.icb_industry t"
            "        JOIN market.industry_icb_map m"
            "          ON m.icb_code = ANY(string_to_array(t.icb_code_path, '/'))"
            "       WHERE t.icb_code = i.icb_code"
            "       ORDER BY array_position(string_to_array(t.icb_code_path, '/'), m.icb_code)"
            "         DESC LIMIT 1)"
            "   ) AS industry_id"
            "   FROM market.issuer i"
            " ) AS r"
            " WHERE iss.issuer_id = r.issuer_id"
            "   AND iss.industry_id IS DISTINCT FROM r.industry_id"
        )
    )
    # Số đo TRẠNG THÁI toàn bảng sau lượt gán (gauge), không phải số phát sinh trong lượt
    # như các counter khác cùng dict — đặt tên theo đúng nghĩa đó. Đếm trên
    # market.v_issuer_industry (COALESCE tay + máy), KHÔNG trên cột issuer.industry_id
    # thẳng — issuer.industry_id chỉ là lớp 1, một issuer có override tay mà mã ICB
    # chưa vào map vẫn CÓ ngành qua view dù cột lớp 1 NULL.
    stats["issuers_without_industry"] = conn.execute(
        sa.text(
            "SELECT count(*) FROM market.issuer iss"
            " LEFT JOIN market.v_issuer_industry v ON v.issuer_id = iss.issuer_id"
            " WHERE v.industry_id IS NULL"
        )
    ).scalar_one()
    if stats["issuers_without_industry"]:
        log.warning(
            "%d doanh nghiệp không tra được ngành (cả tay lẫn máy) — để NULL, không chặn job",
            stats["issuers_without_industry"],
        )

    # Chốt chặn luật BCTC (spec §2b): com_type_code NH|CK|BH ⟺ ngành NGANHANG|
    # CHUNGKHOAN|BAOHIEM, không ngoại lệ. Ba ngành đó là ba MẪU BÁO CÁO TÀI CHÍNH
    # khác nhau — trộn một doanh nghiệp thường vào là hỏng mọi phép tính trên nhóm.
    # Đếm, cảnh báo, KHÔNG chặn job: một mã mới niêm yết gán lệch không đáng để mất
    # cả lượt danh bạ.
    stats["bctc_violations"] = conn.execute(
        sa.text(
            "SELECT count(*) FROM market.issuer iss"
            " LEFT JOIN market.v_issuer_industry v ON v.issuer_id = iss.issuer_id"
            " LEFT JOIN market.industry i ON i.industry_id = v.industry_id"
            " WHERE (coalesce(iss.com_type_code, '') = 'NH')"
            "        IS DISTINCT FROM (coalesce(i.code, '') = 'NGANHANG')"
            "    OR (coalesce(iss.com_type_code, '') = 'CK')"
            "        IS DISTINCT FROM (coalesce(i.code, '') = 'CHUNGKHOAN')"
            "    OR (coalesce(iss.com_type_code, '') = 'BH')"
            "        IS DISTINCT FROM (coalesce(i.code, '') = 'BAOHIEM')"
        )
    ).scalar_one()
    if stats["bctc_violations"]:
        log.warning(
            "%d doanh nghiệp vi phạm luật BCTC (com_type_code ⟺ ngành tài chính)"
            " — xem market.v_issuer_industry",
            stats["bctc_violations"],
        )

    # 5. delist — không bao giờ xoá dòng
    if delist:
        result = conn.execute(
            sa.text(
                "UPDATE market.security SET status = 'delisted', updated_at = now()"
                " WHERE ticker = ANY(:t) AND status = 'listed'"
            ),
            {"t": delist},
        )
        stats["delisted"] += result.rowcount   # đường lật (a) — cộng dồn với đường (b)

    return stats


def store_refusal_evidence(engine, raw: dict[str, str], run_id: int, reasons: list[str]) -> None:
    """Ghi bằng chứng khi từ chối — GIAO DỊCH RIÊNG, chỉ dùng khi guard từ chối (spec §4.3)."""
    meta = json.dumps({"run_id": run_id, "reasons": reasons})
    with engine.begin() as conn:
        for key, text in raw.items():
            conn.execute(
                sa.text(
                    "INSERT INTO staging.raw_payload (source, endpoint_key, content_type, payload, meta)"
                    " VALUES ('refdata', :ek, 'json', cast(:p AS jsonb), cast(:m AS jsonb))"
                ),
                {"ek": f"refdata:{key}", "p": text, "m": meta},
            )


def upsert_domain_state(engine, watermark: str) -> None:
    """Hai dòng trạng thái nguồn (spec §5) — khuôn `omo_store.upsert_domain_state`."""
    with engine.begin() as conn:
        for source in ("bvsc", "fiintrade"):
            conn.execute(
                sa.text(
                    "INSERT INTO ops.data_domain_state"
                    " (domain, source, status, last_success_at, watermark)"
                    " VALUES ('market.reference', :src, 'active', now(), :w)"
                    " ON CONFLICT (domain, source) DO UPDATE"
                    " SET last_success_at = now(), watermark = :w, status = 'active'"
                ),
                {"src": source, "w": watermark},
            )
