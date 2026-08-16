"""The MiniBig Bluetooth integration."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.components import bluetooth
from homeassistant.components.bluetooth import BluetoothScanningMode
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv, device_registry as dr

from .const import (
    CONF_KEEP_CONNECTED,
    CONF_RETRY_COUNT,
    DEFAULT_COMMAND_TIMEOUT_S,
    DEFAULT_IDLE_DISCONNECT_S,
    DEFAULT_KEEP_CONNECTED,
    DEFAULT_MAX_SESSION_S,
    DEFAULT_MOVEMENT_IDLE_S,
    DEFAULT_RETRY_COUNT,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import (
    MiniBigActiveCoordinator,
    MiniBigPassiveBluetoothProcessorCoordinator,
)
from .minibig_ble import (
    MiniBigConnection,
    MiniBigDeviceInfo,
    get_device_profile,
    parse_advertisement,
)
from .types import MiniBigConfigEntry, MiniBigData

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


async def async_setup_entry(hass: HomeAssistant, entry: MiniBigConfigEntry) -> bool:
    """Set up MiniBig from a config entry."""
    address: str = entry.data[CONF_ADDRESS]

    # Find latest advertisement info
    service_info = bluetooth.async_last_service_info(hass, address, connectable=True)
    dev_info = parse_advertisement(service_info) if service_info else None

    if dev_info is None:
        # Fallback default info if device is temporarily offline
        dev_info = MiniBigDeviceInfo(
            address=address,
            name=entry.title,
            idv="0000",
            fv=0,
            rev=0,
            d_type=0,
            init_mode=False,
            is_legacy=False,
            service_uuid="2b8d0001-6828-46af-98aa-557761b15400",
            write_uuid="2b8d0002-6828-46af-98aa-557761b15400",
            notify_uuid="2b8d0003-6828-46af-98aa-557761b15400",
        )

    profile = get_device_profile(dev_info)

    # Register in device registry
    dev_reg = dr.async_get(hass)
    dev_reg.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections={(dr.CONNECTION_BLUETOOTH, address)},
        identifiers={(DOMAIN, address)},
        manufacturer=profile.manufacturer,
        model=profile.model_name,
        name=entry.title,
        sw_version=f"fv{dev_info.fv}" if dev_info.fv else None,
        hw_version=f"rev{dev_info.rev}" if dev_info.rev else None,
    )

    # Instantiate connection manager
    connection = MiniBigConnection(
        device_info=dev_info,
        ble_device_callback=lambda: bluetooth.async_ble_device_from_address(
            hass, address, connectable=True
        ),
        command_timeout=DEFAULT_COMMAND_TIMEOUT_S,
        idle_disconnect_s=DEFAULT_IDLE_DISCONNECT_S,
        keep_connected=entry.options.get(CONF_KEEP_CONNECTED, DEFAULT_KEEP_CONNECTED),
        movement_idle_s=DEFAULT_MOVEMENT_IDLE_S,
        max_session_s=DEFAULT_MAX_SESSION_S,
        retry_count=entry.options.get(CONF_RETRY_COUNT, DEFAULT_RETRY_COUNT),
        loop=hass.loop,
    )

    passive_coordinator = MiniBigPassiveBluetoothProcessorCoordinator(
        hass,
        _LOGGER,
        address=address,
        mode=BluetoothScanningMode.ACTIVE,
        update_method=parse_advertisement,
        entry=entry,
        connectable=True,
    )

    active_coordinator = MiniBigActiveCoordinator(
        hass,
        _LOGGER,
        entry=entry,
        connection=connection,
        profile=profile,
    )

    entry.runtime_data = MiniBigData(
        device_info=dev_info,
        profile=profile,
        connection=connection,
        passive_coordinator=passive_coordinator,
        active_coordinator=active_coordinator,
    )

    # Register custom services once
    await _async_setup_services(hass)

    # Forward entry setups to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: MiniBigConfigEntry) -> bool:
    """Unload a MiniBig config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        data = entry.runtime_data
        await data.connection.disconnect()
        data.active_coordinator.async_unload()

        _async_unload_services_if_empty(hass)

    return unload_ok


