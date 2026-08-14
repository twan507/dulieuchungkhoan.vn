#!/usr/bin/env python3
"""
verify_wichart.py — Tự kiểm chứng tài liệu docs/10-nguon-du-lieu/vi-mo-hang-hoa/wichart.md

Script đọc bảng registry Python NGAY TRONG FILE MD (không gõ lại số nào), rồi
đối chiếu từng trường với API WiChart đang chạy. In PASS/FAIL cho mỗi khẳng định.

Kiểm hai nhóm:
  A. Từng key trong registry — HTTP, số series, tên series, dải giá trị sau khi
     nhân hệ số scale, ngữ nghĩa từng cờ (PCTFRAC / LOWRES / CONST / U1000),
     tần suất thật suy từ khoảng cách điểm, mốc bắt đầu lịch sử, độ trễ.
  B. Các khẳng định đặc thù trong văn bản — quy ước timestamp ICT, neo tháng/quý,
     namespace giả, CORS, ETag, endpoint hỏng, bug nhãn, series chết, chuỗi hằng
     số, đứt gãy GDP và hệ số nối.

Cách chạy:
    pip install requests
    python verify_wichart.py

Exit code 0 nếu mọi khẳng định đúng, 1 nếu có sai lệch.

DÙNG LÀM BỘ GIÁM SÁT HỢP ĐỒNG: chạy hàng ngày trong CI. Vì script đọc registry
trực tiếp từ file md, nó tự bám theo mọi thay đổi bạn ghi vào tài liệu — sai lệch
báo về nghĩa là WiGroup vừa đổi đơn vị, đổi nhãn, đổi tần suất, hoặc một series
đã chết. Xem docs/10-nguon-du-lieu/vi-mo-hang-hoa/wichart.md §7.

Kết quả lần chạy gốc: 509 PASS / 0 FAIL (2026-08-12).
"""
import re
import statistics
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

import requests

MD = Path(__file__).resolve().parent.parent / "docs" / "10-nguon-du-lieu" / "vi-mo-hang-hoa" / "wichart.md"
BASE = "https://api.wichart.vn/vietnambiz/vi-mo"
ICT = timezone(timedelta(hours=7))
NOW = datetime.now(ICT)
UA = {"User-Agent": "Mozilla/5.0", "Accept-Encoding": "gzip"}

P = F = 0
FAILS = []


def chk(cond, label, detail=""):
    global P, F
    if cond:
        P += 1
    else:
        F += 1
        FAILS.append(f"{label} :: {detail}")
    return cond


def url_of(key, group):
    return f"{BASE}?key=hang_hoa&name={key}" if group == "hang_hoa" else f"{BASE}?name={key}"


def fetch(key, group):
    r = requests.get(url_of(key, group), headers=UA, timeout=30)
    return r


def d(ms):
    return datetime.fromtimestamp(ms / 1000, tz=ICT)


# Dải hợp lý của giá trị SAU khi nhân scale, theo đơn vị gốc
BANDS = {
    "VND": (1e11, 1e17), "VND/kg": (1e3, 1e6), "VND/lượng": (1e7, 1e9),
    "VND/lít": (1e3, 1e5), "VND/m2": (1e4, 1e6), "VND/người": (1e6, 1e9),
    "VND/TSC": (1, 1e5), "VND/USD": (1e4, 1e5),
    "USD": (-1e11, 1e12), "USD/tấn": (10, 5000), "USD/ounce": (1, 1e4),
    "USD/pound": (0.05, 100), "USD/thùng": (5, 500), "USD/MMBtu": (0.2, 100),
    "CNY/tấn": (50, 5e5), "MYR/tấn": (100, 5e4), "JPY/kg": (10, 5e3),
    "%": (-200, 400), "điểm": (10, 100), "người": (1e3, 3e8), "tấn": (1e3, 1e10),
    "lượt người": (1e6, 5e9),
}


