"""Constants for MiniBig BLE protocol."""

from __future__ import annotations

from enum import IntEnum

# Service & Characteristic UUIDs
DEVICE_SERVICE_UUID = "2b8d0001-6828-46af-98aa-557761b15400"
DEVICE_WRITE_UUID = "2b8d0002-6828-46af-98aa-557761b15400"
DEVICE_NOTIFY_UUID = "2b8d0003-6828-46af-98aa-557761b15400"

HUBMINI_SERVICE_UUID = "c7d71110-5878-4934-9db6-f1d1cc845b2c"
HUBMINI_WRITE_UUID = "c7d71111-5878-4934-9db6-f1d1cc845b2c"
HUBMINI_NOTIFY_UUID = "c7d71112-5878-4934-9db6-f1d1cc845b2c"

# Pass key for IDV obfuscation (XOR)
PASS_KEY = bytes([0x66, 0x39])


class Opcode(IntEnum):
    """MiniBig command opcodes."""

    REG = 1
    ACTION = 2  # legacy
    SETTING = 3  # legacy
    READ_SETTING = 4  # legacy
    TIMER_SAVE = 5  # legacy
    TIMER_READ = 6  # legacy
    TIMER_DELETE = 7  # legacy
    MANU_RESET = 8  # legacy
    RESTART = 17
    SET_WIFI_DATA = 18
    UNDEFINED_MSG = 20
    ACTION_BLE = 21
    REPORT_DPS = 24  # Device active status report (streaming)
    CONFIRM_BLE = 27
    HUB_CONFIRM_SERVER_BLE = 28
    BOOT = 30
    SET_WIFI = 38
    PUB_DPS = 42
    READ_DPS = 43
    TIMER_SAVE_NEW = 44
    TIMER_READ_NEW = 45
    TIMER_DELETE_NEW = 46
    MANU_RESET_NEW = 47
    CENTRAL_SAVE = 48
    CENTRAL_READ = 49
    CENTRAL_DELETE = 50


class StatusCode(IntEnum):
    """MiniBig response status codes (byte 1)."""

    DEVICE_SUCCESS = 253
    DEVICE_BUSY = 254
    DEVICE_NOT_MATCHING = 255
    DEVICE_NOT_INITIAL = 252
    DEVICE_SAME_DIRECTION = 251
    DEVICE_EXCEED_TIMER_NUM = 238
    DEVICE_UNAUTH = 102
    BLE_RECEIVED_INVALID_DATA = 209


STATUS_MESSAGES: dict[int, str] = {
    StatusCode.DEVICE_SUCCESS: "Success",
    StatusCode.DEVICE_BUSY: "Device busy",
    StatusCode.DEVICE_NOT_MATCHING: "Device matching error (IDV mismatch)",
    StatusCode.DEVICE_NOT_INITIAL: "Device not initialized",
    StatusCode.DEVICE_SAME_DIRECTION: "Device already moving in requested direction",
    StatusCode.DEVICE_EXCEED_TIMER_NUM: "Exceeded timer capacity",
    StatusCode.DEVICE_UNAUTH: "Unauthorized",
    StatusCode.BLE_RECEIVED_INVALID_DATA: "Invalid response data",
}
