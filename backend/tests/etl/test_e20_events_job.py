import json
import os
import pathlib

import pytest
import sqlalchemy as sa

from etl import events_job

FIX = pathlib.Path(__file__).parent / "fixtures" / "events"
NAME = {"AGM": "agm", "CashDividend": "cashdividend", "StockDividend": "stockdividend",
        "Earning": "earning", "IPO": "ipo", "ShareIssuance": "shareissuance"}


def _pages(broken=None):
    out = {}
    for fam, stem in NAME.items():
        text = (FIX / f"{stem}-sample-20260903.json").read_text(encoding="utf-8")
        if fam == broken:                                  # bỏ 1 bản ghi ⇒ vế (i) đỏ
            d = json.loads(text)
            d["items"] = d["items"][:-1]
            text = json.dumps(d, ensure_ascii=False)
        out[fam] = [text]
    return out


def _wire(monkeypatch, engine, pages):
    # KHÔNG dựng DSN từ engine.url với hide_password=False — mật khẩu sẽ lộ nguyên văn ra
    # mọi traceback `--showlocals` và log CI chạm frame này (§5). Đọc thẳng biến môi trường,
    # đúng khuôn `test_e15_screener_job.py`.
    monkeypatch.setenv("ETL_DATABASE_URL", os.environ["TEST_DATABASE_URL"])
    monkeypatch.setattr("etl.events_fetch.fetch", lambda: (pages, 0))
    monkeypatch.setattr("etl.events_job.load_dotenv", lambda *a, **k: None)
    # 🔴 Fixture CỐ Ý dày đặc ca biên: 4 trùng / 28 bản ghi = 14,3%, trong khi lượt thật là
    # 42/110.737 = 0,037%. Ngưỡng 0,5% của vế (iv) đúng cho lượt thật và SAI cho fixture —
    # không có dòng này thì job bị chính guard của nó từ chối và 3 test dưới đỏ.
    # File này kiểm ĐẤU NỐI của job; ngưỡng do test_e18 sở hữu — nới ở đây, KHÔNG nới ở đó.
    monkeypatch.setattr("etl.events_guard.DUP_RATIO", 0.5)


def _fixture_codes():
    """17 organ_code của fixture — chỉ dọn đúng chúng."""
    from etl import events_normalize as en
    return sorted({r.organ_code for r in en.normalize(_pages()).rows})


def _cleanup(engine):
    """Dọn ĐÚNG thứ mình cắm, không dọn cả bảng.

    Khuôn `test_e15_screener_job.py`: `test_e10_refdata_job` commit thật 8 issuer
    `fiintrade` và chúng sống qua cả phiên pytest — `test_e19` dựa vào trạng thái đó.
    `DELETE FROM market.issuer_external_id WHERE source='fiintrade'` sẽ xoá luôn chúng
    và phá hai file test kia nếu file này chạy trước (đổi tên file, `-k`, hay plugin
    đổi thứ tự là đủ).
    """
    codes = _fixture_codes()
    with engine.begin() as c:
        # Lấy id TRƯỚC: `issuer_external_id` trỏ tới `issuer`, xoá issuer trước là vỡ FK,
        # mà xoá `issuer_external_id` trước thì mất luôn đường tra id.
        ids = c.execute(sa.text(
            "SELECT issuer_id FROM market.issuer_external_id"
            " WHERE source = 'fiintrade' AND external_code = ANY(:codes)"),
            {"codes": codes}).scalars().all()
        if ids:
            c.execute(sa.text("DELETE FROM market.corporate_event WHERE issuer_id = ANY(:ids)"),
                      {"ids": ids})
            c.execute(sa.text("DELETE FROM market.issuer_external_id WHERE issuer_id = ANY(:ids)"),
                      {"ids": ids})
            c.execute(sa.text("DELETE FROM market.issuer WHERE issuer_id = ANY(:ids)"), {"ids": ids})
        c.execute(sa.text("DELETE FROM ops.etl_run WHERE job = 'market.events'"))
        c.execute(sa.text("DELETE FROM staging.raw_payload WHERE endpoint_key = 'events:refusal'"))


