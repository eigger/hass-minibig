"""Tests for MiniBig BLE transaction client."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from custom_components.minibig.minibig_ble.client import (
    MiniBigConnection,
    MiniBigDeviceError,
    MiniBigSupersededError,
    MiniBigTimeoutError,
)
from custom_components.minibig.minibig_ble.const import (
    DEVICE_NOTIFY_UUID,
    DEVICE_SERVICE_UUID,
    DEVICE_WRITE_UUID,
    Opcode,
    StatusCode,
)
from custom_components.minibig.minibig_ble.parser import MiniBigDeviceInfo
from tests.fake_transport import FakeBleakClient


def _make_dev() -> MiniBigDeviceInfo:
    return MiniBigDeviceInfo(
        address="11:22:33:44:55:66",
        name="Window Opener",
        idv="1CFE",
        fv=1,
        rev=0,
        d_type=0,
        init_mode=False,
        is_legacy=False,
        service_uuid=DEVICE_SERVICE_UUID,
        write_uuid=DEVICE_WRITE_UUID,
        notify_uuid=DEVICE_NOTIFY_UUID,
    )


@pytest.mark.asyncio
async def test_send_command_success():
    """Test successful command transaction: notify -> write -> ack."""
    fake_client = FakeBleakClient()
    dev = _make_dev()

    # Response generator that produces a valid ack for PUB_DPS
    def canned_response(written: bytes) -> bytes | None:
        if written.startswith(bytes([Opcode.PUB_DPS])):
            # 2a fd 00 00 64 (method=42, status=253, dp0=100)
            return bytes.fromhex("2afd000064")
        return None

    fake_client.response_generator = canned_response

    conn = MiniBigConnection(
        device_info=dev,
        client_override=fake_client,
        idle_disconnect_s=30.0,
    )

    resp = await conn.send_dps([(0, 100)])
    assert resp.ok is True
    assert resp.method == Opcode.PUB_DPS
    assert resp.dps == {0: 100}
    assert fake_client.is_connected is True
    assert len(fake_client.written_frames) == 1
    assert fake_client.written_frames[0].hex() == "2a7ac7000064"

    await conn.disconnect()
    assert fake_client.is_connected is False


@pytest.mark.asyncio
async def test_command_coalescing_rapid_fire():
    """Verify that rapid concurrent commands are coalesced and only the latest command executes."""
    fake_client = FakeBleakClient()
    dev = _make_dev()

    def canned_response(written: bytes) -> bytes | None:
        return bytes.fromhex("2afd000000")

    fake_client.response_generator = canned_response

    conn = MiniBigConnection(
        device_info=dev,
        client_override=fake_client,
    )

    # Fire 3 commands concurrently while disconnected
    task1 = asyncio.create_task(conn.send_dps([(0, 100)]))  # Open (overwritten)
    task2 = asyncio.create_task(conn.send_dps([(0, 0)]))    # Close (overwritten)
    task3 = asyncio.create_task(conn.send_dps([(3, 0)]))    # Stop (latest)

    # Task 1 & 2 should receive MiniBigSupersededError (which is an Exception, not CancelledError)
    results = await asyncio.gather(task1, task2, task3, return_exceptions=True)

    assert isinstance(results[0], MiniBigSupersededError)
    assert isinstance(results[0], Exception)
    assert isinstance(results[1], MiniBigSupersededError)
    assert isinstance(results[1], Exception)
    assert results[2].ok is True  # Task 3 succeeded

    # Only 1 frame (the latest Stop command '2a7ac7030000') must be written to GATT!
    assert len(fake_client.written_frames) == 1
    assert fake_client.written_frames[0].hex() == "2a7ac7030000"

    await conn.disconnect()


@pytest.mark.asyncio
async def test_send_command_device_error():
    """Test device returning an error status code (e.g. 254 BUSY)."""
    fake_client = FakeBleakClient()
    dev = _make_dev()

    def canned_response(written: bytes) -> bytes | None:
        return bytes([Opcode.PUB_DPS, StatusCode.DEVICE_BUSY, 0x00])

    fake_client.response_generator = canned_response

    conn = MiniBigConnection(
        device_info=dev,
        client_override=fake_client,
    )

    with pytest.raises(MiniBigDeviceError) as exc_info:
        await conn.send_dps([(0, 100)])
    assert exc_info.value.status == StatusCode.DEVICE_BUSY

    await conn.disconnect()


@pytest.mark.asyncio
async def test_send_command_timeout():
    """Test timeout waiting for response."""
    fake_client = FakeBleakClient()
    dev = _make_dev()
    fake_client.response_generator = lambda w: None

    conn = MiniBigConnection(
        device_info=dev,
        client_override=fake_client,
        command_timeout=0.05,
    )

    with pytest.raises(MiniBigTimeoutError):
        await conn.send_dps([(0, 100)])

    await conn.disconnect()


@pytest.mark.asyncio
async def test_report_dps_stream_and_movement():
    """Test asynchronous REPORT_DPS(24) streaming triggers movement and report callback."""
    fake_client = FakeBleakClient()
    dev = _make_dev()

    conn = MiniBigConnection(
        device_info=dev,
        client_override=fake_client,
        movement_idle_s=0.05,
    )

    received_reports = []
    movement_states = []

    conn.register_report_callback(lambda r: received_reports.append(r))
    conn.register_movement_callback(lambda m: movement_states.append(m))

    await conn.connect()
    assert conn.is_moving is False

    # Simulate device streaming report (Opcode 24, status 253, dp0=50)
    fake_client.trigger_notify(bytes.fromhex("18fd000032"))
    assert conn.is_moving is True
    assert len(received_reports) == 1
    assert received_reports[0].dps == {0: 50}
    assert True in movement_states

    # Wait for movement_idle_s to expire
    await asyncio.sleep(0.08)
    assert conn.is_moving is False
    assert False in movement_states

    await conn.disconnect()


@pytest.mark.asyncio
async def test_idle_disconnect_and_touch():
    """Test idle timeout disconnect and traffic reset."""
    fake_client = FakeBleakClient()
    dev = _make_dev()

    conn = MiniBigConnection(
        device_info=dev,
        client_override=fake_client,
        idle_disconnect_s=0.05,
        keep_connected=False,
    )

    await conn.connect()
    assert fake_client.is_connected is True

    # Touch before timeout -> resets timer
    await asyncio.sleep(0.03)
    conn._touch()
    await asyncio.sleep(0.03)
    assert fake_client.is_connected is True

    # Allow timeout to expire
    await asyncio.sleep(0.06)
    assert fake_client.is_connected is False


@pytest.mark.asyncio
async def test_max_session_runaway_guard():
    """Test that max_session_s forcibly disconnects runaway traffic when keep_connected=False."""
    fake_client = FakeBleakClient()
    dev = _make_dev()

    conn = MiniBigConnection(
        device_info=dev,
        client_override=fake_client,
        idle_disconnect_s=10.0,
        max_session_s=0.05,
        keep_connected=False,
    )

    await conn.connect()
    assert fake_client.is_connected is True

    # Continuously touch
    for _ in range(5):
        await asyncio.sleep(0.02)
        conn._touch()

    # Session duration exceeded max_session_s (0.05s) -> must be disconnected
    await asyncio.sleep(0.02)
    assert fake_client.is_connected is False


@pytest.mark.asyncio
async def test_keep_connected_mode():
    """Test keep_connected=True prevents idle timeout disconnect."""
    fake_client = FakeBleakClient()
    dev = _make_dev()

    conn = MiniBigConnection(
        device_info=dev,
        client_override=fake_client,
        idle_disconnect_s=0.03,
        max_session_s=0.05,
        keep_connected=True,
    )

    await conn.connect()
    assert fake_client.is_connected is True

    # Sleep well past idle_disconnect_s and max_session_s
    await asyncio.sleep(0.08)
    assert fake_client.is_connected is True

    await conn.disconnect()


@pytest.mark.asyncio
async def test_slot_recovery_retry():
    """Test recovery and retry when connection slot error occurs."""
    fake_client = FakeBleakClient(slot_error_once=True)
    dev = _make_dev()

    conn = MiniBigConnection(
        device_info=dev,
        client_override=fake_client,
    )

    with patch("custom_components.minibig.minibig_ble.client.asyncio.sleep", new_callable=AsyncMock) as mock_sleep, \
         patch("custom_components.minibig.minibig_ble.client.close_stale_connections_by_address", new_callable=AsyncMock) as mock_close:
        await conn.connect()
        assert fake_client.is_connected is True
        mock_close.assert_called()
        mock_sleep.assert_called_with(12.0)

    await conn.disconnect()


@pytest.mark.asyncio
async def test_generic_connect_failure_also_recovers():
    """A plain connect timeout (not BleakOutOfConnectionSlotsError) must still
    trigger the stale-link-clear-and-retry recovery, not fail immediately.

    Real devices only accept one BLE link, and a dead peer connection can
    surface as any exception type depending on platform/backend - not just
    BleakOutOfConnectionSlotsError.
    """
    fake_client = FakeBleakClient(generic_error_once=True)
    dev = _make_dev()

    conn = MiniBigConnection(
        device_info=dev,
        client_override=fake_client,
    )

    with patch("custom_components.minibig.minibig_ble.client.asyncio.sleep", new_callable=AsyncMock) as mock_sleep, \
         patch("custom_components.minibig.minibig_ble.client.close_stale_connections_by_address", new_callable=AsyncMock) as mock_close:
        await conn.connect()
        assert fake_client.is_connected is True
        mock_close.assert_called()
        mock_sleep.assert_called_with(12.0)

    await conn.disconnect()
