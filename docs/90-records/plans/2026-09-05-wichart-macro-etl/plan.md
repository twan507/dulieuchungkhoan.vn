# Lát 6 `etl wichart` — kế hoạch thực thi

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Job `python -m etl wichart` nạp 68 key WiChart (53 series vĩ mô → `macro.observation`, 52 series giá → `asset.price_daily`) kèm hai registry, một dòng `series_break`, bằng chứng thô, guard trước commit.

**Architecture:** Năm module theo khuôn lát 4–5 (`wichart_registry` · `wichart_fetch` · `wichart_normalize` · `wichart_guard` · `wichart_store` · `wichart_job`). Registry = khối Python §9 của `docs/10-sources/macro/wichart.md` (đọc bằng `exec`) ghép với bảng mã của mình trong module; `build()` raise khi hai bên lệch. Ghi UPSERT có `WHERE value IS DISTINCT FROM` để đếm `changed`; guard đánh giá trước khi mở giao dịch ghi.

**Tech Stack:** Python 3.12 · httpx · SQLAlchemy 2 (text SQL) + psycopg 3 · pytest trên Postgres thật (`TEST_DATABASE_URL`) · Alembic đã ở head `0017`, **không migration mới**.

**Spec:** [spec.md](spec.md) cùng thư mục. Mẫu thật: `backend/tests/etl/fixtures/wichart/*.json` (12 key, chụp 2026-09-05 06:5x, bản sao ở `samples/`).

## Global Constraints

- Mọi lệnh chạy từ `backend/`: `set -a && . ../.env && set +a && PYTHONIOENCODING=utf-8 uv run pytest …` (Git Bash). `TEST_DATABASE_URL` phải có trong env (đọc từ `.env` gốc repo). Không in giá trị biến môi trường.
- TDD nghiêm: test đỏ trước, xem nó đỏ **đúng lý do**, rồi mới code (CLAUDE.md §4.5). Expected là literal từ fixture/giải tay, **không** tính lại theo cách code tính.
- Test đụng DB dùng fixture `db` (một giao dịch, rollback) từ `tests/etl/conftest.py`; test job dùng `migrated_engine` + `_cleanup` tự dập nền theo đúng tập của mình.
- Không sửa module ngoài phạm vi task (§4.4.3). Không tạo `.superpowers/` trong repo.
- Commit nhỏ, Conventional Commits, message tiếng Anh, kết thúc bằng `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`. Nhánh `feat/wichart-etl`.
- Kho: `macro.observation.obs_date` = **ngày đầu kỳ**; `asset.price_daily` PK `(asset_id, obs_date, price_type)`; `indicator_source.external_sub` / `asset_external_id.external_sub` = **chỉ số series dạng chuỗi** (`'0'`, `'1'`…).
- Epoch WiChart parse bằng `Asia/Ho_Chi_Minh`; mọi ngày trong test lấy từ fixture hoặc `date.today()`.

---

## Cấu trúc file

| File | Trách nhiệm |
|---|---|
| `backend/etl/wichart_registry.py` | Đọc khối §9, bảng mã `MACRO`/`ASSET`, `BANDS`, `build()` ghép + kiểm hai chủ |
| `backend/etl/wichart_fetch.py` | URL, `classify`, `Fetcher` retry/backoff, `open_fetcher` (get bơm được) |
| `backend/etl/wichart_normalize.py` | `Point`, neo kỳ, nhân `scale`, kiểm tần suất/dải/tên, bỏ điểm cuối tuần chép lại |
| `backend/etl/wichart_guard.py` | `Tally`, `Verdict`, `check` |
| `backend/etl/wichart_store.py` | upsert registry, `apply` (UPSERT đếm inserted/changed), seed `series_break`, raw_payload khi hash đổi, bằng chứng từ chối, domain state hai dòng |
| `backend/etl/wichart_job.py` | `run(keys, dry_run, get, sleep)` |
| `backend/etl/__main__.py` | subcommand `wichart` |
| `docs/10-sources/macro/wichart.md` | `ca_tra` Tier X → A (đo 2026-09-05), rút khỏi `TIER_X` |
| `backend/tests/etl/test_e36…e41_wichart_*.py` | test theo seam spec §6 |

---

### Task 1: Registry — hai chủ ghép lại, lệch là chết

**Files:**
- Modify: `docs/10-sources/macro/wichart.md` (dòng `"ca_tra":` trong khối §9 và danh sách `TIER_X`; dòng `ca_tra` bảng §5.3)
- Create: `backend/etl/wichart_registry.py`
- Test: `backend/tests/etl/test_e36_wichart_registry.py`

**Interfaces:**
- Produces: `Series` (frozen dataclass: `key, idx, group, domain, code, doc_name, name_vi, unit, scale: Decimal, freq, role, flags: tuple[str,...], asset_class, quote_currency, price_type, region, calendar`; property `external_sub -> str`), `build(md_path=WICHART_MD) -> list[Series]`, `key_groups(series) -> list[tuple[str,str]]`, `BANDS: dict[str, tuple[float,float]]`, `RegistryError`, `SOURCE = "wichart"`, `WICHART_MD`.

- [ ] **Step 1: Sửa tài liệu nguồn cho `ca_tra` (đo 2026-09-05, spec §9.1)**

Trong `docs/10-sources/macro/wichart.md`:

1. Khối §9, thay dòng
   ```python
   "ca_tra":          dict(g="hang_hoa", tier="X", s=[("Giá cá tra","VND/kg",1,None,[])]),  # FROZEN tại audit 12/08, sống lại 22/08 (đo 2026-09-05) — tier xét lại ở lát 6
   ```
   bằng
   ```python
   "ca_tra":          dict(g="hang_hoa", tier="A", s=[("Giá cá tra","VND/kg",1,D,[])]),  # FROZEN tại audit 12/08, sống lại 22/08 (đo 2026-09-05) — nâng Tier A ở lát 6 (VHC · ANV · IDI)
   ```
2. Trong `TIER_X = [...]` xoá `"ca_tra",`.
3. Bảng §5.3, dòng `ca_tra`: đổi ô Tier `**X**` thành `**A**` và thêm cuối ô cờ: `— **nâng Tier A 2026-09-05** (lát 6)`.

- [ ] **Step 2: Viết test đỏ**

`backend/tests/etl/test_e36_wichart_registry.py`:

```python
"""Registry WiChart: hai chủ sở hữu (khối §9 của wichart.md · bảng mã trong module) phải khớp từng series."""
import dataclasses
import pathlib
from decimal import Decimal

import pytest

from etl import wichart_registry as wr


def _by_key_idx(series):
    return {(s.key, s.idx): s for s in series}


def test_build_resolves_53_macro_and_52_asset_series():
    series = wr.build()
    dom = {"macro": 0, "asset": 0}
    for s in series:
        dom[s.domain] += 1
    assert dom == {"macro": 53, "asset": 52}
    assert len({s.code for s in series}) == 105                       # mã không trùng
    assert sum(1 for s in series if s.role == "growth_ref") == 13


def test_dead_series_and_tier_x_keys_are_absent():
    m = _by_key_idx(wr.build())
    assert ("xang_dau", 0) not in m and ("xang_dau", 1) in m           # RON 95 chết, E5 sống
    assert ("ncp", 1) not in m and ("ncp", 0) in m and ("ncp", 2) in m
    assert not {k for k, _ in m} & {"thiec", "cao_su", "gdpbinhquan", "gao_tpxk", "xi_mang", "da_1x2"}
    assert ("ca_tra", 0) in m                                          # sống lại 22/08, đo 2026-09-05


def test_td_maps_to_credit_by_key_not_by_source_name():
    m = _by_key_idx(wr.build())
    assert m[("td", 0)].code == "vn.credit" and m[("td", 0)].doc_name == "Tổng tín dụng"
    assert m[("hd", 0)].code == "vn.deposits"
    assert "NAMEWRONG" in m[("td", 0)].flags


def test_scale_and_unit_come_from_the_doc_or_ours_as_designed():
    m = _by_key_idx(wr.build())
    assert m[("vang", 0)].scale == Decimal("1000") and m[("vang", 0)].code == "gold.sjc_buy"
    assert m[("vai_cotton_my", 0)].scale == Decimal("0.01") and m[("vai_cotton_my", 0)].unit == "USD/lb"
    assert m[("gdp", 0)].scale == Decimal("1000000000") and m[("gdp", 0)].unit == "VND"
    assert m[("gdp", 2)].role == "growth_ref" and m[("gdp", 2)].code == "vn.gdp.growth"
    assert m[("dau_wti", 0)].price_type == "futures" and m[("dhtg", 0)].price_type == "fixing"
    assert m[("dhtg", 3)].price_type == "spot" and m[("dhtg", 3)].external_sub == "3"
    assert all(s.calendar == "trading_days" for s in m.values() if s.domain == "asset")


def test_build_raises_when_module_maps_a_series_the_doc_does_not_collect(tmp_path):
    md = wr.WICHART_MD.read_text(encoding="utf-8")
    broken = md.replace('("Giá xăng E5","VND/lít",1e3,D,[])', '("Giá xăng E5","VND/lít",1e3,None,["DEAD"])')
    assert broken != md
    p = tmp_path / "wichart.md"
    p.write_text(broken, encoding="utf-8")
    with pytest.raises(wr.RegistryError, match=r"xang_dau\[1\]"):
        wr.build(p)


def test_build_raises_when_doc_collects_a_series_the_module_lacks(monkeypatch):
    trimmed = {k: v for k, v in wr.MACRO.items() if k != ("cpi", 0)}
    monkeypatch.setattr(wr, "MACRO", trimmed)
    with pytest.raises(wr.RegistryError, match=r"cpi\[0\]"):
        wr.build()


def test_key_groups_lists_each_key_once_with_its_namespace():
    kg = dict(wr.key_groups(wr.build()))
    assert len(kg) == 68
    assert kg["cpi"] == "vi_mo" and kg["vang"] == "hang_hoa" and kg["dhtg"] == "vi_mo"
```

- [ ] **Step 3: Chạy test, xác nhận đỏ vì thiếu module**

Run: `uv run pytest tests/etl/test_e36_wichart_registry.py -q`
Expected: `ImportError`/`ModuleNotFoundError: etl.wichart_registry` (collection error).

- [ ] **Step 4: Viết module**

`backend/etl/wichart_registry.py`:

