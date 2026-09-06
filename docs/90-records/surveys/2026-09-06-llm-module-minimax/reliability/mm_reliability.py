"""Đo độ tin cậy đầu ra có cấu trúc của MiniMax M3 trên 30 bài thật. Tham số: CONFIG ∈ {ant_adaptive, ant_disabled, oai_thinking}.
In một dòng JSON tổng kết + ghi JSONL chi tiết vào scratchpad. Không in khoá."""
import io, json, os, sys, time, urllib.request, urllib.error
import sqlalchemy as sa

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
CONFIG = sys.argv[1]
SUFFIX = sys.argv[2] if len(sys.argv) > 2 else ""
TEMP = float(sys.argv[3]) if len(sys.argv) > 3 else None
KEY = os.environ["LLM_API"]; BASE = "https://api.minimax.io"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"mm_rel_{CONFIG}{SUFFIX}.jsonl")

SUBS = {"1": [f"1{c}" for c in "abcdef"], "2": [f"2{c}" for c in "abcde"], "3": [f"3{c}" for c in "abcdefghi"], "x": ["x"]}
ALL_SUBS = [s for v in SUBS.values() for s in v]
SCHEMA = {"type": "object",
          "properties": {"group": {"type": "string", "enum": ["1", "2", "3", "x"]},
                         "sub": {"type": "string", "enum": ALL_SUBS},
                         "confidence": {"type": "number"},
                         "summary_ai": {"type": "string"},
                         "tickers": {"type": "array", "items": {"type": "string"}}},
          "required": ["group", "sub", "confidence", "summary_ai", "tickers"], "additionalProperties": False}
SYSTEM = """Bạn là bộ phân loại tin tài chính Việt Nam của dulieuchungkhoan.vn. Đọc toàn văn bài và trả về đúng một lời gọi công cụ classify.
Taxonomy 3 nhóm / 20 sub; nhãn x = loại bỏ (tin xã hội, thể thao, giáo dục, y tế thuần; PR, advertorial) — khi group = x thì sub = x.
Nhóm 1 · Vĩ mô trong nước: 1a Thể chế và văn bản pháp quy · 1b Điều hành Chính phủ (gồm kiến nghị, tiếng nói khu vực tư nhân) · 1c Tiền tệ và tỷ giá · 1d Đầu tư công và hạ tầng · 1e Số liệu vĩ mô · 1f Thuế và ngân sách.
Nhóm 2 · Tài chính quốc tế: 2a Chứng khoán thế giới · 2b Ngân hàng trung ương · 2c Hàng hoá và năng lượng · 2d An ninh và địa chính trị · 2e Thương mại và thuế quan.
Nhóm 3 · Doanh nghiệp niêm yết: 3a CBTT và sự kiện quyền · 3b Giao dịch nội bộ và cổ đông lớn · 3c Vốn và cấu trúc · 3d KQKD và vận hành · 3e Nhận định và diễn biến thị trường · 3f Phái sinh, chứng quyền, ETF/quỹ · 3g Vi phạm và xử phạt · 3h Margin và ký quỹ · 3i Xếp hạng tín nhiệm và ESG.
Quy tắc: nhóm gợi ý từ feed chỉ là tín hiệu, được phép ghi đè (1↔3 nhảy thường xuyên). confidence trong [0,1]. summary_ai: 2–3 câu, 200–300 ký tự, không mở đầu bằng "Bài viết nói về", giữ nguyên mọi con số trong bản gốc. tickers: mã niêm yết HOSE/HNX/UPCoM là chủ thể của bài (chỉ khi nhóm 3), rỗng nếu không có; không bịa."""


def post(path, body, anthropic):
    h = {"Content-Type": "application/json"}
    if anthropic:
        h.update({"x-api-key": KEY, "anthropic-version": "2023-06-01"})
    else:
        h["Authorization"] = "Bearer " + KEY
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode(), headers=h, method="POST")
    t = time.time()
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return r.status, json.loads(r.read().decode()), round(time.time() - t, 1)
    except urllib.error.HTTPError as e:
        return e.code, {"_err": e.read().decode()[:300]}, round(time.time() - t, 1)
    except Exception as e:  # noqa: BLE001
        return 0, {"_err": type(e).__name__}, round(time.time() - t, 1)


def validate(d):
    try:
        g, s, c = d["group"], d["sub"], d["confidence"]
        return (g in SUBS and s in SUBS[g] and isinstance(c, (int, float)) and 0 <= c <= 1
                and isinstance(d["summary_ai"], str) and 80 <= len(d["summary_ai"]) <= 450
                and isinstance(d["tickers"], list) and all(isinstance(x, str) for x in d["tickers"])
                and set(d.keys()) == set(SCHEMA["required"]))
    except (KeyError, TypeError):
        return False


def extract_json_text(txt):
    txt = txt.strip()
    if "```" in txt:
        txt = txt.split("```")[1]
        txt = txt[4:] if txt.startswith("json") else txt
    i, j = txt.find("{"), txt.rfind("}")
    if i < 0 or j < 0:
        return None
    try:
        return json.loads(txt[i:j + 1])
    except ValueError:
        return None


