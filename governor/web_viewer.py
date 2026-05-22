"""
web_viewer.py — System Governor 網頁查看器
獨立的 HTTP 服務，提供 /health 和 /archive 端點
"""

import os
import json
import asyncio
import aiosqlite
from aiohttp import web

DB_PATH = os.environ.get("DB_PATH", "/data/governor.db")


async def handle_health(request):
    """健康檢查端點"""
    return web.json_response({
        "status": "ok",
        "service": "system-governor-web-viewer",
        "endpoints": ["health", "archive"]
    })


async def handle_archive(request):
    """決策檔案庫主頁 — 列表視圖"""
    sessions_data = []

    try:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row

            # 取得所有 sessions（只取摘要，不取詳細記錄）
            async with db.execute("SELECT * FROM sessions ORDER BY created_at DESC") as cur:
                sessions = await cur.fetchall()

                for session in sessions:
                    sid = session["id"]
                    session_dict = dict(session)

                    # 只取統計數據
                    async with db.execute(
                        "SELECT COUNT(*) as cnt FROM records WHERE session_id=?", (sid,)
                    ) as cnt_cur:
                        session_dict["record_count"] = (await cnt_cur.fetchone())['cnt']

                    async with db.execute(
                        "SELECT COUNT(*) as cnt FROM stage_progress WHERE session_id=?", (sid,)
                    ) as cnt_cur:
                        session_dict["stage_count"] = (await cnt_cur.fetchone())['cnt']

                    async with db.execute(
                        "SELECT COUNT(*) as cnt FROM stage_progress WHERE session_id=? AND status='completed'", (sid,)
                    ) as cnt_cur:
                        session_dict["completed_stage_count"] = (await cnt_cur.fetchone())['cnt']

                    async with db.execute(
                        "SELECT COUNT(*) as cnt FROM reports WHERE session_id=?", (sid,)
                    ) as cnt_cur:
                        session_dict["report_count"] = (await cnt_cur.fetchone())['cnt']

                    sessions_data.append(session_dict)
    except Exception as e:
        print(f"❌ Database error: {e}")
        sessions_data = []

    html_content = _generate_archive_html(sessions_data)
    return web.Response(text=html_content, content_type="text/html", charset="utf-8")


async def handle_session_detail(request):
    """Session 詳細頁面 — 完整的決策流程檢視"""
    session_id = request.match_info.get('session_id')
    session_data = None

    try:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row

            # 取得 session
            async with db.execute("SELECT * FROM sessions WHERE id=?", (session_id,)) as cur:
                session_data = await cur.fetchone()

            if not session_data:
                return web.Response(text="<h1>404 - Session 不存在</h1>",
                                   content_type="text/html", status=404, charset="utf-8")

            session_dict = dict(session_data)

            # 取得詳細記錄
            async with db.execute(
                "SELECT role, content, created_at FROM records WHERE session_id=? ORDER BY created_at",
                (session_id,)
            ) as rec_cur:
                records = await rec_cur.fetchall()
                session_dict["records"] = [dict(r) for r in records]

            # 取得階段進度
            async with db.execute(
                "SELECT stage, status, completed_at FROM stage_progress WHERE session_id=? ORDER BY stage",
                (session_id,)
            ) as stage_cur:
                stages = await stage_cur.fetchall()
                session_dict["stages"] = [dict(s) for s in stages]

            # 取得報告
            async with db.execute(
                "SELECT report_type, file_path, generated_at FROM reports WHERE session_id=? ORDER BY generated_at DESC",
                (session_id,)
            ) as rep_cur:
                reports = await rep_cur.fetchall()
                session_dict["reports"] = [dict(r) for r in reports]

    except Exception as e:
        print(f"❌ Database error: {e}")
        return web.Response(text=f"<h1>Error - {str(e)}</h1>",
                           content_type="text/html", status=500, charset="utf-8")

    html_content = _generate_session_detail_html(session_dict)
    return web.Response(text=html_content, content_type="text/html", charset="utf-8")


