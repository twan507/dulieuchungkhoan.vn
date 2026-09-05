"""Mã của mình không trùng giữa 5 nguồn quốc tế và WiChart — trừ `wti`, cố ý dùng chung asset cho spot/futures."""
from collections import Counter

from etl import binance_registry, fred_registry, fx_registry, lbma_registry, wichart_registry, yahoo_registry


def test_codes_unique_across_all_registries_except_wti():
    codes = Counter()
    for mod in (fred_registry, fx_registry, lbma_registry, yahoo_registry, binance_registry, wichart_registry):
        codes.update(s.code for s in mod.build())
    dup = {c: n for c, n in codes.items() if n > 1}
    assert dup == {"wti": 2}
    assert sum(codes.values()) == 15 + 6 + 2 + 37 + 11 + 105


def test_external_ids_unique_within_each_source():
    for mod in (fred_registry, fx_registry, lbma_registry, yahoo_registry, binance_registry):
        keys = [(s.source, s.external_key, s.external_sub) for s in mod.build()]
        assert len(keys) == len(set(keys))
