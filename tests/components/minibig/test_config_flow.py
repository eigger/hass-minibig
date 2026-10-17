"""Actual HA discovery, duplicate handling and option reload flows."""

import pytest
from homeassistant.config_entries import SOURCE_BLUETOOTH, SOURCE_USER
from homeassistant.data_entry_flow import FlowResultType

from .conftest import ADDRESS, make_advertisement


async def test_bluetooth_confirm(hass, bluetooth_ready, transport):
    result = await hass.config_entries.flow.async_init(
        "minibig", context={"source": SOURCE_BLUETOOTH}, data=make_advertisement()
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "bluetooth_confirm"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {"address": ADDRESS}
    assert result["result"].unique_id == ADDRESS
    await hass.async_block_till_done()


async def test_bluetooth_duplicate(hass, entry, bluetooth_ready):
    result = await hass.config_entries.flow.async_init(
        "minibig", context={"source": SOURCE_BLUETOOTH}, data=make_advertisement()
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


@pytest.mark.parametrize(
    ("name", "dtype", "reason"), [("unrelated", 5, "not_minibig_device"), ("HubMini", 2, "hubmini_not_supported")]
)
async def test_bluetooth_rejects_unsupported(hass, bluetooth_ready, name, dtype, reason):
    info = make_advertisement(name=name, d_type=dtype)
    if reason == "not_minibig_device":
        info.service_uuids.clear()
    result = await hass.config_entries.flow.async_init("minibig", context={"source": SOURCE_BLUETOOTH}, data=info)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == reason


async def test_user_no_devices(hass, bluetooth_ready):
    result = await hass.config_entries.flow.async_init("minibig", context={"source": SOURCE_USER})
    assert result["reason"] == "no_devices_found"


async def test_user_discovered_device(hass, advertisement, transport):
    result = await hass.config_entries.flow.async_init("minibig", context={"source": SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"address": ADDRESS})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {"address": ADDRESS}
    await hass.async_block_till_done()


async def test_options_reload_preserves_ids_and_closes_old_connection(hass, loaded_entry):
    entry = loaded_entry
    old = entry.runtime_data
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"poll_interval_min": 15.0, "retry_count": 2.0, "keep_connected": True}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert entry.runtime_data is not old
    assert old.connection._closing
    assert old.active_coordinator._unsub_report is None
    assert not old.passive_coordinator._listeners
    assert entry.runtime_data.connection.retry_count == 2
    assert entry.runtime_data.connection.keep_connected
    assert entry.unique_id == ADDRESS
