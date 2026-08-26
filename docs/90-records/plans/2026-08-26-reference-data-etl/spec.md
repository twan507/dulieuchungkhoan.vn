# Spec — ETL dữ liệu tham chiếu: danh bạ, danh mục mã, cây ICB

**Ngày:** 2026-08-26 · **Nhánh:** `feat/reference-data-etl` · **Việc [6]** của [lộ trình](../../../00-overview/roadmap.md) — nút thắt mở khoá cả nhánh ETL thị trường lẫn pipeline tin.

Lát này lấp năm bảng đang **rỗng hoàn toàn** trong `postgres-data`: `market.issuer`, `market.security`, hai bảng `*_external_id`, cộng `market.icb_industry`. Lược đồ đã dựng sẵn từ [phiên schema 2026-08-25](../2026-08-25-postgres-data-schema/step-02-market-identity.md); luật nghiệp vụ đã chốt ở đó, spec này quyết **cách thực hiện**.

---

## 1. Quyết định chốt trong phiên brainstorm 2026-08-26 (chủ dự án)

| # | Câu hỏi | Chốt |
|---|---|---|
| 1 | Danh mục nạp tới đâu | **Cổ phiếu + ETF/quỹ.** Phái sinh để lát riêng dù điều kiện mở lại của step-02 §3b **đã đạt** (đo socket 2026-08-26). Chứng quyền · lô lẻ · trái phiếu vẫn loại có chủ đích (CLAUDE.md §2.2) |
| 2 | `industry_icb_map` lấp thế nào | **Hoãn.** Lát này để `issuer.industry_id` rỗng và `industry_icb_map` rỗng; nạp sau. Hệ quả nhận thức rõ: [7] ETL giá mở khoá được, nhưng **lọc tin theo ngành của [10] và khung ngành cho skill vẫn chờ** |
| 3 | Mã biến mất khỏi `/quotes` | **Tự đổi `delisted`, có chốt chặn sụt.** Không bao giờ xoá dòng |
| 4 | Chỉ số thị trường | **Nạp cả 18**, phẳng — chỉ `security_type='index'`, **không** thêm cột phân loại. Việc chia toàn-thị-trường / rổ / ngành là quyết định nội dung, hoãn cùng nhóm với [2] |

**Chiến lược ghi: dựng lại trọn trong một giao dịch.** ~2.500 dòng nên chi phí không đáng kể, và tính nguyên tử cho thứ quý nhất — không bao giờ có trạng thái nửa vời trong kho. Phương án "tính diff rồi áp" bị loại: `ops.etl_run.stats` đã đủ chỗ ghi *"thêm 3, đổi 12, huỷ 1"*, không cần thêm một tầng code để có bản kiểm toán.

---

## 2. Nguồn — năm endpoint

| Endpoint | Bản ghi *(đo)* | Cho ta |
|---|---|---|
| `BVSC /quotes?symbols=ALL` | 2.534 *(2026-08-15)* | `symbol` `FullName` `exchange` `StockType` `tradelot` |
| `BVSC /datafeed/instruments` *(không tham số)* | 2.001 *(2026-08-15)* | phủ bổ sung; **không** dùng để phân loại |
| `BVSC getIndexSnapshots` — `GET BVSC/datafeed/indexsnaps` | 20 bản ghi, **18 thật** *(2026-08-25)* | 18 chỉ số thị trường |
| `FIIN_CORE/Master/GetListOrganization` | 1.553 *(2026-08-10)* | `organCode` `ticker` `organName` `organShortName` `comTypeCode` `icbCode` |
| `FIIN_CORE/Master/GetAllIcbIndustry` | 176 *(2026-08-10)* | cây ICB 4 cấp → `market.icb_industry` |

Mọi con số trên là **đo tại ngày ghi kèm** và **đổi theo tuần** — dùng làm mốc so sánh tương đối, cấm hardcode *(danh mục tăng 4 mã trong 5 ngày giữa hai lần đo)*.

