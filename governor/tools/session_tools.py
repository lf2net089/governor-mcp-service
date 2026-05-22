"""
tools/session_tools.py — Category A: 會話管理（4 個 Tools）
sg_create_session | sg_get_session | sg_list_sessions | sg_close_session
"""

import uuid
from core.db import create_session, get_session, list_sessions, close_session
from core.reminder import get_active_reminders, format_reminders_for_response


async def tool_create_session(topic: str, stakeholders: list[str] | None = None) -> dict:
    """
    建立新的 System Governor 工作階段。
    topic: 本次訪談/需求/工程議題的主題描述（使用者原始文字）
    stakeholders: 參與者清單（選填）
    """
    session_id = f"sg-{uuid.uuid4().hex[:12]}"
    session = await create_session(session_id, topic, stakeholders)
    return {
        "session_id": session_id,
        "topic": topic,
        "stakeholders": stakeholders or [],
        "status": "active",
        "created_at": session["created_at"],
        "_reminders": [],
        "_note": "請記下 session_id，後續所有工具呼叫都需要帶入。",
    }


async def tool_get_session(session_id: str) -> dict:
    """取得指定 session 的詳情與目前狀態。"""
    session = await get_session(session_id)
    if not session:
        return {"error": f"找不到 session: {session_id}", "_reminders": []}

    reminders = await get_active_reminders(session_id)
    return {
        **session,
        "_reminders": format_reminders_for_response(reminders),
    }


async def tool_list_sessions() -> dict:
    """列出所有工作階段（依建立時間倒序）。"""
    sessions = await list_sessions()
    return {
        "total": len(sessions),
        "sessions": sessions,
        "_reminders": [],
    }


async def tool_close_session(session_id: str) -> dict:
    """標記工作階段為完成。關閉後仍可查詢記錄，但不建議再新增記錄。"""
    session = await get_session(session_id)
    if not session:
        return {"error": f"找不到 session: {session_id}", "_reminders": []}

    await close_session(session_id)
    reminders = await get_active_reminders(session_id)
    return {
        "session_id": session_id,
        "status": "closed",
        "message": "Session 已關閉。如有未生成的報告，建議在關閉前先呼叫 sg_generate_full。",
        "_reminders": format_reminders_for_response(reminders),
    }
