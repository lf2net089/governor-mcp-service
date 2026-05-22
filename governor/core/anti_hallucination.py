"""
core/anti_hallucination.py — 反幻覺保護層
鐵則：
1. content 傳入後只計算 hash，絕不修改
2. 空欄位只能輸出 PENDING_PLACEHOLDER，嚴禁推斷補全
3. 所有 hash 可供外部比對原始對話
"""

import hashlib
from datetime import datetime, timezone


# 空欄位標準佔位符
def pending_placeholder(field_name: str, session_id: str | None = None) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    base = f"【⏳ 待確認 — {ts} 尚未記錄】"
    if field_name:
        base = f"【⏳ {field_name} 待確認 — {ts} 尚未記錄】"
    return base


def compute_sha256(content: str) -> str:
    """計算 content 的 SHA-256 hash，作為防竄改憑據。"""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def short_hash(full_hash: str) -> str:
    """取前 8 碼用於報告顯示。"""
    return full_hash[:8]


def verify_content(content: str, stored_hash: str) -> bool:
    """驗證 content 是否與儲存的 hash 一致（偵測是否被竄改）。"""
    return compute_sha256(content) == stored_hash


def safe_fill(value: str | None, field_name: str = "") -> tuple[str, bool]:
    """
    回傳 (顯示文字, is_filled)。
    若 value 為 None 或空字串，強制輸出佔位符，is_filled=False。
    嚴禁在此函式中推導任何內容。
    """
    if value and value.strip():
        return (value.strip(), True)
    return (pending_placeholder(field_name), False)


def build_hash_chain(records: list[dict]) -> list[dict]:
    """
    為報告建立 hash 鏈列表，供比對驗證。
    每筆輸出：{ record_id, short_hash, created_at, role, stage }
    """
    return [
        {
            "record_id": r["id"],
            "short_hash": short_hash(r.get("sha256_hash", "")),
            "full_hash": r.get("sha256_hash", ""),
            "created_at": r.get("created_at", ""),
            "role": r.get("role", ""),
            "stage": r.get("stage", ""),
        }
        for r in records
    ]
