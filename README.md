# Egile Agent X Twitter

Agent plugin for Egile Agent Core that uses the egile-mcp-x-post-creator MCP server to craft and publish X/Twitter posts with safety confirmations.

## Features
- MCP-powered tools: create_post, publish_post (with explicit confirm=True)
- LLM-enhanced drafting (Claude/GPT via MCP server) with hashtag/emoji smarts
- AgentOS integration with safety-first instructions (preview before publish)
- SSE transport to MCP server (default port 8002)

## Quick Start
1) Install
```
cd egile-agent-x-twitter
./install.sh   # or install.bat on Windows
```
2) Configure .env (copy from .env.example) with:
- Agent model key: XAI or OpenAI or Mistral
- MCP server host/port (defaults: localhost:8002)
- X API credentials for publishing
- Optional LLM keys for better post generation (on the MCP side)
3) Run all services
```
python -m egile_agent_x_twitter.run_server
```
4) (Optional) Start Agent UI in ../agent-ui with `pnpm dev`, then open http://localhost:3000 (AgentOS at http://localhost:8000)

Safety reminder: Always include the exact draft text when calling publish_post. If the user just says “publish” without providing the text in that turn, ask them to paste the draft before publishing. Never invent or paraphrase drafts.

## Tools
- create_post(text, style="professional", include_hashtags=True, max_length=280)
- publish_post(post_text, confirm=False)  # must set confirm=True to actually publish

## Safety
- Always draft first with create_post
- Always show the draft to the user
- Only call publish_post with confirm=True after explicit user approval
- If X credentials are missing, the MCP server responds with setup guidance

## Ports
- MCP server (X Post Creator): 8002
- AgentOS API: 8000
- Agent UI: 3000 (run separately)

## License
MIT
