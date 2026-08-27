"""Bộ đếm `d[]` — spec spill §11: replay bản đo thô qua ĐÚNG `process_record` mà mode
`run` dùng (dry-run, không đụng DB) để tính số dòng KỲ VỌNG mỗi bảng, đối chứng bằng
số với kho ClickHouse thật.

`count_measure` duyệt các file `frames-*.jsonl[.gz]` (measure.py) trong một thư mục đo,
lọc theo cửa sổ `[t_from_ms, t_to_ms]` trên trường `"r"` — mốc `received_at` lúc ghi đo
(§11.1), CÙNG họ đồng hồ với cột `received_at` trên ClickHouse dùng khi đối chứng
(§11.3: so `received_at`, KHÔNG so `ts`). Với mỗi frame còn lại: `eio.parse_packet` →
chỉ giữ `Event` thuộc 5 topic có normalize → `records_of` bóc vỏ sails.io → chạy
`process_record` với `now = r/1000` — đồng hồ CỦA FRAME, không phải đồng hồ máy chạy
công cụ, để kết quả tái lập được bất kể chạy lúc nào.
"""
from __future__ import annotations

import gzip
import json
from pathlib import Path

from ingester import eio
from ingester.dedup import FrameDedup, Stamper
from ingester.main import EVENTS
from ingester.normalize import Metrics, records_of
from ingester.pipeline import process_record


def _lines_of(path: Path):
    opener = gzip.open if path.name.endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield line


def count_measure(day_dir: Path, t_from_ms: int, t_to_ms: int) -> tuple[dict[str, int], Metrics]:
    dedup = FrameDedup()
    stamper = Stamper()
    metrics = Metrics()
    counts: dict[str, int] = {}
    for path in sorted(Path(day_dir).glob("frames-*.jsonl*")):
        for line in _lines_of(path):
            entry = json.loads(line)
            r = entry["r"]
            if not (t_from_ms <= r <= t_to_ms):
                continue
            pkt = eio.parse_packet(entry["p"])
            if not isinstance(pkt, eio.Event) or pkt.name not in EVENTS:
                continue
            event = pkt.name
            now = r / 1000.0
            for record in records_of(pkt.payload):
                n = process_record(event, record, now, dedup, stamper, metrics)
                if n is not None:
                    counts[n.table] = counts.get(n.table, 0) + 1
    return counts, metrics
