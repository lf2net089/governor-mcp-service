"""
tools/workflow_tools.py — Category C: 三段工作流（4 個 Tools）
sg_run_stage_01 | sg_run_stage_02 | sg_run_stage_03 | sg_get_workflow_status

每個 Stage 工具：
1. 呼叫 pre_stage_hook 取得 Reminder
2. 驗證輸入欄位（不補全空欄位）
3. 更新 stage_progress
4. 回傳結果 + _reminders
"""

import uuid
import json
from core.db import upsert_stage_progress, get_stage_progress, get_session, get_records
from core.reminder import get_active_reminders, format_reminders_for_response
from hooks.pre_stage import pre_stage_hook


def _progress_id(session_id: str, stage: str) -> str:
    return f"{session_id}-stage{stage}"


async def tool_run_stage_01(
    session_id: str,
    surface_requirement: str,
    actual_business_purpose: str,
    has_concrete_target: bool,
    has_io_logic: bool,
    has_reference: bool,
    assumption_data_verified: bool,
    assumption_performance_evaluated: bool,
    assumption_dependencies_confirmed: bool,
    boundary_null_defined: bool,
    boundary_concurrency_considered: bool,
) -> dict:
    """
    Stage 01 — 假設對齊門檻驗證。

    所有 bool 欄位由使用者明確回答（True/False），
    系統不推斷、不補全任何未回答的項目。

    必要輸入：
    - surface_requirement: 表象需求（使用者原始描述）
    - actual_business_purpose: 實質業務目的（使用者明確陳述）
    - 8 個 bool 檢查項
    """
    session = await get_session(session_id)
    if not session:
        return {"error": f"找不到 session: {session_id}", "_reminders": []}

    hook = await pre_stage_hook(session_id, "01")
    reminders = hook["reminders"]

    # 計算通過/未通過
    required_checks = {
        "has_concrete_target": has_concrete_target,
        "has_io_logic": has_io_logic,
        "has_reference": has_reference,
        "assumption_data_verified": assumption_data_verified,
        "assumption_performance_evaluated": assumption_performance_evaluated,
        "assumption_dependencies_confirmed": assumption_dependencies_confirmed,
        "boundary_null_defined": boundary_null_defined,
        "boundary_concurrency_considered": boundary_concurrency_considered,
    }

    passed_items = [k for k, v in required_checks.items() if v]
    failed_items = [k for k, v in required_checks.items() if not v]
    all_passed = len(failed_items) == 0

    gate_result = {
        "passed": all_passed,
        "total": len(required_checks),
        "passed_count": len(passed_items),
        "failed_items": failed_items,
        "surface_requirement": surface_requirement,
        "actual_business_purpose": actual_business_purpose,
    }

    status = "passed" if all_passed else "blocked"
    pid = _progress_id(session_id, "01")
    await upsert_stage_progress(pid, session_id, "01", status, gate_result)

    # Reminder：提醒記錄
    if not await get_records(session_id, stage="hypothesis"):
        reminders.append({
            "level": "WARNING",
            "type": "unrecorded_stage",
            "message": "⚠️ Stage 01 已執行，但尚未呼叫 sg_record_input（stage='hypothesis'）記錄討論內容。此段對話不會進入報告。",
            "action": "呼叫 sg_record_input(stage='hypothesis') 記錄討論片段",
        })

    return {
        "session_id": session_id,
        "stage": "01",
        "status": status,
        "gate_passed": all_passed,
        "passed_count": len(passed_items),
        "total_checks": len(required_checks),
        "failed_items": failed_items,
        "surface_requirement": surface_requirement,
        "actual_business_purpose": actual_business_purpose,
        "next_step": "繼續 sg_run_stage_02" if all_passed else "修正後重新呼叫 sg_run_stage_01",
        "_reminders": reminders,
    }