⚠️ `GetListOrganization` là endpoint **chậm nhất nhóm tham chiếu (~4,4 s)**. Chấp nhận — job chạy một lần mỗi ngày.

---

## 3. Hợp nhất danh mục — bốn luật

```
/quotes (2.534)   ─┐
                   ├─→ hợp theo (ticker, exchange) ──→ market.security  status=listed
/datafeed/instr.  ─┘        (2.001)
indexsnaps        ─────────→ 18 chỉ số ───────────────→ security_type='index'

GetListOrganization (1.553) ──→ market.issuer
                            └─→ ticker vắng ở BVSC ───→ security status='delisted'
```

**Luật 1 — không endpoint nào là danh mục chuẩn duy nhất.** `security` là **hợp** của hai endpoint BVSC. Mã chỉ có ở một bên vẫn nạp; `exchange` lấy từ bên có nó. *(Bẫy 11 — `VFMVF1` chỉ có ở `/quotes`; 14 hợp đồng phái sinh chỉ có ở `/datafeed/instruments`.)*

**Luật 2 — `security_type` quyết theo đúng MỘT endpoint: `/quotes`.** Bẫy 10 đo được cùng một mã trái phiếu trả `StockType=12` ở `/quotes` nhưng `1` ở `/datafeed/instruments`. Hai bản ghi đều hợp lệ, chỉ khác nghĩa, **và không báo lỗi gì** — hợp nhất rồi phân loại theo `StockType` chung sẽ xếp sai một phần danh mục trong im lặng.

| `StockType` của `/quotes` | `security_type` |
|---|---|
| `2` | `stock` |
| `3` | `etf` *(xem luật 2b)* |
| `4` chứng quyền · `12` trái phiếu | **không nạp** |

**Luật 2b — tách `etf` với `fund_cert` là câu hỏi mở, không được bịa.** CHECK cho phép cả hai, mà `StockType=3` gộp chung *"ETF / Chứng chỉ quỹ"*. **Chưa đo được cách phân biệt.** Cho tới khi đo: nạp toàn bộ `StockType=3` thành `etf`, ghi vào ledger như câu hỏi mở. *(Luật §1.3: chưa đo thì ghi "chưa kiểm" — bịa một quy tắc phân loại rồi 31 mã xếp sai trong im lặng.)*

**Luật 3 — mã có ở FiinTrade mà vắng ở BVSC ⇒ `delisted`, vẫn nạp.** Đây là nguồn duy nhất của tập đã huỷ niêm yết. Tin cũ phải tra được mã đã rời sàn; gắn mã chỉ nhận `listed` *(hợp đồng [architecture §3.1](../../../00-overview/architecture.md))*.

**Luật 4 — ETF, quỹ và chỉ số không có `issuer`.** `security.issuer_id` để rỗng — đúng luật step-02 *"ETF/chỉ số không có ngành"*, và ngành gán ở issuer nên không issuer là không ngành.

### 3.1 Mười tám chỉ số — hằng số trong ETL, không phải migration seed

Phản xạ đầu là nhét vào migration seed như `0003_seed_industry`. **Sai.** Seed ngành nằm ở migration được vì `market.industry` *không có đường ghi runtime*; `market.security` thì có — chính ETL này. Seed vào đó tạo **hai người ghi một bảng**, đúng bẫy hai-nguồn-sự-thật.

Danh mục là **hằng số trong `refdata_indices`**, upsert cùng đường với mọi thứ khác. Một bảng, một người ghi.

Mười tám mã *(đo 2026-08-25)*: `HOSE` · `30` · `100` · `MID` · `SML` · `XALL` · `X50` · `SI` · `ALL` · `DIAMOND` · `FINLEAD` · `FINSELECT` · `HNX` · `HNX30` · `HNXFin` · `HNXMSCap` · `HNXMan` · `UPCOM`.

