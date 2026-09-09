# Plan — lát 13: scheduler trong `etl` + hoàn thiện toàn bộ kho

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Sau plan này `docker compose up -d` là cả hệ tự chạy theo bảng lịch giờ VN trong code, chết lúc nào dựng lại cũng tự bù đúng, không hai lượt cùng job chồng nhau; kho đã nạp đầy lịch sử và OMO có số dư từ ngày đầu nhờ seed FiinProX nối khít crawl SBV.

**Architecture:** Package `backend/etl/scheduler/` bốn module theo P3: `schedule.py` (dữ liệu thuần) · `planner.py` (`due()` thuần, tính lại mọi nhịp từ sổ `ops.etl_run`) · `runner.py` (spawn/giám sát tiến trình con, log theo ngày) · `loop.py` (vòng mỏng 20 s nối DB thật, đồng hồ, tín hiệu). Khoá chạy chồng là advisory lock Postgres đặt tại `omo_store.open_run` — điểm nghẽn chung 15 họ. Ba sửa nhỏ ở job sẵn có: seed OMO từ CSV, parser SBV gộp dòng cùng kỳ hạn, bỏ quota quét sàn snapshot, `classify_attempts`. Nạp đầu kho 09/09 bằng job sẵn có, chạy trước và song song với code.

**Tech Stack:** Python 3.12 · uv · SQLAlchemy 2 + psycopg 3 · Postgres 16 (advisory lock) · `subprocess` · pytest trên Postgres thật (`migrated_engine`/`db`) · Docker Compose. **Không thư viện mới.**

**Spec:** [`spec.md`](spec.md) cùng thư mục — mọi task tham chiếu mục § của spec. Phương án và tiêu chí: [`options/`](options/).

## Global Constraints

- Subagent: **Sonnet** cho task cơ học ≤ 2 file; **Opus ngay từ đầu** cho Task 6–9 (scheduler) và Task 12 (docs nhiều file). Cấm Fable/Haiku (CLAUDE.md §4.1).
- TDD: mỗi seam một test đỏ trước, literal expected, không tautological (CLAUDE.md §4.5). Không refactor trong vòng đỏ–xanh.
- Múi giờ: mọi "bây giờ" qua `core.clock.now_vn()/today_vn()`; **không** `datetime.now()`/`date.today()` trần — `tests/core/test_tz_contract.py` quét AST toàn `backend/`.
- Code không đọc `docs/` (`test_production_code_never_reads_docs`).
- Không in giá trị bí mật vào log/test/ledger. Không commit dữ liệu FiinProX (CSV nằm ngoài repo).
- Chạy test: `cd backend && uv run pytest <path> -q` với `PYTHONIOENCODING=utf-8`; **không chạy hai phiên pytest song song** (một DB test chung).
- Commit theo mốc, Conventional Commits tiếng Anh, trên nhánh `feat/etl-scheduler`, không `--no-verify`.
- Kho dev là kho thật (§4.2.1): mọi lệnh ghi kho phải idempotent, không `TRUNCATE`/`down -v`.
- Hôm nay 09/09 **không** `docker compose up -d` (sẽ dựng lại ingester đang cố ý dừng); job chạy bằng `docker compose run --name dlck-fill-<x> etl python -m etl …`.
- Mã thoát hợp đồng: 0 ghi xong · 1 chốt chặn từ chối / khoá bận · 2 lỗi thật · 130 dừng tay (`test_e63`, `test_e42`).

---

## Bản đồ file

| File | Trách nhiệm | Task |
|---|---|---|
| `backend/etl/omo_seed.py` (mới) | đọc CSV FiinProX, gộp dòng cùng kỳ hạn, ghi phiên qua `omo_store.store_seed`, rebuild flow, `--dry-run` đối chứng literal | 2 |
| `backend/etl/omo_store.py` | `store_seed()`; `open_run()` advisory lock + nhánh bận; `close_run()` nhả khoá; `close_run_refused()` | 2, 5 |
| `backend/etl/omo_parse.py` | gộp dòng cùng kỳ hạn, `OmoResult.merged` | 1 |
| `backend/etl/__main__.py` | `omo --seed/--dry-run`; nhánh không tham số → scheduler | 2, 9 |
| `backend/etl/snapshot_store.py` | bỏ `QUOTA`/`LIMIT` | 3 |
| `database/migrations/versions/0021_article_classify_attempts.py` (mới) | cột `classify_attempts` | 4 |
| `backend/etl/news_classify.py` | đếm attempts, lọc `< 3`, `stats.skipped_attempts` | 4 |
| 10 chỗ trả 1 trong `etl/*_job.py`, `series_job.py`, `news_classify.py`, `news_job.py` | gọi `close_run_refused` | 5 |
| `backend/etl/scheduler/{__init__,schedule,planner,runner,loop}.py` (mới) | P3 | 6–9 |
| `docker-compose.yml`, `deploy/backend.Dockerfile`, `.env.example`, `backend/core/env.py` | `ETL_LOG_DIR`, volume `etl_logs` | 10 |
| Test: `tests/etl/test_e66_omo_seed.py`, `test_e67_open_run_lock.py`, `test_e68_exit1_marks_refused.py`, `tests/etl/scheduler/test_sch01_planner.py`, `test_sch02_runner.py`, `test_sch03_loop.py`, `tests/schema/test_s17_classify_attempts.py`; sửa `test_e03_parse.py`, `test_e04_store_flow.py`, `test_e01_cli.py`, `test_e29`, `test_e30`, `test_e60`, `tests/docs/test_d03_compose_contract.py`; xoá `tests/test_heartbeat.py` | — |

Thứ tự thực thi: **Task 0 chạy ngay và chạy nền suốt ngày** (vận hành, không code) · Task 1–5 (job sẵn có, có thể giao Sonnet từng task) · Task 6–9 (scheduler, Opus) · Task 10 (compose) · Task 11 (nghiệm thu chạy thật) · Task 12 (tài liệu) · Task 13 (khép).

---

### Task 0: Nạp đầu 09/09 bằng job sẵn có (vận hành, chạy nền — controller tự làm)

**Files:** không sửa code. Ghi từng lượt vào `ledger.md` (cùng thư mục; tạo ở bước 1).

**Interfaces:** Produces: kho có giá 12,5 năm, BCTC toàn sàn, quốc tế, tin tháng 9; số đo phép thử tải (AC3) cho spec §5.5.

- [ ] **Step 1: Mở ledger** — tạo `docs/90-records/plans/2026-09-09-etl-scheduler-and-db-fill/ledger.md` với tiêu đề, bảng "Nạp đầu 09/09" (cột: giờ · lệnh · `run_id` · mã thoát · số đo) và chép kết quả đã có:

```
08:24–08:35  yahoo --backfill run 24 (54 lời gọi) · binance --backfill run 27 (39) · wichart run 28 (68) · fred run 29 (14) · fx run 30 (1) · lbma run 31 (2) — 6/6 success
08:24  price --backfill (run 25, container dlck-fill-price-backfill) và fundamentals --backfill (run 26, dlck-fill-fundamentals) — đang chạy, KHÔNG --stop-before-open
08:27–08:36  FiinTrade "Timeout expired" 3/4 mã đầu của backfill giá (AAA, AAH, AAM) khi BCTC chạy song song; BCTC 2.250 lời gọi 0 retry tới 08:46
```

- [ ] **Step 2: Phép thử tải trong phiên (AC3) — lượt 1 lúc ~10:00**

```bash
docker compose run -d --name dlck-fill-price-daily-1 etl python -m etl price
```

Theo dõi: `docker logs -f dlck-fill-price-daily-1 | grep -v httpx`. Khi xong ghi vào ledger: `run_id`, mã thoát, `stats.failed`/`failed_tickers`/`retries`/`elapsed_s`/`rows_changed`, và số dòng lỗi "hỏng sau" của backfill giá trong cùng khoảng giờ (`docker logs dlck-fill-price-backfill | grep -c "hỏng sau"`, so với số trước lượt). Kỳ vọng hợp đồng: mã thoát 0 hoặc 1 (guard), **không 2**.

- [ ] **Step 3: Lượt 2 lúc ~13:30**, cùng lệnh với tên `dlck-fill-price-daily-2`; ghi như trên. Kết luận AC3 theo §4.3 CLAUDE.md: *"ba luồng FiinTrade song song ở mức X lời gọi/phút: an toàn / không"* — không dò ngưỡng thêm.

- [ ] **Step 4: Seed OMO** — sau Task 2 xong (native, file ngoài repo):

```bash
cd backend
uv run python -m etl omo --seed "C:/Users/tuanb/Downloads/omo-fiinprox-20250908-20260907.csv" --dry-run
uv run python -m etl omo --seed "C:/Users/tuanb/Downloads/omo-fiinprox-20250908-20260907.csv"
```

Expected dry-run in ra: `sessions_new=248 sessions_skipped=0 rows_merged=3 outstanding_2026-09-07=250778.26 outstanding_2026-09-08=249363.44` (tỷ VND); lượt thật `rc=0`, `ops.etl_run` job `macro.omo_seed` `success`; chạy lại lần ba dry-run ⇒ `sessions_skipped=248`. Đối chứng thêm bằng psql:

```bash
docker compose exec -T postgres psql -U dulieu -d dulieu -Atc "select tenor_days, volume_vnd/1e9, participants, winners from macro.omo_auction where session_date='2026-08-14' order by 1"
```

Expected: `7|6307.47|4|4` · `35|3466.54|4|4` · `63|210.17|1|1` · `91|909.92|3|3`.

- [ ] **Step 5: Sitemap tin một tuần** (song song được, nguồn khác):

```bash
docker compose run -d --name dlck-fill-news-tnck etl python -m etl news --backfill-sitemap --source tinnhanhck --from 2026-09
docker compose run -d --name dlck-fill-news-bnews etl python -m etl news --backfill-sitemap --source bnews --from 2026-09
docker compose run -d --name dlck-fill-news-nqs etl python -m etl news --backfill-sitemap --source nguoiquansat --from 2026-09
```

Expected: mỗi lượt `success`, `stats.periods_failed = 0` hoặc ghi rõ kỳ hỏng.

- [ ] **Step 6: Snapshot ép trọn sàn** — chỉ sau khi `dlck-fill-fundamentals` xong (không ba luồng FiinTrade). Danh sách mã = niêm yết **và** có mã FiinTrade **và** chưa bị dấu vắng danh bạ (kho mới có 439 mã dấu `directory_absent_since` từ 08/09, sẽ lật `delisted` khi đủ 3 ngày):

```bash
CODES=$(docker compose exec -T postgres psql -U dulieu -d dulieu -Atc "select string_agg(s.ticker, ',' order by s.ticker) from market.security s join market.issuer_external_id x on x.issuer_id = s.issuer_id and x.source = 'fiintrade' where s.status = 'listed' and s.security_type = 'stock' and s.directory_absent_since is null")
echo "$CODES" | tr ',' '\n' | wc -l          # expected 1523
docker compose run -d --name dlck-fill-snapshot-all etl python -m etl snapshot --codes "$CODES"
```

Expected: `success`, `stats.tally` đọc bằng mắt (lượt `--codes` không guard), `ops.snapshot_check` ≈ 6.092 dòng; ghi `bad_shape`, `failed` vào ledger.

- [ ] **Step 7: Sau 15:05 — khép ngày 09/09** (tuần tự): `screener` → `price` → `events` → `snapshot` → `fundamentals` → `omo` (`omo` thêm một lượt 18:00 và 21:30 nếu SBV chưa lên bài; ngày trùng thì `skipped`). Mỗi lượt một `docker compose run --name dlck-fill-<job>-eod`. Ghi `run_id` + mã thoát.

- [ ] **Step 8: Tối — classify tồn đọng**: lặp `docker compose run --rm etl python -m etl classify --limit 1000` tới khi `stats.selected = 0` hoặc `quota_stop`. Ghi tổng bài, token, thời gian.

- [ ] **Step 9: Sáng 10/09 08:15** — bật ingester và chạy tay các mốc ngày theo bảng lịch §5.7 cho tới khi scheduler tiếp quản (Task 11 Step 3):

