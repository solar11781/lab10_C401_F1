# Quality report — Lab Day 10 (nhóm)

**run_id:** good-run-2 / inject-bad  
**Ngày:** 15/04/2026

---

## 1. Tóm tắt số liệu

| Chỉ số             | Trước | Sau | Ghi chú                                                                                                      |
| ------------------ | ----- | --- | ------------------------------------------------------------------------------------------------------------ |
| raw_records        | 22    | 22  | `manifest_good-run-2.json` và `manifest_inject-bad.json` đều ghi 22                                          |
| cleaned_records    | 9     | 9   | `manifest_good-run-2.json` và `manifest_inject-bad.json` đều ghi 9                                           |
| quarantine_records | 13    | 13  | `manifest_good-run-2.json` và `manifest_inject-bad.json` đều ghi 13                                          |
| Expectation halt?  | Không | Có  | `run_good-run-2.log` ghi toàn bộ expectation đều `OK`; `manifest_inject-bad.json` có `skipped_validate=true` |

---

## 2. Before / after retrieval (bắt buộc)

> Đính kèm hoặc dẫn link tới `artifacts/eval/before_after_eval.csv` (hoặc 2 file before/after).

**Câu hỏi then chốt:** refund window (`q_refund_window`)  
**Trước:** `before_after_eval.csv` → `question_id=q_refund_window`, `top1_doc_id=policy_refund_v4`, `contains_expected=yes`, `hits_forbidden=yes`, `top_k_used=3`, `top1_preview="Yêu cầu được gửi trong vòng 7 ngày làm việc kể từ thời điểm xác nhận đơn hàng."`  
**Sau:** `after_inject_bad.csv` → `question_id=q_refund_window`, `top1_doc_id=policy_refund_v4`, `contains_expected=yes`, `hits_forbidden=no`, `top_k_used=3`, `top1_preview="Yêu cầu được gửi trong vòng 7 ngày làm việc kể từ thời điểm xác nhận đơn hàng."`

**Merit (khuyến nghị):** versioning HR — `q_leave_version` (`contains_expected`, `hits_forbidden`, cột `top1_doc_expected`)

**Trước:** `before_after_eval.csv` → `question_id=q_leave_version`, `top1_doc_id=hr_leave_policy`, `contains_expected=yes`, `hits_forbidden=no`, `top1_doc_expected=yes`, `top_k_used=3`, `top1_preview="Nhân viên dưới 3 năm kinh nghiệm được 12 ngày phép năm theo chính sách 2026."`  
**Sau:** `after_inject_bad.csv` → `question_id=q_leave_version`, `top1_doc_id=hr_leave_policy`, `contains_expected=yes`, `hits_forbidden=no`, `top1_doc_expected=yes`, `top_k_used=3`, `top1_preview="Nhân viên dưới 3 năm kinh nghiệm được 12 ngày phép năm theo chính sách 2026."`

---

## 3. Freshness & monitor

Kết quả quan sát được trong `run_good-run-1.log` và `run_good-run-2.log` là `freshness_check=FAIL` với `latest_exported_at="2026-04-10T08:00:00"` và `sla_hours=24.0`. Ở `run_good-run-2.log`, `age_hours=121.178`, nên dữ liệu vượt SLA 24 giờ. Theo `freshness_check.py`, kiểm tra này đọc `latest_exported_at` từ manifest; nếu không có mới fallback sang `run_timestamp`. Với artifact hiện có, `manifest_good-run-2.json` cũng ghi `latest_exported_at="2026-04-10T08:00:00"`, nên kết quả `FAIL` là nhất quán với SLA 24 giờ.

---

## 4. Corruption inject (Sprint 3)

Inject được thực hiện bằng lệnh `python etl_pipeline.py run --run-id inject-bad --no-refund-fix --skip-validate`. Trong `manifest_inject-bad.json`, hai flags `no_refund_fix=true` và `skipped_validate=true` cho thấy run này cố ý bỏ fix refund và vẫn tiếp tục embed dù expectation halt. So sánh `cleaned_inject-bad.csv` với `cleaned_good-run-2.csv` cho thấy ở bản inject, một chunk `policy_refund_v4` vẫn còn câu `"14 ngày làm việc"`, còn ở `cleaned_good-run-2.csv` câu đó đã được đổi thành `"7 ngày làm việc"` và có thêm marker `[cleaned: stale_refund_window]`. Cách phát hiện trong artifact hiện có là đối chiếu `manifest_inject-bad.json`, hai file cleaned CSV, và hai file eval `before_after_eval.csv` / `after_inject_bad.csv`.

---

## 5. Hạn chế & việc chưa làm

- `freshness_check` vẫn đang `FAIL` với SLA 24 giờ.
- Hai file eval đính kèm cho `q_refund_window` cho kết quả khác nhau (`hits_forbidden=yes` ở `before_after_eval.csv`, `hits_forbidden=no` ở `after_inject_bad.csv`); từ các artifact hiện có chỉ có thể ghi nhận kết quả, chưa đủ để kết luận nguyên nhân.
