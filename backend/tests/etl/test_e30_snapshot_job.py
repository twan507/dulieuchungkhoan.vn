import os
import pathlib
from datetime import date

import pytest
import sqlalchemy as sa

from etl import snapshot_job as sj
from etl import snapshot_store as ss

FIX = pathlib.Path(__file__).parent / "fixtures" / "snapshot"
ORGAN, TICKER = "ZZJOB", "ZZJ"
# snapshot_guard.MIN_SAMPLE = 20 (test_e28: "hệ thống chạy bình thường không được tự phạm luật")
# — một lượt --codes MỘT mã (4 target) không bao giờ chạm ngưỡng này. Test guard-từ-chối phải
# seed đủ 20 mã, giới hạn 1 kind, để tỷ lệ hỏng thật sự vượt ngưỡng.
BATCH = [f"ZZW{i:02d}" for i in range(20)]
ALL_ORGANS = [ORGAN] + BATCH


def _payload(kind):
    name = {"snapshot": "A32-snapshot.json", "ownership": "A32-ownership.json",
            "dividend": "A32-dividend.json", "valuation": "A32-valuation.json"}[kind]
    return (FIX / name).read_text(encoding="utf-8")


def _fake_get(counters=None):
    """get(url, timeout) giả — trả đúng mẫu thật theo endpoint trong URL."""
    def get(u, timeout):
        if counters is not None:
            counters.append(u)
        kind = ("snapshot" if "/Snapshot/" in u else
                "ownership" if "/Ownership/" in u else
                "dividend" if "/CashDividendAnalysis/" in u else "valuation")
        return 200, _payload(kind)
    return get


def _wire(monkeypatch):
    # KHÔNG dựng DSN từ engine.url — mật khẩu lộ ra traceback (§5). Đọc thẳng biến môi trường,
    # đúng khuôn test_e20_events_job.py / test_e25_price_job.py.
    monkeypatch.setenv("ETL_DATABASE_URL", os.environ["TEST_DATABASE_URL"])
    monkeypatch.setattr("etl.snapshot_job.load_dotenv", lambda *a, **k: None)
    # Chặn mạng THẬT cho mọi test trong file: `_recrawl` chạy ở LƯỢT ĐẦY ĐỦ (không --codes/
    # --kinds — vòng sửa 4 chặn hẳn nhánh lượt con, xem `run()`), và khi chạy nó quét
    # `market.corporate_event` TOÀN CỤC trong cửa sổ vài ngày — nếu bảng test còn sót dòng có
    # exright_date gần đây do file test khác để lại, `_recrawl` sẽ gọi thẳng
    # `etl.price_job.run(...)` KHÔNG có `get` giả (review vòng 1, phát hiện #2). Patch này vẫn
    # để mặc định cho MỌI test trong file, kể cả lượt con — phòng hờ, không phải vì lượt con
    # còn gọi tới `_recrawl`.
    # Không test nào ở đây kiểm nội dung re-crawl nên fake trả 0 là đủ, không cần giả lập gì thêm.
    monkeypatch.setattr("etl.price_job.run", lambda **kw: 0)


