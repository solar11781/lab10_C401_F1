# Báo cáo cá nhân — mẫu GV (reference)

**Họ và tên:** Mạc Phương Nga
**Vai trò:** Cleaning 
**Độ dài:** ~450 từ (mẫu)

---

## 1. Phụ trách

Tôi triển khai `transform/cleaning_rules.py` (rule 7–9). Mục tiêu là biến dữ liệu thô thành một tập tài liệu sạch, chuẩn xác và an toàn để phục vụ hệ thống RAG phía sau.

**Bằng chứng:** commit/file trong repo reference `day10-lab-transformer`.

---

## 2. Quyết định kỹ thuật

**Version Cutoff:** Thay vì ghi cứng mốc thời gian cắt bỏ hoặc dùng legacy filter chung chung, tôi quyết định quét file CSV qua 2 vòng. Vòng 1 quét để tìm `effective_date` mới nhất của từng tài liệu (`doc_id`). Vòng 2 dùng chính mốc ngày đó để loại bỏ các phiên bản cũ (`stale_document_version`).
**Đeuplication dựa trên Hash:** Để loại bỏ dòng trùng lặp, tôi không so sánh chuỗi (string) trực tiếp. Tôi chuẩn hóa văn bản (NFC Unicode, loại bỏ khoảng trắng ẩn, đổi dấu ngoặc kép) sau đó băm thành mã MD5. Cách này xử lý triệt để các dòng nhìn bằng mắt thường thì giống nhau nhưng khác biệt về mã ký tự ẩn, giúp hệ thống VectorDB không bị lưu rác.
**Quanrantine:** Nếu văn bản trống rỗng hoặc là rác IT Log -> Tôi cho Drop (loại bỏ hoàn toàn). Nhưng nếu văn bản hợp lệ mà file nguồn bị thiếu `effective_date` -> Tôi gán cờ `review_missing_date` và đẩy vào file Quarantine thay vì xóa bỏ. Quyết định này giúp bảo toàn tri thức nghiệp vụ để SME (Chuyên gia) có thể vào xác nhận lại sau.
---

## 3. Sự cố / anomaly

**Phát hiện:** Trong quá trình test với các bộ dữ liệu dị thường, tôi nhận thấy các rule chuẩn hóa thời gian về dạng `YYYY-MM-DD` chưa kiểm tra tính valid của nó.
**Khắc phục:** Tôi tích hợp thư viện `datetime` và sử dụng hàm `strptime()` bọc trong khối `try...except` ValueError để ép hệ thống đối chiếu với lịch thực tế. Nếu ngày vô lý, mã lỗi phân tách `invalid_effective_date` sẽ được kích hoạt để phân biệt với lỗi định dạng.

---

## 4. Before/after

**Log:** `expectation[refund_no_stale_14d_window] OK (halt)` sau run chuẩn; trước đó với `--no-refund-fix` expectation FAIL.

**CSV:** dòng `q_refund_window` có `hits_forbidden=no` trong `artifacts/eval/after_inject_bad.csv`.

---

## 5. Cải tiến thêm 2 giờ

Bổ sung metadata ghi lại dòng số mấy (row index) trong file CSV gốc đã tạo ra chunk bị lỗi, giúp Data Engineer truy vết và báo cáo lỗi cho nguồn dữ liệu dễ dàng hơn.