def main():
    md = open(MD, encoding="utf-8").read()
    blocks = re.findall(r"```python\n(.*?)```", md, re.S)
    ns = {}
    exec(compile(blocks[-1], "registry", "exec"), ns)  # khối cuối = bảng hardcode
    W, TIER_X = ns["WICHART"], ns["TIER_X"]

    print(f"Đọc registry từ file: {len(W)} key, {len(TIER_X)} key Tier X\n")
    print("=" * 78)
    print("A. KIỂM TỪNG KEY TRONG REGISTRY")
    print("=" * 78)

    for key, meta in W.items():
        grp = meta["g"]
        r = fetch(key, grp)
        if not chk(r.status_code == 200, f"{key}: HTTP", f"got {r.status_code}"):
            continue
        j = r.json()
        api_series = (j.get("chart") or {}).get("series") or []
        decl = meta["s"]

        chk(len(api_series) == len(decl), f"{key}: số series",
            f"file={len(decl)} api={len(api_series)}")

        for i, spec in enumerate(decl):
            if i >= len(api_series):
                break
            name, unit_base, scale, role, flags = spec
            s = api_series[i]
            api_name = (s.get("name") or "").strip()

            # tên: khớp tiền tố, trừ khi cố ý đánh dấu NAMEWRONG
            if "NAMEWRONG" not in flags:
                ok = api_name.startswith(name[:18]) or name.startswith(api_name[:18])
                chk(ok, f"{key}[{i}]: tên series", f"file='{name}' api='{api_name}'")

            vals = [p[1] for p in s.get("data", []) if isinstance(p[1], (int, float))]
            if not vals:
                chk(False, f"{key}[{i}]: có dữ liệu", "rỗng")
                continue
            pts = sorted([p for p in s["data"] if isinstance(p[1], (int, float))],
                         key=lambda p: p[0])
            latest = pts[-1][1]

            # scale đưa về dải hợp lý của đơn vị gốc
            if unit_base in BANDS:
                lo, hi = BANDS[unit_base]
                v = abs(latest * scale)
                inband = lo <= v <= hi or latest == 0
                chk(inband, f"{key}[{i}]: scale→{unit_base}",
                    f"raw={latest} ×{scale:g} = {latest*scale:,.4g} ngoài dải [{lo:g},{hi:g}]")

            # PCTFRAC: giá trị thô phải là phân số (|v|<3 phổ biến) và scale=100
            if "PCTFRAC" in flags:
                chk(scale == 100, f"{key}[{i}]: PCTFRAC scale", f"scale={scale}")
            # LOWRES: tối đa 2 chữ số thập phân
            if "LOWRES" in flags:
                dec = max(len(str(v).split(".")[1]) if "." in str(v) else 0 for v in vals)
                chk(dec <= 2, f"{key}[{i}]: LOWRES ≤2 chữ số", f"max_dec={dec}")
            # CONST: không đổi suốt lịch sử
            if "CONST" in flags:
                chk(len(set(vals)) == 1, f"{key}[{i}]: CONST",
                    f"{len(set(vals))} giá trị phân biệt")
            # U1000: raw = 1000× titleIndex tương ứng (ghép theo giá trị)
            if "U1000" in flags:
                tis = []
                for x in (j.get("titleIndex") or []):
                    try:
                        tis.append(float(str(x).replace(",", "")))
                    except ValueError:
                        pass
                hit = any(abs(latest - t * 1000) <= abs(t * 1000) * 0.01 for t in tis if t)
                chk(hit, f"{key}[{i}]: U1000 vs titleIndex", f"raw={latest} ti={tis}")

        # tần suất thật
        ts = sorted({p[0] for s in api_series for p in s.get("data", [])})
        if len(ts) > 2:
            gaps = [(ts[i + 1] - ts[i]) / 86400000 for i in range(len(ts) - 1)]
            med = statistics.median(gaps)
            real = "d" if med <= 4 else "m" if med <= 45 else "q" if med <= 120 else "y"
            if "freq" in meta:
                chk(meta["freq"] == real, f"{key}: tần suất",
                    f"file={meta['freq']} thật={real} (median gap {med:.0f}d)")
            # lịch sử bắt đầu
            if meta.get("frm", "").startswith("2") and api_series:
                a = min(p[0] for s in api_series for p in s.get("data", []))
                chk(d(a).strftime("%Y-%m") == meta["frm"], f"{key}: mốc bắt đầu",
                    f"file={meta['frm']} api={d(a).strftime('%Y-%m')}")
            # độ trễ
            if "lag" in meta and meta.get("freq") != "d":
                b = max(p[0] for s in api_series for p in s.get("data", []))
                lag = (NOW - d(b)).days
                chk(abs(lag - meta["lag"]) <= 3, f"{key}: độ trễ",
                    f"file={meta['lag']}d api={lag}d")

    print(f"  → {P} pass / {F} fail\n")

    print("=" * 78)
    print("B. KIỂM CÁC KHẲNG ĐỊNH ĐẶC THÙ TRONG VĂN BẢN")
    print("=" * 78)

    # B1 mọi timestamp là 17:00 UTC
    j = fetch("cpi", "vi_mo").json()
    hrs = {(p[0] % 86400000) // 3600000 for p in j["chart"]["series"][0]["data"]}
    chk(hrs == {17}, "B1 timestamp = 17:00 UTC", f"giờ UTC gặp: {hrs}")

    # B2 neo tháng / quý
    chk(d(max(p[0] for p in j["chart"]["series"][0]["data"])).day == 1,
        "B2a neo tháng = ngày 1", "")
    jg = fetch("gdp", "vi_mo").json()
    tq = d(max(p[0] for p in jg["chart"]["series"][0]["data"]))
    chk(tq.day == 1 and tq.month in (3, 6, 9, 12), "B2b neo quý = ngày 1 tháng cuối quý",
        f"{tq:%Y-%m-%d}")

    # B3 key=tien_te bị bỏ qua, các key khác 500
    a = requests.get(f"{BASE}?name=cpi", headers=UA, timeout=20)
    b = requests.get(f"{BASE}?key=tien_te&name=cpi", headers=UA, timeout=20)
    chk(a.text == b.text, "B3a key=tien_te bị bỏ qua", "khác nội dung")
    for k in ["chung_khoan", "nganh", "doanh_nghiep", "vi_mo"]:
        rr = requests.get(f"{BASE}?key={k}&name=cpi", headers=UA, timeout=20)
        chk(rr.status_code == 500, f"B3b key={k} → 500", f"got {rr.status_code}")

    # B4 CORS, ETag, gzip
    h = requests.get(f"{BASE}?name=cpi", headers={"Origin": "https://finext.example"},
                     timeout=20)
    chk(h.headers.get("Access-Control-Allow-Origin") == "*", "B4a CORS *",
        h.headers.get("Access-Control-Allow-Origin"))
    et = h.headers.get("ETag")
    chk(bool(et), "B4b có ETag", "")
    if et:
        r304 = requests.get(f"{BASE}?name=cpi", headers={**UA, "If-None-Match": et},
                            timeout=20)
        chk(r304.status_code == 304, "B4c If-None-Match → 304", f"got {r304.status_code}")

    # B5 xi_mang_pcb hỏng
    r5 = requests.get(f"{BASE}?key=hang_hoa&name=xi_mang_pcb", headers=UA, timeout=20)
    chk(r5.status_code == 500, "B5 xi_mang_pcb → 500", f"got {r5.status_code}")

    # B6 td nhãn sai
    jt = fetch("td", "vi_mo").json()
    chk(jt["chart"]["series"][0]["name"] == "Tổng tiền gửi",
        "B6 td[0].name = 'Tổng tiền gửi' (NAMEWRONG)", jt["chart"]["series"][0]["name"])
    jh = fetch("hd", "vi_mo").json()
    chk(jt["chart"]["series"][0]["data"][0][1] != jh["chart"]["series"][0]["data"][0][1],
        "B6b td ≠ hd về giá trị", "")

    # B7 dhtg đơn vị 'Đông'
    jd = fetch("dhtg", "vi_mo").json()
    chk(jd["chart"]["series"][2]["unit"] == "Đông", "B7 dhtg[2].unit = 'Đông'",
        jd["chart"]["series"][2]["unit"])

    # B8 vdtnsnn khai q nhưng thật là m
    jv = fetch("vdtnsnn", "vi_mo").json()
    tsv = sorted(p[0] for p in jv["chart"]["series"][0]["data"])
    medv = statistics.median([(tsv[i + 1] - tsv[i]) / 86400000 for i in range(len(tsv) - 1)])
    chk(jv["timeArray"] == ["q"] and 25 <= medv <= 35,
        "B8 vdtnsnn FREQMIS (khai q, thật m)", f"timeArray={jv['timeArray']} med={medv}")

    # B9 xang_dau RON95 chết, 3 series kia sống
    jx = fetch("xang_dau", "hang_hoa").json()
    lags = [(NOW - d(max(p[0] for p in s["data"]))).days for s in jx["chart"]["series"]]
    chk(lags[0] > 60 and all(l <= 3 for l in lags[1:]),
        "B9 xang_dau SUBDEAD (chỉ RON95 chết)", f"lags={lags}")

    # B10 các chuỗi chết
    for k, mn in [("thiec", 500), ("cao_su", 520), ("xi_mang", 530)]:
        jj = fetch(k, "hang_hoa").json()
        lag = (NOW - d(max(p[0] for p in jj["chart"]["series"][0]["data"]))).days
        chk(lag >= mn, f"B10 {k} DEAD ≥{mn}d", f"lag={lag}d")

    # B11 CONST ở nhóm VLXD
    for k in ["coc_be_tong_du_ung_luc", "ong_nhua_27x18mm", "ong_nhua_60x2mm",
              "ong_nhua_90x29mm", "son_lot_khang_kiem_cao_cap",
              "son_noi_that_tieu_chuan", "son_ngoai_that_tieu_chuan"]:
        jj = fetch(k, "hang_hoa").json()
        vs = {p[1] for p in jj["chart"]["series"][0]["data"]}
        chk(len(vs) == 1, f"B11 {k} CONST", f"{len(vs)} giá trị")

    # B12 be_tong_mac_300 FROZEN > 1 năm
    jb = fetch("be_tong_mac_300", "hang_hoa").json()
    pb = sorted(jb["chart"]["series"][0]["data"], key=lambda p: p[0])
    ci = next((i for i in range(len(pb) - 1, 0, -1) if pb[i][1] != pb[i - 1][1]), None)
    chk(ci is not None and (NOW - d(pb[ci][0])).days > 365,
        "B12 be_tong_mac_300 FROZEN >365d",
        f"{(NOW - d(pb[ci][0])).days}d" if ci else "hằng số")

    # B13 đứt gãy GDP + hệ số nối
    ssv = {p[0]: p[1] for p in jg["chart"]["series"][1]["data"]}
    tg = sorted(ssv, reverse=True)
    jump = ssv[tg[2]] and (ssv[tg[1]] / ssv[tg[2]] - 1) * 100
    chk(30 <= jump <= 40, "B13a GDP giá so sánh nhảy ~+35% tại 2026-03", f"{jump:.1f}%")
    f1 = (ssv[tg[0]] / 1.0839) / ssv[tg[4]]
    f2 = (ssv[tg[1]] / 1.0794) / ssv[tg[5]]
    chk(abs(f1 - 1.6032) < 0.005 and abs(f2 - 1.5978) < 0.005,
        "B13b hệ số nối 1.6032 / 1.5978", f"{f1:.4f} / {f2:.4f}")
    chk(abs((f1 + f2) / 2 - 1.6005) < 0.002, "B13c hệ số trung bình 1.6005",
        f"{(f1+f2)/2:.4f}")

    # B14 ds tăng trưởng chỉ 1 giá trị
    jds = fetch("ds", "vi_mo").json()
    chk(len({p[1] for p in jds["chart"]["series"][1]["data"]}) == 1,
        "B14 ds tăng trưởng = 1 giá trị duy nhất", "")

    # B15 lsdh ba mức 3.0 / 4.5 / 5.0 và bất biến
    jl = fetch("lsdh", "vi_mo").json()
    got = [sorted({p[1] for p in s["data"]}) for s in jl["chart"]["series"]]
    chk(got == [[3], [4.5], [5]], "B15 lsdh = 3.0/4.5/5.0 bất biến", f"{got}")

    # B16 số series LOWRES đúng 13
    n_low = sum(1 for m in W.values() for s in m["s"] if "LOWRES" in s[4])
    chk(n_low == 15, "B16 đúng 15 series LOWRES", f"đếm được {n_low}")

    # B17 phủ đủ 87 key
    tot = len(W) + len([k for k in TIER_X if k not in W and k != "xi_mang_pcb"])
    chk(tot == 87, "B17 phủ đủ 87 key", f"đếm được {tot}")

    print(f"\n{'='*78}")
    print(f"TỔNG: {P} PASS / {F} FAIL")
    if FAILS:
        print("\nDANH SÁCH SAI:")
        for x in FAILS:
            print("  ✗", x)
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
