# Package Structure

- src/egile_agent_x_twitter/
  - __init__.py        # exports plugin and runners
  - __main__.py        # run all services
  - plugin.py          # XTwitterPlugin with create_post, publish_post
  - mcp_client.py      # HTTP client to MCP /call_tool
  - run_server.py      # orchestrates MCP + AgentOS
  - run_agent.py       # AgentOS only entry
  - run_mcp.py         # MCP only entry
- tests/
  - test_plugin.py     # basic plugin tests
- install.bat, install.sh
- README.md, QUICKSTART.md, USAGE_EXAMPLES.md, ARCHITECTURE.md, PACKAGE_STRUCTURE.md
- pyproject.toml, .env.example, .gitignore
