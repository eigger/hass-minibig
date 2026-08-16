"""Data coordinators for the MiniBig integration."""

from __future__ import annotations

from collections.abc import Callable
from datetime import timedelta
import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.bluetooth import (
    BluetoothScanningMode,
    BluetoothServiceInfoBleak,
)
from homeassistant.components.bluetooth.passive_update_processor import (
    PassiveBluetoothProcessorCoordinator,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_POLL_INTERVAL_MIN,
    CONF_POSITION_DP_ID,
    CONF_POWER_DP_ID,
    DEFAULT_POLL_INTERVAL_MIN,
)
from .minibig_ble import DeviceProfile, MiniBigConnection, MiniBigDeviceInfo

if TYPE_CHECKING:
    from .types import MiniBigConfigEntry

_LOGGER = logging.getLogger(__name__)


class MiniBigPassiveBluetoothProcessorCoordinator(
    PassiveBluetoothProcessorCoordinator[MiniBigDeviceInfo]
):
    """Coordinator that processes BLE advertisements in ACTIVE scanning mode."""

    def __init__(
        self,
        hass: HomeAssistant,
        logger: logging.Logger,
        address: str,
        mode: BluetoothScanningMode,
        update_method: Callable[[BluetoothServiceInfoBleak], MiniBigDeviceInfo | None],
        entry: MiniBigConfigEntry,
        connectable: bool = True,
    ) -> None:
        """Initialize the passive BLE advertisement processor coordinator."""
        self.entry = entry
        self._last_device_info: MiniBigDeviceInfo | None = None

        def _wrapped_update_method(service_info: BluetoothServiceInfoBleak) -> MiniBigDeviceInfo | None:
            info = update_method(service_info)
            if info:
                self._last_device_info = info
            return info

        super().__init__(hass, logger, address, mode, _wrapped_update_method, connectable)

    @property
    def last_device_info(self) -> MiniBigDeviceInfo | None:
        """Return the last parsed device info from advertisement."""
        return self._last_device_info


class MiniBigActiveCoordinator(DataUpdateCoordinator[dict[int, int]]):
    """Coordinator for periodic active GATT polling and push event aggregation."""

    def __init__(
        self,
        hass: HomeAssistant,
        logger: logging.Logger,
        entry: MiniBigConfigEntry,
        connection: MiniBigConnection,
        profile: DeviceProfile,
    ) -> None:
        """Initialize the active polling coordinator."""
        self.entry = entry
        self.connection = connection
        self.profile = profile

        poll_min = entry.options.get(CONF_POLL_INTERVAL_MIN, DEFAULT_POLL_INTERVAL_MIN)
        interval = timedelta(minutes=poll_min) if poll_min > 0 else None

        super().__init__(
            hass,
            logger,
            name=f"MiniBig Active Coordinator {entry.unique_id}",
            update_interval=interval,
        )
        self.data: dict[int, int] = {}

        # Subscribe to streaming notifications from connection
        self._unsub_report = self.connection.register_report_callback(self._handle_device_report)

    def _log_unknown_dps(self, dps: dict[int, int]) -> None:
        """Log unknown or unhandled DPs for diagnostics."""
        known = set(self.profile.known_dps)
        options = self.entry.options
        for opt_key in (CONF_POWER_DP_ID, CONF_POSITION_DP_ID):
            opt_val = options.get(opt_key)
            if opt_val is not None:
                known.add(opt_val)

        for dp_id, val in dps.items():
            if dp_id not in known:
                _LOGGER.debug(
                    "Received unhandled/unknown DP %d with value %d from %s",
                    dp_id,
                    val,
                    self.entry.unique_id,
                )

    def _handle_device_report(self, resp: Any) -> None:
        """Handle streaming status report from device."""
        if hasattr(resp, "dps") and resp.dps:
            self._log_unknown_dps(resp.dps)
            self.data = {**self.data, **resp.dps}
            self.async_set_updated_data(self.data)

    async def _async_update_data(self) -> dict[int, int]:
        """Perform active poll over BLE GATT."""
        poll_min = self.entry.options.get(CONF_POLL_INTERVAL_MIN, DEFAULT_POLL_INTERVAL_MIN)
        if poll_min <= 0:
            return self.data or {}

        # Skip polling while device is moving
        if self.connection.is_moving:
            _LOGGER.debug("Skipping poll for %s: device is currently moving", self.entry.unique_id)
            return self.data or {}

        try:
            strategy = self.profile.refresh_strategy
            if strategy == "dp3":
                # Window opener: send dp3 (stop) which returns position without physical motion
                stop_dp = self.profile.dp_stop if self.profile.dp_stop is not None else 3
                resp = await self.connection.send_dps([(stop_dp, 0)])
            elif strategy == "read_setting":
                resp = await self.connection.read_dps()
            elif strategy == "none":
                return self.data or {}
            else:
                resp = await self.connection.read_dps()

            if resp and resp.ok and resp.dps:
                self._log_unknown_dps(resp.dps)
                self.data = {**self.data, **resp.dps}
                return self.data
        except Exception as err:
            # Polling failures (e.g. app in use, range) should not mark entities unavailable
            _LOGGER.debug("Active polling failed for %s (ignored): %s", self.entry.unique_id, err)

        return self.data or {}

    def async_unload(self) -> None:
        """Unsubscribe listeners on coordinator unload."""
        if self._unsub_report:
            self._unsub_report()
            self._unsub_report = None
