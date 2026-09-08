"""`refdata_fetch` — lớp tải 4 payload thô của job refdata.

🔴 Vì sao file này ra đời (rà chuẩn hoá 2026-09-07): tới lúc đó `refdata_fetch.fetch()` là
đường tải DUY NHẤT trong 15 họ job **không có một lớp retry nào** — `httpx.Client` trần +
`raise_for_status()`, nên một hiccup mạng thoáng qua giết cả lượt. Nó cũng là đường tải duy
nhất **không có test trực tiếp** (chỉ bị mock ở `test_e10_refdata_job`). Hai chuyện đó đi
cùng nhau không phải tình cờ.

Seam: `fetch(get=..., sleep=...)` — `get` bơm được đúng khuôn `http_fetch.Fetcher` dùng
(`(url, timeout) -> (status, text, headers)`), `sleep` bơm được để không ngủ thật.
"""
from __future__ import annotations

import httpx
import pytest

from etl import http_fetch, refdata_fetch as rf

OK = {k: f'{{"d":"{k}"}}' for k in rf.ENDPOINTS}


def _get(seq):
    """Trả một `get` phát lần lượt theo `seq`; mỗi phần tử là (status, text) hoặc Exception."""
    calls = []

    def get(url, timeout):
        calls.append(url)
        item = seq.pop(0) if seq else (200, OK[_key(url)])
        if isinstance(item, Exception):
            raise item
        return item[0], item[1], {}
    return get, calls


def _key(url):
    return next(k for k, u in rf.ENDPOINTS.items() if u == url)


def test_fetch_tra_du_bon_payload_va_dem_retry_bang_khong():
    get, calls = _get([])
    out, retries = rf.fetch(get=get, sleep=lambda s: None)
    assert sorted(out) == sorted(rf.ENDPOINTS)                 # đủ 4 khoá, không thiếu cái nào
    assert out["icb"] == '{"d":"icb"}' and retries == 0
    assert len(calls) == 4                                     # mỗi endpoint đúng một lời gọi


def test_loi_van_chuyen_thoang_qua_duoc_thu_lai_va_lượt_van_thanh_cong():
    """Đây là ca mà bản cũ CHẾT: một `ConnectError` là hỏng cả lượt refdata."""
    get, calls = _get([httpx.ConnectError("boom")])
    slept = []
    out, retries = rf.fetch(get=get, sleep=slept.append)
    assert sorted(out) == sorted(rf.ENDPOINTS) and retries == 1
    assert len(calls) == 5                                     # 1 lần hỏng + 4 lần thật
    assert slept and slept[0] == 2                             # backoff bậc đầu, khuôn chung (2,4,8)


def test_http_500_cung_duoc_thu_lai():
    get, _ = _get([(500, "server error")])
    out, retries = rf.fetch(get=get, sleep=lambda s: None)
    assert retries == 1 and sorted(out) == sorted(rf.ENDPOINTS)


def test_hong_qua_so_lan_thu_thi_nem_FetchError_kem_ten_endpoint():
    get, _ = _get([(503, "x")] * 4)                            # 1 + 3 lần thử đều hỏng
    with pytest.raises(http_fetch.FetchError) as e:
        rf.fetch(get=get, sleep=lambda s: None)
    assert "quotes" in str(e.value)                            # nêu ĐÚNG endpoint hỏng, không nuốt tên


def test_origin_chi_gan_cho_fiintrade_khong_gan_cho_bvsc():
    """`Origin` bắt buộc với `*.fiintrade.vn` (00-conventions §2) và CHỈ với nó.

    Kiểm ở seam `headers_for(url)` chứ không qua `fetch`: `Fetcher.fetch_one` gọi
    `get(url, timeout)` đúng hai tham số, không có chỗ nào để quan sát header — muốn kiểm
    header qua đó thì phải bịa một seam không tồn tại.
    """
    assert rf.headers_for(rf.ENDPOINTS["organization"]) == {"Origin": rf.FIIN_ORIGIN}
    assert rf.headers_for(rf.ENDPOINTS["icb"]) == {"Origin": rf.FIIN_ORIGIN}
    assert rf.headers_for(rf.ENDPOINTS["quotes"]) == {}
    assert rf.headers_for(rf.ENDPOINTS["indexsnaps"]) == {}
