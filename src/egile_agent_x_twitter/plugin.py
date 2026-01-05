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
        mcp_transport: str = "stdio",
        mcp_command: Optional[str] = None,
        timeout: float = 30.0,
        use_mcp: bool = True,
    ) -> None:
        self.mcp_host = mcp_host
        self.mcp_port = mcp_port
        self.mcp_transport = mcp_transport
        self.mcp_command = mcp_command or "python -m egile_mcp_x_post_creator.server"
        self.timeout = timeout
        self.use_mcp = use_mcp
        self._client: Optional[MCPClient] = None
        self._agent = None
        self._last_draft_text: Optional[str] = None

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
        
        if self.use_mcp:
            self._client = MCPClient(
                transport=self.mcp_transport,
                host=self.mcp_host,
                port=self.mcp_port,
                command=self.mcp_command,
                timeout=self.timeout,
            )
            await self._client.connect()
            logger.info(f"XTwitter plugin connected to MCP server via {self.mcp_transport}")
        else:
            logger.info("XTwitter plugin initialized in direct mode (no MCP)")

    async def cleanup(self) -> None:
        """Close MCP client."""
        if self._client:
            await self._client.close()
            self._client = None

    async def create_post(
        self,
        text: str = "",
        post_text: str = "",
        style: str = "professional",
        include_hashtags: bool = True,
        max_length: int = 280,
    ) -> str:
        effective_text = text or post_text
        if not effective_text:
            return "No text provided. Pass either 'text' or 'post_text' with the content to draft."
        
        if self.use_mcp and self._client:
            # Use MCP mode
            result = await self._client.create_post(
                text=effective_text,
                style=style,
                include_hashtags=include_hashtags,
                max_length=max_length,
            )
        else:
            # Direct mode - simple formatting
            result = self._create_post_direct(effective_text, style, include_hashtags, max_length)

        # Try to cache the post text for later publish calls
        cached = self._extract_post_text(str(result))
        if cached:
            self._last_draft_text = cached

        return result
    
    def _create_post_direct(self, text: str, style: str, include_hashtags: bool, max_length: int) -> str:
        """Create a post using simple direct formatting (no LLM)."""
        # Simple formatting based on style
        if style == "casual":
            emoji = "👋 "
        elif style == "witty":
            emoji = "😄 "
        elif style == "inspirational":
            emoji = "✨ "
        else:
            emoji = "📢 "
        
        # Format the post
        post = f"{emoji}{text}"
        
        # Add hashtags if requested
        if include_hashtags:
            # Extract keywords for hashtags (simple approach)
            words = text.split()
            hashtags = [f"#{word.capitalize()}" for word in words if len(word) > 4][:2]
            if hashtags:
                post += f"\n\n{' '.join(hashtags)}"
        
        # Truncate if needed
        if len(post) > max_length:
            post = post[:max_length-3] + "..."
        
        # Return formatted response
        stats = {
            "character_count": len(post),
            "hashtag_count": post.count('#'),
            "emoji_count": len([c for c in post if ord(c) > 127000]),
        }
        
        output = f"✅ Post Created Successfully!\n\n"
        output += f"📝 POST TEXT:\n{'-' * 60}\n"
        output += f"{post}\n"
        output += f"{'-' * 60}\n\n"
        output += f"📊 STATISTICS:\n"
        output += f"  • Characters: {stats['character_count']}/{max_length}\n"
        output += f"  • Hashtags: {stats['hashtag_count']}\n"
        output += f"  • Style: {style}\n\n"
        output += f"💡 TIP: To publish this post, use the publish_post tool with confirm=True\n"
        
        return output

    async def publish_post(self, post_text: str = "", confirm: bool = False) -> str:
        logger.info(f"🚀 publish_post called! post_text length: {len(post_text) if post_text else 0}, confirm: {confirm}")
        
        # Use cached draft if no post_text provided
        effective_post_text = post_text or self._last_draft_text
        if not effective_post_text:
            return (
                "No post_text provided and no cached draft found. Please pass the exact post text to publish "
                "(e.g., the latest draft you just created). The MCP server is stateless, so include the full post_text in this call."
            )
        
        if not confirm:
            return (
                f"⚠️ DRY RUN MODE\n\n"
                f"This post is ready to publish:\n\n{effective_post_text}\n\n"
                f"To actually publish, call this tool again with confirm=True"
            )
        
        if self.use_mcp and self._client:
            # Use MCP mode
            result = await self._client.publish_post(post_text=effective_post_text, confirm=True)
        else:
            # Direct mode - simulate publishing
            result = self._publish_post_direct(effective_post_text)
        
        logger.info(f"📝 publish_post result: {result[:200] if result else 'None'}")
        return result
    
    def _publish_post_direct(self, text: str) -> str:
        """Simulate publishing a post (no actual X API call)."""
        import datetime
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        output = f"🚀 Post Published Successfully!\n\n"
        output += f"📝 PUBLISHED TEXT:\n{'-' * 60}\n"
        output += f"{text}\n"
        output += f"{'-' * 60}\n\n"
        output += f"📊 DETAILS:\n"
        output += f"  • Published At: {timestamp}\n"
        output += f"  • Character Count: {len(text)}\n"
        output += f"  • Status: Success (simulated)\n\n"
        output += f"⚠️ NOTE: This is a simulated publish. To publish to actual X/Twitter,\n"
        output += f"configure the X API credentials in the MCP server and use MCP mode.\n"
        
        return output

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