🔴 **Định danh chỉ số ở BVSC không nhất quán giữa các endpoint** — VN-Index là `HOSE` ở `getIndexSnapshots` nhưng `VNINDEX` ở TVCharts. Vì vậy mỗi chỉ số có **một ticker chuẩn** trong `security` và **nhiều dòng `security_external_id`** phân biệt bằng `external_sub`. Step-02 seam 2b đã đòi đúng điều này: `('bvsc','VNINDEX','tvc')` + `('bvsc','HOSE','snapshot')` cùng trỏ một `security_id`.

⚠️ **Hai bản ghi rác phải lọc** *(đo 2026-08-25)*: dòng header-echo `marketCode='indexCode'` (tên trường đổ vào giá trị) và dòng placeholder `marketCode='0'` toàn số 0 **nhưng vẫn mang `tradingdate` hôm nay**. Lọc theo **danh mục 18 mã đã biết**, không nhận bừa. Cùng họ bẫy "HTTP 200 kèm dữ liệu sai".

---

## 4. Chốt chặn — hai tầng

**Tầng 1 · đếm bản ghi từng endpoint.** So với `record_count` của lần chạy **thành công** gần nhất trong `ops.contract_snapshot`. Sụt quá **2%** ⇒ từ chối cả lượt.

**Tầng 2 · đếm tác động.** Bao nhiêu mã đang `listed` sẽ bị lật `delisted`. Quá **1%** tổng đang niêm yết ⇒ từ chối.

Cần cả hai: tầng 1 bắt response cụt ngay tại nguồn kể cả ở `GetListOrganization` nơi tác hại gián tiếp hơn; tầng 2 canh thẳng **chính thao tác nguy hiểm** và bắt được ca số lượng trông bình thường nhưng nội dung lệch.

Ngưỡng đặt theo **tỷ lệ, không phải số tuyệt đối** — §4.4.4 đòi tiêu chí bất biến, không phải số thời điểm.

### 4.1 Soi ngược: hệ thống chạy bình thường có tự vi phạm không?

| Tình huống | Kích hoạt? |
|---|---|
| Nhịp đổi thật (2.530 → 2.534 trong 5 ngày ≈ 0,16%) | Không — cách ngưỡng hơn một bậc |
| **Lần chạy đầu** (chưa snapshot, kho rỗng) | Không — chưa có mốc ⇒ bỏ qua tầng 1; chưa có `listed` ⇒ tầng 2 không có gì để lật |
| Bỏ chạy một tháng rồi chạy lại | Không — số lượng gần như không trôi |
| Huỷ niêm yết hàng loạt thật | **Có** — và từ chối là đúng: việc đó cần người nhìn |

### 4.2 🔴 Luật quyết định tất cả: chỉ lượt đã COMMIT mới cập nhật mốc

Nếu lượt bị từ chối vẫn ghi `ops.contract_snapshot`, response cụt sẽ **hạ chuẩn** và lần cụt kế tiếp lọt qua êm. **Chốt chặn tự vô hiệu hoá sau đúng một lần hỏng.**

### 4.3 Payload thô hạ cánh trong giao dịch RIÊNG

Khác job OMO (ghi HTML chung giao dịch dữ liệu), và khác **có lý do**: ở đây rollback là đường chạy *bình thường* của chốt chặn, nên bằng chứng về response hỏng phải **sống sót qua rollback**. Không thì ta từ chối một lượt mà không còn gì để khám nghiệm.

Trình tự: fetch → ghi `staging.raw_payload` **commit ngay** → chuyển đổi + ghi `market.*` trong một giao dịch → đánh giá chốt chặn → commit hoặc rollback.

---

## 5. Ngữ nghĩa ghi

