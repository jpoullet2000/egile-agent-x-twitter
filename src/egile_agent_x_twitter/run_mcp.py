"""Run only the MCP server."""

from egile_mcp_x_post_creator import server


def run_mcp_only():
    server.mcp.run()


if __name__ == "__main__":
    run_mcp_only()
