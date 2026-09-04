"""Đếm ĐỘC LẬP số dòng `financial_statement` mà một payload BCTC phải sinh ra — expected cho AC2/§6.

Không import gì từ `backend/etl`: đây là phép đếm thứ hai, viết riêng, để test không tautology (§4.5.3).
Luật đếm = spec §5.3: bỏ `yearReport`/`quarterReport`, bỏ 8 khoá phi chỉ tiêu, bỏ ô null; mọi ô còn lại là một dòng.

Dùng:  python count_rows.py <file.json> [<file.json> ...]
       (mỗi file là một response của GetBalanceSheet / GetIncomeStatement / GetCashFlow)
Kết quả đã ghi vào spec: mẫu A32 trong khảo sát 2026-09-04 → 1.749 + 980 + 916 = 3.645 dòng.
"""
import json
import sys

NON_METRIC = {"organCode", "ebit", "ebitDa", "operating",
              "otherAssetBank", "otherAssetNonBank", "otherLiabilties", "rtq29"}


def count(path: str) -> tuple[int, int]:
    """(số dòng sẽ ghi, số ô non-null của 8 khoá phi chỉ tiêu bị bỏ)."""
    d = json.load(open(path, encoding="utf-8"))
    item = d["items"][0]
    rows = dropped = 0
    for rec in item["quarterly"] + item["yearly"]:
        for k, v in rec.items():
            if k in ("yearReport", "quarterReport") or v is None:
                continue
            if k in NON_METRIC:
                dropped += 1
            else:
                rows += 1
    return rows, dropped


if __name__ == "__main__":
    total = 0
    for p in sys.argv[1:]:
        r, dr = count(p)
        total += r
        print(f"{p}: {r} dòng (bỏ {dr} ô phi chỉ tiêu)")
    print("tổng:", total)
