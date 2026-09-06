"""So khớp lượt 1 và lượt 2 (8 lô mỗi lượt) → thống kê đồng thuận + file bài lệch cho phân xử (chia 3 lô).
Đồng thuận: group & sub bằng nhau; tickers = tập bằng nhau; industries = tập bằng nhau. Lệch bất kỳ trường nào ⇒ đưa phân xử.
Chạy: python compare.py"""
import json, os, collections
G = os.path.dirname(os.path.abspath(__file__))
def load(prefix):
    out = {}
    for i in range(1, 9):
        for l in open(f"{G}/{prefix}-{i}.jsonl", encoding="utf-8"):
            r = json.loads(l); out[r["article_id"]] = r
    return out
art = {}
for i in range(1, 9):
    for l in open(f"{G}/chunk-{i}.jsonl", encoding="utf-8"):
        r = json.loads(l); art[r["article_id"]] = r
p1, p2 = load("p1"), load("p2")
assert set(p1) == set(p2) == set(art), (len(p1), len(p2), len(art))
agree = collections.Counter(); dis = []
for aid in art:
    a, b = p1[aid], p2[aid]
    g = a["group"] == b["group"]; s = a["sub"] == b["sub"]; t = set(a["tickers"]) == set(b["tickers"]); i = set(a["industries"]) == set(b["industries"])
    agree["group"] += g; agree["sub"] += s; agree["tickers"] += t; agree["industries"] += i; agree["all"] += (g and s and t and i)
    if not (g and s and t and i):
        dis.append({"article_id": aid, "diff": [k for k, ok in (("group", g), ("sub", s), ("tickers", t), ("industries", i)) if not ok],
                    "p1": {k: a[k] for k in ("group", "sub", "tickers", "industries", "note")}, "p2": {k: b[k] for k in ("group", "sub", "tickers", "industries", "note")},
                    "hard": a["hard"] or b["hard"], **{k: art[aid][k] for k in ("source", "hint", "url", "title", "sapo", "excerpt")}})
n = len(art)
print("n", n, {k: f"{v}/{n} = {v/n:.0%}" for k, v in agree.items()})
print("lệch theo trường:", collections.Counter(d for x in dis for d in x["diff"]))
print("lệch nhóm (p1→p2):", collections.Counter((x["p1"]["group"], x["p2"]["group"]) for x in dis if "group" in x["diff"]).most_common(10))
k = (len(dis) + 2) // 3
for j in range(3):
    with open(f"{G}/dis-{j+1}.jsonl", "w", encoding="utf-8") as f:
        for x in dis[j*k:(j+1)*k]: f.write(json.dumps(x, ensure_ascii=False) + "\n")
print("bài lệch:", len(dis), "→ dis-1..3 mỗi lô ≈", k)
json.dump({"n": n, "agree": dict(agree), "disagreements": len(dis)}, open(f"{G}/agreement.json", "w"))
