# Cập nhật tài liệu nguồn 2026-08-15 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development để thực thi từng task. Các bước dùng cú pháp checkbox (`- [ ]`).

**Goal:** Đưa `docs/` về đúng trạng thái đã đo trong đợt khảo sát nguồn 2026-08-15 — sửa 2 khẳng định sai, bổ sung phái sinh + ETF, lập tài liệu 6 nguồn mới, đồng bộ tầng tổng quan.

**Architecture:** Chia task theo **quyền sở hữu file** — mỗi task sở hữu trọn một nhóm file, không task nào sửa file của task khác. Mọi thay đổi liên quan README gom vào task cuối. Nhờ vậy các task chạy được độc lập và reviewer chấm được từng task riêng.

**Tech Stack:** Markdown thuần. Không code. Kiểm bằng `grep`/`bash`.

**Spec:** [`spec.md`](spec.md)

## Global Constraints

Mọi task đều phải tuân, không ngoại lệ:

1. **Luật vàng:** tài liệu sống phải tường minh, **không trỏ về `00-overview/decisions/`**. Phép thử: xoá `decisions/` chỉ được mất lịch sử, không mất tri thức vận hành.
2. **Mọi con số phải kèm ngày đo** — dạng *(đo 2026-08-15)*. Không có số đo thì ghi **"chưa kiểm"**, tuyệt đối không đoán.
3. **Nguồn số duy nhất:** thư mục [`docs/superpowers/surveys/2026-08-15-nguon-du-lieu/`](../../surveys/2026-08-15-nguon-du-lieu/README.md). **Cấm tự gọi API để đo lại.**
4. **Tên file/thư mục tiếng Anh, nội dung tiếng Việt** (ADR 0005).
5. **Giọng tài liệu:** bảng nhiều, câu ngắn, bẫy đánh dấu 🔴 (nghiêm trọng) / ⚠️ (cần biết). **Đọc `docs/10-sources/market/00-conventions.md` trước khi viết bất cứ gì** để bắt giọng.
6. **Không sửa** `20-design/market-field-selection.md` (sinh tự động), `30-skills/`, `docs/superpowers/surveys/`.
7. **Commit mỗi task một lần**, tiếng Việt, kết thúc bằng `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.

### Lệnh kiểm dùng chung (chạy cuối mỗi task)

```bash
cd "D:/twan-projects/finext-v2"
# Liên kết nội bộ chết
grep -roh "](\.\?\.\?/\?[a-zA-Z0-9_./-]*\.md" docs --include=*.md | sed 's/](//' | sort -u | while read p; do
  find docs -name "$(basename "$p")" | grep -q . || echo "LIEN KET CHET: $p"
