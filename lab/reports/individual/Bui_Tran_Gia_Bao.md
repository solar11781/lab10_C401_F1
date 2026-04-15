# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Bùi Trần Gia Bảo  
**Vai trò:** Ingestion / Cleaning / Embed / Monitoring — Embed Owner 1  
**Ngày nộp:** 15/04/2026  
**Độ dài yêu cầu:** **400–650 từ** (ngắn hơn Day 09 vì rubric slide cá nhân ~10% — vẫn phải đủ bằng chứng)

---

> Viết **"tôi"**, đính kèm **run_id**, **tên file**, **đoạn log** hoặc **dòng CSV** thật.  
> Nếu làm phần clean/expectation: nêu **một số liệu thay đổi** (vd `quarantine_records`, `hits_forbidden`, `top1_doc_expected`) khớp bảng `metric_impact` của nhóm.  
> Lưu: `reports/individual/[ten_ban].md`

---

## 1. Tôi phụ trách phần nào? (80–120 từ)

**File / module:**

- `etl_pipeline.py`
- `eval_retrieval.py`
- `grading_run.py`
- `artifacts/eval/grading_run.jsonl`
- `artifacts/cleaned/cleaned_good-run-1.csv`
- `artifacts/cleaned/cleaned_good-run-2.csv`
- `artifacts/logs/run_good-run-1.log`
- `artifacts/logs/run_good-run-2.log`
- `artifacts/manifests/manifest_good-run-1.json`
- `artifacts/manifests/manifest_good-run-2.json`
- `artifacts/quarantine/quarantine_good-run-1.csv`
- `artifacts/quarantine/quarantine_good-run-2.csv`
- `docs/pipeline_architecture.md`
- `docs/quality_report.md`

**Kết nối với thành viên khác:**

> Tôi là **Embed Owner 1** và phụ trách phần kiểm tra để chạy pipeline tốt (`good-run-1`, `good-run-2`), kiểm tra log và manifest, xác nhận collection `day10_kb` được cập nhật đúng, và mô tả chiến lược idempotency trong `docs/pipeline_architecture.md`. Công việc của tôi nhận đầu vào từ nhóm Cleaning / Quality sau khi dữ liệu đã đi qua `clean_rows(...)` và `run_expectations(...)`. Sau đó tôi bàn giao collection đã publish, manifest và log cho Embed Owner 2 để bạn đó chạy eval before/after và cùng làm quality report.

---

**Bằng chứng (commit / comment trong code):**

> Commit hash: edbe820a9577301300f2d1bcfb65fbf31c2760ad, 90ac6168294cb1d2b4cf79e4332c7e65269480f9, 559a6e71c8a844ec8706f9823340a171fed4cb74,a1d6c7eeb915ad289edb0d51d8d8adb13f14411d,e23809e21ab0eb84148390c9ef1f12da4948a89d,2a37d81aeb0e9a299582d52ee640fb10f9947cd9

---

---

## 2. Một quyết định kỹ thuật (100–150 từ)

> Quyết định kỹ thuật quan trọng nhất ở phần tôi phụ trách là giữ chiến lược embed theo kiểu **snapshot publish** thay vì append dữ liệu mới một cách mù. Trong `etl_pipeline.py`, bước embed lấy `chunk_id` từ cleaned CSV làm ID ổn định, sau đó `upsert` vào Chroma. Trước khi upsert, code còn đọc các ID hiện có trong collection và xóa những ID không còn nằm trong cleaned run hiện tại (`prev_ids - set(ids)`). Tôi chọn cách giải thích và giữ chiến lược này vì nó phù hợp trực tiếp với tiêu chí chấm idempotency: rerun phải không làm “phình” index và không giữ vector cũ sau publish. Ở `run_good-run-2.log`, pipeline ghi `embed_upsert count=9 collection=day10_kb`, còn manifest ghi `chroma_collection: "day10_kb"`, nên tôi có thể nối rõ từ cleaned CSV sang collection thực tế.

---

---

## 3. Một lỗi hoặc anomaly đã xử lý (100–150 từ)

> Anomaly rõ nhất mà tôi xử lý ở vai trò Embed Owner 1 là **freshness_check bị FAIL** dù pipeline vẫn kết thúc `PIPELINE_OK`. Triệu chứng xuất hiện ở `run_good-run-2.log`: `freshness_check=FAIL {"latest_exported_at": "2026-04-10T08:00:00", "age_hours": 121.178, "sla_hours": 24.0, "reason": "freshness_sla_exceeded"}`. Metric/check phát hiện là chính dòng freshness trong log và field `latest_exported_at` trong `manifest_good-run-2.json`. Tôi không tự ý sửa timestamp vì như vậy sẽ làm sai artifact. Thay vào đó, tôi xử lý theo hướng kỹ thuật đúng hơn: đọc lại `etl_pipeline.py` và `freshness_check.py` để xác nhận logic hiện tại ưu tiên `latest_exported_at` trong manifest, chỉ fallback sang `run_timestamp` khi thiếu timestamp export. Từ đó tôi ghi rõ trong doc rằng SLA đang đo độ mới của **data snapshot/export**, không phải chỉ thời điểm publish.

---

---

## 4. Bằng chứng trước / sau (80–120 từ)

> Bằng chứng before/after tôi dùng là hai dòng từ file eval. Ở `before_after_eval.csv`, dòng `q_refund_window` có `top1_doc_id=policy_refund_v4`, `contains_expected=yes`, nhưng `hits_forbidden=yes`. Ở `after_inject_bad.csv`, cùng câu hỏi đó vẫn có `top1_doc_id=policy_refund_v4`, `contains_expected=yes`, nhưng `hits_forbidden=no`. Với `q_leave_version`, cả hai file đều cho `top1_doc_id=hr_leave_policy`, `contains_expected=yes`, `hits_forbidden=no`, và `top1_doc_expected=yes`. Tôi đã ghi rõ hai run liên quan là `good-run-2` và `inject-bad`, nhưng với vai trò là Embed Owner 1, tôi chỉ dùng các dòng CSV này như bằng chứng before/after của hệ thống sau publish, không suy diễn thêm nguyên nhân vượt quá artifact.

---

---

## 5. Cải tiến tiếp theo (40–80 từ)

> Nếu có thêm thời gian, tôi sẽ bổ sung log đếm size collection trước và sau rerun, hoặc ít nhất log số lượng `prev_ids`, `drop`, và tổng số ID sau publish. Hiện tại idempotency được chứng minh chủ yếu qua code `upsert chunk_id + prune stale ids`. Nếu có thêm count trực tiếp trong log thì phần prove “rerun không tạo duplicate vector” sẽ mạnh hơn và dễ đánh giá hơn.

---
