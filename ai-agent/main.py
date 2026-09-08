"""
FinPay AI Agent — CLI Runner
─────────────────────────────
Quick terminal interface: connects Qwen agent to MCP server and runs a query.

Usage:
    python main.py "Find all customers from Chennai"
    python main.py                                    # interactive mode
"""

import asyncio
import os
import sys

# Ensure workspace root is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
workspace_root = os.path.dirname(current_dir)
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

from agent import FinPayAgent


async def single_query(prompt: str) -> None:
    """Run a single query through the agent."""
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    agent = FinPayAgent()
    answer = await agent.run_with_mcp(prompt)
    print("\n" + "-" * 50)
    print(f"Answer:\n\n{answer}")


async def interactive() -> None:
    """Run an interactive REPL loop with conversation context."""
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("Type 'exit' or 'quit' to end.\n")
    agent = FinPayAgent()
    history = []

    while True:
        try:
            prompt = input("Ask FinPay > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not prompt or prompt.lower() in ("exit", "quit"):
            print("Goodbye!")
            break

        try:
            answer = await agent.run_with_mcp(prompt, history=history)
            print(f"\n{answer}\n")
            history.append({"role": "user", "content": prompt})
            history.append({"role": "assistant", "content": answer})
        except Exception as e:
            print(f"\nError: {e}\n")



async def main() -> None:
    print("╔══════════════════════════════════════════╗")
    print("║  FinPay AI Agent  (Qwen + MCP)           ║")
    print("╚══════════════════════════════════════════╝\n")

    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
        print(f"📝 Query: {prompt}")
        await single_query(prompt)
    else:
        await interactive()


if __name__ == "__main__":
    asyncio.run(main())
