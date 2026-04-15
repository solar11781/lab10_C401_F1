# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Lê Duy Anh
**Vai trò:** Ingestion
**Ngày nộp:** 15/04/2026
**Độ dài yêu cầu:** **400–650 từ** (ngắn hơn Day 09 vì rubric slide cá nhân ~10% — vẫn phải đủ bằng chứng)

---

## 1. Tôi phụ trách phần nào? (80–120 từ)

Tôi triển khai `data/raw/policy_export_dirty.csv` (line 11-22) và `contracts/data_contract.yaml`. Kết nối với cleaning owner để triển khai file `transform/cleaning_rules.py`.

**Bằng chứng (commit / comment trong code):** commit/file trong repo reference `lab10_C401_F1`.

_________________

---

## 2. Một quyết định kỹ thuật (100–150 từ)

**Halt vs warn:** `effective_date` sai format (chỉ nhận YYYY-MM-DD, DD/MM/YYYY) hoặc value vô lý (vd: 32/13/2026) → halt + quarantine (không để vào cleaned) thay vì warn, vì sai mốc thời gian sẽ phá vỡ hoàn toàn logic áp dụng policy/tính toán downstream.

_________________

---

## 3. Một lỗi hoặc anomaly đã xử lý (100–150 từ)

**Phát hiện:** Trong quá trình test với các bộ dữ liệu dị thường (Anomaly), tôi nhận thấy các rule giới hạn độ dài thông thường đã bỏ lọt một loại rác nguy hiểm cho LLM: Lỗi sai bảng mã (Mojibake): `ChÃnh sÃ¡ch nghá»‰ phÃ©p nÄƒ`
**Khắc phục:** Tôi đã tự viết thêm các Heuristic Regex Rules (Luật suy diễn) đặc trị ngay trong Vòng 2 của code: Quét dải ký tự Latin-1 đặc trưng của Mojibake (Ã, Ä, Å). Nhờ đó, toàn bộ dữ liệu "ảo" đã bị tóm gọn vào file `quarantine.csv`.

_________________

---

## 4. Bằng chứng trước / sau (80–120 từ)

**Log:** `expectation[refund_no_stale_14d_window] OK (halt)` sau run chuẩn; trước đó với `--no-refund-fix` expectation FAIL.

**CSV:** dòng `q_refund_window` có `hits_forbidden=no` trong `artifacts/eval/after_inject_bad.csv`.
_________________

---

## 5. Cải tiến tiếp theo (40–80 từ)

Đọc cấu hình SLA freshness linh hoạt (ngưỡng warn/halt, khung giờ) từ `contracts/data_contract.yaml` thay vì hard-code 24h như phiên bản hiện tại.
_________________
