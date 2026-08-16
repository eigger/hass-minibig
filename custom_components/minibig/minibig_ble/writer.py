"""Frame builder and response parser for MiniBig BLE protocol (Pure functions)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from .const import PASS_KEY, Opcode, StatusCode
from .parser import MiniBigDeviceInfo

DPS_OPCODES = {Opcode.PUB_DPS, Opcode.READ_DPS, Opcode.REPORT_DPS}


@dataclass(frozen=True)
class TimerSpec:
    """Timer specification for MiniBig devices."""

    t_id: int
    dp_id: int
    value: int
    hour: int
    minute: int
    weekdays: list[int] | None = None  # 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun
    is_single_shot: bool = False
    activated: bool = True


@dataclass(frozen=True)
class Response:
    """Parsed GATT response from MiniBig device."""

    method: int
    status: int
    data: bytes
    ok: bool
    dps: dict[int, int] = field(default_factory=dict)


def _get_local_epoch(now: datetime) -> int:
    """Calculate 4-byte local epoch (big-endian). Requires timezone-aware datetime."""
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("datetime must be timezone-aware with valid utcoffset (got naive datetime)")
    offset = now.utcoffset().total_seconds()
    return int(now.timestamp() + offset)


def _build_weekday_mask(weekdays: list[int] | None, is_single_shot: bool) -> int:
    """Build weekday bitmask. Mon=0x80 ... Sun=0x02, single-shot=0xFF."""
    if is_single_shot or not weekdays:
        return 0xFF
    mask = 0
    for day in weekdays:
        if 0 <= day <= 6:
            mask |= 1 << (7 - day)
    return mask


def build_frame(method: int, idv: str, payload: bytes = b"") -> bytes:
    """Build a raw MiniBig GATT command frame."""
    idv_clean = idv.strip().replace(":", "").replace(" ", "")
    if len(idv_clean) != 4:
        raise ValueError(f"Invalid IDV length ({len(idv_clean)}), expected 4 hex chars: {idv}")

    idv_bytes = bytes.fromhex(idv_clean)
    idv_xor = bytes([idv_bytes[0] ^ PASS_KEY[0], idv_bytes[1] ^ PASS_KEY[1]])
    return bytes([method]) + idv_xor + payload


def has_back_power(rev: int, fv: int) -> bool:
    """Check if legacy Push device firmware revision supports back power byte."""
    return rev != 0 and not (rev == 1 and fv < 9) and not (rev == 2 and fv < 5) and not (rev == 3 and fv < 5)


def build_legacy_setting(
    dev: MiniBigDeviceInfo,
    is_on: int = 0,
    rotate: int = 0,
    mode: int = 0,
    direction: int = 0,
    m_power: int = 0,
    delay_time: int = 0,
    b_power: int = 2,
) -> bytes:
    """Build legacy SETTING (opcode 3) bitfield frame according to §1 spec."""
    back_power_enabled = has_back_power(dev.rev, dev.fv)

    # When has_back_power is True, byte0's mPower slot is set to 0 and moved to byte1
    m_power_slot = 0 if back_power_enabled else (m_power & 0x03)
    byte0 = (
        ((rotate & 0x01) << 7)
        | ((mode & 0x01) << 6)
        | ((direction & 0x01) << 5)
        | ((is_on & 0x01) << 4)
        | (m_power_slot << 2)
        | (delay_time & 0x03)
    )

    if back_power_enabled:
        byte1 = ((b_power & 0x07) << 3) | (m_power & 0x07)
        payload = bytes([byte0, byte1])
    else:
        payload = bytes([byte0])

    return build_frame(Opcode.SETTING, dev.idv, payload)


def build_pub_dps(dev: MiniBigDeviceInfo, dps: list[tuple[int, int]]) -> bytes:
    """Build PUB_DPS command frame for setting DP values."""
    if not dps:
        raise ValueError("DPS list cannot be empty")

    if dev.is_legacy:
        if len(dps) > 1:
            raise ValueError("Legacy Push devices do not support multiple DPs in a single command")
        dp_id, val = dps[0]
        if dp_id == 0:
            # On/Off action (dp0 -> opcode 2)
            is_on = bool(val)
            return build_frame(Opcode.ACTION, dev.idv, bytes([1 if is_on else 0]))
        raise ValueError(
            f"Legacy Push devices only support dp0 for on/off via build_pub_dps (got dp{dp_id}). "
            "Use build_legacy_setting() for device configuration."
        )

    # Modern PUB_DPS (opcode 42)
    payload = bytearray()
    for dp_id, val in dps:
        val_u16 = val & 0xFFFF
        payload.extend([dp_id & 0xFF, (val_u16 >> 8) & 0xFF, val_u16 & 0xFF])
    return build_frame(Opcode.PUB_DPS, dev.idv, bytes(payload))


def build_read_dps(dev: MiniBigDeviceInfo) -> bytes:
    """Build command frame to read device DPs."""
    if dev.is_legacy:
        return build_frame(Opcode.READ_SETTING, dev.idv)
    return build_frame(Opcode.READ_DPS, dev.idv)


def build_restart(dev: MiniBigDeviceInfo) -> bytes:
    """Build device restart command frame."""
    return build_frame(Opcode.RESTART, dev.idv)


def build_manu_reset(dev: MiniBigDeviceInfo) -> bytes:
    """Build factory reset command frame."""
    if dev.is_legacy:
        return build_frame(Opcode.MANU_RESET, dev.idv)
    return build_frame(Opcode.MANU_RESET_NEW, dev.idv)


def build_timer_save(dev: MiniBigDeviceInfo, timer: TimerSpec, now: datetime) -> bytes:
    """Build timer save command frame."""
    mask = _build_weekday_mask(timer.weekdays, timer.is_single_shot)
    minutes = (timer.hour * 60 + timer.minute) & 0xFFFF
    local_epoch = _get_local_epoch(now)
    epoch_bytes = local_epoch.to_bytes(4, "big")

    if dev.is_legacy:
        # Legacy timer save (opcode 5)
        val_bit = 1 if timer.value else 0
        act_bit = 1 if timer.activated else 0
        t_id_bits = timer.t_id & 0x07
        min_hi = (minutes >> 8) & 0x07
        b0 = (val_bit << 7) | (act_bit << 6) | (t_id_bits << 3) | min_hi
        b1 = minutes & 0xFF
        b2 = mask
        return build_frame(Opcode.TIMER_SAVE, dev.idv, bytes([b0, b1, b2]) + epoch_bytes)

    # Modern timer save (opcode 44)
    act_bit = 1 if timer.activated else 0
    b0 = (act_bit << 7) | (timer.t_id & 0x7F)
    b1 = timer.dp_id & 0xFF
    val_u16 = timer.value & 0xFFFF
    b2_b3 = bytes([(val_u16 >> 8) & 0xFF, val_u16 & 0xFF])
    b4_b5 = bytes([(minutes >> 8) & 0xFF, minutes & 0xFF])
    b6 = mask
    return build_frame(
        Opcode.TIMER_SAVE_NEW,
        dev.idv,
        bytes([b0, b1]) + b2_b3 + b4_b5 + bytes([b6]) + epoch_bytes,
    )


def build_timer_read(dev: MiniBigDeviceInfo, now: datetime) -> bytes:
    """Build timer read command frame."""
    local_epoch = _get_local_epoch(now)
    epoch_bytes = local_epoch.to_bytes(4, "big")
    if dev.is_legacy:
        return build_frame(Opcode.TIMER_READ, dev.idv, epoch_bytes)
    return build_frame(Opcode.TIMER_READ_NEW, dev.idv, epoch_bytes)


def build_timer_delete(dev: MiniBigDeviceInfo, t_id: int) -> bytes:
    """Build timer delete command frame."""
    if dev.is_legacy:
        return build_frame(Opcode.TIMER_DELETE, dev.idv, bytes([t_id & 0xFF]))
    return build_frame(Opcode.TIMER_DELETE_NEW, dev.idv, bytes([t_id & 0xFF]))


def parse_response(raw: bytes) -> Response:
    """Parse GATT notify response into Response object."""
    if len(raw) < 2:
        return Response(
            method=raw[0] if len(raw) == 1 else 0,
            status=StatusCode.BLE_RECEIVED_INVALID_DATA,
            data=raw,
            ok=False,
            dps={},
        )

    method = raw[0]
    status = raw[1]
    data = raw[2:]
    ok = status == StatusCode.DEVICE_SUCCESS

    dps: dict[int, int] = {}
    # Only the DPS opcodes carry triplets. Legacy ACTION/SETTING/READ_SETTING bodies
    # are deliberately left undecoded: the vendor client does not decode them either,
    # and guessing a bitfield layout would report a confident but unfounded state.
    # Callers get the raw body via Response.data.
    if ok and method in DPS_OPCODES and len(data) >= 3:
        idx = 0
        while idx + 3 <= len(data):
            dp_id = data[idx]
            val = (data[idx + 1] << 8) | data[idx + 2]
            dps[dp_id] = val
            idx += 3

    return Response(method=method, status=status, data=data, ok=ok, dps=dps)
