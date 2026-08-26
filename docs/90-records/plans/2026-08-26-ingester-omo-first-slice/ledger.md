# SDD ledger — plan: docs/90-records/plans/2026-08-26-ingester-omo-first-slice/plan.md

Spec: spec.md cùng thư mục (authority). Workspace artifact subagent: scratchpad ngoài repo (CLAUDE.md cấm `.superpowers/`).

## Preflight scan (2026-08-26 12:50)

Cặp task chia sẻ file/interface:

| Cặp | Produce vs consume | Kết quả |
|---|---|---|
| T1 `core/env.py` ↔ T9 `config.py`, T8 `omo_job` | `load_dotenv()` + `REPO_ROOT` | khớp — T9/T8 import đúng tên |
| T2 stub `omo_job.run` ↔ T8 thay thật | `run() -> int` | khớp |
| T5 `OmoResult/OmoRow` ↔ T6 store, T8 job | dataclass field thứ tự (op_type, tenor, part, win, vol, rate) | khớp test T6 |
| T6 `store(result, html, conn)` ↔ T8 | conn = SQLAlchemy Connection, caller giữ tx | khớp |
| T7 `rebuild(conn)` ↔ T8 | gọi trong cùng tx với store | khớp |
| T10 `Normalized/Metrics/COLUMNS` ↔ T13 state, T14 chwriter, T15 reconcile, T16 main | tên bảng + row dict | khớp |
| T11 `frame_key/FrameDedup/Stamper` ↔ T16 | chữ ký như plan | khớp |
| T12 `Catalog/topics/fetch_base_state` ↔ T16 | tên hàm | ⚠️ plan Interfaces T12 có dòng đánh máy "fetch_instруments := fetch_base_state" (ký tự Cyrillic) — **Ruling:** tên đúng là `fetch_base_state`, dòng kia là ghi chú đặt tên, không phải hai hàm. Chi phí nếu sai: không — test T12 chỉ dùng build_catalog/topics |
| T15 `MeasureWriter.write(received_at_ms, packet)` ↔ T16 measure mode | lưu packet nguyên văn | khớp spec §3.5 (đã sửa spec cùng lượt) |
| T16 `run(mode, minutes, out, d)` ↔ `__main__` | chữ ký thống nhất | khớp |

Task tự nhất quán: T5 test expected phải chép từ fixture thật (T4 đứng trước) — plan ghi rõ; T14 test poison dùng giá trị tràn Decimal64 thật; T16 test server giả có một assert viết gọn (`state["subs"][1] == ...replace("421","421")`) — **Ruling:** assert đó viết lại thành so sánh `args` lần 2 == `args` lần 1 (plan tự ghi chú ngay dưới). Không có task nào mâu thuẫn Global Constraints.

**Ruling (điều phối, 12:50):** hôm nay là ngày giao dịch, phiên chiều mở 13:00 — controller tự làm gấp T1 + T9 + T15(measure) + T16(measure-mode tối thiểu) để bật capture `--measure` trong phiên chiều nay làm dữ liệu bổ sung. Gate AC3 vẫn đòi phiên đo TRỌN (08:40–15:05) ở phiên kế tiếp — capture chiều nay không thay thế gate. Vì làm lệch thứ tự, các phần controller tự viết sẽ đi qua vòng review khi task tương ứng được rà lại (T9/T15/T16 vẫn được review theo diff như thường). Chi phí nếu sai: mất ~40 phút nếu không kịp giờ — chấp nhận.

## Tiến trình
