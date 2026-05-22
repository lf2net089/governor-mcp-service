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
    """決策檔案庫網頁查看器"""
    sessions_data = []

    try:
        async with aiosqlite.connect(DB_PATH) as db:
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
    except Exception as e:
        print(f"❌ Database error: {e}")
        sessions_data = []

    html_content = _generate_archive_html(sessions_data)
    return web.Response(text=html_content, content_type="text/html", charset="utf-8")


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
        }

        .empty-state {
            text-align: center;
            padding: 40px 20px;
            color: #999;
            font-size: 14px;
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

            status_badge = "badge-active" if status == "active" else "badge-closed"

            html_parts.append(f"""
        <div class="session-card">
            <div class="session-header">
                <div>
                    <div class="session-title">{topic}</div>
                </div>
                <div class="session-meta">
                    <div>
                        <span class="badge {status_badge}">{status}</span>
                    </div>
                    <div>{created_at}</div>
                    <div style="font-size: 10px; color: #ccc; letter-spacing: 1px;">{sid}</div>
                </div>
            </div>
            <div class="section">
                <div class="section-title">📝 詳情</div>
                <p style="font-size: 13px; color: #555;">
                    已記錄 {len(session.get('records', []))} 筆記錄，
                    {len(session.get('stages', []))} 個工作流階段，
                    {len(session.get('reports', []))} 份報告
                </p>
            </div>
        </div>
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


async def start_web_server():
    """啟動網頁查看器服務"""
    app = web.Application()
    app.router.add_get('/health', handle_health)
    app.router.add_get('/archive', handle_archive)

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
