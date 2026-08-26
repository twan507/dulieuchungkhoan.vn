"""Pass bo sung: kiem SM theo SAN (EX) de lam ro A4 - bo dem toan so hay theo san.
Lay EX cho tung SB tu event 'i' (co truong EX), roi gom SM cua event 't' theo san.
Cung lay mau field la (E12/E13) va vai vi du gia tri rong (E15).
"""
from __future__ import annotations
import gzip, json, sys, time
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, r"D:\twan_projects\dulieuchungkhoan.vn\backend")
from ingester.eio import parse_packet, Event

DATA_DIR = Path(r"D:\twan_projects\dlck-runtime\measure\20260826")
FILES = sorted(DATA_DIR.glob("frames-20260826-*.jsonl.gz"))

sb_to_ex = {}
sm_by_floor = defaultdict(list)  # EX -> list of (sb, sm) samples (chi giu min/max/count, khong list day)
floor_stats = defaultdict(lambda: {"min": None, "max": None, "count": 0, "symbols": set()})

# mau cho field la
i_extra_samples = {"LO": None, "OP": None, "TSI": None}
idx_extra_samples = {"IC": None, "MS": None, "NOF": None}

t0 = time.time()
n = 0
for fp in FILES:
    with gzip.open(fp, "rt", encoding="utf-8") as f:
        for line in f:
            n += 1
            rec = json.loads(line)
            pkt = parse_packet(rec.get("p", ""))
            if not isinstance(pkt, Event):
                continue
            d = (pkt.payload or {}).get("d") or []
            if pkt.name == "i":
                for item in d:
                    sb = item.get("SB")
                    ex = item.get("EX")
                    if sb and ex:
                        sb_to_ex[sb] = ex
                    for k in ("LO", "OP", "TSI"):
                        if k in item and i_extra_samples[k] is None:
                            i_extra_samples[k] = dict(item)
            elif pkt.name == "idx":
                for item in d:
                    for k in ("IC", "MS", "NOF"):
                        if k in item and idx_extra_samples[k] is None:
                            idx_extra_samples[k] = dict(item)
            elif pkt.name == "t":
                for item in d:
                    sb = item.get("SB")
                    sm_raw = item.get("SM")
                    try:
                        sm = int(sm_raw)
                    except (TypeError, ValueError):
                        continue
                    ex = sb_to_ex.get(sb, "UNKNOWN")
                    fs = floor_stats[ex]
                    if fs["min"] is None or sm < fs["min"]:
                        fs["min"] = sm
                    if fs["max"] is None or sm > fs["max"]:
                        fs["max"] = sm
                    fs["count"] += 1
                    fs["symbols"].add(sb)

print(f"doc {n} dong trong {time.time()-t0:.1f}s", file=sys.stderr)

out = {}
out["floor_stats"] = {ex: {"min": v["min"], "max": v["max"], "count": v["count"],
                            "n_symbols": len(v["symbols"])}
                       for ex, v in floor_stats.items()}
out["i_extra_samples"] = i_extra_samples
out["idx_extra_samples"] = idx_extra_samples
# EX chua biet cho cac sb khong xuat hien trong event i (vd derivative dung XHNF - da co)
unknown_syms = floor_stats.get("UNKNOWN", {}).get("symbols")
out["unknown_ex_symbols_sample"] = sorted(unknown_syms)[:20] if unknown_syms else []

out_path = Path(__file__).with_name("result_sm_floor.json")
out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
print("done", out_path, file=sys.stderr)
