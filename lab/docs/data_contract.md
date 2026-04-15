# Data contract — Lab Day 10

> Bắt đầu từ `contracts/data_contract.yaml` — mở rộng và đồng bộ file này.

---

## 1. Nguồn dữ liệu (source map)

| Nguồn | Phương thức ingest | Failure mode chính | Metric / alert |
|-------|-------------------|-------------------|----------------|
| data/docs/policy_refund_v4.txt | Text Export | Lỗi sót policy cũ (cửa sổ 14 ngày), sai định dạng ngày tháng, quá hạn min_effective_date | SLA: 24h |
| data/docs/sla_p1_2026.txt | Text Export | Version tài liệu cũ hơn version mới nhất trong batch, thiếu effective_date. | SLA: 24h |
| data/docs/it_helpdesk_faq.txt | Text Export | Chứa IT log dump (ký tự đặc biệt > 25%), chuỗi vô nghĩa/keysmash, dữ liệu test rác. | SLA: 24h |
| data/docs/hr_leave_policy.txt | Text Export | Cũ hơn 01/01/2026, lỗi hiển thị font (Mojibake), rụng nguyên âm. | SLA: 24h |

---

## 2. Schema cleaned

| Cột | Kiểu | Bắt buộc | Ghi chú |
|-----|------|----------|---------|
| chunk_id | string | Có | ID ổn định sau clean (thường là hash hoặc doc_id + seq). |
| doc_id | string | Có | Khóa logic tài liệu. Phải nằm trong danh sách allowed_doc_ids (policy_refund_v4, sla_p1_2026, it_helpdesk_faq, hr_leave_policy). |
| chunk_text | string | Có | Nội dung văn bản thực tế. Độ dài tối thiểu (min_length): 8 ký tự. |
| effective_date | date | Có | Phải đúng định dạng chuẩn (YYYY-MM-DD / DD/MM/YYYY) và là một ngày có thực |
| exported_at | datetime | Có | Timestamp thời điểm xuất dữ liệu từ nguồn. |

---

## 3. Quy tắc quarantine vs drop

Record bị flag được đẩy vào phân vùng lưu trữ cách ly (Quarantine).

Owner của dataset là người chịu trách nhiệm cuối cùng. Họ sẽ review các record bị giữ lại và quyết định:

    Drop (Loại bỏ): Nếu xác nhận đó là dữ liệu rác thực sự.

    Merge lại (Tái ingest): Nếu đó là lỗi false-positive (nhận diện nhầm) hoặc sau khi team Helpdesk đã cập nhật lại file text nguồn cho chuẩn xác.

---

## 4. Phiên bản & canonical

> Source of truth cho policy refund: Source of truth là file data/docs/policy_refund_v4.txt (ứng với doc_id: policy_refund_v4).