```bash
docker compose start ingester
docker compose logs --tail 5 ingester      # expected: "run: ngoài phiên, chờ tới 2026-09-10T08:30:00+07:00" hoặc đã "giành leader"
```

- [ ] **Step 10: Từ 12/09 — luật huỷ niêm yết sẽ bắn**: 439 mã có dấu vắng danh bạ từ 2026-09-08 16:09 VN, ngưỡng 3 ngày ⇒ lượt `refdata` đầu tiên sau 2026-09-11 16:09 từ chối (`guard refused: sắp lật delisted 439 mã — quá 1%`, exit 1). Đúng thiết kế. Sau khi chủ dự án gật, chạy tay **một lần**: `docker compose run --rm etl python -m etl refdata --accept-drop`; expected `stats.accept_drop=true`, ~439 mã sang `delisted`, lượt kế thành `success`.

---

### Task 1: Parser SBV gộp dòng cùng kỳ hạn (spec §5.2)

**Files:**
- Modify: `backend/etl/omo_parse.py:44-51` (`OmoResult` thêm `merged`), `:88-133` (vòng dòng)
- Test: `backend/tests/etl/test_e03_parse.py` (thêm 2 test cuối file)

**Interfaces:**
- Produces: `OmoResult(session_date, rows, groups_present, merged: int = 0)`; `rows` không bao giờ có hai phần tử cùng `(op_type, tenor_days)`.

- [ ] **Step 1: Test đỏ** — thêm vào `backend/tests/etl/test_e03_parse.py`:

```python
TWO_SESSIONS_HTML = """
<div class="ls01-date">Ngày 03 tháng 02 năm 2026</div>
<h4 class="ls01-subheading">KẾT QUẢ ĐẤU THẦU THỊ TRƯỜNG MỞ</h4>
<table class="ls01-table">
<tr><th>Loại hình giao dịch</th><th>Số thành viên tham gia/trúng thầu</th><th>Khối lượng trúng thầu</th><th>Lãi suất trúng thầu</th></tr>
<tr class="ls01-group"><td colspan="4">Mua kỳ hạn</td></tr>
<tr><td>- Kỳ hạn 7 ngày</td><td>3/3</td><td>4.747,77</td><td>4,5</td></tr>
<tr><td>- Kỳ hạn 7 ngày</td><td>13/13</td><td>35.983,63</td><td>4,5</td></tr>
<tr><td>- Kỳ hạn 28 ngày</td><td>4/4</td><td>5.398,65</td><td>4,5</td></tr>
<tr class="ls01-total"><td>Tổng cộng</td><td></td><td>46.130,05</td><td></td></tr>
</table>"""


def test_two_rows_same_tenor_are_merged_and_counted():
    r = parse(TWO_SESSIONS_HTML)
    seven = [x for x in r.rows if x.tenor_days == 7]
    assert len(seven) == 1
    assert seven[0].volume_vnd == Decimal("40731.40") * 10**9
    assert (seven[0].participants, seven[0].winners) == (16, 16)
    assert r.merged == 1
    assert len(r.rows) == 2


def test_two_rows_same_tenor_with_different_rate_is_a_parse_error():
    html = TWO_SESSIONS_HTML.replace("<td>13/13</td><td>35.983,63</td><td>4,5</td>", "<td>13/13</td><td>35.983,63</td><td>4,4</td>")
    with pytest.raises(ParseError, match="lãi suất"):
        parse(html)
```

(Đầu file đã import `parse`, `ParseError`, `Decimal`, `pytest` — kiểm, thiếu thì thêm.)

- [ ] **Step 2: Chạy, xác nhận đỏ**

Run: `cd backend && uv run pytest tests/etl/test_e03_parse.py -q -k merged`
Expected: 2 failed — `AssertionError` (hai dòng tenor 7) và `merged` không tồn tại.

- [ ] **Step 3: Implement** — trong `omo_parse.py`: `OmoResult` thêm trường `merged: int = 0`; thay `rows.append(OmoRow(...))` bằng:

```python
            existing = next((i for i, x in enumerate(rows) if x.op_type == current and x.tenor_days == tenor), None)
            if existing is None:
                rows.append(OmoRow(current, tenor, part, win, vol, rate))
            else:
                prev = rows[existing]
                if prev.rate_pct != rate:
                    raise ParseError(f"hai dòng cùng kỳ hạn {tenor} ngày nhóm {current} khác lãi suất: {prev.rate_pct} vs {rate}")
                rows[existing] = OmoRow(current, tenor,
                                        None if prev.participants is None or part is None else prev.participants + part,
                                        None if prev.winners is None or win is None else prev.winners + win,
                                        prev.volume_vnd + vol, rate)
                merged += 1
```

khai `merged = 0` cạnh `rows: list[OmoRow] = []`, và `return OmoResult(session_date, rows, frozenset(group_sum), merged)`. Thêm vào docstring đầu module một dòng: *"Hai dòng cùng nhóm cùng kỳ hạn = hai phiên trong ngày (đo FiinProX 03/02/2026) ⇒ gộp, đếm `merged`."*

- [ ] **Step 4: Xanh + cả file**

Run: `cd backend && uv run pytest tests/etl/test_e03_parse.py tests/etl/test_e04_store_flow.py -q`
Expected: tất cả pass (test cũ dùng `OmoResult(...)` ba đối số vẫn chạy nhờ mặc định `merged=0`).

- [ ] **Step 5: Commit** — `git commit -m "feat(omo): merge two auctions of the same tenor in one SBV session"`

---

### Task 2: Seed OMO từ CSV FiinProX (spec §5.1)

**Files:**
- Create: `backend/etl/omo_seed.py`
- Modify: `backend/etl/omo_store.py` (thêm `store_seed`; `store()` ghi `note` khi `result.merged`), `backend/etl/__main__.py:21-23`
- Test: `backend/tests/etl/test_e66_omo_seed.py` (mới), `backend/tests/etl/fixtures/omo/seed_sample.csv` (mới), `backend/tests/etl/test_e01_cli.py`

**Interfaces:**
- `omo_seed.read_csv(path) -> list[SeedRow]` với `SeedRow(session_date: date, tenor_days: int, participants: int | None, winners: int | None, volume_vnd: Decimal, rate_pct: Decimal | None)`.
- `omo_seed.to_results(rows) -> list[OmoResult]` — gộp theo `(date, tenor)`, mọi dòng `reverse_repo`, sắp theo ngày tăng dần.
- `omo_store.store_seed(result, conn, *, crawled_at: datetime, note: str) -> dict` — `{"skipped": True}` nếu ngày đã có; ngược lại `{"sessions": 1, "auctions": n}`; KHÔNG ghi `staging.raw_payload`.
- `omo_seed.run(path: str, dry_run: bool = False, checks: tuple[date, ...] = (date(2026, 9, 7), date(2026, 9, 8))) -> int` — job `macro.omo_seed`.
- CLI: `python -m etl omo [--seed PATH] [--dry-run]`; `--dry-run` chỉ đi với `--seed`.

- [ ] **Step 1: Fixture CSV** `backend/tests/etl/fixtures/omo/seed_sample.csv` (8 dòng thật từ file FiinProX, một dòng khối lượng 0):

```csv
session_date,tenor_days,participants,winners,volume_bn,rate
2026-08-14,7,4,4,6307.47,0.045
2026-08-14,35,4,4,3466.54,0.045
2026-08-14,63,1,1,210.17,0.045
2026-08-14,91,3,3,909.92,0.045
2026-02-03,7,3,3,4747.77,0.045
2026-02-03,7,13,13,35983.63,0.045
2026-02-03,28,4,4,5398.65,0.045
2026-07-17,7,0,0,0,0
```

- [ ] **Step 2: Test đỏ** `backend/tests/etl/test_e66_omo_seed.py`:

```python
"""Seed OMO từ CSV FiinProX (spec lát 13 §5.1): gộp dòng cùng kỳ hạn, ghi qua store_seed, idempotent, flow tính đúng."""
import os
import pathlib
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
import sqlalchemy as sa

from etl import omo_seed
from etl.omo_flow import rebuild
from etl.omo_store import store_seed

CSV = pathlib.Path(__file__).parent / "fixtures" / "omo" / "seed_sample.csv"


def test_read_csv_converts_units_and_keeps_zero_rows():
    rows = omo_seed.read_csv(CSV)
    assert len(rows) == 8
    r = rows[0]
    assert (r.session_date, r.tenor_days, r.participants, r.winners) == (date(2026, 8, 14), 7, 4, 4)
    assert r.volume_vnd == Decimal("6307470000000")
    assert r.rate_pct == Decimal("4.5")
    assert rows[-1].volume_vnd == 0 and rows[-1].rate_pct == 0


def test_to_results_merges_same_tenor_and_orders_by_date():
    results = omo_seed.to_results(omo_seed.read_csv(CSV))
    assert [x.session_date for x in results] == [date(2026, 2, 3), date(2026, 7, 17), date(2026, 8, 14)]
    feb = results[0]
    assert feb.merged == 1 and len(feb.rows) == 2
    seven = next(x for x in feb.rows if x.tenor_days == 7)
    assert seven.volume_vnd == Decimal("40731.40") * 10**9 and (seven.participants, seven.winners) == (16, 16)
    assert all(x.op_type == "reverse_repo" for r in results for x in r.rows)


def test_read_csv_rejects_unknown_columns(tmp_path):
    bad = tmp_path / "x.csv"
    bad.write_text("session_date,tenor_days,op_type,volume_bn,rate\n2026-01-05,7,repo,1,0.04\n", encoding="utf-8")
    with pytest.raises(ValueError, match="cột"):
        omo_seed.read_csv(bad)


def test_read_csv_rejects_same_tenor_different_rate(tmp_path):
    bad = tmp_path / "x.csv"
    bad.write_text("session_date,tenor_days,participants,winners,volume_bn,rate\n"
                   "2026-01-05,7,1,1,10,0.04\n2026-01-05,7,1,1,10,0.045\n", encoding="utf-8")
    with pytest.raises(ValueError, match="lãi suất"):
        omo_seed.to_results(omo_seed.read_csv(bad))


def test_store_seed_writes_session_with_note_and_is_idempotent(db):
    feb = omo_seed.to_results(omo_seed.read_csv(CSV))[0]
    st = store_seed(feb, db, crawled_at=datetime(2026, 9, 8, 3, 52, tzinfo=timezone.utc), note="seed FiinProX export 2026-09-08")
    assert st == {"sessions": 1, "auctions": 2}
    s = db.execute(sa.text("SELECT note, has_reverse_repo, has_repo, has_outright_sale, crawled_at FROM macro.omo_session WHERE session_date = '2026-02-03'")).one()
    assert s.note == "seed FiinProX export 2026-09-08 · gộp 1 dòng cùng kỳ hạn"
    assert (s.has_reverse_repo, s.has_repo, s.has_outright_sale) == (True, False, False)
    assert s.crawled_at == datetime(2026, 9, 8, 3, 52, tzinfo=timezone.utc)
    assert db.execute(sa.text("SELECT count(*) FROM staging.raw_payload WHERE source = 'sbv'")).scalar_one() == 0
    assert store_seed(feb, db, crawled_at=datetime(2026, 9, 8, 3, 52, tzinfo=timezone.utc), note="x") == {"skipped": True}


def test_flow_after_seed_hand_solved(db):
    for r in omo_seed.to_results(omo_seed.read_csv(CSV)):
        store_seed(r, db, crawled_at=datetime(2026, 9, 8, 3, 52, tzinfo=timezone.utc), note="seed")
    rebuild(db)
    inj = db.execute(sa.text("SELECT injection_vnd FROM macro.omo_flow WHERE flow_date = '2026-08-14'")).scalar_one()
    mat = db.execute(sa.text("SELECT maturing_vnd FROM macro.omo_flow WHERE flow_date = '2026-08-21'")).scalar_one()
    assert inj == Decimal("10894.10") * 10**9          # 6307.47 + 3466.54 + 210.17 + 909.92
    assert mat == Decimal("6307.47") * 10**9           # kỳ hạn 7 của 14/08 đáo hạn 21/08


def test_run_dry_run_reports_and_writes_nothing(migrated_engine, monkeypatch, capsys):
    monkeypatch.setenv("ETL_DATABASE_URL", os.environ["TEST_DATABASE_URL"])
    monkeypatch.setattr("etl.omo_seed.load_dotenv", lambda *a, **k: None)
    with migrated_engine.begin() as c:
        c.execute(sa.text("DELETE FROM macro.omo_auction WHERE session_date IN ('2026-02-03','2026-07-17','2026-08-14')"))
        c.execute(sa.text("DELETE FROM macro.omo_session WHERE session_date IN ('2026-02-03','2026-07-17','2026-08-14')"))
    rc = omo_seed.run(str(CSV), dry_run=True, checks=(date(2026, 8, 14), date(2026, 8, 21)))
    out = capsys.readouterr().out
    assert rc == 0
    assert "sessions_new=3" in out and "rows_merged=1" in out
    assert "outstanding_2026-08-14=10894.10" in out
    with migrated_engine.connect() as c:
        assert c.execute(sa.text("SELECT count(*) FROM macro.omo_session WHERE session_date = '2026-08-14'")).scalar_one() == 0
        assert c.execute(sa.text("SELECT count(*) FROM ops.etl_run WHERE job = 'macro.omo_seed'")).scalar_one() == 0


def test_run_real_writes_and_second_run_skips(migrated_engine, monkeypatch):
    monkeypatch.setenv("ETL_DATABASE_URL", os.environ["TEST_DATABASE_URL"])
    monkeypatch.setattr("etl.omo_seed.load_dotenv", lambda *a, **k: None)
    with migrated_engine.begin() as c:
        c.execute(sa.text("DELETE FROM macro.omo_auction WHERE session_date IN ('2026-02-03','2026-07-17','2026-08-14')"))
        c.execute(sa.text("DELETE FROM macro.omo_session WHERE session_date IN ('2026-02-03','2026-07-17','2026-08-14')"))
    try:
        assert omo_seed.run(str(CSV), checks=(date(2026, 8, 14),)) == 0
        with migrated_engine.connect() as c:
            row = c.execute(sa.text("SELECT status, stats FROM ops.etl_run WHERE job = 'macro.omo_seed' ORDER BY run_id DESC LIMIT 1")).one()
            assert row.status == "success" and row.stats["sessions_new"] == 3 and row.stats["rows_merged"] == 1
            assert row.stats["min_session_date"] == "2026-02-03" and row.stats["max_session_date"] == "2026-08-14"
        assert omo_seed.run(str(CSV), checks=(date(2026, 8, 14),)) == 0
        with migrated_engine.connect() as c:
            row = c.execute(sa.text("SELECT stats FROM ops.etl_run WHERE job = 'macro.omo_seed' ORDER BY run_id DESC LIMIT 1")).one()
            assert row.stats["sessions_new"] == 0 and row.stats["sessions_skipped"] == 3
    finally:
        with migrated_engine.begin() as c:
            c.execute(sa.text("DELETE FROM macro.omo_auction WHERE session_date IN ('2026-02-03','2026-07-17','2026-08-14')"))
            c.execute(sa.text("DELETE FROM macro.omo_session WHERE session_date IN ('2026-02-03','2026-07-17','2026-08-14')"))
            c.execute(sa.text("DELETE FROM ops.etl_run WHERE job = 'macro.omo_seed'"))
```

