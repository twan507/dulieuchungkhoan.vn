"""Bộ kiểm thi hành CLAUDE.md §1.7 — "một sự thật một chủ; sửa một chỗ, quét mọi chỗ".

Luật đó viết đúng bệnh nhưng tới 2026-09-07 vẫn không có phép kiểm nào thi hành nó, nên ba
lượt đồng bộ gần nhất đều quên (thêm sub `2f`, hạ ngưỡng screener 0.5 -> 0.2, thêm migration
`0019`/`0020`). Đợt audit 2026-09-07 đếm được 26 chỗ lệch chỉ vì lý do đó.

🔴 Luật chọn phép kiểm (CLAUDE.md §4.4.4 — tiêu chí phải BẤT BIẾN, không phải số thời điểm):
chỉ kiểm "hai biểu diễn của cùng một sự thật phải khớp nhau". CẤM hardcode con số của hôm nay.
Vì thế ở đây KHÔNG có phép kiểm số test — thêm một test là đỏ oan, đúng loại tiêu chí tự vi
phạm mà §4.4.4 cảnh báo. Số test giảm số chủ bằng cách khác: chỉ `database/README.md` nêu nó.

Không DB, không mạng, không import module sản phẩm (đọc hằng số bằng `ast`) — chạy được cả
khi shell chưa có `.env`.
"""
from __future__ import annotations

import ast
import json
import re
import urllib.parse
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]

_SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__", ".pytest_cache"}


def _all_md() -> list[Path]:
    out = []
    for p in REPO.rglob("*.md"):
        if _SKIP_DIRS.isdisjoint(part for part in p.parts):
            out.append(p)
    return sorted(out)


def _strip_noise(text: str) -> list[tuple[int, str]]:
    """(số dòng, nội dung) sau khi bỏ khối ``` và span `...`.

    Hai chỗ này chứa văn bản được TRÍCH chứ không phải link sống — chính đợt audit đã đếm
    nhầm 17 "link chết" vì không lọc. Markdown render chúng thành chữ, không thành link.
    """
    out, in_fence = [], False
    for i, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        out.append((i, re.sub(r"`[^`\n]*`", "", line)))
    return out


