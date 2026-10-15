"""The breakdown of one BLE session, as the diagnostic sensors publish it.

``SessionTrace`` records where a command spent its time and where it died.
``blesession`` turns that into the shared report: which radio the link went
over, and one sentence on what a failure most likely means. The sentences that
are specific to a MiniBig device live here; the ones every BLE device shares
(a proxy with no free slot, a weak signal, a stack that stopped answering)
come from the library.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from blesession import (
    Failure,
    SessionTrace,
    build_report,
    generic_cause,
    placement,
    stages,
)
from blesession.hass import radio_facts

from .minibig_ble import MiniBigDeviceError, StatusCode

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_DEVICE_FAULTS: dict[int, str] = {
    StatusCode.DEVICE_NOT_MATCHING: (
        "The device rejected the command header (IDV mismatch). The stored "
        "identity may be stale; it is refreshed from the next advertisement."
    ),
    StatusCode.DEVICE_BUSY: "The device is busy with another action. Retry in a moment.",
    StatusCode.DEVICE_NOT_INITIAL: "The device is not initialised (not paired / set up yet).",
    StatusCode.DEVICE_UNAUTH: "The device refused the command as unauthorised.",
    StatusCode.BLE_RECEIVED_INVALID_DATA: "The device received malformed data over the link.",
}

_FALLBACK_CAUSE = "The command failed before the first stage was reached; see error."


def _device_cause(failure: Failure) -> str | None:
    """The device's own reading, or None where the shared sentence is the one."""
    exc = failure.exc
    if isinstance(exc, MiniBigDeviceError):
        return _DEVICE_FAULTS.get(exc.status)
    where = failure.detail or failure.stage
    if where == stages.CONNECT:
        return (
            "The device could not be reached. It accepts only one BLE link, so "
            "close the vendor app and keep it in range of the adapter or proxy."
            f"{placement(failure.facts, noun='device')}"
        )
    if where == "subscribe":
        return (
            "Connected, but the device did not accept notifications. Usually "
            "transient; if it repeats, the proxy may be serving a stale GATT cache."
        )
    if where == "response":
        return (
            "The command was sent but the device did not answer in time. Usually "
            f"a weak link or a busy device.{placement(failure.facts, noun='device')}"
        )
    return None


def _cause(failure: Failure) -> str | None:
    """The ``cause`` callback: the device's reading first, else the shared one.

    Returning None lets ``build_report`` word the shared sentence and attach
    ``likely_cause_key``; a failure neither covers still gets the fallback.
    """
    text = _device_cause(failure)
    if text is not None:
        return text
    shared = generic_cause(
        failure.stage or failure.detail,
        failure.error,
        failure.facts,
        exc=failure.exc,
        noun="device",
    )
    return None if shared is not None else _FALLBACK_CAUSE


def build_session_report(
    hass: HomeAssistant,
    address: str,
    *,
    operation: str,
    trace: SessionTrace | None,
    exc: BaseException | None,
) -> dict[str, Any]:
    """Assemble the attributes for one finished command.

    Outcome first, then the radio, then the stage timings, in the order
    ``blesession.build_report`` fixes so the same keys mean the same thing
    on every integration.
    """
    trace = trace if trace is not None else SessionTrace()
    facts: Mapping[str, Any] = radio_facts(hass, address, trace.link)
    return build_report(
        operation=operation,
        trace=trace,
        exc=exc,
        facts=facts,
        cause=_cause,
        noun="device",
    )
