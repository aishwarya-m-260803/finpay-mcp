"""
Optimization & Tool-Usage Evaluation Suite for FinPay AI Agent.

Tests:
1. "Hi" (Greeting - should make 0 tool calls)
2. "What is Arjun Sharma's balance?" (Single-turn DB query - expect search_customers + get_account)
3. "What are his recent transactions?" (Multi-turn with history from #2 - expect get_customer_transactions directly)
4. "Give me Arjun Sharma's balance and recent transactions." (Combined multi-tool query)
"""

import asyncio
import os
import sys
from typing import List, Dict, Any

_current_dir = os.path.dirname(os.path.abspath(__file__))
_workspace_root = os.path.dirname(_current_dir)
if _workspace_root not in sys.path:
    sys.path.insert(0, _workspace_root)

from agent import FinPayAgent


async def main():
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("==================================================")
    print("   FinPay AI Agent — Optimization Test Suite      ")
    print("==================================================")

    agent = FinPayAgent()
    results: List[Dict[str, Any]] = []

    # ── Test 1: "Hi" ─────────────────────────────────────────
    print("\n" + "=" * 50)
    print("TEST 1: Greeting ('Hi')")
    print("=" * 50)
    prompt1 = "Hi"
    ans1 = await agent.run_with_mcp(prompt1)
    print(f"Answer:\n{ans1}\n")

    # ── Test 2: "What is Arjun Sharma's balance?" ────────────
    print("\n" + "=" * 50)
    print("TEST 2: Balance Query ('What is Arjun Sharma's balance?')")
    print("=" * 50)
    prompt2 = "What is Arjun Sharma's balance?"
    ans2 = await agent.run_with_mcp(prompt2)
    print(f"Answer:\n{ans2}\n")

    history = [
        {"role": "user", "content": prompt2},
        {"role": "assistant", "content": ans2},
    ]

    # ── Test 3: Follow-up with history ────────────────────────
    print("\n" + "=" * 50)
    print("TEST 3: Follow-up with History ('What are his recent transactions?')")
    print("=" * 50)
    prompt3 = "What are his recent transactions?"
    ans3 = await agent.run_with_mcp(prompt3, history=history)
    print(f"Answer:\n{ans3}\n")

    # ── Test 4: Combined Query ────────────────────────────────
    print("\n" + "=" * 50)
    print("TEST 4: Combined Query ('Give me Arjun Sharma's balance and recent transactions.')")
    print("=" * 50)
    prompt4 = "Give me Arjun Sharma's balance and recent transactions."
    ans4 = await agent.run_with_mcp(prompt4)
    print(f"Answer:\n{ans4}\n")

    print("\n==================================================")
    print("   Test Suite Complete                             ")
    print("==================================================")


if __name__ == "__main__":
    asyncio.run(main())
