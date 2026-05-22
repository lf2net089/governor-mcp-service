#!/bin/bash
# entrypoint.sh — 啟動 System Governor 的所有服務

set -e

echo "🚀 System Governor 啟動腳本"

# 啟動 Web Viewer（在背景）
echo "啟動 Web Viewer 服務..."
python web_viewer.py &
WEB_VIEWER_PID=$!

# 啟動 FastMCP（在前景）
echo "啟動 FastMCP 服務..."
python server.py

# 清理
kill $WEB_VIEWER_PID 2>/dev/null || true
