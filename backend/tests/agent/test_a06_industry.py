"""Seam S4 — cây ngành RIÊNG của dự án, tuyệt đối không phơi ICB ra model.

Expected lấy từ fixture `kho` (backend/tests/agent/conftest.py): VCB được gán ngành
NGANHANG qua issuer.industry_id (không qua issuer_industry_override) ⇒ view
market.v_issuer_industry trả source='icb'. Cây ngành ('market.industry') do migration
0003/0011/0013 seed sẵn, KHÔNG do fixture `kho` tạo — đo 2026-09-07 bằng đường khác đường
của hàm (đếm thẳng trên bảng, không qua view):
  SELECT count(*) FROM market.industry WHERE level=1  -> 6
  SELECT count(*) FROM market.industry WHERE level=2  -> 24
  SELECT ind.code, ind.name_vi, par.code, par.name_vi FROM market.industry ind
    JOIN market.industry par ON par.industry_id=ind.parent_id
    WHERE ind.code='NGANHANG'
  -> NGANHANG, 'Ngân hàng và Tín dụng', TAICHINH, 'Dịch vụ Tài chính'
"""
import json

import sqlalchemy as sa

from agent.tools.get_industry_tree import cay_nganh


def test_cay_du_sau_nhom_hai_bon_nganh(db, kho):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(cay_nganh(db))
    assert len(out["nhom"]) == 6
    assert sum(len(n["nganh"]) for n in out["nhom"]) == 24


def test_nganh_cua_vcb(db, kho):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(cay_nganh(db, ticker="VCB"))
    assert out["nganh"]["ma"] == "NGANHANG"
    assert out["nganh"]["ten"] == "Ngân hàng và Tín dụng"
    assert out["nhom"]["ten"] == "Dịch vụ Tài chính"
    assert out["nguon_gan"] == "icb"


def test_khong_bao_gio_lo_icb(db, kho):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    assert "icb_code" not in cay_nganh(db, ticker="VCB")
    assert "icb" not in json.loads(cay_nganh(db))["nhom"][0]


def test_ma_khong_ton_tai(db, kho):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    assert json.loads(cay_nganh(db, ticker="ZZZZ"))["tim_thay"] is False
