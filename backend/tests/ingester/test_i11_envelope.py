"""Vỏ bọc sails.io của frame THẬT — đo 2026-08-26 trên capture phiên chiều.

Tài liệu nguồn (11-bvsc-realtime.md §4–§8) chỉ chép BẢN GHI BÊN TRONG. Frame thật
đi kèm một lớp vỏ `{"a": "<u|i>", "d": [ <bản ghi>, ... ]}` — không bóc lớp này
thì mọi frame thật đều hỏng ở cổng chuẩn hoá. Các packet dưới đây là NGUYÊN VĂN
từ file đo `frames-20260826-13.jsonl.gz`.
"""
from decimal import Decimal

import pytest

from ingester.normalize import Metrics, NormalizeError, normalize, records_of, symbol_of

REAL_T = {"a": "i", "d": [{"TD": "26/08/2026", "FV": "1", "LC": "B", "FMP": "1942.3",
                           "FCV": "2.4", "SM": "550316", "AVO": "130589",
                           "AVA": "25356027540000.0", "FT": "13:00:01", "SB": "41I1G9000"}]}
REAL_I = {"a": "u", "d": [{"EX": "XHNF", "t": 1787724001446, "V2": 3, "TB": 146,
                           "SB": "41I1GA000"}]}
REAL_O = {"a": "u", "d": [{"ACT": "U", "TOP": "1", "t": 1787724001444, "CBV": "1",
                           "CSV": "2", "id": "41I1GA000:1", "SP": "1942.0",
                           "BP": "1937.5", "SQ": "2", "SB": "41I1GA000", "BQ": "1"}]}
REAL_PTM = {"a": "u", "d": [{"MVL": 11, "PR": "106164.0", "CE": 999999999,
                             "CNO": "VNHDB1240234-mdds:0:738353283/GHCX000008:1130",
                             "FL": 0, "LS": 1787724001, "MKI": "02", "IAC": True,
                             "SB": "HDB124023", "TD": "26/08/2026", "TI": "13:00:01",
                             "RE": 103780, "MC": "HNX"}]}
RECV = 1787724002000


def test_records_of_unwraps_envelope():
    assert records_of(REAL_T) == REAL_T["d"]
    assert len(records_of(REAL_I)) == 1


def test_records_of_accepts_multiple_records():
    two = {"a": "u", "d": [{"SB": "AAA"}, {"SB": "BBB"}]}
    assert [r["SB"] for r in records_of(two)] == ["AAA", "BBB"]


def test_records_of_passes_through_bare_record():
    """Mẫu trong tài liệu nguồn không có vỏ — vẫn phải dùng được."""
    assert records_of({"SB": "ACV", "FV": "1"}) == [{"SB": "ACV", "FV": "1"}]


def test_normalize_real_trade_record():
    rec = records_of(REAL_T)[0]
    assert symbol_of("t", rec) == "41I1G9000"
    n = normalize("t", rec, RECV, Metrics())
    assert n.table == "trade"
    assert n.row["price"] == Decimal("1942.30")
    assert n.row["volume"] == 1 and n.row["seq"] == 550316
    assert n.row["side"] == "B"


def test_normalize_real_snapshot_record():
    n = normalize("i", records_of(REAL_I)[0], RECV, Metrics())
    assert n.table == "snapshot_delta"
    assert n.row["v2"] == 3 and n.row["total_bid"] == 146
    assert n.row["exchange"] == "XHNF"
    assert n.row["extra"] == ""            # không trường lạ trong frame này


def test_normalize_real_quote_and_ptm_records():
    q = normalize("o", records_of(REAL_O)[0], RECV, Metrics())
    assert q.row["bid_price"] == Decimal("1937.50") and q.row["top"] == 1
    p = normalize("ptm", records_of(REAL_PTM)[0], RECV, Metrics())
    assert p.row["volume"] == 11 and p.row["price"] == Decimal("106164.00")
    assert '"MKI"' in p.row["extra"]


def test_empty_string_price_is_null_not_error():
    """Đo 2026-08-26: B1/S1 của `i` có lúc là chuỗi rỗng (615/519.133 frame,
    0,12%) — nghĩa là 'không có dư mua/bán bậc đó', KHÔNG phải lỗi dữ liệu."""
    m = Metrics()
    n = normalize("i", {"SB": "AAA", "EX": "HOSE", "t": 1787724001446,
                        "B1": "", "S1": "", "V1": "100"}, RECV, m)
    assert n.row["b1"] is None and n.row["s1"] is None
    assert n.row["v1"] == 100
    assert n.row["extra"] == ""            # rỗng không được rơi vào extra


def test_empty_string_in_required_field_still_errors():
    with pytest.raises(NormalizeError):
        normalize("t", {"SB": "AAA", "TD": "26/08/2026", "FT": "13:00:01",
                        "FMP": "", "FV": "1", "SM": "1"}, RECV, Metrics())


def test_undocumented_keys_go_to_extra():
    """Khoá lạ đo được 2026-08-26: i có OP/LO/TSI, idx có IC/MS/NOF."""
    n = normalize("i", {"SB": "WCS", "EX": "HNX", "t": 1787724001934,
                        "OP": 290600, "LO": 290600, "TSI": "OPEN"}, RECV, Metrics())
    assert '"OP"' in n.row["extra"] and '"LO"' in n.row["extra"] and '"TSI"' in n.row["extra"]
    x = normalize("idx", {"MC": "XALL", "IC": "up", "MI": "2870.48", "NOF": "1", "MS": "5",
                          "t": 1787724001934}, RECV, Metrics())
    assert '"IC"' in x.row["extra"] and '"NOF"' in x.row["extra"] and '"MS"' in x.row["extra"]
