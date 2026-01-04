"""Run MCP server + AgentOS for the X/Twitter agent."""

from __future__ import annotations

import asyncio
import logging
import os
import subprocess
import sys
from pathlib import Path

import uvicorn
from dotenv import load_dotenv

from egile_agent_core.models import OpenAI, XAI, Mistral
from egile_agent_core.server import create_agent_os

from .plugin import XTwitterPlugin

log_level = os.getenv("FASTMCP_LOG_LEVEL", os.getenv("LOG_LEVEL", "INFO")).upper()
log_file = os.getenv("LOG_FILE")

logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename=log_file if log_file else None,
)
logger = logging.getLogger(__name__)

load_dotenv()


def create_xtwitter_agent_os():
    """Create AgentOS with XTwitter plugin."""
    plugin = XTwitterPlugin(
        mcp_host=os.getenv("MCP_HOST", "localhost"),
        mcp_port=int(os.getenv("MCP_PORT", "8002")),
    )

    # Model selection priority: Mistral > XAI > OpenAI
    if os.getenv("MISTRAL_API_KEY"):
        model = Mistral(model=os.getenv("MISTRAL_MODEL", "mistral-large-2512"))
    elif os.getenv("XAI_API_KEY"):
        model = XAI(model=os.getenv("XAI_MODEL", "grok-4-1-fast-reasoning"))
    else:
        model = OpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))

    agents_config = [
        {
            "name": "xtwitter",
            "model": model,
            "description": "AI agent that creates and publishes X/Twitter posts.",
            "instructions": [
                "You are a social media manager for X/Twitter.",
                "Use the create_post tool first to draft a post.",
                "Always show the draft to the user before publishing.",
                "Never call publish_post unless the user explicitly confirms.",
                "When publishing, set confirm=True and remind the user it will post to X.",
                "Always pass the explicit post_text into publish_post (do not rely on server state) unless you use the cached draft via get_last_draft.",
                "If the user says 'publish' or approves a draft, retrieve the latest draft text from the current conversation history (chat context) and include that exact text in the publish_post call. Do NOT invent or paraphrase the draft, and do NOT publish if the draft text cannot be recovered.",
                "If you're missing the draft text, first call get_last_draft (the plugin caches the last create_post output). If that is empty, ask the user to paste it again before calling publish_post.",
            ],
            "plugins": [plugin],
            "markdown": True,
        }
    ]

    agent_os = create_agent_os(
        agents_config=agents_config,
        os_id="xtwitter-os",
        description="XTwitter AgentOS - Create and publish X/Twitter posts with AI",
    )
    return agent_os


async def start_mcp_server():
    """Start the MCP server in a subprocess."""
    port = os.getenv("MCP_PORT", "8002")
    host = os.getenv("MCP_HOST", "0.0.0.0")
    logger.info("Starting MCP server on %s:%s...", host, port)
    mcp_module = "egile_mcp_x_post_creator.server"

    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")

    process = subprocess.Popen(
        [sys.executable, "-m", mcp_module, "--transport", "sse", "--host", host, "--port", port],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )

    await asyncio.sleep(2)

    if process.poll() is not None:
        stderr = process.stderr.read() if process.stderr else ""
        logger.error("MCP server failed to start: %s", stderr)
        return None

    logger.info("MCP server started successfully on %s:%s", host, port)
    return process


def start_agent_ui_instructions():
    """Log instructions to start the Agent UI."""
    ui_path = Path(__file__).parent.parent.parent / "agent-ui"
    logger.info("\n" + "=" * 60)
    logger.info("To start the Agent UI, run in a separate terminal:")
    logger.info("=" * 60)
    if ui_path.exists():
        logger.info("cd %s", ui_path)
        logger.info("pnpm dev")
    else:
        logger.info("cd /path/to/agent-ui")
        logger.info("pnpm dev")
    logger.info("\nThen open: http://localhost:3000")
    logger.info(f"Connect to: http://localhost:{os.getenv('AGENTOS_PORT', '8000')}")
    logger.info("=" * 60 + "\n")


def run_all():
    """Run MCP server + AgentOS."""
    logger.info("Starting XTwitter Agent System...")
    mcp_process = None
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        mcp_process = loop.run_until_complete(start_mcp_server())
        if mcp_process is None:
            logger.error("Failed to start MCP server. Exiting.")
            return

        start_agent_ui_instructions()

        agent_os = create_xtwitter_agent_os()
        app = agent_os.get_app()

        logger.info("System Ready")
        logger.info(f"MCP Server:   http://localhost:{os.getenv('MCP_PORT', '8002')}")
        logger.info(f"AgentOS API:  http://localhost:{os.getenv('AGENTOS_PORT', '8000')}")
        logger.info("Agent UI:     http://localhost:3000 (start separately)")

        uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("AGENTOS_PORT", "8000")), log_level="info")
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        if mcp_process:
            mcp_process.terminate()
            mcp_process.wait()
            logger.info("MCP server stopped")


def run_agent_only():
    """Run only the AgentOS server (assumes MCP is running)."""
    logger.info("Starting AgentOS on port 8000 (MCP must be running on 8002)...")
    agent_os = create_xtwitter_agent_os()
    app = agent_os.get_app()
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("AGENTOS_PORT", "8000")), log_level="info")


def run_mcp_only():
    """Run only the MCP server."""
    from egile_mcp_x_post_creator import server

    logger.info(f"Starting MCP server on port {os.getenv('MCP_PORT', '8002')}...")
    server.mcp.run()


if __name__ == "__main__":
    run_all()
