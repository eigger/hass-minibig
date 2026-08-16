"""Switch platform for MiniBig Push/Switch devices."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_POWER_DP_ID, DOMAIN
from .coordinator import MiniBigActiveCoordinator
from .minibig_ble import MiniBigSupersededError
from .types import MiniBigConfigEntry

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MiniBigConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up MiniBig switch entities from config entry."""
    data = entry.runtime_data
    power_dp = entry.options.get(CONF_POWER_DP_ID, data.profile.dp_power)
    if "switch" in data.profile.platforms or power_dp is not None:
        async_add_entities([MiniBigPowerSwitch(entry, data.active_coordinator, power_dp)])


class MiniBigPowerSwitch(CoordinatorEntity[MiniBigActiveCoordinator], SwitchEntity):
    """Switch entity representing power / button press on MiniBig devices."""

    _attr_has_entity_name = True
    _attr_translation_key = "power"

    def __init__(
        self,
        entry: MiniBigConfigEntry,
        coordinator: MiniBigActiveCoordinator,
        power_dp: int | None,
    ) -> None:
        """Initialize the switch entity."""
        super().__init__(coordinator)
        self.entry = entry
        self._power_dp = power_dp
        self._attr_unique_id = f"{entry.unique_id}_switch"

        address = entry.runtime_data.device_info.address
        self._attr_device_info = DeviceInfo(
            connections={(CONNECTION_BLUETOOTH, address)},
            identifiers={(DOMAIN, address)},
        )
        self._optimistic_state: bool | None = None

    @property
    def available(self) -> bool:
        """Return True if entity is available and power DP is known."""
        if self._power_dp is None:
            return False
        return super().available

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        dps = self.coordinator.data or {}
        if self._power_dp is not None and self._power_dp in dps:
            # Sync state with readback value and clear optimistic assumption
            self._optimistic_state = None
        super()._handle_coordinator_update()

    @property
    def is_on(self) -> bool | None:
        """Return True if switch is on."""
        if self._optimistic_state is not None:
            return self._optimistic_state
        dps = self.coordinator.data or {}
        if self._power_dp is not None and self._power_dp in dps:
            return bool(dps[self._power_dp])
        return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn switch on."""
        if self._power_dp is None:
            raise HomeAssistantError("Power DP ID is not configured")

        self._optimistic_state = True
        self.async_write_ha_state()

        try:
            await self.entry.runtime_data.connection.send_dps([(self._power_dp, 1)])
        except MiniBigSupersededError:
            self._optimistic_state = None
            self.async_write_ha_state()
        except Exception as err:
            self._optimistic_state = None
            self.async_write_ha_state()
            raise HomeAssistantError(f"Failed to turn on {self.name}: {err}") from err

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn switch off."""
        if self._power_dp is None:
            raise HomeAssistantError("Power DP ID is not configured")

        self._optimistic_state = False
        self.async_write_ha_state()

        try:
            await self.entry.runtime_data.connection.send_dps([(self._power_dp, 0)])
        except MiniBigSupersededError:
            self._optimistic_state = None
            self.async_write_ha_state()
        except Exception as err:
            self._optimistic_state = None
            self.async_write_ha_state()
            raise HomeAssistantError(f"Failed to turn off {self.name}: {err}") from err
