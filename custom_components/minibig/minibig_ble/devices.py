"""Device profiles and capability mappings for MiniBig BLE devices."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
import logging
from typing import Any

from .parser import MiniBigDeviceInfo

_LOGGER = logging.getLogger(__name__)

# Named DP slots. Resolved from the device profile, overridable per config entry.
SLOT_POSITION = "position"
SLOT_STOP = "stop"
SLOT_POWER = "power"
SLOT_BATTERY = "battery"
SLOT_MEASURE = "measure"
SLOT_MEASURE_STOP = "measure_stop"
SLOT_PAIR_EMITTER = "pair_emitter"
SLOT_UNPAIR_EMITTER = "unpair_emitter"
SLOT_INSTALL_TYPE = "install_type"
SLOT_CURTAIN_TYPE = "curtain_type"
SLOT_DIRECTION = "direction"
SLOT_MODE = "mode"
SLOT_LENGTH = "length"
SLOT_INSTALL_POSITION = "install_position"

ALL_SLOTS = (
    SLOT_POSITION,
    SLOT_STOP,
    SLOT_POWER,
    SLOT_BATTERY,
    SLOT_MEASURE,
    SLOT_MEASURE_STOP,
    SLOT_PAIR_EMITTER,
    SLOT_UNPAIR_EMITTER,
    SLOT_INSTALL_TYPE,
    SLOT_CURTAIN_TYPE,
    SLOT_DIRECTION,
    SLOT_MODE,
    SLOT_LENGTH,
    SLOT_INSTALL_POSITION,
)

# DP code names for the device operations behind each slot. The numeric DP IDs are
# provisioned per product, so these names are what a captured mapping is matched
# against when filling in the dp_* fields below.
SLOT_DP_CODES: dict[str, str] = {
    SLOT_MEASURE: "measureMode",
    SLOT_MEASURE_STOP: "measureEnable",
    SLOT_PAIR_EMITTER: "pair_emitter",
    SLOT_UNPAIR_EMITTER: "pair_emitter_state",
    SLOT_DIRECTION: "control_back",
}

# The travel-limit DP takes enumerated string values rather than a number. The
# integer each enum maps to is provisioned per product, so it cannot be sent until
# that mapping is known.
LIMIT_DP_CODE = "limit_set_del"
LIMIT_VALUE_LABELS = (
    "limit_set_up",
    "limit_set_down",
    "limit_del_up",
    "limit_del_down",
)

# Choice labels observed for the settings above. The raw DP values behind
# them are NOT known, so each profile must supply its own label -> value map
# before a select entity is created.
INSTALL_TYPE_LABELS = ("window", "curtain", "blind")
CURTAIN_TYPE_LABELS = ("oneside", "both")
DIRECTION_LABELS = ("left", "right")


@dataclass(frozen=True)
class DeviceProfile:
    """Capability and platform profile for a MiniBig device."""

    model_name: str
    manufacturer: str = "MiniBig"
    platforms: list[str] = field(
        default_factory=lambda: ["sensor", "binary_sensor", "button"]
    )
    refresh_strategy: str = "read_dps"  # "dp3", "read_dps", "read_setting", "none"
    dp_position: int | None = None
    dp_stop: int | None = None
    dp_power: int | None = None
    dp_battery: int | None = 10

    # Device-side operations found in the vendor app (device_wm_* / device_blind_*).
    # TODO(measure): DP IDs unknown until captured from real hardware. Entities are
    # only created for non-None slots, so leaving these unset changes nothing.
    dp_measure: int | None = None
    dp_measure_stop: int | None = None
    dp_pair_emitter: int | None = None
    dp_unpair_emitter: int | None = None
    dp_install_type: int | None = None
    dp_curtain_type: int | None = None
    dp_direction: int | None = None
    dp_mode: int | None = None
    dp_length: int | None = None
    dp_install_position: int | None = None

    # Label -> raw DP value maps for the choice settings above. A select entity is
    # only created when BOTH the DP ID and its option map are known, so no guessed
    # enum value is ever written to a device.
    # TODO(measure): populate together with the matching dp_* slot.
    install_type_options: dict[str, int] | None = None
    curtain_type_options: dict[str, int] | None = None
    direction_options: dict[str, int] | None = None
    mode_options: dict[str, int] | None = None

    # Bounds for the numeric settings, used by the number entities.
    length_max: int = 1000
    install_position_max: int = 100

    is_supported: bool = True

    @property
    def slot_map(self) -> dict[str, int | None]:
        """Return the named DP slot to DP ID mapping for this profile."""
        return {
            SLOT_POSITION: self.dp_position,
            SLOT_STOP: self.dp_stop,
            SLOT_POWER: self.dp_power,
            SLOT_BATTERY: self.dp_battery,
            SLOT_MEASURE: self.dp_measure,
            SLOT_MEASURE_STOP: self.dp_measure_stop,
            SLOT_PAIR_EMITTER: self.dp_pair_emitter,
            SLOT_UNPAIR_EMITTER: self.dp_unpair_emitter,
            SLOT_INSTALL_TYPE: self.dp_install_type,
            SLOT_CURTAIN_TYPE: self.dp_curtain_type,
            SLOT_DIRECTION: self.dp_direction,
            SLOT_MODE: self.dp_mode,
            SLOT_LENGTH: self.dp_length,
            SLOT_INSTALL_POSITION: self.dp_install_position,
        }

    def options_for(self, slot: str) -> dict[str, int] | None:
        """Return the label -> raw value map for a choice slot, if known."""
        return {
            SLOT_INSTALL_TYPE: self.install_type_options,
            SLOT_CURTAIN_TYPE: self.curtain_type_options,
            SLOT_DIRECTION: self.direction_options,
            SLOT_MODE: self.mode_options,
        }.get(slot)

    @property
    def known_dps(self) -> set[int]:
        """Return set of known DP IDs for this profile."""
        return {dp_id for dp_id in self.slot_map.values() if dp_id is not None}


def resolve_dp(
    profile: DeviceProfile,
    slot: str,
    overrides: Mapping[str, Any] | None = None,
) -> int | None:
    """Resolve a named DP slot, letting a config entry override the profile value."""
    if overrides:
        raw = overrides.get(slot)
        if raw is not None:
            try:
                return int(raw)
            except (TypeError, ValueError):
                _LOGGER.warning("Ignoring invalid DP override for slot '%s': %r", slot, raw)
    return profile.slot_map.get(slot)


PROFILE_WINDOW_OPENER = DeviceProfile(
    model_name="Window Opener",
    manufacturer="MiniBig",
    platforms=["cover", "sensor", "binary_sensor", "button"],
    refresh_strategy="dp3",
    dp_position=0,
    dp_stop=3,
    dp_battery=10,
    is_supported=True,
)

PROFILE_PUSH_MINI_NEW = DeviceProfile(
    model_name="PushMini",
    manufacturer="MiniBig",
    platforms=["switch", "sensor", "binary_sensor", "button"],
    refresh_strategy="read_dps",
    dp_power=0,
    dp_battery=10,
    is_supported=True,
)

PROFILE_PUSH_MINI_LEGACY = DeviceProfile(
    model_name="PushMini (Legacy)",
    manufacturer="MiniBig",
    platforms=["switch", "sensor", "binary_sensor", "button"],
    refresh_strategy="read_setting",
    dp_power=0,
    dp_battery=None,
    is_supported=True,
)

PROFILE_SWITCH_MINI = DeviceProfile(
    model_name="SwitchMini",
    manufacturer="MiniBig",
    platforms=["switch", "sensor", "binary_sensor", "button"],
    refresh_strategy="read_dps",
    dp_power=None,  # Configured via options if custom
    dp_battery=10,
    is_supported=True,
)

PROFILE_HUB_MINI = DeviceProfile(
    model_name="HubMini (Unsupported)",
    manufacturer="MiniBig",
    platforms=[],
    refresh_strategy="none",
    is_supported=False,
)

PROFILE_UNKNOWN = DeviceProfile(
    model_name="Unknown MiniBig Device",
    manufacturer="MiniBig",
    platforms=["sensor", "binary_sensor", "button"],
    refresh_strategy="read_dps",
    dp_position=None,
    dp_stop=None,
    dp_power=None,
    dp_battery=10,
    is_supported=True,
)


def get_device_profile(dev: MiniBigDeviceInfo) -> DeviceProfile:
    """Determine the device capability profile from parsed device information."""
    if dev.d_type == 2 or not dev.supported:
        return PROFILE_HUB_MINI

    name_lower = dev.name.lower()

    if dev.d_type == 1:
        if dev.is_legacy:
            return PROFILE_PUSH_MINI_LEGACY
        return PROFILE_PUSH_MINI_NEW

    if any(k in name_lower for k in ("opener", "window", "curtain", "blind")):
        return PROFILE_WINDOW_OPENER

    if "switch" in name_lower:
        return PROFILE_SWITCH_MINI

    # Unrecognized or generic devices return Unknown profile with diagnostic entities only
    return PROFILE_UNKNOWN
