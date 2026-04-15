# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Lại Gia Khánh  
**Vai trò:** Ingestion / Cleaning / Embed / Monitoring — Embed
**Ngày nộp:** 15/04/2026
**Độ dài yêu cầu:** **400–650 từ** (ngắn hơn Day 09 vì rubric slide cá nhân ~10% — vẫn phải đủ bằng chứng)

---

> Viết **"tôi"**, đính kèm **run_id**, **tên file**, **đoạn log** hoặc **dòng CSV** thật.  
> Nếu làm phần clean/expectation: nêu **một số liệu thay đổi** (vd `quarantine_records`, `hits_forbidden`, `top1_doc_expected`) khớp bảng `metric_impact` của nhóm.  
> Lưu: `reports/individual/[ten_ban].md`

---

## 1. Tôi phụ trách phần nào? (80–120 từ)

**File / module:**

- `eval_retrieval.py`
- `grading_run.py`
- `etl_pipeline.py`
- `artifacts/cleaned/cleaned_inject-bad.csv`
- `artifacts/eval/before_after_eval.csv`
- `artifacts/eval/after_inject_bad.csv`
- `artifacts/eval/grading_run.jsonl`
- `artifacts/logs/run_inject-bad.log1`
- `artifacts/manifests/manifest_inject-bad.json`
- `artifacts/quarantine/quarantine_inject-bad.csv`
- `docs/pipeline_architecture.md`
- `docs/quality_report.md`

**Kết nối với thành viên khác:**

Tôi là **Embed Owner 2** và phụ trách phần chứng minh retrieval thay đổi sau publish. Sau khi Embed Owner 1 bàn giao run tốt `good-run-2` cùng manifest/log của collection `day10_kb`, tôi chạy `python eval_retrieval.py --out artifacts/eval/before_after_eval.csv`, sau đó chạy inject bằng `python etl_pipeline.py run --run-id inject-bad --no-refund-fix --skip-validate` và tiếp tục tạo `after_inject_bad.csv`. Từ hai file eval này, tôi kiểm tra `q_refund_window` và `q_leave_version`, rồi hỗ trợ hoàn thành `docs/quality_report.md` và phần retrieval/evidence trong `reports/group_report.md`. Tôi không lặp lại phần publish/idempotency của Embed Owner 1 mà nối trực tiếp từ artifact bạn ấy bàn giao sang evidence eval của tôi.

---

**Bằng chứng (commit / comment trong code):**

---
- https://github.com/solar11781/lab10_C401_F1/commit/1ddfff2a517413ce98cac234e1f9151161da8c75
- https://github.com/solar11781/lab10_C401_F1/commit/0cfb55259663563a9a97c0d7f6e2d085648fbefe
---

## 2. Một quyết định kỹ thuật (100–150 từ)

> Quyết định kỹ thuật quan trọng nhất ở phần tôi phụ trách là **không đánh giá retrieval chỉ bằng top-1 preview**, mà giữ thêm check `hits_forbidden` trên **toàn bộ top-k**. Trong `eval_retrieval.py`, hệ thống ghép tất cả chunk top-k thành một `blob` rồi mới kiểm tra `must_contain_any` và `must_not_contain`, nên một câu trả lời nhìn đúng ở top-1 vẫn có thể bị xem là chưa an toàn nếu trong top-k còn context stale. Tôi giữ cách đọc này vì README cũng nhấn mạnh `hits_forbidden` là tín hiệu observability quan trọng, đặc biệt cho `q_refund_window`. Với `q_leave_version`, tôi còn giữ thêm cột `top1_doc_expected` vì file câu hỏi yêu cầu top-1 nên đến từ `hr_leave_policy`. Nhờ vậy, phần evidence của tôi bám đúng cả hai lớp kiểm tra: nội dung đúng và nguồn top-1 đúng.

---

## 3. Một lỗi hoặc anomaly đã xử lý (100–150 từ)

> Anomaly rõ nhất mà tôi xử lý là kết quả eval của câu `q_refund_window` nhìn khá khó hiểu nếu chỉ đọc lướt. Ở `before_after_eval.csv`, câu này có `contains_expected=yes` nhưng vẫn `hits_forbidden=yes`, còn ở `after_inject_bad.csv` lại có `contains_expected=yes` và `hits_forbidden=no`. Metric/check phát hiện anomaly là chính hai cột `contains_expected` và `hits_forbidden` trong CSV eval, chứ không phải chỉ `top1_preview`. Cách tôi xử lý không phải là tự suy diễn nguyên nhân ngoài artifact, mà là lần ngược lại toàn bộ chuỗi evidence: `manifest_inject-bad.json` cho thấy `no_refund_fix=true` và `skipped_validate=true`, còn `docs/quality_report.md` ghi rõ inject run được dùng để so sánh với run tốt. Fix ở phần tôi phụ trách là chuẩn hóa cách đọc evidence và ghi lại trung thực trong quality report thay vì kết luận vượt quá những gì file đang chứng minh.

---

## 4. Bằng chứng trước / sau (80–120 từ)

> Bằng chứng before/after tôi dùng là hai dòng eval gắn với `good-run-2` và `inject-bad`. Với `q_refund_window`, ở `before_after_eval.csv` hệ thống trả `top1_doc_id=policy_refund_v4`, `contains_expected=yes`, nhưng `hits_forbidden=yes`; còn ở `after_inject_bad.csv`, cùng câu hỏi vẫn có `top1_doc_id=policy_refund_v4`, `contains_expected=yes`, nhưng `hits_forbidden=no`. Với `q_leave_version`, cả hai file đều cho `top1_doc_id=hr_leave_policy`, `contains_expected=yes`, `hits_forbidden=no`, và `top1_doc_expected=yes`. Tôi dùng đúng hai dòng này vì SCORING yêu cầu evidence before/after có ít nhất hai dòng CSV, và quality report của nhóm cũng đang diễn giải chính hai câu hỏi đó làm trọng tâm.

---

## 5. Cải tiến tiếp theo (40–80 từ)

> Nếu có thêm 2 giờ, tôi sẽ sửa `eval_retrieval.py` để ghi thêm cột `scenario` hoặc `run_id` trực tiếp vào CSV output. Hiện tại tôi phải so sánh thủ công giữa `before_after_eval.csv` và `after_inject_bad.csv`, nên đọc artifact khá dễ nhầm, nhất là ở `q_refund_window`. Một cột scenario cố định sẽ làm phần before/after và group report rõ hơn nhiều.

---
