"""Real Home Assistant binary_sensor platform regression tests."""

from .test_platforms import entity_id


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
