"""
FinPay AI Agent
───────────────
Implements the Qwen tool-calling loop over Ollama /api/chat:

    User request
      → Qwen (via Ollama) + available tools
        → Qwen requests tool call
          → MCP execution via client/mcp_client.py
            → tool result fed back to Qwen
              → repeat if another tool is needed
                → final text answer returned to caller

The loop never executes a tool unless Qwen explicitly requests it.
"""

import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional

# ── sys.path: allow `from client.mcp_client import ...` ──────
_current_dir = os.path.dirname(os.path.abspath(__file__))
_workspace_root = os.path.dirname(_current_dir)
if _workspace_root not in sys.path:
    sys.path.insert(0, _workspace_root)

from qwen_client import QwenClient
from client.mcp_client import MCPClientManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are FinPay AI, a smart financial assistant backed by a PostgreSQL database.\n"
    "You have access to MCP tools for searching customers, searching merchants, viewing accounts, "
    "listing transactions, inspecting merchant transactions, and computing spending summaries.\n"
    "Guidelines:\n"
    "1. For greetings, casual questions, or non-database requests, respond directly without calling any tools.\n"
    "2. For queries requiring database information, use the provided MCP tools.\n"
    "3. Check previous conversation history and past tool outputs before calling tools. Do not make duplicate or redundant calls for customer IDs, account details, or transactions already present in context.\n"
    "4. To find transactions for a merchant by name, first call search_merchants(query) to find the merchant_id, then call get_merchant_transactions(merchant_id).\n"
    "5. If a query requests both account balance and transactions, fetch both account details (for balance) and transaction history.\n"
    "6. Maintain conversation context across turns and resolve references (such as 'he', 'his', 'this customer', 'that account').\n"
    "7. Currency Handling: Preserve the exact database currency (INR / ₹) for all financial amounts, balances, and summaries. Display amounts using ₹ or INR. Never convert or assume $ or USD for FinPay data.\n"
    "8. Answer concisely, accurately, and professionally based on tool results."
)




# ── helpers ──────────────────────────────────────────────────


def _prepare_history(
    history: Optional[List[Dict[str, Any]]],
    max_messages: int = 10,
) -> List[Dict[str, Any]]:
    """Sanitize and limit conversation history to recent user/assistant messages."""
    if not history:
        return []

    clean: List[Dict[str, Any]] = []
    for msg in history:
        if not isinstance(msg, dict):
            continue
        role = msg.get("role")
        content = msg.get("content")
        if role in ("user", "assistant") and content:
            # Do not allow consecutive messages of the same role
            if clean and clean[-1]["role"] == role:
                continue
            clean.append({"role": role, "content": str(content)})

    # Limit to max_messages
    if len(clean) > max_messages:
        clean = clean[-max_messages:]

    # History prior to current turn's user prompt should start with 'user' and end with 'assistant'
    while clean and clean[0]["role"] == "assistant":
        clean.pop(0)

    while clean and clean[-1]["role"] == "user":
        clean.pop()

    return clean



def _mcp_tools_to_ollama_tools(mcp_tools: list) -> List[Dict[str, Any]]:
    """Convert MCP tool schemas into Ollama tool definitions.

    Ollama expects:
        {
            "type": "function",
            "function": {
                "name": "...",
                "description": "...",
                "parameters": { JSON Schema }
            }
        }
    """
    tools = []
    for t in mcp_tools:
        schema = getattr(t, "inputSchema", {})
        if hasattr(schema, "model_dump"):
            schema = schema.model_dump()
        elif hasattr(schema, "dict"):
            schema = schema.dict()
        elif not isinstance(schema, dict):
            schema = dict(schema)

        tools.append({
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description or "",
                "parameters": schema,
            },
        })
    return tools


