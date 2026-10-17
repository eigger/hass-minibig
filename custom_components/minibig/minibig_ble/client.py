"""BLE transaction client for MiniBig devices with command coalescing."""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable
from functools import partial
from dataclasses import dataclass
from typing import Any

from bleak import BleakClient
from bleak_retry_connector import (
    BleakOutOfConnectionSlotsError,
    close_stale_connections_by_address,
)
from blesession import (
    DISCONNECT_TIMEOUT_S,
    LinkInfo,
    SessionDropped,
    SessionReports,
    SessionTrace,
    Unreachable,
    ble_session,
    fallback_report,
    stages,
)

from .const import STATUS_MESSAGES, Opcode, StatusCode
from .parser import MiniBigDeviceInfo
from .writer import (
    Response,
    build_frame,
    build_manu_reset,
    build_pub_dps,
    build_read_dps,
    build_restart,
    parse_response,
)

_LOGGER = logging.getLogger(__name__)

# The device only accepts one BLE link. After clearing a stale one, it needs a
# moment before it starts advertising as connectable again.
RECOVERY_WAIT_S = 12.0

# Device stage -> blesession primary stage. ``connect`` is already primary.
STAGE_MAP = {
    "recovery_wait": stages.CONNECT,
    "subscribe": stages.SESSION,
    "write": stages.TRANSFER,
    "response": stages.TRANSFER,
}

OPERATION_POLL = "poll"
OPERATION_COMMAND = "command"
OPERATION_SERVICE = "service"

_NO_TOKEN = object()

SessionReportBuilder = Callable[[str, SessionTrace, BaseException | None], dict[str, Any]]


class MiniBigError(Exception):
    """Base exception for MiniBig BLE."""


class MiniBigConnectionError(MiniBigError):
    """Error connecting to MiniBig device or BLE slot exhausted."""


class MiniBigTimeoutError(MiniBigError):
    """Timeout waiting for response from MiniBig device."""


class MiniBigSupersededError(MiniBigError):
    """Command was superseded (coalesced) by a newer command before completion."""


class MiniBigDeviceError(MiniBigError):
    """MiniBig device returned an error status code."""

    def __init__(self, status: int, message: str) -> None:
        """Initialize device error."""
        super().__init__(f"Device error status {status}: {message}")
        self.status = status
        self.error_message = message


@dataclass
class _QueuedCommand:
    """Internal representation of a coalesced pending command."""

    frame: bytes
    expected_method: int
    timeout: float
    user_future: asyncio.Future[Response]
    operation: str = OPERATION_COMMAND


