import threading
import time
from datetime import date
from decimal import Decimal

import pytest
import sqlalchemy as sa

from etl.omo_flow import rebuild
from etl.omo_parse import OmoResult, OmoRow
from etl.omo_store import store

R1 = OmoResult(
    session_date=date(2026, 8, 14),
    rows=[
        OmoRow("reverse_repo", 7, 4, 4, Decimal("6307.47") * 10**9, Decimal("4.5")),
        OmoRow("reverse_repo", 35, 4, 4, Decimal("3466.54") * 10**9, Decimal("4.5")),
    ],
    groups_present=frozenset({"reverse_repo"}),
)


def test_store_writes_session_auction_staging(db):
    stats = store(R1, "<html>raw</html>", db)
    assert stats == {"sessions": 1, "auctions": 2}
    s = db.execute(sa.text(
        "SELECT has_reverse_repo, has_repo, has_outright_sale FROM macro.omo_session"
        " WHERE session_date = '2026-08-14'")).one()
    assert tuple(s) == (True, False, False)
    vol = db.execute(sa.text(
        "SELECT volume_vnd FROM macro.omo_auction WHERE session_date='2026-08-14'"
        " AND op_type='reverse_repo' AND tenor_days=7")).scalar_one()
    assert vol == Decimal("6307470000000")
    raw = db.execute(sa.text(
        "SELECT content_type, body, meta FROM staging.raw_payload"
        " WHERE source='sbv' AND endpoint_key='omo'")).one()
    assert raw.content_type == "html" and raw.body == "<html>raw</html>"
    assert raw.meta["bytes"] == len("<html>raw</html>".encode())


def test_store_skips_duplicate_date(db):
    store(R1, "x" , db)
    assert store(R1, "x", db) == {"skipped": True}
    n = db.execute(sa.text("SELECT count(*) FROM macro.omo_auction")).scalar_one()
    assert n == 2


def _seed(db, d, tenor, vol_billion, op="reverse_repo"):
    db.execute(sa.text(
        "INSERT INTO macro.omo_session (session_date, crawled_at, has_reverse_repo,"
        " has_repo, has_outright_sale) VALUES (:d, now(), true, false, false)"
        " ON CONFLICT DO NOTHING"), {"d": d})
    db.execute(sa.text(
        "INSERT INTO macro.omo_auction (session_date, op_type, tenor_days, volume_vnd)"
        " VALUES (:d, :op, :t, :v)"),
        {"d": d, "op": op, "t": tenor, "v": Decimal(str(vol_billion)) * 10**9})


def test_store_writes_note_when_merged_else_null(db):
    """`store()` phải ghi `note` bằng đúng chuỗi `_session_note` sinh ra khi `result.merged`
    dương (nhánh seed FiinProX gộp dòng), và giữ `note` NULL khi `merged == 0` (đường crawl
    thường, R1)."""
    merged_result = OmoResult(
        session_date=date(2026, 2, 3),
        rows=[OmoRow("reverse_repo", 7, 16, 16, Decimal("40731.40") * 10**9, Decimal("4.5"))],
        groups_present=frozenset({"reverse_repo"}),
        merged=1,
    )
    store(merged_result, "<html/>", db)
    note = db.execute(sa.text(
        "SELECT note FROM macro.omo_session WHERE session_date = '2026-02-03'")).scalar_one()
    assert note == "gộp 1 dòng cùng kỳ hạn"

    store(R1, "<html/>", db)
    note_r1 = db.execute(sa.text(
        "SELECT note FROM macro.omo_session WHERE session_date = '2026-08-14'")).scalar_one()
    assert note_r1 is None


def test_flow_hand_solved(db):
    _seed(db, date(2026, 8, 14), 7, "6307.47")
    _seed(db, date(2026, 8, 21), 7, "5000")
    rebuild(db)
    r = db.execute(sa.text(
        "SELECT injection_vnd, maturing_vnd, net_vnd, complete FROM macro.omo_flow"
        " WHERE flow_date = '2026-08-21'")).one()
    assert r.injection_vnd == Decimal("5000") * 10**9
    assert r.maturing_vnd == Decimal("6307.47") * 10**9
    assert r.net_vnd == Decimal("-1307.47") * 10**9
    assert r.complete is False        # price_daily rỗng → không đánh giá được cửa sổ


