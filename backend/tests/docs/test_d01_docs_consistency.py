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
      (a) một `README.md` bất kỳ (index của tầng hay của thư mục cha), hoặc
      (b) một `.md` khác NẰM CÙNG THƯ MỤC (spec/plan/ledger gọi tên file anh em).
    Bị nhắc trong một hồ sơ ở thư mục khác KHÔNG tính — đó là trích dẫn, không phải mục lục.
    """
    plans = REPO / "docs" / "90-records" / "plans"
    corpus = {md: md.read_text(encoding="utf-8") for md in _all_md()}
    orphans = []
    for md in sorted(plans.rglob("*.md")):
        owners = [o for o in corpus
                  if o != md and (o.name == "README.md" or o.parent == md.parent)]
        if not any(md.name in corpus[o] for o in owners):
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
    # Chỉ bắt "N crawler" và "N nguồn crawl" — KHÔNG bắt "N crawl" trần, vì
    # `architecture.md` có "87 REST + 1 crawl" nói về trang OMO của SBV, không phải nguồn tin.
    count = re.compile(r"(\d+)\s+crawler|(\d+)\s+nguồn crawl")
    bad = {}
    for rel in docs:
        for a, b in count.findall(_read(rel)):
            n = int(a or b)
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