@pytest.fixture()
def events_db(migrated_engine):
    """Dọn TRƯỚC và SAU mỗi test — teardown chạy **cả khi test đỏ**.

    Gọi `_cleanup` bằng tay ở cuối thân test thì một assert đỏ giữa chừng để lại 24 dòng
    `corporate_event` đã commit, và mọi `count(*)` của test sau đỏ theo — chuỗi lỗi giả
    che mất lỗi thật.
    """
    _cleanup(migrated_engine)
    yield migrated_engine
    _cleanup(migrated_engine)


def test_missing_env_exits_two(monkeypatch):
    monkeypatch.delenv("ETL_DATABASE_URL", raising=False)
    monkeypatch.setattr("etl.events_job.load_dotenv", lambda *a, **k: None)
    assert events_job.run() == 2


ROWS_OF_FIXTURE = (
    "SELECT count(*) FROM market.corporate_event ce"
    " JOIN market.issuer_external_id x USING (issuer_id)"
    " WHERE x.source = 'fiintrade' AND x.external_code = ANY(:codes)")


def test_full_run_writes_rows_and_records_stats(events_db, monkeypatch):
    _wire(monkeypatch, events_db, _pages())
    assert events_job.run(accept_new=True) == 0     # 17 < ngưỡng 20 nên cờ không đổi kết quả,
    with events_db.begin() as c:                    # nhưng phải chấp nhận được — xem test cờ dưới
        n = c.execute(sa.text(ROWS_OF_FIXTURE), {"codes": _fixture_codes()}).scalar_one()
        stats = c.execute(sa.text(
            "SELECT stats FROM ops.etl_run WHERE job = 'market.events'"
            " ORDER BY run_id DESC LIMIT 1")).scalar_one()
        wm = c.execute(sa.text(
            "SELECT watermark FROM ops.data_domain_state"
            " WHERE domain = 'market.events'")).scalar_one()
    assert n == 24
    assert stats["rows_written"] == 24 and stats["issuers_created"] == 17
    assert stats["dup_conflicts"] == 4 and len(stats["dup_keys"]) == 4
    # Nêu TÊN khoá, không chỉ đếm (§5.3, bài học 3 của lát 1): bốn khoá đụng phải là
    # SASTECO (AGM), ABI của StockDividend, và hai issueMethodName của ABI ở ShareIssuance.
    assert sum(1 for k in stats["dup_keys"] if k.startswith("ShareIssuance|ABI|")) == 2
    assert any(k.startswith("AGM|SASTECO|2018-03-27|") for k in stats["dup_keys"])
    assert any(k.startswith("StockDividend|ABI|2025-09-04|") for k in stats["dup_keys"])
    assert wm == "2026-09-03"                              # publicDate lớn nhất trong fixture


def test_second_run_is_idempotent(events_db, monkeypatch):
    _wire(monkeypatch, events_db, _pages())
    assert events_job.run(accept_new=True) == 0
    assert events_job.run() == 0
    with events_db.begin() as c:
        n = c.execute(sa.text(ROWS_OF_FIXTURE), {"codes": _fixture_codes()}).scalar_one()
        stats = c.execute(sa.text(
            "SELECT stats FROM ops.etl_run WHERE job = 'market.events'"
            " ORDER BY run_id DESC LIMIT 1")).scalar_one()
    assert n == 24 and stats["issuers_created"] == 0
    assert "accept_new" not in stats                       # lượt không cờ không được đóng dấu


