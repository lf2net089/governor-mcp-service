"""
core/reminder.py — Reminder 狀態管理
設計：每個工具回應都會攜帶 _reminders 欄位。
觸發條件：
  1. Stage 完成後超過 THRESHOLD 分鐘未呼叫 sg_record_input
  2. 進入新 Stage 前，前一 Stage 沒有對應記錄
  3. 長時間 idle（可選）
"""

import os
import uuid
from datetime import datetime, timezone, timedelta

from core.db import (
    get_pending_reminders, insert_reminder, get_last_record_time,
    get_stage_progress, get_records
)

THRESHOLD_MINUTES = int(os.environ.get("REMINDER_THRESHOLD_MINUTES", "10"))


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def check_idle_reminder(session_id: str) -> list[dict]:
    """
    若距離上一次 sg_record_input 超過 THRESHOLD 分鐘，
    返回 reminder 提示，並存入 DB。
    """
    reminders = []
    last_ts = await get_last_record_time(session_id)

    if last_ts:
        last_dt = datetime.fromisoformat(last_ts)
        elapsed = (_now() - last_dt).total_seconds() / 60
        if elapsed >= THRESHOLD_MINUTES:
            msg = (
                f"⚠️ 已超過 {int(elapsed)} 分鐘未呼叫 sg_record_input 記錄對話內容。"
                f" 請在繼續前使用 sg_record_input 存入當前討論片段，避免對話遺漏。"
            )
            rid = str(uuid.uuid4())
            reminder = await insert_reminder(rid, session_id, "long_idle", msg)
            reminders.append(reminder)

    return reminders


async def check_unrecorded_stage(session_id: str, current_stage: str) -> list[dict]:
    """
    進入新 Stage 前，確認前一 Stage 是否有 records。
    Stage 順序：01 → 02 → 03
    """
    stage_order = {"02": "hypothesis", "03": "gitnexus_audit"}
    required_stage = stage_order.get(current_stage)
    if not required_stage:
        return []

    records = await get_records(session_id, stage=required_stage)
    reminders = []

    if not records:
        stage_label = {"hypothesis": "Stage 01 假設對齊", "gitnexus_audit": "Stage 02 GitNexus 剖析"}.get(required_stage, required_stage)
        msg = (
            f"⚠️ 你正在進入 Stage {current_stage}，但 {stage_label} 階段尚無任何 sg_record_input 記錄。"
            f" 此段討論將不會出現在最終報告中。強烈建議先呼叫 sg_record_input 將相關對話存入，再繼續。"
        )
        rid = str(uuid.uuid4())
        reminder = await insert_reminder(rid, session_id, "unrecorded_stage", msg)
        reminders.append(reminder)

    return reminders


async def get_active_reminders(session_id: str) -> list[dict]:
    """取得目前所有未確認的 Reminder。"""
    return await get_pending_reminders(session_id)


def format_reminders_for_response(reminders: list[dict]) -> list[dict]:
    """
    將 reminder 格式化為工具回應中的 _reminders 欄位。
    """
    return [
        {
            "level": "WARNING",
            "type": r.get("reminder_type", r.get("type", "unknown")),
            "message": r["message"],
            "action": "呼叫 sg_record_input 記錄當前討論內容",
            "triggered_at": r.get("triggered_at", ""),
        }
        for r in reminders
    ]