def _async_unload_services_if_empty(hass: HomeAssistant) -> None:
    """Unload integration services if no config entries remain loaded."""
    has_loaded = False
    if hasattr(hass.config_entries, "async_loaded_entries"):
        has_loaded = bool(hass.config_entries.async_loaded_entries(DOMAIN))
    elif hasattr(hass.config_entries, "async_entries"):
        has_loaded = any(
            getattr(getattr(e, "state", None), "name", "") == "LOADED"
            for e in hass.config_entries.async_entries(DOMAIN)
        )

    if not has_loaded:
        if hass.services.has_service(DOMAIN, SERVICE_SEND_RAW):
            hass.services.async_remove(DOMAIN, SERVICE_SEND_RAW)
        if hass.services.has_service(DOMAIN, SERVICE_PUBLISH_DPS):
            hass.services.async_remove(DOMAIN, SERVICE_PUBLISH_DPS)


async def _async_setup_services(hass: HomeAssistant) -> None:
    """Register custom services for MiniBig integration."""
    if hass.services.has_service(DOMAIN, SERVICE_SEND_RAW):
        return

    async def handle_send_raw(call: ServiceCall) -> None:
        """Handle sending raw command frame."""
        device_ids = call.data["device_id"]
        method = call.data["method"]
        payload_hex = call.data.get("payload", "")

        try:
            payload = bytes.fromhex(payload_hex) if payload_hex else b""
        except ValueError as err:
            raise HomeAssistantError(f"Invalid hexadecimal payload '{payload_hex}': {err}") from err

        errors: list[str] = []
        for device_id in device_ids:
            entry = _get_entry_from_device_id(hass, device_id)
            if not entry or not hasattr(entry, "runtime_data"):
                errors.append(f"Device '{device_id}' not found or not a MiniBig device")
                continue

            try:
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
            except Exception as err:
                _LOGGER.error("send_raw command failed for %s: %s", device_id, err)
                errors.append(f"{device_id}: {err}")

        if errors:
            raise HomeAssistantError(f"send_raw failed for {len(errors)} device(s): {', '.join(errors)}")

    async def handle_publish_dps(call: ServiceCall) -> None:
        """Handle publishing DP values."""
        device_ids = call.data["device_id"]
        dps_input = call.data["dps"]
        dps = [(item["dp_id"], item["value"]) for item in dps_input]

        errors: list[str] = []
        for device_id in device_ids:
            entry = _get_entry_from_device_id(hass, device_id)
            if not entry or not hasattr(entry, "runtime_data"):
                errors.append(f"Device '{device_id}' not found or not a MiniBig device")
                continue

            try:
                await entry.runtime_data.connection.send_dps(dps)
            except Exception as err:
                _LOGGER.error("publish_dps command failed for %s: %s", device_id, err)
                errors.append(f"{device_id}: {err}")

        if errors:
            raise HomeAssistantError(f"publish_dps failed for {len(errors)} device(s): {', '.join(errors)}")

    hass.services.async_register(
        DOMAIN,
        SERVICE_SEND_RAW,
        handle_send_raw,
        schema=SERVICE_SEND_RAW_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_PUBLISH_DPS,
        handle_publish_dps,
        schema=SERVICE_PUBLISH_DPS_SCHEMA,
    )


def _get_entry_from_device_id(hass: HomeAssistant, device_id: str) -> MiniBigConfigEntry | None:
    """Look up config entry by device registry ID."""
    dev_reg = dr.async_get(hass)
    device = dev_reg.async_get(device_id)
    if not device:
        return None
    for entry_id in device.config_entries:
        entry = hass.config_entries.async_get_entry(entry_id)
        if entry and entry.domain == DOMAIN:
            return entry
    return None
