# Plan — Tái cấu trúc kho tài liệu Finext v2

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Đổi toàn bộ cây thư mục sang tiếng Anh, gom file vận hành về từng nguồn, luật hoá "ADR chỉ là lịch sử", dựng tài liệu chọn trường tường minh.

**Architecture:** Task 1 là phép biến đổi cơ học bằng 3 script chia sẻ chung một bảng ánh xạ (di chuyển → sửa link theo bảng → thay tên trong văn bản, dài-trước-ngắn-sau). Task 2 sửa tay phần script không với tới. Task 3–5 là việc nội dung, chạy trên cây mới.

**Tech Stack:** Python 3 (chạy `PYTHONIOENCODING=utf-8`), git. Không thư viện ngoài.

**Spec:** `docs/superpowers/plans/2026-08-14-restructure-english-tree/spec.md` — bảng ánh xạ §2 của spec là nguồn chuẩn duy nhất cho mọi tên mới.

## Global Constraints

- Làm trên nhánh `restructure/english-tree`. KHÔNG commit lên `main`.
- Nội dung tiếng Việt giữ nguyên — chỉ đổi các chuỗi tên file/đường dẫn/tên skill.
- Vùng cấm: `corpus/` (trừ `corpus/README.md`) không sửa nội dung; prose của ADR 0001–0004 không sửa (link trong đó thì sửa).
- Tài liệu sống không trỏ về ADR (ngoại lệ: mục changelog). Không viết "xem ADR NNNN" trong bất kỳ file mới nào ngoài `decisions/`.
- Windows + tiếng Việt: mọi lệnh Python chạy với `PYTHONIOENCODING=utf-8`; grep ký tự `«` phải dùng PowerShell.
- Mỗi task kết thúc bằng: chạy bộ kiểm (link/toc/residue nếu áp dụng) + commit riêng.
- Spec + plan này COMMIT trong repo tại `docs/superpowers/plans/…`. Ledger, brief, báo cáo subagent, script tạm: thư mục scratchpad của phiên — ngoài repo, không commit.
- **Vùng loại trừ của script sửa link, thay tên và mọi bộ kiểm: `docs/superpowers/`** — spec/plan tự chứa bảng ánh xạ tên cũ, đụng vào là phá bảng hoặc báo giả. `check_residue` loại trừ thêm toàn bộ `decisions/`.

---

## Task 1 — Đổi tên cây + sửa link + thay tên trong văn bản (script)

**Files:**
- Create (workspace, ngoài repo): `sdd-restructure/rename_map.py`, `01_move.py`, `02_fix_links.py`, `03_replace_names.py`, `check_links.py`, `check_residue.py`
- Modify (repo): mọi file di chuyển theo spec §2; mọi `.md` có link/tên cũ

**Interfaces:**
- Produces: cây mới đúng spec §2; `PATHMAP` (old→new) in ra file `pathmap.json` cho Task 2 đối chiếu.

- [ ] **Step 1: Viết `rename_map.py`** (bảng ánh xạ dùng chung — chép nguyên văn spec §2):