- **`issuer` nhận diện qua `issuer_external_id('fiintrade', organCode)`**, không qua tên. Bảng có `UNIQUE (issuer_id, source)` — mỗi doanh nghiệp đúng một mã mỗi nguồn. *(Tên doanh nghiệp đổi được; `organCode` là khoá.)*
- **`security` KHÔNG upsert bằng `ON CONFLICT` đơn giản.** Unique là **một phần**: `(ticker, exchange) WHERE status='listed'`. Tra theo `(ticker, exchange)` **bất kể trạng thái** rồi cập nhật tại chỗ, để mã tái niêm yết **giữ nguyên `security_id`** — **8 bảng đang FK tới nó** *(gồm `news.article_ticker`, `price_daily`, `screener_daily`)*; cấp id mới là bỏ rơi toàn bộ lịch sử đã gắn.
  - Khớp nhiều dòng cùng `(ticker, exchange)` *(chỉ xảy ra khi có nhiều dòng `delisted`)*: ưu tiên dòng `listed`, không có thì lấy `updated_at` mới nhất.
- **`updated_at` chỉ đụng khi có trường thật sự đổi.** Đụng mỗi lượt thì nó thành "giờ chạy gần nhất" và mất hết ý nghĩa — mà đây là cột duy nhất trả lời được *"dữ liệu này cũ chưa"*.
- **Không xoá dòng** — quyết định #3, và 8 FK kia khiến xoá bất khả thi trên thực tế.
- **`issuer.icb_code`** lưu nguyên mã ICB từ `GetListOrganization`; **`industry_id` để rỗng** lát này *(quyết định #2)*.
- **ETL tra `*_external_id` để gọi nguồn, không bao giờ truyền ticker** *(step-02 luật 4 — bẫy `organCode ≠ ticker` ở 41% doanh nghiệp trả HTTP 200 kèm dữ liệu rỗng)*.

---

## 6. Phân rã module — theo khuôn job OMO

| Module | Việc | Thuần? |
|---|---|---|
| `refdata_fetch` | 4 lời gọi HTTP, trả payload thô | I/O |
| `refdata_normalize` | payload → bản ghi có kiểu; lọc 2 dòng rác chỉ số; `security_type` theo `/quotes` | ✅ |
| `refdata_indices` | hằng số 18 chỉ số: mã theo endpoint → ticker chuẩn, tên, sàn | ✅ |
| `refdata_merge` | hợp nhất 2 endpoint BVSC, nối issuer theo ticker, dựng trạng thái đích | ✅ |
| `refdata_guard` | hai tầng chốt chặn | ✅ |
| `refdata_store` | hạ payload thô (giao dịch riêng) · upsert · tính tập huỷ · ghi `contract_snapshot` | DB |
| `refdata_job` | điều phối, y khuôn `omo_job`: `open_run` → việc → `close_run` + `upsert_domain_state` | DB |

Bốn module thuần là nơi **toàn bộ logic khó** nằm — test bằng fixture, không cần mạng, đúng [test-strategy](../../../20-design/test-strategy.md) *(cấm gọi thật nguồn ngoài trong CI)*.

CLI: `python -m etl refdata`, thêm vào `etl/__main__.py` cạnh `omo`.

---

## 7. Seam sẽ test — chốt lại ở plan theo §4.5.2

1. **`normalize`** — fixture payload thật → bản ghi có kiểu; **2 dòng rác chỉ số bị loại**; ánh xạ `StockType` → `security_type`; `StockType=4/12` bị bỏ.
2. **`merge`** — mã chỉ có ở một endpoint BVSC vẫn vào; ticker có ở FiinTrade mà vắng BVSC ⇒ `delisted`; ETF và chỉ số **không** có `issuer_id`; issuer nối đúng theo ticker.
3. **`guard`** — chạm ngưỡng thì từ chối; **lần chạy đầu không mốc thì đi qua**; sụt 0,16% thì không cản *(ca biên ngược — chống ngưỡng đặt quá chặt)*.
4. **`store` trên Postgres thật** — chạy hai lần cho cùng kết quả và `updated_at` **không** đổi ở lượt hai; tái niêm yết **giữ nguyên `security_id`**; unique một phần được tôn trọng; **chạy dưới role `dlck_etl`**, không phải owner.
5. **`job`** — **chốt chặn nổ ⇒ rollback, `etl_run` failed, `contract_snapshot` KHÔNG cập nhật.**

> Seam 5 là **test giá trị nhất của cả lát**: nó khoá luật §4.2. Nếu luật đó sai thì chốt chặn tự vô hiệu sau đúng một lần hỏng — và không có gì báo.
>
> Seam 4 chạy dưới role production là **bài học §3.5 đã cắn ba lần** (`TRUNCATE` của `omo_flow`; `assert_migrated` đòi DDL; task Scheduler lệnh rỗng). Test bằng user owner không bắt được lớp lỗi này.

Fixture chụp từ payload thật **một lần**, lưu ở `backend/tests/etl/fixtures/`, kèm ngày chụp.

---

## 8. Vận hành

- **Nhịp chạy: một lần mỗi ngày làm việc, trước phiên** — danh mục đổi vài mã mỗi tuần, và [7] ETL giá cần danh bạ tươi trước khi chạy. Đăng ký qua `scripts/register-tasks.ps1` theo đúng khuôn 4 task OMO, có `Assert-TaskCommand`.
- **Trước khi bật task: chạy tay chính lệnh đó dưới đúng credential production ít nhất một lần** *(CLAUDE.md §3.5 — phép kiểm rẻ đứng trên tất cả)*.
- `ops.data_domain_state`: `domain='market.reference'`, watermark = ngày chạy.

---

## 9. Ngoài phạm vi spec này

Phân ba loại theo §1.4:

| Việc | Loại | Lý do |
|---|---|---|
| `industry_icb_map` + `issuer.industry_id` | **Hoãn có chủ đích** | Quyết định #2 — là nội dung chứ không phải code; nạp ở lát sau |
| Phân loại con của chỉ số (toàn thị trường / rổ / ngành) | **Hoãn có chủ đích** | Quyết định #4 — nội dung, và thêm cột lúc chưa ai tiêu thụ là đúng cái §4.4.2 cấm |
| Phái sinh (14 hợp đồng) | **Hoãn có chủ đích** | Điều kiện mở lại của step-02 §3b đã đạt, nhưng kéo theo migration `security_type` + bảng thuộc tính hợp đồng + quyết định lược đồ tick. Lát riêng |
| Chứng quyền · lô lẻ · trái phiếu | **Loại có chủ đích** | CLAUDE.md §2.2 — có dữ liệu, không có giá trị phân tích |
| `market.metric_dictionary` | **Đã có đường khác** | 729 mã trường đã giải mã sẵn trong [`field-dictionary.json`](../../../10-sources/market/field-dictionary.json); nạp là lát riêng, không phụ thuộc lát này |
| Phân biệt `etf` với `fund_cert` | **Chưa kiểm — chưa có cách** | `StockType=3` gộp chung, chưa đo được cách tách. Luật 2b: nạp hết thành `etf` và ghi câu hỏi mở |

---

## 10. Checklist quét tài liệu sống khi spec chốt (§1.7)

- [ ] [roadmap §3](../../../00-overview/roadmap.md) — cây phụ thuộc: [6] chuyển trạng thái, ghi rõ phần ngành còn treo
- [ ] [architecture §3.1](../../../00-overview/architecture.md) — mắt xích danh bạ ↔ pipeline tin: ghi rằng danh bạ đã nạp nhưng **ngành chưa**, nên tầng lọc ngành của tin vẫn chặn
- [ ] [market-data-store §4](../../../20-design/market-data-store.md) — mục ETL REST: bổ sung job `refdata` và nhịp chạy
- [ ] [database/README.md](../../../../database/README.md) — bảng nào đã có dữ liệu thật
- [ ] [90-records/README.md](../../README.md) — thêm dòng plan này
- [ ] `docs/10-sources/market/` — **chỉ sửa nếu đo lại** (§1.2); ETL đo được con số mới thì ghi kèm ngày đo
