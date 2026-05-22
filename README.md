# System Governor

> 知識圖譜驅動的系統治理框架 — GitNexus × 理性懷疑論 × 反幻覺 MCP Service

---

## 快速啟動

### 方式 1：Docker 容器（推薦）
```bash
# 進入部署目錄
cd dist/

# 啟動服務（自動下載 ~120MB 鏡像）
docker compose up
```

### 方式 2：本地安裝（需要 Docker）
```bash
# 一鍵安裝與配置
bash install.sh

# 確認 MCP 服務
curl http://localhost:9090/health
```

### 訪問決策檔案庫
```bash
# 打開網頁查看器
open http://localhost:9091/archive
```

詳細部署選項見 [dist/README.md](dist/README.md)

---

## 專案結構

```
pipagent/
│
├── dist/                   ← 🐳 Docker 部署包（推薦）
│   ├── Dockerfile          ← 優化版本（alpine，~120MB）
│   ├── docker-compose.yml  ← 快速啟動配置
│   ├── .env.example        ← 環境變數範本
│   └── README.md           ← 部署指南
│
├── install.sh              ← 一鍵安裝（Docker + mcp_config 寫入）
├── uninstall.sh            ← 一鍵卸載（互動式確認）
│
├── system-governor/        ← HTML 靜態工作流模板（無需伺服器）
│   ├── index.html          ← 主控台儀表板
│   ├── 01_prior_hypotheses_align.html
│   ├── 02_gitnexus_flow_audit.html
│   └── 03_architectural_tradeoff.html
│
├── .github/workflows/      ← GitHub Actions 自動化
│   └── release.yml         ← 自動構建 & 發佈 Docker 鏡像
│
└── governor/               ← System Governor MCP 服務（核心）
    ├── server.py           ← FastMCP 主入口 (HTTP/SSE :9090)
    │                          含 /mcp + /health + /archive（新增）
    ├── Dockerfile
    ├── docker-compose.yml
    ├── requirements.txt
    ├── README.md           ← 服務詳細文檔
    │
    ├── core/               ← 核心層
    │   ├── db.py           ← SQLite（immutable records）
    │   ├── anti_hallucination.py  ← SHA-256 + 空欄位保護
    │   └── reminder.py     ← 主動 Reminder 偵測
    │
    ├── hooks/              ← Stage 生命週期 Hooks
    │   └── pre_stage.py    ← Stage 前置 idle 偵測
    │
    ├── roles/              ← 三角色定義
    │   ├── strict_critic.py
    │   ├── rational_defender.py
    │   └── impartial_judge.py
    │
    ├── tools/              ← 15 個 MCP Tools（分 5 類）
    │   ├── session_tools.py    ← Category A: 會話管理
    │   ├── record_tools.py     ← Category B: 原始輸入捕獲
    │   ├── workflow_tools.py   ← Category C: 三段工作流
    │   ├── skill_tools.py      ← Category D: Skill 查詢
    │   └── report_tools.py     ← Category E: 報告生成
    │
    ├── skills/             ← Skill 定義（Markdown）
    │   └── quick_memo.md
    │
    ├── templates/          ← Jinja2 HTML 報告模板
    │   ├── quick_memo.html.j2      ← 1 頁 Memo
    │   ├── solution_trace.html.j2  ← 2 頁思考軌跡
    │   └── full_report.html.j2     ← 3 頁完整工程報告
    │
    └── data/               ← Docker volume（持久化）
        ├── governor.db
        └── reports/
            ├── memo/
            ├── traces/
            └── full/
```

---

## MCP 工具完整清單

### Category A — 會話管理（4 個）

| 工具 | 必要參數 | 說明 |
|------|---------|------|
| `sg_create_session` | `topic` | 建立新 session，取得 session_id |
| `sg_get_session` | `session_id` | 取得詳情與待確認 Reminders |
| `sg_list_sessions` | — | 列出全部 session |
| `sg_close_session` | `session_id` | 標記完成（建議先生成報告） |

### Category B — 原始輸入捕獲（3 個，核心）

| 工具 | 必要參數 | 說明 |
|------|---------|------|
| `sg_record_input` | `session_id`, `content`, `stage` | 原封不動存入，SHA-256 保護 |
| `sg_check_reminders` | `session_id` | 查詢 / 確認待提醒項目 |
| `sg_get_records` | `session_id` | 查詢記錄（可篩選 stage/role） |

**`stage` 值對照：**

| stage | 使用時機 |
|-------|---------|
| `interview` | 訪談討論 |
| `hypothesis` | 假設對齊 |
| `gitnexus_audit` | GitNexus 圖譜剖析 |
| `tradeoff` | 架構辯證 |
| `conclusion` | 需求結論 |
| `memo` | 想法/備忘 |
| `pain_point` | 目前痛點 |
| `next_session` | 下次待解決 |

### Category C — 三段工作流（4 個）

| 工具 | 說明 |
|------|------|
| `sg_run_stage_01` | 假設對齊（8 項 bool 門檻） |
| `sg_run_stage_02` | GitNexus 剖析 + 自動 Strict Critic 拒絕 |
| `sg_run_stage_03` | 架構辯證 → 輸出 SystemGovernorResponse JSON |
| `sg_get_workflow_status` | 三段進度總覽 |

### Category D — Skill（2 個）

