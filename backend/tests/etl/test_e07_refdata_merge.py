import pathlib
from etl.refdata_merge import merge
from etl.refdata_normalize import normalize

FIX = pathlib.Path(__file__).parent / "fixtures" / "refdata"


def _target():
    raw = {k: (FIX / f"{k}.json").read_text(encoding="utf-8")
           for k in ("quotes", "indexsnaps", "organization", "icb")}
    return merge(normalize(raw))


def test_fiin_only_rows_are_delisted_with_mapped_exchange_and_type():
    t = _target()
    by = {s.ticker: s for s in t.securities}
    egl = by["EGL"]                      # org-only, UpcomIndex
    assert (egl.status, egl.exchange, egl.security_type) == ("delisted", "UPCOM", "stock")
    f4 = by["FUCTVGF4"]                  # org-only, QU, VNINDEX
    assert (f4.status, f4.exchange, f4.security_type) == ("delisted", "HOSE", "fund_cert")
    assert t.counters["fiin_only_delisted"] == 2


def test_indices_present_and_never_delisted_despite_absent_from_quotes():
    t = _target()
    idx = [s for s in t.securities if s.security_type == "index"]
    assert len(idx) == 18 and all(s.status == "listed" for s in idx)
    vni = next(s for s in idx if s.ticker == "VNINDEX")
    assert ("bvsc", "HOSE", "snapshot") in vni.external_ids
    assert ("bvsc", "VNINDEX", "tvc") in vni.external_ids       # seam 2b step-02


def test_issuer_links():
    t = _target()
    by = {s.ticker: s for s in t.securities}
    assert by["VHM"].organ_code == "NHN"
    assert by["FUEMAVND"].organ_code == "2172623"    # ETF khớp QU (luật 4)
    assert by["E1SSHN30"].organ_code is None          # ETF không khớp
    assert by["HTB"].organ_code is None               # CP không issuer
    assert t.counters["stocks_no_issuer"] == 1  # chỉ HTB — giải tay từ fixture (README, sửa 2026-08-26)
    assert len(t.issuers) == 8


def test_target_tickers_are_unique():
    t = _target()
    tickers = [s.ticker for s in t.securities]
    assert len(tickers) == len(set(tickers))


def test_unknown_com_group_skipped_not_fatal():
    """Final review M1: comGroupCode lạ ở dòng fiin-only → bỏ + đếm, không KeyError."""
    import json
    raw = {k: (FIX / f"{k}.json").read_text(encoding="utf-8")
           for k in ("quotes", "indexsnaps", "organization", "icb")}
    d = json.loads(raw["organization"])
    d["items"].append({"organCode": "XTEST", "ticker": "XTS", "comGroupCode": "MoonIndex",
                       "organName": "Thử nghiệm", "organShortName": None,
                       "comTypeCode": "CT", "icbCode": None})
    raw["organization"] = json.dumps(d, ensure_ascii=False)
    t = merge(normalize(raw))
    assert t.counters["unknown_com_group"] == 1
    assert not any(s.ticker == "XTS" for s in t.securities)


def test_duplicate_org_ticker_prefers_dn():
    """Spec §3 luật 6 (phòng thủ): trùng ticker trong GetListOrganization —
    ưu tiên organTypeCode='DN', bản ghi còn lại đếm + log, không chặn job."""
    import json
    raw = {k: (FIX / f"{k}.json").read_text(encoding="utf-8")
           for k in ("quotes", "indexsnaps", "organization", "icb")}
    d = json.loads(raw["organization"])
    # ACV đã có trong fixture (organTypeCode vắng mặt trong fixture cũ → coi như DN);
    # thêm bản ghi TRÙNG ticker ACV loại OTHER với organCode khác
    for item in d["items"]:
        item.setdefault("organTypeCode", "DN")
    d["items"].append({"organCode": "ACV_DUP", "ticker": "ACV", "comGroupCode": "VNINDEX",
                       "organName": "Bản trùng", "organShortName": None,
                       "comTypeCode": "CT", "icbCode": None, "organTypeCode": "OTHER"})
    raw["organization"] = json.dumps(d, ensure_ascii=False)
    t = merge(normalize(raw))
    by = {s.ticker: s for s in t.securities}
    assert by["ACV"].organ_code == "ACVN"            # bản DN thắng
    assert t.counters["dup_org_ticker"] == 1
