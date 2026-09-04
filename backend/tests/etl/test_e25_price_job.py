import contextlib
import json
import os
import pathlib

import pytest
import sqlalchemy as sa

from etl import __main__ as cli
from etl import price_fetch, price_job, price_store

FIX = pathlib.Path(__file__).parent / "fixtures" / "price"
TEXT = {"ZZAORG": (FIX / "bid-page1-20260903.json").read_text(encoding="utf-8"),
        "ZZBORG": (FIX / "dmx-page1-20260903.json").read_text(encoding="utf-8"),
        "ZZCORG": (FIX / "bid-page52-20260903.json").read_text(encoding="utf-8")}
EMPTY = json.dumps({"page": 1, "pageSize": 60, "totalCount": 0, "items": [], "status": "Success", "errors": None})
INVALID = json.dumps({"page": 1, "pageSize": 60, "totalCount": 0, "items": None,
                      "status": "Failed", "errors": ["Code not valid: ZZBORG"]})
SEED = [("ZZA", "ZZAORG"), ("ZZB", "ZZBORG"), ("ZZC", "ZZCORG")]
MINE = ["ZZA", "ZZB", "ZZC"]


def _get(invalid=()):
    def get(url):
        code = url.split("Code=")[1].split("&")[0]
        if code in invalid:
            return 200, INVALID
        return 200, TEXT.get(code, EMPTY)        # mã của test khác trong DB test: rỗng, không phải lỗi
    return get


def _wire(monkeypatch, invalid=()):
    # KHÔNG dựng DSN từ engine.url — mật khẩu lộ ra traceback (§5). Đọc thẳng biến môi trường.
    monkeypatch.setenv("ETL_DATABASE_URL", os.environ["TEST_DATABASE_URL"])
    monkeypatch.setattr("etl.price_job.load_dotenv", lambda *a, **k: None)

    @contextlib.contextmanager
    def fake_open_fetcher():
        yield price_fetch.Fetcher(_get(invalid), sleep=lambda s: None)

    monkeypatch.setattr("etl.price_fetch.open_fetcher", fake_open_fetcher)

    # Job toàn tập (không --codes) đi qua MỌI cổ phiếu listed của DB test — kể cả mã test khác
    # commit và không dọn (test_e10). Fake fetch trả rỗng cho chúng, và từ review 2026-09-04 mã
    # rỗng ĐƯỢC ĐẾM vào guard (i) ⇒ 2/5 > 2 % từ chối. Không xoá dữ liệu của test khác (bài học
    # lát 2); thay vào đó bọc list_codes THẬT rồi giữ lại đúng mã ZZ* — truy vấn thật vẫn chạy,
    # `subset` vẫn False nên baseline/domain_state vẫn đi qua.
    real_list_codes = price_store.list_codes

    def only_mine(conn, tickers=None):
        cl = real_list_codes(conn, tickers)
        return price_store.CodeList([c for c in cl.codes if c.ticker.startswith("ZZ")],
                                    [t for t in cl.no_organ_code if t.startswith("ZZ")])

    monkeypatch.setattr("etl.price_store.list_codes", only_mine)


def _cleanup(engine):
    """Dọn ĐÚNG thứ mình cắm (mã ZZ*), không dọn cả bảng — bài học review lát 2 (#5)."""
    with engine.begin() as c:
        sids = c.execute(sa.text("SELECT security_id FROM market.security WHERE ticker LIKE 'ZZ%'")).scalars().all()
        iids = c.execute(sa.text("SELECT issuer_id FROM market.issuer_external_id"
                                 " WHERE source = 'fiintrade' AND external_code LIKE 'ZZ%ORG'")).scalars().all()
        c.execute(sa.text("DELETE FROM market.price_daily WHERE security_id = ANY(:s)"), {"s": sids})
        c.execute(sa.text("DELETE FROM market.security WHERE security_id = ANY(:s)"), {"s": sids})
        c.execute(sa.text("DELETE FROM market.issuer_external_id WHERE issuer_id = ANY(:i)"), {"i": iids})
        c.execute(sa.text("DELETE FROM market.issuer WHERE issuer_id = ANY(:i)"), {"i": iids})
        c.execute(sa.text("DELETE FROM ops.etl_run WHERE job IN ('market.price_daily', 'market.price_backfill')"))
        c.execute(sa.text("DELETE FROM staging.raw_payload WHERE endpoint_key = 'price:refusal'"))
        c.execute(sa.text("DELETE FROM ops.data_domain_state WHERE domain = 'market.price'"))


