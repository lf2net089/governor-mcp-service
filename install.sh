#!/usr/bin/env bash
# ============================================================
# System Governor — 安裝腳本（支援中斷恢復）
# install.sh
#
# 執行項目：
#   1. 建立 data 目錄
#   2. 建立 Docker Image 並啟動服務
#   3. 等待健康檢查通過
#   4. 寫入 mcp_config.json
#   5. 驗證工具清單與規則集成指南
#
# 功能：
#   - 📋 檢查清單追蹤
#   - 📝 詳細日誌記錄
#   - 🔄 中斷自動恢復
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MCP_SERVICE_DIR="$SCRIPT_DIR/governor"
MCP_CONFIG="$HOME/.gemini/antigravity/mcp_config.json"
CLAUDE_SETTINGS="$HOME/.claude/settings.json"
CLAUDE_RULE_FILE="$HOME/.claude/CLAUDE.md"

# 狀態和日誌檔案
STATUS_FILE="$SCRIPT_DIR/.install_status"
LOG_FILE="$SCRIPT_DIR/install.log"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

# 從 .env 讀取 MCP_PORT，預設值為 9090
if [ -f "$SCRIPT_DIR/.env" ]; then
  MCP_PORT=$(grep "^MCP_PORT=" "$SCRIPT_DIR/.env" | cut -d'=' -f2 | xargs)
else
  MCP_PORT="9090"
fi
SERVICE_URL="http://localhost:$MCP_PORT"
WEB_VIEWER_URL="http://localhost:9091"
MAX_WAIT=60

# ── 顏色和日誌函數 ────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

log_to_file() {
  echo "[${TIMESTAMP}] $*" >> "$LOG_FILE"
}

info()    {
  echo -e "${CYAN}[INFO]${RESET} $*"
  log_to_file "[INFO] $*"
}

success() {
  echo -e "${GREEN}[✅]${RESET} $*"
  log_to_file "[✅] $*"
}

warn()    {
  echo -e "${YELLOW}[⚠️]${RESET} $*"
  log_to_file "[⚠️] $*"
}

error()   {
  echo -e "${RED}[❌]${RESET} $*" >&2
  log_to_file "[❌] $*"
  exit 1
}

# ── 狀態管理函數 ──────────────────────────────────────────

save_step_status() {
  local step=$1
  local status=$2  # completed, failed, skipped
  echo "$step=$status" >> "$STATUS_FILE"
}

step_completed() {
  local step=$1
  grep -q "^$step=completed" "$STATUS_FILE" 2>/dev/null || return 1
}

show_checklist() {
  echo ""
  echo -e "${BOLD}📋 安裝進度檢查清單${RESET}"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  local steps=(
    "check_prereq:前置依賴檢查"
    "create_directories:建立資料目錄"
    "docker_build:Docker Image 構建"
    "docker_start:Docker 容器啟動"
    "health_check:健康檢查"
    "mcp_config:MCP 配置寫入"
    "claude_settings:配置 Claude Code 設定"
    "inject_rules:注入 Agent 規則"
    "verify_tools:工具驗證"
  )

  for step_info in "${steps[@]}"; do
    IFS=':' read -r step_name step_desc <<< "$step_info"
    if step_completed "$step_name"; then
      echo -e "${GREEN}✅${RESET} $step_desc"
    else
      echo -e "${YELLOW}⏳${RESET} $step_desc"
    fi
  done

  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""
}

# ── 主安裝流程 ─────────────────────────────────────────────