```python
"""Registry WiChart — hai chủ sở hữu ghép lại (spec §4.2).

- `docs/10-sources/macro/wichart.md` §9 (khối Python CUỐI file): sự thật ĐO về nguồn — tên series,
  đơn vị gốc, `scale`, role, cờ, nhóm, tần suất. Đọc bằng `exec`, đúng cách `verify_wichart.py` làm.
- `MACRO` / `ASSET` dưới đây: lựa chọn CỦA MÌNH — mã, tên hiển thị, lớp tài sản, tiền tệ, price_type.
`build()` ghép hai bên theo (key, idx) và RAISE khi lệch — hợp đồng khởi động, chết trước khi fetch.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

WICHART_MD = Path(__file__).resolve().parents[2] / "docs" / "10-sources" / "macro" / "wichart.md"
SOURCE = "wichart"


class RegistryError(RuntimeError):
    """Module và tài liệu nguồn lệch nhau."""


@dataclass(frozen=True)
class Series:
    key: str
    idx: int
    group: str                      # 'vi_mo' | 'hang_hoa'
    domain: str                     # 'macro' | 'asset'
    code: str                       # mã của mình
    doc_name: str                   # tên series theo §9 (để đối chiếu với API)
    name_vi: str
    unit: str                       # macro: đơn vị gốc §9 · asset: đơn vị của mình (Phụ lục A)
    scale: Decimal                  # §9 — nhân raw để về đơn vị gốc
    freq: str                       # §9 — bằng tần suất thật đã đo
    role: str                       # 'data' | 'growth_ref'
    flags: tuple[str, ...]
    asset_class: str | None = None
    quote_currency: str | None = None
    price_type: str | None = None
    region: str = "vn"
    calendar: str = "trading_days"

    @property
    def external_sub(self) -> str:
        return str(self.idx)


# (key, idx) -> (code, name_vi). Tăng trưởng = <code>.growth, role growth_ref (theo §9).
MACRO: dict[tuple[str, int], tuple[str, str]] = {
    ("gdp", 0): ("vn.gdp.nominal", "GDP giá hiện hành"),
    ("gdp", 1): ("vn.gdp.real", "GDP giá so sánh"),
    ("gdp", 2): ("vn.gdp.growth", "Tăng trưởng GDP"),
    ("cpi", 0): ("vn.cpi", "CPI (YoY)"),
    ("iip", 0): ("vn.iip", "Sản xuất công nghiệp (YoY)"),
    ("pmi", 0): ("vn.pmi", "PMI"),
    ("hhdv", 0): ("vn.retail", "Tổng mức bán lẻ hàng hoá và dịch vụ"),
    ("hhdv", 1): ("vn.retail.growth", "Tăng trưởng bán lẻ"),
    ("fdi", 0): ("vn.fdi.registered", "FDI đăng ký"),
    ("fdi", 1): ("vn.fdi.realized", "FDI thực hiện"),
    ("fdi", 2): ("vn.fdi.realized.growth", "Tăng trưởng FDI thực hiện"),
    ("fdi", 3): ("vn.fdi.registered.growth", "Tăng trưởng FDI đăng ký"),
    ("cctm", 0): ("vn.export", "Xuất khẩu"),
    ("cctm", 1): ("vn.import", "Nhập khẩu"),
    ("cctm", 2): ("vn.trade_balance", "Cán cân thương mại"),
    ("cctt", 0): ("vn.bop.overall", "Cán cân tổng thể"),
    ("cctt", 1): ("vn.bop.current", "Cán cân vãng lai"),
    ("cctt", 2): ("vn.bop.financial", "Cán cân tài chính"),
    ("cctt", 3): ("vn.bop.errors", "Lỗi và sai sót"),
    ("vdtptxh", 0): ("vn.investment.social", "Vốn đầu tư phát triển xã hội"),
    ("vdtptxh", 1): ("vn.investment.social.growth", "Tăng trưởng vốn đầu tư phát triển xã hội"),
    ("vdtnsnn", 0): ("vn.investment.budget", "Vốn đầu tư từ ngân sách nhà nước"),
    ("vdtnsnn", 1): ("vn.investment.budget.growth", "Tăng trưởng vốn đầu tư từ NSNN"),
    ("vt", 0): ("vn.transport.passengers", "Vận chuyển hành khách"),
    ("vt", 1): ("vn.transport.freight", "Vận chuyển hàng hoá"),
    ("kqt", 0): ("vn.tourists", "Khách quốc tế"),
    ("kqt", 1): ("vn.tourists.growth", "Tăng trưởng khách quốc tế"),
    ("ds", 0): ("vn.population", "Tổng dân số"),
    ("ds", 1): ("vn.population.growth", "Tăng trưởng dân số"),
    ("tn", 0): ("vn.unemployment", "Tỷ lệ thất nghiệp"),
    ("ld", 0): ("vn.labor_force", "Lực lượng lao động"),
    ("ld", 1): ("vn.labor_force.growth", "Tăng trưởng lực lượng lao động"),
    ("tcns", 0): ("vn.budget.revenue", "Thu ngân sách"),
    ("tcns", 1): ("vn.budget.expenditure", "Chi ngân sách"),
    ("tcns", 2): ("vn.budget.deficit", "Bội chi ngân sách"),
    ("ncp", 0): ("vn.gov_debt", "Nợ chính phủ"),
    ("ncp", 2): ("vn.gov_debt.growth", "Tăng trưởng nợ chính phủ"),
    ("ctt", 0): ("vn.m2", "Cung tiền M2"),
    ("ctt", 1): ("vn.m2.growth", "Tăng trưởng cung tiền"),
    ("hd", 0): ("vn.deposits", "Tổng tiền gửi"),
    ("hd", 1): ("vn.deposits.growth", "Tăng trưởng tiền gửi"),
    ("td", 0): ("vn.credit", "Tổng tín dụng"),
    ("td", 1): ("vn.credit.growth", "Tăng trưởng tín dụng"),
    ("dtnh", 0): ("vn.fx_reserves", "Dự trữ ngoại hối"),
    ("lsdh", 0): ("vn.rate.discount", "Lãi suất chiết khấu"),
    ("lsdh", 1): ("vn.rate.refinancing", "Lãi suất tái cấp vốn"),
    ("lsdh", 2): ("vn.rate.overnight_lending", "Lãi suất cho vay qua đêm bù đắp thiếu hụt"),
    ("lslnh", 0): ("vn.rate.interbank.on", "Lãi suất liên ngân hàng qua đêm"),
    ("lslnh", 1): ("vn.rate.interbank.1w", "Lãi suất liên ngân hàng 1 tuần"),
    ("lslnh", 2): ("vn.rate.interbank.2w", "Lãi suất liên ngân hàng 2 tuần"),
    ("lshd", 0): ("vn.rate.deposit.1_3m", "Lãi suất huy động tại quầy 1–3 tháng"),
    ("lshd", 1): ("vn.rate.deposit.6_9m", "Lãi suất huy động tại quầy 6–9 tháng"),
    ("lshd", 2): ("vn.rate.deposit.13m", "Lãi suất huy động tại quầy 13 tháng"),
}

# (key, idx) -> (code, name_vi, asset_class, quote_currency, unit, price_type, region)
_C = "commodity"
ASSET: dict[tuple[str, int], tuple[str, str, str, str, str, str, str]] = {
    ("dhtg", 0): ("fx.usd_vnd.central", "Tỷ giá USD/VND trung tâm", "fx", "VND", "VND/1 USD", "fixing", "vn"),
    ("dhtg", 1): ("fx.usd_vnd.ceiling", "Tỷ giá USD/VND trần", "fx", "VND", "VND/1 USD", "fixing", "vn"),
    ("dhtg", 2): ("fx.usd_vnd.floor", "Tỷ giá USD/VND sàn", "fx", "VND", "VND/1 USD", "fixing", "vn"),
    ("dhtg", 3): ("fx.usd_vnd.bank_sell", "Tỷ giá USD/VND NHTM bán ra", "fx", "VND", "VND/1 USD", "spot", "vn"),
    ("dhtg", 4): ("fx.usd_vnd.free_sell", "Tỷ giá USD/VND tự do bán ra", "fx", "VND", "VND/1 USD", "spot", "vn"),
    ("heo_hoi", 0): ("hog_live", "Giá heo hơi", _C, "VND", "VND/kg", "spot", "vn"),
    ("ca_phe", 0): ("coffee_robusta_vn", "Giá cà phê", _C, "VND", "VND/kg", "spot", "vn"),
    ("tieu", 0): ("pepper_vn", "Giá tiêu", _C, "VND", "VND/kg", "spot", "vn"),
    ("duong", 0): ("sugar", "Giá đường", _C, "USD", "USD/tấn", "spot", "global"),
    ("dau_co_malaysia", 0): ("palm_oil_my", "Giá dầu cọ Malaysia", _C, "MYR", "MYR/tấn", "spot", "my"),
    ("soi_coton", 0): ("cotton_yarn_cn", "Giá sợi cotton Trung Quốc", _C, "CNY", "CNY/tấn", "spot", "cn"),
    ("lua", 0): ("paddy_vn", "Giá lúa", _C, "VND", "VND/kg", "spot", "vn"),
    ("gao_nguyen_lieu", 0): ("rice_raw_vn", "Giá gạo nguyên liệu", _C, "VND", "VND/kg", "spot", "vn"),
    ("phu_pham_lua_gao", 0): ("rice_byproduct_vn", "Giá phụ phẩm lúa gạo", _C, "VND", "VND/kg", "spot", "vn"),
    ("tom_the", 0): ("shrimp_whiteleg_vn", "Giá tôm thẻ", _C, "VND", "VND/kg", "spot", "vn"),
    ("vai_cotton_my", 0): ("cotton_us", "Giá bông Mỹ", _C, "USD", "USD/lb", "spot", "us"),
    ("ca_tra", 0): ("pangasius_vn", "Giá cá tra", _C, "VND", "VND/kg", "spot", "vn"),
    ("quang_sat", 0): ("iron_ore_cn", "Giá quặng sắt Trung Quốc", _C, "CNY", "CNY/tấn", "spot", "cn"),
    ("vang", 0): ("gold.sjc_buy", "Giá vàng miếng SJC mua vào", _C, "VND", "VND/lượng", "spot", "vn"),
    ("vang", 1): ("gold.sjc_sell", "Giá vàng miếng SJC bán ra", _C, "VND", "VND/lượng", "spot", "vn"),
    ("vang_the_gioi", 0): ("gold.intl", "Giá vàng thế giới", _C, "USD", "USD/oz", "spot", "global"),
    ("chi", 0): ("lead_cn", "Giá chì Trung Quốc", _C, "CNY", "CNY/tấn", "spot", "cn"),
    ("kem", 0): ("zinc_cn", "Giá kẽm Trung Quốc", _C, "CNY", "CNY/tấn", "spot", "cn"),
    ("nhom", 0): ("aluminum_cn", "Giá nhôm Trung Quốc", _C, "CNY", "CNY/tấn", "spot", "cn"),
    ("niken", 0): ("nickel_cn", "Giá niken Trung Quốc", _C, "CNY", "CNY/tấn", "spot", "cn"),
    ("dong", 0): ("copper", "Giá đồng", _C, "USD", "USD/lb", "spot", "global"),
    ("bac", 0): ("silver", "Giá bạc", _C, "USD", "USD/oz", "spot", "global"),
    ("dau_wti", 0): ("wti", "Giá dầu WTI tương lai", _C, "USD", "USD/thùng", "futures", "us"),
    ("khi_thien_nhien", 0): ("natgas_hh", "Giá khí thiên nhiên Henry Hub", _C, "USD", "USD/MMBtu", "spot", "us"),
    ("than_newcastle", 0): ("coal_newcastle", "Giá than Newcastle", _C, "USD", "USD/tấn", "spot", "global"),
    ("than_coc", 0): ("coke_cn", "Giá than cốc Trung Quốc", _C, "CNY", "CNY/tấn", "spot", "cn"),
    ("khi_lpg_trung_quoc", 0): ("lpg_cn", "Giá khí LPG Trung Quốc", _C, "CNY", "CNY/tấn", "spot", "cn"),
    ("xang_dau", 1): ("gasoline_e5_vn", "Giá xăng E5 bán lẻ", _C, "VND", "VND/lít", "spot", "vn"),
    ("xang_dau", 2): ("diesel_vn", "Giá dầu diesel bán lẻ", _C, "VND", "VND/lít", "spot", "vn"),
    ("xang_dau", 3): ("kerosene_vn", "Giá dầu hoả bán lẻ", _C, "VND", "VND/lít", "spot", "vn"),
    ("ure_trung_dong", 0): ("urea_me", "Giá ure Trung Đông", _C, "USD", "USD/tấn", "spot", "global"),
    ("phan_ure", 0): ("urea_phumy", "Giá phân ure Phú Mỹ", _C, "VND", "VND/kg", "spot", "vn"),
    ("phan_ure", 1): ("urea_camau", "Giá phân ure Cà Mau", _C, "VND", "VND/kg", "spot", "vn"),
    ("phan_urea_trung_quoc", 0): ("urea_cn", "Giá phân urea Trung Quốc", _C, "CNY", "CNY/tấn", "spot", "cn"),
    ("luu_huynh", 0): ("sulfur_cn", "Giá lưu huỳnh Trung Quốc", _C, "CNY", "CNY/tấn", "spot", "cn"),
    ("phot_pho", 0): ("phosphorus_cn", "Giá phốt pho Trung Quốc", _C, "CNY", "CNY/tấn", "spot", "cn"),
    ("nhua_pvc_trung_quoc", 0): ("pvc_cn", "Giá nhựa PVC Trung Quốc", _C, "CNY", "CNY/tấn", "spot", "cn"),
    ("nhua_pp_trung_quoc", 0): ("pp_cn", "Giá nhựa PP Trung Quốc", _C, "CNY", "CNY/tấn", "spot", "cn"),
    ("pet_trung_quoc", 0): ("pet_cn", "Giá PET Trung Quốc", _C, "CNY", "CNY/tấn", "spot", "cn"),
    ("cao_su_nhat_ban", 0): ("rubber_rss3_jp", "Giá cao su RSS3 Nhật Bản", _C, "JPY", "JPY/kg", "spot", "jp"),
    ("hrc_trung_quoc", 0): ("hrc_cn", "Giá thép cuộn cán nóng Trung Quốc", _C, "CNY", "CNY/tấn", "spot", "cn"),
    ("thep_phe_anh", 0): ("scrap_steel_tr", "Giá thép phế CFR Thổ Nhĩ Kỳ", _C, "USD", "USD/tấn", "spot", "tr"),
    ("thep_thanh_anh", 0): ("rebar_tr", "Giá thép thanh Thổ Nhĩ Kỳ", _C, "USD", "USD/tấn", "spot", "tr"),
    ("ton_lanh_hoa_sen_045mm", 0): ("galv_sheet_hoasen", "Giá tôn lạnh Hoa Sen 0,45 mm", _C, "VND", "VND/m2", "spot", "vn"),
    ("ton_lanh_mau_hoa_sen_045mm", 0): ("galv_sheet_color_hoasen", "Giá tôn lạnh màu Hoa Sen 0,45 mm", _C, "VND", "VND/m2", "spot", "vn"),
    ("giay_gon_song_trung_quoc", 0): ("corrugated_paper_cn", "Giá giấy gợn sóng Trung Quốc", _C, "CNY", "CNY/tấn", "spot", "cn"),
    ("vai_coton", 0): ("cotton_fabric_cn", "Giá vải cotton Trung Quốc", _C, "CNY", "CNY/tấn", "spot", "cn"),
}

# Dải hợp lý của giá trị SAU khi nhân scale (spec Phụ lục C) — chốt (iii) trên điểm mới nhất.
BANDS: dict[str, tuple[float, float]] = {
    "VND": (1e11, 1e17), "USD": (-1e11, 1e12), "%": (-200, 400), "điểm": (10, 100),
    "người": (1e3, 3e8), "tấn": (1e3, 1e10), "lượt người": (1e6, 5e9),
    "VND/1 USD": (1e4, 1e5), "VND/kg": (1e3, 1e6), "VND/lượng": (1e7, 1e9), "VND/lít": (1e3, 1e5),
    "VND/m2": (1e4, 1e6), "USD/tấn": (10, 5000), "USD/oz": (1, 1e4), "USD/lb": (0.1, 20),
    "USD/thùng": (5, 500), "USD/MMBtu": (0.2, 100), "CNY/tấn": (50, 5e5), "MYR/tấn": (100, 5e4),
    "JPY/kg": (10, 5e3),
}


def load_doc(md_path: Path = WICHART_MD) -> tuple[dict, list[str]]:
    """Trả (WICHART, TIER_X) từ khối Python cuối cùng của tài liệu nguồn."""
    blocks = re.findall(r"```python\n(.*?)```", md_path.read_text(encoding="utf-8"), re.S)
    if not blocks:
        raise RegistryError(f"không thấy khối Python trong {md_path}")
    ns: dict = {}
    exec(compile(blocks[-1], "wichart_registry_doc", "exec"), ns)  # noqa: S102 — tài liệu trong repo, cùng cách verify_wichart.py
    return ns["WICHART"], list(ns["TIER_X"])


def build(md_path: Path = WICHART_MD) -> list[Series]:
    doc, tier_x = load_doc(md_path)
    out: list[Series] = []
    ours: dict[tuple[str, int], str] = {**{k: "macro" for k in MACRO}, **{k: "asset" for k in ASSET}}
    for (key, idx), domain in ours.items():
        meta = doc.get(key)
        if meta is None or meta.get("tier") == "X" or key in tier_x:
            raise RegistryError(f"{key}[{idx}] có trong module nhưng §9 không thu thập (thiếu hoặc Tier X)")
        if idx >= len(meta["s"]):
            raise RegistryError(f"{key}[{idx}] vượt số series §9 ({len(meta['s'])})")
        doc_name, unit_doc, scale, role, flags = meta["s"][idx]
        if role is None:
            raise RegistryError(f"{key}[{idx}] §9 đánh dấu không nạp (role None) mà module vẫn map")
        common = dict(key=key, idx=idx, group=meta["g"], domain=domain, doc_name=doc_name,
                      scale=Decimal(str(scale)), freq=meta.get("freq", "d"), role=role, flags=tuple(flags))
        if domain == "macro":
            code, name_vi = MACRO[(key, idx)]
            out.append(Series(code=code, name_vi=name_vi, unit=unit_doc, **common))
        else:
            code, name_vi, cls, ccy, unit, ptype, region = ASSET[(key, idx)]
            out.append(Series(code=code, name_vi=name_vi, unit=unit, asset_class=cls, quote_currency=ccy,
                              price_type=ptype, region=region, **common))
    for key, meta in doc.items():
        if meta.get("tier") == "X" or key in tier_x:
            continue
        for idx, s in enumerate(meta["s"]):
            if s[3] is not None and (key, idx) not in ours:
                raise RegistryError(f"§9 thu thập {key}[{idx}] ({s[0]!r}) mà module chưa map")
    if len({s.code for s in out}) != len(out):
        raise RegistryError("mã trùng trong module")
    return out


def key_groups(series: list[Series]) -> list[tuple[str, str]]:
    """Mỗi key một lần, giữ thứ tự xuất hiện, kèm namespace để dựng URL."""
    seen: dict[str, str] = {}
    for s in series:
        seen.setdefault(s.key, s.group)
    return list(seen.items())
```

