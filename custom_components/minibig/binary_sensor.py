"""Binary sensor platform for the MiniBig integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import MiniBigActiveCoordinator, MiniBigPassiveBluetoothProcessorCoordinator
from .types import MiniBigConfigEntry

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MiniBigConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up MiniBig binary sensor entities from config entry."""
    data = entry.runtime_data
    entities: list[BinarySensorEntity] = [
        MiniBigMovingBinarySensor(entry, data.active_coordinator),
        MiniBigConnectivityBinarySensor(entry, data.passive_coordinator),
        MiniBigInitModeBinarySensor(entry, data.passive_coordinator),
    ]
    async_add_entities(entities)


class MiniBigBaseBinarySensor(CoordinatorEntity[Any], BinarySensorEntity):
    """Base class for MiniBig binary sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        entry: MiniBigConfigEntry,
        coordinator: Any,
        key: str,
        translation_key: str,
    ) -> None:
        """Initialize binary sensor entity."""
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.unique_id}_{key}"
        self._attr_translation_key = translation_key
        address = entry.runtime_data.device_info.address
        self._attr_device_info = DeviceInfo(
            connections={(CONNECTION_BLUETOOTH, address)},
            identifiers={(DOMAIN, address)},
        )


class MiniBigMovingBinarySensor(MiniBigBaseBinarySensor):
    """Binary sensor indicating if the device is actively moving."""

    _attr_device_class = BinarySensorDeviceClass.MOVING

    def __init__(
        self,
        entry: MiniBigConfigEntry,
        coordinator: MiniBigActiveCoordinator,
    ) -> None:
        """Initialize moving binary sensor."""
        super().__init__(entry, coordinator, "moving", "moving")
        self._unsub_movement = None

    async def async_added_to_hass(self) -> None:
        """Register movement state callback."""
        await super().async_added_to_hass()
        self._unsub_movement = self.entry.runtime_data.connection.register_movement_callback(
            self._handle_movement_update
        )

    async def async_will_remove_from_hass(self) -> None:
        """Unregister callback."""
        if self._unsub_movement:
            self._unsub_movement()
            self._unsub_movement = None
        await super().async_will_remove_from_hass()

    @callback
    def _handle_movement_update(self, moving: bool) -> None:
        """Handle updated movement state."""
        self.async_write_ha_state()

    @property
    def is_on(self) -> bool:
        """Return True if device is moving."""
        return self.entry.runtime_data.connection.is_moving


class MiniBigConnectivityBinarySensor(MiniBigBaseBinarySensor):
    """Binary sensor indicating connectivity based on recent advertisements."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        entry: MiniBigConfigEntry,
        coordinator: MiniBigPassiveBluetoothProcessorCoordinator,
    ) -> None:
        """Initialize connectivity binary sensor."""
        super().__init__(entry, coordinator, "connectivity", "connectivity")

    @property
    def is_on(self) -> bool:
        """Return True if advertisements were received recently."""
        return self.coordinator.available


class MiniBigInitModeBinarySensor(MiniBigBaseBinarySensor):
    """Binary sensor indicating if device is in pairing / init mode."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        entry: MiniBigConfigEntry,
        coordinator: MiniBigPassiveBluetoothProcessorCoordinator,
    ) -> None:
        """Initialize init mode binary sensor."""
        super().__init__(entry, coordinator, "init_mode", "init_mode")

    @property
    def is_on(self) -> bool:
        """Return True if init mode is active."""
        if self.coordinator.last_device_info:
            return self.coordinator.last_device_info.init_mode
        return False