def _const(rel: str, name: str):
    """Đọc hằng số module-level bằng ast — không import, không chạy code sản phẩm."""
    tree = ast.parse((REPO / rel).read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == name:
                    return ast.literal_eval(node.value)
    raise AssertionError(f"không thấy hằng số {name} trong {rel}")


def _read(rel: str) -> str:
    return (REPO / rel).read_text(encoding="utf-8")


def _one(rel: str, pattern: str) -> str:
    """Bắt đúng một nhóm. Không khớp = tài liệu đã đổi cách diễn đạt -> sửa test, đừng bỏ."""
    m = re.search(pattern, _read(rel))
    assert m, f"{rel}: không khớp {pattern!r} — nếu câu chữ đã đổi có chủ đích thì cập nhật test này"
    return m.group(1)


# --------------------------------------------------------------------------- 1

def test_no_dead_internal_links():
    """Mọi link markdown nội bộ phải trỏ tới thứ có thật.

    Vùng lịch sử (`90-records/`, `decisions/`) không được sửa NỘI DUNG nhưng ĐƯỢC sửa href
    (§1.7), nên nó cũng nằm trong phép kiểm này.
    """
    link = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
    dead = []
    for md in _all_md():
        for lineno, line in _strip_noise(md.read_text(encoding="utf-8")):
            for m in link.finditer(line):
                target = m.group(1)
                if target.startswith(("http://", "https://", "mailto:", "#", "www.")):
                    continue
                head = urllib.parse.unquote(target.split("#")[0])
                if not head:
                    continue
                if not (md.parent / head).exists():
                    dead.append(f"{md.relative_to(REPO).as_posix()}:{lineno} -> {target}")
    assert not dead, "link nội bộ chết:\n  " + "\n  ".join(dead)


# --------------------------------------------------------------------------- 2

def test_no_orphan_plan_docs():
    """Mọi `.md` trong một thư mục plan phải được một file `.md` khác nhắc đúng tên (§1.6).

    Thư mục plan là hub — vào đó là phải chọn giữa spec/plan/ledger/đo/transcript. File không
    ai nhắc tên là file người sau không biết có mà đọc.

    Chủ sở hữu hợp lệ chỉ có hai dạng — đúng như §1.6 định nghĩa "index sở hữu":
      (a) `docs/90-records/README.md` — index sở hữu tầng này — nhắc tên THƯ MỤC plan, hoặc
      (b) một `.md` khác NẰM CÙNG THƯ MỤC (spec/plan/ledger gọi tên file anh em).
    Bị nhắc trong một hồ sơ ở thư mục khác KHÔNG tính — đó là trích dẫn, không phải mục lục.

    🔴 Bản đầu (2026-09-07 sáng) nhận "README.md BẤT KỲ có nhắc tên file" là đủ, và vì thế
    TỰ VÔ HIỆU: `90-records/README.md:16` có câu quy ước "File bên trong: `spec.md`,
    `plan.md`, `ledger.md`" ⇒ mọi file mang ba tên đó, ở BẤT KỲ thư mục nào, kể cả thư mục
    chưa hề được đưa vào bảng index, đều được tính là "có chủ". Tái hiện 2026-09-07 chiều:
    dựng `plans/9999-99-99-thu-mo-coi/` với `spec.md` + `bao-cao-la.md` — test bắt được file
    tên riêng, `spec.md` LỌT SẠCH. Tức phép kiểm mù đúng ở ba loại file phổ biến nhất.
    Nay tách làm hai vế: thư mục phải có tên trong bảng index, rồi mới xét từng file.
    """
    plans = REPO / "docs" / "90-records" / "plans"
    index = (plans.parent / "README.md").read_text(encoding="utf-8")
    corpus = {md: md.read_text(encoding="utf-8") for md in _all_md()}

    # Vế 1 — mọi thư mục plan phải có tên trong bảng của 90-records/README.md.
    lost_dirs = sorted(d.name for d in plans.iterdir() if d.is_dir() and d.name not in index)
    assert not lost_dirs, (
        "thư mục plan không có dòng nào trong docs/90-records/README.md:\n  "
        + "\n  ".join(lost_dirs))

    # Vế 2 — từng file. Chủ sở hữu là file anh em CÙNG THƯ MỤC, hoặc chính DÒNG index của
    # thư mục đó. Xét theo dòng chứ không theo cả file index: câu quy ước chung ở đầu
    # `90-records/README.md` có nêu `spec.md`/`plan.md`/`ledger.md`, nhận cả file thì mọi
    # file mang ba tên ấy lại được miễn trừ — đúng lỗ hổng vừa vá.
    rows = {d.name: next((ln for ln in index.splitlines() if d.name in ln), "")
            for d in plans.iterdir() if d.is_dir()}
    orphans = []
    for md in sorted(plans.rglob("*.md")):
        if md.name == "README.md":
            continue          # README LÀ index của thư mục nó, không phải thứ cần được index
        plan_dir = md.relative_to(plans).parts[0]
        siblings = [o for o in corpus if o != md and o.parent == md.parent]
        if md.name in rows.get(plan_dir, "") or any(md.name in corpus[o] for o in siblings):
            continue
        orphans.append(md.relative_to(REPO).as_posix())
    assert not orphans, (
        "file .md không index/ledger nào nhắc tên:\n  " + "\n  ".join(orphans))


# --------------------------------------------------------------------------- 3

def test_migration_count_matches_docs():
    real = len(list((REPO / "database" / "migrations" / "versions").glob("[0-9]*.py")))
    assert real > 0
    claims = {
        "database/README.md (câu mở)": _one(
            "database/README.md", r"Schema `postgres-data` đã dựng: \*\*(\d+) migration\*\*"),
        "database/README.md (câu ánh xạ test)": _one(
            "database/README.md", r"không 1-1 với (\d+) migration"),
        "docs/00-overview/roadmap.md §0": _one(
            "docs/00-overview/roadmap.md", r"schema `postgres-data` \*\*(\d+) migration\*\*"),
        "README.md (bảng trạng thái)": _one(
            "README.md", r"Postgres \*\*(\d+) migration\*\*"),
        "README.md (cây repo)": _one("README.md", r"migrations: Postgres (\d+)"),
    }
    bad = {k: v for k, v in claims.items() if int(v) != real}
    assert not bad, f"số migration thật = {real}, tài liệu nói khác: {bad}"


# --------------------------------------------------------------------------- 4

def test_sub_count_matches_code():
    """Taxonomy tin: tổng sub và số sub từng nhóm phải khớp `news_classify.SUBS`."""
    subs = _const("backend/etl/news_classify.py", "SUBS")
    per_group = {g: len(v) for g, v in subs.items() if g != "x"}
    total = sum(per_group.values())

    doc = "docs/20-design/news-pipeline.md"
    text = _read(doc)

    heading = re.compile(r"^### Nhóm (\d) · .*?\((\d+) sub\)", re.M)
    seen = {}
    for m in heading.finditer(text):
        seen[m.group(1)] = int(m.group(2))
    assert seen == per_group, (
        f"{doc}: heading nhóm nói {seen}, code nói {per_group}")

    # Mọi con số "N sub" NGOÀI heading nhóm phải là tổng.
    without_headings = heading.sub("", text)
    totals = {int(n) for n in re.findall(r"(\d+) sub\b", without_headings)}
    assert totals == {total}, (
        f"{doc}: tổng sub nêu trong văn bản = {sorted(totals)}, code nói {total}")

    # 🔴 Và MỌI tài liệu sống khác nhắc con số này cũng phải khớp — không chỉ file chủ.
    # Bản đầu chỉ soi `news-pipeline.md`; hệ quả là lượt sửa 20→21 làm đúng file chủ rồi
    # dừng, để lại bốn bản sao nói 20 ở bốn file khác (rà 2026-09-07 chiều). Đó đúng là
    # "sửa một chỗ, quét mọi chỗ" của §1.7 — nên phép kiểm phải quét mọi chỗ.
    others = ["README.md", "backend/README.md", "docs/README.md",
              "docs/10-sources/README.md", "docs/10-sources/news/README.md",
              "docs/20-design/README.md", "backend/etl/news_classify.py"]
    bad = {rel: sorted({int(n) for n in re.findall(r"(\d+) sub\b", _read(rel))} - {total})
           for rel in others}
    bad = {k: v for k, v in bad.items() if v}
    assert not bad, f"tổng sub thật = {total}; tài liệu nói khác: {bad}"

    # feeds.json tự gọi mình là "bản máy đọc" của taxonomy — nó phải là bản ĐÚNG, không phải
    # bản lạc hậu nhất. Tới 2026-09-07 nó vẫn thiếu `2f` trong khi code và migration đã có.
    tax = json.loads(_read("docs/10-sources/news/feeds.json"))["taxonomy"]
    in_json = {g: sorted(v) for g, v in tax.items() if isinstance(v, dict)}
    in_code = {g: sorted(v) for g, v in subs.items() if g != "x"}
    by_group = {k.split("_")[0]: v for k, v in in_json.items()}   # "2_tai_chinh…" -> "2"
    assert {g: len(v) for g, v in by_group.items()} == per_group, (
        f"feeds.json taxonomy {[(g, len(v)) for g, v in by_group.items()]} != code {per_group}")
    for g, codes in in_code.items():
        assert by_group[g] == codes, f"feeds.json nhóm {g}: {by_group[g]} != code {codes}"


# --------------------------------------------------------------------------- 5

def test_schema_test_count_matches_docs():
    """`database/README.md` nêu số file và số test seam của `tests/schema` — phải khớp thật.

    Đếm `def test_` chứ không gọi pytest: `tests/schema` hiện không dùng `parametrize` nên hai
    cách bằng nhau (kiểm luôn điều đó, để ngày nào thêm parametrize thì phép kiểm này tự lộ).
    """
    d = REPO / "backend" / "tests" / "schema"
    files = sorted(d.glob("test_s*.py"))
    bodies = [f.read_text(encoding="utf-8") for f in files]
    assert not any("parametrize" in b for b in bodies), (
        "tests/schema đã dùng parametrize — 'def test_' hết bằng số pytest thu, sửa phép kiểm này")
    n_tests = sum(len(re.findall(r"^def test_", b, re.M)) for b in bodies)

    claimed_tests = int(_one("database/README.md", r"\*\*(\d+) test\*\* seam"))
    claimed_files = int(_one("database/README.md", r"— (\d+) file, không 1-1"))
    assert (claimed_files, claimed_tests) == (len(files), n_tests), (
        f"database/README.md nói {claimed_files} file / {claimed_tests} test; "
        f"thật là {len(files)} file / {n_tests} test")


# --------------------------------------------------------------------------- 6

def test_crawl_source_count_matches_feeds_json():
    """`feeds.json` là chủ sở hữu số nguồn crawl; tài liệu không được nói một con số thứ ba."""
    feeds = json.loads(_read("docs/10-sources/news/feeds.json"))
    crawl = feeds["crawl_html"]
    total = len(crawl)
    regular = sum(1 for c in crawl if not c.get("chi_backfill"))
    assert feeds["_meta"]["crawl_html"] == total, (
        f"_meta.crawl_html = {feeds['_meta']['crawl_html']} nhưng danh sách có {total} mục")

    allowed = {total, regular}
    docs = ["README.md", "docs/README.md", "docs/00-overview/architecture.md",
            "docs/10-sources/README.md", "docs/10-sources/news/README.md",
            "docs/20-design/news-pipeline.md"]
    # Bắt cả "N crawler", "N nguồn crawl" VÀ "N crawl" trần — hai ô ASCII (`architecture.md`
    # khung L0, `news-pipeline.md` sơ đồ) dùng dạng trần, và bản đầu bỏ sót chúng nên một số
    # sai ở đó sẽ lọt (R1 chỉ ra 2026-09-07). Loại trừ đúng một câu: "REST + 1 crawl" của
    # trang OMO SBV — đó không phải nguồn tin.
    text_of = {rel: _read(rel).replace("REST + 1 crawl", "REST + OMO") for rel in docs}
    count = re.compile(r"(\d+)\s+crawler|(\d+)\s+nguồn crawl|(\d+)\s+crawl")
    bad = {}
    for rel in docs:
        for a, b, c in count.findall(text_of[rel]):
            n = int(a or b or c)
            if n not in allowed:
                bad.setdefault(rel, set()).add(n)
    assert not bad, f"số nguồn crawl hợp lệ là {sorted(allowed)}, tài liệu nói khác: {bad}"


# --------------------------------------------------------------------------- 7

def test_guard_constants_match_docs():
    """Ngưỡng chốt chặn nêu trong tài liệu phải là ngưỡng code thật đang dùng.

    Đây là họ lỗi đắt nhất của đợt audit: `MIN_PRICED_RATIO` hạ 0.5 -> 0.2 ngay trong ngày
    `backend/README.md` trích dẫn, mà README giữ số cũ — ai đọc README rồi phán một lượt chạy
    là bất thường sẽ phán sai.
    """
    bad = []

    priced = _const("backend/etl/screener_guard.py", "MIN_PRICED_RATIO")
    want = f"≥ {priced * 100:.0f} %"
    if want not in _read("backend/README.md"):
        bad.append(f"backend/README.md thiếu '{want}' (MIN_PRICED_RATIO = {priced})")

    delist = _const("backend/etl/refdata_guard.py", "DELIST_RATIO")
    want = f"DELIST_RATIO = {delist}"
    if want not in _read("docs/20-design/market-data-store.md"):
        bad.append(f"market-data-store.md thiếu '{want}'")

    days = _const("backend/etl/refdata_store.py", "DIRECTORY_ABSENT_DAYS")
    want = f"ngưỡng ân hạn {days} ngày"
    if want not in _read("docs/20-design/market-data-store.md"):
        bad.append(f"market-data-store.md thiếu '{want}' (DIRECTORY_ABSENT_DAYS = {days})")

    assert not bad, "ngưỡng tài liệu lệch code:\n  " + "\n  ".join(bad)


# --------------------------------------------------------------------------- 8

def test_trap_count_matches_conventions_headings():
    """Số bẫy nêu trong tài liệu phải khớp số mục `### Bẫy` thật của `00-conventions.md`.

    Lượt sửa 2026-09-07 đổi tiêu đề §7 "Mười ba" -> "Mười bốn" nhưng bỏ sót ba chỗ khác
    vẫn ghi "13 bẫy" (R3 chỉ ra). Cùng họ với `test_sub_count_matches_code`: một con số,
    nhiều chủ, không ai quét.
    """
    conv = "docs/10-sources/market/00-conventions.md"
    real = len(re.findall(r"^### Bẫy", _read(conv), re.M))
    assert real > 0
    word = {13: "Mười ba", 14: "Mười bốn", 15: "Mười lăm"}.get(real)
    assert word, f"chưa có chữ số cho {real} — bổ sung vào bảng trong test này"
    assert f"## 7. {word} bẫy triển khai" in _read(conv), (
        f"{conv}: tiêu đề §7 không khớp {real} mục `### Bẫy`")

    bad = {}
    for rel in ["docs/README.md", "docs/10-sources/README.md",
                "docs/00-overview/roadmap.md", "CLAUDE.md"]:
        for n in re.findall(r"(\d+) bẫy triển khai", _read(rel)):
            if int(n) != real:
                bad.setdefault(rel, set()).add(int(n))
    assert not bad, f"số bẫy thật = {real}; tài liệu nói khác: {bad}"