def _get_status_display(status):
    """將狀態轉換為中文顯示"""
    status_map = {
        'active': '進行中',
        'closed': '已關閉',
        'archived': '已歸檔',
    }
    return status_map.get(status, status)


def _generate_archive_html(sessions_data):
    """生成決策檔案庫主頁 HTML"""

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
            background: #f5f5f7;
            color: #333;
            line-height: 1.6;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 40px 20px;
        }

        header {
            background: white;
            padding: 32px 0;
            margin-bottom: 32px;
            border-bottom: 1px solid #e5e5e5;
        }

        header h1 {
            font-size: 28px;
            font-weight: 600;
            margin-bottom: 8px;
            color: #000;
        }

        header p {
            font-size: 14px;
            color: #666;
        }

        .session-card {
            background: white;
            border-radius: 8px;
            margin-bottom: 16px;
            border: 1px solid #e5e5e5;
            overflow: hidden;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .session-card:hover {
            border-color: #0066cc;
            box-shadow: 0 2px 8px rgba(0, 102, 204, 0.1);
        }

        .session-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 24px;
            border-left: 4px solid #0066cc;
            background: #fafafa;
        }

        .session-title {
            font-size: 16px;
            font-weight: 600;
            color: #000;
            flex: 1;
        }

        .session-stats {
            display: flex;
            gap: 24px;
            margin-left: 20px;
            padding-left: 20px;
            border-left: 1px solid #e5e5e5;
            font-size: 13px;
            color: #666;
        }

        .stat-item {
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .stat-value {
            font-weight: 600;
            color: #0066cc;
        }

        .session-meta {
            display: flex;
            gap: 12px;
            align-items: center;
            font-size: 12px;
            color: #999;
            margin-left: auto;
        }

        .badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
        }

        .badge-active { background: #e8f5e9; color: #2e7d32; }
        .badge-closed { background: #f5f5f5; color: #666; }

        .toggle-icon {
            width: 20px;
            height: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #0066cc;
            font-size: 12px;
            transition: transform 0.2s ease;
        }

        .session-card.expanded .toggle-icon {
            transform: rotate(180deg);
        }

        .session-detail {
            display: none;
            padding: 0 24px 24px 24px;
            border-top: 1px solid #f0f0f0;
        }

        .session-card.expanded .session-detail {
            display: block;
        }

        .detail-section {
            margin-top: 20px;
        }

        .detail-section:first-child {
            margin-top: 0;
        }

        .section-title {
            font-size: 12px;
            font-weight: 700;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 12px;
        }

        .record-item {
            padding: 12px;
            background: #f9f9f9;
            border-radius: 4px;
            margin-bottom: 10px;
            border-left: 3px solid #0066cc;
            font-size: 13px;
        }

        .record-meta {
            display: flex;
            gap: 12px;
            margin-bottom: 8px;
            font-size: 11px;
            color: #999;
        }

        .record-role {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 10px;
            border-radius: 4px;
            font-weight: 600;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .record-role.user {
            background: #fff3e0;
            color: #e65100;
        }

        .record-role.assistant {
            background: #e8f5e9;
            color: #2e7d32;
        }

        .record-role::before {
            display: inline-block;
            width: 20px;
            height: 20px;
            font-size: 14px;
            text-align: center;
        }

        .record-role.user::before {
            content: "👤";
        }

        .record-role.assistant::before {
            content: "🤖";
        }

        .record-content {
            color: #333;
            line-height: 1.5;
            word-break: break-word;
        }

        .stage-progress {
            margin-bottom: 16px;
        }

        .progress-bar {
            height: 6px;
            background: #e5e5e5;
            border-radius: 3px;
            overflow: hidden;
            margin-bottom: 8px;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #0066cc, #0052a3);
            border-radius: 3px;
        }

        .progress-label {
            display: flex;
            justify-content: space-between;
            font-size: 12px;
            color: #666;
        }

        .stage-item {
            display: flex;
            align-items: center;
            padding: 8px 12px;
            background: #f9f9f9;
            border-radius: 4px;
            margin-bottom: 8px;
            font-size: 13px;
        }

        .stage-status {
            width: 16px;
            height: 16px;
            border-radius: 50%;
            margin-right: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 10px;
            color: white;
        }

        .stage-status.completed {
            background: #2e7d32;
        }

        .stage-status.pending {
            background: #999;
        }

        .report-item {
            padding: 10px 12px;
            background: #fff8e1;
            border-radius: 4px;
            border-left: 3px solid #f57f17;
            margin-bottom: 8px;
            font-size: 13px;
        }

        .report-type {
            font-weight: 600;
            color: #f57f17;
        }

        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #999;
            font-size: 14px;
        }

        footer {
            text-align: center;
            padding: 40px 0;
            font-size: 12px;
            color: #999;
            border-top: 1px solid #e5e5e5;
            margin-top: 40px;
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
            record_count = session.get('record_count', 0)
            stage_count = session.get('stage_count', 0)
            completed_stage_count = session.get('completed_stage_count', 0)
            report_count = session.get('report_count', 0)

            status_cn = _get_status_display(status)
            status_badge = "badge-active" if status == "active" else "badge-closed"

            # 計算進度百分比
            progress_pct = (completed_stage_count / stage_count * 100) if stage_count > 0 else 0

            # 報告統計（隱藏為0的報告）
            report_display = f'<div class="stat-item">📊 <span class="stat-value">{report_count}</span> 份報告</div>' if report_count > 0 else ''

            html_parts.append(f"""
        <a href="/archive/session/{sid}" style="text-decoration: none; color: inherit;">
            <div class="session-card">
                <div class="session-header">
                    <div class="session-title">{topic}</div>
                    <div class="session-stats">
                        <div class="stat-item">📝 <span class="stat-value">{record_count}</span> 筆記錄</div>
                        <div class="stat-item">🔄 <span class="stat-value">{completed_stage_count}/{stage_count}</span> 階段</div>
                        {report_display}
                    </div>
                    <div class="session-meta">
                        <span class="badge {status_badge}">{status_cn}</span>
                        <span>{created_at}</span>
                        <div class="toggle-icon">→</div>
                    </div>
                </div>
            </div>
        </a>
""")

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


def _generate_session_detail_html(session_data):
    """生成 Session 詳細頁面 HTML"""

    html_parts = [
        """<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>決策流程 — System Governor</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft YaHei', sans-serif;
            background: #f5f5f7;
            color: #333;
            line-height: 1.6;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 40px 20px;
        }

        header {
            background: white;
            padding: 32px 0;
            margin-bottom: 32px;
            border-bottom: 1px solid #e5e5e5;
        }

        header h1 {
            font-size: 28px;
            font-weight: 600;
            margin-bottom: 8px;
            color: #000;
        }

        header p {
            font-size: 14px;
            color: #666;
        }

        .back-link {
            display: inline-block;
            margin-bottom: 16px;
            color: #0066cc;
            text-decoration: none;
            font-size: 14px;
        }

        .back-link:hover {
            text-decoration: underline;
        }

        .content {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
        }

        .section {
            background: white;
            border-radius: 8px;
            padding: 24px;
            border: 1px solid #e5e5e5;
        }

        .section-title {
            font-size: 14px;
            font-weight: 700;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 2px solid #0066cc;
        }

        .progress-box {
            padding: 20px;
            background: #f9f9f9;
            border-radius: 6px;
            margin-bottom: 20px;
        }

        .progress-bar {
            height: 8px;
            background: #e5e5e5;
            border-radius: 4px;
            overflow: hidden;
            margin-bottom: 12px;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #0066cc, #0052a3);
        }

        .progress-text {
            display: flex;
            justify-content: space-between;
            font-size: 13px;
            color: #666;
            font-weight: 600;
        }

        .stage-list {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .stage-item {
            display: flex;
            align-items: center;
            padding: 10px 12px;
            background: #f9f9f9;
            border-radius: 4px;
            border-left: 3px solid #0066cc;
            font-size: 13px;
        }

        .stage-status {
            width: 20px;
            height: 20px;
            border-radius: 50%;
            margin-right: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 11px;
            color: white;
            flex-shrink: 0;
        }

        .stage-status.completed {
            background: #2e7d32;
        }

        .stage-status.pending {
            background: #999;
        }

        .records-section {
            grid-column: 1 / -1;
        }

        .record-item {
            padding: 16px;
            background: #f9f9f9;
            border-radius: 6px;
            margin-bottom: 12px;
            border-left: 4px solid #0066cc;
        }

        .record-meta {
            display: flex;
            gap: 12px;
            margin-bottom: 10px;
            font-size: 12px;
            color: #999;
            align-items: center;
        }

        .record-role {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 4px 10px;
            border-radius: 4px;
            font-weight: 600;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .record-role.user {
            background: #fff3e0;
            color: #e65100;
        }

        .record-role.assistant {
            background: #e8f5e9;
            color: #2e7d32;
        }

        .record-role::before {
            display: inline-block;
            font-size: 14px;
        }

        .record-role.user::before {
            content: "👤";
        }

        .record-role.assistant::before {
            content: "🤖";
        }

        .record-content {
            color: #333;
            font-size: 13px;
            line-height: 1.6;
            white-space: pre-wrap;
            word-break: break-word;
        }

        footer {
            text-align: center;
            padding: 40px 0;
            font-size: 12px;
            color: #999;
            border-top: 1px solid #e5e5e5;
            margin-top: 40px;
        }

        .empty-section {
            color: #999;
            font-size: 13px;
            padding: 20px;
            text-align: center;
            background: #f9f9f9;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <div class="container">
        <a href="/archive" class="back-link">← 返回檔案庫</a>
        <header>
            <h1>📋 {session_data.get("topic", "未命名")}</h1>
            <p>完整的決策流程與評估過程</p>
        </header>

        <div class="content">
"""
    ]

    records = session_data.get('records', [])
    stages = session_data.get('stages', [])
    reports = session_data.get('reports', [])

    # 進度面板
    total_stages = len(stages)
    completed_stages = sum(1 for s in stages if s.get('status') == 'completed')
    progress_pct = (completed_stages / total_stages * 100) if total_stages > 0 else 0

    status_cn = _get_status_display(session_data.get('status', 'active'))

    html_parts.append(f"""
            <div class="section">
                <div class="section-title">決策狀態</div>
                <div class="progress-box">
                    <div style="margin-bottom: 16px;">
                        <span style="font-weight: 600; font-size: 14px;">進度</span>
                        <span style="float: right; color: #0066cc; font-weight: 600;">{completed_stages}/{total_stages}</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {progress_pct}%"></div>
                    </div>
                    <div class="progress-text">
                        <span>{completed_stages}/{total_stages} 完成</span>
                        <span>{progress_pct:.0f}%</span>
                    </div>
                </div>

                <div style="padding: 12px; background: #f0f7ff; border-radius: 4px; margin-bottom: 16px;">
                    <div style="font-size: 12px; color: #0066cc; font-weight: 600;">狀態：{status_cn}</div>
                </div>

                <div class="section-title" style="border-bottom: 2px solid #0066cc; margin-top: 20px;">工作流階段</div>
                <div class="stage-list">
""")

    for stage in stages:
        stage_name = stage.get('stage', '未知')
        stage_status = stage.get('status', 'pending')
        status_icon = '✓' if stage_status == 'completed' else '○'
        status_class = 'completed' if stage_status == 'completed' else 'pending'

        html_parts.append(f"""
                    <div class="stage-item">
                        <div class="stage-status {status_class}">{status_icon}</div>
                        <span>{stage_name.upper()}</span>
                    </div>
""")

    html_parts.append("""
                </div>
            </div>

            <div class="section">
                <div class="section-title">相關資訊</div>
""")

    # 報告區域
    if reports:
        html_parts.append("""
                <div style="margin-bottom: 20px;">
                    <h4 style="font-size: 12px; color: #666; margin-bottom: 8px;">📄 生成報告</h4>
""")
        for report in reports:
            report_type = report.get('report_type', '未知')
            file_path = report.get('file_path', '')
            generated_at = report.get('generated_at', '')[:19]
            html_parts.append(f"""
                    <div style="padding: 8px; background: #fff8e1; border-radius: 3px; margin-bottom: 6px; font-size: 12px;">
                        <strong>{report_type}</strong><br/>
                        <span style="color: #999;">{file_path}</span><br/>
                        <span style="color: #ccc; font-size: 11px;">{generated_at}</span>
                    </div>
""")
        html_parts.append("""
                </div>
""")
    else:
        html_parts.append("""
                <div class="empty-section">尚未生成報告</div>
""")

    html_parts.append(f"""
                <div style="margin-top: 16px; padding-top: 16px; border-top: 1px solid #e5e5e5;">
                    <p style="font-size: 12px; color: #999;">
                        📝 <strong>{len(records)}</strong> 筆決策記錄<br/>
                        🔄 <strong>{completed_stages}/{total_stages}</strong> 階段完成<br/>
                        ✓ 所有決策已被系統記錄並防竄改驗證
                    </p>
                </div>
            </div>

            <div class="section records-section">
                <div class="section-title">決策過程 — 完整文字記錄</div>
""")

    if records:
        for i, record in enumerate(records, 1):
            role = record.get('role', 'system')
            content = record.get('content', '')
            created = record.get('created_at', '')[:19]

            # 角色標籤
            role_map = {
                'user': '使用者',
                'assistant': '分析助手',
                'system': '系統',
                'analyst': '分析師',
                'architect': '架構師',
                'judge': '評審者'
            }
            role_cn = role_map.get(role, role)
            role_class = role if role in ['user', 'assistant'] else 'assistant'

            html_parts.append(f"""
                <div class="record-item">
                    <div class="record-meta">
                        <span class="record-role {role_class}">{role_cn}</span>
                        <span style="color: #999;">{created}</span>
                    </div>
                    <div class="record-content">{content}</div>
                </div>
""")
    else:
        html_parts.append("""
                <div class="empty-section">暫無決策記錄</div>
""")

    html_parts.append("""
            </div>
        </div>

        <footer>
            <p>System Governor — 架構決策記錄與驗證系統</p>
            <p style="margin-top: 8px; font-size: 11px;">所有決策過程均原文存檔，防竄改驗證確保完整性</p>
        </footer>
    </div>
</body>
</html>
""")

    return "\n".join(html_parts)


async def start_web_server():
    """啟動網頁查看器服務"""
    app = web.Application()
    app.router.add_get('/health', handle_health)
    app.router.add_get('/archive', handle_archive)
    app.router.add_get('/archive/session/{session_id}', handle_session_detail)

    runner = web.AppRunner(app)
    await runner.setup()

    # 在 9091 端口運行（不與 FastMCP 的 9090 衝突）
    site = web.TCPSite(runner, '0.0.0.0', 9091)
    await site.start()

    print("✅ Web Viewer Service 啟動在 http://0.0.0.0:9091")
    print("   /health: 健康檢查")
    print("   /archive: 決策檔案庫")

    # 保持運行
    await asyncio.Event().wait()


if __name__ == '__main__':
    print("🌐 System Governor Web Viewer 啟動中...")
    asyncio.run(start_web_server())
