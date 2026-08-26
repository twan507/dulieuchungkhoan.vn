# Spec — ETL dữ liệu tham chiếu: danh bạ, danh mục mã, cây ICB

**Ngày:** 2026-08-26 · **Sửa bản 2** sau review độc lập (opus) + kiểm chứng chéo — xem [ledger](ledger.md) · **Nhánh:** `feat/reference-data-etl` · **Việc [6]** của [lộ trình](../../../00-overview/roadmap.md) — nút thắt mở khoá cả nhánh ETL thị trường lẫn pipeline tin.

Lát này lấp năm bảng đang **rỗng hoàn toàn** trong `postgres-data`: `market.issuer`, `market.security`, hai bảng `*_external_id`, cộng `market.icb_industry`. Lược đồ đã dựng sẵn từ [phiên schema 2026-08-25](../2026-08-25-postgres-data-schema/step-02-market-identity.md); luật nghiệp vụ đã chốt ở đó, spec này quyết **cách thực hiện**.

---

## 1. Quyết định chốt trong phiên brainstorm 2026-08-26 (chủ dự án)

| # | Câu hỏi | Chốt |
|---|---|---|
| 1 | Danh mục nạp tới đâu | **Cổ phiếu + ETF/quỹ.** Phái sinh để lát riêng dù điều kiện mở lại của step-02 §3b **đã đạt** (đo socket 2026-08-26). Chứng quyền · lô lẻ · trái phiếu vẫn loại có chủ đích (CLAUDE.md §2.2) |
| 2 | `industry_icb_map` lấp thế nào | **Hoãn.** Lát này để `issuer.industry_id` rỗng và `industry_icb_map` rỗng; nạp sau. Hệ quả nhận thức rõ: [7] ETL giá mở khoá được, nhưng **lọc tin theo ngành của [10] và khung ngành cho skill vẫn chờ** |
| 3 | Mã đang `listed` vắng khỏi trạng thái đích của lượt | **Tự đổi `delisted`, có chốt chặn sụt** (luật chính xác: §3 luật 3). Không bao giờ xoá dòng |
| 4 | Chỉ số thị trường | **Nạp cả 18**, phẳng — chỉ `security_type='index'`, **không** thêm cột phân loại. Việc chia toàn-thị-trường / rổ / ngành là quyết định nội dung, hoãn cùng nhóm với [2] |

**Chiến lược ghi: tính trạng thái đích trọn vẹn rồi áp trong MỘT giao dịch — không xoá dòng nào.** *(Không phải "xoá-rồi-nạp": role `dlck_etl` không có quyền `TRUNCATE` — đúng lớp lỗi §3.5 đã trả giá — và 7 bảng đang FK tới `security`.)* ~2.500 dòng nên chi phí không đáng kể; tính nguyên tử cho thứ quý nhất — không bao giờ có trạng thái nửa vời trong kho. `market.icb_industry` **nằm trong cùng giao dịch này**. Phương án "tính diff rồi áp" bị loại: `ops.etl_run.stats` đã đủ chỗ ghi *"thêm 3, đổi 12, huỷ 1"*.

---

## 2. Nguồn — BỐN endpoint

| Endpoint | Bản ghi *(đo)* | Cho ta |
|---|---|---|
| `BVSC /quotes?symbols=ALL` | 2.534 *(2026-08-15)* | `symbol` `FullName` `exchange` `StockType` `tradelot` |
| `BVSC getIndexSnapshots` — `GET BVSC/datafeed/indexsnaps` | 20 bản ghi, **18 thật** *(2026-08-25)* | 18 chỉ số thị trường |
| `FIIN_CORE/Master/GetListOrganization?language=vi` | 1.553 *(2026-08-10)* | `organCode` `ticker` `comGroupCode` `organName` `organShortName` `comTypeCode` `icbCode` |
| `FIIN_CORE/Master/GetAllIcbIndustry?language=vi` | 176 *(2026-08-10)* | cây ICB 4 cấp → `market.icb_industry` |

