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

    def builder(operation, trace, exc):
        with patch.object(session_report, "radio_facts", return_value={}):
            return session_report.build_session_report(None, "aa", operation=operation, trace=trace, exc=exc)

    with patch("custom_components.minibig.minibig_ble.client.RECOVERY_WAIT_S", 0):
        conn = _conn(client, report_builder=builder)
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


def _sensor_entry(conn: MiniBigConnection):
    from unittest.mock import MagicMock

    entry = MagicMock()
    entry.unique_id = "test_entry"
    entry.runtime_data.device_info.address = "11:22:33:44:55:66"
    entry.runtime_data.connection = conn
    return entry


@pytest.mark.asyncio
async def test_last_failure_sensor_follows_the_reports():
    from unittest.mock import MagicMock

    from custom_components.minibig.sensor import MiniBigErrorCountSensor, MiniBigLastFailureSensor

    client = FakeBleakClient()
    client.response_generator = lambda w: bytes([Opcode.PUB_DPS, StatusCode.DEVICE_BUSY, 0])
    conn = _conn(client)
    coordinator = MagicMock()
    coordinator.last_update_success = False
    sensor = MiniBigLastFailureSensor(_sensor_entry(conn), coordinator)
    sensor.async_write_ha_state = MagicMock()

    # Nothing failed yet; and it stays available while the coordinator is not.
    assert sensor.native_value is None
    assert sensor.extra_state_attributes is None
    assert sensor.available is True

    await sensor.async_added_to_hass()
    with pytest.raises(MiniBigDeviceError):
        await conn.send_dps([(0, 100)])

    assert sensor.native_value is not None
    assert sensor.extra_state_attributes["operation"] == OPERATION_COMMAND
    assert "busy" in sensor.extra_state_attributes["error"].lower()
    assert sensor.async_write_ha_state.call_count == 1

    count = MiniBigErrorCountSensor(_sensor_entry(conn), coordinator)
    assert count.native_value == 1
    assert count.extra_state_attributes is None

    await sensor.async_will_remove_from_hass()
    conn.reports.record({"operation": "command", "success": False, "error": "boom"})
    assert sensor.async_write_ha_state.call_count == 1
    await conn.disconnect()


@pytest.mark.asyncio
async def test_connection_duration_keeps_the_last_successful_new_connection():
    from unittest.mock import MagicMock

    from custom_components.minibig.sensor import MiniBigConnectionDurationSensor

    conn = _conn(FakeBleakClient())
    sensor = MiniBigConnectionDurationSensor(_sensor_entry(conn), MagicMock())
    sensor.async_write_ha_state = MagicMock()
    await sensor.async_added_to_hass()
    assert sensor.native_value is None

    # A failed attempt that timed the connect stage is not a connection time.
    conn.reports.record({"operation": "command", "success": False, "connect_s": 9.0})
    assert sensor.native_value is None

    conn.reports.record({"operation": "command", "success": True, "connect_s": 0.0})
    assert sensor.native_value == 0.0
    assert sensor.extra_state_attributes["connect_s"] == 0.0

    # A reused link has no connect stage: the value stays.
    conn.reports.record({"operation": "command", "success": True, "reused": True})
    assert sensor.native_value == 0.0
    await sensor.async_will_remove_from_hass()


def _real_path_conn(**kwargs) -> MiniBigConnection:
    """A connection that goes through ble_session (no client_override)."""
    from unittest.mock import MagicMock

    device = MagicMock(address="11:22:33:44:55:66")
    return MiniBigConnection(device_info=_make_dev(), ble_device_callback=lambda: device, **kwargs)


@pytest.mark.asyncio
async def test_ble_session_connects_reuses_the_link_and_replaces_a_dead_one():
    from unittest.mock import AsyncMock

    first, second = FakeBleakClient(), FakeBleakClient()
    for client in (first, second):
        client.response_generator = _ack
        client._is_connected = True

    conn = _real_path_conn()
    with patch("blesession.session.establish_connection", new_callable=AsyncMock, side_effect=[first, second]) as est:
        await conn.send_dps([(0, 1)])
        await conn.send_dps([(0, 2)])
        assert est.call_count == 1  # second command reused the live link

        # The link died without a clean disconnect: next command opens a new one.
        first._is_connected = False
        conn._is_notifying = False
        await conn.send_dps([(0, 3)])
        assert est.call_count == 2
        assert conn._client is second

    await conn.disconnect()


@pytest.mark.asyncio
async def test_unreachable_device_is_a_command_failure_but_not_a_poll_failure():
    with patch("custom_components.minibig.minibig_ble.client.RECOVERY_WAIT_S", 0):
        conn = MiniBigConnection(device_info=_make_dev(), ble_device_callback=lambda: None)
        with pytest.raises(MiniBigConnectionError, match="11:22:33:44:55:66"):
            await conn.read_dps(operation=OPERATION_POLL)
        assert conn.reports.failures == 0

        with pytest.raises(MiniBigConnectionError):
            await conn.send_dps([(0, 1)])
        assert conn.reports.failures == 1
        assert conn.reports.last_failure["failed_stage"] == "unreachable"


