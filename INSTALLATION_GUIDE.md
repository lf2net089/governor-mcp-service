# System Governor — 安裝指南

> 知識圖譜驅動的系統治理框架 — 3 分鐘快速開始

---

## 📋 前置要求

- **Docker & Docker Compose**
  - [安裝 Docker Desktop](https://www.docker.com/products/docker-desktop)
  - [安裝 Docker Compose](https://docs.docker.com/compose/install/)（Docker Desktop 已包含）

- **硬碟空間**：至少 1GB（Docker 鏡像 ~500MB + 數據）

- **網路連線**：首次啟動時需要拉取 Docker 鏡像

---

## 🚀 快速安裝（3 種方式）

### 方式 A：本地構建（推薦開發）

適合有原始碼且需要定制的使用者。

```bash
# Step 1: Clone 倉庫
git clone https://github.com/lf2net089/governor-mcp-service.git
cd governor-mcp-service

# Step 2: 進入部署目錄
cd dist

# Step 3: 啟動服務
docker compose up
```

**✅ 完成！** 訪問 http://localhost:9091/archive

---

### 方式 B：使用本地預構建鏡像

適合已經構建過鏡像的環境（快速重啟）。

```bash
# Step 1: 進入部署目錄
cd governor-mcp-service/dist

# Step 2: 驗證鏡像存在
docker images | grep governor-mcp-service

# Step 3: 啟動
docker compose up
```

---

### 方式 C：從 GitHub Container Registry 拉取（最簡單）

適合純粹想使用服務，不涉及修改代碼的使用者。

```bash
# Step 1: 建立目錄與配置
mkdir -p system-governor && cd system-governor

# Step 2: 下載 docker-compose 配置
curl -O https://raw.githubusercontent.com/lf2net089/governor-mcp-service/main/dist/docker-compose.yml

# Step 3: 修改 docker-compose.yml 使用遠端鏡像
# 將 `build:` 改為 `image: ghcr.io/lf2net089/governor-mcp-service:latest`

# Step 4: 啟動服務
docker compose up
```

---

## 🔧 配置

### 環境變數（可選）

創建 `.env` 檔案：

```bash
# 複製範本
cp .env.example .env

# 編輯設定（需要時）
# MCP_PORT=9090
# REMINDER_THRESHOLD_MINUTES=10
```

### 網路埠

| 埠 | 用途 | URL |
|-----|-----|----|
| **9090** | MCP 工具端點 | http://localhost:9090/mcp |
| **9091** | 決策檔案庫 | http://localhost:9091/archive ⭐ |

---

## ✅ 驗證安裝

### 1. 檢查容器狀態

```bash
docker ps | grep governor
```

**預期輸出**：容器應該是 `Up` 狀態。

### 2. 測試 MCP 服務

```bash
curl http://localhost:9090/health
```

**預期輸出**：
```json
{"status":"ok","service":"system-governor-mcp","tools":15}
```

### 3. 訪問決策檔案庫

在瀏覽器中打開：
```
http://localhost:9091/archive
```

**預期**：看到空的決策檔案庫頁面

---

## 📊 可用端點

| 端點 | 說明 | 範例 |
|------|------|------|
| `/health` | 健康檢查 | `curl http://localhost:9090/health` |
| `/mcp` | MCP 工具協議 | Claude Code / Gemini 使用 |
| `/archive` | 決策檔案庫（網頁） | http://localhost:9091/archive |

---

## 🛑 停止與清理

### 停止服務

```bash
docker compose down
```

### 完整卸載（清除所有數據）

```bash
bash ../uninstall.sh
```

系統會引導選擇：
- 是否移除 Docker 鏡像
- 是否刪除決策數據庫與報告

---

## 🆘 故障排除

### 問題：容器無法啟動

**症狀**：`docker compose up` 後容器立即退出

**解決**：
```bash
# 查看日誌
docker compose logs system-governor-mcp

# 檢查埠佔用
lsof -i :9090
lsof -i :9091

# 清除舊容器並重試
docker compose down -v
docker compose up
```

### 問題：無法連線到 http://localhost:9091/archive

**症狀**：連線被拒絕或超時

**解決**：
```bash
# 檢查容器是否真的在運行
docker ps | grep governor

# 查看詳細日誌
docker logs system-governor-mcp

# 驗證埠映射
docker port system-governor-mcp
```

### 問題：磁碟空間不足

**症狀**：Docker 鏡像拉取失敗

**解決**：
```bash
# 清理 Docker 系統（警告：會刪除未使用的鏡像）
docker system prune -a

# 檢查磁碟使用情況
docker system df
```

---

## 📚 進階使用

### 持久化數據

決策記錄自動保存到 `./data/governor.db`（SQLite）。

**備份數據**：
```bash
cp data/governor.db data/governor.db.backup
```

**恢復數據**：
```bash
cp data/governor.db.backup data/governor.db
docker compose restart
```

### 整合到 Claude Code / Gemini

1. 啟動服務後，複製 MCP 工具端點：
   ```
   http://localhost:9090/mcp
   ```

2. 在 IDE 配置中添加：
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

3. 重啟 IDE，應該能在工具列表中看到 15 個 System Governor 工具。

---

## 📞 獲取幫助

### 查看日誌

```bash
# 實時日誌
docker compose logs -f

# 只看最後 100 行
docker compose logs --tail 100
```

### 檢查數據庫

```bash
# 進入容器
docker exec -it system-governor-mcp bash

# 查詢決策記錄
sqlite3 /data/governor.db \
  "SELECT id, topic, status, created_at FROM sessions ORDER BY created_at DESC LIMIT 5;"
```

### 報告問題

提交 Issue 到：https://github.com/lf2net089/governor-mcp-service/issues

包含：
- Docker 版本：`docker --version`
- docker-compose 版本：`docker compose version`
- 容器日誌：`docker compose logs --tail 50`
- 系統信息：`uname -a`

---

## 📝 常見問題

**Q：數據會被保存嗎？**
> 是。所有決策記錄存儲於 `governor/data/governor.db`（SQLite），重啟後自動載入。

**Q：可以改變埠號嗎？**
> 可以。編輯 `.env` 並設置 `MCP_PORT=8090`，然後重啟。

**Q：支持多用戶同時使用嗎？**
> 是。SQLite 支持多個連線，MCP 工具同時可被多個 IDE 使用。

**Q：鏡像有多大？**
> ~500MB（優化 alpine 版本，相比 slim 版本更輕量）。

**Q：如何更新到最新版本？**
> 執行 `docker compose down && docker pull ghcr.io/lf2net089/governor-mcp-service:latest && docker compose up`

---

**最後更新**：2026-05-22  
**版本**：1.0.0  
**License**：MIT
