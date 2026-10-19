"""Real Home Assistant sensor platform regression tests."""

from .test_platforms import entity_id


async def test_failed_command_updates_real_diagnostic_states(hass, loaded_entry, transport):
    import pytest
    from homeassistant.exceptions import HomeAssistantError

    transport.response_generator = lambda frame: bytes([frame[0], 255])
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            "cover", "open_cover", {"entity_id": entity_id(hass, "cover", "cover")}, blocking=True
        )
    await hass.async_block_till_done()
    assert hass.states.get(entity_id(hass, "sensor", "error_count")).state == "1"
    failure = hass.states.get(entity_id(hass, "sensor", "last_failure"))
    assert failure.state not in ("unknown", "unavailable")
    assert failure.attributes["success"] is False
