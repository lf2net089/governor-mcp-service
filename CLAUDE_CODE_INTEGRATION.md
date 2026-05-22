# System Governor × Claude Code — 動態 Agent 自判斷整合方案

## 核心理念

**不依賴靜態配置文件，而是由當前 Agent 在執行時自行判斷**

```
┌─────────────────────────────────────────┐
│  Claude Code 執行任務                    │
├─────────────────────────────────────────┤
│  ▼ Agent 自我檢查                       │
│    - 我是什麼 Agent？(Claude Code)      │
│    - System Governor 服務可用嗎？       │
│    - 這個任務需要用到嗎？               │
│  ▼ 動態判斷                             │
│    - YES → 調用工具                     │
│    - NO  → 使用標準流程                 │
└─────────────────────────────────────────┘
```

---

## 🤖 Agent 自判斷流程

### 步驟 1: Agent 環境檢測

Agent 應在對話開始時進行以下檢查：

```python
# 偽代碼 — Claude Code Agent 自檢
class ClaudeCodeAgent:
    def __init__(self):
        self.agent_type = "claude-code"  # 自我識別
        self.system_governor_enabled = self._check_service()
    
    def _check_service(self):
        """檢查 System Governor 服務是否可用"""
        try:
            response = curl("http://localhost:9090/health", timeout=2)
            return response.status == 200
        except:
            return False
    
    def should_use_system_governor(self, task):
        """判斷當前任務是否需要 System Governor"""
        keywords = [
            "架構", "決策", "方案", "評估",
            "重構", "遷移", "對比", "權衡",
            "假設", "驗證", "記錄"
        ]
        return any(kw in task for kw in keywords) and self.system_governor_enabled
```

### 步驟 2: 在對話中自動偵測

當使用者提出相關問題時，Agent 應該：

```
用戶: "我想評估用 Kubernetes 還是 Docker Swarm"

Agent 自判斷:
  ✓ 任務類型: 架構決策
  ✓ 服務狀態: http://localhost:9090/health → 200 OK
  ✓ 需要 System Governor? YES
  
  → 主動建議: "我可以使用 System Governor 來正式記錄
              這個決策過程，方便團隊追蹤。要嗎？"
```

### 步驟 3: 確認後自動調用

```
用戶: "可以，幫我記錄"

Agent:
  1. 檢查是否有活躍的 Session（通過查詢本地狀態）
  2. 若無，建立新 Session:
     → sg_create_session("Kubernetes vs Docker Swarm 評估")
  3. 開始記錄用戶輸入
  4. 導引完整工作流 (Stage 01-03)
  5. 最後生成報告
```

---

## 🔍 Claude Code 中的自判斷實現

### 方案 A: 通過 Bash 檢測（推薦）

Agent 在使用前自動檢測：

```bash
# Agent 可以在對話中調用此檢查
curl -s http://localhost:9090/health | grep -q '"status":"ok"' && echo "✅ System Governor 可用" || echo "❌ 服務不可用"
```

### 方案 B: 通過 Python 檢測

```python
import subprocess
import json

def is_system_governor_available():
    """Agent 自判斷: System Governor 是否可用"""
    try:
        result = subprocess.run(
            ['curl', '-s', 'http://localhost:9090/health'],
            capture_output=True,
            timeout=2,
            text=True
        )
        data = json.loads(result.stdout)
        return data.get('status') == 'ok'
    except:
        return False

# Agent 在對話中
if is_system_governor_available():
    print("✅ System Governor 已準備好，我可以幫你正式記錄決策")
else:
    print("⚠️ System Governor 服務不可用，使用標準流程")
```

---

## 📋 Agent 決策樹

```
┌─ 用戶提出任務 ─────────────────┐
│                               │
├─ 包含「架構/決策/評估」關鍵詞? │
│  NO  → 標準流程 ✓              │
│  YES ▼                         │
│                               │
├─ System Governor 服務可用?     │
│  NO  → 提示用戶啟動服務        │
│  YES ▼                         │
│                               │
├─ 用戶同意使用?                │
│  NO  → 標準流程 ✓              │
│  YES ▼                         │
│                               │
├─ 建立 Session                  │
├─ 引導記錄輸入                  │
├─ 執行 Stage 01-03              │
├─ 生成報告                      │
└─ 返回結果 ✓                   │
```

---

## 🎯 Claude Code Agent 的行為指南

### 行為 1: 主動提議