done
# Khẳng định sai còn sót
grep -rn "không cung cấp dữ liệu phái sinh" docs/ && echo "CON KHANG DINH SAI" || echo "OK: da xoa khang dinh sai"
```

---

## Bản đồ file — ai sở hữu cái gì

| Task | File sở hữu | Loại |
|---|---|---|
| 1 | `docs/10-sources/market/01-bvsc-rest.md` | Sửa |
| 2 | `docs/10-sources/market/00-conventions.md` | Sửa |
| 3 | `docs/10-sources/market/02-bvsc-tvcharts.md` · `09-fiin-market-price.md` | Sửa |
| 4 | `docs/10-sources/macro/wichart.md` | Sửa |
| 5 | `docs/10-sources/macro/sbv-omo.md` | **Tạo** |
| 6 | `docs/10-sources/global/fred.md` · `global/fx.md` | **Tạo** |
| 7 | `docs/10-sources/global/yahoo.md` | **Tạo** |
| 8 | `docs/10-sources/global/commodities.md` · `global/crypto.md` | **Tạo** |
| 9 | `docs/00-overview/decisions/0006-source-selection-2026-08-15.md` | **Tạo** |
| 10 | `docs/README.md` · `10-sources/README.md` · `00-overview/architecture.md` · `00-overview/roadmap.md` · `README.md` gốc | Sửa |

---

## Task 1: Sửa khẳng định sai + bổ sung phái sinh và ETF vào `01-bvsc-rest.md`

**Files:** Modify `docs/10-sources/market/01-bvsc-rest.md`
**Đọc trước:** `docs/superpowers/surveys/2026-08-15-nguon-du-lieu/report-bvsc-derivative.md` và `report-du-lieu-quy-vn.md`

**Produces:** Mục phái sinh và mục ETF trong endpoint `/datafeed/instruments` — task 10 sẽ trỏ link tới.

- [ ] **Bước 1: Xoá khẳng định sai ở dòng 72**

Câu hiện tại: `- Không chứa phái sinh. BVSC không cung cấp dữ liệu phái sinh qua bất kỳ endpoint public nào.`

Thay bằng nội dung nói đúng phạm vi của `/quotes` **và** ghi lại bài học phương pháp:

```markdown
- **`/quotes` không chứa phái sinh** — kiểm 2026-08-15: `/quotes?symbols=41I1G8000` trả `{"s":"ok","d":[]}`.
  ⚠️ **Đừng suy từ đây ra "BVSC không có phái sinh"** — bản trước của tài liệu này đã mắc đúng lỗi đó.
  Phái sinh nằm ở [`/datafeed/instruments`](#datafeed-instruments-phai-sinh), 14 hợp đồng, 62 trường, có `openInterest`.
```

- [ ] **Bước 2: Sửa bảng "Endpoint đã loại khỏi phạm vi"**

Dòng `/priceservice/derivative/snapshot` · `/transactions` → `404` giữ nguyên kết quả, nhưng thêm cột ghi chú: đường dẫn thật trong mã nguồn là `/priceservice/derivative/snapshot/q=` và **cũng 404** — nhóm `/priceservice/` đã chết, dữ liệu phái sinh đi đường `/datafeed/instruments`.

- [ ] **Bước 3: Thêm mục phái sinh vào endpoint `/datafeed/instruments`**

Phải có, lấy số từ `report-bvsc-derivative.md`: bảng 14 hợp đồng (mã · sản phẩm · cơ sở · GD đầu/cuối · đáo hạn · OI · KL) · trường chỉ phái sinh mới có · trường luôn rỗng · **🔴 bẫy OI trễ một phiên kèm bảng kiểm 4/4** · 4 bẫy kiểu dữ liệu · phiên mở **08:45**.

- [ ] **Bước 4: Thêm mục ETF/quỹ**

31 mã `StockType=3` · `FundType` (`E`=ETF, `M`=khác) · `ListedShare`/`TotalListingQtty` · room ngoại · **không có NAV ở BVSC** (NAV ở FiinTrade, task 3 viết).

- [ ] **Bước 5: Kiểm và commit**

```bash
cd "D:/twan-projects/finext-v2"
grep -c "không cung cấp dữ liệu phái sinh" docs/10-sources/market/01-bvsc-rest.md   # ky vong: 0
grep -c "08:45" docs/10-sources/market/01-bvsc-rest.md                              # ky vong: >=1
grep -c "41I1G8000" docs/10-sources/market/01-bvsc-rest.md                          # ky vong: >=1
git add docs/10-sources/market/01-bvsc-rest.md
git commit -m "Sửa khẳng định sai về phái sinh, bổ sung phái sinh và ETF vào 01-bvsc-rest"
```

---

## Task 2: Bẫy chung vào `00-conventions.md`

**Files:** Modify `docs/10-sources/market/00-conventions.md`
**Đọc trước:** `report-bvsc-derivative.md` §5 §7 · `report-vang-dau-doi-chieu-investing.md` §2 §4 · `ra-soat-nguon-cu.md` §2

**Consumes:** không. **Produces:** mục bẫy chung — task 4 và 10 trỏ tới.

- [ ] **Bước 1: Thêm bẫy "Múi giờ WiChart"**

Epoch WiChart là **nửa đêm giờ Việt Nam**: `1786726800000` = 2026-08-14 17:00 UTC = 2026-08-15 00:00 giờ VN. Parse UTC làm **lệch cả chuỗi một ngày**. Ghi rõ đây là lỗi đã thật sự xảy ra trong đợt đo 2026-08-15 và tạo ra một kết luận sai hoàn toàn.

- [ ] **Bước 2: Thêm bẫy "`StockType` không nhất quán giữa hai endpoint"**

Cùng mã trái phiếu `HDC425001`: `/quotes` báo `StockType=12`, `/datafeed/instruments` báo `StockType=1` *(đo 2026-08-15)*. **Không dùng `StockType` làm khoá phân loại chung.**

- [ ] **Bước 3: Thêm bẫy "Hai endpoint BVSC lệch độ phủ"**

`/quotes?symbols=ALL` 2.534 bản ghi vs `/datafeed/instruments` 2.001 *(đo 2026-08-15)*. `VFMVF1` có ở endpoint đầu, không có ở endpoint sau. **Không endpoint nào là danh mục chuẩn duy nhất** — ETL phải hợp nhất.

- [ ] **Bước 4: Thêm bẫy "Giá giao ngay không bằng giá tương lai"**

Chênh ~2% giữa FRED `DCOILWTICO` và WiChart/Yahoo **là chênh lệch cơ sở, không phải sai số**. Xác nhận bằng cấu trúc kỳ hạn WTI *(đo 2026-08-15)*: Sep 82,40 · Oct 81,47 · Nov 80,10 · Dec 78,49 — giảm đơn điệu ⇒ backwardation, dốc ≈ −1,6%/tháng.

- [ ] **Bước 5: Kiểm và commit**

```bash
cd "D:/twan-projects/finext-v2"
for k in "nửa đêm giờ Việt Nam" "StockType" "2.534" "backwardation"; do
  grep -qi "$k" docs/10-sources/market/00-conventions.md && echo "OK: $k" || echo "THIEU: $k"
done
git add docs/10-sources/market/00-conventions.md
git commit -m "Thêm 4 bẫy chung phát hiện trong đợt khảo sát 2026-08-15"
```

---

## Task 3: Phái sinh và ETF vào `02-bvsc-tvcharts.md` + `09-fiin-market-price.md`

**Files:** Modify `docs/10-sources/market/02-bvsc-tvcharts.md` · `docs/10-sources/market/09-fiin-market-price.md`
**Đọc trước:** `report-bvsc-derivative.md` §3.4 §6 · `report-du-lieu-quy-vn.md` §2 · `viec-con-treo.md` §2

**Consumes:** Task 1 đã mô tả 14 hợp đồng ở `01-bvsc-rest.md` — **trỏ link sang đó, đừng chép lại bảng**.

- [ ] **Bước 1: `02-bvsc-tvcharts.md` — mục UDF cho phái sinh**

`/symbols?symbol=41I1G8000` trả `session: "0845-1500"` · `has_intraday: true` · `pricescale: 10` · `timezone: Asia/Bangkok`.
🔴 **Giới hạn:** `/config` khai `supports_search: true` **nhưng `/search` trả 404**; `/history` **chỉ chạy `resolution=1` và `D`**, còn `5`/`15`/`60`/`W` trả **HTTP 200 với body rỗng 0 byte**. Muốn 5/15/30/60 phút phải tự gộp từ nến 1 phút. Parser **bắt buộc kiểm độ dài body trước khi parse JSON**.
Hợp đồng đã đáo hạn **vẫn tra được**; trần ~239 nến vẫn áp dụng.

- [ ] **Bước 2: `09-fiin-market-price.md` — `getPriceData` nhận mã phái sinh**

`Code=VN30F1M` (và `2M`/`1Q`/`2Q`) → **2.233 phiên từ 31/08/2017**, 99 trường, có `openInterest`. `VN100F1M`/`GB05F1M`/`GB10F1M` → `status:"Failed"`, `"Code not valid"`.
⚠️ `percentValueChange` trả **phân số làm tròn 2 chữ số** (−0.01 cho −1,17%) — mất độ chính xác, tự tính từ `valueChange/referenceValue`.
🔴 **FiinTrade là nguồn chuẩn cho `openInterest`** vì BVSC trễ một phiên — trỏ link sang `01-bvsc-rest.md`.

- [ ] **Bước 3: `09-fiin-market-price.md` — `iNav` và `iIndex` cho ETF**

Cùng endpoint, truyền mã ETF thì có thêm `iNav` (NAV nội suy) và `iIndex`.
🔴 **Độ phủ chỉ 6/31 mã** *(đo 2026-08-15)* — 25 mã trả `Code not valid`. Bảng 6 mã kèm số phiên, chênh giá–NAV, KL khớp.
🔴 **Chỉ 2 mã có thanh khoản thật** (`E1VFVN30` 429.417 · `FUEVFVND` 152.251). Bốn mã còn lại KL 2.683–37.352 ⇒ **chênh lệch giá–NAV của quỹ mỏng là nhiễu, không phải tín hiệu**.
⚠️ Nhắc lại bẫy `PageSize` chỉ nhận `30`/`60` — đợt đo đã mắc lại chính bẫy này.

- [ ] **Bước 4: Kiểm và commit**

```bash
cd "D:/twan-projects/finext-v2"
grep -c "0845-1500" docs/10-sources/market/02-bvsc-tvcharts.md   # >=1
grep -c "body rỗng" docs/10-sources/market/02-bvsc-tvcharts.md   # >=1
grep -c "VN30F1M" docs/10-sources/market/09-fiin-market-price.md # >=1
grep -c "iNav" docs/10-sources/market/09-fiin-market-price.md    # >=1
git add docs/10-sources/market/02-bvsc-tvcharts.md docs/10-sources/market/09-fiin-market-price.md
git commit -m "Bổ sung phái sinh vào UDF và getPriceData, thêm iNav cho ETF"
```

---

## Task 4: Sửa `wichart.md` — múi giờ và cờ giá dầu

**Files:** Modify `docs/10-sources/macro/wichart.md`
**Đọc trước:** `report-vang-dau-doi-chieu-investing.md` **toàn bộ** · `report-wichart-oil-deviation.md` *(hồ sơ sai lầm — đọc phần đóng khung đầu file)*

**Consumes:** Task 2 đã ghi bẫy múi giờ ở `00-conventions.md` — ở đây ghi **cụ thể cho WiChart** và trỏ link sang.

- [ ] **Bước 1: Thêm mục múi giờ vào phần quy ước**

Epoch của mọi series WiChart là **nửa đêm giờ Việt Nam**. Ghi ví dụ cụ thể và câu lệnh parse đúng.

- [ ] **Bước 2: Sửa cờ `dau_wti` ở dòng 357**

Cờ hiện tại *"lệch 1,3%"* thay bằng nội dung đo được:
- So với **giá tương lai WTI** (chuẩn Investing, 10 ngày): lệch **0,50%** — bám sát
- So với FRED `DCOILWTICO` (**giao ngay**, 115 ngày): lệch **2,85%**
- **Nguyên nhân: `dau_wti` là giá TƯƠNG LAI, không phải giao ngay** dù nhãn ghi "Giá dầu WTI"
- ⚠️ Ai đọc nó như giá giao ngay sẽ lệch ~2% một cách hệ thống

- [ ] **Bước 3: Ghi bài học về cách sinh cờ lệch**

Cờ cũ sai vì **chấm một điểm** thay vì so chuỗi, và vì **so nhầm chuẩn**. Ghi rõ các cờ `lệch x%` khác trong file **sinh theo cách nào thì chưa rà** — cờ `vang_the_gioi` đã được kiểm trên 712 ngày và **đúng**, nên **không được suy đoán đồng loạt là cả bộ cờ sai**.

- [ ] **Bước 4: Ghi `vang_the_gioi` khớp Investing**

Đo 10 ngày: khớp **0,00%** với Investing XAU/USD — nhiều khả năng cùng nguồn giá *(suy luận, chưa xác nhận nguồn gốc)*. ⚠️ **36,8% điểm cuối tuần trùng khít điểm liền trước** — WiChart giữ nguyên giá cuối tuần.

- [ ] **Bước 5: Kiểm và commit**

```bash
cd "D:/twan-projects/finext-v2"
grep -c "lệch 1,3%" docs/10-sources/macro/wichart.md    # ky vong: 1 (chi con ure_trung_dong)
grep -qi "tương lai" docs/10-sources/macro/wichart.md && echo OK
grep -qi "Asia/Ho_Chi_Minh\|giờ Việt Nam" docs/10-sources/macro/wichart.md && echo OK
git add docs/10-sources/macro/wichart.md
git commit -m "Sửa cờ dau_wti và thêm bẫy múi giờ cho WiChart"
```

---

## Task 5: Tạo `macro/sbv-omo.md`

**Files:** Create `docs/10-sources/macro/sbv-omo.md`
**Đọc trước:** `report-omo-sources.md` §1 §3.3 §5b §6 · `report-omo-gap.md`

**Produces:** file nguồn OMO — task 10 trỏ link.

- [ ] **Bước 1: Viết file theo khuôn `market/`**

Bố cục: Tóm tắt · Vì sao cần OMO *(skill xếp OMO đứng đầu 5 nhân tố thanh khoản hằng ngày)* · Endpoint và cách gọi · Lược đồ bảng · **Bốn giới hạn** · Trường cần mà nguồn không có · Cách dựng bơm ròng · Giới hạn kết luận.

- [ ] **Bước 2: Ghi đủ bốn giới hạn**

1. 🔴 **Chỉ phiên mới nhất, không kho lưu** — không backfill được, **mỗi ngày không crawl là mất vĩnh viễn**
2. 🔴 **Thiếu cột đáo hạn và bơm ròng** — chỉ có 4 cột; phải tự dựng lịch đáo hạn từ kỳ hạn, cần ~140 ngày tích luỹ
3. ⚠️ **HTML viết tay**, class tự chế, `<style>` nội tuyến, số định dạng Việt (`6.307,47`), **ngày nằm trong tiêu đề bài** `(dd.mm.yy)`
4. ⚠️ **WAF chặn theo vân tay client** — `python-requests` UA mặc định nhận body 246 byte "Request Rejected"; PowerShell mặc định **qua được**; gửi đủ header trình duyệt thì chắc chắn qua

- [ ] **Bước 3: Ghi dữ liệu mẫu thật**

Bảng phiên 14/08/2026: 4 dòng "Mua kỳ hạn" (7/35/63/91 ngày), tổng **10.894,10 tỷ**, lãi suất **4,5%** phẳng đều. Ghi rõ **phiên đó không có nhóm "Bán hẳn"** ⇒ không phát hành tín phiếu.

- [ ] **Bước 4: Ghi ba lưu ý vận hành**

Gửi đủ header trình duyệt · lấy ngày từ **tiêu đề bài** không lấy ngày hệ thống · **lưu cả HTML gốc** để parse lại khi markup đổi.

- [ ] **Bước 5: Commit**

```bash
cd "D:/twan-projects/finext-v2"
test -f docs/10-sources/macro/sbv-omo.md && echo OK
grep -qi "không backfill\|mất vĩnh viễn" docs/10-sources/macro/sbv-omo.md && echo OK
git add docs/10-sources/macro/sbv-omo.md
git commit -m "Lập tài liệu nguồn OMO từ SBV"
```

---

## Task 6: Tạo `global/fred.md` và `global/fx.md`

**Files:** Create `docs/10-sources/global/fred.md` · `docs/10-sources/global/fx.md`
**Đọc trước:** `report-fred.md` **toàn bộ** · `report-more-sources.md` §1

- [ ] **Bước 1: `fred.md`**

Bảng **15 series** kèm tần suất, lịch sử, trễ, đơn vị, mắt xích trong phương pháp phân tích.
Bảy bẫy: `"."` là giá trị thiếu (4,3% dòng DGS10) · `file_type` mặc định **XML** · `count` là tổng chuỗi không phải số dòng trả về · `frequency=m` gộp phía server làm kỳ dở dang trả `"."` · `realtime_start` không phải hôm nay · `last_updated` đổi offset theo DST · khoá API nằm trong URL.
🔴 **Vá hồi tố:** PAYEMS tháng 5/2026 có **3 giá trị** (159.001 → 158.927 → 158.861). Kho phải **UPSERT**, làm mới cửa sổ 24 tháng.
🔴 **Chỉ số đô trễ 3–9 ngày** vì bản H.10 ra mỗi thứ Hai — ghi rõ đây là hạn chế thật.
**Giấy phép: chủ dự án đã làm việc với FRED và được đồng ý (2026-08-15).** Một dòng, không phân tích thêm.

- [ ] **Bước 2: `fx.md`**

Frankfurter (ECB): 1 lời gọi đủ 6 cặp, không khoá, lịch sử từ 1999-01-04.
**Công thức DXY** đầy đủ + kết quả nghiệm thu: dựng lại 2026-08-14 = **99,6113** vs DXY ICE **99,67** → lệch **−0,059%**; kiểm 248 phiên: |lệch| TB **0,180%**.
Năm bẫy: fixing **14:15 CET ≠ giá đóng cửa** *(nguồn gốc của toàn bộ sai lệch)* · lịch nghỉ hai bên không trùng · v2 **mặc định trộn 84 NHTW, bắt buộc `providers=ECB`** · nới ngày bắt đầu ra trước · **DXY dựng lại không hiển thị được cạnh giá đóng cửa thật**.
Ghi **Yahoo là nguồn dự phòng** *(chi tiết ở `yahoo.md`, task 7 — chỉ trỏ link)*.

- [ ] **Bước 3: Commit**

```bash
cd "D:/twan-projects/finext-v2"
test -f docs/10-sources/global/fred.md && test -f docs/10-sources/global/fx.md && echo OK
grep -qi "UPSERT\|vá hồi tố" docs/10-sources/global/fred.md && echo OK
grep -q "50.14348112" docs/10-sources/global/fx.md && echo OK
git add docs/10-sources/global/
git commit -m "Lập tài liệu nguồn FRED và tỷ giá Frankfurter"
```

---

## Task 7: Tạo `global/yahoo.md`

**Files:** Create `docs/10-sources/global/yahoo.md`
**Đọc trước:** `report-yfinance.md` **toàn bộ**

- [ ] **Bước 1: Bảng phủ 36 chỉ số/21 nước**

Tách hai bảng châu Á (16) và Âu–Mỹ (20), mỗi mã kèm lịch sử từ năm nào. Ghi `^KOSPI` **không tồn tại** (dùng `^KS11`) và `^DJI` chỉ từ 1992.

- [ ] **Bước 2: Ba bẫy cấu trúc — mục 🔴 riêng**

1. `period1=0` **cắt câm lịch sử ở 1970** — `^GSPC` 14.276 nến vs **24.772** nến khi dùng `period1` âm. **Luật: luôn dùng `period1` âm.**
2. `range=max&interval=1d` **trả nến THÁNG** (`dataGranularity='1mo'`, 173 nến vs 3.730). **Luật: không dùng `range=`, luôn kiểm `meta.dataGranularity`.**
3. `404` **không có nghĩa mã không tồn tại** — `0P0000HY8X.VN` trả 404 với `range=5d` nhưng 200 với `period1`/`period2`.

- [ ] **Bước 3: Chết im lặng và cách nhận biết**

Bảng 5 mã chết (`^BCOM` 2.269 ngày…) vẫn trả `200` + giá hợp lệ. **Hai quy tắc nhận biết nghiệm đúng 5/5:** `quoteType == "ALTSYMBOL"`; và luôn so `regularMarketTime` với lịch phiên.

- [ ] **Bước 4: Các khối lấy được**

Lợi suất Mỹ (`^TNX` lệch FRED **0,009 điểm %**, **tươi hơn 1 ngày**) · biến động (`^MOVE` `^VXN` `^OVX` `^GVZ` `^SKEW`) · `^SPGSCI` · `^SOX` · ETF quốc gia · `VNM` (VanEck Vietnam ETF) · **tỷ giá làm dự phòng** (22/23 cặp, có `VND=X`, đồng bộ bằng nến đóng 23:00 UTC) · quỹ VN niêm yết nước ngoài (`VOF.L` **5.799 phiên từ 2003**).

- [ ] **Bước 5: Ghi rõ ranh giới**

`VND=X` là **tỷ giá thị trường**, cao hơn tỷ giá trung tâm +2,29% ⇒ **không thay được `dhtg` của WiChart**. Mã `.VN` chỉ phủ **HOSE 399/399, HNX 0%, UPCOM 2,5%** ⇒ chỉ dùng **kiểm chứng chéo**. BCTC thua FiinTrade ~90 lần.
🔴 **Gọi thẳng REST, không dùng thư viện `yfinance`** — thư viện tốn 2 request/mã và chạy song song phá nhịp nghỉ. `v7/quote` theo lô 180 mã lấy 399 mã HOSE chỉ tốn **3 request**.

- [ ] **Bước 6: Commit**

```bash
cd "D:/twan-projects/finext-v2"
for k in "period1" "dataGranularity" "ALTSYMBOL" "DX-Y.NYB"; do
  grep -q "$k" docs/10-sources/global/yahoo.md && echo "OK: $k" || echo "THIEU: $k"
done
git add docs/10-sources/global/yahoo.md
git commit -m "Lập tài liệu nguồn Yahoo Finance cho chỉ số quốc tế"
```

---

## Task 8: Tạo `global/commodities.md` và `global/crypto.md`

**Files:** Create `docs/10-sources/global/commodities.md` · `docs/10-sources/global/crypto.md`
**Đọc trước:** `report-more-sources.md` §2.5 · `report-binance.md` §1 §2 · `report-vang-dau-doi-chieu-investing.md` §3

- [ ] **Bước 1: `commodities.md` — LBMA**

`prices.lbma.org.uk/json/gold_pm.json` và `silver.json`: **14.662 / 14.806 điểm từ 1968**, một lời gọi lấy hết (913 KB), không khoá, trễ 0 ngày làm việc.
⚠️ Là **fixing 15:00 London**, không phải giá đóng cửa — lệch 0,56% so với XAU/USD giao ngay là **đặc tính, không phải sai số**.
Ghi rõ vai: **mốc chuẩn và backfill lịch sử dài**, không thay WiChart *(WiChart khớp Investing 0,00%)*.

- [ ] **Bước 2: `crypto.md` — Binance**

**PAXG** làm nguồn vàng 24/7: lệch WiChart **0,369%** trên 712 ngày, premium so LBMA **−0,049%**, lịch sử 6 năm. Lý do lấy: **chạy thật cuối tuần** trong khi WiChart đứng yên 36,8% ngày cuối tuần.
**10 đồng crypto** cho hiển thị và vẽ biểu đồ, kèm bảng niêm yết từ năm nào *(BTC/ETH 9 năm … SOL/AVAX 6 năm)*. Ghi rõ **chọn theo độ nhận biết, không theo khối lượng** — top khối lượng đầy stablecoin và token lạ.
Bốn bẫy: giá theo **USDT không phải USD** (chênh neo <0,15%) · `/klines` **mảng theo vị trí**, số **dạng chuỗi** · nến định danh bằng **thời điểm mở**, epoch **ms UTC**, phải đặt `timeZone` rõ · nhịp tin PAXG **mỏng** (0,25 lệnh/giây).
Hạn mức: `REQUEST_WEIGHT` 6.000/phút, có header `x-mbx-used-weight`.

- [ ] **Bước 3: Commit**

```bash
cd "D:/twan-projects/finext-v2"
test -f docs/10-sources/global/commodities.md && test -f docs/10-sources/global/crypto.md && echo OK
grep -q "1968" docs/10-sources/global/commodities.md && echo OK
grep -qi "USDT" docs/10-sources/global/crypto.md && echo OK
git add docs/10-sources/global/
git commit -m "Lập tài liệu nguồn LBMA và Binance"
```

---

## Task 9: ADR 0006 — quyết định chọn nguồn

**Files:** Create `docs/00-overview/decisions/0006-source-selection-2026-08-15.md`
**Đọc trước:** `docs/00-overview/decisions/0005-english-tree.md` *(bắt khuôn)* · `ra-soat-nguon-cu.md` · `ops-ledger.md`

⚠️ **Ràng buộc quan trọng nhất của task này:** ADR **chỉ ghi quyết định và lý do**. Mọi tri thức vận hành *(endpoint, bẫy, lược đồ, con số)* phải nằm ở tầng sống. Phép thử: **xoá file này đi thì không tài liệu sống nào mất tri thức.**

- [ ] **Bước 1: Viết ADR theo khuôn 0005**

Bối cảnh · Quyết định · Lý do · Hệ quả. Các quyết định phải ghi:
1. Chốt **SBV** cho OMO, Vietstock làm dự phòng — lý do: đăng nhập khó
2. **Giữ WiChart** cho dầu, **lưu cả giao ngay lẫn tương lai** — lý do: chênh 2% là backwardation, hai nguồn đo hai thứ khác nhau
3. **Frankfurter chính, Yahoo dự phòng** cho tỷ giá — lý do: Frankfurter mã nguồn mở tự dựng lại được
4. **Yahoo chính cho chỉ số quốc tế** thay FiinTrade — lý do: 36 mã vs 3 mã, sâu hơn nhiều
5. **Bỏ thư viện `yfinance`**, gọi thẳng REST — lý do: 2 request/mã và chạy song song phá nhịp
6. **akshare chỉ dùng backfill một lần** — lý do: vĩ mô Mỹ chết ~1 năm mà vẫn trả HTTP 200
7. **Loại có chủ đích 4 khối:** chứng quyền · lô lẻ · trái phiếu · realtime FiinTrade
8. Thêm thư mục **`global/`** cho nguồn quốc tế

- [ ] **Bước 2: Kiểm luật vàng**

```bash
cd "D:/twan-projects/finext-v2"
# Khong tai lieu song nao duoc tro ve decisions/
grep -rn "decisions/" docs/10-sources/ docs/20-design/ docs/README.md 2>/dev/null && echo "VI PHAM LUAT VANG" || echo "OK: khong tai lieu song nao tro ve ADR"
git add docs/00-overview/decisions/0006-source-selection-2026-08-15.md
git commit -m "ADR 0006: chốt nguồn dữ liệu sau khảo sát 2026-08-15"
```

---

## Task 10: Đồng bộ tầng tổng quan

**Files:** Modify `docs/README.md` · `docs/10-sources/README.md` · `docs/00-overview/architecture.md` · `docs/00-overview/roadmap.md` · `README.md` (gốc)
**Đọc trước:** `ra-soat-nguon-cu.md` §1 §2 §3 · `viec-con-treo.md` · tất cả file mới do task 5–8 tạo

**Consumes:** mọi file do task 1–9 tạo. **Task này chạy CUỐI CÙNG.**

- [ ] **Bước 1: `10-sources/README.md` — mục 2 "Phạm vi"**

Viết lại **"Ngoài phạm vi" thành ba loại có lý do** *(spec §6.6)*: loại có chủ đích · đã có đường khác · đã kiểm không nguồn nào có. Cập nhật "Trong phạm vi" thêm phái sinh, ETF/quỹ, chỉ số quốc tế, crypto, OMO.

- [ ] **Bước 2: `10-sources/README.md` — mục 3 "Cấu trúc tài liệu"**

Thêm **§3.3 `global/`** với bảng 4 file mới; đổi số các mục sau cho đúng; thêm `sbv-omo.md` vào mục `macro/`.

- [ ] **Bước 3: `10-sources/README.md` — changelog bản 5.0**

Một dòng cho đợt khảo sát 2026-08-15: 9 nguồn, ~400 lời gọi, 6 nguồn mới, 2 khẳng định sai đã sửa. Trỏ link tới thư mục khảo sát.

- [ ] **Bước 4: `docs/README.md`**

Thêm `global/` vào bảng bản đồ tài liệu và vào phần "Toàn bộ tài liệu".

- [ ] **Bước 5: `00-overview/architecture.md`**

Cập nhật tầng **L0 Nguồn ngoài**: thêm SBV · FRED · Frankfurter · Yahoo · LBMA · Binance.

- [ ] **Bước 6: `00-overview/roadmap.md`**

Thêm vào §5 các việc treo ảnh hưởng thiết kế, nổi bật: 🔴 **realtime phái sinh chưa đo được — phải đo trong phiên, khung 08:45–15:00**, kèm quy trình đo *(nối socket, đăng ký cả 20 topic với `41I1G8000`, ghi frame 5 phút)*.

- [ ] **Bước 7: `README.md` gốc**

Cập nhật bảng trạng thái: số nguồn, khối dữ liệu đã phủ.

- [ ] **Bước 8: Kiểm toàn bộ và commit**

```bash
cd "D:/twan-projects/finext-v2"
# 1. Lien ket chet
grep -roh "](\.\?\.\?/\?[a-zA-Z0-9_./-]*\.md" docs --include=*.md | sed 's/](//' | sort -u | while read p; do
  find docs -name "$(basename "$p")" | grep -q . || echo "LIEN KET CHET: $p"
done
# 2. Khang dinh sai
grep -rn "không cung cấp dữ liệu phái sinh" docs/ && echo "CON SOT" || echo "OK"
# 3. Sau file nguon moi ton tai va duoc lien ket
for f in sbv-omo fred fx yahoo commodities crypto; do
  find docs/10-sources -name "$f.md" | grep -q . || echo "THIEU FILE: $f.md"
  grep -rq "$f.md" docs/10-sources/README.md || echo "CHUA LIEN KET: $f.md"
done
git add -A docs README.md
git commit -m "Đồng bộ tầng tổng quan theo khảo sát nguồn 2026-08-15"
```

---

## Self-review của người viết plan

**Phủ spec:** §6.1→T1+T4 · §6.2→T1+T3 · §6.3→T1+T3 · §6.4→T5,T6,T7,T8 · §6.5→T2 · §6.6→T10 · §6.7→T10 · §6.8→T9 · §6.9→T10. **Không mục nào của spec thiếu task.**

**Xung đột file:** không task nào (1–9) sửa file của task khác. T10 sở hữu toàn bộ README và tầng tổng quan, chạy cuối.

**Điểm cần reviewer soi kỹ nhất:**
- T9 có vi phạm luật vàng không (nhét tri thức vận hành vào ADR)
- T4 có sửa nhầm cờ `ure_trung_dong` — cũng mang nhãn *"lệch 1,3%"* ở dòng 368 nhưng **không được đụng**, vì chưa đo lại
- Số liệu chép từ báo cáo có đúng không, có kèm ngày đo không