def test_flow_outright_sale_is_maturing_not_negative_injection(db):
    """IMPORTANT 5 review cuối — `injection_vnd`/`maturing_vnd` là HAI CHIỀU TIỀN, đều
    KHÔNG ÂM, đúng nghĩa tên cột trong migration 0005 ("bơm trong ngày" / "đáo hạn").

    Trước fix, hai cột lưu số đã bù trừ dấu nên phát hành tín phiếu ra cột injection ÂM.
    Giải tay: SBV bán hẳn 1.000 tỷ tại D ⇒ D hút 1.000 tỷ (maturing), D+7 khi tín phiếu
    đáo hạn thì tiền trả lại thị trường ⇒ D+7 bơm 1.000 tỷ (injection).
    """
    _seed(db, date(2026, 8, 14), 7, "1000", op="outright_sale")
    rebuild(db)
    d = db.execute(sa.text(
        "SELECT injection_vnd, maturing_vnd, net_vnd FROM macro.omo_flow"
        " WHERE flow_date='2026-08-14'")).one()
    assert d.injection_vnd == 0
    assert d.maturing_vnd == Decimal("1000") * 10**9
    assert d.net_vnd == Decimal("-1000") * 10**9          # phát hành tín phiếu = hút ròng
    m = db.execute(sa.text(
        "SELECT injection_vnd, maturing_vnd, net_vnd FROM macro.omo_flow"
        " WHERE flow_date='2026-08-21'")).one()
    assert m.injection_vnd == Decimal("1000") * 10**9
    assert m.maturing_vnd == 0
    assert m.net_vnd == Decimal("1000") * 10**9           # đáo hạn tín phiếu = bơm trả lại


def test_flow_mixed_session_keeps_both_directions_separate(db):
    """Phiên HỖN HỢP (SBV vừa cho vay vừa phát hành tín phiếu) — giải tay:
    reverse_repo 10.000 tỷ phát hành tại D ⇒ bơm 10.000 tỷ;
    outright_sale 4.000 tỷ phát hành tại D ⇒ hút 4.000 tỷ;
    net = 10.000 − 4.000 = +6.000 tỷ. Luật bù trừ dấu cũ cho injection = 6.000 tỷ, mất
    hẳn thông tin quy mô hai chiều.
    """
    _seed(db, date(2026, 8, 14), 7, "10000", op="reverse_repo")
    _seed(db, date(2026, 8, 14), 91, "4000", op="outright_sale")
    rebuild(db)
    r = db.execute(sa.text(
        "SELECT injection_vnd, maturing_vnd, net_vnd FROM macro.omo_flow"
        " WHERE flow_date='2026-08-14'")).one()
    assert r.injection_vnd == Decimal("10000") * 10**9
    assert r.maturing_vnd == Decimal("4000") * 10**9
    assert r.net_vnd == Decimal("6000") * 10**9


def test_flow_rebuild_idempotent(db):
    _seed(db, date(2026, 8, 14), 7, "6307.47")
    rebuild(db)
    first = db.execute(sa.text("SELECT * FROM macro.omo_flow ORDER BY flow_date")).all()
    rebuild(db)
    assert db.execute(sa.text("SELECT * FROM macro.omo_flow ORDER BY flow_date")).all() == first


def test_flow_rebuild_works_under_etl_role(db):
    """Regression: rebuild phải chạy được với QUYỀN THẬT của role dlck_etl.

    Bộ test khác chạy bằng user owner nên không thấy: `TRUNCATE` đòi quyền chủ
    bảng, trong khi migration 0009 chỉ cấp SELECT/INSERT/UPDATE/DELETE cho
    dlck_etl → job thật chết giữa chừng (bắt được khi chạy `python -m etl omo`
    lần đầu, 2026-08-26).
    """
    _seed(db, date(2026, 8, 14), 7, "6307.47")
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    rebuild(db)
    db.execute(sa.text("RESET ROLE"))
    n = db.execute(sa.text("SELECT count(*) FROM macro.omo_flow")).scalar_one()
    assert n == 2


def test_close_run_never_wipes_stats_it_was_not_given(migrated_engine):
    """Regression: mọi job gọi `close_run("success", stats)` rồi mới làm nốt vài bước sau
    (`upsert_domain_state`…). Bước sau ném lỗi ⇒ handler biên ngoài gọi lại
    `close_run("failed", error=…)` với `stats=None`. Trước khi có `coalesce`, lượt đó
    MẤT TRẮNG counts/rows_written/watermark của phần việc đã ghi xong — nhìn lại chỉ
    thấy `failed` với stats rỗng, không biết đã ghi được gì.
    """
    from etl.omo_store import close_run, open_run

    run_id = open_run(migrated_engine, "test.close_run")
    close_run(migrated_engine, run_id, "success", {"rows_written": 42, "watermark": "2026-09-03"})
    close_run(migrated_engine, run_id, "failed", error="upsert_domain_state nổ sau khi ghi xong")

    with migrated_engine.begin() as c:
        status, stats, error = c.execute(sa.text(
            "SELECT status, stats, error FROM ops.etl_run WHERE run_id = :r"), {"r": run_id}).one()
        c.execute(sa.text("DELETE FROM ops.etl_run WHERE run_id = :r"), {"r": run_id})
    assert status == "failed"                       # trạng thái phản ánh cái hỏng sau cùng
    assert stats == {"rows_written": 42, "watermark": "2026-09-03"}   # nhưng stats CÒN NGUYÊN
    assert "upsert_domain_state" in error