Thêm vào `test_e01_cli.py`:

```python
def test_omo_seed_flag_dispatches_to_seed_job(monkeypatch):
    import etl.omo_seed
    seen = {}
    monkeypatch.setattr(etl.omo_seed, "run", lambda path, dry_run=False, **kw: seen.update(path=path, dry_run=dry_run) or 0)
    assert main(["omo", "--seed", "x.csv", "--dry-run"]) == 0 and seen == {"path": "x.csv", "dry_run": True}
    with pytest.raises(SystemExit):
        main(["omo", "--dry-run"])          # --dry-run chỉ đi với --seed
```

- [ ] **Step 3: Đỏ** — `cd backend && uv run pytest tests/etl/test_e66_omo_seed.py tests/etl/test_e01_cli.py -q` → `ImportError: cannot import name 'store_seed'` / `No module named 'etl.omo_seed'`.

- [ ] **Step 4: Implement `omo_store.store_seed`** (thêm sau `store()`), và `store()` ghi `note` khi `result.merged`:

```python
def _session_note(base: str | None, merged: int) -> str | None:
    tail = f"gộp {merged} dòng cùng kỳ hạn" if merged else None
    return " · ".join(x for x in (base, tail) if x) or None


def store_seed(result: OmoResult, conn, *, crawled_at, note: str) -> dict:
    """Ghi một phiên từ nguồn ngoài (FiinProX) — cùng khoá PK/ON CONFLICT như `store`, KHÔNG ghi raw_payload."""
    won = conn.execute(
        sa.text("INSERT INTO macro.omo_session (session_date, crawled_at, has_reverse_repo, has_repo, has_outright_sale, note)"
                " VALUES (:d, :c, :r, :p, :o, :n) ON CONFLICT (session_date) DO NOTHING RETURNING session_date"),
        {"d": result.session_date, "c": crawled_at, "r": "reverse_repo" in result.groups_present,
         "p": "repo" in result.groups_present, "o": "outright_sale" in result.groups_present,
         "n": _session_note(note, result.merged)}).first()
    if won is None:
        return {"skipped": True}
    for row in result.rows:
        conn.execute(
            sa.text("INSERT INTO macro.omo_auction (session_date, op_type, tenor_days, participants, winners, volume_vnd, rate_pct)"
                    " VALUES (:d, :op, :t, :p, :w, :v, :r)"),
            {"d": result.session_date, "op": row.op_type, "t": row.tenor_days, "p": row.participants, "w": row.winners,
             "v": row.volume_vnd, "r": row.rate_pct})
    return {"sessions": 1, "auctions": len(result.rows)}
```

Trong `store()` đổi câu INSERT session thêm cột `note` với giá trị `_session_note(None, result.merged)`.

- [ ] **Step 5: Implement `backend/etl/omo_seed.py`**:

```python
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
            with engine.connect() as conn:
                tx = conn.begin()
                st = _seed(conn, results)
                st.update(_outstanding(conn, checks))
                tx.rollback()
            print(" ".join(f"{k}={v}" for k, v in st.items()), flush=True)
            return 0
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
```

- [ ] **Step 6: CLI** — trong `__main__.py` thay nhánh `omo`:

```python
    if args[0] == "omo":
        parser = argparse.ArgumentParser(prog="etl omo")
        parser.add_argument("--seed", metavar="CSV", help="nạp lịch sử từ CSV FiinProX (spec lát 13 §5.1)")
        parser.add_argument("--dry-run", action="store_true", dest="dry_run")
        parsed = parser.parse_args(args[1:])
        if parsed.dry_run and not parsed.seed:
            parser.error("--dry-run chỉ đi với --seed")
        if parsed.seed:
            import etl.omo_seed
            return etl.omo_seed.run(parsed.seed, dry_run=parsed.dry_run)
        import etl.omo_job
        return etl.omo_job.run()
```

- [ ] **Step 7: Xanh** — `cd backend && uv run pytest tests/etl/test_e66_omo_seed.py tests/etl/test_e01_cli.py tests/etl/test_e04_store_flow.py tests/etl/test_e42_interrupt_closes_run.py -q` → pass.

- [ ] **Step 8: Script chuyển xlsx → CSV (dùng một lần, ngoài repo, lệnh ghi ledger)** — chạy bằng Python hệ thống có `openpyxl`:

```python
# scratchpad/omo_xlsx_to_csv.py — KHÔNG commit
import csv, datetime, openpyxl
SRC = r"C:\Users\tuanb\Downloads\FiinProX_Nghiep vu thi truong mo_20250907_20260907_20260908 (1).xlsx"
DST = r"C:\Users\tuanb\Downloads\omo-fiinprox-20250908-20260907.csv"
ws = openpyxl.load_workbook(SRC, data_only=True, read_only=True).worksheets[0]
n = 0
with open(DST, "w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh); w.writerow(["session_date","tenor_days","participants","winners","volume_bn","rate"])
    for r in ws.iter_rows(values_only=True):
        if isinstance(r[0], datetime.datetime):
            w.writerow([r[0].date().isoformat(), int(r[5].split()[0]), int(r[1]), int(r[2]), r[3] or 0, r[4]]); n += 1
print("rows", n)   # expected 826
```

- [ ] **Step 9: Commit** — `git commit -m "feat(omo): seed a year of auctions from a FiinProX CSV, dry-run checks outstanding literals"`

---

### Task 3: Bỏ quota quét sàn snapshot (spec §5.3)

**Files:**
- Modify: `backend/etl/snapshot_store.py:31` (xoá `QUOTA`), `:78-88` (chữ ký), `:145-154` (SQL)
- Test: `backend/tests/etl/test_e29_snapshot_store.py:113-119, 201-210`; `backend/tests/etl/test_e30_snapshot_job.py:233, 308`

**Interfaces:** `plan_due(conn, watermark, kinds=None, codes=None, cadence=None, max_trigger=None)`, `due_list(...)` cùng chữ ký — không còn `quota`.

- [ ] **Step 1: Sửa test e29 thành đỏ** — đổi hai test:

```python
def test_due_list_returns_every_overdue_pair_oldest_first(db):
    """Lát 13: bỏ quota — tới nhịp thì quét TRỌN (chủ dự án 2026-09-09), thứ tự vẫn cũ nhất trước."""
    _quiet_universe(db)
    ids = [_issuer(db, f"Ma {i}", f"ZZQ{i}", f"ZQ{i}") for i in range(5)]
    for n, iid in enumerate(ids):
        _checked(db, iid, "ownership", days_ago=40 + n)     # ZZQ4 cũ nhất
    due = ss.due_list(db, date(1900, 1, 1), kinds=["ownership"])
    assert [t.organ_code for t in due] == ["ZZQ4", "ZZQ3", "ZZQ2", "ZZQ1", "ZZQ0"]
```

và

```python
def test_due_list_floor_returns_all_never_checked_issuers_on_cold_start(db):
    """Lát 13: cold start không còn bị cắt — lượt đầu quét trọn những gì chưa kiểm (NULLS FIRST giữ nguyên)."""
    _quiet_universe(db)
    tickers = [f"ZC{i}" for i in range(5)]
    for i, t in enumerate(tickers):
        _issuer(db, f"Cold start floor {i}", f"ZZCS{i}", t)
    due = ss.due_list(db, date(1900, 1, 1), kinds=["ownership"])
    assert [t.ticker for t in due] == tickers
```

Trong `test_e30_snapshot_job.py` hai dòng `monkeypatch.setattr(ss, "QUOTA", {k: 0 for k in ss.QUOTA})` (dòng 233 và 308) thay bằng `_quiet_floor(snapshot_db)` với helper thêm đầu file (bản committed của `_quiet_universe` e29):

```python
def _quiet_floor(engine):
    """Lát 13 bỏ QUOTA: dập nền quét sàn bằng cách coi mọi issuer đang có là vừa kiểm xong (khuôn e29 `_quiet_universe`, ở đây commit thật)."""
    with engine.begin() as c:
        for kind in ss.CADENCE_DAYS:
            c.execute(sa.text(
                "INSERT INTO ops.snapshot_check (issuer_id, kind, checked_at, keep_hash, found_by)"
                " SELECT i.issuer_id, :k, clock_timestamp(), 'nen', 'floor' FROM market.issuer i"
                " ON CONFLICT (issuer_id, kind) DO UPDATE SET checked_at = clock_timestamp()"), {"k": kind})
```

(`_quiet_floor` gọi TRƯỚC `_seed(snapshot_db)` của hai test đó để issuer của chính test vẫn chưa có dòng sổ kiểm.)

- [ ] **Step 2: Đỏ** — `uv run pytest tests/etl/test_e29_snapshot_store.py tests/etl/test_e30_snapshot_job.py -q` → hai test e29 đỏ (chỉ trả 2/3), e30 lỗi `ss.QUOTA` còn tồn tại không đỏ — chấp nhận, đỏ ở bước sau khi xoá hằng.

