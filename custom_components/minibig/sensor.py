"""Sensor platform for the MiniBig integration."""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    EntityCategory,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import MiniBigActiveCoordinator, MiniBigPassiveBluetoothProcessorCoordinator
from .minibig_ble import STATUS_MESSAGES
from .types import MiniBigConfigEntry

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MiniBigConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up MiniBig sensor entities from config entry."""
    data = entry.runtime_data
    entities: list[SensorEntity] = [
        MiniBigRssiSensor(entry, data.passive_coordinator),
        MiniBigLastStatusSensor(entry, data.active_coordinator),
        MiniBigLastFailureSensor(entry, data.active_coordinator),
        MiniBigLastErrorSensor(entry, data.active_coordinator),
        MiniBigErrorCountSensor(entry, data.active_coordinator),
    ]

    # Add battery sensor if supported by profile
    if data.profile.dp_battery is not None:
        entities.append(
            MiniBigBatterySensor(entry, data.active_coordinator, data.profile.dp_battery)
        )

    async_add_entities(entities)


class MiniBigBaseSensor(CoordinatorEntity[Any], SensorEntity):
    """Base class for MiniBig sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        entry: MiniBigConfigEntry,
        coordinator: Any,
        key: str,
        translation_key: str,
    ) -> None:
        """Initialize sensor entity."""
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.unique_id}_{key}"
        self._attr_translation_key = translation_key
        address = entry.runtime_data.device_info.address
        self._attr_device_info = DeviceInfo(
            connections={(CONNECTION_BLUETOOTH, address)},
            identifiers={(DOMAIN, address)},
        )


class MiniBigBatterySensor(MiniBigBaseSensor):
    """Battery level sensor for MiniBig devices."""

    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        entry: MiniBigConfigEntry,
        coordinator: MiniBigActiveCoordinator,
        battery_dp: int,
    ) -> None:
        """Initialize battery sensor."""
        super().__init__(entry, coordinator, "battery", "battery")
        self._battery_dp = battery_dp

    @property
    def native_value(self) -> int | None:
        """Return the battery percentage."""
        dps = self.coordinator.data or {}
        val = dps.get(self._battery_dp)
        if val is not None:
            return max(0, min(100, val))
        return None


class MiniBigRssiSensor(MiniBigBaseSensor):
    """Bluetooth signal strength (RSSI) sensor."""

    _attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
    _attr_native_unit_of_measurement = SIGNAL_STRENGTH_DECIBELS_MILLIWATT
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        entry: MiniBigConfigEntry,
        coordinator: MiniBigPassiveBluetoothProcessorCoordinator,
    ) -> None:
        """Initialize RSSI sensor."""
        super().__init__(entry, coordinator, "rssi", "rssi")

    @property
    def available(self) -> bool:
        """Return False once the device stops being seen by any scanner.

        RSSI only means something for a device currently in range; keeping the
        last received value on display would present a device that vanished
        hours ago as if it were still there.
        """
        return self.coordinator.available

    @property
    def native_value(self) -> int | None:
        """Return the RSSI value."""
        if self.coordinator.last_device_info:
            return self.coordinator.last_device_info.rssi
        return None


class MiniBigLastStatusSensor(MiniBigBaseSensor):
    """Diagnostic sensor for last GATT response status."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        entry: MiniBigConfigEntry,
        coordinator: MiniBigActiveCoordinator,
    ) -> None:
        """Initialize last status sensor."""
        super().__init__(entry, coordinator, "last_status", "last_status")

    @property
    def native_value(self) -> str | None:
        """Return last status text or code."""
        status = self.entry.runtime_data.connection.last_status
        if status is not None:
            return STATUS_MESSAGES.get(status, f"Code {status}")
        return None


class MiniBigSessionReportSensor(MiniBigBaseSensor):
    """Base for diagnostics that publish the connection session reports.

    Always available: these exist to be read when the device is out of range
    or a command just failed, which is exactly when the coordinator is not
    healthy. They refresh on every filed report, not only on coordinator
    updates.
    """

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        entry: MiniBigConfigEntry,
        coordinator: MiniBigActiveCoordinator,
        key: str,
    ) -> None:
        """Initialize the session report sensor."""
        super().__init__(entry, coordinator, key, key)
        self._remove_report_listener: Callable[[], None] | None = None

    @property
    def _reports(self):
        """Return the connection session reports."""
        return self.entry.runtime_data.connection.reports

    @property
    def available(self) -> bool:
        """Return True: a diagnostic about failures must outlive them."""
        return True

    async def async_added_to_hass(self) -> None:
        """Refresh whenever a session report is filed."""
        await super().async_added_to_hass()
        self._remove_report_listener = self._reports.add_listener(self._handle_report)

    async def async_will_remove_from_hass(self) -> None:
        """Stop listening for session reports."""
        if self._remove_report_listener is not None:
            self._remove_report_listener()
            self._remove_report_listener = None
        await super().async_will_remove_from_hass()

    @callback
    def _handle_report(self) -> None:
        """Handle a newly filed session report."""
        self.async_write_ha_state()

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the breakdown of the session that last failed.

        Kept until the next failure, so a later success does not erase the
        evidence. Polls that never connected are not filed at all.
        """
        return self._reports.last_failure


class MiniBigLastFailureSensor(MiniBigSessionReportSensor):
    """When a BLE command last failed, with that session breakdown."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, entry: MiniBigConfigEntry, coordinator: MiniBigActiveCoordinator) -> None:
        """Initialize last failure sensor."""
        super().__init__(entry, coordinator, "last_failure")

    @property
    def native_value(self) -> datetime | None:
        """Return when the last failure happened."""
        return self._reports.last_failure_at


class MiniBigLastErrorSensor(MiniBigSessionReportSensor):
    """The text of the last BLE command failure."""

    # Home Assistant caps a state at 255 characters.
    MAX_LENGTH = 255

    def __init__(self, entry: MiniBigConfigEntry, coordinator: MiniBigActiveCoordinator) -> None:
        """Initialize last error sensor."""
        super().__init__(entry, coordinator, "last_error")

    @property
    def native_value(self) -> str | None:
        """Return the last error message, shortened to fit a state."""
        failure = self._reports.last_failure
        if not failure:
            return None
        error = str(failure.get("error") or "")
        return error[: self.MAX_LENGTH] or None


class MiniBigErrorCountSensor(MiniBigSessionReportSensor):
    """How many BLE commands have failed since this entry was loaded.

    Starts over on every reload or when the clear button is pressed, so it is
    not a long-term statistic.
    """

    def __init__(self, entry: MiniBigConfigEntry, coordinator: MiniBigActiveCoordinator) -> None:
        """Initialize error count sensor."""
        super().__init__(entry, coordinator, "error_count")

    @property
    def native_value(self) -> int:
        """Return the number of failed commands."""
        return self._reports.failures

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """The count carries no breakdown; Last Failure does."""
        return None