async def tool_run_stage_02(
    session_id: str,
    file_path: str,
    function_name: str,
    change_purpose: str,
    upstream_verification: str,
    downstream_impact: str,
    hardcode_detected: bool,
    ui_hiding_detected: bool,
    todo_hack_detected: bool,
    follows_architecture: bool,
    has_test_coverage: bool,
) -> dict:
    """
    Stage 02 — GitNexus 圖譜剖析記錄。

    upstream_verification / downstream_impact：
    使用者根據 GitNexus 實際查詢結果填入（原始文字，不補全）。
    
    若 hardcode_detected 或 ui_hiding_detected 為 True，
    系統自動將此 Stage 標記為 blocked，並附加拒絕說明。
    """
    session = await get_session(session_id)
    if not session:
        return {"error": f"找不到 session: {session_id}", "_reminders": []}

    hook = await pre_stage_hook(session_id, "02")
    reminders = hook["reminders"]

    # 自動拒絕條件
    reject_reasons = []
    if hardcode_detected:
        reject_reasons.append("偵測到魔法數字或字串硬編碼（Hard Code）")
    if ui_hiding_detected:
        reject_reasons.append("偵測到前端 CSS 隱藏 / display:none 遮蓋（UI 遮醜）")
    if todo_hack_detected:
        reject_reasons.append("存在未規劃移除時程的 TODO/HACK/FIXME 臨時補丁")

    auto_rejected = len(reject_reasons) > 0

    gate_result = {
        "auto_rejected": auto_rejected,
        "reject_reasons": reject_reasons,
        "file_path": file_path,
        "function_name": function_name,
        "change_purpose": change_purpose,
        "upstream_verification": upstream_verification,
        "downstream_impact": downstream_impact,
        "follows_architecture": follows_architecture,
        "has_test_coverage": has_test_coverage,
    }

    status = "blocked" if auto_rejected else "passed"
    pid = _progress_id(session_id, "02")
    await upsert_stage_progress(pid, session_id, "02", status, gate_result)

    if auto_rejected:
        reminders.append({
            "level": "CRITICAL",
            "type": "strict_critic_reject",
            "message": f"🚫 Strict Critic 拒絕分支已觸發。原因：{'; '.join(reject_reasons)}。任務退回至 Stage 01，請提出長期防禦方案。",
            "action": "重新呼叫 sg_run_stage_01，提出不將就的長期對策",
        })

    if not await get_records(session_id, stage="gitnexus_audit"):
        reminders.append({
            "level": "WARNING",
            "type": "unrecorded_stage",
            "message": "⚠️ Stage 02 已執行，但尚未用 sg_record_input（stage='gitnexus_audit'）記錄圖譜剖析討論。",
            "action": "呼叫 sg_record_input(stage='gitnexus_audit') 記錄討論",
        })

    return {
        "session_id": session_id,
        "stage": "02",
        "status": status,
        "auto_rejected": auto_rejected,
        "reject_reasons": reject_reasons,
        "file_path": file_path,
        "function_name": function_name,
        "upstream_verification": upstream_verification,
        "downstream_impact": downstream_impact,
        "next_step": "退回 Stage 01 修正" if auto_rejected else "繼續 sg_run_stage_03",
        "_reminders": reminders,
    }