def _cleanup(engine):
    """Dọn ĐÚNG issuer test này tự cắm (theo organ_code) — khuôn `test_e25_price_job._cleanup`.

    `snapshot_job.run()` tạo engine THẬT của riêng nó (đọc `ETL_DATABASE_URL`) và tự commit —
    fixture `db` (một connection, rollback cuối test) không thấy và không dọn được các lượt ghi
    đó. Vì vậy bộ test này dùng `migrated_engine` thật + dọn tay trước/sau, đúng khuôn
    `test_e20_events_job.py`/`test_e25_price_job.py`, thay vì `db` + monkeypatch `_engine`
    như bản nháp ban đầu (bản đó không thấy được issuer vừa seed — hai connection khác nhau).
    """
    with engine.begin() as c:
        iids = c.execute(sa.text(
            "SELECT issuer_id FROM market.issuer_external_id"
            " WHERE source = 'fiintrade' AND external_code = ANY(:o)"), {"o": ALL_ORGANS}).scalars().all()
        if iids:
            c.execute(sa.text("DELETE FROM market.snapshot_daily WHERE issuer_id = ANY(:i)"), {"i": iids})
            c.execute(sa.text("DELETE FROM ops.snapshot_check WHERE issuer_id = ANY(:i)"), {"i": iids})
            # Vòng sửa 4 thêm: test truyền ngân sách thời gian cho re-crawl tự seed một dòng
            # corporate_event — không dọn trước thì DELETE market.issuer bên dưới vỡ FK.
            c.execute(sa.text("DELETE FROM market.corporate_event WHERE issuer_id = ANY(:i)"), {"i": iids})
            c.execute(sa.text("DELETE FROM market.security WHERE issuer_id = ANY(:i)"), {"i": iids})
            c.execute(sa.text("DELETE FROM market.issuer_external_id WHERE issuer_id = ANY(:i)"), {"i": iids})
            c.execute(sa.text("DELETE FROM market.issuer WHERE issuer_id = ANY(:i)"), {"i": iids})
        c.execute(sa.text("DELETE FROM ops.etl_run WHERE job = :j"), {"j": ss.JOB})
        c.execute(sa.text("DELETE FROM staging.raw_payload WHERE source = 'snapshot'"))
        c.execute(sa.text("DELETE FROM ops.data_domain_state WHERE domain = :d AND source = :s"),
                  {"d": ss.DOMAIN, "s": ss.SOURCE})


def _seed(engine, organ=ORGAN, ticker=TICKER):
    with engine.begin() as c:
        iid = c.execute(sa.text("INSERT INTO market.issuer (name, com_type_code)"
                                " VALUES ('Job test', 'CT') RETURNING issuer_id")).scalar_one()
        c.execute(sa.text("INSERT INTO market.issuer_external_id (issuer_id, source, external_code)"
                          " VALUES (:i, 'fiintrade', :c)"), {"i": iid, "c": organ})
        c.execute(sa.text("INSERT INTO market.security (ticker, exchange, security_type, issuer_id)"
                          " VALUES (:t, 'HOSE', 'stock', :i)"), {"t": ticker, "i": iid})
    return iid


def _seed_batch(engine, tickers=BATCH):
    """20 mã — đủ chạm `MIN_SAMPLE` của guard để lượt hỏng toàn phần thật sự bị từ chối."""
    with engine.begin() as c:
        for i, t in enumerate(tickers):
            iid = c.execute(sa.text("INSERT INTO market.issuer (name, com_type_code)"
                                    " VALUES (:n, 'CT') RETURNING issuer_id"),
                            {"n": f"Outage {i}"}).scalar_one()
            c.execute(sa.text("INSERT INTO market.issuer_external_id (issuer_id, source, external_code)"
                              " VALUES (:i, 'fiintrade', :c)"), {"i": iid, "c": t})
            c.execute(sa.text("INSERT INTO market.security (ticker, exchange, security_type, issuer_id)"
                              " VALUES (:t, 'HOSE', 'stock', :i)"), {"t": t, "i": iid})
    return tickers


@pytest.fixture()
def snapshot_db(migrated_engine, monkeypatch):
    """Dọn TRƯỚC và SAU — teardown chạy cả khi test đỏ."""
    _wire(monkeypatch)
    _cleanup(migrated_engine)
    yield migrated_engine
    _cleanup(migrated_engine)


def test_one_run_writes_four_kinds_and_closes_the_run_row(snapshot_db):
    iid = _seed(snapshot_db)
    rc = sj.run(codes=[TICKER], get=_fake_get())
    assert rc == 0
    with snapshot_db.begin() as c:
        kinds = c.execute(sa.text("SELECT kind FROM market.snapshot_daily WHERE issuer_id = :i"
                                  " ORDER BY kind"), {"i": iid}).scalars().all()
        row = c.execute(sa.text("SELECT status, stats FROM ops.etl_run WHERE job = :j"
                                " ORDER BY run_id DESC LIMIT 1"), {"j": ss.JOB}).one()
    assert kinds == ["dividend", "ownership", "snapshot", "valuation"]
    assert row.status == "success" and row.stats["rows_written"] == 4


