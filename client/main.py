"""
FinPay MCP Client Application
─────────────────────────────
CLI client for FinPay MCP Server.
Allows querying financial data via natural language using LLM tool calling.

Usage:
    python client/main.py "Find transactions for customer Priya"
    python client/main.py  (Starts interactive session)
"""

import asyncio
import os
import sys

from dotenv import load_dotenv

# Add project root directory to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Load .env from client directory or root
load_dotenv(os.path.join(PROJECT_ROOT, "client", ".env"))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from client.llm_runner import LLMRunner
from client.mcp_client import MCPClientManager


def log_status(msg: str) -> None:
    print(f"\033[36m{msg}\033[0m")


async def run_single_query(query: str) -> None:
    """Connect to MCP server, execute prompt via LLM, and print result."""
    print(f"\n\033[1;33mUser Query:\033[0m {query}")

    try:
        runner = LLMRunner(logger=log_status)
    except Exception as e:
        print(f"\033[31mInitialization Error:\033[0m {e}")
        return

    mcp_client = MCPClientManager()
    print("\033[32m[Connecting to FinPay MCP Server via stdio...]\033[0m")

    async with mcp_client.connect():
        answer = await runner.run(query, mcp_client)
        print(f"\n\033[1;32mFinPay AI Response:\033[0m\n{answer}\n")


async def run_interactive_mode() -> None:
    """Start interactive terminal session for asking multiple questions."""
    try:
        runner = LLMRunner(logger=log_status)
    except Exception as e:
        print(f"\033[31mInitialization Error:\033[0m {e}")
        return

    mcp_client = MCPClientManager()
    print("\033[32m[Connecting to FinPay MCP Server via stdio...]\033[0m")

    async with mcp_client.connect():
        print("\n\033[1;35mFinPay AI Terminal Connected.\033[0m Type 'exit' or 'quit' to end.\n")

        while True:
            try:
                user_input = input("\033[1;33mAsk FinPay > \033[0m").strip()
                if not user_input:
                    continue
                if user_input.lower() in ("exit", "quit"):
                    print("Goodbye!")
                    break

                answer = await runner.run(user_input, mcp_client)
                print(f"\n\033[1;32mResponse:\033[0m\n{answer}\n")
            except (KeyboardInterrupt, EOFError):
                print("\nExiting interactive mode...")
                break
            except Exception as e:
                print(f"\033[31mError during execution:\033[0m {e}")


def main() -> None:
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        asyncio.run(run_single_query(query))
    else:
        asyncio.run(run_interactive_mode())


if __name__ == "__main__":
    main()
