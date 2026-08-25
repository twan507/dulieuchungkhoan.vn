# Plan — Lược đồ PostgreSQL `postgres-data`

**Cách làm việc (chốt 2026-08-25, yêu cầu chủ dự án):** spec tách thành **các bước nhỏ, mỗi bước một file, duyệt tuần tự** — chốt xong file nào coi như file đó xong, không mở lại trừ khi bước sau phát hiện mâu thuẫn (khi đó quay lại sửa file cũ tường minh, ghi lý do). Bản nháp spec một-cục ban đầu đã bỏ, nội dung phân rã vào các bước.

## Mục tiêu thiết kế — thước đo của mọi bước

| # | Mục tiêu |
|---|---|
| G1 | **Không mất dữ liệu không tái tạo được** — OMO, snapshot/screener tự tạo lịch sử, tin đã gỡ |
| G2 | **Tra cứu nhanh cho web/API/chatbot** — theo mã × thời gian và cắt ngang toàn thị trường theo ngày |
| G3 | **Nguồn tháo lắp module** — đổi nguồn không đụng dữ liệu, không đụng schema |
| G4 | **Nền sạch cho tầng tự tính** — số tự tính không trộn vào bảng sự thật, rebuild được toàn phần |
| G5 | **Vận hành vừa sức một người** — quy ước lặp lại, idempotent, con số trong tài liệu phải trung thực |

## Trạng thái các bước

| Bước | File | Nội dung | Trạng thái |
|---|---|---|---|
| 1 | [step-01-foundations.md](step-01-foundations.md) | Nguyên tắc nền · bố cục 6 schema · quy ước DDL · migration Alembic | ✅ chốt 2026-08-25 |
| 2 | [step-02-market-identity.md](step-02-market-identity.md) | Định danh: issuer · security · ánh xạ nguồn · **bộ ngành riêng** (thay ICB) | ✅ chốt 2026-08-25 — cây ngành ở [industry-tree.md](../../../20-design/industry-tree.md) |
| 3 | [step-03-market-data.md](step-03-market-data.md) | Giá EOD + view hệ số · BCTC · từ điển chỉ tiêu · snapshot/screener · sự kiện | ✅ chốt 2026-08-25 |
| 4 | [step-04-macro.md](step-04-macro.md) | Registry chỉ tiêu + observation (UPSERT) · cụm OMO | ✅ chốt 2026-08-25 |
| 5 | [step-05-asset.md](step-05-asset.md) | Registry tài sản · price/ohlc/fx · luật dầu-vàng-DXY | ✅ chốt 2026-08-25 |
| 6 | [step-06-news.md](step-06-news.md) | Article/revision không ghi đè · gắn mã · tìm kiếm 4 lớp | ✅ chốt 2026-08-25 |
| 7 | [step-07-staging-ops.md](step-07-staging-ops.md) | Landing zone · data_domain_state · giám sát hợp đồng · etl_run | 🟡 chờ duyệt |
| 8 | step-08-derived.md | **Tầng tự tính**: chỉ số ngành từ cây riêng · chỉ báo kỹ thuật · bảng dẫn xuất khác | ⬜ chưa viết — nguyên tắc đã chốt (xem dưới), danh sách bảng cụ thể chốt sau 3–7, công thức chốt khi có dữ liệu thật |

Sau khi cả 7 bước chốt: viết `plan.md` (bẻ task thực thi) theo quy trình §4.1.

**Checklist quét tài liệu sống khi spec chốt xong** *(luật §1.7 — ghi sẵn từ review vòng 3 để không sót)*:
- [ ] `architecture.md` §3.1/§3.2 — "bảng `organization`" → `issuer`/`security`; "khung ngành = ICB" → `market.industry` (hợp đồng skill không đổi bản chất)
- [ ] `20-design/README.md` dòng "bảng `organization` là nguồn sự thật duy nhất" → cập nhật theo tách issuer/security
- [ ] `market-data-store.md` — đánh dấu §5 được thay bởi spec này (giữ nguyên văn làm lịch sử thiết kế, thêm banner trỏ sang), §9.6 mục cột `source` ghi override
- [ ] `news-pipeline.md` §9.3 — đối chiếu spec bản ghi với DDL bước 6 (feed/group_from_feed/via 3 giá trị đã khớp)

## Quyết định xuyên suốt đã chốt (áp cho mọi bước)