def test_a_second_run_on_the_same_day_writes_nothing_new(snapshot_db):
    iid = _seed(snapshot_db)
    sj.run(codes=[TICKER], get=_fake_get())
    sj.run(codes=[TICKER], get=_fake_get())
    with snapshot_db.begin() as c:
        n = c.execute(sa.text("SELECT count(*) FROM market.snapshot_daily WHERE issuer_id = :i"),
                      {"i": iid}).scalar_one()
        stats = c.execute(sa.text("SELECT stats FROM ops.etl_run WHERE job = :j"
                                  " ORDER BY run_id DESC LIMIT 1"), {"j": ss.JOB}).scalar_one()
    assert n == 4
    assert stats["rows_written"] == 0 and stats["tally"]["unchanged"] == 4


def test_a_source_wide_outage_refuses_the_run_and_writes_no_row(snapshot_db):
    tickers = _seed_batch(snapshot_db)
    failing = (FIX / "BVB-valuation-failed.json").read_text(encoding="utf-8")
    rc = sj.run(codes=tickers, kinds=["valuation"],
               get=lambda u, timeout: (200, failing), sleep=lambda s: None)
    assert rc == 1
    with snapshot_db.begin() as c:
        n = c.execute(sa.text(
            "SELECT count(*) FROM market.snapshot_daily d"
            " JOIN market.issuer_external_id x USING (issuer_id)"
            " WHERE x.source = 'fiintrade' AND x.external_code = ANY(:o)"), {"o": tickers}).scalar_one()
        row = c.execute(sa.text("SELECT status, error FROM ops.etl_run WHERE job = :j"
                                " ORDER BY run_id DESC LIMIT 1"), {"j": ss.JOB}).one()
    assert n == 0
    assert row.status == "failed" and "hỏng" in row.error


def test_a_refused_run_leaves_evidence_behind(snapshot_db):
    tickers = _seed_batch(snapshot_db)
    failing = (FIX / "BVB-valuation-failed.json").read_text(encoding="utf-8")
    sj.run(codes=tickers, kinds=["valuation"],
          get=lambda u, timeout: (200, failing), sleep=lambda s: None)
    with snapshot_db.begin() as c:
        n = c.execute(sa.text("SELECT count(*) FROM staging.raw_payload"
                              " WHERE source = 'snapshot'")).scalar_one()
    # Mọi target đều bị FiinTrade trả 'Failed' (retry, không phải 'ok') ⇒ fetched rỗng ⇒
    # KHÔNG có gì để làm bằng chứng — store_refusal_evidence phải chịu được list rỗng
    # (picked = [] ⇒ vòng for không chạy) mà không nổ, không phải chuyện nó ghi ra gì đó.
    assert n == 0


def test_the_watermark_stays_put_when_a_target_failed(snapshot_db):
    """Đẩy watermark khi còn mã hỏng là mất trigger vĩnh viễn."""
    _seed(snapshot_db)
    with snapshot_db.begin() as c:
        c.execute(sa.text("INSERT INTO ops.data_domain_state (domain, source, status, watermark)"
                          " VALUES (:d, :s, 'active', '2026-09-01')"), {"d": ss.DOMAIN, "s": ss.SOURCE})
    ok = _payload("ownership")
    bad = (FIX / "BVB-valuation-failed.json").read_text(encoding="utf-8")

    def flaky(u, timeout):
        return (200, bad) if "/Valuation/" in u else (200, ok if "/Ownership/" in u else _payload(
            "snapshot" if "/Snapshot/" in u else "dividend"))

    sj.run(codes=[TICKER], get=flaky, sleep=lambda s: None)
    with snapshot_db.connect() as c:
        assert ss.load_watermark(c) == date(2026, 9, 1)