def _parse_tool_arguments(raw_args: Any) -> Dict[str, Any]:
    """Safely parse tool call arguments from the LLM response."""
    if isinstance(raw_args, dict):
        return raw_args
    if isinstance(raw_args, str):
        try:
            return json.loads(raw_args)
        except (json.JSONDecodeError, TypeError):
            return {"_raw": raw_args}
    return {}


def _serialize_tool_result(result: Any) -> str:
    """Convert a tool execution result to a JSON string for the message history."""
    if isinstance(result, str):
        return result
    return json.dumps(result, default=str)


def _extract_tool_calls(message: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract tool_calls array from an Ollama assistant message.

    Ollama returns tool calls as:
        "message": {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "function": {
                        "name": "search_customers",
                        "arguments": {"query": "Chennai"}
                    }
                }
            ]
        }
    """
    return message.get("tool_calls") or []


def _has_tool_calls(message: Dict[str, Any]) -> bool:
    """Check whether the Ollama response message contains tool call requests."""
    return len(_extract_tool_calls(message)) > 0


# ── Agent ────────────────────────────────────────────────────


class FinPayAgent:
    """Manages the Qwen (Ollama) ↔ MCP tool-calling loop.

    The agent:
    1. Connects to the MCP server and discovers tools dynamically.
    2. Translates MCP tool schemas into Ollama tool definitions.
    3. Sends user prompt + conversation history + tools to Qwen via Ollama /api/chat.
    4. If Qwen requests tool calls → executes them via MCP → feeds results back.
    5. Repeats until Qwen produces a final text answer (or iteration limit hit).
    6. Returns only the final answer string.
    """

    def __init__(self, client: Optional[QwenClient] = None):
        self.client = client or QwenClient()

    # ── public entry point ───────────────────────────────────

    async def run_with_mcp(
        self,
        user_prompt: str,
        history: Optional[List[Dict[str, Any]]] = None,
        mcp_client: Optional[MCPClientManager] = None,
        system_instruction: Optional[str] = None,
        max_iterations: int = 10,
        max_history_messages: int = 10,
    ) -> str:
        """Execute the full tool-calling loop and return the final answer.

        Args:
            user_prompt: Natural language query from the user.
            history: Optional list of previous conversation messages
                     [{"role": "user"|"assistant", "content": "..."}].
            mcp_client: Optional pre-connected MCPClientManager.
                        If None or not connected, a new connection is opened.
            system_instruction: Override the default system prompt.
            max_iterations: Safety cap on tool-calling rounds.
            max_history_messages: Maximum recent context messages to keep.

        Returns:
            The final text answer from Qwen (string only, no history).
        """
        if mcp_client is None:
            mcp_client = MCPClientManager()

        # If the client isn't connected yet, open a session for the duration
        if not mcp_client.session:
            async with mcp_client.connect() as connected:
                return await self._tool_loop(
                    user_prompt,
                    connected,
                    system_instruction,
                    max_iterations,
                    history,
                    max_history_messages,
                )
        return await self._tool_loop(
            user_prompt,
            mcp_client,
            system_instruction,
            max_iterations,
            history,
            max_history_messages,
        )

    # ── core tool-calling loop ───────────────────────────────

    async def _tool_loop(
        self,
        user_prompt: str,
        mcp_client: MCPClientManager,
        system_instruction: Optional[str],
        max_iterations: int,
        history: Optional[List[Dict[str, Any]]] = None,
        max_history_messages: int = 10,
    ) -> str:
        """The actual Qwen (Ollama) ↔ MCP loop.

        Flow per iteration:
            1. Send messages (including history & tool results) to Qwen via Ollama.
            2. If Qwen's response has NO tool_calls → return its text (done).
            3. If Qwen's response HAS tool_calls → execute each via MCP,
               append results, and loop back to step 1.
        """
        # ── Step 1: Discover MCP tools and translate schemas ─
        mcp_tools = await mcp_client.list_tools()
        ollama_tools = _mcp_tools_to_ollama_tools(mcp_tools)
        logger.info(
            f"[Agent] Config: num_ctx={self.client.num_ctx}, "
            f"num_predict={self.client.num_predict}, "
            f"temperature={self.client.temperature}"
        )
        logger.info(
            f"[Agent] Discovered {len(mcp_tools)} MCP tools: "
            f"{[t.name for t in mcp_tools]}"
        )

        # ── Step 2: Build initial conversation with history ──
        clean_history = _prepare_history(history, max_messages=max_history_messages)
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_instruction or SYSTEM_PROMPT},
        ]
        messages.extend(clean_history)
        messages.append({"role": "user", "content": user_prompt})

        logger.info(
            f"[Agent] Starting turn with {len(clean_history)} history messages "
            f"and prompt: '{user_prompt}'"
        )

        total_tool_calls = 0

        # ── Step 3: Loop until final answer or limit ─────────
        for iteration in range(1, max_iterations + 1):
            logger.info(f"[Agent] Iteration {iteration}/{max_iterations}")

            # Call Qwen via Ollama with the full conversation + tool definitions
            response = await self.client.chat_completion_async(
                messages=messages,
                tools=ollama_tools if ollama_tools else None,
            )

            assistant_message = response.get("message", {})
            content = assistant_message.get("content", "") or ""

            msg_for_history: Dict[str, Any] = {
                "role": "assistant",
                "content": content,
            }
            tool_calls = _extract_tool_calls(assistant_message)
            if tool_calls:
                msg_for_history["tool_calls"] = tool_calls
            messages.append(msg_for_history)

            # ── No tool calls → Qwen produced a final answer ─
            if not tool_calls:
                final_answer = content.strip()
                logger.info(
                    f"[Agent] Final answer received at iteration {iteration}. "
                    f"Total tool calls in turn: {total_tool_calls}"
                )
                return final_answer

            # ── Tool calls requested → execute each via MCP ──
            total_tool_calls += len(tool_calls)
            for tool_call in tool_calls:
                func_info = tool_call.get("function", {})
                func_name = func_info.get("name", "")
                func_args = _parse_tool_arguments(func_info.get("arguments", {}))

                logger.info(f"[Agent] Qwen requested tool: {func_name}({func_args})")

                try:
                    result = await mcp_client.call_tool(func_name, func_args)
                except Exception as e:
                    logger.error(f"[Agent] MCP tool '{func_name}' failed: {e}")
                    result = {"error": f"Tool execution failed: {str(e)}"}

                logger.info(f"[Agent] MCP tool '{func_name}' result: {result}")

                messages.append({
                    "role": "tool",
                    "content": _serialize_tool_result(result),
                })


            # Loop continues → Qwen will see the tool results on next iteration

        # ── Safety limit reached ─────────────────────────────
        logger.warning(f"[Agent] Max iterations ({max_iterations}) reached")
        return (
            "I was unable to complete the analysis within the allowed number of steps. "
            "Please try a more specific question."
        )


# ── CLI entry point ──────────────────────────────────────────

if __name__ == "__main__":
    import asyncio

    async def main():
        if hasattr(sys.stdout, "reconfigure"):
            try:
                sys.stdout.reconfigure(encoding="utf-8")
            except Exception:
                pass

        prompt = sys.argv[1] if len(sys.argv) > 1 else None
        if not prompt:
            print('Usage: python agent.py "<your question>"')
            print('Example: python agent.py "Find all customers from Chennai"')
            sys.exit(1)

        print("==================================================")
        print("  FinPay AI Agent  (Qwen 3.5 via Ollama + MCP)    ")
        print("==================================================")
        print(f"\nQuery: {prompt}\n")

        agent = FinPayAgent()
        try:
            answer = await agent.run_with_mcp(prompt)
            print("-" * 50)
            print(f"\nAnswer:\n{answer}")
        except Exception as e:
            print(f"\nError: {e}")

    asyncio.run(main())

