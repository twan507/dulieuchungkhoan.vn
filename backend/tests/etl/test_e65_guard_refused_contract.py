"""Sáu họ job dùng CHUNG một lớp `GuardRefused`, không mỗi họ một bản.

🔴 Vì sao file này ra đời (quyết định §4.8 ngày 2026-09-08, hồ sơ
`docs/90-records/plans/2026-09-07-audit-drift-cleanup/decision-unify-jobs-2026-09-08.md`):
tới lúc đó `class GuardRefused` được định nghĩa **6 lần** trong `etl/*_job.py`, ở **2 hình
dạng khác nhau** — bốn bản giữ `.verdict` (`events` `fundamentals` `price` `snapshot`) và hai
bản giữ `.reasons` (`refdata` `screener`). Sáu lớp trùng tên nhưng KHÁC nhau về danh tính:
`except refdata_job.GuardRefused` không bắt được thứ `screener_job` ném ra, dù mắt đọc mã
tưởng là một. Chưa ai bị cắn vì mỗi job tự bắt trong chính nó — nhưng lát 13 gộp lịch vào một
tiến trình, lúc đó một chỗ bắt chung là chuyện tự nhiên sẽ có người viết.

Hai vế, cố ý tách:
  1. **Danh tính** — sáu module phải trỏ về CÙNG MỘT object lớp. Đây là vế duy nhất chặn
     được bug ở trên; kiểm tĩnh bằng grep không đủ vì grep chỉ thấy chữ, không thấy danh tính.
  2. **Cách viết** — không `*_job.py` nào được tự định nghĩa lại. Vế này canh cho họ job thứ
     bảy: nó có thể tự viết một lớp trùng tên mà vế 1 vẫn xanh (vì vế 1 chỉ soi 6 module đã
     liệt kê), nên phải quét cả thư mục.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from etl import (events_job, fundamentals_job, guard_common, price_job, refdata_job,
                 screener_job, snapshot_job)

ETL = Path(__file__).resolve().parents[2] / "etl"
JOB_FILES = sorted(p for p in ETL.glob("*_job.py"))
HO_CO_GUARD = {"events": events_job, "fundamentals": fundamentals_job, "price": price_job,
               "refdata": refdata_job, "screener": screener_job, "snapshot": snapshot_job}


def test_sau_ho_job_tro_ve_cung_mot_lop():
    lop = {ten: mod.GuardRefused for ten, mod in HO_CO_GUARD.items()}
    rieng = {ten: c for ten, c in lop.items() if c is not guard_common.GuardRefused}
    assert not rieng, (
        "họ job giữ lớp GuardRefused riêng — `except guard_common.GuardRefused` sẽ KHÔNG bắt "
        f"được thứ chúng ném ra: {sorted(rieng)}")


def test_khong_job_nao_tu_dinh_nghia_lai():
    """Quét cả thư mục, không chỉ 6 module trên — canh cho họ job thứ bảy."""
    tu_dinh_nghia = [f"{p.name}:{src[:m.start()].count(chr(10)) + 1}"
                     for p in JOB_FILES
                     for src in [p.read_text(encoding="utf-8")]
                     for m in re.finditer(r"^class GuardRefused\b", src, re.M)]
    assert not tu_dinh_nghia, (
        "job tự định nghĩa GuardRefused thay vì import từ etl.guard_common:\n  "
        + "\n  ".join(tu_dinh_nghia))


def test_phep_kiem_nay_that_su_soi_du_ho_job():
    """Canh chính hai phép kiểm trên — cùng lý do đã ghi ở `test_e64`: một phép kiểm quét vào
    tập rỗng thì vẫn xanh, và đó là loại phép kiểm tệ nhất."""
    ten = {p.name for p in JOB_FILES}
    assert len(JOB_FILES) >= 11, f"chỉ thấy {len(JOB_FILES)} file *_job.py — nghi phép kiểm hụt"
    for ho in HO_CO_GUARD:
        assert f"{ho}_job.py" in ten
        assert "GuardRefused" in (ETL / f"{ho}_job.py").read_text(encoding="utf-8"), (
            f"{ho}_job.py không còn nhắc GuardRefused — họ này bỏ chốt chặn, hay phép kiểm lạc?")


class _Verdict:
    """Khuôn tối thiểu mà cả 8 guard đều có: `ok` + `reasons` (kiểm 2026-09-08)."""

    def __init__(self, reasons):
        self.ok = False
        self.reasons = tuple(reasons)


def test_mang_ca_verdict_lan_reasons_va_thong_diep_la_reasons_ghep():
    v = _Verdict(["sụt 3/1545 mã", "mốc nước lùi"])
    e = guard_common.GuardRefused(v)
    assert e.verdict is v                                    # 4 họ cũ đọc `.verdict`
    assert e.reasons == ["sụt 3/1545 mã", "mốc nước lùi"]    # 2 họ cũ đọc `.reasons`, và là list
    assert str(e) == "sụt 3/1545 mã; mốc nước lùi"           # literal, không ghép lại bằng code


def test_reasons_rong_van_dung_duoc():
    """Ca biên: guard từ chối mà không nêu lý do nào (chưa họ nào làm thế, nhưng `reasons` có
    `default_factory=list` nên hình dạng này hợp lệ) — không được nổ, và thông điệp là rỗng."""
    e = guard_common.GuardRefused(_Verdict([]))
    assert e.reasons == [] and str(e) == ""


def test_reasons_la_ban_sao_khong_phai_tham_chieu():
    """Đổi `reasons` của exception không được vọng ngược vào verdict — verdict là bằng chứng
    ghi xuống `staging`, sửa nhầm nó là làm hỏng bằng chứng."""
    v = _Verdict(["a"])
    e = guard_common.GuardRefused(v)
    e.reasons.append("b")
    assert v.reasons == ("a",)


def test_bat_duoc_bang_except_Exception_nhu_truoc():
    with pytest.raises(guard_common.GuardRefused):
        raise guard_common.GuardRefused(_Verdict(["x"]))