```python
# rename_map.py — nguon chuan: spec.md §2
DIR_MAP = [  # (prefix cu, prefix moi) — ap dung dai-truoc-ngan-sau
    ("docs/00-tong-quan/quyet-dinh", "docs/00-overview/decisions"),
    ("docs/00-tong-quan", "docs/00-overview"),
    ("docs/10-nguon-du-lieu/thi-truong", "docs/10-sources/market"),
    ("docs/10-nguon-du-lieu/vi-mo-hang-hoa", "docs/10-sources/macro"),
    ("docs/10-nguon-du-lieu/tin-tuc", "docs/10-sources/news"),
    ("docs/10-nguon-du-lieu", "docs/10-sources"),
    ("docs/20-thiet-ke", "docs/20-design"),
    ("docs/30-tri-thuc", "docs/30-skills"),
    (".claude/skills/co-van-chung-khoan-vn", ".claude/skills/vn-stock-advisor"),
    (".claude/skills/kien-thuc-chung-khoan-vn", ".claude/skills/vn-stock-knowledge"),
]
BASENAME_MAP = {
    "kien-truc-tong-the.md": "architecture.md", "lo-trinh.md": "roadmap.md",
    "0001-cau-truc-kho-tai-lieu.md": "0001-docs-structure.md",
    "0002-chon-nguon-du-lieu.md": "0002-data-source-selection.md",
    "0003-dong-du-an-skill.md": "0003-close-skill-project.md",
    "0004-bo-nhat-ky-phien.md": "0004-drop-session-logs.md",
    "00-quy-uoc-chung.md": "00-conventions.md",
    "03-fiin-tham-chieu.md": "03-fiin-reference.md",
    "04-fiin-ho-so-doanh-nghiep.md": "04-fiin-company-profile.md",
    "05-fiin-bao-cao-tai-chinh.md": "05-fiin-financial-statements.md",
    "06-fiin-cham-diem-dinh-gia.md": "06-fiin-scoring-valuation.md",
    "07-fiin-dong-tien.md": "07-fiin-money-flow.md",
    "08-fiin-lich-su-kien.md": "08-fiin-event-calendar.md",
    "09-fiin-gia-thi-truong.md": "09-fiin-market-price.md",
    "10-fiin-tu-dien.md": "10-fiin-dictionary.md",
    "phu-luc-A-ma-field.md": "appendix-A-field-codes.md",
    "phu-luc-B-do-phu-du-lieu.md": "appendix-B-coverage.md",
    "tu-dien-ma-field.json": "field-dictionary.json",
    "kho-du-lieu-thi-truong.md": "market-data-store.md",
    "pipeline-tin-tuc.md": "news-pipeline.md",
    "tang-ngu-nghia-chatbot.md": "chatbot-semantic-layer.md",
    "bao-tri-skill.md": "maintenance.md", "thuat-ngu.md": "terminology.md",
    "van-phong.md": "writing-style.md", "khung-phan-tich.md": "analysis-framework.md",
    "tu-duy-lap-luan.md": "reasoning.md", "doc-hanh-vi-thi-truong.md": "market-behavior.md",
    "vi-mo-va-tao-tien.md": "macro-money-creation.md",
    "doc-bao-cao-tai-chinh.md": "financial-statements.md", "dinh-gia.md": "valuation.md",
    "ky-thuat-cung-cau.md": "technical-supply-demand.md",
    "ky-thuat-chi-bao.md": "technical-indicators.md",
    "danh-muc-va-luan-chuyen.md": "portfolio-and-rotation.md",
    "tam-ly-va-thong-tin.md": "psychology-information.md", "nang-cao.md": "advanced.md",
}
FILE_MAP_EXTRA = {  # truong hop dac biet: doi ca thu muc cha
    "config/feeds.json": "docs/10-sources/news/feeds.json",
    "scripts/verify_wichart.py": "docs/10-sources/macro/verify_wichart.py",
}
# Thay ten trong van ban — them cap ngoai basename:
PROSE_EXTRA = [
    ("13-wichart-vi-mo-hang-hoa.md", "wichart.md"),  # text hien thi cu con sot tu lan tai cau truc truoc
    ("co-van-chung-khoan-vn", "vn-stock-advisor"),
    ("kien-thuc-chung-khoan-vn", "vn-stock-knowledge"),
    ("config/feeds.json", "docs/10-sources/news/feeds.json"),
    ("scripts/verify_wichart.py", "docs/10-sources/macro/verify_wichart.py"),
    ("00-tong-quan", "00-overview"), ("quyet-dinh", "decisions"),
    ("10-nguon-du-lieu", "10-sources"), ("20-thiet-ke", "20-design"),
    ("30-tri-thuc", "30-skills"), ("thi-truong", "market"),
    ("vi-mo-hang-hoa", "macro"), ("tin-tuc", "news"),
]

def in_corpus_content(p):   # corpus bat bien, tru README chi muc
    return "corpus/" in p.replace("\\", "/") and not p.replace("\\", "/").endswith("corpus/README.md")
def is_frozen_adr(p):
    p = p.replace("\\", "/")
    return any(f"decisions/000{i}-" in p or f"quyet-dinh/000{i}-" in p for i in (1, 2, 3, 4))

def new_path(old):
    old = old.replace("\\", "/")
    if old in FILE_MAP_EXTRA: return FILE_MAP_EXTRA[old]
    d, _, b = old.rpartition("/")
    for pre, npre in DIR_MAP:
        if d == pre or d.startswith(pre + "/"):
            d = npre + d[len(pre):]; break
    if not in_corpus_content(old):
        b = BASENAME_MAP.get(b, b)
    return f"{d}/{b}" if d else b
```

