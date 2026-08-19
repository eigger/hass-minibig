"""Cover platform for MiniBig Window Opener."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.cover import (
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_POSITION_DP_ID,
    DEFAULT_STOP_DP,
    DOMAIN,
)
from .coordinator import MiniBigActiveCoordinator
from .minibig_ble import MiniBigSupersededError
from .types import MiniBigConfigEntry

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MiniBigConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up MiniBig cover entities from config entry."""
    data = entry.runtime_data
    pos_dp = entry.options.get(CONF_POSITION_DP_ID, data.profile.dp_position)
    if "cover" in data.profile.platforms or pos_dp is not None:
        stop_dp = data.profile.dp_stop if data.profile.dp_stop is not None else DEFAULT_STOP_DP
        async_add_entities([MiniBigWindowOpenerCover(entry, data.active_coordinator, pos_dp, stop_dp)])


class MiniBigWindowOpenerCover(
    CoordinatorEntity[MiniBigActiveCoordinator],
    CoverEntity,
    RestoreEntity,
):
    """Cover entity representing a MiniBig BLE Window Opener."""

    _attr_has_entity_name = True
    _attr_supported_features = (
        CoverEntityFeature.OPEN
        | CoverEntityFeature.CLOSE
        | CoverEntityFeature.STOP
        | CoverEntityFeature.SET_POSITION
    )

    def __init__(
        self,
        entry: MiniBigConfigEntry,
        coordinator: MiniBigActiveCoordinator,
        pos_dp: int | None,
        stop_dp: int,
    ) -> None:
        """Initialize the cover entity."""
        super().__init__(coordinator)
        self.entry = entry
        self._pos_dp = pos_dp
        self._stop_dp = stop_dp
        self._attr_unique_id = f"{entry.unique_id}_cover"
        self._attr_translation_key = "window_opener"

        name_lower = entry.runtime_data.device_info.name.lower()
        if "curtain" in name_lower or name_lower.startswith("clwm"):
            self._attr_device_class = CoverDeviceClass.CURTAIN
        elif "blind" in name_lower:
            self._attr_device_class = CoverDeviceClass.BLIND
        elif "garage" in name_lower:
            self._attr_device_class = CoverDeviceClass.GARAGE
        else:
            self._attr_device_class = CoverDeviceClass.WINDOW

        address = entry.runtime_data.device_info.address
        self._attr_device_info = DeviceInfo(
            connections={(CONNECTION_BLUETOOTH, address)},
            identifiers={(DOMAIN, address)},
        )

        self._last_known_position: int | None = None
        self._previous_position: int | None = None
        self._target_position: int | None = None
        self._unsub_movement = None

    @property
    def available(self) -> bool:
        """Return True if entity is available and position DP is known."""
        if self._pos_dp is None:
            return False
        return super().available

    async def async_added_to_hass(self) -> None:
        """Restore previous state and subscribe to movement events."""
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state and last_state.attributes.get("current_position") is not None:
            try:
                self._last_known_position = int(last_state.attributes["current_position"])
            except (ValueError, TypeError):
                pass

        self._unsub_movement = self.entry.runtime_data.connection.register_movement_callback(
            self._handle_movement_update
        )

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe listeners on removal."""
        if self._unsub_movement:
            self._unsub_movement()
            self._unsub_movement = None
        await super().async_will_remove_from_hass()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        dps = self.coordinator.data or {}
        if self._pos_dp is not None and self._pos_dp in dps:
            raw = dps[self._pos_dp]
            pos = self._normalize_position(raw)
            if self._last_known_position is not None and pos != self._last_known_position:
                self._previous_position = self._last_known_position
            self._last_known_position = pos
        super()._handle_coordinator_update()

    @callback
    def _handle_movement_update(self, moving: bool) -> None:
        """Handle movement state changes."""
        if not moving:
            self._target_position = None
        self.async_write_ha_state()

    def _normalize_position(self, raw_val: int) -> int:
        """Clamp dp0 to a valid 0-100 range without altering the value itself.

        Earlier versions snapped values near the ends (<=2 -> 0, >=98 -> 100),
        assuming the motor stops just short of its mechanical limits like the
        reference implementation's window opener. Real hardware disproved
        that for this device: a position confirmed as 97% in the official
        vendor app was previously being snapped to 100% here, silently
        disagreeing with the app's own reading. dp0 is passed through as-is;
        only out-of-range values (e.g. a bad read) are clamped.
        """
        return max(0, min(100, raw_val))

    @property
    def current_cover_position(self) -> int | None:
        """Return current cover position (0=closed, 100=open)."""
        return self._last_known_position

    @property
    def is_closed(self) -> bool | None:
        """Return True if cover is fully closed."""
        pos = self.current_cover_position
        if pos is not None:
            return pos == 0
        return None

    @property
    def is_opening(self) -> bool:
        """Return True if cover is actively opening."""
        if not self.entry.runtime_data.connection.is_moving:
            return False
        if self._target_position is not None and self._last_known_position is not None:
            return self._target_position > self._last_known_position
        if self._previous_position is not None and self._last_known_position is not None:
            return self._last_known_position > self._previous_position
        return False

    @property
    def is_closing(self) -> bool:
        """Return True if cover is actively closing."""
        if not self.entry.runtime_data.connection.is_moving:
            return False
        if self._target_position is not None and self._last_known_position is not None:
            return self._target_position < self._last_known_position
        if self._previous_position is not None and self._last_known_position is not None:
            return self._last_known_position < self._previous_position
        return False

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Move cover to a target position (0..100%)."""
        if self._pos_dp is None:
            raise HomeAssistantError("Position DP ID is not configured")

        position: int = kwargs["position"]
        target = max(0, min(100, position))
        self._target_position = target
        self.async_write_ha_state()

        try:
            await self.entry.runtime_data.connection.send_dps([(self._pos_dp, target)])
        except MiniBigSupersededError:
            # Superseded by a newer position/stop command: clear stale target and exit cleanly
            self._target_position = None
            self.async_write_ha_state()
        except Exception as err:
            self._target_position = None
            self.async_write_ha_state()
            raise HomeAssistantError(f"Failed to set cover position to {target}%: {err}") from err

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open cover fully (100%)."""
        await self.async_set_cover_position(position=100)

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close cover fully (0%)."""
        await self.async_set_cover_position(position=0)

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop cover movement immediately."""
        self._target_position = None
        self.async_write_ha_state()

        try:
            await self.entry.runtime_data.connection.send_dps([(self._stop_dp, 0)])
        except MiniBigSupersededError:
            self._target_position = None
            self.async_write_ha_state()
        except Exception as err:
            raise HomeAssistantError(f"Failed to stop cover: {err}") from err
