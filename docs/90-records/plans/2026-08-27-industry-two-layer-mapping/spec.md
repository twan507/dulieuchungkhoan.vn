# Spec — Lát ngành hai lớp: ICB tự gán + gán tay đè lên

**Trạng thái:** 🟡 **chờ thực thi.** Khung do chủ dự án đặt ra 2026-08-27; nội dung mapping đã dựng xong và nằm ở [`worksheets/industry-mapping.xlsx`](../../worksheets/industry-mapping.xlsx). Phần code **chưa động tới** — chủ dự án đang chạy ghi dữ liệu realtime, hoãn có chủ đích.

**Việc [6] của lộ trình** đã thông phần danh bạ; đây là phần NGÀNH còn hoãn (`industry_icb_map` + `issuer.industry_id` đang rỗng).

---

## 1. Vì sao cần đổi, không chỉ cần điền bảng

Quy trình chủ dự án muốn:

> Mã mới thì tự động lấy `icb_code` khớp sang ngành; nếu có can thiệp của lớp thứ hai thì phải theo lớp thứ hai.

Hiện trạng **không chạy được quy trình đó** — đo trên code 2026-08-27:

| Sự thật đo được | Hệ quả |
|---|---|
| [`refdata_store.py:9`](../../../../backend/etl/refdata_store.py) và `:107` — `industry_id` **không có mặt trong cả INSERT lẫn UPDATE** | Lớp 1 **chưa tồn tại**. Mã mới niêm yết có `industry_id` NULL vĩnh viễn, không có gì tự khớp ICB |
| `industry_icb_map` rỗng, luật phân giải mới chỉ nằm trong comment DDL [`0002_market_identity.py:39`](../../../../database/migrations/versions/0002_market_identity.py) | Chưa ai gọi. Bảng có sẵn nhưng không đường vào |
| `issuer.industry_id` là **một cột duy nhất** cho cả máy gán lẫn tay gán | Không phân biệt được nguồn gốc giá trị ⇒ sửa mapping ICB về sau **không áp lại được** mà không đè mất phần đã gán tay |

Luật *tay thắng máy* hiện được cài bằng cách **cấm ETL đụng vào cột đó**. Cách đó bảo vệ được gán tay, nhưng đồng thời giết luôn lớp 1.

## 2. Thiết kế — tách sở hữu, không tách bằng cờ

| Lớp | Chỗ ở | Ai ghi | Luật |
|---|---|---|---|
| **1 · máy** | `market.issuer.industry_id` | job `etl refdata` | Mỗi lượt tra `industry_icb_map` theo `icb_code`: **khớp chính xác trước, không có thì leo `icb_code_path` lấy tổ tiên gần nhất**. Cột thuần máy — ETL ghi đè tự do |
| **2 · tay** | `market.issuer_industry_override` *(bảng mới)* | Người, qua migration seed hoặc công cụ tay | ETL **không đọc, không ghi** |
| **đọc** | view `market.v_issuer_industry` | — | `COALESCE(override.industry_id, issuer.industry_id)` + cột `source` ∈ `manual` \| `icb` \| `NULL` |

```sql
CREATE TABLE market.issuer_industry_override (
  issuer_id   bigint PRIMARY KEY REFERENCES market.issuer,
  industry_id bigint NOT NULL REFERENCES market.industry,   -- luôn level 2
  note        text NOT NULL,                                -- vì sao đè — bắt buộc, không cho để trống
  updated_at  timestamptz NOT NULL DEFAULT now()
);
```

**Đây là đảo luật cũ**, phải nói rõ để người sau không tưởng là hồi quy: từ *"ETL không được ghi `industry_id`"* thành *"ETL sở hữu `industry_id`, tay nằm bảng khác"*. Vẫn đúng nguyên tắc **một bảng một người ghi** mà repo đang theo.

Cái được:

