# Tiêu chí chấm — hình dạng cấu hình lát 12 (viết TRƯỚC khi sinh phương án, 2026-09-08)

Chấm theo đúng thứ tự dưới. Mỗi tiêu chí phải bất biến (còn đúng sau 3 tháng, trên máy khác).

| # | Tiêu chí | Cách đo |
|---|---|---|
| a | **Một `.env` cho một máy.** Cùng file phục vụ native (host 127.0.0.1) lẫn container (host = tên service) trên máy dev, không sửa tay giữa hai lần chạy | Đếm số file env phải giữ đồng bộ; đếm số lần một mật khẩu/host xuất hiện |
| b | **Cùng code, cùng image** chạy native dev · container dev · container VPS; khác nhau chỉ ở biến môi trường/overlay compose | Có dòng code nào rẽ nhánh theo "đang trong container" không? |
| c | **Secret không in, không nhân bản.** Đổi một mật khẩu = sửa một chỗ; secret không lọt vào log/traceback thường | Số chỗ chứa cùng một mật khẩu; secret có nằm trong chuỗi bị `repr`/log không |
| d | **Bán kính hỏng.** Số file production đụng; rollback bằng một `git revert` | Đếm file; có migration/đổi dữ liệu không |
| e | **Lát 13 và 15 chỉ đổi biến/overlay**, không mở lại quyết định này | Kịch bản: thêm scheduler vào container `etl`; overlay VPS |
| f | **Có phép kiểm tự động** bắt lệch giữa `.env.example` · compose · code (test hợp đồng), không dựa trí nhớ | Phương án có nêu test canh gì không, canh được thật không |
| g | **Không phá hợp đồng khởi động đã có:** thiếu env ⇒ exit 2 · `assert_migrated` · `assert_read_only` · test chạy dưới đúng role production | Rà từng hợp đồng |
| h | **Cấp user login tự động từ env** (etl_worker · agent_reader · ingester_worker · api_reader) trong một bước bootstrap chạy bằng owner — phương án phải nói bốn mật khẩu này sống ở đâu | Có nêu không, có trùng lặp với (c) không |

Loại ngay nếu: cần hai `.env`; cần sửa tay file giữa native và container; secret in ra output; đòi thay đổi migration đã chạy.