def test_accept_new_is_recorded_in_stats(events_db, monkeypatch):
    """Ai đó đã bấm qua chốt chặn (iii) thì `etl_run` phải giữ dấu vết — khuôn `refdata`
    ghi `accept_drop`. Không có dấu này thì ba tháng sau nhìn `issuers_created: 517`
    không phân biệt được 'người duyệt' với 'guard hỏng'."""
    _wire(monkeypatch, events_db, _pages())
    assert events_job.run(accept_new=True) == 0
    with events_db.begin() as c:
        stats = c.execute(sa.text(
            "SELECT stats FROM ops.etl_run WHERE job = 'market.events'"
            " ORDER BY run_id DESC LIMIT 1")).scalar_one()
    assert stats["accept_new"] is True


def test_guard_refusal_writes_nothing_and_leaves_evidence(events_db, monkeypatch):
    _wire(monkeypatch, events_db, _pages(broken="AGM"))
    assert events_job.run() == 1
    with events_db.begin() as c:
        assert c.execute(sa.text(ROWS_OF_FIXTURE),
                         {"codes": _fixture_codes()}).scalar_one() == 0
        # 🔴 issuer cũng phải bị rollback — chúng được tạo TRONG cùng giao dịch
        assert c.execute(sa.text(
            "SELECT count(*) FROM market.issuer_external_id"
            " WHERE external_code = '12681'")).scalar_one() == 0
        status, err = c.execute(sa.text(
            "SELECT status, error FROM ops.etl_run WHERE job = 'market.events'"
            " ORDER BY run_id DESC LIMIT 1")).one()
        ev = c.execute(sa.text(
            "SELECT count(*) FROM staging.raw_payload"
            " WHERE endpoint_key = 'events:refusal'")).scalar_one()
    assert status == "failed" and "thiếu trang" in err and ev == 1


def test_minting_too_many_issuers_is_refused_end_to_end(events_db, monkeypatch):
    """AC4 vế thứ hai: chốt chặn (iii) phải từ chối Ở MỨC JOB, không chỉ ở hàm thuần.

    Bơm 21 organCode lạ vào một họ ⇒ `issuers_new = 38 > 20` mà không có cờ ⇒ từ chối,
    và KHÔNG dòng nào — kể cả issuer vừa đúc — được ghi.
    """
    pages = _pages()
    d = json.loads(pages["IPO"][0])
    base = d["items"][0]
    d["items"] = d["items"] + [{**base, "organCode": f"LA{i:03d}", "ticker": f"L{i:03d}",
                                "publicDate": f"2019-0{i % 9 + 1}-01T00:00:00"} for i in range(21)]
    d["totalCount"] = len(d["items"])
    pages["IPO"] = [json.dumps(d, ensure_ascii=False)]
    _wire(monkeypatch, events_db, pages)
    assert events_job.run() == 1
    with events_db.begin() as c:
        assert c.execute(sa.text(
            "SELECT count(*) FROM market.issuer_external_id"
            " WHERE source = 'fiintrade' AND external_code LIKE 'LA%'")).scalar_one() == 0
        status, err = c.execute(sa.text(
            "SELECT status, error FROM ops.etl_run WHERE job = 'market.events'"
            " ORDER BY run_id DESC LIMIT 1")).one()
    assert status == "failed" and "issuer tối thiểu" in err and "--accept-new" in err
    # KHÔNG chạy lại với cờ ở đây: lượt đó sẽ ghi 21 issuer `LA*` mà `_cleanup` không biết
    # dọn (nó chỉ dọn 17 mã của fixture). Việc cờ đi được tới job đã có test riêng ở trên.


def test_job_runs_under_the_etl_role(events_db, monkeypatch):
    """§3.5: mọi đường đọc/ghi của job phải chạy dưới đúng quyền production."""
    _wire(monkeypatch, events_db, _pages())
    real_create = events_job.sa.create_engine

    def create_engine_with_role(url, **kw):
        eng = real_create(url, **kw)

        @sa.event.listens_for(eng, "connect")
        def _set_role(dbapi_conn, _rec):
            cur = dbapi_conn.cursor(); cur.execute("SET ROLE dlck_etl"); cur.close()

        return eng

    monkeypatch.setattr(events_job.sa, "create_engine", create_engine_with_role)
    assert events_job.run(accept_new=True) == 0