- [ ] **Step 3: Implement** — xoá dòng `QUOTA = {...}`; bỏ tham số `quota` ở `due_list`/`plan_due` và dòng `quota = quota or QUOTA`; SQL nhánh quét sàn bỏ `LIMIT :quota` và tham số `"quota"`; comment ở dòng 103-107 (`Quét sàn (nhánh B) đã tự phủ trọn sàn trong 30/90 ngày`) đổi thành *"Quét sàn (nhánh B) phủ trọn sàn ngay ở lượt tới hạn (lát 13 bỏ quota — chủ dự án 2026-09-09)"*.

- [ ] **Step 4: Xanh** — `uv run pytest tests/etl/test_e29_snapshot_store.py tests/etl/test_e30_snapshot_job.py tests/etl/test_e28_snapshot_guard.py -q` → pass; `git grep -n "QUOTA" backend/etl/snapshot_store.py` → 0.

- [ ] **Step 5: Commit** — `git commit -m "feat(snapshot): floor scan covers every overdue pair when its cadence is due (quota removed)"`

---

### Task 4: `classify_attempts` — migration 0021 + job (spec §5.4)

**Files:**
- Create: `database/migrations/versions/0021_article_classify_attempts.py`, `backend/tests/schema/test_s17_classify_attempts.py`
- Modify: `backend/etl/news_classify.py:105-112` (`_SELECT`), `:227` (`_empty_stats`), `:272-288` (nhánh lỗi), `:246-248` (chữ ký `classify_run`), `:333-336` (đếm bỏ qua)
- Test: `backend/tests/etl/test_e60_classify_job.py` (thêm 1 test)

**Interfaces:** `news_classify.MAX_ATTEMPTS = 3`; `select_articles(...)` chỉ trả bài `classify_attempts < MAX_ATTEMPTS`; `count_skipped_attempts(conn) -> int`; `classify_run(..., skipped_attempts: int = 0)` ghi `st["skipped_attempts"]`.

- [ ] **Step 1: Test schema đỏ** `backend/tests/schema/test_s17_classify_attempts.py`:

```python
"""Migration 0021: news.article.classify_attempts smallint NOT NULL DEFAULT 0 — đếm số lần model trả lỗi (lát 13 §5.4)."""
import sqlalchemy as sa


def test_classify_attempts_defaults_to_zero_and_counts_up(db):
    a = db.execute(sa.text("INSERT INTO news.article (canonical_url, primary_source, fetched_at) VALUES ('https://zz.test/s17-1', 'cafef', now()) RETURNING article_id")).scalar_one()
    assert db.execute(sa.text("SELECT classify_attempts FROM news.article WHERE article_id = :a"), {"a": a}).scalar_one() == 0
    db.execute(sa.text("UPDATE news.article SET classify_attempts = classify_attempts + 1 WHERE article_id = :a"), {"a": a})
    assert db.execute(sa.text("SELECT classify_attempts FROM news.article WHERE article_id = :a"), {"a": a}).scalar_one() == 1
    col = db.execute(sa.text("SELECT data_type, is_nullable FROM information_schema.columns WHERE table_schema = 'news' AND table_name = 'article' AND column_name = 'classify_attempts'")).one()
    assert tuple(col) == ("smallint", "NO")
```

- [ ] **Step 2: Đỏ** — `uv run pytest tests/schema/test_s17_classify_attempts.py -q` → `UndefinedColumn`.

- [ ] **Step 3: Migration** `database/migrations/versions/0021_article_classify_attempts.py`:

```python
"""Đếm số lần lưới phân loại thất bại trên một bài (lát 13 §5.4, chủ dự án 2026-09-09).

Trước: bài lỗi giữ `classified_from NULL` nên được chọn lại mãi, và không phân biệt được với bài chưa thử —
lỗi chỉ nằm ở `ops.llm_call`. Nay job tăng `classify_attempts` mỗi lần model trả lỗi và bỏ qua bài đã thử
đủ `MAX_ATTEMPTS = 3` (hằng trong `etl/news_classify.py`, không CHECK ở DB để đổi ngưỡng không cần migration).

Revision ID: 0021
Revises: 0020
Create Date: 2026-09-09
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0021"
down_revision: Union[str, None] = "0020"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE news.article ADD COLUMN classify_attempts smallint NOT NULL DEFAULT 0;")


def downgrade() -> None:
    op.execute("ALTER TABLE news.article DROP COLUMN classify_attempts;")
```

- [ ] **Step 4: Xanh schema** — `uv run pytest tests/schema/test_s17_classify_attempts.py -q` → pass (conftest migrate `head`).

- [ ] **Step 5: Test job đỏ** — thêm vào `test_e60_classify_job.py`:

```python
def test_failed_article_counts_an_attempt_and_is_skipped_after_three(seeded):
    engine, ids = seeded
    fake = FakeClient([SCHEMA_ERR, R1, R1, R1])
    assert nc.run(limit=4, client=fake) == 0
    assert _n(engine, "SELECT classify_attempts FROM news.article WHERE article_id = :a", a=ids[0]) == 1
    with engine.begin() as c:
        c.execute(sa.text("UPDATE news.article SET classify_attempts = 3 WHERE article_id = :a"), {"a": ids[0]})
    with engine.connect() as c:
        assert ids[0] not in [r.article_id for r in nc.select_articles(c, limit=10)]
        assert nc.count_skipped_attempts(c) == 1
    fake2 = FakeClient([R1])
    assert nc.run(limit=10, client=fake2) == 0
    st = json.loads(_n(engine, "SELECT stats::text FROM ops.etl_run WHERE job = 'news.classify' ORDER BY run_id DESC LIMIT 1"))
    assert st["skipped_attempts"] == 1 and st["selected"] == 1          # chỉ còn ids[4]; ids[0] bị bỏ qua
```

(`SCHEMA_ERR`, `R1`, `FakeClient`, `_n` đã có trong file; kiểm `R1` là `Structured` hợp lệ cho nhóm bất kỳ.)

- [ ] **Step 6: Đỏ** — `uv run pytest tests/etl/test_e60_classify_job.py -q -k attempts` → `AttributeError: count_skipped_attempts` / attempts == 0.

- [ ] **Step 7: Implement** trong `news_classify.py`:
  - hằng `MAX_ATTEMPTS = 3` cạnh `QUOTA_EVERY`;
  - `_SELECT`: `WHERE a.classified_from IS NULL AND a.classify_attempts < :max_attempts AND {bucket}`; mọi `conn.execute(sa.text(_SELECT...), {...})` thêm `"max_attempts": MAX_ATTEMPTS`;
  - hàm mới:

```python
def count_skipped_attempts(conn) -> int:
    return conn.execute(sa.text("SELECT count(*) FROM news.article WHERE classified_from IS NULL AND classify_attempts >= :m"),
                        {"m": MAX_ATTEMPTS}).scalar_one()
```

  - `_empty_stats` thêm `"skipped_attempts": 0`; `classify_run(..., skipped_attempts: int = 0)` đặt `st["skipped_attempts"] = skipped_attempts` ngay sau `_empty_stats`;
  - nhánh `except LLMError as e:` (không dry_run) trong cùng `engine.begin() as c` sau `log_call(...)`: `c.execute(sa.text("UPDATE news.article SET classify_attempts = classify_attempts + 1 WHERE article_id = :a"), {"a": row.article_id})`;
  - trong `run()`: sau `rows = select_articles(...)` thêm `skipped = count_skipped_attempts(c)`; truyền `skipped_attempts=skipped` vào `kw`.

- [ ] **Step 8: Xanh** — `uv run pytest tests/etl/test_e60_classify_job.py tests/etl/test_e59_news_classify.py tests/etl/test_e61_classify_cli.py tests/schema -q` → pass.

- [ ] **Step 9: Commit** — `git commit -m "feat(classify): count failed attempts per article (migration 0021) and skip after three"`

---

### Task 5: Advisory lock trong `open_run` + `close_run_refused` cho mọi nhánh trả 1 (spec §5.8–5.9)

**Files:**
- Modify: `backend/etl/omo_store.py:58-87`; 10 nhánh trả 1: `refdata_job.py:53`, `screener_job.py:49`, `events_job.py:48-49`, `price_job.py:141-142`, `snapshot_job.py:138-139`, `fundamentals_job.py:104`, `wichart_job.py:126`, `series_job.py:143`, `news_classify.py:378`, `news_job.py:431`
- Test: `backend/tests/etl/test_e67_open_run_lock.py` (mới), `backend/tests/etl/test_e68_exit1_marks_refused.py` (mới)

**Interfaces:**
- `omo_store.open_run(engine, job) -> int`: giữ advisory lock `hashtext(job)` trên một connection AUTOCOMMIT riêng cho tới `close_run`; bận ⇒ ghi dòng `failed` (`error='lock busy: lượt khác đang chạy'`, `stats={"lock_busy": true, "guard_refused": true}`) rồi `raise SystemExit(1)`.
- `omo_store.close_run(engine, run_id, status, stats=None, error=None)`: như cũ + `pg_advisory_unlock` và đóng connection giữ khoá.
- `omo_store.close_run_refused(engine, run_id, error: str, stats: dict | None = None) -> None`: đặt `stats["guard_refused"] = True` (tạo dict nếu None) rồi `close_run(..., "failed", stats, error=error)`.
- Hợp đồng tĩnh: mọi `return 1` trong `backend/etl/*.py` (trừ `scheduler/`) phải có `close_run_refused(` trong ≤ 8 dòng phía trên, trừ dạng `return 0 if verdict.ok else 1` (dry-run).

- [ ] **Step 1: Test lock đỏ** `backend/tests/etl/test_e67_open_run_lock.py`:

```python
"""Advisory lock Postgres ở open_run — lớp trong của chặn chạy chồng (spec lát 13 §5.9)."""
import pytest
import sqlalchemy as sa

from etl import omo_store

JOB = "zz.lock.test"


def _hold(engine):
    conn = engine.connect().execution_options(isolation_level="AUTOCOMMIT")
    assert conn.execute(sa.text("SELECT pg_try_advisory_lock(hashtext(:j))"), {"j": JOB}).scalar_one() is True
    return conn


def _release(conn):
    conn.execute(sa.text("SELECT pg_advisory_unlock(hashtext(:j))"), {"j": JOB})
    conn.close()


def _rows(engine):
    with engine.connect() as c:
        return c.execute(sa.text("SELECT run_id, status, error, stats FROM ops.etl_run WHERE job = :j ORDER BY run_id"), {"j": JOB}).all()


@pytest.fixture()
def clean(migrated_engine):
    yield migrated_engine
    with migrated_engine.begin() as c:
        c.execute(sa.text("DELETE FROM ops.etl_run WHERE job = :j"), {"j": JOB})


def test_busy_lock_writes_a_refused_row_and_exits_1(clean):
    holder = _hold(clean)
    try:
        with pytest.raises(SystemExit) as e:
            omo_store.open_run(clean, JOB)
        assert e.value.code == 1
        rows = _rows(clean)
        assert len(rows) == 1 and rows[0].status == "failed"
        assert rows[0].error == "lock busy: lượt khác đang chạy"
        assert rows[0].stats == {"lock_busy": True, "guard_refused": True}
    finally:
        _release(holder)


def test_open_run_holds_the_lock_until_close_run(clean):
    rid = omo_store.open_run(clean, JOB)
    probe = clean.connect().execution_options(isolation_level="AUTOCOMMIT")
    try:
        assert probe.execute(sa.text("SELECT pg_try_advisory_lock(hashtext(:j))"), {"j": JOB}).scalar_one() is False
        omo_store.close_run(clean, rid, "success", {"x": 1})
        assert probe.execute(sa.text("SELECT pg_try_advisory_lock(hashtext(:j))"), {"j": JOB}).scalar_one() is True
        probe.execute(sa.text("SELECT pg_advisory_unlock(hashtext(:j))"), {"j": JOB})
    finally:
        probe.close()
    rows = _rows(clean)
    assert [r.status for r in rows] == ["success"] and rows[0].stats == {"x": 1}


def test_close_run_refused_flags_stats(clean):
    rid = omo_store.open_run(clean, JOB)
    omo_store.close_run_refused(clean, rid, "guard refused: thử", {"calls": 3})
    rows = _rows(clean)
    assert rows[0].status == "failed" and rows[0].error == "guard refused: thử"
    assert rows[0].stats == {"calls": 3, "guard_refused": True}
    rid2 = omo_store.open_run(clean, JOB)               # khoá đã nhả
    omo_store.close_run_refused(clean, rid2, "model down")
    assert _rows(clean)[1].stats == {"guard_refused": True}
```