def test_the_watermark_stays_put_when_a_target_has_a_bad_shape(snapshot_db):
    """Review vòng 1, phát hiện #1: target đi đường BadShape KHÔNG bao giờ được `apply()`
    ghi vào `snapshot_check` (guard.py raise trước khi tới snapshot_store), nhưng nếu điều
    kiện tiến watermark chỉ nhìn `failed` thì mốc vẫn trôi qua đúng ngày sự kiện của nó —
    mất trigger vĩnh viễn, cùng hậu quả với `failed`, chỉ khác đường vào (brief cảnh báo
    đường `failed`, bỏ sót đường `bad_shape`)."""
    _seed(snapshot_db)
    with snapshot_db.begin() as c:
        c.execute(sa.text("INSERT INTO ops.data_domain_state (domain, source, status, watermark)"
                          " VALUES (:d, :s, 'active', '2026-09-01')"), {"d": ss.DOMAIN, "s": ss.SOURCE})
    # JSON hợp lệ, status hợp lệ, nhưng thiếu khoá gốc của kind ⇒ bad_shape, không phải failed.
    bad_shape_payload = '{"items": [{"khac": 1}], "status": 0}'

    def get(u, timeout):
        if "/Snapshot/" in u:
            return 200, bad_shape_payload
        kind = ("ownership" if "/Ownership/" in u else
                "dividend" if "/CashDividendAnalysis/" in u else "valuation")
        return 200, _payload(kind)

    rc = sj.run(codes=[TICKER], get=get, sleep=lambda s: None)
    assert rc == 0                                # guard không từ chối (mẫu quá nhỏ, MIN_SAMPLE)
    with snapshot_db.connect() as c:
        assert ss.load_watermark(c) == date(2026, 9, 1)


def test_recrawl_passes_the_time_budget_to_price_job(snapshot_db, monkeypatch):
    """Số đo thật (kho production, đo 2026-09-22): re-crawl không trần thời gian từng kéo
    một lượt `--codes A32,BAB,BVB` vượt 120 giây, vì mỗi mã re-crawl là một lượt
    `price --backfill` TRỌN LỊCH SỬ ~12,5 năm, không phải một lần gọi nhẹ — mùa cổ tức có
    tuần tới 48 mã trong cửa sổ 3 ngày, chạm gần trần `MAX_RECRAWL`. `_recrawl` phải truyền
    đúng `max_minutes=RECRAWL_MAX_MINUTES` xuống `price_job.run`, không phải gọi trần.

    Ghi đè fake của `_wire()` (vốn chỉ `lambda **kw: 0`, không ghi lại tham số) bằng một
    fake bắt được `kw` — cùng `monkeypatch` instance nên đè hợp lệ, không cần sửa `_wire`.

    PHẢI là lượt ĐẦY ĐỦ (`codes=None`, `kinds=None`): vòng sửa 4 chặn hẳn `_recrawl` ở lượt
    con (xem `test_a_codes_run_does_not_trigger_a_price_recrawl` ngay dưới) — test này đổi từ
    `codes=[TICKER]` sang lượt đầy đủ để còn đứng được sau fix đó, đúng khuôn zero-QUOTA của
    `test_the_watermark_written_reflects_the_due_list_snapshot_not_a_later_insert` (không zero
    thì nhánh quét sàn có thể kéo issuer thật còn sót của file test khác vào lượt).
    """
    monkeypatch.setattr(ss, "QUOTA", {k: 0 for k in ss.QUOTA})
    price_calls = []
    monkeypatch.setattr("etl.price_job.run", lambda **kw: (price_calls.append(kw), 0)[1])
    iid = _seed(snapshot_db)
    with snapshot_db.begin() as c:
        # Ngày không hưởng quyền HÔM NAY — nằm trong cửa sổ mặc định 3 ngày của recrawl_codes().
        c.execute(sa.text(
            "INSERT INTO market.corporate_event (event_type, issuer_id, exright_date, payload)"
            " VALUES ('CashDividend', :i, current_date, '{}'::jsonb)"), {"i": iid})
    rc = sj.run(get=_fake_get())
    assert rc == 0
    assert price_calls == [{"backfill": True, "codes": [TICKER], "max_minutes": sj.RECRAWL_MAX_MINUTES}]


