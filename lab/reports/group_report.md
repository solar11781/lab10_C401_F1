# Báo Cáo Nhóm — Lab Day 10: Data Pipeline & Data Observability

## Thông tin nhóm

**Tên nhóm:** F1-C401  

### Thành viên

| Họ và tên | Vai trò | Email |
|-----------|--------|-------|
| Lê Duy Anh | Ingestion Owner | leduyanh2k3@gmail.com |
| Bùi Trần Gia Bảo | Embedding Owner | billxd04@gmail.com |
| Lại Gia Khánh | Embedding Owner | laigiakhanh1211@gmail.com |
| Trương Minh Sơn | Monitoring / Docs Owner | chokhon2004@gmail.com |
| Mạc Phương Nga | Cleaning / Quality Owner | mpnga03@gmail.com |
| Nguyễn Phạm Trà My | Cleaning / Quality Owner | — |

**Ngày nộp:** 15/4/2026 
**Repo:** (https://github.com/solar11781/lab10_C401_F1) 
**Độ dài khuyến nghị:** 600–1000 từ

---

> **Nộp tại:** `reports/group_report.md`  
> **Deadline commit:** xem `SCORING.md` (code/trace sớm; report có thể muộn hơn nếu được phép).  
> Phải có **run_id**, **đường dẫn artifact**, và **bằng chứng before/after** (CSV eval hoặc screenshot).

---

## 1. Pipeline tổng quan (150–200 từ)

> Nguồn raw là gì (CSV mẫu / export thật)? Chuỗi lệnh chạy end-to-end? `run_id` lấy ở đâu trong log?

**Tóm tắt luồng:**

Hệ thống Pipeline của nhóm thực hiện trích xuất dữ liệu (Ingestion) từ các tệp CSV thô chứa thông tin chính sách nội bộ (HR, SLA, Hoàn tiền). Dữ liệu thô đi qua module làm sạch (cleaning_rules.py), tại đây các bản ghi bị lỗi font (Mojibake), thiếu nguyên âm, hoặc chứa chính sách cũ sẽ bị chặn lại và đẩy vào vùng cách ly (quarantine.csv). Các bản ghi vượt qua hàng rào kiểm tra (expectations.py) sẽ được băm mã SHA-256 (Stable Chunk ID) để đảm bảo tính Idempotency và cuối cùng được nạp (upsert) vào Vector Database (ChromaDB) thông qua collection day10_kb.

Trong phiên chạy thực tế mang mã run_id=good-run-2, hệ thống đã tiếp nhận 22 raw_records, làm sạch và nạp thành công 9 cleaned_records, đồng thời cách ly 13 quarantine_records (tỷ lệ rác ~59%). 

**Lệnh chạy một dòng (copy từ README thực tế của nhóm):**

python etl_pipeline.py run --run-id good-run-2

---

## 2. Cleaning & expectation (150–200 từ)

> Baseline đã có nhiều rule (allowlist, ngày ISO, HR stale, refund, dedupe…). Nhóm thêm **≥3 rule mới** + **≥2 expectation mới**. Khai báo expectation nào **halt**.

### 2a. Bảng metric_impact (bắt buộc — chống trivial)

| Rule / Expectation mới (tên ngắn) | Trước (số liệu) | Sau / khi inject (số liệu) | Chứng cứ (log / CSV / commit) |
|-----------------------------------|------------------|-----------------------------|-------------------------------|
| Rule: Lọc Mojibake & Encoding lỗi | 0 quarantine | Đẩy 13 bản ghi lỗi định dạng vào Quarantine | quarantine_good-run-2.csv|
| Rule: Update Stale Refund Policy| hits_forbidden: true (14 ngày) | hits_forbidden: false (Sửa thành 7 ngày) | artifacts/eval/grading_run.jsonl |
| Exp: effective_date_iso_yyyy_mm_dd (Halt) | Chấp nhận mọi định dạng ngày | dạng ngày	Chặn đứng pipeline nếu ngày không chuẩn ISO | run_good-run-2.log |
| Exp: refund_no_stale_14d_window (Halt) | Lọt thông tin 14 ngày vào DB | violations=0, chặn mọi chunk chứa 14 ngày | run_good-run-2.log |


**Rule chính (baseline + mở rộng):**
Nhóm bổ sung 3 rule làm sạch mới:

encoding_mojibake_error: Phát hiện và loại bỏ các ký tự hỏng do sai chuẩn UTF-8.

broken_text_missing_vowels: Loại bỏ text teencode, rụng nguyên âm (vd: "kh", "cc thit b").

stale_refund_window_update: Tự động tìm chuỗi "14 ngày làm việc" và thay thế bằng "7 ngày làm việc", gắn tag [cleaned: stale_refund_window].
- …

**Ví dụ 1 lần expectation fail (nếu có) và cách xử lý:**

Khi kiểm thử với tệp dữ liệu thô ban đầu, expectation[effective_date_iso_yyyy_mm_dd] báo FAIL và kích hoạt chế độ HALT do một số bản ghi dùng định dạng DD/MM/YYYY. Nhóm xử lý bằng cách viết thêm hàm _normalize_effective_date trong module cleaning để tự động convert sang chuẩn ISO trước khi đưa qua chốt chặn expectation.

---

## 3. Before / after ảnh hưởng retrieval hoặc agent (200–250 từ)

> Bắt buộc: inject corruption (Sprint 3) — mô tả + dẫn `artifacts/eval/…` hoặc log.

**Kịch bản inject:**

Nhóm tiến hành kiểm thử đánh giá Retrieval bằng tập câu hỏi grading_questions.json để đo lường khả năng Agent phản hồi lại các chính sách nhạy cảm về thời gian (Hoàn tiền và Nghỉ phép). Kịch bản bao gồm việc cố tình để lẫn lộn các chunk dữ liệu chính sách hoàn tiền version cũ (14 ngày) với version mới (7 ngày) trong đầu vào.

**Kết quả định lượng (từ CSV / bảng):**

Trước khi áp dụng Data Pipeline mới, hệ thống truy xuất thường xuyên gọi nhầm chunk dữ liệu cũ, khiến Agent trả lời sai chính sách. Sau khi chạy good-run-2, kết quả đánh giá (trích xuất trực tiếp từ artifacts/eval/grading_run.jsonl) cho thấy sự cải thiện tuyệt đối

Câu hỏi gq_d10_01 (Chính sách hoàn tiền): Đạt contains_expected: true (7 ngày) và hits_forbidden: false. Chứng tỏ expectation chặn 14 ngày đã hoạt động hiệu quả 100%.

Câu hỏi gq_d10_03 (Chính sách HR 2026): Đạt top1_doc_matches: true. Hệ thống không chỉ tìm thấy câu trả lời mà còn ưu tiên xếp hạng văn bản năm 2026 lên vị trí Top 1 thay vì các phiên bản cũ hơn

## 4. Freshness & monitoring (100–150 từ)

> SLA bạn chọn, ý nghĩa PASS/WARN/FAIL trên manifest mẫu.

Nhóm thiết lập chỉ số SLA (Service Level Agreement) cho độ tươi của dữ liệu là 24.0 giờ. Tại cuối pipeline, module check_manifest_freshness sẽ quét tệp manifest để so sánh latest_exported_at với thời gian thực chạy batch.

Trong phiên good-run-2, hệ thống giám sát ghi nhận kết quả:
FAIL {"latest_exported_at": "2026-04-10T08:00:00", "age_hours": 121.178, "sla_hours": 24.0, "reason": "freshness_sla_exceeded"}

Quyết định của nhóm là cấu hình lỗi Freshness này ở mức Cảnh báo (Monitoring FAIL) thay vì Dừng hệ thống (Pipeline HALT). Dữ liệu dù cũ (trễ 121 giờ) vẫn được nạp vào Vector DB để đảm bảo tính sẵn sàng (Availability) cho Agent trả lời người dùng, nhưng sẽ kích hoạt cờ cảnh báo cho đội ngũ Data Engineer đi điều tra nguồn cấp dữ liệu gốc.

---

## 5. Liên hệ Day 09 (50–100 từ)

> Dữ liệu sau embed có phục vụ lại multi-agent Day 09 không? Nếu có, mô tả tích hợp; nếu không, giải thích vì sao tách collection.

Collection day10_kb sinh ra từ pipeline này được thiết kế theo cấu trúc module để phục vụ trực tiếp cho hệ thống Agentic Workflows đã xây dựng ở Day 09. Thay vì agent phải đọc file tĩnh, giờ đây Retrieval Agent có thể query trực tiếp vào ChromaDB để lấy ngữ cảnh (context) mới nhất, sạch nhất để thực hiện các luồng điều phối thông tin như gửi Email, Zalo (ví dụ: thông báo chính sách hoàn tiền chuẩn 7 ngày cho khách hàng).

---

## 6. Rủi ro còn lại & việc chưa làm

Chưa có Alerting tự động: Hiện tại freshness_check báo FAIL mới chỉ lưu vào log và manifest. Nhóm cần tích hợp Webhook để bắn cảnh báo tức thời lên Discord/Slack.

Hard-code cutoff date: Việc chặn phiên bản cũ đang dựa trên việc tìm kiếm chuỗi cụ thể hoặc hard-code. Cần cải tiến đọc cutoff date từ cấu hình môi trường hoặc hợp đồng dữ liệu (Data Contract).
