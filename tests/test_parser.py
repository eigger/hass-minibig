"""Tests for MiniBig BLE advertisement parser."""

from __future__ import annotations

from dataclasses import dataclass

from custom_components.minibig.minibig_ble.const import (
    DEVICE_SERVICE_UUID,
    HUBMINI_SERVICE_UUID,
)
from custom_components.minibig.minibig_ble.parser import (
    MiniBigDeviceInfo,
    parse_advertisement,
)


@dataclass
class FakeServiceInfo:
    """Mock advertisement service info."""

    address: str = "AA:BB:CC:DD:EE:FF"
    name: str = "MiniBig Device"
    service_uuids: list[str] | None = None
    manufacturer_data: dict[int, bytes] | None = None
    rssi: int = -65


def test_parse_valid_window_opener():
    """Test parsing a valid window opener advertisement."""
    # manu: cid=0x1234, byte2=(rev=0, fv=1, initMode=0)=0x02, [3..8], idv="1CFE", [11..12], d_type=0
    # raw_manu byte[0..1]=34 12, byte[2]=0x02, byte[9..10]=1C FE, byte[13]=0x00
    payload = bytes([
        0x02,  # [2] flags: init_mode=0, fv=1, rev=0
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # [3..8]
        0x1C, 0xFE,  # [9..10] IDV
        0x00, 0x00,  # [11..12]
        0x00,  # [13] d_type
    ])
    service_info = FakeServiceInfo(
        address="11:22:33:44:55:66",
        name="MiniBig Opener",
        service_uuids=[DEVICE_SERVICE_UUID],
        manufacturer_data={0x1234: payload},
        rssi=-70,
    )

    info = parse_advertisement(service_info)
    assert info is not None
    assert info.address == "11:22:33:44:55:66"
    assert info.name == "MiniBig Opener"
    assert info.idv == "1CFE"
    assert info.fv == 1
    assert info.rev == 0
    assert info.d_type == 0
    assert info.init_mode is False
    assert info.is_legacy is False
    assert info.supported is True
    assert info.rssi == -70


def test_parse_pushmini_modern():
    """Test parsing a modern PushMini advertisement."""
    # d_type=1, rev=2, fv=10 (legacy is rev==2 and fv<=5 -> not legacy)
    # byte2: (rev=2 << 6) | (fv=10 << 1) | initMode=1 -> (2<<6)|(10<<1)|1 = 0x80 | 0x14 | 0x01 = 0x95
    payload = bytes([
        0x95,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0xAF, 0xEA,  # IDV = AFEA
        0x00, 0x00,
        0x01,  # d_type = 1
    ])
    service_info = FakeServiceInfo(
        address="AA:BB:CC:11:22:33",
        name="PushMini",
        service_uuids=[DEVICE_SERVICE_UUID],
        manufacturer_data={0x5678: payload},
        rssi=-60,
    )

    info = parse_advertisement(service_info)
    assert info is not None
    assert info.idv == "AFEA"
    assert info.fv == 10
    assert info.rev == 2
    assert info.d_type == 1
    assert info.init_mode is True
    assert info.is_legacy is False


def test_parse_pushmini_legacy():
    """Test parsing a legacy PushMini advertisement."""
    # d_type=1, rev=1, fv=5 -> legacy is True (rev==1 and fv<=9)
    # byte2: (1<<6) | (5<<1) | 0 = 0x40 | 0x0A = 0x4A
    payload = bytes([
        0x4A,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x12, 0x34,  # IDV = 1234
        0x00, 0x00,
        0x01,  # d_type = 1
    ])
    service_info = FakeServiceInfo(
        address="AA:BB:CC:11:22:33",
        name="PushMini Old",
        service_uuids=[DEVICE_SERVICE_UUID],
        manufacturer_data={0x1234: payload},
    )

    info = parse_advertisement(service_info)
    assert info is not None
    assert info.idv == "1234"
    assert info.fv == 5
    assert info.rev == 1
    assert info.d_type == 1
    assert info.is_legacy is True


def test_parse_clpm_name_override():
    """Test that local name containing 'clpm' forces d_type = 1."""
    payload = bytes([
        0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x99, 0x88,
        0x00, 0x00,
        0x05,  # d_type in manu is 5, but name has CLPM
    ])
    service_info = FakeServiceInfo(
        name="CLPM_Button",
        service_uuids=[DEVICE_SERVICE_UUID],
        manufacturer_data={0x1111: payload},
    )

    info = parse_advertisement(service_info)
    assert info is not None
    assert info.d_type == 1
    assert info.idv == "9988"


def test_parse_hubmini_unsupported():
    """Test parsing HubMini advertisement marks supported as False."""
    payload = bytes([
        0x02,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0xAA, 0xBB,
        0x00, 0x00,
        0x02,  # d_type = 2 (HubMini)
    ])
    service_info = FakeServiceInfo(
        name="HubMini_Gate",
        service_uuids=[HUBMINI_SERVICE_UUID],
        manufacturer_data={0x2222: payload},
    )

    info = parse_advertisement(service_info)
    assert info is not None
    assert info.d_type == 2
    assert info.supported is False


def test_parse_invalid_or_short_advertisement():
    """Test short or missing manufacturer data handling."""
    # Missing UUID
    assert parse_advertisement(FakeServiceInfo(service_uuids=[])) is None

    # Irrelevant UUID
    assert parse_advertisement(FakeServiceInfo(service_uuids=["0000180d-0000-1000-8000-00805f9b34fb"])) is None

    # Too short manufacturer data without clpm name
    short_payload = bytes([0x01, 0x02])
    info = parse_advertisement(FakeServiceInfo(
        service_uuids=[DEVICE_SERVICE_UUID],
        manufacturer_data={0x1234: short_payload},
        name="Unknown",
    ))
    assert info is None


