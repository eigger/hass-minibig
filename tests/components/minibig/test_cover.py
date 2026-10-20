"""Real Home Assistant cover platform regression tests."""

from .test_platforms import entity_id


async def test_cover_commands_and_streamed_position(hass, loaded_entry, transport):
    eid = entity_id(hass, "cover", "cover")
    for service, data, ending in [
        ("set_cover_position", {"position": 97}, "000061"),
        ("open_cover", {}, "000064"),
        ("close_cover", {}, "000000"),
        ("stop_cover", {}, "030000"),
    ]:
        await hass.services.async_call("cover", service, {"entity_id": eid, **data}, blocking=True)
        assert transport.written_frames[-1].hex().endswith(ending)
    transport.trigger_notify(bytes.fromhex("18fd000061"))
    await hass.async_block_till_done()
    assert hass.states.get(eid).attributes["current_position"] == 97
    assert hass.states.get(entity_id(hass, "binary_sensor", "moving")).state == "on"


async def test_live_startup_position_takes_priority_over_restored_state(hass, entry, advertisement, transport):
    from homeassistant.core import State
    from pytest_homeassistant_custom_component.common import mock_restore_cache

    mock_restore_cache(hass, [State("cover.test_opener_window", "open", {"current_position": 22})])
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get(entity_id(hass, "cover", "cover")).attributes["current_position"] == 50


async def test_offline_startup_preserves_restored_position(hass, entry, bluetooth_ready):
    from homeassistant.core import State
    from pytest_homeassistant_custom_component.common import mock_restore_cache

    mock_restore_cache(hass, [State("cover.test_opener_window", "open", {"current_position": 22})])
    hass.config_entries.async_update_entry(entry, options={**entry.options, "position_dp_id": 0})
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get(entity_id(hass, "cover", "cover")).attributes["current_position"] == 22
