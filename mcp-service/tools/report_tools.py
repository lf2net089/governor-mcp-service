"""
tools/report_tools.py — Category E: 三種報告生成（3 個 Tools）
sg_generate_memo | sg_generate_trace | sg_generate_full

鐵則：
- 只將已記錄的 records 填入模板
- 空欄位輸出 pending_placeholder()，嚴禁 LLM 推導補全
- 報告中附帶 SHA-256 hash chain 供防竄改比對
"""

import uuid
import os
from datetime import datetime, timezone
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

from core.db import (
    get_session, get_records, get_stage_progress, insert_report,
    list_reports as db_list_reports
)
from core.anti_hallucination import safe_fill, build_hash_chain
from core.reminder import get_active_reminders, format_reminders_for_response

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
REPORTS_DIR = Path(os.environ.get("REPORTS_DIR", "/data/reports"))

_jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=True,
)
# 注入 safe_fill 至模板
_jinja_env.globals["safe_fill"] = safe_fill
_jinja_env.globals["now_utc"] = lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _report_path(report_type: str, report_id: str) -> Path:
    sub = {"memo": "memo", "trace": "traces", "full": "full"}.get(report_type, "memo")
    d = REPORTS_DIR / sub
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{report_id}.html"


async def _build_context(session_id: str) -> dict:
    """組裝模板 context，嚴禁補全任何空欄位。"""
    session = await get_session(session_id)
    all_records = await get_records(session_id)
    stage_progress = await get_stage_progress(session_id)
    hash_chain = build_hash_chain(all_records)

    # 按 stage 分類記錄
    by_stage: dict[str, list] = {}
    for r in all_records:
        by_stage.setdefault(r["stage"], []).append(r)

    # 從 stage_progress 取出各 Stage 結果
    stages_map = {p["stage"]: p for p in stage_progress}

    return {
        "session": session,
        "all_records": all_records,
        "by_stage": by_stage,
        "stage_01": stages_map.get("01"),
        "stage_02": stages_map.get("02"),
        "stage_03": stages_map.get("03"),
        "hash_chain": hash_chain,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "session_id": session_id,
    }


async def tool_generate_memo(session_id: str) -> dict:
    """
    【Report Type 1】Quick Memo — 需求確認/想法發想/存證（1 頁）
    
    輸出內容（嚴格來自 records，不推導）：
    - 訪談要點（stage='interview' 記錄）
    - memo 記錄（stage='memo'）
    - 確認結論（stage='conclusion'）
    - 所有【⏳ 待確認】項目列表
    - SHA-256 hash 鏈
    """
    session = await get_session(session_id)
    if not session:
        return {"error": f"找不到 session: {session_id}", "_reminders": []}

    ctx = await _build_context(session_id)
    unfilled = []

    # 檢查哪些必要 stage 沒有記錄
    for stage, label in [("interview", "訪談記錄"), ("conclusion", "需求結論")]:
        if not ctx["by_stage"].get(stage):
            unfilled.append(f"{stage}（{label}）")

    try:
        template = _jinja_env.get_template("quick_memo.html.j2")
        html = template.render(**ctx, unfilled_stages=unfilled)
    except Exception as e:
        return {"error": f"模板渲染失敗: {e}", "_reminders": []}

    report_id = f"memo-{uuid.uuid4().hex[:10]}"
    report_path = _report_path("memo", report_id)
    report_path.write_text(html, encoding="utf-8")

    await insert_report(report_id, session_id, "memo", str(report_path), unfilled)
    reminders = await get_active_reminders(session_id)

    return {
        "report_id": report_id,
        "report_type": "memo",
        "file_path": str(report_path),
        "unfilled_stages": unfilled,
        "total_records": len(ctx["all_records"]),
        "hash_count": len(ctx["hash_chain"]),
        "_reminders": format_reminders_for_response(reminders),
        "_note": f"報告已生成。{'部分欄位標示【⏳ 待確認】，請補充後重新生成。' if unfilled else '所有記錄已填入。'}",
    }