@pytest.mark.asyncio
async def test_slot_exhaustion_wrapped_by_blesession_still_triggers_recovery(caplog):
    import logging
    from unittest.mock import AsyncMock

    from custom_components.minibig.minibig_ble.client import BleakOutOfConnectionSlotsError

    client = FakeBleakClient()
    client._is_connected = True
    client.response_generator = _ack
    conn = _real_path_conn()

    with (
        patch("custom_components.minibig.minibig_ble.client.RECOVERY_WAIT_S", 0),
        patch(
            "blesession.session.establish_connection",
            new_callable=AsyncMock,
            side_effect=[BleakOutOfConnectionSlotsError("no slots"), client],
        ),
        caplog.at_level(logging.WARNING),
    ):
        await conn.send_dps([(0, 1)])

    assert "slots exhausted" in caplog.text
    assert conn.reports.failures == 0
    await conn.disconnect()


@pytest.mark.asyncio
async def test_idle_disconnect_waits_for_the_lock_and_yields_to_newer_traffic():
    client = FakeBleakClient()
    client.response_generator = _ack
    conn = _conn(client, idle_disconnect_s=0.05)
    await conn.send_dps([(0, 1)])
    assert client.is_connected

    async with conn._session_lock:
        await asyncio.sleep(0.12)  # the idle timer fires but must wait for the lock
        assert client.is_connected
        conn._touch()  # traffic arrived meanwhile: the fired timer is stale

    await asyncio.sleep(0.02)
    assert client.is_connected

    await asyncio.sleep(0.12)  # now genuinely idle
    assert not client.is_connected


@pytest.mark.asyncio
async def test_ble_session_closes_a_dropped_but_open_handle_and_reuses_a_live_one():
    from unittest.mock import AsyncMock

    first, second = FakeBleakClient(), FakeBleakClient()
    for client in (first, second):
        client.response_generator = _ack
        client._is_connected = True
    callbacks: list = []

    async def establish(_cls, _device, _name, disconnected_callback=None, **_kw):
        callbacks.append(disconnected_callback)
        return [first, second][len(callbacks) - 1]

    conn = _real_path_conn()
    with patch("blesession.session.establish_connection", new=AsyncMock(side_effect=establish)):
        await conn.send_dps([(0, 1)])
        assert conn._client is first

        # Notifications lapsed but the link is still up: ble_session reuses it.
        conn._is_notifying = False
        await conn.send_dps([(0, 2)])
        assert len(callbacks) == 1
        assert conn._client is first

        # The stack reported a drop while the handle still claims to be open:
        # it must be closed before a fresh link is opened.
        callbacks[0](first)
        await conn.send_dps([(0, 3)])
        assert len(callbacks) == 2
        assert first.is_connected is False
        assert conn._client is second

        # A late drop event from the replaced link must not touch the new one.
        callbacks[0](first)
        assert conn.is_connected is True

    await conn.disconnect()


@pytest.mark.asyncio
async def test_disconnect_is_bounded_when_the_stack_hangs():
    client = FakeBleakClient()
    client.response_generator = _ack
    conn = _conn(client)
    await conn.send_dps([(0, 1)])

    async def hang():
        await asyncio.sleep(3600)

    client.disconnect = hang
    with patch("custom_components.minibig.minibig_ble.client.DISCONNECT_TIMEOUT_S", 0.05):
        await asyncio.wait_for(conn.disconnect(), timeout=1.0)


@pytest.mark.asyncio
async def test_idle_disconnect_does_not_fail_a_command_queued_behind_it():
    client = FakeBleakClient()
    client.response_generator = _ack
    conn = _conn(client, idle_disconnect_s=0.05)
    await conn.send_dps([(0, 1)])

    async with conn._session_lock:
        await asyncio.sleep(0.12)  # idle timer fired and is waiting for the lock
        command = asyncio.ensure_future(conn.send_dps([(0, 2)]))
        await asyncio.sleep(0)

    resp = await asyncio.wait_for(command, timeout=1.0)
    assert resp.ok
    assert conn.reports.failures == 0
    await conn.disconnect()


@pytest.mark.asyncio
async def test_close_stops_a_worker_stuck_in_recovery_and_refuses_new_commands():
    client = FakeBleakClient(fail_connect=True)
    conn = _conn(client)

    with patch("custom_components.minibig.minibig_ble.client.RECOVERY_WAIT_S", 30):
        command = asyncio.ensure_future(conn.send_dps([(0, 1)]))
        await asyncio.sleep(0.05)  # worker is now in the recovery wait
        await asyncio.wait_for(conn.close(), timeout=1.0)

    # Callers get an ordinary error on unload, not a bare cancellation.
    with pytest.raises(MiniBigConnectionError, match="closed"):
        await command
    assert not client.is_connected
    with pytest.raises(MiniBigConnectionError, match="closed"):
        await conn.send_dps([(0, 2)])


