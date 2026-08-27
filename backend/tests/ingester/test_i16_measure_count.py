"""Bộ đếm d[] — spec spill §11; seam 18, 19 (golden giải tay, chống tautological)."""
import gzip
import json

from ingester.measure_count import count_measure

T_REC = {"TD": "10/08/2026", "FT": "13:08:56", "SB": "ACV", "FV": "100", "LC": "S",
         "FMP": "42100.0", "FCV": "1000.0", "SM": "74027", "AVO": "590000",
         "AVA": "24983210000.0"}


def _frame(rec=T_REC) -> str:
    return "42" + json.dumps(["t", {"a": "i", "d": [rec]}])


def _write(day_dir, name, lines, gz=False):
    day_dir.mkdir(exist_ok=True)
    p = day_dir / name
    data = "".join(json.dumps(x) + "\n" for x in lines)
    if gz:
        with gzip.open(p, "wt", encoding="utf-8") as fh:
            fh.write(data)
    else:
        p.write_text(data, encoding="utf-8")


def test_count_hand_solved_with_dedup_by_r_clock(tmp_path):
    d = tmp_path / "20260810"
    base = 1_786_342_136_000
    _write(d, "frames-20260810-13.jsonl.gz", [
        {"r": base, "p": _frame()},                        # đếm: 1
        {"r": base + 1_000, "p": _frame()},                # trùng nội dung, cách 1s < 600s → dup
        {"r": base + 700_000, "p": _frame()},              # cách 700s > cửa sổ 600s → đếm: 2
        {"r": base + 700_500, "p": "42" + json.dumps(      # SM khác → nội dung khác → đếm: 3
            ["t", {"a": "i", "d": [{**T_REC, "SM": "74028"}]}])},
    ], gz=True)
    # file TRẦN chưa gzip cũng phải được đọc (spec §11.2)
    _write(d, "frames-20260810-14.jsonl", [
        {"r": base + 800_000, "p": _frame({**T_REC, "SM": "74029"})},   # đếm: 4
    ])
    counts, metrics = count_measure(d, t_from_ms=0, t_to_ms=2 * base)
    # GIẢI TAY: 5 frame 't' → 1 dup (theo đồng hồ r) → 4 dòng trade
    assert counts["trade"] == 4
    assert metrics.counters["dup_dropped"] == 1


def test_window_cut_excludes_frames_outside(tmp_path):
    d = tmp_path / "20260810"
    base = 1_786_342_136_000
    _write(d, "frames-20260810-13.jsonl", [
        {"r": base, "p": _frame()},
        {"r": base + 5_000, "p": _frame({**T_REC, "SM": "74030"})},
    ])
    counts, _ = count_measure(d, t_from_ms=base, t_to_ms=base + 1_000)
    assert counts["trade"] == 1                            # frame thứ hai ngoài cửa sổ — seam 18
