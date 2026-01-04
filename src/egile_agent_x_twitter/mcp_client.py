"""MCP client for the X Post Creator server."""

from __future__ import annotations

import logging
from typing import Any, Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client

logger = logging.getLogger(__name__)


class MCPClient:
    """MCP SSE client to call tools on the MCP server."""

    def __init__(
        self,
        transport: str = "sse",
        host: str = "localhost",
        port: int = 8002,
        timeout: float = 30.0,
    ) -> None:
        self.transport = transport
        self.host = host
        self.port = port
        self.timeout = timeout
        # FastMCP SSE endpoint is at /sse
        self.base_url = f"http://{host}:{port}/sse"
        self._session: Optional[ClientSession] = None
        self._exit_stack: Optional[AsyncExitStack] = None

    async def __aenter__(self) -> "MCPClient":
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()

    async def connect(self) -> None:
        """Establish connection to the MCP server via SSE."""
        if self._session is not None:
            return
        if self.transport != "sse":
            raise ValueError(f"Unsupported transport: {self.transport}")
        
        logger.info("Connecting to MCP server at %s via SSE", self.base_url)
        
        self._exit_stack = AsyncExitStack()
        
        # Connect using SSE transport
        sse_transport = await self._exit_stack.enter_async_context(
            sse_client(self.base_url)
        )
        
        # Create session
        self._session = await self._exit_stack.enter_async_context(
            ClientSession(sse_transport[0], sse_transport[1])
        )
        
        # Initialize the session
        await self._session.initialize()
        logger.info("MCP client connected and initialized")

    async def close(self) -> None:
        """Close the MCP client connection."""
        if self._exit_stack is not None:
            await self._exit_stack.aclose()
            self._exit_stack = None
            self._session = None
            logger.info("MCP client connection closed")

    async def call_tool(self, tool_name: str, arguments: Optional[dict[str, Any]] = None) -> str:
        """Call a tool on the MCP server."""
        if self._session is None:
            await self.connect()
        if self._session is None:
            raise RuntimeError("Failed to initialize MCP session")

        arguments = arguments or {}
        logger.info("Calling MCP tool '%s' with args: %s", tool_name, arguments)

        result = await self._session.call_tool(tool_name, arguments=arguments)
        
        # Extract text content from the result
        if result.content:
            text_parts = [item.text for item in result.content if hasattr(item, 'text')]
            return '\n'.join(text_parts) if text_parts else str(result.content)
        return ""

    async def create_post(
        self,
        text: str,
        style: str = "professional",
        include_hashtags: bool = True,
        max_length: int = 280,
    ) -> str:
        return await self.call_tool(
            "create_post",
            {
                "text": text,
                "style": style,
                "include_hashtags": include_hashtags,
                "max_length": max_length,
            },
        )

    async def publish_post(self, post_text: str, confirm: bool = False) -> str:
        return await self.call_tool(
            "publish_post",
            {
                "post_text": post_text,
                "confirm": confirm,
            },
        )
