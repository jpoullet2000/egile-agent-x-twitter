"""MCP client for the X Post Creator server."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client

logger = logging.getLogger(__name__)


class MCPClient:
    """MCP client to call tools on the MCP server via stdio or SSE."""

    def __init__(
        self,
        transport: str = "stdio",
        host: str = "localhost",
        port: int = 8002,
        command: Optional[str] = None,
        timeout: float = 30.0,
    ) -> None:
        self.transport = transport
        self.host = host
        self.port = port
        self.command = command
        self.timeout = timeout
        self.base_url = f"http://{host}:{port}/sse"  # For SSE
        self._session: Optional[ClientSession] = None
        self._exit_stack: Optional[AsyncExitStack] = None

    async def __aenter__(self) -> "MCPClient":
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()

    async def connect(self) -> None:
        """Establish connection to the MCP server."""
        if self._session is not None:
            return
        
        self._exit_stack = AsyncExitStack()
        
        if self.transport == "stdio":
            # Use stdio transport - spawn server as subprocess
            if not self.command:
                raise ValueError("command is required for stdio transport")
            
            logger.info("Starting MCP server via stdio: %s", self.command)
            
            # Parse command into list
            import shlex
            command_list = shlex.split(self.command)
            
            server_params = StdioServerParameters(
                command=command_list[0],
                args=command_list[1:],
                env=None
            )
            
            stdio_transport = await self._exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            
            self._session = await self._exit_stack.enter_async_context(
                ClientSession(stdio_transport[0], stdio_transport[1])
            )
            
            await self._session.initialize()
            logger.info("MCP client connected via stdio and initialized")
            
        elif self.transport == "sse":
            # Use SSE transport - connect to existing server
            logger.info("Connecting to MCP server at %s via SSE", self.base_url)
            
            sse_transport = await self._exit_stack.enter_async_context(
                sse_client(self.base_url)
            )
            
            self._session = await self._exit_stack.enter_async_context(
                ClientSession(sse_transport[0], sse_transport[1])
            )
            
            await self._session.initialize()
            logger.info("MCP client connected via SSE and initialized")
        else:
            raise ValueError(f"Unsupported transport: {self.transport}")

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
            logger.info("🔌 No session, connecting...")
            await self.connect()
        if self._session is None:
            raise RuntimeError("Failed to initialize MCP session")

        arguments = arguments or {}
        logger.info("Calling MCP tool '%s' with args: %s", tool_name, arguments)

        try:
            logger.info("⏳ Sending tool call to MCP server...")
            # Add timeout to prevent hanging
            result = await asyncio.wait_for(
                self._session.call_tool(tool_name, arguments=arguments),
                timeout=self.timeout
            )
            logger.info("✅ Received response from MCP server")
            
            # Extract text content from the result
            if result.content:
                text_parts = [item.text for item in result.content if hasattr(item, 'text')]
                return '\n'.join(text_parts) if text_parts else str(result.content)
            return ""
        except asyncio.TimeoutError:
            error_msg = f"MCP tool '{tool_name}' timed out after {self.timeout}s"
            logger.error(error_msg)
            raise TimeoutError(error_msg)
        except Exception as e:
            error_msg = f"MCP tool '{tool_name}' failed: {e}"
            logger.error(error_msg)
            raise

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
