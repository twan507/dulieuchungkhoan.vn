"""Mọi job ETL phải dựng engine với `pool_pre_ping=True`.

Lý do đã trả giá, ghi ở `price_job` (2026-09-04): máy dev ngủ theo lịch 02:00 giữa lượt, ba
container sống qua giấc ngủ nhưng **kết nối trong pool thì chết**, lượt kế tiếp lấy ra một
connection hỏng. `pool_pre_ping` là một round-trip `SELECT 1` trước khi giao connection —
rẻ, không tác dụng phụ đã biết.

🔴 Vì sao file này ra đời (rà chuẩn hoá 2026-09-07): 11/15 họ bật, 4 họ (`omo` `refdata`
`screener` `events`) không bật **và không ai ghi lý do**. Bốn họ đó chạy ngắn nên rủi ro thấp
hơn — nhưng đó là suy luận, không phải điều repo viết ra, và lát 12/13 sắp đổi cách chạy
(container `restart: unless-stopped`, bảng lịch gộp cửa sổ) nên tiền đề "chạy ngắn" hết chắc.

Kiểm TĨNH trên mã nguồn, không dựng engine thật: đây là hợp đồng về CÁCH VIẾT, và mọi
`create_engine` đều nằm trong hàm nên không quan sát được nếu không chạy job thật.
"""
from __future__ import annotations

import re
from pathlib import Path

ETL = Path(__file__).resolve().parents[2] / "etl"

# `series_job.py` phục vụ 5 họ quốc tế (fred/fx/lbma/yahoo/binance) nên tính là một đường.
JOB_FILES = sorted(p for p in ETL.glob("*_job.py"))


def test_moi_job_deu_dung_pool_pre_ping():
    thieu = []
    for p in JOB_FILES:
        src = p.read_text(encoding="utf-8")
        for m in re.finditer(r"create_engine\(([^)]*)\)", src):
            if "pool_pre_ping=True" not in m.group(1):
                dong = src[: m.start()].count("\n") + 1
                thieu.append(f"{p.name}:{dong} -> create_engine({m.group(1)})")
    assert not thieu, (
        "job dựng engine không có pool_pre_ping=True:\n  " + "\n  ".join(thieu))


def test_phep_kiem_nay_that_su_soi_du_ho_job():
    """Canh chính phép kiểm trên: nếu ai đó đổi tên file job, `JOB_FILES` rỗng dần mà test
    vẫn xanh — một phép kiểm không còn soi gì vẫn xanh là phép kiểm tệ nhất."""
    ten = {p.name for p in JOB_FILES}
    assert len(JOB_FILES) >= 11, f"chỉ thấy {len(JOB_FILES)} file *_job.py — nghi phép kiểm hụt"
    for bat_buoc in ("omo_job.py", "refdata_job.py", "screener_job.py", "events_job.py",
                     "price_job.py", "series_job.py", "news_job.py"):
        assert bat_buoc in ten, f"thiếu {bat_buoc} trong phạm vi kiểm"
    assert sum("create_engine(" in p.read_text(encoding="utf-8") for p in JOB_FILES) >= 10
