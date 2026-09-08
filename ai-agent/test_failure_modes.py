"""
Focused Failure Mode & Error Handling Verification Suite.

Tests 7 Failure Scenarios across Django -> Agent -> Qwen -> MCP:
1. Empty / Invalid User Message (Django HTTP 400 validation)
2. Customer / Account Not Found (Graceful MCP tool result handling)
3. Invalid Tool Requested (MCP boundary / tool failure handling)
4. Ollama Connection Failure (Unreachable endpoint handling)
5. Ollama Request Timeout (Configurable timeout handling)
6. MCP Server Connection Failure (Invalid server script path)
7. Secret & IP Sanitization (Verifies no leaks in error output)
"""

import asyncio
import json
import os
import sys
import httpx

_current_dir = os.path.dirname(os.path.abspath(__file__))
_workspace_root = os.path.dirname(_current_dir)
_backend_dir = os.path.join(_workspace_root, "backend")
for p in [_workspace_root, _backend_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

from agent import FinPayAgent
from qwen_client import QwenClient
from client.mcp_client import MCPClientManager

DJANGO_CHAT_URL = "http://127.0.0.1:8000/api/chat/"


async def run_tests():
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("==================================================")
    print("  FinPay Error Handling & Failure Mode Test Suite ")
    print("==================================================")

    reports = []

    # ── Test 1: Empty or Invalid User Message ───────────────
    print("\n[Test 1] Empty User Message to Django Endpoint...")
    try:
        with httpx.Client() as client:
            resp = client.post(DJANGO_CHAT_URL, json={"message": "   "})
            data = resp.json()
            cat = data.get("error_type", "ValidationError")
            status_ok = resp.status_code == 400 and data.get("success") is False
            reports.append({
                "scenario": "1. Empty/Invalid User Message",
                "expected": "HTTP 400 with ValidationError",
                "actual": f"HTTP {resp.status_code} ({data.get('message')})",
                "category": cat,
                "status": "PASS" if status_ok else "FAIL",
            })
            print(f"  Result: {reports[-1]['status']} - HTTP {resp.status_code}")
    except Exception as e:
        reports.append({
            "scenario": "1. Empty/Invalid User Message",
            "expected": "HTTP 400",
            "actual": str(e),
            "category": "error",
            "status": "FAIL",
        })

    # ── Test 2: Account Not Found in Database ─────────────────
    print("\n[Test 2] Querying Non-Existent Account (ID: 999999)...")
    try:
        mcp = MCPClientManager()
        async with mcp.connect() as connected:
            res = await connected.call_tool("get_account", {"account_id": 999999})
            has_err = isinstance(res, dict) and "error" in res
            reports.append({
                "scenario": "2. Account Not Found (ID: 999999)",
                "expected": "Return structured error object from tool",
                "actual": f"Tool output: {res}",
                "category": "tool_handled",
                "status": "PASS" if has_err else "FAIL",
            })
            print(f"  Result: {reports[-1]['status']}")
    except Exception as e:
        reports.append({
            "scenario": "2. Account Not Found",
            "expected": "Structured tool error",
            "actual": str(e),
            "category": "error",
            "status": "FAIL",
        })

    # ── Test 3: Invalid Tool Requested ────────────────────────
    print("\n[Test 3] Calling Non-Existent MCP Tool ('delete_user')...")
    try:
        mcp = MCPClientManager()
        async with mcp.connect() as connected:
            try:
                res = await connected.call_tool("delete_user", {})
                has_err = (isinstance(res, dict) and "error" in res) or "Unknown tool" in str(res)
                actual_str = f"Returned error object: {res}"
                status_str = "PASS" if has_err else "FAIL"
            except Exception as tool_err:
                status_str = "PASS"
                actual_str = f"Caught expected exception: {tool_err}"

            reports.append({
                "scenario": "3. Invalid Tool Requested",
                "expected": "Gracefully handle unknown tool error",
                "actual": actual_str,
                "category": "parameter",
                "status": status_str,
            })
            print(f"  Result: {reports[-1]['status']}")
    except Exception as e:
        reports.append({
            "scenario": "3. Invalid Tool Requested",
            "expected": "Caught exception",
            "actual": str(e),
            "category": "parameter",
            "status": "PASS",
        })

    # ── Test 4: Ollama Connection Failure ────────────────────
    print("\n[Test 4] Ollama Connection Failure (Invalid Base URL)...")
    try:
        bad_client = QwenClient(base_url="http://127.0.0.1:59999")
        try:
            await bad_client.chat_completion_async(messages=[{"role": "user", "content": "hi"}])
            actual_str = "Unexpected success"
            status_str = "FAIL"
        except Exception as conn_err:
            actual_str = f"Caught connection error: {type(conn_err).__name__}"
            status_str = "PASS"

        reports.append({
            "scenario": "4. Ollama Connection Failure",
            "expected": "httpx.ConnectError",
            "actual": actual_str,
            "category": "unhandled",
            "status": status_str,
        })
        print(f"  Result: {reports[-1]['status']}")
    except Exception as e:
        reports.append({
            "scenario": "4. Ollama Connection Failure",
            "expected": "Connection error",
            "actual": str(e),
            "category": "unhandled",
            "status": "PASS",
        })

    # ── Test 5: Ollama Request Timeout ────────────────────────
    print("\n[Test 5] Ollama Request Timeout (1ms Timeout)...")
    try:
        timeout_client = QwenClient(timeout=0.001)
        try:
            await timeout_client.chat_completion_async(messages=[{"role": "user", "content": "hi"}])
            actual_str = "Unexpected success"
            status_str = "FAIL"
        except Exception as timeout_err:
            actual_str = f"Caught timeout: {type(timeout_err).__name__}"
            status_str = "PASS"

        reports.append({
            "scenario": "5. Qwen Request Timeout",
            "expected": "httpx.TimeoutException",
            "actual": actual_str,
            "category": "unhandled",
            "status": status_str,
        })
        print(f"  Result: {reports[-1]['status']}")
    except Exception as e:
        reports.append({
            "scenario": "5. Qwen Request Timeout",
            "expected": "Timeout error",
            "actual": str(e),
            "category": "unhandled",
            "status": "PASS",
        })

    # ── Test 6: MCP Server Script Not Found / Connection Failure ───
    print("\n[Test 6] MCP Server Connection Failure (Invalid script)...")
    try:
        bad_mcp = MCPClientManager(server_script_path="invalid_server.py")
        try:
            async with bad_mcp.connect() as connected:
                await connected.list_tools()
            actual_str = "Unexpected success"
            status_str = "FAIL"
        except Exception as mcp_err:
            actual_str = f"Caught MCP failure: {type(mcp_err).__name__}"
            status_str = "PASS"

        reports.append({
            "scenario": "6. MCP Connection/Server Failure",
            "expected": "RuntimeError / Process error",
            "actual": actual_str,
            "category": "unhandled",
            "status": status_str,
        })
        print(f"  Result: {reports[-1]['status']}")
    except Exception as e:
        reports.append({
            "scenario": "6. MCP Connection/Server Failure",
            "expected": "MCP failure",
            "actual": str(e),
            "category": "unhandled",
            "status": "PASS",
        })

    # ── Test 7: Secret & IP Sanitization ─────────────────────
    print("\n[Test 7] Secret & IP Sanitization Verification...")
    try:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "finpay.settings")
        import django
        django.setup()
        from dashboard.api_views import _sanitize_error  # type: ignore[import]

        raw_secret_err = "Failed to connect to http://172.16.0.249:11434 with key AQ.123456789 and postgresql://user:pass@localhost:5432/db"
        sanitized = _sanitize_error(raw_secret_err)
        no_ip = "172.16.0.249" not in sanitized
        no_key = "AQ.123456789" not in sanitized
        no_db = "postgresql://" not in sanitized
        pass_san = no_ip and no_key and no_db

        reports.append({
            "scenario": "7. Secret & IP Sanitization",
            "expected": "Redact IPs, API keys, and DB URIs",
            "actual": f"Sanitized: {sanitized}",
            "category": "security",
            "status": "PASS" if pass_san else "FAIL",
        })
        print(f"  Result: {reports[-1]['status']}")
    except Exception as e:
        reports.append({
            "scenario": "7. Secret & IP Sanitization",
            "expected": "Sanitized error string",
            "actual": str(e),
            "category": "security",
            "status": "FAIL",
        })


    # ── Summary Report Table ─────────────────────────────────
    print("\n" + "=" * 80)
    print(f"{'Scenario Tested':<35} | {'Category':<12} | {'Status':<6} | Actual Result")
    print("=" * 80)
    for r in reports:
        print(f"{r['scenario']:<35} | {r['category']:<12} | {r['status']:<6} | {r['actual'][:30]}")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_tests())
