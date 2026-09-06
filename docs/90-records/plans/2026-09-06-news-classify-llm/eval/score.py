"""Chấm lưới phân loại trên bộ gold. Chạy (từ backend/): uv run python ../docs/90-records/plans/2026-09-06-news-classify-llm/eval/score.py GOLD.jsonl PRED.jsonl
PRED = JSONL của `etl classify --dry-run --ids-file` (mỗi dòng có article_id, value{group, sub, tickers, industries, confidence}).
Đo: đúng nhóm, đúng nhóm+sub, mã (precision/recall theo tập, chỉ bài gold nhóm 3), ngành (precision/recall theo tập), ma trận nhầm nhóm,
độ đúng theo dải confidence (để chọn ngưỡng), và x-vs-không-x."""
import json, sys, collections
gold = {r["article_id"]: r for r in (json.loads(l) for l in open(sys.argv[1], encoding="utf-8"))}
pred = {}
for l in open(sys.argv[2], encoding="utf-8"):
    r = json.loads(l); pred[r["article_id"]] = r["value"] | {"confidence": r["value"].get("confidence")}
ids = [i for i in gold if i in pred]
n = len(ids); print(f"n gold {len(gold)} · có dự đoán {n} · thiếu {len(gold)-n}")
g_ok = sum(gold[i]["group"] == pred[i]["group"] for i in ids); s_ok = sum(gold[i]["group"] == pred[i]["group"] and gold[i]["sub"] == pred[i]["sub"] for i in ids)
print(f"đúng nhóm {g_ok}/{n} = {g_ok/n:.1%} · đúng nhóm+sub {s_ok}/{n} = {s_ok/n:.1%}")
x_g = {i for i in ids if gold[i]["group"] == "x"}; x_p = {i for i in ids if pred[i]["group"] == "x"}
print(f"x: gold {len(x_g)} · dự đoán {len(x_p)} · trùng {len(x_g & x_p)} (precision {len(x_g & x_p)/max(len(x_p),1):.0%}, recall {len(x_g & x_p)/max(len(x_g),1):.0%})")
cm = collections.Counter((gold[i]["group"], pred[i]["group"]) for i in ids if gold[i]["group"] != pred[i]["group"])
print("nhầm nhóm (gold→pred):", cm.most_common())
cs = collections.Counter((gold[i]["sub"], pred[i]["sub"]) for i in ids if gold[i]["group"] == pred[i]["group"] and gold[i]["sub"] != pred[i]["sub"])
print("nhầm sub trong cùng nhóm:", cs.most_common(12))
def prf(key, subset):
    tp = fp = fn = 0
    for i in subset:
        G, P = set(gold[i][key]), set(pred[i][key]); tp += len(G & P); fp += len(P - G); fn += len(G - P)
    p = tp / max(tp + fp, 1); r = tp / max(tp + fn, 1); return f"P {p:.0%} · R {r:.0%} (tp {tp}, fp {fp}, fn {fn})"
g3 = [i for i in ids if gold[i]["group"] == "3"]
print("mã (bài gold nhóm 3, n=%d):" % len(g3), prf("tickers", g3))
print("ngành (mọi bài):", prf("industries", ids))
exact_ind = sum(set(gold[i]["industries"]) == set(pred[i]["industries"]) for i in ids); print(f"ngành khớp tập: {exact_ind}/{n} = {exact_ind/n:.0%}")
bands = [(0, .6), (.6, .7), (.7, .8), (.8, .9), (.9, 1.01)]
print("độ đúng nhóm+sub theo confidence:")
for lo, hi in bands:
    b = [i for i in ids if pred[i]["confidence"] is not None and lo <= pred[i]["confidence"] < hi]
    if b: ok = sum(gold[i]["group"] == pred[i]["group"] and gold[i]["sub"] == pred[i]["sub"] for i in b); print(f"  [{lo:.1f},{hi:.1f}): {ok}/{len(b)} = {ok/len(b):.0%}")
