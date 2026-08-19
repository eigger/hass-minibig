"""Constants for the MiniBig integration."""

from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "minibig"

# Last-known device identity, persisted in the config entry's data so the BLE
# client starts with a real IDV/fv/rev/d_type across Home Assistant restarts
# instead of a idv="0000" placeholder every time no advertisement has been
# captured yet at setup. Updated as fresh advertisements are parsed.
CONF_IDV = "idv"
CONF_FV = "fv"
CONF_REV = "rev"
CONF_D_TYPE = "d_type"
CONF_IS_LEGACY = "is_legacy"

# Default configuration values
DEFAULT_RETRY_COUNT = 3
DEFAULT_COMMAND_TIMEOUT_S = 10.0
DEFAULT_POLL_INTERVAL_MIN = 30
DEFAULT_KEEP_CONNECTED = False
DEFAULT_IDLE_DISCONNECT_S = 30.0
DEFAULT_MOVEMENT_IDLE_S = 3.0
DEFAULT_MAX_SESSION_S = 300.0

# User Options keys (5 options)
CONF_KEEP_CONNECTED = "keep_connected"
CONF_POLL_INTERVAL_MIN = "poll_interval_min"
CONF_RETRY_COUNT = "retry_count"

# Custom DP ID injection for unconfirmed profiles
CONF_POWER_DP_ID = "power_dp_id"
CONF_POSITION_DP_ID = "position_dp_id"
# Named DP slot overrides, e.g. {"measure": 7, "pair_emitter": 8}
CONF_DP_OVERRIDES = "dp_overrides"

DEFAULT_POSITION_DP = 0
DEFAULT_STOP_DP = 3
DEFAULT_POWER_DP = 0
DEFAULT_BATTERY_DP = 10

# Cover end-stop snap thresholds
COVER_SNAP_LOW = 2
COVER_SNAP_HIGH = 98

# Platforms to load
PLATFORMS: list[Platform] = [
    Platform.COVER,
    Platform.SWITCH,
    Platform.SELECT,
    Platform.NUMBER,
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
]
