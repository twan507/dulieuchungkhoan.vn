# Danh mục repo GitHub tham chiếu

Sổ đăng ký **mọi repo ngoài dùng làm nguồn tri thức hay công cụ** cho môi trường làm việc của dự án. Mỗi mục phải ghi quyết định + lý do — danh sách không lý do sẽ khiến người rà lại tốn công mở lại những mục đã loại có chủ đích *(luật kho §1.4)*.

Ba trạng thái: ✅ **đã dùng** · 📦 **kho nguồn** (giữ lại, chưa đến lúc) · ❌ **đã loại** (kèm lý do, đừng mở lại nếu không có dữ kiện mới).

## Đã dùng

| Repo | Là gì | Dùng thế nào | Ngày |
|---|---|---|---|
| [obra/superpowers](https://github.com/obra/superpowers) | Bộ skill quy trình (brainstorming, writing-plans, TDD, debugging…) | Plugin Claude Code — **bộ khung quy trình duy nhất** của dự án, gắn vào CLAUDE.md §4.1 và cấu trúc `90-records/` | trước 2026-08-14 |
| [multica-ai/andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills) | 4 nguyên tắc giảm lỗi LLM khi viết code, đúc từ quan sát của Karpathy *(bên thứ ba biên soạn, không phải Karpathy viết — nhưng nội dung đã kiểm, sạch)* | **Chưng cất thẳng vào CLAUDE.md §4.4**, không cài skill — nội dung tĩnh, ngắn, không cần nạp động | 2026-08-24 |
| [obra/the-elements-of-style](https://github.com/obra/the-elements-of-style) | Strunk & White đóng gói thành skill viết văn (cùng tác giả superpowers) | Cài user-level `~/.claude/skills/writing-clearly-and-concisely` — cho văn tiếng Anh: commit, comment, error text | 2026-08-24 |
| [longhang2004/vietnamese-humanizer](https://github.com/longhang2004/vietnamese-humanizer) | 4 skill biên tập tiếng Việt: humanizer, làm sạch dịch máy, soát ngữ pháp, nhất quán style *(đã đọc source: văn bản thuần, có luật bảo toàn dữ kiện + anti-goals)* | Cài user-level cả 4 skill — dùng khi viết/biên tập tài liệu tiếng Việt, sau này là copy UI, thông báo FE/BE, văn phong chatbot — tránh giọng AI sáo rỗng | 2026-08-24 |

## Kho nguồn — giữ lại, chưa đến lúc

| Repo | Là gì | Khi nào dùng |
|---|---|---|
| [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) | 24 skill vòng đời phát triển của Addy Osmani | Khi bắt đầu code: cherry-pick vài skill superpowers không phủ (vd `browser-testing-with-devtools`, `security-and-hardening`, `performance-optimization`). **Không cài bản full** — trùng khung quy trình với superpowers |
| [taovietducofficial/CI-CD-Beginner](https://github.com/taovietducofficial/CI-CD-Beginner) | Template GitHub Actions production cho Node/TS: CodeQL, Trivy, SBOM, cosign, release-please, staging→prod | Tham khảo khi dựng CI cho `frontend/` (Next.js). `backend/` Python cần pipeline khác — chỉ mượn cấu trúc quality-gate |

## Đã loại — kèm lý do, đừng mở lại

| Repo | Là gì | Lý do loại |
|---|---|---|
| [mattpocock/skills](https://github.com/mattpocock/skills) | Bộ skill quy trình (grill-me, tdd, wayfinder…) | **Đã có đường khác** — trùng gần 1:1 với superpowers đang dùng; hai bộ khung quy trình song song làm agent nhận luật cạnh tranh nhau |
| [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) | Ladder 7 bậc "có cần viết code này không" | **Đã có đường khác** — YAGNI đã nằm trong superpowers + CLAUDE.md §4.4 (Simplicity First) + lệnh `/simplify` |
| [dotanminh/clean-data-xls](https://github.com/dotanminh/clean-data-xls) | Skill dọn Excel (port tiếng Việt từ repo Anthropic) | **Đã có đường khác** — `document-skills:xlsx` chính chủ Anthropic; dữ liệu dự án đi qua API, không qua xls |
| [rohitg00/agentmemory](https://github.com/rohitg00/agentmemory) | Hệ memory ngoài: server local 4 port, 54 MCP tool, hook auto-capture | **Loại có chủ đích** — ngược triết lý đã chốt *"tri thức dự án vào repo"* (đầu CLAUDE.md); 54 tool phình context; auto-capture có nguy cơ ghi secret; bộ nhớ file + CLAUDE.md audit được bằng git |
| [OpenBB-finance/OpenBB](https://github.com/OpenBB-finance/OpenBB) | Nền tảng dữ liệu tài chính mã nguồn mở, có MCP | **Loại có chủ đích khỏi sản phẩm** — (1) license **AGPLv3**, dính vào backend thương mại là rủi ro pháp lý; (2) độ rộng nguồn **đã khép 2026-08-15** ([ADR 0006](decisions/0006-source-selection-2026-08-15.md)). Dùng cá nhân đối chiếu số liệu thì tự do |

## Luật thêm mục mới

1. **Đọc source trước khi cài** — skill là văn bản bơm vào context, tức là kênh prompt-injection. Repo lạ thì clone về scratchpad soi SKILL.md và tìm file thực thi trước.
2. Mỗi loại công cụ chỉ giữ **một** đại diện — nhất là khung quy trình.
3. Ghi mục mới vào đây **cùng lượt** với việc cài/loại, kèm ngày và lý do.
