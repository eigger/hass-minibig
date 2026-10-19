"""Real Home Assistant switch platform regression tests."""

from .test_platforms import entity_id


async def test_switch_override_creates_working_entity(hass, entry, advertisement, transport):
    hass.config_entries.async_update_entry(entry, options={**entry.options, "power_dp_id": 1})
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    eid = entity_id(hass, "switch", "switch")
    assert eid
    for service, ending in [("turn_on", "010001"), ("turn_off", "010000")]:
        await hass.services.async_call("switch", service, {"entity_id": eid}, blocking=True)
        assert transport.written_frames[-1].hex().endswith(ending)