@pytest.fixture()
def price_db(migrated_engine):
    """Dọn TRƯỚC và SAU — teardown chạy cả khi test đỏ."""
    _cleanup(migrated_engine)
    with migrated_engine.begin() as c:
        for t, org in SEED:
            iid = c.execute(sa.text("INSERT INTO market.issuer (name) VALUES (:n) RETURNING issuer_id"),
                            {"n": t}).scalar_one()
            c.execute(sa.text("INSERT INTO market.issuer_external_id (issuer_id, source, external_code)"
                              " VALUES (:i, 'fiintrade', :c)"), {"i": iid, "c": org})
            c.execute(sa.text("INSERT INTO market.security (ticker, exchange, security_type, issuer_id)"
                              " VALUES (:t, 'HOSE', 'stock', :i)"), {"t": t, "i": iid})
    yield migrated_engine
    _cleanup(migrated_engine)


ROWS = ("SELECT count(*) FROM market.price_daily p JOIN market.security s USING (security_id)"
        " WHERE s.ticker LIKE 'ZZ%'")
LAST = "SELECT status, stats, error FROM ops.etl_run WHERE job = :j ORDER BY run_id DESC LIMIT 1"


def _last(engine, job):
    with engine.begin() as c:
        return c.execute(sa.text(LAST), {"j": job}).one()


def _rows(engine):
    with engine.begin() as c:
        return c.execute(sa.text(ROWS)).scalar_one()


def test_missing_env_exits_two(monkeypatch):
    monkeypatch.delenv("ETL_DATABASE_URL", raising=False)
    monkeypatch.setattr("etl.price_job.load_dotenv", lambda *a, **k: None)
    assert price_job.run() == 2


def test_daily_run_writes_rows_records_stats_and_domain_state_then_is_idempotent(price_db, monkeypatch):
    _wire(monkeypatch)
    assert price_job.run() == 0
    status, stats, _ = _last(price_db, "market.price_daily")
    with price_db.begin() as c:
        wm = c.execute(sa.text("SELECT watermark FROM ops.data_domain_state WHERE domain = 'market.price'")).scalar_one()
    assert _rows(price_db) == 24 and status == "success"                 # 5 + 18 + 1 phiên của ba fixture
    assert stats["with_data"] == 3 and stats["rows_sent"] == 24 and stats["rows_changed"] == 24
    assert stats["invalid"] == 0 and stats["failed"] == 0 and stats["raw_close_mismatch"] == 0
    assert stats["empty"] == 0 and stats["no_organ_code_count"] == 0            # review 2026-09-04
    assert stats["latest_trading_date"] == "2026-09-03" and wm == "2026-09-03"
    assert "subset" not in stats
    assert price_job.run() == 0                                          # lượt hai: không dòng nào đổi
    _, stats2, _ = _last(price_db, "market.price_daily")
    assert _rows(price_db) == 24 and stats2["rows_sent"] == 24 and stats2["rows_changed"] == 0


def test_guard_refusal_writes_nothing_and_leaves_evidence(price_db, monkeypatch):
    _wire(monkeypatch, invalid=("ZZBORG",))                              # 1/3 mã sai = 33 % > 2 %
    assert price_job.run(codes=MINE) == 1
    status, stats, err = _last(price_db, "market.price_daily")
    with price_db.begin() as c:
        ev = c.execute(sa.text("SELECT meta FROM staging.raw_payload WHERE endpoint_key = 'price:refusal'")).scalar_one()
    assert _rows(price_db) == 0 and status == "failed" and "1/3 mã" in err
    assert stats["invalid_tickers"] == ["ZZB"] and stats["subset"] is True
    assert ev["reasons"] and "quá 2%" in ev["reasons"][0]


def test_subset_run_does_not_become_the_baseline_nor_move_the_domain_watermark(price_db, monkeypatch):
    _wire(monkeypatch)
    assert price_job.run(codes=["ZZA"]) == 0
    assert price_store.load_baseline(price_db) is None
    with price_db.begin() as c:
        assert c.execute(sa.text("SELECT count(*) FROM ops.data_domain_state WHERE domain = 'market.price'")).scalar_one() == 0


