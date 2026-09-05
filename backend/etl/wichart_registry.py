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
    calendar: str | None = None      # chỉ asset có lịch (asset.asset.calendar); macro để None
    tier: str = "A"                  # §9, cấp KEY (không phải cấp series)
    key_flags: tuple[str, ...] = ()  # §9, cấp KEY (vd WIN2Y, FREQMIS) — khác flags cấp series

    @property
    def external_sub(self) -> str:
        return str(self.idx)

    # Cùng giao diện với `etl.registry.Series` để đi qua `registry.load_registry` chung (lát 7)
    @property
    def external_key(self) -> str:
        return self.key

    @property
    def meta(self) -> dict:
        return {"flags": list(self.flags), "freq": self.freq, "group": self.group, "tier": self.tier,
                "key_flags": list(self.key_flags)}


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
    ("dau_wti", 0): ("wti", "Giá dầu WTI", _C, "USD", "USD/thùng", "futures", "us"),   # tên trung tính: FRED ghi spot cùng asset (lát 7)
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

# Sàn độ lớn theo mã (đơn vị gốc) cho series MỨC có dải đơn vị cắt qua 0 — chốt (iii) bắt cả lỗi làm giá trị NHỎ đi.
LEVEL_FLOOR: dict[str, Decimal] = {
    "vn.export": Decimal("1e9"), "vn.import": Decimal("1e9"),          # ~5e10 USD/tháng
    "vn.fdi.registered": Decimal("1e8"), "vn.fdi.realized": Decimal("1e8"),   # ~1e9–1e10 USD
    "vn.fx_reserves": Decimal("1e10"),                                  # ~8e10 USD
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
                      scale=Decimal(str(scale)), freq=meta.get("freq") or "d", role=role, flags=tuple(flags),
                      tier=meta.get("tier", "A"), key_flags=tuple(meta.get("flags", [])))
        if domain == "macro":
            code, name_vi = MACRO[(key, idx)]
            out.append(Series(code=code, name_vi=name_vi, unit=unit_doc, **common))
        else:
            code, name_vi, cls, ccy, unit, ptype, region = ASSET[(key, idx)]
            out.append(Series(code=code, name_vi=name_vi, unit=unit, asset_class=cls, quote_currency=ccy,
                              price_type=ptype, region=region, calendar="trading_days", **common))
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