- Sửa mapping ICB xong chỉ cần **chạy lại job** là toàn bộ doanh nghiệp cập nhật theo; phần đè tay còn nguyên.
- Mã mới niêm yết tự có ngành ở lượt refdata hôm sau.
- `note` bắt buộc nên mỗi dòng đè đều truy được lý do — không có ca "ai đó đổi hồi nào không rõ".

## 2b. 🔴 Luật BCTC — ba ngành tài chính khoá theo `com_type_code`

*(Chủ dự án nêu 2026-08-27, đo và chốt cùng ngày.)*

`NGANHANG`, `CHUNGKHOAN`, `BAOHIEM` **không phải là ba ngành như 21 ngành còn lại** — chúng là ba **mẫu báo cáo tài chính** khác nhau. Ngân hàng, công ty chứng khoán và bảo hiểm mỗi loại có biểu mẫu BCTC riêng theo quy định, không so sánh chỉ tiêu với doanh nghiệp sản xuất được. Trộn một doanh nghiệp thường vào đó là làm hỏng mọi phép tính trên nhóm.

Kho đã có sẵn trường phân biệt: `market.issuer.com_type_code` ∈ `NH | CK | BH | CT | QU` — chính trường quyết định endpoint snapshot ở [step-02](../2026-08-25-postgres-data-schema/step-02-market-identity.md).

> **Luật hai chiều:** `com_type_code = NH` ⟺ ngành `NGANHANG`; `CK` ⟺ `CHUNGKHOAN`; `BH` ⟺ `BAOHIEM`. Không ngoại lệ.

**Đo 2026-08-27:** ba nhánh ICB lớn sạch tuyệt đối — `8355` Ngân hàng 28 mã · `8777` Môi giới chứng khoán 42 mã · bảo hiểm 13 mã, **không mã `CT` nào lẫn vào**. Nhưng ba nhánh nhỏ thì hỏng:

| Nhánh ICB | Thành viên | Vấn đề |
|---|---|---|
| `8771` Quản lý tài sản | `TIN` (NH) · `DCV` (CT) | Lớp 1 đưa cả hai về CHUNGKHOAN — sai cả hai |
| `8773` Tài chính cá nhân | `EVF` (NH) · `F88` (CT) | `F88` không dùng mẫu BCTC ngân hàng |
| `8775` Tài chính đặc biệt | `HVA` · `OGC` · `TVC` — **cả ba đều CT** | Không mã nào được vào ngành tài chính |

**Xử lý (chốt: xếp theo tài sản thật, không thêm ngành thứ 25):** `TIN` → `NGANHANG` · `OGC` `TVC` `DCV` `FID` `KPF` → `DANDUNG` · `F88` → `BANLE` · `HVA` → `CONGNGHE`.

⚠️ Cây 24 ngành **không có ô cho holding đầu tư phi ngân hàng**. Bảy mã trên nằm nhờ ở `DANDUNG`/`BANLE`/`CONGNGHE` là vùng xám đã biết, chấp nhận vì toàn mã nhỏ.

**Nghiệm thu bắt buộc:** test chạy trên `v_issuer_industry` sau mỗi lượt ETL, khẳng định **0 vi phạm** luật hai chiều trên. Không có test này thì lần sửa `industry_icb_map` sau sẽ lại lọt — chính lớp 1 vừa lọt 6 mã mà không ai biết cho tới khi đo.

## 3. Nội dung mapping — 56 dòng lớp 1, 161 dòng lớp 2

Đã dựng xong trong worksheet. Mục lục và cách đọc: [`worksheets/README.md`](../../worksheets/README.md).

**Lớp 1 = 39 dòng ICB cấp 3 (mặc định) + 16 dòng cấp 4 (ngoại lệ) + 1 dòng không nạp `8980`.** Đủ **40/40** nhánh cấp 3 của cây ICB — kể cả `0580`, `2710`, `8670` chưa có doanh nghiệp nào, vì thiếu chúng thì mã lá mới rơi vào đó sẽ leo lên cấp 2 (không có dòng) rồi rơi NULL. Trộn hai cấp là **cố ý**, đúng luật phân giải ở §2:

