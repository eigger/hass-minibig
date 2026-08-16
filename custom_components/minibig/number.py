"""Number platform for MiniBig numeric device settings."""

from __future__ import annotations

import logging

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_DP_OVERRIDES, DOMAIN
from .coordinator import MiniBigActiveCoordinator
from .minibig_ble import (
    SLOT_INSTALL_POSITION,
    SLOT_LENGTH,
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
    """Set up MiniBig number entities for known numeric settings."""
    data = entry.runtime_data
    overrides = entry.options.get(CONF_DP_OVERRIDES) or {}
    profile = data.profile

    numeric_slots = (
        (SLOT_LENGTH, profile.length_max),
        (SLOT_INSTALL_POSITION, profile.install_position_max),
    )

    entities: list[NumberEntity] = []
    for slot, max_value in numeric_slots:
        dp_id = resolve_dp(profile, slot, overrides)
        if dp_id is None:
            continue
        entities.append(
            MiniBigSettingNumber(entry, data.active_coordinator, slot, dp_id, max_value)
        )

    async_add_entities(entities)


class MiniBigSettingNumber(CoordinatorEntity[MiniBigActiveCoordinator], NumberEntity):
    """A numeric device setting backed by a single DP."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_mode = NumberMode.BOX
    _attr_native_min_value = 0
    _attr_native_step = 1

    def __init__(
        self,
        entry: MiniBigConfigEntry,
        coordinator: MiniBigActiveCoordinator,
        slot: str,
        dp_id: int,
        max_value: int,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self.entry = entry
        self._slot = slot
        self._dp_id = dp_id
        self._attr_native_max_value = max_value
        self._attr_unique_id = f"{entry.unique_id}_{slot}"
        self._attr_translation_key = slot

        address = entry.runtime_data.device_info.address
        self._attr_device_info = DeviceInfo(
            connections={(CONNECTION_BLUETOOTH, address)},
            identifiers={(DOMAIN, address)},
        )

    @property
    def native_value(self) -> float | None:
        """Return the value last reported by the device."""
        raw = (self.coordinator.data or {}).get(self._dp_id)
        return None if raw is None else float(raw)

    async def async_set_native_value(self, value: float) -> None:
        """Write the value to the device."""
        raw = max(0, min(int(self._attr_native_max_value), int(value)))
        try:
            await self.entry.runtime_data.connection.send_dps([(self._dp_id, raw)])
        except MiniBigSupersededError:
            return
        except Exception as err:
            raise HomeAssistantError(
                f"Failed to set {self._slot} to {raw}: {err}"
            ) from err
