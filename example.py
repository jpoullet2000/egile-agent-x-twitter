"""Example: Using XTwitterPlugin with an agent."""

import asyncio
from egile_agent_core import Agent
from egile_agent_x_twitter import XTwitterPlugin


async def main() -> None:
    plugin = XTwitterPlugin(mcp_host="localhost", mcp_port=8002)

    agent = Agent(
        name="XSocialManager",
        model="gpt-4o-mini",
        plugins=[plugin],
        system_prompt=(
            "You are a social media manager for X. Draft posts and ask before publishing."
        ),
    )

    await agent.start()

    print("=" * 60)
    print("Drafting a post...")
    draft = await plugin.create_post(
        text="We just launched our new AI feature!",
        style="casual",
        include_hashtags=True,
    )
    print(draft)

    print("\nAsking user for confirmation before publishing...")
    # Simulate user approval
    publish = await plugin.publish_post(
        post_text="🚀 We just launched our new AI feature! #AI #Launch",
        confirm=True,
    )
    print(publish)


if __name__ == "__main__":
    asyncio.run(main())
