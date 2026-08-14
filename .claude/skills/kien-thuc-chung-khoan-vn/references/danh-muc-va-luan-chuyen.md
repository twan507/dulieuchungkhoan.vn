# Danh mục và luân chuyển

Tầng cơ chế của việc dựng danh mục: phân bậc rủi ro cổ phiếu bằng tiêu chí đo được, phân bổ tỷ trọng bằng công thức, và đọc trật tự tiền chảy giữa các ngành lẫn các bậc dòng tiền. Phần tư duy top-down và chu kỳ chính sách nằm ở `co-van-chung-khoan-vn/references/khung-phan-tich.md`, file này không lặp lại.

## Mục lục

- [Hai lớp luân chuyển: ngành và dòng tiền](#hai-lop-luan-chuyen)
- [Sáu tiêu chí phân bậc dòng tiền cho một cổ phiếu](#sau-tieu-chi)
- [Lưới ngành × dòng tiền và trật tự chạy](#luoi-nganh-dong-tien)
- [Bảng luân chuyển theo chu kỳ tăng và chu kỳ giảm](#bang-luan-chuyen)
- [Đa dạng hoá: bao nhiêu mã](#da-dang-hoa)
- [Lý thuyết danh mục hiện đại và tỷ suất Sharpe](#ly-thuyet-danh-muc)
- [Phân bổ tài sản, tiền mặt như một vị thế](#phan-bo-tai-san)
- [Hai đòn bẩy và cơ chế nhân](#hai-don-bay)
- [Chiến lược lựa chọn cổ phiếu](#chien-luoc-lua-chon)
- [Ba cách mua](#ba-cach-mua)
- [Chiến lược giao dịch theo sự kiện](#chien-luoc-su-kien)
- [Rebalancing](#rebalancing)
- [Rủi ro cổ phiếu và rủi ro bản thân](#rui-ro-ban-than)
- [Ví dụ chạy đủ: một danh mục giả định](#vi-du-chay-du)

---

## Hai lớp luân chuyển

Đây là khác biệt cốt lõi, hay bị gộp làm một. **Luân chuyển ngành** và **luân chuyển dòng tiền** chạy theo hai logic ngược nhau.

| | Luân chuyển ngành | Luân chuyển dòng tiền |
|---|---|---|
| Cấp độ | Giữa các ngành | Giữa các cổ phiếu **trong cùng một ngành** |
| Tiêu chí xếp thứ tự | Độ nhạy của **mô hình kinh doanh** với tình trạng kinh tế | Mức **rủi ro của cổ phiếu** |
| Ai chạy trước | Ngành **nhạy nhất** với điều kiện kinh tế hiện tại | Cổ phiếu **an toàn nhất** trong ngành |
| Tốc độ | Chậm — chuyển từ ngành này sang ngành kia mất lâu | Nhanh — trong ngành, mã sau nối mã trước rất nhanh |

- **Nguyên lý đảo chiều có gốc hành vi.** Người cầm tiền chưa yên tâm thì tìm cái an toàn và hiển hiện trước, tự tin hơn mới nâng mức rủi ro. Nên trong ngành thì an toàn chạy trước; giữa các ngành thì cái nhạy chạy trước vì đó là chỗ biến động lớn nhất.
- **Dòng tiền ở đây không phải dòng tiền kế toán**, cũng không phải dòng tiền thực đo được vào một mã. Nó là **nhãn xếp hạng rủi ro tính sẵn**, dùng để dự đoán mã nào tiền tìm đến sớm.
- **Cơ hội không nằm ở bậc dẫn dắt, nằm ở bậc đầu cơ** — nhưng chỉ khi tiền đã xác nhận vào ngành đó. Mua dòng tiền đầu cơ trước khi tiền đến là sai thời điểm, không phải sai cổ phiếu.
- **Quy tắc cuốn chiếu khi xoay vòng.** Không bao giờ bán hết nhóm cũ để dồn hết vào nhóm mới. Phán đoán ngành A đã chạy xong và ngành B sắp tới lượt thì giữ một ít A, mở một ít B — vì không ai biết chắc A đã hết đà, và vì cách này triệt tiêu cảm giác tiếc, mà tiếc sinh tham, tham sinh sợ. Áp dụng y hệt khi xoay giữa dòng tiền dẫn dắt và dòng tiền lan toả.

---

## Sáu tiêu chí phân bậc dòng tiền

Sáu tiêu chí đơn giản để xếp một cổ phiếu vào ba bậc dòng tiền. Tất cả đều tra được từ dữ liệu thị trường thông thường, không cần mô hình. Đây là bộ tối thiểu, không phải bộ đóng: hệ thống dữ liệu có tiêu chí đo được khác thì thêm vào cùng cách xếp, thiếu tiêu chí nào thì xếp bằng các tiêu chí còn lại.

| Tiêu chí | Dòng tiền dẫn dắt | Dòng tiền lan toả | Dòng tiền đầu cơ |
|---|---|---|---|
| **Vốn hoá** | Lớn | Trung bình | Nhỏ |
| **Thanh khoản** (khối lượng khớp bình quân) | Lớn | Trung bình | Nhỏ |
| **P/E, P/B** | Trung bình đến thấp, **không quá thấp** | Thấp và rất thấp | Cao, hoặc âm |
| **Cổ tức và thu nhập** | Trả cổ tức đều, thu nhập đều | Có trả nhưng không đều, hoặc lợi nhuận thấp, hoặc mới có tiềm năng trả | Không trả cổ tức, lợi nhuận thấp hoặc âm |
| **Thị giá** | Nằm giữa khoảng thấp nhất – cao nhất của ngành | Giá cao | Giá rất thấp (cổ phiếu đầu cơ thị giá thấp) |
| **Danh tiếng** | Phổ biến, nhiều người biết, tiếng tốt lâu năm | Ở giữa | Ít người biết, hoặc có tiếng xấu |

Năm lưu ý kèm theo, phải giữ nguyên:

- **Quan hệ giữa P/E và mức an toàn không đơn điệu — hai đầu cực đều rủi ro, khoảng giữa mới an toàn.** Nguồn có chỗ nói "thị trường xem P/E cao là an toàn" và chỗ khác xếp P/E cao vào bậc đầu cơ; không mâu thuẫn nếu tách hai nguyên nhân: **P/E cao do thị trường trả giá cho tăng trưởng** khác hẳn **P/E cao do lợi nhuận sụp về gần 0** — mẫu số nhỏ đẩy tỷ số lên, và đó là dấu hiệu nguy hiểm, cùng họ với P/E âm.
- **P/E và P/B thấp ở Việt Nam phản ánh rủi ro, không phải rẻ.** Thói quen coi cổ phiếu giá trị là an toàn là sai ở thị trường này. Theo khung Fama-French, cổ phiếu P/E–P/B thấp thuộc nhóm rủi ro cao nên kỳ vọng lợi nhuận cao hơn — chứ không phải nhóm an toàn. Cổ phiếu tăng trưởng mới là nhóm bản chất an toàn hơn.
- **Thị giá quá cao cũng không an toàn.** Giá quá cao thì người ta sợ, giá quá thấp thì người ta cho là rủi ro. Chỗ an toàn là khoảng giữa.
- **Danh tiếng hoàn toàn ước lượng**, không định lượng được. Vẫn giữ vì nó quyết định mã nào được chú ý trước, mà chú ý trước thì tiền vào trước.
- **Tầng bài bản hơn là định giá và đánh giá chất lượng doanh nghiệp:** mã nào vừa rẻ theo định giá so sánh (ngắn hạn) vừa rẻ theo định giá dòng tiền (dài hạn) thì khả năng an toàn cao hơn. Vai trò đúng của định giá ở đây không phải đặt giá mục tiêu, mà là **phân loại dòng tiền**.

---

## Lưới ngành × dòng tiền

Ghép hai trục thành lưới ba × ba, chín ô — bản đồ để biết đang ở đâu trong sóng.

**Trật tự chạy điển hình trong một chu kỳ lớn** (đơn vị một đến hai năm, không phải một đến hai tuần): dòng tiền dẫn dắt của ngành dẫn dắt → dòng tiền lan toả của ngành dẫn dắt → dòng tiền dẫn dắt của ngành lan toả xuất hiện, **không cần chờ** dòng tiền đầu cơ của ngành dẫn dắt kết thúc → dòng tiền đầu cơ của ngành dẫn dắt cộng dòng tiền lan toả của ngành lan toả → dòng tiền dẫn dắt của ngành phòng thủ, cuối cùng là dòng tiền đầu cơ của ngành phòng thủ.

Năm quy tắc đọc lưới:

- **Đan xen, không tuần tự.** Ngành lan toả hoạt động không có nghĩa ngành dẫn dắt đã kết thúc — chỉ nghĩa là ngành lan toả đang có tiền vào nhiều hơn và biên độ mạnh hơn.
- **Lượng tiền giảm dần khi lan ra xa**, nên càng về cuối chuỗi càng ít mã thực sự được đẩy. Lan toả rộng chứng tỏ tổng tiền mạnh.
- **Ngành phòng thủ chạy mang hai nghĩa cùng lúc:** tiền đang nhiều nhất, và tiền sắp hết. Khi dòng tiền đầu cơ của mọi ngành đều đã chạy, thị trường chuẩn bị bão hoà.
- **Tín hiệu điều chỉnh cụ thể:** dòng tiền đầu cơ vẫn tăng tốt nhưng dừng lại, đồng thời xuất hiện lực mua vào dòng tiền dẫn dắt của ngành dẫn dắt → khả năng điều chỉnh cao. Đó là dấu hiệu kết thúc một vòng, không phải dấu hiệu tăng tiếp.
- **Áp dụng được cho cả chu kỳ nhỏ** nằm trong chu kỳ lớn, chỉ khác là ranh giới các giai đoạn mờ hơn nhiều nên độ tin cậy thấp hơn.

---

## Bảng luân chuyển theo chu kỳ

### Xếp hạng ngành theo độ nhạy

Xếp hạng dựa trên bốn thành phần rủi ro cộng lại: **đòn bẩy hoạt động**, **đòn bẩy tài chính**, **rủi ro chu kỳ** (độ nhạy với chính sách kinh tế), **rủi ro mùa vụ** (độ nhạy với giá hàng hoá đầu vào — ví dụ giá dầu với dầu khí; ngành không có biến số hàng hoá rõ ràng thì dùng lạm phát làm biến chung).

**Cách chấm.** Cho mỗi ngành một điểm ở từng thành phần, cộng lại rồi xếp hạng từ an toàn nhất tới rủi ro nhất. Chia dải xếp hạng làm ba phần đều nhau ra ba bậc ngành. Số ngành mỗi bậc tuỳ khung phân ngành đang dùng — với một khung khoảng 19–20 ngành thì mỗi bậc rơi vào 6–7 ngành.

| Bậc | Đặc trưng của ngành rơi vào bậc này | Thứ tự trong bậc |
|---|---|---|
| **Ngành dẫn dắt** | Điểm rủi ro cao nhất — đòn bẩy lớn, nhạy chu kỳ, nhạy mùa vụ. Gồm nhóm tài chính và các ngành sản xuất đầu vào có đòn bẩy cao | Ngành nào **an toàn nhất trong bậc** biến động trước, rồi lan sang các ngành rủi ro hơn cùng bậc |
| **Ngành lan toả** | Điểm rủi ro trung bình — doanh thu gắn sản lượng thực, đòn bẩy vừa phải | Ngành gần người tiêu dùng cuối thường chạy trước, có thể xen vào bậc dẫn dắt |
| **Ngành phòng thủ** | Điểm rủi ro thấp nhất — nhu cầu tồn tại bất kể chu kỳ, đòn bẩy thấp | — |

**Danh sách ngành cụ thể không cố định trong skill** — nó phụ thuộc khung phân ngành mà hệ thống dữ liệu đang dùng. Cái cố định là **cách chấm điểm** ở trên.

**Ngân hàng đứng đầu bảng xếp hạng an toàn nhưng lại hút tiền đầu tiên**, vì nó nằm đúng ranh giới giữa rủi ro và tăng trưởng — nên nó là **ngành báo hiệu**, dùng đọc tín hiệu chu kỳ chứ chưa chắc là chỗ giao dịch tốt nhất. Độ chính xác của xếp hạng khá cao với ngành dẫn dắt, giảm dần ở ngành lan toả và ngành phòng thủ khi tiền vào nhiều. Riêng xếp hạng theo **rủi ro đòn bẩy** (hoạt động cộng tài chính) dùng độc lập được để đoán mã nào bật mạnh, mã nào bật yếu ở mùa công bố kết quả kinh doanh, cho bất kỳ kỳ báo cáo nào.

### Chu kỳ tăng — ba bước

Ba bậc dòng tiền, phân theo vốn hoá — cách phân loại rủi ro phổ biến nhất: **dòng tiền dẫn dắt** vốn hoá lớn, quản trị tốt, đầu ngành; **dòng tiền lan toả** vốn hoá trung bình, có truyền thống tăng giá trong quá khứ; **dòng tiền đầu cơ** vốn hoá nhỏ.

| Bước | Hành động của dòng tiền | Dấu hiệu quan sát | Margin |
|---|---|---|---|
| **1. Đáy** | Cá nhân vào dòng tiền dẫn dắt; nhà đầu tư giá trị vào ngành hưởng lợi chu kỳ | Khối lượng **ngừng giảm**, có dấu hiệu tăng lại. Tăng chậm và từ từ | Chưa dùng |
| **2. Tăng mạnh nhất** | Bán bớt dòng tiền dẫn dắt, mua mạnh dòng tiền lan toả | Khối lượng tăng hàng ngày, thị trường tin đang có sóng lớn | Bắt đầu dùng, và **luôn vào dòng tiền dẫn dắt trước** — muốn đòn bẩy nhưng vẫn muốn bảo toàn vốn |
| **3. Cuối sóng** | Bán bớt dòng tiền dẫn dắt và lan toả, mua mạnh dòng tiền đầu cơ, nhất là mã có tin tốt | Khối lượng vẫn cao nhưng **tăng chậm lại**; chỉ số lưỡng lự | Dồn nhiều vào dòng tiền lan toả |

**Phần luân chuyển của việc nhận diện đỉnh:** luân chuyển phải đã chạm đủ cả ba bậc, kể cả bậc đầu cơ; và margin phải đạt mức cao nhất — margin tập trung ở dòng tiền dẫn dắt và lan toả, dòng tiền đầu cơ thường không có margin, nên margin hết dư địa nghĩa là bên mua hết vũ khí. Đủ bộ ba điều kiện nhận diện đỉnh và cách hành động ở `co-van-chung-khoan-vn/references/doc-hanh-vi-thi-truong.md`, mục *Nhận diện đỉnh*.

### Chu kỳ giảm — ba bước

Chiều đi xuống đảo ngược thứ tự chiều đi lên: tiền quay về dòng tiền dẫn dắt của ngành dẫn dắt trước, rồi ngành lan toả, rồi ngành phòng thủ.

| Bước | Hành động của dòng tiền | Đặc điểm | Bẫy |
|---|---|---|---|
| **1. Giảm âm thầm** | Dòng tiền dẫn dắt và lan toả bị bán, kích hoạt call margin | Margin nằm ở vốn hoá lớn nên bán tạo rối loạn rất nhanh. Dòng tiền đầu cơ **vẫn có thể tăng** vì chưa ai tin sóng đã hết | **Bẫy tăng, xác suất rất cao** |
| **2. Giảm mạnh nhất** | Tất cả bị bán cùng margin. Sau đó nhà đầu tư giá trị mua mạnh dòng tiền dẫn dắt và ngành phòng thủ, tạo một điểm nghỉ | Giai đoạn đáng sợ nhất. Dòng tiền đầu cơ vẫn tiếp tục bị bán | **Bẫy giảm, xác suất cực lớn** |
| **3. Điều chỉnh cuối** | Mua thăm dò, margin dùng lại rất hạn chế. Dòng tiền dẫn dắt và lan toả bắt đầu được mua lại | Chỉ số giảm **từ từ nhưng kéo dài rất lâu**, tạo phân hoá, bào mòn người cầm dòng tiền đầu cơ | — |

---

## Đa dạng hoá danh mục

Một tập hợp mã chỉ thành **danh mục** khi có cấu trúc bù trừ: đủ nhóm ngành, đủ mức rủi ro, đủ vốn hoá lớn nhỏ, đủ tăng trưởng lẫn giá trị. Danh sách 50 mã không cấu trúc vẫn chỉ là danh sách. Mục đích của đa dạng hoá là loại **rủi ro đặc thù doanh nghiệp** (specific risk) để chỉ còn lại **rủi ro thị trường** (systematic risk) — cái không loại được.

**Các nguồn nói khác nhau về số mã tối ưu. Cả ba đều đúng trong điều kiện riêng:**

| Con số | Xuất phát từ | Áp dụng khi |
|---|---|---|
| **20–30 mã** | Ngưỡng lý thuyết để triệt tiêu gần hết rủi ro riêng lẻ — cũng là lý do các chỉ số lớn chỉ cần khoảng 30 mã | Mục tiêu là **bám thị trường**, nắm giữ dài, ít mua bán |
| **10–15 mã** | Kinh nghiệm thị trường Việt Nam: ngoài 20 mã thì lợi ích đa dạng hoá cạn dần, trong khi chi phí theo dõi vẫn tăng | Mục tiêu là danh mục **dài hạn tự quản lý được** |
| **4–5 mã** | Giới hạn theo dõi thực tế của một cá nhân có giao dịch | Có **mua bán thường xuyên** — quá 10 mã mà xoay liên tục là bất khả thi |

Quy tắc gỡ mâu thuẫn: **số mã bị chặn trên bởi hai thứ — tần suất giao dịch và sức theo dõi thực tế của người cầm. Lấy cái nào chặt hơn.** Nắm giữ càng dài thì trần theo tần suất càng cao; xoay càng nhiều thì trần đó càng thấp. Nhưng người mới, vốn nhỏ, hoặc ít thời gian thì **trần sức theo dõi mới là cái chặn thật** — lúc đó ít mã hơn bảng trên là đúng, không phải sai. Và phải tách bạch hai danh sách: **watchlist** 15–30 mã, phân theo bậc dòng tiền và theo ngành, mỗi bậc 5–10 mã. Cách dựng: lấy vài ngành đang trong tầm ngắm của chu kỳ hiện tại, mỗi ngành vài mã ở mỗi bậc dòng tiền — số ngành theo dõi cùng lúc tuỳ sức của người theo, không phải con số cố định. **Danh mục** là phần thực sự có tiền trong đó.

---

## Lý thuyết danh mục hiện đại

Lý thuyết danh mục hiện đại dựng trên đúng hai đặc tính của mọi tài sản tài chính: **lợi nhuận kỳ vọng** và **rủi ro**. Có từ hai tài sản trở lên thì xuất hiện đặc tính thứ ba: **mức tương quan**.

**Hai cách đo rủi ro một cổ phiếu:**

| | Đo cái gì | Ý nghĩa |
|---|---|---|
| **Beta (β)** | Biến động của cổ phiếu so với thị trường | Beta lớn thì bật nhanh hơn thị trường cả hai chiều. Chỉ phản ánh phần rủi ro thị trường |
| **Độ lệch chuẩn (σ)** | Biến động quanh chính mức lợi nhuận trung bình của nó | Phản ánh rủi ro **tổng thể**: rủi ro thị trường cộng rủi ro riêng |

**Công thức cần dùng** (`wi` là tỷ trọng vốn, `Σwi = 1`; `ρ` là hệ số tương quan, từ −1 đến 1):

- Lợi nhuận kỳ vọng danh mục — **luôn bằng đúng bình quân gia quyền**: `E(rp) = Σ wi · E(ri)`
- Rủi ro danh mục hai tài sản: `σp = √( w1²σ1² + w2²σ2² + 2·w1·w2·ρ12·σ1·σ2 )`
- Rủi ro danh mục n tài sản, dùng một `ρ` bình quân cho gọn: `σp² = ρ·(Σ wi·σi)² + (1−ρ)·Σ wi²·σi²`
- **Tỷ suất Sharpe**: `Sharpe = ( E(rp) − rf ) / σp`, với `rf` là lãi suất phi rủi ro — thực dụng thì lấy lãi suất tiết kiệm kỳ hạn 12 tháng.

**Kết luận rút ra từ các công thức này:**

- **Rủi ro danh mục luôn nhỏ hơn bình quân gia quyền rủi ro thành phần**, vì tương quan giữa hai cổ phiếu không bao giờ bằng 1. Đó là toàn bộ lợi ích của đa dạng hoá — nó nằm ở vế rủi ro, không nằm ở vế lợi nhuận.
- **Danh mục tốt là danh mục có Sharpe cao nhất, không phải lợi nhuận cao nhất.** Lãi 30% với rủi ro gấp ba kém hơn lãi 10% với rủi ro một phần. Kiếm 200–300% so với 60–70% không chứng minh giỏi hơn, chỉ chứng minh chấp nhận rủi ro nhiều hơn.
- **Tối ưu hoá tỷ trọng kiểu Markowitz là chuyện của phần mềm**, đòi chạy lại mô hình định kỳ và mua bán để tái cân bằng; cá nhân gần như không ai làm. Thay thế thực dụng: chia đều, hoặc phân bổ theo mức hấp dẫn định giá, hoặc theo tỷ lệ risk-reward kỹ thuật. Nguyên tắc tối thiểu vẫn là không dồn hết vào một rổ.
- Khi ai đó viện dẫn kết luận kiểu "giữ đủ lâu thì danh mục luôn tăng": khung thời gian của các nghiên cứu đó rất dài — nguồn ghi khoảng 60–70 năm, con số không chắc chắn — dài hơn đời đầu tư của phần lớn cá nhân, nên không áp thẳng được.

---

## Phân bổ tài sản

**Phân bổ hạng tài sản quan trọng hơn nhiều so với chọn từng cổ phiếu** — chọn khu rừng quan trọng hơn chọn từng cây. Các hạng: chứng khoán, bất động sản, hàng hoá, hàng sưu tầm, tiền số; trong chứng khoán lại có cổ phiếu, trái phiếu, tiền. Đánh đổi giữa các hạng: chứng khoán thanh khoản hơn bất động sản nhưng dao động mạnh hơn; hàng sưu tập cho cảm giác yên tâm nhưng gần như không thanh khoản.

**Tiền mặt là một cổ phiếu.** Giữ tiền là giữ cổ phiếu an toàn nhất. Hệ quả thực hành:

- Danh mục "thuần cổ phiếu" vẫn phải hàm ý có một tỷ trọng tiền. Không bao giờ chắc chắn mua đúng thời điểm; mua một lần hết tiền thì khi giá giảm thêm không còn sức mua. **Chia tiền làm ba phần, mỗi lần vào một phần.**
- Khi phán đoán thị trường đi xuống, cầm tiền là **vị thế chủ động**, không phải đứng ngoài.
- Ngoài tiền đầu tư còn phải có tiết kiệm dự phòng cho chi phí gia đình. Vay để đầu tư, lỗ rồi vay tiếp để gỡ — không còn là đầu tư.

Tỷ trọng cổ phiếu rủi ro nên gắn với tình trạng cá nhân, không gắn với dự báo thị trường: người trẻ tích luỹ chịu được rủi ro cao hơn; người có gia đình cần cẩn trọng ở khâu **phân bổ nguồn lực** chứ không nhất thiết ở khâu chọn mã an toàn; người cần thu nhập ổn định nghiêng về cổ tức và mã biến động thấp. Số vốn cũng quyết định: vốn lớn thì vốn hoá lớn; vốn nhỏ chơi mã nhỏ thì phải gom dần từng ngày từng tuần, vì khi mã đã lớn thì không mua được nữa.

---

## Hai đòn bẩy

Phân tích ngành theo từng chỉ tiêu một thì không bao giờ hết. Cuối cùng quy về hai biến, và cả hai cùng đo một thứ: **độ nhạy của lợi nhuận trước một đồng doanh thu thêm và một điểm lãi suất thêm.**

| | Bản chất | Đo tĩnh | Đo động | Hưởng lợi khi |
|---|---|---|---|---|
| **Đòn bẩy hoạt động (DOL)** | Tương quan chi phí cố định / chi phí biến đổi | Tỷ lệ chi phí cố định trong tổng chi phí | `DOL = %Δ lợi nhuận hoạt động ÷ %Δ doanh thu` | **Kinh tế tăng trưởng** |
| **Đòn bẩy tài chính (DFL)** | Tương quan nợ / vốn chủ sở hữu | `Nợ ÷ Vốn chủ sở hữu`, hoặc `Nợ ÷ Tổng tài sản` | `DFL = %Δ lợi nhuận sau thuế ÷ %Δ lợi nhuận hoạt động` | **Lãi suất giảm** |

**Cơ chế nhân đôi.** Hai đòn bẩy nhân với nhau, không cộng: `DTL = DOL × DFL`, và `%Δ lợi nhuận sau thuế = DTL × %Δ doanh thu`. Ví dụ: doanh nghiệp có DOL = 2,0 và DFL = 1,8 → DTL = 3,6, nên doanh thu tăng 10% thì lợi nhuận sau thuế tăng 36%. **Cùng cơ chế đó chạy ngược:** doanh thu giảm 10% thì lợi nhuận sau thuế giảm 36%. Đây là lý do nhóm hai đòn bẩy cùng cao vừa bật mạnh nhất ở đoạn thuận, vừa gãy nhanh nhất ở đoạn nghịch.

Ba lưu ý khi áp vào Việt Nam:

- **Ngân hàng là ngoại lệ.** Lý thuyết phương Tây xếp ngân hàng vào nhóm đòn bẩy hoạt động cao, nhưng thực tế Việt Nam thấp vì bị chi phối bởi hạn mức tín dụng.
- **Mở rộng tiền tệ khác mở rộng kinh tế.** Có giai đoạn tiền đã bơm mà kinh tế chưa chạy — đoạn của đòn bẩy tài chính đã qua nhưng đoạn của đòn bẩy hoạt động chưa tới.
- **Thị hiếu ngành là yếu tố thứ ba**, gần như không cần đưa vào mô hình: đó chỉ là cổ phiếu thời trang theo giai đoạn, khác bản chất với hai đòn bẩy.

---

## Chiến lược lựa chọn cổ phiếu

Sáu trục phân loại cổ phiếu. Một danh mục có cấu trúc nên bù trừ trên nhiều trục cùng lúc, không chỉ trục ngành.

| Trục | Hai đầu | Ghi chú |
|---|---|---|
| **Ngành** | Một ngành ↔ nhiều ngành | Chỉ một ngành thì không phải đa dạng hoá, mà là rủi ro |
| **Bậc dòng tiền** | Beta thấp ↔ beta cao (dòng tiền dẫn dắt ↔ dòng tiền đầu cơ) | Trục chính |
| **Vốn hoá** | Lớn ↔ nhỏ | |
| **Giá trị / tăng trưởng** | P/E, P/B thấp ↔ cao | Ở Việt Nam, đầu "giá trị" là đầu rủi ro |
| **Momentum / ngược dòng** | Mua cái đang tăng ↔ bán cái đã tăng lâu | Không đầu nào luôn thắng; tiền vào nhiều thì momentum tốt |
| **Nguồn lợi nhuận** | Cổ tức ↔ tăng trưởng vốn | Chọn thu nhập là đã chọn một điểm cân bằng rủi ro–lợi nhuận |

Phân biệt momentum và ngược dòng cho chặt: **momentum** mua ngay lúc bắt đầu đi lên từ dưới; **ngược dòng** bán khi đã đi lên một thời gian mà vẫn đang tăng. Nước ngoài bán ròng trong lúc thị trường tăng thường là chiến lược ngược dòng, không phải tín hiệu xấu.

**Nguyên tắc trùm lên mọi chiến lược: vào bằng lý do gì, ra bằng lý do đó.** Mua vì môi trường chính sách phù hợp thì khi chính sách đổi phải nghĩ tới ra. Mua vì lợi nhuận đột biến thì khi luận điểm vẫn chỉ là lợi nhuận đột biến cũ, nó đã hết. Mua vì chạm hỗ trợ có phân kỳ mà hai ngày sau không bật lên thì ra.

---

## Ba cách mua

Ba lý thuyết mua phổ biến, không phải bí kíp riêng của ai: **mua hỗ trợ**, **mua đột phá (breakout)**, **mua theo đà (momentum)**. Bảng cách làm và đặc điểm từng kiểu nằm ở `ky-thuat-chi-bao.md`, mục *Khoảng trống giá* — không lặp lại ở đây. Ba điểm bổ sung khi chọn cách mua cho một danh mục:

- **Khối lượng đi kèm là dấu hiệu xác nhận:** mua hỗ trợ thì khối lượng còn **nhỏ** mới đúng, hợp giai đoạn tích luỹ; mua đột phá và mua theo đà đòi khối lượng **lớn**, hợp giai đoạn tăng mạnh.
- **Đột phá và theo đà khác nhau đúng một chỗ:** theo đà chờ đột phá thành công rồi mới vào; đột phá vào ngay khi vượt. **Mua đột phá ở vùng giá đã tăng mạnh là rủi ro nhất** trong ba cách; mua ở lần vượt đầu tiên cũng rủi ro, mua sau một khung dao động hẹp thì bình thường.
- **Mua theo đà chỉ có ý nghĩa nếu khoảng cách tới mục tiêu kế tiếp còn đủ lớn.** Cổ phiếu đã tăng chưa chắc hết cơ hội — câu hỏi là còn bao xa tới mục tiêu, không phải đã tăng bao nhiêu. Trong ngắn hạn nguồn tính theo T+2 đến T+2,5 `[?con số nhận dạng không chắc]`. Thực tế mua hỗ trợ thường là **gom trước ở hai nhịp đầu khi khối lượng còn nhỏ, rồi mua thêm khi đột phá.**

---

## Chiến lược giao dịch theo sự kiện

Mọi sự kiện — vĩ mô hay doanh nghiệp — đi qua ba giai đoạn **dọn đường → thông báo → thực hiện** (cơ chế và phản ứng từng bước ở `tam-ly-va-thong-tin.md`, mục *Quy trình chính sách*). Quy luật: dọn đường và thông báo phản ứng mạnh nhất, thực hiện phản ứng yếu nhất. Đúng cho cả tin tốt lẫn tin xấu, chỉ khác mức điều chỉnh sau đó: tin tốt **dẫn tới tiền ra thật** (ví dụ giảm lãi suất) thì khả năng giữ và tăng tiếp sau điều chỉnh cao hơn; tin tốt dạng **đồn đại, không thực hiện** thì điều chỉnh mạnh hơn; tin xấu **được thực hiện thật** thì thường chỉ quanh quẩn; tin xấu **không phải xấu thật** thì có xu hướng quay trở lại.

**Giai đoạn cửa sổ.** Ngày sự kiện là điểm zero; trước và sau đều có một khoảng cửa sổ, dài ngắn tuỳ trường hợp — vài ngày, một tuần, một tháng — và cửa sổ của bên mua khác bên bán. Điểm phải nói rõ: **cửa sổ tính bằng một số phiên T+, không phải T+0.** Hiểu thành phải vào đúng ngày sự kiện là hiểu sai.

Nguyên tắc hành động: **không làm gì tại đúng ngày sự kiện**, dù tin tốt hay xấu; hành động theo điểm uốn.

- Tin tốt ra mà cổ phiếu vẫn tăng → để chạy, cân nhắc bán khi có điểm uốn.
- Cổ phiếu đang giảm mà tin tốt ra → cân nhắc mua, chờ trong cửa sổ chứ không mua ngày công bố.
- Tin xấu ra, giá điều chỉnh thái quá → cơ hội mua. Tận dụng sự thái quá, không phải tận dụng dài hạn.
- Tin đồn xuất hiện trước sự kiện và cổ phiếu tích luỹ rồi bật lên → điểm mua tốt, vẫn nằm trong cửa sổ.

Chiến lược sự kiện bản chất là **ngắn hạn**, dùng được lâu dài chỉ vì sự kiện luôn xuất hiện: cổ tức, kết quả kinh doanh, cổ phiếu thưởng, tăng vốn. Cảnh báo đi kèm: thông tin lợi nhuận do bên ngoài công bố trước doanh nghiệp phần lớn là game — doanh nghiệp tử tế nói ít về lợi nhuận và không tiết lộ cho đầu mối bên ngoài. Đã là trò chơi thì tuyệt đối không nhầm với đầu tư và không kéo dài hạn.

---

## Rebalancing

**Định nghĩa chặt: bán rồi mua lại đúng cùng một lượng cổ phiếu, để vị thế không đổi.** Mua bán khác lượng thì nó đã thành đầu cơ, ý nghĩa rào chắn không còn. Mục đích là phòng vệ rủi ro và hạ giá vốn, không phải tìm kiếm lợi nhuận.

**Ba điều kiện áp dụng — thiếu một thì không phải rebalancing:** (1) đang giữ cổ phiếu và chưa muốn bán, mục tiêu vẫn là nắm giữ; (2) vẫn tin cổ phiếu còn đà lên — nếu đã nghĩ thị trường giảm sâu hơn thì đó là bán thật, câu chuyện khác; (3) giá đang tiệm cận một vùng quan trọng: hỗ trợ, kháng cự, hoặc đường xu hướng lớn. Cơ hội xuất hiện không có nghĩa phải hành động ngay — cần thêm xác nhận kỹ thuật.

**Chiều thực hiện:** tại vùng kháng cự thì **bán trước mua sau**; tại vùng hỗ trợ thì **mua trước bán sau**. **Khung quan sát và tín hiệu:** dùng nến 30 phút (lý do chọn khung này, và nguyên tắc chỉ hành động ở nhịp thứ hai trước một vùng quan trọng, ở `ky-thuat-chi-bao.md`, mục *Tham số và khung thời gian*). Ba tín hiệu cần nhìn: mẫu hình phân kỳ, các mẫu nến (rút chân, engulfing), tương quan giá–khối lượng. Ở khung này yếu tố cơ bản chưa kịp đổi nên tâm lý chi phối — nhưng tin cơ bản vẫn phải theo dõi vì nó tác động tâm lý tức thì, và đọc nến phiên kế tiếp luôn phải đặt trong bối cảnh hỗ trợ/kháng cự, tách khỏi bối cảnh thì rỗng.

**Làm trong ngày — quy tắc cao nhất.** Để sang ngày sau rồi đợi tiếp thành T+2, T+3 thì bản chất đã thành mua thêm chứ không còn là rebalance. Làm sai còn hơn làm muộn.

**Cách chia vị thế để rebalancing được hàng ngày.** Rào cản là chu kỳ thanh toán: bán thì có tiền ngay (hoặc ứng được), mua thì phải đợi T+ mới bán lại được. Cách gỡ: chia số cổ phiếu đang giữ làm **ba phần**, cộng **một phần tiền mặt**; ba phần luân phiên hỗ trợ nhau nên khi phần vừa bán đang chờ tiền về thì phần khác vẫn giao dịch được. Chia càng nhỏ càng xoay được nhiều lần, đổi lại chi phí và công sức tăng. Chỉ làm khi mục tiêu là **đầu tư dài hạn** — đây là cách tự tạo kho hàng cho mình, không phải lướt sóng.

**Đánh đổi phải nói rõ:** rebalancing khó cho lợi nhuận đột phá như ôm cứng một mã chạy mạnh. Đổi biên độ lấy sự ổn định và giá vốn thấp dần. Phân biệt với **tái cân bằng tỷ trọng danh mục** — bán bớt mã đã tăng để kéo tỷ trọng về mức thiết kế; đó là việc theo chu kỳ tháng hoặc quý, khác hoàn toàn.

---

## Rủi ro cổ phiếu và rủi ro bản thân

Hai loại rủi ro khác hẳn nhau; phần lớn sai lầm đến từ việc gộp chúng lại.

| | Rủi ro cổ phiếu | Rủi ro bản thân |
|---|---|---|
| Bản chất | **Khách quan**, gắn với doanh nghiệp và thị trường | **Chủ quan**, là cách ra quyết định |
| Ai quyết định | Chủ doanh nghiệp và thị trường | Chính mình |
| Can thiệp được không | Không — chỉ quyết định mua hay không | Có, hoàn toàn |
| Đo bằng gì | Beta, độ lệch chuẩn, sáu tiêu chí ở trên | Có nguyên tắc hay không |

- **Người an toàn không có nghĩa phải chọn cổ phiếu an toàn.** Người có nguyên tắc chơi mã rủi ro vẫn ổn vì biết cắt lỗ sớm, ăn một đoạn rồi ra; người không nguyên tắc nhảy vào mã rủi ro mới là vấn đề. Ngược lại, chọn cổ phiếu an toàn không đồng nghĩa giao dịch an toàn.
- Hai quy tắc hành động rút ra từ phân biệt này — "rủi ro cao lợi nhuận cao" hiểu theo hai chiều, và hai nguyên tắc người ta hay làm ngược — nằm ở `co-van-chung-khoan-vn/references/khung-phan-tich.md`, mục *Nguyên tắc vào/ra và tỷ trọng*.
- Bốn câu tự soi hồ sơ rủi ro: có ai mách là mua ngay hay phân tích; đọc tin là mua theo hay tìm hiểu thêm; đến lúc cắt lỗ có cắt không; chọn mã theo tích luỹ hay theo đột phá.

---

## Ví dụ chạy đủ

Số liệu giả định trung tính, doanh nghiệp đặt tên A–E. Vốn 1.000 triệu đồng.

### Bước 1 — Phân bổ theo bậc dòng tiền

Đang ở đoạn tiền bắt đầu vào, chưa xác nhận sóng lớn → nghiêng về bậc dẫn dắt, giữ 10% tiền mặt làm sức mua. Cấu trúc kiểm tra được: đủ ba bậc ngành, đủ ba bậc dòng tiền, dòng tiền dẫn dắt chiếm 50%, dòng tiền đầu cơ chỉ 5%.

| Mã | Bậc ngành | Bậc dòng tiền | Tỷ trọng `w` | `E(r)` | `σ` |
|---|---|---|---|---|---|
| A | Ngành dẫn dắt | Dòng tiền dẫn dắt | 30% | 12% | 18% |
| B | Ngành dẫn dắt | Dòng tiền lan toả | 20% | 18% | 28% |
| C | Ngành lan toả | Dòng tiền dẫn dắt | 20% | 14% | 20% |
| D | Ngành lan toả | Dòng tiền lan toả | 15% | 20% | 32% |
| E | Ngành phòng thủ | Dòng tiền đầu cơ | 5% | 30% | 50% |
| Tiền mặt | — | — | 10% | 5% | 0% |

### Bước 2 — Lợi nhuận kỳ vọng và độ lệch chuẩn

`E(rp) = 0,30·12 + 0,20·18 + 0,20·14 + 0,15·20 + 0,05·30 + 0,10·5 = 3,6 + 3,6 + 2,8 + 3,0 + 1,5 + 0,5 = 15,0%`

Giả định hệ số tương quan bình quân `ρ = 0,6` giữa năm mã (thị trường Việt Nam tương quan cao); tiền mặt có `σ = 0`.

`Σ wi·σi = 0,30·18 + 0,20·28 + 0,20·20 + 0,15·32 + 0,05·50 = 5,4 + 5,6 + 4,0 + 4,8 + 2,5 = 22,3`
`Σ wi²·σi² = 0,09·324 + 0,04·784 + 0,04·400 + 0,0225·1024 + 0,0025·2500 = 29,16 + 31,36 + 16,00 + 23,04 + 6,25 = 105,81`
`σp² = 0,6·(22,3)² + 0,4·105,81 = 298,37 + 42,32 = 340,70` → `σp = √340,70 = 18,5%`

**Đọc kết quả:** bình quân gia quyền độ lệch chuẩn là 22,3%, danh mục chỉ 18,5%. Chênh 3,8 điểm phần trăm chính là phần rủi ro riêng lẻ bị đa dạng hoá triệt tiêu — và nó chỉ xuất hiện ở vế rủi ro, vế lợi nhuận vẫn đúng bằng bình quân gia quyền.

### Bước 3 — Tỷ suất Sharpe và phép so sánh đắt giá

Lấy `rf = 6%` (lãi suất tiết kiệm 12 tháng giả định).

`Sharpe danh mục = (15,0 − 6) / 18,5 = 0,49`
`Sharpe nếu dồn hết vốn vào mã E = (30 − 6) / 50 = 0,48`

Phương án dồn hết vào mã rủi ro nhất có kỳ vọng lãi gấp đôi nhưng **hiệu quả trên mỗi đơn vị rủi ro không hơn**. Đó là toàn bộ lý do không đánh giá kết quả đầu tư bằng con số phần trăm trần trụi.

### Bước 4 — Một lần rebalancing

Vị thế mã A: 30% × 1.000 triệu = 300 triệu, giá 25.000đ → **12.000 cổ phiếu**, chia ba phần mỗi phần **4.000 cổ phiếu**; tiền mặt 100 triệu. Bối cảnh: A tăng bốn phiên liền, tiệm cận kháng cự 27.000. Vẫn tin A còn đà lên, không định bán thật → đủ điều kiện rebalancing; chiều kháng cự nên **bán trước mua sau**.

- **Phiên trước:** nến ngày cho thấy A chạm 27.000 rồi lùi — nhịp 1, chưa hành động.
- **10h30 phiên sau:** nến 30 phút cho thấy A lên 27.000 lần nữa, khối lượng vọt nhưng thân nến ngắn nằm nửa dưới → nhịp 2, có đàm phán thật tại kháng cự. **Bán 4.000 cp ở 27.000 = 108,0 triệu.**
- **14h00:** A lùi về 26.200, nến 30 phút rút chân, khối lượng bán cạn dần. **Mua lại đúng 4.000 cp ở 26.200 = 104,8 triệu.**
- **Chênh gộp** 3,2 triệu. **Chi phí:** phí bán 108,0 × 0,15% = 0,162; thuế bán 108,0 × 0,1% = 0,108; phí mua 104,8 × 0,15% = 0,157 → tổng ≈ 0,43 triệu. **Lãi ròng ≈ 2,77 triệu**, tương đương 2,6% trên phần vốn xoay, 0,9% trên vị thế A.

**Kết thúc ngày vẫn nắm đúng 12.000 cổ phiếu A.** Tỷ trọng danh mục không đổi, giá vốn bình quân giảm. Nếu chỉ mua lại 3.000 cp thì vị thế còn 11.000 — lúc đó không còn là rebalancing mà là bán bớt một phần, phải gọi đúng tên như vậy.

---
