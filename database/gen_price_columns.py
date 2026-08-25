"""Sinh đoạn DDL cột cho market.price_daily từ market-field-selection.json.

Luật chọn (chốt trong plan, khớp architecture §3.4 'giá + dẫn xuất giá — nguồn chuẩn BVSC'):
keep == true AND nguon_chuan == 'BVSC'. Mọi cột kiểu numeric (trường giá/khối lượng);
5 cột spec nêu đích danh (close_adj/close_raw/open_value/highest_value/lowest_value) đã có
tay trong DDL — generator BỎ QUA code trùng sau khi snake_case.
"""
import json
import pathlib
import re

HAND_WRITTEN = {"close_adj", "close_raw", "open_value", "highest_value", "lowest_value"}
# camelCase → snake_case; chuỗi đã ALL_CAPS/underscore giữ nguyên rồi lower
# (bẫy thật: 'PRIOR_PRICE' với regex ngây thơ thành 'p_r_i_o_r__p_r_i_c_e')
snake = lambda s: re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", s).lower()
rows = json.loads(
    pathlib.Path("docs/20-design/market-field-selection.json").read_text(encoding="utf-8")
)
cols = [snake(r["code"]) for r in rows if r.get("keep") and r.get("nguon_chuan") == "BVSC"]
cols = [c for c in dict.fromkeys(cols) if c not in HAND_WRITTEN]
print(f"-- {len(cols)} cột sinh từ market-field-selection.json (keep & nguon_chuan=BVSC)")
for c in cols:
    print(f"  {c} numeric,")
