"""
FinPay MCP Client
─────────────────
Stdio transport client wrapper for connecting to the FinPay MCP server,
discovering available tools dynamically, and executing tool calls.
"""

import json
import os
import sys
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


class MCPClientManager:
    """Manages an active stdio connection to the FinPay MCP server."""

    def __init__(self, server_script_path: str | None = None):
        if server_script_path is None:
            # Default to mcp-server/server.py relative to workspace root
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            server_script_path = os.path.join(root_dir, "mcp-server", "server.py")

        self.server_script_path = server_script_path
        self.session: ClientSession | None = None
        self._read_stream = None
        self._write_stream = None

    @asynccontextmanager
    async def connect(self) -> AsyncGenerator["MCPClientManager", None]:
        """Establish stdio connection and initialize MCP session."""
        server_params = StdioServerParameters(
            command=sys.executable,
            args=[self.server_script_path],
            env=dict(os.environ),
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                self.session = session
                yield self
                self.session = None

    async def list_tools(self) -> list[Any]:
        """Dynamically list all tools registered on the MCP server."""
        if not self.session:
            raise RuntimeError("MCP client is not connected")
        try:
            response = await self.session.list_tools()
            return response.tools
        except Exception as e:
            raise RuntimeError(f"MCP list_tools failed: {e}") from e

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """Call an MCP tool by name with arguments and return the result.

        Defensively wraps the session call so that database errors,
        parameter mismatches, or MCP protocol errors are caught here
        instead of escaping into the stdio_client TaskGroup (which would
        wrap them in an opaque ExceptionGroup).
        """
        if not self.session:
            raise RuntimeError("MCP client is not connected")

        try:
            result = await self.session.call_tool(tool_name, arguments)
        except Exception as e:
            raise RuntimeError(
                f"MCP tool '{tool_name}' execution failed: {e}"
            ) from e

        # Extract text content items from result
        texts = []
        if hasattr(result, "content"):
            for content_item in result.content:
                if getattr(content_item, "type", None) == "text":
                    texts.append(content_item.text)
                elif hasattr(content_item, "text"):
                    texts.append(content_item.text)

        raw_output = "\n".join(texts) if texts else str(result)

        # Attempt to parse output as JSON if possible
        try:
            return json.loads(raw_output)
        except (json.JSONDecodeError, TypeError):
            return raw_output

