"""The MiniBig Bluetooth integration."""

from __future__ import annotations

import logging

from homeassistant.components import bluetooth
from homeassistant.components.bluetooth import BluetoothScanningMode
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.typing import ConfigType

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
from .services import async_setup_services
from .session_report import build_session_report
from .types import MiniBigConfigEntry, MiniBigData

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the MiniBig integration (registers services)."""
    await async_setup_services(hass)
    return True


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
        ble_device_callback=lambda: bluetooth.async_ble_device_from_address(hass, address, connectable=True),
        command_timeout=DEFAULT_COMMAND_TIMEOUT_S,
        idle_disconnect_s=DEFAULT_IDLE_DISCONNECT_S,
        keep_connected=entry.options.get(CONF_KEEP_CONNECTED, DEFAULT_KEEP_CONNECTED),
        movement_idle_s=DEFAULT_MOVEMENT_IDLE_S,
        max_session_s=DEFAULT_MAX_SESSION_S,
        # NumberSelector stores values as floats; bleak-retry-connector's
        # max_attempts is typed as int, so coerce rather than pass a float.
        retry_count=int(entry.options.get(CONF_RETRY_COUNT, DEFAULT_RETRY_COUNT)),
        loop=hass.loop,
        report_builder=lambda operation, trace, exc: build_session_report(
            hass, address, operation=operation, trace=trace, exc=exc
        ),
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

    # Populate state once at startup. Without this, DataUpdateCoordinator only
    # starts its interval timer when the first entity subscribes, so the first
    # actual poll would not happen until a full poll_interval_min (30 min by
    # default) had elapsed - leaving battery/position showing as unknown after
    # every restart until the user pressed Refresh manually.
    #
    # async_config_entry_first_refresh() is deliberately not used: it raises
    # ConfigEntryNotReady on failure, which would abort setup entirely. This
    # device is battery powered and frequently out of range or busy with the
    # official app, and a failed poll is explicitly treated as non-fatal
    # elsewhere in this integration (see MiniBigActiveCoordinator).
    await active_coordinator.async_refresh()

    # Forward entry setups to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: MiniBigConfigEntry) -> bool:
    """Unload a MiniBig config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        data = entry.runtime_data
        await data.connection.close()
        data.active_coordinator.async_unload()

    return unload_ok
