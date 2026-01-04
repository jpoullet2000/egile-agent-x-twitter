"""Test to see the actual response from publish_post"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment from this project
load_dotenv()

from egile_agent_x_twitter.plugin import XTwitterPlugin


async def test_publish():
    """Test publish_post and see the actual response."""
    
    # Create plugin
    plugin = XTwitterPlugin(
        mcp_host=os.getenv("MCP_HOST", "localhost"),
        mcp_port=int(os.getenv("MCP_PORT", "8002")),
    )
    
    # Initialize (simulating agent start)
    class MockAgent:
        pass
    
    await plugin.on_agent_start(MockAgent())
    
    # Try to publish a test post
    test_post = "This is a test post to verify publish_post response."
    
    print("\n" + "="*60)
    print("TESTING publish_post WITH confirm=True")
    print("="*60)
    print(f"\nPost text: {test_post}")
    print(f"\nCalling publish_post...")
    
    try:
        response = await plugin.publish_post(
            post_text=test_post,
            confirm=True
        )
        
        print("\n" + "-"*60)
        print("RESPONSE RECEIVED:")
        print("-"*60)
        print(response)
        print("-"*60)
        
    except Exception as e:
        print(f"\n❌ EXCEPTION CAUGHT: {type(e).__name__}")
        print(f"Error: {str(e)}")
    
    finally:
        # Cleanup
        await plugin.cleanup()
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(test_publish())
