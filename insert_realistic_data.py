#!/usr/bin/env python3
"""
插入真實的、完整的多轮決策流程數據
模擬一個完整的架構決策過程
"""

import sqlite3
import uuid
import hashlib
from datetime import datetime, timedelta
import json

DB_PATH = "/Users/pericchen/Project/pipagent/dist/data/governor.db"

def sha256_hash(content):
    """生成SHA-256雜湊"""
    return hashlib.sha256(content.encode()).hexdigest()

def insert_realistic_decision():
    """插入真實的決策流程"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 建立新的Session
    session_id = str(uuid.uuid4())
    topic = "微服務架構與單體應用的權衡評估"
    created_at = (datetime.now() - timedelta(days=1)).isoformat()

    cursor.execute("""
        INSERT INTO sessions (id, topic, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
    """, (session_id, topic, 'active', created_at, created_at))

    print(f"✓ 建立新Session: {topic}")
    print(f"  ID: {session_id}\n")

    # 記錄序列 - 完整的決策過程
    records = [
        {
            'role': 'user',
            'content': '我們需要決定是否應該將現有的單體應用重構為微服務架構。目前應用有5個主要模塊，團隊規模約20人。',
            'stage': 'analysis'
        },
        {
            'role': 'assistant',
            'content': '假設1：現有單體應用存在模塊間耦合度高的問題，導致開發迭代速度下降\n假設2：團隊具備容器化和分佈式系統的基礎知識\n假設3：運維基礎設施支持容器化部署（Kubernetes或Docker Swarm）',
            'stage': 'analysis'
        },
        {
            'role': 'assistant',
            'content': '分析維度1：當前技術債與發展瓶頸\n- 單體應用部署時間：30分鐘\n- 修改單個模塊影響範圍：全應用\n- 小隊獨立迭代週期：2周\n\n分析維度2：微服務遷移成本\n- 基礎設施建設成本：3人月\n- 應用改造成本：8-10人月\n- 持續運維成本：額外增加1-2個運維人員',
            'stage': 'analysis'
        },
        {
            'role': 'assistant',
            'content': '驗證指標：\n✓ 獨立部署能力：目前不支持 → 微服務可達成\n✓ 開發效率提升：預期提升30-40%\n✓ 系統可靠性：微服務可獨立故障隔離\n✓ 運維複雜度：微服務增加，但可通過自動化降低\n\n成本效益：投入成本 vs 收益週期約為12-18個月',
            'stage': 'analysis'
        },
        {
            'role': 'assistant',
            'content': '建議方案：分階段遷移\n\nPhase 1（第1-3個月）：基礎設施建設\n- 建立Kubernetes集群\n- 設置CI/CD流程\n- 建立服務通訊標準\n\nPhase 2（第4-9個月）：核心服務遷移\n- 首先遷移用戶管理服務（最獨立）\n- 其次遷移訂單服務\n- 最後處理支付服務\n\nPhase 3（第10-12個月）：優化與穩定\n- 性能調優\n- 監控告警完善\n- 文檔與知識轉移',
            'stage': 'analysis'
        },
        {
            'role': 'assistant',
            'content': '決策收斂：基於以上分析，建議採納微服務架構重構，但實施方式為\"漸進式遷移\"而非\"一步到位\"。\n\n核心理由：\n1. 問題本質：單體應用已成為團隊發展的瓶頸，技術債務在積累\n2. 時間適當：公司規模與團隊能力已支持這一決策\n3. 風險可控：通過分階段實施，可降低失敗風險\n4. 預期收益：12-18個月內可收回投資成本，長期提升團隊效能\n\n決策狀態：✓ 已批准 | 下一步：詳細技術方案設計',
            'stage': 'analysis'
        }
    ]

    print("決策記錄流程：\n")
    for i, record in enumerate(records, 1):
        record_id = str(uuid.uuid4())
        content = record['content']
        role = record['role']
        stage = record['stage']

        # 計算SHA-256
        hash_val = sha256_hash(content)

        cursor.execute("""
            INSERT INTO records (id, session_id, role, content, stage, sha256_hash, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (record_id, session_id, role, content, stage, hash_val, created_at))

        # 印出紀錄摘要
        role_emoji = "👤" if role == "user" else "🤖"
        content_preview = content.split('\n')[0][:60]
        print(f"{i}. {role_emoji} {role.upper()}")
        print(f"   {content_preview}...")
        if i < len(records):
            print()

    print("\n" + "="*80)

    # 設置工作流階段
    stages = [
        {'stage': 'analyst', 'status': 'completed', 'order': 1},
        {'stage': 'architect', 'status': 'completed', 'order': 2},
        {'stage': 'judge', 'status': 'completed', 'order': 3},
    ]

    print("\n工作流階段進度：\n")
    for stage_info in stages:
        stage_name = stage_info['stage']
        status = stage_info['status']
        completed_at = (datetime.now() - timedelta(days=1, hours=-stage_info['order'])).isoformat()

        cursor.execute("""
            INSERT INTO stage_progress (id, session_id, stage, status, completed_at)
            VALUES (?, ?, ?, ?, ?)
        """, (str(uuid.uuid4()), session_id, stage_name, status, completed_at))

        status_icon = "✓" if status == "completed" else "○"
        print(f"{status_icon} {stage_name.upper()} - {status}")

    print("\n" + "="*80)
    print(f"\n✅ 成功插入完整的決策流程")
    print(f"   Session ID: {session_id}")
    print(f"   記錄數: {len(records)}")
    print(f"   工作流階段: {len(stages)}")
    print(f"\n📊 訪問: http://localhost:9091/archive\n")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    insert_realistic_decision()
