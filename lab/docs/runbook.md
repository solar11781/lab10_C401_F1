# Runbook — Lab Day 10 (incident tối giản)

---

## Symptom

> User hoặc internal agent nhận câu trả lời sai chính sách hoàn tiền.
- Ví dụ:
Agent trả lời: "Khách hàng có 14 ngày làm việc để yêu cầu hoàn tiền"
Trong khi chính sách mới đúng là:
7 ngày làm việc
- Hiện tượng này xảy ra khi vector database chứa chunk từ policy version cũ hoặc dữ liệu bị inject sai, khiến retrieval trả về thông tin không còn hợp lệ.
---

## Detection

> Metric nào báo? (freshness, expectation fail, eval `hits_forbidden`)
Incident được phát hiện qua các tín hiệu sau:
| Signal | Mô tả | 
|Retrieval evaluation|hits_forbidden = yes trong eval_retrieval|
|Policy Mismatch|Agent trả lời nội dung khác với policy mới|
|Evaluation regression|after_inject_bad.csv cho thấy retrieval trả về chunk bị cấm|
|Freshness monitoring|Manifest có thể cho thấy dữ liệu cũ|

ví dụ phát hiện trong lab:
question: q_refund_window
contains_expected: yes
hits_forbidden: yes
Cho thấy hệ thống đã retrive chunk policy sai (14 ngày)


## Diagnosis

------------------|
| 1 | Kiểm tra `artifacts/manifests/*.json` | Xác nhận pipeline run gần nhất và metadata của dataset|
| 2 | Mở `artifacts/quarantine/*.csv` |Kiểm tra các row bị loại và lý do (duplicate, stale version, encoding lỗi…) |
| 3 | Chạy `python eval_retrieval.py` | Xác định câu hỏi nào đang retrieve chunk sai|
| 4 | Kiểm tra cleaned dataset | Xác nhận text đã được sửa 14 ngày → 7 ngày|
| 5 | Kiểm tra embedding collection | Đảm bảo stale vectors đã bị prune|
---
Giả sử :
Nếu evaluation cho thấy:

hits_forbidden = yes

→ hệ thống vẫn đang retrieve dữ liệu policy sai.
## Mitigation
- Rerun ETL pipeline
python etl_pipeline.py run --run-id good-run-final

- Re-run retrieval evaluation
python eval_retrieval.py --out artifacts/eval/before_after_eval.csv
Mong đợi: hits_forbidden = no

- Check lại file đảm bảo cleaned text chứa:
7 ngày làm việc [cleaned: stale_refund_window]
Rerun lại pipeline để đảm bảo vector DB không tạo ra duplicate 
---

## Prevention
Để phòng tránh các sự cố tương tự, pipeline áp dụng nhiều cơ chế kiểm soát chất lượng dữ liệu trước khi thực hiện embedding. Các cleaning rules sẽ kiểm tra doc_id, chuẩn hóa và xác thực effective_date, đồng thời loại bỏ các phiên bản tài liệu cũ để đảm bảo chỉ những chính sách mới nhất được đưa vào hệ thống. Ngoài ra, pipeline còn phát hiện và loại bỏ dữ liệu trùng lặp, văn bản lỗi hoặc vô nghĩa, đồng thời che thông tin nhạy cảm như số điện thoại và số thẻ. Việc chạy kiểm tra freshness và retrieval evaluation định kỳ giúp phát hiện sớm các lỗi hoặc nội dung chính sách lỗi thời trong hệ thống
