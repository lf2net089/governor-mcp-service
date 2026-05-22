#!/usr/bin/env bash
# ============================================================
# System Governor — 卸載腳本（完整清除版本）
# uninstall.sh
#
# 執行項目：
#   1. 停止並移除 Docker 容器（含強制清除失敗項）
#   2. 選擇性移除 Docker Image（新舊版本）
#   3. 從 mcp_config.json 移除 system-governor 條目
#   4. 選擇性清除 data 目錄（含 DB 與報告）
#   5. 驗證清除結果
#
# 功能：
#   - 📋 多層次清除（docker compose down → 強制 kill → 驗證）
#   - 🔄 兼容舊版本（mcp-service-* 鏡像與容器）
#   - ✅ 完整驗證卸載結果
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MCP_SERVICE_DIR="$SCRIPT_DIR/governor"
MCP_CONFIG="$HOME/.gemini/antigravity/mcp_config.json"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

info()    { echo -e "${CYAN}[INFO]${RESET} $*"; }
success() { echo -e "${GREEN}[✅]${RESET} $*"; }
warn()    { echo -e "${YELLOW}[⚠️]${RESET} $*"; }
error()   { echo -e "${RED}[❌]${RESET} $*" >&2; exit 1; }
confirm() {
  read -rp "$(echo -e "${YELLOW}$* [y/N]${RESET} ")" ans
  [[ "$ans" =~ ^[Yy]$ ]]
}

echo -e "${BOLD}"
echo "╔════════════════════════════════════════════════════╗"
echo "║  System Governor — 完整卸載工具                   ║"
echo "║  支援多層次清除與舊版本相容                         ║"
echo "╚════════════════════════════════════════════════════╝"
echo -e "${RESET}"
warn "此操作將完整移除 System Governor MCP Service 的所有資料與容器。"

confirm "確認繼續卸載？" || { echo "已取消。"; exit 0; }

# ── Step 1: 停止並移除 Docker 容器（含強制清除） ────────────
info "Step 1/5 — 停止 Docker 容器..."

# 1.1 嘗試用 docker compose 優雅關閉
if [ -d "$MCP_SERVICE_DIR" ]; then
  cd "$MCP_SERVICE_DIR" 2>/dev/null && docker compose down 2>/dev/null && success "docker compose 關閉成功" || warn "docker compose 關閉失敗或不存在"
else
  warn "governor 目錄不存在，跳過 docker compose 操作"
fi

# 1.2 強制停止新版本容器
if docker ps -q --filter "name=system-governor-mcp" | grep -q .; then
  info "強制停止容器 system-governor-mcp..."
  docker kill system-governor-mcp 2>/dev/null && success "容器已強制停止" || warn "無法停止容器"
  docker rm -f system-governor-mcp 2>/dev/null && success "容器已移除" || warn "無法移除容器"
fi

# 1.3 清除舊版本容器（mcp-service-* 命名）
if docker ps -a -q --filter "name=mcp-service-system-governor-mcp" | grep -q .; then
  info "清除舊版本容器 mcp-service-system-governor-mcp..."
  docker kill mcp-service-system-governor-mcp 2>/dev/null || true
  docker rm -f mcp-service-system-governor-mcp 2>/dev/null && success "舊版本容器已移除" || warn "舊版本容器清除失敗"
fi

success "所有容器已停止並清除"

# ── Step 2: 選擇性移除 Docker Image ───────────────────────
if confirm "Step 2/5 — 是否移除 Docker Image（釋放磁碟空間，~500MB）？"; then
  info "移除 Docker Image..."

  # 2.1 移除新版本鏡像
  docker rmi governor-system-governor-mcp 2>/dev/null && success "governor-system-governor-mcp 已移除" || info "鏡像不存在或已移除"

  # 2.2 移除舊版本鏡像（帶 latest tag）
  docker rmi mcp-service-system-governor-mcp:latest 2>/dev/null && success "mcp-service-system-governor-mcp:latest 已移除" || info "舊版本鏡像不存在"

  # 2.3 移除測試鏡像
  docker rmi system-governor:test 2>/dev/null && success "system-governor:test 已移除" || info "測試鏡像不存在"

  success "Image 清除完成"
