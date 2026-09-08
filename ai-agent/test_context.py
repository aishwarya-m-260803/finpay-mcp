"""
Multi-turn conversation context test for FinPay AI Agent.

Tests:
Turn 1: "What is Arjun Sharma's current account balance?"
Turn 2: "What are his recent transactions?"  (Contextual follow-up using "his")
"""

import asyncio
import os
import sys

# Ensure workspace root is in sys.path
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
    print("  FinPay AI Agent — Conversation Context Test     ")
    print("==================================================")

    agent = FinPayAgent()
    history = []

    # ── Turn 1: Account Balance Query ────────────────────────
    turn1_prompt = "What is Arjun Sharma's current account balance?"
    print(f"\n--- Turn 1 ---")
    print(f"User: {turn1_prompt}")

    try:
        ans1 = await agent.run_with_mcp(turn1_prompt, history=history)
        print(f"\nAssistant:\n{ans1}\n")

        # Update history with Turn 1
        history.append({"role": "user", "content": turn1_prompt})
        history.append({"role": "assistant", "content": ans1})
    except Exception as e:
        print(f"\n❌ Turn 1 failed: {e}")
        sys.exit(1)

    # ── Turn 2: Contextual Follow-up Query ───────────────────
    turn2_prompt = "What are his recent transactions?"
    print(f"\n--- Turn 2 (Contextual Follow-up) ---")
    print(f"User: {turn2_prompt}")
    print(f"History context passed to agent: {len(history)} messages")

    try:
        ans2 = await agent.run_with_mcp(turn2_prompt, history=history)
        print(f"\nAssistant:\n{ans2}\n")

        # Update history with Turn 2
        history.append({"role": "user", "content": turn2_prompt})
        history.append({"role": "assistant", "content": ans2})
    except Exception as e:
        print(f"\n❌ Turn 2 failed: {e}")
        sys.exit(1)

    print("==================================================")
    print("  Multi-turn Context Test Completed Successfully  ")
    print("==================================================")


if __name__ == "__main__":
    asyncio.run(main())
