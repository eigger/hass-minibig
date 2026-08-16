"""Pytest configuration and Home Assistant module mocks."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock


class MockBase:
    """Base class supporting subscripting for generics in tests."""

    def __init__(self, *args, **kwargs):
        pass

    def __class_getitem__(cls, item):
        return cls


# Mock Home Assistant exceptions
class MockHomeAssistantError(Exception):
    """Mock HomeAssistantError."""


ha_exceptions = MagicMock()
ha_exceptions.HomeAssistantError = MockHomeAssistantError
sys.modules["homeassistant.exceptions"] = ha_exceptions

# Mock Home Assistant core and submodules
sys.modules["homeassistant.components"] = MagicMock()
sys.modules["homeassistant.components.bluetooth"] = MagicMock()

# Setup bluetooth passive update processor mocks
class MockPassiveCoordinator(MockBase):
    pass

class MockPassiveDataProcessor(MockBase):
    pass

ha_bt_processor = MagicMock()
ha_bt_processor.PassiveBluetoothProcessorCoordinator = MockPassiveCoordinator
ha_bt_processor.PassiveBluetoothDataProcessor = MockPassiveDataProcessor
sys.modules["homeassistant.components.bluetooth.passive_update_processor"] = ha_bt_processor

# Mock entity platforms with distinct classes
class MockButtonEntity(MockBase):
    pass

class MockSensorEntity(MockBase):
    pass

class MockBinarySensorEntity(MockBase):
    pass

class MockSwitchEntity(MockBase):
    pass

class MockCoverEntity(MockBase):
    pass

class MockSelectEntity(MockBase):
    pass

class MockNumberEntity(MockBase):
    pass

class MockRestoreEntity(MockBase):
    pass

class MockCoordinatorEntity(MockBase):
    @property
    def available(self) -> bool:
        coord = getattr(self, "coordinator", None)
        if coord is not None and hasattr(coord, "last_update_success"):
            return bool(coord.last_update_success)
        return True

class MockDataUpdateCoordinator(MockBase):
    pass

sys.modules["homeassistant.components.button"] = MagicMock()
sys.modules["homeassistant.components.button"].ButtonEntity = MockButtonEntity

sys.modules["homeassistant.components.sensor"] = MagicMock()
sys.modules["homeassistant.components.sensor"].SensorEntity = MockSensorEntity

sys.modules["homeassistant.components.binary_sensor"] = MagicMock()
sys.modules["homeassistant.components.binary_sensor"].BinarySensorEntity = MockBinarySensorEntity

sys.modules["homeassistant.components.switch"] = MagicMock()
sys.modules["homeassistant.components.switch"].SwitchEntity = MockSwitchEntity

sys.modules["homeassistant.components.cover"] = MagicMock()
sys.modules["homeassistant.components.cover"].CoverEntity = MockCoverEntity

sys.modules["homeassistant.components.select"] = MagicMock()
sys.modules["homeassistant.components.select"].SelectEntity = MockSelectEntity

sys.modules["homeassistant.components.number"] = MagicMock()
sys.modules["homeassistant.components.number"].NumberEntity = MockNumberEntity

sys.modules["homeassistant.helpers.restore_state"] = MagicMock()
sys.modules["homeassistant.helpers.restore_state"].RestoreEntity = MockRestoreEntity

sys.modules["homeassistant.helpers.update_coordinator"] = MagicMock()
sys.modules["homeassistant.helpers.update_coordinator"].CoordinatorEntity = MockCoordinatorEntity
sys.modules["homeassistant.helpers.update_coordinator"].DataUpdateCoordinator = MockDataUpdateCoordinator

sys.modules["homeassistant.config_entries"] = MagicMock()
sys.modules["homeassistant.const"] = MagicMock()
sys.modules["homeassistant.core"] = MagicMock()
sys.modules["homeassistant.helpers"] = MagicMock()
sys.modules["homeassistant.helpers.device_registry"] = MagicMock()
sys.modules["homeassistant.helpers.entity_platform"] = MagicMock()
sys.modules["homeassistant.helpers.selector"] = MagicMock()
sys.modules["homeassistant.helpers.config_validation"] = MagicMock()