else
  info "保留 Docker Image（下次安裝時可快速啟動）"
fi

# ── Step 3: 從 mcp_config.json 移除條目 ──────────────────
info "Step 3/5 — 清理 MCP 配置..."
if [ -f "$MCP_CONFIG" ] && grep -q '"system-governor"' "$MCP_CONFIG" 2>/dev/null; then
  cp "$MCP_CONFIG" "${MCP_CONFIG}.backup.$(date +%Y%m%d%H%M%S)"
  info "已備份至: ${MCP_CONFIG}.backup.*"

  MCP_CONFIG_PATH="$MCP_CONFIG" python3 - <<PYEOF 2>/dev/null
import json, os
p = os.environ['MCP_CONFIG_PATH']
with open(p) as f: c = json.load(f)
c.get('mcpServers', {}).pop('system-governor', None)
with open(p, 'w') as f: json.dump(c, f, indent=2, ensure_ascii=False); f.write('\n')
PYEOF
  success "system-governor 已從 mcp_config.json 移除"
else
  warn "找不到 system-governor 條目，跳過"
fi

# ── Step 4: 選擇性清除 data 目錄 ────────────────────────
echo ""
info "Step 4/5 — 清除決策記錄與報告..."
warn "data 目錄包含 SQLite 資料庫與所有生成報告（無法恢復）"
if confirm "是否清除 governor/data/ 目錄？"; then
  if [ -d "$MCP_SERVICE_DIR/data" ]; then
    rm -rf "$MCP_SERVICE_DIR/data"
    success "data 目錄已清除"
  else
    info "data 目錄不存在，跳過"
  fi
else
  info "保留 data 目錄"
  info "   DB 位置：$MCP_SERVICE_DIR/data/governor.db"
  info "   報告位置：$MCP_SERVICE_DIR/data/reports/"
fi

# ── Step 5: 驗證卸載結果 ────────────────────────────────
info "Step 5/5 — 驗證卸載結果..."
echo ""

# 5.1 檢查容器
if docker ps -q --filter "name=governor" | grep -q .; then
  warn "❌ 仍有運行的 governor 容器"
  docker ps --filter "name=governor"
else
  success "✅ 無運行的容器"
fi

# 5.2 檢查鏡像
if docker images --format "{{.Repository}}" | grep -E "governor|mcp-service" | grep -q .; then
  warn "❌ 仍有相關 Docker 鏡像（可手動清除：docker rmi <image-id>）"
else
  success "✅ 無相關 Docker 鏡像"
fi

# 5.3 檢查 data 目錄
if [ -d "$MCP_SERVICE_DIR/data" ]; then
  warn "⚠️  data 目錄仍存在"
else
  success "✅ data 目錄已清除"
fi

# 5.4 檢查 MCP 配置
if grep -q '"system-governor"' "$MCP_CONFIG" 2>/dev/null; then
  warn "⚠️  system-governor 仍在 mcp_config.json 中"
else
  success "✅ MCP 配置已清除"
fi

# 5.5 檢查服務健康狀態
if curl -s --connect-timeout 2 http://localhost:9090/health 2>/dev/null | grep -q "ok"; then
  warn "⚠️  服務仍在運行"
else
  success "✅ 服務無法連線（已停止）"
fi

echo ""
echo -e "${GREEN}${BOLD}"
echo "╔════════════════════════════════════════════════════╗"
echo "║           ✅ 卸載完成                             ║"
echo "╚════════════════════════════════════════════════════╝"
echo -e "${RESET}"
echo "   📝 MCP 配置已備份：${MCP_CONFIG}.backup.*"
echo "   ⚠️  請重啟 Antigravity IDE 以移除 MCP 工具清單"
echo "   📁 原始碼保留於：$SCRIPT_DIR"
echo "   🔄 重新安裝命令：bash install.sh"
echo "   🐳 快速啟動命令：cd dist && docker compose up"
echo ""
