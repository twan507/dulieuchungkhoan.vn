from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest

from ingester.normalize import Metrics, NormalizeError, TZ, normalize, symbol_of

RECV = 1786342136000  # 2026-08-10 13:08:56.000 +07 (epoch ms bất kỳ trong phiên)

T_FRAME = {"TD": "10/08/2026", "FT": "13:08:56", "SB": "ACV", "FV": "100", "LC": "S",
           "FMP": "42100.0", "FCV": "1000.0", "SM": "74027",
           "AVO": "590000", "AVA": "24983210000.0"}


def test_normalize_t_hand_solved():
    m = Metrics()
    n = normalize("t", T_FRAME, RECV, m)
    assert n.table == "trade" and n.symbol == "ACV"
    assert n.row["ts"] == datetime(2026, 8, 10, 13, 8, 56, tzinfo=TZ)
    assert n.row["price"] == Decimal("42100.00")
    assert n.row["volume"] == 100 and n.row["seq"] == 74027
    assert n.row["cum_value"] == Decimal("24983210000.00")
    assert n.row["received_at"].timestamp() * 1000 == RECV


def test_normalize_t_unknown_key_counted_not_stored():
    m = Metrics()
    n = normalize("t", {**T_FRAME, "ZZ": "1"}, RECV, m)
    assert "ZZ" not in n.row and m.counters.get("unknown_key.t.ZZ") == 1


def test_normalize_excess_decimals_rounded_with_metric():
    m = Metrics()
    n = normalize("t", {**T_FRAME, "FMP": "100.005"}, RECV, m)
    assert n.row["price"] == Decimal("100.00")           # half-even về scale 2
    assert m.counters.get("decimal_normalized") == 1


def test_normalize_t_bad_volume_raises():
    with pytest.raises(NormalizeError):
        normalize("t", {**T_FRAME, "FV": "abc"}, RECV, Metrics())


def test_normalize_i_extra_and_cv_p1():
    m = Metrics()
    p = {"EX": "HOSE", "t": 1786330492737, "U2": "43500", "SB": "BID",
         "CV": "1100", "P1": "1100", "LAZ": {"x": 1}}
    n = normalize("i", p, RECV, m)
    assert n.table == "snapshot_delta"
    assert n.row["u2"] == 43500 and n.row["b1"] is None
    assert '"LAZ"' in n.row["extra"] and m.counters.get("cv_ne_p1") is None
    n2 = normalize("i", {**p, "P1": "9"}, RECV, m)
    assert m.counters.get("cv_ne_p1") == 1
    assert n2.row["extra"] != ""


def test_normalize_i_no_extra_is_empty_string():
    n = normalize("i", {"EX": "HOSE", "t": 1786330492737, "SB": "BID"}, RECV, Metrics())
    assert n.row["extra"] == ""


def test_normalize_idx_ms_epoch_tz():
    p = {"MC": "X50", "MI": "3230.86", "t": 1786342140044, "IT": "13:09:00", "TD": "10/08/2026"}
    n = normalize("idx", p, RECV, Metrics())
    ts = n.row["ts"]
    assert ts.tzinfo is not None and ts.astimezone(TZ).hour == 13 and ts.minute == 9
    assert n.row["index_value"] == Decimal("3230.86")
    assert n.row["extra"] == ""      # IT/TD bỏ có chủ đích, không phải trường lạ


def test_normalize_ptm_epoch_seconds_and_extra():
    p = {"SB": "DBC", "MC": "HOSE", "TD": "10/08/2026", "TI": "13:09:17", "PR": "16650.0",
         "MVL": 590000, "RE": 16650, "CE": 17800, "FL": 15500,
         "CNO": "VN000000DBC2-mdds:0:682530462/GSTO000009:1211905",
         "LS": 1786342157, "MKI": "10", "IAC": True}
    n = normalize("ptm", p, RECV, Metrics())
    assert n.row["ts"] == datetime.fromtimestamp(1786342157, tz=TZ)
    assert n.row["volume"] == 590000
    assert '"MKI"' in n.row["extra"] and '"IAC"' in n.row["extra"]


def test_symbol_of():
    assert symbol_of("t", T_FRAME) == "ACV"
    assert symbol_of("idx", {"MC": "HOSE"}) == "HOSE"
    assert symbol_of("t", {}) is None


def test_normalize_i_b1_s1_are_decimal_not_uint():
    # DDL §3.3: b1..b3/s1..s3 là Nullable(Decimal64(2)) — giá lẻ (chứng quyền) phải qua _dec2
    p = {"EX": "HOSE", "t": 1786330492737, "SB": "CFPT2401", "B1": "23950.5"}
    n = normalize("i", p, RECV, Metrics())
    assert n.row["b1"] == Decimal("23950.50")


def test_normalize_idx_pt_value_is_decimal_not_uint():
    # DDL §3.4: pt_value là Nullable(Decimal64(2))
    p = {"MC": "X50", "MI": "3230.86", "t": 1786342140044, "PTV": "123456.7"}
    n = normalize("idx", p, RECV, Metrics())
    assert n.row["pt_value"] == Decimal("123456.70")


