#!/usr/bin/env python3
"""
System Governor Web UI — UAT Test Cases
測試Web UI的第一階段交互功能
"""

import asyncio
import aiosqlite
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

DB_PATH = "/data/governor.db"  # 容器內路徑
WEB_UI_URL = "http://localhost:9091/archive"

class TestCase:
    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.status = "PENDING"
        self.result = None
        self.details = []

    def pass_test(self, message=""):
        self.status = "✅ PASS"
        self.result = message

    def fail_test(self, message=""):
        self.status = "❌ FAIL"
        self.result = message

    def add_detail(self, detail):
        self.details.append(detail)

    def report(self):
        output = f"\n{'='*80}"
        output += f"\n[{self.status}] TC-{len(test_cases)}: {self.name}"
        output += f"\n📋 {self.description}"
        output += f"\n{'-'*80}"
        if self.result:
            output += f"\n結果: {self.result}"
        if self.details:
            output += f"\n詳細信息:"
            for detail in self.details:
                output += f"\n  • {detail}"
        return output

test_cases = []

async def run_test_suite():
    """執行完整的UAT測試套件"""

    # TC-1: 驗證Web UI可訪問
    tc1 = TestCase(
        "Web UI 可訪問",
        "驗證 http://localhost:9091/archive 可以訪問並返回有效HTML"
    )
    test_cases.append(tc1)
    try:
        response = requests.get(WEB_UI_URL, timeout=5)
        if response.status_code == 200:
            tc1.pass_test(f"HTTP {response.status_code} - 頁面正常加載")
            tc1.add_detail(f"內容類型: {response.headers.get('content-type')}")
            tc1.add_detail(f"頁面大小: {len(response.text)} bytes")
        else:
            tc1.fail_test(f"HTTP {response.status_code} - 服務不可用")
    except Exception as e:
        tc1.fail_test(f"連接失敗: {str(e)}")

    # TC-2: 驗證HTML結構
    tc2 = TestCase(
        "HTML 結構完整",
        "驗證頁面包含所有必要的HTML元素和JavaScript"
    )
    test_cases.append(tc2)
    try:
        response = requests.get(WEB_UI_URL)
        soup = BeautifulSoup(response.text, 'html.parser')

        checks = {
            "標題": soup.find('h1', string=lambda x: x and "決策檔案庫" in x),
            "Session卡片": soup.find_all('div', class_='session-card'),
            "JavaScript函數": 'toggleSession' in response.text,
            "CSS樣式": 'session-header' in response.text,
        }

        all_passed = all(checks.values())
        if all_passed:
            tc2.pass_test("所有HTML結構元素存在")
            tc2.add_detail(f"找到 {len(checks['Session卡片'])} 個Session卡片")
        else:
            failed = [k for k, v in checks.items() if not v]
            tc2.fail_test(f"缺少元素: {', '.join(failed)}")
    except Exception as e:
        tc2.fail_test(f"解析失敗: {str(e)}")

    # TC-3: 驗證Session卡片數據正確性
    tc3 = TestCase(
        "Session 卡片數據準確",
        "驗證頁面顯示的Session信息與數據庫一致"
    )
    test_cases.append(tc3)
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row

            # 從DB獲取Session數據
            async with db.execute(
                "SELECT id, topic, status, created_at FROM sessions ORDER BY created_at DESC LIMIT 2"
            ) as cur:
                db_sessions = await cur.fetchall()

            response = requests.get(WEB_UI_URL)
            soup = BeautifulSoup(response.text, 'html.parser')
            html_sessions = soup.find_all('div', class_='session-card')

            if len(html_sessions) == len(db_sessions):
                tc3.pass_test(f"顯示 {len(db_sessions)} 個Session")
                for i, (db_sess, html_sess) in enumerate(zip(db_sessions, html_sessions)):
                    topic = db_sess['topic']
                    session_id = db_sess['id']

                    # 驗證Session標題
                    title_elem = html_sess.find('div', class_='session-title')
                    if title_elem and topic in str(title_elem.text):
                        tc3.add_detail(f"✓ Session {i+1}: '{topic}' - 標題正確")
                    else:
                        tc3.add_detail(f"✗ Session {i+1}: 標題不匹配")

                    # 驗證Status Badge
                    badge = html_sess.find('span', class_='badge')
                    if badge and db_sess['status'] in str(badge.text):
                        tc3.add_detail(f"✓ Session {i+1}: Status '{db_sess['status']}' - 正確")
                    else:
                        tc3.add_detail(f"✗ Session {i+1}: Status 不正確")
            else:
                tc3.fail_test(f"Session數量不匹配 (UI: {len(html_sessions)}, DB: {len(db_sessions)})")
    except Exception as e:
        tc3.fail_test(f"驗證失敗: {str(e)}")

    # TC-4: 驗證統計數據正確
    tc4 = TestCase(
        "統計信息準確",
        "驗證顯示的記錄、階段、報告數量正確"
    )
    test_cases.append(tc4)
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row

            # 獲取第一個Session的詳細數據
            async with db.execute(
                "SELECT id FROM sessions ORDER BY created_at DESC LIMIT 1"
            ) as cur:
                session = await cur.fetchone()

            if not session:
                tc4.fail_test("數據庫中沒有Session")
                return

            session_id = session['id']

            # 計算統計數據
            async with db.execute(
                "SELECT COUNT(*) as cnt FROM records WHERE session_id=?", (session_id,)
            ) as cur:
                record_count = (await cur.fetchone())['cnt']

            async with db.execute(
                "SELECT COUNT(*) as cnt FROM stage_progress WHERE session_id=?", (session_id,)
            ) as cur:
                stage_count = (await cur.fetchone())['cnt']

            async with db.execute(
                "SELECT COUNT(*) as cnt FROM reports WHERE session_id=?", (session_id,)
            ) as cur:
                report_count = (await cur.fetchone())['cnt']

            # 在HTML中驗證這些數字
            response = requests.get(WEB_UI_URL)
            soup = BeautifulSoup(response.text, 'html.parser')

            # 查找第一個Session卡片的統計信息
            first_card = soup.find('div', class_='session-card')
            stats_text = first_card.get_text() if first_card else ""

            checks = {
                "記錄數": str(record_count) in stats_text,
                "階段數": str(stage_count) in stats_text,
                "報告數": str(report_count) in stats_text,
            }

            if all(checks.values()):
                tc4.pass_test("所有統計信息正確")
                tc4.add_detail(f"記錄: {record_count} ✓")
                tc4.add_detail(f"階段: {stage_count} ✓")
                tc4.add_detail(f"報告: {report_count} ✓")
            else:
                failed = [k for k, v in checks.items() if not v]
                tc4.fail_test(f"統計信息不匹配: {', '.join(failed)}")
    except Exception as e:
        tc4.fail_test(f"驗證失敗: {str(e)}")

    # TC-5: 驗證工作流進度顯示
    tc5 = TestCase(
        "工作流進度可視化",
        "驗證進度條、階段狀態正確顯示"
    )
    test_cases.append(tc5)
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row

            async with db.execute(
                "SELECT id FROM sessions ORDER BY created_at DESC LIMIT 1"
            ) as cur:
                session = await cur.fetchone()

            session_id = session['id']

            # 獲取階段進度
            async with db.execute(
                "SELECT stage, status FROM stage_progress WHERE session_id=? ORDER BY stage",
                (session_id,)
            ) as cur:
                stages = await cur.fetchall()

            response = requests.get(WEB_UI_URL)
            soup = BeautifulSoup(response.text, 'html.parser')

            # 驗證進度條存在
            progress_bar = soup.find('div', class_='progress-bar')
            stage_items = soup.find_all('div', class_='stage-item')

            if progress_bar and len(stage_items) == len(stages):
                tc5.pass_test(f"工作流進度可視化正確 ({len(stages)} 個階段)")

                # 驗證階段狀態
                completed = sum(1 for s in stages if s['status'] == 'completed')
                tc5.add_detail(f"已完成: {completed}/{len(stages)} 階段")

                for stage in stages:
                    status_icon = "✓" if stage['status'] == 'completed' else "○"
                    tc5.add_detail(f"  {status_icon} {stage['stage']} - {stage['status']}")
            else:
                tc5.fail_test(f"進度可視化元素不完整 (進度條: {bool(progress_bar)}, 階段: {len(stage_items)}/{len(stages)})")
    except Exception as e:
        tc5.fail_test(f"驗證失敗: {str(e)}")

    # TC-6: 驗證決策記錄詳細信息
    tc6 = TestCase(
        "決策記錄展示",
        "驗證點擊展開後顯示完整的決策記錄"
    )
    test_cases.append(tc6)
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row

            async with db.execute(
                "SELECT id FROM sessions ORDER BY created_at DESC LIMIT 1"
            ) as cur:
                session = await cur.fetchone()

            session_id = session['id']

            # 獲取記錄數據
            async with db.execute(
                "SELECT role, content FROM records WHERE session_id=? LIMIT 2",
                (session_id,)
            ) as cur:
                records = await cur.fetchall()

            response = requests.get(WEB_UI_URL)
            soup = BeautifulSoup(response.text, 'html.parser')

            record_items = soup.find_all('div', class_='record-item')

            if len(record_items) >= len(records):
                tc6.pass_test(f"找到 {len(record_items)} 條決策記錄")

                for i, record in enumerate(records):
                    role = record['role']
                    content_preview = record['content'][:50]

                    # 驗證記錄內容
                    if i < len(record_items):
                        item_text = record_items[i].get_text()
                        if role in item_text:
                            tc6.add_detail(f"✓ 記錄 {i+1}: '{content_preview}...' - 角色正確")
                        else:
                            tc6.add_detail(f"✗ 記錄 {i+1}: 角色不匹配")
            else:
                tc6.fail_test(f"記錄數量不足 (UI: {len(record_items)}, DB: {len(records)})")
    except Exception as e:
        tc6.fail_test(f"驗證失敗: {str(e)}")

    # TC-7: 驗證JavaScript交互性
    tc7 = TestCase(
        "JavaScript 交互",
        "驗證頁面包含正確的JavaScript代碼用於展開/收合"
    )
    test_cases.append(tc7)
    try:
        response = requests.get(WEB_UI_URL)

        required_js = [
            "function toggleSession",
            "classList.toggle('expanded')",
            "session-detail",
        ]

        missing = [js for js in required_js if js not in response.text]

        if not missing:
            tc7.pass_test("JavaScript代碼完整")
            tc7.add_detail("✓ toggleSession函數存在")
            tc7.add_detail("✓ expanded類切換邏輯存在")
            tc7.add_detail("✓ session-detail選擇器存在")
        else:
            tc7.fail_test(f"缺少代碼: {', '.join(missing)}")
    except Exception as e:
        tc7.fail_test(f"驗證失敗: {str(e)}")

    # TC-8: 驗證CSS樣式
    tc8 = TestCase(
        "CSS 樣式完整",
        "驗證頁面包含必要的CSS樣式定義"
    )
    test_cases.append(tc8)
    try:
        response = requests.get(WEB_UI_URL)

        required_css_classes = [
            ".session-card",
            ".session-header",
            ".progress-bar",
            ".progress-fill",
            ".stage-item",
            ".record-item",
            ".badge-active",
        ]

        missing = [css for css in required_css_classes if css[1:] not in response.text]

        if not missing:
            tc8.pass_test("所有CSS類定義存在")
            for css in required_css_classes:
                tc8.add_detail(f"✓ {css}")
        else:
            tc8.fail_test(f"缺少CSS類: {', '.join(missing)}")
    except Exception as e:
        tc8.fail_test(f"驗證失敗: {str(e)}")

