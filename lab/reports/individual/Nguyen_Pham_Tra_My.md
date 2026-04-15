# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** ___________  
**Vai trò:** Ingestion / Cleaning / Embed / Monitoring — ___________  
**Ngày nộp:** ___________  
**Độ dài yêu cầu:** **400–650 từ** (ngắn hơn Day 09 vì rubric slide cá nhân ~10% — vẫn phải đủ bằng chứng)

---

> Viết **"tôi"**, đính kèm **run_id**, **tên file**, **đoạn log** hoặc **dòng CSV** thật.  
> Nếu làm phần clean/expectation: nêu **một số liệu thay đổi** (vd `quarantine_records`, `hits_forbidden`, `top1_doc_expected`) khớp bảng `metric_impact` của nhóm.  
> Lưu: `reports/individual/[ten_ban].md`

---

## 1. Tôi phụ trách phần nào? (80–120 từ)

**File / module:**

Tôi phụ trách xây dựng expectation suite trong file quality/expectations.py để kiểm tra chất lượng dữ liệu sau bước cleaning. Cụ thể, tôi triển khai các rule từ E1 đến E9 (E1-E6 của baseline, bổ sung thêm E7-E9) nhằm đảm bảo dữ liệu đạt chuẩn trước khi đi vào bước embedding. Các expectation bao gồm kiểm tra dữ liệu tối thiểu (min_one_row), tính đầy đủ (no_empty_doc_id), tính đúng đắn của policy (refund_no_stale_14d_window, hr_leave_no_stale_10d_annual), định dạng dữ liệu (effective_date_iso_yyyy_mm_dd, exported_at_iso_and_present) và chất lượng nội dung (chunk_min_length_8, chunk_text_too_long_warning, doc_id_allowed_set_warning).


**Kết nối với thành viên khác:**


Phần của tôi nhận dữ liệu đầu vào từ cleaning_rules.py và đóng vai trò quality gate trước khi pipeline tiếp tục sang bước embed. Nếu có expectation mức halt fail, pipeline sẽ dừng ngay để tránh đưa dữ liệu sai vào hệ thống.
**Bằng chứng (commit / comment trong code):**

    # E1: có ít nhất 1 dòng sau clean
    ok = len(cleaned_rows) >= 1
    results.append(
        ExpectationResult(
            "min_one_row",
            ok,
            "halt",
            f"cleaned_rows={len(cleaned_rows)}",
        )
    )

    # E2: không doc_id rỗng
    bad_doc = [r for r in cleaned_rows if not (r.get("doc_id") or "").strip()]
    ok2 = len(bad_doc) == 0
    results.append(
        ExpectationResult(
            "no_empty_doc_id",
            ok2,
            "halt",
            f"empty_doc_id_count={len(bad_doc)}",
        )
    )

    # E3: policy refund không được chứa cửa sổ sai 14 ngày (sau khi đã fix)
    bad_refund = [
        r
        for r in cleaned_rows
        if r.get("doc_id") == "policy_refund_v4"
        and "14 ngày làm việc" in (r.get("chunk_text") or "")
    ]
    ok3 = len(bad_refund) == 0
    results.append(
        ExpectationResult(
            "refund_no_stale_14d_window",
            ok3,
            "halt",
            f"violations={len(bad_refund)}",
        )
    )

    # E4: chunk_text đủ dài
    short = [r for r in cleaned_rows if len((r.get("chunk_text") or "")) < 8]
    ok4 = len(short) == 0
    results.append(
        ExpectationResult(
            "chunk_min_length_8",
            ok4,
            "warn",
            f"short_chunks={len(short)}",
        )
    )

    # E5: effective_date đúng định dạng ISO sau clean (phát hiện parser lỏng)
    iso_bad = [
        r
        for r in cleaned_rows
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", (r.get("effective_date") or "").strip())
    ]
    ok5 = len(iso_bad) == 0
    results.append(
        ExpectationResult(
            "effective_date_iso_yyyy_mm_dd",
            ok5,
            "halt",
            f"non_iso_rows={len(iso_bad)}",
        )
    )

    # E6: không còn marker phép năm cũ 10 ngày trên doc HR (conflict version sau clean)
    bad_hr_annual = [
        r
        for r in cleaned_rows
        if r.get("doc_id") == "hr_leave_policy"
        and "10 ngày phép năm" in (r.get("chunk_text") or "")
    ]
    ok6 = len(bad_hr_annual) == 0
    results.append(
        ExpectationResult(
            "hr_leave_no_stale_10d_annual",
            ok6,
            "halt",
            f"violations={len(bad_hr_annual)}",
        )
    )


    # E7: exported_at phải có và đúng định dạng ISO datetime
    bad_exported_at = []
    for r in cleaned_rows:
        val = (r.get("exported_at") or "").strip()
        try:
            # hỗ trợ dạng có Z
            from datetime import datetime
            datetime.fromisoformat(val.replace("Z", "+00:00"))
        except Exception:
            bad_exported_at.append(r)

    ok9 = len(bad_exported_at) == 0
    results.append(
        ExpectationResult(
            "exported_at_iso_and_present",
            ok9,
            "halt",
            f"bad_exported_at_rows={len(bad_exported_at)}",
        )
    )

    # E8: chunk_text quá dài (cảnh báo)
    max_len = 200  # bạn có thể chỉnh

    too_long = [
        r for r in cleaned_rows
        if len((r.get("chunk_text") or "")) > max_len
    ]

    ok11 = len(too_long) == 0
    results.append(
        ExpectationResult(
            "chunk_text_too_long_warning",
            ok11,
            "warn",
            f"too_long_chunks={len(too_long)}, max_len={max_len}",
        )
    )
    # E9: doc_id phải nằm trong allowlist (cảnh báo)
    allowed_doc_ids = {
        "policy_refund_v4",
        "sla_p1_2026",
        "it_helpdesk_faq",
        "hr_leave_policy",
    }
    
    unknown = [
        r for r in cleaned_rows
        if (r.get("doc_id") or "").strip() not in allowed_doc_ids
    ]
    
    ok13 = len(unknown) == 0
    results.append(
        ExpectationResult(
            "doc_id_allowed_set_warning",
            ok13,
            "warn",
            f"unknown_doc_ids={len(unknown)}",
        )
    )
