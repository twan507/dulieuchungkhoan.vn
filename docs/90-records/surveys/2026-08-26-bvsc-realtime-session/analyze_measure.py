"""Phan tich frame tho socket realtime BVSC phien chieu 2026-08-26.
Doc streaming (gzip.open, tung dong), khong nap ca file vao RAM.
Chay: cd backend && PYTHONIOENCODING=utf-8 uv run python <script>
"""
from __future__ import annotations

import gzip
import json
import sys
import time
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path

sys.path.insert(0, r"D:\twan_projects\dulieuchungkhoan.vn\backend")
from ingester.eio import parse_packet, Event, Open, Control, Ack  # noqa: E402

DATA_DIR = Path(r"D:\twan_projects\dlck-runtime\measure\20260826")
FILES = sorted(DATA_DIR.glob("frames-20260826-*.jsonl.gz"))

DERIV_SYMBOLS = ['41B5G9000', '41B5GC000', '41B5H3000', '41BAG9000', '41BAGC000',
                 '41BAH3000', '41I1G9000', '41I1GA000', '41I1GC000', '41I1H3000',
                 '41I2G9000', '41I2GA000', '41I2GC000', '41I2H3000']
DERIV_SET = set(DERIV_SYMBOLS)

DOC_KEYS_T = {"SB", "TD", "FT", "FMP", "FV", "FCV", "LC", "SM", "AVO", "AVA"}
DOC_KEYS_O = {"SB", "TOP", "id", "ACT", "BP", "BQ", "SP", "SQ", "CBV", "CSV", "t"}
DOC_KEYS_I = {"SB", "EX", "t", "B1", "B2", "B3", "V1", "V2", "V3", "S1", "S2", "S3",
              "U1", "U2", "U3", "TB", "TO", "CP", "CH", "CHP", "AP", "HI", "CV",
              "P1", "P2", "TT", "TV", "FB", "FS", "FR", "PMP", "PMQ", "PTQ", "PTV"}
DOC_KEYS_IDX = {"MC", "MI", "ICH", "IPC", "IT", "TD", "TV", "TVA", "ADV", "DE", "NC",
                "AV", "DV", "NCV", "NOC", "PTT", "PTV", "t"}

NUMERIC_FIELDS_T = ["FMP", "FV", "FCV", "SM", "AVO", "AVA"]
NUMERIC_FIELDS_O = ["BP", "BQ", "SP", "SQ", "CBV", "CSV", "TOP", "t"]
NUMERIC_FIELDS_I = ["t", "B1", "B2", "B3", "V1", "V2", "V3", "S1", "S2", "S3",
                     "U1", "U2", "U3", "TB", "TO", "CP", "CH", "CHP", "AP", "HI", "CV",
                     "P1", "P2", "TT", "TV", "FB", "FS", "FR", "PMP", "PMQ", "PTQ", "PTV"]
NUMERIC_FIELDS_IDX = ["MI", "ICH", "IPC", "TV", "TVA", "ADV", "DE", "NC",
                       "AV", "DV", "NCV", "NOC", "PTT", "PTV", "t"]
NUMERIC_FIELDS = {"t": NUMERIC_FIELDS_T, "o": NUMERIC_FIELDS_O,
                   "i": NUMERIC_FIELDS_I, "idx": NUMERIC_FIELDS_IDX}

VN_OFFSET_S = 7 * 3600


def minute_bucket(epoch_ms: int) -> str:
    local = time.gmtime(epoch_ms / 1000 + VN_OFFSET_S)
    return f"{local.tm_hour:02d}:{local.tm_min:02d}"


def try_decimal(v):
    if v is None:
        return False
    try:
        Decimal(str(v))
        return True
    except (InvalidOperation, ValueError, TypeError):
        return False


