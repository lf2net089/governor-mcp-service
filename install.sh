#!/usr/bin/env bash
# ============================================================
# System Governor — 安裝腳本
# install.sh
#
# 執行項目：
#   1. 建立 data 目錄（Docker volume 掛載點）
#   2. 建立 Docker Image 並啟動服務
#   3. 等待健康檢查通過
#   4. 寫入 mcp_config.json（加入 system-governor 條目）
#   5. 驗證工具清單
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MCP_SERVICE_DIR="$SCRIPT_DIR/mcp-service"
MCP_CONFIG="$HOME/.gemini/antigravity/mcp_config.json"
SERVICE_URL="http://localhost:8080"
MAX_WAIT=60   # 最多等待 60 秒

# ── 顏色 ──────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

info()    { echo -e "${CYAN}[INFO]${RESET} $*"; }
success() { echo -e "${GREEN}[✅]${RESET} $*"; }
warn()    { echo -e "${YELLOW}[⚠️]${RESET} $*"; }
error()   { echo -e "${RED}[❌]${RESET} $*" >&2; exit 1; }

echo -e "${BOLD}"
echo "╔══════════════════════════════════════════════╗"
echo "║   System Governor MCP Service — Installer   ║"
echo "╚══════════════════════════════════════════════╝"
echo -e "${RESET}"

# ── 前置檢查 ──────────────────────────────────────────────
info "檢查前置依賴..."
command -v docker   >/dev/null 2>&1 || error "Docker 未安裝。請先安裝 Docker Desktop。"
command -v python3  >/dev/null 2>&1 || warn "python3 未找到（非必需，但建議安裝）"
success "前置依賴檢查通過"

# ── Step 1: 建立 data 目錄 ────────────────────────────────
info "Step 1/5 — 建立 data 目錄..."
mkdir -p "$MCP_SERVICE_DIR/data/reports/memo"
mkdir -p "$MCP_SERVICE_DIR/data/reports/traces"
mkdir -p "$MCP_SERVICE_DIR/data/reports/full"
success "data 目錄就緒：$MCP_SERVICE_DIR/data/"

# ── Step 2: 建立並啟動 Docker ─────────────────────────────
info "Step 2/5 — 建立 Docker Image（首次約需 2-3 分鐘）..."
cd "$MCP_SERVICE_DIR"
docker compose build --quiet
success "Docker Image 建立完成"

info "啟動服務..."
docker compose up -d
success "Docker 容器已啟動"

# ── Step 3: 健康檢查 ──────────────────────────────────────
info "Step 3/5 — 等待服務就緒（最多 ${MAX_WAIT}s）..."
elapsed=0
while true; do
  if curl -sf "${SERVICE_URL}/health" >/dev/null 2>&1; then
    success "服務健康檢查通過 ✅"
    break
  fi
  if [ $elapsed -ge $MAX_WAIT ]; then
    error "服務未在 ${MAX_WAIT}s 內啟動。請檢查：docker compose logs system-governor-mcp"
  fi
  printf "."
  sleep 2
  elapsed=$((elapsed + 2))
done
echo ""

# ── Step 4: 寫入 mcp_config.json ─────────────────────────
info "Step 4/5 — 寫入 Antigravity MCP 設定..."

if [ ! -f "$MCP_CONFIG" ]; then
  warn "找不到 $MCP_CONFIG，跳過自動寫入。請手動加入以下設定："
  echo ""
  echo '  "system-governor": {'
  echo '    "url": "http://localhost:8080/mcp",'
  echo '    "disabled": false'
  echo '  }'
  echo ""
else
  # 檢查是否已存在
  if grep -q '"system-governor"' "$MCP_CONFIG" 2>/dev/null; then
    warn "system-governor 已存在於 mcp_config.json，跳過（避免重複）。"
  else
    # 備份
    cp "$MCP_CONFIG" "${MCP_CONFIG}.backup.$(date +%Y%m%d%H%M%S)"
    # 用 Python 安全注入 JSON（避免手動字串拼接破壞格式）
    python3 - <<PYEOF
import json, sys

config_path = "$MCP_CONFIG"
with open(config_path, 'r') as f:
    config = json.load(f)

config.setdefault('mcpServers', {})['system-governor'] = {
    "url": "http://localhost:8080/mcp",
    "disabled": False
}

with open(config_path, 'w') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)
    f.write('\n')

print("✅ system-governor 已加入 mcp_config.json")
PYEOF
    # Shell 版本替換（若 python3 失敗的 fallback）
    MCP_CONFIG_PATH="$MCP_CONFIG" python3 -c "
import json, os, sys
p = os.environ['MCP_CONFIG_PATH']
with open(p) as f: c = json.load(f)
c.setdefault('mcpServers', {})['system-governor'] = {'url': 'http://localhost:8080/mcp', 'disabled': False}
with open(p, 'w') as f: json.dump(c, f, indent=2, ensure_ascii=False); f.write('\n')
print('✅ mcp_config.json 更新完成')
" 2>/dev/null || warn "自動寫入失敗，請手動加入（見上方說明）"
  fi
fi

# ── Step 5: 驗證 ─────────────────────────────────────────
info "Step 5/5 — 驗證服務端點..."
HEALTH=$(curl -sf "${SERVICE_URL}/health" 2>/dev/null || echo "{}")
echo "   Health: $HEALTH"

echo ""
echo -e "${GREEN}${BOLD}"
echo "╔══════════════════════════════════════════════╗"
echo "║         ✅ 安裝完成！                        ║"
echo "╚══════════════════════════════════════════════╝"
echo -e "${RESET}"
echo "   MCP 服務:    ${SERVICE_URL}/mcp"
echo "   Health 端點: ${SERVICE_URL}/health"
echo "   報告輸出:    $MCP_SERVICE_DIR/data/reports/"
echo "   DB 位置:     $MCP_SERVICE_DIR/data/governor.db"
echo ""
echo "   ⚠️  請重啟 Antigravity IDE 以載入新 MCP 工具。"
echo "   📖 詳細使用說明: $MCP_SERVICE_DIR/README.md"
echo ""
