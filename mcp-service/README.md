# System Governor MCP Service — 啟動與接入說明

## 啟動服務

```bash
cd /Users/pericchen/Project/pipagent/mcp-service

# 建立 data 目錄（volume 掛載點）
mkdir -p data/reports/memo data/reports/traces data/reports/full

# 啟動 Docker
docker compose up -d

# 確認健康
curl http://localhost:8080/health
# 預期: {"status":"ok","service":"system-governor-mcp","tools":15}
```

## 加入 Antigravity IDE mcp_config.json

路徑: `~/.gemini/antigravity/mcp_config.json`

在 `mcpServers` 物件中加入：

```json
"system-governor": {
  "url": "http://localhost:8080/mcp",
  "disabled": false
}
```

## 可用工具一覽（15 個）

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
| sg_generate_full | Full Engineering Report（3 頁） |

## 報告輸出位置

```
mcp-service/data/reports/
├── memo/     ← sg_generate_memo 的 .html 輸出
├── traces/   ← sg_generate_trace 的 .html 輸出
└── full/     ← sg_generate_full 的 .html 輸出
```

## stage 值對照表（sg_record_input 使用）

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