def test_a_codes_run_does_not_trigger_a_price_recrawl(snapshot_db, monkeypatch):
    """Bug thật đo 2026-09-04: ba lượt `--codes` liên tiếp (73 mã, rồi 73 mã, rồi 73 mã ×
    1 kind) đều kéo lại backfill TRỌN LỊCH SỬ ~12,5 năm cho `['RYG', 'TCH']` — hai mã KHÔNG
    nằm trong tập `codes` người dùng ép chạy. Nguyên nhân: `recrawl_codes()` quét TOÀN CỤC
    `market.corporate_event` theo cửa sổ ngày, không lọc theo tham số `codes` của lượt gọi —
    nên `_recrawl` cũ (gọi ở MỌI lượt, kể cả lượt con) luôn nhặt đúng những mã đang trong cửa
    sổ ex-right, bất kể ý định của lượt con.

    Lượt con là hành động thủ công phạm vi hẹp — cùng lý do nó không được đẩy mốc nước
    (`test_a_codes_run_does_not_touch_the_domain_watermark`), nó cũng không được châm một
    lượt backfill giá cho mã ngoài phạm vi. Seed sự kiện đúng NGAY trên mã trong `codes` (thay
    vì một mã khác) để phép thử chặt hơn: nếu `_recrawl` lỡ còn chạy, nó chắc chắn nhặt được
    mã này — sự vắng mặt của `price_calls` chỉ có thể do lượt con bị chặn, không phải tình cờ
    `recrawl_codes()` trả rỗng.
    """
    price_calls = []
    monkeypatch.setattr("etl.price_job.run", lambda **kw: (price_calls.append(kw), 0)[1])
    iid = _seed(snapshot_db)
    with snapshot_db.begin() as c:
        c.execute(sa.text(
            "INSERT INTO market.corporate_event (event_type, issuer_id, exright_date, payload)"
            " VALUES ('CashDividend', :i, current_date, '{}'::jsonb)"), {"i": iid})
    rc = sj.run(codes=[TICKER], get=_fake_get())
    assert rc == 0
    assert price_calls == []
    with snapshot_db.begin() as c:
        stats = c.execute(sa.text("SELECT stats FROM ops.etl_run WHERE job = :j"
                                  " ORDER BY run_id DESC LIMIT 1"), {"j": ss.JOB}).scalar_one()
    assert stats["recrawl"] == {"skipped": "lượt con"}


def test_a_codes_run_does_not_touch_the_domain_watermark(snapshot_db):
    """CRITICAL #1: `price_job.py` đã có tiền lệ `subset` — lượt `--codes`/`--kinds` chỉ phục
    vụ vài mã/kind thì KHÔNG được đẩy mốc nước toàn bảng, nếu không mọi sự kiện công bố của
    ~1.520 issuer còn lại nằm dưới mốc mới sẽ mất trigger vĩnh viễn."""
    _seed(snapshot_db)
    rc = sj.run(codes=[TICKER], get=_fake_get())
    assert rc == 0
    with snapshot_db.begin() as c:
        row = c.execute(sa.text("SELECT 1 FROM ops.data_domain_state"
                                " WHERE domain = :d AND source = :s"),
                        {"d": ss.DOMAIN, "s": ss.SOURCE}).first()
        stats = c.execute(sa.text("SELECT stats FROM ops.etl_run WHERE job = :j"
                                  " ORDER BY run_id DESC LIMIT 1"), {"j": ss.JOB}).scalar_one()
    assert row is None                       # lượt --codes không được ghi/đè data_domain_state
    assert stats["subset"] is True