- [ ] **Step 2: Viết `01_move.py`** — với mỗi file trong `git ls-files`, nếu `new_path(f) != f`: tạo thư mục đích, `git mv f new`. In số file đã chuyển. Sau đó xoá `config/` `scripts/` nếu rỗng. Xuất `pathmap.json` = {old: new} cho MỌI file (kể cả không đổi).

- [ ] **Step 3: Viết `02_fix_links.py`** — với mỗi `.md` (vị trí MỚI, tra ngược vị trí CŨ từ pathmap): với mỗi link `[text](target)` không phải http/mailto/`#`: tách fragment `#...`; old_abs = normpath(old_dir + target); new_abs = pathmap[old_abs] (thử cả khớp tiền tố thư mục qua DIR_MAP cho link trỏ thư mục); ghi lại relpath(new_abs, new_dir) dạng posix + fragment. File trong vùng corpus-content hoặc `docs/superpowers/`: BỎ QUA. In số link đã sửa / không giải được.

- [ ] **Step 4: Viết `03_replace_names.py`** — cặp thay = các cặp (cũ≠mới) trong BASENAME_MAP + PROSE_EXTRA, **sắp theo độ dài giảm dần**; áp lên mọi `.md` TRỪ corpus-content, TRỪ ADR đóng băng (`is_frozen_adr`) và TRỪ `docs/superpowers/`. In bảng đếm thay thế theo file.

- [ ] **Step 5: Chạy theo thứ tự** `01_move.py` → `02_fix_links.py` → `03_replace_names.py` (mỗi bước in kết quả, dừng nếu lỗi).

- [ ] **Step 6: Viết + chạy `check_links.py`** (regex `\[[^\]]*\]\(([^)#][^)]*?)\)`, unquote, bỏ http/mailto, kiểm tồn tại; loại trừ corpus-content và `docs/superpowers/`; strip code fence trước khi quét). Kỳ vọng: `0 treo`.

- [ ] **Step 7: Viết + chạy `check_residue.py`** — quét mọi slug cũ (mọi key BASENAME_MAP + vế trái PROSE_EXTRA) trên `*.md` + `verify_wichart.py`, loại trừ corpus-content, toàn bộ `decisions/` và `docs/superpowers/`. Kỳ vọng: chỉ còn hit trong `verify_wichart.py` (Task 2 xử lý) — liệt kê để bàn giao.

- [ ] **Step 8: Kiểm rename** — `git status --short` phải là các dòng `R` (rename); đếm và ghi vào báo cáo.

- [ ] **Step 9: Commit** — `git add -A && git commit -m "Tái cấu trúc: đổi cây thư mục sang tiếng Anh, gom file vận hành về từng nguồn"`.

## Task 2 — Sửa tay phần script không với tới

**Files:**
- Modify: `README.md` (gốc), `docs/README.md`, `docs/10-sources/README.md`, `docs/10-sources/macro/verify_wichart.py`, `.claude/skills/*/SKILL.md`

**Interfaces:** Consumes cây mới + `pathmap.json` của Task 1.

- [ ] **Step 1: `verify_wichart.py`** — sửa 3 chỗ path (dòng ~3, ~25 docstring; dòng ~37):

```python
MD = Path(__file__).resolve().parent / "wichart.md"
```

Docstring đổi `docs/10-nguon-du-lieu/vi-mo-hang-hoa/wichart.md` → `docs/10-sources/macro/wichart.md`. Chạy `python verify_wichart.py --help` (hoặc import thử) xác nhận không lỗi cú pháp; KHÔNG chạy kiểm API thật.

