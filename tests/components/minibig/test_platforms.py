"""Exercise entity actions and live notifications through HA platforms."""

from homeassistant.helpers import entity_registry as er

from .conftest import ADDRESS


def entity_id(hass, domain, key):
    return er.async_get(hass).async_get_entity_id(domain, "minibig", f"{ADDRESS}_{key}")


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


async def test_buttons_restart_and_refresh(hass, loaded_entry, transport):
    for key in ("restart", "refresh"):
        before = len(transport.written_frames)
        await hass.services.async_call("button", "press", {"entity_id": entity_id(hass, "button", key)}, blocking=True)
        assert len(transport.written_frames) == before + 1


async def test_link_disconnect_and_reconnect_updates_connectivity(hass, loaded_entry, transport):
    connection = loaded_entry.runtime_data.connection
    eid = entity_id(hass, "binary_sensor", "connectivity")
    assert hass.states.get(eid).state == "on"
    transport._is_connected = False
    connection._on_client_disconnected(transport)
    await hass.async_block_till_done()
    assert hass.states.get(eid).state == "off"
    await connection.send_dps([(0, 25)])
    await hass.async_block_till_done()
    assert hass.states.get(eid).state == "on"


async def test_switch_override_creates_working_entity(hass, entry, advertisement, transport):
    hass.config_entries.async_update_entry(entry, options={**entry.options, "power_dp_id": 1})
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    eid = entity_id(hass, "switch", "switch")
    assert eid
    for service, ending in [("turn_on", "010001"), ("turn_off", "010000")]:
        await hass.services.async_call("switch", service, {"entity_id": eid}, blocking=True)
        assert transport.written_frames[-1].hex().endswith(ending)


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


async def test_number_override_uses_configured_dp(hass, entry, advertisement, transport):
    hass.config_entries.async_update_entry(entry, options={**entry.options, "dp_overrides": {"length": 7}})
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    eid = entity_id(hass, "number", "length")
    assert eid
    await hass.services.async_call("number", "set_value", {"entity_id": eid, "value": 200}, blocking=True)
    assert transport.written_frames[-1].hex().endswith("0700c8")
    assert not any(e.domain == "select" for e in er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id))
