"""Advertisement parser for MiniBig BLE devices."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from .const import (
    DEVICE_NOTIFY_UUID,
    DEVICE_SERVICE_UUID,
    DEVICE_WRITE_UUID,
    HUBMINI_NOTIFY_UUID,
    HUBMINI_SERVICE_UUID,
    HUBMINI_WRITE_UUID,
)

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class MiniBigDeviceInfo:
    """Parsed MiniBig BLE device advertisement information."""

    address: str
    name: str
    idv: str
    fv: int
    rev: int
    d_type: int
    init_mode: bool
    is_legacy: bool
    service_uuid: str
    write_uuid: str
    notify_uuid: str
    supported: bool = True
    rssi: int | None = None


def parse_advertisement(service_info: Any) -> MiniBigDeviceInfo | None:
    """Parse BLE advertisement into MiniBigDeviceInfo without external dependencies."""
    service_uuids = getattr(service_info, "service_uuids", None)
    if service_uuids is None and isinstance(service_info, dict):
        service_uuids = service_info.get("service_uuids", [])

    # Normalize UUIDs to lowercase
    uuids_lower = {str(u).lower() for u in service_uuids} if service_uuids else set()

    is_device = DEVICE_SERVICE_UUID.lower() in uuids_lower
    is_hubmini = HUBMINI_SERVICE_UUID.lower() in uuids_lower

    # Some devices (e.g. CLWM-B06) advertise without service UUIDs; fall back to
    # name-based detection so they are still recognised via the manifest local_name matcher.
    name_for_check = getattr(service_info, "name", None) or getattr(service_info, "local_name", None)
    if name_for_check is None and isinstance(service_info, dict):
        name_for_check = service_info.get("name") or service_info.get("local_name") or ""
    name_lower_check = str(name_for_check or "").lower()

    is_name_match = name_lower_check.startswith("clwm") or name_lower_check.startswith("clpm")
    if not is_name_match and not is_device and not is_hubmini:
        return None

    # For name-only matches treat as a standard device (not HubMini)
    if not is_device and not is_hubmini and is_name_match:
        is_device = True

    address = getattr(service_info, "address", None)
    if address is None and isinstance(service_info, dict):
        address = service_info.get("address", "")

    name = getattr(service_info, "name", None) or getattr(service_info, "local_name", None)
    if name is None and isinstance(service_info, dict):
        name = service_info.get("name") or service_info.get("local_name") or ""
    name = str(name or address or "MiniBig")

    rssi = getattr(service_info, "rssi", None)
    if rssi is None and isinstance(service_info, dict):
        rssi = service_info.get("rssi")

    service_uuid = DEVICE_SERVICE_UUID if is_device else HUBMINI_SERVICE_UUID
    write_uuid = DEVICE_WRITE_UUID if is_device else HUBMINI_WRITE_UUID
    notify_uuid = DEVICE_NOTIFY_UUID if is_device else HUBMINI_NOTIFY_UUID
    supported = is_device  # HubMini is not supported directly in HA

    manu_data = getattr(service_info, "manufacturer_data", None)
    if manu_data is None and isinstance(service_info, dict):
        manu_data = service_info.get("manufacturer_data", {})

    raw_manu: bytes | None = None
    if isinstance(manu_data, dict) and manu_data:
        # Reconstruct full manufacturer data including 2-byte company ID (little-endian)
        for cid, payload in manu_data.items():
            if isinstance(cid, int) and isinstance(payload, (bytes, bytearray)):
                reconstructed = cid.to_bytes(2, "little") + bytes(payload)
                # Look for valid MiniBig advertisement length
                if len(reconstructed) >= 12:
                    raw_manu = reconstructed
                    break
        if raw_manu is None:
            # Fallback to first available entry
            for cid, payload in manu_data.items():
                if isinstance(cid, int) and isinstance(payload, (bytes, bytearray)):
                    raw_manu = cid.to_bytes(2, "little") + bytes(payload)
                    break
    elif isinstance(manu_data, (bytes, bytearray)):
        raw_manu = bytes(manu_data)

    has_clpm = "clpm" in name.lower()

    has_clwm = name.lower().startswith("clwm")

    try:
        if raw_manu is None or len(raw_manu) < 3:
            if not has_clpm and not has_clwm:
                return None
            init_mode = False
            fv = 0
            rev = 0
            idv = "0000"
            d_type = 1 if has_clpm else 5
        else:
            byte2 = raw_manu[2]
            init_mode = bool(byte2 & 0x01)
            fv = (byte2 & 0x3E) >> 1
            rev = (byte2 >> 6) & 0x03

            # According to spec: if length < 12, idv is "0000"
            if len(raw_manu) >= 12:
                idv = raw_manu[9:11].hex().upper()
            else:
                idv = "0000"

            if has_clpm:
                d_type = 1
            elif len(raw_manu) >= 14:
                d_type = raw_manu[13]
            elif is_hubmini:
                d_type = 2
            elif is_name_match:
                # Name-matched device without full manufacturer data length; treat as cover type
                d_type = 5
            else:
                return None

        # Check legacy PushMini condition
        is_legacy = (d_type == 1) and (
            rev == 0
            or (rev == 1 and fv <= 9)
            or (rev == 2 and fv <= 5)
            or (rev == 3 and fv <= 5)
        )

        return MiniBigDeviceInfo(
            address=str(address),
            name=str(name),
            idv=idv,
            fv=fv,
            rev=rev,
            d_type=d_type,
            init_mode=init_mode,
            is_legacy=is_legacy,
            service_uuid=service_uuid,
            write_uuid=write_uuid,
            notify_uuid=notify_uuid,
            supported=supported,
            rssi=rssi,
        )
    except (IndexError, ValueError, TypeError) as err:
        _LOGGER.debug("Failed parsing MiniBig advertisement for %s: %s", address, err)
        return None
