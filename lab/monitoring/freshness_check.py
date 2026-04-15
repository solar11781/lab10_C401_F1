"""
Kiểm tra freshness từ manifest pipeline (SLA đa tầng - Multi-tier SLA).

Bản nâng cấp Distinction:
- Hỗ trợ Global SLA (kiểm tra toàn hệ thống).
- Hỗ trợ Document-Level SLA (đọc watermark của từng loại tài liệu).
- Sử dụng biến môi trường (Environment Variables) để linh hoạt cấu hình.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple


def parse_iso(ts: str) -> datetime | None:
    if not ts:
        return None
    try:
        # Cho phép "2026-04-10T08:00:00" không có timezone
        if ts.endswith("Z"):
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None

# =========================================================================
# DYNAMIC SLA CONFIGURATION (Hỗ trợ cấu hình qua Biến môi trường)
# =========================================================================
DOC_SLA_CONFIG = {
    # IT Helpdesk lỗi P1 cần được cập nhật cực nhanh (mặc định 4 giờ)
    "sla_p1_2026": float(os.getenv("SLA_P1_HOURS", 4.0)),
    # Chính sách hoàn tiền CSKH cập nhật hàng ngày (mặc định 24 giờ)
    "policy_refund_v4": float(os.getenv("SLA_REFUND_HOURS", 24.0)),
    # FAQ IT Helpdesk cập nhật 2 ngày 1 lần (mặc định 48 giờ)
    "it_helpdesk_faq": float(os.getenv("SLA_FAQ_HOURS", 48.0)),
    # Chính sách nhân sự ít thay đổi (mặc định 30 ngày = 720 giờ)
    "hr_leave_policy": float(os.getenv("SLA_HR_HOURS", 720.0)),
}


def check_manifest_freshness(
    manifest_path: Path,
    *,
    global_sla_hours: float = 24.0,
    now: datetime | None = None,
) -> Tuple[str, Dict[str, Any]]:
    """
    Trả về ("PASS" | "WARN" | "FAIL", detail dict).

    Thực hiện 2 lớp kiểm tra:
    1. Global check: Xem tổng thể batch gần nhất có chạy quá SLA chung không.
    2. Document check (Watermark): Đọc 'doc_watermarks' từ manifest để xem từng doc_id 
       có vi phạm SLA đặc thù của nó không.
    """
    now = now or datetime.now(timezone.utc)
    if not manifest_path.is_file():
        return "FAIL", {"reason": "manifest_missing", "path": str(manifest_path)}

    data: Dict[str, Any] = json.loads(manifest_path.read_text(encoding="utf-8"))
    detail = {"global": {}, "docs": {}}
    overall_status = "PASS"

    # ---------------------------------------------------------
    # 1. KIỂM TRA GLOBAL SLA (Chạy lô chung)
    # ---------------------------------------------------------
    ts_raw = data.get("latest_exported_at") or data.get("run_timestamp")
    dt = parse_iso(str(ts_raw)) if ts_raw else None

    if dt is None:
        overall_status = "WARN"
        detail["global"] = {"reason": "no_timestamp_in_manifest"}
    else:
        age_hours = (now - dt).total_seconds() / 3600.0
        detail["global"] = {
            "latest_exported_at": ts_raw,
            "age_hours": round(age_hours, 3),
            "sla_hours": global_sla_hours,
        }
        if age_hours > global_sla_hours:
            overall_status = "FAIL"
            detail["global"]["reason"] = "global_freshness_sla_exceeded"

    # ---------------------------------------------------------
    # 2. KIỂM TRA DOCUMENT SLA (Dựa trên Watermark DB)
    # ---------------------------------------------------------
    watermarks = data.get("doc_watermarks", {})
    if watermarks:
        for doc_id, ts_str in watermarks.items():
            doc_dt = parse_iso(ts_str)
            if not doc_dt:
                continue

            doc_age = (now - doc_dt).total_seconds() / 3600.0
            
            # Lấy SLA riêng biệt của doc_id đó, nếu không có thì dùng Global SLA
            doc_sla = DOC_SLA_CONFIG.get(doc_id, global_sla_hours)

            doc_detail = {
                "exported_at": ts_str,
                "age_hours": round(doc_age, 3),
                "sla_hours": doc_sla
            }

            # Nếu bất kỳ tài liệu nào vi phạm SLA riêng của nó, fail toàn bộ quy trình
            if doc_age > doc_sla:
                overall_status = "FAIL"
                doc_detail["status"] = "FAIL"
                doc_detail["reason"] = f"document_sla_exceeded"
            else:
                doc_detail["status"] = "PASS"

            detail["docs"][doc_id] = doc_detail

    return overall_status, detail