def test_close_run_still_overwrites_stats_when_given_new_ones(migrated_engine):
    """Mặt kia của `coalesce`: đưa stats mới thì phải ghi đè, không phải gộp hay bỏ qua."""
    from etl.omo_store import close_run, open_run

    run_id = open_run(migrated_engine, "test.close_run")
    close_run(migrated_engine, run_id, "success", {"a": 1})
    close_run(migrated_engine, run_id, "success", {"b": 2})
    with migrated_engine.begin() as c:
        stats = c.execute(sa.text("SELECT stats FROM ops.etl_run WHERE run_id = :r"),
                          {"r": run_id}).scalar_one()
        c.execute(sa.text("DELETE FROM ops.etl_run WHERE run_id = :r"), {"r": run_id})
    assert stats == {"b": 2}


def test_store_khong_no_khi_tien_trinh_khac_dang_ghi_dung_phien_do(migrated_engine):
    """Cửa sổ giữa kiểm-tồn-tại và ghi của `store()`, ở ĐÚNG mức cô lập production dùng.

    🔴 Vì sao có test này (rà chuẩn hoá 2026-09-08): `store()` từng `SELECT 1 ... WHERE
    session_date` rồi mới `INSERT`. Tiến trình B đi qua `SELECT` trong lúc A **chưa commit** sẽ
    thấy trống, đi thẳng vào `INSERT`, chờ A, rồi đụng `omo_session_pkey` — lượt chạy chết với
    mã 2 như thể nguồn hỏng, trong khi phiên đó đã có người ghi đúng. Lát 13 đặt job vào
    container `restart: unless-stopped` kèm chạy bù, nên hai lượt chồng lấn là chuyện thường.

    🔴 Phải dùng luồng thật, KHÔNG mô phỏng bằng `REPEATABLE READ`: cách đó tái hiện được cửa
    sổ, nhưng `ON CONFLICT DO NOTHING` dưới `REPEATABLE READ` ném `SerializationFailure` — một
    hành vi đúng của Postgres mà production **không bao giờ chạm** vì job chạy ở
    `READ COMMITTED` mặc định. Đo được 2026-09-08 khi thử đúng cách đó: test đỏ vì một lý do
    KHÁC hẳn lý do cần bắt.

    Không có `sleep` mù: chờ tới khi B **thật sự bị khoá** (`pg_stat_activity`) rồi mới commit A.
    """
    d = R1.session_date
    ket_qua: dict = {}

    def tien_trinh_b():
        b = migrated_engine.connect()
        try:
            with b.begin():
                ket_qua["ra"] = store(R1, "x", b)
        except Exception as e:                       # noqa: BLE001 - ghi lại để assert ở luồng chính
            ket_qua["loi"] = e
        finally:
            b.close()

    a = migrated_engine.connect()
    tx_a = a.begin()
    try:
        a.execute(sa.text(
            "INSERT INTO macro.omo_session (session_date, crawled_at, has_reverse_repo,"
            " has_repo, has_outright_sale) VALUES (:d, now(), true, false, false)"), {"d": d})

        t = threading.Thread(target=tien_trinh_b, daemon=True)
        t.start()
        han = time.monotonic() + 15
        while time.monotonic() < han:
            with migrated_engine.connect() as w:
                bi_khoa = w.execute(sa.text(
                    "SELECT count(*) FROM pg_stat_activity WHERE wait_event_type = 'Lock'"
                    " AND query LIKE '%omo_session%'")).scalar_one()
            if bi_khoa:
                break
            time.sleep(0.05)
        else:
            pytest.fail("B không bao giờ bị khoá — phép tái hiện không còn bắt đúng cửa sổ")

        tx_a.commit()
        t.join(15)
        assert not t.is_alive()
        assert "loi" not in ket_qua, f"B nổ thay vì bỏ qua: {ket_qua.get('loi')!r}"
        assert ket_qua["ra"] == {"skipped": True}
        n = a.execute(sa.text(
            "SELECT count(*) FROM macro.omo_auction WHERE session_date = :d"),
            {"d": d}).scalar_one()
        assert n == 0                                # bỏ TRỌN lượt, không ghi nửa vời
    finally:
        a.close()
        with migrated_engine.begin() as c:           # dọn dòng đã commit của chính test này
            c.execute(sa.text("DELETE FROM macro.omo_auction WHERE session_date = :d"), {"d": d})
            c.execute(sa.text("DELETE FROM macro.omo_session WHERE session_date = :d"), {"d": d})