- [ ] **Step 2: Test hợp đồng tĩnh đỏ** `backend/tests/etl/test_e68_exit1_marks_refused.py`:

```python
"""Mọi nhánh trả 1 (chốt chặn từ chối / nguồn chết) phải đóng sổ bằng `close_run_refused` để planner lát 13 đọc
`stats.guard_refused` mà không so chuỗi `error` (spec §5.8). Quét tĩnh, cùng tinh thần test_e65 vế 2."""
import re
from pathlib import Path

ETL = Path(__file__).resolve().parents[2] / "etl"
RETURN_1 = re.compile(r"^\s+return 1\s*(#.*)?$")
DRY_RUN_FORM = re.compile(r"return 0 if .* else 1")


def _violations():
    out = []
    for py in sorted(ETL.glob("*.py")):
        lines = py.read_text(encoding="utf-8").splitlines()
        for i, line in enumerate(lines):
            if RETURN_1.match(line) and not DRY_RUN_FORM.search(line):
                window = "\n".join(lines[max(0, i - 8):i])
                if "close_run_refused(" not in window:
                    out.append(f"{py.name}:{i + 1}")
    return out


def test_every_exit_1_closes_the_run_as_refused():
    assert _violations() == [], "nhánh trả 1 không đi qua close_run_refused: " + ", ".join(_violations())


def test_scanner_sees_the_known_exit_1_sites():
    names = {v.split(":")[0] for v in _violations()} | {p.name for p in ETL.glob("*_job.py")}
    assert {"refdata_job.py", "price_job.py", "series_job.py"} <= names      # đối chứng dương: quét đúng thư mục
```

- [ ] **Step 3: Đỏ** — `uv run pytest tests/etl/test_e67_open_run_lock.py tests/etl/test_e68_exit1_marks_refused.py -q` → e67 `AttributeError`/`DID NOT RAISE`, e68 liệt ≥ 10 vi phạm.

- [ ] **Step 4: Implement `omo_store`**:

```python
_LOCK_CONNS: dict[int, tuple[sa.Connection, str]] = {}   # run_id -> (connection AUTOCOMMIT giữ advisory lock suốt đời lượt, job)
LOCK_BUSY_ERROR = "lock busy: lượt khác đang chạy"


def open_run(engine, job: str) -> int:
    """Mở sổ + giành khoá theo tên job (spec lát 13 §5.9). Khoá session-level trên connection riêng AUTOCOMMIT:
    sống tới `close_run`, tự nhả khi tiến trình chết (Postgres nhả theo phiên). Bận ⇒ ghi một dòng `failed`
    mang `guard_refused` (planner không bù lại mốc đó trong ngày) rồi SystemExit(1) — ném TRƯỚC `try` của mọi
    job nên không sửa file job nào; exit 1 đúng hợp đồng "dữ liệu lành, không cần người"."""
    lock = engine.connect().execution_options(isolation_level="AUTOCOMMIT")
    got = lock.execute(sa.text("SELECT pg_try_advisory_lock(hashtext(:j))"), {"j": job}).scalar_one()
    if not got:
        lock.execute(sa.text("INSERT INTO ops.etl_run (job, status, finished_at, error, stats)"
                             " VALUES (:j, 'failed', now(), :e, cast(:s AS jsonb))"),
                     {"j": job, "e": LOCK_BUSY_ERROR, "s": json.dumps({"lock_busy": True, "guard_refused": True})})
        lock.close()
        print(f"{job}: {LOCK_BUSY_ERROR} — bỏ lượt này", file=sys.stderr, flush=True)
        raise SystemExit(1)
    rid = lock.execute(sa.text("INSERT INTO ops.etl_run (job) VALUES (:j) RETURNING run_id"), {"j": job}).scalar_one()
    _LOCK_CONNS[rid] = (lock, job)
    return rid


def close_run(engine, run_id: int, status: str, stats: dict | None = None, error: str | None = None) -> None:
    """(docstring cũ giữ nguyên) … Sau UPDATE: nhả khoá và đóng connection giữ khoá (lát 13)."""
    with engine.connect() as c:
        c.execute(sa.text("UPDATE ops.etl_run SET finished_at = now(), status = :s,"
                          " stats = coalesce(cast(:st AS jsonb), ops.etl_run.stats), error = :e WHERE run_id = :r"),
                  {"s": status, "st": json.dumps(stats) if stats is not None else None, "e": error, "r": run_id})
        c.commit()
    held = _LOCK_CONNS.pop(run_id, None)
    if held is not None:
        lock, job = held
        try:
            lock.execute(sa.text("SELECT pg_advisory_unlock(hashtext(:j))"), {"j": job})
        finally:
            lock.close()


def close_run_refused(engine, run_id: int, error: str, stats: dict | None = None) -> None:
    """Đóng sổ một lượt exit 1 — chốt chặn từ chối, nguồn/model chết, khoá bận: cờ `guard_refused` cho planner."""
    st = dict(stats or {})
    st["guard_refused"] = True
    close_run(engine, run_id, "failed", st, error=error)
```

Thêm `import sys` đầu file. Lưu ý: `_LOCK_CONNS` lưu theo `run_id` nên `news --loop` (một tiến trình, nhiều lượt) và test (một engine, nhiều lượt) đều nhả đúng.

- [ ] **Step 5: Đổi 10 nhánh trả 1** sang `close_run_refused` — ví dụ `price_job.py:141-142`:

```python
            omo_store.close_run_refused(engine, run_id, "guard refused: " + "; ".join(e.verdict.reasons), stats)
```

`refdata/screener/events/snapshot/fundamentals`: `omo_store.close_run_refused(engine, run_id, "guard refused: " + "; ".join(<reasons>))` (không stats). `wichart_job.py:126` và `series_job.py:143`: `close_run_refused(engine, run_id, "guard refused: " + "; ".join(verdict.reasons), stats)`. `news_classify.py:378`: `omo_store.close_run_refused(engine, run_id, str(e), e.stats)`. `news_job.py:431`: `omo_store.close_run_refused(engine, run_id, str(e), e.stats)`. Dry-run (`return 0 if verdict.ok else 1`) giữ nguyên.

- [ ] **Step 6: Xanh + hồi quy** — `uv run pytest tests/etl/test_e67_open_run_lock.py tests/etl/test_e68_exit1_marks_refused.py tests/etl/test_e63_exit_code_contract.py tests/etl/test_e42_interrupt_closes_run.py tests/etl/test_e04_store_flow.py tests/etl/test_e15_screener_job.py tests/etl/test_e25_price_job.py tests/etl/test_e41_wichart_job.py tests/etl/test_e56_news_job.py tests/etl/test_e60_classify_job.py -q` → pass. Kiểm thêm một job thật dưới quyền production (§3.5 CLAUDE.md): `docker compose run --rm etl python -m etl omo` → exit 0, và trong lúc `dlck-fill-price-backfill` còn chạy: `docker compose run --rm etl python -m etl price --backfill` → in `market.price_backfill: lock busy` và exit 1, một dòng `failed` mới trong sổ.

- [ ] **Step 7: Commit** — `git commit -m "feat(etl): advisory lock per job in open_run; every exit-1 path marks stats.guard_refused"`

---

### Task 6: `scheduler/schedule.py` + `planner.py` (spec §5.6–5.8) — Opus

**Files:**
- Create: `backend/etl/scheduler/__init__.py` (rỗng), `backend/etl/scheduler/schedule.py`, `backend/etl/scheduler/planner.py`
- Test: `backend/tests/etl/scheduler/__init__.py` (rỗng), `backend/tests/etl/scheduler/test_sch01_planner.py`

**Interfaces (Produces):**

```python
# schedule.py
MON_FRI = (0, 1, 2, 3, 4); ALL_DAYS = (0, 1, 2, 3, 4, 5, 6); SAT = (5,)
@dataclass(frozen=True)
class JobSpec: name: str; cmd: tuple[str, ...]; kind: str; times: tuple[tuple[int, int], ...] = (); weekdays: tuple[int, ...] = MON_FRI; depends_on: str | None = None; interval_s: int | None = None; once_until_flag: str | None = None
SCHEDULE: list[JobSpec]        # đúng 19 dòng của spec §5.7
MAX_CONCURRENT_CHILDREN = 6; RETRY_AFTER_MIN = 10; TICK_SECONDS = 20; SHUTDOWN_GRACE_S = 60; LOG_KEEP_DAYS = 30; SUMMARY_AT = (6, 0)
def job_names(schedule: list[JobSpec] = SCHEDULE) -> list[str]   # tên duy nhất, thứ tự bảng đưa vào
# planner.py
LedgerRow = namedtuple("LedgerRow", "job started_at finished_at status stats error")   # started_at/finished_at tz-aware
@dataclass(frozen=True)
class Task: spec: JobSpec; reason: str
def day_bounds_utc(now_vn: datetime) -> tuple[datetime, datetime]
def last_mark(spec: JobSpec, now_vn: datetime) -> datetime | None      # mốc gần nhất đã qua HÔM NAY (None nếu chưa mốc nào / sai thứ)
def due(schedule: list[JobSpec], now_vn: datetime, ledger: list[LedgerRow], once_done: frozenset[str] = frozenset()) -> list[Task]
```

`due` bỏ qua `kind in ("intraday", "daemon")`. Với mỗi spec còn lại tính `mark`: `daily` có `times` → `last_mark`; `daily` có `depends_on` → `started_at` của success **mới nhất hôm nay** của cha (không có ⇒ không due); `weekly_once` → `last_mark`, và nếu `spec.name in once_done` ⇒ không due. Rồi trên các dòng `ledger` cùng `job`, `started_at >= mark`: có `success` ⇒ không due; có `failed` với `stats.guard_refused is True` ⇒ không due; đếm `failed` không có cờ = `n`: `n == 0` ⇒ due (`reason="mốc HH:MM"` / `"chuỗi: cha <tên> success"`); `n == 1` và `now >= started_at + RETRY_AFTER_MIN` ⇒ due (`reason="thử lại sau exit 2 lúc HH:MM"`); `n == 1` chưa đủ 10 phút hoặc `n >= 2` ⇒ không. Dòng `running` bị bỏ qua. Thứ tự kết quả = thứ tự `SCHEDULE`.

- [ ] **Step 1: Test đỏ** `backend/tests/etl/scheduler/test_sch01_planner.py` (12 ca literal; tuần thật 2026-09-07 thứ 2 … 2026-09-12 thứ 7):