- [ ] **Step 5: Chạy test, xanh**

Run: `uv run pytest tests/etl/test_e36_wichart_registry.py -q`
Expected: `7 passed`. Nếu `test_build_resolves…` báo số khác 53/52, đối chiếu lại Phụ lục A/B của spec với khối §9 — **không** sửa số expected.

- [ ] **Step 6: Commit**

```bash
git add docs/10-sources/macro/wichart.md backend/etl/wichart_registry.py backend/tests/etl/test_e36_wichart_registry.py
git commit -m "feat(etl): WiChart registry - doc block joined with our codes, mismatch raises

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 2: Fetch — một key một lời gọi, retry, get bơm được

**Files:**
- Create: `backend/etl/wichart_fetch.py`
- Test: `backend/tests/etl/test_e37_wichart_fetch.py`

**Interfaces:**
- Produces: `url(key, group) -> str`, `classify(http, text) -> tuple[str, dict | None]`, `FetchError`, `BadShape`, `Fetcher(get, sleep, clock)` với `fetch_one(key, group) -> tuple[dict, str]`, thuộc tính `calls`, `retries`; `open_fetcher(get=None, sleep=time.sleep, clock=time.monotonic)` context manager. `get(url: str, timeout: float) -> tuple[int, str]`.

- [ ] **Step 1: Test đỏ**

`backend/tests/etl/test_e37_wichart_fetch.py`:

```python
import json
import pathlib

import pytest

from etl import wichart_fetch as wf

FIX = pathlib.Path(__file__).parent / "fixtures" / "wichart"
CPI = (FIX / "cpi.json").read_text(encoding="utf-8")


def test_url_uses_hang_hoa_namespace_only_for_commodities():
    assert wf.url("cpi", "vi_mo") == "https://api.wichart.vn/vietnambiz/vi-mo?name=cpi"
    assert wf.url("vang", "hang_hoa") == "https://api.wichart.vn/vietnambiz/vi-mo?key=hang_hoa&name=vang"


def test_classify_ok_retry_bad_shape():
    verdict, doc = wf.classify(200, CPI)
    assert verdict == "ok" and doc["timeUpdate"] == "Tháng 08/2026"
    assert wf.classify(500, '{"message":"Có lỗi xảy ra"}') == ("retry", None)
    assert wf.classify(200, "<html>") == ("retry", None)
    assert wf.classify(200, json.dumps({"title": "x", "chart": {}})) == ("bad_shape", None)
    assert wf.classify(200, json.dumps({"chart": {"series": []}}))[0] == "ok"       # rỗng là chuyện của normalize


def test_fetch_one_retries_a_500_then_returns_the_doc():
    answers = [(500, "boom"), (200, CPI)]
    slept = []
    f = wf.Fetcher(get=lambda u, t: answers.pop(0), sleep=slept.append, clock=lambda: 0.0)
    doc, text = f.fetch_one("cpi", "vi_mo")
    assert doc["timeUpdate"] == "Tháng 08/2026" and text == CPI
    assert f.calls == 2 and f.retries == 1 and slept == [2]                       # BACKOFF[0]


def test_fetch_one_raises_after_four_failures_including_transport_errors():
    import httpx
    def get(u, t):
        raise httpx.ReadTimeout("slow")
    f = wf.Fetcher(get=get, sleep=lambda s: None, clock=lambda: 0.0)
    with pytest.raises(wf.FetchError, match="cpi hỏng sau 4 lần"):
        f.fetch_one("cpi", "vi_mo")
    assert f.calls == 4 and f.retries == 3


def test_bad_shape_is_not_retried():
    f = wf.Fetcher(get=lambda u, t: (200, json.dumps({"chart": {}})), sleep=lambda s: None, clock=lambda: 0.0)
    with pytest.raises(wf.BadShape):
        f.fetch_one("cpi", "vi_mo")
    assert f.calls == 1


def test_min_interval_sleeps_between_two_calls():
    clock = iter([0.0, 0.0, 0.05, 0.05, 1.0, 1.0])
    slept = []
    f = wf.Fetcher(get=lambda u, t: (200, CPI), sleep=slept.append, clock=lambda: next(clock))
    f.fetch_one("cpi", "vi_mo")
    f.fetch_one("cpi", "vi_mo")
    assert slept and abs(slept[0] - 0.15) < 1e-9                                   # MIN_INTERVAL 0.2 − 0.05
```

- [ ] **Step 2: Chạy, đỏ vì thiếu module**

Run: `uv run pytest tests/etl/test_e37_wichart_fetch.py -q`
Expected: collection error `ModuleNotFoundError: etl.wichart_fetch`.

- [ ] **Step 3: Module**

`backend/etl/wichart_fetch.py`:

```python
"""Tải một key WiChart (spec §5.2). I/O thuần; `get` bơm được để test không mở kết nối.

Đo 2026-09-05: 90 lời gọi liên tiếp không giãn cách sạch — MIN_INTERVAL chỉ để lịch sự.
"""
from __future__ import annotations

import contextlib
import json
import time

import httpx

BASE = "https://api.wichart.vn/vietnambiz/vi-mo"
TIMEOUT = 30.0
RETRIES = 3
BACKOFF = (2, 4, 8)
MIN_INTERVAL = 0.2
HEADERS = {"Accept-Encoding": "gzip",
           "User-Agent": "dulieuchungkhoan.vn/etl (dulieuchungkhoan.official@gmail.com)"}


def url(key: str, group: str) -> str:
    return f"{BASE}?key=hang_hoa&name={key}" if group == "hang_hoa" else f"{BASE}?name={key}"


def classify(http: int, text: str) -> tuple[str, dict | None]:
    """('ok', doc) | ('retry', None) | ('bad_shape', None)."""
    if http != 200:
        return "retry", None
    try:
        d = json.loads(text)
    except ValueError:
        return "retry", None
    series = (d.get("chart") or {}).get("series") if isinstance(d, dict) else None
    if not isinstance(series, list):
        return "bad_shape", None
    return "ok", d


