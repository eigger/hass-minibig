"""Select platform for MiniBig device settings."""

from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_DP_OVERRIDES, DOMAIN
from .coordinator import MiniBigActiveCoordinator
from .minibig_ble import (
    SLOT_CURTAIN_TYPE,
    SLOT_DIRECTION,
    SLOT_INSTALL_TYPE,
    SLOT_MODE,
    MiniBigSupersededError,
    resolve_dp,
)
from .types import MiniBigConfigEntry

_LOGGER = logging.getLogger(__name__)

CHOICE_SLOTS = (SLOT_INSTALL_TYPE, SLOT_CURTAIN_TYPE, SLOT_DIRECTION, SLOT_MODE)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MiniBigConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up MiniBig select entities for known choice settings."""
    data = entry.runtime_data
    overrides = entry.options.get(CONF_DP_OVERRIDES) or {}

    entities: list[SelectEntity] = []
    for slot in CHOICE_SLOTS:
        dp_id = resolve_dp(data.profile, slot, overrides)
        options = data.profile.options_for(slot)
        # Both the DP ID and its raw value map must be known; otherwise the
        # setting stays unexposed rather than guessing a value to write.
        if dp_id is None or not options:
            continue
        entities.append(
            MiniBigChoiceSelect(entry, data.active_coordinator, slot, dp_id, options)
        )

    async_add_entities(entities)


class MiniBigChoiceSelect(CoordinatorEntity[MiniBigActiveCoordinator], SelectEntity):
    """A device setting exposed as a fixed set of choices backed by one DP."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        entry: MiniBigConfigEntry,
        coordinator: MiniBigActiveCoordinator,
        slot: str,
        dp_id: int,
        options: dict[str, int],
    ) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)
        self.entry = entry
        self._slot = slot
        self._dp_id = dp_id
        self._options = dict(options)
        self._reverse = {value: label for label, value in options.items()}
        self._attr_options = list(options)
        self._attr_unique_id = f"{entry.unique_id}_{slot}"
        self._attr_translation_key = slot

        address = entry.runtime_data.device_info.address
        self._attr_device_info = DeviceInfo(
            connections={(CONNECTION_BLUETOOTH, address)},
            identifiers={(DOMAIN, address)},
        )

    @property
    def current_option(self) -> str | None:
        """Return the currently selected option, if the device reported it."""
        raw = (self.coordinator.data or {}).get(self._dp_id)
        if raw is None:
            return None
        return self._reverse.get(raw)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Log values the profile does not have a label for."""
        raw = (self.coordinator.data or {}).get(self._dp_id)
        if raw is not None and raw not in self._reverse:
            _LOGGER.debug(
                "Unmapped value %s on DP %s (%s) for %s",
                raw,
                self._dp_id,
                self._slot,
                self.entry.unique_id,
            )
        super()._handle_coordinator_update()

    async def async_select_option(self, option: str) -> None:
        """Write the selected option to the device."""
        value = self._options.get(option)
        if value is None:
            raise HomeAssistantError(f"Unknown option '{option}' for {self._slot}")
        try:
            await self.entry.runtime_data.connection.send_dps([(self._dp_id, value)])
        except MiniBigSupersededError:
            return
        except Exception as err:
            raise HomeAssistantError(
                f"Failed to set {self._slot} to '{option}': {err}"
            ) from err
