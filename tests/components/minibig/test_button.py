"""Real Home Assistant button platform regression tests."""

from .test_platforms import entity_id


async def test_buttons_restart_and_refresh(hass, loaded_entry, transport):
    for key in ("restart", "refresh"):
        before = len(transport.written_frames)
        await hass.services.async_call("button", "press", {"entity_id": entity_id(hass, "button", key)}, blocking=True)
        assert len(transport.written_frames) == before + 1
