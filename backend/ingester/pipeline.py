"""Đường xử lý MỘT bản ghi — nguồn sự thật CHUNG cho mode `run` (`make_on_packet`
trong main.py) VÀ bộ đếm `d[]` offline (`measure_count.count_measure`), spec spill
§11: không dựng hai bộ luật song song cho cùng một phép biến đổi.

`process_record` = đúng thân vòng `for record ...` cũ của `make_on_packet`: dedup →
symbol → stamp → normalize, kèm metric `dup_dropped`/`no_symbol_dropped`/
`normalize_error` + log warning khi normalize lỗi. Phần RIÊNG của từng chế độ chạy
(đếm frame, gate `is_leader`, ghi ClickHouse/Redis...) ở NGOÀI hàm này — đó là mối
quan tâm của mode chạy, không phải của phép biến đổi một bản ghi.
"""
from __future__ import annotations

import logging

from ingester.dedup import FrameDedup, Stamper, frame_key
from ingester.normalize import Metrics, Normalized, NormalizeError, normalize, symbol_of

log = logging.getLogger("ingester.pipeline")


def process_record(event: str, record: dict, now: float, dedup: FrameDedup,
                   stamper: Stamper, metrics: Metrics) -> Normalized | None:
    """dedup.seen → symbol_of → stamper.stamp → normalize. `None` nếu bản ghi bị bỏ
    (trùng lặp, không có mã, hoặc frame hỏng tất định — spec §5.8 đường poison)."""
    if dedup.seen(frame_key(event, record), now):
        metrics.inc("dup_dropped")
        return None
    symbol = symbol_of(event, record)
    if symbol is None:
        metrics.inc("no_symbol_dropped")
        return None
    stamped_ms = stamper.stamp(symbol, int(now * 1000))
    try:
        return normalize(event, record, stamped_ms, metrics)
    except NormalizeError as e:
        log.warning("normalize lỗi %s %s: %r", event, symbol, e)
        metrics.inc("normalize_error")
        return None
