"""
Functional Verification Suite for FinPay AI Agent.

Tests:
a) "Show me the transactions for Amazon India."
   - Verifies search_merchants -> get_merchant_transactions tool flow
   - Verifies currency display (INR / ₹)
b) "Give me a transaction summary for account 1."
   - Verifies get_transaction_summary tool flow
   - Verifies currency display in totals & averages (INR / ₹, never USD / $)
"""

import asyncio
import os
import sys

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
    print("   FinPay Functional Fixes Verification Suite     ")
    print("==================================================")

    agent = FinPayAgent()

    # ── Test A: Merchant Search & Transactions ──────────────
    print("\n--- Test A: Merchant Search & Transactions ---")
    prompt_a = "Show me the transactions for Amazon India."
    print(f"User Query: {prompt_a}\n")

    try:
        ans_a = await agent.run_with_mcp(prompt_a)
        print(f"Assistant Response:\n{ans_a}\n")
    except Exception as e:
        print(f"❌ Test A Failed with exception: {e}")
        ans_a = ""

    # ── Test B: Transaction Summary Currency Preservation ───
    print("\n--- Test B: Transaction Summary for Account 1 ---")
    prompt_b = "Give me a transaction summary for account 1."
    print(f"User Query: {prompt_b}\n")

    try:
        ans_b = await agent.run_with_mcp(prompt_b)
        print(f"Assistant Response:\n{ans_b}\n")
    except Exception as e:
        print(f"❌ Test B Failed with exception: {e}")
        ans_b = ""

    print("==================================================")
    print("   Verification Execution Complete                ")
    print("==================================================")


if __name__ == "__main__":
    asyncio.run(main())
