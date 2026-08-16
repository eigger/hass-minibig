"""Tests for MiniBig BLE frame builder and response parser (Golden vectors and edge cases)."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from custom_components.minibig.minibig_ble.const import (
    DEVICE_NOTIFY_UUID,
    DEVICE_SERVICE_UUID,
    DEVICE_WRITE_UUID,
    Opcode,
    StatusCode,
)
from custom_components.minibig.minibig_ble.parser import MiniBigDeviceInfo
from custom_components.minibig.minibig_ble.writer import (
    TimerSpec,
    build_frame,
    build_legacy_setting,
    build_manu_reset,
    build_pub_dps,
    build_read_dps,
    build_restart,
    build_timer_delete,
    build_timer_read,
    build_timer_save,
    has_back_power,
    parse_response,
)


def _make_dev(
    idv: str = "1CFE",
    is_legacy: bool = False,
    d_type: int = 0,
    rev: int = 0,
    fv: int = 1,
) -> MiniBigDeviceInfo:
    return MiniBigDeviceInfo(
        address="11:22:33:44:55:66",
        name="Test Device",
        idv=idv,
        fv=fv,
        rev=rev,
        d_type=d_type,
        init_mode=False,
        is_legacy=is_legacy,
        service_uuid=DEVICE_SERVICE_UUID,
        write_uuid=DEVICE_WRITE_UUID,
        notify_uuid=DEVICE_NOTIFY_UUID,
    )


def test_idv_xor_golden_vectors():
    """Verify IDV XOR logic matches measured real device frames."""
    # Window Opener (IDV 1CFE):
    # 0x1C ^ 0x66 = 0x7A, 0xFE ^ 0x39 = 0xC7 -> prefix [0x7A, 0xC7]
    frame_open = build_frame(Opcode.PUB_DPS, "1CFE", bytes([0x00, 0x00, 0x64]))
    assert frame_open.hex() == "2a7ac7000064"

    frame_stop = build_frame(Opcode.PUB_DPS, "1CFE", bytes([0x03, 0x00, 0x00]))
    assert frame_stop.hex() == "2a7ac7030000"

    # PushMini (IDV AFEA):
    # 0xAF ^ 0x66 = 0xC9, 0xEA ^ 0x39 = 0xD3 -> prefix [0xC9, 0xD3]
    frame_push_on = build_frame(Opcode.PUB_DPS, "AFEA", bytes([0x00, 0x00, 0x01]))
    assert frame_push_on.hex() == "2ac9d3000001"


def test_build_pub_dps_modern():
    """Test PUB_DPS with single and multiple DP triplets."""
    dev = _make_dev(idv="1CFE", is_legacy=False)

    # Single DP: dp0 = 100
    frame = build_pub_dps(dev, [(0, 100)])
    assert frame == bytes.fromhex("2a7ac7000064")

    # Multi DP: dp0 = 50, dp3 = 1
    frame_multi = build_pub_dps(dev, [(0, 50), (3, 1)])
    assert frame_multi == bytes.fromhex("2a7ac7000032030001")


def test_build_pub_dps_legacy():
    """Test legacy PushMini action/setting frame conversion."""
    dev_legacy = _make_dev(idv="AFEA", is_legacy=True, d_type=1)

    # Legacy action (dp0 -> opcode 2)
    frame_on = build_pub_dps(dev_legacy, [(0, 1)])
    # Opcode 2 (ACTION) + C9 D3 + [01]
    assert frame_on.hex() == "02c9d301"

    frame_off = build_pub_dps(dev_legacy, [(0, 0)])
    assert frame_off.hex() == "02c9d300"


def test_build_pub_dps_legacy_multi_dp_raises():
    """Test that passing multiple DPs to legacy device raises ValueError."""
    dev_legacy = _make_dev(idv="AFEA", is_legacy=True, d_type=1)
    with pytest.raises(ValueError, match="Legacy Push devices do not support multiple DPs"):
        build_pub_dps(dev_legacy, [(0, 1), (7, 3)])


def test_build_pub_dps_legacy_non_zero_dp_raises():
    """Test that passing non-zero DP to legacy build_pub_dps raises ValueError."""
    dev_legacy = _make_dev(idv="AFEA", is_legacy=True, d_type=1)
    with pytest.raises(ValueError, match="Legacy Push devices only support dp0"):
        build_pub_dps(dev_legacy, [(5, 1)])


def test_build_legacy_setting_bitfields():
    """Test legacy SETTING bitfield layout according to §1 spec."""
    # Case 1: has_back_power = False (rev=0)
    dev_rev0 = _make_dev(idv="AFEA", is_legacy=True, d_type=1, rev=0, fv=10)
    assert not has_back_power(dev_rev0.rev, dev_rev0.fv)

    # rotate=1, mode=0, direction=1, is_on=1, m_power=3, delay_time=2
    # byte0 = (1<<7) | (0<<6) | (1<<5) | (1<<4) | (3<<2) | (2) = 0x80 | 0x20 | 0x10 | 0x0C | 0x02 = 0xBE
    frame_rev0 = build_legacy_setting(
        dev_rev0,
        is_on=1,
        rotate=1,
        mode=0,
        direction=1,
        m_power=3,
        delay_time=2,
    )
    assert frame_rev0.hex() == "03c9d3be"  # 1 byte payload

    # Case 2: has_back_power = True (rev=2, fv=10)
    dev_rev2 = _make_dev(idv="AFEA", is_legacy=False, d_type=1, rev=2, fv=10)
    assert has_back_power(dev_rev2.rev, dev_rev2.fv)

    # When has_back_power is True:
    # byte0 m_power slot is 0 -> byte0 = 0x80 | 0x20 | 0x10 | 0x00 | 0x02 = 0xB2
    # byte1 = (b_power<<3) | m_power = (2<<3) | 3 = 0x10 | 0x03 = 0x13
    frame_rev2 = build_legacy_setting(
        dev_rev2,
        is_on=1,
        rotate=1,
        mode=0,
        direction=1,
        m_power=3,
        delay_time=2,
        b_power=2,
    )
    assert frame_rev2.hex() == "03c9d3b213"  # 2 byte payload


def test_build_read_dps_and_restart():
    """Test READ_DPS and RESTART frames."""
    dev = _make_dev(idv="1CFE", is_legacy=False)
    assert build_read_dps(dev).hex() == "2b7ac7"  # 43 = 0x2b
    assert build_restart(dev).hex() == "117ac7"   # 17 = 0x11
    assert build_manu_reset(dev).hex() == "2f7ac7"  # 47 = 0x2f

    dev_legacy = _make_dev(idv="1CFE", is_legacy=True)
    assert build_read_dps(dev_legacy).hex() == "047ac7"  # 4 = READ_SETTING
    assert build_manu_reset(dev_legacy).hex() == "087ac7"  # 8 = MANU_RESET


def test_build_timer_frames():
    """Test modern and legacy timer save/read/delete builders."""
    dev = _make_dev(idv="1CFE", is_legacy=False)
    fixed_time = datetime(2026, 8, 16, 12, 0, 0, tzinfo=timezone.utc)

    # Modern timer save (single-shot, mask=0xFF)
    timer_single = TimerSpec(
        t_id=1,
        dp_id=0,
        value=100,
        hour=8,
        minute=30,
        is_single_shot=True,
        activated=True,
    )
    frame_t_save = build_timer_save(dev, timer_single, fixed_time)
    assert frame_t_save[0] == Opcode.TIMER_SAVE_NEW
    # Verify mask is 0xFF
    assert frame_t_save[9] == 0xFF

    # Modern timer save (repeating Mon, Wed: bit7, bit5 -> 0x80 | 0x20 = 0xA0)
    timer_repeat = TimerSpec(
        t_id=2,
        dp_id=0,
        value=0,
        hour=18,
        minute=0,
        weekdays=[0, 2],  # Mon=0, Wed=2
        is_single_shot=False,
    )
    frame_t_rep = build_timer_save(dev, timer_repeat, fixed_time)
    assert frame_t_rep[9] == 0xA0

    # Modern timer read / delete
    assert build_timer_read(dev, fixed_time)[0] == Opcode.TIMER_READ_NEW
    assert build_timer_delete(dev, t_id=1).hex() == "2e7ac701"


def test_naive_datetime_raises():
    """Verify that naive datetime raises ValueError in timer builders."""
    dev = _make_dev(idv="1CFE")
    naive_time = datetime(2026, 8, 16, 12, 0, 0)
    with pytest.raises(ValueError, match="datetime must be timezone-aware"):
        build_timer_read(dev, naive_time)


def test_parse_response_success():
    """Test parsing successful responses (ack and streaming report)."""
    # Ack: 2a fd 00 00 64 0a 00 5b (method=42, status=253, dp0=100, dp10=91)
    raw_ack = bytes.fromhex("2afd0000640a005b")
    resp = parse_response(raw_ack)
    assert resp.ok is True
    assert resp.method == 42
    assert resp.status == StatusCode.DEVICE_SUCCESS
    assert resp.dps == {0: 100, 10: 91}

    # Streaming report: 18 fd 00 00 3c (method=24, status=253, dp0=60)
    raw_report = bytes.fromhex("18fd00003c")
    resp_rep = parse_response(raw_report)
    assert resp_rep.ok is True
    assert resp_rep.method == Opcode.REPORT_DPS
    assert resp_rep.status == StatusCode.DEVICE_SUCCESS
    assert resp_rep.dps == {0: 60}


def test_parse_response_non_dps_method():
    """Verify that non-DPS methods (e.g. SET_WIFI_DATA=18) do not parse payload as garbage DPs."""
    # Method 18 response with ASCII/JSON data
    raw_wifi = bytes([Opcode.SET_WIFI_DATA, StatusCode.DEVICE_SUCCESS]) + b'{"status":"ok"}'
    resp = parse_response(raw_wifi)
    assert resp.ok is True
    assert resp.method == Opcode.SET_WIFI_DATA
    assert resp.data == b'{"status":"ok"}'
    assert resp.dps == {}  # Not parsed as DP triplets


def test_parse_response_legacy_bodies_are_not_decoded():
    """Legacy ACTION/SETTING bodies stay raw: no bitfield layout is assumed."""
    for method, body in (
        (Opcode.ACTION, bytes([0x01])),
        (Opcode.SETTING, bytes([0x10])),
        (Opcode.READ_SETTING, bytes([0x10])),
    ):
        resp = parse_response(bytes([method, StatusCode.DEVICE_SUCCESS]) + body)
        assert resp.ok is True
        assert resp.dps == {}
        # The undecoded body is still available to the caller.
        assert resp.data == body

def test_parse_response_errors_and_edge_cases():
    """Test error status codes and invalid lengths."""
    # Busy error (status=254)
    resp_busy = parse_response(bytes([42, StatusCode.DEVICE_BUSY, 0x00]))
    assert resp_busy.ok is False
    assert resp_busy.status == StatusCode.DEVICE_BUSY
    assert resp_busy.dps == {}

    # Short response (<2 bytes)
    resp_short = parse_response(bytes([42]))
    assert resp_short.ok is False
    assert resp_short.status == StatusCode.BLE_RECEIVED_INVALID_DATA
