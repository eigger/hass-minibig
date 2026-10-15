"""Tests for the per-command session reports behind the diagnostic sensors."""

from __future__ import annotations

import asyncio
from unittest.mock import patch

import pytest
from blesession import SessionTrace

from custom_components.minibig import session_report
from custom_components.minibig.minibig_ble.client import (
    OPERATION_COMMAND,
    OPERATION_POLL,
    STAGE_MAP,
    MiniBigConnection,
    MiniBigConnectionError,
    MiniBigDeviceError,
    MiniBigTimeoutError,
)
from custom_components.minibig.minibig_ble.const import Opcode, StatusCode
from tests.fake_transport import FakeBleakClient
from tests.test_client import _make_dev

ACK = bytes.fromhex("2afd000064")


def _ack(_written: bytes) -> bytes:
    return ACK


def _conn(client: FakeBleakClient, **kwargs) -> MiniBigConnection:
    return MiniBigConnection(device_info=_make_dev(), client_override=client, **kwargs)


@pytest.mark.asyncio
async def test_successful_command_is_filed_without_a_failure():
    client = FakeBleakClient()
    client.response_generator = _ack
    conn = _conn(client)

    await conn.send_dps([(0, 100)])

    assert conn.reports.failures == 0
    assert conn.reports.last is not None
    assert conn.reports.last["operation"] == OPERATION_COMMAND
    assert conn.reports.last["success"] is True
    assert conn.reports.last_failure is None
    await conn.disconnect()


@pytest.mark.asyncio
async def test_device_error_is_a_counted_failure_in_the_transfer_stage():
    client = FakeBleakClient()
    client.response_generator = lambda w: bytes([Opcode.PUB_DPS, StatusCode.DEVICE_NOT_MATCHING, 0])
    conn = _conn(client)

    with pytest.raises(MiniBigDeviceError):
        await conn.send_dps([(0, 100)])

    assert conn.reports.failures == 1
    assert conn.reports.last_failure_at is not None
    failure = conn.reports.last_failure
    assert failure["operation"] == OPERATION_COMMAND
    assert failure["failed_stage"] == "transfer"
    assert failure["failed_detail"] == "response"
    assert "IDV" in failure["error"]
    await conn.disconnect()


@pytest.mark.asyncio
async def test_timeout_is_a_counted_failure():
    client = FakeBleakClient()
    client.response_generator = lambda w: None
    conn = _conn(client, command_timeout=0.05)

    with pytest.raises(MiniBigTimeoutError):
        await conn.send_dps([(0, 100)])

    assert conn.reports.failures == 1
    assert conn.reports.last_failure["failed_detail"] == "response"
    await conn.disconnect()


@pytest.mark.asyncio
async def test_connect_failure_counts_for_a_command_but_not_for_a_poll():
    with patch("custom_components.minibig.minibig_ble.client.RECOVERY_WAIT_S", 0):
        command_conn = _conn(FakeBleakClient(fail_connect=True))
        with pytest.raises(MiniBigConnectionError):
            await command_conn.send_dps([(0, 100)])
        assert command_conn.reports.failures == 1
        assert command_conn.reports.last_failure["failed_stage"] == "connect"

        poll_conn = _conn(FakeBleakClient(fail_connect=True))
        with pytest.raises(MiniBigConnectionError):
            await poll_conn.read_dps(operation=OPERATION_POLL)
        assert poll_conn.reports.failures == 0
        assert poll_conn.reports.last is None


@pytest.mark.asyncio
async def test_poll_counts_only_when_it_fails_after_connecting():
    ok_client = FakeBleakClient()
    ok_client.response_generator = lambda w: bytes([Opcode.READ_DPS, StatusCode.DEVICE_SUCCESS, 0, 5])
    ok_conn = _conn(ok_client)
    await ok_conn.read_dps(operation=OPERATION_POLL)
    assert ok_conn.reports.last is None
    await ok_conn.disconnect()

    bad_client = FakeBleakClient()
    bad_client.response_generator = lambda w: None
    bad_conn = _conn(bad_client, command_timeout=0.05)
    with pytest.raises(MiniBigTimeoutError):
        await bad_conn.read_dps(operation=OPERATION_POLL)
    assert bad_conn.reports.failures == 1
    assert bad_conn.reports.last_failure["operation"] == OPERATION_POLL
    await bad_conn.disconnect()


@pytest.mark.asyncio
async def test_recovered_connect_is_not_blamed():
    client = FakeBleakClient(slot_error_once=True)
    client.response_generator = _ack
    with patch("custom_components.minibig.minibig_ble.client.RECOVERY_WAIT_S", 0):
        conn = _conn(client)
        await conn.send_dps([(0, 100)])

    assert conn.reports.failures == 0
    assert conn.reports.last["success"] is True
    assert "failed_stage" not in conn.reports.last
    assert conn.reports.last["connect_recovered"] is True
    assert "recovery_wait_s" in conn.reports.last
    await conn.disconnect()