def test_normalize_t_missing_nonnullable_defaults_to_zero():
    # DDL §3.1: change/cum_volume/cum_value là non-nullable — thiếu frame phải mặc định 0, không None
    base = {"TD": "10/08/2026", "FT": "13:08:56", "SB": "ACV", "FV": "100", "LC": "S",
            "FMP": "42100.0", "SM": "74027"}
    n = normalize("t", base, RECV, Metrics())
    assert n.row["change"] == Decimal("0.00")
    assert n.row["cum_volume"] == 0
    assert n.row["cum_value"] == Decimal("0.00")


def test_normalize_o_missing_top_raises():
    # DDL §3.2: top không Nullable — thiếu bậc sổ lệnh là frame hỏng tất định, đi đường poison
    p = {"SB": "ACV", "t": 1786330492737, "ACT": "U", "BP": "42100.0", "BQ": "100"}
    with pytest.raises(NormalizeError):
        normalize("o", p, RECV, Metrics())


def test_normalize_t_missing_side_defaults_to_empty_string():
    # DDL §3.1: side không Nullable — LC thiếu mặc định "" (không raise, không None)
    base = {"TD": "10/08/2026", "FT": "13:08:56", "SB": "ACV", "FV": "100",
            "FMP": "42100.0", "SM": "74027"}
    n = normalize("t", base, RECV, Metrics())
    assert n.row["side"] == ""


# --- review cuối: chuỗi rỗng = thiếu (I6) + cột NON-NULLABLE còn lọt None (I7) ---

def test_normalize_t_empty_optional_fields_default_not_error():
    """IMPORTANT 6 — luật "chuỗi rỗng = thiếu" trước chỉ áp cho `i`/`idx`; `t` vẫn dùng
    `"KEY" in payload` nên FCV/AVO/AVA rỗng làm NormalizeError → VỨT CẢ LỆNH KHỚP THẬT.
    """
    p = {**T_FRAME, "FCV": "", "AVO": "", "AVA": ""}
    n = normalize("t", p, RECV, Metrics())
    assert n.row["change"] == Decimal("0.00")
    assert n.row["cum_volume"] == 0
    assert n.row["cum_value"] == Decimal("0.00")
    assert n.row["price"] == Decimal("42100.00")      # phần thật của lệnh khớp vẫn nguyên


def test_normalize_t_empty_required_field_raises():
    with pytest.raises(NormalizeError):
        normalize("t", {**T_FRAME, "FMP": ""}, RECV, Metrics())   # giá khớp rỗng = frame hỏng


def test_normalize_o_empty_optional_fields_default_not_error():
    p = {"SB": "ACV", "t": 1786330492737, "TOP": "1", "ACT": "", "BP": "", "BQ": "",
         "SP": "41000.0", "SQ": "300", "CBV": "", "CSV": ""}
    n = normalize("o", p, RECV, Metrics())
    assert n.row["bid_price"] == Decimal("0.00") and n.row["bid_qty"] == 0
    assert n.row["ask_price"] == Decimal("41000.00") and n.row["ask_qty"] == 300
    assert n.row["action"] == "" and n.row["cum_bid"] == 0 and n.row["cum_ask"] == 0


def test_normalize_o_empty_top_raises():
    p = {"SB": "ACV", "t": 1786330492737, "TOP": "", "BP": "42100.0"}
    with pytest.raises(NormalizeError):
        normalize("o", p, RECV, Metrics())


def test_normalize_i_missing_exchange_defaults_to_empty_string():
    # DDL §3.3: exchange là LowCardinality(String), KHÔNG Nullable — None sẽ hỏng insert
    n = normalize("i", {"SB": "BID", "t": 1786330492737}, RECV, Metrics())
    assert n.row["exchange"] == ""


PTM_FRAME = {"SB": "DBC", "MC": "HOSE", "PR": "16650.0", "MVL": 590000,
             "CNO": "VN000000DBC2-mdds:0:682530462", "LS": 1786342157}


def test_normalize_ptm_missing_market_and_order_id_default_to_empty_string():
    # DDL §3.5: market/order_id là String không Nullable → thiếu thì "" chứ không None
    p = {k: v for k, v in PTM_FRAME.items() if k not in ("MC", "CNO")}
    n = normalize("ptm", p, RECV, Metrics())
    assert n.row["market"] == "" and n.row["order_id"] == ""


def test_normalize_ptm_missing_price_raises():
    # PR/MVL là dữ liệu cốt lõi của bản ghi thoả thuận (Decimal64(2)/UInt64 không Nullable)
    with pytest.raises(NormalizeError):
        normalize("ptm", {k: v for k, v in PTM_FRAME.items() if k != "PR"}, RECV, Metrics())


def test_normalize_ptm_empty_volume_raises():
    with pytest.raises(NormalizeError):
        normalize("ptm", {**PTM_FRAME, "MVL": ""}, RECV, Metrics())