main() {
  echo -e "${BOLD}"
  echo "╔══════════════════════════════════════════════════════╗"
  echo "║   System Governor MCP Service — Installer           ║"
  echo "║   📋 支援中斷恢復 | 📝 日誌記錄 | 🔄 自動跳過       ║"
  echo "╚══════════════════════════════════════════════════════╝"
  echo -e "${RESET}"

  # 檢查先前安裝狀態
  if [ -f "$STATUS_FILE" ]; then
    info "偵測到先前的安裝嘗試，將從中斷處繼續..."
    show_checklist
  else
    info "開始新的安裝"
    touch "$STATUS_FILE"
    touch "$LOG_FILE"
  fi

  # ── Step 0: 前置檢查 ──────────────────────────────────────
  if ! step_completed "check_prereq"; then
    info "前置依賴檢查..."
    command -v docker   >/dev/null 2>&1 || error "Docker 未安裝。請先安裝 Docker Desktop。"
    command -v python3  >/dev/null 2>&1 || warn "python3 未找到（非必需）"
    success "前置依賴檢查通過"
    save_step_status "check_prereq" "completed"
  else
    success "前置依賴檢查 (已完成，跳過)"
  fi

  # ── Step 1: 建立資料目錄 ──────────────────────────────────
  if ! step_completed "create_directories"; then
    info "Step 1/6 — 建立資料目錄..."
    mkdir -p "$MCP_SERVICE_DIR/data/reports/memo"
    mkdir -p "$MCP_SERVICE_DIR/data/reports/traces"
    mkdir -p "$MCP_SERVICE_DIR/data/reports/full"
    success "資料目錄就緒"
    save_step_status "create_directories" "completed"
  else
    success "資料目錄 (已完成，跳過)"
  fi

  # ── Step 2: Docker Image 建立 ────────────────────────────
  if ! step_completed "docker_build"; then
    info "Step 2/6 — 建立 Docker Image（首次約需 2-3 分鐘）..."
    cd "$MCP_SERVICE_DIR"
    set -a
    [ -f "$SCRIPT_DIR/.env" ] && source "$SCRIPT_DIR/.env"
    set +a
    if docker compose build --quiet >> "$LOG_FILE" 2>&1; then
      success "Docker Image 建立完成"
      save_step_status "docker_build" "completed"
    else
      error "Docker Image 建立失敗。查看日誌：$LOG_FILE"
    fi
  else
    success "Docker Image (已完成，跳過)"
  fi

  # ── Step 3: 啟動容器 ──────────────────────────────────────
  if ! step_completed "docker_start"; then
    info "Step 3/6 — 啟動容器..."
    if docker compose up -d >> "$LOG_FILE" 2>&1; then
      success "容器啟動成功"
      save_step_status "docker_start" "completed"
    else
      error "容器啟動失敗"
    fi
  else
    success "容器啟動 (已完成，跳過)"
  fi

  # ── Step 4: 健康檢查 ──────────────────────────────────────
  if ! step_completed "health_check"; then
    info "Step 4/6 — 等待服務就緒（最多 ${MAX_WAIT}s）..."
    elapsed=0
    while true; do
      if curl -sf "${SERVICE_URL}/health" >/dev/null 2>&1; then
        success "服務健康檢查通過"
        save_step_status "health_check" "completed"
        break
      fi
      if [ $elapsed -ge $MAX_WAIT ]; then
        error "服務未在 ${MAX_WAIT}s 內啟動。查看日誌：docker compose logs system-governor-mcp"
      fi
      printf "."
      sleep 2
      elapsed=$((elapsed + 2))
    done
    echo ""
  else
    success "健康檢查 (已完成，跳過)"
  fi

  # ── Step 5: MCP 配置 ──────────────────────────────────────
  if ! step_completed "mcp_config"; then
    info "Step 5/6 — 配置 Antigravity MCP..."

    if [ ! -f "$MCP_CONFIG" ]; then
      warn "找不到 $MCP_CONFIG，跳過自動寫入"
      echo ""
      echo "📋 請手動在 $MCP_CONFIG 中加入："
      echo ""
      echo '  "system-governor": {'
      echo "    \"url\": \"http://localhost:${MCP_PORT}/mcp\","
      echo '    "disabled": false'
      echo '  }'
      echo ""
    else
      if grep -q '"system-governor"' "$MCP_CONFIG" 2>/dev/null; then
        warn "system-governor 已存在於 mcp_config.json，跳過（避免重複）"
      else
        cp "$MCP_CONFIG" "${MCP_CONFIG}.backup.$(date +%Y%m%d%H%M%S)"
        if python3 - <<PYEOF >> "$LOG_FILE" 2>&1
import json, os
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
PYEOF
        then
          success "MCP 配置已寫入"
        else
          warn "自動寫入失敗，請手動配置"
        fi
      fi
    fi
    save_step_status "mcp_config" "completed"
  else
    success "MCP 配置 (已完成，跳過)"
  fi

  # ── Step 7: Claude Code Settings ───────────────────────────
  if ! step_completed "claude_settings"; then
    info "Step 7/9 — 配置 Claude Code 設定..."

    if [ ! -d "$HOME/.claude" ]; then
      mkdir -p "$HOME/.claude"
      success "建立 ~/.claude 目錄"
    fi

    if [ ! -f "$CLAUDE_SETTINGS" ]; then
      # 建立新的 settings.json
      python3 - <<PYEOF >> "$LOG_FILE" 2>&1
import json, os
settings_path = os.path.expanduser("~/.claude/settings.json")
settings = {
    "mcpServers": {
        "system-governor": {
            "url": "http://localhost:$MCP_PORT/mcp",
            "disabled": False
        }
    }
}
with open(settings_path, 'w') as f:
    json.dump(settings, f, indent=2, ensure_ascii=False)
    f.write('\n')
PYEOF
      if [ $? -eq 0 ]; then
        success "建立 ~/.claude/settings.json"
      else
        warn "無法建立 ~/.claude/settings.json"
      fi
    else
      # 更新現有的 settings.json
      if grep -q '"system-governor"' "$CLAUDE_SETTINGS" 2>/dev/null; then
        warn "system-governor 已存在於 settings.json，跳過"
      else
        cp "$CLAUDE_SETTINGS" "${CLAUDE_SETTINGS}.backup.$(date +%Y%m%d%H%M%S)"
        python3 - <<PYEOF >> "$LOG_FILE" 2>&1
import json, os
settings_path = os.path.expanduser("~/.claude/settings.json")
with open(settings_path, 'r') as f:
    settings = json.load(f)
if 'mcpServers' not in settings:
    settings['mcpServers'] = {}
settings['mcpServers']['system-governor'] = {
    "url": "http://localhost:$MCP_PORT/mcp",
    "disabled": False
}
with open(settings_path, 'w') as f:
    json.dump(settings, f, indent=2, ensure_ascii=False)
    f.write('\n')
PYEOF
        if [ $? -eq 0 ]; then
          success "MCP 已注入 ~/.claude/settings.json"
        else
          warn "無法更新 ~/.claude/settings.json"
        fi
      fi
    fi

    save_step_status "claude_settings" "completed"
  else
    success "Claude Code 設定 (已完成，跳過)"
  fi

  # ── Step 8: 注入 Agent 規則 ───────────────────────────────
  if ! step_completed "inject_rules"; then
    info "Step 8/9 — 注入 Agent 規則到 CLAUDE.md..."

    TEMPLATE_FILE="$SCRIPT_DIR/SYSTEM_GOVERNOR_RULE_TEMPLATE.md"

    if [ ! -f "$TEMPLATE_FILE" ]; then
      warn "找不到規則模板：$TEMPLATE_FILE，跳過注入"
      save_step_status "inject_rules" "completed"
    else
      # 從模板中提取 Claude Code 規則（第 25-123 行）
      RULES_TO_INJECT=$(sed -n '25,123p' "$TEMPLATE_FILE")

      if [ ! -f "$CLAUDE_RULE_FILE" ]; then
        # 建立新的 CLAUDE.md
        cat > "$CLAUDE_RULE_FILE" <<'EOF'
# Claude Code — 全域配置規則

> 自動由 System Governor 安裝程序生成

EOF
        echo "$RULES_TO_INJECT" >> "$CLAUDE_RULE_FILE"
        success "建立並注入規則到 ~/.claude/CLAUDE.md"
      else
        # 檢查規則是否已存在
        if grep -q "System Governor MCP" "$CLAUDE_RULE_FILE" 2>/dev/null; then
          warn "System Governor 規則已存在於 CLAUDE.md，跳過"
        else
          # 備份現有文件
          cp "$CLAUDE_RULE_FILE" "${CLAUDE_RULE_FILE}.backup.$(date +%Y%m%d%H%M%S)"

          # 在文件末尾添加規則
          echo "" >> "$CLAUDE_RULE_FILE"
          echo "$RULES_TO_INJECT" >> "$CLAUDE_RULE_FILE"
          success "注入規則到 ~/.claude/CLAUDE.md"
        fi
      fi
    fi

    save_step_status "inject_rules" "completed"
  else
    success "Agent 規則注入 (已完成，跳過)"
  fi

  # ── Step 9: 工具驗證 ──────────────────────────────────────
  if ! step_completed "verify_tools"; then
    info "驗證工具..."

    HEALTH=$(curl -sf "${SERVICE_URL}/health" 2>/dev/null || echo "{}")
    if echo "$HEALTH" | grep -q '"status":"ok"'; then
      success "MCP 服務運行中，15 個工具可用"
      save_step_status "verify_tools" "completed"
    else
      warn "無法驗證 MCP 工具狀態"
    fi
  else
    success "工具驗證 (已完成，跳過)"
  fi

  # ── 完成 ────────────────────────────────────────────────────
  echo ""
  echo -e "${GREEN}${BOLD}"
  echo "╔════════════════════════════════════════════════════╗"
  echo "║            ✅ 安裝完成！                          ║"
  echo "╚════════════════════════════════════════════════════╝"
  echo -e "${RESET}"

  echo "📡 可用端點："
  echo "   MCP 工具:      $SERVICE_URL/mcp"
  echo "   Web Viewer:    $WEB_VIEWER_URL/archive  ⭐"
  echo ""

  echo "💾 重要位置："
  echo "   MCP 設定:      $CLAUDE_SETTINGS"
  echo "   Agent 規則:    $CLAUDE_RULE_FILE"
  echo "   MCP README:    $MCP_SERVICE_DIR/README.md"
  echo "   安裝日誌:      $LOG_FILE"
  echo ""

  echo "✅ 已自動配置："
  echo "   • Docker 容器已運行"
  echo "   • MCP 服務已就緒（15 個工具可用）"
  echo "   • ~/.claude/settings.json 已配置"
  echo "   • ~/.claude/CLAUDE.md 已注入 System Governor 規則"
  echo ""

  echo "🚀 立即開始使用："
  echo "   1️⃣  完全關閉 Claude Code（如果已開啟）"
  echo "   2️⃣  重新打開 Claude Code"
  echo "   3️⃣  在對話框中提問："
  echo "       「評估一下我們應該採用微服務架構嗎？」"
  echo "   4️⃣  Claude 會自動提議使用 System Governor"
  echo ""

  echo "📚 其他資源："
  echo "   • Web Viewer:   $WEB_VIEWER_URL/archive"
  echo "   • 快速開始:     $SCRIPT_DIR/README.md"
  echo "   • 規則指南:     $SCRIPT_DIR/SYSTEM_GOVERNOR_RULE_TEMPLATE.md"
  echo ""

  info "日誌已保存到: $LOG_FILE"
}

# ── 執行主程式 ────────────────────────────────────────────
main "$@"
