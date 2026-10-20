"""Real Home Assistant number platform regression tests."""

from homeassistant.helpers import entity_registry as er

from .test_platforms import entity_id


async def test_number_override_uses_configured_dp(hass, entry, advertisement, transport):
    hass.config_entries.async_update_entry(entry, options={**entry.options, "dp_overrides": {"length": 7}})
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    eid = entity_id(hass, "number", "length")
    assert eid
    await hass.services.async_call("number", "set_value", {"entity_id": eid, "value": 200}, blocking=True)
    assert transport.written_frames[-1].hex().endswith("0700c8")
    assert not any(e.domain == "select" for e in er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id))
