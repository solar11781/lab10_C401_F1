"""
Cleaning rules — raw export → cleaned rows + quarantine.

Baseline gồm các failure mode mở rộng (allowlist doc_id, parse ngày, HR stale version).
Tích hợp thêm các rules Nâng cao (Distinction: PII Masking, IT Log, Teencode, Gibberish, Dynamic Cutoff).
"""

from __future__ import annotations

import csv
import hashlib
import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Tuple
from datetime import datetime

# Khớp export hợp lệ trong lab (mở rộng khi nhóm thêm doc mới — phải đồng bộ contract).
ALLOWED_DOC_IDS = frozenset(
    {
        "policy_refund_v4",
        "sla_p1_2026",
        "it_helpdesk_faq",
        "hr_leave_policy",
    }
)

_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_DMY_SLASH = re.compile(r"^(\d{2})/(\d{2})/(\d{4})$")


def _norm_text(s: str) -> str:
    return " ".join((s or "").strip().split()).lower()


def _stable_chunk_id(doc_id: str, chunk_text: str, seq: int) -> str:
    h = hashlib.sha256(f"{doc_id}|{chunk_text}|{seq}".encode("utf-8")).hexdigest()[:16]
    return f"{doc_id}_{seq}_{h}"


def _normalize_effective_date(raw: str) -> Tuple[str, str]:
    """
    Trả về (iso_date, error_reason).
    iso_date rỗng nếu sai định dạng HOẶC ngày không tồn tại thực tế (vd: tháng 20, ngày 32).
    """
    s = (raw or "").strip()
    if not s:
        return "", "empty_effective_date"
        
    # Trường hợp 1: Khớp định dạng YYYY-MM-DD
    if _ISO_DATE.match(s):
        try:
            # Dùng strptime để validate ngày có thật không
            datetime.strptime(s, "%Y-%m-%d")
            return s, ""
        except ValueError:
            # Trả về lý do lỗi mới cho các ngày vô lý
            return "", "invalid_effective_date"

    # Trường hợp 2: Khớp định dạng DD/MM/YYYY
    m = _DMY_SLASH.match(s)
    if m:
        dd, mm, yyyy = m.group(1), m.group(2), m.group(3)
        iso_str = f"{yyyy}-{mm}-{dd}"
        try:
            # Validate lại chuỗi ISO vừa tạo
            datetime.strptime(iso_str, "%Y-%m-%d")
            return iso_str, ""
        except ValueError:
            return "", "invalid_effective_date"

    # Trường hợp 3: Hoàn toàn sai định dạng chữ/số
    return "", "invalid_effective_date"


def load_raw_csv(path: Path) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append({k: (v or "").strip() for k, v in r.items()})
    return rows