**`language=vi` chốt cứng cho cả hai endpoint FiinTrade** — tham số này đổi nội dung `organName`/`organShortName`/`icbName`; không chốt thì tên trong kho phụ thuộc mặc định của nguồn.

🔴 **`/datafeed/instruments` KHÔNG thuộc lát này** — đây là **thu hẹp có chủ đích luật 5b của step-02** (*"danh bạ = hợp nhất hai endpoint"*), ghi lại tường minh: đóng góp **độc quyền đo được** của nó chỉ là 14 hợp đồng phái sinh (bẫy 11) — thứ đã hoãn theo quyết định #1. Nạp phần còn lại của nó thì vướng bẫy 10: `StockType` của nó không tin được, mà luật 2 dưới đây cấm phân loại theo nó. Endpoint này quay lại **cùng lát phái sinh** — xem §9.

Mọi con số trên là **đo tại ngày ghi kèm** và **đổi theo tuần** — mốc so sánh tương đối, cấm hardcode *(danh mục tăng 4 mã trong 5 ngày giữa hai lần đo)*.

⚠️ `GetListOrganization` chậm nhất nhóm (~4,4 s). Chấp nhận — một lần mỗi ngày.

---

## 3. Hợp nhất danh mục — sáu luật

```
/quotes (2.534)        ──→ StockType 2/3 ─────→ market.security  status=listed
indexsnaps (18 thật)   ──→ đối chiếu hằng số 18 chỉ số ─→ security_type='index'
GetListOrganization    ──→ market.issuer (+ QU nối ETF/quỹ)
        └─→ ticker không có trong TRẠNG THÁI ĐÍCH ─→ security status='delisted'
```

**Luật 1 — trạng thái đích của lượt = hợp của ba nguồn:** mã `StockType=2/3` từ `/quotes` ∪ 18 chỉ số từ hằng số (đối chiếu `indexsnaps`) ∪ ticker chỉ có ở `GetListOrganization`.

**Luật 2 — `security_type` quyết theo đúng MỘT endpoint: `/quotes`.** Bẫy 10 đo được cùng một mã trái phiếu trả `StockType=12` ở `/quotes` nhưng `1` ở `/datafeed/instruments` — phân loại theo nguồn khác sẽ xếp sai trong im lặng.

| Nguồn gốc dòng | `security_type` |
|---|---|
| `/quotes` `StockType=2` | `stock` |
| `/quotes` `StockType=3` | `etf` *(luật 2b)* |
| `/quotes` `StockType=4/12` | **không nạp** (chứng quyền, trái phiếu — §2.2) |
| `/quotes` `StockType` **lạ** | **không nạp** + đếm vào `etl_run.stats` + log warning *(đồng nhất luật "mã ICB lạ không chặn job" của step-02)* |
| Hằng số 18 chỉ số | `index` |
| Ticker chỉ có ở FiinTrade | `stock` *(GetListOrganization chỉ chứa doanh nghiệp — an toàn)* |

**Luật 2b — tách `etf` với `fund_cert` là câu hỏi mở, không được bịa.** `StockType=3` gộp chung *"ETF / Chứng chỉ quỹ"*, chưa đo được cách phân biệt. Nạp toàn bộ thành `etf`, ghi câu hỏi mở vào ledger. *(§1.3: chưa đo thì ghi "chưa kiểm".)*

**Luật 3 — huỷ niêm yết: so với TRẠNG THÁI ĐÍCH, không so với một endpoint.** Dòng đang `status='listed'` trong kho mà ticker **không có trong trạng thái đích hợp nhất của lượt** (luật 1) ⇒ đổi `delisted`. Không xoá.

