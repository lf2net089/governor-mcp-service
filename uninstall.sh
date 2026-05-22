#!/usr/bin/env bash
# ============================================================
# System Governor — 卸載腳本
# uninstall.sh
#
# 執行項目：
#   1. 停止並移除 Docker 容器
#   2. 選擇性移除 Docker Image
#   3. 從 mcp_config.json 移除 system-governor 條目
#   4. 選擇性清除 data 目錄（含 DB 與報告）
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MCP_SERVICE_DIR="$SCRIPT_DIR/mcp-service"
MCP_CONFIG="$HOME/.gemini/antigravity/mcp_config.json"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

info()    { echo -e "${CYAN}[INFO]${RESET} $*"; }
success() { echo -e "${GREEN}[✅]${RESET} $*"; }
warn()    { echo -e "${YELLOW}[⚠️]${RESET} $*"; }
confirm() {
  read -rp "$(echo -e "${YELLOW}$* [y/N]${RESET} ")" ans
  [[ "$ans" =~ ^[Yy]$ ]]
}

echo -e "${BOLD}"
echo "╔══════════════════════════════════════════════╗"
echo "║  System Governor MCP Service — Uninstaller  ║"
echo "╚══════════════════════════════════════════════╝"
echo -e "${RESET}"
warn "此操作將停止 System Governor MCP Service。"

confirm "確認繼續卸載？" || { echo "已取消。"; exit 0; }

# ── Step 1: 停止並移除 Docker 容器 ───────────────────────
info "Step 1 — 停止 Docker 容器..."
cd "$MCP_SERVICE_DIR" 2>/dev/null || { warn "找不到 mcp-service 目錄，跳過 Docker 操作。"; }

if docker ps -q --filter "name=system-governor-mcp" | grep -q .; then
  docker compose down
  success "容器已停止並移除"
else
  warn "容器未運行，跳過。"
fi

# ── Step 2: 選擇性移除 Docker Image ──────────────────────
if confirm "Step 2 — 是否同時移除 Docker Image（釋放磁碟空間）？"; then
  docker rmi mcp-service-system-governor-mcp 2>/dev/null && success "Image 已移除" || warn "Image 不存在或已移除"
else
  info "保留 Docker Image（下次安裝時可快速啟動）"
fi

# ── Step 3: 從 mcp_config.json 移除條目 ──────────────────
info "Step 3 — 從 mcp_config.json 移除 system-governor..."
if [ -f "$MCP_CONFIG" ] && grep -q '"system-governor"' "$MCP_CONFIG" 2>/dev/null; then
  cp "$MCP_CONFIG" "${MCP_CONFIG}.backup.$(date +%Y%m%d%H%M%S)"
  MCP_CONFIG_PATH="$MCP_CONFIG" python3 -c "
import json, os
p = os.environ['MCP_CONFIG_PATH']
with open(p) as f: c = json.load(f)
c.get('mcpServers', {}).pop('system-governor', None)
with open(p, 'w') as f: json.dump(c, f, indent=2, ensure_ascii=False); f.write('\n')
print('✅ system-governor 已從 mcp_config.json 移除')
" && success "mcp_config.json 已更新" || warn "自動移除失敗，請手動編輯 $MCP_CONFIG"
else
  warn "找不到 system-governor 條目，跳過。"
fi

# ── Step 4: 選擇性清除 data 目錄 ─────────────────────────
echo ""
warn "Step 4 — data 目錄包含 SQLite 資料庫與所有生成報告。"
warn "刪除後無法恢復！"
if confirm "是否清除 $MCP_SERVICE_DIR/data/ 目錄（含所有報告與 DB）？"; then
  rm -rf "$MCP_SERVICE_DIR/data/"
  success "data 目錄已清除"
else
  info "保留 data 目錄：$MCP_SERVICE_DIR/data/"
  info "DB 位置：$MCP_SERVICE_DIR/data/governor.db"
fi

echo ""
echo -e "${GREEN}${BOLD}"
echo "╔══════════════════════════════════════════════╗"
echo "║        ✅ 卸載完成                           ║"
echo "╚══════════════════════════════════════════════╝"
echo -e "${RESET}"
echo "   ⚠️  請重啟 Antigravity IDE 以移除 MCP 工具清單。"
echo "   📁 專案原始碼保留於: $SCRIPT_DIR"
echo "   🔄 重新安裝: bash install.sh"
echo ""
