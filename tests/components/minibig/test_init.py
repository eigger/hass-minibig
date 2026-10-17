"""Load MiniBig through the real HA config entry and platform managers."""

from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import device_registry as dr, entity_registry as er

from .conftest import ADDRESS


async def test_setup_platform_states_and_unload(hass, loaded_entry, transport):
    entry = loaded_entry
    assert entry.state is ConfigEntryState.LOADED
    reg = er.async_get(hass)
    entities = er.async_entries_for_config_entry(reg, entry.entry_id)
    assert {e.domain for e in entities} == {"sensor", "binary_sensor", "cover", "button"}
    assert any(
        ("minibig", ADDRESS) in device.identifiers
        for device in dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)
    )

    def state(key, domain):
        return hass.states.get(reg.async_get_entity_id(domain, "minibig", f"{ADDRESS}_{key}"))

    assert state("battery", "sensor").state == "80"
    assert state("rssi", "sensor").state == "-55"
    assert state("cover", "cover").attributes["current_position"] == 50
    assert state("connectivity", "binary_sensor").state == "on"
    connection = entry.runtime_data.connection
    passive = entry.runtime_data.passive_coordinator
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert not transport.is_connected
    assert connection._worker_task.done()
    assert not connection._report_callbacks
    assert not connection._movement_callbacks
    assert not connection._connection_callbacks
    assert not passive._listeners


async def test_setup_cancelled_during_subscribe_releases_link(hass, entry, advertisement, transport, monkeypatch):
    import asyncio

    reached = asyncio.Event()

    async def subscribe(*args):
        reached.set()
        await asyncio.Event().wait()

    monkeypatch.setattr(transport, "start_notify", subscribe)
    setup = asyncio.create_task(hass.config_entries.async_setup(entry.entry_id))
    await reached.wait()
    connection = entry.runtime_data.connection
    setup.cancel()
    try:
        await setup
    except asyncio.CancelledError:
        pass
    await hass.async_block_till_done()
    assert connection._closing
    assert not transport.is_connected
    assert connection._worker_task.done()
    assert not entry.runtime_data.passive_coordinator._listeners
    assert entry.runtime_data.active_coordinator._unsub_report is None
    # A later advertisement must not update the failed entry anymore.
    from .conftest import make_advertisement

    old_info = entry.runtime_data.passive_coordinator.last_device_info
    from habluetooth import get_manager

    get_manager().scanner_adv_received(make_advertisement(idv=b"\x12\x34"))
    await hass.async_block_till_done()
    assert entry.runtime_data.passive_coordinator.last_device_info is old_info


async def test_offline_startup_then_advertisement_self_heals_identity(hass, entry, bluetooth_ready, transport):
    from .conftest import make_advertisement

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    connection = entry.runtime_data.connection
    assert connection.device_info.idv == "0000"
    assert entry.state is ConfigEntryState.LOADED
    assert connection.reports.failures == 0
    bluetooth_ready.scanner_adv_received(make_advertisement())
    await hass.async_block_till_done()
    assert connection.device_info.idv == "1CFE"
    assert entry.data["idv"] == "1CFE"
    await entry.runtime_data.active_coordinator.async_refresh()
    await hass.async_block_till_done()
    assert transport.is_connected
    assert entry.runtime_data.active_coordinator.data[0] == 50
    assert connection.reports.failures == 0


async def test_stored_identity_survives_restart_without_advertisement(hass, entry, bluetooth_ready):
    hass.config_entries.async_update_entry(
        entry, data={"address": ADDRESS, "idv": "1CFE", "fv": 2, "rev": 1, "d_type": 5, "is_legacy": False}
    )
    assert await hass.config_entries.async_setup(entry.entry_id)
    assert entry.runtime_data.connection.device_info.idv == "1CFE"
    assert entry.runtime_data.connection.device_info.fv == 2


async def test_stale_entities_removed_without_changing_current_ids(hass, entry, advertisement, transport):
    registry = er.async_get(hass)
    for domain, key in [("sensor", "last_status"), ("sensor", "last_error"), ("button", "clear_errors")]:
        registry.async_get_or_create(domain, "minibig", f"{ADDRESS}_{key}", config_entry=entry)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    for domain, key in [("sensor", "last_status"), ("sensor", "last_error"), ("button", "clear_errors")]:
        assert registry.async_get_entity_id(domain, "minibig", f"{ADDRESS}_{key}") is None
    assert registry.async_get_entity_id("cover", "minibig", f"{ADDRESS}_cover")


async def test_unexpected_setup_failure_releases_resources(hass, entry, advertisement, transport, monkeypatch):
    """Fault injection after the first real refresh exercises HA's error path."""

    def fail_after_refresh(*args):
        raise RuntimeError("injected setup failure")

    monkeypatch.setattr("custom_components.minibig._async_remove_stale_entities", fail_after_refresh)
    assert not await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    data = entry.runtime_data
    assert entry.state is ConfigEntryState.SETUP_ERROR
    assert data.connection._closing
    assert not transport.is_connected
    assert not data.passive_coordinator._listeners
    assert data.active_coordinator._unsub_report is None


async def test_partial_forward_failure_rolls_back_real_platforms(hass, entry, advertisement, transport, monkeypatch):
    """Exercise rollback after real entities were added and forwarding then fails."""
    forward = hass.config_entries.async_forward_entry_setups

    async def fail_after_real_forward(config_entry, platforms):
        await forward(config_entry, platforms)
        await hass.async_block_till_done()
        raise RuntimeError("injected failure after real platform setup")

    monkeypatch.setattr(hass.config_entries, "async_forward_entry_setups", fail_after_real_forward)
    assert not await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.SETUP_ERROR
    data = entry.runtime_data
    assert data.connection._closing
    assert not transport.is_connected
    assert not data.passive_coordinator._listeners
    assert data.active_coordinator._unsub_report is None
    assert not data.connection._movement_callbacks
    assert not data.connection._connection_callbacks
    for entity in er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id):
        state = hass.states.get(entity.entity_id)
        assert state is None or state.state == "unavailable"


async def test_coordinator_constructor_failure_does_not_subscribe(hass, entry, bluetooth_ready, transport):
    """An initialization error must not leave advertisement listeners behind."""
    from .conftest import make_advertisement

    hass.config_entries.async_update_entry(entry, options={"poll_interval_min": "invalid stored value"})
    assert not await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.SETUP_ERROR
    assert "idv" not in entry.data
    bluetooth_ready.scanner_adv_received(make_advertisement())
    await hass.async_block_till_done()
    # Before the subscription was moved, the leaked identity listener persisted
    # this advertisement into an entry whose initialization had already failed.
    assert "idv" not in entry.data
    assert not transport.is_connected
    assert not transport.written_frames
