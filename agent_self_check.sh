#!/usr/bin/env bash
# System Governor — Agent 自判斷工具
# 供 Claude Code 中的 Agent 在對話中調用
#
# 用途：自動檢測 System Governor 是否可用
#       判斷當前任務是否需要使用
#       提供 Agent 決策依據

set -e

# ============================================================
# 顏色定義
# ============================================================
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;36m'
RESET='\033[0m'

# ============================================================
# 核心檢查函數
# ============================================================

check_service_health() {
    # 檢查 System Governor 服務是否可用
    if curl -s --connect-timeout 2 http://localhost:9090/health | grep -q '"status":"ok"'; then
        return 0
    else
        return 1
    fi
}

check_docker_container() {
    # 檢查 Docker 容器是否運行
    if docker ps | grep -q "system-governor-mcp"; then
        return 0
    else
        return 1
    fi
}

check_database() {
    # 檢查數據庫是否可訪問
    DB_PATH="/Users/pericchen/Project/pipagent/governor/data/governor.db"
    if [ -f "$DB_PATH" ]; then
        return 0
    else
        return 1
    fi
}

get_agent_type() {
    # 自我識別：確認當前 Agent 類型
    # 檢查環境變數或環境特徵
    if [ -n "$CLAUDE_CODE_CONTEXT" ] || [ -n "$VSCODE_PID" ]; then
        echo "claude-code"
    elif [ -n "$ANTIGRAVITY_IDE" ]; then
        echo "antigravity"
    else
        echo "unknown"
    fi
}

# ============================================================
# 主函數
# ============================================================

main() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════╗${RESET}"
    echo -e "${BLUE}║  System Governor — Agent 自判斷檢查    ║${RESET}"
    echo -e "${BLUE}╚════════════════════════════════════════╝${RESET}"
    echo ""

    # 1. 識別 Agent 類型
    AGENT_TYPE=$(get_agent_type)
    echo -e "${BLUE}[1/5] Agent 自我識別${RESET}"
    echo -e "      當前 Agent: ${GREEN}$AGENT_TYPE${RESET}"
    echo ""

    # 2. 檢查服務狀態
    echo -e "${BLUE}[2/5] 檢查 System Governor 服務${RESET}"
    if check_service_health; then
        echo -e "      HTTP 端點: ${GREEN}✅ 可用${RESET} (http://localhost:9090)"
        SERVICE_HEALTH=1
    else
        echo -e "      HTTP 端點: ${RED}❌ 不可用${RESET}"
        SERVICE_HEALTH=0
    fi
    echo ""

    # 3. 檢查 Docker 容器
    echo -e "${BLUE}[3/5] 檢查 Docker 容器${RESET}"
    if check_docker_container; then
        echo -e "      容器狀態: ${GREEN}✅ 運行中${RESET}"
        DOCKER_STATUS=1
    else
        echo -e "      容器狀態: ${RED}❌ 未運行${RESET}"
        DOCKER_STATUS=0
    fi
    echo ""

    # 4. 檢查數據庫
    echo -e "${BLUE}[4/5] 檢查數據庫${RESET}"
    if check_database; then
        echo -e "      數據庫: ${GREEN}✅ 可訪問${RESET}"
        echo "      位置: /Users/pericchen/Project/pipagent/governor/data/governor.db"
        DB_STATUS=1
    else
        echo -e "      數據庫: ${RED}❌ 不存在${RESET}"
        DB_STATUS=0
    fi
    echo ""

    # 5. 給出建議
    echo -e "${BLUE}[5/5] Agent 決策建議${RESET}"
    echo ""

    if [ $SERVICE_HEALTH -eq 1 ] && [ $DB_STATUS -eq 1 ]; then
        echo -e "${GREEN}✅ System Governor 已準備就緒${RESET}"
        echo ""
        echo "   Agent 可以:"
        echo "   • 調用 sg_create_session() 建立會話"
        echo "   • 調用 sg_record_input() 記錄用戶輸入"
        echo "   • 執行 Stage 01-03 工作流"
        echo "   • 生成報告 (Memo/Trace/Full)"
        echo ""
        echo -e "${GREEN}推薦: 主動提議用戶使用 System Governor${RESET}"
        exit 0
    else
        echo -e "${RED}❌ System Governor 尚未準備就緒${RESET}"
        echo ""

        if [ $DOCKER_STATUS -eq 0 ]; then
            echo "   原因: Docker 容器未運行"
            echo ""
            echo "   啟動步驟:"
            echo "   1. cd /Users/pericchen/Project/pipagent"
            echo "   2. bash install.sh"
            echo ""
        fi

        if [ $DB_STATUS -eq 0 ]; then
            echo "   原因: 數據庫文件不存在"
            echo ""
            echo "   修復步驟:"
            echo "   1. cd /Users/pericchen/Project/pipagent"
            echo "   2. bash install.sh  (會自動初始化)"
            echo ""
        fi

        echo -e "${YELLOW}推薦: 提示用戶啟動服務，或使用標準流程${RESET}"
        exit 1
    fi
}

# ============================================================
# 命令行選項
# ============================================================

case "${1:-}" in
    "health")
        # 簡單的健康檢查（用於快速判斷）
        check_service_health && echo "OK" || echo "FAIL"
        ;;
    "docker")
        # 檢查 Docker 容器
        check_docker_container && echo "RUNNING" || echo "STOPPED"
        ;;
    "agent-type")
        # 識別 Agent 類型
        get_agent_type
        ;;
    "full"|"")
        # 完整檢查
        main
        ;;
    *)
        echo "用途: agent_self_check.sh [health|docker|agent-type|full]"
        echo ""
        echo "選項:"
        echo "  health      - 快速健康檢查 (返回 OK/FAIL)"
        echo "  docker      - 檢查容器狀態 (返回 RUNNING/STOPPED)"
        echo "  agent-type  - 識別當前 Agent 類型"
        echo "  full        - 完整檢查報告 (預設)"
        exit 1
        ;;
esac
