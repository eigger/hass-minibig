"""Sensor platform for the MiniBig integration."""

from __future__ import annotations

import logging
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
from homeassistant.core import HomeAssistant
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