def print_summary():
    """打印測試摘要"""
    passed = sum(1 for tc in test_cases if "PASS" in tc.status)
    failed = sum(1 for tc in test_cases if "FAIL" in tc.status)
    total = len(test_cases)

    print("\n" + "="*80)
    print("🧪 SYSTEM GOVERNOR WEB UI — UAT TEST SUMMARY")
    print("="*80)

    for tc in test_cases:
        print(tc.report())

    print("\n" + "="*80)
    print(f"📊 TEST RESULTS: {passed}/{total} PASSED, {failed}/{total} FAILED")
    print("="*80)
    print(f"✅ 成功: {passed}")
    print(f"❌ 失敗: {failed}")
    print(f"📈 成功率: {(passed/total)*100:.1f}%")
    print("="*80 + "\n")

    return failed == 0

if __name__ == "__main__":
    print("\n🚀 啟動 System Governor Web UI UAT 測試...")
    print(f"⏰ 開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 測試URL: {WEB_UI_URL}")
    print(f"💾 數據庫: {DB_PATH}\n")

    success = asyncio.run(run_test_suite())

    if print_summary():
        print("🎉 所有測試通過！Web UI第一階段功能驗證成功。\n")
    else:
        print("⚠️  某些測試失敗，請檢查上述詳細信息。\n")