def test_backfill_budget_stops_after_one_code_and_the_next_run_resumes_to_the_end(price_db, monkeypatch):
    _wire(monkeypatch)
    with price_db.connect() as c:
        order = [x.ticker for x in price_store.list_codes(c).codes]
    assert price_job.run(backfill=True, max_minutes=0) == 0            # ngân sách 0: xong mã đầu rồi dừng
    _, s1, _ = _last(price_db, "market.price_backfill")
    assert (s1["cursor"], s1["codes_done"], s1["budget_hit"], s1["pass_complete"]) == (order[0], 1, True, False)
    assert price_job.run(backfill=True) == 0
    _, s2, _ = _last(price_db, "market.price_backfill")
    assert (s2["cursor"], s2["codes_done"], s2["pass_complete"]) == (order[-1], len(order) - 1, True)
    assert s2["dup_dates"] == 0 and s2["raw_close_mismatch"] == 0             # backfill cũng có hai mắt này
    assert _rows(price_db) == 24
    assert price_job.run(backfill=True, max_minutes=0) == 0            # hết vòng ⇒ vòng mới từ mã đầu
    _, s3, _ = _last(price_db, "market.price_backfill")
    assert s3["cursor"] == order[0]


def test_backfill_with_codes_touches_neither_cursor_nor_pass_flag(price_db, monkeypatch):
    _wire(monkeypatch)
    assert price_job.run(backfill=True, codes=["ZZB"]) == 0
    _, s, _ = _last(price_db, "market.price_backfill")
    assert s["subset"] is True and s["cursor"] is None and s["pass_complete"] is False
    assert s["codes_done"] == 1 and s["rows_sent"] == 18 and price_store.load_cursor(price_db) is None


def test_job_runs_under_the_etl_role(price_db, monkeypatch):
    """§3.5: mọi đường đọc/ghi của cả hai chế độ phải chạy dưới đúng quyền production."""
    _wire(monkeypatch)
    real_create = price_job.sa.create_engine

    def create_engine_with_role(url, **kw):
        eng = real_create(url, **kw)

        @sa.event.listens_for(eng, "connect")
        def _set_role(dbapi_conn, _rec):
            cur = dbapi_conn.cursor(); cur.execute("SET ROLE dlck_etl"); cur.close()

        return eng

    monkeypatch.setattr(price_job.sa, "create_engine", create_engine_with_role)
    # Review 2026-09-04: lượt --codes là `subset`, KHÔNG đi qua load_baseline (đọc etl_run),
    # upsert_domain_state (ghi data_domain_state) và store_refusal_evidence (ghi staging) —
    # đúng ba đường §3.5 từng cắn. Phải chạy lượt TOÀN TẬP, lượt bị từ chối, và backfill toàn tập.
    assert price_job.run() == 0
    assert price_job.run() == 0                                   # lượt hai đọc mốc qua load_baseline
    _wire(monkeypatch, invalid=("ZZBORG",))
    monkeypatch.setattr(price_job.sa, "create_engine", create_engine_with_role)
    assert price_job.run(codes=MINE) == 1                         # store_refusal_evidence dưới role
    _wire(monkeypatch)
    monkeypatch.setattr(price_job.sa, "create_engine", create_engine_with_role)
    assert price_job.run(backfill=True) == 0                      # save_progress + load_cursor dưới role


def test_codes_without_any_organ_code_fail_loudly_not_as_a_source_outage(price_db, monkeypatch):
    """Review 2026-09-04: --codes trỏ vào mã niêm yết chưa có organCode ⇒ tập gọi rỗng. Guard (0)
    sẽ nói "nguồn hỏng" — sai hướng chẩn đoán. Phải lỗi rõ ở tham số, trước khi gọi nguồn."""
    _wire(monkeypatch)
    with price_db.begin() as c:
        c.execute(sa.text("INSERT INTO market.security (ticker, exchange, security_type)"
                          " VALUES ('ZZN', 'HOSE', 'stock')"))
    assert price_job.run(codes=["ZZN"]) == 2
    _, _, err = _last(price_db, "market.price_daily")
    assert "organCode" in err and "nguồn hỏng" not in err


def test_engine_pre_pings_pooled_connections_that_died_while_the_machine_slept(price_db, monkeypatch):
    """Máy ngủ theo lịch 02:00 (chủ dự án): kết nối Postgres nằm trong pool suốt 38 phút fetch
    thường chết sau giấc ngủ (Docker/WSL reset mạng). pool_pre_ping thay nó trước khi dùng, thay vì
    ném OperationalError ở load_baseline/giao dịch ghi sau khi đã gọi xong 1.523 lời gọi."""
    _wire(monkeypatch)
    seen = {}
    real_create = price_job.sa.create_engine

    def create_engine_recording(url, **kw):
        seen.update(kw)
        return real_create(url, **kw)

    monkeypatch.setattr(price_job.sa, "create_engine", create_engine_recording)
    assert price_job.run(codes=["ZZA"]) == 0
    assert seen.get("pool_pre_ping") is True


