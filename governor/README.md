# System Governor MCP Service — 啟動與接入說明

## 🚀 快速啟動

```bash
cd /Users/pericchen/Project/pipagent
bash install.sh
```

安裝腳本會自動：
- ✅ 建立 data 目錄與報告子資料夾
- ✅ 建立 Docker Image
- ✅ 啟動服務容器
- ✅ 驗證健康狀態
- ✅ 設定 Antigravity IDE MCP 配置
- ✅ 顯示 Agent 規則集成指南

## 📡 服務端點

| 用途 | 端點 | 說明 |
|------|------|------|
| **MCP 工具** | `http://localhost:9090/mcp` | 給 Claude Code / Gemini 調用 |
| **健康檢查** | `http://localhost:9090/health` | 服務狀態檢查 |
| **決策檔案庫** | `http://localhost:9090/archive` | 📊 **新增** — 網頁查看器 |

### 驗證服務狀態

```bash
# 快速檢查
curl http://localhost:9090/health

# 預期輸出
{"status":"ok","service":"system-governor-mcp","tools":15}
```

## 📊 決策檔案庫（Archive Viewer）

新增的網頁查看器可視化所有歷史決策。

### 訪問方式
```
在瀏覽器打開: http://localhost:9090/archive
```

### 展示內容
每個決策記錄（Session）包含：
- 💬 **決策過程** — 訪談 / 假設 / 分析 / 權衡的完整時間線
- 👥 **利益相關者** — 誰參與了這個決策
- 🎯 **工作流進度** — Stage 01/02/03 是否通過
- 📄 **生成報告** — 直接打開 Memo / Trace / Full 報告

### 特性
- ✅ 白色簡潔設計，易於閱讀
- ✅ 非專業人士也能理解決策過程
- ✅ 完整決策軌跡可視化
- ✅ 一鍵打開各階段報告

## 🔌 加入 Antigravity IDE

**路徑**: `~/.gemini/antigravity/mcp_config.json`

在 `mcpServers` 物件中加入：

```json
"system-governor": {
  "url": "http://localhost:9090/mcp",
  "disabled": false
}
```

> 💡 `install.sh` 會自動完成此步驟（若 mcp_config.json 存在）

## 📚 可用工具一覽（15 個）

### Category A — 會話管理
| 工具 | 說明 |
|------|------|
| sg_create_session | 建立新 session |
| sg_get_session | 取得 session 詳情 |
| sg_list_sessions | 列出全部 session |
| sg_close_session | 關閉 session |

### Category B — 原始輸入捕獲（核心）
| 工具 | 說明 |
|------|------|
| sg_record_input | 記錄使用者原始文字（SHA-256 保護） |
| sg_check_reminders | 查詢 / 確認待提醒項目 |
| sg_get_records | 查詢記錄（可篩選 stage/role） |

### Category C — 三段工作流
| 工具 | 說明 |
|------|------|
| sg_run_stage_01 | 假設對齊門檻驗證 |
| sg_run_stage_02 | GitNexus 圖譜剖析 + 自動拒絕 |
| sg_run_stage_03 | 架構辯證 + JSON 輸出 |
| sg_get_workflow_status | 三段進度總覽 |

### Category D — Skill
| 工具 | 說明 |
|------|------|
| sg_list_skills | 列出可用 Skill |
| sg_get_skill | 取得 Skill MD 原文 |

### Category E — 報告生成
| 工具 | 說明 |
|------|------|
| sg_generate_memo | Quick Memo（1 頁） |
| sg_generate_trace | Solution Trace（2 頁） |
| sg_generate_full | Full Engineering Report（3 頁 + Hash 防竄改） |

## 💾 數據存儲

### 報告輸出位置

```
governor/data/
├── governor.db           ← SQLite 資料庫（所有決策記錄）
└── reports/
    ├── memo/            ← 1 頁快速記錄
    ├── traces/          ← 2 頁解決方案軌跡
    └── full/            ← 3 頁 + JSON + Hash 完整報告
```

### 表結構

| 表名 | 用途 |
|------|------|
| sessions | 工作階段（topic, stakeholders, status） |
| records | 原始輸入記錄（不可修改，SHA-256 保護） |
| stage_progress | 工作流進度（Stage 01/02/03 狀態） |
| reminders | 自動提醒（未記錄的討論） |
| reports | 生成的報告 metadata |

## 🏷️ stage 值對照表

| stage | 使用時機 |
|-------|---------|
| interview | 訪談討論 |
| hypothesis | 假設對齊 |
| gitnexus_audit | GitNexus 圖譜剖析 |
| tradeoff | 架構辯證 |
| conclusion | 需求結論 |
| memo | 想法/備忘 |
| pain_point | 目前痛點 |
| next_session | 下次待解決 |

## 📖 關聯文檔

- **SYSTEM_GOVERNOR_RULE_TEMPLATE.md** — Agent 規則模板（複製到 ~/.claude/CLAUDE.md 或 ~/.gemini/GEMINI.md）
- **CLAUDE_CODE_INTEGRATION.md** — Claude Code 整合指南
- **AGENT_SELF_AWARENESS.md** — Agent 自判斷能力文檔
- **WORKFLOW_VERIFICATION.md** — E2E 驗證報告

## 🔧 故障排查

### 服務無法啟動
```bash
# 檢查 Docker 狀態
docker ps

# 查看日誌
docker compose logs system-governor-mcp

# 重新啟動
docker compose down
docker compose up -d
```

### 無法訪問 /archive
- ✅ 確保 install.sh 已執行
- ✅ 確保服務在 port 9090 上運行（檢查 .env 中的 MCP_PORT）
- ✅ 刷新瀏覽器，清除快取
