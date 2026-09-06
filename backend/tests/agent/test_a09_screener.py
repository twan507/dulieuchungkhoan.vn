"""Seam S4 — lọc cổ phiếu và so sánh, đọc market.screener_daily (payload jsonb).

Expected lấy từ fixture `kho` (backend/tests/agent/conftest.py, seed 2026-09-07), không phải
đo kho dev thật (§4.4.4 — tiêu chí phải bất biến). Phiên 2026-09-04 (hằng số SCREENER):
  ngành NGANHANG, ROE (rtq12) cao nhất: TIN 0.73478649, HDB 0.24836986, LPB 0.2466187
  P/E (rtd21): HPG 7.89115654, VCB 11.81676534
Payload thật có hai nhánh: 'financial' và 'stockScreenerItem' — chỉ tiêu của tầng ngữ nghĩa
nằm ở nhánh sau, fixture `kho` ghi thẳng payload = {"stockScreenerItem": {...}}.
"""
import json

import sqlalchemy as sa

from agent.tools.compare_peers import so_sanh_cung_nganh
from agent.tools.screen_stocks import loc_co_phieu


def test_top_roe_nganh_ngan_hang(db, kho):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(loc_co_phieu(db, industry_code="NGANHANG", sort_by="rtq12", limit=3))
    assert [c["ma"] for c in out["du_lieu"]] == ["TIN", "HDB", "LPB"]
    assert out["du_lieu"][0]["chi_tieu"]["ROE (TTM)"] == "73,48%"
    assert out["du_lieu"][1]["chi_tieu"]["ROE (TTM)"] == "24,84%"
    assert out["du_lieu"][2]["chi_tieu"]["ROE (TTM)"] == "24,66%"


def test_loc_theo_tieu_chi(db, kho):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(loc_co_phieu(db, criteria=[{"metric_code": "rtd21", "operator": "<", "value": 8}],
                                  industry_code="KIMLOAI", limit=20))
    assert out["co_du_lieu"] is True
    assert [c["ma"] for c in out["du_lieu"]] == ["HPG"]
    assert all("P/E (TTM)" in c["chi_tieu"] for c in out["du_lieu"])


def test_so_sanh_pe_hpg_vcb(db, kho):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(so_sanh_cung_nganh(db, tickers=["HPG", "VCB"], metric_codes=["rtd21"]))
    bang = {c["ma"]: c["chi_tieu"]["P/E (TTM)"] for c in out["du_lieu"]}
    assert bang == {"HPG": "7,89 lần", "VCB": "11,82 lần"}


def test_ma_chi_tieu_ngoai_bang_nhan_bi_tu_choi(db, kho):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(so_sanh_cung_nganh(db, tickers=["HPG"], metric_codes=["rev"]))
    assert out["loi"] is True


def test_luon_kem_ngay_du_lieu(db, kho):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    assert json.loads(loc_co_phieu(db, limit=1))["ngay_du_lieu"] == "2026-09-04"
