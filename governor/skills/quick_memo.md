# Quick Memo Skill
快速記錄需求確認、想法發想、或 Memo 存證的標準程序。

## 觸發時機
- 訪談結束後需要快速留存共識
- 有零散想法需要記錄但不確定是否成案
- 需要一份輕量存證供未來回查

## 操作步驟

### Step 1: 建立 Session（若尚未建立）
```
sg_create_session(topic="本次討論主題", stakeholders=["PM", "Engineer"])
```

### Step 2: 記錄訪談要點（每段對話一筆）
```
sg_record_input(
  session_id="sg-xxx",
  role="user",        # user | pm | engineer | stakeholder
  stage="interview",  # 訪談主體用 interview
  content="使用者的原始話語，不修改",
  source_note="（選填）說明情境，如：PM 在週會提出"
)
```

### Step 3: 記錄 Memo / 想法
```
sg_record_input(session_id="sg-xxx", stage="memo", content="...")
```

### Step 4: 記錄最終結論
```
sg_record_input(session_id="sg-xxx", stage="conclusion", content="...")
```

### Step 5: 生成 Quick Memo 報告
```
sg_generate_memo(session_id="sg-xxx")
```

## ⚠️ 鐵則
- content 必須是使用者的原始文字，嚴禁 AI 摘要或補全
- 若有疑慮，停下來問使用者而非推測
- 生成報告前先呼叫 `sg_check_reminders` 確認沒有遺漏