```python
"""Planner thuần — spec lát 13 §5.8. Ngày thật: 2026-09-09 thứ 4 · 12/09 thứ 7 · 13/09 chủ nhật."""
from datetime import datetime, timedelta, timezone

from core.clock import VN
from etl.scheduler import planner
from etl.scheduler.planner import LedgerRow, day_bounds_utc, due
from etl.scheduler.schedule import ALL_DAYS, MON_FRI, SCHEDULE, JobSpec


def vn(d, h, mi):
    return datetime(2026, 9, d, h, mi, tzinfo=VN)


def row(job, h, mi, status="success", stats=None, d=9):
    return LedgerRow(job, vn(d, h, mi), vn(d, h, mi) + timedelta(minutes=1), status, stats or {}, None)


PRICE = JobSpec("market.price_daily", ("price",), "daily", times=((15, 40),))
EVENTS = JobSpec("market.events", ("events",), "daily", times=((18, 10),))
SNAP = JobSpec("market.snapshot", ("snapshot",), "daily", depends_on="market.events")
OMO = JobSpec("macro.omo_crawl", ("omo",), "daily", weekdays=ALL_DAYS, times=((11, 30), (15, 30), (18, 0), (21, 30)))
BF = JobSpec("market.price_backfill", ("price", "--backfill", "--stop-before-open"), "weekly_once", weekdays=(5,), times=((0, 5),), once_until_flag="pass_complete")
INTRA = JobSpec("global.yahoo", ("yahoo", "--intraday"), "intraday", weekdays=ALL_DAYS, interval_s=600)
DAEMON = JobSpec("news.collect", ("news", "--loop"), "daemon")


def names(tasks):
    return [t.spec.name for t in tasks]


def test_day_bounds_utc_for_a_vn_night():
    start, end = day_bounds_utc(datetime(2026, 9, 10, 0, 30, tzinfo=VN))
    assert start == datetime(2026, 9, 9, 17, 0, tzinfo=timezone.utc) and end == datetime(2026, 9, 10, 17, 0, tzinfo=timezone.utc)


def test_due_fires_once_the_mark_has_passed_with_no_success():
    assert names(due([PRICE], vn(9, 15, 41), [])) == ["market.price_daily"]
    assert due([PRICE], vn(9, 15, 40), [])[0].reason == "mốc 15:40"


def test_not_due_before_the_mark_or_on_a_weekend():
    assert due([PRICE], vn(9, 15, 39), []) == []
    assert due([PRICE], vn(12, 16, 0), []) == []              # thứ 7, MON_FRI


def test_silent_once_marked_success_after_the_mark():
    assert due([PRICE], vn(9, 16, 0), [row("market.price_daily", 15, 42)]) == []


def test_a_success_before_the_mark_does_not_count():
    assert names(due([PRICE], vn(9, 16, 0), [row("market.price_daily", 10, 0)])) == ["market.price_daily"]   # lượt thử tải buổi sáng


def test_omo_recatches_the_15_30_slot_but_is_quiet_after_a_fresh_success():
    assert names(due([OMO], vn(9, 15, 31), [row("macro.omo_crawl", 11, 35)])) == ["macro.omo_crawl"]
    assert due([OMO], vn(9, 15, 35), [row("macro.omo_crawl", 15, 31)]) == []


def test_snapshot_waits_for_events_then_fires():
    assert due([EVENTS, SNAP], vn(9, 20, 0), [row("market.events", 18, 12, "failed", {"guard_refused": True})]) == []
    tasks = due([EVENTS, SNAP], vn(9, 18, 13), [row("market.events", 18, 12)])
    assert names(tasks) == ["market.snapshot"] and tasks[0].reason == "chuỗi: cha market.events success"


def test_exit2_retries_once_after_ten_minutes_then_stops():
    fail = row("market.price_daily", 15, 41, "failed")
    assert due([PRICE], vn(9, 15, 49), [fail]) == []
    tasks = due([PRICE], vn(9, 15, 52), [fail])
    assert names(tasks) == ["market.price_daily"] and tasks[0].reason == "thử lại sau exit 2 lúc 15:41"
    assert due([PRICE], vn(9, 16, 30), [fail, row("market.price_daily", 15, 53, "failed")]) == []


def test_guard_refused_never_retries_the_same_day():
    assert due([PRICE], vn(9, 20, 0), [row("market.price_daily", 15, 41, "failed", {"guard_refused": True})]) == []


def test_running_rows_are_ignored():
    assert names(due([PRICE], vn(9, 15, 45), [row("market.price_daily", 15, 41, "running")])) == ["market.price_daily"]


def test_saturday_backfill_due_at_00_05_and_off_forever_after_pass_complete():
    assert names(due([BF], vn(12, 0, 5), [])) == ["market.price_backfill"]
    assert due([BF], vn(13, 0, 5), []) == []                                        # chủ nhật
    assert due([BF], vn(12, 10, 0), [], once_done=frozenset({"market.price_backfill"})) == []


def test_intraday_and_daemon_never_appear():
    assert due([INTRA, DAEMON], vn(9, 12, 0), []) == []


def test_schedule_is_the_spec_table():
    assert len(SCHEDULE) == 19
    assert [s.name for s in SCHEDULE if s.kind == "daemon"] == ["news.collect"]
    assert [s.interval_s for s in SCHEDULE if s.kind == "intraday"] == [600, 300, 300]
    classify = next(s for s in SCHEDULE if s.name == "news.classify")
    assert classify.times == ((7, 0), (9, 0), (11, 0), (13, 0), (15, 0), (17, 0), (19, 0), (21, 0)) and classify.weekdays == ALL_DAYS
    assert next(s for s in SCHEDULE if s.name == "market.fundamentals").depends_on == "market.snapshot"
    assert next(s for s in SCHEDULE if s.name == "macro.wichart" and s.kind == "daily").times == ((8, 15),)
    assert next(s for s in SCHEDULE if s.name == "market.refdata").weekdays == MON_FRI
```

- [ ] **Step 2: Đỏ** — `uv run pytest tests/etl/scheduler -q` → `ModuleNotFoundError: etl.scheduler`.

- [ ] **Step 3: Implement `schedule.py`** — đúng bảng spec §5.7 (19 `JobSpec`, comment chỗ lát 14), các hằng ở Interfaces, `job_names()`.

- [ ] **Step 4: Implement `planner.py`** theo mô tả Interfaces. Khung:

```python
def last_mark(spec, now_vn):
    if now_vn.weekday() not in spec.weekdays or not spec.times:
        return None
    passed = [datetime.combine(now_vn.date(), dtime(h, m), tzinfo=now_vn.tzinfo) for h, m in spec.times
              if (h, m) <= (now_vn.hour, now_vn.minute)]
    return max(passed) if passed else None


def _verdict(spec, mark, now_vn, rows):
    since = [r for r in rows if r.job == spec.name and r.started_at >= mark]
    if any(r.status == "success" for r in since):
        return None
    if any(r.status == "failed" and (r.stats or {}).get("guard_refused") is True for r in since):
        return None
    real = sorted((r for r in since if r.status == "failed"), key=lambda r: r.started_at)
    if not real:
        return "mốc"
    if len(real) == 1 and now_vn >= real[0].started_at + timedelta(minutes=RETRY_AFTER_MIN):
        return f"thử lại sau exit 2 lúc {real[0].started_at.astimezone(now_vn.tzinfo):%H:%M}"
    return None
```

`due` ghép `reason`: mốc ⇒ `f"mốc {mark:%H:%M}"`; chuỗi ⇒ `f"chuỗi: cha {spec.depends_on} success"`; thử lại giữ nguyên chuỗi từ `_verdict`. So sánh `r.started_at >= mark` với datetime có tz (ledger từ Postgres là UTC tz-aware).

- [ ] **Step 5: Xanh** — `uv run pytest tests/etl/scheduler/test_sch01_planner.py tests/core/test_tz_contract.py -q` → pass (không giờ trần).

- [ ] **Step 6: Commit** — `git commit -m "feat(scheduler): schedule table and pure planner with the six catch-up rules"`

---

### Task 7: `scheduler/runner.py` (spec §5.10–5.11) — Opus

**Files:**
- Create: `backend/etl/scheduler/runner.py`
- Test: `backend/tests/etl/scheduler/test_sch02_runner.py`

**Interfaces (Produces):**

```python
@dataclass
class Child: spec: JobSpec; proc: object; started_at: datetime; log_fh: object; reason: str
@dataclass(frozen=True)
class Finished: name: str; rc: int; seconds: int; reason: str
class Runner:
    def __init__(self, log_dir: Path, *, spawn_fn=subprocess.Popen, clock=now_vn, max_children: int = MAX_CONCURRENT_CHILDREN, python: str = sys.executable): ...
    def alive(self, name: str) -> bool
    def log_path(self, name: str, now: datetime) -> Path          # <log_dir>/<name>-YYYYMMDD.log
    def spawn(self, spec: JobSpec, now: datetime, reason: str) -> Child | None   # None nếu đang sống cùng tên hoặc đầy trần (daemon không tính trần)
    def reconcile(self, tasks: list[Task], now: datetime) -> list[str]          # tên đã spawn
    def tick_intraday(self, specs: list[JobSpec], now: datetime) -> list[str]   # spawn khi đủ interval_s và không sống
    def ensure_daemon(self, spec: JobSpec, now: datetime) -> bool               # True nếu vừa spawn; backoff 30→300 s, reset khi sống > 300 s
    def poll(self, now: datetime) -> list[Finished]                             # in 1 dòng stdout mỗi con vừa thoát
    def shutdown(self, *, grace_s: int = SHUTDOWN_GRACE_S, sleep=time.sleep) -> None   # terminate/CTRL_BREAK → chờ → kill
    def prune_old_logs(self, now: datetime, keep_days: int = LOG_KEEP_DAYS) -> list[str]
```

Spawn: `spawn_fn([python, "-m", "etl", *spec.cmd], cwd=BACKEND_DIR, env=os.environ.copy(), stdout=fh, stderr=subprocess.STDOUT, **platform_kwargs)` với `platform_kwargs = {"start_new_session": True}` trên POSIX, `{"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}` trên Windows. Dòng stdout khi con thoát: `f"[{now:%Y-%m-%d %H:%M:%S}] {name} rc={rc} {seconds}s ({reason})"`.

- [ ] **Step 1: Test đỏ** `test_sch02_runner.py` với `FakePopen` (thuộc tính `returncode`, `poll()`, `terminate()`, `kill()`, `wait(timeout)`, `send_signal`) và `FakeClock` (khuôn `test_i16_daemon`), `tmp_path` làm `log_dir`:

