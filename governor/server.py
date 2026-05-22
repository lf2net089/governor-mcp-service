"""
server.py — System Governor MCP Service 主入口
傳輸: HTTP/SSE (StreamableHTTP)，Port 9090
"""

import os
import asyncio
import json
import aiosqlite
from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Route
from starlette.middleware.cors import CORSMiddleware

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
PORT = int(os.environ.get("MCP_PORT", "9090"))

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

# ─── HTTP 端點處理 ──────────────────────────────────────────────────────────

async def handle_health(request):
    """健康檢查端點"""
    return JSONResponse({"status": "ok", "service": "system-governor-mcp", "tools": 15})


async def handle_archive(request):
    """決策檔案庫網頁查看器"""
    db_path = os.environ.get("DB_PATH", "/data/governor.db")

    # 查詢所有 sessions 及其相關數據
    sessions_data = []
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row

        # 取得所有 sessions
        async with db.execute("SELECT * FROM sessions ORDER BY created_at DESC") as cur:
            sessions = await cur.fetchall()

            for session in sessions:
                sid = session["id"]
                session_dict = dict(session)

                # 取得該 session 的 records
                async with db.execute(
                    "SELECT stage, role, content, created_at FROM records WHERE session_id=? ORDER BY created_at",
                    (sid,)
                ) as rec_cur:
                    records = await rec_cur.fetchall()
                    session_dict["records"] = [dict(r) for r in records]

                # 取得該 session 的 stage_progress
                async with db.execute(
                    "SELECT stage, status, completed_at FROM stage_progress WHERE session_id=? ORDER BY stage",
                    (sid,)
                ) as stage_cur:
                    stages = await stage_cur.fetchall()
                    session_dict["stages"] = [dict(s) for s in stages]

                # 取得該 session 的 reports
                async with db.execute(
                    "SELECT report_type, file_path, generated_at FROM reports WHERE session_id=? ORDER BY generated_at DESC",
                    (sid,)
                ) as rep_cur:
                    reports = await rep_cur.fetchall()
                    session_dict["reports"] = [dict(r) for r in reports]

                sessions_data.append(session_dict)

    # 生成 HTML
    html_content = _generate_archive_html(sessions_data)
    return HTMLResponse(content=html_content)