@pytest.mark.asyncio
async def test_report_builder_is_used_and_its_failure_falls_back():
    client = FakeBleakClient()
    client.response_generator = _ack
    seen: list[tuple[str, SessionTrace, BaseException | None]] = []

    def builder(operation, trace, exc):
        seen.append((operation, trace, exc))
        return {"operation": operation, "success": exc is None, "marker": True}

    conn = _conn(client, report_builder=builder)
    await conn.send_dps([(0, 100)])
    assert conn.reports.last["marker"] is True
    assert seen[0][2] is None
    assert {"connect", "subscribe", "write", "response"} <= set(seen[0][1].timings)
    await conn.disconnect()

    broken = FakeBleakClient()
    broken.response_generator = lambda w: bytes([Opcode.PUB_DPS, StatusCode.DEVICE_BUSY, 0])

    def exploding(operation, trace, exc):
        raise RuntimeError("boom")

    conn = _conn(broken, report_builder=exploding)
    with pytest.raises(MiniBigDeviceError):
        await conn.send_dps([(0, 100)])
    assert conn.reports.failures == 1
    assert conn.reports.last_failure["operation"] == OPERATION_COMMAND
    await conn.disconnect()


def test_build_session_report_words_device_errors_and_uses_the_radio_facts():
    trace = SessionTrace(stage_map=STAGE_MAP)
    exc = MiniBigDeviceError(StatusCode.DEVICE_NOT_MATCHING, "Device matching error (IDV mismatch)")
    with pytest.raises(MiniBigDeviceError), trace.timed("response"):
        raise exc

    with patch.object(session_report, "radio_facts", return_value={"via": "proxy-1", "rssi": -60, "paths": 2}):
        report = session_report.build_session_report(
            None, "11:22:33:44:55:66", operation="command", trace=trace, exc=exc
        )

    assert report["operation"] == "command"
    assert report["success"] is False
    assert report["failed_stage"] == "transfer"
    assert "IDV" in report["likely_cause"]
    assert report["via"] == "proxy-1"
    assert report["response_s"] >= 0


def test_build_session_report_gives_connect_failures_a_device_specific_cause():
    trace = SessionTrace(stage_map=STAGE_MAP)
    exc = MiniBigConnectionError("not currently visible")
    with pytest.raises(MiniBigConnectionError), trace.timed("connect"):
        raise exc

    with patch.object(session_report, "radio_facts", return_value={}):
        report = session_report.build_session_report(
            None, "11:22:33:44:55:66", operation="command", trace=trace, exc=exc
        )

    assert report["failed_stage"] == "connect"
    assert "one BLE link" in report["likely_cause"]


def test_unmapped_device_status_is_not_reported_as_a_timeout():
    trace = SessionTrace(stage_map=STAGE_MAP)
    exc = MiniBigDeviceError(0x42, "Unknown device error")
    trace.fail("response")

    with patch.object(session_report, "radio_facts", return_value={}):
        report = session_report.build_session_report(
            None, "11:22:33:44:55:66", operation="command", trace=trace, exc=exc
        )

    assert "refused the command" in report["likely_cause"]
    assert "in time" not in report["likely_cause"]


@pytest.mark.asyncio
async def test_same_direction_is_not_counted_as_a_failure():
    client = FakeBleakClient()
    client.response_generator = lambda w: bytes([Opcode.PUB_DPS, StatusCode.DEVICE_SAME_DIRECTION, 0])
    conn = _conn(client)

    with pytest.raises(MiniBigDeviceError):
        await conn.send_dps([(0, 100)])

    assert conn.reports.failures == 0
    await conn.disconnect()


@pytest.mark.asyncio
async def test_write_failure_is_attributed_to_the_write_stage():
    client = FakeBleakClient()

    async def broken_write(*_args, **_kwargs):
        raise ConnectionError("link lost")

    client.write_gatt_char = broken_write
    conn = _conn(client)

    with pytest.raises(MiniBigConnectionError):
        await conn.send_dps([(0, 100)])

    failure = conn.reports.last_failure
    assert failure["failed_stage"] == "transfer"
    assert failure["failed_detail"] == "write"
    await conn.disconnect()


@pytest.mark.asyncio
async def test_subscribe_failure_counts_even_for_a_poll():
    client = FakeBleakClient()

    async def broken_notify(*_args, **_kwargs):
        raise ConnectionError("no notify")

    client.start_notify = broken_notify
    conn = _conn(client)

    with pytest.raises(MiniBigConnectionError):
        await conn.read_dps(operation=OPERATION_POLL)

    assert conn.reports.failures == 1
    assert conn.reports.last_failure["failed_stage"] == "session"
    assert conn.reports.last_failure["failed_detail"] == "subscribe"


@pytest.mark.asyncio
async def test_superseded_and_disconnected_commands_are_not_recorded():
    client = FakeBleakClient()
    client.response_generator = lambda w: None
    conn = _conn(client, command_timeout=5.0)

    first = asyncio.ensure_future(conn.send_dps([(0, 1)]))
    await asyncio.sleep(0)
    second = asyncio.ensure_future(conn.send_dps([(0, 2)]))
    third = asyncio.ensure_future(conn.send_dps([(0, 3)]))
    await asyncio.sleep(0.05)
    await conn.disconnect()
    results = await asyncio.gather(first, second, third, return_exceptions=True)

    assert any(isinstance(r, BaseException) for r in results)
    assert conn.reports.failures == 0
