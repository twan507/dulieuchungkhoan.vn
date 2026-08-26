from etl.refdata_indices import INDICES, SNAP_CODES


def test_indices_match_spec_table():
    assert len(INDICES) == 18
    # literal độc lập: chép từ spec §3.1, không import từ module
    assert SNAP_CODES == {"HOSE","30","100","MID","SML","XALL","X50","SI","ALL",
                          "DIAMOND","FINLEAD","FINSELECT","HNX","HNX30","HNXFin",
                          "HNXMSCap","HNXMan","UPCOM"}
    assert len({d.ticker for d in INDICES}) == 18          # ticker chuẩn không trùng
    assert all(d.exchange in ("HOSE","HNX","UPCOM") for d in INDICES)


def test_only_three_tvc_codes_are_measured():
    tvc = {d.snap_code: d.tvc_code for d in INDICES if d.tvc_code is not None}
    assert tvc == {"HOSE": "VNINDEX", "30": "VN30", "HNX": "HNXIndex"}


def test_key_rows_verbatim():
    by = {d.snap_code: d for d in INDICES}
    assert (by["HOSE"].ticker, by["HOSE"].exchange) == ("VNINDEX", "HOSE")
    assert (by["UPCOM"].ticker, by["UPCOM"].exchange) == ("UPINDEX", "UPCOM")
    assert (by["XALL"].ticker, by["XALL"].exchange) == ("VNXALL", "HOSE")
