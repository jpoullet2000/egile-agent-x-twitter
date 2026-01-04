# Architecture

## Components
- XTwitterPlugin (agent plugin) -> calls MCP Client
- MCPClient -> HTTP POST /call_tool to egile-mcp-x-post-creator (port 8002)
- AgentOS (egile-agent-core) -> exposes API/UI for interactions (port 8000)
- Agent UI (optional) -> next.js frontend (port 3000)

## Data Flow
User -> AgentOS -> Plugin -> MCPClient -> MCP Server -> X API (for publish)

## Ports
- MCP: 8002
- AgentOS: 8000
- UI: 3000

## Safety
- publish_post requires confirm=True
- Draft-first workflow enforced in instructions
- MCP server validates X credentials before publishing