> Vì trạng thái đích **đã gồm hằng số 18 chỉ số**, luật này tự nhiên: (a) **không bao giờ huỷ oan chỉ số** — chúng vắng ở `/quotes` nhưng luôn có trong đích *(lỗ Critical #1 của bản 1: viết "vắng ở `/quotes` ⇒ delisted" sẽ lật cả 18 chỉ số, và 18/~2.023 = 0,89% — dưới ngưỡng tầng 2, chốt chặn im lặng cho qua)*; (b) trả lời luôn ca "ETF bị huỷ niêm yết" — ETF không bao giờ có ở `GetListOrganization`, vắng khỏi `/quotes` là vắng khỏi đích ⇒ huỷ đúng; (c) một chỉ số chỉ bị huỷ khi **gỡ khỏi hằng số** — một thay đổi code có chủ đích.

**Luật 4 — nối issuer.** Cổ phiếu nối `issuer` theo ticker khớp `GetListOrganization`. **Chênh đo được:** `/quotes` có 1.974 cổ phiếu, FiinTrade có 1.553 doanh nghiệp ⇒ **~400+ cổ phiếu (chủ yếu UPCOM) không có issuer** — nhóm này `issuer_id` NULL, **đếm vào `etl_run.stats`**, không phải lỗi. ETF/quỹ nối issuer **nếu** FiinTrade có bản ghi khớp ticker *(24 bản ghi `comTypeCode='QU'` — không nối thì 24 issuer mồ côi vĩnh viễn)*; không có thì NULL. Chỉ số không có issuer. *(Ngành gán ở issuer — dòng không issuer thì không ngành, đúng step-02.)*

**Luật 5 — `exchange` (cột NOT NULL) theo nguồn gốc dòng:**

| Nguồn gốc | `exchange` |
|---|---|
| `/quotes` | trường `exchange` của nó (`HOSE`/`HNX`/`UPCOM`) |
| Ticker chỉ có ở FiinTrade | **ánh xạ `comGroupCode`**: `VNINDEX`→`HOSE` · `HNXIndex`→`HNX` · `UpcomIndex`→`UPCOM` *(quy ước FiinTrade khác BVSC — bảng ở [03-fiin-reference.md](../../../10-sources/market/03-fiin-reference.md); đừng nhầm chuỗi `VNINDEX` này với mã TVC của VN-Index ở §3.1)* |
| Chỉ số | cột `exchange` trong hằng số §3.1 |

**Luật 6 — trùng ticker trong `GetListOrganization`: chưa đo, phải kiểm ở fixture.** Nếu gặp: ưu tiên `organTypeCode='DN'` (1.522/1.553), bản ghi còn lại đếm + log, không chặn job. Plan phải kiểm fixture thật và ghi kết quả vào ledger.

### 3.1 Hằng số 18 chỉ số — nội dung đầy đủ, một bảng một người ghi

**Vì sao là hằng số trong ETL chứ không phải migration seed:** seed ngành (`0003_seed_industry`) hợp lệ vì `market.industry` không có đường ghi runtime; `market.security` thì có — chính ETL này. Seed vào đó tạo **hai người ghi một bảng**.

| Mã `indexsnaps` | Ticker chuẩn | Tên | `exchange` | Mã TVC |
|---|---|---|---|---|
| `HOSE` | `VNINDEX` | VN-Index | HOSE | `VNINDEX` ✅ *(đo 2026-08-15)* |
| `30` | `VN30` | VN30 | HOSE | `VN30` ✅ |
| `100` | `VN100` | VN100 | HOSE | chưa kiểm |
| `MID` | `VNMID` | VNMidcap | HOSE | chưa kiểm |
| `SML` | `VNSML` | VNSmallcap | HOSE | chưa kiểm |
| `XALL` | `VNXALL` | VNX AllShare | HOSE | chưa kiểm |
| `X50` | `VNX50` | VNX50 | HOSE | chưa kiểm |
| `SI` | `VNSI` | VN Sustainability | HOSE | chưa kiểm |
| `ALL` | `VNALL` | VNAllShare | HOSE | chưa kiểm |
| `DIAMOND` | `VNDIAMOND` | VN Diamond | HOSE | chưa kiểm |
| `FINLEAD` | `VNFINLEAD` | VN Financial Lead | HOSE | chưa kiểm |
| `FINSELECT` | `VNFINSELECT` | VN Financial Select | HOSE | chưa kiểm |
| `HNX` | `HNXINDEX` | HNX-Index | HNX | `HNXIndex` ✅ |
| `HNX30` | `HNX30` | HNX30 | HNX | chưa kiểm |
| `HNXFin` | `HNXFIN` | HNX Finance | HNX | chưa kiểm |
| `HNXMSCap` | `HNXMSCAP` | HNX Mid/Small Cap | HNX | chưa kiểm |
| `HNXMan` | `HNXMAN` | HNX Manufacturing | HNX | chưa kiểm |
| `UPCOM` | `UPINDEX` | UPCOM-Index | UPCOM | chưa kiểm |

- **Ticker chuẩn là định danh nội bộ của dự án** (mình đặt, không phải khai của nguồn — đặt được tự do). **`exchange` của rổ liên sàn VNX (`XALL`/`X50`) và các rổ chuyên đề gán `HOSE`** theo sàn vận hành chỉ số — cũng là quy ước nội bộ, ghi ở đây làm chỗ tra duy nhất.
- **Mã TVC: chỉ 3/18 đã đo** ([02-bvsc-tvcharts.md](../../../10-sources/market/02-bvsc-tvcharts.md) — `HNX`/`UPCOM` thử rồi trả `no_data`). **Chỉ ghi dòng `external_sub='tvc'` cho 3 mã đã đo**; 15 mã kia KHÔNG bịa (§1.3).
- `security_external_id` cho chỉ số: `('bvsc', <mã indexsnaps>, 'snapshot')` cho cả 18 + `('bvsc', <mã TVC>, 'tvc')` cho 3 — thoả đúng seam 2b step-02: VN-Index mang `('bvsc','VNINDEX','tvc')` + `('bvsc','HOSE','snapshot')` cùng trỏ một `security_id`.
- 🔴 **PK của `security_external_id` là `(source, external_code)` — `external_sub` KHÔNG tham gia PK.** Mã `indexsnaps` như `ALL`/`MID`/`SML`/`SI` có hình dạng trùng ticker cổ phiếu hợp lệ. Nếu một cổ phiếu trùng tên xuất hiện, hai identity **âm thầm đè nhau**. Luật: mỗi lượt normalize **assert giao của 18 mã indexsnaps với tập symbol `/quotes` = ∅**, khác rỗng thì fail to — không đoán.

⚠️ **Hai bản ghi rác của `indexsnaps` phải lọc** *(đo 2026-08-25)*: dòng header-echo `marketCode='indexCode'` và dòng placeholder `marketCode='0'` toàn số 0 nhưng vẫn mang `tradingdate` hôm nay. Lọc bằng đối chiếu **hằng số 18 mã**, không nhận bừa.

### 3.2 `security_external_id` cho dòng KHÔNG phải chỉ số

| Nhóm | Dòng ghi |
|---|---|
| Cổ phiếu / ETF có ở `/quotes` | `('bvsc', ticker, '')` |
| Ticker chỉ có ở FiinTrade (`delisted`) | **không ghi** — không còn gì để gọi ở đâu; đường gọi FiinTrade đi qua `issuer_external_id('fiintrade', organCode)` |

*(Luật step-02 "ETL tra `*_external_id` để gọi nguồn, không truyền ticker" là ràng buộc cho **các lát sau** — lát này chính là lát dựng bảng tra đó; cả 4 endpoint của nó đều không nhận tham số theo mã.)*

---

## 4. Chốt chặn — hai tầng

**Mốc so sánh: `ops.etl_run.stats` của lần chạy `status='success'` gần nhất của chính job `market.refdata`.** KHÔNG dùng `ops.contract_snapshot` — bảng đó **đã có chủ khác** (bộ giám sát hợp đồng, cũng chạy trước phiên, đếm trên mẫu 51 mã — job khác ghi cùng endpoint là mốc trôi, và số của nó không cùng ngữ nghĩa). Nhờ đặt mốc ở `etl_run`, luật §4.2 **tự thi hành về mặt cấu trúc**: lượt failed không bao giờ được đọc làm mốc.

**Tầng 1 · đếm bản ghi SAU normalize, từng endpoint:**

| Endpoint | Luật |
|---|---|
| `/quotes` · `GetListOrganization` · `GetAllIcbIndustry` | sụt quá **2%** so mốc ⇒ từ chối cả lượt |
| `indexsnaps` | **khớp đúng tập**: thiếu bất kỳ mã nào trong 18 mã đã biết ⇒ từ chối. *(Ngưỡng tỷ lệ vô nghĩa ở N=20: mất một dòng rác đã là 5% — cò súng nhạy oan; khớp tập vừa mạnh hơn vừa không giòn)* |

**Tầng 2 · đếm tác động:** số mã đang `listed` sẽ bị lật `delisted` quá **1%** tổng đang niêm yết ⇒ từ chối.

Cần cả hai: tầng 1 bắt response cụt tại nguồn; tầng 2 canh thẳng thao tác nguy hiểm, bắt cả ca số lượng bình thường nhưng nội dung lệch. Ngưỡng theo **tỷ lệ** (§4.4.4 — tiêu chí bất biến, không phải số thời điểm).

### 4.1 Soi ngược: hệ thống chạy bình thường có tự vi phạm không?

| Tình huống | Kích hoạt? |
|---|---|
| Nhịp đổi thật (2.530 → 2.534 trong 5 ngày ≈ 0,16%) | Không — cách ngưỡng hơn một bậc |
| **Lần chạy đầu** (chưa có `etl_run` success, kho rỗng) | Không — chưa mốc ⇒ bỏ tầng 1 (trừ khớp-tập `indexsnaps`, luôn chạy được); chưa `listed` ⇒ tầng 2 không có gì lật |
| Bỏ chạy một tháng rồi chạy lại | Không — số lượng gần như không trôi |
| `indexsnaps` bớt một dòng RÁC (20→19 thô) | Không — đếm sau normalize, 18 mã vẫn đủ |
| Huỷ niêm yết hàng loạt thật | **Có** — từ chối là đúng: việc đó cần người nhìn. Mở khoá: §4.4 |

### 4.2 Chỉ lượt đã COMMIT mới thành mốc

Nếu lượt bị từ chối vẫn hạ được mốc, response cụt sẽ **hạ chuẩn** và lần cụt kế tiếp lọt qua êm — chốt chặn tự vô hiệu sau đúng một lần hỏng. Với mốc đặt ở `etl_run.stats` + `status='success'`, luật này được cấu trúc thi hành; ghi ra đây để **seam test khoá nó vĩnh viễn** (seam 5).

### 4.3 Bằng chứng khi từ chối — ghi staging TRONG GIAO DỊCH RIÊNG, và CHỈ khi từ chối

[Step-07 §1](../2026-08-25-postgres-data-schema/step-07-staging-ops.md) đã chốt danh bạ **không vào staging** (*"crawl lại rẻ"*) — spec này **giữ nguyên quyết định đó cho đường chạy bình thường**. Ngoại lệ hẹp, ghi tường minh: **khi chốt chặn từ chối**, payload đã fetch được ghi vào `staging.raw_payload` trong giao dịch riêng (commit độc lập với rollback của giao dịch dữ liệu), vì đây là **bằng chứng để khám nghiệm một response nghi hỏng** — đúng vai trò "trọng tài khi nghi ngờ" của staging, và crawl lại KHÔNG thay được: response cụt lần sau có thể đã lành.

- `endpoint_key`: `refdata:quotes` · `refdata:indexsnaps` · `refdata:organization` · `refdata:icb`. `content_type='json'`, ghi vào `payload` (jsonb), `meta` mang `run_id` + lý do từ chối.
- Payload không parse được (WAF, rác) **không vào staging** — đi vào `etl_run.error`, đúng luật hình thức của step-07.

### 4.4 Mở khoá khi từ chối đúng

`python -m etl refdata --accept-drop`: chạy lại và bỏ qua hai tầng chốt chặn **đúng một lượt**, ghi `{"accept_drop": true}` vào `etl_run.stats`. Lượt đó commit thì thành mốc mới như thường. Không có cờ này, huỷ niêm yết hàng loạt thật sẽ đóng băng danh bạ vĩnh viễn.

---

## 5. Ngữ nghĩa ghi

- **`issuer` nhận diện qua `issuer_external_id('fiintrade', organCode)`**, không qua tên *(tên đổi được; `organCode` là khoá; bẫy 1 — 41% doanh nghiệp `organCode ≠ ticker`)*. Cột: `name`←`organName` (NOT NULL — nguồn phủ 100%), `short_name`←`organShortName`, `com_type_code`←`comTypeCode`, `icb_code`←`icbCode`.
- 🔴 **`issuer.industry_id` KHÔNG nằm trong danh sách cột UPDATE.** Step-02 luật 2: *tay thắng máy* — ETL không ghi đè giá trị đã gán tay. Viết "để rỗng lát này" thành lệnh `SET industry_id=NULL` mỗi lượt thì lát ngành sau vừa đổ dữ liệu vào, job hằng ngày sẽ xoá sạch.
- **`security` khớp theo TICKER (một mình), không theo `(ticker, exchange)`.** Ticker là duy nhất toàn thị trường VN; khớp kèm `exchange` thì ca **chuyển sàn** (UPCOM→HOSE — chuyện thường) không khớp dòng cũ ⇒ cấp `security_id` mới ⇒ mất toàn bộ lịch sử đã gắn (**7 bảng · 8 ràng buộc FK** đang trỏ tới, gồm `news.article_ticker`, `price_daily`). Đổi sàn = UPDATE `exchange` tại chỗ, giữ id, đếm vào `etl_run.stats`. Khớp nhiều dòng cùng ticker: ưu tiên `listed`, rồi `updated_at` mới nhất; các dòng thừa giữ nguyên.
- **`full_name`:** dòng từ `/quotes` ← `FullName`; dòng FiinTrade-only ← `organName`; chỉ số ← cột Tên của hằng số §3.1.
- **`updated_at` chỉ đụng khi có trường thật sự đổi** — đụng mỗi lượt thì nó thành "giờ chạy gần nhất", mất khả năng trả lời *"dữ liệu này cũ chưa"*. **`ingested_at`** (ở `icb_industry` và hai bảng `*_external_id` — migration `0010`) **chỉ ghi lúc INSERT, không bao giờ UPDATE** — seam 4 (idempotency) tính cả hai cột này vào phép so.
- **`icb_industry`:** upsert theo PK `icb_code`, **cùng giao dịch** dựng lại. Mã ICB biến mất khỏi nguồn: **giữ nguyên dòng** (`issuer.icb_code` có thể còn trỏ tới; không FK nhưng vẫn là tham chiếu), đếm + log. Không xoá.
- **Không xoá dòng ở bất kỳ bảng nào** — quyết định #3.
- **`ops.data_domain_state`: hai dòng** — `('market.reference','bvsc')` và `('market.reference','fiintrade')`, cùng watermark = ngày chạy *(PK là `(domain, source)`; khuôn OMO ghi `('macro.omo','sbv')`)*.

---

## 6. Phân rã module — theo khuôn job OMO

| Module | Việc | Thuần? |
|---|---|---|
| `refdata_fetch` | **4** lời gọi HTTP, trả payload thô | I/O |
| `refdata_normalize` | payload → bản ghi có kiểu; lọc rác `indexsnaps` theo hằng số; assert giao 18 mã ∩ symbol `/quotes` = ∅; `StockType` lạ → bỏ + đếm | ✅ |
| `refdata_indices` | hằng số bảng §3.1 (18 dòng, 5 cột) | ✅ |
| `refdata_merge` | dựng trạng thái đích (luật §3), nối issuer, tính tập lật `delisted` | ✅ |
| `refdata_guard` | hai tầng §4 (nhận mốc làm tham số — thuần) | ✅ |
| `refdata_store` | upsert 5 bảng trong một giao dịch · ghi staging-khi-từ-chối (giao dịch riêng) | DB |
| `refdata_job` | điều phối y khuôn `omo_job`: `open_run` → fetch → normalize → merge → guard → store → `close_run` + `upsert_domain_state`; cờ `--accept-drop` | DB |

Bốn module thuần chứa **toàn bộ logic khó** — test bằng fixture, không mạng *(test-strategy: cấm gọi thật nguồn ngoài trong CI)*.

CLI: `python -m etl refdata [--accept-drop]` — thêm cạnh `omo`, **sửa cả chuỗi help** `(hỗ trợ: omo)` trong `etl/__main__.py`.

---

## 7. Seam sẽ test — chốt lại ở plan theo §4.5.2

1. **`normalize`** — fixture payload thật → bản ghi có kiểu; 2 dòng rác `indexsnaps` bị loại (literal: `marketCode='indexCode'` và `'0'`); `StockType=4/12` bị bỏ; `StockType` lạ bị bỏ + đếm; assert-giao nổ khi cấy một symbol `ALL` giả vào fixture `/quotes`.
2. **`merge`** — ticker FiinTrade-only ⇒ `delisted` + `security_type='stock'` + `exchange` từ `comGroupCode`; ETF khớp bản ghi `QU` thì có `issuer_id`, không khớp thì NULL; cổ phiếu không có issuer ⇒ NULL + đếm; **18 chỉ số KHÔNG nằm trong tập lật `delisted` dù fixture `/quotes` không chứa chúng** *(khoá Critical #1)*.
3. **`guard`** — chạm 2% ⇒ từ chối; sụt 0,16% ⇒ qua *(biên ngược)*; **lần đầu không mốc ⇒ qua**; `indexsnaps` thiếu 1 trong 18 mã ⇒ từ chối; mất dòng rác (20→19 thô) ⇒ qua.
4. **`store` trên Postgres thật, dưới role `dlck_etl`** *(bài học §3.5 — ba lần trả giá)* — chạy hai lần: kết quả y hệt, `updated_at` **và `ingested_at`** không đổi lượt hai; đổi sàn giữ nguyên `security_id`; tái niêm yết giữ nguyên `security_id`; seam 2b step-02: VN-Index mang `('bvsc','VNINDEX','tvc')` + `('bvsc','HOSE','snapshot')` cùng một `security_id`; `industry_id` gán tay trước đó **không bị đè**.
5. **`job`** — chốt chặn nổ ⇒ giao dịch dữ liệu rollback, `etl_run` failed, **mốc không đổi** (lượt sau vẫn so với mốc cũ), staging **có** bản ghi `refdata:*` với `meta.run_id` đúng; `--accept-drop` cho lượt đó qua và thành mốc mới.

> Seam 5 khoá luật §4.2 — sai luật đó thì chốt chặn tự vô hiệu sau một lần hỏng, không gì báo. Seam 2 và 4 khoá hai lỗi Critical nặng nhất mà review bản 1 tìm ra.

Expected của mọi seam lấy từ **bảng đo trong `docs/10-sources/market/`** hoặc giải tay trên fixture — không tính lại theo cách code tính (§4.5.3). Fixture chụp payload thật **một lần**, để ở `backend/tests/etl/fixtures/`, kèm ngày chụp; lúc chụp phải **kiểm và ghi vào ledger**: có trùng ticker trong `GetListOrganization` không (luật 6).

---

## 8. Vận hành

- **Nhịp: 08:00 mỗi ngày làm việc** — trước `dlck-ingester` 08:30, để [7] ETL giá và ingester có danh bạ tươi. Đăng ký qua `scripts/register-tasks.ps1` (khuôn 4 task OMO, `Assert-TaskCommand`).
- **Trước khi bật task: chạy tay chính lệnh đó dưới đúng credential production ít nhất một lần** *(§3.5)*.
- Job ghi `ops.etl_run` (job=`market.refdata`) — `stats` tối thiểu: đếm theo endpoint sau normalize, thêm/đổi/lật `delisted`, cổ phiếu không issuer, `StockType` lạ, đổi sàn.

---

## 9. Ngoài phạm vi spec này

Phân ba loại theo §1.4:

| Việc | Loại | Lý do |
|---|---|---|
| `/datafeed/instruments` trong danh bạ | **Hoãn có chủ đích** | Thu hẹp luật 5b step-02, lý do ở §2: đóng góp độc quyền đo được = 14 hợp đồng phái sinh (đã hoãn); phần còn lại phân loại không tin được (bẫy 10). Quay lại cùng lát phái sinh |
| Phái sinh (14 hợp đồng) | **Hoãn có chủ đích** | Điều kiện mở step-02 §3b đã đạt, nhưng cần migration `security_type` + bảng thuộc tính hợp đồng + quyết định lược đồ tick. Lát riêng |
| `industry_icb_map` + `issuer.industry_id` | **Hoãn có chủ đích** | Quyết định #2 — nội dung, không phải code |
| Phân loại con của chỉ số | **Hoãn có chủ đích** | Quyết định #4 — thêm cột lúc chưa ai tiêu thụ là đúng cái §4.4.2 cấm |
| Chứng quyền · lô lẻ · trái phiếu | **Loại có chủ đích** | CLAUDE.md §2.2 |
| `security_external_id` cho dòng FiinTrade-only | **Loại có chủ đích** | §3.2 — không còn gì để gọi; đường FiinTrade đi qua `issuer_external_id` |
| `getSymbolMapping` (`BVSC /mapping`) | **Đã có đường khác** | Tập con của `/quotes` (cùng 8 trường trừ giá) — `/quotes` phủ hết |
| `market.metric_dictionary` | **Đã có đường khác** | 729 mã có sẵn trong [`field-dictionary.json`](../../../10-sources/market/field-dictionary.json); nạp là lát riêng |
| Mã TVC của 15/18 chỉ số | **Chưa kiểm — không bịa** | Chỉ 3 mã đã đo (§3.1); đo thêm thì ghi thêm dòng `external_sub='tvc'` |
| Phân biệt `etf` với `fund_cert` | **Chưa kiểm — chưa có cách** | Luật 2b |

---

## 10. Checklist quét tài liệu sống khi spec chốt (§1.7)

- [ ] [roadmap §3](../../../00-overview/roadmap.md) — [6] chuyển trạng thái, ghi rõ phần ngành còn treo
- [ ] [architecture §3.1](../../../00-overview/architecture.md) — danh bạ đã nạp nhưng **ngành chưa** ⇒ tầng lọc ngành của tin vẫn chặn
- [ ] [market-data-store §4](../../../20-design/market-data-store.md) — bổ sung job `refdata`, nhịp 08:00, và ngoại lệ staging-khi-từ-chối (§4.3)
- [ ] [database/README.md](../../../../database/README.md) — bảng nào đã có dữ liệu thật
- [ ] [90-records/README.md](../../README.md) — cập nhật dòng plan này
- [ ] `docs/10-sources/market/` — **chỉ sửa nếu đo lại** (§1.2); ETL đo được số mới thì ghi kèm ngày đo
