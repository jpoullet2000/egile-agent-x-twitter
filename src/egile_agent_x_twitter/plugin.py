"""XTwitter plugin for Egile Agent Core."""

from __future__ import annotations

import logging
import re
from typing import Any, Optional

from egile_agent_core.plugins import Plugin

from .mcp_client import MCPClient

logger = logging.getLogger(__name__)


class XTwitterPlugin(Plugin):
    """Plugin that creates and publishes X/Twitter posts via MCP."""

    def __init__(
        self,
        mcp_host: str = "localhost",
        mcp_port: int = 8002,
        mcp_transport: str = "sse",
        timeout: float = 30.0,
    ) -> None:
        self.mcp_host = mcp_host
        self.mcp_port = mcp_port
        self.mcp_transport = mcp_transport
        self.timeout = timeout
        self._client: Optional[MCPClient] = None
        self._agent = None
        self._last_draft_text: Optional[str] = None
        self._client_initialized = False

    @property
    def name(self) -> str:
        return "xtwitter"

    @property
    def description(self) -> str:
        return (
            "Creates engaging X/Twitter posts and can publish them via MCP. "
            "Always preview posts before publishing and require explicit confirmation."
        )

    @property
    def version(self) -> str:
        return "0.1.0"

    async def on_agent_start(self, agent) -> None:
        """Initialize MCP client when agent starts."""
        self._agent = agent
        self._client = MCPClient(
            transport=self.mcp_transport,
            host=self.mcp_host,
            port=self.mcp_port,
            timeout=self.timeout,
        )
        await self._client.connect()

    async def cleanup(self) -> None:
        """Close MCP client."""
        if self._client:
            await self._client.close()
            self._client = None

    async def _ensure_client(self) -> None:
        """Ensure MCP client is initialized."""
        if not self._client and not self._client_initialized:
            self._client_initialized = True
            self._client = MCPClient(
                transport=self.mcp_transport,
                host=self.mcp_host,
                port=self.mcp_port,
                timeout=self.timeout,
            )
            await self._client.connect()
            logger.info(f"✅ MCP client initialized and connected")
    
    async def create_post(
        self,
        text: str = "",
        post_text: str = "",
        style: str = "professional",
        include_hashtags: bool = True,
        max_length: int = 280,
    ) -> str:
        await self._ensure_client()
        if not self._client:
            raise RuntimeError("MCP client not initialized")
        effective_text = text or post_text
        if not effective_text:
            return "No text provided. Pass either 'text' or 'post_text' with the content to draft."

        result = await self._client.create_post(
            text=effective_text,
            style=style,
            include_hashtags=include_hashtags,
            max_length=max_length,
        )

        # Try to cache the post text for later publish calls
        cached = self._extract_post_text(str(result))
        if cached:
            self._last_draft_text = cached

        return result

    async def publish_post(self, post_text: str, confirm: bool = False) -> str:
        logger.info(f"🚀 publish_post called! post_text length: {len(post_text) if post_text else 0}, confirm: {confirm}")
        if not self._client:
            raise RuntimeError("MCP client not initialized")
        if not post_text:
            if self._last_draft_text:
                post_text = self._last_draft_text
            else:
                return (
                    "No post_text provided and no cached draft found. Please pass the exact post text to publish (e.g., the latest draft you just created). "
                    "The MCP server is stateless, so include the full post_text in this call."
                )
        result = await self._client.publish_post(post_text=post_text, confirm=confirm)
        logger.info(f"📝 publish_post result: {result[:200] if result else 'None'}")
        return result

    async def get_last_draft(self) -> str:
        """Return the most recent cached draft text, if any."""
        return self._last_draft_text or ""

    @staticmethod
    def _extract_post_text(output: str) -> Optional[str]:
        """Extract the post text block from the create_post output."""
        match = re.search(r"POST TEXT:\s*\n[-]+\n(.+?)\n[-]+\n", output, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None

    def get_tools(self) -> list[dict[str, Any]]:
        """Describe tools for LLM function-calling interfaces."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "create_post",
                    "description": "Create an attractive X/Twitter post from input text.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "Input text to transform into a post",
                            },
                            "post_text": {
                                "type": "string",
                                "description": "Alias for text; the content to transform into a post",
                            },
                            "style": {
                                "type": "string",
                                "enum": [
                                    "professional",
                                    "casual",
                                    "witty",
                                    "inspirational",
                                ],
                                "description": "Writing style",
                                "default": "professional",
                            },
                            "include_hashtags": {
                                "type": "boolean",
                                "description": "Include relevant hashtags",
                                "default": True,
                            },
                            "max_length": {
                                "type": "integer",
                                "description": "Max characters (default 280)",
                                "default": 280,
                            },
                        },
                        "required": [],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "publish_post",
                    "description": "Publish a post to X/Twitter. Defaults to the latest cached draft if post_text is omitted. Always set confirm=True to actually publish.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "post_text": {
                                "type": "string",
                                "description": "The full post text to publish (optional if a draft was just created)",
                            },
                            "confirm": {
                                "type": "boolean",
                                "description": "Must be true to publish (safety)",
                                "default": False,
                            },
                        },
                        "required": [],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_last_draft",
                    "description": "Return the most recent created draft text (empty string if none).",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            },
        ]

    def get_tool_functions(self) -> dict[str, Any]:
        return {
            "create_post": self.create_post,
            "publish_post": self.publish_post,
            "get_last_draft": self.get_last_draft,
        }