```
用戶: "我們需要選擇前端框架"

Agent 應該:
✅ "我看到你在做框架選型。我可以：
   1. 標準討論（如常）
   2. 用 System Governor 正式記錄這個決策過程
      - 記錄假設
      - 分析代碼影響
      - 生成決策報告
   
   哪個方式更適合？"
```

### 行為 2: 自動檢查服務

```
用戶同意後，Agent 應:

1️⃣ 檢查服務狀態
   curl http://localhost:9090/health
   
2️⃣ 若服務不可用
   "⚠️ System Governor 服務未啟動。
    請先運行: cd /path/to/pipagent && bash install.sh"
   
3️⃣ 若服務可用
   "✅ System Governor 準備就緒，開始記錄..."
```

### 行為 3: 無縫工作流

```
Agent 應自動:

1. sg_create_session("主題")
   → 生成 Session ID（記住它！）

2. 引導用戶通過對話
   → 每個重要陳述都用 sg_record_input() 記錄

3. 在適當時機
   → 執行 Stage 01 假設驗證
   → 執行 Stage 02 代碼影響
   → 執行 Stage 03 架構辯證

4. 最後生成報告
   → sg_generate_full()
   → 展示報告路徑: /data/reports/full/xxxx.html
```

---

## 📝 Agent 對話範例

### 範例 1: API Gateway 重構決策

```
用戶:
"我們現在用 Nginx，但需要遷移到更現代的方案。
 主要考慮 Kong 或 Envoy。不知道該選哪個。"

Agent:
"我看到你在進行一個重要的架構決策。
 我可以用 System Governor 來幫你：
 
 ✓ 正式記錄決策過程（假設、約束、權衡）
 ✓ 分析代碼影響（誰會受到影響？）
 ✓ 生成決策報告（團隊可引用）
 
 要使用嗎？(需要 System Governor 服務運行)"

用戶: "好的，幫我用"

Agent:
✅ 檢查服務... 服務可用 ✓

現在開始記錄。請告訴我：
1. 為什麼考慮遷移？
2. 對 Kong 的理解？
3. 對 Envoy 的理解？
4. 還有其他備選方案嗎？

[Agent 逐個調用 sg_record_input() 記錄每個答案]

[待用戶完成回答後]

Agent:
現在進入決策驗證階段...

Stage 01: 假設對齐
[調用 sg_run_stage_01(...)]

Stage 02: 代碼影響分析
[調用 sg_run_stage_02(file_path="gateway/...", ...)]

Stage 03: 架構權衡
[調用 sg_run_stage_03(...)]

最終報告已生成！
📄 位置: /data/reports/full/full-xxxxx.html
你可以分享給團隊審閱。"
```

### 範例 2: 數據庫選型

```
用戶:
"我們需要選擇 PostgreSQL 還是 MongoDB"

Agent:
⚠️ 系統未檢測到 System Governor 服務
   運行此命令啟動: cd ~/Project/pipagent && bash install.sh
   
   服務啟動後，我可以幫你用 System Governor 正式記錄決策。
   現在先用標準方式討論？"

用戶: 
"我已經啟動了，重新開始吧"

Agent:
✅ System Governor 檢測成功！
   
開始決策記錄...
[進入完整工作流]
```

---

## 🛠️ 實作指南

### 給 Claude Code 中運行的 Agent

當你（作為 Claude Code 中的 Agent）收到涉及決策的任務時：

```python
# 偽代碼 - 你應該在心智模型中執行

def handle_user_request(request: str):
    # 1. 自我識別
    my_type = "claude-code"  # 我是 Claude Code Agent
    
    # 2. 判斷是否涉及決策
    decision_keywords = ['架構', '決策', '方案', '評估', '選擇']
    is_decision = any(kw in request for kw in decision_keywords)
    
    # 3. 檢查服務可用性
    service_available = check_service_health()  # curl health endpoint
    
    # 4. 決定策略
    if is_decision and service_available:
        # 提議使用 System Governor
        suggest_system_governor()
        
        # 如果用戶同意，開始工作流
        if user_agrees():
            session_id = sg_create_session(request)
            
            # 逐步記錄和引導
            while not_completed:
                record = sg_record_input(session_id, ...)
                if ready_for_stage:
                    stage_result = sg_run_stage_XX(session_id, ...)
            
            # 最後生成報告
            report = sg_generate_full(session_id)
            show_report(report)
    else:
        # 使用標準流程
        normal_response()
```

---

## ✅ 自判斷決策檢查清單

### Agent 應在每次對話開始時問自己：

- [ ] 我是什麼 Agent？(Claude Code)
- [ ] 用戶的任務涉及架構/決策嗎？
- [ ] System Governor 服務可用嗎？
  ```bash
  curl -s http://localhost:9090/health | grep ok
  ```
