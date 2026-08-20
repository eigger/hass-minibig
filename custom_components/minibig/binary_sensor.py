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
        MiniBigInRangeBinarySensor(entry, data.passive_coordinator),
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
    """Binary sensor indicating whether a BLE link to the device is established.

    Deliberately reports the live GATT link state and not advertisement
    presence: the passive coordinator's `available` only says "an
    advertisement was seen recently", which stays True while the device is
    merely in range - and, worse, never notified these entities when it
    flipped back to False, so the sensor could sit at "Connected" with no
    connection (and no usable adapter) at all.
    """

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        entry: MiniBigConfigEntry,
        coordinator: MiniBigPassiveBluetoothProcessorCoordinator,
    ) -> None:
        """Initialize connectivity binary sensor."""
        super().__init__(entry, coordinator, "connectivity", "connectivity")
        self._unsub_connection = None

    async def async_added_to_hass(self) -> None:
        """Register link state callback."""
        await super().async_added_to_hass()
        self._unsub_connection = self.entry.runtime_data.connection.register_connection_callback(
            self._handle_connection_update
        )

    async def async_will_remove_from_hass(self) -> None:
        """Unregister callback."""
        if self._unsub_connection:
            self._unsub_connection()
            self._unsub_connection = None
        await super().async_will_remove_from_hass()

    @callback
    def _handle_connection_update(self, connected: bool) -> None:
        """Handle updated link state."""
        self.async_write_ha_state()

    @property
    def is_on(self) -> bool:
        """Return True while a GATT link to the device is established."""
        return self.entry.runtime_data.connection.is_connected


class MiniBigInRangeBinarySensor(MiniBigBaseBinarySensor):
    """Binary sensor indicating the device is currently advertising in range.

    This is the advertisement-presence signal the connectivity entity used to
    report. It is kept as its own entity because the two answer different
    questions: this one says the device is nearby and reachable, while
    connectivity says a GATT link is actually open right now. Deliberately has
    no `available` override - "not seen by any scanner" is exactly the state
    this entity exists to report, so it must stay available to report it.
    """

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        entry: MiniBigConfigEntry,
        coordinator: MiniBigPassiveBluetoothProcessorCoordinator,
    ) -> None:
        """Initialize in-range binary sensor."""
        super().__init__(entry, coordinator, "in_range", "in_range")

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
    def available(self) -> bool:
        """Return False once the device stops being seen by any scanner.

        Pairing mode is read out of the advertisement, so without a current
        advertisement there is nothing to report - showing the last known
        value would claim knowledge about a device that is no longer visible.
        """
        return self.coordinator.available

    @property
    def is_on(self) -> bool:
        """Return True if init mode is active."""
        if self.coordinator.last_device_info:
            return self.coordinator.last_device_info.init_mode
        return False
