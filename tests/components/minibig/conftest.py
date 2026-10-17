"""Actual HA entries and a remote-only Bluetooth transport replacement."""

from time import monotonic

import pytest
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from habluetooth import get_manager
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.minibig.minibig_ble.const import DEVICE_SERVICE_UUID
from tests.components.minibig.fake_transport import FakeBleakClient

ADDRESS = "AA:BB:CC:DD:EE:FF"


@pytest.fixture
async def bluetooth_ready(hass, enable_bluetooth):
    assert await async_setup_component(hass, "bluetooth", {})
    return get_manager()


def make_advertisement(*, name="CLWM_TEST", address=ADDRESS, idv=b"\x1c\xfe", d_type=5, rssi=-55):
    raw = b"\x01\x00\x02" + bytes(6) + idv + bytes(2) + bytes([d_type])
    device = BLEDevice(address, name, {})
    adv = AdvertisementData(
        local_name=name,
        manufacturer_data={1: raw[2:]},
        service_data={},
        service_uuids=[DEVICE_SERVICE_UUID],
        tx_power=None,
        rssi=rssi,
        platform_data=(),
    )
    return BluetoothServiceInfoBleak.from_scan("00:00:00:00:00:01", device, adv, monotonic(), True)


@pytest.fixture
async def advertisement(hass, bluetooth_ready):
    info = make_advertisement()
    bluetooth_ready.scanner_adv_received(info)
    await hass.async_block_till_done()
    return info


@pytest.fixture
def transport(monkeypatch):
    client = FakeBleakClient(address=ADDRESS)

    async def connect(*args, **kwargs):
        await client.connect()
        return client

    def response(frame):
        return bytes([frame[0], 253, 0, 0, 50, 10, 0, 80])

    client.response_generator = response
    monkeypatch.setattr("blesession.session.establish_connection", connect)
    monkeypatch.setattr("custom_components.minibig.minibig_ble.client.RECOVERY_WAIT_S", 0)
    return client


@pytest.fixture
def entry(hass):
    config = MockConfigEntry(
        domain="minibig",
        unique_id=ADDRESS,
        title="Test opener",
        data={"address": ADDRESS},
        options={"poll_interval_min": 0},
    )
    config.add_to_hass(hass)
    return config


@pytest.fixture
async def loaded_entry(hass, entry, advertisement, transport):
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry
