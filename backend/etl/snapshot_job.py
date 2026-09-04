"""Một lượt chạy snapshot: due_list → fetch → guard → apply → re-crawl giá (spec §5.1).

Y khuôn `events_job.run`: MỘT giao dịch cho dữ liệu, guard đánh giá TRƯỚC commit — từ chối
thì raise bên trong `engine.begin()` để tự rollback; bằng chứng ghi ở giao dịch riêng.
"""
from __future__ import annotations

import logging
import os
import sys
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import sqlalchemy as sa

from core.env import load_dotenv
from etl import omo_store, snapshot_fetch, snapshot_guard, snapshot_store
from etl.snapshot_fetch import BadShape, FetchError

log = logging.getLogger("etl.snapshot")
JOB = snapshot_store.JOB
VN = ZoneInfo("Asia/Ho_Chi_Minh")
MAX_RECRAWL = 50                       # trần re-crawl giá một lượt — xem chú thích trong _recrawl
RECRAWL_MAX_MINUTES = 20               # trần thời gian cho phần re-crawl giá — xem chú thích trong _recrawl


class GuardRefused(Exception):
    def __init__(self, verdict):
        self.verdict = verdict
        super().__init__("; ".join(verdict.reasons))


def _engine():
    url = os.environ.get("ETL_DATABASE_URL")
    if not url:
        raise RuntimeError("thiếu ETL_DATABASE_URL")
    # pool_pre_ping: kết nối nằm trong pool suốt lượt fetch dài có thể chết sau giấc ngủ 02:00
    return sa.create_engine(url, pool_pre_ping=True)


def _fetch_all(targets, get, sleep, deadline):
    fetched, failed, bad_shape, stopped = [], 0, 0, False
    with snapshot_fetch.open_fetcher(get=get, sleep=sleep) as f:
        for i, t in enumerate(targets, 1):
            if deadline is not None and time.monotonic() > deadline:
                stopped = True
                log.info("hết ngân sách thời gian sau %d/%d target", i - 1, len(targets))
                break
            try:
                item, text = f.fetch_one(t)
                fetched.append(snapshot_store.Fetched(target=t, item=item, text=text))
            except BadShape as e:
                bad_shape += 1
                log.warning("hình dạng lạ: %s", e)
            except FetchError as e:
                failed += 1
                log.warning("%s", e)
            if i % 50 == 0:
                log.info("đã gọi %d/%d target (%d lời gọi, %d retry)", i, len(targets), f.calls, f.retries)
        return fetched, failed, bad_shape, stopped, f.calls, f.retries


def _recrawl(engine, stats):
    """Sự kiện quyền làm chuỗi close_adj của mã đó sai — kéo lại bằng đường có sẵn của lát 3.

    Không còn nhánh 'bỏ qua ở lượt khởi tạo': `recrawl_codes()` (spec mới, đo bug thật
    2026-09-22) đã đổi sang cửa sổ vài ngày quanh hôm nay thay vì so với watermark, nên tự
    nó chặn số mã ở MỌI lượt — kể cả lượt khởi tạo — không còn nguy cơ trả cả 1.523 mã.

    Vẫn cần TRẦN THỜI GIAN riêng: mỗi mã re-crawl là một lượt `price --backfill` TRỌN LỊCH SỬ
    ~12,5 năm (mã lâu năm tới 53 trang), không phải một lần gọi nhẹ. Số đo thật (kho
    production, tám tuần gần nhất): 8·22·34·23·48·32·41·46 mã MỖI TUẦN có ngày không hưởng
    quyền — mùa cổ tức chạm gần trần `MAX_RECRAWL = 50` ngay trong cửa sổ 3 ngày. Không chặn
    thời gian thì job snapshot hằng ngày (bản thân ~5 phút) có thể biến thành hàng chục phút
    tới hàng giờ, không trần — đúng thứ gặp thật khi lượt `--codes A32,BAB,BVB` kéo theo
    backfill của 8 mã và vượt 120 giây (đo 2026-09-22).

    Cắt giữa chừng AN TOÀN: mã chưa kịp kéo không mất — `recrawl_codes()` dùng cửa sổ ngày
    (không phải con trỏ một lần), nên hai lượt snapshot sau vẫn thấy lại đúng mã đó trong
    cửa sổ 3 ngày; và `etl price --backfill --codes` tự nó idempotent, kéo lại nhiều lần vô
    hại. `price_job.run(max_minutes=...)` đã có sẵn ngân sách thời gian từ lát 3 — chỉ cần
    truyền xuống, không cần dựng cơ chế mới.
    """
    with engine.begin() as conn:
        codes = snapshot_store.recrawl_codes(conn)
    if not codes:
        return
    if len(codes) > MAX_RECRAWL:
        stats["recrawl"] = {"skipped": f"{len(codes)} mã > trần {MAX_RECRAWL}", "codes": codes}
        log.warning("re-crawl bỏ qua: %d mã vượt trần %d", len(codes), MAX_RECRAWL)
        return
    try:
        import etl.price_job
        rc = etl.price_job.run(backfill=True, codes=codes, max_minutes=RECRAWL_MAX_MINUTES)
        stats["recrawl"] = {"codes": codes, "exit": rc}
    except Exception as e:                    # noqa: BLE001 — re-crawl hỏng KHÔNG kéo đổ lượt snapshot
        stats["recrawl"] = {"codes": codes, "error": f"{type(e).__name__}: {e}"}
        log.exception("re-crawl giá thất bại — lượt snapshot vẫn tính là xong")


def run(codes=None, kinds=None, max_minutes=None, get=None, sleep=time.sleep) -> int:
    logging.basicConfig(level=logging.INFO, stream=sys.stderr,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    load_dotenv()
    # Lượt con: --codes hoặc --kinds chỉ phục vụ một phần vũ trụ — KHÔNG được đẩy mốc nước toàn
    # bảng, nếu không mọi sự kiện công bố của phần còn lại nằm dưới mốc mới sẽ mất trigger vĩnh
    # viễn. Tiền lệ: price_job.py đã có đúng khái niệm `subset` này (review, phát hiện #1).
    subset = codes is not None or kinds is not None
    try:
        engine = _engine()
    except RuntimeError as e:
        log.error("%s", e)
        return 2
    run_id = omo_store.open_run(engine, JOB)
    try:
        with engine.begin() as conn:
            watermark = snapshot_store.load_watermark(conn)
            targets = snapshot_store.due_list(conn, watermark, kinds=kinds, codes=codes)
            # Lấy 'mốc nước MỚI' ngay CÙNG giao dịch với due_list, ở T0 — không đọc lại sau khi
            # fetch/re-crawl xong (T1, cách nhau tới 20 phút). Đọc hai lần tạo cửa sổ đua: sự
            # kiện `events_job` chèn đúng lúc đó bị mốc T1 nuốt mất mà không job nào phục vụ
            # (review, phát hiện #3). Giá trị này chỉ THỰC SỰ dùng khi lượt đầy đủ và trót lọt —
            # tính sẵn ở đây, rẻ, và loại bỏ hẳn cửa sổ đua.
            new_wm = snapshot_store.new_watermark(conn)
        log.info("tới hạn: %d target (%d theo sự kiện)", len(targets),
                 sum(1 for t in targets if t.found_by == "event"))

        deadline = time.monotonic() + max_minutes * 60 if max_minutes else None
        fetched, failed, bad_shape, stopped, calls, retries = _fetch_all(targets, get, sleep, deadline)

        run_date = datetime.now(VN).date()
        try:
            with engine.begin() as conn:
                tally, written = snapshot_store.apply(conn, fetched, run_date)
                tally.attempted = len(targets)
                tally.failed, tally.bad_shape = failed, bad_shape
                verdict = snapshot_guard.check(tally)
                if not verdict.ok:
                    raise GuardRefused(verdict)
        except GuardRefused as e:
            snapshot_store.store_refusal_evidence(engine, fetched, run_id, e.verdict)
            omo_store.close_run(engine, run_id, "failed",
                                error="guard refused: " + "; ".join(e.verdict.reasons))
            log.error("snapshot từ chối: %s", e.verdict.reasons)
            return 1

        stats = {"tally": vars(tally), "rows_written": written, "calls": calls,
                 "retries": retries, "stopped_early": stopped, "run_date": run_date.isoformat()}
        if subset:
            stats["subset"] = True             # lượt con không được làm mốc cho lượt toàn tập

        if subset:
            # Lượt con (--codes/--kinds) là hành động thủ công phạm vi hẹp — cùng lý do nó
            # không được đẩy mốc nước (xem push_watermark bên dưới), nó cũng không được châm
            # một lượt backfill giá TRỌN LỊCH SỬ cho những mã ngoài phạm vi người dùng ép chạy.
            # `recrawl_codes()` đọc theo cửa sổ ngày trên TOÀN vũ trụ (không lọc theo `codes`
            # tham số), nên gọi `_recrawl` ở đây từng kéo lại mã hoàn toàn không liên quan tới
            # ý định của lượt con (bug thật đo 2026-09-04: ba lượt --codes liên tiếp đều kéo
            # lại ['RYG', 'TCH'] dù hai mã đó không nằm trong `codes` truyền vào).
            stats["recrawl"] = {"skipped": "lượt con"}
            log.info("re-crawl bỏ qua: lượt con không được châm backfill giá ngoài phạm vi")
        elif stopped:
            # `--max-minutes` là trần cho CẢ LƯỢT (backend/README.md), không phải riêng pha
            # fetch — pha fetch vừa bị cắt vì hết giờ thì đừng châm thêm tới 20 phút re-crawl
            # nữa (review, phát hiện #4).
            stats["recrawl"] = {"skipped": "pha fetch đã bị cắt vì hết --max-minutes"}
            log.info("re-crawl bỏ qua: pha fetch đã dừng vì hết ngân sách thời gian")
        else:
            _recrawl(engine, stats)

        # Watermark chỉ tiến khi KHÔNG mã nào hỏng VÀ đây là lượt ĐẦY ĐỦ: đẩy mốc lên trong lúc
        # còn target chưa phục vụ — hoặc chỉ vì lượt này vốn chỉ phục vụ vài mã/kind — là mất
        # trigger vĩnh viễn cho phần còn lại của sàn (review, phát hiện #1). `bad_shape` cũng
        # phải chặn y như `failed` — target đó cũng CHƯA được apply() ghi vào snapshot_check
        # (review vòng 1, phát hiện #1: brief chỉ cảnh báo đường `failed`, bỏ sót `bad_shape`).
        push_watermark = not subset and failed == 0 and bad_shape == 0 and not stopped
        if push_watermark:
            stats["watermark"] = new_wm.isoformat()
        elif not subset:
            stats["watermark"] = watermark.isoformat()
            stats["watermark_held"] = True

        # close_run TRƯỚC, upsert_domain_state SAU — khuôn events_job.py/price_job.py, đúng
        # thứ tự docstring `omo_store.close_run` chốt: cột `stats` dùng `coalesce`, nên nếu bước
        # sau ném lỗi thì bằng chứng của lượt đã ghi xong vẫn còn, chỉ đổi status (review, phát
        # hiện #8 — trước fix, gọi ngược lại làm mất sạch stats khi upsert_domain_state hỏng).
        omo_store.close_run(engine, run_id, "success", stats)
        if push_watermark:
            snapshot_store.upsert_domain_state(engine, new_wm.isoformat())

        log.info("snapshot xong: %s", stats)
        return 0
    except Exception as e:                    # noqa: BLE001 — job biên ngoài: mọi lỗi vào etl_run
        omo_store.close_run(engine, run_id, "failed", error=f"{type(e).__name__}: {e}")
        log.exception("snapshot thất bại")
        return 2
    finally:
        engine.dispose()