def test_session_s_is_left_out_of_reports():
    trace = SessionTrace(stage_map=STAGE_MAP)
    with trace.timed("session"):
        pass
    with patch.object(session_report, "radio_facts", return_value={}):
        report = session_report.build_session_report(None, "aa", operation="command", trace=trace, exc=None)
    assert "session_s" not in report


@pytest.mark.asyncio
async def test_close_does_not_start_a_queued_command_while_a_response_is_awaited():
    client = FakeBleakClient()
    client.response_generator = lambda w: None  # never answers
    conn = _conn(client, command_timeout=30.0)
    first = asyncio.ensure_future(conn.send_dps([(0, 1)]))
    await asyncio.sleep(0.05)  # worker is waiting for the response
    queued = asyncio.ensure_future(conn.send_dps([(0, 2)]))
    await asyncio.sleep(0)
    writes_before = len(client.written_frames)

    await asyncio.wait_for(conn.close(), timeout=1.0)

    assert len(client.written_frames) == writes_before
    results = await asyncio.gather(first, queued, return_exceptions=True)
    for result in results:
        assert isinstance(result, MiniBigConnectionError)
        assert "closed" in str(result)
    assert not client.is_connected


@pytest.mark.asyncio
async def test_link_drop_while_waiting_fails_fast_and_is_reported_as_a_drop():
    client = FakeBleakClient()
    client.response_generator = lambda w: None  # no answer will come

    def builder(operation, trace, exc):
        with patch.object(session_report, "radio_facts", return_value={}):
            return session_report.build_session_report(None, "aa", operation=operation, trace=trace, exc=exc)

    conn = _conn(client, command_timeout=30.0, report_builder=builder)
    command = asyncio.ensure_future(conn.send_dps([(0, 1)]))
    await asyncio.sleep(0.05)  # written, waiting for the response

    client._is_connected = False
    conn._on_client_disconnected(client)

    with pytest.raises(ConnectionError, match="dropped"):
        await asyncio.wait_for(command, timeout=1.0)
    failure = conn.reports.last_failure
    assert failure["failed_detail"] == "response"
    assert "went away mid-session" in failure["likely_cause"]
    assert "did not answer in time" not in failure["likely_cause"]
    await conn.disconnect()


@pytest.mark.asyncio
async def test_reused_link_keeps_reporting_how_it_was_opened():
    client = FakeBleakClient()
    client.response_generator = _ack
    seen: list[SessionTrace] = []

    def builder(operation, trace, exc):
        seen.append(trace)
        return {"operation": operation, "success": exc is None, **trace.facts}

    conn = _conn(client, report_builder=builder)
    link = object()
    await conn.send_dps([(0, 1)])
    conn._link = link  # as ble_session's probe_link would have recorded
    await conn.send_dps([(0, 2)])

    assert seen[1].link is link
    assert conn.reports.last["reused"] is True
    await conn.disconnect()


@pytest.mark.asyncio
async def test_subscribe_failure_does_not_fail_a_command_queued_meanwhile():
    client = FakeBleakClient()
    client.response_generator = _ack
    real_start_notify = client.start_notify
    calls = {"n": 0}

    async def flaky_start_notify(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            await asyncio.sleep(0.05)  # time for a second command to queue up
            raise ConnectionError("no notify")
        return await real_start_notify(*args, **kwargs)

    client.start_notify = flaky_start_notify
    conn = _conn(client)

    first = asyncio.ensure_future(conn.send_dps([(0, 1)]))
    await asyncio.sleep(0.01)
    second = asyncio.ensure_future(conn.send_dps([(0, 2)]))

    results = await asyncio.gather(first, second, return_exceptions=True)
    assert isinstance(results[0], MiniBigConnectionError)
    assert results[1].ok
    await conn.disconnect()


@pytest.mark.asyncio
async def test_link_info_is_stored_on_connect_reused_and_cleared_on_disconnect():
    from unittest.mock import AsyncMock

    client = FakeBleakClient()
    client._is_connected = True
    client.response_generator = _ack
    traces: list[SessionTrace] = []

    def builder(operation, trace, exc):
        traces.append(trace)
        return {"operation": operation, "success": exc is None}

    conn = _real_path_conn(report_builder=builder)
    with patch("blesession.session.establish_connection", new_callable=AsyncMock, return_value=client):
        await conn.send_dps([(0, 1)])
        await conn.send_dps([(0, 2)])

    assert traces[0].link is not None
    assert traces[1].link is traces[0].link
    assert traces[1].facts["reused"] is True
    assert conn._link is traces[0].link

    await conn.disconnect()
    assert conn._link is None
