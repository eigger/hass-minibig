"""Tests for MiniBig services."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError

from custom_components.minibig import services
from custom_components.minibig.minibig_ble import OPERATION_SERVICE


def _entry(state=ConfigEntryState.LOADED, send_raw=None, send_dps=None):
    conn = MagicMock()
    conn.send_raw = send_raw or AsyncMock()
    conn.send_dps = send_dps or AsyncMock()
    return SimpleNamespace(
        domain="minibig",
        state=state,
        unique_id="AA:BB",
        runtime_data=SimpleNamespace(connection=conn),
    )


async def _register(entries: dict):
    hass = MagicMock()
    handlers = {}
    hass.services.async_register = lambda d, name, h, schema=None: handlers.__setitem__(name, h)
    await services.async_setup_services(hass)
    hass.config_entries.async_get_entry = lambda eid: entries.get(eid)
    dev_reg = MagicMock()
    dev_reg.async_get = lambda did: SimpleNamespace(config_entries=[did]) if did in entries else None
    return hass, handlers, dev_reg


def _call(**data):
    return SimpleNamespace(data=data)


async def test_unknown_device_is_validation_error():
    hass, handlers, dev_reg = await _register({})
    with patch.object(services.dr, "async_get", return_value=dev_reg):
        with pytest.raises(ServiceValidationError):
            await handlers["publish_dps"](_call(device_id=["nope"], dps=[{"dp_id": 1, "value": 2}]))


async def test_unloaded_entry_rejected():
    hass, handlers, dev_reg = await _register({"d1": _entry(state=ConfigEntryState.NOT_LOADED)})
    with patch.object(services.dr, "async_get", return_value=dev_reg):
        with pytest.raises(ServiceValidationError):
            await handlers["publish_dps"](_call(device_id=["d1"], dps=[{"dp_id": 1, "value": 2}]))


async def test_invalid_hex_payload():
    hass, handlers, dev_reg = await _register({"d1": _entry()})
    with patch.object(services.dr, "async_get", return_value=dev_reg):
        with pytest.raises(ServiceValidationError):
            await handlers["send_raw"](_call(device_id=["d1"], method=1, payload="zz"))


async def test_publish_dps_passes_operation():
    entry = _entry()
    hass, handlers, dev_reg = await _register({"d1": entry})
    with patch.object(services.dr, "async_get", return_value=dev_reg):
        await handlers["publish_dps"](_call(device_id=["d1"], dps=[{"dp_id": 1, "value": 2}]))
    entry.runtime_data.connection.send_dps.assert_awaited_once_with([(1, 2)], operation=OPERATION_SERVICE)


async def test_partial_failure_aggregates_and_good_device_still_runs():
    good = _entry()
    good.runtime_data.connection.send_raw.return_value = SimpleNamespace(method=1, status=0, data=b"\x01", ok=True)
    bad = _entry(send_raw=AsyncMock(side_effect=RuntimeError("boom")))
    hass, handlers, dev_reg = await _register({"g": good, "b": bad})
    with patch.object(services.dr, "async_get", return_value=dev_reg):
        with pytest.raises(HomeAssistantError) as exc:
            await handlers["send_raw"](_call(device_id=["b", "g"], method=1, payload=""))
    assert not isinstance(exc.value, ServiceValidationError)
    good.runtime_data.connection.send_raw.assert_awaited_once()
    hass.bus.async_fire.assert_called_once()