- Cấp 3 làm **nền** cho cả nhánh — nhờ đó một mã ICB lá **mới** chưa từng thấy vẫn leo lên được tổ tiên và có ngành, thay vì rơi NULL. Đây là lý do không dùng bảng cấp-4-thuần.
- Cấp 4 chỉ thêm ở **10 nhánh cấp 3 chứa từ hai ngành riêng trở lên**. Riêng `2350` và `1350` nếu để nguyên cấp 3 sẽ gán sai một nửa của **370 doanh nghiệp**.

**Lớp 2 = 161 dòng.** Dựng bằng cách hợp ba nguồn — lớp 1, suy đoán của Claude, và **danh sách 712 mã đã phân tay của hệ thống cũ** — rồi rà từng nhóm chủ đề với chủ dự án. Toàn bộ 295 quyết định, kèm lý do từng mã: [`layer2-review.md`](layer2-review.md).

🔴 **Luật lọc quan trọng nhất:** mã nào cả ba nguồn cùng một ngành thì **không vào lớp 2**. 485/712 mã của danh sách cũ trùng lớp 1 và bị loại ngay; thêm 104 mã nữa bị loại sau khi rà. Bê nguyên danh sách cũ vào lớp 2 sẽ **đóng băng 589 mã** — sửa `industry_icb_map` về sau không lan tới được.

Ba nhóm chiếm hơn một nửa, đều là chỗ ICB không tách được:

| Nhóm | Vì sao lớp 1 không với tới | Số dòng |
|---|---|---|
| **KHUCONGNGHIEP** | ICB không có nút nào tách khu công nghiệp khỏi BĐS dân dụng | 34 |
| **NONGNGHIEP** | `3573` gộp nuôi trồng với thủy sản; lớp 1 đã đảo sang THUYSAN (đa số 29/45) nên nông nghiệp bóc tay | 29 |
| **DANDUNG** | holding đa ngành + 5 mã bị luật BCTC đẩy ra khỏi ngành tài chính | 21 |

Còn lại: CAOSU 11 · XAYDUNG 10 · DAUKHI 9 · TIENICH 6 · các ngành khác ≤5 dòng.

## 4. Bốn ca ở [industry-tree §5](../../../20-design/industry-tree.md) — đối chiếu lại với ICB thật

| Ca | Kết quả đối chiếu |
|---|---|
| Gỗ nội thất TTF/ACG/SAV/GDT | **Lớp 1 tự giải.** ICB `1733` Lâm sản & chế biến gỗ → DETMAY; GDT ở `3726` → DETMAY. Không cần gán tay |
| VEF | **Lớp 1 tự giải.** ICB xếp VEF vào `8633` Bất động sản → DANDUNG, không phải DULICH |
| IPA | **Cần lớp 2.** ICB xếp `2791` Tư vấn → XAYDUNG; đè sang DANDUNG — luật BCTC §2b chặn đường vào CHUNGKHOAN |
| TRC/DRI | 🔴 **Tiền đề của §5 sai.** §5 giả định CAOSU gồm 5 mã (2 thiên nhiên, 3 săm lốp) nên lo hai nửa triệt tiêu nhau. Đo thật: **11 mã cao su thiên nhiên vs 4 mã săm lốp** — thiên nhiên là đa số áp đảo, chỉ số CAOSU sẽ bám giá cao su chứ không tự triệt tiêu. **Không dời sang NONGNGHIEP.** Riêng DPR, GVR, PHR sang KHUCONGNGHIEP vì nay ăn theo sóng chuyển đổi đất KCN |

## 5. Bốn nhánh mơ hồ — đã chốt hết 2026-08-27