```python
class FakePopen:
    def __init__(self, exits_after: int | None = 0):   # số lần poll trả None trước khi thoát; None = sống mãi
        self.left, self.returncode, self.terminated, self.killed = exits_after, None, 0, 0
    def poll(self):
        if self.left is None:
            return None
        if self.left == 0:
            self.returncode = 0
        else:
            self.left -= 1
        return self.returncode
    def terminate(self): self.terminated += 1
    def send_signal(self, _s): self.terminated += 1
    def kill(self): self.killed += 1; self.returncode = -9
    def wait(self, timeout=None): return self.returncode


def test_spawn_writes_a_daily_log_file_and_blocks_duplicates(tmp_path):
    spawned = []
    r = Runner(tmp_path, spawn_fn=lambda cmd, **kw: spawned.append((cmd, kw)) or FakePopen(None), clock=lambda: vn(9, 15, 40))
    assert r.spawn(PRICE, vn(9, 15, 40), "mốc 15:40") is not None
    assert (tmp_path / "market.price_daily-20260909.log").exists()
    assert spawned[0][0][1:] == ["-m", "etl", "price"]
    assert r.spawn(PRICE, vn(9, 15, 41), "mốc 15:40") is None and len(spawned) == 1


def _runner(tmp_path, clock, exits_after=None, log=None):
    log = [] if log is None else log
    return Runner(tmp_path, spawn_fn=lambda cmd, **kw: log.append(cmd) or FakePopen(exits_after), clock=clock), log


def test_cap_of_six_children_excludes_the_daemon(tmp_path):
    r, log = _runner(tmp_path, lambda: vn(9, 15, 40))
    specs = [JobSpec(f"zz.j{i}", ("omo",), "daily", times=((15, 40),)) for i in range(7)]
    spawned = r.reconcile([Task(s, "mốc 15:40") for s in specs], vn(9, 15, 40))
    assert spawned == [f"zz.j{i}" for i in range(6)]                       # con thứ 7 chờ nhịp sau
    assert r.ensure_daemon(DAEMON, vn(9, 15, 40)) is True                     # daemon không tính vào trần
    assert len(log) == 7


def test_poll_reports_exit_code_and_duration(tmp_path, capsys):
    r, _ = _runner(tmp_path, lambda: vn(9, 15, 40), exits_after=2)
    r.spawn(PRICE, vn(9, 15, 40), "mốc 15:40")
    assert r.poll(vn(9, 16, 0)) == [] and r.poll(vn(9, 16, 20)) == []
    fin = r.poll(vn(9, 16, 20))
    assert fin == [Finished("market.price_daily", 0, 40, "mốc 15:40")]
    assert "market.price_daily rc=0 40s (mốc 15:40)" in capsys.readouterr().out
    assert r.alive("market.price_daily") is False


def test_intraday_spawns_on_interval_only_when_not_alive(tmp_path):
    r, log = _runner(tmp_path, lambda: vn(9, 12, 0), exits_after=None)
    t0 = vn(9, 12, 0)
    assert r.tick_intraday([INTRA], t0) == ["global.yahoo"]
    assert r.tick_intraday([INTRA], t0 + timedelta(seconds=300)) == []
    assert r.tick_intraday([INTRA], t0 + timedelta(seconds=600)) == []      # đủ nhịp nhưng con còn sống
    r._children["global.yahoo"].proc.left = 0                                # cho con "chết"
    r.poll(t0 + timedelta(seconds=620))
    assert r.tick_intraday([INTRA], t0 + timedelta(seconds=620)) == ["global.yahoo"]
    assert len(log) == 2


def test_daemon_backoff_30_60_120_and_reset(tmp_path):
    fc = FakeClock(vn(9, 12, 0))
    r, log = _runner(tmp_path, fc.now, exits_after=0)                        # con chết ngay ở lần poll đầu
    marks = []
    for _ in range(4):
        if r.ensure_daemon(DAEMON, fc.now()):
            marks.append(fc.now())
        r.poll(fc.now())
        fc.t += timedelta(seconds=10)
        while not r.ensure_daemon(DAEMON, fc.now()):
            fc.t += timedelta(seconds=10)
        marks.append(fc.now())
        r.poll(fc.now())
    gaps = [(b - a).total_seconds() for a, b in zip(marks, marks[1:])][:3]
    assert gaps == [30.0, 60.0, 120.0]
    fc.t += timedelta(seconds=400)                                            # sống quá 300 s ⇒ reset
    r._children["news.collect"].proc.left = 0
    r.poll(fc.now())
    fc.t += timedelta(seconds=30)
    assert r.ensure_daemon(DAEMON, fc.now()) is True


def test_shutdown_terminates_then_kills_after_grace(tmp_path):
    r, _ = _runner(tmp_path, lambda: vn(9, 15, 40), exits_after=None)
    r.spawn(PRICE, vn(9, 15, 40), "mốc 15:40")
    proc = r._children["market.price_daily"].proc
    slept = []
    r.shutdown(grace_s=60, sleep=lambda s: slept.append(s))
    assert proc.terminated == 1 and proc.killed == 1 and sum(slept) >= 60
    assert r.alive("market.price_daily") is False


def test_prune_old_logs_keeps_30_days(tmp_path):
    (tmp_path / "zz-20260101.log").write_text("cũ", encoding="utf-8")
    (tmp_path / "zz-20260909.log").write_text("mới", encoding="utf-8")
    r, _ = _runner(tmp_path, lambda: vn(9, 15, 40))
    assert r.prune_old_logs(vn(9, 15, 40)) == ["zz-20260101.log"]
    assert sorted(p.name for p in tmp_path.iterdir()) == ["zz-20260909.log"]
```

`PRICE`, `INTRA`, `DAEMON`, `vn`, `FakeClock` chép từ `test_sch01_planner.py` (FakeClock: `t`, `now()`). `Runner._children: dict[str, Child]` là seam nội bộ test được phép chạm để "giết" con giả.

- [ ] **Step 2: Đỏ** — `uv run pytest tests/etl/scheduler/test_sch02_runner.py -q` → `ImportError`.

- [ ] **Step 3: Implement `runner.py`** theo Interfaces; `poll()` đóng `log_fh` khi con thoát; `ensure_daemon` giữ `_daemon_last_exit`, `_daemon_backoff` trong RAM (vô hại — spec §4.3). `prune_old_logs` theo khuôn `ingester.measure.prune_old` (parse `YYYYMMDD` trong tên, cắt theo `today_vn`).

- [ ] **Step 4: Xanh** — `uv run pytest tests/etl/scheduler -q tests/core/test_tz_contract.py` → pass.

- [ ] **Step 5: Commit** — `git commit -m "feat(scheduler): runner spawns children with per-job daily logs, cap, daemon backoff and graceful shutdown"`

---

### Task 8: `scheduler/loop.py` + CLI (spec §5.6, §5.10, §5.12) — Opus

**Files:**
- Create: `backend/etl/scheduler/loop.py`
- Modify: `backend/etl/__main__.py:7,13-20` (bỏ heartbeat, nhánh không tham số)
- Delete: `backend/etl/heartbeat.py`, `backend/tests/test_heartbeat.py`
- Test: `backend/tests/etl/scheduler/test_sch03_loop.py`, `backend/tests/etl/test_e01_cli.py`

**Interfaces (Produces):**

```python
def resolve_log_dir(env: Mapping[str, str]) -> Path        # env["ETL_LOG_DIR"] hoặc REPO_ROOT.parent/"dlck-runtime"/"etl-logs"; mkdir
def read_today(engine, now_vn: datetime, job_names: list[str]) -> list[LedgerRow]   # SQL spec §5.8
def once_done(engine) -> frozenset[str]                     # job có success với stats.pass_complete = true (mọi thời điểm)
def summary_lines(engine, now_vn: datetime) -> list[str]    # 24 giờ qua: "<job> success=<n> refused=<n> lock_busy=<n> failed=<n> interrupted=<n>"
def run_once(engine, runner, now_vn, *, schedule=SCHEDULE) -> dict   # một nhịp: ensure_daemon → tick_intraday → due → reconcile → poll → prune; trả {"spawned": [...], "finished": [...]}
def main(argv: list[str] | None = None) -> int              # vòng 20 s tới khi cờ dừng; SIGTERM/SIGINT đặt cờ; thoát 0; thiếu env ⇒ 2
```

- [ ] **Step 1: Test đỏ** `backend/tests/etl/scheduler/test_sch03_loop.py`:

```python
"""loop.py: nối planner + runner với sổ thật (spec lát 13 §5.6, §5.8, §5.10). Ngày giả cố định 2026-09-09 (thứ 4)."""
import json
from datetime import datetime, timedelta

import pytest
import sqlalchemy as sa

from core.clock import VN
from etl.scheduler import loop
from etl.scheduler.runner import Runner
from etl.scheduler.schedule import ALL_DAYS, JobSpec

JOB = "zz.loop.a"


def vn(d, h, mi):
    return datetime(2026, 9, d, h, mi, tzinfo=VN)


def _insert(engine, job, started, status="success", stats=None):
    with engine.begin() as c:
        c.execute(sa.text("INSERT INTO ops.etl_run (job, started_at, finished_at, status, stats)"
                          " VALUES (:j, :s, :s, :st, cast(:x AS jsonb))"),
                  {"j": job, "s": started, "st": status, "x": json.dumps(stats or {})})


@pytest.fixture()
def clean(migrated_engine):
    yield migrated_engine
    with migrated_engine.begin() as c:
        c.execute(sa.text("DELETE FROM ops.etl_run WHERE job LIKE 'zz.loop.%'"))


def test_resolve_log_dir_prefers_env_and_creates_it(tmp_path):
    p = loop.resolve_log_dir({"ETL_LOG_DIR": str(tmp_path / "x")})
    assert p == tmp_path / "x" and p.is_dir()
    assert loop.resolve_log_dir({}).as_posix().endswith("dlck-runtime/etl-logs")


def test_read_today_filters_by_vn_day_and_drops_intraday_subset_dry_run(clean):
    _insert(clean, JOB, vn(9, 8, 5))
    _insert(clean, JOB, vn(9, 9, 0), stats={"intraday": True})
    _insert(clean, JOB, vn(9, 9, 5), stats={"subset": True})
    _insert(clean, JOB, vn(9, 9, 10), stats={"dry_run": True})
    _insert(clean, JOB, vn(8, 23, 0))
    rows = loop.read_today(clean, vn(9, 10, 0), [JOB])
    assert [(r.job, r.started_at.astimezone(VN).hour, r.status) for r in rows] == [(JOB, 8, "success")]


def test_once_done_lists_jobs_that_ever_completed_a_pass(clean):
    _insert(clean, "zz.loop.bf", vn(5, 0, 5), stats={"pass_complete": True})
    _insert(clean, "zz.loop.nb", vn(5, 0, 5), stats={"pass_complete": False})
    done = loop.once_done(clean)
    assert "zz.loop.bf" in done and "zz.loop.nb" not in done


def test_summary_lines_count_last_24h_by_outcome(clean):
    _insert(clean, JOB, vn(9, 8, 5))
    _insert(clean, JOB, vn(9, 8, 6), "failed", {"guard_refused": True})
    _insert(clean, JOB, vn(9, 8, 7), "failed", {"guard_refused": True, "lock_busy": True})
    lines = loop.summary_lines(clean, vn(9, 9, 0))
    assert "zz.loop.a success=1 refused=2 lock_busy=1 failed=0 interrupted=0" in lines


class FakePopen:
    def __init__(self):
        self.returncode = None
    def poll(self):
        return self.returncode
    def terminate(self):
        self.returncode = 130
    def send_signal(self, _s):
        self.returncode = 130
    def kill(self):
        self.returncode = -9
    def wait(self, timeout=None):
        return self.returncode


def test_run_once_spawns_daemon_intraday_then_due_marks_in_order(clean, tmp_path):
    schedule = [JobSpec("zz.loop.a", ("omo",), "daily", weekdays=ALL_DAYS, times=((8, 0),)),
                JobSpec("zz.loop.b", ("omo",), "daily", weekdays=ALL_DAYS, depends_on="zz.loop.a"),
                JobSpec("zz.loop.i", ("yahoo", "--intraday"), "intraday", weekdays=ALL_DAYS, interval_s=600),
                JobSpec("zz.loop.d", ("news", "--loop"), "daemon")]
    spawned = []
    runner = Runner(tmp_path, spawn_fn=lambda cmd, **kw: spawned.append(cmd[3]) or FakePopen(), clock=lambda: vn(9, 8, 16))
    out = loop.run_once(clean, runner, vn(9, 8, 16), schedule=schedule)
    assert out["spawned"] == ["zz.loop.d", "zz.loop.i", "zz.loop.a"] and out["finished"] == []
    _insert(clean, "zz.loop.a", vn(9, 8, 17))                       # cha success ⇒ con tới hạn ở nhịp sau
    runner._children["zz.loop.a"].proc.returncode = 0
    out = loop.run_once(clean, runner, vn(9, 8, 18), schedule=schedule)
    assert out["spawned"] == ["zz.loop.b"] and [f.name for f in out["finished"]] == ["zz.loop.a"]
    assert spawned == ["news", "yahoo", "omo", "omo"]
```

Thêm vào `test_e01_cli.py`:

```python
def test_no_args_runs_the_scheduler_loop(monkeypatch):
    import etl.scheduler.loop
    monkeypatch.setattr(etl.scheduler.loop, "main", lambda argv=None: 7)
    assert main([]) == 7
```

Xoá `backend/tests/test_heartbeat.py`.

- [ ] **Step 2: Đỏ** — `uv run pytest tests/etl/scheduler/test_sch03_loop.py tests/etl/test_e01_cli.py -q`.

- [ ] **Step 3: Implement `loop.py`** — `main()`: `load_dotenv()`; `url = ETL_DATABASE_URL` thiếu ⇒ in lý do, `return 2`; `log_dir = resolve_log_dir(os.environ)`; `engine = create_engine(url, pool_pre_ping=True)`; cờ `_stop = threading.Event()`; `signal.signal(SIGTERM, ...)` và `SIGINT` đặt cờ (đăng ký SAU `install_signal_handlers` của `__main__`, nên thắng); vòng: `now = now_vn(); run_once(...); if now đã qua SUMMARY_AT và chưa in hôm nay: print(*summary_lines)`; `_stop.wait(TICK_SECONDS)`; khi dừng: `runner.shutdown()`, `engine.dispose()`, `return 0`. Log một dòng lúc khởi động: `scheduler: <n> job, log_dir=<path>, tick 20s`.
  `__main__.py`: bỏ `import time`, `datetime`, `heartbeat`; `if not args: from etl.scheduler.loop import main as loop_main; return loop_main()`.

