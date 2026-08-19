"""The MiniBig Bluetooth integration."""

from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant.components import bluetooth
from homeassistant.components.bluetooth import BluetoothScanningMode
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr

from .const import (
    CONF_D_TYPE,
    CONF_FV,
    CONF_IDV,
    CONF_IS_LEGACY,
    CONF_KEEP_CONNECTED,
    CONF_RETRY_COUNT,
    CONF_REV,
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
    DEVICE_NOTIFY_UUID,
    DEVICE_SERVICE_UUID,
    DEVICE_WRITE_UUID,
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
        # No live advertisement yet at this exact moment (e.g. right after HA
        # startup). Prefer the last known-good identity persisted from a
        # previous session over a blind idv="0000" placeholder, so the very
        # first command after a restart already carries a real IDV header
        # instead of being guaranteed to fail with 255 DEVICE_NOT_MATCHING
        # until a fresh advertisement happens to be parsed.
        stored_idv = entry.data.get(CONF_IDV)
        dev_info = MiniBigDeviceInfo(
            address=address,
            name=entry.title,
            idv=stored_idv or "0000",
            fv=entry.data.get(CONF_FV, 0),
            rev=entry.data.get(CONF_REV, 0),
            d_type=entry.data.get(CONF_D_TYPE, 0),
            init_mode=False,
            is_legacy=entry.data.get(CONF_IS_LEGACY, False),
            service_uuid=DEVICE_SERVICE_UUID,
            write_uuid=DEVICE_WRITE_UUID,
            notify_uuid=DEVICE_NOTIFY_UUID,
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
    # Without this, the coordinator never subscribes to advertisement events at
    # all: RSSI/connectivity/pairing-mode entities stay stuck at their initial
    # (usually unknown) value forever, and the device_info self-heal listener
    # registered below never fires either.
    entry.async_on_unload(passive_coordinator.async_start())

    @callback
    def _refresh_connection_device_info() -> None:
        """Keep the BLE client's IDV/fv/rev in sync with live advertisements,
        and persist a real identity into the config entry so it survives
        restarts too.

        Setup above only captures one snapshot (a live advertisement, a
        previously persisted identity, or a idv="0000" placeholder as a last
        resort). Without this listener, a bad initial snapshot sends the
        wrong IDV header on every command for the entry's whole lifetime
        (device replies 255 DEVICE_NOT_MATCHING) until Home Assistant is
        restarted. update_device_info() ignores a placeholder idv if a real
        one is already known, so this only ever improves on the initial
        snapshot - and once persisted, later restarts start from that real
        identity immediately instead of the "0000" placeholder again.
        """
        if (info := passive_coordinator.last_device_info) is None:
            return
        connection.update_device_info(info)

        if info.idv == "0000":
            return
        stored = (
            entry.data.get(CONF_IDV),
            entry.data.get(CONF_FV),
            entry.data.get(CONF_REV),
            entry.data.get(CONF_D_TYPE),
            entry.data.get(CONF_IS_LEGACY),
        )
        fresh = (info.idv, info.fv, info.rev, info.d_type, info.is_legacy)
        if stored != fresh:
            hass.config_entries.async_update_entry(
                entry,
                data={
                    **entry.data,
                    CONF_IDV: info.idv,
                    CONF_FV: info.fv,
                    CONF_REV: info.rev,
                    CONF_D_TYPE: info.d_type,
                    CONF_IS_LEGACY: info.is_legacy,
                },
            )

    entry.async_on_unload(passive_coordinator.async_add_listener(_refresh_connection_device_info))

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
