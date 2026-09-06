# Brief phân xử (lượt 3) — bộ gold

Hai annotator độc lập (lượt 1, lượt 2) đã gán nhãn cùng một bài và LỆCH nhau ở ít nhất một trường. Bạn là trọng tài: đọc bài, đọc hai nhãn và ghi chú của họ, rồi quyết nhãn CUỐI theo đúng tiêu chí — không thoả hiệp kiểu "lấy trung bình", không nghiêng về lượt nào theo mặc định. Được phép chọn nhãn thứ ba nếu cả hai đều sai.

Tiêu chí và tài liệu chuẩn: đọc C:/Users/tuanb/AppData/Local/Temp/claude/D--twan-projects-dulieuchungkhoan-vn/8822569d-752d-4211-8356-f10bb9cedcae/scratchpad/gold/v2/BRIEF.md (mục "Tài liệu chuẩn" và "Tiêu chí") — áp dụng y nguyên.

Đầu vào: file dis-N.jsonl, mỗi dòng: article_id, diff (trường lệch), p1, p2 (nhãn + note của hai lượt), hard, source, hint, url, title, sapo, excerpt.
Đầu ra: một dòng JSON mỗi bài, cùng thứ tự, không bỏ sót:
{"article_id": <int>, "group": ..., "sub": ..., "tickers": [...], "industries": [...], "picked": "p1"|"p2"|"new", "reason": "<một câu: vì sao, bám tiêu chí nào>", "taxonomy_gap": "<rỗng, hoặc một câu nếu bài này lộ ra chỗ taxonomy chưa phủ>"}
Ghi bằng Python utf-8 ensure_ascii=False; tự kiểm hợp lệ (sub thuộc group, ticker ∈ listed.json, industry ∈ 24 mã, ≤5 mã, ≤3 ngành, ticker rỗng khi group ≠ 3). Không dispatch subagent, không sửa file trong repo.
Trả lời chỉ: số bài, phân bố picked, và tối đa 5 câu taxonomy_gap đáng chú ý nhất (gộp các bài giống nhau).