async def tool_generate_trace(session_id: str) -> dict:
    """
    【Report Type 2】Solution + Thinking Trace — 解決方案+思考軌跡（2 頁）
    
    輸出內容（嚴格來自 records，不推導）：
    Page 1: 問題定義 → 假設 → 求證 → 解法
    Page 2: 疑惑釐清 / 目前痛點 / 下次待解決 / 思考時間軸
    """
    session = await get_session(session_id)
    if not session:
        return {"error": f"找不到 session: {session_id}", "_reminders": []}

    ctx = await _build_context(session_id)
    unfilled = []

    for stage, label in [
        ("hypothesis", "假設對齊討論"),
        ("gitnexus_audit", "GitNexus 圖譜剖析"),
        ("tradeoff", "架構辯證"),
    ]:
        if not ctx["by_stage"].get(stage):
            unfilled.append(f"{stage}（{label}）")

    try:
        template = _jinja_env.get_template("solution_trace.html.j2")
        html = template.render(**ctx, unfilled_stages=unfilled)
    except Exception as e:
        return {"error": f"模板渲染失敗: {e}", "_reminders": []}

    report_id = f"trace-{uuid.uuid4().hex[:10]}"
    report_path = _report_path("trace", report_id)
    report_path.write_text(html, encoding="utf-8")

    await insert_report(report_id, session_id, "trace", str(report_path), unfilled)
    reminders = await get_active_reminders(session_id)

    return {
        "report_id": report_id,
        "report_type": "trace",
        "file_path": str(report_path),
        "unfilled_stages": unfilled,
        "total_records": len(ctx["all_records"]),
        "_reminders": format_reminders_for_response(reminders),
    }


async def tool_generate_full(session_id: str) -> dict:
    """
    【Report Type 3】Full Engineering Report — 完整工程報告（3 頁，含工程圖）
    
    輸出內容：
    Page 1: 訪談記錄 + 需求結論
    Page 2: 工程軌跡（Stage 01/02/03 完整記錄）+ 流程圖
    Page 3: 架構決策 + SystemGovernorResponse JSON + 行動清單 + SHA-256 防竄改鏈
    """
    session = await get_session(session_id)
    if not session:
        return {"error": f"找不到 session: {session_id}", "_reminders": []}

    ctx = await _build_context(session_id)
    unfilled = []

    # 全面檢查
    all_stages = [
        ("interview", "訪談記錄"),
        ("hypothesis", "假設對齊"),
        ("gitnexus_audit", "GitNexus 剖析"),
        ("tradeoff", "架構辯證"),
        ("conclusion", "需求結論"),
    ]
    for stage, label in all_stages:
        if not ctx["by_stage"].get(stage):
            unfilled.append(f"{stage}（{label}）")

    try:
        template = _jinja_env.get_template("full_report.html.j2")
        html = template.render(**ctx, unfilled_stages=unfilled)
    except Exception as e:
        return {"error": f"模板渲染失敗: {e}", "_reminders": []}

    report_id = f"full-{uuid.uuid4().hex[:10]}"
    report_path = _report_path("full", report_id)
    report_path.write_text(html, encoding="utf-8")

    await insert_report(report_id, session_id, "full", str(report_path), unfilled)
    reminders = await get_active_reminders(session_id)

    return {
        "report_id": report_id,
        "report_type": "full",
        "file_path": str(report_path),
        "unfilled_stages": unfilled,
        "total_records": len(ctx["all_records"]),
        "hash_chain_count": len(ctx["hash_chain"]),
        "_reminders": format_reminders_for_response(reminders),
        "_note": f"完整工程報告已生成於 {report_path}。{'有 ' + str(len(unfilled)) + ' 個階段缺少記錄。' if unfilled else '全部階段皆有記錄。'}",
    }
