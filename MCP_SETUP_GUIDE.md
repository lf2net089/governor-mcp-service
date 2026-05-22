# System Governor — MCP 安裝與配置指南

> 完整的架構決策記錄系統 + Claude Code 整合

---

## 📋 安裝檢查清單

- [ ] **第一步** — Docker 服務部署
- [ ] **第二步** — MCP 自動配置
- [ ] **第三步** — Claude Code 重啟
- [ ] **第四步** — 驗證工具可用性

---

## ✅ 第一步 — 啟動 Docker 服務

### 1.1 進入 dist 目錄
```bash
cd /Users/pericchen/Project/pipagent/dist
```

### 1.2 啟動容器
```bash
docker compose up -d
```

### 1.3 驗證服務正常運行
```bash
# 檢查容器狀態
docker compose ps

# 預期輸出：status = Up (healthy)
```

### 1.4 驗證兩個服務
```bash
# MCP 服務（端口 9090）
curl http://localhost:9090/health
# 預期：{"status":"ok","service":"system-governor-mcp","tools":15}

# Web UI 服務（端口 9091）
curl http://localhost:9091/health
# 預期：{"status":"ok","service":"system-governor-web-viewer"}
```

---

## ⚙️ 第二步 — MCP 自動配置

### 方法 A：執行自動配置腳本（推薦）

```bash
bash /Users/pericchen/Project/pipagent/setup-mcp.sh
```

**腳本會自動：**
- ✓ 讀取 `~/.claude/settings.json`
- ✓ 備份原始文件（`.backup.時間戳`）
- ✓ 添加 MCP 服務配置
- ✓ 驗證配置成功

### 方法 B：手動配置（如果腳本失敗）

編輯 `~/.claude/settings.json`，添加以下內容（如果沒有 `mcpServers` 部分）：

```json
{
  "mcpServers": {
    "system-governor": {
      "url": "http://localhost:9090/mcp",
      "disabled": false
    }
  }
}
```

### ✓ 驗證配置

```bash
python3 -c "
import json
with open('~/.claude/settings.json') as f:
    settings = json.load(f)
    if 'system-governor' in settings.get('mcpServers', {}):
        print('✅ MCP 配置已成功添加')
    else:
        print('❌ MCP 配置未找到')
"
```

---

## 🔄 第三步 — 重啟 Claude Code

**重要：新配置需要重啟才能生效**

1. **完全關閉 Claude Code**
   - 關閉所有 Claude Code 窗口
   - 確保應用完全退出

2. **重新打開 Claude Code**
   - 啟動 Claude Code
   - 等待初始化完成

3. **檢查系統日誌**
   - 查看是否有任何 MCP 連接錯誤
   - 正常情況下應該看到類似信息：「MCP 伺服器已連接」

---

## ✨ 第四步 — 驗證工具可用性

### 4.1 在 Claude Code 中檢查工具列表

1. 打開任何項目
2. 打開對話框（Chat）
3. 查看工具清單 — 應該看到 **15 個 System Governor 工具**

### 4.2 工具列表

```
System Governor MCP Tools (15 total):

📝 決策管理
  ├─ sg_create_session         建立新決策 Session
  ├─ sg_record_input          記錄決策輸入（使用者/AI）
  ├─ sg_complete_stage        完成工作流階段
  └─ sg_generate_report       生成決策報告

🔍 查詢與分析
  ├─ sg_get_session           查詢單個 Session
  ├─ sg_list_sessions         列出所有 Session
  ├─ sg_search_sessions       搜尋 Session（關鍵字）
  └─ sg_get_session_stats     取得統計資訊

🔐 數據驗證與導出
  ├─ sg_verify_integrity      驗證 SHA-256 完整性
  ├─ sg_export_session        匯出 Session（JSON/PDF）
  └─ [其他 5 個工具]          ...

🌐 Web UI
  └─ Archive Viewer           http://localhost:9091/archive
```

### 4.3 測試工具呼叫

在 Claude Code 中提問：

```
你好，幫我評估是否應該採用微服務架構。
請使用 System Governor 工具記錄這個決策過程。
```

**預期行為：**
- Claude 會呼叫 `sg_create_session`
- 建立新 Session
- 記錄決策內容
- 完成工作流階段
- 回覆：「已建立決策 Session [ID]，訪問 http://localhost:9091/archive 查看」

---

## 🌐 使用 Web UI 檢查決策

訪問決策檔案庫：

```
http://localhost:9091/archive
```