def classify(user):
    if CONFIG.startswith("ant"):
        body = {"model": "MiniMax-M3", "max_tokens": 4000, "system": SYSTEM,
                "thinking": {"type": "adaptive" if CONFIG == "ant_adaptive" else "disabled"},
                "tools": [{"name": "classify", "description": "Kết quả phân loại một bài", "input_schema": SCHEMA}],
                "tool_choice": {"type": "tool", "name": "classify"},
                "messages": [{"role": "user", "content": user}]}
        if TEMP is not None:
            body["temperature"] = TEMP
        st, d, dt = post("/anthropic/v1/messages", body, True)
        if st != 200:
            return "error", dt, {}, str(d)[:120]
        u = d.get("usage", {})
        usage = {"in": u.get("input_tokens"), "cache": u.get("cache_read_input_tokens"), "out": u.get("output_tokens"),
                 "think": (u.get("output_tokens_details") or {}).get("thinking_tokens")}
        tool = [b for b in d.get("content", []) if b["type"] == "tool_use"]
        texts = " ".join(b.get("text", "") for b in d.get("content", []) if b["type"] == "text")
        if tool:
            return ("tool_ok" if validate(tool[0]["input"]) else "tool_invalid"), dt, usage, json.dumps(tool[0]["input"], ensure_ascii=False)
        j = extract_json_text(texts)
        if j is not None:
            return ("text_json_ok" if validate(j) else "text_json_invalid"), dt, usage, json.dumps(j, ensure_ascii=False)
        return "fail", dt, usage, texts[:200]
    else:
        body = {"model": "MiniMax-M3", "max_completion_tokens": 4000, "reasoning_split": True,
                "tools": [{"type": "function", "function": {"name": "classify", "description": "Kết quả phân loại một bài", "parameters": SCHEMA}}],
                "tool_choice": {"type": "function", "function": {"name": "classify"}},
                "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]}
        st, d, dt = post("/v1/chat/completions", body, False)
        if st != 200 or "choices" not in d:
            return "error", dt, {}, str(d)[:120]
        u = d.get("usage", {})
        usage = {"in": u.get("prompt_tokens"), "cache": (u.get("prompt_tokens_details") or {}).get("cached_tokens"),
                 "out": u.get("completion_tokens"), "think": (u.get("completion_tokens_details") or {}).get("reasoning_tokens")}
        m = d["choices"][0]["message"]
        tc = m.get("tool_calls") or []
        if tc:
            try:
                arg = json.loads(tc[0]["function"]["arguments"])
            except ValueError:
                return "tool_invalid", dt, usage, tc[0]["function"]["arguments"][:200]
            return ("tool_ok" if validate(arg) else "tool_invalid"), dt, usage, json.dumps(arg, ensure_ascii=False)
        j = extract_json_text(m.get("content") or "")
        if j is not None:
            return ("text_json_ok" if validate(j) else "text_json_invalid"), dt, usage, json.dumps(j, ensure_ascii=False)
        return "fail", dt, usage, (m.get("content") or "")[:200]


e = sa.create_engine(os.environ["ETL_DATABASE_URL"])
with e.connect() as c:
    rows = c.execute(sa.text(
        "SELECT a.article_id, a.primary_source, a.feed, a.group_from_feed, r.title, coalesce(r.sapo,''), left(r.content,3000) "
        "FROM news.article a JOIN news.article_revision r ON r.article_id=a.article_id AND r.version=1 "
        "WHERE length(r.content) >= 800 AND a.article_id % 7 = 3 ORDER BY a.article_id DESC LIMIT 30")).all()
counts, lat, tok_in, tok_out, tok_think, tok_cache = {}, [], [], [], [], []
with open(OUT, "w", encoding="utf-8") as f:
    for aid, src, feed, gff, title, sapo, content in rows:
        user = f"Nguồn: {src} · feed: {feed} · nhóm gợi ý: {gff}\nTiêu đề: {title}\nSapo: {sapo}\n\nToàn văn (đã cắt 3.000 ký tự):\n{content}"
        outcome, dt, usage, sample = classify(user)
        counts[outcome] = counts.get(outcome, 0) + 1
        lat.append(dt)
        for lst, k in ((tok_in, "in"), (tok_out, "out"), (tok_think, "think"), (tok_cache, "cache")):
            if usage.get(k) is not None:
                lst.append(usage[k])
        f.write(json.dumps({"article_id": aid, "source": src, "feed": feed, "hint": gff, "title": title[:80], "outcome": outcome,
                            "latency_s": dt, "usage": usage, "sample": sample}, ensure_ascii=False) + "\n")
        time.sleep(0.5)
med = lambda xs: (sorted(xs)[len(xs) // 2] if xs else None)
print(json.dumps({"config": CONFIG + SUFFIX, "temperature": TEMP, "n": len(rows), "outcomes": counts,
                  "latency_median_s": med(lat), "latency_max_s": max(lat) if lat else None,
                  "in_median": med(tok_in), "cache_median": med(tok_cache), "out_median": med(tok_out), "think_median": med(tok_think),
                  "out_file": os.path.basename(OUT)}, ensure_ascii=False))
