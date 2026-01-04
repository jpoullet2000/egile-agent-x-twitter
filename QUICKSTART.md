# Quick Start

1) Install
```
cd egile-agent-x-twitter
./install.sh    # or install.bat on Windows
```

2) Configure env
```
cp .env.example .env
# Set one agent model key: XAI_API_KEY or OPENAI_API_KEY or MISTRAL_API_KEY
# Set X API keys to publish: X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET
# MCP defaults: MCP_HOST=localhost, MCP_PORT=8002
```

3) Run everything (MCP + AgentOS)
```
python -m egile_agent_x_twitter.run_server
```

4) Optional: start Agent UI
```
cd ../agent-ui
pnpm dev
# open http://localhost:3000 (AgentOS at http://localhost:8000)
```

5) Test a draft via plugin (pseudo)
```
agent.process("Draft a witty post about our new AI feature")
# Plugin will call create_post then ask to confirm before publish_post
```

Notes
- Publishing requires confirm=True and valid X credentials
- Drafting works without X credentials; LLM quality depends on MCP-side keys
