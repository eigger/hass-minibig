"""Tests for MiniBig coordinator option handling."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import MagicMock

from custom_components.minibig.const import (
    CONF_POLL_INTERVAL_MIN,
    DEFAULT_POLL_INTERVAL_MIN,
)
from custom_components.minibig.coordinator import MiniBigActiveCoordinator
from custom_components.minibig.minibig_ble.devices import PROFILE_WINDOW_OPENER


def _make_coordinator(options: dict) -> MiniBigActiveCoordinator:
    entry = MagicMock()
    entry.unique_id = "AA:BB:CC:DD:EE:FF"
    entry.options = options
    connection = MagicMock()
    return MiniBigActiveCoordinator(
        MagicMock(),
        MagicMock(),
        entry=entry,
        connection=connection,
        profile=PROFILE_WINDOW_OPENER,
    )


def test_poll_interval_accepts_float_from_number_selector():
    """NumberSelector stores numbers as floats, so a float option must still
    produce a valid timedelta rather than leaking a float into scheduling."""
    coord = _make_coordinator({CONF_POLL_INTERVAL_MIN: 15.0})
    assert coord.update_interval == timedelta(minutes=15)


def test_poll_interval_zero_disables_polling():
    """0 means 'disabled' and must yield no interval, for both int and float."""
    for zero in (0, 0.0):
        coord = _make_coordinator({CONF_POLL_INTERVAL_MIN: zero})
        assert coord.update_interval is None


def test_poll_interval_defaults_when_unset():
    """With no option set, the documented default interval applies."""
    coord = _make_coordinator({})
    assert coord.update_interval == timedelta(minutes=DEFAULT_POLL_INTERVAL_MIN)
