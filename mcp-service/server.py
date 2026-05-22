"""
server.py — System Governor MCP Service 主入口
傳輸: HTTP/SSE (StreamableHTTP)，Port 8080
"""

import os
import asyncio
from contextlib import asynccontextmanager
from fastmcp import FastMCP

from core.db import init_db

from tools.session_tools import (
    tool_create_session, tool_get_session,
    tool_list_sessions, tool_close_session
)
from tools.record_tools import (
    tool_record_input, tool_check_reminders, tool_get_records
)
from tools.workflow_tools import (
    tool_run_stage_01, tool_run_stage_02,
    tool_run_stage_03, tool_get_workflow_status
)
from tools.skill_tools import tool_list_skills, tool_get_skill
from tools.report_tools import (
    tool_generate_memo, tool_generate_trace, tool_generate_full
)

HOST = os.environ.get("MCP_HOST", "0.0.0.0")
PORT = int(os.environ.get("MCP_PORT", "8080"))

# ─── FastMCP 實例 ────────────────────────────────────────────────────────────

mcp = FastMCP(
    name="system-governor",
    instructions="""
System Governor MCP — 知識圖譜驅動的系統治理服務。

核心原則：
1. 萬物皆可遲疑，合理求證，不輕易將就
2. 所有記錄來自使用者原始輸入，嚴禁推導補全
3. 空欄位只標示【⏳ 待確認】，嚴禁幻覺填充
4. 系統會主動提醒未記錄的討論（_reminders 欄位）

工具分類：
- Category A (session_*): 會話管理
- Category B (record_*): 原始輸入捕獲
- Category C (workflow_*): 三段式工作流
- Category D (skill_*): Skill 定義查詢
- Category E (report_*): 三種報告生成

⚠️ 重要：每個工具回應都包含 _reminders 欄位，請主動檢查並處理。
""",
)

# ─── Category A: Session ─────────────────────────────────────────────────────

@mcp.tool(description="建立新的 System Governor 工作階段。topic 為本次討論主題（使用者原始描述）。")
async def sg_create_session(topic: str, stakeholders: list[str] | None = None) -> dict:
    return await tool_create_session(topic, stakeholders)

@mcp.tool(description="取得指定 session 的詳情、狀態與待確認 Reminder。")
async def sg_get_session(session_id: str) -> dict:
    return await tool_get_session(session_id)

@mcp.tool(description="列出所有工作階段（依建立時間倒序）。")
async def sg_list_sessions() -> dict:
    return await tool_list_sessions()

@mcp.tool(description="標記工作階段為完成。關閉前建議先生成最終報告。")
async def sg_close_session(session_id: str) -> dict:
    return await tool_close_session(session_id)

# ─── Category B: Record (核心) ───────────────────────────────────────────────

@mcp.tool(description="""
【核心工具】將使用者原始文字原封不動存入資料庫（嚴禁 AI 修改或補全）。

stage 選項：
- interview: 訪談討論
- hypothesis: 假設對齊
- gitnexus_audit: GitNexus 圖譜剖析
- tradeoff: 架構辯證
- conclusion: 需求結論
- memo: 想法/備忘
- pain_point: 目前痛點
- next_session: 下次待解決
""")
async def sg_record_input(
    session_id: str,
    content: str,
    role: str = "user",
    stage: str = "interview",
    source_note: str | None = None,
) -> dict:
    return await tool_record_input(session_id, content, role, stage, source_note)

@mcp.tool(description="查詢目前所有待確認的 Reminder。acknowledge=true 時同時標記為已確認。")
async def sg_check_reminders(session_id: str, acknowledge: bool = False) -> dict:
    return await tool_check_reminders(session_id, acknowledge)

@mcp.tool(description="查詢指定 session 的原始記錄。可用 stage/role 篩選。")
async def sg_get_records(
    session_id: str,
    stage: str | None = None,
    role: str | None = None,
) -> dict:
    return await tool_get_records(session_id, stage, role)