---

## 2. Một quyết định kỹ thuật (100–150 từ)

> VD: chọn halt vs warn, chiến lược idempotency, cách đo freshness, format quarantine.

Một quyết định quan trọng là phân loại severity giữa halt và warn. Tôi thiết kế các expectation liên quan đến tính đúng đắn dữ liệu (ví dụ exported_at_iso_and_present) ở mức halt, vì nếu timestamp sai format, các bước downstream như manifest hoặc freshness check sẽ không hoạt động đúng. Điều này có thể dẫn đến sai lệch trong toàn bộ pipeline, nên cần chặn ngay.

Các expectation như chunk_text_too_long_warning và doc_id_allowed_set_warning được đặt ở mức warn. Các vấn đề này không làm pipeline lỗi ngay, nhưng có thể ảnh hưởng đến chất lượng embedding hoặc đưa dữ liệu ngoài phạm vi vào hệ thống. Việc này giúp pipeline đảm bảo sẽ không bị dừng quá sớm.
---

## 3. Một lỗi hoặc anomaly đã xử lý (100–150 từ)

> Mô tả triệu chứng → metric/check nào phát hiện → fix.

Trong quá trình TEST, tôi phát hiện một anomaly khi một dòng dữ liệu có exported_at sai format (2026/04/10 08:00:00). Expectation exported_at_iso_and_present đã phát hiện lỗi này với bad_exported_at_rows=1 và khiến pipeline dừng với trạng thái PIPELINE_HALT.

Triệu chứng là pipeline không thực hiện bước embed và không ghi manifest. Sau khi sửa lại dữ liệu về đúng định dạng ISO (2026-04-10T08:00:00), expectation pass và pipeline chạy hoàn chỉnh. Ngoài ra, tôi cũng test thêm trường hợp chunk quá dài, expectation chunk_text_too_long_warning đã cảnh báo đúng với too_long_chunks=1 nhưng không dừng pipeline, đúng với thiết kế.
---

## 4. Bằng chứng trước / sau (80–120 từ)

> Dán ngắn 2 dòng từ `before_after_eval.csv` hoặc tương đương; ghi rõ `run_id`.

Run lỗi (run_id=test-exported):

expectation[exported_at_iso_and_present] FAIL (halt) :: bad_exported_at_rows=1
expectation[chunk_text_too_long_warning] FAIL (warn) :: too_long_chunks=1
PIPELINE_HALT

Run sau khi sửa:

expectation[exported_at_iso_and_present] OK (halt) :: bad_exported_at_rows=0
expectation[chunk_text_too_long_warning] OK (warn) :: too_long_chunks=0
PIPELINE_OK

---

## 5. Cải tiến tiếp theo (40–80 từ)

> Nếu có thêm 2 giờ — một việc cụ thể (không chung chung).

Tôi muốn bổ sung thêm các expectation liên quan đến freshness để kiểm soát độ mới của dữ liệu tốt hơn.
