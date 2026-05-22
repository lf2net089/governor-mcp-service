"""
hooks/pre_stage.py — Stage 進入前 Hook
在執行任何 Stage 前呼叫，執行前置條件檢查並回傳 Reminder。
"""

from core.reminder import check_idle_reminder, check_unrecorded_stage, format_reminders_for_response


async def pre_stage_hook(session_id: str, stage: str) -> dict:
    """
    Returns: { "allowed": bool, "reminders": list, "blocked_reason": str | None }
    Note: 此 Hook 不阻斷流程，只提醒。工程師最終決定是否繼續。
    """
    reminders = []

    # 檢查 idle
    idle_reminders = await check_idle_reminder(session_id)
    reminders.extend(idle_reminders)

    # 檢查前一 Stage 是否有記錄
    unrecorded = await check_unrecorded_stage(session_id, stage)
    reminders.extend(unrecorded)

    return {
        "allowed": True,  # 永遠允許，但必須帶 reminders
        "reminders": format_reminders_for_response(reminders),
        "has_warnings": len(reminders) > 0,
    }
