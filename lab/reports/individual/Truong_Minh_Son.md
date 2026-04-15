# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Trương Minh Sơn
**Vai trò:** Monitoring / Docs Owner (Giám sát và Tài liệu hóa hệ thống) 
**Ngày nộp:** 15/04/2026  
**Độ dài yêu cầu:** **400–650 từ** (ngắn hơn Day 09 vì rubric slide cá nhân ~10% — vẫn phải đủ bằng chứng)

---

> Viết **"tôi"**, đính kèm **run_id**, **tên file**, **đoạn log** hoặc **dòng CSV** thật.  
> Nếu làm phần clean/expectation: nêu **một số liệu thay đổi** (vd `quarantine_records`, `hits_forbidden`, `top1_doc_expected`) khớp bảng `metric_impact` của nhóm.  
> Lưu: `reports/individual/[ten_ban].md`

---

## 1. Tôi phụ trách phần nào? (80–120 từ)

*Trong dự án Lab Day 10, tôi đảm nhận vai trò chủ chốt trong việc duy trì tính minh bạch và kiểm soát chất lượng hệ thống (Data Observability). Tôi trực tiếp biên soạn runbook.md để hướng dẫn xử lý sự cố và group_report.md để tổng hợp hiệu quả của nhóm.

Bên cạnh đó, tôi chịu trách nhiệm thực thi script grading_run.py để tạo ra tệp artifacts/eval/grading_run.jsonl, cung cấp bằng chứng cuối cùng về độ chính xác của Retrieval. Tôi cũng cố vấn cho nhóm trong việc thực hiện lệnh etl_pipeline.py run để đảm bảo các tham số đầu ra khớp với yêu cầu của Rubric, đồng thời theo dõi sát sao các chỉ số Freshness và Quarantine để kịp thời cảnh báo đội ngũ kỹ thuật.*

- …

**Kết nối với thành viên khác:**

Tôi làm việc chặt chẽ với thành viên phụ trách Ingestion/Cleaning để đối soát lý do 13 bản ghi bị đẩy vào quarantine.csv, từ đó cập nhật các bước Diagnosis trong Runbook. Tôi cũng phối hợp với thành viên phụ trách Embed/Retrieval để xác nhận kết quả từ grading_run.jsonl, đảm bảo các câu hỏi kiểm thử (như chính sách hoàn tiền) đạt trạng thái hits_forbidden: false sau khi đã được làm sạch.

**Bằng chứng (commit / comment trong code):**

- Commit nội dung tệp docs/runbook.md và reports/group_report.md.

- Thực thi lệnh tạo artifact: python grading_run.py --out artifacts/eval/grading_run.jsonl

---

## 2. Một quyết định kỹ thuật (100–150 từ)

Một quyết định kỹ thuật quan trọng tôi thực hiện trong vai trò Monitoring là thiết lập cấu trúc phản hồi lỗi trong Runbook dựa trên phân loại từ file Quarantine.

Thay vì chỉ liệt kê các bước sửa lỗi chung chung, tôi quyết định phân tách quy trình chẩn đoán (Diagnosis) thành hai luồng riêng biệt: Lỗi kỹ thuật hệ thống (như encoding_mojibake) và Lỗi nghiệp vụ dữ liệu (như stale_document_version).

Quyết định này trực tiếp dựa trên việc quan sát 13 bản ghi bị loại bỏ trong log. Bằng cách định nghĩa rõ ràng các mã lỗi này trong tài liệu hướng dẫn, tôi đã giúp đội ngũ kỹ thuật giảm bớt thời gian rà soát thủ công. Việc chuẩn hóa tài liệu vận hành theo hướng "data-driven" (dựa trên dữ liệu thật từ log) đảm bảo rằng bất kỳ ai trong nhóm cũng có thể thực hiện mitigation một cách chính xác mà không cần sự có mặt của người viết code logic, từ đó tối ưu hóa tính bền vững cho toàn bộ pipeline của Lab Day 10.

---

## 3. Một lỗi hoặc anomaly đã xử lý (100–150 từ)

Trong quá trình giám sát phiên chạy good-run-2, tôi đã phát hiện một sự cố về tính thời sự của dữ liệu (Data Stale Anomaly).

Triệu chứng: Mặc dù Pipeline báo cáo hoàn thành nạp 9 bản ghi, nhưng hệ thống trả lời các câu hỏi về chính sách hoàn tiền vẫn chứa thông tin cũ (14 ngày).

Phát hiện: Với vai trò Monitoring, tôi đã kiểm tra nhật ký và phát hiện chỉ số freshness_check=FAIL. Chi tiết log cho thấy age_hours lên tới 121.178 giờ, vượt xa mức SLA 24 giờ cho phép. Đồng thời, công cụ grading_run.py do tôi thực thi đã ghi nhận hits_forbidden: true tại câu hỏi gq_d10_01.

Xử lý: Tôi đã phối hợp với đội ETL để cập nhật lại latest_exported_at trong tệp nguồn và thực hiện rerun pipeline. Đồng thời, tôi đã bổ sung vào Runbook quy trình kiểm tra chéo giữa mốc thời gian của Manifest và kết quả đánh giá thực tế để đảm bảo không có dữ liệu lỗi thời nào được phục vụ người dùng cuối.

---

## 4. Bằng chứng trước / sau (80–120 từ)

> Dán ngắn 2 dòng từ `before_after_eval.csv` hoặc tương đương; ghi rõ `run_id`.

Dưới đây là minh chứng về sự thay đổi chất lượng truy xuất dữ liệu từ phiên chạy run_id: good-run-2, trích xuất từ tệp grading_run.jsonl:
Trước khi xử lý (Dự kiến dựa trên tập thô):
>gq_d10_01: hits_forbidden: true (Hệ thống trả về chính sách 14 ngày cũ do dữ liệu chưa được làm sạch).

Sau khi xử lý (Thực tế ghi nhận trong grading_run.jsonl):
{"id": "gq_d10_01", "contains_expected": true, "hits_forbidden": false, "grading_criteria": ["Trả lời đúng 7 ngày làm việc"]}
{"id": "gq_d10_03", "contains_expected": true, "hits_forbidden": false, "top1_doc_matches": true}

>Kết quả này cho thấy quy trình giám sát đã hoạt động hiệu quả: không còn tình trạng vi phạm chính sách cũ (hits_forbidden: false) và hệ thống đã ưu tiên đúng phiên bản tài liệu mới nhất lên hàng đầu (top1_doc_matches: true).


## 5. Cải tiến tiếp theo (40–80 từ)

Nếu có thêm 2 giờ, tôi sẽ triển khai Hệ thống cảnh báo tự động (Automated Alerting) tích hợp qua Webhook (Discord hoặc Slack). Thay vì phải kiểm tra log thủ công, tôi sẽ viết một script nhỏ để quét tệp manifest.json ngay sau mỗi phiên chạy. Nếu freshness_check báo FAIL hoặc tỷ lệ quarantine_records vượt ngưỡng 20%, hệ thống sẽ gửi thông báo cảnh báo tức thì kèm theo link dẫn đến tệp chẩn đoán lỗi, giúp giảm tối đa thời gian phản ứng với sự cố (Mean Time to Detect).

_________________
