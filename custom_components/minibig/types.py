"""Type definitions for the MiniBig integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry

if TYPE_CHECKING:
    from .coordinator import (
        MiniBigActiveCoordinator,
        MiniBigPassiveBluetoothProcessorCoordinator,
    )
    from .minibig_ble import DeviceProfile, MiniBigConnection, MiniBigDeviceInfo


@dataclass
class MiniBigData:
    """Runtime data stored in config entry."""

    device_info: MiniBigDeviceInfo
    profile: DeviceProfile
    connection: MiniBigConnection
    passive_coordinator: MiniBigPassiveBluetoothProcessorCoordinator
    active_coordinator: MiniBigActiveCoordinator


MiniBigConfigEntry = ConfigEntry[MiniBigData]
