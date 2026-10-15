"""Services for the MiniBig integration."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

import voluptuous as vol
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN
from .minibig_ble import OPERATION_SERVICE
from .types import MiniBigConfigEntry

_LOGGER = logging.getLogger(__name__)

SERVICE_SEND_RAW = "send_raw"
SERVICE_PUBLISH_DPS = "publish_dps"

SERVICE_SEND_RAW_SCHEMA = vol.Schema(
    {
        vol.Required("device_id"): vol.All(cv.ensure_list, [cv.string]),
        vol.Required("method"): cv.positive_int,
        vol.Optional("payload", default=""): cv.string,
    }
)

SERVICE_PUBLISH_DPS_SCHEMA = vol.Schema(
    {
        vol.Required("device_id"): vol.All(cv.ensure_list, [cv.string]),
        vol.Required("dps"): vol.All(
            cv.ensure_list,
            [
                vol.Schema(
                    {
                        vol.Required("dp_id"): cv.positive_int,
                        vol.Required("value"): cv.positive_int,
                    }
                )
            ],
        ),
    }
)


def _get_loaded_entry(hass: HomeAssistant, device_id: str) -> MiniBigConfigEntry:
    """Resolve a device registry ID to its loaded MiniBig config entry."""
    device = dr.async_get(hass).async_get(device_id)
    if device is not None:
        for entry_id in device.config_entries:
            entry = hass.config_entries.async_get_entry(entry_id)
            if entry is not None and entry.domain == DOMAIN:
                if entry.state is not ConfigEntryState.LOADED:
                    raise ServiceValidationError(f"Device '{device_id}' is not loaded")
                return entry
    raise ServiceValidationError(f"Device '{device_id}' not found or not a MiniBig device")


async def _async_for_each_device(
    hass: HomeAssistant,
    service: str,
    device_ids: list[str],
    action: Callable[[str, MiniBigConfigEntry], Awaitable[None]],
) -> None:
    """Run an action for every targeted device, aggregating failures."""
    errors: list[str] = []
    for device_id in device_ids:
        try:
            entry = _get_loaded_entry(hass, device_id)
            await action(device_id, entry)
        except Exception as err:  # noqa: BLE001 - report per-device, keep going
            _LOGGER.error("%s command failed for %s: %s", service, device_id, err)
            errors.append(f"{device_id}: {err}")

    if errors:
        raise HomeAssistantError(f"{service} failed for {len(errors)} device(s): {', '.join(errors)}")


async def async_setup_services(hass: HomeAssistant) -> None:
    """Register MiniBig services (once, from async_setup)."""

    async def handle_send_raw(call: ServiceCall) -> None:
        method = call.data["method"]
        payload_hex = call.data["payload"]
        try:
            payload = bytes.fromhex(payload_hex) if payload_hex else b""
        except ValueError as err:
            raise ServiceValidationError(f"Invalid hexadecimal payload '{payload_hex}': {err}") from err

        async def _send(device_id: str, entry: MiniBigConfigEntry) -> None:
            resp = await entry.runtime_data.connection.send_raw(method, payload)
            _LOGGER.info(
                "minibig.send_raw response from %s: status=%s, data=%s",
                entry.unique_id,
                resp.status,
                resp.data.hex(),
            )
            hass.bus.async_fire(
                "minibig_raw_response",
                {
                    "device_id": device_id,
                    "address": entry.unique_id,
                    "method": resp.method,
                    "status": resp.status,
                    "data": resp.data.hex(),
                    "ok": resp.ok,
                },
            )

        await _async_for_each_device(hass, SERVICE_SEND_RAW, call.data["device_id"], _send)

    async def handle_publish_dps(call: ServiceCall) -> None:
        dps = [(item["dp_id"], item["value"]) for item in call.data["dps"]]

        async def _publish(_device_id: str, entry: MiniBigConfigEntry) -> None:
            await entry.runtime_data.connection.send_dps(dps, operation=OPERATION_SERVICE)

        await _async_for_each_device(hass, SERVICE_PUBLISH_DPS, call.data["device_id"], _publish)

    hass.services.async_register(DOMAIN, SERVICE_SEND_RAW, handle_send_raw, schema=SERVICE_SEND_RAW_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_PUBLISH_DPS, handle_publish_dps, schema=SERVICE_PUBLISH_DPS_SCHEMA)