| Nhánh | Chốt | Căn cứ |
|---|---|---|
| `7573` Phân phối xăng dầu & khí đốt (32 DN) | → **DAUKHI** | Biến động theo giá dầu/LPG thế giới, cùng sóng với BSR/PLX/PVS. Đặt vào TIENICH sẽ trộn hai nửa ngược chiều trong một rổ |
| `2799` Chất thải & Môi trường (29 DN) | → **TIENICH** | Cùng họ dịch vụ công ích địa phương với cấp nước: doanh thu theo hợp đồng nhà nước, không theo chu kỳ |

| Nhánh | Chốt | Căn cứ |
|---|---|---|
| `5557` Sách & ấn bản (25 DN) | → **YTE**, không tách ngành thứ 25 | Xem §6 |
| `3353` Ô tô (13 DN) | → **BANLE**, TMT đè sang THIETBI ở lớp 2 | 6/7 mã HOSE là đại lý (HAX, SVC, CTF, HHS, HTL, VVS); TMT là nhà sản xuất duy nhất. VEA không nằm ở đây — ICB xếp `2757` |

## 6. Có nên tách ngành "Truyền thông và Giải trí"? — không

Chủ dự án đặt câu hỏi có nên bẻ lại DULICH và YTE để đón nhóm xuất bản. Đo bằng tỷ lệ mã HOSE *(thước thanh khoản đo được ngay, chưa cần dữ liệu giá — 2026-08-27)*:

- `5557`: **24/25 mã nằm HNX+UPCOM**, chỉ PNC ở HOSE.
- Ngành TRUYENTHONG giả định (`5557`+`5555`+`5553`+`5755`+`3747`) = 40 DN, **15% HOSE** — sẽ kém thanh khoản nhất cây.
- DULICH sau khi bị rút phần giải trí: 39 DN, **21% HOSE** — cũng tệ đi, vì thanh khoản của DULICH nằm ở HVN/VJC/SCS chứ không ở giải trí.

Tách xong được hai ngành đều yếu hơn ngành gốc.

Còn nỗi lo "25 mã chết làm loãng YTE" thì **YTE 16% HOSE không phải ngoại lệ** — ngang XAYDUNG (17%), trên THIETBI (14%) và KHOANGSAN (11%); toàn thị trường 26%. Bỏ hẳn `5557` ra thì YTE chỉ nhích lên 21%.

🔴 **Kết luận: micro-cap là vấn đề trọng số chỉ số, không phải vấn đề phân ngành.** Ngành nào của cây cũng ~3/4 là UPCOM+HNX vì thị trường Việt Nam vốn thế. Chữa bằng cách bẻ cây là chữa sai bệnh — chỗ chữa đúng là công thức dòng tiền/breadth ở [architecture §3.2](../../../00-overview/architecture.md): **lọc theo thanh khoản trước khi đếm**, chứ không phải tách ngành cho tới khi mỗi ngành đều sạch.

## 7. Độ phủ sau khi áp cả hai lớp *(đo 2026-08-27)*

**1.525/1.525 cổ phiếu có issuer đều có ngành**, cả 24 ngành đều có mã:

```
XAYDUNG 198 · TIENICH 144 · DANDUNG 117 · VANTAI 109 · VATLIEU 90 · THUCPHAM 89
YTE 89 · DETMAY 72 · THIETBI 69 · NHUA 54 · DAUKHI 52 · DULICH 51 · KIMLOAI 44
CHUNGKHOAN 42 · KHOANGSAN 40 · CONGNGHE 39 · HOACHAT 37 · BANLE 37
KHUCONGNGHIEP 34 · THUYSAN 32 · NGANHANG 30 · NONGNGHIEP 29 · CAOSU 14 · BAOHIEM 13
```

Hai khoản ngoài tầm với, **là độ phủ thật của nguồn, không phải lỗi**:

- **24 chứng chỉ quỹ/ETF** (ICB `8980`) — không nạp, ETF và quỹ không có ngành *(luật bước 2)*.
- **437 cổ phiếu không có issuer** *(UPCOM 377 · HNX 39 · HOSE 21)* — xem §7b.

