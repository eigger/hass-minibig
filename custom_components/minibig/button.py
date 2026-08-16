"""Button platform for the MiniBig integration."""

from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_DP_OVERRIDES, DOMAIN
from .coordinator import MiniBigActiveCoordinator
from .minibig_ble import (
    SLOT_MEASURE,
    SLOT_MEASURE_STOP,
    SLOT_PAIR_EMITTER,
    SLOT_UNPAIR_EMITTER,
    MiniBigSupersededError,
    resolve_dp,
)
from .types import MiniBigConfigEntry

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MiniBigConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up MiniBig button entities from config entry."""
    data = entry.runtime_data
    entities: list[ButtonEntity] = [
        MiniBigRestartButton(entry, data.active_coordinator),
        MiniBigRefreshButton(entry, data.active_coordinator),
        MiniBigFactoryResetButton(entry, data.active_coordinator),
    ]

    # Device-side operations. Each needs its DP ID; unknown slots stay unexposed.
    overrides = entry.options.get(CONF_DP_OVERRIDES) or {}
    for slot in (SLOT_MEASURE, SLOT_MEASURE_STOP, SLOT_PAIR_EMITTER, SLOT_UNPAIR_EMITTER):
        dp_id = resolve_dp(data.profile, slot, overrides)
        if dp_id is not None:
            entities.append(
                MiniBigDpActionButton(entry, data.active_coordinator, slot, dp_id)
            )

    async_add_entities(entities)


class MiniBigBaseButton(CoordinatorEntity[MiniBigActiveCoordinator], ButtonEntity):
    """Base class for MiniBig button entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        entry: MiniBigConfigEntry,
        coordinator: MiniBigActiveCoordinator,
        key: str,
        translation_key: str,
    ) -> None:
        """Initialize button entity."""
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.unique_id}_{key}"
        self._attr_translation_key = translation_key
        address = entry.runtime_data.device_info.address
        self._attr_device_info = DeviceInfo(
            connections={(CONNECTION_BLUETOOTH, address)},
            identifiers={(DOMAIN, address)},
        )


class MiniBigRestartButton(MiniBigBaseButton):
    """Button to restart the MiniBig device."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self, entry: MiniBigConfigEntry, coordinator: MiniBigActiveCoordinator
    ) -> None:
        """Initialize restart button."""
        super().__init__(entry, coordinator, "restart", "restart")

    async def async_press(self) -> None:
        """Handle button press to restart device."""
        try:
            await self.entry.runtime_data.connection.restart()
        except Exception as err:
            raise HomeAssistantError(f"Failed to restart MiniBig device: {err}") from err


class MiniBigRefreshButton(MiniBigBaseButton):
    """Button to manually refresh device state."""

    def __init__(
        self, entry: MiniBigConfigEntry, coordinator: MiniBigActiveCoordinator
    ) -> None:
        """Initialize refresh button."""
        super().__init__(entry, coordinator, "refresh", "refresh")

    async def async_press(self) -> None:
        """Handle button press to refresh device state."""
        try:
            await self.coordinator.async_request_refresh()
        except Exception as err:
            raise HomeAssistantError(f"Failed to refresh MiniBig device: {err}") from err


class MiniBigFactoryResetButton(MiniBigBaseButton):
    """Button to factory reset the MiniBig device."""

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self, entry: MiniBigConfigEntry, coordinator: MiniBigActiveCoordinator
    ) -> None:
        """Initialize factory reset button."""
        super().__init__(entry, coordinator, "factory_reset", "factory_reset")

    async def async_press(self) -> None:
        """Handle button press to reset device to factory settings."""
        try:
            await self.entry.runtime_data.connection.factory_reset()
        except Exception as err:
            raise HomeAssistantError(f"Failed to factory reset MiniBig device: {err}") from err


class MiniBigDpActionButton(MiniBigBaseButton):
    """One-shot device operation triggered by writing a single DP."""

    _attr_entity_category = EntityCategory.CONFIG

    # TODO(measure): the trigger value is assumed to be 1. Confirm against a real
    # capture; the stop DP for covers uses 0, so this may differ per operation.
    TRIGGER_VALUE = 1

    def __init__(
        self,
        entry: MiniBigConfigEntry,
        coordinator: MiniBigActiveCoordinator,
        slot: str,
        dp_id: int,
    ) -> None:
        """Initialize the action button."""
        super().__init__(entry, coordinator, slot, slot)
        self._slot = slot
        self._dp_id = dp_id

    async def async_press(self) -> None:
        """Trigger the device operation."""
        try:
            await self.entry.runtime_data.connection.send_dps(
                [(self._dp_id, self.TRIGGER_VALUE)]
            )
        except MiniBigSupersededError:
            return
        except Exception as err:
            raise HomeAssistantError(f"Failed to run {self._slot}: {err}") from err
