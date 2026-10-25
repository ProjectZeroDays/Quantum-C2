"""SQLite database schema and connection management for Quantum-CLI."""

from __future__ import annotations

import sqlite3
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Optional

from quantum.core.env import QCLI_DIR

DB_PATH = Path(QCLI_DIR) / "quantum.db"
_SCHEMA_VERSION = 7
_local = threading.local()


def get_conn() -> sqlite3.Connection:
    """Get thread-local database connection with WAL mode."""
    if not hasattr(_local, "conn") or _local.conn is None:
        _local.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _local.conn.row_factory = sqlite3.Row
        _local.conn.execute("PRAGMA journal_mode=WAL")
        _local.conn.execute("PRAGMA foreign_keys=ON")
        _local.conn.execute("PRAGMA busy_timeout=5000")
    return _local.conn


@contextmanager
def transaction() -> Iterator[sqlite3.Connection]:
    """Context manager for database transactions."""
    conn = get_conn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def init_db() -> None:
    """Initialize database schema with migrations."""
    conn = get_conn()
    cursor = conn.cursor()

    # Create schema_version table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            applied_at REAL NOT NULL
        )
    """)

    # Get current version
    row = cursor.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1").fetchone()
    current_version = row[0] if row else 0

    # Apply migrations
    if current_version < 1:
        _migrate_v1(cursor)
        current_version = 1
    if current_version < 2:
        _migrate_v2(cursor)
        current_version = 2
    if current_version < 3:
        _migrate_v3(cursor)
        current_version = 3
    if current_version < 4:
        _migrate_v4(cursor)
        current_version = 4
    if current_version < 5:
        _migrate_v5(cursor)
        current_version = 5
    if current_version < 6:
        _migrate_v6(cursor)
        current_version = 6
    if current_version < 7:
        _migrate_v7(cursor)
        current_version = 7

    # Record final version
    cursor.execute(
        "INSERT OR REPLACE INTO schema_version (version, applied_at) VALUES (?, ?)",
        (current_version, time.time())
    )
    conn.commit()


def _migrate_v1(cursor: sqlite3.Cursor) -> None:
    """Initial schema - devices, tasks, telemetry, artifacts, loot_fts, creds, edges, otp, geofences, alerts, alert_rules, reports, settings, keys, events."""
    cursor.executescript("""
        CREATE TABLE devices (
            id TEXT PRIMARY KEY,
            nickname TEXT,
            tags TEXT,
            grp TEXT,
            hostname TEXT,
            platform TEXT,
            arch TEXT,
            os_version TEXT,
            build TEXT,
            vendor TEXT,
            model TEXT,
            serial TEXT,
            mac TEXT,
            imei TEXT,
            msisdn TEXT,
            root INTEGER DEFAULT 0,
            selinux TEXT,
            adb INTEGER DEFAULT 0,
            state TEXT NOT NULL DEFAULT 'DISCOVERED',
            channel TEXT,
            last_seen REAL,
            first_seen REAL,
            beacon_s REAL,
            opsec_score INTEGER,
            notes TEXT,
            created REAL,
            updated REAL
        );
        CREATE INDEX ix_devices_state ON devices(state, last_seen);

        CREATE TABLE transitions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            from_state TEXT,
            to_state TEXT NOT NULL,
            reason TEXT,
            ts REAL NOT NULL,
            FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
        );

        CREATE TABLE tasks (
            id TEXT PRIMARY KEY,
            device_id TEXT NOT NULL,
            module TEXT NOT NULL,
            args TEXT,
            cmd TEXT,
            state TEXT NOT NULL DEFAULT 'queued',
            queued REAL NOT NULL,
            started REAL,
            finished REAL,
            exit_code INTEGER,
            stdout TEXT,
            stderr TEXT,
            artifacts TEXT,
            dry_run INTEGER DEFAULT 0,
            FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
        );
        CREATE INDEX ix_tasks_device ON tasks(device_id, state);

        CREATE TABLE telemetry (
            device_id TEXT NOT NULL,
            metric TEXT NOT NULL,
            ts REAL NOT NULL,
            value REAL NOT NULL,
            src TEXT,
            PRIMARY KEY (device_id, metric, ts),
            FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
        );
        CREATE INDEX ix_tel ON telemetry(device_id, metric, ts);

        CREATE TABLE artifacts (
            id TEXT PRIMARY KEY,
            device_id TEXT NOT NULL,
            task_id TEXT,
            kind TEXT NOT NULL,
            path TEXT NOT NULL,
            size INTEGER,
            sha256 TEXT,
            mime TEXT,
            sealed INTEGER DEFAULT 0,
            ts REAL NOT NULL,
            FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE,
            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE SET NULL
        );
        CREATE INDEX ix_art_device ON artifacts(device_id, kind);

        CREATE VIRTUAL TABLE loot_fts USING fts5(
            content,
            path UNINDEXED,
            device_id UNINDEXED,
            kind UNINDEXED,
            tokenize='porter'
        );

        CREATE TABLE creds (
            id TEXT PRIMARY KEY,
            device_id TEXT NOT NULL,
            source TEXT NOT NULL,
            kind TEXT NOT NULL,
            username TEXT,
            secret TEXT,
            secret_enc INTEGER DEFAULT 0,
            host TEXT,
            service TEXT,
            cracked INTEGER DEFAULT 0,
            ts REAL NOT NULL,
            FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
        );
        CREATE INDEX ix_creds_user ON creds(username, service);

        CREATE TABLE edges (
            src TEXT NOT NULL,
            dst TEXT NOT NULL,
            kind TEXT NOT NULL,
            label TEXT,
            conf REAL,
            PRIMARY KEY (src, dst, kind, label)
        );

        CREATE TABLE otp (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            service TEXT NOT NULL,
            code TEXT NOT NULL,
            sender TEXT,
            captured REAL NOT NULL,
            ttl_s INTEGER,
            relayed REAL,
            used INTEGER DEFAULT 0,
            FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
        );

        CREATE TABLE geofences (
            id TEXT PRIMARY KEY,
            device_id TEXT NOT NULL,
            name TEXT NOT NULL,
            lat REAL NOT NULL,
            lon REAL NOT NULL,
            radius_m INTEGER NOT NULL,
            on_enter TEXT,
            on_exit TEXT,
            FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
        );

        CREATE TABLE alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT,
            rule TEXT NOT NULL,
            severity TEXT NOT NULL,
            title TEXT NOT NULL,
            body TEXT,
            ts REAL NOT NULL,
            acked INTEGER DEFAULT 0,
            FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE SET NULL
        );

        CREATE TABLE alert_rules (
            id TEXT PRIMARY KEY,
            expr TEXT NOT NULL,
            severity TEXT NOT NULL,
            route TEXT NOT NULL,
            enabled INTEGER DEFAULT 1,
            hits INTEGER DEFAULT 0
        );

        CREATE TABLE reports (
            id TEXT PRIMARY KEY,
            kind TEXT NOT NULL,
            scope TEXT,
            window TEXT,
            fmt TEXT,
            path TEXT,
            schedule TEXT,
            last_run REAL,
            status TEXT
        );

        CREATE TABLE settings (
            k TEXT PRIMARY KEY,
            v TEXT
        );

        CREATE TABLE keys (
            name TEXT PRIMARY KEY,
            value BLOB NOT NULL,
            created REAL NOT NULL
        );

        CREATE TABLE events (
            seq INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            device_id TEXT,
            payload TEXT NOT NULL,
            ts REAL NOT NULL
        );
        CREATE INDEX ix_events_topic ON events(topic, seq);
    """)


def _migrate_v2(cursor: sqlite3.Cursor) -> None:
    """Add task correlation and result attribution."""
    cursor.execute("ALTER TABLE tasks ADD COLUMN correlation_id TEXT")
    cursor.execute("CREATE INDEX ix_tasks_correlation ON tasks(correlation_id)")


def _migrate_v3(cursor: sqlite3.Cursor) -> None:
    """Add device capabilities JSON column."""
    cursor.execute("ALTER TABLE devices ADD COLUMN capabilities TEXT")


def _migrate_v4(cursor: sqlite3.Cursor) -> None:
    """Add loot indexing columns."""
    cursor.execute("ALTER TABLE artifacts ADD COLUMN indexed INTEGER DEFAULT 0")
    cursor.execute("CREATE INDEX ix_art_indexed ON artifacts(indexed)")


def _migrate_v5(cursor: sqlite3.Cursor) -> None:
    """Add payload customization tracking."""
    cursor.executescript("""
        CREATE TABLE payload_builds (
            id TEXT PRIMARY KEY,
            cve TEXT NOT NULL,
            device_id TEXT,
            options TEXT NOT NULL,
            output_path TEXT,
            size_bytes INTEGER,
            sha256 TEXT,
            locked INTEGER DEFAULT 0,
            ts REAL NOT NULL,
            FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE SET NULL
        )
    """)


def _migrate_v6(cursor: sqlite3.Cursor) -> None:
    """Add scan results table."""
    cursor.executescript("""
        CREATE TABLE scans (
            id TEXT PRIMARY KEY,
            device_id TEXT NOT NULL,
            stage TEXT NOT NULL,
            status TEXT NOT NULL,
            result TEXT,
            started REAL NOT NULL,
            finished REAL,
            FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
        );
        CREATE INDEX ix_scans_device ON scans(device_id, stage);
    """)


def _migrate_v7(cursor: sqlite3.Cursor) -> None:
    """Add module registry table for dynamic module loading."""
    cursor.executescript("""
        CREATE TABLE module_registry (
            name TEXT PRIMARY KEY,
            lane TEXT NOT NULL,
            platforms TEXT NOT NULL,
            requires TEXT NOT NULL,
            destructive INTEGER DEFAULT 0,
            reversible INTEGER DEFAULT 0,
            args_schema TEXT,
            timeout_s INTEGER DEFAULT 120,
            verified INTEGER DEFAULT 0,
            last_verified REAL
        )
    """)


# Convenience functions for common operations

def execute(query: str, params: tuple = ()) -> list[sqlite3.Row]:
    """Execute a query and return all rows."""
    conn = get_conn()
    cursor = conn.execute(query, params)
    return cursor.fetchall()


def execute_one(query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
    """Execute a query and return one row."""
    conn = get_conn()
    cursor = conn.execute(query, params)
    return cursor.fetchone()


def execute_write(query: str, params: tuple = ()) -> int:
    """Execute a write query and return lastrowid."""
    conn = get_conn()
    cursor = conn.execute(query, params)
    conn.commit()
    return cursor.lastrowid


def close() -> None:
    """Close the thread-local connection."""
    if hasattr(_local, "conn") and _local.conn is not None:
        _local.conn.close()
        _local.conn = None