def test_the_watermark_written_reflects_the_due_list_snapshot_not_a_later_insert(
        snapshot_db, monkeypatch):
    """CRITICAL #1 (nhánh lượt đầy đủ) + IMPORTANT #3: `run()` đọc watermark hai lần — T0 cùng
    `due_list`, T1 sau khi fetch/re-crawl xong (tới 20 phút) — tạo cửa sổ đua: sự kiện MỚI được
    chèn (giả lập `events_job` chạy song song) ngay trong lúc snapshot đang fetch bị mốc T1 nuốt
    mất, không job nào phục vụ nó. Sửa: `max(public_date)` phải lấy CÙNG giao dịch với
    `due_list` ở T0 và ghi đúng giá trị đó ở cuối lượt — bất kể chuyện gì xảy ra ở giữa.

    Zero hoá `QUOTA` để nhánh quét sàn không kéo issuer thật còn sót của file test khác vào
    lượt (đây phải là lượt ĐẦY ĐỦ — codes=None, kinds=None — mới thật sự ghi watermark theo
    fix #1). `expected_wm` tự đo NGAY TRƯỚC khi chạy job thay vì hard-code, để test không phụ
    thuộc việc `market.corporate_event` có sạch tuyệt đối hay không (§1.7 — không giả định
    trạng thái người khác để lại)."""
    monkeypatch.setattr(ss, "QUOTA", {k: 0 for k in ss.QUOTA})
    iid = _seed(snapshot_db)
    with snapshot_db.begin() as c:
        c.execute(sa.text(
            "INSERT INTO ops.data_domain_state (domain, source, status, watermark)"
            " VALUES (:d, :s, 'active', '2026-08-01')"), {"d": ss.DOMAIN, "s": ss.SOURCE})
        c.execute(sa.text(
            "INSERT INTO market.corporate_event (event_type, issuer_id, public_date, payload)"
            " VALUES ('Earning', :i, current_date, '{}'::jsonb)"), {"i": iid})
    with snapshot_db.begin() as c:
        expected_wm = c.execute(sa.text(
            "SELECT max(public_date) FROM market.corporate_event")).scalar_one()

    inserted = {"done": False}

    def get(u, timeout):
        if not inserted["done"]:
            inserted["done"] = True
            with snapshot_db.begin() as c:
                c.execute(sa.text(
                    "INSERT INTO market.corporate_event (event_type, issuer_id, public_date, payload)"
                    " VALUES ('Earning', :i, current_date + 30, '{}'::jsonb)"), {"i": iid})
        return _fake_get()(u, timeout)

    rc = sj.run(get=get, sleep=lambda s: None)
    assert rc == 0
    with snapshot_db.begin() as c:
        wm = c.execute(sa.text("SELECT watermark FROM ops.data_domain_state"
                               " WHERE domain = :d AND source = :s"),
                       {"d": ss.DOMAIN, "s": ss.SOURCE}).scalar_one()
    assert wm == expected_wm.isoformat()


def test_recrawl_is_skipped_when_the_fetch_phase_was_cut_by_max_minutes(snapshot_db, monkeypatch):
    """IMPORTANT #4: `--max-minutes` chỉ chặn pha fetch — `_recrawl` vẫn chạy tiếp tới 20 phút
    nữa kể cả khi fetch vừa bị cắt vì hết giờ, trong khi `backend/README.md` mô tả cờ này như
    trần thời gian của CẢ LƯỢT. `max_minutes=-1` đặt hạn ở quá khứ nên `stopped=True` ngay từ
    target đầu tiên — tất định, không phụ thuộc đồng hồ thật."""
    price_calls = []
    monkeypatch.setattr("etl.price_job.run", lambda **kw: (price_calls.append(kw), 0)[1])
    _seed(snapshot_db)
    rc = sj.run(codes=[TICKER], get=_fake_get(), max_minutes=-1)
    assert rc == 0
    assert price_calls == []
    with snapshot_db.begin() as c:
        stats = c.execute(sa.text("SELECT stats FROM ops.etl_run WHERE job = :j"
                                  " ORDER BY run_id DESC LIMIT 1"), {"j": ss.JOB}).scalar_one()
    assert stats["stopped_early"] is True
    assert "skipped" in stats["recrawl"]