class FetchError(Exception):
    """Một key hỏng sau mọi lần thử — key đó CHƯA nạp, không ghi gì."""


class BadShape(Exception):
    """Response hợp lệ nhưng không có chart.series — nguồn đổi hình dạng, thử lại vô ích."""


class Fetcher:
    def __init__(self, get, sleep=time.sleep, clock=time.monotonic):
        self._get, self._sleep, self._clock = get, sleep, clock
        self.calls = 0
        self.retries = 0
        self._last: float | None = None

    def _request(self, u: str) -> tuple[int, str]:
        if self._last is not None:
            wait = MIN_INTERVAL - (self._clock() - self._last)
            if wait > 0:
                self._sleep(wait)
        self._last = self._clock()
        self.calls += 1
        return self._get(u, TIMEOUT)

    def fetch_one(self, key: str, group: str) -> tuple[dict, str]:
        u = url(key, group)
        http, text = 0, ""
        for attempt in range(RETRIES + 1):
            try:
                http, text = self._request(u)
            except httpx.HTTPError as e:
                # Timeout/đứt kết nối đi CÙNG đường với response xấu (bài học lát 3, e7f80f6)
                http, text = 0, f"{type(e).__name__}: {e}"
            verdict, doc = classify(http, text)
            if verdict == "ok":
                return doc, text
            if verdict == "bad_shape":
                raise BadShape(f"{key}: response không có chart.series")
            if attempt == RETRIES:
                break
            self._sleep(BACKOFF[attempt])
            self.retries += 1
        raise FetchError(f"{key} hỏng sau {RETRIES + 1} lần (HTTP {http}): {text[:200]}")


@contextlib.contextmanager
def open_fetcher(get=None, sleep=time.sleep, clock=time.monotonic):
    if get is not None:                            # test tiêm get giả, không mở kết nối
        yield Fetcher(get, sleep, clock)
        return
    with httpx.Client(headers=HEADERS) as client:  # MỘT client cho trọn lượt
        def get_one(u: str, timeout: float) -> tuple[int, str]:
            r = client.get(u, timeout=timeout)
            return r.status_code, r.text
        yield Fetcher(get_one, sleep, clock)
```

- [ ] **Step 4: Chạy, xanh**

Run: `uv run pytest tests/etl/test_e37_wichart_fetch.py -q` → `6 passed`.

- [ ] **Step 5: Commit**

```bash
git add backend/etl/wichart_fetch.py backend/tests/etl/test_e37_wichart_fetch.py
git commit -m "feat(etl): WiChart fetcher - classify, retry with backoff, injectable get

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 3: Normalize — neo kỳ, nhân scale, dải, cuối tuần

**Files:**
- Create: `backend/etl/wichart_normalize.py`
- Test: `backend/tests/etl/test_e38_wichart_normalize.py`

**Interfaces:**
- Consumes: `Series`, `BANDS` từ Task 1.
- Produces: `Point(domain, code, obs_date: date, value: Decimal, price_type: str | None)` frozen; `SeriesError(reason, msg)` với `reason ∈ {'shape','freq','band'}`; `real_freq(epochs) -> str | None`; `anchor(day, freq) -> date`; `series_points(series, api_series: list[dict]) -> list[Point]`; `drop_weekend_carry(points) -> list[Point]`; `VN`.

- [ ] **Step 1: Test đỏ**

`backend/tests/etl/test_e38_wichart_normalize.py`:

```python
"""Expected là literal đọc tay từ fixture (chụp 2026-09-05) hoặc giải tay — không tính lại theo code."""
import dataclasses
import json
import pathlib
from datetime import date
from decimal import Decimal

import pytest

from etl import wichart_normalize as wn
from etl import wichart_registry as wr

FIX = pathlib.Path(__file__).parent / "fixtures" / "wichart"
REG = {(s.key, s.idx): s for s in wr.build()}


def _series(key):
    return json.loads((FIX / f"{key}.json").read_text(encoding="utf-8"))["chart"]["series"]


def _last(points):
    return max(points, key=lambda p: p.obs_date)


def test_month_anchors_on_day_one_in_vietnam_time_not_utc():
    pts = wn.series_points(REG[("cpi", 0)], _series("cpi"))
    last = _last(pts)
    assert last.obs_date == date(2026, 8, 1) and last.value == Decimal("4.45")   # epoch 1785517200000 = 01/08 00:00 VN
    assert last.obs_date != date(2026, 7, 31)                                  # parse UTC sẽ ra 31/07
    assert last.domain == "macro" and last.code == "vn.cpi" and last.price_type is None


def test_quarter_anchors_on_first_month_of_the_quarter_and_scale_1e9():
    pts = wn.series_points(REG[("gdp", 0)], _series("gdp"))
    last = _last(pts)
    assert last.obs_date == date(2026, 4, 1)                                    # nguồn neo 01/06 = Q2
    assert last.value == Decimal("3479487.23") * Decimal("1000000000")          # 3,479,487.23 tỷ VND
    growth = _last(wn.series_points(REG[("gdp", 2)], _series("gdp")))
    assert growth.value == Decimal("8") and growth.code == "vn.gdp.growth"      # 0.08 × 100


def test_year_anchors_on_january_first_even_when_source_anchors_december():
    last = _last(wn.series_points(REG[("ds", 0)], _series("ds")))
    assert last.obs_date == date(2025, 1, 1) and last.value == Decimal("102345320")   # 102,345.32 nghìn người


def test_td_is_credit_even_though_source_names_it_deposits():
    pts = wn.series_points(REG[("td", 0)], _series("td"))
    assert pts and all(p.code == "vn.credit" for p in pts)
    assert _last(pts).value == Decimal("20150411") * Decimal("1000000000")


def test_asset_scale_and_unit_gold_cotton_fuel():
    gold = _last(wn.series_points(REG[("vang", 0)], _series("vang")))
    assert gold.value == Decimal("145600000") and gold.code == "gold.sjc_buy" and gold.price_type == "spot"
    cotton = _last(wn.series_points(REG[("vai_cotton_my", 0)], _series("vai_cotton_my")))
    assert cotton.value == Decimal("0.8233") and cotton.obs_date == date(2026, 9, 4)
    e5 = _last(wn.series_points(REG[("xang_dau", 1)], _series("xang_dau")))
    assert e5.value == Decimal("22480") and e5.code == "gasoline_e5_vn"


def test_weekend_point_equal_to_previous_is_dropped_but_a_different_one_is_kept():
    by_date = {p.obs_date: p.value for p in wn.series_points(REG[("lua", 0)], _series("lua"))}
    assert date(2024, 10, 5) not in by_date and by_date[date(2024, 10, 4)] == Decimal("8458")   # T7 chép lại T6
    assert by_date[date(2025, 3, 23)] == Decimal("7029")                                        # CN khác T7 (6750)
    gold = {p.obs_date: p.value for p in wn.series_points(REG[("vang_the_gioi", 0)], _series("vang_the_gioi"))}
    assert date(2024, 11, 16) not in gold and gold[date(2024, 11, 15)] == Decimal("2561.24")
    assert gold[date(2024, 9, 8)] == Decimal("2496.93")
    fx = {p.obs_date: p.value for p in wn.series_points(REG[("dhtg", 0)], _series("dhtg"))}
    assert date(2025, 1, 25) not in fx and fx[date(2025, 4, 26)] == Decimal("24963")


def test_weekday_repeat_is_kept_and_macro_weekend_is_kept():
    lua = {p.obs_date: p.value for p in wn.series_points(REG[("lua", 0)], _series("lua"))}
    # 27/08 và 26/08/2026 đều 7550 (điểm cuối fixture) — chép lại TRONG TUẦN phải giữ
    assert lua[date(2026, 8, 27)] == Decimal("7550") and lua[date(2026, 8, 26)] == Decimal("7550")
    # macro chuỗi ngày: điểm T7 bằng T6 vẫn giữ (không áp luật cuối tuần)
    s = dataclasses.replace(REG[("lslnh", 0)])
    api = [{"name": "LS qua đêm liên ngân hàng", "unit": "%",
            "data": [[1756400400000, 4.1], [1756486800000, 4.1], [1756573200000, 4.1]]}]   # 29/08 T6 · 30/08 T7 · 31/08 CN 2026
    pts = wn.series_points(s, api)
    assert [p.obs_date for p in pts] == [date(2026, 8, 29), date(2026, 8, 30), date(2026, 8, 31)]


def test_name_mismatch_freq_mismatch_band_and_bad_anchor_raise_with_reason():
    with pytest.raises(wn.SeriesError) as e:
        wn.series_points(REG[("cpi", 0)], [{"name": "Lạm phát lõi", "data": [[1785517200000, 4.45]]}])
    assert e.value.reason == "shape"
    with pytest.raises(wn.SeriesError) as e:
        wn.series_points(dataclasses.replace(REG[("cpi", 0)], freq="d"), _series("cpi"))
    assert e.value.reason == "freq"
    with pytest.raises(wn.SeriesError) as e:                                   # 141.3 × 1e3 = 141.300 < 1e7
        wn.series_points(REG[("vang", 0)], [{"name": "Giá vàng mua vào", "data": [[1788454800000, 141.3]]},
                                           {"name": "Giá vàng bán ra", "data": [[1788454800000, 148.6]]}])
    assert e.value.reason == "band"
    with pytest.raises(wn.SeriesError) as e:                                   # quý neo tháng 5 — không phải tháng cuối quý
        wn.series_points(REG[("tn", 0)], [{"name": "Tỷ lệ thất nghiệp", "data": [[1777568400000, 2.2]]}])  # 01/05/2026 VN
    assert e.value.reason == "shape"
    with pytest.raises(wn.SeriesError) as e:
        wn.series_points(REG[("vang", 1)], [{"name": "Giá vàng mua vào", "data": [[1, 1]]}])   # thiếu series [1]
    assert e.value.reason == "shape"


def test_real_freq_and_anchor_helpers():
    assert wn.real_freq([0, 86_400_000, 2 * 86_400_000]) == "d"
    assert wn.real_freq([1785517200000, 1782838800000, 1780246800000]) == "m"
    assert wn.real_freq([0, 1]) is None
    assert wn.anchor(date(2026, 6, 1), "q") == date(2026, 4, 1)
    assert wn.anchor(date(2025, 12, 31), "y") == date(2025, 1, 1)
    assert wn.anchor(date(2026, 8, 15), "m") == date(2026, 8, 1)
    assert wn.anchor(date(2026, 9, 4), "d") == date(2026, 9, 4)
```

- [ ] **Step 2: Chạy, đỏ vì thiếu module**

Run: `uv run pytest tests/etl/test_e38_wichart_normalize.py -q` → `ModuleNotFoundError: etl.wichart_normalize`.

- [ ] **Step 3: Module**

`backend/etl/wichart_normalize.py`:

