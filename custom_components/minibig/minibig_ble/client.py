"""BLE transaction client for MiniBig devices with command coalescing."""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from bleak import BleakClient
from bleak.exc import BleakError

try:
    from bleak_retry_connector import (
        BleakOutOfConnectionSlotsError,
        close_stale_connections_by_address,
        establish_connection,
    )
except ImportError:
    class BleakOutOfConnectionSlotsError(BleakError):  # type: ignore[no-redef]
        """Fallback BleakOutOfConnectionSlotsError."""

    async def close_stale_connections_by_address(address: str) -> None:
        """Fallback close stale connections."""
        pass

    async def establish_connection(
        client_class: Any,
        device: Any,
        name: str,
        max_attempts: int = 3,
        **kwargs: Any,
    ) -> Any:
        """Fallback establish connection."""
        client = client_class(device)
        await client.connect()
        return client

from .const import STATUS_MESSAGES, Opcode
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

        self._client_override = client_override
        self._client: BleakClient | Any | None = client_override

        # Coalescing slot: holds at most 1 pending command, newer commands overwrite older
        self._pending_command: _QueuedCommand | None = None
        self._worker_task: asyncio.Task[None] | None = None
        self._session_lock = asyncio.Lock()
        self._write_lock = asyncio.Lock()

        self._idle_timer_handle: asyncio.TimerHandle | None = None
        self._movement_timer_handle: asyncio.TimerHandle | None = None
        self._session_start_time: float | None = None

        self._current_waiter: asyncio.Future[Response] | None = None
        self._current_method: int | None = None

        self._report_callbacks: list[Callable[[Response], None]] = []
        self._movement_callbacks: list[Callable[[bool], None]] = []
        self._background_tasks: set[asyncio.Task[Any]] = set()

        self._is_moving: bool = False
        self._last_status: int | None = None
        self._is_notifying: bool = False

    def _get_loop(self) -> asyncio.AbstractEventLoop:
        """Get the active event loop."""
        if self._loop is not None:
            return self._loop
        try:
            return asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.get_event_loop()

    @property
    def is_connected(self) -> bool:
        """Return True if BLE client is connected."""
        return self._client is not None and self._client.is_connected

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
                self._schedule_disconnect()
                return

            if self._idle_timer_handle:
                self._idle_timer_handle.cancel()
            self._idle_timer_handle = loop.call_later(
                self.idle_disconnect_s,
                self._schedule_disconnect,
            )

    def _schedule_disconnect(self) -> None:
        """Schedule disconnect in background task."""
        loop = self._get_loop()
        task = loop.create_task(self.disconnect())
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

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

    async def connect(self) -> None:
        """Establish BLE GATT connection and start notifications."""
        if self.is_connected and self._is_notifying:
            return

        address = self.device_info.address
        _LOGGER.debug("Connecting to %s", address)

        # Clear any stale connection prior to connecting
        try:
            await close_stale_connections_by_address(address)
        except Exception:
            pass

        ble_device = self._ble_device_callback() if self._ble_device_callback else None

        async def _attempt_connect() -> Any:
            if self._client_override is not None:
                await self._client_override.connect()
                return self._client_override
            if ble_device:
                client = await establish_connection(
                    BleakClient,
                    ble_device,
                    self.device_info.name or address,
                    max_attempts=self.retry_count,
                )
            else:
                client = BleakClient(address)
                await client.connect()
            return client

        try:
            if self._client is None or not self._client.is_connected:
                self._client = await _attempt_connect()
        except BleakOutOfConnectionSlotsError:
            _LOGGER.warning(
                "BLE connection slots exhausted for %s, waiting 12s to retry",
                address,
            )
            try:
                await close_stale_connections_by_address(address)
            except Exception:
                pass
            await asyncio.sleep(12.0)
            try:
                self._client = await _attempt_connect()
            except Exception as exc:
                raise MiniBigConnectionError(
                    f"Failed to connect to {address} after slot exhaustion retry: {exc}"
                ) from exc
        except Exception as exc:
            raise MiniBigConnectionError(f"Failed to connect to {address}: {exc}") from exc

        # Subscribe to notify characteristic
        try:
            await self._client.start_notify(self.device_info.notify_uuid, self._on_notify)
            self._is_notifying = True
        except Exception as exc:
            await self.disconnect()
            raise MiniBigConnectionError(
                f"Failed to subscribe to notify on {address}: {exc}"
            ) from exc

        self._session_start_time = time.monotonic()
        self._touch()
        _LOGGER.debug("Connected and notifications enabled for %s", address)

    async def disconnect(self) -> None:
        """Disconnect BLE connection and cancel all timers and in-flight waiters."""
        if self._idle_timer_handle:
            self._idle_timer_handle.cancel()
            self._idle_timer_handle = None

        if self._movement_timer_handle:
            self._movement_timer_handle.cancel()
            self._movement_timer_handle = None

        self._set_moving(False)
        self._session_start_time = None
        self._is_notifying = False

        # Cancel pending queued command
        if self._pending_command and not self._pending_command.user_future.done():
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
                    await client.disconnect()
            except Exception as err:
                _LOGGER.debug("Error disconnecting %s: %s", self.device_info.address, err)

        _LOGGER.debug("Disconnected from %s", self.device_info.address)

    async def send_frame(
        self,
        frame: bytes,
        expected_method: int,
        timeout: float | None = None,
    ) -> Response:
        """Queue and execute a command frame with strict single-slot coalescing."""
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
            while self._pending_command is not None:
                cmd = self._pending_command
                self._pending_command = None

                if cmd.user_future.done():
                    continue

                try:
                    await self.connect()
                except Exception as exc:
                    if not cmd.user_future.done():
                        cmd.user_future.set_exception(exc)
                    continue

                internal_future: asyncio.Future[Response] = loop.create_future()
                self._current_waiter = internal_future
                self._current_method = cmd.expected_method

                # Write frame to characteristic
                try:
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
                    if not cmd.user_future.done():
                        cmd.user_future.set_exception(
                            MiniBigConnectionError(
                                f"Failed writing command to {self.device_info.address}: {exc}"
                            )
                        )
                    continue

                # Wait for matching response
                try:
                    resp = await asyncio.wait_for(internal_future, timeout=cmd.timeout)
                except asyncio.TimeoutError:
                    if not cmd.user_future.done():
                        cmd.user_future.set_exception(
                            MiniBigTimeoutError(
                                f"Timeout ({cmd.timeout}s) waiting for response (opcode {cmd.expected_method}) from {self.device_info.address}"
                            )
                        )
                    continue
                except asyncio.CancelledError:
                    if not cmd.user_future.done():
                        cmd.user_future.cancel()
                    continue
                except Exception as exc:
                    if not cmd.user_future.done():
                        cmd.user_future.set_exception(exc)
                    continue
                finally:
                    self._current_waiter = None
                    self._current_method = None

                # Check status code and fulfill user future
                if not resp.ok:
                    msg = STATUS_MESSAGES.get(resp.status, "Unknown device error")
                    if not cmd.user_future.done():
                        cmd.user_future.set_exception(MiniBigDeviceError(resp.status, msg))
                else:
                    if not cmd.user_future.done():
                        cmd.user_future.set_result(resp)

    async def send_dps(self, dps: list[tuple[int, int]], timeout: float | None = None) -> Response:
        """Send PUB_DPS command to set DP values."""
        frame = build_pub_dps(self.device_info, dps)
        expected_method = frame[0]
        return await self.send_frame(frame, expected_method, timeout=timeout)

    async def read_dps(self, timeout: float | None = None) -> Response:
        """Send READ_DPS command to get current DP values."""
        frame = build_read_dps(self.device_info)
        expected_method = frame[0]
        return await self.send_frame(frame, expected_method, timeout=timeout)

    async def restart(self, timeout: float | None = None) -> Response:
        """Send device restart command."""
        frame = build_restart(self.device_info)
        return await self.send_frame(frame, frame[0], timeout=timeout)

    async def factory_reset(self, timeout: float | None = None) -> Response:
        """Send device factory reset command."""
        frame = build_manu_reset(self.device_info)
        return await self.send_frame(frame, frame[0], timeout=timeout)

    async def send_raw(self, method: int, payload: bytes = b"", timeout: float | None = None) -> Response:
        """Send an arbitrary raw command frame for diagnostics or testing."""
        frame = build_frame(method, self.device_info.idv, payload)
        return await self.send_frame(frame, method, timeout=timeout)