### 7b. 🔴 Luật: không có issuer thì không gán ngành

*(Đo và chốt 2026-08-27.)*

Câu **"437 cổ phiếu không có `icb_code`"** ở các bản trước là **sai**. Đo lại trên `all-securities.xlsx`:

| | Số mã |
|---|---|
| Cổ phiếu trong kho | 1.963 |
| Có issuer | 1.526 |
| **Không có issuer nào** | **437** |
| Có issuer nhưng thiếu `icb_code` | **0** |

Không mã nào có issuer mà thiếu ICB. Vấn đề thật là **danh bạ doanh nghiệp không phủ tới 437 mã**, đúng như [plan refdata](../2026-08-26-reference-data-etl/plan.md) đã lường (`stocks_no_issuer = 437`).

Ngành gán ở **doanh nghiệp**, mã thừa hưởng *(industry-tree §4)*. Lớp 1 ghi `issuer.industry_id`, lớp 2 ghi `issuer_industry_override.issuer_id` — **không có issuer thì không có hàng nào để gắn ngành vào, ở cả hai lớp.**

> **Luật:** cổ phiếu không có issuer ⇒ **không gán ngành, để trống**. Không phải lỗi, không cần cảnh báo.

Chủ dự án xác nhận nhóm này thực chất **đã huỷ niêm yết**. Danh sách phân tay cũ có 29 mã thuộc nhóm này (AMD, ATB, AVF, BCG, BCR, BII, DPS, DTE, DZM, FLC, GAB, HAI, HIG, HRT, HVG, IBC, KLF, KSH, LCS, LTG, NHP, RDP, ROS, SRT, SSN, TKG, TS4, VCW, VOC) — **không nạp**, giữ trong [sổ rà lớp 2](layer2-review.md) làm bản ghi.

### 7c. 🔴 Phát hiện kèm theo — `security.status` sai cho 437 dòng

*(Chủ dự án nêu giả thuyết "không issuer tức là đã huỷ niêm yết", đo 2026-08-27 để kiểm.)*

**Bảng chéo issuer × status, chỉ cổ phiếu:**

| | `listed` | `delisted` |
|---|---|---|
| Có issuer | 1.525 | 1 *(`EGL`)* |
| **Không issuer** | **437** | 0 |

Toàn kho 2.015 mã chỉ có **4 dòng `delisted`** (3 chứng chỉ quỹ + `EGL`). Nên `status` **không dùng để kiểm giả thuyết được** — nó gần như trống thông tin huỷ niêm yết.

**Kiểm bằng danh tính thay vì bằng cờ.** 21 mã HOSE trong nhóm không issuer:

`BBC` Bibica · `BHS` Đường Biên Hòa *(sáp nhập SBT)* · `CAV` Cadivi · `NKD` Kinh Đô miền Bắc · `TAC` Tường An *(sáp nhập KDC)* · `PME` Pymepharco · `PVF` PVFinance *(sáp nhập SHB)* · `GTN` GTNFoods · `VIS` Thép Việt Ý · `THI` Thiết bị điện · BCI, CEE, CVS, CXM, EMC, HT2, NHS, PHT, SEC, SVI, TIC

39 mã HNX gồm `HBB` **Habubank** — sáp nhập SHB từ **2012** — và `KLS` Chứng khoán Kim Long đã giải thể.

**Không mã nào còn giao dịch.** Giả thuyết đúng: **không có issuer ⟺ đã huỷ niêm yết**. Điều này *củng cố* luật §7b — 437 mã đó là mã chết, không phải mã thiếu dữ liệu.