class MiniBigConnection:
    """Manages the BLE connection session and coalesced transactions for a MiniBig device."""

    def __init__(
        self,
        device_info: MiniBigDeviceInfo,
        ble_device_callback: Callable[[], Any] | None = None,
        command_timeout: float = 10.0,
        idle_disconnect_s: float = 30.0,
        keep_connected: bool = False,
        movement_idle_s: float = 3.0,
        max_session_s: float = 300.0,
        retry_count: int = 3,
        loop: asyncio.AbstractEventLoop | None = None,
        client_override: BleakClient | None = None,
        report_builder: SessionReportBuilder | None = None,
    ) -> None:
        """Initialize MiniBig BLE connection manager."""
        self.device_info = device_info
        self._ble_device_callback = ble_device_callback
        self.command_timeout = command_timeout
        self.idle_disconnect_s = idle_disconnect_s
        self.keep_connected = keep_connected
        self.movement_idle_s = movement_idle_s
        self.max_session_s = max_session_s
        self.retry_count = retry_count
        self._loop = loop

        # Per-command session breakdown for the diagnostic sensors. The
        # builder is injected (it needs hass for the radio facts); without
        # one a minimal report is filed so a failure is still counted.
        self.reports = SessionReports()
        self.report_builder = report_builder

        self._client_override = client_override
        self._client: BleakClient | Any | None = client_override

        # Coalescing slot: holds at most 1 pending command, newer commands overwrite older
        self._pending_command: _QueuedCommand | None = None
        self._worker_task: asyncio.Task[None] | None = None
        self._session_lock = asyncio.Lock()
        self._write_lock = asyncio.Lock()

        self._idle_timer_handle: asyncio.TimerHandle | None = None
        self._touch_generation = 0
        self._session_guard_pending = False
        self._closing = False
        self._inflight_command: _QueuedCommand | None = None
        # Which radio the current link went over, kept so commands that reuse
        # the link still report it (they never pass through ble_session).
        self._link: LinkInfo | None = None
        # Identifies the link whose drop events count. A late disconnect event
        # from a link we already replaced (a proxy can deliver it long after)
        # must not fail a command running on the new one.
        self._link_token: object | None = None
        self._movement_timer_handle: asyncio.TimerHandle | None = None
        self._session_start_time: float | None = None

        self._current_waiter: asyncio.Future[Response] | None = None
        self._current_method: int | None = None

        self._report_callbacks: list[Callable[[Response], None]] = []
        self._movement_callbacks: list[Callable[[bool], None]] = []
        self._connection_callbacks: list[Callable[[bool], None]] = []
        self._background_tasks: set[asyncio.Task[Any]] = set()

        self._is_moving: bool = False
        self._last_status: int | None = None
        self._is_notifying: bool = False
        # Last connection state pushed to callbacks, so repeated connect() /
        # disconnect() calls that do not actually change the link state stay
        # silent instead of re-notifying every subscriber.
        self._notified_connected: bool = False

    def _get_loop(self) -> asyncio.AbstractEventLoop:
        """Get the active event loop."""
        if self._loop is not None:
            return self._loop
        try:
            return asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.get_event_loop()

    def update_device_info(self, new_info: MiniBigDeviceInfo) -> None:
        """Refresh the device info used to build frames from a fresh advertisement.

        device_info is normally captured once at config entry setup (from the
        last known advertisement, or a placeholder with idv="0000" if none was
        available yet). If it is never refreshed, a boot-time placeholder stays
        wired into every frame for the entry's whole lifetime, silently sending
        the wrong IDV header on every command (device replies 255
        DEVICE_NOT_MATCHING) until Home Assistant is restarted or the entry is
        reloaded. Callers should feed this from an ongoing advertisement stream
        (see MiniBigPassiveBluetoothProcessorCoordinator) so a bad initial
        snapshot self-heals as soon as a real advertisement is parsed.

        A placeholder idv ("0000") never overwrites a previously known real
        one, since that would regress good data to a worse guess.
        """
        if new_info.idv == "0000" and self.device_info.idv != "0000":
            return
        self.device_info = new_info

    @property
    def is_connected(self) -> bool:
        """Return True if a GATT link to the device is currently established.

        This is the live link state, not "the device is in range": it is only
        True between a successful connect() and the matching disconnect (idle
        timeout, session guard, unload, or a drop reported by the BLE stack).
        """
        return (
            self._client is not None
            and self._client.is_connected
            and self._is_notifying
        )

    @property
    def is_moving(self) -> bool:
        """Return True if cover/device is actively moving."""
        return self._is_moving

    @property
    def last_status(self) -> int | None:
        """Return last received status code."""
        return self._last_status

    def register_report_callback(self, callback: Callable[[Response], None]) -> Callable[[], None]:
        """Register callback for status updates and return unregister function."""
        self._report_callbacks.append(callback)
        return lambda: self._report_callbacks.remove(callback) if callback in self._report_callbacks else None

    def register_movement_callback(self, callback: Callable[[bool], None]) -> Callable[[], None]:
        """Register callback for movement state changes."""
        self._movement_callbacks.append(callback)
        return lambda: self._movement_callbacks.remove(callback) if callback in self._movement_callbacks else None

    def register_connection_callback(self, callback: Callable[[bool], None]) -> Callable[[], None]:
        """Register callback for GATT link state changes."""
        self._connection_callbacks.append(callback)
        return lambda: self._connection_callbacks.remove(callback) if callback in self._connection_callbacks else None

    def _notify_connection_state(self) -> None:
        """Push the current link state to subscribers if it changed."""
        connected = self.is_connected
        if self._notified_connected == connected:
            return
        self._notified_connected = connected
        for cb in list(self._connection_callbacks):
            try:
                cb(connected)
            except Exception as err:
                _LOGGER.error("Error in connection callback: %s", err)

    def _on_client_disconnected(self, _client: Any, token: object = _NO_TOKEN) -> None:
        """Handle a link drop reported by the BLE stack.

        Without this, a link that dies on its own (device powered off, out of
        range, another central taking the single available slot) leaves every
        piece of derived state - notify subscription, movement, the
        connectivity entity - showing a session that no longer exists until
        the next command happens to fail.
        """
        if token is not _NO_TOKEN and token is not self._link_token:
            _LOGGER.debug("Ignoring a late drop event from a replaced link to %s", self.device_info.address)
            return
        _LOGGER.debug("BLE link to %s dropped by the stack", self.device_info.address)
        self._is_notifying = False
        if self._movement_timer_handle:
            self._movement_timer_handle.cancel()
            self._movement_timer_handle = None
        self._set_moving(False)
        # A command waiting for its answer will never get it: fail it now as a
        # dropped link rather than after command_timeout as a slow device.
        if self._current_waiter is not None and not self._current_waiter.done():
            self._current_waiter.set_exception(
                SessionDropped(f"The link to {self.device_info.address} dropped while waiting for the response")
            )
        self._notify_connection_state()

    def _set_moving(self, moving: bool) -> None:
        """Update moving state and notify callbacks."""
        if self._is_moving != moving:
            self._is_moving = moving
            for cb in list(self._movement_callbacks):
                try:
                    cb(moving)
                except Exception as err:
                    _LOGGER.error("Error in movement callback: %s", err)

    def _touch(self) -> None:
        """Record traffic activity and reset idle disconnect timer."""
        now = time.monotonic()
        loop = self._get_loop()

        if not self.keep_connected:
            # Check runaway session guard
            if self._session_start_time and (now - self._session_start_time > self.max_session_s):
                _LOGGER.warning(
                    "Session exceeded max duration (%.1fs) on %s, forcing disconnect",
                    self.max_session_s,
                    self.device_info.address,
                )
                if not self._session_guard_pending:
                    self._session_guard_pending = True
                    started = self._session_start_time
                    self._schedule_disconnect(lambda: self._session_start_time == started, guard=True)
                return

            if self._idle_timer_handle:
                self._idle_timer_handle.cancel()
            self._touch_generation += 1
            generation = self._touch_generation
            self._idle_timer_handle = loop.call_later(
                self.idle_disconnect_s,
                self._schedule_disconnect,
                lambda: generation == self._touch_generation,
            )

    def _schedule_disconnect(self, still_wanted: Callable[[], bool], guard: bool = False) -> None:
        """Schedule disconnect in background task."""
        loop = self._get_loop()
        task = loop.create_task(self._disconnect_when_idle(still_wanted, guard))
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

    async def _disconnect_when_idle(self, still_wanted: Callable[[], bool], guard: bool) -> None:
        """Disconnect once no command is using the link.

        Waiting for the session lock keeps the disconnect from tearing the
        link down under a connect or write that is in flight. Once it has the
        lock, ``still_wanted`` says whether the link is still the idle (or
        over-long) one this was scheduled for, and a queued command means it
        is not idle: that command must not be failed with "Disconnected".
        """
        try:
            async with self._session_lock:
                if not still_wanted() or self._pending_command is not None:
                    return
                await self.disconnect()
        finally:
            if guard:
                self._session_guard_pending = False

    def _on_notify(self, _characteristic: Any, data: bytearray | bytes) -> None:
        """Handle incoming GATT notify packet."""
        raw = bytes(data)
        _LOGGER.debug("GATT Notify from %s: %s", self.device_info.address, raw.hex())
        self._touch()

        resp = parse_response(raw)
        self._last_status = resp.status

        if resp.dps:
            _LOGGER.debug("Parsed %d DP(s) from %s: %s", len(resp.dps), self.device_info.address, resp.dps)

        # If device active streaming report (Opcode 24)
        if resp.method == Opcode.REPORT_DPS:
            self._set_moving(True)
            if self._movement_timer_handle:
                self._movement_timer_handle.cancel()
            loop = self._get_loop()
            self._movement_timer_handle = loop.call_later(
                self.movement_idle_s,
                lambda: self._set_moving(False),
            )
            for cb in list(self._report_callbacks):
                try:
                    cb(resp)
                except Exception as err:
                    _LOGGER.error("Error in report callback: %s", err)
            return

        # Standard command ack
        if self._current_waiter and not self._current_waiter.done():
            if self._current_method is None or resp.method == self._current_method:
                self._current_waiter.set_result(resp)

        for cb in list(self._report_callbacks):
            try:
                cb(resp)
            except Exception as err:
                _LOGGER.error("Error in report callback: %s", err)

    def _file_session(
        self,
        cmd: _QueuedCommand,
        trace: SessionTrace,
        exc: BaseException | None,
    ) -> None:
        """File one finished command's report, unless it does not count.

        A cancelled command is not an outcome. A status poll that dies at
        connect is the device being off or out of range between polls:
        counting it would climb on every interval and push the last real
        failure off the sensor, and a poll that succeeds is not news.
        """
        if isinstance(exc, asyncio.CancelledError):
            return
        if cmd.operation == OPERATION_POLL and (
            exc is None or trace.failed_primary in (stages.CONNECT, stages.UNREACHABLE)
        ):
            return
        if isinstance(exc, MiniBigDeviceError) and exc.status == StatusCode.DEVICE_SAME_DIRECTION:
            # Already where it was asked to go: the command's purpose is met.
            return
        try:
            if self.report_builder is None:
                raise LookupError("no report builder")
            report = self.report_builder(cmd.operation, trace, exc)
        except Exception as err:  # noqa: BLE001 - diagnostics must not mask the outcome
            _LOGGER.debug("Building the session report failed: %s", err)
            report = fallback_report(cmd.operation, trace=trace, exc=exc)
        self.reports.record(report)

    async def connect(self, trace: SessionTrace | None = None) -> None:
        """Establish BLE GATT connection and start notifications."""
        trace = trace if trace is not None else SessionTrace(stage_map=STAGE_MAP)
        if self.is_connected and self._is_notifying:
            # Reusing the live link: there is no connect stage, so say so, and
            # keep reporting the radio the link was opened over.
            trace.link = self._link
            trace.note(reused=True)
            return

        address = self.device_info.address
        _LOGGER.debug("Connecting to %s", address)

        async def _attempt_connect(*, first: bool, token: object) -> Any:
            if self._client_override is not None:
                if not self._client_override.is_connected:
                    with trace.timed("connect"):
                        await self._client_override.connect()
                return self._client_override
            # Re-resolve on every attempt, not once for the whole connect() call.
            # HA's own connectable-advertisement cache can be momentarily empty
            # (e.g. right after startup, or right after this device's stale link
            # was cleared) and later attempts - especially the recovery retry
            # after RECOVERY_WAIT_S - are specifically there to give it time to
            # repopulate. Reusing a stale (possibly None) lookup across attempts
            # defeats that wait entirely.
            ble_device = self._ble_device_callback() if self._ble_device_callback else None
            if ble_device is None:
                # No known-good fallback exists here: a bare BleakClient(address)
                # bypasses bleak-retry-connector's scanner routing and is
                # guaranteed to fail with a confusing "never seen by any
                # scanner" error even while HA's own scanners are actively
                # seeing the device, because it carries no scanner/backend
                # affinity at all. Fail with a clear message instead so the
                # caller's retry-with-recovery-wait path gets a real chance of
                # a fresh, successful lookup instead of a guaranteed failure.
                trace.fail(stages.UNREACHABLE)
                raise Unreachable(address)
            # keep=True: the link outlives this block and is ours to close
            # (idle timer / disconnect()). A previous handle that is no longer
            # up is closed by ble_session before it opens a fresh one, so a
            # dead link never keeps holding the device's single slot.
            async with ble_session(
                ble_device,
                trace=trace,
                name=self.device_info.name or address,
                client=self._client,
                keep=True,
                close_stale=first,
                disconnected_callback=partial(self._on_client_disconnected, token=token),
                max_attempts=self.retry_count,
            ) as client:
                return client

        previous = self._client
        token = object()
        try:
            self._client = await _attempt_connect(first=True, token=token)
            if self._client is not previous:
                self._link_token = token
        except Exception as first_exc:
            # The device accepts only one BLE link. A link that died without the
            # peer noticing leaves it advertising as non-connectable, which
            # surfaces here as anything from BleakOutOfConnectionSlotsError to a
            # plain connect timeout depending on platform/backend. Either way the
            # recovery is the same: clear the stale link and give the device a
            # moment to start advertising as connectable again before one retry.
            # blesession wraps the bleak error in ConnectFailed, so look at the cause too.
            if isinstance(first_exc, BleakOutOfConnectionSlotsError) or isinstance(
                first_exc.__cause__, BleakOutOfConnectionSlotsError
            ):
                _LOGGER.warning(
                    "BLE connection slots exhausted for %s, clearing stale link "
                    "and waiting %.0fs to retry",
                    address,
                    RECOVERY_WAIT_S,
                )
            else:
                _LOGGER.warning(
                    "Connect to %s failed (%s), clearing stale link and waiting "
                    "%.0fs to retry",
                    address,
                    first_exc,
                    RECOVERY_WAIT_S,
                )
            try:
                await close_stale_connections_by_address(address)
            except Exception:
                pass
            # Let the retry's own failure, not the first one, name the stage.
            first_stage = trace.failed_stage
            trace.forgive()
            if first_stage is not None:
                trace.note(first_failed_stage=first_stage)
            with trace.timed("recovery_wait"):
                await asyncio.sleep(RECOVERY_WAIT_S)
            previous = self._client
            token = object()
            try:
                self._client = await _attempt_connect(first=False, token=token)
                if self._client is not previous:
                    self._link_token = token
                # The first attempt failed but the recovery worked: the
                # command went on, so the report must not blame connect.
                trace.forgive()
                trace.note(connect_recovered=True)
            except Exception as exc:
                raise MiniBigConnectionError(
                    f"Failed to connect to {address} after stale-link recovery "
                    f"retry (first attempt: {first_exc}): {exc}"
                ) from exc

        # Subscribe to notify characteristic
        try:
            with trace.timed("subscribe"):
                await self._client.start_notify(self.device_info.notify_uuid, self._on_notify)
            self._is_notifying = True
        except Exception as exc:
            # A command queued meanwhile has not run yet: leave it for the
            # next loop instead of failing it with "Disconnected".
            await self.disconnect(fail_pending=False)
            raise MiniBigConnectionError(
                f"Failed to subscribe to notify on {address}: {exc}"
            ) from exc

        self._link = trace.link
        self._session_start_time = time.monotonic()
        self._touch()
        self._notify_connection_state()
        _LOGGER.debug("Connected and notifications enabled for %s", address)

    async def disconnect(self, *, fail_pending: bool = True) -> None:
        """Disconnect BLE connection and cancel all timers and in-flight waiters.

        ``fail_pending=False`` leaves a queued command alone, for cleanup done
        by the worker itself between two commands.
        """
        if self._idle_timer_handle:
            self._idle_timer_handle.cancel()
            self._idle_timer_handle = None

        if self._movement_timer_handle:
            self._movement_timer_handle.cancel()
            self._movement_timer_handle = None

        self._set_moving(False)
        self._session_start_time = None
        self._is_notifying = False
        self._link = None
        self._link_token = None

        # Cancel pending queued command
        if fail_pending and self._pending_command and not self._pending_command.user_future.done():
            self._pending_command.user_future.set_exception(MiniBigConnectionError("Disconnected"))
            self._pending_command = None

        # Cancel current in-flight waiter
        if self._current_waiter and not self._current_waiter.done():
            self._current_waiter.cancel()
            self._current_waiter = None
            self._current_method = None

        if self._client:
            client = self._client
            if self._client_override is None:
                self._client = None
            try:
                if client.is_connected:
                    # Bounded: this can run holding the session lock, and a
                    # proxy that hung the session can hang the close too.
                    async with asyncio.timeout(DISCONNECT_TIMEOUT_S):
                        await client.disconnect()
            except Exception as err:
                _LOGGER.debug("Error disconnecting %s: %s", self.device_info.address, err)

        self._notify_connection_state()
        _LOGGER.debug("Disconnected from %s", self.device_info.address)

    async def close(self) -> None:
        """Stop for good: refuse new commands, stop the worker, drop the link.

        Used on unload. Plain disconnect() leaves a worker that is in the
        middle of connecting free to finish and leave a fresh link behind,
        which would keep holding the device's single slot.
        """
        self._closing = True
        # A queued command must not start a new connect while we shut down.
        if self._pending_command is not None and not self._pending_command.user_future.done():
            self._pending_command.user_future.set_exception(MiniBigConnectionError("Connection is closed"))
        self._pending_command = None
        worker = self._worker_task
        if worker is not None and not worker.done():
            worker.cancel()
            await asyncio.gather(worker, return_exceptions=True)
        if self._inflight_command is not None and not self._inflight_command.user_future.done():
            self._inflight_command.user_future.set_exception(MiniBigConnectionError("Connection is closed"))
        self._inflight_command = None
        await self.disconnect()

    async def send_frame(
        self,
        frame: bytes,
        expected_method: int,
        timeout: float | None = None,
        operation: str = OPERATION_COMMAND,
    ) -> Response:
        """Queue and execute a command frame with strict single-slot coalescing.

        ``operation`` names the caller (poll / command / service) in the
        session report; it does not change how the frame is sent.
        """
        if self._closing:
            raise MiniBigConnectionError("Connection is closed")
        timeout_val = timeout if timeout is not None else self.command_timeout
        loop = self._get_loop()
        user_future: asyncio.Future[Response] = loop.create_future()

        # Coalescing: Replace previous pending command if one exists
        if self._pending_command and not self._pending_command.user_future.done():
            _LOGGER.debug(
                "Coalescing: replacing previous pending command (opcode %s) with new opcode %s on %s",
                self._pending_command.expected_method,
                expected_method,
                self.device_info.address,
            )
            self._pending_command.user_future.set_exception(
                MiniBigSupersededError(
                    f"Command (opcode {self._pending_command.expected_method}) superseded by newer opcode {expected_method}"
                )
            )

        self._pending_command = _QueuedCommand(
            frame=frame,
            expected_method=expected_method,
            timeout=timeout_val,
            user_future=user_future,
            operation=operation,
        )

        # Trigger worker task if not already running
        self._ensure_worker()

        return await user_future

    def _ensure_worker(self) -> None:
        """Ensure the command execution worker is running."""
        if self._worker_task is None or self._worker_task.done():
            loop = self._get_loop()
            self._worker_task = loop.create_task(self._process_command_queue())
            self._background_tasks.add(self._worker_task)
            self._worker_task.add_done_callback(self._background_tasks.discard)

    async def _process_command_queue(self) -> None:
        """Worker loop that executes queued commands one by one, picking only the latest."""
        loop = self._get_loop()
        async with self._session_lock:
            while self._pending_command is not None and not self._closing:
                cmd = self._pending_command
                self._pending_command = None

                if cmd.user_future.done():
                    continue

                self._inflight_command = cmd
                trace = SessionTrace(stage_map=STAGE_MAP)
                try:
                    await self.connect(trace)
                except Exception as exc:
                    self._file_session(cmd, trace, exc)
                    if not cmd.user_future.done():
                        cmd.user_future.set_exception(exc)
                    continue

                internal_future: asyncio.Future[Response] = loop.create_future()
                # A drop during the write sets an exception nobody awaits yet;
                # retrieve it so asyncio does not log it as never retrieved.
                internal_future.add_done_callback(lambda f: f.cancelled() or f.exception())
                self._current_waiter = internal_future
                self._current_method = cmd.expected_method

                # Write frame to characteristic
                try:
                    with trace.timed("write"):
                        async with self._write_lock:
                            _LOGGER.debug("GATT Write to %s: %s", self.device_info.address, cmd.frame.hex())
                            chunk_size = 20
                            for i in range(0, len(cmd.frame), chunk_size):
                                chunk = cmd.frame[i : i + chunk_size]
                                await self._client.write_gatt_char(
                                    self.device_info.write_uuid,
                                    chunk,
                                    response=False,
                                )
                            self._touch()
                except Exception as exc:
                    self._current_waiter = None
                    self._current_method = None
                    error = MiniBigConnectionError(
                        f"Failed writing command to {self.device_info.address}: {exc}"
                    )
                    error.__cause__ = exc
                    self._file_session(cmd, trace, error)
                    if not cmd.user_future.done():
                        cmd.user_future.set_exception(error)
                    continue

                # Wait for matching response
                try:
                    with trace.timed("response"):
                        resp = await asyncio.wait_for(internal_future, timeout=cmd.timeout)
                except asyncio.TimeoutError:
                    error = MiniBigTimeoutError(
                        f"Timeout ({cmd.timeout}s) waiting for response (opcode {cmd.expected_method}) from {self.device_info.address}"
                    )
                    self._file_session(cmd, trace, error)
                    if not cmd.user_future.done():
                        cmd.user_future.set_exception(error)
                    continue
                except asyncio.CancelledError:
                    if not cmd.user_future.done():
                        if self._closing:
                            # Unload: callers get an ordinary error, not a cancellation.
                            cmd.user_future.set_exception(MiniBigConnectionError("Connection is closed"))
                        else:
                            cmd.user_future.cancel()
                    continue
                except Exception as exc:
                    self._file_session(cmd, trace, exc)
                    if not cmd.user_future.done():
                        cmd.user_future.set_exception(exc)
                    continue
                finally:
                    self._current_waiter = None
                    self._current_method = None

                # Check status code and fulfill user future
                if not resp.ok:
                    msg = STATUS_MESSAGES.get(resp.status, "Unknown device error")
                    error = MiniBigDeviceError(resp.status, msg)
                    # The exchange completed; the device refused it.
                    trace.fail("response")
                    self._file_session(cmd, trace, error)
                    if not cmd.user_future.done():
                        cmd.user_future.set_exception(error)
                else:
                    self._file_session(cmd, trace, None)
                    if not cmd.user_future.done():
                        cmd.user_future.set_result(resp)

    async def send_dps(
        self,
        dps: list[tuple[int, int]],
        timeout: float | None = None,
        operation: str = OPERATION_COMMAND,
    ) -> Response:
        """Send PUB_DPS command to set DP values."""
        frame = build_pub_dps(self.device_info, dps)
        expected_method = frame[0]
        return await self.send_frame(frame, expected_method, timeout=timeout, operation=operation)

    async def read_dps(
        self,
        timeout: float | None = None,
        operation: str = OPERATION_COMMAND,
    ) -> Response:
        """Send READ_DPS command to get current DP values."""
        frame = build_read_dps(self.device_info)
        expected_method = frame[0]
        return await self.send_frame(frame, expected_method, timeout=timeout, operation=operation)

    async def restart(self, timeout: float | None = None) -> Response:
        """Send device restart command."""
        frame = build_restart(self.device_info)
        return await self.send_frame(frame, frame[0], timeout=timeout)

    async def factory_reset(self, timeout: float | None = None) -> Response:
        """Send device factory reset command."""
        frame = build_manu_reset(self.device_info)
        return await self.send_frame(frame, frame[0], timeout=timeout)

    async def send_raw(
        self,
        method: int,
        payload: bytes = b"",
        timeout: float | None = None,
        operation: str = OPERATION_SERVICE,
    ) -> Response:
        """Send an arbitrary raw command frame for diagnostics or testing."""
        frame = build_frame(method, self.device_info.idv, payload)
        return await self.send_frame(frame, method, timeout=timeout, operation=operation)