def main():
    # -------- state --------
    frame_counts = Counter()          # event name -> so frame (packet)
    ditem_counts = Counter()          # event name -> so dong d-item
    len_d_dist = defaultdict(Counter)  # event -> Counter(len(d))
    other_control = Counter()          # Open/Control/Ack/None counts

    all_keys = {"t": set(), "o": set(), "i": set(), "idx": set()}
    total_keys_i = set()

    # A. SM
    sm_dup_pair_count = 0            # so cap (SB,TD,FT,SM) trung > 1 lan (dem THEM moi lan lap, tru lan dau)
    smsecond_counts = Counter()      # (SB,TD,FT,SM) -> count
    sm_symbol_seen = defaultdict(set)   # SB -> set(SM) ca phien
    sm_symbol_total = Counter()          # SB -> tong so ban ghi t
    sm_prev_by_symbol = {}               # SB -> SM truoc do (int)
    sm_decrease_count = 0
    sm_global_min = None
    sm_global_max = None
    sm_global_prev = None
    sm_global_decrease_count = 0
    trade_symbol_total = Counter()       # SB -> so ban ghi t (dung de chon top3 thanh khoan)
    symbol_second_trade_count = Counter()  # (SB,TD,FT) -> count lenh khop trong giay do

    # B. derivatives
    deriv_event_counts = defaultdict(Counter)  # SB(deriv) -> Counter(event_name)
    deriv_samples = {}   # (event,SB) -> sample dict (1 mau moi to hop)
    all_event_names = Counter()   # TAT CA ten event thuc nhan duoc (tu Event pkt)

    # C. pth
    pth_frame_count = 0
    pth_samples = []

    # D. gio day du lieu
    minute_range = {}   # event -> [min_minute, max_minute]

    # E15. so gia tri khong parse duoc Decimal, theo (event, field)
    numeric_fail = Counter()
    numeric_fail_samples = defaultdict(list)

    # E14. CV vs P1
    cv_p1_both = 0
    cv_p1_diff = 0

    # F. tai
    minute_total = Counter()   # phut(VN) -> tong so d-item (tat ca event)
    idx_minute_counts = Counter()   # phut(VN) -> so frame idx (rieng, cho D10)

    n_lines = 0
    n_bad_json = 0
    n_event_pkt = 0
    n_no_d = 0

    t0 = time.time()
    for fp in FILES:
        with gzip.open(fp, "rt", encoding="utf-8") as f:
            for line in f:
                n_lines += 1
                if n_lines % 500000 == 0:
                    print(f"... {n_lines} dong, {time.time()-t0:.1f}s", file=sys.stderr)
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    n_bad_json += 1
                    continue
                r_ms = rec.get("r")
                raw = rec.get("p", "")
                pkt = parse_packet(raw)
                if not isinstance(pkt, Event):
                    other_control[type(pkt).__name__] += 1
                    continue
                n_event_pkt += 1
                name = pkt.name
                all_event_names[name] += 1
                frame_counts[name] += 1
                payload = pkt.payload or {}
                d = payload.get("d")
                if not isinstance(d, list):
                    n_no_d += 1
                    continue
                len_d_dist[name][len(d)] += 1

                minute = minute_bucket(r_ms) if r_ms else None
                if minute:
                    if name not in minute_range:
                        minute_range[name] = [minute, minute]
                    else:
                        if minute < minute_range[name][0]:
                            minute_range[name][0] = minute
                        if minute > minute_range[name][1]:
                            minute_range[name][1] = minute
                    minute_total[minute] += len(d)
                    if name == "idx":
                        idx_minute_counts[minute] += 1

                # pth
                if name == "pth":
                    pth_frame_count += len(d)
                    if len(pth_samples) < 5:
                        pth_samples.append(d[:2])

                for item in d:
                    if not isinstance(item, dict):
                        continue
                    sb = item.get("SB")

                    # derivatives tracking - applies regardless of event name
                    if sb in DERIV_SET:
                        deriv_event_counts[sb][name] += 1
                        key = (name, sb)
                        if key not in deriv_samples:
                            deriv_samples[key] = item

                    if name == "t":
                        all_keys["t"] |= set(item.keys())
                        # numeric parse check
                        for fld in NUMERIC_FIELDS_T:
                            if fld in item:
                                if not try_decimal(item[fld]):
                                    numeric_fail[("t", fld)] += 1
                                    if len(numeric_fail_samples[("t", fld)]) < 5:
                                        numeric_fail_samples[("t", fld)].append(repr(item[fld]))
                        if sb is not None:
                            trade_symbol_total[sb] += 1
                            sm_raw = item.get("SM")
                            td = item.get("TD")
                            ft = item.get("FT")
                            try:
                                sm_val = int(sm_raw)
                            except (TypeError, ValueError):
                                sm_val = None
                            if sm_val is not None:
                                if sm_global_min is None or sm_val < sm_global_min:
                                    sm_global_min = sm_val
                                if sm_global_max is None or sm_val > sm_global_max:
                                    sm_global_max = sm_val
                                if sm_global_prev is not None and sm_val < sm_global_prev:
                                    sm_global_decrease_count += 1
                                sm_global_prev = sm_val

                                sm_symbol_seen[sb].add(sm_val)
                                sm_symbol_total[sb] += 1
                                prev = sm_prev_by_symbol.get(sb)
                                if prev is not None and sm_val < prev:
                                    sm_decrease_count += 1
                                sm_prev_by_symbol[sb] = sm_val

                                if td is not None and ft is not None:
                                    k = (sb, td, ft, sm_val)
                                    smsecond_counts[k] += 1
                                    ksec = (sb, td, ft)
                                    symbol_second_trade_count[ksec] += 1

                    elif name == "o":
                        all_keys["o"] |= set(item.keys())
                        for fld in NUMERIC_FIELDS_O:
                            if fld in item:
                                if not try_decimal(item[fld]):
                                    numeric_fail[("o", fld)] += 1
                                    if len(numeric_fail_samples[("o", fld)]) < 5:
                                        numeric_fail_samples[("o", fld)].append(repr(item[fld]))

                    elif name == "i":
                        all_keys["i"] |= set(item.keys())
                        total_keys_i |= set(item.keys())
                        for fld in NUMERIC_FIELDS_I:
                            if fld in item:
                                if not try_decimal(item[fld]):
                                    numeric_fail[("i", fld)] += 1
                                    if len(numeric_fail_samples[("i", fld)]) < 5:
                                        numeric_fail_samples[("i", fld)].append(repr(item[fld]))
                        if "CV" in item and "P1" in item:
                            cv_p1_both += 1
                            if str(item["CV"]) != str(item["P1"]):
                                cv_p1_diff += 1

                    elif name == "idx":
                        all_keys["idx"] |= set(item.keys())
                        for fld in NUMERIC_FIELDS_IDX:
                            if fld in item:
                                if not try_decimal(item[fld]):
                                    numeric_fail[("idx", fld)] += 1
                                    if len(numeric_fail_samples[("idx", fld)]) < 5:
                                        numeric_fail_samples[("idx", fld)].append(repr(item[fld]))

    elapsed = time.time() - t0
    print(f"\n=== XONG doc {n_lines} dong trong {elapsed:.1f}s ===", file=sys.stderr)

    out = {}
    out["n_lines"] = n_lines
    out["n_bad_json"] = n_bad_json
    out["n_event_pkt"] = n_event_pkt
    out["n_no_d"] = n_no_d
    out["other_control"] = dict(other_control)
    out["all_event_names"] = dict(all_event_names)
    out["frame_counts"] = dict(frame_counts)
    out["ditem_counts"] = {k: sum(c * n for c, n in v.items()) for k, v in len_d_dist.items()}
    out["len_d_dist"] = {k: dict(v.most_common(10)) for k, v in len_d_dist.items()}

    # A1
    dup_groups = [k for k, c in smsecond_counts.items() if c > 1]
    out["A1_total_sb_td_ft_groups_with_sm"] = len(smsecond_counts)
    out["A1_dup_sb_td_ft_sm_count"] = len(dup_groups)
    out["A1_dup_examples"] = dup_groups[:10]

    # A2
    dup_symbols = [sb for sb, s in sm_symbol_seen.items() if len(s) < sm_symbol_total[sb]]
    out["A2_symbols_total"] = len(sm_symbol_seen)
    out["A2_symbols_with_repeated_sm"] = len(dup_symbols)
    out["A2_examples"] = dup_symbols[:10]

    # A3
    out["A3_sm_decrease_count_per_symbol"] = sm_decrease_count
    out["A3_total_transitions"] = sum(sm_symbol_total.values()) - len(sm_symbol_total)

    # A4
    out["A4_sm_global_min"] = sm_global_min
    out["A4_sm_global_max"] = sm_global_max
    out["A4_sm_global_decrease_count"] = sm_global_decrease_count
    top3 = [sb for sb, _ in trade_symbol_total.most_common(3)]
    out["A4_top3_symbols"] = top3
    top3_ranges = {}
    for sb in top3:
        vals = sm_symbol_seen[sb]
        if vals:
            top3_ranges[sb] = {"min": min(vals), "max": max(vals), "count": len(vals)}
    out["A4_top3_sm_ranges"] = top3_ranges

    # A5
    secs_with_ge2 = sum(1 for c in symbol_second_trade_count.values() if c >= 2)
    out["A5_total_sb_second_groups"] = len(symbol_second_trade_count)
    out["A5_secs_with_ge2_trades"] = secs_with_ge2
    out["A5_pct"] = (secs_with_ge2 / len(symbol_second_trade_count) * 100) if symbol_second_trade_count else None

    # B
    out["B_deriv_symbols"] = DERIV_SYMBOLS
    out["B_deriv_event_counts"] = {sb: dict(c) for sb, c in deriv_event_counts.items()}
    out["B_deriv_samples"] = {f"{ev}|{sb}": item for (ev, sb), item in list(deriv_samples.items())}

    # C
    out["C_pth_frame_count"] = pth_frame_count
    out["C_pth_samples"] = pth_samples

    # D
    out["D_minute_range"] = minute_range

    # E11-13
    out["E11_t_extra_keys"] = sorted(all_keys["t"] - DOC_KEYS_T)
    out["E11_t_missing_keys"] = sorted(DOC_KEYS_T - all_keys["t"])
    out["E11_o_extra_keys"] = sorted(all_keys["o"] - DOC_KEYS_O)
    out["E11_o_missing_keys"] = sorted(DOC_KEYS_O - all_keys["o"])
    out["E12_i_total_distinct_keys"] = len(total_keys_i)
    out["E12_i_extra_keys"] = sorted(total_keys_i - DOC_KEYS_I)
    out["E12_i_missing_keys"] = sorted(DOC_KEYS_I - total_keys_i)
    out["E13_idx_extra_keys"] = sorted(all_keys["idx"] - DOC_KEYS_IDX)
    out["E13_idx_missing_keys"] = sorted(DOC_KEYS_IDX - all_keys["idx"])

    # E14
    out["E14_cv_p1_both_present"] = cv_p1_both
    out["E14_cv_p1_diff"] = cv_p1_diff

    # E15
    out["E15_numeric_fail"] = {f"{ev}.{fld}": c for (ev, fld), c in numeric_fail.items()}
    out["E15_numeric_fail_samples"] = {f"{ev}.{fld}": s for (ev, fld), s in numeric_fail_samples.items()}

    # F
    out["F_minute_total_stats"] = {
        "n_minutes": len(minute_total),
        "sum_rows": sum(minute_total.values()),
        "max_minute_rows": minute_total.most_common(1),
        "avg_rows_per_minute": (sum(minute_total.values()) / len(minute_total)) if minute_total else None,
    }
    out["F_minute_total_top10"] = minute_total.most_common(10)
    out["D10_idx_minute_counts_sorted"] = sorted(idx_minute_counts.items())

    out_path = Path(__file__).with_name("result.json")
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"Ghi ket qua vao {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