| 工具 | 說明 |
|------|------|
| `sg_list_skills` | 列出可用 Skill |
| `sg_get_skill` | 取得 Skill Markdown 原文 |

### Category E — 報告生成（3 個）

| 工具 | 輸出 | 說明 |
|------|------|------|
| `sg_generate_memo` | 1 頁 HTML | 需求確認 / 想法發想 / 存證 |
| `sg_generate_trace` | 2 頁 HTML | 解決方案 + 思考軌跡 + 痛點 |
| `sg_generate_full` | 3 頁 HTML | 完整工程報告 + 工程圖 + Hash 鏈 |

---

## 標準工作流程

### 模式 A：快速 Memo（訪談後 5 分鐘完成）

```
sg_create_session → sg_record_input × N → sg_generate_memo
```

### 模式 B：完整工程治理（含 GitNexus 剖析）

```
sg_create_session
  → sg_run_stage_01（假設對齊）
  → sg_record_input（stage='hypothesis'）
  → sg_run_stage_02（GitNexus 剖析）
  → sg_record_input（stage='gitnexus_audit'）
  → sg_run_stage_03（架構辯證）
  → sg_record_input（stage='tradeoff'）
  → sg_record_input（stage='conclusion'）
  → sg_generate_full
  → sg_close_session
```

---

## 反幻覺機制

| 機制 | 說明 |
|------|------|
| **Immutable Records** | `records` 表寫入後不可更新 |
| **SHA-256 Hash** | 每筆記錄計算 hash，報告顯示前 8 碼供比對 |
| **空欄位不補全** | 空值只顯示 `【⏳ 待確認 — 時間 尚未記錄】` |
| **主動 Reminder** | 每個工具回應含 `_reminders`，超過 10 分鐘未記錄自動警告 |
| **Strict Critic 拒絕** | Stage 02 偵測到 Hard Code / UI 遮醜自動觸發拒絕分支 |

---

## Reminder 機制說明

每個工具的回應都包含 `_reminders` 陣列：

```json
{
  "result": { "..." : "..." },
  "_reminders": [
    {
      "level": "WARNING",
      "type": "long_idle",
      "message": "⚠️ 已超過 10 分鐘未呼叫 sg_record_input...",
      "action": "呼叫 sg_record_input 記錄當前討論內容",
      "triggered_at": "2026-05-22T07:00:00Z"
    }
  ]
}
```

**觸發條件：**
- 超過 `REMINDER_THRESHOLD_MINUTES`（預設 10 分鐘）未呼叫 `sg_record_input`
- 進入新 Stage 前，前一 Stage 沒有對應記錄

---

---

## 📊 新功能：決策檔案庫

在瀏覽器訪問 `http://localhost:9090/archive` 可查看所有歷史決策記錄：

- 💬 **決策過程** — 完整時間線（訪談 → 假設 → 分析 → 權衡 → 結論）
- 👥 **利益相關者** — 誰參與了這個決策
- 🎯 **工作流進度** — Stage 01/02/03 進度一覽
- 📄 **生成報告** — 直接打開 Memo / Trace / Full 報告

設計特性：
- ✅ 白色簡潔設計，易於閱讀
- ✅ 非專業人士也能理解決策過程
- ✅ 完整軌跡可視化，方便分享

---

## Antigravity IDE 接入

在 `~/.gemini/antigravity/mcp_config.json` 的 `mcpServers` 加入：

```json
"system-governor": {
  "url": "http://localhost:9090/mcp",
  "disabled": false
}
```

重啟 IDE 後，`sg_*` 工具即可使用。

> 💡 `install.sh` 會自動完成此步驟（若 mcp_config.json 存在）

---

## 📋 服務端點

| 用途 | 端點 |
|------|------|
| MCP 工具調用 | `http://localhost:9090/mcp` |
| 健康檢查 | `http://localhost:9090/health` |
| 決策檔案庫 | `http://localhost:9090/archive` ⭐ 新增 |

---

## 報告查詢

```bash
# 訪問決策檔案庫（推薦）
open http://localhost:9090/archive

# 或手動查詢報告文件
open governor/data/reports/memo/*.html
open governor/data/reports/full/*.html

# 直接查詢 SQLite DB
sqlite3 governor/data/governor.db "SELECT id, role, stage, created_at, substr(content,1,80) FROM records ORDER BY created_at DESC LIMIT 20;"
```

---

## 常見問題

**Q: 報告中有很多【⏳ 待確認】？**
> 這是正確行為。系統只填入已記錄的內容，請呼叫 `sg_record_input` 補充後重新生成。

**Q: 想修改已記錄的 content？**
> 不支援。Records 為 immutable，這是防竄改設計。請新增一筆修正記錄，在 `source_note` 說明「修正前一筆記錄 #xxx」。

**Q: Docker 服務停止後資料是否保留？**
> 是。資料儲存於 `governor/data/governor.db`，重啟後自動載入。

**Q: Reminder 很煩，可以關閉嗎？**
> 可調整 `docker-compose.yml` 中的 `REMINDER_THRESHOLD_MINUTES` 環境變數（設為更大的值），但不建議完全停用。

---

## 開發資訊

- **版本**: v1.0.0
- **Git**: `git log --oneline`
- **GitNexus 索引**: `.gitnexus/` 目錄（執行 `npx gitnexus analyze` 後生成）
- **技術棧**: Python 3.12 · FastMCP · SQLite · Jinja2 · Docker