| # | Quyết định | Ngày |
|---|---|---|
| 1 | Migration bằng **Alembic**, SQL thô trong migration; `postgres-app` là env riêng sau này | 2026-08-25 |
| 2 | Schema tổ chức **theo miền tiêu thụ**, không theo nguồn — ETL biến đổi mọi nguồn về mô hình chuẩn | 2026-08-25 |
| 3 | Định danh bằng **khoá nội bộ** + bảng ánh xạ external cho thực thể (chứng khoán, chỉ tiêu, tài sản) | 2026-08-25 |
| 4 | **Không cột `source` ở bảng dữ liệu** — nguồn có thể đổi, xuất xứ nằm ở bảng ánh xạ registry + `staging`/`ops`. Chỉ tin tức ghi nguồn (báo nào đăng). *Override có ý thức* mục "thêm cột source" ở [market-data-store §9.6](../../../20-design/market-data-store.md) — cập nhật tài liệu sống khi spec chốt xong | 2026-08-25 |
| 5 | **Phân ngành dùng bộ riêng của chủ dự án**, không dùng cây ICB làm chuẩn — chi tiết chốt ở bước 2 | 2026-08-25 |
| 6 | Hai instance `postgres-data`/`postgres-app`, hai connection string, cấm JOIN chéo instance (chốt D — service-topology §4) | 2026-08-25 |

## Tầng dữ liệu tự tính (derived) — nguyên tắc mở rộng, chốt 2026-08-25

Chủ dự án sẽ tự tính thêm từ số đã có (chỉ số ngành theo cây riêng, chỉ báo kỹ thuật từng mã…). Ba luật để thêm bảng mới không phá kiến trúc:

1. **Nằm cùng schema miền tiêu thụ** — chỉ số ngành ngân hàng vẫn là câu hỏi miền market ⇒ `market.industry_index_daily`; không lập schema `derived` riêng (người dùng hỏi theo miền, không hỏi theo cách số được tạo ra).
2. **Rebuild được toàn phần, idempotent** — bảng dẫn xuất tính lại 100% từ bảng sự thật; xoá đi tính lại không mất gì. Hệ quả: không cần backup riêng, sai công thức thì sửa rồi tính lại, và **không bảng dẫn xuất nào được là nguồn sự thật duy nhất của bất kỳ con số nào**. (Tiền lệ đã có: `macro.omo_flow`, view `market.price_factor`.)
3. **Không trộn cột dẫn xuất vào bảng sự thật** — không thêm cột RSI vào `price_daily`; dẫn xuất ở bảng/view riêng. Chọn dạng: tính rẻ lúc đọc → **view**; cần quét toàn thị trường/screener theo giá trị đã tính → **bảng vật chất hoá** do job `etl` dựng.

Điểm tinh tế ghi trước: doanh nghiệp **đổi ngành** (gán tay) thì rebuild chỉ số ngành sẽ viết lại lịch sử theo gán mới — chấp nhận (triết lý rebuild); nếu ngày nào cần "lịch sử ngành tại thời điểm", mới thêm bảng membership theo thời gian, chưa làm bây giờ.

## Hợp đồng tháo lắp nguồn — ranh giới spec này ↔ code ETL

Yêu cầu chủ dự án 2026-08-25: đổi nguồn raw = thay khối code ETL khác, vẫn chèn vào bảng chuẩn — nguồn tháo lắp như module. Phân vai:

| Bộ phận | Vai trò trong việc tháo lắp | Nằm ở đâu |
|---|---|---|
| Registry ánh xạ (`*_external_id`, `indicator_source`) | **Ổ cắm** — adapter mới cắm vào bằng dòng ánh xạ, bảng dữ liệu không biết nguồn tồn tại | Spec này (bước 2/4/5) |
| Bảng canonical + *ngữ nghĩa ghi* từng bảng (append / UPSERT / thêm-version) | **Mặt bích cố định** — hợp đồng mọi adapter phải tôn trọng | Spec này (bước 2–7) |
| `staging.raw_payload` | Kho đồ thô theo nguồn — đổi adapter vẫn còn đồ cũ để dựng lại | Spec này (bước 7) |
| `ops.data_domain_state` | **Công tắc** miền × nguồn: `active/frozen/migrating` | Spec này (bước 7) |
| Cấu trúc module code: mỗi nguồn một **adapter** (fetch + parse + chuẩn hoá đơn vị/múi giờ), mỗi miền một **writer** (giữ ngữ nghĩa ghi) | Phần chuyển động | **Plan riêng** khi dựng lát ETL đầu, sau khi schema chốt |

Giữ nguyên ràng buộc đã chốt ở [market-data-store §9.6](../../../20-design/market-data-store.md): **không dựng khung plugin trừu tượng** cho nguồn chưa biết — tháo lắp đạt bằng ranh giới adapter/writer + registry, không bằng framework tổng quát viết sớm.

## Hồ sơ kèm theo

- **[Review toàn cục 2026-08-25](review-2026-08-25.md)** — 6 lỗi đã sửa (F1–F6), 6 điểm làm rõ, 3 điểm ghi nhận có chủ đích; đối chiếu theo mục tiêu G1–G5
- Sơ đồ quan hệ để duyệt (artifact, cập nhật theo từng bước): https://claude.ai/code/artifact/f37d1b8f-505e-4915-8009-35b1ee203b01
- Khảo sát hình dạng dữ liệu nguồn phục vụ thiết kế: rút từ [`10-sources/macro/`](../../../10-sources/macro/) và [`10-sources/global/`](../../../10-sources/global/) (đợt đọc 2026-08-25, không đo mới)