def test_stats_survive_when_upsert_domain_state_fails_after_close_run(snapshot_db, monkeypatch):
    """MINOR #8: `omo_store.close_run` docstring chốt thứ tự — mọi job gọi
    `close_run('success', stats)` TRƯỚC rồi mới làm nốt bước sau (`upsert_domain_state`); cột
    `stats` dùng `coalesce` nên nếu bước sau ném lỗi, `etl_run` vẫn GIỮ được stats đã ghi, chỉ
    đổi `status` sang `failed`. Trước fix, `snapshot_job` gọi `upsert_domain_state` TRƯỚC
    `close_run` — lỗi ở đó làm `stats = NULL`, mất sạch bằng chứng của lượt đã ghi xong."""
    monkeypatch.setattr(ss, "QUOTA", {k: 0 for k in ss.QUOTA})
    monkeypatch.setattr(ss, "upsert_domain_state",
                        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
    iid = _seed(snapshot_db)
    with snapshot_db.begin() as c:
        c.execute(sa.text(
            "INSERT INTO ops.data_domain_state (domain, source, status, watermark)"
            " VALUES (:d, :s, 'active', '2026-08-01')"), {"d": ss.DOMAIN, "s": ss.SOURCE})
        c.execute(sa.text(
            "INSERT INTO market.corporate_event (event_type, issuer_id, public_date, payload)"
            " VALUES ('Earning', :i, current_date, '{}'::jsonb)"), {"i": iid})
    rc = sj.run(get=_fake_get(), sleep=lambda s: None)
    assert rc == 2
    with snapshot_db.begin() as c:
        row = c.execute(sa.text("SELECT status, stats, error FROM ops.etl_run WHERE job = :j"
                                " ORDER BY run_id DESC LIMIT 1"), {"j": ss.JOB}).one()
    assert row.status == "failed"
    assert "boom" in row.error
    assert row.stats["rows_written"] == 1    # bằng chứng KHÔNG mất, dù status = failed


def test_a_partial_outage_refuses_the_run_and_leaves_real_evidence(snapshot_db):
    """Review vòng 1, phát hiện #3: hai test outage toàn phần ở trên có `fetched` LUÔN RỖNG
    (payload lỗi khiến classify() không bao giờ trả 'ok') nên chỉ chứng minh
    `store_refusal_evidence` không nổ với list rỗng — không chứng minh nó GHI được dòng thật.
    Ở đây 4/20 mã thành công, 16/20 hỏng (80% > ngưỡng 20%) ⇒ guard vẫn từ chối, nhưng
    `fetched` có 4 bản ghi thật để đứng làm bằng chứng."""
    tickers = _seed_batch(snapshot_db)
    ok_organs = set(tickers[:4])
    failing = (FIX / "BVB-valuation-failed.json").read_text(encoding="utf-8")

    def get(u, timeout):
        if any(f"OrganCode={o}" in u for o in ok_organs):
            return 200, _payload("valuation")
        return 200, failing

    rc = sj.run(codes=tickers, kinds=["valuation"], get=get, sleep=lambda s: None)
    assert rc == 1
    with snapshot_db.begin() as c:
        n_daily = c.execute(sa.text(
            "SELECT count(*) FROM market.snapshot_daily d"
            " JOIN market.issuer_external_id x USING (issuer_id)"
            " WHERE x.source = 'fiintrade' AND x.external_code = ANY(:o)"), {"o": tickers}).scalar_one()
        rows = c.execute(sa.text("SELECT endpoint_key FROM staging.raw_payload"
                                 " WHERE source = 'snapshot'")).scalars().all()
    assert n_daily == 0                            # transaction dữ liệu rollback thật khi guard từ chối
    assert set(rows) == {f"snapshot:valuation:{o}" for o in ok_organs}