```python
"""Chuẩn hoá một series WiChart thành điểm ghi kho (spec §5.3). Thuần, không I/O.

Luật đo được (spec §2.1): epoch = 00:00 giờ VN · tháng neo ngày 1 · quý neo THÁNG CUỐI quý · năm bất
nhất (12-01 hoặc 01-01) · kho neo ĐẦU kỳ · điểm cuối tuần chỉ bỏ khi là chép lại của điểm liền trước.
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from etl.wichart_registry import BANDS, Series

VN = ZoneInfo("Asia/Ho_Chi_Minh")
QUARTER_END_TO_START = {3: 1, 6: 4, 9: 7, 12: 10}
NAME_PREFIX = 18


@dataclass(frozen=True)
class Point:
    domain: str
    code: str
    obs_date: date
    value: Decimal
    price_type: str | None


class SeriesError(Exception):
    def __init__(self, reason: str, msg: str):
        self.reason = reason            # 'shape' | 'freq' | 'band'
        super().__init__(msg)


def real_freq(epochs: list[int]) -> str | None:
    ts = sorted(set(epochs))
    if len(ts) < 3:
        return None
    med = statistics.median((b - a) / 86_400_000 for a, b in zip(ts, ts[1:]))
    return "d" if med <= 4 else "m" if med <= 45 else "q" if med <= 120 else "y"


def anchor(day: date, freq: str) -> date:
    if freq == "d":
        return day
    if freq == "m":
        return day.replace(day=1)
    if freq == "q":
        if day.month not in QUARTER_END_TO_START:
            raise SeriesError("shape", f"quý neo tháng {day.month}, không phải tháng cuối quý")
        return date(day.year, QUARTER_END_TO_START[day.month], 1)
    if freq == "y":
        return date(day.year, 1, 1)
    raise ValueError(f"freq lạ: {freq!r}")


def drop_weekend_carry(points: list[Point]) -> list[Point]:
    """Bỏ điểm T7/CN có giá trị bằng đúng điểm liền trước (theo thứ tự nguồn). Chép lại trong tuần giữ."""
    out: list[Point] = []
    prev: Point | None = None
    for p in points:
        if prev is not None and p.obs_date.weekday() >= 5 and p.value == prev.value:
            prev = p
            continue
        out.append(p)
        prev = p
    return out


def series_points(s: Series, api_series: list[dict]) -> list[Point]:
    if s.idx >= len(api_series):
        raise SeriesError("shape", f"{s.key}[{s.idx}] thiếu series (API trả {len(api_series)})")
    api = api_series[s.idx]
    api_name = (api.get("name") or "").strip()
    if "NAMEWRONG" not in s.flags:
        want = s.doc_name[:NAME_PREFIX]
        if not (api_name.startswith(want) or s.doc_name.startswith(api_name[:NAME_PREFIX])):
            raise SeriesError("shape", f"{s.key}[{s.idx}] tên series {api_name!r} ≠ {s.doc_name!r}")
    raw = [p for p in api.get("data") or []
           if isinstance(p, list) and len(p) == 2 and isinstance(p[1], (int, float)) and not isinstance(p[1], bool)]
    if not raw:
        raise SeriesError("shape", f"{s.key}[{s.idx}] không có điểm số")
    rf = real_freq([p[0] for p in raw])
    if rf is not None and rf != s.freq:
        raise SeriesError("freq", f"{s.key}[{s.idx}] tần suất thật {rf} ≠ {s.freq} khai ở §9")
    pts: list[Point] = []
    for epoch, v in sorted(raw, key=lambda p: p[0]):
        day = datetime.fromtimestamp(epoch / 1000, tz=VN).date()
        pts.append(Point(s.domain, s.code, anchor(day, s.freq), Decimal(str(v)) * s.scale, s.price_type))
    band = BANDS.get(s.unit)
    latest = pts[-1]
    if band and latest.value != 0 and not (Decimal(str(band[0])) <= abs(latest.value) <= Decimal(str(band[1]))):
        raise SeriesError("band", f"{s.key}[{s.idx}] giá trị mới nhất {latest.value} ngoài dải {band} ({s.unit})")
    if s.domain == "asset" and s.calendar == "trading_days":
        pts = drop_weekend_carry(pts)
    dedup: dict[date, Point] = {}
    for p in pts:                                   # hai điểm cùng ngày sau neo → giữ điểm sau (PK không nổ)
        dedup[p.obs_date] = p
    return list(dedup.values())
```

- [ ] **Step 4: Chạy, xanh**

Run: `uv run pytest tests/etl/test_e38_wichart_normalize.py -q` → `9 passed`.

Nếu `test_weekday_repeat…` đỏ vì 26/08 không phải 7550 trong fixture, **đọc fixture** (`lua.json`, hai điểm cuối) và sửa expected theo fixture — literal đó phải là số thật, không phải số code tính.

- [ ] **Step 5: Commit**

```bash
git add backend/etl/wichart_normalize.py backend/tests/etl/test_e38_wichart_normalize.py
git commit -m "feat(etl): WiChart normalize - VN-time anchoring to period start, scale, unit band, weekend carry-forward drop

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 4: Guard

**Files:**
- Create: `backend/etl/wichart_guard.py`
- Test: `backend/tests/etl/test_e39_wichart_guard.py`

**Interfaces:**
- Produces: `Tally(keys_total, keys_failed, keys_bad_shape, series_total, series_shape, series_freq, series_band, series_ok)`, `Verdict(ok, reasons)`, `check(t) -> Verdict`, hằng `MIN_SAMPLE=20, MAX_FAILED=0.20, MAX_SHAPE=0.05, MAX_BAND=0.05`.

- [ ] **Step 1: Test đỏ**

```python
from etl import wichart_guard as wg


def _t(**kw):
    base = dict(keys_total=68, keys_failed=0, keys_bad_shape=0, series_total=105,
                series_shape=0, series_freq=0, series_band=0, series_ok=105)
    base.update(kw)
    return wg.Tally(**base)


def test_clean_run_passes_and_zero_changes_is_not_an_error():
    assert wg.check(_t()).ok


def test_failed_keys_threshold_is_twenty_percent_inclusive():
    assert wg.check(_t(keys_total=20, keys_failed=4)).ok                       # 20 % — chưa vượt
    v = wg.check(_t(keys_total=20, keys_failed=5))                              # 25 %
    assert not v.ok and "hỏng" in v.reasons[0] and "5/20" in v.reasons[0]


def test_shape_and_band_thresholds_are_five_percent_of_series():
    assert wg.check(_t(series_total=20, series_shape=1)).ok
    assert not wg.check(_t(series_total=20, series_shape=2)).ok
    assert wg.check(_t(series_total=20, series_band=1)).ok
    v = wg.check(_t(series_total=20, series_band=2))
    assert not v.ok and "dải" in v.reasons[0]


def test_freq_drift_is_reported_not_refused():
    assert wg.check(_t(series_freq=50)).ok


def test_below_min_sample_nothing_refuses():
    assert wg.check(_t(keys_total=19, keys_failed=19, series_total=19, series_shape=19, series_band=19)).ok
```

- [ ] **Step 2: Đỏ** — `uv run pytest tests/etl/test_e39_wichart_guard.py -q` → `ModuleNotFoundError`.

- [ ] **Step 3: Module**

```python
"""Chốt chặn một lượt `etl wichart` (spec §5.4). Thuần; đánh giá TRƯỚC khi mở giao dịch ghi."""
from __future__ import annotations

from dataclasses import dataclass, field

MIN_SAMPLE = 20
MAX_FAILED = 0.20
MAX_SHAPE = 0.05
MAX_BAND = 0.05


@dataclass
class Tally:
    keys_total: int = 0
    keys_failed: int = 0        # hỏng sau mọi lần thử
    keys_bad_shape: int = 0     # response không có chart.series — mọi series của key tính vào series_shape
    series_total: int = 0
    series_shape: int = 0       # thiếu series / tên lệch / quý neo sai / key bad_shape
    series_freq: int = 0        # tần suất thật ≠ khai — chỉ báo
    series_band: int = 0        # giá trị mới nhất ngoài dải đơn vị
    series_ok: int = 0


@dataclass
class Verdict:
    ok: bool
    reasons: list[str] = field(default_factory=list)


def check(t: Tally) -> Verdict:
    reasons: list[str] = []
    if t.keys_total >= MIN_SAMPLE:
        rate = t.keys_failed / t.keys_total
        if rate > MAX_FAILED:
            reasons.append(f"tỷ lệ key hỏng {rate:.1%} > {MAX_FAILED:.0%} ({t.keys_failed}/{t.keys_total}) — nguồn sự cố")
    if t.series_total >= MIN_SAMPLE:
        for n, cap, label in ((t.series_shape, MAX_SHAPE, "series sai hình dạng"),
                              (t.series_band, MAX_BAND, "series ngoài dải đơn vị")):
            rate = n / t.series_total
            if rate > cap:
                reasons.append(f"tỷ lệ {label} {rate:.1%} > {cap:.0%} ({n}/{t.series_total}) — nguồn đổi cấu trúc/thang")
    return Verdict(ok=not reasons, reasons=reasons)
```

- [ ] **Step 4: Xanh** — `5 passed`.
- [ ] **Step 5: Commit** — `feat(etl): WiChart guard - failed-key, shape and band ratios`.

---

### Task 5: Store — registry upsert, apply đếm changed, series_break, raw_payload, domain state

**Files:**
- Create: `backend/etl/wichart_store.py`
- Test: `backend/tests/etl/test_e40_wichart_store.py`

**Interfaces:**
- Consumes: `Series`, `build()`, `SOURCE` (Task 1); `Point` (Task 3); `Verdict` (Task 4); `omo_store.open_run/close_run`.
- Produces: `JOB = "macro.wichart"`; `Resolved(domain, row_id, price_type)`; `load_registry(conn, series) -> tuple[dict[str, Resolved], dict]` (map theo `code`, và stats `{"macro": n, "asset": n, "deactivated": n}`); `Written(inserted, changed)`; `apply(conn, points, resolved) -> Written`; `seed_series_break(conn) -> None`; `store_payload_if_changed(conn, key, text, run_id) -> bool`; `store_refusal_evidence(engine, texts: dict[str, str], run_id, verdict)`; `upsert_domain_state(engine, watermark: str)`.

- [ ] **Step 1: Test đỏ**

`backend/tests/etl/test_e40_wichart_store.py`:

```python
"""Ghi kho thật (fixture `db` = một giao dịch, rollback cuối test)."""
from datetime import date
from decimal import Decimal

import sqlalchemy as sa

from etl import wichart_registry as wr
from etl import wichart_store as ws
from etl.wichart_normalize import Point


def _count(db, sql, **p):
    return db.execute(sa.text(sql), p).scalar()


def test_load_registry_upserts_53_indicators_and_52_assets_idempotently(db):
    series = wr.build()
    resolved, stats = ws.load_registry(db, series)
    assert stats == {"macro": 53, "asset": 52, "deactivated": 0}
    assert len(resolved) == 105 and resolved["vn.cpi"].domain == "macro" and resolved["wti"].price_type == "futures"
    n_ind = _count(db, "SELECT count(*) FROM macro.indicator WHERE code LIKE 'vn.%'")
    n_src = _count(db, "SELECT count(*) FROM macro.indicator_source WHERE source = 'wichart'")
    n_ast = _count(db, "SELECT count(*) FROM asset.asset_external_id WHERE source = 'wichart'")
    assert (n_ind, n_src, n_ast) == (53, 53, 52)
    first_id = resolved["vn.cpi"].row_id
    resolved2, stats2 = ws.load_registry(db, series)                      # lượt hai: không nhân đôi, id giữ
    assert stats2 == stats and resolved2["vn.cpi"].row_id == first_id
    assert _count(db, "SELECT count(*) FROM macro.indicator_source WHERE source = 'wichart'") == 53
    row = db.execute(sa.text("SELECT external_key, external_sub, scale, active FROM macro.indicator_source s"
                             " JOIN macro.indicator i USING (indicator_id) WHERE i.code = 'vn.credit'")).one()
    assert tuple(row) == ("td", "0", Decimal("1000000000"), True)
    row = db.execute(sa.text("SELECT a.asset_class, a.quote_currency, a.unit, a.calendar, x.price_type, x.scale"
                             " FROM asset.asset a JOIN asset.asset_external_id x USING (asset_id) WHERE a.code = 'cotton_us'")).one()
    assert tuple(row) == ("commodity", "USD", "USD/lb", "trading_days", "spot", Decimal("0.01"))


def test_series_missing_from_registry_is_deactivated_not_deleted(db):
    series = wr.build()
    ws.load_registry(db, series)
    trimmed = [s for s in series if s.code != "vn.pmi"]
    _, stats = ws.load_registry(db, trimmed)
    assert stats["deactivated"] == 1
    assert _count(db, "SELECT count(*) FROM macro.indicator WHERE code = 'vn.pmi'") == 1
    assert db.execute(sa.text("SELECT active FROM macro.indicator_source WHERE source='wichart' AND external_key='pmi'")).scalar() is False
    _, stats = ws.load_registry(db, series)                               # quay lại: active = true
    assert db.execute(sa.text("SELECT active FROM macro.indicator_source WHERE source='wichart' AND external_key='pmi'")).scalar() is True