async def tool_run_stage_03(
    session_id: str,
    blind_spot: str,
    upstream_verification: str,
    downstream_impact: str,
    option_a_immediate_cost: str,
    option_a_long_term_risk: str,
    option_b_implementation_cost: str,
    option_b_asset_value: str,
    system_reflection_question: str,
) -> dict:
    """
    Stage 03 — 架構辯證，輸出完整 SystemGovernorResponse JSON。

    所有欄位必須由使用者（三角色辯論結果）明確填入。
    空字串欄位不補全，在報告中標示為【⏳ 待確認】。
    """
    session = await get_session(session_id)
    if not session:
        return {"error": f"找不到 session: {session_id}", "_reminders": []}

    hook = await pre_stage_hook(session_id, "03")
    reminders = hook["reminders"]

    # 建構 SystemGovernorResponse（嚴格不補全）
    response_json = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "SystemGovernorResponse",
        "rational_skepticism": {
            "blind_spot": blind_spot or "【⏳ 待確認 — Strict Critic 盲點尚未記錄】"
        },
        "gitnexus_flow_audit": {
            "upstream_verification": upstream_verification or "【⏳ 待確認 — GitNexus Upstream 尚未記錄】",
            "downstream_impact": downstream_impact or "【⏳ 待確認 — GitNexus Downstream 尚未記錄】"
        },
        "architectural_tradeoff": {
            "option_a_short_term": {
                "immediate_cost": option_a_immediate_cost or "【⏳ 待確認】",
                "long_term_risk_and_entropy": option_a_long_term_risk or "【⏳ 待確認】"
            },
            "option_b_long_term": {
                "implementation_cost": option_b_implementation_cost or "【⏳ 待確認】",
                "asset_value_protection": option_b_asset_value or "【⏳ 待確認】"
            }
        },
        "system_reflection_question": system_reflection_question or "【⏳ 待確認 — 閉環反問尚未設定】"
    }

    # 統計空欄位
    unfilled = []
    if not blind_spot: unfilled.append("blind_spot")
    if not upstream_verification: unfilled.append("upstream_verification")
    if not downstream_impact: unfilled.append("downstream_impact")
    if not option_a_immediate_cost: unfilled.append("option_a_immediate_cost")
    if not option_a_long_term_risk: unfilled.append("option_a_long_term_risk")
    if not option_b_implementation_cost: unfilled.append("option_b_implementation_cost")
    if not option_b_asset_value: unfilled.append("option_b_asset_value")
    if not system_reflection_question: unfilled.append("system_reflection_question")

    gate_result = {
        "response_json": response_json,
        "unfilled_fields": unfilled,
        "completeness": f"{8 - len(unfilled)}/8",
    }

    status = "passed" if not unfilled else "in_progress"
    pid = _progress_id(session_id, "03")
    await upsert_stage_progress(pid, session_id, "03", status, gate_result)

    if unfilled:
        reminders.append({
            "level": "INFO",
            "type": "missing_field",
            "message": f"ℹ️ {len(unfilled)} 個欄位尚未填入：{', '.join(unfilled)}。報告中這些欄位將標示【⏳ 待確認】。",
            "action": "補充後重新呼叫 sg_run_stage_03，或直接生成報告並手動補充",
        })

    if not await get_records(session_id, stage="tradeoff"):
        reminders.append({
            "level": "WARNING",
            "type": "unrecorded_stage",
            "message": "⚠️ Stage 03 已執行，但尚未用 sg_record_input（stage='tradeoff'）記錄辯論過程。",
            "action": "呼叫 sg_record_input(stage='tradeoff') 記錄三角色辯論片段",
        })

    return {
        "session_id": session_id,
        "stage": "03",
        "status": status,
        "completeness": gate_result["completeness"],
        "unfilled_fields": unfilled,
        "system_governor_response": response_json,
        "next_step": "可呼叫 sg_generate_full 生成完整工程報告",
        "_reminders": reminders,
    }


async def tool_get_workflow_status(session_id: str) -> dict:
    """查看三段工作流目前進度概覽。"""
    session = await get_session(session_id)
    if not session:
        return {"error": f"找不到 session: {session_id}", "_reminders": []}

    progress = await get_stage_progress(session_id)
    reminders = await get_active_reminders(session_id)

    stages = {p["stage"]: p for p in progress}
    summary = []
    for s in ["01", "02", "03"]:
        label = {"01": "假設對齊", "02": "GitNexus 剖析", "03": "架構辯證"}[s]
        p = stages.get(s)
        summary.append({
            "stage": s,
            "label": label,
            "status": p["status"] if p else "pending",
            "completed_at": p["completed_at"] if p else None,
        })

    return {
        "session_id": session_id,
        "session_topic": session["topic"],
        "session_status": session["status"],
        "stages": summary,
        "_reminders": format_reminders_for_response(reminders),
    }
