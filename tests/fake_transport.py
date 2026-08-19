"""Fake BleakClient transport for unit testing MiniBig BLE client."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any


class FakeBleakClient:
    """Mock BleakClient that simulates BLE GATT operations."""

    def __init__(
        self,
        address: str = "11:22:33:44:55:66",
        fail_connect: bool = False,
        slot_error_once: bool = False,
        generic_error_once: bool = False,
    ) -> None:
        """Initialize fake client."""
        self.address = address
        self._is_connected = False
        self.fail_connect = fail_connect
        self.slot_error_once = slot_error_once
        self._slot_error_occurred = False
        self.generic_error_once = generic_error_once
        self._generic_error_occurred = False

        self.written_frames: list[bytes] = []
        self.notify_callbacks: dict[str, Callable[[Any, bytearray], None]] = {}
        self.response_generator: Callable[[bytes], bytes | None] | None = None

    @property
    def is_connected(self) -> bool:
        """Return connection state."""
        return self._is_connected

    async def connect(self) -> bool:
        """Simulate connect."""
        if self.slot_error_once and not self._slot_error_occurred:
            self._slot_error_occurred = True
            from custom_components.minibig.minibig_ble.client import BleakOutOfConnectionSlotsError
            raise BleakOutOfConnectionSlotsError("No free connection slots")

        if self.generic_error_once and not self._generic_error_occurred:
            self._generic_error_occurred = True
            raise TimeoutError("Timeout waiting for connect response")

        if self.fail_connect:
            raise ConnectionError("Failed to connect")

        self._is_connected = True
        return True

    async def disconnect(self) -> bool:
        """Simulate disconnect."""
        self._is_connected = False
        return True

    async def start_notify(
        self,
        char_specifier: str,
        callback: Callable[[Any, bytearray], None],
    ) -> None:
        """Register notify callback."""
        if not self._is_connected:
            raise ConnectionError("Not connected")
        self.notify_callbacks[char_specifier.lower()] = callback

    async def stop_notify(self, char_specifier: str) -> None:
        """Unregister notify callback."""
        self.notify_callbacks.pop(char_specifier.lower(), None)

    async def write_gatt_char(
        self,
        char_specifier: str,
        data: bytes | bytearray,
        response: bool = False,
    ) -> None:
        """Record written frame and optionally generate mock notification response."""
        if not self._is_connected:
            raise ConnectionError("Not connected")

        raw = bytes(data)
        self.written_frames.append(raw)

        if self.response_generator:
            resp_bytes = self.response_generator(raw)
            if resp_bytes:
                # Trigger notify asynchronously
                for cb in self.notify_callbacks.values():
                    asyncio.get_running_loop().call_soon(cb, None, bytearray(resp_bytes))

    def trigger_notify(self, data: bytes, char_uuid: str | None = None) -> None:
        """Manually trigger incoming notify (e.g. REPORT_DPS streaming)."""
        for uuid, cb in self.notify_callbacks.items():
            if char_uuid is None or uuid == char_uuid.lower():
                cb(None, bytearray(data))
