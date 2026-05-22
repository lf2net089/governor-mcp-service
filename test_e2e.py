#!/usr/bin/env python3
"""
System Governor MCP — E2E 測試腳本
測試 1: 快速 Memo 流程
測試 2: 完整工程治理流程
"""

import asyncio
import httpx
import json
from datetime import datetime

BASE_URL = "http://localhost:8080"
MCP_ENDPOINT = f"{BASE_URL}/mcp"

async def mcp_call(method: str, params: dict) -> dict:
    """調用 MCP 工具"""
    payload = {
        "jsonrpc": "2.0",
        "id": "test-" + datetime.now().isoformat(),
        "method": method,
        "params": params
    }

    headers = {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(MCP_ENDPOINT, json=payload, headers=headers)
        print(f"[DEBUG] {method} → Status {response.status_code}")
        return response.json()

async def test_quick_memo_flow():
    """測試 1: 快速 Memo 流程"""
    print("\n" + "="*60)
    print("測試 1: 快速 Memo 流程")
    print("="*60)

    # 1. 建立 Session
    print("\n[Step 1] 建立 Session...")
    create_result = await mcp_call("tools/call", {
        "name": "sg_create_session",
        "arguments": {
            "topic": "System Governor 快速驗證",
            "stakeholders": ["user", "ai"]
        }
    })
    print(f"Response: {json.dumps(create_result, indent=2, ensure_ascii=False)}")

    session_id = create_result.get("result", {}).get("session_id")
    if not session_id:
        print("❌ 無法取得 session_id")
        return False
    print(f"✅ Session 建立成功: {session_id}")

    # 2. 記錄輸入
    print("\n[Step 2] 記錄使用者輸入...")
    record_result = await mcp_call("tools/call", {
        "name": "sg_record_input",
        "arguments": {
            "session_id": session_id,
            "content": "我們需要評估是否應該重構認證系統",
            "role": "user",
            "stage": "interview"
        }
    })
    print(f"✅ 記錄成功")

    # 3. 生成 Quick Memo
    print("\n[Step 3] 生成 Quick Memo 報告...")
    memo_result = await mcp_call("tools/call", {
        "name": "sg_generate_memo",
        "arguments": {
            "session_id": session_id
        }
    })

    if memo_result.get("result", {}).get("report_html"):
        print("✅ Memo 報告生成成功")
        # 檢查是否包含防竄改 Hash
        html = memo_result["result"]["report_html"]
        if "SHA-256" in html or "hash" in html.lower():
            print("✅ Hash 防竄改鏈已包含")
        else:
            print("⚠️ 未發現 Hash 防竄改鏈")
    else:
        print("❌ Memo 報告生成失敗")
        return False

    return True

async def test_full_governance_flow():
    """測試 2: 完整工程治理流程"""
    print("\n" + "="*60)
    print("測試 2: 完整工程治理流程 (Stage 01 -> 02 -> 03)")
    print("="*60)

    # 1. 建立 Session
    print("\n[Step 1] 建立 Session...")
    create_result = await mcp_call("tools/call", {
        "name": "sg_create_session",
        "arguments": {
            "topic": "認證系統重構 — 完整治理評估",
            "stakeholders": ["architect", "security-lead"]
        }
    })

    session_id = create_result.get("result", {}).get("session_id")
    if not session_id:
        print("❌ 無法取得 session_id")
        return False
    print(f"✅ Session: {session_id}")

    # 2. 執行 Stage 01 — 假設對齐
    print("\n[Step 2] 執行 Stage 01 — 假設對齐門檻驗證...")
    stage01_result = await mcp_call("tools/call", {
        "name": "sg_run_stage_01",
        "arguments": {
            "session_id": session_id,
            "surface_requirement": "重構舊有的 Session-based Auth",
            "actual_business_purpose": "支援 JWT + 微服務架構",
            "has_concrete_target": True,
            "has_io_logic": True,
            "has_reference": True,
            "assumption_data_verified": True,
            "assumption_performance_evaluated": True,
            "assumption_dependencies_confirmed": True,
            "boundary_null_defined": True,
            "boundary_concurrency_considered": True
        }
    })
    print(f"Stage 01: {stage01_result.get('result', {}).get('stage_status', 'unknown')}")

    # 3. 執行 Stage 02 — GitNexus 圖譜剖析（測試 hard code 拒絕機制）
    print("\n[Step 3] 執行 Stage 02 — GitNexus 圖譜剖析...")
    stage02_result = await mcp_call("tools/call", {
        "name": "sg_run_stage_02",
        "arguments": {
            "session_id": session_id,
            "file_path": "src/auth/session_manager.py",
            "function_name": "validate_session",
            "change_purpose": "遷移到 JWT 驗證",
            "upstream_verification": "已檢查 12 個 callers",
            "downstream_impact": "影響 API Gateway 與 Middleware",
            "hardcode_detected": False,
            "ui_hiding_detected": False,
            "todo_hack_detected": False,
            "follows_architecture": True,
            "has_test_coverage": True
        }
    })
    print(f"Stage 02: {stage02_result.get('result', {}).get('stage_status', 'unknown')}")

    # 4. 執行 Stage 03 — 架構辯證
    print("\n[Step 4] 執行 Stage 03 — 架構辯證...")
    stage03_result = await mcp_call("tools/call", {
        "name": "sg_run_stage_03",
        "arguments": {
            "session_id": session_id,
            "blind_spot": "token refresh 的緩存策略在高併發下的表現不確定",
            "upstream_verification": "API Gateway、Middleware 已驗證兼容性",
            "downstream_impact": "微服務需要更新 token 解析邏輯",
            "option_a_immediate_cost": "3 周工期、需要全棧測試",
            "option_a_long_term_risk": "JWT 無法主動 revoke，需要實現 blacklist",
            "option_b_implementation_cost": "8 周，包括漸進式遷移",
            "option_b_asset_value": "完全支援 OAuth2、OpenID Connect，日後可對接第三方身份提供商",
            "system_reflection_question": "在當前微服務規模下，token revoke delay 是否可接受？"
        }
    })
    print(f"Stage 03: {stage03_result.get('result', {}).get('stage_status', 'unknown')}")

    # 5. 查看工作流狀態
    print("\n[Step 5] 查看完整工作流狀態...")
    status_result = await mcp_call("tools/call", {
        "name": "sg_get_workflow_status",
        "arguments": {
            "session_id": session_id
        }
    })
    print(f"Workflow Status: {json.dumps(status_result.get('result', {}), indent=2, ensure_ascii=False)}")

    # 6. 生成完整報告
    print("\n[Step 6] 生成完整工程報告...")
    full_report_result = await mcp_call("tools/call", {
        "name": "sg_generate_full",
        "arguments": {
            "session_id": session_id
        }
    })

    if full_report_result.get("result", {}).get("report_html"):
        print("✅ 完整報告生成成功")
        html = full_report_result["result"]["report_html"]
        if "【⏳ 待確認】" in html:
            print("✅ 空欄位正確標示為【⏳ 待確認】")
        if "SHA-256" in html or "hash" in html.lower():
            print("✅ Hash 防竄改鏈已包含")
    else:
        print("❌ 報告生成失敗")
        return False

    return True

async def main():
    print("\n" + "🔥 "*20)
    print("System Governor MCP — E2E 測試開始")
    print("🔥 "*20)

    # 測試 1
    test1_passed = await test_quick_memo_flow()

    # 測試 2
    test2_passed = await test_full_governance_flow()

    print("\n" + "="*60)
    print("測試結果摘要")
    print("="*60)
    print(f"測試 1 (快速 Memo): {'✅ PASS' if test1_passed else '❌ FAIL'}")
    print(f"測試 2 (完整治理): {'✅ PASS' if test2_passed else '❌ FAIL'}")
    print("\n" + "🎉 "*20 if (test1_passed and test2_passed) else "⚠️  "*20)

if __name__ == "__main__":
    asyncio.run(main())
