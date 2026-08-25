# Plan — Lược đồ PostgreSQL `postgres-data`

**Cách làm việc (chốt 2026-08-25, yêu cầu chủ dự án):** spec tách thành **các bước nhỏ, mỗi bước một file, duyệt tuần tự** — chốt xong file nào coi như file đó xong, không mở lại trừ khi bước sau phát hiện mâu thuẫn (khi đó quay lại sửa file cũ tường minh, ghi lý do). Bản nháp spec một-cục ban đầu đã bỏ, nội dung phân rã vào các bước.

## Trạng thái các bước

| Bước | File | Nội dung | Trạng thái |
|---|---|---|---|
| 1 | [step-01-foundations.md](step-01-foundations.md) | Nguyên tắc nền · bố cục 6 schema · quy ước DDL · migration Alembic | ✅ chốt 2026-08-25 |
| 2 | [step-02-market-identity.md](step-02-market-identity.md) | Định danh: issuer · security · ánh xạ nguồn · **bộ ngành riêng** (thay ICB) | 🟡 **chờ duyệt DDL** — cây ngành đã chốt 2026-08-25, nội dung ở [industry-tree.md](../../../20-design/industry-tree.md) |
| 3 | step-03-market-data.md | Giá EOD + view hệ số · BCTC · từ điển chỉ tiêu · snapshot/screener · sự kiện | ⬜ chưa viết |
| 4 | step-04-macro.md | Registry chỉ tiêu + observation (UPSERT) · cụm OMO | ⬜ chưa viết |
| 5 | step-05-asset.md | Registry tài sản · price/ohlc/fx · luật dầu-vàng-DXY | ⬜ chưa viết |
| 6 | step-06-news.md | Article/revision không ghi đè · gắn mã · tìm kiếm | ⬜ chưa viết |
| 7 | step-07-staging-ops.md | Landing zone · data_domain_state · giám sát hợp đồng · etl_run | ⬜ chưa viết |

Sau khi cả 7 bước chốt: viết `plan.md` (bẻ task thực thi) theo quy trình §4.1.

## Quyết định xuyên suốt đã chốt (áp cho mọi bước)

| # | Quyết định | Ngày |
|---|---|---|
| 1 | Migration bằng **Alembic**, SQL thô trong migration; `postgres-app` là env riêng sau này | 2026-08-25 |
| 2 | Schema tổ chức **theo miền tiêu thụ**, không theo nguồn — ETL biến đổi mọi nguồn về mô hình chuẩn | 2026-08-25 |
| 3 | Định danh bằng **khoá nội bộ** + bảng ánh xạ external cho thực thể (chứng khoán, chỉ tiêu, tài sản) | 2026-08-25 |
| 4 | **Không cột `source` ở bảng dữ liệu** — nguồn có thể đổi, xuất xứ nằm ở bảng ánh xạ registry + `staging`/`ops`. Chỉ tin tức ghi nguồn (báo nào đăng). *Override có ý thức* mục "thêm cột source" ở [market-data-store §9.6](../../../20-design/market-data-store.md) — cập nhật tài liệu sống khi spec chốt xong | 2026-08-25 |
| 5 | **Phân ngành dùng bộ riêng của chủ dự án**, không dùng cây ICB làm chuẩn — chi tiết chốt ở bước 2 | 2026-08-25 |
| 6 | Hai instance `postgres-data`/`postgres-app`, hai connection string, cấm JOIN chéo instance (chốt D — service-topology §4) | 2026-08-25 |

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

- Sơ đồ quan hệ để duyệt (artifact, cập nhật theo từng bước): https://claude.ai/code/artifact/f37d1b8f-505e-4915-8009-35b1ee203b01
- Khảo sát hình dạng dữ liệu nguồn phục vụ thiết kế: rút từ [`10-sources/macro/`](../../../10-sources/macro/) và [`10-sources/global/`](../../../10-sources/global/) (đợt đọc 2026-08-25, không đo mới)