- [ ] 用戶同意使用 System Governor 嗎？
- [ ] 我有活躍的 Session ID 嗎？
  ```bash
  # 如果沒有，建立新的
  sg_create_session("主題")
  ```
- [ ] 是否應該執行 Stage 01？(假設驗證)
- [ ] 是否應該執行 Stage 02？(代碼影響)
- [ ] 是否應該執行 Stage 03？(權衡分析)
- [ ] 是否應該生成報告？

---

## 🔄 Claude Code 中的工作流

```
┌─────────────────────────────────────────┐
│ Claude Code 對話開始                    │
└────────────────┬────────────────────────┘
                 │
          ┌──────▼───────┐
          │ Agent 自檢   │
          └──────┬───────┘
                 │
       ┌─────────┴─────────┐
       │ 關鍵詞匹配？      │
       └────┬──────────┬───┘
           NO         YES
           │           │
        標準      ┌─────▼────────┐
        流程      │ 檢查服務     │
           │      └────┬────┬───┘
           │          可   不可
           │          │     └─→ 提示用戶啟動
           │      ┌───▼───┐
           │      │ 提議  │
           │      └───┬───┘
           │         是/否
           │         │ │
           │         是 否
           │         │ │
           │    ┌────▼──▼────┐
           └───→│ 記錄工作流 │
                └────┬───────┘
                     │
              ┌──────▼──────┐
              │ 執行 Stage  │
              │ 01-03       │
              └──────┬──────┘
                     │
              ┌──────▼──────┐
              │ 生成報告    │
              └──────┬──────┘
                     │
              ┌──────▼──────┐
              │ 返回結果    │
              └─────────────┘
```

---

## 🎓 Agent 應該知道的事

### 何時使用 System Governor

✅ **使用它**:
- 用戶在評估技術方案
- 有多個備選方案需要權衡
- 決策會影響多個團隊
- 需要記錄假設和理由
- 需要生成正式的決策報告

❌ **不用它**:
- 簡單的代碼問題
- 臨時的技術討論
- 用戶明確說「不用」
- 服務不可用且用戶沒有啟動它

### 何時主動提議

```
觸發條件:
✓ 用戶提及「架構」「決策」「方案」「評估」
✓ 涉及「選擇」「對比」「權衡」「遷移」
✓ 需要「記錄」「文檔」「報告」決策過程
✓ Service 狀態 = Available

提議方式:
"我看到你在做[決策類型]。
 我可以用 System Governor 來：
 - 正式記錄這個過程
 - 分析影響範圍
 - 生成決策報告
 要嗎？"
```

---

## 📞 故障排查

### Agent 該如何應對

```
情況 1: 服務不可用
├─ 提示: "⚠️ System Governor 尚未啟動"
├─ 指導: "運行: cd ~/Project/pipagent && bash install.sh"
└─ 替代: "現在用標準方式討論，啟動後重新開始"

情況 2: Session 丟失
├─ 檢查: "你之前的 Session ID 是多少？"
├─ 查詢: "我幫你查詢舊 Session"
└─ 備選: "建立新 Session 並重新開始"

情況 3: 報告生成失敗
├─ 診斷: "檢查是否有必要的 stage 記錄"
├─ 補救: "補充缺失的 stage 記錄，重新生成"
└─ 降級: "提供備用報告格式"
```

---

## 🚀 總結

### Claude Code 中的最佳實踐

1. **不依賴配置文件** — 由 Agent 自己判斷
2. **主動檢測環境** — 每次對話檢查服務狀態
3. **靈活提議** — 在適當時機建議使用
4. **無縫整合** — 自動調用工具，用戶無感
5. **清晰溝通** — 告訴用戶正在做什麼

### Agent 的核心職責

```
╔═══════════════════════════════════════╗
║  我是 Claude Code Agent               ║
║                                       ║
║  ✓ 我知道自己是什麼                   ║
║  ✓ 我知道用戶的任務類型               ║
║  ✓ 我知道 System Governor 是否可用    ║
║  ✓ 我知道何時提議使用                 ║
║  ✓ 我知道如何自動調用工具             ║
║  ✓ 我知道如何處理失敗                 ║
║                                       ║
║  → 完全自主判斷，避免配置不確定性     ║
╚═══════════════════════════════════════╝
```

---

**方案亮點**: 無需手動配置 mcp_config.json，Agent 在執行時自動判斷是否需要 System Governor，實現真正的動態集成。
