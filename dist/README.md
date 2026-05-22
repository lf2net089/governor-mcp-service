# System Governor MCP — 部署包

輕量化 Docker 發佈版本（基於 alpine，~120MB）

## 快速開始

### 前置需求
- Docker 與 Docker Compose（[安裝連結](https://docs.docker.com/get-docker/)）

### 方法 1：從 GitHub 容器倉庫拉取

```bash
docker pull ghcr.io/lf2net089/system-governor:latest
docker compose up
```

### 方法 2：本地構建

```bash
docker compose build
docker compose up
```

## 可用端點

| 端點 | 埠 | 用途 |
|------|-----|-----|
| `http://localhost:9090/mcp` | 9090 | MCP 工具端點 |
| `http://localhost:9091/health` | 9091 | Web Viewer 健康檢查 |
| `http://localhost:9091/archive` | 9091 | 決策檔案庫（網頁查看器）⭐ |

## 環境變數

在 `.env` 檔案中自訂：

```
MCP_PORT=9090
DATA_DIR=/data
DB_PATH=/data/governor.db
REPORTS_DIR=/data/reports
MCP_HOST=0.0.0.0
REMINDER_THRESHOLD_MINUTES=10
```

## 資料持久化

容器內的 `/data` 目錄已掛載到本地 `./data`，確保決策記錄不會丟失。

```
./data/
├── governor.db          # SQLite 決策數據庫
├── reports/
│   ├── memo/           # 備忘錄報告
│   ├── traces/         # 執行追蹤
│   └── full/           # 完整報告
```

## 故障排除

**容器無法啟動？**
```bash
# 查看日誌
docker compose logs system-governor-mcp

# 檢查埠佔用
lsof -i :9090
lsof -i :9091
```

**健康檢查失敗？**
```bash
# 手動測試
curl http://localhost:9090/health
curl http://localhost:9091/health
```

## 完整文檔

詳細使用方法與 Agent 規則整合，請見根目錄 `README.md`。
