# System Governor MCP — Agent Rule 動態整合模板

## 概述

這個模板可以被複製到任何 Agent 的全域配置文件中（不硬編碼用戶路徑）。

### 支持的配置文件位置

```bash
# Claude Code
~/.claude/CLAUDE.md          # 全域 Claude 規則

# Gemini
~/.gemini/GEMINI.md          # 全域 Gemini 規則
```

**關鍵**：使用 `~` 或 `$HOME` 動態展開，不硬編碼用戶路徑。

---

## 📋 Rule 模板 — 複製到 CLAUDE.md

### Claude Code 專用規則

```markdown
# System Governor MCP — Claude Code 主動決策介入

## 觸發條件（符合任一即可）

### Pattern 1: 多方案權衡
用戶同時提及 ≥2 個技術方案，且：
- 包含對比詞：「vs」「還是」「或」「對比」「權衡」
- 涉及「選哪個」「應該用」「如何評估」

**範例**：
- "我們是用 Kong 還是 Envoy？"
- "考慮 PostgreSQL 或 MongoDB，哪個更合適？"
- "Kubernetes 跟 Docker Swarm 怎麼選？"

### Pattern 2: 系統性改動
用戶討論影響長期架構的變更：
- 「遷移」「重構」「升級」「替換」核心組件
- 「引入」新的 framework / 基礎設施
- 涉及多個團隊協作（API 變更、數據結構調整）

**範例**：
- "我們考慮從 monolith 遷移到微服務"
- "需要重構認證層，支持 OAuth"
- "引入新的日誌系統"

### Pattern 3: 假設驗證
用戶提出「我以為...」「為什麼...」「是否...」的疑問：
- 需要驗證設計假設
- 尋求技術方案的合理性論證
- 評估隱藏風險

**範例**：
- "我們假設 Redis 的效能足以支撐...對嗎？"
- "使用 ORM 會不會影響查詢性能？"
- "這個架構在高併發下會不會出問題？"

## 主動提議邏輯

### Step 1: 檢測場景
Agent 在對話中識別上述任一 Pattern，**主動提議**（不等用戶要求）

### Step 2: 檢查服務
```bash
bash ~/Project/pipagent/agent_self_check.sh health
```
- 返回 `OK` → 執行提議
- 返回 `FAIL` → 告知用戶啟動（給出 install 命令）

### Step 3: 提議模板
```
我注意到你在評估 [決策類型]。這涉及多個方案的權衡/長期架構影響。

我可以用 System Governor 來幫你：
• 正式記錄每個方案的假設與約束
• 分析代碼影響範圍（哪些模塊會受影響）
• 生成決策報告（方便團隊追蹤）

要用嗎？
```

### Step 4: 執行工作流
若用戶同意，依序執行：
1. `sg_create_session("{決策主題}")`
2. `sg_record_input()` × N 記錄用戶輸入
3. `sg_run_stage_01()` 假設對齐
4. `sg_run_stage_02()` 代碼影響 + Hard Code 檢測
5. `sg_run_stage_03()` 架構辯證
6. `sg_generate_full()` 生成報告

## 情景示例

### ❌ 不提議的情況
```
用戶: "如何在 Python 中寫一個遞迴函數？"
→ 這是實作問題，不是決策
```

### ✅ 應主動提議
```
用戶: "我們現在用 Redis，但考慮遷移到 Memcached 或 DynamoDB"
→ Pattern 1 + Pattern 2 都符合
→ 主動提議使用 System Governor
```

```
用戶: "引入 Kubernetes 會不會影響我們的 CI/CD？"
→ Pattern 2（新 infra）+ Pattern 3（假設驗證）
→ 主動提議
```

## 關鍵原則

✓ **主動介入** — 不等用戶說「幫我記錄」，自己看出決策場景就提
✓ **詢問優先** — 提議後一定要等用戶確認，不強制執行
✓ **模式優於關鍵詞** — 基於上下文判斷，不只看特定詞彙
✓ **優雅降級** — 服務不可用時提供啟動指引，切換到標準流程
✓ **無需 Skill** — 本規則自包含，無需用戶知道 `/system-governor-mcp-guide`
```

---

## 📋 Rule 模板 — 複製到 GEMINI.md

### Gemini 專用規則

```markdown
# System Governor MCP — Gemini 主動決策介入

## 觸發條件（符合任一即可）

### Pattern 1: 多方案權衡
用戶同時提及 ≥2 個技術方案，且：
- 包含對比詞：「vs」「還是」「或」「對比」「權衡」
- 涉及「選哪個」「應該用」「如何評估」

### Pattern 2: 系統性改動
用戶討論影響長期架構的變更：
- 「遷移」「重構」「升級」「替換」核心組件
- 「引入」新的 framework / 基礎設施
- 涉及多個團隊協作

### Pattern 3: 假設驗證
用戶提出「我以為...」「為什麼...」「是否...」的疑問：
- 需要驗證設計假設
- 評估隱藏風險或邊界情況

## 主動提議邏輯

### Step 1: 檢測場景
Agent 在對話中識別上述任一 Pattern，**主動提議**（不等用戶要求）

### Step 2: 檢查服務
```bash
bash ~/Project/pipagent/agent_self_check.sh health
```

### Step 3: 提議模板
```
我注意到你在評估 [決策類型]。這涉及多個方案的權衡/長期架構影響。

