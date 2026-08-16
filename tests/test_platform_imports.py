"""Tests for platform imports and entity structure."""

from __future__ import annotations

import importlib


def test_import_all_platforms():
    """Verify that all platform modules and components can be imported without errors."""
    modules = [
        "custom_components.minibig",
        "custom_components.minibig.const",
        "custom_components.minibig.types",
        "custom_components.minibig.coordinator",
        "custom_components.minibig.config_flow",
        "custom_components.minibig.button",
        "custom_components.minibig.sensor",
        "custom_components.minibig.binary_sensor",
        "custom_components.minibig.switch",
        "custom_components.minibig.cover",
        "custom_components.minibig.select",
        "custom_components.minibig.number",
        "custom_components.minibig.minibig_ble",
        "custom_components.minibig.minibig_ble.const",
        "custom_components.minibig.minibig_ble.parser",
        "custom_components.minibig.minibig_ble.writer",
        "custom_components.minibig.minibig_ble.client",
        "custom_components.minibig.minibig_ble.devices",
    ]

    for mod in modules:
        m = importlib.import_module(mod)
        assert m is not None


def test_cover_and_switch_availability_with_none_dp():
    """Verify that cover and switch entities with None dp_id are initialized as available=False."""
    from unittest.mock import MagicMock

    from custom_components.minibig.cover import MiniBigWindowOpenerCover
    from custom_components.minibig.switch import MiniBigPowerSwitch

    entry = MagicMock()
    entry.unique_id = "test_entry"
    entry.runtime_data.device_info.address = "11:22:33:44:55:66"
    coord = MagicMock()
    coord.last_update_success = True

    # Cover with pos_dp=None -> available=False
    cover_unconf = MiniBigWindowOpenerCover(entry, coord, pos_dp=None, stop_dp=3)
    assert cover_unconf.available is False

    # Cover with pos_dp=0 -> available=True
    cover_conf = MiniBigWindowOpenerCover(entry, coord, pos_dp=0, stop_dp=3)
    assert cover_conf.available is True

    # Switch with power_dp=None -> available=False
    switch_unconf = MiniBigPowerSwitch(entry, coord, power_dp=None)
    assert switch_unconf.available is False

    # Switch with power_dp=0 -> available=True
    switch_conf = MiniBigPowerSwitch(entry, coord, power_dp=0)
    assert switch_conf.available is True


def test_new_setting_platforms_add_nothing_until_measured():
    """Select/number setups create no entities while DP slots are unmeasured."""
    from unittest.mock import MagicMock

    from custom_components.minibig import number, select
    from custom_components.minibig.minibig_ble.devices import PROFILE_WINDOW_OPENER

    entry = MagicMock()
    entry.unique_id = "test_entry"
    entry.options = {}
    entry.runtime_data.profile = PROFILE_WINDOW_OPENER
    entry.runtime_data.device_info.address = "11:22:33:44:55:66"

    for module in (select, number):
        added: list = []
        import asyncio

        asyncio.run(
            module.async_setup_entry(MagicMock(), entry, lambda e: added.extend(e))
        )
        assert added == []