🔴 **Luật còn thiếu ở ETL danh mục** (việc riêng, không thuộc spec này): job refdata chỉ đánh `delisted` cho ca *"có trong danh bạ mà vắng trong bảng giá"* — đúng 4 mã. Ca ngược lại — **có trong bảng giá BVSC mà vắng trong danh bạ FiinTrade** — không có luật nào bắt, nên 437 mã chết vẫn mang nhãn `listed`, kể cả Habubank đã biến mất 14 năm. **Vắng mặt trong danh bạ doanh nghiệp chính là tín hiệu huỷ niêm yết** — bảng giá giữ lại dòng cũ, danh bạ thì không. Ảnh hưởng mọi thống kê "mã đang niêm yết".

## 8. Việc phải làm khi thực thi

1. Migration đổi **6 code và 7 tên** ở `market.industry` *(industry-tree §2)* — **không sửa `0003` tại chỗ** vì nó đã chạy trên DB thật. Sửa kèm literal 24 code ở [`test_s02_identity.py:6`](../../../../backend/tests/schema/test_s02_identity.py) — test duy nhất chạm tới code ngành.
2. Migration thêm `market.issuer_industry_override` + view `market.v_issuer_industry`.
3. Migration seed nạp `industry_icb_map` (**56 dòng**) và `issuer_industry_override` (**161 dòng**) từ worksheet — cùng chỗ với `0003_seed_industry`, vì hai bảng này **không có đường ghi runtime**.
4. `refdata_store` gán `industry_id` theo luật phân giải ở §2, cả INSERT lẫn UPDATE. Mã ICB lạ ⇒ NULL + cảnh báo, **không chặn job**.
5. Viết lại test *tay thắng máy*: ghi override → chạy ETL hai lượt → override không đổi, `issuer.industry_id` được refresh theo map. Test cũ khoá đúng hành vi cũ nên sẽ đỏ — đó là dấu hiệu đúng, không phải hồi quy.
6. Đồng bộ tài liệu sống: [industry-tree §4-5](../../../20-design/industry-tree.md), [architecture §3.2](../../../00-overview/architecture.md), [roadmap](../../../00-overview/roadmap.md), [database/README](../../../../database/README.md).

## 9. Nghiệm thu

- [ ] Chạy `etl refdata` **dưới role `dlck_etl`** *(CLAUDE.md §3.5 — mọi đường production đi qua, đọc lẫn ghi)*, hai lượt: kết quả y hệt, `updated_at` không đổi lượt hai.
- [ ] Đếm trên DB thật: `v_issuer_industry` cho **1.525 dòng có ngành**, phân bố khớp §7 từng ngành.
- [ ] Đè tay một issuer bất kỳ → chạy job → giá trị đè **không đổi**, `source` = `manual`.
- [ ] Đổi một dòng `industry_icb_map` → chạy job → doanh nghiệp thuộc nhánh đó **đổi theo**, doanh nghiệp có override **không đổi**.
- [ ] Thêm một issuer giả mang `icb_code` lá chưa có trong map → leo path → nhận ngành của tổ tiên gần nhất.

## 10. Việc còn lại sau spec này

| Mục | Nội dung |
|---|---|
| **Nguồn issuer cho 437 mã** | Xem §7b–7c. Đây là mã đã huỷ niêm yết nên **không cần ngành** — nhưng `security.status` đang sai, thuộc ETL danh mục |
| **Trọng số chỉ số ngành** | §6 kết luận micro-cap phải chặn ở tầng tính chỉ số, không phải ở cây ngành. Ngưỡng thanh khoản là việc riêng |
| **8 mã độ tin cậy thấp** | `ANI` `KSD` `SGI` `HTT` `LPT` `SDA` `VHG` `STH` — tra web không ra ngành nghề, xếp theo ICB hoặc theo danh sách cũ. Đã đánh dấu trong [sổ rà](layer2-review.md) |
| **`PVT`** | Đội tàu chở dầu lớn nhất VN, xếp `DAUKHI` theo luật "tên có dầu khí" nhưng doanh thu chạy theo giá cước thuê tàu. Mã đầu tiên nên xem lại nếu chỉ số DAUKHI nhiễu |
