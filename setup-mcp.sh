#!/bin/bash
# System Governor — MCP 自動配置腳本
# 在 Claude Code 安裝過程中自動配置 MCP 服務

set -euo pipefail

echo "🔧 System Governor — MCP 自動配置"
echo "═══════════════════════════════════════════"

# 檢查 settings.json 路徑
SETTINGS_FILE="$HOME/.claude/settings.json"

if [ ! -f "$SETTINGS_FILE" ]; then
    echo "❌ 找不到 $SETTINGS_FILE"
    echo "   請確保已安裝 Claude Code"
    exit 1
fi

# 備份原始文件
BACKUP_FILE="$SETTINGS_FILE.backup.$(date +%Y%m%d%H%M%S)"
cp "$SETTINGS_FILE" "$BACKUP_FILE"
echo "✓ 已備份設定到: $BACKUP_FILE"

# 使用 Python 添加 MCP 配置
python3 << EOF
import json
import sys

try:
    settings_file = "$SETTINGS_FILE"

    # 讀取設定
    with open(settings_file, 'r') as f:
        settings = json.load(f)

    # 初始化 mcpServers
    if 'mcpServers' not in settings:
        settings['mcpServers'] = {}

    # 添加 System Governor MCP 服務
    settings['mcpServers']['system-governor'] = {
        "url": "http://localhost:9090/mcp",
        "disabled": False
    }

    # 寫回設定
    with open(settings_file, 'w') as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)

    print("✅ MCP 配置已添加")
    print("   Service: system-governor")
    print("   URL: http://localhost:9090/mcp")

except Exception as e:
    print(f"❌ 配置失敗: {e}")
    sys.exit(1)
EOF

echo ""
echo "═══════════════════════════════════════════"
echo "⚠️  接下來的步驟："
echo ""
echo "1️⃣  重啟 Claude Code"
echo "    - 完全關閉 Claude Code"
echo "    - 重新打開應用"
echo ""
echo "2️⃣  驗證 MCP 工具"
echo "    - 打開對話框"
echo "    - System Governor 的 15 個工具應該出現在工具清單中"
echo ""
echo "3️⃣  開始使用"
echo "    - 提問關於架構決策的問題"
echo "    - Claude 會自動使用 MCP 工具記錄決策過程"
echo ""
echo "═══════════════════════════════════════════"
echo "✨ MCP 配置完成！"