def test_device_profile_resolution():
    """Verify that get_device_profile strictly differentiates models and defaults unknown to PROFILE_UNKNOWN."""
    from custom_components.minibig.minibig_ble.devices import (
        PROFILE_HUB_MINI,
        PROFILE_PUSH_MINI_LEGACY,
        PROFILE_PUSH_MINI_NEW,
        PROFILE_UNKNOWN,
        PROFILE_WINDOW_OPENER,
        get_device_profile,
    )

    # 1. Window opener by name
    dev_opener = MiniBigDeviceInfo(
        address="AA:BB:CC:11:22:33",
        name="MiniBig Window Opener",
        idv="1CFE",
        fv=1,
        rev=0,
        d_type=0,
        init_mode=False,
        is_legacy=False,
        service_uuid=DEVICE_SERVICE_UUID,
        write_uuid="write",
        notify_uuid="notify",
    )
    prof_opener = get_device_profile(dev_opener)
    assert prof_opener == PROFILE_WINDOW_OPENER
    assert "cover" in prof_opener.platforms

    # 2. PushMini modern
    dev_push = MiniBigDeviceInfo(
        address="AA:BB:CC:11:22:33",
        name="PushMini",
        idv="AFEA",
        fv=10,
        rev=2,
        d_type=1,
        init_mode=False,
        is_legacy=False,
        service_uuid=DEVICE_SERVICE_UUID,
        write_uuid="write",
        notify_uuid="notify",
    )
    prof_push = get_device_profile(dev_push)
    assert prof_push == PROFILE_PUSH_MINI_NEW
    assert "switch" in prof_push.platforms

    # 3. PushMini legacy
    dev_legacy = MiniBigDeviceInfo(
        address="AA:BB:CC:11:22:33",
        name="PushMini",
        idv="1234",
        fv=5,
        rev=1,
        d_type=1,
        init_mode=False,
        is_legacy=True,
        service_uuid=DEVICE_SERVICE_UUID,
        write_uuid="write",
        notify_uuid="notify",
    )
    prof_legacy = get_device_profile(dev_legacy)
    assert prof_legacy == PROFILE_PUSH_MINI_LEGACY

    # 4. Unknown d_type (e.g. d_type=7 with generic name)
    dev_unknown = MiniBigDeviceInfo(
        address="AA:BB:CC:11:22:33",
        name="MiniBig_Device_99",
        idv="9999",
        fv=1,
        rev=0,
        d_type=7,
        init_mode=False,
        is_legacy=False,
        service_uuid=DEVICE_SERVICE_UUID,
        write_uuid="write",
        notify_uuid="notify",
    )
    prof_unknown = get_device_profile(dev_unknown)
    assert prof_unknown == PROFILE_UNKNOWN
    assert "cover" not in prof_unknown.platforms
    assert "switch" not in prof_unknown.platforms
    assert "sensor" in prof_unknown.platforms

    # 5. HubMini
    dev_hub = MiniBigDeviceInfo(
        address="AA:BB:CC:11:22:33",
        name="HubMini",
        idv="0000",
        fv=1,
        rev=0,
        d_type=2,
        init_mode=False,
        is_legacy=False,
        service_uuid="hub",
        write_uuid="write",
        notify_uuid="notify",
        supported=False,
    )
    prof_hub = get_device_profile(dev_hub)
    assert prof_hub == PROFILE_HUB_MINI
    assert prof_hub.is_supported is False


def test_dp_slots_default_to_none():
    """New device-operation slots stay unset until measured on real hardware."""
    from custom_components.minibig.minibig_ble.devices import (
        ALL_SLOTS,
        PROFILE_WINDOW_OPENER,
    )

    slot_map = PROFILE_WINDOW_OPENER.slot_map
    assert set(slot_map) == set(ALL_SLOTS)

    # Only the DPs confirmed by real captures are populated.
    populated = {slot for slot, dp in slot_map.items() if dp is not None}
    assert populated == {"position", "stop", "battery"}

    # Choice settings expose no options, so no select entity can be built yet.
    for slot in ("install_type", "curtain_type", "direction", "mode"):
        assert PROFILE_WINDOW_OPENER.options_for(slot) is None

    # known_dps stays limited to the populated slots.
    assert PROFILE_WINDOW_OPENER.known_dps == {0, 3, 10}


def test_resolve_dp_overrides():
    """Config entry overrides win over the profile, invalid values are ignored."""
    from custom_components.minibig.minibig_ble.devices import (
        PROFILE_WINDOW_OPENER,
        resolve_dp,
    )

    assert resolve_dp(PROFILE_WINDOW_OPENER, "measure") is None
    assert resolve_dp(PROFILE_WINDOW_OPENER, "measure", {"measure": 7}) == 7
    assert resolve_dp(PROFILE_WINDOW_OPENER, "measure", {"measure": "7"}) == 7
    assert resolve_dp(PROFILE_WINDOW_OPENER, "position", {"position": 5}) == 5
    # Unparseable override falls back to the profile value instead of raising.
    assert resolve_dp(PROFILE_WINDOW_OPENER, "position", {"position": "abc"}) == 0
    assert resolve_dp(PROFILE_WINDOW_OPENER, "measure", {}) is None