def test_backfill_budget_counts_wall_clock_so_a_sleep_ends_the_run_at_wake(price_db, monkeypatch):
    """Ngân sách --max-minutes tính theo đồng hồ TƯỜNG: máy ngủ 4 giờ giữa chừng thì thức dậy là hết
    ngân sách ⇒ dừng sau mã đang dở, không chạy lấn vào giờ giao dịch với phần ngân sách còn lại."""
    _wire(monkeypatch)
    ticks = iter([1_000.0] + [1_000.0 + 4 * 3600.0] * 50)      # lần gọi đầu: đặt hạn; các lần sau: đã ngủ 4 h
    # Patch seam của job, KHÔNG patch time.time toàn cục: SQLAlchemy pool cũng gọi time.time() khi
    # tạo kết nối (open_run chạy trước khi đặt hạn) và ăn mất tick đầu ⇒ hạn đặt sai, test xanh giả.
    monkeypatch.setattr(price_job, "_wall_clock", lambda: next(ticks))
    assert price_job.run(backfill=True, max_minutes=60) == 0
    _, s, _ = _last(price_db, "market.price_backfill")
    assert s["codes_done"] == 1 and s["budget_hit"] is True and s["pass_complete"] is False


def test_next_open_is_0845_of_the_next_weekday():
    """Task backfill chạy tay buổi tối hoặc tự động sáng thứ 7: hạn là 08:45 của NGÀY GIAO DỊCH kế
    tiếp — tối thứ 3 ⇒ sáng thứ 4; thứ 7 ⇒ thứ 2; thứ 6 sau 08:45 ⇒ thứ 2. Chưa biết ngày lễ."""
    from datetime import datetime
    VN = price_job.VN
    f = price_job._next_open
    assert f(datetime(2026, 9, 5, 0, 5, tzinfo=VN)) == datetime(2026, 9, 7, 8, 45, tzinfo=VN)    # thứ 7 → thứ 2
    assert f(datetime(2026, 9, 8, 20, 0, tzinfo=VN)) == datetime(2026, 9, 9, 8, 45, tzinfo=VN)   # tối thứ 3 → thứ 4
    assert f(datetime(2026, 9, 4, 9, 0, tzinfo=VN)) == datetime(2026, 9, 7, 8, 45, tzinfo=VN)    # thứ 6 09:00 → thứ 2
    assert f(datetime(2026, 9, 7, 8, 0, tzinfo=VN)) == datetime(2026, 9, 7, 8, 45, tzinfo=VN)    # thứ 2 08:00 → hôm nay


def test_stop_before_open_ends_the_run_at_the_next_trading_morning(price_db, monkeypatch):
    from datetime import datetime
    _wire(monkeypatch)
    target = price_job._next_open(datetime.now(price_job.VN)).timestamp()
    monkeypatch.setattr(price_job, "_wall_clock", lambda: target + 1)      # đồng hồ đã qua 08:45 ngày giao dịch kế
    assert price_job.run(backfill=True, stop_before_open=True) == 0
    _, s, _ = _last(price_db, "market.price_backfill")
    assert s["codes_done"] == 1 and s["budget_hit"] is True
    assert s["stop_at"] == datetime.fromtimestamp(target, price_job.VN).isoformat(timespec="minutes")


def test_ctrl_c_closes_the_run_as_failed_with_a_reason_and_exits_130(price_db, monkeypatch):
    """Ctrl+C là cách dừng chính thức của cửa sổ task (nút X đã khoá) — không được để lượt treo
    'running' trong ops.etl_run với traceback KeyboardInterrupt."""
    _wire(monkeypatch)

    def boom(self, code, max_pages=1):
        raise KeyboardInterrupt

    monkeypatch.setattr(price_fetch.Fetcher, "pages", boom)
    assert price_job.run(backfill=True) == 130
    status, stats, err = _last(price_db, "market.price_backfill")
    assert status == "failed" and "Ctrl+C" in err and stats["codes_done"] == 0
    assert price_job.run() == 130
    status, _, err = _last(price_db, "market.price_daily")
    assert status == "failed" and "Ctrl+C" in err


def test_cli_parses_backfill_codes_and_max_minutes(monkeypatch):
    seen = {}
    monkeypatch.setattr("etl.price_job.run", lambda **kw: seen.update(kw) or 0)
    assert cli.main(["price", "--backfill", "--codes", "bid, dmx", "--max-minutes", "5",
                     "--stop-before-open"]) == 0
    assert seen == {"backfill": True, "codes": ["BID", "DMX"], "max_minutes": 5.0, "stop_before_open": True}
    assert cli.main(["price"]) == 0
    assert seen == {"backfill": False, "codes": None, "max_minutes": None, "stop_before_open": False}