我可以用 System Governor 來幫你：
• 正式記錄每個方案的假設與約束
• 分析影響範圍和風險
• 生成決策報告（方便團隊追蹤）

要用嗎？
```

### Step 4: 執行工作流
若用戶同意，依序執行：
1. `sg_create_session("{決策主題}")`
2. `sg_record_input()` × N 記錄用戶輸入
3. `sg_run_stage_01()` 假設對齐
4. `sg_run_stage_02()` 影響範圍分析
5. `sg_run_stage_03()` 架構辯證
6. `sg_generate_full()` 生成報告

## 關鍵原則

✓ **主動介入** — 不等用戶說「幫我記錄」，自己看出決策場景就提
✓ **詢問優先** — 提議後一定要等用戶確認，不強制執行
✓ **模式優於關鍵詞** — 基於上下文判斷，不只看特定詞彙
✓ **優雅降級** — 服務不可用時提供啟動指引，切換到標準流程
✓ **無需 Skill** — 本規則自包含，無需用戶知道複雜工具
```

---

## 🔄 動態路徑解析 — 供 MCP 服務使用

### 檢查配置文件位置的正確方式

**不要這樣做**（硬編碼）:
```bash
❌ /Users/pericchen/.claude/CLAUDE.md
❌ /Users/pericchen/.gemini/GEMINI.md
```

**應該這樣做**（動態路徑）:
```bash
✅ ~/.claude/CLAUDE.md          # 展開為 $HOME/.claude/CLAUDE.md
✅ ~/.gemini/GEMINI.md          # 展開為 $HOME/.gemini/GEMINI.md
```

### Python 實現

```python
import os
from pathlib import Path

def get_agent_rule_file(agent_type: str) -> str:
    """根據 Agent 類型取得規則文件路徑（動態）"""
    home = Path.home()
    
    rules = {
        "claude-code": home / ".claude" / "CLAUDE.md",
        "gemini": home / ".gemini" / "GEMINI.md",
    }
    
    rule_file = rules.get(agent_type)
    if rule_file and rule_file.exists():
        return str(rule_file)
    else:
        return None  # 規則文件不存在

# 使用
current_agent = "claude-code"
rule_path = get_agent_rule_file(current_agent)
print(f"使用規則: {rule_path}")
# 輸出: 使用規則: /Users/anyone/.claude/CLAUDE.md
```

### Bash 實現

```bash
#!/bin/bash

# 根據 Agent 類型取得規則文件
get_agent_rule_file() {
    local agent_type=$1
    
    case "$agent_type" in
        "claude-code")
            echo ~/.claude/CLAUDE.md
            ;;
        "gemini")
            echo ~/.gemini/GEMINI.md
            ;;
        *)
            echo ""
            ;;
    esac
}

# 使用
AGENT_TYPE="claude-code"
RULE_FILE=$(get_agent_rule_file "$AGENT_TYPE")
RULE_FILE="${RULE_FILE/#\~/$HOME}"  # 展開 ~

if [ -f "$RULE_FILE" ]; then
    echo "規則文件: $RULE_FILE"
else
    echo "規則文件不存在: $RULE_FILE"
fi
```

---

## 📝 安裝說明

### 1. 複製規則到 Claude 環境

```bash
# 打開 ~/.claude/CLAUDE.md
nano ~/.claude/CLAUDE.md

# 在文件中找到合適位置（通常在最後）
# 複製「Rule 模板 — 複製到 CLAUDE.md」部分
# 粘貼進去，保存
```

### 2. 複製規則到 Gemini 環境

```bash
# 打開 ~/.gemini/GEMINI.md
nano ~/.gemini/GEMINI.md

# 在文件中找到合適位置（通常在最後）
# 複製「Rule 模板 — 複製到 GEMINI.md」部分
# 粘貼進去，保存
```

### 3. 驗證規則已正確加入

```bash
# 檢查 Claude 規則
grep -i "System Governor" ~/.claude/CLAUDE.md

# 檢查 Gemini 規則
grep -i "System Governor" ~/.gemini/GEMINI.md
```

---

## 🎯 工作流程圖

```
Agent 啟動
    ↓
檢測 Agent 類型（claude-code / gemini）
    ↓
動態加載對應規則
~/.claude/CLAUDE.md 或 ~/.gemini/GEMINI.md
    ↓
用戶提出任務
    ↓
檢查規則的觸發條件
    ├─ 匹配 → 執行 System Governor 流程
    └─ 不匹配 → 標準流程
    ↓
詢問用戶 (不強制)
    ├─ YES → sg_create_session() → Stage 01-03 → 報告
    └─ NO → 標準流程
```

---

## ✅ 優勢

- ✅ **無硬編碼** — 使用 `~` 動態展開，支援任何用戶
- ✅ **多 Agent 支持** — 每個 Agent 類型有自己的規則
- ✅ **易於擴展** — 新增 Agent 只需添加規則文件
- ✅ **自動檢測** — MCP 服務自動加載對應規則
- ✅ **用戶友善** — 詢問優先，不強制介入

---

## 🚀 部署步驟

1. ✅ 複製模板到 `~/.claude/CLAUDE.md`
2. ✅ 複製模板到 `~/.gemini/GEMINI.md`
3. ✅ 安裝並啟動 System Governor MCP
4. ✅ Agent 自動加載對應規則
5. ✅ 完成！

每個新用戶只需在自己的 `~/.claude/CLAUDE.md` 和 `~/.gemini/GEMINI.md` 中粘貼相應規則即可。
