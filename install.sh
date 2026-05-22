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

# 從 .env 讀取 MCP_PORT，預設值為 9090
if [ -f "$SCRIPT_DIR/.env" ]; then
  MCP_PORT=$(grep "^MCP_PORT=" "$SCRIPT_DIR/.env" | cut -d'=' -f2 | xargs)
else
  MCP_PORT="9090"
fi
SERVICE_URL="http://localhost:$MCP_PORT"
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
# 載入 .env 環境變數
set -a
source "$SCRIPT_DIR/.env"
set +a
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
  echo "    \"url\": \"http://localhost:${MCP_PORT}/mcp\","
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
    "url": "http://localhost:$MCP_PORT/mcp",
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
c.setdefault('mcpServers', {})['system-governor'] = {'url': 'http://localhost:$MCP_PORT/mcp', 'disabled': False}
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
echo "   📡 可用端點："
echo "      MCP 工具:      ${SERVICE_URL}/mcp"
echo "      Health 檢查:   ${SERVICE_URL}/health"
echo "      決策檔案庫:    ${SERVICE_URL}/archive  ⭐ 新增"
echo ""
echo "   💾 數據存儲："
echo "      報告輸出:      $MCP_SERVICE_DIR/data/reports/"
echo "      資料庫:        $MCP_SERVICE_DIR/data/governor.db"
echo ""
echo "   ⚠️  下一步："
echo "      1. 重啟 Antigravity IDE 以載入新 MCP 工具"
echo "      2. 複製 Agent 規則到你的配置檔（見下方指南）"
echo "      3. 訪問 ${SERVICE_URL}/archive 查看決策檔案"
echo ""
echo "   📖 詳細文檔: $MCP_SERVICE_DIR/README.md"
echo ""

# ── Agent 自判斷與規則集成 ─────────────────────────────────
info "Agent 規則集成指南"
echo ""
echo "System Governor 可以自動介入架構決策。根據你使用的 Agent，"
echo "複製對應的規則模板到你的全域設定檔："
echo ""

CLAUDE_RULE_FILE="$HOME/.claude/CLAUDE.md"
GEMINI_RULE_FILE="$HOME/.gemini/GEMINI.md"
TEMPLATE_FILE="$SCRIPT_DIR/SYSTEM_GOVERNOR_RULE_TEMPLATE.md"

# 偵測當前環境
if [ -n "${VSCODE_PID:-}" ] || [ -n "${CLAUDE_CODE_CONTEXT:-}" ]; then
  DETECTED_AGENT="Claude Code"
  TARGET_RULE_FILE="$CLAUDE_RULE_FILE"
  AGENT_TYPE="claude-code"
elif [ -n "${ANTIGRAVITY_IDE:-}" ]; then
  DETECTED_AGENT="Gemini (Antigravity)"
  TARGET_RULE_FILE="$GEMINI_RULE_FILE"
  AGENT_TYPE="gemini"
else
  DETECTED_AGENT="未知（可能在終端執行）"
  TARGET_RULE_FILE=""
  AGENT_TYPE=""
fi

echo "   🤖 偵測到當前環境: ${BLUE}${DETECTED_AGENT}${RESET}"
echo ""

if [ -n "$AGENT_TYPE" ] && [ -f "$TEMPLATE_FILE" ]; then
  echo "   📋 設定步驟："
  echo ""
  echo "   1️⃣  打開規則模板："
  echo "       nano $TEMPLATE_FILE"
  echo ""

  if [ "$AGENT_TYPE" = "claude-code" ]; then
    echo "   2️⃣  複製「Rule 模板 — 複製到 CLAUDE.md」部分"
  else
    echo "   2️⃣  複製「Rule 模板 — 複製到 GEMINI.md」部分"
  fi

  echo ""
  echo "   3️⃣  粘貼到你的規則檔："
  echo "       nano $TARGET_RULE_FILE"
  echo "       （若檔案不存在，會自動建立）"
  echo ""
  echo "   4️⃣  驗證規則已加入："
  echo "       grep -i 'System Governor' $TARGET_RULE_FILE"
  echo ""

  if [ "$AGENT_TYPE" = "claude-code" ]; then
    echo "   ✅ 完成後，重新啟動 Claude Code 即可！"
  else
    echo "   ✅ 完成後，重新啟動 Antigravity IDE 即可！"
  fi
else
  echo "   📋 設定步驟："
  echo ""
  echo "   1️⃣  打開規則模板："
  echo "       nano $TEMPLATE_FILE"
  echo ""
  echo "   2️⃣  根據你使用的 Agent 類型，複製對應規則："
  echo "       • Claude Code  → 複製到 ~/.claude/CLAUDE.md"
  echo "       • Gemini       → 複製到 ~/.gemini/GEMINI.md"
  echo ""
  echo "   3️⃣  粘貼進對應檔案後重啟 IDE 即可。"
fi

echo ""
echo ""
echo "   📚 更多資訊："
echo "       • System Governor 文檔:        $SCRIPT_DIR/SYSTEM_GOVERNOR_RULE_TEMPLATE.md"
echo "       • 決策檔案庫指南:              在瀏覽器打開 ${SERVICE_URL}/archive"
echo "       • MCP 服務 README:             $MCP_SERVICE_DIR/README.md"
echo "       • Agent 自判斷指南:            ~/.claude/skills/system-governor-mcp-guide/AGENT_SELF_AWARENESS.md"
echo "       • Claude Code 整合說明:        $SCRIPT_DIR/CLAUDE_CODE_INTEGRATION.md"
echo ""
echo "   ⭐ 新功能提示："
echo "       決策檔案庫網頁查看器已就緒！"
echo "       • 訪問 ${SERVICE_URL}/archive 查看所有決策記錄"
echo "       • 完整的時間線、工作流進度、生成報告一覽無遺"
echo "       • 白色簡潔設計，易於分享給非專業人士"
echo ""