def test_apply_counts_inserted_then_changed_and_leaves_unchanged_rows_untouched(db):
    resolved, _ = ws.load_registry(db, wr.build())
    pts = [Point("macro", "vn.cpi", date(2026, 7, 1), Decimal("3.19"), None),
           Point("macro", "vn.cpi", date(2026, 8, 1), Decimal("4.45"), None),
           Point("asset", "gold.sjc_buy", date(2026, 9, 4), Decimal("145600000"), "spot")]
    w = ws.apply(db, pts, resolved)
    assert (w.inserted, w.changed) == (3, 0)
    ts1 = _count(db, "SELECT max(ingested_at) FROM macro.observation o JOIN macro.indicator i USING (indicator_id) WHERE i.code='vn.cpi'")
    w = ws.apply(db, pts, resolved)                                         # chạy lại: không chạm dòng nào
    assert (w.inserted, w.changed) == (0, 0)
    assert _count(db, "SELECT max(ingested_at) FROM macro.observation o JOIN macro.indicator i USING (indicator_id) WHERE i.code='vn.cpi'") == ts1
    pts[1] = Point("macro", "vn.cpi", date(2026, 8, 1), Decimal("4.50"), None)   # vá hồi tố một điểm
    w = ws.apply(db, pts, resolved)
    assert (w.inserted, w.changed) == (0, 1)
    got = dict(db.execute(sa.text("SELECT obs_date, value FROM macro.observation o JOIN macro.indicator i USING (indicator_id)"
                                  " WHERE i.code='vn.cpi'")).all())
    assert got == {date(2026, 7, 1): Decimal("3.19"), date(2026, 8, 1): Decimal("4.50")}
    assert _count(db, "SELECT value FROM asset.price_daily p JOIN asset.asset a USING (asset_id)"
                      " WHERE a.code='gold.sjc_buy' AND price_type='spot'") == Decimal("145600000")


def test_series_break_seed_makes_the_spliced_view_scale_the_old_segment(db):
    resolved, _ = ws.load_registry(db, wr.build())
    ws.apply(db, [Point("macro", "vn.gdp.real", date(2025, 10, 1), Decimal("1642683"), None),
                  Point("macro", "vn.gdp.real", date(2026, 1, 1), Decimal("2401927"), None)], resolved)
    ws.seed_series_break(db)
    ws.seed_series_break(db)                                                # idempotent
    rows = dict(db.execute(sa.text("SELECT obs_date, value_spliced FROM macro.observation_spliced v"
                                   " JOIN macro.indicator i USING (indicator_id) WHERE i.code='vn.gdp.real'")).all())
    assert rows[date(2025, 10, 1)] == Decimal("1642683") * Decimal("1.6005")   # đoạn CŨ × hệ số
    assert rows[date(2026, 1, 1)] == Decimal("2401927")                        # từ 01/03/2026 nền mới — 01/01 vẫn cũ? xem ghi chú
    n = db.execute(sa.text("SELECT count(*), max(factor), max(verified_at)::date FROM macro.series_break")).one()
    assert n[0] == 1 and n[1] == Decimal("1.6005") and n[2] == date(2026, 9, 5)
```

⚠️ Ghi chú cho assert thứ hai của test `series_break`: break_date là `2026-03-01` (điểm ĐẦU TIÊN thuộc nền mới, theo neo **đầu kỳ** = Q1/2026 → `2026-01-01`?). Đọc lại [wichart.md Bẫy 6](../../../10-sources/macro/wichart.md): nhảy tại "2026-03" theo neo **của nguồn** (tháng cuối quý) = Q1/2026; theo neo đầu kỳ của kho, Q1/2026 = `2026-01-01`. **Vậy `break_date` trong kho phải là `2026-01-01`**, không phải `2026-03-01` như spec §5.5 chép từ tài liệu nguồn. Implementer: dùng `date(2026, 1, 1)`; view nhân hệ số cho `obs_date < break_date` ⇒ `2025-10-01` × 1,6005, `2026-01-01` giữ nguyên — đúng như assert. Ghi vào ledger là ruling; kiến trúc sư sửa spec §5.5 cùng lượt.

```python
def test_payload_is_stored_only_when_its_hash_changes(db):
    assert ws.store_payload_if_changed(db, "cpi", '{"a":1}', run_id=1) is True
    assert ws.store_payload_if_changed(db, "cpi", '{"a":1}', run_id=2) is False
    assert ws.store_payload_if_changed(db, "cpi", '{"a":2}', run_id=3) is True
    rows = db.execute(sa.text("SELECT endpoint_key, meta->>'run_id' FROM staging.raw_payload"
                              " WHERE source='wichart' ORDER BY payload_id")).all()
    assert [tuple(r) for r in rows] == [("wichart:cpi", "1"), ("wichart:cpi", "3")]