def clean_rows(
    rows: List[Dict[str, str]],
    *,
    apply_refund_window_fix: bool = True,
    run_id: str = "DEFAULT_RUN_ID", # Added rule: tracking
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Trả về (cleaned, quarantine).
    """
    quarantine: List[Dict[str, Any]] = []
    cleaned: List[Dict[str, Any]] = []
    seq = 0

    # =========================================================================
    # VÒNG 1: DYNAMIC VERSION CUTOFF
    # =========================================================================
    max_dates: Dict[str, str] = {}
    for r in rows:
        d_id = r.get("doc_id", "")
        if d_id in ALLOWED_DOC_IDS:
            eff_norm, err = _normalize_effective_date(r.get("effective_date", ""))
            if not err and (d_id not in max_dates or eff_norm > max_dates[d_id]):
                max_dates[d_id] = eff_norm

    # =========================================================================
    # VÒNG 2: CLEANING & FILTERING
    # =========================================================================
    seen_content: set[Tuple[str, str]] = set()

    for raw in rows:
        doc_id = raw.get("doc_id", "")
        text = raw.get("chunk_text", "")
        eff_raw = raw.get("effective_date", "")
        exported_at = raw.get("exported_at", "")

        # --- BASE RULES (Kiểm tra Schema & Format) ---
        if doc_id not in ALLOWED_DOC_IDS:
            quarantine.append({**raw, "reason": "unknown_doc_id", "run_id": run_id})
            continue

        eff_norm, eff_err = _normalize_effective_date(eff_raw)
        if eff_err == "empty_effective_date":
            quarantine.append({**raw, "reason": "missing_effective_date", "run_id": run_id})
            continue
        if eff_err in ["invalid_effective_date_format", "invalid_effective_date_value"]:
            quarantine.append({**raw, "reason": eff_err, "effective_date_raw": eff_raw, "run_id": run_id})
            continue

        # --- BASE RULE + ADDED RULE (Lọc Version Cũ) ---
        if doc_id == "hr_leave_policy" and eff_norm < "2026-01-01":
            quarantine.append({
                **raw, "reason": "stale_hr_policy_effective_date", 
                "effective_date_normalized": eff_norm, "run_id": run_id
            })
            continue
        if max_dates.get(doc_id) and eff_norm < max_dates[doc_id]:
            quarantine.append({**raw, "reason": "stale_document_version", "run_id": run_id})
            continue

        if not text.strip():
            quarantine.append({**raw, "reason": "missing_chunk_text", "run_id": run_id})
            continue

        # =====================================================================
        # CÁC RULE CHẶN DATA RÁC TỐI THƯỢNG (Bao gồm các ca đặc trị)
        # =====================================================================
        text_lower = text.lower()

        # 1. Dummy Data
        if "lorem ipsum" in text_lower or "test data" in text_lower or "dữ liệu test" in text_lower or "[lỗi hệ thống]" in text_lower:
            quarantine.append({**raw, "reason": "dummy_test_data", "run_id": run_id})
            continue
            
        # 2. Oversized Chunk
        if len(text.split()) > 300:
            quarantine.append({**raw, "reason": "oversized_chunk", "run_id": run_id})
            continue

        # 3. [ĐÃ THÊM LẠI] Mojibake Encoding: Chặn lỗi font chữ (Diệt "ChÃnh sÃ¡ch")
        # Các ký tự như Ã, Ä, Å... sinh ra khi file UTF-8 bị đọc nhầm format
        if re.search(r'[ÃÄÅÆÇËÌÎÏÐÑÖØÙÛÜÝÞß]', text):
            quarantine.append({**raw, "reason": "encoding_mojibake_error", "run_id": run_id})
            continue

        # 4. [ĐÃ THÊM LẠI] Missing Vowels: Chặn lỗi rụng nguyên âm (Diệt "cc thit b ngoi vi")
        pure_consonants = [w for w in re.findall(r'\b[bcdfghjklmnpqrstvwxz]+\b', text_lower) if w not in ['tr', 'th', 'ch', 'ph', 'nh', 'kh', 'sh', 'vn']]
        if len(pure_consonants) >= 2:
            quarantine.append({**raw, "reason": "broken_text_missing_vowels", "run_id": run_id})
            continue

        # 5. Gibberish / Keysmash Filter
        if re.search(r'[bcdfghjklmnpqrstvwxz]{6,}', text_lower): # Nâng lên 6 phụ âm để an toàn hơn
            quarantine.append({**raw, "reason": "gibberish_keysmash_consonants", "run_id": run_id})
            continue
        if any(len(word) > 25 for word in text.split()):
            quarantine.append({**raw, "reason": "gibberish_absurd_word_length", "run_id": run_id})
            continue

        # --- BASE RULE UPGRADE (Deduplication dùng Hash) ---
        fixed_text = unicodedata.normalize("NFC", text)
        fixed_text = re.sub(r'[“”]', '"', fixed_text)
        
        norm_hash = hashlib.md5(_norm_text(fixed_text).encode('utf-8')).hexdigest()
        dedup_key = (doc_id, norm_hash)
        if dedup_key in seen_content:
            quarantine.append({**raw, "reason": "duplicate_chunk_text", "run_id": run_id})
            continue
        seen_content.add(dedup_key)

        # --- ADDED RULES (Transform: Fix text) ---
        text_for_ratio = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', fixed_text)
        if len(text_for_ratio) > 0 and (len(re.findall(r'[^\w\s]', text_for_ratio)) / len(text_for_ratio)) > 0.25:
            quarantine.append({**raw, "reason": "it_log_dump_noise", "run_id": run_id})
            continue

        if "{{" in fixed_text and "}}" in fixed_text:
            fixed_text = re.sub(r"\{\{SUPPORT_EMAIL\}\}", "support@company.com", fixed_text, flags=re.IGNORECASE)
            fixed_text = re.sub(r"\{\{[^}]+\}\}", "[SYSTEM_DATA]", fixed_text)

        for pattern, replacement in {r'\bkh\b': 'khách hàng', r'\bsp\b': 'sản phẩm', r'\bko\b': 'không', r'\bđc\b': 'được', r'\btt\b': 'thanh toán'}.items():
            fixed_text = re.sub(pattern, replacement, fixed_text, flags=re.IGNORECASE)

        fixed_text = re.sub(r'\b(?:\d{4}[ -]?){3}\d{4}\b', '[REDACTED_CC]', fixed_text)
        fixed_text = re.sub(r'\b0\d{9}\b', '[REDACTED_PHONE]', fixed_text)
        fixed_text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', fixed_text)

        if apply_refund_window_fix and doc_id == "policy_refund_v4":
            if "14 ngày làm việc" in fixed_text:
                fixed_text = fixed_text.replace("14 ngày làm việc", "7 ngày làm việc")
                fixed_text += " [cleaned: stale_refund_window]"

        fixed_text = " ".join(fixed_text.split())
        
        seq += 1
        cleaned.append(
            {
                "chunk_id": _stable_chunk_id(doc_id, fixed_text, seq),
                "doc_id": doc_id,
                "chunk_text": fixed_text,
                "effective_date": eff_norm,
                "exported_at": exported_at or "",
            }
        )

    return cleaned, quarantine

def write_cleaned_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("chunk_id,doc_id,chunk_text,effective_date,exported_at\n", encoding="utf-8")
        return
    fieldnames = ["chunk_id", "doc_id", "chunk_text", "effective_date", "exported_at"]
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fieldnames})


def write_quarantine_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("chunk_id,doc_id,chunk_text,effective_date,exported_at,reason,run_id\n", encoding="utf-8")
        return
    
    # Safe key extraction để tránh lỗi vỡ Schema khi có cột reason lạ
    keys: List[str] = []
    for r in rows:
        for k in r.keys():
            if k not in keys and k not in ["reason", "run_id"]:
                keys.append(k)
    keys.extend(["reason", "run_id"])
    
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore", restval="")
        w.writeheader()
        for r in rows:
            w.writerow(r)