# ─── Category C: Workflow ────────────────────────────────────────────────────

@mcp.tool(description="Stage 01 — 假設對齊門檻驗證（8 項 bool 檢查）。不通過則退回計劃階段。")
async def sg_run_stage_01(
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
    return await tool_run_stage_01(
        session_id, surface_requirement, actual_business_purpose,
        has_concrete_target, has_io_logic, has_reference,
        assumption_data_verified, assumption_performance_evaluated,
        assumption_dependencies_confirmed, boundary_null_defined,
        boundary_concurrency_considered,
    )

@mcp.tool(description="Stage 02 — GitNexus 圖譜剖析記錄。偵測到 hard code/UI 遮醜自動觸發 Strict Critic 拒絕。")
async def sg_run_stage_02(
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
    return await tool_run_stage_02(
        session_id, file_path, function_name, change_purpose,
        upstream_verification, downstream_impact,
        hardcode_detected, ui_hiding_detected, todo_hack_detected,
        follows_architecture, has_test_coverage,
    )

@mcp.tool(description="Stage 03 — 架構辯證，輸出完整 SystemGovernorResponse JSON。空欄位標示【⏳ 待確認】。")
async def sg_run_stage_03(
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
    return await tool_run_stage_03(
        session_id, blind_spot, upstream_verification, downstream_impact,
        option_a_immediate_cost, option_a_long_term_risk,
        option_b_implementation_cost, option_b_asset_value,
        system_reflection_question,
    )

@mcp.tool(description="查看三段工作流目前進度概覽（pending/in_progress/passed/blocked）。")
async def sg_get_workflow_status(session_id: str) -> dict:
    return await tool_get_workflow_status(session_id)

# ─── Category D: Skill ───────────────────────────────────────────────────────

@mcp.tool(description="列出所有可用的 System Governor Skill。")
async def sg_list_skills() -> dict:
    return await tool_list_skills()

@mcp.tool(description="取得指定 Skill 的完整 Markdown 定義原文。name 為 skill 檔名（不含 .md）。")
async def sg_get_skill(name: str) -> dict:
    return await tool_get_skill(name)

# ─── Category E: Report ──────────────────────────────────────────────────────

@mcp.tool(description="生成 Quick Memo 報告（1 頁）：需求確認/想法發想/存證。空欄位標示【⏳ 待確認】。")
async def sg_generate_memo(session_id: str) -> dict:
    return await tool_generate_memo(session_id)

@mcp.tool(description="生成 Solution Trace 報告（2 頁）：解決方案 + 思考軌跡 + 痛點 + 下次待解決。")
async def sg_generate_trace(session_id: str) -> dict:
    return await tool_generate_trace(session_id)

@mcp.tool(description="生成完整工程報告（3 頁，含工程圖）：訪談 + 工程軌跡 + 架構決策 + JSON + Hash 防竄改鏈。")
async def sg_generate_full(session_id: str) -> dict:
    return await tool_generate_full(session_id)

# ─── Health endpoint ─────────────────────────────────────────────────────────

@mcp.custom_route("/health", methods=["GET"])
async def handle_health(request):
    from starlette.responses import JSONResponse
    return JSONResponse({"status": "ok", "service": "system-governor-mcp", "tools": 15})

# ─── Main ────────────────────────────────────────────────────────────────────

async def main():
    # 初始化 DB
    await init_db()
    print(f"✅ System Governor MCP Service 啟動中...")
    print(f"📡 HTTP/SSE: http://{HOST}:{PORT}")
    print(f"🏥 Health:   http://{HOST}:{PORT}/health")
    print(f"🗄️  DB:      {os.environ.get('DB_PATH', '/data/governor.db')}")
    print(f"📁 Reports:  {os.environ.get('REPORTS_DIR', '/data/reports')}")

    # Run FastMCP HTTP server
    await mcp.run_http_async(host=HOST, port=PORT)


if __name__ == "__main__":
    asyncio.run(main())
