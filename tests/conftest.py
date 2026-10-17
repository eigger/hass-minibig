"""Enable actual Home Assistant custom integration fixtures."""

import pytest


@pytest.fixture(autouse=True)
def custom_integrations(enable_custom_integrations):
    yield
