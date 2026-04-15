# Kiến trúc pipeline — Lab Day 10

**Nhóm:** C401 - F1  
**Cập nhật:** 15/04/2026

---

## 1. Sơ đồ luồng (bắt buộc có 1 diagram: Mermaid / ASCII)

```
raw export (`data/raw/policy_export_dirty.csv`)
→ clean (`transform/cleaning_rules.py`)
→ validate (`quality/expectations.py`)
→ cleaned CSV + quarantine CSV
→ embed to Chroma collection `day10_kb`
→ serving / retrieval for Day 08–09

run_id được ghi trong log và manifest (`good-run-1`).
freshness được đo sau khi ghi manifest, dựa trên `latest_exported_at`.
quarantine được ghi ra `artifacts/quarantine/quarantine_good-run-1.csv`.
```

> Vẽ thêm: điểm đo **freshness**, chỗ ghi **run_id**, và file **quarantine**.

---

## 2. Ranh giới trách nhiệm

| Thành phần | Input                                                              | Output                                                                                                                                                                       | Owner nhóm               |
| ---------- | ------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------ |
| Ingest     | `data/raw/policy_export_dirty.csv`                                 | 10 raw records để đưa vào bước clean                                                                                                                                         | Ingestion Owner          |
| Transform  | 10 raw records từ file export                                      | `artifacts/cleaned/cleaned_good-run-1.csv` với 6 cleaned records và `artifacts/quarantine/quarantine_good-run-1.csv` với 4 quarantine records                                | Cleaning & Quality Owner |
| Quality    | 6 cleaned records sau bước transform                               | Expectation pass: `min_one_row`, `no_empty_doc_id`, `refund_no_stale_14d_window`, `effective_date_iso_yyyy_mm_dd`, `hr_leave_no_stale_10d_annual`; warn `chunk_min_length_8` | Cleaning & Quality Owner |
| Embed      | `artifacts/cleaned/cleaned_good-run-1.csv`                         | 6 chunks được upsert vào Chroma collection `day10_kb`, metadata gồm `doc_id`, `effective_date`, `run_id`                                                                     | Embed Owners             |
| Monitor    | log run và manifest `artifacts/manifests/manifest_good-run-1.json` | freshness result = FAIL vì `latest_exported_at = 2026-04-10T08:00:00`, age = 117.251 giờ, SLA = 24 giờ                                                                       | Monitoring / Docs Owner  |

---

## 3. Idempotency & rerun

> Mô tả: upsert theo `chunk_id` hay strategy khác? Rerun 2 lần có duplicate vector không?

> Pipeline embed dùng `chunk_id` để upsert vào Chroma, nên khi chạy lại sẽ cập nhật lại chunk hiện tại thay vì tạo vector mới bị trùng. Ở run `good-run-1`, log ghi `embed_upsert count=6 collection=day10_kb`, nghĩa là 6 cleaned chunks đã được publish vào collection. Trước khi upsert, pipeline còn lấy danh sách id cũ trong collection và xóa các id không còn xuất hiện trong cleaned run hiện tại, nên index được giữ đồng bộ với snapshot mới nhất thay vì giữ lại vector stale từ run cũ. Cách này giúp rerun an toàn và hạn chế việc retrieval trả về chunk cũ mà đã bị loại khỏi cleaned data.

---

## 4. Liên hệ Day 09

> Pipeline này cung cấp / làm mới corpus cho retrieval trong `day09/lab` như thế nào? (cùng `data/docs/` hay export riêng?)

---

## 5. Rủi ro đã biết

- Nếu collection đã có vector cũ từ run trước và không prune đúng, retrieval có thể vẫn lấy nhầm chunk stale.
- …
