"""Unknown enum mappings must not expose guessed Home Assistant controls."""

from homeassistant.helpers import entity_registry as er


async def test_dp_override_without_enum_mapping_exposes_no_select(hass, entry, advertisement, transport):
    """A DP override alone cannot provide the device-specific raw value map."""
    hass.config_entries.async_update_entry(entry, options={**entry.options, "dp_overrides": {"direction": 7}})
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert not any(e.domain == "select" for e in er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id))
    assert hass.config_entries.async_get_entry(entry.entry_id) is entry
