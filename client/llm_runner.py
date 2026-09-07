"""
FinPay LLM Runner
─────────────────
Discovers MCP tool schemas dynamically, converts them to OpenAI tool specifications,
and manages the agentic function calling loop for user queries.
"""

import json
import os
from typing import Any, Callable

from dotenv import load_dotenv

from client.mcp_client import MCPClientManager

load_dotenv()


# ── Structured MCP Error Classes ─────────────────────────────

class MCPQuotaError(Exception):
    """Category 1: API Quota or Key Exhaustion (429, rate limit, auth failure)."""
    pass


class MCPBoundaryError(Exception):
    """Category 2: MCP Boundary & Rule Violations (cross-tenant, restricted actions)."""
    pass


class MCPParameterError(Exception):
    """Category 3: Parameter Mismatch / Missing Filter."""
    pass


class MCPToolError(Exception):
    """Category 4: Unhandled Tool Exception."""
    pass


SYSTEM_INSTRUCTION = (
    "You are FinPay AI Assistant, a helpful financial intelligence agent backed by PostgreSQL. "
    "Use the provided MCP tools to search customers, view accounts, list transactions, "
    "and calculate summaries to answer the user's questions accurately and concisely."
)


class LLMRunner:
    """Manages LLM interaction via OpenAI API and dynamic tool execution loop."""

    def __init__(self, logger: Callable[[str], None] | None = None):
        self.logger = logger or (lambda msg: None)

        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")

        if self.openai_key:
            self.provider = "openai"
            self.model_name = os.getenv("OPENAI_MODEL") or os.getenv("MODEL_NAME") or "gpt-4o"
        elif self.gemini_key:
            self.provider = "gemini"
            self.model_name = os.getenv("GEMINI_MODEL") or os.getenv("MODEL_NAME") or "gemini-3.6-flash"
        elif self.anthropic_key:
            self.provider = "anthropic"
            self.model_name = os.getenv("ANTHROPIC_MODEL") or os.getenv("MODEL_NAME") or "claude-3-5-sonnet-20241022"
        else:
            raise ValueError(
                "No API key found in client/.env! Please set OPENAI_API_KEY, "
                "GEMINI_API_KEY, or ANTHROPIC_API_KEY in your client/.env file."
            )

        self.logger(f"[LLM] Active Provider: {self.provider.upper()} (Model: {self.model_name})")

    async def run(self, user_query: str, mcp_client: MCPClientManager) -> str:
        """Execute user query using dynamic MCP tools in an LLM agent loop."""
        try:
            mcp_tools = await mcp_client.list_tools()
        except Exception as e:
            raise MCPToolError(f"MCP server connection failed: {str(e)}") from e

        self.logger(f"[MCP] Discovered {len(mcp_tools)} tools: {[t.name for t in mcp_tools]}")

        if self.provider == "openai":
            return await self._run_openai(user_query, mcp_tools, mcp_client)
        elif self.provider == "gemini":
            return await self._run_gemini(user_query, mcp_tools, mcp_client)
        elif self.provider == "anthropic":
            return await self._run_anthropic(user_query, mcp_tools, mcp_client)
        else:
            raise MCPToolError(f"Provider {self.provider} not supported")

    async def _run_openai(
        self, user_query: str, mcp_tools: list[Any], mcp_client: MCPClientManager
    ) -> str:
        from openai import OpenAI

        client = OpenAI(api_key=self.openai_key)

        # Convert raw MCP tool schemas dynamically to OpenAI function tool definitions
        tools = [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description or "",
                    "parameters": t.inputSchema,
                },
            }
            for t in mcp_tools
        ]

        messages = [
            {"role": "system", "content": SYSTEM_INSTRUCTION},
            {"role": "user", "content": user_query},
        ]

        while True:
            try:
                response = client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    tools=tools,
                    temperature=0.1,
                )
            except Exception as e:
                err_msg = str(e)
                if any(k in err_msg.lower() for k in ["429", "rate_limit", "rate limit", "quota", "insufficient_quota"]):
                    raise MCPQuotaError(f"RESOURCE_EXHAUSTED: {err_msg}") from e
                if any(k in err_msg.lower() for k in ["authentication", "invalid key", "api_key", "forbidden", "permission denied"]):
                    raise MCPQuotaError(f"AUTH_FAILURE: {err_msg}") from e
                raise MCPToolError(err_msg) from e

            choice = response.choices[0]
            msg = choice.message
            messages.append(msg)

            # Check if LLM decided to answer directly without calling tools
            if not msg.tool_calls:
                return msg.content or "No answer provided."

            # Execute tool calls requested by LLM
            for tool_call in msg.tool_calls:
                fn_name = tool_call.function.name
                fn_args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}

                self.logger(f"[MCP Tool Exec] Executing {fn_name}({fn_args})...")
                try:
                    result = await mcp_client.call_tool(fn_name, fn_args)
                except Exception as e:
                    raise MCPToolError(f"MCP tool '{fn_name}' failed: {str(e)}") from e
                self.logger(f"[MCP Tool Result] Received output from {fn_name}")

                result_str = json.dumps(result) if not isinstance(result, str) else result
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result_str,
                    }
                )

    async def _run_gemini(
        self, user_query: str, mcp_tools: list[Any], mcp_client: MCPClientManager
    ) -> str:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=self.gemini_key)

        func_decls = [
            types.FunctionDeclaration(
                name=t.name,
                description=t.description or "",
                parameters=t.inputSchema,
            )
            for t in mcp_tools
        ]

        tools = [types.Tool(function_declarations=func_decls)]
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            tools=tools,
            temperature=0.1,
        )

        contents = [user_query]

        # Model fallback cascade if rate limited / quota exhausted / model deprecated
        candidate_models = []
        for m in [self.model_name, "gemini-2.0-flash", "gemini-1.5-flash", "gemini-2.0-flash-lite"]:
            if m and m not in candidate_models:
                candidate_models.append(m)

        def _call_generate_with_fallback(current_contents):
            last_exc = None
            for model in candidate_models:
                try:
                    return client.models.generate_content(
                        model=model,
                        contents=current_contents,
                        config=config,
                    )
                except Exception as e:
                    err_msg = str(e)
                    # Skip to next model on rate limits, quota exhaustion, or deprecated/retired models
                    if any(k in err_msg for k in [
                        "429", "RESOURCE_EXHAUSTED", "Quota", "quota", "LimitExceeded",
                        "404", "NOT_FOUND", "no longer available", "deprecated",
                    ]):
                        self.logger(f"[Gemini Fallback] Model {model} unavailable ({err_msg[:80]}...). Trying next...")
                        last_exc = e
                        continue
                    # Re-raise non-quota errors with structured types
                    if any(k in err_msg.lower() for k in ["invalid key", "api_key", "authentication", "forbidden", "permission denied"]):
                        raise MCPQuotaError(f"RESOURCE_EXHAUSTED: {err_msg}") from e
                    raise MCPToolError(err_msg) from e
            if last_exc:
                raise MCPQuotaError(
                    f"RESOURCE_EXHAUSTED: All fallback models exhausted. "
                    f"Last error: {str(last_exc)}"
                ) from last_exc

        while True:
            response = _call_generate_with_fallback(contents)

            if not response.function_calls:
                return response.text or "No answer provided."

            if response.candidates and response.candidates[0].content:
                contents.append(response.candidates[0].content)

            for call in response.function_calls:
                tool_name = call.name
                tool_args = dict(call.args) if call.args else {}

                self.logger(f"[MCP Tool Exec] Executing {tool_name}({tool_args})...")
                try:
                    result = await mcp_client.call_tool(tool_name, tool_args)
                except Exception as e:
                    raise MCPToolError(f"MCP tool '{tool_name}' failed: {str(e)}") from e
                self.logger(f"[MCP Tool Result] Received output from {tool_name}")

                contents.append(
                    types.Part.from_function_response(
                        name=tool_name,
                        response={"result": result},
                    )
                )

    async def _run_anthropic(
        self, user_query: str, mcp_tools: list[Any], mcp_client: MCPClientManager
    ) -> str:
        from anthropic import Anthropic

        client = Anthropic(api_key=self.anthropic_key)

        tools = [
            {
                "name": t.name,
                "description": t.description or "",
                "input_schema": t.inputSchema,
            }
            for t in mcp_tools
        ]

        messages = [{"role": "user", "content": user_query}]
        claude_model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")

        while True:
            try:
                response = client.messages.create(
                    model=claude_model,
                    system=SYSTEM_INSTRUCTION,
                    messages=messages,
                    tools=tools,
                    max_tokens=2048,
                )
            except Exception as e:
                err_msg = str(e)
                if any(k in err_msg.lower() for k in ["429", "rate_limit", "rate limit", "quota", "overloaded"]):
                    raise MCPQuotaError(f"RESOURCE_EXHAUSTED: {err_msg}") from e
                if any(k in err_msg.lower() for k in ["authentication", "invalid key", "api_key", "forbidden", "permission denied"]):
                    raise MCPQuotaError(f"AUTH_FAILURE: {err_msg}") from e
                raise MCPToolError(err_msg) from e

            messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason != "tool_use":
                text_blocks = [b.text for b in response.content if hasattr(b, "text")]
                return "\n".join(text_blocks) or "No answer provided."

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    tool_name = block.name
                    tool_args = block.input or {}

                    self.logger(f"[MCP Tool Exec] Executing {tool_name}({tool_args})...")
                    try:
                        result = await mcp_client.call_tool(tool_name, tool_args)
                    except Exception as e:
                        raise MCPToolError(f"MCP tool '{tool_name}' failed: {str(e)}") from e
                    self.logger(f"[MCP Tool Result] Received output from {tool_name}")

                    result_str = json.dumps(result) if not isinstance(result, str) else result
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result_str,
                        }
                    )

            messages.append({"role": "user", "content": tool_results})
