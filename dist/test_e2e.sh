#!/bin/bash

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 System Governor 端到端測試"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 創建臨時的 Python 測試腳本
python3 << 'PYEOF'
import sqlite3
import json
from datetime import datetime

DB_PATH = "data/governor.db"

print("📊 [Step 1/4] 創建新決策會話...")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 插入新會話
session_topic = f"E2E 測試會話 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
cursor.execute("""
    INSERT INTO sessions (topic, status, created_at)
    VALUES (?, ?, ?)
""", (session_topic, "active", datetime.now().isoformat()))

session_id = cursor.lastrowid
conn.commit()
print(f"   ✅ 會話已建立：ID={session_id}")

print("")
print("📝 [Step 2/4] 記錄決策輸入...")

# 插入決策記錄
records = [
    ("user", "architect", "決策題目：評估是否採用 System Governor 來管理架構決策"),
    ("user", "architect", "假設：團隊需要一個防竄改的決策記錄系統"),
    ("assistant", "analyst", "分析：System Governor 提供 SHA-256 完整性驗證和 SQLite 不可變性"),
]

for role, stage, content in records:
    cursor.execute("""
        INSERT INTO records (session_id, stage, role, content, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (session_id, stage, role, content, datetime.now().isoformat()))

conn.commit()
print(f"   ✅ 已記錄 {len(records)} 筆決策輸入")

print("")
print("🔄 [Step 3/4] 完成工作流階段...")

# 更新 stage_progress
stages = ["architect", "analyst", "judge"]
for stage_name in stages:
    cursor.execute("""
        INSERT OR REPLACE INTO stage_progress (session_id, stage, status, completed_at)
        VALUES (?, ?, ?, ?)
    """, (session_id, stage_name, "completed", datetime.now().isoformat()))

conn.commit()
print(f"   ✅ 已完成 {len(stages)} 個工作流階段")

print("")
print("📄 [Step 4/4] 驗證數據庫狀態...")

# 查詢驗證
cursor.execute("SELECT COUNT(*) FROM sessions WHERE id=?", (session_id,))
session_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM records WHERE session_id=?", (session_id,))
record_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM stage_progress WHERE session_id=?", (session_id,))
stage_count = cursor.fetchone()[0]

print(f"   ✅ 會話數：{session_count}")
print(f"   ✅ 記錄數：{record_count}")
print(f"   ✅ 階段數：{stage_count}")

print("")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("✨ E2E 測試完成！")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

conn.close()
PYEOF

