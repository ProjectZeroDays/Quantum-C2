"""Unique ID generators for tasks, scans, loot, events, etc."""

from __future__ import annotations

import hashlib
import os
import time
import uuid
from typing import Optional


# Global counters for monotonic IDs
_task_counter = 0
_scan_counter = 0
_loot_counter = 0
_event_counter = 0
_counters_lock = __import__('threading').Lock()


def new_task_id(device_id: Optional[str] = None) -> str:
    """Generate a unique task ID with format: tsk_<timestamp>_<counter>_<device_prefix>."""
    global _task_counter
    with _counters_lock:
        _task_counter += 1
        counter = _task_counter

    ts = int(time.time() * 1000)
    prefix = ""
    if device_id:
        # Use first 4 chars of device ID for readability
        prefix = f"_{device_id[:4]}"
    return f"tsk_{ts}_{counter:04d}{prefix}"


def new_scan_id(device_id: Optional[str] = None) -> str:
    """Generate a unique scan ID with format: scn_<timestamp>_<counter>_<device_prefix>."""
    global _scan_counter
    with _counters_lock:
        _scan_counter += 1
        counter = _scan_counter

    ts = int(time.time() * 1000)
    prefix = ""
    if device_id:
        prefix = f"_{device_id[:4]}"
    return f"scn_{ts}_{counter:04d}{prefix}"


def new_loot_id(device_id: Optional[str] = None) -> str:
    """Generate a unique loot artifact ID with format: lot_<timestamp>_<counter>_<device_prefix>."""
    global _loot_counter
    with _counters_lock:
        _loot_counter += 1
        counter = _loot_counter

    ts = int(time.time() * 1000)
    prefix = ""
    if device_id:
        prefix = f"_{device_id[:4]}"
    return f"lot_{ts}_{counter:04d}{prefix}"


def new_event_id() -> str:
    """Generate a unique event ID with format: evt_<timestamp>_<counter>."""
    global _event_counter
    with _counters_lock:
        _event_counter += 1
        counter = _event_counter

    ts = int(time.time() * 1000)
    return f"evt_{ts}_{counter:04d}"


def new_device_id(platform: str = "") -> str:
    """Generate a unique device ID with format: dev_<platform>_<random>."""
    platform_prefix = platform[:3].lower() if platform else "gen"
    random_part = uuid.uuid4().hex[:8]
    return f"dev_{platform_prefix}_{random_part}"


def new_report_id(kind: str = "") -> str:
    """Generate a unique report ID with format: rpt_<kind>_<timestamp>_<random>."""
    ts = int(time.time())
    random_part = uuid.uuid4().hex[:6]
    kind_prefix = f"{kind}_" if kind else ""
    return f"rpt_{kind_prefix}{ts}_{random_part}"


def new_alert_id() -> str:
    """Generate a unique alert ID with format: alt_<timestamp>_<random>."""
    ts = int(time.time() * 1000)
    random_part = uuid.uuid4().hex[:6]
    return f"alt_{ts}_{random_part}"


def new_geofence_id() -> str:
    """Generate a unique geofence ID with format: gfc_<timestamp>_<random>."""
    ts = int(time.time())
    random_part = uuid.uuid4().hex[:6]
    return f"gfc_{ts}_{random_part}"


def new_key_name(prefix: str = "key") -> str:
    """Generate a unique key name with format: <prefix>_<timestamp>_<random>."""
    ts = int(time.time())
    random_part = uuid.uuid4().hex[:6]
    return f"{prefix}_{ts}_{random_part}"


def new_payload_build_id(cve: str) -> str:
    """Generate a unique payload build ID with format: pld_<cve>_<timestamp>_<random>."""
    cve_clean = cve.replace("-", "").replace(".", "").lower()
    ts = int(time.time())
    random_part = uuid.uuid4().hex[:6]
    return f"pld_{cve_clean}_{ts}_{random_part}"


def new_module_invocation_id(module: str, device_id: Optional[str] = None) -> str:
    """Generate a unique module invocation ID for tracking."""
    ts = int(time.time() * 1000)
    random_part = uuid.uuid4().hex[:6]
    device_part = f"_{device_id[:4]}" if device_id else ""
    return f"mod_{module}_{ts}_{random_part}{device_part}"


def content_hash(data: bytes, algorithm: str = "sha256") -> str:
    """Compute content hash for deduplication."""
    if algorithm == "sha256":
        return hashlib.sha256(data).hexdigest()
    elif algorithm == "sha1":
        return hashlib.sha1(data).hexdigest()
    elif algorithm == "md5":
        return hashlib.md5(data).hexdigest()
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")


def file_hash(path: str, algorithm: str = "sha256") -> str:
    """Compute hash of a file."""
    h = hashlib.new(algorithm)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def deterministic_id(*parts: str) -> str:
    """Generate a deterministic ID from parts (same parts = same ID)."""
    combined = "|".join(parts)
    return hashlib.sha256(combined.encode()).hexdigest()[:16]


def short_id(length: int = 8) -> str:
    """Generate a short random ID."""
    return uuid.uuid4().hex[:length]


def correlation_id() -> str:
    """Generate a correlation ID for request tracing."""
    return f"corr_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"


# Device fingerprint-based ID generation

def device_fingerprint_id(hardware_id: str) -> str:
    """Generate a stable device ID from hardware fingerprint."""
    return f"dev_{hashlib.sha256(hardware_id.encode()).hexdigest()[:16]}"


def session_id(device_id: str) -> str:
    """Generate a session ID for a device check-in."""
    return f"ses_{device_id}_{int(time.time())}_{uuid.uuid4().hex[:6]}"