- [ ] **Step 2: Sơ đồ cây trong `README.md` gốc** — thay khối cấu trúc repo bằng:

```
finext-v2/
├── docs/                Toàn bộ tài liệu — bản đồ ở docs/README.md
│   ├── 00-overview/     kiến trúc · lộ trình · sổ quyết định (chỉ lịch sử)
│   ├── 10-sources/      reference: market · macro · news — mỗi nguồn tự chứa đủ đồ nghề
│   ├── 20-design/       lựa chọn kiến trúc của Finext
│   └── 30-skills/       tài liệu bảo trì + corpus của hai skill
├── .claude/skills/      vn-stock-advisor · vn-stock-knowledge — sản phẩm chạy được
└── (chưa có)            chỗ cho frontend / backend — chốt khi bắt đầu code
```

- [ ] **Step 3: `docs/README.md`** — mục "Ngoài `docs/`": xoá dòng `config/` và `scripts/` cũ; bảng nguồn ghi rõ `news/feeds.json` và `macro/verify_wichart.py` nằm trong từng nguồn.

- [ ] **Step 4: Kiểm frontmatter 2 SKILL.md** — `name:` phải là `vn-stock-advisor` / `vn-stock-knowledge` (script Task 1 đã thay; xác nhận, sai thì sửa).

- [ ] **Step 5: Đọc lướt `docs/10-sources/README.md`** — các câu quanh feeds.json/verify_wichart phải còn nghĩa sau khi thay tên (câu văn, không chỉ path).

- [ ] **Step 6: Chạy lại `check_links.py` + `check_residue.py`** — kỳ vọng 0 treo, 0 tồn dư (kể cả verify_wichart.py).

- [ ] **Step 7: Chạy `check_toc.py`** (đối chiếu mục lục↔heading 2 skill) — kỳ vọng 0 lệch.

- [ ] **Step 8: Commit** — `"Tái cấu trúc: sửa sơ đồ cây, path trong verify_wichart, bản đồ tài liệu"`.

## Task 3 — Tài liệu chọn trường tường minh

**Files:**
- Create: `docs/20-design/market-field-selection.md`, `docs/20-design/market-field-selection.json`
- Modify: `docs/00-overview/architecture.md` (§3.4, một câu trỏ), `docs/20-design/README.md` (thêm dòng bảng)

**Interfaces:** Consumes: `decisions/0002-data-source-selection.md`, `10-sources/market/10-fiin-dictionary.md`, `appendix-A-field-codes.md`, `field-dictionary.json`, `appendix-B-coverage.md`, `04-fiin-company-profile.md`.

- [ ] **Step 1:** Đọc ADR 0002 toàn văn; chép ra cấu trúc nhóm: Screener bỏ 113 (11 nhóm lý do + số đếm), giữ 80; Snapshot giữ 16 độc quyền; BVSC nhóm giá; BCTC 556; MoneyFlow.
- [ ] **Step 2:** Từ tài liệu nguồn, dựng danh sách trường từng nguồn (Screener 193, Snapshot 54) và gán mỗi trường vào một nhóm lấy/bỏ **chỉ khi tài liệu nguồn cho phép suy trực tiếp** (vd trường nằm trong bảng "chỉ báo kỹ thuật" của tài liệu nguồn → nhóm "chỉ báo kỹ thuật — tính từ giá BVSC"). Không suy được → `cần kiểm API`.
- [ ] **Step 3:** Viết `market-field-selection.md`: đầu file ghi luật chọn nguồn (chép tường minh từ architecture §3.4, không trỏ ADR); bảng từng nguồn: `mã · tên · lấy/bỏ · nguồn chuẩn · lý do tại chỗ`; cuối file: bảng đối soát số đếm với con số 80/193 · 16/54 · 113 — lệch thì ghi rõ lệch bao nhiêu, ở nhóm nào, KHÔNG ép.
- [ ] **Step 4:** Xuất `market-field-selection.json`: `[{code, name_vi, source, keep, reason, status: "chốt"|"cần kiểm API"}]` — nội dung phải sinh từ cùng dữ liệu với bảng md (viết script nhỏ sinh json từ md hoặc ngược lại, không gõ tay hai lần).
- [ ] **Step 5:** `architecture.md` §3.4: câu `Đầy đủ: ...` trỏ tới `../20-design/market-field-selection.md`. `20-design/README.md` thêm dòng cho file mới, trạng thái `✅ đã chốt (trải từ quyết định 2026-08-14)`.
- [ ] **Step 6:** Chạy `check_links.py`. Commit — `"Thiết kế: tài liệu chọn trường tường minh cho ETL"`.