def test_store_works_under_etl_role(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    resolved, stats = ws.load_registry(db, wr.build())
    assert stats["macro"] == 53
    w = ws.apply(db, [Point("macro", "vn.cpi", date(2026, 8, 1), Decimal("4.45"), None),
                      Point("asset", "wti", date(2026, 9, 4), Decimal("62.1"), "futures")], resolved)
    assert w.inserted == 2
    ws.seed_series_break(db)
    assert ws.store_payload_if_changed(db, "cpi", '{"x":1}', run_id=9) is True
```

- [ ] **Step 2: Đỏ** — `uv run pytest tests/etl/test_e40_wichart_store.py -q` → `ModuleNotFoundError`.

- [ ] **Step 3: Module**

`backend/etl/wichart_store.py`:

```python
"""Ghi kho cho `etl wichart` (spec §5.5). SQL thuần; hai miền trong cùng giao dịch của caller."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

import sqlalchemy as sa

from etl.wichart_guard import Verdict
from etl.wichart_normalize import Point
from etl.wichart_registry import SOURCE, Series

JOB = "macro.wichart"
DOMAINS = ("macro.indicator", "asset")
CHUNK = 5000
# Đứt gãy GDP giá so sánh: nguồn nhảy tại kỳ nguồn neo "2026-03" = Q1/2026; kho neo đầu kỳ ⇒ 2026-01-01
# là điểm ĐẦU TIÊN thuộc nền mới. Hệ số = TB hai ước lượng độc lập (wichart.md Bẫy 6). Chủ dự án chốt
# 2026-09-05: không cần verified_by, ghi ngày.
GDP_BREAK = dict(code="vn.gdp.real", break_date=date(2026, 1, 1), factor=Decimal("1.6005"),
                 reason="Đổi năm gốc giá so sánh; trung bình hai ước lượng độc lập 1.6032 / 1.5978 (wichart.md Bẫy 6)",
                 verified_at=date(2026, 9, 5))


@dataclass(frozen=True)
class Resolved:
    domain: str
    row_id: int
    price_type: str | None


@dataclass
class Written:
    inserted: int = 0
    changed: int = 0


def load_registry(conn, series: list[Series]) -> tuple[dict[str, Resolved], dict]:
    resolved: dict[str, Resolved] = {}
    present_m, present_a = [], []
    for s in series:
        meta = json.dumps({"tier_flags": list(s.flags), "freq": s.freq, "group": s.group}, ensure_ascii=False)
        if s.domain == "macro":
            iid = conn.execute(sa.text(
                "INSERT INTO macro.indicator (code, name_vi, unit, freq, region, role)"
                " VALUES (:code, :name, :unit, :freq, :region, :role)"
                " ON CONFLICT (code) DO UPDATE SET name_vi = excluded.name_vi, unit = excluded.unit,"
                " freq = excluded.freq, role = excluded.role RETURNING indicator_id"),
                {"code": s.code, "name": s.name_vi, "unit": s.unit, "freq": s.freq, "region": s.region, "role": s.role}).scalar_one()
            conn.execute(sa.text(
                "INSERT INTO macro.indicator_source (indicator_id, source, external_key, external_sub, scale, active, meta)"
                " VALUES (:iid, :src, :key, :sub, :scale, true, cast(:meta AS jsonb))"
                " ON CONFLICT (source, external_key, external_sub) DO UPDATE SET indicator_id = excluded.indicator_id,"
                " scale = excluded.scale, active = true, meta = excluded.meta"),
                {"iid": iid, "src": SOURCE, "key": s.key, "sub": s.external_sub, "scale": s.scale, "meta": meta})
            resolved[s.code] = Resolved("macro", iid, None)
            present_m.append(f"{s.key}/{s.external_sub}")
        else:
            aid = conn.execute(sa.text(
                "INSERT INTO asset.asset (code, name_vi, asset_class, quote_currency, unit, calendar, region)"
                " VALUES (:code, :name, :cls, :ccy, :unit, :cal, :region)"
                " ON CONFLICT (code) DO UPDATE SET name_vi = excluded.name_vi, asset_class = excluded.asset_class,"
                " quote_currency = excluded.quote_currency, unit = excluded.unit, calendar = excluded.calendar,"
                " region = excluded.region RETURNING asset_id"),
                {"code": s.code, "name": s.name_vi, "cls": s.asset_class, "ccy": s.quote_currency, "unit": s.unit,
                 "cal": s.calendar, "region": s.region}).scalar_one()
            conn.execute(sa.text(
                "INSERT INTO asset.asset_external_id (asset_id, source, external_code, external_sub, scale, active, price_type, meta)"
                " VALUES (:aid, :src, :key, :sub, :scale, true, :pt, cast(:meta AS jsonb))"
                " ON CONFLICT (source, external_code, external_sub) DO UPDATE SET asset_id = excluded.asset_id,"
                " scale = excluded.scale, active = true, price_type = excluded.price_type, meta = excluded.meta"),
                {"aid": aid, "src": SOURCE, "key": s.key, "sub": s.external_sub, "scale": s.scale, "pt": s.price_type, "meta": meta})
            resolved[s.code] = Resolved("asset", aid, s.price_type)
            present_a.append(f"{s.key}/{s.external_sub}")
    deact = conn.execute(sa.text(
        "UPDATE macro.indicator_source SET active = false WHERE source = :src AND active"
        " AND NOT (external_key || '/' || external_sub = ANY(:present))"), {"src": SOURCE, "present": present_m}).rowcount
    deact += conn.execute(sa.text(
        "UPDATE asset.asset_external_id SET active = false WHERE source = :src AND active"
        " AND NOT (external_code || '/' || external_sub = ANY(:present))"), {"src": SOURCE, "present": present_a}).rowcount
    return resolved, {"macro": len(present_m), "asset": len(present_a), "deactivated": deact}


_UPSERT_MACRO = sa.text(
    "INSERT INTO macro.observation (indicator_id, obs_date, value)"
    " SELECT * FROM unnest(cast(:ids AS bigint[]), cast(:dates AS date[]), cast(:vals AS numeric[]))"
    " ON CONFLICT (indicator_id, obs_date) DO UPDATE SET value = excluded.value, ingested_at = clock_timestamp()"
    " WHERE macro.observation.value IS DISTINCT FROM excluded.value"
    " RETURNING (xmax = 0) AS inserted")
_UPSERT_ASSET = sa.text(
    "INSERT INTO asset.price_daily (asset_id, obs_date, price_type, value)"
    " SELECT * FROM unnest(cast(:ids AS bigint[]), cast(:dates AS date[]), cast(:types AS text[]), cast(:vals AS numeric[]))"
    " ON CONFLICT (asset_id, obs_date, price_type) DO UPDATE SET value = excluded.value, ingested_at = clock_timestamp()"
    " WHERE asset.price_daily.value IS DISTINCT FROM excluded.value"
    " RETURNING (xmax = 0) AS inserted")


def apply(conn, points: list[Point], resolved: dict[str, Resolved]) -> Written:
    w = Written()
    macro = [p for p in points if p.domain == "macro"]
    asset = [p for p in points if p.domain == "asset"]
    for start in range(0, len(macro), CHUNK):
        chunk = macro[start:start + CHUNK]
        flags = conn.execute(_UPSERT_MACRO, {"ids": [resolved[p.code].row_id for p in chunk],
                                             "dates": [p.obs_date for p in chunk],
                                             "vals": [p.value for p in chunk]}).scalars().all()
        w.inserted += sum(1 for f in flags if f)
        w.changed += sum(1 for f in flags if not f)
    for start in range(0, len(asset), CHUNK):
        chunk = asset[start:start + CHUNK]
        flags = conn.execute(_UPSERT_ASSET, {"ids": [resolved[p.code].row_id for p in chunk],
                                             "dates": [p.obs_date for p in chunk],
                                             "types": [p.price_type for p in chunk],
                                             "vals": [p.value for p in chunk]}).scalars().all()
        w.inserted += sum(1 for f in flags if f)
        w.changed += sum(1 for f in flags if not f)
    return w


def seed_series_break(conn) -> None:
    conn.execute(sa.text(
        "INSERT INTO macro.series_break (indicator_id, break_date, factor, reason, verified_at)"
        " SELECT indicator_id, :d, :f, :r, :v FROM macro.indicator WHERE code = :code"
        " ON CONFLICT (indicator_id, break_date) DO UPDATE SET factor = excluded.factor, reason = excluded.reason,"
        " verified_at = excluded.verified_at"),
        {"code": GDP_BREAK["code"], "d": GDP_BREAK["break_date"], "f": GDP_BREAK["factor"],
         "r": GDP_BREAK["reason"], "v": GDP_BREAK["verified_at"]})


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def store_payload_if_changed(conn, key: str, text: str, run_id: int) -> bool:
    ek = f"wichart:{key}"
    h = _hash(text)
    last = conn.execute(sa.text(
        "SELECT meta->>'hash' FROM staging.raw_payload WHERE source = :src AND endpoint_key = :ek"
        " ORDER BY payload_id DESC LIMIT 1"), {"src": SOURCE, "ek": ek}).scalar()
    if last == h:
        return False
    conn.execute(sa.text(
        "INSERT INTO staging.raw_payload (source, endpoint_key, content_type, payload, meta)"
        " VALUES (:src, :ek, 'json', cast(:p AS jsonb), cast(:m AS jsonb))"),
        {"src": SOURCE, "ek": ek, "p": text, "m": json.dumps({"hash": h, "run_id": run_id, "bytes": len(text)})})
    return True


def store_refusal_evidence(engine, texts: dict[str, str], run_id: int, verdict: Verdict) -> None:
    """Bằng chứng ở giao dịch RIÊNG — lượt chính không ghi gì."""
    meta = json.dumps({"run_id": run_id, "reasons": verdict.reasons, "refused": True}, ensure_ascii=False)
    with engine.begin() as conn:
        for key, text in texts.items():
            conn.execute(sa.text(
                "INSERT INTO staging.raw_payload (source, endpoint_key, content_type, payload, meta)"
                " VALUES (:src, :ek, 'json', cast(:p AS jsonb), cast(:m AS jsonb))"),
                {"src": SOURCE, "ek": f"wichart:{key}", "p": text, "m": meta})


def upsert_domain_state(engine, watermark: str) -> None:
    with engine.begin() as conn:
        for domain in DOMAINS:
            conn.execute(sa.text(
                "INSERT INTO ops.data_domain_state (domain, source, status, last_success_at, watermark)"
                " VALUES (:d, :s, 'active', now(), :w)"
                " ON CONFLICT (domain, source) DO UPDATE SET last_success_at = now(), watermark = :w, status = 'active'"),
                {"d": domain, "s": SOURCE, "w": watermark})
```

Nếu psycopg từ chối bind list `Decimal`/`date` thành mảng (lỗi `cannot adapt`), đổi sang `cast(:vals AS numeric[])` với `vals = [str(v) for v in ...]` và `dates = [d.isoformat() ...]` — Postgres cast text[] → numeric[]/date[] hợp lệ. Ghi vào ledger nếu phải đổi.

- [ ] **Step 4: Xanh** — `uv run pytest tests/etl/test_e40_wichart_store.py -q` → `6 passed`.

- [ ] **Step 5: Commit** — `feat(etl): WiChart store - registry upsert, changed-only UPSERT, GDP break seed, payload on hash change`.

---

### Task 6: Job + CLI

**Files:**
- Create: `backend/etl/wichart_job.py`
- Modify: `backend/etl/__main__.py` (thêm nhánh `wichart` trước dòng `print(f"etl: subcommand không hợp lệ…`, cập nhật danh sách hỗ trợ)
- Test: `backend/tests/etl/test_e41_wichart_job.py`

**Interfaces:**
- Consumes: mọi thứ Task 1–5; `omo_store.open_run/close_run`; `core.env.load_dotenv`.
- Produces: `run(keys: list[str] | None = None, dry_run: bool = False, get=None, sleep=time.sleep) -> int` (0 ok · 1 guard từ chối · 2 lỗi).

- [ ] **Step 1: Test đỏ**

`backend/tests/etl/test_e41_wichart_job.py`:

```python
"""Job trọn vòng trên Postgres thật. `get` giả: fixture thật cho 12 key, response tổng hợp cho phần còn lại
(một điểm, giá trị giữa dải đơn vị, neo đúng tần suất) — đủ để guard và apply đi qua đường thật."""
import json
import os
import pathlib
from datetime import datetime
from decimal import Decimal

import pytest
import sqlalchemy as sa

from etl import wichart_job as wj
from etl import wichart_registry as wr
from etl import wichart_store as ws
from etl.wichart_normalize import VN

FIX = pathlib.Path(__file__).parent / "fixtures" / "wichart"
EPOCH = {"d": 1788454800000, "m": 1785517200000, "q": 1780246800000, "y": 1764522000000}   # 04/09/2026 · 08/2026 · 06/2026 (Q2) · 12/2025, giờ VN
DOC, _ = wr.load_doc()
OURS = {(s.key, s.idx): s for s in wr.build()}


def _synthetic(key: str) -> str:
    meta = DOC[key]
    series = []
    for idx, (name, unit_doc, scale, role, flags) in enumerate(meta["s"]):
        s = OURS.get((key, idx))
        if s is None:
            raw = 1.0                                          # series không nạp (chết) — giữ vị trí
        else:
            lo, hi = wr.BANDS.get(s.unit, (1, 1))
            v = Decimal(str(lo)) * 10 if Decimal(str(lo)) * 10 <= Decimal(str(hi)) else Decimal(str(lo))
            raw = float(v / s.scale)
        series.append({"name": name, "unit": unit_doc, "data": [[EPOCH[meta.get("freq", "d")], raw]]})
    return json.dumps({"title": key, "timeArray": [meta.get("freq", "d")], "chart": {"series": series}})


def _fake_get(calls=None, fail_all=False):
    def get(u, timeout):
        key = u.rsplit("name=", 1)[1]
        if calls is not None:
            calls.append(key)
        if fail_all:
            return 503, ""
        p = FIX / f"{key}.json"
        return 200, (p.read_text(encoding="utf-8") if p.exists() else _synthetic(key))
    return get


def _wire(monkeypatch):
    monkeypatch.setenv("ETL_DATABASE_URL", os.environ["TEST_DATABASE_URL"])
    monkeypatch.setattr("etl.wichart_job.load_dotenv", lambda *a, **k: None)


def _cleanup(engine):
    with engine.begin() as c:
        c.execute(sa.text("DELETE FROM macro.series_break WHERE indicator_id IN"
                          " (SELECT indicator_id FROM macro.indicator_source WHERE source='wichart')"))
        c.execute(sa.text("DELETE FROM macro.observation WHERE indicator_id IN"
                          " (SELECT indicator_id FROM macro.indicator_source WHERE source='wichart')"))
        c.execute(sa.text("DELETE FROM asset.price_daily WHERE asset_id IN"
                          " (SELECT asset_id FROM asset.asset_external_id WHERE source='wichart')"))
        c.execute(sa.text("DELETE FROM staging.raw_payload WHERE source = 'wichart'"))
        c.execute(sa.text("DELETE FROM ops.etl_run WHERE job = :j"), {"j": ws.JOB})
        c.execute(sa.text("DELETE FROM ops.data_domain_state WHERE source = 'wichart'"))


def _last_run(engine):
    with engine.connect() as c:
        return c.execute(sa.text("SELECT status, stats, error FROM ops.etl_run WHERE job = :j ORDER BY run_id DESC LIMIT 1"),
                         {"j": ws.JOB}).one()


def _scalar(engine, sql):
    with engine.connect() as c:
        return c.execute(sa.text(sql)).scalar()


@pytest.fixture()
def clean(migrated_engine):
    _cleanup(migrated_engine)
    yield migrated_engine
    _cleanup(migrated_engine)


def test_full_run_writes_both_domains_and_pushes_two_domain_states(clean, monkeypatch):
    _wire(monkeypatch)
    calls = []
    assert wj.run(get=_fake_get(calls), sleep=lambda s: None) == 0
    assert len(calls) == 68 and len(set(calls)) == 68
    status, stats, _ = _last_run(clean)
    assert status == "success"
    assert stats["registry"] == {"macro": 53, "asset": 52, "deactivated": 0}
    assert stats["tally"]["keys_failed"] == 0 and stats["tally"]["series_shape"] == 0 and stats["tally"]["series_band"] == 0
    assert stats["tally"]["series_ok"] == 105 and stats["changed"] == 0 and stats["inserted"] > 1000
    assert _scalar(clean, "SELECT count(*) FROM macro.observation o JOIN macro.indicator i USING (indicator_id) WHERE i.code='vn.cpi'") == 284
    assert _scalar(clean, "SELECT value FROM macro.observation o JOIN macro.indicator i USING (indicator_id)"
                          " WHERE i.code='vn.cpi' AND obs_date='2026-08-01'") == Decimal("4.45")
    assert _scalar(clean, "SELECT value FROM asset.price_daily p JOIN asset.asset a USING (asset_id)"
                          " WHERE a.code='gold.sjc_buy' AND obs_date='2026-09-04'") == Decimal("145600000")
    assert _scalar(clean, "SELECT count(*) FROM macro.series_break") == 1
    assert stats["payloads_stored"] == 68
    today = datetime.now(VN).date().isoformat()
    with clean.connect() as c:
        rows = dict(c.execute(sa.text("SELECT domain, watermark FROM ops.data_domain_state WHERE source='wichart'")).all())
    assert rows == {"macro.indicator": today, "asset": today}


def test_second_run_same_day_changes_nothing_and_stores_no_payload(clean, monkeypatch):
    _wire(monkeypatch)
    assert wj.run(get=_fake_get(), sleep=lambda s: None) == 0
    n_payload = _scalar(clean, "SELECT count(*) FROM staging.raw_payload WHERE source='wichart'")
    ts = _scalar(clean, "SELECT max(ingested_at) FROM macro.observation")
    assert wj.run(get=_fake_get(), sleep=lambda s: None) == 0
    _, stats, _ = _last_run(clean)
    assert stats["inserted"] == 0 and stats["changed"] == 0 and stats["payloads_stored"] == 0
    assert _scalar(clean, "SELECT count(*) FROM staging.raw_payload WHERE source='wichart'") == n_payload
    assert _scalar(clean, "SELECT max(ingested_at) FROM macro.observation") == ts


def test_all_keys_failing_is_refused_with_nothing_written(clean, monkeypatch):
    _wire(monkeypatch)
    assert wj.run(get=_fake_get(fail_all=True), sleep=lambda s: None) == 1
    status, stats, err = _last_run(clean)
    assert status == "failed" and "key hỏng" in err
    assert _scalar(clean, "SELECT count(*) FROM macro.observation") == 0
    assert _scalar(clean, "SELECT count(*) FROM ops.data_domain_state WHERE source='wichart'") == 0


def test_keys_subset_writes_but_does_not_touch_domain_state(clean, monkeypatch):
    _wire(monkeypatch)
    calls = []
    assert wj.run(keys=["cpi", "vang"], get=_fake_get(calls), sleep=lambda s: None) == 0
    assert sorted(calls) == ["cpi", "vang"]
    _, stats, _ = _last_run(clean)
    assert stats["subset"] is True and stats["tally"]["keys_total"] == 2
    # vang.json: 522 điểm/series, bỏ 5 điểm T7/CN chép lại ⇒ 517 × 2 — đếm bằng script độc lập, ghi ở ledger
    assert _scalar(clean, "SELECT count(*) FROM asset.price_daily p JOIN asset.asset a USING (asset_id)"
                          " WHERE a.code IN ('gold.sjc_buy','gold.sjc_sell')") == 1034
    assert _scalar(clean, "SELECT count(*) FROM ops.data_domain_state WHERE source='wichart'") == 0


def test_dry_run_writes_nothing_but_records_the_run(clean, monkeypatch):
    _wire(monkeypatch)
    assert wj.run(dry_run=True, get=_fake_get(), sleep=lambda s: None) == 0
    status, stats, _ = _last_run(clean)
    assert status == "success" and stats["dry_run"] is True and stats["tally"]["series_ok"] == 105
    assert _scalar(clean, "SELECT count(*) FROM macro.observation") == 0
    assert _scalar(clean, "SELECT count(*) FROM staging.raw_payload WHERE source='wichart'") == 0
    # registry không bị _cleanup dập (id ổn định giữa các test) — dry-run không được THÊM dòng nào
    n_before = _scalar(clean, "SELECT count(*) FROM macro.indicator_source WHERE source='wichart'")
    assert wj.run(dry_run=True, get=_fake_get(), sleep=lambda s: None) == 0
    assert _scalar(clean, "SELECT count(*) FROM macro.indicator_source WHERE source='wichart'") == n_before


def test_unknown_key_is_an_error_before_any_call(clean, monkeypatch):
    _wire(monkeypatch)
    calls = []
    assert wj.run(keys=["cpi", "khong_co"], get=_fake_get(calls), sleep=lambda s: None) == 2
    assert calls == []
```

Số đếm trong test đến từ script độc lập chạy trên fixture 2026-09-05 (kiến trúc sư đếm trước khi giao, ghi ở ledger §0): `cpi.json` 284 điểm tháng (macro không áp luật cuối tuần) ⇒ 284 dòng `vn.cpi`; `vang.json` 522 điểm/series, 5 điểm T7/CN chép lại ⇒ 517 × 2 = 1.034 dòng vàng SJC.

- [ ] **Step 2: Đỏ** — `uv run pytest tests/etl/test_e41_wichart_job.py -q` → `ModuleNotFoundError: etl.wichart_job`.

- [ ] **Step 3: Module job**

`backend/etl/wichart_job.py`:

```python
"""Một lượt `etl wichart`: registry → fetch 68 key → normalize → guard → apply (spec §5.1).

Khác lát 4–5: guard đánh giá TRƯỚC khi mở giao dịch ghi (chưa ghi gì nên không cần rollback);
bằng chứng từ chối ở giao dịch riêng. `--keys` = lượt con: không guard, không đụng domain state.
"""
from __future__ import annotations

import logging
import os
import sys
import time
from datetime import datetime

import sqlalchemy as sa

from core.env import load_dotenv
from etl import omo_store, wichart_fetch, wichart_guard, wichart_normalize, wichart_registry, wichart_store
from etl.wichart_fetch import BadShape, FetchError
from etl.wichart_normalize import VN, SeriesError

log = logging.getLogger("etl.wichart")
JOB = wichart_store.JOB
MAX_ERRORS_IN_STATS = 50


def _engine():
    url = os.environ.get("ETL_DATABASE_URL")
    if not url:
        raise RuntimeError("thiếu ETL_DATABASE_URL")
    return sa.create_engine(url, pool_pre_ping=True)


def _fetch_all(groups, get, sleep):
    docs, texts, failed, bad = {}, {}, [], []
    with wichart_fetch.open_fetcher(get=get, sleep=sleep) as f:
        for key, group in groups:
            try:
                docs[key], texts[key] = f.fetch_one(key, group)
            except BadShape as e:
                bad.append(key)
                log.warning("%s", e)
            except FetchError as e:
                failed.append(key)
                log.warning("%s", e)
        return docs, texts, failed, bad, f.calls, f.retries


def _normalize_all(series, docs, failed, bad):
    t = wichart_guard.Tally(series_total=len(series))
    points, errors = [], []
    for s in series:
        if s.key in failed:
            continue                                   # key hỏng: không tính vào hình dạng
        if s.key in bad:
            t.series_shape += 1
            continue
        try:
            points.extend(wichart_normalize.series_points(s, docs[s.key]["chart"]["series"]))
            t.series_ok += 1
        except SeriesError as e:
            errors.append(f"{s.key}[{s.idx}] {e.reason}: {e}")
            if e.reason == "shape":
                t.series_shape += 1
            elif e.reason == "freq":
                t.series_freq += 1
            else:
                t.series_band += 1
    return points, t, errors


def run(keys=None, dry_run=False, get=None, sleep=time.sleep) -> int:
    logging.basicConfig(level=logging.INFO, stream=sys.stderr,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    load_dotenv()
    subset = keys is not None
    try:
        engine = _engine()
    except RuntimeError as e:
        log.error("%s", e)
        return 2
    run_id = omo_store.open_run(engine, JOB)
    try:
        registry = wichart_registry.build()                     # hợp đồng khởi động: lệch là chết trước fetch
        series = registry
        if subset:
            known = {s.key for s in registry}
            unknown = sorted(set(keys) - known)
            if unknown:
                raise RuntimeError(f"key không có trong registry: {unknown}")
            series = [s for s in registry if s.key in set(keys)]
        groups = wichart_registry.key_groups(series)

        docs, texts, failed, bad, calls, retries = _fetch_all(groups, get, sleep)
        points, tally, errors = _normalize_all(series, docs, failed, bad)
        tally.keys_total, tally.keys_failed, tally.keys_bad_shape = len(groups), len(failed), len(bad)
        verdict = wichart_guard.check(tally) if not subset else wichart_guard.Verdict(ok=True)
        run_date = datetime.now(VN).date()
        stats = {"tally": vars(tally), "calls": calls, "retries": retries, "points": len(points),
                 "run_date": run_date.isoformat(), "errors": errors[:MAX_ERRORS_IN_STATS],
                 "failed_keys": failed, "bad_shape_keys": bad}
        if subset:
            stats["subset"] = True
        if dry_run:
            stats["dry_run"] = True
            stats["refused"] = verdict.reasons
            omo_store.close_run(engine, run_id, "success", stats)
            log.info("wichart dry-run: %s", stats)
            return 0 if verdict.ok else 1
        if not verdict.ok:
            wichart_store.store_refusal_evidence(engine, texts, run_id, verdict)
            omo_store.close_run(engine, run_id, "failed", stats, error="guard refused: " + "; ".join(verdict.reasons))
            log.error("wichart từ chối: %s", verdict.reasons)
            return 1

        with engine.begin() as conn:
            resolved, reg_stats = wichart_store.load_registry(conn, registry)   # registry TRỌN, kể cả lượt con
            written = wichart_store.apply(conn, points, resolved)
            wichart_store.seed_series_break(conn)
            stored = sum(1 for key, text in texts.items() if wichart_store.store_payload_if_changed(conn, key, text, run_id))
        stats.update({"registry": reg_stats, "inserted": written.inserted, "changed": written.changed,
                      "payloads_stored": stored})
        if not subset:
            stats["watermark"] = run_date.isoformat()
        omo_store.close_run(engine, run_id, "success", stats)      # close_run TRƯỚC, domain state SAU
        if not subset:
            wichart_store.upsert_domain_state(engine, run_date.isoformat())
        log.info("wichart xong: %s", stats)
        return 0
    except Exception as e:                    # noqa: BLE001 — job biên ngoài: mọi lỗi vào etl_run
        omo_store.close_run(engine, run_id, "failed", error=f"{type(e).__name__}: {e}")
        log.exception("wichart thất bại")
        return 2
    finally:
        engine.dispose()
```

Thêm vào `backend/etl/__main__.py`, ngay trước `print(f"etl: subcommand không hợp lệ…`:

```python
    if args[0] == "wichart":
        import etl.wichart_job
        parser = argparse.ArgumentParser(prog="etl wichart")
        parser.add_argument("--keys", type=lambda s: [k.strip() for k in s.split(",") if k.strip()])
        parser.add_argument("--dry-run", action="store_true", dest="dry_run")
        parsed = parser.parse_args(args[1:])
        return etl.wichart_job.run(keys=parsed.keys, dry_run=parsed.dry_run)
```

và sửa chuỗi hỗ trợ thành `(hỗ trợ: omo, refdata, screener, events, price, snapshot, fundamentals, wichart)`.

- [ ] **Step 4: Xanh**

Run: `uv run pytest tests/etl/test_e41_wichart_job.py -q` → `6 passed`. Rồi `uv run pytest tests -q` → **toàn bộ xanh** (596 + số test mới, 2 skipped).

- [ ] **Step 5: Commit**

```bash
git add backend/etl/wichart_job.py backend/etl/__main__.py backend/tests/etl/test_e41_wichart_job.py
git commit -m "feat(etl): wichart job - guard before write, changed-only upsert, --keys and --dry-run

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 7: Nghiệm thu trên kho production + tài liệu sống *(kiến trúc sư làm, không giao subagent)*

- [ ] `uv run python -m etl wichart --dry-run` trên nguồn sống → dán `stats` (AC2).
- [ ] `uv run python -m etl wichart` (AC3, AC8) → truy vấn đếm + 4 literal đối chiếu API.
- [ ] Lượt hai (AC4) · truy vấn cuối tuần `paddy_vn`/`gold.intl` (AC5) · AC6 bằng test job `fail_all` + một lượt `--keys` ép `get` giả nếu cần chứng minh trên kho production · AC7 view spliced.
- [ ] Checklist spec §8 (roadmap lát 6 ✅ + "Điểm vào cho lát 7", wichart.md §10 mức tải, backend/README, market-data-store, 90-records/README, ledger).
- [ ] Sửa spec §5.5 `break_date` → `2026-01-01` (ruling Task 5) nếu chưa.
- [ ] Review toàn nhánh hai trục, merge `main`.

---

## Tự kiểm plan (đã chạy trước khi giao)

- **Phủ spec:** §4.1/4.2 → Task 1+5 · §4.3 → Task 6 · §4.4 → Task 5 (`WHERE IS DISTINCT`, hash) · §4.5 → Task 3 · §4.6 → Task 1 (bảng mã) · §4.7 → Task 1 (không map series chết) · §5.1–5.6 → Task 2–6 · §6 seam → test e36–e41 · §7 AC → Task 7 · §9.1 `ca_tra` → Task 1 Step 1 · §9.4 seed → Task 5.
- **Phát hiện khi viết plan:** `break_date` của spec §5.5 (`2026-03-01`) là neo **của nguồn**; kho neo đầu kỳ nên phải là `2026-01-01` — Task 5 dùng `2026-01-01`, kiến trúc sư sửa spec ở Task 7.
- **Nhất quán tên:** `Series.external_sub`, `Resolved.row_id`, `Written.inserted/changed`, `Tally.*` dùng thống nhất ở Task 1/5/6; `wichart_guard.Verdict(ok=True)` có `reasons` mặc định rỗng.
- **Số đếm trong test e41** (284 · 1.034) đếm bằng script độc lập trên fixture trước khi giao, không lấy từ output của code.
