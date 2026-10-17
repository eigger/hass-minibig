"""Services exercised through the actual HA service and config entry registries."""

import pytest
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.minibig.minibig_ble import OPERATION_SERVICE


def device_id(hass, entry):
    return next(d.id for d in dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id))


async def test_unknown_device_is_validation_error(hass, loaded_entry):
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            "minibig", "publish_dps", {"device_id": ["nope"], "dps": [{"dp_id": 1, "value": 2}]}, blocking=True
        )


async def test_unloaded_entry_rejected(hass, loaded_entry):
    did = device_id(hass, loaded_entry)
    assert await hass.config_entries.async_unload(loaded_entry.entry_id)
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            "minibig", "publish_dps", {"device_id": [did], "dps": [{"dp_id": 1, "value": 2}]}, blocking=True
        )


async def test_invalid_hex_payload(hass, loaded_entry):
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            "minibig",
            "send_raw",
            {"device_id": [device_id(hass, loaded_entry)], "method": 1, "payload": "zz"},
            blocking=True,
        )


async def test_publish_dps_passes_operation(hass, loaded_entry, transport):
    await hass.services.async_call(
        "minibig",
        "publish_dps",
        {"device_id": [device_id(hass, loaded_entry)], "dps": [{"dp_id": 1, "value": 2}]},
        blocking=True,
    )
    assert transport.written_frames[-1].hex().endswith("010002")
    assert loaded_entry.runtime_data.connection.reports.last["operation"] == OPERATION_SERVICE


async def test_partial_failure_aggregates_and_good_device_still_runs(hass, loaded_entry, transport):
    bad = MockConfigEntry(
        domain="minibig",
        unique_id="11:22:33:44:55:66",
        title="Offline",
        data={"address": "11:22:33:44:55:66"},
        options={"poll_interval_min": 0},
    )
    bad.add_to_hass(hass)
    assert await hass.config_entries.async_setup(bad.entry_id)
    await hass.async_block_till_done()
    events = []
    remove = hass.bus.async_listen("minibig_raw_response", events.append)
    with pytest.raises(HomeAssistantError) as exc:
        await hass.services.async_call(
            "minibig",
            "send_raw",
            {"device_id": [device_id(hass, bad), device_id(hass, loaded_entry)], "method": 1},
            blocking=True,
        )
    assert not isinstance(exc.value, ServiceValidationError)
    await hass.async_block_till_done()
    assert len(events) == 1
    assert events[0].data["address"] == loaded_entry.unique_id
    remove()


async def test_all_targets_validated_before_actuation(hass, loaded_entry, transport):
    before = len(transport.written_frames)
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            "minibig",
            "publish_dps",
            {"device_id": [device_id(hass, loaded_entry), "invalid"], "dps": [{"dp_id": 0, "value": 100}]},
            blocking=True,
        )
    assert len(transport.written_frames) == before


async def test_debug_logs_omit_device_identity_and_raw_payload(hass, loaded_entry, caplog):
    import logging

    from .conftest import ADDRESS

    caplog.set_level(logging.DEBUG, logger="custom_components.minibig")
    await hass.services.async_call(
        "minibig",
        "send_raw",
        {"device_id": [device_id(hass, loaded_entry)], "method": 1, "payload": "cafebabe"},
        blocking=True,
    )
    component_log = "\n".join(
        record.getMessage() for record in caplog.records if record.name.startswith("custom_components.minibig")
    )
    assert ADDRESS not in component_log
    assert "cafebabe" not in component_log