## Task 4 — Quét "xem ADR" + luật hoá quy tắc

**Files:**
- Modify: `README.md`, `docs/README.md`, `docs/00-overview/architecture.md`, `docs/00-overview/roadmap.md`, `docs/30-skills/README.md`, `docs/30-skills/maintenance.md`, `docs/30-skills/corpus/README.md`, `docs/20-design/README.md` (nếu có hit)

**Interfaces:** Consumes cây sau Task 3.

- [ ] **Step 1:** `grep -rn "ADR" docs README.md --include=*.md` loại trừ `decisions/` — liệt kê mọi hit vào báo cáo, phân loại: (a) con trỏ thừa — phát biểu đã tường minh; (b) nội dung dựa ADR; (c) changelog — được giữ.
- [ ] **Step 2:** Loại (a): gỡ con trỏ, giữ phát biểu. Loại (b): viết thẳng nội dung vào tại chỗ (ngắn — một mệnh đề lý do), rồi gỡ con trỏ. Cột "bằng chứng" trong bảng trạng thái README/roadmap: link tới tài liệu sống tương ứng (vd chọn trường → `market-field-selection.md`), không link ADR.
- [ ] **Step 3:** `docs/README.md` — thêm vào bảng luật sửa dòng cho `decisions/`: *"Chỉ ghi lịch sử quyết định. Tài liệu sống phải tường minh, không trỏ về đây; xoá cả thư mục này chỉ được phép mất lịch sử."*
- [ ] **Step 4:** Grep lại `ADR` — hit còn lại chỉ được ở changelog và `decisions/`. Chạy `check_links.py`. Commit — `"Luật hoá: tài liệu sống tường minh, ADR chỉ là lịch sử"`.

## Task 5 — ADR 0005 + nghiệm thu cuối

**Files:**
- Create: `docs/00-overview/decisions/0005-english-tree.md`
- Modify: `docs/README.md` (dòng chỉ mục decisions thêm 0005)

- [ ] **Step 1:** Viết ADR 0005 theo format ADR hiện có (Bối cảnh / Quyết định / Hệ quả / Đã cân nhắc và loại): lý do tái cấu trúc (cây phản ánh lịch sử thay vì sản phẩm; tên Việt mơ hồ; config/scripts vô chủ), **bảng ánh xạ đầy đủ chép từ spec §2**, quyết định luật "ADR chỉ là lịch sử" + phép kiểm xoá-decisions, ghi chú tương lai: feeds.json chuyển về config của app pipeline tin khi có code. Ghi rõ thay thế ADR 0001 §1/§5. ADR được phép nhắc ADR cũ.
- [ ] **Step 2:** Chạy đủ bộ: `check_links.py` (0 treo) + `check_residue.py` (0 tồn dư) + `check_toc.py` (0 lệch) + grep `ADR` (chỉ changelog + decisions + docs/superpowers) + `ls` gốc repo (chỉ README.md, docs, .claude, .git).
- [ ] **Step 3:** Commit — `"ADR 0005: tái cấu trúc cây tiếng Anh"`.

---

## Self-review đã chạy (theo writing-plans)

- Spec coverage: §1.1–1.3→Task 1–2 · §1.4→Task 4 · §1.5→Task 3 · §2→Task 1 (map) + Task 5 (ADR) · §3→ràng buộc Task 1/4 · §6→bước kiểm rải trong task + Task 5 Step 2. Đủ.
- Placeholder: không còn "TBD/tự xử". Code script chính đã nêu đủ logic; implementer chuyển thành file chạy được.
- Nhất quán tên: `pathmap.json`, tên script, tên file mới — thống nhất giữa các task.
