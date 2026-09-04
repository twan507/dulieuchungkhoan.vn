import json
import pathlib

import pytest

from etl import fundamentals_normalize as fn

FIX = pathlib.Path(__file__).parent / "fixtures" / "fundamentals"


def _item(name):
    d = json.loads((FIX / name).read_text(encoding="utf-8"))
    return {"items": d["items"]} if name.endswith("reports.json") else d["items"][0]


def test_rows_of_a32_match_the_independent_count():
    """1.749 / 980 / 916 do docs/.../count_rows.py đếm riêng trên cùng mẫu — không chung code."""
    assert len(fn.rows("bs", _item("A32-bs.json"))) == 1749
    assert len(fn.rows("is", _item("A32-is.json"))) == 980
    assert len(fn.rows("cf", _item("A32-cf.json"))) == 916


def test_rows_carry_the_literal_values_of_the_2025_annual_report():
    got = {(r.year, r.length, r.metric_code): r for r in fn.rows("bs", _item("A32-bs.json"))}
    r = got[(2025, 5, "bsa1")]
    assert r.statement_type == "BS" and r.value == 365335639678.0
    assert got[(2025, 5, "bsa23")].value == 125782590230.0
    assert got[(2025, 5, "bsa53")].value == 491118229908.0                # bsa1 + bsa23 = bsa53 (Phụ lục A)
    assert (2025, 5, "bsb98") not in got                                  # null ⇒ không có dòng
    assert (2025, 5, "organcode") not in got and (2025, 5, "organCode") not in got
    cf = {(r.year, r.metric_code): r.value for r in fn.rows("cf", _item("A32-cf.json"))}
    assert cf[(2025, "cfa18")] == -55721888430.0


def test_rows_lower_case_the_two_mixed_case_keys_and_drop_the_eight_non_metric_keys():
    codes = {r.metric_code for r in fn.rows("bs", _item("A32-bs.json"))}
    assert "bsi141" in codes and "bsI141" not in codes                   # đo 2026-09-04, 4/4 mã
    is_codes = {r.metric_code for r in fn.rows("is", _item("A32-is.json"))}
    assert not ({"ebit", "ebitda", "operating", "rtq29"} & is_codes)


def test_rows_refuse_a_quarter_report_outside_one_to_five():
    item = {"quarterly": [{"yearReport": 2026, "quarterReport": 6, "bsa1": 1.0}], "yearly": []}
    with pytest.raises(fn.BadRecord, match="quarterReport"):
        fn.rows("bs", item)


def test_rows_refuse_a_duplicated_period():
    item = {"quarterly": [], "yearly": [{"yearReport": 2025, "quarterReport": 5, "bsa1": 1.0},
                                        {"yearReport": 2025, "quarterReport": 5, "bsa1": 2.0}]}
    with pytest.raises(fn.BadRecord, match="trùng"):
        fn.rows("bs", item)


def test_report_rows_keep_the_source_id_and_the_seven_allowed_lengths():
    got = fn.rows("reports", _item("A32-reports.json"))
    assert len(got) == 8 and got[0].source_id == 9412069 and got[0].year == 2025 and got[0].length == 5
    assert got[0].title == "BCTC đã kiểm toán năm 2025"
    assert got[0].url.endswith("A32_BCTC_CN_2025_HN_KT.pdf")
    bab = fn.rows("reports", _item("BAB-reports.json"))
    assert len(bab) == 106 and {r.length for r in bab} == {1, 2, 3, 4, 5, 6, 9}
    with pytest.raises(fn.BadRecord):
        fn.rows("reports", {"items": [{"id": 1, "yearReport": 2024, "lengthReport": 7, "sourceUrl": "u"}]})
    with pytest.raises(fn.BadRecord):
        fn.rows("reports", {"items": [{"yearReport": 2024, "lengthReport": 1, "sourceUrl": "u"}]})   # thiếu id


def test_payload_hash_ignores_order_and_nulls_but_sees_a_value_change():
    item = _item("A32-bs.json")
    h0 = fn.payload_hash(fn.rows("bs", item))

    shuffled = {"quarterly": [], "yearly": list(reversed(item["yearly"]))}
    assert fn.payload_hash(fn.rows("bs", shuffled)) == h0                # đổi thứ tự kỳ

    rec = dict(item["yearly"][0]); rec = {k: rec[k] for k in reversed(list(rec))}
    reordered = {"quarterly": [], "yearly": [rec] + item["yearly"][1:]}
    assert fn.payload_hash(fn.rows("bs", reordered)) == h0               # đổi thứ tự khoá

    extra_null = {"quarterly": [], "yearly": [dict(item["yearly"][0], zzz_new=None)] + item["yearly"][1:]}
    assert fn.payload_hash(fn.rows("bs", extra_null)) == h0              # thêm ô null

    changed = {"quarterly": [], "yearly": [dict(item["yearly"][0], bsa1=1.0)] + item["yearly"][1:]}
    assert fn.payload_hash(fn.rows("bs", changed)) != h0                 # đổi một giá trị

    assert fn.payload_hash([]) == fn.EMPTY_HASH


def test_rows_merge_an_identical_duplicated_period_but_refuse_a_conflicting_one():
    """Đo 2026-09-04 20:12 trên BSHCO (lượt backfill thật): `quarterly` chứa kỳ 2024/Q2 HAI lần,
    hai bản ghi giống hệt nhau (160 ô non-null, 0 khác biệt) — nguồn lặp bản ghi, không phải hai kỳ.
    Bản trùng giống hệt thì gộp; hai bản KHÁC nhau mới là sai hợp đồng (mất dữ liệu nếu chọn bừa)."""
    item = _item("BSHCO-bs-duplicate-period.json")
    assert sum(1 for r in item["quarterly"] if (r["yearReport"], r["quarterReport"]) == (2024, 2)) == 2
    got = fn.rows("bs", item)
    periods = {(r.year, r.length) for r in got}
    assert (2024, 2) in periods and len(periods) == 17 - 1 + 16          # 17 quý (1 trùng) + 16 năm
    assert len([r for r in got if (r.year, r.length) == (2024, 2)]) == 159       # 160 ô non-null trừ `otherAssetNonBank` (khoá phi chỉ tiêu duy nhất có giá trị ở kỳ này)
    conflicting = {"quarterly": [], "yearly": [{"yearReport": 2025, "quarterReport": 5, "bsa1": 1.0},
                                               {"yearReport": 2025, "quarterReport": 5, "bsa1": 2.0}]}
    with pytest.raises(fn.BadRecord, match="trùng"):
        fn.rows("bs", conflicting)
