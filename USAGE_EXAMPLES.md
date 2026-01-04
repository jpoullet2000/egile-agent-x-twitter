# Usage Examples

## Inside an Agent Conversation
- User: "Draft a professional post about our Q1 launch."
- Agent: calls `create_post` -> shows draft with stats -> asks "Publish?"
- User: "Yes, publish it."
- Agent: calls `publish_post(post_text=draft, confirm=True)` and returns tweet URL.

## Direct Plugin Usage (async)
```python
from egile_agent_x_twitter import XTwitterPlugin
import asyncio

async def demo():
    plugin = XTwitterPlugin(mcp_host="localhost", mcp_port=8002)
    await plugin.on_agent_start(agent=None)  # minimal init

    draft = await plugin.create_post("We just shipped a new AI feature!", style="casual")
    print(draft)

    # Only publish with explicit confirmation
    published = await plugin.publish_post(post_text="🚀 We just shipped a new AI feature! #AI", confirm=True)
    print(published)

asyncio.run(demo())
```

## Safety Pattern
1) Always draft with `create_post`
2) Show user the draft text
3) Require explicit confirmation
4) Call `publish_post(..., confirm=True)` only after approval

## Typical Prompts
- "Create a witty post about our new release, include hashtags"
- "Make an inspirational post under 200 chars about team growth"
- "Publish the last draft now" (agent should verify confirmation)
