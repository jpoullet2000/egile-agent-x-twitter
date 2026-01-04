import pytest
from egile_agent_x_twitter import XTwitterPlugin


@pytest.mark.asyncio
async def test_plugin_properties():
    plugin = XTwitterPlugin()
    assert plugin.name == "xtwitter"
    assert plugin.version == "0.1.0"
    assert "Creates engaging X/Twitter posts" in plugin.description


@pytest.mark.asyncio
async def test_create_post_invokes_client(monkeypatch):
    plugin = XTwitterPlugin()

    class DummyClient:
        async def create_post(self, **kwargs):
            return "ok"

    plugin._client = DummyClient()
    result = await plugin.create_post(text="hello")
    assert result == "ok"


@pytest.mark.asyncio
async def test_publish_requires_client(monkeypatch):
    plugin = XTwitterPlugin()
    with pytest.raises(RuntimeError):
        await plugin.publish_post("text", confirm=True)


@pytest.mark.asyncio
async def test_publish_requires_post_text(monkeypatch):
    plugin = XTwitterPlugin()

    class DummyClient:
        async def publish_post(self, **kwargs):
            return kwargs.get("post_text")

    plugin._client = DummyClient()

    # Missing post_text with no cached draft should return guidance
    result = await plugin.publish_post(post_text="", confirm=True)
    assert "No post_text provided" in result
    assert "cached draft" in result

    # Missing post_text with cached draft should use cached value
    plugin._last_draft_text = "cached text"
    result_cached = await plugin.publish_post(post_text="", confirm=True)
    assert result_cached == "cached text"


@pytest.mark.asyncio
async def test_get_last_draft_returns_cached(monkeypatch):
    plugin = XTwitterPlugin()
    plugin._last_draft_text = "draft text"
    assert await plugin.get_last_draft() == "draft text"
