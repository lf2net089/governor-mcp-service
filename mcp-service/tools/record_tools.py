"""
tools/record_tools.py — Category B: 原始輸入捕獲（核心，3 個 Tools）
sg_record_input | sg_check_reminders | sg_get_records

鐵則：
- content 傳入後只計算 hash，絕不修改任何字元
- 寫入資料庫後，records 表中的 content 欄位永不更新
- 若有疑慮停下來跟使用者確認，嚴禁幻覺補全
"""

import uuid
from core.db import (
    insert_record, get_records, get_session,
    get_pending_reminders, acknowledge_reminders
)
from core.anti_hallucination import compute_sha256, short_hash
from core.reminder import (
    check_idle_reminder, get_active_reminders,
    format_reminders_for_response
)

VALID_ROLES = {"user", "stakeholder", "pm", "engineer", "system"}
VALID_STAGES = {
    "interview", "hypothesis", "gitnexus_audit",
    "tradeoff", "conclusion", "memo", "pain_point", "next_session"
}


async def tool_record_input(
    session_id: str,
    content: str,
    role: str = "user",
    stage: str = "interview",
    source_note: str | None = None,
) -> dict:
    """
    【核心工具】將使用者的原始文字原封不動存入資料庫。
    
    content: 使用者原始話語或討論片段（不做任何修改）
    role: 發言角色 — user | stakeholder | pm | engineer | system
    stage: 所屬階段 — interview | hypothesis | gitnexus_audit | tradeoff | conclusion | memo | pain_point | next_session
    source_note: 選填，說明此記錄的情境背景
    
    ⚠️ 系統只存入，絕不修改、補全或推導。
    """
    # 驗證 session
    session = await get_session(session_id)
    if not session:
        return {"error": f"找不到 session: {session_id}", "_reminders": []}

    # 驗證參數
    if role not in VALID_ROLES:
        return {
            "error": f"無效的 role: {role}，可用值: {sorted(VALID_ROLES)}",
            "_reminders": []
        }
    if stage not in VALID_STAGES:
        return {
            "error": f"無效的 stage: {stage}，可用值: {sorted(VALID_STAGES)}",
            "_reminders": []
        }
    if not content or not content.strip():
        return {
            "error": "content 不可為空。嚴禁傳入空字串——請確認使用者確實說了這段話。",
            "_reminders": []
        }

    # 計算 hash（content 保持原始，不做任何處理）
    raw_content = content  # 明確命名，強調不修改
    h = compute_sha256(raw_content)
    record_id = f"rec-{uuid.uuid4().hex[:12]}"

    record = await insert_record(record_id, session_id, role, stage, raw_content, h, source_note)

    # 確認後清除 idle reminders
    await acknowledge_reminders(session_id)

    return {
        "record_id": record_id,
        "session_id": session_id,
        "role": role,
        "stage": stage,
        "sha256_hash": h,
        "short_hash": short_hash(h),
        "content_length": len(raw_content),
        "source_note": source_note,
        "created_at": record["created_at"],
        "_note": f"記錄已存入。防竄改 hash 前 8 碼: {short_hash(h)}。content 未經任何修改。",
        "_reminders": [],  # 剛記錄完，清空提醒
    }


async def tool_check_reminders(session_id: str, acknowledge: bool = False) -> dict:
    """
    查詢目前所有待確認的 Reminder。
    acknowledge=True 時，同時將所有 Reminder 標記為已確認。
    
    此工具應定期呼叫，確保不遺漏任何記錄提醒。
    """
    session = await get_session(session_id)
    if not session:
        return {"error": f"找不到 session: {session_id}", "_reminders": []}

    # 主動偵測 idle
    idle_r = await check_idle_reminder(session_id)
    all_reminders = await get_active_reminders(session_id)

    if acknowledge:
        await acknowledge_reminders(session_id)
        return {
            "acknowledged": True,
            "count": len(all_reminders),
            "message": f"已確認 {len(all_reminders)} 個 Reminder。",
            "_reminders": [],
        }

    return {
        "pending_count": len(all_reminders),
        "reminders": format_reminders_for_response(all_reminders),
        "_reminders": format_reminders_for_response(all_reminders),
        "_note": "若要確認所有 Reminder，呼叫時帶入 acknowledge=true。",
    }


async def tool_get_records(
    session_id: str,
    stage: str | None = None,
    role: str | None = None,
) -> dict:
    """
    查詢指定 session 的原始輸入記錄。
    可選用 stage / role 篩選。
    回傳的 content 為完整原始文字，附帶 SHA-256 短碼供比對。
    """
    session = await get_session(session_id)
    if not session:
        return {"error": f"找不到 session: {session_id}", "_reminders": []}

    records = await get_records(session_id, stage=stage, role=role)
    reminders = await get_active_reminders(session_id)

    # 為每筆記錄加上 short_hash 方便顯示
    display_records = [
        {**r, "short_hash": short_hash(r.get("sha256_hash", ""))}
        for r in records
    ]

    return {
        "session_id": session_id,
        "total": len(records),
        "filter": {"stage": stage, "role": role},
        "records": display_records,
        "_reminders": format_reminders_for_response(reminders),
    }