**應該看到：**
- ✓ 所有建立過的 Session 清單
- ✓ 點擊卡片進入詳情頁面
- ✓ 完整的決策流程與文字記錄
- ✓ 工作流進度與統計信息

---

## 🛠️ 故障排除

### 問題 1：MCP 工具未出現

**症狀：** 重啟後工具清單仍是空的

**解決方案：**
1. 驗證 `~/.claude/settings.json` 中有 `mcpServers`
2. 確保 MCP 服務正在運行：`curl http://localhost:9090/health`
3. 重啟 Claude Code 並等待 30 秒讓系統初始化
4. 檢查 Claude Code 的系統日誌是否有錯誤

### 問題 2：無法連接到 localhost:9090

**症狀：** 工具呼叫失敗，顯示「連接被拒絕」

**解決方案：**
```bash
# 檢查容器狀態
docker compose ps

# 檢查端口是否真的開放
lsof -i :9090
lsof -i :9091

# 如果容器停止，重新啟動
docker compose up -d

# 查看容器日誌
docker compose logs system-governor-mcp
```

### 問題 3：Web UI 無法訪問

**症狀：** http://localhost:9091/archive 顯示「拒絕連接」

**解決方案：**
```bash
# 驗證 Web Viewer 服務
curl http://localhost:9091/health

# 如果失敗，檢查容器日誌
docker exec system-governor-mcp ps aux | grep web_viewer

# 重新啟動容器
docker compose restart
```

---

## 📊 完整流程示範

### 使用情境：評估是否重構為微服務

**步驟 1：提問**
```
Claude：
使用 System Governor 幫我完整評估 「我們應該將單體應用
重構為微服務架構嗎？」
請記錄：
- 使用者的問題
- 至少 3 個假設
- 成本效益分析
- 最終決策建議
```

**步驟 2：Claude 自動執行**
```
Claude 呼叫的工具序列：
1. sg_create_session("微服務架構重構評估")
   ↓ 返回 session_id: abc123

2. sg_record_input(session_id, "user", "問題：...")
   ↓ 記錄已保存

3. sg_record_input(session_id, "assistant", "假設1：...")
   ↓ 記錄已保存

4. sg_record_input(session_id, "assistant", "分析：...")
   ↓ 記錄已保存

5. sg_complete_stage(session_id, "analyst", "completed")
   ↓ 階段標記完成

6. sg_generate_report(session_id, "decision-summary")
   ↓ 生成決策報告

7. sg_get_session(session_id)
   ↓ 返回完整 Session 資訊
```

**步驟 3：查看決策檔案庫**
```
訪問 http://localhost:9091/archive
  ↓
點擊「微服務架構重構評估」
  ↓
查看完整的決策流程、工作流進度、所有記錄
```

**步驟 4：導出或分享**
```
Claude 呼叫：
  sg_export_session(session_id, "pdf")
  ↓ 生成 PDF 報告

可分享給團隊或存檔
```

---

## 📝 常見提問模板

### 架構決策評估
```
使用 System Governor 評估：[技術決策]
記錄維度：
- 現狀問題
- 可選方案（至少 3 個）
- 成本分析
- 風險評估
- 建議決策
```

### 技術方案比較
```
使用 System Governor 比較：[方案 A] vs [方案 B]
請記錄：
- 各方案的假設
- 關鍵指標評分
- 優缺點分析
- 最終推薦
```

### 決策追蹤
```
列出過去 30 天的所有架構決策
使用 System Governor 提供統計信息
```

---

## ✅ 檢查清單 — 完成後確認

- [ ] Docker 容器在運行（`docker compose ps` 顯示 healthy）
- [ ] MCP 服務正常（`curl http://localhost:9090/health` 返回 200）
- [ ] Web UI 可訪問（`curl http://localhost:9091/health` 返回 200）
- [ ] `~/.claude/settings.json` 已添加 `mcpServers` 配置
- [ ] Claude Code 已重啟
- [ ] System Governor 工具出現在工具清單中（15 個）
- [ ] 已成功調用至少一個工具（如 `sg_create_session`）
- [ ] Web UI 顯示新建立的 Session

---

## 🚀 準備就緒！

所有步驟完成後，你可以：

1. ✅ 在 Claude Code 中直接使用 15 個 MCP 工具
2. ✅ 自動記錄架構決策過程
3. ✅ 訪問 Web UI 查看決策歷史
4. ✅ 生成決策報告
5. ✅ 導出決策記錄（JSON/PDF）

**開始提問吧！🎉**

---

**最後更新：** 2026-05-22  
**版本：** 1.0.0  
**維護者：** System Governor Team
