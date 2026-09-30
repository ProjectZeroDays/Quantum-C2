"""quantum.weapons.bluetooth — Bluetooth-tier weapons (BlueBorne family).

BlueBorne (CVE-2017-0781 BNEP heap overflow, CVE-2017-0785 SDP info leak,
CVE-2018-5383 KNOB) plus a BlackBED-class BLE staging entry. Remote targets
are probed over the Bluetooth stack surfaces implied by the target profile
(port/stack hints); this module keeps the same never-raise fire contract as
the other tiers.
"""
from __future__ import annotations

from quantum.core.opsec import tcp_probe


def check_blueborne_bnep(ip, params=None):
    """CVE-2017-0781 — BlueBorne BNEP L2CAP heap overflow (Android <=8.0)."""
    params = params or {}
    l2cap = tcp_probe(ip, params.get("bt_port", 8118), 2) if ip else False
    return {
        "cve": "CVE-2017-0781", "status": "check",
        "vector": "bluetooth/l2cap-bnep",
        "hint": "Android <= 8.0 with Bluetooth on; needs proximity — "
                "remote probe limited to stack surface",
        "l2cap_surface": bool(l2cap),
    }


def check_blueborne_sdp(ip, params=None):
    """CVE-2017-0785 — BlueBorne SDP information leak."""
    return {
        "cve": "CVE-2017-0785", "status": "check",
        "vector": "bluetooth/sdp",
        "hint": "Android 4.2–8.1 SDP leak; stage via SDP browse when in range",
    }


def check_knob(ip, params=None):
    """CVE-2018-5383 — Bluetooth KNOB key downgrade (experimental)."""
    return {
        "cve": "CVE-2018-5383", "status": "check",
        "vector": "bluetooth/link-manager",
        "hint": "BR/EDR key entropy downgrade; requires active capture role",
    }


def check_blackbed(ip, params=None):
    """BlackBED-class — BLE GATT staging/attack surface probe."""
    params = params or {}
    gatt = tcp_probe(ip, params.get("gatt_port", 8222), 2) if ip else False
    return {
        "cve": "BLACKBED-BLE", "status": "check",
        "vector": "ble/gatt",
        "hint": "BLE GATT surface reachable; pair/relay staging applies "
                "when in range",
        "gatt_surface": bool(gatt),
    }


def check_bluefrag(ip, params=None):
    """CVE-2020-0022 — BlueFrag L2CAP continuation-fragment heap overflow."""
    return {
        "cve": "CVE-2020-0022", "status": "check",
        "vector": "bluetooth/l2cap-reassembly",
        "hint": "Android 8.0–9.0 in-range overflow; payload generator at "
                "exploit_payloads/CVE-2020-0022-bluefrag",
    }


def check_krack(ip, params=None):
    """CVE-2017-13077 — KRACK WPA2 4-way-handshake key reinstall."""
    return {
        "cve": "CVE-2017-13077", "status": "check",
        "vector": "wifi/eapol-m3-replay",
        "hint": "client-side replay in monitor range; payload generator at "
                "exploit_payloads/CVE-2017-13077-krack",
    }