def _generate_archive_html(sessions_data):
    """生成歸檔查看器 HTML"""

    html_parts = [
        """<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>System Governor — 決策檔案庫</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft YaHei', sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }

        .container {
            max-width: 1000px;
            margin: 0 auto;
            padding: 40px 20px;
        }

        header {
            background: white;
            padding: 30px 0;
            margin-bottom: 40px;
            border-bottom: 2px solid #f0f0f0;
        }

        header h1 {
            font-size: 28px;
            font-weight: 600;
            margin-bottom: 8px;
            color: #222;
        }

        header p {
            font-size: 14px;
            color: #666;
        }

        .session-card {
            background: white;
            border-radius: 8px;
            padding: 24px;
            margin-bottom: 20px;
            border-left: 4px solid #0066cc;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }

        .session-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 16px;
            border-bottom: 1px solid #f0f0f0;
            padding-bottom: 12px;
        }

        .session-title {
            font-size: 18px;
            font-weight: 600;
            color: #222;
            flex: 1;
        }

        .session-meta {
            display: flex;
            gap: 16px;
            font-size: 12px;
            color: #999;
            text-align: right;
        }

        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 500;
        }

        .badge-active { background: #e8f5e9; color: #2e7d32; }
        .badge-closed { background: #f5f5f5; color: #666; }
        .badge-passed { background: #e3f2fd; color: #1565c0; }
        .badge-stage { background: #fff3e0; color: #e65100; padding: 2px 8px; }

        .section {
            margin-top: 20px;
        }

        .section-title {
            font-size: 13px;
            font-weight: 600;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .timeline {
            margin-left: 0;
            border-left: 2px solid #f0f0f0;
            padding-left: 16px;
        }

        .timeline-item {
            position: relative;
            margin-bottom: 16px;
            padding-bottom: 12px;
        }

        .timeline-item::before {
            content: '';
            position: absolute;
            left: -21px;
            top: 2px;
            width: 10px;
            height: 10px;
            background: #0066cc;
            border-radius: 50%;
            border: 2px solid white;
            box-shadow: 0 0 0 1px #f0f0f0;
        }

        .timeline-time {
            font-size: 11px;
            color: #999;
            margin-bottom: 4px;
        }

        .timeline-content {
            background: #fafafa;
            padding: 12px;
            border-radius: 4px;
            font-size: 13px;
            line-height: 1.5;
            color: #555;
            border-left: 2px solid #e0e0e0;
            word-break: break-word;
        }

        .timeline-stage {
            display: inline-block;
            margin-right: 8px;
            font-size: 11px;
        }

        .stage-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid #f5f5f5;
            font-size: 13px;
        }

        .stage-name {
            font-weight: 500;
            color: #222;
            flex: 1;
        }

        .reports-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 12px;
        }

        .report-link {
            display: block;
            padding: 12px;
            background: #f0f7ff;
            border: 1px solid #d0e8ff;
            border-radius: 6px;
            text-decoration: none;
            color: #0066cc;
            font-size: 12px;
            font-weight: 500;
            text-align: center;
            transition: all 0.2s;
        }

        .report-link:hover {
            background: #0066cc;
            color: white;
            border-color: #0066cc;
        }

        .empty-state {
            text-align: center;
            padding: 40px 20px;
            color: #999;
            font-size: 14px;
        }

        .stakeholders {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 8px;
        }

        .stakeholder-tag {
            display: inline-block;
            padding: 4px 12px;
            background: #f5f5f5;
            border-radius: 4px;
            font-size: 11px;
            color: #666;
        }

        footer {
            text-align: center;
            padding: 40px 0;
            font-size: 12px;
            color: #999;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📋 System Governor — 決策檔案庫</h1>
            <p>所有的架構決策與評估過程，一目瞭然</p>
        </header>
"""
    ]

    if not sessions_data:
        html_parts.append("""
        <div class="empty-state">
            <p>目前沒有任何決策記錄</p>
            <p style="margin-top: 12px; font-size: 12px; color: #ccc;">
                使用 Claude Code 或 Gemini Agent 開始你的第一個決策評估
            </p>
        </div>
""")
    else:
        for session in sessions_data:
            sid = session.get("id", "")
            topic = session.get("topic", "未命名")
            status = session.get("status", "active")
            created_at = session.get("created_at", "")[:19]
            stakeholders = json.loads(session.get("stakeholders", "[]")) if isinstance(session.get("stakeholders"), str) else session.get("stakeholders", [])

            status_badge = "badge-active" if status == "active" else "badge-closed"

            html_parts.append(f"""
        <div class="session-card">
            <div class="session-header">
                <div>
                    <div class="session-title">{topic}</div>
                    <div class="stakeholders">
""")

            if stakeholders:
                for sh in stakeholders:
                    html_parts.append(f'<span class="stakeholder-tag">{sh}</span>')

            html_parts.append(f"""
                    </div>
                </div>
                <div class="session-meta">
                    <div>
                        <span class="badge {status_badge}">{status}</span>
                    </div>
                    <div>{created_at}</div>
                    <div style="font-size: 10px; color: #ccc; letter-spacing: 1px;">{sid}</div>
                </div>
            </div>
""")

            # 顯示 records
            records = session.get("records", [])
            if records:
                html_parts.append("""
            <div class="section">
                <div class="section-title">💬 決策過程</div>
                <div class="timeline">
""")
                for rec in records:
                    stage = rec.get("stage", "")
                    role = rec.get("role", "")
                    content = rec.get("content", "")[:150]
                    rec_time = rec.get("created_at", "")[:19]

                    stage_color = {
                        "interview": "#0066cc",
                        "hypothesis": "#ff6b00",
                        "gitnexus_audit": "#6b21a8",
                        "tradeoff": "#d97706",
                        "conclusion": "#059669",
                        "memo": "#7c3aed"
                    }.get(stage, "#999")

                    html_parts.append(f"""
                    <div class="timeline-item">
                        <div class="timeline-time">{rec_time}</div>
                        <div style="margin-bottom: 4px;">
                            <span class="badge-stage" style="background: {stage_color}40; color: {stage_color};">{stage}</span>
                            <span style="font-size: 11px; color: #999;">({role})</span>
                        </div>
                        <div class="timeline-content">{content}...</div>
                    </div>
""")

                html_parts.append("""
                </div>
            </div>
""")

            # 顯示 stages 進度
            stages = session.get("stages", [])
            if stages:
                html_parts.append("""
            <div class="section">
                <div class="section-title">🎯 工作流進度</div>
""")
                stage_names = {
                    "01": "假設對齊驗證",
                    "02": "代碼影響分析",
                    "03": "架構辯證權衡"
                }
                for stage in stages:
                    st = stage.get("stage", "")
                    st_status = stage.get("status", "pending")
                    st_completed = stage.get("completed_at", "")[:10] if stage.get("completed_at") else "-"
                    st_name = stage_names.get(st, st)

                    status_color = {
                        "pending": "#999",
                        "in_progress": "#ff6b00",
                        "passed": "#059669",
                        "blocked": "#dc2626"
                    }.get(st_status, "#999")

                    html_parts.append(f"""
                <div class="stage-row">
                    <div class="stage-name">Stage {st}: {st_name}</div>
                    <div style="display: flex; gap: 12px; align-items: center;">
                        <span style="font-size: 11px; color: {status_color}; font-weight: 500;">{st_status.upper()}</span>
                        <span style="font-size: 11px; color: #999;">{st_completed}</span>
                    </div>
                </div>
""")

                html_parts.append("""
            </div>
""")

            # 顯示 reports
            reports = session.get("reports", [])
            if reports:
                html_parts.append("""
            <div class="section">
                <div class="section-title">📄 生成的報告</div>
                <div class="reports-grid">
""")
                report_labels = {
                    "memo": "Quick Memo",
                    "trace": "Solution Trace",
                    "full": "完整報告"
                }
                for rep in reports:
                    rep_type = rep.get("report_type", "")
                    rep_path = rep.get("file_path", "")
                    rep_label = report_labels.get(rep_type, rep_type)

                    html_parts.append(f"""
                    <a href="file://{rep_path}" class="report-link">
                        {rep_label}
                    </a>
""")

                html_parts.append("""
                </div>
            </div>
""")

            html_parts.append("</div>")

    html_parts.append("""
        <footer>
            <p>System Governor — 架構決策記錄與驗證系統</p>
            <p style="margin-top: 8px; font-size: 11px;">所有決策過程均原文存檔，防竄改驗證確保完整性</p>
        </footer>
    </div>
</body>
</html>
""")

    return "\n".join(html_parts)

# ─── Main ────────────────────────────────────────────────────────────────────

async def main():
    # 初始化 DB
    await init_db()
    print(f"✅ System Governor MCP Service 啟動中...")
    print(f"📡 HTTP/SSE: http://{HOST}:{PORT}")
    print(f"🏥 Health:   http://{HOST}:{PORT}/health")
    print(f"📊 Archive:  http://{HOST}:{PORT}/archive")
    print(f"🗄️  DB:      {os.environ.get('DB_PATH', '/data/governor.db')}")
    print(f"📁 Reports:  {os.environ.get('REPORTS_DIR', '/data/reports')}")

    # Run FastMCP HTTP server
    await mcp.run_http_async(host=HOST, port=PORT)


if __name__ == "__main__":
    asyncio.run(main())