- [ ] **Step 4: Xanh + toàn bộ** — `uv run pytest tests -q` → pass (số test mới do `database/README.md` ghi ở Task 12); `git grep -n heartbeat -- backend` → 0.

- [ ] **Step 5: Chạy thử native 3 phút** (§3.5 CLAUDE.md, ngoài giờ hoặc trong giờ đều được — mọi mốc đã qua hôm nay sẽ bù ngay, đó chính là phép thử):

```bash
cd backend && PYTHONIOENCODING=utf-8 timeout 180 uv run python -m etl ; echo rc=$?
ls ../../dlck-runtime/etl-logs
```

Expected: dòng khởi động, các dòng `rc=` khi con thoát, file `<job>-20260909.log`; Ctrl+C/timeout ⇒ thoát sạch, con nhận tín hiệu. Ghi output vào ledger.

- [ ] **Step 6: Commit** — `git commit -m "feat(scheduler): loop wires planner and runner to the ledger; python -m etl runs it"`

---

### Task 9: Nhịp ngày và chuỗi phụ thuộc trên kho thật — kiểm bù (AC5 phần native)

**Files:** không sửa code (nếu lộ lỗi thì quay lại Task 6–8 theo TDD).

- [ ] **Step 1:** Trong giờ chiều 09/09 (sau 15:05), với `dlck-fill-*` đã xong, chạy native `uv run python -m etl` 10 phút: expected bù đúng thứ tự `screener` → `price` → `events` → `snapshot` → `fundamentals`, `omo` mốc 15:30, các job quốc tế đã success hôm nay không chạy lại. Ghi bảng "job · reason · rc" vào ledger.
- [ ] **Step 2:** Chạy tay chồng: trong lúc scheduler đang chạy `price`, mở `docker compose run --rm etl python -m etl price` ⇒ exit 1, sổ có dòng `lock_busy`. Ghi ledger (AC6 phần 1).

---

### Task 10: Compose · Dockerfile · env · test hợp đồng (spec §5.12)

**Files:**
- Modify: `docker-compose.yml` (service `etl` `environment` + `volumes`, khối `volumes:` gốc, comment dòng 117), `deploy/backend.Dockerfile:10`, `.env.example:44-48`, `backend/core/env.py` (`OPTIONAL_KEYS`)
- Test: `backend/tests/docs/test_d03_compose_contract.py`

- [ ] **Step 1: Test đỏ** — `ETL_OVERRIDES` thêm `"ETL_LOG_DIR": "/var/lib/dlck/etl-logs"`; test mới:

```python
def test_etl_log_dir_is_a_named_volume_next_to_backups():
    etl = _services()["etl"]
    targets = {v.split(":")[1] for v in etl["volumes"]}
    assert targets == {"/backups", "/var/lib/dlck/etl-logs"}
    assert "etl_logs" in yaml.safe_load(COMPOSE.read_text(encoding="utf-8"))["volumes"]
```

và trong `test_image_owns_the_runtime_dirs_for_appuser` thêm `"/var/lib/dlck/etl-logs"` vào tuple.

- [ ] **Step 2: Đỏ** — `uv run pytest tests/docs/test_d03_compose_contract.py tests/core/test_env_contract.py -q`.

- [ ] **Step 3: Implement** — compose:

```yaml
  # Scheduler (lát 13): `python -m etl` không tham số = vòng lịch trong etl/scheduler/. Job lẻ vẫn chạy qua `docker compose run --rm etl …`.
  etl:
    <<: *app
    restart: unless-stopped
    command: ["python", "-m", "etl"]
    stop_grace_period: 60s
    environment:
      <<: *app-env
      CLICKHOUSE_BACKUP_DIR: /backups
      ETL_LOG_DIR: /var/lib/dlck/etl-logs
    volumes:
      - ${CLICKHOUSE_BACKUP_DIR:-./deploy/infra/clickhouse-backups}:/backups
      - etl_logs:/var/lib/dlck/etl-logs
```

khối `volumes:` gốc thêm `etl_logs:`; Dockerfile `mkdir -p … /var/lib/dlck/etl-logs …` (cùng lệnh RUN, `chown -R appuser … /var/lib/dlck …` đã phủ); `.env.example` thêm `# ETL_LOG_DIR=` sau `# INGESTER_SPILL_DIR=` với chú thích "log từng job của scheduler (lát 13); để trống khi native = <repo>/../dlck-runtime/etl-logs"; `core/env.py` `OPTIONAL_KEYS` thêm `"ETL_LOG_DIR"`.

- [ ] **Step 4: Xanh** — `uv run pytest tests/docs tests/core/test_env_contract.py tests/core/test_env.py -q` → pass; `docker compose config --quiet` → 0.

- [ ] **Step 5: Commit** — `git commit -m "build(compose): etl service gets ETL_LOG_DIR and the etl_logs volume for the scheduler"`

---

### Task 11: Nghiệm thu chạy thật trong container (AC4–AC7, AC10) — controller

- [ ] **Step 1 (sáng 10/09 ~07:30):** build và lên cả hệ — đây là lần `up` đầu tiên sau khi dừng ingester:

```bash
docker compose up -d --build
docker compose ps -a
docker compose logs --tail 20 etl
```

Expected: `migrate` `Exited (0)`; `etl` in dòng khởi động rồi bù các mốc đã qua (05:00 fred, 07:15 binance nếu đã qua); `ingester` "ngoài phiên, chờ tới 08:30".

- [ ] **Step 2 (AC5):** `docker compose stop etl` lúc 08:10, `docker compose start etl` lúc 08:20 ⇒ trong ≤ 40 s sổ có `market.refdata` mốc 08:00 (`reason` "mốc 08:00") và `macro.wichart` 08:15. Ghi ledger.
- [ ] **Step 3 (AC7):** `docker compose stop etl` trong lúc một job `daily` đang chạy (ví dụ 15:41 khi `price` chạy) ⇒ dòng `market.price_daily` `failed: dừng tay (Ctrl+C)`, container `etl` thoát 0 trong ≤ 60 s; `start` lại ⇒ planner thấy 1 failed không cờ ⇒ thử lại sau 10 phút. Ghi ledger.
- [ ] **Step 4 (AC6):** trùng mốc 18:10 chạy tay `docker compose run --rm etl python -m etl events` ⇒ exit 1 `lock busy`.
- [ ] **Step 5 (AC4):** sau 24 giờ (sáng 11/09) đọc bảng tóm tắt 06:00 trên `docker compose logs etl` và truy vấn:

```sql
SELECT job, count(*) FILTER (WHERE status='success') AS ok, count(*) FILTER (WHERE stats->>'guard_refused'='true') AS refused,
       count(*) FILTER (WHERE status='failed' AND coalesce(stats->>'guard_refused','false')<>'true' AND error NOT LIKE 'dừng tay%') AS real_fail
FROM ops.etl_run WHERE started_at >= now() - interval '24 hours' GROUP BY job ORDER BY job;
```

Expected: mọi job `daily` có `ok ≥ 1`; `real_fail = 0` hoặc từng dòng có giải thích trong ledger; `news.collect` liên tục (số vòng ≈ 288).

- [ ] **Step 6 (AC10):** sau 15:05 ngày 10/09: `docker compose logs --tail 30 ingester` có `reconcile:`; `docker compose exec clickhouse clickhouse-client --password "$CLICKHOUSE_PASSWORD" -q "select count() from rt.trade where toDate(received_at) = today()"` > 0. Ghi vào **ledger lát 12** mục mới "Phiên thật đầu tiên trong container (10/09)" và ledger lát 13.
- [ ] **Step 7 (AC9):** 10–12/09 mỗi sáng đọc tóm tắt; 12/09 xử lý `refdata --accept-drop` (Task 0 Step 10); ghi giờ nạp vĩ mô WiChart (so `stats.changed` của lượt 08:15 với lượt intraday cùng ngày).

---

### Task 12: Tài liệu sống (spec §8) — Opus, một lượt

**Files:** `backend/README.md`, `docs/10-sources/macro/sbv-omo.md` (Giới hạn 2 dòng 145-151; §8 dòng 211-217; §4 danh mục kỳ hạn; thêm mục "Hai phiên một ngày" và dòng pháp lý FiinProX), `docs/20-design/service-topology.md` (§2 bảng `etl`, §5 mục 5, §6 bố cục container thêm `etl_logs`), `docs/20-design/market-data-store.md` (dòng 213, 246-252 quota → nhịp), `database/README.md` (migration `0021`, số test), `docs/00-overview/roadmap.md` ([4d] dòng 53 + §3 dòng lát 13 + "Điểm vào cho lát 14"), `docs/90-records/README.md` (trạng thái dòng lát 13), `.env.example` (đã ở Task 10).

- [ ] **Step 1:** `backend/README.md`: mục mới "Scheduler (`python -m etl`)" — bảng lịch (chép §5.7), sáu luật bù, khoá và mã 1 `lock busy`, log `<job>-YYYYMMDD.log` ở `ETL_LOG_DIR`, tóm tắt 06:00; mục `etl omo --seed`; snapshot: bỏ câu quota (dòng 191, 197) thay bằng "tới nhịp 30/90 ngày quét trọn"; classify: `classify_attempts`, 8 mốc; xoá mọi "⚠️ Chưa đăng ký task Scheduler" (dòng 230, 266, 305, 362).
- [ ] **Step 2:** `sbv-omo.md`: Giới hạn 2 thêm đoạn *"✅ 2026-09-09: số dư tính được từ ngày đầu nhờ seed một năm từ FiinProX, khớp tới từng đồng với cột lưu hành của họ từ 19/12/2025"*; §8 điều kiện 1 ghi "đã thoả bằng seed"; §4 kỳ hạn thêm 42 và 105 *(đo FiinProX 2026-09-09)*; mục mới "Hai phiên một ngày" (03/02/2026, parser gộp); dòng pháp lý: *"FiinProX: chủ dự án xác nhận được dùng, 2026-09-09"*.
- [ ] **Step 3:** `service-topology.md`, `market-data-store.md`, `database/README.md` như bảng file.
- [ ] **Step 4:** roadmap: [4d] thêm *"✅ Cập nhật 2026-09-09: kho dev là kho thật, không xoá dựng lại; ingester bật lại 10/09; mọi job chạy theo scheduler từ khi lát 13 tiếp quản"*; dòng lát 13 §3 ghi ✅ kèm ngày; viết "Điểm vào cho lát 14" (giám sát hợp đồng: thêm một `JobSpec`; dọn dòng `running` mồ côi; kênh báo động; số đo từ ba ngày chạy thử).
- [ ] **Step 5: Phép kiểm §1.7** — `git grep -n "heartbeat\|Chưa đăng ký task\|QUOTA" -- docs backend README.md` → mọi hit thuộc `90-records/`, `decisions/` hoặc khối gạch ngang lịch sử.
- [ ] **Step 6: Commit** — `git commit -m "docs: slice 13 scheduler, OMO seed, snapshot cadence, classify attempts; roadmap entry for slice 14"`

---

### Task 13: Review, verify, khép nhánh (CLAUDE.md §4.1.5–7)

- [ ] **Step 1:** `superpowers:requesting-code-review` — hai trục Chuẩn và Spec, reviewer Opus, gói diff `main..feat/etl-scheduler`. Sửa theo vòng, re-review phạm vi hẹp.
- [ ] **Step 2:** `superpowers:verification-before-completion`: `cd backend && uv run pytest tests -q` (dán output), `git grep -c "\[DEBUG-" -- backend` → 0, `docker compose config --quiet`.
- [ ] **Step 3:** Sau AC9 (ba ngày chạy thử tới 12/09): `superpowers:finishing-a-development-branch` — merge `--no-ff` vào `main`, cả bộ trên `main`, push, xoá nhánh; ghi SHA vào roadmap và `90-records/README.md`; cập nhật memory `slice-12-in-progress` → lát 13 khép.
